import httpx
from mcp.server.fastmcp import FastMCP


BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"
USER_AGENT = "UniArticlesMCP/3.0.0 (https://github.com/thinktraveller/UniArticles_MCPserver)"


def _ok(query: str, items: list[dict]) -> dict:
    return {"ok": True, "source": "chembl", "query": query, "count": len(items), "items": items, "error": None}


def _err(query: str, message: str) -> dict:
    return {"ok": False, "source": "chembl", "query": query, "count": 0, "items": [], "error": message}


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "application/json"}


def _normalize_document(doc: dict) -> dict:
    return {
        "document_chembl_id": doc.get("document_chembl_id"),
        "doi": doc.get("doi"),
        "title": doc.get("title"),
        "authors": doc.get("authors"),
        "abstract": doc.get("abstract"),
        "journal": doc.get("journal"),
        "pubmed_id": doc.get("pubmed_id"),
        "year": doc.get("year"),
    }


def _normalize_activity(act: dict) -> dict:
    return {
        "standard_type": act.get("standard_type"),
        "standard_value": act.get("standard_value"),
        "standard_units": act.get("standard_units"),
        "pchembl_value": act.get("pchembl_value"),
        "canonical_smiles": act.get("canonical_smiles"),
        "target_pref_name": act.get("target_pref_name"),
        "molecule_chembl_id": act.get("molecule_chembl_id"),
        "assay_description": act.get("assay_description"),
    }


async def _lookup(doi: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
        doc_resp = await client.get(f"{BASE_URL}/document.json", params={"doi": doi})
        doc_resp.raise_for_status()
        doc_payload = doc_resp.json()
        total = (doc_payload.get("page_meta") or {}).get("total_count", 0)
        documents = doc_payload.get("documents", []) or []
        if not total or not documents:
            # "Not indexed" is a clean, expected result — not an error.
            return _ok(query=doi, items=[{"collected": False, "doi": doi, "document": None, "activities": []}])

        document = documents[0]  # only the first matching document (see docstring)
        chembl_id = document.get("document_chembl_id")
        activities: list[dict] = []
        if chembl_id:
            act_resp = await client.get(
                f"{BASE_URL}/activity.json",
                params={"document_chembl_id": chembl_id, "limit": 50},
            )
            act_resp.raise_for_status()
            activities = [
                _normalize_activity(a)
                for a in (act_resp.json().get("activities", []) or [])
                if isinstance(a, dict)
            ]
    item = {
        "collected": True,
        "doi": doi,
        "document": _normalize_document(document),
        "activities": activities,
    }
    return _ok(query=doi, items=[item])


def register(server: FastMCP) -> None:
    @server.tool()
    async def chembl_bioactivity_lookup_by_doi(doi: str) -> dict:
        """Look up whether a paper (by DOI) is indexed in ChEMBL and, if so, its
        structured SAR/bioactivity data (IC50/MIC/Ki, etc.). This is NOT a keyword
        search tool — doi is required and must be non-empty. Most papers are NOT in
        ChEMBL (it covers medicinal-chemistry papers only); an empty result with
        collected=false is a normal, expected outcome, not an error."""
        normalized_doi = doi.strip() if doi else ""
        if not normalized_doi:
            return _err(query=doi, message="doi must not be empty")
        try:
            return await _lookup(doi=normalized_doi)
        except Exception as exc:
            return _err(query=normalized_doi, message=str(exc))
