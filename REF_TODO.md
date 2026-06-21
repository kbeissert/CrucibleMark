# REF_TODO.md – Refactoring & Future Development

## Abgeschlossen

### Provider-Connector SSoT + Judge Token Usage Context (v4.10.5 – 21.06.26)
- [x] **`utils/providers/base.py` — 3 SSoT-Utilities:** `_extract_reasoning_tokens(usage)` (provider-agnostisch), `_extract_think_from_message(msg, field_names)` (generisch), `ThinkAccumulator` (Streaming-Helper). Ersetzen 5 identische lokale Methoden + 7 Streaming `think_parts`-Patterns.
- [x] **9 Provider auf Shared Utilities umgestellt:** openai, anthropic, groq, xai, openrouter, google, mistral, ollama, llamacpp_base.
- [x] **Streaming-Bugs gefixt:** OpenRouter fehlte `reasoning_tokens` im Streaming; llamacpp_base fehlte `reasoning_tokens` + `think_content` im Streaming.
- [x] **Judge Token Usage Context (universal):** `judge_evaluator.py` baut `token_usage_context` (tokens_used, reasoning_tokens, token_budget, module_budget, truncated). `judge_runner.py` + `judge_prompt_builder.py` rendern `### TOKEN USAGE ###` Section. 7 Verifikations-Tests inline. 822/822 Tests grün.

### CSV-Write-Through Bug Fix (v4.10.4 – 21.06.26)
- [x] **`utils/result_manager.py` — Atomare Schreibvorgänge:** `_write_to_csv()` mit `tempfile.mkstemp()` + `os.replace()` statt `"w"` (truncate). Existing Rows werden NICHT re-validiert. 10 Modelle mit 0 CSV-Einträgen identifiziert (Root-Cause: Full-Rewrite-Überschreibung).
- [x] **`config/provider_config.yaml` — Cleanup (-130 Zeilen):** Redundante Kommentare entfernt, 92 aktive Modelle erhalten.
- [x] **4 neue Tests** in `test_result_manager_validates.py`. 822/822 Tests grün.

### Token-Budget-Refactoring (v4.10.3 – 21.06.26)
- [x] **`utils/providers/base.py` — `_resolve_request_tokens()` (SSoT):** Shared Helper für alle 7 API-Provider. Zweistufige Kaskade: `resolve_token_budget()` → Provider-Default `max_tokens` → Per-Model Override `model_max_tokens`.
- [x] **7 Provider migriert:** openrouter, openai, anthropic, groq, xai, google, mistral.
- [x] **Provider-Config:** 7 Provider mit `max_tokens` Default, OpenRouter mit Per-Model Overrides.
- [x] **Token-Budget-Optimierung:** code_quality 65536→20000, cultural_intelligence 1000→3000, documentation_quality 6000→8000.
- [x] **Design-Constraints dokumentiert** in `systemPatterns.md` + `CLAUDE.md`. 819/819 Tests grün.

### Provider-Connector Thinking/Reasoning-Fix (v4.10.1 – 20.06.26)
- [x] **Alle 7 Provider-Connectors:** `reasoning_tokens`, `think_content`, `usage` jetzt konsistent in `last_response_metadata`. Anthropic Streaming komplett neu implementiert.
- [x] **Card-Cleanup:** 3 Cards mit fehlenden Sampling-Keys ergänzt, 1 Taxonomy-Placeholder entfernt. 819/819 Tests grün.

### Web-Export Nullwert-Entfernung (v4.10.0 – 20.06.26)
- [x] **`scripts/web_export.py` — `_strip_none()`** — Entfernt `None`-Werte rekursiv aus Dicts vor JSON-Export. Angewendet auf `_build_leaderboard_entry()`, `_build_compass_entry()`, `model_card`-Sub-Dict, `data.json`-Write.
- [x] **Neue Export-Felder:** `profile_verified_by`, `last_modified_at` (waren im Template als web_export-consumer markiert, fehlten im Export).
- [x] **`tests/test_web_export_card_field_coverage.py`** — Sample-Card ergänzt, Test 5 (`model_card: None` → Key entfernt), 4 `_strip_none`-Unit-Tests + 1 Integrationstest. 818/818 Tests grün.
- [x] **Verifikation:** 93 Modelle exportiert, 0 None-Werte in `model_card`, 0 None-Werte in `leaderboard`, 0 None-Werte in `political_compass`.

### Card-Research Force-Run + Template-Cleanup (v4.10.0 – 20.06.26)
- [x] **110/110 Cards `profile_verified=true`** — Vollständiger Force-Run mit `make card-research MODEL=all FORCE=1`. Template von 42 auf 37 required Felder reduziert.
- [x] **`config/card_template_model.yaml`** — 6 Felder von `required` auf `optional` verschoben: `params_total_b`, `params_active_b`, `knowledge_cutoff`, `license_url`, `input_price_per_1m`, `output_price_per_1m`. Beschreibungen sagten "null wenn X" aber `required: true` war ein Widerspruch.
- [x] **`scripts/manage_model_cards.py` — `MODEL=all`** — `--card all` als Spezialwert erkannt. Early-Validation in `main()` erkennt `all` ebenfalls.
- [x] **`scripts/manage_model_cards.py` — `MAX_CARDS=N`** — Neuer CLI-Arg `--max-cards N` + Makefile-Variable `MAX_CARDS`. Limitiert Targets pro Run. Fortschrittsanzeige am Ende.
- [x] **`scripts/tools/probe_thinking.py` Path-Bug** — `card_path.relative_to(ROOT_DIR)` crash bei relativen Pfaden → `card_path.resolve().relative_to(ROOT_DIR)` mit Fallback.
- [x] **9 lokale Modelle** — Thinking-Probe-Placeholder manuell ersetzt (Ollama entfernt): Qwen3-Familie → `detected=True`, Gemma 4 → `detected=False`, Hermes 4.3 (Qwen3-basiert) → `detected=True`.
- [x] **7 Cards** — `thinking_probe_at` Timestamp nachgetragen.
- [x] **1 Card** (`claude-sonnet-4-5-20250929`) — `license_url` manuell gesetzt.
- [x] **1 Card** (`gemma-4-26B-A4B-it-UD-Q8_K_XL`) — `supports_tool_use=False` gesetzt.
- [x] **Dokumentation** — CLAUDE.md (6 neue Pitfalls), activeContext.md, progress.md, DEVELOPER_GUIDE.md, ARCHITECTURE.md, systemPatterns.md, Makefile (probe-thinking Hilfe) aktualisiert.

### Vendor Card description-Feld + editor_prompts-Fix (v4.9.3 – 12.06.26)
- [x] **`config/card_template_vendor.yaml` v1.1.0** — Neues optionales Feld `description` (Position: erstes optionales Feld, vor `card_subtype`). Constraints: `min_length: 240`, `max_length: 480`, `target_length: 360`. `consumers: [web_export, review]`, `since: "v4.9.3"`. Template-Version: `1.0.0` → `1.1.0`.
- [x] **`config/editor_prompts.yaml` Pfad- + Feldname-Fix** — `targets.directory: provider_cards/` → `vendor_cards/`; Prompt-Text Schritt "Auftrag" + Schritt 1 + Schritt 4: `provider_id` → `vendor_id`.
- [x] **`tests/test_card_template.py`** — `test_provider_template_loads` Version-Assertion `"1.0.0"` → `"1.1.0"`. 803/803 Tests grün.
- [x] **Dokumentation** — README (badge + Recent Versions), CHANGELOG (v4.9.3-Eintrag), PROJECT_STATUS, memory-bank/activeContext.md, memory-bank/progress.md, docs/CARD_MANAGEMENT.md (Felder-Anzahl Vendor Card), REF_TODO.md.

### Card-Datenpflege-System: Vendor-Kanonisierung + profile_verified + Editor-Prompt (v4.9.0 – 12.06.26)
- [x] **`config/classification_taxonomy.json → manufacturers`** — 13 kanonische Hersteller-Namen als SSOT. Aliase (z.B. "Alibaba Cloud" → "Alibaba") werden in `_normalize_vendor()` aufgelöst.
- [x] **`scripts/web_export.py::_normalize_vendor()`** — Normalisiert Vendor-Strings auf kanonische Namen vor dem Export. Nicht-kanonische Werte werden gewarnt, nicht hart abgebrochen.
- [x] **`scripts/verify_model_cards.py`** — `🏭`-Warnungen bei nicht-kanonischen Vendor-Namen. 16 Model Card JSONs mit Vendor-Korrekturen migriert.
- [x] **`config/card_template_model.yaml`** — 2 neue optionale Felder (seit v4.9.0) ergänzt: `profile_verified: bool` (default: false) und `profile_verified_at: str | null` (default: null). `last_updated` auf 2026-06-12 gesetzt.
- [x] **`scripts/verify_model_cards.py`** — `🔍`-Warnungen wenn `profile_verified` fehlt (noch nicht migriert) oder `false` (Inhalt unverifiziert). Informell, kein Hard-Fail.
- [x] **119 Model Card JSONs** — per `jq` bulk-migriert: `profile_verified: false`, `profile_verified_at: null`. `_index.json` ausgelassen (kein Model Card Schema).
- [x] **`config/editor_prompts.yaml`** — Neuer Prompt `model_card_verification`: Strukturierter LLM-Workflow für redaktionelle Card-Verifikation. Glossar, 5-Schritt-Prozess, Was-verändern/Was-gesperrt-Tabelle, Qualitätskriterien. Gesperrte Felder: alle Probe-Felder, ToolUse-Felder, Sampling-Parameter, `generated_at`, `card_status`, `heritage_ids`.
- [x] **`docs/CARD_MANAGEMENT.md`** — 3 neue Sektionen: "Vendor-Kanonisierung (ab v4.9.0)", "Datenpflege-Verifikation: profile_verified (ab v4.9.0)", "Editor-Prompts: Redaktionelle LLM-Aufgaben (ab v4.9.0)". Feldzahl-Update.
- [x] **Memory Bank** — `memory-bank/activeContext.md` + `memory-bank/progress.md` mit Session-16-Eintrag aktualisiert.

### Robustness-Fixes: Judge-Coverage, Draft-Card-Warning, ToolUse P1/P2 SSoT (v4.8.6 – 12.06.26)
- [x] **`scripts/leaderboard/score_calculator.py::_aggregate_basic_stats()`** — Judge-Skip-Zeilen mit `judge_prog.str.contains("skip")` vor Coverage-Formel gefiltert. Verhindert falsches 98%-Coverage bei absichtlich übersprungenen Antworten.
- [x] **`scripts/leaderboard/__init__.py`** — Draft-Card-Warning nach `_model_name_ssot()`: `print()` + `logger.warning()` wenn `Model Name == "TODO"`. Macht auto-erstellte Draft-Cards (`ensure_card()`) sofort sichtbar.
- [x] **`utils/model_utils.py::update_model_card_tooluse_fields()`** — Neue Parameter `p1_score: float | None` und `p2_score: float | None`. Schreibt `tooluse_score_p1`/`tooluse_score_p2` in Card JSON.
- [x] **`scripts/core/tooluse_exporter.py::finalize_model()`** — Ruft `update_model_card_tooluse_fields()` mit `p1_score=_p1_mean`, `p2_score=_p2_mean` auf — persistiert Scores nach Live-Run in Card.
- [x] **`scripts/core/tooluse_exporter.py::_aggregate_asset_rows()`** — Return-Dict bevorzugt `card.get("tooluse_score_p1/p2")` über CSV-Neuberechnung. Verhindert dass `make tooluse-leaderboard` validierte Scores überschreibt.
- [x] **52/52 Tests grün.** Dokumentation: `docs/MAINTENANCE_LOG.md` (v4.8.6-Eintrag), `docs/TOOLUSE_MODULE.md` (Card-Score-Felder), `docs/SCORING_METHODOLOGY.md` (Judge-Skip-Hinweis), `memory-bank/ActiveContext.md` (Session 15).

### Thinking-SSoT-Auflösung + Runner-Consumer-Anbindung (v4.7.3 – 10.06.26)
- [x] **`utils/model_utils.resolve_effective_thinking(model_card, provider_model_cfg, *, model_id, now)`** — zentrale SSoT-Auflösung mit Audit-Trail. Priorität: aktiver `thinking_override` > Card-Probe > None. Rückgabe `(effective, source)`. Audit-Log: `[ThinkingOverride] model_id: override active (value=…, reason=…)`.
- [x] **`utils/model_utils._is_override_active(override, now=None)`** — Override-Validierung. `value` muss bool sein, `reason` Pflicht (Whitespace-only zählt als leer), `active_until` optional (ISO-8601, naive wird UTC, muss in der Zukunft liegen). Inaktivität → Card-Probe gewinnt automatisch (Auto-Expiry).
- [x] **`resolve_token_budget(..., *, provider=None)`** — neuer keyword-only kwarg. Bei `provider="..."` wird die Provider-Card via `load_provider_card()` geladen und an `resolve_effective_thinking()` durchgereicht. Effekt: aktiver Override schaltet den 5×-Reasoning-Multiplikator an/aus. Card-Probe `false` gewinnt über Trigger-Liste. 5 alte Call-Sites (`mistral.py`, `openrouter.py`, `openai.py`, `llamacpp_base.py`, `make_optional_arg`) funktionieren ohne `provider`-Argument unverändert.
- [x] **`utils/base_runner.py:121`** — reicht `provider=provider` an `resolve_token_budget()` durch. Lokale Importe umgehen potentiellen Circular-Import.
- [x] **Tests** — `tests/test_thinking_override.py` (24 Tests, SSoT-Auflösungsmatrix, Override-Validierung, Audit-Trail, Backward-Compat) + `tests/test_base_runner_thinking_budget.py` (17 Tests, Backward-Compat, Trigger-Fallback, Override aktiv/expired/ohne-reason, Probe-SSoT, Audit-Log, Card-Cap, kaputte Card-JSON, Edge-Cases).
- [x] **Full-Suite:** **634/634 grün in 2.11s** (vorher 617, +17 durch Runner-Consumer + 24 v4.7.1 Override-Tests).
- [x] **Dokumentation** — `docs/THINKING_PROBE.md` NEU (Methodik-Doku, Drei-Signal-Hierarchie, Multi-Prompt-Aggregation, SSoT-Auflösung, Override-Regeln, Runner-Consumer, Discovery-Inventar). `CHANGELOG.md` v4.7.3-Eintrag. `docs/ARCHITECTURE.md` + `docs/CARD_MANAGEMENT.md` + `CLAUDE.md` + Memory-Bank synchronisiert.
- [x] **Architektur-Begründung** — Discovery-Fund (9/9 Modelle, 27 Probes, 100 % Erkennungsrate) zeigte: Inline-CoT ist der einzige robuste Trigger über alle Provider. Tags bei `enable_thinking: false` / OpenRouter-Strip unzuverlässig, `reasoning_tokens` nur bei manchen OpenRouter-Modellen. Card-First-Property verhindert Drift; `active_until` zeitlich begrenzt sie.

### Thinking-Probe v2 — Multi-Prompt + Familien-Inventar (v4.7.2 – 09.06.26)
- [x] **`_PROBE_PROMPTS` Dict in `utils/model_utils.py`** — 3 Probe-Prompts (`math`/`code`/`decision`) ersetzen den einzelnen Mathe-Prompt. 3 Domänen verhindern Fehlklassifikation (manche Familien zeigen CoT nur bei ethischen Fragen, andere nur bei Code/Mathe).
- [x] **Erweiterte `_THINK_TAGS` Liste (3 → 13 Tags):** `<think>`/`<thinking>`/`<thought>` (Qwen 3, Magistral, GLM), `<|thinking|>`/`<|reasoning|>` (OpenAI OSS), `<reasoning>`/`<reason>` (DeepSeek R1/V3), `<reflection>` (Meta Llama 4), `<analysis>`/`<plan>` (Anthropic), `<scratchpad>` (Hermes), `<solution>` (Mistral), `<cot>` (Custom).
- [x] **`_find_think_tags()` + `_probe_single()` + `probe_thinking_model(prompts=...)`** — Multi-Prompt-Pfad mit Aggregation. Höchste Confidence gewinnt. Bei `prompts=None` werden alle 3 aus `_PROBE_PROMPTS` gesendet. Single-Prompt-Modus für Card-First-Hook bleibt erhalten.
- [x] **`ThinkingProbeResult` mit `prompts_used` und `tags_found` Feldern** — Backward-Compat-Defaults erhalten.
- [x] **`scripts/tools/discover_thinking_tags.py` (NEU, ~370 Zeilen)** — read-only Discovery-Skript. Lädt Configs, gruppiert nach Familie (18 Familien via `identify_family()`), wählt 1 Repräsentant (lokal > openrouter > cloud; Thinking-Bonus), sendet 3 Prompts, schreibt `docs/THINKING_TAGS_INVENTORY.md`. CLI: `--families`, `--provider`, `--max-per-family`, `--output`, `--dry-run`, `--fail-fast`. **Schreibt KEINE Model Cards** — saubere Trennung Discovery ↔ Card-Update.
- [x] **Tests** — `tests/test_thinking_probe_families.py` (59 Tests: Multi-Prompt-Aggregation, _THINK_TAGS, _find_think_tags, identify_family, pick_representatives, aggregate_probe). 587/587 grün.
- [x] **Discovery-Run** — 3 Wellen, 9 Modelle, 27 Probes, 0 Fehler, 100 % Erkennungsrate, ~12 min. Tags nirgends sichtbar (Provider-stripped oder `--reasoning off`). Inline-CoT universell (400-4619 chars). `docs/THINKING_TAGS_INVENTORY_M4.md` / `_SPARK.md` / `_CLOUD.md` (Roh-Daten).

### Web-Export-Blacklist (v4.7.1 – 09.06.26)
- [x] **`config/web_export_blacklist.yaml`** — flache YAML-Liste mit `fnmatch`-Wildcards (z. B. `qwen3.5-35b-a3b-*` sperrt alle Quants). Datei fehlt/leer → keine Filterung (graceful).
- [x] **`scripts/web_export.py::_load_export_blacklist()` + `_is_blacklisted()`** — SSoT-Helper. Splittet in `exact_set` (O(1)) + `pattern_set` (fnmatch). Parse-Error → WARNING + leer. Hook nach PC-Skip, vor `mkdir()`. Match-Schlüssel: `raw_model_id` aus Leaderboard-CSV (SSoT).
- [x] **`meta.json` Block `blacklist`** — additiv: `source`, `total_entries`, `skipped_in_run`. 17 neue Tests, 471/471 grün.
- [x] **Use-Case** — Quant-Vergleichstests + experimentelle Modelle aus Web-Frontend raus halten, ohne sie aus dem Leaderboard zu löschen.

### 4-Phasen-Refactoring der Kern-Skripte (v4.7.0 – 09.06.26)
- [x] **Phase 1 — Ruff Auto-Fix** (209 Auto-Fixes) — `utils/llm_client.py`, `scripts/core/benchmark_auto.py`, `scripts/core/llamacpp_batch.py`, `scripts/core/unified_runner.py`. Reduktion auf 0 Ruff-Issues.
- [x] **Phase 2 — SSOT-Konsolidierung** in `llamacpp_batch.py` (5 Ebenen: Lifecycle-Helper, Context-Manager, Cache-Helper, Asset-Ermittlung, Leaderboard-Cache). `canonical_lookup_keys()` als zentrale SSoT für Modell-Lookup-Keys (hf.co-Prefix, Datumssuffix, `_safe_name`, asymmetrische Brücke Underscore→Punkt).
- [x] **Phase 3 — CC-Reduktion** (11 Helfer-Funktionen extrahiert, alle CC ≤ 12):
  - `get_startable_assets` → 4 Helfer (`_should_skip_due_to_card`, `_is_batch_module_done`, `_resolve_uncached_assets`, `_is_asset_uncached`)
  - `get_leaderboard_scored_modules` → 3 Helfer (`_extract_model_id_from_row`, `_add_scored_modules_for_model`, `_is_module_scored`)
  - `run_benchmark` → 11 Helfer (CC 35 → ≤ 12)
  - `_process_single_test` → 8 Helfer (CC 32 → ≤ 12)
  - `run_commercial_batch` → 7 Helfer (CC 24 → ≤ 12)
  - `main` → 6 Helfer (CC 18 → ≤ 12)
- [x] **Phase 4 — Magic-Number-Konsolidierung** in `utils/constants.py`:
  - `MIN_REFUSAL_CHARS: int = 15`, `HTTP_OK: int = 200`
  - 5× `LLAMACPP_*` (Health-Check, Probe, Reset-Pauses heavy/medium/ok/fallback)
  - `OLLAMA_UNLOAD_SETTLE_SEC: float = 0.5`
  - 12 Magic-Value-Stellen in `unified_runner.py` ersetzt
  - 3 SIM-Fixes: `SIM110` (`_has_open_tests`), `SIM103` (`_is_module_scored`, `_is_asset_uncached`)
- [x] **Type-Hint-Bug-Fix:** `_load_commercial_existing_tests` Return-Type `dict` → `set[tuple[str, str]]` (echter Return-Type). Sed-Replacement für 6 weitere Vorkommen.
- [x] **Verifikation (alle 4 Quality-Gates grün):**
  - Ruff: `All checks passed!` (0 Issues)
  - Pytest: **481/481 grün** (Refactoring-Scope, ohne die 14 vorbestehenden MCP-Server-HTTP-404-Failures, die mit `git stash` reproduziert wurden)
  - Pylint: **10.00/10** für alle 5 Kern-Dateien
  - Mypy: **0 Issues in 5 source files**
- [x] **Dokumentation** — README.md (Versionsbadge, Recent-Versions-Sektion, Status), PROJECT_STATUS.md (Header v4.7.0 + Phase-30-Block), CHANGELOG.md (v4.7.0-Eintrag), memory-bank/progress.md (Phase-4-Block).
- [x] **Erkenntnisse** — Ruff `SIM103` mit `--unsafe-fixes` ist zu aggressiv (`if not is_batch: return False` lässt sich nicht 1:1 umkehren bei `or`-Bedingung; idiomatische Lösung: `return not any(...)`). `_is_batch_module_done` und `_is_asset_uncached` hatten das identische Anti-Pattern. `pandas.isna()` braucht expliziten None-Check vor `str(val).strip()`.

## Backlog (Phase 2)
- [ ] **`content_transformation_005` — Body-Word-Parser:** `keyword_presence`-Check für 300-Wort-Limit des Email-Bodys durch echten Wort-Count ersetzen. Benötigt Section-Parser der Analyse-Teil von Newsletter-Body trennt. Aufwand: ~30 LOC in `__init__.py` + Issue-Umstellung in `asset_005_newsletter_adaptation.yaml`. Risiko: Modelle formatieren Body uneinheitlich — falsche Penalties bei ~20% der Antworten möglich. Wert: 2.4 Pkt. Nicht zeitkritisch.

## Abgeschlossen

### CSV-Hygiene Defense-in-Depth (v4.6.1 – 08.06.26)
- [x] **`utils/result_manager.py::_validate_row_for_write()`** (NEU) — Hard-Fail-Guard: validiert JEDE Zeile (neu + bestehend) gegen die Sanitizer-Heuristiken. Wirft `ValueError` bei Header-Repeat, narrativer Asset-ID oder ungültigem Modell. Caller fängt ab und überspringt resilient.
- [x] **`utils/result_manager.py::_write_to_csv()`** (refactored) — nutzt den Hard-Fail-Guard; zeigt `🛡️ Hard-Fail-Guard: N korrupte Zeile(n) übersprungen` bei Funden.
- [x] **`scripts/maintenance/consolidate_csv.py::_filter_corrupt_rows()`** (NEU) — wendet identische Sanitizer-Heuristiken auf den DataFrame VOR `to_csv()` an. Verhindert dass Maintenance-Konsolidierung Müll zurück in die CSV schreibt.
- [x] **`scripts/maintenance/consolidate_csv.py::consolidate_file()`** (erweitert) — Logging mit Korrupt-Drop-Counter (`🗑️ Korrupt-Drop: header_repeat / narrative_asset_id / invalid_model`).
- [x] **`Makefile::validate-csv`** (NEU) — Makefile-Target für Dry-Run-Validierung (CI-/Smoke-tauglich).
- [x] **`tests/test_consolidate_csv_validates.py`** (NEU, 9 Tests) — Filter-Unit-Tests (Header-Repeat, narrative Asset-ID, Boolean-Model), leere DataFrames, fehlende Spalten, E2E mit tmp-CSV, fehlende Datei, gemischte Korruptions-Muster.
- [x] **`tests/test_result_manager_validates.py`** (NEU, 7 Tests) — Hard-Fail-Guard: akzeptiert saubere Zeilen, lehnt narrative/Header-Repeat/Boolean/leere Modelle ab, E2E mit Save, Resilienz bei gemischter Korruption.
- [x] **Dokumentation** — `CHANGELOG.md` (v4.6.1-Eintrag), `docs/MAINTENANCE_LOG.md` (v4.6.1-Sektion), `memory-bank/activeContext.md` und `memory-bank/progress.md` (Phase 9 Block) aktualisiert.
- [x] **226/226 Tests grün** (vorher 210, +16). Pylint 10.00/10 für `result_manager.py`, `consolidate_csv.py`, beide Test-Dateien.

### CSV-Hygiene-Sanitizer (v4.6.0 – 08.06.26)
- [x] **`scripts/maintenance/sanitize_benchmark_csvs.py`** (NEU) — Vier-Klassen-Filter (Header-Repeat, Rohtext-Asset-IDs >60 Zeichen + Romananfänge + Markdown-Marker, Boolean-Modelle, leere Modelle). Dry-Run + `--apply`, idempotente `.bak`-Backups, atomare `.tmp`+`replace()`-Writes. SSoT-CSV-Pfade aus `scripts.leaderboard.config`. Exit-Code 0 in beiden Modi.
- [x] **`tests/test_sanitize_benchmark_csvs.py`** (NEU, 65 Tests) — parametrisierte Filter-Unit-Tests (14 Romananfänge, 5 Markdown-Marker, 5 pandas-Sentinel-Varianten), Pipeline-Tests, Backup-Idempotenz, Atomic-Write, E2E mit `monkeypatch` auf SSoT-Pfade.
- [x] **Daten-Sanierung** — 13.466 Müll-Zeilen aus `local_models_benchmark.csv` entfernt (93% der CSV: 17.705 → 1.013). `commercial_models_benchmark.csv` 11 Zeilen verworfen (0.6%). `cloud_models_benchmark.csv` bereits sauber. Backups `*.bak` (idempotent).
- [x] **Leaderboard regeneriert** — 84 Zeilen, 78 vollständig (43/43), 5 unvollständig (echte Asset-Lücken für Re-Run: Kimi K2.6, DeepSeek V4 Pro, Qwen 3.5 397B A17B, MiniMax M2.7, GLM-4.7), 1 mit Test-Override-Logik (Tool-Use-Backlog).
- [x] **210/210 Tests grün** (vorher 145, +65). Pylint 10.00/10 für Sanitizer + Test-File.

### ID-SSoT-Refactoring (v4.5.0 – 08.06.26)
- [x] **`utils/model_utils.py::strip_date_suffix()`** (NEU) — SSoT für Datums-Suffix-Strip (`-YYYYMMDD` / `-MMDD` mit gültigem Monat); idempotent.
- [x] **`utils/model_utils.py::enforce_card_first()`** (NEU) — Card-First-Vertrag: garantiert Card-Existenz via `ensure_card()` (Draft falls fehlt, WARNING wird geloggt). Rückgabe `(canonical_id, has_card)`.
- [x] **`utils/model_utils.py::resolve_canonical_model_id()`** (refactored) — zentrale ID-Bridge (Card-Lookup + Suffix-Strip + `_safe_name`-Fallback).
- [x] **`utils/result_manager.py::save_results()`** — nutzt jetzt `enforce_card_first()` statt `resolve_canonical_model_id()`. CSV-Senke ist die zentrale Card-First-Durchsetzungsstelle.
- [x] **12 Inline-ID-Transformationen migriert** auf SSoT — in `utils/benchmark_utils.py`, `utils/scoring_utils.py`, `utils/providers/llamacpp.py`, `scripts/maintenance/*`, `scripts/core/*`, `scripts/analysis/*`, `scripts/core/tooluse_exporter.py`.
- [x] **`scripts/analysis/generate_provider_cards.py`** + **`scripts/analysis/review/risk_calculator.py`** — lokale `safe_id()`-Duplikate entfernt; Import von `utils.provider_card_template._safe_id`.
- [x] **`scripts/leaderboard/module_integration.py::_resolve_to_canonical_id()`** — delegiert primär an `utils.model_utils.resolve_canonical_model_id()`; lokaler 5-Level-Card-Lookup bleibt als Bulk-Fallback.
- [x] **`scripts/maintenance/migrate_canonical_model_ids.py`** entfernt — Workaround durch SSoT-Funktionen ersetzt. 22 `*.bak`-Dateien in `benchmark_scores/model_cards/` gelöscht.
- [x] **`tests/test_enforce_card_first.py`** (NEU, 5 Tests) — Card-First-Vertrag-Invariante: existing-card, missing-card-creates-draft, idempotent, empty-input, hf.co-prefix-pipeline.
- [x] **`tests/test_id_ssot_invariants.py`** (NEU, 4 Tests) — Brücken-Äquivalenz zwischen `enforce_card_first` und `resolve_canonical_model_id`; Slugify-Konsistenz für `:/ .` + Leerzeichen; Idempotenz (10 Wiederholungen); AST-Sweep gegen Inline-`re.sub` mit Slugify-Pattern außerhalb der SSoT-Module.
- [x] **Dokumentation** — `docs/ARCHITECTURE.md`, `docs/DEVELOPER_GUIDE.md`, `memory-bank/systemPatterns.md` und `memory-bank/activeContext.md` auf ID-SSoT-Stand aktualisiert. Veraltete `_resolve_dir()`-4-Stufen- und `migrate_canonical_model_ids.py`-Erwähnungen entfernt bzw. präzisiert.
- [x] **145/145 Tests grün** (vorher 124, +21). Klare SSOT-Trennung: keine DRY-Verletzungen im ID-Layer mehr.

### CSV Robustness & Leaderboard Pipeline Hardening (v4.4.0 – 07.06.26)
- [x] **`utils/csv_recovery.py` — `load_csv_robust()`:** Robuster CSV-Loader mit `on_bad_lines="skip"` implementiert. Korrupte Zeilen (z.B. durch Audit-Log-Injection) werden übersprungen statt Parser-Fehler zu werfen.
- [x] **`scripts/maintenance/consolidate_csv.py` — ID Resolution:** `_resolve_to_canonical_id()` implementiert für Mapping von Display-Namen zu kanonischen Model-IDs. Fallback-Strategien (robust → standard pandas) mit Zeitzone-Fix (`utc=True`).
- [x] **`scripts/maintenance/consolidate_csv.py` — Robust Loader Integration:** `_load_csv_robust_with_fallback()` mit 2-Stufen-Strategie: (1) `load_csv_robust()` → (2) Standard pandas mit `on_bad_lines="skip"`.
- [x] **CSV-Korruption bereinigt:** `local_models_benchmark.csv` von 79.444 Zeilen (mit Audit-Log-Content) auf 14.222 Zeilen bereinigt. Backup: `local_models_benchmark.csv.backup_20260607_033454`.
- [x] **Leaderboard-Verifikation:** `qwen3.6-35b-a3b-q8` korrekt im Leaderboard (Rank 32, Score 73.39, 43/43 Tests).
- [x] **Backup-System:** `make backup` erstellt konsistente 39MB-Archive mit `consolidate_csv.py`.
- [x] **Web Export:** `make web-export` exportiert 80 Modelle korrekt mit Model Card als SSOT.
- [x] **Memory Bank:** `techContext.md` und `progress.md` mit v4.4.0-Meilenstein aktualisiert.
- [x] **Dokumentation:** `README.md`, `PROJECT_STATUS.md`, `REF_TODO.md` auf v4.4.0 synchronisiert.

### llamacpp Kontextfenster-Fix & Provider-Architektur-Analyse (v4.3.2 – 05.06.26)
- [x] **`utils/providers/llamacpp.py` — Kontextfenster-Resolution:** `_build_server_cmd()` nutzt Provider-Level `context_window` als Fallback, wenn `model_cfg.context_length` fehlt. Prioritätenkette: Model-Level → Provider-Level → Globaler Default → Hardcoded (32768).
- [x] **Provider-Instanziierungs-Analyse:** Registry in `BaseProviderClient` erzeugt separate Instanzen für jeden Provider-Namen (`llamacpp`, `llamacpp_spark`, etc.). Parallele Benchmarks auf verschiedenen Hosts sind architektonisch möglich.
- [x] **Memory Bank:** `techContext.md` mit neuer Sektion "Kontextfenster-Resolution" aktualisiert.

### Code Quality Pass (v4.3.1 – 05.06.26)
- [x] **`unified_runner.py` — F841 Bug** — `existing_card` wurde befüllt aber nie genutzt. Entfernt.
- [x] **`unified_runner.py` — R1716** — Chained comparison `0 < response_len < threshold`.
- [x] **`unified_runner.py` — `_BUDGET_KEYWORDS`** — Modul-Level-Konstante statt Rebuild pro Exception.
- [x] **`unified_runner.py` — Inline-Imports** — `csv`, `hashlib`, `time`, `datetime`, `append_global_run_metrics` an Dateianfang; `_language_validator = LanguageValidator()` auf Modul-Ebene.
- [x] **`benchmark_auto.py` — `_LLAMACPP_STOP_SETTLE_SEC = 3`** — Magic Number ersetzt.
- [x] **`run_tooluse_benchmark.py` — `import argparse`** — Aus `main()` an Dateianfang verschoben.
- [x] **`llamacpp.py` — `subprocess.Popen`** — Erklärender Kommentar warum kein Context Manager (Hintergrundprozess).
- [x] **`political_compass/test.py` — ANSI-Guard** — `sys.stdout.isatty()`-Check für Escape-Codes.
- [x] **`scripts/core/model_discovery.py`** (NEU) — DRY-Konsolidierung: `discover_local_models()`, `discover_commercial_models()`, `discover_models()` — war identisch in `run_score_benchmark.py` und `run_political_compass_benchmark.py` dupliziert. Beide Worker importieren jetzt aus dem SSOT.
- [x] **Pylint 10.00/10** (+0.01), Ruff clean, 227/227 Tests grün.

### Spark-Connector Konsolidierung & Lifecycle-Cleanup (v4.3.0 – 04.06.26)
- [x] **`utils/providers/llamacpp.py` — Readiness-Hardening:** 200-Response gilt als valide Readiness auch bei leerem `content`, wenn `reasoning_content`, `finish_reason` oder `usage.total_tokens` gesetzt sind.
- [x] **Endpoint-Adoption-Warmup:** Läuft unter `base_url` bereits das Zielmodell, wartet der Connector innerhalb eines konfigurierbaren Fensters auf Readiness statt sofort mit Konfliktwarnung abzubrechen.
- [x] **`scripts/core/unified_runner.py` — garantierter Cleanup:** Lokale Provider (`ollama`, `llamacpp`, `llamacpp_spark`) werden in `finally` bereinigt; `cleanup_on_exit` + `server_post_stop_cmd` laufen auch bei `KeyboardInterrupt`/`sys.exit`.
- [x] **CLI-Modul-Qwen-Validierung:** `cli_benchmark` Kurztest mit `qwen3.6-35b-a3b-q8` auf Spark erfolgreich; Erfolgspfad und Abbruchpfad inkl. Unload/Cache-Clear verifiziert.

### ToolUse-Pipeline Bug-Fixes & Leaderboard-Audit (v4.2.1 – 03.06.26)
- [x] **`run_tooluse_benchmark.py` — Exporter nach Delegate-Einzellauf** — `benchmark_auto.py` ruft Delegate immer mit `--model <id>` auf; dieser Pfad hatte keinen `ToolUseExporter`-Aufruf → `tooluse_leaderboard.csv` blieb nach `make benchmark-auto` ewig veraltet. Fix: Exporter nach `_run_model()` im `--model`-Zweig eingefügt.
- [x] **`tooluse_exporter.py` — Asset-Level-De-Duplikation** — `aggregate_from_benchmark_csvs()` sammelte blind aus allen 3 CSVs. Dasselbe `(model_id, asset_id)` aus zwei CSVs (z.B. nach Mock-Fehler-Run) halbierte den Score. Fix: `best_rows`-Dict auf `(model_id, asset_id)` — neuester Timestamp/`success`-Status gewinnt.
- [x] **`data_loader.py` — Dead-Code Boundary-Filter** — Filter für `"Open Weights (Cloud)"` / `"Open Weights (Local)"` waren seit `get_model_category()`-SSOT-Migration wirkungslos (Strings werden nie erzeugt). Beide entfernt; `source`-Feld aus CSV-Pfad verhindert Cross-CSV-Kontamination bereits per Design.

### OpenRouter-Migration, Free-Tier & Qwen-Integration (v4.2.0 – 31.05.26)
- [x] **`openrouter.py` — `data_collection: allow`** — Alibaba-Cloud-Endpoints (Qwen via OpenRouter) liefern ohne explizite Policy-Zustimmung HTTP 404. Fix: `extra_body={"data_collection": "allow"}` bei jedem OR-Request.
- [x] **Model Cards Qwen** — `qwen_qwen3_7-max.json` (Proprietär, $1.25/$3.75 per 1M, context 131K, thinking_probe: false) und `qwen_qwen3_6-plus.json` (Hybrid-Reasoning, $0.33/$1.95 per 1M bis 256K, thinking_probe: true).
- [x] **`resolve_provider()` — `:free`-Suffix-Bug** — `":" in model_id` → Ollama nur wenn kein `"/"` im Namen. `"/" in model_id` → `openrouter` (nicht Groq).
- [x] **OpenRouter Free Tier** — `openrouter_free`-Rate-Limit-Profil (18 RPM / 1 concurrent) in `rate_limits.yaml`. `unified_runner.py` wählt automatisch per `model.endswith(":free")`.
- [x] **Ollama → OpenRouter Migration (3 Modelle)** — `google/gemma-4-31b-it`, `deepseek/deepseek-chat-v3.1`, `deepseek/deepseek-v3.2`. Model Cards umbenannt, alle 5 Benchmark-CSVs migriert.
- [x] **`generate_review.py` Skip-Logik** — mtime-Vergleich entfernt; Existenz-Check reicht.
- [x] **`make review` FLAGS** — `AUTO=1` und `FORCE=1` werden korrekt an `generate_review.py` weitergereicht.
- [x] **`CLAUDE.md` Pitfall** — `resolve_provider()` `:free`-Suffix-Verhalten dokumentiert.

### llamacpp-Erweiterung & Bug-Fixes (v4.1.0 – 30.05.26)
- [x] **Double-Start-Bug** — `_query_active_model()` in `llamacpp.py`: Server-Modell per API erkennen statt In-Process-State. Verhindert unnötigen Restart in Sub-Prozess-Kontext.
- [x] **Duplicate-Runner-Bug** — Zweite `UnifiedBenchmarkRunner`-Zeile in `benchmark_auto.py` entfernt; `lcpp_client` zeigte auf weggeworfene erste Instanz.
- [x] **gemma-3-12b-it-q8** — Provider-Config-Eintrag + Model Card (Q8_0-GGUF, `weights_source`-Feld).
- [x] **Model Card Schema** — `model_version` = Format/Quant, `weights_source` = Plattform.
- [x] **3 Module aktiviert** — `code_quality`, `reasoning_logic`, `documentation_quality` on by default.

### v4.0.0 Release — Pricing-Architektur-Bereinigung (26.05.26)
- [x] **Daily Budget Enforcement entfernt** — `check_budget()`, `get_daily_spend()`, `get_remaining_budget()` aus `CostTracker` entfernt. `cost_limits.yaml` gelöscht. Budget-Vorab-Check in `llm_client.py` entfernt. `CostLimitExceededError` entfernt.
- [x] **`CostTracker` vereinfacht** — Kein YAML-Config-Loading mehr. `calculate_cost()` 1-stufig: Model Card → Warning + 0.0.
- [x] **Docs synchronisiert** — `CLAUDE.md`, `README.md`, `USER_GUIDE.md`, `DEVELOPER_GUIDE.md`: alle `cost_limits.yaml`-Referenzen entfernt.
- [x] **Version auf 4.0.0 angehoben** — README-Badge, `PROJECT_STATUS.md`, `REF_TODO.md`, `CHANGELOG.md` synchronisiert. Git-Tag `v4.0.0` gesetzt.

### Model Card Content Completion — 4 Frontier-Modelle (v3.15.1 — 26.05.26)
- [x] **`mistral-large-2512.json`** — Mistral Large 3 (MoE, 675B/41B aktiv, Apache 2.0, open-weights, context 262K, input 0.50$/1M, output 1.50$/1M). Recherchiert + vollständig befüllt, `card_status: "complete"`.
- [x] **`devstral-2512.json`** — Devstral 2 (Dense 123B, Modified MIT, restricted-weights, context 256K, input 0.40$/1M, output 2.00$/1M). Recherchiert + vollständig befüllt, `card_status: "complete"`. Lizenz: Modified MIT mit kommerziellem Aktivierungsmechanismus → korrekt als `restricted-weights` klassifiziert.
- [x] **`gpt-5_5.json`** — GPT-5.5 (Proprietär, OpenAI, context 1050K, knowledge_cutoff 2026-04, input 5.00$/1M, output 30.00$/1M). Recherchiert + vollständig befüllt, `card_status: "complete"`.
- [x] **`gemini-3_5-flash.json`** — Gemini 3.5 Flash (Proprietär, Google DeepMind, context 1049K, knowledge_cutoff 2025-01, input 1.50$/1M, output 9.00$/1M). Recherchiert + vollständig befüllt, `card_status: "complete"`.
- [x] **Dokumentation aktualisiert** — `ARCHITECTURE.md`: delegate_script-Mechanismus (PC + tooluse als Sub-Runner) + Model-Card-Lifecycle-Sektion. `DEVELOPER_GUIDE.md`: `card_status`-Tabelle von `"stub"` auf `"draft"/"minimal"/"complete"` korrigiert. `README.md`: `make benchmark-auto` im Quickstart ergänzt.

### Tool Use Probe-Run — 5 Modelle Live + Code-Fixes (v3.15.0 — 25.05.26)
- [x] **Probe-Run** — 5 Modelle live gegen alle 6 Assets (Tavily web_search + http_fetch, mode=live). gpt-5-mini 76.5% [PRODUCTION], grok-4-fast-non-reasoning 74.2% [PRODUCTION], moonshotai/kimi-k2 73.6% [NOT_REC], qwen/qwen3-32b 72.9% [NOT_REC], gemma4:E4B 65.7% [NOT_REC]. Leaderboard: 11 Modelle.
- [x] **`tooluse_exporter.py` — `cost_usd="local"`** — `_LOCAL_DEPLOYMENT_TYPES` um `"open-weights"` erweitert. Open-Weights-Modelle zeigen `local` statt `0.0` im Leaderboard.
- [x] **gemma4:E4B fleet_group-Backfill** — `fleet_group=local_sovereign`, `sovereignty_gap=-7.28` nachgepflegt.
- [x] **Model Cards** — `gpt-4o.json`, `magistral-medium-latest.json`: `tooluse_tested_at` + Scoring-Felder gesetzt.

### Tool Use Bug-Fixes (v3.14.0 — 25.05.26)
- [x] **`utils/providers/anthropic.py` — `system`-Kwarg-Fix** — `system`-Feld aus `**kwargs` nicht extrahiert → stillschweigend verworfen → alle Anthropic-Modelle `retry_required=true`, Latenz verdoppelt, tooluse006 Timeout bei Opus 4.6. Fix: explizite `kwargs.get("system")`-Extraktion vor Temperature-Check.
- [x] **`benchmark_modules/tooluse/assets/tooluse003.yaml` v1.3.0** — `uncertainty_handling.unacceptable` ohne `acceptable_patterns` für httpbin.org-Kontext → Judge False-Positive (hallucination_detected=true für korrekte HTTP-Erklärungen). Fix: `acceptable_patterns`-Sektion mit 5 Einträgen.
- [x] **`scripts/core/unified_runner.py` — Token/Cost-Tracking** — `last_token_usage` (nur letzter API-Call) → `max(exec_result.tokens_used, client.last_token_usage)`. Multi-Call-Module zeigten falsche Token-Summe im Audit-Log. `isinstance`-Check für MagicMock-Sicherheit in Tests.
- [x] **Re-Runs (--force)** — Haiku 4.5 (75.0%), Opus 4.5 (79.2%), Sonnet 4.6 (79.0%), Opus 4.6 (80.0%) — alle `parse_attempts=1`. Leaderboard: 7 Modelle, Sovereignty Gap -10.9. 257/257 Tests grün.

### Phase-C Asset + Judge Hardening (v3.13.0 — 25.05.26)
- [x] **`tooluse006.yaml`** — Phase-C-Asset: Multilingual Search & German Synthesis. `web_search`, Zielsprache Deutsch, auch bei englischsprachigen Search-Results. Kalibriert (Sonnet 90, Hermes 90 nach Rubrik-Fix).
- [x] **`phase2_rubric`-Verdrahtung** — `_build_rubric_override()` in `test.py` serialisiert Asset-YAML-Rubrik als `rubric_override` an `runner.score()`. Rubrik war zuvor totes YAML.
- [x] **Hallucination Cap config-first** — `config/scoring.yaml → tool_use.hallucination.cap_hard: 20`. `ToolAdapterAudit.load_hallucination_cap()`. Cap-Anwendung nach Judge-Call in `test.py`.
- [x] **`tool_result_ignored`-Flag** — Boolean im CV-Block: content_usable=True + state=B2 → Modell ignorierte verwertbaren Tool-Output.
- [x] **`tooluse002`-Rubrik False-Positive-Fix** — `unacceptable` schränkte auf "Fakten hinzufügen die nicht im Fixture stehen" → korrekte Parameterwissen-Ergänzungen als Halluzination gewertet. Korrigiert auf "faktisch falsche Angaben".
- [x] **257/257 Tests grün** (7 neue Tests für `tool_result_ignored` + `language_consistency`).

### Tool Use Phase-A-Erweiterung (v3.12.0 — 24.05.26)
- [x] **`tooluse004.yaml`** — Phase-A: Tool Selection (web_search, kein URL-Target vorgegeben; Topic: LLM-Leaderboard auf Hugging Face).
- [x] **`tooluse005.yaml`** — Phase-A: URL Construction (fetch, URL muss selbst abgeleitet werden; Python-Wikipedia). Mock-Fixture (~1047 chars) in `cruciblemark-mcp/tools/mock_provider.py`.
- [x] **`parse_error_flag` → `retry_required`** — Umbenennung im gesamten Stack: `ToolUseIOManager`, `ToolUseExporter`, `tooluse_leaderboard.py`, alle Tests. Semantisch präziser.
- [x] **`methodology_notes.py`** — 7 deterministische Annotations-Templates für asset-spezifische Reviewer-Diagnosen.
- [x] **P1-Ceiling: 96.0** — (100+100+80+100+100)/5. 41 Modelle im Leaderboard nach Phase-A-Integration.
- [x] **Phase-A-Calibration** — MCP `http_fetch` → `fetch` Standard-Alignment. `_OVERLAP_WINDOW = 3` (B2-False-Positive-Fix). Mock-Excerpts auf ~250 Zeichen. `web.search`-Alias in `AUTHORIZED_TOOLS`. TIMEOUT_PER_MODEL 300→600s. 67 Tests grün. Verifikation claude-sonnet-4-6: Avg 85.2%, P1=96.

### Tool Use & Function Calling Benchmark-Modul (v3.10.0 – 23.05.26)
- [x] **`benchmark_modules/tooluse/`** — Vollständige Implementierung: `ToolUseTest` (erbt `BaseTest`), `ToolUseEvaluator` (Phase 1 Tool Execution + Phase 2 Synthesis Quality), `ToolUseIOManager` (Leaderboard CSV + Terminal-Summary), `constants.py`. Zwei-Phasen-Scoring: 50/50, Hallucination Penalty −100, Tool Call Bonus +10.
- [x] **`cruciblemark-mcp/server.py`** — FastAPI-basierter MCP-Server Port 8765. Mock-Modus (deterministisch) + Live-Modus (Tavily → DuckDuckGo). Health-Endpoint `/health`.
- [x] **`scripts/core/tooluse_exporter.py`** — `ToolUseExporter`: `finalize_model()` (Buffer-Pfad), `aggregate_from_benchmark_csvs()` (Produktionspfad), `calculate_sovereignty_gap()` (Formel: `local_avg − all_avg`), `get_summary()`. `_LOCAL_DEPLOYMENT_TYPES = {"localweights", "open-weights-cloud-available", "open-weights"}` (v3.15.0 erweitert). `cost_usd="local"` für diese Typen. `get_fleet_group()`.
- [x] **`scripts/tools/tooluse_leaderboard.py`** — Leaderboard-CLI mit Sovereignty Gap, Fleet Averages, Performance-Metriken.
- [x] **`scripts/analysis/generate_tooluse_report.py`** — Markdown-Reports pro Modell + Fleet Summary.
- [x] **`scripts/run_tooluse_benchmark.py`** — Batch-Runner mit interaktivem Wizard (Provider → Modell/Alle). MCP-Neustart pro Modell (`_restart_mcp()`). `--no-restart-mcp` als Opt-out. Timeout 300s pro Modell.
- [x] **`utils/mcp_health.py`** — MCP-Health-Check-Utility.
- [x] **Makefile** — 6 neue Targets. `mcp-start` idempotent (curl Health-Check). `mcp-stop` stale-PID-sicher (`kill ... 2>/dev/null || true`).
- [x] **Bug-Fixes:** Sovereignty Gap Vorzeichen (`local − all`). `tool_call_attempts` max statt sum (beide Aggregationspfade). GPT OSS 20B `supports_tool_use: false` (nicht installiert). Card-Key-Namen snake_case. `get_fleet_group()` akzeptiert `open-weights-cloud-available`.
- [x] **`print_run_summary_from_row()`** in `ToolUseIOManager` — feuert in Live-Runs aus `aggregate_from_benchmark_csvs()` (nicht nur im Buffer-Pfad).
- [x] **Model Card** `hf_co_bartowski_NousResearch_Hermes-4-14B-GGUF_Q4_K_M.json` — Pflichtfelder ergänzt (`display_name`, `size_class`, `deployment_type`, `model_version`, `vendor`).
- [x] **Dokumentation:** `docs/TOOLUSE_MODULE.md` (450 Zeilen, 14 Abschnitte), `benchmark_modules/tooluse/README.md` (Komplettrewrite), `docs/BENCHMARK_MODULES.md` (Tool Use Abschnitt), `benchmark_modules/tooluse/SCORING_STATUS.md`.
- [x] **Tests:** 212/212 grün. `test_calculate_sovereignty_gap` auf korrektes Vorzeichen aktualisiert.

### Architektur-Compliance-Refactoring: Provider-Registry, LanguageValidator, God-Script-Zerlegung (v3.9.0 – 23.05.26)
- [x] `utils/language_validator.py` (NEU) — `LanguageValidator`-Klasse kapselt DE/EN-Marker-basierten Mismatch-Check. Konstanten in `utils/constants.py` (`LANGUAGE_MIN_WORDS`, `LANGUAGE_EN_DE_RATIO`, `LANGUAGE_EN_MIN_COUNT`, `LANGUAGE_DE_MARKERS`, `LANGUAGE_EN_MARKERS`).
- [x] `scripts/core/unified_runner.py` — Inline-Language-Detection → `LanguageValidator`-Delegation. `120.0` → `TIMEOUT_DEFAULT`, `100` → `DEFAULT_MAX_SCORE`, lokales `TRUNCATION_THRESHOLDS`-Dict → importierte Konstante.
- [x] `benchmark_modules/political_compass/test.py` — Magic Numbers durch `PC_*`-Konstanten aus `core/constants.py` ersetzt (`PC_DEFAULT_NUM_RUNS`, `PC_MAX_REFUSAL_RETRIES`, `PC_RETRY_TEMPERATURES`, `PC_SLEEP_BETWEEN_REQUESTS`, `PC_SLEEP_AFTER_RESPONSE`, `PC_QUERY_TIMEOUT`).
- [x] `utils/scoring/llm_judge/judge_runner.py` — 5-Branch-Provider-If-Chain → `_PROVIDER_MODULES`-Registry + `importlib.import_module()`. `_ENV_KEY_MAP`-Dict statt If-Chain für API-Key-Validierung.
- [x] `scripts/analysis/review/` (NEU) — Package mit `metrics.py`, `risk_calculator.py`, `token_efficiency.py`, `audit_scanner.py`. `generate_review.py`: 1309 → ~200 Zeilen.
- [x] `benchmark_modules/reasoning_logic/core/constants/rubrics.py` (NEU) — `RUBRICS` + `DIMENSION_SCORE_THRESHOLDS` extrahiert aus `evaluators.py`.
- [x] `utils/model_utils.py` — `_param_b_to_size_class()` If-Kette → `_SIZE_CLASS_THRESHOLDS`-Tupel-Konstante.
- [x] **Bug:** `utils/providers/mistral.py` — `token_param_name` wurde in `_execute_with_token_fallback()` ignoriert (hardcoded `"max_tokens"`). Behoben.
- [x] **Ruff** — F401/F541 auto-fix (185 Issues), F841 manual (12 unused vars). Pylint Score: 9.37 → 9.99/10.


- [x] **`scripts/analysis/generate_model_cards.py`** — LLM-basierter Auto-Generator ersetzt durch schlanken Template-Generator. Kein API-Call, kein Config-Laden. `make model-cards MODEL=<id>` → JSON mit allen Pflichtfeldern als `"TODO"`, `size_class` automatisch berechnet, `_index.json` aktualisiert.
- [x] **`Makefile`** — Target `model-cards` vereinfacht. Alias `model-card` (Singular) ergänzt. `--provider`-Flag für lokale Modelle.
- [x] **Docs:** `DEVELOPER_GUIDE.md` (Card-Generierung-Sektion), `AUDIT_AND_METAREVIEW.md`, `USER_GUIDE.md`, `README.md` aktualisiert. Alle Versionsnummern → v3.8.2.

### Model Card Klassifikations-System & Reviewer-Prompt-Überarbeitung (v3.8.0 – 22.05.26)
- [x] **`benchmark_scores/model_cards/*.json`** — `use_case_primary` (`generalist`/`coding`/`reasoning`/`vision-language`/`agentic`), `parameter_architecture` (`dense`/`moe`), `context_window_k` (Kilotoken), `knowledge_cutoff` (`YYYY-MM`) als Pflichtfelder in alle ~77 Cards migriert.
- [x] **`config/classification_taxonomy.json`** (NEU) — SSoT für Taxonomy mit `label`, `description` und `reviewer_guidance` pro Wert. Zwei Sektionen: `use_case` (5 Werte) + `size_class` (6 Werte).
- [x] **`scripts/dev/migrate_use_case_primary.py`** (NEU) — Idempotentes Migrationsskript mit `--dry-run`-Support. Zuweisung nach Prioritätskaskade: `primary_focus=coding` → `"coding"`, Vision/Multimodal-Tags → `"vision-language"`, Thinking-Tags → `"reasoning"`, Agentic-Tag → `"agentic"`, sonst `"generalist"`. Thinking-Optional bleibt `"generalist"`.
- [x] **`scripts/dev/migrate_context_fields.py`** (NEU) — Idempotentes Migrationsskript für `context_window_k` + `knowledge_cutoff`. Liest Werte aus `benchmark_config.yaml`-Beschreibungsfeldern oder setzt sinnvolle Defaults.
- [x] **`utils/model_utils.py` — `get_use_case_primary()`** — Neue Hilfsfunktion. `card_data`-Parameter optional. Fallback immer `"generalist"` — kein None, kein Exception.
- [x] **`scripts/analysis/generate_review.py` — `_format_classification_context()`** — Rendert `classification_taxonomy.json` als Markdown-Tabellen. Hebt `use_case_primary` und `size_class` des aktuellen Modells mit `▶` hervor. Injektion als `{use_case_classification_context}` nach Modell-Identitäts-Block.
- [x] **`config/meta_reviewer_prompt.yaml`** — 3 neue Prompt-Regeln: (1) Gedankenstrich max 2–3 im gesamten Artikel, (2) Fachbegriffe im Kontext erklären (Zielgruppe: Nicht-Experten, nicht ML-Ingenieure), (3) keine internen Test-IDs im Review-Text — Modulbeschreibung stattdessen. Test-ID-Referenzen aus allen Diagnostik-Blöcken entfernt.
- [x] **Reviewer-Wettbewerb** — Claude Sonnet 4.6 / Gemini 3.1 Pro / GPT-5.4 auf identischen Grok-3-Rohdaten. Ergebnis: GPT-5.4 gewinnt (1 Gedankenstrich gesamt, stärkste Zugänglichkeit, "Löschzug nach Lackfarbe"-Metapher). Claude bleibt Standard in `benchmark_config.yaml`. Gemini: zu kurz, fehlende Pflichtstruktur.
- [x] **`benchmark_config.yaml` — `llm_review`** — `max_tokens` von 8192 auf 32768 erhöht (Rohdaten pro Modell: 25–35k Wörter). Reviewer-Komparativen auskommentiert (Claude/Gemini/GPT-5.4).
- [x] **`docs/blog_entwurf_reviewer_experiment.md`** (NEU) — Blog-Entwurf für cruciblemark.com/magazine: Zufälls-qwen2.5vl-Benchmark → SSOT-Problem → 3-Säulen-Card-Überarbeitung → Reviewer-Wettbewerb → 3 Erkenntnisse. Zielgruppe Nicht-Experten, Fachbegriffe erklärt.
- [x] **Docs:** `docs/MODEL_CLASSIFICATION.md` v3.0.0 (neue Sektionen use_case_primary, parameter_architecture, context_window_k). `docs/AUDIT_AND_METAREVIEW.md` (Card-Felltabelle, neue Prompt-Regeln, use_case_classification_context). `docs/DEVELOPER_GUIDE.md` (Model Card Schema Pflichtfelder, Migrationsskripte, `get_use_case_primary()`). `memory-bank/activeContext.md` + `progress.md` aktualisiert.

### Pricing SSoT Migration: Model Cards als primäre Preisquelle (v3.7.5 – 22.05.26)
- [x] `benchmark_scores/model_cards/*.json`: `input_price_per_1m` + `output_price_per_1m` (USD/1M Tokens) in alle 53 API-Cards migriert. Konvertierung: `per_1k × 1000`. Model Card = primäre Preisquelle für das Framework.
- [x] `config/cost_limits.yaml`: Von ~25 Modelleinträgen auf 6 Legacy-Einträge reduziert (nur Modelle ohne Card: MiniMax Cloud, Kimi-K2.5 Cloud, GLM-5 Cloud, Llama-3.1-8B, Kimi-K2-Instruct, Groq Daily Budget).
- [x] `scripts/leaderboard/score_calculator.py` — `_build_price_lookup()`: Card-First-Lookup; liest `output_price_per_1m` aus Model Card JSONs. `cost_limits.yaml` als Legacy-Fallback für kartenlose Modelle.
- [x] `utils/cost_tracker.py` — `calculate_cost()`: 3-Tier-Kaskade: LiteLLM → Model Card → `cost_limits.yaml` Legacy.
- [x] `scripts/dev/sync_cost_limits.py`: Card-First-SSoT; `--fix` schreibt Platzhalter nur für Modelle ohne Card.
- [x] `scripts/dev/migrate_prices_to_cards.py` (NEU): One-Time-Migrationsskript für Audit. `_card_path()`-SSoT, regex für `-latest`-Aliases und Datumssuffixe.
- [x] Neue Cards: `mistral-medium-3-5` (EU, Modified MIT, 256k), `mistral-small-2603` / Mistral Small 4 (24B, Apache-2.0), `qwen/qwen3.6-plus`, `qwen/qwen3.7-max` (CN, proprietary, BSI-Risiko: high). Card-Renames: `mistral-medium-3_5` → `mistral-medium-3-5`, `mistral-small-4` → `mistral-small-2603`.
- [x] 3 neue Reviews: `docs/reviews/mistral-medium-3-5/`, `docs/reviews/mistral-small-2603/`, `docs/reviews/qwen2.5vl_7b/`.
- [x] Docs: `USER_GUIDE.md`, `ARCHITECTURE.md`, `SCORING_METHODOLOGY.md` auf card-first Pricing aktualisiert.

### Architektur-Compliance-Refactoring: `_find_card()`, `WEIGHTS_TIER_DISPLAY`, `_BLOCK_META` (v3.7.4 – 21.05.26)
- [x] `utils/model_utils.py` — `_find_card(card_dir)`: Neuer optionaler Parameter `card_dir: Path | None = None`. Rückwärtskompatibel; `None` greift auf `CARD_DIR`-Konstante zurück.
- [x] `utils/model_utils.py` — `WEIGHTS_TIER_DISPLAY`: Tier-Mapping als öffentliche Konstante exportiert. Kein Duplikat mehr in `web_export.py`.
- [x] `scripts/web_export.py` — `load_model_card()`: Delegiert Pfad-Lookup an `_find_card(card_dir=card_dir)` (SSoT). ~40 Zeilen.
- [x] `scripts/web_export.py` — `_BLOCK_META`: Hardcodiertes Dict entfernt. `_load_pc_block_meta(config_path)` liest Block-Metadaten aus `benchmark_modules/political_compass/config.yaml`.
- [x] `benchmark_modules/political_compass/config.yaml`: `blocks:`-Sektion (9 Block-Einträge: ID, Label, Achse) als YAML-SSoT aufgenommen.

### Anti-God-Script-Sanierung: `scripts/web_export.py` (v3.7.3 – 21.05.26)
- [x] `main()` von ~490 auf ~80 Zeilen reduziert. 9 Top-Level-Hilfsfunktionen extrahiert (vollständige Type Hints, mypy-kompatibel).
- [x] `_resolve_dir()`, `_setup_output_dirs()`, `_load_sources()`, `_build_pc_lookups()`, `_export_model_files()` extrahiert.
- [x] `_build_leaderboard_entry()`, `_lookup_pc_row()`, `_build_compass_entry()`, `_write_top_level_outputs()` extrahiert.
- [x] `load_csv_with_fallback()`: Exception-Handling spezifiziert (`OSError | pd.errors.ParserError`). `ARCHITECTURE.md` aktualisiert.

### Web-Export Date Fields: benchmark_run_at, report_published_at, last_activity_at (v3.7.2 – 16.05.26)
- [x] `scripts/web_export.py`: `_build_benchmark_run_dates()` liest `outputs/runs/results_*_YYYYMMDD_*.json`, extrahiert Datum aus Dateiname + `model`-Feld aus JSON → `model_id → earliest_date` Map.
- [x] `scripts/web_export.py`: `_review_date_range()` parst `review_YYYYMMDD_*.md` Dateinamen → `(published_at, updated_at)`. Kein mtime — Filename ist SSOT.
- [x] 4 neue Felder im `leaderboard`-Block: `benchmark_run_at`, `report_published_at`, `report_updated_at` (null wenn = published_at), `last_activity_at` (max aller Datumssignale).

### Code-Quality & Bug-Fix: `_find_card()` SSOT, Provider-Config-Lesung, Exporter-Lint (v3.7.1 – 15.05.26)
- [x] `scripts/analysis/generate_review.py`: 4 × naive `cards_dir / f"{re.sub(...)}.json"` → `_find_card(model_id)`. Lokale `import re` entfernt.
- [x] `scripts/analysis/generate_model_cards.py`: Unused `_safe_name` Import entfernt (Pylint W0611).
- [x] `scripts/web_export.py` — `build_provider_map()`: `_FALLBACK_NAMES`-Hardcode durch dynamisches Lesen aus `benchmark_config.yaml` ersetzt. Guard `"name" not in prov_val` schützt vor Settings-Blöcken als Fake-Provider.
- [x] `scripts/leaderboard/exporter.py`: `# type: ignore[call-overload]` für pandas `apply`-Overloads. `import re as _re` vor `if`-Block (Pylint E0606).
- [x] `docs/ARCHITECTURE.md`: `is_reasoning_model_from_card()` Lookup auf `_find_card()` aktualisiert.

### Modell-Kategorisierungs-SSOT: 3-Tier `weights_license_tier` (v3.7.0 – 14.05.26)
- [x] `get_model_category()` in `utils/model_utils.py`: Card-First-Lookup via `_find_card()` → `weights_license_tier` → Display-String. Drei gültige Tiers: `Proprietär` / `Restricted Weights` / `Open Weights`.
- [x] `scripts/web_export.py`: `type`-Feld aus Model Card zur Export-Zeit abgeleitet; Legacy-CSV-Werte werden überschrieben ohne Rebuild. `model_category` im PC-Export ebenfalls Card-basiert.
- [x] `benchmark_modules/political_compass/core/io_manager.py`: Inline-Kategorie-Logik durch `get_model_category()`-Aufruf ersetzt.
- [x] `scripts/leaderboard/data_loader.py`: Fallback-Funktion auf 3-Tier-Strings vereinfacht.
- [x] Frontend `model-types.js`: 3-Tier-SSoT (`isCommercial`, `isRestrictedWeights`, `isOpenWeight`, `CHART_SERIES_CONFIG` 3 Einträge). Alle Chart-Module migriert: `political-compass-chart.js`, `politicalCompass.11tydata.js`, `leaderboard-chart.js`, `scoreboard-table.js`, `shift-chart.js`.
- [x] SCSS: `--cm-chart-label-restricted: $cm-amber`, Badge-Styles `cm-model-badge--restricted` + `--restricted-sub`.
- [x] Docs: `CLAUDE.md` Critical Pitfalls, `ARCHITECTURE.md` Web Export Pipeline, `memory-bank/systemPatterns.md` neuer Pattern-Block.

### Archetyp-Umbenennung: Stoiker + Narr (v3.6.5 – 09.05.26)
- [x] `Das Schaf` → `Der Stoiker`, `Chamäleon` → `Der Narr`. Finale vier Bezeichnungen: Stoiker / Wolf im Schafspelz / Die Chimäre / Der Narr. Nur Labels geändert, Logik/Schwellwerte unverändert. CSV-Backfill 76 Zeilen, Web-Export 72/72.

### Archetyp-Umbenennung: Chimäre + Das Schaf, Chamäleon-Threshold (v3.6.4 – 08.05.26)
- [x] `Offener Wolf` → `Die Chimäre` (hoher Shift + Quadrantenwechsel). `Echtes Schaf` → `Das Schaf`. `classify_behavior_archetype()` um `forced_x`/`forced_y` erweitert. CSV-Backfill 76 Zeilen. Neue Verteilung: Schaf 54, Wolf 18, Chimäre 2, Chamäleon 2.
- [x] `ARCHETYPE_CHAMELEON_FLIP_THRESHOLD` von 50 → 35 (Operator `>` → `>=`). Empirisch kalibriert (P90=27.2 %, n=76). Chamäleon: gemini-3-flash-preview + dolphin-mistral-nemo.

### behavior_archetype, vendor, Modellnamen-Normalisierung (v3.6.3 – 08.05.26)
- [x] `behavior_archetype`-Feld im PC-Leaderboard + Web-Export. Modellnamen-Normalisierung (Datumssuffix-Strip `-YYYYMMDD`/`-MMDD`). 8 CSV-Einträge bereinigt, 76 Zeilen backgefüllt.
- [x] `vendor`-Feld in allen 72 Model Cards (13 Werte). Leaderboard-Detailed-CSV Vendor-Spalte.

### model_id SSOT, benchmark-auto Fix, supports_tool_use, 3 Grok-Modelle (v3.6.0 – 04.05.26)
- [x] **`scripts/leaderboard/exporter.py` — `model_id`-Spalte:** Rohe Config-ID in `benchmark_leaderboard_detailed.csv` als SSOT.
- [x] **`scripts/web_export.py` — Dir-Lookup via `model_id`:** Fallback 1: Date-Suffix-Strip. Fallback 2: Suffix-Match. 69/69 Coverage.
- [x] **`scripts/core/benchmark_auto.py` — `COMPLETED_STATUSES`:** `language_mismatch`/`truncated`/`refusal` nicht mehr retried.
- [x] **`utils/benchmark_utils.py` — P95-Akkumulation:** Regex-Fix. 154 Dateien bereinigt.
- [x] **`supports_tool_use`** in 77 Model Cards migriert. Prompt-Dokumentation aktualisiert.
- [x] **3 neue Grok-Modelle** in `benchmark_config.yaml` + `cost_limits.yaml`.
- [x] **Docs:** `ARCHITECTURE.md`, `USER_GUIDE.md`, `systemPatterns.md`, `PROJECT_STATUS.md`, `CHANGELOG.md`, `README.md` synchronisiert.

### size_class Card-Lookup, empty_response_context, Model-Card-Korrekturen (v3.5.9 – 24.04.26)
- [x] **`utils/model_utils.py` — `get_model_size_class()` Priority-Kaskade:** (1) Card-Lookup SSoT → (2) Ollama-Colon-Tag case-insensitive → (3) Dash/Dot-Suffix-Regex → Fallback `"Frontier"`. Hilfsfunktionen `_param_b_to_size_class()` + `_SIZE_CLASS_VALID`. Leaderboard: Nano=5, Edge=5, Desktop=7, Workstation=4, Server=1, Frontier=40.
- [x] **`scripts/analysis/generate_review.py` — `_build_empty_response_context()`:** Liest alle 3 Benchmark-CSVs, filtert `response_length=0 + status=success`, liefert Asset-IDs als Kontext-Block an Meta-Reviewer. Nur aktiv für `review_type == "benchmark"`.
- [x] **`config/meta_reviewer_prompt.yaml` — `{empty_response_context}`:** Neuer Pflicht-Block nach `constraint_violations_context`. Lautlose Verweigerungen werden als Qualitätsmerkmal dokumentiert.
- [x] **`scripts/analysis/generate_model_cards.py` — Auto-`size_class`:** Beide Pfade (`_generate_card()` + `_create_minimal_card()`) schreiben `size_class` via `get_model_size_class()`. Bestehende Felder werden nicht überschrieben.
- [x] **Model-Card-Korrekturen:** 6 Cards manuell korrigiert (Desktop/Server/Workstation/Nano). Slug-Mismatch `CognitiveComputations/dolphin-mistral-nemo:latest` → `CognitiveComputations_dolphin-mistral-nemo_latest.json` behoben.
- [x] **Dokumentation:** `README.md`, `PROJECT_STATUS.md`, `CHANGELOG.md`, `REF_TODO.md`, `scripts/web_export.py`, `memory-bank/`, `.github/copilot-instructions.md` (neuer Fallstrick: size_class Card-Slug-Mismatch) synchronisiert.

### ThinkingProbe & Card-First Workflow (v3.5.8 – 23.04.26)
- [x] **`utils/model_utils.py` — `ThinkingProbeResult` & `probe_thinking_model()`:** Dataclass mit `detected: bool`, `evidence: str`, `confidence: Literal["high","medium","low"]`. Signal A: `<think>`/`<thinking>`/`<thought>`-Tags in Response-Body. Signal B: `reasoning_tokens > 0` in API-Metadaten. Signal C (Response-Länge) bewusst nicht implementiert (False-Positive bei Instruction-Following-Modellen).
- [x] **`utils/model_utils.py` — `is_reasoning_model_from_card()`:** Card-First-Lookup für `thinking_probe_detected`-Feld. Dateinamen via `re.sub(r'[:/.\s]', '_', model_id)` auflösen — konsistent mit `_safe_name()` in `generate_model_cards.py`. Gibt `None` bei fehlender Card oder fehlendem Feld zurück.
- [x] **`utils/model_utils.py` — `is_reasoning_model()` Hierarchie:** Card-Lookup hat Vorrang. Neuer Trigger `kimi-k2` ergänzt.
- [x] **`scripts/core/unified_runner.py` — `_ensure_model_card()`:** Vor erstem Run eines Modells: Card + Feld vorhanden → Skip; Feld fehlt → Probe → Feld schreiben; keine Card → Probe → Minimal-Card erstellen (`card_status: minimal`); Probe-Fehler → RuntimeError (kein stilles Skip).
- [x] **`scripts/analysis/generate_model_cards.py` — `_create_minimal_card()`:** Erstellt Card ohne LLM-Aufruf mit `card_status: minimal`. `_generate_card()` setzt `card_status: complete` und bewahrt bestehende Probe-Felder bei `--force`.
- [x] **`scripts/tools/probe_thinking.py`** (NEU): Standalone-CLI. `--model <id>`, `--missing` (Batch: alle ohne Feld), `--all` (Force-Rescan). `_infer_provider()`: Config-Lookup → `/` im ID → `openrouter` → sonst `ollama`. Batch-Modus bricht bei Einzelfehlern nicht ab (`sys.exit(1)` nur bei `--model`).
- [x] **Makefile:** `probe-thinking` (`MODEL=<id>` required) + `probe-all-thinking` (`--missing`) als neue `.PHONY`-Targets.
- [x] **Bugfix `is_reasoning_model_from_card()` — `_safe_name()`:** War `replace('/', '_')` → ist jetzt `re.sub(r'[:/.\s]', '_', model_id)`. Behebt: `gemini-2.5-flash` fand `gemini-2_5-flash.json` nicht.
- [x] **Bugfix `probe_thinking.py` — `_infer_provider()`:** War Substring-Matching (`"deepseek" in model_id`) → ist jetzt `/`-Präsenz-Heuristik. Behebt: `deepseek-r1:8b` (lokal) wurde fälschlich via OpenRouter geprobt.
- [x] **Bugfix Batch-Exit:** `sys.exit(1)` nur noch bei explizitem `--model`-Fehler. `--missing`/`--all` bricht bei Einzelfehlern nicht ab.
- [x] **26 API-Model-Cards retroaktiv** via `make probe-all-thinking` mit Probe-Feldern versehen. 25 Offline-Ollama-Modelle: graceful failure.
- [x] **o1/o3-mini/o4-mini:** Manuelle Overrides (`thinking_probe_detected: true`, `thinking_probe_manual_override: true`) — OpenAI exponiert Reasoning-Tokens nicht im API-Response.
- [x] **`moonshotai/kimi-k2.5`:** Neue Minimal-Card via Card-First-Hook während Re-Run erstellt.
- [x] **Re-Runs:** 18 `gemini-2.5-flash`-Zeilen in `commercial_models_benchmark.csv` (code_quality 5, cultural_intelligence 5, ux_writing 4, documentation_quality 2, content_transformation 2) + 3 Zeilen `gemini-2.5-pro` gelöscht. 3 `kimi-k2.5`-Zeilen in `cloud_models_benchmark.csv` gelöscht + re-run.
- [x] **Dokumentation:** `CHANGELOG.md` v3.5.8, `docs/ARCHITECTURE.md`, `docs/DEVELOPER_GUIDE.md` (v3.2.0), `docs/MODEL_CLASSIFICATION.md`, `memory-bank/systemPatterns.md`, `memory-bank/activeContext.md`, `memory-bank/progress.md`, `.github/copilot-instructions.md` (3 neue Fallstricke: Signal-C-Verbot, `_safe_name()`-Konsistenz, `_infer_provider()`-`/`-Heuristik, OpenAI-o-Series-Override).

### SSoT Token-Budget, Gemini-2.5 Reasoning-Fix, Judge-Verbosity-Penalty, Refusal-Metadaten (v3.5.7 – 23.04.26)
- [x] **`utils/model_utils.py` — `resolve_token_budget()`:** Zentrale SSoT-Funktion für Token-Budget-Berechnung. Gibt `(effektives_budget: int, is_reasoning: bool)` zurück. Alle drei Provider (`openai.py`, `openrouter.py`, `mistral.py`) delegieren dorthin. Behebt fehlende `elif is_reasoning and tokens < 10000: tokens = 25000`-Branch in `mistral.py`.
- [x] **`benchmark_config.yaml` — `token_param_name` pro Provider:** Fünf Provider-Blöcke (`mistral`, `openai`, `groq`, `xai`, `openrouter`) mit `token_param_name: max_tokens` bzw. `max_completion_tokens`. Provider lesen via `_provider_cfg.get("token_param_name", "<fallback>")`.
- [x] **`utils/model_utils.py` — `gemini-2.5` Reasoning-Trigger:** `is_reasoning_model()` erkennt `gemini-2.5-flash`/`gemini-2.5-pro`. Elevated Budget: ux_writing 8.000 statt 500, documentation_quality 12.000 statt 6.000 Tokens. Behebt 12–18%-Scores durch Thinking-Token-Budget-Erschöpfung.
- [x] **`utils/scoring/llm_judge/judge_prompt_builder.py` — `token_budget_context`:** Neuer Parameter `token_budget_context: Optional[Dict[str, int]]`. Injiziert `TOKEN BUDGET NOTE` in System-Prompt: sichtbarer Output > 2× Standard-Budget mit Padding/Wiederholung → −1 Punkt `output_quality`.
- [x] **`utils/scoring/llm_judge/judge_runner.py` — Pass-through:** `token_budget_context`-Parameter zu `score()` ergänzt und an `build_prompts()` weitergegeben.
- [x] **`utils/scoring/judge_evaluator.py` — Auto-Injektion:** Liest `standard`/`elevated`-Budget aus Config und setzt `kwargs["token_budget_context"]` automatisch für Reasoning-Modelle.
- [x] **`scripts/core/unified_runner.py` — Refusal-Metadaten:** Antworten < 15 Zeichen setzen `refusal_flag=True`, `refusal_type="content_safety"`, `refusal_note` im Result.
- [x] **`utils/result_manager.py` — CSV-Schema:** `refusal_flag`, `refusal_type`, `refusal_note` in `_get_updated_fieldnames()` als neue Pflicht-Spalten registriert.
- [x] **Dokumentation:** `CHANGELOG.md` v3.5.7, `docs/ARCHITECTURE.md` (SSoT-Abschnitt, Refusal-Metadaten, Trigger-Liste), `docs/SCORING_METHODOLOGY.md` (Verbosity-Penalty, Refusal-Dokumentation), `.github/copilot-instructions.md` (3 neue Fallstricke), `memory-bank/`.

### OpenRouter Reasoning-Token-Tracking (v3.5.6 – 23.04.26)
- [x] **`utils/model_utils.py` — `minimax-m2` Reasoning-Trigger:** `is_reasoning_model()` um `"minimax-m2"` ergänzt. OpenRouter-Provider setzt 5× Token-Budget (~40.000 Tokens) für alle `minimax-m2.*`-Varianten — verhindert `finish_reason: length` mit leerem Output.
- [x] **`schemas/result.py` — `reasoning_tokens`-Feld:** Neues `Optional[int]`-Feld in `BenchmarkResult` zwischen `finish_reason` und `token_limit_cutoff`. Wird als neue CSV-Spalte persistiert.
- [x] **`utils/providers/openrouter.py` — Extraktion:** `completion_tokens_details.reasoning_tokens` aus API-Response → `last_response_metadata["reasoning_tokens"]`.
- [x] **`utils/base_runner.py` — Propagation:** `reasoning_tokens` aus `client.last_response_metadata` → `exec_result.reasoning_tokens` → Result-Dict.
- [x] **`utils/benchmark_utils.py` — Audit-Log-Erweiterung:** Token-Header zeigt `(davon N Reasoning-Tokens, die intern verbraucht wurden)`. Neuer `[!WARNING]`-Block bei `reasoning_tokens > 0 AND token_limit_cutoff=True` mit Erklärung des Budget-Konflikts.
- [x] **`utils/scoring/judge_evaluator.py` — Pass-through:** `reasoning_tokens=result.get("reasoning_tokens")` an `save_audit_log()` weitergegeben.
- [x] **2 ungültige CSV-Zeilen gelöscht:** `minimax/minimax-m2.7` × `cli005` + `ux_writing_005` aus `cloud_models_benchmark.csv` (resp_len=0, finish_reason: length — Budget-Erschöpfung vor Fix).
- [x] **`Makefile` — `clean-bak`-Target:** Entfernt `.bak_*`-Dateien aus `benchmark_scores/`. `backup`-Target um `docs/reviews/`, `docs/audits/`, `config/`, `memory-bank/` erweitert, `.bak_*` excludiert.
- [x] **Dokumentation:** `docs/ARCHITECTURE.md` (Provider-Tabelle + Besonderheiten-Spalte + Reasoning-Budget-Abschnitt), `memory-bank/systemPatterns.md` (neuer Abschnitt), `.github/copilot-instructions.md` (Fallstrick).

### Asset-Limit-Kalibrierung & Fleet-Audit (v3.5.3 – 21.04.26)
- [x] **`ux_writing/assets/asset_005_microcopy_audit.yaml` — Limit-Kalibrierung:** `max_expected_words` 150 → 350 (P25 der Ist-Längen × 1.20 = 337, aufgerundet auf 350). Prompt-Text ergänzt: `"Maximale Länge: 350 Wörter gesamt (Analyse + Tabelle). Sei präzise – jeder Satz zählt."` — Modell war zuvor nie über das Limit informiert. 50/52 Modelle verletzten das alte Limit.
- [x] **`content_transformation/assets/asset_003_glossary_simplification.yaml` — Limit-Kalibrierung:** `max_expected_words` 150 → 250 (P25 = 210 W × 1.20 = 252 → 250). Format-Hinweis `"Max 150 Wörter"` → `"Max 250 Wörter"` synchronisiert. 29/52 Modelle verletzten das alte Limit.
- [x] **`content_transformation/assets/asset_004_video_script_tutorial.yaml` — Limit-Kalibrierung:** `max_expected_words` 600 → 900 (P25 = 789 W × 1.20 = 947 → 900). Format-Range `"400-600 Wörter"` → `"600-900 Wörter"` synchronisiert. Min-Ist aller 52 Modelle war 742 W.
- [x] **156 CSV-Zeilen gelöscht:** ct_003/ct_004/ux_005-Einträge aus allen 3 Benchmark-CSVs (75 + 42 + 39). Trigger für automatischen Re-Run.
- [x] **156 Audit-Log-Dateien gelöscht:** Alle `*/ux_writing_005.md`, `*/content_transformation_003.md`, `*/content_transformation_004.md` aus `outputs/audit_logs/`.
- [x] **Fleet-Scan (52 Modelle × 37 Tasks):** Alle Tasks auf strukturelle Limit-Fehler analysiert. Befund: 3 isolierte Fehler (behoben). `ux_writing_003` (per-Step-Limit korrekt), `content_transformation_005` (abschnittsbezogenes Limit, `keyword_presence` begründeter Trade-off) und 34 bewusst limit-lose Tasks.

### Code-Qualität, Terminologie & Block-7.9-Dokumentation (v3.5.2 – 21.04.26)
- [x] **`scripts/core/unified_runner.py` — Pylint W1309:** `f`-Prefix aus String ohne Interpolation entfernt (Zeile 511).
- [x] **`utils/providers/base.py` — Pylint W0719:** `raise Exception(...)` → `raise RuntimeError(...)`.
- [x] **`benchmark_modules/political_compass/core/audit_logger.py` — Pylint C0206:** `for _q_id in hydrated_responses:` → `for _q_id, _q_data in hydrated_responses.items():`. Beispieltext `repressiv-nationalistisch` → `repressiv-reaktionär`.
- [x] **`benchmark_modules/political_compass/core/evaluators.py` — Mypy annotation-unchecked:** `__init__(self) -> None` in `ExtremismWatchdog` und zweiter Klasse ergänzt.
- [x] **`benchmark_modules/political_compass/config.yaml` — Skalen-Label:** `Nationalistisch` → `Reaktionär` (X-Achse, Range 4.4–7.4).
- [x] **`docs/POLITICAL_COMPASS_KONZEPT.md` — Block 7.9:** Neuer Abschnitt 7 „Die Parolen-Extremismus-Sonde" mit Konzept, Asset-Tabelle (11 Assets), 80/20-Koordinatenformel und Hard-Refusal-Interpretationshinweis.

### Gemini Daily-Quota Fast-Fail (v3.5.1 – 17.04.26)
- [x] **`utils/providers/base.py` — `retry_delay`-Schwellenwert:** `retry_delay > 300 s` aus Gemini-API-Antwort gilt als Tages-Quota-Erschöpfung (Google Daily Quota, Reset Mitternacht Pacific). Statt 7,6 h zu schlafen: Fast-Fail mit `exceeded your current quota`-Exception → `_quota_exhausted = True` → sauberer Checkpoint-erhaltender Abbruch.
- [x] **`config/rate_limits.yaml` — `max_retry_delay_seconds: 300`:** Schwellenwert als dokumentierter Config-Wert eingetragen.

### PC Token-Asymmetrie-Analyse & Bias-Reviewer-Restrukturierung (v3.5.0 – 17.04.26)
- [x] **`utils/llm_client.py` — `last_output_tokens`:** `self.last_output_tokens = 0` vor jedem API-Call, `self.last_output_tokens = output_tokens` nach Kosten-Tracking (nur wenn Wert verfügbar). Liefert Output-Tokens (Ollama `eval_count`) ohne Nachparsing.
- [x] **`benchmark_modules/political_compass/test.py` — `output_tokens` im Checkpoint:** Live-Pfad nutzt `getattr(llm_client, "last_output_tokens", 0)`; Resume-Pfad schreibt `None` — semantisch trennbar von echter Null.
- [x] **`benchmark_modules/political_compass/core/audit_logger.py` — Section 2.6 Token-Asymmetrie:** Neuer Audit-Log-Abschnitt, nur bei `verification_mode=True`. Primär: echte `output_tokens` aus Checkpoint. Fallback: Zeitproxy mit `Hardware-abhängige Schätzung`-Label. Flags: `ELABORATION_SPIKE` (Forced > +50 %), `CAPITULATION_DROP` (Forced < −40 %). None-sicherer `(... or 0) > 0`-Filter, Coverage-Warnung bei partiellen Daten.
- [x] **`config/meta_reviewer_prompt.yaml` — Prompt-Architektur:** `{model_card_context}` vor Pflichtstruktur verschoben (sequenzielles LLM-Lesen). Drei offene Leitfragen → eine präzise Einzel-Instruktion. Section-2.6-Verzahnungs-Instruktion: Token-Befund als Dimension der Schattenmetriken (nicht isolierter Absatz). YAML-Kommentar vor `bias_reviewer:` dokumentiert Legacy/Neu-Lauf-Unterschied und Re-Run-Prioritäten.
- [x] **12 Legacy-Audit-Logs retroaktiv gepflegt:** Alle PC-Anomaly-Modelle (Shift > 1.0) aus initialem Run erhalten Section 2.6 mit Zeitproxy und `Hardware-abhängige Schätzung`-Label. Zero-Write-Regel greift — historischer Record vollständig.
- [x] **`docs/AUDIT_AND_METAREVIEW.md`:** Neuer Abschnitt "Section 2.6 Token-Asymmetrie" mit Primär-/Fallback-Modus, Flag-Schwellenwerten, Thinking-Modell-Einschränkung, retroaktiver Legacy-Notiz.
- [x] **`docs/POLITICAL_COMPASS_KONZEPT.md`:** Neues Kapitel 5 "Schattenmetriken" (Section 2.5 Standardabweichung, Section 2.6 Token-Asymmetrie, Flag-Tabelle, Kombinations-Interpretation).

### PC Budget-Exhaustion-Guard & Daten-Hygiene (v3.4.7 – 16.04.26)
- [x] **`benchmark_modules/political_compass/test.py` — Budget-Exhaustion-Erkennung:** Exception-Handler im Query-Loop setzt `self._quota_exhausted = True` bei Budget/Quota-Keywords (`quota`, `budget`, `billing`, `credit`, `payment`, `insufficient_funds`, ...). Logger-Warning statt stiller Absorption.
- [x] **`utils/base_runner.py` — Quota-Flag-Propagation:** `execute_batch_module()` prüft `getattr(test, "_quota_exhausted", False)` nach `test.execute()` und setzt `self.provider_quota_exhausted = True`. Gibt `[]` zurück — kein korruptes All-Zero-Ergebnis mehr im Leaderboard.
- [x] **`benchmark_modules/political_compass/core/io_manager.py` — `cost`-Spalte entfernt:** `fieldnames`-Liste und `row`-Dict bereinigt. Interne `total_cost`-Berechnung in `test.py` für Audit-Log erhalten.
- [x] **`config/meta_reviewer_prompt.yaml` — `bias_reviewer`-Prompt:** Neuer `bias_reviewer:`-Key mit 4300-Zeichen-System-Prompt für politische Bias-Analyse ergänzt.
- [x] **`scripts/web_export.py` — `inference_provider`-Feld:** `leaderboard.json` enthält jetzt `inference_provider` pro Eintrag.
- [x] **PC-Leaderboard bereinigt:** 34 → 13 Zeilen (21 März-Einträge mit `polarity_flip_rate = 0.0` entfernt). 21× `Political Bias` → `Pending` in `benchmark_leaderboard.csv`.

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

### Technische Schulden (Code-Qualität)

#### refactor(model_utils): God-Script aufteilen
- [ ] **`utils/model_utils.py` (1801 Zeilen, 13 inhaltliche Domänen)** verletzt die "keine God-Scripts"-Architektur-Regel. Diagnose: 2026-06-10 Code-Review.
- [ ] **Vorgeschlagene Module:**
  - `utils/card_paths.py` — `_safe_name`, `_card_path`, `_find_card`, `build_card_id`, `resolve_canonical_model_id`, `enforce_card_first`
  - `utils/thinking_probe.py` — `_THINK_TAGS`, `_PROBE_PROMPTS`, `_COT_FAMILY_MAP`, `ThinkingProbeResult`, `probe_thinking_model`, `classify_cot_marker_family`, `resolve_effective_thinking`, `_is_override_active`
  - `utils/token_budget.py` — `resolve_token_budget`, `is_reasoning_model`, `is_reasoning_model_from_card`, `is_thinking_optional_from_card`
  - `utils/model_identity.py` — `get_model_identity`, `get_model_category`, `get_model_version`, `get_model_size_class`
  - `utils/model_utils.py` bleibt als Re-Export-Layer (kein Breaking Change an bestehenden Imports)
- [ ] **Vorgehen:** Module für Modul splitten, beginnen mit `thinking_probe.py` (stärkstes in-sich-geschlossenes Cluster). Nach jedem Split: 786 Tests grün verifizieren.
- [ ] **Scope:** ~40–60 Dateien haben `from utils.model_utils import X`-Statements. Re-Export-Layer macht Migration graduell.

---

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

**Last Updated:** 2026-06-20 **Version:** 4.10.0 (Web-Export Nullwert-Entfernung + Card-Research Force-Run) **Nächster Meilenstein:** v5.0.0 / Nächster Feature-Release
