# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-03-24

### Changed
- **Documentation**: Added explicit stability warnings for Google Scholar in all main docs.
  - Clarified that Google Scholar connectivity may be unstable or temporarily unavailable.
  - Marked Google Scholar-related capability as experimental/test-only.

## [1.2.0] - 2026-03-24

### Added
- **Paperscraper Tools**: Added two MCP tools in the main server source set.
  - Added `search_pubmed_papers(query, max_results)` for PubMed retrieval.
  - Added `search_scholar_papers(title)` for Google Scholar title lookup.

### Changed
- **Architecture**: Merged paperscraper functionality into `src/uniarticles/sources/paperscraper.py` and registered it in the main MCP server.
- **Documentation**: Updated README and step-by-step guides to include PubMed and Google Scholar capabilities.
- **Dependencies**: Added `paperscraper` dependency and refreshed lockfile.

### Removed
- **Semantic Scholar Source**: Removed Semantic Scholar source module, registration, API-key references, and related docs/config mentions.

## [1.1.0]

### Changed
- **Terminology**: Standardized user-facing wording from “Scopus API” to “Elsevier API” across documentation and configuration examples.
  - Clarified that Scopus is an Elsevier database.
  - Clarified that `SCOPUS_API_KEY` is an Elsevier API key and may be used for other Elsevier APIs when subscription scope allows.
- **Docs & Examples**: Updated API key placeholders from `your_scopus_api_key_here`/`your_scopus_api_key` to Elsevier-oriented naming in guides and config examples.
### Removed
- **Scopus Citing Feature**: Removed non-working citing-paper capability from tools and scripts.
  - Removed MCP tool `get_citing_papers`.
  - Removed related CLI/script command paths and documentation references.

## [1.0.0] - 2026-03-10

### Added
- **Configuration**: Added `--refresh` flag to `uvx` command in documentation and example config to force package cache refresh.
  - This ensures users always get the latest version with ChemRxiv removed.

## [0.3.0] - 2026-03-10

### Removed
- **ChemRxiv**: Completely removed ChemRxiv data source integration.
  - The ChemRxiv API platform has been closed since 2026.
  - Removed all related code, tests, and documentation references.

## [0.2.3] - 2026-03-10

### Fixed
- **Documentation**: Corrected `.env.example` file format.

## [0.2.2] - 2026-03-10

### Added
- **Documentation**: Added comprehensive `README.md` and `step-by-step-guide` (English & Chinese).
- **Guide**: Detailed configuration instructions for MCP clients.

## [0.2.1] - 2026-03-10

### Changed
- Minor internal updates.

## [0.2.0] - 2026-03-10

### Added
- Initial release of UniArticles MCP Server.
- Support for Scopus and ArXiv.
