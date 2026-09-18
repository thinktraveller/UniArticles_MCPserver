"""
CORE API v3 复测诊断脚本
=========================

用途：在**你自己的真实网络环境**里复测 CORE API（api.core.ac.uk）的几个端点，
      判断此前记录的失败/不一致结果到底是"端点本身有问题"，还是"当时那台
      探测机器的网络环境 / 上游瞬时故障"。

背景：UniArticles 正在评估把 CORE 从当前的 1 个工具（关键词检索）扩展到约
      7-8 个工具（详见 project-docs/goal.md 的《附录：CORE API v3 能力盘点》
      与 QA-R021）。2026-09-18 的调研在两个不同探测环境里跑出了不一致的结果，
      有 5 类端点需要用户复测：

        1. GET  /v3/search/journals   - 连续三次读超时（45 / 60 / 95 秒）
        2. POST /v3/discover          - 500，错误体显示下游 oadiscovery 服务 404
        3. POST /v3/recommend         - 500，错误体显示下游 recommender 服务 500
        4. GET  /v3/works/tei/{id}    - 一次 200 但响应体 0 字节，另一 ID 返回 404
        5. GET  /v3/search/outputs    - 一个环境两次 500，另一个环境四种组合全 200

      用户在 QA-R021 第 3 问选择了"先复测再立项"(a) 档，因此需要用户在自己的
      网络环境里跑一遍本脚本、把结果反馈回来，才能锁定 CORE 的扩展范围。这也是
      项目既定的 QA-R013 流程：构建期遇到疑似网络/环境噪声的失败，不得由 agent
      单方面定性，必须产出独立诊断脚本交用户复测。

怎么用：在项目根目录打开 PowerShell / CMD，执行：

          python _verify/core_api_probe.py

      网络较慢时可放宽超时，或只跑其中几项：

          python _verify/core_api_probe.py --timeout 90
          python _verify/core_api_probe.py --only R1,R6,R7,R8

      然后把整段输出（尤其是最后的"诊断结论"）复制反馈即可。

这个脚本只做只读的网络探测：不改任何文件、不下载任何二进制、不落地任何内容；
输出里出现的 IPv4 地址与 API Key 会自动打码，可以安全粘贴。API Key 优先从
环境变量 CORE_API_KEY 读取，读不到再回退到仓库根目录的 .env；两者都没有时脚本
会以匿名方式继续跑完（匿名档位更低：100 tokens/天、10 次/分钟，且官方不提供
fullText）。
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
USER_AGENT = "UniArticlesMCP-CoreProbe/1.0 (+https://github.com/thinktraveller/UniArticles_MCPserver)"

# 单次响应最多读取 512 KB：CORE 的 works/outputs 记录默认内联 fullText，
# 不去限制的话一个 limit=100 的查询就能拉回 1 MB 以上。脚本只需要判断
# "能不能拿到数据"，不需要把正文全部读进内存。
MAX_BODY = 512 * 1024

# CORE 官方称每个响应都带这三个限流头，实测确认存在且对区分
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


# ---------------------------------------------------------------- 分层连通性


def _check_layers(timeout):
    """DNS -> TCP -> TLS -> HTTPS 四层依次检查，定位断在哪一层。"""
    _print("")
    _print("=" * 78)
    _print("第一层：网络连通性（DNS -> TCP -> TLS -> HTTPS）")
    _print("=" * 78)

    # DNS
    addrs = []
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

    _print("  [HTTPS] 前三层都通过，接下来用真实 API 请求验证应用层（见下方基线组）")
    return True


# ---------------------------------------------------------------- 测试清单


def _tests():
    """返回本次要跑的请求清单。

    group = "基线" 的是已知可用的对照组：它们的成败决定"复测项的失败能不能
    归因到端点本身"。group = "复测" 的是 QA-R021 里记录过失败/不一致的项。
    """
    works_q = urllib.parse.urlencode({"q": "machine learning", "limit": 1})
    works_25 = urllib.parse.urlencode({"q": "machine learning", "limit": 25})
    outputs_plain = urllib.parse.urlencode({"q": "machine learning", "limit": 2})
    outputs_title = urllib.parse.urlencode({"q": 'title:"machine learning"', "limit": 2})
    outputs_doi = urllib.parse.urlencode({"q": 'doi:"10.1007/s10994-024-06619-7"', "limit": 2})
    journals_q = urllib.parse.urlencode({"q": "Nature", "limit": 2})

    return [
        # ---- 对照组（预期全部可用；其中一个失败就说明是本机网络问题） ----
        {"id": "B1", "group": "基线", "name": "GET  /v3/search/works（关键词检索，已知 200）",
         "url": f"{BASE}/v3/search/works?{works_q}", "method": "GET", "payload": None},
        {"id": "B2", "group": "基线", "name": "GET  /v3/works/{裸DOI}（按 DOI 取详情，已知 200）",
         "url": f"{BASE}/v3/works/10.1038/nature12373", "method": "GET", "payload": None},
        {"id": "B3", "group": "基线", "name": "GET  /v3/search/works limit=25（现工具上限，测响应体体积）",
         "url": f"{BASE}/v3/search/works?{works_25}", "method": "GET", "payload": None},
        {"id": "B4", "group": "基线", "name": "POST /v3/search/works + exclude[fullText]（(a) 档拟采用的改法）",
         "url": f"{BASE}/v3/search/works", "method": "POST",
         "payload": {"q": "machine learning", "limit": 25, "exclude": ["fullText"]}},
        {"id": "B5", "group": "基线", "name": "GET  /v3/data-providers/1630（机构库详情，已知 200）",
         "url": f"{BASE}/v3/data-providers/1630", "method": "GET", "payload": None},
        {"id": "B6", "group": "基线", "name": "GET  /v3/outputs/29197653（output 详情，(c) 档候选）",
         "url": f"{BASE}/v3/outputs/29197653", "method": "GET", "payload": None},

        # ---- 复测项（QA-R021 里记录过失败 / 两环境结果不一致） ----
        {"id": "R1", "group": "复测", "name": "GET  /v3/search/journals（期刊关键词检索，此前连续超时）",
         "url": f"{BASE}/v3/search/journals?{journals_q}", "method": "GET", "payload": None},
        {"id": "R2", "group": "复测", "name": "POST /v3/discover（按 DOI 找全文链接，此前 500）",
         "url": f"{BASE}/v3/discover", "method": "POST", "payload": {"doi": "10.1038/nature12373"}},
        {"id": "R3", "group": "复测", "name": "POST /v3/recommend（相似推荐，此前 500）",
         "url": f"{BASE}/v3/recommend", "method": "POST",
         "payload": {"identifier": "core:171513974", "limit": "3", "result_type": "works"}},
        {"id": "R4", "group": "复测", "name": "GET  /v3/works/tei/267312（结构化全文，此前 200 但 0 字节）",
         "url": f"{BASE}/v3/works/tei/267312", "method": "GET", "payload": None},
        {"id": "R5", "group": "复测", "name": "GET  /v3/works/tei/127610059（文档示例 ID，此前 404）",
         "url": f"{BASE}/v3/works/tei/127610059", "method": "GET", "payload": None},
        {"id": "R6", "group": "复测", "name": "GET  /v3/search/outputs 普通关键词（此前 500 vs 4/4 全 200）",
         "url": f"{BASE}/v3/search/outputs?{outputs_plain}", "method": "GET", "payload": None},
        {"id": "R7", "group": "复测", "name": "GET  /v3/search/outputs 字段限定 title:（同上，测表达式差异）",
         "url": f"{BASE}/v3/search/outputs?{outputs_title}", "method": "GET", "payload": None},
        {"id": "R8", "group": "复测", "name": "GET  /v3/search/outputs DOI 精确命中（(c) 档候选的可行性前提）",
         "url": f"{BASE}/v3/search/outputs?{outputs_doi}", "method": "GET", "payload": None},
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
        snippet = (res["body"] or "").replace("\n", " ").strip()
        _print(f"      响应体前 300 字符: {snippet[:300] if snippet else '(空)'}")
    _print(f"      判定: {verdict}")

    return {"id": test["id"], "group": test["group"], "name": test["name"], "verdict": verdict, "res": res}


def _summary_table(rows):
    _print("")
    _print("=" * 78)
    _print("诊断结论")
    _print("=" * 78)
    for group in ("基线", "复测"):
        subset = [r for r in rows if r["group"] == group]
        if not subset:
            continue
        _print("")
        _print(f"【{group}组】" + ("（对照组：预期全部可用，用来证明本机网络正常）" if group == "基线" else "（QA-R021 记录过失败/不一致的项）"))
        for row in subset:
            res = row["res"]
            elapsed = f"{res['elapsed']:.2f} s" if res["elapsed"] is not None else "-"
            status = str(res["status"]) if res["status"] is not None else "-"
            # 固定宽度的字段放前面、名字放最后：中文在等宽字体下宽度是双份，
            # 名字里的中文一多就会把后面的判定列顶歪，所以不拿它做对齐列。
            _print(f"  {row['id']:<3} 状态 {status:<5} 耗时 {elapsed:<9} {_fmt_bytes(res['bytes']):<9} {row['verdict']:<12} {row['name']}")
    _print("")


def _conclusions(rows):
    """按"先看对照组、再看复测项"的顺序给结论。"""
    by_id = {row["id"]: row for row in rows}
    baseline = [row for row in rows if row["group"] == "基线"]
    baseline_bad = [row for row in baseline if row["verdict"] != "可用"]

    _print("=" * 78)
    _print("怎么读这份结论")
    _print("=" * 78)

    if baseline_bad:
        bad_ids = ", ".join(row["id"] for row in baseline_bad)
        _print(f"1. 对照组里 {bad_ids} 也失败了 —— 说明**本机网络环境**或 CORE 整体在当前")
        _print("   时刻不可达，这次复测**不能**用来判断某个具体端点好不好使。建议换个")
        _print("   网络（例如手机热点）重跑一次，再对比结果。")
    else:
        _print("1. 对照组全部可用 —— 本机网络、TLS、鉴权都正常，因此下面复测项出现的")
        _print("   异常可以归因到**端点/上游服务本身**，而不是你的网络。")

    # outputs 检索：唯一会改变 (c) 档工具清单的复测项
    outputs = [by_id.get("R6"), by_id.get("R7"), by_id.get("R8")]
    outputs = [row for row in outputs if row]
    outputs_ok = [row for row in outputs if row["verdict"] == "可用"]
    _print("")
    if len(outputs_ok) == len(outputs) and outputs_ok:
        _print(f"2. 【outputs 关键词检索】本次跑的 {len(outputs_ok)} 个查询组合全部返回 200 —— 此前那个 500 更像是")
        _print("   上游瞬时故障或与特定查询表达式相关，不是稳定故障。**这是唯一会改变 CORE")
        _print("   扩展工具清单的复测项**：若维持可用，goal.md 候选清单第 9 项")
        _print("   （core_output_search_by_query）可以纳入 (c) 档。")
        if len(outputs) < 3:
            _print("   （提示：本次只跑了部分组合，建议把 R6/R7/R8 三个都跑一遍再下结论。）")
    else:
        bad = ", ".join(f"{row['id']}={row['verdict']}" for row in outputs if row["verdict"] != "可用")
        _print(f"2. 【outputs 关键词检索】未全部通过（{bad}）—— 该能力**不稳定**，不应纳入")
        _print("   (c) 档，按「不含 outputs 关键词检索」成立即可。")

    _print("")
    _print("3. 【不影响范围的复测项】以下四项都不在 (c) 档候选内，复测结果只用于记录，")
    _print("   不改变已经定下的扩展范围：")
    for rid, note in (
        ("R1", "journals 关键词检索 —— 期刊维度已确认排除（ISSN 查询只返回回显式空壳记录）"),
        ("R2", "discover —— 语义是\"按 DOI 找全文链接\"，已被第 2 问\"不加入相关功能\"覆盖"),
        ("R3", "recommend —— 相似推荐不在 (c) 档内"),
        ("R4", "works TEI —— 已被第 2 问\"不返回全文/不下载二进制\"的硬边界排除"),
        ("R5", "works TEI —— 同上"),
    ):
        row = by_id.get(rid)
        if row:
            _print(f"    - {rid}：{note}（本次判定：{row['verdict']}）")

    # 顺带验证 (a) 档的性能改法是否在本机同样成立
    b3, b4 = by_id.get("B3"), by_id.get("B4")
    if b3 and b4 and b3["verdict"] == "可用" and b4["verdict"] == "可用":
        size3, size4 = b3["res"]["bytes"], b4["res"]["bytes"]
        if size3 and size4:
            _print("")
            _print(f"4. 【顺带验证 (a) 档的改法】同样 25 条 works：")
            _print(f"      B3 现状（GET，响应内含被丢弃的 fullText）= {_fmt_bytes(size3)} / {b3['res']['elapsed']:.2f} s")
            _print(f"      B4 改法（POST + exclude[fullText]）      = {_fmt_bytes(size4)} / {b4['res']['elapsed']:.2f} s")
            if size4 and size3:
                _print(f"      -> 体积降到约 1/{size3 / size4:.1f}，改法在本机同样有效。")

    _print("")
    _print("=" * 78)
    _print("下一步：把从「第一层：网络连通性」到这里的整段输出复制回对话即可。")
    _print("脚本不做任何写操作，也不会下载/保存任何文件内容。")
    _print("=" * 78)


def main():
    parser = argparse.ArgumentParser(
        description="CORE API v3 复测诊断脚本（只读网络探测，不改任何文件）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--timeout", type=float, default=60.0, help="单次请求超时秒数，默认 60")
    parser.add_argument("--only", default="", help="只跑指定编号，逗号分隔，例如 R1,R6,R7,R8")
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
        unknown = wanted - {test["id"] for test in tests}
        if unknown:
            _print(f"[提示] --only 里有无法识别的编号，已忽略：{', '.join(sorted(unknown))}")
        tests = [test for test in tests if test["id"] in wanted]
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
