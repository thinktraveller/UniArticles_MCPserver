# UniArticles MCP Server

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://opensource.org/licenses/AGPL-3.0)
[![Commercial-Use](https://img.shields.io/badge/Commercial-Restricted-red.svg)](LICENSE)

[中文 (Chinese)](README_ZH.md)

---

## 🇬🇧 English

A unified academic literature retrieval server implementing the Model Context Protocol (MCP). Integrates multiple scholarly databases (**Scopus**, **ChemRxiv**, **ArXiv**, **Semantic Scholar**) into a single, standardized API for LLM agents (like Claude).

### Features

- **Unified Interface**: Single search structure for all sources.
- **Multi-Source Support**:
  - **Scopus**: Search, abstract details, author profiles, citing papers, quota check.
  - **ChemRxiv**: Search (term/title), details by ID/DOI, categories, licenses, OAI-PMH records.
  - **ArXiv**: Search papers, search by ID, list recent papers, download PDF.
  - **Semantic Scholar**: Search papers.
- **Standardized Returns**: Consistent JSON structure (`ok`, `source`, `query`, `count`, `items`, `error`).
- **Secure Configuration**: API keys managed via environment variables.

### Installation & Usage

#### Prerequisites
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (Recommended) or pip

#### Option 1: Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-username/UniArticles_MCPserver.git
cd UniArticles_MCPserver

# Sync dependencies and run
uv sync
uv run uniarticles-mcp
```

#### Option 2: Using pip

```bash
# Clone and setup venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Run
python -m uniarticles
```

#### Claude Desktop Integration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "uniarticles": {
      "command": "uv",
      "args": [
        "--directory",
        "C:/path/to/UniArticles_MCPserver",
        "run",
        "uniarticles-mcp"
      ],
      "env": {
        "SCOPUS_API_KEY": "your_key_here",
        "SEMANTIC_SCHOLAR_API_KEY": "optional_key_here"
      }
    }
  }
}
```

### Configuration

Create a `.env` file in the project root:

```env
SCOPUS_API_KEY=your_scopus_api_key
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_api_key
ARXIV_DOWNLOAD_DIR=./arxiv_downloads
```

### Project Structure

```
src/
└── uniarticles/
    ├── server.py        # MCP Server entry point
    └── sources/         # Data source modules
        ├── arxiv.py
        ├── scopus.py
        ├── chemrxiv.py
        ├── semanticscholar.py
        └── ...
tests/                   # Integration and verification tests
pyproject.toml           # Project metadata and dependencies
```

### Testing

Run automated integration tests:

```bash
python -m unittest discover tests
```

Verify MCP protocol handshake:

```bash
python tests/verify_server.py
```

### Available Tools

#### Scopus
- `search_scopus(query, count, sort)`: Search for documents.
- `get_abstract_details(eid)`: Get detailed abstract information.
- `get_author_profile(author_id)`: Get author profile information.
- `get_citing_papers(eid, count)`: Get citing papers.
- `get_quota_status()`: Check API quota.

#### ChemRxiv
- `search_chemrxiv(term, limit, page, sort)`: Search preprints.
- `search_chemrxiv_title(title, limit)`: Search by title.
- `get_chemrxiv_by_id(item_id)`: Get details by ID.
- `get_chemrxiv_by_doi(doi)`: Get details by DOI.
- `list_chemrxiv_oai_records(limit)`: List OAI-PMH records.

#### ArXiv
- `search_arxiv(query, max_results)`: Search papers.
- `list_papers(max_results)`: List recent papers.
- `read_paper(paper_id)`: Get paper metadata.
- `download_paper(paper_id, filename, output_dir)`: Download PDF.

#### Semantic Scholar
- `search_semantic_scholar(query, limit)`: Search papers.

---

## ⚖️ License & Acknowledgments / 协议与致谢

### License / 协议

**AGPL-3.0 License with Commercial Restriction**

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.
本项目采用 **GNU Affero 通用公共许可证 v3.0 (AGPL-3.0)** 授权。

🔴 **Commercial Use Restriction / 商业使用限制**:
Commercial use of this software is permitted **ONLY** with explicit written authorization from the author.
**未经作者明确书面授权，严禁将本软件用于任何商业用途**（包括但不限于销售、SaaS服务、集成到商业产品中）。

### Special Acknowledgments / 特别致谢

- **[ScopusMCP](https://github.com/qwe4559999/scopus-mcp)**:
  ScopusMCP是笔者第一个开发成功的文献检索MCP工具，但初始相当臃肿与难以抑制，感谢舍友 [(https://github.com/qwe4559999)](https://github.com/qwe4559999) 提供的使用pypi和uv打包的建议；
  *ScopusMCP was the author's first successful literature retrieval MCP tool. Thanks to my roommate for the suggestion to use pypi and uv for packaging.*

- **[ArxivMCPserver](https://github.com/blazickjp/arxiv-mcp-server)**:
  ArxivMCPserver项目，本项目直接将其进行了打包集成。
  *Integrated directly from the ArxivMCPserver project.*
