import asyncio
import re

import arxiv
from mcp.server.fastmcp import FastMCP


# arXiv official category codes: a lowercase archive (optionally hyphenated, e.g.
# "astro-ph", "cond-mat", "q-bio") optionally followed by a "." and a subcategory
# (letters, optionally hyphenated, e.g. "AI", "optics", "acc-ph", "stat-mech").
# See https://arxiv.org/category_taxonomy for the authoritative list.
_ARXIV_CATEGORY_RE = re.compile(r"^[a-z][a-z-]*(\.[A-Za-z][A-Za-z-]*)?$")

# `export.arxiv.org` occasionally accepts a connection and then never answers;
# before these bounds existed a tool call hung ~5 minutes before erroring
# (measured 337.8s / 338.1s on 2026-09-18). Two layers are used on purpose:
# the socket timeout is the real fix (it lets the worker thread exit), the
# asyncio deadline is only a backstop should the injection below ever stop
# working, since a `wait_for` timeout does not kill the thread it wraps.
_ARXIV_REQUEST_TIMEOUT_SECONDS = 15.0
_ARXIV_TOTAL_TIMEOUT_SECONDS = 45.0


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


def _build_client() -> arxiv.Client:
    """Build an arXiv client with a real request timeout.

    ``arxiv.Client`` exposes only ``page_size`` / ``delay_seconds`` /
    ``num_retries`` — none of which bounds a stalled request. arxiv 2.4.1
    issues every query through an internal ``requests.Session``
    (``arxiv/__init__.py:613`` created it, ``:729`` calls ``.get``), so the
    socket timeout is injected there. ``num_retries`` is lowered from the
    default 3 so a connect-time worst case stays ~2x the per-request timeout
    instead of ~4x.
    """
    client = arxiv.Client(num_retries=1)
    session = getattr(client, "_session", None)  # private attr: version-sensitive
    if session is not None:
        original_get = session.get

        def _get_with_timeout(url, **kwargs):
            kwargs.setdefault("timeout", _ARXIV_REQUEST_TIMEOUT_SECONDS)
            return original_get(url, **kwargs)

        session.get = _get_with_timeout
    return client


def _timeout_message() -> str:
    return (
        f"arXiv request timed out (per-request limit "
        f"{_ARXIV_REQUEST_TIMEOUT_SECONDS:.0f}s, overall deadline "
        f"{_ARXIV_TOTAL_TIMEOUT_SECONDS:.0f}s); "
        "upstream export.arxiv.org may be stalling — retry shortly, or run "
        "_verify/arxiv_connectivity_test.py for a layered diagnosis"
    )


def _is_timeout_error(exc: BaseException) -> bool:
    """True for the several shapes a stalled request can surface as.

    A socket timeout injected into the session arrives as
    ``requests.exceptions.ReadTimeout``/``ConnectTimeout`` (an ``OSError``, not
    a ``TimeoutError``), so matching on the builtin type alone would miss it.
    Only the message is inspected — no import of ``requests`` is added.
    """
    text = str(exc).lower()
    return isinstance(exc, TimeoutError) or "timed out" in text or "timeout" in text


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
    client = _build_client()
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
    client = _build_client()
    search = arxiv.Search(id_list=[paper_id])
    try:
        paper = next(client.results(search))
        return _ok(query=paper_id, items=[_serialize_paper(paper)])
    except StopIteration:
        return _err(query=paper_id, message="Paper not found")


def register(server: FastMCP) -> None:
    @server.tool()
    async def arxiv_paper_search_by_query(query: str, max_results: int = 10) -> dict:
        """Search for papers in ArXiv using a query string.

        ``query`` is passed to arXiv verbatim, so arXiv's field prefixes work —
        use them to pin down one known paper, e.g.
        ``ti:"Attention Is All You Need"``, ``au:Vaswani``,
        ``abs:transformer``, ``cat:cs.LG``. A bare title string is a loose
        full-text query and will not reliably return the paper itself.
        """
        normalized_query = query.strip()
        bounded = max(1, min(max_results, 25))
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        try:
            # Relevance (not SubmittedDate): date ordering returned only the
            # newest papers that merely mention the query terms. See step 59.
            return await asyncio.wait_for(
                asyncio.to_thread(
                    _run_arxiv_search,
                    normalized_query,
                    bounded,
                    arxiv.SortCriterion.Relevance,
                ),
                timeout=_ARXIV_TOTAL_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            return _err(query=normalized_query, message=_timeout_message())
        except Exception as exc:
            return _err(
                query=normalized_query,
                message=_timeout_message() if _is_timeout_error(exc) else str(exc),
            )

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
            return await asyncio.wait_for(
                asyncio.to_thread(
                    _run_arxiv_search,
                    category_query,
                    bounded,
                    arxiv.SortCriterion.SubmittedDate,
                ),
                timeout=_ARXIV_TOTAL_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            return _err(query=category, message=_timeout_message())
        except Exception as exc:
            return _err(
                query=category,
                message=_timeout_message() if _is_timeout_error(exc) else str(exc),
            )

    @server.tool()
    async def arxiv_paper_detail_by_id(paper_id: str) -> dict:
        """Get detailed information (abstract/metadata) for a specific ArXiv paper."""
        normalized_id = paper_id.strip()
        if not normalized_id:
            return _err(query=paper_id, message="paper_id must not be empty")
        try:
            return await asyncio.wait_for(
                asyncio.to_thread(_get_paper_details, normalized_id),
                timeout=_ARXIV_TOTAL_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            return _err(query=normalized_id, message=_timeout_message())
        except Exception as exc:
            return _err(
                query=normalized_id,
                message=_timeout_message() if _is_timeout_error(exc) else str(exc),
            )
