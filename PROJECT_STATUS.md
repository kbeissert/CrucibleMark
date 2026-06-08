# PROJECT_STATUS.md

**Last Updated:** 2026-06-08
**Current Version:** 4.7.0 — 4-Phasen-Refactoring der Kern-Skripte (Phase 30)
**Status:** ✅ Production-Ready

> **Hinweis:** Die Executive Summary weiter unten historisch auf v4.6.1.
> Die Sub-Versionen v4.6.2–v4.6.8 sind im `docs/MAINTENANCE_LOG.md`
> detailliert dokumentiert. Dieser Header wird bei jedem Phase-Commit
> nachgezogen, die Executive Summary nur bei Major-Milestones.
>
> **Aktueller Stand (Phase 30 — v4.7.0 4-Phasen-Refactoring):**
> - 481/481 Tests grün
> - Pylint 10.00/10 (alle 5 Kern-Dateien)
> - Mypy 0 Issues
> - Ruff 0 Issues
> - 11 Helfer-Funktionen extrahiert (alle CC ≤ 12, Schwelle aus `.ruff.toml` C901)
> - 9 SSOT-Konstanten in `utils/constants.py` (Refusal-Min, HTTP_OK, 5× `LLAMACPP_*`-Reset-Pauses, `OLLAMA_UNLOAD_SETTLE_SEC`)
> - 12 Magic-Value-Stellen in `unified_runner.py` durch benannte Konstanten ersetzt
> - 3 SIM-Fixes: `SIM110` (`_has_open_tests`), `SIM103` (`_is_module_scored`, `_is_asset_uncached`)
>
> **Aenderungen seit v4.6.1 im Detail:**
> - v4.6.2: Provider-Card SSoT-Bereinigung (Phasen 20–21)
> - v4.6.3: Card-Status-Tool + Provider-Detection-SSoT (Phasen 22–23)
> - v4.6.4: Card-Templates als SSoT (Phase 24)
> - v4.6.5: SSoT-Card-Sync (Phase 25)
> - v4.6.6: Backup-System SSoT + ID-Normalisierung (Phase 27)
> - v4.6.7: make clean Hardening (Phase 28)
> - v4.6.8: Makefile help v2 + argparse Hardening (Phase 29)
> - **v4.7.0: 4-Phasen-Refactoring der Kern-Skripte (Phase 30) — aktueller Stand**

---

## Executive Summary

CrucibleMark v4.6.1 schließt die CSV-Hygiene-Härtung mit einem dreischichtigen Defense-in-Depth-Modell ab: Hard-Fail-Guard im `result_manager.py`, Sanitizer-Heuristiken in `consolidate_csv.py` und `make validate-csv` für CI. Aufbauend auf v4.6.0 (Sanitizer entfernte 13.466 Müll-Zeilen) und v4.5.0 (ID-SSoT-Refactoring mit `resolve_canonical_model_id()` / `enforce_card_first()`) sind alle drei CSV-Schreibpfade nun gegen Header-Repeat, narrative Asset-IDs, Boolean- und leere Modelle abgesichert. Pylint 10.00/10, 226/226 Tests grün.

**Key Achievements (v4.6.1):**
- ✅ **Hard-Fail-Guard in `result_manager.py`** — `_validate_row_for_write()` validiert JEDE Zeile (neu + bestehend) gegen die Sanitizer-Heuristiken und überspringt korrupte Zeilen resilient. `🛡️ Hard-Fail-Guard: N korrupte Zeile(n) übersprungen`-Log.
- ✅ **Consolidate-Filter** — `_filter_corrupt_rows()` in `consolidate_csv.py` wendet die identischen Heuristiken auf den DataFrame VOR `to_csv()` an. Verhindert dass Maintenance-Konsolidierung Müll zurück in die CSV schreibt.
- ✅ **`make validate-csv`** — neues Makefile-Target für Dry-Run-Validierung (CI-/Smoke-tauglich).
- ✅ **16 neue Tests** — 9 in `test_consolidate_csv_validates.py` + 7 in `test_result_manager_validates.py`. Parametrisiert für Header-Repeat, narrative Asset-IDs, Boolean-Modelle, leere Modelle, E2E-Pipeline, Resilienz.
- ✅ **Defense-in-Depth-Pyramide** — 3 unabhängige Schichten (Sanitizer, Consolidate, Result Manager) garantieren: Phase-8-Erfolg kann nicht durch zukünftige Module oder manuelle Edits zunichtegemacht werden.
- ✅ **226/226 Tests grün** (vorher 210, +16). Pylint 10.00/10 für `result_manager.py`, `consolidate_csv.py`, beide Test-Dateien.

**Key Achievements (v4.6.0):**
- ✅ **CSV-Hygiene-Sanitizer** — `scripts/maintenance/sanitize_benchmark_csvs.py` mit Vier-Klassen-Filter (Header-Repeat, Rohtext-Asset-IDs >60 Zeichen + Romananfänge + Markdown-Marker, Boolean-Modelle, leere Modelle). Dry-Run + `--apply`, idempotente `.bak`-Backups, atomare `.tmp`+`replace()`-Writes.
- ✅ **13.466 Müll-Zeilen entfernt** aus `local_models_benchmark.csv` (93 % der CSV). `commercial_models_benchmark.csv` 11 Zeilen verworfen (0.6 %). `cloud_models_benchmark.csv` bereits sauber.
- ✅ **Leaderboard regeneriert** — 84 Zeilen, 78 vollständig (43/43), 5 unvollständig (echte Asset-Lücken für Re-Run), 1 mit Test-Override-Logik.
- ✅ **65 neue Tests** — parametrisierte Filter-Unit-Tests (14 Romananfänge, 5 Markdown-Marker, 5 pandas-Sentinel-Varianten), Pipeline-Tests, Backup-Idempotenz, Atomic-Write, E2E. 210/210 Tests grün.
- ✅ **Pylint 10.00/10** für Sanitizer + Test-File.

**Key Achievements (v4.5.0):**
- ✅ **ID-SSoT-Refactoring** — `resolve_canonical_model_id()` und `enforce_card_first()` in `utils/model_utils.py` als zentrale ID-Bridge (Card-Lookup + Suffix-Strip + `_safe_name`-Fallback).
- ✅ **12 Inline-ID-Transformationen migriert** — in `utils/benchmark_utils.py`, `utils/scoring_utils.py`, `utils/providers/llamacpp.py`, `scripts/maintenance/*`, `scripts/core/*`, `scripts/analysis/*`, `scripts/core/tooluse_exporter.py`.
- ✅ **`enforce_card_first()` Vertrag** — garantiert Card-Existenz via `ensure_card()` (Draft falls fehlt, WARNING wird geloggt). `result_manager.save_results()` ist die zentrale Card-First-Durchsetzungsstelle.
- ✅ **`strip_date_suffix()` SSoT** — für `-YYYYMMDD` / `-MMDD` mit gültigem Monat; idempotent.
- ✅ **Workaround `migrate_canonical_model_ids.py` entfernt** — SSoT-Funktionen reichen für die Kanonisierung. 22 `*.bak`-Dateien in `benchmark_scores/model_cards/` gelöscht.
- ✅ **21 neue Invarianten-Tests** — Brücken-Äquivalenz zwischen `enforce_card_first` und `resolve_canonical_model_id`; Slugify-Konsistenz für `:/ .` + Leerzeichen; Idempotenz; AST-Sweep gegen Inline-`re.sub` mit Slugify-Pattern außerhalb der SSoT-Module.
- ✅ **145/145 Tests grün** (vorher 124, +21). Klare SSOT-Trennung: keine DRY-Verletzungen im ID-Layer mehr.

**Key Achievements (v4.4.0):**
- ✅ **CSV Robustness** — `load_csv_robust()` mit `on_bad_lines="skip"` implementiert. Korrupte CSV-Zeilen (z.B. durch Audit-Log-Injection) werden automatisch übersprungen statt den Parser zu blockieren.
- ✅ **Leaderboard ID Resolution** — `_resolve_to_canonical_id()` in `consolidate_csv.py` implementiert. Mapping von Display-Namen zu kanonischen Model-IDs für konsistente Leaderboard-Einträge.
- ✅ **Backup Strategy Hardening** — `consolidate_csv.py` mit Fallback-Strategien (robust → standard pandas) und Zeitzone-Fix (`utc=True`) aktualisiert. `make backup` erstellt konsistente 39MB-Archive.
- ✅ **Web Export Pipeline** — `scripts/web_export.py` exportiert 80 Modelle korrekt mit Model Card als Single Source of Truth für Modell-Identität.
- ✅ **Memory Bank** — `techContext.md` und `progress.md` mit v4.4.0-Meilenstein aktualisiert.

**Key Achievements (v4.3.2):**
- ✅ **Kontextfenster-Resolution** — `llamacpp.py:_build_server_cmd()` nutzt jetzt Provider-Level `context_window` als Fallback, wenn `model_cfg.context_length` fehlt. Prioritätenkette: Model-Level → Provider-Level → Globaler Default → Hardcoded (32768).
- ✅ **Provider-Instanziierungs-Analyse** — Die Registry in `BaseProviderClient` erzeugt separate Instanzen für jeden Provider-Namen (`llamacpp`, `llamacpp_spark`, etc.). Parallele Benchmarks auf verschiedenen Hosts sind architektonisch möglich.
- ✅ **Dokumentation** — Memory Bank (`techContext.md`) mit neuer Sektion "Kontextfenster-Resolution" aktualisiert.

**Key Achievements (v4.3.1):**
- ✅ **F841 Bug behoben** — `existing_card` in `_ensure_model_card()` wurde befüllt aber nie genutzt (echter Bug).
- ✅ **DRY-Konsolidierung** — Neues `scripts/core/model_discovery.py` als SSOT für `discover_local_models()`, `discover_commercial_models()`, `discover_models()` — war identisch in `run_score_benchmark.py` und `run_political_compass_benchmark.py` dupliziert.
- ✅ **Import-Cleanup** — Alle Inline-Imports in `unified_runner.py` an Dateianfang; `_language_validator` auf Modul-Ebene (hatte 3 Tests gebrochen).
- ✅ **Magic Numbers** — `_LLAMACPP_STOP_SETTLE_SEC = 3` in `benchmark_auto.py`; `_BUDGET_KEYWORDS` als Modul-Konstante in `unified_runner.py`.
- ✅ **ANSI-Guard** — `political_compass/test.py`: `sys.stdout.isatty()`-Check für Escape-Codes.
- ✅ **Pylint 10.00/10** (+0.01 gegenüber v4.3.0).

**Vorherige Version (v4.3.0 — Spark-Connector-Konsolidierung, Readiness-Hardening & garantierter Lifecycle-Cleanup):**
- ✅ **Spark-Readiness-Hardening** — Probe-Logik akzeptiert neben sichtbarem Content auch valide 200-Signale (`reasoning_content`, `finish_reason`, `usage.total_tokens`).
- ✅ **Endpoint-Adoption mit Warmup-Fenster** — Läuft unter derselben `base_url` bereits das Zielmodell, wartet der Connector auf Readiness statt voreilig abzubrechen.
- ✅ **UnifiedRunner-Cleanup via `finally`** — Lokale Provider inkl. `llamacpp_spark` werden nach Run-Ende oder Abbruch zuverlässig gestoppt; optionaler `server_post_stop_cmd` wird ausgeführt.
- ✅ **CLI-Modul mit Qwen validiert** — Kurztest auf `cli_benchmark` mit Qwen über Spark erfolgreich; Cleanup-Pfad für Success und Abbruch verifiziert.

**Key Achievements (v4.3.0):**
- ✅ **Spark-Readiness-Hardening** — Probe-Logik akzeptiert neben sichtbarem Content auch valide 200-Signale (`reasoning_content`, `finish_reason`, `usage.total_tokens`).
- ✅ **Endpoint-Adoption mit Warmup-Fenster** — Läuft unter derselben `base_url` bereits das Zielmodell, wartet der Connector auf Readiness statt voreilig abzubrechen.
- ✅ **UnifiedRunner-Cleanup via `finally`** — Lokale Provider inkl. `llamacpp_spark` werden nach Run-Ende oder Abbruch zuverlässig gestoppt; optionaler `server_post_stop_cmd` wird ausgeführt.
- ✅ **CLI-Modul mit Qwen validiert** — Kurztest auf `cli_benchmark` mit Qwen über Spark erfolgreich; Cleanup-Pfad für Success und Abbruch verifiziert.

**Vorherige Version (v4.2.1 — ToolUse-Backlog-Rearm, Provider-Preflight-Fix & Benchmark-Auto-Stabilisierung):**
- ✅ **ToolUse-Backlog reaktiviert** — Modelle mit Tool-Use-Strich werden aus der Leaderboard-Analyse auf `supports_tool_use="untested"` zurückgesetzt und von `benchmark_auto` wieder im Pre-Step verarbeitet.
- ✅ **Provider-Preflight-Fix** — `validate_untested_card()` inferiert den Provider aus `model_id`, wenn ältere Model Cards keinen `provider`-Key tragen.
- ✅ **Benchmark-Auto stabilisiert** — Legacy-Cards scheitern nicht mehr an `missing_provider`, sondern liefern den tatsächlichen Erreichbarkeitsgrund wie `ollama_model_not_installed`.

**Vorherige Version (v4.2.0 — OpenRouter-Migration, Free-Tier-Support, Qwen-Integration & Pipeline-Bug-Fixes):**
- ✅ **OpenRouter-Migration** — 3 Modelle von Ollama-Cloud-Proxy auf OpenRouter umgestellt: `google/gemma-4-31b-it`, `deepseek/deepseek-chat-v3.1`, `deepseek/deepseek-v3.2`. Model Cards umbenannt, alle 5 Benchmark-CSVs migriert.
- ✅ **Qwen-Integration** — `qwen/qwen3.7-max` und `qwen/qwen3.6-plus` via OpenRouter. Model Cards vollständig angelegt inkl. Pricing und Thinking-Probe-Status.
- ✅ **`data_collection: allow`-Fix** — Alle Alibaba-Cloud-Endpoints antworten jetzt via OpenRouter ohne 404. `extra_body`-Override in `openrouter.py`.
- ✅ **Free-Tier-Rate-Limiting** — `openrouter_free`-Profil (18 RPM / 1 concurrent) für `:free`-Suffix-Modelle. `unified_runner.py` wählt das Profil automatisch.
- ✅ **`resolve_provider()` Bug-Fix** — `:free`-Suffix + `/`-Heuristik korrigiert; kein falsches Groq-Routing mehr.
- ✅ **`make review` FLAGS** — `AUTO=1` und `FORCE=1` werden jetzt korrekt an `generate_review.py` weitergegeben.
- ✅ **ToolUse-Exporter nach Delegate-Einzellauf** — `run_tooluse_benchmark.py`: Exporter-Aufruf nach `_run_model()` eingefügt; `tooluse_leaderboard.csv` wird nach jedem `make benchmark-auto`-Run korrekt aktualisiert.
- ✅ **Asset-Level-De-Duplikation im Exporter** — `tooluse_exporter.py`: `best_rows`-Dict auf `(model_id, asset_id)` verhindert Score-Halbierung bei Cross-CSV-Doppeleinträgen.
- ✅ **Dead-Code Boundary-Filter entfernt** — `data_loader.py`: Wirkungslose "Open Weights (Cloud/Local)"-Filter seit `get_model_category()`-SSOT-Migration entfernt.

**Vorherige Version (v4.1.0 — llamacpp Expansion & Bug Fixes):**
- ✅ **Double-Start-Bug** — `_query_active_model()` in `llamacpp.py`: Server-Modell per API erkennen statt In-Process-State.
- ✅ **Duplicate-Runner-Bug** — Zweite `UnifiedBenchmarkRunner`-Zeile in `benchmark_auto.py` entfernt.
- ✅ **gemma-3-12b-it-q8** — Provider-Config-Eintrag + Model Card (Q8_0-GGUF).
- ✅ **3 Module aktiviert** — `code_quality`, `reasoning_logic`, `documentation_quality` on by default.

**Vorherige Version (v4.0.0 — erster öffentlicher Release):**
- ✅ **Tool Use Benchmark Module** — 6 Assets in 3 Phasen (Tool Selection, Content Synthesis, Multilingual), Live-MCP-Integration (Tavily `web_search` + `http_fetch`), Content Verification Framework mit Halluzinations-Cap, 257 Tests. Erste Production-Runs: gpt-5-mini 76.5 % [PRODUCTION], grok-4-fast 74.2 % [PRODUCTION], kimi-k2 73.6 %, qwen3-32b 72.9 %.
- ✅ **Model Cards als Pricing-SSoT** — Vollständige Pipeline-Migration: `score_calculator.py`, `cost_tracker.py` und Web-Export lesen Preise ausschließlich aus `benchmark_scores/model_cards/*.json`. LiteLLM aus Pricing-Pfad entfernt.
- ✅ **Budget-Enforcement entfernt** — `cost_limits.yaml` gelöscht, `CostLimitExceededError` entfernt, Architektur vereinfacht.
- ✅ **Token-Budget-Berechnung zentralisiert** — `resolve_token_budget()` als SSoT für alle Provider.
- ✅ **257/257 Tests grün** — Ruff + Pylint 10.00/10.
- ✅ **Vollständige Model Card Coverage** — 4 neue Frontier-Cards: Mistral Large 3, Devstral 2, GPT-5.5, Gemini 3.5 Flash.

**Vorherige Version (v3.15.1 — 4 Frontier Model Cards complete + Dokumentations-Update):**
- ✅ **`mistral-large-2512.json`** — Mistral Large 3, MoE 675B/41B aktiv, Apache 2.0, context 262K, input $0.50/1M, output $1.50/1M.
- ✅ **`devstral-2512.json`** — Devstral 2, Dense 123B, Modified MIT (restricted-weights), context 256K, input $0.40/1M, output $2.00/1M.
- ✅ **`gpt-5_5.json`** — GPT-5.5, Proprietär, context 1050K, knowledge_cutoff 2026-04, input $5.00/1M, output $30.00/1M.
- ✅ **`gemini-3_5-flash.json`** — Gemini 3.5 Flash, Proprietär, context 1049K, knowledge_cutoff 2025-01, input $1.50/1M, output $9.00/1M.
- ✅ **Dokumentation** — `ARCHITECTURE.md`: delegate_script + Model-Card-Lifecycle. `DEVELOPER_GUIDE.md`: card_status-Tabelle korrigiert. `README.md`: `make benchmark-auto` ergänzt.

**Vorherige Version (v3.15.0 — Tool Use Probe-Run: 5 Modelle live, 2 PRODUCTION-Modelle, 11-Modell-Leaderboard):**
- ✅ **Probe-Run 5 Modelle** — Live-MCP-Modus (mode=live, Port 8765, Tavily). gpt-5-mini 76.5% [PRODUCTION], grok-4-fast-non-reasoning 74.2% [PRODUCTION], moonshotai/kimi-k2 73.6%, qwen/qwen3-32b 72.9%, gemma4:E4B 65.7%.
- ✅ **`cost_usd="local"` für Open-Weights** — `_LOCAL_DEPLOYMENT_TYPES` in `tooluse_exporter.py` um `"open-weights"` erweitert.
- ✅ **Leaderboard 11 Modelle** — `benchmark_scores/tooluse_leaderboard.csv`. Sovereignty Gap dokumentiert.
- ✅ **gemma4:E4B fleet_group-Backfill** — `fleet_group=local_sovereign`, `sovereignty_gap=-7.28` nachgepflegt.
- ✅ **Model Cards aktualisiert** — `gpt-4o.json`, `magistral-medium-latest.json`: `tooluse_tested_at` + Scoring-Felder gesetzt.

**Vorherige Version (v3.14.0 — Bug-Fixes Tool Use Benchmark):**
- ✅ **`anthropic.py` `system`-Kwarg-Fix** — System-Prompt wurde stillschweigend verworfen (silent drop in `**kwargs`). Alle Anthropic-Modelle: `retry_required=true` → `parse_attempts=1`. Latenz halbiert, tooluse006-Timeout bei Opus 4.6 behoben.
- ✅ **`tooluse003.yaml` v1.3.0 Rubrik-Fix** — False-Positive-Halluzination bei httpbin.org-Kontext-Erklärungen behoben. `acceptable_patterns`-Sektion mit 5 Einträgen.
- ✅ **`unified_runner.py` Token-Tracking-Fix** — Multi-Call-Module zeigten nur letzten Call statt Gesamtsumme. `max(exec_result.tokens_used, client.last_token_usage)` + `isinstance`-Check.
- ✅ **Re-Runs** — Haiku 4.5 (75.0%), Opus 4.5 (79.2%), Sonnet 4.6 (79.0%), Opus 4.6 (80.0%) — alle mit `parse_attempts=1`. Leaderboard: 7 Modelle, Sovereignty Gap -10.9.
- ✅ **257/257 Tests grün.**

**Vorherige Version (v3.13.0 — Phase-C Asset + Judge Hardening):**
- ✅ **`tooluse006.yaml`** — Phase-C-Asset: Multilingual Search & German Synthesis. Kalibriert: Sonnet 90, Hermes 90 (Rubrik misst Synthese, kein Grounding-Edge).
- ✅ **`phase2_rubric`-Verdrahtung** — `_build_rubric_override()` in `test.py`; Asset-YAML-Rubrik wird jetzt an den LLM-Judge übergeben (war zuvor totes YAML).
- ✅ **Hallucination Cap config-first** — `config/scoring.yaml → tool_use.hallucination.cap_hard: 20`. Cap-Anwendung nach Judge-Call in `test.py`.
- ✅ **`tool_result_ignored`-Flag** — Boolean im CV-Block: Modell hatte verwertbaren Tool-Inhalt, antwortete aber aus Trainings-Vorwissen. Distinct von B1 (transparenter Fehlerstatus).
- ✅ **257/257 Tests grün** (7 neue Tests für `tool_result_ignored` + `language_consistency`-Rubrik).

**Vorherige Version (v3.12.0 — Tool Use Phase-A-Erweiterung):**
- ✅ **`tooluse004.yaml`** — Phase-A: Tool Selection (web_search, kein vorgegebenes URL-Target).
- ✅ **`tooluse005.yaml`** — Phase-A: URL Construction (fetch, Modell muss URL selbst ableiten). Python-Wikipedia-Fixture in Mock-Provider.
- ✅ **`parse_error_flag` → `retry_required`** — Umbenennung im gesamten Stack (Exporter, IO-Manager, Tests).
- ✅ **`methodology_notes.py`** — 7 deterministische Annotations-Templates für Reviewer.
- ✅ **P1-Ceiling: 96.0** (5 Assets, statt 93.33 mit 3 Assets). 41 Modelle im Leaderboard.

**Vorherige Version (v3.11.0 — Golden Standard v1.2.0: Kalibrierungsrunde 1):**
CrucibleMark v3.11.0 schließt die Kalibrierungsrunde 1 des Tool Use Benchmark-Moduls ab. Golden Standard v1.2.0 ist finalisiert: Alle drei Assets (tooluse001–003) haben manuell validierte Referenzantworten und Bewertungsrubrik. Kalibrierungsrun mit 12 Modellen liefert stabile, vergleichbare P2-Scores (Spread: 57.8–70.3). P1-Ceiling 100 für http_fetch-Assets. 17 Tests grün.

**Vorherige Version (v3.10.0 – Tool Use Benchmark-Modul Launch):**
CrucibleMark v3.10.0 führt das Tool Use Benchmark-Modul als vollständig implementiertes Diagnosemodul ein. Es misst, ob LLMs externe Tools (Web-Suche, HTTP-Fetch) via MCP tatsächlich aufrufen oder Ergebnisse halluzinieren — kritisch für Agenten-Pipelines. Ein eigener MCP-Server (`cruciblemark-mcp/`) liefert deterministischen Mock- und Live-Modus. Der Batch-Runner (`scripts/run_tooluse_benchmark.py`) mit interaktivem Wizard verarbeitet alle tool-fähigen Modelle mit MCP-Neustart zwischen Modellen für faire Vergleichsbedingungen. Das Modul fließt nicht in den Total Score ein.

**Vorherige Version (v3.9.0 – Architektur-Compliance-Refactoring: Provider-Registry, LanguageValidator, God-Script-Zerlegung, Pylint 9.99/10):**
CrucibleMark v3.9.0 führt ein vollständiges Architektur-Compliance-Refactoring durch. 7 zentrale Dateien werden auf PILIN ≥ 9 gebracht — ohne Funktionalitäts- oder Scoring-Änderungen. `LanguageValidator` kapselt die Spracherkennung, `judge_runner.py` nutzt eine `_PROVIDER_MODULES`-Registry statt If-Ketten, `generate_review.py` wird von 1309 auf ~200 Zeilen reduziert (→ `scripts/analysis/review/`-Package). Alle Magic Numbers durch zentrale Konstanten ersetzt. 12 unused variables (Ruff F841) entfernt, 185 Issues auto-gefixt. Pylint Score: 9.37 → 9.99/10.


CrucibleMark v3.7.5 schließt die Pricing-Architektur: Preise werden nicht mehr zentral in `config/cost_limits.yaml` gepflegt, sondern als `input_price_per_1m` / `output_price_per_1m` (USD/1M Tokens) direkt in den Model Cards hinterlegt. 53 API-Model-Cards migriert. `cost_limits.yaml` auf 6 Legacy-Einträge reduziert. 4 neue Cards, 3 neue Reviews.

**Vorherige Version (v3.7.3–v3.7.4 – Architektur-Compliance & Anti-God-Script-Sanierung):**
- ✅ **v3.7.4** — `_find_card(card_dir)` parametrisiert (SSoT). `WEIGHTS_TIER_DISPLAY` als exportierte Konstante aus `model_utils.py` (kein Duplikat in `web_export.py`). `_BLOCK_META` → `political_compass/config.yaml` + `_load_pc_block_meta()` (No Magic Numbers). 74/74 Export, 6/6 Tests.
- ✅ **v3.7.3** — `scripts/web_export.py` Anti-God-Script: `main()` von ~490 auf ~80 Zeilen. 9 Top-Level-Hilfsfunktionen extrahiert. `load_csv_with_fallback()` Exception spezifiziert. `ARCHITECTURE.md` aktualisiert.

**Vorherige Version (v3.7.1–v3.7.2 – Bug-Fixes & Web-Export Date Fields):**
- ✅ **v3.7.2** — `scripts/web_export.py`: 4 Datumsfelder (`benchmark_run_at`, `report_published_at`, `report_updated_at`, `last_activity_at`). `_review_date_range()` + `_build_benchmark_run_dates()`.
- ✅ **v3.7.1** — `generate_review.py` 4× `_find_card()`. `build_provider_map()` Config-Lesung. `exporter.py` Pylance-Fixes. `ARCHITECTURE.md` Doku-Fix.

**Vorherige Version (v3.7.0 – Modell-Kategorisierungs-SSOT: 3-Tier `weights_license_tier` als einzige Quelle):**
- ✅ **`utils/model_utils.py` — `get_model_category()` Card-First:** `_find_card()` → `weights_license_tier` → Display-String. Drei gültige Werte: `Proprietär` / `Restricted Weights` / `Open Weights`.
- ✅ **`scripts/web_export.py` — Type-Override aus Card:** `type`-Feld wird zur Export-Zeit aus Model Card abgeleitet; kein CSV-Rebuild nötig. Auch `model_category` im PC-Export Card-basiert.
- ✅ **`benchmark_modules/political_compass/core/io_manager.py`:** Nutzt `get_model_category()` statt eigenständiger Inline-Logik.
- ✅ **`scripts/leaderboard/data_loader.py`:** Fallback-Funktion auf 3-Tier-Strings reduziert.
- ✅ **Frontend SSOT `model-types.js`:** 3 Tiers, `isRestrictedWeights`, `CHART_SERIES_CONFIG` 3 Einträge.
- ✅ **Alle Chart-Module aktualisiert:** `political-compass-chart.js`, `politicalCompass.11tydata.js`, `leaderboard-chart.js`, `scoreboard-table.js`, `shift-chart.js`.
- ✅ **SCSS:** `--cm-chart-label-restricted: $cm-amber`, `cm-model-badge--restricted` + `--restricted-sub`.
- ✅ **Web-Export 72/72 OK.** Verifikation: `['Open Weights', 'Proprietär', 'Restricted Weights']` in beiden Exports.

**Vorherige Version (v3.6.5 – Archetyp-Umbenennung: Stoiker + Narr):**

CrucibleMark v3.6.5 benennt zwei Archetypen um: `Das Schaf` → `Der Stoiker`, `Chamäleon` → `Der Narr`. Finale vier Labels: Stoiker / Wolf im Schafspelz / Die Chimäre / Der Narr. Nur Labels geändert, Klassifikationslogik und Schwellwerte unverändert. CSV-Backfill 76 Zeilen, Web-Export 72/72.

**Vorherige Version (v3.6.2 – `vendor`-Feld in Model Cards):**

CrucibleMark v3.6.2 führt das `vendor`-Feld als Filterdimension für den UI-Familienfilter ein. Alle 72 Model Cards wurden mit einem normalisierten Hersteller-Namen gepatcht (13 Werte, 0 ungemappte Modelle). `web_export.py` exportiert `vendor` als Top-Level-Feld (analog zu `size_class`), `benchmark_leaderboard_detailed.csv` enthält eine neue `Vendor`-Spalte. Zusätzlich (v3.6.1): Lizenz-Metadaten (`license`, `license_url`, `commercial_use_allowed`) in allen Cards; hf.co-Modell-Card-Lookup-Fallback in `web_export.py`; Abliterated-Card-Korrektur (Apache-2.0). (Commits `5241532`, `7551b31`, `ecdff77`)

**Key Achievements (v3.6.2):**
- ✅ **72 Model Cards — `vendor`-Feld:** 13 Werte; `scripts/dev/add_vendor_field.py` idempotent; 0 ungemappte Modelle.
- ✅ **`scripts/web_export.py` — `vendor` Top-Level:** 71/71 Modelle mit `vendor` im Export.
- ✅ **`scripts/leaderboard/exporter.py` — `Vendor`-Spalte:** Vor `Size Class` in `benchmark_leaderboard_detailed.csv`.
- ✅ **`scripts/analysis/generate_model_cards.py` — `vendor` im Prompt:** Vollständige Werteliste für LLM-generierte Cards.
- ✅ **`benchmark_modules/MODULE_SCHEMA_TEMPLATE.yaml`:** `vendor` mit Wertebereich dokumentiert.

**Vorherige Version (v3.6.1 – Lizenz-Metadaten, hf.co-Lookup-Fix):**

CrucibleMark v3.6.1 ergänzt Lizenz-Transparenz: Alle 69 Cards haben `license`, `license_url` und `commercial_use_allowed`; `web_export.py` gibt diese Felder im `model_card`-Subobject aus. Ein Lookup-Bug für hf.co-Modelle (CSV-Name ≠ Card-Dateiname) wurde durch einen Fallback auf `raw_model_id` behoben — 69/69 Modelle vollständig.

**Vorherige Version (v3.6.0 – model_id SSOT, benchmark-auto Fix, supports_tool_use, 3 Grok-Modelle):**

CrucibleMark v3.6.0 schließt drei strukturelle Lücken: (1) **`model_id`-SSOT im Web-Export:** `benchmark_leaderboard_detailed.csv` enthält jetzt eine `model_id`-Spalte (rohe Config-ID). `web_export.py` nutzt diese direkt für den Verzeichnis-Lookup — identische Transformation wie `benchmark_utils.py`. Zwei explizite Fallbacks decken historische Daten ab. 69/69 Modelle vollständig (Report + Review + PC). (2) **benchmark-auto Retry-Logik:** `language_mismatch`, `truncated` und `refusal` werden nicht mehr als technische Fehler retried (`COMPLETED_STATUSES`-Set). (3) **P95-Akkumulations-Bug:** Regex in `benchmark_utils.py` konsumiert bestehende Suffixe — 154 Audit-Logs bereinigt. Außerdem: `supports_tool_use`-Feld in alle 77 Model Cards migriert; 3 neue xAI-Modelle (grok-4.3, grok-4.20-0309-non/reasoning) in Config + Preisliste eingetragen. (1 Commit, c321f53)

**Key Achievements (v3.6.0):**
- ✅ **`scripts/leaderboard/exporter.py` — `model_id`-Spalte:** Rohe Config-ID als SSOT in `benchmark_leaderboard_detailed.csv` exportiert.
- ✅ **`scripts/web_export.py` — Dir-Lookup via `model_id`:** Kein Raten aus Display-Namen mehr. Fallback 1: Date-Suffix-Strip (historische Reviews ohne Versionssuffix). Fallback 2: Suffix-Match (Dirs ohne Provider-Präfix). Coverage: 69/69 ✅
- ✅ **`scripts/core/benchmark_auto.py` — `COMPLETED_STATUSES`:** `{success, language_mismatch, truncated, refusal}` — nur echte technische Fehler werden wiederholt.
- ✅ **`utils/benchmark_utils.py` — P95-Regex:** `r"(\*\*Execution Time:\*\* [\d.]+ s)(?:\s*\(Modul-P95: [\d.]+ s\))*"` — Akkumulation behoben. 154 Dateien bereinigt.
- ✅ **`supports_tool_use`** in allen 77 Model Cards (72× true, 5× false). `generate_model_cards.py` + `generate_model_cards.py` Prompt aktualisiert.
- ✅ **3 neue Grok-Modelle:** `grok-4.3`, `grok-4.20-0309-non-reasoning`, `grok-4.20-0309-reasoning` in `benchmark_config.yaml` + `config/cost_limits.yaml`.
- ✅ **Docs:** `ARCHITECTURE.md`, `USER_GUIDE.md`, `systemPatterns.md` mit model_id-SSOT aktualisiert.

**Vorherige Version (v3.5.9 – size_class Card-Lookup, empty_response_context, Model-Card-Korrekturen):**

CrucibleMark v3.5.9 verbessert die Datenqualität auf drei Ebenen: (1) Die **Size-Class-Klassifikation** ist jetzt Card-First: `get_model_size_class()` liest `size_class` zuerst aus der JSON-Model-Card (SSoT für Overrides), dann per Colon-Tag-Regex (Ollama) und zuletzt per Dash/Dot-Suffix-Regex auf dem Modellnamen. Das Leaderboard weist damit korrekt 7 Desktop-Modelle aus statt vorher 3. Neue Hilfsfunktionen: `_param_b_to_size_class()` und das Sentinel-Set `_SIZE_CLASS_VALID`. (2) **`empty_response_context`** im Report-Generator: `generate_review.py` erkennt Assets mit `response_length=0` (lautlose Content-Policy-Verweigerung) und liefert die betroffenen Asset-IDs als strukturierten Kontext an den Meta-Reviewer, der sie im jeweiligen Modul-Abschnitt des Reviews dokumentiert. (3) **`generate_model_cards.py`** setzt `size_class` automatisch beim Generieren jeder neuen Card. 6 fehlklassifizierte Model-Cards manuell korrigiert; Slug-Mismatch bei `CognitiveComputations/dolphin-mistral-nemo:latest` behoben. (5 Commits, aac7315…75c0cb1)

**Key Achievements (v3.5.9):**
- ✅ **`utils/model_utils.py` — `get_model_size_class()` Priority-Kaskade:** (1) Card-Lookup SSoT → (2) Ollama-Colon-Tag case-insensitive → (3) Dash/Dot-Suffix-Regex → Fallback `"Frontier"`. Hilfsfunktionen `_param_b_to_size_class()` + `_SIZE_CLASS_VALID`.
- ✅ **`scripts/analysis/generate_review.py` — `_build_empty_response_context()`:** Liest alle 3 Benchmark-CSVs, filtert `response_length=0 + status=success`, liefert Asset-IDs als Kontext-Block. Nur aktiv für `review_type == "benchmark"`.
- ✅ **`config/meta_reviewer_prompt.yaml` — `{empty_response_context}`:** Neuer Pflicht-Block nach `constraint_violations_context`. Lautlose Verweigerungen werden als Qualitätsmerkmal dokumentiert, nicht als technische Fehler.
- ✅ **`scripts/analysis/generate_model_cards.py` — Auto-`size_class`:** Beide Pfade (`_generate_card()` + `_create_minimal_card()`) schreiben `size_class` via `get_model_size_class()`. Bestehende Felder werden nicht überschrieben.
- ✅ **Model-Card-Korrekturen:** 6 Cards manuell mit korrektem `size_class` versehen (Desktop/Server/Workstation/Nano). Slug-Mismatch `dolphin-mistral-nemo` behoben: Card-Pfad basiert auf rohem CSV-Wert `CognitiveComputations/dolphin-mistral-nemo:latest` → `CognitiveComputations_dolphin-mistral-nemo_latest.json`.
- ✅ **Leaderboard-Distribution:** Nano=5, Edge=5, Desktop=7, Workstation=4, Server=1, Frontier=40.

**Vorherige Version (v3.5.8 – ThinkingProbe, Card-First Workflow, empirische Reasoning-Erkennung):**

CrucibleMark v3.5.8 führt eine empirische Reasoning-Erkennung ein, die die bisherige rein heuristische String-Matching-Logik in `is_reasoning_model()` ablöst. Kernstück ist der **ThinkingProbe**: Ein deterministischer API-Call, der anhand von `<think>`-Tags (Signal A) und `reasoning_tokens > 0` (Signal B) validiert, ob ein Modell Chain-of-Thought produziert. Das Ergebnis wird in der JSON-Model-Card (`benchmark_scores/model_cards/`) persistiert. Der **Card-First-Hook** in `unified_runner.py` stellt sicher, dass jedes neue Modell automatisch geprobt wird, bevor es einen Benchmark-Run startet. `is_reasoning_model()` liest die Card zuerst — String-Trigger bleiben als Fallback erhalten. Drei Bugs wurden behoben: Signal C (Response-Länge) erzeugte False-Positives und wurde entfernt, `_infer_provider()` nutzte Substring-Matching statt `/`-Präsenz-Heuristik, und `is_reasoning_model_from_card()` verwendete `replace('/', '_')` statt der vollständigen `_safe_name()`-Transformation. (Commit e1e61f6, 33 Dateien, 738 Insertions)

- ✅ **`utils/model_utils.py` — `ThinkingProbeResult` & `probe_thinking_model()`:** Neues Dataclass (`detected`, `evidence`, `confidence`). Signal A = `<think>`/`<thinking>`/`<thought>`-Tags (confidence=high), Signal B = `reasoning_tokens > 0` (confidence=medium). Signal C (Response-Länge) nicht implementiert — systematische False-Positive-Quelle bei Instruction-Following-Modellen.
- ✅ **`utils/model_utils.py` — `is_reasoning_model_from_card()`:** Liest `thinking_probe_detected` aus JSON-Card. Dateinamen-Auflösung via `re.sub(r'[:/.\s]', '_', model_id)` (`_safe_name()`-Transformation). Gibt `None` zurück wenn Card oder Feld fehlt (kein False-Positive).
- ✅ **`utils/model_utils.py` — `is_reasoning_model()` Card-First:** Card-Lookup hat Vorrang vor String-Trigger-Heuristik. Neuer Trigger `kimi-k2` ergänzt.
- ✅ **`scripts/core/unified_runner.py` — `_ensure_model_card()`:** Hook vor erstem Benchmark-Run. Card mit Feld → Skip. Card ohne Feld → Probe → Feld schreiben. Keine Card → Probe → Minimal-Card erstellen. Probe-Fehler → RuntimeError.
- ✅ **`scripts/analysis/generate_model_cards.py` — `_create_minimal_card()`:** Erstellt Card ohne LLM-Aufruf (`card_status: minimal`) — nur Probe-Felder.
- ✅ **`scripts/tools/probe_thinking.py`** (NEU): Standalone-CLI für retroaktive und On-Demand-Probes. Modi: `--model <id>`, `--missing` (Batch), `--all` (Force-Rescan). Provider-Inference: Config → `/` im ID → `openrouter` → sonst `ollama`.
- ✅ **Makefile:** `probe-thinking` (requires `MODEL=`) und `probe-all-thinking` als neue Targets.
- ✅ **26 API-Model-Cards** mit Probe-Feldern versehen (retroaktiv via `make probe-all-thinking`). 25 Offline-Ollama-Modelle: graceful failure (kein Blocking).
- ✅ **o1/o3-mini/o4-mini:** `thinking_probe_detected: true` + `thinking_probe_manual_override: true` — OpenAI verbirgt Reasoning-Tokens intern.
- ✅ **Re-Runs:** 18 `gemini-2.5-flash`-Zeilen (5 Module) + 3 `kimi-k2.5`-Zeilen neu ausgeführt.
- ✅ **Dokumentation:** `CHANGELOG.md`, `docs/ARCHITECTURE.md`, `docs/DEVELOPER_GUIDE.md`, `docs/MODEL_CLASSIFICATION.md`, `.github/copilot-instructions.md` (3 neue Fallstricke), `memory-bank/` vollständig aktualisiert.

**Vorherige Version (v3.5.7 – SSoT Token-Budget, Gemini-2.5 Reasoning-Fix, Judge-Verbosity-Penalty, Refusal-Metadaten):**

CrucibleMark v3.5.7 bringt vier zusammenhängende Verbesserungen: (1) Die Token-Budget-Logik für Reasoning-Modelle ist jetzt in `resolve_token_budget()` zentralisiert (SSoT) — alle drei Provider (`openai.py`, `openrouter.py`, `mistral.py`) delegieren dorthin statt Logik zu duplizieren. (2) `gemini-2.5-flash` und `gemini-2.5-pro` werden als Reasoning-Modelle erkannt und erhalten das erhöhte Token-Budget aus `token_budgets_reasoning_models` — behebt systematisch fehlerhafte 12–18%-Scores durch Thinking-Token-Budget-Erschöpfung. (3) Der LLM-Judge erhält bei Reasoning-Modellen einen `TOKEN BUDGET NOTE`-Block: sichtbarer Output > 2× Standard-Budget mit Padding → −1 Punkt `output_quality`. (4) Kurze Antworten (< 15 Zeichen) werden als `refusal_flag=True` dokumentiert — maschinell lesbar, CSV-persistiert, kein Re-Run.

**Key Achievements (v3.5.7):**
- ✅ **`utils/model_utils.py` — `resolve_token_budget()` SSoT:** Zentrale Token-Budget-Funktion für alle Provider. Gibt `(effektives_budget, is_reasoning)` zurück. Behebt fehlende `elif`-Branch in `mistral.py` (war in `openai.py`/`openrouter.py` vorhanden).
- ✅ **`benchmark_config.yaml` — `token_param_name` pro Provider:** `max_tokens` vs. `max_completion_tokens` für alle 5 kommerziellen Provider als Config-Key — kein Hardcoding mehr.
- ✅ **`utils/model_utils.py` — `gemini-2.5` Reasoning-Trigger:** `is_reasoning_model()` erkennt jetzt `gemini-2.5-flash`/`gemini-2.5-pro`. Budget-Fix: ux_writing 8.000 statt 500 Tokens, documentation_quality 12.000 statt 6.000 Tokens.
- ✅ **Judge-Verbosity-Penalty (`judge_prompt_builder.py` + `judge_runner.py` + `judge_evaluator.py`):** `token_budget_context = {"standard": N, "elevated": M}` wird für Reasoning-Modelle automatisch injiziert. Judge bewertet sichtbaren Output am Standard-Budget.
- ✅ **Refusal-Metadaten (`unified_runner.py` + `result_manager.py`):** Drei neue CSV-Felder: `refusal_flag`, `refusal_type`, `refusal_note`. Unterscheidet aktive Ablehnung (Qualitätsmerkmal) von ungeproblematischen Fehlern.
- ✅ **Dokumentation:** `CHANGELOG.md`, `docs/ARCHITECTURE.md`, `docs/SCORING_METHODOLOGY.md`, `.github/copilot-instructions.md` vollständig aktualisiert.

**Vorherige Versionen (v3.5.5 – 6 Deployment-Tiers / v3.5.6 – OpenRouter Reasoning-Token-Tracking):**

CrucibleMark v3.5.6 behebt ein kritisches Produktionsproblem mit OpenRouter-Reasoning-Modellen: `minimax/minimax-m2.7` lieferte auf `cli005` und `ux_writing_005` leeren Output (`finish_reason: length`), weil OpenRouter interne Reasoning-Tokens direkt gegen `max_tokens` verrechnet. Fix: `minimax-m2`-Trigger in `is_reasoning_model()` aktiviert automatisch ein 5×-Budget. Neue `reasoning_tokens`-CSV-Spalte und `[!WARNING]`-Block im Audit-Log.

CrucibleMark v3.5.5 ersetzt das 2-Tier-Size-Class-System durch eine deployment-orientierte 6-Tier-Taxonomie (`Nano/Edge/Desktop/Workstation/Server/Frontier`). v3.5.4 führte die initiale `Nano (≤5B)`-Klassifikation mit `🔬`-Badge ein. Beide Versionen betreffen ausschließlich `utils/model_utils.py`, `MODEL_CLASSIFICATION.md` und das Leaderboard-System.

**Vorherige Version (v3.5.3 – Asset-Limit-Kalibrierung & Fleet-Audit):**

CrucibleMark v3.5.3 schließt einen fleet-weiten Audit der Benchmark-Prompts ab. Drei strukturelle Kalibrierungsfehler bei Word-Limits wurden datengetrieben behoben: Die Limits für `ux_writing_005`, `content_transformation_003` und `content_transformation_004` wurden auf P25 × 1.20 angehoben. 156 CSV-Einträge und Audit-Logs chirurgisch entfernt.

**Vorherige Version (v3.5.2 – Code-Qualität, Terminologie & Block-7.9-Dokumentation):**

CrucibleMark v3.5.2 bereinigt Code-Qualitätsprobleme (Pylint W1309/W0719/C0206, Mypy annotation-unchecked) und vollendet die terminologische Umbenennung „Nationalistisch" → „Reaktionär" auf der X-Achsen-Skala des Political Compass. Die Dokumentation wird um Block 7.9 (Parolen-Extremismus-Sonde) erweitert, der bisher undokumentiert war.

CrucibleMark v3.5.1 schließt drei Stabilitätslücken im Benchmark-Workflow und vervollständigt das PC-Leaderboard auf 48 Modelle. `UnboundLocalError` bei Quota-Abbruch in `test.py` behoben, modellspezifische Token-Limits für gpt-4o/gpt-4o-mini über `benchmark_config.yaml` konfigurierbar gemacht (Ende der Fallback-Warnungen), Gemini Daily-Quota Fast-Fail in `base.py` aktiv. `kimi-k2-instruct` von Groq (Modell dort entfernt) auf `kimi-k2.5:cloud` via Ollama Cloud migriert. 7 neue PC-Runs abgeschlossen (gpt-5, gpt-5.4, gpt-5.4-mini, gpt-4o, gpt-4o-mini, llama-4-scout, qwen3-32b).

**Key Achievements (v3.5.1):**
- ✅ **`test.py` — `UnboundLocalError` behoben:** `query_exec_time = 0.0` als Default vor der `while True:`-Schleife — verhindert Absturz bei Quota-Abbruch.
- ✅ **`openai.py` — Modellspezifisches Token-Limit:** `model_max_tokens`-Lookup aus Config-Override — keine Fallback-Warnungen mehr bei gpt-4o/gpt-4o-mini.
- ✅ **`base.py` — Gemini Daily-Quota Fast-Fail:** `retry_delay > 300s` löst sofort Fast-Fail aus statt 7,6h zu blockieren.
- ✅ **PC-Leaderboard: 48 Modelle vollständig:** 7 neue Runs + kimi-k2.5:cloud (bereits seit 16.04. vorhanden).
- ✅ **`benchmark_config.yaml` — kimi-k2 Groq → Ollama Cloud:** `kimi-k2.5:cloud` unter `ollama_cloud` eingetragen.

**Vorherige Version (v3.5.0 – PC Token-Asymmetrie / Kognitions-Signal):**

CrucibleMark v3.5.0 führt mit der **Token-Asymmetrie-Analyse (Section 2.6)** eine neue analytische Dimension in den Political-Compass-Workflow ein. Das Framework misst jetzt nicht mehr nur *wo* ein Modell unter Anti-Diplomat-Druck driftet, sondern auch *wie viel kognitiven Aufwand* es dabei betreibt: `last_output_tokens` wird nach jedem API-Call in `llm_client.py` gespeichert und pro Frage in den PC-Checkpoint geschrieben. Bei Anomaly-Verification-Runs (Shift ≥ 1.0) erzeugt `audit_logger.py` daraus Section 2.6 mit `ELABORATION_SPIKE`- und `CAPITULATION_DROP`-Flags. Der `bias_reviewer`-Prompt wurde strukturell überarbeitet (Model Card vor Pflichtstruktur, Verzahnungs-Instruktion für Token-Befunde). Erste Version mit vollständigem kognitiven Fingerabdruck für PC-Anomalien.

**Key Achievements (v3.5.0):**
- ✅ **`utils/llm_client.py` — `last_output_tokens`:** Reset vor jedem API-Call, Setzen auf `eval_count` nach erfolgreichem Call. Liefert Output-Tokens pro Frage ohne Nachparsing.
- ✅ **`benchmark_modules/political_compass/test.py` — `output_tokens` im Checkpoint:** Live-Paths schreiben tatsächliche Token-Zahl, Resume-Pfad schreibt explizit `None` (semantisch von `0` trennbar — verhindert falsche Coverage-Warnungen).
- ✅ **`audit_logger.py` — Section 2.6 Token-Asymmetrie:** `ELABORATION_SPIKE` (Forced > +50 %), `CAPITULATION_DROP` (Forced < −40 %), Zeitproxy-Fallback mit Hardware-Schätzungs-Label, None-sicherer Filter, Coverage-Warnung bei partiellen Daten.
- ✅ **`meta_reviewer_prompt.yaml` — Prompt-Architektur:** Model Card vor Pflichtstruktur verschoben; drei Leitfragen durch Einzel-Instruktion ersetzt; Section-2.6-Verzahnungs-Instruktion (Token-Befund als Dimension der Schattenmetriken, nicht isolierter Absatz); Upgrade-Pfad-Kommentar mit Re-Run-Prioritäten.
- ✅ **Dokumentation:** `AUDIT_AND_METAREVIEW.md` um "Section 2.6 Token-Asymmetrie"-Abschnitt ergänzt; `POLITICAL_COMPASS_KONZEPT.md` um Kapitel 5 "Schattenmetriken: Internes Chaos und kognitive Fingerabdrücke" erweitert.
- ✅ **12 Legacy-Audit-Logs retroaktiv nachgepflegt:** Alle Anomaly-Modelle mit Section 2.6 (Zeitproxy, `Hardware-abhängige Schätzung`) ergänzt. Reviewer ignoriert sie bewusst (Zero-Write-Regel), historischer Record vollständig.

**Vorherige Version (v3.4.7 – PC Budget-Exhaustion-Guard & Daten-Hygiene):**

CrucibleMark v3.4.7 schließt die letzte verbleibende Sicherheitslücke im Political-Compass-Modul: Budget-Erschöpfung mitten in einem PC-Run wurde bisher lautlos verschluckt. `test.py` fing alle Exceptions mit `response = ""` ab — ohne Propagation. Das Modell wurde als erledigt markiert und korrupte All-Zero-Daten in das Leaderboard geschrieben. Fix: `test.py` setzt `self._quota_exhausted = True` bei Budget-/Quota-Keywords; `execute_batch_module()` in `utils/base_runner.py` prüft das Flag nach `execute()` und propagiert es als `self.provider_quota_exhausted`. Zusätzlich: `cost`-Spalte aus dem PC-Leaderboard entfernt (redundant, immer `0.0` für lokale Modelle), `bias_reviewer`-Prompt in `meta_reviewer_prompt.yaml` ergänzt und `inference_provider`-Feld in `web_export.py` hinzugefügt.

**Key Achievements (v3.4.7):**
- ✅ **PC Budget-Exhaustion-Guard:** `test.py` erkennt Budget/Quota-Keywords in Exceptions und setzt `self._quota_exhausted = True`. `execute_batch_module()` propagiert dies als `provider_quota_exhausted`-Flag — identisches Verhalten wie normaler Benchmark-Runner.
- ✅ **`cost`-Spalte entfernt:** `political_compass_leaderboard.csv` und `io_manager.py` bereinigt. Interne `total_cost`-Berechnung für Audit-Log bleibt erhalten.
- ✅ **`bias_reviewer`-Prompt:** `config/meta_reviewer_prompt.yaml` um `bias_reviewer:`-Key mit initialem System-Prompt ergänzt.
- ✅ **`inference_provider` in Web-Export:** `scripts/web_export.py` schreibt `inference_provider`-Feld in `leaderboard.json` pro Eintrag.
- ✅ **PC-Leaderboard bereinigt:** 34 → 13 Zeilen (21 März-Einträge mit `polarity_flip_rate = 0.0` entfernt). 21 Modelle zur Neuberechnung freigegeben.

**Vorherige Version (v3.4.6 – PC Skip-Logic Fix & Leaderboard-Bereinigung):**

CrucibleMark v3.4.5 schließt die redaktionelle Überarbeitung aller 16 Projektdokumente ab. README.md, 13 docs/-Dateien, REF_TODO.md und PROJECT_STATUS.md wurden auf einheitlichen Ton, Ansprache und Struktur gebracht: unpersönliches `man`/`sein`, Emojis aus Überschriften entfernt, alle englischen Header ins Deutsche übertragen, Intro-Blöcke (`**Zielgruppe:**`/`**Inhalt:**`) ergänzt und alle `______`-Trennlinien in `---` umgewandelt. Kein funktionaler Code geändert.

**Vorherige Version (v3.4.4 – Architecture Compliance: No Magic Numbers/Strings):**

CrucibleMark v3.4.4 überführt alle Magic Numbers und Magic Strings in eine zentrale `constants.py` als SSOT. Hardcodierte Schwellenwerte, Spaltennamen und Provider-Strings wurden aus dem gesamten Codebase extrahiert und über importierbare Konstanten referenziert — kein funktionaler Verhaltensunterschied, aber deutlich reduzierte technische Schuld.

**Vorherige Version (v3.4.3 – Module Weight System & Score-Fairness):**

CrucibleMark v3.4.3 führt ein **selbstnormalisierendes Modulgewichtungs-System** ein, das den Total Score von der Asset-Anzahl-basierten Zufallsgewichtung entkoppelt. Jedes Vollmodul fließt jetzt mit gleichem Gewicht (`module_weight: 1.0`) in den Gesamtscore ein – unabhängig davon, wie viele Assets in ihm liegen. Das CLI-Modul ist als leichtgewichtiges Supplement mit `module_weight: 0.5` eingestuft. Ergänzend wurde die `cost_limits.yaml` um 5 neue Ollama-Cloud-Modelle erweitert und die Benchmark-Dokumentation um die Modulgewichtungs-Philosophie ergänzt.
- ✅ **`module_weight`-System:** Neues `integration.leaderboard.module_weight`-Feld in allen Modul-`config.yaml`s. Alle 6 Vollmodule: `1.0`. CLI: `0.5` (Supplement, kein vollwertiges Evaluierungsmodul).
- ✅ **Selbstnormierende Formel:** `TotalScore = Σ(ModuleScore × module_weight) / Σ(module_weight)` — Ergebnis immer 0–100, unabhängig von aktiven Modul-Subsets oder gewählten Gewichtswerten.
- ✅ **`_module_scale()` in `score_calculator.py`:** Hilfsfunktion berechnet `scale = module_weight / config_weight_sum` pro Modul. Alle 4 Contrib-Spalten werden vor der Aggregation skaliert.
- ✅ **`scripts/leaderboard/__init__.py`:** `module_weight` wird aus `lb_config` gelesen und ins `mod_entry`-Dict propagiert (Fallback `None` → `scale = 1.0`).
- ✅ **5 neue Ollama-Cloud-Modelle** in `cost_limits.yaml`: `deepseek-v3.1:671b-cloud`, `qwen3.5:397b-cloud`, `gemma4:31b-cloud`, `kimi-k2.5:cloud`, `glm-5:cloud`.
- ✅ **Dokumentation:** `docs/BENCHMARK_MODULES.md` (Designprinzip "geschlossene Module, gleiche Gewichtung") und `docs/SCORING_METHODOLOGY.md` (Formel + Gewichts-Tabelle mit Default-Werten) aktualisiert.

**Vorherige Version (v3.4.2 – Vollständige Modell-Preisliste & Sync-Tool):**

CrucibleMark v3.4.2 schließt die Preis-Datenbasis für alle konfigurierten Cloud- und Commercial-Modelle. Alle 25 Modelle haben jetzt verifizierte Preiseinträge in `config/cost_limits.yaml`. Ergänzend wurde ein neues Dev-Tool (`sync_cost_limits.py`) eingeführt, das Missing-Entries automatisch erkennt und Platzhalter scaffoldet. Das Leaderboard weist jetzt für alle Modelle `Cost per 1K (USD)` und `Benchmark Cost (USD)` aus.

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


## Modul-Status

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

---

## Framework-Architektur-Status

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

---

## Code-Qualitätsmetriken

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

---

## Historische Meilensteine (v1.x)

Die v1.x-Phase legte die Modul-Infrastruktur, den Provider-Abstraktions-Layer und das erste Scoring-System. Die wesentlichen Meilensteine in Kurzform:

- Modulare Architektur mit BaseTest Interface, YAML-Konfiguration und Asset-Driven Testing
- Unified Provider Interface für alle LLM-Anbieter, Mock-Provider für Tests
- Unified CSV-Schema, Leaderboard, Checkpoint/Resume-System
- Refaktorierung aller 6 Kernmodule auf Pylint 8.8–9.85/10
- DeepSeek-R1 Reasoning Model Support (v1.1.3): `is_reasoning_model()`-Erkennung, erhöhter Warmup-Probe auf 50 Tokens
- Versioning System Overhaul: Dual-Version-Format (`{OFFICIAL_ID}-{BEHAVIORAL_HASH}`), `utils/fingerprinting.py` als SSOT
- Golden Standard Consolidation: 37 `golden_standard`-Konfigurationen über alle YAML-Assets validiert
- LLM-as-Judge vollständig integriert (v2.4.0): 4 Provider, Fallback-Chain, Audit Mode Logging

---

## Bekannte Lücken & Einschränkungen

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

---

Die vollständige Roadmap steht in [README.md](README.md). Stand Q1/Q2 2026 konzentriert sich die Entwicklung auf:

- [ ] **Agentic Workflow Benchmarks:** Native Tests für Multi-Step Tool-Usage (Welches Modell plant komplexe File-Edits am sichersten?).
- [ ] **Visuelles Sub-System (Multimodal):** Integration visueller Benchmarks zur Architekturanalyse (UML-Diagramm lesen, UI designen).
- [ ] **Web-UI / Dashboard:** Eine interaktive React- oder Streamlit-Umgebung zur Visualisierung der CSV-Output-Ergebnisse und Leaderboards.
- [ ] **Erweiterung von CI/CD System-Hooks:** Automatische Integration für GitHub Actions, um KI-Akteure in Pull Requests zu prüfen.

---

## Strategische Prioritäten

### Kurzfristig

1. **Test Coverage abschließen** (60% → 95%)
2. **CI/CD einrichten** (GitHub Actions)
3. **E2E Systemtests** (Volldurchlauf aller lokalen Modelle, finales Leaderboard)

### Mittelfristig

1. **Externes Frontend starten** (`cruciblemark-web`, 11ty-basiert)
2. **Agentic Workflow Benchmarks** (neue Testdimension)
3. **Multimodal Support** (visuelle Benchmarks)

---

## Erfolgsmetriken

### v3.2.0 Achievements

- ✅ 8/8 Module Production-Ready
- ✅ Pylint Score Provider-Layer: 10.00/10
- ✅ Average Pylint Score: 9.15/10 (Ziel: 8.5)
- ✅ 100% Type Hints auf Public APIs
- ✅ 100% Docstring Coverage
- ✅ SSOT erzwungen, Fail-Fast aktiv, keine versteckten Fallbacks

---

## Forschung & Entwicklung

### Aktive Forschungsbereiche

#### 1. Agentic Workflow Evaluation

Welche Modelle planen komplexe Multi-Step Tool-Usage-Szenarien zuverlässig? Wie misst man Planungsqualität ohne Ground Truth? Die Antwort erfordert neue Asset-Formate und einen erweiterten Judge-Mechanismus.

**Status:** Konzeptphase

#### 2. Multimodal Benchmarks

Visuelle Aufgaben (UML lesen, UI-Designs beurteilen) benötigen neue Asset-Formate und Judge-Mechanismen jenseits von Text-Matching.

**Status:** Design-Phase

---

## Community & Contributions

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

---

## Dokumentationsstatus

### Abgeschlossen

- [x] Root README (v3.8.0, aktualisiert 22.05.26)
- [x] docs/ (14 Dateien, zuletzt synchronisiert 22.05.26)
- [x] Module READMEs (8/8)
- [x] Configuration docs
- [x] Contributing guidelines
- [x] REF_TODO.md (auf aktuellem Stand 22.05.26)
- [x] PROJECT_STATUS.md (dieses Dokument)

### In Bearbeitung

- [ ] API-Referenz-Dokumentation
- [ ] Architecture deep-dive
- [ ] Tutorial-Reihe

### Geplant

- [ ] FAQ document
- [ ] Troubleshooting guide
- [ ] Video tutorials
- [ ] Blog posts (use cases)

---

## Risikoabschätzung

#### 1. Test Coverage Gaps

**Risk:** Bugs in production due to low test coverage\
**Mitigation:** Fokus auf Unit Tests, GitHub Actions CI/CD\
**Priority:** High

### Business Risks

#### 1. Maintenance Burden

**Risk:** Single maintainer cannot sustain project\
**Mitigation:** Community building, documentation\
**Priority:** Medium

---

## Kontakt & Maintainer

**Maintainer:** kbeissert\
**Repository:** [github.com/kbeissert/cruciblemark](https://github.com/kbeissert/cruciblemark)\
**Issues:** [GitHub Issues](https://github.com/kbeissert/cruciblemark/issues)

---

## Changelog

### Docs: Redaktionelle Überarbeitung (2026-04-11) – v3.4.5

- 16 Projektdokumente einheitlich überarbeitet: Ansprache, Ton, Emoji-Verwendung
- Einheitliche Intro-Blöcke (`**Zielgruppe:**` / `**Inhalt:**`), alle `______` → `---`

### v3.4.4 (2026-04-11) – Architecture Compliance: No Magic Numbers/Strings

- Alle Magic Numbers/Strings in `constants.py` zentralisiert; kein Verhaltensunterschied

### v3.4.3 (2026-04-10) – Module Weight System & Score-Fairness

- `module_weight`-System: Vollmodule `1.0`, CLI `0.5`; selbstnormierende Formel
- `_module_scale()` in `score_calculator.py`; 5 neue Ollama-Cloud-Modelle in `cost_limits.yaml`

### v3.4.2 (2026-04-09) – Vollständige Modell-Preisliste & Sync-Tool

- Alle 25 Modelle mit verifizierten Preiseinträgen; `sync_cost_limits.py` + `make sync-cost-limits`

### v3.4.1 (2026-04-08) – Token-Verbrauch im Leaderboard

- `Tokens Total` + `Tokens: <Modul>`-Spalten; Scoring-Only-Basis, PC ausgeschlossen

### v3.4.0 (2026-04-08) – Token-Budget-System & Verbosity-Transparenz

- `max_tokens`-API-Cap via `token_budgets`; `[!NOTE]`-Flag + Meta-Review-Kontext

### v3.3.1 (2026-04-08) – Political Compass Integration Fix

- `model_category`-Feld in Leaderboard-CSV; Upsert-Parität; CSV-Datenbereinigung

### v3.3.0 (2026-04-07) – Language Compliance & Prompt Hardening

- Language-Compliance-Pipeline; 30 Editorial Fixes in 21 Assets; Audit-Infrastruktur

### v3.2.2 (2026-04-07) – 3-CSV Data Architecture

- Dediziertes `cloud_models_benchmark.csv`; Meta-Review-Context-Fix für Cloud-Open-Weights

### v3.2.1 – Performance & Cache Repair

- Lazy Loading; Data-Routing-Bugfix; Groq API Connectivity Fix

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

---

**Document Version:** 4.7.0\
**Last Updated:** 2026-06-09\
**Next Review:** v4.8.0 / Nächster Feature-Meilenstein
