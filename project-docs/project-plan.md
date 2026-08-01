# UniArticles（亿文通）MCP Server v2.0 构建计划书

## 项目概述

- **项目目标**：在 v1.x（当前 `pyproject.toml` 版本号 1.5.0，已收尾）基础上，完成两件"收尾整理"工作，并落地 `project-docs/goal.md` 已定稿的 v2.0 核心目标——新增 Serial Title（期刊信息查询）与 Object Retrieval（图表/补充材料获取）两个 MCP 工具，使 UniArticles 的 Elsevier 能力覆盖从"检索文献"延伸到"评估期刊质量"和"获取文献配图/补充材料"。
- **预期成果与核心功能**：
  1. 项目历史变更记录从 `CHANGELOG.md` 迁移至新建的 `project-docs/buildlog.md`，为后续 `project-builder-cn`/`project-bugfix-cn` 的持续构建提供统一的内部日志载体。
  2. 环境变量 `SCOPUS_API_KEY` 全面改名为 `ELSEVIER_API_KEY`（更准确反映其"Elsevier 通用 Key"的本质，与已有的 `ELSEVIER_INSTTOKEN` 命名保持一致）。
  3. 新增 `get_serial_title` 工具（期刊信息查询）与 `get_article_objects` 工具（图表/补充材料元信息获取），均已用真实 API Key 实测确认可用。
  4. 对 goal.md 中记录的遗留风险（`get_abstract_details`/`retrieve_article` 默认 view 为受限视图）给出明确处理结论并落地。
- **目标用户或使用场景**：通过 Claude Desktop / Cherry Studio 等 LLM 客户端使用 UniArticles MCP Server 检索学术文献的科研人员/学生，机构订阅了基础级别（非商业、无 Insttoken）Elsevier Scopus/ScienceDirect API 访问权限。

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

## Q&A 记录

### 通用问题

（暂无。后续用户与 `project-builder-cn`/`project-bugfix-cn` 交流中产生的重要问答将按步骤归类记录于此，与特定步骤无关的问题归入本节。）

## 备注

- 本计划书基于 `project-docs/goal.md`（commit `09c837e`，已定稿）第二步范围与用户在本轮对话中明确指定的第一步范围共同产出。
- 步骤 1、2 为用户直接指定的固定收尾事项；步骤 3～7 为落实 `goal.md` 核心目标及处理其记录的遗留风险所设计的具体步骤。
- 若用户对步骤 2 中"是否兼容旧变量名"的建议有不同意见，可在 `project-builder-cn` 开始执行前告知调整，避免已落地代码后再返工。
