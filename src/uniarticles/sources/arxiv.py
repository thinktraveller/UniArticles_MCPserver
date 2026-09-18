import asyncio
import re

import arxiv
from mcp.server.fastmcp import FastMCP


# arXiv official category codes: a lowercase archive (optionally hyphenated, e.g.
# "astro-ph", "cond-mat", "q-bio") optionally followed by a "." and a subcategory
# (letters, optionally hyphenated, e.g. "AI", "optics", "acc-ph", "stat-mech").
# See https://arxiv.org/category_taxonomy for the authoritative list.
_ARXIV_CATEGORY_RE = re.compile(r"^[a-z][a-z-]*(\.[A-Za-z][A-Za-z-]*)?$")


def _build_category_query(category: str) -> str:
    """Turn a comma-separated list of arXiv category codes into arXiv's official
    ``cat:`` query syntax, e.g. ``'cs.AI,cs.LG' -> 'cat:cs.AI OR cat:cs.LG'``.

    Raises ValueError on empty input or a malformed category code (so the tool
    layer can return a clear _err instead of forwarding a confusing remote error).
    """
    parts = [c.strip() for c in category.split(",") if c.strip()]
    if not parts:
        raise ValueError("category must not be empty")
    for part in parts:
        if not _ARXIV_CATEGORY_RE.match(part):
            raise ValueError(f"invalid arXiv category code: {part!r}")
    return " OR ".join(f"cat:{p}" for p in parts)


def _ok(query: str, items: list[dict]) -> dict:
    return {
        "ok": True,
        "source": "arxiv",
        "query": query,
        "count": len(items),
        "items": items,
        "error": None,
    }


def _err(query: str, message: str) -> dict:
    return {
        "ok": False,
        "source": "arxiv",
        "query": query,
        "count": 0,
        "items": [],
        "error": message,
    }


def _serialize_paper(paper) -> dict:
    return {
        "id": paper.get_short_id(),
        "title": paper.title,
        "authors": [author.name for author in paper.authors],
        "abstract": paper.summary,
        "published": paper.published.isoformat(),
        "categories": paper.categories,
        "pdf_url": paper.pdf_url,
        "doi": paper.doi,
    }


def _run_arxiv_search(query: str, max_results: int, sort_by: arxiv.SortCriterion) -> dict:
    """Run an arXiv query with an explicit sort criterion.

    The criterion is a parameter because the two callers need different
    semantics: keyword search must rank by relevance, while "latest papers in
    category" must stay newest-first (v3.3.0 step 59/60).
    """
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=sort_by,
    )
    papers = []
    for paper in client.results(search):
        papers.append(_serialize_paper(paper))
    return _ok(query=query, items=papers)


def _get_paper_details(paper_id: str) -> dict:
    client = arxiv.Client()
    search = arxiv.Search(id_list=[paper_id])
    try:
        paper = next(client.results(search))
        return _ok(query=paper_id, items=[_serialize_paper(paper)])
    except StopIteration:
        return _err(query=paper_id, message="Paper not found")


def register(server: FastMCP) -> None:
    @server.tool()
    async def arxiv_paper_search_by_query(query: str, max_results: int = 10) -> dict:
        """Search for papers in ArXiv using a query string."""
        normalized_query = query.strip()
        bounded = max(1, min(max_results, 25))
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        try:
            # Relevance (not SubmittedDate): date ordering returned only the
            # newest papers that merely mention the query terms. See step 59.
            return await asyncio.to_thread(
                _run_arxiv_search, normalized_query, bounded, arxiv.SortCriterion.Relevance
            )
        except Exception as exc:
            return _err(query=normalized_query, message=str(exc))

    @server.tool()
    async def arxiv_latest_paper_list_by_category(category: str, max_results: int = 10) -> dict:
        """List the most recently submitted arXiv papers in a given category
        (e.g. 'cs.AI'). Multiple categories may be comma-separated (e.g.
        'cs.AI,cs.LG'). Uses arXiv's official `cat:` query syntax."""
        bounded = max(1, min(max_results, 25))
        try:
            category_query = _build_category_query(category)
        except ValueError as exc:
            return _err(query=category, message=str(exc))
        try:
            # This tool's whole purpose is "most recently submitted", so it
            # deliberately keeps date ordering.
            return await asyncio.to_thread(
                _run_arxiv_search, category_query, bounded, arxiv.SortCriterion.SubmittedDate
            )
        except Exception as exc:
            return _err(query=category, message=str(exc))

    @server.tool()
    async def arxiv_paper_detail_by_id(paper_id: str) -> dict:
        """Get detailed information (abstract/metadata) for a specific ArXiv paper."""
        normalized_id = paper_id.strip()
        if not normalized_id:
            return _err(query=paper_id, message="paper_id must not be empty")
        try:
            return await asyncio.to_thread(_get_paper_details, normalized_id)
        except Exception as exc:
            return _err(query=normalized_id, message=str(exc))
