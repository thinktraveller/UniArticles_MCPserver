import httpx
from mcp.server.fastmcp import FastMCP

from ..config import settings


BASE_URL = "https://api.core.ac.uk/v3/search/works"
USER_AGENT = "UniArticlesMCP/3.0.0 (https://github.com/thinktraveller/UniArticles_MCPserver)"


def _ok(query: str, items: list[dict]) -> dict:
    return {"ok": True, "source": "core", "query": query, "count": len(items), "items": items, "error": None}


def _err(query: str, message: str) -> dict:
    return {"ok": False, "source": "core", "query": query, "count": 0, "items": [], "error": message}


def _headers() -> dict[str, str]:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if settings.core_api_key:
        headers["Authorization"] = f"Bearer {settings.core_api_key}"
    return headers


def _normalize(work: dict) -> dict:
    authors = [a.get("name") for a in work.get("authors", []) or [] if isinstance(a, dict) and a.get("name")]
    return {
        "title": work.get("title"),
        "authors": authors,
        "abstract": work.get("abstract"),
        "doi": work.get("doi"),
        "cited_by_count": work.get("citationCount"),
        # Expose the download link only; do NOT dump the full text (`fullText`) into
        # items — consistent with the project's "metadata/links only" stance.
        "download_url": work.get("downloadUrl"),
        "arxiv_id": work.get("arxivId"),
        "pubmed_id": work.get("pubmedId"),
    }


async def _search(query: str, max_results: int) -> dict:
    params = {"q": query, "limit": max_results}
    # CORE occasionally 301-redirects the request; follow redirects so a valid call
    # is not surfaced as a bare 3xx error.
    async with httpx.AsyncClient(timeout=30.0, headers=_headers(), follow_redirects=True) as client:
        response = await client.get(BASE_URL, params=params)
        if response.status_code == 429:
            # Surface the rate-limit context (see plan step 37.2): without a key CORE
            # locks out after ~5 requests for ~10 minutes. Tell the caller when they
            # can retry and that configuring CORE_API_KEY avoids this.
            retry_after = response.headers.get("x-ratelimit-retry-after") or response.headers.get("Retry-After")
            hint = "" if settings.core_api_key else " Configure CORE_API_KEY for a higher rate limit."
            return _err(
                query=query,
                message=f"CORE rate limit reached (HTTP 429). Retry after: {retry_after or 'unknown'}.{hint}",
            )
        response.raise_for_status()
        payload = response.json()
    items = [_normalize(w) for w in payload.get("results", []) or [] if isinstance(w, dict)]
    return _ok(query=query, items=items)


def register(server: FastMCP) -> None:
    # Unconditional registration (unlike Semantic Scholar): CORE works without a key,
    # just with a strict rate limit, mirroring the existing Elsevier "register always,
    # surface limits at runtime" model.
    @server.tool()
    async def core_work_search_by_query(query: str, max_results: int = 10) -> dict:
        """Search CORE (global open-access aggregator) by keyword. Works without an
        API key (~5 requests before a ~10-minute rate-limit lockout); configuring
        CORE_API_KEY is strongly recommended for reliable use (see README)."""
        normalized_query = query.strip()
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        bounded = max(1, min(max_results, 25))
        try:
            return await _search(query=normalized_query, max_results=bounded)
        except Exception as exc:
            return _err(query=normalized_query, message=str(exc))
