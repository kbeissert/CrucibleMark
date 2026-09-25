# CrucibleMark Code-Review Audit-Protokoll

**Datum:** 2026-09-25
**Reviewer:** Kilo (deepseek-v4-pro)
**Scope:** Vollständige Codebasis (v5.3.0, 477 Python-Dateien, ~110.000 LOC)
**Referenz:** AGENTS.md, docs/ARCHITECTURE.md, docs/DEVELOPER_GUIDE.md, memory-bank/
**Baseline:** Ruff ✓ | Pylint 9.99/10 | 1913 Tests passed | 17 Skipped

---

## Executive Summary

### Kritische Befunde (Critical)
| ID | Bereich | Beschreibung |
|---|---|---|
| CRIT-01 | Provider | **Anthropic Streaming: reasoning_tokens immer None** — `output_tokens_details` wird beim Merge verworfen |
| CRIT-02 | Provider | **Groq Streaming: Kein finish_reason, unguarded choices[0]** — Reask-Trigger tot, potenzieller IndexError |

### Schwere Befunde (High)
| ID | Bereich | Beschreibung |
|---|---|---|
| HIGH-01 | SSoT | Card-Pfad-Bypass in lifecycle_hooks.py (inline statt _find_card) |
| HIGH-02 | SSoT | _safe_name-Bypass in delegate_runner.py |
| HIGH-03 | Architektur | unified_runner.py: 1623 Zeilen (Anti-God-Script) |
| HIGH-04 | Architektur | # noqa: C901 in 2 Dateien (verboten laut AGENTS.md) |
| HIGH-C01 | Provider | OpenAI is_accessible() verwechselt 404 mit Auth-Fehler |
| HIGH-C02 | Provider | Ungeschlossene Probe-Clients in OpenAI + Groq |
| HIGH-C03 | Provider | Groq Client ohne max_retries=0 |

### Weitere Befunde
- **10 Medium** (SSoT-Bypasses, Hardcoded CARD_DIR, shell=True-Risiken, commercial close()-Lücken)
- **5 Low** (Dokumentations-Leaks, irreführende Judge-Docstrings)

---

## 1. Architektur-Compliance

### 1.1 SSoT/DRY-Verstöße

#### HIGH-01: Card-Pfad-Bypass (lifecycle_hooks.py)
- **Datei:** `scripts/core/lifecycle_hooks.py:72-73`
- **Verstoß:** Card-Pfade inline: `card_dir / f"{mid.replace('/', '_').replace(':', '_')}.json"` + zweite Variante mit `.replace('.', '_')`. Dupliziert `_find_card()`.
- **Fix:** `_find_card()` aus `utils.model_utils` importieren und verwenden.

#### HIGH-02: _safe_name-Bypass (delegate_runner.py)
- **Datei:** `scripts/core/delegate_runner.py:62, :120`
- **Verstoß:** `normalize_model_id(model).replace("/", "_").replace(":", "_")` inline dupliziert `_safe_name()`.
- **Fix:** `_safe_name()` importieren und aufrufen.

#### MED-01: Slug-Bypass (base_test.py)
- **Datei:** `benchmark_modules/base_test.py:175`
- **Verstoß:** `result_data.model.replace(":", "_").replace("/", "_")` inline.
- **Fix:** `_safe_name()` verwenden.

#### MED-02: Slug-Duplikation (political_compass)
- **Dateien:** `benchmark_modules/political_compass/test.py:941` + `benchmark_modules/political_compass/core/audit_logger.py:746`
- **Verstoß:** `str(model).replace(":", "_").replace("/", "_").replace(".", "_")` — identische `_safe_name()`-Duplikation an 2 Stellen.
- **Fix:** Einmaliger Import aus `utils.model_utils._safe_name()`.

#### MED-03: Hardcoded CARD_DIR (7 Dateien)
- **Dateien:**
  - `scripts/leaderboard/module_integration.py:59, 480`
  - `scripts/leaderboard/score_calculator.py:38`
  - `scripts/leaderboard/exporter.py:215`
  - `scripts/leaderboard/data_loader.py:226`
  - `scripts/web_export/entry_builders.py:64`
  - `scripts/web_export/top_level.py:256`
  - `scripts/core/unified_runner.py:171`
- **Verstoß:** `Path("benchmark_scores/model_cards")` statt `CARD_DIR` aus `utils.model_card_io`.
- **Fix:** `from utils.model_card_io import CARD_DIR`.

#### MED-04: _safe_name()-Redefinition (dev-Tool)
- **Datei:** `scripts/dev/recompute_pc_v31.py:59`
- **Verstoß:** Lokale `_safe_name()`-Redefinition statt Import.
- **Fix:** Import aus `utils.model_utils`.

### 1.2 Anti-God-Script

#### HIGH-03: unified_runner.py (1.623 Zeilen)
- **Datei:** `scripts/core/unified_runner.py`
- **Verstoß:** Größte Datei. Enthält Runner-Logik + PC-Leaderboard-Cache-Skip (`_check_pc_leaderboard_skip`).
- **Fix:** PC-Helfer in `pc_skip_resolver.py` auslagern.

#### MED-05: benchmark_auto.py (1.136 Zeilen)
- **Datei:** `scripts/core/benchmark_auto.py`
- **Verstoß:** Orchestration + Leaderboard-Triggering + Skip-Logik gemischt.
- **Fix:** Skip-Logik in `skip_resolver.py` auslagern.

#### MED-06: base_runner.py (919 Zeilen) — Concern-Mix
- **Datei:** `utils/base_runner.py:718`
- **Verstoß:** Measurement-Layer liest Leaderboard-CSV (`_check_pc_leaderboard_skip`).
- **Fix:** Leaderboard-Prüfung in Publishing-Layer oder als Callback.

### 1.3 Separation of Concerns

#### INFO-01: Leaderboard-Update im Benchmark-Loop (akzeptiert)
- **Datei:** `scripts/core/benchmark_auto.py:563`
- **Kontext:** `update_leaderboard` via Subprocess während Benchmark. Failure-isolated, dokumentiert in `runner_contract.py:17-22`.
- **Betroffen:** `run_benchmark.py:311`, `run_score_benchmark.py:182,300,329,364`, `run_tooluse_benchmark.py:591,632,667,683`, `run_political_compass_benchmark.py:86,121,156,182`.

### 1.4 Design-Constraint-Verstöße

#### HIGH-04: # noqa: C901 in Nicht-Test-Code
- **Dateien:**
  - `benchmark_modules/political_compass/test.py:828` (execute: 3 Runs + Anti-Diplomat + Intersection)
  - `scripts/dev/create_model_card.py:179` (main: zu viele Pfade)
- **Regel:** AGENTS.md verbietet `# noqa: C901`. CC ≤ 12 verbindlich.
- **Fix:** Methoden nach Pfaden aufteilen.

#### INFO-02: Judge-Fallback-Docstring irreführend
- **Datei:** `utils/scoring/llm_judge/judge_runner.py:9, 163`
- **Verstoß:** Docstring "Provider fallback chain: primary → fallback", aber `_call_provider:266` implementiert Fail-Fast (raises JudgeUnavailableError).
- **Implementierung:** AGENTS-konform (kein Fallback). Docstring muss korrigiert werden.

### 1.5 Bestanden
- ✅ vLLM Dual-Profile: Expansion nur für `api_type == "vllm"` (config_validator.py:142)
- ✅ Blacklist-Scope: Nur Web-Export liest `web_export_blacklist.yaml`
- ✅ `# ruff: noqa: F401`: Keine Vorkommen in Codebasis
- ✅ Sequenzielle Ausführung: Keine Parallel-Primitive (ThreadPool, ProcessPool, asyncio.gather)
- ✅ Config-Layer: Expansion nach Merge, vor Duplikat-Check

---

## 2. Provider-Connector-Audit (geprüft: base, anthropic, openai, groq)

### 2.1 Critical Issues

#### CRIT-01: Anthropic Streaming — reasoning_tokens permanent None
- **Datei:** `utils/providers/anthropic.py:303-306`
- **Schweregrad:** 🔴 Critical
- **Verstoß:** `_apply_anthropic_message_delta` merged `stream_usage` als `{"input_tokens": ..., "output_tokens": ...}` — `output_tokens_details` (enthält `reasoning_tokens`) wird verworfen.
- **Impact:** `_extract_reasoning_tokens` (line 218) bekommt ein Plain-Dict → `getattr(dict, "output_tokens_details")` ist None → Reasoning-Tokens für ALLE Anthropic-Streaming-Runs = None. Untergräbt Reask-Trigger #5 (base.py:552-554).
- **Fix:** `"output_tokens_details": getattr(usage, "output_tokens_details", None)` ins Merge-Dict.

#### CRIT-02: Groq Streaming — Drei Mängel
- **Datei:** `utils/providers/groq.py:145-186`
- **Schweregrad:** 🔴 Critical
- **Verstoß 1:** Kein `stream_options={"include_usage": True}` → `stream_usage` None.
- **Verstoß 2:** `chunk.choices[0]` unguarded (line 158) → Usage-Chunks mit `choices=[]` → IndexError.
- **Verstoß 3:** `finish_reason` nie im Streaming-Pfad erfasst → Reask-Trigger tot.
- **Fix:** `stream_options` setzen, Guard für `choices[0]`, Finish-Reason extrahieren.

### 2.2 High Issues

#### HIGH-C01: OpenAI is_accessible() — 404 ≠ Auth-Fehler
- **Datei:** `utils/providers/openai.py:263-266`
- **Schweregrad:** 🟠 High
- **Verstoß:** `except Exception` fängt ALLE Fehler. `NotFoundError` auf Test-Modell `gpt-3.5-turbo` → False (obwohl API erreichbar).
- **Kontrast:** Groq/Anthropic unterscheiden korrekt: 404 → True, Auth → False, Permission → False.
- **Fix:** Spezifische Exception-Typen wie Groq.py:71-86.

#### HIGH-C02: Ungeschlossene Probe-Clients
- **Dateien:** `utils/providers/openai.py:256`, `utils/providers/groq.py:64`
- **Schweregrad:** 🟠 High
- **Verstoß:** `check_client = OpenAI(...)` in `is_accessible()` ohne `close()` → dangling Connection-Pools.
- **Fix:** `try/finally: check_client.close()`.

#### HIGH-C03: Groq ohne max_retries=0
- **Datei:** `utils/providers/groq.py:51`
- **Schweregrad:** 🟠 High
- **Verstoß:** `Groq(api_key=...)` OHNE `max_retries=0` → SDK-Retries + Framework-Retries = doppelte Wiederholungen.
- **Contrast:** `openai.py:247` setzt `max_retries=0` mit Kommentar.
- **Fix:** `max_retries=0` ergänzen.

### 2.3 Medium Issues

#### MED-C01: Base.close() No-Op + Watchdog-Lücke
- **Datei:** `utils/providers/base.py:133-141`
- **Schweregrad:** 🟡 Medium
- **Verstoß:** `close()` ist Default-No-Op. Kein kommerzieller Connector überschreibt es (anthropic, openai, groq, xai, openrouter, mistral, cohere). Der Watchdog `_abort_on_escalation_timeout` (base.py:1060-1074) dokumentiert bereits: Provider ohne close() sind vom Loop-Guard-Abbruch nicht betroffen.
- **Impact:** Watchdog kann hängende API-Requests nicht abbrechen.
- **Fix:** `close()`-Override mit `self._client.close()` in jedem Connector.

#### MED-C02: Redundante Re-Imports (base.py)
- **Datei:** `utils/providers/base.py:376, 390`
- **Verstoß:** `import re` + `import time` im Retry-Loop, obwohl beide Modul-Top-Level-Imports sind (lines 7, 9).
- **Fix:** Entfernen.

### 2.4 Noch nicht geprüfte Connectors
- mistral.py, google.py, xai.py, cohere.py, openrouter.py, ollama.py, llamacpp_base.py, llamacpp.py, llamacpp_spark.py, vllm_base.py, vllm_spark.py
- vLLM Dual-Profile-Swap-Audit (`vllm_base.py:_ensure_model_ready`, 1573 Zeilen)

---

## 3. Sicherheit

### Gemeldete Befunde

| ID | Severity | Datei | Beschreibung |
|---|---|---|---|
| MED-07 | 🟡 Medium | docs/: vllm-gx10-config-guide.md | sk-local-mg2026 in Git-getrackten Docs |
| MED-08 | 🟡 Medium | 14 Stellen (llamacpp/vllm base) | Systematisches shell=True (Config-getrieben) |
| MED-09 | 🟡 Medium | scripts/card_research/common.py:946 | subprocess.run ohne check=True |
| LOW-03 | 🟢 Low | config/provider_config.yaml:553 | Platzhalter sk-local (localhost-only) |

### Bestanden
- ✅ Alle YAML-Ladevorgänge: `yaml.safe_load()` (39 Vorkommen)
- ✅ Keine hardcodierten API-Keys im Python-Source
- ✅ `.env` in `.gitignore`
- ✅ `${DGX_AUTH_TOKEN}` externalisiert
- ✅ Kein `eval()`/`exec()` gefunden

### Offene Sicherheits-Checks
- Path-Traversal (user-controlled Pfade)
- Dependency-CVEs (requirements.txt)
- Injection in Shell-Kommandos (Modell-IDs in cmd-Strings)

---

## 4. Performance & Ressourcen

| ID | Severity | Datei | Beschreibung |
|---|---|---|---|
| MED-C01 | 🟡 Medium | base.py:133-141 | Commercial-Connectors ohne close()-Override |
| MED-C02 | 🟡 Medium | base.py:376,390 | Redundante Re-Imports im Retry-Loop |
| LOW-P01 | 🟢 Low | base.py:364, llm_client.py:96,108 | F-Strings in Logger-Calls (immer formatiert) |
| PASS | ✅ | llm_client.py:77 | atexit.register(self.close) vorhanden |
| PASS | ✅ | llamacpp/vllm | close()-Override + "close instead of drop" |
| PASS | ✅ | openrouter.py:89-97 | httpx.Client mit with-Block |

### Offene Performance-Checks
- Memory: CSV-Loading, Dict-Akkumulation, Card-Bulk-Load
- Heavy Top-Level Imports (numpy, torch, sentence-transformers)
- Logging-in-Loop
- N+1 File-Read Patterns

---

## 5. Code-Qualität (Pylint C-Level)

| ID | Severity | Datei | Beschreibung |
|---|---|---|---|
| CQ-01 | 🟡 Medium | utils/model_id.py:70,73,128,137,268 | 5 line-too-long (104-109 chars, Limit 100) |
| CQ-02 | 🟡 Medium | utils/base_runner.py:105-596 | 19 line-too-long (101-137 chars) |
| CQ-03 | 🟡 Medium | utils/scoring_utils.py:74 | line-too-long (124 chars) |
| CQ-04 | 🟡 Medium | utils/model_id.py:182,215,231 | Import outside toplevel (3 Stellen) |
| CQ-05 | 🟡 Medium | utils/base_runner.py:334,623,667 | Import outside toplevel (4 Stellen) |
| CQ-06 | 🟡 Medium | utils/model_utils.py:182 | Wrong import order (standard nach first-party) |
| CQ-07 | 🟢 Low | utils/text_helpers.py:155,162 | Missing function docstrings |
| CQ-08 | 🟢 Low | utils/base_runner.py:582,588 | "d != 0" → "d" vereinfachen |

---

## 6. Testing

### Befunde

| ID | Severity | Datei | Beschreibung |
|---|---|---|---|
| TEST-01 | 🟡 Medium | tests/test_id_ssot_invariants.py:203 | Skip auf Directory-Existenz (fragil) |
| TEST-02 | 🟡 Medium | tests/test_web_export_field_coverage.py:46 | Skip "Web-Export noch nicht erstellt" bei fehlendem Glob-Match |
| TEST-03 | 🟡 Medium | tests/test_provider_reasoning_ssot.py:106 | Skip "Nur base.py wird geprueft" — unvollständige Abdeckung |

### Bestanden
- ✅ Phase 2 Judge-Fix: `_resolve_judge_cfg()` → keine Live-Judge-Calls in ToolUse-Tests
- ✅ `_resolve_haiku_export_dir` jetzt dynamisch (Glob statt Slug)
- ✅ `test_controller.py` stubbt SemanticSimilarity (autouse-Fixture)

### Offene Testing-Checks
- Flaky-Test-Kandidaten (time/network/random-abhängig)
- Live-Endpoint-Calls in anderen Testmodulen
- Global-State-Mutationen zwischen Tests

---

## 7. Pylint Technische Schulden

| ID | Typ | Datei | Beschreibung |
|---|---|---|---|
| PTD-01 | Cyclic Import | run_benchmark.py | utils.model_card_io ↔ utils.model_version |
| PTD-02 | Cyclic Import | run_benchmark.py | utils.card_utils → model_utils → token_budget → thinking |
| PTD-03 | Cyclic Import | run_benchmark.py | llm_client → providers.base → model_thinking |
| PTD-04 | Cyclic Import | run_benchmark.py | cost_tracker → model_utils → token_budget → thinking → llm_client |
| PTD-05 | Cyclic Import | run_benchmark.py | benchmark_auto → lifecycle_hooks → delegate_runner (×2) |
| PTD-06 | Unreachable | run_benchmark.py:200 | Intentionally unreachable (type-checker guard) — akzeptiert |
| PTD-07 | Arguments | utils/providers/cohere.py:386 | arguments-differ in _extract_reasoning_tokens |
| PTD-08 | Indentation | scripts/dev/audit_model_cards_full.py:82 | Bad indentation (16 statt 12 spaces) |
| PTD-09 | Complexity | utils/base_runner.py:196 | 7 positional args (Limit 5) |
| PTD-10 | Complexity | utils/providers/base.py:339,447 | 6/9 positional args |
| PTD-11 | Style | 7 Dateien | Trailing newlines |
| PTD-12 | Simplify | utils/model_card_io.py:351 | Unnecessary set comprehension |
| PTD-13 | Simplify | utils/similarity.py:16 | Simplifiable if-statement |

---

## 8. load_dotenv() Audit

| Datei | Zeile | Risiko | Bewertung |
|---|---|---|---|
| utils/config_validator.py | 18 | 🔴 HIGH | Modul-level → jeder Import lädt .env. Bekannte Flaky-Test-Quelle (AGENTS.md 2026-09-25) |
| scripts/core/benchmark_auto.py | 43 | 🟡 MEDIUM | Hat No-Op-Fallback-Stub, aber importiert trotzdem |
| scripts/tools/list_models.py | 40 | 🟢 LOW | Nur Tool-Script, kein Test-Impact |

---

## 9. Nicht auditierte Bereiche (Folgepass nötig)

- **Provider (7/14 Connectors):** mistral, google, xai, cohere, openrouter, ollama, llamacpp (3), vllm (2)
- **Judge-Internal:** State-Reuse, Blind-Evaluation-Verifikation (get_model_identity)
- **Config-Parsing:** `enabled: false`-Duplikate, Bare `models:` Keys
- **Magic Numbers:** Vollständiger Scan (Hardcoded Thresholds, Timeouts, Limits)
- **Testing-Tiefe:** Flaky-Tests, Live-Endpoints, State-Leaks
- **Dependency-CVEs:** requirements.txt Audit
- **Performance-Tiefe:** Memory-Profile, N+1-CSV-Reads

---

## 10. Maßnahmenkatalog (priorisiert)

### Sofort (Critical — Bugfix)
1. **CRIT-01** Anthropic reasoning_tokens Fix (`anthropic.py:303-306`)
2. **CRIT-02** Groq Streaming Fix (stream_options, guard, finish_reason)

### Kurzfristig (High — Woche 1)
3. **HIGH-01** lifecycle_hooks.py Card-Lookup via _find_card
4. **HIGH-02** delegate_runner.py via _safe_name
5. **HIGH-04** # noqa: C901 entfernen — Refactoring (2 Dateien)
6. **HIGH-C01** OpenAI is_accessible Exception-Typen
7. **HIGH-C02** Probe-Client close() in OpenAI/Groq
8. **HIGH-C03** Groq max_retries=0

### Mittelfristig (Medium — Woche 2)
9. **MED-01..04** SSoT-Bypasses (base_test, political_compass, recompute, CARD_DIR)
10. **HIGH-03** unified_runner.py Splitting (PC-Helfer extrahieren)
11. **MED-05..06** Anti-God-Script (benchmark_auto, base_runner concern-mix)
12. **MED-C01** Commercial close()-Overrides
13. **MED-08** Shell=True Audit (Injection-Prüfung)
14. **MED-07** Docs: sk-local-mg2026 rotieren/ersetzen
15. **PTD-01..05** Cyclic-Import-Analyse (echte Probleme vs. Pylint-FPs)
16. **CQ-01..08** Pylint-C-Level-Korrekturen (line-too-long, imports, docstrings)

### Langfristig (Low — Backlog)
17. **INFO-01** Leaderboard-Update im Benchmark-Loop (technische Schuld, dokumentiert)
18. **INFO-02** Judge-Docstring korrigieren
19. **LOW-01..03, P01** Kosmetik (Logger-F-Strings, missing-docstrings, line-length)
20. **PTD-07..13** Pylint-Einzelfälle (cohere signature, indentation, simplifications)

---

## 11. Bugfix-Arbeitsplan

### Sprint 1: Provider-Critical-Fixes (CRIT-01, CRIT-02)
**Geschätzt:** ~2h
1. `anthropic.py`: `_apply_anthropic_message_delta` — `output_tokens_details` ins Merge-Dict
2. `groq.py`: `stream_options`, `choices[0]`-Guard, `finish_reason`-Extraktion
3. Tests: `test_anthropic_stream_usage.py` ergänzen (reasoning_tokens-Assert), Groq-Streaming-Test

### Sprint 2: SSoT-Bereinigung (HIGH-01..02, MED-01..04)
**Geschätzt:** ~3h
1. `lifecycle_hooks.py`: `_find_card()`-Migration
2. `delegate_runner.py`: `_safe_name()`-Migration
3. `base_test.py`, `political_compass`: `_safe_name()`-Migration
4. 7 Dateien: `CARD_DIR`-Import
5. `recompute_pc_v31.py`: `_safe_name()`-Import

### Sprint 3: Provider-Fixes (HIGH-C01..C03, MED-C01)
**Geschätzt:** ~2h
1. `openai.py`: Exception-Typen in `is_accessible()`
2. `openai.py`, `groq.py`: `check_client.close()` in `is_accessible()`
3. `groq.py`: `max_retries=0`
4. Optional: `close()`-Overrides in allen kommerziellen Connectoren

### Sprint 4: Architektur-Refactoring (HIGH-03..04, MED-05..06)
**Geschätzt:** ~6h
1. `noqa: C901`-Refactoring in political_compass/test.py + create_model_card.py
2. `unified_runner.py`: PC-Helfer in `pc_skip_resolver.py` extrahieren
3. `benchmark_auto.py`: Skip-Logik auslagern
4. `base_runner.py`: `_check_pc_leaderboard_skip`-Callback

### Sprint 5: Code-Qualität & Pylint (CQ-01..08, PTD-07..13)
**Geschätzt:** ~4h
1. Line-too-long-Korrekturen (model_id.py, base_runner.py)
2. Import-Order, Import-outside-toplevel
3. Docstrings in text_helpers.py
4. Pylint-Einzelfälle (cohere signature, indentation, simplifications)

### Sprint 6: Follow-Up-Audit (nicht auditierte Bereiche)
**Geschätzt:** ~4h
1. 7 Connector-Audit (mistral, google, xai, cohere, openrouter, ollama, llamacpp/vllm)
2. Judge-Internal-Audit
3. Magic-Numbers-Scan
4. Dependency-CVEs
5. Performance-Tiefe

---

*Protokoll wird nach Abschluss der noch laufenden Agenten (Phase 2, 5+6, 7+8) aktualisiert.*

---

## 5. Testing-Qualität (Phase 5, Teilbefund)

### A1. Live-Endpoint-Risiken in Tests

#### TEST-04: ConfigValidator mit realem Config-Pfad (import-triggered load_dotenv)
- **Datei:** `tests/test_config_thinking_expansion.py:377, 411`
- **Schweregrad:** 🟡 Medium
- **Verstoß:** `ConfigValidator(config_path=...)` wird instanziiert. Modul-Import `utils/config_validator.py:15-18` führt `load_dotenv()` aus → echte API-Keys aus `.env` in `os.environ`.
- **Risiko:** Bei Judge/LLM-Pfad-Auslösung: Live-Calls. Entspricht dem AGENTS.md-Trap (2026-09-25).
- **Fix:** Monkeypatch wie in `test_llamacpp_provider_separation.py:1004` (_FakeValidator).

#### TEST-05: vLLM Spark Test umgeht init, aber import triggert load_dotenv
- **Datei:** `tests/test_vllm_spark_provider.py:1052-1068`
- **Schweregrad:** 🟢 Low
- **Kontext:** `ConfigValidator.__new__` umgeht `__init__`, aber Modul-Import lädt trotzdem `.env`.

#### PASS: Korrekt gepatched
- `test_run_benchmark_delegate.py:42`, `test_pipeline_integration.py:15`, `test_run_political_compass_benchmark.py:30`, `test_run_score_benchmark.py:40`, `test_verify_compass_persistence.py:73` — alle patchen ConfigValidator vor Instanziierung.

### A2. Conditional-Skip-Tests

#### TEST-06: Web-Export Skip bei fehlendem Directory
- **Dateien:** `tests/test_web_export_field_coverage.py:46`, `tests/test_web_export_card_field_coverage.py:344,347`
- **Schweregrad:** 🟡 Medium
- **Verstoß:** `pytest.skip("Web-Export noch nicht erstellt")` bei fehlendem Glob-Match. Pattern aus 2026-09-25: Coverage kann still sterben, wenn Export unter anderem Slug liegt.
- **Status für field_coverage:** `_resolve_haiku_export_dir` wurde bereits fixiert (Glob statt Slug). Skip nur noch bei komplett fehlendem Export — akzeptabel.
- **Status für card_field_coverage:** Prüft `outputs/web_export_check/raw/models/` — fragil.

#### TEST-07: Skip auf Directory-Existenz
- **Datei:** `tests/test_id_ssot_invariants.py:203`
- **Schweregrad:** 🟢 Low
- **Verstoß:** `pytest.skip("outputs/audit_logs/ existiert nicht")`. Tests werden in CI ohne Audit-Logs nicht laufen.
- **Fix:** Fixture mit Temp-Dir statt Skip.

#### TEST-08: Module-Level Skip auf ImportError
- **Dateien:** `test_sanitize_tooluse_consistency.py:27`, `test_clean_results_arch_coverage.py:28`, `test_size_class_taxonomy_ssot.py:158`
- **Schweregrad:** 🟢 Low
- **Verstoß:** `pytest.skip(allow_module_level=True)` versteckt Refactoring-Brüche still.
- **Fix:** Mindestens loggen, dass ein Modul nicht importierbar ist.

### A3. Flaky-Test-Kandidaten

#### TEST-09: Timing-basierte Tests
- **Dateien:** `test_unified_runner_heartbeat.py:88`, `test_reasoning_loop_guard.py:110,129`, `test_migrate_architecture_tags.py:103`
- **Schweregrad:** 🟢 Low
- **Verstoß:** `time.sleep(0.005-0.01)` ohne Patch — Grenzwertig flaky auf überlasteten Systemen.
- **Alle anderen 19 time.sleep-Vorkommen:** korrekt gepatched.

### A4–A5 (Mock-Qualität, Isolation, Order-Dependencies) — nicht auditiert
- os.environ-Mutationen, random.seed, autouse-Fixtures, order-dependencies: nicht scanbar wegen Step-Limit.

---

## 6. Error-Handling (Phase 6, Teilbefund)

### B6. Bare Except — PASS ✅
Kein bare `except:` in der gesamten Codebasis gefunden.

### B7. Overbreadth Exception-Handling

#### ERR-01: Exception-schluckendes Tuple
- **Datei:** `utils/pricing_updater.py:237`
- **Schweregrad:** 🟡 Medium
- **Verstoß:** `except (URLError, OSError, Exception)` — `Exception` an letzter Stelle macht die spezifischen Typen wirkungslos. TypeError/KeyError werden als "Warning" geloggt statt zu crashen.
- **Fix:** `except (URLError, OSError)`.

#### ERR-02: Broad `except Exception:` (29+ Stellen)
- **Dateien (Auswahl):**
  - **Connectors:** `utils/providers/groq.py:220`, `mistral.py:159`, `openrouter.py:408`, `base.py:880,973`, `anthropic.py:161,223`, `xai.py:220`, `google.py:262`
  - **Utils:** `utils/provider_selector.py:274,340`, `benchmark_utils.py:660`, `export/tooluse_context.py:73,85,126,224`, `system_context.py:11`, `logging_config.py:26`, `ollama_config.py:33,54,79`, `model_version.py:76`, `cost_tracker.py:128`, `model_id.py:204,238,316`, `model_card_io.py:700,769`, `io_helpers.py:49,78,104`, `model_id_base.py:570`
- **Schweregrad:** 🟡 Medium
- **Bewertung:** Viele sind intentional tolerant (Config-Fallbacks, Parse-Toleranz), aber einige könnten echte Programmierfehler verschleiern.
- **Priorität:** Connector-Excepts zuerst prüfen (parsing/closing vs. swallowing).

### B8. Exception Swallowing (except-pass)

#### ERR-03: Passives Exception-Swallowing (kein Log, kein Re-Raise)
- **Dateien:** `utils/provider_selector.py:274-275,340-341`, `utils/benchmark_utils.py:660-661`, `utils/export/tooluse_context.py:73-74,126-127`, `scripts/core/run_cross_model_benchmark.py:345-346`, `scripts/analysis/generate_review.py:141,198,254,607,1234`, `scripts/leaderboard/exporter.py:121-122`, `scripts/analysis/review/risk_calculator.py:110, metrics.py:54`
- **Schweregrad:** 🟡 Medium
- **Fix:** Mindestens `logger.debug/warning` hinzufügen oder re-raise.

#### ERR-04: Debug-Level-Swallow (Card-Fehler unsichtbar)
- **Datei:** `utils/model_token_budget.py:271-273,310-312,335-337`
- **Schweregrad:** 🟡 Medium
- **Verstoß:** Card-Read-Errors nur auf DEBUG geloggt, Rückgabe `None`/`False`. Korrupte Kalibrierungsdaten verschwinden still.
- **Fix:** `logger.warning` statt `logger.debug`.

### B9–B10 (Retry-Konsistenz, Streaming-Robustheit, Fast-Fail) — nicht auditiert
Geplant: Review `_execute_with_token_fallback()`, Provider-Streaming-Pfade, 402/insufficient_quota.

---

## Offene Bereiche (aus beiden Phasen)

**Testing:**
- 28 Test-Dateien unter `benchmark_modules/*/tests/` nicht auf Live-Judge-Calls geprüft
- Mock-Qualität, os.environ-Mutationen, random.seed, autouse-Fixtures, Order-Dependencies

**Error-Handling:**
- B8-B10: Retry-Logik-Konsistenz, Streaming-Pfad-Robustheit, 402/Quota-Fast-Fail

---

---

## 7. Config-Driven Design (Phase 7, Teilbefund)

### A1. Magic Numbers — Hardcoded Values

#### MAGIC-01: Ollama Reasoning-Boost hardcodiert
- **Datei:** `utils/providers/ollama.py:69-71`
- **Schweregrad:** 🟠 High
- **Verstoß:** `num_predict = 8192`, `num_ctx = 8192` — Business-Regel ("Reasoning-Modelle → Boost gegen Memory-Freezes") hardcodiert im Connector.
- **Fix:** In `provider_config.yaml` oder `benchmark_config.yaml` auslagern.

#### MAGIC-02: Rate-Limit-Retries hardcodiert
- **Datei:** `utils/providers/base.py:367`
- **Schweregrad:** 🟠 High
- **Verstoß:** `max_rate_limit_retries = 3` inline. Keine Config-Referenz.
- **Fix:** Über `benchmark_config.yaml#rate_limits` oder `provider_config.yaml` steuern.

#### MAGIC-03: Backoff-Parameter hardcodiert
- **Datei:** `utils/retry_handler.py:96`
- **Schweregrad:** 🟠 High
- **Verstoß:** `wait_time = min(60 * (2 ** attempt), 600)` — base_delay=60, cap=600. Nicht config-gesteuert.
- **Fix:** `config/rate_limits.yaml` auslesen.

#### MAGIC-04: Ollama Default-Werte mehrfach dupliziert
- **Dateien:** `utils/ollama_config.py:17,31,36,101,112`, `utils/providers/ollama.py:176`
- **Schweregrad:** 🟡 Medium
- **Verstoß:** 4096/8192/32768-Defaults mehrfach im Code (`# Absoluter Fallback 8192`).
- **Fix:** SSoT-Quelle in Config definieren, einmal referenzieren.

#### MAGIC-05: Token-Budget-Konstanten
- **Dateien:** `utils/constants.py:20` (`MAX_TOKENS_ANTHROPIC = 8192`), `utils/scoring/llm_judge/judge_config.py:27` (`DEFAULT_MAX_TOKENS = 4096`), `utils/model_thinking.py:47` (`_PROBE_MAX_TOKENS = 4096`)
- **Schweregrad:** 🟡 Medium
- **Verstoß:** Zentrale Konstanten statt Config-Referenzen.
- **Fix:** Entweder als bewusste Kernel-Konstanten dokumentieren oder in Config migrieren.

#### MAGIC-06: Hardcodierte CSV-Daten
- **Datei:** `scripts/maintenance/backfill_tooluse_csv_rows.py:208`
- **Schweregrad:** 🟡 Medium
- **Verstoß:** `"token_limit_used": "4096.0"` als Datenwert in CSV-Zeilen geschrieben.
- **Risiko:** Backfill produziert historisch inkonsistente Daten bei Config-Änderung.
- **Fix:** Aus Config lesen oder als "unknown" markieren.

#### MAGIC-07: Server-Probe-Timeout hardcodiert
- **Dateien:** `openrouter.py:97` (10s), `llamacpp_base.py:275,350,828` (3, 3, 5s), `vllm_base.py:396,449,534,686` (10, 15, 10, 10s)
- **Schweregrad:** 🟡 Medium
- **Verstoß:** `httpx.Client(timeout=10.0)` und diverse Poll-Timeout-Werte hardcodiert.
- **Fix:** `server_probe_timeouts`-Block in `provider_config.yaml`.

#### MAGIC-08: Pause/Sleep-Werte
- **Dateien:** `run_score_benchmark.py:174` (3s), `verify_compass_anomalies.py:150` (5s), `run_tooluse_benchmark.py:256` (5s), `card_research/common.py:935` (1s)
- **Schweregrad:** 🟡 Medium
- **Fix:** In `benchmark_config.yaml#runner_environment` aufnehmen.

### A2. Config-Hierarchie — nicht auditierbar
### A3. Config-Validator — nicht auditierbar
### A4. benchmark_config.yaml SSoT-Sections — nicht auditierbar
(Step-Limit erreicht — Folgepass nötig)

---

## 8. Pylint-Technische-Schulden (Phase 8, Teilbefund)

### PTD-06: Unreachable Code — bestätigt, benign
- **Datei:** `run_benchmark.py:200`
- **Kontext:** `return provider, model_id` nach `sys.exit(1)` — "keeps type-checkers quiet".
- **Bewertung:** Intentional. `# pylint: disable=unreachable` setzen oder mit `raise SystemExit(1)` (mypy erkennt NoReturn) umschreiben.

### PTD-12/13: Simplifiable-Code — bestätigt
- **Datei:** `utils/similarity.py:16-19`
- **Verstoß:** `if importlib.util.find_spec(...) is not None: HAS_TRANSFORMERS = True else: HAS_TRANSFORMERS = False`
- **Fix:** `HAS_TRANSFORMERS = importlib.util.find_spec(...) is not None`
- **Schweregrad:** 🟢 Low

### PTD-01..05: Cyclic Imports — Teilevidenz
- **Signal:** `run_benchmark.py` verwendet function-local imports zum Brechen von Zyklen (`from utils.model_utils import resolve_canonical_model_id` bei :178, `PoliticalCompassHandler` bei :501, reimports von `json/subprocess/sys` in `_check_for_anomaly` bei :482-484).
- **Bewertung:** Die App startet nachweislich (1913 Tests passed). Zyklen sind eher order-abhängige latente Risiken als aktive Failures. Pylint-Cyclic-Import-Run + Cold-Import-Test empfohlen.

### PTD-07: Cohere arguments-differ — nicht auditierbar
### PTD-08: Bad Indentation — nicht auditierbar
(Step-Limit)

---

## Angepasster Maßnahmenkatalog (erweitert)

### Neue High-Priority-Befunde (aus Phase 7)

| ID | Bereich | Beschreibung | Aufwand |
|---|---|---|---|
| MAGIC-01 | Config | Ollama Reasoning-Boost (8192) hardcodiert | ~30min |
| MAGIC-02 | Config | Rate-Limit-Retries=3 hardcodiert | ~15min |
| MAGIC-03 | Config | Backoff 60/600 hardcodiert | ~20min |

### Neue Medium-Priority-Befunde

| ID | Bereich | Beschreibung | Aufwand |
|---|---|---|---|
| MAGIC-04 | Config | Ollama Default-Werte dupliziert | ~1h |
| MAGIC-05 | Config | Token-Budget-Konstanten | ~30min |
| MAGIC-06 | Config | Backfill-CSV hardcodierte Daten | ~15min |
| MAGIC-07 | Config | Server-Probe-Timeouts | ~45min |
| MAGIC-08 | Config | Pause/Sleep-Werte | ~30min |

---

## Angepasster Bugfix-Arbeitsplan

### Sprint 1: Provider-Critical-Fixes (CRIT-01, CRIT-02)
**Geschätzt:** ~2h
- anthropic.py: reasoning_tokens-Fix + output_tokens_details-Merge
- groq.py: stream_options, choices-Guard, finish_reason

### Sprint 2: Config-Magic-Numbers (MAGIC-01..03)
**Geschätzt:** ~1.5h — **NEU**
- ollama.py: 8192-Boost in Config
- base.py: max_rate_limit_retries aus Config
- retry_handler.py: Backoff-Parameter aus Config

### Sprint 3: SSoT-Bereinigung (HIGH-01..02, MED-01..04)
**Geschätzt:** ~3h
- lifecycle_hooks, delegate_runner, base_test, political_compass, CARD_DIR-Migration

### Sprint 4: Provider-Fixes (HIGH-C01..C03, MED-C01)
**Geschätzt:** ~2h
- OpenAI is_accessible Exception-Typen
- Probe-Client close(), Groq max_retries=0
- Commercial close()-Overrides

### Sprint 5: Architektur-Refactoring (HIGH-03..04, MED-05..06)
**Geschätzt:** ~6h
- noqa: C901-Refactoring (2 Dateien)
- unified_runner.py: PC-Helfer extrahieren
- benchmark_auto.py: Skip-Logik auslagern

### Sprint 6: Code-Qualität + Error-Handling
**Geschätzt:** ~4h
- Pylint C-Level (line-too-long, imports)
- Exception-Swallowing (ERR-01..04)
- Pylint-Einzelfälle (cohere, indentation)

### Sprint 7: Folge-Audit (nicht auditierte Bereiche)
**Geschätzt:** ~4h
- 7 Connectors (mistral, google, xai, cohere, openrouter, ollama, llamacpp/vllm)
- Config-Validator-Vollständigkeit
- Benchmark-Config-SSoT-Sections
- Cyclic-Import-Analyse
- Dependency-CVEs

---

---

## 2. Code-Qualität & Style (Phase 2)

### 2.1 Type Hints — Fehlende Annotationen

#### CQ-09: base_runner.py — 12 Methoden ohne vollständige Type Hints
- **Datei:** `utils/base_runner.py`
- **Schweregrad:** 🟡 Medium
| Line | Methode | Mangel |
|---|---|---|
| 27 | `__init__` | Fehlt `-> None` |
| 481 | `save_results` | Bare `list` statt `list[dict[str, Any]]` |
| 489 | `print_summary` | Bare `list` |
| 525 | `safe_float` (nested) | Keine Annotations |
| 561 | `_print_reference_comparison` | Bare `list`, fehlt `-> None` |
| 574 | `_print_best_worst` | Bare `list`, fehlt `-> None` |
| 590 | `_print_tiered_analysis` | Bare `list`, fehlt `-> None` |
| 613 | `execute_batch_module` | Bare `dict`/`list` |
| 680 | `_check_batch_cache_skip` | Bare `dict`/`list` |
| 755 | `_load_batch_test` | **Keine Return-Annotation** |
| 803 | `_run_batch_test` | Bare `dict`/`list` |
| 858 | `_finalize_batch_result` | Bare `dict`/`list` |

#### CQ-10: Weitere Annotation-Lücken
- **Datei:** `utils/config_validator.py:39` — `__init__` fehlt `-> None`
- **Datei:** `utils/result_manager.py:47` — `__init__` fehlt `-> None`
- **Datei:** `utils/result_manager.py:453` — `update_leaderboard` fehlt Return-Annotation
- **Nicht auditiert:** `unified_runner.py` (1623 Z.), `benchmark_auto.py` (1136 Z.), `run_benchmark.py` (676 Z.), alle Connectors außer base.py

### 2.2 DRY-Verstöße

#### CQ-11: Duplizierte Budget-Injection (base_runner.py)
- **Datei:** `utils/base_runner.py:85-109` vs. `222-235`
- **Schweregrad:** 🟡 Medium
- **Verstoß:** Identischer Block `resolve_token_budget` + `test.execute(...)` im Non-Batch- und Batch-Pfad. Kommentar bei :818: "identisch zum Non-Batch-Pfad".
- **Fix:** In Shared-Helfer extrahieren.

#### CQ-12: Doppelt geloggte Fehler (result_manager.py)
- **Datei:** `utils/result_manager.py:286-287, 342-343, 407-408, 466-467`
- **Schweregrad:** 🟢 Low
- **Verstoß:** Gleicher Fehler zweimal geloggt (`logger.error("...%s", e)` + `logger.error("❌ ...", e)`).
- **Fix:** Nur einmal loggen.

#### CQ-13: Redundante Re-Imports (base_runner.py)
- **Datei:** `utils/base_runner.py:720, 769, 778`
- **Schweregrad:** 🟢 Low
- **Verstoß:** `from pathlib import Path` (Modul-Level bei :7), `import logging` (Modul-Level bei :6) — doppelt importiert.
- **Fix:** Entfernen.

### 2.3 Naming

#### CQ-14: Private API als öffentliche Schnittstelle
- **Datei:** `utils/model_utils.py:8-87` (`__all__`)
- **Schweregrad:** 🟢 Low
- **Kontext:** `__all__` exportiert ~15 underscore-prefixed-Funktionen (`_safe_name`, `_find_card`, `_card_path`). File-Kommentar :89 bestätigt externe Nutzung.
- **Fix:** Entweder public umbenennen oder Importe auf Submodule umleiten.

#### CQ-15: Dynamisches Attribut ohne __init__
- **Datei:** `utils/base_runner.py:840`
- **Schweregrad:** 🟢 Low
- **Verstoß:** `self.provider_quota_exhausted = True` nie in `__init__` initialisiert — Muster ähnlich AGENTS.md "undeclared attribute"-Pitfall.
- **Fix:** In `__init__` als `False` initialisieren.

#### CQ-16: Tippfehler
- **Datei:** `scripts/dev/create_model_card.py:179`
- **Verstoß:** "Hilfefunktionen" → "Hilfsfunktionen"
- **Schweregrad:** 🟢 Low

### 2.4 Docstrings

#### CQ-17: Fehlende Docstrings
- **Datei:** `utils/base_runner.py:561, 574, 590`
- **Schweregrad:** 🟢 Low
- **Verstoß:** `_print_reference_comparison`, `_print_best_worst`, `_print_tiered_analysis` ohne Docstring.
- **Fix:** Docstring ergänzen.

#### Positiv: ✅ config_validator.py, result_manager.py, providers/base.py — alle öffentlichen Methoden dokumentiert.

### 2.5 Complexity-Hotspots (auditierte Dateien)

| Datei | Methode | Zeilen | Risiko |
|---|---|---|---|
| `base.py:339` | `_execute_with_token_fallback` | ~82 | 🔴 Hoch (nested for+while+try/except, 4 decision branches) |
| `base.py:900` | `_maybe_run_last_resort_guarded` | ~99 | 🟡 Mittel (lineare Guards) |
| `base_runner.py:346` | `build_base_result` | ~100 | 🟢 Niedrig (flat Dict-Build) |
| `base_runner.py:45` | `execute_test_module` | ~90 | 🟡 Mittel (gemischte Branches) |
| `base_runner.py:489` | `print_summary` | ~65 | 🟡 Mittel (branch-dicht) |
| `config_validator.py:113` | `_expand_thinking_profiles` | ~79 | 🟢 Niedrig (nested loops + guards) |

### 2.6 PEP-8-Mängel

#### CQ-18: Fehlende Blank-Lines zwischen Methoden
- **Dateien:** `utils/providers/base.py` (6 Stellen), `utils/base_runner.py` (5 Stellen)
- **Schweregrad:** 🟢 Low
- **Fix:** Ruff auto-formatting `ruff format`.

### 2.7 Nicht auditierte Bereiche
- Type Hints in `unified_runner.py`, `benchmark_auto.py`, `run_benchmark.py`
- Connector-Docstrings (anthropic, openai, groq, xai, cohere, google, mistral, ollama, openrouter, llamacpp/vllm)
- `utils/model_*` Submodule (model_id_base, model_card_io, model_version, model_size_class, model_thinking)

---

## Finale Statistik (alle 8 Phasen)

| Schweregrad | Arch | CodeQ | Sec | Perf | Test | Err | Config | Pylint | **Summe** |
|---|---|---|---|---|---|---|---|---|---|
| 🔴 Critical | — | — | — | — | — | — | — | — | **2** |
| 🟠 High | 4 | — | 2 | 2 | — | — | 3 | — | **11** |
| 🟡 Medium | 6 | 3 | 3 | 1 | 4 | 5 | 5 | — | **27** |
| 🟢 Low | 3 | 8 | 2 | 1 | 4 | 1 | — | 2 | **21** |
| **Total** | **13** | **11** | **7** | **4** | **8** | **6** | **8** | **2** | **61** |

---

## Finaler Bugfix-Arbeitsplan (7 Sprints, ~25h)

### Sprint 1: Provider-Critical-Fixes (~2h) 🔴
| ID | Datei | Beschreibung |
|---|---|---|
| CRIT-01 | `anthropic.py:303-306` | reasoning_tokens-Fix: `output_tokens_details` ins Merge-Dict |
| CRIT-02 | `groq.py:145-186` | stream_options setzen, choices[0]-Guard, finish_reason extrahieren |

### Sprint 2: Config-Magic-Numbers (~1.5h) 🟠
| ID | Datei | Beschreibung |
|---|---|---|
| MAGIC-01 | `ollama.py:69-71` | 8192-Boost in Config auslagern |
| MAGIC-02 | `base.py:367` | max_rate_limit_retries aus Config |
| MAGIC-03 | `retry_handler.py:96` | Backoff 60/600 aus Config |

### Sprint 3: SSoT-Bereinigung (~3h) 🟠
| ID | Datei | Beschreibung |
|---|---|---|
| HIGH-01 | `lifecycle_hooks.py:72` | _find_card()-Migration |
| HIGH-02 | `delegate_runner.py:62,120` | _safe_name()-Migration |
| MED-01 | `base_test.py:175` | Slug-Bypass beheben |
| MED-02 | `political_compass/*` | _safe_name-Duplizierung beseitigen |
| MED-03 | 7 Dateien | CARD_DIR-Import |
| MED-04 | `recompute_pc_v31.py:59` | _safe_name-Import |

### Sprint 4: Provider-Fixes (~2h) 🟠
| ID | Datei | Beschreibung |
|---|---|---|
| HIGH-C01 | `openai.py:263-266` | is_accessible Exception-Typen |
| HIGH-C02 | `openai.py:256`, `groq.py:64` | check_client.close() |
| HIGH-C03 | `groq.py:51` | max_retries=0 |
| MED-C01 | Alle kommerziellen Connectors | close()-Overrides |

### Sprint 5: Architektur-Refactoring (~6h) 🟠
| ID | Datei | Beschreibung |
|---|---|---|
| HIGH-03 | `unified_runner.py` | PC-Helfer in pc_skip_resolver.py |
| HIGH-04 | `political_compass/test.py:828`, `create_model_card.py:179` | # noqa: C901 entfernen (Methoden-Splitting) |
| MED-05 | `benchmark_auto.py` | Skip-Logik auslagern |
| MED-06 | `base_runner.py:718` | _check_pc_leaderboard_skip als Callback |

### Sprint 6: Code-Qualität + Error-Handling (~4h) 🟡
| ID | Datei | Beschreibung |
|---|---|---|
| CQ-09..10 | `base_runner.py`, `config_validator.py`, `result_manager.py` | Type-Hints ergänzen |
| CQ-11 | `base_runner.py:85,222` | Budget-Injection-Duplikat extrahieren |
| ERR-01 | `pricing_updater.py:237` | Exception-Tuple reparieren |
| ERR-03 | 9+ Dateien | except-pass → logger.warning |
| ERR-04 | `model_token_budget.py:271` | DEBUG → WARNING |
| CQ-01..08 | `model_id.py`, `base_runner.py`, `scoring_utils.py` | Line-too-long, imports, docstrings |
| PTD-07..13 | `cohere.py`, `audit_model_cards_full.py`, etc. | Pylint-Einzelfälle |
| CQ-17 | `base_runner.py:561,574,590` | Fehlende Docstrings |

### Sprint 7: Folge-Audit (~4h) 🟡
| Bereich | Beschreibung |
|---|---|
| 7 Connectors | mistral, google, xai, cohere, openrouter, ollama, llamacpp/vllm (auditieren) |
| Config-Validator | Vollständigkeitsprüfung |
| benchmark_config.yaml | SSoT-Sections (token_budgets, scoring_tiers, runner_environment) |
| Cyclic-Imports | Pylint-Run + Cold-Import-Test (7 Zyklen) |
| Dependency-CVEs | requirements.txt-Review |
| Performance-Tiefe | Memory-Profile, N+1-CSV-Reads |
| Type Hints | unified_runner, benchmark_auto, run_benchmark, Connectors |

---

*Protokoll abgeschlossen am 2026-09-25, 643 → 797 Zeilen.*
