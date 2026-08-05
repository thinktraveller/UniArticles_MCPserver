import httpx
from mcp.server.fastmcp import FastMCP


BASE_URL = "https://api.archives-ouvertes.fr/search/"
USER_AGENT = "UniArticlesMCP/3.0.0 (https://github.com/thinktraveller/UniArticles_MCPserver)"
# Solr `fl` field list MUST be explicit, otherwise the default field set may omit
# the fields we normalize below. Confirmed by pre-coding probe.
_FL = "docid,title_s,abstract_s,authFullName_s,doiId_s,uri_s,docType_s"


def _ok(query: str, items: list[dict]) -> dict:
    return {"ok": True, "source": "hal", "query": query, "count": len(items), "items": items, "error": None}


def _err(query: str, message: str) -> dict:
    return {"ok": False, "source": "hal", "query": query, "count": 0, "items": [], "error": message}


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "application/json"}


def _first(value):
    """HAL Solr dynamic `*_s` fields such as title_s/abstract_s are arrays even for a
    single value (confirmed by probe); take the first element for scalar fields."""
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _normalize(doc: dict) -> dict:
    authors = doc.get("authFullName_s")
    if not isinstance(authors, list):
        authors = [authors] if authors else []
    return {
        "docid": doc.get("docid"),
        "title": _first(doc.get("title_s")),
        "abstract": _first(doc.get("abstract_s")),
        "authors": authors,
        "doi": doc.get("doiId_s"),
        "url": doc.get("uri_s"),
        "doc_type": doc.get("docType_s"),
    }


async def _search(query: str, max_results: int) -> dict:
    params = {"q": query, "rows": max_results, "fl": _FL, "wt": "json"}
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        response = await client.get(BASE_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    docs = payload.get("response", {}).get("docs", []) or []
    items = [_normalize(d) for d in docs if isinstance(d, dict)]
    return _ok(query=query, items=items)


def register(server: FastMCP) -> None:
    @server.tool()
    async def hal_document_search_by_query(query: str, max_results: int = 10) -> dict:
        """Search HAL (French open archive) for documents by keyword. HAL is
        oriented toward French/European scholarly output — English keyword search
        has recall but coverage may be less complete than English-focused sources.
        No API key needed."""
        normalized_query = query.strip()
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        bounded = max(1, min(max_results, 25))
        try:
            return await _search(query=normalized_query, max_results=bounded)
        except Exception as exc:
            return _err(query=normalized_query, message=str(exc))
