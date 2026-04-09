# PROJECT_STATUS.md

**Last Updated:** 2026-04-09
**Current Version:** 3.4.2 (Vollständige Modell-Preisliste & Sync-Tool)
**Status:** ✅ Production-Ready

______________________________________________________________________

## 🎯 Executive Summary

CrucibleMark v3.4.2 schließt die Preis-Datenbasis für alle konfigurierten Cloud- und Commercial-Modelle. Alle 25 Modelle haben jetzt verifizierte Preiseinträge in `config/cost_limits.yaml`. Ergänzend wurde ein neues Dev-Tool (`sync_cost_limits.py`) eingeführt, das Missing-Entries automatisch erkennt und Platzhalter scaffoldet. Das Leaderboard weist jetzt für alle Modelle `Cost per 1K (USD)` und `Benchmark Cost (USD)` aus.

**Key Achievements (v3.4.2):**
- ✅ **Vollständige Preisliste:** Alle Cloud-/Commercial-Modelle in `config/cost_limits.yaml` mit verifizierten Preisen (Quellen: openai.com/api/pricing, ai.google.dev/gemini-api/docs/pricing, Stand 2026-04-09). Neu eingetragen: `gpt-5.4`, `gpt-5.4-mini`, `gemini-3-flash-preview`, `gemini-3.1-pro-preview`, `o1`, `gemini-2.5-pro` sowie neue Provider-Sektionen (`ollama_cloud`, `google`, korrigiertes `xai`).
- ✅ **LLM Judge Avg Sterne-Format:** `exporter.py` formatiert `LLM Judge Avg` jetzt als `3.8 ★` im Leaderboard.
- ✅ **`sync_cost_limits.py`:** Neues Dev-Tool (`scripts/dev/`) prüft, ob alle konfigurierten Modelle einen Preiseintrag haben. `--fix`-Flag schreibt automatisch `null`-Platzhalter ein (mit `providers:`-Boundary, duplikatfrei).
- ✅ **`make sync-cost-limits [FIX=1]`:** Makefile-Target für den täglichen Workflow — neues Modell hinzufügen, `make sync-cost-limits FIX=1`, Preis eintragen, `make leaderboard`.
- ✅ **Dokumentiert:** `docs/USER_GUIDE.md` (F.2 Systemgesundheit + neuer Abschnitt "Preisliste abgleichen").

**Vorherige Version (v3.4.1 – Token-Verbrauch im Leaderboard):**

CrucibleMark v3.4.1 ergänzt das Leaderboard um transparente Token-Verbrauchsdaten. Beide Leaderboard-CSVs weisen jetzt `Tokens Total` aus — auf identischer Modul-Basis wie der Total Score (nur `enable_scoring: true`). Das Detailed-Leaderboard enthält zusätzlich eine Aufschlüsselung pro Modul. Damit ist Token-Hunger für API-Nutzer direkt messbar.

**Key Achievements (v3.4.1):**
- ✅ **Tokens Total (Compact + Detailed):** Kumulierte Output-Token-Summe über alle bewerteten Benchmark-Module. Basis: `scoring_df` (identisch mit Total Score) — Political Compass und Info-Module ausgeschlossen, da deren Re-Test-Mengen variieren und Provider-Vergleiche verzerren würden.
- ✅ **Tokens: \<Modul\> (Detailed only):** Aufschlüsselung pro Modul als dynamische Spalten (`Tokens: Code Quality`, `Tokens: UX Writing`, …); alphabetisch sortiert, only scoring modules.
- ✅ **Scoring-Only Basis:** `score_calculator.py` überschreibt nach dem Merge die `tokens_used`-Spalte aus `_aggregate_basic_stats()` mit einer expliziten `scoring_df`-Aggregation, sodass die Tokens-Summe exakt der gleichen Filterbasis folgt wie Routine Score und Reasoning Score.
- ✅ **Dokumentiert:** `README.md` (Key Features), `REF_TODO.md` (Completed), `docs/SCORING_METHODOLOGY.md` (Sektion Token-Verbrauch im Leaderboard).

**Vorherige Version (v3.4.0 – Token-Budget-System & Verbosity-Transparenz):**

CrucibleMark v3.4.0 führt ein datenbasiertes Token-Budget-System ein, das faire Provider-Vergleichbarkeit durch einen direkten `max_tokens`-API-Parameter sicherstellt. Ergänzend dazu liefern neue Transparenz-Schichten in Audit-Logs und Meta-Reviewer-Reports fundierte Einblicke in die Token-Effizienz von Modellen.

**Key Achievements (v3.4.0):**
- ✅ **Token-Budget-System:** `base_runner.py` liest `token_budgets[module_key]` aus `benchmark_config.yaml` und setzt `max_tokens` als direkten API-Parameter — nur wenn ein Budget definiert ist (`None` wird nicht weitergegeben). Reasoning-Module sind bewusst ausgenommen.
- ✅ **Kalibrierte Budget-Werte:** `token_budgets` auf 2× Modul-Median gesetzt: `cultural_intelligence: 500`, `ux_writing: 3500`, `content_transformation: 3500`, `documentation_quality: 6000`, `code_quality: 6000`. `cli_benchmark` ohne Limit (entfernt).
- ✅ **Token-Effizienz-Flag in Audit-Logs:** Neuer `[!NOTE]`-Block in `benchmark_utils.py` — Trigger: `token_limit_cutoff is True AND _budget is not None`.
- ✅ **Token-Effizienz-Kontext in Meta-Reviews:** `generate_review.py` injiziert modulspezifische Ø-Token-Werte (Modell vs. Fleet-Median) via `{token_efficiency_context}`. `meta_reviewer_prompt.yaml` enthält neuen Diagnostik-Block für Ratio > 1.5× Median.

**Vorherige Version (v3.3.1 – Political Compass Integration Fix):**
- ✅ **Political Compass: model_category-Feld:** `io_manager.py` schreibt jetzt `model_category` (`local` / `cloud` / `commercial`) in die Leaderboard-CSV — analog zur bestehenden Logik in `result_manager.py`.
- ✅ **Cloud-Erkennung bei PC-Write:** `provider_type` wird für Ollama-gehostete Cloud-Modelle (`:cloud`-Suffix) korrekt auf `cloud` gesetzt statt `ollama`.
- ✅ **Upsert-Parität:** `political_compass_handler.py`'s `_update_local_pc_csv()` dedupliziert jetzt per Upsert (identisch zur kommerziellen Variante); kein append-only mehr.
- ✅ **clean_results.py vollständig:** `political_compass_leaderboard.csv` ist jetzt in der Dateiliste; defensiver `asset_id`-Guard verhindert KeyError bei PC-CSVs ohne diese Spalte.
- ✅ **CSV-Datenbereinigung:** Leaderboard-CSV bereinigt: 66 → 56 Zeilen (Duplikate entfernt, letzter Eintrag behalten), `model_category` rückwirkend für alle 56 Einträge befüllt, `provider_type` für 8 Cloud-Modelle korrigiert.
- ✅ **Anomalie-Cleanup:** 6 historische Cloud-Modell-Einträge aus `local_models_benchmark.csv` entfernt (495 → 489 Zeilen).

**Vorherige Version (v3.3.0 – Language Compliance + Prompt Hardening):**

CrucibleMark v3.3.0 führt eine sprachkonforme Evaluierungsebene ein und schließt eine systemweite redaktionelle Bereinigung aller YAML-Benchmark-Assets ab. Die Language-Compliance-Pipeline ermöglicht es, pro Asset eine Pflichtsprache zu definieren, die der LLM-Judge automatisch mit gewichteter Penalty-Logik bewertet. Gleichzeitig wurden in einem vollständigen Editorial Audit 30 Gemini-generierte Artefakte aus 21 Assets bereinigt und die Bewertungsgrundlage aller betroffenen Module reaktiviert.

**Key Achievements (v3.3.0):**
- ✅ **Language Compliance Pipeline:** `judge_prompt_builder.py` unterstützt `required_language` + `language_weight`; Judge-Rubrik wird automatisch um einen gewichteten Sprachkonformitäts-Block ergänzt (Standard: 20 % des Scores).
- ✅ **Prompt Hardening (30 Fixes, 21 Assets):** Token-Limit-Leaks (13×), Höflichkeitsformeln (13×), Gemini-Pseudolabels (2×), Erfülle-Floskel (5×) vollständig aus 5 Modulen entfernt.
- ✅ **Unicode-Artefakt-Fix:** 3 kyrillische Zeichen in `asset_6a` durch korrekte lateinische Entsprechungen ersetzt. Systemweiter Scan bestätigt alle übrigen 42 Assets clean.
- ✅ **Golden Standard Korrektur:** Grammatikfehler in `asset_6e` (deutscher Artikel) behoben.
- ✅ **Metacog Language Enforcement:** `reasoning_logic` metacog_001–005 mit `language: de` Metadaten und Deutsch-Constraint versehen.
- ✅ **Audit-Infrastruktur:** Neues `docs/audits/`-Verzeichnis; erster Audit-Report archiviert.
- ✅ **Stale Data Cleanup:** 492 obsolete Benchmark-Zeilen aus 3 CSVs für die 5 geänderten Module entfernt (werden beim nächsten Run neu befüllt).

**Vorherige Version (v3.2.2 – 3-CSV Architecture & SSOT Completion):**
CrucibleMark v3.2.2 schließt die vollständige Single Source of Truth Separation ab, indem die alte 2-CSV Architektur durch eine logisch trennscharfe 3-CSV Architektur ersetzt wurde. Das Framework unterscheidet im Ausführungs- und Evaluierungskontext nun strukturell perfekt zwischen lokalen VRAM-Modellen, Commercial API-Modellen und den neuen Cloud Open-Weights Proxies.

**Key Achievements (v3.2.2):**
- ✅ **3-CSV Data Architecture:** Vollständige Abkehr vom fehleranfälligen "Local Cloud" Konstrukt in ein dediziertes `cloud_models_benchmark.csv` Logging.
- ✅ **Meta-Review & LLM-Judge Context Fix:** Anpassung der generativen Injektion für "Cloud Open-Weights"-Modelle, sodass diese vom Evaluator nicht fälschlicherweise für "lokale Hardware-Limitierungen" penalisiert werden.

**Vorherige Version (v3.2.1 – Performance & Cache Repair):**
CrucibleMark v3.2.1 liefert tiefgreifende Performance-Optimierungen durch die Implementierung von Lazy-Loading für schwergewichtige ML-Module (wie `sentence_transformers` und `sklearn`), wodurch sich die Boot-Zeiten drastisch verkürzen. Zudem wurde nach der Architektur-Bereinigung auf den `UnifiedBenchmarkRunner` ein potenziell kritischer Cache/Routing-Fehler zwischen lokalen und kommerziellen Scores identifiziert und nachhaltig isoliert.

**Key Achievements (v3.2.1):**
- ✅ **Lazy Loading von Transformers:** Massiv beschleunigte Boot-Time durch inline Importe in mathematischen Scores (Cosine Similarity).
- ✅ **API Connectivity Fix (Groq):** Der Deprecation-Status von `llama3-8b-8192` bei Groq wurde erkannt und der Test-Bouncer modernisiert, wodurch groq-Modelle wieder fehlerfrei zugelassen werden.
- ✅ **Terminal Metrics Restore:** Laufzeit-Statistiken (Score, Tokendichte, Preise & Dauer) werden pro Modul nun wieder dynamisch als Summary im CLI konsolidiert ausgegeben (`base_runner`/`unified_runner`).
- ✅ **Data-Routing Bugfix & Cache Repair:** Ein Fehler der UnifiedRunner, bei dem kommerzielle Ergebnisse fälschlicherweise den lokalen Logs zugeteilt wurden und der Resume/Autofill-Zyklus kollabierte, wurde hardcodiert behoben. Alle betroffenen Scores wurden duplikatfrei repariert und in ihr rechtmäßiges CSV-Target verschoben.
- ✅ **Strict SSOT Enforcement & Fail-Fast (v3.2.0):** Versteckte Modellausweichmechanismen (z.B. automatisiertes Laden von `claude-3-5-sonnet` oder `mistral-large-latest` bei ungenauen Modellnamen im Provider) wurden vollständig restlos entfernt. Das System nutzt nur exakt das, was in der Config steht (`ValueError` bei Fehlern).
- ✅ **Dynamic Provider & Category Rendering:** Die Zuweisung von Modell-Kategorien (Commercial, Cloud (Open-Weights), Local) wurde vollständig in die Konfiguration überführt. Der veraltete Begriff "Local Cloud" wurde aus UI und Analyse entfernt. "Open-Weights"-Provider wie Groq sind nun vollwertig integriert.
- ✅ **Provider Code Perfection & Type Safety:** Die API-Integrationen im `utils/providers/`-Verzeichnis wurden radikal aufgeräumt. Der Pylint-Score aller Provider erreicht makellose 10.00/10, tote Imports und Codeabschnitte wurden entfernt. Pylance Type-Checker False-Positives (bspw. `reportPrivateImportUsage` im Google SDK) wurden per Pyright-Direktiven sauber unterdrückt.
- ✅ **Judge Skip Clarification & Meta-Context:** Das UI und Log-Output wurden verbessert, um `⚠️ Judge: skip (zu kurz/abgelehnt)` auszuweisen. Zudem erhält der Judge für "Cloud (Open-Weights)"-Modelle nun immer den korrekten Cloud-Hardwarekontext injiziert, um fehlerhafte Hardware-Bewertugen zu unterbinden.

**Vorherige Version (v3.1.0 – Audit- & Meta-Review Generation):**
CrucibleMark v3.1.0 verbessert den "LLM-as-a-Judge"-Flow radikal und eliminiert Judge-Halluzinationen in finalen Audit- und Trend-Reports. Hochgradig kalibrierte Prompt-Mechaniken sorgen für fehlerfreies Markdown-Parsing und verhindern, dass Modellen eine menschlich-aktive Denkweise angedichtet wird.

**Key Achievements (v3.1.0):**
- ✅ **Meta-Reviewer Stabilisierung & Anchoring:** Der Off-by-One Fehler beim Einlesen langer Markdown-Audit-Logs durch den Judge (z.B. Gemini) wurde behoben. Strukturierte "ID-Anchor" (wie z.B. 7.2.001) wurden in der Prompt-Datei implementiert, damit das Modell auch bei hunderten Zeilen Log-Code fehlerfrei trackt.
- ✅ **Grammar-Restrictions gegen aktive Halluzination:** Der Meta-Review-Prompt forciert nun striktes Passiv- und Objekt-Wording (z.B. verbietet Wörter wie "versucht", "scheitert", "weicht aus"), um insbesondere im Zusammenfassungs-Bereich (Fazit) zu verhindern, dass die Review-Modelle dem getesteten LLM eigenständigen menschlichen Willen oder Agenden andichten.
- ✅ **Automatisierte Metadaten-Extraktion:** Laufzeit-Warnings (`⚠️ Anomaly Verification Protocol`), Hard-Refusal Raten und Token-Fallback Informationen werden per Regex in den Reports identifiziert und direkt als Kontext für den LLM-Judge bereitgestellt. Der Meta-Reviewer kann so architektonische Limits und Zensurunterschiede bei der finalen Bewertung optimal einordnen.

**Vorherige Version (v3.0.0 – Safety & Refusal Architecture):**
CrucibleMark v3.0.0 härtet die Evaluierung stark regulierter Modelle (z. B. Claude, Gemini) durch eine neuartige **3-Tier Refusal Engine**. Das Framework durchbricht Zensur-Blockaden proaktiv durch schrittweises "Progressive Temperature Scaling" und System-Injektionen.

**Key Achievements (v3.0.0):**
- ✅ **3-Tier Refusal Architecture:** CrucibleMark unterscheidet nahtlos zwischen temporären API-Timeouts, Soft-Refusals (Ausweich-Text) und Hard-Refusals und wiederholt Testblöcke bei Modellen, die sich bevormundend verhalten, völlig automatisch.
- ✅ **Progressive Temperature & Safety Shifts:** Automatisiertes Erhöhen der Kreativität bei Ablehnungen (`0.1 → 0.4 → 0.7`), inkl. theoretischer Aufarbeitung in der Systemdokumentation.
- ✅ **Pydantic Serialization Bugfix:** Abstürze beim Auswerten von verschachtelten Metriken (`Vanilla_X`/`Vanilla_Y`) in Verify-Skripten wurden behoben (Umstellung auf `json.loads(raw_response)`).
- ✅ **Public Presentation Overhaul:** Reduktion der technischen Schuld durch das vollständige Neuschreiben der `README.md` und das Bereinigen veralteter Code-Artefakte.

**Vorherige Version (v2.6.1 – Stability & Context Handling):**
CrucibleMark v2.6.1 bringt wichtige Stabilitäts-Patches für die API-Kommunikation (inkl. Token-Loop-Halluzinations-Fallback für Modelle wie Gemini) und überarbeitet die Dokumentationsstruktur entlang der Konfigurations-Assets.

**Key Achievements (v2.6.1):**
- ✅ **Halluzinations-Prävention:** Auto-Truncation in `llm_client.py` eingebaut, um "Token-Loops" (z.B. endlose Leerzeichen-Generierung) bei kommerziellen APIs (Gemini 2.5 Flash) abzufangen. Entsprechende Warn-Flags (`⚠️ SYSTEM INFO`) wurden zum Metareview-Audit-Log hinzugefügt.
- ✅ **Dokumentations-Konsolidierung:** Die `README.md` Modulliste wurde an die logische Kategorisierung (Hard Skills, Core Metrics, Soft Skills, Sonstige) aus der `benchmark_config.yaml` angeglichen; die Aufzählung wurde von 6 auf alle 8 aktiven Module korrigiert.
- ✅ **Cleanup:** Entfernung obsoleter Check-Skripte (`fix_test_file.py`, `mypy_out.txt`) und tiefere Modul-Refactorings für einen sauberen Root-Workspace.

**Vorherige Version (v2.6.0 – Metric Accuracy & Bias Prevention):**
CrucibleMark v2.6.0 garantiert mathematisch einwandfreie Metriken und beseitigt Position/Token-Bias im Political Compass Modul durch dynamisches Alpha-Mapping.

**Key Achievements (v2.6.0):**
- ✅ **Metrics Accuracy:** Behebung des Leaderboard-Numerator-Bugs (44/43 Tests Run), indem nicht-punktende Module (wie Political Compass) beim Parsing vollständig ignoriert werden.
- ✅ **Bias Prevention:** Alpha-Randomization in Multiple Choice Setups eingebaut, um LLM-Primacy/Token-Gedächtniseffekte (Drift zur Mitte) zu verhindern.
- ✅ **Meta-Reviewer Tuning:** Prompt-Überarbeitung gegen Halluzinationen (verhindert, dass der Meta-Reviewer generative Argumentationen herbeifantasiert, wo nur Choice-Optionen gewählt wurden).
- ✅ **Human Baseline Script:** `run_human_compass.py` umstrukturiert auf direkte Nummern-Eingaben für validierbare Human-Benchmarks.

**Vorherige Version (v2.5.0):**
CrucibleMark v2.5.0 schließt die SSOT-Migration ab. Die alte, dynamische "Golden Standard Model"-Pipeline entfällt vollständig. Ab sofort gilt ausschließlich eine statische "Design by Intention"-Evaluierung via LLM-Judge auf Basis der `asset.yaml`.

- ✅ **Architectural Deprecation:** Vollständiges Entfernen des `--mode golden_standard` in Kommandozeilen. Kein Referenz-Modell generiert mehr dynamische Responses für den Vergleich.
- ✅ **Clean Runner Logic:** `run_commercial_benchmark.py` & `run_local_benchmark.py` verarbeiten nur noch den puren Test-Modus ohne komplexe Interaktionen.
- ✅ **Leaderboard Isolation:** Evaluierung nutzt jetzt 1:1 die rohen Prozent-Werte des Intent-Judges; die fehleranfällige, relative Berechnungslogik (`performance_ratio`) zur Referenz wurde gelöscht.
- ✅ **Validation Tools Cleanup:** Veraltete Analyse- und Validator-Skripte wie `validate_golden_standards.py` getilgt.

**Vorherige Version (v2.4.1):**
- ✅ **Golden Standard Consolidation (SSOT):** 37 `golden_standard` Konfigurationen über alle YAML-Assets strukturell validiert. Die manuell verdichteten Standards fungieren nun offiziell als "Design by Intention" Ground Truth.
- ✅ **Validation Tooling:** Einführung von `scripts/analysis/validate_golden_standards.py` zur LLM-basierten Validierung (Claude Haiku) von Aufgaben-Assets.
- ✅ **Storage Cleanup:** Entfernung der obsoleten Roh-Referenz-Logs (`outputs/reference-logs/`), um den Fokus auf qualitätsgesicherte, manuelle Golden Standards zu legen und pedantische LLM-False-Positives zu vermeiden.

**Vorherige Version (v2.4.0):**
- ✅ **Audit Mode Logging:** Vollständige Markdown-Protokollierung mit dynamischem `evaluated_prompt`, regelbasierten Category-Scores und LLM-Judge Reasoning.
- ✅ **LLM Judge Pipeline:** Vollständige Integration von 4 Providern (Ollama, Anthropic, Mistral, OpenAI) mit automatischer Fallback-Chain.
- ✅ **Bulletproof Parsing:** Robuster Regex-Parser, der auch Markdown-Ausreißer von Modellen (z.B. `### **SCORE:**`) sicher verarbeitet.
- ✅ **Lifecycle Management:** Isolierte Lade/Entlade-Zyklen (Ollama) mit Delays für fehlerfreie VRAM-Freigabe, Timeout-Resilienz (120s).
- ✅ **Leaderboard & Metric Stability:** Leaderboard Typ-Konvertierungen und Pydantic Validierungen gehärtet. 165+ Tests Passed.

**Vorherige Version (v2.2.0):**
- LLM Judge Pipeline Kernarchitektur

**Vorherige Version (v2.1.1):**
- Leaderboard & Aggregation Update
- Pydantic Migration für Typ-Sicherheit
- Political Compass Batch Mode


## 📊 Module Status Overview

### Production-Ready Modules (8/8) ✅

| # | Module | Version | Pylint | Status | Assets | Features |
|---|--------|---------|--------|--------|--------|----------|
| 1 | **Code Quality Audit** | v2.0.1 | 9.2/10 | ✅ Prod | 25 files | 3 tiers, pattern scoring |
| 2 | **CLI Operations** | v1.0 | 9.0/10 | ✅ Prod | 6 files | Fast-Fail Batch Mode |
| 3 | **UX Writing & Microcopy** | v2.0 | 8.8/10 | ✅ Prod | 20 scenarios | Tone analysis, keyword checks |
| 4 | **Documentation Quality** | v2.0 | 9.0/10 | ✅ Prod | 15 tasks | Completeness metrics |
| 5 | **Content Transformation** | v2.0.1 | 8.9/10 | ✅ Prod | 12 pieces | Tone adaptation, format conversion |
| 6 | **Cultural Intelligence** | v2.0 | 9.1/10 | ✅ Prod | 18 scenarios | Idiom understanding, cultural context |
| 7 | **Logical Reasoning** | v1.0 | 9.0/10 | ✅ Prod | 11 scenarios | Paradox detection, Metacognition |
| 8 | **Political Compass** | v3.1.0 | 9.85/10 | ✅ Prod | 74 questions | Batch mode, 3 runs, variance analysis |

**Average Code Quality:** 9.15/10 (Elite-Level) 🏆

______________________________________________________________________

## 🏗️ Framework Architecture Status

### Core Components ✅

#### 1. Module System

```
✅ Modular architecture
✅ Plugin-based design
✅ Standardized interfaces (BaseTest)
✅ YAML configuration per module
✅ Asset-based test cases
```

#### 2. Provider System

```
✅ Unified client interface
✅ Ollama support (local models)
✅ OpenAI support (GPT-4, GPT-4o)
✅ Anthropic support (Claude 3.5)
✅ Mock provider (testing)
✅ Error handling & retries
```

#### 3. Scoring System

```
✅ Pattern-based scoring (regex, keywords)
✅ Absolute Standard Scoring (Gold/Silver/Bronze)
✅ Speed Classification (Fast/Medium/Slow)
✅ Automated Skill Profiling
✅ LLM-as-Judge (seit v2.4.0)
```

#### 4. Output System

```
✅ CSV export (local_models_benchmark.csv)
✅ CSV export (commercial_models_benchmark.csv)
✅ Leaderboard generation
✅ Individual module results (e.g., political_compass_results.csv)
✅ Checkpoint/resume functionality
```

#### 5. Configuration System

```
✅ YAML-based module configs
✅ Execution modes (single, batch)
✅ Scoring configuration
✅ Leaderboard integration settings
✅ Provider-specific settings
```

______________________________________________________________________

## 📈 Code Quality Metrics

### Framework-Level Metrics

| Metric | Target | Achieved | Status |
|--------|--------|----------|--------|
| **Average Pylint Score** | 8.5/10 | 9.15/10 | ✅ Exceeded |
| **Type Hints Coverage** | 90% | 100% (public APIs) | ✅ Exceeded |
| **Docstring Coverage** | 90% | 100% (public methods) | ✅ Exceeded |
| **Test Coverage** | 95% | ~60% (critical paths) | ⚠️ In Progress |
| **Black Compliance** | 100% | 100% | ✅ Complete |
| **isort Compliance** | 100% | 100% | ✅ Complete |

### Module-Level Breakdown

**Top Performers (9.0+/10):**

- Political Compass: 9.85/10 🏆
- Code Quality Audit: 9.2/10
- Cultural Intelligence: 9.1/10
- Documentation Quality: 9.0/10

**Good (8.5-9.0/10):**

- Content Transformation: 8.9/10
- UX Writing & Microcopy: 8.8/10

Alle Module überschreiten den Industry-Standard-Schwellenwert (8.0+).

______________________________________________________________________

## ✅ Historische Meilensteine (v1.x)

Die v1.x-Phase legte die Modul-Infrastruktur, den Provider-Abstraktions-Layer und das erste Scoring-System. Die wesentlichen Meilensteine in Kurzform:

- Modulare Architektur mit BaseTest Interface, YAML-Konfiguration und Asset-Driven Testing
- Unified Provider Interface für alle LLM-Anbieter, Mock-Provider für Tests
- Unified CSV-Schema, Leaderboard, Checkpoint/Resume-System
- Refaktorierung aller 6 Kernmodule auf Pylint 8.8–9.85/10
- DeepSeek-R1 Reasoning Model Support (v1.1.3): `is_reasoning_model()`-Erkennung, erhöhter Warmup-Probe auf 50 Tokens
- Versioning System Overhaul: Dual-Version-Format (`{OFFICIAL_ID}-{BEHAVIORAL_HASH}`), `utils/fingerprinting.py` als SSOT
- Golden Standard Consolidation: 37 `golden_standard`-Konfigurationen über alle YAML-Assets validiert
- LLM-as-Judge vollständig integriert (v2.4.0): 4 Provider, Fallback-Chain, Audit Mode Logging

______________________________________________________________________

## ⚠️ Known Gaps & Limitations

### 1. Testing Infrastructure

**Status:** In Progress (60% coverage)

**Current:**

- ✅ Mock provider tests
- ✅ Integration tests (basic)
- ⚠️ Unit tests incomplete (60% coverage)
- ❌ CI/CD pipeline missing

**Target:**

- [ ] Unit tests 95%+ coverage
- [ ] GitHub Actions CI/CD
- [ ] Automated pylint checks
- [ ] Performance benchmarks

### 2. User Interface

**Status:** CLI-only

**Geplant:**

- [ ] Web UI (basic dashboard)
- [ ] Real-time progress visualization
- [ ] Interactive result exploration

______________________________________________________________________

## 🗺️ Roadmap

Die vollständige Roadmap steht in [README.md](README.md). Stand Q1/Q2 2026 konzentriert sich die Entwicklung auf:

- [ ] **Agentic Workflow Benchmarks:** Native Tests für Multi-Step Tool-Usage (Welches Modell plant komplexe File-Edits am sichersten?).
- [ ] **Visuelles Sub-System (Multimodal):** Integration visueller Benchmarks zur Architekturanalyse (UML-Diagramm lesen, UI designen).
- [ ] **Web-UI / Dashboard:** Eine interaktive React- oder Streamlit-Umgebung zur Visualisierung der CSV-Output-Ergebnisse und Leaderboards.
- [ ] **Erweiterung von CI/CD System-Hooks:** Automatische Integration für GitHub Actions, um KI-Akteure in Pull Requests zu prüfen.

______________________________________________________________________

## 🎯 Strategic Priorities

### Kurzfristig

1. **Test Coverage abschließen** (60% → 95%)
2. **CI/CD einrichten** (GitHub Actions)
3. **E2E Systemtests** (Volldurchlauf aller lokalen Modelle, finales Leaderboard)

### Mittelfristig

1. **Externes Frontend starten** (`cruciblemark-web`, 11ty-basiert)
2. **Agentic Workflow Benchmarks** (neue Testdimension)
3. **Multimodal Support** (visuelle Benchmarks)

______________________________________________________________________

## 📈 Success Metrics

### v3.2.0 Achievements

- ✅ 8/8 Module Production-Ready
- ✅ Pylint Score Provider-Layer: 10.00/10
- ✅ Average Pylint Score: 9.15/10 (Ziel: 8.5)
- ✅ 100% Type Hints auf Public APIs
- ✅ 100% Docstring Coverage
- ✅ SSOT erzwungen, Fail-Fast aktiv, keine versteckten Fallbacks

______________________________________________________________________

## 🔬 Research & Development

### Aktive Forschungsbereiche

#### 1. Agentic Workflow Evaluation

Welche Modelle planen komplexe Multi-Step Tool-Usage-Szenarien zuverlässig? Wie misst man Planungsqualität ohne Ground Truth? Die Antwort erfordert neue Asset-Formate und einen erweiterten Judge-Mechanismus.

**Status:** Konzeptphase

#### 2. Multimodal Benchmarks

Visuelle Aufgaben (UML lesen, UI-Designs beurteilen) benötigen neue Asset-Formate und Judge-Mechanismen jenseits von Text-Matching.

**Status:** Design-Phase

______________________________________________________________________

## 🤝 Community & Contributions

### Aktueller Status

- **Repository:** Public (GitHub)
- **License:** MIT
- **Contributors:** 1 (maintainer)
- **Issues:** 0 open
- **Pull Requests:** 0 open

### Ziel

- [ ] First external contribution
- [ ] Community feedback integration
- [ ] Issue tracking system
- [ ] Contributor guidelines published

______________________________________________________________________

## 📄 Documentation Status

### Completed ✅

- [x] Root README (v3.2.0)
- [x] Module READMEs (8/8)
- [x] Configuration docs
- [x] Contributing guidelines
- [x] REF_TODO.md (updated)
- [x] PROJECT_STATUS.md (this file)

### In Progress 🔄

- [ ] API reference docs
- [ ] Architecture deep-dive
- [ ] Tutorial series

### Planned 📅

- [ ] FAQ document
- [ ] Troubleshooting guide
- [ ] Video tutorials
- [ ] Blog posts (use cases)

______________________________________________________________________

## 🚨 Risk Assessment

### Technical Risks

#### 1. Test Coverage Gaps

**Risk:** Bugs in production due to low test coverage\
**Mitigation:** Fokus auf Unit Tests, GitHub Actions CI/CD\
**Priority:** High

### Business Risks

#### 1. Maintenance Burden

**Risk:** Single maintainer cannot sustain project\
**Mitigation:** Community building, documentation\
**Priority:** Medium

______________________________________________________________________

## 📞 Contact & Maintainer

**Maintainer:** kbeissert\
**Repository:** [github.com/kbeissert/cruciblemark](https://github.com/kbeissert/cruciblemark)\
**Issues:** [GitHub Issues](https://github.com/kbeissert/cruciblemark/issues)

______________________________________________________________________

## 📝 Change Log Summary

### v3.2.0 (2026-03-25) – Strict SSOT & Full Provider Refactoring

- Alle versteckten Modell-Fallbacks auf Provider-Ebene entfernt
- Pylint 10/10 für alle Provider-Integrationen (`utils/providers/`)
- Pyright-Direktiven für Google SDK `reportPrivateImportUsage` False-Positives
- "Judge: skip (zu kurz/abgelehnt)" im UI und Log-Output implementiert

### v3.1.0 – Audit- & Meta-Review Generation

- Off-by-One-Bug im Meta-Reviewer bei langen Markdown-Logs behoben
- Strukturierte ID-Anker (z. B. 7.2.001) in `meta_reviewer_prompt.yaml`
- Grammar-Restrictions gegen aktive Halluzination (Passiv- und Objekt-Wording)
- Automatisierte Metadaten-Extraktion per Regex (Hard-Refusal Raten, Token-Fallbacks)

### v3.0.0 – Safety & Refusal Architecture

- 3-Tier Refusal Architecture (API-Timeout vs. Soft- vs. Hard-Refusal)
- Progressive Temperature Scaling (`0.1 → 0.4 → 0.7`)
- Pydantic Serialization Bugfix für verschachtelte Metriken

### v2.6.x – Stability, Metrics & Bias Prevention

- Token-Loop-Halluzination Fallback (Auto-Truncation, Gemini 2.5 Flash)
- Leaderboard-Numerator-Bug behoben (44/43 → korrekt)
- Alpha-Randomization gegen Position/Token-Bias in Multiple Choice

______________________________________________________________________

**Document Version:** 3.0\
**Last Updated:** 2026-03-25\
**Next Review:** Web Frontend Release
