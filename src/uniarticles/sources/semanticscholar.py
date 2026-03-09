from mcp.server.fastmcp import FastMCP
from semanticscholar import SemanticScholar

from ..config import settings


def _create_client() -> SemanticScholar:
    return SemanticScholar(api_key=settings.semanticscholar_api_key)


def _ok(query: str, items: list[dict]) -> dict:
    return {
        "ok": True,
        "source": "semanticscholar",
        "query": query,
        "count": len(items),
        "items": items,
        "error": None,
    }


def _err(query: str, message: str) -> dict:
    return {
        "ok": False,
        "source": "semanticscholar",
        "query": query,
        "count": 0,
        "items": [],
        "error": message,
    }


def _serialize_paper(paper: object) -> dict:
    return {
        "paperId": getattr(paper, "paperId", None),
        "title": getattr(paper, "title", None),
        "year": getattr(paper, "year", None),
        "abstract": getattr(paper, "abstract", None),
        "url": getattr(paper, "url", None),
        "venue": getattr(paper, "venue", None),
        "citationCount": getattr(paper, "citationCount", None),
    }


def register(server: FastMCP) -> None:
    @server.tool()
    async def search_semantic_scholar(query: str, limit: int = 10) -> dict:
        """Search for papers in Semantic Scholar using a query string."""
        normalized_query = query.strip()
        bounded = max(1, min(limit, 25))
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        try:
            client = _create_client()
            results = client.search_paper(normalized_query, limit=bounded)
            items = [_serialize_paper(item) for item in results]
            return _ok(query=normalized_query, items=items)
        except Exception as exc:
            return _err(query=normalized_query, message=str(exc))
