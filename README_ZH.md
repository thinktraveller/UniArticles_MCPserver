# UniArticles MCP Server

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://opensource.org/licenses/AGPL-3.0)
[![Commercial-Use](https://img.shields.io/badge/Commercial-Restricted-red.svg)](LICENSE)

[English](README.md)

---

## 🇨🇳 中文

UniArticles MCP Server 是一个实现了模型上下文协议 (MCP) 的统一学术文献检索服务器。它将多个学术数据库（**Scopus**, **ChemRxiv**, **ArXiv**, **Semantic Scholar**）集成到一个标准化的 API 中，供 LLM 智能体（如 Claude）调用。

### 功能特性

- **统一接口**: 所有数据源使用统一的返回结构。
- **多源支持**:
  - **Scopus**: 搜索、摘要详情、作者档案、引用论文、配额查询。
  - **ChemRxiv**: 搜索 (关键词/标题)、ID/DOI 详情、分类列表、许可列表、OAI-PMH 记录。
  - **ArXiv**: 论文搜索、ID 查询、最新论文列表、PDF 下载。
  - **Semantic Scholar**: 论文搜索。
- **标准化返回**: 一致的 JSON 结构 (`ok`, `source`, `query`, `count`, `items`, `error`)。
- **安全配置**: 通过环境变量管理 API 密钥。

### 安装与使用

#### 前置要求
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (推荐) 或 pip

#### 方式一：使用 uv (推荐)

```bash
# 克隆仓库
git clone https://github.com/your-username/UniArticles_MCPserver.git
cd UniArticles_MCPserver

# 同步依赖并运行
uv sync
uv run uniarticles-mcp
```

#### 方式二：使用 pip

```bash
# 克隆并设置虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 安装依赖
pip install -e .

# 运行
python -m uniarticles
```

#### 集成到 Claude Desktop

将以下配置添加到您的 `claude_desktop_config.json` 文件中：

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
        "SCOPUS_API_KEY": "您的Scopus密钥",
        "SEMANTIC_SCHOLAR_API_KEY": "可选的SemanticScholar密钥"
      }
    }
  }
}
```

### 配置说明

在项目根目录创建 `.env` 文件：

```env
SCOPUS_API_KEY=your_scopus_api_key
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_api_key
ARXIV_DOWNLOAD_DIR=./arxiv_downloads
```

### 项目结构

```
src/
└── uniarticles/
    ├── server.py        # MCP Server 入口点
    └── sources/         # 数据源模块
        ├── arxiv.py
        ├── scopus.py
        ├── chemrxiv.py
        ├── semanticscholar.py
        └── ...
tests/                   # 集成与验证测试
pyproject.toml           # 项目元数据与依赖
```

### 测试

运行自动化集成测试:

```bash
python -m unittest discover tests
```

验证 MCP 协议握手:

```bash
python tests/verify_server.py
```

### 可用工具列表

#### Scopus
- `search_scopus(query, count, sort)`: 搜索文档。
- `get_abstract_details(eid)`: 获取详细摘要信息。
- `get_author_profile(author_id)`: 获取作者档案。
- `get_citing_papers(eid, count)`: 获取引用该文的论文。
- `get_quota_status()`: 检查 API 配额。

#### ChemRxiv
- `search_chemrxiv(term, limit, page, sort)`: 搜索预印本。
- `search_chemrxiv_title(title, limit)`: 按标题搜索。
- `get_chemrxiv_by_id(item_id)`: 按 ID 获取详情。
- `get_chemrxiv_by_doi(doi)`: 按 DOI 获取详情。
- `list_chemrxiv_oai_records(limit)`: 列出 OAI-PMH 记录。

#### ArXiv
- `search_arxiv(query, max_results)`: 搜索论文。
- `list_papers(max_results)`: 列出最新论文。
- `read_paper(paper_id)`: 获取论文元数据。
- `download_paper(paper_id, filename, output_dir)`: 下载 PDF。

#### Semantic Scholar
- `search_semantic_scholar(query, limit)`: 搜索论文。

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
