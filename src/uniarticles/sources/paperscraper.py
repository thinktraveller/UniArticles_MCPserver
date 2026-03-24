import asyncio

from mcp.server.fastmcp import FastMCP
from paperscraper.pubmed.pubmed import get_pubmed_papers
from paperscraper.scholar.scholar import get_scholar_papers


def _ok(query: str, items: list[dict]) -> dict:
    return {
        "ok": True,
        "source": "paperscraper",
        "query": query,
        "count": len(items),
        "items": items,
        "error": None,
    }


def _err(query: str, message: str) -> dict:
    return {
        "ok": False,
        "source": "paperscraper",
        "query": query,
        "count": 0,
        "items": [],
        "error": message,
    }


def _to_items(result: object) -> list[dict]:
    if result is None:
        return []
    if hasattr(result, "empty") and result.empty:
        return []
    if hasattr(result, "to_dict"):
        records = result.to_dict(orient="records")
        return records if isinstance(records, list) else []
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    return []


def _search_pubmed(query: str, max_results: int) -> dict:
    data = get_pubmed_papers(query=query, max_results=max_results)
    return _ok(query=query, items=_to_items(data))


def _search_scholar(title: str) -> dict:
    data = get_scholar_papers(title=title)
    return _ok(query=title, items=_to_items(data))


def register(server: FastMCP) -> None:
    @server.tool()
    async def search_pubmed_papers(query: str, max_results: int = 10) -> dict:
        """Search for papers in PubMed using a query string and return normalized results."""
        normalized_query = query.strip()
        bounded = max(1, min(max_results, 9998))
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        try:
            return await asyncio.to_thread(_search_pubmed, normalized_query, bounded)
        except Exception as exc:
            return _err(query=normalized_query, message=str(exc))

    @server.tool()
    async def search_scholar_papers(title: str) -> dict:
        """Search Google Scholar by title and return normalized paper metadata results."""
        normalized_title = title.strip()
        if not normalized_title:
            return _err(query=title, message="title must not be empty")
        try:
            return await asyncio.to_thread(_search_scholar, normalized_title)
        except Exception as exc:
            return _err(query=normalized_title, message=str(exc))
