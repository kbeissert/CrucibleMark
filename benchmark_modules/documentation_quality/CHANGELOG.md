# Changelog - Documentation Quality Module

## [2.0.0] - 2026-02-02

### Added
- **StructureValidator**: Markdown format checks (headings, code blocks, hierarchy)
- **ReadabilityScorer**: Flesch-Kincaid metrics for setup guides/tutorials
- **CompletenessChecker**: Required sections detection with fuzzy matching
- Integration test suite (`tests/test_evaluators.py`) with 4 test cases
- `doc_type` metadata field for all assets

### Changed
- **Architecture**: Split monolithic `evaluators.py` (280 LOC) into 6 specialized modules
- **Pylint Score**: 7.5 → 9.0+ (+20% improvement)
- **Maintainability**: Medium → High (single responsibility principle)

### Fixed
- None (no breaking changes, backward compatible)

## [1.0.0] - 2025-12-28

### Initial Release
- Tiered difficulty system (Labeled → Expert)
- Hybrid semantic matching (keyword + similarity)
- Solution quality scoring (keyword presence)
- 5 test assets (README, API, Component, Setup, Changelog)
