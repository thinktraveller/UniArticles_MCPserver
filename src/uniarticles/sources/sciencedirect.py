import httpx
from mcp.server.fastmcp import FastMCP

from ..config import settings
from .scopus import _get_headers, BASE_URL


def _ok(query: str, items: list[dict]) -> dict:
    return {
        "ok": True,
        "source": "sciencedirect",
        "query": query,
        "count": len(items),
        "items": items,
        "error": None,
    }


def _err(query: str, message: str) -> dict:
    return {
        "ok": False,
        "source": "sciencedirect",
        "query": query,
        "count": 0,
        "items": [],
        "error": message,
    }


async def _retrieve_article(identifier: str, identifier_type: str, view: str) -> dict:
    headers = _get_headers()
    url = f"{BASE_URL}content/article/{identifier_type}/{identifier}"
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(url, params={"view": view})
        response.raise_for_status()
        return _ok(query=identifier, items=[response.json()])


async def _get_article_objects(identifier: str, identifier_type: str, view: str) -> dict:
    headers = _get_headers()
    url = f"{BASE_URL}content/object/{identifier_type}/{identifier}"
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(url, params={"view": view})
        response.raise_for_status()
        payload = response.json()
    attachments = payload.get("attachment-metadata-response", {}).get("attachment", []) or []
    normalized = []
    for att in attachments:
        normalized.append(
            {
                "filename": att.get("filename"),
                "ref": att.get("ref"),
                "type": att.get("type"),
                "mimetype": att.get("mimetype"),
                "size": att.get("size"),
                "width": att.get("width"),
                "height": att.get("height"),
                "eid": att.get("eid"),
                "download_url": att.get("prism:url"),
            }
        )
    return _ok(query=identifier, items=normalized)


def register(server: FastMCP) -> None:
    @server.tool()
    async def retrieve_article(identifier: str, identifier_type: str = "pii", view: str = "META") -> dict:
        """Retrieve a full-text article record by identifier type (pii, doi, pubmed_id, eid) and value.
        Default view is META (unrestricted). Pass view='FULL'/'META_ABS' for more
        complete data if your subscription supports it.
        """
        normalized_id = identifier.strip()
        normalized_type = identifier_type.strip().lower()
        if not normalized_id:
            return _err(query=identifier, message="identifier must not be empty")
        try:
            return await _retrieve_article(identifier=normalized_id, identifier_type=normalized_type, view=view)
        except Exception as exc:
            return _err(query=normalized_id, message=str(exc))

    @server.tool()
    async def get_article_objects(identifier: str, identifier_type: str = "doi", view: str = "META") -> dict:
        """Get metadata (filename, mimetype, type, download link) for figures/tables/
        supplementary materials attached to an article. Does NOT download the binary
        content itself -- only returns the metadata list and download links.
        identifier_type: doi or pii (both verified working); scopus_id/pubmed_id may also work.
        """
        normalized_id = identifier.strip()
        normalized_type = identifier_type.strip().lower()
        if not normalized_id:
            return _err(query=identifier, message="identifier must not be empty")
        try:
            return await _get_article_objects(identifier=normalized_id, identifier_type=normalized_type, view=view)
        except Exception as exc:
            return _err(query=normalized_id, message=str(exc))
