# UniArticles（亿文通）MCP Server v2.0 构建计划书

## 项目概述

- **项目目标**：在 v1.x（当前 `pyproject.toml` 版本号 1.5.0，已收尾）基础上，完成两件"收尾整理"工作，并落地 `project-docs/goal.md` 已定稿的 v2.0 核心目标——新增 Serial Title（期刊信息查询）与 Object Retrieval（图表/补充材料获取）两个 MCP 工具，使 UniArticles 的 Elsevier 能力覆盖从"检索文献"延伸到"评估期刊质量"和"获取文献配图/补充材料"。
- **预期成果与核心功能**：
  1. 项目历史变更记录从 `CHANGELOG.md` 迁移至新建的 `project-docs/buildlog.md`，为后续 `project-builder-cn`/`project-bugfix-cn` 的持续构建提供统一的内部日志载体。
  2. 环境变量 `SCOPUS_API_KEY` 全面改名为 `ELSEVIER_API_KEY`（更准确反映其"Elsevier 通用 Key"的本质，与已有的 `ELSEVIER_INSTTOKEN` 命名保持一致）。
  3. 新增 `get_serial_title` 工具（期刊信息查询）与 `get_article_objects` 工具（图表/补充材料元信息获取），均已用真实 API Key 实测确认可用。
  4. 对 goal.md 中记录的遗留风险（`get_abstract_details`/`retrieve_article` 默认 view 为受限视图）给出明确处理结论并落地。
- **目标用户或使用场景**：通过 Claude Desktop / Cherry Studio 等 LLM 客户端使用 UniArticles MCP Server 检索学术文献的科研人员/学生，机构订阅了基础级别（非商业、无 Insttoken）Elsevier Scopus/ScienceDirect API 访问权限。

### v2.1.0 范围收缩补充（QA-R003，2026-08-03）

v2.0（2.0.1）发布后，用户在真实 Cherry Studio 环境下对已发布的全部 17 个工具做了一轮完整可用性实测（11 可用/6 不可用），并据此在 `project-docs/goal.md` QA-R003 锁定了 v2.1.0 的范围：**删除 6 个已确认不可用或超出产品定位的工具**（`download_paper`/`search_authors`/`get_author_profile`/`search_sciencedirect`/`get_article_metadata`/`search_scholar_papers`），将 MCP Server 从 17 个工具收窄为 11 个稳定可用工具；同步修正 README.md/README_ZH.md 中的 Elsevier Key 资质说明与工具清单/计数；`pyproject.toml` 版本号提升至 `2.1.0`。这是一次事后范围收缩（非新增功能），对应开发计划见下方"步骤 8～12"。

### v2.2.0 范围补充（QA-R004～QA-R006，2026-08-03）

源自 `docs/TODO.md` 两条待办 + 用户后续多轮澄清，`project-docs/goal.md` QA-R004～QA-R006 已完整锁定本轮范围与决策，本计划书只需转化为可执行构建步骤，不再重新决策。目标发布版本号为用户明确拍板的 **`2.2.0`**（否决了本 agent 曾建议的 `3.0.0`，理由是本轮改动未净增加工具数量，不再讨论版本号）。本轮是对已发布 v2.1.0（11 个已注册工具，含未公开列出的别名 `search_paper`）的一次**无过渡期破坏性变更**，包含五块内容：

1. **删除 `search_paper`**（`src/uniarticles/sources/arxiv.py`）：它是 `search_arxiv` 的纯别名，功能正常但从未公开列入 README；v2.1.0 曾特意保留，本轮用户主动放弃，无过渡期直接删除代码与注册，MCP Server 实际注册工具数由 11 降至 10。
2. **对删除后剩余的全部 10 个工具一次性彻底重命名**，风格为方案 A"数据源_对象_动作(_by_限定词)"（如 `arxiv_paper_search_by_query`），不设新旧名字过渡期，旧名字直接消失，不做 deprecated 别名/兼容层。
3. **`list_papers`（重命名后 `arxiv_latest_paper_list_by_category`）功能补全**：不是纯改名，借这次改名之机把实现从"无筛选拉取最新论文"补全为真正支持按 arXiv category 过滤——复用 arXiv 官方查询语法的 `cat:` 字段前缀拼接进 `query` 字符串，不新增 `arxiv.Search` 不支持的原生 `category` 参数，也不做客户端侧二次过滤。
4. **`get_abstract_details`/`retrieve_article`（重命名后 `scopus_abstract_detail_by_eid`/`sciencedirect_article_retrieve_by_identifier`）归一化**：从"Elsevier 原始 JSON 整体透传"改为逐字段提取，与 `get_serial_title`/`get_article_objects` 的现有风格对齐。**关键前提**：这两个端点此前从未被记录过真实响应体字段样例（只确认过 HTTP 200 与响应根对象名），归一化字段方案必须先做真实 API 探测（见步骤 14）才能确定，不得在本计划书中凭空预设字段名。
5. **调整 `src/uniarticles/sources/__init__.py` 中 `register_all_sources()` 的文件级调用顺序**：从 `arxiv → scopus → paperscraper → sciencedirect` 改为 `scopus → sciencedirect → arxiv → paperscraper`。仅要求文件级顺序（QA-R006 已明确澄清），各文件内部工具的相对注册顺序不需要调整。

对应开发计划见下方"步骤 13～20"。步骤 1～12（v2.0/v2.1.0 构建）已全部执行完毕并发布，保留在文档中作为历史记录，不受本轮改动影响。

### v2.3.0 范围补充（QA-R007～QA-R008，2026-08-04）

源自用户要求调研本地参考项目 `reference-projects/elsevier-mcp-main/`，`project-creator-cn` 逐一比对该项目 14 个工具的端点与 `project-docs/goal.md` 已有实测结论后，发现 3 个此前完全未调研过的全新端点，用真实 `ELSEVIER_API_KEY` 逐一探测（QA-R007），确认 2 个可用（`content/serial/title` 期刊多条件搜索、`content/subject/{source}` 学科分类代码查询）、2 个不可用（`analytics/plumx/...` PlumX 指标、`content/article/.../` 纯文本变体，均已记录进 goal.md"范围界定/排除"表格）。用户在 QA-R008 中正式确认把 2 个可用端点纳入 **v2.3.0**，版本号由用户直接指定，无需再走版本号确认流程。

**本轮明确边界：v2.3.0 是纯新增（Additive）版本**，只新增 `scopus_serial_title_search_by_criteria`、`scopus_subject_classification_lookup_by_source` 两个 MCP 工具，均放入 `src/uniarticles/sources/scopus.py`（不新建模块）；**不删除、不重命名、不改动**现有 10 个工具（`scopus_document_search_by_query`/`scopus_abstract_detail_by_eid`/`scopus_serial_title_by_issn`/`scopus_api_usage_status`/`sciencedirect_article_retrieve_by_identifier`/`sciencedirect_article_object_by_identifier`/`arxiv_paper_search_by_query`/`arxiv_latest_paper_list_by_category`/`arxiv_paper_detail_by_id`/`pubmed_paper_search_by_query`）的名称/参数/返回结构/注册顺序，与 v2.1.0（删除）、v2.2.0（重命名+功能改造）在改动性质上完全不同。MCP Server 工具总数由 10 个增至 **12 个**。

**命名复核**：goal.md QA-R008 建议的两个名字（`scopus_serial_title_search_by_criteria`、`scopus_subject_classification_lookup_by_source`）已符合 v2.2.0（QA-R004）确认的方案 A"数据源_对象_动作(_by_限定词)"命名风格，与现有 `scopus_serial_title_by_issn`/`scopus_abstract_detail_by_eid` 等同文件工具命名一致，`_by_criteria`/`_by_source` 均如实反映其参数语义（前者是多条件组合搜索，后者 `source` 是唯一必填参数），未发现类似 QA-R004 中 `list_papers` 那种"命名承诺了实现不具备的能力"的问题，本计划书采纳该命名，不做调整。

对应开发计划见下方"步骤 21～26"。步骤 1～20（v2.0/v2.1.0/v2.2.0 构建）已全部执行完毕并发布，保留在文档中作为历史记录，不受本轮改动影响。

## 可行性分析

### 技术可行性评估
- 两个新工具接入的端点（`content/serial/title/issn/{issn}`、`content/object/{id_type}/{id}`）均已在 goal.md 阶段用真实 `SCOPUS_API_KEY` 实测返回 HTTP 200，技术可行性已验证，无需额外可行性摸底。
- 两个新工具的实现模式与现有 `scopus.py`/`sciencedirect.py` 中已实现的工具（`search_scopus`、`get_abstract_details`、`retrieve_article` 等）高度同构：同样使用 `httpx.AsyncClient` + `_get_headers()` + `_ok`/`_err` 统一响应结构，没有引入新的技术栈或依赖，开发风险低。
- 环境变量改名是纯文本/字符串层面的改动，不涉及逻辑变更，风险低，但涉及文件较多（8 个"活跃"文件，见步骤 2），需要逐一核对，避免遗漏。

### 主要依赖与第三方服务
- 无新增第三方 Python 依赖，继续使用现有 `httpx>=0.27.0`、`mcp>=1.0.0`、`python-dotenv>=1.0.0`。
- 依赖同一个 Elsevier 开发者 API Key（`content/serial/*` 属于 Scopus API 族，`content/object/*` 属于 ScienceDirect API 族，但两者与现有实现一样共用 `X-ELS-APIKey` 请求头，无需额外申请新 Key）。

### 开发工作量估算
- 步骤 1（buildlog 迁移）：约 0.5 人日，纯文档整理。
- 步骤 2（环境变量改名）：约 0.5～1 人日，8 个文件的文本替换 + 兼容性代码 + 本地验证。
- 步骤 3（遗留 view 风险处置）：约 0.5 人日，含真实 API 验证。
- 步骤 4～5（两个新工具开发）：约 1～1.5 人日（含真实响应结构探测、字段归一化、错误处理）。
- 步骤 6（文档更新）：约 0.5 人日。
- 步骤 7（整体验证）：约 0.5 人日。
- 合计约 3.5～4.5 人日，工作量较小，无阻断性技术风险。

### 潜在风险与应对策略
| 风险 | 应对策略 |
|---|---|
| Serial Title / Object Retrieval 的真实响应字段结构在 goal.md 中未被完整记录（仅记录了 HTTP 200，未记录响应体字段） | 开发时必须先用真实 Key 发起一次实际请求并打印/查看完整响应体，确认字段名后再写归一化逻辑，不臆造字段名（详见步骤 4、5"具体操作"） |
| 环境变量改名后，已发布到 PyPI 的历史用户若未同步更新其客户端配置（如 `claude_desktop_config.json`）中的 `env` 字段，会导致密钥读取失败 | 见步骤 2 的兼容性方案（保留旧变量名的过渡期兼容读取 + 弃用提示），并在 CHANGELOG/README 中明确提示迁移方法 |
| `get_abstract_details`/`retrieve_article` 默认 view 是否为受限视图，goal.md 阶段仅确认了 Scopus Search 的 `COMPLETE` view 会 401，未直接测试 `META_ABS` | 步骤 3 中用真实 Key 单独验证一次 `META`/`META_ABS` 两种 view 的实际返回状态，再决定最终默认值，不凭文档标记直接下结论 |
| MCP Server 通过 stdio 与客户端通信，任何写入 `stdout` 的内容都会破坏 JSON-RPC 协议帧 | 步骤 2 的弃用提示必须走 `stderr`（如 Python `warnings` 模块或 `logging`），严禁使用 `print()` 到标准输出 |
| `CHANGELOG.md` 存在数据缺口（见步骤 1 风险提示） | 迁移时如实记录缺口，不臆造缺失版本的变更内容 |

## 技术选型

- **编程语言与运行环境**：Python ≥ 3.10（沿用现有 `requires-python = ">=3.10"`），不升级。
- **核心框架与库**：`FastMCP`（`mcp>=1.0.0`）、`httpx>=0.27.0`（异步 HTTP 客户端）、`python-dotenv>=1.0.0`（本地 `.env` 加载）。v2.0 不引入新依赖。
- **数据存储方案**：无（本项目为无状态 MCP 工具封装层，不涉及持久化存储）。
- **部署与基础设施**：沿用现有发布方式——PyPI 包 `uniarticles-mcp`，通过 `uvx uniarticles-mcp` 或本地 `uv run` / `pip install -e .` 运行，v2.0 不改变部署形态。

## 环境配置

### 硬件/系统要求
- 无特殊硬件要求，标准开发机即可。
- 当前开发环境为 Windows 11，需要 PowerShell 或兼容 POSIX 语义的 shell（本项目此前已在该环境下正常开发，无需额外适配）。

### 开发环境搭建
- Git 已初始化，当前分支 `main`，工作区状态干净（无需 `git init`）。
- 建议在开始 v2.0 构建前确认本地 `.env` 中已配置真实 `SCOPUS_API_KEY`（用于步骤 3、4、5 的真实 API 验证；步骤 2 完成改名后需同步改为 `ELSEVIER_API_KEY`，见步骤 2 的操作细节）。

### 依赖安装
本轮不新增依赖，仅需确认现有依赖已安装：

```powershell
# 1. 首先尝试官方源
uv sync
# 或
pip install -e ".[dev]"

# 2. 若上述命令失败或超时，使用镜像源
pip install -e ".[dev]" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

备用镜像：阿里云 `https://mirrors.aliyun.com/pypi/simple`、中科大 `https://pypi.mirrors.ustc.edu.cn/simple`。

> 注：`pyproject.toml` 中 `dev` 可选依赖仅有 `pytest>=8.0.0`，但项目当前没有 `tests/` 目录，历史上从未编写过自动化测试，验证方式一直是"真实 API 手动探测"（goal.md 阶段的做法）。本计划书延续这一惯例，见"质量保证"相关说明。

## 开发计划

---

### 步骤 1：CHANGELOG.md 信息迁移至 buildlog.md

#### 目标说明
用户明确要求把 `CHANGELOG.md`（面向 PyPI/GitHub 用户的公开发布说明）中的历史信息迁移到新建的 `project-docs/buildlog.md`（面向 `project-builder-cn`/`project-bugfix-cn` 的内部构建日志，供后续中断后按断点继续构建、定位历史变更）。二者定位不同：**`CHANGELOG.md` 保留在原位置不删除**，继续作为对外发布说明，未来每次版本发布仍需同步更新；`buildlog.md` 是新增的内部文档，记录"构建过程"而非"对外发布说明"。

#### 具体操作
1. 在 `D:\Demo\UniArticles_MCPserver\project-docs\` 目录下新建 `buildlog.md`（与 `goal.md`、`teach.md` 同级）。
2. 文件开头写明文档用途说明（一段话，说明本文件供 `project-builder-cn`/`project-bugfix-cn` 断点续建/排查历史使用）。
3. 设置两个一级章节：
   - `## 历史记录（迁移自 CHANGELOG.md）`：把 `CHANGELOG.md` 现有内容（截至 `[1.3.0] - 2026-03-24` 及更早版本）逐条迁移，**保留粒度**——版本号、日期、`Added`/`Changed`/`Removed`/`Fixed` 分类、每条变更描述均需保留，允许适当精简措辞但不得丢失功能点信息。
   - `## v2.0.0 构建记录`：留空占位，由 `project-builder-cn` 在实际执行步骤 2～7 时依次追加条目。
4. 每条迁移记录建议采用统一格式：
   ```markdown
   ### [版本号] - 日期
   - 类别：Added / Changed / Removed / Fixed
   - 内容：<从 CHANGELOG.md 原样保留的描述>
   ```
5. v2.0.0 构建记录部分，建议每完成一个开发步骤追加一条，格式：
   ```markdown
   ### 步骤 N：<步骤名称> —— 完成于 <日期>
   - 完成内容：<摘要>
   - 涉及文件：<文件路径列表>
   - 验证结果：<如何验证、结果如何>
   - 遗留问题/风险：<如有>
   ```

#### 验证方法
- `project-docs/buildlog.md` 文件存在，且"历史记录"章节条目数量与 `CHANGELOG.md` 中的版本条目数量一致（含重复版本号，见风险提示）。
- 抽查 2～3 条迁移记录，确认版本号、日期、变更描述与原 `CHANGELOG.md` 一致，未被篡改或臆造。

#### 风险提示
- **`CHANGELOG.md` 中 `[1.3.0]` 版本号重复出现两次**（一次是 "Google Scholar 稳定性警告" 相关改动，日期 2026-03-24；一次是 "ScienceDirect Integration / Enhanced Scopus Tools / Institutional Support" 相关改动，同日期）。迁移时应将两次改动**合并到同一个 `[1.3.0]` 条目下**（视为同一版本号下的两次独立改动记录），不要拆分成两个不同版本，也不要静默丢弃其中一次。
- **版本号空白**：`pyproject.toml` 当前版本号为 `1.5.0`，但 `CHANGELOG.md` 最新记录仅到 `[1.3.0]`，说明 `1.4.0`/`1.5.0` 两个版本的变更从未被记录在 `CHANGELOG.md` 中。迁移时应如实标注这一空白（例如在 buildlog.md 中注明"`1.4.0`/`1.5.0` 版本变更内容缺失，未在 `CHANGELOG.md` 中找到对应记录"），**不得凭猜测臆造这两个版本的变更内容**。
- 迁移是纯信息搬运操作，不涉及代码逻辑，风险整体较低，主要风险点是信息遗漏或臆造。

---

### 步骤 2：环境变量改名 `SCOPUS_API_KEY` → `ELSEVIER_API_KEY`

#### 目标说明
`SCOPUS_API_KEY` 这个命名从 v1.1.0 起就已在文档中被承认"名不副实"（CHANGELOG v1.1.0 记录："Clarified that `SCOPUS_API_KEY` is an Elsevier API key"），且项目已存在 `ELSEVIER_INSTTOKEN` 这一采用 `ELSEVIER_` 前缀的配置项，两者命名不一致容易造成用户困惑。v2.0 作为主版本号升级，是修正这一命名债务的合适时机，统一改为 `ELSEVIER_API_KEY`。

#### 具体操作

**1. 二次确认涉及文件（已核实，共 8 个"活跃"文件需要改动）**：

| 文件 | 需改动内容 |
|---|---|
| `src/uniarticles/config.py` | `Settings.scopus_api_key` 字段（含内部字段名）改为 `elsevier_api_key`，`os.getenv("SCOPUS_API_KEY")` 改为读取新变量名（含兼容性回退逻辑，见下） |
| `src/uniarticles/sources/scopus.py` | `_get_headers()` 中 `settings.scopus_api_key` → `settings.elsevier_api_key`；错误提示文案 `"SCOPUS_API_KEY is required"` → `"ELSEVIER_API_KEY is required"` |
| `.env.example` | `SCOPUS_API_KEY=your_scopus_api_key` → `ELSEVIER_API_KEY=your_elsevier_api_key` |
| `README.md` | 3 处 JSON 配置示例 + 1 处 `.env` 示例 + 1 处说明段落，共 5 处 |
| `README_ZH.md` | 同上，共 5 处 |
| `tutorial/step_by_step_guide_zh.md` | 1 处 JSON 配置示例 |
| `tutorial/step_by_step_guide_en.md` | 1 处 JSON 配置示例 |
| `claude_desktop_config.example.json` | 1 处 `env` 字段 |

**注**：`src/uniarticles/sources/sciencedirect.py` 经核实**不直接引用** `SCOPUS_API_KEY`（它通过 `from .scopus import _get_headers, BASE_URL` 复用 `scopus.py` 的鉴权逻辑），因此无需单独改动，只要 `scopus.py` 改对即可自动生效。

**不在改名范围内（历史记录，禁止修改）**：
- `project-docs/goal.md`、`project-docs/teach.md`——历史决策/讲解文档，如实记录了改名前的状态，属于历史快照，且 planner/builder 均不应改写这两个文件的历史表述。
- `CHANGELOG.md` 中已有的历史版本条目（如 `[1.1.0]` 提到 `SCOPUS_API_KEY`）——历史记录应保持原样，不得为了"政治正确"而篡改历史。新增的 `[2.0.0]` 条目（见步骤 6）中提及改名时使用新名称 `ELSEVIER_API_KEY` 并说明这是一次改名。

**2. 是否需要向后兼容？—— 建议采用"过渡期兼容 + 弃用提示"方案，而非硬切换**

推荐方案：`config.py` 中同时识别两个变量名，优先读取 `ELSEVIER_API_KEY`，若未设置则回退读取旧的 `SCOPUS_API_KEY` 并打印弃用警告（写入 `stderr`，**不可写入 `stdout`**，因为 MCP Server 通过 stdio 与客户端通信，任何 stdout 输出都会破坏 JSON-RPC 协议帧）。示例实现方向：

```python
import os
import sys
import warnings
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _resolve_elsevier_api_key() -> str | None:
    new_key = os.getenv("ELSEVIER_API_KEY")
    if new_key:
        return new_key
    legacy_key = os.getenv("SCOPUS_API_KEY")
    if legacy_key:
        warnings.warn(
            "环境变量 SCOPUS_API_KEY 已弃用，请改用 ELSEVIER_API_KEY（计划于未来主版本移除兼容支持）。",
            DeprecationWarning,
            stacklevel=2,
        )
        return legacy_key
    return None


@dataclass(frozen=True)
class Settings:
    elsevier_api_key: str | None = field(default_factory=_resolve_elsevier_api_key)
    elsevier_insttoken: str | None = os.getenv("ELSEVIER_INSTTOKEN")
    arxiv_download_dir: str = os.getenv("ARXIV_DOWNLOAD_DIR", os.path.join(os.getcwd(), "arxiv_downloads"))


settings = Settings()
```

**理由**：
1. 本项目已发布到 PyPI（包名 `uniarticles-mcp`），历史用户的密钥配置存放在其本地 `claude_desktop_config.json`/Cherry Studio 配置中，属于**代码改动无法触达的外部状态**——仅改代码 + 改文档不能自动帮用户改他们本地的客户端配置文件。若硬切换，这些用户在不知情的情况下升级包版本后，会遇到"密钥读取失败"的运行时报错（`_get_headers()` 会抛出 `ValueError`），需要自行排查才能发现是变量名变了。
2. 兼容层的实现成本极低（约 15 行代码），且是一次性的、有明确移除时间点的技术债务（可在未来的 v3.0 大版本中移除），性价比高于"用户困惑 + issue 排查成本"。
3. 这次改名本身是**表述澄清**（旧名字"能用但名不副实"），不是功能性缺陷修复，没有必须立刻硬切换的紧迫性，兼容处理更稳妥。
4. 与项目历史上"破坏性变更直接硬切"的先例（如 v1.1.0 直接删除 `get_citing_papers` 工具、v1.2.0 直接删除 Semantic Scholar 模块）不同的是：那些是**功能删除**（用不用得上是产品决策，用户无法通过"改配置"来延续使用），而这次是**纯命名变更**（用户只需改一下配置就能无缝延续），兼容成本远低于收益，因此建议与那些先例区别对待。

> 若用户不认可该建议、坚持硬切换，可在构建开始前告知 `project-builder-cn` 直接跳过兼容层实现，仅保留新变量名读取逻辑即可（改动量更小）。

**3. 本地 `.env` 同步**：改名代码落地后，需要提醒使用者将本地 `.env` 中的 `SCOPUS_API_KEY=...` 手动改为 `ELSEVIER_API_KEY=...`（或依赖上述兼容层继续用旧名过渡）。

#### 验证方法
- 全文搜索确认：8 个"活跃"文件中不再出现旧变量名（除非有意保留兼容层代码里的 `SCOPUS_API_KEY` 字符串本身，那属于兼容逻辑的一部分，不算遗漏）。
- `project-docs/goal.md`、`project-docs/teach.md`、`CHANGELOG.md` 历史条目中的 `SCOPUS_API_KEY` 原样保留，未被误改。
- 分别设置仅 `ELSEVIER_API_KEY`、仅 `SCOPUS_API_KEY`（模拟旧用户）、两者都不设置 三种本地环境变量组合，运行任意一个 Scopus/ScienceDirect 工具（如 `search_scopus`），确认：
  1. 仅新变量名：正常工作，无警告。
  2. 仅旧变量名：正常工作，`stderr` 输出弃用警告，`stdout`/MCP 响应本身不受影响（重点验证协议帧未被破坏）。
  3. 两者都无：报错信息为 `"ELSEVIER_API_KEY is required"`（而非旧文案）。

#### 风险提示
- 遗漏某个文档文件中的旧变量名引用，导致文档与代码不一致——用步骤中列出的 8 个文件清单逐一核对，构建完成后再做一次全局搜索确认。
- 弃用警告若误写入 `stdout` 会直接导致 MCP 客户端解析 JSON-RPC 消息失败、连接中断，这是本步骤最高优先级的风险点，务必用 `warnings.warn`（默认输出到 `stderr`）或 `logging`，绝对不能用 `print()`。
- `Settings` 是 `frozen=True` 的 dataclass，字段默认值目前用的是"类定义时求值一次"的写法（`os.getenv(...)` 直接作为默认值表达式），改为 `field(default_factory=...)` 时注意 dataclass 字段求值时机的细微差异（`default_factory` 在每次实例化时调用，而模块级 `settings = Settings()` 只实例化一次，实际效果等价，但如果后续有单元测试需要动态改变环境变量重新读取，需要重新实例化 `Settings()` 而非依赖模块级单例）。

---

### 步骤 3：遗留风险处置——调整 `get_abstract_details`/`retrieve_article` 默认 view

#### 目标说明
`goal.md` 明确记录了一个遗留风险并要求本计划书给出结论：现有 `get_abstract_details`（`scopus.py`）默认 `view=META_ABS`、`retrieve_article`（`sciencedirect.py`）默认 `view=META_ABS`，根据 Elsevier 官方文档，这两个默认 view 均被标记为需要机构订阅/entitlement 的受限 view，而非受限 view 是 `BASIC`/`META`。当前账号是基础非商业 Key、无 Insttoken，`goal.md` 阶段已实测确认同账号下 Scopus Search 的 `COMPLETE` view 会返回 401，说明账号权限确实受限，但**未直接实测过** `get_abstract_details`/`retrieve_article` 这两个具体端点在 `META_ABS` view 下的真实返回结果。

**结论：修（调整默认值），理由如下**：
1. 两个函数的 `view` 参数本身**并非枚举校验的强约束**，只是默认值——把默认值从受限的 `META_ABS` 改为文档标记为无限制的 `META`，不会剥夺任何能力：高权限用户仍可在调用时显式传入 `view="META_ABS"`/`view="FULL"` 等更高视图获取更完整数据；低权限用户则不再因为"不知道要传参数"而默认踩坑收到 401/403。
2. 改动成本极低（两处函数签名默认值各改一行），且完全向后兼容显式传参的调用方式。
3. 与本次新增的两个工具（Serial Title、Object Retrieval）默认使用已实测确认可用的 view 保持一致的产品原则："默认参数必须是当前账号验证过能跑通的最小可用视图"。
4. 不修的代价：新用户首次调用 `get_abstract_details`/`retrieve_article`（这是项目里两个核心检索工具）不传参数就大概率遇到 401/403，直接影响"开箱可用"的产品体验，且用户不知道要额外传 `view="META"` 才能绕开，是一个隐蔽的可用性缺陷。

#### 具体操作
1. **先做真实验证，再改代码**：使用本地 `.env` 中的真实 Key（改名后为 `ELSEVIER_API_KEY`），分别对 `content/abstract/eid/{eid}` 和 `content/article/{identifier_type}/{identifier}` 两个端点各发起 1～2 次真实请求，对比 `view=META`、`view=META_ABS` 两种视图的实际 HTTP 状态码，方法与 `goal.md` 阶段"临时探测脚本、不提交仓库"的做法一致（脚本放在 scratchpad，验证完即弃）。
2. 若验证结果显示 `META` 确实可用而 `META_ABS` 确实受限（与文档标记一致），执行以下改动：
   - `src/uniarticles/sources/scopus.py`：`get_abstract_details(eid: str, view: str = "META_ABS")` → 默认值改为 `view: str = "META"`。
   - `src/uniarticles/sources/sciencedirect.py`：`retrieve_article(identifier: str, identifier_type: str = "pii", view: str = "META_ABS")` → 默认值改为 `view: str = "META"`。
   - 在两个工具的 docstring 中补充一句说明，如：`"Default view is META (unrestricted). Pass view='FULL'/'META_ABS' for more complete data if your subscription supports it."`
3. 若验证结果与预期不符（例如 `META` 同样受限，或 `META_ABS` 实际可用），**以实测结果为准调整最终默认值选择**，不要机械套用文档标记——这正是 `goal.md` 阶段反复强调的"文档存在 vs 实际可用"的原则，本步骤同样适用。
4. 将验证过程和最终决策记录进 `project-docs/buildlog.md` 的"v2.0.0 构建记录"章节。

#### 验证方法
- 真实调用 `get_abstract_details`（传入一个已知有效的 Scopus EID）与 `retrieve_article`（传入一个已知有效的 DOI/PII），确认在不显式传 `view` 参数的情况下能返回 200 且拿到预期的元数据字段（而非空数据或错误）。
- 显式传入更高 view（如 `view="FULL"`）验证仍会按预期报 401/403（确认没有意外破坏高权限用户的可选路径）。

#### 风险提示
- 如果实测发现连 `META` view 都返回 401/403，说明当前账号权限比预想的更受限，此时应如实记录（不要为了"看起来能跑通"而选择一个实测也失败的默认值），并在 README/工具 docstring 中明确提示"该工具在基础订阅下可能无法返回完整数据"，把决策权交还给用户而非静默失败。
- 该调整只改变默认值，不改变函数签名的参数位置和类型，不构成破坏性变更，无需在 CHANGELOG 中标注为 Breaking Change，但仍应作为 `Changed` 条目记录。

---

### 步骤 4：新增 Serial Title（期刊信息查询）MCP 工具

#### 目标说明
接入 `content/serial/title/issn/{issn}` 端点（已实测 `view=STANDARD` 返回 200），给定 ISSN 返回期刊的出版商、Open Access 状态、期刊主页等元数据，对应 `goal.md` 核心目标 1 与成功标准 1。

**代码归属**：加入现有 `src/uniarticles/sources/scopus.py`，不新建文件。理由：该端点属于 Elsevier 开发者门户 Scopus API 族（`sc_apis.html` 下的 Content API），与 `scopus.py` 中已有的 `content/abstract/*`、`content/author/*` 属于同一产品线分组；且 `scopus.py` 当前仅 193 行，尚未到需要拆分的规模，新增一个端点不会显著增加维护复杂度。

#### 具体操作
1. **先用真实 Key 探测一次完整响应体**（`goal.md` 阶段只记录了 HTTP 200，未记录响应体字段结构），确认实际返回的 JSON 结构（Elsevier Serial Title 响应通常以 `serial-metadata-response.entry[]` 为根结构，但具体字段名——如 `dc:title`、`dc:publisher`、`prism:issn`、`openaccess`、`openaccessType`、`link[]` 中期刊主页的 `@ref` 值等——必须以实际抓包结果为准，不得凭本计划书的推测直接编码）。
2. 在 `scopus.py` 中新增内部异步函数：
   ```python
   async def _get_serial_title(issn: str, view: str) -> dict:
       headers = _get_headers()
       url = f"{BASE_URL}content/serial/title/issn/{issn}"
       async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
           response = await client.get(url, params={"view": view})
           response.raise_for_status()
           payload = response.json()
       # 归一化逻辑：字段名以步骤 1 实测结果为准
       entries = payload.get("serial-metadata-response", {}).get("entry", [])
       normalized = [...]
       return _ok(query=issn, items=normalized)
   ```
3. 在 `register()` 函数内新增 MCP 工具：
   ```python
   @server.tool()
   async def get_serial_title(issn: str, view: str = "STANDARD") -> dict:
       """Get journal/serial metadata (publisher, Open Access status, homepage) by ISSN.
       Default view is STANDARD (verified working with basic subscription tier).
       """
       normalized_issn = issn.strip()
       if not normalized_issn:
           return _err(query=issn, message="issn must not be empty")
       try:
           return await _get_serial_title(issn=normalized_issn, view=view)
       except Exception as exc:
           return _err(query=normalized_issn, message=str(exc))
   ```
4. 归一化输出字段建议至少包含：`issn`（含 eISSN 若有）、`title`（期刊名）、`publisher`（出版商）、`openaccess`（OA 状态布尔/标记）、`openaccess_type`（OA 类型，若有）、`homepage_url`（期刊主页链接）、`subject_area`（学科分类，若响应中有）、`coverage_start_year`/`coverage_end_year`（Scopus 收录年份范围，若有）——具体以第 1 步实测的真实字段为准，允许增减。
5. 在 `src/uniarticles/sources/__init__.py` 中**无需新增 import**（因为复用 `scopus.py` 的 `register`），只需确保新工具注册逻辑写在 `scopus.py` 的 `register()` 函数体内即可自动生效。

#### 验证方法
- 用真实存在的 ISSN（如一本已知期刊的 ISSN）调用 `get_serial_title`，确认返回 `ok: true`，且 `items` 中包含标题、出版商等可读字段（不是空值或原始未解析的 JSON blob）。
- 用一个格式错误或不存在的 ISSN 调用，确认走 `_err` 分支返回清晰的 `error` 信息而非抛出未捕获异常（对齐 `goal.md` 成功标准 3）。

#### 风险提示
- 不要在没有真实抓包验证的情况下凭空编写字段归一化逻辑——`goal.md` 只确认了状态码 200，字段结构未知，这是本步骤最大的不确定性来源。
- ISSN 格式可能带连字符（如 `0028-0836`）也可能不带（`00280836`），保持与现有代码风格一致——不做额外格式转换，直接 `.strip()` 后透传给 Elsevier API，由 API 自身处理格式容错（除非实测发现 API 对格式敏感，再补充处理逻辑）。

---

### 步骤 5：新增 Object Retrieval（图表/补充材料获取）MCP 工具

#### 目标说明
接入 `content/object/{id_type}/{id}` 端点（已实测 `content/object/doi/{doi}?view=META` 返回 200），给定文献标识符返回该文献关联的图片、表格、视频、补充材料等对象的**元信息**（文件名、mimetype、类型、下载链接），对应 `goal.md` 核心目标 2 与成功标准 2。

**范围边界（重要）**：`goal.md` 明确的目标是获取对象的"元信息"（清单），**不是**下载对象本身的二进制内容。本工具只返回元数据列表（`view=META`），不实现下载/拉取图片字节流的功能——这与 `goal.md` 期望成果"获取某篇文献的配图/补充材料清单及下载链接，用于快速预览"完全一致，用户可自行用返回的下载链接去获取实际文件。

**代码归属**：加入现有 `src/uniarticles/sources/sciencedirect.py`，不新建文件。理由：`goal.md` 本身将该端点归类在 ScienceDirect API 族（`sd_apis.html`），且 `sciencedirect.py` 已复用 `scopus.py` 的 `_get_headers`/`BASE_URL`，新增该工具符合现有代码组织方式，也符合"两个新工具分别落在各自最贴近的现有模块"的最小改动原则。

#### 具体操作
1. **先用真实 Key 探测一次完整响应体**（同步骤 4 的原则），确认 `content/object/doi/{doi}?view=META` 实际返回的 JSON 结构（通常是对象列表，字段可能包括文件名、mimetype、类型/category、下载引用地址等，具体字段名以实测为准）。
2. 在 `sciencedirect.py` 中新增内部异步函数：
   ```python
   async def _get_article_objects(identifier: str, identifier_type: str, view: str) -> dict:
       headers = _get_headers()
       url = f"{BASE_URL}content/object/{identifier_type}/{identifier}"
       async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
           response = await client.get(url, params={"view": view})
           response.raise_for_status()
           payload = response.json()
       # 归一化逻辑：字段名以实测结果为准
       normalized = [...]
       return _ok(query=identifier, items=normalized)
   ```
3. 在 `register()` 函数内新增 MCP 工具，参数设计对齐现有 `retrieve_article` 的 `identifier`/`identifier_type` 模式：
   ```python
   @server.tool()
   async def get_article_objects(identifier: str, identifier_type: str = "doi", view: str = "META") -> dict:
       """Get metadata (filename, mimetype, type, download link) for figures/tables/
       supplementary materials attached to an article. Does NOT download the binary
       content itself — only returns the metadata list and links.
       identifier_type: doi, pii, scopus_id, or pubmed_id.
       """
       normalized_id = identifier.strip()
       normalized_type = identifier_type.strip().lower()
       if not normalized_id:
           return _err(query=identifier, message="identifier must not be empty")
       try:
           return await _get_article_objects(identifier=normalized_id, identifier_type=normalized_type, view=view)
       except Exception as exc:
           return _err(query=normalized_id, message=str(exc))
   ```
4. 归一化输出字段建议至少包含：`filename`（文件名）、`mimetype`（MIME 类型）、`category`/`type`（对象类型，如 figure/table/supplementary）、`download_url`（下载链接）——具体以实测字段为准。

#### 验证方法
- 用真实存在且已知有配图的 DOI 调用 `get_article_objects`，确认返回 `ok: true` 且 `items` 中包含可读的文件名/类型/链接字段。
- 用一个不存在的 DOI 或权限不足的标识符调用，确认走 `_err` 分支返回清晰错误信息。
- 分别测试 `identifier_type="doi"`、`"pii"` 两种取值（`goal.md` 实测只验证了 `doi`，构建时应至少补测一种其他类型以确认参数设计的通用性；若其他类型实测不通，需在 README/docstring 中明确注明"仅 doi 已验证可用"，不得声称全部类型都可用）。

#### 风险提示
- 同步骤 4，字段结构需要真实抓包确认，不得凭空编写。
- `identifier_type` 目前不做枚举强校验（与现有 `retrieve_article` 风格一致），非法值会直接透传给 Elsevier API 由其返回错误——如果构建时发现这样会产生难以理解的错误信息，可以补充一层更友好的校验和提示，但需权衡"额外校验代码"与"和现有代码风格保持一致"之间的取舍，优先保持一致。
- 该工具明确不做二进制下载，若后续用户反馈需要"直接下载图片"能力，属于新需求，需要走新一轮 `project-planner-cn` 规划，不在本次 v2.0 范围内擅自扩展。

---

### 步骤 6：文档与元数据更新

#### 目标说明
新工具需要在用户可见的文档中体现，避免出现"代码已支持但文档没写、用户不知道能用"的落差（这正是 `goal.md` 反复强调要避免的"文档 vs 实际"落差，只是这次方向反过来——要防止代码有了但文档没跟上）。

#### 具体操作
1. `README.md` / `README_ZH.md` 的 `Features` 章节，在 "Scopus" 条目下补充 "journal/serial metadata lookup by ISSN"，在 "ScienceDirect" 条目下补充 "article object (figures/tables/supplementary materials) metadata retrieval"。
2. `CHANGELOG.md` 新增 `[2.0.0]` 条目（保留在原文件，不迁移到 buildlog——该文件继续承担对外发布说明职责），内容至少包含：
   - Added：`get_serial_title`、`get_article_objects` 两个新工具。
   - Changed：环境变量 `SCOPUS_API_KEY` 更名为 `ELSEVIER_API_KEY`（说明兼容策略，若采纳步骤 2 的建议方案则注明"旧变量名在本版本仍受支持，会输出弃用警告，计划在未来主版本移除"）；`get_abstract_details`/`retrieve_article` 默认 view 调整。
   - Docs：新建 `project-docs/buildlog.md`。
3. `pyproject.toml` 版本号从 `1.5.0` 升级至 `2.0.0`（符合语义化版本规范——本次包含破坏性变更候选项，即环境变量改名，即使做了兼容层也建议按主版本号升级对外沟通"这是一次值得关注的更新"）。
4. `tutorial/step_by_step_guide_zh.md`/`step_by_step_guide_en.md`：这两个文件聚焦"如何配置客户端连接 MCP Server"，不逐一介绍每个工具的功能，因此**除步骤 2 的变量名替换外，无需为新工具补充额外教程内容**（工具功能由 LLM 客户端通过 MCP 协议自动发现，无需手册单独教学）。
5. `project-docs/buildlog.md` 的 "v2.0.0 构建记录" 章节，补全步骤 1～7 各自的完成记录（若步骤 1 执行时该章节还是空的，此时回填）。

#### 验证方法
- 全文检索确认 README 两个语言版本、CHANGELOG 均已更新且中英文/术语一致。
- `pyproject.toml` 版本号与 `CHANGELOG.md` 最新条目版本号一致。

#### 风险提示
- README 更新时注意保持中英文版本内容对等，避免只更新一个语言版本导致文档不同步（这是本项目历史上曾经出现过的模式，如 CHANGELOG 记录的多次"Update README"式提交）。

---

### 步骤 7：整体验证与回归检查

#### 目标说明
在完成上述所有改动后，做一次整体回归检查，确认新增功能可用、老功能未被破坏、环境变量改名的兼容层按预期工作。

#### 具体操作
1. 完整跑一遍现有的手动验证清单（因项目无自动化测试套件）：
   - `search_scopus`、`get_abstract_details`、`get_author_profile`、`search_authors`、`get_quota_status`（Scopus 现有工具）
   - `search_sciencedirect`、`get_article_metadata`、`retrieve_article`（ScienceDirect 现有工具，重点验证步骤 3 的默认 view 调整未导致回归）
   - `get_serial_title`、`get_article_objects`（v2.0 新工具）
2. 验证环境变量三种组合（新变量名/旧变量名/都不设置）下的行为符合步骤 2 的预期。
3. 用 `uv run uniarticles-mcp` 或 `python -m uniarticles` 启动服务，确认进程正常启动、stdout 未被意外的日志/警告污染。

#### 验证方法
- 上述所有工具均能返回 `ok: true` 或结构清晰的 `_err`，无未捕获异常导致进程崩溃。
- MCP Server 能被 Claude Desktop/Cherry Studio 正常加载并列出全部工具（含 2 个新工具）。

#### 风险提示
- 如果条件允许，建议在真实 Claude Desktop/Cherry Studio 中实际加载一次，而不仅是单元级别调用函数，因为 MCP 协议层面的问题（如 stdout 污染）只有在真实客户端连接时才容易暴露。

---

### 步骤 8：删除 6 个已确认不可用/超出产品定位的工具（代码层清理）

#### 目标说明
依据 `project-docs/goal.md` QA-R003 锁定的决策，删除以下 6 个工具及其在各 `sources/*.py` 中的注册函数、私有实现函数，以及仅服务于这些工具的辅助代码/配置，**不做面向未来的预留**（尤其 `download_paper`，是产品定位性排除，即便未来 `arxiv` 库的 `AttributeError` 被修好也不恢复）。删除后 MCP Server 实际注册工具数应为 **11 个**：ArXiv 4（`search_arxiv`/`search_paper`/`list_papers`/`read_paper`）、Scopus 3（`search_scopus`/`get_abstract_details`/`get_serial_title`）、ScienceDirect 2（`retrieve_article`/`get_article_objects`）、PubMed 1（`search_pubmed_papers`）、系统 1（`get_quota_status`）。

#### 具体操作

**8.1 `src/uniarticles/sources/arxiv.py` — 删除 `download_paper`**
- 删除 `_download_paper()` 私有函数（现第 67-96 行）。
- 删除 `register()` 内的 `download_paper` 工具定义（现第 146-161 行）。
- **不要删除 `search_paper`**（现第 112-115 行）——它是 `search_arxiv` 的别名工具，与 `download_paper` 无关，属于保留的 4 个 ArXiv 工具之一，两者名字相近，删除前务必用精确工具名匹配，不要用模糊搜索批量删除。
- 删除 `_download_paper` 后，文件顶部 `import os` 与 `from ..config import settings` 两行已无其他调用方（`_get_paper_details`/`_run_arxiv_search`/`_serialize_paper` 均不使用），一并删除，避免遗留死 import。

**关联死配置清理（本计划书的衍生决策，非 goal.md 字面列出，但符合其"不做面向未来预留代码"原则，明确写清以免 builder 临场决定）**：
`ARXIV_DOWNLOAD_DIR` 环境变量与 `Settings.arxiv_download_dir` 字段只服务于 `download_paper`，该工具删除后即为无人读取的死配置，一并清理：
- `src/uniarticles/config.py`：删除 `arxiv_download_dir: str = os.getenv(...)` 字段（现第 40 行）。
- `.env.example`：删除 `ARXIV_DOWNLOAD_DIR=./arxiv_downloads` 一行。
- `README.md` / `README_ZH.md`：`.env` 配置示例中删除该行（与步骤 9 联动，执行步骤 8 时一并完成，步骤 9 不重复处理）。
- `CLAUDE.md`：`.env` 配置示例中删除该行——`CLAUDE.md` 不在 goal.md"禁止修改"清单内（该清单排除的是 `project-docs/goal.md`、`project-docs/teach.md`），保持其配置示例准确有必要性。
- 删除该字段后重新运行 `Settings()` 实例化（如调用任意 Scopus 工具触发 `settings` 模块级单例），确认无 dataclass 报错。

**8.2 `src/uniarticles/sources/scopus.py` — 删除 `search_authors`、`get_author_profile`**
- 删除 `_search_authors()` 私有函数（现第 94-119 行）与 `_get_author()` 私有函数（现第 85-91 行）。
- 删除 `register()` 内 `get_author_profile`（现第 209-218 行）与 `search_authors`（现第 220-230 行）工具定义。
- 保留不动：`_search_scopus`/`search_scopus`、`_get_abstract`/`get_abstract_details`、`_get_serial_title`/`get_serial_title`、`_get_quota`/`get_quota_status`——这是 Scopus 保留的 3 个工具 + 1 个系统工具。
- `_get_headers()`、`BASE_URL`、`_ok`/`_err` 被保留工具及 `sciencedirect.py`（`from .scopus import _get_headers, BASE_URL`）跨文件依赖，禁止删除。

**8.3 `src/uniarticles/sources/sciencedirect.py` — 删除 `search_sciencedirect`、`get_article_metadata`**
- 删除 `_search_sciencedirect()` 私有函数（现第 30-41 行）与 `_get_article_metadata()` 私有函数（现第 44-55 行）。
- 删除 `register()` 内 `search_sciencedirect`（现第 94-104 行）与 `get_article_metadata`（现第 106-116 行）工具定义。
- 保留不动：`_retrieve_article`/`retrieve_article`、`_get_article_objects`/`get_article_objects`——ScienceDirect 保留的 2 个工具。

**8.4 `src/uniarticles/sources/paperscraper.py` — 删除 `search_scholar_papers`**
- **明确决策（避免 builder 临场判断该文件的去留）**：`paperscraper.py` 文件本身保留，不删除、不从 `src/uniarticles/sources/__init__.py` 的 `register_all_sources()` 中摘除注册调用。理由：删除 `search_scholar_papers` 后文件仍保留 `search_pubmed_papers`（PubMed 检索，属于保留的 11 个工具之一），文件并未清空。已核实 `sources/__init__.py` 中 `register_paperscraper_source(server)` 这一行**无需任何改动**。
- 删除 `_search_scholar()` 私有函数（现第 48-50 行）与 `register()` 内 `search_scholar_papers` 工具定义（现第 66-75 行）。
- 删除文件头部 `from paperscraper.scholar.scholar import get_scholar_papers` 这一行 import（现第 5 行）——删除 `_search_scholar` 后该 import 已无引用。
- 保留不动：`from paperscraper.pubmed.pubmed import get_pubmed_papers`、`_to_items()`、`_search_pubmed()`、`search_pubmed_papers` 工具、`_ok`/`_err`。

#### 验证方法
- 在 `src/` 全目录全局搜索，确认这 6 个工具名（`download_paper`/`search_authors`/`get_author_profile`/`search_sciencedirect`/`get_article_metadata`/`search_scholar_papers`）不再作为函数名或 `@server.tool()` 出现；`search_paper`（别名）与 `search_pubmed_papers` 必须仍然存在且未被误删。
- 启动服务并通过真实 stdio 客户端连接（或 FastMCP 提供的工具枚举接口，具体以当时 `mcp` 库版本为准）确认实际注册工具数为 11。
- 用本地 `.env` 中的真实 `ELSEVIER_API_KEY` 启动服务，手动调用保留的 11 个工具中至少 ArXiv/Scopus/ScienceDirect/PubMed 各 1 个，确认均正常返回，不因误删共享代码导致 `ImportError`/`NameError`。
- 已核实项目当前**不存在** `tests/` 目录（`Glob "tests/**/*.py"` 无匹配），因此不存在"硬编码 17 个工具数量/清单的验证脚本需要同步更新"这一风险点——本计划书已代 builder 完成这项核查，无需在构建时重新排查。

#### 风险提示
- 最大风险是"手滑删多"：`search_paper`（保留）与 `search_authors`（删除）、`search_arxiv`（保留）三者名字相近，务必按精确工具名操作。
- `sciencedirect.py` 通过 `from .scopus import _get_headers, BASE_URL` 依赖 `scopus.py`，删除 `scopus.py` 内容时不要误删这两个被跨文件引用的对象。
- 若使用编辑器"删除未使用 import"自动化功能，需人工复核，避免误删多个工具间共享的顶层 import（如 `httpx`、`asyncio`）。

---

### 步骤 9：README.md / README_ZH.md 同步修正

#### 目标说明
`goal.md` 成功标准 7、8 要求 README 工具清单/计数与代码实际注册的 11 个工具一一对应，且 Elsevier Key 资质说明段落改为准确反映实测结论（非商业/无机构资质的基础 Key 即可让删减后的全部 11 个工具正常工作）。中英文两个版本必须同步修改，不能只改一个语言。

#### 具体操作
对 `README.md` 与 `README_ZH.md` 同步执行，字段一一对应翻译：

1. **`## Features`/`## 功能特性` 章节**：
   - Scopus 条目：`Search, abstract details, author profiles, author search, quota check` → 改为 `Search, abstract details, journal/serial title lookup by ISSN, quota check`（中文同步："搜索、摘要详情、按 ISSN 查询期刊信息、配额查询"）。
   - ScienceDirect 条目：`Article search, metadata search, full-text retrieval (requires entitlement)` → 改为 `Full-text article retrieval, article object (figures/tables/supplementary materials) metadata retrieval`（中文同步）。
   - ArXiv 条目：`Search papers, search by ID, list recent papers, download PDF` → 去掉 "download PDF"，改为 `Search papers, list recent papers, read paper metadata by ID`（中文同步）。
   - Paperscraper 条目：`PubMed search and Google Scholar title search` → 改为仅 `PubMed search`（中文同步）。
   - **整条删除** `Google Scholar Stability Notice`/`Google Scholar 稳定性说明` 该行 bullet——功能已删除，不再需要稳定性提示。

2. **`## ⚠️ API Key Requirements`/`## ⚠️ API 密钥说明` 章节**第 2 条 "Restriction"/"限制"：
   - 英文原句 `Your institution must have a subscription to Elsevier's services; otherwise, you cannot use related functions even with an API Key.` → 改为准确表述，例如：`A basic, non-commercial Elsevier API key (no institutional subscription or Insttoken required) is sufficient to use all remaining Elsevier-related tools in this server — apply for free with a personal account at the Elsevier Developer Portal. (Verified against the current 11 tools using a real non-commercial key.)`
   - 中文原句 `您的机构必须购买了 Elsevier 的相关数据库服务，否则无法申请 API Key，亦无法使用相关功能。` → 改为：`非商业性质、无机构订阅/Insttoken 的基础级 Elsevier API Key 即可让本服务器当前保留的全部 Elsevier 相关工具正常工作——可在 Elsevier Developer Portal 用个人账号免费申请。（该结论已用真实的非商业 Key 对当前全部 11 个工具做过实测验证。）`
   - **不新增未经验证的申请步骤/链接/承诺**（`goal.md` 成功标准 8 的明确约束）——仅替换这一句限制性表述，不改写整段结构，不新增 Elsevier Developer Portal 之外的说明。

3. **`## Available Tools`/`## 可用工具列表` 章节**：
   - Scopus 小节：删除 `get_author_profile(...)`、`search_authors(...)` 两行，保留 `search_scopus`/`get_abstract_details`/`get_serial_title`/`get_quota_status` 四行（`get_quota_status` 沿用现有归类放在 Scopus 小节下，属组织方式差异非计数错误）。
   - ScienceDirect 小节：删除 `search_sciencedirect(...)`、`get_article_metadata(...)` 两行，保留 `retrieve_article`/`get_article_objects` 两行。
   - ArXiv 小节：删除 `download_paper(...)` 一行，保留 `search_arxiv`/`list_papers`/`read_paper` 三行（`search_paper` 别名此前 README 就未单独列出，无需改动）。
   - Paperscraper 小节：删除 `search_scholar_papers(...)` 一行，只保留 `search_pubmed_papers(...)`。
   - 若 README 中存在对外的工具总数陈述（如徽章/文字提及"17 个工具"），一并改为"11 个工具"。

4. **明确不在本次改动范围内**（避免范围蔓延）：
   - `#### Project Structure`/`#### 项目结构` 与 `#### Testing`/`#### 测试` 两节提到的 `tests/` 目录——经核实项目当前不存在该目录，这是先于本轮改动已存在的文档失真，不属于 `goal.md` QA-R003 圈定的范围（QA-R003 只圈定 Elsevier Key 说明段落 + 工具清单/计数），本轮不处理；如需修正应作为独立事项另行提出，不要顺手在本步骤扩大范围。

#### 验证方法
- 全文检索 `README.md`、`README_ZH.md`，确认 6 个已删工具名不再出现在 `Features`/`Available Tools` 任何位置。
- 逐条清点 `Available Tools` 章节工具总数为 11，与步骤 8 验证方法中确认的实际注册数一致。
- 中英文两版逐段比对，确保内容对等。

#### 风险提示
- 该项目历史上多次出现"只更新一个语言版本"的模式（buildlog.md 历史记录 `[1.3.0]` 已提及类似问题），本轮务必同步检查两个文件。
- Elsevier Key 说明段落改写时，不要把"实测验证"表述扩大为对未来订阅升级/其他 Elsevier 产品线（如 SciVal/Embase）的泛化承诺——只针对"当前保留的 11 个工具"陈述实测结论。

---

### 步骤 10：`pyproject.toml` 版本号提升至 2.1.0

#### 目标说明
`goal.md` 明确指定本轮对应版本号 `2.1.0`（非 patch 号），因为包含移除已发布公开工具接口这一使用者可见的破坏性变更。

#### 具体操作
- `pyproject.toml` 第 7 行 `version = "2.0.1"` → 改为 `version = "2.1.0"`。
- 无需改动 `dependencies`/`classifiers`/`optional-dependencies` 等其他字段，本轮不引入新依赖，不涉及 Python 版本要求变化。

#### 验证方法
- `python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"` 输出 `2.1.0`。
- 若本地为 editable install（`pip install -e .`），确认 `python -c "import importlib.metadata as m; print(m.version('uniarticles-mcp'))"` 与新版本号一致（如因 editable 安装机制未即时刷新，可重新执行 `pip install -e .`，不算功能性 bug）。

#### 风险提示
- 版本号是发布到 PyPI 的关键字段，建议放在步骤 8、9 全部验证通过之后再改，避免代码未改完就先改版本号导致误发布不完整版本。

---

### 步骤 11：`project-docs/buildlog.md` 记录本轮变更

#### 目标说明
`goal.md` 成功标准 9 要求 buildlog.md 记录本轮变更；`goal.md` 约束条件明确要求记录决策依据链接到 QA-R003。

#### 具体操作
- 在 `project-docs/buildlog.md` 的 `## v2.0.0 构建记录` 章节之后新增 `## v2.1.0 构建记录` 一级章节。
- 章节开头一段简述本轮背景：引用 `project-docs/goal.md` 的 `QA-R003`（真实 Cherry Studio 环境下对已发布 v2.0/2.0.1 全部 17 个工具的实测，11 可用/6 不可用），说明本轮是范围收缩而非新增功能。
- 逐条记录：
  - 删除的 6 个工具清单（工具名 + 所在文件 + 删除原因，复用 `goal.md` 范围界定表格中的措辞，**不收录** `docs/调用错误分析报告.md` 中未经核实的具体归因推测，如"需联系机构管理员升级"——只记录客观现象：HTTP 状态码 401、请求超时）。
  - 关联清理的死配置：`ARXIV_DOWNLOAD_DIR`/`Settings.arxiv_download_dir`（本计划书步骤 8 的衍生决策，简述理由）。
  - README.md / README_ZH.md 修改摘要。
  - 版本号变更：`2.0.1` → `2.1.0`。
- 每完成一个开发步骤追加一条，格式延续该文件既有约定（参考步骤 1 中 `### 步骤 N：<步骤名称> —— 完成于 <日期>` 的格式）。

#### 验证方法
- `project-docs/buildlog.md` 中能找到明确指向 `goal.md` `QA-R003` 的引用文字。
- 6 个被删工具在 buildlog.md 中均有对应记录，且未收录报告中未经核实的具体归因推测。

#### 风险提示
- 不要把 `docs/调用错误分析报告.md` 中的推测性归因原文照抄进 buildlog.md——`goal.md` QA-R003 已明确这一处理原则，buildlog.md 作为下游文档同样应遵循。

---

### 步骤 12：整体回归验证

#### 目标说明
确认删除操作未破坏保留的 11 个工具，且 MCP 协议层面（stdio/JSON-RPC）未受影响。

#### 具体操作
1. 全局搜索复核（`src/` 全目录 + `README.md`/`README_ZH.md`/`.env.example`/`CLAUDE.md`）：确认 6 个已删工具名、`ARXIV_DOWNLOAD_DIR` 均无残留引用（`project-docs/goal.md`、`project-docs/teach.md`、`CHANGELOG.md` 历史条目除外——这些是历史记录，须保留原样，不得修改）。
2. 用 `uv run uniarticles-mcp` 或 `python -m uniarticles` 启动服务，确认进程正常启动，`stdout` 未被污染（重点关注步骤 8 中 import 清理是否引入任何 `print`/未捕获异常）。
3. 若条件允许，在真实 Claude Desktop/Cherry Studio 中实际加载一次，确认工具列表恰好显示 11 个工具，且名称与 README 一致。
4. 用真实 `.env`（`ELSEVIER_API_KEY`）手动调用保留的 11 个工具中至少覆盖 4 个数据源各 1 个（如 `search_scopus`、`get_serial_title`、`retrieve_article`、`get_article_objects`、`search_arxiv`、`search_pubmed_papers` 中选取），确认均正常返回 `ok: true` 或结构清晰的 `_err`。

#### 验证方法
- 上述 4 项操作均通过，无 `ImportError`/`NameError`/未捕获异常。
- MCP 客户端加载后工具计数为 11，与 README 描述一致。

#### 风险提示
- 本项目没有自动化测试套件（`tests/` 目录不存在），回归验证只能靠手动/真实调用完成，不要因为"删除操作看似简单"而跳过实际启动验证——步骤 2（v2.0 环境变量改名）已有先例说明"看似纯文本改动"也可能因一个 `stdout` 污染就破坏协议帧。

---

### 步骤 13：删除 `search_paper`（`src/uniarticles/sources/arxiv.py`）

#### 目标说明
`project-docs/goal.md` QA-R004/QA-R005 已确认核实：`search_paper`（`arxiv.py` 现第 77-80 行）是 `search_arxiv` 的纯别名（函数体仅 `return await search_arxiv(query, max_results)`），无独立校验/异常处理逻辑，功能正常但从未公开列入 README。v2.1.0 清理 6 个不可用工具那一轮曾特意保留它；本轮用户在明知"无法 100% 排除有用户在文档外凭经验用过这个工具名"这一低概率兼容性风险的前提下，主动放弃该别名。这与步骤 8 删除的 6 个工具性质不同：那 6 个是**实测确认不可用**（401/403/超时），删除是"清理故障"；`search_paper` 是**能正常工作**的别名，删除是"主动做破坏性简化"。删除后 MCP Server 实际注册工具数由 11 降至 10。

#### 具体操作
1. 删除 `arxiv.py` 的 `register()` 内 `search_paper` 工具定义（现第 77-80 行）。
2. 全局搜索确认无其他 `src/` 代码引用 `search_paper`（已预先核实：仅 `arxiv.py` 本体 + `project-docs/goal.md`/`teach.md`/`buildlog.md`/`project-plan.md` 历史文档提及；历史文档保持原样，不修改）。
3. 本步骤独立先行执行并验证，与步骤 15（arxiv.py 改名 + `list_papers` 功能补全）分开操作，避免两类改动混在一次编辑中难以定位问题。

#### 验证方法
- 全局搜索 `search_paper` 确认仅存于历史文档（`goal.md`/`teach.md`/`buildlog.md`/`project-plan.md`）中，`src/` 目录下不再出现。
- 真实调用其余 ArXiv 工具（此时仍为旧名 `search_arxiv`/`list_papers`/`read_paper`，改名在步骤 15 执行）确认未受影响，返回结构正常。

#### 风险提示
- `search_paper` 与保留的 `search_arxiv` 名字接近，删除时务必按精确函数名操作，不要误删 `search_arxiv`。

---

### 步骤 14：真实探测 `get_abstract_details`（Scopus）与 `retrieve_article`（ScienceDirect）响应体结构 —— 归一化前置步骤

#### 目标说明
`project-docs/goal.md` QA-R006 核实确认：这两个端点此前（v2.0 阶段，`buildlog.md` 133-141 行）只记录过 `view=META` 下的 HTTP 200 与响应根对象名（Scopus 侧 `abstracts-retrieval-response`，ScienceDirect 侧 `full-text-retrieval-response.coredata`），**未记录完整字段级结构**。这与步骤 4/5（`get_serial_title`/`get_article_objects`）当年"先抓包确认字段、再写归一化"的做法一致，本步骤是步骤 15.2/15.3 归一化编码的**显式前置步骤**——必须先做真实探测拿到完整响应体样例，才能确定要提取的字段，不得跳过探测直接编码，不得在本计划书或代码中凭空定义字段名。

#### 具体操作
1. 使用本地 `.env` 中的真实 `ELSEVIER_API_KEY`，对一个已知有效的 Scopus EID 发起真实请求 `content/abstract/eid/{eid}?view=META`（可临时复用现有 `_get_abstract()` 逻辑写一次性探测脚本，放在 scratchpad，验证完即弃、不提交仓库——延续 `goal.md` 阶段"临时探测脚本"的一贯做法）。
2. 打印/查看完整响应体 JSON，记录 `abstracts-retrieval-response` 根对象下实际存在的字段路径（标题、作者列表、摘要正文、DOI、期刊名、EID、出版日期、关键词、引用数等——具体以实测为准，不得预设）。
3. 对一个已知有效的 DOI 或 PII，发起真实请求 `content/article/{identifier_type}/{identifier}?view=META`，记录 `full-text-retrieval-response.coredata` 下实际存在的字段路径。
4. 将两份真实字段样例整理成清单，作为步骤 15.2（`scopus.py`）、步骤 15.3（`sciencedirect.py`）编写归一化逻辑的直接依据；并按 `buildlog.md` 步骤 4/5"真实抓包确认的响应字段结构"的既有写法，把清单记入步骤 19 的 buildlog.md 条目。
5. 若探测中发现权限不足（如当前 Key 对某些字段不可见）或响应结构与预期差异较大，如实记录，不得为"看起来完整"而编造字段。

#### 验证方法
- 两个端点的探测请求均返回 HTTP 200，且能看到具体字段名清单（而非仅确认状态码）。
- 探测记录已整理成可直接用于编码的字段列表，供步骤 15.2/15.3 直接引用。

#### 风险提示
- 这是本轮唯一一个"探测优先于编码"的强制前置步骤——若跳过直接假设字段名编码，等同于重演 `goal.md` 已明确警示过的"文档存在 vs 实际可用"风险的变体（这次是"猜测字段名 vs 真实字段名"），同样不可接受。
- 探测脚本务必只发 GET 请求，不对 Elsevier 账号产生任何写副作用。

---

### 步骤 15：全部 10 个工具一次性重命名（含 6 维度改动清单表格）+ 逐文件实现

#### 目标说明
`project-docs/goal.md` QA-R004～QA-R006 确认的核心变更：对步骤 13 删除 `search_paper` 后剩余的 10 个工具，按方案 A"数据源_对象_动作(_by_限定词)"命名风格一次性彻底重命名，不设新旧名字过渡期、不做兼容别名。同时顺带完成 `list_papers` 的功能补全（真实 category 过滤）与 `get_abstract_details`/`retrieve_article` 的归一化（基于步骤 14 探测结果）。以下 6 维度表格是用户在 `goal.md` 约束条件中明确要求的交付格式，逐一覆盖删除 `search_paper` 后剩余的全部 10 个工具，不得省略或简化维度。

#### 6 维度工具改动清单表格

| # | ①改动前工具名 | ②改动后工具名 | ③请求体（参数列表） | ④预期返回体（`items` 字段结构变化） | ⑤作用 | ⑥允许的参数 |
|---|---|---|---|---|---|---|
| 1 | `search_arxiv` | `arxiv_paper_search_by_query` | `query: str`、`max_results: int = 10` | 不变：`id, title, authors[], abstract, published, categories[], pdf_url` | 按关键词全文检索 arXiv 论文；对接 arXiv 官方 API（`arxiv` 库） | `query` 必填、非空字符串；`max_results` 默认 10，服务端 clamp 到 `[1,25]` |
| 2 | `list_papers` | `arxiv_latest_paper_list_by_category` | `category: str`（**新增，必填**）、`max_results: int = 10` | 序列化结构不变（同上），但内容语义改变：由"无筛选最新论文"变为"该分类下最新论文" | 按 arXiv 分类代码列出该分类下最新提交论文；对接 arXiv 官方 API，通过 `cat:` 查询语法拼接过滤（非库原生参数，非客户端二次过滤） | `category` **新增参数**，必填、非空，需匹配 arXiv 官方分类码格式（如 `cs.AI`），支持逗号分隔多个分类；格式非法时工具层直接报错，不透传给 API；`max_results` 默认 10，clamp `[1,25]`（不变） |
| 3 | `read_paper` | `arxiv_paper_detail_by_id` | `paper_id: str` | 不变：同 `_serialize_paper` 结构 | 按 arXiv ID 精确获取单篇论文详情；对接 arXiv 官方 API 的 `id_list` 查询 | `paper_id` 必填、非空字符串 |
| 4 | `search_scopus` | `scopus_document_search_by_query` | `query: str`、`count: int = 5`、`sort: str = "coverDate"`、`view: str = "STANDARD"` | 不变：`title, eid, doi, coverDate, publicationName, creator, citedbyCount, openaccess` | 按关键词检索 Scopus 文献；对接 `content/search/scopus` | `query` 必填非空；`count` 默认 5，clamp `[1,25]`；`sort`/`view` 默认值不变，无强校验、透传 API |
| 5 | `get_abstract_details` | `scopus_abstract_detail_by_eid` | `eid: str`、`view: str = "META"` | **归一化变化**：由 `items=[response.json()]` 原始整体透传改为逐字段提取；具体字段清单待步骤 14 真实探测 `content/abstract/eid/{eid}` 响应体后填充（占位，探测后确定，禁止凭空预设） | 按 EID 获取 Scopus 文献摘要详情；对接 `content/abstract/eid/{eid}` | `eid` 必填非空；`view` 默认 `"META"`，无强校验、透传 API |
| 6 | `get_serial_title` | `scopus_serial_title_by_issn` | `issn: str`、`view: str = "STANDARD"` | 不变：`title, publisher, issn, eissn, aggregation_type, openaccess, openaccess_type, coverage_start_year, coverage_end_year, subject_areas[], homepage_url, source_id, scopus_url` | 按 ISSN 查询期刊元数据（出版商/OA 状态/收录年份等）；对接 `content/serial/title/issn/{issn}` | `issn` 必填非空；`view` 默认 `"STANDARD"`，无强校验、透传 API |
| 7 | `get_quota_status` | `scopus_api_usage_status` | 无参数 | 不变：`limit, remaining, reset, status` | 探测当前 Elsevier API Key 的用量/速率限制状态（借用 Scopus search 响应头模拟，非官方专用端点）；对接 `content/search/scopus` 响应头 | 无参数 |
| 8 | `search_pubmed_papers` | `pubmed_paper_search_by_query` | `query: str`、`max_results: int = 10` | 不变：透传 `paperscraper` 库 `get_pubmed_papers` 返回记录 | 按关键词检索 PubMed 文献；对接 `paperscraper` 库 PubMed 检索能力 | `query` 必填非空；`max_results` 默认 10，clamp `[1,9998]` |
| 9 | `retrieve_article` | `sciencedirect_article_retrieve_by_identifier` | `identifier: str`、`identifier_type: str = "pii"`、`view: str = "META"` | **归一化变化**：由 `items=[response.json()]` 原始整体透传（根为 `full-text-retrieval-response.coredata`）改为逐字段提取；具体字段清单待步骤 14 真实探测后填充（占位，探测后确定，禁止凭空预设） | 按标识符（pii/doi/pubmed_id/eid）检索全文文章记录；对接 `content/article/{identifier_type}/{identifier}` | `identifier` 必填非空；`identifier_type` 默认 `"pii"`，无强校验、透传 API 判定；`view` 默认 `"META"` |
| 10 | `get_article_objects` | `sciencedirect_article_object_by_identifier` | `identifier: str`、`identifier_type: str = "doi"`、`view: str = "META"` | 不变：`filename, ref, type, mimetype, size, width, height, eid, download_url` | 获取文献配图/表格/补充材料对象元信息清单（不下载二进制内容）；对接 `content/object/{identifier_type}/{identifier}` | `identifier` 必填非空；`identifier_type` 默认 `"doi"`（doi/pii 已验证可用，scopus_id/pubmed_id 未验证）；`view` 默认 `"META"` |

#### 具体操作（按文件分组执行，注意保留跨文件依赖 `from .scopus import _get_headers, BASE_URL` 不受影响）

**15.1 `src/uniarticles/sources/arxiv.py` —— 3 个工具仅改名 + `list_papers` 改名同时功能补全**
- `search_arxiv` → `arxiv_paper_search_by_query`：仅改函数名与 `@server.tool()` 绑定名，函数体/参数/docstring 内容不变。
- `read_paper` → `arxiv_paper_detail_by_id`：仅改名，函数体不变。
- `list_papers` → `arxiv_latest_paper_list_by_category`：改名 **同时** 补全实现：
  - 新增必填参数 `category: str`。
  - 新增内部校验/拼接函数，例如：
    ```python
    import re

    _ARXIV_CATEGORY_RE = re.compile(r"^[a-z][a-z-]*(\.[A-Za-z]{2})?$")

    def _build_category_query(category: str) -> str:
        """将逗号分隔的分类码转换为 arXiv 官方 query 语法，如
        'cs.AI,cs.LG' -> 'cat:cs.AI OR cat:cs.LG'。"""
        parts = [c.strip() for c in category.split(",") if c.strip()]
        if not parts:
            raise ValueError("category must not be empty")
        for part in parts:
            if not _ARXIV_CATEGORY_RE.match(part):
                raise ValueError(f"invalid arXiv category code: {part!r}")
        return " OR ".join(f"cat:{p}" for p in parts)
    ```
    正则示例覆盖常见格式（如 `cs.AI`/`math.NA`/`physics.optics`），但实际 arXiv 分类码规则以 arXiv 官方分类列表（`https://arxiv.org/category_taxonomy`）为准；构建时应对照该列表核实正则是否有遗漏（如 `econ.GN`/`q-bio.PE` 等含连字符的子分类前缀），必要时调整正则或改用一份内置分类白名单集合做更严格的校验，具体取舍由 `project-builder-cn` 结合实测决定。
  - `arxiv_latest_paper_list_by_category` 工具体内先调用 `_build_category_query(category)` 得到查询字符串，再传给现有 `_run_arxiv_search(query=query, max_results=bounded)`（复用现有函数与 `arxiv.Search(sort_by=SubmittedDate)` 调用方式，不改 `_run_arxiv_search` 本身，只改传入的 `query` 内容）。
  - `category` 参数为空或格式非法时，工具层直接捕获 `_build_category_query` 抛出的 `ValueError` 并返回 `_err`（不透传给 arXiv API 产生难以理解的远程错误）。
  - 清理原代码第 85-93 行大段"决策过程注释"（`# Since 'list' implies...` 等历史思考痕迹），替换为准确描述新行为的简洁 docstring，例如："List the most recently submitted arXiv papers in a given category (e.g. 'cs.AI'). Uses arXiv's official `cat:` query syntax."。

**15.2 `src/uniarticles/sources/scopus.py` —— 3 个工具仅改名 + `get_abstract_details` 改名同时归一化**
- `search_scopus` → `scopus_document_search_by_query`：仅改名，函数体不变。
- `get_serial_title` → `scopus_serial_title_by_issn`：仅改名，函数体不变。
- `get_quota_status` → `scopus_api_usage_status`：仅改名（**注意**：按 QA-R006 用户明确要求为 `scopus_api_usage_status`，不是此前拟定的 `scopus_api_quota_status`），函数体不变。
- `get_abstract_details` → `scopus_abstract_detail_by_eid`：改名 **同时** 归一化：
  - `_get_abstract()` 从 `return _ok(query=eid, items=[response.json()])`（整体透传）改为基于步骤 14 真实探测结果做逐字段提取，写法风格对齐 `_get_serial_title()`（`.get()` 容错、可选字段允许为 `None`）。
  - 归一化目标字段清单以步骤 14 探测记录为准，此处不预设字段名，避免重蹈 QA-R006 指出的"凭空编字段"问题。

**15.3 `src/uniarticles/sources/sciencedirect.py` —— 1 个工具仅改名 + `retrieve_article` 改名同时归一化**
- `get_article_objects` → `sciencedirect_article_object_by_identifier`：仅改名，函数体不变。
- `retrieve_article` → `sciencedirect_article_retrieve_by_identifier`：改名 **同时** 归一化：
  - `_retrieve_article()` 从 `return _ok(query=identifier, items=[response.json()])` 改为基于步骤 14 真实探测结果做逐字段提取，写法风格对齐 `_get_article_objects()`。
  - 归一化目标字段清单以步骤 14 探测记录为准。

**15.4 `src/uniarticles/sources/paperscraper.py` —— 1 个工具仅改名**
- `search_pubmed_papers` → `pubmed_paper_search_by_query`：仅改名，函数体不变。

#### 验证方法
- 在 `src/` 全目录全局搜索，确认 10 个旧工具名（`search_arxiv`/`list_papers`/`read_paper`/`search_scopus`/`get_abstract_details`/`get_serial_title`/`get_quota_status`/`search_pubmed_papers`/`retrieve_article`/`get_article_objects`）不再作为函数名或 `@server.tool()` 出现；10 个新工具名均能找到对应的 `@server.tool()` 定义。
- 启动服务并通过真实 stdio 客户端连接（或 `mcp` 库提供的工具枚举接口）确认实际注册工具数为 10，名称与表格一致。
- 用本地 `.env` 中真实 `ELSEVIER_API_KEY` 手动调用 `arxiv_latest_paper_list_by_category`，分别测试合法分类（如 `cs.AI`）、非法格式分类（如空字符串、`cs..AI`）、多分类逗号分隔（如 `cs.AI,cs.LG`）三种情况，确认合法请求返回该分类下的最新论文（`categories` 字段中应能看到对应分类码），非法格式请求返回清晰 `_err` 而非未捕获异常。
- 手动调用 `scopus_abstract_detail_by_eid`、`sciencedirect_article_retrieve_by_identifier`，确认 `items` 中是逐字段结构而非原始 JSON blob，字段与步骤 14 探测记录一致。
- 手动调用其余 6 个仅改名工具，确认功能与改名前完全一致（不应有任何行为差异）。

#### 风险提示
- 这是无过渡期的破坏性变更，任何硬编码旧工具名的外部提示词/工作流会在本轮发布后立即失效——这是用户在 `goal.md` QA-R004 中已明确知情并接受的风险，不属于本步骤需要"补救"的问题，但执行时应确保 10 个新名字与表格完全一致，不要在实现过程中随手做二次调整（如缩写不一致）。
- `list_papers` 补全为真正的 category 过滤是"命名+功能开发"，风险高于纯改名的另外 8 个工具，务必按验证方法中的三种分类输入分别测试，不要只测合法输入。
- 归一化的两个工具（`scopus_abstract_detail_by_eid`/`sciencedirect_article_retrieve_by_identifier`）必须严格依赖步骤 14 的真实探测记录，不得在没有先完成步骤 14 的情况下开始编码。
- `search_arxiv`/`arxiv_paper_search_by_query` 与新分类过滤工具容易在实现时被误合并逻辑（如误把 category 过滤混入 `arxiv_paper_search_by_query`），保持两者职责边界清晰。

---

### 步骤 16：调整 `src/uniarticles/sources/__init__.py` 注册顺序（文件级）

#### 目标说明
`project-docs/goal.md` QA-R006 已明确"只要求文件级顺序"，不要求把 `scopus_api_usage_status` 从 `scopus.py` 的 `register()` 中拆出单独调用。当前 `register_all_sources()` 调用顺序为 `arxiv → scopus → paperscraper → sciencedirect`，改为 `scopus → sciencedirect → arxiv → paperscraper`。

#### 具体操作
```python
def register_all_sources(server: FastMCP) -> None:
    register_scopus_source(server)
    register_sciencedirect_source(server)
    register_arxiv_source(server)
    register_paperscraper_source(server)
```
文件顶部 4 行 `from .xxx import register as register_xxx_source` 的书写顺序可一并调整以保持可读性一致（非强制，只影响代码风格，不影响实际调用顺序，实际顺序以函数体内调用顺序为准）。

#### 验证方法
- 阅读改动后的 `__init__.py`，确认 `register_all_sources()` 函数体内调用顺序为 `scopus → sciencedirect → arxiv → paperscraper`。
- 启动服务后通过 MCP 工具枚举确认工具列表按"Scopus 4 个 → ScienceDirect 2 个 → ArXiv 3 个 → Paperscraper 1 个"的文件级分组出现，每个文件内部工具的相对顺序与改名前一致（不需要跨文件精确匹配全局顺序，QA-R006 已明确此为轻量方案）。

#### 风险提示
- 这是纯顺序调整，不改变任何工具的功能/参数，风险很低。
- 应在步骤 15（工具已完成改名）之后执行，避免用旧名字验证顺序造成混淆——建议按本计划书步骤编号顺序整体执行，不要跳步。

---

### 步骤 17：README.md / README_ZH.md 同步修正

#### 目标说明
v2.1.0 已把 README 的工具清单改到"11 个工具"的旧名字状态；本轮要在此基础上把工具名继续换成新名字，同步说明 `list_papers`（重命名后 `arxiv_latest_paper_list_by_category`）新增的 `category` 必填参数，并修正因删除 `search_paper` 导致的注册工具计数变化（11 → 10）。

#### 具体操作
对 `README.md` 与 `README_ZH.md` 同步执行，字段一一对应翻译：

1. **`## Available Tools`/`## 可用工具列表` 章节**（现分别位于 `README.md` 第 147-165 行、`README_ZH.md` 第 145-163 行）：按步骤 15 的表格逐行替换为新工具名与新参数签名。重点是 ArXiv 小节的 `list_papers(max_results)` 一行，改为 `arxiv_latest_paper_list_by_category(category, max_results)`，并在描述中写清 `category` 为**必填**参数、需符合 arXiv 官方分类码格式（给出示例如 `cs.AI`）。`search_paper` 此前从未在该章节列出，删除后无需改动这里。

2. **Elsevier Key 说明章节的工具计数修正**（`README.md` 第 31 行、`README_ZH.md` 第 31 行）：现文案分别为 `"Verified against the current 11 tools using a real non-commercial key."` / `"该结论已用真实的非商业 Key 对当前全部 11 个工具做过实测验证。"`——这个"11"是 v2.1.0 阶段的**实际注册工具数**（含未公开列出的 `search_paper`），删除 `search_paper` 后注册工具数变为 **10**，这两处需同步改为 "10 tools" / "10 个工具"。**不得跳过这一处**，它不在 `Available Tools` 表格里，容易被漏改。

3. **`## Features`/`## 功能特性` 章节**：核实该章节是否直接点名具体旧工具名；若只是功能性描述（未点名具体函数名），无需改动；若发现有点名旧工具名的地方，同步替换为新名字。

4. **明确不在本次改动范围内**：`.env.example`、`tutorial/step_by_step_guide_zh.md`、`tutorial/step_by_step_guide_en.md`、`CLAUDE.md` —— 已用全局搜索核实这些文件均**不包含**任何旧工具名引用（`Grep` 结果仅命中 `project-docs/goal.md`/`teach.md`/`buildlog.md`/`project-plan.md`/`README.md`/`README_ZH.md` 与 4 个 `src/uniarticles/sources/*.py` 源文件），本轮无需改动这些文件，不要顺手扩大范围。

#### 验证方法
- 全文检索 `README.md`、`README_ZH.md`，确认 10 个旧工具名不再出现在 `Available Tools` 章节任何位置，10 个新工具名均能找到。
- 确认 "11 tools"/"11 个工具" 的表述已改为 "10 tools"/"10 个工具"（仅限第 31 行这一处工具计数陈述，不要误改其他含"11"的无关数字，如若有版本号/年份等字符串需排除）。
- 中英文两版逐段比对，确保内容对等。

#### 风险提示
- 该项目历史上多次出现"只更新一个语言版本"的模式（`buildlog.md` 历史记录已多次提及类似问题），本轮务必同步检查两个文件。
- Elsevier Key 说明段落的"实测验证"表述改写时，不要把工具计数之外的其他内容一并改动（如不要因为改了数字就顺带重写整段措辞），保持改动最小化、可追溯。

---

### 步骤 18：`pyproject.toml` 版本号提升至 2.2.0

#### 目标说明
`project-docs/goal.md` QA-R005 明确指定本轮对应版本号 `2.2.0`（用户已否决 `3.0.0`，不再讨论版本号）。

#### 具体操作
- `pyproject.toml` 第 7 行 `version = "2.1.0"` → 改为 `version = "2.2.0"`。
- 无需改动 `dependencies`/`classifiers`/`optional-dependencies` 等其他字段，本轮不引入新依赖（`re` 为 Python 标准库，无需加入 `dependencies`），不涉及 Python 版本要求变化。

#### 验证方法
- `python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"` 输出 `2.2.0`。
- 若本地为 editable install（`pip install -e .`），确认 `python -c "import importlib.metadata as m; print(m.version('uniarticles-mcp'))"` 与新版本号一致（如因 editable 安装机制未即时刷新，可重新执行 `pip install -e .`，不算功能性 bug）。

#### 风险提示
- 版本号是发布到 PyPI 的关键字段，建议放在步骤 13～17 全部验证通过之后再改，避免代码未改完就先改版本号导致误发布不完整版本。

---

### 步骤 19：`project-docs/buildlog.md` 记录本轮变更

#### 目标说明
记录本轮 v2.2.0 变更，链接到 `project-docs/goal.md` 的 `QA-R004`/`QA-R005`/`QA-R006`，延续该文件既有的"版本号一级章节 + 步骤条目"格式。

#### 具体操作
- 在 `project-docs/buildlog.md` 的 `## v2.1.0 构建记录` 章节之后新增 `## v2.2.0 构建记录` 一级章节。
- 章节开头一段简述本轮背景：引用 `project-docs/goal.md` 的 `QA-R004`（删除 `search_paper` + 全量重命名的可行性核实与决策）、`QA-R005`（版本号确认为 `2.2.0`）、`QA-R006`（`scopus_api_usage_status` 命名微调 + 归一化前置探测要求 + 注册顺序文件级调整），说明本轮是"删除 + 破坏性重命名 + 功能补全 + 归一化 + 顺序调整"五合一改动。
- 逐条记录：
  - `search_paper` 删除（步骤 13）。
  - 步骤 14 的真实探测结果：`get_abstract_details`/`retrieve_article` 两个端点的完整字段清单（格式参考现有 `buildlog.md` 步骤 4/5"真实抓包确认的响应字段结构"写法）。
  - 10 个工具的新旧名字对照表（可直接复用步骤 15 的 6 维度表格前两列）。
  - `list_papers` → `arxiv_latest_paper_list_by_category` 的 category 过滤实现方式摘要。
  - `get_abstract_details`/`retrieve_article` 归一化后的最终字段清单。
  - `sources/__init__.py` 注册顺序变更摘要。
  - README.md / README_ZH.md 修改摘要（含"11→10 个工具"计数修正）。
  - 版本号变更：`2.1.0` → `2.2.0`。
- 每完成一个开发步骤追加一条，格式延续该文件既有约定（`### 步骤 N：<步骤名称> —— 完成于 <日期>`）。

#### 验证方法
- `project-docs/buildlog.md` 中能找到明确指向 `goal.md` `QA-R004`/`QA-R005`/`QA-R006` 的引用文字。
- 步骤 14 的真实探测字段清单、10 个工具的新旧名字对照均在 buildlog.md 中有完整记录。

#### 风险提示
- 归一化字段清单必须是步骤 14 真实探测的结果，不得在 buildlog.md 中补记不曾探测过的字段。

---

### 步骤 20：整体回归验证

#### 目标说明
确认删除 + 重命名 + 功能补全 + 归一化 + 顺序调整五类改动叠加后，MCP Server 整体仍然稳定可用，协议层（stdio/JSON-RPC）未受影响。

#### 具体操作
1. 全局搜索复核（`src/` 全目录 + `README.md`/`README_ZH.md`）：确认 `search_paper` 与 10 个旧工具名均无残留引用（`project-docs/goal.md`、`project-docs/teach.md`、`CHANGELOG.md`/`buildlog.md` 历史条目除外——这些是历史记录，须保留原样）。
2. 用 `uv run uniarticles-mcp` 或 `python -m uniarticles` 启动服务，确认进程正常启动，`stdout` 未被污染（重点关注步骤 15 中新增的 `_build_category_query` 校验逻辑是否有意外的 `print`/未捕获异常）。
3. 若条件允许，在真实 Claude Desktop/Cherry Studio 中实际加载一次，确认工具列表恰好显示 10 个工具、名称与 README 一致、且按"Scopus 4 → ScienceDirect 2 → ArXiv 3 → Paperscraper 1"的文件级分组呈现。
4. 用真实 `.env`（`ELSEVIER_API_KEY`）手动调用全部 10 个新工具各至少 1 次，确认均正常返回 `ok: true` 或结构清晰的 `_err`：
   - `arxiv_paper_search_by_query`、`arxiv_latest_paper_list_by_category`（含合法/非法 category 两种输入）、`arxiv_paper_detail_by_id`
   - `scopus_document_search_by_query`、`scopus_abstract_detail_by_eid`、`scopus_serial_title_by_issn`、`scopus_api_usage_status`
   - `sciencedirect_article_retrieve_by_identifier`、`sciencedirect_article_object_by_identifier`
   - `pubmed_paper_search_by_query`

#### 验证方法
- 上述 4 项操作均通过，无 `ImportError`/`NameError`/未捕获异常。
- MCP 客户端加载后工具计数为 10，与 README 描述一致，且名称与步骤 15 表格完全一致。

#### 风险提示
- 本项目没有自动化测试套件，回归验证只能靠手动/真实调用完成；本轮改动量（删除+重命名+功能+归一化+顺序）是历次版本中最大的一次，务必完整走完 10 个工具的逐一验证，不要因为"只是改名字"而跳过功能类改动（`list_papers`/`get_abstract_details`/`retrieve_article`）的实际调用验证。

---

### 步骤 21：真实探测补测——`serial_title_search`/`subject_classifications` 参数边界（编码前置步骤）

#### 目标说明
`project-docs/goal.md` QA-R007/QA-R008 已用真实 `ELSEVIER_API_KEY` 确认两个新端点在**最基础的调用组合**下返回 HTTP 200（`content/serial/title?title=Cell&count=5`；`content/subject/scopus?description=computer`），但明确标注"探测覆盖不全"，以下细节均未验证：
- `content/serial/title`：`issn`/`pub`/`subj`/`content`/`date`/`oa`/`start`/`count`/`view` 各参数的真实调用效果；不带任何检索条件时服务端的真实行为（拒绝还是返回全量）；`count` 的服务端真实上限是否为参考项目 Zod schema 注释里声称的 200（未经本项目验证，不可采信）；无效 `subj` 学科代码的错误响应；无匹配结果时的响应结构。
- `content/subject/{source}`：`source=scidir`（ScienceDirect 学科分类）分支的真实响应字段结构，**不能假设**与已验证的 `source=scopus` 分支（`code`/`description`/`detail`/`abbrev`）同构；`code`/`abbrev`/`field` 精确过滤参数的真实效果；`source` 传入非法值时的错误响应；不带过滤条件、只传 `source` 时的响应体量级（是否需要分页提示）。
- 两工具的错误处理边界（无效标识符/无匹配结果/权限不足）均未真实触发过。

这是步骤 22 编码的**强制前置步骤**，与步骤 14（`get_abstract_details`/`retrieve_article` 归一化前的真实探测）性质相同——不得跳过探测直接假设参数签名/字段结构编码，不得照抄参考项目 `reference-projects/elsevier-mcp-main/` 的 Zod schema 假设（那是别的项目自己的实现选择，不代表 Elsevier 服务端真实行为，`goal.md` 约束条件已明确这一点）。

#### 具体操作
1. 使用本地 `.env` 中真实 `ELSEVIER_API_KEY`，写一次性探测脚本（放 scratchpad，验证完即弃，不提交仓库，延续项目一贯"临时探测脚本"做法），对 `content/serial/title` 端点逐一测试：
   - 在已确认可用的 `title=Cell` 基础上，单变量新增/替换 `issn`/`pub`/`subj`/`content`/`date`/`oa`/`start`/`count`/`view` 各参数，观察响应是否按预期过滤/是否报错。
   - 测试不带任何检索条件的调用（零条件），记录服务端真实行为（拒绝/报错/返回全量）。
   - 测试 `count` 传入较大值（如 200、201、500），确认服务端真实截断上限。
   - 测试一个明显无效/不存在的 `subj` 学科代码，记录错误响应结构。
   - 测试一个明显不存在的 `title`/`issn` 组合，记录"无匹配结果"时的响应结构（空 `entry` 数组还是错误）。
2. 对 `content/subject/{source}` 端点：
   - 测试 `source=scidir` 分支（如 `description=engineering` 或类似关键词），完整记录响应字段结构，与已确认的 `source=scopus` 分支逐字段比对，明确结论"是否同构"（不能含糊带过）。
   - 单独测试 `code`/`abbrev`/`field` 作为过滤参数的真实效果。
   - 测试 `source` 传入非法值（如 `source=invalid`）的错误响应。
   - 测试只传 `source`、不带任何过滤条件时的响应体条目数量级，判断是否需要在归一化/文档中提示"结果量较大"。
3. 将两个端点的真实探测结果整理成清单（参数名/是否生效/错误响应结构/字段列表），作为步骤 22 编码的直接依据；并按 `buildlog.md` 步骤 4/5/14 既有"真实抓包确认的响应字段结构"写法，记入步骤 25 的 buildlog.md 条目。
4. 若探测发现某参数实际不受支持、或行为与 `goal.md` QA-R008 记录的推测不同（如 `count` 上限并非 200、零条件被服务端拒绝），以本步骤实测结果为准调整步骤 22 的最终实现，不强行套用 `goal.md`/参考项目的推测。

#### 验证方法
- 两个端点列出的全部待测参数/边界情况均有真实探测记录（HTTP 状态码 + 响应体摘要），不是假设。
- `subject_classifications` 的 `scidir` 分支字段结构已被明确记录为"与 `scopus` 分支相同"或"不同，具体差异是……"二选一，不留模糊结论。

#### 风险提示
- 探测脚本务必只发 GET 请求，不对 Elsevier 账号产生任何写副作用。
- 不要因探测耗时而只测一部分参数就跳到步骤 22 编码——`goal.md` 约束条件已完整列出全部待测项，步骤 22 的参数签名/校验逻辑/归一化字段必须完整覆盖本步骤的探测结论，不能留"未探测就编码"的缺口。

---

### 步骤 22：新增 `scopus_serial_title_search_by_criteria` + `scopus_subject_classification_lookup_by_source` 两个 MCP 工具

#### 目标说明
基于步骤 21 真实探测结果，在 `src/uniarticles/sources/scopus.py` 中新增两个工具，复用文件已有的 `_get_headers()`/`BASE_URL`/`_ok`/`_err`/`_as_list` 等既有模式，遵循 `_ok`/`_err` 统一响应结构（`{"ok", "source", "query", "count", "items", "error"}`），参数校验风格对齐现有工具（`.strip()` 去空白、必填项判空、`try/except` 捕获异常转 `_err`）。命名沿用 `goal.md` QA-R008 建议、已在本计划书"v2.3.0 范围补充"中复核通过，不做调整。

**22.1 `scopus_serial_title_search_by_criteria`（期刊多条件搜索）**
- 新增内部异步函数 `_search_serial_title(...)`：
  ```python
  async def _search_serial_title(
      title: str | None,
      issn: str | None,
      pub: str | None,
      subj: str | None,
      content: str | None,
      date: str | None,
      oa: str | None,
      start: int | None,
      count: int | None,
      view: str,
  ) -> dict:
      headers = _get_headers()
      params = {
          k: v
          for k, v in {
              "title": title, "issn": issn, "pub": pub, "subj": subj,
              "content": content, "date": date, "oa": oa,
              "start": start, "count": count, "view": view,
          }.items()
          if v is not None
      }
      async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
          response = await client.get(f"{BASE_URL}content/serial/title", params=params)
          response.raise_for_status()
          payload = response.json()
      entries = payload.get("serial-metadata-response", {}).get("entry", []) or []
      normalized = [...]  # 复用 _get_serial_title 的字段提取逻辑（title/publisher/issn/eissn/
                            # aggregation_type/openaccess/openaccess_type/coverage_start_year/
                            # coverage_end_year/subject_areas/homepage_url/source_id/scopus_url），
                            # 并新增该端点独有的 SNIPList/SJRList 期刊计量指标字段——具体子结构
                            # 以步骤 21 真实探测样本为准提取，不得凭空定义
      return _ok(query=..., items=normalized)
  ```
  具体参数是否必填、`count` 是否 clamp 及上限值、零条件时工具层是直接 `_err` 还是允许透传给 API，均以步骤 21 探测结论为准调整——若探测确认服务端拒绝零条件请求，工具层需在全部参数皆为空时直接返回 `_err`，避免把明显会失败的请求发给 API 产生难懂的远端错误；若服务端允许零条件返回全量，则允许调用但应在 docstring 中提示"不带任何条件会返回大量结果，建议至少提供一个过滤条件"。
- `register()` 内新增 `@server.tool() async def scopus_serial_title_search_by_criteria(...)`，各字符串参数 `.strip()` 后判空转 `None`，`try/except` 包裹调用，异常转 `_err`。

**22.2 `scopus_subject_classification_lookup_by_source`（学科分类代码查询）**
- 新增内部异步函数 `_lookup_subject_classification(source: str, description/detail/code/abbrev/field: str | None)`：`source` 必填，工具层先做枚举校验（`source.strip().lower() not in {"scopus", "scidir"}` 时直接返回 `_err`，不透传给 API 产生远端错误，参照步骤 15 中 `arxiv_latest_paper_list_by_category` 对 `category` 的前置校验思路——但若步骤 21 探测发现 API 对非法 `source` 已有清晰易懂的错误响应，也可选择不做前置校验、直接透传，与现有 `identifier_type` "不做强枚举校验、透传 API" 的风格保持一致，两种做法均可接受，具体取舍由 `project-builder-cn` 参照步骤 21 探测结果决定，并在 buildlog.md 中说明选择依据）。
- 归一化：根据步骤 21 确认的 `scopus`/`scidir` 是否同构决定实现方式——若同构，单一归一化逻辑复用；若不同构，按 `source` 分支分别提取字段，不得强行套用同一套字段名。已确认 `scopus` 分支字段：`code`/`description`/`detail`/`abbrev`（扁平结构，无嵌套）。
- `register()` 内新增 `@server.tool() async def scopus_subject_classification_lookup_by_source(source: str, description: str | None = None, detail: str | None = None, code: str | None = None, abbrev: str | None = None, field: str | None = None) -> dict`，`source` 做归一化+校验，其余参数 `.strip()` 后可选透传。

#### 验证方法
- 用真实 `ELSEVIER_API_KEY` 调用两个新工具：
  - `scopus_serial_title_search_by_criteria(title="Cell", count=5)` 确认返回 `ok: true` 且 `items` 为逐字段结构（非原始 JSON blob）。
  - `scopus_subject_classification_lookup_by_source(source="scopus", description="computer")` 确认返回 `ok: true` 且字段与已确认样本一致。
  - 若步骤 21 探测确认 `source=scidir` 可用，追加一次真实 `source="scidir"` 调用验证归一化分支正确。
- 用边界/无效输入验证 `_err` 分支：全部检索条件留空调用 `scopus_serial_title_search_by_criteria`（按步骤 21 结论预期报错或返回提示）；`scopus_subject_classification_lookup_by_source(source="invalid")` 确认走 `_err` 而非未捕获异常。

#### 风险提示
- 归一化字段（尤其 `SNIPList`/`SJRList`、`scidir` 分支字段）必须严格来自步骤 21 的真实探测结果，不得凭空定义。
- 两个新工具与已有 `scopus_serial_title_by_issn`/`scopus_abstract_detail_by_eid` 写在同一文件，复制粘贴时容易手滑改到已有函数体，编码时应新增独立函数而非在已有函数上"顺手改造"。
- `count`/`start` 等数值参数若类型处理不当（如 MCP 客户端传入字符串数字）需按现有 `search_scopus` 的 `count: int` 处理方式保持一致。

---

### 步骤 23：README.md / README_ZH.md 同步更新

#### 目标说明
`project-docs/goal.md` 核心目标 15 要求 MCP Server 工具总数由 10 个增至 12 个，README 工具清单与计数需同步，不得出现"代码有但文档没写"的落差。

#### 具体操作
对 `README.md` 与 `README_ZH.md` 同步执行：
1. **`## Available Tools`/`## 可用工具列表` 章节 → Scopus 小节**：在 `scopus_api_usage_status()` 一行之后新增两行（紧跟其后，与 `register()` 函数体内新增工具的定义顺序一致）：
   - 英文：`` `scopus_serial_title_search_by_criteria(title, issn, pub, subj, content, date, oa, start, count, view)`: Search journals/serials by title, publisher, subject, Open Access status, etc. (multiple optional criteria, no ISSN required). Sibling tool to `scopus_serial_title_by_issn`. ``
   - 英文：`` `scopus_subject_classification_lookup_by_source(source, description, detail, code, abbrev, field)`: Look up Scopus/ScienceDirect subject classification codes to help build more precise search queries. ``
   - 中文对应两行同步翻译。
   - 最终参数列表以步骤 22 实际落地的函数签名为准，此处为草案，若步骤 21 探测导致参数增减，此处需同步调整。
2. **Elsevier Key 说明章节的工具计数修正**（`README.md`/`README_ZH.md` 现均为第 31 行）：现文案 `"Verified against the current 10 tools using a real non-commercial key."` / `"该结论已用真实的非商业 Key 对当前全部 10 个工具做过实测验证。"` → 改为 `"12 tools"` / `"12 个工具"`。**不得漏改**——这一处不在 `Available Tools` 表格内，v2.2.0 步骤 17 已特别标注过此类计数遗漏的教训，本轮同样适用。
3. `## Features`/`## 功能特性` 章节：若该章节有明确点名工具能力的描述，可顺带补充"期刊多条件搜索"/"学科分类代码查询"，非强制展开新条目。
4. **明确不在本次改动范围内**：`.env.example`、`tutorial/step_by_step_guide_zh.md`/`step_by_step_guide_en.md`、`CLAUDE.md`——本轮不涉及新环境变量、不改变客户端配置方式，无需改动这些文件。

#### 验证方法
- 全文检索确认两个新工具名在 `Available Tools` 章节的中英文版本均出现，参数签名与步骤 22 最终实现一致。
- 确认 "10 tools"/"10 个工具" 已改为 "12 tools"/"12 个工具"（仅限第 31 行这一处工具计数陈述，不误改其他含"10"的无关数字）。
- 中英文两版逐段比对，确保内容对等。

#### 风险提示
- 沿用步骤 9/17 已多次验证过的教训：务必同步检查两个语言版本，避免只改一个语言导致文档不同步。
- 第 31 行工具计数容易被漏改，务必单独核对一次。

---

### 步骤 24：`pyproject.toml` 版本号提升至 2.3.0

#### 目标说明
`project-docs/goal.md` QA-R008 已明确用户直接指定本轮对应版本号 `2.3.0`，无需再讨论版本号。

#### 具体操作
- `pyproject.toml` 第 7 行 `version = "2.2.0"` → 改为 `version = "2.3.0"`。
- 无需改动 `dependencies`/`classifiers`/`optional-dependencies` 等其他字段，本轮不引入新依赖，不涉及 Python 版本要求变化。

#### 验证方法
- `python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"` 输出 `2.3.0`。
- 若本地为 editable install（`pip install -e .`），确认 `python -c "import importlib.metadata as m; print(m.version('uniarticles-mcp'))"` 与新版本号一致（如因 editable 安装机制未即时刷新，可重新执行 `pip install -e .`，不算功能性 bug）。

#### 风险提示
- 版本号是发布到 PyPI 的关键字段，建议放在步骤 21～23 全部验证通过之后再改，避免代码未改完就先改版本号导致误发布不完整版本。

---

### 步骤 25：`project-docs/buildlog.md` 记录本轮变更

#### 目标说明
记录本轮 v2.3.0 变更，链接到 `project-docs/goal.md` 的 `QA-R007`（参考项目调研 + 新候选端点发现 + 4 项真实探测）、`QA-R008`（正式立项 v2.3.0，确认纯新增性质），延续该文件既有的"版本号一级章节 + 步骤条目"格式。

#### 具体操作
- 在 `project-docs/buildlog.md` 的 `## v2.2.0 构建记录` 章节之后新增 `## v2.3.0 构建记录` 一级章节。
- 章节开头一段简述本轮背景：引用 `QA-R007`（调研 `reference-projects/elsevier-mcp-main/` 发现 3 个新候选端点，真实探测确认 2 可用 2 不可用）、`QA-R008`（用户正式立项 v2.3.0），并明确说明本轮是**纯新增（Additive）**版本，不涉及删除/重命名/改动现有 10 个工具。
- 逐条记录：
  - 步骤 21 真实探测补测的完整结果（两个端点各参数的真实效果、`count` 服务端真实上限、零条件行为、`scidir` 分支字段结构对比结论、错误响应结构）——格式参照 buildlog.md 已有的"真实抓包确认的响应字段结构"写法。
  - 两个新工具的最终参数签名、归一化字段清单。
  - README.md / README_ZH.md 修改摘要（含"10→12 个工具"计数修正）。
  - 版本号变更：`2.2.0` → `2.3.0`。
- 每完成一个开发步骤追加一条，格式延续该文件既有约定（`### 步骤 N：<步骤名称> —— 完成于 <日期>`）。

#### 验证方法
- `project-docs/buildlog.md` 中能找到明确指向 `goal.md` `QA-R007`/`QA-R008` 的引用文字。
- 步骤 21 真实探测的完整参数边界结果、两个新工具的最终归一化字段清单均在 buildlog.md 中有完整记录。

#### 风险提示
- 不得在 buildlog.md 中补记未曾真实探测过的参数/字段，延续项目一贯的"真实验证优先"原则。

---

### 步骤 26：整体回归验证

#### 目标说明
确认新增的 2 个工具可用，且现有 10 个工具未受影响——本轮不改动它们，但两个新工具与部分现有工具（`scopus_serial_title_by_issn`/`scopus_abstract_detail_by_eid`）写在同一文件 `scopus.py`，需要重点防止编码时误伤共享代码（`_get_headers`/`_ok`/`_err`/`_as_list`/`BASE_URL` 等被 10 个现有工具复用的公共函数）。

#### 具体操作
1. 全局搜索/`git diff` 复核 `src/uniarticles/sources/scopus.py` 改动范围：确认改动只新增了步骤 22 的两个内部函数 + 两个 `@server.tool()` 定义，未触及 `_search_scopus`/`_get_abstract`/`_get_serial_title`/`_get_quota` 等已有函数体，也未修改 `_get_headers`/`_ok`/`_err`/`_as_list`/`BASE_URL`。
2. 用 `uv run uniarticles-mcp` 或 `python -m uniarticles` 启动服务，确认进程正常启动，`stdout` 未被污染。
3. 若条件允许，在真实 Claude Desktop/Cherry Studio 中实际加载一次，确认工具列表恰好显示 **12 个工具**（Scopus 6 个 → ScienceDirect 2 个 → ArXiv 3 个 → Paperscraper 1 个，与 v2.2.0 步骤 16 确认的文件级注册顺序一致，新增两个工具紧跟 `scopus_api_usage_status` 之后，与 `register()` 函数体内定义顺序一致）。
4. 用真实 `.env`（`ELSEVIER_API_KEY`）手动调用：
   - 新增 2 个工具各至少 1 次（含至少 1 次边界/错误输入，如空条件或非法 `source`）。
   - 现有 10 个工具各至少 1 次（覆盖 ArXiv/Scopus/ScienceDirect/PubMed 四个数据源），确认均正常返回 `ok: true` 或结构清晰的 `_err`，返回字段/结构与 v2.2.0 发布前一致，未因本轮改动产生回归。

#### 验证方法
- 上述 4 项操作均通过，无 `ImportError`/`NameError`/未捕获异常。
- MCP 客户端加载后工具计数为 12，与 README 描述一致。
- 现有 10 个工具的返回结构/字段与 v2.2.0 发布前逐一比对一致，无意外变化。

#### 风险提示
- 本项目没有自动化测试套件，回归验证只能靠手动/真实调用完成；重点验证"新增没有误伤旧工具"，因为两个新工具与现有 `scopus_serial_title_by_issn`/`scopus_abstract_detail_by_eid` 写在同一个文件，编码时容易复制粘贴手滑改到已有函数。
- 若真实探测（步骤 21）发现的参数行为与 `goal.md` QA-R008 记录的推测有出入，回归验证时应以步骤 21/22 的最终实现为准，而非机械对照 `goal.md` 原文。

---

## Q&A 记录

### 通用问题

（暂无。后续用户与 `project-builder-cn`/`project-bugfix-cn` 交流中产生的重要问答将按步骤归类记录于此，与特定步骤无关的问题归入本节。）

## 备注

- 本计划书基于 `project-docs/goal.md`（commit `09c837e`，已定稿）第二步范围与用户在本轮对话中明确指定的第一步范围共同产出。
- 步骤 1、2 为用户直接指定的固定收尾事项；步骤 3～7 为落实 `goal.md` 核心目标及处理其记录的遗留风险所设计的具体步骤。
- 若用户对步骤 2 中"是否兼容旧变量名"的建议有不同意见，可在 `project-builder-cn` 开始执行前告知调整，避免已落地代码后再返工。

---

- （v2.1.0，2026-08-03）步骤 8～12 基于 `project-docs/goal.md` QA-R003（commit f57416d）追加，是对已发布 v2.0（2.0.1）的一次事后范围收缩：删除 6 个已确认不可用/超出产品定位的工具，同步修正 README 的 Elsevier Key 说明与工具清单，版本号提升至 `2.1.0`。步骤 1～7（v2.0 构建）已全部执行完毕并发布，保留在文档中作为历史记录，不受本轮改动影响。
- 步骤 8 中"清理 `ARXIV_DOWNLOAD_DIR` 死配置"是本计划书基于"不做面向未来预留代码"原则做出的衍生决策，`goal.md` QA-R003 未逐字列出该配置项，已在步骤 8 中明确标注该决策来源，避免 `project-builder-cn` 误以为超出授权范围而跳过，或反过来误以为是临场发挥。
- 步骤 9 中明确排除了 README `tests/` 目录相关描述的修正——该失真先于本轮改动已存在，不属于 QA-R003 圈定范围，留待未来独立事项处理，避免本轮范围蔓延。

---

- （v2.2.0，2026-08-03）步骤 13～20 基于 `project-docs/goal.md` QA-R004/QA-R005/QA-R006（源自 `docs/TODO.md` 两条待办）追加，是对已发布 v2.1.0（11 个已注册工具，含未公开列出的别名 `search_paper`）的一次无过渡期破坏性变更：删除 `search_paper`、剩余 10 个工具一次性彻底重命名（方案 A 风格）、`list_papers` 功能补全为真正的 category 过滤、`get_abstract_details`/`retrieve_article` 归一化、`sources/__init__.py` 注册顺序文件级调整，版本号提升至 `2.2.0`（用户已在 QA-R005 明确否决 `3.0.0`，不再讨论版本号）。步骤 1～12（v2.0/v2.1.0 构建）已全部执行完毕并发布，保留在文档中作为历史记录，不受本轮改动影响。
- 步骤 14（真实探测 `get_abstract_details`/`retrieve_article` 响应体）是应 QA-R006 明确要求新增的强制前置步骤——此前从未记录过这两个端点的真实字段级结构，归一化编码必须以该步骤的探测结果为依据，不得凭空定义字段名，步骤 15.2/15.3 已在"具体操作"中明确标注这一依赖关系。
- 步骤 17 中"11 tools/11 个工具"→"10 tools/10 个工具"的计数修正（`README.md`/`README_ZH.md` 第 31 行）是本计划书核实源码后发现的必要改动点：该数字统计的是"实际注册工具数"（含此前未公开列出的 `search_paper`），删除 `search_paper` 后必须同步下修，否则会与代码实际注册数不一致——此处不在 `Available Tools` 表格内，容易被遗漏，已在步骤 17 中特别标注。

---

- （v2.3.0，2026-08-04）步骤 21～26 基于 `project-docs/goal.md` QA-R007/QA-R008 追加，源自用户要求调研本地参考项目 `reference-projects/elsevier-mcp-main/` 后发现的候选新端点：真实探测确认 `content/serial/title`（期刊多条件搜索）、`content/subject/{source}`（学科分类代码查询）可用，`analytics/plumx/...`（PlumX 指标）、`content/article/.../` 纯文本变体不可用（已排除）。用户在 QA-R008 中正式立项，直接指定版本号 `2.3.0`，无需再走版本号确认流程。**本轮是纯新增（Additive）版本**：只新增 `scopus_serial_title_search_by_criteria`、`scopus_subject_classification_lookup_by_source` 两个工具（均放入 `src/uniarticles/sources/scopus.py`），不删除、不重命名、不改动现有 10 个工具的名称/参数/返回结构/注册顺序，与 v2.1.0（删除）、v2.2.0（重命名+功能改造）的任务性质均不同。MCP Server 工具总数由 10 个增至 12 个。步骤 1～20（v2.0/v2.1.0/v2.2.0 构建）已全部执行完毕并发布，保留在文档中作为历史记录，不受本轮改动影响。
- 步骤 21（真实探测补测 `serial_title_search`/`subject_classifications` 参数边界）是应 QA-R007/QA-R008 明确要求新增的强制前置步骤——此前的探测只覆盖了每个端点最基础的一种调用组合（`title=Cell` 单条件、`source=scopus`），大量参数（`issn`/`pub`/`subj`/`content`/`date`/`oa`/`start`/`count`/`view`、零条件行为、`source=scidir` 分支字段结构）均未验证过，步骤 22 的参数签名与归一化逻辑必须以该步骤的探测结果为依据，不得凭空定义，也不得照抄参考项目的 Zod schema 假设（`goal.md` 约束条件已明确排除这一做法）。
- 步骤 23 中"10 tools/10 个工具"→"12 tools/12 个工具"的计数修正（`README.md`/`README_ZH.md` 第 31 行）延续了 v2.2.0 步骤 17 已发现的同一类风险点——该数字不在 `Available Tools` 表格内，容易被遗漏，已在步骤 23 中特别标注核对要求。
