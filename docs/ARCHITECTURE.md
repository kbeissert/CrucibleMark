# System Architecture (Core/MVC)

Standard: **Version 0.9.11 (Unified MVC + Granular Scoring)**

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

### 3. Modul-Spezifika

#### reasoning_logic (v2.0.0)
*   **Architektur**: 3-Tier System (Tier 0: Sanity, Tier 1-2: Logic/Systems, Tier 3: Metacognition).
*   **Besonderheit**: Implementiert Parser für `<think>` Tags und berechnet den **RCI**.

---

## 🏗 Granular Scoring System (v3.0)

Eingeführt in Version 0.9.11, ermöglicht dieses System eine feingranulare Zuweisung von Scores auf Asset-Ebene.

### Motivation
Frühere Versionen ordneten ein gesamtes Modul entweder der Kategorie "Routine" oder "Reasoning" zu. Dies war ungenau, da viele Module gemischte Anforderungen haben (z.B. ist ein Security Audit in `code_quality` komplexer als ein Linter-Check).

### Funktionsweise
Statt einer pauschalen Zuordnung definiert nun jedes Asset in der Modul-Konfiguration (`config.yaml`), wie stark es zu den beiden Meta-Scores beiträgt.

1.  **Konfiguration**:
    ```yaml
    benchmarks:
      - id: "asset_001"
        score_contribution:
          routine: 1.0    # 100% Routine
          reasoning: 0.0
      - id: "asset_002"
        score_contribution:
          routine: 0.3    # 30% Routine
          reasoning: 0.7  # 70% Reasoning
    ```

2.  **Laufzeit-Berechnung**:
    Der Benchmark-Runner berechnet *nach jedem Test* sofort die Teil-Scores und speichert sie in den Ergebnis-CSVs (`routine_contribution`, `reasoning_contribution`).

3.  **Aggregation**:
    Das Leaderboard muss keine Business-Logik mehr kennen. Es summiert einfach die Contributions aller Assets.
    `Routine Score = Sum(Routine Contributions) / Count(Assets)`

Dies ermöglicht maximale Flexibilität bei der Gestaltung neuer Module ohne Änderungen am Core-System.

---

## 📐 Benchmark Complexity Tiers

Die Klassifizierung von Benchmarks in Complexity Tiers ist eine fundamentale Strukturkomponente von CrucibleMark. Sie dient als Leitfaden für die Erstellung neuer Assets und steuert perspektivisch Gewichtungsfaktoren im Scoring.

### Tier 1: Surface & Routine
Aufgaben, die primär auf Mustererkennung und gelernter Reproduktion basieren.
*   **Merkmale:** Eindeutige Instruktionen, geschlossener Lösungsraum, Fokus auf Syntax oder Format.
*   **Kognitive Anforderung:** "Fast Thinking" (System 1) - Abruf von Wissen.
*   **Beispiele:** Linter-Checks, Rechtschreibprüfung, einfache Format-Konvertierung, Faktenchecks.
*   **Scoring-Tendenz:** Hoher Anteil an **Routine Score**.

### Tier 2: Logic & Context
Aufgaben, die Multi-Step-Reasoning und tiefes Kontextverständnis erfordern.
*   **Merkmale:** Constraints, die gegeneinander abgewogen werden müssen. Transfer von Regeln auf neue Szenarien.
*   **Kognitive Anforderung:** Logische Schlussfolgerung, Kontext-Erhalt, Anwendung von Regeln.
*   **Beispiele:** Refactoring mit Seiteneffekten, Security Threat Modeling, deduktive Logik-Rätsel, Tonalitätsanpassung.
*   **Scoring-Tendenz:** Balance zwischen Routine und Reasoning.

### Tier 3: Metacognition & Expert
Aufgaben, die Selbstreflexion, Strategiewechsel oder den Umgang mit Paradoxien erfordern.
*   **Merkmale:** Offener Lösungsraum, widersprüchliche Anforderungen, Notwendigkeit zur Selbstkorrektur.
*   **Kognitive Anforderung:** "Slow Thinking" (System 2) - Metakognition, Planungsfähigkeit.
*   **Beispiele:** System-Design architektureller Paradoxien, Erkennung logischer Fallen, komplexe Argumentationsketten.
*   **Scoring-Tendenz:** Dominanter **Reasoning Score**. Assets dieses Tiers sind die Basis für High-Level Reasoning Tests.

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

### 5. Config Management (SSOT v3.1)
Die Konfiguration folgt dem **Kaskadierenden Ansatz**:
*   **Global Toggle (`enable_scoring`):** Nimmt Module komplett aus der Wertung (z.B. Info-Module).
*   **Asset-Level (`score_contribution`):** Spezifische Werte (Routine/Reasoning) überschreiben alles.
*   **Modul-Default (`default_contribution`):** Fallback für alle Assets ohne eigene Definition.

---

## 🔄 Datenfluss (Execution Flow)

Ein typischer Benchmark-Lauf für ein Asset:

1.  **Load**: `CodeQualityTest` lädt "Asset 001" (YAML) und `config.yaml` (Modul-Metadaten).
2.  **Prompt**: Controller baut Prompt + Kontext zusammen.
3.  **Generate**: Sende an `OllamaClient` -> LLM generiert Antwort -> Return String.
4.  **Evaluate**:
    *   Controller ruft `CodeQualityEvaluator.evaluate(response_string)` auf.
    *   Evaluator entfernt `<think>` Tags.
    *   Evaluator prüft Keywords (Hard Check).
    *   Evaluator ruft `utils.similarity` für Semantic Check (Soft Check).
    *   Evaluator berechnet gewichteten Score.
5.  **Score Attribution (Kaskadierung)**: Leaderboard-Generator prüft Asset-Config -> dann Modul-Default -> berechnet `routine`/`reasoning` Anteile.
6.  **Record**: Controller erhält Resultat-Dict zurück und schreibt CSV-Zeile inkl. Contributions.

---

## 📁 File Structure Standard

```
benchmark_modules/
    module_name/
        test.py              # Controller
        config.yaml          # Metadata + Benchmarks Config
        README.md            # Docs
        assets/              # Data
```        core/                # Isolation Layer
            __init__.py
            evaluators.py    # Logic
            constants.py     # Config
```

---

## 📊 Leaderboard Logic (Dynamic & Config-Driven)

Das Leaderboard () ab Version v0.9.6 arbeitet nach dem **Config-First Prinzip**:

1.  **Single Source of Truth**: Die  bestimmt, welche Module existieren und wie sie gewertet werden.
2.  **Score Groups**:
    *   Module mit `score_group: routine` fließen in den **Routine Score** ein (Durchschnitt aller Routine-Module).
    *   Module mit `score_group: reasoning` fließen in den **Reasoning Score** ein.
    *   Module mit `score_group: info` (z.B. Political Compass) werden als Zusatzspalten angezeigt, beeinflussen aber nicht das Ranking.
3.  **Completion Logic**:
    *   Ein Modell gilt als "Pending" (*), wenn es weniger Assets absolviert hat, als die Summe aller `assets_count` der aktiven *Routine* und *Reasoning* Module.
    *   Info-Module blockieren den "Completed"-Status nicht.

---

## 🛠️ Observability & Logging

Das System verfolgt eine **"Silent Console, Noisy Log"** Strategie:

1.  **Console (User Interface)**: 
    *   Fokus auf UX. Zeigt nur High-Level-Status, Fortschritt (Progress Bars) und Ergebnisse.
    *   Filtert Warnungen von Drittanbieter-Bibliotheken (`transformers`, `urllib3`) aktiv heraus, um Benutzer nicht zu verunsichern.

2.  **Log-File (`logs/crucible.log`)**:
    *   Fokus auf Debugging. Speichert alle Events (Level `DEBUG`), inklusive der unterdrückten Warnungen.
    *   Dient als "Black Box" für Post-Mortem-Analysen bei Fehlern.
