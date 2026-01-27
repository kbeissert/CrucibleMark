# System-Architektur

CrucibleMark ist als modulares Framework konzipiert, um Erweiterbarkeit und Wartbarkeit zu gewährleisten.

## Kern-Komponenten

### 1. Orchestrator (`run_benchmark.py`)
Der zentrale Einstiegspunkt. Er:
*   Lädt die Konfiguration (`benchmark_config.yaml`).
*   Entdeckt verfügbare Module und Provider.
*   Führt den interaktiven Wizard oder den automatisierten Modus aus.
*   Delegiert die Ausführung an die spezifischen Runner.

### 2. Module System (`benchmark_modules/`)
Jedes Test-Szenario ist ein eigenständiges Modul. Ein Modul kapselt:
*   **Logik**: `test.py` (Test-Klasse). Komplexere Module können weitere Files (z.B. `models.py`, `services.py`) enthalten.
*   **Daten**: `assets/*.yaml` (Test-Fälle).
*   **Konfiguration**: `config.yaml` (Metadaten).

Siehe [ADDING_MODULES.md](ADDING_MODULES.md) für Details zur Erstellung neuer Module.

### 3. Provider Layer (`utils/provider_clients.py`)
Abstrahiert die Kommunikation mit verschiedenen LLM-Backends:
*   **OllamaClient**: Für lokale Modelle (via `ollama` Python-Lib).
*   **CommercialClients**: Für APIs (Mistral, Anthropic, OpenAI).

### 4. Scoring Engine
Bewertet die Antworten der Modelle.
*   **Standard-Module**: Hybrid-Ansatz. Kombiniert Regex/Keyword-Matching mit semantischer Ähnlichkeit (Embedding-Vergleich).
    *   **Semantic Similarity**: Implementiert in `utils/similarity.py` (nutzt `sentence-transformers`).
    *   **Golden Standard**: Vergleich mit High-End-Referenzen.
*   **Political Compass**: Verwendet ein spezialisiertes Scoring (v3.0). Statt "Richtig/Falsch" wird die ideologische Position (Economic/Social Axis) ermittelt und ein Archetyp (z.B. "Links-Liberal") zugewiesen. Die Ergebnisse werden gemittelt aus 3 Durchläufen pro Modell.

---

## Datenfluss

1.  **Initialisierung**: User startet `make benchmark`.
2.  **Selektion**: User wählt Modul (z.B. `code_quality`) und Modell (z.B. `mistral-large`).
3.  **Loading**: Framework lädt `CodeQualityTest` Klasse und YAML-Assets.
4.  **Execution**:
    *   Für jedes Asset wird ein Prompt generiert.
    *   Der Provider-Client sendet den Prompt an das LLM.
    *   Die Antwort wird empfangen und gespeichert.
5.  **Scoring**:
    *   Die Antwort wird gegen definierte Kriterien (Keywords) geprüft.
    *   Falls vorhanden, wird sie mit dem Golden Standard verglichen (via `utils/similarity.py`).
7.  **Fehlerbehandlung**:
    *   Der `utils/retry_handler.py` fängt Netzwerkfehler und spezifische API-Rate-Limits (HTTP 429) ab. Bei Rate Limits pausiert das System intelligent (Start: 60s) mit exponentiellem Backoff, um den Benchmark-Lauf nicht zu gefährden.
8.  **Reporting**:
    *   **Commercial Runs**: Ergebnisse landen in `benchmark_scores/commercial_models_benchmark.csv`.
    *   **Local Runs**: Ergebnisse landen in `benchmark_scores/local_models_benchmark.csv`.
    *   **Golden Standard Runs**: Ergebnisse werden **doppelt** gespeichert:
        *   In `benchmark_scores/golden_standard_benchmark.csv` (als Referenz).
        *   In `benchmark_scores/commercial_models_benchmark.csv` (für das Leaderboard).
    *   **Leaderboard**: Das Skript `generate_leaderboard.py` nutzt `utils/csv_recovery.py` zur robusten Datenaufbereitung und aggregiert die Ergebnisse in `benchmark_scores/benchmark_leaderboard.csv`. Es berechnet dabei Meta-Metriken (Routine vs. Reasoning) und verleiht Badges.

---

## Verzeichnis-Struktur

```
crucible-mark/
├── benchmark_config.yaml   # Zentrale Registry für Module & Provider
├── run_benchmark.py        # CLI Entrypoint
├── Makefile                # Shortcuts (install, benchmark, validate)
│
├── docs/                   # Dokumentation
│
├── benchmark_modules/      # Plugin-Container
│
├── benchmark_scores/       # Output: CSV Ergebnisse & Leaderboard
│
├── utils/                  # Hilfsfunktionen
│   ├── llm_client.py       # Unified LLM Client
│   ├── csv_recovery.py     # Robust CSV Parsing & Repair
│   ├── provider_clients.py # Provider Implementierungen
│   ├── model_utils.py      # Filter-Logik
│   └── similarity.py       # Semantic Scoring
│
└── scripts/                # Helper Scripts
    ├── generate_leaderboard.py # Badge & Rank Generation
    └── ...
```
