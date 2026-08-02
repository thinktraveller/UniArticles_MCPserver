# 构建日志（buildlog.md）

> 本文件是 UniArticles（亿文通）MCP Server 的**内部构建日志**，供 `project-builder-cn` / `project-bugfix-cn` 在构建中断后按断点继续、以及排查历史变更时定位使用。它记录"构建过程"，与面向 PyPI/GitHub 用户的对外发布说明 `CHANGELOG.md` 定位不同——`CHANGELOG.md` 继续保留在项目根目录，作为对外发布说明，未来每次版本发布仍需同步更新；本文件由各构建阶段按步骤追加条目。
>
> 历史记录部分迁移自 `CHANGELOG.md`（截至 `[1.3.0] - 2026-03-24`），保留了版本号、日期、变更分类（Added/Changed/Removed/Fixed）与各条变更描述。迁移时如实反映了 `CHANGELOG.md` 存在的两处数据情况：`[1.3.0]` 版本号重复出现（已合并）、`1.4.0`/`1.5.0` 版本从未被记录（如实标注为空白，未臆造内容）。

---

## 历史记录（迁移自 CHANGELOG.md）

> 说明：以下内容按 `CHANGELOG.md` 原样迁移，历史表述（包括当时使用的旧变量名 `SCOPUS_API_KEY` 等）保持原样，不做"政治正确"式改写。

### ⚠️ 版本记录空白：1.4.0 / 1.5.0（缺失）

- `pyproject.toml` 当前版本号为 `1.5.0`，但 `CHANGELOG.md` 最新记录仅到 `[1.3.0]`。
- 这意味着 `1.4.0`、`1.5.0` 两个版本的变更内容**从未被记录在 `CHANGELOG.md` 中**，属于历史数据空白。
- 此处如实标注为"无记录/空白"，**不臆造这两个版本的变更内容**。若后续需要补全，需从 git 提交历史中考证，超出本次迁移范围。

### [1.3.0] - 2026-03-24

> 注：`CHANGELOG.md` 中 `[1.3.0]` 版本号重复出现了两次（同为 2026-03-24），此处按计划书要求**合并到同一版本号下**，作为该版本下的两组独立改动记录保留，未拆分为两个版本，也未丢弃其中任意一组。

**改动组 1（Google Scholar 稳定性警告相关）**
- 类别：Changed
- 内容：**Documentation** — 在所有主要文档中为 Google Scholar 增加了明确的稳定性警告；说明 Google Scholar 连通性可能不稳定或临时不可用；将 Google Scholar 相关能力标记为实验性/仅测试用途。

**改动组 2（ScienceDirect 集成 / 增强 Scopus 工具 / 机构支持相关）**
- 类别：Added
  - **ScienceDirect Integration**：新增数据源模块 `src/uniarticles/sources/sciencedirect.py`，提供文章检索、元数据、全文获取等工具。
  - **Enhanced Scopus Tools**：新增 `search_authors` 工具；为所有 Elsevier 工具引入 `view` 参数以控制数据详尽程度。
  - **Institutional Support**：新增 `ELSEVIER_INSTTOKEN` 配置支持，供拥有机构订阅令牌的用户使用。
- 类别：Changed
  - **Documentation**：更新所有 README 与分步指南，纳入 ScienceDirect 与增强的 Scopus 能力。
  - **Stability Notice**：在所有文档中增加关于 Google Scholar 不稳定性的明确警告。

### [1.2.0] - 2026-03-24

- 类别：Added
  - **Paperscraper Tools**：在主服务源集中新增两个 MCP 工具。
  - 新增 `search_pubmed_papers(query, max_results)` 用于 PubMed 检索。
  - 新增 `search_scholar_papers(title)` 用于 Google Scholar 标题查询。
- 类别：Changed
  - **Architecture**：将 paperscraper 功能合并进 `src/uniarticles/sources/paperscraper.py`，并注册到主 MCP 服务。
  - **Documentation**：更新 README 与分步指南，纳入 PubMed 与 Google Scholar 能力。
  - **Dependencies**：新增 `paperscraper` 依赖并刷新锁文件。
- 类别：Removed
  - **Semantic Scholar Source**：移除 Semantic Scholar 数据源模块、注册逻辑、API Key 引用及相关文档/配置提及。

### [1.1.0]

> 注：`CHANGELOG.md` 中该版本条目未标注日期。

- 类别：Changed
  - **Terminology**：将面向用户的表述从"Scopus API"统一为"Elsevier API"（涉及文档与配置示例）。
  - 澄清 Scopus 是 Elsevier 旗下的数据库。
  - 澄清 `SCOPUS_API_KEY` 本质是一个 Elsevier API Key，在订阅范围允许时也可用于其他 Elsevier API。
  - **Docs & Examples**：将 API Key 占位符从 `your_scopus_api_key_here`/`your_scopus_api_key` 更新为面向 Elsevier 的命名。
- 类别：Removed
  - **Scopus Citing Feature**：移除无法工作的引文（citing-paper）能力。
  - 移除 MCP 工具 `get_citing_papers`。
  - 移除相关 CLI/脚本命令路径与文档引用。

### [1.0.0] - 2026-03-10

- 类别：Added
  - **Configuration**：在文档与示例配置的 `uvx` 命令中新增 `--refresh` 标志，用于强制刷新包缓存，确保用户始终获取移除了 ChemRxiv 的最新版本。

### [0.3.0] - 2026-03-10

- 类别：Removed
  - **ChemRxiv**：完全移除 ChemRxiv 数据源集成（ChemRxiv API 平台自 2026 年起已关闭）；移除所有相关代码、测试与文档引用。

### [0.2.3] - 2026-03-10

- 类别：Fixed
  - **Documentation**：修正 `.env.example` 文件格式。

### [0.2.2] - 2026-03-10

- 类别：Added
  - **Documentation**：新增完整的 `README.md` 与分步指南（英文与中文）。
  - **Guide**：为 MCP 客户端提供详细的配置说明。

### [0.2.1] - 2026-03-10

- 类别：Changed
  - 少量内部更新（Minor internal updates）。

### [0.2.0] - 2026-03-10

- 类别：Added
  - UniArticles MCP Server 的首个发布版本。
  - 支持 Scopus 与 ArXiv。

---

## v2.0.0 构建记录

> 本章节由 `project-builder-cn` 在执行 `project-plan.md` 的开发计划时逐步追加。

### 步骤 1：CHANGELOG.md 信息迁移至 buildlog.md —— 完成于 2026-08-02

- 完成内容：新建本文件 `project-docs/buildlog.md`；将 `CHANGELOG.md` 的历史版本记录迁移至"历史记录"章节；`CHANGELOG.md` 保留在原位置不删除，继续作为对外发布说明。
- 涉及文件：`project-docs/buildlog.md`（新增）。
- 关键处理：
  - `[1.3.0]` 版本号在 `CHANGELOG.md` 中重复出现两次，已按计划书要求合并到同一 `[1.3.0]` 条目下（保留两组独立改动，未拆分、未丢弃）。
  - `1.4.0`/`1.5.0` 版本变更在 `CHANGELOG.md` 中从未被记录，已如实标注为空白，未臆造内容。
- 验证结果：文件已创建；历史记录含 9 个去重后版本条目（对应 CHANGELOG 中 10 个版本标题、其中 `[1.3.0]` 重复合并为 1 个），抽查 `[1.2.0]`、`[1.1.0]`、`[0.2.0]` 条目的版本号/日期/变更描述与原 `CHANGELOG.md` 一致。
- 遗留问题/风险：`1.4.0`/`1.5.0` 变更内容缺失，如需补全需另行从 git 历史考证，不在本次范围。

### 步骤 2：环境变量改名 `SCOPUS_API_KEY` → `ELSEVIER_API_KEY` —— 完成于 2026-08-02

- 完成内容：将环境变量 `SCOPUS_API_KEY` 全面改名为 `ELSEVIER_API_KEY`，与已有的 `ELSEVIER_INSTTOKEN` 命名保持一致；在 `config.py` 中实现**向后兼容**读取逻辑（优先读新名，未设置则回退旧名并输出弃用警告）。
- 涉及文件（8 个活跃文件）：
  - `src/uniarticles/config.py`：字段 `scopus_api_key` → `elsevier_api_key`；新增 `_resolve_elsevier_api_key()` 兼容读取函数（`ELSEVIER_API_KEY` 优先，回退 `SCOPUS_API_KEY` 并经 `warnings.warn` 发出 `DeprecationWarning`）；字段默认值改为 `field(default_factory=...)`。
  - `src/uniarticles/sources/scopus.py`：`_get_headers()` 中 `settings.scopus_api_key` → `settings.elsevier_api_key`；错误文案 `"SCOPUS_API_KEY is required"` → `"ELSEVIER_API_KEY is required"`。
  - `.env.example`：`SCOPUS_API_KEY=...` → `ELSEVIER_API_KEY=...`。
  - `README.md` / `README_ZH.md`：JSON 配置示例、`.env` 示例、说明段落均更新为新名，并在说明段落补充"旧名仍向后兼容、已弃用、未来主版本移除"的迁移提示。
  - `tutorial/step_by_step_guide_zh.md` / `tutorial/step_by_step_guide_en.md`：JSON 配置示例更新为新名。
  - `claude_desktop_config.example.json`：`env` 字段更新为新名。
- 关键处理：弃用警告使用 `warnings.warn`（写入 **stderr**），严禁写入 stdout —— 因为 MCP Server 通过 stdio 以 JSON-RPC 与客户端通信，任何 stdout 输出都会破坏协议帧。
- 未改动（历史/非本模块，按计划书要求保持原样）：`src/uniarticles/sources/sciencedirect.py`（经核实不直接引用旧变量名，通过 `from .scopus import _get_headers` 复用鉴权，改 `scopus.py` 后自动生效）；`CHANGELOG.md`、`project-docs/goal.md`、`project-docs/teach.md`、`project-docs/project-plan.md` 中的历史 `SCOPUS_API_KEY` 表述。
- 验证结果（隔离测试脚本运行，验证后即删除，未提交仓库）：
  1. 仅新名 `ELSEVIER_API_KEY`：正常读取，无弃用警告。
  2. 仅旧名 `SCOPUS_API_KEY`（模拟老用户）：正常读取，弃用警告写入 stderr，**stdout 保持干净**（协议帧不受影响）。
  3. 新旧都不设置：解析为 `None`，错误文案为 `ELSEVIER_API_KEY is required`（新文案）。
  4. **不改本地真实 `.env`（其中仍用旧名 `SCOPUS_API_KEY`）**：Key 经兼容层成功解析（非空，长度 32，未打印真值）并触发弃用警告 —— 证明兼容逻辑允许用户不改 `.env` 继续用旧名跑通。
  - 全局搜索确认：残留的 `SCOPUS_API_KEY` 仅出现在 `config.py` 兼容回退逻辑、README 兼容说明段落，以及历史文档（`CHANGELOG.md`、`project-docs/*`）中，均属预期保留，非遗漏。
- 遗留问题/风险：
  - 本地 `.venv` 中 `annotated_types`/`pydantic` 包已损坏（`SyntaxError: source code string cannot contain null bytes`），导致 `mcp` 无法导入。这是**预先存在的环境问题，与本次改动无关**，不影响 config 解析逻辑的验证；但会阻碍后续步骤中"真实启动 MCP Server / 真实调用 API 工具"的验证，建议在进入计划书步骤 3～7 前先修复该 venv（重装依赖）。
  - 提醒使用者：可继续用旧名 `SCOPUS_API_KEY` 过渡（会有弃用警告），或在方便时将本地 `.env` 手动改为 `ELSEVIER_API_KEY`。

### 步骤 3：遗留风险处置——调整 `get_abstract_details`/`retrieve_article` 默认 view —— 完成于 2026-08-02

- 完成内容：将两个核心检索工具的默认 `view` 从受限的 `META_ABS` 改为无限制的 `META`；在 docstring 中补充"默认 META（无限制），高权限用户可显式传 FULL/META_ABS"说明。
- 涉及文件：`src/uniarticles/sources/scopus.py`（`get_abstract_details` 默认值）、`src/uniarticles/sources/sciencedirect.py`（`retrieve_article` 默认值）。
- **真实 API 验证（改前先测，不凭文档标记下结论）**，用 `.env` 中真实 `ELSEVIER_API_KEY`（基础非商业 Key、无 Insttoken）实测：
  - `content/abstract/eid`（Scopus）：`view=META` → **HTTP 200**（返回 `abstracts-retrieval-response`）；`view=META_ABS` → **HTTP 401**（`AUTHORIZATION_ERROR`，视图受限）。→ 证实计划书假设，改 `META` 是真正的可用性修复。
  - `content/article/doi`（ScienceDirect）：`view=META` → **HTTP 200**（`full-text-retrieval-response.coredata` 含真实 title/doi）；`view=META_ABS` → **该账号意外地也返回 200**。
- 决策说明：`retrieve_article` 的 `META_ABS` 在本账号实测可用，与 abstract 端点不同；但按计划书"默认参数应为当前账号验证过能跑通的最小可用视图"原则，且为对更低权限账号更稳妥，仍统一改为 `META`（`META` 同样实测 200 且返回真实内容）。高权限用户可显式传 `META_ABS`/`FULL`，向后兼容不受影响。
- 验证结果：改后 `get_abstract_details`（默认 META）、`retrieve_article`（默认 META）真实调用均返回 `ok:true`。

### 步骤 4：新增 Serial Title（期刊信息查询）工具 `get_serial_title` —— 完成于 2026-08-02

- 完成内容：在 `src/uniarticles/sources/scopus.py`（不新建文件）新增内部函数 `_get_serial_title()` 与 MCP 工具 `get_serial_title(issn, view="STANDARD")`，接入端点 `content/serial/title/issn/{issn}`。
- **真实抓包确认的响应字段结构**（用 ISSN `0092-8674`=Cell 实测，`view=STANDARD` → 200）：根为 `serial-metadata-response.entry[]`，每个 entry 含：
  - `dc:title`（期刊名，如 "Cell"）、`dc:publisher`（"Elsevier B.V."）、`prism:issn`、`prism:eIssn`、`prism:aggregationType`（"journal"）、`source-id`、`prism:url`
  - `openaccess`（"0"/"1"）、`openaccessType`、`coverageStartYear`、`coverageEndYear`
  - `subject-area[]`：每项 `{@code, @abbrev, $=名称}`
  - `link[]`：`@ref` 取值 `scopus-source`/`homepage`/`coverimage`（注意：homepage 的 `@href` 可能为空串，归一化时空串转 `None`）
  - 另有指标字段 `SNIPList`/`SJRList`/`citeScoreYearInfoList`（本工具未纳入归一化，保持精简）
- 归一化输出字段：`title, publisher, issn, eissn, aggregation_type, openaccess, openaccess_type, coverage_start_year, coverage_end_year, subject_areas[], homepage_url, source_id, scopus_url`，全部用 `.get()` 容错。
- 验证结果：
  - 真实 ISSN `0092-8674` → `ok:true, count:1`，`title=Cell / publisher=Elsevier B.V. / issn=0092-8674 / eissn=1097-4172 / coverage 1974–2026`，`subject_areas=[{code:1300, abbrev:BIOC, name:...}]`，`homepage_url=None`（该刊 homepage href 为空串）。
  - 无效 ISSN `0000-0000` → 端点返回 404（`RESOURCE_NOT_FOUND`），`raise_for_status()` 抛 `HTTPStatusError`，工具层 `try/except` 转为统一 `_err` 结构（`ok:false`）。

### 步骤 5：新增 Object Retrieval（图表/补充材料）工具 `get_article_objects` —— 完成于 2026-08-02

- 完成内容：在 `src/uniarticles/sources/sciencedirect.py`（不新建文件）新增内部函数 `_get_article_objects()` 与 MCP 工具 `get_article_objects(identifier, identifier_type="doi", view="META")`，接入端点 `content/object/{id_type}/{id}`。
- **范围边界**：仅返回对象元信息（文件名/类型/下载链接）清单，**不下载二进制内容本身**（与 goal.md 目标一致）。
- **真实抓包确认的响应字段结构**（用 DOI `10.1016/j.jmst.2026.07.003` 实测，`view=META` → 200）：根为 `attachment-metadata-response.{coredata, attachment[]}`。`attachment[]`（本例 25 个对象）每项字段**因对象类型而异、均为可选**：
  - 完整字段（以 IMAGE-THUMBNAIL 类型为例）：`@_fa, prism:url(下载链接), eid, ref(如 "gr6"), filename(如 "gr6.sml"), mimetype, size, height, width, type`
  - 部分类型（如 IMAGE-DOWNSAMPLED）仅有 `@_fa, prism:url, mimetype, type`（无 filename/eid/尺寸）→ 归一化必须全部 `.get()`
  - `type` 实测取值集合：`ALTIMG / APPLICATION / IMAGE-DOWNSAMPLED / IMAGE-HIGH-RES / IMAGE-THUMBNAIL`
  - `mimetype` 实测取值集合：`image/jpeg / image/gif / image/svg+xml / application/word`
- 归一化输出字段：`filename, ref, type, mimetype, size, width, height, eid, download_url`（`download_url` 取自 `prism:url`）。
- 验证结果：
  - `identifier_type="doi"` → `ok:true, count:25`，全部对象含 `download_url`。
  - `identifier_type="pii"`（PII `S100503022600486X`）→ `ok:true, count:25`，确认第二种标识符类型同样可用（计划书要求至少补测一种非 doi 类型）。
  - 无效 DOI → 抛 `HTTPStatusError`，工具层转 `_err`（`ok:false`）。
- 两个新工具均遵循项目统一返回结构 `{ok, source, query, count, items, error}`，复用各自模块已有的 `_ok`/`_err` 辅助函数。

### 步骤 6：文档与元数据更新 —— 完成于 2026-08-02

- `README.md` / `README_ZH.md`：在 "Available Tools / 可用工具列表" 章节 Scopus 分组下新增 `get_serial_title`、ScienceDirect 分组下新增 `get_article_objects`，中英文对等更新。
- `pyproject.toml`：版本号 `1.5.0` → `2.0.0`（语义化主版本升级，含环境变量改名这一破坏性变更候选项）。
- `uv.lock`：`uniarticles-mcp` 自身条目版本随之由 `1.5.0` → `2.0.0`（`uv lock` 自我纠偏，diff 仅此一行）。
- 说明：`CHANGELOG.md` 已在此前被删除（见下方 bugfix 记录），变更说明改由本 buildlog.md 承载，故不再新增 `[2.0.0]` CHANGELOG 条目。教程文档（`tutorial/*`）按计划书要求无需为新工具单独补充内容。
- 测试策略：延续项目"真实 API 手动验证"惯例，未引入 pytest 自动化用例。

### 步骤 7：整体验证 —— 完成于 2026-08-02

- 用 `create_server()` 构建 `FastMCP` 实例并 `list_tools()`，确认 `get_serial_title`、`get_article_objects` 两个新工具均已成功注册。
- 现有工具回归：`get_abstract_details`（新默认 META）、`retrieve_article`（新默认 META）真实调用返回 `ok:true`，未因默认 view 调整而回归。
- 所有真实 API 验证通过隔离脚本完成（脚本存于 scratchpad 临时目录，验证后已删除，未提交仓库）。
- 遗留说明：`content/search/sciencedirect`（现有 `search_sciencedirect` 工具）在本基础订阅账号下实测返回 401（该账号无 ScienceDirect 全文搜索 entitlement），属账号权限层面限制、非本次代码改动引入；新增的 `get_article_objects` 因走 `content/object` 端点则可正常返回，两者权限边界不同。

### 下一步计划

- `project-plan.md` 的**第一步（收尾整理）+ 第二步（goal.md 范围：view 修复 + 两个新工具 + 文档/版本收尾）已全部完成**。当前无待执行的计划步骤。
- 如需进一步扩展（如"直接下载对象二进制内容"能力、接入更多 Elsevier 产品线），属新需求，需另行经 `project-planner-cn` 规划后再构建。

---

## Bug 修复记录（project-bugfix-cn）

## [2026-08-02 21:46] 修复：本地 .venv 环境损坏（annotated_types/pydantic 含空字节，导致 mcp 无法导入）

### 问题描述
- 现象：`import mcp` 报 `SyntaxError: source code string cannot contain null bytes`，追溯调用链为 `mcp/types.py` → `from pydantic import ...` → `pydantic/fields.py` → `import annotated_types` → 加载 `annotated_types/__init__.py` 时触发。单独 `import pydantic` 不报错（因 pydantic 用 `__getattr__` 做懒加载，未触发到坏文件）。
- 影响范围：`mcp` 包（FastMCP 来源）在本地 `.venv` 中完全无法导入，阻塞"真实启动 MCP Server / 真实调用 API"的验证工作；不影响已完成的步骤 1、2 中纯字符串/配置逻辑层面的验证（`config.py` 的验证是用隔离脚本单独跑的，未依赖 `mcp` 导入）。

### 根本原因
用 Python 直接读取受损文件的字节内容确认：`.venv/Lib/site-packages/annotated_types/__init__.py` 全文件 13819 字节中前 12288 字节（3 个 4096 字节的磁盘簇整数倍）全部是 `\x00` 空字节，从第 12288 字节起才是正常的 Python 源码文本；`pydantic/fields.py` 本身完好（0 个空字节），是它依赖的 `annotated_types` 被破坏导致间接失败。进一步扫描整个 `.venv/Lib/site-packages` 下的 1258 个 `.py` 文件，发现 **40 个文件**受到同样模式的破坏（均是从文件开头起、按 4096 字节磁盘簇整数倍长度被清零，之后内容正常），且分布在互不相关的多个包中（如 `annotated_types`、`adodbapi` 等），并非仅限于 `mcp`/`pydantic` 依赖链。这种"按磁盘簇边界整块清零、非纯软件逻辑错误"的模式是典型的**磁盘/文件系统层面写入中断或稀疏文件损坏特征**（例如安装过程中被中断、杀毒软件/同步工具介入、磁盘写入异常等），而不是某次 pip/uv 安装的包版本冲突或单一依赖问题——因此判断为 `.venv` 整体环境层面的损坏，而非代码或配置逻辑缺陷。

### 修复方案
1. 先尝试影响最小的方式：`uv sync`（按 `pyproject.toml`/`uv.lock` 重新同步依赖）。执行后复测 `import mcp` 仍报相同错误——因为 `uv sync` 只在包版本/依赖关系不满足时才会重新安装，对"版本号匹配但文件内容已损坏"的包不会重装，无法修复本问题。
2. 改用 `uv sync --reinstall`（强制重新安装所有已解析的包，从 uv 缓存重新落盘覆盖现有文件，不改变 `pyproject.toml`/`uv.lock` 中除自身包版本号外的依赖解析结果）。执行后受损的 40 个文件全部被覆盖为正常内容（复扫确认 0 个文件含空字节）。未采用"删除整个 `.venv` 目录再重建"的更重方案，因为 `--reinstall` 已能达到同等修复效果且成本更低（复用本地/uv 缓存，未重新联网下载大体积依赖如 scipy/pandas，仅少量新包走了网络下载）。
3. 修复过程完全未触碰项目根目录的 `.env`（真实凭据文件）——`.venv` 是虚拟环境目录，与 `.env` 是两个不同的文件/目录，修复前后用 `ls -la .env` 核对其修改时间未变化，确认未被误删或改动。

### 变更文件
- `D:\Demo\UniArticles_MCPserver\.venv\**`：虚拟环境内的第三方包文件被 `uv sync --reinstall` 重新落盘覆盖（`.venv` 已被 `.gitignore` 排除，不产生 git 变更，仅记录于此供后续排查参考）。
- `D:\Demo\UniArticles_MCPserver\uv.lock`：`uniarticles-mcp` 自身条目的 `version` 字段从残留的旧值 `1.2.0` 更正为 `pyproject.toml` 中的当前值 `1.5.0`（`uv sync` 重新解析时的正常副作用，属于锁文件自我纠偏，未涉及其他依赖版本变化，已用 `git diff uv.lock` 核对确认）。

### 验证方法
- `.venv/Scripts/python.exe -c "import mcp; print(mcp.__file__)"` 成功导入并打印路径（此前报 `SyntaxError`）。
- `.venv/Scripts/python.exe -c "import pydantic; from pydantic import BaseModel; print(pydantic.__version__)"` 成功，输出 `2.12.5`。
- 对 `.venv/Lib/site-packages` 全量 `.py` 文件复扫空字节，确认 0 个文件仍含空字节（修复前为 40 个）。
- 编写一次性验证脚本（存放于 scratchpad 临时目录，验证完已删除，未提交仓库）：`from uniarticles.server import create_server; server = create_server()`，成功构建 `FastMCP` 实例（`name="uniarticles-mcp"`），确认不仅是依赖能 import，项目自身的 `create_server()`（含 `register_all_sources()` 注册全部数据源工具）也能正常构建，不需要真正阻塞式运行进程即完成验证。
- `git status --short` 确认 `.env` 未出现在变更列表中（`.venv` 被 gitignore，`.env` 本就应被 gitignore 排除且未受影响）。

---

## [2026-08-02 21:46] 修复：删除过时的 CHANGELOG.md，改由 buildlog.md 作为唯一变更记录

### 问题描述
- 现象：用户明确要求删除项目根目录的 `CHANGELOG.md`。该文件已过时——其历史内容已在 v2.0 构建步骤 1（commit `14dc8bd`）完整迁移至 `project-docs/buildlog.md` 的"历史记录"章节，迁移时已如实处理了 `[1.3.0]` 重复记录合并、`1.4.0`/`1.5.0` 缺失记录标注空白两个已知数据问题。
- 说明：这与 `project-docs/project-plan.md` 步骤 1/6 中"`CHANGELOG.md` 继续保留、作为对外发布说明，与 `buildlog.md` 分工"的原设计不同——用户在本次修复中明确改变主意，要求直接删除 `CHANGELOG.md`，只保留 `buildlog.md` 作为唯一变更记录。按 bugfix 职责边界，本次**不修改** `project-docs/project-plan.md` 本身（该文件历史设计表述保持原样，如需正式变更设计应走 `project-planner-cn` 重新规划），仅执行用户对本次操作的直接指示。

### 根本原因
不适用（非代码缺陷，为用户主动要求的文档结构调整）。

### 修复方案
1. 直接删除 `D:\Demo\UniArticles_MCPserver\CHANGELOG.md`（git 保留历史，可通过 `git log -- CHANGELOG.md` 找回，非不可逆丢失）。
2. 全仓库（尊重 `.gitignore`，即排除 `.venv` 等）搜索 `CHANGELOG`/`changelog`/"更新日志" 关键词，核对是否存在指向该文件的死链接：
   - `README.md`、`README_ZH.md`、`tutorial/step_by_step_guide_zh.md`、`tutorial/step_by_step_guide_en.md`、`pyproject.toml`（含 `[project.urls]`）、`claude_desktop_config.example.json`：均无引用，无需改动。
   - `project-docs/project-plan.md`：存在多处历史设计表述引用 `CHANGELOG.md`（步骤 1、2、6 等），但该文件是历史构建计划书快照，按职责边界 bugfix 不得修改，予以保留原样（不算需要清理的"死链接"，而是历史决策记录的一部分）。
   - 项目根目录 `CLAUDE.md`（未纳入 git 跟踪，但属于会被 Claude Code 读取的项目说明文档）第 51 行原文写着"`buildlog.md`（distinct from the user-facing `CHANGELOG.md`, which is kept as the public release-notes file）"，属于会产生误导的过时引用，已同步更新为"`CHANGELOG.md` was removed; its history was merged into this file's 历史记录 section"。

### 变更文件
- `D:\Demo\UniArticles_MCPserver\CHANGELOG.md`：已删除。
- `D:\Demo\UniArticles_MCPserver\CLAUDE.md`：第 51 行更新，移除对已删除 `CHANGELOG.md` 的过时引用（该文件未纳入 git 跟踪，此次为随手同步修正，不在正式提交范围内）。

### 验证方法
- `ls CHANGELOG.md` 返回 "No such file or directory"，确认已删除。
- 用 ripgrep 对整个仓库（遵循 `.gitignore`）不限文件类型搜索 `CHANGELOG`（大小写不敏感），仅命中 `CLAUDE.md`（已修正）与 `project-docs/project-plan.md`（历史文档，按职责边界保留原样，已在上文说明原因），确认 `README.md`/`README_ZH.md`/教程文档/`pyproject.toml`/`claude_desktop_config.example.json` 均无死链接残留。

---

## 打包发布准备（project-builder-cn）

## [2026-08-02 22:55] v2.0.0 打包 + sdist exclude 收敛（仅打包，不发布）

### 执行的任务
- 用项目工具链 `uv build`（hatchling backend）打包出 `dist/uniarticles_mcp-2.0.0-py3-none-any.whl` 与 `dist/uniarticles_mcp-2.0.0.tar.gz`。**仅打包，未执行任何发布/上传动作**（`twine`/`uv publish` 均未触碰，发布由用户本人执行）。
- 首次打包后发现 sdist 把内部研发文档也打了进去（`project-docs/`、`.claude/settings.local.json`、`CLAUDE.md`），据此给 `pyproject.toml` 增加 `[tool.hatch.build.targets.sdist]` 的 `exclude` 规则并重新打包。

### 关键变更
- `pyproject.toml`：新增 `[tool.hatch.build.targets.sdist]`，`exclude = ["/project-docs", "/.claude", "/CLAUDE.md", "/docs", "/.env"]`（gitignore 风格锚定 glob）。未改动 `[tool.hatch.build.targets.wheel]`（wheel 早已用 `packages = ["src/uniarticles"]` 限定范围，本无此问题）。
- `dist/`（gitignore 排除，不入库）：重新生成 wheel + sdist。

### 验证结果
- 重新打包后 sdist 已不含 `CLAUDE.md`/`.claude`/`project-docs`/`docs`；wheel 未被误伤，仍含全部 9 个 `uniarticles/*.py` 模块（含 `scopus.py`/`sciencedirect.py`）。
- 版本号仍为 2.0.0（pyproject / wheel 文件名 / sdist 文件名 / METADATA 一致）。
- **安全项**：`.env`（真实凭据）在 wheel 与 sdist 中均确认无泄漏（本就被 `.gitignore` 排除，exclude 再加双保险）；`docs/elsevier-documentation/` 等内部调研资料本已被 `.gitignore` 排除、未进任何产物，exclude 中同样列入做双保险。

### 下一步计划
- 打包产物已就绪，等待用户本人执行发布（PyPI）。构建侧无待执行步骤。

---
