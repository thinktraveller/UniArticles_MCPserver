import httpx
from mcp.server.fastmcp import FastMCP


BASE_URL = "https://api.openaire.eu/search/researchProducts"
USER_AGENT = "UniArticlesMCP/3.0.0 (https://github.com/thinktraveller/UniArticles_MCPserver)"


def _ok(query: str, items: list[dict]) -> dict:
    return {"ok": True, "source": "openaire", "query": query, "count": len(items), "items": items, "error": None}


def _err(query: str, message: str) -> dict:
    return {"ok": False, "source": "openaire", "query": query, "count": 0, "items": [], "error": message}


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "application/json"}


def _as_list(value) -> list:
    """OpenAIRE (XML-derived JSON) returns a single dict when there is one element
    and a list when there are several; coerce to a list for uniform iteration."""
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _text(value):
    """Extract the text payload ('$') from an OpenAIRE value that may be a
    {'$': 'text', '@attr': ...} dict, a plain scalar, or a single-element list."""
    if isinstance(value, list):
        value = value[0] if value else None
    if isinstance(value, dict):
        return value.get("$")
    return value


def _extract_results(payload: dict) -> list[dict]:
    results = payload.get("response", {}).get("results", {})
    results = results.get("result") if isinstance(results, dict) else None
    return [r for r in _as_list(results) if isinstance(r, dict)]


def _oaf_result(result: dict) -> dict:
    entity = result.get("metadata", {}).get("oaf:entity", {})
    if not isinstance(entity, dict):
        return {}
    oaf = entity.get("oaf:result", {})
    return oaf if isinstance(oaf, dict) else {}


def _pick_title(titles) -> str | None:
    entries = _as_list(titles)
    for t in entries:
        if isinstance(t, dict) and t.get("@classid") == "main title":
            return t.get("$")
    return _text(entries[0]) if entries else None


def _pick_doi(pids) -> str | None:
    for p in _as_list(pids):
        if isinstance(p, dict) and p.get("@classid") == "doi":
            return p.get("$")
    return None


def _normalize(result: dict) -> dict:
    oaf = _oaf_result(result)
    authors = [_text(c) for c in _as_list(oaf.get("creator")) if _text(c)]
    subjects = [_text(s) for s in _as_list(oaf.get("subject")) if _text(s)]
    bestaccess = oaf.get("bestaccessright")
    best = bestaccess.get("@classname") if isinstance(bestaccess, dict) else None
    return {
        "title": _pick_title(oaf.get("title")),
        "authors": authors,
        "doi": _pick_doi(oaf.get("pid")),
        "publisher": _text(oaf.get("publisher")),
        "publication_date": _text(oaf.get("dateofacceptance")),
        "best_access_right": best,
        "subjects": subjects,
    }


async def _search(query: str, max_results: int) -> dict:
    params = {"keywords": query, "size": max_results, "format": "json"}
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        response = await client.get(BASE_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    items = [_normalize(r) for r in _extract_results(payload)]
    return _ok(query=query, items=items)


def register(server: FastMCP) -> None:
    @server.tool()
    async def openaire_research_product_search_by_query(query: str, max_results: int = 10) -> dict:
        """Search OpenAIRE (European open science aggregator) for research products by
        keyword. No API key needed. NOTE: reference projects reported occasional HTTP
        403 from this service; it was not reproduced during this project's probing.
        A network error here may reflect that known intermittency, not a tool bug."""
        normalized_query = query.strip()
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        bounded = max(1, min(max_results, 25))
        try:
            return await _search(query=normalized_query, max_results=bounded)
        except Exception as exc:
            return _err(query=normalized_query, message=str(exc))
