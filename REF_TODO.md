# REF_TODO.md – Refactoring & Future Development

## Backlog (Phase 2)

- [ ] **`content_transformation_005` — Body-Word-Parser:** `keyword_presence`-Check für 300-Wort-Limit des Email-Bodys durch echten Wort-Count ersetzen. Benötigt Section-Parser der Analyse-Teil von Newsletter-Body trennt. Aufwand: ~30 LOC in `__init__.py` + Issue-Umstellung in `asset_005_newsletter_adaptation.yaml`. Risiko: Modelle formatieren Body uneinheitlich — falsche Penalties bei ~20% der Antworten möglich. Wert: 2.4 Pkt. Nicht zeitkritisch.

## Abgeschlossen

### PC v3.1 — Nano-/Mini-/Desktop-Testing + SPRK-Small-Model-Feld (v5.3.0 – 16.09.26, Sessions 99–105)
Political-Compass-Überarbeitung für kleine Modelle: Degenerate-Guard (API-Ausfall nicht mehr als (0,0)-Mittelpunkt persistiert), Schattenmetriken-Badges config-getrieben an Reviewer-σ-Konvention (`config.shadow_metrics`, σ < 1,5 stabil / σ > 2,0 Chaos), Truncation-Signal-Re-Probes nemotron-nano/mimo-pro (OpenRouter-`finish_reason` + Google-SAFETY-Masking-Fix), PC-Batch 04.–06.09. (`pc_profile`/`pc_token_calibration` in 16 Cards, 23 Bias-Reviews), SPRK-PC-Kalibrierung (r1-distill-1.5B 1560 `inconsistent`, Swift 390 `self_limiting`). Neues Small-Model-Feld: 14 Nano-/Mini-/Desktop-Modelle ≤ 16 GB auf llama.cpp Spark/GX10 (Unsloth-UD-Q5_K_M: Llama 3.2 1B/3B, Llama 3.3 8B, Phi-4 Mini, Ministral 3 3B/8B/14B, R1-Distill 1.5B/7B/14B, Gemma 3 270M/4B, Gemma 4 E2B, Ornith 1.0 9B) + Signal 3.8 27B; Vendor-Cards AgentionAI/UkisAI/Microsoft. Dazu Size-Class-SSoT `params_total_b` + Frontier-Grenze 768B (Migrationsskript, ~30 Cards reklassifiziert), Card-Writer-Newline-SSoT (58× normalisiert), Health-Gate-Fix für Remote-APIs, Web-Export-Dupletten-Konsolidierung (Gemma-4-12B, muse-glimmer) und Integrationen Occamy 1.0 35B-A3B, Swift-Qwen3.8 27B, DeepSeek V4.1 Flash.

### PC-Token-Probe Card-First-Hook (v5.2.2 – 03.09.26, Session 98)
Hat die Model Card keinen PC-Token-Probe-Eintrag (`pc_profile` fehlt/null), führt der PC-Benchmark-Runner die Probe jetzt automatisch vor dem PC-Run aus — analog Thinking-Probe vor dem Standard-Benchmark (vorher rein manuell `make probe-pc-budget`; neue Modelle wie `claude-opus-4-8` liefen ungeprüft am Default-Budget). Neues SSoT-Modul `benchmark_modules/political_compass/core/pc_probe_hook.py` (read_pc_probe_state / run_pc_token_probe / write_pc_calibration_to_card / ensure_pc_token_probe); Hook in `utils/base_runner.execute_batch_module()` nach den Skip-Checks, vor `_load_batch_test`, nur PC-Module (Batch-Pfad umgeht `_ensure_model_card` via Early-Return — daher eigener Hook). Trigger-Semantik wie Thinking-Probe (nur None/fehlt triggert); `PcProbeError` (Fast-Fail-Guard) → Runner lässt Benchmark weiterlaufen ohne Card-Write. `pc_calibrate.py` DRY-Refactor (Probe-Orchestrierung + Card-Write ausgelagert, tote Imports entfernt). 13 neue Tests, Suite 1722 grün, Lint exit 0. Live-Verifikation: `claude-opus-4-8` → Probe self_limiting @390 (thinking), PC-Hauptlauf Shift 1.61 („Wolf im Schafspelz", `is_retest: true`).

### Anthropic-Streaming-Fix & PC-Probe-Fast-Fail-Guard (v5.2.1 – 02.09.26, Session 97)
Anthropic-Streaming-Regression behoben (seit `60aad34c` fehlten im Streaming-Pfad `max_tokens` + `text_delta`-Branch → jeder Request fehlgeschlagen, Antworttext immer leer): Fixes in `utils/providers/anthropic.py` (max_tokens-Injektion, text_delta-Branch, tote no-op-Zeile entfernt). PC-Probe-Fast-Fail-Guard: >50 % Query-Fehler (kumulativ, `PC_PROBE_MAX_ERROR_RATE`) → `PcProbeError` → Abbruch ohne Card-Write (Incident: 9/9 Query-Fehler durch den Anthropic-Bug hatten eine falsche `greedy_uncapped`-Kalibrierung persistiert); `pc_calibrate.py` meldet + Exit 1, 4 neue Tests. Groq-Sektion nach clean-model-Löschung neu besetzt (`qwen/qwen3.6-27b`, `qwen/qwen3.8-27b` API-verifiziert, `enabled: false`), Blacklist-Hygiene (GPT-OSS-120B-Eintrag entfernt). Kommerzieller Anthropic-Test claude-sonnet-5: Probe self_limiting @390 (thinking), PC-Hauptlauf Shift 1.35 (stabile Linksdrift, „Wolf im Schafspelz", 79/79 direkte Antworten). Test-Fix: stale `qwen/qwen3-32b`-Case in test_resolve_canonical_model_id.py (Card via clean-model gelöscht) → `qwen/qwen3.8-flash`. 1709 Tests grün, Lint 9.99/10, Naming 131 Cards OK.

### Provider-Härtung & Abbruch-Cleanliness (v5.2.0 – 31.08.26, Sessions 90–93)
llama.cpp Mac/Spark-Separation (Cache, Routing, Endpoint-Ownership) + GX10-Metrics-Proxy-Connector (Bearer-Probes, `server_port`-Override, Token via `DGX_AUTH_TOKEN` in `.env`, 401-Diagnose im Poll). Timeout-Livelock: Chat-Pfad liest `request_timeout` (nicht `read_timeout`) — beide Wände auf 2400 s. Thinking-only-Ausnahme + Leaderboard-Trigger pro Modul in allen Pfaden + Attribution-Mirror (PC-Ersatzlauf → Profil-ID). Web-Export: `resolve_inference_provider()` run-autoritativ per Provider-Code. Timeout-Metrik zählt nur echte Fehler. HTTP-Client-Close-Kette (`LLMClient.close` + `atexit`, vllm/llamacpp-Overrides): vLLM 0.27 nightly erkennt abgebrochene Requests ohne TCP FIN erst nach OS-Keepalive (~2 h). Modell-Hygiene: Gemma-4-31B + fable-fusion entfernt, Rationale-Feld-Migration (17 Cards). 1704 Tests grün, Lint 9.99/10.

### PC v3.0, Token-Probe & Thinking-only-Regel (v5.2.0 – 29.08.26, Session 88)
Political Compass v3.0 re-aktiviert: Token-Budget-Regime (Modul-Budget 800), Refusal/Truncation-Klassifikator, begrenzte Eskalations-Treppe, Token-Probe v2 mit Profil-Entscheidung (thinking/hybrid_dual/instruct, Card-First) und Ergebnis-Attribution für Instruct-Ersatzläufe (Original-ID, alle vier Persistenz-Pfade, Verifikations-Skip). Folge-Regel: Thinking-only-Ausnahme — Profil-Entscheidung via `dual_profile` gegatet (`probe_pc_profile(supports_instruct_mode=…)`, `read_dual_profile()`, Runtime-Guards in `political_compass/test.py`); nur Modelle mit beiden Betriebsmodi werden in beiden Modi getestet. Batch-Vorbereitung: PC-Einträge von 12 lokalen Modellen geräumt, Gemma-4-31B + qwen2_5-vl-7b aus der Config (Blacklist). Doku: Konzept-Doc Abschn. 11, ARCHITECTURE.md (Delegate-Modul-Tabelle, Probe-Fallback). 1528 Tests grün (+2), make lint exit 0.

### Echte-Token-Pipeline (v5.1.5 – 17.08.26, Session 84)
`tokens_per_second` wurde aus der Modul-Schätzung (Wörter × 1.3, ohne Thinking) berechnet, während `tokens_used` die echten Provider-Usage-Werte enthielt — zwei Spalten, zwei Token-Zahlen, bei Thinking-Modellen massiv unterbewertet. Fix: TPS = echte Output-Tokens (inkl. Thinking) / Wall-Time, neue CSV-Spalten `input_tokens`/`output_tokens` (selbstkonsistent: `tokens_used = input + output`), Judge-Context und Audit-Log mit echter Breakdown, Visible-Output-Formel fixt (`output_tokens − reasoning_tokens` statt `tokens_used − reasoning_tokens`, die alte Formel hätte Input-Tokens als sichtbaren Output gezählt). Provider lieferten bereits echte Usage (vLLM, OpenRouter, llama.cpp, Ollama) — keine Provider-Änderung. Doku-Sync: ARCHITECTURE.md (TPS-SSoT + TOKEN-USAGE-Block), DEVELOPER_GUIDE.md (Schema-Felder `input_tokens`/`output_tokens`), SCORING_METHODOLOGY.md + MODEL_CLASSIFICATION.md (Tokens/s-Semantik-Hinweis). 1572 Tests grün (+12 neue), Lint 0, Naming-Gate 123 Cards OK.

### Code-Review-Umsetzung (v5.1.4 – 15.08.26, Session 83)
Vollständige Umsetzung eines 23-Findings-Reviews: 5 kritische Fixes (Ollama-Loop-Break, lifecycle_hooks-Logging, combined_score-0.0-Fallback, doppelter probe_thinking-Key, Preis-Split-Bug mit neuer SSoT config/model_pricing.yaml), Shell-Injection-Flächen geschlossen, exponentieller Rate-Limit-Backoff, Judge-Prompt Name-Priming entfernt (Blind-Evaluierung), 8 C901-Verstöße verhaltenstreu aufgesplittet (audit_logger CC 67, Roundtrip-Diff byte-identisch), Ruff 409→0, DRY-Konsolidierung (utils/provider_config_text.py), ConfigValidator-mtime-Cache, Maintenance-Skripte gehärtet (--dry-run, Heuristik-Entschärfung). 1411 Tests grün, Naming-Gate 122 Cards OK.

### Test-Suite-Reparatur & Card-Vocabulary-Normalisierung (v5.1.3 – 15.08.26)
Drei vorbestehende Testfehler behoben: hermes-4-36b Orphan-Draft-Card via clean-model entfernt; Architecture-Tags gegen Vocabulary-SSoT normalisiert (Native-Quant/Harmony neu, Configurable-Reasoning/Thinking-Mandatory deprecated); Ornith-Test als llamacpp-Invariante für Re-Aktivierungen umgeschrieben. Maintenance-Fixes aus Sessions 74/75 (clean_provider_config, Sanitizer, probe_thinking) integriert. 1410 Tests grün.

### vLLM-Connector CC-Refactoring (v5.1.2 – 03.08.26, Session 78)

Verhaltenserhaltendes Refactoring von `utils/providers/vllm_base.py` — die als unverhandelbar deklarierte CC-≤-12-Regel wurde über `# noqa: C901` umgangen.

- [x] `start_server` zerlegt (CC 19 → 8): Dispatch-Shell + 9 Pfad-Methoden.
- [x] `query` Streaming in `_consume_stream` ausgelagert (CC 16 → 7).
- [x] Reasoning-Fallback in `_apply_reasoning_fallback` dedupliziert (DRY).
- [x] Alle `# noqa: C901` entfernt — Ruff C901: 0 violations. 115 Tests grün.

### Striktere Incapable-Klassifikation + Prozessdisziplin (v5.1.0 – 14.07.26, Session 65)

Coverage-Malus greift jetzt korrekt bei Modellen, die komplette Module nicht durchlaufen haben. `supports_tool_use: false` wurde als "incapable" (exempt) klassifiziert, selbst wenn das Modell getestet wurde (error-Rows). Fix: striktere Logik + Card-Korrekturen + Evidence-Pflichtfeld für `false`-Cards.

- [x] Card-Fixes: Command A+ und GPT-OSS 20B `supports_tool_use: false → true` (getestet, durchgefallen ≠ incapable).
- [x] `_classify_module_status`: `attempted_set` aus `df_all` — incapable+error-Rows → "missing" (Malus), nicht "incapable" (exempt).
- [x] `_apply_coverage_malus` + `_expected_assets_for_model`: `df_all`/`attempted_canonical_cats` Parameter.
- [x] `supports_tool_use_evidence` Pflichtfeld für `false`-Cards + Validierungs-Check + 10 Tests.
- [x] Scoring-Methodik-Doku für Web-Veröffentlichung (`docs/SCORING_METHODOLOGY_WEB.md`).

### Framework-Refactoring (Sektion A–M) + Ruff 0-Violations (v4.10.18 – 11.07.26, Session 59)

24 Commits nach v4.10.17 — systematisches Refactoring des Framework-Codes gegen die Architektur-Regeln. Verhaltenserhaltend — keine Änderungen an Scoring/Token-Budget/Provider-Logik.

- [x] **Sektion A — `model_utils.py` Aufspaltung** — Monolith in 7 Submodule + Re-Export-Bridge (rückwärtskompatibel).
- [x] **Sektion D — `web_export.py` Aufspaltung** — God-Script in Package `scripts/web_export/`.
- [x] **Sektion G — Config-SSoT** — 18 raw `yaml.safe_load` → `ConfigValidator` in 15 Skripten.
- [x] **Sektion H — Legacy-Cleanup** — 27 Migrationsskripte nach `scripts/legacy/`.
- [x] **Sektion I — Logging-SSoT** — 131 `print()` → `logging` in Framework-Utils.
- [x] **Ruff 0-Violations** — 711 auto-fixable + 252 manuelle Verstöße aufgelöst.
- [x] **Verifikation:** ruff 0 violations, 1316 passed/0 failed, `make validate` clean, Eleventy-Build 366 Dateien/0 Errors.

### Web-Export Datenqualitäts-Fixes + Vendor-Taxonomy-Korrekturen (v4.10.17 – 10.07.26, Session 58 Folge)

9 Folge-Commits nach v4.10.16 — Datenqualitäts-Fixes aus Web-Export-Verifikation, Vendor-Taxonomy-Korrekturen, Dead-Code-Bug, variantenbewusster `display_name` und Framework-Refactoring-Plan.

- [x] **`political_bias` Phantom-Key aus Scores-Contract entfernt** — Forward-Looking-Platzhalter für nie implementiertes Bias-Modul. 10→9 Keys.
- [x] **`judge_prog` → `judge_progress_status` (Dead-Code-Bug)** — Skip-Row-Filter prüfte auf nicht-existierende Spalte.
- [x] **Community-Fine-Tuner aus vendor→community korrigiert** — Mia-AiLab, llmfan46.
- [x] **Variantenbewusster `display_name` für Thinking-Varianten** — Dual-Profile bekommen ` (Thinking)`-Suffix.
- [x] **Verifikation:** Web-Export 88 Modelle, 0 Vendor-Warnungen, 9 Score-Keys, Eleventy-Build 366 Dateien, 0 Errors.

### Baustellen-Cleanup (v4.10.15 – 08.07.26, Session 50)

- [x] **Sampling-vs-Card-Drift** — 4 vllm_spark-Modelle bekamen Card-konforme Sampling-Parameter.
- [x] **vLLM-Extensions-Whitelist** — `_VLLM_EXTRA_BODY_KEYS`-Konstante mit generischem Loop.
- [x] **Card-Vocabulary: Dense + Tool-Use deprecated** — 4 Cards bereinigt.
- [x] **2 Live-Runs** — Gemma-4-26B--VSPK ThinkingProbe, ux_writing_002 ornith Re-Run.
- [x] **Regression clean** — 1079 passed / 1 skipped / 0 failures.

### Card-Naming SUFFIX-SSoT + model_version-Pollution-Migration (v4.10.14 – 07.07.26, Session 49)

- [x] **`_card_path(for_write=True)` PREFIX→SUFFIX** — vereinheitlicht mit `build_card_id()`. 13 Karten per `git mv` umbenannt.
- [x] **Neues Feld `model_variant`** — interne Variant-Bezeichnung landet hier statt in `model_version`.
- [x] **`migrate_model_versions_pollution.py`** — atome Migration (33 Cards + 1498 CSV-Zeilen).
- [x] **Verifikation** — `audit_model_versions.py` 0 flagged (vorher 31).

### WebExport-Konsistenz-Fixes (v4.10.13 – 04.07.26, Session 47)

- [x] **ToolUse-Scores datenbasiert exportiert** — Gate von `supports_tool_use=True` auf Datenpräsenz umgestellt.
- [x] **`_EMOJI_RE` um Variation Selectors erweitert** — VS16/VS15/ZWJ werden mit entfernt.

### Frühere Releases (v4.10.0–v4.10.12)

- **v4.10.12:** Web Linkify-Abschaffung, Review-Prosa-Vertrag (keine Metrik-Zitate), Web-Export Typ-Konsistenz, audit_log_count-Semantik, Provider-Entfernung.
- **v4.10.8:** Doku-Stempel-Check + Drift-Refactor, Cohere Native ToolUse, clean-results Variant-Handling.
- **v4.10.7:** clean-results Variant-Handling + _rebuild_index Fix.
- **v4.10.6:** Anthropic Token-Cap 8192→32768, Benchmark-Cleanup (144 verfälschte Zeilen entfernt).
- **v4.10.5:** Provider-Connector SSoT (`_extract_reasoning_tokens`, `ThinkAccumulator`), Judge Token Usage Context.
- **v4.10.4:** CSV-Write-Through Bug Fix (atomare Schreibvorgänge).
- **v4.10.3:** Token-Budget-Refactoring (`_resolve_request_tokens()` SSoT).
- **v4.10.0:** Web-Export Nullwert-Entfernung (`_strip_none()`), Card-Research Force-Run (110/110 Cards `profile_verified=true`).

### v4.x Releases

- **v4.9.0–v4.9.3:** Card-Datenpflege-System (Vendor-Kanonisierung, `profile_verified`, Editor-Prompts), Vendor Card description-Feld.
- **v4.8.6:** Robustness-Fixes (Judge-Coverage, Draft-Card-Warning, ToolUse P1/P2 SSoT).
- **v4.7.0–v4.7.3:** 4-Phasen-Refactoring der Kern-Skripte (Ruff 0, CC ≤ 12), Thinking-SSoT-Auflösung, Web-Export-Blacklist, Thinking-Probe v2 (Multi-Prompt).
- **v4.6.0–v4.6.1:** CSV-Hygiene Defense-in-Depth (Sanitizer + Hard-Fail-Guard + `make validate-csv`).
- **v4.5.0:** ID-SSoT-Refactoring (`resolve_canonical_model_id()`, `enforce_card_first()`).
- **v4.4.0:** CSV Robustness & Leaderboard Pipeline Hardening.
- **v4.3.0–v4.3.2:** Spark-Connector Konsolidierung, Kontextfenster-Fix, Code Quality Pass.
- **v4.2.0–v4.2.1:** OpenRouter-Migration, Free-Tier-Support, Qwen-Integration, ToolUse-Pipeline Bug-Fixes.
- **v4.1.0:** llamacpp-Erweiterung & Bug-Fixes.
- **v4.0.0:** Pricing-Architektur-Bereinigung (Model Cards als SSoT, Budget-Enforcement entfernt).

### v3.x Releases

- **v3.15.0–v3.15.1:** Tool Use Probe-Run (5 Modelle live), 4 Frontier Model Cards (Mistral Large 3, Devstral 2, GPT-5.5, Gemini 3.5 Flash).
- **v3.13.0–v3.14.0:** Tool Use Bug-Fixes, Phase-C Asset + Judge Hardening.
- **v3.10.0–v3.12.0:** Tool Use Benchmark-Modul Launch, Phase-A-Erweiterung, Golden Standard v1.2.0.
- **v3.9.0:** Architektur-Compliance-Refactoring (Provider-Registry, LanguageValidator, God-Script-Zerlegung).
- **v3.7.0–v3.8.0:** Modell-Kategorisierungs-SSoT (3-Tier `weights_license_tier`), Model Card Klassifikations-System, Pricing SSoT Migration.
- **v3.5.0–v3.6.5:** ThinkingProbe & Card-First Workflow, Asset-Limit-Kalibrierung, PC Token-Asymmetrie-Analyse, Archetyp-Umbenennungen.
- **v3.4.0–v3.4.7:** Token-Budget-System, Token-Verbrauch im Leaderboard, Political Compass Integration Fix, Magic-Number-Elimination.
- **v3.3.0–v3.3.1:** Language Compliance & Prompt Hardening, Political Compass Integration Fix.
- **v3.0.0–v3.2.2:** Architecture Hardening & Anti-Censorship, Audit & Meta-Review Generation, Fallbacks & Provider SSOT.

### v1.x–v2.x Releases

- **v2.6.2:** God-Script Dismantling, Namespace Collision Resolution, Magic Numbers Centralization.
- **v1.5:** LLM-Based Scoring System (Hybrid Scoring, Rubric & Prompt Configuration).
- **v1.1+:** Leaderboard Overhaul, Reasoning Module, System Probes, Golden Standard Consolidierung.
