# CrucibleMark - Projekt-Status & Architektur

**Version:** 0.3.0-beta
**Datum:** 27. Dezember 2025
**Status:** Beta - Expert Level (Tier 4) implementiert, Qwen3 Support gefixt

---

## 1. Projekt-Übersicht

### Zweck
Framework zum systematischen Benchmarking von **lokalen** (Ollama) und **kommerziellen** (Mistral, Claude, GPT) Large Language Models anhand strukturierter Test-Module.

### Kernkonzepte
1.  **Modular Architecture**: Plugin-basiertes System - neue Test-Module einfach hinzufügbar
2.  **Tiered Difficulty (1-4)**: Assets enthalten Fehler in 4 Schwierigkeitsstufen (Labeled, Standard, Advanced, Expert)
3.  **Hybrid Scoring**: Kombination aus quantitativer Bewertung (Keyword/Regex) und qualitativer Analyse (Semantische Ähnlichkeit zu Golden Standards)
4.  **Golden Standard**: Ein kommerzielles Referenz-Modell als Vergleichsmaßstab für lokale Modelle
5.  **Multi-Provider**: Unterstützt Ollama, Mistral AI, Anthropic, OpenAI

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
│   └── run_commercial_benchmark.py      # Benchmark-Runner für kommerzielle LLMs
│                                        # (Zwei Modi: Golden Standard / Test)
│
├── test_modules/                  # ⭐ TEST-MODULE (Plugin-System)
│   └── code_quality/              # ✅ Erstes vollständiges Modul
│       ├── test.py                # CodeQualityTest Klasse (erbt von BaseTest)
│       ├── config.yaml            # Modul-Metadaten
│       ├── README.md              # Modul-Dokumentation
│       └── assets/                # 5 YAML Test-Assets (Tiered Difficulty 1-4)
│           ├── 001_wcag_audit.yaml
│           ├── 002_security_audit.yaml
│           ├── 003_performance_audit.yaml
│           ├── 004_api_design_audit.yaml
│           └── 005_code_smells_audit.yaml
│
├── utils/
│   ├── llm_client.py              # Unified LLM Provider Wrapper
│   ├── config_validator.py        # Golden Standard Validierung
│   ├── module_loader.py           # Dynamic Module Loading
│   └── scoring/                   # Scoring Logic (Hybrid)
│
├── docs/
│   ├── ADDING_MODULES.md          # Anleitung: Neue Module erstellen
│   └── GOLDEN_STANDARDS.md        # Golden Standard Konzept
│
├── golden_standards/              # Referenz-Antworten (JSON)
├── outputs/                       # Ergebnisse (CSV, Logs)
│
└── _backup_old/                   # Alte Files vor Refactoring
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
- Wird als Referenz für alle lokalen Benchmark-Vergleiche genutzt
- Generiert separate CSV: `golden_standard_benchmark.csv`

### 3.2 Module Registry

```yaml
modules:
  code_quality:
    name: "Code Quality Audit"
    description: "Umfassende Code-Qualitätsanalyse"
    path: "test_modules/code_quality"
    test_class: "CodeQualityTest"
    version: "0.2.0"
    enabled: true
    assets_count: 5
    tags: [quality, security, performance, accessibility]
```

### 3.3 Provider Configuration

```yaml
providers:
  commercial:
    mistral:
      name: "Mistral AI"
      api_type: "mistral"
      enabled: true
      env_var: "MISTRAL_API_KEY"
      models:
        - id: "mistral-large-latest"
          name: "Mistral Large (123B)"
    
    anthropic:
      enabled: true
      env_var: "ANTHROPIC_API_KEY"
      models: [...]
    
    openai:
      enabled: true
      env_var: "OPENAI_API_KEY"
      models: [...]
  
  local:
    ollama:
      api_type: "ollama"
      auto_discover: true  # Modelle werden dynamisch abgefragt
```

---

## 4. Test-Modul Architektur

### 4.1 Modul-Struktur (Code Quality Beispiel)

```
test_modules/code_quality/
│
├── test.py                  # Test-Klasse (Hauptlogik)
├── config.yaml              # Metadaten
├── README.md                # Dokumentation
│
└── assets/                  # Test-Cases
    └── 001_wcag_audit.yaml
        ├── name: "WCAG 2.2 Audit (Tiered Difficulty)"
        ├── category: "accessibility"
        ├── code: |                # Fehlerhafter Code
        │     <button onclick="...">
        ├── expected_findings:     # Was das LLM finden soll
        │   - "Missing ARIA labels"
        │   - "Poor keyboard navigation"
        └── scoring:
            ├── error_detection: 45  # Max-Punkte
            ├── solution_quality: 30
            ├── formatting: 15
            └── expertise: 10
```

### 4.2 Tiered Difficulty System

Jedes Asset enthält Fehler in 3 Schwierigkeitsstufen:

1.  **Labeled (Easy)**: Fehler sind durch TODOs oder Kommentare markiert.
2.  **Standard (Medium)**: Offensichtliche Fehler (z.B. SQL Injection, Blocking CSS).
3.  **Advanced (Hard)**: Subtile Logikfehler, Architektur-Probleme oder Edge Cases.

### 4.3 Bewertungssystem (Hybrid Scoring)

#### Kategorien (Code Quality):

| Kategorie | Max | Beschreibung |
|-----------|-----|--------------|
| **Error Detection** | 45 | Wie viele Probleme wurden erkannt? (Keyword/Regex) |
| **Solution Quality** | 30 | Qualität der Lösungsvorschläge (Semantic Similarity) |
| **Formatting** | 15 | Strukturierung der Antwort |
| **Expertise** | 10 | Tiefe des technischen Verständnisses |

---

## 5. Benchmark-Ablauf

### 5.1 Interaktives Menü (`run_benchmark.py`)

```
🚀 CRUCIBLE MARK v0.2.0-beta
============================================================

📦 VERFÜGBARE TEST-MODULE
  1. Code Quality Audit (5 Assets)

Wähle Modul (1): 1
✓ Code Quality Audit

🌐 PROVIDER-AUSWAHL
  1. Kommerzielle Modelle (Mistral, Claude, GPT)
  2. Lokale Modelle (Ollama)

Wähle Provider (1-2): 2
✓ Lokale Modelle

🖥️ LOKALE OLLAMA-MODELLE
  1. qwen3-vl:8b (5.7 GB)
  2. ministral-3:8b (5.6 GB)
  3. ministral-3:14b (8.5 GB)
  ...

Wähle Modell (1-6): 2
✓ ministral-3:8b
```

---

## 6. Golden Standard System

### 6.1 Drei separate CSV-Dateien

| Datei | Zweck | Inhalt |
|-------|-------|--------|
| **golden_standard_benchmark.csv** | Referenz | Nur Mistral Large Scores (5 Assets) |
| **commercial_models_benchmark.csv** | Vergleich | Alle kommerziellen Tests (beliebig viele) |
| **local_models_benchmark.csv** | Evaluation | Lokale Modelle mit Golden Standard Vergleich |

### 6.2 Workflow: Golden Standard generieren

```bash
python scripts/run_commercial_benchmark.py

# Modus wählen:
1. Golden Standard generieren  ← Wähle dies
2. Kommerzielle Modelle testen

# → Mistral Large wird automatisch aus Config geladen
# → Benchmark läuft für 5 Assets
# → Ergebnis: golden_standard_benchmark.csv
```

---

## 7. LLM Client (utils/llm_client.py)

### 7.1 Unified Interface

```python
class LLMClient:
    """Wrapper für alle LLM-Provider."""
    
    def query(self, model: str, prompt: str, provider: str = 'ollama') -> str:
        """Sendet Prompt an LLM, gibt Antwort zurück."""
        
        if provider == 'ollama':
            return self._query_ollama(model, prompt)
        elif provider == 'mistral':
            return self._query_mistral(model, prompt)
        elif provider == 'anthropic':
            return self._query_anthropic(model, prompt)
        elif provider == 'openai':
            return self._query_openai(model, prompt)
```

---

## 8. Bekannte Probleme & Refactoring-Potenzial

### 8.1 Kritische Issues

#### 1. `run_commercial_benchmark.py` ist repariert
**Status:** ✅ Behoben
**Lösung:** Wurde durch `run_commercial_benchmark_new.py` ersetzt und dann in `run_commercial_benchmark.py` umbenannt.

#### 2. String-Matching zu streng
**Status:** ✅ Behoben
**Lösung:** Semantic Similarity mit `sentence-transformers` implementiert.

#### 3. BaseTest-Klasse
**Status:** ✅ Behoben
**Lösung:** `BaseTest` Klasse existiert und wird von `CodeQualityTest` genutzt.

### 8.2 Architektur-Verbesserungen

#### 1. Dynamic Module Loading verbessert
**Status:** ✅ Behoben
**Lösung:** Zentralisiert in `utils/module_loader.py`.

#### 2. Test-Asset Validierung
**Fehlt:** Schema-Validierung für YAML-Assets
**Aktuell:** Keine Prüfung ob `expected_findings`, `scoring` etc. vorhanden
**Lösung:** JSON Schema oder Pydantic Models

#### 3. Parallel Execution
**Aktuell:** Assets werden sequenziell abgearbeitet (5× ~55s = 4:30min)
**Potenzial:** Parallel mit `asyncio` oder `ThreadPoolExecutor`
**Einschränkung:** Rate Limits bei kommerziellen APIs beachten

#### 4. Result Storage
**Aktuell:** Nur CSV
**Potenzial:**
- SQLite für historische Vergleiche
- JSON für detaillierte Logs
- Markdown für Human-Readable Reports

---

## 9. Geplante Module (Roadmap)

### Q1 2026

**UX Writing Module:**
- Assets: Microcopy, Error Messages, Onboarding Texte
- Scoring: Tonality, Clarity, User-Centricity

**Technical Documentation Module:**
- Assets: API Docs, README, Architecture Docs
- Scoring: Completeness, Accuracy, Examples

### Q2 2026

**Reasoning & Logic Module:**
- Assets: Math Problems, Logic Puzzles, Code Refactoring
- Scoring: Correctness, Explanation Quality

---

## 10. Für Entwickler: Quick Start

### 10.1 Neues Test-Modul erstellen

**1. Verzeichnis anlegen:**
```bash
mkdir -p test_modules/my_module/assets
```

**2. Dateien erstellen:**
```
my_module/
├── test.py          # Klasse: MyModuleTest
├── config.yaml      # name, version, description
├── README.md        # Dokumentation
└── assets/
    └── 001_test.yaml
```

**3. In `benchmark_config.yaml` registrieren:**
```yaml
modules:
  my_module:
    name: "My Module"
    path: "test_modules/my_module"
    test_class: "MyModuleTest"
    enabled: true
```

**4. Test-Klasse implementieren:**
```python
class MyModuleTest:
    def __init__(self, asset_path: str):
        self.asset = yaml.safe_load(open(asset_path))
    
    def run(self, llm_response: str) -> Dict:
        return {
            'total_score': 75,
            'max_score': 100,
            'category_scores': {...}
        }
```

**Siehe:** `docs/ADDING_MODULES.md` für Details

### 10.2 Code-Conventions

- **Python Version:** 3.10+
- **Formatting:** Black (Line Length: 100)
- **Type Hints:** Überall wo möglich
- **Docstrings:** Google Style
- **Imports:** Standard → Third-Party → Local
- **Naming:**
  - Files: `snake_case.py`
  - Classes: `PascalCase`
  - Functions: `snake_case`
  - Constants: `UPPER_CASE`

---

## 11. Technische Schulden

### High Priority
1. ✅ Golden Standard System → **ERLEDIGT**
2. ✅ `run_commercial_benchmark.py` reparieren → **ERLEDIGT**
3. ✅ Semantic Similarity statt String-Matching → **ERLEDIGT**
4. ✅ BaseTest Klasse einführen → **ERLEDIGT**
5. ✅ Tiered Difficulty System → **ERLEDIGT**

### Medium Priority
6. 🟡 Unit Tests schreiben
7. 🟡 JSON Schema für Assets
8. ✅ Logging implementieren (in LLMClient) → **ERLEDIGT**

### Low Priority
9. 🟢 Parallel Execution
10. 🟢 SQLite Storage
11. 🟢 Web UI (Flask/FastAPI)

---

## 12. Abhängigkeiten

```toml
[tool.poetry.dependencies]
python = "^3.10"
ollama = "^0.4.6"
mistralai = "^1.2.5"
anthropic = "^0.40.0"
openai = "^1.58.1"
pyyaml = "^6.0.2"
tqdm = "^4.67.1"
pandas = "^2.2.3"
```

**Installation:**
```bash
poetry install
# oder
pip install -r requirements.txt
```

---

## 13. Kontakt & Weiterentwicklung

**Current State:**
- ✅ Modular Architecture funktioniert
- ✅ Code Quality Module vollständig (Tiered Difficulty)
- ✅ Golden Standard System implementiert
- ✅ Lokale + Kommerzielle Benchmarks funktionieren

**Next Steps:**
1. Unit Tests schreiben
2. Weitere Module entwickeln (UX Writing, Tech Docs)

**Für Fragen:** Siehe `docs/` oder README.md

---

**Letzte Aktualisierung:** 27.12.2025
**Version:** 0.2.0-beta
**Status:** Produktionsbereit für Code Quality Tests
