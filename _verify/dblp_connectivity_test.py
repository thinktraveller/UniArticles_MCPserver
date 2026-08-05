"""
dblp.org 网络连通性分层诊断脚本
================================

用途：判断当前网络环境能否访问 dblp.org（计算机科学文献库）的公开 API。

背景：dblp 是 UniArticles v3.0.0 的候选数据源之一，但在此前的探测环境里
      对 dblp.org 的 TLS 握手直接失败（HTTP 状态码 000），无法确认 dblp 到底
      是真的不可用，还是仅仅是那台探测机器的网络被拦截了。由于 MCP Server
      最终运行在终端用户自己的电脑上，网络环境可能完全不同，所以需要用户
      在实际部署/使用的网络下亲自跑一遍这个脚本，把结果反馈回来定案。
      （对应 project-docs/goal.md 的 QA-R012，dblp 状态：待定。）

怎么用：
      在项目根目录打开 PowerShell / CMD，执行：

          python _verify/dblp_connectivity_test.py

      然后把整段输出（尤其是最后的“诊断结论”）复制反馈即可。

这个脚本只做只读的网络探测，不改任何文件、不需要 API Key、不联网下载任何东西，
放心运行。它把“能不能连上 dblp”拆成 4 层逐步检查，哪一层断了就告诉你大概是
什么原因（DNS 污染 / 防火墙拦截 / TLS 被中间人拦截 / 应用层限流等）。
"""

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

HOST = "dblp.org"
PORT = 443
# 一个真实的轻量 API 请求：搜索标题含 "graph" 的论文，只要 1 条，返回 JSON。
API_URL = "https://dblp.org/search/publ/api?q=graph&format=json&h=1"
TIMEOUT = 15  # 每一步的超时秒数


def line():
    print("-" * 60)


def step_dns():
    """第 1 层：DNS 解析——域名能不能翻译成 IP 地址。"""
    print("[第 1 步 / 共 4 步] DNS 解析：把域名 dblp.org 翻译成 IP 地址 ...")
    try:
        infos = socket.getaddrinfo(HOST, PORT, proto=socket.IPPROTO_TCP)
        ips = sorted({info[4][0] for info in infos})
        print(f"  [成功] dblp.org 解析到 IP：{', '.join(ips)}")
        return True, ips[0]
    except socket.gaierror as e:
        print(f"  [失败] 无法解析域名：{e}")
        print("  可能原因：本机没有网络、DNS 服务器不通，或该域名被 DNS 污染/拦截。")
        return False, None


def step_tcp(ip):
    """第 2 层：TCP 连接——能不能连上对方 443 端口。"""
    print(f"[第 2 步 / 共 4 步] TCP 连接：尝试连接 {ip}:{PORT}（HTTPS 端口）...")
    sock = None
    try:
        sock = socket.create_connection((ip, PORT), timeout=TIMEOUT)
        print("  [成功] TCP 端口已连通，对方 443 端口可达。")
        return True
    except (socket.timeout, TimeoutError):
        print("  [失败] 连接超时，对方端口在规定时间内没有响应。")
        print("  可能原因：防火墙/网关静默丢弃了数据包，或该 IP 在本网络被封锁。")
        return False
    except OSError as e:
        print(f"  [失败] 连接被拒绝或网络错误：{e}")
        print("  可能原因：防火墙主动拒绝连接，或本机没有到外网的路由。")
        return False
    finally:
        if sock is not None:
            sock.close()


def step_tls():
    """第 3 层：TLS 握手——能不能建立加密通道并验证证书。"""
    print(f"[第 3 步 / 共 4 步] TLS 握手：与 {HOST} 建立 HTTPS 加密通道 ...")
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((HOST, PORT), timeout=TIMEOUT) as raw:
            with ctx.wrap_socket(raw, server_hostname=HOST) as tls:
                cert = tls.getpeercert()
                subject = dict(x[0] for x in cert.get("subject", []))
                issuer = dict(x[0] for x in cert.get("issuer", []))
                print("  [成功] TLS 握手完成，加密通道已建立。")
                print(f"         证书颁发给：{subject.get('commonName', '未知')}")
                print(f"         证书颁发者：{issuer.get('commonName', '未知')}")
                print(f"         协议版本：{tls.version()}")
        return True
    except ssl.SSLCertVerificationError as e:
        print(f"  [失败] TLS 证书验证失败：{e}")
        print("  可能原因：网络中存在 HTTPS 中间人拦截（如企业代理/防火墙替换了证书），")
        print("            或本机时间不对、根证书缺失。")
        return False
    except ssl.SSLError as e:
        print(f"  [失败] TLS 握手出错：{e}")
        print("  可能原因：连接在加密协商阶段被设备干扰/重置（常见于对特定境外站点的拦截）。")
        return False
    except (socket.timeout, TimeoutError):
        print("  [失败] TLS 握手超时。")
        print("  可能原因：握手数据包被中途丢弃，通常也是防火墙层面的干扰。")
        return False
    except OSError as e:
        print(f"  [失败] 握手期间网络错误：{e}")
        return False


def step_http():
    """第 4 层：HTTP 实际请求——真正调用一次 dblp API，看能不能拿到数据。"""
    print("[第 4 步 / 共 4 步] HTTP 请求：真正调用一次 dblp 搜索 API ...")
    print(f"         请求地址：{API_URL}")
    req = urllib.request.Request(
        API_URL,
        headers={"User-Agent": "UniArticles-dblp-connectivity-test/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            status = resp.getcode()
            body = resp.read(400).decode("utf-8", errors="replace")
            print(f"  [成功] 服务器返回 HTTP {status}，已收到响应内容。")
            print(f"         响应开头（前 200 字）：{body[:200]}")
            return True
    except urllib.error.HTTPError as e:
        # 能连上并拿到 HTTP 状态码，说明网络是通的，只是服务端返回了错误码。
        print(f"  [部分成功] 网络可达，但服务器返回错误状态 HTTP {e.code}。")
        if e.code == 429:
            print("  说明：429 是限流（请求太频繁），网络本身没问题，稍后重试即可。")
        else:
            print("  说明：网络连通正常，这是应用层的响应问题，与网络封锁无关。")
        return True
    except urllib.error.URLError as e:
        print(f"  [失败] 请求未能完成：{e.reason}")
        print("  可能原因：应用层被拦截、超时或连接被重置。")
        return False
    except (socket.timeout, TimeoutError):
        print("  [失败] HTTP 请求超时。")
        return False


def main():
    print("=" * 60)
    print(" dblp.org 网络连通性诊断 ")
    print("=" * 60)
    print("将从 4 个层面逐步检查：DNS → TCP → TLS → HTTP")
    print("哪一步失败会立即停止，并给出该层的可能原因。")
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


def conclude(reached):
    """打印最终诊断结论，用大白话说明结果。"""
    print("=" * 60)
    print(" 诊断结论 ")
    print("=" * 60)
    if reached == "全部通过":
        print("[结果] 当前网络可以正常访问 dblp.org 的 API。")
        print("       4 层检查全部通过，dblp 在这个网络环境下是可用的。")
        print("       => 可以把这个结果反馈回去，用于确定是否将 dblp 纳入数据源。")
    else:
        print(f"[结果] 当前网络无法正常访问 dblp.org，卡在了「{reached}」这一层。")
        print("       上面对应步骤已经给出了该层最可能的原因。")
        print("       => 这通常是本网络环境的限制，换一个网络（如手机热点、")
        print("          其它宽带、VPN）再跑一次本脚本，往往结果会不同。")
        print("       => 请把从头到尾的完整输出反馈回去，用于判断 dblp 的去留。")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[已取消] 用户中断了诊断。")
        sys.exit(1)
