import os
import warnings
from dataclasses import dataclass, field

from dotenv import load_dotenv


load_dotenv()


def _resolve_elsevier_api_key() -> str | None:
    """Resolve the Elsevier API key with backward compatibility.

    Prefers the new ``ELSEVIER_API_KEY`` variable. If it is unset, falls back to
    the legacy ``SCOPUS_API_KEY`` and emits a deprecation warning.

    NOTE: The warning is emitted via ``warnings.warn`` (which writes to stderr),
    never to stdout. This MCP server communicates with clients over stdio using
    JSON-RPC; any stray write to stdout would corrupt the protocol frames.
    """
    new_key = os.getenv("ELSEVIER_API_KEY")
    if new_key:
        return new_key
    legacy_key = os.getenv("SCOPUS_API_KEY")
    if legacy_key:
        warnings.warn(
            "环境变量 SCOPUS_API_KEY 已弃用，请改用 ELSEVIER_API_KEY"
            "（计划于未来主版本移除兼容支持）。",
            DeprecationWarning,
            stacklevel=2,
        )
        return legacy_key
    return None


@dataclass(frozen=True)
class Settings:
    elsevier_api_key: str | None = field(default_factory=_resolve_elsevier_api_key)
    elsevier_insttoken: str | None = os.getenv("ELSEVIER_INSTTOKEN")
    # v3.0.0 optional keys (brand-new variables, no legacy-name migration needed).
    # Semantic Scholar: if unset, its tools are NOT registered at all (its keyword
    # search fails deterministically without a key — confirmed 429 on every request
    # during probing; see buildlog step 33). CORE: if unset, its tool still works but
    # is severely rate-limited (~5 requests before a 10-minute lockout).
    semantic_scholar_api_key: str | None = field(
        default_factory=lambda: os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    )
    core_api_key: str | None = field(default_factory=lambda: os.getenv("CORE_API_KEY"))
    # v3.1.0 optional key (unconditional registration, mirroring CORE — NOT Semantic
    # Scholar). NCBI Entrez works fine WITHOUT a key; a key only raises the official
    # rate limit from 3 to 10 requests/sec. So all pubmed tools register regardless of
    # whether this is set (see buildlog step 44 / goal.md QA-R014).
    ncbi_api_key: str | None = field(default_factory=lambda: os.getenv("NCBI_API_KEY"))


settings = Settings()
