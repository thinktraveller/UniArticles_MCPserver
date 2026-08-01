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

### 下一步计划

- 本次任务范围仅为 `project-plan.md` 的**第一步（收尾整理）**，即上述"步骤 1（buildlog 迁移）+ 步骤 2（环境变量改名）"，现已完成。
- 尚未执行：`project-plan.md` 步骤 3（遗留 view 风险处置）、步骤 4/5（新增 `get_serial_title`、`get_article_objects` 工具）、步骤 6（文档与 `pyproject.toml` 版本号升级）、步骤 7（整体验证）。这些属于下一阶段任务，需另行启动。
- **前置阻塞**：进入步骤 3～7 前，需先修复 `.venv` 中损坏的 `annotated_types`/`pydantic`（否则无法启动 MCP Server 或做真实 API 验证）。

---
