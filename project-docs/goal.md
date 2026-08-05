# 项目目标文档

## 项目愿景
在 UniArticles v2.0 中，让 Elsevier（Scopus / ScienceDirect）能力覆盖从"检索文献"延伸到"评估文献所在期刊的质量/OA状态"和"获取文献的图表与补充材料"，且新增的每一项能力都以真实 API 调用验证过、在当前订阅等级下确实可用，不做"文档上存在但实际调不通"的空实现。

## 背景与动机
UniArticles（亿文通）是一个基于 Python + FastMCP 的学术文献检索 MCP Server，已封装 Scopus、ScienceDirect、ArXiv、PubMed、Google Scholar 等数据源为 MCP 工具，供 Claude Desktop / Cherry Studio 等 LLM 客户端调用。项目 v1.x 已收尾（最新提交："对文件夹结构进行了调整，准备进行v2.0.0的开发"），现规划 v2.0。

本轮目标聚焦于 Elsevier（Scopus / ScienceDirect）相关能力的扩展：通过对比 `docs/elsevier-documentation/` 下的官方 API 文档与当前已实现的 `src/uniarticles/sources/scopus.py`、`src/uniarticles/sources/sciencedirect.py`，识别出文档中存在但项目尚未实现的功能点，评估其对学术检索场景的价值，并明确 v2.0 中应纳入的具体目标。

## 核心目标
1. 新增 Serial Title（期刊信息查询）MCP 工具：给定 ISSN，返回期刊的出版商、Open Access 状态、期刊主页等元数据，帮助判断"这本期刊值不值得投/读"。
2. 新增 Object Retrieval（图表/补充材料获取）MCP 工具：给定文献标识符（DOI/PII/EID/PubMed ID），返回该文献关联的图片、表格、视频、补充材料等对象的元信息（文件名、mimetype、类型、下载链接）。
3. 两项新工具均以当前 SCOPUS_API_KEY 在真实调用中验证通过（HTTP 200）为前提落地，不实现已实测确认不可用或未经许可访问的功能。
4. 明确记录并对外暴露"哪些 Elsevier 能力当前订阅不支持"，避免用户误以为 MCP Server 支持了实际调不通的功能。
5.（v2.1.0，QA-R003）基于用户在真实 Cherry Studio 环境下对已发布 v2.0（2.0.1）全部 17 个工具的一轮完整实测（11 可用/6 不可用，见 `docs/调用错误分析报告.md`），删除 6 个确认不可用或超出产品定位的工具——`downloadPaper`、`searchAuthors`、`getAuthorProfile`、`searchSciencedirect`、`getArticleMetadata`、`searchScholarPapers`——将 MCP Server 收窄为 11 个稳定可用工具；同步修正 README.md / README_ZH.md 对 Elsevier Key 资质要求的描述，使其准确反映"非商业/无机构资质的基础 Elsevier Key 即可让删减后的全部剩余功能正常工作"这一实测结论，不做无实测依据的营销式表述。
6.（v2.3.0，QA-R007/QA-R008）基于调研本地参考项目 `reference-projects/elsevier-mcp-main/` 发现的候选功能，用真实 Elsevier Key 实测确认可用后，**新增两个 MCP 工具**：`serial_title_search`（期刊多条件搜索，接入 `content/serial/title`，不要求预先知道 ISSN，是现有 `scopus_serial_title_by_issn`的姊妹工具）与 `subject_classifications`（学科分类代码查询，接入 `content/subject/{scopus|scidir}`，全新概念，帮助用户查代码构造更精确的 Scopus 查询）。**这是纯新增（Additive）版本，不删除、不重命名、不改动现有 10 个工具的任何行为**，与 v2.1.0（删除故障工具）、v2.2.0（破坏性重命名+功能改造）性质均不同。

## 目标用户
使用 Claude Desktop / Cherry Studio 等 LLM 客户端、通过 UniArticles MCP Server 检索学术文献的科研人员/学生，且其机构订阅了基础级别的 Elsevier Scopus/ScienceDirect API 访问权限（非商业性质 Key，无 Insttoken）。

## 期望成果
- 用户在 LLM 客户端中检索到一篇文献后，可以直接追问"这本期刊是不是 OA/什么出版社"，由新的期刊信息工具直接给出答案，无需跳出对话去查期刊官网。
- 用户在 LLM 客户端中可以获取某篇文献的配图/补充材料清单及下载链接，用于快速预览文献的图表内容。
- v2.0 发布后，Elsevier 相关功能的"文档存在 vs 实际可用"差距被公开记录在案，为未来订阅升级后重新评估 Affiliation/Citation/Article Entitlement 等功能留出清晰的路径。

## 成功标准
1. 新增的 `get_serial_title`（或等价命名）工具能够对真实 ISSN 返回 200 响应并正确解析出出版商、OA 状态、期刊主页字段。
2. 新增的 `get_article_objects`（或等价命名）工具能够对真实 DOI/PII 返回 200 响应并正确解析出对象列表（至少包含文件名/类型/下载链接）。
3. 两项工具均遵循项目现有的 `_ok`/`_err` 统一响应结构，并有对应的空值/异常处理（无权限、未找到等情况返回清晰的 `error` 信息而非抛出未捕获异常）。
4. `docs/elsevier-documentation` 对照出的"实测不可用"清单（Affiliation Retrieval/Search、Citation Overview/Count、Article Entitlement、SciVal、Embase、Engineering Village、Nonserial Title）均未被纳入 v2.0 代码改动。
5. 项目内文档（如 README 或后续构建计划书）清晰说明这两项新工具的权限前提，避免使用了更高订阅等级 Key 的用户误以为功能上限止步于此。
6.（v2.1.0，QA-R003）`downloadPaper`、`searchAuthors`、`getAuthorProfile`、`searchSciencedirect`、`getArticleMetadata`、`searchScholarPapers` 六个工具对应的 `@server.tool()` 注册、私有实现函数、以及 `arxiv.py`/`scopus.py`/`sciencedirect.py`/`paperscraper.py` 中不再被引用的辅助代码被完整移除，仓库内（含测试、README 工具清单）不再残留对这 6 个工具名的引用。
7.（v2.1.0，QA-R003）删除后 MCP Server 实际注册的工具数量为 11 个，README.md / README_ZH.md 中的工具清单、表格、计数与代码实际注册的工具一一对应，不再出现"文档写了但代码没有/代码有但文档没写"的不一致。
8.（v2.1.0，QA-R003）README.md / README_ZH.md 中 Elsevier Key 的说明段落不再包含"您的机构必须购买了 Elsevier 的相关数据库服务，否则无法申请 API Key，亦无法使用相关功能"这类与实测结论相悖的表述，改为准确反映实测结论：非商业、无机构资质的基础 Elsevier Key 可在 Elsevier Developer Portal 个人免费申请，且能让删减后的全部 11 个工具正常工作；改写内容不超出实测证据范围，不新增未经验证的申请步骤/链接/承诺。
9.（v2.1.0，QA-R003）`pyproject.toml` 版本号更新为 `2.1.0`，`project-docs/buildlog.md` 记录本轮变更（工具删除 + README 修正）。
10.（QA-R004/QA-R005/QA-R006，源自 `docs/TODO.md` 两条待办）删除能正常工作但未公开宣传的兼容别名 `search_paper`；对删除后剩余的全部 10 个工具，按"数据源_对象_动作(_by_限定词)"语义化命名风格（用户选定的方案 A，如 `arxiv_paper_search_by_query`）做一次性彻底重命名（不设新旧名字并存的过渡期，旧工具名直接消失），其中 `get_quota_status` 的新名字按 QA-R006 用户要求由 `scopus_api_quota_status` 改为 `scopus_api_usage_status`；并把 `list_papers` 的实现从"无筛选拉取最新论文"补全为**真正支持按 arXiv category 过滤**，使其重命名后的新工具名（暗示 category 过滤能力）与实际功能一致。目标版本号已由用户在 QA-R005 确认为 **`2.2.0`**（否决了本 agent 建议的 3.0.0，理由是工具数量未净增加）。
11.（QA-R006，范围已确认，字段方案留待构建阶段真实探测）新增 `get_abstract_details`（`scopus.py`）与 `retrieve_article`（`sciencedirect.py`）两个工具的 JSON 归一化任务——当前两者均为 Elsevier 原始响应整体透传（`items=[response.json()]`），不像 `search_scopus`/`get_serial_title`/`get_article_objects` 那样做逐字段提取；归一化字段方案本身**不在本文档中给出**，需 `project-builder-cn` 先做真实 API 探测确认响应体字段结构（原因见约束条件），再由 `project-planner-cn` 在构建计划书中据实拟定提取字段。
12.（QA-R006，已确认）调整 `src/uniarticles/sources/__init__.py` 中 `register_all_sources()` 的文件级调用顺序，从当前的 `arxiv → scopus → paperscraper → sciencedirect` 改为 `scopus → sciencedirect → arxiv → paperscraper`（pubmed）；用户已明确选择"只要求文件级顺序"，不要求把 `scopus_api_usage_status` 从 `scopus.py` 的 `register()` 中拆出单独注册，`scopus.py` 内部各工具相对顺序维持不变。
13.（v2.3.0，QA-R007/QA-R008）`serial_title_search`（暂定名，最终名称由 project-planner-cn 在方案 A 命名风格下确认，本 agent 建议 `scopus_serial_title_search_by_criteria`）能够对真实检索条件（如 `title=Cell`）返回 200 响应并正确解析出 `serial-metadata-response.entry[]` 列表。
14.（v2.3.0，QA-R007/QA-R008）`subject_classifications`（暂定名，本 agent 建议 `scopus_subject_classification_lookup_by_source`）能够对真实 `source=scopus` 请求返回 200 响应并正确解析出 `code`/`description`/`detail`/`abbrev` 字段；`source=scidir` 分支需 project-builder-cn 补充真实探测后再确认字段一致性，不得凭空假设与 scopus 分支同构。
15.（v2.3.0，QA-R007/QA-R008）两个新工具均遵循项目现有的 `_ok`/`_err` 统一响应结构，且均放入 `src/uniarticles/sources/scopus.py`，不新建模块；MCP Server 工具总数由 10 个增至 12 个，不删除、不重命名任何现有工具。
16.（v3.0.0，QA-R010/QA-R011，已确认）新增全部 11 个通用学术检索数据源的 MCP 工具：Semantic Scholar、OpenAlex、Crossref、PMC、Europe PMC、DOAJ、CORE、Zenodo、HAL、dblp、OpenAIRE，每个数据源在 `src/uniarticles/sources/` 下建立独立脚本文件（复用现有"一数据源一文件、暴露 `register(server)`"的 source-module 模式）。用户在 QA-R011 明确选择"全部纳入"这一最大范围选项，且要求"对每一个源都进行真实性探测"、"先测试再说"（不预先排除或优先任何一个）——因此 11 个候选以同等地位进入真实 API 可行性验证环节，纳入前均需经真实探测确认端点可用性、限流表现、真实字段结构（延续本项目"真实验证优先"方法论，不得凭 README/代码逻辑直接假设可用）。
17.（v3.0.0，QA-R010，已确认）新增 bioRxiv、medRxiv 两个预印本数据源的 MCP 工具，明确其官方公开 API 本质是"按分类+时间窗口浏览"而非关键词全文检索，工具描述与文档需如实说明这一局限性，不得暗示支持任意关键词搜索。
18.（v3.0.0，QA-R010，已确认）新增 ChEMBL 数据源的 MCP 工具，产品语义为"给定一篇已知 DOI 的论文，查询其是否被 ChEMBL 收录及结构化 SAR/生物活性数据（IC50/MIC/Ki 等）"，是 DOI 输入型的文献关联数据查询，不是关键词检索工具，参数签名（`doi` 必填）与实现方式不应比照 Semantic Scholar/OpenAlex/Crossref 等关键词检索型工具设计。
19.（v3.0.0，QA-R010，已确认）为现有 `arxiv_paper_search_by_query`/`arxiv_latest_paper_list_by_category`/`arxiv_paper_detail_by_id` 三个工具的输出补充 `doi` 字段（复用第三方 `arxiv` 库 `Result.doi` 属性，零额外请求成本），列为本轮一个独立、可优先完成的步骤，不依赖新数据源接入进度。
20.（v3.0.0，QA-R010，已确认）目标发布版本号为 **`3.0.0`**，用户明确要求跳过此前遗留、尚未启动的 v2.4.0（`paperscraper.py` 改名等决策，原 QA-R009）；原 QA-R009 已由用户在主线程确认作废，对应内容已通过 `git revert c316c98`（提交 `d44d066`）从本文档移除。
21.（v3.0.0，QA-R012，已确认）承接 project-builder-cn 步骤 28-33 真实探测后交还用户判断的 4 项"技术可行但价值存疑"候选（Semantic Scholar、PMC、CORE、dblp，止损规则见约束条件 QA-R011 相关条目），用户逐项给出最终去留：**Semantic Scholar 纳入**（key 申请中，且需按 key 是否配置条件注册工具，架构影响见约束条件）、**PMC 排除**（未满足用户自设的"比 paperscraper 现有实现更稳定"条件，理由见范围界定/排除）、**CORE 纳入**（key 已配置在 `.env` 的 `CORE_API_KEY`，此前限流顾虑解除）、**dblp 暂缓**（探测环境 SSL 握手失败，待用户在其他网络环境下用分层诊断脚本复测后另开 QA-R013 定案，本轮不代为判定）。至此 v3.0.0 通用检索型新数据源范围收窄为：11 个候选中确认落地 10 个（原 3 个推荐重点候选 + 7 个中等价值候选，扣除 PMC）+ dblp 悬而未决，加上此前已单独确认的 bioRxiv/medRxiv、ChEMBL、arXiv 补 `doi` 字段。

## 范围界定
### 包含
- **Serial Title（期刊信息查询）**：接入 `content/serial/title/issn/{issn}`，实测 HTTP 200 可用，加入 `scopus.py`（或新建期刊相关模块，具体归属由后续构建计划书决定）。
- **Object Retrieval（图表/补充材料获取）**：接入 `content/object/{identifier_type}/{id}`，实测 HTTP 200 可用，加入 `sciencedirect.py`（或新建模块）。
- 以上两项对应的新 MCP 工具注册、参数校验、错误处理，遵循现有 `scopus.py`/`sciencedirect.py` 的代码风格（`_ok`/`_err`/`_get_headers` 等既有模式）。
- **（v2.1.0，QA-R003）删除以下 6 个已发布工具的代码与文档引用**，依据是用户在真实 Cherry Studio 环境下对 v2.0（2.0.1）全部 17 个工具的实测结果（`docs/调用错误分析报告.md`）+ 用户明确指示：

| 工具 | 所在文件 | 不可用/排除原因（用户确认） |
|---|---|---|
| `downloadPaper` | `src/uniarticles/sources/arxiv.py` | 代码层 AttributeError（`arxiv` 库 API 不兼容）；且用户明确将下载类功能排除出"以查询为主"的产品定位，即便修复也不恢复 |
| `searchAuthors` | `src/uniarticles/sources/scopus.py` | 实测 HTTP 401，用户确认为 Elsevier API Key 权限问题 |
| `getAuthorProfile` | `src/uniarticles/sources/scopus.py` | 实测 HTTP 401，用户确认为 Elsevier API Key 权限问题 |
| `searchSciencedirect` | `src/uniarticles/sources/sciencedirect.py` | 实测 HTTP 401，用户确认为 Elsevier API Key 权限问题 |
| `getArticleMetadata` | `src/uniarticles/sources/sciencedirect.py` | 实测 HTTP 401，用户确认为 Elsevier API Key 权限问题 |
| `searchScholarPapers` | `src/uniarticles/sources/paperscraper.py` | 实测请求超时，用户确认为网络访问受限（非权限问题） |

- **（v2.1.0，QA-R003）同步修改 README.md / README_ZH.md**：(1) Elsevier Key 资质要求说明段落，改为准确反映"非商业/无机构资质的基础 Key 即可让删减后的全部 11 个剩余工具正常工作"，并说明可在 Elsevier Developer Portal 个人免费申请；(2) 工具清单/表格/计数从 17 个同步更新为 11 个，覆盖 ArXiv(4)/Scopus(3)/ScienceDirect(2)/PubMed(1)/系统(1)。
- **（v2.1.0，QA-R003）`pyproject.toml` 版本号提升为 `2.1.0`**，`project-docs/buildlog.md` 记录本轮变更。
- **（QA-R004/QA-R005/QA-R006，全部已确认）删除 `search_paper` + 全部剩余 10 个工具一次性彻底重命名 + `list_papers` 功能补全 + 新增两处归一化任务 + 工具注册顺序调整**，依据是用户在 `docs/TODO.md` 提出的两条待办 + goal.md QA-R004/QA-R005/QA-R006 的澄清确认，目标版本号 **`2.2.0`**：
  1. **删除 `search_paper`**（`src/uniarticles/sources/arxiv.py`）：它是 `search_arxiv` 的纯别名，功能正常但从未公开列入 README，v2.1.0 曾被有意保留；本轮用户主动放弃该兼容别名，无过渡期，直接删除代码、注册与测试引用。
  2. **删除后剩余 10 个工具（`search_arxiv`/`list_papers`/`read_paper`/`search_scopus`/`get_abstract_details`/`get_serial_title`/`get_quota_status`/`search_pubmed_papers`/`retrieve_article`/`get_article_objects`）全部按方案 A 命名风格重命名**，一次性切换，旧名字不保留、不设别名过渡期。具体的新工具名、每个工具改动前后的请求体/返回体/参数/作用，由 project-planner-cn 在构建计划书中以表格形式逐一给出（要求详见"备注"交接说明）；其中 **`get_quota_status` 按 QA-R006 用户要求，新名字为 `scopus_api_usage_status`**（不是此前拟定的 `scopus_api_quota_status`），其余 9 个工具新名字维持已交付表格的方案 A 结果不变。
  3. **`list_papers` 功能补全**：新增真实的 arXiv category 过滤能力（不是仅改名字），实现方式需复用 arXiv 官方查询语法的 `cat:` 字段前缀拼接进 `query`，而不是新增 `arxiv.Search` 不存在的原生 `category` 参数，也不是客户端侧对全量结果做二次过滤（技术依据见备注）。
  4. **（QA-R006 新增）`get_abstract_details`/`retrieve_article` 归一化**：本轮范围扩大到把这两个工具的返回体从"Elsevier 原始 JSON 整体透传"改为像 `get_serial_title`/`get_article_objects` 一样做逐字段提取归一化，具体字段方案留待 `project-builder-cn` 做真实探测后由 `project-planner-cn` 补充（不在本文档中凭空定义字段，理由见约束条件）。
  5. **（QA-R006，已确认）工具注册顺序调整为文件级顺序**：`sources/__init__.py` 中 `register_all_sources()` 内四个 `register_xxx_source()` 调用顺序改为 `scopus → sciencedirect → arxiv → paperscraper`（pubmed）。用户已明确选择"只要求文件级顺序"，不要求把 `scopus_api_usage_status` 从 `scopus.py` 的 `register()` 中拆出单独最后调用，`scopus.py` 内部各工具（`search_scopus`/`get_abstract_details`/`get_serial_title`/`scopus_api_usage_status`）相对顺序维持文件内原有顺序不变，不需要跨文件拆分注册逻辑。
- **（v2.3.0，QA-R007/QA-R008，已确认）新增 `serial_title_search` + `subject_classifications` 两个工具**，依据是调研本地参考项目 `reference-projects/elsevier-mcp-main/` 后用真实 Elsevier Key 实测确认可用（探测记录见附录"实测可行性探测（2026-08-04，QA-R007 新候选项）"，commit `d9890f8`），用户明确指定版本号 `2.3.0`：
  1. **`serial_title_search`**：接入 `content/serial/title`（GET，query 参数：`title`/`issn`/`pub`/`subj`/`content`/`date`/`oa`/`start`/`count`/`view` 均为可选过滤条件，可任意组合），放入 `src/uniarticles/sources/scopus.py`（与同源的 `scopus_serial_title_by_issn` 放在一起，复用文件内既有的 `_get_headers()`/`BASE_URL`/`_ok`/`_err`），建议命名 `scopus_serial_title_search_by_criteria`（方案 A 风格；不用 `_by_title` 是因为端点支持多条件组合，避免重蹈 `list_papers` 命名与实现不符的覆辙）。
  2. **`subject_classifications`**：接入 `content/subject/{source}`（`source` 必填，取值 `scopus`/`scidir`；`description`/`detail`/`code`/`abbrev`/`field` 均为可选过滤条件），同样放入 `src/uniarticles/sources/scopus.py`（本 agent 判断：端点路径属通用 `content/subject/` 前缀而非 ScienceDirect 专属家族，且已有 `scopus_serial_title_by_issn` 放置通用 Elsevier 内容概念于 scopus.py 的先例；project-planner-cn 若认为应新建独立模块可提出并说明理由），建议命名 `scopus_subject_classification_lookup_by_source`（方案 A 风格）。
  3. **两个新工具的真实响应字段结构、建议命名的完整依据、以及尚未探测的参数边界**，均已详细记录在附录"实测可行性探测（2026-08-04，QA-R007 新候选项）"与 QA-R008 提炼结论中，project-planner-cn 编写构建计划书时可直接引用，不需要重新做探测。
  4. **本轮明确边界：v2.3.0 是纯新增（Additive）版本**，不涉及删除、重命名或修改现有 10 个工具（`scopus_document_search_by_query`/`scopus_abstract_detail_by_eid`/`scopus_serial_title_by_issn`/`scopus_api_usage_status`/`sciencedirect_article_retrieve_by_identifier`/`sciencedirect_article_object_by_identifier`/`arxiv_paper_search_by_query`/`arxiv_latest_paper_list_by_category`/`arxiv_paper_detail_by_id`/`pubmed_paper_search_by_query`）的名称、参数、返回结构或注册顺序，与 v2.1.0（删除）、v2.2.0（重命名+功能改造）在改动性质上完全不同，project-planner-cn 制定构建计划书时不应顺带评估或改动这 10 个现有工具。
- **（v3.0.0，QA-R010，部分已确认）新增数据源，均遵循现有 source-module 模式，在 `src/uniarticles/sources/` 下各建立独立脚本文件**，依据是调研本地参考项目 `reference-projects/paper-search-mcp-main/`、`reference-projects/research-superpower-main/` 后的核实结论（详见附录"实测可行性探测"章节新增小节）+ 用户在 QA-R010 的确认：
  1. **Semantic Scholar、OpenAlex、Crossref**（已确认纳入）：均为免费/公开、无需强制 key 的通用学术检索数据源，纳入前需 project-builder-cn 按本项目一贯方法论做真实 API 可行性验证（确认字段结构、限流表现），不得直接照抄参考项目的 Python 实现。
  2. **bioRxiv、medRxiv**（已确认纳入）：官方公开 API 语义为"按分类+时间窗口浏览"而非关键词全文检索，实现与文档需如实体现这一局限性，不能承诺关键词搜索体验。
  3. **ChEMBL**（已确认纳入，产品语义与其余数据源不同）：DOI 输入型的文献关联数据查询（查询已知 DOI 论文是否被 ChEMBL 收录及其结构化 SAR 数据），不是关键词检索工具，参数签名需以 `doi` 必填设计，不得比照关键词检索型工具的 `query`+`max_results` 模式。
  4. **PMC、Europe PMC、DOAJ、CORE、Zenodo、HAL、dblp、OpenAIRE**（QA-R011 已确认全部纳入探测环节）：这 8 个数据源在 QA-R010 中被评估为"中等价值"，此前只核实了 README 描述与代码逻辑、未做过真实 API 探测；用户在 QA-R011 明确要求"把 11 个候选源全部纳入"且"对每一个源都进行真实性探测"、"先测试再说"（不预先取舍），因此这 8 个与前 3 个推荐重点候选（Semantic Scholar/OpenAlex/Crossref）合计 11 个，以同等地位纳入探测环节。**探测完成后的最终去留结论见 QA-R012（核心目标第 21 条）**：Europe PMC、DOAJ、Zenodo、HAL、OpenAIRE 连同 Semantic Scholar/OpenAlex/Crossref 共 9 项已由 project-builder-cn 步骤 28-33 直接实测落地；CORE 因用户已配置 `CORE_API_KEY` 一并确认落地；PMC 已排除（见范围界定/排除）；dblp 因探测环境 SSL 握手失败暂缓，待用户另行网络环境复测后经 QA-R013 定案。
- **（v3.0.0，QA-R010，已确认）arXiv 三个现有工具补充 `doi` 输出字段**，复用第三方 `arxiv` 库 `Result.doi` 属性，零额外请求成本，作为独立步骤，可先于新数据源接入完成。
- **（v3.0.0，QA-R010/QA-R011，已确认）v3.0.0 立项之初范围合计规划新增 13 个数据源/功能点，是本项目至今规模最大的一轮版本**：11 个通用检索型新数据源（Semantic Scholar、OpenAlex、Crossref、PMC、Europe PMC、DOAJ、CORE、Zenodo、HAL、dblp、OpenAIRE）+ 2 个语义特殊的新数据源（bioRxiv/medRxiv 的浏览语义、ChEMBL 的 DOI 查询语义）+ 1 个现有工具增强（arXiv 三工具补 `doi` 字段）。**经 project-builder-cn 步骤 28-33 真实探测与 QA-R012 用户最终裁决后（详见核心目标第 21 条），13 个立项候选中已确认落地 11 个**（OpenAlex、Crossref、Europe PMC、DOAJ、Zenodo、HAL、OpenAIRE、bioRxiv/medRxiv、ChEMBL 共 9 个经真实探测直接落地，Semantic Scholar、CORE 经 QA-R012 用户裁决补充确认落地）+ **arXiv 补 `doi` 字段独立落地**，**明确排除 1 个（PMC）**，**悬而未决 1 个（dblp，等用户提供新网络环境探测结果后经 QA-R013 定案）**。project-planner-cn/project-builder-cn 制定后续文档时应引用 QA-R012 的最新结论作为范围现状，不再引用立项之初的"13 个"作为最终交付数量的等价表述。

### 排除
| 功能 | 排除原因 |
|---|---|
| Affiliation Retrieval（机构档案检索） | 实测 401 AUTHORIZATION_ERROR，当前订阅权限不足 |
| Affiliation Search（机构搜索） | 实测 401 AUTHORIZATION_ERROR，当前订阅权限不足 |
| Citation Overview（逐年引用趋势） | 实测 403 AUTHENTICATION_ERROR，当前订阅权限不足 |
| Citation Count Metadata（批量总被引次数） | 实测 403 AUTHENTICATION_ERROR，当前订阅权限不足 |
| Article Entitlement（ScienceDirect 全文权限探测） | 实测 403 AUTHENTICATION_ERROR，当前订阅权限不足 |
| SciVal APIs | 实测 403 ENTITLEMENTS_ERROR；根因是该资源仅对商业性质的 Elsevier 开发者 Key 开放，当前 Key 为非商业性质，账号类型不满足 |
| Embase APIs | 用户明确不需要；且需单独向 Elsevier 申请，与现有订阅无关 |
| Engineering Village APIs | 用户明确不需要；且需 EV 订阅 + 联系支持单独启用 |
| Nonserial Title（图书/专著元数据） | 用户产品定位不关注图书/专著检索场景，直接排除，不再深究 404 的技术性质 |
| TDM Service（批量文本挖掘授权） | 本轮未讨论，非新端点而是使用条款/注册流程，超出本次范围 |
| PlumX Metrics（`analytics/plumx/{id_type}/{id_value}`，替代计量学指标） | （QA-R007，2026-08-04 实测）401 AUTHENTICATION_ERROR，与 SciVal 同属 `analytics/` 前缀资源，当前非商业 Key 无法访问 |
| ScienceDirect 全文纯文本变体（同一 `content/article/{id_type}/{id}` 端点，`Accept: text/plain`） | （QA-R007，2026-08-04 实测）固定返回 400 INVALID_INPUT（与 view 参数取值无关，含不传 view），而同端点 `Accept: application/json`/`text/xml` 均正常 200；非新能力，是已实现端点 `sciencedirect_article_retrieve_by_identifier` 的响应格式变体，JSON 归一化已覆盖等价信息，不值得为此单独投入 |
| Unpaywall（v3.0.0，QA-R010） | 代码核实其检索本质是"给定 DOI 查开放获取全文位置"的单条查找，非关键词检索，产品语义属于全文下载兜底工具，与本项目已排除的下载类功能高度相关；用户在 QA-R010 认可排除 |
| Sci-Hub（v3.0.0，QA-R010） | 项目自身声明合规风险因司法辖区而异，非本项目产品定位所涉及；用户在 QA-R010 认可排除 |
| IEEE Xplore（v3.0.0，QA-R010） | 代码核实即便配置 API key，`search()` 仍无条件 `raise NotImplementedError`（含未完工的 TODO 注释），是作者自己也未写完的空壳，不构成真实可用功能；用户在 QA-R010 认可排除 |
| ACM Digital Library（v3.0.0，QA-R010） | 同 IEEE Xplore，`search()` 同样是无条件 raise 的空壳，未真实实现；用户在 QA-R010 认可排除 |
| SSRN（v3.0.0，QA-R010） | 参考项目 README 明确标注 403 bot-detection，不稳定；用户在 QA-R010 认可排除 |
| CiteSeerX（v3.0.0，QA-R010） | 参考项目 README 明确标注端点间歇性不可用/重定向到网页存档，不稳定；用户在 QA-R010 认可排除 |
| BASE（v3.0.0，QA-R010） | OAI-PMH 接口需机构 IP 注册才能返回实际结果，个人/非机构用户几乎不可用；用户在 QA-R010 认可排除 |
| Google Scholar（v3.0.0，QA-R010，重申） | 本项目 v2.1.0 已因网络访问受限删除过同类工具（`searchScholarPapers`），参考项目同样标注 bot-detection 问题，无新证据支持重新评估；用户在 QA-R010 认可排除 |
| PMC（v3.0.0，QA-R012） | 用户设定排除/纳入的判断条件为"若 PMC 实现比现有 `paperscraper.py` 依赖的第三方 API 更稳定，则考虑做"。技术核实：`paperscraper.py` 的 `_search_pubmed()` 底层调用 `paperscraper.pubmed.pubmed.get_pubmed_papers`，实质是对 NCBI Entrez 官方 API（`esearch`/`efetch`）的封装，并非真正的网页爬虫；候选 PMC 走的同样是 NCBI Entrez API（`esearch`/`esummary?db=pmc`），与现有 pubmed 工具是同一套后端基础设施，仅 `db` 参数从 `pubmed` 换成 `pmc`。因此 PMC 相较现有实现**没有稳定性提升**，唯一区别是内容范围收窄（PMC 仅覆盖全文开放获取子集，现有 pubmed 工具覆盖范围更广，含非开放获取文献摘要）。用户自设条件未成立，故排除，不纳入 v3.0.0 落地范围 |

## 约束条件
- 当前 `SCOPUS_API_KEY` 为**基础级别、非商业性质**的 Elsevier 开发者 Key，未配置 `X-ELS-Insttoken`（机构令牌）。
- 该订阅等级下，Scopus Search 的 `COMPLETE` 视图也会返回 401（实测确认），意味着账号整体权限受限，不止是本次新增的两项功能。
- 遗留风险（非本次 v2.0 范围改动，但需在后续构建计划书中知悉）：现有 `get_abstract_details` 默认 `view=META_ABS`、`retrieve_article` 默认 `view=META_ABS`，这两个默认 view 在 Elsevier 文档中被标记为需要机构订阅/entitlement 的受限视图，当前账号权限下调用可能拿不到完整内容。是否在 v2.0 中一并调整默认 view 或增加权限不足时的降级提示，留待构建计划阶段评估。
- 若未来用户订阅等级提升（获得机构订阅/商业 Key/Insttoken），本文档"排除"清单中的功能可重新评估纳入，无需重新走一遍可行性摸底——已有的实测方法（临时脚本探测真实端点）可复用。
- **（v2.1.0，QA-R003）`downloadPaper` 的删除是产品定位性约束，非临时性技术债**：即便未来 `arxiv` 库的 `AttributeError` 被修复，也不应仅因为"代码能跑了"就自动恢复该工具；如果要重新引入下载能力，需要作为一次新的、独立的目标澄清（说明为什么下载功能重新符合产品定位），而不是顺带恢复。
- **（v2.1.0，QA-R003）`searchScholarPapers` 的删除原因是用户确认的网络访问受限**（不是 Elsevier API Key 权限问题），与其余 5 个工具的删除原因（`downloadPaper` 除外）不同，特此分开记录，避免后续误将其归因为"权限不足"。
- **（v2.1.0，QA-R003）本轮目标（工具删除 + README 修正）对应的发布版本号为 `2.1.0`**（当前 `pyproject.toml` 为 `2.0.1`），采用新增功能/范围调整级别的版本号而非 patch 号，因为该变更包含移除已发布公开工具接口这一对使用者可见的破坏性变更。
- **（v2.1.0，QA-R003）执行分工**：本 agent（project-creator-cn）仅负责将上述决策写入本文档；实际的代码删除（`arxiv.py`/`scopus.py`/`sciencedirect.py`/`paperscraper.py` 及对应测试）与 README.md/README_ZH.md 文案修改，需要移交给 `project-planner-cn` 制定构建计划书，再由 `project-builder-cn` 落地执行并更新 `project-docs/buildlog.md`。
- **（下一轮，QA-R004）重命名是无过渡期的一次性破坏性变更，用户已知情并接受**：不做新旧名字并存、不做 deprecated 别名、不做兼容层，任何硬编码旧工具名（含已删除的 `search_paper`）的外部提示词/工作流会在新版本发布后立即失效，这是用户主动选择的方案，不属于遗留风险，无需后续版本中"补救式"恢复旧名字。
- **（QA-R005，已确认）本轮目标发布版本号为 `2.2.0`**：本 agent 曾判断"删除+破坏性重命名+功能新增"三者叠加，按语义化版本规范倾向于用主版本号（如 `3.0.0`），但用户明确否决并拍板 `2.2.0`，理由是本轮改动没有净增加工具数量。project-planner-cn/project-builder-cn 后续统一使用 `2.2.0`，不再讨论 `3.0.0`。
- **（下一轮，QA-R004，技术核实，供 project-planner-cn 参考）`list_papers` category 过滤的实现方式**：已实际读取当前项目 `.venv` 安装的 `arxiv` 库（版本 3.0.0，`arxiv.Search.__init__`）源码确认，其构造参数仅有 `query`/`id_list`/`max_results`/`sort_by`/`sort_order`，**不存在独立的 `category` 参数**；当前 `arxiv.py` 的 `list_papers` 实现（第 82-98 行）传入固定 `query="all"`，因此完全没有分类过滤。要让新工具真正支持按 category 过滤，正确做法是复用 arXiv 官方 API 的查询语法——用 `cat:` 字段前缀构造 `query` 字符串（例如 `cat:cs.AI`，多个分类可用 `OR` 组合），传给现有的 `arxiv.Search(query=..., sort_by=SubmittedDate)` 即可拿到"某分类下最新论文"的效果，无需修改 `arxiv` 库本身、也无需在客户端对全量结果做二次内存过滤。project-planner-cn 编写构建计划书时应按"拼接查询字符串复用官方查询语法"这一方式规划实现步骤和参数校验（例如 `category` 参数格式校验、非法分类码的错误处理），而非假设需要升级依赖库或自研过滤逻辑。
- **（下一轮，QA-R004，交接给 project-planner-cn 的表格要求）用户明确要求构建计划书中必须包含一张覆盖以下 6 个维度的工具改动清单表格，逐一覆盖删除后剩余的全部 10 个工具（不含已确认删除的 `search_paper`）**：
  1. 改动前工具名
  2. 改动后工具名（遵循方案 A 命名风格）
  3. 请求体（入参签名/参数列表）
  4. 预期返回体（沿用现有 `_ok`/`_err` 统一结构时，`items` 内的字段结构是否随之变化，需明确写出）
  5. 作用（一句话说明该工具做什么、对接哪个数据源的哪个端点）
  6. 允许的参数（含默认值、取值范围/枚举、是否新增参数——例如 `list_papers` 新增的 `category` 参数）
  project-planner-cn 在制定构建计划书时不得省略此表格或简化维度，这是用户在本轮 QA 中明确提出的交付格式要求。
- **（QA-R006）`scopus_api_usage_status` 命名确认**：`get_quota_status` 的新名字最终确认为 `scopus_api_usage_status`（用 usage 替代此前拟定的 quota），交付表格中其余 9 个工具的新名字维持不变。
- **（QA-R006，前置事实核实：归一化任务不能凭空编字段）`get_abstract_details`/`retrieve_article` 归一化缺少真实响应体字段样例，需先做真实探测**：核实 `project-docs/buildlog.md` 136-141 行，此前 v2.0 阶段的实测只确认了这两个端点在 `view=META` 下返回 **HTTP 200** 及**响应根对象名**（Scopus 侧为 `abstracts-retrieval-response`，ScienceDirect 侧为 `full-text-retrieval-response.coredata`），并未记录完整的字段级结构；对比之下 `get_article_objects` 的归一化在 `buildlog.md` 161-163 行有完整的真实抓包字段清单（`attachment[]` 各字段及可选性）可直接复用。因此 `get_abstract_details`/`retrieve_article` 的归一化字段方案**当前无法在 goal.md 或构建计划书中直接凭空定义**，必须先由 `project-builder-cn`（或构建前的探测步骤）用真实 `ELSEVIER_API_KEY` 对两个端点各发起真实请求、拿到完整响应体样例后，才能确定要提取哪些字段、哪些字段是可选的——这是本项目一贯的"真实验证优先"原则（同 QA-R001/QA-R002 对 Elsevier 端点可行性的处理方式）的延续。project-planner-cn 编写构建计划书时应把"真实探测 → 确定字段 → 编写归一化代码"列为该任务的显式前置步骤，不能跳过探测直接写归一化实现。
- **（QA-R006，已确认）工具注册顺序调整的实现粒度已由用户明确选择为"文件级顺序"**：`src/uniarticles/sources/__init__.py` 的 `register_all_sources()` 内四个 `register_xxx_source()` 调用顺序改为 `scopus → sciencedirect → arxiv → paperscraper`（pubmed）即可；用户明确不要求把 `scopus_api_usage_status` 从 `scopus.py` 的 `register()` 中拆出单独调用，`scopus.py` 内部工具相对顺序不变，不需要跨文件拆分注册逻辑。这是比"全局工具注册顺序精确匹配"更轻量的方案，project-planner-cn/project-builder-cn 按此实现即可，无需再评估拆分注册逻辑的方案。
- **（v2.3.0，QA-R007/QA-R008）`serial_title_search`/`subject_classifications` 的真实探测尚未覆盖全部参数边界，构建阶段需先补测再写实现，不得凭空补全**：QA-R007/QA-R008 的真实探测各只验证了一种最基础的调用组合（`serial_title_search` 只测了单一 `title` 条件；`subject_classifications` 只测了 `source=scopus` 分支）。以下细节明确标注为"未探测"，project-builder-cn 在正式构建阶段需先用真实 Elsevier Key 补测，再据实确定参数校验/归一化字段，不能照抄参考项目 `reference-projects/elsevier-mcp-main/` 的 Zod schema 假设（那是别的项目自己的实现选择，不代表 Elsevier 服务端真实行为）：
  1. `serial_title_search`：`issn`/`pub`/`subj`/`content`/`date`/`oa`/`start`/`count`/`view` 参数逐一的真实调用效果；不带任何检索条件时服务端的真实行为（拒绝还是返回全量）；`count` 的服务端真实上限是否为 200；无效 `subj` 学科代码的错误响应。
  2. `subject_classifications`：`source=scidir`（ScienceDirect 学科分类）分支的真实响应字段结构（不能假设与已验证的 `source=scopus` 分支同构）；`code`/`abbrev`/`field` 精确过滤参数的真实效果；`source` 传入非法值时的错误响应；不带过滤条件、只传 `source` 时的响应体量级（是否需要分页提示）。
  3. 两工具的错误处理边界（无效标识符/无匹配结果/权限不足）均未真实触发过，需按项目现有 `_ok`/`_err` 规范真实测试后再确定归一化降级行为。
- **（v2.3.0，QA-R007/QA-R008）本轮新增工具建议命名（`scopus_serial_title_search_by_criteria`、`scopus_subject_classification_lookup_by_source`）为本 agent 拟定，非不可更改的最终方案**：project-planner-cn 若在构建计划书阶段认为有更贴切的命名，可以调整，但须说明理由，并保持 v2.2.0（QA-R004）已确认的"数据源_对象_动作(_by_限定词)"方案 A 命名风格不变，不得引入新的命名规则或退回方案 B。
- **（v3.0.0，QA-R010，已确认）ChEMBL 的产品定位差异需要在构建阶段被严格遵守**：不得按论文关键词检索工具的参数模式（`query`+`max_results`）设计，必须是 `doi` 必填的查询工具，语义为"这篇论文是否被 ChEMBL 收录及其结构化数据"。project-planner-cn/project-builder-cn 需在构建计划书/实现中明确标注这一差异，避免与其他新增数据源工具的参数模式混淆。
- **（v3.0.0，QA-R010，架构提示，非强制要求）新数据源数量已确认达到 11 个（通用检索型）+ 2 个（语义特殊型），`src/uniarticles/sources/__init__.py` 的 `register_all_sources()` 调用列表会明显变长**，project-planner-cn 制定构建计划书时可以考虑相应的组织方式（例如分组注释、保持固定排序规则），但用户未要求现在就设计解决方案，不强制在本轮给出方案。
- **（v3.0.0，QA-R010/QA-R011，已确认）全部 11 个通用检索型新数据源纳入前必须先做真实 API 可行性验证，不得直接照抄参考项目的实现假设**：QA-R011 中用户明确要求"对每一个源都进行真实性探测"，不区分此前 QA-R010 里"推荐重点候选"与"中等价值候选"的分档——即便是核实较深的 Semantic Scholar/OpenAlex/Crossref，也只是代码级核实（读过参考项目源码），并未做过针对本项目 `.env` 环境的真实请求验证，同样需要真实探测。project-builder-cn 在正式开发前需延续本项目一贯的"真实验证优先"方法论（同 QA-R001/QA-R002 对 Elsevier 端点、QA-R007 对新候选端点的处理方式），对 11 个候选逐一发起真实请求确认端点可用性、字段结构、限流表现，不能仅凭参考项目 README/代码逻辑就直接假设可用并开始实现。
- **（v3.0.0，QA-R011，探测策略与止损机制，供 project-planner-cn 组织计划书参考）**：11 个候选源的真实探测本身是一项工作量庞大的前置任务，如何组织（先出一版"11 源探测结果汇总"再统一决定实现顺序，还是探测+实现按数据源逐个串行推进；是否分批分阶段交付而非一次性列完所有步骤）由 project-planner-cn 自行判断，本文档不代为规定。**关于探测结果如何影响最终范围，本 agent 依据本项目已有先例（QA-R002：Elsevier 候选端点实测确认不可用的 5 项被直接排除出 v2.0，未再逐项征求用户确认）给出以下默认处理原则，project-planner-cn/project-builder-cn 按此执行，不需要为每个探测结果单独发起新一轮 QA**：
  1. 若某候选**真实探测确认技术上不可行**（例如端点已下线、强制要求付费商业 key、无 key 时限流严重到实际不可用、返回结构与文档描述不符导致无法可靠解析），比照 QA-R002 先例，**直接排除出 v3.0.0，不需要单独找用户二次确认**，在 goal.md 或构建计划书中如实记录排除原因即可。
  2. 若某候选**真实探测确认技术上可行**，但探测过程中发现的某些特性（如字段稀疏、需要用户自行申请免费 key 才能获得可用体验）让其实际价值明显低于预期，**这类"技术可行但价值存疑"的情况不应由 project-planner-cn/project-builder-cn 自行拍板剔除**，因为用户已在 QA-R011 明确表态"全部纳入"、"先测试再说"，说明用户本身就预期会看到探测结果后再做取舍——出现这种情况时应整理成清晰的探测结果汇总，交还给用户做最终去留判断，而不是代为决定。
  3. 简言之：**技术不可行 → 直接排除（沿用先例，无需二次确认）；技术可行但价值存疑 → 汇总后交用户判断（不擅自剔除）**。这一原则同样适用于此前已确认的 bioRxiv/medRxiv、ChEMBL 两个语义特殊候选。
- **（v3.0.0，QA-R010，已确认）原 QA-R009（v2.4.0，`paperscraper.py` 改名/依赖选型/PubMed 新增 ESummary·ELink 的决策请求）已作废**：用户在 QA-R010 问题 6 的回答"本次版本就是3.0.0版本，跳过原本的2.4.0版本"实质确认不再需要该轮次；主线程已代为执行 `git revert c316c98`（提交 `d44d066`）将 QA-R009 从"澄清问答记录"中移除。QA-R010 正文中此前对 QA-R009 的引用（C.3、问题列表问题 6）已改为说明性编者按，不再指代实际存在的轮次。paperscraper.py 相关的技术债（改名/依赖精简/PubMed 功能扩展）如果未来仍需处理，需要作为一次新的、独立的目标澄清重新发起，不因并入 v3.0.0 而自动继承 QA-R009 已调研的内容。
- **（v3.0.0，QA-R012，已确认，新增架构分支，需 project-planner-cn 在设计步骤 34+ 时明确纳入考量）Semantic Scholar 提出"无 key 则不注册工具"的条件注册需求，这是本项目至今第一次出现按 key 存在与否条件注册工具的模式**：用户要求"如果 json 配置中没有配置 Semantic Scholar 的 API key，就不启用/不注册该工具（而不是注册了但调用时报错）"，即在对应 source 模块的 `register(server)` 函数内，判断 `settings` 中是否存在 Semantic Scholar 的 key（需新增 `settings` 字段，例如 `semantic_scholar_api_key`），若为空则跳过该工具的 `@server.tool()` 注册，使其在无 key 时不出现在 MCP 工具列表里，而非注册后在调用时才返回 401/403。**这与现有 Elsevier（`scopus.py`/`sciencedirect.py`）套路不同**——现有套路是无论是否配置 key 都无条件注册全部工具，缺 key 时调用才在运行时报 401/403。project-planner-cn 需要在构建计划书中权衡：这种"按 key 条件注册"模式是仅限 Semantic Scholar 这一处使用，还是要回溯应用到未来其他需要 key 的数据源（如本轮的 CORE），由 planner 自行判断并写入计划书，本文档不代为决定。
- **（v3.0.0，QA-R012，待定，非本 agent 代为判定）dblp 的最终去留悬而未决，等待用户提供新网络环境下的探测结果**：探测环境对 `dblp.org` 的 SSL 握手失败（requests+curl 双栈一致，HTTP 状态码 000），已排除是 API key 问题（dblp.org 公开 API 本身不要求 key），推测是探测环境的主机级网络拦截（防火墙/DNS 污染/TLS 中间人拦截），具体性质需换网络环境实测才能确认。已向用户提供分层诊断脚本（DNS 解析→TCP 连接→TLS 握手→HTTP 请求四层探测），用户尚未回报结果。**在用户回报新网络环境下的探测结果并经 QA-R013 正式定案前，dblp 不得被 project-planner-cn/project-builder-cn 视为已纳入或已排除**，不得代为假设任何一种结论后就开始设计/实现。

## 附录：Elsevier API 现状盘点（前置调研结论）

以下为对 `docs/elsevier-documentation/` 全部相关 HTML 文档与当前 `scopus.py` / `sciencedirect.py` 实现比对后的结论，作为后续澄清问答与目标制定的事实依据。

### 已实现功能
| 功能 | 端点 | 对应 MCP 工具 |
|---|---|---|
| Scopus Search | `content/search/scopus` | `search_scopus` |
| Abstract Retrieval | `content/abstract/eid/{eid}` | `get_abstract_details` |
| Author Retrieval | `content/author/author_id/{author_id}` | `get_author_profile` |
| Author Search | `content/search/author` | `search_authors` |
| 配额查询（非官方专用端点，借用 search 响应头模拟） | — | `get_quota_status` |
| ScienceDirect Search V2 | `content/search/sciencedirect` | `search_sciencedirect` |
| Article Metadata | `content/metadata/article` | `get_article_metadata` |
| Article Retrieval（全文/摘要获取） | `content/article/{identifier_type}/{identifier}` | `retrieve_article` |

注：`get_abstract_details` 默认 view 为 `META_ABS`，`retrieve_article` 默认 view 为 `META_ABS`——根据文档，这两个默认 view 均被标记为需要机构订阅/entitlement 的受限 view（`*`），非受限 view 为 `BASIC`/`META`。这意味着如果账号订阅等级不够，当前实现的默认调用可能无法拿到完整内容。

### 文档中存在、当前未实现的功能
| 功能 | 端点 | 认证/权限要求（文档判断） | 对文献检索场景的价值（初评） |
|---|---|---|---|
| Affiliation Retrieval（机构档案检索） | `content/affiliation/affiliation_id/{id}`（已通过 dev.elsevier.com 检索确认字面存在） | 文档未明确标记受限，疑似普通 Key 可用 | 中高：查看机构档案、该机构的作者/文献列表 |
| Affiliation Search（机构搜索） | `content/search/affiliation`（推断，与 search/author、search/scopus 同构） | 普通 Key | 中高：是 Affiliation Retrieval 的必要前置检索 |
| Citation Overview（逐年引用趋势） | `content/abstract/citations`（已通过 dev.elsevier.com 检索确认） | 需机构订阅/entitlement（标记为 `*`） | 中：文献计量/评价场景，受访问权限制约 |
| Citation Count Metadata（批量总被引次数） | `content/abstract/citation-count`（本地文档 examples.html 字面确认） | 文档未标记受限 | 中：比 Abstract Retrieval 更轻量的批量被引次数查询 |
| Serial Title（期刊信息，含 OA 状态、出版商） | `content/serial/title/issn/{issn}`（文档字面确认） | 需机构订阅/entitlement | 高：评估期刊质量/OA 状态的关键信息 |
| Article Entitlement（全文权限探测，ScienceDirect） | `content/article/entitlement/{doi\|pii\|eid\|scopus_id}/{id}`（已通过 dev.elsevier.com 检索确认） | 文档未明确，功能上是权限探测 | 高：可在调用全文检索前判断是否会命中付费墙，提升健壮性 |
| Nonserial Title（图书/专著元数据） | `content/nonserial/isbn:{isbn}`（文档字面确认） | 需机构订阅/entitlement | 中：仅在覆盖图书场景时有价值 |
| Object Retrieval（图/表/补充材料获取） | `content/object/{doi\|pii\|scopus_id\|pubmed_id}/{id}`（已通过 dev.elsevier.com 检索确认） | 文档未标记受限 | 中：获取文章配图/补充材料，非核心检索功能 |
| Embase APIs | 路径文档未给出 | **需单独向 Elsevier 申请**，与 embase.com 订阅无关 | 视目标用户群而定（生物医学检索）；接入门槛高 |
| Engineering Village APIs | 路径文档未给出（有 Swagger） | **需 EV 订阅 + 联系支持单独启用** | 视目标用户群而定（工程领域检索）；接入门槛高 |
| SciVal APIs | `analytics/scival/institution/...`（已通过 dev.elsevier.com 检索确认，base 为 analytics/scival，非 content/） | **需 SciVal 订阅** | 低（非检索类，是科研绩效分析工具） |
| TDM Service（文本数据挖掘授权机制） | 无独立端点，是使用条款/注册流程，本质是对 Article Retrieval 的批量授权 | 需机构订阅 + 完成 TDM 注册协议 | 中：仅在需要批量下载全文语料时有价值，属流程/合规问题而非纯技术缺口 |

**端点路径可信度说明**：`content/search/scopus`、`content/search/author`、`content/serial/title/issn/{issn}`、`content/nonserial/isbn:{isbn}`、`content/abstract/citation-count` 在本地文档中有字面 URL 依据；`content/affiliation/affiliation_id/{id}`、`content/abstract/citations`（Citation Overview）、`content/article/entitlement/...`、`content/object/...`、`analytics/scival/institution/...` 已于 2026-08-02 通过检索 dev.elsevier.com 官方文档二次确认字面路径；`content/search/affiliation` 仍为按命名惯例推断，未见字面确认。

### 实测可行性探测（2026-08-02，使用用户提供的真实 SCOPUS_API_KEY，见 QA-R002）

用户明确要求"对每一项都进行可行性检测"，且订阅等级"可能是最基础等级、未配置 Insttoken"。为把"文档理论上存在"收窄为"当前账号实测可用"，用临时探测脚本（未纳入正式代码，脚本在会话 scratchpad 中，不提交仓库）对上表候选端点各发起 1-2 次真实请求，结果如下：

| 功能 | 探测请求 | HTTP 状态 | Elsevier 错误码 | 结论 |
|---|---|---|---|---|
| Scopus Search（基线，view=STANDARD，已实现） | `content/search/scopus?view=STANDARD` | 200 | — | 正常，账号基础检索功能可用 |
| Scopus Search（view=COMPLETE，用于对比） | 同上，view=COMPLETE | 401 | AUTHORIZATION_ERROR | 当前账号连 Scopus Search 的 COMPLETE 视图都不可用，只能用 STANDARD |
| Affiliation Retrieval | `content/affiliation/affiliation_id/{id}?view=STANDARD` | 401 | AUTHORIZATION_ERROR | **实测不可用**，当前订阅无权限 |
| Affiliation Search | `content/search/affiliation` | 401（两次复测一致） | AUTHORIZATION_ERROR | **实测不可用**，当前订阅无权限 |
| Serial Title | `content/serial/title/issn/{issn}?view=STANDARD` | **200** | — | **实测可用** |
| Citation Count Metadata | `content/abstract/citation-count?scopus_id=...` | 403 | AUTHENTICATION_ERROR（"Requestor configuration settings insufficient"） | **实测不可用** |
| Citation Overview | `content/abstract/citations?scopus_id=...&date=...` | 403 | AUTHENTICATION_ERROR（同上） | **实测不可用** |
| Article Entitlement（ScienceDirect） | `content/article/entitlement/doi/{doi}` | 403 | AUTHENTICATION_ERROR（同上） | **实测不可用** |
| Object Retrieval（ScienceDirect） | `content/object/doi/{doi}?view=META` | **200** | — | **实测可用** |
| Nonserial Title | `content/nonserial/isbn:{isbn}?view=STANDARD/BASIC`（两个不同真实 ISBN） | 404（两次） | RESOURCE_NOT_FOUND | **结论不确定**：错误码是"资源不存在"而非权限类错误码，与其他确认不可用的端点（401/403）性质不同，无法排除是"账号无该数据集权限导致统一返回404"还是"两本测试图书恰好都不在 Elsevier 图书库"，需要更多样本或官方确认 |
| SciVal（Institution Count，不依赖具体ID） | `analytics/scival/institution/count` | 403 | ENTITLEMENTS_ERROR（"Not entitled to the resource specified"） | **实测不可用**。根因（据用户在 QA-R002 补充的 Elsevier 开发者门户说明修正）：SciVal、Scopus、Embase 确实共用同一个 Elsevier 开发者 API Key，但 SciVal/Embase 仅对**商业性质**的 Key 开放，用户当前 Key 为**非商业性质**，属于账号类型不满足，而非"无关的独立订阅产品线" |

**关键发现**：
1. 当前 SCOPUS_API_KEY 对应的订阅等级确实非常基础——不仅未实现的功能大多不可用，连已实现的 Scopus Search 的 COMPLETE 视图、`get_abstract_details`/`retrieve_article` 默认使用的受限 view（`META_ABS` 等）也大概率会受到同样限制（此前 goal.md 已记录这一风险，现有实测结果印证了该风险是真实存在的）。
2. **实测可用**：Serial Title（期刊信息）、Object Retrieval（ScienceDirect 图表/补充材料）——这两项可以直接纳入 v2.0 开发范围。
3. **实测不可用（需要更高订阅/entitlement，非当前 Key 能解决）**：Affiliation Retrieval、Affiliation Search、Citation Count Metadata、Citation Overview、Article Entitlement (ScienceDirect)——均为订阅等级不足。SciVal 单独列出：并非与现有 Key 无关，而是同一 Elsevier 开发者 Key 下"商业 vs 非商业"账号类型的区隔，用户当前 Key 为非商业性质，因此无法访问。
4. **结论待定**：Nonserial Title（图书检索），错误性质与其他"确认不可用"项不同，且用户对图书类目的检索场景是否是刚需本身也未明确。

### 实测可行性探测（2026-08-04，QA-R007 新候选项，使用 `.env` 中真实 Elsevier Key）

来源：调研本地参考项目 `reference-projects/elsevier-mcp-main/`（非本仓库代码，`.gitignore` 排除）后发现的 3 个本文档从未调研过的全新端点，以及 1 个"同端点换 Accept 头"的响应格式变体。用户在 QA-R007 中回答"验证一下"（四项全部要求真实探测，明确表示即便结构上高度可疑（`plumx_metrics`）也要实测而非凭同构证据下结论）。沿用一贯方法论：临时探测脚本（`probe_qa_r007.py`，位于会话 scratchpad，未纳入仓库）对四个候选各发起 1-3 次真实请求，复用此前探测中已验证有效的真实标识符（ISSN `0092-8674`=Cell、DOI `10.1016/j.jmst.2026.07.003`）。结果如下：

| 功能 | 探测请求 | HTTP 状态 | Elsevier 错误码/说明 | 结论 |
|---|---|---|---|---|
| `serial_title_search`（期刊搜索，不需要 ISSN） | `content/serial/title?title=Cell&count=5` | **200** | — | **实测可用**。返回 `serial-metadata-response.entry[]`，字段结构与已实现的 `content/serial/title/issn/{issn}` 高度一致（`dc:title`/`dc:publisher`/`prism:issn`/`prism:aggregationType`/`subject-area[]`/`link[]`），另有 `SNIPList`/`SJRList`（期刊计量指标，当前 `scopus_serial_title_by_issn` 未提取）。真实返回的第一条是 *Advanced Fuel Cell Technology*（`title=Cell` 是子串匹配，非精确匹配，符合"搜索"语义预期）。 |
| `subject_classifications`（学科分类代码查询） | `content/subject/scopus?description=computer` | **200** | — | **实测可用**。返回 `subject-classifications.subject-classification[]`，每项含 `code`/`description`/`detail`/`abbrev`（真实样本：`code=1700-1712` 均为 Computer Science 大类下的细分学科，如 `1702`="Artificial Intelligence"、`1709`="Human-Computer Interaction"）。字段结构简单、扁平，无嵌套问题。 |
| `plumx_metrics`（PlumX 替代计量学指标） | `analytics/plumx/doi/{doi}` | 401 | AUTHENTICATION_ERROR（"The requestor is not authorized to access this resource"） | **实测不可用**。印证了 QA-R007 中"`analytics/` 前缀与 SciVal 同构、大概率同样受限"的判断——虽然具体错误码与 SciVal 的 `403 ENTITLEMENTS_ERROR` 不完全相同（这里是 `401 AUTHENTICATION_ERROR`），但结论一致：当前非商业 Key 无法访问。 |
| `fulltext_retrieval` 纯文本变体（同一 `content/article/doi/{id}` 端点，仅 `Accept: text/plain`） | `content/article/doi/{doi}`，`Accept: text/plain`，分别测试 `view=META`/`view=META_ABS`/`view=FULL`/不带 view 共 4 种组合 | 400（4 种组合均一致） | INVALID_INPUT（"View parameter specified in request is not valid"） | **实测不可用**，且现象比较特殊：同一端点、同一 DOI，把 `Accept` 换回 `application/json`（不带 view）或 `text/xml`（`view=META`）都能正常返回 **200**，只有 `Accept: text/plain` 这一种协商方式始终 400，与 `view` 参数取值无关（含不传 `view`）。错误信息字面是"view 参数无效"，但实际上没有传无效 view 也照样报错，怀疑是账号对 `text/plain` 纯文本正文输出的实体协商本身不被支持/不受当前订阅覆盖，Elsevier 用了一个措辞上有误导性的校验错误来表达。由于这只是已实现端点的响应格式变体（不是新能力），且实测确认此路不通，不建议为它单独投入更多探测。 |

**关键发现（QA-R007 探测）**：
1. **实测可用、且推荐纳入候选范围**：`serial_title_search`（期刊搜索）、`subject_classifications`（学科分类查询）——两者均返回 200 且拿到了真实、结构清晰的响应字段，与本项目已实现的 Elsevier 功能属于同一订阅层级，技术风险低。
2. **实测不可用，建议排除**：`plumx_metrics`——与 SciVal 同属 `analytics/` 前缀资源，当前非商业 Key 确认无法访问（401 AUTHENTICATION_ERROR）。
3. **实测不可用，建议排除**：`fulltext_retrieval` 纯文本变体——同一已实现端点换 `Accept: text/plain` 后固定返回 400，JSON/XML 协商方式均正常，说明问题出在纯文本这一特定响应格式上，而非端点本身或 view 参数；不是新能力，本项目已有的 JSON 归一化返回已能覆盖同等信息，无需为此单独开发。

## 澄清问答记录
<!-- GOAL-QA-LOG-START -->

### QA-R001：范围优先级与权限约束摸底
<!-- GOAL-QA-R001-START -->
- **提问时间**：2026-08-01 23:04
- **提问目的**：调研已给出"文档存在但未实现"的功能清单，但哪些值得纳入 v2.0、以及能否真正跑通，取决于用户的实际订阅权限和产品定位，必须先摸清这两点才能收窄范围。
- **问题列表**
  1. 在未实现的功能清单中（机构检索、期刊信息 Serial Title、全文权限探测 Article Entitlement、引用趋势 Citation Overview/Count、图表获取 Object Retrieval、图书检索 Nonserial Title），你觉得哪几项是 v2.0 里"必须做"的，哪几项是"可以不做/以后再说"？
  2. 当前使用的 SCOPUS_API_KEY 对应的 Elsevier 订阅等级大概是什么情况？是否配置了 X-ELS-Insttoken（机构令牌）？是否知道能否访问标记为"需要机构订阅/entitlement"的受限 view（比如 Serial Title 的 Standard/Enhanced、Citation Overview 的 Standard）？如果不确定，是否需要我们后续通过实际调用测试来探测？
  3. Embase、Engineering Village、SciVal 这三条产品线都需要独立于 SCOPUS_API_KEY 的额外订阅或人工审批，短期内接入门槛较高——v2.0 是否要明确排除它们（留到未来单独评估），还是其中某一个恰好是你的目标用户群非常需要的（比如做生物医学检索需要 Embase）？
- **用户回答**
  1. 都是需要尝试做的
  2. 可能是最基础的订阅等级，没有配置机构令牌，需要对每一项都进行可行性检测
  3. embase和engineering village都不需要，scival需要先测试一下能否用（scival和scopus的调用都是基于elsevier的apikey），如果可以的话再考虑下一步
- **提炼结论**
  - 用户希望"文档存在但未实现"的候选功能（机构检索、Serial Title、Article Entitlement、Citation Overview/Count、Object Retrieval、Nonserial Title）全部先做可行性尝试，不预先排除任何一项。
  - 当前 SCOPUS_API_KEY 的订阅等级用户自评为"可能是最基础等级"，且未配置 Insttoken（机构令牌），因此哪些功能能真正跑通存在不确定性，用户要求逐项做实测而非只凭文档判断。
  - Embase、Engineering Village 明确不需要，直接排除出 v2.0 范围。
  - SciVal 用户基于"SciVal 和 Scopus 调用都用同一个 Elsevier API Key"的假设，希望先测试是否能直接复用现有 Key 访问，如果可行再考虑纳入。
  - 后续（见 QA-R002）已用用户提供的真实 Key 完成实测：SciVal 返回 `ENTITLEMENTS_ERROR` 被拒绝。根因**不是**"SciVal 是与 Scopus 无关的独立产品线"，而是：SciVal、Scopus、Embase 等资源确实共用同一个 Elsevier 开发者 API Key，但 SciVal 和 Embase 只对**商业性质**的 Key 开放访问，用户当前的 Key 是**非商业性质**，因此账号类型不满足，并非 Key 本身无关（此表述已根据 QA-R002 用户澄清修正）。
- **影响的目标文档章节**
  - 核心目标 / 范围界定 / 约束条件
  <!-- GOAL-QA-R001-END -->

### QA-R002：真实 API 探测与范围收窄确认
<!-- GOAL-QA-R002-START -->
- **提问时间**：2026-08-02 00:03
- **提问目的**：QA-R001 中用户要求"对每一项都进行可行性检测"，并提供了真实 SCOPUS_API_KEY（放在项目根目录 `.env`）。已用临时探测脚本对候选端点各发起 1-2 次真实请求（详见本文档"实测可行性探测"表格），把"文档理论上存在"收窄为"当前账号实测可用/不可用"。现基于实测结果，向用户确认 v2.0 的最终范围和对不可用项的处理方式。
- **问题列表**
  1. 实测确认**不可用**（当前订阅拿不到，返回 401/403）的 5 项——Affiliation Retrieval、Affiliation Search、Citation Overview、Citation Count Metadata、Article Entitlement（ScienceDirect）——v2.0 是否仍要把它们写成代码（这样订阅升级后无需改代码即可直接用，但短期内实际调用会报错/降级），还是本轮直接不写代码、只记录为"待订阅升级后再评估"？
  2. 实测确认**可用**的 Serial Title（期刊信息）和 Object Retrieval（ScienceDirect 图表/补充材料）是否确认列为 v2.0"确定要做"的范围？
  3. SciVal 已证实与现有 Key 无关、必须单独订阅——是否确认从 v2.0 范围中排除（如未来拿到 SciVal 订阅再单独立项）？
  4. Nonserial Title（图书/专著检索）实测结果是 404（资源不存在），错误性质与其他"确认不可用"项的 401/403 不同，无法直接判定是权限问题还是数据未命中；同时也想确认：图书/专著检索本身是否是你产品定位里关心的场景？如果你的检索场景本来就聚焦期刊论文，这项可以不必再深究技术细节，直接排除。
- **用户回答**
  1. 既然不可用，那么就不纳入本次升级
  2. 加入确定范围
  3. 根据Elsevier开发门户的说明，scival、scopus、embase等资源都是使用同样的Elsevier开发者apikey，但是scival和embase只对商业用户的apikey开放，所以并不是无关，而是我的key是非商业的，无法访问scival，因此，不将scival加入到v2.0的升级范围中
  4. 直接排除
- **提炼结论**
  - v2.0 Elsevier 扩展的最终范围收敛为：**只做实测确认可用的两项**——Serial Title（期刊信息查询）、Object Retrieval（ScienceDirect 图表/补充材料获取）。
  - 实测确认不可用的 5 项（Affiliation Retrieval、Affiliation Search、Citation Overview、Citation Count Metadata、Article Entitlement）——用户明确"不纳入本次升级"，不写代码，不做"面向未来订阅升级"的预留实现，全部排除出 v2.0。
  - SciVal——用户补充关键信息并纠正了此前的定性：SciVal、Scopus、Embase 共用同一个 Elsevier 开发者 API Key，但 SciVal/Embase 仅对**商业性质**的 Key 开放，用户当前 Key 为**非商业性质**，因此是"账号类型不满足"而非"无关的独立订阅产品线"。结论：不纳入 v2.0，此表述已同步修正到 QA-R001 提炼结论与"实测可行性探测"表格中。
  - Nonserial Title（图书/专著检索）——直接排除，不再纠结 404 的技术性质（权限问题还是数据未命中），因为该场景本身不是本次升级的关注点。
  - 用户回复"确认完毕"，标志着范围澄清已完成，可以据此正式填充 goal.md 的核心目标/范围界定/约束条件等章节。
- **影响的目标文档章节**
  - 核心目标 / 目标用户 / 期望成果 / 成功标准 / 范围界定（包含/排除） / 约束条件
  <!-- GOAL-QA-R002-END -->

### QA-R003：真实环境全量实测后的工具范围收缩与 README 准确性修正
<!-- GOAL-QA-R003-START -->
- **提问时间**：2026-08-03 13:44
- **提问目的**：v2.0（2.0.1）发布后，用户在真实 Cherry Studio 环境下用同一枚基础/非商业 Elsevier Key，对全部 17 个已发布工具做了一轮完整可用性实测（报告见 `docs/调用错误分析报告.md`），结果 11 个可用、6 个不可用。用户明确要求：不论不可用原因是网络问题还是权限不足，一律舍弃这 6 个工具（并额外舍弃 `downloadPaper`，理由是下载类功能不属于"以查询为主"的产品定位）；同时修改 README，准确说明"非商业 Elsevier Key 即可让删减后的全部剩余功能正常工作"。这是对已发布 v2.0 范围的一次事后收缩，需要正式记录决策来源（用户实测报告 + 用户明确指示），并核实报告中哪些结论是实测事实、哪些是该次会话自行推测、不应直接采信。
- **问题列表**
  1. 确认删除范围＝以下 6 个工具全部删除、不做保留、不做"面向未来订阅升级/未来修复 bug 的预留代码"：`downloadPaper`（arxiv 库 API 不兼容，AttributeError）、`searchAuthors`（Scopus，401）、`getAuthorProfile`（Scopus，401）、`searchSciencedirect`（ScienceDirect，401）、`getArticleMetadata`（ScienceDirect，401）、`searchScholarPapers`（Google Scholar，请求超时）——是否认可这个范围，且 `downloadPaper` 是"产品定位性排除"（即便未来有人修好那个 AttributeError，也不因此恢复，因为下载不在查询类 MCP 的范围内），而非单纯的技术 bug 待修？
  2. 需要向你指出两处疑点供你复核（但不影响默认执行删除的决定）：(a) `searchAuthors`/`getAuthorProfile`（401）与本项目 goal.md 此前 QA-R002 实测记录的 Affiliation Retrieval/Search（同为 401 AUTHORIZATION_ERROR）、以及 Scopus Search 的 COMPLETE view（同为 401）属于同一账号权限受限模式，可信度较高，不像偶发；`searchSciencedirect`/`getArticleMetadata`（401）也是同类模式。(b) `searchScholarPapers` 的"请求超时"证据强度相对更弱——超时可能是网络抖动/反爬/单次偶发，而不是结构性不可用，且本项目 buildlog.md 历史记录（[1.3.0]）显示 Google Scholar 一直被标注为"实验性、连通性不稳定"。是否仍按你原话，对 (a)(b) 一视同仁全部删除，不做"保留 searchScholarPapers 但加更强的不稳定警告"这类折中？另外报告中对 401 根因的具体解释（如"需联系机构管理员升级""需要机构订阅"）是撰写该报告的另一会话在未查看本项目代码/goal.md 前提下的推测，我不会把这些具体归因原文写入 goal.md，只记录客观现象（HTTP 状态码/超时），是否同意这个处理方式？
  3. README 修改范围：除了 Elsevier Key 资质要求的说明段落外，README.md/README_ZH.md 中列举 17 个工具的清单/表格、工具计数等处是否也要同步改为 11 个工具（预期是必然联动），是否还有其他你希望一并核实准确性的措辞？是否需要在 goal.md 里指定这次改动对应的具体版本号（当前 `pyproject.toml` 为 2.0.1），还是版本号交给后续 project-planner-cn/project-builder-cn 决定？
- **用户回答**
  1. 是的
  2. 一视同仁，全部删除，Googlescholar就是单纯网络受限用不了，Elsevier相关的删除都是apikey的权限问题
  3. README同步改动，版本号提升为2.1.0
- **提炼结论**
  - 用户确认删除范围＝以下 6 个工具，全部删除，不保留，不做"面向未来订阅升级/未来修复 bug 的预留代码"：`downloadPaper`（arxiv 库 API 不兼容，AttributeError）、`searchAuthors`（Scopus，401）、`getAuthorProfile`（Scopus，401）、`searchSciencedirect`（ScienceDirect，401）、`getArticleMetadata`（ScienceDirect，401）、`searchScholarPapers`（Google Scholar，请求超时）。
  - `downloadPaper` 明确为**产品定位性排除**：即便未来该 `AttributeError` 被修好，也不因此恢复，因为下载类功能不属于"以查询为主"的 MCP 产品定位，这是范围收缩而非技术债待还。
  - 用户对疑点 (a)(b) 均确认"一视同仁，全部删除"，并补充了比该会话此前判断更明确的归因：`searchScholarPapers` 的不可用，用户确认是**单纯的网络访问受限**（而非该会话所猜测的"可能是偶发抖动"），态度是确定性的不可用，只是归因方式和该会话此前的"证据强度较弱、疑似偶发"判断不同——用户判断是网络层面确定受限，删除决策本身不受此差异影响。4 个 Elsevier 401（`searchAuthors`/`getAuthorProfile`/`searchSciencedirect`/`getArticleMetadata`）用户确认是 **API Key 权限问题**，与本文档 QA-R002 实测记录的 Affiliation Retrieval/Search（401）、Scopus Search COMPLETE view（401）属于同一账号权限受限模式，判断一致。
  - 报告 `docs/调用错误分析报告.md` 中对 401 根因的具体推测性表述（如"需联系机构管理员升级""需要机构订阅"）不作为 goal.md 的定论收录，goal.md 只记录客观现象（HTTP 状态码/请求超时）与用户本人的归因判断。
  - README.md / README_ZH.md 需要同步修改：(1) Elsevier Key 资质要求说明段落，改为准确反映"非商业/无机构资质的基础 Key 即可让删减后的全部 11 个剩余工具正常工作"；(2) 工具清单/表格/计数从 17 个同步改为 11 个（`docs/调用错误分析报告.md` 已给出清晰的可用/不可用工具分类，可直接作为改写依据）。
  - 版本号明确定为 **2.1.0**（新增功能/范围调整级别的版本号，而非 2.0.2 这类纯 patch 号），因为这次改动同时包含"移除已发布的公开工具接口"（对使用者是破坏性/范围性变更）和"文档准确性修正"，用 2.0.x patch 号不足以体现变更性质。
  - 用户明确认可本 agent（project-creator-cn）提出的分工：本轮由 project-creator-cn 完成 goal.md 的目标记录；实际的代码删除（`src/uniarticles/sources/arxiv.py`、`scopus.py`、`sciencedirect.py`、`paperscraper.py` 中对应函数及其 `@server.tool()` 注册、相关测试）与 README.md/README_ZH.md 文案修改，移交给 project-planner-cn 制定构建计划书、再由 project-builder-cn 落地执行，本 agent 不直接改动这些文件。
- **影响的目标文档章节**
  - 核心目标 / 范围界定（包含/排除） / 成功标准 / 约束条件
  <!-- GOAL-QA-R003-END -->

### QA-R004：`docs/TODO.md` 两条待办（移除 search_paper + 全量工具语义化重命名）的可行性核实与破坏性变更决策
<!-- GOAL-QA-R004-START -->
- **提问时间**：2026-08-03 19:43
- **提问目的**：用户在 `docs/TODO.md` 写下两条待办——①移除 `search_paper`（保留实现完全一致的 `search_arxiv`）；②对全部工具做更语义化的命名，并给出 `search_arxiv → arxiv_paper_search_by_query`、`list_paper → arxiv_latest_paper_list_by_category` 两个示例。用户要求先评估、不要直接照单全收去改代码。核实代码（`src/uniarticles/sources/arxiv.py`、`scopus.py`、`sciencedirect.py`、`paperscraper.py`）与既有文档（`project-docs/teach.md`、`project-plan.md`）后，形成以下专业判断：
  1. **关于移除 `search_paper`**：确认它是 `search_arxiv` 的纯别名（函数体仅 `return await search_arxiv(...)`），无独立校验/异常处理逻辑。README.md/README_ZH.md 从未公开列出过它（`project-plan.md` 469 行已记录）。但 v2.1.0 清理 6 个不可用工具那一轮，`buildlog.md`/`project-plan.md` 明确"故意保留 `search_paper`，删除时别误删"，`teach.md` 记录的推测是"可能为兼容某些习惯 `search_paper`/`search_papers` 命名的客户端/提示词而保留"——这只是推测，没有任何提交记录或文档写明确切原因。它与此前删除的 6 个工具性质不同：那 6 个是**实测确认不可用**（401/403/超时），删除是"清理故障"；`search_paper` 是**能正常工作**的别名，移除它是"主动做破坏性简化"，风险评估的性质不一样，需要用户单独确认而非套用上一轮的删除逻辑。
  2. **关于全量工具重命名**：当前 11 个工具命名规则本身不统一——`search_arxiv`/`search_scopus`/`search_pubmed_papers` 是"动词_数据源"，但 `list_papers`/`read_paper`/`get_abstract_details`/`get_serial_title`/`get_quota_status`/`retrieve_article`/`get_article_objects` 完全不带数据源信息。用户提出按数据源加前缀语义化命名的方向合理，但重命名 MCP 工具名对已发布的 PyPI 包（`uniarticles-mcp`，已被 `uvx` 方式在 Claude Desktop/Cherry Studio 等客户端启动使用）是**破坏性变更**：MCP 客户端通常在连接时动态拉取工具列表，重命名本身不会导致协议层报错，但任何用户已经写好并硬编码旧工具名的提示词/自定义指令/工作流会失效，且用户此前没有任何弃用过渡（deprecation）就直接改名，无法被识别为"同一功能换了皮"。这与此前"删除确认不可用工具"的破坏性质不同（那是删除本就用不了的功能，实际影响面小），重命名影响的是全部 11 个**当前正常工作**的工具，影响面最大，必须单独决策，不能顺带执行。
  3. **核实用户示例命名的准确性问题**：`list_paper`（实际工具名为 `list_papers`，复数）目前的实现（`arxiv.py` 第 82-98 行）**并没有真正按分类过滤**——代码注释显示开发者最初想做"按 category 列出最新论文"，但最终改为对 `_run_arxiv_search` 传入固定 query `"all"`，本质是"不带筛选条件的最新论文搜索"。若直接采用用户建议的 `arxiv_latest_paper_list_by_category`，命名会宣称一个当前代码并不具备的能力（承诺功能与实现不符），这是命名规范之外必须先澄清的事实问题：这次改动是"只改名字"还是要"顺带把实现补全到匹配新名字所暗示的能力"。
- **问题列表**
  1. 移除 `search_paper`：确认按你在 TODO 里写的直接删除？需要你明确知晉这是主动放弃一个"能正常工作但未公开宣传"的兼容别名，而不是清理故障工具，且没有任何证据能 100% 排除有用户在文档外凭经验用过这个工具名——你是否接受这个不可完全排除的低概率兼容性风险？
  2. 全量工具重命名属于影响全部 11 个当前可用工具的破坏性变更：你希望现在就在下一个版本里直接把所有工具名改掉（旧名字彻底消失，一次性切换），还是希望采用"新旧名字并存一段时间"的过渡方案（新名字是主实现，旧名字保留为别名并在文档/日志中标注"deprecated，将在下个大版本移除"，给已配置好提示词的用户一个缓冲期）？如果选择一次性切换，是否同意这类量级的改动应该对应一个更高的版本号（例如 3.0.0 而非 2.x 的 minor 版本），以便使用语义化版本号的用户能一眼看出这是破坏性变更？
  3. 命名风格：你给的示例（`arxiv_paper_search_by_query`、`arxiv_latest_paper_list_by_category`）是"数据源_对象_动作_by_限定词"模式，信息完整但偏长。我倾向的备选方案是更紧凑的"数据源_动词_对象"模式（例如 `arxiv_search_papers`、`sciencedirect_get_article_objects`），同样体现数据源+动作+对象，但去掉 `by_x` 限定词后缀。下面这两种风格你更倾向哪一种？还是希望我针对个别工具单独讨论？
     - 方案A（你的示例风格，逐词更完整）：`arxiv_paper_search_by_query`、`arxiv_latest_paper_list_by_category`……
     - 方案B（更紧凑）：`arxiv_search_papers`、`arxiv_list_recent_papers`……
  4. 承接第 3 点发现的问题：`list_papers` 当前实现并不按分类过滤，只是无筛选地拉取最新论文。这次改动中，你希望（a）只改名字，新名字要如实反映"无分类过滤"这一现状（例如 `arxiv_list_recent_papers`，不含 category 字样），还是（b）借这次改名的机会顺带把实现补全为真正支持按 category 过滤（这会把一次"纯命名"任务变成"命名+功能开发"任务，需要另外评估工作量和 arxiv 库的 category 参数支持情况）？
- **用户回答**
  1. 确认完全删除
  2. 彻底改掉
  3. 方案A
  4. 改成完全且真正支持按category过滤
- **提炼结论**
  - **`search_paper` 确认完全删除**：用户明确接受"无法 100% 排除文档外用户依赖该别名"这一低概率兼容性风险，`search_paper` 不再作为过渡别名保留，随本轮改动一并从 `arxiv.py` 移除（函数体、`@server.tool()` 注册及相关测试引用）。
  - **全量工具重命名确认为一次性彻底切换**：不做"新旧名字并存/deprecated 过渡期"方案，旧工具名在新版本中直接消失，不提供向后兼容别名。这是用户主动选择的更激进方案（相对于本 agent 在问题 2 中提出的过渡期备选方案），意味着任何硬编码旧工具名的用户提示词/工作流会在升级后立即失效，无缓冲期。
  - **命名风格确认为方案 A**（用户示例风格）：采用"数据源_对象_动作(_by_限定词)"的完整语义模式，例如 `arxiv_paper_search_by_query`，不采用本 agent 备选的更紧凑的"数据源_动词_对象"方案 B。全部工具的具体新名称由 project-planner-cn 在构建计划书中按此风格逐一拟定。
  - **`list_papers` 确认为"命名+功能开发"双重任务**：不是仅改名字掩盖现状，而是要求本次改动把实现补全为**真正支持按 category 过滤**，新名字（暗示 category 过滤能力）与实际功能要对齐。技术可行性已核实（见备注中的交接说明）：`arxiv` 库（当前项目依赖版本 3.0.0）的 `arxiv.Search.__init__` 只有 `query`/`id_list`/`max_results`/`sort_by`/`sort_order` 五个参数，**没有独立的 `category` 参数**；但 arXiv 官方查询语法支持 `cat:` 字段前缀（如 `cat:cs.AI`），可以通过拼接 `query` 字符串复用这一官方查询语法实现按分类过滤，既不是"库原生参数直接可用"，也不需要"客户端拿到全量结果后自己按 category 字段过滤"，是介于两者之间的第三种实现方式——细节已写入下方"备注"交接说明，供 project-planner-cn 编写构建计划书时参考，避免凭空判断工作量。
  - **版本号问题：用户本轮回答未覆盖**。本 agent 在问题 2 中把"是否一次性切换"和"版本号应为 3.0.0 还是延续 2.x"绑定在一起提问，但用户的回答"彻底改掉"只回应了切换方式，没有对版本号表态。鉴于版本号是不可由本 agent 代替用户决定的一次性发布决策，已追加 **QA-R005** 单独确认，不在本轮结论中替用户预设版本号。
- **影响的目标文档章节**
  - 核心目标 / 范围界定（包含/排除） / 约束条件
  <!-- GOAL-QA-R004-END -->

### QA-R005：全量重命名+功能补全对应的版本号确认
<!-- GOAL-QA-R005-START -->
- **提问时间**：2026-08-03 19:51
- **提问目的**：QA-R004 问题 2 把"重命名是否一次性切换"与"版本号是否应为 3.0.0"绑定提问，用户只回答了"彻底改掉"（一次性切换），未对版本号单独表态。本轮改动包含三类变更叠加：①删除一个当前能正常工作的工具（`search_paper`）；②对剩余全部 10 个工具做无过渡期的破坏性重命名；③新增/修改 `list_papers` 的功能（真正支持 category 过滤，非纯 bugfix，是能力扩展）。按语义化版本规范的通行理解，②是典型的破坏性变更（Breaking Change），③是功能新增（Feature），二者叠加通常应体现为主版本号（Major）提升而非 2.x 的 minor 号；但版本号最终标识的是对外发布语义，必须由用户本人明确拍板，本 agent 不能替用户悄悄定版本号，故单独追问确认。
- **问题列表**
  1. 本轮改动（删除 `search_paper` + 全部 10 个工具一次性重命名 + `list_papers` 新增真实 category 过滤）对应的目标发布版本号，是否确认为 **`3.0.0`**（主版本号提升，明确标识破坏性变更）？还是你有其他版本号考虑（例如仍归入 2.x，或使用其他版本策略）？
- **用户回答**
  1. 版本为2.2.0；因为并没有明确增多新工具
- **提炼结论**
  - **版本号确认为 `2.2.0`**，用户否决了本 agent 倾向的主版本号（3.0.0）建议，理由是本轮改动没有净增加工具数量（删除 `search_paper` 后剩余 10 个工具原地重命名+功能补全，不是新增工具集）。本 agent 的判断依据（重命名是破坏性变更、按 SemVer 惯例应提主版本号）已如实记录在问题描述中供后续参考，但版本号最终以用户决定为准，`project-planner-cn`/`project-builder-cn` 后续执行时应统一使用 `2.2.0`，不再沿用本 agent 建议的 `3.0.0`。
- **影响的目标文档章节**
  - 核心目标 / 约束条件
  <!-- GOAL-QA-R005-END -->

### QA-R006：交付重命名表格后追加的三项决策（quota→usage改名微调 / 归一化新任务 / 工具注册顺序调整）
<!-- GOAL-QA-R006-START -->
- **提问时间**：2026-08-03 20:21
- **提问目的**：主线程已基于 QA-R004 的方案 A 命名风格，交付了一份覆盖删除 `search_paper` 后剩余 10 个工具的 6 维度改动表格（旧名字/新名字/请求参数/预期返回体/作用/允许的参数）。用户看完表格后追加了三项新决策，需要本 agent 核实事实依据并正式记录，其中第 3 项存在必须向用户澄清的实现歧义，不能替用户假设。
- **问题列表（前两项为记录性核实，第 3 项为正式提问）**
  1. `get_quota_status` 的新名字，QA-R004 表格中原拟 `scopus_api_quota_status`，用户要求改为 `scopus_api_usage_status`（用 usage 替换 quota）——其余 9 个工具的新名字是否维持表格原方案不变？
  2. 用户要求新增：把 `get_abstract_details`（`scopus.py`）与 `retrieve_article`（`sciencedirect.py`）也纳入 JSON 归一化范围。本 agent 核实代码确认：`scopus.py` 第 76-82 行 `_get_abstract()` 与 `sciencedirect.py` 第 30-36 行 `_retrieve_article()` 目前均为 `items=[response.json()]`——把 Elsevier 原始响应整体透传，没有像 `search_scopus`/`get_serial_title`/`get_article_objects` 那样做逐字段提取。核实 `project-docs/goal.md`/`buildlog.md`/`teach.md` 是否已记录过这两个端点的真实响应体样例，以判断归一化方案能否直接编写、还是需要先做真实探测。
  3. 用户要求工具注册顺序从当前"杂乱"改为 **scopus → sciencedirect → arxiv → pubmed → 用量查询** 的顺序。本 agent 核实 `src/uniarticles/sources/__init__.py` 当前 `register_all_sources()` 调用顺序为 `arxiv → scopus → paperscraper → sciencedirect`（文件级）；而"用量查询"工具（`scopus_api_usage_status`）是在 `scopus.py` 的 `register()` 函数内部、与 `search_scopus`/`get_abstract_details`/`get_serial_title` 同一个函数体里通过 `@server.tool()` 注册的，不是独立的跨文件注册单元。这产生一个必须向用户澄清、不能自行假设的实现分歧：用户要的"scopus-sciencedirect-arxiv-pubmed-用量查询"顺序，是**只要求文件级顺序**（`sources/__init__.py` 里四个 `register_xxx_source()` 调用顺序改为 scopus→sciencedirect→arxiv→paperscraper 即可，`scopus.py` 内部各工具的相对顺序不强求"用量查询"必须排在全局最后），还是**要求全局工具注册顺序精确匹配**（"用量查询"必须是全部 10 个工具里最后一个被注册的，因为 `scopus.py` 是最先被调用的文件，若不做特殊处理，其内部注册的 `scopus_api_usage_status` 会先于 `sciencedirect`/`arxiv`/`pubmed` 的工具被注册，与"最后"的要求矛盾，需要把该工具的注册逻辑从 `scopus.py` 的 `register()` 中拆出，改为由 `sources/__init__.py` 最后单独调用）？— 请用户明确选择其一，避免 `project-builder-cn` 做无用功或理解错方向。
- **用户回答**
  1. 保持不变
  2. 没有记录过真实响应案例
  3. 只要求文件级别的顺序
- **提炼结论**
  - **`scopus_api_usage_status` 改名最终确认**：其余 9 个工具的新名字维持已交付表格的方案 A 结果不变，只有 `get_quota_status` 一处从原拟 `scopus_api_quota_status` 改为 `scopus_api_usage_status`。
  - **归一化任务前提已获用户确认**：用户确认 `get_abstract_details`/`retrieve_article` 的真实响应体样例此前确实未被记录过，印证了本 agent 的核实结论——归一化字段方案不能在本文档或构建计划书中凭空定义，必须先由 `project-builder-cn` 做真实探测拿到字段样例后再定，这一前提已无争议、可直接执行。
  - **注册顺序歧义最终澄清为"只要求文件级顺序"**：用户明确选择较轻量的方案——只需把 `src/uniarticles/sources/__init__.py` 中 `register_all_sources()` 内四个 `register_xxx_source()` 调用顺序，从当前的 `arxiv → scopus → paperscraper → sciencedirect` 改为 `scopus → sciencedirect → arxiv → paperscraper`（pubmed）即可；**不要求**把 `scopus_api_usage_status` 的注册逻辑从 `scopus.py` 的 `register()` 函数中拆出、单独挪到 `sources/__init__.py` 末尾调用。也就是说，`scopus.py` 内部 `search_scopus`/`get_abstract_details`/`get_serial_title`/`scopus_api_usage_status` 四个工具之间的相对注册顺序**保持文件内原有顺序不变**，不需要跨文件拆分注册逻辑；"用量查询排在最后"这一表述在最终实现上，只在"scopus.py 是文件级顺序中最先被调用的模块、其内部工具自然先于其他三个文件被注册"的意义上得到满足，不代表 `scopus_api_usage_status` 会是全部 10 个工具里字面意义上最后一个被注册的工具。此理解已经过用户本人明确选择确认，不是本 agent 的猜测性简化。
- **影响的目标文档章节**
  - 核心目标 / 范围界定 / 约束条件
  <!-- GOAL-QA-R006-END -->

### QA-R007：调研参考项目 `reference-projects/elsevier-mcp-main/` 后发现的新候选功能点确认
<!-- GOAL-QA-R007-START -->
- **提问时间**：2026-08-04 12:57
- **提问目的**：用户要求调研本地 `reference-projects/elsevier-mcp-main/`（一个 TypeScript 实现的开源 Elsevier MCP 参考项目，`.gitignore` 排除，非本仓库代码），评估其中是否有值得纳入 UniArticles 的能力。已完整阅读该项目 `src/` 下全部 14 个工具源码（`scopus-search.ts`/`abstract-retrieval.ts`/`article-retrieval.ts`/`serial-title.ts`/`subject-classifications.ts`/`author-search.ts`/`author-retrieval.ts`/`affiliation-search.ts`/`affiliation-retrieval.ts`/`citation-count.ts`/`citations-overview.ts`/`plumx-metrics.ts`/`fulltext-retrieval.ts`及`client.ts`/`errors.ts`），并逐个核对其调用的真实端点路径，与本文档"附录：Elsevier API 现状盘点"逐项比对，结论如下：
  - **8/14 个工具的端点与本文档已用真实 Key 实测并排除的功能完全一致**（`author_search`↔`content/search/author`、`affiliation_search`↔`content/search/affiliation`、`author_retrieval`↔`content/author/author_id/{id}`、`affiliation_retrieval`↔`content/affiliation/affiliation_id/{id}`、`citation_count`↔`content/abstract/citation-count`、`citations_overview`↔`content/abstract/citations`——均已实测 401/403；另外 `article_retrieval`/`abstract_retrieval` 与本项目已实现的 `sciencedirect_article_retrieve_by_identifier`/`scopus_abstract_detail_by_eid` 是同一端点）。这 8 项**没有新增价值**，参考项目也没有揭示任何本文档实测结论之外的新可行性证据（该项目 README 同样把这类工具标注为"需机构网络/额外订阅"）。
  - **`serial_title_retrieval`** 与本项目已实现的 `scopus_serial_title_by_issn` 是同一端点（`content/serial/title/issn/{issn}`），已覆盖。
  - **发现 3 个本文档从未提及、goal.md 完全没有调研过的全新端点**（详见下方问题列表），其中 1 个（`serial_title_search`）与已验证可用的端点同属一个资源族、把握较高；1 个（`subject_classifications`）完全未知可行性；1 个（`plumx_metrics`）因使用 `analytics/` 前缀、与已证实"仅限商业 Key"的 SciVal（`analytics/scival/...`）同构，大概率同样不可用。
  - 另发现参考项目的 `fulltext_retrieval` **不是新端点**，调用的正是本项目已实现的 `content/article/{id_type}/{id}`（即 `sciencedirect_article_retrieve_by_identifier` 背后的同一端点），差异只在于它请求 `Accept: text/plain` 而非 JSON，目的是拿到清洗过的纯文本全文而非结构化元数据。这是一个"响应格式变体"而非新功能，价值有限但成本极低（同一端点换一个 Accept 头）。
  - 工程实践方面观察到两点可能有参考价值、但都不是功能缺口：(1) 该项目在收到 401 时会自动尝试 `/authenticate` 端点做一次机构网络 IP 认证重试，这个机制只对处于机构网络内的调用方有意义，对本项目当前"非商业、无 Insttoken"的账号场景没有实际用处；(2) 该项目用 `ElsevierApiError` 自定义异常类把 HTTP 状态码与错误消息分开保存，而本项目当前 `except Exception as exc: _err(..., message=str(exc))` 依赖 httpx 异常的 `str()` 表示（已包含状态码文本），效果上大体等价但结构化程度较低。
  - 按项目一贯的"真实 API 验证优先"原则，以下 3 个新候选**均未做真实调用验证**，在获得用户确认要不要投入验证之前，不预判其可行性、也不直接建议采纳。
- **问题列表**
  1. **`serial_title_search`**（端点 `content/serial/title`，按期刊标题/出版商/学科代码/OA 状态等条件搜索期刊，不要求预先知道 ISSN）——与本项目已验证可用的 `content/serial/title/issn/{issn}` 同属期刊元数据资源族，价值在于补齐"不知道 ISSN、只想按主题/出版商找期刊"的场景。是否希望投入一次真实 API 探测来验证当前 Key 下是否可用（HTTP 200）？如果验证通过，是否原则上同意把它纳入未来版本的候选范围（作为 `scopus_serial_title_by_issn` 的姊妹工具）？
  2. **`subject_classifications`**（端点 `content/subject/{scopus|scidir}`，查询 Scopus ASJC 学科分类代码/缩写/说明，或 ScienceDirect 学科分类代码）——本文档此前完全没有调研过这个端点，可行性未知。价值在于给用户提供"学科代码速查"能力，间接帮助构造更精确的 Scopus 搜索查询（如 `SUBJAREA(COMP)`）。是否希望投入真实验证？
  3. **`plumx_metrics`**（端点 `analytics/plumx/{id_type}/{id_value}`，PlumX 替代计量学指标——使用量/收藏/社交媒体提及等）——因为它和已证实"仅商业性质 Key 可访问"的 SciVal 同属 `analytics/` 路径前缀，结构上高度可疑同样受限（但不是 100% 确定，两者是否共用同一权限判定逻辑并未验证过）。是否仍希望花一次真实探测请求做实锤确认，还是基于这个同构证据直接判定"大概率不可用"、本轮不再单独测试、留到未来订阅升级后再评估？
  4.（次要，供参考）`fulltext_retrieval` 这个"纯文本全文"变体，是否有兴趣顺带验证一下——用同一个 `retrieve_article`/`sciencedirect_article_retrieve_by_identifier` 已经在用的端点，换成 `Accept: text/plain` 请求头，看当前 Key 能否拿到比现有 `view=META` 更完整的正文纯文本？如果没兴趣，我们就不再展开。
- **用户回答**
  1. 验证一下
  2. 验证一下
  3. 验证一下
  4. 验证一下
- **提炼结论**
  - 用户对全部 4 项均要求"验证一下"，即便本 agent 已给出"`plumx_metrics` 与 SciVal 同构、大概率不可用"的初步判断，用户仍坚持要真实实测而非采信同构推断——已用 `.env` 中真实 Elsevier Key（临时探测脚本 `probe_qa_r007.py`，位于会话 scratchpad，未纳入仓库）对四项各发起真实请求，结果记录在附录新增小节"实测可行性探测（2026-08-04，QA-R007 新候选项）"。
  - **`serial_title_search`（期刊搜索）：实测可用（HTTP 200）**。返回 `serial-metadata-response.entry[]`，字段结构与已实现的 `scopus_serial_title_by_issn` 高度一致，另有 `SNIPList`/`SJRList` 期刊计量指标是现有工具未提取的增量字段。本 agent 专业判断：**值得纳入候选范围**，作为 `scopus_serial_title_by_issn` 的姊妹工具，补齐"不知道 ISSN、只想按标题/出版商/学科搜期刊"的场景，技术风险低（同资源族、同订阅层级）。
  - **`subject_classifications`（学科分类查询）：实测可用（HTTP 200）**。返回 `subject-classifications.subject-classification[]`，字段简单扁平（`code`/`description`/`detail`/`abbrev`），真实样本验证通过。本 agent 专业判断：**值得纳入候选范围**，可作为独立小工具，帮助用户查学科代码以构造更精确的 Scopus 查询（如 `SUBJAREA(COMP)`），实现成本低。
  - **`plumx_metrics`：实测不可用（401 AUTHENTICATION_ERROR）**。印证了此前"与 SciVal 同属 `analytics/` 前缀、大概率同样受限"的判断，虽具体错误码与 SciVal 的 403 ENTITLEMENTS_ERROR 不同，但结论一致——当前非商业 Key 无权访问。本 agent 专业判断：**排除**，已记录到"范围界定/排除"表格，理由与既有 SciVal 排除项保持同一逻辑（账号类型不满足，非代码问题，未来若拿到商业 Key 可重新评估）。
  - **`fulltext_retrieval` 纯文本变体：实测不可用（400 INVALID_INPUT，与 view 参数取值无关）**。同一端点换 `Accept: application/json`/`text/xml` 均正常 200，唯独 `text/plain` 协商方式固定报错，现象与错误文案本身不一致（错误说"view 参数无效"，但不传 view 一样报错），怀疑是账号对该纯文本输出格式本身不受支持/未被订阅覆盖，Elsevier 用了措辞有误导性的校验错误表达。本 agent 专业判断：**排除**，且不建议为查明这个错误文案的真实语义投入更多探测精力——它本来就不是新能力（同一端点、同一数据，JSON 归一化已覆盖等价信息），性价比低。已记录到"范围界定/排除"表格。
  - **总结**：4 项候选中 2 项（`serial_title_search`、`subject_classifications`）实测通过、建议纳入未来版本候选范围；2 项（`plumx_metrics`、`fulltext_retrieval` 纯文本变体）实测确认不可用/无增量价值、建议排除，已记录排除原因。是否正式把前两项纳入某个具体版本的开发范围（核心目标/包含范围），仍需用户明确拍板（本轮 QA 用户只回答了"验证一下"，尚未对"验证通过后是否纳入"给出最终意见），留待用户确认后再补充版本号与具体范围条目，或开启新一轮 QA 记录。
- **影响的目标文档章节**
  - 核心目标 / 范围界定（包含/排除） / 附录：Elsevier API 现状盘点
  <!-- GOAL-QA-R007-END -->

### QA-R008：v2.3.0 正式立项——`serial_title_search` + `subject_classifications` 纳入开发范围
<!-- GOAL-QA-R008-START -->
- **提问时间**：2026-08-04 13:53
- **提问目的**：QA-R007 已用真实 Elsevier Key 实测确认 `serial_title_search`（期刊搜索）、`subject_classifications`（学科分类查询）均可用（HTTP 200），但当轮用户只回答"验证一下"，未对"验证通过后是否正式纳入某个版本"表态，本 agent 在上一轮结尾主动留了这个待确认问题。本轮用户已通过协调方明确答复，直接完成立项确认，不需要再像 v2.2.0 那样单独开一轮问版本号（用户已直接指定 `2.3.0`）。
- **问题列表**（本轮为用户主动确认，非本 agent 追问触发，问题以"待确认事项"形式记录）
  1. `serial_title_search`、`subject_classifications` 是否正式纳入下一版本开发范围？版本号是多少？
- **用户回答**
  1. "纳入下一版本 v2.3.0 的开发范围，继续完善 project-docs/goal.md 以便规划计划"
- **提炼结论**
  - **版本号确认为 `2.3.0`**，用户直接指定，无需像 v2.2.0（QA-R005）那样单独走一轮版本号确认流程。
  - **v2.3.0 范围边界明确为"纯新增两个工具"，与此前两个版本性质不同，需要在文档中讲清楚以避免后续误解**：
    - v2.1.0＝删除 6 个已发布但不可用的工具（清理故障）。
    - v2.2.0＝删除 1 个别名工具 + 剩余 10 个工具全部破坏性重命名 + `list_papers` 功能补全 + 2 处归一化（改造性质，涉及全部现有工具）。
    - **v2.3.0＝仅新增 2 个工具**（`serial_title_search`、`subject_classifications` 对应的新 MCP 工具），**不删除、不重命名、不改动任何现有 10 个工具的名称/参数/返回结构/注册顺序**。这是纯粹的能力扩展（Additive/Feature 版本），风险面和 v2.1.0/v2.2.0 完全不同，project-planner-cn 制定构建计划书时只需规划"新增"相关的步骤，不应顺带评估或触碰现有 10 个工具。
  - **落地细节（供 project-planner-cn 直接使用，不必回头翻 QA-R007 探测记录）**：
    - **`serial_title_search`**：
      - 端点：`content/serial/title`（GET，query 参数搜索，区别于已实现的 `content/serial/title/issn/{issn}` 单 ISSN 精确查询）。
      - 文件归属：**`src/uniarticles/sources/scopus.py`**（与同源的 `scopus_serial_title_by_issn` 放在一起，复用同文件已有的 `_get_headers()`/`BASE_URL`/`_ok`/`_err`/`_as_list` 等既有工具函数，不新建模块）。
      - 建议命名（方案 A 风格，本 agent 拟定，project-planner-cn 如有更贴切方案可在构建计划书中调整，但需说明理由、保持方案 A 风格不变）：**`scopus_serial_title_search_by_criteria`**（不用 `_by_title`，因为端点实际支持 `title`/`issn`/`pub`/`subj`/`oa`/`content`/`date` 等多个可选检索条件的任意组合，命名为 `by_title` 会像 QA-R004 发现的 `list_papers` 问题一样"承诺了实现不具备的单一维度"，用 `_by_criteria` 更如实反映"多条件组合搜索"这一实际能力）。
      - 已通过真实探测确认的响应字段（`title=Cell&count=5` → 200）：根为 `serial-metadata-response.entry[]`，单条 entry 至少含 `dc:title`/`dc:publisher`/`prism:issn`/`prism:eIssn`/`prism:aggregationType`/`coverageStartYear`/`coverageEndYear`/`openaccess`/`openaccessType`/`subject-area[]`（`@code`/`@abbrev`/`$`）/`link[]`（含 `@ref=homepage`/`@ref=coverimage`/`@ref=scopus-source`）/`prism:url`/`source-id`，另外还观察到 `SNIPList.SNIP[]`/`SJRList.SJR[]`（期刊计量指标，按年份列出 SNIP/SJR 值）——这是现有 `scopus_serial_title_by_issn` 归一化字段里**没有**提取的新字段，是否要在新工具里补充提取由 project-planner-cn/project-builder-cn 决定。
      - 参考项目额外支持的可选参数：`pub`（出版商）、`subj`（学科代码）、`content`（journal/tradejournal/conferenceproceeding/bookseries）、`date`、`oa`（all/full/partial/none）、`start`（分页偏移）、`count`（每页数量，文档标注上限 200）、`view`（STANDARD/ENHANCED/CITESCORE）——这些参数**均未在真实探测中逐一测试**，只测过 `title` 单一条件，具体见下方"尚待探测的细节"。
    - **`subject_classifications`**：
      - 端点：`content/subject/{source}`，`{source}` 取值 `scopus` 或 `scidir`（GET，可选 query 参数 `description`/`detail`/`code`/`abbrev`/`field` 做过滤）。
      - 这是一个**全新概念的工具**（本项目此前没有任何"学科分类代码查询"能力），不依附于文献检索/期刊检索，而是辅助用户构造更精确查询用的元数据速查工具。
      - 文件归属判断：**同样放入 `src/uniarticles/sources/scopus.py`**（本 agent 的判断：虽然该端点通过 `source` 参数同时覆盖 Scopus 和 ScienceDirect 两套分类体系，功能上不完全等同"纯 Scopus"，但 (a) 端点路径前缀是通用的 `content/subject/`，不属于 ScienceDirect 专属的 `content/article`/`content/object` 家族；(b) 现有 `scopus_serial_title_by_issn` 已经开了"Elsevier 内容级通用概念放进 scopus.py"的先例；(c) 单独为一个小工具新建模块会增加文件数量但收益不明显。project-planner-cn 若认为应新建独立模块，可在构建计划书中提出并说明理由，本决定非不可更改的硬性约束）。
      - 建议命名（方案 A 风格，本 agent 拟定）：**`scopus_subject_classification_lookup_by_source`**（`source` 是该端点唯一必填参数，其余 `description`/`detail`/`code`/`abbrev`/`field` 均为可选过滤条件，参照现有 `scopus_abstract_detail_by_eid` "detail_by_主键参数" 的命名思路）。
      - 已通过真实探测确认的响应字段（`source=scopus&description=computer` → 200）：根为 `subject-classifications.subject-classification[]`，每项字段扁平、无嵌套：`code`（字符串数字，如 `"1700"`）、`description`（大类名，如 `"Computer Science"`）、`detail`（细分学科名，如 `"Artificial Intelligence"`）、`abbrev`（大类缩写，如 `"COMP"`）。
      - **`source=scidir`（ScienceDirect 学科分类）分支完全未测试**，真实响应结构是否与 `source=scopus` 一致（字段名是否相同）未知，不能凭空假设一致。
  - **尚待探测的细节（如实标注，留给 project-builder-cn 在正式构建阶段补充真实探测，不在本文档凭空补全）**：
    1. `serial_title_search`：`issn`/`pub`/`subj`/`content`/`date`/`oa`/`start`/`count`/`view` 等参数逐一的真实调用效果未测试（只测过纯 `title` 条件）；不带任何检索条件调用会返回什么（参考项目在 TS 客户端侧做了"至少需要 title/issn/pub/subj 之一"的前置校验，但这只是参考项目自己的实现选择，不代表 Elsevier 服务端本身的真实行为，本项目要不要照搬这个前置校验、或服务端在零条件下到底是报错还是返回全量数据，需要真实探测确认）；`count` 参数的服务端实际上限是否真的是 200（该值来自参考项目 Zod schema 的注释，未在本项目端验证）；无效/不存在的 `subj` 学科代码时的错误行为。
    2. `subject_classifications`：`source=scidir` 分支未测试，字段结构未知；`code`/`abbrev`/`field` 精确过滤参数的真实调用效果未测试；`source` 传入非法值（既非 scopus 也非 scidir）时的错误响应未测试；不带任何过滤条件、只传 `source` 时的响应体量级未知（学科分类总数可能较大，需要确认是否需要分页或客户端提示）。
    3. 两个工具的错误处理（无效标识符/无匹配结果/权限不足等边界情况）尚未真实触发过，需要 project-builder-cn 按项目现有 `_ok`/`_err` 规范真实测试后再确定归一化的降级行为。
  - **两个新工具均须遵循项目现有的 `_ok`/`_err` 统一响应结构规范**（`{"ok", "source", "query", "count", "items", "error"}`），与现有 10 个工具保持完全一致的对外契约，不引入新的响应结构。
- **影响的目标文档章节**
  - 核心目标 / 目标用户 / 期望成果 / 成功标准 / 范围界定（包含） / 约束条件
  <!-- GOAL-QA-R008-END -->

### QA-R010：v3.0.0 调研——`paper-search-mcp-main` 与 `research-superpower-main` 源码核实结论，候选新数据源确认
<!-- GOAL-QA-R010-START -->
- **提问时间**：2026-08-04 20:32

- **提问目的**：v2.3.0（12 个工具）已发布。用户浏览了《Zotero 加 Codex：2026最新科研 Skills 合集，从找文献到写综述.md》一文里列出的全部科研相关项目，认为除 2 个外均无参考价值，自行下载了 `reference-projects/paper-search-mcp-main`（对应文章里的 `openags/paper-search-mcp`）与 `reference-projects/research-superpower-main`（对应文章里的 `kthorn/research-superpower`）到本地（该目录已被 `.gitignore` 排除，不提交仓库），要求本 agent 实际阅读源码/README，识别本项目当前 4 个数据源（Scopus/ScienceDirect/ArXiv/PubMed）完全未覆盖过的候选新数据源，并区分"真正的新数据源"与"同一数据源的更好实现方式"。本 agent 已逐一阅读两个项目的 README 全文、`paper-search-mcp-main` 的 `academic_platforms/` 目录下全部 26 个连接器源码（含逐一核实 arxiv.py/pubmed.py/semantic.py/openalex.py/crossref.py/biorxiv.py/core.py/unpaywall.py/ieee.py/acm.py）、`server.py` 的全部工具注册、`research-superpower-main` 的全部 9 个 `SKILL.md`，以及本项目自身的 `src/uniarticles/sources/arxiv.py`。核实结论如下（供下方问题列表引用）：

  **A. `paper-search-mcp-main` 核实结论**：这是一个真正的多源 MCP Server（不是流程/技能），`academic_platforms/*.py` 每个数据源一个 `PaperSource` 子类，`server.py` 注册了 60+ 个 `@mcp.tool()`（search_x/download_x/read_x 三件套 × 20+ 数据源 + 跨源统一 `search_papers` + `download_with_fallback`）。逐一核实覆盖的数据源中，与本项目现有 4 个数据源完全不重叠的候选，按推荐优先级列出：

    | 候选数据源 | Key 要求 | 限流/稳定性（README+代码核实） | 与本项目定位（查询检索为主，goal.md 已排除下载类功能）的契合度 |
    |---|---|---|---|
    | **Semantic Scholar** | 免费，无需 key 可用（有 key 提升 100→1000 req/5min），代码对 429/403 有自动重试+去 key 重试逻辑 | 较好，官方限流明确 | 高：字段丰富（citations/DOI/openAccessPdf），是通用学术图谱型数据源，**推荐重点候选** |
    | **OpenAlex** | 完全免费，无需 key（UA 带 email 可进 polite pool 提升限额） | 好，公开 REST API，代码实测字段解析完整 | 高：覆盖 2 亿+ 学术作品元数据，**推荐重点候选** |
    | **Crossref** | 完全免费，无需 key（`mailto` 参数进 polite pool），代码有 429 重试 | 好 | 高：DOI 注册权威库，覆盖几乎所有有 DOI 的出版物元数据，**推荐重点候选** |
    | PMC / Europe PMC | 免费公开 API | 较好 | 中：偏向本项目已有 PubMed 的姊妹/补充数据源，非独立新领域 |
    | bioRxiv / medRxiv | 免费公开 API | 好，但**官方 API 本质是"按分类+日期区间浏览"**（`api.biorxiv.org/details/biorxiv/{start}/{end}/{cursor}`），paper-search-mcp 代码把 `query` 参数当作"分类名"而非关键词，不是真正的全文检索 | 中：如接入需按"浏览"语义设计，不能承诺关键词搜索体验 |
    | DOAJ | 免费公开 API，key 可选（提升限额） | 一般 | 中：聚焦"是否有免费全文"，与开放获取期刊目录场景相关 |
    | CORE | 推荐但非强制 key，无 key 限流更严，代码有 401/403 自动降级重试 | 一般 | 中：全球 OA 论文聚合器，规模大但依赖 key 体验更好 |
    | Zenodo / HAL / dblp / OpenAIRE | 均免费公开 API，无需 key | OpenAIRE 代码里有"3次重试+逐步升级请求头"应对 403，说明服务端不太稳定；其余较好 | 中低：分别偏窄（数据仓储/CS专领域/欧盟聚合），非通用检索核心 |
    | SSRN / CiteSeerX / BASE | — | README 明确标注不稳定：SSRN "403 bot-detection"；CiteSeerX "间歇性不可用/重定向到网页存档"；BASE "需机构 IP 注册，否则优雅返回空" | 低，不推荐 |
    | **Unpaywall** | 需配置联系邮箱（`PAPER_SEARCH_MCP_UNPAYWALL_EMAIL`） | 好 | **低**：代码核实其 `search()` 本质是"给定 DOI 查开放获取全文位置"的单条查找（`max_results` 形同虚设，最多返回 1 条），不是关键词检索接口，产品语义更接近"全文下载兜底工具"，与 goal.md 已排除的下载类功能高度相关，不建议引入 |
    | Google Scholar / Sci-Hub | — | Google Scholar 标注"bot-detection，需代理"（本项目 v2.1.0 已因同类问题删除过 `searchScholarPapers`）；Sci-Hub 项目自己定性为"法律/合规风险因司法辖区而异" | 不推荐 |
    | **IEEE Xplore / ACM DL** | 需付费/申请商业 key | 代码核实：即便配置了 key，`search()` 仍无条件 `raise NotImplementedError`（含 `# TODO: implement real IEEE Xplore REST call here once key is available` 注释）——**是作者自己也还没写完的空壳，不是真实可用的功能，不构成有效候选** | 不推荐，且不符合免费/公开优先路线 |

  **B. `research-superpower-main` 核实结论**：**这不是 MCP Server / 独立数据获取工具集，而是一套 Claude Code Skills（`skills/research/*/SKILL.md`）+ hooks 的"文献研究工作流编排"插件**——逐一读取全部 9 个 SKILL.md 确认，其实现方式是在 Markdown 里教 Claude 在什么阶段执行哪些裸 `curl` 命令，没有任何源码、没有 MCP tool 注册、没有可复用的客户端封装。其调用的底层数据源核实如下，**均与本项目已有数据源或 `paper-search-mcp-main` 已覆盖的数据源完全重叠，没有任何独立新增数据源**：
    1. PubMed E-utilities（`esearch.fcgi`/`esummary.fcgi`）——本项目已有，`paper-search-mcp-main` 也已有。
    2. Semantic Scholar Graph API（论文查找/引用/被引）——`paper-search-mcp-main` 已覆盖（`search_semantic`）。
    3. Unpaywall（开放获取全文查找）——`paper-search-mcp-main` 已覆盖（`search_unpaywall`）。
    4. **ChEMBL API**（`www.ebi.ac.uk/chembl/api/data/`，仅接受 DOI 查询，返回结构化药物化学 SAR 数据如 IC50/MIC/Ki）——是本次调研中**唯一在 `paper-search-mcp-main` 里也没出现过的全新端点**，但它不是论文搜索/元数据源，而是窄分领域化学生物活性数据库（仅覆盖约 9.9 万篇医药化学论文），仅在"已有一篇药物化学论文 DOI、想查它是否被 ChEMBL 收录并结构化提取过 SAR 数据"这一具体场景下才有意义，与本项目当前"通用学术文献检索"定位的相关性存疑，性质上更接近"文献的关联数据补充"而非"多一个可搜索的论文来源"。
      **结论：`research-superpower-main` 对本项目"新增数据源"目标没有增量价值**。它真正有参考价值的部分是"工作流方法论"（引用追踪相关性打分规则、两阶段筛选流程、去重与断点续跑设计等），但这些是面向 LLM 客户端自身推理行为的提示词工程/工作流设计，不是 MCP Server 该实现的"数据获取工具"范畴，不建议作为 v3.0.0 的功能改造依据。

  **C. 现有数据源（arxiv/pubmed）可借鉴的实现细节（非新数据源，单独归类，不与 A/B 混为一谈）**：
    1. **arXiv DOI 字段缺失**：`paper-search-mcp-main` 的 `arxiv.py` 为每篇论文提取 `doi` 字段（优先取 `entry.doi`，缺失时正则兜底提取）。核实本项目 `src/uniarticles/sources/arxiv.py` 的 `_serialize_paper()`（第 53-62 行）完全没有输出 `doi` 字段，而本项目依赖的第三方 `arxiv` 库（`.venv/Lib/site-packages/arxiv/__init__.py` 第 71/123/158 行）其 `Result` 对象本身就自带 `.doi` 属性（从 Atom feed 的 `arxiv_doi` 解析），**这是零额外请求成本就能拿到的字段，当前是"库已给但没透出"的疏漏**，可作为独立于新数据源决策之外的小改进项。
    2. **arXiv 网络重试**：`paper-search-mcp-main` 手写了 3 次重试+指数退避；核实本项目使用的 `arxiv` 库 `Client` 类本身已内置 `num_retries`（默认 3）/`delay_seconds`（默认 3.0）重试机制（同文件第 585-623 行），**本项目已有等价能力，不构成缺口**，仅作记录避免误判。
    3. **PubMed**：`paper-search-mcp-main` 手写 esearch+efetch；本项目通过第三方 `paperscraper`→`pymed_paperscraper` 间接调用同样的 NCBI 官方端点。（编者按：原文此处曾引用"QA-R009 已对 PubMed 侧实现方式/改名/依赖精简做过更深入的核实"——该轮次已因用户明确放弃 v2.4.0、直接对齐 v3.0.0，被主线程用 `git revert c316c98`（提交 `d44d066`）从本文档移除，相关调研内容不再存在于本文档中，此处的深入核实不再可引用，仅保留"两者是同源 NCBI API 包装"这一事实性结论。）

- **问题列表**
  1. A 部分里本 agent 判断"较优、免费公开、限流可控、且与产品定位相符"的是 Semantic Scholar / OpenAlex / Crossref 三个。是否将其中若干个（或全部）正式纳入 v3.0.0 候选范围，交给 project-builder-cn 做真实 API 可行性验证（比照本项目一贯"文档判断→真实调用验证→再决定"的方法论）？还是你对 PMC/Europe PMC/dblp/Zenodo/DOAJ/CORE/OpenAIRE/HAL 等分领域数据源有额外的兴趣或排除意见？
  2. bioRxiv/medRxiv 的公开 API 本质是"按分类+时间窗口浏览"而非关键词全文搜索——如果仍然感兴趣，是否接受这种"浏览"语义（类似本项目已有的 `arxiv_latest_paper_list_by_category`），而不是期待关键词搜索体验？
  3. Unpaywall/Sci-Hub/IEEE/ACM/SSRN/CiteSeerX/BASE/Google Scholar，本 agent 判断均不建议纳入 v3.0.0（理由见 A 表格），是否认可这个排除判断？
  4. `research-superpower-main` 的核实结论是：它是工作流插件而非独立数据源工具集，四个底层 API 中三个已被 `paper-search-mcp-main` 覆盖，唯一全新的 ChEMBL 是窄分领域化学数据库、非通用论文检索源——是否认可"该项目对 v3.0.0 新数据源目标没有增量价值"这一判断？还是你对 ChEMBL（药物化学 SAR 数据附加查询）本身有独立兴趣，希望作为与"新增论文检索数据源"不同性质的功能单独评估？
  5. 关于 arXiv DOI 字段缺失（C.1）：是否要把"在现有 `arxiv_paper_search_by_query`/`arxiv_latest_paper_list_by_category`/`arxiv_paper_detail_by_id` 三个工具的输出里补充 `doi` 字段"也一并纳入本轮范围（这是对现有工具的小幅增强，不是新增数据源，理论上可独立于新数据源决策先做）？
  6. **版本规划**：goal.md 中存在一个来自上一次会话、**尚未回答**的 QA-R009（v2.4.0，`paperscraper.py` 改名+依赖选型+PubMed 新增 ESummary/ELink 的决策请求），与本轮 v3.0.0（新数据源）是两条独立的待办线。是否需要先回答 QA-R009 确定 v2.4.0 范围、再启动 v3.0.0（即 v2.4.0 → v3.0.0 顺序发布），还是两者合并成一轮更大的版本（例如直接对齐到 v3.0.0，把 paperscraper 改造和新数据源一起做）？这个顺序决策会影响后续 project-planner-cn 的版本号命名，需要你明确。（编者按：本问题提出时 QA-R009 仍存在于本文档中；用户随后在主线程明确要求撤销 QA-R009 对应的提交，本轮问题 6 的回答已实质确认"跳过 v2.4.0，直接对齐 v3.0.0"，QA-R009 已被移除，此问题的历史文本保留以追溯提问背景，不代表 QA-R009 仍然存在。）
  
- **用户回答**
  1. 将全部都纳入项目中，针对每个数据源单独创建src下的脚本文件，分类明确
  2. 也纳入项目中，但明确说明局限性
  3. 认可排除判断
  4. chembl有独立兴趣，希望能增加该数据源的检索
  5. 也纳入本轮范围，可以列为一个独立步骤，先完成它
  6. 本次版本就是3.0.0版本，跳过原本的2.4.0版本
  
- **提炼结论**
  - **问题1（部分确认，范围边界仍有歧义，需 QA-R011 收敛）**：用户回答"将全部都纳入项目中"，但 A 表格里的候选分了三档——3 个"推荐重点候选"（Semantic Scholar/OpenAlex/Crossref）与 8 个"中等价值"分领域候选（PMC/Europe PMC/DOAJ/CORE/Zenodo/HAL/dblp/OpenAIRE），"全部"具体指哪一档存在歧义，且中等价值候选此前只做了 README+代码逻辑核实，没有做过真实 API 探测，与本项目"真实验证优先"的一贯方法论存在落差，不能在歧义未消解、且未做真实验证前直接照单全收执行。至少可以确认：3 个推荐重点候选（Semantic Scholar/OpenAlex/Crossref）无论如何都在范围内。中等价值 8 个候选是否全部纳入、是否需要先逐一真实探测，已转入 QA-R011 继续澄清。
  - **架构决策（已确认，无歧义）**：新增数据源"针对每个数据源单独创建 src 下的脚本文件，分类明确"，即遵循本项目现有的 source-module 模式（一个数据源一个文件、暴露 `register(server)`），不新建其他组织方式。
  - **问题2（已确认）**：bioRxiv、medRxiv 纳入 v3.0.0 候选范围，用户接受其官方 API"按分类+时间窗口浏览"而非关键词全文检索的语义局限性，要求在实现和文档中明确说明这一点，不得暗示支持任意关键词搜索。
  - **问题3（已确认）**：Unpaywall、Sci-Hub、IEEE Xplore、ACM Digital Library、SSRN、CiteSeerX、BASE、Google Scholar 全部排除出 v3.0.0 范围，用户认可 QA-R010 A 表格给出的排除理由（DOI查找而非检索/合规风险/未实现的空壳/不稳定/需机构IP/bot-detection 等）。
  - **问题4（已确认，产品定位需如实记录差异）**：ChEMBL 纳入 v3.0.0，用户明确表示"有独立兴趣，希望能增加该数据源的检索"。但需要如实记录一个产品定位上的差异：ChEMBL 不接受关键词检索，只接受 DOI 查询（`document.json?doi=...`），本质是"给定一篇已知 DOI 的论文，查它是否被 ChEMBL 收录及其结构化 SAR/生物活性数据（IC50/MIC/Ki 等）"，是文献的关联数据查询工具，不是与 Semantic Scholar/OpenAlex/Crossref 同类的"关键词搜论文"工具。project-planner-cn/project-builder-cn 设计该工具的参数签名时必须体现这个差异（`doi` 必填，而非 `query`+`max_results`），避免被误设计成关键词检索接口。
  - **问题5（已确认）**：在现有 `arxiv_paper_search_by_query`/`arxiv_latest_paper_list_by_category`/`arxiv_paper_detail_by_id` 三个工具的输出中补充 `doi` 字段，列为本轮一个独立、可优先完成的步骤（不依赖新数据源接入进度，可以先做）。
  - **问题6（已确认）**：目标版本号直接对齐为 **`3.0.0`**，跳过原本规划中尚未启动的 `2.4.0`。原 QA-R009（v2.4.0，`paperscraper.py` 改名+依赖选型+PubMed 新增 ESummary/ELink 的决策请求）由此作废，用户已在主线程明确要求撤销其对应提交，coordinator 已执行 `git revert c316c98`（提交 `d44d066`）将 QA-R009 从"澄清问答记录"中完整移除；QA-R010 正文中原本对 QA-R009 的两处引用（C.3、问题列表问题 6）已改为说明性编者按，不再指代实际存在的轮次。paperscraper.py 的改名/依赖精简/PubMed 功能扩展若未来仍需处理，需作为一次新的、独立的目标澄清重新发起。
- **影响的目标文档章节**
  - 核心目标 / 范围界定（包含/排除） / 约束条件
  <!-- GOAL-QA-R010-END -->

### QA-R011：v3.0.0 范围收敛——"全部纳入"候选数据源的边界确认
<!-- GOAL-QA-R011-START -->
- **提问时间**：2026-08-04 21:16
- **提问目的**：QA-R010 问题 1 用户回答"将全部都纳入项目中"，但 QA-R010 的 A 表格把候选数据源分了三档——3 个"推荐重点候选"（Semantic Scholar/OpenAlex/Crossref，README+代码核实较充分）与 8 个"中等价值"分领域候选（PMC/Europe PMC/DOAJ/CORE/Zenodo/HAL/dblp/OpenAIRE，核实程度明显更粗略，仅凭 README 描述+代码逻辑判断，均未做过真实 API 请求验证）。"全部"具体指哪一档、是否包含全部 8 个中等价值候选，直接决定 v3.0.0 是"新增 3 个数据源"还是"新增 11+ 个数据源"，工作量与真实验证覆盖范围差异巨大，不能由本 agent 自行猜测执行，必须问清楚。同时，本项目一贯坚持"真实验证优先"（同 QA-R001/QA-R002/QA-R007 的方法论），若中等价值候选也要纳入，需要确认是否要求正式开发前逐一做真实探测。
- **问题列表**
  1. QA-R010 问题 1 的"全部都纳入"，具体范围是：(a) 仅 3 个推荐重点候选（Semantic Scholar/OpenAlex/Crossref）；(b) 3 个推荐重点候选 + 8 个中等价值分领域候选（PMC/Europe PMC/DOAJ/CORE/Zenodo/HAL/dblp/OpenAIRE），合计 11 个新数据源；(c) 其他组合（请具体列出包含/不包含哪些）？
  2. 如果最终确认是 (b) 或包含中等价值候选的其他组合，是否要求在正式开发前，比照本项目一贯的"真实验证优先"方法论，对每一个候选逐一做真实 API 探测（确认端点可用性、限流表现、真实字段结构），再由 project-planner-cn/project-builder-cn 据实制定实现方案？（本 agent 判断这是必要步骤，因为中等价值候选目前只核实了 README 描述和代码逻辑，没有做过真实请求验证）
  3. （可选，若你希望进一步收窄）中等价值 8 个候选里，是否有你认为明显应该排除或明显应该优先的？例如 CORE 需要注册免费 key 才能获得较好体验（无 key 限流更严）、OpenAIRE 参考项目代码显示服务端不太稳定（有 3 次重试+逐步升级请求头应对 403 的复杂逻辑）——这类信息是否影响你的取舍？
- **用户回答**
  1. 把11个候选源全部纳入
  2. 是的，对每一个源都进行真实性探测
  3. 先测试再说
- **提炼结论**
  - **问题1（已确认，范围收敛为最大档）**：用户明确选择"把 11 个候选源全部纳入"，即 3 个推荐重点候选（Semantic Scholar、OpenAlex、Crossref）与全部 8 个中等价值候选（PMC、Europe PMC、DOAJ、CORE、Zenodo、HAL、dblp、OpenAIRE）无一保留地全部纳入 v3.0.0。加上 QA-R010 已确认的 bioRxiv/medRxiv（浏览语义）、ChEMBL（DOI 查询语义）两个语义特殊的数据源，以及 arXiv 补 `doi` 字段这一现有工具增强项，**v3.0.0 合计新增 13 个数据源/功能点**（11 个通用检索型新数据源 + 2 个语义特殊的新数据源 + 1 个现有工具增强），是本项目至今为止规模最大的一轮版本——此前最大的单轮范围扩张是 v2.2.0（QA-R004~QA-R006，删除1个+重命名10个+功能补全1个+归一化2个+注册顺序调整1个，共影响约 14 处但不涉及新增数据源模块），而本轮是净新增 13 个全新数据源/功能点，规模量级明显更大，必须在文档中如实体现，不能用"新增若干数据源"这类轻描淡写的措辞。
  - **问题2（已确认）**：用户明确要求"对每一个源都进行真实性探测"，即全部 11 个通用检索候选（不只是此前已核实较深的 3 个推荐重点候选）在正式写入构建计划书/开始实现前，都必须先由 project-builder-cn（或本 agent）用真实请求逐一验证端点可用性、限流表现、真实字段结构，延续本项目自 QA-R001/QA-R002 起一贯坚持的"真实验证优先"方法论，不允许仅凭参考项目 README 描述或代码逻辑就直接假设可用并开始实现。
  - **问题3（已确认，不预先取舍）**：用户回答"先测试再说"，即不对 8 个中等价值候选做预先的优先级排序或预先排除（例如不因为"CORE 需要 key"或"OpenAIRE 服务端不稳定"这类线索就预先降低优先级），全部 11 个候选以同等地位进入真实探测环节，取舍留到真实探测结果出来后再做判断。
  - **规模提示（供 project-planner-cn 组织计划书参考，非用户直接决策，见下方约束条件的说明）**：11 个候选源的真实探测本身就是一项工作量庞大的前置任务（需要为每个数据源准备探测请求、记录响应、判断是否可行），project-planner-cn 在制定构建计划书时需要认真考虑如何拆分组织（例如是否先出一版"11 源探测结果汇总"再统一决定实现顺序，还是探测+实现按数据源逐个串行推进），具体组织方式由 project-planner-cn 判断，本文档不代为规定。
- **影响的目标文档章节**
  - 核心目标 / 范围界定（包含） / 约束条件 / 备注
  <!-- GOAL-QA-R011-END -->

### QA-R012：project-builder-cn 步骤28-33探测后"技术可行但价值存疑"4项候选（Semantic Scholar/PMC/CORE/dblp）的最终去留裁决
<!-- GOAL-QA-R012-START -->
- **提问时间**：2026-08-05 14:34
- **提问目的**：project-builder-cn 完成步骤 28-33，对 13 个候选数据源/功能点逐一做真实 API 探测，9 个已确认落地并写入 buildlog.md（commit `008d509`），其余 4 个（Semantic Scholar、PMC、CORE、dblp）按约束条件中 QA-R011 已确认的止损规则——"技术可行但价值存疑"不由 project-planner-cn/project-builder-cn 自行拍板剔除，需汇总后交还用户做最终去留判断——被交还用户裁决。用户已在与本 agent（负责对话的助手）的交流中逐项回应，其中 PMC、Semantic Scholar 两项由该助手补充了技术核实依据，现将四项最终结论正式定案写入 goal.md。
- **问题列表**
  1. Semantic Scholar：探测阶段确认技术可行，但 API key 尚未到手，是否纳入 v3.0.0？
  2. PMC：探测阶段确认技术可行（走 NCBI Entrez API），但与现有 `paperscraper.py` 的 pubmed 工具高度同构，是否纳入 v3.0.0？
  3. CORE：探测阶段确认技术可行，但无 key 时限流严重（约 5 次请求锁 10 分钟），是否纳入 v3.0.0？
  4. dblp：探测阶段因 SSL 握手失败（HTTP 000）未能验证可行性，是否纳入 v3.0.0，或如何处理这一不确定状态？
- **用户回答**
  1. API Key 正在申请中，届时可用；并提出新架构需求：若未配置 Semantic Scholar 的 key，应不注册该工具，而非注册后调用时才报错。
  2. 用户设定判断条件："我想了解这个PMC和当前的paperscraper的实现上有多大的区别，如果PMC的实现会比依赖第三方API的paperscraper更稳定，则考虑做。"（助手随后核实：两者底层同为 NCBI Entrez API 封装，PMC 无稳定性优势，仅内容范围收窄，条件未成立）
  3. API Key 已申请到，已配置在项目根目录 `.env` 文件的 `CORE_API_KEY` 变量下，此前限流顾虑解除。
  4. 尚未回报新网络环境下的探测结果，本轮不做最终判定，等后续复测结果。
- **提炼结论**
  - **问题1（已确认，纳入）**：Semantic Scholar 纳入 v3.0.0，但落地方式需支持"无 key 不注册工具"的条件注册模式——这是本项目至今第一次出现的新架构分支，与现有 Elsevier 套路（无条件注册、缺 key 时运行时报错）不同，需 project-planner-cn 在构建计划书中明确设计并权衡是否推广到其他数据源（不在本轮 goal.md 中代为决定，见约束条件）。
  - **问题2（已确认，排除）**：PMC 排除，不纳入 v3.0.0。依据是用户自设条件（"更稳定则做"）经技术核实未成立——`paperscraper.py` 的 `_search_pubmed()` 与候选 PMC 均为 NCBI Entrez 官方 API（`esearch`/`efetch`/`esummary`）的封装，仅 `db` 参数从 `pubmed` 换成 `pmc`，PMC 相较现有实现没有稳定性提升，唯一区别是内容范围收窄（仅覆盖 PMC 全文开放获取子集）。此推理链已记入范围界定/排除表格。
  - **问题3（已确认，纳入）**：CORE 纳入 v3.0.0，key 已配置在 `.env` 的 `CORE_API_KEY`，此前"无 key 限流严重"的顾虑已解除，确认落地。
  - **问题4（待定，不代为判定）**：dblp 本轮不做最终判定，明确记录为"待定，等待用户提供新网络环境下的 dblp 探测结果后再补充最终 QA 决策"（可能是 QA-R013）。探测环境 SSL 握手失败已排除是 API key 问题（dblp.org 公开 API 不要求 key），具体是否为主机级网络拦截需换网络环境用已提供的分层诊断脚本复测确认。
  - **v3.0.0 范围现状小结**：13 个立项候选中，确认落地 11 个（OpenAlex、Crossref、Europe PMC、DOAJ、Zenodo、HAL、OpenAIRE、bioRxiv/medRxiv、ChEMBL、Semantic Scholar、CORE）；明确排除 1 个（PMC）；悬而未决 1 个（dblp，等 QA-R013）。
- **影响的目标文档章节**
  - 核心目标（新增第 21 条） / 范围界定（包含、排除） / 约束条件（新增 Semantic Scholar 条件注册架构提示、dblp 待定说明）
  <!-- GOAL-QA-R012-END -->

<!-- GOAL-QA-LOG-END -->

## 备注
- （v2.1.0，QA-R003，2026-08-03）目标澄清已完成，用户确认无需继续追问。下一步建议调用 `project-planner-cn` 基于本文档制定构建计划书，覆盖两块工作：① 删除 6 个工具（`downloadPaper`/`searchAuthors`/`getAuthorProfile`/`searchSciencedirect`/`getArticleMetadata`/`searchScholarPapers`）的代码、注册与测试引用；② 同步修改 README.md / README_ZH.md 的 Elsevier Key 说明与工具清单。目标发布版本号为 `2.1.0`，构建计划书应涵盖 `pyproject.toml` 版本号更新与 `project-docs/buildlog.md` 变更记录，再交由 `project-builder-cn` 落地执行。
- （v2.2.0，QA-R004/QA-R005/QA-R006，2026-08-03）本轮目标澄清（源自 `docs/TODO.md` 两条待办：移除 `search_paper` + 全量工具语义化重命名）已全部闭环，QA-R004~QA-R006 三轮问题均已获用户明确回答，文档中不再有"待定/待用户确认"的占位状态。下一步建议调用 `project-planner-cn` 基于本文档最终版制定 v2.2.0 构建计划书，覆盖五块工作：
  1. 删除 `search_paper`（`src/uniarticles/sources/arxiv.py`），无过渡期。
  2. 对删除后剩余的全部 10 个工具做一次性彻底重命名（方案 A 风格，`get_quota_status` 特别改为 `scopus_api_usage_status`），旧名字不保留、不设别名过渡期。
  3. `list_papers` 新增真正的 arXiv category 过滤能力（复用 `cat:` 查询语法，而非新增库参数或客户端二次过滤）。
  4. 新增 `get_abstract_details`/`retrieve_article` 的 JSON 归一化，**必须先由 project-builder-cn 做真实 API 探测确认响应体字段结构，再确定提取字段**，不得凭空编写归一化方案。
  5. 调整 `src/uniarticles/sources/__init__.py` 的 `register_all_sources()` 文件级调用顺序为 `scopus → sciencedirect → arxiv → paperscraper`，`scopus.py` 内部工具相对顺序不变，无需拆分注册逻辑。
  构建计划书必须包含用户明确要求的"6 维度工具改动清单表格"（要求详见"约束条件"章节，此处不重复），目标发布版本号为 **`2.2.0`**，构建计划书应涵盖 `pyproject.toml` 版本号更新与 `project-docs/buildlog.md` 变更记录，再交由 `project-builder-cn` 落地执行。
- （v2.3.0，QA-R007/QA-R008，2026-08-04）本轮目标澄清（源自调研本地参考项目 `reference-projects/elsevier-mcp-main/`，QA-R007 发现候选 + 真实 API 探测 + QA-R008 用户正式立项确认）已闭环，用户明确指定版本号 `2.3.0`，无待定事项。**下一步建议调用 `project-planner-cn` 基于本文档最终版制定 v2.3.0 构建计划书**，交接要点：
  1. **范围边界必须在计划书开头明确重申**：v2.3.0 是纯新增（Additive）版本，只新增 `serial_title_search`、`subject_classifications` 两个工具，**不得**顺带评估或改动现有 10 个工具的名称/参数/返回结构/注册顺序——这与 v2.1.0（删除）、v2.2.0（重命名+功能改造）的任务性质不同，务必在计划书里讲清楚以避免误将本轮当成又一轮"清理/重构"来做。
  2. **两个新工具的落地要点**（完整细节见"范围界定/包含"最后一条 + 附录"实测可行性探测（2026-08-04）"+ QA-R008 提炼结论，此处不重复）：均放入 `src/uniarticles/sources/scopus.py`；均遵循 `_ok`/`_err` 统一响应结构；建议命名 `scopus_serial_title_search_by_criteria`、`scopus_subject_classification_lookup_by_source`（方案 A 风格，可调整但须说明理由）。
  3. **构建前必须先做真实探测补测，不得凭空写归一化方案**：本轮 QA-R007/QA-R008 的探测只覆盖了每个端点最基础的一种调用组合，"约束条件"章节已详细列出两个工具各自尚未探测的参数边界（`serial_title_search` 的 `issn`/`pub`/`subj`/`content`/`date`/`oa`/`start`/`count`/`view` 等参数、零条件行为；`subject_classifications` 的 `source=scidir` 分支字段结构、`code`/`abbrev`/`field` 过滤参数），project-builder-cn 需先补测这些边界，再确定参数校验与归一化字段——延续本项目一贯的"真实验证优先"原则，与此前 `get_abstract_details`/`retrieve_article` 归一化任务的处理方式一致。
  4. 目标发布版本号为 **`2.3.0`**，构建计划书应涵盖 `pyproject.toml` 版本号更新（当前为 `2.2.0`）与 `project-docs/buildlog.md` 变更记录，工具总数由 10 个增至 12 个，README.md / README_ZH.md 的工具清单/计数需同步更新，再交由 `project-builder-cn` 落地执行。
- （v3.0.0，QA-R010/QA-R011，2026-08-04）本轮目标澄清（源自用户调研本地参考项目 `reference-projects/paper-search-mcp-main/`、`reference-projects/research-superpower-main/`，QA-R010 发现候选 + QA-R011 收敛范围边界）已闭环，QA-R010 六个问题、QA-R011 三个问题均已获用户明确回答，文档中不再有"待定/待 QA-R011 确认"的占位状态，目标版本号明确对齐为 **`3.0.0`**（用户主动跳过原规划中尚未启动的 v2.4.0，原 QA-R009 已作废并被 revert）。**下一步建议调用 `project-planner-cn` 基于本文档最终版制定 v3.0.0 构建计划书**，交接要点：
  1. **范围规模空前，务必如实体现，不得淡化**：本轮合计新增 **13 个数据源/功能点**——11 个通用检索型新数据源（Semantic Scholar、OpenAlex、Crossref、PMC、Europe PMC、DOAJ、CORE、Zenodo、HAL、dblp、OpenAIRE）+ 2 个语义特殊的新数据源（bioRxiv/medRxiv 的"按分类浏览"语义、ChEMBL 的"DOI 查询"语义）+ 1 个现有工具增强（arXiv 三个现有工具补充 `doi` 字段）。这是本项目至今规模最大的一轮版本，**强烈建议 project-planner-cn 不要沿用此前几轮"一次性列完所有步骤"的构建计划书组织方式，而应考虑分阶段/分批组织**（例如：第一阶段先完成 11 个新数据源的真实 API 探测并汇总结果、第二阶段再据探测结果分批实现），具体怎么拆分由 project-planner-cn 自行判断。
  2. **正式实现前必须先做真实 API 可行性验证，这是一个规模庞大的前置任务，不能跳过**：用户在 QA-R011 明确要求"对每一个源都进行真实性探测"，11 个通用检索候选（不区分此前"推荐重点"与"中等价值"分档）均需真实验证端点可用性、限流表现、真实字段结构，不得照抄参考项目 `paper-search-mcp-main` 的 Python 实现直接假设可用。
  3. **探测结果如何影响最终范围，已有明确的默认处理原则（见"约束条件"最新一条）**：技术上确认不可行的候选，比照 QA-R002 先例直接排除、无需二次确认用户；技术上可行但价值存疑的候选，需整理成探测结果汇总交还用户做最终去留判断，不得由 project-planner-cn/project-builder-cn 自行拍板剔除。
  4. **ChEMBL 的参数签名有特殊要求**：必须是 `doi` 必填的查询工具语义，不能比照其余数据源的 `query`+`max_results` 关键词检索模式设计（详见"约束条件"）。
  5. **arXiv 补 `doi` 字段是独立、低风险、可优先完成的步骤**，不依赖 11 个新数据源的探测/实现进度，可以作为构建计划书里最先交付的一小步。
  6. 目标发布版本号为 **`3.0.0`**（当前 `pyproject.toml` 为 `2.3.0`），构建计划书应涵盖 `pyproject.toml` 版本号更新与 `project-docs/buildlog.md` 变更记录；由于规模庞大，工具总数的最终变化量需等真实探测结果出来后才能确定，不建议在计划书开头就假定"13 个"全部会变成对应数量的新工具（部分候选探测后可能被排除）。
- （v3.0.0，QA-R012，2026-08-05）project-builder-cn 步骤 28-33 完成 13 个候选的真实探测（9 个直接落地，见 buildlog.md commit `008d509`），其余 4 个"技术可行但价值存疑"候选（Semantic Scholar、PMC、CORE、dblp）按 QA-R011 已确认的止损规则交还用户裁决，本轮全部逐项定案：**Semantic Scholar 纳入**（key 申请中；新增"无 key 不注册工具"的条件注册架构需求，需 project-planner-cn 在后续步骤中设计）、**PMC 排除**（技术核实其与现有 pubmed 工具同为 NCBI Entrez API 封装，无稳定性优势，用户自设的纳入条件未成立）、**CORE 纳入**（key 已配置在 `.env` 的 `CORE_API_KEY`，限流顾虑解除）、**dblp 暂缓**（探测环境 SSL 握手失败，待用户提供新网络环境探测结果后另开 QA-R013 定案，本轮不代为判定）。**v3.0.0 范围现状**：13 个立项候选中确认落地 11 个、明确排除 1 个（PMC）、悬而未决 1 个（dblp）。**下一步交接**：project-planner-cn 在设计步骤 34+（Semantic Scholar/CORE 的具体实现）时需一并纳入"按 key 条件注册"这一新架构分支的设计与权衡（见约束条件）；dblp 在 QA-R013 定案前不得被视为已纳入或已排除，不得代为假设结论。
