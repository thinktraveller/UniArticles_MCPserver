# UniArticles MCP Server

[![License: AGPL-3.0-or-later](https://img.shields.io/badge/License-AGPL%203.0--or--later-blue.svg)](https://www.gnu.org/licenses/agpl-3.0.html)
[![License: Dual (AGPL or Commercial)](https://img.shields.io/badge/License-Dual%3A%20AGPL%20%7C%20Commercial-orange.svg)](LICENSE)

[中文版本 (Chinese)](README_ZH.md)

---

## Overview

UniArticles (亿文通) is a unified academic literature retrieval server implementing the Model Context Protocol (MCP). As of v3.4.0 it brings **9 data sources and 21 tools** — Scopus, ScienceDirect, arXiv, PubMed, Crossref, Europe PMC, DOAJ, OpenAIRE and CORE — behind a single standardized interface for LLM clients (Codex Desktop, Cherry Studio, Claude Desktop, …).
          
## Features

- **Unified Interface**: Single search structure for all sources.
- **Multi-Source Support**:
  - **Scopus**: Search, abstract details, journal/serial title lookup by ISSN, quota check.
  - **ScienceDirect**: Full-text article retrieval, article object (figures/tables/supplementary materials) metadata retrieval.
  - **ArXiv**: Search papers, list recent papers, read paper metadata by ID.
  - **PubMed (NCBI Entrez)**: Keyword search, batch summary lookup, related-article discovery, and PMC full-text/citation linkage — direct NCBI E-utilities calls (no third-party wrapper).
  - **General academic search (v3.0.0)**: Crossref, Europe PMC, DOAJ, OpenAIRE, and CORE keyword/DOI lookup across open scholarly catalogs.
- **Standardized Returns**: Consistent JSON structure (`ok`, `source`, `query`, `count`, `items`, `error`).
- **Secure Configuration**: API keys managed via environment variables.

## Supported Data Sources

UniArticles unifies the following **9 data sources** behind one consistent MCP interface, all returning the same normalized JSON shape and all active by default, providing **21 tools**. Every source except arXiv is a direct call to the provider's official REST API (via `httpx`); arXiv is wrapped through the official `arxiv` Python package.

| Data Source | Coverage | Access Method | API Key |
|---|---|---|---|
| **Scopus** | Elsevier's curated abstract & citation database spanning the sciences, social sciences, and arts & humanities. | Elsevier REST API (`api.elsevier.com`) via `httpx` | **Required** — `ELSEVIER_API_KEY` |
| **ScienceDirect** | Elsevier's full-text platform for peer-reviewed journals and books. | Elsevier REST API (`api.elsevier.com`) via `httpx` | **Required** — `ELSEVIER_API_KEY` |
| **arXiv** | Open-access preprints in physics, mathematics, computer science, quantitative biology, economics, and more. | Official [`arxiv`](https://pypi.org/project/arxiv/) Python package | Not needed |
| **PubMed** | Biomedical and life-sciences literature indexed by the US National Library of Medicine (NCBI). | NCBI Entrez E-utilities REST API (`eutils.ncbi.nlm.nih.gov`) via `httpx` | Optional — `NCBI_API_KEY` (raises rate limit only) |
| **Crossref** | DOI registration metadata across all disciplines. | Crossref REST API (`api.crossref.org`) via `httpx` | Not needed |
| **Europe PMC** | EBI's life-sciences literature aggregator (distinct from NCBI PubMed), including PMC full text. | Europe PMC REST API (`ebi.ac.uk/europepmc`) via `httpx` | Not needed |
| **DOAJ** | Directory of Open Access Journals — peer-reviewed open-access articles. | DOAJ REST API (`doaj.org/api`) via `httpx` | Not needed |
| **OpenAIRE** | European open-science aggregator of research products. | OpenAIRE REST API (`api.openaire.eu`) via `httpx` | Not needed |
| **CORE** | Global aggregator of open-access research papers from repositories and journals worldwide. | CORE v3 REST API (`api.core.ac.uk`) via `httpx` | Optional — `CORE_API_KEY` (recommended; heavy rate limit without it) |

## ⚠️ API Key Requirements

This server integrates multiple data sources, and some advanced features require API keys:

1. **Elsevier API (Scopus database, Required)**:
   - **How to get**: Apply at [Elsevier Developer Portal](https://dev.elsevier.com/).
   - **Restriction**: A basic, non-commercial Elsevier API key (no institutional subscription or Insttoken required) is sufficient to use all remaining Elsevier-related tools in this server — apply for free with a personal account at the Elsevier Developer Portal. (The 8 Elsevier-related tools have been verified against a real non-commercial key. The server currently registers **21 tools total** covering 9 data sources; the newer non-Elsevier sources do not require this key.)
   - **Clarification**: Scopus is an Elsevier database. The `ELSEVIER_API_KEY` configured here is an Elsevier API key and may also be used for other Elsevier API services allowed by your subscription and key scope. (The legacy variable name `SCOPUS_API_KEY` is still accepted for backward compatibility but is deprecated and will be removed in a future major version.)

**Note**: Even without the above API key, you can still use other functions normally.

## Installation & Usage

### Method 1: Direct Integration with LLM Clients (Recommended)
Suitable for **Cherry Studio**, **LM Studio**, **Claude Desktop**, **Trae**, etc.

**This project is published on PyPI, so you can configure it directly without downloading the full source code.**
**Since these LLM clients are already configured with Python and uv environments, no additional downloads are required.**

Simply add the following configuration to your client's MCP settings (e.g., `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "uniarticles-mcp-server": {
      "command": "uvx",
      "args": [
        "--refresh", 
        "uniarticles-mcp"
      ],
      "env": {
        "ELSEVIER_API_KEY": "your_elsevier_api_key_here",
        "ELSEVIER_INSTTOKEN": "your_elsevier_insttoken_here",
        "NCBI_API_KEY": "your_ncbi_api_key_here",
        "CORE_API_KEY": "your_core_api_key_here"
      }
    }
  }
}
```

> **About the `env` fields**: Only `ELSEVIER_API_KEY` is required (for Scopus / ScienceDirect). All the others are **optional** — if you don't have a given key, **delete that entire line** (JSON does not allow comments, and the last remaining line must not end with a comma). The optional fields are:
> - `ELSEVIER_INSTTOKEN` — only if your institution issued an Elsevier Institutional Token, for broader Elsevier access.
> - `NCBI_API_KEY` — PubMed works without it; a key only raises the rate limit from 3 to 10 requests/sec.
> - `CORE_API_KEY` — CORE works without it but is heavily rate-limited (~5 requests, then a ~10-minute lockout); a key is recommended.

If you do not want to force refresh the cache package every time you restart, then instead add the following content: (but this will cause you to need to manually update the package when the package is updated)

```json
{
  "mcpServers": {
    "uniarticles-mcp-server": {
      "command": "uvx",
      "args": [
        "uniarticles-mcp"
      ],
      "env": {
        "ELSEVIER_API_KEY": "your_elsevier_api_key_here",
        "ELSEVIER_INSTTOKEN": "your_elsevier_insttoken_here",
        "NCBI_API_KEY": "your_ncbi_api_key_here",
        "CORE_API_KEY": "your_core_api_key_here"
      }
    }
  }
}
```

📖 Troubleshooting? See: [Step-by-Step Configuration Guide](tutorial/step_by_step_guide_en.md)

If you encounter `MCP error -32000: Connection closed` when starting the service, please find the solution in the related Cherry Studio issue: https://github.com/CherryHQ/cherry-studio/issues/3264

### Method 2: Local Installation (Advanced)
Requires Python 3.10+ and [uv](https://github.com/astral-sh/uv) (recommended) or pip.
Useful for developers or those who want to modify the source code.

**Using uv:**
```bash
# Clone the repository
git clone https://github.com/your-username/UniArticles_MCPserver.git
cd UniArticles_MCPserver

# Sync dependencies and run
uv sync
uv run uniarticles-mcp
```

**Using pip:**
```bash
# Clone and setup venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Run
python -m uniarticles
```

#### Configuration

Create a `.env` file in the project root:

```env
ELSEVIER_API_KEY=your_elsevier_api_key
# Optional. Only if your institution issued an Elsevier Institutional Token
# (broader Elsevier access). Leave unset otherwise.
ELSEVIER_INSTTOKEN=your_elsevier_insttoken
# Optional. NCBI Entrez works without it; setting it only raises the PubMed
# rate limit from 3 to 10 requests/sec (free from NCBI).
NCBI_API_KEY=your_ncbi_api_key
# Optional. CORE works without it but is heavily rate-limited (~5 requests, then
# a ~10-minute lockout); setting it is recommended. Free from https://core.ac.uk/services/api
CORE_API_KEY=your_core_api_key
```

#### Project Structure

```
src/
└── uniarticles/
    ├── server.py        # MCP Server entry point
    └── sources/         # Data source modules
        ├── arxiv.py
        ├── pubmed.py
        ├── scopus.py
        └── ...
pyproject.toml           # Project metadata and dependencies
```

#### Verifying the Installation

This project does not ship a separate test suite; verify the installation by launching the server. It communicates over stdio, so on a successful start it stays running and waits silently for JSON-RPC input from a client (press `Ctrl+C` to exit):

```bash
uv run uniarticles-mcp     # if installed via uv
# or
python -m uniarticles      # if installed via pip
```

If the process starts without import or configuration errors, the installation is working.

## Available Tools

The tools are grouped below by data source, one table per source. **21 tools are registered in total**, and every one of them is available as long as its source's key (when required) is configured. Every tool returns the same normalized JSON shape (`ok`, `source`, `query`, `count`, `items`, `error`).

### Scopus

| Tool | Parameters | Description |
|---|---|---|
| `scopus_document_search_by_query` | `query`, `count`=5, `sort`="relevancy", `view`="STANDARD" | Search Scopus documents by query string. Defaults to relevance ranking, so a title query returns the paper itself rather than the newest loose matches; pass `sort="coverDate"` for date ordering. |
| `scopus_abstract_detail_by_eid` | `eid`, `view`="META" | Get a normalized abstract record (title, authors, affiliations, journal, identifiers) by EID. The abstract body is only populated under richer, subscription-gated views. |
| `scopus_serial_title_by_issn` | `issn`, `view`="STANDARD" | Look up journal/serial metadata (publisher, Open Access status, coverage years, subject areas, homepage) by ISSN. |
| `scopus_api_usage_status` | *(none)* | Check Elsevier API usage/rate-limit status (via the Scopus endpoint). |
| `scopus_serial_title_search_by_criteria` | `title`, `issn`, `pub`, `subj`, `content`, `date`, `oa`, `start`, `count`, `view`="STANDARD" (all optional) | Search journals/serials by title, publisher, subject, Open Access status, etc. (no ISSN required); results include SNIP/SJR metrics. `subj` takes a subject abbreviation (e.g. `COMP`), not a numeric code; `count` max is 200. |
| `scopus_subject_classification_lookup_by_source` | `source` (required: `scopus`/`scidir`), `description`, `detail`, `code`, `abbrev`, `field` | Look up Scopus/ScienceDirect subject classification codes to help build more precise search queries. |

### ScienceDirect

| Tool | Parameters | Description |
|---|---|---|
| `sciencedirect_article_retrieve_by_identifier` | `identifier`, `identifier_type`="pii", `view`="META" | Retrieve a normalized article record (title, authors, journal, identifiers, subjects) by identifier (pii/doi/pubmed_id/eid). |
| `sciencedirect_article_object_by_identifier` | `identifier`, `identifier_type`="doi", `view`="META" | Retrieve metadata (filename, mimetype, type, download link) for an article's figures/tables/supplementary materials. Returns the object list and links only — does not download the binary content. |

### ArXiv

| Tool | Parameters | Description |
|---|---|---|
| `arxiv_paper_search_by_query` | `query`, `max_results`=10 | Search arXiv papers by query string. |
| `arxiv_latest_paper_list_by_category` | `category` (required, e.g. `cs.AI`; comma-separate multiple like `cs.AI,cs.LG`), `max_results`=10 | List the most recently submitted papers in one or more arXiv categories. |
| `arxiv_paper_detail_by_id` | `paper_id` | Get metadata for a specific arXiv paper by ID. |

Availability note: the upstream host `export.arxiv.org` can stall. During the 2026-09-18 sweep, `arxiv_paper_detail_by_id` and `arxiv_latest_paper_list_by_category` both hung ~5 minutes and then failed with a connection timeout, while `arxiv_paper_search_by_query` returned normally from the same host in 1.4s; the stall cleared ~15 minutes later and all three tools worked again. That hang was originally unbounded, because `arxiv.Client` exposes no timeout parameter at all — only `page_size` / `delay_seconds` / `num_retries`. Since v3.4.0 the client is built with a **15-second per-request timeout plus a 45-second overall deadline**, so a stalled upstream now fails fast with one actionable error naming both limits instead of hanging. `_verify/arxiv_timeout_check.py` reproduces that behaviour offline by pointing the client at a local listener that accepts connections and never answers; if you do hit a real timeout, `_verify/arxiv_connectivity_test.py` runs a layered DNS→TCP→TLS→HTTP diagnosis to tell an upstream stall apart from a local network problem.

### PubMed (NCBI Entrez)

These tools call the NCBI E-utilities directly. They work without a key; setting the optional `NCBI_API_KEY` (free from NCBI) only raises the rate limit from 3 to 10 requests/sec.

| Tool | Parameters | Description |
|---|---|---|
| `pubmed_paper_search_by_query` | `query`, `max_results`=10 | Keyword search (ESearch + EFetch); returns normalized records (title, abstract, authors, journal, doi, pmid, pmcid, keywords, date). |
| `pubmed_paper_summary_lookup_by_pmids` | `pmids` (list) | Batch lightweight metadata lookup (ESummary); carries fields the search tool lacks (pmcid, pubstatus, pmcrefcount, elocationid). Invalid PMIDs come back as items with a per-item `error`. Max 200 per call. |
| `pubmed_related_article_search_by_pmid` | `pmid`, `max_results`=10 | Find PubMed articles topically related to a PMID (ELink "Similar articles"). Returns related PMIDs (source PMID excluded). |
| `pubmed_pmc_linkage_lookup_by_pmid` | `pmid` | Look up a PMID's PubMed Central linkages — `own_pmc_fulltext` (its own open-access PMC record, if any) and `cited_by_pmc_articles` (PMC articles citing it), kept as two distinct groups. |

### Crossref

| Tool | Parameters | Description |
|---|---|---|
| `crossref_work_search_by_query` | `query`, `max_results`=10 | Search works by keyword. No key needed. |
| `crossref_work_detail_by_doi` | `doi` | Look up a single work by DOI. No key needed. |

### Europe PMC

| Tool | Parameters | Description |
|---|---|---|
| `europepmc_paper_search_by_query` | `query`, `max_results`=10 | Search Europe PMC (EBI life-sciences aggregator, distinct from NCBI PubMed) by keyword; first page of results only. No key needed. |

### DOAJ

| Tool | Parameters | Description |
|---|---|---|
| `doaj_article_search_by_query` | `query`, `max_results`=10 | Search the Directory of Open Access Journals by keyword. No key needed. |

### OpenAIRE

| Tool | Parameters | Description |
|---|---|---|
| `openaire_research_product_search_by_query` | `query`, `max_results`=10 | Search OpenAIRE (European open science aggregator) by keyword. No key needed. |

### CORE

| Tool | Parameters | Description |
|---|---|---|
| `core_work_search_by_query` | `query`, `max_results`=10 | Search CORE (global open-access aggregator) by keyword. Works without a key but is heavily rate-limited (~5 requests then a ~10-minute lockout); configuring `CORE_API_KEY` is strongly recommended. |

## 📝 Recommended Prompt: Literature Search

The prompt below turns a vague request into a reproducible multi-source search. Paste it into any MCP client with UniArticles connected, then replace the last line with your own request. Its query-shape rules were verified against the live APIs — the probe results are in `project-docs/buildlog.md`.

On 2026-09-18 a sweep invoked every registered tool once against the live APIs. OpenAlex (the one source that kept failing that day — its search endpoint returned HTTP 429 under the upstream's anonymous-traffic rate limiting) has since been removed in v3.4.0, and the sweep was then repeated against the remaining source set: **21 tools, 21/21 succeeded**.

```text
You are my literature-search assistant. UniArticles MCP tools are connected.
Follow these four steps exactly, in order.

STEP 1 — Split my request BEFORE searching.
Restate what I need as: (a) topic or research question in one sentence;
(b) search type — breadth scan, one specific known paper, or author/venue lookup;
(c) research domain; (d) time window; (e) language; (f) how many papers is enough.

STEP 2 — Rule out the sources that certainly cannot match, and say so out loud.
Apply these rules and skip those sources without calling them:
- Topic is biomedical/life-sciences ONLY -> drop arXiv (wrong domain). Note that
  DOAJ, CORE and OpenAIRE are open-access aggregators across ALL disciplines and
  do cover biomedicine, so do not drop them on domain grounds; whether they are
  dropped depends only on the next rule.
- Topic is physics, mathematics, computer science, statistics, quantitative
  biology or economics -> arXiv is usable; ANY other domain (humanities, social
  sciences, clinical medicine) -> drop arXiv (it is preprint-only and has no
  journal coverage).
- I want peer-reviewed / mainstream / non-open-access journals -> drop DOAJ,
  CORE and OpenAIRE (open-access only, so they bias the result set).
- I want the full text or a PDF -> no UniArticles tool returns full text or
  binaries. Say this up front and keep sources only for metadata plus links.
- I want non-English (e.g. Chinese) literature -> this server indexes no Chinese
  database at all (no CNKI / Wanfang / VIP). Measured with a Chinese query such
  as "深度学习": Crossref, DOAJ and CORE return Chinese-language records, Europe
  PMC returns bracketed English translations of Chinese journal articles, Scopus
  is inconsistent (0~1 hits for the same query), and PubMed and arXiv return 0.
  State that coverage is far below a Chinese database; never claim it replaces
  CNKI or Wanfang.
- Scopus and ScienceDirect -> only usable if ELSEVIER_API_KEY is configured. If a
  call returns an auth/quota error, mark that source unavailable and continue; do
  not silently drop the requirement.
Always keep at least two sources.

STEP 3 — Search the remaining sources in this order, using these query shapes.
1. Scopus — for a known paper use TITLE("exact title"); for a topic use
   TITLE-ABS-KEY(term AND term); count 5-10.
2. Crossref — plain keyword search; also use it to confirm each DOI.
3. PubMed (biomedical only) — for a known paper use  Exact paper title[Title]
   and do NOT wrap it in quotes: the quoted form returns 0 results. Never pass
   a long natural-language sentence; stopwords such as "in" can zero the whole
   query. Put explicit AND between term groups.
4. Europe PMC — same field syntax as PubMed, e.g. TITLE:"exact title".
5. arXiv (preprint domains only) — ti:"exact title" for a known paper,
   all:term for a topic.
6. DOAJ, CORE, OpenAIRE — open-access only. DOAJ's relevance ranking is weak
   and returns off-topic hits for title-like queries, so verify every title
   before reporting it.
7. ScienceDirect — identifier lookup only (DOI/PII). It has NO search tool, so
   never try to search it.
Use 5-10 results per source. Running the same topic against several sources is
the expected pattern, not a fallback chain. Skip any source that errors and
record it.

STEP 4 — Merge and report.
Deduplicate by DOI, then by normalized title. Output ONE Markdown table,
newest first, with exactly these columns:

| Title | Published | Journal / Venue | DOI Link | Source | Summary |

- DOI Link: [10.xxxx/yyy](https://doi.org/10.xxxx/yyy); if there is no DOI,
  use the source's own URL.
- Summary: 1-2 sentences, derived ONLY from an abstract actually returned by a
  tool. If no abstract is available, write "no abstract available". Never
  invent or infer content.
- Source: the tool's `source` value; list every source that returned the paper.
After the table, list which sources you skipped and why, plus any query that
returned 0 results.

My request: <describe what you want here>
```

### Query shapes that are verified to work

| Goal | Use | Not this (returns related-but-different papers) |
|---|---|---|
| Find one known paper in Scopus | `TITLE("Attention Is All You Need")` | bare `Attention Is All You Need` |
| Find one known paper in arXiv | `ti:"Attention Is All You Need"` | bare title, even with relevance sorting |
| Find one known paper in PubMed | `Exact title[Title]` — unquoted | bare title (a stopword can zero the query), or `"title"[Title]` (returns 0) |
| Topic search in PubMed | `term AND term`, keep it short | a full natural-language sentence |

---

## 🤝 Call for Contributions

Due to the author's background in Chemistry, I am less familiar with databases and API developments in other research fields. I warmly welcome contributions and Pull Requests (PRs) from the community to add more data sources!

## ⚖️ License & Acknowledgments

### License

**Dual licensed: AGPL-3.0-or-later _or_ a commercial license**

This project is released under the **GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)** — full text in [`LICENSE`](LICENSE). You may use, modify, and redistribute it, **including for commercial purposes**, provided you comply with the AGPL: if you distribute a modified version, or expose one to users over a network, you must offer those users the corresponding source code.

💼 **Commercial licensing**:
If the AGPL's copyleft obligations do not fit your use case — for example, embedding this server in a closed-source product, or operating a modified version as a network service without publishing your changes — a separate commercial license is available from the author: wangzh685@mail2.sysu.edu.cn.

> Note: the earlier wording "AGPL-3.0 with commercial restriction" was inaccurate and has been corrected in v3.4.0. The AGPL does not restrict commercial use; what it restricts is **closed-source redistribution and closed-source network deployment**.

### Special Acknowledgments

- **[ScopusMCP](https://github.com/qwe4559999/scopus-mcp)**:
  ScopusMCP is the first literature retrieval MCP tool the author successfully developed, but initially it was quite bloated and difficult to port.Thanks to my roommate [(https://github.com/qwe4559999)](https://github.com/qwe4559999) for the suggestion to use pypi and uv for packaging.

- **[ArxivMCPserver](https://github.com/blazickjp/arxiv-mcp-server)**:
  Integrated directly from the ArxivMCPserver project.

### Special Declaration

This project uses AI-generated content.
