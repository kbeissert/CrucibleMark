# CrucibleMark - Projekt-Status & Architektur

**Version:** 0.9.7-release-candidate
**Datum:** 28. Januar 2026
**Status:** Refactoring Complete / Golden Standards Baseline Set

---

## 🚧 Status Update (Jan 2026)
Das Framework erreicht Version 0.9.7 (Release Candidate für Pre-Extension Baseline).
Das Reasoning-Modul wurde vollständig refactored (Modularität, Type-Safety, DRY).
Die aktuellen Benchmarks wurden als "Golden Standards" (v0.9 Baseline) eingefroren.

Nächster Fokus: Erweiterung der Reasoning-Logik vor v1.0.

1.  **✅ Modul-Standardisierung**: Alle Module (Code, Content, UX, Documentation, Reasoning, Political, Cultural) sind auf die Core/MVC-Architektur migriert.
2.  **✅ Code Integrity Check**: Reasoning-Modul ist fully linted (Ruff/Mypy/Pylint clean).
3.  **⏳ Module Extension**: Geplante Erweiterung des Reasoning-Moduls.
4.  **⏳ Full Benchmark Test**: Kompletter Durchlauf v1.0.

---

## 1. Projekt-Übersicht

### Zweck
Framework zum systematischen Benchmarking von **lokalen** (Ollama) und **kommerziellen** (Mistral, Claude, GPT) Large Language Models anhand strukturierter Test-Module.

### Kernkonzepte
1.  **Modular Architecture**: Plugin-basiertes System - neue Test-Module einfach hinzufügbar
2.  **Tiered Difficulty (1-4)**: Assets enthalten Fehler in 4 Schwierigkeitsstufen (Labeled, Standard, Advanced, Expert)
3.  **Efficiency Tracking**: Messung von Token-Verbrauch und Kosten ($) pro Benchmark-Run
4.  **Hybrid Scoring**: Kombination aus quantitativer Bewertung (Keyword/Regex) und qualitativer Analyse (Semantische Ähnlichkeit zu Golden Standards)
5.  **Golden Standard**: Ein kommerzielles Referenz-Modell als Vergleichsmaßstab für lokale Modelle
6.  **Reproducibility**: Deterministische Outputs durch Seed-Steuerung (Random Seed 42)

---

## 2. Verzeichnisstruktur

```
crucible-mark/
│
├── benchmark_config.yaml          # ⭐ ZENTRALE KONFIGURATION
│   ├── modules: {}                # Test-Module Registry
│   ├── golden_standard: {}        # Golden Standard Definition
│   ├── providers: {}              # LLM Provider (commercial + local)
│   └── output: {}                 # CSV-Pfade
│
├── run_benchmark.py               # ⭐ HAUPT-ORCHESTRATOR (Interaktives Menü)
│
├── scripts/
│   ├── run_local_benchmark.py           # Benchmark-Runner für Ollama-Modelle
│   ├── run_commercial_benchmark.py      # Benchmark-Runner für kommerzielle LLMs
│   └── validate_assets.py               # ✅ Asset-Validierung (Schema & Version)
│
│
├── benchmark_modules/             # ⭐ TEST-MODULE (Plugin-System)
│   ├── code_quality/              # ✅ Code Quality Audit
│   │   ├── test.py                # Controller (Runner)
│   │   ├── README.md
│   │   ├── core/                  # Business Logic
│   │   │   ├── evaluators.py      # Scoring Logic
│   │   │   └── constants.py       # Config & Thresholds
│   │   └── assets/ (YAML)
│   │
│   ├── ux_writing/                # ✅ UX Writing & Microcopy
│   │   ├── test.py
│   │   ├── core/
│   │   └── assets/
│   │
│   ├── documentation_quality/     # ✅ Documentation Quality
│   │   ├── test.py
│   │   ├── core/
│   │   └── assets/
│   │
│   ├── content_transformation/    # ✅ Content Adaption
│   │   ├── test.py
│   │   ├── core/
│   │   └── assets/
│   │
│   ├── reasoning_logic/           # ✅ Reasoning & Logic
│   │   ├── test.py
│   │   ├── core/
│   │   └── assets/
│   │
│   └── political_compass/         # ✅ Political Compass (Bias Check)
│       ├── test.py
│       ├── README.md
│       ├── core/                  # Extended Architecture
│       └── assets/ (YAML)
│
├── utils/
│   ├── llm_client.py              # Unified LLM Provider Wrapper
│   ├── config_validator.py        # Golden Standard Validierung
│   ├── module_loader.py           # Dynamic Module Loading
│   ├── provider_clients.py        # Provider Implementations
│   └── similarity.py              # ⭐ SEMANTIC SCORING (Sentence Transformers)
│
├── docs/
│   ├── ADDING_MODULES.md          # Anleitung: Neue Module erstellen
│   └── GOLDEN_STANDARDS.md        # Golden Standard Konzept
│
├── golden_standards/              # Referenz-Antworten (JSON)
├── benchmark_scores/              # Ergebnisse (CSV, Leaderboard)
└── outputs/                       # Logs & Details
```

---

## 3. Zentrale Konfiguration (`benchmark_config.yaml`)

### 3.1 Golden Standard Definition

```yaml
golden_standard:
  provider: "mistral"              # Referenz zu providers.commercial.mistral
  model: "mistral-large-latest"    # Spezifisches Modell
  description: "Mistral Large als stabile Referenz"
```

**Wichtig:**
- Nur **ein** Golden Standard möglich (strukturell durch Design)
- Wiversion: "0.9.0-rc"
  
  ux_writing:
    version: "1.0.0"

  documentation_quality:
    version: "1.0.0"
    
  content_transformation:
    version: "0.9.0-beta"
    
  reasoning:
    version: "0.5.0-beta"
    
  political_compass:
    version: "3.0.0"
```

---

## 4. Roadmap & Next Steps

### ✅ Completed
- [x] **Benchmark Engine Hardening (v0.9.5)**:
    - [x] **Performance Ratio**: Normalisierung für faire Vergleichbarkeit.
    - [x] **Documentation Quality**: Modul technisch validiert.
    - [x] **Validation Report**: Qwen (104%) & Dolphin Recovery (55%) bestätigt.
- [x] **Hardening & Validation (v0.9.4)**:
    - [x] **Scoring Logic**: Strict 40% keyword match & 0.78 semantic similarity threshold.
    - [x] **UX Writing**: Asset-Specific Ratios (100% false-positive free).
    - [x] **Verification**: Validated with `dolphin-llama3:8b` (38% score confirmed as accurate).
- [x] **Core Framework** (Runner, Config, Utils, CLI Menu)
- [x] **Project Hygiene & Operations** (New v0.9.2):
    - [x] **Smart Cleanup**: Automated log retention (N latest runs per model)
    - [x] **Backup Workflow**: `make backup` archives and auto-cleans workspace
    - [x] **Config UX**: Reorganized `benchmark_config.yaml` for better usability
- [x] **Political Compass 3.0 (Final)**:
    - [x] **Qualitative Results**: Archetypes instead of Scores (Tier format)
    - [x] **Pipeline**: Shared CSV output for Leaderboard & standalone detailed CSV
    - [x] **Recovery**: Added `recover_pc_results.py` to restore data from logs
    - [x] **Consistency**: Enforced 3-pass auditing per model
- [x] **Cost & Token Tracking**:
    - [x] Integrated real-time cost calculation (Input/Output) for commercial providers
    - [x] "Coins per Run" & "Tokens per Run" metrics in Leaderboard
    - [x] Budget protection (Daily Limits)
- [x] **Robustness**:
    - [x] **Smart Rate Limit Handling**: Automatic pause & linear/exponential backoff (429 detection)
    - [x] **Data Safety**: Automated Backups & Git Versioning for Benchmark Scores
- [x] **Hybrid Model Classification**: Gen 1-3 Categorization (Heuristics & Overrides)
- [x] **Entertainment Mode**: Streaming "Thinking" Output for Reasoning Models
- [x] **Completed Modules** (All Tiered & Production Ready):
    - [x] Code Quality (5 Assets)
    - [x] UX Writing (5 Assets)
    - [x] Documentation Quality (5 Assets)
    - [x] Content Transformation (6 Assets)
    - [x] Reasoning Logic (River Crossing, Deadlocks)
    - [x] Political Compass (Anti-Diplomat Prompting, Consistency-Check, Extremism Detection)
- [x] **Golden Standard**: Mistral Integration & Leaderboard Sync
- [x] **Reproducibility**: Random Seed 42

### 🚧 In Progress: Path to Version 1.0.0
- [ ] **Module Refactoring (Modules 1-6)**:
    - [ ] Anpassung an neuen Modulstandard (Ordnerstruktur).
    - [ ] **Code Quality** Refactoring
    - [ ] **UX Writing** Refactoring
    - [ ] **Documentation Quality** Refactoring
    - [ ] **Content Transformation** Refactoring
    - [ ] **Cultural Intelligence** Refactoring
    - [ ] **Reasoning Logic** Refactoring
- [ ] **Calibration Phase**:
    - [ ] Fine-tuning aller Module für konsistente Ergebnisse.
    - [ ] Scoring-Schwellenwerte validieren.
- [ ] **Pre-Release Testing**:
    - [ ] **Commercial Benchmark Run**: Full run mit Mistral, Claude, OpenAI nach Refactoring.
    - [ ] **Local Benchmark Run**: Test mit ausgewählten lokalen Modellen zwecks Regression Testing.
- [ ] **Documentation**:
    - [ ] Finalisierung aller Modul-READMEs.

### 🔮 Planned
- [ ] **Reporting Dashboard**: Visualisierung der Ergebnisse (Streamlit/Dash)
- [ ] **HuggingFace Leaderboard Integration**: Automatischer Upload der Ergebnisse
- [ ] **Custom Model Support**: Unterstützung für lokale GGUF-Files ohne Ollama

