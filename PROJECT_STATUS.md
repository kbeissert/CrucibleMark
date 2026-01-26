# CrucibleMark - Projekt-Status & Architektur

**Version:** 0.9.2-beta
**Datum:** 26. Januar 2026
**Status:** Pre-Commercial Beta - Refactoring & Hardening

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
│   │   ├── test.py
│   │   ├── config.yaml
│   │   ├── README.md
│   │   └── assets/ (5 Assets)
│   │
│   ├── ux_writing/                # ✅ UX Writing & Microcopy
│   │   ├── ...
│   │
│   ├── documentation_quality/     # ✅ Documentation Quality
│   │   ├── ...
│   │
│   ├── content_transformation/    # ✅ Content Adaption
│   │   ├── ...
│   │
│   ├── reasoning_logic/           # ✅ Reasoning & Logic
│   │   ├── ...
│   │
│   └── political_compass/         # ✅ Political Compass (Bias Check)
│       ├── test.py
│       ├── config.yaml
│       ├── README.md
│       ├── models.py              # Extended Module Architecture
│       ├── services.py
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
    version: "0.9.5-beta"

  documentation_quality:
    version: "0.9.5-beta"
    
  content_transformation:
    version: "0.9.0-beta"
    
  reasoning:
    version: "0.5.0-beta"
    
  political_compass:
    version: "2.0.0"
```

---

## 4. Roadmap & Next Steps

### ✅ Completed
- [x] **Core Framework** (Runner, Config, Utils, CLI Menu)
- [x] **Project Hygiene & Operations** (New v0.9.2):
    - [x] **Smart Cleanup**: Automated log retention (N latest runs per model)
    - [x] **Backup Workflow**: `make backup` archives and auto-cleans workspace
    - [x] **Config UX**: Reorganized `benchmark_config.yaml` for better usability
- [x] **Political Compass 2.0 (Refactoring)**:
    - [x] **Clean Architecture**: Separation into `core/`, `assets/`, `scripts/`
    - [x] **Asset Audit**: Complete review and tightening of questionnaire assets
    - [x] **Scoring Update**: Revised calculation logic for higher precision
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

### 🚧 In Progress
- [ ] **Semantic Similarity**: Fix dependency conflict (torch vs sentence-transformers)
- [ ] **Reporting Dashboard**: Visualisierung der Ergebnisse (Streamlit/Dash)
- [ ] **More Modules**:
    - [ ] Security Auditing (Advanced)
    - [ ] Architecture Design

### 🔮 Planned
- [ ] **HuggingFace Leaderboard Integration**: Automatischer Upload der Ergebnisse
- [ ] **Custom Model Support**: Unterstützung für lokale GGUF-Files ohne Ollama

