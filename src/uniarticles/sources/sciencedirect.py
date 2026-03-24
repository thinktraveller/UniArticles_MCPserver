import httpx
from mcp.server.fastmcp import FastMCP

from ..config import settings
from .scopus import _get_headers, BASE_URL


def _ok(query: str, items: list[dict]) -> dict:
    return {
        "ok": True,
        "source": "sciencedirect",
        "query": query,
        "count": len(items),
        "items": items,
        "error": None,
    }


def _err(query: str, message: str) -> dict:
    return {
        "ok": False,
        "source": "sciencedirect",
        "query": query,
        "count": 0,
        "items": [],
        "error": message,
    }


async def _search_sciencedirect(query: str, count: int, start: int, view: str) -> dict:
    headers = _get_headers()
    params = {
        "query": query,
        "count": count,
        "start": start,
        "view": view,
    }
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(f"{BASE_URL}content/search/sciencedirect", params=params)
        response.raise_for_status()
        return _ok(query=query, items=[response.json()])


async def _get_article_metadata(query: str, count: int, start: int, view: str) -> dict:
    headers = _get_headers()
    params = {
        "query": query,
        "count": count,
        "start": start,
        "view": view,
    }
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(f"{BASE_URL}content/metadata/article", params=params)
        response.raise_for_status()
        return _ok(query=query, items=[response.json()])


async def _retrieve_article(identifier: str, identifier_type: str, view: str) -> dict:
    headers = _get_headers()
    url = f"{BASE_URL}content/article/{identifier_type}/{identifier}"
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(url, params={"view": view})
        response.raise_for_status()
        return _ok(query=identifier, items=[response.json()])


def register(server: FastMCP) -> None:
    @server.tool()
    async def search_sciencedirect(query: str, count: int = 25, start: int = 0, view: str = "STANDARD") -> dict:
        """Search ScienceDirect records using the query syntax."""
        normalized_query = query.strip()
        bounded_count = max(1, min(count, 200))
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        try:
            return await _search_sciencedirect(query=normalized_query, count=bounded_count, start=start, view=view)
        except Exception as exc:
            return _err(query=normalized_query, message=str(exc))

    @server.tool()
    async def get_article_metadata(query: str, count: int = 25, start: int = 0, view: str = "STANDARD") -> dict:
        """Search ScienceDirect article metadata."""
        normalized_query = query.strip()
        bounded_count = max(1, min(count, 200))
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        try:
            return await _get_article_metadata(query=normalized_query, count=bounded_count, start=start, view=view)
        except Exception as exc:
            return _err(query=normalized_query, message=str(exc))

    @server.tool()
    async def retrieve_article(identifier: str, identifier_type: str = "pii", view: str = "META_ABS") -> dict:
        """Retrieve a full-text article record by identifier type (pii, doi, pubmed_id, eid) and value."""
        normalized_id = identifier.strip()
        normalized_type = identifier_type.strip().lower()
        if not normalized_id:
            return _err(query=identifier, message="identifier must not be empty")
        try:
            return await _retrieve_article(identifier=normalized_id, identifier_type=normalized_type, view=view)
        except Exception as exc:
            return _err(query=normalized_id, message=str(exc))
