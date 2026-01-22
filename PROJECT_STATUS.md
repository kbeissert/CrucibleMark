# CrucibleMark - Projekt-Status & Architektur

**Version:** 0.9.0-beta
**Datum:** 23. Januar 2026
**Status:** Pre-Commercial Beta - Local Models Validated

---

## 1. Projekt-Übersicht

### Zweck
Framework zum systematischen Benchmarking von **lokalen** (Ollama) und **kommerziellen** (Mistral, Claude, GPT) Large Language Models anhand strukturierter Test-Module.

### Kernkonzepte
1.  **Modular Architecture**: Plugin-basiertes System - neue Test-Module einfach hinzufügbar
2.  **Tiered Difficulty (1-4)**: Assets enthalten Fehler in 4 Schwierigkeitsstufen (Labeled, Standard, Advanced, Expert)
3.  **Hybrid Scoring**: Kombination aus quantitativer Bewertung (Keyword/Regex) und qualitativer Analyse (Semantische Ähnlichkeit zu Golden Standards)
4.  **Golden Standard**: Ein kommerzielles Referenz-Modell als Vergleichsmaßstab für lokale Modelle
5.  **Reproducibility**: Deterministische Outputs durch Seed-Steuerung (Random Seed 42)

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
│   ├── validate_assets.py               # ✅ Asset-Validierung (Schema & Version)
│   └── debug_ollama.py                  # Debugging Script
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
- [x] Core Framework (Runner, Config, Utils)
- [x] **Hybrid Model Classification**: Gen 1-3 Categorization (Heuristics & Overrides)
- [x] **Entertainment Mode**: Streaming "Thinking" Output for Reasoning Models
- [x] **Data Safety**: Automated Backups & Git Versioning for Benchmark Scores
- [x] **Completed Modules** (All Tiered & Production Ready):
    - [x] Code Quality (5 Assets)
    - [x] UX Writing (5 Assets)
    - [x] Documentation Quality (5 Assets)
    - [x] Content Transformation (6 Assets)
    - [x] Reasoning Logic (River Crossing, Deadlocks)
    - [x] Political Compass (Anti-Diplomat Prompting
- [x] Core Framework (Runner, Config, Utils)
- [x] **Hybrid Model Classification**: Gen 1-3 Categorization (Heuristics & Overrides)
- [x] **Entertainment Mode**: Streaming "Thinking" Output for Reasoning Models
- [x] **Data Safety**: Automated Backups & Git Versioning for Benchmark Scores
- [x] Code Quality Module (5 Assets, Tiered Difficulty, Hardened)
- [x] UX Writing Module (5 Assets, Tiered Difficulty)
- [x] Documentation Quality Module (5 Assets, Tiered Difficulty, Hardened)
- [x] Content Transformation Module (5 Assets, Tiered Difficulty)
- [x] Golden Standard Integration (Mistral) & Leaderboard Sync
- [x] Commercial Provider Support (Anthropic, OpenAI)
- [x] Interactive CLI Menu (`make benchmark`)
- [x] Reproducibility (Random Seed 42)

### 🚧 In Progress
- [ ] **Semantic Similarity**: Fix dependency conflict (torch vs sentence-transformers)
- [ ] **Reporting Dashboard**: Visualisierung der Ergebnisse (Streamlit/Dash)
- [ ] **More Modules**:
    - [ ] Security Auditing (Advanced)
    - [ ] Architecture Design

### 🔮 Planned
- [ ] **HuggingFace Leaderboard Integration**: Automatischer Upload der Ergebnisse
- [ ] **Custom Model Support**: Unterstützung für lokale GGUF-Files ohne Ollama

