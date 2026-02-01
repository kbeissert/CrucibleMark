# CrucibleMark - Projekt-Status & Architektur

**System Version:** 0.9.5-beta  
**Golden Standard:** v2.1.0 (Mistral Large, 30. Jan 2026)  
**Datum:** 1. Februar 2026  
**Status:** Pre-Release Validation (Path to v1.0)

---

## 🚧 Aktueller Status (Februar 2026)

Wir befinden uns in der **Beta-Phase (0.9.5)** – der Weg zu Version 1.0.0 ist klar definiert.

### ✅ Framework Refactoring Complete (Phase 4 - Feb 2026)

**Das Framework wurde auf Production-Grade Code-Qualität gebracht:**

1. **Modulare Leaderboard-Architektur**:
   - `generate_leaderboard.py` (1384 Zeilen) wurde in ein sauberes Package mit 7 Modulen aufgeteilt
   - Neue Struktur: `scripts/leaderboard/` (config, data_loader, score_calculator, module_integration, formatter, exporter)
   - PyLint-Score: **9.13/10** (vorher: 8.79)

2. **Duplicate Code Elimination**:
   - Scoring-Logik zentralisiert in `utils/scoring_utils.py`
   - Benchmark-Loading in `utils/module_registry.py` erweitert
   - -48 Zeilen Duplikation aus Benchmark-Runnern eliminiert

3. **Code Quality Achievement**:
   - Ruff: **0 Errors** (100% clean)
   - PyLint Framework-Average: **9.1/10**
   - Zero Regressions (alle Funktionen validiert)

4. **Technical Debt Reduced**:
   - Monster-Scripts eliminiert (größte Datei jetzt <800 Zeilen)
   - DRY-Prinzip durchgesetzt (Don't Repeat Yourself)
   - Single Responsibility Principle (jedes Modul <300 Zeilen)

---

### Vorherige Framework-Updates (Phase 1-3)

**Phase 3 - Granular Scoring (Jan 2026)**:
- ✅ **Asset-Level Contributions** für Routine/Reasoning Scores
- ✅ Ermöglicht "gemischte" Module (z.B. Security Audits mit Reasoning-Anteil)
- ✅ Volle Rückwärtskompatibilität für alte Benchmark-Runs
- ✅ **Inversion of Control**: Leaderboard generiert Spalten dynamisch basierend auf aktivierten Modulen

**Phase 2 - Reasoning v2.3 (Jan 2026)**:
- ✅ **Tier Weighting**: Leaderboard berechnet korrekt (Expert=2.0x, Basic=1.0x)
- ✅ **Regex Hardening**: Scorer erkennen "0/10" auch als "Feasibility: 0" (Phi4 Fix)
- ✅ **Debug Mode**: Automatische Speicherung von Responses bei <30% Score
- ✅ **Anti-Ceiling Maßnahmen**: Keine 100% Gesamtschnitt mehr (Mistral Large ~73%)

**Phase 1 - Golden Standard Hygiene (Dez 2025)**:
- ✅ **Trial-and-Commit Strategie**: Keine automatischen Updates während Benchmarks
- ✅ Explizites Update via `make generate-golden`
- ✅ Dokumentation in `GOLDEN_STANDARD_CHANGELOG.md`

---

## 1. Projekt-Übersicht

### Zweck
Framework zum systematischen Benchmarking von **lokalen** (Ollama) und **kommerziellen** (Mistral, Claude, GPT) Large Language Models anhand strukturierter Test-Module.

### Kernkonzepte
1. **Modulare Architektur**: Plugin-basiertes System – neue Test-Module einfach hinzufügbar
2. **Tiered Difficulty (1-4)**: Assets enthalten Fehler in 4 Schwierigkeitsstufen (Labeled, Standard, Advanced, Expert)
3. **Efficiency Tracking**: Messung von Token-Verbrauch und Kosten ($) pro Benchmark-Run
4. **Hybrid Scoring**: Kombination aus quantitativer Bewertung (Keyword/Regex) und qualitativer Analyse (Semantische Ähnlichkeit zu Golden Standards)
5. **Golden Standard**: Mistral Large (123B) als Vergleichsmaßstab für alle Modelle
6. **Reproducibility**: Deterministische Outputs durch Seed-Steuerung (Random Seed 42)

---

## 2. Framework-Architektur (Updated Feb 2026)

### 2.1 Verzeichnisstruktur

```
cruciblemark/
│
├── benchmark_config.yaml          # ⭐ ZENTRALE KONFIGURATION
│   ├── modules: {}                # Test-Module Registry
│   ├── golden_standard: {}        # Golden Standard Definition
│   ├── providers: {}              # LLM Provider (commercial + local)
│   └── output: {}                 # CSV-Pfade
│
├── run_benchmark.py               # ⭐ HAUPT-ORCHESTRATOR (Deprecated - verwende scripts/core/)
│
├── scripts/
│   ├── core/                           # 🆕 Daily-Use Scripts
│   │   ├── run_local_benchmark.py      # Benchmark-Runner für Ollama-Modelle
│   │   ├── run_commercial_benchmark.py # Benchmark-Runner für kommerzielle LLMs
│   │   ├── benchmark_auto.py           # Automatisierung (Overnight Mode)
│   │   └── generate_leaderboard.py     # Thin Wrapper für Leaderboard-Package
│   │
│   ├── leaderboard/                    # 🆕 MODULAR PACKAGE (Production-Grade)
│   │   ├── __init__.py                 # Main Orchestration
│   │   ├── config.py                   # Configuration Loading
│   │   ├── data_loader.py              # CSV/JSON Parsing
│   │   ├── score_calculator.py         # Core Scoring Logic (Business Logic)
│   │   ├── module_integration.py       # Plugin-System für Module
│   │   ├── formatter.py                # Presentation Layer (Badges, Tabellen)
│   │   └── exporter.py                 # CSV/Markdown Export
│   │
│   ├── utilities/                      # Info & Validation
│   │   ├── list_models.py
│   │   ├── list_modules.py
│   │   ├── validate_assets.py
│   │   └── validate_structure.py
│   │
│   ├── analysis/                       # Analysis Tools
│   │   ├── analyze_prompts.py
│   │   ├── classify_generation.py
│   │   └── compare_baselines.py
│   │
│   ├── maintenance/                    # Cleanup Scripts
│   │   ├── clean_results.py
│   │   ├── cleanup_runs.py
│   │   ├── consolidate_csv.py
│   │   └── recover_pc_results.py
│   │
│   └── dev/                            # Developer Tools
│       ├── scaffold_module.py
│       ├── test_reasoning_metacog.py
│       ├── audit_validation.py
│       └── setup_env.py
│
├── benchmark_modules/             # ⭐ TEST-MODULE (Plugin-System)
│   ├── code_quality/              # ✅ v1.0.0
│   │   ├── test.py                # Controller (Runner)
│   │   ├── config.yaml            # Module Configuration
│   │   ├── README.md
│   │   ├── core/                  # Business Logic
│   │   │   ├── evaluators.py      # Scoring Logic
│   │   │   └── constants.py       # Config & Thresholds
│   │   └── assets/                # Test Assets (YAML)
│   │
│   ├── ux_writing/                # ✅ v1.0.0
│   ├── documentation_quality/     # ✅ v1.0.0
│   ├── content_transformation/    # ✅ v0.9.0-beta
│   ├── reasoning_logic/           # ✅ v2.3.0
│   ├── political_compass/         # ✅ v3.0.0
│   └── cultural_intelligence/     # ✅ v1.0.0
│
├── utils/                         # ⭐ FRAMEWORK UTILITIES
│   ├── llm_client.py              # Unified LLM Provider Wrapper
│   ├── config_validator.py        # Golden Standard Validierung
│   ├── module_loader.py           # Dynamic Module Loading
│   ├── module_registry.py         # 🆕 Benchmark Loading (Enhanced)
│   ├── provider_clients.py        # Provider Implementations
│   ├── scoring_utils.py           # 🆕 Score Contribution Logic
│   ├── similarity.py              # Semantic Scoring (Sentence Transformers)
│   ├── cost_tracker.py            # Token & Cost Tracking
│   ├── logging_config.py          # "Silent Console / Noisy Log"
│   └── model_utils.py             # Model Versioning (DRY)
│
├── docs/                          # Documentation
│   ├── USER_GUIDE.md
│   ├── ARCHITECTURE.md
│   ├── ADDING_MODULES.md
│   ├── DATA_FORMAT.md
│   ├── GOLDEN_STANDARDS.md
│   ├── GOLDEN_STANDARD_CHANGELOG.md
│   ├── MODEL_CLASSIFICATION.md
│   └── BENCHMARK_SCENARIOS.md
│
├── golden_standards/              # Referenz-Antworten (JSON)
│   ├── mistral/                   # Golden Standard Files (v2.1.0)
│   └── README.md
│
├── benchmark_scores/              # Ergebnisse (CSV, Leaderboard)
│   ├── local_models_benchmark.csv
│   ├── commercial_models_benchmark.csv
│   ├── benchmark_leaderboard.csv
│   └── political_compass_results.csv
│
├── outputs/                       # Logs & Details
│   ├── runs/                      # JSON Results per Run
│   ├── cost_log.csv               # Token & Cost Tracking
│   └── temp/                      # Session Data
│
├── schemas/                       # Data Models
│   └── result.py                  # BenchmarkResult Schema
│
├── backups/                       # Automated Backups
├── logs/                          # Application Logs
└── Makefile                       # Task Automation
```

---

### 2.2 Zentrale Konfiguration (`benchmark_config.yaml`)

**Golden Standard Definition:**
```yaml
golden_standard:
  provider: "mistral"              # Referenz zu providers.commercial.mistral
  model: "mistral-large-latest"    # Spezifisches Modell (123B)
  description: "Mistral Large als stabile Referenz (v2.1.0)"
```

**Module Registry:**
```yaml
modules:
  code_quality:
    enabled: true
    version: "1.0.0"
    category: "reasoning"          # Routing für Leaderboard

  ux_writing:
    enabled: true
    version: "1.0.0"
    category: "routine"

  political_compass:
    enabled: false                 # Modul optional deaktivieren
    version: "3.0.0"
```

---

## 3. Modul-Versionen (Stand Feb 2026)

| Modul | Version | Status | Kategorie |
|-------|---------|--------|-----------|
| `code_quality` | 1.0.0 | ✅ Production | reasoning |
| `ux_writing` | 1.0.0 | ✅ Production | routine |
| `documentation_quality` | 1.0.0 | ✅ Production | routine |
| `content_transformation` | 0.9.0-beta | 🟡 Beta | routine |
| `reasoning_logic` | 2.3.0 | ✅ Production | reasoning |
| `political_compass` | 3.0.0 | ✅ Production | qualitative |
| `cultural_intelligence` | 1.0.0 | ✅ Production | routine |

---

## 4. Roadmap & Next Steps

### ✅ Completed (v0.9.5 - Feb 2026)

**Framework Hardening:**
- [x] **Leaderboard Refactoring**: Modulare Package-Architektur (7 Module)
- [x] **Code Quality**: PyLint 9.1/10, Ruff 100% clean
- [x] **Duplicate Code Elimination**: Scoring-Logik zentralisiert
- [x] **Zero Regressions**: Functional Validation (11 Reasoning-Tests)

**Scoring & Methodology:**
- [x] **Granular Scoring (v3.0)**: Asset-Level Contributions (Routine/Reasoning Split)
- [x] **Performance Ratio**: Normalisierung für faire Vergleichbarkeit
- [x] **Reasoning v2.3**: Tier Weighting, Anti-Ceiling, Debug Mode
- [x] **Golden Standard Hygiene**: Trial-and-Commit Strategie

**Operations:**
- [x] **Cost & Token Tracking**: Real-time Calculation für kommerzielle Provider
- [x] **Logging System**: "Silent Console / Noisy Logfile"
- [x] **Smart Rate Limit Handling**: Automatic Pause & Backoff (429 Detection)
- [x] **Backup Workflow**: `make backup` mit Auto-Cleanup

**Module (Production-Ready):**
- [x] Code Quality (5 Assets, Tier 1-4)
- [x] UX Writing (5 Assets, Tier 1-4)
- [x] Documentation Quality (5 Assets, Tier 1-4)
- [x] Content Transformation (6 Assets, Tier 1-3)
- [x] Reasoning Logic (11 Assets, Tier 2-3, inkl. Metacognition)
- [x] Political Compass (74 Questions, Anti-Diplomat Prompting, v3.0)
- [x] Cultural Intelligence (5 Assets, Tier 1-4)

---

### 🚧 In Progress (Path to v1.0)

**Priority 1: LLM-as-a-Judge Scorer** (🔥 Critical for v1.0)
- [ ] Design: Hybrid-Scorer (LLM-Judge + Current Scorer)
- [ ] Implementation: `data.llm_judge` in Structured Result Objects
- [ ] Validation: Vergleich LLM-Judge vs. Hybrid auf Golden Standard
- [ ] Documentation: Scorer-Methodology im USER_GUIDE

**Priority 2: Module Refactoring** (Code Hygiene)
- [ ] Code Quality: Ruff + PyLint auf 9.0+
- [ ] UX Writing: Utility-Konsolidierung
- [ ] Documentation Quality: Test-Coverage prüfen
- [ ] Content Transformation: Scorer-Logik Review
- [ ] Cultural Intelligence: Asset-Erweiterung
- [ ] Reasoning Logic: RCI-Optimierung

**Priority 3: Documentation Polish**
- [ ] USER_GUIDE: Tutorial-Section erweitern
- [ ] ARCHITECTURE: Leaderboard-Package dokumentieren
- [ ] ADDING_MODULES: Best Practices aus Refactoring
- [ ] DATA_FORMAT: LLM-Judge-Metriken erklären

---

### 🔮 Planned (Post v1.0)

**Features:**
- [ ] **Reporting Dashboard**: Streamlit/Dash Visualization
- [ ] **HuggingFace Leaderboard Integration**: Auto-Upload der Ergebnisse
- [ ] **Custom Model Support**: GGUF-Files ohne Ollama
- [ ] **Web Frontend**: CSV-basierte Reports & Charts

**Quality:**
- [ ] **Leaderboard Weight Classes**: Lightweight (<20B) vs. Heavyweight (>70B)
- [ ] **Calibration Phase**: Fine-Tuning aller Module für konsistente Ergebnisse
- [ ] **Test-Coverage**: Unit-Tests für Scorer & Evaluators (>80% Coverage)

---

## 5. Archived Updates (Pre-0.9.5)

<details>
<summary>Click to expand previous updates</summary>

### v0.9.4 (Jan 2026)
- ✅ Scoring Logic: Strict 40% keyword match & 0.78 semantic similarity threshold
- ✅ UX Writing: Asset-Specific Ratios (100% false-positive free)
- ✅ Verification: Validated with dolphin-llama3:8b (38% score confirmed)

### v0.9.3 (Jan 2026)
- ✅ Performance Ratio: Normalisierung eingeführt
- ✅ Documentation Quality: Modul technisch validiert
- ✅ Validation Report: Qwen (104%) & Dolphin Recovery (55%) bestätigt

### v0.9.2 (Dez 2025)
- ✅ Smart Cleanup: Automated log retention (N latest runs per model)
- ✅ Backup Workflow: `make backup` archives and auto-cleans workspace
- ✅ Config UX: Reorganized benchmark_config.yaml

### v0.9.1 (Dez 2025)
- ✅ Political Compass 3.0: Qualitative Results (Archetypes statt Scores)
- ✅ Pipeline: Shared CSV output für Leaderboard
- ✅ Recovery: restore_pc_results.py für Log-Recovery

### v0.9.0 (Nov 2025)
- ✅ Core Framework (Runner, Config, Utils, CLI Menu)
- ✅ Hybrid Model Classification: Gen 1-3 Categorization
- ✅ Entertainment Mode: Streaming "Thinking" Output
- ✅ Golden Standard: Mistral Integration

</details>

---

## 6. Technische Details

### Code Quality Metrics (Framework)

| Komponente | PyLint Score | Ruff Status | Zeilen |
|------------|--------------|-------------|--------|
| `scripts/leaderboard/` | 9.13/10 | ✅ Clean | ~900 (7 Module) |
| `utils/` | 9.37/10 | ✅ Clean | ~2800 |
| `scripts/core/` | ~9.0/10 | ✅ Clean | ~2200 |
| **Framework Average** | **9.1/10** | **0 Errors** | **~5900** |

### Design Patterns
- **Package-by-Feature**: Leaderboard als eigenständiges Package
- **Single Responsibility**: Jedes Modul < 300 Zeilen
- **DRY Principle**: Keine Code-Duplikation
- **Inversion of Control**: Leaderboard fragt Module, nicht umgekehrt

---

## 7. Support & Contact

- **Issues**: GitHub Issues (wenn Public)
- **Discussions**: Interne Dokumentation
- **Logs**: `logs/crucible.log` (Debug-Informationen)

---

**Last Updated:** 1. Februar 2026  
**Next Milestone:** v1.0.0 (LLM-Judge-Scorer)
