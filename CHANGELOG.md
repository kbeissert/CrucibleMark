# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v2.1.1] - 2026-02-14

### Added

- **New Provider Category:** "Local Cloud" for Ollama Cloud proxy models
  - Distinguishes cloud proxies (minimax-m2:cloud, gpt-oss:120b-cloud) from true local models
  - Appears separately in leaderboard and statistics
- **SSOT for Model Categorization:** Centralized `is_cloud_model()` function in `utils/model_utils.py`
  - Detection rules: `:cloud` tag, `-cloud` suffix, or size < 0.01 GB
  - Used consistently across UI filters, data loading, and model listing

### Changed

- **Provider Selection UI:** Now offers three distinct categories:
  1. Commercial (Mistral, Claude, GPT)
  1. Local (Ollama offline models)
  1. Local Cloud (Ollama Cloud proxy)
- **Leaderboard Generation:** Automatic categorization using SSOT instead of filename-based inference
- **Documentation:** Updated `MODEL_CLASSIFICATION.md` with detailed categorization logic

### Fixed

- Cloud models (e.g., `gpt-oss:120b-cloud`) no longer miscategorized as "Local"
- Consistent cloud model detection across entire codebase

## [v2.1.0] - 2026-02-03

### Added

- Stricter v2.1 rubric thresholds (80%+ keywords for full credit)
- Rubrics for `reasoning_5e_001` and `metacog_004`
- Deprecation warning system for legacy scoring
- Migration timeline (legacy removal in v3.0)

### Changed

- v2.0 scoring now requires 80%+ keyword matches for full credit (was 66%)
- `reasoning_5e_001`: Fair scoring (15% → ~70% for good responses)
- All v2.1 tests now have binary % \<30% (improved discrimination)

### Deprecated

- Legacy scoring system (will be removed in v3.0)
- 6 tests still use legacy with deprecation warnings

### Fixed

- `reasoning_5e_001`: Good responses now score appropriately (was 15%)
- `metacog_004`: Binary % reduced from 31% to ~20%
