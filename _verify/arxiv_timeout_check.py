"""
arXiv 超时行为的离线确定性验证脚本
==================================

用途：验证 `src/uniarticles/sources/arxiv.py` 的显式超时在"上游接受连接但
      永不响应"时确实生效——即工具在限定时间内返回归一化的 `_err()`，
      而不是长时间挂起。

背景：2026-09-18 的交付后复验实测 `arxiv_paper_detail_by_id` 与
      `arxiv_latest_paper_list_by_category` 分别挂起 337.8 秒、338.1 秒后才以
      连接超时失败，根因是 `arxiv.Client` 只暴露 page_size / delay_seconds /
      num_retries，**没有任何超时参数**。构建计划书步骤 66 为此加入
      "15 秒请求超时（注入 requests.Session）+ 45 秒 asyncio 兜底"。

      本脚本用本机 TCP 监听冒充上游（只 accept、不回任何数据），把"上游卡住"
      这一条件变成**确定性、可离线复现**的输入：不依赖外网，也不受 arXiv
      当时状态影响。真实网络下复现该故障窗口是不可能的，这正是需要脚本的原因。

怎么用：在项目根目录执行（需 .venv，因为要 import arxiv / mcp）

    .venv\\Scripts\\python.exe _verify\\arxiv_timeout_check.py

判据：三个 arXiv 工具各自满足
  1) 返回归一化形状（ok / source / query / count / items / error 六个键）；
  2) `ok=False` 且 error 含超时关键字；
  3) 耗时小于 25 秒（= 15 秒请求超时 + 余量；对照：故障窗口内为 337.8 秒）。

脚本只做本地回环探测：不改任何文件、不需要 API Key、不访问外网；结束时恢复被
改写的 `arxiv.Client.query_url_format` 并关闭监听端口。输出中的非回环 IPv4
地址会自动脱敏，可安全整段复制回对话。
"""

from __future__ import annotations

import asyncio
import json
import re
import socket
import sys
import threading
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

import arxiv  # noqa: E402
from mcp.server.fastmcp import FastMCP  # noqa: E402

from uniarticles.sources import arxiv as arxiv_source  # noqa: E402

# 耗时预算：请求超时（15 秒）+ 充足余量。故障窗口内的实测值是 337.8 / 338.1 秒，
# 与本预算相差一个数量级，因此这个断言不会因机器快慢而误判。
BUDGET_SECONDS = 25.0

# 三个工具各覆盖一条代码路径：关键词检索、分类浏览、按 ID 详情。
CHECK_CASES = [
    ("arxiv_paper_search_by_query", {"query": 'ti:"Attention Is All You Need"', "max_results": 3}),
    ("arxiv_latest_paper_list_by_category", {"category": "cs.AI", "max_results": 3}),
    ("arxiv_paper_detail_by_id", {"paper_id": "1706.03762"}),
]

_IPV4_RE = re.compile(r"\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b")


def _mask_ipv4(text: str) -> str:
    """把非回环 IPv4 的后两段替换成 xxx.xxx（回环地址保留原样以便读数）。"""

    def repl(match: re.Match) -> str:
        if match.group(1) == "127":
            return match.group(0)
        return f"{match.group(1)}.{match.group(2)}.xxx.xxx"

    return _IPV4_RE.sub(repl, text)


def _print(text: str = "") -> None:
    print(_mask_ipv4(text))


class _StallingServer:
    """TCP 监听：只 accept，从不读取也不回写，用来模拟卡死的上游。"""

    def __init__(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(("127.0.0.1", 0))
        self._sock.listen(8)
        self._sock.settimeout(0.5)
        self.port: int = self._sock.getsockname()[1]
        self._held: list[socket.socket] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._serve, daemon=True)

    def _serve(self) -> None:
        while not self._stop.is_set():
            try:
                conn, _ = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self._held.append(conn)  # 故意既不 recv 也不 send

    def __enter__(self) -> "_StallingServer":
        self._thread.start()
        return self

    def __exit__(self, *exc_info) -> None:
        self._stop.set()
        self._thread.join(timeout=2)
        for conn in self._held:
            try:
                conn.close()
            except OSError:
                pass
        try:
            self._sock.close()
        except OSError:
            pass


def _unwrap(result):
    """把 FastMCP.call_tool 的返回形状归一成 dict（与 tool_availability_check.py 一致）。"""
    if isinstance(result, tuple):
        result = result[0]
    if isinstance(result, list):
        for block in result:
            text = getattr(block, "text", None)
            if text:
                return json.loads(text)
        return {"ok": False, "error": "no text content block"}
    if isinstance(result, dict):
        return result
    return {"ok": False, "error": f"unexpected result type {type(result)!r}"}


async def main() -> int:
    failures: list[str] = []
    original_format = arxiv.Client.query_url_format

    # 检查 0：先确认注入真的装上了——否则后面的"快速失败"可能被误读成超时生效。
    probe = arxiv_source._build_client()  # noqa: SLF001 - 脚本就是来验证这个私有实现的
    injected_get = getattr(getattr(probe, "_session", None), "get", None)
    injection_ok = getattr(injected_get, "__name__", "") == "_get_with_timeout"
    _print("=" * 108)
    _print(f"check 0  build_client injects session timeout : {'PASS' if injection_ok else 'FAIL'}")
    _print(
        f"         constants: request={arxiv_source._ARXIV_REQUEST_TIMEOUT_SECONDS}s "
        f"total={arxiv_source._ARXIV_TOTAL_TIMEOUT_SECONDS}s  budget={BUDGET_SECONDS}s"
    )
    if not injection_ok:
        failures.append("check 0: _build_client() did not install a session timeout")

    with _StallingServer() as stalling:
        arxiv.Client.query_url_format = f"http://127.0.0.1:{stalling.port}/api/query?{{}}"
        try:
            mcp = FastMCP("arxiv-timeout-check")
            arxiv_source.register(mcp)
            _print("=" * 108)
            _print(f"stalling listener at 127.0.0.1:{stalling.port} (accepts, never responds)")
            _print("")
            for tool_name, args in CHECK_CASES:
                started = time.perf_counter()
                try:
                    payload = _unwrap(await mcp.call_tool(tool_name, args))
                except Exception as exc:  # noqa: BLE001 - 异常穿透本身就是失败
                    payload = {
                        "ok": False,
                        "error": f"{type(exc).__name__}: {exc} (raised past the tool layer)",
                    }
                elapsed = time.perf_counter() - started

                raw_err = payload.get("error")
                err = str(raw_err).strip().splitlines()[0] if raw_err else ""
                shape_ok = set(payload) == {"ok", "source", "query", "count", "items", "error"}
                time_ok = elapsed < BUDGET_SECONDS
                norm_err_ok = payload.get("ok") is False and (
                    "timed out" in err.lower() or "timeout" in err.lower()
                )
                passed = shape_ok and time_ok and norm_err_ok

                _print(f"{tool_name:<38} {'PASS' if passed else 'FAIL'}  {elapsed:6.1f}s  ok={payload.get('ok')}")
                _print(f"{'':<38} error: {err[:150]}")
                if not passed:
                    reasons = []
                    if not shape_ok:
                        reasons.append(f"normalized shape broken: {sorted(payload)}")
                    if not time_ok:
                        reasons.append(f"{elapsed:.1f}s exceeded the {BUDGET_SECONDS:.0f}s budget")
                    if not norm_err_ok:
                        reasons.append("did not return a normalized timeout error")
                    failures.append(f"{tool_name}: " + "; ".join(reasons))
        finally:
            arxiv.Client.query_url_format = original_format

    _print("=" * 108)
    if failures:
        _print(f"RESULT: FAIL ({len(failures)} problem(s))")
        for item in failures:
            _print(f"  - {item}")
        return 1
    _print(f"RESULT: PASS — all {len(CHECK_CASES)} arXiv tools failed fast with a normalized timeout error")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
