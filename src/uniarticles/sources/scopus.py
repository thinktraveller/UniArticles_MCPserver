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
        return _ok(query=eid, items=[response.json()])


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
    async def search_scopus(query: str, count: int = 5, sort: str = "coverDate", view: str = "STANDARD") -> dict:
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
    async def get_abstract_details(eid: str, view: str = "META") -> dict:
        """Get detailed abstract information for a Scopus document (by EID).
        Default view is META (unrestricted). Pass view='FULL'/'META_ABS' for more
        complete data if your subscription supports it.
        """
        normalized_eid = eid.strip()
        if not normalized_eid:
            return _err(query=eid, message="eid must not be empty")
        try:
            return await _get_abstract(eid=normalized_eid, view=view)
        except Exception as exc:
            return _err(query=normalized_eid, message=str(exc))

    @server.tool()
    async def get_serial_title(issn: str, view: str = "STANDARD") -> dict:
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
    async def get_quota_status() -> dict:
        """Check current Elsevier API quota status (via Scopus endpoint)."""
        try:
            return await _get_quota()
        except Exception as exc:
            return _err(query="quota", message=str(exc))
