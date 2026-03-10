# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Support for Scopus, ArXiv, and Semantic Scholar.
