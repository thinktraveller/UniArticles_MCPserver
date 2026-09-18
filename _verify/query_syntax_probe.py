"""Probe how each keyword source reacts to query *shape* (bare vs field-tagged).

Motivated by a real failure mode found during the v3.3.x availability sweep:
the PubMed query "CRISPR base editor off-target effects in human embryos"
returns 0 hits untagged but 2 hits once field tags are added, because NCBI's
Automatic Term Mapping resolves the "in human embryos" segment to nothing.
This script records the equivalent bare-vs-tagged behaviour per source so the
recommended literature-search prompt can state the rule accurately.

Run:  .venv\\Scripts\\python.exe _verify\\query_syntax_probe.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from uniarticles.server import create_server  # noqa: E402

PROBES = [
    ("pubmed", "pubmed_paper_search_by_query", "max_results", [
        ("bare long sentence", "CRISPR base editor off-target effects in human embryos"),
        ("field-tagged", "CRISPR base editor off-target effects in human embryos[tiab]"),
        ("bare title", "Attention Is All You Need"),
        ("field-tagged title", "Attention Is All You Need[Title]"),
    ]),
    ("scopus", "scopus_document_search_by_query", "count", [
        ("bare title", "Attention Is All You Need"),
        ("TITLE()", 'TITLE("Attention Is All You Need")'),
        ("chinese bare", "深度学习在医学图像分割中的应用"),
    ]),
    ("arxiv", "arxiv_paper_search_by_query", "max_results", [
        ("bare title", "Attention Is All You Need"),
        ("ti:", 'ti:"Attention Is All You Need"'),
    ]),
    ("europepmc", "europepmc_paper_search_by_query", "max_results", [
        ("bare title", "Attention Is All You Need"),
        ("TITLE:", 'TITLE:"Attention Is All You Need"'),
        ("chinese bare", "深度学习在医学图像分割中的应用"),
    ]),
    ("crossref", "crossref_work_search_by_query", "max_results", [
        ("bare title", "Attention Is All You Need"),
        ("chinese bare", "深度学习在医学图像分割中的应用"),
    ]),
    ("doaj", "doaj_article_search_by_query", "max_results", [
        ("bare title", "Attention Is All You Need"),
        ("short biomed", "CRISPR"),
        ("long biomed", "CRISPR base editor off-target effects in human embryos"),
        ("chinese bare", "深度学习在医学图像分割中的应用"),
    ]),
]


def _unwrap(result):
    if isinstance(result, tuple):
        result = result[0]
    if isinstance(result, list):
        for block in result:
            text = getattr(block, "text", None)
            if text:
                return json.loads(text)
    return result if isinstance(result, dict) else {"ok": False}


def _first_title(items):
    for item in items or []:
        if isinstance(item, dict):
            for key in ("title", "name", "display_name"):
                if item.get(key):
                    return str(item[key])[:66]
    return ""


async def main() -> int:
    server = create_server()
    for label, tool_name, size_key, cases in PROBES:
        print(f"\n### {label}  ({tool_name})")
        for case_label, query in cases:
            try:
                payload = _unwrap(await server.call_tool(tool_name, {"query": query, size_key: 3}))
            except Exception as exc:  # noqa: BLE001
                payload = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            if payload.get("ok"):
                detail = f"n={payload.get('count')}  {_first_title(payload.get('items'))}"
            else:
                detail = f"FAIL {str(payload.get('error'))[:80]}"
            print(f"  {case_label:<20} {query[:52]:<54} {detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
