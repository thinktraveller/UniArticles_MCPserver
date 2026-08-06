"""PubMed data source — direct NCBI Entrez E-utilities integration (v3.1.0).

Replaces the former ``paperscraper.py`` (which wrapped the third-party
``paperscraper``/``pymed-paperscraper`` packages). This module calls the NCBI
Entrez E-utilities endpoints directly via ``httpx`` and parses their responses
in-process (EFetch returns XML, ESearch/ESummary/ELink return JSON), removing
the heavy ``paperscraper`` dependency chain.

Field mappings / XML paths are grounded in the real probe captured in step 43
(``_verify/pubmed_eutils_field_probe.py`` output), not on documentation guesses.

The public tools are defined in ``register()`` (added incrementally in steps
45~48). This module intentionally is NOT wired into ``sources/__init__.py`` until
step 49, to avoid registering a half-built source mid-refactor.
"""

import xml.etree.ElementTree as ET

import httpx
from mcp.server.fastmcp import FastMCP

from ..config import settings


BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
# Version kept in sync with sibling v3.0.0 modules (core.py/dblp.py/...); the
# project-wide version-string reconciliation is handled centrally in step 51.
USER_AGENT = "UniArticlesMCP/3.0.0 (https://github.com/thinktraveller/UniArticles_MCPserver)"
# NCBI etiquette: identify the caller via tool/email (recommended, not required).
CONTACT_EMAIL = "wangzh685@mail2.sysu.edu.cn"
TOOL_NAME = "uniarticles-mcp"


def _ok(query: str, items: list[dict]) -> dict:
    # NOTE: source is "pubmed" (v3.1.0 breaking change — was "paperscraper").
    return {"ok": True, "source": "pubmed", "query": query, "count": len(items), "items": items, "error": None}


def _err(query: str, message: str) -> dict:
    return {"ok": False, "source": "pubmed", "query": query, "count": 0, "items": [], "error": message}


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT}


def _params(extra: dict) -> dict:
    """Build the common query params for an E-utilities call.

    Always injects ``tool``/``email`` (NCBI etiquette) and ``api_key`` when
    ``NCBI_API_KEY`` is configured. Defaults ``db=pubmed`` but lets callers
    override it (ELink PMC needs ``db=pmc``). Rate limiting is deliberately NOT
    done client-side: like every other source module here (e.g. core.py only
    surfaces the 429 context on hit), a single MCP tool call issues just 1~2 HTTP
    requests, well under NCBI's per-second ceiling; a token bucket / sliding
    window would be needless complexity for this low-probability case. If step 52
    regression ever observes a real 429, add throttling then — do not pre-design it.
    """
    params: dict = {"tool": TOOL_NAME, "email": CONTACT_EMAIL}
    params.update(extra)
    params.setdefault("db", "pubmed")
    if settings.ncbi_api_key:
        params["api_key"] = settings.ncbi_api_key
    return params


# --------------------------------------------------------------------------- #
# XML parsing helpers (grounded in step 43 real EFetch capture, not doc guesses)
# --------------------------------------------------------------------------- #
def _itertext(el: ET.Element | None) -> str | None:
    """Join all descendant text of an element (ArticleTitle/AbstractText may embed
    <i>/<sup>/<sub> subtags; plain ``.text`` would truncate them)."""
    if el is None:
        return None
    text = "".join(el.itertext()).strip()
    return text or None


def _parse_abstract(article: ET.Element) -> str | None:
    """Concatenate Abstract/AbstractText segments.

    Step 43 confirmed the two-state trap: a single unlabeled AbstractText, OR
    several labeled segments (RATIONALE/METHODS/RESULTS/CONCLUSIONS). Labeled
    segments are prefixed with their label so the structure is preserved in one
    string; unlabeled segments are joined plainly.
    """
    segments = article.findall(".//Abstract/AbstractText")
    if not segments:
        return None
    parts: list[str] = []
    for seg in segments:
        text = _itertext(seg)
        if not text:
            continue
        label = seg.get("Label")
        parts.append(f"{label}: {text}" if label else text)
    return "\n".join(parts) if parts else None


def _parse_authors(article: ET.Element) -> list[str]:
    """Author display names. ``LastName ForeName`` for personal authors, or the
    ``CollectiveName`` for group/institutional authors. AuthorList may be absent."""
    authors: list[str] = []
    for author in article.findall(".//AuthorList/Author"):
        collective = _itertext(author.find("CollectiveName"))
        if collective:
            authors.append(collective)
            continue
        last = _itertext(author.find("LastName"))
        fore = _itertext(author.find("ForeName"))
        name = " ".join(p for p in (last, fore) if p)
        if name:
            authors.append(name)
    return authors


def _parse_pubdate(article: ET.Element) -> str | None:
    """Publication date as ``YYYY[-MM[-DD]]``. Prefers Article/ArticleDate
    (numeric), falls back to Journal/JournalIssue/PubDate (Month may be text like
    'Aug'). Many historical records carry only a year, so month/day are optional."""
    for path in (".//Article/ArticleDate", ".//Journal/JournalIssue/PubDate"):
        node = article.find(path)
        if node is None:
            continue
        year = _itertext(node.find("Year"))
        if not year:
            # Some PubDate carry a free-text <MedlineDate> (e.g. "2020 Jan-Feb").
            medline = _itertext(node.find("MedlineDate"))
            if medline:
                return medline
            continue
        month = _itertext(node.find("Month"))
        day = _itertext(node.find("Day"))
        return "-".join(p for p in (year, month, day) if p)
    return None


def _find_article_id(article: ET.Element, id_type: str) -> str | None:
    for aid in article.findall(f".//ArticleIdList/ArticleId[@IdType='{id_type}']"):
        text = _itertext(aid)
        if text:
            return text
    return None


def _find_elocation(article: ET.Element, eid_type: str) -> str | None:
    for el in article.findall(f".//ELocationID[@EIdType='{eid_type}']"):
        text = _itertext(el)
        if text:
            return text
    return None


def _normalize_article(article: ET.Element) -> dict:
    doi = _find_article_id(article, "doi") or _find_elocation(article, "doi")
    keyword_els = article.findall(".//KeywordList/Keyword")  # KeywordList may be absent
    return {
        "pmid": _itertext(article.find(".//MedlineCitation/PMID")),
        "title": _itertext(article.find(".//Article/ArticleTitle")),
        "abstract": _parse_abstract(article),
        "authors": _parse_authors(article),
        "journal": _itertext(article.find(".//Journal/Title"))
        or _itertext(article.find(".//Journal/ISOAbbreviation")),
        "publication_date": _parse_pubdate(article),
        "doi": doi,
        "pii": _find_elocation(article, "pii"),
        "pmcid": _find_article_id(article, "pmc"),
        "keywords": [kw for kw in (_itertext(k) for k in keyword_els) if kw],
    }


# --------------------------------------------------------------------------- #
# NCBI E-utilities requests
# --------------------------------------------------------------------------- #
async def _esearch(query: str, retmax: int) -> list[str]:
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        response = await client.get(
            f"{BASE_URL}esearch.fcgi",
            params=_params({"term": query, "retmax": retmax, "retmode": "json"}),
        )
        response.raise_for_status()
        payload = response.json()
    return payload.get("esearchresult", {}).get("idlist", []) or []


async def _efetch(pmids: list[str]) -> list[dict]:
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        response = await client.get(
            f"{BASE_URL}efetch.fcgi",
            params=_params({"id": ",".join(pmids), "rettype": "abstract", "retmode": "xml"}),
        )
        response.raise_for_status()
    root = ET.fromstring(response.text)
    return [_normalize_article(el) for el in root.findall(".//PubmedArticle")]


async def _search(query: str, max_results: int) -> dict:
    try:
        pmids = await _esearch(query, max_results)
    except Exception as exc:  # noqa: BLE001 - report which step failed (see plan step 45)
        return _err(query=query, message=f"ESearch failed: {exc}")
    if not pmids:
        return _ok(query=query, items=[])  # 0 hits is a valid empty result, not an error
    try:
        items = await _efetch(pmids)
    except Exception as exc:  # noqa: BLE001
        return _err(query=query, message=f"EFetch failed (ESearch returned {len(pmids)} PMIDs): {exc}")
    return _ok(query=query, items=items)


# --------------------------------------------------------------------------- #
# ESummary (lightweight batch metadata)
# --------------------------------------------------------------------------- #
def _clean_pmids(pmids: list[str], cap: int) -> list[str]:
    """Normalize a PMID list: defensive comma-split (some MCP clients may pass a
    single comma-joined string element), strip, drop empties, dedupe (order-preserving),
    cap the batch size (NCBI recommends <=200 IDs per GET)."""
    flat: list[str] = []
    for raw in pmids:
        if raw is None:
            continue
        for part in str(raw).split(","):
            part = part.strip()
            if part:
                flat.append(part)
    seen: set[str] = set()
    deduped = [p for p in flat if not (p in seen or seen.add(p))]
    return deduped[:cap]


def _normalize_summary(entry: dict) -> dict:
    uid = entry.get("uid")
    if entry.get("error"):
        # Invalid/not-found PMID: surface it as a per-item error so the caller sees
        # exactly which requested IDs failed, while the overall call stays ok=True.
        return {"pmid": uid, "error": entry.get("error"), "title": None, "authors": [],
                "journal": None, "publication_date": None, "doi": None, "pmcid": None,
                "pii": None, "pubstatus": None, "pmcrefcount": None, "elocationid": None}
    ids = {a.get("idtype"): a.get("value") for a in entry.get("articleids", []) or [] if isinstance(a, dict)}
    authors = [a.get("name") for a in entry.get("authors", []) or [] if isinstance(a, dict) and a.get("name")]
    return {
        "pmid": uid,
        "error": None,
        "title": entry.get("title"),
        "authors": authors,
        "journal": entry.get("fulljournalname") or entry.get("source"),
        "publication_date": entry.get("pubdate") or entry.get("epubdate"),
        "doi": ids.get("doi"),
        "pmcid": ids.get("pmc"),  # e.g. "PMC6286148"; absent when no PMC full text
        "pii": ids.get("pii"),
        "pubstatus": entry.get("pubstatus"),
        "pmcrefcount": entry.get("pmcrefcount"),
        "elocationid": entry.get("elocationid"),
    }


async def _esummary(pmids: list[str]) -> list[dict]:
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        response = await client.get(
            f"{BASE_URL}esummary.fcgi",
            params=_params({"id": ",".join(pmids), "retmode": "json"}),
        )
        response.raise_for_status()
        payload = response.json()
    result = payload.get("result", {}) or {}
    uids = result.get("uids", []) or []
    return [_normalize_summary(result[uid]) for uid in uids if uid in result]


# --------------------------------------------------------------------------- #
# ELink neighbor (related articles)
# --------------------------------------------------------------------------- #
def _links_for(payload: dict, linkname: str) -> list[str]:
    """Extract the plain PMID/ID list under a specific ELink ``linkname``.

    Returns [] when the linkname is absent — which is a legitimately empty result
    (e.g. a brand-new article NCBI hasn't computed neighbors for yet), NOT a parse
    failure. Callers rely on this distinction (see plan step 47 risk note)."""
    for linkset in payload.get("linksets", []) or []:
        for db in linkset.get("linksetdbs", []) or []:
            if db.get("linkname") == linkname:
                return [str(x) for x in (db.get("links", []) or [])]
    return []


async def _related(pmid: str, max_results: int) -> list[dict]:
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        response = await client.get(
            f"{BASE_URL}elink.fcgi",
            params=_params(
                {"dbfrom": "pubmed", "db": "pubmed", "id": pmid, "cmd": "neighbor", "retmode": "json"}
            ),
        )
        response.raise_for_status()
        payload = response.json()
    # "pubmed_pubmed" is the canonical "Similar articles" neighbor set (ranked by
    # relevance). Links are plain PMID strings with NO score field (confirmed step 43).
    related = _links_for(payload, "pubmed_pubmed")
    # The query PMID itself is typically the first neighbor — drop it, then slice.
    filtered = [pid for pid in related if pid != str(pmid)][:max_results]
    return [{"pmid": pid} for pid in filtered]


def register(server: FastMCP) -> None:
    # Unconditional registration (mirrors CORE/Elsevier): NCBI works without a key,
    # NCBI_API_KEY only raises the rate limit. Tools added in steps 45~48.

    @server.tool()
    async def pubmed_paper_search_by_query(query: str, max_results: int = 10) -> dict:
        """Search PubMed by keyword via NCBI Entrez (ESearch to get PMIDs, then
        EFetch to retrieve and parse the article XML). Returns normalized records
        (title, abstract, authors, journal, doi, pmid, pmcid, keywords, date)."""
        normalized_query = query.strip()
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        # NCBI ESearch retmax ceiling is 9999 for a single call.
        bounded = max(1, min(max_results, 9998))
        try:
            return await _search(query=normalized_query, max_results=bounded)
        except Exception as exc:  # noqa: BLE001
            return _err(query=normalized_query, message=str(exc))

    @server.tool()
    async def pubmed_paper_summary_lookup_by_pmids(pmids: list[str]) -> dict:
        """Look up lightweight PubMed metadata for a batch of PMIDs via ESummary.
        Faster than a full fetch and carries fields the search tool lacks (pmcid,
        pubstatus, pmcrefcount, elocationid). Invalid PMIDs are returned as items
        with a per-item ``error`` field rather than failing the whole call. Max 200
        PMIDs per call (excess is truncated)."""
        cleaned = _clean_pmids(pmids or [], cap=200)
        query = ",".join(cleaned)
        if not cleaned:
            return _err(query=query, message="pmids must not be empty")
        try:
            return _ok(query=query, items=await _esummary(cleaned))
        except Exception as exc:  # noqa: BLE001
            return _err(query=query, message=str(exc))

    @server.tool()
    async def pubmed_related_article_search_by_pmid(pmid: str, max_results: int = 10) -> dict:
        """Find PubMed articles topically related to a given PMID (NCBI ELink
        'Similar articles' / pubmed_pubmed neighbor set, ranked by relevance).
        Returns a list of related PMIDs (the source PMID itself is excluded). Call
        pubmed_paper_summary_lookup_by_pmids on the results for their metadata."""
        normalized_pmid = pmid.strip()
        if not normalized_pmid:
            return _err(query=pmid, message="pmid must not be empty")
        bounded = max(1, min(max_results, 100))
        try:
            return _ok(query=normalized_pmid, items=await _related(normalized_pmid, bounded))
        except Exception as exc:  # noqa: BLE001
            return _err(query=normalized_pmid, message=str(exc))
