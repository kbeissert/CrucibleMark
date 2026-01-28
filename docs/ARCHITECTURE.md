# System Architecture (Core/MVC)

Standard: **Version 0.9.6 (Unified MVC)**

CrucibleMark nutzt eine strikt modulare Architektur, um LLM-Benchmarks reproduzierbar, erweiterbar und wartbar zu halten.

---

## 🏗 High-Level Übersicht

```
       +-------------------+
       |   Orchestrator    |  run_benchmark.py
       | (CLI / Config)    |
       +---------+---------+
                 |
        +--------v--------+
        |   BaseTest      |  Inheritance Base
        +--------+--------+
                 |
      +----------v-----------+    +-----------------------+
      |  Specific Module     |    |   External Services   |
      |  (Controller)        |    |                       |
      |  /code_quality/      +--->+  - LLM Clients        |
      |  test.py             |    |  - Provider APIs      |
      +----------+-----------+    +-----------------------+
                 |
      +----------v-----------+
      |  Core Evaluator      |    <-- PURE LOGIC (No IO)
      |  (Model/Logic)       |
      |  /core/evaluators.py |
      +----------------------+
```

---

## 🧩 Komponenten-Detail

### 1. Der Orchestrator (Root Layer)
*   **`run_benchmark.py`**: Liest die CLI-Argumente und startet den Prozess.
*   **`benchmark_config.yaml`**: Die zentrale "Registry". Hier werden Module aktiviert, LLM-Provider konfiguriert und Pfade gesetzt.
*   **`utils/module_loader.py`**: Lädt Test-Klassen dynamisch zur Laufzeit ("Plugin System").

### 2. Der Controller Layer (`benchmark_modules/*/test.py`)
Jedes Modul hat eine `test.py`. Diese Datei agiert als **Controller**:
*   Erbt von `BaseTest`.
*   Lädt die Assets (`assets/*.yaml`).
*   Sendet den Prompt via `utils.llm_client` an das LLM.
*   Empfängt die "Raw Response".
*   Übergibt die Antwort an den Evaluator.
*   **Wichtig:** Der Controller enthält *keine* Bewertungslogik!

### 3. Der Logic Layer (`benchmark_modules/*/core/`)
Hier findet die eigentliche Arbeit statt. Dieser Layer ist isoliert und testbar.
*   **`evaluators.py`**: Enthält Klassen wie `CodeQualityEvaluator` oder `ReasoningEvaluator`.
    *   Input: Raw String (LLM Output) + Asset Config.
    *   Output: Score (0-100) + Details (JSON).
    *   Features: Think-Tag-Removal, Keyword-Matching (Regex), Semantic Scoring.
*   **`constants.py`**: Enthält Schwellenwerte, Regex-Pattern und statische Listen (z.B. "Banned Words").

### 4. Der Provider Layer (`utils/`)
Abstrahiert die Außenwelt.
*   **`llm_client.py`**: Einheitliches Interface (`.generate()`) für alle Modelle.
*   **`provider_clients.py`**: Spezifische Adapter für Ollama, Mistral, OpenAI, Anthropic.
*   **`similarity.py`**: Berechnet Embedding-Vektoren für semantische Vergleiche (genutzt von Evaluatoren).

---

## 🔄 Datenfluss (Execution Flow)

Ein typischer Benchmark-Lauf für ein Asset:

1.  **Load**: `CodeQualityTest` lädt "Asset 001" (YAML).
2.  **Prompt**: Controller baut Prompt + Kontext zusammen.
3.  **Generate**: Sende an `OllamaClient` -> LLM generiert Antwort -> Return String.
4.  **Evaluate**:
    *   Controller ruft `CodeQualityEvaluator.evaluate(response_string)` auf.
    *   Evaluator entfernt `<think>` Tags.
    *   Evaluator prüft Keywords (Hard Check).
    *   Evaluator ruft `utils.similarity` für Semantic Check (Soft Check).
    *   Evaluator berechnet gewichteten Score.
5.  **Record**: Controller erhält Resultat-Dict zurück und schreibt CSV-Zeile.

---

## 📁 File Structure Standard

```
benchmark_modules/
    module_name/
        test.py              # Controller
        config.yaml          # Metadata
        README.md            # Docs
        assets/              # Data
        core/                # Isolation Layer
            __init__.py
            evaluators.py    # Logic
            constants.py     # Config
```
