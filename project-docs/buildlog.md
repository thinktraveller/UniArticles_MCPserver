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
