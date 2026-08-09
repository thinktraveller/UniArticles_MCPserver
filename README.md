# UniArticles MCP Server

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://opensource.org/licenses/AGPL-3.0)
[![Commercial-Use](https://img.shields.io/badge/Commercial-Restricted-red.svg)](LICENSE)

[中文版本 (Chinese)](README_ZH.md)

---

## Overview

UniArticles(亿文通) is a unified academic literature retrieval server implementing the Model Context Protocol (MCP). Integrates multiple scholarly databases (**Scopus**, **ArXiv**) and literature APIs (**PubMed**) into a single, standardized API for LLM agents (like Claude).
          
## Features

- **Unified Interface**: Single search structure for all sources.
- **Multi-Source Support**:
  - **Scopus**: Search, abstract details, journal/serial title lookup by ISSN, quota check.
  - **ScienceDirect**: Full-text article retrieval, article object (figures/tables/supplementary materials) metadata retrieval.
  - **ArXiv**: Search papers, list recent papers, read paper metadata by ID.
  - **PubMed (NCBI Entrez)**: Keyword search, batch summary lookup, related-article discovery, and PMC full-text/citation linkage — direct NCBI E-utilities calls (no third-party wrapper).
  - **General academic search (v3.0.0)**: OpenAlex, Crossref, Europe PMC, DOAJ, Zenodo, HAL, OpenAIRE, dblp, Semantic Scholar, and CORE keyword/DOI lookup across open scholarly catalogs.
  - **Specialized sources (v3.0.0)**: bioRxiv/medRxiv preprint browsing by date range, and ChEMBL medicinal-chemistry bioactivity lookup by DOI.
- **Standardized Returns**: Consistent JSON structure (`ok`, `source`, `query`, `count`, `items`, `error`).
- **Secure Configuration**: API keys managed via environment variables.

## Supported Data Sources

UniArticles unifies the following **16 data sources** behind one consistent MCP interface, all returning the same normalized JSON shape. **15 are active by default**, providing **28 tools**; Semantic Scholar registers its 2 additional tools only when `SEMANTIC_SCHOLAR_API_KEY` is set, for a total of **30 tools**. Every source except arXiv is a direct call to the provider's official REST API (via `httpx`); arXiv is wrapped through the official `arxiv` Python package.

| Data Source | Coverage | Access Method | API Key |
|---|---|---|---|
| **Scopus** | Elsevier's curated abstract & citation database spanning the sciences, social sciences, and arts & humanities. | Elsevier REST API (`api.elsevier.com`) via `httpx` | **Required** — `ELSEVIER_API_KEY` |
| **ScienceDirect** | Elsevier's full-text platform for peer-reviewed journals and books. | Elsevier REST API (`api.elsevier.com`) via `httpx` | **Required** — `ELSEVIER_API_KEY` |
| **arXiv** | Open-access preprints in physics, mathematics, computer science, quantitative biology, economics, and more. | Official [`arxiv`](https://pypi.org/project/arxiv/) Python package | Not needed |
| **PubMed** | Biomedical and life-sciences literature indexed by the US National Library of Medicine (NCBI). | NCBI Entrez E-utilities REST API (`eutils.ncbi.nlm.nih.gov`) via `httpx` | Optional — `NCBI_API_KEY` (raises rate limit only) |
| **OpenAlex** | Open, cross-disciplinary catalog of scholarly works, authors, and venues. | OpenAlex REST API (`api.openalex.org`) via `httpx` | Not needed |
| **Crossref** | DOI registration metadata across all disciplines. | Crossref REST API (`api.crossref.org`) via `httpx` | Not needed |
| **Europe PMC** | EBI's life-sciences literature aggregator (distinct from NCBI PubMed), including PMC full text. | Europe PMC REST API (`ebi.ac.uk/europepmc`) via `httpx` | Not needed |
| **DOAJ** | Directory of Open Access Journals — peer-reviewed open-access articles. | DOAJ REST API (`doaj.org/api`) via `httpx` | Not needed |
| **Zenodo** | General-purpose open research repository (CERN); filtered here to publication-type records. | Zenodo REST API (`zenodo.org/api`) via `httpx` | Not needed |
| **HAL** | French/European open archive of scholarly documents. | HAL REST API (`api.archives-ouvertes.fr`) via `httpx` | Not needed |
| **OpenAIRE** | European open-science aggregator of research products. | OpenAIRE REST API (`api.openaire.eu`) via `httpx` | Not needed |
| **Semantic Scholar** | AI-powered academic graph covering all fields. | Semantic Scholar Graph API (`api.semanticscholar.org`) via `httpx` | **Required** — `SEMANTIC_SCHOLAR_API_KEY` (its tools are not registered at all without it) |
| **CORE** | Global aggregator of open-access research papers from repositories and journals worldwide. | CORE v3 REST API (`api.core.ac.uk`) via `httpx` | Optional — `CORE_API_KEY` (recommended; heavy rate limit without it) |
| **dblp** | Computer science bibliography. | dblp REST API (`dblp.org`) via `httpx` | Not needed |
| **bioRxiv / medRxiv** | Preprints in biology (bioRxiv) and health sciences (medRxiv); browse by date range. | bioRxiv REST API (`api.biorxiv.org`) via `httpx` | Not needed |
| **ChEMBL** | Manually curated bioactivity / medicinal-chemistry database; DOI lookup only. | ChEMBL REST API (`ebi.ac.uk/chembl`) via `httpx` | Not needed |

## ⚠️ API Key Requirements

This server integrates multiple data sources, and some advanced features require API keys:

1. **Elsevier API (Scopus database, Required)**:
   - **How to get**: Apply at [Elsevier Developer Portal](https://dev.elsevier.com/).
   - **Restriction**: A basic, non-commercial Elsevier API key (no institutional subscription or Insttoken required) is sufficient to use all remaining Elsevier-related tools in this server — apply for free with a personal account at the Elsevier Developer Portal. (The 8 Elsevier-related tools have been verified against a real non-commercial key. As of v3.1.0 the server registers **28 tools total** covering 15 data sources when `SEMANTIC_SCHOLAR_API_KEY` is not configured, or **30 tools** when it is; the newer non-Elsevier sources do not require this key.)
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
        "CORE_API_KEY": "your_core_api_key_here",
        "SEMANTIC_SCHOLAR_API_KEY": "your_semantic_scholar_api_key_here"
      }
    }
  }
}
```

> **About the `env` fields**: Only `ELSEVIER_API_KEY` is required (for Scopus / ScienceDirect). All the others are **optional** — if you don't have a given key, **delete that entire line** (JSON does not allow comments, and the last remaining line must not end with a comma). The optional fields are:
> - `ELSEVIER_INSTTOKEN` — only if your institution issued an Elsevier Institutional Token, for broader Elsevier access.
> - `NCBI_API_KEY` — PubMed works without it; a key only raises the rate limit from 3 to 10 requests/sec.
> - `CORE_API_KEY` — CORE works without it but is heavily rate-limited (~5 requests, then a ~10-minute lockout); a key is recommended.
> - `SEMANTIC_SCHOLAR_API_KEY` — without it the Semantic Scholar tools are **not registered at all** (its keyword search is unusable without a key).

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
        "CORE_API_KEY": "your_core_api_key_here",
        "SEMANTIC_SCHOLAR_API_KEY": "your_semantic_scholar_api_key_here"
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
# Optional. Without it the Semantic Scholar tools are NOT registered at all
# (its keyword search is unusable without a key).
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_api_key
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

The tools are grouped below by data source, one table per source. **28 tools are registered by default**; configuring `SEMANTIC_SCHOLAR_API_KEY` adds the 2 Semantic Scholar tools for a total of **30**. Every tool returns the same normalized JSON shape (`ok`, `source`, `query`, `count`, `items`, `error`).

### Scopus

| Tool | Parameters | Description |
|---|---|---|
| `scopus_document_search_by_query` | `query`, `count`=5, `sort`="coverDate", `view`="STANDARD" | Search Scopus documents by query string. |
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

### PubMed (NCBI Entrez)

These tools call the NCBI E-utilities directly. They work without a key; setting the optional `NCBI_API_KEY` (free from NCBI) only raises the rate limit from 3 to 10 requests/sec.

| Tool | Parameters | Description |
|---|---|---|
| `pubmed_paper_search_by_query` | `query`, `max_results`=10 | Keyword search (ESearch + EFetch); returns normalized records (title, abstract, authors, journal, doi, pmid, pmcid, keywords, date). |
| `pubmed_paper_summary_lookup_by_pmids` | `pmids` (list) | Batch lightweight metadata lookup (ESummary); carries fields the search tool lacks (pmcid, pubstatus, pmcrefcount, elocationid). Invalid PMIDs come back as items with a per-item `error`. Max 200 per call. |
| `pubmed_related_article_search_by_pmid` | `pmid`, `max_results`=10 | Find PubMed articles topically related to a PMID (ELink "Similar articles"). Returns related PMIDs (source PMID excluded). |
| `pubmed_pmc_linkage_lookup_by_pmid` | `pmid` | Look up a PMID's PubMed Central linkages — `own_pmc_fulltext` (its own open-access PMC record, if any) and `cited_by_pmc_articles` (PMC articles citing it), kept as two distinct groups. |

### OpenAlex

| Tool | Parameters | Description |
|---|---|---|
| `openalex_work_search_by_query` | `query`, `max_results`=10 | Search works by keyword (abstract reconstructed to readable text). No key needed. |
| `openalex_work_detail_by_doi` | `doi` | Look up a single work by DOI. No key needed. |

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

### Zenodo

| Tool | Parameters | Description |
|---|---|---|
| `zenodo_record_search_by_query` | `query`, `max_results`=10 | Search Zenodo for publication-type records by keyword (datasets/software excluded); returns file metadata/links only. No key needed. |

### HAL

| Tool | Parameters | Description |
|---|---|---|
| `hal_document_search_by_query` | `query`, `max_results`=10 | Search HAL (French/European open archive) by keyword. No key needed. |

### OpenAIRE

| Tool | Parameters | Description |
|---|---|---|
| `openaire_research_product_search_by_query` | `query`, `max_results`=10 | Search OpenAIRE (European open science aggregator) by keyword. No key needed. |

### Semantic Scholar

**These two tools are registered only when `SEMANTIC_SCHOLAR_API_KEY` is configured** — without a key, Semantic Scholar's keyword search fails deterministically, so no tool from this source is exposed at all.

| Tool | Parameters | Description |
|---|---|---|
| `semantic_scholar_paper_search_by_query` | `query`, `max_results`=10 | Search Semantic Scholar by keyword. |
| `semantic_scholar_paper_detail_by_doi` | `doi` | Look up a paper by DOI. |

### CORE

| Tool | Parameters | Description |
|---|---|---|
| `core_work_search_by_query` | `query`, `max_results`=10 | Search CORE (global open-access aggregator) by keyword. Works without a key but is heavily rate-limited (~5 requests then a ~10-minute lockout); configuring `CORE_API_KEY` is strongly recommended. |

### dblp

| Tool | Parameters | Description |
|---|---|---|
| `dblp_publication_search_by_query` | `query`, `max_results`=10 | Search dblp (computer science bibliography) by keyword. No key needed. Note: dblp.org may fail intermittently due to network path variance in some environments. |

### bioRxiv / medRxiv

| Tool | Parameters | Description |
|---|---|---|
| `biorxiv_paper_list_by_date_range` | `server` (`biorxiv`/`medrxiv`), `start_date` (YYYY-MM-DD), `end_date` (YYYY-MM-DD), `cursor`=0 | Browse bioRxiv/medRxiv preprints within a date range (**browse by date, NOT keyword search**). 30 results per page (use `cursor` to page). |

### ChEMBL

| Tool | Parameters | Description |
|---|---|---|
| `chembl_bioactivity_lookup_by_doi` | `doi` (required) | Look up whether a paper (by DOI) is indexed in ChEMBL and, if so, its structured SAR/bioactivity data (**`doi` required, NOT keyword search**). Most papers are not in ChEMBL; `collected=false` is a normal result. |

---

## 🤝 Call for Contributions

Due to the author's background in Chemistry, I am less familiar with databases and API developments in other research fields. I warmly welcome contributions and Pull Requests (PRs) from the community to add more data sources!

## ⚖️ License & Acknowledgments

### License

**AGPL-3.0 License with Commercial Restriction**

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

🔴 **Commercial Use Restriction**:
Commercial use of this software is permitted **ONLY** with explicit written authorization from the author.

### Special Acknowledgments

- **[ScopusMCP](https://github.com/qwe4559999/scopus-mcp)**:
  ScopusMCP is the first literature retrieval MCP tool the author successfully developed, but initially it was quite bloated and difficult to port.Thanks to my roommate [(https://github.com/qwe4559999)](https://github.com/qwe4559999) for the suggestion to use pypi and uv for packaging.

- **[ArxivMCPserver](https://github.com/blazickjp/arxiv-mcp-server)**:
  Integrated directly from the ArxivMCPserver project.

### Special Declaration

This project uses AI-generated content.
