import re

import httpx
from mcp.server.fastmcp import FastMCP


BASE_URL = "https://api.crossref.org"
USER_AGENT = "UniArticlesMCP/3.0.0 (https://github.com/thinktraveller/UniArticles_MCPserver)"
MAILTO = "uniarticles-mcp@users.noreply.github.com"

# Crossref abstracts are wrapped in (JATS) XML tags such as <jats:p>/<p>; strip them
# for a readable plain-text abstract consistent with the other sources.
_TAG_RE = re.compile(r"<[^>]+>")


def _ok(query: str, items: list[dict]) -> dict:
    return {"ok": True, "source": "crossref", "query": query, "count": len(items), "items": items, "error": None}


def _err(query: str, message: str) -> dict:
    return {"ok": False, "source": "crossref", "query": query, "count": 0, "items": [], "error": message}


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "application/json"}


def _first(value):
    """Crossref returns `title`/`container-title` as arrays even when there is one
    element; take the first item, tolerating a plain string or missing value."""
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _clean_abstract(abstract: str | None) -> str | None:
    if not abstract:
        return None
    return _TAG_RE.sub("", abstract).strip() or None


def _format_published(published: dict | None) -> str | None:
    """Crossref dates are `{"date-parts": [[2024, 3, 15]]}` (nested arrays); flatten
    to an ISO-ish string like '2024-03-15' / '2024-03' / '2024'."""
    if not isinstance(published, dict):
        return None
    parts = published.get("date-parts")
    if not isinstance(parts, list) or not parts or not isinstance(parts[0], list):
        return None
    return "-".join(str(p) for p in parts[0] if p is not None) or None


def _normalize_work(work: dict) -> dict:
    authors = []
    for a in work.get("author", []) or []:
        if not isinstance(a, dict):
            continue
        name = " ".join(p for p in (a.get("given"), a.get("family")) if p)
        if name:
            authors.append(name)
    return {
        "doi": work.get("DOI"),
        "title": _first(work.get("title")),
        "authors": authors,
        "abstract": _clean_abstract(work.get("abstract")),
        "cited_by_count": work.get("is-referenced-by-count"),
        "container_title": _first(work.get("container-title")),
        "publisher": work.get("publisher"),
        "url": work.get("URL"),
        "published": _format_published(work.get("published")),
    }


async def _search(query: str, max_results: int) -> dict:
    params = {"query": query, "rows": max_results, "mailto": MAILTO}
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        response = await client.get(f"{BASE_URL}/works", params=params)
        response.raise_for_status()
        payload = response.json()
    items = [_normalize_work(w) for w in payload.get("message", {}).get("items", []) if isinstance(w, dict)]
    return _ok(query=query, items=items)


async def _detail_by_doi(doi: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        response = await client.get(f"{BASE_URL}/works/{doi}", params={"mailto": MAILTO})
        response.raise_for_status()
        payload = response.json()
    return _ok(query=doi, items=[_normalize_work(payload.get("message", {}) or {})])


def register(server: FastMCP) -> None:
    @server.tool()
    async def crossref_work_search_by_query(query: str, max_results: int = 10) -> dict:
        """Search Crossref (DOI registration agency metadata) for works by keyword.
        No API key needed."""
        normalized_query = query.strip()
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        bounded = max(1, min(max_results, 25))
        try:
            return await _search(query=normalized_query, max_results=bounded)
        except Exception as exc:
            return _err(query=normalized_query, message=str(exc))

    @server.tool()
    async def crossref_work_detail_by_doi(doi: str) -> dict:
        """Look up a single work on Crossref by DOI. No API key needed."""
        normalized_doi = doi.strip()
        if not normalized_doi:
            return _err(query=doi, message="doi must not be empty")
        try:
            return await _detail_by_doi(doi=normalized_doi)
        except Exception as exc:
            return _err(query=normalized_doi, message=str(exc))
