import httpx
import xml.etree.ElementTree as ET
from mcp.server.fastmcp import FastMCP


BASE_URL = "https://chemrxiv.org/engage/chemrxiv/public-api/v1"


def _ok(term: str, items: list[dict]) -> dict:
    return {
        "ok": True,
        "source": "chemrxiv",
        "query": term,
        "count": len(items),
        "items": items,
        "error": None,
    }


def _err(term: str, message: str) -> dict:
    return {
        "ok": False,
        "source": "chemrxiv",
        "query": term,
        "count": 0,
        "items": [],
        "error": message,
    }


def _normalize_item(item: dict) -> dict:
    return {
        "itemId": item.get("itemId") or item.get("id"),
        "doi": item.get("doi"),
        "title": item.get("title"),
        "abstract": item.get("abstract"),
        "authors": item.get("authors"),
        "publishedDate": item.get("publishedDate") or item.get("published"),
        "url": item.get("url"),
        "license": item.get("license"),
    }


async def _search_items(term: str, limit: int, page: int | None, sort: str | None) -> dict:
    params = {"term": term, "limit": limit}
    if page is not None:
        params["page"] = page
    if sort:
        params["sort"] = sort
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(f"{BASE_URL}/items", params=params)
        response.raise_for_status()
        payload = response.json()
    items = payload.get("items") or payload.get("results") or []
    normalized = [_normalize_item(item) for item in items]
    return _ok(term=term, items=normalized)


async def _get_item_by_id(item_id: str) -> dict:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(f"{BASE_URL}/items/{item_id}")
        response.raise_for_status()
        item = response.json()
    return _ok(term=item_id, items=[_normalize_item(item)])


async def _get_item_by_doi(doi: str) -> dict:
    async with httpx.AsyncClient(timeout=20.0) as client:
        # Search for the DOI
        response = await client.get(f"{BASE_URL}/items", params={"term": doi})
        response.raise_for_status()
        payload = response.json()
    items = payload.get("items") or []
    # Strict filter for DOI
    matched = [item for item in items if item.get("doi") == doi]
    if matched:
        return _ok(term=doi, items=[_normalize_item(matched[0])])
    return _err(term=doi, message="DOI not found")


async def _list_categories() -> dict:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(f"{BASE_URL}/categories")
        response.raise_for_status()
        items = response.json()
    return _ok(term="categories", items=items)


async def _list_licenses() -> dict:
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(f"{BASE_URL}/licenses")
        response.raise_for_status()
        items = response.json()
    return _ok(term="licenses", items=items)


async def _list_oai_records(limit: int) -> dict:
    url = f"{BASE_URL}/oai?verb=ListRecords&metadataPrefix=oai_dc"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        xml_content = response.text

    items = []
    try:
        root = ET.fromstring(xml_content)
        # OAI Namespaces
        ns = {
            "oai": "http://www.openarchives.org/OAI/2.0/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
        }

        # Iterate over records
        for record in root.findall(".//oai:record", ns):
            if len(items) >= limit:
                break

            header = record.find("oai:header", ns)
            identifier = (
                header.find("oai:identifier", ns).text
                if header is not None and header.find("oai:identifier", ns) is not None
                else None
            )
            datestamp = (
                header.find("oai:datestamp", ns).text
                if header is not None and header.find("oai:datestamp", ns) is not None
                else None
            )

            title = None
            creators = []

            metadata = record.find("oai:metadata", ns)
            if metadata is not None:
                oai_dc = metadata.find("oai_dc:dc", ns)
                if oai_dc is not None:
                    t = oai_dc.find("dc:title", ns)
                    if t is not None:
                        title = t.text
                    for c in oai_dc.findall("dc:creator", ns):
                        if c.text:
                            creators.append(c.text)

            items.append(
                {
                    "identifier": identifier,
                    "datestamp": datestamp,
                    "title": title,
                    "creators": creators,
                }
            )
    except Exception as e:
        return _err(term="oai", message=f"Failed to parse OAI XML: {str(e)}")

    return _ok(term="oai_records", items=items)


def register(server: FastMCP) -> None:
    @server.tool()
    async def search_chemrxiv(
        term: str,
        limit: int = 10,
        page: int | None = None,
        sort: str | None = None,
    ) -> dict:
        """Search for preprints in ChemRxiv using a search term."""
        normalized_term = term.strip()
        bounded = max(1, min(limit, 50))
        if not normalized_term:
            return _err(term=term, message="term must not be empty")
        try:
            return await _search_items(term=normalized_term, limit=bounded, page=page, sort=sort)
        except Exception as exc:
            return _err(term=normalized_term, message=str(exc))

    @server.tool()
    async def search_chemrxiv_title(
        title: str,
        limit: int = 10,
        page: int | None = None,
        sort: str | None = None,
    ) -> dict:
        """Search for preprints in ChemRxiv by title."""
        normalized_title = title.strip()
        bounded = max(1, min(limit, 50))
        if not normalized_title:
            return _err(term=title, message="title must not be empty")
        try:
            # Search using title as term, then filter results?
            # Or trust that 'term' search includes title (it does).
            # We can post-filter if strict title match is needed, but 'term' is usually enough.
            # To be more specific, we rely on the search engine ranking.
            return await _search_items(term=normalized_title, limit=bounded, page=page, sort=sort)
        except Exception as exc:
            return _err(term=normalized_title, message=str(exc))

    @server.tool()
    async def get_chemrxiv_by_id(item_id: str) -> dict:
        """Get a ChemRxiv preprint by its Item ID."""
        normalized_id = item_id.strip()
        if not normalized_id:
            return _err(term=item_id, message="item_id must not be empty")
        try:
            return await _get_item_by_id(item_id=normalized_id)
        except Exception as exc:
            return _err(term=normalized_id, message=str(exc))

    @server.tool()
    async def get_chemrxiv_by_doi(doi: str) -> dict:
        """Get a ChemRxiv preprint by its DOI."""
        normalized_doi = doi.strip()
        if not normalized_doi:
            return _err(term=doi, message="doi must not be empty")
        try:
            return await _get_item_by_doi(doi=normalized_doi)
        except Exception as exc:
            return _err(term=normalized_doi, message=str(exc))

    @server.tool()
    async def list_chemrxiv_categories() -> dict:
        """List all available ChemRxiv categories."""
        try:
            return await _list_categories()
        except Exception as exc:
            return _err(term="categories", message=str(exc))

    @server.tool()
    async def list_chemrxiv_licenses() -> dict:
        """List all available ChemRxiv licenses."""
        try:
            return await _list_licenses()
        except Exception as exc:
            return _err(term="licenses", message=str(exc))

    @server.tool()
    async def list_chemrxiv_oai_records(limit: int = 10) -> dict:
        """List records from ChemRxiv OAI-PMH interface."""
        bounded = max(1, min(limit, 50))
        try:
            return await _list_oai_records(limit=bounded)
        except Exception as exc:
            return _err(term="oai", message=str(exc))
