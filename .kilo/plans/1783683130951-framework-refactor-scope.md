# Framework-Refactoring: Scope-Analyse & Section-Plan

**Ziel:** Framework-Codebasis (nicht Module) gegen Architektur-Regeln prüfen, Drift identifizieren und in **abschnittsweise abarbeitbare Refactoring-Sektionen** zerlegen — sequenziert nach Abhängigkeit, damit jeder Block für sich allein prüfbar bleibt.

**Refactoring-Tiefe (Nutzer-Entscheidung):** Strukturell + Drift-Fix. God-Script-Zerlegung, tote-Stubs-Entfernung, Config-SSoT-Migration, print→logging in `utils/`. Keine Verhaltensänderung an Scoring/Token-Budget/Provider-Logik.

**Out of Scope:** Implementation, neue Features, Datenmigration, `benchmark_modules/*`, `tests/`-Refactoring (Tests sind Akzeptanznetz), Web-Site-Repo, Performance-Optimierung, CHANGELOG/Versions-Bump, `memory-bank/`-Updates.

---

## 1. Architektur-Invariants (Referenz — nicht verhandelbar)

Aus `CLAUDE.md`, `.agent/architecture.md`, `.agent/data-pipeline.md`, `memory-bank/systemPatterns.md`:

| Regel | SSoT-Aufruf |
|---|---|
| Judge ≠ Test (Blind-Judge) | `judge_evaluator.evaluate_with_judge()` → `JudgeRunner.score()` ohne `tested_model_name` in der Prompt-Variable |
| Sequenzielle Modell-Abarbeitung | `UnifiedBenchmarkRunner.run_benchmark()` stoppt/restartet pro Modell — NICHT parallelisieren |
| Atomare CSV-Writes | `_write_to_csv()` → `tempfile.mkstemp()` + `os.replace()` |
| Card-Pfad SUFFIX-SSoT | `build_card_id()` in `utils/model_utils.py` — Schreibpfad `{base}--{shortcode}.json` |
| Card-First CSV-Senke | `enforce_card_first()` in `utils/model_utils.py`, aufgerufen von `result_manager.save_results()` |
| Config via `ConfigValidator` | `utils/config_validator.py:_load_config()` — Skripte dürfen NICHT `yaml.safe_load()` auf `benchmark_config.yaml`/`provider_config.yaml` anwenden |
| Thinking-Extraktion SSoT | `_extract_reasoning_tokens()` + `ThinkAccumulator` in `utils/providers/base.py` — nur genuine proprietäre Felder dürfen overriden |
| Anti-God-Script | `ruff.toml` C901 `max-complexity = 12` (hart konfiguriert, keine Ausnahmen) |
| Judge-Reset zwischen Tasks | Jede `.score()`-Bewertung ist ein frischer API-Call. KEIN Evaluation-Context-Caching (HTTP-Client-Reuse ist erlaubt). |

---

## 2. Quantitative Basis (verifizierte Messwerte)

### 2.1 C901-Komplexitätsverletzungen (80 gesamt)

`ruff check --select C901` über `scripts/ utils/ run_benchmark.py`:

| Datei | C901-Verstöße | LOC |
|---|---|---|
| `utils/model_utils.py` | 6 | 2429 |
| `scripts/manage_model_cards.py` | 4 | 2006 |
| `scripts/maintenance/clean_results.py` | 3 | 660 |
| `scripts/analysis/generate_review.py` | 3 | 1195 |
| `scripts/leaderboard/score_calculator.py` | 2 | 844 |
| `scripts/leaderboard/module_integration.py` | 2 | 432 |
| `scripts/core/tooluse_exporter.py` | 2 | 908 |
| `scripts/analysis/generate_tooluse_report.py` | 2 | 805 |
| `utils/scoring/judge_evaluator.py` | 1 | 328 |
| `utils/providers/xai.py` | 1 | — |
| `utils/providers/openrouter.py` | 1 | — |
| + weitere (1× je Datei) | ~14 | — |

**Die 5 größten Dateien** (LOC, top-level + method defs):

| Datei | LOC | Defs | C901 |
|---|---|---|---|
| `utils/model_utils.py` | 2429 | 49 | 6 |
| `scripts/web_export.py` | 2050 | 60 | 0 |
| `scripts/manage_model_cards.py` | 2006 | 55 | 4 |
| `scripts/core/unified_runner.py` | 1525 | 47 | 0 |
| `scripts/core/benchmark_auto.py` | 1509 | 46 | 0 |

**Auffällig:** `web_export.py` hat 0 C901-Verstöße trotz 2050 LOC — die Komplexität verteilt sich auf viele kleine Funktionen, aber die Datei verstößt gegen Anti-God-Script per Länge, nicht per Komplexität.

### 2.2 `print()` in Framework-Utils (verifiziert)

| Datei | `print()`-Calls | Kategorie |
|---|---|---|
| `scripts/core/benchmark_auto.py` | 107 | CLI — vertretbar |
| `scripts/analysis/generate_review.py` | 73 | CLI — vertretbar |
| `utils/benchmark_ui.py` | 53 | **Framework-Util** — auf logging umstellen |
| `utils/base_runner.py` | 42 | **Framework-Util** — auf logging umstellen |
| `utils/provider_selector.py` | 21 | **Framework-Util** — auf logging umstellen |
| `scripts/core/unified_runner.py` | 38 | CLI-Orchestrator — teilweise vertretbar |

### 2.3 Config-Raw-Loads (verifiziert: 13 Skripte laden roh)

Skripte, die `yaml.safe_load` auf `benchmark_config.yaml`/`provider_config.yaml` anwenden statt `ConfigValidator` zu nutzen:

**Kritisch (Framework-Core):**
- `scripts/manage_model_cards.py` (2 Calls, Z.262/299)
- `scripts/core/vllm_batch.py`

**Sekundär (Tools/Analysis):**
- `scripts/analysis/generate_vendor_cards.py`
- `scripts/tools/list_models.py`, `list_modules.py`, `validate_assets.py`, `discover_thinking_tags.py`, `judge_health.py`, `smoketest_vllm_spark.py`
- `scripts/dev/setup_env.py`, `sync_cost_limits.py`
- `scripts/verify_model_cards.py`
- `scripts/leaderboard/formatter.py`

**Bereits SSoT-OK:** `unified_runner.py` (nutzt `self.validator.config`), `web_export.py`, `generate_review.py`, `probe_thinking.py`, `clean_results.py`, `run_cross_model_benchmark.py`, `llamacpp_batch.py`, `module_integration.py`, `create_model_card.py`.

### 2.4 Provider-Override-Audit (verifiziert)

`_extract_reasoning_tokens` — 6 Vorkommen:

| Datei | Implementierung | Status |
|---|---|---|
| `utils/providers/base.py:173` | SSoT — prüft 3 Pfade (OpenAI `completion_tokens_details`, Anthropic `output_tokens_details`, Mistral `reasoning_tokens`) | **SSoT** |
| `utils/providers/openai.py:316` | `return super()._extract_reasoning_tokens(usage)` | **Dead no-op stub** — löschen |
| `utils/providers/xai.py:183` | `return super()._extract_reasoning_tokens(usage)` | **Dead no-op stub** — löschen |
| `utils/providers/groq.py:190` | `return super()._extract_reasoning_tokens(usage)` | **Dead no-op stub** — löschen |
| `utils/providers/anthropic.py:164` | `return super()._extract_reasoning_tokens(usage)` | **Dead no-op stub** — löschen |
| `utils/providers/cohere.py:354` | Genuine Logik: `tokens.reasoning_tokens` (Cohere-spezifisch) | **Behalten** — dokumentieren |

### 2.5 Judge-Subsystem (verifiziert: EINE Pipeline, keine Duplikation)

- `utils/scoring/judge_evaluator.py` (328 LOC) = **aktive Fassade**. Importiert `JudgeRunner` + `LLMJudgeConfig` aus `llm_judge/`. Caller: `unified_runner.py:52` (`from utils.scoring.judge_evaluator import evaluate_with_judge, generate_audit_log`).
- `utils/scoring/llm_judge/` (1587 LOC, 5 Module) = **Implementation**. Wird von `judge_evaluator.py` aufgerufen.
- **KEINE Doppel-Pipeline** — der ursprüngliche Plan-Entwurf war hier falsch.
- **Caching-Befund:** `evaluate_with_judge._runner_cache` cached den `JudgeRunner` (HTTP-Client) über Tasks hinweg. Das ist Connection-Pooling, KEIN Evaluation-Context-Caching. `JudgeRunner` trägt nur `self._config` + `self._provider` als Instance-State — keine Ergebnis-/Kontext-Historie. **Invariant NICHT verletzt.**
- **Echte Probleme:**
  1. Function-Attribute-Caching (`evaluate_with_judge._runner_cache`, `._cfg_cache`, `._runner_cfg_key`) — untestbar, ungewöhnliches Pattern. Sollte ein Modul-Level-Singleton oder eine kleine Klasse werden.
  2. `llm_judge/tests/` (5 Test-Dateien) liegt **im Package** statt im Root `tests/`-Verzeichnis — Inkonsistenz mit Repo-Konvention. → Nach `tests/` verschieben (Nutzer-Entscheidung).
  3. 1 C901-Verstoß in `judge_evaluator.py`.

### 2.6 Helper-Duplikations-Audit (verifiziert: KEINE Duplikation)

| Helper | Definitionsort | Duplikat? |
|---|---|---|
| `slugify()` | `scripts/web_export.py:150` | **Nein** — `_safe_name()` in `model_utils.py:183` hat andere Semantik (filename-safe vs URL-slug, andere Normalisierung) |
| `_strip_none()` | `scripts/web_export.py:2040` | **Nein** — einzige Definition im Repo |
| `parse_compact_number/parse_percent/parse_int` | `scripts/web_export.py:368/392/404` | **Nein** — einzige Definitionen |
| `sanitize_audit_log()` | `scripts/web_export.py:312` | **Nein** — einzige Definition |
| `_atomic_write_json/_text/_copy` | `scripts/web_export.py` | **Nein** — einzige Definitionen |

**Fazit:** Die Helper sind nicht dupliziert, aber **falsch platziert** — sie leben in `web_export.py` statt in `utils/`. Organisatorisches Problem, kein DRY-Bruch.

---

## 3. Scope-Inventar pro Bereich

### 3.1 Core Benchmark-Funktionalität

**Dateien:** `run_benchmark.py` (576), `scripts/core/unified_runner.py` (1525), `scripts/core/benchmark_auto.py` (1509), `utils/base_runner.py` (529), `utils/result_manager.py` (425), `utils/benchmark_utils.py` (~480), `scripts/core/runner_contract.py` (88).

**Befund — stabil, drei Drift-Punkte:**
1. **`benchmark_auto.py` (1509 LOC, 107 `print()`, 46 Defs):** Größtes CLI-Skript. Enthält vLLM-Batch-Wrapper, ToolUse/PC-Subprozess-Delegation, Force-Skip-Logik, Pre/Post-Run-Hooks. 0 C901-Verstöße — Komplexität ist verteilt, aber Länge verstößt gegen Anti-God-Script.
2. **`unified_runner.py` (1525 LOC, 38 `print()`):** 4× `if provider == "ollama"` (Z.389/400/804) + 1× `openrouter :free`-Sonderpfad (Z.1053). Config-Zugriff via `self.validator.config` (SSoT-OK). 0 C901-Verstöße.
3. **`base_runner.py` (529 LOC, 42 `print()`):** Framework-Util mit hohem print-Anteil → auf logging umstellen.

### 3.2 Konnektoren (Provider-Plugins)

**Dateien:** `utils/providers/` (15 Dateien, ~3500 LOC).

**Befund — stabil, zwei Drift-Punkte:**
1. **4 dead no-op `_extract_reasoning_tokens`-Stubs** (siehe 2.4) — löschen.
2. **`vllm_base.py` (1244 LOC):** Swap-Entkopplung (Session 52), Sampling-Whitelist (Session 50), Probe-3-State (Session 47). 0 C901-Verstöße, aber lange Methoden (`swap_model`, `start_server`, `_ensure_model_ready`).
3. **`llamacpp_base.py` (888 LOC):** 1-Klasse-pro-Hardware-Pattern (Auto-Registry via `__init_subclass__`). Stabil.
4. **`provider_selector.py` (21 `print()`), `provider_health.py`, `provider_detection.py`:** Drei Module mit teils überlappender Provider-Inferenz-Logik. Raw-Loads in `provider_selector.py` + `provider_health.py`.

### 3.3 Leaderboard-Erzeugung

**Dateien:** `scripts/leaderboard/` (8 Dateien, ~2500 LOC gesamt).

**Befund — bereits gut modularisiert, minimaler Handlungsbedarf:**
- `__init__.py` (308), `score_calculator.py` (844, 2 C901), `module_integration.py` (432, 2 C901), `data_loader.py` (261), `exporter.py` (260), `formatter.py` (308, raw-load), `config.py` (67), `print_leaderboard.py` (7).
- Package ist mit kleinen Dateien bereits Anti-God-Script-konform.
- 4 C901-Verstöße in 2 Dateien — auflösen.
- `formatter.py` lädt Config roh → auf ConfigValidator umstellen.

### 3.4 Karten & Datenbestände (SSoT-Datenfluss)

**Dateien:** `utils/model_utils.py` (2429, 6 C901), `utils/card_utils.py`, `utils/card_template.py`, `utils/vendor_card_template.py`, `utils/card_sync.py`, `utils/result_manager.py` (425), `benchmark_scores/`.

**Befund — kritischster Bereich:**
1. **`utils/model_utils.py` (2429 LOC, 49 Defs, 6 C901):** SSoT-Schaltzentrale für Card-Pfad, Model-ID-Auflösung, Token-Budget, Thinking, Provider-Inferenz. Größter C901-Offender im Framework. God-Script per Funktionsdichte.
2. **Card-Pfad-SSoT (SUFFIX):** Funktionsfähig (Session 49). 13 Karten via `git mv` migriert. Direkt-Aufrufer von `_card_path()` ohne `provider=X` sind potenzielle Bug-Quellen — zu auditieren.
3. **27 Migrations-/Cleanup-Skripte** in `scripts/maintenance/` + `scripts/dev/` — Nutzer-Entscheidung: einmalige Migrationen nach `scripts/legacy/` verschieben.

### 3.5 Web-Export

**Dateien:** `scripts/web_export.py` (2050, 60 Defs, 0 C901), `scripts/analysis/generate_vendor_cards.py` (346, raw-load), `scripts/analysis/generate_tooluse_report.py` (805, 2 C901), `scripts/analysis/generate_review.py` (1195, 3 C901, 73 `print()`).

**Befund — God-Script per Länge, nicht per Komplexität:**
1. **`web_export.py` (2050 LOC, 0 C901):** Komplexität ist verteilt (60 kleine Funktionen), aber Dateilänge verstößt gegen Anti-God-Script. Helper (`slugify`, `parse_*`, `_strip_none`, `_atomic_*`) sind korrekt implementiert aber falsch platziert → nach `utils/` extrahieren.
2. **`generate_review.py` (1195, 3 C901, 73 `print()`):** Review-Generator mit Prompt-Variablen-Auflösung. Höchste C901-Dichte nach `model_utils.py`.
3. **`generate_vendor_cards.py` (346, raw-load):** Lädt Config roh → auf ConfigValidator umstellen.

### 3.6 Logging

**Dateien:** `utils/logging_config.py` (~100), `logs/`, `outputs/audit_logs/`, `outputs/cost_log.csv`.

**Befund — dünn besiedelt:**
1. `logging_config.py` ist das einzige formale Logging-Modul.
2. Framework-Utils mit hohem `print()`-Anteil: `benchmark_ui.py` (53), `base_runner.py` (42), `provider_selector.py` (21) → auf logging umstellen.
3. Keine Rotation-/Retention-Policy in `logging_config.py`.

---

## 4. Refactoring-Sektionen (abschnittsweise Abarbeitung)

**Nutzer-Entscheidungen integriert:**
- Refactoring-Tiefe: Strukturell + Drift-Fix
- Migrationsskripte → `scripts/legacy/`
- `llm_judge/tests/` → `tests/`

Reihenfolge nach Abhängigkeit. Jede Sektion einzeln abschließbar.

---

### **Sektion A — `utils/model_utils.py` aufschlüsseln** [strukturell]

**Ziel:** 2429-LOC-SSoT-Datei in logische Submodule zerlegen, 6 C901-Verstöße auflösen.

**Scope:**
- Funktionenscan via `rg -n "^def \|^_PROVIDER_\|^class " utils/model_utils.py`.
- Gruppierung in Submodule (Arbeitshypothese — bei Implementation zu verifizieren):
  - `utils/model_id.py`: `_safe_name`, `normalize_model_id`, `internal_id_to_config_form`, `resolve_canonical_model_id`, `resolve_provider`
  - `utils/model_card_io.py`: `build_card_id`, `_card_path`, `_find_card`, `enforce_card_first`, `ensure_card`, `CARD_DIR`
  - `utils/model_thinking.py`: `resolve_effective_thinking`, `probe_thinking_model`, `is_reasoning_model`, `is_reasoning_model_from_card`, `_THINK_TAGS`
  - `utils/model_token_budget.py`: `resolve_token_budget`
  - `utils/model_pricing.py`: Price-Lookup-Helper (falls vorhanden)
- `model_utils.py` wird Re-Export-Bridge (`from utils.model_id import *` etc.) —保持了 Abwärtskompatibilität für alle existierenden `from utils.model_utils import X`-Importe.

**Validierung:**
- `make validate` exit 0
- `pytest -v` identische Pass-Rate (Baseline: 1148 passed, 1 skipped, 1 pre-existing failure)
- `ruff check --select C901 utils/model_utils.py` → 0 Verstöße (oder alle in Submodule verschoben)
- Smoke-Run: `make benchmark MODEL=<one_local> MODULE=cli_benchmark` verifiziert `resolve_provider()` + `_find_card()` + `resolve_canonical_model_id()` + `resolve_token_budget()`

**Risiko:** Hoch — alle anderen Sektionen hängen davon ab. Circular-Import-Gefahr. Tests sind Akzeptanznetz.

**Reihenfolge:** Zuerst.

---

### **Sektion B — Judge-Subsystem aufräumen** [strukturell + drift-fix]

**Ziel:** Fassade+Impl-Struktur vereinfachen, Function-Attribute-Caching eliminieren, Tests harmonisieren.

**Scope:**
1. **Function-Attribute-Caching → Modul-Level-Singleton:** `evaluate_with_judge._runner_cache` / `._cfg_cache` / `._runner_cfg_key` durch eine `_JudgeRunnerCache`-Klasse oder Modul-Level-Variable ersetzen. Besser testbar, selbe Semantik (HTTP-Client-Reuse, kein Context-Caching).
2. **`llm_judge/tests/` → `tests/`:** 5 Test-Dateien verschieben, Import-Pfade anpassen.
3. **1 C901-Verstoß in `judge_evaluator.py`** auflösen.
4. **KEINE Pipeline-Konsolidierung** — es gibt nur eine Pipeline (`judge_evaluator.py` → `llm_judge/`). Ursprünglicher Plan-Entwurf war hier falsch.

**Validierung:**
- Blind-Judge-Invariante: in keinem Judge-Prompt-Pfad taucht `tested_model_name` als sichtbare Variable auf (nur als `tested_model_id`-Metadatum, das der Judge nicht sieht).
- `pytest tests/test_judge_runner_lifecycle.py tests/test_pipeline_integration.py tests/test_judge_integration.py tests/test_judge_parser.py tests/test_judge_handoff.py`
- Smoke-Run: 1 Modell + 1 Modul, Judge-Score identisch zu Pre-Refactor-Snapshot.

**Risiko:** Mittel — Score-Drift = historische Benchmarks ungültig. Snapshot-Vergleich Pflicht.

---

### **Sektion C — Provider-Connectors: Dead Stubs + Modularisierung** [drift-fix + strukturell]

**Ziel:** 4 no-op Provider-Stubs löschen, `vllm_base.py`-Methoden aufteilen.

**Scope:**
1. **4 dead no-op Stubs löschen:** `_extract_reasoning_tokens` in `openai.py:316`, `xai.py:183`, `groq.py:190`, `anthropic.py:164` — alle sind `return super()._extract_reasoning_tokens(usage)`. Base-Methode prüft bereits alle 3 Pfade (OpenAI/Anthropic/Mistral).
2. **`cohere.py:354` behalten** — genuine Cohere-spezifische Logik (`tokens.reasoning_tokens`). Mit Kommentar dokumentieren warum.
3. **`vllm_base.py` (1244 LOC):** Lange Methoden (`swap_model`, `start_server`, `_ensure_model_ready`, `_resolve_sampling`) in private Helper zerlegen. Swap-Entkopplung (Session 52) und Token-Capture-Proxy-Fix (Session 47) intakt lassen.
4. **`provider_selector.py` + `provider_health.py`:** Raw-Loads auf `ConfigValidator` umstellen.
5. **Neuer Guardrail-Test:** `tests/test_provider_reasoning_ssot.py` — AST-Sweep über `utils/providers/*.py`, stellt sicher dass kein Provider `_extract_reasoning_tokens` definiert außer `cohere.py`.

**Validierung:**
- `pytest tests/test_vllm_spark_provider.py` (34 Tests), `tests/test_vllm_batch.py` (9 Tests)
- `pytest tests/test_provider_reasoning_ssot.py` (neu — muss grün sein)
- Pro Provider: `reasoning_tokens`-Wert in CSV vorher/nachher identisch (insb. OpenAI o-Series, Anthropic Extended Thinking, Groq, xAI).
- Smoke-Run: vllm_spark + llamacpp_spark Real-Lifecycle-Test.

**Risiko:** Niedrig für Stub-Löschung (dead code). Mittel für vllm_base-Aufteilung (zarte Pfade).

---

### **Sektion D — `web_export.py` & `manage_model_cards.py` aufbrechen** [strukturell]

**Abhängigkeit:** Sektion A (model_utils.py) muss abgeschlossen sein, damit Helper-Extraktion sauber importiert.

**Ziel:** Beide 2000+-LOC-Skripte in logische Submodule zerlegen.

**Scope für `web_export.py` (2050 LOC, 0 C901):**
- Helper extrahieren nach `utils/web_helpers.py`: `slugify`, `sanitize_audit_log`, `parse_compact_number`, `parse_percent`, `parse_int`, `parse_star_float`, `normalize_pending`, `extract_badge_tier`, `extract_version`, `_strip_emojis`, `_strip_none`, `_atomic_write_json/_text/_copy`.
- Filter-Logik → `scripts/web_export/filters.py` (neue Package): `_load_export_blacklist`, `_build_vendor_alias_map/_card_id_lookup`, `_normalize_vendor`, `_collect_community_cards`, `_build_community_*`.
- Loader → `scripts/web_export/loader.py`: `_load_sources`, `_build_pc_lookups`, `_load_pc_block_meta`.
- Entry-Builder → `scripts/web_export/entry_builders.py`: `_build_characteristics`, `_build_leaderboard_entry`, `_lookup_pc_row`, `_build_compass_entry`, `_build_block_scores`.
- Top-Level-Output → `scripts/web_export/top_level.py`: `_write_top_level_outputs`, `_setup_output_dirs`, `_export_model_files`.
- `main()` + CLI-Args bleiben in `scripts/web_export.py` (~150 LOC schlanker Orchestrator).

**Scope für `manage_model_cards.py` (2006 LOC, 4 C901):**
- `Researcher`-Klasse → `scripts/card_research/researcher.py`
- `CardManager`-Klasse → `scripts/card_research/manager.py`
- Dataclasses (`CardFinding`, `CardCheckReport`, `CardMakeReport`, `RunSummary`, `ResearchReport`, `LLMSpec`, `LLMSession`) → `scripts/card_research/models.py`
- CLI-Entry bleibt.
- 2 C901-Verstöße in `_parse_tool_call` (15), `_extract_json_object` (13), `_research_tooluse_one` (17) auflösen.

**Validierung:**
- `pytest tests/test_web_export_*.py` (viele vorhanden)
- `make web-export` + JSON-Snapshot-Diff gegen Pre-Refactor-Output
- `make card-research MODEL=<one>` Smoke-Test

**Risiko:** Mittel — Vendor-/Blacklist-Logik ist komplex. JSON-Snapshot-Diff als Sicherheitsnetz.

---

### **Sektion E — `benchmark_auto.py` aufschlüsseln** [strukturell]

**Ziel:** 1509-LOC-CLI-Orchestrator entzerren, 107 `print()` teilweise auf logging umstellen.

**Scope:**
- vLLM-Batch-Aufruf-Strang → prüfen ob `scripts/core/vllm_batch.py` bereits alles kapselt (Wrapper in `benchmark_auto.py` evtl. überflüssig).
- ToolUse-/PC-Subprozess-Delegation → `scripts/core/delegate_runner.py` (generischer Subprozess-Wrapper, ersetzt inline-`subprocess.run`).
- Pre/Post-Run-Hooks → `scripts/core/lifecycle_hooks.py`.
- `main()` + CLI-Argumente bleiben in `benchmark_auto.py`.

**Validierung:**
- `make benchmark-auto MODEL=<x>` Smoke-Run
- `pytest tests/test_vllm_batch.py`

**Risiko:** Niedrig–Mittel — Orchestration-Code, gut testbar.

---

### **Sektion F — Helper-SSoT: utils/text_helpers.py + utils/io_helpers.py** [strukturell]

**Abhängigkeit:** Sektion D (web_export.py) extrahiert die Helper — diese Sektion definiert die SSoT-Module.

**Ziel:** Aus `web_export.py` extrahierte Helper als SSoT in `utils/` etablieren.

**Scope:**
- `utils/text_helpers.py`: `slugify`, `sanitize_audit_log`, `parse_compact_number`, `parse_percent`, `parse_int`, `parse_star_float`, `normalize_pending`, `extract_badge_tier`, `extract_version`.
- `utils/io_helpers.py`: `_atomic_write_json`, `_atomic_write_text`, `_atomic_copy`, `_strip_none` (generalisiert auf `Any`).
- `web_export.py` importiert aus diesen Modulen.
- Audit: welche anderen Dateien inline-Replikationen haben (verifiziert: keine — siehe 2.6).

**Validierung:**
- `pytest tests/test_web_export_helpers.py`
- JSON-Snapshot-Diff

**Risiko:** Niedrig — viele Tests decken die Helper ab.

---

### **Sektion G — Config-SSoT: Raw-Loads auf ConfigValidator umstellen** [drift-fix]

**Ziel:** 13 Skripte von `yaml.safe_load` auf `ConfigValidator` umstellen.

**Scope:**
- **Kritisch:** `scripts/manage_model_cards.py` (2 Calls), `scripts/core/vllm_batch.py`.
- **Sekundär:** `generate_vendor_cards.py`, `list_models.py`, `list_modules.py`, `validate_assets.py`, `discover_thinking_tags.py`, `judge_health.py`, `smoketest_vllm_spark.py`, `setup_env.py`, `sync_cost_limits.py`, `verify_model_cards.py`, `leaderboard/formatter.py`.
- Pattern: `yaml.safe_load(open(path))` → `ConfigValidator(str(ROOT_DIR / "benchmark_config.yaml")).config`.
- Bei Skripten, die nur Modul-Config (`benchmark_modules/*/config.yaml`) laden — nicht `benchmark_config.yaml` — bleibt `yaml.safe_load` korrekt (Modul-Configs sind separate YAMLs, nicht Teil des ConfigValidator-Merge).
- **Neuer Guardrail-Test:** `tests/test_config_ssot.py` — AST-Sweep über `scripts/`, prüft dass kein `yaml.safe_load`-Call ein String-Argument mit `benchmark_config` oder `provider_config` enthält.

**Validierung:**
- Pro Skript: Dry-Run / `--help` verifiziert.
- `pytest tests/test_config_ssot.py` (neu — muss grün sein)
- `.venv/bin/ruff check <geänderte-dateien>` — keine neuen Verstöße.

**Risiko:** Niedrig — reiner Import-Tausch, keine Logikänderung.

---

### **Sektion H — Migrationsskripte nach `scripts/legacy/`** [organisatorisch]

**Nutzer-Entscheidung:** Einmalige Migrationen nach `scripts/legacy/` verschieben.

**Scope:**
- **Aktive Werkzeuge (bleiben):** `consolidate_csv.py`, `clean_results.py`, `cleanup_runs.py`, `cleanup_reviews.py`, `verify_counts.py`, `prune_orphaned_reports.py`, `audit_model_versions.py`, `audit_markdown.py`, `audit_id_variants.py`, `clean.py`, `cleanup_helpers.py`, `recover_pc_results.py`, `repair_pc_leaderboard.py`, `repair_tooluse_card_fields.py`, `backfill_tooluse_csv_rows.py`, `backfill_card_versions.py`.
- **Nach `scripts/legacy/` verschieben** (Pattern: `migrate_*`, `fix_*`, `sanitize_*`, `retroactive_*`):
  - `scripts/maintenance/`: `migrate_model_versions.py`, `migrate_model_versions_pollution.py`, `fix_version_names.py`, `fix_commercial_hashes.py`, `fix_all_caches_and_dbs.py`, `sanitize_8_models_source_csvs.py`, `sanitize_8_models_tooluse.py`, `sanitize_benchmark_csvs.py`, `retroactive_polarity_fix.py`, `debug_gemma_score.py`.
  - `scripts/dev/`: `migrate_use_case_primary.py`, `migrate_context_fields.py`, `migrate_supports_tool_use_tri_state.py`, `migrate_parameter_architecture.py`, `migrate_prices_to_cards.py`, `migrate_architecture_tags.py`, `migrate_tooluse_runs_nested.py`, `fix_benchmark_costs.py`, `fix_cost_log.py`, `fix_model_cards_whitelist.py`, `patch_tool_use.py`, `add_license_fields.py`, `add_sampling_keys.py`, `add_vendor_field.py`, `backfill_modalities.py`, `backfill_parolen_scores.py`, `backfill_pc_block_scores.py`.
- Makefile-Targets nur für aktive Werkzeuge behalten.
- `scripts/legacy/__init__.py` leer anlegen.

**Validierung:**
- `make audit` / `make consolidate-csv` Smoke-Run
- `make validate` exit 0

**Risiko:** Niedrig — rein organisatorisch. `git mv` für Audit-Trail.

---

### **Sektion I — Logging: print() → logging in Framework-Utils** [drift-fix]

**Ziel:** Framework-Utils (`utils/`) nutzen `logging` statt `print()`.

**Scope:**
- `utils/benchmark_ui.py` (53 `print()`) → `logger.info()`/`logger.warning()`.
- `utils/base_runner.py` (42 `print()`) → `logging`.
- `utils/provider_selector.py` (21 `print()`) → `logging`.
- `utils/logging_config.py`: Rotation-/Retention-Policy ergänzen (`RotatingFileHandler` 10 MB × 5).
- CLI-Skripte (`benchmark_auto.py`, `generate_review.py`, `unified_runner.py`) dürfen `print()` für User-Facing-Output behalten — nur Framework-Utils umstellen.
- **Neuer Guardrail-Test:** `tests/test_utils_no_print.py` — AST-Sweep über `utils/*.py`, prüft dass kein `print()`-Call existiert (außer in `logging_config.py`).

**Validierung:**
- `pytest tests/test_utils_no_print.py` (neu — muss grün sein)
- `make benchmark MODEL=<x> MODULE=<y>` Smoke-Run, `logs/`-Verzeichnis beobachtet.
- `.venv/bin/ruff check utils/` — keine neuen Verstöße.
- `make benchmark MODEL=<x> MODULE=<y>` Smoke-Run, `logs/`-Verzeichnis beobachtet.
- `rg "^\s*print\(" utils/` → 0 Treffer (außer `logging_config.py` selbst).

**Risiko:** Niedrig.

---

### **Sektion J — Provider-Inferenz-Branching → Config** [drift-fix]

**Ziel:** 4 `if provider == "ollama"` + 1 `openrouter :free`-Sonderpfad in `unified_runner.py` konfigurierbar machen.

**Scope:**
- Pro Branch: extrahieren, was _konkret_ anders ist (Rate-Limit? Endpoint-Detection? Sampling?).
- Wenn konfigurierbar in `provider_config.yaml` → Config-Feld hinzufügen, Branch entfernen.
- Wenn hardcoded special case → Pitfall-Doku + Kommentar.

**Validierung:**
- Smoke-Run: ollama_local-Modell + openrouter-Modell mit `:free`-Suffix.
- `pytest tests/test_resolve_provider_canonical_form.py` (9 Tests).

**Risiko:** Niedrig–Mittel — reine Strukturierung, aber Provider-Logik ist kritisch.

---

### **Sektion K — ToolUse-Sub-Persistenz-Refactoring** [strukturell]

**Ziel:** `run_tooluse_benchmark.py` + `tooluse_exporter.py` (908 LOC, 2 C901) Schema-Konsistenz prüfen.

**Scope:**
- Schema-Vergleich `tooluse_*.csv` ↔ `*_benchmark.csv`.
- SSoT-Entscheidung: separate CSV-Familie (Tool-Daten sind strukturell anders), aber ToolUse-Scores wandern ins gemeinsame Leaderboard.
- 2 C901-Verstöße in `tooluse_exporter.py` auflösen.
- `generate_tooluse_report.py` (805, 2 C901) aufräumen.

**Validierung:**
- Web-Export-Snapshot: ToolUse-Detail-Block + ToolUse-Scores stimmen überein.
- `pytest tests/test_repair_tooluse_card_fields.py`

**Risiko:** Hoch — ToolUse-Pfade in Sessions 44/47/49 mehrfach korrigiert.

---

### **Sektion L — Leaderboard-C901 + `formatter.py` Raw-Load** [drift-fix]

**Ziel:** 4 C901-Verstöße in `scripts/leaderboard/` auflösen, `formatter.py` auf ConfigValidator umstellen.

**Scope:**
- `score_calculator.py` (844, 2 C901): komplexe Score-Aggregations-Funktionen entzerren.
- `module_integration.py` (432, 2 C901): Card-Lookup-Logik entzerren.
- `formatter.py` (308): Raw-Load auf ConfigValidator umstellen.

**Validierung:**
- `make leaderboard` + CSV-Snapshot-Diff
- `pytest tests/test_leaderboard*.py`

**Risiko:** Niedrig — Leaderboard ist bereits gut modularisiert.

---

### **Sektion M — `generate_review.py` (1195, 3 C901) + `clean_results.py` (660, 3 C901)** [strukturell]

**Ziel:** C901-Verstöße in Review-Generator und Cleanup-Script auflösen.

**Scope:**
- `generate_review.py`: 3 komplexe Funktionen (Prompt-Variablen-Auflösung, Metric-Stripping, Per-Model-Loop) entzerren.
- `clean_results.py`: 3 komplexe Cleanup-Funktionen entzerren.

**Validierung:**
- `make reviews-auto --force` Smoke-Run + Markdown-Snapshot-Diff
- `make clean-results --dry-run` Smoke-Run

**Risiko:** Mittel — Review-Generator ist LLM-Prompt-Pipeline.

---

## 5. Bearbeitungs-Reihenfolge (sequenziell)

```
Phase 0 (QA-Fundament — VOR allem anderen):
  0a. make lint-Target einführen (ruff + pylint)
  0b. make test um tests/ erweitern (SSoT-Guardrails aktivieren)
  0c. Test-Baseline verifizieren und dokumentieren
  0d. Ruff-Baseline einfrieren (1146 Verstöße); auto-fixable (631) optional vorab bereinigen

Phase 1 (Fundament):
  A. utils/model_utils.py aufschlüsseln [strukturell]
     └─ C901: 6 → 0
     └─ test_id_ssot_invariants.py AST-Whitelist um neue Submodule erweitern

Phase 2 (Provider + Judge — parallel möglich nach A):
  B. Judge-Subsystem aufräumen [strukturell + drift-fix]
  C. Provider-Connectors: Stubs + Modularisierung [drift-fix + strukturell]

Phase 3 (Web-Export — braucht A):
  F. Helper-SSoT utils/text_helpers.py + io_helpers.py [strukturell]
  D. web_export.py & manage_model_cards.py aufbrechen [strukturell]  (braucht F)

Phase 4 (Core-Orchestrierung):
  E. benchmark_auto.py aufschlüsseln [strukturell]
  J. Provider-Inferenz-Branching → Config [drift-fix]

Phase 5 (Drift-Fixes — parallel möglich):
  G. Config-SSoT: Raw-Loads umstellen [drift-fix]
  I. Logging: print() → logging [drift-fix]
  L. Leaderboard-C901 + formatter.py [drift-fix]

Phase 6 (Spezialisierte Bereiche):
  K. ToolUse-Sub-Persistenz [strukturell]
  M. generate_review.py + clean_results.py C901 [strukturell]

Phase 7 (Organisatorisch — jederzeit parallel):
  H. Migrationsskripte → scripts/legacy/ [organisatorisch]
```

**Parallele Tracks:** B+C (Phase 2), G+I+L (Phase 5), H (jederzeit). Phase 0 ist blockierend für alle anderen.

---

## 6. QA-Regime: Ruff, Pylint, Mypy (Lücke im aktuellen Setup)

### 6.1 Ist-Zustand (verifiziert — kritische Lücke)

| Aspekt | Ist-Zustand | Problem |
|---|---|---|
| `make validate` | Führt `scripts/tools/validate_assets.py --all` aus | Prüft **nur Asset-Schemas** (YAML), NICHT Python-Code |
| `make test` | Führt `pytest benchmark_modules/ utils/scoring/llm_judge/tests/` aus | Läuft **NICHT** über `tests/` — die SSoT-Guardrail-Tests werden nicht ausgeführt |
| `make lint` | **Existiert nicht** | Ruff + Pylint sind installiert aber ohne Makefile-Target |
| Mypy | `mypy.ini` konfiguriert (lenient), aber kein Target | Wird nie automatisch ausgeführt |
| Ruff-Verstöße aktuell | **1146** (576 auto-fixable) | Codebasis ist NICHT ruff-clean |

**Ruff-Verstoß-Breakdown (Top 15):**

| Code | Count | Bedeutung | Auto-fix? |
|---|---|---|---|
| UP006 | 263 | `typing.List` → `list` (pyupgrade) | Ja |
| UP045 | 154 | `typing.Optional` → `X \| None` (pyupgrade) | Ja |
| PLR2004 | 126 | Magic value in comparison | Nein |
| E701 | 89 | Multiple statements on one line (`if x: pass`) | Ja |
| UP035 | 86 | Deprecated `typing.*` import | Ja |
| **C901** | **80** | **Mccabe complexity > 12** | Nein |
| E402 | 79 | Import not at top of file | Teilweise |
| UP015 | 55 | Redundant open mode (`"r"` → default) | Ja |
| W293 | 39 | Whitespace on blank line | Ja |
| SIM105 | 37 | Use `contextlib.suppress` | Ja |
| UP017 | 23 | `datetime.UTC` alias | Ja |
| SIM102 | 23 | Collapsible nested if | Ja |
| F401 | 15 | Unused import | Ja |
| F541 | 10 | f-string without placeholders | Ja |
| F841 | 9 | Unused variable | Ja |

### 6.2 Soll-Zustand: Neues QA-Regime für das Refactoring

**Vor Sektion A (Prä-Phase 0):**

1. **`make lint`-Target einführen** (neu im Makefile):
   ```makefile
   lint:
       $(PYTHON) -m ruff check scripts/ utils/ run_benchmark.py
       $(PYTHON) -m pylint scripts/ utils/ run_benchmark.py --rcfile=.pylintrc
   ```
2. **`make test`-Target korrigieren** — `tests/` hinzufügen:
   ```makefile
   test: validate
       $(PYTHON) -m pytest benchmark_modules/ tests/ utils/scoring/llm_judge/tests/ -v --tb=short
   ```
3. **Ruff-Baseline einfrieren:** Vor dem ersten Refactoring-Schritt die 1146-Verstöße dokumentieren. Policy: **keine neuen Verstöße**; auto-fixable violations (UP006/UP045/UP035/E701/W293 = 631) dürfen vorab in einem separaten Commit bereinigt werden (ohne Logikänderung).

**Pro Sektion (einheitliche QA-Gates):**

| Gate | Befehl | Blocker? | Policy |
|---|---|---|---|
| Ruff | `.venv/bin/ruff check <sektion-files>` | Ja | Neue Verstöße = 0; bestehende dürfen nicht steigen. Sektions-spezifisch: C901 → 0 für aufgeteilte Dateien. |
| Pylint | `.venv/bin/pylint <sektion-files>` | Warn | Pylint läuft lenient (viele disabled rules). Nur `error`-Level als Blocker, `warning` als Review-Punkt. |
| Mypy | `.venv/bin/mypy <sektion-files>` | Nein (Empfehlung) | Mypy ist stark relaxt (`disable_error_code` für 9 Codes). Als Optional-Check, nicht als Blocker. |
| SSoT-Tests | `pytest tests/test_*_ssot*.py tests/test_id_ssot_invariants.py tests/test_web_export_*.py` | Ja — alle müssen grün sein | Siehe Section 7. |
| Unit-Tests | `pytest -v --tb=short` (gesamtes Repo) | Ja — Pass-Rate darf nicht sinken | Baseline vorab verifizieren (siehe 6.3). |

### 6.3 Test-Baseline (vorab zu verifizieren)

Die Memory-Bank nennt "1148 passed, 1 skipped, 1 pre-existing failure" (Session 57). Aber: diese Zahl stammt aus dem Memory-Bank, nicht aus einem aktuellen Run. **Vor Sektion A muss die tatsächliche Baseline verifiziert werden:**

```bash
.venv/bin/pytest benchmark_modules/ tests/ utils/scoring/llm_judge/tests/ -v --tb=short 2>&1 | tail -5
```

Die hier dokumentierte Zahl ist **ungeprüft** — der implementierende Agent muss die echte Baseline als Referenz abspeichern, bevor er die erste Sektion beginnt.

---

## 7. Architektur-Guardrails: SSoT-Test-Suite (bestehend + neu)

### 7.1 Bestehende SSoT-Enforcement-Tests (8 Dateien in `tests/`)

Diese Tests sind die **architektonischen Guardrails** — sie erzwingen SSoT-Invariants zur Compile-Zeit. **Kritisch:** `make test` führt sie aktuell NICHT aus (nur `benchmark_modules/` + `llm_judge/tests/`). Sektion 0 muss `make test` um `tests/` erweitern, damit diese Guardrails wirksam werden.

| Test-Datei | Erzwungene Invariant | Mechanismus |
|---|---|---|
| `test_card_path_suffix_ssot.py` | `build_card_id()` + `_card_path(for_write=True)` produzieren beide SUFFIX-Form `{base}--{shortcode}.json` | Funktions-Aufruf + Pfad-Vergleich |
| `test_id_ssot_invariants.py` | (1) `enforce_card_first()` ↔ `resolve_canonical_model_id()` liefern gleiche kanonische Form. (2) `_safe_name()` deckt alle Sonderzeichen. (3) Idempotenz. (4) **AST-Sweep:** `re.sub` für ID-Transformation NUR in `model_utils.py` + `card_utils.py` erlaubt — nirgendwo sonst. | `ast.walk()` über alle `.py`-Dateien, prüft `re.sub`-Calls mit String-Arg |
| `test_card_vocabulary_ssot.py` | Card-Feld-Vokabular konsistent zwischen Template, Validator und existierenden Cards | JSON-Feld-Vergleich |
| `test_sampling_defaults_ssot.py` | Alle 7 Sampling-Default-Felder in Template + allen 112 Cards vorhanden (mit `null`) | JSON-Feld-Sweep |
| `test_taxonomy_ssot.py` | Taxonomy-Werte konsistent zwischen Config und Cards | Wertemengen-Vergleich |
| `test_vendor_card_ssot_refactor.py` | Vendor-Card-Struktur (keine Preise, keine Stärken/Schwächen in Vendor-Cards) | Feld-Whitelist-Check |
| `test_web_export_ssot.py` | `load_model_card()` nutzt `resolve_canonical_model_id()` als SSoT-Brücke; `_lookup_pc_row()` nutzt `slugify` (bewusst gegen `_safe_name`); `_build_tooluse_entry()` kanonisiert via `resolve_canonical_model_id` | Funktions-Verkettungs-Asserts |
| `test_web_export_vendor_drift.py` | Vendor-Card-Daten nicht driftend zwischen Model-Card und Vendor-Card | Feld-Vergleich |

**Der AST-Sweep in `test_id_ssot_invariants.py` ist das Schlüsselmuster** — er zeigt, wie Architekturregeln nicht nur dokumentiert, sondern **automatisch durchgesetzt** werden. Dieses Pattern wird für neue Guardrails erweitert (siehe 7.2).

### 7.2 Neue Architektur-Tests pro Refactoring-Sektion

Jede drift-fixende Sektion bekommt einen **neuen SSoT-Guardrail-Test**, der den fix dauerhaft absichert. Pattern: AST-Sweep oder Import-Check, analog zu `test_id_ssot_invariants.py`.

| Sektion | Neue Test-Datei | Erzwungene Invariant | Mechanismus |
|---|---|---|---|
| **C** (Provider-Stubs) | `tests/test_provider_reasoning_ssot.py` | Kein Provider darf `_extract_reasoning_tokens` definieren, außer `cohere.py` (genuine `tokens.reasoning_tokens`-Logik) | `ast.walk()` über `utils/providers/*.py`, prüft Method-Defs |
| **G** (Config-SSoT) | `tests/test_config_ssot.py` | Kein Skript darf `yaml.safe_load` auf `benchmark_config.yaml` oder `provider_config.yaml` anwenden — nur `ConfigValidator` | AST-Sweep: `yaml.safe_load`-Calls, prüft ob String-Arg `benchmark_config`/`provider_config` enthält |
| **I** (print→logging) | `tests/test_utils_no_print.py` | Keine `print()`-Aufrufe in `utils/` (außer `logging_config.py`) | `ast.walk()` über `utils/*.py`, prüft `Call`-Nodes mit `func.id == "print"` |
| **A** (model_utils split) | `test_id_ssot_invariants.py` erweitern | AST-Sweep erlaubt `re.sub` für ID-Transformation in den NEUEN Submodulen statt nur `model_utils.py` | Test-Whitelist erweitern |

**Diese Tests sind Teil des Sektion-Scopes** — eine Sektion ist erst abgeschlossen, wenn ihr Guardrail-Test grün ist.

### 7.3 Guardrail-Test-Ausführung

Nach Sektion 0 (`make test` um `tests/` erweitert) werden alle SSoT-Tests automatisch bei jedem `make test`-Lauf ausgeführt. Zusätzlich pro Sektion:

```bash
.venv/bin/pytest tests/test_*_ssot*.py tests/test_id_ssot_invariants.py -v --tb=short
```

---

## 8. Snapshot-Diff-Mechanismus (konkret)

Der Plan fordert JSON-/CSV-/Markdown-Snapshot-Diffs als Validierung. Da kein bestehendes Tool dafür existiert, hier das konkrete Vorgehen:

**Vor jeder Sektion (Pre-Refactor-Snapshot erstellen):**
```bash
# Web-Export-Snapshot
make web-export
cp -r CrucibleMark-Web/src/_data/ /tmp/snapshot-pre-<sektion>/

# Leaderboard-CSV-Snapshot
make leaderboard
cp benchmark_scores/benchmark_leaderboard*.csv /tmp/snapshot-pre-<sektion>/

# Review-Snapshot (für Sektion M)
make reviews-auto --force
cp -r docs/reviews/ /tmp/snapshot-pre-<sektion>/
```

**Nach der Sektion (Post-Refactor-Snapshot vergleichen):**
```bash
make web-export
diff -r /tmp/snapshot-pre-<sektion>/ CrucibleMark-Web/src/_data/  # muss leer sein
```

**Toleranz:** Strukturelle Identität (gleiche Keys, gleiche Werte). Feldreihenfolge in JSON darf differieren (`diff` mit `jq -S` normalisieren). Wenn Diff nicht leer → Sektion fehlgeschlagen, Rollback.

---

## 9. Risiken

**Top-Risiken:**
- **Sektion A** (`model_utils.py`) — Risk-Surface. Circular-Import-Gefahr bei Submodule-Aufspaltung. Re-Export-Bridge als Sicherheitsnetz, aber Smoke-Run pro Schritt Pflicht. **AST-Sweep-Test (`test_id_ssot_invariants.py`) muss vorab um die neuen Submodul-Pfade erweitert werden**, sonst schlägt er nach dem Split fehl.
- **Sektion B** (Judge) — Score-Drift = historische Benchmarks ungültig. Snapshot-Vergleich vorher/nachher Pflicht.
- **Sektion K** (ToolUse) — bereits mehrfach korrigiert (Sessions 44/47/49), jeder weitere Eingriff birgt Regressionsrisiko.
- **Sektion D** (web_export.py) — Vendor-/Blacklist-Logik komplex, JSON-Snapshot-Diff als Sicherheitsnetz. **Achtung:** `web_export.py` wird von 5+ Test-Dateien via `__import__("scripts.web_export", ...)` importiert — Package-Umwandlung muss diese Import-Pfade intakt lassen oder alle Tests anpassen.

**Niedrige Risiko:**
- Sektion C (Stub-Löschung = dead code).
- Sektion G (Config-SSoT = Import-Tausch).
- Sektion H (organisatorisch).
- Sektion I (print→logging).

---

## 10. Korrekturen zum ursprünglichen Plan-Entwurf

Der erste Plan-Entwurf enthielt 7 faktische Fehler, die durch Code-Verifikation korrigiert wurden:

1. ~~"Doppel-Pipeline Judge"~~ → `judge_evaluator.py` ist Fassade, `llm_judge/` ist Implementation. Eine Pipeline. Caching = HTTP-Client-Reuse, kein Context-Caching.
2. ~~"5 redundante Provider-Overrides"~~ → 4 dead no-op Stubs (löschen) + 1 genuine Override (cohere, behalten).
3. ~~"`slugify`/`_strip_none` Duplikation"~~ → Keine Duplikation. Verschiedene Semantiken bzw. einzige Definition. Nur falsch platziert.
4. ~~"Leaderboard braucht Refactoring"~~ → Package ist bereits modular (8 kleine Dateien). Nur 4 C901-Verstöße.
5. ~~Byte-Zahlen als LOC~~ → Korrigiert: z.B. `leaderboard/__init__.py` = 308 LOC (nicht 11235 bytes).
6. ~~"`make validate` prüft Lint"~~ → `make validate` prüft nur Asset-Schemas. Kein `make lint`-Target existiert. 1146 Ruff-Verstöße unaddressed.
7. ~~"SSoT-Tests werden automatisch ausgeführt"~~ → `make test` läuft nicht über `tests/`. Die 8 Guardrail-Tests sind aktuell blind. Prä-Phase 0 muss `make test` um `tests/` erweitern.

---

**Status:** Plan korrigiert und verifiziert. Bereit zur Implementation. Prä-Phase 0 (`make lint` + `make test`-Fix) ist der erste Schritt, Sektion A der empfohlene Startpunkt danach.
