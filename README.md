# CrucibleMark

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Version](https://img.shields.io/badge/Version-0.2.0--beta-orange.svg)](CHANGELOG.md)
[![Ollama](https://img.shields.io/badge/Ollama-Compatible-green.svg)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Modulares Benchmarking-Framework** zum Testen und Vergleichen von lokalen und kommerziellen LLMs mit gestaffelter Schwierigkeit.

## 🎯 Features

*   **Modulare Architektur**: Tests sind in unabhängige Module gekapselt (z.B. `code_quality`).
*   **Tiered Difficulty System**: Assets enthalten Fehler in 3 Schwierigkeitsstufen (Labeled, Standard, Advanced), um Junior- von Senior-Modellen zu unterscheiden.
*   **Hybrid Scoring**: Kombination aus quantitativer Bewertung (Keyword/Regex) und qualitativer Analyse (Semantische Ähnlichkeit zu Golden Standards).
*   **Dual Runner**:
    *   **Local Runner**: Testet lokale Modelle via Ollama.
    *   **Commercial Runner**: Testet API-Modelle (Mistral, Claude, OpenAI) und generiert Golden Standards.

## ⚡ Quick Start

### 1. Installation

```bash
# Repository klonen
git clone https://github.com/yourusername/crucible-mark.git
cd crucible-mark

# Virtual Environment erstellen
python3 -m venv .venv
source .venv/bin/activate

# Abhängigkeiten installieren
pip install -r requirements.txt
```

### 2. Konfiguration

```bash
# Environment-Variablen einrichten (für API-Keys)
cp .env.example .env
# -> Bearbeite .env und füge deine Keys ein (MISTRAL_API_KEY etc.)

# Optional: Lokale Config-Overrides
cp config_local.yaml.example config_local.yaml
```

### 3. Benchmark ausführen

**Interaktiver Modus (Empfohlen):**
```bash
make benchmark
```

**Spezifische Runner:**
```bash
# Nur lokale Modelle (Ollama)
make benchmark-local

# Nur kommerzielle Modelle (oder Golden Standard Generierung)
make benchmark-commercial
```

## 📦 Test-Module

### Code Quality Module (`test_modules/code_quality`)

Dieses Modul prüft die Fähigkeit eines LLMs, Code-Reviews durchzuführen. Es nutzt 5 Assets mit gestaffelter Schwierigkeit:

| Asset | Fokus | Schwierigkeit |
| :--- | :--- | :--- |
| **001 WCAG Audit** | Barrierefreiheit (HTML/CSS) | Tiered (1-3) |
| **002 Security Audit** | OWASP Top 10 (PHP) | Tiered (1-4) |
| **003 Performance** | Core Web Vitals (JS/HTML) | Tiered (1-3) |
| **004 API Design** | REST Principles | Tiered (1-4) |
| **005 Code Smells** | Refactoring Patterns | Tiered (1-3) |

**Schwierigkeits-Level:**
1.  **Labeled (Easy)**: Fehler sind durch TODOs/Kommentare markiert.
2.  **Standard (Medium)**: Offensichtliche Fehler (z.B. SQL Injection, Blocking CSS).
3.  **Advanced (Hard)**: Subtile Logikfehler, Architektur-Probleme oder Edge Cases.
4.  **Expert (Very Hard)**: Komplexe Business-Logik-Fehler (IDOR, Race Conditions) für Top-Tier Modelle.

## 📊 Bewertungsskala (v3.0)

Aufgrund der gehärteten Assets (Level 4) gelten neue Maßstäbe für die Alltagstauglichkeit:

*   **🏆 > 85% (Weltklasse / Expert)**: Für Modelle wie Gemini 3, Claude 3.5 Opus. Versteht komplexe Zusammenhänge.
*   **⭐ > 70% (Production Ready)**: Der "Sweet Spot" für starke lokale Modelle (z.B. Mistral Large). Alltagsfähig und verlässlich.
*   **✓ > 55% (Competent)**: Brauchbar für Standard-Aufgaben und als Assistenz.
*   **⚠️ < 55% (Limited)**: Nicht für kritische Audits empfohlen.

## 🏆 Golden Standards

Das Framework nutzt "Golden Standards" als Referenz. Diese werden von High-End-Modellen (z.B. Mistral Large, Claude 3.5 Sonnet) generiert.

*   **Speicherort**: `golden_standards/<provider>/<model>/`
*   **Format**: Vollständige JSON-Antworten der Referenz-Modelle.
*   **Vergleich**: Lokale Modelle werden semantisch gegen diese Referenzen geprüft (via `sentence-transformers`).

## 🛠 Projektstruktur

```
crucible-mark/
├── benchmark_config.yaml       # Zentrale Konfiguration (Module, Provider)
├── run_benchmark.py            # Haupt-Einstiegspunkt
├── .env                        # API Keys (nicht im Git)
├── test_modules/               # Die eigentlichen Tests
│   └── code_quality/
│       ├── test.py             # Test-Logik
│       └── assets/             # YAML-Test-Definitionen
├── scripts/                    # Runner-Skripte
│   ├── run_local_benchmark.py
│   └── run_commercial_benchmark.py
├── golden_standards/           # Referenz-Antworten (JSON)
└── outputs/                    # Ergebnisse (CSV, Logs)
```

## 🤝 Contributing

Neue Test-Module können einfach hinzugefügt werden:
1.  Ordner in `test_modules/` erstellen.
2.  `test.py` (erbt von `BaseTest`) implementieren.
3.  `assets/` mit YAML-Dateien füllen.
4.  Modul in `benchmark_config.yaml` registrieren.

## 📄 License

MIT
