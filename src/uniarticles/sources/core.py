import re
from datetime import datetime, timezone

import httpx
from mcp.server.fastmcp import FastMCP

from ..config import settings


# v3.5.0: 由"检索端点整条 URL"改为"API 基址"，各端点按 f"{BASE_URL}/…" 拼装，
# 避免每个工具各自硬编码长字符串（原常量值 https://api.core.ac.uk/v3/search/works）。
BASE_URL = "https://api.core.ac.uk/v3"
USER_AGENT = "UniArticlesMCP/3.5.0 (https://github.com/thinktraveller/UniArticles_MCPserver)"

# 单次请求超时。CORE 在命中大响应体时并不快：limit=100 的 works 检索实测 435.5 KB、
# 耗时 28.75～44.82 s（见 buildlog 步骤 69 的 F4 与复核），固定 30 s 会在本机网络下
# 间歇性超时。60 s 兼顾"慢网络下能拿到大结果"与"上游卡死时仍能快速失败"。
REQUEST_TIMEOUT = 60.0


def _ok(query: str, items: list[dict]) -> dict:
    """标准成功响应：items 恒为列表（跨全部数据源统一形状）。"""
    return {"ok": True, "source": "core", "query": query, "count": len(items), "items": items, "error": None}


def _ok_one(query: str, item: dict) -> dict:
    """单条记录类工具（详情 / stats）专用：语义由调用方写入工具 docstring。"""
    return _ok(query=query, items=[item])


def _err(query: str, message: str) -> dict:
    return {"ok": False, "source": "core", "query": query, "count": 0, "items": [], "error": message}


def _headers() -> dict[str, str]:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if settings.core_api_key:
        headers["Authorization"] = f"Bearer {settings.core_api_key}"
    return headers


# ------------------------------------------------------------------ 标识符规则

_CORE_ID_RE = re.compile(r"^\d+$")


def _is_core_id(identifier: str) -> bool:
    return bool(_CORE_ID_RE.match(identifier.strip()))


def _require_core_id(identifier: str, *, tool: str) -> str | None:
    """返回规范化后的数字 CORE ID；若调用方传了 DOI 等非数字标识符则返回 None。

    CORE 的 works 子资源（/outputs）只接受数字 CORE ID——实测传裸 DOI 会 404
    （见 buildlog 步骤 69 的 F8 / F11），因此调用方需要在工具层给出明确提示，
    而不是把上游 404 原样抛给 LLM。
    """
    candidate = identifier.strip()
    return candidate if _is_core_id(candidate) else None


def _as_list(payload) -> list:
    """把多种"列表载体"形态统一取出列表，取不到就返回空列表。

    CORE 的各端点并不统一：/works/{id}/outputs 返回**裸列表**，
    而 /data-providers/{id}/outputs 与各 search 端点返回 {"results": [...]} 分页对象
    （见 buildlog 步骤 69 的 F8 与 F15）。两种形态都必须支持。
    """
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        results = payload.get("results")
        if isinstance(results, list):
            return results
    return []


# ------------------------------------------------------------------ HTTP 层


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
    hint = ""
    if not settings.core_api_key:
        hint = " 配置 CORE_API_KEY 可获得更高额度（未认证档：100 tokens/天、10 次/分钟，且不提供 fullText）。"
    return (
        f"CORE 触发限流（HTTP 429）。可重试时间：{when}；"
        f"额度：limit={limit or '未知'} / remaining={remaining or '未知'}。{hint}"
    ).strip()


def _error_for(response: httpx.Response, *, query: str) -> dict:
    """把非 200 响应转成统一 _err 结构。三类真实失败分别给可操作文案。"""
    if response.status_code == 429:
        return _err(query=query, message=_rate_limit_message(response))
    if response.status_code == 404:
        return _err(
            query=query,
            message=(
                "CORE 未找到该记录（HTTP 404）。请确认标识符存在且端点接受该标识符类型；"
                f"{query!r} 对应的记录可能未收录。"
            ),
        )
    try:
        detail = response.json()
    except ValueError:
        detail = (response.text or "").strip()[:200]
    message = detail.get("message") if isinstance(detail, dict) else detail
    extra = ""
    if response.status_code >= 500:
        # /v3/search/outputs 历史上对部分查询表达式返回过 500（上游 Azure Search
        # 表达式错误），见 buildlog 步骤 69 与 goal.md QA-R021。
        extra = '该端点对部分查询表达式不稳定，可改用 title:"..." / doi:"..." 限定写法。'
    return _err(
        query=query,
        message=f"CORE 请求失败（HTTP {response.status_code}）：{message or '上游未返回错误说明'}。{extra}".strip(),
    )


async def _request(
    method: str,
    path: str,
    *,
    query: str,
    params: dict | None = None,
    json_body: dict | None = None,
) -> dict:
    """所有 CORE 工具的唯一出口：成功返回 {"ok": True, "payload": <原始 JSON>}，失败返回 _err 结构。

    把 follow_redirects（CORE 偶发 301）、超时、headers、错误转换集中处理；
    调用方只需判定 result["ok"] 后取 result["payload"]。
    """
    url = f"{BASE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, headers=_headers(), follow_redirects=True) as client:
            response = await client.request(method, url, params=params, json=json_body)
        if response.status_code != 200:
            return _error_for(response, query=query)
        return {"ok": True, "payload": response.json()}
    except Exception as exc:  # noqa: BLE001 - 工具层必须把任何异常转成 _err，不能让它冒泡
        return _err(query=query, message=f"CORE 请求异常：{type(exc).__name__}: {exc}")


# ------------------------------------------------------------------ 归一化层


def _author_names(authors) -> list[str]:
    """作者列表的元素形态在不同端点间不一致（dict / str 都出现过），两种都要兼容。"""
    names = []
    for author in authors or []:
        if isinstance(author, dict):
            name = author.get("name")
            if name:
                names.append(name)
        elif isinstance(author, str) and author:
            names.append(author)
    return names


def _normalize_work(work: dict) -> dict:
    """作品（works）维度的题录归一化。

    字段名取自 buildlog 步骤 69 的 F1/F7 实测结构。既有 8 个字段
    （title / authors / abstract / doi / cited_by_count / download_url /
    arxiv_id / pubmed_id）是既有调用方的可见契约，不得删除；其余为本次按实测
    结构增补（core_id / document_type / field_of_study / journals / data_providers …）。

    **硬边界**：绝不把 `fullText` 写入返回值——即便上游内联返回了正文也必须丢弃。
    """
    data_providers = []
    for provider in work.get("dataProviders") or []:
        if isinstance(provider, dict):
            data_providers.append(
                {"id": provider.get("id"), "name": provider.get("name"), "url": provider.get("url")}
            )
    journals = []
    for journal in work.get("journals") or []:
        if isinstance(journal, dict):
            journals.append({"title": journal.get("title"), "issn": journal.get("issn")})
        elif isinstance(journal, str) and journal:
            journals.append({"title": journal, "issn": None})
    return {
        "core_id": work.get("id"),
        "title": work.get("title"),
        "authors": _author_names(work.get("authors")),
        "abstract": work.get("abstract"),
        "doi": work.get("doi"),
        "cited_by_count": work.get("citationCount"),
        # Expose the download link only; do NOT dump the full text (`fullText`) into
        # items — consistent with the project's "metadata/links only" stance.
        "download_url": work.get("downloadUrl"),
        "arxiv_id": work.get("arxivId"),
        "pubmed_id": work.get("pubmedId"),
        "document_type": work.get("documentType"),
        "field_of_study": work.get("fieldOfStudy"),
        "language": work.get("language"),
        "publisher": work.get("publisher"),
        "published_date": work.get("publishedDate"),
        "deposited_date": work.get("depositedDate"),
        "year_published": work.get("yearPublished"),
        "journals": journals,
        "data_providers": data_providers,
        "outputs": [url for url in work.get("outputs") or [] if isinstance(url, str)],
        "identifiers": work.get("identifiers") if isinstance(work.get("identifiers"), dict) else {},
    }


def _normalize_output(output: dict) -> dict:
    """原始采集记录（outputs）维度的归一化，字段名取自步骤 69 的 F8/F15/F16/F17 实测结构。"""
    data_provider = output.get("dataProvider")
    provider = None
    if isinstance(data_provider, dict):
        provider = {
            "id": data_provider.get("id"),
            "name": data_provider.get("name"),
            "url": data_provider.get("url"),
        }
    identifiers = output.get("identifiers") if isinstance(output.get("identifiers"), dict) else {}
    return {
        "output_id": output.get("id"),
        "title": output.get("title"),
        "authors": _author_names(output.get("authors")),
        "abstract": output.get("abstract"),
        "doi": output.get("doi") or identifiers.get("doi"),
        "download_url": output.get("downloadUrl"),
        "document_type": output.get("documentType"),
        "language": output.get("language"),
        "publisher": output.get("publisher"),
        "published_date": output.get("publishedDate"),
        "deposited_date": output.get("depositedDate"),
        "license": output.get("license"),
        "fulltext_status": output.get("fulltextStatus"),
        "repositories": output.get("repositories") if isinstance(output.get("repositories"), list) else [],
        "sdg": output.get("sdg") if isinstance(output.get("sdg"), list) else [],
        "source_fulltext_urls": [url for url in output.get("sourceFulltextUrls") or [] if isinstance(url, str)],
        "data_provider": provider,
        "identifiers": identifiers,
    }


def _normalize_data_provider(provider: dict) -> dict:
    """机构库（data providers）维度的归一化，字段名取自步骤 69 的 F12/F13 实测结构。"""
    location = provider.get("location") if isinstance(provider.get("location"), dict) else {}
    return {
        "id": provider.get("id"),
        "name": provider.get("name"),
        "type": provider.get("type"),
        "url": provider.get("homepageUrl") or provider.get("uri"),
        "homepage_url": provider.get("homepageUrl"),
        "oai_pmh_url": provider.get("oaiPmhUrl"),
        "software": provider.get("software"),
        "source": provider.get("source"),
        "metadata_format": provider.get("metadataFormat"),
        "open_doar_id": provider.get("openDoarId"),
        "ror_id": provider.get("rorId"),
        "institution_name": provider.get("institutionName"),
        "country_code": location.get("countryCode") or None,
        "aliases": [alias for alias in provider.get("aliases") or [] if isinstance(alias, str)],
    }


def _normalize_data_provider_stats(stats: dict) -> dict:
    """机构库统计（/data-providers/{id}/stats）字段名取自步骤 69 的 F14 实测结构。"""
    last_seen = stats.get("lastSeen") if isinstance(stats.get("lastSeen"), dict) else {}
    return {
        "id": stats.get("id"),
        "count_metadata": stats.get("countMetadata"),
        "count_fulltext": stats.get("countFulltext"),
        "is_active": last_seen.get("isActive"),
        "set": stats.get("set"),
    }


def _normalize_work_stats(stats: dict) -> dict:
    """作品生命周期时间戳（/works/{id}/stats）——实测响应体只有 5 个键（步骤 69 的 F9/F9b）。"""
    return {
        "core_id": stats.get("id"),
        "deposited_date": stats.get("depositedDate"),
        "published_date": stats.get("publishedDate"),
        "updated_date": stats.get("updatedDate"),
        "accepted_date": stats.get("acceptedDate"),
    }


# ------------------------------------------------------------------ 工具层


async def _search(query: str, max_results: int, offset: int = 0) -> dict:
    # v3.5.0: switch GET → POST so `exclude:["fullText"]` can be used. CORE inlines the
    # full text of every hit by default and `_normalize_work()` discards it, so the old
    # GET path was paying for 6x the payload for nothing (measured: 676,692 B vs
    # 112,549 B for the same 25 hits). `offset`/`limit=100` were both verified against
    # the real API in buildlog step 69 (F2/F3/F4).
    body = {"q": query, "limit": max_results, "offset": offset, "exclude": ["fullText"]}
    # CORE occasionally 301-redirects the request; _request() follows redirects so a
    # valid call is not surfaced as a bare 3xx error.
    result = await _request("POST", "/search/works", query=query, json_body=body)
    if not result["ok"]:
        return result
    payload = result["payload"]
    items = [_normalize_work(w) for w in _as_list(payload) if isinstance(w, dict)]
    return _ok(query=query, items=items)


async def _aggregate(query: str, fields: list[str], top_n: int) -> dict:
    """Distribution (facet) query. Request body verified in buildlog step 69 (F5/F6):

    `{"q": <keyword>, "aggregations": [<dimension>, ...]}` — `aggregations` is
    OPTIONAL (F5 returned 200 with only `q`), and the dimension names are camelCase
    when supplied explicitly (`yearPublished` / `authors` / `publisher`). Note that
    CORE's *default* dimension set comes back in snake_case instead
    (`year_published` / `field_of_study`), so dimension names are passed through
    verbatim and never renamed.

    Each dimension returns a `{bucket_value: count}` mapping that upstream truncates
    to 100 buckets, and the dimension order is not guaranteed to match the request.
    """
    body: dict = {"q": query}
    if fields:
        body["aggregations"] = fields
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
        # Bucket values are strings (years, publisher names) and the counts are ints,
        # but treat a non-numeric count defensively so one odd bucket cannot break the
        # whole response.
        ranked = sorted(
            buckets.items(),
            key=lambda kv: kv[1] if isinstance(kv[1], (int, float)) else 0,
            reverse=True,
        )
        items.append(
            {
                "field": field,
                "total_buckets": len(buckets),
                "top": [
                    {"value": str(value), "count": count if isinstance(count, (int, float)) else 0}
                    for value, count in ranked[:top_n]
                ],
            }
        )
    return _ok(query=query, items=items)


def register(server: FastMCP) -> None:
    # CORE registers unconditionally: it works without a key, just with a strict rate
    # limit, mirroring the existing Elsevier "register always, surface limits at
    # runtime" model.
    @server.tool()
    async def core_work_search_by_query(query: str, max_results: int = 10, offset: int = 0) -> dict:
        """Search CORE (global open-access aggregator) by keyword, with paging.

        `query` accepts CORE's own query syntax (field qualifiers such as
        `title:"..."` / `doi:"..."`, boolean operators, phrase matching).
        `max_results` is capped at 100 (CORE's per-request ceiling) and `offset`
        pages through the result set; note that a large `max_results` returns a big
        payload (roughly 435 KB for 100 hits) and can take up to ~45 s on slow
        networks, so keep the default 10 unless you need more.

        Returns metadata and download links only — the upstream `fullText` field is
        excluded at the request level and never surfaces. Works without an API key,
        but the anonymous tier is token-metered (100 tokens/day, 10 requests per
        minute, no fullText); configuring CORE_API_KEY raises it to 1,000 tokens/day
        at 25 requests per minute.
        """
        normalized_query = query.strip()
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        bounded = max(1, min(max_results, 100))
        bounded_offset = max(0, offset)
        return await _search(query=normalized_query, max_results=bounded, offset=bounded_offset)

    @server.tool()
    async def core_work_detail_by_identifier(identifier: str) -> dict:
        """Fetch the full CORE record of one work by bare DOI or numeric CORE ID.

        Use the bare DOI form (e.g. `10.1038/nature12373`) — the `doi:` prefix is
        not a valid path segment upstream and returns 404. Both identifier forms
        were verified against the real API in buildlog step 69 (F7).

        The detail record carries `dataProviders` / `outputs` / `identifiers` that
        keyword search results do not include. `outputs` here are URLs only; call
        `core_work_outputs_by_id` to expand them. Returns a single item.
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

    @server.tool()
    async def core_work_outputs_by_id(identifier: str) -> dict:
        """List the per-repository copies (`outputs`) CORE harvested for one work.

        `identifier` MUST be a numeric CORE ID (e.g. `171513974`); this sub-resource
        rejects DOIs with a 404 (verified in buildlog step 69's F8/F11). If you only
        have a DOI, call `core_work_detail_by_identifier` first and take the numeric
        id from its `core_id` / `identifiers` fields.

        Each item is a de-duplication *source record*, not the paper text: it carries
        `download_url` / `license` / `fulltext_status` / `data_provider`, which is how
        you tell how many repository copies exist and under what licence.
        """
        candidate = identifier.strip()
        if not candidate:
            return _err(query=identifier, message="identifier must not be empty")
        core_id = _require_core_id(candidate, tool="core_work_outputs_by_id")
        if core_id is None:
            return _err(
                query=candidate,
                message=(
                    f"该端点只接受数字 CORE ID，收到 {candidate!r}。"
                    "请先用 core_work_detail_by_identifier 按 DOI 取详情，"
                    "再从返回的 core_id / identifiers 字段取得数字 ID 后重试。"
                ),
            )
        result = await _request("GET", f"/works/{core_id}/outputs", query=core_id)
        if not result["ok"]:
            return result
        items = [_normalize_output(o) for o in _as_list(result["payload"]) if isinstance(o, dict)]
        return _ok(query=core_id, items=items)

    @server.tool()
    async def core_work_stats_by_id(identifier: str) -> dict:
        """Fetch the lifecycle timestamps of one CORE work (deposited / published /
        updated / accepted).

        `identifier` accepts either a bare DOI or a numeric CORE ID — unlike
        `core_work_outputs_by_id`, this endpoint does not require a numeric id
        (both verified in buildlog step 69's F9/F9b). Returns a single item with
        only those timestamp fields, because that is all the upstream returns.
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

    @server.tool()
    async def core_work_aggregate_by_query(
        query: str,
        fields: list[str] | None = None,
        top_n: int = 10,
    ) -> dict:
        """Summarise the distribution of CORE works matching a keyword query.

        This is a facet/distribution view, NOT a result list: each item is one
        dimension (`field` / `total_buckets` / `top[{value, count}]`), with `top`
        sorted by count descending and truncated to `top_n` (default 10, capped at
        50). `count` in the response is therefore the number of *dimensions*
        returned, not the number of papers.

        `query` uses the same syntax as `core_work_search_by_query`. `fields` is
        optional: leave it unset to let CORE pick its default dimensions, or pass
        explicit camelCase dimension names (e.g. `["yearPublished", "authors",
        "publisher"]`). Dimension names are passed through verbatim — CORE's
        default set is snake_case (`year_published`, `field_of_study`) while an
        explicit request is camelCase, and both are returned as-is. Each dimension
        is capped by upstream at 100 buckets, so `total_buckets` is also capped at
        100 and does not reveal the untruncated cardinality.

        Aggregation queries cost more tokens than a plain search upstream; call it
        when you actually need a distribution, not after every search.
        """
        normalized_query = query.strip()
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        bounded_top = max(1, min(top_n, 50))
        normalized_fields = [f.strip() for f in (fields or []) if isinstance(f, str) and f.strip()]
        return await _aggregate(query=normalized_query, fields=normalized_fields, top_n=bounded_top)

    @server.tool()
    async def core_data_provider_search_by_query(query: str, max_results: int = 10) -> dict:
        """Search CORE's data providers — institutional repositories and journal sources.

        Each item is a repository/journal source (`id` / `name` / `type` / `url` /
        `software` / `country_code` …), not a paper. Take an `id` from here into
        `core_data_provider_detail_by_id`, or reach a provider id from a work by
        reading `data_providers` in `core_work_detail_by_identifier` / search results.

        `max_results` is capped at 200 (verified against the real API in buildlog
        step 69's F12 plus this step's limit probe: 50/100/200 all accepted).
        """
        normalized_query = query.strip()
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        bounded = max(1, min(max_results, 200))
        result = await _request(
            "GET", "/search/data-providers", query=normalized_query,
            params={"q": normalized_query, "limit": bounded},
        )
        if not result["ok"]:
            return result
        items = [_normalize_data_provider(p) for p in _as_list(result["payload"]) if isinstance(p, dict)]
        return _ok(query=normalized_query, items=items)

    @server.tool()
    async def core_data_provider_detail_by_id(
        provider_id: str,
        include_stats: bool = False,
        include_outputs: bool = False,
    ) -> dict:
        """Fetch one CORE data provider (repository / journal source) by numeric id.

        `include_stats` and `include_outputs` each add one extra upstream request, so
        they are off by default; turn them on only when you need the figures. Get the
        numeric id from `core_data_provider_search_by_query` or from the
        `data_providers` field of a work record.

        The two sub-resources are best-effort: if the main detail call succeeds but a
        sub-resource fails, the response stays `ok=True` and the failure is reported
        under that sub-key (`stats` / `outputs` holding an `{ok, error}` object)
        instead of discarding the detail you already have.
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
            if stats["ok"] and isinstance(stats["payload"], dict):
                item["stats"] = _normalize_data_provider_stats(stats["payload"])
            else:
                item["stats"] = {"ok": False, "error": stats.get("error", "机构库统计信息不可用。")}

        if include_outputs:
            outputs = await _request(
                "GET", f"/data-providers/{candidate}/outputs", query=candidate, params={"limit": 25}
            )
            if outputs["ok"]:
                item["outputs"] = [
                    _normalize_output(o) for o in _as_list(outputs["payload"]) if isinstance(o, dict)
                ]
            else:
                item["outputs"] = {"ok": False, "error": outputs.get("error", "机构库 outputs 不可用。")}

        return _ok_one(query=candidate, item=item)

    @server.tool()
    async def core_output_detail_by_id(output_id: str) -> dict:
        """Fetch one raw CORE harvesting record (`output`) by numeric id.

        An `output` is a de-duplicated *source signal*: the same paper shows up once
        per repository that harvested it, whereas a `work` is CORE's merged record
        for that paper. Call this when you need per-repository detail — `license`,
        `repositories`, `sdg`, `fulltext_status`, `source_fulltext_urls` — and use
        the works tools (`core_work_detail_by_identifier`) for the paper itself.

        `output_id` must be numeric. Returns a single item.
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
