# CrucibleMark 🚀

[![Version](https://img.shields.io/badge/version-3.3.0-blue)](.)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](.)
[![License](https://img.shields.io/badge/license-MIT-green)](.)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)](.)

## A Modular LLM Benchmark Framework for Product Engineers

Akademische Benchmarks wie MMLU messen, was Modelle wissen. CrucibleMark misst, was sie können – dort, wo es für Product Engineers zählt: Code-Qualität, UX-Schreiben, logisches Schlussfolgern und politischer Bias.

Anstatt starrer akademischer Metriken setzt CrucibleMark auf manuell verifizierte Golden Standards und ein kalibriertes LLM-Judge-System. Das Ergebnis ist keine Rangliste der beliebtesten Modelle. Es ist eine ehrliche Antwort auf die Frage: Wie souverän agiert dieses Modell im produktiven Alltag?

---

## 🎯 Philosophie

> 🛑 **WICHTIG (Für Entwickler):** Bevor du an diesem Code arbeitest, lies unbedingt die 4 unumstößlichen Design-Gesetze in [ARCHITECTURE.md](docs/ARCHITECTURE.md). (TL;DR: Keine God-Scripts, Keine Magic Numbers, DRY & Separation of Concerns).

Die meisten Benchmarks fokussieren sich auf rein theoretische Prüfungen. CrucibleMark testet die **gelebte Realität**:
- ✅ **Code Quality:** Kann die KI Code wie ein Senior Engineer auditieren?
- ✅ **CLI Operations:** Agiert sie als verlässlicher Kommandozeilen-Agent?
- ✅ **Reasoning & Logik:** Bewältigt sie Paradoxa und logische Stress-Tests?
- ✅ **UX Writing:** Versteht sie die feinen Nuancen von Microcopy?
- ✅ **Cultural Intelligence:** Begreift sie Idiome, Kontexte und kulturelle Feinheiten?
- ✅ **Political Bias & Safety:** Welches Weltbild spiegelt sie wider? Handelt es sich um eine starre Filterblase ("Schaf im Schafspelz"), oder maskiert sie radikale Shifts ("Wolf im Schafspelz")?

---

## 🚀 Key Features

* **LLM-as-a-Judge Architektur:** Ein dediziertes Sub-System delegiert die semantische Bewertung der Antworten an hochperformante Judges (wie `claude-haiku-4.5` oder lokale Modelle).
* **Multi-Provider Support:** Volle Unterstützung für lokale, datenschutzkonforme Ausführung via **Ollama** sowie cloud-basierte kommerzielle Modelle (Mistral, Anthropic Claude, OpenAI, Google Gemini, xAI).
* **SSOT 3-CSV Data Architecture:** Isolierte Logik und trennscharfes Logging von Local VRAM, Cloud Open-Weights Proxies und kommerziellen API-Modellen.
* **Ausfallsicherheit & Checkpointing:** Block-Level-Checkpointing sichert den Fortschritt bei Budget-Erschöpfung, Rate Limits (429) oder Verbindungsabbrüchen. Der Run setzt auf den Token genau dort weiter, wo er endete.
* **Erweiterte Refusal-Architektur:** Das Framework erkennt Zensur und "I cannot answer this"-Verweigerungen eigenständig, erhöht progressiv die Temperatur und streicht Hard-Refusals aus der Wertung.
* **Automatisierter Safety-Shift Test:** Bei starken Abweichungen in Verhaltensfiltern triggert das System vollautomatisch einen verschärften Triple-Run Outlier-Check inklusive euklidischem Clustering.
* **Umfassendes Audit-Logging & Meta-Reviews:** Jede Frage, jeder Prompt und jede LLM-Entscheidung landet in granularen Markdown-Reports. Ein kalibriertes Meta-Review-LLM liest diese Logs zusammen mit technischen API-Limits ein und verfasst halluzinationsfreie Endberichte – gestützt auf strikte Off-by-one-Anker und Grammatikrestriktionen.

---

## 🛠 Installation & Quickstart

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
Kopiere die Konfigurations-Vorlagen und hinterlege deine API-Schlüssel **ausschließlich** in einer lokalen `.env` Datei.
Aktiviere oder deaktiviere die gewünschten Provider in der zentralen Konfiguration (z. B. `providers.commercial` oder `providers.open_weights_cloud`):
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

### 🌐 Web Export Pipeline

CrucibleMark enthält einen integrierten Export, der sämtliche Benchmark-Ergebnisse (CSVs) sowie Audit- und Review-Markdowns als aufbereitetes JSON-Datenmodell aggregiert. Die Ausgabe versorgt das externe Frontend-Projekt `cruciblemark-web` dynamisch mit Ergebnisdaten und generierten Metadaten.

```bash
# Basis-Export (schreibt standardmäßig sicher nach ./web_export/raw/)
make web-export

# Direkter Export ins Development-Frontend (11ty, schreibt nach src/_data/raw/)
make web-export-dev
```

---

## 🗺️ Roadmap (Stand: Q1/Q2 2026)

Viele der einst geplanten Fundamental-Features (wie *Reasoning*, *Cultural Intelligence* und tiefe *Sicherheitsarchitekturen*) sind im Core implementiert. So geht es als Nächstes weiter:

- [ ] **Agentic Workflow Benchmarks:** Native Tests für Multi-Step Tool-Usage (Welches Modell plant komplexe File-Edits am sichersten?).
- [ ] **Visuelles Sub-System (Multimodal):** Integration visueller Benchmarks zur Architekturanalyse (UML-Diagramm lesen, UI designen).
- [ ] **Web-UI / Dashboard:** Eine interaktive React- oder Streamlit-Umgebung zur Visualisierung der CSV-Output-Ergebnisse und Leaderboards.
- [ ] **Erweiterung von CI/CD System-Hooks:** Automatische Integration für GitHub Actions, um KI-Akteure in Pull Requests zu prüfen.

---

## 📂 Dokumentations-Hub

Tiefergehende Einblicke in die Methodik findest du im `docs/` Verzeichnis:
- [Methodik & Political Compass Shift Concept](docs/POLITICAL_COMPASS_KONZEPT.md)
- [Architektur des Systems](docs/ARCHITECTURE.md)
- [Developer Guide (Eigene Module bauen)](docs/DEVELOPER_GUIDE.md)

---

## 📧 Kontakt & Maintainer

- **Maintainer:** kbeissert
- **Repository:** [github.com/kbeissert/cruciblemark](https://github.com/kbeissert/cruciblemark)
- **Status:** ✅ Production-Ready (v3.3.0)
