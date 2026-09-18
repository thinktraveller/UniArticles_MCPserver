"""
arXiv 排序行为探测（v3.3.0 步骤 59 的 arXiv 分段）
==================================================

为什么不走裸 HTTP：本机对 `export.arxiv.org` 的裸请求会间歇性收到 HTTP 406
或连接超时（arXiv 侧的限流），而项目实际调用路径是官方 `arxiv` 包——该包内置
指数退避重试，能在限流下最终拿到结果。因此本脚本直接用 `arxiv` 包复现模块
真实的请求方式，结论对步骤 60 更有说服力。

用法（在项目根目录）：

    .venv\\Scripts\\python.exe _verify/arxiv_sort_probe.py

只读探测，不改任何文件，不需要 API Key。每次请求之间会等待，整轮可能需要
数分钟——arXiv 限流严重时这是正常的，不要中断。
"""

import sys

import arxiv

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

TARGET = "attention is all you need"


def _norm(text: str) -> str:
    return text.lower().replace(":", "").replace("-", " ").strip()


def probe(label: str, query: str, sort_by) -> None:
    client = arxiv.Client()
    search = arxiv.Search(query=query, max_results=10, sort_by=sort_by)
    print(f"\n[{label}]")
    print(f"    query={query!r}  sort_by={sort_by}")
    try:
        papers = list(client.results(search))
    except Exception as exc:  # noqa: BLE001
        print(f"    FAILED: {type(exc).__name__}: {exc}")
        return
    titles = [p.title for p in papers]
    ranks = [i + 1 for i, t in enumerate(titles) if TARGET in _norm(t)]
    for idx, title in enumerate(titles[:3]):
        print(f"    [{idx + 1}] {title[:90]}")
    print(f"    → 目标论文（Attention Is All You Need）："
          f"{'第 ' + str(ranks[0]) + ' 位' if ranks else '未命中（前 %d 条内无目标）' % len(titles)}")


CASES = [
    ("当前实现：all: 查询 + SubmittedDate", "all:Attention Is All You Need",
     arxiv.SortCriterion.SubmittedDate),
    ("候选修复：all: 查询 + Relevance", "all:Attention Is All You Need",
     arxiv.SortCriterion.Relevance),
    ("候选修复：ti: 字段查询 + Relevance", 'ti:"Attention Is All You Need"',
     arxiv.SortCriterion.Relevance),
]

for label, query, sort_by in CASES:
    probe(label, query, sort_by)
