"""
CORE API v3 字段/端点能力探测脚本（编码前置）
==============================================

用途：在**你自己的真实网络环境**里，把 UniArticles v3.5.0（CORE 扩展）要新增
      的工具所依赖的端点与响应字段全部跑一遍，拿到真实结构后再写归一化代码。
      计划书明确要求：**不得**依据官方文档字面描述或历史备注凭空定义字段名。

与 `core_api_probe.py` 的分工（两份脚本缺一不可，不要互相替代）：

  * `core_api_probe.py`  —— 回答"此前的失败是不是本机环境噪声"（复测 QA-R021
                            记录过的 5 类失败端点 + 基线对照）。
  * 本脚本               —— 回答"新端点 / 新字段到底长什么样"（F1～F17），
                            供 project-builder-cn 的步骤 70～75 直接引用。

本脚本覆盖三类此前**从未被真实请求验证过**的东西：

  1. `POST /v3/search/works` 的请求体 schema（`exclude` / `offset` / `limit=100`）；
  2. `POST /v3/search/works/aggregate` 的请求体 schema —— 本轮最大的未验证点；
  3. 详情类端点的真实字段名（works 详情 / works outputs / works stats /
     data-providers 详情·统计·其下 outputs / outputs 详情），以及
     `GET /v3/search/data-providers` 的响应结构。

另外 F17 是 `core_output_search_by_query`（C 档第 9 项）的**击杀条件判据**：
三种查询组合必须全部 200 才纳入本版本。

怎么用：在项目根目录打开 PowerShell / CMD，执行：

          python _verify/core_api_field_probe.py

      网络较慢时放宽超时，或只跑其中几项：

          python _verify/core_api_field_probe.py --timeout 90
          python _verify/core_api_field_probe.py --only F5,F6,F8,F16,F17

      然后把整段输出（尤其是最后的"诊断结论"）复制反馈即可。

这个脚本只做只读的网络探测：不改任何文件、不下载任何二进制、不落地任何内容
（所有响应体只在内存里截断后打印，绝不写盘）。输出里的 IPv4 地址与 API Key
会自动打码，可以安全粘贴。API Key 优先从环境变量 CORE_API_KEY 读取，读不到再
回退到仓库根目录的 .env；两者都没有时脚本会以匿名方式继续跑完（匿名档位更低：
100 tokens/天、10 次/分钟，且官方不提供 fullText）。
"""

import argparse
import builtins
import json
import os
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Windows 控制台默认可能是 GBK 编码，会把中文显示成乱码。
# 这里强制把输出改成 UTF-8，保证提示文字在 PowerShell / CMD 里能正常显示。
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# IPv4 脱敏正则：匹配点分十进制的 4 段数字。用户会把整段输出复制给对话助手
# 做诊断，不应把本机解析出的真实 IP 明文外泄。统一把后两段打码
# （如 104.18.32.7 -> 104.18.xxx.xxx），保留前两段够用来判断是不是同一网段。
_IPV4_RE = re.compile(r"\b(\d{1,3})\.(\d{1,3})\.\d{1,3}\.\d{1,3}\b")

# 运行期从 .env / 环境变量拿到的 API Key，用于输出脱敏（万一它出现在错误信息里）。
_API_KEY_VALUE = None


def _mask(text):
    """对单个字符串做脱敏：先打码 IPv4，再打码 API Key 明文。"""
    text = _IPV4_RE.sub(r"\1.\2.xxx.xxx", text)
    if _API_KEY_VALUE:
        text = text.replace(_API_KEY_VALUE, "***API_KEY***")
    return text


def _print(*args, **kwargs):
    """print 的包装函数：打印前对所有字符串参数脱敏。

    脚本内所有输出一律走这里，这样以后新增打印语句也会自动脱敏，不用逐行手动
    改字符串，避免遗漏。
    """
    masked = [_mask(a) if isinstance(a, str) else a for a in args]
    builtins.print(*masked, **kwargs)


HOST = "api.core.ac.uk"
PORT = 443
BASE = "https://api.core.ac.uk"
USER_AGENT = "UniArticlesMCP-CoreFieldProbe/1.0 (+https://github.com/thinktraveller/UniArticles_MCPserver)"

# 单次响应最多读取 512 KB：CORE 的 works/outputs 记录默认内联 fullText，
# 不限制的话一个 limit=100 的查询就能拉回 1 MB 以上（实测 1,145,330 字节）。
# 本脚本只判断"能不能拿到数据、字段叫什么"，不需要把正文全部读进内存。
MAX_BODY = 512 * 1024

# 每个请求最多打印多长的响应体片段。诊断目的下 1200 字符足够看清键名层级。
# 注意：json.dumps 时用 indent 展开，方便肉眼核对嵌套字段，但会更快触到这个上限。
MAX_SNIPPET = 1200

# CORE 官方称每个响应都带这三个限流头，实测确认存在，且对区分
# "被限流" 与 "端点故障" 很关键。
RATE_HEADERS = ("x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-retry-after")


def _load_api_key():
    """按 环境变量 CORE_API_KEY -> 仓库根目录 .env 的顺序取 key，取不到返回 None。"""
    global _API_KEY_VALUE

    value = os.environ.get("CORE_API_KEY", "").strip()
    origin = "环境变量 CORE_API_KEY"

    if not value:
        # 脚本位于 <仓库根>/_verify/ 下，向上一级就是仓库根目录。
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r", encoding="utf-8", errors="replace") as fh:
                    for raw in fh:
                        line = raw.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        name, _, val = line.partition("=")
                        if name.strip() == "CORE_API_KEY":
                            val = val.strip().strip('"').strip("'")
                            if val:
                                value = val
                                origin = "仓库根目录的 .env 文件"
                            break
            except OSError as exc:
                _print(f"[提示] 读取 .env 失败（不影响继续运行）：{exc}")

    _API_KEY_VALUE = value or None
    return value or None, origin


def _http(url, method="GET", payload=None, key=None, timeout=60.0):
    """发一次请求并归一化结果，任何异常都转成结构化的 error 字段，不向外抛。"""
    data = None
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if key:
        headers["Authorization"] = f"Bearer {key}"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    result = {
        "status": None,
        "elapsed": None,
        "bytes": None,
        "ctype": "",
        "rate": {},
        "body": "",
        "truncated": False,
        "error": None,
    }
    started = time.time()

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result["status"] = response.status
            result["ctype"] = response.headers.get("Content-Type", "") or ""
            result["rate"] = {h: response.headers.get(h) for h in RATE_HEADERS if response.headers.get(h) is not None}
            declared = response.headers.get("Content-Length")
            chunk = response.read(MAX_BODY)
            result["elapsed"] = time.time() - started
            if declared and declared.isdigit():
                result["bytes"] = int(declared)
                result["truncated"] = int(declared) > len(chunk)
            else:
                result["bytes"] = len(chunk)
            result["body"] = chunk.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        # 4xx/5xx 会以异常形式抛出，但响应体里往往写着上游的真实错误，必须读出来。
        result["status"] = exc.code
        result["ctype"] = (exc.headers.get("Content-Type", "") if exc.headers else "") or ""
        if exc.headers:
            result["rate"] = {h: exc.headers.get(h) for h in RATE_HEADERS if exc.headers.get(h) is not None}
        chunk = exc.read(MAX_BODY)
        result["elapsed"] = time.time() - started
        result["bytes"] = len(chunk)
        result["body"] = chunk.decode("utf-8", errors="replace")
    except (socket.timeout, TimeoutError) as exc:
        result["elapsed"] = time.time() - started
        result["error"] = f"超时（{timeout:g} 秒内未返回）：{type(exc).__name__}"
    except urllib.error.URLError as exc:
        result["elapsed"] = time.time() - started
        reason = exc.reason
        if isinstance(reason, (socket.timeout, TimeoutError)):
            result["error"] = f"超时（{timeout:g} 秒内未返回）"
        else:
            result["error"] = f"连接失败：{reason}"
    except Exception as exc:  # noqa: BLE001 - 诊断脚本要保证任何异常都能跑完全程
        result["elapsed"] = time.time() - started
        result["error"] = f"{type(exc).__name__}: {exc}"

    return result


def _verdict(res):
    """把一次请求结果翻译成一句人话判定。"""
    if res["error"]:
        return "超时" if "超时" in res["error"] else "网络层失败"
    status = res["status"]
    if status == 200:
        return "200 但空响应体" if res["bytes"] == 0 else "可用"
    if status in (401, 403):
        return f"{status} 鉴权/权限"
    if status == 404:
        return "404 未找到"
    if status == 429:
        return "429 被限流"
    if status == 400:
        return "400 请求体/参数被拒"
    if status == 422:
        return "422 参数校验失败"
    if status and 400 <= status < 500:
        return f"{status} 请求被拒"
    if status and status >= 500:
        return f"{status} 上游故障"
    return "结果不确定"


def _fmt_bytes(value):
    if value is None:
        return "-"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f} MB"
    if value >= 1_000:
        return f"{value / 1_000:.1f} KB"
    return f"{value} B"


def _pretty_snippet(body, limit=MAX_SNIPPET):
    """把响应体渲染成便于核对的片段：能解析成 JSON 就缩进展开，否则原样截断。"""
    if not body:
        return "(空)"
    try:
        parsed = json.loads(body)
    except ValueError:
        text = body.replace("\n", " ").strip()
        return f"{text[:limit]}{' …(已截断)' if len(text) > limit else ''}"
    dumped = json.dumps(parsed, ensure_ascii=False, indent=2, sort_keys=False)
    return f"{dumped[:limit]}{' …(已截断)' if len(dumped) > limit else ''}"


# ---------------------------------------------------------------- 分层连通性


def _check_layers(timeout):
    """DNS -> TCP -> TLS -> HTTPS 四层依次检查，定位断在哪一层。"""
    _print("")
    _print("=" * 78)
    _print("第一层：网络连通性（DNS -> TCP -> TLS -> HTTPS）")
    _print("=" * 78)

    # DNS
    try:
        infos = socket.getaddrinfo(HOST, PORT, proto=socket.IPPROTO_TCP)
        addrs = sorted({info[4][0] for info in infos})
        _print(f"  [DNS ] 解析 {HOST} 成功，得到 {len(addrs)} 个地址：{', '.join(addrs)}")
    except OSError as exc:
        _print(f"  [DNS ] 解析失败：{exc}")
        _print("         -> 到这里就断了，后面的 TCP/TLS/HTTP 都跑不了。")
        _print("         -> 常见原因：DNS 污染、公司网络/校园网策略、代理未生效。")
        return False

    # TCP
    try:
        with socket.create_connection((HOST, PORT), timeout=timeout):
            _print(f"  [TCP ] 与 {HOST}:{PORT} 建立 TCP 连接成功")
    except OSError as exc:
        _print(f"  [TCP ] TCP 连接失败：{exc}")
        _print("         -> 443 端口被防火墙/代理拦住了。")
        return False

    # TLS
    try:
        context = ssl.create_default_context()
        with socket.create_connection((HOST, PORT), timeout=timeout) as raw:
            with context.wrap_socket(raw, server_hostname=HOST) as tls:
                cert = tls.getpeercert() or {}
                subject = dict(item[0] for item in cert.get("subject", []) if item)
                _print(f"  [TLS ] 握手成功，协议版本 {tls.version()}")
                _print(f"         证书 CN = {subject.get('commonName', '(未读到)')}，到期时间 = {cert.get('notAfter', '(未读到)')}")
    except (ssl.SSLError, OSError) as exc:
        _print(f"  [TLS ] TLS 握手失败：{exc}")
        _print("         -> 常见原因：中间人代理、证书链不受信任、TLS 被拦截。")
        return False

    _print("  [HTTPS] 前三层都通过，接下来用真实 API 请求验证应用层（见下方 F1～F17）")
    return True


# ---------------------------------------------------------------- 测试清单


def _tests():
    """返回本次要跑的请求清单（F1～F17，与计划书步骤 69 的编号一一对应）。

    group 取值：
      "基线"   —— 已知可用的对照组，用来证明本机网络与鉴权正常；
      "请求体" —— POST /search/works 的字段验证（exclude / offset / limit=100）；
      "聚合"   —— POST /search/works/aggregate 的请求体候选形态；
      "字段"   —— 详情类端点的真实字段结构采集；
      "击杀"   —— core_output_search_by_query 的纳入判据。
    """

    def enc(**kwargs):
        return urllib.parse.urlencode(kwargs)

    return [
        # ---- 基线：先证明"本机网络 + 鉴权"没问题，否则后面所有失败都不可归因 ----
        {"id": "F1", "group": "基线",
         "name": "GET  /v3/search/works?q=…&limit=2（对照组：确认网络与鉴权正常）",
         "url": f"{BASE}/v3/search/works?{enc(q='machine learning', limit=2)}",
         "method": "GET", "payload": None},
        {"id": "F2", "group": "请求体",
         "name": "POST /v3/search/works body{q,limit=2,exclude:[fullText]}（exclude 与体积收益）",
         "url": f"{BASE}/v3/search/works", "method": "POST",
         "payload": {"q": "machine learning", "limit": 2, "exclude": ["fullText"]}},
        {"id": "F3", "group": "请求体",
         "name": "POST /v3/search/works body{…,offset:2}（验证 offset 分页被接受）",
         "url": f"{BASE}/v3/search/works", "method": "POST",
         "payload": {"q": "machine learning", "limit": 2, "offset": 2, "exclude": ["fullText"]}},
        {"id": "F4", "group": "请求体",
         "name": "POST /v3/search/works body{limit:100}（验证步骤 71 上限提到 100 的前提）",
         "url": f"{BASE}/v3/search/works", "method": "POST",
         "payload": {"q": "machine learning", "limit": 100, "exclude": ["fullText"]}},

        # ---- 聚合端点：本轮最大的未验证点 ----
        {"id": "F5", "group": "聚合",
         "name": "POST /v3/search/works/aggregate body{q}（最小可用请求体）",
         "url": f"{BASE}/v3/search/works/aggregate", "method": "POST",
         "payload": {"q": "machine learning"}},
        {"id": "F6", "group": "聚合",
         "name": "POST /v3/search/works/aggregate body{q,aggregations:[…]}（显式维度字段名）",
         "url": f"{BASE}/v3/search/works/aggregate", "method": "POST",
         "payload": {"q": "machine learning",
                     "aggregations": ["yearPublished", "authors", "publisher"]}},

        # ---- 字段结构采集：works 维度 ----
        {"id": "F7", "group": "字段",
         "name": "GET  /v3/works/171513974（works 详情：dataProviders / outputs / identifiers）",
         "url": f"{BASE}/v3/works/171513974", "method": "GET", "payload": None},
        {"id": "F8", "group": "字段",
         "name": "GET  /v3/works/171513974/outputs（core_work_outputs_by_id 的字段依据）",
         "url": f"{BASE}/v3/works/171513974/outputs", "method": "GET", "payload": None},
        {"id": "F9", "group": "字段",
         "name": "GET  /v3/works/171513974/stats（数字 ID）",
         "url": f"{BASE}/v3/works/171513974/stats", "method": "GET", "payload": None},
        {"id": "F9b", "group": "字段",
         "name": "GET  /v3/works/10.1038/nature12373/stats（确认 stats 亦接受 DOI）",
         "url": f"{BASE}/v3/works/10.1038/nature12373/stats", "method": "GET", "payload": None},
        {"id": "F10", "group": "字段",
         "name": "GET  /v3/works/10.1000/does-not-exist-xyz（未知 DOI 的 404 体形态）",
         "url": f"{BASE}/v3/works/10.1000/does-not-exist-xyz", "method": "GET", "payload": None},
        {"id": "F11", "group": "字段",
         "name": "GET  /v3/works/10.1038/nature12373/outputs（复核：子资源只收数字 ID，DOI 应 404）",
         "url": f"{BASE}/v3/works/10.1038/nature12373/outputs", "method": "GET", "payload": None},

        # ---- 字段结构采集：data-providers 与 outputs 维度 ----
        {"id": "F12", "group": "字段",
         "name": "GET  /v3/search/data-providers?q=university&limit=2（字段依据 + limit 上限）",
         "url": f"{BASE}/v3/search/data-providers?{enc(q='university', limit=2)}",
         "method": "GET", "payload": None},
        {"id": "F13", "group": "字段",
         "name": "GET  /v3/data-providers/1630（机构库详情主字段）",
         "url": f"{BASE}/v3/data-providers/1630", "method": "GET", "payload": None},
        {"id": "F14", "group": "字段",
         "name": "GET  /v3/data-providers/1630/stats（统计子资源字段）",
         "url": f"{BASE}/v3/data-providers/1630/stats", "method": "GET", "payload": None},
        {"id": "F15", "group": "字段",
         "name": "GET  /v3/data-providers/1630/outputs?limit=2（机构库 outputs 字段 + sort 取值）",
         "url": f"{BASE}/v3/data-providers/1630/outputs?{enc(limit=2)}",
         "method": "GET", "payload": None},
        {"id": "F16", "group": "字段",
         "name": "GET  /v3/outputs/29197653（output 详情：license / sdg / repositories）",
         "url": f"{BASE}/v3/outputs/29197653", "method": "GET", "payload": None},

        # ---- 击杀条件判据：三种组合必须全部 200 才纳入第 9 项工具 ----
        {"id": "F17a", "group": "击杀",
         "name": "GET  /v3/search/outputs?q=machine learning（组合 1/3：普通关键词）",
         "url": f"{BASE}/v3/search/outputs?{enc(q='machine learning', limit=2)}",
         "method": "GET", "payload": None},
        {"id": "F17b", "group": "击杀",
         "name": "GET  /v3/search/outputs?q=title:\"machine learning\"（组合 2/3：字段限定）",
         "url": f"{BASE}/v3/search/outputs?{enc(q='title:"machine learning"', limit=2)}",
         "method": "GET", "payload": None},
        {"id": "F17c", "group": "击杀",
         "name": "GET  /v3/search/outputs?q=doi:\"10.1007/s10994-024-06619-7\"（组合 3/3：DOI 精确命中）",
         "url": f"{BASE}/v3/search/outputs?{enc(q='doi:"10.1007/s10994-024-06619-7"', limit=2)}",
         "method": "GET", "payload": None},
    ]


def _run_one(test, key, timeout, index, total):
    _print("")
    _print("-" * 78)
    _print(f"[{index}/{total}] [{test['id']}] {test['name']}")
    _print(f"      {test['method']} {_mask(test['url'])}")
    if test["payload"] is not None:
        _print(f"      body: {json.dumps(test['payload'], ensure_ascii=False)}")

    res = _http(test["url"], method=test["method"], payload=test["payload"], key=key, timeout=timeout)
    verdict = _verdict(res)

    elapsed = f"{res['elapsed']:.2f} s" if res["elapsed"] is not None else "-"
    if res["error"]:
        _print(f"      结果: {res['error']}")
    else:
        _print(f"      状态码: {res['status']}   耗时: {elapsed}   响应体: {_fmt_bytes(res['bytes'])}   Content-Type: {res['ctype'] or '(空)'}")
        if res["rate"]:
            _print("      限流头: " + ", ".join(f"{k}={v}" for k, v in res["rate"].items()))
        if res["truncated"]:
            _print(f"      （响应体过大，仅读取了前 {_fmt_bytes(MAX_BODY)}，上面的字节数取自 Content-Length）")
        _print("      响应体片段（缩进展开，便于核对字段名）:")
        for line in _pretty_snippet(res["body"]).splitlines():
            _print(f"        {line}")
    _print(f"      判定: {verdict}")

    return {"id": test["id"], "group": test["group"], "name": test["name"], "verdict": verdict, "res": res}


def _summary_table(rows):
    _print("")
    _print("=" * 78)
    _print("探测结果总表")
    _print("=" * 78)
    for group in ("基线", "请求体", "聚合", "字段", "击杀"):
        subset = [r for r in rows if r["group"] == group]
        if not subset:
            continue
        _print("")
        _print(f"【{group}组】")
        for row in subset:
            res = row["res"]
            elapsed = f"{res['elapsed']:.2f} s" if res["elapsed"] is not None else "-"
            status = str(res["status"]) if res["status"] is not None else "-"
            # 固定宽度的字段放前面、名字放最后：中文在等宽字体下宽度是双份，
            # 名字里的中文一多就会把后面的判定列顶歪，所以不拿它做对齐列。
            _print(f"  {row['id']:<5} 状态 {status:<5} 耗时 {elapsed:<9} {_fmt_bytes(res['bytes']):<9} {row['verdict']:<16} {row['name']}")
    _print("")


# ---------------------------------------------------------------- 结论区


def _extract_keys(body, path_hint=None):
    """从响应体里尽力取出顶层键名，供"字段清单"结论使用；解析失败返回 None。"""
    try:
        parsed = json.loads(body)
    except ValueError:
        return None
    if isinstance(parsed, dict):
        if path_hint and isinstance(parsed.get(path_hint), dict):
            return sorted(parsed[path_hint].keys())
        return sorted(parsed.keys())
    if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
        return sorted(parsed[0].keys())
    return None


def _conclusions(rows):
    """按"先看基线、再看请求体、再看聚合、最后看击杀条件"的顺序给结论。"""
    by_id = {row["id"]: row for row in rows}

    def ok(rid):
        row = by_id.get(rid)
        return bool(row) and row["verdict"] == "可用"

    def status_of(rid):
        row = by_id.get(rid)
        if not row:
            return "(未跑)"
        res = row["res"]
        return str(res["status"]) if res["status"] is not None else (res["error"] or "?").split("：")[0]

    _print("=" * 78)
    _print("诊断结论")
    _print("=" * 78)

    # 1) 基线
    baseline_rows = [row for row in rows if row["group"] == "基线"]
    baseline_bad = [row for row in baseline_rows if row["verdict"] != "可用"]
    _print("")
    _print("【1】基线（决定后面所有结论是否可用）")
    if not baseline_rows:
        _print("    F1 未跑 —— 请至少跑 F1 以确认本机网络与鉴权正常。")
    elif baseline_bad:
        _print(f"    F1 失败（{status_of('F1')}）—— 本机网络或 CORE 整体当前不可达，")
        _print("    本次结果**不能**作为编码依据。按 QA-R013：换网络重跑，或把输出交用户复测。")
    else:
        _print("    F1 可用 —— 本机网络、TLS、鉴权正常，下面的失败可归因到端点本身。")

    # 2) POST 检索请求体
    _print("")
    _print("【2】POST /v3/search/works 请求体（步骤 71 的编码依据）")
    _print(f"    F2 exclude[fullText]：{status_of('F2')} / {by_id.get('F2', {}).get('verdict', '(未跑)')}")
    if by_id.get("F1") and by_id.get("F2") and ok("F1") and ok("F2"):
        s1 = by_id["F1"]["res"]["bytes"] or 0
        s2 = by_id["F2"]["res"]["bytes"] or 0
        _print(f"      体积对照（同为 2 条）：GET 未排除 = {_fmt_bytes(s1)}，POST exclude = {_fmt_bytes(s2)}")
    _print(f"    F3 offset=2：{status_of('F3')} / {by_id.get('F3', {}).get('verdict', '(未跑)')}")
    _print(f"    F4 limit=100：{status_of('F4')} / {by_id.get('F4', {}).get('verdict', '(未跑)')}")
    if ok("F4"):
        _print("      -> 上限提到 100 的前提成立。")
    else:
        _print("      -> limit=100 不被接受，步骤 71 的上限需按实测回调。")

    # 3) 聚合端点（本轮最大未知量）
    _print("")
    _print("【3】POST /v3/search/works/aggregate 请求体（步骤 73 的唯一编码前提）")
    if not by_id.get("F5") and not by_id.get("F6"):
        _print("    F5/F6 未跑 —— 无法判定，聚合工具不得凭猜测上线。")
    elif ok("F5") and ok("F6"):
        _print("    F5、F6 均 200 —— 聚合端点可用。请从上方 F5/F6 的响应体片段里读出：")
        _print("      (a) 请求体里维度的确切字段名（是 `aggregations` 还是别的键）；")
        _print("      (b) 响应里 `aggregations` 的嵌套层级与桶值类型。")
        keys5 = _extract_keys(by_id["F5"]["res"]["body"]) if by_id.get("F5") else None
        keys6 = _extract_keys(by_id["F6"]["res"]["body"]) if by_id.get("F6") else None
        if keys5:
            _print(f"      F5 顶层键：{', '.join(keys5)}")
        if keys6:
            _print(f"      F6 顶层键：{', '.join(keys6)}")
        agg5 = _extract_keys(by_id["F5"]["res"]["body"], path_hint="aggregations") if by_id.get("F5") else None
        if agg5:
            _print(f"      F5 aggregations 下的维度名：{', '.join(agg5)}")
        agg6 = _extract_keys(by_id["F6"]["res"]["body"], path_hint="aggregations") if by_id.get("F6") else None
        if agg6:
            _print(f"      F6 aggregations 下的维度名：{', '.join(agg6)}")
    elif ok("F5") or ok("F6"):
        good = "F5" if ok("F5") else "F6"
        bad = "F6" if good == "F5" else "F5"
        _print(f"    {good} 可用但 {bad} 失败（{status_of(bad)}）—— 以通过的形态为基准写请求体，")
        _print(f"    并把 {bad} 的失败形态记录到 buildlog，作为「不支持显式指定维度」的证据。")
    else:
        _print(f"    F5/F6 全部失败（F5={status_of('F5')}，F6={status_of('F6')}）—— 聚合端点不可用。")
        _print("    按计划书步骤 73 的风险预案：**整体回退**，本轮范围缩减为 8 项，")
        _print("    聚合维度顺延到后续版本；严禁用猜测的请求体硬上线。")
        _print("    若 F1 可用而 F5/F6 失败，仍建议把整段输出交用户复测一次（QA-R013）。")

    # 4) 字段结构
    _print("")
    _print("【4】详情类端点的字段结构（步骤 70/72/74 的归一化依据）")
    for rid, label, hint in (
        ("F7", "works 详情", None),
        ("F8", "works outputs", None),
        ("F9", "works stats（数字 ID）", None),
        ("F9b", "works stats（DOI）", None),
        ("F12", "search/data-providers", None),
        ("F13", "data-provider 详情", None),
        ("F14", "data-provider stats", None),
        ("F15", "data-provider outputs", None),
        ("F16", "output 详情", None),
    ):
        row = by_id.get(rid)
        if not row:
            continue
        res = row["res"]
        if res["status"] == 200:
            keys = _extract_keys(res["body"])
            shown = ", ".join(keys[:24]) if keys else "(非 JSON 或结构无法解析)"
            if keys and len(keys) > 24:
                shown += f" …（共 {len(keys)} 个键）"
            _print(f"    {rid:<5} {label}：200，顶层键 = {shown}")
        else:
            _print(f"    {rid:<5} {label}：{status_of(rid)}（{row['verdict']}）")
    f11 = by_id.get("F11")
    if f11:
        _print(f"    F11   DOI 打在 /works/{{id}}/outputs 上：{status_of('F11')}（预期 404，用于确认子资源只收数字 ID）")
    f10 = by_id.get("F10")
    if f10:
        body = (f10["res"]["body"] or "").strip()
        _print(f"    F10   未知 DOI 的 404 响应体：{body[:160] if body else '(空)'}")
        _print("          -> 步骤 70 的 _error_for() 404 分支必须自带兜底文案，不能依赖上游 message。")

    # 5) 击杀条件（第 9 项工具）
    _print("")
    _print("【5】击杀条件：core_output_search_by_query（C 档第 9 项，条件纳入）")
    kill_rows = [by_id[rid] for rid in ("F17a", "F17b", "F17c") if rid in by_id]
    if not kill_rows:
        _print("    F17a/F17b/F17c 未跑 —— 无法判定，第 9 项按「不纳入」处理（保守）。")
    else:
        for row in kill_rows:
            _print(f"    {row['id']}：{status_of(row['id'])} / {row['verdict']}")
        passed = len(kill_rows) == 3 and all(row["verdict"] == "可用" for row in kill_rows)
        _print("")
        if passed:
            _print("    => 三种组合全部 200：**判定为「可纳入」**，本版本工具总数按 29 计。")
        else:
            bad = ", ".join(f"{row['id']}={row['verdict']}" for row in kill_rows if row["verdict"] != "可用")
            _print(f"    => 存在非 200 组合（{bad}）：**判定为「不纳入」**，本版本工具总数按 28 计。")
            _print("       按计划书：击杀条件是硬约束，不得反复重试直到碰上一次 200 再纳入。")
            _print("       其余 8 项不受影响；构建时 buildlog 需记录失败证据（状态码 + 响应体摘要 + 请求形态）。")
        if len(kill_rows) < 3:
            _print("       （本次只跑了部分组合，判定不完整，请把 F17a/F17b/F17c 三个都跑一遍。）")

    _print("")
    _print("=" * 78)
    _print("下一步：把从「第一层：网络连通性」到这里的整段输出复制回对话即可。")
    _print("脚本不做任何写操作，也不会下载/保存任何文件内容。")
    _print("=" * 78)


def main():
    parser = argparse.ArgumentParser(
        description="CORE API v3 字段/端点能力探测脚本（只读网络探测，不改任何文件）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--timeout", type=float, default=60.0, help="单次请求超时秒数，默认 60")
    parser.add_argument("--only", default="",
                        help="只跑指定编号，逗号分隔，例如 F5,F6,F8,F16,F17a")
    args = parser.parse_args()

    key, origin = _load_api_key()
    if key:
        _print(f"[鉴权] 已读取到 CORE API Key（来源：{origin}，长度 {len(key)}，输出中已自动打码）")
    else:
        _print("[鉴权] 未找到 CORE_API_KEY（环境变量与仓库根目录 .env 均未命中），将以匿名方式运行。")
        _print("       匿名档位更低（100 tokens/天、10 次/分钟），且官方不提供 fullText。")

    _print(f"[参数] 单次请求超时 = {args.timeout:g} 秒；仓库远端 = {BASE}")

    layers_ok = _check_layers(args.timeout)

    tests = _tests()
    if args.only.strip():
        wanted = {token.strip().upper() for token in args.only.split(",") if token.strip()}
        known = {test["id"].upper() for test in tests}
        unknown = wanted - known
        if unknown:
            _print(f"[提示] --only 里有无法识别的编号，已忽略：{', '.join(sorted(unknown))}")
        tests = [test for test in tests if test["id"].upper() in wanted]
        if not tests:
            _print("[中止] --only 没有匹配到任何测试项，请检查编号后重试。")
            return 2

    _print("")
    _print("=" * 78)
    _print(f"第二层：API 请求实测（共 {len(tests)} 项）")
    _print("=" * 78)

    rows = []
    for index, test in enumerate(tests, start=1):
        rows.append(_run_one(test, key, args.timeout, index, len(tests)))

    _summary_table(rows)
    _conclusions(rows)

    if not layers_ok:
        _print("")
        _print("[注意] 上面第一层的分层检查已经失败过，本次 API 请求的失败结果不能归因到端点。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
