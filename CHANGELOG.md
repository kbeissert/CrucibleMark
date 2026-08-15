# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [v5.1.4] - 2026-08-15

**Patch-Release: Code-Review-Umsetzung (Sicherheit, Konsistenz, Robustheit).**

- **Judge-Prompt (Blind-Evaluierung):** Illustrative Modellnamen-Beispiele
  (o1, DeepSeek R1, Qwen3, Gemini 2.5 etc.) aus den Tag-Beschreibungen des
  EVALUATION-CONTEXT-Blocks entfernt — Verhaltensanweisungen unverändert,
  Judge bleibt name-blind. Bekannte Limitierung dokumentiert: Tag
  Agentic-Orchestrator mappt 1:1 auf Claude-Opus.
- **Scoring-Fix ToolUse-Exporter:** `combined_score == 0.0` fiel bisher durch
  einen `or`-Fallback fälschlich auf `total_score` zurück (0.0 ist falsy).
  Ersetzt durch expliziten `None`-Check. Betrifft ausschließlich Assets mit
  exakt 0.0 — historische Werte mit echten Scores bleiben unverändert.
- **Robustheit:** Ollama-Modul-Loop in `benchmark_auto.py` bricht bei echtem
  Fehler ab (Spiegelbild zu vllm/llamacpp); `lifecycle_hooks` verschluckt
  ToolUseExporter-Fehler nicht mehr still; 8 stille Exception-Swallows mit
  Logging versehen; `LLMScorer` Fail-Fast statt stillem 0-Score.
- **Preis-Update refactored:** Longest-Prefix-Match statt fehlerhaftem
  `split("-")[0:2]` (falsche Preise bei Versionssuffixen), Preis-SSoT nach
  `config/model_pricing.yaml`, atomare Card-Writes.
- **Sicherheit:** Shell-Injection-Flächen geschlossen (List-Subprocess für
  MCP-Start, `shlex.quote` in llamacpp-Server-Cmd); Rate-Limit-Backoff
  exponentiell (60s-Basis, 600s-Cap).
- **DRY/Performance:** `utils/provider_config_text.py` als SSoT für
  YAML-Text-Helfer; Blacklist-Load und Vendor-Lookup delegieren an
  `web_export/filters.py`; `ConfigValidator` mit mtime-invalidiertem
  Cache (52+ Call-Sites); Card-Lookup-Cache in `clean_results`.
- **CC≤12:** Alle 8 ruff-bestätigten C901-Verstöße verhaltenstreu
  aufgesplittet (audit_logger CC 67 → Methoden; Roundtrip-Diff
  byte-identisch).
- **Ruff:** 409 → 0 Fehler (413 Auto-Fixes, veraltete Typ-Annotations,
  E402-Zeilen-noqas statt file-level noqa, SIM/B007-Bereinigung).
- **Maintenance:** `consolidate_csv.py --dry-run`; Sanitizer-Numeric-Heuristik
  entschärft (ID-artige Werte wie `3-8` bleiben valide);
  `_fix_csv_efficiency.py` unlauffähig gemacht (One-Shot-Doku);
  Dead Code entfernt (`verify_counts.py`, `_apply_research_diff`).
- **Konsistenz:** llamacpp-Modell-Normalisierung case-insensitive (analog
  vllm); `run_reviews.sh` mit `set -euo pipefail`; Makefile `mcp-start`
  schreibt `.mcp.pid` (gezielter Kill statt pkill-Race).

## [v5.1.3] - 2026-08-15

**Patch-Release: Test-Suite-Reparatur & Card-Vocabulary-Normalisierung.**

Behebt drei vorbestehende Testfehler (alle auf HEAD reproduzierbar) und
normalisiert die Architecture-Tags gegen die Vocabulary-SSoT.

- **hermes-4-36b Orphan-Cleanup:** Draft-Card (alle Felder `TODO`, aus
  abgebrochenem Run vom 01.08.) via `make clean-model` entfernt — der
  vollständige Benchmark lief korrekt unter `hermes-4-3-36b` (ID-Rename-
  Orphan-Muster). 15 verwaiste Audit-Logs und 19 Cost-Log-Einträge bereinigt.
- **Tag-Whitelist normalisiert:** Redundante Quant/Param-Tags (`MXFP4`,
  `NVFP4`, `36B`, `Compressed-Tensors`, `512K-Context`) aus 2 Cards entfernt —
  Info steht in dedizierten Feldern. Vocabulary um `Native-Quant` und
  `Harmony` (informational, neue Web-Export-Badges) erweitert;
  `Configurable-Reasoning` → `Thinking-Optional` und `Thinking-Mandatory` →
  `Thinking` als Deprecated-Normalisierungen. Wirkung: `qwen3-8-2-4t-a95b`
  erhält jetzt korrekt `thinking_mode: "thinking"` (5x Reasoning-Multiplikator
  greift), GPT-OSS-120b zeigt Native-Quant/Harmony-Badges.
- **Ornith-Test invariantisiert:** llamacpp-Ornith-Test an leeres
  `llamacpp_spark` (seit 2026-08-10 auskommentiert) angepasst — Kern-Invariante
  (keine Thinking-Expansion für llama.cpp-Modelle) bleibt für
  Re-Aktivierungen aktiv.
- **Maintenance-Fixes (Sessions 74/75):** `clean_provider_config` Endlosschleife/
  YAML-Bruch, `models`-None-Crash, `sanitize_benchmark_csvs` aktualisiert,
  `probe_thinking` auf rein diagnostisch umgestellt.
- **Model-Cards:** Null-/Standardfelder für alle Cards ergänzt;
  `deepseek-v4-flash-ud-iq2` (IQ2_M, GGUF, llama.cpp Spark) integriert;
  `political_compass` deaktiviert; llamacpp-Port 1234 korrigiert.
- 1410 Tests grün, Naming-Gate 122 Cards OK, Ruff sauber.

## [v5.1.2] - 2026-08-03

**Patch-Release: vLLM-Connector CC-Refactoring — Architektur-Regel-Konformität.**

Verhaltenserhaltendes Refactoring von `utils/providers/vllm_base.py`. Die als
*unverhandelbar* deklarierte CC-≤-12-Regel (`.ruff.toml` C901, max-complexity=12)
wurde bisher über zwei `# noqa: C901`-Annotationen umgangen. Alle drei Verstöße
behoben — keine `noqa` mehr im Connector.

### Changed — vLLM-Connector Komplexitäts-Reduktion (Session 78)

- **`start_server` zerlegt (CC 19 → 8):** 280-Zeilen-Monolith in Dispatch-Shell
  + 9 Pfad-Methoden (`_start_already_running`, `_start_adopt`, `_adopt_with_warmup`,
  `_start_swap_restart`, `_stop_and_verify`, `_start_loading_or_cold`,
  `_start_wait_for_loading`, `_cold_start`, `_mark_active`). Kein Verhaltenswechsel.
- **`query` Streaming ausgelagert (CC 16 → 7):** Streaming-Block in `_consume_stream()`
  extrahiert.
- **Reasoning-Fallback dedupliziert (DRY):** `_apply_reasoning_fallback()` als
  Shared-Helper — ersetzt doppelten vLLM-0.25.1-Fallback in Streaming + Non-Streaming.

### Tests

- 115 passed (78 vLLM-Connector + 37 Thinking-Expansion/Config), 0 failed.
- Ruff C901: 0 violations, 0 `noqa`-Annotationen in `vllm_base.py`.



## [v5.1.0] - 2026-07-14

**Striktere Incapable-Klassifikation + Card-Korrekturen.**

Fixt einen Design-Defekt in v5.0: Modelle mit `supports_tool_use: false` wurden
pauschal als "incapable" exempt, selbst wenn sie getestet wurden (alle 6 Rows
error). Das führte zur Inversion des gewünschten Verhaltens — Modelle, die
antraten und durchfielen, wurden belohnt (exempt), während Modelle, die antraten
und teilweise durchfielen, bestraft wurden (Malus).

⚠️ **Breaking Change:** Total Scores und Rankings für betroffene Modelle ändern sich.

### Fixed — Incapable-Klassifikation (v5.1)

- **Striktere `_classify_module_status`:** Ein Modell mit `capability_field: false`
  ist NUR dann "incapable" (exempt), wenn es **0 Rows überhaupt** für das Module
  hat (keine error-Rows, keine success-Rows). Hat es ≥1 Row (auch error), wurde
  es getestet → Klassifikation "missing" (Malus). Verhindert die Inversion
  "getestet und durchgefallen = exempt".
- **`attempted_set` aus `df_all`:** Neuer Parameter in `_classify_module_status`
  und `_apply_coverage_malus`. Enthält (model, version, category)-Tuples aus dem
  rohen DataFrame (inkl. error-Rows), gebaut via Helper `_build_model_category_set`.
- **`_expected_assets_for_model` Konsistenz:** Auch hier wird `attempted_canonical_cats`
  geprüft — ein Modell mit Rows bekommt keinen expected_assets-Abzug (Tests Run
  zeigt 43/49, nicht 43/43).
- **`_calculate_run_counts` baut `attempted_canonical_cats`:** (canonical_id,
  category)-Set aus df_all, durchgereicht an `_expected_assets_for_model`.

### Fixed — Card-Korrekturen (Data Quality)

- **`command-a-plus-05-2026.json`:** `supports_tool_use: false → true`. Cohere
  Command A+ ist explizit für Tool-Use/Agentic gebaut (`use_case_primary: "agentic"`).
  Der `false`-Flag war mit "Tool-Use über die Cohere-API derzeit nicht stabil"
  begründet — das ist eine Provider/API-Stabilitätsaussage, keine
  Modellkapabilität. Das Modell WURDE getestet (6 error-Rows, tooluse_runs mit
  score_p2: 13.33).
- **`openai_gpt-oss-20b.json`:** `supports_tool_use: false → true`. GPT-OSS
  unterstützt Function Calling. Wurde getestet (6 error-Rows, tooluse_runs
  mit 0.0/0.0).
- **`deepseek-r1-distill-qwen-32b.json`:** Unverändert (`supports_tool_use: false`).
  0 ToolUse-Rows, keine tooluse_runs → legitimerweise incapable (Reasoning-Distill
  ohne native Tool-Use-Fähigkeit). Bleibt exempt.

### Score-Auswirkungen (verifiziert)

- **Command A+:** Rank 62 → Rank 104 (−42 Plätze). Score 71.42 → 61.90.
  coverage_ratio 1.00 → 0.87. Tests Run 43/43 → 43/49.
- **GPT-OSS 20B:** Rank 104 → Rank 108 (−4 Plätze). Score 64.85 → 56.20.
  coverage_ratio 1.00 → 0.87. Tests Run 43/43 → 43/49.
- **DeepSeek R1 Distill Qwen 32B:** unverändert (Rank 106, Score 60.46,
  coverage_ratio 1.0, Tests Run 43/43 — legit. incapable).
- **Llama 4 Scout:** unverändert (Rank 110, Score 55.17, coverage_ratio 0.87).
- **coverage_ratio-Verteilung:** 107× 1.0 + 3× 0.87 (vorher 109× 1.0 + 1× 0.87).
- **Invariante** `Routine + Reasoning = Total` für alle 110 Modelle (0 Verletzungen).
- **Benchmark-CSVs** (local/cloud/commercial) unverändert.

### Tests

- 4 neue Tests in `tests/test_score_calculator_coverage.py`:
  - `test_classify_incapable_with_error_rows_becomes_missing`
  - `test_classify_incapable_no_attempted_set_still_incapable`
  - `test_expected_assets_incapable_with_rows_no_reduction`
  - `test_expected_assets_incapable_without_rows_still_reduced`
- 1350 passed, 22 skipped, 0 failed.



## [v5.1.1] - 2026-08-02

**Patch-Release: vLLM-Connector-Fixes, Laguna Dual-Profile-Bereinigung, Naming-Validator, Tool-Use-Memory-Bank.**

### Fixed — vLLM-Connector (Session 71, Commits fd386047, 659f34e0)

- **Thinking-Profile-Adoption:** `_adopt_matches()` scheiterte an MoE-Notation (`a3b`, `thinking`) im ID-Segment. Fix in `vllm_base.py`: Config/TOML-Name-Match.
- **Post-Stop-Verifikation:** Proxy-502 nicht mehr als `loading` interpretiert. `_backend_stopped()` mit SSH-Check.
- **502-Mehrdeutigkeit:** Pfad 3.5 in `vllm_base.py:start_server()` wartete bei Proxy-502 600s ohne `vllm-start`-Aufruf. `_remote_chat_server_running()` (SSH `pgrep`) prüft Chat-Prozess-Existenz.

### Fixed — ToolUse Timestamp-Overwrite (Session 72, Commit 79a88fe0)

- `tooluse_exporter.py:_write_card_from_aggregated_row` (Path B) überschrieb `tested_at` in 107 Cards mit `datetime.now()`. Fix: existierenden Card-Wert bewahren.

### Changed — Historical Rename (Session 72, Commit 79a88fe0)

- `qwen3_6-27B` → `qwen3_6-27B-pre025` (capital B, vLLM vor 0.25.1). CSV (99 Zeilen), Card, NVFP4-Summary, Blacklist (kept_overrides → aktive blacklist), Audit-Logs (93 Dateien), Reviews, Runs-JSON, Test-Fixtures aktualisiert. `pre025` blacklisted, `nvfp4` exportiert.

### Changed — Laguna Dual-Profile-Bereinigung (Session 73, Commit 7a05dbd7)

- Laguna S 2.1 als selektives Reasoning-Modell identifiziert (HF Discussion #13: "thinks when needed"). `enable_thinking: true` aus `provider_config.yaml` entfernt → keine Dual-Profile-Expansion. `dual_profile` in Card auf `null`. 65 CSV-Zeilen entfernt.

### Added — Coverage Ratio (Session 74, Commit 7ccbc0cf)

- `coverage_ratio` als neue Spalte im Leaderboard (generalisiert Coverage-Bewertung pro Modell).
- Laguna S 2.1 als 9. vollständig integriertes Modell: Rank 92, Score 69.1%, Silver Badge, 49/49 Tests, ToolUse P1=78.33/P2=33.33.

### Added — Naming-Validator als Publication-Gate (Session 76, Commit 1c48c1d9)

- `scripts/analysis/validate_naming.py`: 11 display_name + 7 model_version Forbidden-Patterns. Hard-Gate in `make web-export` (exit 1), Soft-Gate in `make web-export-dev` (warn-only).
- 7 vLLM/NVFP4 display_name + 10 model_version + 4 Cloud/Groq model_version Korrekturen.
- `make validate-naming` Target. `data-schema.md` als Konventionen-SSoT.

### Added — Memory-Bank Tool Use Schema (Commit e2bab258)

- `memory-bank/reference/feedback_schema.md`: Tool Use Schema Finalisierung v3.11.0 (Separation of Concerns, SSoT-Integrität).
- `memory-bank/reference/tooluse_module.md`: Tool Use Modul v3.11.0 — Architektur, Golden Standard v1.3.0, AUTHORIZED_TOOLS-Aliases, MCP-Konfiguration, P1-Scoring-Stufen.

### Fixed — Vendor Card Cleanup (Commit 45f879a2)

- 7 auto-generierte compound-name Vendor-Cards gelöscht (`alibaba_jackrong_x2`, `alibaba_hauhaucs`, `cognitive_computations`, `google_deepmind_ara_apex`, `google_deepmind_llmfan46`, `google_deepmind_undix`, `google_deepmind_unsloth`).
- `ara_apex_quant.json`: `unknown: false` (verifiziert via HF Collection).
- `llmfan46.json`: vollständig überarbeitet (Community Contributor Profil).
- `jackrong.json`: neue Community Contributor Card.

---

## [v5.0.0] - 2026-07-13

**Generalized Coverage Scoring + ToolUse Integration.**

ToolUse wird als vollwertiges 8. Scoring-Modul in den Total Score integriert
(`enable_scoring: true`, `module_weight: 1.0`). Die bisherige
selbstnormalisierende Modulgewichtung (v3.4.3) wird durch eine
Coverage-aware-Formel ersetzt: fehlende Modul-Daten reduzieren den Score
(Malus im Nenner), strukturell incapable Modelle sind exempt. Keine
Benchmark-Re-Runs nötig — die Per-Asset-Daten liegen bereits in den CSVs.

⚠️ **Breaking Change:** Total Scores und Rankings ändern sich. Alte Leaderboards
bleiben in der Git-History reproduzierbar.

### Changed — Scoring-Formel (v5.0 Coverage-aware)

- **ToolUse als Scoring-Modul:** `benchmark_modules/tooluse/config.yaml` — `enable_scoring: false → true`, `moduleweight → module_weight` (Typo-Fix), `module_weight: 1.0`, `default_contribution: {routine: 0.5, reasoning: 0.5}`, `capability_field: supports_tool_use`. `combined_score` (= `percentage`) fließt in den Total Score ein.
- **Coverage-aware Nenner:** `Total Score = Σ(present scores×weights) / Σ(present + missing + unknown weights)`. Bisher: Nenner nur über present-Module (Renormalisierung auf 0–100). Jetzt: missing/unknown-Module tragen zum Nenner bei ohne Zähler → Malus.
- **6-Status-Taxonomie:** `present` / `missing` / `unknown` / `incapable` / `rolling_out` / `not_deployed`. `unknown` = capability_field fehlt in Card (Malus + WARNING-Log). `incapable` = capability_field explizit false (exempt). `rolling_out` = < deployment_threshold Coverage (für alle ausgeschlossen).
- **Deployment-Schwelle:** `deployment_threshold: 0.10` in `benchmark_config.yaml`. Ein Modul gilt als deployed ab ≥10% der Modelle mit gültigen Daten. Verhindert dass ein Modul mit 3/110 Daten 107 Modelle bestraft.
- **`coverage_ratio`-Spalte:** Neue Leaderboard-Spalte (gewichtete Test-Abdeckung, 0.0–1.0). 109 Modelle = 1.0, 1 Missing-Modell (llama-4-scout) ≈ 0.87.
- **Per-Modell `Tests Run`-Erwartung:** Incapable-Modelle bekommen `expected_assets` um die incapable-Modul-Assets reduziert (z.B. 43/43 statt 43/49). `logical_count` zählt nur gültige Status (Error-Rows nicht als "run" gezählt).

### Fixed

- **`moduleweight` → `module_weight` Typo:** `_build_modules_config()` liest `lb_config.get("module_weight")` — der Key `moduleweight` (ohne Unterstrich) wurde ignoriert. Mit `enable_scoring: true` wäre das Gewicht `None` gewesen. Fix im Config-YAML.

### Score-Auswirkungen (verifiziert)

- **106 present-Modelle:** ToolUse trägt normal zum Score bei.
- **1 missing-Modell** (`meta-llama/llama-4-scout-17b-16e-instruct`): `supports_tool_use: true`, aber alle 6 Rows error → ~13% Score-Reduktion (1.0/7.5 Gewicht), coverage_ratio ≈ 0.87, Tests Run 43/49.
- **3 incapable-Modelle** (`openai/gpt-oss-20b`, `command-a-plus-05-2026`, `deepseek-r1-distill-qwen-32b`): `supports_tool_use: false` → exempt, keine Strafe, coverage_ratio = 1.0, Tests Run 43/43.
- **Invariante** `Routine Score + Reasoning Score = Total Score` für alle 110 Modelle erhalten (Toleranz 0.01).
- **Benchmark-CSVs** (local/cloud/commercial) unverändert — nur Leaderboard-CSVs neu generiert.


## [v4.10.18] - 2026-07-11

**Framework-Refactoring (Sektion A–M) + Ruff-Cleanup + Bugfixes + Doku-Sync.**

24 Commits nach v4.10.17 — systematisches Refactoring des Framework-Codes gegen die Architektur-Regeln: God-Script-Zerlegung, Helper-SSoT-Konsolidierung, `print`→`logging`, `yaml.safe_load`→`ConfigValidator`, C901-Komplexitäts-Auflösung, Ruff-0-Violations, Dead-Code-Entfernung. Verhaltenserhaltend — keine Änderungen an Scoring/Token-Budget/Provider-Logik. Zusätzlich Bugfixes (ensure_card Duplicate-Cards, Runtime-Bugs) und Doku-Sync auf die neue Package-Struktur.

### Changed — Refactoring (Sektion A–M)

- **Sektion A — `utils/model_utils.py` Aufspaltung:** Monolithisches `model_utils.py` in 7 fokussierte Submodule zerlegt (`model_card_io.py`, `model_id_base.py`, `model_id.py`, `model_size_class.py`, `model_thinking.py`, `model_token_budget.py`, `model_version.py`) + Re-Export-Bridge in `model_utils.py` (rückwärtskompatibel — alle `from utils.model_utils import X`-Imports funktionieren unverändert).
- **Sektion B — Judge-Caching refactor:** Function-Attribute-Caching (`functools`-Decorator auf Instanzmethoden) → Modul-Level-Singleton. C901-Auflösung + Tests harmonisiert.
- **Sektion C — Provider-Connectors:** 4 dead no-op `_extract_reasoning_tokens`-Stubs gelöscht. `vllm_base.py` Methoden-Extraktion + `provider_health` ConfigValidator.
- **Sektion D — `scripts/web_export.py` Aufspaltung:** God-Script in Package `scripts/web_export/` zerlegt (`constants.py`, `entry_builders.py`, `filters.py`, `loader.py`, `main.py`, `top_level.py`). Einstiegspunkt: `python -m scripts.web_export`. `manage_model_cards.py` analog aufgespalten.
- **Sektion E+J — `benchmark_auto` Aufspaltung + Provider-Branch Pitfall-Doku.**
- **Sektion F — Helper-SSoT:** Neue `utils/text_helpers.py` (`strip_none`, `slugify`, `normalize_pending`, `parse_star_float`, etc.) + `utils/io_helpers.py` (`atomic_write_json`, `atomic_copy`, etc.). Eliminiert Duplikate über Web-Export, Card-Utils, Maintenance-Skripte.
- **Sektion G — Config-SSoT:** 18 raw `yaml.safe_load`-Aufrufe → `ConfigValidator` in 15 Skripten.
- **Sektion H — Legacy-Cleanup:** 27 Migrationsskripte nach `scripts/legacy/` verschoben (von Lint-Checks excludiert).
- **Sektion I — Logging-SSoT:** 131 `print()` → `logging` in Framework-Utils.
- **Sektion K+L+M — C901-Auflösung:** ToolUse Exporter, Report, Leaderboard, Review/Cleanup Komplexitäts-Reduktion. Alle C901-Verstöße aufgelöst (gesamt 0).

### Fixed

- **`ensure_card_structure.py` doppelte Base-Cards für suffixed Modelle:** `run_for_card()` erzeugte beim Batch-Modus (`--all`/`--missing`) doppelte Base-Cards für provider-suffixed Modelle (`--SPRK`, `--VSPK`, `--M4APL`, `--GR`), weil `ensure_card(model_id)` ohne `card_path` aufgerufen wurde → `_card_path()` erzeugte den unprefixed Pfad → neue Base-Card statt in-place Patch. Fix: `card_path` wird durchgereicht (`ensure_card(model_id, card_path=card_path)`). `--model`-Modus via `_find_card()` vereinheitlicht. Filename-Fallback stript Shortcode-Suffix. 7 Regression-Tests neu.
- **4 Runtime-Bugs + 3 verlorene Refactor-Artefakte** aus Makefile-Audit korrigiert.
- **2 pre-existing Test-Failures** korrigiert.
- **F821:** Fehlende `stream_handler`-Parameter + `Any`-Importe in C901-Helpern ergänzt.

### Maintenance

- **Ruff 0-Violations:** 711 auto-fixable Verstöße bereinigt + alle verbleibenden 252 manuellen Verstöße aufgelöst (gesamt 0).
- **QA-Härtung:** `make lint` + `make test` um `tests/` erweitert (Framework-Refactor Phase 0).
- **Web-Projekt LCL-Duplikation behoben:** `is_local_provider`-Macro in `_badges.njk` als SSoT für `LCL|SPRK|M4APL|VSPK`-Check, 3 Templates refactored (CrucibleMark-Web Commit `1b12fbd`).

### Docs

- **Doku-Sync auf Package-Struktur:** `.agent/web-export-cleanup.md`, `docs/ARCHITECTURE.md`, `docs/TOOLUSE_MODULE.md`, `docs/CARD_MANAGEMENT.md` — verwaiste `scripts/web_export.py`-Referenzen auf `scripts/web_export/`-Submodule aktualisiert. `_strip_none` → `strip_none` in `utils/text_helpers.py`.

### Verifikation

- `ruff check`: 0 violations. `make test`: 1316 passed, 21 skipped, 0 failed. `make validate`: clean. Eleventy-Build (Web): 366 Dateien, 0 Errors.


## [v4.10.17] - 2026-07-10

**Web-Export Datenqualitäts-Fixes + Vendor-Taxonomy-Korrekturen + Dead-Code-Bug + Framework-Refactoring-Plan.**

9 Folge-Commits nach v4.10.16 — Datenqualitäts-Fixes aus Web-Export-Verifikation, Vendor-Taxonomy-Korrekturen, ein Dead-Code-Bug im Judge-Coverage-Filter, variantenbewusster `display_name` für Thinking-Varianten und ein Framework-Refactoring-Scope-Plan.

### Fixed

- **`political_bias` Phantom-Key aus Scores-Contract entfernt — `scripts/web_export.py`:** `political_bias` war ein Forward-Looking-Platzhalter für ein nie implementiertes Bias-Modul. Die CSV hatte nie eine `Political Bias`-Spalte → `row.get()` → immer `None` → Contract injizierte `political_bias: null` in alle 88 Modelle. Das Web-Projekt erwartet 9 Modul-Keys (9 echte Module + `tooluse_combined` vom Frontend injiziert), nicht 10. `LdbCols.POLITICAL_BIAS` + `_SCORE_COLUMN_TO_KEY`-Eintrag entfernt. `_SCORES_CONTRACT_KEYS`: 10 → 9 Keys. Political Compass-Daten bleiben in `data.json.political_compass` (separate Section). Neue Pitfall in `systemPatterns.md`: Phantom-Contract-Keys (Forward-Looking-Platzhalter). 93 tests passed, 0 `political_bias` in Export (88/88 verifiziert).

- **`judge_prog` → `judge_progress_status` (Dead-Code-Bug) — `scripts/leaderboard/score_calculator.py:464`:** Der Skip-Row-Filter in `_aggregate_basic_stats()` prüfte auf die Spalte `judge_prog`, die im CSV nicht existiert. Die tatsächliche Spalte heißt `judge_progress_status` (CSV-Header, siehe `unified_runner.py:762` und `judge_evaluator.py:205`). Dadurch war die `if`-Bedingung immer `False` und Skip-Zeilen (`⚠️ Judge: skip`) wurden nie aus der Judge-Coverage-Berechnung ausgefiltert. Aktuell 0 Skip-Rows in der CSV → keine Score-Veränderung, aber der Filter greift jetzt korrekt, sobald Skip-Rows auftreten.

- **Codestral `thinking_probe_detected` false→null — `benchmark_scores/model_cards/codestral-2508.json`:** Codestral 25.08 ist ein spezialisiertes Code-Modell, kein Thinking-Modell. `thinking_probe_detected=false` mit `confidence=null`+`probe_at=null` war inkonsistent — `false` impliziert „probed and not detected", aber `confidence`/`probe_at` fehlen (nie probed). Korrekt: `null` = nicht probed.

- **Community-Fine-Tuner aus vendor→community korrigiert — 2 Modellkarten:** Zwei Karten hatten Community-Fine-Tuner fälschlich als `vendor` gesetzt statt als `community` — führte zu Web-Export-Warnungen.
  - `qwable-3_6-35b-q5--SPRK.json`: `vendor: Mia-AiLab → Alibaba` (Basis: Qwen3.6-35B-A3B), `community: null → Mia-AiLab`.
  - `Gemma-4-31B-Wordsmith-NVFP4--VSPK.json`: `vendor: llmfan46 → Google` (Basis: Gemma 4 31B), `community: true (boolean!) → llmfan46`.
  - Zusätzlich: `llmfan46` in `classification_taxonomy.json/community_groups` eingetragen (`speciality: finetune_uncensored`, analog HauhauCS).

### Changed

- **Variantenbewusster `display_name` für Thinking-Varianten — `scripts/web_export.py`:** Dual-Profile-Modelle (5 Basis-Modelle mit Standard + Thinking-Variante) hatten identische `model_name`/`display_name` — im Scoreboard standen zwei Zeilen mit demselben Namen, nur an Score/Slug unterscheidbar. Neues top-level `display_name`-Feld im Leaderboard-Eintrag. Für Thinking-Varianten (Slug endet auf `-thinking` UND `thinking_mode=="thinking"`) wird ` (Thinking)`-Suffix angehängt. Thinking-only Modelle (Claude Opus 4.8, o4-mini, etc.) ohne Standard-Gegenpart bekommen keinen Suffix. `model_name` bleibt unverändert (karteinvariant, für Card-Identifikation). `display_name` ist der variantenbewusste Name für UIs. Web-Projekt: `leaderboard-builder.js` bevorzugt Export-`display_name` über `model_card.display_name` (Fallback für Backward-Compat); `data-utils.js` `leaderboardById` von `Map<id,entry>` zu `Map<id,entry[]>` (Multi-Map — keine Silent Data Loss bei Duplikat-IDs).

### Added

- **DeepReinforce als Hersteller eingetragen — `config/classification_taxonomy.json`:** Ornith-Modellkarten hatten `vendor='DeepReinforce'`, aber der Hersteller fehlte in `manufacturers` → Web-Export-Warnung bei jedem Lauf. Vendor-Card `deepreinforce.json` existierte bereits (`vendor_id='deepreinforce'`). Jetzt auch in der Taxonomy registriert mit `jurisdiction=US`.

- **Framework-Refactoring Scope-Plan — `docs/`:** Plan zur systematischen Prüfung des Framework-Codes gegen Architektur-Regeln: God-Script-Zerlegung, tote-Stubs-Entfernung, Config-SSoT-Migration, `print`→`logging` in `utils/`. Keine Verhaltensänderung an Scoring/Token-Budget/Provider-Logik.

### Maintenance

- **Reviews + Bias-Reviews + ToolUse-Narratives regeneriert (Session 58):** 31 Review-Dateien (6 Reviews, 3 Bias-Reviews, 13 ToolUse-Narratives, 5 neue Thinking-Profil-Dirs + `qwable-3_6-35b-q5`) am 2026-07-10 regeneriert. Enthält erstmals Reviews für Thinking-Profile: `Gemma-4-26B-thinking`, `Gemma-4-31B-thinking`, `Gemma-4-31B-Wordsmith-NVFP4-thinking`, `qwen3_6-27B-thinking`.

- **`tooluse_runs` `tested_at` Timestamps aktualisiert (Session 58 Re-Run):** 29 Cards mit aktualisierten `tested_at`-Zeitstempeln im `tooluse_runs`-Block vom ToolUse-Benchmark-Re-Run am 2026-07-10 (08:45 → 14:20-14:21 UTC). Keine Score-Änderungen — nur Timestamp-Updates.

### Verifikation

- Web-Export: 88 Modelle, 0 Vendor-Warnungen, 9 Score-Keys (0 `political_bias`), Eleventy-Build 366 Dateien, 0 Errors, 0 Warnings.
- Ornith CSV: 6 Error-Rows entfernt (44/43 → 43/43), Leaderboard regeneriert.
- Political Compass: 79/88 haben PC-Daten, 9 fehlen operational (7 VSPK + 2 SPRK).
- `llm_judge_coverage` 100% verifiziert REAL — Error-Rows korrekt gefiltert.

---

## [v4.10.16] - 2026-07-10

**Web-Export Blacklist-Restructure + Slug-SSoT + `normalize_pending`-Hardening + `leaderboard.json` Scores-Contract.**

### Changed

- **Blacklist-Restructure — `config/web_export_blacklist.yaml`:** Zwei-Sektion-Layout eingeführt: `blacklist:` (24 aktive Einträge) + `kept_overrides:` (22 dokumentierte Modelle in 5 Gruppen mit rank/score/size/mode/reason). Eliminiert das alte `# -`-Kommentar-Konvention für dokumentierte Ausnahmen. Jeder `kept_overrides`-Eintrag dokumentiert warum ein Modell trotz Filter-Logik (gleiche Param-Size, stärkere Quant) behalten wurde — Audit-Trail ohne Code-Änderung. Loader liest nur `data.get("blacklist", [])`, `kept_overrides` ist reine Dokumentation (zusätzliche Top-Level-Keys werden ignoriert).

- **Slug-SSoT — `scripts/web_export.py:_process_leaderboard`:** Slug-Generierung von `slugify(model_name)` auf `slugify(raw_model_id)` umgestellt. `model_id` ist die stabile Identität (eindeutig pro CSV-Zeile), `model_name` ist ein veränderlicher Display-Wert. Eliminiert alle 5 Hybrid-Pair-Slug-Kollisionen (Thinking/Standard-Varianten mit gleichem Display-Namen aber unterschiedlichen model_ids). Fallback auf `model_name` nur wenn `model_id` fehlt (defensiv, sollte bei benchmarked Models nicht vorkommen). Web-Projekt nutzt `model_id`/`slug` für Routing (Identität), `model_name`/`display_name` für Display nur.

### Fixed

- **`normalize_pending()` Sentinel-Set erweitert — `scripts/web_export.py`:** Alter Code kannte nur `("Pending", "—", "")` als Sentinels. En-Dash `–` (U+2013, verschieden von Em-Dash `—` U+2014), `n/a`, `N/A`, `NA`, `null`, `None`, `none`, `nan` leckten als String-Werte in den JSON-Export. Neue `_PENDING_SENTINELS` frozenset (O(1)-Lookup) fängt alle bekannten CSV-Platzhalter-Strings ab. Rückgabewert `float | str | None` (zuvor `str | None`) — Zahlen werden als float durchgereicht, nicht-numerische Strings sind ein CSV-Datenproblem (werden durchgereicht, nicht stillgeschluckt).

- **`leaderboard.json` Scores-Contract — `scripts/web_export.py:_write_top_level_outputs`:** `_strip_none()` entfernte null-Werte aus Model-Einträgen im `leaderboard.json`, aber der Contract verlangt alle 10 Score-Keys (auch null). Vorher sah das Frontend im Leaderboard-Index 7-9 Keys statt 10. Neue Contract-Enforcement direkt vor dem `leaderboard.json`-Write: `setdefault` für bestehende `scores`-Dicts, `dict.fromkeys` für fehlende. Konsistent mit `data.json` (das bereits seit Session-49-Folge den Contract erzwingt).

### Tests

- `test_web_export_blacklist.py::test_main_loop_skips_blacklisted_model` — erwartet `["ok-id"]` (model_id-Slug) statt `["model-b"]` (model_name-Slug). `make validate` exit 0. **97 tests passed** (31 Blacklist + 14 Normalization + 3 Field-Coverage + 14 Helpers + 35 SSOT/Blacklist-Path).

### Out of Scope

- 88 Modelle exportiert, 23 blacklisted (24 Config-Einträge, 1 nicht in CSV: `mistral-medium-2312` Legacy). 79/88 mit Political Compass, 9 ohne (7 VSPK-vLLM, 2 SPRK-llama.cpp).
- Benchmark-Daten-Fixes (nicht Export-Code): Ornith CSV `44/43` → `43/43`, Codestral `thinking_probe_confidence` fehlt in Card, `llm_judge_coverage` 100% uniform (verifizieren ob real oder Stub).
- Web-Projekt: `?? model_name` Fallbacks in Chart-Handlern können entfernt werden (Slug jetzt stabil aus model_id).

---

## [v4.10.15] - 2026-07-08

**Baustellen-Cleanup: Sampling-Drift, vLLM-Extensions-Whitelist, Card-Vocabulary, Sub-Family-LB-Entfernung, 2 pre-existing Test-Failures behoben, 2 Live-Runs.**

### Changed

- **Sampling-vs-Card-Drift (vllm_spark, 4 Modelle) — `config/provider_config.yaml`:** 4 vllm_spark-Modelle dokumentierten Sampling-Werte in Cards, die `provider_config.yaml` nicht lieferte → effektiv lief nur Framework-Default temperature=0.1. Nutzer-Entscheidung (Cards→provider_config): `Gemma-4-26B`/`Gemma-4-31B`/`Gemma-4-31B-Wordsmith-NVFP4` erhalten temperature=1.0, top_p=0.95, top_k=64 (Google-Empfehlung, bestätigt durch vLLM-`generation_config.json`-Warning beim Server-Start); `qwen3.6-27B` erhält temperature=0.6, top_p=0.95, top_k=20. ornith-1.0-35B-FP8 war bereits synchron (Reference-Pattern). Hinweis: Zukünftige Runs weichen von historischen (temperature=0.1) ab.

- **vLLM-Extensions-Whitelist — `utils/providers/vllm_base.py:_resolve_sampling`:** Bislang war nur `top_k` hardcodiert in `extra_body`; gleiche Bug-Klasse drohte bei jedem weiteren Sampling-Override. Neue generische Whitelist-Konstante `_VLLM_EXTRA_BODY_KEYS` (top_k, min_p, repetition_penalty, chat_template_kwargs, guided_json/regex/choice/grammar/decoding_backend/whitespace_pattern, bad_words, stop_token_ids) mit Schleife. Neue vLLM-Extensions: nur ein Konstanten-Eintrag, kein Code-Churn in `_resolve_sampling` (DRY gegen Mapping-Drift). `_OPENAI_STANDARD_SAMPLING_KEYS` dokumentiert die direkten Body-Keys (temperature, top_p).

- **Card-Vocabulary: `Dense` + `Tool-Use` deprecated — `config/card_vocabulary.yaml`:** `Dense` (redundant mit `parameter_architecture='dense'`, symmetrisch zu `MoE`) und `Tool-Use` (redundant mit `supports_tool_use`, symmetrisch zu `Function-Calling`) als deprecated→null aufgenommen. 4 Cards bereinigt (`Gemma-4-31B--VSPK`, `Gemma-4-31B-Wordsmith-NVFP4--VSPK`, `qwen3_6-27B--VSPK`: Dense entfernt; `openai_gpt-oss-120b`: Tool-Use entfernt).

- **Sub-Family-Leaderboard-Konzept entfernt — `scripts/maintenance/clean_results.py`:** `SUB_FAMILY_LEADERBOARD_CSVS` (gemma_leaderboard.csv, qwen_leaderboard.csv) entfernt — die Dateien wurden nie generiert und nie in git getrackt (verwaistes Konzept). `CLEAN_CSV_FILES` ohne Sub-Family-LBs. Symmetrisch zu provider_leaderboard.csv-Stilllegung (v4.10.12).

### Fixed

- **`test_card_vocabulary_ssot::test_all_model_cards_pass_tag_whitelist`** (pre-existing failure): 4 Cards mit unbekannten Tags (Dense×3, Tool-Use×1) — durch deprecated-Aufnahme + Card-Bereinigung gelöst.
- **`test_clean_results_arch_coverage::test_dry_run_mentions_all_csv_files`** (pre-existing failure): erwartete verwaiste `gemma_leaderboard.csv`/`qwen_leaderboard.csv` im Dry-Run-Output — durch Sub-Family-Konzept-Entfernung gelöst.

### Added

- **Gemma-4-26B--VSPK ThinkingProbe (live):** Card hatte `thinking_probe_detected=null`. Probe via vllm_spark: 3/3 Probes detected → `detected=true, confidence=medium`. Alle 5 VSPK-Cards jetzt probed.
- **ux_writing_002 ornith-1-0-35b Re-Run (live):** Audit-Log existierte (60.25%), aber CSV-Zeile fehlte (Inkonsistenz nach Session-46-Cleanup). Re-Run: 5/5 Tests, Ø 71.91%, ux_writing_002=78.75%/Judge 4.0/5 (vormals 1.1% Reasoning-Loop). enable_thinking:false-Fix wirkt. CSV + Audit-Logs konsistent.

### Tests

- `make validate` 0 invalid. `pytest` **1079 passed / 1 skipped / 0 failures** (vorher 2 pre-existing failures). `test_vllm_spark_provider` 34/34 grün (Sampling-Chain-Tests kompatibel mit Whitelist-Refactor).

### Out of Scope

- Die in progress.md (Session 49) erwähnten „3 pre-existing `check:drift` True-Mismatches" sind Web-Repo-Checks (`check:drift`/`check:coverage` sind npm-Skripte in cruciblemark-web; Begriff „True-Mismatch" existiert nicht im Python-Repo). Nicht im Python-Repo fixbar.

---

## [v4.10.14] - 2026-07-07

**Card-Naming SUFFIX-SSoT-Alignment + `model_version`-Pollution-Migration (neues Feld `model_variant`).**

### Changed

- **`utils/model_utils.py:_card_path(for_write=True)` — PREFIX→SUFFIX:**
  `_card_path(for_write=True)` produzierte PREFIX `{shortcode}_{base}.json`, während `build_card_id()` (die bereits bestehende SSoT) SUFFIX `{base}--{shortcode}.json` erzeugte. Diese Divergenz zwischen zwei SSoT-Funktionen verursachte Duplikat-Karten (PREFIX-Version + unprefixed Auto-Generierung via `enforce_card_first`, weil `_find_card` den VSPK-Prefix nicht kannte). `_card_path(for_write=True)` ruft jetzt `build_card_id()` auf → SUFFIX. `_find_card()` Read-Reihenfolge: SUFFIX → legacy PREFIX → unprefixed (Backward-Compat für unrenamte Karten). 13 Karten per `git mv` umbenannt (5 VSPK, 8 SPRK). 2 Auto-Duplikate gelöscht (`Gemma-4-26B.json`, `Gemma-4-31B.json`).

- **`utils/card_utils.py:_CARD_TEMPLATE` — neues Feld `model_variant`:**
  Neue interne Fein-Tune-/Variant-Bezeichnung für Varianten wie MTP, Coder-MTP, Ortenzya Wordsmith, E4B, QAT, Abliterated. Landet zukünftig in `model_variant` statt in `model_version` (die reine Versionsnummer bleibt). Vorher hatten diese Tokens nowhere to go und leckten nach `model_version` (zusammen mit Quant-Tokens). Felder-Separierung SSoT: `model_version`=Versionsnummer, `model_variant`=interne Variante, `quantization_format`=Quant/Format, `hardware_profile`=Hardware (CSV-Spalte, bleibt dort).

- **`model_version`-Pollution-Migration (33 Karten + 1498 CSV-Zeilen):**
  33 Karten hatten Quant/Format-Tokens (`Q8_0 GGUF`, `FP8`, `NVFP4`) und interne Variant-Namen (`Ortenzya`, `MTP`, `Coder-MTP`) in `model_version` angesammelt, weil das korrekte Feld `quantization_format` in allen Karten `null` war. Atome Migration via `scripts/maintenance/migrate_model_versions_pollution.py` (explizite 33-Modell-Mapping-Tabelle, idempotent, mit Backup). Card-Felder (`model_version`/`model_variant`/`quantization_format`) UND CSV-`model_version`-Spalte zusammen aktualisiert (Groupby-Continuity — `model_version` ist Leaderboard-Groupby-Key, Split vermeiden). 2 vorgängige CSV/Card-Splits geheilt (`hermes-4-14b-abliterated`, `hermes-4-14b-q4` — Card bereits manuell bereinigt, CSV nie mit-migriert).

- **`scripts/analysis/generate_review.py:210-215` — SSoT-Delegation:**
  Direkten `_card_path()`-Aufruf entfernt, `ensure_card(model_id)` ohne expliziten Pfad (SSoT-Delegation an `build_card_id`).

### Added

- **`scripts/maintenance/migrate_model_versions_pollution.py`** — Atome Migration für `model_version`-Pollution. Explizite Mapping-Tabelle (keine Heuristiken), Dry-Run/`--apply`-Modi, Backup-Verzeichnis, Idempotenz-Checks.
- **`scripts/maintenance/audit_model_versions.py`** — Audit-Script für `model_version`-Drift (nach Migration: 0 flagged).
- **`tests/test_card_path_suffix_ssot.py`** — 12 Regressionstests (SUFFIX-Produktion, Read-Reihenfolge, SSoT-Konsistenz `build_card_id` ↔ `_card_path`).

### Tests

- `make validate` 0 invalid. `pytest` 1054 passed / 1 skipped / 2 pre-existing failures (unverändert — `test_card_vocabulary_ssot::test_all_model_cards_pass_tag_whitelist` "Dense"/"Tool-Use" Tags, `test_clean_results_arch_coverage::test_dry_run_mentions_all_csv_files` gemma_leaderboard.csv). CSV-Kontinuität: `model_id`-Felder in allen 13 Karten unverändert. Audit-Script 0 flagged. Leaderboard regeneriert, 0 Split-Rows.

---

## [v4.10.13] - 2026-07-04

**WebExport-Konsistenz-Fixes: `synthesis_quality`/`tool_execution` datenbasiert exportiert; Emoji-Variation-Selectors werden gestrippt.**

### Changed

- **`scripts/web_export.py:_build_leaderboard_entry()` — ToolUse-Scores datenbasiert:**
  `synthesis_quality` (ToolUse P1) und `tool_execution` (ToolUse P2) werden jetzt exportiert, sobald das Modell einen Wert im Leaderboard hat — unabhängig vom `supports_tool_use`-Flag. Zuvor wurden sie nur bei `supports_tool_use is True` exportiert, was 7 getestete Modelle mit `supports_tool_use: false` fälschlich ohne diese Scores ließ (command-a-plus-05-2026, openai_gpt-oss-20b, qwen2_5-coder-7b, qwen3-4b, qwen3-14b, qwen3_5-4b-*, qwen3_5-9b). Die Modelle haben echte ToolUse-Daten (P1/P2/combined) in `tooluse_leaderboard.csv`. Der detail-ToolUse-Block in `data.json.tooluse` (Per-Asset-Details, Radar, Reliability) bleibt weiterhin an `supports_tool_use=true` gebunden (Session-44-Frontend-Navigation). `supports_tool_use_state` ("true"/"false"/null) bleibt separates Capability-Indikator.

- **`scripts/web_export.py:_EMOJI_RE` — Variation Selectors + ZWJ ergänzt:**
  Die Emoji-Strip-Regex erfasste bisher die Emoji-Basiszeichen (z.B. ⏱ U+23F1), aber nicht die Variation Selectors U+FE0F (VS16) / U+FE0E (VS15) und die Zero Width Joiner U+200D. Nach `_strip_emojis("⏱\ufe0f Interactive")` blieb `"\ufe0f Interactive"` — ein unsichtbares Zeichen in `performance_tier`/`speed_profile`. Betraf ~20 Modelle. Jetzt werden VS16/VS15/ZWJ mit entfernt.

### Fixed

- **Dead-Code `_supports_tool_use` entfernt:** Die nach dem Refactor ungenutzte lokale Variable in `_build_leaderboard_entry()` (vorheriger einziger Konsument `_has_tooluse` wurde gelöscht) entfernt. `supports_tool_use_state` liest direkt `card.get("supports_tool_use")`.

### Tests

- **`tests/test_web_export_helpers.py`** — 5 neue Regressionstests: 2 für VS16/VS15/ZWJ-Stripping (`TestStripEmojis`), 3 für datenbasierte Synthesis-Export-Entscheidung (`TestSynthesisQualityDatenbasiert`) + `_lb_entry`-Helper.

### Verifikation

- 1002 passed / 1 skipped / 2 pre-existing failures (unrelated: `test_card_vocabulary_ssot::test_all_model_cards_pass_tag_whitelist`, `test_clean_results_arch_coverage::TestEndToEndCleanupDryRun::test_dry_run_mentions_all_csv_files`).
- VS16-Fix verifiziert: "⏱️ Interactive" → "Interactive".
- Synthesis-Fix verifiziert: stu=false+data → `synthesis_quality=51.67` exportiert; untested → Key absent.

### Nicht behoben (out of scope Python-Repo)

- **Problem 1 (Missing prices):** `command-a-plus-05-2026` + `ornith-1-0-35b` haben legitim null-Preise. Template-Fix `price-comparison-row.njk` (Web-Repo) ausstehend.
- **Problem 3 (architecture_tags vs features):** Python-Export bereits korrekt. Doppel-Rendering in `model-header.njk` (Web-Repo) ausstehend.

## [v4.10.8] - 2026-06-23

**Cohere ToolUse-Connector auf native `tools`-API migriert. `command-a-plus-05-2026` als `supports_tool_use=false` markiert (serverseitiger 500-Bug).**

### Changed

- **`utils/providers/cohere.py` — Native ToolUse-Connector:**
  Prompt-basierte JSON-Tool-Schemas im System-Prompt kollidierten mit Cohere's Reasoning-Modellen (HTTP 422/500). Die Lösung nutzt Cohere-native `tools`-API statt Prompt-Injektion:
  - **`_extract_tool_schema(system_prompt)`:** Extrahiert das Tool-Schema-JSON aus dem ToolUse-System-Prompt via Bracket-Counting. Erkennt das Marker `"Verfügbares Tool:\n"` und parst das folgende JSON-Objekt.
  - **`_schema_to_cohere_tools(schema)`:** Konvertiert das CrucibleMark-Tool-Schema ins Cohere-native Format (`{"type": "function", "function": {"name": ..., "parameters": ...}}`).
  - **`_format_tool_calls_as_text(response_message)`:** Extrahiert Tool-Calls aus Cohere's nativer Response und formatiert sie als JSON-Text (`{"tool_call": {"name": ..., "parameters": ...}}`), kompatibel mit dem ToolUse-Modul-Parser.
  - **Module-Key-Dispatch:** `_module_key == "tooluse"` triggert den nativen Pfad; alle anderen Module bleiben prompt-basiert (unverändert).
  - **Reasoning-Modell-Handling:** `_is_cohere_reasoning_model()` erkennt `command-a-reasoning` und `command-a-plus` als Substring-Match. Bei Native Tools + Reasoning-Modell → `thinking: {"type": "disabled"}` gesetzt (verhindert 422 durch auto-thinking).
  - **500-Retry:** 2 Retries mit exponentiellem Backoff (2s, 4s) für serverseitige 500-Fehler.

### Fixed

- **`command-a-plus-05-2026.json` — `supports_tool_use` auf `false`:**
  Cohere's erstes MoE-Modell (218B/25B aktiv) zeigt persistente HTTP 500 bei Benchmark-System-Prompts + nativen Tools. Einfache Prompts funktionieren, komplexe Benchmark-Szenarien nicht. Serverseitiger Bug, nicht clientseitig behebbar. `known_limitations`-Eintrag ergänzt.

### Benchmark-Ergebnisse (Cohere, nach Fix)

| Modell | Assets | P1 | P2 | Combined | Status |
|---|---|---|---|---|---|
| command-a-03-2025 | 4/6 live | 85.0 | 50.0 | 43.3 | 2× 422 intermittierend (fetch-Assets) |
| command-a-plus-05-2026 | 0/6 mock | 0.0 | 20.0 | 6.0 | `supports_tool_use=false` |
| command-a-reasoning-08-2025 | 6/6 live | 90.0 | 51.7 | 70.5 | Halluzination=YES |

## [v4.10.7] - 2026-06-22

**`clean-results`-Script: Vollständige Varianten-Auflösung für Model-IDs. `grok-4.1-fast-reasoning` vollständig entfernt. `_rebuild_index()`-Crash in `generate_review.py` gefixt.**

### Fixed

- **`scripts/maintenance/clean_results.py` — 5 Fixes für Variant-Handling:**
  - **Fix 1 (`clean_model_card`):** Löscht jetzt ALLE Card-Dateien für ein Modell (Underscore, Hyphen, Dot-Varianten). Vorher: nur eine Variante via `_safe_name()` → Orphan-Cards blieben übrig.
  - **Fix 2 (`clean_csv`):** Matched alle ID-Varianten direkt in CSV-Spalten (`model`, `Model ID`, `model_id_raw`). Vorher: nur kanonische Form → Orphan-Zeilen mit anderen Schreibweisen blieben.
  - **Fix 3 (Reihenfolge):** CSV-Bereinigung vor Card-Löschung. `resolve_canonical_model_id()` braucht die Card für die Variant-Auflösung — wenn die Card zuerst gelöscht wird, fehlt die Quelle.
  - **Fix 4 (`clean_model_output_directories`):** Variant-aware Matching für audit_logs, comparisons, runs, reviews via `_collect_model_id_variants()`.
  - **Fix 5 (neue Funktionen):** `clean_cost_log()` für `outputs/cost_log.csv`. `_dead_model_info()`-Checker (warnt wenn Modell in Blacklist oder provider_config auskommentiert). `LEADERBOARD_CSVS`-Konstante für `benchmark_leaderboard.csv` + `benchmark_leaderboard_detailed.csv`.
  - **Neue SSoT-Funktion `_collect_model_id_variants()`:** Sammelt alle Schreibweisen einer Model-ID (Underscore, Hyphen, Punkt) über `_safe_name()` + `_find_card()` + Card-Inhalt-Scan. Wird von allen Clean-Funktionen verwendet.

- **`scripts/maintenance/clean.py` — `--dry-run` Flag ergänzt:**
  - `argparse` akzeptierte `--dry-run` nicht, obwohl `Makefile` es übergab. Flag jetzt in beiden Dispatchern (`main()` + `main_with_args()`) verfügbar.

- **`scripts/analysis/generate_review.py` — `_rebuild_index()` Crash gefixt:**
  - Verwaister `mc_gen._rebuild_index()`-Aufruf (Zeile 200) + unbenutzter `mc_gen`-Import entfernt. Die Funktion wurde in `utils.card_template.rebuild_card_index()` verschoben, aber der Caller nicht aktualisiert. Symptom: `AttributeError` bei `reviews-auto` Lauf (Modell 54/118).

- **Dead-Model `grok-4.1-fast-reasoning` vollständig entfernt:**
  - 49 CSV-Zeilen, 256 cost_log-Einträge, 6 Leaderboard-Einträge, 1 Model Card, audit_logs-Dir, reviews-Dir.
  - Alle 3 ID-Varianten (`grok-4_1-fast-reasoning`, `grok-4-1-fast-reasoning`, `grok-4.1-fast-reasoning`) bereinigt.

### Added

- **`--dry-run` Support für `make clean-model`:** `make clean-model MODEL=x DRY=1` zeigt jetzt korrekt eine Vorschau ohne zu löschen (funktioniert mit dem neuen `--dry-run`-Flag in `clean.py`).

## [v4.10.6] - 2026-06-22

**Anthropic Provider-Cap angehoben (8192→32768). 144 verfälschte Benchmark-Zeilen entfernt (MAX_TOKENS + CI@500). Leaderboard aktualisiert.**

### Changed

- **`config/provider_config.yaml` — Anthropic `max_tokens` 8192 → 32768:**
  Der bisherige Provider-Default von 8192 war zu niedrig für Claude 4.x Modelle (unterstützen bis 128K Output).
  `code_quality` (Reasoning-Budget 20000) wurde auf 8192 gecappt (−59%), `documentation_quality` (12000) auf 8192 (−32%).
  Neuer Default 32768 gibt allen Reasoning-Budgets ausreichend Spielraum.
  Per-Model Override für `claude-haiku-4-5-20251001`: 8192 (Desktop-Klasse, kein Thinking-Tag).
  `fallback_max_tokens: 4096` entfernt — wurde nirgends im Code gelesen (Dead Config).

### Fixed

- **144 verfälschte Benchmark-Zeilen entfernt aus `commercial_models_benchmark.csv`:**
  Zwei Kategorien von Token-Limit-Artefakten identifiziert und bereinigt:
  - **Kategorie A — MAX_TOKENS-Truncation (24 Zeilen, 5 Modelle):** Antworten wurden durch `max_tokens` hart abgeschnitten (`finish_reason: max_tokens`). Betroffen: gemini-3.5-flash (9 Tasks), gemini-2.5-flash (7), gemini-3-flash-preview (5), claude-opus-4-6 (2), claude-opus-4-5 (1).
  - **Kategorie B — Cultural Intelligence bei 500 Tokens (130 Zeilen, 26 Modelle):** Alle 5 CI-Tasks liefen mit dem uralten Limit von 500 Tokens (April/Mai 2026). Aktuelles Budget: 3000 (Standard) / 4000 (Reasoning). Kein einziges Modell wurde zwischenzeitlich nachgetestet.

  **Auswirkung auf Leaderboard:** 27 Modelle zeigen jetzt fehlende Tasks (34/43 bis 38/43 statt 43/43). CI-Scores auf "Pending". Beim nächsten `benchmark_auto`-Lauf werden genau die 144 betroffenen Tasks automatisch nachgetestet.

  **Backup:** `commercial_models_benchmark.csv.bak_token_cleanup_20260622`

## [v4.10.5] - 2026-06-21

**Reasoning/Thinking-Extraktion: SSoT-Utilities in `base.py`. Streaming-Bugs in OpenRouter + llamacpp gefixt. Judge erhält universelle Token-Verbrauchsinformation.**

### Added

- **Judge TOKEN USAGE Context (universal für alle Modelle):**
  Der LLM-Judge erhält jetzt für JEDE Aufgabe die tatsächliche Token-Verbrauchsinformation:
  - `tokens_used` — Gesamtverbrauch
  - `reasoning_tokens` — Thinking/Reasoning-Anteil
  - `token_budget` — das tatsächlich gesetzte `max_tokens` (API-Limit)
  - `module_budget` — das konfigurierte Modul-Budget aus `benchmark_config.yaml`
  - `truncated` — ob die Antwort abgeschnitten wurde

  Der Judge kann damit beurteilen, ob das Modell:
  - sein Token-Budget eingehalten hat
  - übermäßig viel Thinking-Token verbraucht hat
  - die Antwort innerhalb des Limits abgeschlossen hat

  Bisher sah der Judge nur Budget-Bereiche (standard/elevated) für Reasoning-Modelle,
  aber nie den tatsächlichen Verbrauch. Drei separate, bedingte Kontexte
  (reasoning, truncation, small_model) wurden durch den universellen Context ergänzt.

  **Dateien:**
  - `utils/scoring/judge_evaluator.py`: Baut `token_usage_context` aus result dict
  - `utils/scoring/llm_judge/judge_runner.py`: Neuer `token_usage_context` Parameter in `score()`
  - `utils/scoring/llm_judge/judge_prompt_builder.py`: Neuer Parameter + TOKEN USAGE NOTE Section

### Fixed

- **`utils/providers/openrouter.py` Streaming — `reasoning_tokens` fehlte:**
  Der Streaming-Pfad extrahierte `usage` und `think_content` korrekt, aber `_extract_reasoning_tokens()` wurde nie aufgerufen. Downstream-Konsumenten (`judge_evaluator.py:272`, `base_runner.py:159`) erhielten `None` für OpenRouter-Streaming-Responses.

- **`utils/providers/llamacpp_base.py` Streaming — `reasoning_tokens` + `think_content` fehlte:**
  Der Streaming-Las `delta.content` nur — `delta.reasoning_content` (llama.cpp-natives Thinking-Feld) wurde ignoriert. `_extract_response_content()` (Non-Streaming) wurde nicht aufgerufen. Fix: Think-Content-Akkumulation + Post-Stream `reasoning_tokens`-Extraktion.

### Added (SSoT)

- **`utils/providers/base.py` — 3 Reasoning/Thinking-Extraktions-Utilities (SSoT):**
  1. `_extract_reasoning_tokens(usage)` — Provider-agnostisch. Prüft: `completion_tokens_details` (OpenAI-kompatibel) → `output_tokens_details` (Anthropic) → `usage.reasoning_tokens` (Mistral-Fallback). ersetzt 5 identische lokale Methoden in openai.py, groq.py, xai.py, anthropic.py + Inline-Code in openrouter.py, mistral.py, llamacpp_base.py.
  2. `_extract_think_from_message(msg, field_names)` — Generisch. Versucht `getattr(msg, field)` für jedes Feld. Ersetzt identische Inline-Patterns in openai.py, groq.py, xai.py, openrouter.py.
  3. `ThinkAccumulator` — Streaming-Helper. `add(chunk)` → `content`/`has_content`. Ersetzt `think_parts: list[str]` + `"".join(think_parts)` in allen 7 Streaming-Pfaden.

- **9 Provider auf Shared Utilities umgestellt:**
  | Provider | `_extract_reasoning_tokens` | `_extract_think_from_message` | `ThinkAccumulator` |
  |---|---|---|---|
  | openai.py | Delegation auf Base | ✅ Non-Streaming | ✅ Streaming |
  | anthropic.py | Delegation auf Base | — (eigene `_extract_think_content`) | ✅ Streaming |
  | groq.py | Delegation auf Base | ✅ Non-Streaming | ✅ Streaming |
  | xai.py | Delegation auf Base | ✅ Non-Streaming | ✅ Streaming |
  | openrouter.py | Inline → Base | ✅ Non-Streaming | ✅ Streaming |
  | google.py | Inline (`thoughts_token_count`) | — (candidate parts) | ✅ beide Pfade |
  | mistral.py | Inline → Base | — (Chunk-Liste) | — (kein Streaming) |
  | ollama.py | Inline (`eval_count`-Heuristik) | Inline (`msg.thinking`) | — (always streaming, eigene Logik) |
  | llamacpp_base.py | Inline → Base + Fallback | Inline (`reasoning_content`) | ✅ Streaming |

---

## [v4.10.4] - 2026-06-21

**CSV-Write-Through Bug: Atomare Schreibvorgänge + Existing-Row-Schutz. Provider-Config Cleanup.**

### Fixed

- **`utils/result_manager.py` `_write_to_csv()` — 3 Root Causes für Datenverlust:**
  1. **Truncate-on-Open (`"w"`):** `_write_to_csv()` öffnete die CSV mit `"w"` (truncate). Bei Kill/Crash während des Full-Rewrites gingen ALLE Daten verloren — die Originaldatei war bereits gelöscht bevor die neue geschrieben war. **Fix:** Atomare Schreibvorgänge via `tempfile.mkstemp()` + `os.replace()`. Originaldatei bleibt intakt bis der Write komplett ist. Bei Fehler: Temp-Datei wird aufgeräumt.
  2. **Re-Validierung aller Existing Rows:** Bestehende Zeilen wurden bei jedem Full-Rewrite durch die Hard-Fail-Guard-Validierung gejagt. Wenn sich die Validierungslogik änderte (z.B. neue Pflichtfelder), wurden alte, bereits gültige Zeilen verworfen. **Fix:** Nur neue Zeilen werden validiert. Existing Rows aus der CSV werden ungeprüft übernommen — sie waren gültig als sie geschrieben wurden.
  3. **`_csv_header_matches()` — exakter Vergleich beibehalten:** Tolerantes Matching (Teilmengen-Vergleich) hätte im Append-Path Zeilen mit falscher Spaltenanzahl erlaubt. Full-Rewrite ist jetzt sicher durch atomare Writes → exakter Match ist korrekt.

- **Root Cause für 10 Modelle mit 0 CSV-Einträgen:**
  10 Modelle (llama-3.3-70b-versatile, llama-4-scout, nemotron-3-ultra, qwen3-32b, qwen3.5-397b, glm-4.7, glm-5-20260211, glm-5-turbo, glm-5.1, glm-5.2) hatten dispatch summaries + audit logs aber LEERE CSVs. Ursächlich: ein Full-Rewrite während eines Session-Wechsels (Kill/Restart) verwarf alle Daten. Die Audit-Logs enthalten alle Daten — Re-Run der Modelle oder `sanitize_benchmark_csvs.py`-Rekonstruktion möglich.

- **`deepseek/deepseek-chat-v3.1` — abgebrochenes Modell:**
  34/43 Tasks in CSV (Write-Through funktionierte korrekt). Fehlende Tasks: content_transformation 003-005, cultural_intelligence, tooluse. Audit-Logs vollständig für alle 34 abgeschlossenen Tasks.

### Added

- **4 neue Tests in `tests/test_result_manager_validates.py`:**
  - `test_full_rewrite_preserves_existing_rows_not_revalidated` — Existing Rows werden beim Full-Rewrite nicht re-validiert
  - `test_atomic_write_no_corruption_on_header_mismatch` — Bei Header-Mismatch: Originaldatei bleibt intakt
  - `test_write_through_fast_path_single_result` — O(1) Append bei neuem (model, asset_id)
  - `test_upsert_dedup_replaces_existing_row` — Gleiche (model, asset_id) Kombination wird ersetzt

### Changed

- **`config/provider_config.yaml` — Cleanup (-130 Zeilen):**
  Redundante navigational/description Kommentare entfernt. 92 aktive Modelle + alle auskommentierten Modelle erhalten. Technische Kommentare (Hermes SWA, enable_thinking: false, MTP, Hybrid-Attention) beibehalten. Section-Header (`# ── Aktive Spark-Modelle ──`) ersetzen nummerierte Einträge.

---

## [v4.10.3] - 2026-06-21

**Token-Budget-Refactoring: SSoT-Helper `_resolve_request_tokens()` in `base.py`. Provider-Kaskade `max_tokens`. Design-Constraints dokumentiert.**

### Added

- **`utils/providers/base.py` `_resolve_request_tokens()` — Zentrale Token-Budget-Auflösung (SSoT):**
  Alle 7 API-Provider-Connectors (openrouter, openai, anthropic, groq, xai, google, mistral) nutzen jetzt einen Shared Helper in `base.py` statt inline duplizierter Token-Logik. Zweistufige Kaskade:
  1. `resolve_token_budget()` — Reasoning-/Thinking-Erkennung + Modul-Budgets aus `benchmark_config.yaml`
  2. Provider-Default `max_tokens` → Per-Model Override `model_max_tokens[model_id]` aus `provider_config.yaml`

  Neue Klassen-Attribute auf `BaseProviderClient`: `PROVIDER_CONFIG_KEY` (z.B. `"openrouter"`) und `DEFAULT_TOKEN_PARAM` (z.B. `"max_tokens"`). Neuer Provider → nur Attribut setzen, fertig.

- **`config/provider_config.yaml` — Provider-Default `max_tokens` für alle 7 API-Provider:**
  | Provider | Default | Per-Model Overrides |
  |---|---|---|
  | openrouter | 16384 | kimi-k2.7-code: 25000, kimi-k2.6: 20000, kimi-k2.5: 18000, deepseek-v4: 16000 |
  | openai | 16384 | gpt-4o: 4096, gpt-4o-mini: 4096 |
  | anthropic | 8192 | — |
  | xai | 16384 | — |
  | groq | 16384 | — |
  | google | 16384 | — |
  | mistral | 16384 | — |

- **`benchmark_config.yaml` — Token-Budget-Optimierung (empirisch kalibriert):**
  | Budget | Vorher | Nachher | Begründung |
  |---|---|---|---|
  | `code_quality` (Reasoning) | 65536 | 20000 | p99=16382, max=24985 (kimi-k2.7-code). Reduktion von 85 Min/Task auf 26 Min/Task bei 12.75 T/s |
  | `cultural_intelligence` (Standard) | 1000 | 3000 | Cloud-p90=2893 |
  | `documentation_quality` (Standard) | 6000 | 8000 | Cloud-p90=7789 |

### Fixed

- **`utils/providers/anthropic.py`, `groq.py`, `xai.py`, `google.py` — Token-Budget fehlte komplett:**
  Diese 4 Provider gaben `max_tokens` unverändert an die API durch, ohne `resolve_token_budget()` aufzurufen. Reasoning-/Thinking-Modelle erhielten kein elevated Budget → Antworten wurden abgeschnitten. Jetzt: alle 7 Provider nutzen `_resolve_request_tokens()`.

- **`utils/providers/openrouter.py` — Hardcoded `"max_tokens"` in Fallback-Call:**
  `_execute_with_token_fallback()` erhielt hardcoded `"max_tokens"` statt des config-aufgelösten `token_param_name`. Bei Provider-Config-Override wäre der falsche Parametername verwendet worden.

- **Duplikat-Code entfernt:**
  `groq.py` und `xai.py` enthielten nahezu identischen Token-Handling-Code (Copy-Paste). Beide nutzen jetzt den Shared Helper. ~30 Zeilen Duplikat eliminiert.

### Design Constraints (dokumentiert)

- **Sequenzielle Modell-Abarbeitung:** `systemPatterns.md` + `AGENTS.md` — Modelle werden einzeln getestet, Server-Restart + Cooldown zwischen Modellen. Kein Performance-Bug — garantiert gleichwertige Testumgebungen.
- **Judge-Reset zwischen Tasks:** `systemPatterns.md` + `AGENTS.md` — Jede Bewertung ist ein frischer API-Call. Kein Caching — verhindert Kontextmix.

---

## [v4.10.2] - 2026-06-21

**Judge-Pipeline: Reasoning-Modelle mit leerem `content`-Feld nicht mehr als Safety-Refusal markiert. + CSV Write-Through gegen Datenverlust.**

### Fixed

- **`scripts/core/unified_runner.py` `_handle_single_asset` — CSV Write-Through (Datenverlust-Fix):**
  Jedes Benchmark-Ergebnis wird jetzt SOFORT nach der Generierung in die CSV geschrieben (`save_results([result])`), nicht erst gesammelt am Ende des gesamten Runs. Vorher: bei Crash/Kill/Timeout zwischen Tasks waren ALLE Ergebnisse des Runs verloren — Audit-Logs blieben (werden pro Task geschrieben), CSV aber leer. Der finale `save_results(results)`-Aufruf in `benchmark_auto.py:498` und `run_score_benchmark.py:180` bleibt als Safety-Netz (Upsert ist idempotent).
  
  Root Cause: 35 Modelle (minimax M3, Xiaomi MiMo, NVIDIA Nemotron, DeepSeek V4 etc.) hatten vollständige Scoring-Audit-Logs aber leere CSV-Einträge — der Batch-Write am Ende wurde nie erreicht.

- **`scripts/core/unified_runner.py` `_apply_judge_pipeline` — Reasoning-only Response Detection:**
  Reasoning-Modelle (GLM-5.x via OpenRouter, Claude Extended Thinking, o-Series, etc.) geben ihre Antwort teils im separaten `reasoning`/`think_content`-Feld zurück statt im `content`-Feld. Wenn `content` kürzer als `MIN_REFUSAL_CHARS` (15) Zeichen ist, aber `think_content` aus `last_response_metadata` substantiell ist, wird jetzt `think_content` als effektive Antwort für den Judge verwendet.
  
  Vorher: `raw_response = content` (leer/zu kurz) → `refusal_flag=True` → Judge wird übersprungen → Score 0%.
  Nachher: `effective_response = think_content` → Judge bewertet das tatsächliche Reasoning → valides Score.
  
  Neues Feld `result["reasoning_only_response"]: True` markiert diesen Fall für Audit/CSV. Nur wenn BEIDE Felder zu kurz sind, wird der Refusal-Flag gesetzt.

- **Betroffenes Modell:** GLM-5.2 (`z-ai/glm-5.2`) — Code Quality Test 1 lieferte valides Reasoning im `reasoning`-Feld, aber leeres `content`-Feld → wurde fälschlich als "Unusable Specialist" mit 0.0% bewertet.

### Impact

- Reasoning-Modelle, die ihre Antwort primär im `reasoning`-Feld zurückgeben, werden nicht mehr fälschlich als Safety-Refusal klassifiziert.
- Der Judge bewertet jetzt das tatsächliche Reasoning-Output solcher Modelle.


## [v4.10.1] - 2026-06-20

**Provider-Connectors: Vollständige Thinking/Reasoning vs. Response-Token-Trennung. Sampling-Keys SSOT-Fix.**

### Fixed

- **Alle Provider-Connectors extrahieren jetzt konsistent `reasoning_tokens`, `think_content` und `usage`** in `last_response_metadata`:
  - **`anthropic.py`** — Vollständiger Fix: `think_content` aus `response.content` Blocks mit `type="thinking"`, `reasoning_tokens` aus `usage.output_tokens_details.reasoning_tokens`. **Streaming-Pfad neu implementiert** (`_query_streaming`): akkumuliert `thinking_delta`-Chunks aus `content_block_delta`-Events, trackt `usage` aus `message_start`/`message_delta`-Events.
  - **`openai.py`** — `think_content` aus `msg.reasoning` / `msg.reasoning_content` (Non-Streaming) und `delta.reasoning` (Streaming). `reasoning_tokens` aus `usage.completion_tokens_details.reasoning_tokens` in beiden Pfaden.
  - **`google.py`** — `think_content` aus `candidates[0].content.parts[].thinking`. `usage_metadata` jetzt in `last_response_metadata["usage"]` gespeichert (vorher fehlend). `reasoning_tokens` aus `thoughts_token_count` bereits korrekt.
  - **`groq.py`** — `think_content` und `reasoning_tokens` in beiden Pfaden extrahiert. `usage` jetzt auch im Streaming-Pfad gespeichert.
  - **`xai.py`** — `think_content` und `reasoning_tokens` in beiden Pfaden extrahiert. `usage` jetzt auch im Streaming-Pfad gespeichert.
  - **`ollama.py`** — `usage` als Dict (`prompt_tokens`/`completion_tokens`/`total_tokens`) aus `prompt_eval_count`/`eval_count` erstellt. `reasoning_tokens` aus `eval_count` gesetzt wenn Thinking erkannt wurde (Ollama liefert keine separate Count). `think_content` jetzt in `last_response_metadata["think_content"]` gespeichert.
  - **`mistral.py`** — `reasoning_tokens` aus `usage.completion_tokens_details.reasoning_tokens` oder `usage.reasoning_tokens` extrahiert. `think_content` wird jetzt immer gesetzt wenn Thinking-Chunks vorhanden sind (vorher nur bei leerem Content).

- **Model-Card Sampling-Keys SSOT-Fix** — Fehlende 7 Sampling-Default-Felder (`top_p`, `top_k`, `repetition_penalty`, `frequency_penalty`, `presence_penalty`, `seed`, `stop_sequences`) in 3 Cards ergänzt:
  - `gemma-4-31b-it-creative-wordsmith-q8.json`: `presence_penalty: null`
  - `hermes-4_3-36b-q6.json`: alle 7 Sampling-Keys als `null`
  - `mistral-large-2512.json`: alle 7 Sampling-Keys als `null`

- **Model-Card Taxonomy-Placeholder entfernt** — `gemini-3-flash-preview.json`: `parameter_architecture: "unknown"` (verbotener Placeholder) → `"dense"` (gültiger Taxonomie-Wert).

### Impact

- **Judge-Evaluation:** Thinking-Aufwand pro Aufgabe wird jetzt pro Provider gemessen — Judge sieht reale `reasoning_tokens` aus `last_response_metadata`.
- **Cost-Analyse:** `LLMParser.extract_usage_tokens()` greift jetzt auf echte `usage`-Objekte zu (vorher fiel es auf `estimate_tokens()` zurück). Reasoning-Tokens werden korrekt als `completion_tokens` abgerechnet.
- **Benchmark-Qualität:** `tokens_used` zählt reale API-Tokens statt geschätzte Zeichen-Tokens.
- **`_extract_reasoning_tokens(usage)` Helper** wurde als DRY-Pattern in `anthropic.py`, `openai.py`, `groq.py`, `xai.py` eingeführt (OpenAI-kompatibles Schema: `usage.completion_tokens_details.reasoning_tokens`).

### Tests

- 819/819 Tests grün (Stand 2026-06-20).
- 2 vorbestehende Failures (`test_sampling_defaults_ssot.py`, `test_taxonomy_ssot.py`) behoben.

---

## [v4.10.0] - 2026-06-20

**Card-Research Force-Run: 110/110 Cards `profile_verified=true`. Template-Cleanup, Batch-Processing, `MODEL=all`.**

### Changed

- **`config/card_template_model.yaml`** — 6 Felder von `required` auf `optional` verschoben:
  `params_total_b`, `params_active_b`, `knowledge_cutoff`, `license_url`,
  `input_price_per_1m`, `output_price_per_1m`. Beschreibungen sagten "null wenn X" aber
  `required: true` war ein Widerspruch — `is_unknown_sentinel(None)` returned `True`,
  also wird `null` bei `required: true` als Fehler gewertet. Template: 42 → 37 required Felder.

### Added

- **`scripts/manage_model_cards.py` — `MODEL=all` Support** — `--card all` wird als
  Spezialwert erkannt (gleichbedeutend mit kein `--card`). Early-Validation in `main()`
  erkennt `all` ebenfalls.

- **`scripts/manage_model_cards.py` — `MAX_CARDS=N`** — Neuer CLI-Arg `--max-cards N`
  + Makefile-Variable `MAX_CARDS`. Limitiert Targets pro Run. Fortschrittsanzeige am Ende:
  `📊 Fortschritt: X verarbeitet, Y noch offen.`

### Fixed

- **`scripts/tools/probe_thinking.py`** — `card_path.relative_to(ROOT_DIR)` crash bei
  relativen Pfaden. Fix: `card_path.resolve().relative_to(ROOT_DIR)` mit Fallback.

- **110 Model Cards** — Alle `profile_verified=true` durch vollständigen Force-Run.
  9 lokale Modelle: Thinking-Probe-Placeholder manuell ersetzt (Ollama entfernt).
  7 Cards: `thinking_probe_at` Timestamp nachgetragen.
  1 Card (`claude-sonnet-4-5-20250929`): `license_url` manuell gesetzt.
  1 Card (`gemma-4-26B-A4B-it-UD-Q8_K_XL`): `supports_tool_use=False` gesetzt.

### Removed

- **`scripts/web_export.py` — None-Werte im Export** — `_strip_none()` entfernt
  `None`-Werte rekursiv aus allen exportierten Dicts (Leaderboard-Entry, `model_card`-Sub-Dict,
  Political-Compass-Entry, `data.json`). Felder mit Wert (`0`, `False`, `""`, `[]`) bleiben
  erhalten. `"model_card": null` wird komplett entfernt (Key fehlt statt `null`). Neue
  Export-Felder: `profile_verified_by`, `last_modified_at`.

### Tests

- Parse-Fehler bei `qwen3_5-9b` (1×) — LLM lieferte kein valides JSON, Retry erfolgreich.
- `Apache-2.0` vs `Apache 2.0` — LLM interpretiert als Lizenz-Wechsel, rewrite't alle
  Textfelder (viel Lärm, aber korrektes Ergebnis).

---

## [v4.9.3] - 2026-06-12

**Vendor Card Template v1.1.0 — `description`-Feld + Editor-Prompt-Fix.**

### Added

- **`config/card_template_vendor.yaml` v1.1.0 — Optionalfeld `description`** — Redaktionelle
  Kurzbeschreibung der Organisation für die CrucibleMark-Website. Semantisch getrennt von
  `privacy_note` (Compliance-Text): `description` = "Wer sind die, was machen die?" (Editorial),
  `privacy_note` = "Wie werden Daten verarbeitet?" (Compliance).
  Constraints: min 240 / max 480 / Ziel 360 Zeichen. Konsumenten: `web_export`, `review`.
  `web_export.py::_collect_vendor_cards()` exportiert alle Felder dynamisch — kein Allowlist-Change nötig.

### Fixed

- **`config/editor_prompts.yaml` — `provider_card_verification`-Prompt** — Drei Fehler korrigiert:
  1. `targets.directory`: `benchmark_scores/provider_cards/` → `benchmark_scores/vendor_cards/`
     (Verzeichnis existiert nach v4.9.1-Rename nicht mehr)
  2. Prompt-Text Abschnitt "Auftrag": gleicher Pfad-Fix
  3. Feldname `provider_id` → `vendor_id` an zwei Stellen (Schritt 1 "Datei lesen" +
     Schritt 4 "NICHT verändern")

### Tests

- **`tests/test_card_template.py::test_provider_template_loads`** — Versionsassert
  von `"1.0.0"` auf `"1.1.0"` aktualisiert. **803/803 Tests grün.**

---

## [v4.8.5] - 2026-06-10

**Pricing-Update: Modellkarten-Preise auf Stand Juni 2026 aktualisiert.**

11 kommerzielle Modellkarten hatten veraltete oder fehlende `input_price_per_1m` /
`output_price_per_1m`-Felder. Neues Wartungsskript `update_model_pricing.py`
führt zukünftige Preisanpassungen ohne manuelle JSON-Edits durch.

### Added

- **`scripts/update_model_pricing.py`** — Neues Wartungsskript. Lädt alle
  `benchmark_scores/model_cards/*.json`, matcht Model-IDs gegen `CURRENT_PRICING`
  (exakt oder Präfix-Match), schreibt `input_price_per_1m` und `output_price_per_1m`
  nur wenn sich der Wert ändert, setzt `generated_at` auf aktuellen Timestamp.
  Preisstand: OpenAI, Anthropic, Google Gemini, Mistral, xAI Grok — Juni 2026.

### Changed

- **11 Modellkarten aktualisiert** (`gpt-4o-mini`, `gpt-5`, `gpt-5-mini`,
  `grok-3`, `grok-3-mini`, `magistral-medium-latest`, `magistral-small-latest`,
  `mistral-large-2411`, `mistral-large-2512`, `mistral-medium-3-5`,
  `qwen3-coder-next-q8`): `input_price_per_1m` und `output_price_per_1m`
  auf recherchierte Marktpreise gesetzt.

---

## [v4.8.4] - 2026-06-10

**Backup-System-Audit: 3 SSoT-Abweichungen in cleanup_reviews, Tests und Docs behoben.**

Vollständige Prüfung des Backup-Systems nach Phase-27-Refactoring.
Makefile und Kern-Skripte korrekt. 3 Abweichungen identifiziert und behoben.

### Fixed

- **`scripts/maintenance/cleanup_reviews.py`** — `REVIEWS_KEEP_PER_CATEGORY`
  aus `utils/backup_targets` (SSoT) nicht importiert. Hardcoded `[1:]` in 3
  `to_delete.extend()`-Aufrufen. Fix: Import ergänzt, `[1:]` → `[REVIEWS_KEEP_PER_CATEGORY:]`.

- **`tests/test_backup_targets.py`** — Test-Lücke: `audit_logs_legacy_backup_*`
  fehlte in der `required`-Menge von `test_build_tar_excludes_contains_critical_patterns`.
  Fix: Pattern ergänzt. **28/28 Backup-Tests grün.**

- **`docs/BACKUP_STRATEGY.md` Abschnitt 4.3** — Zeigte vereinfachtes, veraltetes
  Makefile-Recipe: falscher Skript-Pfad (`cleanup_runs.py --keep` statt `make clean-runs`),
  7 fehlende tar-Excludes (`.DS_Store`, `audit_logs_legacy_backup_*`,
  `audit_logs_spurious_archive`, `audit_logs.zip`, `model_cards_backup_*.tar.gz`,
  `model_cards_spurious_archive`, `outputs/temp/session_*.json`), fehlende
  Post-Backup-Schritte (`clean-bak`, `clean-reviews FORCE=1`, `prune-orphans FORCE=1`).
  Neuer Hinweis: Exclude-Liste muss synchron mit `build_tar_excludes()` gehalten werden.

---

## [v4.8.3] - 2026-06-10

**ToolUse P1/P2 NaN-Bug behoben — Flat-Column-Schema eingeführt.**

`qwen3-coder-next-q8` zeigte nach erfolgreichem ToolUse-Lauf (6/6 Tests, live MCP)
`P1=NaN`, `P2=NaN`, `mcp_mode=mock` im Leaderboard. Root Cause:
`_aggregate_asset_rows()` las P1/P2 aus dem deprecated `score_contributions`-Feld,
das seit dem Writer-Redesign nicht mehr geschrieben wird.
Zusätzlich: `CRUCIBLE_DELEGATE_PARENT`-Env-Var wurde in `run_score_benchmark.py`
zu früh gesetzt → MCP wurde nie gestartet. MCP-Idle-Timeout deaktiviert (GGUF-Ladezeit
bis 420 s).

### Fixed

- **`scripts/core/unified_runner.py` `_build_result_envelope()`** — ToolUse-Felder
  als flache CSV-Spalten aus `exec_result.data` promoten (Duck-Typing:
  `"p1_score" in exec_result.data`). Felder: `p1_score`, `p2_score`, `combined_score`,
  `mcp_mode`, `tool_call_valid`, `tool_call_attempts`, `mcp_latency_s`, `call1_time_s`,
  `call2_time_s`, `total_time_s`, `call1_tokens`, `call2_tokens`, `hallucination_flag`.

- **`scripts/core/tooluse_exporter.py` `_aggregate_asset_rows()`** — Flat-Column-
  Fallback nach `score_contributions`-Parsing; Boolean-Konvertierung;
  `mcp_mode`-Fallback via `row.get("mcp_mode") == "live"`.
  `score_contributions`-Feld ist deprecated — Flat-Columns sind SSoT.

- **`scripts/run_score_benchmark.py`** — `CRUCIBLE_DELEGATE_PARENT` darf nur
  von `run_tooluse_benchmark.py` gesetzt werden. Guard hinzugefügt:
  `os.environ.pop("CRUCIBLE_DELEGATE_PARENT", None)` am Skript-Start, damit
  ein fälschlicherweise gesetztes Env-Var den MCP-Start nicht verhindert.

- **`cruciblemark-mcp/config/mcp_config.yaml`** — `idle_timeout_seconds: 0`
  (Idle-Timeout deaktiviert). GGUF-Modelle auf dem DGX Spark brauchen bis 420 s
  zum Laden — der MCP-Server darf währenddessen nicht disconnecten.

- **`benchmark_scores/model_cards/qwen3-coder-next-q8.json`** — Direkt-Patch:
  `p1_score=90.00`, `p2_score=59.17`, `combined_score=74.62`, `mcp_mode=live`,
  `hallucination_flag=true` aus dem Live-Lauf eingetragen.

---

## [v4.8.2] - 2026-06-10

**Fix: `gpt-5.4-nano` — Card `model_id` auf API-korrekte Punkt-Form korrigiert.**

Die Card `gpt-5_4-nano.json` wurde manuell mit `model_id: "gpt-5_4-nano"` (Underscore)
erstellt — korrekt als Dateiname (Filesystem-Konvention), aber falsch als interner `model_id`-Wert.
`resolve_canonical_model_id()` findet die Card über `_safe_name` (Dateiname = Underscore),
gibt aber `card.model_id` zurück. War das `gpt-5_4-nano` (Underscore), scheiterte der
OpenAI-API-Call mit 404. Die anderen GPT-Modelle (`gpt-5_4`, `gpt-5_4-mini`, `gpt-5_5`)
akzeptiert OpenAI zufällig auch in Underscore-Form — `gpt-5.4-nano` jedoch nicht.

### Fixed

- **`benchmark_scores/model_cards/gpt-5_4-nano.json`** — `model_id` von `gpt-5_4-nano`
  auf `gpt-5.4-nano` korrigiert. Dateiname bleibt `gpt-5_4-nano.json` (Underscore-Konvention).
  `resolve_canonical_model_id("gpt-5.4-nano")` → findet Card über `_safe_name` →
  gibt `gpt-5.4-nano` zurück → API-Call erfolgreich.

- **`tests/test_resolve_canonical_model_id.py`** — Zwei Regressionstests ergänzt:
  `gpt-5.4-nano` und `gpt-5_4-nano` → beide erwarten `gpt-5.4-nano` (dot-form aus Card).

- **`scripts/maintenance/cleanup_helpers.py`** — `canonical_model_slug()`:
  Wendet jetzt explizit `_safe_name(canonical)` an statt das Ergebnis von
  `resolve_canonical_model_id` direkt zurückzugeben. Behebt Regression aus
  v4.8.1: Der veränderte Fallback (`return base` statt `return _safe_name(base)`)
  ließ Whitespace-Eingaben (`"  "`) als `"  "` statt `"__"` zurückkehren.
  `canonical_model_slug` ist für Dateisystem-Slugs gedacht — `_safe_name` als
  letzter Schritt ist hier immer korrekt (Punkte/Leerzeichen/Slashes → Underscores).

- **`utils/model_utils.py`** — `resolve_canonical_model_id()`: Fallback von
  `return base` (v4.8.1) zurück auf `return _safe_name(base)` gesetzt. Die
  systemweite Konvention ist Punkte/Doppelpunkte → Underscores; der v4.8.1-
  Fallback-Wechsel war unnötig, da der eigentliche Fix für `gpt-5.4-nano` in der
  Card-`model_id` liegt (Pfad 3: `card.model_id = "gpt-5.4-nano"`). Der
  `_safe_name`-Fallback betrifft nur Modelle OHNE Card — dort ist die
  Underscore-Form konsistent mit CSVs, Card-Dateinamen und Leaderboard.
  3 zuvor fehlschlagende Tests (`test_enforce_card_first`,
  `test_consolidate_csv` ×2) sind damit wieder grün. **788/788 Tests grün.**

- **`tests/test_resolve_canonical_model_id.py`** — `qwen3.5-35b-a3b-q6`
  Test-Case zurück auf erwartetem Wert `qwen3_5-35b-a3b-q6` (Underscore, via
  `_safe_name`-Fallback). Konvention: kein Card → Underscore-Form.

---

## [v4.8.1] - 2026-06-10

**Fix: Kommerzielle API-Modelle mit Punkt in der ID schlugen mit HTTP 404 fehl.**

`gpt-5.4-nano` (und andere OpenAI-Modelle mit Versionspunkten) wurden als
`gpt-5_4-nano` an die API gesendet → 404. Ursache: `resolve_canonical_model_id()`
verwendete `_safe_name()` als Fallback wenn keine Card existiert. `_safe_name`
ersetzt Punkte durch Underscores — korrekt für Card-Dateinamen, fatal für API-Calls.

### Fixed

- **`utils/model_utils.py`** — `resolve_canonical_model_id()`: Fallback von
  `_safe_name(base)` auf `base` geändert. Modelle mit vorhandener Card nutzen
  weiterhin `card.model_id` (Pfad 3), für die der Underscore-Wert korrekt eingetragen
  ist. Nur für neue/kartenlose Modelle greift der Fallback — und dort ist die
  Original-ID (mit Punkt) korrekt. Lokale Modelle (llamacpp) akzeptieren Punkte
  im `--alias` Flag ohne Einschränkung.

- **`tests/test_resolve_canonical_model_id.py`** — Test-Case `qwen3.5-35b-a3b-q6`
  auf erwartetes Ergebnis `qwen3.5-35b-a3b-q6` (kein Card → base unverändert)
  korrigiert. Das Modell existiert nicht in der aktiven Config; der alte Test
  lief nur durch, weil `_safe_name` zufällig denselben Wert lieferte wie eine
  Card-Lookup hätte. 51/51 Tests grün.

### Betroffene Modelle (Beispiele)

`gpt-5.4-nano`, `gpt-5.4-mini`, `gpt-5.4`, `gpt-5.5`, `gemini-3.5-flash`,
`gemini-3.1-pro-preview` — alle kommerziellen IDs mit Versionspunkten
ohne vorhandene Card.

---

## [v4.8.0] - 2026-06-10

**Per-Modell `server_ready_timeout_sec` — Fix für Split-GGUF-Start-Timeout.**

`qwen3-coder-next-q8` (3-teiliger Split-GGUF) schlug mit
`llama.cpp server did not become ready within 180 s.` fehl, weil der Server noch lud,
als der Benchmark bereits aufgab. Der Provider-Level-Timeout (180s) war zu kurz;
ein Per-Modell-Override war nicht möglich.

### Fixed

- **`utils/providers/llamacpp_base.py`** — `start_server()` liest `server_ready_timeout_sec`
  jetzt zuerst aus dem Modell-Config-Eintrag (`model_cfg.get("server_ready_timeout_sec")`),
  fällt bei Fehlen auf den Provider-Default zurück. Kein Breaking Change für bestehende Modelle.

- **`config/provider_config.yaml`** — `server_ready_timeout_sec: 420` für
  `qwen3-coder-next-q8` (llamacpp_spark) gesetzt. 7 Minuten reichen für das
  3-Part-Split-GGUF auf dem DGX Spark.

### Ursache

Das Modell-Ladesystem in `llamacpp_base.py` kannte bisher nur Provider-weite Timeouts.
Große Modelle (Split-GGUFs, mehrere Dateien) brauchen deutlich länger; der
DGX-Spark-Benchmark-Kommentar ("Timeout von 420s → 180s nach Refactoring") bezog sich
auf Standard-Modelle, nicht auf Split-GGUFs.

---

## [v4.7.9] - 2026-06-10

**Gemma 4 12B Thinking-Hang-Fix (--reasoning off).**

Alle drei `gemma-4-12b-it-ud-q*`-Varianten (Q4/Q6/Q8) hingen beim Reasoning-Benchmark
unbegrenzt, weil Gemma 4 12B IT in llama.cpp standardmäßig Thinking-Modus aktiviert —
dieselbe Ursache wie beim Qwen-Bug in v4.3.5. `thinking_probe_detected=True` war bekannt
(in der Card gesetzt), aber `enable_thinking: false` fehlte in der Provider-Config.

### Fixed

- **`config/provider_config.yaml`** — `enable_thinking: false` für `gemma-4-12b-it-ud-q4_k_xl`,
  `gemma-4-12b-it-ud-q6_k_xl`, `gemma-4-12b-it-ud-q8_k_xl` hinzugefügt. Der llamacpp_base-
  Provider liest diesen Wert beim Server-Start und ergänzt `--reasoning off`, was den
  unbounded Thinking-Chain unterbindet.

### Ursache

`llamacpp_base.py` startet den llama-server ohne `--reasoning`-Flag, wenn `enable_thinking`
nicht explizit in der Model-Config steht. Gemma 4 12B IT (Instruct-Variante mit Thinking-
Support) aktiviert Thinking dann per Default aus dem Chat-Template heraus → unbounded
Generation → kein Token-Output → Heartbeat läuft hoch ohne Fortschritt.

---

## [v4.7.8] - 2026-06-10

**Prober schreibt CoT-Quartett + Web-Export loggt fehlende Cards.**

Zwei offene Findings aus dem Web-Export-Audit v4.7.7 (`outputs/audits/web_export_compatibility_2026-06-10.md`) behoben:

- **WEBEXP-009** — `_write_probe_to_card()` (sowohl in `scripts/core/unified_runner.py` als auch in `scripts/tools/probe_thinking.py`) schrieb bisher nur `thinking_probe_detected/evidence/confidence/at`, nicht aber die v4.7.1-CoT-Quartett-Felder `cot_marker_family` und `cot_tags_detected`. Damit fehlten die Daten im Web-Export, obwohl das Card-Template die Felder bereits deklariert hatte. **0/115 Cards** hatten die Felder gesetzt.
- **WEBEXP-010** — `scripts/web_export.py` lieferte `model_card: null` stillschweigend, wenn ein Leaderboard-Modell keine Card-Datei hatte. Frontend zeigte unvollständige Detailseite ohne Hinweis. Betroffen: `gpt-5_4` (im Leaderboard, aber keine Card-Datei).

### Heuristik + Schreibpfade

- **`utils/model_utils.py`** — Neue Konstante `_COT_FAMILY_MAP` (9 Familien) und neue Funktion `classify_cot_marker_family()`. Reihenfolge signifikant (erster Match gewinnt): `qwen-think`, `openai-oss`, `deepseek-reasoning`, `llama-cot`, `anthropic-extended`, `hermes-scratchpad`, `mistral-reasoning`, `glm-cot`, `generic-cot`. Bei leerem Input: `"none"`.
- **`scripts/core/unified_runner.py` + `scripts/tools/probe_thinking.py`** — `_write_probe_to_card()` setzt `cot_marker_family` und `cot_tags_detected` jetzt nur dann, wenn `tags_found` nicht leer ist (verhindert `null`-Noise im Web-Export). Wenn leer, bleiben die Felder ungesetzt.

### Web-Export-Logik

- **`scripts/web_export.py`** — Vor dem Schreiben der `data.json` wird geprüft, ob `load_model_card()` für das aktuelle Modell `None` liefert. Wenn ja und das Modell in der Leaderboard-CSV auftaucht: WARNING-Log mit `raw_model_id`, Hinweis auf `scripts/maintenance/create_model_card.py`. Frontend bekommt weiterhin `model_card=null` (kein Crash), aber der Lauf hinterlässt Spuren im Log.

### Karten

- **`benchmark_scores/model_cards/gpt-5_4.json`** — Neue Card, vollständig SSoT-konform (card_status `complete`, Vendor `OpenAI`, Display-Name `GPT-5.4`, size_class `Frontier`, modalitäten `text/image`, `supports_tool_use: true`).

### Neue Tests (+23)

- `tests/test_cot_marker_family_probe.py` (21 Tests) — Familien-Mapping (15 parametrisierte Fälle), case-insensitivity, list/tuple/None-Input, `_probe_fields_to_dict` Schreib-/Skip-Verhalten, `_write_probe_to_card` in `unified_runner`.
- `tests/test_web_export_missing_card_log.py` (4 Tests) — WARNING-Log-Format inkl. `raw_model_id`, gpt-5_4-Card-Existenz und Pflichtfeld-Coverage.

### Test-Status

- 1023/1037 Tests grün — 14 pre-existing Failures in `cruciblemark-mcp/tests/test_server.py` (Mock-Fixture, kein Bezug zu WEBEXP-009/010, auch auf `b2e850a` reproduzierbar).
- Re-Export `/tmp/cm_webexport_v478/raw/models`: 92/92 Modelle, gpt-5_4 jetzt enthalten.
- `cot_marker_family`/`cot_tags_detected` im Web-Export weiterhin 0/91 — erwartet, weil der Prober Live-API-Calls (Ollama/Cloud) braucht und in dieser Umgebung nicht läuft. Der Schreibpfad ist verifiziert (Test-Coverage).


## [v4.7.7] - 2026-06-10

**Web-Exporter an die v4.7.0-Model-Cards angepasst — letztes Glied der Pipeline.**

Audit 2026-06-10 (`outputs/audits/web_export_compatibility_2026-06-10.md`) hatte aufgedeckt, dass `scripts/web_export.py` 8 Felder aus den seit v4.7.0 standardisierten Model-Cards NICHT im `model_card` sub-dict der `data.json` durchreichte — darunter die explizit als `consumers: [web_export, ...]` markierten `input_modalities` und `output_modalities`. Das 11ty-Frontend konnte deshalb keine Vision-/Audio-Badges rendern, obwohl 61 Karten Bild/Audio verarbeiten.

### Web-Export-Erweiterungen (`scripts/web_export.py`)
- **Pflicht-Tri-State-Felder ergänzt** im `model_card` sub-dict: `model_id`, `model_version`, `unknown`, `generated_at`, `primary_focus`, `judge_context_hint`, `size_class`.
- **Modalitäten ergänzt** (v4.7.0-Pflicht, `consumers: [web_export, leaderboard]`): `input_modalities`, `output_modalities`.
- **Conditional CoT-Felder** (v4.7.1-Optional, `consumers: [probe, web_export, review]`): `cot_marker_family` und `cot_tags_detected` werden nur exportiert, wenn in der Card gesetzt — Sonde schreibt sie nur bei detektiertem CoT, sonst wäre das Frontend-JSON mit `null`-Noise belastet.
- **Sub-dict thematisch neu geordnet** (Identität → Deployment → Architektur → Modalitäten → Beschreibung → Lizenz → Pricing → Tool-Use) für bessere Lesbarkeit und Frontend-Mapping.

### Neue Tests (+11)
- `tests/test_web_export_card_field_coverage.py` (11 Tests) — Pflichtfeld-Coverage, web_export-consumer-Coverage, Modalitäten-Pass-Through, Tri-State-Text-Felder, None-Card-Handling, Integration-Check gegen `outputs/web_export_check/raw/`.

### Audit-Artefakte
- `outputs/audits/web_export_compatibility_2026-06-10.md` — Vollständiger Audit-Report mit Methodik, Findings-Tabelle, Detailanalyse, Side-Checks, Test-Reproduktion.
- `outputs/audits/web_export_findings_2026-06-10.json` — 10 Findings (2 critical, 3 high, 2 medium, 3 low) als versionierbares JSON.

### Side-Check-Ergebnis
- 91/92 Modelle haben vollständige Cards im Web-Export (1 Modell ohne Card: `gpt-5_4`, siehe Befund WEBEXP-010).
- Modalitäten-Backfill v4.7.6 sauber durchgelaufen (text:52, image+text:47, audio+image+text:14).
- `architecture_tags`-DEPRECATED-Filter, `supports_tool_use`-Tri-State, Emoji-Stripping, Blacklist, Slugify — alles unverändert funktional.


## [v4.7.6] - 2026-06-10

**Vollständiger SSoT-Audit + Beseitigung aller Card-Drift.**

Neues Audit-Skript `scripts/dev/audit_model_cards_full.py` deckt alle 38 Pflichtfelder, Typen, Whitelists und Widerspruchsregeln ab — im Gegensatz zu `validate_model_cards.py`, das nur 7 Pflichtfelder prüft. Damit wurden 529 CRITICAL + 54 WARNING in 113 Cards aufgedeckt und behoben (100 % Reduktion).

### Neue Skripte
- **`scripts/dev/audit_model_cards_full.py`** — Vollständiger SSoT-Audit, prüft ALLE Whitelists aus `card_template_model.yaml`, `card_vocabulary.yaml` und `classification_taxonomy.json`. Akzeptiert `--json --output` für CI-Integration.
- **`scripts/dev/fix_model_cards_whitelist.py`** — 67 triviale Whitelist-Fixes in 54 Karten (card_status `verified`→`complete`, supports_tool_use `"untested"`→`null`, unknown=true→false, weights_provenance_risk Deutsch→Englisch, deployment_type-Tippfehler, size_class `Consumer-GPU`→`Workstation`).
- **`scripts/dev/backfill_modalities.py`** — Heuristische Ableitung von `input_modalities`/`output_modalities` aus `model_id` + `architecture_tags` (z.B. `Vision-Capable` → `["text", "image"]`). 224 Einträge in 112 Karten ergänzt.

### Audit-Verbesserungen
- **`is_todo()`-Helfer** im Audit: TODO-Platzhalter in Whitelist-Feldern (`deployment_type`, `weights_provenance_risk`, `size_class`) werden in draft-Cards toleriert, da der Template-Default `"TODO"` ist.
- **`null`-Toleranz für TODO-Default-Felder** im Typ-Check: null-Werte sind in Feldern erlaubt, deren Template-Default `"TODO"` ist (Skeleton-Karten).
- **Strict-Mode für complete-Cards**: `MISSING_INPUT/OUTPUT_MODALITIES` ist nur in `card_status=complete` CRITICAL, in draft-Cards nur WARNING.

### Bug-Fix
- **`migrate_architecture_tags.py`** — Walrus-Pattern `data := json.loads(...)` las die Originaldatei erneut und überschrieb die in-Memory normalisierten Tags. Erste Migrations-Runde schrieb 32 Karten un-migriert zurück. Fix: `migrate_card()` gibt die normalisierten Daten im Report zurück, `main()` schreibt sie direkt. Verifiziert per Regression-Test.

### Neue Tests (+18)
- `tests/test_audit_model_cards_full.py` (13 Tests) — TODO-Schutz, DEPRECATED/UNKNOWN-Tag-Erkennung, Widerspruchs-Checks, Pflichtfeld-Logik.
- `tests/test_migrate_architecture_tags.py` (5 Tests) — inkl. Regressions-Test für den Walrus-Bug, Idempotenz, dry-run-Verhalten, Modalities-Backfill.

### Ergebnis
- 529 CRITICAL → **0** (−100 %)
- 54 WARNING → **0** (−100 %)
- 113 Cards geprüft, alle SSoT-konform
- 744/744 Tests grün (vorher 726)


## [v4.7.5] - 2026-06-10

**`generate_model_cards.py` an die Validate-Card-Konvention angeglichen.**

Rein strukturelle und stilistische Anpassung. Keine funktionalen Änderungen am `ensure_card()`-Verhalten. Card-Erstellung folgt jetzt denselben Architektur- und Prozessregeln wie Card-Validierung (`validate_cards.py`, Phase 24). 726/726 Tests grün, +25 neue Tests in `tests/test_generate_model_cards.py`. CLI-Flags konsolidiert (`--model-id`, `--card-type`, `--force`, `--interactive`, `--json`); Flags `--update`/`--yes`/`--dry-run` entfernt (duplikativ zu `sync_cards.py` — SRP-Trennung). Neue SSoT-Funktionen `cards_dir()` + `rebuild_card_index()` in `utils/card_template.py`.

### Follow-up (Doku-Konsistenz)
- **`Makefile` — `model-cards-update` repariert** — Delegiert jetzt auf `cards-sync` (statt auf das entfernte `--update`-Flag) und gibt einen Migrations-Hinweis aus. Vermeidet stille CLI-Fehler bei Usern, die den Target noch kennen.
- **`docs/CARD_MANAGEMENT.md` — Tabelle `Make-Targets` und CLI-Referenz präzisiert** — `model-cards-update`-Zeile durch `cards-sync CARD_TYPE=model` ersetzt, `--card-type`-Flag für `generate_model_cards.py` ergänzt, doppeltes `## Card-Lifecycle`-Heading bereinigt, Block-Code-Beispiel für `generate_model_cards.py --card-type model --json` ergänzt.


## [v4.7.4] - 2026-06-10

**Heartbeat-Intervall konfigurierbar — Terminal-Spam-Reduktion.**

Additiver Patch ohne API-Bruch. Das Heartbeat-Intervall des
`UnifiedBenchmarkRunner` (Status-Prints während langer Benchmarks) wird
aus dem Code in die `benchmark_config.yaml` verlagert. Bisher
hardcodiertes 60 s wird Default 120 s — die Print-Frequenz sinkt
deutlich, der Beobachter sieht bei extrem langen Läufen trotzdem noch,
dass der Prozess arbeitet.

### Added
- **`benchmark_config.yaml` — neuer Top-Level-Block `heartbeat:`** mit `enabled` (bool, Default `true`) und `interval_seconds` (float, Default `120`). Komplett optional — fehlt der Block, läuft das System mit `(enabled=True, interval=60.0)` weiter (Backward-Compat).
- **`UnifiedBenchmarkRunner._get_heartbeat_config()`** — liest den Block aus `self.validator.config`, mit Defensiv-Fallback bei fehlendem Block, nicht-dict-Wert, nicht-numerischem Intervall und Intervall `<= 0`. Fehler werden geschluckt (Heartbeat ist nice-to-have, niemals fatal).
- **`_run_asset_loop()` — Heartbeat-Branch** — `threading.Thread` wird nur bei `enabled=True` gestartet. Bei `enabled=False` bleibt das Stop-Event gesetzt, `heartbeat_thread = None` als Sentinel für den `finally`-Block. Verhindert, dass ein Thread für eine disabled-Funktion aufgesetzt wird.
- **`docs/BENCHMARK_SCRIPT_OVERVIEW.md` §6 "Runtime Feedback (Heartbeat)"** — NEU: Config-Beispiel, Robustheits-Hinweise, Disable-Use-Case (CI/kurze Tests).

### Changed
- **`scripts/core/unified_runner.py::_run_asset_loop()`** — `_heartbeat_loop` nutzt `wait(timeout=heartbeat_interval)` statt `wait(timeout=60.0)`. Heartbeat-Branch liest `heartbeat_enabled` / `heartbeat_interval` direkt nach der State-Initialisierung.
- **`benchmark_config.example.yaml`** — Selber `heartbeat:`-Block mit Kommentaren.

### Tests
- **`tests/test_unified_runner_heartbeat.py::TestGetHeartbeatConfig` (NEU, 16 Tests, parametrisiert):**
  - `test_defaults_when_block_missing` — Block fehlt komplett → `(True, 60.0)`
  - `test_explicit_values` / `test_disabled` / `test_interval_only` / `test_enabled_only` — partielle und volle Konfiguration
  - `test_zero_or_negative_interval_falls_back` (parametrisiert: 0, -1, -100, 0.0, -0.5) — Intervall `<= 0` → 60.0
  - `test_non_numeric_interval_falls_back` (parametrisiert: "abc", None, [], {}) — ungültiger Typ → 60.0
  - `test_non_dict_block_falls_back` — Block ist String statt Dict → Defaults
- **`tests/test_unified_runner_heartbeat.py::TestHeartbeatDisabledInRunAssetLoop` (NEU, 1 Test):** `test_disabled_heartbeat_starts_no_thread` — Verifiziert, dass `enabled=False` keinen Thread startet und die Sentinel-Logik im `finally`-Block nicht crasht.
- **Bestehende `TestHeartbeatLifecycle` Tests angepasst** — `_make_runner()`-Helper bekam `validator`-Mock mit leerer Config, damit `validator.config.get(...)` nicht fehlschlägt.
- **Gesamt-Suite:** **603/603 grün** (Heartbeat-Test-Scope, 33/33; 2 pre-existing Failures `test_id_ssot_invariants.py` + `test_provider_health_preflight.py` übersprungen, nicht durch Heartbeat-Änderung verursacht).

### Architektur-Begründung
- **Heartbeat ist Benchmark-Feature, nicht Framework-Internes** — Intervall gehört in `benchmark_config.yaml` neben `logging:`, `rate_limit:` etc., nicht in den Code. Wer ihn komplett ausschalten will (CI-Runs, kurze Tests), setzt `enabled: false`.
- **Default 120 s (statt 60 s)** — User-Praxis-Feedback: 60 s spammt das Terminal bei mehrstündigen Läufen, 120 s gibt Sichtbarkeit ohne Ablenkung. Original-Verhalten bleibt durch Fallback `(True, 60.0)` für Configs ohne Block erreichbar.
- **Robustheit > strikte Validierung** — Heartbeat ist nice-to-have, ungültige Config darf den Benchmark nicht abbrechen. Defensiv-Fallback in `_get_heartbeat_config()` mit `try/except` + `isinstance`-Checks statt `pydantic`-Validation.

### Files
| Datei | Aktion |
|---|---|
| `benchmark_config.yaml` | +`heartbeat:`-Block (top-level) |
| `benchmark_config.example.yaml` | +`heartbeat:`-Block (top-level) |
| `scripts/core/unified_runner.py` | +`_get_heartbeat_config()`, `_run_asset_loop` Heartbeat-Branch, finally-Sentinel |
| `docs/BENCHMARK_SCRIPT_OVERVIEW.md` | +§6 "Runtime Feedback (Heartbeat)" |
| `tests/test_unified_runner_heartbeat.py` | +`TestGetHeartbeatConfig` (16 Tests), +`TestHeartbeatDisabledInRunAssetLoop` (1 Test) |
| `memory-bank/{activeContext,progress,techContext}.md` | v4.7.4-Eintrag |
| `CHANGELOG.md` | v4.7.4-Eintrag |


## [v4.7.3] - 2026-06-10

**Thinking-SSoT-Auflösung + Runner-Consumer-Anbindung.**
>>>>===


Schließt die Discovery-Phase aus v4.7.2 ab: das Card-First-Property der Probe
wird zur **Single Source of Truth** (SSoT), ein optionaler `thinking_override`
in der Provider-Card ist ein expliziter Escape-Hatch, und `base_runner.py`
nutzt die SSoT-Auflösung für das Token-Budget (kein Verlass mehr nur auf
String-Trigger im Modellnamen).

### Added
- **`utils/model_utils.resolve_effective_thinking(model_card, provider_model_cfg, *, model_id, now)`** — zentrale SSoT-Auflösung mit Audit-Trail. Gibt `(effective, source)` zurück:
  1. aktiver `thinking_override` in der Provider-Card → `(value, "override")` + Log `[ThinkingOverride] model_id: override active (value=…, reason=…)`
  2. `thinking_probe_detected` in der Model-Card → `(value, "card_probe")`
  3. sonst → `(None, "none")`
- **`utils/model_utils._is_override_active(override, now=None)`** — Helper für die Override-Validierung: `value` muss bool sein, `reason` Pflicht (Whitespace-only zählt als leer), `active_until` optional (ISO-8601; muss in der Zukunft liegen, naive wird UTC interpretiert).
- **`resolve_token_budget(..., *, provider=None)`** — neuer keyword-only Parameter. Bei `provider="..."` wird die Provider-Card via `load_provider_card()` geladen und an `resolve_effective_thinking()` durchgereicht. **Effekt:** Ein aktiver `thinking_override` in der Provider-Card schaltet den 5×-Reasoning-Multiplikator an/aus. Card-Probe `false` gewinnt über Trigger-Liste. Bei `provider=None` (Default) bleibt das alte Verhalten (Backward-Compat für 5 alte Call-Sites: `mistral.py`, `openrouter.py`, `openai.py`, `llamacpp_base.py`).
- **`docs/THINKING_PROBE.md` (NEU, Methodik-Doku)** — Drei-Signal-Hierarchie, Multi-Prompt-Aggregation, SSoT-Auflösung, Override-Regeln, Runner-Consumer-Anbindung, Discovery-Inventar.

### Changed
- **`utils/base_runner.py:121`** — reicht `provider=provider` an `resolve_token_budget()` durch. Damit wirkt ein `thinking_override` in der Provider-Card auf das Token-Budget. Lokale Importe umgehen potentiellen Circular-Import.
- **`docs/THINKING_TAGS_INVENTORY.md`** — Sektion "SSoT-Auflösung: Card + Override (ab v4.7.1)" verweist jetzt auf die zentrale Methodik in `docs/THINKING_PROBE.md`.
- **`config/card_template_provider.yaml`** — `thinking_override` Optionalfeld (since v4.7.1) ist jetzt mit Verweis auf `resolve_effective_thinking()` dokumentiert.

### Tests
- **`tests/test_thinking_override.py` (NEU, 24 Tests)** — SSoT-Auflösungsmatrix (Override vs. Card-Probe vs. None), Override-Validierung (bool, reason-Pflicht, active_until, naive-UTC, expired, whitespace-reason), Audit-Trail-Verifikation, Backward-Compat.
- **`tests/test_base_runner_thinking_budget.py` (NEU, 17 Tests)** — monkeypatch-basiert mit echten tmp_path-JSON-Files. Coverage: Backward-Compat (`provider=None`), Trigger-Fallback, Override aktiv/expired/ohne-reason, Probe-SSoT (`true`/`false` gewinnt über Trigger), Audit-Log, Card-Cap, kaputte Card-JSON, Edge-Cases (Floor, module-key ohne Reasoning-Slot).
- **Gesamt-Suite:** **634/634 grün** in 2.11s (vorher 617, +17). Alle 17 v4.7.3-Tests + alle 24 v4.7.1-Tests + alle 593 vorherigen Tests.

### Architektur-Begründung
- **Discovery-Fund:** Inline-CoT ist der einzige robuste Trigger über alle Provider (9/9 Discovery-Modelle, 27 Probes, 100 % Erkennungsrate). Tags sind bei `enable_thinking: false` / OpenRouter-Strip unzuverlässig. `reasoning_tokens` nur bei manchen OpenRouter-Modellen.
- **Card-First-Property:** Probe-Ergebnisse sind empirisch robust, Card ist SSoT. Drift wird über `active_until` zeitlich begrenzt.
- **Runner-Consumer:** `base_runner.py` ist der erste Konsument der SSoT-Auflösung. Modul-spezifische Reasoning-Slots (Option C: `reasoning_logic`, `code_quality`, `political_compass`) bleiben als Folge-Aufgabe offen.
- **5× Reasoning-Multiplikator:** greift nur noch bei empirisch validierten Reasoning-Modellen (Card-Probe) oder explizitem Override — String-Trigger im Namen ist Fallback für Karten ohne Probe.

### Files
| Datei | Aktion |
|---|---|
| `utils/model_utils.py` | +`resolve_effective_thinking()`, +`_is_override_active()`, +`provider=` kwarg in `resolve_token_budget()` |
| `utils/base_runner.py` | `provider=provider` durchreichen (Zeile 121) |
| `config/card_template_provider.yaml` | `thinking_override` Doku-Verweis auf SSoT-Schnittstelle |
| `docs/THINKING_PROBE.md` | NEU (Methodik-Doku) |
| `docs/THINKING_TAGS_INVENTORY.md` | Verweis auf zentrale Methodik |
| `tests/test_thinking_override.py` | NEU (24 Tests) |
| `tests/test_base_runner_thinking_budget.py` | NEU (17 Tests) |
| `CHANGELOG.md` | v4.7.3 Eintrag |


## [v4.7.2] - 2026-06-09

**Thinking-Probe v2 — Multi-Prompt + Familien-Inventar.**

### Added
- **`_PROBE_PROMPTS` Dict in `utils/model_utils.py`** — drei Probe-Prompts (`math` / `code` / `decision`) ersetzen den einzelnen Mathe-Prompt. Drei Domänen sind nötig, weil manche Familien CoT nur bei ethischen/Decision-Fragen zeigen, andere nur bei Code-Reasoning, wieder andere nur bei Mathematik.
- **Erweiterte `_THINK_TAGS` Liste (3 -> 13 Tags):**
  - `<think>` / `<thinking>` / `<thought>` (Qwen 3, Magistral, GLM)
  - `<|thinking|>` / `<|reasoning|>` (OpenAI OSS / gpt-oss)
  - `<reasoning>` / `<reason>` (DeepSeek R1 / V3)
  - `<reflection>` (Meta Llama 4)
  - `<analysis>` / `<plan>` (Anthropic Extended Thinking)
  - `<scratchpad>` (NousResearch Hermes)
  - `<solution>` (Mistral Reasoning)
  - `<cot>` (Custom / Future)
- **`_find_think_tags()` Helper** — gibt alle gefundenen Tags zurueck (lowercase match, Multi-Tag-aware).
- **`_probe_single()` und `probe_thinking_model(prompts=...)`** — Multi-Prompt-Pfad mit Aggregation. Hoechste Confidence gewinnt. Bei `prompts=None` (default) werden alle 3 aus `_PROBE_PROMPTS` gesendet. Single-Prompt-Modus (1 Eintrag) bleibt erhalten fuer Card-First-Hook.
- **`ThinkingProbeResult` mit `prompts_used` und `tags_found` Feldern** — Defaults erhalten Backward-Compat.
- **`scripts/tools/discover_thinking_tags.py` (NEU, read-only Discovery-Skript):**
  - Laedt `benchmark_config.yaml` + `config/provider_config.yaml`, gruppiert Modelle nach Familie (18 Familien via `identify_family()`).
  - Waehlt pro Familie 1 Repraesentant aus (Prioritaet: lokal > openrouter > cloud; Thinking-Modelle bevorzugt).
  - Sendet 3 Probe-Prompts pro Modell, aggregiert Ergebnisse.
  - Schreibt `docs/THINKING_TAGS_INVENTORY.md` mit Tabellen, Cross-Family-Statistik, Roh-Antworten (gekuerzt).
  - **Schreibt KEINE Model Cards** — saubere Trennung Discovery <-> Card-Update.
  - CLI: `--families`, `--provider`, `--max-per-family`, `--output`, `--dry-run`, `--fail-fast`.
- **`docs/THINKING_TAGS_INVENTORY.md`** (read-only, auto-generiert) — Inventar pro Familie mit Tags, Confidence, Roh-Antworten.

### Changed
- **`probe_thinking_model()` Signatur** — neuer keyword-only Parameter `prompts: dict[str, str] | str | None = None`. Backward-compat: alte Aufrufer ohne Argument funktionieren weiterhin, erhalten jetzt aber Multi-Prompt (3 Calls) statt Single-Prompt.
- **`scripts/tools/probe_thinking.py` Card-First-Hook** — unveraendert (ruft `probe_thinking_model()` mit defaults auf, kriegt Multi-Prompt-Ergebnis).
- **`scripts/core/unified_runner.py:probe_thinking_model()` Aufruf** — unveraendert.

### Tests
- **`tests/test_thinking_probe_families.py` (NEU, 59 Tests):**
  - 12 Tests fuer `_find_think_tags()` (leer, kurz, alle 13 Tags, case-insensitive, Multi-Tag, keine false positives)
  - 8 Tests fuer `probe_thinking_model()` Multi-Prompt (str-Argument, Single-Dict, Multi-Aggregation, Hoechste-Confidence, All-Fail-Raise, Partial-Failure-Continue, Default-3-Prompts, Backward-Compat-Defaults)
  - 19 Tests fuer `identify_family()` (jede Familie + Spezifitaet: Magistral > Mistral, Qwen-Coder > Qwen)
  - 4 Tests fuer `pick_representatives()` (Lokal-Prioritaet, Thinking-Bonus, max-per-family, Multi-Family)
  - 6 Tests fuer `aggregate_probe()` (Tags=high, reasoning_t=medium, inline_cot=medium, no-signal=low, High-beats-Medium, Errors-excluded)
  - 7 Tests fuer `_THINK_TAGS` Vollstaendigkeit (jede Familie vertreten, lowercase, ...)
  - 3 Tests fuer `_PROBE_PROMPTS` Konfiguration (3 Prompts, non-empty, distinct)
- **Regression-check:** Bestehende 11 `test_thinking_probe_inline_cot.py`-Tests gruen (Backward-Compat der bestehenden API).
- **Gesamt-Suite:** 587/587 Tests gruen (vorher 528, +59).

### Discovery-Methodik
- **Quellen der Tag-Liste:** Recherche zu OpenAI OSS (gpt-oss), DeepSeek R1/V3, Anthropic Extended Thinking, Meta Llama 4, NousResearch Hermes, Mistral Magistral. Bei neu entdeckten Tags: `_THINK_TAGS` ergaenzen + Test in `test_thinking_probe_families.py`.
- **Signal-Hierarchie (unveraendert):** high = explizite Tags; medium = `reasoning_tokens > 0` ODER Inline-CoT im content-Feld; low = kein Signal.
- **Aggregation:** Bei Multi-Prompt gewinnt die hoechste Confidence ueber alle Prompts. Wenn irgendein Prompt `detected=True` liefert, ist das Gesamtergebnis `detected=True` mit kombinierter Evidence.

### Files
| Datei | Aktion |
|---|---|
| `utils/model_utils.py` | +`_PROBE_PROMPTS`, erweiterte `_THINK_TAGS` (3->13), +`_find_think_tags`, +`_probe_single`, +`prompts=` Param in `probe_thinking_model()`, +Felder in `ThinkingProbeResult` |
| `scripts/tools/discover_thinking_tags.py` | NEU (Discovery-Skript, ~370 Zeilen) |
| `tests/test_thinking_probe_families.py` | NEU (59 Tests) |
| `docs/THINKING_TAGS_INVENTORY.md` | NEU (auto-generiert, read-only) |
| `docs/THINKING_PROBE.md` | NEU (Methodik-Doku) |
| `CHANGELOG.md` | v4.7.2 Eintrag |


## [v4.7.1] - 2026-06-09

**Web-Export-Blacklist — Modelle per Config vom Export ausschliessen.**

### Added
- **Neue Config-Datei `config/web_export_blacklist.yaml`** — flache YAML-Liste mit Model-IDs, die `make web-export` ueberspringt. Wildcards via `fnmatch` (z.B. `qwen3.5-35b-a3b-*` sperrt alle Quantisierungen einer Familie). Use-Case: Quant-Vergleichstests und experimentelle Modelle aus dem Web-Frontend raus halten, ohne sie aus dem Leaderboard zu loeschen.
- **`_load_export_blacklist()` und `_is_blacklisted()` in `scripts/web_export.py`** — neue SSoT-Helper. Robuste Defaults: Datei fehlt oder ist leer -> keine Filterung; Parse-Error -> WARNING-Log + leere Filterung (nicht fatal). Eintraege werden automatisch in exakte IDs (O(1)-Set) und `fnmatch`-Patterns getrennt.
- **`meta.json` Block `blacklist`** — dokumentiert `source`, `total_entries` (Anzahl in Config) und `skipped_in_run` (Anzahl waehrend dieses Exports). Add-on Feld, bestehende Tests bleiben gruen.

### Changed
- **`scripts/web_export.py` Hauptloop** — nach PC-Skip, vor `mkdir()`: geblacklistete Modelle werden uebersprungen mit `SKIP (blacklisted: ...)`-Log. Verhindert leere `models/{slug}/`-Verzeichnisse.
- **Match-Schluessel**: `raw_model_id` aus Leaderboard-CSV-Spalte `Model ID` (SSoT, gleiche Spalte wie in `_build_leaderboard_entry` verwendet).

### Tests
- **`tests/test_web_export_blacklist.py` (NEU, 17 Tests):**
  - 5 Tests fuer `_load_export_blacklist()` (missing, empty, malformed YAML, top-level not-dict, key not-list) — alle 4 Fehlerfaelle warnen + returnen leer
  - 2 Tests fuer Split exakt/pattern (Wildcards vs. exakte IDs)
  - 6 Tests fuer `_is_blacklisted()` (exact match, exact no-match, pattern star, pattern `?`, empty sets, exact-priority)
  - 2 Tests fuer `meta.json`-Blacklist-Block (mit Args, mit Defaults)
  - 2 Integration-Tests fuer `main()`-Loop (3 Modelle geprueft, geblacklistetes Modell uebersprungen)
- **Regression-check:** Bestehende 10 `test_web_export_ssot.py`-Tests gruen (kein meta.json-Feld umbenannt/entfernt).
- **Gesamt-Suite:** 471/471 Tests gruen (vorher 444, +27).

### Files
| Datei | Aktion |
|---|---|
| `config/web_export_blacklist.yaml` | NEU (mit Beispiel-Kommentaren) |
| `scripts/web_export.py` | +`_load_export_blacklist`, +`_is_blacklisted`, +Loop-Hook, +`meta.json`-Block |
| `tests/test_web_export_blacklist.py` | NEU (17 Tests) |
| `CHANGELOG.md` | v4.7.1 Eintrag |
| `memory-bank/activeContext.md` | Phase-Eintrag |


## [v4.7.0] - 2026-06-08

**4-Phasen-Refactoring der 5 großen Kern-Skripte (Phase 30).**

### Changed
- **Phase 1 — Ruff Auto-Fix** — 209 Auto-Fixes + manuelle Nacharbeit auf `utils/llm_client.py`, `scripts/core/benchmark_auto.py`, `scripts/core/llamacpp_batch.py`, `scripts/core/unified_runner.py`. Reduktion auf 0 Ruff-Issues.
- **Phase 2 — SSOT-Konsolidierung in `llamacpp_batch.py`** — fünf-ebenen Architektur (Lifecycle-Helper, Context-Manager, Cache-Helper, Asset-Ermittlung, Leaderboard-Cache). `canonical_lookup_keys()` als zentrale SSoT für Modell-Lookup-Keys.
- **Phase 3 — CC-Reduktion** — 11 Helfer-Funktionen extrahiert. Alle Funktionen CC ≤ 12 (Schwelle gemäß `.ruff.toml` C901):
  - `get_startable_assets` → 4 Helfer (`_should_skip_due_to_card`, `_is_batch_module_done`, `_resolve_uncached_assets`, `_is_asset_uncached`)
  - `get_leaderboard_scored_modules` → 3 Helfer (`_extract_model_id_from_row`, `_add_scored_modules_for_model`, `_is_module_scored`)
  - `run_benchmark` → 11 Helfer (CC 35 → ≤ 12)
  - `_process_single_test` → 8 Helfer (CC 32 → ≤ 12)
  - `run_commercial_batch` → 7 Helfer (CC 24 → ≤ 12)
  - `main` → 6 Helfer (CC 18 → ≤ 12)
- **Phase 4 — Magic-Number-Konsolidierung** — 9 SSOT-Konstanten in `utils/constants.py`:
  - `MIN_REFUSAL_CHARS: int = 15`, `HTTP_OK: int = 200`
  - 5× `LLAMACPP_*` (Health-Check, Probe, Reset-Pauses heavy/medium/ok/fallback)
  - `OLLAMA_UNLOAD_SETTLE_SEC: float = 0.5`
  - 12 Magic-Value-Stellen in `unified_runner.py` ersetzt.
  - 3 SIM-Fixes: `SIM110` (`_has_open_tests`), `SIM103` (`_is_module_scored`, `_is_asset_uncached`).

### Fixed
- **Type-Hint-Bug in `_load_commercial_existing_tests`** — Return-Type war fälschlich als `dict[tuple, dict]` typisiert, obwohl die Funktion ein `set[tuple[str, str]]` zurückgibt. Sed-Replacement für 6 weitere Vorkommen von `existing_tests: dict[tuple, dict]` → `set[tuple[str, str]]`.

### Verification
- **481/481 Tests grün** (Refactoring-Scope, ohne die 14 vorbestehenden MCP-Server-HTTP-404-Failures, die mit `git stash` reproduziert wurden)
- **Pylint 10.00/10** für alle 5 Kern-Dateien
- **Mypy 0 Issues in 5 source files**
- **Ruff 0 Issues**


## [v4.6.4] - 2026-06-08

**benchmark_auto: Tristate-Return aus `_run_module_for_model` (skipped ≠ failed).**

### Fixed
- **Auto-Benchmark brach bei llama.cpp-Provider nach 1 Modul ab** — `_run_single_llamacpp_provider_batch()` in `scripts/core/benchmark_auto.py` brach die Modul-Loop ab, sobald `_run_module_for_model()` `False` zurückgab. Der Bool-Return konnte aber nicht zwischen **"Leaderboard-Cache sagt done"** (legitim) und **"echter Fehler"** (Abbruch-berechtigt) unterscheiden. Resultat für `llamacpp_spark`: Server startete (✅ Server bereit 35s), erstes Modul zeigte `Leaderboard-Score vorhanden — übersprungen`, der Loop brach trotzdem ab, alle weiteren Module wurden übersprungen, Server wurde gestoppt (`🛑 Stoppe llama.cpp Server...`). Symptom: `⚠️ Modul 'X' für 'Y' fehlgeschlagen (mit offenen Assets). Restliche Module für dieses Modell werden übersprungen.`

### Changed
- **`_run_module_for_model()` in `scripts/core/benchmark_auto.py`** — Rückgabe von `bool` auf `str` umgestellt: `"ran" | "skipped" | "failed"`. Drei klare Pfade:
  - `"ran"` — Modul wurde ausgeführt und Ergebnisse gespeichert (had_new_results = True)
  - `"skipped"` — Leaderboard-Cache hat Score ODER keine Assets in CSV ODER n/a via Card-Flag → kein Fehler
  - `"failed"` — Subprozess-Fehler, Exception, oder leere Ergebnisse nach echtem Run
- **Caller `_run_single_llamacpp_provider_batch()` (Z. ~446-475)** — Loop bricht jetzt NUR auf `"failed"` UND `assets_todo` (echter Fehler mit offenen Assets). `"skipped"` ist explizit kein Abbruch-Grund.
- **Caller `run_local_batch()` (Z. ~949-958)** — `had_new_results` wird nur bei `"ran"` gesetzt (korrekt mit String-Vergleich statt Bool-OR, weil Tristate kein Bool mehr ist).
- **Defensive Robustheit:** In-Process-Pfad (`runner.run_benchmark`) returnt jetzt `"failed"` wenn der Run keine Ergebnisse produziert (vorher `False`).

### Tests
- **Bestehender Test `test_run_module_for_model_uses_score_delegate`** angepasst: `assertTrue(result)` → `assertEqual(result, "ran")`.
- **8 neue Tests in `TestRunModuleForModelTristate` (Phase 21):**
  1. `test_leaderboard_cache_returns_skipped` — Regression-Test für den User-Bug
  2. `test_no_assets_returns_skipped`
  3. `test_score_delegate_success_returns_ran`
  4. `test_score_delegate_failure_returns_failed`
  5. `test_force_bypasses_leaderboard_cache` — verifiziert, dass `force=True` den Cache umgeht
  6. `test_llamacpp_provider_skips_score_delegate` — in-process statt Subprozess für llama.cpp
  7. `test_generic_delegate_failure_returns_failed`
  8. `test_run_score_delegate_builds_expected_command` (aus altem Test verschoben)

### Result
- 482/482 Tests grün (vorher 474, +8 Phase-21-Tests).
- `make benchmark-auto` mit `llamacpp_spark` durchläuft jetzt alle Module pro Modell, auch wenn einzelne Module per Leaderboard-Cache geskippt werden — der Server bleibt aktiv, das nächste Modul startet ohne Unterbrechung.
- `make benchmark` (Wizard-Pfad) war nicht betroffen — der nutzt den direkten run_benchmark.py-Pfad ohne diesen Loop.

---

## [v4.6.3] - 2026-06-08

**Spark-Connector Auto-Start: `start_server()` als SSoT in `_process_single_test()` (Phase 20).**

### Fixed
- **0-Token-Test-Runs bei llamacpp-Provider (insb. DGX Spark)** — `scripts/core/unified_runner.py::_process_single_test()` hat vor dem Test nur passiv per `requests.get()` geprüft, ob der llama.cpp-Server auf `/health` antwortet. Bei „nicht erreichbar" wurde nur ein WARNING geloggt, der Test startete trotzdem — und lief mit 0 Tokens, weil der Server zwischen Check und `client.query()`-Aufruf keine Zeit zum Starten hatte. Symptom: `❌ [1/5] 001 Wcag Audit: 0.0% | 0 T | 6.1s`, gefolgt von `Retrying request to /models in 0.45s/0.77s` (OpenAI-Library-Retries).

### Changed
- **`scripts/core/unified_runner.py::_process_single_test()` (Zeile ~380-419):** Passiver Health-Check durch `client.start_server(model)` ersetzt. Damit ist `start_server()` aus `LlamaCppBaseClient` die **Single Source of Truth** für den Server-Lifecycle. Behandelt die drei relevanten Fälle:
  1. Server läuft + Modell matched → schneller Return, Test läuft sofort
  2. Server läuft + anderes Modell → stop+start mit korrektem Modell
  3. Server läuft nicht → kompletter Start mit Modell-Laden
- **Fehlerverhalten:** Bei `start_server() == False` oder Exception → `_create_error_result()` mit klarer Fehlermeldung („llama.cpp Server (X) Start fehlgeschlagen für Modell 'Y' — Server-Log prüfen"). Verhindert 0-Token-Runs und gibt dem User frühzeitig ein deutliches Signal, statt 5 Tests mit 0% zu produzieren.
- **Memory-Reset-Block (nach Judge, llama.cpp-spezifisch)** bleibt unverändert — der ist für „Server lebt noch, Modell blockiert nach schwerem Test" zuständig, nicht für Auto-Start.

### Result
- 474/474 Tests grün (kein neuer Test nötig, da Lifecycle-Logik bereits in `test_llamacpp_provider_separation.py` abgedeckt ist).
- Erwartung beim nächsten `make benchmark` mit `llamacpp_spark`: Test-Skip mit Error-Result statt 0-Token-Run, wenn der SSH-Tunnel zum DGX Spark nicht steht.

---

## [Unreleased]

**Per-Modell-Override für `context_length` + `parallel` bei llama.cpp (Hermes-4.3-36B Retries-Fix).**

### Fixed
- **`Retrying request to /chat/completions`-Meldungen** beim Hermes 4.3 36B Q6_K Benchmark auf DGX Spark (8.6.2026, 22:49–23:47). Diagnose: Hybrid-Mode-Reasoning-Modell (ByteDance Seed 36B-Basis) mit SWA/Hybrid-Attention führt bei 4 parallelen Slots + 8 GB Prompt-Cache nach Heavy-Tasks (>200s) zu sporadischen Connection-Resets. llama.cpp hat `n_ctx` automatisch von 65536 auf 16384 runterreguliert; 5.83–5.92 t/s Decoding-Speed (vs. 43–44 t/s für Gemma 4 26B-A4B auf demselben Server) belegt den Recurrent-Layer-Overhead.
- **Lösung (Per-Modell-Override statt globaler Provider-Reduktion):**
  - `utils/providers/llamacpp_base.py:_build_server_cmd()` liest `parallel` jetzt zuerst aus `model_cfg` (`model_cfg.get("parallel", prov_cfg.get("parallel", 4))`) — historisch hartcodiert Provider-Level. `swap_model()` startet llama-server pro Modellwechsel frisch, daher ist der Per-Modell-Wert beim Server-Start wirksam.
  - `config/provider_config.yaml` `providers.local.llamacpp_spark.models.hermes-4.3-36b-q6` bekommt: `context_length: 16384` (Override, llama.cpp hatte sowieso auf 16K runterreguliert) + `parallel: 1` (Override).
  - Andere Spark-Modelle (Qwen 3.5/3.6, Gemma 4) bleiben unangetastet auf 4 parallel.

### Added
- **2 neue Regressionstests** in `tests/test_llamacpp_provider_separation.py`:
  - `test_per_model_context_length_and_parallel_override` — Per-Modell-Override greift, andere Modelle im selben Provider bleiben unangetastet (Hermes: 16384/1, Default: 65536/4)
  - `test_per_model_context_length_falls_back_to_provider_default` — Fallback-Kette Model → Provider bleibt intakt

### Doku
- `memory-bank/techContext.md` Sektion „Per-Modell-Override für `context_length` und `parallel` (Hermes-Fix)" — Diagnose, Root Cause, Lösung, Verifikation, offene Punkte (8 GB Prompt-Cache bleibt aktiv).

### Result
- 483/483 Tests grün (vorher 481, +2 neue). Pylint 10.00/10, Mypy 0 issues, Ruff clean.
- Manuelle Verifikation: `_build_server_cmd("hermes-4.3-36b-q6")` liefert `--ctx-size 16384 --parallel 1`; `_build_server_cmd("qwen3.6-35b-a3b-q8")` liefert weiterhin `--ctx-size 65536 --parallel 4` (unverändert).
- Nächster Schritt: `make benchmark-auto` mit Hermes 4.3 36B zur Verifikation, dass die Retries tatsächlich verschwinden.


**llama.cpp Sampling-Defaults: `benchmark_defaults` → `llama_cpp_defaults` (SSoT-Klarstellung) + vollständige Flag-Pipeline.**

### Changed
- **Config-Block umbenannt:** `providers.local.config.benchmark_defaults` → `providers.local.config.llama_cpp_defaults`. Werte entsprechen jetzt den **llama.cpp-Upstream-Defaults** (außer `seed=42`):
  - `temperature: 0.1` → `0.8` (llama.cpp-Default)
  - `top_p: 0.9` → `0.95` (llama.cpp-Default)
  - `top_k: 40` (unverändert)
  - `repeat_penalty: 1.1` → `1.0` (llama.cpp-Default)
  - `seed: 42` (explizit für Reproduzierbarkeit; llama.cpp-Default wäre -1 = random)
- **Zwei neue Flags ergänzt:** `min_p: 0.0` und `presence_penalty: 0.0` werden jetzt als Server-Start-Flags (`--min-p`, `--presence-penalty`) an llama-server durchgereicht. Vorher waren sie nur via Pro-Modell-Override in `optional_numeric_flags` setzbar, nicht als Default.
- **Code-Defaults angepasst:** Die hardcoded Fallback-Werte in `_build_server_cmd()` (`utils/providers/llamacpp_base.py`) wurden auf 0.8/0.95/40/0.0/0.0/1.0/42 vereinheitlicht. Damit bleibt die Funktion backward-kompatibel, wenn der `llama_cpp_defaults`-Block fehlt.

### Added
- **Pro-Modell-Override für `min_p` und `presence_penalty`** in `optional_numeric_flags` — vorher waren nur `temperature`/`top_p`/`top_k`/`repeat_penalty` überschreibbar. Jetzt sind alle sieben Sampling-Parameter pro Modell steuerbar.
- **3 neue Regressionstests** in `tests/test_llamacpp_provider_separation.py`:
  - `test_build_server_cmd_uses_llama_cpp_defaults` — verifiziert alle sieben Flags im Server-Cmd
  - `test_build_server_cmd_model_override_wins` — Modell-Override schlägt Default
  - `test_build_server_cmd_works_without_defaults_block` — Code-Defaults greifen ohne Config-Block

### Migration
- Wer eigene Repo-Konfigs mit dem alten `benchmark_defaults`-Block hat, muss auf `llama_cpp_defaults` umbenennen. Sonst schlägt der Server-Start fehl (KeyError auf `benchmark_defaults` ist nicht das Problem — `local_config.get("llama_cpp_defaults", {})` liefert leeren Dict, dann greifen Code-Defaults).

### Doku
- `docs/DEVELOPER_GUIDE.md` Abschnitt „Sampling-Defaults via `llama_cpp_defaults` (SSoT)" neu — Tabelle aller Flags, Pro-Modell-Override-Beispiel, Override-Reihenfolge, Hinweis zum historischen Rename.


## [v4.6.2] - 2026-06-08

**llama.cpp-Connector-Trennung — eine Klasse pro Hardware-Target (M4 ↔ Spark).**

### Changed
- **Architektur-Korrektur:** Die Multi-Provider-Klasse `LlamaCppClient` mit `_provider_name`-Runtime-Switch ist aufgeteilt in eine Basisklasse + zwei Hardware-spezifische Subklassen. Damit folgt die llama.cpp-Integration dem Muster aller anderen Provider (OllamaClient, OpenRouterClient, …): **1 Klasse pro Hardware-Target, 1 Instanz pro Provider-Key, kein State-Sharing, keine Bug-Klasse mehr durch vergessene `_set_provider_context()`-Aufrufe.**
- `utils/providers/llamacpp.py` (NEU als `LlamaCppLocalClient`): nur noch M4-MacBook. Erbt von `LlamaCppBaseClient`, `PROVIDER_NAMES = ["llamacpp"]`, `_PROVIDER_KEY = "llamacpp"`.
- `utils/providers/llamacpp_spark.py` (NEU als `LlamaCppSparkClient`): nur noch DGX Spark (Remote via SSH, NVIDIA CUDA). Erbt von `LlamaCppBaseClient`, `PROVIDER_NAMES = ["llamacpp_spark"]`, `_PROVIDER_KEY = "llamacpp_spark"`.
- `utils/providers/llamacpp_base.py` (NEU als `LlamaCppBaseClient`): provider-agnostische Logik (Server-Lifecycle, OpenAI-Client, Health-Check, Query-Loop, Model-Norm). `PROVIDER_NAMES = []` (kein Auto-Register) und `_PROVIDER_KEY = ""` (muss von Subklasse gesetzt werden). Direkte Instanziierung wirft `NotImplementedError`.
- `utils/llm_client.py::_LOCAL_PROVIDERS`: Aliase `llama_cpp` und `llamacpp_local` entfernt — jede Provider-Instanz hat jetzt ihren eigenen eindeutigen Schlüssel.
- `scripts/core/llamacpp_batch.py::is_llamacpp_provider()`: Aliase entfernt (`{"llamacpp", "llamacpp_spark"}`).
- `scripts/core/model_discovery.py::discover_local_models()`: iteriert jetzt über ALLE aktivierten llamacpp-Provider (M4 + Spark), nicht nur den hartcodierten Key `llamacpp`. Damit erscheinen Spark-Modelle in `--all`/Discovery-Listen.

### Removed
- `_set_provider_context()`, `_normalize_provider_name()`, `_provider_name`-Attribut aus der llama.cpp-Provider-Logik. Jede Instanz kennt ihren Provider ab Konstruktion.
- Aliase `llama_cpp` und `llamacpp_local` aus dem Auto-Registry und aus `_LOCAL_PROVIDERS`.

### Added
- **`tests/test_llamacpp_provider_separation.py`** (10 Tests): Auto-Registry-Korrektheit (Basisklasse ohne `PROVIDER_NAMES`, Subklassen mit eindeutigen Keys, Aliase entfernt), Provider-spezifischer Config-Lookup (M4 vs. Spark lesen jeweils ihre eigene Config), State-Isolation (kein Leak zwischen Instanzen), Konstruktor-Validierung (Basisklasse wirft ohne `_PROVIDER_KEY`), `_LOCAL_PROVIDERS` Tuple bereinigt, `model_discovery` enthält Spark-Modelle.

### Result
- 469/469 Tests grün (vorher 459, +10 durch Phase-19-Tests).
- Architektur-Konsistenz: llama.cpp folgt jetzt dem Muster aller anderen Provider (1 Klasse pro Hardware-Target).
- Bug-Klasse `_set_provider_context()`-Switch strukturell eliminiert — der ursprüngliche Spark-Connector-Bug (falsche Config, falsche base_url, falsche context_window) kann in dieser Form nicht mehr auftreten.

### Migration für eigene Skripte
Wer die Aliase `llama_cpp` oder `llamacpp_local` in eigenen Skripts referenziert hat, muss auf `llamacpp` umstellen. Im Repo selbst waren nur `scripts/core/unified_runner.py` und `scripts/core/llamacpp_batch.py` betroffen — beide sind in dieser Phase angepasst.

---

## [v4.6.1] - 2026-06-08

**CSV-Hygiene Defense-in-Depth — Hard-Fail-Guard in `result_manager` + Sanitizer-Heuristiken in `consolidate_csv`.**

### Added
- **`utils/result_manager.py::_validate_row_for_write()`** — Hard-Fail-Guard, der JEDE Zeile (sowohl `new_results` als auch `existing_rows`) vor dem CSV-Write gegen die Sanitizer-Heuristiken prüft. Wirft `ValueError` bei Header-Repeat, narrativer Asset-ID oder ungültigem Modell. Korrupte Zeilen werden geloggt + ÜBERSPRUNGEN (resilient — Save bricht nicht ab).
- **`utils/result_manager.py::_write_to_csv()` (refactored)** — nutzt den Hard-Fail-Guard; zeigt `🛡️ Hard-Fail-Guard: N korrupte Zeile(n) übersprungen` bei Funden.
- **`scripts/maintenance/consolidate_csv.py::_filter_corrupt_rows()`** — wendet die identischen Sanitizer-Heuristiken (`_is_narrative_asset_id`, `_is_invalid_model`, Header-Repeat) auf den DataFrame VOR `to_csv()` an. Verhindert dass die Maintenance-Konsolidierung Müll zurück in die CSV schreibt.
- **`scripts/maintenance/consolidate_csv.py::consolidate_file()` (erweitert)** — Logging mit Korrupt-Drop-Counter (`🗑️ Korrupt-Drop: header_repeat / narrative_asset_id / invalid_model`).
- **`Makefile::validate-csv`** — neues Target für Dry-Run-Validierung (CI-/Smoke-tauglich).
- **`tests/test_consolidate_csv_validates.py`** (9 Tests) — vollständige Defense-in-Depth-Pyramide für `consolidate_csv`: Filter-Unit-Tests (Header-Repeat, narrative Asset-ID, Boolean-Model), leere DataFrames, fehlende Spalten, E2E mit tmp-CSV, fehlende Datei, gemischte Korruptions-Muster.
- **`tests/test_result_manager_validates.py`** (7 Tests) — Hard-Fail-Guard-Validierung: akzeptiert saubere Zeilen, lehnt narrative/Header-Repeat/Boolean/leere Modelle ab, E2E mit Save-Operation, Resilienz bei gemischter Korruption.

### Data
- **Live-Verifikation auf den 3 Benchmark-CSVs nach Phase 8:** Sanitizer meldet 0 Drops (`local_models_benchmark.csv` 1013, `cloud_models_benchmark.csv` 1282, `commercial_models_benchmark.csv` 1940 — alle sauber). Phase-8-Erfolg hält.

### Result
- 226/226 Tests grün (vorher 210, +16 durch Phase-9-Tests).
- Pylint 10.00/10 für `result_manager.py`, `consolidate_csv.py`, `sanitize_benchmark_csvs.py`, `test_consolidate_csv_validates.py`, `test_result_manager_validates.py`.

### Architecture (Defense-in-Depth-Schichten)
1. **Schicht 1 — Sanitizer (`sanitize_benchmark_csvs.py`):** räumt historische Altlasten auf, Dry-Run + Apply.
2. **Schicht 2 — Consolidate (`consolidate_csv.py`):** filtert via `_filter_corrupt_rows()` VOR jedem `to_csv()`.
3. **Schicht 3 — Result Manager (`result_manager.py`):** Hard-Fail-Guard validiert jede Zeile VOR dem CSV-Write.

Drei unabhängige Schichten garantieren: **Phase-8-Erfolg kann nicht durch zukünftige Module oder manuelle Edits zunichtegemacht werden.**

## [v4.6.0] - 2026-06-08

**CSV-Hygiene-Sanitizer — Bereinigung korrupter Benchmark-CSVs.**

### Added
- **`scripts/maintenance/sanitize_benchmark_csvs.py`** — Vier-Klassen-Filter für korrupte Datenzeilen: Header-Repeat, Rohtext-Asset-IDs (Länge > 60, Romananfänge, Markdown-Marker), Boolean-Modelle, leere Modelle. Dry-Run + `--apply`-Modus. Idempotente `.bak`-Backups, atomare `.tmp`+`replace()`-Schreibvorgänge. SSoT-CSV-Pfade aus `scripts.leaderboard.config`. Exit-Code 0 in beiden Modi.
- **`tests/test_sanitize_benchmark_csvs.py`** (65 Tests) — Filter-Unit-Tests (parametrisiert für 14 Romananfänge, 5 Markdown-Marker, 5 pandas-Sentinel-Varianten), Pipeline-Tests, Backup-Idempotenz, Atomic-Write, E2E mit `monkeypatch` auf SSoT-Pfade.

### Data
- **13466 Müll-Zeilen aus `local_models_benchmark.csv` entfernt** (93 % der CSV). Vorher 17705 Zeilen mit 13265 leeren `model`-Feldern; nachher 1013 saubere Zeilen. `commercial_models_benchmark.csv` 11 Zeilen verworfen (0.6 %). `cloud_models_benchmark.csv` bereits sauber. Backups unter `*.bak` (idempotent).
- **Leaderboard regeneriert** — 84 Zeilen, 78 vollständig (43/43 Tests), 5 unvollständig (40–42/43, echte Asset-Lücken die das Auto-Benchmark füllen muss: Kimi K2.6, DeepSeek V4 Pro, Qwen 3.5 397B A17B, MiniMax M2.7, GLM-4.7), 1 Modell mit 49/43 (Test-Override-Logik / Tool-Use-Backlog).

### Result
- 210/210 Tests grün (vorher 145, +65 Sanitizer-Tests).
- Pylint 10.00/10 für `sanitize_benchmark_csvs.py` und `test_sanitize_benchmark_csvs.py`.

---

## [v4.5.0] - 2026-06-08

**ID-SSoT-Refactoring — Card-First-Vertrag & Workaround-Entfernung.**

### Added
- **`strip_date_suffix()`** in `utils/model_utils.py` — SSoT für Datums-Suffix-Strip (`-YYYYMMDD` / `-MMDD` mit gültigem Monat); idempotent.
- **`enforce_card_first()`** in `utils/model_utils.py` — Card-First-Vertrag: garantiert Card-Existenz via `ensure_card()` (Draft falls fehlt, kein Hard-Fail, WARNING wird geloggt). Rückgabe `(canonical_id, has_card)`.
- **`tests/test_enforce_card_first.py`** (5 Tests) — Card-First-Vertrag-Invariante: existing-card, missing-card-creates-draft, idempotent, empty-input, hf.co-prefix-pipeline.
- **`tests/test_id_ssot_invariants.py`** (4 Tests) — Brücken-Äquivalenz zwischen `enforce_card_first` und `resolve_canonical_model_id`; Slugify-Konsistenz für `:/ .` + Leerzeichen; Idempotenz (10 Wiederholungen); AST-Sweep gegen Inline-`re.sub` mit Slugify-Pattern außerhalb der SSoT-Module.

### Changed
- **`utils/model_utils.py`** — `resolve_canonical_model_id()` ist jetzt die zentrale ID-Bridge (Card-Lookup + Suffix-Strip + `_safe_name`-Fallback). Alle 12 Inline-ID-Transformationen (in `utils/benchmark_utils.py`, `utils/scoring_utils.py`, `utils/providers/llamacpp.py`, `scripts/maintenance/*`, `scripts/core/*`, `scripts/analysis/*`, `scripts/core/tooluse_exporter.py`) auf SSoT migriert.
- **`utils/result_manager.py`** — `save_results()` ruft `enforce_card_first()` statt `resolve_canonical_model_id()`. CSV-Senke ist die zentrale Card-First-Durchsetzungsstelle; jede geschriebene `model_id` ist garantiert durch eine Card im Filesystem abgedeckt.
- **`scripts/analysis/generate_provider_cards.py`** + **`scripts/analysis/review/risk_calculator.py`** — lokale `safe_id()`-Duplikate entfernt; Import von `utils.provider_card_template._safe_id`. Provider-Card-SSoT ist nun ebenfalls konsolidiert.
- **`scripts/leaderboard/module_integration.py::_resolve_to_canonical_id()`** — delegiert primär an `utils.model_utils.resolve_canonical_model_id()`; lokaler 5-Level-Card-Lookup bleibt als Bulk-Fallback.
- **Dokumentation** — `docs/ARCHITECTURE.md`, `docs/DEVELOPER_GUIDE.md`, `memory-bank/systemPatterns.md` und `memory-bank/activeContext.md` auf den ID-SSoT-Stand aktualisiert. Veraltete `_resolve_dir()`-4-Stufen- und `migrate_canonical_model_ids.py`-Erwähnungen entfernt bzw. präzisiert (4-Stufen-Fallback ist legitime Robustheit, kein Workaround).

### Removed
- **`scripts/maintenance/migrate_canonical_model_ids.py`** — Workaround entfernt; SSoT-Funktionen reichen für die Kanonisierung.
- **22 `*.bak`-Dateien** in `benchmark_scores/model_cards/` — gelöscht (Legacy-Backups vor ID-SSoT-Refactoring, kein aktiver Bestand).

### Brücken-Klassifikation
- **Card-/Path-Use-Case** (z. B. CSV-Schreiben, Tool-Use-Aggregation, Card-Generierung) → `resolve_canonical_model_id()` / `enforce_card_first()`.
- **Leaderboard-/Display-Use-Case** (menschenlesbare Vendor-Schreibweise, z. B. `qwen/qwen3-32b`) → `normalize_model_id()` + optional `strip_date_suffix()`.

### Result
- 145/145 Tests grün (vor Refactoring: 124, +21 durch neue Invarianten-Tests).
- Klare SSOT-Trennung: keine DRY-Verletzungen mehr im ID-Layer; Inline-`re.sub` mit Slugify-Pattern nur noch in den SSoT-Modulen.

---

## [v4.3.9] - 2026-06-07

**Benchmark-Hang-Diagnose — Connection-Leak-Fix & Stabilisierung für Remote-llama.cpp-Provider.**

### Fixed
- **Connection-Leak in `utils/providers/llamacpp.py`** — Der httpx-Client hielt Verbindungen im Keep-Alive-Zustand, der Server (besonders Remote via SSH) schloss sie nach langen Requests, aber der Client merkte es nicht → CLOSE_WAIT-Sockets. Fix: `httpx.Limits(max_keepalive_connections=0)` — Keep-Alive deaktiviert, jeder Request bekommt eine frische Verbindung. Zusätzlich: `self._client = None` nach jedem `query()` um sicherzustellen, dass beim nächsten Aufruf ein neuer Client erstellt wird.
- **NameError in `scripts/core/unified_runner.py`** — Fehlendes `import os` verursachte `name 'os' is not defined` in `_cleanup_local_provider()`. Behoben: `import os` am Dateianfang hinzugefügt.
- **Stale-Ready in `utils/providers/llamacpp.py`** — `_is_healthy()` allein reichte nicht, wenn der Server auf /health antwortete, aber das Modell nach Memory Reset noch nicht bereit war. Fix: `_is_model_ready()` zusätzlich zu `_is_healthy()` in `query()`.

### Changed
- **`scripts/run_score_benchmark.py`** — 3s Pause zwischen Modulen hinzugefügt (Server-Stabilisierung nach Modul-Wechsel).

### Result
- Gemma 4 26B-A4B Q8 via llamacpp_spark: Alle 6 CLI-Tests erfolgreich durchgelaufen (Durchschnitt: 93.7%).
- Kein Hang, keine Race-Conditions zwischen Tests.

---

## [v4.3.1] - 2026-06-05

**Code Quality Pass — Bugfixes, DRY-Konsolidierung & Import-Cleanup.**

### Fixed
- **F841 Bug in `_ensure_model_card()`** — `existing_card` wurde befüllt aber nie genutzt; `card_content` wurde stattdessen durch einen zweiten `json.loads()`-Aufruf neu geladen. Behoben: Variable entfernt, `card_content` direkt aus `loaded` befüllt.
- **R1716 in `unified_runner.py`** — Chained comparison `response_len > 0 and response_len < threshold` → `0 < response_len < threshold`.
- **`_language_validator` auf Modul-Ebene** — War als Inline-Instanz in `_process_single_test()` nicht sichtbar für Tests → `NameError` in 3 Tests. Behoben: `_language_validator = LanguageValidator()` auf Modul-Ebene.
- **ANSI-Escape-Codes in `political_compass/test.py`** — Escape-Codes ohne `isatty()`-Guard erschienen als rohe Zeichenfolgen wenn Benchmark als Subprozess läuft (kein TTY). Behoben: `sys.stdout.isatty()`-Check.

### Changed
- **`unified_runner.py` — Import-Cleanup:** Alle Inline-Imports (`csv`, `hashlib`, `time`, `datetime`, `append_global_run_metrics`) an Dateianfang verschoben. `_BUDGET_KEYWORDS` als Modul-Level-Konstante (kein Rebuild pro Exception-Handler-Aufruf).
- **`benchmark_auto.py` — Magic Number:** `time.sleep(3)` → `_LLAMACPP_STOP_SETTLE_SEC = 3` Konstante.
- **`run_tooluse_benchmark.py` — Import-Position:** `import argparse` aus `main()` an Dateianfang verschoben.
- **`llamacpp.py` — `subprocess.Popen`:** Erklärender Kommentar ergänzt warum kein Context Manager verwendet wird (Hintergrundprozess, der nach dem Aufruf weiterläuft).

### Added
- **`scripts/core/model_discovery.py`** (NEU) — DRY-Konsolidierung: `discover_local_models()`, `discover_commercial_models()`, `discover_models()` — war identisch in `run_score_benchmark.py` und `run_political_compass_benchmark.py` dupliziert. Beide Worker importieren jetzt aus dem SSOT.

### Result
- Pylint 10.00/10 (+0.01 gegenüber v4.3.0), Ruff clean, 227/227 Tests grün.

---

## [v4.3.0] - 2026-06-04

**Per-Model Review-Batch + PC-Leaderboard-Repair + Tool-Use Pre-Flight-Validierung + llama.cpp Spark Connector-Konsolidierung.**

### Added
- **Konsolidierter `llamacpp_spark`-Connector** — lokale OpenAI-kompatible Intranet-Ausführung mit robuster Endpoint-Adoption, tolerantem Readiness-Probing (`content`/`reasoning_content`/`finish_reason`/`usage.total_tokens`) und konfliktfreiem Fremd-Endpoint-Verhalten.
- **UnifiedRunner-Lifecycle-Cleanup (`finally`)** — `scripts/core/unified_runner.py` führt für lokale Provider (inkl. `llamacpp_spark`) jetzt garantiert End-of-Run-Cleanup aus (`server_stop_cmd` + optional `server_post_stop_cmd`) — auch bei `KeyboardInterrupt`/Abbruch.

### Changed
- **Readiness-Logik in `utils/providers/llamacpp.py` gehärtet** — bei bereits laufendem identischem Modell wird ein konfigurierbares Warmup-Fenster genutzt, statt den Lauf vorschnell mit "noch nicht stabil" zu beenden.
- **Dokumentation aktualisiert** — `README.md`, `PROJECT_STATUS.md`, `docs/SETUP_GUIDE.md`, `docs/ARCHITECTURE.md`, `docs/DEVELOPER_GUIDE.md`, `REF_TODO.md` und `memory-bank/` auf den Connector-Stand v4.3.0 gebracht.


### Fixed
- **Voreiliger Cache-Hit in `execute_batch_module`** — `BaseBenchmarkRunner.execute_batch_module()` (`utils/base_runner.py:364-369`) returnte früh, wenn `(model, "political_compass")` in den 3-CSV-Caches vorhanden war. Das umging `PoliticalCompassHandler.handle_results()` und damit `save_leaderboard_csv()` → 3 Modelle hatten PC-Daten in `pc_results.csv` aber keinen Eintrag im `pc_leaderboard.csv` → "Pending" im Hauptboard. Fix: PC-Module werden explizit vom 3-CSV-Fast-Path ausgenommen; `pc_leaderboard.csv` ist jetzt die alleinige SSoT für Batch-Skip-Entscheidungen. Statischer Regression-Test in `tests/test_repair_pc_leaderboard.py::test_execute_batch_module_fix_in_source`.
- **Provider-Index-Methoden-Asymmetrie** — `generate_review.py` rief modul-lokales `_rebuild_index()` auf `pc_gen` auf, was bei Provider-Cards nicht existiert. Fix: konsistenter Aufruf `pc_gen.rebuild_provider_index()` (aus `utils.provider_card_template`).

### Added
- **`scripts/maintenance/repair_pc_leaderboard.py`** — Idempotente Daten-Reparatur für `political_compass_leaderboard.csv`. Liest AVG-Zeilen aus `pc_results.csv`, rekonstruiert vanilla/forced Hauptkoordinaten aus `module_stats.{vanilla,forced}` (Mittel über 9 PC-Blöcke 7.1–7.9), normalisiert HF-Präfixe via `normalize_model_id`, klassifiziert Archetyp + Axis-Labels, schreibt per Upsert. `--dry-run` für Probe-Lauf. 7 Unit-Tests grün.
- **3 fehlende PC-Leaderboard-Einträge ergänzt** — DeepSeek V3.1-671B (Soziale-Mitte/Konservative-Mitte, Shift 0.49), DeepSeek V3-2 (Sozial/Konservative-Mitte, Shift 0.27), Hermes 4 14B Q4_K_M (Sozial/Konservative-Mitte, Shift 0.56). Backup der Original-Datei unter `political_compass_leaderboard.csv.bak_20260603_075304`.

### Added
- **`make benchmark-auto` Tool-Use Backlog Auto-Fill** — Metaskript-Funktion erkennt Model Cards mit `supports_tool_use="untested"` und delegiert an `scripts/run_tooluse_benchmark.py --models <comma-list>`. Ein einziger Subprozess statt pro Modell (spart MCP-Restart-Overhead). Läuft als Pre-Step `[0/2]` vor den regulären Ollama/llama.cpp/Commercial-Batches. Lücken wie `qwen2_5vl_7b` werden beim nächsten `make benchmark-auto`-Lauf automatisch geschlossen. `FORCE=1` wirkt durch, betrifft aber nur `untested` (nie `true`-Cards neu testen — wer FORCE will, nutzt `make benchmark-tooluse-force`). Bei Fehlschlag wird der Hauptlauf nicht abgebrochen. Neue Helper `_collect_untested_tooluse_cards()` und `_run_untested_tooluse_models()` in `scripts/core/benchmark_auto.py`. 14 neue Tests in `tests/test_benchmark_auto_untested_tooluse.py`.

### Removed
- **`qwen2.5vl:7b` komplett aus Konfiguration und Datenbank entfernt** — VL-Modell (Vision-Language), das im Text-Benchmark deutlich schwächer abschneidet als reine Text-Modelle. War ein temporärer Test-Eintrag. Entfernt aus: Model Card (`benchmark_scores/model_cards/qwen2_5vl_7b.json`), Card-Index (`_index.json`, 87 → 86), 6 CSVs (`local_models_benchmark.csv` 51 Zeilen, `benchmark_leaderboard.csv` 1 Zeile, `benchmark_leaderboard_detailed.csv` 1 Zeile, `political_compass_leaderboard.csv` 1 Zeile, `political_compass_results.csv` 3 Zeilen, `tooluse_leaderboard.csv` 1 Zeile), Audit-Logs-Verzeichnis (`outputs/audit_logs/qwen2.5vl_7b/`, 50 MD-Dateien), Reviews (`docs/reviews/qwen2.5vl_7b/`, 2 MD-Dateien). Backup unter `backups/qwen2_5vl_7b_removal_20260603_1203*`. Leaderboards regeneriert via `make leaderboard` + `make tooluse-leaderboard`. Tool-Use-Auto-Fill-Backlog schrumpft von 2 auf 1 (`test`-Placeholder bleibt).

### Added
- **Tool-Use Pre-Flight Card-Validierung** — Neue Utility `utils/provider_health.py` mit `get_installed_ollama_models()`, `is_ollama_model_installed()`, `is_api_provider_available()`, `validate_untested_card()` und `filter_testable_cards()`. Vor dem Subprocess-Delegation prüft `scripts/core/benchmark_auto.py::_run_untested_tooluse_models()` nun pro Card: ist das Ollama-Modell installiert (`ollama list`-Cache, prozess-lokal, einmal pro Lauf), ist der API-Provider-Key gesetzt (mistral/anthropic/openai/google/xai/groq/openrouter), existiert ein llama.cpp-Binary-Pfad? Unerreichbare Cards werden nach `outputs/tooluse_unreachable_YYYYMMDD_HHMMSS.json` geloggt (Diagnose), nur testbare Cards gehen an `scripts/run_tooluse_benchmark.py --models <comma-list>`. Verhindert, dass Pre-Step bei nicht-installierten Modellen (z.B. `qwen2.5vl:7b` nach Entfernung, oder fehlkonfigurierte API-Keys) in Endlos-Loops hängt oder crasht. 29 neue Tests in `tests/test_provider_health_preflight.py` (alle Bereiche: Cache, Force-Refresh, Timeout, Prefix-Strip, API-Key-Mapping, Card-Validierung, Filter-Logik, E2E mit Unreachables-Report). 4 Tests in `tests/test_benchmark_auto_untested_tooluse.py` an neue Pre-Flight-Signatur angepasst (deterministisches Mocking von `filter_testable_cards`). Pylint 10.00/10 für `utils/provider_health.py` und `scripts/core/benchmark_auto.py`.

### Fixed
- **`make benchmark-auto` Python 3.14 Import-Fehler** — `ModuleNotFoundError: No module named 'utils'` beim Aufruf via `python scripts/core/benchmark_auto.py`. Ursache: `sys.path.insert()` war NACH den `from utils...` Imports positioniert (Zeile 47 nach Zeile 26). Python 3.14+ hat strengere `sys.path[0]`-Semantik für `python script.py` (Skript-Modus) — `Path(".")` als `sys.path[0]` reicht nicht für relative Package-Imports. Fix: `sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))` VOR die Drittanbieter-Imports verschoben. `resolve()` liefert den absoluten Pfad, der in Python 3.14 für Package-Imports funktioniert. Pre-Step `[0/2]` Tool-Use-Backlog-Auto-Fill konnte durch diesen Fix erstmals live feuern (Lauf am 2026-06-03 11:56 UTC, 83KB Log-Output).
- **Pylint `wrong-import-position` nach Refactoring** — Reaktivierung des `pylint: disable=wrong-import-position`-Markers für die Third-Party-Imports, der beim Refactoring versehentlich entfernt wurde. Pylint 9.94 → 10.00/10.

### Changed
- **`.gitignore`** — Neue Patterns für Backup-/Draft-Artefakte: `*.bak`, `*.bak_*`, `benchmark_scores/**/*.bak`, `benchmark_scores/**/*_todo*.json`, `benchmark_scores/**/*TODO*.json`. Verhindert versehentliches Committen unfertiger Placeholder-Cards.
- **`config/provider_config.yaml`** — Neues lokales Modell `hermes-4-14b-abliterated` (Hermes 4 14B BF16 Abliterated GGUF) hinzugefügt.
- **Provider-Index bereinigt** — Verwaisten `provider_id: "todo"`-Eintrag aus `_index.json` entfernt; zugehörige `todo.json` Card gelöscht (war versehentlich vom Review-Generator angelegt worden).
- **DeepSeek Model Cards** — Display-Namen und Pricing-Updates (v3.1: $0.21/$0.79, v3.2: $0.2288/$0.3432).
- **Provider Card ergänzt** — `nous_research.json` (Nous Research, CLOUD-Act-Exposition).
- **Reviews-Batch** — 28 neue `review_*.md`-Dateien für 2026-06-02/03-Benchmark-Outputs (Magistral, Mistral, Qwen, GLM, DeepSeek, etc.).
- **Per-Model Review-Batch-Modus** — `make reviews-auto` löst jetzt **alle drei** Review-Typen (Benchmark + PC-Bias + Tool-Use) pro Modell in Folge aus, statt nur Benchmark. Verhindert Tool-Use-Review-Lücken (12 Modelle waren ohne `tooluse_narrative_review_*.md` trotz vorhandener `tooluse*.md` Audit-Logs). Neues `--per-model` Flag in `scripts/analysis/generate_review.py` mit Helper `_run_per_model_all_reviews()`; iteriert `audit_logs/<slug>/` und ruft für jeden Slug `_run_audit_reviews(benchmark)` → `_run_audit_reviews(bias)` → `_run_tooluse_reviews()` auf. Skip-Logik (mtime-Check) bleibt pro Review-Typ erhalten. `make reviews-auto-legacy` ruft das alte Verhalten auf. 8 neue Tests in `tests/test_generate_review_per_model.py`. Validierung: `--per-model` benötigt `--type all` UND (`--all` ODER `--model`). 40/40 Tests grün.
- **Diagnose-Doku** — Klarstellung in `systemPatterns.md`: Weder `run_benchmark.py` noch `benchmark_auto.py` triggern Reviews am Laufende. Reviews sind immer ein expliziter separater Schritt. Ursprüngliche Hypothese „Local Benchmark triggert Reviews nicht" war falsch — kein Benchmark-Skript tut das.
- **Tri-State `supports_tool_use`** — Klarstellung: `true / false / "untested"` als kanonische Zustände. `null` ist Legacy-Synonym für `"untested"`. Helper `normalize_supports_tool_use()` und Konstante `SUPPORT_TOOL_USE_UNTESTED` in `utils/model_utils.py`. `update_model_card_tooluse_fields()` akzeptiert jetzt `bool | "untested" | None` und entfernt `tooluse_tested_at` bei `untested`. Review-Generator zeigt unterschiedliche Meldungen für `false` („nicht fähig") vs. `untested` („Benchmark zuerst ausführen"). `tooluse_exporter.py` setzt `untested` automatisch wenn `p1_scores` leer ist. Web-Export normalisiert in `data.leaderboard.model_card.supports_tool_use_state` zu einem von drei Strings. Migration-Skript `scripts/dev/migrate_supports_tool_use_tri_state.py` aktualisiert alle Cards (Dry-Run unterstützt) und schreibt Tool-Use-Backlog nach `docs/MAINTENANCE_LOG.md`. 17 neue Tests in `tests/test_supports_tool_use_tri_state.py`.

## [v4.2.0] - 2026-05-31

**OpenRouter-Migration, Free-Tier-Support und Provider-Routing-Bug-Fix.**

### Fixed
- **`resolve_provider()` — `:free`-Suffix-Bug** — Ollama-Erkennung griff bisher bei jedem `:` im Modell-Namen, also auch bei `vendor/model:free`. Fix: `:` → Ollama nur wenn kein `/` im Namen (`utils/model_utils.py`).
- **Fallback-Heuristik `"/" in model_id`** — Führte bisher zu falschem Groq-Routing. Korrigiert: `"/"` → `openrouter` (nicht mehr Groq). Groq-Fallback bleibt nur für bare Namen ohne Namespace-Slash (`qwen`, `llama`, `moonshot`).
- **`openrouter.py` — Alibaba Cloud `data_collection`-Policy** — Qwen-Modelle (und andere Alibaba-Cloud-Endpoints via OpenRouter) lieferten HTTP 404 ohne explizite Zustimmung. Fix: `extra_body={"data_collection": "allow"}` wird bei jedem Request gesetzt (Override der Account-Defaultpolicy).

### Added
- **OpenRouter Free Tier** — Modelle mit `:free`-Suffix (`vendor/model:free`) nutzen automatisch das neue `openrouter_free`-Rate-Limit-Profil (18 RPM / `concurrent_requests: 1`, konservativ unter dem 20-RPM-Limit). Kein anderer Endpoint, kein zweiter API-Key notwendig — nur der Suffix genügt.
- **`config/rate_limits.yaml`** — Neues `openrouter`-Profil (60 RPM / 3 concurrent) und `openrouter_free`-Profil (18 RPM / 1 concurrent).
- **`unified_runner.py` — Free-Tier-RateLimiter-Routing** — Erkennt `provider=openrouter` + `model.endswith(":free")` und wählt das konservative Profil automatisch.

### Changed
- **Ollama → OpenRouter Migration (3 Modelle):** `gemma4:31b-cloud` → `google/gemma-4-31b-it`, `deepseek-v3.1:671b-cloud` → `deepseek/deepseek-chat-v3.1`, `deepseek-v3.2:cloud` → `deepseek/deepseek-v3.2`. Model Cards umbenannt und `model_id` aktualisiert. Alle 5 Benchmark-CSVs migriert (Modell-IDs + `provider: ollama → openrouter`).
- **`config/provider_config.yaml`** — 3 Modelle unter `openrouter.models` eingetragen (DeepSeek, Gemma 31B). Zwei neue kostenpflichtige Qwen-Modelle hinzugefügt (`qwen/qwen3.7-max`, `qwen/qwen3.6-plus`) mit `model_type: proprietary_api`.
- **`generate_review.py` — Skip-Logik vereinfacht** — mtime-Vergleich gegen Leaderboard-CSV entfernt; Existenz-Check reicht: vorhandene Narrative-Reviews werden immer übersprungen (kein `--force` nötig für Nicht-Wiederholungen).
- **`Makefile` — `make review` FLAGS** — `AUTO=1` und `FORCE=1` werden jetzt korrekt an `generate_review.py` weitergegeben (für `--all` und `--model`-Pfad).
- **Docs** — `ARCHITECTURE.md`, `SCORING_METHODOLOGY.md`, `SETUP_GUIDE.md`: Ollama-Cloud-Proxy-Ära entfernt, OpenRouter-Free-Tier-Doku ergänzt.
- **`AGENTS.md` — Pitfall ergänzt** — `resolve_provider()` `:free`-Suffix-Verhalten und OpenRouter-Namespace-Heuristik dokumentiert.

### Added (Model Cards)
- **`qwen_qwen3_7-max.json`** — Qwen 3.7 Max (Proprietär, Alibaba Cloud via OpenRouter, input $1.25/1M, output $3.75/1M, context 131K, `thinking_probe_detected: false`).
- **`qwen_qwen3_6-plus.json`** — Qwen 3.6 Plus (Proprietär, Alibaba Cloud via OpenRouter, Hybrid-Reasoning, input $0.33/1M bis 256K / $2.00/1M darüber, output $1.95/1M bis 256K / $6.00/1M darüber, `thinking_probe_detected: true`, `parameter_architecture: hybrid`).

---

## [v4.1.0] - 2026-05-30

**llamacpp-Erweiterung, Bug-Fixes und Modul-Aktivierung.**

### Fixed
- **Double-Start-Bug (llamacpp.py)** — `_query_active_model()` erkennt laufendes Modell per `/v1/models`-API; verhindert Server-Neustart wenn korrektes Modell bereits läuft.
- **Duplicate-Runner-Bug (benchmark_auto.py)** — Zweite `UnifiedBenchmarkRunner`-Instanziierung entfernt; `lcpp_client` zeigte auf veraltete Instanz und ignorierte laufenden Server.

### Added
- **gemma-3-12b-it-q8** — Neues lokales Modell (Q8_0-GGUF) in `provider_config.yaml` + vollständige Model Card.
- **3 Module aktiviert** — `code_quality`, `reasoning_logic`, `documentation_quality` in `benchmark_config.yaml` standardmäßig aktiv.

### Changed
- **Model Card Schema** — `model_version` enthält nur noch Format/Quant-Stufe (z.B. `Q4_K_M (GGUF)`). Plattform-Info ausgelagert in neues Feld `weights_source`.
- **Docs** — `ARCHITECTURE.md`, `DEVELOPER_GUIDE.md`, `SETUP_GUIDE.md`, `AGENTS.md`: llamacpp Server-Management, `reasoning_content`-Sonderfall (Gemma-4 Native Thinking), `_infer_provider()`-Heuristik-Pitfall.

---

## [v4.0.0] - 2026-05-26

**Erster öffentlicher Release nach abgeschlossener Tool-Use-Phase und vollständiger Architektur-Migration.**

### Highlights
- **Tool Use Benchmark Module** — Erstes agentic Benchmark-Modul: 6 Assets in 3 Phasen (Tool Selection, Content Synthesis, Multilingual), Live-MCP-Integration (Tavily `web_search` + `http_fetch`), Content Verification Framework mit Halluzinations-Cap, 257 Tests. Erste Production-Runs: gpt-5-mini 76.5 %, grok-4-fast 74.2 %, kimi-k2 73.6 %.
- **Model Cards als Pricing-SSoT** — Vollständige Pipeline-Migration. LiteLLM aus Pricing-Pfad entfernt.
- **Architektur-Bereinigung** — Budget-Enforcement entfernt, `cost_limits.yaml` gelöscht, `resolve_token_budget()` als SSoT.
- **257/257 Tests grün** — Ruff + Pylint 10.00/10.

### Details
Vollständige Einzelversionen: v3.10.0 → v3.15.1 (siehe unten).

---

## [v3.15.1] - 2026-05-26

### Removed
- **Daily Budget Enforcement komplett entfernt** — `CostTracker.check_budget()`, `get_daily_spend()`, `get_remaining_budget()` und `warning_threshold` gelöscht. `config/cost_limits.yaml` (enthielt nur noch tägl. Budget-Limits) gelöscht. Budget-Vorab-Check in `llm_client.py` entfernt. "Remaining Budget"-Anzeige in `base_runner.py` entfernt. `CostLimitExceededError`-Klasse und Exception-Handler in `unified_runner.py` entfernt.

### Changed
- **`utils/cost_tracker.py`:** Schlanker konstruktor — kein YAML-Config-Loading mehr. `cost_log_file` ist jetzt hardcodiert (`outputs/cost_log.csv`). `calculate_cost()` ist 1-stufig: Model Card JSON → Warning-Log + `return 0.0`. Kosten-Tracking (`track_request()`, `get_spend_breakdown()`) vollständig erhalten.

### Docs
- **`AGENTS.md`**, **`README.md`**, **`docs/USER_GUIDE.md`**, **`docs/DEVELOPER_GUIDE.md`:** Alle Referenzen auf `cost_limits.yaml` als Legacy-Fallback und auf tägliche Budget-Limits entfernt. Pricing-SSoT-Hinweis zeigt jetzt direkt auf Model Card JSON.

---

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
