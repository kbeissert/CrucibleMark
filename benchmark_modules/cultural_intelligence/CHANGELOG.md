# Changelog - Cultural Intelligence Module

## [2.0.0] - 2026-02-02

### Added

- **RegionalConsistencyValidator**: Detects mixing of DE/AT/CH regional terms
- **FormalityScorer**: Continuous formality scale (0.0-1.0)
- Integration test suite (`tests/test_evaluators.py`) with 4 test cases
- `constants.py` with German markers, regional expressions, formality markers

### Changed

- **Architecture**: Split monolithic `evaluators.py` (320 LOC) into 5 specialized modules
- **Pylint Score**: 7.5 → 9.0+ (+20% improvement)
- **Maintainability**: Medium → High (single responsibility principle)

### Fixed

- None (no breaking changes, backward compatible)

## [1.0.0] - 2025-12-28

### Initial Release

- Language proficiency scoring (German markers, formality)
- Cultural fit scoring (regional expressions, politeness)
- Solution quality scoring (keyword presence)
- 3 test assets (German Email, Swiss Localization, Austrian Customer Service)
