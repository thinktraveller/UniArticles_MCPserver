"""
NCBI E-utilities 字段结构采集脚本（编码前置探测，非连通性诊断）
================================================================

用途：真实调用 NCBI Entrez E-utilities 的 5 个端点，**完整打印各端点返回的
      真实结构**（ESearch/ESummary/ELink 为 JSON，EFetch 为 XML），用于核对/
      确定 UniArticles v3.1.0 PubMed 数据源（`src/uniarticles/sources/pubmed.py`）
      的归一化字段映射与 XML 解析路径。

对应 project-docs/project-plan.md 步骤 43、project-docs/goal.md QA-R014/QA-R015
以及 QA-R013 通用流程约束（探测脚本必须产出到 `_verify/` 供用户在自己的网络
环境下独立验证，不得仅凭构建环境单次结果下结论）。

覆盖的 5 个真实请求（统一 base：https://eutils.ncbi.nlm.nih.gov/entrez/eutils/）：
    1. esearch.fcgi   —— 检索关键词，取回 PMID 列表（idlist）
    2. efetch.fcgi    —— 按 PMID 拉取完整 XML，逐层打印标签树 + 完整样例
    3. esummary.fcgi  —— 轻量元数据（含 PMCID/PII/期刊全名/发表状态历史等）
    4. elink.fcgi (neighbor)          —— 相关文献列表
    5. elink.fcgi (dbfrom=pubmed&db=pmc) —— PMC 全文/引用关联

可选：若本机 shell 已设置环境变量 NCBI_API_KEY，脚本会对 ESearch 分别做一次
      带 key / 不带 key 的调用，比对可观察差异（NCBI 通常不在响应体中标注实际
      生效的限速值，若观测不到差异脚本会如实说明，不编造结论）。

怎么用：
      在项目根目录打开 PowerShell / CMD，执行：

          python _verify/pubmed_eutils_field_probe.py

      然后把整段输出复制反馈即可。

本脚本只读、不改任何文件、仅用 Python 标准库（urllib / xml.etree / json），
不依赖项目自身代码或任何第三方包，可独立运行。
"""

import builtins
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# IPv4 脱敏（与 dblp 探测脚本一致）：打印前把 IP 后两段打码，避免复制输出时外泄本机 IP。
_IPV4_RE = re.compile(r"\b(\d{1,3})\.(\d{1,3})\.\d{1,3}\.\d{1,3}\b")


def _mask_ipv4(text):
    return _IPV4_RE.sub(r"\1.\2.xxx.xxx", text)


def _print(*args, **kwargs):
    masked = [_mask_ipv4(a) if isinstance(a, str) else a for a in args]
    builtins.print(*masked, **kwargs)


BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
TIMEOUT = 30
API_KEY = os.getenv("NCBI_API_KEY")  # 可选；未设置则跳过带 key 的对照
UA = "UniArticles-pubmed-field-probe/1.0"

# 关键词：用一个结构化摘要（BACKGROUND/METHODS/...）常见的临床/生物医学主题，
# 更可能命中"结构化 AbstractText 分段"这一陷阱，供步骤 45 解析逻辑参考。
SEARCH_TERM = "CRISPR gene editing"


def _build_url(endpoint, params, with_key=True):
    p = dict(params)
    p.setdefault("tool", "uniarticles-mcp")
    p.setdefault("email", "wangzh685@mail2.sysu.edu.cn")
    if with_key and API_KEY:
        p["api_key"] = API_KEY
    return f"{BASE}{endpoint}?{urllib.parse.urlencode(p)}"


def _fetch(url):
    """返回 (status, text) 或抛出异常。请求前打印脱敏后的 URL（api_key 打码）。"""
    shown = re.sub(r"api_key=[^&]+", "api_key=***", url)
    _print(f"  GET {shown}")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.getcode(), resp.read().decode("utf-8", errors="replace")


def _describe_json(value, indent=0, max_depth=6):
    pad = "  " * indent
    if indent > max_depth:
        _print(f"{pad}...(达到最大深度，省略)")
        return
    if isinstance(value, dict):
        for k, v in value.items():
            if isinstance(v, (dict, list)):
                _print(f"{pad}{k}: {type(v).__name__}")
                _describe_json(v, indent + 1, max_depth)
            else:
                _print(f"{pad}{k}: {type(v).__name__} = {str(v)[:100]}")
    elif isinstance(value, list):
        _print(f"{pad}[list, len={len(value)}]")
        if value:
            _describe_json(value[0], indent + 1, max_depth)


def _describe_xml(el, indent=0, max_depth=8):
    """逐层打印 XML 标签树：标签名、属性、直接文本（截断）、子标签计数。"""
    pad = "  " * indent
    if indent > max_depth:
        _print(f"{pad}...(达到最大深度，省略)")
        return
    attrs = " ".join(f'{k}="{v}"' for k, v in el.attrib.items())
    direct_text = (el.text or "").strip()
    text_note = f"  text={direct_text[:60]!r}" if direct_text else ""
    _print(f"{pad}<{el.tag}{(' ' + attrs) if attrs else ''}>{text_note}")
    # 统计同名子标签出现次数，帮助识别列表型标签
    child_tags = {}
    for c in el:
        child_tags[c.tag] = child_tags.get(c.tag, 0) + 1
    seen = set()
    for c in el:
        if child_tags[c.tag] > 1 and c.tag in seen:
            continue  # 同名重复标签只递归展开第一个，其余仅计数提示
        if child_tags[c.tag] > 1 and c.tag not in seen:
            _print(f"{pad}  # <{c.tag}> 出现 {child_tags[c.tag]} 次（列表型，仅展开首个）")
        seen.add(c.tag)
        _describe_xml(c, indent + 1, max_depth)


def probe_esearch():
    _print("=" * 70)
    _print(" [1/5] ESearch —— 检索 PMID 列表")
    _print("=" * 70)
    idlist = []
    # 不带 key
    try:
        url = _build_url("esearch.fcgi", {"db": "pubmed", "term": SEARCH_TERM, "retmax": 5, "retmode": "json"}, with_key=False)
        status, text = _fetch(url)
        payload = json.loads(text)
        idlist = payload.get("esearchresult", {}).get("idlist", []) or []
        _print(f"  [不带 key] HTTP {status}，idlist={idlist}")
        _print("  结构：")
        _describe_json(payload.get("esearchresult", {}), indent=2, max_depth=2)
    except Exception as e:  # noqa: BLE001
        _print(f"  [不带 key] 失败：{type(e).__name__}: {e}")
    # 带 key 对照
    if API_KEY:
        try:
            time.sleep(0.4)
            url = _build_url("esearch.fcgi", {"db": "pubmed", "term": SEARCH_TERM, "retmax": 5, "retmode": "json"}, with_key=True)
            status, text = _fetch(url)
            payload = json.loads(text)
            idlist2 = payload.get("esearchresult", {}).get("idlist", []) or []
            _print(f"  [带 key ] HTTP {status}，idlist={idlist2}")
            _print("  => 两次调用均返回 200；NCBI 不在响应体中标注实际限速值，")
            _print("     故无法从响应体直接验证 3→10 请求/秒的差异，仅确认带 key 调用可用。")
            if not idlist:
                idlist = idlist2
        except Exception as e:  # noqa: BLE001
            _print(f"  [带 key ] 失败：{type(e).__name__}: {e}")
    else:
        _print("  [提示] 未设置环境变量 NCBI_API_KEY，跳过带 key 对照。")
    return idlist


def probe_efetch(pmids):
    _print("")
    _print("=" * 70)
    _print(" [2/5] EFetch —— 完整 XML 结构（步骤 45 解析逻辑的直接依据）")
    _print("=" * 70)
    if not pmids:
        _print("  （无可用 PMID，跳过）")
        return
    try:
        time.sleep(0.4)
        url = _build_url("efetch.fcgi", {"db": "pubmed", "id": ",".join(pmids), "rettype": "abstract", "retmode": "xml"})
        status, text = _fetch(url)
        _print(f"  HTTP {status}，XML 长度 {len(text)} 字节")
        root = ET.fromstring(text)
        articles = root.findall(".//PubmedArticle")
        _print(f"  .//PubmedArticle 命中 {len(articles)} 篇")
        # 关键字段陷阱检查：逐篇统计列表型/结构化标签是否存在
        _print("  -" * 33)
        _print("  各篇关键字段边界情况检查（标签是否存在 / 结构化摘要 / 作者形态）：")
        for i, art in enumerate(articles):
            pmid = art.findtext(".//PMID")
            abstract_texts = art.findall(".//Abstract/AbstractText")
            labels = [a.get("Label") for a in abstract_texts]
            authors = art.findall(".//AuthorList/Author")
            collective = art.findall(".//AuthorList/Author/CollectiveName")
            keywords = art.findall(".//KeywordList/Keyword")
            has_authorlist = art.find(".//AuthorList") is not None
            has_keywordlist = art.find(".//KeywordList") is not None
            doi = art.find(".//ArticleIdList/ArticleId[@IdType='doi']")
            title_el = art.find(".//ArticleTitle")
            title_itertext = "".join(title_el.itertext()) if title_el is not None else None
            _print(f"    [{i}] PMID={pmid}")
            _print(f"        ArticleTitle(.itertext 拼接)={(title_itertext or '')[:90]!r}")
            _print(f"        AbstractText 分段数={len(abstract_texts)} Label={labels}")
            _print(f"        AuthorList存在={has_authorlist} Author数={len(authors)} CollectiveName数={len(collective)}")
            _print(f"        KeywordList存在={has_keywordlist} Keyword数={len(keywords)}")
            _print(f"        doi={doi.text if doi is not None else None}")
        _print("  -" * 33)
        _print("  第 1 篇 PubmedArticle 完整标签树：")
        _describe_xml(articles[0])
        _print("  -" * 33)
        _print("  第 1 篇 PubmedArticle 原始 XML（前 4000 字节，供逐字段核对）：")
        first_raw = ET.tostring(articles[0], encoding="unicode")
        _print(first_raw[:4000])
    except Exception as e:  # noqa: BLE001
        _print(f"  失败：{type(e).__name__}: {e}")


def probe_esummary(pmids):
    _print("")
    _print("=" * 70)
    _print(" [3/5] ESummary —— 轻量元数据 JSON（核对 pmcid/pii/期刊全名/发表状态）")
    _print("=" * 70)
    if not pmids:
        _print("  （无可用 PMID，跳过）")
        return
    try:
        time.sleep(0.4)
        url = _build_url("esummary.fcgi", {"db": "pubmed", "id": ",".join(pmids), "retmode": "json"})
        status, text = _fetch(url)
        payload = json.loads(text)
        result = payload.get("result", {})
        uids = result.get("uids", []) or []
        _print(f"  HTTP {status}，result.uids={uids}")
        if uids:
            first = result.get(uids[0], {})
            _print(f"  第 1 个 uid（{uids[0]}）完整结构：")
            _describe_json(first, indent=2, max_depth=4)
            # 重点字段直读
            _print("  -" * 33)
            _print("  重点字段直读（若不存在则为 None）：")
            for key in ("pubdate", "epubdate", "source", "fulljournalname", "elocationid",
                        "pubstatus", "articleids", "history", "pmcid"):
                _print(f"    {key} = {str(first.get(key))[:120]}")
            aids = first.get("articleids", [])
            if aids:
                _print(f"    articleids 明细（含 pmcid/doi/pii 常在此处）：")
                for a in aids:
                    _print(f"      - idtype={a.get('idtype')!r} value={a.get('value')!r}")
    except Exception as e:  # noqa: BLE001
        _print(f"  失败：{type(e).__name__}: {e}")


def probe_elink_neighbor(pmid):
    _print("")
    _print("=" * 70)
    _print(" [4/5] ELink neighbor —— 相关文献列表（含 score?）")
    _print("=" * 70)
    if not pmid:
        _print("  （无可用 PMID，跳过）")
        return
    try:
        time.sleep(0.4)
        url = _build_url("elink.fcgi", {"dbfrom": "pubmed", "db": "pubmed", "id": pmid, "cmd": "neighbor", "retmode": "json"})
        status, text = _fetch(url)
        payload = json.loads(text)
        linksets = payload.get("linksets", []) or []
        _print(f"  HTTP {status}，linksets 数={len(linksets)}")
        if linksets:
            ls0 = linksets[0]
            _print("  linksets[0] 结构：")
            _describe_json(ls0, indent=2, max_depth=4)
            dbs = ls0.get("linksetdbs", []) or []
            for db in dbs:
                links = db.get("links", []) or []
                _print(f"  linksetdb linkname={db.get('linkname')!r} dbto={db.get('dbto')!r} links数={len(links)}")
                if links:
                    _print(f"    links[0] 类型={type(links[0]).__name__} 值样例={str(links[0])[:120]}")
                    _print(f"    => links 元素是否带 score/权重：{'是' if isinstance(links[0], dict) else '否（纯 id 列表）'}")
    except Exception as e:  # noqa: BLE001
        _print(f"  失败：{type(e).__name__}: {e}")


def probe_elink_pmc(pmid):
    _print("")
    _print("=" * 70)
    _print(" [5/5] ELink PMC —— PMC 全文/引用关联（区分'自身全文' vs '被引用'）")
    _print("=" * 70)
    if not pmid:
        _print("  （无可用 PMID，跳过）")
        return
    try:
        time.sleep(0.4)
        url = _build_url("elink.fcgi", {"dbfrom": "pubmed", "db": "pmc", "id": pmid, "retmode": "json"})
        status, text = _fetch(url)
        payload = json.loads(text)
        linksets = payload.get("linksets", []) or []
        _print(f"  HTTP {status}，linksets 数={len(linksets)}")
        if linksets:
            ls0 = linksets[0]
            dbs = ls0.get("linksetdbs", []) or []
            _print(f"  linksetdbs 数={len(dbs)}——每个 linkname 代表一种关联性质：")
            for db in dbs:
                links = db.get("links", []) or []
                _print(f"    linkname={db.get('linkname')!r} dbto={db.get('dbto')!r} links数={len(links)} 样例={str(links[:3])[:120]}")
            _print("  => 请据实际 linkname 判断哪个是'该文献自身的 PMC 全文'、")
            _print("     哪个是'引用/关联它的其他 PMC 文章'（步骤 48 分组归一化依据）。")
            _print("  linksets[0] 完整结构：")
            _describe_json(ls0, indent=2, max_depth=4)
    except Exception as e:  # noqa: BLE001
        _print(f"  失败：{type(e).__name__}: {e}")


def main():
    _print("#" * 70)
    _print(" NCBI E-utilities 字段结构采集（UniArticles v3.1.0 步骤 43）")
    _print(f" NCBI_API_KEY 环境变量：{'已设置' if API_KEY else '未设置'}")
    _print("#" * 70)
    try:
        idlist = probe_esearch()
    except Exception as e:  # noqa: BLE001
        _print(f"[致命] ESearch 阶段异常，无法取得样本 PMID：{type(e).__name__}: {e}")
        _print("=> 若为网络类失败（超时/DNS/拦截），比照 dblp 先例：不据此判定端点不可用，")
        _print("   请换网络重跑，或把本输出反馈回来。")
        return
    # 取 2 个样本 PMID 做 EFetch/ESummary 交叉验证（避免单一样本特殊性带偏），
    # ELink 用第 1 个 PMID。
    sample_pmids = idlist[:2] if len(idlist) >= 2 else idlist[:1]
    first_pmid = idlist[0] if idlist else None
    _print("")
    _print(f"选用样本 PMID：EFetch/ESummary={sample_pmids}，ELink={first_pmid}")
    probe_efetch(sample_pmids)
    probe_esummary(sample_pmids)
    probe_elink_neighbor(first_pmid)
    probe_elink_pmc(first_pmid)
    _print("")
    _print("#" * 70)
    _print("=> 请把以上完整输出整段复制反馈，用于最终核对 pubmed.py 的字段映射与 XML 解析路径。")
    _print("#" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        _print("\n[已取消] 用户中断。")
        sys.exit(1)
