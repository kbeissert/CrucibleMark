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
*   **Logik**: `test.py` (Test-Klasse).
*   **Daten**: `assets/*.yaml` (Test-Fälle).
*   **Konfiguration**: `config.yaml` (Metadaten).

Siehe [ADDING_MODULES.md](ADDING_MODULES.md) für Details zur Erstellung neuer Module.

### 3. Provider Layer (`utils/provider_clients.py`)
Abstrahiert die Kommunikation mit verschiedenen LLM-Backends:
*   **OllamaClient**: Für lokale Modelle (via `ollama` Python-Lib).
*   **CommercialClients**: Für APIs (Mistral, Anthropic, OpenAI).

### 4. Scoring Engine (`scoring/`)
Bewertet die Antworten der Modelle.
*   **Hybrid-Ansatz**: Kombiniert Regex/Keyword-Matching mit semantischer Ähnlichkeit (Embedding-Vergleich).
*   **Golden Standard**: Vergleicht lokale Antworten mit Referenz-Antworten von High-End-Modellen.

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
    *   Falls vorhanden, wird sie mit dem Golden Standard verglichen.
6.  **Reporting**: Ergebnisse werden als CSV in `benchmark_results/` gespeichert.

---

## Verzeichnis-Struktur

```
crucible-mark/
├── benchmark_config.yaml   # Zentrale Registry für Module & Provider
├── run_benchmark.py        # CLI Entrypoint
├── Makefile                # Shortcuts (install, benchmark, validate)
│
├── docs/                   # Dokumentation
│   ├── ARCHITECTURE.md     # Diese Datei
│   ├── ADDING_MODULES.md   # Developer Guide
│   └── ...
│
├── benchmark_modules/      # Plugin-Container
│   ├── code_quality/       # Modul 1
│   └── ux_writing/         # Modul 2
│
├── utils/                  # Hilfsfunktionen
│   ├── llm_client.py       # Veraltet (Refactored)
│   ├── provider_clients.py # Neue Client-Struktur
│   └── model_utils.py      # Filter-Logik
│
└── scripts/                # Helper Scripts
    ├── validate_assets.py  # CI/CD Check
    └── list_models.py      # Status Check
```
