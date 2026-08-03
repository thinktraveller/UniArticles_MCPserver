# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

UniArticles (亿文通) is a Model Context Protocol (MCP) server that unifies multiple academic literature sources — Scopus, ScienceDirect, ArXiv, PubMed, and Google Scholar — behind a single set of MCP tools, so LLM clients (Claude Desktop, Cherry Studio, etc.) can search and retrieve papers through one consistent interface. It is published to PyPI as `uniarticles-mcp` and typically launched by client tooling via `uvx uniarticles-mcp`, not run standalone by a human.

## Commands

```bash
# Install and run (uv, recommended)
uv sync
uv run uniarticles-mcp

# Install and run (pip)
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -e .
python -m uniarticles

# Tests
python -m unittest discover tests
python tests/verify_server.py   # verifies the MCP protocol handshake
```

Configuration lives in a `.env` file at the project root (loaded via `python-dotenv`):
```env
ELSEVIER_API_KEY=your_elsevier_api_key
```
`SCOPUS_API_KEY` is still read as a deprecated fallback for `ELSEVIER_API_KEY` — see `src/uniarticles/config.py`.

## Architecture

**Entry point chain**: `__main__.main()` → `server.create_server()` builds a `FastMCP("uniarticles-mcp")` instance → `sources.register_all_sources(server)` registers every data source's tools onto that one instance → `server.run()` serves over stdio.

**Source module pattern** (`src/uniarticles/sources/*.py`, one file per external data source: `arxiv.py`, `scopus.py`, `sciencedirect.py`, `paperscraper.py`): each module is self-contained and exposes a single `register(server: FastMCP) -> None` function that the `sources/__init__.py` aggregator calls. Inside each module:
- Private `async def _xxx(...)` functions do the actual HTTP call (via `httpx`) or wrap a third-party client library (`arxiv`, `paperscraper`) and return a normalized dict.
- `register()` defines the public `@server.tool()`-decorated functions, which validate/clamp input (e.g. bounding `count`, stripping empty queries) and catch exceptions from the private functions, converting them into the error shape below rather than letting them raise.
- Every tool returns the same normalized JSON shape regardless of source: `{"ok": bool, "source": str, "query": str, "count": int, "items": list[dict], "error": str | None}`, built via each module's local `_ok()` / `_err()` helpers. When adding a new tool or source, follow this exact shape so results stay uniform across sources for the calling LLM.

**Config** (`src/uniarticles/config.py`): a single frozen `Settings` dataclass instantiated once as module-level `settings`, populated from environment variables at import time. `_resolve_elsevier_api_key()` prefers `ELSEVIER_API_KEY`, falls back to legacy `SCOPUS_API_KEY` with a `warnings.warn` deprecation notice. Any diagnostic/log output anywhere in this codebase must go to stderr, never stdout — stdout is the JSON-RPC channel for the MCP stdio transport, and any stray write corrupts protocol frames for the connected client.

**Elsevier (Scopus/ScienceDirect) access is entitlement-gated**: `scopus.py` and `sciencedirect.py` call `https://api.elsevier.com/` endpoints that require a valid `ELSEVIER_API_KEY`, and some views/endpoints additionally require the caller's institution to hold an Elsevier subscription (optionally via `ELSEVIER_INSTTOKEN`) — a non-institutional or basic key will get 401/403 on those even though the code path is otherwise correct. `project-docs/goal.md` documents which Elsevier endpoints have been verified to actually work under a basic/non-commercial key vs. which return authorization errors regardless of code changes; consult it before assuming a new Elsevier endpoint is reachable.

## Project docs (Chinese)

This repo uses a set of Chinese-language planning documents under `project-docs/` that track intent across sessions — check these before starting nontrivial work, since they carry context not present in code:
- `project-docs/goal.md` — target/scope definition for the current version, including a clarification Q&A log and real API feasibility test results for Elsevier endpoints.
- `project-docs/project-plan.md` — the build plan derived from `goal.md`.
- `project-docs/buildlog.md` — the sole change log for this project (the previously separate user-facing `CHANGELOG.md` was removed; its history was merged into this file's "历史记录" section).
