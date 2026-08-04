import httpx
from mcp.server.fastmcp import FastMCP

from ..config import settings


BASE_URL = "https://api.elsevier.com/"


def _ok(query: str, items: list[dict]) -> dict:
    return {
        "ok": True,
        "source": "scopus",
        "query": query,
        "count": len(items),
        "items": items,
        "error": None,
    }


def _err(query: str, message: str) -> dict:
    return {
        "ok": False,
        "source": "scopus",
        "query": query,
        "count": 0,
        "items": [],
        "error": message,
    }


def _as_list(value) -> list:
    """Elsevier returns a single object (dict) when there is one element and a
    list when there are several; coerce to a list for uniform iteration."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _author_name(author: dict) -> str | None:
    """Extract a readable author name from a Scopus abstract author object,
    tolerating the several shapes Elsevier uses."""
    if not isinstance(author, dict):
        return None
    for key in ("ce:indexed-name", "$"):
        name = author.get(key)
        if name:
            return name
    preferred = author.get("preferred-name")
    if isinstance(preferred, dict):
        for key in ("ce:indexed-name", "$"):
            name = preferred.get(key)
            if name:
                return name
    surname = author.get("ce:surname")
    given = author.get("ce:given-name")
    if surname or given:
        return " ".join(p for p in (surname, given) if p)
    return None


def _get_headers() -> dict[str, str]:
    api_key = settings.elsevier_api_key
    if not api_key:
        raise ValueError("ELSEVIER_API_KEY is required")
    headers = {
        "X-ELS-APIKey": api_key,
        "Accept": "application/json",
        "User-Agent": "UniArticlesMCP/0.1.0",
    }
    if settings.elsevier_insttoken:
        headers["X-ELS-Insttoken"] = settings.elsevier_insttoken
    return headers


async def _search_scopus(query: str, count: int, sort: str, view: str) -> dict:
    headers = _get_headers()
    params = {
        "query": query,
        "count": count,
        "sort": sort,
        "view": view,
    }
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(f"{BASE_URL}content/search/scopus", params=params)
        response.raise_for_status()
        payload = response.json()
    entries = payload.get("search-results", {}).get("entry", [])
    normalized = []
    for entry in entries:
        normalized.append(
            {
                "title": entry.get("dc:title"),
                "eid": entry.get("eid"),
                "doi": entry.get("prism:doi"),
                "coverDate": entry.get("prism:coverDate"),
                "publicationName": entry.get("prism:publicationName"),
                "creator": entry.get("dc:creator"),
                "citedbyCount": entry.get("citedby-count"),
                "openaccess": entry.get("openaccess"),
            }
        )
    return _ok(query=query, items=normalized)


async def _get_abstract(eid: str, view: str) -> dict:
    headers = _get_headers()
    url = f"{BASE_URL}content/abstract/eid/{eid}"
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(url, params={"view": view})
        response.raise_for_status()
        payload = response.json()
    # Field structure confirmed by real probe (step 14, view=META): root
    # `abstracts-retrieval-response` has `coredata` (dict) + `affiliation` (list);
    # authors live under `coredata.dc:creator.author`. META does not include the
    # abstract body (`dc:description`); higher views (FULL) may add it.
    response_root = payload.get("abstracts-retrieval-response", {}) or {}
    coredata = response_root.get("coredata", {}) or {}

    creator = coredata.get("dc:creator")
    author_objs: list = []
    if isinstance(creator, dict):
        author_objs = _as_list(creator.get("author"))
    elif isinstance(creator, list):
        author_objs = creator
    authors = [name for name in (_author_name(a) for a in author_objs) if name]

    affiliations = [
        {
            "name": aff.get("affilname"),
            "city": aff.get("affiliation-city"),
            "country": aff.get("affiliation-country"),
        }
        for aff in _as_list(response_root.get("affiliation"))
        if isinstance(aff, dict)
    ]

    # `dc:description` only present in richer views; include it when available.
    abstract_text = coredata.get("dc:description")

    normalized = {
        "title": coredata.get("dc:title"),
        "eid": coredata.get("eid"),
        "doi": coredata.get("prism:doi"),
        "scopus_id": coredata.get("dc:identifier"),
        "publication_name": coredata.get("prism:publicationName"),
        "issn": coredata.get("prism:issn"),
        "aggregation_type": coredata.get("prism:aggregationType"),
        "document_type": coredata.get("subtypeDescription"),
        "cover_date": coredata.get("prism:coverDate"),
        "volume": coredata.get("prism:volume"),
        "issue": coredata.get("prism:issueIdentifier"),
        "page_range": coredata.get("prism:pageRange"),
        "cited_by_count": coredata.get("citedby-count"),
        "publisher": coredata.get("dc:publisher"),
        "openaccess": coredata.get("openaccess"),
        "abstract": abstract_text,
        "authors": authors,
        "affiliations": affiliations,
        "scopus_url": coredata.get("prism:url"),
    }
    return _ok(query=eid, items=[normalized])


async def _get_serial_title(issn: str, view: str) -> dict:
    headers = _get_headers()
    url = f"{BASE_URL}content/serial/title/issn/{issn}"
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(url, params={"view": view})
        response.raise_for_status()
        payload = response.json()
    entries = payload.get("serial-metadata-response", {}).get("entry", []) or []
    normalized = []
    for entry in entries:
        homepage = None
        for link in entry.get("link", []) or []:
            if link.get("@ref") == "homepage":
                homepage = link.get("@href") or None
                break
        subject_areas = [
            {
                "code": area.get("@code"),
                "abbrev": area.get("@abbrev"),
                "name": area.get("$"),
            }
            for area in entry.get("subject-area", []) or []
        ]
        normalized.append(
            {
                "title": entry.get("dc:title"),
                "publisher": entry.get("dc:publisher"),
                "issn": entry.get("prism:issn"),
                "eissn": entry.get("prism:eIssn"),
                "aggregation_type": entry.get("prism:aggregationType"),
                "openaccess": entry.get("openaccess"),
                "openaccess_type": entry.get("openaccessType"),
                "coverage_start_year": entry.get("coverageStartYear"),
                "coverage_end_year": entry.get("coverageEndYear"),
                "subject_areas": subject_areas,
                "homepage_url": homepage,
                "source_id": entry.get("source-id"),
                "scopus_url": entry.get("prism:url"),
            }
        )
    return _ok(query=issn, items=normalized)


def _serial_metrics(metric_list, wrapper_key: str, metric_key: str) -> list[dict]:
    """Extract Scopus serial metrics (SNIP/SJR) into a flat [{year, value}] list.
    Elsevier shape: {"SNIP": [{"@year": "2014", "$": "0.5"}, ...]} (single -> dict)."""
    if not isinstance(metric_list, dict):
        return []
    return [
        {"year": m.get("@year"), "value": m.get("$")}
        for m in _as_list(metric_list.get(metric_key))
        if isinstance(m, dict)
    ]


def _normalize_serial_entry(entry: dict) -> dict:
    """Shared serial-title entry normalizer (used by search-by-criteria).
    Superset of the by-ISSN normalization, additionally exposing the SNIP/SJR
    journal metric lists that the endpoint returns (confirmed by step 21 probe)."""
    homepage = None
    for link in entry.get("link", []) or []:
        if link.get("@ref") == "homepage":
            homepage = link.get("@href") or None
            break
    subject_areas = [
        {
            "code": area.get("@code"),
            "abbrev": area.get("@abbrev"),
            "name": area.get("$"),
        }
        for area in _as_list(entry.get("subject-area"))
        if isinstance(area, dict)
    ]
    return {
        "title": entry.get("dc:title"),
        "publisher": entry.get("dc:publisher"),
        "issn": entry.get("prism:issn"),
        "eissn": entry.get("prism:eIssn"),
        "aggregation_type": entry.get("prism:aggregationType"),
        "openaccess": entry.get("openaccess"),
        "openaccess_type": entry.get("openaccessType"),
        "coverage_start_year": entry.get("coverageStartYear"),
        "coverage_end_year": entry.get("coverageEndYear"),
        "subject_areas": subject_areas,
        "homepage_url": homepage,
        "source_id": entry.get("source-id"),
        "scopus_url": entry.get("prism:url"),
        "snip_list": _serial_metrics(entry.get("SNIPList"), "SNIPList", "SNIP"),
        "sjr_list": _serial_metrics(entry.get("SJRList"), "SJRList", "SJR"),
    }


async def _search_serial_title(
    title: str | None,
    issn: str | None,
    pub: str | None,
    subj: str | None,
    content: str | None,
    date: str | None,
    oa: str | None,
    start: int | None,
    count: int | None,
    view: str,
) -> dict:
    headers = _get_headers()
    params = {
        k: v
        for k, v in {
            "title": title,
            "issn": issn,
            "pub": pub,
            "subj": subj,
            "content": content,
            "date": date,
            "oa": oa,
            "start": start,
            "count": count,
            "view": view,
        }.items()
        if v is not None
    }
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(f"{BASE_URL}content/serial/title", params=params)
        response.raise_for_status()
        payload = response.json()
    # Real-probe (step 21) shapes: matches -> `serial-metadata-response.entry[]`;
    # no-match -> HTTP 200 with `serial-metadata-response.error="No results found"`
    # and NO `entry` key. `.get("entry", [])` yields [] for the latter -> ok+empty.
    entries = payload.get("serial-metadata-response", {}).get("entry", []) or []
    query_desc = ", ".join(f"{k}={v}" for k, v in params.items() if k not in ("start", "count", "view")) or "(browse)"
    normalized = [_normalize_serial_entry(e) for e in entries if isinstance(e, dict)]
    return _ok(query=query_desc, items=normalized)


async def _lookup_subject_classification(
    source: str,
    description: str | None,
    detail: str | None,
    code: str | None,
    abbrev: str | None,
    field: str | None,
) -> dict:
    headers = _get_headers()
    params = {
        k: v
        for k, v in {
            "description": description,
            "detail": detail,
            "code": code,
            "abbrev": abbrev,
            "field": field,
        }.items()
        if v is not None
    }
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(f"{BASE_URL}content/subject/{source}", params=params)
        response.raise_for_status()
        payload = response.json()
    # Real-probe (step 21): root `subject-classifications.subject-classification`
    # is a single dict when one match, a list when several -> coerce with _as_list.
    # scopus items: code/description/detail/abbrev. scidir items add `parentCode`
    # (hierarchy) -> exposed as parent_code, None for scopus. Single normalizer covers both.
    raw = payload.get("subject-classifications", {}) or {}
    items = _as_list(raw.get("subject-classification"))
    normalized = [
        {
            "code": item.get("code"),
            "description": item.get("description"),
            "detail": item.get("detail"),
            "abbrev": item.get("abbrev"),
            "parent_code": item.get("parentCode"),
        }
        for item in items
        if isinstance(item, dict)
    ]
    return _ok(query=source, items=normalized)


async def _get_quota() -> dict:
    headers = _get_headers()
    # Use search endpoint for quota check
    url = f"{BASE_URL}content/search/scopus?query=test&count=1"
    async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
        response = await client.get(url)
        # Even if it fails (e.g. 429), headers might be present.
        # But for simplicity, we assume we can at least reach the server.
        quota = {
            "limit": response.headers.get("X-RateLimit-Limit"),
            "remaining": response.headers.get("X-RateLimit-Remaining"),
            "reset": response.headers.get("X-RateLimit-Reset"),
            "status": response.status_code,
        }
        return _ok(query="quota", items=[quota])


def register(server: FastMCP) -> None:
    @server.tool()
    async def scopus_document_search_by_query(query: str, count: int = 5, sort: str = "coverDate", view: str = "STANDARD") -> dict:
        """Search for documents in Scopus using a query string."""
        normalized_query = query.strip()
        bounded = max(1, min(count, 25))
        if not normalized_query:
            return _err(query=query, message="query must not be empty")
        try:
            return await _search_scopus(query=normalized_query, count=bounded, sort=sort, view=view)
        except Exception as exc:
            return _err(query=normalized_query, message=str(exc))

    @server.tool()
    async def scopus_abstract_detail_by_eid(eid: str, view: str = "META") -> dict:
        """Get detailed abstract information for a Scopus document (by EID).
        Returns a normalized record (title, authors, affiliations, journal,
        identifiers, etc.). Default view is META (unrestricted); the abstract
        body is only populated under richer views such as FULL/META_ABS if your
        subscription supports them.
        """
        normalized_eid = eid.strip()
        if not normalized_eid:
            return _err(query=eid, message="eid must not be empty")
        try:
            return await _get_abstract(eid=normalized_eid, view=view)
        except Exception as exc:
            return _err(query=normalized_eid, message=str(exc))

    @server.tool()
    async def scopus_serial_title_by_issn(issn: str, view: str = "STANDARD") -> dict:
        """Get journal/serial metadata (title, publisher, Open Access status, coverage
        years, subject areas, homepage) by ISSN.
        Default view is STANDARD (verified working with a basic subscription tier).
        """
        normalized_issn = issn.strip()
        if not normalized_issn:
            return _err(query=issn, message="issn must not be empty")
        try:
            return await _get_serial_title(issn=normalized_issn, view=view)
        except Exception as exc:
            return _err(query=normalized_issn, message=str(exc))

    @server.tool()
    async def scopus_api_usage_status() -> dict:
        """Check current Elsevier API usage/rate-limit status (via Scopus endpoint)."""
        try:
            return await _get_quota()
        except Exception as exc:
            return _err(query="quota", message=str(exc))

    @server.tool()
    async def scopus_serial_title_search_by_criteria(
        title: str | None = None,
        issn: str | None = None,
        pub: str | None = None,
        subj: str | None = None,
        content: str | None = None,
        date: str | None = None,
        oa: str | None = None,
        start: int | None = None,
        count: int | None = None,
        view: str = "STANDARD",
    ) -> dict:
        """Search journals/serials by multiple optional criteria (no ISSN required).
        Sibling of scopus_serial_title_by_issn, which looks up ONE journal by exact ISSN;
        this tool searches across journals and returns a list, including SNIP/SJR metrics.
        Optional filters: title (substring match), issn, pub (publisher), subj (subject
        ABBREVIATION such as COMP/CHEM, NOT the numeric code), content
        (journal/tradejournal/conferenceproceeding/bookseries), date (year), oa
        (all/full/partial/none), start (page offset), count (page size, max 200).
        view defaults to STANDARD (ENHANCED/CITESCORE may require a higher subscription).
        Passing no filter is allowed but browses ALL serials (large) — supply at least one.
        """
        norm_title = title.strip() if title else None
        norm_issn = issn.strip() if issn else None
        norm_pub = pub.strip() if pub else None
        norm_subj = subj.strip() if subj else None
        norm_content = content.strip() if content else None
        norm_date = date.strip() if date else None
        norm_oa = oa.strip() if oa else None
        bounded_count = None if count is None else max(1, min(count, 200))
        bounded_start = None if start is None else max(0, start)
        try:
            return await _search_serial_title(
                title=norm_title or None,
                issn=norm_issn or None,
                pub=norm_pub or None,
                subj=norm_subj or None,
                content=norm_content or None,
                date=norm_date or None,
                oa=norm_oa or None,
                start=bounded_start,
                count=bounded_count,
                view=view,
            )
        except Exception as exc:
            return _err(query=norm_title or norm_issn or "serial-search", message=str(exc))

    @server.tool()
    async def scopus_subject_classification_lookup_by_source(
        source: str,
        description: str | None = None,
        detail: str | None = None,
        code: str | None = None,
        abbrev: str | None = None,
        field: str | None = None,
    ) -> dict:
        """Look up Scopus/ScienceDirect subject classification codes (to help build
        more precise search queries). `source` is required and must be 'scopus' or
        'scidir'. Optional filters: description, detail, code, abbrev, field (field
        restricts which fields are returned). scidir results additionally carry
        parent_code (hierarchy); scopus results have parent_code = null.
        """
        normalized_source = source.strip().lower() if source else ""
        if normalized_source not in ("scopus", "scidir"):
            # The API silently returns misleading scidir-shaped data for an unknown
            # source (HTTP 200, no clear error) — validate up front instead.
            return _err(query=source, message="source must be 'scopus' or 'scidir'")
        norm_desc = description.strip() if description else None
        norm_detail = detail.strip() if detail else None
        norm_code = code.strip() if code else None
        norm_abbrev = abbrev.strip() if abbrev else None
        norm_field = field.strip() if field else None
        try:
            return await _lookup_subject_classification(
                source=normalized_source,
                description=norm_desc or None,
                detail=norm_detail or None,
                code=norm_code or None,
                abbrev=norm_abbrev or None,
                field=norm_field or None,
            )
        except Exception as exc:
            return _err(query=normalized_source, message=str(exc))
