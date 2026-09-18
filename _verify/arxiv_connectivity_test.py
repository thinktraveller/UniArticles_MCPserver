"""
export.arxiv.org 网络连通性分层诊断脚本
=======================================

用途：判断当前网络环境能否访问 arXiv 的公开 API（export.arxiv.org）。

背景：2026-09-18 对 UniArticles v3.4.0 的剩余源集合（9 源 / 21 工具）重跑全量
      工具可用性回归时，arXiv 的两个工具
      `arxiv_paper_detail_by_id` 与 `arxiv_latest_paper_list_by_category`
      分别耗时 337 秒、171 秒后以连接超时失败，而**同一轮**里
      `arxiv_paper_search_by_query` 在 1.4 秒内正常返回了 3 条结果。随后用
      Python 标准库直接请求 export.arxiv.org，30 秒无响应亦超时。

      失败形态是"连接超时"，而非 TLS 握手失败或 4xx：既可能是 arXiv 上游在
      限流/降级，也可能是当前网络到该主机的链路问题。从单机单次结果无法区分
      这两者——按本项目 QA-R013 确立的 `_verify/` 流程规则（见 AGENTS.md），
      这种情况**不得**由 agent 单方判定该数据源不可用，须交由用户在实际网络
      环境下自行验证后再下结论。

怎么用：
      在项目根目录打开 PowerShell / CMD，执行：

          python _verify/arxiv_connectivity_test.py

      然后把整段输出（尤其是最后的“诊断结论”）复制反馈即可。
      如果当前网络失败，可换一个网络（手机热点 / 其它宽带 / VPN）再跑一次，
      用来区分"上游问题"与"本网络链路问题"。

这个脚本只做只读的网络探测，不改任何文件、不需要 API Key、不下载任何东西。
它把“能不能连上 export.arxiv.org”拆成 4 层逐步检查（DNS → TCP → TLS → HTTP），
哪一层断了就给出该层最可能的原因。
"""

import re
import socket
import ssl
import sys
import urllib.request
import urllib.error

# Windows 控制台默认可能是 GBK 编码，会把中文显示成乱码。
# 这里强制把输出改成 UTF-8，保证提示文字在 PowerShell / CMD 里能正常显示。
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# IPv4 地址脱敏正则：匹配点分十进制的 4 段数字。
# 用途：用户会把整段输出复制给对话助手做诊断，不希望本机解析出的真实 IP
#       明文外泄。这里统一在打印时把 IP 的后两段打码（如 151.101.2.132 ->
#       151.101.xxx.xxx），保留前两段方便判断大致网段（够用来分辨是不是同一
#       网络环境的重复测试），但不暴露完整可识别的主机地址。
_IPV4_RE = re.compile(r"\b(\d{1,3})\.(\d{1,3})\.\d{1,3}\.\d{1,3}\b")


def _mask_ipv4(text):
    """把字符串里所有 IPv4 地址的后两段替换成 xxx.xxx。"""
    return _IPV4_RE.sub(r"\1.\2.xxx.xxx", text)


def _print(*args, **kwargs):
    """print 的包装函数：打印前对所有字符串参数做 IPv4 脱敏。

    脚本内所有输出一律走这里，这样以后新增打印语句也会自动脱敏，
    不用逐行手动改字符串，避免遗漏。
    """
    safe_args = [_mask_ipv4(a) if isinstance(a, str) else a for a in args]
    builtin_print(*safe_args, **kwargs)


# 保存一份未被包装的 print，供上面的 _print 内部调用，避免无限递归。
builtin_print = print

HOST = "export.arxiv.org"
PORT = 443
TIMEOUT = 15  # 单层探测的超时秒数（项目内实测失败时是 300+ 秒，这里 15 秒足够区分）

# arXiv 的 `arxiv` 包三个工具全部走同一个 API 端点，只是查询参数不同。
# 这里分别探测"检索"与"按 ID 取详情"两条实际使用的路径。
PROBE_URLS = [
    ("检索路径 (search_query)", f"https://{HOST}/api/query?search_query=all:electron&max_results=1"),
    ("详情路径 (id_list)", f"https://{HOST}/api/query?id_list=1706.03762"),
]


def line():
    _print("-" * 60)


def step_dns():
    """第 1 层：DNS 解析。"""
    _print(f"[1/4] DNS 解析：{HOST}")
    try:
        ip = socket.gethostbyname(HOST)
        _print(f"  [成功] 解析到 IP：{ip}")
        return True, ip
    except socket.gaierror as e:
        _print(f"  [失败] DNS 解析失败：{e}")
        _print("  可能原因：DNS 污染、域名被拦截，或本机 DNS 配置异常。")
        return False, None


def step_tcp(ip):
    """第 2 层：TCP 连接（443 端口）。"""
    _print(f"[2/4] TCP 连接：{ip}:{PORT}")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)
    try:
        sock.connect((ip, PORT))
        _print("  [成功] TCP 三次握手完成，端口可达。")
        return True
    except (socket.timeout, TimeoutError):
        _print(f"  [失败] TCP 连接超时（{TIMEOUT} 秒无响应）。")
        _print("  可能原因：防火墙丢包、路由不可达，或该 IP 被限制访问。")
        return False
    except OSError as e:
        _print(f"  [失败] TCP 连接失败：{e}")
        return False
    finally:
        sock.close()


def step_tls():
    """第 3 层：TLS 握手。"""
    _print(f"[3/4] TLS 握手：{HOST}:{PORT}")
    ctx = ssl.create_default_context()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)
    try:
        sock.connect((HOST, PORT))
        with ctx.wrap_socket(sock, server_hostname=HOST) as tls_sock:
            cert = tls_sock.getpeercert()
            _print(f"  [成功] TLS 握手完成，协议版本：{tls_sock.version()}")
            subject = dict(x[0] for x in cert.get("subject", []))
            _print(f"         证书主体：{subject.get('commonName', '(未提供)')}")
        return True
    except ssl.SSLError as e:
        _print(f"  [失败] TLS 握手失败：{e}")
        _print("  可能原因：中间人拦截、证书校验不通过，或该网络对 443 做了劫持。")
        return False
    except (socket.timeout, TimeoutError):
        _print(f"  [失败] TLS 握手超时（{TIMEOUT} 秒无响应）。")
        return False
    except OSError as e:
        _print(f"  [失败] TLS 阶段出错：{e}")
        return False
    finally:
        try:
            sock.close()
        except OSError:
            pass


def step_http():
    """第 4 层：HTTP 请求（分别探测检索与详情两条真实路径）。"""
    _print("[4/4] HTTP 请求：")
    all_ok = True
    for label, url in PROBE_URLS:
        _print(f"  → {label}")
        req = urllib.request.Request(url, headers={"User-Agent": "UniArticlesMCP-verify/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                status = resp.getcode()
                body = resp.read(300).decode("utf-8", errors="replace")
                _print(f"    [成功] HTTP {status}，已收到响应（前 200 字）：{body[:200]}")
        except urllib.error.HTTPError as e:
            # 能拿到状态码说明网络是通的，属于应用层响应。
            _print(f"    [部分成功] 网络可达，但服务器返回 HTTP {e.code}。")
            if e.code == 429:
                _print("    说明：429 是限流（请求太频繁），网络本身没问题，稍后重试即可。")
            elif e.code in (503, 502, 500):
                _print("    说明：服务端暂时不可用（上游降级/维护），与本机网络无关。")
            else:
                _print("    说明：网络连通正常，这是应用层的响应问题，与网络封锁无关。")
            try:
                err_body = e.read(300).decode("utf-8", errors="replace")
                if err_body:
                    _print(f"    服务器响应体（前 300 字节）：{err_body}")
            except Exception:  # noqa: BLE001 - 读响应体失败不影响诊断
                pass
        except (socket.timeout, TimeoutError):
            _print(f"    [失败] HTTP 请求超时（{TIMEOUT} 秒无响应）。")
            all_ok = False
        except urllib.error.URLError as e:
            _print(f"    [失败] 请求未能完成：{e.reason}")
            all_ok = False
    return all_ok


def conclude(reached):
    """打印最终诊断结论，用大白话说明结果。"""
    _print("=" * 60)
    _print(" 诊断结论 ")
    _print("=" * 60)
    if reached == "全部通过":
        _print("[结果] 当前网络可以正常访问 export.arxiv.org 的 API。")
        _print("       4 层检查全部通过，arXiv 在这个网络环境下是可用的。")
        _print("       => 此前观察到的超时属于 arXiv 上游的临时状态，")
        _print("          可稍后重跑 `_verify/tool_availability_check.py` 复核。")
    else:
        _print(f"[结果] 当前网络无法正常访问 export.arxiv.org，卡在了「{reached}」这一层。")
        _print("       上面对应步骤已经给出了该层最可能的原因。")
        _print("       => 若卡在 DNS/TCP/TLS，通常是本网络环境的限制，")
        _print("          换一个网络（手机热点 / 其它宽带 / VPN）再跑一次往往结果不同。")
        _print("       => 若 4 层都通、只是 HTTP 层超时或返回 5xx，则更可能是")
        _print("          arXiv 上游在限流/降级，与本机网络无关，稍后重试即可。")
        _print("       => 请把从头到尾的完整输出反馈回来，用于判断是否为临时故障。")
    _print("=" * 60)


def main():
    _print("=" * 60)
    _print(" export.arxiv.org 网络连通性诊断 ")
    _print("=" * 60)
    _print("将从 4 个层面逐步检查：DNS → TCP → TLS → HTTP")
    _print("哪一步失败会立即停止，并给出该层的可能原因。")
    line()

    ok_dns, ip = step_dns()
    line()
    if not ok_dns:
        conclude(reached="DNS 解析")
        return

    ok_tcp = step_tcp(ip)
    line()
    if not ok_tcp:
        conclude(reached="TCP 连接")
        return

    ok_tls = step_tls()
    line()
    if not ok_tls:
        conclude(reached="TLS 握手")
        return

    ok_http = step_http()
    line()
    if not ok_http:
        conclude(reached="HTTP 请求")
        return

    conclude(reached="全部通过")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        _print("\n[已取消] 用户中断了诊断。")
        sys.exit(1)
