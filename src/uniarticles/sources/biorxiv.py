from datetime import datetime

import httpx
from mcp.server.fastmcp import FastMCP


BASE_URL = "https://api.biorxiv.org/details"
USER_AGENT = "UniArticlesMCP/3.0.0 (https://github.com/thinktraveller/UniArticles_MCPserver)"
_SERVERS = {"biorxiv", "medrxiv"}


def _ok(query: str, items: list[dict]) -> dict:
    return {"ok": True, "source": "biorxiv", "query": query, "count": len(items), "items": items, "error": None}


def _err(query: str, message: str) -> dict:
    return {"ok": False, "source": "biorxiv", "query": query, "count": 0, "items": [], "error": message}


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "application/json"}


def _valid_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _normalize(paper: dict) -> dict:
    return {
        "title": paper.get("title"),
        "authors": paper.get("authors"),
        "doi": paper.get("doi"),
        "date": paper.get("date"),
        "version": paper.get("version"),
        "type": paper.get("type"),
        "category": paper.get("category"),
        "abstract": paper.get("abstract"),
        "published": paper.get("published"),
        "server": paper.get("server"),
    }


async def _browse(server: str, start_date: str, end_date: str, cursor: int) -> dict:
    url = f"{BASE_URL}/{server}/{start_date}/{end_date}/{cursor}"
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()
    messages = payload.get("messages", []) or []
    info = messages[0] if messages else {}
    collection = payload.get("collection", []) or []
    items = [_normalize(p) for p in collection if isinstance(p, dict)]
    total = info.get("total")
    count = info.get("count")
    # Paging info is carried in the `query` description string (30 results/page);
    # the fixed {ok,source,query,count,items,error} response contract is not extended.
    query_desc = (
        f"{server} {start_date}~{end_date} (cursor={cursor}, page_count={count}, "
        f"total={total}); pass a larger cursor to page further"
    )
    return _ok(query=query_desc, items=items)


def register(server: FastMCP) -> None:
    @server.tool()
    async def biorxiv_paper_list_by_date_range(
        server: str,
        start_date: str,
        end_date: str,
        cursor: int = 0,
    ) -> dict:
        """Browse bioRxiv/medRxiv preprints within a date range (NOT keyword search —
        the official API only supports browsing by date window). `server` must be
        'biorxiv' or 'medrxiv'. Dates are YYYY-MM-DD. Results are paged 30 per call;
        use `cursor` (an integer offset) to page further."""
        normalized_server = server.strip().lower()
        if normalized_server not in _SERVERS:
            return _err(query=server, message="server must be 'biorxiv' or 'medrxiv'")
        s_date = start_date.strip()
        e_date = end_date.strip()
        if not _valid_date(s_date) or not _valid_date(e_date):
            return _err(query=f"{start_date}~{end_date}", message="start_date/end_date must be YYYY-MM-DD")
        safe_cursor = max(0, cursor)
        try:
            return await _browse(normalized_server, s_date, e_date, safe_cursor)
        except Exception as exc:
            return _err(query=f"{normalized_server} {s_date}~{e_date}", message=str(exc))
