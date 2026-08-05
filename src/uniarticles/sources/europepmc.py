import httpx
from mcp.server.fastmcp import FastMCP


BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"
USER_AGENT = "UniArticlesMCP/3.0.0 (https://github.com/thinktraveller/UniArticles_MCPserver)"


def _ok(query: str, items: list[dict]) -> dict:
    return {"ok": True, "source": "europepmc", "query": query, "count": len(items), "items": items, "error": None}


def _err(query: str, message: str) -> dict:
    return {"ok": False, "source": "europepmc", "query": query, "count": 0, "items": [], "error": message}


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "application/json"}


def _normalize(result: dict) -> dict:
    journal = (result.get("journalInfo") or {}).get("journal") or {}
    return {
        "id": result.get("id"),
        "source": result.get("source"),
        "pmcid": result.get("pmcid"),
        "title": result.get("title"),
        "doi": result.get("doi"),
        "authors": result.get("authorString"),
        "journal": journal.get("title"),
        "publication_year": result.get("pubYear"),
        "cited_by_count": result.get("citedByCount"),
        "is_open_access": result.get("isOpenAccess"),
        "in_epmc": result.get("inEPMC"),
        "in_pmc": result.get("inPMC"),
        "has_pdf": result.get("hasPDF"),
        "first_publication_date": result.get("firstPublicationDate"),
    }


async def _search(query: str, max_results: int) -> dict:
    # Maintained by EBI (NOT NCBI). resultType=core returns the rich field set
    # (authorString/doi/journalInfo/citedByCount/...). Single-page query only; the
    # `nextCursorMark` cursor is not exposed (see docstring).
    params = {"query": query, "format": "json", "resultType": "core", "pageSize": max_results}
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        response = await client.get(f"{BASE_URL}/search", params=params)
        response.raise_for_status()
        payload = response.json()
    results = payload.get("resultList", {}).get("result", []) or []
    items = [_normalize(r) for r in results if isinstance(r, dict)]
    return _ok(query=query, items=items)


def register(server: FastMCP) -> None:
    @server.tool()
    async def europepmc_paper_search_by_query(query: str, max_results: int = 10) -> dict:
        """Search Europe PMC (EBI's life-sciences literature aggregator, distinct from
        NCBI PubMed) for papers by keyword. Returns the first page of results only
        (result ordering is Europe PMC's relevance ranking). No API key needed."""
        normalized_query = query.strip()
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        bounded = max(1, min(max_results, 25))
        try:
            return await _search(query=normalized_query, max_results=bounded)
        except Exception as exc:
            return _err(query=normalized_query, message=str(exc))
