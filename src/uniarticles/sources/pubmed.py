"""PubMed data source — direct NCBI Entrez E-utilities integration (v3.1.0).

Replaces the former ``paperscraper.py`` (which wrapped the third-party
``paperscraper``/``pymed-paperscraper`` packages). This module calls the NCBI
Entrez E-utilities endpoints directly via ``httpx`` and parses their responses
in-process (EFetch returns XML, ESearch/ESummary/ELink return JSON), removing
the heavy ``paperscraper`` dependency chain.

Field mappings / XML paths are grounded in the real probe captured in step 43
(``_verify/pubmed_eutils_field_probe.py`` output), not on documentation guesses.

The public tools are defined in ``register()`` (added incrementally in steps
45~48). This module intentionally is NOT wired into ``sources/__init__.py`` until
step 49, to avoid registering a half-built source mid-refactor.
"""

import httpx
from mcp.server.fastmcp import FastMCP

from ..config import settings


BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
# Version kept in sync with sibling v3.0.0 modules (core.py/dblp.py/...); the
# project-wide version-string reconciliation is handled centrally in step 51.
USER_AGENT = "UniArticlesMCP/3.0.0 (https://github.com/thinktraveller/UniArticles_MCPserver)"
# NCBI etiquette: identify the caller via tool/email (recommended, not required).
CONTACT_EMAIL = "wangzh685@mail2.sysu.edu.cn"
TOOL_NAME = "uniarticles-mcp"


def _ok(query: str, items: list[dict]) -> dict:
    # NOTE: source is "pubmed" (v3.1.0 breaking change — was "paperscraper").
    return {"ok": True, "source": "pubmed", "query": query, "count": len(items), "items": items, "error": None}


def _err(query: str, message: str) -> dict:
    return {"ok": False, "source": "pubmed", "query": query, "count": 0, "items": [], "error": message}


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT}


def _params(extra: dict) -> dict:
    """Build the common query params for an E-utilities call.

    Always injects ``tool``/``email`` (NCBI etiquette) and ``api_key`` when
    ``NCBI_API_KEY`` is configured. Defaults ``db=pubmed`` but lets callers
    override it (ELink PMC needs ``db=pmc``). Rate limiting is deliberately NOT
    done client-side: like every other source module here (e.g. core.py only
    surfaces the 429 context on hit), a single MCP tool call issues just 1~2 HTTP
    requests, well under NCBI's per-second ceiling; a token bucket / sliding
    window would be needless complexity for this low-probability case. If step 52
    regression ever observes a real 429, add throttling then — do not pre-design it.
    """
    params: dict = {"tool": TOOL_NAME, "email": CONTACT_EMAIL}
    params.update(extra)
    params.setdefault("db", "pubmed")
    if settings.ncbi_api_key:
        params["api_key"] = settings.ncbi_api_key
    return params


def register(server: FastMCP) -> None:
    # Tools are added in steps 45~48:
    #   - pubmed_paper_search_by_query        (ESearch + EFetch, XML)         [step 45]
    #   - pubmed_paper_summary_lookup_by_pmids (ESummary)                     [step 46]
    #   - pubmed_related_article_search_by_pmid (ELink neighbor)             [step 47]
    #   - pubmed_pmc_linkage_lookup_by_pmid    (ELink PMC)                    [step 48]
    pass
