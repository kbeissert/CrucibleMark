# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.10] - 2026-01-30

### Reasoning v2.3 - The "Phi4" Patch & Leaderboard Fix

**Release Date:** 2026-01-30
**Status:** ✅ PRODUCTION-READY

#### **Core Fixes**
*   **Leaderboard Logic**: Implemented definitive Tier Weighting in `generate_leaderboard.py`.
    *   Tier 1 (Basic): 1.0x
    *   Tier 2 (Advanced): 1.5x
    *   Tier 3 (Expert): 2.0x
*   **Scorer Robustness**: Fixed regex extraction to handle "Feasibility: 0" cases where the denominator "/10" is missing (specifically fixing `phi4` scoring 0%).
*   **Contradiction Logic**: Relaxed keyword penalties in `Tier2_Systems` to prevent false positives on phrases like "solution is feasible".

#### **Developer Experience**
*   **Debug Mode**: Added `--debug-responses` flag to `run_local_benchmark.py` which auto-saves full LLM responses for low-performing tests (<30%).
*   **System Reset**: Wiped reasoning scores from CSVs to enforce a clean re-run with the patched evaluators.

## [0.9.9] - 2026-01-30

### Reasoning v2.2 - Anti-Ceiling Effect Release (Final)

**Release Date:** 2026-01-30  
**Status:** ✅ PRODUCTION-READY

#### **Mission Accomplished**
*   **Ceiling Effect Eliminated**: 0 models @ 100% (was 3).
*   **Score Differentiation**: Range increased to 35pp (Mistral 73% vs Dolphin 38%).
*   **Inverse Hierarchy Fixed**: Mistral > Gemma > Dolphin validated.

#### **New Features & Improvements**
*   **New Expert Asset (5e_001)**: "Nested Transaction Paradox".
    *   Testet Distributed Systems Constraints.
    *   Multi-Dimensional Scoring (Analysis + Solution + Depth).
    *   Result: Mistral Large 35% (Realistic Expert Scope).
*   **Enhanced Physics Trap (5c_001)**:
    *   New **Bidirectional Negation Detection** (15+ keywords).
    *   Context-aware analysis prevents false positives on constraint repetition.
*   **Hardened Deadlock Detection (5d_001)**:
    *   Parametric feasibility extraction.
    *   3-Signal requirement (Feasibility + Keyword + Explanation).

#### **Fixed Bugs (Critical)**
1.  **Asset-ID Mismatch**: Fixed underscore bug (`reasoning_5d_001`).
2.  **Feasibility Extraction**: Added 9 new regex patterns & bidirectional search.
3.  **Negation Logic**: Fixed unidirectional check failing on "using X is forbidden".
4.  **False Positives**: Fixed penalty for repeating "no machinery allowed".

#### **Validation Results**
*   **Mistral Large**: 73.3% (Overall) - 100% on 5c/5d.
*   **Gemma2:9b**: 58.9% (Overall) - Hidden Champion.
*   **Dolphin:8b**: 37.9% (Overall) - Correctly placed at bottom.

## [0.9.8] - 2026-01-30

### Reasoning v2.2 - Anti-Ceiling Effect Release

#### **Major Changes**
*   **Module Upgrade**: Reasoning Logic Modul auf **v2.2** aktualisiert.
    *   Ziel: Eliminierung des "Ceiling Effects" (zu viele Modelle bei 100%).
    *   Ergebnis: Score-Spreizung von 30pp auf 45pp erhöht.
    *   Status: **Production-Ready**.

#### **New Features & Improvements**
*   **New Expert Asset (5e_001)**: "Nested Transaction Paradox".
    *   Testet Distributed Systems Constraints (CAP-Theorem Style).
    *   Multi-Dimensional Scoring (Analysis, Solution, Depth).
    *   Nur Top-Tier Modelle (Mistral Large) erreichen hier 100%.
*   **Dynamic Feasibility Extraction**:
    *   Regex-Engine erweitert (9 Patterns statt 3).
    *   Erkennt Robust Formulierungen wie "Feasibility Assessment: 2/10".
    *   Fallback-Logik verbessert (Default=7 statt 5 für Fairness).
*   **Hardened Physics Trap (5c_001)**:
    *   Strikte Prüfung für "Mount Everest" Szenario.
    *   Creative Workarounds (Schrumpfstrahl etc.) geben keine Punkte mehr.
*   **Hardened Deadlock Detection (5d_001)**:
    *   Erfordert nun 3 Signale: Feasibility=0 + Keyword "Deadlock" + Erklärung.

#### **Fixed**
*   **Asset-ID Bug**: Korrektur eines kritischen Bugs im `ReasoningEvaluator`, bei dem Asset-IDs durch Underscore-Removal falsch gemappt wurden (`reasoning5d001` vs `reasoning_5d_001`). Dies führte zu 0% Scores bei korrekten Antworten.
*   **Scoring-Logik**: Diverse Stabilisierungsmaßnahmen in der Punktevergabe.

## [0.9.7] - 2026-01-30

### Robustness & Automation Hardening

#### Added
- **Pre-flight Checks**: `benchmark_auto.py` führt nun vor dem Start von kommerziellen Tests einen Zugriffstest durch.
- **Provider Accessibility**: Neue `is_accessible()` Methode in `LLMClient` und Provider-Klassen.
  - Erkennt "Insufficient Quota" / "Credit Limit" Fehler bei OpenAI/Anthropic vorab.
  - Verhindert Endlosschleifen und unnötige API-Calls bei leeren Accounts.

#### Changed
- **Error Handling**: Automatisches Überspringen von konfigurierten, aber nicht nutzbaren Providern (statt Abbruch).

## [0.9.6] - 2026-01-29

### Metacognition & RCI Update

#### Added
- **Tier 3 (Metacognition)**: Neues Test-Level im `reasoning_logic` Modul.
  - Prüft die Fähigkeit zur **Selbstkorrektur** ("The Sheep Trap").
  - Prüft das **Infragestellen falscher Prämissen** ("The Green Sky").
  - 5 neue Assets (`METACOG_001` bis `METACOG_005`).
- **RCI (Reasoning Complexity Index)**: Neue Metrik (0-100%).
  - Berechnet sich aus: `(Avg_Tier1_2 * 0.6) + (Avg_Tier3 * 0.4)`.
  - Unterscheidet zwischen "Non-Thinking" (<50%), "Basic Thinking" (50-70%) und "Deep Thinking" (>85%).
- **<think> Tag Parsing**: Unterstützung für Reasoning-Traces in `<think>` oder `<thought>` Tags (kompatibel mit DeepSeek R1).

#### Changed
- **Reasoning Logic Module**: Upgrade auf v2.0.0.
- **Scoring Engine**: Hybrid-Ansatz für robuste Bewertung (Keywords + Struktur-Analyse + Trajectory Detection).

#### Fixed
- **YAML Schema**: Fehlerhafte `dimensions` Struktur in den Metacognition-Assets behoben.

## [0.9.5] - 2026-01-28

### Cultural Intelligence Module (Complete)

#### Added
- **Asset 6D (Formal vs. Informal)**: New test for register switching (Sie -> Du)
- **Asset 6E (German Idioms)**: New test for cultural translation of idioms (e.g. "went south")

#### Improved
- **Asset 6C (Berlin Agency Vibe)**: 
  - Fixed false positives by removing 'lösung' (solution) and 'ganzheitlich' (holistic)
  - Scoring optimized to 9 buzzwords
- **Scoring Logic**:
  - Hardened checks for Asset 6D (requires frequent 'Du' usage)
  - Expanded accepted variants for Asset 6E (idioms)

#### Impact
- **DeepSeek**: 100% on Cultural Vibe (Matches Reference)
- **Dolphin**: 90% on Formal/Informal (Impressive register switch)
- **Robustness**: Improved discrimination between pure translation and cultural adaptation

## [0.9.4-rc2] - 2026-01-27

### Fixed
- **Expert Tier Enforcement**: Expert issues now require 100% keyword coverage (exact OR semantic)
- **Semantic Threshold**: 0.55 threshold now applied to each missing keyword individually
- **Impact**: Qwen Sarcasm Shield score corrected from unrealistic 100% → realistic 86%

### Technical Details
- Missing keywords in Expert tier must pass semantic similarity check (threshold: 0.55)
- Other tiers (Labeled/Standard/Advanced) remain at 0.45 threshold
- Prevents false positives from paraphrasing (e.g., "exceeded SLA thresholds" vs "SLA breach")

## [0.9.4-rc] - 2026-01-27

### Security & Hardening (Critical Update)
- **Scoring-Härtung:** Umfassende Überarbeitung der Code-Quality-Bewertung, um "Optimierungs-Bias" und "Lucky Hits" zu eliminieren.
  - **Keyword-Matching:** Schwellenwert auf **40%** wiederhergestellt (statt 1 Match). Verhindert, dass unscharfe Synonyme zu vollen Punkten führen.
  - **Semantic Similarity:** Threshold von `0.65` auf **0.78** erhöht, um semantische Matches strikter zu validieren.
  - **Keyword-Bereinigung:** Reduktion von Keyword-Listen (z.B. "God Object" von 11 auf 5 primäre Fachbegriffe), um Spamming zu verhindern.
  - **Asset-Specific Validation:** Strengere Anforderungen an Tabellen-Struktur für WCAG (min 10 Zeilen) und Security Audits (min 8 Zeilen).

### Features
- **Local Model Optimization:** Spezielle Anpassungen für Modelle wie `dolphin-llama3`, die deutsche Antworten mit englischen Fachbegriffen mischen.
  - Assets unterstützen nun hybride (DE/EN) Keyword-Erkennung ohne Aufweichung der Kriterien.
- **Framework:** `run_benchmark.py` unterstützt vollständig entkoppelte Modul-Architektur via `benchmark_config.yaml`.

## [0.5.0-beta] - 2026-01-17

### Added
- **Gamified Badges:** Automatische Kategorisierung von Modellen im Leaderboard:
  - 👑 **God Mode:** Hohe Routine & Reasoning Scores (>85/80).
  - 🏎️ **Daily Driver:** Stark im Alltag (Routine >80).
  - 🧠 **Deep Thinker:** Stark in Logik (Reasoning >80).
  - ⚠️ **Needs Tuning:** Modelle unterhalb der Schwellenwerte.
- **Meta-Metrics:**
  - **Routine Score:** Basierend auf Tier 1 Aufgaben (Standard).
  - **Reasoning Score:** Basierend auf Tier 2 Aufgaben (Advanced Logic).
  - **Efficiency Index:** Score pro Sekunde Ausführungszeit.
- **Utils:** Neues Modul `utils/csv_recovery.py` für robuste Reparatur von defekten LLM-Output-CSVs.

### Changed
- **Refactoring:**
  - `scripts/generate_leaderboard.py` komplett modularisiert und DRY-konform umgebaut.
  - CSV-Parsing-Logik (Heuristiken) in eigenes Utility-Modul ausgelagert.
  - Pylint Score des Leaderboard-Skripts auf 9.6 verbessert.
- **Reporting:** Leaderboard zeigt nun gruppierte Tabellen basierend auf Badges statt einer flachen Liste.

## [0.3.4-beta] - 2025-12-29

### Added
- **Content Transformation Module:** Neues Modul für Format-Adaption und Stil-Transfer (5 Assets).
- **Reproducibility:** `random_seed=42` für deterministische LLM-Outputs (Mistral/Ollama).
- **Hardened Assets:**
  - `documentation_quality`: Assets 003 (Props) und 005 (Changelog) deutlich verschärft.
  - `code_quality`: Asset 005 (Code Smells) Punkteverteilung optimiert (Fokus auf Expert Issues).

### Changed
- **Scoring System:**
  - `documentation_quality`: Error Detection Gewichtung auf 100 Punkte erhöht.
  - `code_quality` & `ux_writing`: Standardisiert auf 60/30/10 (ED/SQ/FM).
- **Documentation:**
  - `BENCHMARK_SCENARIOS.md` um Content Transformation erweitert.
  - `ARCHITECTURE.md` aktualisiert (Fallback-Logik für Semantic Similarity).
  - `README.md` Status-Tabellen aktualisiert.

### Fixed
- **Scoring Logic:** Bug in `base_test.py` behoben, der Scores >100 Punkte verhinderte (jetzt dynamisch basierend auf YAML).
- **Indentation:** Syntax-Fehler in `documentation_quality/test.py` behoben.

## [0.2.0-beta] - 2025-12-27

### Added
- **Tiered Difficulty System:** Alle Code Quality Assets (001-005) unterstützen nun 3 Schwierigkeitsstufen:
  - **Labeled (Easy):** Fehler sind durch Kommentare markiert.
  - **Standard (Medium):** Offensichtliche Fehler.
  - **Advanced (Hard):** Subtile Logik- oder Architekturfehler.
- **Hybrid Scoring:** Kombination aus Keyword/Regex-Matching und Semantic Similarity (via `sentence-transformers`) für präzisere Bewertungen.
- **Configuration Management:**
  - `.env.example` mit ausführlichen Kommentaren.
  - `config_local.yaml.example` für lokale Overrides.
  - `golden_standard_models.yaml.example` Template.
- **Project Cleanup:**
  - Entfernung von `_backup_old/` und alten CSV-Dateien.
  - Bereinigung von `outputs/runs/`.
  - Aktualisierte `.gitignore`.

### Changed
- **Documentation:**
  - Root `README.md` komplett überarbeitet.
  - `PROJECT_STATUS.md` auf v0.2.0 aktualisiert.
  - `docs/` Dateien an neue Architektur angepasst.
- **Asset Refactoring:** Alle 5 Code Quality Assets wurden auf das neue Schema migriert.

## [2.0.0] - 2025-12-27

### Added
- **Unified Configuration:** Zentrale `utils/ollama_config.py` mit `BENCHMARK_OPTIONS`
  - `temperature=0.1` für deterministisches Scoring
  - `seed=42` für Reproduzierbarkeit
  - `num_predict=2000`, `top_k=10`, `repeat_penalty=1.0`
- **Multi-Run-Support:** `--runs N` Parameter in `run_benchmark.py`
  - Automatische Statistik-Berechnung (Avg, Median, Std-Dev, Min/Max)
  - Coefficient of Variation (CV) zur Stabilitäts-Bewertung
  - Separate Output-Files pro Run (z.B. `code_quality_001_run1.json`)
- **Stability Testing Suite:** Neues Script `scripts/test_stability.py`
  - 5 Runs zur Varianz-Messung
  - CSV + Markdown Reports mit CV-Metriken
  - Qualitäts-Assessment (🟢/🟡/🔴)
- **Dokumentation:**
  - `QUICKSTART.md` - 5-Minuten Quick Start
  - `UNIFIED_FRAMEWORK.md` - Vollständige Architektur-Dokumentation
  - `STATUS_UPDATE.md` - Was in v2.0 implementiert wurde
  - README mit Badges, realistischen Beispielen, Erwartungstabellen

### Changed
- **LLMClient:** Nutzt jetzt zentrale `BENCHMARK_OPTIONS` aus `ollama_config.py`
- **BaseTest:** `save_result()` unterstützt optionalen `output_file`-Parameter
- **CSV-Format:** Erweitert um `run_1_score`, `run_2_score`, `run_3_score`, `avg_score`, `median_score`, `std_dev`, `min_score`, `max_score`, `cv_percent`
- **Makefile:** Neue Targets `test-stability`, aktualisiertes `help`
- **Progress Bar:** Zeigt "Run 2/3 for model" bei Multi-Runs
- **print_summary():** Unterstützt `avg_score` (Multi-Run) und `total_score` (Single-Run)

### Fixed
- **Score Variance:** Reduziert von 26.67 auf 7.67 Punkte (-71%)
- **Standard Deviation:** Reduziert von 11.4 auf 3.2 (-72%)
- **Coefficient of Variation:** Reduziert von 13.7% auf 3.8% (-72%)
- **Execution Time:** Verbessert von 87s auf 52s (-35%)

### Deprecated
- **Alte Systeme:** `writing_benchmark_with_claude.py` und `run_political_compass_test.py` nach `_backup_old/` verschoben
- Diese nutzen nicht die neuen Stability-Features (temperature=default)

### Known Issues
- ⚠️ Multi-Run: Bei `--runs 5` kann letzter Run timeout bei Ollama-Restart
- ⚠️ Golden Standard: Claude API rate-limits bei >10 Assets/Minute
- ⚠️ Windows: Symlinks (`latest/`) funktionieren nur mit Admin-Rechten
- ⚠️ CSV-Export: Bei sehr langen Modell-Namen (>50 Zeichen) kann Spalten-Alignment brechen

## [1.0.0] - 2025-12-26

### Added
- **Code Quality Test v2.0.0:** WCAG 2.2 Accessibility Audit
  - 11 Accessibility-Issues
  - 4 Scoring-Kategorien (Error Detection 45p, Solution Quality 30p, Formatting 15p, Expertise 10p)
  - Flexible Keyword-Matching mit 40% Threshold
- **Golden Standard System:**
  - Integration mit Claude 3.5 Sonnet (92-98/100 Baseline)
  - `generate_golden_standard.py` mit Multi-Provider-Support
  - `golden_standards_scores.csv` für Tracking
- **Unified LLM Client:** `utils/llm_client.py`
  - Ollama-Support (alle lokalen Modelle)
  - Anthropic Claude API
  - Unified Interface für beide Provider
- **Benchmark-Runner:** `scripts/run_benchmark.py`
  - Interaktiver Modus (`interactive_benchmark.py`)
  - CSV-Export mit allen Metriken
  - Progress Bars mit tqdm
  - Symlink `latest/` für neuesten Run
- **Cleanup System:** `scripts/cleanup_runs.py`
  - Automatisches Löschen alter Runs
  - `--keep N` Parameter (default: 5)
  - Dry-run Mode mit Größenanzeige
- **Makefile:** Automation-Targets
  - `run-benchmark`, `generate-golden`, `clean-runs`
  - Virtual Environment Support (`.venv/`)
- **Test-Asset-Struktur:**
  - YAML-basierte Asset-Definitionen
  - Metadata, Test-Data, Golden-Standard-Config
  - Validierungs-System
- **BaseTest Framework:**
  - Abstract Base Class für alle Tests
  - `execute()`, `score_response()`, `compare_to_golden_standard()`
  - Automatische JSON/Markdown Report-Generierung

### Changed
- Projektstruktur refactored:
  - `test_modules/` für Test-Code
  - `scripts/` für CLI-Tools
  - `utils/` für Core-Libraries
- Python 3.11+ als Minimum (Type Hints, moderne Syntax)

### Fixed
- Progress Bar Overlap mit Output-Messages (tqdm.write())
- 4 Bugs in `run_benchmark.py` (response key, category_scores, golden_path, base_test.py)
- Base Test category_scores Format (von `categories` zu `category_scores`)

### Known Issues (Fixed in 2.0.0)
- ❌ Hohe Score-Varianz (20-30%) bei default temperature
- ❌ Keine Multi-Run-Support
- ❌ Keine zentrale Configuration
- ❌ Keyword-Matching zu strikt (fixed 2 keywords erforderlich)

## [0.9.0] - 2025-12-25 (Pre-Release)

### Added
- Initial Project Setup
- Writing Benchmark System (später nach `_backup_old/` verschoben)
- Political Compass Test (später nach `_backup_old/` verschoben)
- Basic Ollama Integration

### Known Issues
- Hohe Score-Varianz (20-30%) bei default temperature
- Keine Multi-Run-Support
- Keine zentrale Configuration

---

## Migration Guide

### v1.0 → v2.0

**Für Nutzer:**
```bash
# Alte Single-Run-Befehle funktionieren weiterhin
python scripts/run_benchmark.py --models qwen2.5:14b --category code_quality

# Neu: Multi-Run für robuste Ergebnisse
python scripts/run_benchmark.py --models qwen2.5:14b --category code_quality --runs 3
```

**CSV-Format-Änderungen:**
- v1.0: `total_score`
- v2.0: `avg_score`, `median_score`, `std_dev`, `run_1_score`, `run_2_score`, `run_3_score`

**Für Entwickler:**
```python
# utils/llm_client.py nutzt jetzt:
from utils.ollama_config import BENCHMARK_OPTIONS

# Keine manuelle temperature mehr nötig!
response = ollama.chat(model=model, messages=[...], options=BENCHMARK_OPTIONS)
```

---

## Future Roadmap

### v2.1.0 (Q1 2026)
- [ ] Semantic Similarity Matching (statt Keyword-based)
- [ ] LLM-as-Judge für ambige Fälle
- [ ] Web-Dashboard für Ergebnis-Visualisierung
- [ ] CI/CD Integration (GitHub Actions)

### v3.0.0 (Q2 2026)
- [ ] UX Writing Test-Kategorie
- [ ] Technical Documentation Test
- [ ] Mistral API Integration
- [ ] OpenAI GPT-4 Integration
- [ ] Google Gemini Integration
- [ ] Multi-Language Support (EN/DE)

---

## Contributing

Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für Details zu:
- Code-Style (Black, Type Hints)
- Testing-Requirements
- Pull Request Process

## License

MIT License - siehe [LICENSE](LICENSE)
