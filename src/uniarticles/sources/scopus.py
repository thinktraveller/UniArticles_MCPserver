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


async def _search_scopus(query: str, count: int, sort: str) -> dict:
    api_key = settings.scopus_api_key
    if not api_key:
        raise ValueError("SCOPUS_API_KEY is required")
    headers = {
        "X-ELS-APIKey": api_key,
        "Accept": "application/json",
        "User-Agent": "UniArticlesMCP/0.1.0",
    }
    params = {
        "query": query,
        "count": count,
        "sort": sort,
        "view": "STANDARD",
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
            }
        )
    return _ok(query=query, items=normalized)


async def _get_abstract(eid: str) -> dict:
    api_key = settings.scopus_api_key
    if not api_key:
        raise ValueError("SCOPUS_API_KEY is required")
    headers = {
        "X-ELS-APIKey": api_key,
        "Accept": "application/json",
        "User-Agent": "UniArticlesMCP/0.1.0",
    }
    url = f"{BASE_URL}content/abstract/eid/{eid}"
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()
        # The API returns a wrapper like {"abstracts-retrieval-response": ...}
        # We return the whole JSON as the item.
        return _ok(query=eid, items=[response.json()])


async def _get_author(author_id: str) -> dict:
    api_key = settings.scopus_api_key
    if not api_key:
        raise ValueError("SCOPUS_API_KEY is required")
    headers = {
        "X-ELS-APIKey": api_key,
        "Accept": "application/json",
        "User-Agent": "UniArticlesMCP/0.1.0",
    }
    url = f"{BASE_URL}content/author/author_id/{author_id}"
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()
        return _ok(query=author_id, items=[response.json()])


async def _get_quota() -> dict:
    api_key = settings.scopus_api_key
    if not api_key:
        raise ValueError("SCOPUS_API_KEY is required")
    headers = {
        "X-ELS-APIKey": api_key,
        "Accept": "application/json",
        "User-Agent": "UniArticlesMCP/0.1.0",
    }
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
    async def search_scopus(query: str, count: int = 5, sort: str = "coverDate") -> dict:
        """Search for documents in Scopus using a query string."""
        normalized_query = query.strip()
        bounded = max(1, min(count, 25))
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        try:
            return await _search_scopus(query=normalized_query, count=bounded, sort=sort)
        except Exception as exc:
            return _err(query=normalized_query, message=str(exc))

    @server.tool()
    async def get_abstract_details(eid: str) -> dict:
        """Get detailed abstract information for a Scopus document (by EID)."""
        normalized_eid = eid.strip()
        if not normalized_eid:
            return _err(query=eid, message="eid must not be empty")
        try:
            return await _get_abstract(eid=normalized_eid)
        except Exception as exc:
            return _err(query=normalized_eid, message=str(exc))

    @server.tool()
    async def get_author_profile(author_id: str) -> dict:
        """Get author profile information from Scopus (by Author ID)."""
        normalized_id = author_id.strip()
        if not normalized_id:
            return _err(query=author_id, message="author_id must not be empty")
        try:
            return await _get_author(author_id=normalized_id)
        except Exception as exc:
            return _err(query=normalized_id, message=str(exc))

    @server.tool()
    async def get_quota_status() -> dict:
        """Check current Elsevier API quota status (via Scopus endpoint)."""
        try:
            return await _get_quota()
        except Exception as exc:
            return _err(query="quota", message=str(exc))
