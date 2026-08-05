import httpx
from mcp.server.fastmcp import FastMCP


BASE_URL = "https://api.openalex.org"
USER_AGENT = "UniArticlesMCP/3.0.0 (https://github.com/thinktraveller/UniArticles_MCPserver)"
# OpenAlex asks for a contact (mailto) to enter the faster "polite pool". We use a
# fixed project identifier rather than requiring the user to configure an email.
MAILTO = "uniarticles-mcp@users.noreply.github.com"


def _ok(query: str, items: list[dict]) -> dict:
    return {"ok": True, "source": "openalex", "query": query, "count": len(items), "items": items, "error": None}


def _err(query: str, message: str) -> dict:
    return {"ok": False, "source": "openalex", "query": query, "count": 0, "items": [], "error": message}


def _reconstruct_abstract(inverted_index: dict | None) -> str | None:
    """OpenAlex returns the abstract as an inverted index ({word: [positions]}) and
    NOT as plain text; reconstruct it into readable text so downstream clients get a
    string like every other source, not an unreadable position dict."""
    if not inverted_index:
        return None
    positions: dict[int, str] = {}
    for word, idxs in inverted_index.items():
        for idx in idxs:
            positions[idx] = word
    if not positions:
        return None
    return " ".join(positions[i] for i in sorted(positions))


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "application/json"}


def _normalize_work(work: dict) -> dict:
    authors = [
        a.get("author", {}).get("display_name")
        for a in work.get("authorships", []) or []
        if isinstance(a, dict) and a.get("author", {}).get("display_name")
    ]
    oa = work.get("open_access") or {}
    primary = work.get("primary_location") or {}
    source = primary.get("source") or {}
    return {
        "id": work.get("id"),
        "doi": work.get("doi"),
        "title": work.get("title"),
        "authors": authors,
        "abstract": _reconstruct_abstract(work.get("abstract_inverted_index")),
        "cited_by_count": work.get("cited_by_count"),
        "publication_year": work.get("publication_year"),
        "is_open_access": oa.get("is_oa"),
        "open_access_url": oa.get("oa_url"),
        "venue": source.get("display_name"),
    }


async def _search(query: str, max_results: int) -> dict:
    params = {"search": query, "per_page": max_results, "mailto": MAILTO}
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        response = await client.get(f"{BASE_URL}/works", params=params)
        response.raise_for_status()
        payload = response.json()
    items = [_normalize_work(w) for w in payload.get("results", []) if isinstance(w, dict)]
    return _ok(query=query, items=items)


async def _detail_by_doi(doi: str) -> dict:
    # OpenAlex supports looking up a work by its full DOI URL in the path.
    url = f"{BASE_URL}/works/https://doi.org/{doi}"
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        response = await client.get(url, params={"mailto": MAILTO})
        response.raise_for_status()
        payload = response.json()
    return _ok(query=doi, items=[_normalize_work(payload)])


def register(server: FastMCP) -> None:
    @server.tool()
    async def openalex_work_search_by_query(query: str, max_results: int = 10) -> dict:
        """Search OpenAlex (open scholarly catalog) for works by keyword. Returns
        normalized records with a reconstructed readable abstract. No API key needed."""
        normalized_query = query.strip()
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        bounded = max(1, min(max_results, 25))
        try:
            return await _search(query=normalized_query, max_results=bounded)
        except Exception as exc:
            return _err(query=normalized_query, message=str(exc))

    @server.tool()
    async def openalex_work_detail_by_doi(doi: str) -> dict:
        """Look up a single work on OpenAlex by DOI. No API key needed."""
        normalized_doi = doi.strip()
        if not normalized_doi:
            return _err(query=doi, message="doi must not be empty")
        try:
            return await _detail_by_doi(doi=normalized_doi)
        except Exception as exc:
            return _err(query=normalized_doi, message=str(exc))
