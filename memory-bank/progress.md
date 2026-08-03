# Progress
Letzte Releases + aktueller Stand.

### 2026-08-03 (Session 79) — Web-Export-Code-Review + 10 Architektur-Fixes [DONE]

Code-Review des `scripts/web_export/`-Packages gegen die Architekturregeln. 10 Befunde umgesetzt: (B1) `assert` vor `shutil.rmtree` → echter `if/raise` (Safety-Gate überlebt `python -O`); (B2) Monkeypatching-Mechanismus (`_sync_package_patches`/`_PATCHABLE_NAMES`) aus `__init__.py` entfernt — Tests patchen jetzt direkt auf dem Submodul; (B3) `_ROOT_DIR`-Redefinition entfernt (war durch file-level `F401`-noqa verborgen); (B4) Magic-String `"__fallbacks__"` → `ProviderMap`-NamedTuple; (B5) 4× breite `except Exception`/`suppress(Exception)` → konkrete `(OSError, ValueError, yaml.YAMLError)`; (B6) duplizierte Pending-Sentinels → SSoT `normalize_pending()` (schließt En-Dash-Lücke); (B7) sys.path-Bootstrap von 6 Modulen → 1 zentrale Stelle; (B8) `__all__` explizit; (B9) `_build_model_card_subdict` aus `_build_leaderboard_entry` ausgelagert (SRP); (B10) file-level `F401`-noqa aus `main.py` entfernt (deckte 3 tote Imports). Test-Laufzeit 80s→0.6s (Mock-Fix aus B2). AGENTS.md um file-level-F401-Verbot ergänzt.

---

### 2026-08-03 (Session 78) — vLLM-Connector CC-Refactoring [DONE] v5.1.2

Verhaltenserhaltendes Refactoring von `utils/providers/vllm_base.py`. Die als unverhandelbar deklarierte CC-≤-12-Regel wurde über zwei `# noqa: C901`-Annotationen umgangen (start_server CC=19, query CC=16). Drei Maßnahmen: (1) `start_server` in Dispatch-Shell + 9 Pfad-Methoden zerlegt (CC→8), (2) `query`-Streaming in `_consume_stream` ausgelagert (CC→7), (3) Reasoning-Fallback in `_apply_reasoning_fallback` dedupliziert (DRY). Keine `noqa` mehr. 115 Tests grün (78 vLLM + 37 Thinking/Config). AGENTS.md um noqa-Verbot ergänzt. Versionssynchro v5.1.2 über 7 Stellen (fixt auch v5.1.1-Drift in AGENTS.md/PROJECT_STATUS.md/REF_TODO.md).

---

### 2026-08-03 (Session 77) — Vollständiger Doku-Audit + list_models Bugfix [DONE]

**Bugfix:** `scripts/tools/list_models.py` hatte duplikaten `check_commercial()`-Aufruf (Zeile 319), führte zu 5+ Min Timeout bei API-Pings. Entfernt.

**Doku-Audit:** 15 Files in 3 thematischen Commits gefixt. Stichproben:
- `docs/SETUP_GUIDE.md`: Python 3.10 → 3.12, Module-Key `coding` → `code_quality` (existiert nicht)
- `docs/PRICING_REVIEW.md`: Duplikate Qwen 3.7 Max-Zeile entfernt
- `docs/MCP_LOCAL_SERVER.md`: Lowercase Path → `CrucibleMark` (Case-Sensitive-FS-Robustheit)
- `docs/SCORING_METHODOLOGY_WEB.md`: Modul-Display-Namen korrigiert (Tool Execution → Tool Use & Assistenz, CLI Badge → CLI Operations)
- 4 drift Doku-Stempel sync (4.10.17 → 5.1.0): ARCHITECTURE, BACKUP_STRATEGY, DEVELOPER_GUIDE, MODEL_CLASSIFICATION
- `CHANGELOG.md`: v5.1.1 Sektion (Sessions 71–76) hinzugefügt
- `AGENTS.md`: Quick Commands ergänzt (validate-naming, validate-csv, tooluse-leaderboard, mcp-start/stop, docs-version-check/sync)
- `memory-bank/reference/_index.md`: Neue Files `feedback_schema.md` und `tooluse_module.md` indiziert
- `.agent/web-export-cleanup.md`: Political Bias entfernt (9 Spalten statt 10), Pfad `scripts/legacy/` statt `scripts/maintenance/`
- `.agent/provider-models.md`: `utils/card_template.py` (Datei) statt Verzeichnis
- `.agent/data-pipeline.md`: Hartcodierte Zeilennummern durch Dateinamen ersetzt
- `README.md`: Badge v5.1.1, Python 3.12, v5.1.1 Section, Status aktualisiert

`make docs-version-check`: 0 drift (vorher 4).

---

### 2026-08-02 (Session 76) — Naming-Validator + Card-Bereinigung [DONE]

Automatisierter Naming-Validator (`scripts/analysis/validate_naming.py`) erstellt: prüft 11 display_name + 7 model_version Forbidden-Patterns. Als Publication-Gate integriert: `make web-export` hard-gate (exit 1), `make web-export-dev` warn-only. 7 vLLM/NVFP4 display_name-Korrekturen + 10 model_version-Korrekturen + 4 Cloud/Groq model_version-Fixes. `ornith-1_0-35B-FP8` display_name bereinigt. Konventionen in `memory-bank/reference/data-schema.md` als SSoT dokumentiert. Web-Export rebuilt: 96 Models, 0 Fehler. `validate-naming` Makefile-Target + `.kilo/command/card-cleanup.md` aktualisiert.

---

### 2026-08-02 (Session 75) — Hermes 4.3 36B Card-Verifikation [DONE]

Hermes 4.3 36B Model Card verifiziert (`card_status: "complete"`, `profile_verified: true`). `context_window_k` korrigiert: 32 → 512 (512K nativer Kontext laut HF-Card). activeContext.md auf Session 75 aktualisiert.

---

### 2026-08-02 (Session 74) — Laguna S 2.1 Benchmark abgeschlossen [DONE]

**Benchmark-Run:** 50 Standard-Profile + 43 Thinking-Profile Audit-Logs (31.07.2026, asus_gx10_blackwell, vllm_spark). Leaderboard: Rank 92, Score 69.1%, Silver Badge, 49/49 Tests completed (100% coverage). ToolUse: P1=78.33, P2=33.33. Politischer Kompass: Progressiv-Autoritär (-5.12, 3.36), "Wolf im Schafspelz".

**Card-Updates:** `card_status: "complete"`, `profile_verified: true`. `judge_context_hint` aktualisiert auf selektives Reasoning.

**Dual-Profile-Anomalie aufgeklärt:** Thinking-Profile lief parallel zum Standard-Profil, obwohl `enable_thinking: true` aus `provider_config.yaml` entfernt wurde. Erklärung: Laguna wählt selbst, wann thinking/nonthinking genutzt wird (selektives Reasoning). TOML-Parameter steuert nur, ob thinking *erlaubt* ist — die Entscheidung trifft das Modell intern.

---

### 2026-07-31 (Session 73) — Laguna S 2.1: Selektives Reasoning, Dual-Profile entfernt [DONE]

Laguna S 2.1 als selektives Reasoning-Modell identifiziert (HF Discussion #13: "thinks when needed", nicht Always-Thinking wie Qwen3.6). `enable_thinking: true` aus `provider_config.yaml` entfernt → keine Dual-Profile-Expansion mehr. `dual_profile` in Card auf `null`. Alle Laguna-CSV-Einträge aus 4 CSVs entfernt (65 Zeilen). `add-model`-Skill um Modell-Klassen-Tabelle ergänzt. AGENTS.md + systemPatterns.md um Fallstrick ergänzt. `reasoning_effort` darf NICHT gesendet werden (vLLM 0.25.1 400-Fehler).

---

### 2026-07-30 (Session 72) — qwen3_6-27B → qwen3_6-27B-pre025 Historical Rename + ToolUse Timestamp-Bugfix [DONE]

**Rename:** Historische `qwen3_6-27B`-ID (capital B, vLLM vor 0.25.1) zu `qwen3_6-27B-pre025` umbenannt. CSV (99 Zeilen), Card (`git mv` + model_id + tooluse_runs), NVFP4-Card-Summary, Blacklist (`kept_overrides` → aktive `blacklist`), Audit-Logs (93 Dateien), Reviews, Runs-JSON, Test-Fixtures aktualisiert. 1553 Tests grün, Webexport erfolgreich (pre025 blacklisted, nvfp4 exportiert).

**Bugfix:** `tooluse_exporter.py:_write_card_from_aggregated_row` (Path B) überschrieb `tested_at` in 107 Cards mit `datetime.now()` bei jedem `make tooluse-leaderboard`-Lauf. Fix: existierenden Card-Wert bewahren.

---

### 2026-07-29 (Session 71) — vLLM-Connector Thinking-Profile-Adoption-Fix [DONE] (committed `fd386047`)

Benchmark-Abbruch beim Auswählen des Thinking-Profils behoben. Zwei gekoppelte Bugs in `vllm_base.py`: `_adopt_matches()` scheiterte an MoE-Notation (`a3b`, `thinking`) im ID-Segment; Post-Stop-Verifikation interpretierte Proxy-502 als `"loading"`. Fix: Config/TOML-Name-Match + `_backend_stopped()` mit SSH-Check. 120 Tests grün.

---

### 2026-07-28 (Session 69–70) — vLLM-Connector 502-Mehrdeutigkeits-Fix + Thinking-Trace-Verifikation [DONE] (committed `659f34e0`, `2b1a9321`)

**502-Fix:** Pfad 3.5 in `vllm_base.py:start_server()` wartete bei Proxy-502 600s ohne `vllm-start`-Aufruf. `_remote_chat_server_running()` (SSH `pgrep`) prüft Chat-Prozess-Existenz. 6 neue + 78 bestehende Tests grün.

**Thinking-Trace-Verifikation:** REASONING TRACE NOTE + `<think>`-Wrapping modellunabhängig verifiziert — 2 Modelle (Ornith 1.0 35B + qwen3.6-27B), 50+ Audit-Logs, kein einziger Think-Block-Penalty. ux_writing Re-Run: 4/5 erfolgreich, ux_writing_002 reproduzierbar trunciert (akzeptiert als modellseitige Known Limitation).

---

### 2026-07-19 (Session 67) — Web-Export-Verifikation [DONE]

92/92 Modelle in `web_export/raw/models/` — alle vermeintlich "fehlenden" Modelle waren Artefakt eines unvollständigen Vorlaufs.

---

### 2026-07-15 (Session 66) — Hermes 4.3 36B (Seed-OSS) Integration [DONE]

`provider_config.yaml`: Eintrag `hermes-4-3-36b` mit `config: Hermes4.3-36B`, `enable_thinking: true`. Model Card erstellt, strukturelle Felder manuell gefüllt (ByteDance/Seed-OSS, Nous Research Vendor, 36B Dense, BF16, vLLM, Apache-2.0, `dual_profile: true`). `card-research` erfolgreich.

**Benchmark-Runs (Sessions 66–74):**
- Thinking-Probe: `detected: true`, `confidence: medium`.
- Standard-Profil: Rank 98, Score 68.57%, Silver Badge, 100% Coverage.
- Thinking-Profil: Rank 103, Score 68.02%, Silver Badge, 100% Coverage.
- Political Compass: Standard (-5.67, 1.81), Thinking (-4.67, 2.93).
- ToolUse: Standard P1=90.0/P2=43.33, Thinking P1=90.0/P2=44.17.

---

### 2026-07-14 (Session 65) — v5.1 Incapable-Klassifikation-Fix [DONE] v5.1.0

Coverage-Malus greift jetzt korrekt bei Modellen, die komplette Module nicht durchlaufen haben. `supports_tool_use: false` wurde als "incapable" (exempt) klassifiziert, selbst wenn getestet (6 error-Rows). Fix: striktere Logik (`attempted_set` aus `df_all`) + Card-Korrekturen (Command A+, GPT-OSS 20B) + Evidence-Pflichtfeld für `false`-Cards. Command A+ fällt von Rank 62 auf 104. 1350 passed, 0 failed.

---

### 2026-07-13 (Session 63–64) — v5.0 Generalized Coverage Scoring + ToolUse Integration [DONE] (committed `5a330906`)

ToolUse als vollwertiges 8. Scoring-Modul integriert (`enable_scoring: true`, `module_weight: 1.0`). Coverage-Logik generalisiert: missing/unknown → Malus, incapable → exempt, rolling_out/not_deployed → für alle ausgeschlossen. Neue `coverage_ratio`-Spalte. Per-Modell `Tests Run` (incapable reduziert). Invariante `Routine + Reasoning = Total` erhalten. Code-Review (6 Sub-Agenten): Dead-Code wired, SSoT `_compute_module_scale_factors` extrahiert, `incapable_map` einmal berechnet, `clear_cards_cache()`. 1346 passed, 0 failed.

---

### 2026-07-13 (Session 61–62) — Baustellen-Reconciliation + PC-Nachhol-Verifikung [DONE]

Vier Baustellen aus Session-61-Zusammenfassung geschlossen: ungepushter Zustand (bereits clean), flaky ToolUse-Test (nicht reproduzierbar), PC-Lücken-Widerspruch (historisch korrigiert), 8 PC-Lücken als Known Limitation akzeptiert. Memory-Bank-Sync für neue PC-Einträge (Gemma-4-31B-Wordsmith-NVFP4, grok-4.20-0309-reasoning, kimi-k2.7-code, glm-5.2). 1320 passed, 0 failed.

---

### 2026-07-12 (Session 60) — WordSmith Gemma 4 Bias-Reviews + Web-Export-Audit [DONE] (committed v4.10.18)

WordSmith-NVFP4 Card-Fix (origin_country/developer_jurisdiction). 2 Bias-Reviews generiert. Bias-Review-Audit: 3 weitere Modelle ohne PC-Daten identifiziert (nicht code-seitig lösbar). Web-Export-Audit: Sentinel-Werte in `benchmark_cost` (Root-Cause: `_coerce_dataframe_metrics` coercete 12 Spalten nicht zu numeric → Fix). `card_id`-Konflikt für Gemma-4-31B-Wordsmith-NVFP4(-thinking) als by Design bestätigt.

---

### 2026-07-09–11 (Session 54–59) — Framework-Refactoring + Web-Export-Härtung [DONE] (committed v4.10.16–v4.10.18)

**Session 59 (v4.10.18):** Framework-Refactoring Sektion A–M. `model_utils.py` → 7 Submodule + Bridge. `web_export.py` → Package. 18× `yaml.safe_load` → `ConfigValidator`. 131× `print` → `logging`. 27 Legacy-Skripte nach `scripts/legacy/`. Ruff 252→0. 1316 passed.

**Session 58 (v4.10.16–17):** Web-Export Blacklist-Restructure (2-Sektion-Layout), Slug-SSoT (`model_id` statt `model_name`), `normalize_pending` Sentinel-Hardening, `leaderboard.json` Scores-Contract. `political_bias` Phantom-Key entfernt (10→9). Variantenbewusster `display_name`. 97 tests passed.

**Session 54–57:** `thinking_mode`-Spalte (CSV + Leaderboard + Audit-Log + Review-Prompt), Display-Name-Fix für Thinking-Profile, `-thinking`-Suffix-Fallback in Card-Lookup, Local-Model Price = 0.0 Defense-in-Depth.

---

### 2026-07-08–09 (Session 50–53) — vLLM-Thinking-Profile + Card-Naming-SSoT [DONE] (committed v4.10.14–15)

**Session 52–53:** vLLM Dual-Thinking-Profile Expansion (`_expand_thinking_profiles()`), `card_model_id`-Redirect, `-thinking`-Suffix-Fallback. Connector Wrapped Thinking (`<think>`-Tags an Judge).

**Session 50–51:** Baustellen-Cleanup (Sampling-vs-Card-Drift, vLLM-Extensions-Whitelist), Card-Naming SUFFIX-SSoT (`_card_path` → `build_card_id()`), `model_version`-Pollution-Migration (neues Feld `model_variant`). vLLM-Experiment-Status: llama.cpp primärer Backend.

---

### 2026-06-21–07-07 (Session 40–49) — Provider-Connector-SSoT + CSV-Hygiene + Card-System [DONE] (committed v4.10.4–v4.10.13)

**Session 49 (v4.10.13–14):** WebExport-Konsistenz-Fixes (ToolUse-Scores datenbasiert, Emoji-Variation-Selectors), Card-Naming SUFFIX-SSoT, `model_version`-Pollution-Migration.

**Session 47 (v4.10.13):** ToolUse Tri-State Export (Scores datenbasiert, Detail-Block gated).

**Session 40 (v4.10.8):** Doku-Stempel-Check + Drift-Refactor (`make docs-version-check`/`docs-version-sync`).

**v4.10.4–v4.10.7:** CSV-Write-Through Bug Fix (atomar), Token-Budget-Refactoring (`_resolve_request_tokens`), Provider-Connector Thinking/Reasoning-Fix, clean-results Variant-Handling, Anthropic Token-Cap 8192→32768.

**v4.10.0–v4.10.3:** Web-Export Nullwert-Entfernung (`_strip_none`), Card-Research Force-Run (110/110 Cards verified), Provider-Connector SSoT (`_extract_reasoning_tokens`, `ThinkAccumulator`), Judge Token Usage Context.

---

### 2026-05–06 (Session 16–39) — Card-Datenpflege + Thinking-SSoT + CSV-Hygiene [DONE] (committed v4.5.0–v4.9.3)

**v4.9.0–v4.9.3:** Card-Datenpflege-System (Vendor-Kanonisierung, `profile_verified`, Editor-Prompts), Vendor Card description-Feld.

**v4.7.0–v4.7.3:** 4-Phasen-Refactoring (Ruff 0, CC ≤ 12), Thinking-SSoT-Auflösung (`resolve_effective_thinking`), Web-Export-Blacklist, Thinking-Probe v2 (Multi-Prompt + Familien-Inventar).

**v4.6.0–v4.6.1:** CSV-Hygiene Defense-in-Depth (Sanitizer entfernt 13.466 Müll-Zeilen, Hard-Fail-Guard, `make validate-csv`).

**v4.5.0:** ID-SSoT-Refactoring (`resolve_canonical_model_id()`, `enforce_card_first()`).

**v4.8.6:** Robustness-Fixes (Judge-Coverage, Draft-Card-Warning, ToolUse P1/P2 SSoT).

---

### 2026-04–05 (Session 1–15) — v1.0–v4.4.0: Kern-Architektur + Module + Provider [DONE]

Aufbau des Frameworks von Grund auf: LLM-Based Scoring System (v1.5), God-Script Dismantling (v2.6.2), Architecture Hardening & Anti-Censorship (v3.0.0), Language Compliance & Prompt Hardening (v3.3.0), Token-Budget-System (v3.4.0), ThinkingProbe & Card-First Workflow (v3.5.8), Tool Use Benchmark-Modul (v3.10.0), Modell-Kategorisierungs-SSoT (v3.7.0), Pricing SSoT Migration (v3.7.5), OpenRouter-Migration (v4.2.0), Pricing-Architektur-Bereinigung (v4.0.0), CSV Robustness & Leaderboard Pipeline Hardening (v4.4.0).

Siehe [CHANGELOG.md](../CHANGELOG.md) für vollständige Versionshistorie.
