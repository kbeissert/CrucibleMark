# CrucibleMark

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Version](https://img.shields.io/badge/Version-0.5.0--beta-orange.svg)](CHANGELOG.md)
[![Ollama](https://img.shields.io/badge/Ollama-Compatible-green.svg)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Modulares Benchmarking-Framework** zum Testen und Vergleichen von lokalen und kommerziellen LLMs mit gestaffelter Schwierigkeit.

## 📖 Einstieg & Überblick

CrucibleMark ist ein Framework, um die Fähigkeiten von Large Language Models (LLMs) systematisch zu testen. Anders als reine "Vibe-Checks" nutzt dieses Projekt strukturierte Test-Assets mit definierten Scoring-Kriterien.

Einen verständlichen Überblick über die Testszenarien für Nicht-Techniker findest du hier:
👉 **[Benchmark Szenarien & Erklärungen](docs/BENCHMARK_SCENARIOS.md)**

Detaillierte Architektur-Informationen und den aktuellen Projektstatus findest du hier:
👉 **[Projekt-Status & Architektur](PROJECT_STATUS.md)**

## 🎯 Features

*   **Modulare Architektur**: Tests sind in unabhängige Module gekapselt.
*   **Tiered Difficulty System**: Assets enthalten Fehler in 4 Schwierigkeitsstufen (Labeled, Standard, Advanced, Expert), um Junior- von Senior-Modellen zu unterscheiden.
*   **Hybrid Scoring**: Kombination aus quantitativer Bewertung (Keyword/Regex) und qualitativer Analyse (Semantische Ähnlichkeit).
*   **Reproduzierbarkeit**: Fixierte Seeds und deterministische Prompts für vergleichbare Ergebnisse.

## 📦 Benchmark Module

Jedes Modul deckt spezifische Fähigkeiten ab und verfügt über eine eigene, detaillierte Dokumentation.

| ID | Modul Name | Beschreibung | Details |
| :--- | :--- | :--- | :--- |
| `code_quality` | **Code Quality** | Statische Analyse, Security & Best Practices | [README](benchmark_modules/code_quality/README.md) |
| `ux_writing` | **UX Writing** | Microcopy, Accessibility & User Flow | [README](benchmark_modules/ux_writing/README.md) |
| `documentation_quality` | **Documentation** | Technische Dokumentation & Struktur | [README](benchmark_modules/documentation_quality/README.md) |
| `content_transformation` | **Content Adaption** | Format-Transformation & Stil-Anpassung | [README](benchmark_modules/content_transformation/README.md) |
| `reasoning` | **Reasoning Logic** | Logik, Deduktion & Deadlock-Erkennung | [README](benchmark_modules/reasoning_logic/README.md) |

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

1.  Kopiere `.env.example` zu `.env` und trage deine API-Keys ein (falls kommerzielle Modelle genutzt werden).
2.  Kopiere `config_local.yaml.example` zu `config_local.yaml`, um lokale Pfade anzupassen.

### 3. Benchmark Ausführen

Der einfachste Weg ist der interaktive Modus:

```bash
make benchmark
```

Weitere Befehle:
*   `make leaderboard` - Generiert eine Bestenliste aus den Ergebnissen.
*   `make validate` - Prüft die Integrität aller Test-Assets.

## 📚 Weitere Dokumentation

*   [Hinzufügen neuer Module](docs/ADDING_MODULES.md)
*   [Architektur-Details](docs/ARCHITECTURE.md)
*   [Golden Standards Guide](docs/GOLDEN_STANDARDS.md)
