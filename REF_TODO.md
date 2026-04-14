# REF_TODO.md – Refactoring & Future Development

## Abgeschlossen

### PC Skip-Logic Fix & Leaderboard-Bereinigung (v3.4.6 – 14.04.26)
- [x] **`utils/base_runner.py` — PC Skip-Logic-Fallback:** `execute_batch_module()` liest `benchmark_scores/political_compass_leaderboard.csv` direkt, wenn Standard-CSV-Cache leer ist (Post-Reset-Szenario). Aktiviert nur für PC-Module via `PoliticalCompassHandler.is_political_compass()`. Graceful-Fallback bei `OSError`/`csv.Error`.
- [x] **PC-Leaderboard-Bereinigung:** 11 Einträge mit korrupten Koordinaten (runde Ganzzahlwerte aus Verweigerungssession 23.03.2026) entfernt. Leaderboard: 31 → 20 verifizierte Einträge. Backup: `political_compass_leaderboard.bak_20260414_222150.csv`. 31 Modelle für Re-Run freigegeben.
- [x] **`.github/copilot-instructions.md`:** Fallstrick „PC Skip-Logic Gap" dokumentiert.

### Architektur-Code-Review & Magic-String/Number-Elimination (v3.4.4 – 11.04.26)
- [x] **`utils/constants.py` — 12 neue Konstanten:** `MODEL_TYPE_OPEN_WEIGHTS_CLOUD`, `RESULT_TYPE_LOCAL/CLOUD/COMMERCIAL`, `TIMEOUT_OLLAMA_HEALTH/LIST_FAST/LIST/VERSION/WARMUP`, `TIMEOUT_HTTP_FETCH`, `TIMEOUT_ANTHROPIC_API` als SSOT definiert.
- [x] **Magic Strings/Numbers aus 8 Dateien eliminiert:** `result_manager.py`, `model_utils.py`, `providers/anthropic.py`, `pricing_updater.py`, `benchmark_auto.py`, `unified_runner.py`, `run_cross_model_benchmark.py`, `list_models.py` referenzieren alle Werte ausschließlich via `constants.py`.
- [x] **Verifikation:** 163/163 pytest passed, mypy clean (9 Dateien). Commit 95f2055, Tag v3.4.4.

### Dokumentation: Redaktionelle Überarbeitung (11.04.26)
- [x] **14 Dokumentationsdateien (README.md + docs/) einheitlich überarbeitet:** Ansprache (`du`/`dein`) → unpersönliches `man`/`sein`; alle Emojis aus Überschriften entfernt (nur 🛑 als Warnmarker behalten); alle englischen H1–H3 ins Deutsche übertragen; einheitliche Intro-Blöcke (`**Zielgruppe:**` / `**Inhalt:**` / `> **Voraussetzung:**`) ergänzt; alle `______`-Trennlinien → `---`.
- [x] **`module_weight`-Feld in alle 7 Modul-`config.yaml`s:** Neues `integration.leaderboard.module_weight`-Key pro Modul. Vollmodule je `1.0`, CLI `0.5` (Supplement, kein vollwertiges Evaluierungsmodul). Direkter YAML-Hebel für kundenspezifische Gewichtung ohne Code-Änderung.
- [x] **`score_calculator.py: _module_scale()`:** Hilfsfunktion berechnet `scale = module_weight / config_weight_sum` — self-normalizing, kein hardcodierter Kehrwert nötig. Alle 4 Contrib-Spalten (`final_routine`, `final_reasoning`, `weight_routine`, `weight_reasoning`) werden vor Aggregation mit `scale` multipliziert.
- [x] **`scripts/leaderboard/__init__.py`:** `module_weight` aus `lb_config.get("module_weight")` ins `mod_entry`-Dict propagiert. `None`-Fallback → `scale = 1.0` (Rückwärtskompatibilität).
- [x] **5 neue Ollama-Cloud-Modelle in `config/cost_limits.yaml`:** `deepseek-v3.1:671b-cloud` ($0.28/$0.42 per 1M Input/Output), `qwen3.5:397b-cloud`, `gemma4:31b-cloud`, `kimi-k2.5:cloud`, `glm-5:cloud`.
- [x] **`docs/BENCHMARK_MODULES.md`:** Abschnitt "Designprinzip: Module als gleichwertige, geschlossene Tests" mit Erklärung der `module_weight`-Konfiguration und CLI-Sonderfall ergänzt.
- [x] **`docs/SCORING_METHODOLOGY.md`:** Formel auf selbstnormierende Variante aktualisiert (`Σ(score × weight) / Σ(weight)`). Neue Sektion "Modulgewichtung" mit Default-Gewichtstabelle und Konfigurationshinweis.

### Vollständige Modell-Preisliste & Sync-Tool (v3.4.2 – 09.04.26)
- [x] **config/cost_limits.yaml: Vollständige Preis-Datenbasis:** Alle 25 konfigurierten Cloud-/Commercial-Modelle haben jetzt verifizierte Preiseinträge. Neue Sektionen: `ollama_cloud`, `google`; `xai` aus `settings:` in `providers:` verschoben.
- [x] **exporter.py: LLM Judge Avg Sterne-Format:** `_format_judge_stars()` formatiert den Wert als `3.8 ★` im Compact- und Detailed-Leaderboard.
- [x] **scripts/dev/sync_cost_limits.py:** Neues Dev-Tool. Vergleicht konfigurierte Modelle gegen `cost_limits.yaml`, meldet Missing-Entries. `--fix` schreibt `null`-Platzhalter — boundary-sicher (`providers_start/end`) und duplikatfrei.
- [x] **Makefile: `sync-cost-limits [FIX=1]`:** Neues Target für den standardisierten Pricing-Workflow.
- [x] **docs/USER_GUIDE.md:** `make sync-cost-limits` in F.2 Systemgesundheit dokumentiert + eigenständiger Workflow-Abschnitt "Preisliste abgleichen" ergänzt.

### Token-Verbrauch im Leaderboard (v3.4.1 – 08.04.26)
- [x] **score_calculator.py: scoring_df im calculate_scores():** Lokale `scoring_df`-Variable aus `cat_to_scoring`-Map aufgebaut (analog zu `_aggregate_basic_stats()`), damit Token-Aggregation dieselbe Modul-Basis wie der Total Score nutzt.
- [x] **score_calculator.py: Tokens Total Korrektur:** `tokens_used`-Summe aus `_aggregate_basic_stats()` (inkl. Political Compass) wird nach dem Merge überschrieben — neue Summe nur über `scoring_df` (enable_scoring=True). Verhindert Verzerrung durch variable PC-Retest-Mengen.
- [x] **score_calculator.py: Tokens: \<Modul\>-Spalten:** `token_by_module`-Block unpivotiert Token-Summen pro `(model, model_version, category)` aus `scoring_df` und prefixiert Spalten mit `Tokens: `. Political Compass bleibt ausgeschlossen.
- [x] **exporter.py: Compact-Leaderboard:** `Tokens Total` nach `Cost per 1K (USD)` eingefügt.
- [x] **exporter.py: Detailed-Leaderboard:** `Tokens Total` + alle dynamischen `Tokens: <Modul>`-Spalten (alphabetisch sortiert) ergänzt.
- [x] **README.md: Key Features:** Neuer Bullet-Punkt "Token-Verbrauch im Leaderboard" ergänzt.
- [x] **docs/SCORING_METHODOLOGY.md: Dokumentation:** Neue Sektion "Token-Verbrauch im Leaderboard" mit Tabelle, Begründung und Kosten-Kontext (API vs. Flat-Rate) eingefügt.

### Token-Budget-System & Verbosity-Transparenz (v3.4.0 – 08.04.26)
- [x] **base_runner.py: max_tokens API-Cap:** `execute_test_module()` liest `token_budgets[module_key]` aus der Config und übergibt `max_tokens=budget` NUR wenn budget nicht `None` ist. Kein None-Wert wird an Provider-Clients weitergegeben. Reasoning/Metacog/CLI ohne Limit (by design).
- [x] **benchmark_config.yaml: token_budgets kalibriert:** Werte auf 2× Modul-Median gesetzt: `cultural_intelligence: 500`, `ux_writing: 3500`, `content_transformation: 3500`, `documentation_quality: 6000`, `code_quality: 6000`. `cli_benchmark` entfernt.
- [x] **benchmark_utils.py: Token-Effizienz-Flag im Audit-Log:** Neuer `[!NOTE]`-Header-Block wenn `token_limit_cutoff is True AND _budget is not None`. Bestehender `[!CAUTION]`-Block bleibt unverändert.
- [x] **generate_review.py: Token-Effizienz-Kontext:** Neue Template-Variable `{token_efficiency_context}` injiziert modulspezifische Ø-Token-Werte (Modell vs. Fleet-Median) vor `{log_data}`.
- [x] **meta_reviewer_prompt.yaml: Verbosity-Diagnostik:** Neuer Block "Token-Effizienz (Verbosity)" — Reviewer schreibt Pflicht-Absatz wenn Ratio > 1.5× Median (Reasoning/Metacog ausgenommen).

### Political Compass Integration Fix (v3.3.1 – 08.04.26)
- [x] **io_manager.py: model_category-Feld:** `save_leaderboard_csv()` schreibt jetzt `model_category` (`local` / `cloud` / `commercial`) in die Leaderboard-CSV (nach `model`-Spalte); Routing-Logik analog `result_manager.py`.
- [x] **io_manager.py: provider_type-Korrektur:** Ollama-gehostete Cloud-Modelle (`:cloud`-Suffix) erhalten `provider_type=cloud` statt `ollama`.
- [x] **political_compass_handler.py Upsert:** `_update_local_pc_csv()` von append-only auf Upsert umgestellt — Parität zu `_update_commercial_pc_csv()`; eliminiert Duplikate bei Retry/Re-Run.
- [x] **clean_results.py: PC Leaderboard-CSV:** `political_compass_leaderboard.csv` zur `files`-Liste hinzugefügt; defensiver `asset_id`-Guard in `clean_csv()` verhindert KeyError bei PC-CSVs.
- [x] **CSV-Datenbereinigung:** `political_compass_leaderboard.csv` 66 → 56 Zeilen (Duplikate entfernt), `model_category` rückwirkend befüllt, `provider_type` für 8 Cloud-Modelle korrigiert.
- [x] **local_models_benchmark.csv:** 6 historische Cloud-Modell-Einträge entfernt (495 → 489 Zeilen).

### Language Compliance & Prompt Hardening (v3.3.0 – 07.04.26)
- [x] **Language Compliance Pipeline:** `judge_prompt_builder.py` um `required_language` / `language_weight` erweitert. Bei gesetztem Asset-Metadatum `language: de` wird dem Judge automatisch ein LANGUAGE COMPLIANCE Rubrik-Block injiziert (Standard 20 % Gewichtung; Sprachverstoß − 1,5 Punkte, Sprachmix −0,5 Punkte).
- [x] **judge_runner.py Forwarding:** `required_language` und `language_weight` werden aus dem Asset-Config-Dict an `build_prompts()` weitergeleitet.
- [x] **judge_evaluator.py:** `language_mismatch`-Flag wird aus der Judge-Response extrahiert und im Ergebnis-Dict protokolliert.
- [x] **Metacog Language Enforcement:** `reasoning_logic` Assets `metacog_001–005` mit `language: de` Metadatum und explizitem Deutsch-Constraint (`Antworte auf Deutsch.`) versehen.
- [x] **Editorial Audit (30 Fixes, 21 Assets):** Systemweite Bereinigung aller Gemini-Artefakte über 5 Module:
  - Token-Limit-Leak entfernt aus 13 Prompts (ux_writing, content_transformation, documentation_quality, code_quality)
  - Höflichkeitsformel `Bitte` aus 13 imperativen WICHTIG/HINWEIS-Blöcken gestrichen
  - Gemini-Pseudolabels `Mission:` / `TASK:` aus cultural_intelligence entfernt
  - `Erfülle dabei strikt die folgenden Anforderungen:` → `Anforderungen (strikt einhalten):` in 5 ux_writing Assets
- [x] **Kyrillischer Unicode-Artefakt-Fix:** 3 cyrillische Zeichen (U+043C м, U+0430 а, U+0442 т) in `asset_6a_german_tech_localization.yaml` durch lateinische Entsprechungen ersetzt. Systemweiter Scan: alle 43 übrigen Assets clean.
- [x] **Golden Standard Grammatikfehler:** `ein negatives Entwicklung` → `eine negative Entwicklung` in `asset_6e_german_idioms.yaml`.
- [x] **Stale Data Cleanup:** 492 obsolete Benchmark-Zeilen für geänderte Module aus `local_models_benchmark.csv`, `cloud_models_benchmark.csv`, `commercial_models_benchmark.csv` entfernt.
- [x] **Audit-Infrastruktur:** `docs/audits/`-Verzeichnis angelegt; `AUDIT_2026-04-07_editorial.md` archiviert.

### Audit Fixes & Scoring Integrity (v3.2.2 Patch – 07.04.26)
- [x] **Loop Detection in `llm_parser.py`:** Strukturelle Endlosschleifen (>50 Zeichen, >10× Wiederholung) werden erkannt und mit `> [!ERROR]`-Block ins Audit-Log injiziert.
- [x] **Regex Fix `generate_review.py`:** Multi-Line-Alert-Blöcke (`> [!WARNING]`) werden durch `re.DOTALL` korrekt erfasst.
- [x] **Hard Constraint generisch ausgerollt:** `constraints.max_expected_words` in YAML aktiviert für `ct003` (150W), `ct004` (600W) und `ux_writing_005` (150W). Constraint-Prüfung in beiden Evaluatoren (CT + UX) generisch per YAML-Read.
- [x] **Progressive Penalty-Stufen:** Flat-40%-Abzug durch dreistufige Logik ersetzt: Toleranzzone ≤120%; >120%→−20%, >200%→−40%, >300%→−60% (`tier_label` im Audit-Log dokumentiert).
- [x] **Language-Mismatch Auto-Flag:** Heuristische DE/EN Marker-Frequenzprüfung nach `score_response()` in `unified_runner.py`; setzt `status=language_mismatch` + `> [!WARNING]`-Block.
- [x] **ux_writing_002 Two-Step Enforcement:** Prompt um explizite `[SCHRITT 1 – ANALYSE]` / `[SCHRITT 2 – OPTIMIERUNG]` Header ergänzt.
- [x] **Code Quality Asset Hardening:** `asset_001_wcag_audit.yaml` um WCAG 2.2 Kriterien (Focus Not Obscured 2.4.11, Target Size 2.5.8) erweitert; `asset_002_security_audit.yaml` um 5 implizite Schwachstellen (Mail Header Injection, SQL Injection, User Enumeration, Unsafe Cookies) ergänzt.

### Data Architecture & Meta-Review (v3.2.2)
- [x] **3-CSV Data Separation:** Migration der fehleranfälligen Fallbacks aus der 2-CSV Form auf exakte SSOT-Aufspaltung (`cloud_models_benchmark.csv`).
- [x] **Context Injection Pipeline:** Meta-Reviewer Logik um das Modul `cloud_open_weights` ausgebaut, um Hardware-Fehlurteile bei API-Proxies zu verhindern.

### Performance & Cache Repair (v3.2.1)
- [x] **Data-Routing Bugfix:** Behebung des kritischen Autofill-Fehlers im `UnifiedBenchmarkRunner` (kommerzielle Ergebnisse in `local_models_benchmark.csv`).
- [x] **Datenbereinigung Log-Files:** Skriptbasierte und verlustfreie Überführung von 75 fehlgeleiteten Scores (`gpt-oss`, `llama-4-scout`) ins korrekte kommerzielle Logbuch.
- [x] **Lazy Loading Implementation:** Startup-Beschleunigung durch On-Demand Import von `sentence_transformers`/`sklearn` in mathematischen Evaluationsbausteinen.
- [x] **Groq API Ping Bypass:** Anpassung des 1-Token-Ping-Modells zur Provider-Validierung auf `llama-3.1-8b-instant`, da alte Referenz durch Groq inaktiviert wurde.
- [x] **CLI Terminal Metrics:** Output-Konsolidierung am Ende einzelner Module zur dynamischen Berechnung und Visualisierung von Durchschnittsscores, Dauer, Tokens und USD-Kosten.

### Fallbacks & Provider SSOT (v3.2.0)
- [x] **Dynamic Provider SSOT:** Hardgecodete Kategorie-Definitionen in CLI und Leaderboard entfernt; zentral über `benchmark_config.yaml` (`utils/model_utils.py`) dynamisiert.
- [x] **Open-Weights Cloud API Support:** Dedizierte Cloud-Infrastruktur für Open-Weights Modelle (z. B. via Groq) eingerichtet.
- [x] **Local Cloud Removal:** Legacy-Kategorie "Local Cloud" im gesamten System (Scores, Meta-Reviews, DataFrames) sauber mit `Cloud (Open-Weights)` fusioniert.

### Audit & Meta-Review Generation (v3.1.0)
- [x] **Meta-Reviewer Anchoring:** Off-by-one Parsing Bugs behoben (via durchgängiger YAML ID-Anker).
- [x] **Anti-Halluzinations-Schutz (Grammar Restriktionen):** Meta-Review-Prompt um harten Passiv-Zwang ergänzt, um Anthropomorphisierung im Fazit zu verhindern.
- [x] **Automatisierte Metadaten-Extraktion:** Regex-basiertes Herausfiltern von API-Limits, Endlosschleifen und Safety-Protokollen (Warnings) in den Audit-Logs für kontextsensitive Evaluierung.

### Architecture Hardening & Anti-Censorship (v3.0.0)
- [x] **3-Tier Refusal Framework:** Intelligentes Abfangen von Hard- und Soft-Refusals und API-Timeouts.
- [x] **Progressive Temperature Loop:** `while True`-Retry-Block im Execution-Layer mit schrittweisen Temperaturerhöhungen (0.1, 0.4, 0.7) als Safety-Bypass.
- [x] **Pydantic Schema Serialization:** Behebung von `AttributeError`-Abstürzen durch präzises `json.loads()` Parsing aus der rohen String-Response.
- [x] **Repository Consolidation:** Major Markdown-Updates, Entschlackung der Roadmap und Framework Bump auf 3.0.0.

### Version 1.1+ Core Architecture
- [x] **Leaderboard Overhaul (v1.1)** (Absolute Scoring, Speed Profiles)
- [x] **Reasoning Module Implementation**
- [x] **System Probes & Warnungen**
- [x] **Global Cascading Token Fallback & Error Handling** ("Fast Fail")
- [x] **Golden Standard Consolidierung** (Asset YAML as SSOT)

### LLM-Based Scoring System (v1.5 Milestone Reached)
- [x] Abstract Scorer Interface und Provider Abstraction
- [x] Native Pipeline Integration & Phase 1–3 implementation
- [x] Hybrid Scoring System (Gewichtung Regex- und Judge-Scores, Fallback-Weights)
- [x] Rubric & Prompt Configuration (`benchmark_config.yaml`)
- [x] Module Rollout (Code Quality, UX Writing, Docs, Content)

### Refactoring & Stability (v2.6.2)
- [x] **God-Script Dismantling (Phase 3):** `provider_clients.py` sauber in modulare Pakete unter `utils/providers/` aufgeteilt – Facade Pattern.
- [x] **Namespace Collision Resolution:** Modulspezifische `ResultManager`-Logik extrahiert, strikte Entkopplung von globalen Systemen hergestellt.
- [x] **Magic Numbers Centralization:** Endpunkte und Limits (z. B. Ollamas Default-Port 11434) in `constants.py` zentralisiert.
- [x] **LLM Token Loop Hallucination Fallback:** API-Trimming-Logik in `llm_client.py` implementiert und in `AUDIT_AND_METAREVIEW.md` dokumentiert.
- [x] **Documentation Restructuring:** README.md rigoros an `benchmark_config.yaml`-Kategorien angeglichen, veraltete Scripts vollständig entfernt.

### Module Refactoring & Features
- [x] Political Compass Decoupling (Metrics-Logik von Scoring isoliert)
- [x] Alpha-Randomization in Multiple Choice Modules (Label-Bias vermieden)
- [x] Human Baseline Script (`run_human_compass.py`)
- [x] Code Quality Audit → v2.0.1 (Fixed Import)
- [x] UX Writing & Microcopy → v2.0
- [x] Documentation Quality → v2.0
- [x] Content Transformation → v2.0.1 (Fixed Logic)
- [x] Cultural Intelligence → v2.0

---

## In Bearbeitung

### Nächste Session
- [ ] **LLM Judge: Batch-Mode (Phase 3.5)**: Token-Verbrauch durch gebündelte Requests reduzieren.
- [ ] **Volldurchlauf aller lokalen Modelle**: Generierung eines echten finalen Leaderboards (43/43).
- [ ] **Re-run Reasoning Logic**: Verfälschte 0-Punkte für lokale Modelle bereinigen.

### Offene Features (v3.5.x+)
- [ ] **Score-Penalty für Token-Verbosity:** Separates Feature — keine Änderung an bestehenden Scores. Bewertungsabzug wenn Modell Token-Budget konsistent ausschöpft ohne Qualitätsgewinn.
- [ ] **Leaderboard-Spalten: avg_tokens, token_efficiency_ratio, est_cost_per_1k_tasks:** Implementierung in `score_calculator.py` + `generate_leaderboard.py`.
- [ ] **gpt-5.4-mini cultural_intel 108-Token-Anomalie:** `--force` Re-Run prüfen, ob echter Bug (abgeschnittene Response) oder valides Ergebnis.

### Testing Infrastructure
- [ ] Unit tests für alle Module (aktuell ca. 60%)
- [ ] Integration tests (Framework-Ebene)
- [ ] Performance Benchmarks
- [ ] CI/CD Pipeline (GitHub Actions)

---

## Backlog

### Q3 und Q4 2026

#### 1. Creative Writing Module
- Story generation
- Poetry evaluation
- Character development
- Plot coherence

#### 2. Web UI
- Interactive dashboard
- Real-time progress
- Result visualization
- Model comparison

#### 3. API Mode
- REST API for remote benchmarking
- Queue management
- Authentication

#### 4. Cost vs. Accuracy Analysis
- Meta-Analyse der Judge-Cost- und Token-Verhältnisse über Modelle hinweg
- System-Prompts tunen, um Overhead zu reduzieren (ohne Konsensqualität zu opfern)

### v2.0.0 (Cloud & Redesign)

#### 1. Multimodal Support
- Image + Text tasks
- Vision-based benchmarks
- OCR evaluation

#### 2. Advanced Feature Set
- Custom Plugin Evaluator System
- Adaptive Testing (Dynamic Difficulty)
- Scheduled Continuous Benchmarking & Alerting

---

| Task | Priority | Effort | Status |
|------|----------|--------|---------|
| **LLM Judge JSON Batching** | High | 1 week | In Progress |
| **Volldurchlauf Leaderboard** | High | 1 week | Pending |
| **Unit Tests & CI/CD** | Med | 2–3 weeks | Pending |
| **Web UI / Analytics Dash.** | Low | 4–6 weeks | Backlog |
| **Multimodal Support** | Low | 6–8 Wochen | Backlog |

---

**Last Updated:** 2026-04-11 **Version:** 3.4.4 (Architecture Compliance — No Magic Numbers/Strings) **Nächster Meilenstein:** Volldurchlauf aller lokalen Modelle / Leaderboard-Update
