import httpx
from mcp.server.fastmcp import FastMCP


BASE_URL = "https://zenodo.org/api/records"
USER_AGENT = "UniArticlesMCP/3.0.0 (https://github.com/thinktraveller/UniArticles_MCPserver)"


def _ok(query: str, items: list[dict]) -> dict:
    return {"ok": True, "source": "zenodo", "query": query, "count": len(items), "items": items, "error": None}


def _err(query: str, message: str) -> dict:
    return {"ok": False, "source": "zenodo", "query": query, "count": 0, "items": [], "error": message}


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "application/json"}


def _normalize(record: dict) -> dict:
    metadata = record.get("metadata", {}) or {}
    creators = [c.get("name") for c in metadata.get("creators", []) or [] if isinstance(c, dict) and c.get("name")]
    resource_type = metadata.get("resource_type", {}) or {}
    # Only expose file metadata + link (filename/size/link), never fetch content —
    # consistent with sciencedirect_article_object_by_identifier's "metadata only".
    file_links = [
        {
            "filename": f.get("key"),
            "size": f.get("size"),
            "link": (f.get("links") or {}).get("self"),
        }
        for f in record.get("files", []) or []
        if isinstance(f, dict)
    ]
    return {
        "doi": record.get("doi"),
        "conceptdoi": record.get("conceptdoi"),
        "title": metadata.get("title"),
        "authors": creators,
        "description": metadata.get("description"),
        "publication_date": metadata.get("publication_date"),
        "resource_type": resource_type.get("type"),
        "resource_subtype": resource_type.get("subtype"),
        "file_links": file_links,
    }


async def _search(query: str, max_results: int) -> dict:
    # `type=publication` is REQUIRED: Zenodo is a general-purpose repository (also
    # hosting datasets/software/posters); without this filter the tool would return
    # non-paper resources, inconsistent with "academic literature search".
    params = {"q": query, "type": "publication", "size": max_results}
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        response = await client.get(BASE_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    hits = payload.get("hits", {}).get("hits", []) or []
    items = [_normalize(h) for h in hits if isinstance(h, dict)]
    return _ok(query=query, items=items)


def register(server: FastMCP) -> None:
    @server.tool()
    async def zenodo_record_search_by_query(query: str, max_results: int = 10) -> dict:
        """Search Zenodo (general research repository) for PUBLICATION-type records by
        keyword. Filtered to publications only (datasets/software are excluded).
        Returns file metadata/links only, not file contents. No API key needed."""
        normalized_query = query.strip()
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        bounded = max(1, min(max_results, 25))
        try:
            return await _search(query=normalized_query, max_results=bounded)
        except Exception as exc:
            return _err(query=normalized_query, message=str(exc))
