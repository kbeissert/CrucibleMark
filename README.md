# CrucibleMark

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Version](https://img.shields.io/badge/Version-0.9.6--beta-blue.svg)](CHANGELOG.md)
[![Ollama](https://img.shields.io/badge/Ollama-Compatible-green.svg)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **"The Product Engineer's Compass"** – Ein spezielles Benchmarking-Framework für alle, die digitale Produkte nicht nur coden, sondern *erschaffen*.

CrucibleMark ist kein generischer Benchmark wie MMLU oder HumanEval. Er ist ein **Spezialwerkzeug für "Technical Creators"**:  
Die Schnittmenge aus **Product Engineers**, **UX Writern** und **System Architects**, die sicherstellen müssen, dass KI nicht nur "funktioniert", sondern den richtigen Ton trifft, sauberen Code liefert und logisch stabil bleibt.

Von **Code Quality & Accessibility** über **UX Writing & Tone of Voice** bis zu **Complex Reasoning**:  
Dieses Framework ist der "TÜV für digitale Produktentwicklung" – flexibel, modular und erweiterbar wie ein Lego-System für KI-Tests. Jeder Use-Case kann durch eigene Module adaptiert werden.

---

## 📖 Einstieg & Überblick

CrucibleMark ist ein Framework, um die Fähigkeiten von Large Language Models (LLMs) systematisch zu testen. Anders als reine "Vibe-Checks" nutzt dieses Projekt strukturierte Test-Assets mit definierten Scoring-Kriterien.

Einen verständlichen Überblick über die Testszenarien für Nicht-Techniker findest du hier:
👉 **[Benchmark Szenarien & Erklärungen](docs/BENCHMARK_SCENARIOS.md)**

Detaillierte Architektur-Informationen und den aktuellen Projektstatus findest du hier:
👉 **[Projekt-Status & Architektur](PROJECT_STATUS.md)**

## 🎯 Features

*   **Modulare Architektur (Core/MVC)**: Alle Module folgen einem strengen Controller-Evaluator-Pattern. Die Business-Logik (`core/evaluators.py`) ist strikt von der LLM-Ausführung (`test.py`) getrennt.
*   **Tiered Difficulty System**: Assets enthalten Fehler in 4 Schwierigkeitsstufen (Labeled, Standard, Advanced, Expert), um Junior- von Senior-Modellen zu unterscheiden.
*   **Structured Prompting**: Alle kreativen Module (`Code Quality`, `Documentation`, `UX Writing`) erzwingen einen strengen "Analyse-vor-Lösung"-Ablauf, um flüchtige oder fehleranfällige Modelle objektiv vergleichbar zu machen.
*   **Hybrid Scoring**: Kombination aus quantitativer Bewertung (Keyword/Regex) und qualitativer Analyse (Semantische Ähnlichkeit).
*   **Reproduzierbarkeit**: Fixierte Seeds, Rate-Limit-Handling und deterministische Prompts für vergleichbare Ergebnisse.

## 📦 Benchmark Module

Jedes Modul deckt spezifische Fähigkeiten ab.
**NEU:** Welche Module aktiv sind, wird zentral in der `benchmark_config.yaml` gesteuert. Du kannst Module an- oder abschalten, ohne den Code zu ändern.

Die Standard-Module:

| ID | Modul Name | Beschreibung | Details |
| :--- | :--- | :--- | :--- |
| `code_quality` | **Code Quality** | Statische Analyse, Security & Best Practices | [README](benchmark_modules/code_quality/README.md) |
| `ux_writing` | **UX Writing** | Microcopy, Accessibility & User Flow | [README](benchmark_modules/ux_writing/README.md) |
| `documentation_quality` | **Documentation** | Technische Dokumentation & Struktur | [README](benchmark_modules/documentation_quality/README.md) |
| `content_transformation` | **Content Adaption** | Format-Transformation & Stil-Anpassung | [README](benchmark_modules/content_transformation/README.md) |
| `reasoning` | **Reasoning Logic** | Logik, Deduktion & Deadlock-Erkennung | [README](benchmark_modules/reasoning_logic/README.md) |
| `political_compass` | **Political Compass** | Ideological Bias & Extremism Check (v3.0 Logic) | [README](benchmark_modules/political_compass/README.md) |
| `cultural_intelligence` | **Cultural Intelligence** | Kulturelles Verständnis & Sprachnuancen | [README](benchmark_modules/cultural_intelligence/README.md) |

## 🏆 Leaderboard & Metrics

Das Leaderboard klassifiziert Modelle nicht nur nach Punkten, sondern nach Profil:

### 🏅 Gamified Badges
*   👑 **God Mode**: Exzellent in beiden Bereichen (Routine >85% & Reasoning >80%).
*   🏎️ **Daily Driver**: Perfekt für schnelle Standard-Aufgaben (Routine >80%).
*   🧠 **Deep Thinker**: Spezialist für komplexe Logik (Reasoning >80%).
*   ⚠️ **Needs Tuning**: Modelle, die noch Optimierung benötigen.

### 📊 Meta-Metrics
*   **Routine Score (Tier 1)**: Misst die Zuverlässigkeit bei Standard-Aufgaben (Linting, Typos).
*   **Reasoning Score (Tier 2)**: Misst logische Deduktion und Architektur-Verständnis (Deadlocks).

## ⚡ Quick Start

### 1. Installation

```bash
git clone https://github.com/yourusername/crucible-mark.git
make install
```

### 2. Konfiguration

Die zentrale Steuerung erfolgt über **`benchmark_config.yaml`**:

1.  **API Keys & Provider:** Trage Keys in eine `.env` Datei ein und aktiviere Provider in der YAML.
2.  **Module Verwalten:** Unter dem Key `modules:` kannst du Test-Suiten aktivieren/deaktivieren:
    ```yaml
    modules:
      code_quality:
        enabled: true
      political_compass:
        enabled: false  # Modul überspringen
    ```

### 3. Benchmark Ausführen

Der einfachste Weg ist der interaktive Modus:

```bash
make benchmark
```

Weitere Befehle:
*   `make benchmark-auto` - **Overnight Mode**: Führt alle Module auf allen lokalen und kommerziellen Modellen vollautomatisch aus.
*   `make list-models` - Listet alle verfügbaren Modelle (Lokal & API) und prüft die Verbindung ("Ping Test") sowie die API-Keys.
*   `make validate-structure` - Prüft, ob alle Module der definierten Verzeichnisstruktur (`core/`, `assets/`) folgen.
*   `make analyze-costs` - Berechnet die geschätzten Token-Kosten für einen kompletten Benchmark-Durchlauf aller Assets.
*   `make leaderboard` - Generiert eine Bestenliste aus den Ergebnissen.
*   `make validate` - Prüft die Integrität aller Test-Assets.

## 📚 Weitere Dokumentation

*   [Hinzufügen neuer Module](docs/ADDING_MODULES.md)
*   [Architektur-Details](docs/ARCHITECTURE.md)
*   [Modell-Management & Klassifizierung](docs/MODEL_CLASSIFICATION.md) - **Neu:** Wie das Hybrid-System Modelle klassifiziert.
*   [Golden Standards Guide](docs/GOLDEN_STANDARDS.md)
