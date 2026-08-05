from urllib.parse import quote

import httpx
from mcp.server.fastmcp import FastMCP


BASE_URL = "https://doaj.org/api/search/articles"
USER_AGENT = "UniArticlesMCP/3.0.0 (https://github.com/thinktraveller/UniArticles_MCPserver)"


def _ok(query: str, items: list[dict]) -> dict:
    return {"ok": True, "source": "doaj", "query": query, "count": len(items), "items": items, "error": None}


def _err(query: str, message: str) -> dict:
    return {"ok": False, "source": "doaj", "query": query, "count": 0, "items": [], "error": message}


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "application/json"}


def _extract_doi(identifiers: list) -> str | None:
    for ident in identifiers or []:
        if isinstance(ident, dict) and ident.get("type") == "doi":
            return ident.get("id")
    return None


def _normalize(result: dict) -> dict:
    bibjson = result.get("bibjson", {}) or {}
    authors = [a.get("name") for a in bibjson.get("author", []) or [] if isinstance(a, dict) and a.get("name")]
    subjects = [s.get("term") for s in bibjson.get("subject", []) or [] if isinstance(s, dict) and s.get("term")]
    links = [
        {"type": link.get("type"), "content_type": link.get("content_type"), "url": link.get("url")}
        for link in bibjson.get("link", []) or []
        if isinstance(link, dict)
    ]
    return {
        "title": bibjson.get("title"),
        "authors": authors,
        "abstract": bibjson.get("abstract"),
        "keywords": bibjson.get("keywords"),
        "journal": (bibjson.get("journal") or {}).get("title"),
        "doi": _extract_doi(bibjson.get("identifier")),
        "subjects": subjects,
        "year": bibjson.get("year"),
        "links": links,
    }


async def _search(query: str, max_results: int) -> dict:
    # The query is part of the URL PATH (not a query-string param), so it must be
    # URL-encoded — never string-concatenate raw user input into the path.
    url = f"{BASE_URL}/{quote(query, safe='')}"
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        response = await client.get(url, params={"pageSize": max_results})
        response.raise_for_status()
        payload = response.json()
    items = [_normalize(r) for r in payload.get("results", []) if isinstance(r, dict)]
    return _ok(query=query, items=items)


def register(server: FastMCP) -> None:
    @server.tool()
    async def doaj_article_search_by_query(query: str, max_results: int = 10) -> dict:
        """Search DOAJ (Directory of Open Access Journals) for open-access articles by
        keyword. No API key needed."""
        normalized_query = query.strip()
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        bounded = max(1, min(max_results, 25))
        try:
            return await _search(query=normalized_query, max_results=bounded)
        except Exception as exc:
            return _err(query=normalized_query, message=str(exc))
