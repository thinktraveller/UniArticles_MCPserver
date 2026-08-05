import httpx
from mcp.server.fastmcp import FastMCP


BASE_URL = "https://dblp.org/search/publ/api"
USER_AGENT = "UniArticlesMCP/3.0.0 (https://github.com/thinktraveller/UniArticles_MCPserver)"


def _ok(query: str, items: list[dict]) -> dict:
    return {"ok": True, "source": "dblp", "query": query, "count": len(items), "items": items, "error": None}


def _err(query: str, message: str) -> dict:
    return {"ok": False, "source": "dblp", "query": query, "count": 0, "items": [], "error": message}


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "application/json"}


def _as_list(value) -> list:
    """dblp returns a single dict when there is one element and a list when there are
    several (e.g. `info.authors.author`, `hits.hit`); coerce to a list."""
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _extract_authors(authors_field) -> list[str]:
    """dblp author shape (per official docs): info.authors.author is a dict/list of
    {"@pid": "...", "text": "Author Name"}. NOTE: NOT yet verified by real capture in
    the build environment — see module docstring / buildlog step 39."""
    if not isinstance(authors_field, dict):
        return []
    names = []
    for author in _as_list(authors_field.get("author")):
        if isinstance(author, dict) and author.get("text"):
            names.append(author["text"])
        elif isinstance(author, str):
            names.append(author)
    return names


def _normalize(hit: dict) -> dict:
    info = hit.get("info", {}) or {}
    return {
        "id": hit.get("@id"),
        "title": info.get("title"),
        "authors": _extract_authors(info.get("authors")),
        "venue": info.get("venue"),
        "year": info.get("year"),
        "type": info.get("type"),
        "doi": info.get("doi"),
        "url": info.get("url") or info.get("ee"),
        "key": info.get("key"),
    }


async def _search(query: str, max_results: int) -> dict:
    params = {"q": query, "format": "json", "h": max_results}
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        response = await client.get(BASE_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    hits = payload.get("result", {}).get("hits", {}).get("hit", [])
    items = [_normalize(h) for h in _as_list(hits) if isinstance(h, dict)]
    return _ok(query=query, items=items)


def register(server: FastMCP) -> None:
    @server.tool()
    async def dblp_publication_search_by_query(query: str, max_results: int = 10) -> dict:
        """Search dblp (computer science bibliography) by keyword. dblp itself requires
        no API key. NOTE: dblp.org has been observed to fail intermittently due to
        network path variance (TLS handshake failures, occasional HTTP 500) in some
        network environments — this reflects network conditions, not a bug in this
        tool or dblp being down. If you see a connection error here, retrying later or
        from a different network is often sufficient.

        (Field mapping is based on dblp's official API docs and has NOT yet been
        verified against a real response capture in this build environment; run
        `_verify/dblp_field_probe.py` on a network that can reach dblp.org to confirm.)"""
        normalized_query = query.strip()
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        bounded = max(1, min(max_results, 25))
        try:
            return await _search(query=normalized_query, max_results=bounded)
        except Exception as exc:
            # dblp is known to fail intermittently for network reasons (see README/
            # buildlog QA-R013); surface that context rather than a bare exception so
            # this is not misread as a code bug on retry.
            return _err(
                query=normalized_query,
                message=f"{exc}（dblp.org 可能因网络环境波动间歇性失败，非必然故障；建议稍后重试或更换网络环境）",
            )
