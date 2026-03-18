# CrucibleMark 🚀

[![Version](https://img.shields.io/badge/version-3.0.0-blue)](.)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](.)
[![License](https://img.shields.io/badge/license-MIT-green)](.)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)](.)

## A Modular LLM Benchmark Framework for Product Engineers

CrucibleMark ist ein umfassendes Benchmarking-Framework, das entwickelt wurde, um Large Language Models (LLMs) genau dort zu testen, wo es für Product Engineers am wichtigsten ist: Code-Qualität, UX-Schreiben, logisches Schlussfolgern (Reasoning) und der zugrundeliegende Bias (Political Compass Safety).

Anstelle von starren akademischen Metriken (wie MMLU) misst CrucibleMark die echte Arbeitsqualität und die *Souveränität* eines Assistenten im produktiven Alltag.

---

## 🎯 Philosophie

Die meisten Benchmarks fokussieren sich auf rein theoretische Prüfungen. CrucibleMark testet die **gelebte Realität**:
- ✅ **Code Quality:** Kann die KI Code wie ein Senior Engineer auditieren?
- ✅ **CLI Operations:** Agiert sie als verlässlicher Kommandozeilen-Agent?
- ✅ **Reasoning & Logik:** Bewältigt sie Paradoxa und logische Stress-Tests?
- ✅ **UX Writing:** Versteht sie die feinen Nuancen von Microcopy?
- ✅ **Cultural Intelligence:** Begreift sie Idiome, Kontexte und kulturelle Feinheiten?
- ✅ **Political Bias & Safety:** Welches Weltbild spiegelt sie wider? Handelt es sich um eine starre Filterblase ("Schaf im Schafspelz"), oder maskiert sie radikale Shifts ("Wolf im Schafspelz")?

---

## 🚀 Key Features

* **LLM-as-a-Judge Architektur:** Ein fortschrittliches Sub-System delegiert die semantische Bewertung der Antworten an hochperformante Judges (wie `gpt-4o` oder lokale Modelle).
* **Multi-Provider Support:** Volle Unterstützung für lokale, datenschutzkonforme Ausführung via **Ollama**, sowie cloud-basierte kommerzielle Modelle (Mistral, Anthropic Claude, OpenAI, Google Gemini, xAI).
* **Ausfallsicherheit & Checkpointing:** Verliert nie deinen Fortschritt! Durch stetiges Block-Level-Checkpointing kannst du bei Budget-Erschöpfung, API-Limits (Rate Limit, 429) oder Stromausfällen einfach abbrechen und später auf den Token genau dort weitermachen, wo du aufgehört hast.
* **Erweiterte Refusal-Architektur:** Das Framework registriert eigenständig Zensur oder "I cannot answer this"-Verweigerungen, erhöht progressiv die Temperatur und streicht Hard-Refusals aus der Wertung (Tracking von KI-Überregulierung).
* **Automatisierter Safety-Shift Test:** Bei starken Abweichungen in Verhaltensfiltern (z. B. auf dem Political Compass) triggert das System vollautomatisch einen verschärften Triple-Run Outlier-Check inklusive euklidischem Clustering.
* **Umfassendes Audit-Logging:** Jede Frage, jeder Prompt, jede LLM-Entscheidung und die Standardabweichung (insb. bei Kulturkampf- vs. Ethik-Themen) wird in granularen Markdown-Reports transparent dokumentiert.

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
Kopiere die Konfigurations-Vorlagen und hinterlege deine API-Schlüssel:
```bash
cp benchmark_config.example.yaml benchmark_config.yaml
# Trage in benchmark_config.yaml deine API Keys für commercial_providers ein.
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
- **Status:** ✅ Production-Ready (v3.0.0)

*"Wir benchmarken die Fähigkeiten, die im echten Engineer-Alltag entscheidend sind, nicht nur die akademischen Standardwerte."*
