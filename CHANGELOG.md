# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v3.1.1] - 2026-03-25

### Changed
- **Strict Judge Fail-Fast Mechanism:** Der LLM Judge verzichtet nun komplett auf das inkonsistente und fehleranfällige "Fallback"-Muster (z.B. der automatische Wechsel auf lokale Modelle, wenn die Anthropic-API ausfällt oder das Budget erschöpft ist). Stattdessen wird nun eine `JudgeUnavailableError` Exception geworfen, die den Benchmark sofort pausiert und unvollständige Durchläufe verlässlich speichert, um Kosten zu schonen.
- **Judge Coverage Calculation:** Die Formel für die "LLM Judge Coverage" im Leaderboard wurde repariert, sodass unbeurteilte Module (wie der "Political Compass") den Prozentwert nicht mehr künstlich senken. Der Wert wird im CSV nun sauber als echter Prozentwert formatiert (z.B. "100%").
- **Codebase Maintenance & Refactoring:** Utils-Skripte wurden hinsichtlich "Magic Numbers" und Typisierungs-Warnungen überarbeitet. Veraltete Debug-Aufrufe (`save_debug_response`) und root-Skripte wurden aufgeräumt, sowie `make audit_markdown` in die Makefile-Toolchain integriert.

### Fixed
- **Meta-Review Prompt Formats:** Ein Off-by-One Bug wurde behoben und die Grammatik- bzw. Parsing-Regeln im externen Meta-Review-Prompt wurden verschärft.
- **Political Compass Polarity:** Ein Fehler bei der Berechnung des Flips direkt auf der Null-Achse ("Zero-Axis Polarity Flip") wurde korrigiert.

### Removed
- **Fallback Configurations:** Alle `fallback` Knoten aus der `benchmark_config.yaml` sowie die zugrunde liegende `FallbackProviderConfig` innerhalb der Python-Infrastruktur wurden gelöscht.

## [v3.1.0] - 2026-03-20

### Added
- **Reasoning Tokens & Metacognition:** Einführung der `<thought>`-Tag Metakognitions-Überprüfung. Das System trackt nun den `reasoning_tokens` Count und filtert die `<thought>` Blöcke vor der finalen LLM-Judge Auswertung restriktiver Modelle heraus.
- **Dynamic Meta-Review Prompting:** Der `generate_review.py` Meta-Reviewer nutzt nicht länger einen Python-hardgecodeten Prompt, sondern liest seinen System-Prompt dynamisch und versionierbar aus der neuen Konfigurationsdatei `config/meta_reviewer_prompt.yaml` ein.
- **Coder/Thinking Model Leniency:** Einführung einer Kulanzklausel (Leniency Clause) beim Bias-Review, um speziell trainierte Coder- oder Reasoning-Modelle vor ungerechtfertigten Penalties zu bewahren.

### Changed
- **CLI Hybrid Scoring Migration:** Das Modul `cli_benchmark` (`cli001` - `cli006`) wurde von der reinen Regex-Evaluierung auf ein hybrides `llm_judge`-Scoring umgestellt (inkl. Fallbacks, Penalty-Systemen und JSON-orientierter Aufbereitung der `functional_goal`s).
- **Judge Context Expansion:** Das Token-Limit des LLM-Judges in `benchmark_config.yaml` wurde von 2048 auf 4096 Tokens erhöht, um zu verhindern, dass ausführliche Architekturbewertungen (z.B. in `reasoning_5e_001`) mitten in JSON-Strukturen abbrechen.
- **Robust CSV Sync:** Der `--force`-Parameter und das Cross-Model-Resuming (`run_cross_model_benchmark.py`) überschreiben und integrieren bestehende CSVs nun intelligenter, ohne manuelle und fehleranfällige Löschvorgänge zu erfordern.

### Fixed
- **Judge Parse Fallbacks:** Bei korruptem Output (z. B. abgeschnittenes JSON) fängt `judge_parser.py` den Parse-Fehler ab, verweigert den Runtime-Crash und speichert stattdessen den rohen Debugging-Output unter `last_failed_raw.txt`.
- **Political Compass Anomaly Scan:** Ein Fehler in der Scoring-Logik wurde behoben, sodass nun bei einem Achsen-Shift `> 1` automatisch ein Anomalie-Scan ausgelöst wird (`auto-trigger anomaly scan on pc shift > 1`).

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

## [v2.5.0] - 2026-03-14

### Added
- **XAI / Grok Support:** Integration von XAI Grok Modellen inkl. API Pricing Tracking.
- **Cascading Token Fallback:** Implementierung eines kaskadierenden Token-Fallback-Systems zur besseren Fehlerabfangung mit Verhaltens-Metadaten.

### Changed
- **Meta-Reviewer:** Verbesserung der Erkennung von System-Info-Blöcken durch den Meta-Reviewer.
- **Anthropic Stabilität:** Das Timeout für den Anthropic-Client wurde auf 600s erhöht, um Abbrüche bei langen Generierungen zu vermeiden. Automatische Retry-Logs wurden im Konsolen-Output unterdrückt.

### Removed
- **Unused Pipeline Logic:** Die reine dynamische Golden Standard Validierungsausgabe sowie alte ungenutzte Pipelines (`refactor(core)`) wurden entfernt.

## [v2.3.0] - 2026-03-12

### Added
- **Audit Mode (Robust):** Einführung eines vollumfänglichen Audit-Modus. Dieser protokolliert ausgeführte Prompts, LLM-Judge Fingerprinting, komplette Reasoning Trails sowie die Kategorie-Sub-Scores der Regex-Evaluationen.
- **Google / Gemini Provider:** Native Unterstützung von Google Modellen für LLM-Judge Pipelines ergänzt.
- **Hybrid Scoring Architecture:** Implementierung einer modular gewichteten Hybrid-Scoring Architektur (0.10 Regex / 0.90 Judge) für präzisere semantische Auswertungen.

### Fixed
- **LLM Judge Bugfixes:** Behebung von Routing-, Caching- und Parsing-Bugs im Judge sowie Schutz vor "Reasoning Truncation".

## [v2.2.0] - 2026-03-08

### Added
- **CLI Benchmark Integration:** Das CLI v2 Benchmark wurde gehärtet (inkl. 6-Task YAML-Unterstützung) und nativ in die "Standard Base Test" Architektur integriert.

### Fixed
- **Ollama Token Limits:** Reduzierung der Token-Limits für lokale Reasoning-Modelle von 32k auf 8k, um "VRAM Swap" System-Freezes auf macOS Maschinen zu verhindern.

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

## [v1.1.3] - 2026-02-11

### Added
- **Adaptive Pause System:** Implementierung eines adaptiven Pause-Systems für den Benchmark inkl. Dev Mode Unterstützung.
- **Probe/Warm-up:** Separation von Load-Time Tracking und Warm-up Probes für genauere Statistik-Erfassungen.

### Fixed
- **Code Quality:** Stabilitätsverbesserungen im Code Quality Modul, speziell für kleinere Modelle. Kompatibilitätsfix für DeepSeek-R1.

## [v1.1.0] - 2026-02-03

### Changed
- **Leaderboard V1.1 Overhaul:** Umstellung auf V1.1 Leaderboards mit neuen Aggregations-Metriken und Kosten-Analysen in USD/1K Tokens.
- **Golden Standard:** Stabilisierung der Golden Standard Generation für die kommerziellen Modelle.

## [v1.0.0] - 2026-02-03

### Added
- **Initial Production Release:** Einführung der Basis-Architektur (`run_commercial_benchmark`, `run_local_benchmark`).
- **Political Compass:** Implementierung und Stabilisierung der v3.0 Political Compass Metriken inkl. Mock-Testing.
- **Last-Hyphen-Rule:** Dynamische Asset-Gruppierung basierend auf der "Last-Hyphen-Rule" im Leaderboard.
