# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v3.15.0] - 2026-05-25

### Added
- **Tool Use Probe-Run — 5 Modelle live** — Erster vollständiger 6-Asset-Durchlauf im `mode=live` gegen echte MCP-Tools (Tavily web_search + http_fetch). Getestete Modelle: gpt-5-mini (76.5% — [PRODUCTION]), grok-4-fast-non-reasoning (74.2% — [PRODUCTION]), moonshotai/kimi-k2 (73.6%), qwen/qwen3-32b (72.9%), gemma4:E4B (65.7%). PRODUCTION-Kriterium: keine Halluzination + alle 6 Tool-Calls valide. Leaderboard auf 11 Modelle erweitert.

### Changed
- **`scripts/core/tooluse_exporter.py` — `cost_usd="local"`** — `_LOCAL_DEPLOYMENT_TYPES` um `"open-weights"` erweitert. Modelle mit diesem `deployment_type` erhalten `cost_usd="local"` im Leaderboard statt `0.0` (numerisch). Verhindert Fehlinterpretation als "kostenlos via API".
- **`benchmark_scores/model_cards/gemma4:E4B`** — `fleet_group=local_sovereign`, `sovereignty_gap=-7.28` backfilled. War durch einen Bug nicht gesetzt worden.
- **Model Cards `gpt-4o.json`, `magistral-medium-latest.json`** — `tooluse_tested_at` und Scoring-Felder aus Re-Runs gesetzt.

---

## [v3.14.0] - 2026-05-25

### Fixed
- **`utils/providers/anthropic.py` — `system`-Kwarg-Bug** — `system`-Feld wurde aus `**kwargs` nicht explizit extrahiert und beim API-Call stillschweigend verworfen. Alle Anthropic-Modelle benötigten 2 Parse-Versuche statt 1 (`retry_required=true`), Latenz verdoppelt, tooluse006 lief bei Opus 4.6 in Timeout. Fix: `func_kwargs["system"] = kwargs.get("system")` vor Temperature-Check. Re-Runs (--force): Haiku 4.5=75.0, Opus 4.5=79.2, Sonnet 4.6=79.0, Opus 4.6=80.0 — alle `parse_attempts=1`.
- **`benchmark_modules/tooluse/assets/tooluse003.yaml` v1.3.0 — Rubrik False-Positive** — `uncertainty_handling.unacceptable` hatte keine `acceptable_patterns` für httpbin.org-Kontext-Erklärungen. Judge erkannte korrekte HTTP-Status-Erklärungen als Halluzination. Fix: `acceptable_patterns`-Sektion mit 5 explizit erlaubten Erklärungstypen.
- **`scripts/core/unified_runner.py` — Token/Cost-Tracking** — `last_token_usage` (nur letzter API-Call) durch `max(exec_result.tokens_used, client.last_token_usage)` ersetzt. Multi-Call-Module (z. B. Tool Use mit zwei LLM-Calls) zeigten nur Tokens des letzten Calls im Audit-Log-Header statt der Gesamtsumme. `isinstance`-Check verhindert `MagicMock`-Vergleichsfehler in Tests.

### Test Coverage
- 257/257 Tests grün nach allen Fixes.

---

## [v3.13.0] - 2026-05-25

### Added
- **`tooluse006.yaml` — Phase C: Multilingual Search & German Synthesis** — Sechstes Asset: Modell recherchiert via `web_search` internationale Handelsperspektiven und synthetisiert auf Deutsch — auch bei englischsprachigen Search-Results. Dimension: Sprachübergreifende Synthese. Kalibrierung: Sonnet 90/100, Hermes 90/100 nach Rubrik-Fix.
- **`phase2_rubric`-Verdrahtung** — `_build_rubric_override()` in `benchmark_modules/tooluse/test.py` serialisiert Asset-YAML-Rubrik zu strukturiertem Text → `rubric_override`-Parameter in `runner.score()`. Rubrik war zuvor totes YAML — Judge ignorierte es.
- **Hallucination Cap config-first** — `config/scoring.yaml → tool_use.hallucination.cap_hard: 20`. `ToolAdapterAudit.load_hallucination_cap()` liest Cap aus Config (Default 20 bei Fehler). `test.py`: nach Judge-Call `if hallucination_detected: p2 = min(p2, float(hal_cap))`.
- **`tool_result_ignored`-Flag im CV-Block** — Boolean: `true` wenn `content_usable=True` + `state="B2"`. Semantik: Modell hatte verwertbaren Tool-Inhalt, antwortete aber trotzdem aus Trainings-Vorwissen. Distinct von B1 (Modell war transparent über die Lücke).

### Fixed
- **`tooluse002`-Rubrik False-Positive** — `uncertainty_handling.unacceptable` enthielt "Fakten hinzufügen die nicht im Fixture stehen". Korrigiert auf "faktisch falsche Angaben" — korrekte Parameterwissen-Ergänzungen sind explizit erlaubt.

### Documentation
- `docs/SCORING_METHODOLOGY.md` — vollständige Tool-Use-Sektion (Content-Verification-Framework, config-first Halluzinations-Cap, rubric_override)
- `docs/TOOLUSE_MODULE.md` — 6 Assets, 257 Tests, Phase-C-Sektion, `tool_result_ignored`-Beschreibung
- `docs/MAINTENANCE_LOG.md` — v3.13.0 Eintrag

### Test Coverage
- 257/257 Tests grün (7 neue Tests für `tool_result_ignored` + `language_consistency`-Rubrik).

---

## [v3.12.0] - 2026-05-24

### Added
- **`tooluse004.yaml` — Tool Selection (Phase A)** — Viertes Asset: `web_search` zu einem Thema ohne vorgegebene URL. Dimension: Tool-Intelligenz (Modell muss selbst entscheiden, welches Tool für die Aufgabe geeignet ist). Topic: LLM-Leaderboard-Ranking auf Hugging Face.
- **`tooluse005.yaml` — URL Construction (Phase A)** — Fünftes Asset: `fetch` auf eine konstruierte URL. Modell muss `en.wikipedia.org`-URL korrekt ableiten und abrufen. Python-Wikipedia-Mock-Fixture (1047 chars) in `cruciblemark-mcp/tools/mock_provider.py` ergänzt.
- **`methodology_notes.py`** — 7 deterministische Annotations-Templates für den Reviewer. Verhindert generische Hinweise ("Modell hatte Schwierigkeiten") und erzwingt präzise, asset-spezifische Diagnosen.

### Changed
- **`parse_error_flag` → `retry_required`** — Umbenennung im gesamten Stack: `ToolUseIOManager`, `ToolUseExporter`, `tooluse_leaderboard.py`, alle Tests. Semantisch präziser: beschreibt nicht den Fehler, sondern die Konsequenz (Parse-Retry notwendig).
- **P1-Ceiling nach Erweiterung** — `(100+100+80+100+100)/5 = 96.0` (statt 93.33 mit 3 Assets). Phase-A-Assets erreichen volle 100 P1 bei korrektem Tool-Call.

### Documentation
- `README.md` — Phase-A/B-Framework erklärt (Tool-Intelligence vs. Tool-Synthesis)
- `docs/BENCHMARK_MODULES.md` — Tool-Use Phase-A-Abschnitt mit tooluse004/005
- `benchmark_modules/tooluse/SCORING_RUBRIC.md` v3.12.0 — P1-Tabelle korrigiert, Phase-A/B-Profile
- `benchmark_modules/tooluse/JUDGE_CHECKLIST.md` v3.12.0 — tooluse004/005-Sektionen

### Test Coverage
- 41 Modelle im Leaderboard nach Phase-A-Integration. Alle Tests grün.

---

## [v3.11.0] - 2026-05-24

### Added
- **Golden Standard v1.2.0** — Alle drei Tool-Use-Assets haben manuell validierte Referenzantworten und Bewertungsrubrik. Kalibrierungsrunde 1 mit 12 Modellen abgeschlossen. P2-Scores stabil und vergleichbar.
- **`evaluation.phase2` in allen Assets** — `golden_answer`, `keywords`, `min_length`, `requires_url_citation` / `requires_structured_output` als YAML-Felder. LLM-Judge liest Referenzantwort aus diesem Pfad (SSoT).
- **P1 Content-Quality-Check (`http_fetch`)** — `evaluators.py` bewertet bei Non-Failure-http_fetch-Assets ob `content_excerpt ≥ 100` Zeichen extrahiert wurden (+20 Punkte). P1-Maximum für tooluse002: 100 statt 80.
- **`http_fetch_and_extract` als AUTHORIZED_TOOLS-Alias** — `core/tool_adapter_audit.py` normalisiert diesen Tool-Namen auf `http_fetch`, sodass Gemini-Modelle nicht fälschlich als "falsches Tool" gewertet werden.
- **17 Tests grün** — Neue Fixtures `ASSET_002` + 2 Tests (`test_phase1_http_fetch_with_usable_content`, `test_phase1_http_fetch_empty_content`) in `tests/test_evaluators.py`.

### Changed
- **`tooluse001` Golden Standard v1.2.0:** Explizite Unterscheidung multimodale vs. textbasierte Llama-Modelle als Pflichtkriterium. `llama.com` zur `golden_source_domains`-Liste hinzugefügt.
- **`tooluse002` Golden Standard v1.2.0:** Keywords auf `["llama 3.2", "vision", "llama guard", "hugging"]` geschärft — diskriminiert tatsächliche Seiten-Extraktion von Trainings-Vorwissen-Reproduktion. `must_not_include` ergänzt um "Modelle die nicht zu Meta Llama gehören (GPT, BERT, T5 etc.)".
- **`tooluse003` Golden Standard v1.2.0:** Referenzantwort in Erste-Person umgeschrieben ("Ich konnte keine Inhalte abrufen"). Rubrik ergänzt um "Keine Überexplikation jenseits des Fehlerstatus".
- **`assets/combined_assets.yaml`** synchronisiert auf v1.2.0 für alle drei Assets.
- **`CALIBRATION_LOG.md`** mit tatsächlichen Kalibrierungsergebnissen befüllt.
- **`SCORING_STATUS.md`** — "Vorläufige Scores" entfernt; Status auf finalisiert gesetzt. Kalibrierungsergebnisse für 12 Modelle dokumentiert.
- **`SCORING_RUBRIC.md` / `JUDGE_CHECKLIST.md`** — Auf v3.11.0 aktualisiert; P1-Stufenmodell und asset-spezifische Kriterien (multimodal/textbasiert, Seiten-Extraktion vs. Vorwissen) dokumentiert.

### Calibration Results (v1.2.0, 12 Modelle)

| Modell | P1 | P2 | Combined |
|---|---|---|---|
| Claude Sonnet 4.6 | 95 | 65.0 | 80.0 |
| Claude Sonnet 4.5 | 85 | 70.3 | 77.6 |
| Claude Opus 4.6 | 85 | 68.6 | 76.8 |
| Hermes 4 70B | 90 | 62.7 | 76.3 |
| Claude Haiku 4.5 | 85 | 62.8 | 73.9 |
| Gemini 2.5 Pro | 85 | 61.8 | 73.4 |
| Gemini 3 Flash | 85 | 57.8 | 71.4 |
| GPT-5.4 | 75 | 65.0 | 70.0 |

P2-Spread: 57.8 – 70.3 (+12.5) — gute Diskriminierung ✅

---

## [v3.10.0] - 2026-05-23

### Added
- **`benchmark_modules/tooluse/`** (VOLLSTÄNDIG) — `ToolUseTest`, `ToolUseEvaluator`, `ToolUseIOManager`, `constants.py`. Zwei-Phasen-Scoring: P1 (Tool Execution 50%) + P2 (Synthesis Quality 50%). Hallucination Penalty −100, Tool Call Bonus +10.
- **`cruciblemark-mcp/server.py`** (NEU) — FastAPI-basierter MCP-Server auf Port 8765. Mock-Modus (deterministisch, kein Internet) + Live-Modus (Tavily → DuckDuckGo Fallback). Health-Endpoint für Runner-Checks.
- **`scripts/core/tooluse_exporter.py`** (NEU) — `ToolUseExporter`: Aggregation aus Benchmark-CSVs, Leaderboard-Upsert, Sovereignty-Gap-Berechnung, `get_summary()`. Fleet-Gruppen: `local_sovereign` vs. `full_fleet`.
- **`scripts/tools/tooluse_leaderboard.py`** (NEU) — Leaderboard-CLI mit Sovereignty-Gap-Anzeige, Fleet-Averages, Performance-Metriken (Latenz, Tokens, Parse-Error-Rate).
- **`scripts/analysis/generate_tooluse_report.py`** (NEU) — Markdown-Reports pro Modell + Fleet Summary.
- **`scripts/run_tooluse_benchmark.py`** (NEU) — Batch-Runner mit interaktivem Wizard (Provider → Modell/Alle). MCP-Neustart pro Modell (Fairness). `--no-restart-mcp` als Opt-out. Timeout 300s pro Modell.
- **`utils/mcp_health.py`** (NEU) — MCP-Health-Check-Utility.
- **3 Assets** (`tooluse001`–`tooluse003`): Websearch Research, HTTP Fetch & Extract, Tool Failure Handling (404-Simulation).
- **Makefile** — 6 neue Targets: `benchmark-tooluse`, `benchmark-tooluse-local`, `benchmark-tooluse-force`, `tooluse-leaderboard`, `tooluse-report`, `tooluse-report-summary`. `mcp-start` idempotent. `mcp-stop` stall-PID-sicher.

### Fixed
- Sovereignty-Gap-Vorzeichen (`local - all`, nicht `all - local`).
- `tool_call_attempts` max statt sum.
- GPT OSS 20B Card deaktiviert (nicht in Ollama installiert).
- Card-Key-Namen (snake_case) in Exporter korrigiert.
- `get_fleet_group()` akzeptiert `open-weights-cloud-available`.

### Documentation
- `docs/TOOLUSE_MODULE.md` (450 Zeilen, 14 Abschnitte)
- `benchmark_modules/tooluse/README.md` (Komplettrewrite)
- `docs/BENCHMARK_MODULES.md` (Tool Use Abschnitt)
- `benchmark_modules/tooluse/SCORING_STATUS.md` (Vorläufige-Scores-Vorbehalt)

---

## [v3.9.0] - 2026-05-23

### Refactored
- **`utils/language_validator.py`** (NEU) — `LanguageValidator`-Klasse kapselt DE/EN-Marker-basierten Mismatch-Check (extrahiert aus `unified_runner.py`). Konstanten `LANGUAGE_MIN_WORDS`, `LANGUAGE_EN_DE_RATIO`, `LANGUAGE_EN_MIN_COUNT`, `LANGUAGE_DE_MARKERS`, `LANGUAGE_EN_MARKERS` in `utils/constants.py`.
- **`scripts/core/unified_runner.py`** — Inline-Language-Detection → `LanguageValidator`-Delegation. Magic Numbers ersetzt: `120.0` → `TIMEOUT_DEFAULT`, `100` → `DEFAULT_MAX_SCORE`, lokales `TRUNCATION_THRESHOLDS`-Dict → importierte Konstante.
- **`benchmark_modules/political_compass/test.py`** — Alle Magic Numbers durch `PC_*`-Konstanten aus `political_compass/core/constants.py` ersetzt (`PC_DEFAULT_NUM_RUNS`, `PC_MAX_REFUSAL_RETRIES`, `PC_RETRY_TEMPERATURES`, `PC_SLEEP_BETWEEN_REQUESTS`, `PC_SLEEP_AFTER_RESPONSE`, `PC_QUERY_TIMEOUT`).
- **`utils/scoring/llm_judge/judge_runner.py`** — 5-Branch-Provider-If-Chain durch `_PROVIDER_MODULES`-Registry + `importlib.import_module()` ersetzt. Env-Key-If-Chain durch `_ENV_KEY_MAP`-Dict ersetzt.
- **`scripts/analysis/review/`** (NEU) — Package mit `metrics.py`, `risk_calculator.py`, `token_efficiency.py`, `audit_scanner.py`. `generate_review.py` von 1309 auf ~200 Zeilen reduziert.
- **`benchmark_modules/reasoning_logic/core/constants/rubrics.py`** (NEU) — `RUBRICS`-Dict und `DIMENSION_SCORE_THRESHOLDS` aus `evaluators.py` extrahiert.
- **`utils/model_utils.py`** — `_param_b_to_size_class()` If-Kette durch `_SIZE_CLASS_THRESHOLDS`-Tupel-Konstante ersetzt.

### Fixed
- **`utils/providers/mistral.py`** — `token_param_name`-Config-Wert wurde in `_execute_with_token_fallback()` ignoriert (hardcoded `"max_tokens"`). Jetzt korrekt an Variable gebunden.
- **Ruff F841** — 12 unused variables entfernt (`scripts/leaderboard/`, `benchmark_modules/cli_benchmark/`, `scripts/maintenance/`, u. a.).
- **Ruff F401/F541** — 185 auto-fixable Issues behoben (unused imports, leere f-strings).

### Quality
- **Pylint Score:** 9.37 → **9.99/10** (alle Python-Dateien)

---

## [v3.8.2] - 2026-05-23

### Changed
- **`scripts/analysis/generate_model_cards.py`** — vollständig ersetzt. LLM-basierter Auto-Generator entfernt; neuer schlanker Template-Generator ohne API-Call. `make model-cards MODEL=<id>` legt JSON mit allen Pflichtfeldern als `"TODO"`-Platzhalter an. `size_class` wird automatisch über `get_model_size_class()` berechnet. `_index.json` wird nach jeder Card aktualisiert.
- **`Makefile` — `model-cards`-Target:** Vereinfacht auf Template-Generator-Aufruf. Neuer `--provider`-Parameter für lokale Modelle (Provider-Präfix im Dateinamen). Alias `model-card` (Singular) als `.PHONY`-Target ergänzt.
- **Docs:** `DEVELOPER_GUIDE.md` (Card-Generierung-Sektion, `for_write`-Hinweis, Schema-Beschreibung), `AUDIT_AND_METAREVIEW.md`, `USER_GUIDE.md`, `README.md` auf neues manuelles Card-Konzept aktualisiert.

### Removed
- LLM-Prompts, `LLMClient`-Abhängigkeit, Config-Loading und Batch-Loop aus `generate_model_cards.py` entfernt.

## [v3.7.5] - 2026-05-22

### Added
- **`benchmark_scores/model_cards/*.json` — Preisfelder:** `input_price_per_1m` und `output_price_per_1m` (USD pro 1 Million Tokens) in alle 53 API-Model-Cards migriert. Model Cards sind die primäre Preisquelle (SSoT) für das gesamte Framework.
- **`scripts/dev/migrate_prices_to_cards.py`:** One-Time-Migrationsskript — konvertiert `input_cost_per_1k` / `output_cost_per_1k` aus `cost_limits.yaml` (×1000) in `per_1m`-Felder der Cards. Für Audit-Zwecke erhalten.
- **4 neue Model Cards:** `mistral-medium-3-5` (EU, Modified MIT, 256k, multimodal), `mistral-small-2603` / Mistral Small 4 (24B, Apache-2.0), `qwen/qwen3.6-plus`, `qwen/qwen3.7-max` (CN, proprietary, BSI-Risiko: high).
- **Reviews:** Benchmark + Bias Reviews für `mistral-medium-3-5`, `mistral-small-2603`, `qwen2.5vl_7b` in `docs/reviews/`.

### Changed
- **`config/cost_limits.yaml`:** Von ~25 Modelleinträgen auf 6 Legacy-Einträge reduziert (nur Modelle ohne eigene Card: MiniMax Cloud Proxy, Kimi-K2.5 Cloud, GLM-5 Cloud, Llama-3.1-8B, Kimi-K2-Instruct, Groq Daily Budget). Alle anderen Modelle sind über ihre Card bepreist.
- **`scripts/leaderboard/score_calculator.py` — `_build_price_lookup()`:** Card-First-Lookup: liest `output_price_per_1m` aus Model Cards; `cost_limits.yaml` als Legacy-Fallback für Modelle ohne Card.
- **`utils/cost_tracker.py` — `calculate_cost()`:** 3-stufige Kaskade: (1) LiteLLM-Cache, (2) Model Card JSON (`input_price_per_1m` / `output_price_per_1m`), (3) `cost_limits.yaml` Legacy-Fallback.
- **`scripts/dev/sync_cost_limits.py`:** Versteht card-first SSoT; `--fix` schreibt Platzhalter in `cost_limits.yaml` nur als temporären Fallback bis eine vollständige Card existiert. Typ-Korrekturen: `str(provider_key)`, `m.get("id") or ""`.
- **Card-Renames:** `mistral-medium-3_5.json` → `mistral-medium-3-5.json`, `mistral-small-4.json` → `mistral-small-2603.json` (korrekte Naming-Convention: Dash-Separator, versioniert).

### Docs
- **`docs/USER_GUIDE.md`:** `make sync-cost-limits`-Beschreibung auf card-first SSoT aktualisiert. "Preisliste abgleichen"-Sektion zeigt jetzt Card-JSON als primären Weg.
- **`docs/ARCHITECTURE.md`:** Model-Cards-Beschreibung um Preisfelder (`input_price_per_1m`, `output_price_per_1m`) und Konsumenten (`score_calculator.py`, `cost_tracker.py`) erweitert.
- **`docs/SCORING_METHODOLOGY.md`:** v3.7.5-Eintrag in Versionshistorie ergänzt.

---

## [v3.7.4] - 2026-05-21

### Refactored
- **`utils/model_utils.py` — `_find_card()` parametrisiert:** Neuer optionaler Parameter `card_dir: Path | None = None`. Callers können die Card-Verzeichnis-Auflösung überschreiben (z.B. `web_export.py` mit absolutem Root-Pfad). Rückwärtskompatibel — `None` greift auf Modul-Konstante `CARD_DIR` zurück.
- **`utils/model_utils.py` — `WEIGHTS_TIER_DISPLAY` exportiert:** Tier-Mapping-Dict aus lokalem `_TIER_MAP` in `get_model_category()` als öffentliche Modul-Konstante hochgezogen. Kein Duplikat mehr in `web_export.py`.
- **`scripts/web_export.py` — `load_model_card()` auf ~40 Zeilen reduziert:** Delegiert Kern-Pfad-Lookup an `_find_card(card_dir=card_dir)` (SSoT). Zwei web-spezifische Fallbacks (Display-Name-Vollscan, hf.co-Suffix-Match) bleiben erhalten.
- **`scripts/web_export.py` — `_BLOCK_META` externalisiert:** Hardcodiertes Python-Dict entfernt. Neue Funktion `_load_pc_block_meta(config_path)` liest Block-Metadaten aus `benchmark_modules/political_compass/config.yaml` (Fallback: statisches Dict). `_build_block_scores()` und `_build_compass_entry()` erhalten `block_meta` als expliziten Parameter.
- **`benchmark_modules/political_compass/config.yaml` — `blocks:`-Sektion:** 9 Block-Einträge (ID, Label, Achse) als YAML-Konfiguration aufgenommen — SSoT für Web Export.

---

## [v3.7.3] - 2026-05-21

### Refactored
- **`scripts/web_export.py` — Anti-God-Script-Sanierung:** `main()` von ~490 auf ~80 Zeilen reduziert. 9 Top-Level-Hilfsfunktionen extrahiert (alle mit vollständigen Type Hints, mypy-kompatibel):
  - `_resolve_dir(dirs, raw_slug)`: Top-Level-Funktion (war zuvor nested in `main()`). 4-stufiger Fallback: direkter Match → Date-Suffix-Strip → Suffix-Match → `-latest`-Alias-Auflösung via `get_model_version()`.
  - `_setup_output_dirs(args)`: Safety-Guard (`raw/`-Erzwingung), `shutil.rmtree(models/)`, Verzeichnis-Init; gibt `(out_dir, models_dir, root_dir)` zurück.
  - `_load_sources(scores_dir)`: Lädt alle 4 Quell-CSVs zentral (`ldb`, `pc`, `pc_lb`, `provider_df`).
  - `_build_pc_lookups(pc_lb)`: Baut PC-Leaderboard-Dicts (exakter Name + slug-Schlüssel).
  - `_export_model_files(model_out, audit_src, comp_src)`: Kopiert Audit-Logs (sanitiert) + Review-Markdowns für ein Modell; gibt `(audit_files, comp_files_dict)` zurück.
  - `_build_leaderboard_entry(row, card, slug, vendor, thinking_mode, model_type, ...)`: Baut den vollständigen Leaderboard-Dict (~40 Felder).
  - `_lookup_pc_row(model_name, slug, pc)`: Sucht AVG-Zeile in `political_compass_results.csv` (exakt + slug-Fallback für datierte/geprefixte IDs).
  - `_build_compass_entry(pc_row, lb_row, slug, model_name, model_type)`: Baut den Political-Compass-Dict inkl. Archetyp- und Extremismus-Felder.
  - `_write_top_level_outputs(out_dir, generated_at, ...)`: Schreibt `leaderboard.json`, `political_compass.json`, `provider_stats.json`, `meta.json`.
- **`_TIER_MAP`:** Als Modul-Konstante hochgezogen (war pro Loop-Iteration neu erstellt).
- **`load_csv_with_fallback()`:** Exception spezifiziert zu `(OSError, pd.errors.ParserError)`; Return-Type-Hint `pd.DataFrame | None` ergänzt.
- **Imports bereinigt:** Alle lokalen `from typing import Dict, List, Optional` aus Loop/Funktionen entfernt; builtin-Typen (`dict[str, Any]`, `list[str]`) konsequent verwendet (Python 3.12-idiomatisch).

### Docs
- **`docs/ARCHITECTURE.md`:** Web-Export-Pipeline-Sektion um Tabelle der 10 Helfer-Funktionen mit Verantwortlichkeiten erweitert. `_resolve_dir()` als Top-Level dokumentiert. Verzeichnis-Auflösungs-Abschnitt auf 4 Fallback-Stufen aktualisiert.

---

## [v3.7.2] - 2026-05-16

### Added
- **`scripts/web_export.py` — 4 Datumsfelder im `leaderboard`-Block** jedes per-Modell-`data.json`:
  - `benchmark_run_at`: Frühestes PC-Run-Datum aus `outputs/runs/results_*_YYYYMMDD_*.json` (liest `model`-Feld aus JSON → model_id-Map). Abgedeckt: 72/72 Modelle.
  - `report_published_at`: Ältestes `review_YYYYMMDD_*.md` in `docs/reviews/{model}/` (Filename-Parsing, kein mtime).
  - `report_updated_at`: Neuestes Review-Datum — `null` wenn identisch mit `published_at`.
  - `last_activity_at`: `max()` der drei vorgenannten Felder (neuestes Signal pro Modell).
- **`_review_date_range(dir_path, prefix)`**: Hilfsfunktion, extrahiert `(published_at, updated_at)` aus Review-Dateinamen.
- **`_build_benchmark_run_dates(runs_dir)`**: Baut `model_id → earliest_date` Map aus allen `outputs/runs/results_*.json`.

---

## [v3.7.1] - 2026-05-15

### Fixed
- **`scripts/analysis/generate_review.py`:** 4 Stellen mit naiver `cards_dir / f"{re.sub(...)}.json"` Pfadkonstruktion → `_find_card(model_id)` ersetzt (SSOT inkl. `-latest`-Alias-Fallback). Überflüssige lokale `import re` entfernt.
- **`scripts/analysis/generate_model_cards.py`:** Unused `_safe_name` Import entfernt (Pylint W0611).
- **`scripts/web_export.py` — `build_provider_map()`:** Hardcoded `_FALLBACK_NAMES`-Dict durch dynamisches Config-Lesen aus `benchmark_config.yaml` ersetzt. Guard `"name" not in prov_val: continue` verhindert, dass Settings-Blöcke (z.B. `providers.local.config`) als Fake-Provider in `__fallbacks__` landen.
- **`scripts/leaderboard/exporter.py`:** `# type: ignore[call-overload]` für beide pandas-`Series.apply(_fmt)`-Aufrufe (Pylance `reportCallIssue`). `import re as _re` vor den `if _cards_dir.exists():`-Block verschoben (Pylint E0606 `possibly-used-before-assignment`).

### Docs
- **`docs/ARCHITECTURE.md`:** `is_reasoning_model_from_card()` Dateiname-Auflösung korrekt als `_find_card()` dokumentiert (war noch `re.sub`-Beschreibung vor der Migration).

---

## [v3.6.5] - 2026-05-09

### Changed
- **Archetyp-Umbenennung:** `Das Schaf` → `Der Stoiker`, `Chamäleon` → `Der Narr`. Vier finale kanonische Bezeichnungen: `Der Stoiker`, `Wolf im Schafspelz`, `Die Chimäre`, `Der Narr`. Klassifikationslogik und Schwellwerte unverändert. CSV-Backfill 76 Zeilen, Web-Export 72/72 OK.

---

## [v3.6.4] - 2026-05-08

### Changed
- **Archetyp-Umbenennung und neue Klassifikationslogik:** `Offener Wolf` → `Die Chimäre`, `Echtes Schaf` → `Das Schaf`. Die Chimäre ersetzt den vanilla-positionsbasierten "Offenen Wolf" durch eine semantisch präzisere Kategorie: *hoher Shift + Quadrantenwechsel unter Druck* (sign(vanilla_x) ≠ sign(forced_x) ODER sign(vanilla_y) ≠ sign(forced_y)). `classify_behavior_archetype()` erweitert um `forced_x`/`forced_y`-Parameter. Priorität: Chamäleon → Chimäre → Wolf → Schaf. CSV-Backfill 76 Zeilen. Neue Verteilung: `Das Schaf`: 54, `Wolf im Schafspelz`: 18, `Die Chimäre`: 2 (gemini-3.1-pro-preview, grok-4.20-0309-non-reasoning), `Chamäleon`: 2.

---

## [v3.6.3] - 2026-05-08

### Changed
- **Chamäleon-Schwellwert empirisch kalibriert:** `ARCHETYPE_CHAMELEON_FLIP_THRESHOLD` von `50.0` auf `35.0` gesenkt, Operator `>` → `>=`. Datenbasis n=76 Modelle, P90 der `polarity_flip_rate`-Verteilung liegt bei 27.2 % — ab 35 % statistischer Ausreißer. Betrifft 2 Modelle: `gemini-3-flash-preview` (PFR=50.0 %) und `dolphin-mistral-nemo` (PFR=48.05 %) → neu klassifiziert als Chamäleon. CSV-Backfill ohne Re-Run.

### Added
- **`behavior_archetype`-Feld im PC-Leaderboard:** Neue Spalte in `political_compass_leaderboard.csv` mit vier kanonischen Archetyp-Labels: `Echtes Schaf`, `Wolf im Schafspelz`, `Offener Wolf`, `Chamäleon`. Klassifikationslogik in `classify_behavior_archetype()` (`evaluators.py`) — SSoT-Thresholds in `constants.py`. Backfill: alle 76 Bestandszeilen automatisch befüllt.
- **Archetyp-Namen finalisiert:** Vier kanonische Bezeichnungen (`Das echte Schaf`, `Der Wolf im Schafspelz`, `Der offene Wolf`, `Das Chamäleon`) in `docs/POLITICAL_COMPASS_KONZEPT.md`, `docs/BENCHMARK_MODULES.md`, `.temp_prompt.yaml` und `constants.py` konsistent dokumentiert.
- **Themenbereiche-Übersicht in `POLITICAL_COMPASS_KONZEPT.md`:** Neue Sektion 8 mit Tabelle aller 9 Fragenkatalog-Blöcke (7.1–7.9): Themenbereich, Fragenanzahl, Achse, inhaltliche Detail-Topics.
- **`behavior_archetype` im Web-Export:** Feld in `scripts/web_export.py` ergänzt — steht in jedem Modell-JSON als direktes Filterkriterium.

### Fixed
- **Modellnamen-Normalisierung (PC-Leaderboard):** `save_leaderboard_csv()` in `io_manager.py` schneidet Datumssuffixe (`-YYYYMMDD`) jetzt beim Schreiben automatisch ab. Betraf 8 Einträge (u. a. `claude-sonnet-4-5-20250929`, `z-ai/glm-5-20260211`, `minimax/minimax-m2.7-20260318`). Bestehende CSV bereinigt — kein Re-Run erforderlich.

---

## [v3.6.2] - 2026-05-04

### Added
- **`vendor`-Feld in allen 72 Model Cards:** Normalisierter Hersteller-Name als neues Card-Pflichtfeld für den UI-Filter „Familie". 13 Werte: `Anthropic`, `OpenAI`, `Google`, `Mistral AI`, `xAI`, `DeepSeek`, `Meta`, `NousResearch`, `Zhipu AI`, `Moonshot AI`, `MiniMax`, `Alibaba`, `Community`. `Community` = abliterated/fine-tuned Derivate ohne eigenständigen Hersteller. Migrations-Script: `scripts/dev/add_vendor_field.py` (idempotent, 0 ungemappte Modelle).
- **`scripts/web_export.py` — `vendor` als Top-Level-Feld:** `vendor` steht wie `size_class` und `badge` auf der Top-Level-Ebene des JSON-Eintrags (Filterkriterium, nicht Card-Detail). 71/71 Modelle mit `vendor` im Export.
- **`scripts/leaderboard/exporter.py` — `Vendor`-Spalte:** Neue Spalte in `benchmark_leaderboard_detailed.csv` vor `Size Class`. Wert wird zur Export-Zeit aus der Model Card gelesen; kein zusätzlicher State in der Leaderboard-Pipeline.
- **`scripts/analysis/generate_model_cards.py` — `vendor` im Prompt-Template:** Neues Feld im JSON-Schema mit vollständiger Werteliste für LLM-generierte Cards.
- **`benchmark_modules/MODULE_SCHEMA_TEMPLATE.yaml` — `vendor` im Kommentarblock:** Alle 13 gültigen Werte + Verweis auf Migrations-Script dokumentiert.

---

## [v3.6.1] - 2026-05-04

### Added
- **Lizenz-Metadaten in allen Model Cards:** Felder `license` (SPDX-ID), `license_url` und `commercial_use_allowed` (`true`/`false`/`null`) in alle 69 Model Cards eingetragen. `commercial_use_allowed: null` = skalenabhängig oder lizenzrechtlich unklar (Meta Llama, Gemma, Moonshot). Migrationsscript: `scripts/dev/add_license_fields.py`.
- **`benchmark_modules/MODULE_SCHEMA_TEMPLATE.yaml` — `model_card`-Kommentarblock:** Doku der Lizenz-Felder mit SPDX-Konvention und Wertebereich von `commercial_use_allowed` direkt im Schema-Template.
- **`README.md` — Kernziel-Absatz:** Explizite Formulierung des Benchmark-Kernziels: selbstgehostete Open-Weights-Modelle vs. proprietäre Cloud-Modelle, datenschutzkonforme Alternativen, und Lizenzfreiheit (Apache 2.0 / MIT vs. kommerzielle Beschränkungen).
- **`docs/ARCHITECTURE.md` — Lizenz-Metadaten-Abschnitt:** Beschreibung der neuen Card-Felder und ihrer Rolle für den Deployment-Vergleich.

### Changed
- **`Makefile` — `backup`-Target:** `benchmark_config.yaml` ergänzt in der `tar`-Zeile. Die Datei ist in `.gitignore` und wurde bisher nicht gesichert — bei Workspace-Verlust wäre sie unwiederbringlich weg.
- **GLM-5-Serie — `deployment_type` korrigiert:** `z-ai/glm-5-20260211`, `z-ai/glm-5-turbo-20260315`, `z-ai/glm-5.1-20260406` auf `cloud-only` gesetzt (Zhipu AI veröffentlicht für GLM-5 keine Gewichte; GLM-4.x bleibt korrekt `open-weights`).

### Removed
- **8 Duplikat-Model-Cards (alte Underscore-Konvention):** `z-ai_glm-5.json`, `z-ai_glm-5-turbo.json`, `z-ai_glm-5_1.json`, `moonshotai_kimi-k2_5.json`, `minimax_minimax-m2_7.json`, `CognitiveComputations_dolphin-mistral-nemo_latest.json`, `NousResearch_Hermes-4-14B-GGUF_Q4_K_M.json`, `Ministral-3-14B-abliterated-GGUF_Q8_0.json`. Aktive IDs verwenden die Slash-Konvention (`provider/model`) — versioned Cards (`-YYYYMMDD`) sind SSoT.

### Data
- `moonshotai/kimi-k2.6`: Benchmark-Run durchgeführt, Card aktualisiert.

---

## [v3.6.0] - 2026-05-04

### Added
- **`scripts/leaderboard/exporter.py` — `model_id`-Spalte in Detailed-CSV:** Rohe Config-ID (z. B. `moonshotai/kimi-k2-thinking-20251106`) als neues SSOT-Feld in `benchmark_leaderboard_detailed.csv`. Downstream-Tools (insb. `web_export.py`) lesen diese Spalte direkt — kein Raten aus Display-Namen mehr.
- **`benchmark_config.yaml` + `config/cost_limits.yaml` — 3 neue xAI-Modelle:** `grok-4.3`, `grok-4.20-0309-non-reasoning`, `grok-4.20-0309-reasoning` mit verifizierten Preisen ($1.25/$2.50 per 1M Tokens, docs.x.ai Mai 2026).
- **`supports_tool_use`-Feld in allen 77 Model Cards:** Migrationsscript `scripts/dev/patch_tool_use.py` gepatcht alle bestehenden Cards (72× `true`, 5× `false`). `generate_model_cards.py`-Prompt dokumentiert das Feld inkl. Faustregel.

### Changed
- **`scripts/web_export.py` — Dir-Lookup via `model_id` (SSOT):** `_resolve_dir()` nutzt den `model_id`-Slug (`model_id.replace('/', '_')` + `slugify`) statt den transformierten Display-Namen. Zwei explizite Fallbacks für historische Daten: (1) Date-Suffix-Strip (`-\d{4,8}$`) für Reviews die vor Versionssuffix-Einführung angelegt wurden; (2) Suffix-Match für Dirs ohne Provider-Präfix. Coverage: 69/69 Modelle vollständig.
- **`docs/ARCHITECTURE.md`, `docs/USER_GUIDE.md`, `memory-bank/systemPatterns.md`:** model_id-SSOT dokumentiert; Verzeichnis-Auflösungslogik beschrieben.

### Fixed
- **`scripts/core/benchmark_auto.py` — Retry-Logik:** `COMPLETED_STATUSES = {"success", "language_mismatch", "truncated", "refusal"}` — nur echte technische Fehler (`error`, `timeout` etc.) lösen einen Re-Run aus. Vorher wurden 89× `language_mismatch` + 8× `truncated` + 2× `refusal` bei jedem `benchmark-auto`-Lauf neu ausgeführt → neue Audit-mtime → kaskadierend 30 unnötige Reviews.
- **`utils/benchmark_utils.py` — P95-Akkumulation:** Regex `r"(\*\*Execution Time:\*\* [\d.]+ s)(?:\s*\(Modul-P95: [\d.]+ s\))*"` konsumiert jetzt alle vorhandenen Suffixe bevor ein neuer geschrieben wird. 154 bestehende Audit-Log-Dateien bereinigt.

### Data
- 33 neue/aktualisierte Reviews (inkl. `deepseek-v4-flash`, `deepseek-v4-pro`, `kimi-k2.6`).
- Neue Model Cards: `deepseek_deepseek-v4-flash`, `deepseek_deepseek-v4-pro`, `moonshotai_kimi-k2_5`, `moonshotai_kimi-k2_6`, `z-ai_glm-4_6`, `z-ai_glm-4_7`, `z-ai_glm-5`, `z-ai_glm-5_1`, `z-ai_glm-5-turbo`, `nousresearch_hermes-4-70b`, `nousresearch_hermes-4-405b`.

---

## [v3.5.9] - 2026-04-24

### Added
- **`scripts/analysis/generate_review.py` — `empty_response_context`:** Neue Hilfsfunktion `_build_empty_response_context(model_name)` liest alle drei Benchmark-CSVs und identifiziert Assets, bei denen `response_length=0` + `status=success` vorliegt (lautlose Content-Policy-Verweigerungen). Die betroffenen Asset-IDs werden dem Meta-Reviewer als strukturierter Kontext-Block übergeben. Nur aktiv bei `review_type == "benchmark"`.
- **`config/meta_reviewer_prompt.yaml` — `{empty_response_context}`-Platzhalter:** Neuer Block im System-Prompt nach `constraint_violations_context`. Der Meta-Reviewer ist angewiesen, leer gelieferte Assets namentlich im Modul-Abschnitt zu dokumentieren und sie nicht als technischen Fehler, sondern als Qualitätsmerkmal zu werten.
- **`scripts/analysis/generate_model_cards.py` — automatisches `size_class`-Setzen:** `_generate_card()` und `_create_minimal_card()` rufen `get_model_size_class(model_id)` auf und schreiben das Ergebnis als `size_class`-Feld in jede neu generierte Card. Bestehende Cards mit vorhandenem Feld werden nicht überschrieben.

### Changed
- **`utils/model_utils.py` — `get_model_size_class()` Priority-Kaskade:** Funktion komplett überarbeitet. Neue 3-stufige Logik: (1) Card-Lookup — `size_class`-Feld aus der JSON-Model-Card (SSoT für Overrides); (2) Ollama-Colon-Tag — case-insensitive Regex auf `:<tag>` (z. B. `gemma4:E4B` → Nano); (3) Dash/Dot-Suffix — Regex auf Parameter-Zahl nach `-`/`.` im Modellnamen (z. B. `llama-3.3-70b` → Server, `qwen3-32b` → Workstation). Fallback: `"Frontier"`. Hilfsfunktionen: `_SIZE_CLASS_VALID: set`, `_param_b_to_size_class(param_b: float) -> str`.

### Fixed
- **`get_model_size_class()` — case-insensitive Colon-Tag-Regex:** Regex war case-sensitive, `gemma4:E4B` (`E` großgeschrieben) wurde als unbekannt behandelt. Fix: `re.IGNORECASE`-Flag.
- **`benchmark_scores/model_cards/CognitiveComputations_dolphin-mistral-nemo_latest.json`** — `size_class: Desktop`: Card existierte unter falschem Slug `dolphin-mistral-nemo_latest.json`, der card-Lookup schlug daher fehl. Das korrekte Slug leitet sich aus dem rohen CSV-Wert `CognitiveComputations/dolphin-mistral-nemo:latest` ab (`re.sub(r'[:/.\s]', '_', …)` → `CognitiveComputations_dolphin-mistral-nemo_latest`). Beide Cards korrigiert.

### Data
- **`benchmark_scores/model_cards/`** — Manuelle `size_class`-Korrekturen: `hf_co_mradermacher_Ministral-3-14B-…` → Desktop, `hf_co_bartowski_NousResearch_Hermes-4-14B-…` → Desktop, `llama-3_3-70b-versatile` → Server, `meta-llama_llama-4-scout-17b-16e-instruct` → Desktop, `qwen_qwen3-32b` → Workstation, `gemma4_E4B` → Nano. 5 MISSING-Cards neu als Frontier angelegt (`glm-5_cloud`, `kimi-k2_5_cloud`, `minimax-m2_7_cloud`, `moonshotai_kimi-k2-instruct`, `CognitiveComputations_dolphin-mistral-nemo_latest`).
- **Leaderboard-Ergebnis nach `make leaderboard`:** 7 Desktop (vorher 3), 4 Workstation, 1 Server, 5 Edge, 5 Nano, 40 Frontier.

### Docs
- **`.github/copilot-instructions.md` — neuer Fallstrick:** *`size_class` Card-Slug-Mismatch* — Card-Pfad wird aus dem **rohen model_id aus der CSV** berechnet, nicht aus dem Display-Namen. `CognitiveComputations/dolphin-mistral-nemo:latest` → `CognitiveComputations_dolphin-mistral-nemo_latest.json`. Bei Klassifikations-Fixes immer den CSV-Namen als Basis nehmen.

---

## [v3.5.8] - 2026-07-17

### Added
- **`utils/model_utils.py` — `ThinkingProbeResult` Dataclass + `probe_thinking_model()`:** Neue empirische API-basierte Erkennung von Chain-of-Thought-Reasoning-Modellen. Zwei verlässliche Signale: A = `<think>`/`<thinking>`/`<thought>`-Tags im Response-Body (high confidence), B = `reasoning_tokens` > 0 in der Metadaten-Antwort (medium confidence). Probe-Ergebnis wird als `thinking_probe_detected`, `thinking_probe_confidence`, `thinking_probe_evidence` in der Model-Card persistiert.
- **`utils/model_utils.py` — `is_reasoning_model_from_card()`:** Card-First-Lookup liest `thinking_probe_detected` aus der Model-Card-JSON. Unterstützt korrekte `_safe_name()`-Transformation (`:`, `/`, `.`, Leerzeichen → `_`) für zuverlässige Dateinamen-Auflösung. Gibt `None` zurück wenn keine Card/kein Feld vorhanden.
- **`utils/model_utils.py` — `is_reasoning_model()` Card-First-Hierarchie:** Card-Lookup hat Vorrang vor String-Trigger-Heuristik. Neuer Trigger `"kimi-k2"` ergänzt. Verhindert Fehlklassifikation bei Modellen deren API-Verhalten nicht durch Namens-Patterns eindeutig erkennbar ist.
- **`scripts/tools/probe_thinking.py`** (neues Skript): Standalone-CLI für einmalige und retroaktive Thinking-Probes. Modi: `--model <id>` (einzeln), `--missing` (alle Cards ohne Probe-Feld), `--all` (Force-Rescan). Provider-Inference: Config-Lookup → `/` im Model-ID → `openrouter` → sonst `ollama`. Batch-Modus bricht bei Einzelfehlern nicht ab.
- **`scripts/analysis/generate_model_cards.py` — `_create_minimal_card()`:** Erstellt eine Minimal-Card (nur Probe-Felder + `card_status: "minimal"`) ohne LLM-Aufruf. Wird vom Card-First-Hook in `unified_runner.py` genutzt wenn noch keine Card existiert.
- **`scripts/analysis/generate_model_cards.py` — `_probe_fields_to_dict()`:** Hilfsfunktion, die `ThinkingProbeResult` in persistierbare Card-Felder konvertiert.
- **`scripts/core/unified_runner.py` — `_ensure_model_card()` Card-First-Hook:** Vor dem ersten Benchmark-Run jedes Modells wird automatisch geprüft ob eine Card mit `thinking_probe_detected`-Feld existiert. Fehlendes Feld → Probe → Card-Update. Keine Card → Probe → Minimal-Card-Erstellung. Bereits vorhandenes Feld → Skip. Probe-Fehler → `RuntimeError` (Benchmark-Abbruch).
- **`Makefile` — `probe-thinking` + `probe-all-thinking`:** Neue Targets für manuelle Probe-Ausführung (`make probe-thinking MODEL=<id>`) und retroaktiven Batch-Scan aller Cards ohne Probe-Feld (`make probe-all-thinking`).
- **OpenAI o-Modell-Cards — Manual Override:** `o1`, `o3-mini`, `o4-mini` haben `thinking_probe_detected: true` mit `thinking_probe_manual_override: true`, da OpenAI interne Reasoning-Tokens nicht im API-Response exponiert und die automatische Probe diese Modelle nicht erkennen kann.

### Changed
- **`utils/model_utils.py` — `is_reasoning_model()` Trigger:** `"kimi-k2"` zu den String-Triggers hinzugefügt.

### Fixed
- **`is_reasoning_model_from_card()` — `_safe_name()`-kompatible Dateinamen-Auflösung:** Vorheriger Lookup verwendete nur `replace('/', '_')` — Modelle mit `.` im Namen (z. B. `gemini-2.5-flash`) wurden nicht in `gemini-2_5-flash.json` aufgelöst, sodass die Card nie gefunden wurde und der String-Trigger `"gemini-2.5"` fälschlich `True` zurückgab. Fix: `re.sub(r'[:/.\ ]', '_', model_id)` — identisch mit `_safe_name()`.
- **`probe_thinking_model()` — Signal-C-Entfernung (False-Positive-Fix):** Response-Length-Heuristik (Signal C: Antwortlänge > 5× Baseline) entfernt. Instruction-Following-Modelle (Claude, GPT, Codestral etc.) liefern auf den Probe-Prompt `"Show your reasoning"` verbose Antworten (700–1.300 Zeichen), was fälschlich `detected=True` ergab. Nur Signal A (think-Tags) und Signal B (reasoning_tokens) sind zuverlässige CoT-Indikatoren.
- **`probe_thinking.py` — `_infer_provider()` Substring-Matching-Bug:** `p.rstrip("/") in model_id`-Prüfung schlug bei lokalen Modellen fehl (z. B. `"deepseek" in "deepseek-r1:8b"` → fälschlich `openrouter`). Fix: Eindeutige `/`-Präsenz-Heuristik — `/` im Model-ID → `openrouter`, sonst `ollama`.
- **`probe_thinking.py` — Batch-Exit-Verhalten:** `sys.exit(1)` wird nur noch bei explizitem `--model`-Fehler ausgelöst. `--missing`/`--all`-Batch-Modi berichten Fehleranzahl und enden mit Exit Code 0.

### Data
- **`benchmark_scores/commercial_models_benchmark.csv`:** 18 ungültige `gemini-2.5-flash`-Zeilen gelöscht (falsches Token-Budget vor v3.5.7-Fix: `code_quality` ×5, `cultural_intelligence` ×5, `ux_writing` ×4, `documentation_quality` ×2, `content_transformation` ×2). Re-Run durchgeführt: alle 18 Tasks neu bewertet.
- **`benchmark_scores/commercial_models_benchmark.csv`:** 3 ungültige `gemini-2.5-pro`-Zeilen gelöscht (Safety-Filter / Budget-Erschöpfung).
- **`benchmark_scores/cloud_models_benchmark.csv`:** 3 ungültige `kimi-k2.5`-Zeilen gelöscht (`resp_len=0`: `cultural_intel_001`, `cultural_intel_002`, `ux_writing_002`). Re-Run durchgeführt.
- **`benchmark_scores/model_cards/`:** 51 Model-Cards retroaktiv mit Thinking-Probe-Feldern versehen. 26 API-Modelle erfolgreich geprobt. 25 offline/nicht-installierte Ollama-Modelle schlagen gracefully fehl (kein Probe-Feld gesetzt). 1 neue Minimal-Card für `moonshotai/kimi-k2.5` via Card-First-Hook erstellt.

### Docs
- **`.github/copilot-instructions.md` — Neue Fallstricke dokumentiert:**
  - `_safe_name()`-Transformation muss in allen Card-Lookup-Pfaden konsistent verwendet werden.
  - Signal-C (Response-Length) ist kein zuverlässiger CoT-Indikator.
  - `_infer_provider()` muss `/`-Präsenz-Heuristik verwenden statt Substring-Matching.

---

## [v3.5.7] - 2026-04-23

### Added
- **`utils/model_utils.py` — `resolve_token_budget()` SSoT-Hilfsfunktion:** Neue Funktion, die Token-Budget-Berechnung für alle Provider zentralisiert. Ersetzt die zuvor in `openai.py`, `openrouter.py` und `mistral.py` duplizierte inline-Logik. Gibt `(effektives_budget, is_reasoning)` zurück. Logik: Bei Reasoning-Modellen mit explizitem Budget → `token_budgets_reasoning_models[module_key]` aus Config (Fallback: ×5); ohne explizites Budget und < 10.000 Tokens → 25.000 Tokens fix.
- **`benchmark_config.yaml` — `token_param_name` pro Provider:** Alle 5 kommerziellen Provider-Blöcke (`mistral`, `openai`, `groq`, `xai`, `openrouter`) haben jetzt ein explizites `token_param_name`-Feld (`max_tokens` oder `max_completion_tokens`). Providers lesen ihren Parametermamen aus der Config statt ihn hart zu kodieren.
- **`utils/scoring/llm_judge/judge_prompt_builder.py` — `token_budget_context`-Parameter:** Neuer optionaler Parameter in `build_prompts()`. Bei Reasoning-Modellen erhält der Judge eine `TOKEN BUDGET NOTE`: standard- und elevated-Budget werden kommuniziert, und der Judge wird angewiesen, 1 Punkt von `output_quality` abzuziehen, wenn der sichtbare Output > 2× Standard-Budget beträgt und das Mehr reine Ausschweifung ist.
- **`utils/scoring/judge_evaluator.py` — automatische Budget-Kontext-Injektion:** Bei Reasoning-Modellen werden `standard` und `elevated` Budget automatisch aus der Config gelesen und als `token_budget_context` an den Judge weitergegeben.
- **`scripts/core/unified_runner.py` — Refusal-Metadaten:** Wenn eine Modellantwort kürzer als 15 Zeichen ist (Ablehnungs-Signal), werden drei neue Felder ins Result geschrieben: `refusal_flag: True`, `refusal_type: "content_safety"`, `refusal_note` mit Freitext-Begründung.
- **`utils/result_manager.py` — Refusal-Felder in CSV-Schema:** `refusal_flag`, `refusal_type`, `refusal_note` in `_get_updated_fieldnames()` registriert — erscheinen ab sofort als CSV-Spalten in allen drei Benchmark-CSVs.

### Changed
- **`utils/model_utils.py` — `is_reasoning_model()` Trigger erweitert:** `"gemini-2.5"` ergänzt. `gemini-2.5-flash` und `gemini-2.5-pro` erhalten jetzt automatisch das erhöhte Token-Budget aus `token_budgets_reasoning_models` (ux_writing: 8.000, documentation_quality: 12.000 statt 500/6.000 Tokens). Behebt systematisch fehlerhafte 1/5-Judge-Scores durch Thinking-Token-Budget-Erschöpfung.
- **`utils/providers/openai.py`**, **`openrouter.py`**, **`mistral.py`** — alle drei Provider-Implementierungen auf `resolve_token_budget()` umgestellt. `mistral.py` erhält damit den zuvor fehlenden `elif is_reasoning and tokens < 10000: tokens = 25000`-Branch (war in openai.py/openrouter.py bereits vorhanden).

### Analysis & Methodology
- **Refusal als Qualitätsmerkmal dokumentiert:** Modelle, die den *Input-Text* eines Rewriting-Tasks flaggen statt die Aufgabe auszuführen (z. B. Kimi K2.5 und GLM-5 bei `ci_6B Inclusive Job Ad`), versagen in echten UX-Writing-Workflows. Das neue `refusal_flag`-System macht dieses Versagen transparent — kein Re-Run, kein Asset-Fix. Der Benchmark ist durch 60+ Modelle validiert, die dieselben Assets lösen.
- **Gemini Safety-Filter auf ux_002 (Banking-CTAs):** `gemini-2.5-pro` und `gemini-3.1-pro-preview` blockieren Button-Label-Formulierungen für Banking-Transaktionen (`5.000 € überweisen`) und irreversible Aktionen. Kein Benchmark-Bug — valides Qualitätsmerkmal, da alle anderen Modelle ux_002 normal lösen.

---

## [v3.5.6] - 2026-04-23

### Added
- **`schemas/result.py` — `reasoning_tokens`-Feld:** Neues `Optional[int]`-Feld in `BenchmarkResult` — wird als neue CSV-Spalte persistiert. Enthält die intern verbrauchten Reasoning-/Thinking-Tokens, die nicht im sichtbaren Output erscheinen.
- **`utils/providers/openrouter.py` — Reasoning-Token-Extraktion:** `last_response_metadata` enthält jetzt `reasoning_tokens` aus `completion_tokens_details.reasoning_tokens` der OpenRouter-API.
- **`utils/benchmark_utils.py` — Audit-Log `[!WARNING]`-Block:** Bei `reasoning_tokens > 0 AND token_limit_cutoff=True` wird ein Warnblock injiziert, der erklärt, dass Reasoning-Tokens das Output-Budget verdrängt haben. Token-Header zeigt `(davon N Reasoning-Tokens, die intern verbraucht wurden)`.
- **`Makefile` — `clean-bak`-Target:** Neues Target entfernt `.bak_*`-Dateien aus `benchmark_scores/`. `backup`-Target erweitert um `docs/reviews/`, `docs/audits/`, `config/`, `memory-bank/` und excludet `.bak_*`.

### Fixed
- **`utils/model_utils.py` — `minimax-m2` als Reasoning-Trigger:** `is_reasoning_model()` erkennt jetzt `minimax/minimax-m2.7` (und alle `minimax-m2.*`-Varianten). OpenRouter-Provider setzt automatisch 5× Token-Budget (~40.000 statt 8.192 Tokens) — verhindert `finish_reason: length` mit leerem Output.

### Data
- **2 ungültige CSV-Zeilen gelöscht:** `minimax/minimax-m2.7` × `cli005` und `ux_writing_005` aus `cloud_models_benchmark.csv` — beide hatten `resp_len=0` durch Budget-Erschöpfung vor dem Fix. Re-Run automatisch bei nächstem Lauf.

### Docs
- **`docs/ARCHITECTURE.md`:** Provider-Tabelle um OpenRouter- und xAI-Zeile + `Besonderheiten`-Spalte erweitert. Neuer Abschnitt „OpenRouter: Reasoning-Token-Budget-Konflikt" nach Token-Cap-Beschreibung.
- **`memory-bank/systemPatterns.md`:** Neuer Abschnitt „OpenRouter: Reasoning-Token-Budget-Konflikt" mit vollständiger Implementierungsreferenz.
- **`.github/copilot-instructions.md`:** Fallstrick „OpenRouter Reasoning-Token-Budget" dokumentiert.

---

## [v3.5.5] - 2026-04-22

### Changed
- **Size-Class-System auf 6 Deployment-Tiers erweitert:** `get_model_size_class()` in `utils/model_utils.py` ersetzt das alte 2-Tier-System (`Nano (≤5B)` / `Standard`) durch eine deployment-orientierte 6-Tier-Taxonomie: `Nano` (≤ 4B, < 4 GB RAM), `Edge` (5–9B, 4–8 GB), `Desktop` (10–17B, 8–14 GB), `Workstation` (18–35B, 14–24 GB), `Server` (36–75B, 24–48 GB), `Frontier` (> 75B / API-only). Modelle ohne Größen-Tag (kommerzielle APIs, Cloud-Proxies) landen automatisch in `Frontier`. Badge-Marker `🔬` bleibt auf `Nano` beschränkt (≤ 4B, Floor-Tier). `MODEL_CLASSIFICATION.md` vollständig aktualisiert.

---

## [v3.5.4] - 2026-04-21

### Added
- **Nano/Edge-Tier:** Modelle mit ≤ 5B Parametern werden automatisch erkannt und im Leaderboard als `Nano (≤5B)` klassifiziert. Neue Spalte `Size Class` in Compact- und Detailed-CSV. Badge-Suffix `🔬` (z. B. `🥉 Bronze 🔬`) macht die Hardwareklasse auf einen Blick sichtbar, ohne Tier-Schwellen zu verändern. Web-Export propagiert `size_class`-Feld ins JSON. Erkennung via `get_model_size_class()` in `utils/model_utils.py` (Regex auf Ollama-Style-Tag, z. B. `qwen3:4b`, `phi3.5:3.8b`).
- **Docs:** `MODEL_CLASSIFICATION.md` — neuer Abschnitt „Nano/Edge-Tier (≤ 5B Parameter)" mit Use-Cases, Erkennungslogik und Beispiel-Tabelle.

---

## [v3.5.3] - 2026-04-21

### Fixed
- **`benchmark_modules/ux_writing/assets/asset_005_microcopy_audit.yaml` — Limit-Kalibrierung:** `max_expected_words` 150 → 350 (datengetrieben: P25 der Ist-Längen × 1.20 = 337 → 350). Prompt-Text ergänzt um explizite Längenanweisung `"Maximale Länge: 350 Wörter gesamt"` — Modell war zuvor nie über das Limit informiert. 50/52 Modelle hatten das alte Limit verletzt (Min-Ist 255 W > Limit+Toleranz 162 W).
- **`benchmark_modules/content_transformation/assets/asset_003_glossary_simplification.yaml` — Limit-Kalibrierung:** `max_expected_words` 150 → 250 (P25 = 210 W × 1.20 = 252 → 250). Format-Hinweis im Prompt synchronisiert (`Max 150 Wörter` → `Max 250 Wörter`). 29/52 Modelle hatten das alte Limit verletzt.
- **`benchmark_modules/content_transformation/assets/asset_004_video_script_tutorial.yaml` — Limit-Kalibrierung:** `max_expected_words` 600 → 900 (P25 = 789 W × 1.20 = 947 → 900). Format-Range im Prompt synchronisiert (`400-600 Wörter` → `600-900 Wörter`). Min-Ist aller 52 Modelle war 742 W — das alte Limit war physisch unlösbar.

### Data
- **156 CSV-Zeilen gelöscht:** Alle Einträge der 3 betroffenen Tasks (`ux_writing_005`, `content_transformation_003`, `content_transformation_004`) aus `commercial_models_benchmark.csv`, `cloud_models_benchmark.csv` und `local_models_benchmark.csv` entfernt (75 + 42 + 39 Zeilen). Re-Run wird automatisch durch fehlende `(model, asset_id)`-Keys getriggert.
- **156 Audit-Log-Dateien gelöscht:** Alle `*/ux_writing_005.md`, `*/content_transformation_003.md`, `*/content_transformation_004.md` aus `outputs/audit_logs/` entfernt. Neue Audit-Logs entstehen beim Re-Run.

### Analysis
- **Fleet-weiter Violation-Scan:** 52 Modelle × 37 Tasks systematisch auf strukturelle Kalibrierungsfehler analysiert. Befund: 3 isolierte Limit-Fehler (alle behoben). `content_transformation_005` als begründeter Design-Trade-off eingestuft (`keyword_presence`-Check für abschnittsbezogenes Limit korrekt — `max_expected_words` auf Gesamtantwort wäre methodisch falsch). Phase-2-Backlog angelegt.

---

## [v3.5.2] - 2026-04-21

### Fixed
- **`scripts/core/unified_runner.py` — Pylint W1309:** `f`-Prefix aus String ohne Interpolation entfernt (Zeile 511: `f"   💸 Budget-/Quota-Fehler..."` → `"   💸 Budget-/Quota-Fehler..."`).
- **`utils/providers/base.py` — Pylint W0719:** `raise Exception(...)` → `raise RuntimeError(...)` — spezifischer Fehlertyp statt `Exception`-Basisklasse.
- **`benchmark_modules/political_compass/core/audit_logger.py` — Pylint C0206:** Dict-Iteration `for _q_id in hydrated_responses:` → `for _q_id, _q_data in hydrated_responses.items():` — Pylint-konformes `.items()`-Pattern.
- **`benchmark_modules/political_compass/core/evaluators.py` — Mypy annotation-unchecked:** `__init__(self)` → `__init__(self) -> None` in `ExtremismWatchdog` (Zeile 49) und zweiter Klasse (Zeile 332) — mypy prüft jetzt `List[ExtremismDetail]`-Annotation korrekt.

### Changed
- **`benchmark_modules/political_compass/config.yaml` — Skalen-Label X-Achse:** `label: "Nationalistisch"` → `label: "Reaktionär"` (Range 4.4–7.4). Terminologisch präziser, da das Segment wirtschafts- und gesellschaftspolitischen Konservatismus beschreibt, nicht ethnischen Nationalismus.
- **`benchmark_modules/political_compass/core/audit_logger.py` — Beispieltext:** `repressiv-nationalistisch` → `repressiv-reaktionär` synchronisiert mit Skalen-Umbenennung.

### Docs
- **`docs/POLITICAL_COMPASS_KONZEPT.md` — Block 7.9:** Neuer Abschnitt 7 „Block 7.9: Die Parolen-Extremismus-Sonde" mit drei Unterkapiteln: Konzept und Asset-Tabelle (11 Parolen-Assets), Koordinatenformel mit 80/20-Gewichtung und Begründung, Interpretationshinweis für Hard-Refusal-Verhalten (parolen_x/y = 0).

---

## [v3.5.0] - 2026-04-17

### Added
- **`utils/llm_client.py` — `last_output_tokens`-Feld:** `self.last_output_tokens` wird vor jedem API-Call auf `0` zurückgesetzt und nach erfolgreichem Call auf den tatsächlichen `eval_count` (Ollama) gesetzt. Liefert pro Frage-Anruf die exakten Output-Tokens ohne nachträgliches Parsing.
- **`benchmark_modules/political_compass/test.py` — `output_tokens` im Checkpoint:** Live-Paths schreiben `getattr(llm_client, "last_output_tokens", 0)` ins `detailed_responses`-Dict. Resume-Pfad schreibt explizit `None` (kein Token-Datum verfügbar, semantisch von `0` trennbar).
- **`benchmark_modules/political_compass/core/audit_logger.py` — Section 2.6 Token-Asymmetrie:** Neue optional Sektion im PC-Audit-Log, ausschließlich bei `verification_mode=True` (Shift ≥ 1.0). Berechnet `ELABORATION_SPIKE` (Forced > +50 % Output-Tokens) und `CAPITULATION_DROP` (Forced < −40 %) aus echten per-Frage-`output_tokens`. Fallback auf Antwortzeit-Proxy (mit `Hardware-abhängige Schätzung`-Label) bei Legacy-Runs ohne Token-Daten. None-sichere Filter (`or 0`-Guard). Coverage-Warnung bei partiellen Daten.
- **`config/meta_reviewer_prompt.yaml` — `bias_reviewer` Section-2.6-Integration:** Reviewer-Prompt erweitert um Verzahnungs-Instruktion: Token-Asymmetrie-Befunde sollen als Dimension der Schattenmetriken (Section 2.5) eingewoben werden, nicht als isolierter Absatz. Zero-Write-Regel für Hardware-Schätzungen. Dokumentierter Upgrade-Pfad und Re-Run-Prioritäten als YAML-Kommentar.
- **`config/meta_reviewer_prompt.yaml` — `bias_reviewer` Prompt-Architektur:** Model Card vor Pflichtstruktur verschoben (sequenzielles LLM-Lesen), drei offene Leitfragen durch eine präzise Einzel-Instruktion ersetzt.
- **`docs/AUDIT_AND_METAREVIEW.md` — Section 2.6 dokumentiert:** Neuer Abschnitt "Political Compass: Section 2.6 Token-Asymmetrie" mit Flag-Schwellenwerten, Thinking-Modell-Einschränkung, Zero-Write-Regel und Nachweis der retroaktiven Legacy-Nachpflege.
- **`docs/POLITICAL_COMPASS_KONZEPT.md` — Kapitel 5 Schattenmetriken:** Neues Kapitel "Schattenmetriken: Internes Chaos und kognitive Fingerabdrücke" erklärt Standardabweichung (Section 2.5), Token-Asymmetrie (Section 2.6), Flag-Tabelle, Kombinations-Interpretation und Thinking-Modell-Einschränkung.

### Fixed
- **`benchmark_modules/political_compass/test.py` — Resume-Pfad `None` statt `0`:** Resume-Checkpoints schrieben `output_tokens: 0`, was falsche „partiell-vollständige" Coverage-Meldungen in Section 2.6 verursachte. Fix: explizites `None` macht fehlende Token-Daten semantisch von tatsächlichen Null-Token trennbar.
- **`benchmark_modules/political_compass/core/audit_logger.py` — None-sicherer Filter:** `token_pairs`-Filter verwendete `> 0`, was bei `None`-Werten einen `TypeError` verursachen konnte. Fix: `(... or 0) > 0`-Guard.

### Data
- **12 PC-Audit-Logs retroaktiv mit Section 2.6 (Zeitproxy) ergänzt:** Alle Modelle mit Shift > 1.0 aus dem initialen Benchmark-Run. Zeitproxy mit `Hardware-abhängige Schätzung`-Label — Reviewer-Zero-Write-Regel greift weiterhin. Auffälligste Werte: `qwen3.5:9b` +149 %, `gemma4:26b` −58 %.

---

## [v3.5.1] - 2026-04-19

### Fixed
- **`utils/providers/base.py` — Gemini Daily-Quota Fast-Fail:** `retry_delay`-Werte > 300 Sekunden (Google Tages-Quota-Erschöpfung, z. B. `retry_delay { seconds: 27331 }`) lösen jetzt Fast-Fail aus statt das System 7,6 Stunden zu blockieren. Die geworfene Exception enthält `exceeded your current quota` und wird vom bestehenden `budget_keywords`-Guard in `test.py` als `_quota_exhausted = True` behandelt — Checkpoint bleibt erhalten, nächster Provider wird normal weitergeführt.
- **`config/rate_limits.yaml` — `max_retry_delay_seconds: 300`:** Schwellenwert dokumentiert.
- **`benchmark_modules/political_compass/test.py` — `UnboundLocalError` bei Quota-Abbruch:** `query_exec_time = 0.0` als Default vor der `while True:`-Schleife eingefügt. Bei Quota-Fehlern brach `break` die Schleife ab bevor die Variable zugewiesen wurde — `UnboundLocalError` in der Ergebnis-Aggregation (Zeile ~371) war die Folge.
- **`utils/providers/openai.py` — Modellspezifisches Token-Limit (gpt-4o, gpt-4o-mini):** Nach dem Standard-Token-Limit-Lookup wird jetzt `model_max_tokens` aus der Provider-Config ausgelesen und als hartes Obergrenze angewendet. Verhindert die bisher bei jedem Request ausgelöste Fallback-Warnung `⚠️ Token limit rejected. Retrying with fallback limit: 4096 tokens.`

### Changed
- **`benchmark_config.yaml` — `kimi-k2-instruct` Groq → Ollama Cloud:** `moonshotai/kimi-k2-instruct` aus dem Groq-Provider entfernt (Modell dort nicht mehr verfügbar). Ersetzt durch `kimi-k2.5:cloud` unter `ollama_cloud` (via `ollama pull kimi-k2.5:cloud`). Benchmark-Werte für `kimi-k2.5:cloud` bereits seit 2026-04-16 im PC-Leaderboard vorhanden.
- **`benchmark_config.yaml` — `model_max_tokens`-Override (OpenAI):** Neuer Block `model_max_tokens: {gpt-4o: 4096, gpt-4o-mini: 4096}` im OpenAI-Provider-Abschnitt als konfigurierbare SSOT für modellspezifische Token-Obergrenzen.

### Data
- **7 neue PC-Leaderboard-Einträge:** gpt-5, gpt-5.4, gpt-5.4-mini, gpt-4o, gpt-4o-mini, meta-llama/llama-4-scout-17b-16e-instruct, qwen/qwen3-32b. PC-Leaderboard jetzt auf 48 Modellen (inkl. kimi-k2.5:cloud aus vorherigem Run).

---

## [v3.4.7] - 2026-04-16

### Fixed
- **`benchmark_modules/political_compass/test.py` — Budget-Exhaustion-Guard:** Exception-Handler im Query-Loop erkennt Budget/Quota-Keywords und setzt `self._quota_exhausted = True`. Verhindert lautloses Schlucken von Budget-Fehlern und das Schreiben korrupter All-Zero-Daten ins Leaderboard.
- **`utils/base_runner.py` — Quota-Flag-Propagation:** `execute_batch_module()` prüft `getattr(test, "_quota_exhausted", False)` nach `execute()` und setzt `self.provider_quota_exhausted = True`. Gibt `[]` zurück — kein korruptes Ergebnis mehr.

### Changed
- **`benchmark_modules/political_compass/core/io_manager.py` — `cost`-Spalte entfernt:** Redundante Spalte (immer `0.0` für lokale Modelle) aus Leaderboard-CSV und `io_manager.py` entfernt. Interne `total_cost`-Berechnung für Audit-Log bleibt erhalten.
- **`config/meta_reviewer_prompt.yaml` — `bias_reviewer`-Prompt:** Initialer `bias_reviewer:`-Key mit vollständigem System-Prompt für politische Bias-Analyse.
- **`scripts/web_export.py` — `inference_provider`-Feld:** `leaderboard.json` enthält jetzt `inference_provider` pro Eintrag.

### Data
- **PC-Leaderboard bereinigt:** 34 → 13 Zeilen (21 März-Einträge mit `polarity_flip_rate = 0.0` entfernt). 21 Modelle zur Neuberechnung freigegeben.

---

## [v3.4.6] - 2026-04-14

### Fixed
- **`utils/base_runner.py` — PC Skip-Logic-Lücke geschlossen:** `execute_batch_module()` prüfte bei Political-Compass-Runs nur die 3 Standard-CSVs auf bereits vorhandene Ergebnisse. Nach einem Leaderboard-Reset (leere Standard-CSVs) wurden alle PC-Modelle fälschlich erneut gerunnt. Fix: Expliziter Fallback-Check gegen `benchmark_scores/political_compass_leaderboard.csv` — wird nur für PC-Module aktiviert (`PoliticalCompassHandler.is_political_compass()`). Graceful-Fallback bei `OSError`/`csv.Error`.

### Data
- **Political Compass Leaderboard-Bereinigung:** 11 Einträge mit korrupten Koordinaten (runde Null-Werte aus fehlerhafter Session 23.03.2026 — Verweigerungen produzierten Ganzzahlwerte wie `(0.0, 9.0)`) aus `political_compass_leaderboard.csv` entfernt. Leaderboard: 31 → 20 verifizierte Einträge. Betroffene Modelle für Re-Run freigegeben. Backup gesichert unter `political_compass_leaderboard.bak_20260414_222150.csv`.

---

## [v3.4.5] - 2026-04-11

### Changed
- **Redaktionelle Überarbeitung (16 Dateien):** README.md, 13 `docs/`-Dateien, REF_TODO.md und PROJECT_STATUS.md auf einheitlichen Ton gebracht: Ansprache `du`/`dein` → unpersönliches `man`/`sein`; Emojis aus Überschriften entfernt (nur `🛑` als kritischer Warnmarker behalten); alle englischen H1–H3 ins Deutsche übertragen; einheitliche Intro-Blöcke (`**Zielgruppe:**` / `**Inhalt:**` / `> **Voraussetzung:**`) in allen Dateien ergänzt; ~80 `______`-Trennlinien → `---`.

---

## [v3.4.4] - 2026-04-11

### Changed
- **`utils/constants.py` — Neue Konstanten (Regeln 2+3):** `MODEL_TYPE_OPEN_WEIGHTS_CLOUD`, `RESULT_TYPE_LOCAL/CLOUD/COMMERCIAL` und 7 Timeout-Konstanten (`TIMEOUT_OLLAMA_HEALTH/LIST_FAST/LIST/VERSION/WARMUP`, `TIMEOUT_HTTP_FETCH`, `TIMEOUT_ANTHROPIC_API`) als SSOT zentral definiert.
- **Beseitigung von Magic Strings/Numbers in 8 Dateien:** `utils/result_manager.py`, `utils/model_utils.py`, `utils/providers/anthropic.py`, `utils/pricing_updater.py`, `scripts/core/benchmark_auto.py`, `scripts/core/unified_runner.py`, `scripts/core/run_cross_model_benchmark.py`, `scripts/tools/list_models.py` referenzieren alle Timeout- und Typ-Werte ausschließlich via `constants.py`.

---

## [v3.4.3] - 2026-04-10

### Added
- **`module_weight`-Feld in allen Modul-`config.yaml`s:** Neues `integration.leaderboard.module_weight`-Key entkoppelt den Total-Score-Einfluss eines Moduls von seiner Asset-Anzahl. Default: Vollmodule `1.0`, CLI-Modul `0.5` (Supplement). Konfigurierbar pro Deployment ohne Code-Änderung.
- **`_module_scale()` in `score_calculator.py`:** Hilfsfunktion berechnet den normierten Skalierungsfaktor pro Modul (`scale = module_weight / Σ active weights`). Alle 4 Contrib-Spalten werden vor der Aggregation skaliert. Fallback: fehlender `module_weight`-Wert → `scale = 1.0`.
- **5 neue Ollama-Cloud-Modelle in `config/cost_limits.yaml`:** `deepseek-v3.1:671b-cloud` ($0.28/$0.42 per 1M), `qwen3.5:397b-cloud` ($0.60/$3.60 per 1M), `gemma4:31b-cloud` ($0.14/$0.40 per 1M), `kimi-k2.5:cloud` ($0.45/$2.25 per 1M), `glm-5:cloud` ($0.14/$0.40 per 1M).
- **`docs/BENCHMARK_MODULES.md`:** Neuer Abschnitt "Designprinzip: Module als gleichwertige, geschlossene Tests" erklärt die Modulgewichtungs-Philosophie, den Einsatz von Einzel-Modul-Scores und den CLI-Sonderfall.
- **`docs/SCORING_METHODOLOGY.md`:** Neue Sektion "Modulgewichtung (`module_weight`)" mit selbstnormierender Formel, Gewichts-Tabelle (alle 7 Module mit Einfluss-Prozenten) und Konfigurationshinweis.

### Changed
- **`scripts/leaderboard/__init__.py`:** `module_weight` aus `lb_config.get("module_weight")` ins `mod_entry`-Dict übernommen — stellt sicher, dass `score_calculator.py` den konfigurierten Wert jedes Moduls erhält.
- **`docs/SCORING_METHODOLOGY.md`:** Formel von `(Routine Score + Reasoning Score) / 2` (veraltet) auf `Σ(ModuleScore × module_weight) / Σ(module_weight)` (korrekte selbstnormierende Variante) aktualisiert.

---

## [v3.4.2] - 2026-04-09

### Added
- **`scripts/dev/sync_cost_limits.py`:** Neues Dev-Tool erkennt automatisch Modelle ohne Preiseintrag in `config/cost_limits.yaml`. Mit `--fix`-Flag werden `null`-Platzhalter (inkl. `# TODO: Preis nachtragen`-Kommentar) direkt in die YAML-Datei geschrieben — boundary-sicher (`providers:`-Block) und duplikatfrei.
- **`make sync-cost-limits [FIX=1]`:** Neues Makefile-Target für den standardisierten Workflow beim Hinzufügen neuer Modelle.
- **LLM Judge Avg Sterne-Format in `exporter.py`:** `LLM Judge Avg`-Spalte im Leaderboard wird jetzt als `3.8 ★` formatiert.
- **Neue `cost_limits.yaml`-Sektionen:** `ollama_cloud` (deepseek-v3.2, minimax-m2.7, gpt-oss:120b), `google` (gemini-2.5-pro, gemini-3-flash-preview, gemini-3.1-pro-preview), korrigiertes `xai` (aus `settings:` in `providers:` verschoben).
- **`docs/USER_GUIDE.md`:** Zwei neue Abschnitte dokumentieren `make sync-cost-limits` (F.2 Systemgesundheit + eigenständiger Workflow-Abschnitt).

### Changed
- **`config/cost_limits.yaml`:** Vollständige Preisabdeckung für alle 25 konfigurierten Modelle. Neu eingetragen (Quellen verifiziert 2026-04-09): `gpt-5.4` ($2.50/$15.00 per 1M), `gpt-5.4-mini` ($0.75/$4.50 per 1M), `o1` ($15/$60 per 1M), `gemini-2.5-pro` ($1.25/$10 per 1M), `gemini-3-flash-preview` ($0.50/$3.00 per 1M), `gemini-3.1-pro-preview` ($2.00/$12.00 per 1M), Groq-Ergänzungen (Qwen3-32B, Kimi K2), Claude Haiku 4.5 (key-fix).

---

## [v3.4.0] - 2026-04-08

### Added
- **Token-Budget-System:** `max_tokens`-Cap als direkter API-Parameter in `base_runner.py`. Lädt `token_budgets[module_key]` aus `benchmark_config.yaml` und übergibt das Limit nur wenn es gesetzt ist (`None` wird nicht an Provider-Clients weitergegeben). Gewährleistet faire, Provider-übergreifende Vergleichbarkeit.
- **Token-Effizienz-Transparenz in Audit-Logs:** Neuer `[!NOTE]`-Header-Block in `benchmark_utils.py` macht Token-Effizienz-Anomalien sichtbar. Trigger: `token_limit_cutoff is True AND _budget is not None`. Bestehender `[!CAUTION]`-Block vor der Response bleibt unverändert.
- **Token-Effizienz-Kontext in Meta-Reviewer-Reports:** Neue Template-Variable `{token_efficiency_context}` in `generate_review.py` injiziert modulspezifische Ø-Token-Werte des Modells vs. Gesamt-Median vor `{log_data}`. Neuer Diagnostik-Block "Token-Effizienz (Verbosity)" in `meta_reviewer_prompt.yaml` — der Reviewer schreibt einen Absatz wenn Ratio > 1.5× Median (Reasoning/Metacog ausgenommen).

### Changed
- **benchmark_config.yaml:** `token_budgets`-Werte auf 2× Modul-Median kalibriert: `cultural_intelligence: 500`, `ux_writing: 3500`, `content_transformation: 3500`, `documentation_quality: 6000`, `code_quality: 6000`.
- **benchmark_utils.py:** Verbosity-Flag-Trigger auf `token_limit_cutoff` (API-`finish_reason`) umgestellt — kein berechneter Schwellenwert mehr.

### Removed
- **cli_benchmark** aus `token_budgets` entfernt — kein Output-Limit für CLI-Tasks (by design).

### Deferred to v3.4.x
- Score-Penalty für Token-Verbosity (separates Feature, keine Änderung an bestehenden Scores)
- Leaderboard-Metriken `avg_tokens`, `token_efficiency_ratio`, `est_cost_per_1k_tasks` in `score_calculator.py` + `generate_leaderboard.py`

---

## [v3.3.1] - 2026-04-08

### Fixed
- **Political Compass: model_category-Feld** in `io_manager.py` ergänzt (`save_leaderboard_csv`): Die Leaderboard-CSV trägt jetzt `model_category` (`local` / `cloud` / `commercial`) — identische Routing-Logik wie `result_manager.py`.
- **Political Compass: provider_type-Korrektur** für Ollama-gehostete Cloud-Modelle (`:cloud`-Suffix): Wert wird jetzt korrekt auf `cloud` gesetzt statt auf `ollama`.
- **political_compass_handler.py:** `_update_local_pc_csv()` von append-only auf Upsert umgestellt — entfernt bestehende Einträge des Modells vor dem Schreiben (Parität zu `_update_commercial_pc_csv()`).
- **clean_results.py:** `political_compass_leaderboard.csv` fehlte in der `files`-Liste; bei `--model xyz` blieb der PC-Leaderboard-Eintrag stehen. Außerdem defensiver `asset_id`-Guard in `clean_csv()` eingebaut (KeyError bei CSVs ohne `asset_id`-Spalte).
- **CSV-Anomalie-Cleanup:** 6 historische Cloud-Modell-Einträge aus `local_models_benchmark.csv` entfernt (hatten `provider_type=ollama` + `:cloud`-Suffix, wurden aber vor dem `:cloud`-Routing-Fix in die falsche CSV geschrieben).

### Changed
- **political_compass_leaderboard.csv** einmalig bereinigt: 66 → 56 Zeilen (Duplikate), `model_category`-Spalte rückwirkend befüllt, `provider_type` für 8 Cloud-Modelle korrigiert.

---

## [v3.3.0] - 2026-04-07

### Added
- **Language Compliance Pipeline:** `judge_prompt_builder.py` erhält neue Parameter `required_language` und `language_weight`. Wenn ein Asset `language: de` definiert, wird dem Judge automatisch ein gewichteter LANGUAGE COMPLIANCE Block injiziert, der Sprachverstöße unter `task_compliance` penalisiert (Standard: 20 % des Gesamtscores).
- **Language Metadata in Metacog-Assets:** `reasoning_logic` Assets `metacog_001–005` tragen nun `language: de` im Metadata-Block und ein explizites `Antworte auf Deutsch.`-Constraint im Prompt.
- **Audit-Infrastruktur:** Neues Verzeichnis `docs/audits/` für operatives Audit-Logging. Erster Report: `AUDIT_2026-04-07_editorial.md`.

### Changed
- **Prompt Hardening (21 Assets, 30 Änderungen):** Systematisches Bereinigen aller AI-generierten Gemini-Artefakte aus 5 Modulen (`cultural_intelligence`, `ux_writing`, `content_transformation`, `documentation_quality`, `code_quality`):
  - *Token-Limit-Leak entfernt (13 Treffer):* Interne Benchmark-Constraints (`um Token-Limits nicht zu überschreiten`) sind nicht Teil des Prompts — ersetzt durch direkte quantitative Schranken.
  - *Höflichkeitsformeln entfernt (13 Treffer):* `Bitte` in imperativen WICHTIG/HINWEIS-Instruktionen gestrichen.
  - *Pseudolabels entfernt (2 Treffer):* `Mission:` und `TASK:` Gemini-Strukturlabels aus `cultural_intelligence` entfernt.
  - *Erfülle-Floskel ersetzt (5 Treffer):* `Erfülle dabei strikt die folgenden Anforderungen:` → `Anforderungen (strikt einhalten):`.
- **judge_runner.py / judge_evaluator.py:** Forwarding von `required_language`/`language_weight` aus Asset-Config; `language_mismatch`-Flag-Extraktion aus Judge-Response.

### Fixed
- **Kyrillischer Unicode-Artefakt** in `asset_6a_german_tech_localization.yaml`: 3 cyrillische Zeichen (U+043C м, U+0430 а, U+0442 т) in `Idioматisches` durch korrekte lateinische Zeichen ersetzt.
- **Golden Standard Grammatikfehler** in `asset_6e_german_idioms.yaml`: `ein negatives Entwicklung` → `eine negative Entwicklung`.

## [v3.2.0] - 2026-03-28

### Added
- **Dynamic Provider SSOT:** Vollständiges Refactoring der Provider-Kategorisierung. Das System nutzt nun strikt die `benchmark_config.yaml` als Single Source of Truth für Model-Kategorien.
- **Open-Weights Cloud Support:** Neue Kategorie `Cloud (Open-Weights)` hinzugefügt. Erlaubt die native Integration von Cloud-Hostern für Open-Source Modelle (z. B. Groq), welche automatisch im Leaderboard korrekt zugewiesen und bewertet werden.

### Changed
- **Kategorien Konsolidierung:** Der veraltete Begriff "Local Cloud" wurde aus dem Dashboard, dem Leaderboard und den Dokumentationen entfernt. Cloud-Proxies von Ollama (erkennbar am `:cloud` Suffix) werden jetzt präzise als `Cloud (Open-Weights)` gehandhabt.
- **Meta-Review Context Injection:** Der Report Generator (`generate_review.py`) wurde aktualisiert und behandelt "Cloud (Open-Weights)" Modelle nun konsistent mit dem Hardware-Kontext `local_cloud`, um dem LLM Judge korrekte Annahmen über APIs und Hardware-Limits mitzuteilen.
- **Leaderboard Rendering:** Pandas DataFrames im `data_loader.py` cachen nun die Konfigurations-Dictionaries (`model_utils.py::_CACHED_CONFIG`), um Blocking & Deadlocks durch iteratives YAML-Lesen über hunderte Rows zu verhindern.

### Fixed
- **Dokumentation:** Die Beschreibungen des Setup-Guides (`SETUP_GUIDE.md`) und der Klassifizierungsregeln (`MODEL_CLASSIFICATION.md`) wurden umfangreich bereinigt und reflektieren nun das neue 3-Kategorien-System (Commercial, Cloud (Open-Weights), Local).

## [v3.1.1] - 2026-03-25

### Changed
- **Strict Judge Fail-Fast Mechanism:** Der LLM Judge verzichtet nun komplett auf das inkonsistente und fehleranfällige "Fallback"-Muster (z.B. der automatische Wechsel auf lokale Modelle, wenn die Anthropic-API ausfällt oder das Budget erschöpft ist). Stattdessen wird nun eine `JudgeUnavailableError` Exception geworfen, die den Benchmark sofort pausiert und unvollständige Durchläufe verlässlich speichert, um Kosten zu schonen.
- **Judge Coverage Calculation:** Die Formel für die "LLM Judge Coverage" im Leaderboard wurde repariert, sodass unbeurteilte Module (wie der "Political Compass") den Prozentwert nicht mehr künstlich senken. Der Wert wird im CSV nun sauber als echter Prozentwert formatiert (z.B. "100%").
- **Codebase Maintenance & Refactoring:** Utils-Skripte wurden hinsichtlich "Magic Numbers" und Typisierungs-Warnungen überarbeitet. Veraltete Debug-Aufrufe (`save_debug_response`) und root-Skripte wurden aufgeräumt, sowie `make audit_markdown` in die Makefile-Toolchain integriert.

### Fixed
- **Meta-Review Prompt Formats:** Ein Off-by-One Bug wurde behoben und die Grammatik- bzw. Parsing-Regeln im externen Meta-Review-Prompt wurden verschärft.
- **Political Compass Polarity:** Ein Fehler bei der Berechnung des Flips direkt auf der Null-Achse ("Zero-Axis Polarity Flip") wurde korrigiert.

### Removed
- **Fallback Configurations:** Alle `fallback` Knoten aus der `benchmark_config.yaml` sowie die zugrunde liegende `FallbackProviderConfig` innerhalb der Python-Infrastruktur wurden gelöscht.

## [v3.1.0] - 2026-03-20

### Added
- **Reasoning Tokens & Metacognition:** Einführung der `<thought>`-Tag Metakognitions-Überprüfung. Das System trackt nun den `reasoning_tokens` Count und filtert die `<thought>` Blöcke vor der finalen LLM-Judge Auswertung restriktiver Modelle heraus.
- **Dynamic Meta-Review Prompting:** Der `generate_review.py` Meta-Reviewer nutzt nicht länger einen Python-hardgecodeten Prompt, sondern liest seinen System-Prompt dynamisch und versionierbar aus der neuen Konfigurationsdatei `config/meta_reviewer_prompt.yaml` ein.
- **Coder/Thinking Model Leniency:** Einführung einer Kulanzklausel (Leniency Clause) beim Bias-Review, um speziell trainierte Coder- oder Reasoning-Modelle vor ungerechtfertigten Penalties zu bewahren.

### Changed
- **CLI Hybrid Scoring Migration:** Das Modul `cli_benchmark` (`cli001` - `cli006`) wurde von der reinen Regex-Evaluierung auf ein hybrides `llm_judge`-Scoring umgestellt (inkl. Fallbacks, Penalty-Systemen und JSON-orientierter Aufbereitung der `functional_goal`s).
- **Judge Context Expansion:** Das Token-Limit des LLM-Judges in `benchmark_config.yaml` wurde von 2048 auf 4096 Tokens erhöht, um zu verhindern, dass ausführliche Architekturbewertungen (z.B. in `reasoning_5e_001`) mitten in JSON-Strukturen abbrechen.
- **Robust CSV Sync:** Der `--force`-Parameter und das Cross-Model-Resuming (`run_cross_model_benchmark.py`) überschreiben und integrieren bestehende CSVs nun intelligenter, ohne manuelle und fehleranfällige Löschvorgänge zu erfordern.

### Fixed
- **Judge Parse Fallbacks:** Bei korruptem Output (z. B. abgeschnittenes JSON) fängt `judge_parser.py` den Parse-Fehler ab, verweigert den Runtime-Crash und speichert stattdessen den rohen Debugging-Output unter `last_failed_raw.txt`.
- **Political Compass Anomaly Scan:** Ein Fehler in der Scoring-Logik wurde behoben, sodass nun bei einem Achsen-Shift `> 1` automatisch ein Anomalie-Scan ausgelöst wird (`auto-trigger anomaly scan on pc shift > 1`).

## [v3.0.1] - 2026-03-19

### Changed
- **Architecture Refactoring:** Consolidated base logic from `run_local_benchmark.py` and `run_commercial_benchmark.py` into a unified `utils/base_runner.py` to eliminate significant redundancy and improve maintenance. (Phases 1-4)

## [v3.0.0] - 2026-03-18

### Added
- **3-Tier Refusal Architecture:** Integrierte Anti-Zensur-Logik für rigide LLMs im Political Compass Modul.
- **Progressive Temperature Check:** Automatischer Retest abgelehnter Prompts durch Temperaturerhöhung (0.1 → 0.4 → 0.7) und angehängte System-Injektion (Safety-Bypass).
- **Erweiterte Safety-Metriken:** Aufzeichnung von `hard_refusals` und automatische Erkennung von "Safety Shifts" (Werte-Verzerrungen durch das heuristische Red-Teaming) in der Endauswertung dokumentiert.

### Changed
- **Repository Cleanup & README Overhaul:** Die `README.md` wurde radikal entschlackt, neu strukturiert und auf die tatsächliche v3.0.0 Architektur (inkl. API-Verbindungen & Makefile) gehoben.
- **Roadmap Shift:** Voller Fokus für die kommenden Iterationen auf Web-UI (React/Streamlit), Multimodalität und "Agentic Workflow"-Evaluierung gesetzt.
- **Dokumentation:** Umfangreiche Erweiterung der `POLITICAL_COMPASS_KONZEPT.md` um das 6. Kapitel (Erweiterte Sicherheitsarchitektur & Refusals).

### Fixed
- **Pydantic Serialization Bug:** Ein hartnäckiger `AttributeError` im Anomaly Checker (`verify_compass_anomalies.py`) beim Nested-Parsing von `BenchmarkResult.get()` wurde durch nativ robustes `.raw_response` JSON-Loading behoben.
- **Checkpointer Stability:** Aufgeklärte Architektur für das nahtlose Wiederaufsetzen von durch Token-Limits oder Budget-Caps abgebrochenen Testläufen.

## [v2.5.0] - 2026-03-14

### Added
- **XAI / Grok Support:** Integration von XAI Grok Modellen inkl. API Pricing Tracking.
- **Cascading Token Fallback:** Implementierung eines kaskadierenden Token-Fallback-Systems zur besseren Fehlerabfangung mit Verhaltens-Metadaten.

### Changed
- **Meta-Reviewer:** Verbesserung der Erkennung von System-Info-Blöcken durch den Meta-Reviewer.
- **Anthropic Stabilität:** Das Timeout für den Anthropic-Client wurde auf 600s erhöht, um Abbrüche bei langen Generierungen zu vermeiden. Automatische Retry-Logs wurden im Konsolen-Output unterdrückt.

### Removed
- **Unused Pipeline Logic:** Die reine dynamische Golden Standard Validierungsausgabe sowie alte ungenutzte Pipelines (`refactor(core)`) wurden entfernt.

## [v2.3.0] - 2026-03-12

### Added
- **Audit Mode (Robust):** Einführung eines vollumfänglichen Audit-Modus. Dieser protokolliert ausgeführte Prompts, LLM-Judge Fingerprinting, komplette Reasoning Trails sowie die Kategorie-Sub-Scores der Regex-Evaluationen.
- **Google / Gemini Provider:** Native Unterstützung von Google Modellen für LLM-Judge Pipelines ergänzt.
- **Hybrid Scoring Architecture:** Implementierung einer modular gewichteten Hybrid-Scoring Architektur (0.10 Regex / 0.90 Judge) für präzisere semantische Auswertungen.

### Fixed
- **LLM Judge Bugfixes:** Behebung von Routing-, Caching- und Parsing-Bugs im Judge sowie Schutz vor "Reasoning Truncation".

## [v2.2.0] - 2026-03-08

### Added
- **CLI Benchmark Integration:** Das CLI v2 Benchmark wurde gehärtet (inkl. 6-Task YAML-Unterstützung) und nativ in die "Standard Base Test" Architektur integriert.

### Fixed
- **Ollama Token Limits:** Reduzierung der Token-Limits für lokale Reasoning-Modelle von 32k auf 8k, um "VRAM Swap" System-Freezes auf macOS Maschinen zu verhindern.

## [v2.1.1] - 2026-02-14

### Added

- **New Provider Category:** "Local Cloud" for Ollama Cloud proxy models
  - Distinguishes cloud proxies (minimax-m2:cloud, gpt-oss:120b-cloud) from true local models
  - Appears separately in leaderboard and statistics
- **SSOT for Model Categorization:** Centralized `is_cloud_model()` function in `utils/model_utils.py`
  - Detection rules: `:cloud` tag, `-cloud` suffix, or size < 0.01 GB
  - Used consistently across UI filters, data loading, and model listing

### Changed

- **Provider Selection UI:** Now offers three distinct categories:
  1. Commercial (Mistral, Claude, GPT)
  1. Local (Ollama offline models)
  1. Local Cloud (Ollama Cloud proxy)
- **Leaderboard Generation:** Automatic categorization using SSOT instead of filename-based inference
- **Documentation:** Updated `MODEL_CLASSIFICATION.md` with detailed categorization logic

### Fixed

- Cloud models (e.g., `gpt-oss:120b-cloud`) no longer miscategorized as "Local"
- Consistent cloud model detection across entire codebase

## [v2.1.0] - 2026-02-03

### Added

- Stricter v2.1 rubric thresholds (80%+ keywords for full credit)
- Rubrics for `reasoning_5e_001` and `metacog_004`
- Deprecation warning system for legacy scoring
- Migration timeline (legacy removal in v3.0)

### Changed

- v2.0 scoring now requires 80%+ keyword matches for full credit (was 66%)
- `reasoning_5e_001`: Fair scoring (15% → ~70% for good responses)
- All v2.1 tests now have binary % \<30% (improved discrimination)

### Deprecated

- Legacy scoring system (will be removed in v3.0)
- 6 tests still use legacy with deprecation warnings

### Fixed

- `reasoning_5e_001`: Good responses now score appropriately (was 15%)
- `metacog_004`: Binary % reduced from 31% to ~20%

## [v1.1.3] - 2026-02-11

### Added
- **Adaptive Pause System:** Implementierung eines adaptiven Pause-Systems für den Benchmark inkl. Dev Mode Unterstützung.
- **Probe/Warm-up:** Separation von Load-Time Tracking und Warm-up Probes für genauere Statistik-Erfassungen.

### Fixed
- **Code Quality:** Stabilitätsverbesserungen im Code Quality Modul, speziell für kleinere Modelle. Kompatibilitätsfix für DeepSeek-R1.

## [v1.1.0] - 2026-02-03

### Changed
- **Leaderboard V1.1 Overhaul:** Umstellung auf V1.1 Leaderboards mit neuen Aggregations-Metriken und Kosten-Analysen in USD/1K Tokens.
- **Golden Standard:** Stabilisierung der Golden Standard Generation für die kommerziellen Modelle.

## [v1.0.0] - 2026-02-03

### Added
- **Initial Production Release:** Einführung der Basis-Architektur (`run_commercial_benchmark`, `run_local_benchmark`).
- **Political Compass:** Implementierung und Stabilisierung der v3.0 Political Compass Metriken inkl. Mock-Testing.
- **Last-Hyphen-Rule:** Dynamische Asset-Gruppierung basierend auf der "Last-Hyphen-Rule" im Leaderboard.

## [v0.9.8] - 2026-01-29

### Added
- **Drift Detection:** Einführung eines Drift Detection Systems.
- **Checkpoint System:** Ein neues Checkpoint-System, um bei API-Ausfällen den Fortschritt zu sichern.

## [v0.9.6] - 2026-01-28

### Changed
- **MVC Architecture:** Vollständige Migration auf die Core/MVC (Model-View-Controller) Architektur.

### Fixed
- **Stability:** Behebung von Benchmark-Stabilitätsproblemen, Infinite Loops und Pfadauflösungsfehlern.

## [v0.9.5] - 2026-01-28

### Added
- **Cultural Intelligence:** Das Modul 5 (Cultural Intelligence) wurde finalisiert (neue Assets und gefestigtes Scoring).

## [v0.9.0] - 2026-01-23

### Changed
- **Framework Refactoring Complete:** Abschluss des großen Refactorings; die neue `BaseBenchmarkRunner`-Architektur für kommerzielle und lokale Modelle wurde als Baseline etabliert.

## [v0.5.0] - 2026-01-17

### Added
- **Gamification & Badges:** Einführung von gamifizierten Badges und Meta-Metriken ins Leaderboard.

## [v0.3.0-beta] - 2025-12-28

### Added
- **Documentation Quality Modul:** Ein neues Modul wurde hinzugefügt zur Untersuchung der Dokumentationsqualität.
- **Expert Difficulty:** Anpassung der UX-Writing Assets an ein 4-stufiges Schwierigkeitssystem (inkl. "Expert Level").

## [v0.2.0-beta] - 2025-12-27

### Added
- **Initial Release:** Initialer Startpunkt von CrucibleMark (mit grundlegenden Benchmarks zu Security, API Design und Code Quality).
