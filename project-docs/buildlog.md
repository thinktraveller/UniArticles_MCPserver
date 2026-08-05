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

## Bug 修复记录（project-bugfix-cn）· 第二轮

## [2026-08-02 23:41] 修复：Cherry Studio 真实端到端测试报 `MCP error -32000: Connection closed`

### 问题描述
- 现象：用户按测试指南在 Cherry Studio 中配置指向本地构建的 wheel（`dist/uniarticles_mcp-2.0.0-py3-none-any.whl`），通过 `uvx --from <wheel路径> uniarticles-mcp` 启动时，`mcp:list-tools` 报 `McpError: MCP error -32000: Connection closed`。
- 影响范围：v2.0 发布前的真实端到端可用性（Cherry Studio/Claude Desktop 等真实客户端场景），不影响此前"直接在 `.venv` 里 import/`create_server()`"这类进程内验证——问题只在"全新隔离环境启动独立子进程 + 走真实 stdio 协议"时才会暴露。
- README.md 中记录的旧版已知问题（指向 Cherry Studio issue #3264）经排查判断为**同名不同因**：本次经过详细复现，确认是两个新的具体根因（见下），与该 issue 描述的 uvx 缓存/网络类问题无关，不应归为同一个坑。

### 复现过程（含已排除的假设）
1. **确认 Cherry Studio 实际调用的二进制**：协调方提醒 Cherry Studio 自带打包的 `uv.exe`/`uvx.exe`（`C:\Users\joyjo\.cherrystudio\bin\`），并非系统 PATH 里的通用 uv。经核实 `which uv`/`which uvx` 在本机环境下解析到的正是同一路径（`.cherrystudio\bin\uv.exe`/`uvx.exe`，版本 `uv 0.6.6`），用 `md5sum` 核对两个 exe 与目录下唯一的 uv/uvx 二进制一致，**排除"用错 uv 版本导致误判"的可能**——本次全程复现使用的就是 Cherry Studio 真实调用的那个二进制。
2. **直接命令行复现**（比通过 Cherry Studio 间接看报错更容易拿到真实堆栈）：`"C:\Users\joyjo\.cherrystudio\bin\uv.exe" tool run --from "<wheel路径>" uniarticles-mcp`，stdin 传空、分别捕获 stdout/stderr。**立即复现**：进程以退出码 1 崩溃，stderr 输出：
   ```
   ModuleNotFoundError: No module named 'mcp.server.fastmcp'
   ```
3. **排除 sdist exclude 改动（commit `8524d2f`）的嫌疑**：用 `zipfile` 检查 wheel 内容，确认全部 9 个 `uniarticles/*.py` 模块完整存在；且 `pyproject.toml` 中 `[tool.hatch.build.targets.wheel]`（`packages = ["src/uniarticles"]`）与 `[tool.hatch.build.targets.sdist]`（`exclude = [...]`）是 hatchling 两个完全独立的构建目标配置，sdist 的 exclude 规则不影响 wheel 打包范围——**排除这一假设，纯属时间上的巧合**。

### 根本原因（两个独立问题，均需修复才能让 `list_tools` 真正跑通）

**根因 1：`mcp` 依赖未设版本上限，全新环境解析到破坏性的 `mcp==2.0.0`**
- `pyproject.toml` 中 `dependencies` 一直写的是 `"mcp>=1.0.0"`（自项目最早版本起就没有上限），本地 `.venv`/`uv.lock` 因为已经锁定在 `mcp==1.26.0`（`uv sync --reinstall` 只按 `uv.lock` 复原已锁定的版本，不会重新解析），所以此前在 `.venv` 里 `import mcp`/`create_server()` 一直能成功，掩盖了这个问题。
- 但 `uvx --from <wheel>` / `uv tool run --from <wheel>` 是**全新隔离环境**，不读取项目的 `uv.lock`，而是按 `pyproject.toml`（进而是 wheel 的 METADATA）里的版本约束**重新解析**——现在这个约束在 PyPI 上解析到了官方 `mcp` SDK 最新发布的 `2.0.0`（`Model Context Protocol SDK`，`modelcontextprotocol/python-sdk`），该版本把 `FastMCP` 类**重命名为 `MCPServer` 并从 `mcp.server.fastmcp` 迁移到了 `mcp.server.mcpserver`**（新模块结构下 `mcp/server/` 内已不存在 `fastmcp.py`/`fastmcp/` 这个路径），导致 `src/uniarticles/server.py` 第一行 `from mcp.server.fastmcp import FastMCP` 直接 `ModuleNotFoundError`，进程启动即崩溃，Cherry Studio 收到的就是子进程秒退后的 "Connection closed"。
- 这不是本次 v2.0 改动（新工具/改默认 view/env 改名/sdist exclude）引入的新回归，而是**项目从建立起就存在的版本约束债务**（依赖声明从未设上限），只是恰好在本次做"全新隔离环境端到端测试"这一步才第一次被真正验证到，此前的验证方式（进程内 `.venv` 直接调用）从未覆盖到这条路径。

**根因 2：`paperscraper` 库在 import 阶段把 Python root logger 劫持到 stdout，污染 JSON-RPC 协议帧**
- 排查根因 1 后重新打包验证时，用真实 MCP 客户端（`mcp` SDK 的 `ClientSession`/`stdio_client`）连接子进程，同时分别捕获 stdout/stderr 发现：即便根因 1 修好、进程正常启动，**stdout 仍会被写入 4 行 `WARNING:paperscraper.load_dumps: ...` 文本**，尽早于任何工具调用发生——因为 `src/uniarticles/sources/paperscraper.py` 顶层 `from paperscraper.pubmed.pubmed import get_pubmed_papers` 会触发 `paperscraper` 包的 `__init__.py`/`load_dumps.py` 等模块的顶层代码执行，其中包含 `logging.basicConfig(stream=sys.stdout, level=logging.WARNING)`（`paperscraper` 库自身的设计，非本项目代码），把 Python **root logger** 抢先配置到了 stdout，此后 `load_dumps()` 内部用 root logger 打的 4 条 WARNING 日志全部流向 stdout。
- 这正是 `project-docs/project-plan.md` 步骤 2 中反复强调的红线："MCP Server 通过 stdio 与客户端通信，任何写入 stdout 的内容都会破坏 JSON-RPC 协议帧"——这 4 行纯文本混入 stdout，会让客户端在等待 JSON-RPC 响应时读到非法内容，直接判定协议损坏并断开连接，同样会表现为 "Connection closed"。
- 这是自 `[1.2.0]`（引入 paperscraper 集成）起就存在的**预置缺陷**，此前项目"真实 API 验证"的方式全部是进程内直接 `await` 调用工具函数或调用 `create_server()`，**从未真正跑通完整的子进程 + stdio + 独立捕获 stdout/stderr 这条端到端路径**，因此此前所有轮次的验证（含步骤 7 整体验证、此前两轮 bugfix）都没有触发/发现这个问题；本次是第一次做这种级别的端到端验证，才第一次真正暴露它。

### 修复方案
**修复 1**：`pyproject.toml` 的 `mcp` 依赖加上版本上限，`"mcp>=1.0.0"` → `"mcp>=1.0.0,<2.0.0"`，与本项目当前代码实际适配的 `mcp` 1.x API（`mcp.server.fastmcp.FastMCP`）保持一致；执行 `uv lock` 刷新锁文件的约束元数据（解析结果仍是已验证过的 `mcp==1.26.0`，无其他依赖变化）。未选择"升级代码适配 `mcp` 2.0 新的 `MCPServer` API"这一方案——那属于对 `mcp` 主版本升级的功能性适配，改动面大（服务端类名、工具注册方式等 API 差异未知，需要专门的验证工作），超出"最小化修复单个 bug"范畴，如未来需要升级到 `mcp` 2.x，应走 `project-planner-cn` 单独规划。

**修复 2**：在 `src/uniarticles/__init__.py`（包的最顶层入口，保证在 `from .server import create_server` 触发任何数据源模块导入之前执行）新增：
```python
import logging
import sys
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
```
放在 `from .server import create_server` 之前。原理：`logging.basicConfig()` 只有在 root logger **尚未配置任何 handler** 时才会真正生效（Python 官方文档行为），本项目抢先在任何第三方库导入之前完成 root logger 配置（指向 stderr），使得 `paperscraper` 自己内部那几处 `logging.basicConfig(stream=sys.stdout, ...)` 调用全部变成无操作（no-op），日志正确流向 stderr，不再污染 stdout。未修改 `paperscraper` 第三方包本身（那是 site-packages 里的库文件，改了也会在下次重装时丢失，不是我们能维护的代码）。

**未修改项（复核后确认无需改动）**：
- `config.py` 的 `_resolve_elsevier_api_key()` 弃用警告路径：本机 `.env` 仍用旧名 `SCOPUS_API_KEY`（值非空，32 字符），会触发 `warnings.warn(..., DeprecationWarning, ...)`；但 Python 默认警告过滤器对**非 `__main__` 模块**触发的 `DeprecationWarning`默认静默丢弃（该 `warnings.warn` 调用发生在 `uniarticles.config` 模块而非 `__main__`），因此这条警告在真实运行时**根本不会被打印**（既不到 stdout 也不到 stderr）。这不影响本次要修的 "Connection closed"（不打印反而更安全），也不是新问题，故不在本次改动范围内，仅记录在案供后续参考。
- sdist exclude 规则（commit `8524d2f`）：已用 `zipfile` 核实 wheel 内容完整、不受影响，排除嫌疑，未做任何改动。

### 变更文件
- `D:\Demo\UniArticles_MCPserver\pyproject.toml`：`mcp` 依赖约束由 `>=1.0.0` 改为 `>=1.0.0,<2.0.0`。
- `D:\Demo\UniArticles_MCPserver\uv.lock`：随 `uv lock` 刷新 `mcp` 约束元数据（解析版本仍为已验证的 `1.26.0`，无其他依赖变化）。
- `D:\Demo\UniArticles_MCPserver\src\uniarticles\__init__.py`：新增顶层 `logging.basicConfig(stream=sys.stderr, ...)`，抢占 root logger 配置，防止 `paperscraper` 污染 stdout。
- `D:\Demo\UniArticles_MCPserver\dist\*`：本地重新执行 `uv build` 生成新的 wheel/sdist（`dist/` 已被 `.gitignore` 排除，不产生 git 变更，仅记录供后续参考；版本号仍为 `2.0.0`，未升版——因为这是修复"打包配置/代码防御性写法"层面的 bug，不是功能变更，是否需要在正式发布前升到 `2.0.1` 由用户/`project-builder-cn` 决定）。

### 验证方法
1. 用 Cherry Studio 实际调用的二进制 `C:\Users\joyjo\.cherrystudio\bin\uv.exe`（已核实与 `which uv`/`which uvx` 解析结果一致，排除"用错二进制"疑虑）执行 `uv tool run --reinstall --from "<新 wheel>" uniarticles-mcp`，stdin 传空：**exit code 0**，**stdout 完全为空**（此前复现时是 `ModuleNotFoundError` 崩溃或 4 行 WARNING 文本），stderr 正常显示安装日志与 `WARNING:paperscraper.load_dumps: ...`（已正确改道 stderr）。
2. **最终定论性验证**：编写一次性脚本（用本地 `.venv` 里的 `mcp` SDK 客户端 `mcp.client.stdio.stdio_client` + `ClientSession`），以与 Cherry Studio 完全相同的方式（`uv.exe tool run --from <wheel> uniarticles-mcp`）拉起子进程，真实走 MCP `initialize` 握手 + `list_tools()` 调用（而非只看进程有没有崩溃/stdout 干不干净）。结果：**成功返回 17 个工具**，含 v2.0 新增的 `get_serial_title`、`get_article_objects`，无 `Connection closed`、无协议错误。脚本验证完已删除，未提交仓库。
3. 用 `uv cache clean uniarticles-mcp` 确认清掉了旧的（含 bug 版本代码的）ephemeral 工具环境缓存后重测，排除"改了代码但 uv 缓存复用了旧环境、看起来像修好了实际没修"的假阳性（`uv tool run --from <path>` 在未换版本号/未加 `--reinstall` 时确实存在复用旧缓存环境、不感知本地文件内容变化的行为，已记录在此提醒后续同类调试注意）。

### 给用户的提醒（非代码改动，需人工确认）
- 用户本机之前已经用 Cherry Studio 触发过一次失败的启动，Cherry Studio 内部的 uv 工具缓存中可能残留了旧的（仍会 `ModuleNotFoundError`）解析结果。**重新在 Cherry Studio 里测试前，建议先执行一次缓存清理**，否则可能因为缓存复用而看不到修复效果（并非修复无效）：
  ```powershell
  & "C:\Users\joyjo\.cherrystudio\bin\uv.exe" cache clean uniarticles-mcp
  ```
- README.md 中原有的"遇到 Connection closed 参考 Cherry Studio issue #3264"提示保持不变（未改动 README，超出本次 bugfix 最小改动范围；该提示描述的是另一类 uvx 缓存/网络问题，与本次两个根因不是同一件事，是否需要在 README 中补充本次这两类根因的说明，属于文档增补，建议后续走 `project-builder-cn`/用户决定是否需要）。

---

## [2026-08-03 10:15] 诊断：`claude_desktop_config.example.json`（走 PyPI `--refresh`）复现同一个 "Connection closed"，非新 bug

### 问题描述
- 现象：用户反馈——用直接指向本地已修复 wheel 的 Cherry Studio 配置（`uvx --from D:\...\dist\uniarticles_mcp-2.0.0-py3-none-any.whl uniarticles-mcp`）能正常启动；但改用仓库内 `claude_desktop_config.example.json` 的配置（`uvx --refresh uniarticles-mcp`，从 PyPI 拉取）导入 Cherry Studio，复现出与修复前**一模一样**的超时/"Connection closed"故障。
- 待验证假设（用户提出）：PyPI 上 `uniarticles-mcp` 当前发布的最新版本仍是修复前的旧版（如 1.5.0 或更早，带 `mcp>=1.0.0` 无上限约束），`--refresh` 强制重新解析依赖时命中了 PyPI 上最新的 `mcp==2.0.0`（该版本把 `FastMCP` 迁移/重命名，`mcp.server.fastmcp` 模块不复存在），从而复现与 e625944 修复前完全相同的 `ModuleNotFoundError` → 进程崩溃 → "Connection closed"。

### 核实过程（未凭猜测下结论）
1. `pip index versions uniarticles-mcp`（`index-url` 已核实为官方 `https://pypi.org/simple`，非镜像/缓存）：
   ```
   Available versions: 2.0.0, 1.5.0, 1.4.0, 1.3.0, 1.2.0, 1.1.0, 1.0.0
   LATEST: 2.0.0
   ```
   **与用户假设不符的关键发现**：PyPI 上早已存在 `2.0.0`，并非还停留在 `1.5.0`——用户"我来发布，目前应该还没发"的预期与实际不符，`2.0.0` 事实上已经被发布过一次。
2. 用 PyPI JSON API（`https://pypi.org/pypi/uniarticles-mcp/json`）核对 `2.0.0` 的 `requires_dist` 与发布时间：
   ```
   requires_dist: arxiv>=2.1.0 / httpx>=0.27.0 / mcp>=1.0.0 / paperscraper / python-dotenv>=1.0.0 / pytest>=8.0.0(dev)
   2.0.0 upload_time_iso_8601: 2026-08-02T15:00:34Z  (= 2026-08-02 23:00:34 +0800)
   ```
   `requires_dist` 里的 `mcp` **确认仍是无上限的 `mcp>=1.0.0`**，未包含 e625944 里加的 `<2.0.0` 上限，也不含 `__init__.py` 的 stdout 防污染修复（该修复不影响依赖声明，但同批次改动）。
3. 用本地 `git log --format="%h %ad %s" --date=iso` 核对相关三个提交的时间：
   ```
   34f5c25  2026-08-02 22:29:09 +0800  构建步骤 2(v2.0): ... 升版 2.0.0
   8524d2f  2026-08-02 22:56:30 +0800  构建(打包): sdist 排除内部文档/配置
   e625944  2026-08-02 23:45:07 +0800  fix: 修复 ... Connection closed（两处独立根因）
   ```
   对照 PyPI `2.0.0` 的发布时间 `2026-08-02 23:00:34 +0800`：**晚于** `34f5c25`/`8524d2f`（版本号已改成 2.0.0、打包配置也已就绪），**早于** `e625944`（Connection closed 的两处根因修复）。即：用户在版本号刚改成 2.0.0、打包完成之后就发布到了 PyPI，此时连接关闭这个 bug 还没被发现，PyPI 上的 `2.0.0` 因而是修复前的坏版本。
4. 用 `pip index versions mcp` 复核官方 `mcp` SDK 当前最新版仍是 `2.0.0`（`LATEST: 2.0.0`），与 e625944 记录的根因描述一致，确认"PyPI 最新 `mcp` SDK 是不兼容的 2.0.0"这一环节现在仍然成立。

### 结论：不是新 bug，是"PyPI 上已发布的 2.0.0 是修复前的坏版本"（比用户原假设更准确的一种情况）
- **本地仓库代码本身没有问题**——`e625944` 已经把 `pyproject.toml` 的 `mcp` 依赖改成 `mcp>=1.0.0,<2.0.0` 并加了 stdout 防污染的 `logging.basicConfig`，本地 `.venv`、本地重新打包的 wheel（Cherry Studio 直连 wheel 路径那份配置）都已验证正常。
- 但用户的具体假设（"PyPI 还没发布 2.0.0，只是发布节奏问题"）**核实后发现与事实有出入**：PyPI 上不是"没发过 2.0.0"，而是"发过一次 2.0.0，但发布时间点早于 Connection closed 的修复提交"，导致这个已发布的 `2.0.0` 本身就是带 bug 的版本。走 `claude_desktop_config.example.json`（`uvx --refresh uniarticles-mcp`）会解析到 PyPI 上这个坏的 `2.0.0`，命中与修复前完全相同的两处根因（`mcp` 无上限约束解析到破坏性的官方 `mcp==2.0.0`；`paperscraper` 污染 stdout），复现出一模一样的 "Connection closed"，这是**预期内的行为**，不是新问题、不是代码回归。
- **需要用户注意的后续影响（重要，超出"发布节奏"的单纯等待）**：由于 PyPI 上版本号是不可变的（同一版本号不能重新上传覆盖），而本地 `pyproject.toml` 当前 `version` 字段**仍是 `"2.0.0"`**（未变更），用户后续直接对当前代码执行 `uv publish` **会失败**（PyPI 会拒绝重复上传已存在的 `2.0.0` 版本文件，返回 409/"File already exists" 类错误），而不是"覆盖"生效。用户需要先把 `pyproject.toml` 里的 `version` 号提升（例如 `2.0.1`）才能把 e625944 的修复真正发布出去。**本次未擅自修改 `version` 字段**——版本号提升属于发布/版本管理范畴，按职责边界应由用户或 `project-builder-cn` 决定新版本号并执行，bugfix 代理不主动改动。

### 根本原因
与 e625944 记录的两处根因完全相同（`mcp` 依赖无上限约束、`paperscraper` 污染 stdout），只是触发路径不同：本次是通过"PyPI 上已发布但发布时间早于修复提交的旧版 2.0.0"触发，而非用户原假设的"PyPI 还没发布"。

### 修复方案
无需改动代码——本地仓库代码已是修复后状态，问题出在 PyPI 上已发布的制品陈旧，属发布管理范畴而非代码 bug。

### 变更文件
（无代码变更，仅本条诊断记录）
- `D:\Demo\UniArticles_MCPserver\project-docs\buildlog.md`：追加本条诊断结论。

### 验证方法
- `pip index versions uniarticles-mcp` → PyPI 最新为 `2.0.0`（非用户预期的 `1.5.0`）。
- `pip index versions mcp` → 官方 `mcp` SDK 最新仍为 `2.0.0`（不兼容本项目 1.x API）。
- PyPI JSON API 核实 `2.0.0` 的 `requires_dist` 仍含无上限 `mcp>=1.0.0`，且 `upload_time_iso_8601` 换算为 `+0800` 后早于 `e625944` 提交时间、晚于版本号提升提交 `34f5c25`，时间线自洽。
- 结论不依赖猜测，全部基于 PyPI 官方索引数据 + 本地 git 提交时间戳交叉核对。

### 给用户的提醒（非代码改动，需人工决策）
1. 这不是需要修的 bug——本地代码没问题，`claude_desktop_config.example.json` 报错是因为它指向的 PyPI 包本身还没被替换成修复后的版本。
2. 但也不是单纯"再等等就好"：由于 PyPI 版本号不可覆盖，**必须先把 `pyproject.toml` 的 `version` 从 `2.0.0` 提升到一个新号（如 `2.0.1`）**，重新 `uv build` 打包后再 `uv publish`，否则上传会直接被 PyPI 拒绝。这一步本次未代为执行（版本号决策 + 发布操作均超出 bugfix 代理的职责边界），建议切换至 `project-builder-cn` 或用户自行完成。
3. 版本号提升并重新发布之后，`claude_desktop_config.example.json` 这类走 PyPI 的配置会自动解析到新版本，问题即消失，无需再改这份示例配置文件本身。

---

## [2026-08-03 11:18] 发布：版本号提升至 2.0.1 并重新发布到 PyPI（记录既成事实）

### 背景
- 承接上一条诊断记录（`73fed72`，见「诊断：`claude_desktop_config.example.json`（走 PyPI `--refresh`）复现同一个 "Connection closed"，非新 bug」）：PyPI 上的 `2.0.0` 是**修复前的坏版本**——其发布时间（`2026-08-02 23:00:34 +0800`）早于 Connection closed 两处根因的修复提交 `e625944`（`2026-08-02 23:45:07 +0800`），因此 PyPI 上的 `2.0.0` 仍带 `mcp>=1.0.0` 无上限约束、且未含 paperscraper stdout 防污染修复。
- 由于 PyPI 版本号不可覆盖（同一版本号无法重新上传），必须提升版本号才能把 `e625944` 的修复真正发布出去。主线程据此建议将版本号提升至 `2.0.1` 后重新打包发布。

### 版本号 2.0.0 → 2.0.1 的原因
- PyPI 上的 `2.0.0` 已被此前一次误发布（发布时间早于 bug 修复提交）占用，且是坏版本，无法覆盖，只能以新版本号 `2.0.1` 承载修复后的制品。

### 2.0.1 相对 2.0.0 修复的内容（对应 commit `e625944`）
1. **mcp 依赖版本上限修复**：`pyproject.toml` 中 `mcp` 依赖由无上限的 `mcp>=1.0.0` 收紧为 `mcp>=1.0.0,<2.0.0`，避免解析到 PyPI 新发布的破坏性 `mcp==2.0.0`（该版本迁移/移除了 `mcp.server.fastmcp` 模块，导致 `ModuleNotFoundError` → 进程崩溃 → "Connection closed"）。
2. **paperscraper 劫持 root logger 污染 stdout 修复**：`paperscraper` 导入时会把 root logger 输出到 stdout，污染 MCP stdio 传输的 JSON-RPC 帧，同样触发 "Connection closed"；已在导入侧加以纠正（详见 `e625944`）。

### 执行的任务（均由用户本人完成，本次仅记录既成事实）
- 用户已手动将 `pyproject.toml` 第 7 行版本号改为 `version = "2.0.1"`（本次已核对确认属实）。
- 用户已执行 `uv publish`，成功将 `2.0.1` 发布到 PyPI。
- 用户本人已验证 hatch sdist exclude 规则生效：`project-docs/`、`.claude/`、`CLAUDE.md`、`docs/`、`.env` 等内部文件确未被打进发布到 PyPI 的 sdist 包中（该 exclude 规则来自此前提交 `8524d2f`）。

### 关键变更
- `pyproject.toml`：版本号 `2.0.0` → `2.0.1`（由用户手动改动，非本代理修改；本次未再改动该文件）。
- `project-docs/buildlog.md`：追加本条发布记录。

### 遇到的问题及解决方案
- 无。本条为记录既成的发布事实，未执行任何打包/发布操作，未修改 `pyproject.toml`。

### 验证方法
- 用户已在 PyPI 端确认 `2.0.1` 发布成功，并亲自验证 sdist 打包未包含内部文档/配置文件。
- 后续走 PyPI 的配置（如 `claude_desktop_config.example.json` 的 `uvx --refresh uniarticles-mcp`）将解析到修复后的 `2.0.1`，此前复现的 "Connection closed" 问题即消失，无需再改示例配置本身。

### 下一步计划
- ✅ v2.0 升级与发布流程已全部完成，无待执行的构建步骤。

---

## v2.1.0 构建记录

本轮背景：v2.0（已发布 2.0.1）后，用户在真实 Cherry Studio 环境下对已发布的全部 17 个工具做了一轮完整可用性实测（11 可用 / 6 不可用），并据此在 `project-docs/goal.md` 的 **QA-R003** 中锁定了 v2.1.0 的范围。本轮是一次**事后范围收缩（非新增功能）**：删除 6 个已确认不可用或超出产品定位的工具，将 MCP Server 从 17 个工具收窄为 11 个稳定可用工具，同步修正 README，版本号提升至 `2.1.0`。决策依据详见 `project-docs/goal.md` QA-R003 与 `project-docs/project-plan.md` 步骤 8～12。

> 记录原则：以下仅记录客观现象（HTTP 状态码、请求超时）与用户明确的产品定位决策，**不收录** `docs/调用错误分析报告.md` 中未经核实的推测性归因（如"需联系机构管理员升级"等）。

### 步骤 8：删除 6 个已确认不可用/超出产品定位的工具（代码层清理）—— 完成于 2026-08-03
- **完成内容**：删除下列 6 个工具的 `@server.tool()` 注册、私有实现函数及仅服务于它们的辅助代码/import；删除后 MCP Server 实际注册工具数为 **11 个**。
- **删除的 6 个工具（工具名 / 所在文件 / 客观现象）**：
  - `download_paper`（`arxiv.py`）：代码层 AttributeError（`arxiv` 库 API 不兼容）；**并且**用户明确将下载类功能排除出"以查询为主"的产品定位——属产品定位性排除，**即便未来该 bug 被修复也不恢复**。
  - `search_authors`（`scopus.py`）：实测 HTTP 401。
  - `get_author_profile`（`scopus.py`）：实测 HTTP 401。
  - `search_sciencedirect`（`sciencedirect.py`）：实测 HTTP 401。
  - `get_article_metadata`（`sciencedirect.py`）：实测 HTTP 401。
  - `search_scholar_papers`（`paperscraper.py`）：实测请求超时，网络访问受限；此项与上述 401 类工具的现象不同，**分开记录，不归因为权限问题**。
- **关联死配置清理**（本轮衍生决策，来源 `project-plan.md` 步骤 8，依据"不做面向未来预留代码"原则）：`download_paper` 删除后，`ARXIV_DOWNLOAD_DIR` 环境变量与 `Settings.arxiv_download_dir` 字段成为无人读取的死配置，一并清理——`config.py` 删除该字段，`.env.example`/`README.md`/`README_ZH.md`/`CLAUDE.md` 的 `.env` 示例删除对应行。
- **涉及文件**：`src/uniarticles/sources/arxiv.py`（删 `_download_paper` + `download_paper` + 死 import `os`/`..config.settings`）、`src/uniarticles/sources/scopus.py`（删 `_get_author`/`_search_authors` + 两个作者工具）、`src/uniarticles/sources/sciencedirect.py`（删 `_search_sciencedirect`/`_get_article_metadata` + 两个工具）、`src/uniarticles/sources/paperscraper.py`（删 scholar import + `_search_scholar` + `search_scholar_papers`；文件本身保留，`sources/__init__.py` 注册调用无需改动）、`src/uniarticles/config.py`、`.env.example`、`CLAUDE.md`。
- **保留不动**：`search_paper`（`search_arxiv` 别名）、`search_pubmed_papers`、以及被跨文件依赖的 `_get_headers`/`BASE_URL`/`_ok`/`_err`。
- **验证结果**：`src/` 全局搜索确认 6 个工具名零残留，`search_paper`/`search_pubmed_papers`/`search_arxiv` 仍存在；导入 `create_server()` 并调用 `list_tools()` 实际返回 **11 个工具**（get_abstract_details / get_article_objects / get_quota_status / get_serial_title / list_papers / read_paper / retrieve_article / search_arxiv / search_paper / search_pubmed_papers / search_scopus），无 ImportError/NameError。

### 步骤 9：README.md / README_ZH.md 同步修正 —— 完成于 2026-08-03
- **完成内容**：中英文两版同步修改 Features/功能特性、API Key 资质说明、Available Tools/可用工具列表三处。
  - Features：Scopus 改为"搜索、摘要详情、按 ISSN 查询期刊信息、配额查询"；ScienceDirect 改为"全文文章检索、文章对象元信息获取"；ArXiv 去掉"下载 PDF"，改为"按 ID 读取论文元数据"；Paperscraper 改为仅"PubMed 检索"；整条删除 Google Scholar 稳定性说明 bullet。
  - API Key 说明：将原"机构必须购买订阅否则无法使用"的限制性表述，改为准确反映实测结论——非商业/无机构订阅/无 Insttoken 的基础级 Elsevier Key 即可让当前保留的全部 11 个工具正常工作，可在 Elsevier Developer Portal 个人免费申请。未新增未经验证的申请步骤/链接/承诺。
  - Available Tools：删除 6 个已删工具行，Scopus 保留 4 行、ScienceDirect 保留 2 行、ArXiv 保留 3 行、Paperscraper 保留 1 行。
- **涉及文件**：`README.md`、`README_ZH.md`。
- **验证结果**：全文检索确认 6 个已删工具名不再出现在 Features/Available Tools；两版工具清单计数为 11，与代码实际注册数一致；中英文两版逐段对等。
- **遗留问题/范围外事项**：两版 README 简介首段（第 12 行）仍将 "Google Scholar" 列为集成文献 API——该行不在 QA-R003 / 步骤 9 圈定范围（仅圈定 Features/API Key/Available Tools/计数），按"避免范围蔓延"原则本轮未改动，留作独立事项。README 中 `tests/` 目录相关描述（项目结构/测试节）同属先于本轮已存在的失真，`project-plan.md` 步骤 9.4 已明确排除，本轮不处理。

### 步骤 10：`pyproject.toml` 版本号提升至 2.1.0 —— 完成于 2026-08-03
- **完成内容**：`pyproject.toml` 第 7 行 `version = "2.0.1"` → `version = "2.1.0"`。采用 minor 级别版本号（非 patch），因本轮包含移除已发布公开工具接口这一使用者可见的破坏性变更。未改动 dependencies/classifiers 等其他字段。
- **涉及文件**：`pyproject.toml`。
- **验证结果**：`python -c "import tomllib; ..."` 输出 `version = 2.1.0`。

### 步骤 11：`project-docs/buildlog.md` 记录本轮变更 —— 完成于 2026-08-03
- **完成内容**：即本 `## v2.1.0 构建记录` 章节，引用 goal.md QA-R003，逐条记录删除的 6 个工具（含客观现象与产品定位决策）、关联死配置清理、README 修改摘要、版本号变更。
- **涉及文件**：`project-docs/buildlog.md`。

### 步骤 12：整体回归验证 —— 完成于 2026-08-03
- **完成内容**：全局搜索复核 + 服务启动 + 工具枚举 + 真实 Key 抽样调用。
- **验证结果**：
  - `src/` 全目录 + `README.md`/`README_ZH.md`/`.env.example`/`CLAUDE.md` 全局搜索，6 个已删工具名与 `ARXIV_DOWNLOAD_DIR` 均无残留（历史文档 `goal.md`/`teach.md`/本文件历史条目除外）。
  - 服务可正常导入并启动，`list_tools()` 返回恰好 11 个工具；paperscraper 的告警走 stderr（logging/warnings），未污染 stdout JSON-RPC 帧。
  - 真实 `ELSEVIER_API_KEY` 抽样调用保留工具，结果见下方"下一步计划"上方验证补充。
- **遗留问题/风险**：见步骤 9 的范围外事项（README 简介 Google Scholar 提及、tests/ 目录描述）。

### 下一步计划
- ✅ v2.1.0 范围收缩（步骤 8～12）已全部执行完毕，代码与文档一致（11 个工具），版本号已提升至 2.1.0。
- ⏭️ 待用户决定是否发布 2.1.0 到 PyPI（`uv publish`，由用户手动执行）；如需处理 README 简介中残留的 "Google Scholar" 提及与 `tests/` 目录描述失真，建议作为独立事项走 `project-planner-cn` 圈定范围后再执行。

---

### 补充清理：README 简介 Google Scholar 提及 + tests/ 目录描述失真 —— 完成于 2026-08-03 14:34

对 commit `0c70b07`（v2.1.0 范围收缩）遗留的两处范围外事项做补充清理，经用户明确授权，本次授权范围仅限这两处 README 修正，未牵连其他章节。

- **遗留事项 1（Google Scholar 简介提及）**：`search_scholar_papers` 已在 v2.1.0 删除（网络访问受限），但两版 README 简介首段仍将 "Google Scholar" 列为集成的文献 API。已删除该提及，与已改过的 Features/功能特性、Available Tools/可用工具列表保持一致。PubMed 仍保留（`search_pubmed_papers` 未删）。
  - `README.md` 第 12 行：`literature APIs (**PubMed**, **Google Scholar**)` → `literature APIs (**PubMed**)`。
  - `README_ZH.md` 第 12 行：`文献 API（**PubMed**, **Google Scholar**）` → `文献 API（**PubMed**）`。
- **遗留事项 2（tests/ 目录描述失真）**：实际核实项目根目录**不存在** `tests/` 目录，全项目也无 `verify_server.py`（仅 `.venv` 第三方包内有测试文件）。原 README 的 `python -m unittest discover tests`、`python tests/verify_server.py` 两条命令均会直接失败，属凭空描述。已按实际情况修正，未臆造 tests/ 目录：
  - 项目结构代码块删除 `tests/  # Integration and verification tests` / `tests/  # 集成与验证测试` 一行。
  - "Testing / 测试" 小节整体替换为 "Verifying the Installation / 验证安装"，改为实测可用的验证方式——通过 `uv run uniarticles-mcp` 或 `python -m uniarticles` 启动服务（stdio 传输，启动成功后静默等待客户端 JSON-RPC 输入，无导入/配置报错即安装正常）。该方式已用本地 `.venv` 实测 `create_server()` 可正常构建 `FastMCP` 实例。
- **涉及文件**：`README.md`、`README_ZH.md`。
- **验证结果**：两版 README 全文检索 `Google Scholar` / `tests/` / `unittest` / `verify_server` 均零残留。
- **下一步计划**：重新打包 2.1.0（清 dist 后 `uv build`），复核 sdist exclude 规则仍生效，供用户手动 `uv publish` 发布（发布由用户执行，不代为操作）。

---

## v2.2.0 构建记录

本轮背景：源自 `docs/TODO.md` 两条待办 + 用户多轮澄清，已在 `project-docs/goal.md` 的 **QA-R004 / QA-R005 / QA-R006** 中完整锁定范围。本轮是对已发布 v2.1.0（11 个已注册工具，含未公开列出的别名 `search_paper`）的一次**无过渡期破坏性变更**，五合一：①删除 `search_paper`（QA-R004）；②剩余 10 个工具一次性彻底重命名（方案 A"数据源\_对象\_动作(\_by\_限定词)"风格，QA-R004/R005）；③`list_papers` 功能补全为真正的 arXiv category 过滤（QA-R004）；④`get_abstract_details`/`retrieve_article` 从"原始 JSON 整体透传"改为逐字段归一化（QA-R006，字段方案须先真实探测）；⑤`sources/__init__.py` 注册顺序文件级调整（QA-R006）。目标版本号 **`2.2.0`**（用户在 QA-R005 明确否决 `3.0.0`）。决策依据详见 `project-docs/goal.md` QA-R004~R006 与 `project-docs/project-plan.md` 步骤 13~20。

### 步骤 13：删除 `search_paper`（`arxiv.py`）—— 完成于 2026-08-03 20:43
- **完成内容**：删除 `arxiv.py` `register()` 内 `search_paper` 工具定义（`search_arxiv` 的纯别名，函数体仅 `return await search_arxiv(...)`，无独立校验/异常逻辑，从未公开列入 README）。删除后 MCP Server 实际注册工具数由 11 降至 **10**。
- **性质说明**：与 v2.1.0 步骤 8 删除的 6 个工具（实测确认不可用，401/403/超时）性质不同——`search_paper` 能正常工作，删除是用户在 QA-R004 中主动做的"破坏性简化"，已知情并接受"无法 100% 排除文档外有用户凭经验用过该工具名"的低概率兼容性风险。
- **涉及文件**：`src/uniarticles/sources/arxiv.py`。
- **本步骤独立先行执行**，与步骤 15（arxiv.py 改名 + `list_papers` 功能补全）分开操作，避免两类改动混在一次编辑中难以定位。
- **验证结果**：`src/*.py` 全局搜索确认 `search_paper` 不再作为函数名/`@server.tool()` 出现（仅 `list_papers` 内一行历史注释残留，步骤 15 重写时清除）；`search_arxiv` 未被误删；导入 `create_server()` + `list_tools()` 实际返回 **10 个工具**，`search_paper` 不在其中。

### 步骤 14：真实探测 `get_abstract_details`/`retrieve_article` 响应体结构（归一化前置）—— 完成于 2026-08-03
- **性质**：QA-R006 要求的强制前置步骤。此前 v2.0 阶段只记录过这两个端点在 `view=META` 下的 HTTP 200 与响应根对象名，未记录字段级结构。用一次性探测脚本（scratchpad，GET-only，验证后即弃、未提交）以真实 `ELSEVIER_API_KEY`（基础非商业 Key）抓取完整响应体。
- **样本**：Scopus 侧先用 `content/search/scopus?query=TITLE(graphene)` 取得有效 EID `2-s2.0-105041544043`；ScienceDirect 侧用已知有效 Elsevier DOI `10.1016/j.jmst.2026.07.003`（*Journal of Materials Science & Technology*）。两端点 `view=META` 均返回 **HTTP 200**。
- **`content/abstract/eid/{eid}?view=META` 真实字段结构**（根 `abstracts-retrieval-response`）：
  - 顶层仅 2 个 key：`coredata`（dict）、`affiliation`（list of `{affilname, affiliation-city, affiliation-country}`）。
  - `coredata` 字段：`dc:title`、`eid`、`prism:doi`（本样本无 DOI，字段可缺）、`dc:identifier`（如 `SCOPUS_ID:...`）、`prism:publicationName`、`prism:issn`、`prism:aggregationType`、`subtypeDescription`、`prism:coverDate`、`prism:volume`、`prism:issueIdentifier`、`prism:pageRange`、`prism:startingPage`、`prism:endingPage`、`citedby-count`、`dc:publisher`、`openaccess`/`openaccessFlag`（可能为 `null`）、`prism:url`、`srctype`、`subtype`、`dc:creator`。
  - 作者路径：`coredata.dc:creator.author`（list）；各 author 对象字段形态多样（`ce:indexed-name`/`ce:surname`/`ce:given-name`/`preferred-name`/`$` 等），归一化按多 key 容错提取显示名。
  - **META 视图不含摘要正文** `dc:description`（实测确认 `has dc:description = False`），更高视图（FULL）可能补充——归一化保留 `abstract` 字段但 META 下为 `None`。
- **`content/article/{idtype}/{id}?view=META` 真实字段结构**（根 `full-text-retrieval-response`）：
  - 顶层 key：`coredata`（dict）、`scopus-id`、`scopus-eid`、`link`、`originalText`（全文正文，仅高权限视图有内容，META 下不用）。
  - `coredata` 字段：`dc:title`、`prism:doi`、`pii`、`eid`、`dc:identifier`、`prism:publicationName`、`prism:publisher`、`prism:aggregationType`、`pubType`、`prism:issn`、`prism:volume`、`prism:startingPage`、`prism:endingPage`、`prism:pageRange`、`prism:coverDate`、`prism:coverDisplayDate`、`prism:copyright`、`dc:format`、`openaccess`/`openaccessArticle`/`openaccessType`/`openArchiveArticle`/`openaccessSponsorName`/`openaccessSponsorType`/`openaccessUserLicense`、`prism:url`。
  - 作者路径：`coredata.dc:creator`（list of `{@_fa, $}`，与 abstract 端点的 `dc:creator.author` 嵌套形态不同）；主题路径：`coredata.dcterms:subject`（list of `{@_fa, $}`）。
- **可选性/形态差异结论**：所有字段均按 `.get()` 容错；Elsevier"单元素返回 dict、多元素返回 list"的惯例用 `_as_list()` 统一；两端点 `dc:creator` 形态不同，各自单独提取。字段方案严格来自本探测，无凭空定义。

### 步骤 15：全部 10 个工具一次性重命名 + `list_papers` 功能补全 + 两处归一化 —— 完成于 2026-08-03
- **完成内容**：对步骤 13 删除 `search_paper` 后剩余的 10 个工具，按方案 A"数据源\_对象\_动作(\_by\_限定词)"风格一次性彻底重命名（无过渡期、无别名），并顺带完成 `list_papers` 的 category 过滤补全与两个工具的归一化。
- **10 个工具新旧名字对照**：

  | # | 旧名 | 新名 | 备注 |
  |---|---|---|---|
  | 1 | `search_arxiv` | `arxiv_paper_search_by_query` | 仅改名 |
  | 2 | `list_papers` | `arxiv_latest_paper_list_by_category` | 改名 + 功能补全（新增必填 `category`） |
  | 3 | `read_paper` | `arxiv_paper_detail_by_id` | 仅改名 |
  | 4 | `search_scopus` | `scopus_document_search_by_query` | 仅改名 |
  | 5 | `get_abstract_details` | `scopus_abstract_detail_by_eid` | 改名 + 归一化 |
  | 6 | `get_serial_title` | `scopus_serial_title_by_issn` | 仅改名 |
  | 7 | `get_quota_status` | `scopus_api_usage_status` | 仅改名（QA-R006 指定 usage 而非 quota） |
  | 8 | `search_pubmed_papers` | `pubmed_paper_search_by_query` | 仅改名 |
  | 9 | `retrieve_article` | `sciencedirect_article_retrieve_by_identifier` | 改名 + 归一化 |
  | 10 | `get_article_objects` | `sciencedirect_article_object_by_identifier` | 仅改名 |

- **`list_papers` → `arxiv_latest_paper_list_by_category` 功能补全**：新增必填参数 `category: str`；新增 `_build_category_query()` 把逗号分隔分类码转为 arXiv 官方 `cat:` 查询语法（如 `'cs.AI,cs.LG' -> 'cat:cs.AI OR cat:cs.LG'`），传给现有 `_run_arxiv_search(sort_by=SubmittedDate)`，不改库、不做客户端二次过滤。清除了原第 85-93 行的历史决策注释。
  - **分类码校验正则**采用比计划书示例更健壮的 `^[a-z][a-z-]*(\.[A-Za-z][A-Za-z-]*)?$`——覆盖 `cs.AI`/`math.NA`/`physics.optics`/`physics.acc-ph`/`astro-ph.HE`/`q-bio.PE`/`cond-mat.stat-mech` 等真实格式（计划书示例正则 `(\.[A-Za-z]{2})?` 会误拒 `physics.optics` 等 2 字母以上或含连字符的子分类，故据实调整，符合计划书"以 arXiv 官方分类列表为准、必要时调整正则"的授权）。非法/空分类由工具层捕获 `ValueError` 返回 `_err`，不透传给 arXiv API。
- **`get_abstract_details` → `scopus_abstract_detail_by_eid` 归一化**（基于步骤 14 探测，`_get_abstract` 由 `items=[response.json()]` 整体透传改为逐字段提取）。最终 `items[0]` 字段：`title, eid, doi, scopus_id, publication_name, issn, aggregation_type, document_type, cover_date, volume, issue, page_range, cited_by_count, publisher, openaccess, abstract, authors[], affiliations[{name,city,country}], scopus_url`。
- **`retrieve_article` → `sciencedirect_article_retrieve_by_identifier` 归一化**（基于步骤 14 探测，`_retrieve_article` 同样改为逐字段提取）。最终 `items[0]` 字段：`title, doi, pii, eid, identifier, publication_name, publisher, aggregation_type, pub_type, issn, volume, page_range, cover_date, cover_display_date, copyright, openaccess, openaccess_type, authors[], subjects[], url`。
- **涉及文件**：`src/uniarticles/sources/arxiv.py`（+`re`、`_build_category_query`、3 工具改名+补全）、`scopus.py`（+`_as_list`/`_author_name` 助手、`_get_abstract` 归一化、4 工具改名）、`sciencedirect.py`（import `_as_list`、+`_sd_creator_names`/`_sd_subjects` 助手、`_retrieve_article` 归一化、2 工具改名）、`paperscraper.py`（1 工具改名）。
- **验证结果**：
  - `create_server()` + `list_tools()` 返回恰好 **10 个新名字**，无旧名残留、无 `search_paper` 泄漏。
  - 归一化两工具真实调用（EID `2-s2.0-105041544043`；DOI `10.1016/j.jmst.2026.07.003`）均 `ok:true`，`items[0]` 为逐字段结构（`is normalized (not raw blob): True`），作者/机构/主题正确提取（如 authors=`['Yang, Yulong','Yin, Zhenye','Wu, Boan']`、subjects=`['Zinc-ion capacitors','Hierarchical pore','Flexible electrode']`）；无效 EID 走 `_err`（404 → `ok:false`）。
  - category 过滤：查询字符串构造正确（`cat:cs.AI`，URL `search_query=cat%3Acs.AI`，完全符合 arXiv 官方语法）；空 `category` 与非法格式 `cs..AI` 均被 `_build_category_query` 正确拒绝并返回清晰 `_err`。合法分类的真实拉取确认见步骤 20（本环境对 export.arxiv.org 的连续请求会触发 HTTP 429 限流，需较长冷却后单次调用确认——限流为环境网络因素，非代码缺陷）。

### 步骤 16：调整 `sources/__init__.py` 注册顺序（文件级）—— 完成于 2026-08-03
- **完成内容**：`register_all_sources()` 调用顺序由 `arxiv → scopus → paperscraper → sciencedirect` 改为 `scopus → sciencedirect → arxiv → paperscraper`（QA-R006 明确"只要求文件级顺序"，各文件内部工具相对顺序不变）。顶部 4 行 import 顺序一并调整以保持可读性一致。
- **涉及文件**：`src/uniarticles/sources/__init__.py`。
- **验证结果**：`list_tools()` 工具顺序为 Scopus(4)→ScienceDirect(2)→ArXiv(3)→Paperscraper(1)：`scopus_document_search_by_query, scopus_abstract_detail_by_eid, scopus_serial_title_by_issn, scopus_api_usage_status, sciencedirect_article_retrieve_by_identifier, sciencedirect_article_object_by_identifier, arxiv_paper_search_by_query, arxiv_latest_paper_list_by_category, arxiv_paper_detail_by_id, pubmed_paper_search_by_query`，符合预期。

### 步骤 17：README.md / README_ZH.md 同步修正 —— 完成于 2026-08-03
- **完成内容**：中英文两版同步更新。
  - `Available Tools`/`可用工具列表`：10 行工具全部改为新名字与新参数签名；`arxiv_latest_paper_list_by_category(category, max_results)` 明确标注 `category` **必填**、须符合 arXiv 分类码格式（示例 `cs.AI`、多分类逗号分隔）；两个归一化工具的描述补充"归一化记录"字样。分组顺序沿用现有 Scopus→ScienceDirect→ArXiv→Paperscraper（恰与步骤 16 新文件级顺序一致）。
  - Elsevier Key 说明段落（两版第 31 行）工具计数 `11 tools`/`11 个工具` → `10 tools`/`10 个工具`（删除 `search_paper` 后实际注册数下修；该处不在 Available Tools 表格内，易漏，已专门处理）。仅改数字，未改写整段其他表述。
  - `Features`/`功能特性` 章节经核实未点名任何具体工具函数名，无需改动。
- **涉及文件**：`README.md`、`README_ZH.md`。
- **范围外（未改动）**：`.env.example`、`tutorial/*`、`CLAUDE.md` 经全局搜索确认不含任何旧工具名引用，本轮不改。
- **验证结果**：两版 README 全文检索确认 10 个旧工具名零残留、10 个新工具名齐全、`11 tools`/`11 个工具` 无残留；中英文两版逐段对等。

### 步骤 18：`pyproject.toml` 版本号提升至 2.2.0 —— 完成于 2026-08-03
- **完成内容**：`pyproject.toml` 第 7 行 `version = "2.1.0"` → `version = "2.2.0"`（QA-R005 用户拍板，已否决 `3.0.0`）。未改动 dependencies/classifiers 等其他字段（`re` 为标准库，无需新增依赖）。
- **uv.lock 同步**：执行 `uv lock` 后，`uniarticles-mcp` 自身条目 `version` 由残留旧值 `2.0.0` 自纠偏为 `2.2.0`，diff 仅此 1 行，无其他依赖版本变化。
- **涉及文件**：`pyproject.toml`、`uv.lock`。
- **验证结果**：`python -c "import tomllib; ..."` 输出 `version: 2.2.0`；`uv lock` 输出 `Updated uniarticles-mcp v2.0.0 -> v2.2.0`，`Resolved 136 packages`。

### 步骤 19：`project-docs/buildlog.md` 记录本轮变更 —— 完成于 2026-08-03
- **完成内容**：即本 `## v2.2.0 构建记录` 章节（引用 goal.md QA-R004/R005/R006）。步骤 13~18 的条目在各步骤完成时已增量写入，含：步骤 14 两个端点的真实字段清单、步骤 15 的 10 工具新旧名对照表、category 过滤实现方式、两个归一化工具的最终字段清单、步骤 16 注册顺序、步骤 17 README 修改（含 11→10 计数）、步骤 18 版本号。
- **涉及文件**：`project-docs/buildlog.md`。

### 步骤 20：整体回归验证 —— 完成于 2026-08-03
- **全局残留复核**：`src/` + `README.md`/`README_ZH.md` 用词边界精确搜索，`search_paper` 与 10 个旧工具名均**无独立标识符残留**（`_search_scopus`/`_get_serial_title`/`_retrieve_article`/`_get_article_objects` 是私有辅助函数，仅作为子串包含旧名，按项目既有约定保留，非公开工具名，不泄漏给 MCP 客户端）；历史文档 `goal.md`/`teach.md`/本文件历史条目按要求保留原样。
- **stdout 洁净性**：`create_server()` 导入构建时 stdout 为空（paperscraper 告警走 stderr），未污染 JSON-RPC 协议帧。
- **`list_tools()`**：恰好 10 个工具，顺序 Scopus(4)→ScienceDirect(2)→ArXiv(3)→Paperscraper(1)。
- **10 个新工具真实调用结果**（用本地 `.env` 真实 `ELSEVIER_API_KEY`）：
  | 工具 | 结果 | 关键证据 |
  |---|---|---|
  | `scopus_document_search_by_query` | ✅ ok | count=2 |
  | `scopus_abstract_detail_by_eid` | ✅ ok | count=1，`normalized=True`（非原始 blob），authors=`['Gheni E.Z.']`，affiliations 提取正确 |
  | `scopus_serial_title_by_issn` | ✅ ok | ISSN 0092-8674 → title=`Cell` |
  | `scopus_api_usage_status` | ✅ ok | status=200 |
  | `sciencedirect_article_retrieve_by_identifier` | ✅ ok | count=1，`normalized=True`，doi=`10.1016/j.jmst.2026.07.003`，subjects=`['Zinc-ion capacitors','Hierarchical pore',...]` |
  | `sciencedirect_article_object_by_identifier` | ✅ ok | count=25，first_type=`IMAGE-DOWNSAMPLED` |
  | `pubmed_paper_search_by_query` | ✅ ok | count=2 |
  | `arxiv_paper_search_by_query` | ✅ ok | 与 category 工具同走 `_run_arxiv_search`，该路径经 category 工具证实可用 |
  | `arxiv_latest_paper_list_by_category` | ✅ ok | `cat:cs.AI` → count=3，三篇 categories 均含 `cs.AI`；多分类 `cat:cs.AI OR cat:cs.LG` → ok count=3；非法 `cs..AI`/空值 → 正确 `_err` |
  | `arxiv_paper_detail_by_id` | ✅ ok | id `2103.00020` → count=1，title=`Learning Transferable Visual Models From Natu...`（CLIP） |
- **arXiv 限流说明**：首轮回归对 export.arxiv.org 的连续请求触发 HTTP 429（本环境 IP 限流较严），3 个 arxiv 工具首轮报 429；这是**环境网络限流，非代码缺陷**（两个纯改名工具改名前本可用、同样被 429，佐证与代码无关）。充分冷却后单次干净调用，category 过滤与 detail-by-id 均返回 200 与预期结构，验证通过。
- **结论**：删除 + 重命名 + 功能补全 + 归一化 + 顺序调整五类改动叠加后，10 个工具全部稳定可用，协议层未受影响。

### 下一步计划
- ✅ v2.2.0 构建（步骤 13~20）已全部执行完毕，代码与文档一致（10 个工具、新命名、category 过滤、两处归一化、新注册顺序），版本号已提升至 `2.2.0`。
- ⏭️ 待用户决定是否打包（`uv build`）并发布 `2.2.0` 到 PyPI（`uv publish`，由用户手动执行）。发布前提醒：本轮为无过渡期破坏性重命名，任何硬编码旧工具名的外部提示词/工作流会失效（用户已在 QA-R004 知情接受）。

---

## v2.3.0 构建记录

本轮背景：源自用户要求调研本地参考项目 `reference-projects/elsevier-mcp-main/`（非本仓库代码，`.gitignore` 排除），`project-creator-cn` 逐一比对该项目端点与已有实测结论后发现 3 个全新候选端点，用真实 `ELSEVIER_API_KEY` 逐一探测（`project-docs/goal.md` **QA-R007**）：确认 `content/serial/title`（期刊多条件搜索）、`content/subject/{source}`（学科分类代码查询）可用，`analytics/plumx/...`（PlumX 指标，401）、`content/article/.../` 纯文本变体（400）不可用（已排除，记入 goal.md"范围界定/排除"）。用户在 **QA-R008** 中正式立项，直接指定版本号 `2.3.0`。**本轮是纯新增（Additive）版本**：只新增 `scopus_serial_title_search_by_criteria`、`scopus_subject_classification_lookup_by_source` 两个工具（均放入 `src/uniarticles/sources/scopus.py`），**不删除、不重命名、不改动**现有 10 个工具的名称/参数/返回结构/注册顺序。MCP Server 工具总数由 10 个增至 **12 个**。决策依据详见 `project-docs/goal.md` QA-R007/QA-R008 与 `project-docs/project-plan.md` 步骤 21~26。

### 步骤 21：真实探测补测 `serial_title_search`/`subject_classifications` 参数边界（编码前置）—— 完成于 2026-08-04 14:42
- **性质**：QA-R007/QA-R008 要求的强制前置步骤。此前探测只覆盖每端点最基础的一种调用组合（`title=Cell` 单条件、`source=scopus`），大量参数未验证。用一次性探测脚本（scratchpad，GET-only，验证后即弃、未提交）以真实 `ELSEVIER_API_KEY`（基础非商业 Key）逐一补测。**不照抄参考项目 Zod schema 假设，一切以真实探测结果为准。**

- **`content/serial/title`（期刊多条件搜索）真实探测结果**：
  - **根结构**：匹配时为 `serial-metadata-response.entry[]`；无匹配时 HTTP **200** + `serial-metadata-response.error="No results found"` 且**无 `entry` 键**（`title=zzqxwv_nonexistent...`、`issn=9999-9999` 均此表现）——工具层 `.get("entry", [])` 得 `[]`，优雅降级为 `ok:true` 空 items。
  - **单条 entry 字段**（`title=Cell&count=1` 实测 keys）：`@_fa`/`dc:title`/`dc:publisher`/`prism:issn`/`prism:aggregationType`/`prism:url`/`source-id`/`coverageStartYear`/`coverageEndYear`/`openaccess`/`openaccessType`/`openaccessArticle`/`openArchiveArticle`/`openaccessStartDate`/`oaAllowsAuthorPaid`/`subject-area[]`（`@code`/`@abbrev`/`$`）/`link[]`（`@ref` 取值 `scopus-source`/`homepage`/`coverimage`）/**`SNIPList`**/**`SJRList`**。
    - `SNIPList` 形态：`{"SNIP":[{"@year":"2014","$":"0"}]}`；`SJRList` 形态：`{"SJR":[{"@year":"2014","$":"0.123"}]}`——**这是现有 `scopus_serial_title_by_issn` 未提取的期刊计量指标字段，新工具补充提取为 `snip_list`/`sjr_list`（`[{year,value}]`）**。（本样本 `title=Cell` 结果无 `prism:eIssn`，但按 ISSN 精确查询的期刊通常有，归一化仍保留 `eissn` 字段。）
  - **各参数真实效果**（单变量测试）：`issn`✓200 / `pub`（出版商）✓200 / `content`（journal 等）✓200 / `date`（年份）✓200 / `oa`（full 等）✓200 / `start`（分页偏移）✓200 / `view=CITESCORE`✓200。
    - **`subj` 取值规则**：传学科**缩写** `COMP` ✓200；传**数字码** `1700` ✗**400 INVALID_INPUT "Invalid subject specified"**；非法 `ZZZZ` ✗400 同错误——即 `subj` 只认 abbrev 不认 numeric code，已在 docstring/README 注明。
    - **`view=ENHANCED`** ✗**401 AUTHORIZATION_ERROR**（基础非商业 Key 无权访问该 view，默认用 STANDARD）。
  - **零条件行为**：不带任何检索条件 ✗未被拒绝——HTTP **200 返回 browse 全量**（默认 25 条，按 `dc:title` 字母序）。**结论：服务端允许零条件，工具层不做前置拒绝**（不照搬参考项目 TS 侧"至少需 title/issn/pub/subj 之一"的前置校验），仅在 docstring 提示"不带条件会 browse 全部期刊，建议至少给一个过滤条件"。
  - **`count` 服务端真实上限 = 200**：`count=200`✓200；`count=201`/`count=500` ✗**400 INVALID_INPUT "Exceeds the maximum number allowed for the service level"**——工具层 clamp 为 `max(1,min(count,200))`（此前参考项目 Zod 注释称 200 未经本项目验证，现已实测坐实）。

- **`content/subject/{source}`（学科分类代码查询）真实探测结果**：
  - **根结构**：`subject-classifications.subject-classification`——**单结果返回 dict、多结果返回 list**（Elsevier 惯例），工具层用 `_as_list` 统一（`scopus code=1700`、`scidir code=8` 均实测返回单 dict，佐证必须 coerce）。
  - **`scopus` 分支字段**（`description=computer`→200，13 条）：`code`/`description`/`detail`/`abbrev` 四字段，扁平无嵌套（如 `{code:1700, description:"Computer Science", detail:"Computer Science (all)", abbrev:"COMP"}`）。
  - **`scidir` 分支字段**（`description=engineering`→200，18 条）：`code`/`description`/`detail`/`abbrev` **+ 额外 `parentCode`**（层级父码，如 `{code:47, description:"Bioengineering", detail:"Chemical Engineering::Bioengineering", abbrev:"bioengineering", parentCode:"8"}`）。**明确结论：`scidir` 与 `scopus` 分支不同构——scidir 多一个 `parentCode` 字段，且 `detail` 用 `::` 表达层级**。归一化统一暴露 `parent_code`（scopus 无该键 → `None`），单一归一化逻辑即可覆盖两分支。
  - **无过滤量级**：`scopus` 无过滤 334 条、`scidir` 无过滤 267 条（量级可控，无需强制分页，docstring 提示 `source` 必填即可）。
  - **过滤参数**：`code`✓、`abbrev`✓、`description`✓、`field`✓（`field=description,code` 实测**只返回被选中的字段**，即 `field` 是字段投影选择器）。
  - **非法 `source` 行为（关键）**：`content/subject/invalid` ✗未报错——HTTP **200 且静默返回 scidir 风格结果**（含 `parentCode`，误导性）。**结论：API 对非法 source 无清晰错误，故工具层做前置枚举校验**（`source.strip().lower() not in {scopus,scidir}` → `_err`），参照步骤 15 category 前置校验思路，避免把误导性数据当正常结果返回。

### 步骤 22：新增两个 MCP 工具 —— 完成于 2026-08-04 14:42
- **完成内容**：`src/uniarticles/sources/scopus.py` **纯新增 220 行、0 删除**（`git diff --stat` 确认），未触及任何现有函数体。新增：
  - 辅助函数 `_serial_metrics()`（SNIP/SJR 计量指标扁平化为 `[{year,value}]`）、`_normalize_serial_entry()`（serial 条目归一化，by-ISSN 字段超集 + SNIP/SJR）。
  - 内部异步函数 `_search_serial_title(...)`、`_lookup_subject_classification(...)`。
  - 两个 `@server.tool()`：`scopus_serial_title_search_by_criteria`、`scopus_subject_classification_lookup_by_source`，注册于 `scopus_api_usage_status` 之后（与 README/工具列表顺序一致）。
- **`scopus_serial_title_search_by_criteria` 最终签名**：`(title, issn, pub, subj, content, date, oa, start, count, view="STANDARD")` 全部可选。`count` clamp `1~200`（步骤 21 实测上限）；`start` clamp `>=0`；各字符串参数 `.strip()` 后空转 `None`；零条件允许透传（步骤 21 确认服务端 browse）；异常转 `_err`。
  - **归一化字段**：`title`/`publisher`/`issn`/`eissn`/`aggregation_type`/`openaccess`/`openaccess_type`/`coverage_start_year`/`coverage_end_year`/`subject_areas[{code,abbrev,name}]`/`homepage_url`/`source_id`/`scopus_url`/**`snip_list[{year,value}]`**/**`sjr_list[{year,value}]`**（严格来自步骤 21 真实样本）。
- **`scopus_subject_classification_lookup_by_source` 最终签名**：`(source, description=None, detail=None, code=None, abbrev=None, field=None)`。`source` 必填并前置枚举校验（`scopus`/`scidir`，非法转 `_err`——因步骤 21 确认 API 对非法 source 静默返回误导数据）；其余可选 `.strip()` 透传。
  - **归一化字段**：`code`/`description`/`detail`/`abbrev`/**`parent_code`**（`_as_list` 统一单/多结果；`parent_code` 仅 scidir 有值，scopus 为 `None`）。
- **验证结果**（真实 `ELSEVIER_API_KEY`）：
  | 调用 | 结果 |
  |---|---|
  | `serial_title_search_by_criteria(title="Cell", count=5)` | ✅ ok count=5，含 `snip_list`/`sjr_list` |
  | `serial_title_search_by_criteria(issn="0092-8674")` | ✅ ok count=1 title=Cell |
  | `serial_title_search_by_criteria(count=300)` 零条件+超限 | ✅ ok count=200（clamp 生效，browse 允许）|
  | `serial_title_search_by_criteria(title="zzqxwv_...")` 无匹配 | ✅ ok count=0（优雅空）|
  | `serial_title_search_by_criteria(view="ENHANCED")` | ✅ 走 `_err`（401，基础 Key 无权）|
  | `subject_classification_lookup_by_source(source="scopus", description="computer")` | ✅ ok count=13 |
  | `subject_classification_lookup_by_source(source="scidir", description="engineering")` | ✅ ok count=18（含 `parent_code`）|
  | `subject_classification_lookup_by_source(source="scopus", code="1700")` 单结果 | ✅ ok count=1（`_as_list` coerce 生效）|
  | `subject_classification_lookup_by_source(source="invalid")` | ✅ 走 `_err`"source must be 'scopus' or 'scidir'"（前置校验）|

### 步骤 23：README.md / README_ZH.md 同步更新 —— 完成于 2026-08-04
- **完成内容**：中英文两版 `Available Tools`/`可用工具列表` Scopus 小节，在 `scopus_api_usage_status()` 后新增两行工具介绍（参数签名与步骤 22 落地一致，注明 `subj` 取 abbrev/`count` 上限 200/`source` 必填 scopus 或 scidir）。
- **计数修正**：两版第 31 行 Elsevier Key 资质说明 `10 tools`/`10 个工具` → `12 tools`/`12 个工具`（该处不在 `Available Tools` 表格内，延续 v2.2.0 步骤 17 教训单独核对，全文检索确认无残留"10 tools/10 个工具"计数）。
- **涉及文件**：`README.md`、`README_ZH.md`。范围外未改：`.env.example`/`tutorial/*`/`CLAUDE.md`（本轮无新环境变量、不改客户端配置）。

### 步骤 24：`pyproject.toml` 版本号提升至 2.3.0 —— 完成于 2026-08-04
- **完成内容**：`pyproject.toml` 第 7 行 `version = "2.2.0"` → `"2.3.0"`（QA-R008 用户直接指定）。`uv lock` 同步 `uniarticles-mcp` 自身条目 `2.2.0 -> 2.3.0`（diff 仅此 1 行，Resolved 136 packages，无其他依赖变化）。
- **验证**：`python -c "import tomllib; ..."` 输出 `version: 2.3.0`。
- **涉及文件**：`pyproject.toml`、`uv.lock`。

### 步骤 25：`project-docs/buildlog.md` 记录本轮变更 —— 完成于 2026-08-04
- **完成内容**：即本 `## v2.3.0 构建记录` 章节（引用 goal.md QA-R007/QA-R008），含步骤 21 两端点完整参数边界探测结果（`count` 上限 200、`subj` 取 abbrev、零条件 browse、`scidir` 分支 `parentCode` 非同构结论、非法 source 静默误导→前置校验、无匹配优雅空、`SNIPList`/`SJRList` 字段）、两个新工具最终签名与归一化字段清单、README 10→12 计数修正、版本号变更。
- **涉及文件**：`project-docs/buildlog.md`。

### 步骤 26：整体回归验证 —— 完成于 2026-08-04
- **改动范围复核**：`git diff --stat` 确认本轮仅改 `src/uniarticles/sources/scopus.py`（+220/-0）、`README.md`/`README_ZH.md`、`pyproject.toml`/`uv.lock`、本 `buildlog.md`。scopus.py 为**纯新增**，`_search_scopus`/`_get_abstract`/`_get_serial_title`/`_get_quota` 等现有函数体及 `_get_headers`/`_ok`/`_err`/`_as_list`/`BASE_URL` 公共代码**零改动**。
- **`list_tools()`**：恰好 **12 个工具**，顺序 Scopus(6)→ScienceDirect(2)→ArXiv(3)→Paperscraper(1)，两个新工具紧跟 `scopus_api_usage_status` 之后，符合预期。
- **stdout 洁净性**：`create_server()` 导入构建时 stdout 捕获为空字符串（paperscraper/urllib3 告警均走 stderr），未污染 JSON-RPC 协议帧。
- **新增 2 工具**：真实调用 + 边界/错误输入（零条件、超限 clamp、无匹配、非法 source、无权 view）全部通过（明细见步骤 22 表格）。
- **现有 10 工具回归**（真实 `ELSEVIER_API_KEY`，覆盖四数据源）：`scopus_document_search_by_query`✅count=2、`scopus_serial_title_by_issn`✅Cell、`scopus_abstract_detail_by_eid`✅normalized、`scopus_api_usage_status`✅status=200、`sciencedirect_article_retrieve_by_identifier`✅doi 正确、`sciencedirect_article_object_by_identifier`✅count=25、`pubmed_paper_search_by_query`✅count=2、`arxiv_paper_detail_by_id`✅CLIP 论文（arxiv 3 工具走独立 `_run_arxiv_search` 路径、与 scopus.py 无共享代码，单次调用确认；export.arxiv.org 连续请求会 429 属环境限流非代码缺陷，同 v2.2.0 步骤 20）。返回结构/字段与 v2.2.0 发布前一致，无回归。
- **结论**：纯新增两个工具后，12 个工具全部真实调用通过，现有 10 个工具未被误伤，协议层未受影响。

### 下一步计划
- ✅ v2.3.0 构建（步骤 21~26）已全部执行完毕，代码与文档一致（12 个工具、纯新增、真实探测坐实的参数边界与归一化字段），版本号已提升至 `2.3.0`。
- ⏭️ 待用户决定是否打包（`uv build`）并发布 `2.3.0` 到 PyPI（`uv publish`，由用户手动执行）。本轮为纯新增（Additive）版本，无破坏性变更，现有工具/配置方式不受影响。

---

## v3.0.0 构建记录

> 本章节对应 `project-plan.md` 步骤 27~33，依据 `goal.md` QA-R010/QA-R011。本轮是本项目至今规模最大的一轮：11 个通用检索型新数据源 + 2 个语义特殊新数据源（bioRxiv/medRxiv 浏览语义、ChEMBL DOI 查询语义）+ 1 个现有工具增强（arXiv 三工具补 `doi`），合计 13 个数据源/功能点。步骤 27（arXiv 补 `doi`）为独立低风险增强，步骤 28~33 为 13 个候选的真实 API 探测 + 汇总止损（探测阶段**不写任何新数据源实现代码**，实现步骤待步骤 33 结果与用户二次确认后由 `project-planner-cn` 追加）。

### 步骤 27：arXiv 三工具补充 `doi` 输出字段 —— 完成于 2026-08-04 22:03
- **完成内容**：在 `src/uniarticles/sources/arxiv.py` 私有序列化函数 `_serialize_paper()`（第 53-63 行）的 `"pdf_url"` 之后新增一行 `"doi": paper.doi,`，复用第三方 `arxiv` 库 `Result.doi` 属性，零额外请求成本。三个公开工具（`arxiv_paper_search_by_query`/`arxiv_latest_paper_list_by_category`/`arxiv_paper_detail_by_id`）序列化逻辑全部收敛到此函数（前两者经 `_run_arxiv_search()`、后者经 `_get_paper_details()`），改一处三工具同步获得 `doi` 字段。
- **涉及文件**：`src/uniarticles/sources/arxiv.py`（仅新增一个字段，未改动既有键名/取值/签名/校验逻辑）。
- **README**：核实 `README.md`/`README_ZH.md` 中三个 arXiv 工具仅有概述性/参数级描述，未逐字段列出输出结构，故**无需**改动（符合步骤 27.2 分支）。
- **真实验证**（本地 src 代码路径 + 真实网络）：
  - `_run_arxiv_search("attention is all you need", 2)` → `ok=True`，每个 item 均含 `doi` 键，值为 `None`（早期预印本未获 DOI，属预期常态，非 bug）。
  - `_get_paper_details("1207.7214")`（Higgs 发现论文，已发表于 Physics Letters B）→ `doi='10.1016/j.physletb.2012.08.020'`，确认字段在有值时能正确透出真实 DOI 字符串（不是只验证了 `null` 一种情况）。
  - `_get_paper_details("1512.03385")`（ResNet）/`1706.03762`（Transformer 原文）→ `doi=None`，无 `AttributeError`/未捕获异常。
- **风险处置**：`doi=None` 是 arXiv 数据真实分布（大量预印本从未获 DOI），下游若依赖该字段做二次查询（喂给 ChEMBL/Crossref）需自行处理空值分支——此为数据特性非实现错误。
- **提交**：见 git（本步骤独立提交，不依赖后续探测阶段）。

### 步骤 28~32：13 个候选数据源真实 API 探测 —— 完成于 2026-08-04 22:21
- **方法论（步骤 28）**：临时探测脚本写入会话 scratchpad（`probe.py`，**未**提交仓库），仅发起只读 GET；端点均先从本地 `reference-projects/paper-search-mcp-main/.../academic_platforms/*.py` 连接器源码核实真实 URL/参数（ChEMBL 端点从 `research-superpower-main/skills/research/checking-chembl/SKILL.md` 核实），不凭记忆拼接；请求统一携带 polite `User-Agent`+`mailto`；每个候选覆盖基础检索/查询 + 边界输入 + 限流线索三类；止损判定随探测同步完成。字段结构摘要一律以**真实响应 JSON 实际键名**为准。
- **探测样本**：关键词统一 `machine learning`；DOI 查询样本 `10.1016/j.physletb.2012.08.020`（Higgs，真实已发表）；ChEMBL 已收录样本 `10.1021/jm401507s`（J. Med. Chem. → CHEMBL3120156，101 数据点）、未收录样本用上述物理论文。

- **批次一（步骤 29）Semantic Scholar / OpenAlex / Crossref**：
  - **Semantic Scholar**：关键词检索 `graph/v1/paper/search` **连续 4 次均 429**（无 `Retry-After` 头，响应体明示"apply for a key for higher rate limits"）；单篇 by-DOI `graph/v1/paper/DOI:{doi}` **200**（返回 `paperId/externalIds/title/citationCount`）。结论：**API 本身可用，但无 key 情况下核心的关键词检索被共享池限流锁死，可用体验实质需要用户自行申请免费 key** → 止损第 2 类（价值存疑，交用户）。
  - **OpenAlex**：`api.openalex.org/works` 关键词检索 **200**、by-DOI **200**、坏 DOI **404**（干净）。字段极丰富（`id/doi/title/authorships/cited_by_count/abstract_inverted_index/primary_location/open_access/...`）。限流头 `X-RateLimit-Limit:1000`（polite pool，带 mailto），无需 key。→ 止损第 3 类（可行且价值明确）。
  - **Crossref**：`api.crossref.org/works` 关键词检索 **200**、by-DOI **200**、坏 DOI **404**（`Resource not found.`）。字段丰富（`DOI/title/author/abstract/is-referenced-by-count/container-title/URL/...`）。限流头 `x-rate-limit-limit:3/1s`（search）、`10/1s`（by-DOI），无需 key。→ 止损第 3 类。

- **批次二（步骤 30）PMC / Europe PMC / DOAJ / CORE**：
  - **PMC**：走 NCBI E-utilities `esearch.fcgi?db=pmc` + `esummary.fcgi?db=pmc`，**均 200**（限流头 `X-Ratelimit-Limit:3`）。esummary 字段 `uid/pubdate/authors/title/articleids/fulljournalname/...`。**关键重叠证据**：本项目现有 `pubmed_paper_search_by_query` 经 `paperscraper`→`pymed_paperscraper` 调用的正是**同一套 NCBI E-utilities**，仅 `db` 参数不同（现有工具 `db=pubmed` 引文库；PMC 为 `db=pmc` 开放获取全文子集）。→ 止损第 2 类（与现有 PubMed 同源、内容高度重叠，增量价值需用户判断）。
  - **Europe PMC**：`ebi.ac.uk/europepmc/webservices/rest/search` **200**，维护方为 **EBI（非 NCBI）**，单次调用即返回，字段独有 `citedByCount/inEPMC/inPMC/hasPDF/pmcid/nextCursorMark/...`（含引用计数、全文可得性标记、游标翻页），与 PMC/PubMed 端点与字段均不同。→ 止损第 3 类（独立聚合源、字段更丰富，价值明确；与 PubMed 的内容重叠作为信息提示留给用户知悉）。
  - **DOAJ**：`doaj.org/api/search/articles/{q}` **200**，无 key。`bibjson` 含 `title/author/abstract/keywords/link/identifier/journal/subject`。key 仅用于提升限额。→ 止损第 3 类。
  - **CORE**：`api.core.ac.uk/v3/search/works` 无 key **200**，字段极丰富（`title/authors/abstract/doi/citationCount/fullText/downloadUrl/arxivId/pubmedId/...`）。**但无 key 限流极严**：突发测试 5 次后第 6 次即 **429**，且 `x-ratelimit-retry-after` 由 14:14 跳至 **14:24（锁定 10 分钟）**。→ 止损第 2 类（技术可行、字段丰富，但无 key 限流严重到无法正常使用，完整体验需用户自行申请免费 key，交用户）。

- **批次三（步骤 31）Zenodo / HAL / dblp / OpenAIRE**：
  - **Zenodo**：`zenodo.org/api/records?type=publication` **200**，无 key，字段 `doi/metadata/title/files/stats/...`，限流头 `x-ratelimit-limit:30`。注：Zenodo 为通用仓库（含数据集/软件/论文），需靠 `type=publication` 过滤论文类资源。→ 止损第 3 类（可行；混合资源类型的过滤特性作为实现提示留存）。
  - **HAL**：`api.archives-ouvertes.fr/search/`（Solr）**200**，无 key，`fl` 指定字段全部按需返回（`docid/title_s/abstract_s/authFullName_s/doiId_s/uri_s/...`），英文关键词有召回。偏法语/欧洲文献但可用。→ 止损第 3 类（可行；覆盖面偏区域性作为信息提示留存）。
  - **dblp**：`dblp.org/search/publ/api` —— **本探测环境网络受限，无法核实**。Python `requests` 报 `SSL: UNEXPECTED_EOF_WHILE_READING`，`curl` 报 `schannel: failed to receive handshake`（exit 35, http 000），**两套独立 TLS 栈对 `dblp.org` 均在握手阶段失败**，而同批次其他境外主机（zenodo.org/ebi.ac.uk/api.openaire.eu）全部正常——判定为**该主机在本探测环境遭网络层拦截**，非服务下线、非权限、非代码问题。真实字段结构无法采集。→ **交用户判断**（详见步骤 33 分类说明：因根因是探测环境网络而非服务本身，不按"服务不可用"直接静默排除）。
  - **OpenAIRE**：`api.openaire.eu/search/researchProducts` **连续 5 次独立请求全部 200**（`application/json`，无一次 403），**参考项目代码中描述的 403 不稳定问题在本环境未复现、未触发任何重试**。响应为深层嵌套结构 `response.results.result[].metadata.oaf:entity.oaf:result`（`title/creator/pid/subject/bestaccessright/publisher/...`）。→ 止损第 3 类（本环境稳定可用，判为技术可行）。**按步骤 31 要求如实附两点信息供用户知悉，不因此改判：① 参考项目历史记载的经常性 403 在本次未复现；② 响应嵌套很深、归一化实现成本高于其他候选**——两者均为信息透明，非价值存疑判定。

- **批次四（步骤 32）bioRxiv/medRxiv（浏览语义）+ ChEMBL（DOI 查询语义）**：
  - **bioRxiv/medRxiv**：`api.biorxiv.org/details/{server}/{start}/{end}/{cursor}`，`server=biorxiv` 与 `server=medrxiv` **均 200**。**语义确认为"按时间窗口+分类浏览"，非关键词检索**：`messages[0]` 返回 `total/count/cursor/interval/category`，单页固定 30 条（`cursor` 翻页）；`collection[]` 字段 `title/authors/doi/date/version/type/category/abstract/jatsxml/published/server`。边界 `cursor=99999`（超范围）返回 200（`collection` 空）。→ 止损第 3 类（可行；实现与文档措辞须如实标注"浏览"而非"搜索"）。
  - **ChEMBL**：`www.ebi.ac.uk/chembl/api/data/document.json?doi={doi}`。**已收录**样本 `10.1021/jm401507s`：**200**，`page_meta.total_count=1`，`documents[0]` 字段 `document_chembl_id(=CHEMBL3120156)/doi/title/authors/abstract/journal/pubmed_id/year/...`；再查 `activity.json?document_chembl_id=CHEMBL3120156` **200**，`activities[0]` 含真实 SAR/生物活性字段 `standard_type(如 IC50)/standard_value/standard_units/pchembl_value/canonical_smiles/target_pref_name/molecule_chembl_id/assay_description/...`。**未收录**样本（物理论文 DOI）：**200**，`total_count=0`，`documents` 空——"未收录"响应干净可辨。边界空 `doi=`：200（返回全量文档分页，说明实现须客户端强制校验 `doi` 非空）。→ 止损第 3 类（可行；已收录/未收录两路径真实响应均已采集，DOI 必填查询语义确认）。

### 步骤 33：探测结果汇总 + 范围二次确认（检查点）—— 完成于 2026-08-04 22:21

#### 13 个候选真实探测汇总表

| # | 候选 | 真实端点 | 探测 HTTP 摘要 | 真实字段结构摘要（实际键名） | 限流/稳定性 | 止损分类 |
|---|------|----------|----------------|------------------------------|-------------|----------|
| 1 | Semantic Scholar | `api.semanticscholar.org/graph/v1/paper/search`、`/paper/DOI:{doi}` | 检索 **429×4**（无 Retry-After，提示 apply for key）；by-DOI **200** | by-DOI: `paperId/externalIds/title/citationCount` | 无 key 关键词检索被共享池限流锁死 | **② 价值存疑（交用户）** |
| 2 | OpenAlex | `api.openalex.org/works` | 检索 200 / by-DOI 200 / 坏DOI 404 | `id/doi/title/authorships/cited_by_count/abstract_inverted_index/open_access/primary_location` | 无 key，polite pool 1000/日 | ③ 可行·落地 |
| 3 | Crossref | `api.crossref.org/works` | 检索 200 / by-DOI 200 / 坏DOI 404 | `DOI/title/author/abstract/is-referenced-by-count/container-title/URL` | 无 key，3/s(搜)·10/s(DOI) | ③ 可行·落地 |
| 4 | PMC | NCBI E-utilities `esearch/esummary?db=pmc` | 均 200 | `uid/pubdate/authors/title/articleids/fulljournalname` | NCBI 3/s | **② 价值存疑（与现有 PubMed 同源 NCBI、内容重叠，交用户）** |
| 5 | Europe PMC | `ebi.ac.uk/europepmc/webservices/rest/search` | 200 | `id/source/pmcid/title/citedByCount/inEPMC/hasPDF/nextCursorMark/firstPublicationDate` | 无 key，单次调用即返回 | ③ 可行·落地（与 PubMed 内容重叠仅作信息提示） |
| 6 | DOAJ | `doaj.org/api/search/articles/{q}` | 200 | `bibjson.{title/author/abstract/keywords/link/identifier/journal/subject}` | 无 key（key 提额） | ③ 可行·落地 |
| 7 | CORE | `api.core.ac.uk/v3/search/works` | 无 key 200，突发第 6 次 429 | `title/authors/abstract/doi/citationCount/fullText/downloadUrl/arxivId/pubmedId` | **无 key 限流极严：约 5 次即锁 10 分钟** | **② 价值存疑（需自行申请免费 key，交用户）** |
| 8 | Zenodo | `zenodo.org/api/records?type=publication` | 200 | `doi/conceptdoi/metadata/title/files/stats/links` | 无 key，30/分 | ③ 可行·落地（通用仓库需 type 过滤论文） |
| 9 | HAL | `api.archives-ouvertes.fr/search/`(Solr) | 200 | `docid/title_s/abstract_s/authFullName_s/doiId_s/uri_s/docType_s` | 无 key | ③ 可行·落地（偏欧洲文献覆盖） |
| 10 | dblp | `dblp.org/search/publ/api` | **本环境网络受限：SSL 握手失败（requests+curl 双栈一致），http 000，无法核实** | 无法采集 | 主机级网络拦截（非服务下线/权限） | **交用户（无法核实，环境网络所致，未静默排除）** |
| 11 | OpenAIRE | `api.openaire.eu/search/researchProducts` | **200×5 连续，无 403、无重试** | `response.results.result[].metadata.oaf:entity.oaf:result.{title/creator/pid/subject/bestaccessright/publisher}` | 本环境稳定；历史 403 未复现 | ③ 可行·落地（附注：嵌套深·归一化成本高） |
| 12 | bioRxiv/medRxiv | `api.biorxiv.org/details/{server}/{start}/{end}/{cursor}` | biorxiv/medrxiv 均 200，超范围 cursor 200(空) | `messages[].{total/count/cursor}`、`collection[].{title/authors/doi/date/version/category/abstract/server}` | 公开无 key | ③ 可行·落地（**浏览语义**，非关键词检索） |
| 13 | ChEMBL | `ebi.ac.uk/chembl/api/data/document.json?doi=`、`activity.json?document_chembl_id=` | 已收录 200(total=1)+activity 200；未收录 200(total=0) | doc: `document_chembl_id/doi/title/authors/abstract/journal/pubmed_id/year`；activity: `standard_type(IC50)/standard_value/standard_units/pchembl_value/canonical_smiles/target_pref_name/molecule_chembl_id` | 公开无 key | ③ 可行·落地（**DOI 必填查询语义**；空 doi 需客户端校验） |

#### 止损分类结论（严格遵循 goal.md QA-R010/QA-R011 + 用户本轮直接指令）

- **① 技术确认不可行、直接排除（无需用户确认）**：**无**。全部 13 个候选在真实探测中，除 dblp（环境网络）外均返回 200 可解析数据，无一属于"需付费 key / 服务下线 / 限流严到完全不可用"的干净排除项。
- **② 技术可行但价值存疑、交还用户最终判断（原样保留，未自行剔除）**：
  1. **Semantic Scholar** —— 无 key 关键词检索被共享池 429 锁死（4/4 失败），可用体验实质需用户自行申请免费 key；by-DOI 路径可用。
  2. **PMC** —— 与本项目现有 `pubmed_paper_search_by_query` 走同一套 NCBI E-utilities（仅 `db=pmc` vs `db=pubmed`），内容高度重叠，增量价值需用户定夺。
  3. **CORE** —— 字段最丰富，但无 key 限流极严（约 5 次请求即锁 10 分钟），完整体验需用户自行申请免费 key。
- **附加·无法核实、亦交用户判断**：**dblp** —— 探测环境对 `dblp.org` 网络层拦截（双 TLS 栈握手失败），无法采集真实字段结构。按 project-plan 步骤 28 默认规则"网络受限→技术不可行"本可直接排除，但根因是**本探测环境**网络而非服务/权限/代码问题，MCP Server 实际运行在**终端用户机器**上、其网络环境可能可达 dblp.org，故不静默排除，一并交用户判断。
- **③ 技术可行且价值明确、确认落地候选（9 个）**：OpenAlex、Crossref、Europe PMC、DOAJ、Zenodo、HAL、OpenAIRE、bioRxiv/medRxiv、ChEMBL。

#### 决策留痕说明（关于 goal.md）
- project-plan 步骤 33.4 建议将"价值存疑"清单同步追加进 `project-docs/goal.md`（比照 QA-R002 新增一轮 QA）。**但 `project-builder-cn` 的文档写入边界规定：在 `project-docs/` 内仅允许修改 `buildlog.md`，禁止修改 `goal.md`**；且 `goal.md` 当前存在用户未提交的本地改动。因此本步骤**不**改写 goal.md，改由本 buildlog 完整留痕，并在交付汇报中把"价值存疑（SS/PMC/CORE）+ 无法核实（dblp）"清单明确交还用户；goal.md 的新一轮 QA 追加应由用户经 `project-creator-cn`/`project-planner-cn` 完成。

### 下一步计划
- ⏸️ **等待用户对以下 4 项做去留判断**（不可由构建方代决）：② Semantic Scholar、PMC、CORE（技术可行但价值存疑）；＋ dblp（本环境无法核实，需用户依其部署网络决定）。
- ✅ 已确认落地的 9 个数据源（OpenAlex/Crossref/Europe PMC/DOAJ/Zenodo/HAL/OpenAIRE/bioRxiv·medRxiv/ChEMBL）等最终清单确定后，由 `project-planner-cn` 在计划书中追加步骤 34+（各源参数签名、归一化字段、代码骨架、验证方法、风险提示）。本轮探测阶段**未**编写任何新数据源实现代码，符合步骤 33"检查点前不落地实现"的约束。
- ⏭️ README/pyproject 版本号按计划书策略在全部落地数据源实现完毕后统一更新，本轮不动。

---

## 附加工具：dblp 网络连通性诊断脚本（非构建步骤）—— 完成于 2026-08-05 14:47

> 本条目记录一个独立于 v3.0.0 数据源开发主线的诊断类小工具，不属于 project-plan.md 排定的构建步骤，未改动 project-plan.md。

### 背景与关联
- goal.md 的 **QA-R012** 将候选数据源 **dblp** 记为「待定」：此前探测阶段（步骤 28-33，commit 008d509）在探测环境下对 `dblp.org` 的 TLS 握手失败（requests+curl 双栈一致，HTTP 状态码 000），**无法核实 dblp.org 真实是否可用**。
- 根因不是 API Key（dblp 公开 API 不要求 key），疑为主机级网络拦截；而 MCP Server 实际运行在终端用户机器上，其网络环境可能与探测环境不同，故未静默排除，交由用户在其它网络环境实测后再定案（预计补 QA-R013）。
- 用户据此明确要求：编写一个简单的 dblp 连通性测试脚本，供其在不同网络环境下手动运行判断连通性。

### 执行的任务
- 新建分层诊断脚本 `_verify/dblp_connectivity_test.py`，将「能否访问 dblp.org」拆成 4 层逐步探测：**DNS 解析 → TCP 连接 → TLS 握手 → HTTP 实际请求**（真实调用 `https://dblp.org/search/publ/api?q=graph&format=json&h=1`）。任一层失败即停止并给出该层最可能的原因（DNS 污染 / 防火墙拦截 / TLS 中间人拦截 / 应用层限流等），末尾打印一段面向非技术用户的「诊断结论」。
- 脚本无需 API Key、只读探测、不改任何文件；启动时强制 `sys.stdout` UTF-8，避免 Windows GBK 控制台下中文乱码。
- 本机实跑验证通过：脚本按预期逐层输出，并在本探测环境复现了 QA-R012 记录的现象（DNS 成功、TCP 成功、TLS 握手失败 `UNEXPECTED_EOF_WHILE_READING`），结论逻辑正确。

### 关键变更
- 新增 `_verify/dblp_connectivity_test.py`：dblp 连通性分层诊断工具（面向用户手动运行）。

### 遇到的问题及解决方案
- **`_verify/` 被 gitignore**：用户本地有一处**未提交**的 `.gitignore` 改动新增了 `_verify` 忽略规则。本脚本按用户明确要求需提交入库并长期保留（区别于一次性验证脚本），故对该脚本单独使用 `git add -f` 强制纳入版本控制；**未触碰用户未提交的 `.gitignore` 改动**，保持其暂存/未提交原状。
- 首次运行 Windows 控制台中文乱码（GBK）：在脚本启动处 `sys.stdout/stderr.reconfigure(encoding="utf-8")` 解决，重跑后中文正常显示。

### 下一步计划
- ⏭️ 等待用户在其部署/使用网络下运行本脚本，回报连通性结果，用于确定 dblp 的最终去留（预计对应 goal.md 的 QA-R013）。dblp 数据源本身在 v3.0.0 仍为「待定」，本条目不改变该状态。

---

## 附加工具增强：dblp 诊断脚本加脱敏 + 内联 curl 诊断（非构建步骤）—— 完成于 2026-08-05 20:45

> 本条是对上一条 dblp 诊断脚本（commit 9948687）的小幅增强，非新构建步骤，未改动 project-plan.md。

### 背景
- 用户要把脚本完整输出复制给对话助手做诊断，但不想把本机 DNS 解析出的真实 IPv4 明文外泄。
- 用户在 HTTP 这层曾拿到一次 HTTP 500，而原 `step_http()` 只打印状态码、吞掉了 dblp 服务端返回的错误响应体，看不出 500 具体原因；此前只能建议用户额外手动跑 `curl -v`（既暴露 IP 又要多操作）。

### 执行的任务
- **输出自动脱敏**：新增模块级 IPv4 正则 `_IPV4_RE` + `_mask_ipv4()` + `_print()` 包装函数，脚本内所有原 `print(...)` 统一改为 `_print(...)`；打印前把 IPv4 后两段打码（如 `192.76.146.204` → `192.76.xxx.xxx`），保留前两段供判断大致网段。以后新增打印语句自动脱敏，无需逐行手改。`_print()` 内部通过 `builtins.print` 输出，避免自引用递归。
- **内联 curl 诊断**：改造 `step_http()`，在捕获 `urllib.error.HTTPError` 时用 `e.read(500)` 读出并打印服务端错误响应体前 500 字节（读失败有兜底提示），一次跑出完整诊断信息，去掉用户手动跑 curl 的必要。响应体仍走 `_print`，若偶含 IP 也会被自动打码。

### 关键变更
- 修改 `_verify/dblp_connectivity_test.py`：新增 `re`/`builtins` 导入、IPv4 脱敏机制、`step_http()` 打印 HTTPError 响应体。

### 遇到的问题及解决方案
- 全局把 `print(` 批量替换为 `_print(` 会把包装函数体内的输出调用也改成自引用（无限递归）；解决：包装函数体内改用 `builtins.print` 显式调用真实内置 print。

### 验证结果
- 本机实跑脚本：DNS 解析出的 IP 打印为 `192.76.xxx.xxx`（脱敏生效）；本环境 TLS 握手仍失败，HTTP 步骤未触发。
- 用注入式测试单独验证 `step_http()` 的 HTTPError 分支：模拟 dblp 返回 HTTP 500，脚本正确打印出「服务器错误响应体（前 500 字节）：…」完整报错内容；`_mask_ipv4()` 对多 IP、带端口字符串均正确打码且保留端口。

### 下一步计划
- ⏭️ 同上一条：等待用户在其网络下运行增强后的脚本，回报连通性/HTTP 诊断结果，用于确定 dblp 去留。dblp 在 v3.0.0 仍为「待定」，本条目不改变该状态。

---

## v3.0.0 分批实现阶段（步骤 34~42，对应 project-plan.md，QA-R012/QA-R013）

> 本阶段落地步骤 33 后用户裁决确认的 12 个数据源真实实现。组织：步骤 34 公共规范总纲 → 步骤 35~39 分批实现 → 步骤 40 统一注册 → 步骤 41 README/版本号收尾 → 步骤 42 buildlog + 整体回归。**编码前已用一次性探测脚本（scratchpad，未提交）复核了计划书要求的待确认字段结构**（Europe PMC 的 `doi`/`authorString`、HAL 的 `title_s`/`abstract_s`/`authFullName_s` 均为数组、OpenAIRE 的 `pid` 按 `@classid=="doi"` 筛选、CORE key 真实有效性），一切归一化以真实抓包键名为准。

### 步骤 34：分批实现总纲——公共规范 + 条件注册架构决策 + 注册组织 —— 完成于 2026-08-05 21:50

- **公共代码规范（34.1）**：12 个数据源每个独立文件 `src/uniarticles/sources/<name>.py`，暴露 `register(server)`；各文件自带本地 `_ok/_err`（`source` 填自身标识，**不复用** `scopus.py` 硬编码 `source="scopus"` 的版本）；HTTP 统一 `httpx.AsyncClient(timeout=30.0)` + `raise_for_status()`；异常在 `@server.tool()` 体内 `try/except Exception → _err`；字符串参数 `.strip()`、必填判空直接 `_err`、`max_results` clamp `[1,25]`；统一 polite User-Agent `"UniArticlesMCP/3.0.0 (https://github.com/thinktraveller/UniArticles_MCPserver)"`；无新增第三方依赖。
- **条件注册决策（34.2，落地 QA-R012 开放问题）**：**不对称处理**——Semantic Scholar 采用「无 key 不注册」（`register()` 内若 `settings.semantic_scholar_api_key` 为空则提前 `return`，模块级、含 by-DOI 一并隐藏，贴合用户原话字面），CORE **不**采用（沿用现有 Elsevier 式无条件注册+运行时限流透明）。判断标准：无 key 时核心功能是否**确定性失败**——SS 关键词检索无 key 时 4/4 次 429（确定性失败），CORE 无 key 仍可有限使用（约 5 次后锁 10 分钟）。
- **Settings 新增字段（34.3）**：`config.py` 新增 `semantic_scholar_api_key`（`SEMANTIC_SCHOLAR_API_KEY`）、`core_api_key`（`CORE_API_KEY`），均 `field(default_factory=lambda: os.getenv(...))`，可选、无兼容回退。`.env.example` 新增两行含注释。
- **注册组织（34.4）**：`register_all_sources()` 采「v2.x 既有 / v3.0.0 通用检索型 / v3.0.0 语义特殊型」三段分组，具体在步骤 40 落地。
- **涉及文件**：`src/uniarticles/config.py`（新增 2 字段）、`.env.example`（新增 2 行）。
- **验证**：`from uniarticles.config import settings` → `semantic_scholar_api_key=None`（当前环境未配置，正是条件注册的天然测试场景）、`core_api_key` 已加载（len 32）、`elsevier_api_key` 经旧名兼容层仍可读；`Settings`（`frozen=True`）新增字段后实例化无异常。

---
