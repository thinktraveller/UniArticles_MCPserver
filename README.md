# UniArticles MCP Server

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://opensource.org/licenses/AGPL-3.0)
[![Commercial-Use](https://img.shields.io/badge/Commercial-Restricted-red.svg)](LICENSE)

[中文版本 (Chinese)](README_ZH.md)

---

## Overview

UniArticles(亿文通) is a unified academic literature retrieval server implementing the Model Context Protocol (MCP). Integrates multiple scholarly databases (**Scopus**, **ArXiv**, **Semantic Scholar**) into a single, standardized API for LLM agents (like Claude).
          
## Features

- **Unified Interface**: Single search structure for all sources.
- **Multi-Source Support**:
  - **Scopus**: Search, abstract details, author profiles, quota check.
  - **ArXiv**: Search papers, search by ID, list recent papers, download PDF.
  - **Semantic Scholar**: Search papers.
- **Standardized Returns**: Consistent JSON structure (`ok`, `source`, `query`, `count`, `items`, `error`).
- **Secure Configuration**: API keys managed via environment variables.

## ⚠️ API Key Requirements

This server integrates multiple data sources, and some advanced features require API keys:

1. **Elsevier API (Scopus database, Required)**:
   - **How to get**: Apply at [Elsevier Developer Portal](https://dev.elsevier.com/).
   - **Restriction**: Your institution must have a subscription to Elsevier's services; otherwise, you cannot use related functions even with an API Key.
   - **Clarification**: Scopus is an Elsevier database. The `SCOPUS_API_KEY` configured here is an Elsevier API key and may also be used for other Elsevier API services allowed by your subscription and key scope.

2. **Semantic Scholar (Recommended)**:
   - **How to get**: Apply at [Semantic Scholar API Key Form](https://www.semanticscholar.org/product/api#api-key-form).
   - **Restriction**: Using an institutional email is recommended. Without an API Key, rate limits and results will be severely restricted.

**Note**: Even without the above API keys, you can still use other functions normally.

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
        "SCOPUS_API_KEY": "your_elsevier_api_key_here",
        "SEMANTIC_SCHOLAR_API_KEY": "your_semantic_scholar_api_key_here"
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
        "SCOPUS_API_KEY": "your_elsevier_api_key_here",
        "SEMANTIC_SCHOLAR_API_KEY": "your_semantic_scholar_api_key_here"
      }
    }
  }
}
```

📖 Troubleshooting? See: [Step-by-Step Configuration Guide](docs/step_by_step_guide_en.md)

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
SCOPUS_API_KEY=your_elsevier_api_key
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_api_key
ARXIV_DOWNLOAD_DIR=./arxiv_downloads
```

#### Project Structure

```
src/
└── uniarticles/
    ├── server.py        # MCP Server entry point
    └── sources/         # Data source modules
        ├── arxiv.py
        ├── scopus.py
        ├── semanticscholar.py
        └── ...
tests/                   # Integration and verification tests
pyproject.toml           # Project metadata and dependencies
```

#### Testing

Run automated integration tests:

```bash
python -m unittest discover tests
```

Verify MCP protocol handshake:

```bash
python tests/verify_server.py
```

## Available Tools

### Scopus
- `search_scopus(query, count, sort)`: Search for documents.
- `get_abstract_details(eid)`: Get detailed abstract information.
- `get_author_profile(author_id)`: Get author profile information.
- `get_quota_status()`: Check Elsevier API quota (via Scopus endpoint).

### ArXiv
- `search_arxiv(query, max_results)`: Search papers.
- `list_papers(max_results)`: List recent papers.
- `read_paper(paper_id)`: Get paper metadata.
- `download_paper(paper_id, filename, output_dir)`: Download PDF.

### Semantic Scholar
- `search_semantic_scholar(query, limit)`: Search papers.

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
