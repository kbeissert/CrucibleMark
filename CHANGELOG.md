# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v3.0.1] - 2026-03-19

### Changed
- **Architecture Refactoring:** Consolidated base logic from `run_local_benchmark.py` and `run_commercial_benchmark.py` into a unified `utils/base_runner.py` to eliminate significant redundancy and improve maintenance. (Phases 1-4)

## [v3.0.0] - 2026-03-18

### Added
- **3-Tier Refusal Architecture:** Integrierte Anti-Zensur-Logik für rigide LLMs im Political Compass Modul.
- **Progressive Temperature Check:** Automatischer Retest abgelehnter Prompts durch Temperaturerhöhung (0.1 → 0.4 → 0.7) und angehängte System-Injektion (Safety-Bypass).
- **Erweiterte Safety-Metriken:** Aufzeichnung von `hard_refusals` und automatische Erkennung von "Safety Shifts" (Werte-Verzerrungen durch das heuristische Red-Teaming) in der Endauswertung dokumentiert.

### Changed
- **Repository Cleanup & README Overhaul:** Die `README.md` wurde radikal entschlackt, neu strukturiert und auf die tatsächliche v3.0.0 Architektur (inkl. API-Verbindungen & Makefile) gehoben.
- **Roadmap Shift:** Voller Fokus für die kommenden Iterationen auf Web-UI (React/Streamlit), Multimodalität und "Agentic Workflow"-Evaluierung gesetzt.
- **Dokumentation:** Umfangreiche Erweiterung der `POLITICAL_COMPASS_KONZEPT.md` um das 6. Kapitel (Erweiterte Sicherheitsarchitektur & Refusals).

### Fixed
- **Pydantic Serialization Bug:** Ein hartnäckiger `AttributeError` im Anomaly Checker (`verify_compass_anomalies.py`) beim Nested-Parsing von `BenchmarkResult.get()` wurde durch nativ robustes `.raw_response` JSON-Loading behoben.
- **Checkpointer Stability:** Aufgeklärte Architektur für das nahtlose Wiederaufsetzen von durch Token-Limits oder Budget-Caps abgebrochenen Testläufen.

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
