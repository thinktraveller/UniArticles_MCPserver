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
    """dblp author shape (CONFIRMED by real capture, buildlog step 43): each author is
    {"@pid": "...", "text": "Author Name"} at info.authors.author. The classic dblp
    trap — a SINGLE author is a plain dict, MULTIPLE authors are a list of dicts — is
    handled by _as_list() below (the real thesis sample captured had exactly one
    author, arriving as a bare dict, and now parses correctly)."""
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
    # Field paths verified against a real dblp capture (buildlog step 43):
    #   hit.@id / hit.@score live at the OUTER hit level; everything else under hit.info.
    #   Confirmed-real info keys: title, authors.author(.text), year, type, access, key,
    #   ee (electronic edition = link to the actual paper), url (the dblp record page).
    # `ee` and `url` are DISTINCT in real data (ee -> external paper, url -> dblp record),
    # so they are surfaced as separate fields rather than merged.
    # `venue` and `doi` come from dblp's official API docs and are genuine journal/
    # conference fields, but were ABSENT from the captured "Books and Theses" sample and
    # are therefore not yet confirmed against a real journal-article response; kept with
    # a safe .get() (None when missing, never raises) both for doc fidelity and to keep
    # the cross-source normalized shape's `doi` field uniform with every other source.
    info = hit.get("info", {}) or {}
    return {
        "id": hit.get("@id"),
        "title": info.get("title"),
        "authors": _extract_authors(info.get("authors")),
        "venue": info.get("venue"),
        "year": info.get("year"),
        "type": info.get("type"),
        "access": info.get("access"),
        "doi": info.get("doi"),
        "ee": info.get("ee"),
        "url": info.get("url"),
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

        (Field mapping was corrected against a real dblp response capture in buildlog
        step 43: the outer @id/@score vs. inner info.* split, the single-vs-multiple
        author dict/list shape, and the access/ee/url fields are all confirmed. The
        venue/doi fields remain documented-but-not-yet-capture-confirmed because the
        available sample was a thesis record that omits them.)"""
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
