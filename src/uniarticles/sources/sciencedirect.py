import httpx
from mcp.server.fastmcp import FastMCP

from ..config import settings
from .scopus import _get_headers, BASE_URL, _as_list


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


def _sd_creator_names(creator) -> list:
    """`coredata.dc:creator` in the article response is a list of {'@_fa','$'}
    objects (or a single such object); extract the display names."""
    names = []
    for item in _as_list(creator):
        if isinstance(item, dict):
            name = item.get("$")
            if name:
                names.append(name)
        elif isinstance(item, str) and item:
            names.append(item)
    return names


def _sd_subjects(subject) -> list:
    """`coredata.dcterms:subject` is a list of {'@_fa','$'} objects."""
    subjects = []
    for item in _as_list(subject):
        if isinstance(item, dict):
            value = item.get("$")
            if value:
                subjects.append(value)
        elif isinstance(item, str) and item:
            subjects.append(item)
    return subjects


async def _retrieve_article(identifier: str, identifier_type: str, view: str) -> dict:
    headers = _get_headers()
    url = f"{BASE_URL}content/article/{identifier_type}/{identifier}"
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(url, params={"view": view})
        response.raise_for_status()
        payload = response.json()
    # Field structure confirmed by real probe (step 14, view=META): root
    # `full-text-retrieval-response` has `coredata` (dict) plus `scopus-id`,
    # `scopus-eid`, `link`, `originalText`. Authors are under
    # `coredata.dc:creator` (list of {'@_fa','$'}); subjects under
    # `coredata.dcterms:subject`. The full-text body (`originalText`) is only
    # present under richer, entitlement-gated views, not META.
    response_root = payload.get("full-text-retrieval-response", {}) or {}
    coredata = response_root.get("coredata", {}) or {}

    normalized = {
        "title": coredata.get("dc:title"),
        "doi": coredata.get("prism:doi"),
        "pii": coredata.get("pii"),
        "eid": coredata.get("eid"),
        "identifier": coredata.get("dc:identifier"),
        "publication_name": coredata.get("prism:publicationName"),
        "publisher": coredata.get("prism:publisher"),
        "aggregation_type": coredata.get("prism:aggregationType"),
        "pub_type": coredata.get("pubType"),
        "issn": coredata.get("prism:issn"),
        "volume": coredata.get("prism:volume"),
        "page_range": coredata.get("prism:pageRange"),
        "cover_date": coredata.get("prism:coverDate"),
        "cover_display_date": coredata.get("prism:coverDisplayDate"),
        "copyright": coredata.get("prism:copyright"),
        "openaccess": coredata.get("openaccess"),
        "openaccess_type": coredata.get("openaccessType"),
        "authors": _sd_creator_names(coredata.get("dc:creator")),
        "subjects": _sd_subjects(coredata.get("dcterms:subject")),
        "url": coredata.get("prism:url"),
    }
    return _ok(query=identifier, items=[normalized])


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
    async def sciencedirect_article_retrieve_by_identifier(identifier: str, identifier_type: str = "pii", view: str = "META") -> dict:
        """Retrieve an article record by identifier type (pii, doi, pubmed_id, eid)
        and value. Returns a normalized record (title, authors, journal,
        identifiers, subjects, etc.). Default view is META (unrestricted); the
        full-text body is only populated under richer, entitlement-gated views.
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
    async def sciencedirect_article_object_by_identifier(identifier: str, identifier_type: str = "doi", view: str = "META") -> dict:
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
