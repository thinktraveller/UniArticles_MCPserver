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

## 约束条件
- 当前 `SCOPUS_API_KEY` 为**基础级别、非商业性质**的 Elsevier 开发者 Key，未配置 `X-ELS-Insttoken`（机构令牌）。
- 该订阅等级下，Scopus Search 的 `COMPLETE` 视图也会返回 401（实测确认），意味着账号整体权限受限，不止是本次新增的两项功能。
- 遗留风险（非本次 v2.0 范围改动，但需在后续构建计划书中知悉）：现有 `get_abstract_details` 默认 `view=META_ABS`、`retrieve_article` 默认 `view=META_ABS`，这两个默认 view 在 Elsevier 文档中被标记为需要机构订阅/entitlement 的受限视图，当前账号权限下调用可能拿不到完整内容。是否在 v2.0 中一并调整默认 view 或增加权限不足时的降级提示，留待构建计划阶段评估。
- 若未来用户订阅等级提升（获得机构订阅/商业 Key/Insttoken），本文档"排除"清单中的功能可重新评估纳入，无需重新走一遍可行性摸底——已有的实测方法（临时脚本探测真实端点）可复用。
- **（v2.1.0，QA-R003）`downloadPaper` 的删除是产品定位性约束，非临时性技术债**：即便未来 `arxiv` 库的 `AttributeError` 被修复，也不应仅因为"代码能跑了"就自动恢复该工具；如果要重新引入下载能力，需要作为一次新的、独立的目标澄清（说明为什么下载功能重新符合产品定位），而不是顺带恢复。
- **（v2.1.0，QA-R003）`searchScholarPapers` 的删除原因是用户确认的网络访问受限**（不是 Elsevier API Key 权限问题），与其余 5 个工具的删除原因（`downloadPaper` 除外）不同，特此分开记录，避免后续误将其归因为"权限不足"。
- **（v2.1.0，QA-R003）本轮目标（工具删除 + README 修正）对应的发布版本号为 `2.1.0`**（当前 `pyproject.toml` 为 `2.0.1`），采用新增功能/范围调整级别的版本号而非 patch 号，因为该变更包含移除已发布公开工具接口这一对使用者可见的破坏性变更。
- **（v2.1.0，QA-R003）执行分工**：本 agent（project-creator-cn）仅负责将上述决策写入本文档；实际的代码删除（`arxiv.py`/`scopus.py`/`sciencedirect.py`/`paperscraper.py` 及对应测试）与 README.md/README_ZH.md 文案修改，需要移交给 `project-planner-cn` 制定构建计划书，再由 `project-builder-cn` 落地执行并更新 `project-docs/buildlog.md`。

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

<!-- GOAL-QA-LOG-END -->

## 备注
- （v2.1.0，QA-R003，2026-08-03）目标澄清已完成，用户确认无需继续追问。下一步建议调用 `project-planner-cn` 基于本文档制定构建计划书，覆盖两块工作：① 删除 6 个工具（`downloadPaper`/`searchAuthors`/`getAuthorProfile`/`searchSciencedirect`/`getArticleMetadata`/`searchScholarPapers`）的代码、注册与测试引用；② 同步修改 README.md / README_ZH.md 的 Elsevier Key 说明与工具清单。目标发布版本号为 `2.1.0`，构建计划书应涵盖 `pyproject.toml` 版本号更新与 `project-docs/buildlog.md` 变更记录，再交由 `project-builder-cn` 落地执行。
