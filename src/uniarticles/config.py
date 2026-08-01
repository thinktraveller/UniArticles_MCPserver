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
    arxiv_download_dir: str = os.getenv("ARXIV_DOWNLOAD_DIR", os.path.join(os.getcwd(), "arxiv_downloads"))


settings = Settings()
