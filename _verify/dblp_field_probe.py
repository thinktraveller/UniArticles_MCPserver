"""
dblp.org 字段结构采集脚本（编码前置探测，非连通性诊断）
====================================================

用途：在能访问 dblp.org 的网络环境下，真实调用一次 dblp 论文搜索 API，
      **完整打印返回 JSON 的字段结构**，用于核对/修正 UniArticles v3.0.0
      dblp 数据源（`src/uniarticles/sources/dblp.py`）的归一化字段映射。

与同目录 `dblp_connectivity_test.py` 的分工：
      - `dblp_connectivity_test.py`：诊断“连不连得通”（DNS→TCP→TLS→HTTP 分层）。
      - 本脚本 `dblp_field_probe.py`：连通之后“返回什么字段”，采集真实结构。

背景（重要，对应 project-docs/goal.md QA-R013 与 project-plan.md 步骤 39）：
      构建方（project-builder-cn）在自己的探测环境中对 dblp.org 的 TLS 握手
      **反复失败**（`UNEXPECTED_EOF_WHILE_READING` / 握手超时，多次重试一致），
      因此**未能**在构建环境采集到 dblp 的真实字段结构。dblp.py 的字段映射
      目前是**依据 dblp 官方 API 文档的字面描述**编写的，**尚未经过本项目真实
      抓包验证**。按 QA-R013 的流程约束，本脚本被留在 `_verify/` 供用户在其
      可达 dblp.org 的网络环境下运行，把真实输出反馈回来核对字段。

怎么用：
      在项目根目录打开 PowerShell / CMD，执行：

          python _verify/dblp_field_probe.py

      然后把 “采集到的字段结构” 段落整段复制反馈即可。

本脚本只读、不改任何文件、不需要 API Key。
"""

import builtins
import json
import re
import sys
import urllib.error
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# IPv4 脱敏（与连通性脚本一致）：打印前把 IP 后两段打码，避免复制输出时外泄本机 IP。
_IPV4_RE = re.compile(r"\b(\d{1,3})\.(\d{1,3})\.\d{1,3}\.\d{1,3}\b")


def _mask_ipv4(text):
    return _IPV4_RE.sub(r"\1.\2.xxx.xxx", text)


def _print(*args, **kwargs):
    masked = [_mask_ipv4(a) if isinstance(a, str) else a for a in args]
    builtins.print(*masked, **kwargs)


# 与 dblp.py 使用同一组请求参数，保证采集到的结构与工具实际调用一致。
QUERY = "graph"
API_URL = f"https://dblp.org/search/publ/api?q={QUERY}&format=json&h=2"
TIMEOUT = 20


def _describe(value, indent=0):
    """递归打印一个 JSON 值的键与类型（值太长则截断），用于人工核对结构。"""
    pad = "  " * indent
    if isinstance(value, dict):
        for k, v in value.items():
            if isinstance(v, (dict, list)):
                _print(f"{pad}{k}: {type(v).__name__}")
                _describe(v, indent + 1)
            else:
                _print(f"{pad}{k}: {type(v).__name__} = {str(v)[:80]}")
    elif isinstance(value, list):
        _print(f"{pad}[list, len={len(value)}]")
        if value:
            _describe(value[0], indent + 1)


def main():
    _print("=" * 60)
    _print(" dblp.org 字段结构采集 ")
    _print("=" * 60)
    _print(f"请求地址：{API_URL}")
    _print("-" * 60)
    req = urllib.request.Request(API_URL, headers={"User-Agent": "UniArticles-dblp-field-probe/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            status = resp.getcode()
            payload = json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        _print(f"[失败] 服务器返回 HTTP {e.code}（网络可达但应用层报错）。")
        try:
            _print(f"错误响应体（前 500 字节）：{e.read(500).decode('utf-8', errors='replace')}")
        except Exception:
            pass
        _print("=> 请稍后或换网络重试；若持续失败请把本输出反馈回来。")
        return
    except Exception as e:  # noqa: BLE001 - 采集脚本，任何异常都如实打印供诊断
        _print(f"[失败] 请求未完成：{type(e).__name__}: {e}")
        _print("=> 这通常是本网络环境对 dblp.org 的拦截（与构建环境现象一致）。")
        _print("   请换一个网络（手机热点 / 其它宽带 / VPN）再跑一次本脚本。")
        return

    _print(f"[成功] HTTP {status}，已解析 JSON。")
    hits = payload.get("result", {}).get("hits", {})
    _print(f"hits @total={hits.get('@total')} @sent={hits.get('@sent')} @first={hits.get('@first')}")
    hitlist = hits.get("hit", [])
    if isinstance(hitlist, dict):
        hitlist = [hitlist]
    _print(f"命中条数：{len(hitlist)}")
    _print("-" * 60)
    _print(" 采集到的字段结构（hit[0] 完整结构）：")
    _print("-" * 60)
    if hitlist:
        _describe(hitlist[0])
        _print("-" * 60)
        _print(" hit[0] 原始 JSON（供逐字段核对）：")
        _print(json.dumps(hitlist[0], ensure_ascii=False, indent=2)[:2500])
    else:
        _print("（无命中，换个关键词或加大 h 再试）")
    _print("=" * 60)
    _print("=> 请把上面「采集到的字段结构」整段复制反馈，用于核对 dblp.py 归一化字段。")
    _print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        _print("\n[已取消] 用户中断。")
        sys.exit(1)
