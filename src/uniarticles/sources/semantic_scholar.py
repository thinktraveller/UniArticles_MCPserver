import httpx
from mcp.server.fastmcp import FastMCP

from ..config import settings


BASE_URL = "https://api.semanticscholar.org/graph/v1"
USER_AGENT = "UniArticlesMCP/3.0.0 (https://github.com/thinktraveller/UniArticles_MCPserver)"
# Fields to request from the Graph API (defaults return a very thin record).
_FIELDS = "title,abstract,authors,year,citationCount,externalIds"


def _ok(query: str, items: list[dict]) -> dict:
    return {"ok": True, "source": "semantic_scholar", "query": query, "count": len(items), "items": items, "error": None}


def _err(query: str, message: str) -> dict:
    return {"ok": False, "source": "semantic_scholar", "query": query, "count": 0, "items": [], "error": message}


def _headers() -> dict[str, str]:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if settings.semantic_scholar_api_key:
        headers["x-api-key"] = settings.semantic_scholar_api_key
    return headers


def _normalize(paper: dict) -> dict:
    external = paper.get("externalIds") or {}
    authors = [a.get("name") for a in paper.get("authors", []) or [] if isinstance(a, dict) and a.get("name")]
    return {
        "paper_id": paper.get("paperId"),
        "doi": external.get("DOI"),
        "arxiv_id": external.get("ArXiv"),
        "pubmed_id": external.get("PubMed"),
        "title": paper.get("title"),
        "abstract": paper.get("abstract"),
        "authors": authors,
        "year": paper.get("year"),
        "cited_by_count": paper.get("citationCount"),
    }


async def _search(query: str, max_results: int) -> dict:
    params = {"query": query, "limit": max_results, "fields": _FIELDS}
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        response = await client.get(f"{BASE_URL}/paper/search", params=params)
        response.raise_for_status()
        payload = response.json()
    items = [_normalize(p) for p in payload.get("data", []) or [] if isinstance(p, dict)]
    return _ok(query=query, items=items)


async def _detail_by_doi(doi: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        response = await client.get(f"{BASE_URL}/paper/DOI:{doi}", params={"fields": _FIELDS})
        response.raise_for_status()
        payload = response.json()
    return _ok(query=doi, items=[_normalize(payload)])


def register(server: FastMCP) -> None:
    # Conditional (module-level) registration: without a key, Semantic Scholar's
    # keyword search fails deterministically (429 on every request in the shared
    # anonymous pool — confirmed during probing). Per goal.md QA-R012, do NOT
    # register ANY tool from this module rather than exposing tools that always
    # error at call time. This must be an early return here (so @server.tool() never
    # runs), NOT an in-tool key check — the difference is tool-list visibility.
    if not settings.semantic_scholar_api_key:
        return

    @server.tool()
    async def semantic_scholar_paper_search_by_query(query: str, max_results: int = 10) -> dict:
        """Search Semantic Scholar by keyword. Requires SEMANTIC_SCHOLAR_API_KEY
        (this tool is not registered at all when the key is missing)."""
        normalized_query = query.strip()
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        bounded = max(1, min(max_results, 25))
        try:
            return await _search(query=normalized_query, max_results=bounded)
        except Exception as exc:
            return _err(query=normalized_query, message=str(exc))

    @server.tool()
    async def semantic_scholar_paper_detail_by_doi(doi: str) -> dict:
        """Look up a paper on Semantic Scholar by DOI. Requires
        SEMANTIC_SCHOLAR_API_KEY (this tool is not registered when the key is missing)."""
        normalized_doi = doi.strip()
        if not normalized_doi:
            return _err(query=doi, message="doi must not be empty")
        try:
            return await _detail_by_doi(doi=normalized_doi)
        except Exception as exc:
            return _err(query=normalized_doi, message=str(exc))
