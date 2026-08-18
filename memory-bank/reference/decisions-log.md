# Decisions Log

Architekturentscheidungen und Release-Meilensteine seit v3.x.
Hot-Context (systemPatterns.md) zeigt nur die aktuell gültigen Patterns.
Hier liegt die Historie mit Rationale.

---

## BACKLOG: Reasoning-Aware-Benchmark (Option C) — zurückgestellt 2026-06-10

**User-Frage:** „Würde es von Vorteil sein, wenn Modelle, die reasoningfähig sind, während der Benchmarks diese Fähigkeit auch nutzen können?"

**Befund:** Kommerzielle Modelle mit architektonischem Reasoning (o-Serie, GPT-5, R1, Magistral) nutzen es automatisch. Claude ohne expliziten `thinking`-Param und llama.cpp mit `enable_thinking: false` NICHT → systematische Verzerrung.

**Zweistufiger Plan (zweistufige Empfehlung KI):**
- **Phase 1:** Server-Param-Mapping pro Provider (Ollama `think=True`, llama.cpp `reasoning=True`, Anthropic `thinking.budget_tokens`, OpenAI `reasoning_effort="medium"`).
- **Phase 2:** `benchmarks.<module>.reasoning_strategy: auto | force_on | force_off` + Leaderboard-Spalte `reasoning_active`.

**User-Entscheidung 2026-06-10:** Zurückgestellt. Begründung:
- (a) großer Versionssprung
- (b) kommerzielle Reasoning-Modelle müssten 2x getestet werden
- (c) würde Benchmark-Konzept verzerren
- (d) aktuelle Idee: „Modelle so testen, wie man sie halt in den Provider wirft und nutzt"
- (e) später nachziehen, wenn Konzept sauber abgestimmt ist

**Aktueller Bias (akzeptiert):** `thinking_override.value=false` (v4.7.1, erweitert v4.7.3) deckt `force_off`-Use-Case ab. `force_on` fehlt noch.

**Re-Aktivierungs-Bedingung:** Sobald Uri-Vergleich (lokal vs. kommerziell) explizit um die „Reasoning-Fairness"-Frage erweitert werden soll.

---

## v4.5.0 (2026-06-08) — ID-SSoT-Refactoring (Phasen 1–6)

**Problem:** Mehrere unkoordinierte ID-Transformationen + Workarounds (`migrate_canonical_model_ids.py`, `*.bak`-Dateien, 4-Stufen-`_resolve_dir()`-Fallback).

**5-Phasen-Plan:**
1. `module_integration.py::_resolve_to_canonical_id()` delegiert an `resolve_canonical_model_id()`
2. `web_export.py::slugify()` → `_safe_name()`; `_resolve_dir()`-Eingabe durch `_safe_name()`
3. Alle 12 Inline-ID-Transformationen → `_safe_name()`; neue SSoT `strip_date_suffix()`; `safe_id()` löschen
4. Card-First-Vertrag: `result_manager`, `tooluse_exporter`, `repair_pc_leaderboard`, `generate_model_cards` rufen `resolve_canonical_model_id()`
5. `migrate_canonical_model_ids.py` entfernt, `*.bak` aufräumt, Tests härten

**Phase 6:** Doku + Memory-Bank synchronisiert.

**Neue SSoT-Funktionen in `utils/model_utils.py`:** `strip_date_suffix()`, `enforce_card_first()`. 12 Inline-ID-Transformationen auf SSoT migriert. `enforce_card_first()` in `result_manager.save_results()` als CSV-Senke eingebunden.

**145/145 Tests grün.** Card-First ist KEIN Hard-Fail — Draft-Card wird angelegt, WARNING geloggt.

---

## v4.6.0 (2026-06-08) — CSV-Hygiene-Sanitizer

**Problem:** `local_models_benchmark.csv` 17705 Zeilen, 13265 (75 %) mit leerem `model`-Feld. Korrupte Rohtext-Antworten, Header-Repeats, Boolean-Modell-Werte.

**Lösung:** `scripts/maintenance/sanitize_benchmark_csvs.py` mit Vier-Klassen-Filter (Header-Repeat, Rohtext-Asset-ID, Boolean-Modell, leeres Modell). Dry-Run/Apply-Modus, idempotente `.bak`-Backups, atomares `.tmp`+`replace()`-Schreiben.

**Bereinigung:** 13466 Müll-Zeilen aus `local_models_benchmark.csv` entfernt (93 %), 11 aus `commercial_models_benchmark.csv` (0.6 %).

**Leaderboard-Befund nach Sanitizer:** 84 Zeilen, 78 vollständig (43/43), 5 unvollständig (40–42/43 — echte Test-Lücken: Kimi K2.6, DeepSeek V4 Pro, Qwen 3.5 397B A17B, MiniMax M2.7, GLM-4.7), 1 mit 49/43 (Test-Override-Logik).

---

## v4.6.1 (2026-06-08) — CSV-Hygiene Defense-in-Depth

**Diagnose:** Aktive Benchmark-Pipeline ist sauber (`unified_runner` lädt `asset_id` aus YAML, `result_manager` macht Rewrite mit `extrasaction="ignore"`).

**Lücken identifiziert:**
1. `consolidate_csv` ohne Schreib-Validierung
2. `result_manager` ohne Hard-Fail-Guard

**Fix in 3 Schichten:**
1. `result_manager._validate_row_for_write()` — Hard-Fail-Guard, der jede Zeile VOR dem CSV-Write prüft. Wirft `ValueError` bei Korruption; `_write_to_csv()` fängt ab und überspringt.
2. `consolidate_csv._filter_corrupt_rows()` — wendet identische Sanitizer-Heuristiken auf DataFrame an.
3. `Makefile::validate-csv` — neues Target für CI-/Smoke-Tests.

**226/226 Tests grün** (vorher 210, +16). Pylint 10.00/10.

---

## v4.4.0 (2026-06-07) — Modellname-Mismatch Fix & Leaderboard-Redundanz entfernt

**Problem:** `make benchmark-auto` führte zu unerwartetem Cache-Cleanup zwischen Benchmark-Modulen desselben Modells.

**Root Cause:** `_ensure_model_card()` in `unified_runner.py` wandelt Config-Modellnamen in kanonischen Card-Namen (Punkt → Unterstrich) um. Server wurde mit Punkt-Namen gestartet, Module liefen mit Unterstrich-Namen.

**Fix:** `utils/providers/llamacpp.py` `query()` + `start_server()` normalisieren Punkt → Unterstrich vor Vergleich.

**Ergebnis:** 0 Cache-Cleanup-Ereignisse.

---

## v4.4.2 (2026-06-07) — Leaderboard Model-ID Normalisierung

**Problem:** Partial re-runs erschienen nicht im Leaderboard, zwei Zeilen für selbes Modell (Punkt vs. Unterstrich).

**Root Cause:** `data_loader.py` normalisierte nur `model_version`, nicht `model` via Card-Lookup.

**Fix:** `scripts/leaderboard/data_loader.py` — `_normalize_row()` mappt Alias → kanonische `model_id` + `model_version`. Deduplizierung läuft auf vereinheitlichten IDs.

---

## v4.4.1 (2026-06-07) — Code-Review Refactoring: SSOT, DRY, Magic Numbers

**Fixes:**
- Leaderboard-Generierung aus `run_score_benchmark.py`, `run_political_compass_benchmark.py`, `run_tooluse_benchmark.py` entfernt (SSOT bei `run_benchmark.py`)
- `benchmark_auto.py` ~100 Zeilen toten/duplizierten Code entfernt — Delegation an `llamacpp_batch.py`
- `utils/providers/llamacpp.py` Modellnamen-Normalisierung zentralisiert
- `run_tooluse_benchmark.py` Magic Numbers durch Config-Werte aus `tooluse_report_config.yaml` ersetzt

---

## v4.3.5 (2026-06-05) — 0.0%-Bug Fix + CSV Cleanup

**Root Cause:** Thinking-Modelle via llamacpp zeigten 0.0% (response_length=0, finish_reason=length).

**Ursache:** `thinking_probe_detected=True` → `is_reasoning_model=True` → `resolve_token_budget*5=40960` > `num_predict=8192` → alle Tokens für Thinking, 0 für Output.

**Fix:** Provider-Level num_predict-Cap in `utils/providers/llamacpp.py`. `num_predict: 16384` in `config/provider_config.yaml` (llamacpp + llamacpp_spark).

**CSV Cleanup:** 4 Qwen-Modelle mit >15% Fehlerquote gelöscht (140 Zeilen).

---

## v4.3.0 (2026-06-04) — Spark-Connector Konsolidierung & Lifecycle-Cleanup

**Fixes:**
- `utils/providers/llamacpp.py`: Readiness akzeptiert `reasoning_content` / `finish_reason` / `usage.total_tokens`
- Endpoint-Adoption mit Warmup-Fenster für bereits laufendes identisches Modell
- `scripts/core/unified_runner.py`: Lokaler Provider-Cleanup in `finally` (`cleanup_on_exit` + `server_post_stop_cmd`)

---

## v4.2.0 (2026-05-31) — OpenRouter-Migration, Free-Tier & Qwen-Integration

- `openrouter.py`: `extra_body={"data_collection": "allow"}` — Qwen/Alibaba-Cloud 404-Fix
- Model Cards: `qwen_qwen3_7-max.json`, `qwen_qwen3_6-plus.json`
- `resolve_provider()`: `:free`-Suffix-Bug + `/`-Heuristik korrigiert
- OpenRouter Free Tier Rate-Limit-Profil (`openrouter_free`: 18 RPM/1)
- Ollama→OpenRouter Migration: 3 Model Cards + Reviews umbenannt
- Tool-Use-Reviews: 14 Modelle generiert (devstral, gemini, gemma, gpt-5.5, deepseek, mistral)

---

## v4.1.x (2026-05-30) — Tool Use Full-Fleet-Run

- Tool Use Full-Fleet-Run: alle toolfähigen Modelle getestet

---

## v4.1.0 (2026-05-30) — llamacpp Expansion & Bug Fixes

- Double-Start-Bug + Duplicate-Runner-Fix (`llamacpp.py`, `benchmark_auto.py`)
- gemma-3-12b-it-q8: Provider-Config + Model Card
- Model Card Schema: `model_version` = Format/Quant, `weights_source` = Plattform
- 3 Module aktiviert: code_quality, reasoning_logic, documentation_quality

---

## v4.0.0 (2026-05-26) — Major Release: Tool Use + Pricing SSoT Migration

- Budget-Enforcement vollständig entfernt: `cost_limits.yaml` gelöscht, `CostLimitExceededError` entfernt
- `cost_tracker.py` + `score_calculator.py` + Web-Export: Model Cards als alleinige Pricing-SSoT
- LiteLLM aus Pricing-Pfad entfernt
- Controller-Architektur (`benchmark-auto`): MCP-Lifecycle SSOT-Fix
- 257/257 Tests grün, Ruff + Pylint 10.00/10

---

## v3.x-Serie (Architekturfundament)

- **v3.15.0 (2026-05-25):** Bug-Fixes + Tool Use Probe-Run; `anthropic.py` system-Kwarg-Fix
- **v3.14.0 (2026-05-25):** Phase-C Asset + Judge Hardening; `tooluse006.yaml` Multilingual
- **v3.13.0 (2026-05-25):** Hallucination-Cap config-first
- **v3.12.0 (2026-05-24):** Tool Use Phase-A-Erweiterung (tooluse004, tooluse005)
- **v3.11.0 / v3.10.0 (2026-05-23):** Tool Use Benchmark-Modul Launch; MCP-Server; Content Verification Framework
- **v3.9.0 (2026-05-23):** Architektur-Compliance-Refactoring (Pylint 9.99/10); Anti-God-Script-Package
- **v3.8.x (2026-05-22–23):** `generate_model_cards.py` schlanker Template-Creator; Classification Taxonomy SSoT
- **v3.7.x:** Pricing SSoT v1; Card-First 3-Tier-Klassifizierung; Web-Export Anti-God-Script
- **v3.6.x:** Political Compass Archetypen finalisiert; Lizenz-Metadaten in allen Cards
- **v3.5.8:** ThinkingProbe & Card-First Workflow
- **v3.4.x–v3.5.7:** Token-Budget SSoT; Module-Weight-System; Language Compliance
- **v3.2.x–v3.3.x:** LLM Judge komplett; Provider SSOT-Refactoring; Political Compass entkoppelt

---

## v4.6.2 — Card-ID-Pipeline (Unique Card-Erzeugung)

**Problem:** Card-ID-Kollisionen (z.B. `qwen3.5-4b` als Cloud-Variante und als lokales Ollama-Modell) überschrieben sich gegenseitig. Cache-Lookup scheiterte zwischen Punkt- und Underscore-Schreibweise.

**Lösung in 3 Bausteinen:**
1. `build_card_id(model_id, provider)` in `utils/model_utils.py` — Schema `{base_after_last_slash}--{suffix}`. Suffix = `provider.lower()` für API-Provider, Shortcode (`OR`, `GR`, `M4APL`, `SPRK`, `VSPK`, `LCL`) für lokale Provider.
2. `resolve_unique_card_id(desired_id, card_dir=None)` — prüft Disk-Konflikt, hängt `-2`, `-3` an. Logger-WARNING.
3. `ensure_card(..., provider=...)` in `utils/card_utils.py` — `provider` hat Vorrang vor explizitem `card_path`.

**Defense-in-Depth:** `canonical_lookup_keys()` in `llamacpp_batch.py` (Schritt 4) erweitert Varianten mit Heuristik `re.sub(r"(\d)_(\d)", r"\1.\2", v)`. Dadurch findet Leaderboard (`qwen2_5-coder-7b`) auch Caller-Lookups mit `qwen2.5-coder-7b`.

**Test-Coverage:** 21 neue Tests in `test_build_card_id_and_resolve_unique.py`, 7 in `test_ensure_card_with_provider.py`, 3 in `test_canonical_lookup_keys.py`. Gesamt-Suite: 444/444 grün.

---

## v4.6.3 (2026-06-08) — 0-Token-Test-Runs Fix (start_server als SSoT)

**Symptom:** Tests starteten mit 0 Tokens bei Remote-llama.cpp-Providern (DGX Spark).

**Root Cause:** `_process_single_test()` hatte passiven `requests.get()`-Health-Check. Bei Remote-SSH-basierten Providern war die Cold-Start-Latenz um Größenordnungen höher als bei lokalen Servern.

**Fix:** Passiver `requests.get()`-Health-Check entfernt. Stattdessen direkter `client.start_server(model)`-Aufruf vor dem Test. Drei mögliche Outcomes, alle mit klarem Error-Path.

**Result:** 474/474 Tests grün, kein neuer Test nötig.

---

## v4.6.4 (2026-06-08) — benchmark_auto: Skipped-vs-Failed Bug Fix (Tristate-Return)

**Symptom:** `make benchmark-auto` brach reproduzierbar nach 1 Modul ab, obwohl `make benchmark` (Wizard-Pfad) korrekt durchlief.

**Root Cause:** `_run_module_for_model()` returnte `bool` — `False` hatte drei Bedeutungen (Cache-Skip, kein Asset, echter Fehler). Caller konnte nicht unterscheiden.

**Fix:** Tristate-Return: `"ran" | "skipped" | "failed"`. Beide Caller (`_run_single_llamacpp_provider_batch`, `run_local_batch`) angepasst.

**Result:** 481/481 Tests grün.

---

## v4.7.0 (2026-06-09) — Hermes-Retries Fix (Per-Modell-Override für ctx-size + parallel)

**Symptom:** Hermes 4.3 36B auf DGX Spark zeigte sporadische Connection-Resets nach Heavy-Tasks.

**Root Cause:** Hybrid-Mode Reasoning (SWA/Recurrent) + 4 parallele Slots + 8 GB Prompt-Cache-Limit.

**Lösung:** Per-Modell-Override `context_length: 16384` und `parallel: 1` für `hermes-4.3-36b-q6` in `config/provider_config.yaml`. Andere Spark-Modelle unangetastet.

**Result:** 483/483 Tests grün, 0 Retries im Lauf.

---

## v4.7.1 (2026-06-09) — Web-Export-Blacklist + Thinking-SSoT-Auflösung

**Zwei Features in einer Version:**

### 4.7.1a — Web-Export-Blacklist
- Neue Config `config/web_export_blacklist.yaml` (flache YAML-Liste)
- `_load_export_blacklist()` splittet in `exact_set` (O(1)) und `pattern_set` (fnmatch)
- Hauptloop-Hook nach PC-Skip, vor `mkdir()`: verhindert leere Verzeichnisse
- SSoT Match-Schlüssel = `raw_model_id` aus Leaderboard-CSV
- Wildcards via fnmatch (z.B. `qwen3.5-35b-a3b-*` sperrt alle Quants)
- 17 neue Tests in `test_web_export_blacklist.py`

### 4.7.1b — Thinking-SSoT-Auflösung (Card + Override)
- `resolve_effective_thinking()` mit Priorität: Override > Card-Probe > None
- `_is_override_active()` mit `value` (bool), `reason` (Pflicht), `active_until` (optional)
- `resolve_token_budget(..., *, provider=None)` — neuer kwarg
- `base_runner.py:121` reicht `provider=provider` durch
- 24 neue Tests in `test_thinking_override.py`
