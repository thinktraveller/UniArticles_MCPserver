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
  - **Paperscraper APIs**: PubMed search.
- **Standardized Returns**: Consistent JSON structure (`ok`, `source`, `query`, `count`, `items`, `error`).
- **Secure Configuration**: API keys managed via environment variables.

## ⚠️ API Key Requirements

This server integrates multiple data sources, and some advanced features require API keys:

1. **Elsevier API (Scopus database, Required)**:
   - **How to get**: Apply at [Elsevier Developer Portal](https://dev.elsevier.com/).
   - **Restriction**: A basic, non-commercial Elsevier API key (no institutional subscription or Insttoken required) is sufficient to use all remaining Elsevier-related tools in this server — apply for free with a personal account at the Elsevier Developer Portal. (Verified against the current 12 tools using a real non-commercial key.)
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
        "ELSEVIER_API_KEY": "your_elsevier_api_key_here"
      }
    }
  }
}
```

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
        "ELSEVIER_API_KEY": "your_elsevier_api_key_here"
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
```

#### Project Structure

```
src/
└── uniarticles/
    ├── server.py        # MCP Server entry point
    └── sources/         # Data source modules
        ├── arxiv.py
        ├── paperscraper.py
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

### Scopus
- `scopus_document_search_by_query(query, count, sort, view)`: Search for documents.
- `scopus_abstract_detail_by_eid(eid, view)`: Get a normalized abstract record (title, authors, affiliations, journal, identifiers) by EID. The abstract body is only populated under richer, subscription-gated views.
- `scopus_serial_title_by_issn(issn, view)`: Look up journal/serial metadata (publisher, Open Access status, coverage years, subject areas, homepage) by ISSN.
- `scopus_api_usage_status()`: Check Elsevier API usage/rate-limit status (via Scopus endpoint).
- `scopus_serial_title_search_by_criteria(title, issn, pub, subj, content, date, oa, start, count, view)`: Search journals/serials by title, publisher, subject, Open Access status, etc. (multiple optional criteria, no ISSN required; results include SNIP/SJR metrics). Sibling tool to `scopus_serial_title_by_issn`. Note: `subj` takes a subject abbreviation (e.g. `COMP`) not a numeric code; `count` max is 200.
- `scopus_subject_classification_lookup_by_source(source, description, detail, code, abbrev, field)`: Look up Scopus/ScienceDirect subject classification codes to help build more precise search queries. `source` is required (`scopus` or `scidir`).

### ScienceDirect
- `sciencedirect_article_retrieve_by_identifier(identifier, identifier_type, view)`: Retrieve a normalized article record (title, authors, journal, identifiers, subjects) by identifier.
- `sciencedirect_article_object_by_identifier(identifier, identifier_type, view)`: Retrieve metadata (filename, mimetype, type, download link) for an article's figures/tables/supplementary materials. Returns the object list and links only — does not download the binary content.

### ArXiv
- `arxiv_paper_search_by_query(query, max_results)`: Search papers.
- `arxiv_latest_paper_list_by_category(category, max_results)`: List the most recently submitted papers in a given arXiv category. `category` is **required** and must be a valid arXiv category code (e.g. `cs.AI`); comma-separate multiple categories (e.g. `cs.AI,cs.LG`).
- `arxiv_paper_detail_by_id(paper_id)`: Get paper metadata.

### Paperscraper
- `pubmed_paper_search_by_query(query, max_results)`: Search papers from PubMed.

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
