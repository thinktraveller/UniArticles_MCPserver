"""
排序行为真实探测脚本（v3.3.0 步骤 59）
=====================================

用途：为「三处默认排序修复」（步骤 60）提供编码前的真实依据。

背景：QA-R017 的实测只留下结论、没有留下可复现脚本——
  - Scopus：`sort` 默认 `coverDate` 时，用标题查三篇已知论文命中 0/3；
            改 `sort=relevancy` 后 3/3 命中；`TITLE("...")` 字段查询 top-1 命中。
  - arXiv ：模块硬编码 `sort_by=SubmittedDate`，普通标题查询命中 0/3；
            改用 `ti:"..."` 后命中。
  - PubMed：`_esearch()` 完全没传 `sort`，NCBI ESearch 原始 API 的默认序不是
            网页端的 Best Match；另外带引号的 `"标题"[Title]` 在原始 API 上
            返回 0 条（属 NCBI 自身行为，不是本项目 bug）。

本脚本把 Scopus / PubMed 两段的结论逐条重跑一遍，并把「目标论文出现在第几位」
直接打出来，以免仅凭"命中了/没命中"的二元结论去改代码。

arXiv 分段**不在这里**：本机对 `export.arxiv.org` 的裸 HTTP 请求会间歇性收到
406/超时（arXiv 侧限流），裸请求得到的 406 会被误读成"某种查询语法不被支持"。
arXiv 的探测改用官方 `arxiv` 包（自带退避重试，且与模块真实调用路径一致），
见同目录的 `arxiv_sort_probe.py`。

怎么用：
    在项目根目录打开 PowerShell / CMD，执行：

        python _verify/sort_probe.py

    只会读取项目根目录的 `.env` 拿 API Key（不会回显 Key 本身），
    只做只读的 GET 请求，不改任何文件。

    如果 Scopus 段落报 401/403：说明当前网络的 Key 或订阅额度有问题，
    与代码无关；arXiv / PubMed 两段不依赖 Key，可独立参考。
"""

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = Path(__file__).resolve().parent.parent


def _load_env() -> dict:
    """极简 .env 读取：只取 KEY=VALUE 形式的行，忽略注释与空行。"""
    env = {}
    env_file = ROOT / ".env"
    if not env_file.exists():
        return env
    for line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def _get(url: str, params: dict, headers: dict | None = None, timeout: int = 30):
    """发起一次 GET，返回 (status, body_text)；HTTP 错误也返回状态码而不抛。"""
    full = f"{url}?{urllib.parse.urlencode(params)}"
    # arXiv 在快速连续请求后会短暂返回 406/503（限流，不是查询语法错误）；
    # 实测等待十几秒后即恢复，故对这两个状态码做一次退避重试，避免把限流
    # 误读成"某种查询写法不被支持"。
    for attempt in range(3):
        req = urllib.request.Request(full, headers=headers or {"User-Agent": "uniarticles-sort-probe/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if exc.code in (406, 503) and attempt < 2:
                time.sleep(15)
                continue
            return exc.code, body
        except Exception as exc:  # noqa: BLE001 - 网络层失败也要如实打印
            return None, f"<{type(exc).__name__}: {exc}>"
    return None, "<retries exhausted>"


def _rank_of(targets: list[str], titles: list[str]) -> str:
    """在 titles 里找 targets 中的任意一项（大小写/标点无关的子串匹配）。"""
    norm = [t.lower().replace(":", "").replace("-", " ").strip() for t in titles]
    for target in targets:
        needle = target.lower().replace(":", "").replace("-", " ").strip()
        for idx, title in enumerate(norm):
            if needle in title:
                return f"第 {idx + 1} 位（共 {len(titles)} 条）"
    return f"未命中（前 {len(titles)} 条中无目标）"


def _show_titles(titles: list[str], limit: int = 3) -> None:
    for idx, title in enumerate(titles[:limit]):
        print(f"      [{idx + 1}] {title[:100]}")


# --------------------------------------------------------------------------- #
# Scopus
# --------------------------------------------------------------------------- #
def probe_scopus(env: dict) -> None:
    print("\n=== Scopus（排序参数 / 字段语法）===")
    api_key = env.get("ELSEVIER_API_KEY") or env.get("SCOPUS_API_KEY")
    if not api_key:
        print("  [跳过] .env 中既无 ELSEVIER_API_KEY 也无 SCOPUS_API_KEY")
        return
    headers = {"X-ELS-APIKey": api_key, "Accept": "application/json",
               "User-Agent": "uniarticles-sort-probe/1.0"}

    # 目标：AlphaFold 论文（Nature 2021，DOI 10.1038/s41586-021-03819-2）
    target_title = "Highly accurate protein structure prediction with AlphaFold"
    target_substrings = ["Highly accurate protein structure prediction with AlphaFold"]
    raw = f'"{target_title}"'
    fielded = f'TITLE("{target_title}")'
    taxk = f'TITLE-ABS-KEY("{target_title}")'

    configs = [
        ("裸标题 + sort=coverDate（当前默认）", raw, "coverDate"),
        ("裸标题 + sort=relevancy", raw, "relevancy"),
        ("TITLE(...) + sort=coverDate", fielded, "coverDate"),
        ("TITLE(...) + sort=relevancy", fielded, "relevancy"),
        ("TITLE-ABS-KEY(...) + sort=relevancy（对照）", taxk, "relevancy"),
    ]

    for label, query, sort in configs:
        params = {"query": query, "count": "10", "sort": sort, "view": "STANDARD"}
        status, body = _get("https://api.elsevier.com/content/search/scopus", params, headers)
        print(f"\n  [{label}]  status={status}")
        if status != 200:
            print(f"      响应片段：{body[:200]}")
            continue
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            print(f"      非 JSON 响应：{body[:200]}")
            continue
        results = payload.get("search-results", {})
        entries = results.get("entry", []) or []
        # Scopus 无结果时会返回一条 opensearch:totalResults=0 且 entry 内含 error 项
        entries = [e for e in entries if "error" not in e]
        titles = [(e.get("dc:title") or "") for e in entries]
        total = results.get("opensearch:totalResults", "?")
        print(f"      totalResults={total}，取回 {len(titles)} 条")
        _show_titles(titles)
        print(f"      → 目标论文：{_rank_of(target_substrings, titles)}")
        time.sleep(0.4)


# --------------------------------------------------------------------------- #
# PubMed (NCBI ESearch)
# --------------------------------------------------------------------------- #
def probe_pubmed(env: dict) -> None:
    print("\n=== PubMed / NCBI ESearch（sort 取值）===")
    api = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    base = {"tool": "uniarticles-sort-probe", "email": "sort-probe@example.com",
            "db": "pubmed", "retmode": "json", "retmax": "10"}
    if env.get("NCBI_API_KEY"):
        base["api_key"] = env["NCBI_API_KEY"]

    target_pmid = "34265844"  # AlphaFold 论文
    title = "Highly accurate protein structure prediction with AlphaFold"

    configs = [
        ("无引号 [Title] + 不传 sort（当前默认）", f"{title}[Title]", None),
        ("无引号 [Title] + sort=relevance", f"{title}[Title]", "relevance"),
        ("带引号 [Title] + 不传 sort（复现 0 条现象）", f'"{title}"[Title]', None),
        ("带引号 [Title] + sort=relevance", f'"{title}"[Title]', "relevance"),
    ]

    for label, term, sort in configs:
        params = dict(base)
        params["term"] = term
        if sort:
            params["sort"] = sort
        status, body = _get(api, params)
        print(f"\n  [{label}]  status={status}")
        if status != 200:
            print(f"      响应片段：{body[:200]}")
            continue
        try:
            result = json.loads(body).get("esearchresult", {})
        except json.JSONDecodeError:
            print(f"      非 JSON 响应：{body[:200]}")
            continue
        ids = result.get("idlist", []) or []
        print(f"      count={result.get('count')}，idlist={ids[:5]}")
        if target_pmid in ids:
            print(f"      → 目标 PMID {target_pmid}：第 {ids.index(target_pmid) + 1} 位")
        else:
            print(f"      → 目标 PMID {target_pmid}：不在前 {len(ids)} 条内")
        time.sleep(0.5)


def main() -> None:
    print("UniArticles v3.3.0 排序修复前置探测（步骤 59）")
    print(f"项目根目录：{ROOT}")
    env = _load_env()
    print(f".env 中读取到的配置键：{sorted(env.keys())}")
    # 可选：只跑其中一段，便于某一段网络波动时单独重试
    #   python _verify/sort_probe.py arxiv
    wanted = {a.lower() for a in sys.argv[1:]} or {"scopus", "arxiv", "pubmed"}
    if "scopus" in wanted:
        probe_scopus(env)
    if "pubmed" in wanted:
        probe_pubmed(env)
    print("\n探测结束。请把以上输出整体回传，作为步骤 60 的编码依据。")


if __name__ == "__main__":
    main()
