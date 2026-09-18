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

### v3.1.0 范围补充（QA-R014/QA-R015，2026-08-07）

v3.0.0 已在 QA-R013 全部定案发布（当前 `pyproject.toml` 版本号 `3.0.0`）。本轮范围源自用户重启此前作废的 QA-R009（2026-08-04，v2.4.0 调研）遗留决策点——"PubMed 检索改为直连 NCBI Entrez API"，经 QA-R014（范围对应方案C/新能力是否一并纳入/`NCBI_API_KEY` 注册模式）与 QA-R015（命名/字段对等性/版本号）两轮问答，`goal.md` 已完整闭环，无遗留待定事项。

**本轮性质：重构 + 新增混合，且是一次用户已知情并接受的破坏性变更**，与此前 v2.3.0/v3.0.0（纯新增）不同，反而更接近 v2.2.0（QA-R004）"无过渡期破坏性变更"的先例——但范围窄得多，只涉及一个数据源模块：

1. **重写**：现有 `pubmed_paper_search_by_query`（工具名不变）底层由"调用第三方包 `paperscraper`（内部依赖 `pymed_paperscraper`）"改为"直接 `httpx` 调用 NCBI 官方 Entrez `esearch.fcgi` + `efetch.fcgi`，自行解析返回 XML"。
2. **改名**（破坏性，无过渡期，比照 v2.2.0 先例处理）：源码文件 `src/uniarticles/sources/paperscraper.py` → `pubmed.py`；`sources/__init__.py` 中 `register_paperscraper_source` → `register_pubmed_source`；`CLAUDE.md`/`README.md`/`README_ZH.md`/`project-docs/teach.md` 中对该文件名/函数名的引用同步更新；`_ok`/`_err` 硬编码写入 JSON 响应体的 `"source"` 字段值从 `"paperscraper"` 改为 `"pubmed"`（面向调用方可见的行为变化，用户已明确接受，无需设计兼容层或新旧字段值并存）。
3. **新增 3 个独立工具**（同批交付，非独立评估，工具总数由当前 25/27 增至 **28/30**）：

| 工具名（本计划书拟定，方案 A 命名风格） | 状态 | 对接端点 | 拟定参数 |
|---|---|---|---|
| `pubmed_paper_search_by_query` | 重写（工具名不变，仅底层实现与 `source` 字段值变化） | `esearch.fcgi` + `efetch.fcgi` | `query: str`, `max_results: int = 10` |
| `pubmed_paper_summary_lookup_by_pmids` | 新增 | `esummary.fcgi` | `pmids: list[str]` |
| `pubmed_related_article_search_by_pmid` | 新增 | `elink.fcgi`（`cmd=neighbor`） | `pmid: str`, `max_results: int = 10` |
| `pubmed_pmc_linkage_lookup_by_pmid` | 新增 | `elink.fcgi`（`dbfrom=pubmed&db=pmc`） | `pmid: str` |

   **命名说明**：延续项目既定"数据源_对象_动作(_by_限定词)"风格，与 `chembl_bioactivity_lookup_by_doi`（单值查询用 `_lookup_by_`）、`dblp_publication_search_by_query`/`biorxiv_paper_list_by_date_range`（列表类结果用 `_search_by_`/`_list_by_`）等既有命名保持同构：ESummary 是"给一批 PMID、查一批轻量元数据"的批量查找，故用 `summary_lookup_by_pmids`；ELink neighbor 返回的是"检索出的相关文献列表"，语义更接近搜索而非单值查找，故用 `related_article_search_by_pmid`；ELink PMC 关联查询是"给一个 PMID、查它在 PMC 的单一关联结果（内含两组子信息）"，故用 `pmc_linkage_lookup_by_pmid`。以上命名为本计划书拟定，非不可更改的最终方案——`project-builder-cn` 若在真实探测（步骤 43）后认为有更贴切的命名，可以调整，但须说明理由并保持方案 A 风格不变（同 v2.3.0 先例的处理方式）。

4. **新增可选环境变量 `NCBI_API_KEY`**，采用**无条件注册模式**（对齐 Elsevier/CORE 先例）：不管是否配置该 key，全部 4 个 pubmed 相关工具均注册；配置了 key 时请求带上该参数，NCBI 官方限速从 3 请求/秒提升到 10 请求/秒；未配置时仍可正常使用。**与 Semantic Scholar 的条件注册模式明确区分**：Semantic Scholar 无 key 时确定性失败（实测 429），故 QA-R012 引入"无 key 不注册工具"；NCBI 官方 Entrez API 无 key 也完全可用、只是限速更严，不满足"确定性失败"的条件，因此本轮不扩大条件注册模式的适用范围，用户已在 QA-R014 明确选择维持无条件注册（`goal.md` 约束条件已记录这一区分依据）。用户确认 key 已配置在 `.env` 的 `NCBI_API_KEY` 变量中，具备真实验证条件。
5. **字段归一化不预先规定**：重写后的检索工具与 3 个新工具的返回字段集合，均按 `project-builder-cn` 真实探测 NCBI 各端点返回结构（EFetch 为 XML，ESummary/ELink 通常可用 `retmode=json`）后如实确定，不强制与现有 `paperscraper` 输出字段一一对齐，允许有增有减——延续本项目"先探测再定字段，不凭空编字段"的一贯做法（同 QA-R006 对 `get_abstract_details`/`retrieve_article`、QA-R007/QA-R008 对 `serial_title_search`/`subject_classifications` 归一化任务的处理方式）。
6. **依赖移除**：`pyproject.toml`/`uv.lock` 中的 `paperscraper` 依赖声明彻底移除；`pymed-paperscraper` 从未作为直接依赖出现在 `pyproject.toml`（是 `paperscraper` 拉入的传递依赖），随 `paperscraper` 移除、`uv lock` 重新生成锁文件后会自动一并清除，无需单独处理。**本计划书新增一项 `goal.md` 未逐字提及、但经代码核实后应一并处理的衍生决策**（比照 v2.1.0 步骤 8"清理 `ARXIV_DOWNLOAD_DIR` 死配置"先例，在此明确标注来源，避免被误认为超出授权范围或临场发挥）：`pandas>=2.0.0` 这条依赖经全仓库检索确认**仅被 `paperscraper.py` 一处引用**（`_to_items()` 用于把 `paperscraper` 返回的 `pd.DataFrame` 转成 `list[dict]`），本项目其余任何模块均未使用 `pandas`；重写后的 `pubmed.py` 自行解析 XML/JSON，不再需要 `pandas`，因此建议**一并从 `pyproject.toml` 移除 `pandas` 依赖**，减少不必要的依赖体积（这也是本轮"依赖精简"这一原始动机的一部分，见 `goal.md` 背景与动机）。
7. **正式实现前必须先做真实 API 复测**：`goal.md`（QA-R014/约束条件）明确指出，本轮大量决策依据已作废的 QA-R009 探测结论（ESummary/ELink 三项候选端点实测 200 可用、无需 Key），但探测发生在数日之前，且本计划书截稿时仍未对 ESearch/EFetch 做过字段级真实抓包（此前 `paperscraper.py` 的间接实现从未暴露过 EFetch 原始 XML 结构）。因此本计划书将"真实复测"列为独立的强制前置步骤（步骤 43），比照 `_verify/dblp_field_probe.py` 的既有模式，覆盖 ESearch/EFetch/ESummary/ELink（neighbor）/ELink（PMC）共 5 个真实请求，产出诊断脚本到 `_verify/`（`goal.md` QA-R013 已确立的通用流程约束——不得仅凭 agent 自身探测环境的单次结果下结论）。

**目标版本号 `3.1.0`**（当前 `pyproject.toml` 为 `3.0.0`），工具总数由 25 个（或配置 `SEMANTIC_SCHOLAR_API_KEY` 时 27 个）增至 **28 个（或 30 个）**，README.md/README_ZH.md 的工具清单/计数与文件名引用需同步更新。

**本计划书组织的步骤 43～52**：
- 步骤 43：NCBI 5 个端点真实复测（编码前置探测，产出脚本到 `_verify/`）。
- 步骤 44：`config.py` 新增 `NCBI_API_KEY` + `pubmed.py` 公共骨架（`_ok`/`_err`/公共请求参数/限速处理策略）。
- 步骤 45：重写检索工具 `pubmed_paper_search_by_query`（ESearch+EFetch，XML 解析）。
- 步骤 46：新增 `pubmed_paper_summary_lookup_by_pmids`（ESummary）。
- 步骤 47：新增 `pubmed_related_article_search_by_pmid`（ELink neighbor）。
- 步骤 48：新增 `pubmed_pmc_linkage_lookup_by_pmid`（ELink PMC）。
- 步骤 49：`sources/__init__.py` 接入改名 + 移除 `paperscraper`/`pandas` 依赖（含需用户确认的 `uv` 命令）+ 确认无遗留引用。
- 步骤 50：文档同步更新（README.md/README_ZH.md/CLAUDE.md/`project-docs/teach.md`）。
- 步骤 51：`pyproject.toml` 版本号提升至 `3.1.0`。
- 步骤 52：`project-docs/buildlog.md` 记录本轮变更 + 整体回归验证（v3.1.0 最终交付检查点）。

步骤 1～42（v2.0～v3.0.0 构建）已全部执行完毕并发布，保留在文档中作为历史记录，不受本轮改动影响。

### v3.3.0 范围补充（QA-R017，2026-09-18）

v3.2.0 已在 QA-R016 定案发布（本轮改动前基线：`pyproject.toml` 版本号 `3.2.0`、14 个数据源、默认 26 个工具、配置 `SEMANTIC_SCHOLAR_API_KEY` 时 28 个工具）。本轮范围源自用户"当前文献源有些太多了"的范围收缩意向，经 QA-R017 一轮澄清问答（判定标准）加一轮全量实测（14 个源 24 次真实调用 + 3 篇已知文献的定向检索矩阵）闭合。**用户决策（QA-R017 逐字记录）：采用方案 A，并额外移除 Zenodo。**

**本轮性质：范围收缩型破坏性变更，但排除依据与 v3.2.0 不同，必须严格区分。** v3.2.0 的 ChEMBL/HAL 属"产品价值收窄"（两者均已实测可用，本轮不否定该历史结论）；本轮三个源分属三类依据，`goal.md` QA-R017 已明确要求不得混写：

| 源（模块） | 被删工具 | 排除性质 | 判据来源 |
| --- | --- | --- | --- |
| bioRxiv / medRxiv（`biorxiv.py`） | `biorxiv_paper_list_by_date_range` | 上游 API **结构性不支持定向检索**（本集合唯一一例：上游无关键词检索，只能按 `server` + 日期窗口 + `cursor` 浏览、固定 30 条/次） | QA-R017 定向检索矩阵"结构性无法定向检索"一档 |
| dblp（`dblp.py`） | `dblp_publication_search_by_query` | **可连接性不达标**（本机实测 0/4：HTTP 429 + 连接被重置 + 非 JSON 响应） | QA-R017 连通性全量实测；性质与 QA-R013 记录的间歇性不可达一致，按该条既定流程规则此记录**不构成**"技术不可行"结论 |
| Zenodo（`zenodo.py`） | `zenodo_record_search_by_query` | **检索形态重复造成的工具干扰**（差异化内容——数据集/软件——已因 `type=publication` 硬过滤而放弃，剩余记录与 OpenAlex/Crossref 重叠） | QA-R017 判定标准①"工具干扰" + 定向检索矩阵命中 1/3 |

三者均**不属于** QA-R003（权限受限，401/超时）与 QA-R012（技术不可行，PMC）的排除性质。

**收缩后规模**：

- 数据源 **14 → 11**（默认激活 13 → 10；Semantic Scholar 为条件注册，不计入默认集合）
- 工具 **26 → 23**（配置 `SEMANTIC_SCHOLAR_API_KEY` 时 **28 → 25**）
- 源码减少 280 行（`biorxiv.py` 91 + `dblp.py` 113 + `zenodo.py` 76，占源文件总量 2137 行的 13.1%；行数已逐一核对）
- 工具名称+描述合计约 7041 → 5662 字符（-19.6%，据 QA-R017 实测）
- "关键词检索型"工具由 12 个降至 10 个（减少 dblp、zenodo 两个；biorxiv 本就不属该形态）——这是"工具干扰"这一主要困扰的直接下降量

**保留的 11 个源各有不可替代角色**（本轮不因删源而降低定向检索能力）：Scopus（受控索引 + 引用数 + 期刊元数据 + 学科分类代码）、ScienceDirect（全库唯一提供图表/补充材料清单；注意它没有任何检索工具）、arXiv、PubMed（MeSH + 相关文献 + PMC 关联）、OpenAlex、Crossref、Europe PMC（定向检索 3/3 命中，且提供 PubMed 缺失的引用数与预印本覆盖）、DOAJ、OpenAIRE、CORE、Semantic Scholar（条件注册）。

**未纳入本轮的两项（`goal.md` QA-R017 明确记录，本计划书不得默认其为已授权）**：

1. **三处默认排序修复**（`scopus.py` 默认排序改相关性、`pubmed.py` 显式传 `sort=relevance`、评估 `arxiv.py` 硬编码的 `SubmittedDate`）——用户本轮未表态，QA-R017 记录为"默认不纳入"。这是用户回答 1 后半句"部分工具无法直接检索到特定文献"的直接病根，本计划书以"候选步骤 59/60"形式预置（默认不执行），待用户确认后按既有"增量追加步骤"方式启用。
2. **版本号**——QA-R017 记录建议 `3.3.0`（比照 QA-R016 先例），但**需用户在构建计划书阶段确认**；本计划书按 `3.3.0` 拟制步骤 57，并在该步骤标注确认门禁。

**本计划书组织的步骤 54～58**：

- 步骤 54：删除三个源文件与 `sources/__init__.py` 中的注册引用（代码层）。
- 步骤 55：`README.md` / `README_ZH.md` 全量同步（计数下修 + 三个源小节删除）。
- 步骤 56：`AGENTS.md` / `CLAUDE.md` 两份 agent 指导文件同步（含两文件的未跟踪/被忽略状态说明）。
- 步骤 57：版本号提升至 `3.3.0`（**待用户确认**）。
- 步骤 58：`project-docs/buildlog.md` 记录本轮变更 + 整体回归验证（v3.3.0 交付检查点）。
- 候选步骤 59/60（默认不纳入）：三处默认排序修复的真实探测与实施。

步骤 1～53（v2.0～v3.2.0 构建）已全部执行完毕并发布，保留在文档中作为历史记录，不受本轮改动影响。

### v3.5.0 范围补充（QA-R021，2026-09-19）

v3.4.0 已发布（当前 `pyproject.toml` 版本号 `3.4.0`，基线状态：**9 个数据源 / 21 个工具**，全部无条件注册、无任何配置相关的工具数变化）。本轮范围源自用户要求"详细了解 CORE 官方 API 文档，还有什么功能可以加入到这个 MCP server"，经 `project-docs/goal.md` 附录《CORE API v3 能力盘点（QA-R021 前置调研，2026-09-18）》双线调研（文档站 + OpenAPI 规范 `https://api.core.ac.uk/swagger/v3.json`）加 `.env` 真实 `CORE_API_KEY` 的真实端点探测，再经 QA-R021 三轮问答与会后复测定案。

**本轮是 CORE 单数据源的能力扩展（新增 + 既有工具增强），不是新增数据源，也不是范围收缩。** 数据源集合保持 9 个不变，全部工具仍无条件注册。用户决策（QA-R021 逐字记录）：

1. **范围档位 = (c) 档**：在 (a) 现有工具检索质量增强、(b) works 维度新工具之上，再新增"聚合统计 + 机构库维度"工具。**期刊维度确认不纳入**（`/v3/journals/issn:{issn}` 实测返回 200 但只有回显式空壳记录：无刊名、出版商为 `null`、`dataProviderId` 为空串，不提供任何产品语义所需信息；`/v3/search/journals` 累计 4 次超时）。
2. **"文件内容 / 下载"边界不破例**：维持项目既有硬边界——只返回元数据与链接，不取回文件本体、不返回原始全文、不下载二进制。`/v3/works/{id}/download`、`/v3/works/tei/{id}`、`/v3/outputs/{id}/download|raw|history` **全部不接入**。
3. **验证节奏**：复测脚本已产出并经由第三个环境复测通过（见下），闸门已由用户"key 既然有效就不用管，开始更新计划书"解除，实现范围锁定为 C 档 9 项。

**C 档最终范围 = 1 个现有工具增强 + 8 个新增工具**（工具名沿用 `goal.md` 候选名并按本项目 `<source>_<object>_<action>_by_<axis>` 命名风格复核，结论见步骤 69；最终命名仍由 `project-builder-cn` 在真实探测后确认，如调整须说明理由）：

| # | 工具 | 端点 | 语义 | 状态 |
|---|---|---|---|---|
| 1 | `core_work_search_by_query` | `POST /v3/search/works` | 现有工具增强：`limit` 上限 25 → 100、新增 `offset` 分页、改用 POST + `exclude:["fullText"]`、429 文案改为按响应头给出可执行重试时间 | 增强（非新增） |
| 2 | `core_work_detail_by_identifier` | `GET /v3/works/{identifier}` | 按**裸 DOI 或数字 CORE ID** 取单篇作品详情 | 新增 |
| 3 | `core_work_outputs_by_id` | `GET /v3/works/{id}/outputs` | 该作品在各机构库的版本实例列表（含 `downloadUrl`/`license`/`fulltextStatus`/`dataProvider`） | 新增，**只接受数字 CORE ID** |
| 4 | `core_work_stats_by_id` | `GET /v3/works/{id}/stats` | 生命周期时间戳（deposited / published / updated / accepted） | 新增，DOI 亦可 |
| 5 | `core_work_aggregate_by_query` | `POST /v3/search/works/aggregate` | 按年 / 作者 / 机构 / 类型 / 期刊 / 语言 / 出版社分布统计（项目工具集中**首个 facet / 分布维度**） | 新增 |
| 6 | `core_data_provider_search_by_query` | `GET /v3/search/data-providers` | 机构库 / 期刊源检索 | 新增 |
| 7 | `core_data_provider_detail_by_id` | `GET /v3/data-providers/{id}`（含 `/stats`、`/outputs`） | 机构库详情、统计与其下 outputs（"works → 机构库画像"链路端到端实测通过） | 新增 |
| 8 | `core_output_detail_by_id` | `GET /v3/outputs/{id}` | 未去重的原始采集记录（`license`/`sdg`/`repositories`/`fulltextStatus` 等） | 新增，无条件纳入 |
| 9 | `core_output_search_by_query` | `GET /v3/search/outputs` | outputs 关键词检索 | **条件纳入** |

**第 9 项的条件纳入与击杀条件**：该端点历史上在 creator 环境两次 HTTP 500（上游 Azure Search 报 `Invalid expression: The operand for a binary operator 'Equal' is not a single value`），而在另一环境四种组合 4/4 全 200；第三个环境的复测中三种查询组合（普通关键词 / `title:` 字段限定 / DOI 精确命中）**再次全部 200**，累计 **7 次连续 200、跨 2 个环境**。据此本计划书支持纳入，但保留击杀条件——**实现期探测（步骤 69）或用户自行复测只要出现任何一次非 200，则该工具不纳入**，其余 8 项完全不受影响（此时工具总数为 27 而非 28）。

**顺带更正项（属修既有缺陷，实现阶段一并处理；`goal.md` 未逐字要求版本号，但由 QA-R021 明确要求更正）**：

- `src/uniarticles/sources/core.py` 的模块注释与 429 错误文案、以及 `AGENTS.md` 关于 CORE 限流的表述（"无 key 约 5 次请求后约 10 分钟锁死"），与 CORE 官方现行 token 制口径不符（未认证 100 tokens/天、10 次/分钟且**不提供 `fullText`**；注册个人 1,000 tokens/天、25 次/分钟），须改为按响应头 `X-RateLimit-Limit` / `X-RateLimit-Remaining` / `X-RateLimit-Retry-After` 给出可执行重试时间（该头实测为 **ISO 时间戳**而非秒数）。
- 官方文档入口 `https://api.core.ac.uk/docs` 实测 404，正确入口是 `https://api.core.ac.uk/docs/v3`，机器可读规范在 `https://api.core.ac.uk/swagger/v3.json`——仓库内如有引用需一并更正。

**规模与版本号**：

- 数据源 **9 个不变**；工具由 **21 → 27 个**（不含条件第 9 项）/ **28 个**（含之）。CORE 单源工具数由 1 → 8 或 9。
- 本轮**纯增量**：不删除、不重命名、不改动其余 8 个数据源现有的 20 个工具的名称/参数/返回结构/注册顺序（增强的 `core_work_search_by_query` 工具名与返回结构也保持不变，仅新增可选参数并放宽 `max_results` 上限）。
- 目标版本号 **`3.5.0`**（当前 `3.4.0`）。**该版本号由 `goal.md` 标注为"默认值、未获用户逐字确认"**，比照 v3.2.0 步骤 53 先例：若用户另有指定，只需替换 `pyproject.toml` 与 `src/uniarticles/__init__.py` 两处字面值。
- `project-docs/teach.md` 按用户既有指示**不更新**（已滞后多轮，属已知失真，非本轮缺陷）。

**本计划书组织的步骤 69～77**：

- 步骤 69：CORE v3 新端点与响应字段真实探测（编码前置，产出 `_verify/core_api_field_probe.py`）。
- 步骤 70：`core.py` 公共骨架重构（标识符解析、限流头解析、单条/多条响应构造、公共请求入口）。
- 步骤 71：增强现有工具 `core_work_search_by_query`（POST + `exclude` + `offset` + 上限 100 + 可执行 429 文案）。
- 步骤 72：新增 `core_work_detail_by_identifier` / `core_work_outputs_by_id` / `core_work_stats_by_id`（works 维度 3 项）。
- 步骤 73（编号顺延说明见该步骤）：新增 `core_work_aggregate_by_query`（聚合统计维度）。
- 步骤 74：新增 `core_data_provider_search_by_query` / `core_data_provider_detail_by_id` / `core_output_detail_by_id`（机构库 + output 详情维度）。
- 步骤 75：新增 `core_output_search_by_query`（条件纳入，含击杀条件与回退处理）。
- 步骤 76：文档同步（`README.md` / `README_EN.md` / `AGENTS.md` / `_verify/tool_availability_check.py` + 限流与文档入口口径更正）。
- 步骤 77：版本号提升至 `3.5.0` + `buildlog.md` 记录 + 整体回归验证（v3.5.0 交付检查点）。

步骤 1～68（v2.0～v3.4.0 构建，含已发布的 v3.4.0）已全部执行完毕并发布，保留在文档中作为历史记录，不受本轮改动影响。

## 可行性分析

**v3.5.0 增补（CORE 扩展，2026-09-19）**：本轮不引入任何新技术栈或新依赖——8 个新增工具全部复用 `core.py` 现有的 `httpx.AsyncClient` + `_ok`/`_err` + `@server.tool()` 模式，端点可用性已由三轮真实探测（两个环境、共 7 次连续 200）与官方 OpenAPI 规范交叉确认，技术可行性无阻断项。风险集中在三处，均已在步骤 69～77 中给出应对：(1) `POST /v3/search/works/aggregate` 的**请求体 schema 从未在真实探测中覆盖**（现有 `_verify/core_api_probe.py` 未含该端点），故把真实探测列为强制前置步骤 69；(2) CORE 响应对非 JSON 错误体、空 `message` 的 404、以及 ISO 时间戳格式的重试头都不友好，需在归一化层统一兜底；(3) 工具数由 21 增至 27/28，与本项目 v3.2.0–v3.4.0 的收缩趋势相反，但新增维度（facet 分布、机构库画像）不与现有任何源重叠，属**新查询维度**而非"又一个关键词检索源"，已在范围小节中记录该判断依据。

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

### 步骤 43：NCBI 5 个端点真实复测（编码前置探测，产出脚本到 `_verify/`）

#### 目标说明
`goal.md` 明确要求：本轮大量决策依据已作废的 QA-R009 探测结论，但探测发生在数日之前，且从未对 ESearch/EFetch 的真实响应结构做过字段级抓包（现有 `paperscraper.py` 是对第三方包的间接调用，从未直接看过 NCBI 原始响应）。按本项目一贯的"真实验证优先"方法论（同 QA-R001/QA-R002/QA-R007/QA-R013 的处理方式）及 QA-R013 新增的通用流程约束（验证脚本必须产出到 `_verify/` 供用户独立验证，不得仅凭 agent 自身探测环境的单次结果下结论），本步骤是步骤 44～48 编码工作的强制前置步骤，不得跳过直接编写归一化代码。

#### 具体操作
1. 在 `_verify/` 目录下新增 `pubmed_eutils_field_probe.py`，比照 `_verify/dblp_field_probe.py` 的既有模式：standalone、仅用标准库（`urllib.request`/`xml.etree.ElementTree`/`json`），不依赖项目自身代码或第三方包，可独立运行、只读、不改任何文件。
2. 脚本依次对以下 5 个真实端点各发起一次请求（统一 base：`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`），选用一个已知存在的真实 PMID 作为样本（建议用第 1 步 ESearch 返回的第一个真实命中 PMID，而非硬编码猜测的 PMID，避免样本本身不存在导致后续 4 个端点全部空转）：
   - `esearch.fcgi?db=pubmed&term=<query>&retmax=5&retmode=json`：确认返回 `esearchresult.idlist` 结构与真实字段名。
   - `efetch.fcgi?db=pubmed&id=<pmid>&rettype=abstract&retmode=xml`：**逐层打印完整 XML 树结构**（标签路径、每个候选归一化字段的真实出现次数）——比照 `dblp.py` 中"单作者是 dict、多作者是 list"的陷阱，PubMed XML 里 `AuthorList/Author`/`KeywordList/Keyword`/`MeshHeadingList/MeshHeading` 等列表型标签虽然 `ElementTree.findall()` 恒返回 `list`（不存在 JSON 那种 dict/list 二义性），但存在"整个列表标签缺失"（如机构统一署名、无关键词的老文献）这一容易被忽视的边界情况，脚本输出需明确标注。
   - `esummary.fcgi?db=pubmed&id=<pmid>&retmode=json`：打印完整 JSON 结构，重点核对 `goal.md` 提到的"PMCID/PII/期刊全名/发表状态历史"等字段的真实键名。
   - `elink.fcgi?dbfrom=pubmed&db=pubmed&id=<pmid>&cmd=neighbor&retmode=json`：打印 `linksets[].linksetdbs[].links[]` 真实结构，确认是否带 score/权重字段。
   - `elink.fcgi?dbfrom=pubmed&db=pmc&id=<pmid>&retmode=json`：打印返回结构，确认"该文献自身在 PMC 有无全文"与"哪些 PMC 文章引用/关联了它"分别对应哪个 `linkname`/字段路径（`goal.md` 描述这是两种不同信息，需要脚本输出中明确区分，具体 `linkname` 取值不得凭记忆硬编码）。
3. 脚本应支持可选传入 `NCBI_API_KEY`（读取环境变量 `NCBI_API_KEY`，若已在本机 shell 中设置则自动带上 `&api_key=`；未设置则跳过），对 ESearch 分别测一次带 key、一次不带 key，对比响应是否有可观察差异；若 NCBI 未在响应体中明确标注实际生效的限速值，应如实记录"无法从响应体直接验证限速差异，仅能确认两种调用方式均返回 200"，不得编造观测不到的结论。
4. 脚本输出建议复用 `_verify/dblp_field_probe.py` 的 `_print()`/IPv4 脱敏封装风格（保持项目 `_verify/` 脚本的一致性），并在结尾提示用户"请把完整输出复制反馈"。
5. 用 `git add -f _verify/pubmed_eutils_field_probe.py` 强制添加（`CLAUDE.md` 已记录：本机 `.gitignore` 有未提交改动会排除 `_verify/`，不要动用户待处理的 `.gitignore` 改动）。
6. 若本环境探测部分/全部失败（网络类失败），按 QA-R013 通用流程约束处理：如实记录失败现象，不据此直接判定端点不可用，把脚本留在 `_verify/` 交用户在其网络环境下运行验证，步骤 44 之后的编码工作可以先按 QA-R009 历史结论 + NCBI 官方文档字面描述的字段结构起草一版，并显式标注"待用户真实验证反馈确认"（比照步骤 39 dblp 允许的妥协路径）。

#### 验证方法
- 脚本能独立运行（`python _verify/pubmed_eutils_field_probe.py`），无需安装项目本身或额外第三方包。
- 5 个端点的真实响应结构（或如实记录的失败现象）已被完整捕获并可供后续步骤引用，不存在"跳过探测直接假设字段名"的情况。
- 若本环境探测成功，产出物应包含至少一条真实、完整的 EFetch XML 样例（供步骤 45 编写解析逻辑的直接依据）。

#### 风险提示
- **PubMed EFetch XML 的真正陷阱不是"单值/列表二义性"（`ElementTree.findall()` 类型稳定），而是"标签整体缺失"**：`AbstractText` 可能被拆成多个带 `Label`/`NlmCategory` 属性的结构化分段、`ArticleTitle` 可能内嵌斜体/上下标子标签（需 `.itertext()` 而非 `.text`）、`AuthorList` 可能整体缺失或退化为 `CollectiveName`（机构作者），这些都需要在探测脚本输出中如实呈现，而不是假设"标准结构总是存在"。
- 若探测环境完全无法访问 `eutils.ncbi.nlm.nih.gov`（网络拦截/DNS 问题），不得直接得出"NCBI 端点不可用"的结论——比照 dblp 先例，记录现象、留脚本给用户，不擅自 downgrade 或跳过后续步骤。
- 样本 PMID 若选取到已撤稿（retracted）或非常规文献类型（书籍章节、临床试验注册记录等），字段结构可能与常规期刊论文有差异；建议额外用 1～2 篇结构简单的常规期刊论文样本交叉验证，避免归一化方案被单一样本的特殊性带偏。

---

### 步骤 44：`config.py` 新增 `NCBI_API_KEY` + `pubmed.py` 公共骨架

#### 目标说明
落地 `goal.md` 已确认的无条件注册模式（对齐 Elsevier/CORE 先例），并为步骤 45～48 的 4 个工具准备好共享的请求参数构造、认证注入、`_ok`/`_err` 统一结构等公共代码，避免 4 个工具各自重复实现。

#### 具体操作
1. `src/uniarticles/config.py`：在 `Settings` frozen dataclass 中新增字段，写法对齐现有 `core_api_key`（同为"无条件注册、缺 key 仅限速更严"语义，不对齐 `semantic_scholar_api_key` 的"缺 key 不注册"语义）：
   ```python
   ncbi_api_key: str | None = field(default_factory=lambda: os.getenv("NCBI_API_KEY"))
   ```
2. 新建 `src/uniarticles/sources/pubmed.py`（先建骨架，具体检索/新工具逻辑在步骤 45～48 中补充），包含：
   - `BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"`
   - `USER_AGENT`，风格对齐现有模块（如 `dblp.py`/`core.py` 的 `UniArticlesMCP/3.0.0 (...)`，随步骤 51 版本号最终确定后统一核对回填，不要在骨架阶段硬编码后忘记同步）。
   - `_ok(query, items)`/`_err(query, message)`，`source="pubmed"`（对应本轮破坏性变更后的新值）。
   - `_params(extra: dict) -> dict`：公共参数注入函数，统一处理 `db=pubmed`、`tool=uniarticles-mcp`、`email`（NCBI 官方礼仪建议提供 `tool`/`email` 标识调用方，非强制但被官方文档推荐，`email` 可用 `pyproject.toml` 现有作者邮箱或省略，由 `project-builder-cn` 决定）、以及 `settings.ncbi_api_key`（若已配置则注入 `api_key` 参数）。
   - 限速处理策略（**明确不做客户端主动节流，理由需写入代码注释**）：本项目其余数据源模块均未实现请求速率限制（如 `core.py` 只在收到 429 时通过 `_err` 把限流上下文原样返回给调用方），NCBI 的限速是"每秒请求数"级别的服务端策略，而单次 MCP 工具调用通常只触发 1～2 个 HTTP 请求；因此本轮同样采用"不主动节流、429 时按 `core.py` 先例把限速上下文清晰返回"的策略，不引入令牌桶/滑动窗口等主动限速机制，避免为低概率场景引入不必要的复杂度。若步骤 52 整体回归验证中真实观察到 429，再按需补充节流逻辑，不预先过度设计。
3. 该步骤只搭骨架、不实现 `register()` 内的具体工具，`sources/__init__.py` 的接入改动放到步骤 49（避免中间态破坏现有 `paperscraper_source` 的可运行状态）。

#### 验证方法
- `Settings()` 能正常实例化，`settings.ncbi_api_key` 在 `.env` 已配置 `NCBI_API_KEY` 时能正确读到真实值（用一次性 `python -c "from uniarticles.config import settings; print(bool(settings.ncbi_api_key))"` 验证，不打印真实 key 值本身）。
- `pubmed.py` 骨架代码能被正常 import，不因尚未实现 `register()` 内容而报错（`register()` 函数体可暂时留空或 `pass`，供步骤 45 起逐步填充）。

#### 风险提示
- `Settings` 是 `frozen=True` dataclass，新增字段需使用 `field(default_factory=...)` 写法（与 `core_api_key`/`semantic_scholar_api_key` 一致），不要误用直接赋值写法（会在类定义时立即求值，与其他 v3.0.0 新增字段的风格不统一）。
- 骨架阶段不要提前把 `pubmed.py` 加入 `sources/__init__.py` 的 import——此时 `register()` 还未实现完整工具，若中途因步骤 45～48 分批提交，提前接入会导致 `register_all_sources()` 调用一个空/半成品的 `register()`，MCP Server 实际可用工具数与预期不符，容易造成中间态混乱。

---

### 步骤 45：重写检索工具 `pubmed_paper_search_by_query`（ESearch + EFetch，XML 解析）

#### 目标说明
落地 `goal.md` 核心目标 7/23、方案 C：现有 `pubmed_paper_search_by_query` 工具名不变，但底层实现从"调用第三方包 `paperscraper`"改为"直接 `httpx` 调用 `esearch.fcgi` 检索 PMID 列表 + `efetch.fcgi` 按 PMID 批量拉取 XML 并自行解析"，`source` 字段值同步改为 `"pubmed"`。这是本轮范围内改动量最大、也是唯一涉及 XML 解析的一步——本项目此前所有数据源模块均只处理 JSON 响应，这是本项目第一次需要解析 XML，需额外谨慎。

#### 具体操作
1. 用 `git mv src/uniarticles/sources/paperscraper.py src/uniarticles/sources/pubmed.py`（若步骤 44 已直接新建 `pubmed.py`，改为直接删除旧的 `paperscraper.py`，保留新文件；两种做法二选一，`project-builder-cn` 按实际操作顺序选择，结果一致即可）。
2. 实现 `_esearch(query: str, retmax: int) -> list[str]`：
   ```python
   async def _esearch(query: str, retmax: int) -> list[str]:
       async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
           response = await client.get(
               f"{BASE_URL}esearch.fcgi",
               params=_params({"term": query, "retmax": retmax, "retmode": "json"}),
           )
           response.raise_for_status()
           payload = response.json()
       return payload.get("esearchresult", {}).get("idlist", []) or []
   ```
   保留现有实现已有的 `max_results` clamp 逻辑（`[1, 9998]`，对应 NCBI ESearch 官方单次最多取回 9999 条的限制），命名与既有代码风格一致。
3. 实现 `_efetch(pmids: list[str]) -> list[dict]`，用标准库 `xml.etree.ElementTree` 解析（**不引入新依赖**，`ElementTree` 是 Python 标准库，符合本项目一贯"能用标准库/现有依赖就不额外引入新包"的偏好）：
   ```python
   import xml.etree.ElementTree as ET

   async def _efetch(pmids: list[str]) -> list[dict]:
       async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
           response = await client.get(
               f"{BASE_URL}efetch.fcgi",
               params=_params({"id": ",".join(pmids), "rettype": "abstract", "retmode": "xml"}),
           )
           response.raise_for_status()
       root = ET.fromstring(response.text)
       return [_normalize_article(el) for el in root.findall(".//PubmedArticle")]
   ```
4. `_normalize_article(el: ET.Element) -> dict`：**具体字段与路径以步骤 43 真实探测结果为准**，此处仅给出以 NCBI 官方文档字面描述、待步骤 43 确认/修正的起点（比照 `dblp.py` 中"文档记载但未经真实抓包确认"字段的注释处理方式，明确标注哪些是已确认、哪些待确认）：
   - `pmid`：`.//PMID`（注意 `ArticleIdList` 下也可能有一个 `IdType="pubmed"` 的 `ArticleId`，与顶层 `PMID` 标签是否总是一致，需步骤 43 确认）。
   - `title`：`.//ArticleTitle`（内容可能包含内嵌斜体/上下标等子标签，需用 `"".join(el.itertext())` 而非 `.text` 直接取值，避免截断）。
   - `abstract`：`.//Abstract/AbstractText`（**注意结构化摘要**——部分文献的摘要被拆成多个带 `Label`/`NlmCategory` 属性的 `AbstractText` 分段，如 `BACKGROUND`/`METHODS`/`RESULTS`/`CONCLUSIONS`，需要拼接而非只取第一个）。
   - `authors`：`.//AuthorList/Author`，每个作者取 `LastName`+`ForeName`（或 `CollectiveName` 用于机构作者，需判空处理）。
   - `journal`：`.//Journal/Title` 或 `.//Journal/ISOAbbreviation`。
   - `doi`：`.//ArticleIdList/ArticleId[@IdType='doi']`。
   - `publication_date`：`.//Article/ArticleDate` 或 `.//Journal/JournalIssue/PubDate`（字段完整性不一，很多历史文献只有年份，需容错到"年-月-日均可选"）。
   - `keywords`：`.//KeywordList/Keyword`。
   - 现有 `paperscraper` 输出还含 `methods`/`conclusions`/`results`/`copyrights` 等字段——这些实际来自结构化摘要的分段标签（`Label="METHODS"` 等），**不强制保留**（`goal.md` 已明确允许有增有减），若步骤 43 探测确认这些分段有稳定的 `Label` 属性，可选择性保留为独立字段，否则合并进统一的 `abstract` 字段即可，由 `project-builder-cn` 视真实探测结果决定，不在计划书中预先拍板。
5. `register()` 内工具签名/校验逻辑基本保持现有 `paperscraper.py` 风格不变（`query.strip()`、`max_results` clamp、空 query 报错），仅内部改为调用 `_esearch`+`_efetch` 并处理"ESearch 返回 0 个 PMID"这一正常空结果场景（返回 `ok: true`、`items: []`，不是错误）。

#### 验证方法
- 用真实存在的关键词（如 `"CRISPR"`）调用 `pubmed_paper_search_by_query`，确认 `ok: true`，`items` 中字段为真实解析值（非空、非硬编码占位），`source` 字段值为 `"pubmed"`（不是 `"paperscraper"`）。
- 用一个几乎不可能命中的生僻关键词组合，确认 ESearch 返回 0 条时走的是正常空结果分支而非误判为错误。
- 对比同一关键词在改造前（`paperscraper.py`）与改造后的返回条数量级是否合理（不要求完全一致，因为两者检索语法/排序可能有差异，但不应出现数量级失真，如改造后始终只返回 1 条）。
- 用一个已知有多位作者的真实 PMID 抽查 `authors` 字段是否完整解析出全部作者。

#### 风险提示
- **本项目首次引入 XML 解析，`ElementTree` 对命名空间/HTML 实体等边界情况的处理需格外小心**：PubMed XML 中偶见 HTML 实体转义（如 `&amp;`）与内嵌斜体标签（`<i>`/`<sup>`/`<sub>`），直接用 `.text` 只取第一段纯文本会丢失后续内容，务必用 `.itertext()` 拼接完整文本。
- **`AuthorList`/`KeywordList` 等列表型标签"整个标签缺失"是真实存在的边界情况**（如无关键词的老文献、机构统一署名的文献），必须用 `.find(...) is not None` 判空，不能假设标签总存在。
- ESearch/EFetch 是两次独立请求，中间若 ESearch 成功但 EFetch 因 PMID 列表过长/网络问题失败，需在 `_err` 中如实说明是哪一步失败，不要笼统报错让调用方无法定位问题。
- 这是一次面向已发布工具的破坏性变更：**任何硬编码依赖旧 `source: "paperscraper"` 字段值做逻辑判断的外部调用方/工作流会在本版本发布后失效**，比照 `goal.md` 约束条件已记录的"无过渡期"处理方式，不在代码层面做兼容判断，但应在步骤 50 的文档更新与步骤 52 的 buildlog 记录中显著提示这一变化，方便用户对外通知自己的下游调用方。

---

### 步骤 46：新增 `pubmed_paper_summary_lookup_by_pmids`（ESummary 批量元数据）

#### 目标说明
接入 `esummary.fcgi`，对应 `goal.md` 核心目标 24：比 EFetch 更轻量，含 PMCID/PII/期刊全名/发表状态历史等现有实现没有的字段，给定一批 PMID 批量取回。

#### 具体操作
1. 参数设计：`pmids: list[str]`（也可设计为逗号分隔字符串，但 `list[str]` 更符合 MCP 工具入参的类型清晰度；FastMCP 对 `list[str]` 类型有原生支持，但与本项目其余工具入参多为标量字符串不同，属于本轮新引入的参数类型，构建时需确认真实 MCP 客户端环境下的兼容性，见风险提示）。
2. 输入校验：去重、过滤空值，限制批量数量上限（NCBI 官方文档建议 GET 方式不超过约 200 个 ID，超出建议改用 POST；本步骤先按 GET + 上限 200 实现，超出上限截断并在返回结果中提示，不做自动分批递归请求这种更复杂的方案，除非步骤 43 探测发现 200 这个数字需要调整）。
3. 实现 `_esummary(pmids: list[str]) -> list[dict]`：
   ```python
   async def _esummary(pmids: list[str]) -> list[dict]:
       async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
           response = await client.get(
               f"{BASE_URL}esummary.fcgi",
               params=_params({"id": ",".join(pmids), "retmode": "json"}),
           )
           response.raise_for_status()
           payload = response.json()
       result = payload.get("result", {})
       uids = result.get("uids", []) or []
       return [result[uid] for uid in uids if uid in result]
   ```
4. 归一化字段：**待步骤 43 真实探测确认**，起点参考 `goal.md` 已提及的 `pmcid`（若有 PMC 全文）、`elocationid`（含 PII 信息）、`fulljournalname`、`pubstatus`（发表状态，如 epublish/ppublish）等；建议同时保留 `title`/`authors`（ESummary 的 `authors` 通常是 `[{"name": "...", ...}]` 结构，与 EFetch 的 `LastName`+`ForeName` 拆分不同，归一化时统一成本项目习惯的字符串数组或 `{name}` 字典数组，与步骤 45 的 `authors` 字段形态保持跨工具一致，便于调用方复用解析逻辑）。
5. 对不存在的 PMID：ESummary 通常会在 `result.uids` 中省略该 ID 或在对应键下返回一个错误结构，需真实探测确认后按"部分成功、跳过无效 ID 并在 items 中体现"的方式处理，不要因为批量请求中混入 1 个无效 ID 就让整个调用失败。

#### 验证方法
- 用真实存在的 1 个 PMID、以及一批（如 5 个）真实 PMID 分别调用，确认批量场景下 `items` 数量与请求的有效 PMID 数量一致。
- 混入 1 个明显不存在的 PMID（如 `"1"`），确认不会导致整个请求失败，能正常返回其余有效 PMID 的结果并对无效 ID 做出清晰说明。
- 抽查返回字段确实包含现有 EFetch 实现没有的信息（如 `pmcid`），验证"ESummary 更轻量但字段有差异化价值"这一 `goal.md` 立项依据成立。

#### 风险提示
- FastMCP 对 `list[str]` 类型入参的 JSON Schema 生成与实际客户端（Cherry Studio 等）传参兼容性此前未在本项目验证过（其余 25 个工具入参均为标量），若真实客户端环境下 `list[str]` 传参存在兼容性问题，需考虑退化为逗号分隔字符串入参（`pmids: str`，内部 `.split(",")`）这一更保守的方案，构建时应两种方案都验证一次，不要只测试通过 Python 直接调用（那不能反映真实 MCP 客户端的参数编解码行为）。
- 批量请求的部分失败处理若设计不当，容易让调用方误以为"整批都失败了"或"缺失的 PMID 被静默忽略而不自知"，归一化时应在返回结构中明确标注哪些请求的 PMID 未返回结果。

---

### 步骤 47：新增 `pubmed_related_article_search_by_pmid`（ELink 相关文献查询）

#### 目标说明
接入 `elink.fcgi`（`cmd=neighbor`），对应 `goal.md` 核心目标 24：给定 PMID，返回主题相关的其他 PubMed 文献 PMID 列表。

#### 具体操作
1. 参数：`pmid: str`（单值，与 `chembl_bioactivity_lookup_by_doi` 单值查询的参数模式一致）、`max_results: int = 10`（ELink neighbor 官方接口本身不提供 limit 参数，返回全部相关结果，需要客户端侧对结果做切片。**这里的"客户端侧切片"与 QA-R004 明确禁止的"`list_papers` 客户端侧二次过滤"性质不同**——后者是本该由服务端按分类过滤、却被错误地实现成客户端全量拉取后过滤，属于实现偷懒；这里是服务端本身不支持分页/限量参数、只能返回全部结果，客户端侧截断只是为了控制返回给 LLM 的结果体积，不构成对既有先例的违反）。
2. 实现：
   ```python
   async def _related(pmid: str, max_results: int) -> list[dict]:
       async with httpx.AsyncClient(timeout=30.0, headers=_headers()) as client:
           response = await client.get(
               f"{BASE_URL}elink.fcgi",
               params=_params({"dbfrom": "pubmed", "db": "pubmed", "id": pmid, "cmd": "neighbor", "retmode": "json"}),
           )
           response.raise_for_status()
           payload = response.json()
       linksets = payload.get("linksets", []) or []
       # 具体 key 路径（linksetdbs[].links[].id/score）待步骤 43 真实探测确认
       items = [...]
       return items[:max_results]
   ```
3. 归一化输出：至少含相关文献的 `pmid`（可能还有 `score`，若步骤 43 探测确认该字段真实存在）；不在本工具内自动对每个相关 PMID 再发起 EFetch/ESummary 请求补全标题等信息（避免 1 次调用放大成 N+1 次请求，若用户需要相关文献的详细信息，应再调用 `pubmed_paper_summary_lookup_by_pmids`，工具之间保持职责单一，这与 `get_article_objects`"只给元信息链接、不做二次下载"的既有产品原则一致）。

#### 验证方法
- 用一个真实存在且有一定引用/主题关联度的 PMID 调用，确认返回非空的相关 PMID 列表。
- 用一个几乎没有关联文献的冷门 PMID（如非常新/非常小众的文献）调用，确认空结果走的是 `ok: true`、`items: []` 而非误判为错误。
- `max_results` 切片逻辑正确（请求 5 条时最多返回 5 条，即使服务端实际返回更多）。

#### 风险提示
- 若步骤 43 探测发现 `linksets` 结构本身可能为空列表（该 PMID 暂无 NCBI 计算出的相关文献，这是正常情况非错误），归一化逻辑需要能区分"结构缺失/字段路径变化导致的解析失败"与"结构完整但确实没有相关结果"两种情况，不要把后者误判成前者从而返回一个掩盖真实解析问题的假"空结果"。
- 命名用 `_search` 而非 `_lookup`：因为结果本质是一个列表（多条相关文献），与 ChEMBL"给一个 DOI 查一条收录记录"的单值语义不同；若后续真实探测发现该端点本质更接近"关联关系图谱查询"而非"检索"，命名可在步骤 43 后调整，需说明理由。

---

### 步骤 48：新增 `pubmed_pmc_linkage_lookup_by_pmid`（ELink PMC 全文/引用关联查询）

#### 目标说明
接入 `elink.fcgi`（`dbfrom=pubmed&db=pmc`），对应 `goal.md` 核心目标 24：给定 PMID，返回该文献在 PMC 是否有开放获取全文、以及哪些 PMC 文章引用/关联了它——这是两种不同性质的信息（"这篇文献本身的 PMC 全文"vs"引用/关联它的其他 PMC 文章"），归一化时需要在返回结构中明确区分，不能混为一谈。

#### 具体操作
1. 参数：`pmid: str`（单值，命名与语义同 `chembl_bioactivity_lookup_by_doi` 一致——"给一个已知标识符，查它的一条关联信息记录"）。
2. 实现思路：ELink 支持在同一次 `dbfrom=pubmed&db=pmc` 请求中通过不同 `linkname`（如该文献自身的 PMC 全文对应一种 `linkname`，引用它的 PMC 文章对应另一种 `linkname`，**确切取值需步骤 43 真实探测确认，不得凭 NCBI 文档记忆直接硬编码**）区分这两种关联，返回结构中应有清晰分组，例如：
   ```python
   {
       "own_pmc_fulltext": [...],       # 该文献自身若被 PMC 收录，对应的 PMC ID
       "cited_by_pmc_articles": [...],  # 引用/关联它的其他 PMC 文章
   }
   ```
   具体键名与是否需要额外的 `linkname` 参数区分，均以步骤 43 探测结果为准。
3. 若该 PMID 在 PMC 完全没有任何关联信息（既无全文也未被引用），返回 `ok: true`，两个分组均为空列表，不是错误。

#### 验证方法
- 用一个已知在 PMC 有开放获取全文的真实 PMID 调用，确认 `own_pmc_fulltext` 非空。
- 用一个已知被其他 PMC 文章引用过的真实 PMID 调用（若能找到测试样本），确认 `cited_by_pmc_articles` 非空。
- 用一个较新、大概率两类关联都还没有的 PMID 调用，确认两个分组均正常返回空列表而非报错。

#### 风险提示
- 这是本轮 4 个工具中语义最容易被简化/混淆的一个——若归一化时不小心把"自身全文"和"被引用"两组信息合并成一个扁平列表，会让调用方误判某篇文献"有开放获取全文"，实际上那条记录只是"引用了它的其他文章"，造成误导性结果，构建与验证阶段需重点覆盖这一区分逻辑。
- 与步骤 47 相同，不在本工具内自动对关联的 PMC 文章再做进一步的详情请求，保持工具职责单一。

---

### 步骤 49：`sources/__init__.py` 接入改名 + 移除 `paperscraper`/`pandas` 依赖（含需用户确认的 `uv` 命令）+ 确认无遗留引用

#### 目标说明
把步骤 44～48 完成的 `pubmed.py` 正式接入 `register_all_sources()`，同时从依赖清单中彻底移除不再需要的第三方包，并做一次全仓库检索确认没有任何其他模块/文档仍在引用旧的 `paperscraper` 相关命名——这是"重命名+依赖移除"类改动最容易遗漏、也是用户特别要求关注的风险点。

#### 具体操作
1. `src/uniarticles/sources/__init__.py`：
   ```python
   from .pubmed import register as register_pubmed_source
   ```
   替换原有 `from .paperscraper import register as register_paperscraper_source`；`register_all_sources()` 内 `register_paperscraper_source(server)` 调用改为 `register_pubmed_source(server)`，**调用位置维持在原有"v2.x 既有数据源"分组内不变**（`goal.md` QA-R014/R015 未要求调整注册顺序分组，本轮不是 QA-R006 那种顺序调整任务，不应顺带改动无关的注册顺序）。
2. `pyproject.toml` 的 `dependencies` 列表中删除 `"paperscraper"` 与 `"pandas>=2.0.0"` 两行（后者是本计划书附带确认的衍生决策，见"v3.1.0 范围补充"小节说明）。
3. **依赖变更需要用户在环境中执行以下命令确认**（涉及重新生成锁文件、修改本地 `.venv`，属于环境影响操作，`project-builder-cn` 应在执行前把以下命令原样提供给用户确认，而非静默直接跑）：
   ```powershell
   # 1. 修改 pyproject.toml 后，重新生成锁文件（会同步移除 paperscraper 及其全部传递依赖：
   #    pymed-paperscraper、scholarly、boto3、matplotlib、seaborn、matplotlib-venn 等）
   uv lock

   # 2. 按新锁文件同步本地虚拟环境
   uv sync

   # 3. 确认 paperscraper 及其传递依赖已从环境中移除（应无输出或报 "not found"）
   uv pip show paperscraper
   uv pip show pymed-paperscraper
   ```
4. 全仓库检索确认无遗留引用（`project-builder-cn` 应实际执行检索，不能仅凭"应该改完了"的印象下结论）：
   - 搜索 `paperscraper`（大小写不敏感）：预期仅剩 `project-docs/goal.md`、`project-docs/teach.md`（历史记录/需按语境判断是否需要同步，见步骤 50）、`project-docs/buildlog.md` 历史条目（如实保留，不得篡改历史记录）中出现，其余 `src/`、`README.md`、`README_ZH.md`、`CLAUDE.md`、`tutorial/` 下不应再有任何引用。
   - 搜索 `register_paperscraper_source`：应仅在 `git log` 历史中可见，当前工作区代码中不应再出现。
   - 搜索硬编码字符串 `"paperscraper"`（JSON 响应体 `source` 字段值）：应仅在 `pubmed.py` 的说明性注释（如有提及历史命名）中出现，不应再作为实际返回值出现。
5. `src/uniarticles/__init__.py` 中为压制 `paperscraper` 包 `logging.basicConfig(stream=sys.stdout, ...)` 而设的 stderr-handler-抢占防御性代码——**`goal.md` 已明确这是一个开放决策，留给 `project-builder-cn` 按代码实际情况判断，本计划书不预先规定答案**，但要求 `project-builder-cn` 在此步骤中必须显式做出选择并说明理由（二选一，均可接受）：
   - **方案一（简化）**：既然 `paperscraper` 依赖已移除，其"顶层执行 `logging.basicConfig(stream=sys.stdout, ...)`"这一根因已不存在，可以移除这段 workaround 代码及其注释，简化 `__init__.py`。
   - **方案二（保留作为通用防御）**：即便当前没有已知第三方依赖会污染 stdout，未来任何新增依赖都可能引入同样的问题（"库在 import 时抢占 root logger"这类行为并不罕见），保留这段防御性代码作为面向未来的通用防线，代价极低（约 12 行代码），仅需把注释中"根因是 paperscraper"的表述改为更通用的措辞（不再点名具体某个包）。
   - **本计划书倾向方案二**（防御性代码保留的边际成本远低于"未来某个新依赖重蹈覆辙、又要排查一次 stdout 污染"的风险，且这正是本项目从 `paperscraper` 事件中学到的教训，主动放弃这层防御没有必要的收益），但最终决定权与理由说明留给 `project-builder-cn`，并要求把选择与理由记入步骤 52 的 `buildlog.md` 记录。

#### 验证方法
- `uv run uniarticles-mcp` 能正常启动（或 `python -m uniarticles`），无 `ImportError`。
- `uv pip list` 中确认 `paperscraper`、`pymed-paperscraper`、`pandas`、`scholarly`、`boto3`、`matplotlib`、`seaborn`、`matplotlib-venn` 均已不在已安装依赖列表中（后 5 项是 `paperscraper` 的传递依赖，随之一并清除；`goal.md` 背景与动机中点名的依赖臃肿问题应在此步骤后得到实质缓解，值得在验证记录中对比移除前后的依赖数量）。
- 全仓库检索结果（步骤 4 的三项搜索）与预期一致，无意外遗漏。

#### 风险提示
- **`uv lock`/`uv sync` 是会实际修改本地 `.venv` 与 `uv.lock` 文件的环境操作**，务必按上述命令顺序执行并让用户知情，不要在用户不知情的情况下静默改动依赖环境。
- 若全仓库检索发现遗漏（例如某处文档遗漏了改名），应回头修正而不是记录为"已知遗留问题"带入下一版本——这与破坏性变更本身（用户已接受）是两回事，遗漏引用是本步骤应该发现并修复的执行质量问题，不是需要用户额外决策的产品问题。
- `matplotlib`/`seaborn`/`matplotlib-venn`/`boto3`/`scholarly` 等包体积较大，若用户本地 `.venv` 此前已下载过，`uv sync` 后磁盘空间会明显释放，属于预期中的正常现象，不是异常。

---

### 步骤 50：文档同步更新（README.md/README_ZH.md/CLAUDE.md/`project-docs/teach.md`）

#### 目标说明
`goal.md` 核心目标 26 明确要求这几处文档的引用需同步更新，避免"代码已改名但文档仍写旧名字"的落差；同时工具总数变化（25/27→28/30）需要在 README 的工具清单/计数中如实体现。

#### 具体操作
1. `README.md`/`README_ZH.md`：
   - Features/Available Tools 章节：`Available Tools` 表格新增 3 个新工具的行（工具名、简要说明、对接端点），并把现有 `pubmed_paper_search_by_query` 行的实现说明从"基于 `paperscraper`"改为"直连 NCBI Entrez API"。
   - 工具总数计数（延续 v2.2.0 步骤 17、v2.3.0 步骤 23 已发现的"计数不在表格内、容易被遗漏"这一风险点，本次同样需要专门核对）：`25 tools`/`27 tools`（视 `SEMANTIC_SCHOLAR_API_KEY` 是否配置）改为 `28 tools`/`30 tools`。
   - 环境变量配置示例（`.env`/JSON 配置片段）新增 `NCBI_API_KEY`（标注为可选，说明"提速用，缺省可用但限速更严"，与 `CORE_API_KEY` 的现有说明风格一致）。
   - 若 README 中存在提及 `paperscraper` 依赖臃肿问题的历史说明（若有），同步更新为"已移除，改为直连 NCBI API"。
2. `CLAUDE.md`：
   - "Project overview" 段落中 "PubMed (via `paperscraper`)" 改为 "PubMed (via direct NCBI Entrez API calls)"。
   - "Configuration" 段落的 `.env` 示例新增 `NCBI_API_KEY=your_ncbi_api_key   # optional — see conditional/unconditional registration note`。
   - 工具总数 "25 tools / 27 tools" 改为 "28 tools / 30 tools"。
   - "Source module pattern" 或相关段落中若有列举各数据源文件名的地方，同步把 `paperscraper.py` 改为 `pubmed.py`。
3. `project-docs/teach.md`：**注意执行分工边界**——该文档按项目既定分工由 `project-explainer-cn` 工作流独立维护，本计划书/`project-builder-cn` 通常不应跨界改写其讲解性内容；但 `goal.md` 已明确要求这一次例外同步"文件名引用"（核心目标 26 逐字列出 `project-docs/teach.md`），因此本步骤的操作范围**严格限定为**：把文档中明确指代"当前代码状态"的 `paperscraper.py`/`paperscraper` 相关字面提及替换为 `pubmed.py`/`pubmed`，**不改写其余讲解性文字、不重新组织章节结构、不补充新内容**——这是一次机械的引用同步，不是内容维护，执行完毕后应如实告知用户"teach.md 可能因本次机械同步而与 `project-explainer-cn` 下次维护时的预期略有出入，如有需要可请 `project-explainer-cn` 复核"。

#### 验证方法
- 在 README.md/README_ZH.md/CLAUDE.md 中全文检索 `paperscraper`，确认已无残留（历史 CHANGELOG/buildlog 类章节除外，那些属于历史记录不应修改）。
- README 的工具计数与 `src/uniarticles/sources/__init__.py` 实际注册的工具数量一致（可通过启动服务后实际列出工具名核对，而非仅靠人工数表格行数）。

#### 风险提示
- 与 v2.2.0/v2.3.0 步骤 17/23 同类风险：工具计数散落在正文段落中（不止 Available Tools 表格），容易漏改，需要全文搜索数字而非只改表格。
- `project-docs/teach.md` 的改动务必控制在"文件名引用替换"范围内，不得借这次机会顺带补充/重写讲解内容——这不是本步骤的授权范围，即便发现 teach.md 有其他过时之处也应留给 `project-explainer-cn` 处理，不越界代劳。

---

### 步骤 51：`pyproject.toml` 版本号提升至 `3.1.0`

#### 目标说明
`goal.md` QA-R015 已明确目标发布版本号为 `3.1.0`（当前 `3.0.0`）。

#### 具体操作
1. `pyproject.toml` 第 7 行 `version = "3.0.0"` 改为 `version = "3.1.0"`。
2. 核对 `src/uniarticles/sources/*.py` 中各模块 `USER_AGENT` 字符串里硬编码的版本号（如 `"UniArticlesMCP/3.0.0 (...)"`，目前 `dblp.py`/`chembl.py`/`biorxiv.py`/`core.py` 等模块均有此字符串），**是否需要同步改为 `3.1.0` 由 `project-builder-cn` 核实项目既往版本发布时是否有同步更新这一约定**（若历次版本发布时未同步更新过 `USER_AGENT` 里的版本号，说明这本身就不是本项目的既有约定，不必在本轮特意补上；若历次确实同步更新过，本轮也应一并更新，保持一致性）。此项为本计划书基于代码巡查发现、`goal.md` 未提及的细节点，明确标注来源避免被误认为超出授权范围。

#### 验证方法
- `pyproject.toml` 版本号确认为 `3.1.0`。
- 若决定同步更新 `USER_AGENT` 版本号，抽查 2～3 个模块文件确认已改。

#### 风险提示
- 版本号改动本身风险极低，唯一需要注意的是不要漏改（`pyproject.toml` 是唯一权威版本号来源，`src/uniarticles/__init__.py` 中若有独立的 `__version__` 字段——经查当前为 `"1.0.0"`，与 `pyproject.toml` 早已不同步，这是**本项目已存在、非本轮引入的历史不一致**，是否借此机会一并修正，超出 `goal.md` 本轮授权范围，不在本步骤处理，如实记录供用户后续单独决策，不擅自顺带修改）。

---

### 步骤 52：`project-docs/buildlog.md` 记录本轮变更 + 整体回归验证（v3.1.0 最终交付检查点）

#### 目标说明
记录步骤 43～51 的完整实现过程，并做一次覆盖全部数据源（v2.x 既有工具 + v3.0.0 新增 12 个数据源 + 本轮重写/新增的 pubmed 4 个工具）的整体回归验证，确认 v3.1.0 全部范围已完整交付、MCP 协议层未受影响、依赖精简目标达成。这是 v3.1.0 的最终交付检查点。

#### 具体操作
1. 在 `project-docs/buildlog.md` 新增 `## v3.1.0 构建记录` 章节，逐条包含：
   - 步骤 43 的真实探测结果摘要（5 个端点的真实字段结构要点，或如实记录的探测失败/待用户验证状态）。
   - 步骤 44～48 每个工具的最终参数签名、归一化字段清单、命名是否与本计划书拟定一致（如有调整需说明理由）。
   - 步骤 49 的架构决策记录：`register_all_sources()` 最终接入方式、`pandas`/`paperscraper` 依赖移除结果（含移除前后依赖数量对比）、`__init__.py` stdout 防御代码的最终处理方案与理由（步骤 49.5 二选一的最终选择）。
   - 步骤 50 的文档更新摘要。
   - 版本号变更：`3.0.0` → `3.1.0`。
   - **本轮范围收尾小结**：1 个工具重写 + 3 个新增工具 + 1 个可选环境变量 + 2 个依赖移除，工具总数由 25/27 增至 28/30，与 `goal.md` QA-R014/QA-R015 记录的范围完全对应。
2. 整体回归验证：
   - 用 `uv run uniarticles-mcp` 或 `python -m uniarticles` 启动服务，确认进程正常启动，`stdout` 未被污染（`pubmed.py` 是本轮唯一改动的模块，但依赖环境发生了较大变化——`paperscraper` 及其一大批传递依赖被移除——需确认启动过程无残留的 import 报错或路径问题）。
   - 若条件允许，在真实 Claude Desktop/Cherry Studio 中实际加载一次，确认工具列表数量与步骤 50 陈述的数字一致。
   - 用真实网络环境分别在**配置 `NCBI_API_KEY`** 与**不配置 `NCBI_API_KEY`**两种情况下各调用一遍全部 4 个 pubmed 工具，确认均正常返回 `ok: true` 或结构清晰的 `_err`，且两种配置下均可用（无条件注册模式的核心验收标准）。
   - 用真实 `.env`（`ELSEVIER_API_KEY`）随机抽查现有其余数据源中至少 3～4 个工具，确认未因本轮改动（尤其 `config.py` 新增字段、`sources/__init__.py` 改动、依赖环境变化）产生回归。
   - 确认步骤 49 的三项全仓库检索结果仍然成立（未在后续步骤中意外引入新的遗留引用）。

#### 验证方法
- buildlog.md 中能找到本轮全部改动的完整记录，探测失败/待验证项若存在需有明确标注，不得含糊带过。
- 整体回归验证的各项操作均通过，无 `ImportError`/`NameError`/未捕获异常，无 stdout 污染。
- v3.1.0 全轮范围与 `goal.md` QA-R014/QA-R015 记录的最终范围完全对应，无遗漏无多算。

#### 风险提示
- 本轮虽然只改动 1 个数据源模块，但**依赖环境的改动幅度不小**（移除 7～8 个包），整体回归验证不能因为"只是一个模块的改动"而简化验证覆盖面，尤其要重点验证依赖移除没有意外破坏其余模块（虽经检索确认 `pandas` 仅被 `paperscraper.py` 引用，但仍建议实际启动一次服务、跑一轮其余工具的抽查作为双重确认，而非只依赖静态检索结论）。
- 若步骤 43 的真实探测在构建环境中持续受阻（网络原因），比照步骤 39 dblp 先例的妥协路径：可以先用 NCBI 官方文档字面描述的字段结构完成一版"待验证"实现，正常收口本轮版本发布，待用户在可达网络环境下用 `_verify/pubmed_eutils_field_probe.py` 验证反馈后再补一轮小版本修正，不必让 v3.1.0 无限期卡在单一探测环节。
- 这是一次对已发布工具的破坏性变更（`source` 字段值变化 + 文件/函数改名），发布后应在 buildlog 中显著提示这一变化，避免用户在未察觉的情况下升级后因硬编码判断 `source == "paperscraper"` 的下游逻辑静默失效。

---

### 步骤 53：移除 ChEMBL / HAL 两个数据源 + 版本号提升至 `3.2.0`（v3.2.0，QA-R016）

#### 目标说明
`goal.md` QA-R016 已明确并确认：用户直接指令移除 ChEMBL 与 HAL 两个数据源（理由：产品价值不足，"用处不大"，非技术不可行——两者在 v3.0.0/QA-R010 纳入时均已实测确认可用，本轮不否定该历史结论）。范围小而封闭，无需分阶段/探索性调研，一步完成代码删除、验证、文档同步与版本号提升。

#### 具体操作
1. 删除源文件 `src/uniarticles/sources/chembl.py`（工具 `chembl_bioactivity_lookup_by_doi`）与 `src/uniarticles/sources/hal.py`（工具 `hal_document_search_by_query`）。
2. `src/uniarticles/sources/__init__.py`：删除对应的 2 行 import（`from .chembl import register as register_chembl_source`、`from .hal import register as register_hal_source`）与 2 行注册调用（`register_hal_source(server)`、`register_chembl_source(server)`），一并清理孤立的分组注释（原 `register_chembl_source(server)   # DOI 必填查询语义` 整行删除，不留残留注释）。
3. `README.md`/`README_ZH.md` 同步更新：总览"通用学术检索"列表中删去 HAL、"专项数据源"列表中删去 ChEMBL；数据源总数摘要段落（16→14 总数、15→13 默认激活、28→26 默认工具、30→28 含 Semantic Scholar）；数据源对比表格中删去 HAL、ChEMBL 两行；删除独立的 `### HAL`/`### ChEMBL` 工具小节（含各自工具表格）；Elsevier Key 说明段落与工具列表小节开头的工具计数摘要同步下修。
4. 版本号提升：`pyproject.toml` `version = "3.1.0"` → `"3.2.0"`；`src/uniarticles/__init__.py` `__version__ = "3.1.0"` → `"3.2.0"`（用户已在澄清中确认本轮 bump 版本号，遵循本项目"范围变更即 bump minor 版本号"的既有惯例）。
5. 各 `sources/*.py` 模块内硬编码的 `USER_AGENT` 版本号字符串（如 `"UniArticlesMCP/3.0.0 (...)"）**不做同步修改**——沿用 v3.1.0 步骤 51/buildlog 已确认的既有惯例："USER_AGENT 版本号仅在该模块被创建/重写时设为当时版本号，不存在'随发布统一同步'的约定"（v3.1.0 时仅新建的 `pubmed.py` 设为 3.1.0，其余模块仍是 3.0.0）；本轮未新建/重写任何模块，故不涉及此项改动。

#### 验证方法
- 启动 `create_server()` 并枚举工具：未配置 `SEMANTIC_SCHOLAR_API_KEY` 时应为 **13 个数据源、26 个工具**；配置后应为 **28 个工具**；工具名单中确认无 `hal_*`/`chembl_*`。
- `README.md`/`README_ZH.md` 中不再出现任何 HAL/ChEMBL 引用（含表格行、独立小节、总数摘要）。

#### 风险提示
- 这是一次对已发布工具的破坏性变更（无过渡期直接删除），发布后若有下游用户依赖 `hal_document_search_by_query`/`chembl_bioactivity_lookup_by_doi`，升级后会静默失效，应在对外发布说明中明确提示。

---

### 步骤 54：删除 `biorxiv.py` / `dblp.py` / `zenodo.py` 与 `sources/__init__.py` 中的注册引用（v3.3.0，QA-R017）

#### 目标说明
落实 QA-R017 的用户决策（方案 A + 额外移除 Zenodo），删除三个源模块，数据源 14→11、默认工具 26→23。范围小且封闭（3 个文件 + 聚合文件中的 6 行），无需分阶段或探索性调研，一步完成代码层删除，文档同步交由步骤 55/56。三个源的排除性质见"项目概述 → v3.3.0 范围补充"表格，buildlog 记录必须沿用该三分类，不得笼统写成"不可用"。

#### 具体操作
1. 删除 `src/uniarticles/sources/biorxiv.py`、`src/uniarticles/sources/dblp.py`、`src/uniarticles/sources/zenodo.py`（共 280 行，行数已核对：91 + 113 + 76）。
2. `src/uniarticles/sources/__init__.py` 删除 3 行 import：`from .zenodo import register as register_zenodo_source`、`from .dblp import register as register_dblp_source`、`from .biorxiv import register as register_biorxiv_source`。
3. 同文件 `register_all_sources()` 内删除 3 行调用：`register_zenodo_source(server)`（位于"v3.0.0 新增：通用检索型"分组内）、`register_dblp_source(server)`（该分组的最后一行）、`register_biorxiv_source(server)  # 浏览语义（server/start_date/end_date/cursor）`（单独构成"v3.0.0 新增：语义特殊型（非关键词检索）"分组）。
4. **连带清理分组注释**：删除 `register_biorxiv_source` 后，"v3.0.0 新增：语义特殊型（非关键词检索）"这一分组标题注释**整体为空**，必须连同注释一并删除，不得遗留空的分组注释块（比照步骤 53 对孤立分组注释的处理）。"通用检索型"分组删去 2 行后仍剩 7 个源（OpenAlex / Crossref / Europe PMC / DOAJ / OpenAIRE / Semantic Scholar / CORE），该分组标题保留。
5. 不改动其余 11 个源模块的任何代码，包括各模块内硬编码的 `USER_AGENT` 版本号字符串——沿用 v3.1.0 步骤 51 已确认的惯例："仅在该模块被创建/重写时设为当时版本号，不存在随发布统一同步的约定"；本轮未新建/重写任何模块，故不涉及。
6. 删除后做一次全仓库静态检索 `biorxiv|dblp|zenodo`（排除 `project-docs/`、`.venv/`、`dist/`），确认 `src/` 下已无任何指向这三个模块的 import 或调用。

#### 验证方法
- 启动 server 并枚举工具（本项目无自动化测试，沿用既有手动回归方式）：未配置 `SEMANTIC_SCHOLAR_API_KEY` 时为 **11 个数据源、23 个工具**；配置后为 **25 个工具**；工具名单中确认无 `biorxiv_*`、`dblp_*`、`zenodo_*`。
- 逐源核对注册数，**必须以实际 `list_tools()` 返回值为准**，不要用 `rg -c "@server.tool"` 的直接计数：`semantic_scholar.py` 的该字符串有 1 处出现在注释中（第 67 行），会使计数虚高 1。逐源应为 scopus 6、sciencedirect 2、arxiv 3、pubmed 4、openalex 2、crossref 2、europepmc 1、doaj 1、openaire 1、core 1、semantic_scholar 2（条件注册）。

#### 风险提示
- 破坏性变更、无过渡期：下游若硬编码了 `biorxiv_paper_list_by_date_range` / `dblp_publication_search_by_query` / `zenodo_record_search_by_query`，升级后会静默失效——buildlog 与外发说明中必须逐个列出这三个工具名（比照 v3.2.0 的处理方式）。
- `zenodo.py` 删除后，归一化响应中的 `file_links` 字段不再有任何产出方；README 与 `AGENTS.md` 中"文件元信息/链接"一类描述需同步清理，避免留下"文档描述了不存在字段来源"的失真（步骤 55/56 处理）。
- `biorxiv.py` 是本项目**唯一**非关键词检索型源，删除后"语义特殊型"这一分类在代码与文档中都不复存在；README 第 22–23 行的两条分类 bullet 会退化为一条（步骤 55），今后不得再引用该分类。
- `_verify/dblp_connectivity_test.py` 与 `_verify/dblp_field_probe.py` **保留不删**。这是本计划书的衍生决策（`goal.md` 未逐字提及），理由有三：① dblp.org 站点仍然存在，两个脚本诊断的是 DNS→TCP→TLS→HTTP 分层可达性，与"本项目是否注册 dblp 源"无关，仍具复用价值；② `AGENTS.md` 的 `_verify/` 常设流程规则把这两个脚本列为该模式的标准范例，删除会连带使该规则失去示例；③ 两脚本已按 `git add -f` 强制入库（`_verify` 在 `.gitignore` 中被忽略），删除属无必要的额外改动。只需避免新增 dblp 引用。

---

### 步骤 55：`README.md` / `README_ZH.md` 全量同步（计数下修 + 三个源小节删除）

#### 目标说明
两份 README 是项目对外门面，硬编码了数据源清单与四处工具/数据源计数，删源后必须逐处下修，且中英文两份保持结构一致。历史上计数漏改已发生两次（v2.2.0 步骤 17、v2.3.0 步骤 23，均因"计数不在表格内、位置隐蔽"），本步骤明确列出全部改动位置以免重犯。

#### 具体操作
以下行号为**改动前基线**（`README.md` 与 `README_ZH.md` 的对应位置几乎逐行对齐），实施时以内容匹配为准，删除小节后行号会整体上移。

1. **第 22 行**（功能特性 → "通用学术检索"分类 bullet）：列表中删去 `Zenodo`、`dblp`，保留 OpenAlex、Crossref、Europe PMC、DOAJ、OpenAIRE、Semantic Scholar、CORE。
2. **第 23 行**（`专项数据源（v3.0.0）: bioRxiv/medRxiv 预印本按日期区间浏览。`）：**整行删除**——该分类仅含 bioRxiv/medRxiv 一个源，删除后分类为空，不保留空 bullet。
3. **第 29 行**（"当前支持的文献数据源"总览段落）：`14 个数据源` → `11 个`、`13 个默认即启用` → `10 个`、`26 个工具` → `23 个`、配置 key 后 `28 个` → `25 个`。
4. **第 41 / 45 / 46 行**（数据源对比表格）：删除 `Zenodo`、`dblp`、`bioRxiv / medRxiv` 三行。
5. **第 54 行**（⚠️ API 密钥说明 → Elsevier 限制段落）：`共注册 26 个工具、覆盖 13 个数据源` → `23 个工具、10 个数据源`；`配置后为 28 个` → `25 个`。
6. **第 196 / 198 行**（可用工具列表 → 计数摘要段）：`默认注册 26 个工具` → `23 个`；`总数达到 28 个` → `25 个`。
7. 删除三个独立小节及其工具表格：`### Zenodo`（README.md 263–267 / README_ZH.md 261–265）、`### dblp`（290–294 / 288–292）、`### bioRxiv / medRxiv`（296–300 / 294–298）。其中 `### bioRxiv / medRxiv` 是"可用工具列表"章节的最后一节，删除后该章节直接接 `## 🤝 贡献与共建` / `## 🤝 Call for Contributions`，注意不要留下多余空行或孤立分隔。
8. 两份各做一次全文检索 `Zenodo|dblp|bioRxiv|medRxiv` 与 `26|28|14 个|13 个`，确认除历史叙述外无残留；两份 README 当前均无 TOC（已核实），若最终版本存在指向被删小节的锚点则一并清理。
9. 中英文逐项对齐：分类 bullet 数量、数据源表格行数、`###` 级小节数量两份一致。

#### 验证方法
- 两份 README 中检索三个源名与 `medRxiv`：正文（分类 bullet、数据源表格、工具小节）零命中。
- 两份 README 中所有计数与代码实际一致（11 源 / 23 工具 / 25 工具含 key），且两份文件互相对齐。
- 对比两份 README 的 `###` 级小节目录，确认一一对应。

#### 风险提示
- 计数散落在至少 4 处互不相邻的位置（分类 bullet、总览段、Key 说明段、工具列表段），历史上两次漏改都出在这里——必须以"全文检索数字"的方式穷尽检查，而不是只改显眼处。
- `README.md:204` / `README_ZH.md:202` 的 Scopus 工具表格写有 `sort`="coverDate"：**本轮不改**（排序修复属候选步骤 60，未获授权）。若用户后续决定纳入排序修复，该表格行必须同步更新，届时另行追加步骤。
- 中英文两份必须同批改完，不允许只改一份（历史各轮均以两份同批交付）。

---

### 步骤 56：`AGENTS.md` / `CLAUDE.md` 两份 agent 指导文件同步

#### 目标说明
仓库中另有两份面向 AI agent 的指导文件硬编码了数据源清单与计数，本轮删源后同样失真。用户在上一轮已明确要求 `AGENTS.md` 应如实列出当前全部数据源的可检索范围，因此该文件的同步属于用户已表达的意图，不是本计划书的自作主张；但两份文件的**入库状态特殊**（见风险提示），故单独成步，与代码/README 的改动分开处理。

#### 具体操作
1. `AGENTS.md`（16626 字节，**当前 git 未跟踪**，内容基线为 v3.2.0）：
   - Project overview 段：`**14 data sources / 26 tools** by default (**28 tools** if SEMANTIC_SCHOLAR_API_KEY is set)` → `**11 data sources / 23 tools** ... (**25 tools** ...)`；数据源枚举串中删去 `Zenodo`、`dblp`、`bioRxiv/medRxiv`；沿用既有"product-scope decision, not a technical failure"的表述方式补一句本轮性质说明，但须按 QA-R017 修正为三类依据，并指向 `project-docs/goal.md` QA-R017。
   - `## Data sources and searchable scope` 一节：删除 `Zenodo`、`dblp`、`bioRxiv / medRxiv` 三行表格行；表头说明与 Cross-cutting notes 中对该三源的引用同步清理，至少两处：`Nothing in this server returns file contents or downloads binaries` 一条中的 "Zenodo a `file_links` list"，以及 `query` 字段说明中的 "a human-readable `server/start/end` description for `biorxiv.py`"。
   - `Architecture` 段中把 `sciencedirect.py` / `biorxiv.py` / `zenodo.py` 并列说明"语义特殊型"的那句改写——`biorxiv.py`、`zenodo.py` 均已删除，只剩 `sciencedirect.py`。
   - `_verify/` 常设流程规则段**保留不变**（该规则本身与本轮无关，其举例的 `dblp_*` 脚本按步骤 54 的决定保留）。
2. `CLAUDE.md`（9079 字节，**被 `.gitignore` 第 53 行忽略、不入库**）：该文件停在 v3.1.0 基线（15 源 / 28 工具 / 30 工具），比当前代码落后两轮（v3.2.0 删除 ChEMBL/HAL 时步骤 53 并未同步此文件）。因此本步骤应把 overview 段一次性刷新到当前基线（11 源 / 23 工具 / 25 工具），而不是只做"三个源"的减法——在旧基线上做减法只会得到一个仍然错误的数字。
3. 两个文件均**不得 `git add`**：`AGENTS.md` 未跟踪（是否入库由用户决定），`CLAUDE.md` 被 `.gitignore` 显式忽略。同时不得改动 `.gitignore` 本身（该文件在本机存在与本轮无关的既有状态，`AGENTS.md` 内已有明确告诫）。

#### 验证方法
- 两份文件中检索 `Zenodo|dblp|bioRxiv|26|28|14 |15 `，确认残留处均为历史叙述或已更新为新计数。
- `git status --short` 中不出现这两个文件的暂存项：`AGENTS.md` 应仍显示为 `?? AGENTS.md`，`CLAUDE.md` 不应出现（被忽略）。

#### 风险提示
- 这是"改 agent 自己阅读的规则书"的改动，且 `AGENTS.md` 处于未跟踪状态：若用户对该文件的入库安排另有打算，**本步骤的内容更新可整体跳过**——跳过不会破坏其他步骤的正确性，代价只是两份指导文件继续描述已删除的源，后续会话可能据此产生错误假设。
- `CLAUDE.md` 长期被 `.gitignore` 忽略却仍在维护，存在"本机有效、他处缺失"的固有风险；本计划书不改变这一现状（是否取消忽略属独立的仓库治理问题）。
- 修改 `AGENTS.md` 时**不要**触碰其中的 `_verify/` 流程规则与 "Project docs (Chinese)" 分工约定——那两条与本轮无关。

---

### 步骤 57：版本号提升至 `3.3.0`（**待用户确认**）

#### 目标说明
本项目既有惯例是"范围变更即 bump minor 版本号"（v2.1.0、v2.2.0、v3.2.0 均如此，其中 v3.2.0 与删除 ChEMBL/HAL 同批）。`goal.md` QA-R017 记录：建议 `3.3.0`，但**需用户在构建计划书阶段确认**——本步骤即该确认的门禁点。

#### 具体操作
1. `pyproject.toml` 第 7 行 `version = "3.2.0"` → `"3.3.0"`。
2. `src/uniarticles/__init__.py` 第 20 行 `__version__ = "3.2.0"` → `"3.3.0"`。
3. 两处必须**同时**修改并保持一致——v3.1.0 步骤 51 处理过这两个字段历史不一致的问题，不得只改其一。已核实 `pyproject.toml` 中项目版本号仅此一处。
4. 若用户否决 `3.3.0`（要求改号、或要求本轮不 bump），仅替换上述两处字面值即可，不影响步骤 54–56、58 的任何内容。

#### 验证方法
- `python -c "import uniarticles; print(uniarticles.__version__)"` 输出与 `pyproject.toml` 的 `version` 一致（均为 `3.3.0`）。

#### 风险提示
- **本步骤在用户明确确认前不得执行**：写入计划书不等于获得授权，QA-R017 已把版本号列为"仍未确认事项"。
- 版本号失真最容易被外部察觉（PyPI 元数据、`uvx` 缓存均受影响）；若最终决定不 bump，须在 buildlog 中说明理由。

---

### 步骤 58：`project-docs/buildlog.md` 记录本轮变更 + 整体回归验证（v3.3.0 交付检查点）

#### 目标说明
`buildlog.md` 是本项目唯一的变更日志（`CHANGELOG.md` 已并入其"历史记录"段）。本轮属破坏性变更，需留下可追溯记录，并与整体回归验证共同构成交付检查点，格式对齐 v3.2.0 的既有条目。

#### 具体操作
1. 在 `project-docs/buildlog.md` 追加本轮条目（v3.3.0，引用 QA-R017）：逐个列出删除的 3 个源/3 个工具名；**排除性质按三类分写**（biorxiv = 上游结构性不支持定向检索、dblp = 可连接性不达标、zenodo = 检索形态重复），并明确"三者均非技术不可行、非权限受限"，与 QA-R016 的产品价值收窄一并作为历史对照；记录计数变化（14→11 源、26→23 工具、28→25 含 key）、README 同步范围、版本号（若步骤 57 未执行则如实说明）。
2. 登记两条已知文档失真（本轮不改，留给对应角色处理）：`project-docs/teach.md` 第 127/132/133 行仍在描述 Zenodo/dblp/bioRxiv，其第 128/134/65 行仍描述 v3.2.0 已删除的 HAL/ChEMBL 与 `paperscraper.py` 时代的实现——该文件由 `project-explainer-cn` 维护且明确"可能滞后"，本轮删源不改变其归属；`CLAUDE.md` 的忽略状态（若步骤 56 被跳过）。
3. 整体回归（无自动化测试，沿用人工回归惯例）：启动 server → 枚举工具，确认 23/25；对**保留的 11 个源**各抽查至少 1 个工具做真实调用（Scopus/ScienceDirect 依赖 Elsevier key，Semantic Scholar 视 key 是否配置），确认删源未影响其余模块的注册与调用；确认 stdout 无任何多余输出（stdout 是 MCP stdio 的 JSON-RPC 通道）。

#### 验证方法
- `buildlog.md` 新条目中可检索到三个被删工具名与 QA-R017 引用。
- 回归结果：11 源 / 23 工具（含 key 25），保留源抽查无新增失败；服务可正常启动并退出。
- `git status --short` 中除本轮预期改动外无新增意外文件。

#### 风险提示
- 无自动化测试，"已删工具确实不再注册"只能通过枚举确认；若枚举方式本身有误（例如手工数 `@server.tool` 字符串），会得到错误结论——必须以实际 `list_tools()` 结果为准（见步骤 54 对 `semantic_scholar.py` 注释干扰的提醒）。
- 抽查若出现失败，先按 QA-R013 / `_verify/` 流程判断是否属本机网络环境波动，不要据此判定源不可用或回滚本轮改动。

---

### 步骤 59 / 60（原候选，已由用户确认并执行于 v3.3.0）：三处默认排序修复

> **执行状态（补记）**：用户在 v3.3.0 澄清中回答"2、修复"，本节候选随即启用并执行完毕——步骤 59 产出 `_verify/sort_probe.py`（提交 `f199fc1`），步骤 60 完成三处排序修复（提交 `7c66c7e`），并追加一次工具描述补全（提交 `7f18783`）。**执行中修正了本节的两处判断**：① arXiv"裸标题查不到已知论文"的决定性因素是**缺少 `ti:` 字段前缀**，而非排序——加 `ti:"..."` 后即便配合相关性排序亦能命中，只改 `SortCriterion` 不会命中（此为对 v3.3.0 计划阶段结论的更正）；② 因此 `arxiv.py` 仅把关键词检索的排序改为 `Relevance`、分类浏览保持 `SubmittedDate`（二者共用一个私有函数，一刀切会让"按分类列最新"的语义失效）；"把裸标题自动包装成 `ti:`"这一设想被明确否决，因其会破坏既有的 `au:` / `abs:` 查询习惯。下面**候选文本原样保留，不改写**（当时的"默认不纳入"前提已被用户后续确认取代）。

`goal.md` QA-R017 明确记录："三处排序修复……用户本轮未表态，默认不纳入，留待后续按 project-plan.md 增量追加步骤的方式补入"。此处以候选形式预置，用户一旦确认即可直接启用（步骤编号顺延为 59/60）。

**候选步骤 59：三处排序行为真实探测（编码前置步骤）**

- 目的：QA-R017 的实测只记录了结论（Scopus 改 `sort=relevancy` 后 3/3 命中、`TITLE("...")` 字段查询 top-1 命中、arXiv 改用 `ti:"..."` 命中、PubMed 未传 `sort` 时默认非 Best Match），**未留存可复现脚本**；按本项目"先探测再定实现、不凭空编写"的一贯做法（步骤 14/21/43 先例），实施前必须补一次真实探测。
- 内容：分别验证 `scopus.py` 的 `sort` 参数取值（`relevancy` / `coverDate`）与 `TITLE(...)` 字段语法、`arxiv.py` 的 `sort_by` 取值与 `ti:` 前缀、NCBI ESearch 的 `sort` 参数取值（含 `relevance`），以及带引号的 `"标题"[Title]` 查询返回 0 条这一现象是否可复现（QA-R017 实测记录，属 NCBI 自身行为，非本项目 bug）。
- 产出：诊断脚本写入 `_verify/`（注意 `_verify` 在 `.gitignore` 中被忽略，新脚本需 `git add -f` 才会入库——`AGENTS.md` 已记录这一既有约定，且不得为此改动 `.gitignore`）。

**候选步骤 60：实施排序修复 + 文档同步**

- 改动点（位置已由代码核实）：`src/uniarticles/sources/scopus.py:364` 的 `sort: str = "coverDate"` 默认值；`src/uniarticles/sources/arxiv.py:71` 硬编码的 `sort_by=arxiv.SortCriterion.SubmittedDate`；`src/uniarticles/sources/pubmed.py` 的 ESearch 请求补显式排序参数（该文件当前未传 `sort`）。
- 文档同步：`README.md:204` / `README_ZH.md:202` 的 Scopus 工具表格中 `sort`="coverDate" 默认值需同步更新；两份 README 与 `AGENTS.md` 中若有排序相关描述一并更新。
- 性质：这是**默认行为变更，属对已发布工具的破坏性变更**，需在 buildlog 中显著提示（依赖"按日期排序"既有行为的调用方会感知到变化）。

---

### 补记说明（步骤 61～68 的组织方式）

**步骤 61～65 为事后补记，均已执行完毕。** v3.4.0 的两轮删源（QA-R018 移除 Semantic Scholar、QA-R019 移除 OpenAlex）系用户**直接指令**，`goal.md` 已判定本轮"性质均为删除型、范围小而封闭，不需要项目规划专家介入做分阶段设计，可由 project-builder-cn 直接执行"，因此当时未走本计划书。为保持本计划书"完整构建记录"的一贯要求，此处按已实际执行的提交与 `buildlog.md` 条目回填。**编号依据**：步骤 61～64 沿用 project-builder-cn 已在提交信息与 `buildlog.md` 标题中使用的编号（不改写历史、避免与 buildlog 交叉引用矛盾）；步骤 65 那一轮在**时间上最早**（先于 61～64），但因未获编号而以"补记"置于其后，其编号仅为本计划书的文档序号，**不代表执行顺序**。

**步骤 66～68 为本轮新增、尚未执行**，由用户本轮指令直接指定："补充之前的步骤并且增加修复 arXiv 的超时步骤，保持版本号为 3.4.0，修复好后清理 dist 并发布包"。

---

### 步骤 61（补记，已完成）：删除 OpenAlex 数据源与注册引用（v3.4.0，QA-R019）

#### 目标说明
落实用户指令"既然 openalex 经常出问题，那就把它也移除了"（QA-R019）。OpenAlex 的两个工具（`openalex_work_search_by_query`、`openalex_work_detail_by_doi`）均为**无条件注册**，因此本轮工具数**确实下降**（23→21），这与步骤 65（Semantic Scholar，无 Key 时本就注册 0 个工具、用户可见工具数不变）性质不同，两者不得混写。删除性质为**上游可用性/限流不稳定**（检索与 DOI 解析两条路径均 429，唯一可用的实体 ID 直取形态本项目并未暴露），**非代码缺陷、非权限受限**——不得据此认为 OpenAlex 的接口实现有缺陷。

#### 具体操作
1. 删除 `src/uniarticles/sources/openalex.py`（含其倒排索引摘要重建逻辑 `abstract_inverted_index`）。
2. `src/uniarticles/sources/__init__.py`：删除 `from .openalex import register as register_openalex_source` 与 `register_openalex_source(server)`，并清理随之孤立的分组注释（若有，比照步骤 53/54 对孤立注释的处理）。
3. `_verify/tool_availability_check.py`：删除 4 处 OpenAlex 调用，其中一处是**以 OpenAlex 搜索结果回填 DOI 的依赖链**——该依赖同时导致 `openalex_work_detail_by_doi` 在上游 429 时被"连锁判失败"（脚本层面的失真，非工具本身缺陷）。
4. 不改动其余 9 个源模块的任何代码，包括各模块内硬编码的 `USER_AGENT` 版本号字符串（沿用 v3.1.0 步骤 51 已确认的惯例：仅在该模块被创建/重写时设为当时版本号）。
5. 执行结果：提交 `6ac1aef`。

#### 验证方法
- `create_server()` → `list_tools()`：**9 个数据源 / 21 个工具**，工具名单中无 `openalex_*`。
- 全仓库静态检索（**必须 `rg --no-ignore`**，`_verify/` 被 `.gitignore` 遮蔽）：`openalex` / `OpenAlex` 在 `src/`、`_verify/` 中零命中，仅历史文档条目保留。

#### 风险提示
- **不得**用 `rg -c "@server.tool"` 计数（历史上有注释中的同名字符串导致虚高的先例），一律以 `list_tools()` 返回值为准。
- OpenAlex 移除后，"匿名限流导致某一源不可用"在本项目**已无同类先例**；后续若新增源遇到同类现象，仍按 QA-R013 的 `_verify/` 流程处置，不得据单机单次失败直接删源。

---

### 步骤 62（补记，已完成）：`README.md` / `README_ZH.md` 同步下线 OpenAlex + 全工具可用性复测

#### 目标说明
文档与代码不得出现"文档写了但代码没有"的不一致（本项目历史上已两次发生计数漏改：v2.2.0 步骤 17、v2.3.0 步骤 23）；同时用一次真实全量复测确认删源未波及其余源。

#### 具体操作
1. 两份 README 同步：特性列表中的源清单、数据源对比表格行、`### OpenAlex` 独立小节（含 2 个工具行与 429 风险说明）、"工具可用性实测"段落的计数与结论、以及"文献查找"推荐提示词第 2/3 步中的 OpenAlex 引用与 429 处置说明，逐处删除或改写。
2. 推荐提示词的第三步列表因删去 OpenAlex 出现**编号断档**，重排为连续编号（OpenAlex 原为第 2 项），并复核正文中其余编号引用。
3. 复测后把实测结论写回两份 README 的可用性段落。
4. 执行结果：提交 `de237ee`。

#### 验证方法
- 两份 README 中 `openalex` / `OpenAlex` 零命中（除刻意保留的历史说明）。
- 推荐提示词第三步编号连续、无跳号。
- `_verify/tool_availability_check.py` 实跑：该时点 **21 called / 21 ok**。同日 19:45 的独立复跑出现 19/21（两个 arXiv 工具挂起 337.8s / 338.1s 后失败），属 arXiv 上游瞬时超时窗口，见步骤 66 与 `buildlog.md` 2026-09-18 20:08 条目——**两条记录均予保留**，后者不推翻前者。

#### 风险提示
- 提示词步骤编号重排最易漏改（同一源同时出现在"第三步"列表、表格与正文说明中）。
- 复测结果受上游瞬时状态影响，**不得**把单轮失败直接定性为源不可用或回滚改动（QA-R013）。

---

### 步骤 63（补记，已完成）：`AGENTS.md` 同步下线 OpenAlex

#### 目标说明
`AGENTS.md` 是 agent 进入本仓库的第一手上下文，源清单与工具计数必须以代码为准。

#### 具体操作
1. `AGENTS.md`：项目概述的源清单与工具计数改为 **9 个数据源 / 21 个工具**，并补入 v3.4.0 两轮删源的性质说明；"Data sources and searchable scope" 表删除 OpenAlex 一行。
2. **不得 `git add` `AGENTS.md`**（用户未授权该文件入库），不得改动 `.gitignore`；该文件当前仍为 git 未跟踪状态。
3. 执行结果：提交 `67e2815`。

#### 验证方法
- 全仓库检索 `openalex`（`--no-ignore`）确认仅剩历史文档条目。
- `git status --short` 中 `AGENTS.md` 仍为未跟踪状态（`?? AGENTS.md`），未被暂存。

#### 风险提示
- `AGENTS.md` 与 `project-docs/*` 同属"手工维护的上下文文件"，每轮删源都需同步；若后续继续删源，宜将其列为构建步骤的固定检查项。

---

### 步骤 64（补记，已完成）：整体终验 + 完成标记（v3.4.0）

#### 具体操作
1. 端到端 stdio 验证：以子进程启动 server、发送 `initialize`，断言 stdout 仅 1 行且为合法 JSON-RPC、stderr 无多余输出（stdout 是 MCP stdio 的协议通道）。
2. 静态终检：`list_tools()` = 21；`pyproject.toml` 与 `src/uniarticles/__init__.py` 版本号均为 `3.4.0`；文档计数零残留。
3. `buildlog.md` 追加"🎉 项目构建完成"条目并登记遗留事项。
4. 执行结果：提交 `91a9989`。

#### 验证方法 / 风险提示
- 判据同步骤 61/62/63。
- 终验只证明"该时点可用"，**不构成对上游长期稳定性的承诺**——随后 19:42、20:08 两条补正条目即为反例，其中 20:08 那条直接催生了步骤 66。

---

### 步骤 65（补记，已完成，**时间上先于步骤 61～64**）：移除 Semantic Scholar 数据源（v3.4.0，QA-R018）

#### 目标说明
落实用户指令："移除源码、项目说明和 README.md 中关于 `SEMANTIC_SCHOLAR_API_KEY` 的部分，因为该机构的 API key 申请存在权限问题。" **只能整源移除，不能只去掉 Key 要求**：实测无 Key 时 `paper/search` 连续 4 次全部返回 HTTP 429（响应体自述 "apply for a key"），保留工具等于对外暴露一个永远失败的工具，违反 QA-R012 已确立的"不注册永远不可能成功的工具"原则。删除性质为**外部授权/准入受限（机构无法取得 Key）**，与 QA-R003（可换 Key 的权限受限）、QA-R012（技术不可行）、QA-R016（产品价值收窄）、QA-R017（有效性/可连接性）、QA-R019（上游限流）均不同。

#### 具体操作
1. 源码：删除 `src/uniarticles/sources/semantic_scholar.py`（95 行）；清理 `sources/__init__.py` 的 import/注册；`config.py` 移除 `semantic_scholar_api_key` 字段；`core.py` 注释中 "unlike Semantic Scholar" 的对照说明改写。
2. 用户文档：`README.md` / `README_ZH.md`（特性列表、数据源表、工具清单、JSON 示例、`.env` 示例、API Key 说明段、"可用工具"前言、推荐提示词中的 Key 前置条件）、`tutorial/step_by_step_guide_en.md`、`tutorial/step_by_step_guide_zh.md`、`.env.example`；`claude_desktop_config.example.json` 中该行由用户先行删除。
3. 项目说明：`AGENTS.md` 项目概述、配置示例、以及"条件注册 vs 无条件注册"整段改写为"全部无条件注册"（保留 Semantic Scholar 作为历史反例）、数据源范围表。
4. 未改动：`project-docs/teach.md`（用户明确"没必要更新"）。
5. 执行结果：提交 `e21475d`、`b4e88c8`。

#### 验证方法
- `create_server()` → `list_tools()`：**23 个工具不变**（无 Key 时该源本就注册 0 个工具）。这是本轮最容易被误读的一点：变更的是**数据源数 11→10** 与"配置 Key 后追加 2 个工具、总数 25"这一承诺的消失，**不是**用户可见的工具数。
- 全仓库 `SEMANTIC_SCHOLAR_API_KEY` 零引用（含 `--no-ignore` 覆盖 `_verify/`）。
- 附带收益（已验证）：**全项目不再存在条件注册架构**——所有源的 `register()` 均不再读取 `settings`，工具列表在任何配置下恒定。

#### 风险提示
- buildlog 与文档中不得把"工具数不变"写成"无变化"；也不得把本轮记成"技术不可行"或"权限受限但可换 Key"。
- 该源若未来重新纳入，需先评估是否恢复条件注册模式（本步骤已留书面反例）。

---

### 步骤 66：为 `arxiv.py` 增加显式超时（**本轮新增，待执行**）

#### 目标说明
修复交付后复验发现的**真实缺陷**（`buildlog.md` 2026-09-18 20:08 条目）：`arxiv.py` 使用 `arxiv.Client()` 默认配置、**未设置任何超时上限**，上游 `export.arxiv.org` 卡住时工具会挂起 **300+ 秒**（实测 337.8s / 338.1s）才返回错误，而非快速失败。上游卡顿时客户端侧很可能表现为整个工具调用超时，与"为可靠性收缩数据源"的产品取向直接冲突。用户本轮明确要求修复。工具名、参数、返回结构均不变，属内部行为变更。

根因（**已核实，非推测**）：项目 `.venv` 实际安装 `arxiv==2.4.1`（`uv.lock` 锁定值），其 `arxiv/__init__.py:729` 通过 `self._session.get(url, headers=...)` 发请求，`self._session` 是 `requests.Session()`（同文件 `__init__` 第 613 行），而 `requests` 的 `Session.get` 支持 `timeout=`；但 `Client.__init__(self, page_size=100, delay_seconds=3.0, num_retries=3)` **不暴露任何超时参数**，因此必须在客户端外注入。

#### 具体操作
1. 新增两个模块级常量（置于 `_ARXIV_CATEGORY_RE` 附近）：`_ARXIV_REQUEST_TIMEOUT_SECONDS = 15.0`、`_ARXIV_TOTAL_TIMEOUT_SECONDS = 45.0`。
2. 新增私有工厂，三处调用点统一改用：
```python
def _build_client() -> arxiv.Client:
    """Build an arxiv client with a real request timeout.

    arxiv.Client exposes only page_size/delay_seconds/num_retries — no timeout
    — so an upstream stall hangs the call (measured 337.8s / 338.1s on
    2026-09-18). arxiv 2.4.1 issues requests through an internal
    requests.Session (arxiv/__init__.py:613, :729), so injecting `timeout=`
    there bounds each attempt at the socket level. num_retries is lowered to 1
    so the worst case stays ~2x the per-request timeout instead of ~4x.
    """
    client = arxiv.Client(num_retries=1)
    session = getattr(client, "_session", None)  # private attr: version-sensitive
    if session is not None:
        original_get = session.get

        def _get_with_timeout(url, **kwargs):
            kwargs.setdefault("timeout", _ARXIV_REQUEST_TIMEOUT_SECONDS)
            return original_get(url, **kwargs)

        session.get = _get_with_timeout
    return client
```
3. 三处调用点（`_run_arxiv_search` 的两个调用方 + `_get_paper_details`）加上**外层兜底**，覆盖"私有属性在未来版本中消失导致注入失效"的情形：
```python
try:
    return await asyncio.wait_for(
        asyncio.to_thread(
            _run_arxiv_search, normalized_query, bounded, arxiv.SortCriterion.Relevance
        ),
        timeout=_ARXIV_TOTAL_TIMEOUT_SECONDS,
    )
except asyncio.TimeoutError:
    return _err(
        query=normalized_query,
        message=(
            f"arXiv request timed out after {_ARXIV_TOTAL_TIMEOUT_SECONDS:.0f}s; "
            "upstream export.arxiv.org may be stalling — retry shortly, or run "
            "_verify/arxiv_connectivity_test.py for a layered diagnosis"
        ),
    )
except Exception as exc:
    return _err(query=normalized_query, message=str(exc))
```
（分类浏览工具沿用 `arxiv.SortCriterion.SubmittedDate`、详情工具沿用 `_get_paper_details`，仅补同样的超时包装。）
4. 不改注册、不改工具名/参数/返回结构、不新增环境变量（沿用"不做面向未来的预留配置"原则）。
5. `requests` 属 `arxiv` 的传递依赖，**不需要**新增依赖项，`pyproject.toml` 的 `dependencies` 不变。

#### 验证方法
1. 正向（真实网络）：`_verify/tool_availability_check.py` 中三个 arXiv 工具全部 `ok`，各次耗时 < 10s（对照：故障窗口内为 337.8s / 338.1s，正常时约 1～2s）。
2. 负向（**离线、确定性、不依赖外网**）：新增 `_verify/arxiv_timeout_check.py`——本机起一个"只 accept、不响应"的 TCP 监听，把 `arxiv.Client.query_url_format`（`arxiv/__init__.py:574` 的公开类属性）临时指向该地址，断言调用在 `_ARXIV_REQUEST_TIMEOUT_SECONDS + 余量`（建议断言 < 25s）内返回 `ok=False` 且 `error` 含 timeout 关键字；脚本结束前恢复被改写的类属性并关闭监听端口。脚本按 `_verify/` 惯例无第三方依赖、输出自动脱敏、只做只读探测。
3. 静态：`create_server()` → `list_tools()` 仍为 21；`python -c "import uniarticles"` 无 stdout 输出。
4. 边界：三个工具在超时路径上必须返回归一化 `_err()`，**不得**让异常穿透到 MCP 层。

#### 风险提示
- `client._session` 是**私有属性**，依赖它属于脆弱写法：已在 `getattr` 缺失时降级（只保留外层兜底），并要求 buildlog 记录该依赖点与 `arxiv==2.4.1` 版本。未来若放宽/升级 `arxiv` 版本，本步须重测。
- `asyncio.wait_for` 超时**不会真正终止**已在 `to_thread` 中执行的线程：上游始终不返回时，该线程会继续占用默认线程池槽位（`min(32, cpu+4)`）直到 socket 超时。因此**注入 socket 超时是主手段**（真正让线程退出），外层 `wait_for` 只是版本漂移的兜底，**两者不可只用后者**。
- 超时值取舍：arXiv 正常响应约 1～2 秒，15 秒已足够宽裕；若保留 `num_retries=3`（默认值），最坏耗时约 4×15s + 3 次 3s 间隔 ≈ 69s，**等于没治**，故必须同时降到 1。
- 异常捕获须用 `asyncio.TimeoutError`（`requires-python >= 3.10`，3.10 中它与内建 `TimeoutError` 并非同一对象）。
- **不得**使用 `socket.setdefaulttimeout()` 或改动全局 `requests` 行为：那会波及同进程内其余 8 个源（`httpx`）与所有 `requests` 调用，属跨模块副作用。
- 这是**行为变更**（原本长时间等待 → 现在快速失败），需在 buildlog 显著标注；对调用方而言，从"超时无响应"变为"明确错误 + 可操作提示"，是方向性改善而非破坏。

---

### 步骤 67：文档同步 arXiv 超时（`README.md` / `README_ZH.md` / `AGENTS.md`）

#### 目标说明
两份 README 的 arXiv 可用性提示当前写的是"**未设置显式超时**……会先长时间挂起再报错"，步骤 66 落地后该描述即失实，必须同步，否则形成新的"文档与代码不一致"。

#### 具体操作
1. `README.md:214` / `README_ZH.md:212` 的可用性提示段：**保留** 2026-09-18 的实测事实（337.8s / 338.1s 挂起、约 15 分钟后自愈、同主机另一工具正常返回），把"未设置显式超时"的现状描述改写为"已设 15 秒请求超时 + 45 秒兜底，超时将返回带提示的错误；`_verify/arxiv_connectivity_test.py` 仍可用于区分上游卡顿与本机网络问题"。
2. `AGENTS.md` 数据源范围表 arXiv 行的 "Caps & caveats" 补入超时参数，并保留"字段前缀对已知文献定位决定成败"的既有结论。
3. 不修改 `project-docs/teach.md`（用户已明确不更新，当前已滞后多轮，属已知失真）。

#### 验证方法
- 检索"未设置显式超时" / "no explicit timeout"：两份 README 中零命中。
- 检索超时数值：两份 README 的 arXiv 小节与 `AGENTS.md` 中出现的秒数与 `arxiv.py` 常量**逐一一致**（防文档与代码数值漂移）。
- `git status --short` 中 `AGENTS.md` 仍未被暂存。

#### 风险提示
- 该段落是"历史事件 + 现状成因"的混合叙述，改写时**不得**连历史实测数据一并删除——那是该源风险的真实证据。
- 若步骤 66 最终调整了超时数值，本步三处（两份 README + `AGENTS.md`）必须同步。

---

### 步骤 68：保持版本号 `3.4.0` + 清理 `dist/` + 构建 + 发布 PyPI（**发布为不可逆对外操作，须用户在场确认后方可执行**）

#### 目标说明
把 v3.4.0（9 个数据源 / 21 个工具）发布到 PyPI。用户本轮指令："保持版本号为 3.4.0，修复好后清理 dist 并发布包"。

#### 具体操作
1. **版本号核对（不改动）**：`pyproject.toml` 与 `src/uniarticles/__init__.py` 当前均已是 `3.4.0`；`uv run python -c "import uniarticles; print(uniarticles.__version__)"` 应输出 `3.4.0`。本轮只新增源码修复与文档同步，**不得**再 bump 版本号。
2. **发布前门禁（阻塞项）：许可证元数据不一致**。`pyproject.toml` 现为 `license = { text = "MIT" }`，且 classifiers 含 `"License :: OSI Approved :: MIT License"`；而 `LICENSE` 文件是 **GNU AGPL-3.0**、`README.md` 第 3～4 行徽章为 AGPL-3.0 + Commercial-Restricted。发布后 PyPI 将对外呈现与仓库许可证**相矛盾**的元数据，且同一版本号无法撤销重发。须先由用户确认目标许可证，再据此对齐 `pyproject.toml`（若确认为 AGPL-3.0：`license = "AGPL-3.0-or-later"` + classifier `License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)`，并移除 MIT classifier）。**本门禁未通过前不得执行第 3～7 步。**
3. **清理 `dist/`**：当前目录内是上一版残留产物（`uniarticles_mcp-3.2.0-py3-none-any.whl`、`uniarticles_mcp-3.2.0.tar.gz`），**没有任何 3.4.0 产物**——正是 `AGENTS.md` 明确警告过的"陈旧产物被误传至 PyPI"场景。先列出目录确认内容，再删除整个 `dist/` 目录（`Remove-Item -Recurse -Force` 的目标须为仓库内 `<repo>\dist`，删除前用 `Resolve-Path` 核对绝对路径；该目录已在 `.gitignore:11` 中，删除不影响版本控制）。
4. **构建**：`uv build`。
5. **产物核对（发布前最后一道门禁）**：确认只生成 `uniarticles_mcp-3.4.0-py3-none-any.whl` 与 `uniarticles_mcp-3.4.0.tar.gz`；列出 wheel 内文件确认 `sources/` 下恰为 9 个源模块（且无 `openalex.py` / `semantic_scholar.py` / `biorxiv.py` / `dblp.py` / `zenodo.py` / `chembl.py` / `hal.py`）；列出 sdist 内容确认**不含** `project-docs/`、`.env`、`docs/`、`CLAUDE.md`（`pyproject.toml` 的 `[tool.hatch.build.targets.sdist] exclude` 已配置，但 `.env` 属凭据泄漏风险最高项，必须实测确认）。
6. **发布**：`uv publish`。**凭据现状（已核实）**：本机不存在 `~/.pypirc`，环境变量 `UV_PUBLISH_TOKEN` 未设置 → 直接执行会在非交互 shell 中失败或挂起。需用户提供 PyPI API token，并以 `UV_PUBLISH_TOKEN` 环境变量传入（**不得**将 token 写入任何文件、命令回显或日志）。
7. **发布后核对与记录**：访问 `https://pypi.org/project/uniarticles-mcp/3.4.0/` 或于临时环境 `uv pip install --refresh "uniarticles-mcp==3.4.0"` 确认可安装；`buildlog.md` 追加本步记录（发布结果、产物文件名与大小、许可证结论）；`git status --short` 应保持干净（`dist/`、`sdist/` 均被 `.gitignore` 忽略）。
8. 本仓库历史从未打过 git tag（`git tag` 为空），故本步**不引入** tag；如需可另议。

#### 验证方法
- PyPI 上存在 `3.4.0`，且页面呈现的许可证与仓库 `LICENSE` 一致。
- wheel/sdist 文件清单符合第 5 步判据（无内部文档、无凭据）。
- 本地 `dist/` 中不存在任何非 3.4.0 产物。

#### 风险提示
- **PyPI 版本不可回收**：同一版本号上传后不可覆盖（只能 yank，且 yank 不等于删除），故第 2、5 步门禁必须先过；许可证尚未定论时**宁可推迟发布**。
- 发布属不可逆对外动作，必须在用户明确在场授权后执行；agent 不得在无人确认的情况下自行发布。
- 若 `uv publish` 中途失败（网络/凭据），先确认 PyPI 上是否已有部分文件上传，再决定是否重试；**不要盲目重复执行**。
- 构建须用 `uv build`（遵循 `uv.lock` 锁定版本），不要改用全局 `python -m build`，以免产物元数据来自未经锁定验证的环境。
- 发布后若发现产物内容缺陷，只能 bump 至 `3.4.1` 重发，**不能重发 `3.4.0`**。
- `pyproject.toml` 的 sdist `exclude` 中仍列有已删除的 `/CLAUDE.md`，属无害冗余，可选清理，不属本步门禁。

---

### 步骤 69：CORE v3 新端点与响应字段真实探测（v3.5.0，QA-R021，**编码前置步骤，必须最先执行**）

#### 目标说明
步骤 70～75 的全部参数签名与归一化字段必须建立在**真实响应结构**之上，不得依据官方文档字面描述或历史备注凭空定义。现有 `_verify/core_api_probe.py`（commit `ad95420`）只覆盖两类请求：**连通性与复测项**（`GET /v3/search/works`、`GET /v3/works/{裸 DOI}`、`POST /v3/search/works` + `exclude`、`GET /v3/data-providers/{id}`、`GET /v3/outputs/{id}`、以及 journals / discover / recommend / TEI / outputs 检索的复测），**没有**覆盖本轮新增工具依赖的以下结构与字段：

- `POST /v3/search/works/aggregate` 的**请求体 schema**（聚合维度字段名、是否支持 `limit`、`q` 与 `filter` 的关系）——这是本轮**唯一一处从未被真实探测过的请求体**；
- `GET /v3/works/{id}/outputs`、`/works/{id}/stats` 的响应字段；
- `GET /v3/data-providers/{id}/stats`、`/data-providers/{id}/outputs` 的响应字段；
- `GET /v3/search/data-providers?q=` 的响应结构；
- 以上各端点在 `offset` / `limit` 边界上的真实行为（`limit=100` 是否被接受、越界 `offset` 是空结果还是 400）。

本步骤产出一个**独立、纯标准库、只读**的诊断脚本并按 `goal.md` QA-R013 的既有流程交用户在真实网络环境复测；同时它也是 `project-builder-cn` 自身编码时的字段依据。**不得**在本步骤之前编写任何归一化代码。

> **命名与流程说明**：本步骤**新增** `_verify/core_api_field_probe.py`，**不修改、不替换** `_verify/core_api_probe.py`（后者是 QA-R021 复测的存档证据，须原样保留）。两者的分工是：前者回答"新端点/新字段长什么样"，后者回答"此前的失败是不是环境噪声"。

#### 具体操作
1. 新建 `_verify/core_api_field_probe.py`，沿用 `_verify/core_api_probe.py` 的三个既有约定（照抄其实现风格，不要另起一套）：
   - **零第三方依赖**（仅 `argparse`/`json`/`os`/`re`/`socket`/`ssl`/`sys`/`time`/`urllib`），保证用户在未安装项目依赖的环境里也能直接 `python _verify/core_api_field_probe.py`；
   - **输出脱敏**：所有输出走一个 `_print()` 包装器，先对 IPv4 点分十进制后两段打码，再把 API Key 明文替换为 `***API_KEY***`；Key 读取顺序为环境变量 `CORE_API_KEY` → 仓库根目录 `.env`，都取不到时以匿名请求继续跑完并显式提示该档位更低；
   - **只读**：不改任何文件、不下载任何二进制、不落地任何内容。
2. 脚本的请求清单（建议一次性跑完，允许 `--only` 选择子集）应至少覆盖下表；每项记录 `status` / `elapsed` / 字节数 / 三个限流响应头 / 响应体前 N 字节（截断，防 1MB+ 的 `fullText` 刷屏）：

| 编号 | 请求 | 探测目的 |
|---|---|---|
| F1 | `GET /v3/search/works?q=machine learning&limit=2` | 对照组：确认本机网络与鉴权正常 |
| F2 | `POST /v3/search/works`，body `{"q": "...", "limit": 2, "exclude": ["fullText"]}` | 确认 `exclude` 与响应体积收益（对照 F1） |
| F3 | `POST /v3/search/works`，body 追加 `"offset": 2` | 验证 `offset` 分页被接受、且与 `limit` 组合后的结果条数 |
| F4 | `POST /v3/search/works`，body `limit=100` | 验证步骤 71 把上限提到 100 的前提 |
| F5 | `POST /v3/search/works/aggregate`，body `{"q": "machine learning"}` | **核心待测项**：确认聚合请求体最小可用集；若 400/422，逐一试 `{"q": ..., "limit": ...}`、`{"q": ..., "aggregations": [...]}` 等候选形态并记录上游错误体 |
| F6 | 同上，body 增加显式维度字段（如 `"aggregations": ["yearPublished","authors","publisher"]`） | 确认维度字段名与"是否可指定维度"；与 F5 对照得出最终签名 |
| F7 | `GET /v3/works/171513974` | 取 `dataProviders` / `outputs` / `identifiers` 真实字段（含 `core_id` / `doi` / `oai` 等键名） |
| F8 | `GET /v3/works/171513974/outputs` | `core_work_outputs_by_id` 的字段依据（`downloadUrl`/`license`/`fulltextStatus`/`dataProvider` 等确切键名与嵌套层级） |
| F9 | `GET /v3/works/171513974/stats` 与 `GET /v3/works/10.1038/nature12373/stats` | `core_work_stats_by_id` 字段依据 + 确认"DOI 亦可" |
| F10 | `GET /v3/works/10.1000/does-not-exist-xyz` | 未知 DOI 的 404 响应体形态（历史记录为 `{"message":""}`，需复核是否为空 message，供兜底文案使用） |
| F11 | `GET /v3/works/10.1038/nature12373/outputs` | 复核"子资源只接受数字 CORE ID、DOI 会 404"这一边界（`core_work_outputs_by_id` 的输入校验依据） |
| F12 | `GET /v3/search/data-providers?q=university&limit=2` | `core_data_provider_search_by_query` 字段依据 + 该端点的 `limit` 上限 |
| F13 | `GET /v3/data-providers/1630` | `core_data_provider_detail_by_id` 主字段依据 |
| F14 | `GET /v3/data-providers/1630/stats` | 统计子资源字段依据（决定是否并入详情工具或单独暴露参数） |
| F15 | `GET /v3/data-providers/1630/outputs?limit=2` | 机构库下 outputs 字段依据 + 确认 `sort` 取值 |
| F16 | `GET /v3/outputs/29197653` | `core_output_detail_by_id` 字段依据（`license`/`sdg`/`repositories`/`fulltextStatus`/`sourceFulltextUrls` 等确切键名） |
| F17 | `GET /v3/search/outputs?q=machine learning&limit=2`、`?q=title:"machine learning"&limit=2`、`?q=doi:"10.1007/s10994-024-06619-7"&limit=2` | **第 9 项工具（条件纳入）的击杀条件判据**：三种查询组合必须全部 200 方可纳入 |

3. 脚本末尾输出一段"诊断结论"，把 F17 的三种组合结果显式判定为"可纳入 / 不纳入"两种结论之一（与 `core_api_probe.py` 的 `_conclusions()` 同样风格），并对 F5/F6 给出"聚合请求体的确证形态"或"聚合端点不可用，需回退方案"。
4. 脚本写好后先由 `project-builder-cn` 在本机跑一遍（若本机同样出现网络/HTTP 异常，**不得据此定性端点失败**，按 QA-R013 交用户复测）；结果（尤其 F5/F6/F8/F16/F17）如实抄录进 `project-docs/buildlog.md` 的本步骤条目，作为步骤 70～75 的编码依据。

#### 验证方法
- `python _verify/core_api_field_probe.py --help` 正常输出；不带参数可完整跑完（有 key 与无 key 两种情形都不崩）。
- 输出中不含任何未脱敏的 IPv4 明文与 API Key 明文（逐行核对关键字 `104.` / `Bearer`）。
- F1/F2 至少一项 200（否则说明本机网络问题，结论不可用于编码依据）。
- `git status --short` 显示新增文件仅为 `_verify/core_api_field_probe.py`（未被 `.gitignore` 遮蔽；若被遮蔽须 `git add -f`，与既有 `_verify/` 脚本的处理方式一致）。
- 关键探测结果（聚合请求体确证形态、F17 三组合状态码）已写入 `buildlog.md`。

#### 风险提示
- **聚合端点是本轮最大的未验证点**：`POST /v3/search/works/aggregate` 的请求体此前从未被真实请求验证过；若 F5/F6 全部失败，**不得**擅自把该工具改为"猜测的请求体"上线，应按 QA-R013 记录失败证据、交用户复测，并准备回退方案（步骤 73 的备选：本轮缩减为 8 项工具，聚合维度顺延到后续版本）。
- 该端点的响应是**字典而非列表**（历史记录为 `{"aggregations":{"yearPublished":{"2019":575,...}}}`），与项目既有"`items` 为列表"的约定不同——归一化方案必须在拿到真实结构后再定（见步骤 73），本步骤**只记录结构、不写转换代码**。
- CORE 对 4xx/5xx 可能返回非 JSON 或空 `message` 的错误体（F10 即为此设计），脚本解析响应体时须容错，避免诊断脚本自己崩在 JSON 解析上。
- `limit=100` 的 outputs/works 响应体可达 1 MB 以上（`fullText` 内联），脚本必须截断读取，否则在慢网络上极易超时并污染结论。
- 本脚本会消耗 CORE token（个人档 1,000 tokens/天）；17 项请求属轻量范围，但**不要**把它写成循环压测或批量扫描。
- 严禁把真实 Key 写入脚本、命令回显或 buildlog——脚本只从环境变量/`.env` 读取，不打印。

---

### 步骤 70：`core.py` 公共骨架重构（v3.5.0）

#### 目标说明
步骤 71～75 会在同一文件内新注册 8 个工具，如果每个工具各自拼 URL、各自处理 429、各自拼错误文案，`core.py` 会迅速退化成一堆重复代码。本步骤先把公共能力抽出来，使后续 5 个编码步骤只写"参数校验 + 调用 + 归一化"三段。**本步骤不改变任何已注册工具的名称、参数或返回结构**（增强本身放在步骤 71）。

本步骤同时落地 QA-R021 明确要求的**限流口径更正**（原注释与文案"无 key 约 5 次请求后约 10 分钟锁死"与官方现行 token 制不符）。

#### 具体操作
1. `USER_AGENT` 由 `UniArticlesMCP/3.0.0` 更新为 `UniArticlesMCP/3.5.0`（同一 URL 后缀不变）。**不要**顺手去改 `crossref.py`/`doaj.py`/`europepmc.py`/`openaire.py`/`pubmed.py`/`scopus.py` 里各自的 `USER_AGENT` 版本串——那是既存的版本串漂移问题（多个源仍写 3.0.0/3.1.0/0.1.0），影响面超出本轮授权范围，按 v3.1.0 步骤 9"不蔓延"的先例留待后续独立事项；如需一并处理，须先取得用户同意。
2. URL 常量改为基址 + 端点拼装的形式，避免每个工具各自硬编码长字符串：
```python
BASE_URL = "https://api.core.ac.uk/v3"
```
并在各工具内部用 `f"{BASE_URL}/works/{identifier}"` 这类写法拼装；原 `BASE_URL = "https://api.core.ac.uk/v3/search/works"` 常量被替换（注意：该常量此前只在 `_search()` 内部使用，替换后须全文确认无残留引用）。
3. 公共响应构造统一为三个 helper，并对**单条结果**明确使用 `items` 单元素列表以保持全局响应形状不变：
```python
def _ok(query: str, items: list[dict]) -> dict:
    """标准成功响应：items 恒为列表（跨全部数据源统一形状）。"""
    return {"ok": True, "source": "core", "query": query, "count": len(items), "items": items, "error": None}


def _ok_one(query: str, item: dict) -> dict:
    """单条记录类工具（详情 / stats）专用：语义由调用方写入工具 docstring。"""
    return _ok(query=query, items=[item])


def _err(query: str, message: str) -> dict:
    return {"ok": False, "source": "core", "query": query, "count": 0, "items": [], "error": message}
```
4. 新增**标识符解析 helper**，把"哪些端点接受 DOI、哪些只接受数字 CORE ID"这条真实边界固化在一处，并给出可操作错误文案：
```python
_CORE_ID_RE = re.compile(r"^\d+$")


def _is_core_id(identifier: str) -> bool:
    return bool(_CORE_ID_RE.match(identifier.strip()))


def _require_core_id(identifier: str, *, tool: str) -> str | None:
    """返回规范化后的数字 CORE ID；若调用方传了 DOI 等非数字标识符则返回 None。

    CORE 的 works 子资源（/outputs）只接受数字 CORE ID——实测传裸 DOI 会 404，
    因此调用方需要在工具层给出明确提示，而不是把上游 404 原样抛给 LLM。
    """
    candidate = identifier.strip()
    return candidate if _is_core_id(candidate) else None
```
5. 新增**限流响应解析 helper**（替换既有"Retry after: 原样字符串"的文案）：
```python
from datetime import datetime, timezone


def _rate_limit_message(response: httpx.Response) -> str:
    """把 CORE 的限流响应头翻译成可执行的中文提示。

    X-RateLimit-Retry-After 实测是 ISO 时间戳（如 2026-09-18T15:35:09+0000），
    不是秒数；解析失败时原样回显，绝不抛异常。官方档位：未认证 100 tokens/天、
    10 次/分钟且不提供 fullText；注册个人 1,000 tokens/天、25 次/分钟。
    """
    raw = response.headers.get("x-ratelimit-retry-after") or response.headers.get("Retry-After")
    limit = response.headers.get("x-ratelimit-limit")
    remaining = response.headers.get("x-ratelimit-remaining")
    when = raw or "未知"
    if raw:
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            seconds = (parsed - datetime.now(parsed.tzinfo or timezone.utc)).total_seconds()
            if seconds > 0:
                when = f"{raw}（约 {int(seconds)} 秒后）"
        except ValueError:
            pass
    hint = "" if settings.core_api_key else " 配置 CORE_API_KEY 可获得更高额度（未认证档：100 tokens/天、10 次/分钟，且不提供 fullText）。"
    return f"CORE 触发限流（HTTP 429）。可重试时间：{when}；额度：limit={limit or '未知'} / remaining={remaining or '未知'}。{hint}".strip()
```
6. 新增统一的**错误响应工厂**，覆盖三类真实失败：
```python
def _error_for(response: httpx.Response, *, query: str) -> dict:
    if response.status_code == 429:
        return _err(query=query, message=_rate_limit_message(response))
    if response.status_code == 404:
        return _err(query=query, message=f"CORE 未找到该记录（HTTP 404）。请确认标识符存在且端点接受该标识符类型；{query!r} 对应的记录可能未收录。")
    try:
        detail = response.json()
    except ValueError:
        detail = (response.text or "").strip()[:200]
    message = detail.get("message") if isinstance(detail, dict) else detail
    return _err(query=query, message=f"CORE 请求失败（HTTP {response.status_code}）：{message or '上游未返回错误说明'}")
```
   **注意**：`raise_for_status()` 不再作为主路径——它抛出的英文异常信息既不带限流重试时间，也不带可读的上游错误体，全部改用 `_error_for()` 显式分支。
7. 新增统一的**公共请求入口**，把 `follow_redirects`、超时、headers、错误转换集中处理（CORE 偶发 301 重定向，既有代码已开 `follow_redirects=True`，必须保留）：
```python
async def _request(method: str, path: str, *, query: str, params: dict | None = None, json_body: dict | None = None) -> dict:
    """所有 CORE 工具的唯一出口：成功返回归一化后的原始 payload，失败返回 _err 结构。

    返回值为 dict：成功时是 {"ok": True, "payload": <原始 JSON>}，失败时就是 _err(...)。
    """
    url = f"{BASE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=30.0, headers=_headers(), follow_redirects=True) as client:
            response = await client.request(method, url, params=params, json=json_body)
        if response.status_code != 200:
            return _error_for(response, query=query)
        return {"ok": True, "payload": response.json()}
    except Exception as exc:  # noqa: BLE001 - 工具层必须把任何异常转成 _err，不能让它冒泡
        return _err(query=query, message=f"CORE 请求异常：{type(exc).__name__}: {exc}")
```
   `_on_error(response, query)` 判定与 `{ok: True, payload}` 解包在调用方统一为：
```python
result = await _request("GET", f"/works/{identifier}", query=identifier)
if not result["ok"]:
    return result          # 已是 _err 结构，直接回给调用方
payload = result["payload"]
```
8. 新增/整理**归一化 helper**（字段名必须在步骤 69 真实探测后最终确认；下列键名来自 2026-09-18 探测记录，仍须复核）：
   - `_normalize_work(work: dict) -> dict`：保留既有字段语义（`title`/`authors`/`abstract`/`doi`/`cited_by_count`/`download_url`/`arxiv_id`/`pubmed_id`），并把 `authors` 的取值改为**兼容 dict 与 str 两种元素形态**（不同端点返回的作者元素形态可能不一致：详情端点历史上出现过对象数组），其余字段**按步骤 69 实测结构增补**（如 `year_published`/`publisher`/`journals`/`data_providers`/`core_id`）。
   - `_normalize_output(output: dict) -> dict`：`title`/`doi`/`download_url`/`source_fulltext_urls`/`license`/`fulltext_status`/`repositories`/`sdg`/`year_published`/`data_provider_id`。
   - `_normalize_data_provider(provider: dict) -> dict`：`id`/`name`/`url`/`type`/`metadata_count`/`fulltext_count`（字段名以 F13/F12 实测为准）。
   - **三个归一化函数都不得把 `fullText` 写入返回值**——这是项目"只给元数据与链接"的硬边界；即便上游返回了也必须丢弃（现有 `_normalize()` 已如此，重构时不得回退）。

#### 验证方法
- `uv run python -c "from uniarticles.sources import core; print(core._is_core_id('171513974'), core._is_core_id('10.1038/nature12373'))"` 输出 `True False`。
- `uv run python -c "import uniarticles.sources.core as c; print(c.BASE_URL)"` 输出 `https://api.core.ac.uk/v3`。
- 静态检查：`rg -n "raise_for_status|_normalize\(" src/uniarticles/sources/core.py` 在本步骤结束时不再出现 `raise_for_status`（被 `_error_for` 取代）；`_normalize` 已按用途拆成三个函数且被步骤 71～75 调用。
- `create_server()` 后 `list_tools()` 仍为 **21 个工具**（本步骤不新增工具，仅重构）；`core_work_search_by_query` 的入参签名在本步骤结束时**尚未**改变（增强在步骤 71）。
- 已用真实 key 跑通至少一次 `GET /v3/search/works`，确认重构后 `items` 字段内容与重构前一致（对照 `_verify/tool_availability_check.py` 的 `core_work_search_by_query` 调用）。

#### 风险提示
- **重构与增强混在一起最容易出回归**：本步骤刻意不改变任何工具签名与输出字段；如执行中发现"顺手改一下更顺"，应放到步骤 71 之后单独进行，避免把签名变更混进纯重构导致难以定位回归来源。
- `_error_for()` 的 404 分支文案要能同时覆盖两类完全不同的 404：**记录不存在**（F10，空 `message`）与**端点不接受该标识符类型**（F11，DOI 打到 `/outputs`）。二者的区分在步骤 72 由调用方预校验完成，本步骤的兜底文案只是最后一道防线。
- `datetime.fromisoformat()` 在 Python 3.10 上对 `+0000`（无冒号时区）与 `Z` 的解析支持存在版本差异：代码必须 `try/except ValueError` 兜底为原样回显字符串，**不得**引入 `dateutil` 等新依赖（本项目坚持零新增依赖）。
- `httpx.AsyncClient` 每个工具各自开一次仍是既有模式（`scopus.py`/`pubmed.py` 均如此），本步骤沿用，不引入连接池/全局 client——避免在无自动化测试的项目里改变并发行为面。
- `_headers()` 在未配置 `CORE_API_KEY` 时不带 `Authorization`，属预期（匿名档可用）；不要因为"新工具都依赖 key"就改成缺失即报错——本项目所有工具无条件注册，缺失凭证只在**调用**时以 `_err` 表现。
- 本步骤**不要**改动 `sources/__init__.py` 的注册顺序或分组注释（CORE 仍在"v3.0.0 新增：通用检索型"分组内，文件级顺序不变）。

---

### 步骤 71：增强现有工具 `core_work_search_by_query`（v3.5.0，QA-R021 第 1 项）

#### 目标说明
这是 C 档中**唯一的"修既有缺陷"项**（其余 8 项都是纯新增），也是性价比最高的一项。现有实现的真实缺陷有两处，均有实测证据：

1. **性能浪费**：works 检索响应**默认内联 `fullText`**。实测 `GET /v3/search/works?q=machine learning&limit=25`（正是现工具的 `max_results` 上限）→ **676,692 字节 / 4.8 秒**，其中 `fullText` 占 **536,574 字符**，而 `_normalize()` 拿到之后又把整个字段丢弃。改用 `POST /v3/search/works` + `exclude:["fullText"]` 后同样 25 条 → **112,549 字节 / 2.8 秒**（体积约 1/6、耗时约六折）。
2. **能力上限偏低**：现有 `max_results` 被硬夹在 25（`bounded = max(1, min(max_results, 25))`），且没有分页参数；实测 `limit=100` 被 CORE 接受。

本步骤**保持工具名 `core_work_search_by_query` 与响应结构不变**（`items` 仍是 `_normalize_work()` 产出的列表），只新增可选参数、放宽上限、切换请求方式、改进错误文案——因此对现有调用方是**向后兼容的增强**，不需要 README 里的"破坏性变更"警示。

#### 具体操作
1. 把 `_search()` 从 GET 改为 POST，请求体按步骤 69 实测确认的字段拼装（下列为基准形态）：
```python
async def _search(query: str, max_results: int, offset: int = 0) -> dict:
    body = {"q": query, "limit": max_results, "offset": offset, "exclude": ["fullText"]}
    result = await _request("POST", "/search/works", query=query, json_body=body)
    if not result["ok"]:
        return result
    payload = result["payload"]
    items = [_normalize_work(w) for w in payload.get("results", []) or [] if isinstance(w, dict)]
    return _ok(query=query, items=items)
```
2. 工具签名增加一个**可选**分页参数（默认 0，保持既有调用方行为不变），并放宽上限：
```python
@server.tool()
async def core_work_search_by_query(query: str, max_results: int = 10, offset: int = 0) -> dict:
    """按关键词检索 CORE（全球开放获取聚合库）。

    query 支持 CORE 自身的查询语法（字段限定、布尔、范围、短语/关键词匹配）。
    max_results 上限 100（CORE 单次上限）；offset 用于翻页。返回体已剔除 fullText
    只保留题录与下载链接；无 Key 亦可用但限流严格（官方未认证档 100 tokens/天、
    10 次/分钟且不提供 fullText），配置 CORE_API_KEY 后为 1,000 tokens/天。
    """
    normalized_query = query.strip()
    if not normalized_query:
        return _err(query=query, message="query must not be empty")
    bounded = max(1, min(max_results, 100))
    bounded_offset = max(0, offset)
    try:
        return await _search(query=normalized_query, max_results=bounded, offset=bounded_offset)
    except Exception as exc:
        return _err(query=normalized_query, message=f"CORE 请求异常：{type(exc).__name__}: {exc}")
```
3. **同步更新 docstring 中的限流口径**——现有 docstring 写的"~5 requests before a ~10-minute rate-limit lockout"与官方现行 token 制不符，必须按步骤 70 的更正口径重写（如上方示例）。`README.md` / `README_EN.md` / `AGENTS.md` 中的同类表述在步骤 76 统一处理。
4. 注释里"without a key CORE locks out after ~5 requests for ~10 minutes"（`_search()` 内 429 分支的旧注释）删除或改写，改为指向 `_rate_limit_message()`；429 文案不再手写，统一由步骤 70 的 helper 产出。
5. 明确**不暴露** `stats=`（GET 端点的统计参数）与 `sort` / `filter` / `search_fields` / CSV 导出等 POST 字段：本轮范围内只加 `offset` 与 `exclude`；其余字段留待有真实需求时再评估，避免一次把工具参数面撑得过大（与 v3.2.0–v3.4.0"控制工具选择噪声"的取向一致）。

#### 验证方法
- `list_tools()` 中 `core_work_search_by_query` 的入参为 `query` / `max_results` / `offset`（`offset` 有默认值）；**工具总数本步骤后仍为 21 个**（本步骤只增强、不新增，总数从步骤 72 起才变化）。
- 真实调用对照（需 `.env` 中真实 key）：
  - `core_work_search_by_query(query="machine learning", max_results=25)` 的返回条数为 25，且耗时与响应体相较重构前明显下降（可用 `_verify/tool_availability_check.py` 的耗时输出对照；预期从约 4.8 s / 676 KB 降至约 2.8 s / 112 KB 量级）。
  - `core_work_search_by_query(query="machine learning", max_results=100)` 返回 100 条且**不报错**（旧上限会静默夹到 25，本条是新旧行为差异的直接判据）。
  - `offset=2` 与 `offset=0` 的前 2 条不重复（分页确实生效）。
  - 空 `query` 返回 `ok=False` 且 `error` 明确；`max_results=999` 被夹到 100；`offset=-5` 被夹到 0。
- 429 文案检查（可临时用无效 key 或连续请求触发）：错误信息包含 `HTTP 429`、可重试时间，且**不含**旧文案"~5 requests / ~10 minutes"。

#### 风险提示
- **`POST /v3/search/works` 对空 `query` 的行为未验证**：现有实现是在工具层先挡掉空串（`query must not be empty`），本步骤必须保留这道前置校验，不能依赖上游 400。
- **`exclude` 与 `offset` 的实际交互以步骤 69 的 F3/F4 为准**：若探测发现 `offset` 不被接受或与 `limit` 有额外约束，以探测结果调整参数名/边界，**不得**沿用文档字面描述硬写。
- 上限从 25 提到 100 会显著放大单次响应体（`exclude` 后 100 条仍可能达数百 KB），对 LLM 客户端的上下文是真实成本。docstring 必须明示"上限 100，请按需设置"，默认值仍保留 10。
- 若步骤 69 发现 `exclude` 在 POST 路径下**不生效**（与 GET 表现不同），应回退为"仍然剔除 `fullText` 但接受较大响应体"，并在 buildlog 如实记录——不得为了性能指标而编造已生效的结论。
- 本步骤**不得**改动 `source` 字段值（仍是 `"core"`）、不得改动 `_ok`/`_err` 的键集合，也不得删除 `arxiv_id`/`pubmed_id`/`cited_by_count` 等既有字段——这些字段是既有调用方的可见契约。

---

### 步骤 72：新增 works 维度 3 个工具（v3.5.0，QA-R021 第 2～4 项）

#### 目标说明
现有 CORE 工具只能"按关键词检索"，拿不到 CORE 自身的**作品详情**、**机构库实例**与**生命周期**。本步骤补齐这三个维度（C 档 (b) 层）：

- `core_work_detail_by_identifier`：给定一篇作品，取它的完整题录（含 `dataProviders` / `outputs` / `identifiers` 等检索结果里没有的字段）；
- `core_work_outputs_by_id`：取该作品在**各机构库中的版本实例**（同一篇论文的多个采集副本，含 `downloadUrl` / `license` / `fulltextStatus` / `dataProvider`）；
- `core_work_stats_by_id`：取生命周期时间戳（deposited / published / updated / accepted）。

三者的输入语义有**实测确认的差异**，必须在工具层就区分开，不能把上游 404 直接透传给调用方：

| 工具 | 接受的标识符 | 实测依据 |
|---|---|---|
| `core_work_detail_by_identifier` | **裸 DOI 或数字 CORE ID 均可** | `GET /v3/works/10.1038/nature12373` → 200；带 `doi:` 前缀写法 → **404 No route found**（前缀不通、裸 DOI 通） |
| `core_work_outputs_by_id` | **只接受数字 CORE ID** | `/works/{id}/outputs` → 200；`/works/{裸 DOI}/outputs` → **404** |
| `core_work_stats_by_id` | **裸 DOI 或数字 CORE ID 均可** | `/works/{裸 DOI}/stats` → 200（返回体含内部 CORE id） |

#### 具体操作
1. **`core_work_detail_by_identifier`**：
```python
@server.tool()
async def core_work_detail_by_identifier(identifier: str) -> dict:
    """按裸 DOI（如 10.1038/nature12373）或数字 CORE ID 取 CORE 作品详情。

    注意 DOI 必须使用裸写法，不要加 "doi:" 前缀（上游对前缀写法返回 404）。
    详情比检索结果多出 dataProviders / outputs / identifiers 等字段。
    """
    candidate = identifier.strip()
    if not candidate:
        return _err(query=identifier, message="identifier must not be empty")
    result = await _request("GET", f"/works/{candidate}", query=candidate)
    if not result["ok"]:
        return result
    payload = result["payload"]
    if not isinstance(payload, dict):
        return _err(query=candidate, message="CORE 返回了非预期的详情结构（不是单个对象）。")
    return _ok_one(query=candidate, item=_normalize_work(payload))
```
   已知边界：未知 DOI 的 404 响应体是**空 message**（`{"message":""}`），因此 `_error_for()` 的 404 文案（步骤 70）是兜底关键；本工具**不得**依赖上游 message 报错。
2. **`core_work_outputs_by_id`**：先在工具层做数字 ID 预校验，命中 DOI 时返回**可操作**的提示而不是 404：
```python
@server.tool()
async def core_work_outputs_by_id(identifier: str) -> dict:
    """取某个 CORE 作品在各机构库中的版本实例列表（未去重的采集副本）。

    identifier 必须是**数字 CORE ID**（如 171513974）；该子资源不接受 DOI，
    传入 DOI 会得到 404。若手上只有 DOI，请先用 core_work_detail_by_identifier
    取详情，再从 identifiers / core_id 字段拿到数字 ID。返回各项含 downloadUrl /
    license / fulltextStatus / dataProvider，可用于判断同一论文有多少机构库版本。
    """
    candidate = identifier.strip()
    if not candidate:
        return _err(query=identifier, message="identifier must not be empty")
    if not _is_core_id(candidate):
        return _err(
            query=candidate,
            message=(
                f"该端点只接受数字 CORE ID，收到 {candidate!r}。"
                "请先用 core_work_detail_by_identifier 按 DOI 取详情，"
                "再从返回的 identifiers / core_id 字段取得数字 ID 后重试。"
            ),
        )
    result = await _request("GET", f"/works/{candidate}/outputs", query=candidate)
    ...
    items = [_normalize_output(o) for o in _as_list(payload) if isinstance(o, dict)]
    return _ok(query=candidate, items=items)
```
   `_as_list(payload)` 是步骤 70 之外的**新增小 helper**（若响应是 `{"results": [...]}` 或裸列表两种形态之一，均能取出列表）——其确切形态由步骤 69 的 F8 决定，不得预先假设。
3. **`core_work_stats_by_id`**：DOI 与数字 ID 均可：
```python
@server.tool()
async def core_work_stats_by_id(identifier: str) -> dict:
    """取 CORE 作品的生命周期时间戳（deposited / published / updated / accepted）。

    标识符可为裸 DOI 或数字 CORE ID。返回体为单个对象（items 长度为 1）。
    """
    candidate = identifier.strip()
    if not candidate:
        return _err(query=identifier, message="identifier must not be empty")
    result = await _request("GET", f"/works/{candidate}/stats", query=candidate)
    if not result["ok"]:
        return result
    payload = result["payload"]
    if not isinstance(payload, dict):
        return _err(query=candidate, message="CORE 返回了非预期的时间戳结构。")
    return _ok_one(query=candidate, item=_normalize_work_stats(payload))
```
   `_normalize_work_stats()` 按 F9 实测键名提取（历史记录显示响应体约 126 字节，字段极少）；**不得**把 `id`/`core_id` 之外的推断字段写进返回值。
4. 三个工具的 docstring 都必须写明**接受哪种标识符**，这是本步骤最容易被 LLM 调用方踩坑的地方（DOI 打在 `/outputs` 上 404）；同时不要为了"统一"把 `core_work_outputs_by_id` 的参数也改名为 `identifier` 后假装三者等价。
5. 本步骤结束时 `list_tools()` 应为 **24 个**（21 + 3）。

#### 验证方法
- 真实调用（`.env` 中真实 key）：
  - `core_work_detail_by_identifier("10.1038/nature12373")` → `ok=True`，`items` 长度为 1，标题为 Nature 那篇论文的正确标题；
  - `core_work_detail_by_identifier("171513974")` → `ok=True`；
  - `core_work_detail_by_identifier("10.1000/does-not-exist-xyz")` → `ok=False`，`error` 中**不含**空字符串（走兜底文案）；
  - `core_work_outputs_by_id("171513974")` → `ok=True`，各项含 `download_url`/`license`/`fulltext_status`/`data_provider` 中至少若干键；
  - `core_work_outputs_by_id("10.1038/nature12373")` → `ok=False`，错误文案含"只接受数字 CORE ID"并指向 `core_work_detail_by_identifier`；
  - `core_work_stats_by_id("10.1038/nature12373")` 与 `core_work_stats_by_id("171513974")` 均 `ok=True`。
- 返回结构一致性：三个工具的响应键集合与其余全部工具完全一致（`ok`/`source`/`query`/`count`/`items`/`error`），`source` 恒为 `"core"`。
- `items` 中**不出现** `fullText` / `full_text` 键（硬边界回归检查）。

#### 风险提示
- **`/works/{identifier}` 与 `/works/{id}/outputs` 的标识符规则相反**（前者接受 DOI、后者只收数字 ID），这是本轮最容易写错的点；测试用例必须同时覆盖"DOI 打详情"与"DOI 打 outputs"两侧。
- 详情端点响应体较大（历史记录 27,681 字节），其中可能内联 `fullText`——归一化必须丢弃该字段；若发现去掉 `fullText` 后仍异常大，检查是否把 `outputs`/`dataProviders` 原样塞进了返回值（应只取 id/name/url 这类轻量子字段）。
- **不要给 `core_work_detail_by_identifier` 加 `doi:` 前缀自动补全**：实测前缀写法返回 404，自动补全反而会制造失败。
- `core_work_outputs_by_id` 的返回值是"版本实例"，**不是**"正文"；docstring 必须避免写成"获取全文"，否则会与项目硬边界的口径冲突，也误导 LLM 调用方。
- 若 F8 显示 outputs 列表是**分页对象**（含 `totalHits` 等），是否需要 `offset` 参数以步骤 69 结果为准；本步骤默认不加深，避免无依据的复杂化。

---

### 步骤 73：新增 `core_work_aggregate_by_query`（v3.5.0，QA-R021 第 5 项）

#### 目标说明
这是**本项目工具集中首次出现的 facet / 分布维度**——现有 9 个源的 21 个工具清一色是"检索列表"或"按标识符取单条"，没有任何工具能回答"某个主题的文献都发在哪些年/哪些期刊/哪些机构/哪些语言"。CORE 的聚合端点正好补上这个空档，且与检索类工具互补：检索给具体文献，聚合给分布画像。

本步骤的难点不在 HTTP（就是一次 POST），而在**响应形状与全局约定不一致**：聚合返回的是 `{"aggregations": {"yearPublished": {"2019": 575, ...}, ...}}` 这样的**字典嵌套**，而项目所有工具的 `items` 都是列表。如何在不破坏全局响应形状的前提下承载分布数据，是本步骤的核心设计点。

> **编号说明**：C 档候选清单里 works 维度是 3 项（第 2～4 项）、聚合是第 5 项，但 `goal.md` 把"聚合统计 + 机构库维度"合并表述为 (c) 层。本计划书按**实现特征**拆成两步（步骤 73 聚合 / 步骤 74 机构库与 output 详情），与 v3.0.0"按实现复杂度分批"的既有组织方式一致；步骤 73 因此不承载 `goal.md` 中某个单独的编号，属编号顺延而非新增范围。

#### 具体操作
1. 先依据步骤 69 的 F5/F6 **确证请求体**，再写死参数。基准形态（待 F5/F6 复核）：
```python
async def _aggregate(query: str, fields: list[str], top_n: int) -> dict:
    body = {"q": query}
    if fields:
        body["aggregations"] = fields          # 确切键名以 F6 实测为准
    result = await _request("POST", "/search/works/aggregate", query=query, json_body=body)
    if not result["ok"]:
        return result
    payload = result["payload"]
    aggregations = payload.get("aggregations") if isinstance(payload, dict) else None
    if not isinstance(aggregations, dict):
        return _err(query=query, message="CORE 聚合返回了非预期的结构（未找到 aggregations 字段）。")
    items = []
    for field, buckets in aggregations.items():
        if not isinstance(buckets, dict):
            continue
        ranked = sorted(buckets.items(), key=lambda kv: kv[1] if isinstance(kv[1], (int, float)) else 0, reverse=True)
        items.append({
            "field": field,
            "total_buckets": len(buckets),
            "top": [{"value": str(value), "count": count} for value, count in ranked[:top_n]],
        })
    return _ok(query=query, items=items)
```
2. 工具签名（`fields` 可选，留空表示让 CORE 返回其默认维度集；`top_n` 控制每个维度的取值条数，防响应体过大）：
```python
@server.tool()
async def core_work_aggregate_by_query(query: str, fields: list[str] | None = None, top_n: int = 10) -> dict:
    """按关键词统计 CORE 文献的分布（年 / 作者 / 机构 / 类型 / 期刊 / 语言 / 出版社）。

    返回的不是文献列表，而是每个维度的取值分布：items 的每一项对应一个维度
    （field / total_buckets / top[{value, count}]），top 按出现次数降序，最多
    取 top_n 条（默认 10，上限 50）。query 语法与 core_work_search_by_query 相同；
    fields 留空则由 CORE 决定返回哪些维度。
    """
    normalized_query = query.strip()
    if not normalized_query:
        return _err(query=query, message="query must not be empty")
    bounded_top = max(1, min(top_n, 50))
    normalized_fields = [f.strip() for f in (fields or []) if isinstance(f, str) and f.strip()]
    try:
        return await _aggregate(query=normalized_query, fields=normalized_fields, top_n=bounded_top)
    except Exception as exc:
        return _err(query=normalized_query, message=f"CORE 请求异常：{type(exc).__name__}: {exc}")
```
3. **`query` 字段的语义**在本工具中与其他工具不同：聚合工具没有"单条命中"，故 `query` 应回显**输入的关键词**（与检索工具一致），而 `count` 取 `len(items)` 即"返回的维度个数"。这一约定必须写进 docstring，避免调用方误以为 `count` 是文献数——**文献总量若需要，应从各维度 top 之外的 `totalHits` 类字段获取；该字段是否存在以 F5 实测为准**，存在则以 `total_hits` 之类的顶层扩展键补充（扩展键只能新增，不得改动既有 6 个键）。
4. `fields` 传入未知维度名时的行为（400 / 静默忽略）以 F6 为准；若上游 400，工具层应把错误文本原样透出并提示"维度名以 CORE 文档为准"。
5. 本步骤结束时 `list_tools()` 应为 **25 个**（24 + 1）。

#### 验证方法
- `core_work_aggregate_by_query(query="machine learning")` → `ok=True`，`items` 至少含 `yearPublished` 一个维度，且 `top` 内 count 降序。
- `core_work_aggregate_by_query(query="machine learning", fields=["yearPublished","publisher"], top_n=5)` → 返回维度数 ≤ 2、每个维度 `top` 长度 ≤ 5。
- `core_work_aggregate_by_query(query="", ...)` → `ok=False`，错误明确。
- 响应键集合仍为标准的 6 键（若新增 `total_hits` 之类的附加键，须在 buildlog 与 docstring 中显式记录为**新增扩展键**，且不得影响既有 6 键）。
- 实测耗时（历史记录约 1.4 秒）可接受，无长尾。

#### 风险提示
- **这是本轮唯一的"请求体从未被真实验证"的工具**。若步骤 69 的 F5/F6 表明聚合端点不可用（400/500/超时），本步骤**必须整体回退**：本轮范围缩减为 8 项、工具总数按 27 计，并在 buildlog 与范围小节中如实标注"聚合维度因上游不可用顺延"。**严禁**用猜测的请求体硬上线，或把失败包装成"偶发"。
- `aggregations` 字典的**规模不可控**：某些维度（如 `authors`）可能返回成千上万个桶。因此 `top_n` 截断是必需的，且 `total_buckets` 必须如实回传（让调用方知道被截断了），不得静默丢弃。
- 桶值可能是**数字**也可能是**字符串**（如年份 `"2019"`），排序前必须做类型判断，否则 `TypeError` 会让工具直接崩。
- 该端点消耗的 token 比普通检索高（官方口径"复杂查询约 3～5 token"），docstring 应提示按需使用；本步骤不要把它包装成"每次检索后自动调用"的组合工具。
- 不要把它命名为 `core_work_search_by_query` 的变体或给检索工具加 `aggregate: bool` 开关——独立工具 + 独立语义更符合本项目"一工具一职责"的既有风格。

---

### 步骤 74：新增机构库与 output 详情 3 个工具（v3.5.0，QA-R021 第 6～8 项）

#### 目标说明
本步骤补齐 C 档 (c) 层的剩余已实测可用端点。"机构库画像"是 CORE 相对其余 8 个源的独特价值——它能回答"某篇论文来自哪些机构库/期刊源"，而这条链路的可行性已端到端实测：`/v3/works/171513974` 的 `dataProviders` 字段给出 `[{"id":1630,"name":"Intellectum (Universidad de La Sabana)","url":".../v3/data-providers/1630"}]`，再取 `/v3/data-providers/1630` 返回 200。

| 工具 | 端点 | 语义 |
|---|---|---|
| `core_data_provider_search_by_query` | `GET /v3/search/data-providers?q=` | 按关键词检索机构库 / 期刊源 |
| `core_data_provider_detail_by_id` | `GET /v3/data-providers/{id}`（可选 `/stats` 与 `/outputs`） | 机构库详情、统计、其下 outputs |
| `core_output_detail_by_id` | `GET /v3/outputs/{id}` | 未去重的原始采集记录详情 |

**`work` 与 `output` 的语义区别必须在 docstring 中讲清楚**，否则 LLM 调用方会随机选用两者：`work` 是 CORE **去重后的作品级记录**（同一论文只一条），`output` 是**未经去重的原始采集信号**（同一论文在各机构库各有一条，含 `license`/`sdg`/`repositories`/`fulltextStatus`）。要"这篇论文的基本信息"用 works 系工具；要"这个采集副本的许可与仓库信息"才用 outputs 系工具。

#### 具体操作
1. **`core_data_provider_search_by_query`**：
```python
@server.tool()
async def core_data_provider_search_by_query(query: str, max_results: int = 10) -> dict:
    """按关键词检索 CORE 的机构库 / 期刊源（data providers）。

    返回各机构的 id / name / url / 类型与收录量统计；拿到 id 后可用
    core_data_provider_detail_by_id 查看详情与其下 outputs。
    """
    normalized_query = query.strip()
    if not normalized_query:
        return _err(query=query, message="query must not be empty")
    bounded = max(1, min(max_results, 100))     # 上限以步骤 69 的 F12 实测为准
    result = await _request("GET", "/search/data-providers", query=normalized_query, params={"q": normalized_query, "limit": bounded})
    if not result["ok"]:
        return result
    items = [_normalize_data_provider(p) for p in _as_list(result["payload"]) if isinstance(p, dict)]
    return _ok(query=normalized_query, items=items)
```
2. **`core_data_provider_detail_by_id`**：详情为主，`include_stats` / `include_outputs` 两个可选布尔控制是否附带子资源（默认都关，避免单次调用放大成三个请求）：
```python
@server.tool()
async def core_data_provider_detail_by_id(provider_id: str, include_stats: bool = False, include_outputs: bool = False) -> dict:
    """按数字 ID 取 CORE 机构库详情（可选附带统计与其下 outputs）。

    include_stats / include_outputs 会各追加一次上游请求（更慢、消耗更多 token），
    仅在确实需要时开启。机构库 ID 可从 core_data_provider_search_by_query 或
    core_work_detail_by_identifier 的 dataProviders 字段获得。
    """
    candidate = provider_id.strip()
    if not _is_core_id(candidate):
        return _err(query=provider_id, message=f"机构库 ID 必须是数字（收到 {candidate!r}）。")
    result = await _request("GET", f"/data-providers/{candidate}", query=candidate)
    if not result["ok"]:
        return result
    payload = result["payload"]
    if not isinstance(payload, dict):
        return _err(query=candidate, message="CORE 返回了非预期的机构库详情结构。")
    item = _normalize_data_provider(payload)
    if include_stats:
        stats = await _request("GET", f"/data-providers/{candidate}/stats", query=candidate)
        if stats["ok"]:
            item["stats"] = stats["payload"]           # 字段名以 F14 实测为准
    if include_outputs:
        outputs = await _request("GET", f"/data-providers/{candidate}/outputs", query=candidate, params={"limit": 25})
        if outputs["ok"]:
            item["outputs"] = [_normalize_output(o) for o in _as_list(outputs["payload"]) if isinstance(o, dict)]
    return _ok_one(query=candidate, item=item)
```
   子资源失败**不改变**主结果的成功状态（`ok=True`），但必须把失败原因写进该子键（如 `item["stats"] = {"ok": False, "error": ...}`），不允许静默吞掉——这是"部分成功"在既有 `_ok`/`_err` 二元结构下的处理方式，须在 docstring 与本步骤 buildlog 中说明。
3. **`core_output_detail_by_id`**：
```python
@server.tool()
async def core_output_detail_by_id(output_id: str) -> dict:
    """按数字 ID 取 CORE 的原始采集记录（output）详情。

    output 是**未去重**的原始采集信号（同一论文在各机构库各一条），含 license /
    sdg / repositories / fulltextStatus / sourceFulltextUrls 等字段；若只需要
    作品级信息，请改用 works 系工具（core_work_detail_by_identifier）。
    """
    candidate = output_id.strip()
    if not _is_core_id(candidate):
        return _err(query=output_id, message=f"output ID 必须是数字（收到 {candidate!r}）。")
    result = await _request("GET", f"/outputs/{candidate}", query=candidate)
    if not result["ok"]:
        return result
    payload = result["payload"]
    if not isinstance(payload, dict):
        return _err(query=candidate, message="CORE 返回了非预期的 output 结构。")
    return _ok_one(query=candidate, item=_normalize_output(payload))
```
   **这是本步骤唯一无条件纳入的**（`goal.md` QA-R021 明确标注"实测 200 可用，无条件纳入"）。
4. `_as_list()` / `_normalize_data_provider()` / `_normalize_output()` 的确切字段以步骤 69 的 F12～F16 为准；所有归一化函数同样**不得**写入 `fullText`。
5. 本步骤结束时 `list_tools()` 应为 **28 个**（25 + 3）。

#### 验证方法
- 真实调用：
  - `core_data_provider_search_by_query("university")` → `ok=True`，各项含 id 与 name；
  - `core_data_provider_detail_by_id("1630")` → `ok=True`，`items[0]` 含 `name`（预期为 Intellectum 相关机构库）；
  - `core_data_provider_detail_by_id("1630", include_stats=True, include_outputs=True)` → `ok=True`，`items[0]` 含 `stats` 与 `outputs` 两个子键；
  - `core_data_provider_detail_by_id("abc")` → `ok=False`，错误含"必须是数字"；
  - `core_output_detail_by_id("29197653")` → `ok=True`，含 `license` / `fulltext_status` / `repositories` 等字段中的若干；
  - 端到端链路：`core_work_detail_by_identifier("171513974")` → 取 `data_providers[0].id` → `core_data_provider_detail_by_id(<该 id>)` 两者均 `ok=True`。
- `items` 中不出现 `fullText`（硬边界回归）。
- 三个工具的响应键集合与其他工具一致，`source` 恒为 `"core"`。

#### 风险提示
- **子资源的"部分成功"是本步骤最容易被漏掉的语义**：`include_stats=True` 但上游 500 时，如果用 `_err` 直接返回，会把已经取到的机构库详情一起丢掉。必须按第 2 条实现"主结果成功 + 子键记录失败"，并在 docstring 里明说。
- **`/outputs` 的响应体极大**（历史记录：`q=machine learning&limit=2` → 81,738 字节；`limit=100` → 1,145,330 字节），因为 output 记录内联 `fullText`。`include_outputs=True` 的 `limit` 必须保守（示例取 25），且归一化必须丢弃 `fullText`。
- **`dataProviders` 的 `id` 是数字、`url` 是完整 API URL**，工具应接受数字 `id`（与 `_is_core_id()` 一致），不要接受 URL——URL 形态解析会引入无谓的脆弱性。
- 机构库 `type` 字段的取值集合（如 `Journal` / `Repository` / `Aggregator`）未在探测记录中穷举，归一化时按原值透传，**不要**自建枚举映射表。
- 不要把 `core_output_detail_by_id` 与 `core_output_search_by_query`（步骤 75，条件纳入）打包成"一步交付/一步回退"——两者纳入条件不同，回退时必须能独立处理。

---

### 步骤 75：新增 `core_output_search_by_query`（v3.5.0，QA-R021 第 9 项，**条件纳入**）

#### 目标说明
这是 C 档 9 项中**唯一带击杀条件**的一项，也是全轮证据链最特殊的一项：

- **失败证据**：creator 环境 `GET /v3/search/outputs` 两次 HTTP 500，上游 Azure Search 返回 `Invalid expression: The operand for a binary operator 'Equal' is not a single value`；
- **通过证据**：另一环境四种查询组合 4/4 全 200；第三个环境按 QA-R013 复测的三种组合（普通关键词 / `title:` 字段限定 / DOI 精确命中）**再次全部 200**——累计 **7 次连续 200、跨 2 个环境**；
- **判定**：按 QA-R013"不得凭单次结果定性失败"，证据足以支持纳入；但保留**击杀条件**——步骤 69 的 F17 或后续任何一次真实调用出现非 200，则该工具不纳入，其余 8 项不受影响。

**注意该工具与步骤 74 的 `core_output_detail_by_id` 是不同粒度**：前者按关键词检索一批原始采集记录，后者按 ID 取一条。两者都属 outputs 维度，但纳入条件相互独立。

#### 具体操作
1. 先读步骤 69 的 F17 结论，据此二选一：
   - **三种组合全部 200** → 按下方代码注册该工具，本版本工具总数按 **28** 计；
   - **任意组合非 200** → **不注册该工具**，在 `buildlog.md` 中记录失败证据（状态码 + 响应体摘要 + 请求形态），工具总数按 **27** 计；步骤 76 的文档同步与步骤 77 的计数一律按 27 执行。
2. 注册实现（仅在通过击杀条件时执行）：
```python
@server.tool()
async def core_output_search_by_query(query: str, max_results: int = 10) -> dict:
    """按关键词检索 CORE 的原始采集记录（outputs，未去重）。

    与 core_work_search_by_query 的区别：works 是去重后的作品级记录，outputs 是
    各机构库的原始采集信号（同一论文可能多条），适合按 DOI/标题精确定位某个机构的
    采集副本并查看其 license / fulltextStatus / repositories。上限 100，返回体已
    剔除 fullText。
    """
    normalized_query = query.strip()
    if not normalized_query:
        return _err(query=query, message="query must not be empty")
    bounded = max(1, min(max_results, 100))
    result = await _request(
        "GET", "/search/outputs", query=normalized_query,
        params={"q": normalized_query, "limit": bounded},
    )
    if not result["ok"]:
        return result
    items = [_normalize_output(o) for o in _as_list(result["payload"]) if isinstance(o, dict)]
    return _ok(query=normalized_query, items=items)
```
   **已知边界**：该端点历史上触发过上游 500（Azure Search 表达式错误），因此 `_error_for()` 的 5xx 分支文案必须直接可用——不要把 500 包装成"未知错误"，应透出上游 message 并提示"该端点对部分查询表达式不稳定，可改用 `title:"..."` / `doi:"..."` 限定写法或改查 works"。
3. 写入 docstring 的**稳定性提示**：说明该端点历史上对部分查询表达式出现过 5xx（属上游行为），建议用字段限定写法；这是对调用方的诚实告知，也是 QA-R013 记录的风险在工具层的显式表达。
4. **不得**为了"提高稳定性"自行加自动重试循环——重试会放大 token 消耗且掩盖真实失败；失败就按 `_err` 如实返回（与全项目其余工具一致，无任何重试逻辑）。
5. 本步骤结束时 `list_tools()` 为 **28 个**（通过）或 **27 个**（未通过）；两者都是本步骤的合法终态，取决于判定而非执行质量。

#### 验证方法
- `list_tools()` 工具数与本步骤第 1 条的判定一致（28 或 27），且 `core_output_search_by_query` 的出现/缺席与判定一致。
- 通过时的真实调用：
  - `core_output_search_by_query("machine learning", max_results=2)` → `ok=True`；
  - `core_output_search_by_query('doi:"10.1007/s10994-024-06619-7"', max_results=2)` → `ok=True` 且命中 1 条（历史记录为精确命中）；
  - 空 `query` → `ok=False`。
- 未通过时的记录要求：`buildlog.md` 中必须有"日期 / 环境 / 请求形态 / 状态码 / 上游响应体摘要 / 结论（不纳入）"六项，且明确写出"其余 8 项不受影响"。

#### 风险提示
- **击杀条件是硬约束，不得"再试一次看看"**：若 F17 出现非 200，反复重试直到碰上一次 200 再据此纳入，属于对 QA-R013 结论的选择性采信，明确禁止。判定应基于**首次**运行的完整结果。
- 该端点的响应体比 works 检索更大（`limit=100` 历史记录 1,145,330 字节），即使剔除 `fullText`，`max_results=100` 下的响应仍可能让 LLM 客户端上下文吃紧；docstring 与 README 应保留"上限 100，按需设置"的提示。
- **不要**因为该工具"条件纳入"就把它写成可选注册（依赖配置/环境变量）——本项目的工具集必须对每个客户端都一致（`goal.md` 与 `AGENTS.md` 都已把"配置相关的工具数可预测性"列为架构约束）。条件只决定**是否进入本版本的代码**，一旦纳入即无条件注册。
- 若未通过击杀条件，README 中"28/27"的计数与 CORE 工具表必须同步为"不含 outputs 关键词检索"，并在表格中**不出现**该行（不要留空行或注释行）。
- 该工具与 `core_work_search_by_query` 的 docstring 必须互相点明差异，否则 LLM 调用方会对同一查询随机二选一，直接损害工具选择的可预测性——这正是 v3.2.0–v3.4.0 三轮收缩试图解决的问题。

---

### 步骤 76：文档同步与既有口径更正（v3.5.0）

#### 目标说明
CORE 工具数由 1 变为 8（或含条件项 9），工具总数由 21 变为 27（或 28），同时 QA-R021 明确要求更正仓库内关于 CORE 限流与文档入口的失实表述。本步骤把代码变更与文档、回归脚本一次性对齐，避免留下"文档写了但代码没有"或"代码变了但文档没跟"的任何一侧不一致——这是本项目历次版本（v2.2.0 步骤 17、v2.3.0 步骤 23、v3.3.0 步骤 55）都特别点名过的高频事故点。

**计数一律以 `list_tools()` 返回值为准**，不得用 `rg -c "@server.tool"` 直接计数（历史上有注释中的该字符串导致虚高的先例，`goal.md` QA-R018 已明确禁止）。

#### 具体操作
1. **先确定本版本的实际工具数**：执行 `create_server()` → `list_tools()`，记下真实数量（预期 **27** 或 **28**）；后续所有计数改写以该值为准，**不得**在各文档里分别推算。
2. `README.md`（中文上位）与 `README_EN.md`（英文）逐处同步，**两份必须逐项对齐**：
   - 首段"**9 个数据源、21 个工具**" → "9 个数据源、**27/28 个工具**"（按实际值）；
   - §数据源总览后的"共提供 **21 个工具**"；
   - §API Key Requirements 表中 `CORE_API_KEY` 行的"（1 个工具）"→ CORE 实际工具数，并把"约 5 次请求后锁定约 10 分钟"改写为官方现行口径（未认证 100 tokens/天、10 次/分钟且不提供 `fullText`；配置 key 后 1,000 tokens/天、25 次/分钟），同时把"建议配置"提升为"使用 CORE 系工具时强烈建议配置"；
   - "即使一个 Key 都不配置，服务器仍会注册并暴露全部 **21** 个工具"这句中的数字；
   - `### CORE` 小节的工具表：由 1 行扩为完整工具表，逐行给出工具名 / 参数 / 说明，参数与 docstring 完全一致（含 `offset`、`fields`、`top_n`、`include_stats`、`include_outputs`）；
   - 工具总览段落"**共注册 21 个工具**"；
   - §故障排查或 FAQ 中任何提及 CORE 限流次数的句子（同样口径更正）；
   - "文献查找"推荐提示词小节中，把 CORE 的定位由"仅开放获取聚合源"补充为"另可给出分布统计（`core_work_aggregate_by_query`）与机构库画像（`core_data_provider_*`）"，使提示词与新增能力匹配。
3. `AGENTS.md` 同步（该文件已在版本控制中，属正常可提交文件）：
   - 项目概述段的"**9 data sources / 21 tools**"→ 实际值；并补一句说明 CORE 是本版本唯一被扩展的源（1 → 8/9 个工具）；
   - `.env` 配置段与"Registration is unconditional"段中 CORE 的限流口径更正为 token 制；
   - §Data sources and searchable scope 表格中 **CORE 行**由"1 — search"改为完整工具清单（工具名 + 端点 + 语义 + 上限），并把它与其余 8 个源的区别写清（全书唯一提供 facet 分布与机构库画像的源）；
   - **不要**改动本轮无关的源描述、也不要"顺手"更新其余源的 `USER_AGENT` 版本串（属既有漂移，按步骤 70 的说明留待独立事项）。
4. `_verify/tool_availability_check.py` 同步（该脚本被本地 `.gitignore` 遮蔽，搜索引用时须 `rg --no-ignore`）：
   - 现有第 107 行附近的三元组 `("core", "core_work_search_by_query", "max_results")` 与第 147 行附近的调用条目须扩展覆盖新增工具；
   - 新增条目应选择**低成本、稳定命中**的调用形态（例如 `core_work_detail_by_identifier("10.1038/nature12373")`、`core_work_stats_by_id("171513974")`、`core_data_provider_detail_by_id("1630")`、`core_output_detail_by_id("29197653")`），聚合工具用小 `top_n`；
   - **`core_work_aggregate_by_query` 是否纳入该脚本以步骤 69 的 F5/F6 结论为准**：若聚合端点在真实探测中可用则纳入，否则脚本中不得留会稳定失败的条目（回归脚本的失败必须意味着真回归）；
   - 若第 75 步判定"不纳入"，脚本中**不得**包含 `core_output_search_by_query` 条目。
5. `CLAUDE.md` 实际已不存在（仓库内无该文件，且 `.gitignore` 仍有 `CLAUDE.md` 一行、`pyproject.toml` 的 sdist `exclude` 仍列有 `/CLAUDE.md`，二者均为历史残留）——本项**跳过并在 buildlog 说明**，该 agent 指导角色已由 `AGENTS.md` 承担。**不得**为了"清理干净"而删除 `.gitignore` 或 `pyproject.toml` 中的这两条历史条目（属无关改动，超出本轮授权范围）。
6. `project-docs/teach.md` **不更新**（用户既有指示，已滞后多轮，属已知失真，非本轮缺陷）。
7. 全文一致性自查命令（结果贴入 buildlog）：
```powershell
rg -n "21 个工具|21 tools|共注册 21|9 个数据源、21" README.md README_EN.md AGENTS.md
rg -n "5 次请求|10 分钟|five requests|10-minute" README.md README_EN.md AGENTS.md src/uniarticles/sources/core.py
rg --no-ignore -n "core_work_search_by_query" _verify/tool_availability_check.py
```
   第一条应**零命中**（旧计数已全部替换）；第二条应**零命中**（旧限流口径已全部替换，且 `core.py` 内也不例外）；第三条应命中新增的全部 CORE 工具条目。

#### 验证方法
- 上述三条自查命令的结果符合第 7 条的预期（第一条零命中、第二条零命中、第三条覆盖全部新增工具）。
- 两份 README 的 CORE 工具表**逐行同名同参**（可把两段表格贴进 diff 工具核对）；两份 README 中出现的工具总数、数据源数数值完全相同。
- `AGENTS.md` 中 CORE 行的工具清单与 `list_tools()` 实际返回的 `core_*` 工具集合**逐一致**（数量与名称都对得上）。
- `rg --no-ignore -n "21 tools|21 个工具" .` 在仓库范围内（排除 `project-docs/`）零命中。

#### 风险提示
- **两份 README 的最容易漏点仍是"不显眼的计数"**：历史上 v2.2.0 步骤 17、v2.3.0 步骤 23、v3.3.0 步骤 55 三次都栽在"只改了显眼表格、漏了正文里的数字"。必须用第 7 条的全文检索穷尽检查，而不是只改看起来相关的那几行。
- **限流口径存在三个互不一致的官方来源**（token 档位表、`core.ac.uk/services/api` 页面的"每 10 秒 5 次"、以及实测响应头）。本轮统一采用 **token 档位 + 响应头实测** 这一组，理由是它是唯一能由代码在运行时读到的口径（`x-ratelimit-*` 响应头）。文档改写时不要引入第三套说法。
- `AGENTS.md` 当前把"21 tools"也写进了首段与表格两处，且表格里 CORE 行还有 `max_results ≤ 25` 的旧上限（步骤 71 已改为 100）——两处都必须改，只改一处会造成新的不一致。
- **`_verify/tool_availability_check.py` 的结果不是门禁**：它依赖真实网络与真实 key，个别源失败属正常（历史回归中 CORE 就曾受限流波动）。文档同步的通过判据是"条目与工具集合一致"，不是"脚本全绿"。
- 若步骤 75 判定"不纳入第 9 项"，README/AGENTS 的 CORE 小节中**不要留下**该工具的任何痕迹（含"暂不支持"之类的注释），否则会形成"文档承诺了但代码没有"的反向不一致。

---

### 步骤 77：版本号 `3.5.0` + `buildlog.md` 记录 + 整体回归验证（v3.5.0 交付检查点）

#### 目标说明
收尾步骤，与 `goal.md` QA-R021"开始更新计划书"之后无待定事项相衔接。本步骤把版本号提升、内部日志记录、全量回归三件事一次做完，构成 v3.5.0 的交付判据。

**版本号标注**：`3.5.0` 由 `goal.md` 记为"默认值，用户尚未逐字确认"。执行前若用户另有指定，只需替换两处字面值（见下），其余步骤不受影响——比照 v3.2.0 步骤 53 的既有处理方式。

#### 具体操作
1. **版本号提升**（仅两处字面值）：
```powershell
# pyproject.toml 第 7 行附近
version = "3.5.0"
# src/uniarticles/__init__.py 第 20 行附近
__version__ = "3.5.0"
```
   同时确认 `core.py` 的 `USER_AGENT` 已为 `UniArticlesMCP/3.5.0`（步骤 70 已处理）。
   **本次不发布到 PyPI**：发布属不可逆对外操作，须用户在场明确授权后才可执行（v3.4.0 步骤 68 已确立该硬门禁）。本版本默认只落到本地仓库与文档。
2. `project-docs/buildlog.md` 追加本轮记录，按既有格式（标题含日期与步骤号）逐条覆盖：
   - 步骤 69：真实探测结果表（F1～F17 的状态码/字节数/耗时摘要；聚合请求体确证形态；F17 的纳入/不纳入判定）；
   - 步骤 70：`core.py` 公共骨架重构要点（新增 helper 清单、`raise_for_status` 移除、限流口径更正）；
   - 步骤 71：`core_work_search_by_query` 增强的前后对照（**必须给出实测的响应体字节数与耗时**，对照历史 676,692 B / 4.8 s → 112,549 B / 2.8 s 量级）；
   - 步骤 72～75：每个新增工具的端点、参数、真实调用样例（含成功与失败各一例）；第 9 项的纳入/不纳入结论与依据；
   - 步骤 76：文档同步清单（改动的文件与计数）、三条自查命令的结果；
   - 步骤 77：版本号、工具总数、回归结果；
   - 结论区显式写明**工具总数（27 或 28）、CORE 单源工具数（8 或 9）、未发布状态**。
3. **整体回归验证**（本项目无自动化测试，沿用"启动 server → 枚举工具 → 真实调用"的手动惯例）：
```powershell
# 1) 工具清单与计数（以 list_tools() 为准）
uv run python -c "import asyncio; from uniarticles.server import create_server; s=create_server(); ts=asyncio.run(s.list_tools()); print(len(ts)); print(sorted(t.name for t in ts if t.name.startswith('core_')))"
# 2) 全量可用性回归（依赖真实网络与 .env 中的 key）
uv run python _verify/tool_availability_check.py
```
   第 1 条须输出 27 或 28，且 `core_` 前缀工具集合恰为本文档列出的 8 或 9 个；
   第 2 条允许个别源因网络/限流失败（历史回归中 CORE 与 arXiv 都曾波动），但**CORE 系新增工具中"稳定可用"的那几项不得全部失败**——若集体失败，先按 QA-R013 判断是本机网络问题还是实现问题，产出/复用 `_verify/` 脚本交用户复测，不得直接判定实现有误。
4. 更新 `README`/`AGENTS.md` 中若在步骤 76 之后仍有遗漏的版本号引用（`rg -n "3\.4\.0|3\.5\.0" README.md README_EN.md AGENTS.md pyproject.toml src/uniarticles/__init__.py src/uniarticles/sources/core.py`），确认没有把"上一版本号"错误地留在描述当前状态的句子里（历史版本号出现在 buildlog/`project-plan.md` 的历史记录中是**正常**的，不要改）。
5. **提交边界**（本仓库的文档角色分工约束）：本步骤的提交**只允许**包含本计划书新增/修改的 `project-docs/project-plan.md`（由 `project-planner-cn` 提交）与 `project-builder-cn` 执行期间的源码/文档改动（由其按自身工作流提交）。执行者不得把 `project-docs/goal.md`、`teach.md` 等其他角色的文件一并暂存或提交。

#### 验证方法
- `uv run python -c "import uniarticles; print(uniarticles.__version__)"` 输出 `3.5.0`；`pyproject.toml` 的 `version` 同为 `3.5.0`。
- `list_tools()` 计数与工具集合符合第 3 条第 1 项判据。
- `buildlog.md` 中本轮条目齐全（步骤 69～77 各一条，含实测数据而非仅结论），且结论区写明工具总数与"未发布"状态。
- 三条文档自查命令（步骤 76 第 7 条）在收尾后仍为零命中/覆盖完整。
- `git status --short` 中不出现 `project-docs/goal.md`、`project-docs/teach.md` 的暂存项。
- `dist/` 中不含 `3.5.0` 产物（本步骤不构建、不发布）。

#### 风险提示
- **不要把"版本号已提升"当成"已发布"**：PyPI 上 `3.5.0` 在本步骤结束时应当**不存在**；任何上传动作都须用户在场明确授权（同 v3.4.0 的门禁）。
- **回归失败不要急着改代码**：本项目历史上多次出现"agent 本机网络不通 → 误判端点失败"（dblp、arXiv、CORE 均有先例），步骤 3 已明确对应流程。任何因网络原因的重试都不得写入 `_err` 文案充当"修复"。
- 若步骤 75 判定不纳入第 9 项，则 `buildlog.md`、README、`AGENTS.md`、回归脚本四处都必须按 **27** 口径一致，任何一处残留 28 都会形成新的不一致。
- `pyproject.toml` 的 sdist `exclude` 中仍有已删除的 `/CLAUDE.md`（仓库内已无该文件）之类的历史条目，属无害冗余，**不属本步骤门禁**，可选清理（若清理须单独说明，不要顺手改动其他无关配置）。
- `project-docs/teach.md` 已滞后多轮，本轮**不更新**；如用户后续要求同步，须作为独立事项处理，不要夹带进本版本。
- 本步骤完成后，v3.5.0 的"待办"只剩"是否发布到 PyPI"一项，须在 buildlog 结论区显式列出，避免下一位执行者误以为本版本已完结发布。

---

- （v3.5.0，2026-09-19）步骤 69～77 基于 `project-docs/goal.md` QA-R021（commit `3eddd1e`，含《附录：CORE API v3 能力盘点》前置调研 + 三轮问答 + 第三个环境复测）追加。**本轮性质：单数据源（CORE）能力扩展 = 1 个既有工具增强 + 8 个新增工具**，其中 `core_output_search_by_query`（outputs 关键词检索）为**条件纳入**，带击杀条件（见步骤 75），因此工具总数的合法终态有两个：**27**（不含该项）或 **28**（含该项）。数据源集合保持 9 个不变，全部工具仍无条件注册，这一点与 v3.2.0–v3.4.0 三轮删源方向相反，但依据是"新增维度不与任何现有源重叠"（facet 分布、机构库画像在现有 21 个工具中完全没有对应物），属**新查询维度**而非"又一个关键词检索源"；该判断依据完整记录在"v3.5.0 范围补充"小节与 `goal.md` QA-R021 提炼结论中。
- **本轮最大的未验证点是聚合端点的请求体**：`POST /v3/search/works/aggregate` 的请求体 schema 从未被真实请求覆盖（现有 `_verify/core_api_probe.py` 只覆盖连通性与复测项），故把真实探测列为强制前置步骤 69（产出**新增**的 `_verify/core_api_field_probe.py`，不修改原 `core_api_probe.py`），并要求步骤 73 的归一化方案以探测结果为准；若聚合端点不可用，步骤 73 整体回退为 8 项范围并在 buildlog 如实记录。**严禁**用猜测的请求体硬上线。
- **步骤 70 的骨架重构是本轮唯一的"共享代码"步骤**，与 v3.0.0 步骤 34 的定位类似：先把限流头解析、标识符规则、错误分支、归一化函数集中处理，再让步骤 71～75 只写"参数校验 + 调用 + 归一化"。限流口径更正（"无 key 约 5 次请求后约 10 分钟锁死" → 官方现行 token 制 + 实测响应头）是 QA-R021 明确要求的**修既有缺陷**项，不是本轮新增能力，两条实施路径（`core.py` 与 `AGENTS.md`）须一并完成，不得只改代码不改文档。
- **"文件内容 / 下载"是硬边界**：`/v3/works/{id}/download`、`/v3/works/tei/{id}`、`/v3/outputs/{id}/download|raw|history` 全部不接入，用户已在 QA-R021 第 2 问明确否决"有限破例"与"允许下载 PDF"两档。C 档 9 项中没有任何一项触碰该边界；步骤 71 的 `exclude:["fullText"]` 只是不再**下载**一个本来就要被 `_normalize()` 丢弃的字段，与"不返回文件内容"不矛盾。
- **版本号 `3.5.0` 是默认值而非既定值**：`goal.md` 明确标注用户尚未逐字确认（v3.4.0 已发布，本轮为新 minor）。执行前若用户另有指定，只需替换 `pyproject.toml` 与 `src/uniarticles/__init__.py` 两处字面值，其余步骤不受影响。
- **本轮不发布 PyPI**：版本号提升与内部日志、回归验证完成后，v3.5.0 的剩余待办只有"是否发布"一项，须由用户在场明确授权（v3.4.0 步骤 68 已确立"发布属不可逆对外操作"的硬门禁）。
- **文档角色边界在本轮被特别强调**（步骤 77 第 5 条）：`project-docs/goal.md` 的范围章节按用户指示仍由 goal 定义角色维护，本轮由 `project-plan.md` 承载范围条目（`goal.md` QA-R021 已记录这一分工）；`project-planner-cn` 的提交只允许包含 `project-docs/project-plan.md`，不得暂存 `goal.md`、`teach.md`、`buildlog.md`（后者由 `project-builder-cn` 在构建期追加）。
- 步骤 1～68（v2.0～v3.4.0 构建，含已发布的 v3.4.0）已全部执行完毕；步骤 69～77 待 `project-builder-cn` 执行。

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

---

- （v3.1.0，2026-08-07）步骤 43～52 基于 `project-docs/goal.md` QA-R014/QA-R015 追加，源自用户重启此前作废的 QA-R009（v2.4.0 调研）遗留决策点——"PubMed 检索改为直连 NCBI Entrez API"。本轮是重构+新增混合性质的一次面向已发布工具的破坏性变更（用户已明确接受）：① 重写 `pubmed_paper_search_by_query`（新文件 `pubmed.py`，改为直接 `httpx` 调用 `esearch.fcgi`+`efetch.fcgi`，移除 `paperscraper`/`pymed-paperscraper` 依赖）；② 新增 3 个独立工具（`pubmed_paper_summary_lookup_by_pmids`/`pubmed_related_article_search_by_pmid`/`pubmed_pmc_linkage_lookup_by_pmid`，命名为本计划书拟定）；③ 新增 `NCBI_API_KEY` 可选环境变量，无条件注册模式（对齐 Elsevier/CORE 先例，非 Semantic Scholar 式条件注册）；④ 源码文件/注册函数名/README/CLAUDE.md/teach.md 引用同步改名，JSON 响应体 `source` 字段值由 `"paperscraper"` 改为 `"pubmed"`。目标版本号 `3.1.0`（当前 `3.0.0`），工具总数由 25/27 增至 28/30。
- 步骤 43（NCBI 5 个端点真实复测）是应 `goal.md` 明确要求新增的强制前置步骤——本轮大量决策依据已作废的 QA-R009 探测结论，探测发生在数日之前且从未对 EFetch 做过字段级抓包，比照 `_verify/dblp_field_probe.py` 先例产出诊断脚本到 `_verify/`（`goal.md` QA-R013 通用流程约束），步骤 45～48 的归一化字段方案均以该步骤的真实探测结果为准，不得凭空编写。
- 步骤 49 中"一并移除 `pandas` 依赖"是本计划书基于代码巡查（全仓库检索确认 `pandas` 仅被 `paperscraper.py` 一处引用）发现的衍生决策，`goal.md` 未逐字提及，已在步骤中明确标注来源，比照 v2.1.0 步骤 8"清理 `ARXIV_DOWNLOAD_DIR` 死配置"的处理先例，避免被误认为超出授权范围或临场发挥。
- 步骤 49.5 中 `src/uniarticles/__init__.py` 的 stdout 防御性代码是否随 `paperscraper` 依赖移除而简化，`goal.md` 已明确留给 `project-builder-cn` 按代码实际情况判断，本计划书给出两个可接受方案（保留作通用防御 / 简化移除）并倾向"保留"，但不代为拍板，要求最终选择与理由记入步骤 52 的 buildlog 记录。
- 步骤 1～42（v2.0～v3.0.0 构建）已全部执行完毕并发布，保留在文档中作为历史记录，不受本轮改动影响。

---

- （v3.2.0，2026-08-09）步骤 53 基于 `project-docs/goal.md` QA-R016 追加，源自用户直接、明确的范围收缩指令——移除 ChEMBL 与 HAL 两个数据源（理由：产品价值不足，"用处不大"，非技术不可行）。范围小而封闭，一步完成代码删除（`chembl.py`/`hal.py` 源文件 + `sources/__init__.py` 中对应 import/注册行）、验证（`create_server()` 工具数量核对）、README.md/README_ZH.md 同步更新、版本号提升。数据源规模由 15 个降为 13 个，工具规模由 28/30 降为 26/28。用户在本轮澄清中已明确确认将版本号一并 bump 至 `3.2.0`（当前 `3.1.0`），延续本项目"范围变更即 bump minor 版本号"的既有惯例。
- 与此前几轮删除性质变更（v2.1.0 QA-R003、v2.2.0 QA-R004）不同：本轮排除的 ChEMBL/HAL **均已实测确认可用**（非技术不可行），排除依据是用户对已发布范围的主观产品价值判断，`goal.md` 已特别标注这一性质区分，步骤 53 与 buildlog 记录中均需如实反映，不得误写为"技术不可行"。
- 步骤 1～52（v2.0～v3.1.0 构建）已全部执行完毕并发布，保留在文档中作为历史记录，不受本轮改动影响。

---

- （v3.3.0，2026-09-18）步骤 54～58 基于 `project-docs/goal.md` QA-R017 追加，源自用户"当前文献源有些太多了"的范围收缩意向。用户决策为"采用方案 A，并额外移除 Zenodo"，删源集合为 `biorxiv.py` / `dblp.py` / `zenodo.py` 三个源文件（各 1 个工具），数据源由 14 降为 11、默认工具由 26 降为 23（配置 `SEMANTIC_SCHOLAR_API_KEY` 时 28→25）。三个源的排除性质分属三类（biorxiv 上游 API 结构性不支持定向检索、dblp 可连接性不达标、zenodo 检索形态重复），与 QA-R016"产品价值收窄"、QA-R003"权限受限"、QA-R012"技术不可行"均不同，buildlog 记录不得混写。
- 步骤 55 的改动位置以"改动前行号 + 内容匹配"双条件给出（两份 README 的对应行号几乎逐行对齐）；历史上计数漏改已发生两次（v2.2.0 步骤 17、v2.3.0 步骤 23），故本步骤要求以全文检索数字的方式穷尽检查，而非只改显眼处。
- 步骤 56 涉及 `AGENTS.md`（当前 git 未跟踪）与 `CLAUDE.md`（被 `.gitignore` 忽略、不入库）两份 agent 指导文件：前者是用户上一轮明确要求维护的对象，后者的基线停在 v3.1.0（比代码落后两轮）。两文件均**不得 `git add`**，也不得改动 `.gitignore`；若用户对 `AGENTS.md` 另有安排，该步骤可整体跳过且不影响其余步骤。
- 步骤 57（版本号 `3.3.0`）标注为**待用户确认**：`goal.md` QA-R017 把版本号列为"仍未确认事项"，本计划书按既有惯例拟制为 `3.3.0`，但不等于获得授权；若否决，仅替换两处字面值。
- 候选步骤 59/60（三处默认排序修复）**默认不纳入本版本**，依据 QA-R017 明文记录；这是用户回答"部分工具无法直接检索到特定文献"的直接病根，本计划书以候选形式预置并保留充分细节，待用户确认后按既有"增量追加步骤"方式启用。
- `_verify/dblp_connectivity_test.py` / `_verify/dblp_field_probe.py` 在删源后**保留不删**，属本计划书的衍生决策（`goal.md` 未逐字提及），理由见步骤 54 风险提示（诊断脚本与"是否注册该源"无关、`AGENTS.md` 常设规则以其为标准范例、已按 `git add -f` 入库）。
- 步骤 1～53（v2.0～v3.2.0 构建）已全部执行完毕并发布，保留在文档中作为历史记录，不受本轮改动影响。

---

- （v3.4.0，2026-09-18）本轮计划书的追加由**性质不同的两部分**组成：
  - **步骤 61～65：事后补记（全部已完成）**。v3.4.0 的两轮删源（QA-R018 移除 Semantic Scholar、QA-R019 移除 OpenAlex）系用户直接指令，`goal.md` 已判定"不需要项目规划专家介入做分阶段设计，可由 project-builder-cn 直接执行"，故当时未走本计划书。为使计划书保持"完整构建记录"，此处按实际提交与 `buildlog.md` 条目回填。**编号依据**：步骤 61～64 沿用 project-builder-cn 已在提交信息与 `buildlog.md` 标题中使用的编号（不改写历史、避免交叉引用矛盾）；步骤 65 那一轮**时间上最早**（先于 61～64），因未获编号而以"补记"置于其后，其编号仅为本计划书的文档序号，**不代表执行顺序**。此约定须在后续再遇"直接指令型删源未经计划书"时沿用。
  - **步骤 66～68：本轮新增，尚未执行**，由用户本轮指令"补充之前的步骤并且增加修复 arXiv 的超时步骤，保持版本号为 3.4.0，修复好后清理 dist 并发布包"直接指定。
- **步骤 66 的缺陷来源与性质**：交付后独立复验（`buildlog.md` 2026-09-18 20:08）实测 arXiv 两个工具挂起 337.8s / 338.1s 后失败，追查出 `arxiv.Client` 不暴露任何超时参数这一真实缺陷。该缺陷**非本轮删源引入**，而是自 v3.0.0 引入 `arxiv` 包封装起既存的可用性问题，故如实标注为"修复既存缺陷"，不得写成删源的连带影响。根因与实现方案已在步骤 66 中逐条给出（含 `arxiv==2.4.1` 的代码行号证据），执行者不得凭印象另选实现（例如用 `socket.setdefaulttimeout()` 或全局改写 `requests` 行为——那会波及同进程内其余 8 个 `httpx` 源）。
- **版本号维持 `3.4.0`**（用户本轮明确指令）：`pyproject.toml` 与 `src/uniarticles/__init__.py` 已是 `3.4.0`，步骤 66/67 属同一**尚未发布**版本内的修复，不另开 `3.5.0`；已发布的 v3.3.0 不受影响。步骤 68 的"版本号核对"是**只读核对项**，执行时不得顺手 bump。
- **发布门禁（必须由用户解除，两项）**：① `pyproject.toml` 的 `license = { text = "MIT" }` 与 `LICENSE`（AGPL-3.0）、README 徽章（AGPL-3.0 + Commercial-Restricted）不一致，发布前须由用户确认目标许可证并对齐元数据；② 本机无 PyPI 凭据（`~/.pypirc` 不存在、`UV_PUBLISH_TOKEN` 未设置），需用户提供 token 并以环境变量传入。两项未解决前，步骤 68 的第 3～7 步不得执行——这与"发布属不可逆对外操作"的既有约束共同构成硬门禁，宁可推迟发布也不得先发后改。
- `project-docs/teach.md` 按用户指示**不更新**（现已滞后多轮，属已知失真，非本轮缺陷）；`AGENTS.md` 仍为 git 未跟踪状态，本轮同步其内容但**不得**将其暂存入库。
- 步骤 1～60（v2.0～v3.3.0 构建，含已执行的排序修复）已全部执行完毕；v3.3.0 已发布，v3.4.0 **尚未发布**。步骤 66～68 待 `project-builder-cn` 执行。
