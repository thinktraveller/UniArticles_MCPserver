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

### v3.0.0 范围补充（QA-R010～QA-R011，2026-08-04）

源自用户调研本地参考项目 `reference-projects/paper-search-mcp-main/`、`reference-projects/research-superpower-main/`，`project-creator-cn` 逐一核实两个项目源码后，在 `project-docs/goal.md` QA-R010（候选发现+分档评估）与 QA-R011（范围收敛）两轮问答中，用户明确选择"全部纳入"这一最大范围选项。**v3.0.0 是本项目至今规模最大的一轮版本**，合计新增 13 个数据源/功能点：

1. **11 个通用检索型新数据源**（Semantic Scholar、OpenAlex、Crossref、PMC、Europe PMC、DOAJ、CORE、Zenodo、HAL、dblp、OpenAIRE），每个数据源在 `src/uniarticles/sources/` 下建立独立脚本文件，遵循现有"一数据源一文件、暴露 `register(server)`"模式。**用户在 QA-R011 明确要求"对每一个源都进行真实性探测"**——此前 QA-R010 的调研只核实了本地参考项目 `paper-search-mcp-main` 的 README 描述与 Python 代码逻辑，未对本项目环境做过任何真实 HTTP 请求验证，因此 11 个候选无论此前被评估为"推荐重点"（Semantic Scholar/OpenAlex/Crossref）还是"中等价值"（PMC/Europe PMC/DOAJ/CORE/Zenodo/HAL/dblp/OpenAIRE），均需以同等地位重新走一遍真实探测，不分先后主次。
2. **2 个语义特殊的新数据源**：bioRxiv/medRxiv（官方 API 本质是"按分类+时间窗口浏览"，非关键词全文检索）、ChEMBL（DOI 输入型的文献关联数据查询，非关键词检索）。
3. **1 个现有工具增强**：arXiv 三个现有工具（`arxiv_paper_search_by_query`/`arxiv_latest_paper_list_by_category`/`arxiv_paper_detail_by_id`）补充 `doi` 输出字段——独立、低风险、不依赖新数据源探测进度，本计划书将其列为可优先交付的第一步（步骤 27）。

**本计划书采用的分阶段组织方案（回应 `goal.md` 备注"强烈建议不要沿用一次性列完所有步骤"的提醒，不把 13 个候选塞进一份线性步骤列表）**：

- **第一阶段（步骤 27）——低风险独立交付**：arXiv 补 `doi` 字段，不依赖任何探测结果，可立即开发验证，不受后续阶段进度影响。
- **第二阶段（步骤 28～32）——真实探测**：对 11 个通用数据源 + bioRxiv/medRxiv + ChEMBL 共 13 个候选做真实 API 可行性验证，按候选置信度/类型分 4 个探测批次执行（统一方法论见步骤 28，批次划分见步骤 29～32），每个候选逐一记录真实 HTTP 状态码、真实字段结构、限流/稳定性表现，不凭参考项目代码逻辑或官方文档字面描述直接假设可用。
- **第三阶段（步骤 33）——探测结果汇总 + 范围二次确认（检查点）**：整理全部 13 个候选的探测结论，按下方"止损处理规则"完成分类，产出"确认排除"清单（无需用户二次确认）与"技术可行但价值存疑，交用户判断"清单（若存在），这是本轮范围从"13 个候选"收敛为"最终实现清单"的关键节点。
- **第四阶段——分批实现（步骤 34～42，已于 2026-08-05 补充，见下方"v3.0.0 分批实现阶段补充"小节）**：步骤 33 完成后，交还用户裁决的 4 项候选（Semantic Scholar/PMC/CORE/dblp）已在 `goal.md` QA-R012/QA-R013 中逐项定案（3 纳入 1 排除），v3.0.0 最终确认落地 12 个数据源。本计划书据此追加步骤 34～42，覆盖全部 12 个数据源的具体实现（含代码骨架、真实字段归一化、验证方法、风险提示）、`register_all_sources()` 接入、README/版本号收尾与整体回归验证。

**探测结果对范围的止损处理规则（`goal.md` 约束条件已定，步骤 28～33 执行时必须遵守，不得自行加码或减码）**：
1. **技术上确认不可行**（端点已下线、强制要求付费商业 key、无 key 时限流严重到实际不可用、返回结构与文档描述不符导致无法可靠解析）→ 直接排除出 v3.0.0，不需要单独找用户二次确认，比照 `goal.md` QA-R002 先例，在探测结果表格中如实记录排除原因即可。
2. **技术上可行但价值存疑**（字段稀疏、需自行申请免费 key 才能获得可用体验、限流严格影响体验、与现有数据源高度重叠等）→ **不得由 `project-planner-cn`/`project-builder-cn` 自行拍板剔除**，必须整理成清晰的探测结果汇总，在步骤 33 交还用户做最终去留判断。
3. 该规则同样适用于 bioRxiv/medRxiv、ChEMBL 两个语义特殊候选，不因其"已确认纳入范围"就免于真实探测或免于止损判断。

**ChEMBL 与 bioRxiv/medRxiv 的实现设计差异（现在预先明确，避免后续实现阶段与其余 9 个通用检索源的设计模式混淆）**：
- **ChEMBL**：参数签名必须是 `doi` 必填（如 `chembl_lookup_by_doi(doi: str)`），语义为"给定一篇已知 DOI 的论文，查询其是否被 ChEMBL 收录及其结构化 SAR/生物活性数据（IC50/MIC/Ki 等）"，**不得**设计成 `query`+`max_results` 关键词检索模式。已知探测起点（来自 `goal.md` QA-R010 B 部分对 `research-superpower-main` 的核实）：`www.ebi.ac.uk/chembl/api/data/document.json?doi={doi}`；真实探测仍需在步骤 32 执行，不因文档已记录端点路径就跳过真实验证。
- **bioRxiv/medRxiv**：参数签名应体现"分类+时间窗口浏览"语义（如 `server`/`category`/`start_date`/`end_date`/`cursor`），**不得**提供 `query` 关键词参数误导用户以为支持全文检索，工具描述（docstring）必须显式声明这一局限，与已有的 `arxiv_latest_paper_list_by_category`（真正的关键词/分类检索）区分清楚。已知探测起点（来自 `goal.md` QA-R010 A 表格对 `paper-search-mcp-main` 的核实）：`api.biorxiv.org/details/{server}/{start}/{end}/{cursor}`，`server` 取值 `biorxiv`/`medrxiv`。

**收尾文档（README.md/README_ZH.md、`pyproject.toml` 版本号、`project-docs/buildlog.md`）的更新策略（`goal.md` 未指定，本计划书给出方案并说明理由）**：
- **`project-docs/buildlog.md`：跟随每个阶段/批次增量更新**，不等 13 个候选全部处理完才一次性补记。理由：`buildlog.md` 是内部构建日志，其价值在于"断点续建时能看到已完成到哪一步"——v3.0.0 战线长、大概率跨多个会话执行，若集中到最后才写，一旦中途中断（例如步骤 33 交还用户判断后用户迟迟未决策），此前已完成的探测/实现工作将没有任何落盘记录，不符合本项目一贯"buildlog 记录构建过程"的定位。步骤 28～33 每步完成后均需追加 buildlog 条目，后续实现阶段每批完成后同样追加。
- **README.md/README_ZH.md 与 `pyproject.toml` 版本号：不跟随每批次更新，只在 v3.0.0 全部已确认数据源均实现完毕后统一更新一次**。理由：(1) README 的工具清单/计数需要保持"文档与代码实际注册工具一一对应"（`goal.md` 历次版本的一贯要求），若每批次更新一次，中间状态的 README 会出现"这一批做完了，但还有候选没测完/没做"的模糊表述，不如等最终范围确定后一次性准确描述；(2) `pyproject.toml` 版本号对外代表一次完整发布，v3.0.0 若分批发布多个中间版本号，超出本项目历来"一次范围澄清对应一个版本号、无预发布版本"的版本管理方式，不建议引入新的复杂度；(3) 待最终实现数据源清单确定后，`pyproject.toml` 版本号提升与 README 更新将作为本轮分批实现阶段完成后的最后一个正式步骤统一执行（届时由 `project-planner-cn` 追加为具体步骤）。

**`register_all_sources()` 组织方式提示（`goal.md` 约束条件已声明非强制，仅供后续实现阶段参考）**：新数据源数量达两位数后，`src/uniarticles/sources/__init__.py` 的 `register_all_sources()` 调用列表会明显变长（当前仅 4 行，见下方代码），建议在后续实现阶段按"通用检索型 / 语义特殊型 / 已有数据源（v2.x）"分组加注释组织调用顺序，但不强制要求某种具体排序规则，具体方案留待实现阶段落地时视实际情况决定：
```python
# 当前（v2.3.0）：
def register_all_sources(server: FastMCP) -> None:
    register_scopus_source(server)
    register_sciencedirect_source(server)
    register_arxiv_source(server)
    register_paperscraper_source(server)
```

对应开发计划见下方"步骤 27～42"（步骤 34～42 为本次续写的第四阶段"分批实现"，详见下方"v3.0.0 分批实现阶段补充"小节）。步骤 1～26（v2.0/v2.1.0/v2.2.0/v2.3.0 构建）已全部执行完毕并发布，保留在文档中作为历史记录，不受本轮改动影响。

### v3.0.0 分批实现阶段补充（QA-R012/QA-R013，2026-08-05）

步骤 33（探测结果汇总检查点）完成后，4 项"技术可行但价值存疑/无法核实"的候选（Semantic Scholar、PMC、CORE、dblp）已交还用户裁决。用户在 `goal.md` QA-R012/QA-R013 中逐项定案：**Semantic Scholar 纳入**（key 申请中，且提出"无 key 不注册工具"的条件注册新架构需求）、**PMC 排除**（与现有 `pubmed_paper_search_by_query` 同源 NCBI E-utilities，无稳定性增量）、**CORE 纳入**（key 已配置在 `.env` 的 `CORE_API_KEY`）、**dblp 纳入**（用户三轮不同网络环境实测后确认服务端本身可用，但记录一条已知风险——可能因网络环境波动间歇性失败）。至此 v3.0.0 最终确认落地 **12 个数据源**：OpenAlex、Crossref、Europe PMC、DOAJ、Zenodo、HAL、OpenAIRE、bioRxiv/medRxiv、ChEMBL（以上 9 个已在步骤 28～33 真实探测确认可行）+ Semantic Scholar、CORE、dblp（本轮由用户裁决补充确认）；PMC 排除，不纳入实现范围。

本次续写的步骤 34～42 覆盖这 12 个数据源的具体实现，组织原则：

1. **总纲先行（步骤 34）**：统一约定本批次的公共代码规范，并正式落地两项此前留给 `project-planner-cn` 自行判断的开放性决策——(a) `goal.md` QA-R012 提出的"按 key 条件注册"架构的适用范围（Semantic Scholar 采用、CORE 不采用，附完整理由）；(b) `register_all_sources()` 的分组组织方式。同时明确 `goal.md` QA-R013 新增的通用流程约束（探测失败必须把验证脚本产出到 `_verify/` 供用户独立验证）在本轮如何落地。
2. **按实现特征分批（步骤 35～39）**：不再沿用探测阶段"推荐重点/中等价值"的分档（那是探测优先级维度，探测阶段已完成使命），改按**实现复杂度与代码结构共性**重新分批——批次一（步骤 35）是 4 个字段结构清晰、无 key 要求的标准检索源（OpenAlex/Crossref/Europe PMC/DOAJ）；批次二（步骤 36）是 3 个需要额外结构处理的检索源（Zenodo 的资源类型过滤、HAL 的 Solr 字段选择、OpenAIRE 的深层嵌套响应）；批次三（步骤 37）是 2 个需要"按 key 条件注册"新架构的源（Semantic Scholar/CORE，架构设计集中在同一步骤便于对照验证）；批次四（步骤 38）是 2 个语义特殊源（bioRxiv/medRxiv 浏览语义、ChEMBL DOI 查询语义），延续与其余 10 个通用检索源不同的参数模式约束；dblp（步骤 39）单列，因其"探测环境网络受限、真实字段结构尚未完整采集"+"已知间歇性网络失败风险"两个特殊性质，需要独立的编码前置探测与错误提示文案设计，不适合与其他任何批次合并处理。
3. **收尾（步骤 40～42）**：`register_all_sources()` 统一接入全部 12 个新数据源（步骤 40）→ README/`pyproject.toml` 版本号统一更新至 `3.0.0`（步骤 41，延续本计划书此前确定的"全部落地后统一更新"策略）→ `buildlog.md` 记录 + 整体回归验证检查点（步骤 42，v3.0.0 最终交付节点）。

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

### 步骤 27：arXiv 三工具补充 `doi` 输出字段（独立、低风险、优先交付）

#### 目标说明
`project-docs/goal.md` 核心目标 19 / QA-R010 问题 5 已确认：为现有 `arxiv_paper_search_by_query`/`arxiv_latest_paper_list_by_category`/`arxiv_paper_detail_by_id` 三个工具的输出补充 `doi` 字段，复用第三方 `arxiv` 库 `Result` 对象自带的 `.doi` 属性，零额外请求成本。这是对现有工具的小幅增强，不依赖任何新数据源的探测/实现进度，可以独立于第二～四阶段先行完成并验证。

核实 `src/uniarticles/sources/arxiv.py` 源码确认：三个公开工具的序列化逻辑全部收敛到同一个私有函数 `_serialize_paper()`（第 53-62 行），`arxiv_paper_search_by_query`/`arxiv_latest_paper_list_by_category` 经 `_run_arxiv_search()` 调用它，`arxiv_paper_detail_by_id` 经 `_get_paper_details()` 调用它——因此只需修改这一处，三个工具的输出会同步获得 `doi` 字段，不需要分别改三处。

#### 具体操作
1. 修改 `src/uniarticles/sources/arxiv.py` 第 53-62 行 `_serialize_paper()`，在 `"pdf_url": paper.pdf_url,` 之后新增一行：
   ```python
   def _serialize_paper(paper) -> dict:
       return {
           "id": paper.get_short_id(),
           "title": paper.title,
           "authors": [author.name for author in paper.authors],
           "abstract": paper.summary,
           "published": paper.published.isoformat(),
           "categories": paper.categories,
           "pdf_url": paper.pdf_url,
           "doi": paper.doi,
       }
   ```
   `arxiv` 库的 `Result.doi` 属性在论文未被分配 DOI 时返回 `None`（这是常态——大量 arXiv 预印本从未在期刊正式发表、从未获得 DOI），`None` 可以直接序列化为 JSON `null`，无需额外判空处理。
2. 检查 `README.md`/`README_ZH.md` 中三个 arXiv 工具的描述是否逐字段列出了输出结构；若有，同步补充 `doi` 字段说明并注明"可能为 `null`（部分预印本未获分配 DOI）"；若只是概述性描述（未逐字段列出），则无需改动。
3. 无需修改三个 `@server.tool()` 函数签名或参数校验逻辑，本步骤只涉及返回体新增一个字段。

#### 验证方法
- 用真实网络环境调用 `arxiv_paper_search_by_query(query="attention is all you need")`，确认返回的 `items[]` 每项均含 `doi` 键；由于该论文较早期，`doi` 大概率为 `null`，属预期行为，不是 bug。
- 额外调用 `arxiv_paper_detail_by_id` 传入一个已知已在期刊发表、大概率被分配了 DOI 的较新论文 ID，确认此时 `doi` 字段能拿到非空的真实 DOI 字符串（用于确认字段确实能在有值时正确透出，而不是只验证了 `null` 这一种情况）。
- 确认三个工具均无 `AttributeError`/未捕获异常。

#### 风险提示
- 不要把 `doi` 为 `None` 误判为实现错误——这是 arXiv 数据本身的真实分布，下游 MCP 客户端/提示词若依赖该字段做进一步查询（如喂给 ChEMBL/Crossref），需自行处理空值分支，这一点建议在 README 补充说明中提醒到。
- 本步骤修改的是全部三个工具共用的私有函数，务必只新增字段、不改动既有键名/取值逻辑，避免误伤三个工具已发布的现有返回结构。

---

### 步骤 28：13 个候选数据源——真实探测方法论总纲与止损规则执行规范

#### 目标说明
为步骤 29～33（覆盖 11 个通用检索型候选 + bioRxiv/medRxiv + ChEMBL 共 13 个候选）统一制定探测方法论、记录规范与止损判定标准，避免在每个探测步骤中重复表述，并确保严格遵循 `goal.md` 约束条件已锁定的"真实验证优先"方法论与止损规则（详见"v3.0.0 范围补充"小节）。本步骤本身不产出任何代码，是后续 5 个探测步骤共同遵守的执行规范。

#### 具体操作
1. **探测脚本纪律**：延续本项目一贯做法——临时探测脚本写入会话 scratchpad 目录，验证完即弃，不提交仓库，不放入 `src/`/`tests/`；脚本只发起 GET 等只读请求，不对任何远端账号/数据产生写副作用。
2. **端点确定顺序**：对每个候选，先查阅本地 `reference-projects/paper-search-mcp-main/academic_platforms/` 下对应的连接器源码（若存在），以其中实际调用的 URL/参数作为真实端点依据；若参考项目未覆盖该候选或本地无法访问，则查阅该数据源官方文档确定端点。**任何情况下都不得跳过这一步直接凭记忆/推测拼接端点 URL 就发起探测**——若确实无法核实到可信端点（网络访问受限或文档缺失），如实记录"端点无法核实"，并按止损规则归入"技术不可行"（结构不明确导致无法可靠验证）。
3. **每个候选至少覆盖以下三类真实请求**：
   - **基础检索/查询路径**：关键词检索类候选用一个通用关键词（建议统一用 `"machine learning"` 或候选官方文档示例中的关键词，保持样本可比性）；DOI 查询类候选（ChEMBL）复用本项目已验证过的真实 DOI 样本或另找合适样本（见步骤 32）。
   - **边界/异常输入路径**：空查询、明显不存在的标识符、非法参数，记录真实错误响应结构（状态码 + 错误体摘要）。
   - **限流/稳定性线索**：记录响应头中的 `X-RateLimit-*`/`Retry-After` 等字段（如有）；若单次探测中观察到 429/403 等限流类响应，需追加 1～2 次复测确认是否稳定复现，而非凭一次响应下结论。
4. **记录格式**：延续 `goal.md` 附录"实测可行性探测"已使用的表格格式（列：候选/探测请求/HTTP 状态/真实字段结构摘要/结论），每个探测批次产出一张表格。字段结构摘要必须以真实响应 JSON 的实际键名为准，**禁止**照抄参考项目变量名/官方文档字面描述的字段名。
5. **止损判定必须随探测同步完成**，不得拖延到步骤 33 才做判断——步骤 33 的职责是"汇总"，不是"重新评估"：
   - 技术上确认不可行 → 直接判定排除，记录具体依据（比照 `goal.md` QA-R002 先例的表述方式，如"401，需商业 key"/"端点已下线，返回 404"/"字段全部为 null，无法可靠解析"）。
   - 技术上可行但价值存疑（字段稀疏/需自行申请 key 才有可用体验/限流严格/与现有数据源高度重叠）→ 判定为"需用户确认"，**不得**自行归入排除或落地任一方。
   - 技术上可行且价值明确 → 判定为"确认落地候选"。

#### 验证方法
- 每个探测批次的产出，必须同时满足：（a）批次内每个候选都有至少一次真实 HTTP 请求记录（含状态码与响应摘要）；（b）每个候选都已给出止损三分类结论之一，不留"未判断"。

#### 风险提示
- 不得因某候选"看起来很像另一个已验证过的候选"就跳过真实探测（例如 Europe PMC 与本项目已有的 PubMed、及候选中的 PMC 三者名称相近但维护方/端点均不同，必须分别真实验证，不能以其中一个的结果代替另外两个）。
- 若探测中遇到网络访问受限（本项目 v2.1.0 已有 `searchScholarPapers` 因网络问题被删除的先例），需如实记录为"网络访问受限"，与"权限不足"（401/403）、"结构不可解析"在止损分类的证据表述上要分开，避免后续误读探测结论。
- 请求建议携带合理的 `User-Agent`/联系邮箱（沿用 OpenAlex/Crossref 官方推荐的 polite pool 惯例），降低被目标服务误判为滥用请求而限流的概率。

---

### 步骤 29：真实探测批次一——Semantic Scholar / OpenAlex / Crossref（3 个推荐重点候选）

#### 目标说明
这 3 个候选是 `goal.md` QA-R010 A 表格中评估为"较优、免费公开、限流可控、且与产品定位相符"的推荐重点候选，均免费且无强制 key 要求，技术把握相对较高，作为探测阶段第一批建立方法论执行基准。**QA-R011 已明确要求即便是推荐重点候选也不能免于真实探测**，此前的核实仅停留在阅读参考项目代码逻辑，不能作为"已验证"的依据。

#### 具体操作
1. **Semantic Scholar**：已知信息（`goal.md`）——免费无需 key 即可用，配置 key 后限额从 100 req/5min 提升到 1000 req/5min；先核实 `reference-projects/paper-search-mcp-main/academic_platforms/semantic.py` 中实际调用的 Graph API 端点，据此发起真实请求，覆盖：关键词检索、按已知论文 ID/DOI 查询详情两类；记录无 key 情况下的真实限流表现（若触发 429，记录 `Retry-After`）。
2. **OpenAlex**：已知信息——完全免费，无需 key，`User-Agent` 中带邮箱可进入 polite pool 提升限额；核实 `academic_platforms/openalex.py` 真实端点后发起请求，覆盖：关键词检索、按 DOI 查询两类。
3. **Crossref**：已知信息——完全免费，无需 key，`mailto` 参数进 polite pool；核实 `academic_platforms/crossref.py` 真实端点后发起请求，覆盖：关键词检索、按 DOI 查询两类。
4. 按步骤 28 规范逐一记录三个候选的探测表格与止损分类结论。

#### 验证方法
- 三个候选均产出探测表格，含真实 HTTP 状态、真实字段结构摘要（至少包含标题/作者/DOI/摘要/引用数等本项目已有数据源普遍提供的核心字段是否存在）、止损分类结论。

#### 风险提示
- 不要因为这 3 个候选"此前代码核实较充分、大概率能过"而简化探测流程或减少边界用例覆盖，`goal.md` 约束条件明确要求同等地位对待全部 11 个通用候选。

---

### 步骤 30：真实探测批次二——PMC / Europe PMC / DOAJ / CORE（4 个中等价值候选）

#### 目标说明
`goal.md` QA-R010 A 表格标注为"中等价值"的分领域候选，此前仅核实 README 描述与代码逻辑，未做真实探测。其中 CORE 明确存在"无 key 限流更严、推荐但非强制注册 key"的特性，需重点验证有无 key 两种情况下的真实体验差异，为步骤 33 的止损判定提供依据。

#### 具体操作
1. **PMC**：核实是否存在 `academic_platforms/pmc.py`（若无，查阅 NCBI PMC/E-utilities 官方文档确定真实端点）；探测时需明确记录其与本项目已有 `pubmed_paper_search_by_query`（经 `paperscraper`→`pymed_paperscraper` 间接调用 NCBI E-utilities）在端点/返回内容上的实际差异，避免后续止损判定时把"高度重叠"这一存疑理由用错对象。
2. **Europe PMC**：核实真实端点（EBI 维护，非 NCBI）；因与 PMC 名称相近但维护方不同，**必须独立真实探测，不得假设二者行为一致**。
3. **DOAJ**：已知信息——免费，key 可选（提升限额）；先测无 key 情况下的真实可用性与字段丰富度。
4. **CORE**：**重点探测无 key 与有免费注册 key 两种体验的差异**——若本地暂无现成 key，至少完整记录"无 key 情况下的真实限流表现"（如连续请求几次后开始被限流），并在结论中如实标注"完整体验需要用户自行申请免费 key"，供步骤 33 判断是否落入止损规则第 2 类（技术可行但价值存疑）。

#### 验证方法
- 4 个候选均产出探测表格；CORE 额外产出"有无 key 对比"记录（即便暂无 key 可测，也需如实记录"未测试有 key 场景，无 key 场景结论为……"，不得跳过这一说明）。
- PMC/Europe PMC/现有 PubMed 三者的端点与返回内容差异已被明确记录，供步骤 33 判断是否存在功能重叠。

#### 风险提示
- PMC 与 Europe PMC、PMC 与本项目现有 PubMed 容易被想当然地判为重复而简化探测，探测阶段必须给出三者的真实端点/字段差异证据，重叠与否的最终判断留给步骤 33，不在本步骤自行下结论排除。

---

### 步骤 31：真实探测批次三——Zenodo / HAL / dblp / OpenAIRE（4 个中等价值候选）

#### 目标说明
均为免费无需 key 的候选，但 `goal.md` QA-R010 A 表格已提示 OpenAIRE 在参考项目代码中有"3 次重试+逐步升级请求头应对 403"的复杂逻辑，暗示服务端不稳定，需重点验证真实稳定性，为止损判定提供扎实依据而非停留在参考项目代码的间接推测。

#### 具体操作
1. **Zenodo**：核实真实端点后发起关键词检索请求，记录字段结构（Zenodo 覆盖数据集/软件/论文等多种资源类型，需确认检索结果中论文类资源的占比/可筛选性）。
2. **HAL**：核实真实端点后发起关键词检索请求；HAL 偏向法语/欧洲文献，探测时用英文关键词观察真实召回情况，如实记录覆盖面窄这一特点（若确实如此）。
3. **dblp**：核实真实端点后发起关键词检索请求；dblp 专注计算机科学领域文献目录，探测结论需明确说明这一覆盖范围局限。
4. **OpenAIRE**：**重点测试稳定性**——对同一端点连续发起至少 3～5 次真实请求，记录是否复现参考项目代码中描述的 403 问题；若复现，记录实际需要多少次重试/退避才能成功，作为止损判定依据。**若确认服务端确实经常性 403 且需要复杂重试逻辑才能勉强可用，属于止损规则第 2 类"技术可行但价值存疑"，需列入步骤 33 交还用户判断，不得因实现起来麻烦就自行判定为"技术不可行"直接排除，也不得因"多试几次总能成功"就简化为"技术可行且价值明确"直接落地**——这两种简化都是越权判断。

#### 验证方法
- 4 个候选均产出探测表格；OpenAIRE 额外产出"多次请求稳定性"记录（含每次请求的真实状态码序列）。

#### 风险提示
- OpenAIRE 的止损判定最容易被简化处理，需特别提醒 `project-builder-cn`：多次重试后能成功 ≠ 技术不可行；服务端不稳定需要复杂重试逻辑 ≠ 可以直接归为价值明确的落地候选；这类"技术可行但体验有代价"的情况，止损规则要求的处理方式是如实汇报给用户，而不是执行者自行拍板。

---

### 步骤 32：真实探测——bioRxiv/medRxiv（浏览语义）+ ChEMBL（DOI 查询语义）

#### 目标说明
这两个候选语义与其余 11 个通用检索型候选不同（浏览语义/DOI 关联数据查询语义），`goal.md` 已给出较明确的端点线索（见"v3.0.0 范围补充"小节），但仍属于 QA-R011"每个源都要真实探测"的范围，不能因端点路径已知就跳过真实验证，也不能因语义特殊就用与其余候选不同的、更宽松的探测标准。

#### 具体操作
1. **bioRxiv/medRxiv**：探测 `api.biorxiv.org/details/{server}/{start}/{end}/{cursor}`：
   - `server` 分别测试 `biorxiv`/`medrxiv` 两个取值，不假设二者行为完全一致。
   - `start`/`end` 使用近期真实日期区间（如最近 30 天），验证按分类/时间窗口浏览的真实返回结构（标题/作者/摘要/DOI/分类等字段以真实响应为准，不得照抄 `goal.md` 中转述的推测字段）。
   - 验证 `cursor` 分页参数的真实行为（翻页是否正确、超出范围时的响应）。
   - 额外验证边界：日期区间过大、`cursor` 超出实际数据范围时的真实响应。
2. **ChEMBL**：探测 `www.ebi.ac.uk/chembl/api/data/document.json?doi={doi}`：
   - 先用本项目此前 Elsevier 探测阶段已验证过的真实 DOI 样本（如 `10.1016/j.jmst.2026.07.003`）测试，**但需先确认该 DOI 恰好被 ChEMBL 收录**——ChEMBL 仅覆盖约 9.9 万篇药物化学相关论文（`goal.md` QA-R010 B 部分已核实），大概率不被收录；若未被收录，需另找一篇已知与药物化学/SAR 数据相关、大概率被 ChEMBL 收录的真实论文 DOI（例如知名药物化学期刊的公开论文）作为"已收录"场景的探测样本，**不能只验证"未收录"这一种响应路径就下结论**。
   - 验证"已收录"（含 SAR/生物活性数据字段，如 IC50/MIC/Ki）与"未收录"两种真实响应结构。
   - 验证非法 DOI 格式、空 `doi` 参数的错误响应。

#### 验证方法
- bioRxiv/medRxiv：两个 `server` 取值 + 边界日期/`cursor` 场景均有真实探测记录。
- ChEMBL：**必须**同时覆盖"已收录"和"未收录"两种真实响应场景才算完成探测；若探测过程中确实找不到合适的"已收录"样本，需在步骤 33 中如实注明"仅验证未收录路径，已收录路径的真实字段结构待有合适样本时补测"，不得凭 ChEMBL 官方文档字面描述凭空定义已收录响应的字段结构。

#### 风险提示
- bioRxiv/medRxiv 的探测脚本、记录文字、后续实现文档中，切勿使用"关键词搜索"等措辞描述该功能——`goal.md` 已明确要求"如实说明局限性，不得暗示支持任意关键词搜索"，这一要求同样适用于探测阶段的记录用词，避免探测结果的表述方式本身就先入为主地误导后续实现。
- ChEMBL 若最终无法找到合适的"已收录"真实样本完成验证，不得为了"凑齐"验证结果而编造字段结构，如实记录缺口即可，留待后续有合适样本时补测。

---

### 步骤 33：探测结果汇总 + 范围二次确认（检查点）

#### 目标说明
汇总步骤 28～32 产出的 13 个候选真实探测结果，按 `goal.md` 约束条件已定的止损规则完成最终分类。这是本轮范围从"13 个候选"收敛为"最终实现清单"的关键节点，也是"分批实现阶段"能够被 `project-planner-cn` 具体化为可执行步骤的前提条件——在本步骤完成前，不应有任何新数据源的正式实现代码被编写。

#### 具体操作
1. 汇总一张覆盖全部 13 个候选（11 个通用检索型 + bioRxiv/medRxiv + ChEMBL）的总表，列：候选名称 | 真实端点 | 真实探测 HTTP 状态摘要 | 真实字段结构摘要 | 限流/稳定性结论 | 止损分类（技术不可行排除 / 技术可行价值存疑需用户确认 / 技术可行且确认落地）。
2. 对"技术不可行"分类的候选，直接从 v3.0.0 落地清单中排除，在表格中写明具体排除依据（比照 `goal.md` QA-R002 先例的表述格式），**不需要**单独发起新一轮用户确认。
3. 对"技术可行但价值存疑"分类的候选，整理为清晰的候选对比清单（每项附真实探测证据摘要+存疑原因），作为向用户/`project-creator-cn` 汇报的材料，等待用户最终去留判断——**这一步不得由 `project-builder-cn` 自行拍板，必须真实交还决策，不能以"反正大概率会通过"为由代为决定**。
4. 将本步骤的完整汇总表格记入 `project-docs/buildlog.md`（延续步骤 28 要求的记录规范）；将"技术可行但价值存疑"的候选清单同步整理进 `project-docs/goal.md`（建议追加为新一轮 QA，比照 QA-R002 模式，由用户在后续对话中或经 `project-creator-cn` 确认），确保决策留痕、可追溯。
5. 待"价值存疑"候选的去留意见明确后（可能需要用户单独确认，非本步骤能自行终结），`project-planner-cn` 将基于最终确认的实现清单，在本文档中追加步骤 34 及以后的具体实现步骤（含每个数据源的参数签名、归一化字段、代码骨架、验证方法、风险提示），并同步细化"v3.0.0 范围补充"小节中预留的分批安排与收尾文档更新时机。

#### 验证方法
- 总表覆盖全部 13 个候选，每项均有明确的三分类结论之一，不留"未判断"的候选。
- "技术不可行"候选的排除依据均可追溯到步骤 28～32 的真实探测记录，不是凭印象下结论。
- "技术可行但价值存疑"清单已实际提交给用户（或 `project-creator-cn`），不是停留在 `project-builder-cn` 内部自行处理后就当作已解决。

#### 风险提示
- 本步骤是整个 v3.0.0 探测阶段的收口，若前序步骤 28～32 有候选遗漏未探测或探测不完整（如 ChEMBL 未覆盖"已收录"场景），必须在本步骤发现并回头补测，不能带着空白直接进入汇总。
- 不得因"想尽快进入实现阶段"而把"技术可行但价值存疑"的候选悄悄挪入"确认落地"分类，这违反 `goal.md` 约束条件明确写下的止损规则，属于越权决策，一旦发生需要在后续回溯时能被"止损分类"这张表清楚地核查出来。
- 本步骤完成后，若用户对"价值存疑"清单的回复导致最终落地数据源数量与最初 13 个候选有出入，`project-planner-cn` 后续追加的实现步骤数量与内容应以用户最终确认结果为准，不强行凑够或强行压缩到某个预设数字。

---

### 步骤 34：分批实现阶段总纲——公共规范、条件注册架构决策、注册组织方式

#### 目标说明
为步骤 35～42（12 个新数据源的实现 + 收尾）统一制定执行规范，避免在每个批次步骤中重复表述，并把 `goal.md` QA-R012/QA-R013 中两项留给 `project-planner-cn` 自行判断落地方式的开放性决策——"按 key 条件注册"架构的适用范围、`register_all_sources()` 的组织方式——正式定案。本步骤本身不产出任何数据源实现代码，是后续步骤共同遵守的执行规范，性质上与步骤 28（探测方法论总纲）对应，只是对象从"探测"换成"实现"。

#### 具体操作

**34.1 通用代码规范（延续现有 source-module 模式，12 个数据源全部适用）**
- 每个数据源独立文件 `src/uniarticles/sources/<name>.py`，暴露 `register(server: FastMCP) -> None`；文件内自带本模块的 `_ok(query, items)`/`_err(query, message)` 辅助函数，`source` 字段填数据源自身标识（如 `"openalex"`），**不复用** `scopus.py` 的 `_ok`/`_err`（那两个硬编码 `source="scopus"`，跨文件复用会导致响应体 `source` 字段值错误，与现有 `sciencedirect.py` 只复用 `scopus.py` 的 `_get_headers`/`BASE_URL`——这两个与 Elsevier 鉴权强相关、本轮新数据源用不上——而不复用 `_ok`/`_err` 的既有先例一致）。
- HTTP 调用统一用 `httpx.AsyncClient(timeout=30.0, ...)` + `await response.raise_for_status()` 的既有风格（对齐 `scopus.py`/`sciencedirect.py`）；异常统一在 `@server.tool()` 函数体的 `try/except Exception as exc: return _err(..., message=str(exc))` 中捕获。
- 参数校验风格对齐现有工具：字符串参数 `.strip()` 去空白、必填项判空直接 `_err`（不透传给远端产生难懂的错误）、数值参数（如 `max_results`）clamp 到合理区间（沿用项目惯例 `[1, 25]`，除非该数据源官方限制更严格）。
- **无新增第三方依赖**：全部 12 个数据源均为标准 REST/JSON 接口，用现有 `httpx` 即可完成，`pyproject.toml` 的 `dependencies` 无需改动。
- **Polite 请求头约定**：OpenAlex/Crossref 官方文档建议在 `User-Agent`/`mailto` 中携带联系方式以进入更高限额的 polite pool（探测阶段步骤 28 已用此惯例）。本轮不新增必需的环境变量，统一使用固定的项目标识 User-Agent（如 `"UniArticlesMCP/<version> (https://github.com/thinktraveller/UniArticles_MCPserver)"`），不强制用户配置联系邮箱；若未来需要进一步提升限额，应作为独立需求另行提出，本轮不预先设计新的环境变量。

**34.2 "按 key 条件注册"架构的适用范围决策（回应 `goal.md` QA-R012 留给 planner 的开放问题）**

`goal.md` 约束条件明确：Semantic Scholar 必须"无 key 不注册工具"；CORE 是否也套用同一模式，由本计划书自行判断。核实 `buildlog.md` 步骤 33 汇总表的真实探测证据后，给出以下**不对称处理**决策：

| 数据源 | 无 key 时的真实探测表现（`buildlog.md` 步骤 33） | 本计划书决策 |
|---|---|---|
| Semantic Scholar | 关键词检索**连续 4 次均 429**，核心检索能力无 key 时**确定性失败**；仅 by-DOI 查询可用（200） | **采用条件注册**：`register()` 内若 `settings.semantic_scholar_api_key` 为空，直接 `return`，模块内全部工具均不注册（含 by-DOI 查询，理由见下） |
| CORE | 无 key 检索**可正常返回 200**，仅在连续 5 次请求后触发 429 并锁定 10 分钟 | **不采用条件注册，沿用现有 Elsevier 式"无条件注册+运行时透明"模式**：始终注册工具，`core_api_key` 有值时加入鉴权头提升限额，无值时仍可用（退化为有限流约束的体验），在工具 docstring 与 README 中明确提示"建议配置 `CORE_API_KEY`，否则约 5 次请求后需等待 10 分钟" |

**理由**：两者虽然都"建议配置 key"，但无 key 时的实际可用性存在质的差异——Semantic Scholar 的核心检索功能无 key 时是"确定性失败"（4/4 次 429，非偶发），把一个必然报错的工具暴露在工具列表里，用户调用后只会得到清一色错误，等同"看得见用不了"，隐藏它更符合 `goal.md` 明确要求的初衷（"而不是注册了但调用时才报错"）；CORE 无 key 时是"有限次数内可正常工作、超额后短暂锁定"，属于现有 Elsevier 工具一直采用的"能用但有限流约束"模式（`scopus_api_usage_status` 同样只是报告限流状态而非阻止调用），继续沿用现有模式风险更低、也不引入新的不一致——本决策的判断标准明确为"无 key 时核心功能是否确定性失败"，可复用于未来类似决策，不是逐案拍脑袋。

**Semantic Scholar 的 by-DOI 查询为何也一并隐藏（而非只隐藏检索、保留 by-DOI）**：技术上可以做成"细粒度条件注册"（仅隐藏检索、保留 by-DOI），但 `goal.md` QA-R012 用户原话是"如果没有配置 Semantic Scholar 的 API key，就不启用/不注册该工具"，未区分模块内的子能力；且拆成两个粒度不同的工具（一个受 key 门控、一个不受）会让同一数据源在"有无 key"两种状态下呈现不一致的工具数量，增加用户理解成本。本计划书采用**整个模块级别**的条件注册，更贴合用户原话字面意思，也更容易验证（"有 key → 该数据源全部工具可见；无 key → 全部不可见"，二元判断，无需记忆哪个子工具例外）。

**34.3 `Settings` 新增字段**

`src/uniarticles/config.py` 新增两个可选字段（无需兼容性回退逻辑，这是全新的环境变量，不存在旧命名迁移问题）：
```python
@dataclass(frozen=True)
class Settings:
    elsevier_api_key: str | None = field(default_factory=_resolve_elsevier_api_key)
    elsevier_insttoken: str | None = os.getenv("ELSEVIER_INSTTOKEN")
    semantic_scholar_api_key: str | None = field(default_factory=lambda: os.getenv("SEMANTIC_SCHOLAR_API_KEY"))
    core_api_key: str | None = field(default_factory=lambda: os.getenv("CORE_API_KEY"))
```
`.env.example` 同步新增两行（含注释说明二者均为可选，Semantic Scholar 未配置时对应工具不会出现在工具列表中，CORE 未配置时工具仍可用但限流更严）：
```env
# 可选：不配置则 Semantic Scholar 相关工具不会注册（无 key 时该数据源检索功能实质不可用）
SEMANTIC_SCHOLAR_API_KEY=
# 可选：不配置 CORE 工具仍可用，但约 5 次请求后限流锁定 10 分钟
CORE_API_KEY=
```
用户本地 `.env` 已核实存在 `CORE_API_KEY`，`SEMANTIC_SCHOLAR_API_KEY` 尚未配置（key 申请中）——这正是验证"条件注册"逻辑的天然测试场景：构建时应能观察到 Semantic Scholar 工具在当前环境下不出现在工具列表中。

**34.4 `register_all_sources()` 分组组织方式**

`goal.md` 约束条件已声明这是非强制建议，留给实现阶段视情况决定。本计划书采用"按 v2.x 既有 / v3.0.0 通用检索型 / v3.0.0 语义特殊型"三段分组加注释：
```python
def register_all_sources(server: FastMCP) -> None:
    # v2.x 既有数据源（Elsevier 全家桶 + arXiv + PubMed）
    register_scopus_source(server)
    register_sciencedirect_source(server)
    register_arxiv_source(server)
    register_paperscraper_source(server)
    # v3.0.0 新增：通用检索型（标准 query 关键词检索模式）
    register_openalex_source(server)
    register_crossref_source(server)
    register_europepmc_source(server)
    register_doaj_source(server)
    register_zenodo_source(server)
    register_hal_source(server)
    register_openaire_source(server)
    register_semantic_scholar_source(server)  # 无 key 时内部不注册任何工具
    register_core_source(server)
    register_dblp_source(server)
    # v3.0.0 新增：语义特殊型（非关键词检索）
    register_biorxiv_source(server)  # 浏览语义
    register_chembl_source(server)   # DOI 查询语义
```
该顺序具体落地在步骤 40 执行，本步骤先行定案分组方式与顺序规则，供步骤 35～39 各批次实现时预先知晓自己模块在最终注册顺序中的位置（不要求各批次实现时就同步改 `__init__.py`，统一在步骤 40 一次性完成，避免多批次并行改同一文件产生冲突）。

**34.5 `_verify/` 流程约束（`goal.md` QA-R013 新增通用规则，本轮首次落地执行）**

`goal.md` 明确要求：今后任何构建/测试环节，若 agent 在自身探测/验证环境中遇到失败结果（尤其网络类失败），不得仅凭自身单次结果下结论，必须把验证脚本产出到仓库 `_verify/` 目录，交用户独立验证。本轮已知最可能触发该规则的是**步骤 39（dblp）**——其在步骤 28～33 的原始探测就曾遭遇网络层拦截，即便用户后续两次复测已给出"服务端可用"的结论，`project-builder-cn` 在本轮实现阶段自己的环境中若再次连接失败，**不得**直接判定实现有 bug 或服务不可用，应比照已有先例 `_verify/dblp_connectivity_test.py`（commit `9948687`/`abd3e3f`）的做法处理，具体要求见步骤 39。其余 11 个数据源若在实现阶段的真实调用验证中遇到网络类失败（而非明确的字段解析错误/代码逻辑错误），同样应遵循这一规则。

#### 验证方法
- `Settings` 新增的两个字段可通过 `python -c "from uniarticles.config import settings; print(settings.semantic_scholar_api_key, settings.core_api_key)"` 读出预期值（当前环境下分别应为 `None` 和真实 key 字符串）。
- 本步骤本身不产出可独立验证的运行时行为，验证将在步骤 37（条件注册实现）与步骤 40（注册顺序）中体现。

#### 风险提示
- 34.2 的不对称决策（Semantic Scholar 条件注册、CORE 不条件注册）是本计划书基于真实探测证据做出的专业判断，不是 `goal.md` 的字面指令；若后续用户认为 CORE 也应做条件注册，可在 `project-builder-cn` 执行本步骤前明确提出调整，避免已按本方案实现后再返工。
- `.env.example` 新增两行时注意不要误改文件中已有的 `ELSEVIER_API_KEY`/`ELSEVIER_INSTTOKEN` 行的相对顺序或格式。

---

### 步骤 35：批次一实现——OpenAlex / Crossref / Europe PMC / DOAJ（4 个标准通用检索源）

#### 目标说明
这 4 个数据源在步骤 28～33 真实探测中均已确认：无需 key、字段结构清晰完整、返回 200 且可直接解析（详见 `buildlog.md` 步骤 33 汇总表 #2/#3/#5/#6 行）。均遵循标准"关键词检索 + 按 DOI/标识符精确查询"两件套模式，是本轮实现难度最低的一组，可作为后续批次的参照基准。

#### 具体操作

**35.1 OpenAlex（`src/uniarticles/sources/openalex.py`）**
- 端点：`https://api.openalex.org/works`（关键词检索，`search` 参数）、`https://api.openalex.org/works/https://doi.org/{doi}`（按 DOI 精确查询，OpenAlex 官方支持把完整 DOI URL 拼在路径里）。
- **归一化关键坑点（务必处理，不得省略）**：OpenAlex 不直接返回摘要正文，而是返回 `abstract_inverted_index`（倒排索引：`{"word": [位置1, 位置2, ...]}`），需按位置重新拼接成可读摘要文本，否则 `abstract` 字段会是不可读的 dict，与本项目其余工具"abstract 是可读字符串"的一贯约定不一致：
  ```python
  def _reconstruct_abstract(inverted_index: dict | None) -> str | None:
      if not inverted_index:
          return None
      positions: dict[int, str] = {}
      for word, idxs in inverted_index.items():
          for idx in idxs:
              positions[idx] = word
      if not positions:
          return None
      return " ".join(positions[i] for i in sorted(positions))
  ```
- 归一化字段（真实键名，来自 `buildlog.md` 步骤 29 探测记录）：`id`（OpenAlex ID）、`doi`、`title`、`authors`（从 `authorships[].author.display_name` 提取）、`abstract`（用上述函数处理 `abstract_inverted_index`）、`cited_by_count`、`open_access`（`open_access.is_oa`/`open_access.oa_url`）、`publication_year`、`primary_location`（期刊/来源名，`primary_location.source.display_name`）。
- 工具：`openalex_work_search_by_query(query: str, max_results: int = 10) -> dict`、`openalex_work_detail_by_doi(doi: str) -> dict`。`max_results` clamp `[1, 25]`，映射到 OpenAlex 的 `per_page` 参数。
- 坏 DOI 查询已探测确认返回 **404**，`httpx` 的 `raise_for_status()` 会抛出 `HTTPStatusError`，工具层 `except Exception` 捕获后统一转 `_err`，无需为 404 单独分支。

**35.2 Crossref（`src/uniarticles/sources/crossref.py`）**
- 端点：`https://api.crossref.org/works`（`query` 参数关键词检索）、`https://api.crossref.org/works/{doi}`（按 DOI 精确查询）。
- **归一化坑点**：Crossref 的 `title`/`container-title`（期刊名）均为**数组**而非字符串（即便通常只有一个元素），`author` 是对象数组（`given`/`family` 需拼接成姓名），直接 `entry.get("title")` 会拿到 `["..."]` 而非字符串，需 `(entry.get("title") or [None])[0]` 取首项。
- 归一化字段（真实键名）：`doi`（原始字段名是大写 `DOI`）、`title`（数组取首项）、`authors`（`author[]` 的 `given`+`family` 拼接）、`abstract`（`abstract` 字段，Crossref 常带 JATS XML 标签如 `<jats:p>`，是否清洗标签由 `project-builder-cn` 视实际抓包结果决定）、`cited_by_count`（`is-referenced-by-count`）、`container_title`（数组取首项）、`url`（`URL`）、`published`（`published.date-parts`，嵌套数组如 `[[2024, 3, 15]]`，需拼接成日期字符串或保留原始结构，由 builder 视一致性决定）。
- 工具：`crossref_work_search_by_query(query: str, max_results: int = 10) -> dict`、`crossref_work_detail_by_doi(doi: str) -> dict`。请求携带 `mailto` 参数（polite pool），沿用步骤 34.1 约定的固定项目标识。
- 限流：探测确认 `x-rate-limit-limit: 3/1s`（检索）、`10/1s`（by-DOI），无需 key；工具层无需额外限流处理，依赖 `httpx` 超时+异常捕获即可，不引入新的限流中间件。

**35.3 Europe PMC（`src/uniarticles/sources/europepmc.py`）**
- 端点：`https://www.ebi.ac.uk/europepmc/webservices/rest/search`（`query` 参数）。**注意与本项目已有 `pubmed_paper_search_by_query`、本轮排除的 PMC 三者均不同源**（Europe PMC 维护方是 EBI，非 NCBI），实现时不得复用 `paperscraper` 的 PubMed 逻辑。
- 归一化字段（真实键名）：`id`、`source`、`pmcid`、`title`、`doi`（若探测响应中确认存在，若 `buildlog.md` 步骤 29 未记录该字段需在实现前补测一次确认字段名，不得假设）、`cited_by_count`（`citedByCount`）、`in_epmc`（`inEPMC`）、`in_pmc`（`inPMC`）、`has_pdf`（`hasPDF`）、`first_publication_date`（`firstPublicationDate`）。
- **游标分页**：响应含 `nextCursorMark`，工具签名可选提供 `cursor: str | None = None` 支持翻页，或本轮先只做单页查询、不暴露游标参数（更简单，`max_results` 控制单页条数即可）——由 `project-builder-cn` 视实现复杂度取舍，若选择不支持分页需在工具 docstring 中如实说明"仅返回首页结果"。
- 工具：`europepmc_paper_search_by_query(query: str, max_results: int = 10) -> dict`。

**35.4 DOAJ（`src/uniarticles/sources/doaj.py`）**
- 端点：`https://doaj.org/api/search/articles/{query}`（**注意 query 是拼进 URL 路径而非 query string 参数**，需做 URL 编码，用 `urllib.parse.quote` 处理特殊字符，不能直接字符串拼接未转义的用户输入）。
- 归一化字段（真实键名，均在 `bibjson` 对象下）：`title`（`bibjson.title`）、`authors`（`bibjson.author[].name`）、`abstract`（`bibjson.abstract`）、`keywords`（`bibjson.keyword`）、`journal`（`bibjson.journal.title`）、`doi`（从 `bibjson.identifier[]` 中筛选 `type=="doi"` 的 `id`）、`links`（`bibjson.link[]`，含全文/OA 链接）、`subjects`（`bibjson.subject[]`）。
- 工具：`doaj_article_search_by_query(query: str, max_results: int = 10) -> dict`。key 可选，本轮探测未验证有 key 场景的具体差异，工具应在无 key 情况下正常工作，不强制新增 `Settings` 字段——除非未来用户明确要求提升限额。

#### 验证方法
- 用真实关键词（如 `machine learning`，与探测阶段样本一致，便于比对）分别调用 4 个数据源的检索工具，确认均返回 `ok: true` 且 `items` 为逐字段结构（非原始 JSON blob）。
- OpenAlex/Crossref 额外用真实 DOI（如探测阶段样本 `10.1016/j.physletb.2012.08.020`）调用 by-DOI 工具，确认能正确返回；用一个不存在的假 DOI 调用，确认走 `_err` 分支（对应探测确认的 404）。
- OpenAlex 摘要重建函数需专门测一次：找一篇 `abstract_inverted_index` 非空的真实论文，确认 `abstract` 字段输出的是连贯可读文本而非倒排索引 dict 或乱序词语。
- Crossref 的 `title`/`container_title` 字段需确认最终归一化结果是字符串而非数组。

#### 风险提示
- OpenAlex 摘要重建逻辑如果实现时"偷懒"直接透传 `abstract_inverted_index`，会导致下游 LLM 客户端拿到不可读的位置索引字典，必须重建为文本，这是本批次唯一一处"直接透传会产生错误可用性"的坑点，务必落实。
- Crossref 的 `title`/`container-title`/`author` 均需做数组/对象解包，不能照搬 `entry.get("title")` 这类简单写法，否则字段类型与项目其余工具（均为字符串/字符串数组）不一致，容易让下游 LLM 误判数据结构。
- DOAJ 的 URL 路径拼接查询词需做转义，避免特殊字符（空格、`/`、`&` 等）破坏请求路径。
- 4 个数据源均不需要 key，但仍应在网络调用失败（超时/DNS 失败/连接拒绝）时走 `_err` 分支返回清晰错误，不能让未捕获异常导致 MCP 进程崩溃——这是项目一贯要求，非本批次新增。

---

### 步骤 36：批次二实现——Zenodo / HAL / OpenAIRE（3 个需要额外结构处理的检索源）

#### 目标说明
这 3 个数据源同样无需 key、探测确认可行（`buildlog.md` 步骤 33 汇总表 #8/#9/#11 行），但各自都有一个需要额外处理的结构性特点（Zenodo 混合资源类型、HAL 的 Solr 字段选择语法、OpenAIRE 的深层嵌套响应），归一化实现比批次一（步骤 35）复杂，故单独分批，避免与"标准两件套"模式混淆。

#### 具体操作

**36.1 Zenodo（`src/uniarticles/sources/zenodo.py`）**
- 端点：`https://zenodo.org/api/records`，**必须携带 `type=publication` 过滤参数**——Zenodo 是通用研究成果仓库（同时托管数据集/软件/论文/海报等），不加此过滤会返回大量非论文类资源，与本项目"学术文献检索"定位不符（探测记录已确认此特性，见 `buildlog.md` 步骤 31）。
- 归一化字段（真实键名）：`doi`、`conceptdoi`（同一记录不同版本共享的概念 DOI）、`title`（`metadata.title`）、`authors`（`metadata.creators[].name`）、`description`（`metadata.description`，可能含 HTML 标签，视抓包结果决定是否清洗）、`publication_date`（`metadata.publication_date`）、`file_links`（从 `files[]` 中只提取文件名+链接，**不**归一化全文内容——比照 `sciencedirect_article_object_by_identifier` 的既有产品定位原则，只暴露元信息/链接，不做下载搬运）。
- 工具：`zenodo_record_search_by_query(query: str, max_results: int = 10) -> dict`，内部固定拼接 `type=publication`，不作为可选参数暴露给调用方（保持工具语义单一，避免调用方误传其他 type 值导致检索出非论文资源却以为在用"学术文献检索"工具）。
- 限流：探测确认 `x-ratelimit-limit: 30`（每分钟），无需 key，工具层无需特殊处理。

**36.2 HAL（`src/uniarticles/sources/hal.py`）**
- 端点：`https://api.archives-ouvertes.fr/search/`（Solr 检索接口，`q` 参数为关键词，`fl` 参数**必须显式指定**要返回的字段列表，否则 Solr 默认字段集可能不含所需信息或包含大量冗余字段）。
- 归一化字段（真实键名，均带 Solr 动态字段后缀 `_s`）：`docid`、`title`（`title_s`，是单值还是数组需在编码前对真实响应实际确认，`buildlog.md` 未细化到这一层，不得假设）、`abstract`（`abstract_s`）、`authors`（`authFullName_s`，通常是数组）、`doi`（`doiId_s`）、`url`（`uri_s`）、`doc_type`（`docType_s`）。请求需在 `fl` 参数中列出全部需要的字段名（如 `fl=docid,title_s,abstract_s,authFullName_s,doiId_s,uri_s,docType_s`），否则响应可能缺失部分字段。
- 工具：`hal_document_search_by_query(query: str, max_results: int = 10) -> dict`，docstring 需注明"HAL 偏重法语/欧洲学术产出，英文关键词检索有召回但覆盖面可能不如面向英语文献的数据源全面"（`buildlog.md` 步骤 31 已如实记录这一特点，实现文档需同步体现，不夸大覆盖面）。

**36.3 OpenAIRE（`src/uniarticles/sources/openaire.py`）**
- 端点：`https://api.openaire.eu/search/researchProducts`（`keywords` 参数关键词检索）。
- **归一化关键坑点**：响应是**深层嵌套结构**（`response.results.result[].metadata["oaf:entity"]["oaf:result"]`，键名含 `oaf:` XML 命名空间前缀，说明这是从 XML 转换来的 JSON），比本轮其余所有数据源都更复杂，需要专门的嵌套导航函数，并对单元素被压缩为 dict（而非 list）的情况做兼容——**这一特性在本项目 Elsevier 代码中已有先例**：`scopus.py` 的 `_as_list()` 正是处理同一类"单个元素返回 dict、多个返回 list"的问题，建议在 `openaire.py` 内新增一个本地 `_as_list()`（不跨文件导入 `scopus.py` 版本，保持每个 source 模块自包含）：
  ```python
  def _as_list(value):
      if value is None:
          return []
      return value if isinstance(value, list) else [value]

  def _extract_results(payload: dict) -> list[dict]:
      results = payload.get("response", {}).get("results", {}).get("result", [])
      return [r for r in _as_list(results) if isinstance(r, dict)]
  ```
  归一化字段（真实键名，路径均在 `metadata["oaf:entity"]["oaf:result"]` 下）：`title`、`creator`（作者，可能是列表或单个对象，同样需 `_as_list` 处理）、`pid`（标识符，可能含 DOI，需按类型筛选，如 `pid[].classid=="doi"` 对应的 `$` 值——具体判别写法以 `project-builder-cn` 实现前对真实响应的抓包结果为准，`buildlog.md` 目前只记录到字段名层级，未记录 `pid` 内部按类型筛选的具体写法，属于本步骤需要在编码前二次确认的细节）、`subject`、`bestaccessright`（开放获取状态）、`publisher`。
- 工具：`openaire_research_product_search_by_query(query: str, max_results: int = 10) -> dict`。docstring 附注（延续步骤 31 探测记录的透明度要求）："参考项目历史记录曾显示该服务偶发 403，本项目探测环境下连续 5 次请求均未复现；若实际使用中遇到网络类错误，属已知可能的服务端不稳定，非本工具实现缺陷"。

#### 验证方法
- 3 个工具均用真实关键词调用，确认返回 `ok: true` 且 `items` 为逐字段结构。
- Zenodo：确认返回结果均为论文类资源，未混入数据集/软件类资源。
- HAL：确认 `fl` 参数生效——对比不传 `fl` 与传 `fl` 两种请求的响应差异，确认显式声明字段列表是必要步骤而非可省略的多余操作。
- OpenAIRE：用真实关键词调用，确认深层嵌套结构被正确导航到（`items` 中每项应为扁平的归一化对象，而非仍嵌套着 `response.results.result` 等中间层级）；额外用一个只返回单条结果的窄关键词测试，确认单元素被 `_as_list` 正确处理。

#### 风险提示
- OpenAIRE 的 `pid` 字段（DOI 等标识符）内部按类型筛选的具体写法，`buildlog.md` 探测记录未细化到这一层，`project-builder-cn` 实现前需要对真实响应做一次针对性抓包确认，不得凭字段名"看起来像"就假设写法，这是本步骤唯一一处需要"编码前再确认一次细节"的地方。
- HAL 的 `title_s`/`authFullName_s` 等 Solr 动态字段是单值还是多值（数组）未在探测记录中明确区分，实现前需实际打印一次真实响应确认，避免按错误的类型假设编码导致解析异常。
- Zenodo 若不慎遗漏 `type=publication` 过滤参数，会导致该工具实际检索范围远超"学术文献"，与产品定位不符，编码后务必用验证方法中"确认均为论文类资源"这一项复查。

---

### 步骤 37：批次三实现——Semantic Scholar / CORE（按 key 条件注册架构落地）

#### 目标说明
落地步骤 34.2 已定案的架构决策：Semantic Scholar 采用"无 key 不注册工具"的条件注册模式（`goal.md` QA-R012 明确要求）；CORE 沿用现有 Elsevier 式"无条件注册、key 可选提升体验"模式。这是本项目至今第一次实现"模块级条件注册"，需要重点验证该逻辑本身工作正常（有 key 时正常注册、无 key 时完全不出现在工具列表），而不仅是验证数据源本身的检索功能。

#### 具体操作

**37.1 Semantic Scholar（`src/uniarticles/sources/semantic_scholar.py`）**
- 端点：`https://api.semanticscholar.org/graph/v1/paper/search`（关键词检索，`query` 参数）、`https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}`（按 DOI 精确查询）。有 key 时通过请求头 `x-api-key` 携带。
- 归一化字段（真实键名，来自 `buildlog.md` 步骤 29 探测记录）：`paper_id`（`paperId`）、`doi`（`externalIds.DOI`，`externalIds` 下还可能有 `ArXiv`/`PubMed` 等其他标识符，视需要一并提取）、`title`、`cited_by_count`（`citationCount`）。探测记录字段较基础，若实现时请求携带更完整的 `fields` query 参数（Semantic Scholar Graph API 支持 `fields=title,abstract,authors,year,citationCount,externalIds` 显式声明返回字段），建议在实现前用真实 key（若已申请到）验证一次，确认能拿到 `abstract`/`authors`/`year` 等本项目其余工具普遍提供的核心字段，不要因探测记录只列了 4 个字段就在实现中也只归一化这 4 个字段。
- **条件注册实现**：
  ```python
  def register(server: FastMCP) -> None:
      if not settings.semantic_scholar_api_key:
          # No key configured: Semantic Scholar's core search capability fails
          # deterministically without a key (confirmed 429 on every request during
          # probing). Per goal.md QA-R012, do not register ANY tool from this module
          # rather than exposing a tool that will always error at call time.
          return

      @server.tool()
      async def semantic_scholar_paper_search_by_query(query: str, max_results: int = 10) -> dict:
          """Search Semantic Scholar by keyword. Requires SEMANTIC_SCHOLAR_API_KEY to
          be configured (this tool is not registered at all if the key is missing)."""
          ...

      @server.tool()
      async def semantic_scholar_paper_detail_by_doi(doi: str) -> dict:
          """Look up a paper on Semantic Scholar by DOI. Requires
          SEMANTIC_SCHOLAR_API_KEY (see module-level note)."""
          ...
  ```
- 工具：`semantic_scholar_paper_search_by_query(query: str, max_results: int = 10) -> dict`、`semantic_scholar_paper_detail_by_doi(doi: str) -> dict`（两者均仅在有 key 时存在）。

**37.2 CORE（`src/uniarticles/sources/core.py`）**
- 端点：`https://api.core.ac.uk/v3/search/works`（`q` 参数关键词检索）。有 key 时通过请求头 `Authorization: Bearer {key}` 携带（若 `project-builder-cn` 实现前发现 CORE 官方文档规定的鉴权头格式与此不同，以官方文档/实测为准调整）。
- 归一化字段（真实键名）：`title`、`authors`、`abstract`、`doi`、`citation_count`（`citationCount`）、`download_url`（`downloadUrl`，**不**默认把 `fullText` 全文塞进 `items`，只暴露下载链接，与本项目一贯"只返回元信息/链接、不做下载/全文搬运"的产品定位保持一致，比照 `sciencedirect_article_object_by_identifier` 的既有处理原则）、`arxiv_id`（`arxivId`）、`pubmed_id`（`pubmedId`）。
- **无条件注册**（对齐现有 Elsevier 工具风格）：
  ```python
  def register(server: FastMCP) -> None:
      @server.tool()
      async def core_work_search_by_query(query: str, max_results: int = 10) -> dict:
          """Search CORE (global OA aggregator) by keyword. Works without an API key
          (~5 requests before a 10-minute rate-limit lockout); configuring
          CORE_API_KEY is recommended for reliable use. See README for how to obtain
          a free key."""
          ...
  ```
  内部实现中，`settings.core_api_key` 有值时加入鉴权头；无值时不加鉴权头直接请求（探测已确认无 key 仍可用，只是限流更严）。若请求触发 429，工具层应将 CORE 返回的限流相关响应头（如 `x-ratelimit-retry-after`，探测记录已确认存在该头）一并整理进 `_err` 的 `message`，让调用方能看懂"为什么现在不能用、大概什么时候能重试"，而不是只返回一句笼统的 HTTP 错误文本。
- 工具：`core_work_search_by_query(query: str, max_results: int = 10) -> dict`。

#### 验证方法
- **条件注册专项验证**（本步骤最重要的验证项）：
  1. 当前环境（`.env` 无 `SEMANTIC_SCHOLAR_API_KEY`）下启动服务，通过 MCP 工具枚举确认**不出现** `semantic_scholar_paper_search_by_query`/`semantic_scholar_paper_detail_by_doi` 任何一个工具。
  2. 临时在本地 `.env` 中设置一个测试用 `SEMANTIC_SCHOLAR_API_KEY`（哪怕是无效值，只为验证注册逻辑本身，不验证真实调用成功率）重启服务，确认此时**两个工具均出现**在工具列表中。
  3. 恢复步骤 1 的无 key 状态，确认工具再次消失——验证该逻辑是纯粹依据当前配置动态决定，无缓存/残留状态问题。
- 待用户申请到真实 `SEMANTIC_SCHOLAR_API_KEY` 后，补充一次真实检索+by-DOI 调用验证（若本轮构建时 key 仍未到手，可先只做条件注册逻辑验证，真实功能验证留到用户拿到 key 后自行确认，在 buildlog.md 中如实标注"条件注册逻辑已验证，真实检索功能待用户配置 key 后自行验证"）。
- CORE：用真实关键词调用确认 `ok: true`；连续调用 6 次以上验证是否复现探测阶段观察到的"第 6 次 429"限流行为，若复现确认 `_err` 中包含限流相关的可读提示（而非仅一句 HTTP 状态码文本）。

#### 风险提示
- 条件注册逻辑最容易被误实现为"注册了工具，但工具内部 `try/except` 捕获无 key 情况后返回 `_err`"——这**不等同于** `goal.md` 要求的"不注册"，二者在 MCP 客户端工具列表可见性上有本质区别，必须是 `register()` 函数体内的**提前 `return`**，让 `@server.tool()` 装饰器根本不被执行，而不是把判断逻辑放进工具函数体内部。
- Semantic Scholar 若实现时携带了 `fields` 参数扩展字段范围，需注意这可能改变探测阶段记录的响应结构（探测只用了默认字段集），实现前建议做一次针对性验证而非直接照抄探测记录的字段清单。
- CORE 的鉴权头格式（`Authorization: Bearer` vs 其他约定）探测阶段未逐一验证不同鉴权头写法的效果，若实现时用户已配置的真实 `CORE_API_KEY` 调用失败，应优先核实鉴权头格式是否符合 CORE 官方文档，而非假设 key 本身无效。

---

### 步骤 38：批次四实现——bioRxiv/medRxiv（浏览语义）+ ChEMBL（DOI 查询语义）

#### 目标说明
这两个数据源在 `goal.md` 约束条件与本计划书"v3.0.0 范围补充"小节中已被反复强调：参数签名与产品语义**不得**比照其余 10 个通用检索型数据源的 `query`+`max_results` 模式设计，必须分别体现"按分类+时间窗口浏览"与"DOI 必填的关联数据查询"两种不同语义。真实探测结果（`buildlog.md` 步骤 32/33）已完整覆盖两种数据源的核心路径，可直接据实编码，无需额外前置探测。

#### 具体操作

**38.1 bioRxiv/medRxiv（`src/uniarticles/sources/biorxiv.py`，一个文件覆盖两个 server）**
- 端点：`https://api.biorxiv.org/details/{server}/{start_date}/{end_date}/{cursor}`，`server` 取值 `biorxiv`/`medrxiv`，`start_date`/`end_date` 为 `YYYY-MM-DD` 格式日期，`cursor` 为分页游标（整数，默认 `0`）。
- **工具签名严格禁止出现 `query`/关键词参数**，签名设计为：
  ```python
  @server.tool()
  async def biorxiv_paper_list_by_date_range(
      server: str,
      start_date: str,
      end_date: str,
      cursor: int = 0,
  ) -> dict:
      """Browse bioRxiv/medRxiv preprints within a date range (NOT keyword search —
      the official API only supports browsing by date window). `server` must be
      'biorxiv' or 'medrxiv'. Dates are YYYY-MM-DD. Use `cursor` (see response) to
      page through results (30 per page)."""
  ```
- `server` 参数做枚举校验（`{"biorxiv", "medrxiv"}` 之外直接 `_err`，不透传给 API），`start_date`/`end_date` 建议做基础格式校验（正则或 `datetime.strptime` 尝试解析，失败直接 `_err`，不透传给 API 产生远端错误），`cursor` 默认 `0`。
- 归一化字段（真实键名，来自 `buildlog.md` 步骤 32 探测记录）：分页信息 `total`/`count`/`cursor`（来自 `messages[0]`），逐条 `title`/`authors`/`doi`/`date`/`version`/`type`/`category`/`abstract`/`published`/`server`（来自 `collection[]`）。**分页信息如何呈现需权衡**：项目现有 `_ok`/`_err` 固定为 `{"ok","source","query","count","items","error"}` 五个键，不建议为容纳游标而扩展这一全局响应契约；折中做法是把翻页提示写进 `query` 描述文本（如 `"biorxiv 2026-07-01~2026-07-31 (cursor=30, has_more=true)"`），或在 docstring 中说明"如需更多结果，可加大日期区间或自行传入更大的 `cursor` 重新调用"，不强行支持自动翻页。具体取舍由 `project-builder-cn` 决定，需在 buildlog.md 中记录选择理由。
- 边界：`cursor` 超出实际数据范围时探测已确认返回 200 且 `collection` 为空，工具层应正常返回 `_ok(items=[])` 而非误判为错误。

**38.2 ChEMBL（`src/uniarticles/sources/chembl.py`）**
- 端点：`https://www.ebi.ac.uk/chembl/api/data/document.json?doi={doi}`（判断是否收录+基础文献信息）+ `https://www.ebi.ac.uk/chembl/api/data/activity.json?document_chembl_id={id}`（收录情况下进一步查询 SAR/生物活性数据）。
- **`doi` 严格必填，且必须在客户端前置校验非空**（`goal.md` QA-R011/约束条件明确要求，探测已确认空 `doi` 传给 API 会返回 200 全量分页数据而非报错，如果不做前置校验，空字符串调用会得到一个巨大的、与"这篇论文的 ChEMBL 数据"完全无关的错误结果，必须在工具层拦截）：
  ```python
  @server.tool()
  async def chembl_bioactivity_lookup_by_doi(doi: str) -> dict:
      """Look up whether a paper (by DOI) is indexed in ChEMBL and, if so, its
      structured SAR/bioactivity data (IC50/MIC/Ki, etc.). This is NOT a keyword
      search tool — doi is required and must be non-empty. Most papers are NOT in
      ChEMBL (it covers ~99k medicinal-chemistry papers only); an empty result with
      collected=false is a normal, expected outcome, not an error."""
      normalized_doi = doi.strip() if doi else ""
      if not normalized_doi:
          return _err(query=doi, message="doi must not be empty")
      try:
          return await _lookup_chembl(doi=normalized_doi)
      except Exception as exc:
          return _err(query=normalized_doi, message=str(exc))
  ```
- 内部函数 `_lookup_chembl(doi)` 先请求 `document.json?doi=...`，`page_meta.total_count == 0` 时直接返回 `_ok(items=[{"collected": False, "doi": doi}])`（未收录是干净的预期结果，不是错误，探测已确认此路径响应结构清晰）；`total_count >= 1` 时取 `documents[0].document_chembl_id`，再请求 `activity.json?document_chembl_id=...`，把两次请求的结果合并进单个归一化 item：
  - 文档层字段（真实键名）：`document_chembl_id`/`doi`/`title`/`authors`/`abstract`/`journal`/`pubmed_id`/`year`。
  - 生物活性层字段（真实键名，`activities[]` 逐条）：`standard_type`（如 `IC50`）/`standard_value`/`standard_units`/`pchembl_value`/`canonical_smiles`/`target_pref_name`/`molecule_chembl_id`/`assay_description`。
  - 归一化输出建议结构：`{"collected": True, "document": {...}, "activities": [...]}`，放入 `_ok()` 的 `items` 列表（单元素列表，与项目其余"单条详情类"工具如 `scopus_abstract_detail_by_eid` 的 `items=[normalized]` 风格一致）。
- ChEMBL 文档层理论上可能返回多篇匹配文档（探测样本是 1 篇），若实现时发现为每篇都补查 `activities` 会显著增加请求次数/延迟，可先支持"仅处理第一条匹配文档"并在 docstring 注明这一简化，避免不必要的过度设计。

#### 验证方法
- bioRxiv/medRxiv：分别用 `server="biorxiv"` 与 `server="medrxiv"`、近期真实日期区间调用，确认 `ok: true` 且条目含真实标题/作者/DOI；用非法 `server` 值（如 `"arxiv"`）调用确认走 `_err`；用超出范围的 `cursor` 调用确认返回空 `items` 而非报错。
- ChEMBL：用探测阶段已验证的"已收录"样本 DOI（`10.1021/jm401507s`）调用，确认返回 `collected: true` 且 `activities` 非空、含真实 `standard_type`/`standard_value` 等字段；用"未收录"样本（如 Higgs 论文 DOI `10.1016/j.physletb.2012.08.020`）调用，确认返回 `collected: false`；用空字符串调用，确认走 `_err` 而非把空 doi 透传给 API。

#### 风险提示
- bioRxiv/medRxiv 的工具描述、参数名、README 描述中**严禁**出现"搜索"/"检索关键词"等措辞，一律使用"浏览"/"按日期区间列出"等准确表述，这是 `goal.md` 反复强调的硬性要求，不是可选的措辞偏好。
- ChEMBL 若因"图省事"而跳过客户端 `doi` 非空校验、直接透传给 API，会因空 `doi` 返回全量分页数据而产生一个极大且无意义的响应体，必须严格执行前置校验。
- 两个工具的参数签名如果被实现成与其余 10 个通用检索源一致的 `query`+`max_results` 模式，属于对 `goal.md` 明确约束的违反，构建验证阶段应重点检查这一点。

---

### 步骤 39：dblp 实现（含已知网络波动风险提示 + 编码前字段结构补测）

#### 目标说明
dblp 是本轮 12 个数据源中唯一一个**尚未采集到完整真实字段结构**的候选——`goal.md` QA-R013 记录的用户第二次实测只确认了 HTTP 200 与响应根结构片段（`{"result":{"query":"...", "status":{"@code":"200","text":"OK"}, ...}}`，其余部分未完整记录），不足以直接支撑归一化编码。同时 dblp 是本轮唯一已知存在"间歇性网络失败"风险的数据源（三次实测分别为 TLS 握手失败/HTTP 500/完全成功），需要在实现与错误提示文案中体现这一特性，并严格遵循 `goal.md` QA-R013 新增的 `_verify/` 流程约束。

#### 具体操作

**39.1 编码前字段结构补测（强制前置步骤，性质同步骤 14/21）**
- 使用真实网络环境，对 `https://dblp.org/search/publ/api?q={query}&format=json&h={h}` 发起真实请求，完整打印/记录响应体 JSON（可参考已有 `_verify/dblp_connectivity_test.py` 的请求逻辑，但该脚本目的是连通性诊断，需另编写一个聚焦"采集完整字段结构"的一次性探测脚本）。
- 完整记录 `result.hits.hit[]` 下每条命中记录的真实字段结构（如 `@id`/`info.title`/`info.authors`/`info.venue`/`info.year`/`info.type`/`info.doi`/`info.url`/`info.key` 等——这些是根据 dblp 官方 API 文档的一般性认知列出的**待验证候选字段名**，**不是**已确认的真实抓包结果，不得照抄直接编码）。
- **若本轮构建时（`project-builder-cn` 自身探测环境）再次遇到网络失败**（TLS 握手失败、超时或其他网络类错误）：**不得**直接判定 dblp 实现有问题或服务不可用，必须执行 `goal.md` QA-R013 新增的通用流程约束——把本次用于采集字段结构的探测脚本保存到仓库 `_verify/` 目录（可另起文件名如 `_verify/dblp_field_probe.py`，与已有的 `_verify/dblp_connectivity_test.py` 分工不同：后者诊断"连不连得通"，前者采集"连通后返回什么字段"），提交入库，在交付说明中明确告知用户"本环境未能采集到完整字段结构，已将探测脚本留在 `_verify/`，需要用户在其网络环境下运行并回报结果"，**不得**凭本环境的失败结果就跳过归一化实现或编造字段结构。
- 若本轮构建时探测成功，正常记录完整字段清单供 39.2 编码使用，并在步骤 42 一并补记入 `project-docs/buildlog.md`。

**39.2 工具实现（基于 39.1 补测结果编码，以下为待补测确认的骨架，字段名以补测结果为准调整）**
```python
@server.tool()
async def dblp_publication_search_by_query(query: str, max_results: int = 10) -> dict:
    """Search dblp (computer science bibliography) by keyword. dblp itself requires
    no API key. NOTE: dblp.org has been observed to fail intermittently due to
    network path variance (TLS handshake failures, occasional HTTP 500) in some
    network environments — this reflects network conditions, not a bug in this
    tool or dblp being down. If you see a connection error here, retrying later or
    from a different network is often sufficient."""
    normalized_query = query.strip()
    if not normalized_query:
        return _err(query=query, message="query must not be empty")
    bounded = max(1, min(max_results, 25))
    try:
        return await _search_dblp(query=normalized_query, max_results=bounded)
    except Exception as exc:
        # dblp is known to fail intermittently for network reasons (see README/
        # buildlog for QA-R013 background); surface that context in the error
        # rather than a bare exception string, to avoid this being misread as a
        # code bug on retry.
        return _err(
            query=normalized_query,
            message=f"{exc}（dblp.org 可能因网络环境波动间歇性失败，非必然故障；建议稍后重试或更换网络环境）",
        )
```
- `_search_dblp()` 内部函数：请求 `dblp.org/search/publ/api`，`q` 参数为关键词，`format=json`，`h` 参数控制返回条数（对应 `max_results`）；归一化字段以 39.1 补测结果为准。
- **错误提示文案设计**（回应 `goal.md` QA-R013"建议在该数据源的工具实现和/或文档中向用户说明这一特性"的要求）：本步骤采用"在 `_err` 的 `message` 中追加固定提示文本"的方式，而非更复杂的方案（如自动重试+退避）——理由：(1) 自动重试会增加平均响应延迟且不保证解决问题（三次实测中有一次是应用层 500，重试可能有效，但另一次是 TLS 握手失败，短时间内重试大概率仍失败）；(2) 项目现有工具均无自行实现的重试机制（`arxiv` 库内置重试是第三方库自带能力，非本项目模式），新增重试逻辑会让 dblp 模块与其余数据源风格不一致；(3) 清晰的错误文案已足以让用户/LLM 客户端理解"这不是需要报 bug 的情况"，符合 `goal.md` 原文"可能需要标注强调"的表述程度，未要求实现自动容错机制。

#### 验证方法
- 39.1 的字段结构补测记录完整、可直接用于编码，或已按流程把探测脚本产出到 `_verify/` 交用户补充。
- 真实调用 `dblp_publication_search_by_query(query="graph")`（复用 QA-R013 用户实测时使用的关键词，便于比对结果一致性），若本环境网络可达，确认返回 `ok: true` 且 `items` 为逐字段结构；若本环境网络不可达，确认走 `_err` 分支且错误信息包含"网络环境波动"提示文案，而非未捕获异常导致进程崩溃。
- 空查询调用确认走 `_err`（`query must not be empty`），不透传给 API。

#### 风险提示
- 这是本轮唯一一个"实现前置探测本身就可能失败"的数据源，`project-builder-cn` 需要有心理预期：即便严格执行 39.1 的补测流程，本环境仍可能因网络原因无法采集到字段结构，此时应遵循 `_verify/` 流程约束而非强行编造字段结构继续往下走。
- 若最终因本环境网络原因导致 39.1 补测彻底失败、无法拿到任何真实字段样本，`project-builder-cn` 可以参考 dblp 官方 API 文档的字段说明作为**临时占位实现**，但必须在 buildlog.md 与工具 docstring 中**明确标注"字段结构来自官方文档字面描述，尚未经过本项目真实抓包验证，待用户在可达网络环境下验证后可能需要调整"**，不得将其表述为已验证的真实结构——这是本项目"真实验证优先"原则在探测彻底受阻情况下的最低限度妥协，且必须显式留痕，不能悄悄降级为"看起来验证过"。

---

### 步骤 40：更新 `src/uniarticles/sources/__init__.py`，注册全部 12 个新数据源

#### 目标说明
步骤 35～39 完成后，12 个新数据源模块均已具备 `register(server)` 函数，但尚未被 `register_all_sources()` 调用，实际不会出现在 MCP 工具列表中。本步骤按步骤 34.4 已定案的分组顺序统一接入。

#### 具体操作
```python
from mcp.server.fastmcp import FastMCP

from .scopus import register as register_scopus_source
from .sciencedirect import register as register_sciencedirect_source
from .arxiv import register as register_arxiv_source
from .paperscraper import register as register_paperscraper_source
from .openalex import register as register_openalex_source
from .crossref import register as register_crossref_source
from .europepmc import register as register_europepmc_source
from .doaj import register as register_doaj_source
from .zenodo import register as register_zenodo_source
from .hal import register as register_hal_source
from .openaire import register as register_openaire_source
from .semantic_scholar import register as register_semantic_scholar_source
from .core import register as register_core_source
from .dblp import register as register_dblp_source
from .biorxiv import register as register_biorxiv_source
from .chembl import register as register_chembl_source


def register_all_sources(server: FastMCP) -> None:
    # v2.x 既有数据源（Elsevier 全家桶 + arXiv + PubMed）
    register_scopus_source(server)
    register_sciencedirect_source(server)
    register_arxiv_source(server)
    register_paperscraper_source(server)
    # v3.0.0 新增：通用检索型（标准 query 关键词检索模式）
    register_openalex_source(server)
    register_crossref_source(server)
    register_europepmc_source(server)
    register_doaj_source(server)
    register_zenodo_source(server)
    register_hal_source(server)
    register_openaire_source(server)
    register_semantic_scholar_source(server)  # 无 SEMANTIC_SCHOLAR_API_KEY 时不注册任何工具
    register_core_source(server)
    register_dblp_source(server)
    # v3.0.0 新增：语义特殊型（非关键词检索）
    register_biorxiv_source(server)  # 浏览语义（server/start_date/end_date/cursor）
    register_chembl_source(server)   # DOI 必填查询语义
```
文件名/模块名与步骤 35～39 中各数据源实际落地的文件名保持一致，若实现阶段文件名与本计划书草拟的不同（例如 `europepmc.py` 改成了 `europe_pmc.py`），以实际文件名为准同步调整 import 语句，不强行拘泥于本计划书的命名。

#### 验证方法
- 启动服务，通过 MCP 工具枚举，确认：(a) 当前环境（无 `SEMANTIC_SCHOLAR_API_KEY`）下，v2.x 既有 12 个工具 + 10 个新数据源工具（OpenAlex 2 + Crossref 2 + Europe PMC 1 + DOAJ 1 + Zenodo 1 + HAL 1 + OpenAIRE 1 + CORE 1 + dblp 1，Semantic Scholar 0 因无 key、bioRxiv/medRxiv 1 + ChEMBL 1）均正常出现；(b) 顺序符合步骤 34.4 定案的分组顺序。
- 精确统计当前环境下 MCP Server 实际注册的工具总数，供步骤 41/42 中 README 陈述引用（具体总数以实际统计为准，不在本步骤预先假定，因为 Semantic Scholar 的注册与否取决于当时环境是否已配置 key，需要如实反映实际环境状态或明确注明"视 Semantic Scholar key 是否配置而定"）。

#### 风险提示
- 若某个数据源模块在步骤 35～39 实现时文件名/函数名与本步骤预设的 import 语句不一致，会导致 `ImportError`，构建时需仔细核对每个 `from .xxx import register as register_xxx_source` 与实际文件是否匹配。
- 12 个新 `register_xxx_source(server)` 调用顺序本身不影响功能正确性（各数据源相互独立），但为保持与 README 工具清单描述顺序一致，建议不要在后续维护中随意打乱本步骤确定的顺序。

---

### 步骤 41：README.md / README_ZH.md 全量更新 + `pyproject.toml` 版本号提升至 3.0.0（收尾）

#### 目标说明
延续本计划书"v3.0.0 范围补充"小节已确定的收尾策略——README 与版本号**不**跟随每批次更新，只在全部数据源实现完毕后统一执行一次。本步骤是 v3.0.0 全部代码改动完成后的收口动作。

#### 具体操作
1. **`## Available Tools`/`## 可用工具列表` 章节**：新增 12 个数据源对应的工具条目（Semantic Scholar 的 2 个工具需注明"仅在配置 `SEMANTIC_SCHOLAR_API_KEY` 时注册"；CORE 的 1 个工具注明"建议配置 `CORE_API_KEY` 以获得完整体验"；bioRxiv/medRxiv 的工具注明"按日期区间浏览，非关键词检索"；ChEMBL 的工具注明"`doi` 必填，非关键词检索"；dblp 的工具注明"可能因网络环境波动间歇性失败"）。中英文同步。
2. **`## Features`/`## 功能特性` 章节**：补充新数据源覆盖说明，可按"通用学术检索"（OpenAlex/Crossref/Europe PMC/DOAJ/Zenodo/HAL/OpenAIRE/dblp/Semantic Scholar/CORE）与"专项数据源"（bioRxiv/medRxiv 预印本浏览、ChEMBL 药物化学关联数据）分组描述，避免逐一罗列 12 行导致该章节过于冗长。
3. **Elsevier Key 说明章节的工具计数核实与修正**（`README.md`/`README_ZH.md` 现均为第 31 行）：现文案 `"Verified against the current 12 tools using a real non-commercial key."` / `"该结论已用真实的非商业 Key 对当前全部 12 个工具做过实测验证。"`。**构建时需先核实这句话的真实语义范围**——它字面上紧跟在 Elsevier Key 说明段落之后，理论上应特指"已用非商业 Elsevier key 验证过的 Elsevier 相关工具数"，但历次版本（v2.1.0→v2.2.0→v2.3.0，11→10→12）该数字恰好始终与"MCP Server 实际注册工具总数"精确相等（因为此前全部工具确实都是 Elsevier/arXiv/PubMed，全部工具都受同一枚 Elsevier key 影响验证范围），从未真正需要区分过这两个概念。v3.0.0 是第一次出现"新增工具与 Elsevier key 完全无关"的情况，需要按核实结果处理：
   - 若核实确认这句话历史上就是"全部工具数"的口语化表达 → 需要拆成两句话：一句延续"MCP Server 当前共注册 N 个工具，覆盖 M 个数据源"（全局计数），另一句保留"其中 Elsevier 相关的 6 个工具已用真实非商业 key 验证"（不受本轮影响，数量不变）。
   - 若核实确认这句话本来就应严格限定为 Elsevier 范围 → 维持原语义，只需确认数字仍为 12（Elsevier 工具本身数量未变），另在文档其他位置（如简介/徽章，若存在）新增一处独立的全局工具总数陈述。
   - **无论采用哪种处理方式，全局工具总数陈述都必须明确标注"若未配置 `SEMANTIC_SCHOLAR_API_KEY`，Semantic Scholar 相关工具不会出现，总数为 21；配置后为 22"**（Elsevier 6 + arXiv 3 + PubMed 1 + 本轮新增 11 个不含 Semantic Scholar 的固定工具 + Semantic Scholar 视 key 而定的 0/2 个），不得用单一固定数字掩盖这一条件性。核实结论需记入 buildlog.md（步骤 42）。
4. `.env.example` 新增步骤 34.3 确定的两行环境变量说明。
5. `pyproject.toml` 第 7 行 `version = "2.3.0"` → 改为 `version = "3.0.0"`（`goal.md` QA-R010 已明确目标版本号）。

#### 验证方法
- 全文检索确认 12 个新数据源的工具名均出现在 `Available Tools` 章节，中英文对等。
- 工具总数陈述（无论最终以何种形式呈现）与步骤 40 验证方法中实际统计的数字一致，且明确区分"Semantic Scholar key 已配置/未配置"两种情况下的数字差异。
- `python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"` 输出 `3.0.0`。

#### 风险提示
- 第 31 行"12 个工具"的语义核实是本步骤最容易出错的一处，务必按"具体操作"第 3 条列出的两种可能情形分别处理，不强行套用本计划书的推测，以实际核实结论为准。
- Semantic Scholar 的条件注册特性使得"总工具数"不再是固定值，这是本项目历史上第一次出现"工具数量取决于运行环境配置"的情况，README 措辞需要清晰处理这一新情况，不能简单照抄此前版本"精确固定数字"的写法。

---

### 步骤 42：`project-docs/buildlog.md` 记录本轮变更 + 整体回归验证（检查点）

#### 目标说明
记录步骤 34～41 的完整实现过程，并做一次覆盖全部数据源（v2.x 既有 4 个文件 12 个工具 + v3.0.0 新增 12 个数据源）的整体回归验证，确认 v3.0.0 全部范围（12 个确认落地数据源 + arXiv 补 `doi` 字段，PMC 排除）已完整交付，MCP 协议层未受影响。这是 v3.0.0 的最终交付检查点。

#### 具体操作
1. 在 `project-docs/buildlog.md` 的 `## v3.0.0 构建记录` 章节内（步骤 33 记录之后）新增本轮记录，逐条包含：
   - 步骤 34 的架构决策摘要（Semantic Scholar 条件注册 vs CORE 不条件注册的理由、`Settings` 新增字段、`register_all_sources()` 分组方式）。
   - 步骤 35～39 每个数据源的最终参数签名、归一化字段清单（若步骤 39 dblp 因网络原因未能在本环境完成补测，如实记录"字段结构待用户在 `_verify/` 下补充验证"这一状态，不得记录为已完成）。
   - 步骤 40 的 `register_all_sources()` 最终顺序。
   - 步骤 41 的 README/pyproject 修改摘要（含第 31 行语义核实结论）。
   - 版本号变更：`2.3.0` → `3.0.0`。
   - **v3.0.0 全轮范围收尾小结**：13 个立项候选的最终结果——12 个确认落地并完成实现（OpenAlex/Crossref/Europe PMC/DOAJ/Zenodo/HAL/OpenAIRE/bioRxiv·medRxiv/ChEMBL/Semantic Scholar/CORE/dblp）+ 1 个排除（PMC）+ arXiv 补 `doi` 字段独立完成，与 `goal.md` QA-R013 记录的范围现状完全对应。
2. 整体回归验证：
   - 用 `uv run uniarticles-mcp` 或 `python -m uniarticles` 启动服务，确认进程正常启动，`stdout` 未被污染（12 个新数据源模块均为本轮新增代码，是污染风险最集中的一批改动）。
   - 若条件允许，在真实 Claude Desktop/Cherry Studio 中实际加载一次，确认工具列表数量与步骤 41 陈述的数字一致（含 Semantic Scholar 条件注册导致的数量差异）。
   - 用真实网络环境手动调用全部新增工具各至少 1 次（含 dblp、Semantic Scholar 视 key 配置情况），确认均正常返回 `ok: true` 或结构清晰的 `_err`。
   - 用真实 `.env`（`ELSEVIER_API_KEY`）手动调用现有 12 个 v2.x 工具中至少覆盖 4 个数据源各 1 个，确认未因本轮改动（尤其 `config.py` 新增字段、`sources/__init__.py` 改动）产生回归。

#### 验证方法
- buildlog.md 中能找到本轮全部数据源的最终参数签名与归一化字段记录，dblp 若未完成补测需有明确的"待用户验证"标注，不得含糊带过。
- 整体回归验证的 4 项操作均通过，无 `ImportError`/`NameError`/未捕获异常。
- v3.0.0 全轮范围与 `goal.md` QA-R013 记录的最终范围（12 落地 + 1 排除 + 1 独立增强）完全对应，无遗漏无多算。

#### 风险提示
- 本轮改动是本项目至今单轮新增代码量最大的一次（12 个新文件 + `config.py`/`sources/__init__.py`/README×2/`pyproject.toml` 改动），回归验证不能因为"每个数据源本身都不复杂"而简化整体验证覆盖面，尤其要重点验证 `config.py` 新增字段与现有 `elsevier_api_key`/`elsevier_insttoken` 字段共存不冲突（`Settings` 是 `frozen=True` dataclass，新增字段若书写不当可能影响整个类的实例化）。
- 若 dblp 在本轮构建环境中始终未能完成字段结构补测（39.1 反复受阻），v3.0.0 不应因此被无限期拖延——可以先用官方文档字面描述的字段结构完成一版"待验证"实现（步骤 39 风险提示已允许这一妥协路径），正常收口本轮版本发布，待用户后续在可达网络环境下验证后再补一轮小版本修正，不必让整个 v3.0.0 卡在单个数据源的网络可达性问题上。

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

---

- （v3.0.0，2026-08-04）步骤 27～33 基于 `project-docs/goal.md` QA-R010/QA-R011 追加，源自用户调研本地参考项目 `reference-projects/paper-search-mcp-main/`、`reference-projects/research-superpower-main/` 后确认的、本项目至今规模最大的一轮范围：11 个通用检索型新数据源（Semantic Scholar/OpenAlex/Crossref/PMC/Europe PMC/DOAJ/CORE/Zenodo/HAL/dblp/OpenAIRE）+ 2 个语义特殊新数据源（bioRxiv/medRxiv 浏览语义、ChEMBL DOI 查询语义）+ 1 个现有工具增强（arXiv 三工具补 `doi` 字段），合计 13 个数据源/功能点，目标版本号 `3.0.0`（用户主动跳过原规划中尚未启动的 v2.4.0，原 QA-R009 已作废并被 `git revert`）。鉴于规模空前，本计划书**未**沿用此前几轮"一次性列完所有步骤"的组织方式，而是分四阶段组织：① 步骤 27（arXiv `doi` 字段，独立低风险，可立即执行，不依赖后续阶段）；② 步骤 28～32（13 个候选的真实 API 探测，含步骤 28 的统一方法论总纲 + 4 个探测批次，按置信度/类型分组：批次一为 3 个推荐重点候选，批次二/三为 8 个中等价值候选，单独一步覆盖 bioRxiv/medRxiv+ChEMBL 两个语义特殊候选）；③ 步骤 33（探测结果汇总+范围二次确认检查点，遵循 `goal.md` 已定的止损规则——技术不可行直接排除、技术可行但价值存疑必须交还用户判断，不得由 `project-planner-cn`/`project-builder-cn` 自行拍板）；④ 分批实现阶段（步骤 34 及以后，具体步骤数量与内容待步骤 33 探测结果与可能的用户二次确认完成后，由 `project-planner-cn` 在后续会话中追加，本轮**不**预先编造尚未经真实验证的实现细节）。步骤 1～26（v2.0/v2.1.0/v2.2.0/v2.3.0 构建）已全部执行完毕并发布，保留在文档中作为历史记录，不受本轮改动影响。
- **收尾文档更新策略**（`goal.md` 未指定，本计划书在"v3.0.0 范围补充"小节中给出方案并说明理由）：`project-docs/buildlog.md` 跟随每个探测/实现阶段或批次增量更新，避免长战线执行中途中断（例如步骤 33 交还用户判断后迟迟未获回复）导致已完成工作无落盘记录；`README.md`/`README_ZH.md` 与 `pyproject.toml` 版本号则**不**跟随每批次更新，只在最终实现清单确定且全部已确认数据源均落地完毕后统一执行一次，避免中间状态的 README 出现"这批做完了但还有候选没测完"的模糊表述，也避免引入本项目此前从未使用过的预发布版本号管理方式。
- **ChEMBL（`doi` 必填查询语义）与 bioRxiv/medRxiv（分类+时间窗口浏览语义）** 在步骤 32 中已被有意与其余 9 个通用检索候选的探测方式区分对待，探测脚本与记录用词均需避免先入为主地套用"关键词检索"假设，为后续实现阶段的参数签名设计（`doi` 必填 / `server`+`start`+`end`+`cursor`，均不提供 `query` 关键词参数）预先埋下依据，避免实现阶段与其余通用检索型数据源的设计模式混淆。
- **止损规则是本轮范围收敛的核心机制，贯穿步骤 28～33**：技术上确认不可行的候选可由 `project-builder-cn` 直接排除、无需二次确认用户（比照 `goal.md` QA-R002 先例）；但技术上可行、只是价值存疑（字段稀疏/需自行申请 key/限流严格/与现有数据源重叠）的候选，任何执行者都**不得**自行拍板剔除或纳入，必须整理成清晰的对比材料交还用户做最终判断——这一规则已在步骤 28、31（OpenAIRE 稳定性判定）、33 中反复强调，因为它是全轮最容易被无意间"图省事"违反的一条要求。

---

- （v3.0.0 分批实现阶段，2026-08-05）步骤 34～42 基于 `project-docs/goal.md` QA-R012/QA-R013 追加。步骤 33 交还用户裁决的 4 项候选已逐一定案：**Semantic Scholar 纳入**（key 申请中，需按 key 条件注册）、**PMC 排除**（与现有 `pubmed_paper_search_by_query` 同源 NCBI E-utilities，无稳定性增量）、**CORE 纳入**（key 已配置在 `.env`）、**dblp 纳入**（三轮网络环境实测确认服务端可用，记录已知的间歇性网络失败风险）。v3.0.0 最终确认落地 **12 个数据源**：OpenAlex、Crossref、Europe PMC、DOAJ、Zenodo、HAL、OpenAIRE、bioRxiv/medRxiv、ChEMBL、Semantic Scholar、CORE、dblp。
- 步骤 34 是本轮唯一的"公共规范"步骤，正式落地两项此前留给本计划书自行判断的架构决策：**Semantic Scholar 采用"无 key 不注册工具"的条件注册模式（模块级，非细粒度），CORE 不采用**（无 key 时 CORE 仍可有限使用，Semantic Scholar 无 key 时核心检索确定性失败，二者处理方式不同的判断标准已在步骤 34.2 中明确记录，供未来同类决策复用）；`register_all_sources()` 采用"v2.x 既有 / v3.0.0 通用检索型 / v3.0.0 语义特殊型"三段分组。
- 步骤 35～39 按**实现复杂度与代码结构共性**分批（区别于步骤 29～32 按"探测优先级"分批）：批次一（步骤 35）OpenAlex/Crossref/Europe PMC/DOAJ 为标准两件套模式；批次二（步骤 36）Zenodo/HAL/OpenAIRE 各有一个需要额外处理的结构性特点（资源类型过滤/Solr 字段选择/深层嵌套响应）；批次三（步骤 37）Semantic Scholar/CORE 集中处理条件注册架构；批次四（步骤 38）bioRxiv/medRxiv/ChEMBL 保持与其余 10 个通用检索源不同的参数模式；dblp（步骤 39）单列，因其真实字段结构尚未完整采集，编码前需先做一次补测（若本环境网络仍不可达，按 `goal.md` QA-R013 新增的 `_verify/` 流程约束处理，不得凭本环境失败结果下结论或编造字段）。
- 步骤 40～42 为收尾：`register_all_sources()` 统一接入（步骤 40）→ README/`pyproject.toml` 版本号统一更新至 `3.0.0`（步骤 41，延续本计划书此前确定的"全部落地后统一更新"策略，并特别标注 Semantic Scholar 条件注册导致"总工具数视 key 配置而定"这一本项目历史上首次出现的情况）→ buildlog 记录 + 整体回归验证检查点（步骤 42，v3.0.0 最终交付节点）。
- 步骤 1～33（v2.0/v2.1.0/v2.2.0/v2.3.0 构建 + v3.0.0 探测阶段）已全部执行完毕，保留在文档中作为历史记录，不受本轮改动影响。
