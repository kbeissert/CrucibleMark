# CrucibleMark

[![Version](https://img.shields.io/badge/version-3.4.7-blue)](.)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](.)
[![License](https://img.shields.io/badge/license-MIT-green)](.)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)](.)

## Ein modulares LLM-Benchmark-Framework für Product Engineers

Akademische Benchmarks wie MMLU messen, was Modelle wissen. CrucibleMark misst, was sie können – dort, wo es für Product Engineers zählt: Code-Qualität, UX-Schreiben, logisches Schlussfolgern und politischer Bias.

Anstatt starrer akademischer Metriken setzt CrucibleMark auf manuell verifizierte Golden Standards und ein kalibriertes LLM-Judge-System. Das Ergebnis ist keine Rangliste der beliebtesten Modelle. Es ist eine ehrliche Antwort auf die Frage: Wie souverän agiert dieses Modell im produktiven Alltag?

---

## Philosophie

> 🛑 **Für Entwickler:** Vor dem Einstieg in den Code die 4 unumstößlichen Design-Gesetze in [ARCHITECTURE.md](docs/ARCHITECTURE.md) lesen. (TL;DR: Keine God-Scripts, Keine Magic Numbers, DRY & Separation of Concerns).

Die meisten Benchmarks fokussieren sich auf rein theoretische Prüfungen. CrucibleMark testet die **gelebte Realität**:
- ✅ **Code Quality:** Kann die KI Code wie ein Senior Engineer auditieren?
- ✅ **CLI Operations:** Agiert sie als verlässlicher Kommandozeilen-Agent?
- ✅ **Reasoning & Logik:** Bewältigt sie Paradoxa und logische Stress-Tests?
- ✅ **UX Writing:** Versteht sie die feinen Nuancen von Microcopy?
- ✅ **Cultural Intelligence:** Begreift sie Idiome, Kontexte und kulturelle Feinheiten?
- ✅ **Political Bias & Safety:** Welches Weltbild spiegelt sie wider? Handelt es sich um eine starre Filterblase ("Schaf im Schafspelz"), oder maskiert sie radikale Shifts ("Wolf im Schafspelz")?

---

## Features

* **LLM-as-a-Judge Architektur:** Ein dediziertes Sub-System delegiert die semantische Bewertung der Antworten an hochperformante Judges (wie `claude-haiku-4.5` oder lokale Modelle).
* **Multi-Provider Support:** Volle Unterstützung für lokale, datenschutzkonforme Ausführung via **Ollama** sowie cloud-basierte kommerzielle Modelle (Mistral, Anthropic Claude, OpenAI, Google Gemini, xAI).
* **SSOT 3-CSV Data Architecture:** Isolierte Logik und trennscharfes Logging von Local VRAM, Cloud Open-Weights Proxies und kommerziellen API-Modellen.
* **Ausfallsicherheit & Checkpointing:** Block-Level-Checkpointing sichert den Fortschritt bei Budget-Erschöpfung, Rate Limits (429) oder Verbindungsabbrüchen. Der Run setzt auf den Token genau dort weiter, wo er endete.
* **Erweiterte Refusal-Architektur:** Das Framework erkennt Zensur und "I cannot answer this"-Verweigerungen eigenständig, erhöht progressiv die Temperatur und streicht Hard-Refusals aus der Wertung.
* **Automatisierter Safety-Shift Test:** Bei starken Abweichungen in Verhaltensfiltern triggert das System vollautomatisch einen verschärften Triple-Run Outlier-Check inklusive euklidischem Clustering.
* **Umfassendes Audit-Logging & Meta-Reviews:** Jede Frage, jeder Prompt und jede LLM-Entscheidung landet in granularen Markdown-Reports. Ein kalibriertes Meta-Review-LLM liest diese Logs zusammen mit technischen API-Limits ein und verfasst halluzinationsfreie Endberichte – gestützt auf strikte Off-by-one-Anker und Grammatikrestriktionen.
* **Token-Budget-System:** Für definierte Benchmark-Module (z. B. `cultural_intelligence`, `code_quality`) wird ein `max_tokens`-Cap als direkter API-Parameter gesetzt, um Provider-übergreifende Vergleichbarkeit herzustellen. Reasoning-Module (`reasoning_logic`) sind bewusst ausgenommen und laufen ohne Output-Limit. Die Budgets sind in `benchmark_config.yaml` unter `token_budgets` kalibrierbar.
* **Token-Verbrauch im Leaderboard:** Beide Leaderboard-CSVs weisen `Tokens Total` aus — die kumulierte Output-Token-Summe über alle bewerteten Benchmark-Module (identische Basis wie der Total Score). Das Detailed-Leaderboard enthält zusätzlich eine Aufschlüsselung pro Modul (`Tokens: Code Quality`, `Tokens: UX Writing`, …). Für API-Nutzer (Pay-per-Token) ist dies die entscheidende zweite Kostendimension neben `Cost per 1K (USD)`.

---

## Installation & Quickstart

### Voraussetzungen
- MacOS / Linux / Windows (WSL)
- Python 3.10+
- Ollama (für den lokalen Modus)

### 1. Repository klonen und einrichten
```bash
git clone https://github.com/kbeissert/cruciblemark.git
cd cruciblemark
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Provider konfigurieren
Konfigurationsvorlagen kopieren und API-Schlüssel **ausschließlich** in einer lokalen `.env`-Datei hinterlegen.
Provider nach Bedarf in der zentralen Konfiguration aktivieren oder deaktivieren (z. B. `providers.commercial` oder `providers.open_weights_cloud`):
```bash
cp benchmark_config.example.yaml benchmark_config.yaml
```

### 3. Benchmarks ausführen
CrucibleMark bietet native Kommandos und ein CLI, um exakte Tests durchzuführen:

```bash
# Geführtes UI und interaktive Modulauswahl:
python run_benchmark.py

# Nur lokale Ollama-Modelle testen:
python run_benchmark.py --provider local

# Kommerzielle Modelle testen (inkl. automatischem Refusal-Tracking):
python run_benchmark.py --provider commercial

# Einzelnes Modul oder Modell erzwingen:
python run_benchmark.py --provider commercial --module political_compass --model gpt-4o

# Dedizierter Shift-Safety Outlier Test (Makefile Alias):
make political-compass-safe
```

### Web-Export-Pipeline

CrucibleMark enthält eine integrierte Export-Pipeline (`scripts/web_export.py`), die sämtliche Benchmark-Ergebnisse als aufbereitetes Datenpaket für das externe Frontend-Projekt `cruciblemark-web` bereitstellt.

**Model Cards & Provider Cards** sind strukturierte JSON-Steckbriefe, die per LLM generiert werden und Entwickler, Herkunftsland, Datenschutz-Metadaten und eine Sovereign-Risk-Einschätzung enthalten. Sie fließen als Kontext in den Meta-Reviewer ein und stehen dem Web-Frontend als eigenständige JSON-API zur Verfügung.

```bash
make model-cards      # Model Cards generieren (fehlende)
make provider-cards   # Provider Cards generieren (fehlende)
```

**Was exportiert wird:**
- `leaderboard.json` — globale Rangliste (Quelle: Leaderboard-CSV als SSOT)
- `models/<slug>/data.json` — Scores und Modul-Details pro Modell
- `models/<slug>/comparisons/` — redaktionelle Meta-Reviews (`docs/reviews/`)
- `models/<slug>/audit_logs/` — **sanitierte** Einzeltest-Protokolle: Prompt (die Anfrage ans Modell), Modellantwort und Modul-Metriken

Die Judge-Auswertung (Scores, Rubriken, Golden-Standard-Referenzen) wird vor dem Export entfernt. Sie fließt ausschließlich in die Meta-Review-Artikel ein, wo sie redaktionell verdichtet und kontextualisiert wird.

**Vollständiger Rebuild:** Jeder Export-Lauf löscht `models/` komplett und baut alles neu auf — der Export ist damit immer synchron mit der Leaderboard-CSV.

```bash
# Export in konfigurierten Ausgabeordner (benchmark_config.yaml → output.web_export_dir)
make web-export

# Direkter Export ins Development-Frontend (11ty, schreibt nach src/_data/raw/)
make web-export-dev
```

---

## Roadmap (Stand: Q1/Q2 2026)

Viele der einst geplanten Fundamental-Features (wie *Reasoning*, *Cultural Intelligence* und tiefe *Sicherheitsarchitekturen*) sind im Core implementiert. So geht es als Nächstes weiter:

- [ ] **Agentic Workflow Benchmarks:** Native Tests für Multi-Step Tool-Usage (Welches Modell plant komplexe File-Edits am sichersten?).
- [ ] **Visuelles Sub-System (Multimodal):** Integration visueller Benchmarks zur Architekturanalyse (UML-Diagramm lesen, UI designen).
- [ ] **Web-UI / Dashboard:** Eine interaktive React- oder Streamlit-Umgebung zur Visualisierung der CSV-Output-Ergebnisse und Leaderboards.
- [ ] **Erweiterung von CI/CD System-Hooks:** Automatische Integration für GitHub Actions, um KI-Akteure in Pull Requests zu prüfen.

---

## Dokumentations-Hub

Tiefergehende Einblicke in die Methodik findest du im `docs/` Verzeichnis:
- [Methodik & Political Compass Shift Concept](docs/POLITICAL_COMPASS_KONZEPT.md)
- [Architektur des Systems](docs/ARCHITECTURE.md)
- [Developer Guide (Eigene Module bauen)](docs/DEVELOPER_GUIDE.md)

---

## Kontakt & Maintainer

- **Maintainer:** kbeissert
- **Repository:** [github.com/kbeissert/cruciblemark](https://github.com/kbeissert/cruciblemark)
- **Status:** ✅ Production-Ready (v3.4.4)
