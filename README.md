# CrucibleMark

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Version](https://img.shields.io/badge/Version-0.9.5--beta-orange.svg)](PROJECT_STATUS.md)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](LICENSE)
[![Ollama](https://img.shields.io/badge/Ollama-Compatible-green.svg)](https://ollama.ai)

> **"The Product Engineer's Compass"** – Ein Benchmarking-Framework für digitale Produktentwickler, die KI nicht nur nutzen, sondern verstehen wollen.

---

## 🎯 Was ist CrucibleMark?

CrucibleMark ist **kein generischer LLM-Benchmark** wie MMLU oder HumanEval. Es ist ein **Spezialwerkzeug für Technical Creators** – die Schnittmenge aus Product Engineers, UX Writers und System Architects, die sicherstellen müssen, dass KI:

- ✅ **Sauberen, sicheren Code** liefert (nicht nur "funktionierenden")
- ✅ **Den richtigen Ton trifft** (UX Writing, Accessibility)
- ✅ **Logisch stabil bleibt** (Reasoning, Deadlock-Erkennung)
- ✅ **Kulturell sensibel agiert** (Bias-Checks, Extremismus-Erkennung)

**Von Code Quality über UX Writing bis Complex Reasoning** – CrucibleMark ist der "TÜV für digitale Produktentwicklung", flexibel und modular wie ein Lego-System für KI-Tests.

---

## 💡 About This Project

CrucibleMark ist ein **persönliches Leuchtturmprojekt**, das zeigt, wie weit man mit KI-Assistenz (Copilot, Perplexity) als Nicht-Entwickler kommen kann.

### Die Story
Als Screen- und UX-Designer ohne klassische Software-Entwickler-Ausbildung wollte ich herausfinden:
**Kann KI mir helfen, ein komplexes Benchmark-Framework zu bauen?**

Die Antwort: **Ja!** Dieses Projekt beweist, dass KI-Assistenz nicht nur "Autocomplete" ist, sondern echte **Produktentwicklung** ermöglicht.

### Warum Open Source?
Ich teile den Code, um:
- 🎓 Anderen zu zeigen, was mit KI-Assistenz möglich ist
- 🔍 Transparenz über meine Arbeitsweise zu schaffen
- 🤝 Mit der Community zu lernen und zu wachsen
- 🚀 Ein Werkzeug zu bauen, das anderen hilft (wie 3DMark für LLMs)

### Built With AI
Dieses Projekt wurde entwickelt mit Unterstützung von:
- **GitHub Copilot** (Code-Completion & Refactoring)
- **Perplexity AI** (Architektur-Beratung & Best Practices)
- **Claude Sonnet** (Documentation & Code-Review)

**Proof:** KI ist kein Hype – es ist ein Werkzeug, das Kreativität entfesselt! 🚀

---

## 🆕 Neu in Version 0.9.5 (Feb 2026)

### Framework Refactoring (Production-Ready Architecture)
Die Version 0.9.5 bringt massive Verbesserungen in der Code-Qualität und Wartbarkeit:

- **Modulare Leaderboard-Architektur**: `generate_leaderboard.py` (1384 Zeilen) wurde in ein sauberes Package mit 7 Modulen aufgeteilt
- **Duplicate Code Elimination**: Scoring-Logik zentralisiert in `utils/scoring_utils.py` (DRY-Prinzip)
- **Code Quality**: PyLint-Score von 8.79 → 9.1/10, Ruff 100% clean
- **Zero Regressions**: Alle Funktionen validiert, keine Breaking Changes

### Advanced Reasoning (v2.3)
Das Reasoning-Modul wurde mit neuen "Hard-Mode" Assets erweitert:

- **Differenzierte Gewichtung**: Tier 2 (Operational Logic, 60%) vs. Tier 3 (Metacognition, 40%)
- **Neue Adversarial Tests**: Monitoring Paradox, Subtle Deadlock
- **Difficulty Ladder**: Parallele Basis- und Hard-Mode-Tests messen die "Reasoning Ceiling"

### Golden Standard Methodology (v2.1.0)
- **Model**: Mistral Large (123B) als Referenz
- **Reasoning Score**: 87.40
- **Updates**: RCI Weighting (60/40), Fix für 5C-001 Scoring
- **Datum**: 30. Januar 2026

Siehe [GOLDEN_STANDARD_CHANGELOG.md](docs/GOLDEN_STANDARD_CHANGELOG.md) für die vollständige Historie.

---

## ⚡ Quick Start (3 Befehle)

```bash
# 1. Installation
make install

# 2. Interaktiver Benchmark-Wizard
make benchmark

# 3. Leaderboard generieren
make leaderboard
```

**Fertig!** Die Ergebnisse findest du in `benchmark_scores/benchmark_leaderboard.csv`.

---

## 🎯 Warum CrucibleMark?

### Das Problem
Standard-Benchmarks wie MMLU messen akademisches Wissen. HumanEval testet Code-Completion. **Aber wer testet, ob ein LLM:**
- Security-Lücken in Legacy-Code findet?
- UX-Copy für Screen-Reader optimiert?
- Deadlocks in verteilten Systemen erkennt?
- Extremistische Narrative ablehnt?

### Die Lösung
CrucibleMark testet **echte Product-Engineering-Szenarien**:

| Standard-Benchmark | CrucibleMark |
|-------------------|--------------|
| "Schreibe eine Funktion" | "Auditiere diesen Legacy-Code und finde 4 Security-Lücken (Tier 1-4)" |
| "Übersetze einen Satz" | "Schreibe Error-Messages für Sehbehinderte (Screen-Reader-optimiert)" |
| "Löse ein Logik-Rätsel" | "Erkenne den Deadlock in diesem verteilten System (versteckt in Narrative)" |

---

## 🚀 Features

- **Modulares Plugin-System**: Eigene Test-Module in 15 Minuten erstellen
- **Tiered Difficulty (1-4)**: Von "Labeled Errors" (Junior-Modelle) bis "Expert Hidden Issues" (Senior-Modelle)
- **Hybrid Scoring**: Kombination aus Keyword-Matching (40%) und Semantischer Ähnlichkeit (60%)
- **Golden Standard Comparison**: Jedes Modell wird gegen Mistral Large verglichen (Performance Ratio)
- **Reproduzierbarkeit**: Fixierte Seeds (42), deterministische Prompts, Rate-Limit-Handling
- **Cost Tracking**: Token-Verbrauch und Kosten ($) pro Benchmark-Run

---

## 📦 Benchmark-Module

**Welche Module aktiv sind, steuerst du zentral in `benchmark_config.yaml`** (einfach `enabled: false` setzen).

| ID | Modul | Beschreibung | Status |
|----|-------|--------------|--------|
| `code_quality` | **Code Quality** | Statische Analyse, Security, Best Practices | ✅ v1.0 |
| `ux_writing` | **UX Writing** | Microcopy, Accessibility, User Flow | ✅ v1.0 |
| `documentation_quality` | **Documentation** | Technische Dokumentation & Struktur | ✅ v1.0 |
| `content_transformation` | **Content Adaption** | Format-Transformation, Stil-Anpassung | ✅ v0.9 |
| `reasoning_logic` | **Reasoning** | Logik, Deduktion, Deadlock-Erkennung | ✅ v2.3 |
| `political_compass` | **Political Compass** | Ideological Bias & Extremism Check | ✅ v3.0 |
| `cultural_intelligence` | **Cultural Intelligence** | Kulturelles Verständnis & Sprachnuancen | ✅ v1.0 |

**Details zu jedem Modul:** Siehe `benchmark_modules/<module_id>/README.md`

---

## 🏆 Leaderboard & Metrics

Das Leaderboard klassifiziert Modelle nach **Profil**, nicht nur nach Punkten:

### 🏅 Gamified Badges
- 👑 **God Mode**: Exzellent in beiden Bereichen (Routine >85% & Reasoning >80%)
- 🏎️ **Daily Driver**: Perfekt für schnelle Standard-Aufgaben (Routine >80%)
- 🧠 **Deep Thinker**: Spezialist für komplexe Logik (Reasoning >80%)
- ⚠️ **Needs Tuning**: Modelle, die noch Optimierung benötigen

### 📊 Meta-Metrics
- **Routine Score**: Aggregiert aus `routine`-Modulen (UX Writing, Documentation, Content)
- **Reasoning Score**: Aggregiert aus `reasoning`-Modulen (Code Quality, Logic, Metacognition)
- **Performance Ratio**: Prozentualer Vergleich zum Golden Standard (Mistral Large)

**Beispiel:**
```
Model: qwen2.5-coder:14b
Routine: 78% | Reasoning: 85% | Badge: 🧠 Deep Thinker
Performance Ratio: 92% (vs. Mistral Large)
```

---

## 📖 Installation & Setup

### Voraussetzungen
- **Python 3.10+** (mit pip)
- **Ollama** (für lokale Modelle) – [Installation](https://ollama.ai)
- **API-Keys** (optional, für kommerzielle Modelle):
  - Mistral AI, OpenAI, Anthropic

### Schritt 1: Repository klonen
```bash
git clone https://github.com/yourusername/cruciblemark.git
cd cruciblemark
```

### Schritt 2: Dependencies installieren
```bash
make install
# Oder manuell:
pip install -r requirements.txt
```

### Schritt 3: Konfiguration

#### A) Lokale Modelle (Ollama)
```bash
# Prüfe verfügbare Modelle
ollama list

# Ziehe ein Modell (falls nicht vorhanden)
ollama pull qwen2.5-coder:14b
```

#### B) Kommerzielle Modelle (Optional)
Erstelle eine `.env`-Datei im Root-Verzeichnis:
```bash
# .env
MISTRAL_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

**Aktiviere Provider in `benchmark_config.yaml`:**
```yaml
providers:
  commercial:
    mistral:
      enabled: true
      api_key: ${MISTRAL_API_KEY}
```

### Schritt 4: Module konfigurieren
Öffne `benchmark_config.yaml` und passe an, welche Module aktiv sein sollen:
```yaml
modules:
  code_quality:
    enabled: true
  political_compass:
    enabled: false  # Modul überspringen
```

---

## 🎮 Erste Schritte

### 1. Interaktiver Benchmark
```bash
make benchmark
# Oder direkt:
python scripts/core/run_local_benchmark.py
```

**Du wirst gefragt:**
1. Welches Modul? (z.B. "Code Quality")
2. Welches Modell? (z.B. "qwen2.5-coder:14b")
3. Wie viele Runs? (Standard: 1)

**Output:**
- Console: Fortschritt + Zusammenfassung
- CSV: `benchmark_scores/local_models_benchmark.csv`
- Logs: `logs/crucible.log`

---

### 2. Automatischer Batch-Modus
```bash
make benchmark-auto
# Führt ALLE Module auf ALLEN Modellen aus (Overnight Mode)
```

**Warnung:** Das kann Stunden dauern und API-Kosten verursachen!

---

### 3. Leaderboard generieren
```bash
make leaderboard
# Generiert: benchmark_scores/benchmark_leaderboard.csv
```

**Das Leaderboard zeigt:**
- Ranking (nach Performance Ratio)
- Badges (God Mode, Daily Driver, Deep Thinker)
- Routine/Reasoning Split
- Durchschnittliche Antwortzeit
- Token-Verbrauch & Kosten

---

## 🛠️ Nützliche Befehle

```bash
# Modelle auflisten (mit Connectivity-Check)
make list-models

# Module auflisten
make list-modules

# Assets validieren (Schema-Check)
make validate-assets

# Projekt-Struktur prüfen
make validate-structure

# Kosten schätzen (vor großem Batch-Run)
make analyze-costs

# Backup erstellen
make backup

# Golden Standard neu generieren (nach Mistral-Update)
make generate-golden
```

---

## 📚 Dokumentation

### Für Nutzer
- **[USER_GUIDE.md](docs/USER_GUIDE.md)** – Wie man Benchmarks startet, steuert und auswertet
- **[DATA_FORMAT.md](docs/DATA_FORMAT.md)** – Erklärung der CSV-Outputs und Metriken
- **[GOLDEN_STANDARDS.md](docs/GOLDEN_STANDARDS.md)** – Golden Standard Konzept & Methodology

### Für Entwickler
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** – Aktueller Entwicklungsstand & Architektur
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** – Technische Architektur & Design-Entscheidungen
- **[ADDING_MODULES.md](docs/ADDING_MODULES.md)** – Anleitung zum Erstellen eigener Test-Module
- **[MODEL_CLASSIFICATION.md](docs/MODEL_CLASSIFICATION.md)** – Wie das Hybrid-System Modelle klassifiziert

### Für Nicht-Techniker
- **[BENCHMARK_SCENARIOS.md](docs/BENCHMARK_SCENARIOS.md)** – Verständliche Erklärung der Testszenarien

---

## ⚖️ Golden Standard Methodology

CrucibleMark verwendet **Mistral Large (123B)** als Golden Standard Referenz.

### Wie es funktioniert
1. **Mistral Large** wird auf allen Assets getestet
2. Antworten werden als **"perfekte Referenz"** in `golden_standards/mistral/` gespeichert
3. Alle anderen Modelle werden gegen diese Referenz verglichen (Semantische Ähnlichkeit)

### Scores interpretieren
- **100%**: Entspricht Golden Standard Performance
- **>100%**: Übertrifft Golden Standard (selten, deutet auf veralteten Standard hin)
- **<100%**: Unter Golden Standard (typisch für lokale Modelle)

### Wann Golden Standard aktualisieren?
- Neue Assets hinzugefügt
- Mistral Large erhält Major-Update
- Konsistent >100% Ratios bei anderen Modellen

**Befehl:**
```bash
make generate-golden
```

### 📦 Pre-Generated Standards
Dieses Repository enthält **vorgenerierte Golden Standards** (basierend auf Mistral Large). Du kannst also sofort loslegen, ohne API-Key!

Wenn du einen neuen Standard etablieren willst (z.B. mit GPT-5):
1. Update `benchmark_config.yaml` → Golden Standard Modell ändern
2. Run `make generate-golden`
3. Commit die neuen JSON-Files in `golden_standards/`

---

## 🗺️ Roadmap

### ✅ Completed (v0.9.5)
- [x] Framework Refactoring (Production-Ready Code)
- [x] Modulare Leaderboard-Architektur
- [x] Advanced Reasoning (Tier 2 & 3)
- [x] 7 Production-Ready Module
- [x] Golden Standard Methodology
- [x] Cost & Token Tracking
- [x] Hybrid Model Classification

### 🚧 In Progress (Path to v1.0)
- [ ] LLM-as-a-Judge Scorer (Priority 1 for v1.0)
- [ ] Module Refactoring (Cleanup & Optimization)
- [ ] Documentation Polish (User Guide, Architecture)

### 🔮 Planned (Post v1.0)
- [ ] Reporting Dashboard (Streamlit/Dash Visualization)
- [ ] HuggingFace Leaderboard Integration
- [ ] Custom Model Support (GGUF ohne Ollama)
- [ ] Web Frontend (CSV-basierte Reports)

Siehe [REF_TODO.md](REF_TODO.md) für Details.

---

## 🤝 Contributing

Contributions sind willkommen! Besonders gesucht:

- **Neue Module** (z.B. "API Design", "Database Schema Review")
- **Mehr Assets** (erweitere bestehende Module)
- **Scorer-Verbesserungen** (bessere Semantik-Checks)
- **Dokumentation** (Tutorials, Beispiele)

**Wichtig**: Alle Contributions müssen unter der Apache 2.0 Lizenz erfolgen.
Siehe [CONTRIBUTING.md](CONTRIBUTING.md) und [CONTRIBUTORS.md](CONTRIBUTORS.md) für Details.

---

## 📄 License & Legal

### Open Source License

CrucibleMark is licensed under the **Apache License 2.0**.

**What this means for you:**

✅ **You MAY:**
- Use the software for personal and commercial purposes
- Modify and distribute the code
- Use it in proprietary software
- Patent your own implementations

❌ **You MUST:**
- Include the original copyright notice
- Include the LICENSE file
- State significant changes made
- Include the NOTICE file (if distributing)

❌ **You CANNOT:**
- Use the trademark "CrucibleMark" for competing products (see [TRADEMARK.md](TRADEMARK.md))
- Hold the author liable for damages
- Claim this is your original work

**Full License**: See [LICENSE](LICENSE) file  
**Attribution Requirements**: See [NOTICE](NOTICE) file  
**Trademark Policy**: See [TRADEMARK.md](TRADEMARK.md)

---

### Dependencies & Third-Party Licenses

This project uses the following open-source components:

| Component | License | Use Case |
|-----------|---------|----------|
| **Ollama** | MIT | Local LLM hosting |
| **Sentence Transformers** | Apache 2.0 | Semantic similarity scoring |
| **PyYAML** | MIT | Configuration parsing |
| **Python Requests** | Apache 2.0 | HTTP client |
| **Mistral AI Client** | Apache 2.0 | Commercial LLM provider |

For a complete list, see [requirements.txt](requirements.txt) and [NOTICE](NOTICE).

---

### Citation

If you use CrucibleMark in academic work, please cite:

```bibtex
@software{cruciblemark2026,
  author = {Kay Beißert},
  title = {CrucibleMark: A Benchmarking Framework for Product Engineering LLM Evaluation},
  year = {2026},
  url = {https://github.com/yourusername/cruciblemark},
  version = {0.9.5-beta}
}
```

---

## 🙏 Acknowledgments

- **Mistral AI** für das Golden Standard Modell
- **Ollama** für lokales LLM-Hosting
- **Sentence Transformers** für semantische Scoring-Engine
- **GitHub Copilot, Perplexity AI, Claude** für AI-Assistenz während der Entwicklung
- **Community** für Feedback & Testing

---

## 📞 Support & Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/cruciblemark/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/cruciblemark/discussions)
- **Email**: kay.beissert@media-garage.de
- **Docs**: [docs/](docs/)

---

## 📛 Trademark Notice

**"CrucibleMark"** is a trademark of Kay Beißert.

You may use the name to refer to this project, but not for competing products or services. See [TRADEMARK.md](TRADEMARK.md) for details.

---

**Happy Benchmarking! 🚀**

---

**Built with 💡 AI-Assistance**  
_Proving that KI-Assistenz enables real product development, not just autocomplete._
