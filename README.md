# CrucibleMark

[![Version](https://img.shields.io/badge/version-5.1.4-blue)](.)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](.)
[![License](https://img.shields.io/badge/license-MIT-green)](.)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)](.)

**Stand: v5.1.2 · 2026-08-03**

## Ein modulares LLM-Benchmark-Framework für Product Engineers

Akademische Benchmarks wie MMLU messen, was Modelle wissen. CrucibleMark misst, was sie im produktiven Alltag leisten: Code-Reviews, UX-Texte, logisches Schlussfolgern, Tool-Nutzung, politische Verzerrungen.

Statt starrer akademischer Metriken arbeitet das Framework mit manuell verifizierten Golden Standards und einem kalibrierten LLM-Judge. Das Ergebnis ist keine Rangliste der populärsten Modelle, sondern eine ehrliche Antwort auf eine konkrete Frage: Wie souverän agiert dieses Modell im produktiven Alltag?

**Kernfrage:** Wie schlagen selbstgehostete Open-Weights-Modelle — als datenschutzkonforme Alternative ohne externe Datensammlung — gegen proprietäre Cloud-Modelle ab? Welche Open-Weights-Modelle sind unter Apache 2.0 oder MIT frei einsetzbar, welche an kommerzielle Beschränkungen gebunden?

---

## Was CrucibleMark misst

Jedes Modul deckt eine Alltagsdimension ab, mit der Produktteams, Entwickler und Redakteure täglich konfrontiert sind:

- **Code Quality** — funktioniert der Code-Review? Erkennt das Modell Sicherheitslücken (OWASP), Accessibility-Verstöße (WCAG) und Architekturprobleme?
- **CLI Operations** — liefert das Modell exakte Kommandozeilen-Befehle oder halluziniert Flags?
- **Reasoning & Logik** — bewältigt das Modell Paradoxa, logische Stresstests und Selbstkorrektur?
- **UX Writing** — schreibt das Modell Microcopy für Fehlermeldungen, Buttons, Onboarding-Flows auf dem Niveau eines professionellen UX-Writers?
- **Cultural Intelligence** — beherrscht das Modell idiomatische Übersetzungen, regionale Varianten (DE/AT/CH), Formalitätsstufen?
- **Political Bias & Safety** — welches Weltbild spiegelt das Modell, und wie stabil bleibt es unter Druck?
- **Tool Use & Function Calling** — ruft das Modell externe Tools tatsächlich auf oder halluziniert es Ergebnisse? Entscheidender Infrastrukturtest für Agenten-Pipelines.

**Was CrucibleMark einzigartig macht:** Jede Model Card dokumentiert `deployment_type` (lokal oder Cloud), `local_deployment_possible`, `license` und `commercial_use_allowed`. Damit lässt sich das Leaderboard direkt nach selbst hostbaren und uneingeschränkt nutzbaren Modellen filtern.

---

## Architektur in Kürze

> 🛑 **Für Entwickler:** Vor dem Einstieg in den Code die unumstößlichen Design-Gesetze in [ARCHITECTURE.md](docs/ARCHITECTURE.md) lesen. Kurzfassung: keine God-Scripts, keine Magic Numbers, DRY, Separation of Concerns.

Das Framework folgt vier Prinzipien:

1. **Trennung von Measurement und Publishing.** Der Benchmark-Loop ist autark und ausfallsicher. Judge und Meta-Reviewer laufen als API-Modelle in strikt getrennten Phasen (sequenziell, ohne gemeinsamen State); der Web-Export läuft offline und wird manuell ausgelöst.
2. **Single Source of Truth.** Jede Funktion hat genau einen festen Platz. Preise, Modell-Identität und Scoring-Konstanten werden ausschließlich aus den Model Cards gelesen.
3. **Config-Driven.** Alle Regeln, Zahlen und Limits stehen in YAML. Keine Magic Numbers im Code.
4. **Sequenzielle Modell-Abarbeitung.** Jedes Modell wird einzeln getestet, mit Server-Neustart und Cooldown. Cache-Vorteile werden so ausgeschlossen.

Die volle Beschreibung mit Layer-Architektur, Provider-Abstraktion und Datenfluss steht in [ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Features

### Benchmark-Engine

- **LLM-as-a-Judge.** Dediziertes Sub-System bewertet die Antworten über starke Judge-Modelle (Claude Haiku, Gemini Pro oder lokale Modelle).
- **Hybrid Scoring.** Regex, Embeddings und LLM Judge ergänzen sich. Regex liefert Objektivität, der Judge liefert Nuancen, Embeddings fangen Format-Varianz ab.
- **Multi-Provider.** Volle Unterstützung für OpenAI, Anthropic, Google, Mistral, xAI, OpenRouter, Cohere, Ollama, llama.cpp, Spark (llamacpp) und vLLM (Spark).
- **Sequenzielle, faire Testbedingungen.** Modelle werden einzeln nacheinander mit Server-Neustart und Cooldown getestet. Kein Cache-Vorteil, kein Kontextmix.
- **Block-Level-Checkpointing.** Runs überstehen Budget-Erschöpfung, 429-Limits und Verbindungsabbrüche. Resume erfolgt auf den Token genau.

### Bewertung

- **Token-Budget-System mit kaskadierenden Limits.** Definierte Module erhalten einen direkten `max_tokens`-API-Cap für Provider-übergreifende Vergleichbarkeit. Reasoning-Modelle erhalten ein erhöhtes Budget. Schwellen aus `benchmark_config.yaml → token_budgets` und `token_budgets_reasoning_models`.
- **Refusal-Architektur.** Das Framework erkennt Zensur und "I cannot answer this"-Verweigerungen eigenständig, erhöht progressiv die Temperatur und streicht Hard-Refusals aus der Wertung.
- **Hard Constraints.** Wortanzahl- und Sprach-Mismatch-Verstöße werden separat vom Inhalts-Score dokumentiert, ohne den Inhalt verschwinden zu lassen.
- **Tool-Use-Modul mit Zwei-Phasen-Scoring.** Phase 1 prüft Tool-Auswahl und Parameter, Phase 2 die inhaltliche Qualität der Synthese. Content Verification Gate und Halluzinations-Cap sind config-first und SSoT-basiert.

### Datenschutz und Selbst-Hosting

- **License- und Sovereign-Filter im Leaderboard.** Filter nach Apache 2.0, MIT, gewerblicher Nutzbarkeit und Hosting-Realität.
- **Open-Weights-First-Doku.** Card-Felder dokumentieren Herkunftsland, Provider-Jurisdiktion und Datenschutz-Hinweise.

### Reporting

- **Audit-Logs und Meta-Reviews.** Jeder Prompt, jede Antwort und jede Judge-Entscheidung liegt in granularen Markdown-Reports. Ein kalibrierter Meta-Reviewer verdichtet sie zu redaktionellen Beiträgen.
- **Web-Export.** Aggregierte Leaderboards, Reviews und Audit-Logs als aufbereitetes Datenpaket für das externe Frontend-Projekt `cruciblemark-web`.

---

## Installation und Quickstart

### Voraussetzungen

- macOS, Linux oder Windows (WSL)
- Python 3.12 oder höher
- Ollama für den lokalen Modus

### Schritt 1: Repository klonen und einrichten

```bash
git clone https://github.com/kbeissert/cruciblemark.git
cd cruciblemark
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Schritt 2: Konfiguration kopieren

Konfigurationsvorlagen kopieren. API-Schlüssel ausschließlich in einer lokalen `.env`-Datei hinterlegen:

```bash
cp benchmark_config.example.yaml benchmark_config.yaml
```

### Schritt 3: Erster Benchmark-Lauf

```bash
# Vollautomatischer Batch-Run über alle aktivierten Module und Modelle:
make benchmark-auto

# Geführtes UI mit interaktiver Modulauswahl:
python run_benchmark.py

# Nur lokale Ollama-Modelle:
python run_benchmark.py --provider local

# Kommerzielle Modelle mit Refusal-Tracking:
python run_benchmark.py --provider commercial

# Einzelnes Modul und Modell:
python run_benchmark.py --provider commercial --module political_compass --model gpt-4o

# Political-Compass-Safety-Run (Triple-Run mit euklidischem Clustering):
make political-compass-safe
```

Detaillierte Anleitung zu Setup, Hardware-Profilen und Provider-Konfiguration: [SETUP_GUIDE.md](docs/SETUP_GUIDE.md).

---

## Web-Export-Pipeline

CrucibleMark enthält eine integrierte Export-Pipeline (`scripts/web_export.py`), die Benchmark-Ergebnisse als aufbereitetes Datenpaket für das externe Frontend-Projekt `cruciblemark-web` bereitstellt.

**Model Cards und Vendor Cards** sind strukturierte JSON-Steckbriefe mit Entwickler, Herkunftsland, Datenschutz-Metadaten, Sovereign-Risk-Einschätzung und Preisinformationen. Sie werden redaktionell gepflegt — `make model-cards MODEL=<id>` legt ein Template an. Model Cards sind die Single Source of Truth für Pricing (`input_price_per_1m`, `output_price_per_1m`), Modell-Kategorie (`weights_license_tier`) und Thinking-Probe-Status.

```bash
make model-cards MODEL=<id>  # Neues Model Card Template anlegen
make vendor-cards            # Vendor Cards für fehlende Provider generieren
```

**Was exportiert wird:**

- `leaderboard.json` — globale Rangliste
- `models/<slug>/data.json` — Scores und Modul-Details pro Modell
- `models/<slug>/comparisons/` — redaktionelle Meta-Reviews
- `models/<slug>/audit_logs/` — sanitisierte Einzeltest-Protokolle: Prompt, Modellantwort und Modul-Metriken

Die Judge-Auswertung fließt vor dem Export heraus. Sie erscheint ausschließlich in den Meta-Review-Artikeln.

```bash
# Export in konfigurierten Ausgabeordner (benchmark_config.yaml → output.web_export_dir)
make web-export

# Direkter Export ins Development-Frontend (Eleventy)
make web-export-dev
```

> **Der Web-Export läuft nicht automatisch mit `make leaderboard`.** Er wird manuell ausgelöst, wenn das Leaderboard vollständig und bereit für die Veröffentlichung ist.

```bash
# Modell vollständig entfernen (CSV-Zeilen, Audit-Logs, Reviews, Model Card)
make clean-model MODEL="mistral-large-2411"
make clean-model MODEL="mistral-large-2411" DRY=1   # Vorschau ohne Löschen
```

---

## Roadmap (Stand: Q1/Q2 2026)

- [x] **Agentic Workflow Benchmarks / Tool Use** — vollständig implementiert als `tooluse`-Modul (v3.10.0+).
- [ ] **Visuelles Sub-System (Multimodal)** — Integration visueller Benchmarks (UML-Diagramme, UI-Design).
- [ ] **Web-UI / Dashboard** — interaktive Streamlit- oder React-Umgebung für CSV-Output und Leaderboards.
- [ ] **CI/CD-System-Hooks** — GitHub-Actions-Integration für Pull-Request-Prüfungen.

---

## Dokumentations-Hub

- [Methodik & Political-Compass-Konzept](docs/POLITICAL_COMPASS_KONZEPT.md)
- [Scoring-Methodik](docs/SCORING_METHODOLOGY.md)
- [Architektur](docs/ARCHITECTURE.md)
- [Entwicklerhandbuch](docs/DEVELOPER_GUIDE.md)
- [Setup-Anleitung](docs/SETUP_GUIDE.md)
- [Benutzerhandbuch](docs/USER_GUIDE.md)
- [Modul-Übersicht](docs/BENCHMARK_MODULES.md)
- [Modellklassifizierung](docs/MODEL_CLASSIFICATION.md)
- [Card-Management](docs/CARD_MANAGEMENT.md)
- [ToolUse-Modul](docs/TOOLUSE_MODULE.md)
- [Thinking-Probe](docs/THINKING_PROBE.md)
- [Backup-Strategie](docs/BACKUP_STRATEGY.md)
- [Glossar](docs/GLOSSAR.md)

---

## Recent Versions

Die vollständige Versionshistorie steht in [CHANGELOG.md](CHANGELOG.md). Kurzfassung der letzten drei Releases:
### v5.1.2 (2026-08-03) — vLLM-Connector CC-Refactoring

Verhaltenserhaltendes Refactoring von `vllm_base.py`: `start_server` (CC 19→8) in Dispatch-Shell + 9 Pfad-Methoden zerlegt, `query` (CC 16→7) Streaming in `_consume_stream` ausgelagert, Reasoning-Fallback in `_apply_reasoning_fallback` dedupliziert (DRY). Alle `# noqa: C901`-Annotationen entfernt — die als unverhandelbar deklarierte CC-≤-12-Regel wird nicht mehr umgangen. 115 Tests grün, Ruff 0 violations.



### v5.1.1 (2026-08-02) — vLLM-Connector-Fixes, Laguna Dual-Profile, Naming-Validator

vLLM-Connector gehärtet: Thinking-Profile-Adoption (MoE-Notation im ID-Segment), Post-Stop-Verifikation via SSH statt 502-Interpretation, 502-Mehrdeutigkeit (Pfad 3.5 wartete 600s ohne vllm-start). ToolUse-Exporter überschrieb  in 107 Cards behoben.  →  als Historical Rename (vLLM vor 0.25.1). Laguna S 2.1 als selektives Reasoning-Modell erkannt —  aus  entfernt, keine Dual-Profile-Expansion.  als neue Leaderboard-Spalte. Naming-Validator () als Publication-Gate in === Pre-Check: Naming Conventions ===
=== Naming Convention Validator (model-cards) ===
Alle 116 Cards OK — keine Namensverstoesse.

Starte Web Export...
.venv/bin/python -m scripts.web_export 
Export abgeschlossen. (hard) / === Pre-Check: Naming Conventions (warn-only) ===
=== Naming Convention Validator (model-cards) ===
Alle 116 Cards OK — keine Namensverstoesse.

Exportiere direkt ins 11ty-Projekt...
.venv/bin/python -m scripts.web_export --output ../cruciblemark-web/src/_data/raw/
Dev-Export abgeschlossen. (warn-only) — 11 display_name + 7 model_version Forbidden-Patterns. 7 Vendor-Cards mit compound-Namen bereinigt (llmfan46, jackrong, ara_apex neu strukturiert). 1553 Tests grün.

### v5.1.0 (2026-07-14) — Striktere Incapable-Klassifikation

Fixt einen Design-Defekt aus v5.0: Modelle mit `supports_tool_use: false` wurden pauschal als "incapable" exempt, selbst wenn sie getestet wurden und fehlschlugen. Jetzt gilt "incapable" nur, wenn das Modell null Rows für das Modul hat. `attempted_set` aus `df_all` prüft, ob ein Modell angetreten ist. Zwei Cards korrigiert (Command A+ und GPT-OSS 20B, beide wurden getestet, `false` war Provider-Stabilitätsaussage, nicht Kapabilität). Command A+ fällt von Rang 62 auf Rang 104.

⚠️ **Breaking Change.** Total Scores und Rankings ändern sich für betroffene Modelle.

### v5.0.0 (2026-07-13) — Generalized Coverage Scoring + ToolUse Integration

ToolUse wird als vollwertiges achtes Scoring-Modul integriert (`enable_scoring: true`, `module_weight: 1.0`). Die Coverage-Logik wurde generalisiert: missing- und unknown-Module lösen einen Malus aus, incapable-Modelle bleiben exempt, rolling_out- und not_deployed-Module sind für alle ausgeschlossen. Neue `coverage_ratio`-Spalte. Per-Modell-`Tests Run`-Erwartung (incapable reduziert). Invariante `Routine + Reasoning = Total` erhalten.

⚠️ **Breaking Change.** Total Scores und Rankings ändern sich.

### v4.10.18 (2026-07-11) — Framework-Refactoring + Ruff 0-Violations

Systematisches Refactoring gegen die Architektur-Regeln: `model_utils.py` zerlegt in sieben Submodule mit Re-Export-Bridge, `web_export.py` als Package, `yaml.safe_load` durch `ConfigValidator` in 15 Skripten ersetzt, 131 `print`-Aufrufe auf `logging` migriert. 27 Legacy-Skripte nach `scripts/legacy/` verschoben. Ruff-Verstöße 252 → 0. Bugfix für doppelte Base-Cards bei suffixed Modellen. 1316 Tests grün, verhaltenserhaltend.

---

## Mitwirken

Bug-Reports, Feature-Wünsche und Diskussionen laufen über [GitHub Issues](https://github.com/kbeissert/cruciblemark/issues). Vorschläge für neue Model Cards, Module oder Provider-Integrationen sind willkommen. Maintainer-Richtlinien stehen in [CONTRIBUTORS.md](CONTRIBUTORS.md).

---

## Kontakt

- **Maintainer:** [kbeissert](https://github.com/kbeissert)
- **Repository:** [github.com/kbeissert/cruciblemark](https://github.com/kbeissert/cruciblemark)
- **Status:** Production-Ready (v5.1.4)