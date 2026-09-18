"""Real-network availability check for every registered UniArticles tool.

Unlike a unit test this deliberately calls each tool against the live upstream
APIs, because the question being answered is "is this tool usable right now"
rather than "is the code self-consistent".

Two modes:
  default     — call all 23 tools once, print an OK/FAIL table.
  --matrix    — additionally probe domain coverage: run a humanities, a
                biomedical, and a Chinese-language query against every keyword
                source, to ground the "which source certainly won't match"
                rules used by the recommended literature-search prompt.

Run:  .venv\\Scripts\\python.exe _verify\\tool_availability_check.py [--matrix]
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from uniarticles.server import create_server  # noqa: E402

# A cross-domain topic that every source indexes something for.
GENERAL_QUERY = "retrieval augmented generation"

# A paper every source should either index or not, used for known-item lookup.
KNOWN_TITLE = "Attention Is All You Need"
# NOTE: 10.48550/arXiv.1706.03762 is a *DataCite* DOI (arXiv-assigned), so
# Crossref / ScienceDirect are supposed to 404 on it. Detail lookups are seeded
# from each source's own search output instead of a hardcoded DOI.


def _unwrap(result):
    """Normalize FastMCP.call_tool's return shape into a dict."""
    if isinstance(result, tuple):
        result = result[0]
    if isinstance(result, list):
        for block in result:
            text = getattr(block, "text", None)
            if text:
                return json.loads(text)
        return {"ok": False, "error": "no text content block"}
    if isinstance(result, dict):
        return result
    return {"ok": False, "error": f"unexpected result type {type(result)!r}"}


def _summarize(payload):
    ok = bool(payload.get("ok"))
    count = payload.get("count")
    items = payload.get("items") or []
    first_title = ""
    if items and isinstance(items[0], dict):
        for key in ("title", "name", "display_name"):
            if items[0].get(key):
                first_title = str(items[0][key])[:58]
                break
    raw_err = payload.get("error")
    err = ""
    if isinstance(raw_err, str) and raw_err.strip():
        err = raw_err.strip().splitlines()[0][:90]
    elif raw_err:
        err = str(raw_err)[:90]
    return ok, count, first_title, err


def _harvest(items):
    """Collect identifier-ish values from a result list for later lookup tests."""
    found = {}
    for item in items or []:
        if not isinstance(item, dict):
            continue
        for key, value in item.items():
            if not isinstance(value, str) or not value:
                continue
            lowered = key.lower()
            if lowered in ("doi", "eid", "pmid", "pii", "issn", "arxiv_id", "id"):
                found.setdefault(lowered, value)
    return found


MATRIX_QUERIES = [
    ("humanities", "Shakespeare authorship attribution stylometry"),
    ("biomedical", "CRISPR base editor off-target effects in human embryos"),
    ("chinese", "深度学习在医学图像分割中的应用"),
]


async def run_matrix(server, tools) -> None:
    """Probe each keyword source with off-domain queries to find real cut-offs."""
    names = {t.name for t in tools}
    keyword_tools = [
        ("scopus", "scopus_document_search_by_query", "count"),
        ("arxiv", "arxiv_paper_search_by_query", "max_results"),
        ("pubmed", "pubmed_paper_search_by_query", "max_results"),
        ("openalex", "openalex_work_search_by_query", "max_results"),
        ("crossref", "crossref_work_search_by_query", "max_results"),
        ("europepmc", "europepmc_paper_search_by_query", "max_results"),
        ("doaj", "doaj_article_search_by_query", "max_results"),
        ("openaire", "openaire_research_product_search_by_query", "max_results"),
        ("core", "core_work_search_by_query", "max_results"),
    ]
    print("=" * 132)
    print("PHASE 3  domain-coverage matrix (does an off-domain query return noise?)")
    for label, query in MATRIX_QUERIES:
        print(f"\n  query[{label}] = {query!r}")
        for short, tool_name, size_key in keyword_tools:
            if tool_name not in names:
                continue
            args = {"query": query, size_key: 3}
            try:
                payload = _unwrap(await server.call_tool(tool_name, args))
            except Exception as exc:  # noqa: BLE001
                payload = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            ok, count, first_title, err = _summarize(payload)
            verdict = f"n={count:<4} {first_title}" if ok else f"FAIL {err}"
            print(f"    {short:<10} {verdict}")


async def main() -> int:
    server = create_server()
    tools = await server.list_tools()
    print(f"registered tools: {len(tools)}")
    print("=" * 132)

    harvested: dict[str, str] = {}
    per_source_doi: dict[str, str] = {}
    elsevier_dois: list[str] = []
    rows = []
    failures = []

    # Phase 1: every tool that takes a bare keyword query.
    search_phase = [
        ("scopus_document_search_by_query", {"query": GENERAL_QUERY, "count": 3}),
        ("arxiv_paper_search_by_query", {"query": GENERAL_QUERY, "max_results": 3}),
        ("pubmed_paper_search_by_query", {"query": GENERAL_QUERY, "max_results": 3}),
        ("openalex_work_search_by_query", {"query": GENERAL_QUERY, "max_results": 3}),
        ("crossref_work_search_by_query", {"query": GENERAL_QUERY, "max_results": 3}),
        ("europepmc_paper_search_by_query", {"query": GENERAL_QUERY, "max_results": 3}),
        ("doaj_article_search_by_query", {"query": GENERAL_QUERY, "max_results": 3}),
        ("openaire_research_product_search_by_query", {"query": GENERAL_QUERY, "max_results": 3}),
        ("core_work_search_by_query", {"query": GENERAL_QUERY, "max_results": 3}),
    ]

    for name, args in search_phase:
        if name not in {t.name for t in tools}:
            rows.append((name, "NOT-REGISTERED", "-", "-", "-"))
            continue
        started = time.perf_counter()
        try:
            payload = _unwrap(await server.call_tool(name, args))
        except Exception as exc:  # noqa: BLE001 - report, never abort the sweep
            payload = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        elapsed = time.perf_counter() - started
        ok, count, first_title, err = _summarize(payload)
        found = _harvest(payload.get("items"))
        harvested.update(found)
        if "doi" in found:
            per_source_doi[name] = found["doi"]
        for item in payload.get("items") or []:
            if isinstance(item, dict):
                doi = item.get("doi")
                if isinstance(doi, str) and doi.startswith("10.1016") and doi not in elsevier_dois:
                    elsevier_dois.append(doi)
        rows.append((name, "OK" if ok else "FAIL", f"{count}", f"{elapsed:.1f}s", first_title or err))
        if not ok:
            failures.append((name, err))

    print("PHASE 1  keyword search")
    for name, status, count, elapsed, detail in rows:
        print(f"  {status:<14} {name:<52} n={count:<5} {elapsed:<7} {detail}")

    # Phase 2: identifier / browsing tools, seeded with phase-1 output.
    print("-" * 132)
    print(f"harvested identifiers: {json.dumps(harvested, ensure_ascii=False)}")
    print("-" * 132)

    crossref_doi = per_source_doi.get("crossref_work_search_by_query", "")
    openalex_doi = per_source_doi.get("openalex_work_search_by_query", "")
    elsevier_doi = elsevier_dois[0] if elsevier_dois else ""
    print(f"elsevier-ish DOIs seen in scopus results: {elsevier_dois[:3]}")

    lookup_phase = [
        ("scopus_abstract_detail_by_eid", {"eid": harvested.get("eid")}),
        ("scopus_serial_title_by_issn", {"issn": "0278-2715"}),
        ("scopus_serial_title_search_by_criteria", {"title": "Nature", "count": 3}),
        ("scopus_subject_classification_lookup_by_source", {"source": "scopus", "abbrev": "COMP"}),
        ("scopus_api_usage_status", {}),
        ("sciencedirect_article_retrieve_by_identifier", {"identifier": elsevier_doi, "identifier_type": "doi"}),
        ("sciencedirect_article_object_by_identifier", {"identifier": elsevier_doi, "identifier_type": "doi"}),
        ("arxiv_paper_detail_by_id", {"paper_id": "1706.03762"}),
        ("arxiv_latest_paper_list_by_category", {"category": "cs.CL", "max_results": 3}),
        ("pubmed_paper_summary_lookup_by_pmids", {"pmids": ["32634418"]}),
        ("pubmed_related_article_search_by_pmid", {"pmid": "32634418", "max_results": 3}),
        ("pubmed_pmc_linkage_lookup_by_pmid", {"pmid": "32634418"}),
        ("openalex_work_detail_by_doi", {"doi": openalex_doi}),
        ("crossref_work_detail_by_doi", {"doi": crossref_doi}),
    ]

    for name, args in lookup_phase:
        if name not in {t.name for t in tools}:
            rows.append((name, "NOT-REGISTERED", "-", "-", "-"))
            continue
        cleaned = {k: v for k, v in args.items() if v is not None}
        started = time.perf_counter()
        try:
            payload = _unwrap(await server.call_tool(name, cleaned))
        except Exception as exc:  # noqa: BLE001
            payload = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        elapsed = time.perf_counter() - started
        ok, count, first_title, err = _summarize(payload)
        rows.append((name, "OK" if ok else "FAIL", f"{count}", f"{elapsed:.1f}s", first_title or err))
        if not ok:
            failures.append((name, err))

    print("PHASE 2  identifier / browsing")
    for name, status, count, elapsed, detail in rows[len(search_phase):]:
        print(f"  {status:<14} {name:<52} n={count:<5} {elapsed:<7} {detail}")

    print("=" * 132)
    called = [r for r in rows if r[1] != "NOT-REGISTERED"]
    print(f"called {len(called)} tools, {sum(1 for r in called if r[1] == 'OK')} ok, {len(failures)} failed")
    for name, err in failures:
        print(f"  FAILURE {name}: {err}")

    if "--matrix" in sys.argv:
        await run_matrix(server, tools)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
