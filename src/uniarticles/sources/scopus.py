import httpx
from mcp.server.fastmcp import FastMCP

from ..config import settings


BASE_URL = "https://api.elsevier.com/"


def _ok(query: str, items: list[dict]) -> dict:
    return {
        "ok": True,
        "source": "scopus",
        "query": query,
        "count": len(items),
        "items": items,
        "error": None,
    }


def _err(query: str, message: str) -> dict:
    return {
        "ok": False,
        "source": "scopus",
        "query": query,
        "count": 0,
        "items": [],
        "error": message,
    }


def _as_list(value) -> list:
    """Elsevier returns a single object (dict) when there is one element and a
    list when there are several; coerce to a list for uniform iteration."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _author_name(author: dict) -> str | None:
    """Extract a readable author name from a Scopus abstract author object,
    tolerating the several shapes Elsevier uses."""
    if not isinstance(author, dict):
        return None
    for key in ("ce:indexed-name", "$"):
        name = author.get(key)
        if name:
            return name
    preferred = author.get("preferred-name")
    if isinstance(preferred, dict):
        for key in ("ce:indexed-name", "$"):
            name = preferred.get(key)
            if name:
                return name
    surname = author.get("ce:surname")
    given = author.get("ce:given-name")
    if surname or given:
        return " ".join(p for p in (surname, given) if p)
    return None


def _get_headers() -> dict[str, str]:
    api_key = settings.elsevier_api_key
    if not api_key:
        raise ValueError("ELSEVIER_API_KEY is required")
    headers = {
        "X-ELS-APIKey": api_key,
        "Accept": "application/json",
        "User-Agent": "UniArticlesMCP/0.1.0",
    }
    if settings.elsevier_insttoken:
        headers["X-ELS-Insttoken"] = settings.elsevier_insttoken
    return headers


async def _search_scopus(query: str, count: int, sort: str, view: str) -> dict:
    headers = _get_headers()
    params = {
        "query": query,
        "count": count,
        "sort": sort,
        "view": view,
    }
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(f"{BASE_URL}content/search/scopus", params=params)
        response.raise_for_status()
        payload = response.json()
    entries = payload.get("search-results", {}).get("entry", [])
    normalized = []
    for entry in entries:
        normalized.append(
            {
                "title": entry.get("dc:title"),
                "eid": entry.get("eid"),
                "doi": entry.get("prism:doi"),
                "coverDate": entry.get("prism:coverDate"),
                "publicationName": entry.get("prism:publicationName"),
                "creator": entry.get("dc:creator"),
                "citedbyCount": entry.get("citedby-count"),
                "openaccess": entry.get("openaccess"),
            }
        )
    return _ok(query=query, items=normalized)


async def _get_abstract(eid: str, view: str) -> dict:
    headers = _get_headers()
    url = f"{BASE_URL}content/abstract/eid/{eid}"
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(url, params={"view": view})
        response.raise_for_status()
        payload = response.json()
    # Field structure confirmed by real probe (step 14, view=META): root
    # `abstracts-retrieval-response` has `coredata` (dict) + `affiliation` (list);
    # authors live under `coredata.dc:creator.author`. META does not include the
    # abstract body (`dc:description`); higher views (FULL) may add it.
    response_root = payload.get("abstracts-retrieval-response", {}) or {}
    coredata = response_root.get("coredata", {}) or {}

    creator = coredata.get("dc:creator")
    author_objs: list = []
    if isinstance(creator, dict):
        author_objs = _as_list(creator.get("author"))
    elif isinstance(creator, list):
        author_objs = creator
    authors = [name for name in (_author_name(a) for a in author_objs) if name]

    affiliations = [
        {
            "name": aff.get("affilname"),
            "city": aff.get("affiliation-city"),
            "country": aff.get("affiliation-country"),
        }
        for aff in _as_list(response_root.get("affiliation"))
        if isinstance(aff, dict)
    ]

    # `dc:description` only present in richer views; include it when available.
    abstract_text = coredata.get("dc:description")

    normalized = {
        "title": coredata.get("dc:title"),
        "eid": coredata.get("eid"),
        "doi": coredata.get("prism:doi"),
        "scopus_id": coredata.get("dc:identifier"),
        "publication_name": coredata.get("prism:publicationName"),
        "issn": coredata.get("prism:issn"),
        "aggregation_type": coredata.get("prism:aggregationType"),
        "document_type": coredata.get("subtypeDescription"),
        "cover_date": coredata.get("prism:coverDate"),
        "volume": coredata.get("prism:volume"),
        "issue": coredata.get("prism:issueIdentifier"),
        "page_range": coredata.get("prism:pageRange"),
        "cited_by_count": coredata.get("citedby-count"),
        "publisher": coredata.get("dc:publisher"),
        "openaccess": coredata.get("openaccess"),
        "abstract": abstract_text,
        "authors": authors,
        "affiliations": affiliations,
        "scopus_url": coredata.get("prism:url"),
    }
    return _ok(query=eid, items=[normalized])


async def _get_serial_title(issn: str, view: str) -> dict:
    headers = _get_headers()
    url = f"{BASE_URL}content/serial/title/issn/{issn}"
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(url, params={"view": view})
        response.raise_for_status()
        payload = response.json()
    entries = payload.get("serial-metadata-response", {}).get("entry", []) or []
    normalized = []
    for entry in entries:
        homepage = None
        for link in entry.get("link", []) or []:
            if link.get("@ref") == "homepage":
                homepage = link.get("@href") or None
                break
        subject_areas = [
            {
                "code": area.get("@code"),
                "abbrev": area.get("@abbrev"),
                "name": area.get("$"),
            }
            for area in entry.get("subject-area", []) or []
        ]
        normalized.append(
            {
                "title": entry.get("dc:title"),
                "publisher": entry.get("dc:publisher"),
                "issn": entry.get("prism:issn"),
                "eissn": entry.get("prism:eIssn"),
                "aggregation_type": entry.get("prism:aggregationType"),
                "openaccess": entry.get("openaccess"),
                "openaccess_type": entry.get("openaccessType"),
                "coverage_start_year": entry.get("coverageStartYear"),
                "coverage_end_year": entry.get("coverageEndYear"),
                "subject_areas": subject_areas,
                "homepage_url": homepage,
                "source_id": entry.get("source-id"),
                "scopus_url": entry.get("prism:url"),
            }
        )
    return _ok(query=issn, items=normalized)


async def _get_quota() -> dict:
    headers = _get_headers()
    # Use search endpoint for quota check
    url = f"{BASE_URL}content/search/scopus?query=test&count=1"
    async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
        response = await client.get(url)
        # Even if it fails (e.g. 429), headers might be present.
        # But for simplicity, we assume we can at least reach the server.
        quota = {
            "limit": response.headers.get("X-RateLimit-Limit"),
            "remaining": response.headers.get("X-RateLimit-Remaining"),
            "reset": response.headers.get("X-RateLimit-Reset"),
            "status": response.status_code,
        }
        return _ok(query="quota", items=[quota])


def register(server: FastMCP) -> None:
    @server.tool()
    async def scopus_document_search_by_query(query: str, count: int = 5, sort: str = "coverDate", view: str = "STANDARD") -> dict:
        """Search for documents in Scopus using a query string."""
        normalized_query = query.strip()
        bounded = max(1, min(count, 25))
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        try:
            return await _search_scopus(query=normalized_query, count=bounded, sort=sort, view=view)
        except Exception as exc:
            return _err(query=normalized_query, message=str(exc))

    @server.tool()
    async def scopus_abstract_detail_by_eid(eid: str, view: str = "META") -> dict:
        """Get detailed abstract information for a Scopus document (by EID).
        Returns a normalized record (title, authors, affiliations, journal,
        identifiers, etc.). Default view is META (unrestricted); the abstract
        body is only populated under richer views such as FULL/META_ABS if your
        subscription supports them.
        """
        normalized_eid = eid.strip()
        if not normalized_eid:
            return _err(query=eid, message="eid must not be empty")
        try:
            return await _get_abstract(eid=normalized_eid, view=view)
        except Exception as exc:
            return _err(query=normalized_eid, message=str(exc))

    @server.tool()
    async def scopus_serial_title_by_issn(issn: str, view: str = "STANDARD") -> dict:
        """Get journal/serial metadata (title, publisher, Open Access status, coverage
        years, subject areas, homepage) by ISSN.
        Default view is STANDARD (verified working with a basic subscription tier).
        """
        normalized_issn = issn.strip()
        if not normalized_issn:
            return _err(query=issn, message="issn must not be empty")
        try:
            return await _get_serial_title(issn=normalized_issn, view=view)
        except Exception as exc:
            return _err(query=normalized_issn, message=str(exc))

    @server.tool()
    async def scopus_api_usage_status() -> dict:
        """Check current Elsevier API usage/rate-limit status (via Scopus endpoint)."""
        try:
            return await _get_quota()
        except Exception as exc:
            return _err(query="quota", message=str(exc))
