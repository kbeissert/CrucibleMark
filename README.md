# CrucibleMark

[![Version](https://img.shields.io/badge/version-4.3.1-blue)](.)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](.)
[![License](https://img.shields.io/badge/license-MIT-green)](.)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)](.)

## Ein modulares LLM-Benchmark-Framework für Product Engineers

Akademische Benchmarks wie MMLU messen, was Modelle wissen. CrucibleMark misst, was sie können – dort, wo es für Product Engineers zählt: Code-Qualität, UX-Schreiben, logisches Schlussfolgern und politischer Bias.

Anstatt starrer akademischer Metriken setzt CrucibleMark auf manuell verifizierte Golden Standards und ein kalibriertes LLM-Judge-System. Das Ergebnis ist keine Rangliste der beliebtesten Modelle. Es ist eine ehrliche Antwort auf die Frage: Wie souverän agiert dieses Modell im produktiven Alltag?

**Kernfrage:** Wie gut schneiden selbstgehostete Open-Weights-Modelle – als echte datenschutzkonforme Alternative ohne externe Datensammlung und ohne Manipulationspotenzial durch Dritte – gegen proprietäre Cloud-Modelle ab? Und welche Open-Weights-Modelle sind dabei frei einsetzbar (Apache 2.0 / MIT), welche an kommerzielle Beschränkungen geknüpft?

---

## Philosophie

> 🛑 **Für Entwickler:** Vor dem Einstieg in den Code die 4 unumstößlichen Design-Gesetze in [ARCHITECTURE.md](docs/ARCHITECTURE.md) lesen. (TL;DR: Keine God-Scripts, Keine Magic Numbers, DRY & Separation of Concerns).

Die meisten Benchmarks fokussieren sich auf rein theoretische Prüfungen. CrucibleMark testet die **gelebte Realität**:
- ✅ **Code Quality:** Kann die KI Code wie ein Senior Engineer auditieren?
- ✅ **CLI Operations:** Agiert sie als verlässlicher Kommandozeilen-Agent?
- ✅ **Reasoning & Logik:** Bewältigt sie Paradoxa und logische Stress-Tests?
- ✅ **UX Writing:** Versteht sie die feinen Nuancen von Microcopy?
- ✅ **Cultural Intelligence:** Begreift sie Idiome, Kontexte und kulturelle Feinheiten?
- ✅ **Political Bias & Safety:** Welches Weltbild spiegelt sie wider? Handelt es sich um ein stabiles Modell ohne nennenswerte Werteverschiebung ("Der Stoiker"), maskiert es radikale Shifts unter diplomatischem Auftreten ("Wolf im Schafspelz"), wechselt es unter Druck die ideologische Seite ("Die Chimäre") oder verhält es sich völlig inkonsistent ("Der Narr")?
- ✅ **Tool Use & Function Calling:** Ruft das Modell externe Tools (Web-Suche, HTTP-Fetch) tatsächlich auf — oder halluziniert es Ergebnisse? Kritischer Infrastrukturtest für Agenten-Pipelines: Modelle, die nach einem 404-Fehler trotzdem Inhalte liefern, scheiden für autonome Workflows aus.

**Was CrucibleMark einzigartig macht:** Jede Modell-Karte dokumentiert `deployment_type` (lokal / Cloud), `local_deployment_possible`, `license` und `commercial_use_allowed`. Damit lässt sich das Leaderboard direkt nach „Welche Modelle kann ich selbst hosten und ohne Einschränkungen kommerziell nutzen?" filtern.

---

## Features

* **LLM-as-a-Judge Architektur:** Ein dediziertes Sub-System delegiert die semantische Bewertung der Antworten an hochperformante Judges (wie Claude Haiku oder lokale Modelle).
* **Multi-Provider Support:** Volle Unterstützung für lokale, datenschutzkonforme Ausführung via **Ollama** sowie cloud-basierte kommerzielle Modelle (Mistral, Anthropic Claude, OpenAI, Google Gemini, xAI).
* **SSOT 3-CSV Data Architecture:** Isolierte Logik und trennscharfes Logging von Local VRAM, Cloud Open-Weights Proxies und kommerziellen API-Modellen.
* **Ausfallsicherheit & Checkpointing:** Block-Level-Checkpointing sichert den Fortschritt bei Budget-Erschöpfung, Rate Limits (429) oder Verbindungsabbrüchen. Der Run setzt auf den Token genau dort weiter, wo er endete.
* **Erweiterte Refusal-Architektur:** Das Framework erkennt Zensur und "I cannot answer this"-Verweigerungen eigenständig, erhöht progressiv die Temperatur und streicht Hard-Refusals aus der Wertung.
* **Automatisierter Safety-Shift Test:** Bei starken Abweichungen in Verhaltensfiltern triggert das System vollautomatisch einen verschärften Triple-Run Outlier-Check inklusive euklidischem Clustering.
* **Umfassendes Audit-Logging & Meta-Reviews:** Jede Frage, jeder Prompt und jede LLM-Entscheidung landet in granularen Markdown-Reports. Ein kalibriertes Meta-Review-LLM liest diese Logs zusammen mit technischen API-Limits ein und verfasst halluzinationsfreie Endberichte – gestützt auf strikte Off-by-one-Anker und Grammatikrestriktionen.
* **Token-Budget-System:** Für definierte Benchmark-Module (z. B. `cultural_intelligence`, `code_quality`) wird ein `max_tokens`-Cap als direkter API-Parameter gesetzt, um Provider-übergreifende Vergleichbarkeit herzustellen. Reasoning-Module (`reasoning_logic`) sind bewusst ausgenommen und laufen ohne Output-Limit. Die Budgets sind in `benchmark_config.yaml` unter `token_budgets` kalibrierbar.
* **Token-Verbrauch im Leaderboard:** Beide Leaderboard-CSVs weisen `Tokens Total` aus — die kumulierte Output-Token-Summe über alle bewerteten Benchmark-Module (identische Basis wie der Total Score). Das Detailed-Leaderboard enthält zusätzlich eine Aufschlüsselung pro Modul (`Tokens: Code Quality`, `Tokens: UX Writing`, …). Für API-Nutzer (Pay-per-Token) ist dies die entscheidende zweite Kostendimension neben `Cost per 1K (USD)`.
* **ThinkingProbe & Card-First Workflow:** CrucibleMark erkennt Reasoning-Modelle seit v3.5.8 empirisch statt rein heuristisch. Vor jedem Benchmark-Run prüft der Runner, ob für das Modell eine validierte Model Card mit `thinking_probe_detected`-Feld vorliegt. Fehlt das Feld, sendet das Framework einen deterministischen Reasoning-Probe-Prompt und wertet `<think>`-Tags (Signal A) und `reasoning_tokens > 0` (Signal B) aus. Das Ergebnis wird in der Model Card persistiert und dient ab sofort als primäre Quelle für `is_reasoning_model()` — String-Trigger bleiben als Fallback erhalten. Retroaktiver Batch-Scan via `make probe-all-thinking`.
* **Konsolidierter llama.cpp-Spark-Connector (v4.3.0):** Der lokale OpenAI-kompatible Spark-Connector (`llamacpp_spark`) unterstützt robuste Endpoint-Adoption, tolerantem Readiness-Probing (inkl. `reasoning_content`/`finish_reason`) und garantiertem End-of-Run-Cleanup (Stop + optionales Cache-Clear) auch bei Abbruch.
* **Size-Class-Klassifikation (Card-First):** `get_model_size_class()` nutzt eine 3-stufige Priority-Kaskade: (1) `size_class`-Feld der JSON-Model-Card (SSoT), (2) Ollama-Colon-Tag (z. B. `gemma4:E4B` → Nano), (3) Dash/Dot-Suffix-Regex auf den Modellnamen (z. B. `llama-3.3-70b` → Server). Fallback: Frontier. Das Leaderboard weist damit 6 Deployment-Tiers aus (Nano/Edge/Desktop/Workstation/Server/Frontier).
* **Transparenz bei lautlosen Verweigerungen:** Meta-Reviews enthalten seit v3.5.9 einen `empty_response_context`-Block: Assets, bei denen ein Modell `response_length=0` liefert (lautlose Content-Policy-Ablehnung), werden namentlich im Modul-Abschnitt des Reviews dokumentiert.
* **Use-Case-Klassifikation & Reviewer-Kontext (v3.8.0):** Jede Model Card trägt das Pflichtfeld `use_case_primary` (Werte: `generalist`, `coding`, `reasoning`, `vision-language`, `agentic`). Ergänzt durch `parameter_architecture` (dense/moe), `context_window_k` und `knowledge_cutoff`. Die Taxonomy aller erlaubten Werte liegt in `config/classification_taxonomy.json` (SSoT). Beim Generieren eines Reviews injiziert `generate_review.py` die vollständige Taxonomy inklusive modellspezifischer Hervorhebung als `{use_case_classification_context}` in den Reviewer-Prompt — so bewertet der Reviewer ein Vision-Language-Modell nicht am selben Maßstab wie einen Generalisten.

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
# Vollautomatischer Batch-Run (alle aktivierten Module, alle konfigurierten Modelle):
make benchmark-auto

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

**Model Cards & Provider Cards** sind strukturierte JSON-Steckbriefe mit Entwickler, Herkunftsland, Datenschutz-Metadaten, Sovereign-Risk-Einschätzung sowie Preisinformationen. Sie werden **manuell gepflegt** — `make model-cards` erstellt ein Template, das dann redaktionell befüllt wird. Model Cards sind die **Single Source of Truth** für Pricing (`input_price_per_1m` / `output_price_per_1m`), Modell-Kategorie (`weights_license_tier`) und Thinking-Probe-Status.

```bash
make model-cards MODEL=<id>  # Neues Model Card Template anlegen (dann manuell befüllen)
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

> **Web-Export ist nicht automatisch mit `make leaderboard` verknüpft.** Er wird manuell ausgelöst, wenn das Leaderboard vollständig und bereit für die Veröffentlichung ist.

**Modell vollständig entfernen:**
```bash
make clean-model MODEL="mistral-large-2411"       # CSV-Zeilen, Audit-Logs, Reviews, Model Card
make clean-model MODEL="mistral-large-2411" DRY=1 # Vorschau (kein Löschen)
```

---

## Roadmap (Stand: Q1/Q2 2026)

Viele der einst geplanten Fundamental-Features (wie *Reasoning*, *Cultural Intelligence* und tiefe *Sicherheitsarchitekturen*) sind im Core implementiert. So geht es als Nächstes weiter:

- [x] **Agentic Workflow Benchmarks / Tool Use:** Native Tests für Multi-Step Tool-Usage — vollständig implementiert als `tooluse`-Modul (v3.10.0+). 6 Assets, Live-MCP-Modus, PRODUCTION/NOT_RECOMMENDED-Klassifikation.
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
- **Status:** ✅ Production-Ready (v4.3.1)
