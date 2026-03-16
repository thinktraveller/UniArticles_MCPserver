# UniArticles MCP Server

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://opensource.org/licenses/AGPL-3.0)
[![Commercial-Use](https://img.shields.io/badge/Commercial-Restricted-red.svg)](LICENSE)

[English Version](README.md)

---

## 总览

亿文通（UniArticles）是一个实现了模型上下文协议 (MCP) 的统一学术文献检索服务器。它将多个学术数据库（**Scopus**, **ArXiv**, **Semantic Scholar**）集成到一个标准化的 API 中，供 LLM 智能体（如 Claude）调用。

## 功能特性

- **统一接口**: 所有数据源使用统一的返回结构。
- **多源支持**:
  - **Scopus**: 搜索、摘要详情、作者档案、配额查询。
  - **ArXiv**: 论文搜索、ID 查询、最新论文列表、PDF 下载。
  - **Semantic Scholar**: 论文搜索。
- **标准化返回**: 一致的 JSON 结构 (`ok`, `source`, `query`, `count`, `items`, `error`)。
- **安全配置**: 通过环境变量管理 API 密钥。

## ⚠️ API 密钥说明

本服务器集成多个数据源，部分高级功能需要 API 密钥支持：

1. **Elsevier API（Scopus 数据库，必需）**:
   - **获取方式**: 需前往 [Elsevier Developer Portal](https://dev.elsevier.com/) 申请。
   - **限制**: 您的机构必须购买了 Elsevier 的相关数据库服务，否则无法申请 API Key ，亦无法使用相关功能。
   - **说明**: Scopus 是 Elsevier 旗下数据库。此处配置项名为 `SCOPUS_API_KEY`，但其本质是 Elsevier API Key，在订阅权限与密钥作用域允许的前提下，也可用于其他 Elsevier API 服务。

2. **Semantic Scholar (建议)**:
   - **获取方式**: 需前往 [Semantic Scholar API Key Form](https://www.semanticscholar.org/product/api#api-key-form) 申请。
   - **限制**: 建议使用教育机构邮箱申请（即使拥有，您的申请也可能像笔者一样被拒绝）。如无 API Key，功能调用频率和返回结果将大幅受限。

**注意**: 即使您没有上述 API 密钥，您仍然可以正常使用其他相关功能。

## 安装与使用

### 方法一：直接集成到 LLM 客户端（推荐）
适用于 **Cherry Studio**、**LM Studio**、**Claude Desktop**、**Trae** 等。

**本项目已发布至 PyPI，您无需下载完整项目源码，直接通过配置即可使用。**
**由于上述 LLM 客户端通常内置了 Python 和 uv 环境，您无需额外下载**，只需在客户端的 MCP 配置文件（如 `claude_desktop_config.json`）中添加以下内容即可：

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

如果您不希望每次重启时强制刷新缓存包，则改为添加以下内容：（但这会导致包更新时您需要对包进行手动更新）

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

📖 **如果您在该方法下遇见了任何问题，详见：[傻瓜式配置攻略](docs/step_by_step_guide_zh.md)**

### 方法二：本地安装（高级）
需要 Python 3.10+ 和 [uv](https://github.com/astral-sh/uv) (推荐) 或 pip。
此方法适合开发者或需要手动配置环境的用户。

**使用 uv:**
```bash
# 克隆仓库
git clone https://github.com/your-username/UniArticles_MCPserver.git
cd UniArticles_MCPserver

# 同步依赖并运行
uv sync
uv run uniarticles-mcp
```

**使用 pip:**
```bash
# 克隆并设置虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 安装依赖
pip install -e .

# 运行
python -m uniarticles
```

#### 配置说明

在项目根目录创建 `.env` 文件：

```env
SCOPUS_API_KEY=your_elsevier_api_key
SEMANTIC_SCHOLAR_API_KEY=your_semantic_scholar_api_key
ARXIV_DOWNLOAD_DIR=./arxiv_downloads
```

#### 项目结构

```
src/
└── uniarticles/
    ├── server.py        # MCP Server 入口点
    └── sources/         # 数据源模块
        ├── arxiv.py
        ├── scopus.py
        ├── semanticscholar.py
        └── ...
tests/                   # 集成与验证测试
pyproject.toml           # 项目元数据与依赖
```

#### 测试

运行自动化集成测试:

```bash
python -m unittest discover tests
```

验证 MCP 协议握手:

```bash
python tests/verify_server.py
```

## 可用工具列表

### Scopus
- `search_scopus(query, count, sort)`: 搜索文档。
- `get_abstract_details(eid)`: 获取详细摘要信息。
- `get_author_profile(author_id)`: 获取作者档案。
- `get_quota_status()`: 检查 Elsevier API 配额（通过 Scopus 端点）。

### ArXiv
- `search_arxiv(query, max_results)`: 搜索论文。
- `list_papers(max_results)`: 列出最新论文。
- `read_paper(paper_id)`: 获取论文元数据。
- `download_paper(paper_id, filename, output_dir)`: 下载 PDF。

### Semantic Scholar
- `search_semantic_scholar(query, limit)`: 搜索论文。

---

## 🤝 贡献与共建

囿于笔者主修化学方向，对其他研究方向的数据库及API开发情况不甚了解，欢迎有志之士提出PR、贡献其他数据源。

## ⚖️ 协议与致谢

### 协议

**AGPL-3.0 License with Commercial Restriction**
本项目采用 **GNU Affero 通用公共许可证 v3.0 (AGPL-3.0)** 授权。

🔴 **商业使用限制**:
**未经作者明确书面授权，严禁将本软件用于任何商业用途**（包括但不限于销售、集成到商业产品中）。

###  特别致谢

- **[ScopusMCP](https://github.com/qwe4559999/scopus-mcp)**:
  ScopusMCP是笔者第一个开发成功的文献检索MCP工具，但初始相当臃肿与难以移植，感谢舍友 [(https://github.com/qwe4559999)](https://github.com/qwe4559999) 提供的使用pypi和uv打包的建议。
- **[ArxivMCPserver](https://github.com/blazickjp/arxiv-mcp-server)**:
  ArxivMCPserver项目，本项目直接将其进行了打包集成。

### 特别声明

本项目使用了人工智能生成内容。
