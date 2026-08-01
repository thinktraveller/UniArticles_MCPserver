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

## 范围界定
### 包含
- **Serial Title（期刊信息查询）**：接入 `content/serial/title/issn/{issn}`，实测 HTTP 200 可用，加入 `scopus.py`（或新建期刊相关模块，具体归属由后续构建计划书决定）。
- **Object Retrieval（图表/补充材料获取）**：接入 `content/object/{identifier_type}/{id}`，实测 HTTP 200 可用，加入 `sciencedirect.py`（或新建模块）。
- 以上两项对应的新 MCP 工具注册、参数校验、错误处理，遵循现有 `scopus.py`/`sciencedirect.py` 的代码风格（`_ok`/`_err`/`_get_headers` 等既有模式）。

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

<!-- GOAL-QA-LOG-END -->

## 备注
[其他重要信息]
