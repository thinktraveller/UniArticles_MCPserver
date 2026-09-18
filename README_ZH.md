# UniArticles MCP Server

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://opensource.org/licenses/AGPL-3.0)
[![Commercial-Use](https://img.shields.io/badge/Commercial-Restricted-red.svg)](LICENSE)

[English Version](README.md)

---

## 总览

亿文通（UniArticles）是一个实现了模型上下文协议 (MCP) 的统一学术文献检索服务器。它将多个学术数据库（**Scopus**, **ArXiv**）和文献 API（**PubMed**）集成到一个标准化的 API 中，供 LLM 智能体（如 Claude）调用。

## 功能特性

- **统一接口**: 所有数据源使用统一的返回结构。
- **多源支持**:
  - **Scopus**: 搜索、摘要详情、按 ISSN 查询期刊信息、配额查询。
  - **ScienceDirect**: 全文文章检索、文章对象（配图/表格/补充材料）元信息获取。
  - **ArXiv**: 论文搜索、最新论文列表、按 ID 读取论文元数据。
  - **PubMed（NCBI Entrez）**: 关键词检索、批量摘要查询、相关文献发现、PMC 全文/引用关联——直连 NCBI E-utilities（不再依赖第三方封装包）。
  - **通用学术检索（v3.0.0）**: OpenAlex、Crossref、Europe PMC、DOAJ、OpenAIRE、CORE 的关键词/DOI 检索，覆盖多个开放学术目录。
- **标准化返回**: 一致的 JSON 结构 (`ok`, `source`, `query`, `count`, `items`, `error`)。
- **安全配置**: 通过环境变量管理 API 密钥。

## 当前支持的文献数据源

亿文通将以下 **10 个数据源**统一到同一套 MCP 接口下，全部返回相同的归一化 JSON 结构，且全部默认启用，共提供 **23 个工具**。除 arXiv 通过官方 `arxiv` Python 包封装外，其余每个数据源都是通过 `httpx` 直连该服务商的官方 REST API。

| 数据源 | 覆盖范围 | 接入方式 | API Key |
|---|---|---|---|
| **Scopus** | Elsevier 精选的摘要与引文数据库，覆盖自然科学、社会科学、艺术与人文。 | Elsevier REST API（`api.elsevier.com`），经 `httpx` 直连 | **必需** —— `ELSEVIER_API_KEY` |
| **ScienceDirect** | Elsevier 的同行评审期刊与图书全文平台。 | Elsevier REST API（`api.elsevier.com`），经 `httpx` 直连 | **必需** —— `ELSEVIER_API_KEY` |
| **arXiv** | 物理、数学、计算机科学、定量生物、经济学等领域的开放预印本。 | 官方 [`arxiv`](https://pypi.org/project/arxiv/) Python 包封装 | 无需 |
| **PubMed** | 美国国立医学图书馆（NCBI）收录的生物医学与生命科学文献。 | NCBI Entrez E-utilities REST API（`eutils.ncbi.nlm.nih.gov`），经 `httpx` 直连 | 可选 —— `NCBI_API_KEY`（仅提升限速） |
| **OpenAlex** | 开放、跨学科的学术成果/作者/期刊目录。 | OpenAlex REST API（`api.openalex.org`），经 `httpx` 直连 | 无需 |
| **Crossref** | 覆盖所有学科的 DOI 注册元数据。 | Crossref REST API（`api.crossref.org`），经 `httpx` 直连 | 无需 |
| **Europe PMC** | EBI 的生命科学文献聚合库（区别于 NCBI PubMed），含 PMC 全文。 | Europe PMC REST API（`ebi.ac.uk/europepmc`），经 `httpx` 直连 | 无需 |
| **DOAJ** | 开放获取期刊目录（Directory of Open Access Journals）中的同行评审文章。 | DOAJ REST API（`doaj.org/api`），经 `httpx` 直连 | 无需 |
| **OpenAIRE** | 欧洲开放科学研究成果聚合库。 | OpenAIRE REST API（`api.openaire.eu`），经 `httpx` 直连 | 无需 |
| **CORE** | 汇聚全球仓储与期刊的开放获取论文聚合库。 | CORE v3 REST API（`api.core.ac.uk`），经 `httpx` 直连 | 可选 —— `CORE_API_KEY`（建议配置，无 Key 限流严格） |

## ⚠️ API 密钥说明

本服务器集成多个数据源，部分高级功能需要 API 密钥支持：

1. **Elsevier API（Scopus 数据库，必需）**:
   - **获取方式**: 需前往 [Elsevier Developer Portal](https://dev.elsevier.com/) 申请。
   - **限制**: 非商业性质、无机构订阅/Insttoken 的基础级 Elsevier API Key 即可让本服务器当前保留的全部 Elsevier 相关工具正常工作——可在 Elsevier Developer Portal 用个人账号免费申请。（其中 8 个 Elsevier 相关工具已用真实的非商业 Key 实测验证。本服务器当前共注册 **23 个工具**、覆盖 10 个数据源；非 Elsevier 数据源均不需要此 Key。）
   - **说明**: Scopus 是 Elsevier 旗下数据库。此处配置项名为 `ELSEVIER_API_KEY`，其本质是 Elsevier API Key，在订阅权限与密钥作用域允许的前提下，也可用于其他 Elsevier API 服务。（旧变量名 `SCOPUS_API_KEY` 仍向后兼容可用，但已弃用，将在未来主版本中移除。）

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
        "ELSEVIER_API_KEY": "your_elsevier_api_key_here",
        "ELSEVIER_INSTTOKEN": "your_elsevier_insttoken_here",
        "NCBI_API_KEY": "your_ncbi_api_key_here",
        "CORE_API_KEY": "your_core_api_key_here"
      }
    }
  }
}
```

> **关于 `env` 字段**：只有 `ELSEVIER_API_KEY` 是必需的（用于 Scopus / ScienceDirect），其余全部为**可选项**——如果您没有某个 Key，请**整行删除**（JSON 不支持注释，且删除后剩下的最后一行末尾不能带逗号）。各可选字段说明：
> - `ELSEVIER_INSTTOKEN` —— 仅当您的机构签发了 Elsevier 机构令牌（Insttoken）时填写，用于访问更多 Elsevier 数据。
> - `NCBI_API_KEY` —— PubMed 无此 Key 也能用；配置后仅将限速从 3 请求/秒提升到 10 请求/秒。
> - `CORE_API_KEY` —— CORE 无此 Key 也能用，但限流严格（约 5 次请求后锁定约 10 分钟），建议配置。

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
        "ELSEVIER_API_KEY": "your_elsevier_api_key_here",
        "ELSEVIER_INSTTOKEN": "your_elsevier_insttoken_here",
        "NCBI_API_KEY": "your_ncbi_api_key_here",
        "CORE_API_KEY": "your_core_api_key_here"
      }
    }
  }
}
```

📖 **如果您在该方法下遇见了任何问题，详见：[傻瓜式配置攻略](tutorial/step_by_step_guide_zh.md)**

如果您在启动服务时遇到 “MCP error -32000: Connection closed” 错误，请在 Cherry Studio 项目的该issue界面寻找解决方法：https://github.com/CherryHQ/cherry-studio/issues/3264

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
ELSEVIER_API_KEY=your_elsevier_api_key
# 可选。仅当您的机构签发了 Elsevier 机构令牌（Insttoken）时填写，用于访问
# 更多 Elsevier 数据；否则请留空/删除此行。
ELSEVIER_INSTTOKEN=your_elsevier_insttoken
# 可选。NCBI Entrez 无此 Key 也可用；配置后仅将 PubMed 限速从 3 请求/秒
# 提升到 10 请求/秒（NCBI 免费申请）。
NCBI_API_KEY=your_ncbi_api_key
# 可选。CORE 无此 Key 也可用，但限流严格（约 5 次请求后锁定约 10 分钟），
# 建议配置。免费申请：https://core.ac.uk/services/api
CORE_API_KEY=your_core_api_key
```

#### 项目结构

```
src/
└── uniarticles/
    ├── server.py        # MCP Server 入口点
    └── sources/         # 数据源模块
        ├── arxiv.py
        ├── pubmed.py
        ├── scopus.py
        └── ...
pyproject.toml           # 项目元数据与依赖
```

#### 验证安装

本项目未附带独立的测试套件；请通过启动服务来验证安装是否成功。服务通过 stdio 通信，启动成功后会保持运行并静默等待客户端发来的 JSON-RPC 输入（按 `Ctrl+C` 退出）：

```bash
uv run uniarticles-mcp     # 使用 uv 安装时
# 或
python -m uniarticles      # 使用 pip 安装时
```

若进程启动过程中没有出现导入或配置错误，即表示安装正常。

## 可用工具列表

以下工具按数据源分组，每个数据源一张表格。**共注册 23 个工具**，只要对应数据源的 Key（如有要求）已配置即可全部使用。每个工具都返回相同的归一化 JSON 结构（`ok`、`source`、`query`、`count`、`items`、`error`）。

### Scopus

| 工具名 | 参数 | 说明 |
|---|---|---|
| `scopus_document_search_by_query` | `query`、`count`=5、`sort`="relevancy"、`view`="STANDARD" | 按查询串搜索 Scopus 文档。默认按相关度排序，因此用标题检索能直接返回目标文献本身，而不是最新的松散匹配；如需按日期排序请显式传 `sort="coverDate"`。 |
| `scopus_abstract_detail_by_eid` | `eid`、`view`="META" | 按 EID 获取归一化的摘要记录（标题、作者、机构、期刊、标识符）。摘要正文仅在更高级别、受订阅限制的视图下才会返回。 |
| `scopus_serial_title_by_issn` | `issn`、`view`="STANDARD" | 按 ISSN 查询期刊/连续出版物元数据（出版商、Open Access 状态、收录年份、学科领域、期刊主页）。 |
| `scopus_api_usage_status` | *（无）* | 检查 Elsevier API 用量/速率限制状态（通过 Scopus 端点）。 |
| `scopus_serial_title_search_by_criteria` | `title`、`issn`、`pub`、`subj`、`content`、`date`、`oa`、`start`、`count`、`view`="STANDARD"（均可选） | 按期刊名、出版商、学科、Open Access 状态等多个可选条件搜索期刊/连续出版物（无需 ISSN），结果含 SNIP/SJR 计量指标。`subj` 需传学科缩写（如 `COMP`）而非数字代码；`count` 上限为 200。 |
| `scopus_subject_classification_lookup_by_source` | `source`（必填：`scopus`/`scidir`）、`description`、`detail`、`code`、`abbrev`、`field` | 查询 Scopus/ScienceDirect 学科分类代码，用于构造更精确的检索查询。 |

### ScienceDirect

| 工具名 | 参数 | 说明 |
|---|---|---|
| `sciencedirect_article_retrieve_by_identifier` | `identifier`、`identifier_type`="pii"、`view`="META" | 按标识符（pii/doi/pubmed_id/eid）检索归一化的文章记录（标题、作者、期刊、标识符、主题）。 |
| `sciencedirect_article_object_by_identifier` | `identifier`、`identifier_type`="doi"、`view`="META" | 获取某篇文章的配图/表格/补充材料的元信息（文件名、MIME 类型、对象类型、下载链接）。仅返回对象清单与链接，不下载二进制内容本身。 |

### ArXiv

| 工具名 | 参数 | 说明 |
|---|---|---|
| `arxiv_paper_search_by_query` | `query`、`max_results`=10 | 按查询串搜索 arXiv 论文。 |
| `arxiv_latest_paper_list_by_category` | `category`（必填，如 `cs.AI`；多个用逗号分隔如 `cs.AI,cs.LG`）、`max_results`=10 | 列出指定 arXiv 分类下最新提交的论文。 |
| `arxiv_paper_detail_by_id` | `paper_id` | 按 ID 获取指定 arXiv 论文的元数据。 |

### PubMed（NCBI Entrez）

以下工具直连 NCBI E-utilities。无 Key 即可使用；配置可选的 `NCBI_API_KEY`（NCBI 免费申请）仅将限速从 3 请求/秒提升到 10 请求/秒。

| 工具名 | 参数 | 说明 |
|---|---|---|
| `pubmed_paper_search_by_query` | `query`、`max_results`=10 | 按关键词检索（ESearch + EFetch），返回归一化记录（标题、摘要、作者、期刊、doi、pmid、pmcid、关键词、日期）。 |
| `pubmed_paper_summary_lookup_by_pmids` | `pmids`（列表） | 对一批 PMID 做轻量元数据批量查询（ESummary），含检索工具没有的字段（pmcid、pubstatus、pmcrefcount、elocationid）。无效 PMID 会作为带 `error` 字段的条目返回。单次上限 200 个。 |
| `pubmed_related_article_search_by_pmid` | `pmid`、`max_results`=10 | 查询与某 PMID 主题相关的 PubMed 文献（ELink“相似文献”），返回相关 PMID 列表（已剔除该 PMID 自身）。 |
| `pubmed_pmc_linkage_lookup_by_pmid` | `pmid` | 查询某 PMID 的 PubMed Central 关联——`own_pmc_fulltext`（其自身的开放获取 PMC 记录，若有）与 `cited_by_pmc_articles`（引用它的 PMC 文章），两组明确区分。 |

### OpenAlex

| 工具名 | 参数 | 说明 |
|---|---|---|
| `openalex_work_search_by_query` | `query`、`max_results`=10 | 按关键词检索文献（摘要已从倒排索引重建为可读文本）。无需 Key。**已知风险**：该端点会偶发 HTTP 429（上游在搜索集群高负载时限流匿名检索，响应含 `retry-after`），等待约 30 秒重试通常即可成功；同一时刻按 DOI 查询的 `openalex_work_detail_by_doi` 不受影响。 |
| `openalex_work_detail_by_doi` | `doi` | 按 DOI 查询单篇文献。无需 Key。 |

### Crossref

| 工具名 | 参数 | 说明 |
|---|---|---|
| `crossref_work_search_by_query` | `query`、`max_results`=10 | 按关键词检索文献。无需 Key。 |
| `crossref_work_detail_by_doi` | `doi` | 按 DOI 查询单篇文献。无需 Key。 |

### Europe PMC

| 工具名 | 参数 | 说明 |
|---|---|---|
| `europepmc_paper_search_by_query` | `query`、`max_results`=10 | 检索 Europe PMC（EBI 生命科学聚合库，区别于 NCBI PubMed），仅返回首页结果。无需 Key。 |

### DOAJ

| 工具名 | 参数 | 说明 |
|---|---|---|
| `doaj_article_search_by_query` | `query`、`max_results`=10 | 检索开放获取期刊目录（DOAJ）。无需 Key。 |

### OpenAIRE

| 工具名 | 参数 | 说明 |
|---|---|---|
| `openaire_research_product_search_by_query` | `query`、`max_results`=10 | 检索 OpenAIRE（欧洲开放科学聚合库）。无需 Key。 |

### CORE

| 工具名 | 参数 | 说明 |
|---|---|---|
| `core_work_search_by_query` | `query`、`max_results`=10 | 按关键词检索 CORE（全球开放获取聚合库）。无 Key 亦可用但限流严格（约 5 次请求后锁定约 10 分钟），**建议配置 `CORE_API_KEY`** 以获得完整体验。 |

## 📝 推荐提示词：文献查找

下面这段提示词把一句模糊的需求变成可复现的多源检索。把它粘贴到任意已接入 UniArticles 的 MCP 客户端，然后替换最后一行的需求描述即可。其中关于「查询写法」的规则均经过真实接口验证，探测结果见 `project-docs/buildlog.md`。

同一日（2026-09-18）对当前注册的全部 **23 个工具**做了逐一真实调用验证，**23/23 成功**；当时唯一的可用性风险点是 OpenAlex 检索端点的 429，已写入下方第 3 步与上方数据源小节。

```text
你是一名文献检索助手，已接入 UniArticles 的 MCP 工具。
请严格按以下四步依次执行，不要跳步。

第一步 —— 检索之前，先拆分我的需求。
用一句话复述我到底要什么，并拆出以下要素：
（a）主题/研究问题；（b）检索类型：广泛扫描 / 定位某一篇已知文献 / 按作者或期刊查找；
（c）学科领域；（d）时间窗口；（e）语言；（f）需要多少篇算够用。

第二步 —— 判断哪些数据源「一定不匹配」，并明确告诉我。
按以下规则直接跳过，不要调用这些源：
- 主题仅属生物医学/生命科学 —— 排除 arXiv（学科不对口）。注意 DOAJ、CORE、
  OpenAIRE 是全学科的开放获取聚合源，生物医学一样覆盖，不要按学科排除它们；
  它们是否该排除只取决于下一条。
- 主题属物理、数学、计算机、统计、定量生物学、经济学 —— arXiv 可用；
  其他学科（人文社科、临床医学等）—— 排除 arXiv（它只有预印本，没有期刊覆盖）。
- 我要找同行评审 / 主流期刊 / 非开放获取的文献 —— 排除 DOAJ、CORE、OpenAIRE
  （三者只收开放获取内容，会把结果集带偏）。
- 我要全文或 PDF —— UniArticles 的任何工具都不返回全文或二进制文件。
  请先说明这一点，然后只把各源用作「元数据 + 链接」。
- 我要非英文（如中文）文献 —— 本服务器不收录 CNKI / 万方 / 维普，没有任何中文
  数据库源。实测「深度学习」这类中文查询：Crossref、DOAJ、CORE 能返回中文题录，
  Europe PMC 返回中文期刊的英译题录（标题带方括号），Scopus 命中不稳定（同一查询
  0~1 条），PubMed 与 arXiv 为 0 条。请如实说明覆盖率远低于中文数据库，不要声称
  可以替代 CNKI/万方。
- Scopus、ScienceDirect —— 仅在 `ELSEVIER_API_KEY` 已配置时可用。若调用返回授权/
  配额错误，把该源标记为「不可用」后继续，不要悄悄放弃这部分需求。
无论如何至少保留两个数据源。

第三步 —— 在剩下的数据源中按以下顺序检索，并遵循对应的查询写法。
1. Scopus —— 定位已知文献用 TITLE("完整标题")；主题检索用
   TITLE-ABS-KEY(词 AND 词)；count 取 5–10。
2. OpenAlex —— 普通关键词检索（该源不支持字段语法）。若返回 HTTP 429，
   等约 30 秒后重试一次：搜索集群在高负载时会限流匿名检索，
   但它的 DOI 详情接口仍可用。
3. Crossref —— 普通关键词检索；同时用它核对每篇文献的 DOI。
4. PubMed（仅生物医学）—— 定位已知文献用  完整标题[Title]，且不要加引号，
   加了引号反而返回 0 条。不要直接传一长句自然语言：诸如 "in" 这类停用词
   会让整条查询归零。多个词组之间请显式使用 AND。
5. Europe PMC —— 字段语法与 PubMed 一致，例如 TITLE:"完整标题"。
6. arXiv（仅限预印本学科）—— 定位已知文献用 ti:"完整标题"；主题检索用 all:词。
7. DOAJ、CORE、OpenAIRE —— 仅开放获取。DOAJ 的相关度排序偏弱，
   用标题式查询会返回明显离题的结果，因此每一条都必须先核对标题再写进结果。
8. ScienceDirect —— 只能按标识符查询（DOI/PII），它没有检索工具，不要试图检索。
每个源取 5–10 条。同一主题在多个源各查一遍是预期用法，而不是「失败后降级」。
任何源报错就跳过，并记录下来。

第四步 —— 汇总成表并汇报。
先按 DOI 去重，再按归一化标题去重。只输出一张 Markdown 表格，按发表时间由新到旧：

| 文献标题 | 标题翻译 | 发表时间 | 期刊/会议 | DOI 链接 | 文献源 | 内容介绍 |

- 标题翻译：把文献标题翻译成中文；若原标题已是中文，此列填「—」。
- DOI 链接：[10.xxxx/yyy](https://doi.org/10.xxxx/yyy) 格式；若无 DOI，则给出该源的原始链接。
- 内容介绍：1–2 句，且只能依据工具真实返回的摘要撰写。
  没有摘要时写「无摘要」，严禁自行编造或推测内容。
- 文献源：填工具返回的 `source` 值；同一篇文献被多个源命中时全部列出。
表格之后，再列出：跳过了哪些源及原因，以及哪些查询返回了 0 条结果。

我的需求：<在这里写下你要查找的内容>
```

### 已实测验证的查询写法

| 目标 | 应该这样写 | 不要这样写（只会得到「相关但不同」的文献） |
|---|---|---|
| 在 Scopus 定位某一篇已知文献 | `TITLE("Attention Is All You Need")` | 裸标题 `Attention Is All You Need` |
| 在 arXiv 定位某一篇已知文献 | `ti:"Attention Is All You Need"` | 裸标题（即使按相关度排序也不行） |
| 在 PubMed 定位某一篇已知文献 | `完整标题[Title]`，不加引号 | 裸标题（停用词会让查询归零），或 `"标题"[Title]`（返回 0 条） |
| 在 PubMed 做主题检索 | `词 AND 词`，保持简短 | 一整句自然语言 |

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
