# PROJECT_STATUS.md

> **Interner Statusbericht.** Diese Datei dokumentiert den Projektfortschritt für Maintainer und Contributor. Sie ist nicht Teil der öffentlichen Dokumentation. Aktuelle, kuratierte Release-Informationen stehen in [README.md](README.md) (Recent Versions) und [CHANGELOG.md](CHANGELOG.md).

**Last Updated:** 2026-09-25
**Current Version:** 5.4.0 — Provider-Härtung, Eskalationsleiter, Refusal-Retry, OpenRouter-Pinning & Code-Review
**Status:** Production-Ready

---

## Executive Summary

CrucibleMark v5.3.0 ist ein production-ready LLM-Benchmark-Framework mit 135+ getesteten Modellen über 11 Provider. Das Framework misst praxisnahe Leistung (Code-Reviews, UX-Texte, Reasoning, Tool-Use) mit blindem LLM-Judge und generiert Leaderboards mit License-/Sovereign-Filtern.

**Aktueller Stand (2026-09-25):**
- **135+ Modelle** im Leaderboard (Größenklassen nach Size-Class-SSoT: Frontier 47 / Workstation 34 / Server 26 / Desktop 18 / Nano 10 / Edge 9), Web-Export nach Dupletten-Konsolidierung (Mac/Spark, muse-glimmer).
- **11 Provider:** OpenAI, Anthropic, Google, Mistral, xAI, OpenRouter, Cohere, Ollama, Llama.cpp (Mac), Llama.cpp Spark (GX10 via Metrics-Proxy), vLLM (Spark).
- **8 Scoring-Module + Political Compass (v3.1):** Code Quality, CLI Operations, Reasoning & Logik, UX Writing, Cultural Intelligence, Documentation Quality, Content Transformation, Tool Use. PC seit v3.0 mit Token-Budget-Regime, Token-Probe-Profilentscheidung und Card-First-Hook (v5.2.2); v3.1 härtet für Nano-/Mini-/Desktop-Modelle (Degenerate-Guard, config-getriebene Schattenmetriken-Badges, Truncation-Signal-Korrekturen, SPRK-Kalibrierungen).
- **SPRK-Small-Model-Feld:** 14 Nano-/Mini-/Desktop-Modelle ≤ 16 GB (Unsloth-UD-Q5_K_M) + Signal 3.8 27B neu auf llama.cpp Spark integriert.
- **1917 Tests** passed, 17 skipped, 0 failed · Lint 9.99/10 · Ruff 0 violations · Pylint E-Level clean.

**Aktuelle Arbeit (Sessions 106–122):**
- **Code-Review & Bugfix-Serie (Sessions 121–122):** Vollständiges strukturiertes Code-Review (61 Befunde, 7 Sprints) — Provider-Bugs (Anthropic reasoning_tokens, Groq Streaming), magic-numbers→Config, SSoT-Cleanup, close()-Overrides, CC-Refactoring (PC execute 34→11), Skip-Logik in Resolver-Module extrahiert, Exception-Handling, Type-Hints. Audit: `docs/audits/2026-09-25_code-review.md`.
- **Eskalationsleiter + Cap-Persistierung (Session 110):** Absolut-Deckel [24k/32k], Card-First-Kalibrierung `cot_budget_calibration`, Last-Resort-Modus (48k), Erschöpfungs-Semantik, Krümel-Schwelle 500 Zeichen, Reviewer-Diagnostik. Leiter live verifiziert (GLM-5.3-Flash → +15 %).
- **Hermes Agentic-Track entfernt (Session 108):** Konzeptionelle Entscheidung — CrucibleMark misst rohe LLM-Endpoints, kein Agent-Loop. Vollständiger Rückbau (Connector, Tests, Wizard-Typ, Framework-Hooks).
- **Refusal-Retry ausgeweitet (Sessions 116–117):** Serverseitige Refusals (Claude Opus 5) erhalten tag-freien Zweitversuch; Trigger-Isolation beweist Zaun+Wrapper=Jailbreak-Signatur; code_quality_002/5A/5D/5E mit Retry-Prompts versehen.

**Aktuelle Modell-Integrationen (Sessions 82–84):**
- **Qwen 3.8 27B NVFP4** (lokal, vLLM gx10) — Standard-Profil Rank 63, Score 72.25, Silver Badge. Thinking-Profil im Benchmark (Dual-Profile-Expansion).
- **Qwen3.8 2.4T A95B** (OpenRouter, Cloud) — Rank 115, Score 67.23, Silver Badge.
- **Echte-Token-Pipeline (v5.1.5):** TPS, Judge-Context und Audit-Log laufen jetzt auf echten Provider-Usage-Werten (`input_tokens`/`output_tokens`).

**Known Limitations (akzeptiert, nicht blockierend):**
- **PC-Modul deaktiviert:** Nutzer-Entscheidung zur LLM-Nachtest-Serie — Reaktivierung ist Teil des nächsten Schritts (Opus-5.5-Nativ-Re-Run via `make political-compass`).
- **vLLM-Spark offline:** GX10 nicht verfügbar — `vllm_spark`-Einträge enabled, Batch-Runner läuft ohne sie (bewusste Nutzer-Entscheidung).
- **`make benchmark-auto` lokal nicht verfügbar:** GX10/Python-3.14-API-Break (Provider-Discovery-Teile) — Workaround: Modul-Läufe via `run_benchmark.py --module X --model Y`.
- **Changeset uncommittet:** Code-Review-Serie + vorbefindliche Fremdänderungen (AGENTS.md/progress.md) und untracked Reviews sind nicht committed.
- **Web-Frontend (separates Repo):** `price-comparison-row.njk` Null-Guard, `model-header.njk` Doppel-Rendering, Frontend stu=false-Score-Anzeige.

---

## Recent Releases

### v5.3.0 (2026-09-16) — PC v3.1 Nano-/Mini-/Desktop-Testing + SPRK-Small-Model-Feld

Political-Compass-Überarbeitung für kleine Modelle: Degenerate-Guard (API-Ausfall wird nicht mehr als (0,0)-Mittelpunkt persistiert), Schattenmetriken-Badges config-getrieben an der Reviewer-σ-Konvention (`config.shadow_metrics`, σ < 1,5 stabil / σ > 2,0 Chaos), OpenRouter-`finish_reason`- und Google-SAFETY-Masking-Korrektur mit Truncation-Re-Probes (nemotron-nano, mimo-pro), PC-Batch 04.–06.09. (`pc_profile`/`pc_token_calibration` in 16 Cards, 23 Bias-Reviews), SPRK-PC-Kalibrierung (r1-distill-1.5B 1560 `inconsistent`, Swift 390 `self_limiting`). Neues SPRK-Small-Model-Feld: 14 Nano-/Mini-/Desktop-Modelle ≤ 16 GB (Unsloth-UD-Q5_K_M) + Signal 3.8 27B, Vendor-Cards AgentionAI/UkisAI/Microsoft. Dazu Size-Class-SSoT `params_total_b` + Frontier-Grenze 768B (~30 Cards reklassifiziert, Migrationsskript), Card-Writer-Newline-SSoT (58× normalisiert), Health-Gate-Fix für Remote-APIs, Web-Export-Dupletten-Konsolidierung, Integrationen Occamy 1.0 35B-A3B / Swift-Qwen3.8 27B / DeepSeek V4.1 Flash. 1753 Tests grün, Lint exit 0 (4 vorbestehende SPRK-Card-Inhaltsfehler offen).

### v5.2.2 (2026-09-03) — PC-Token-Probe Card-First-Hook

Hat die Model Card keinen PC-Token-Probe-Eintrag (`pc_profile` fehlt/null), führt der PC-Benchmark-Runner die Probe jetzt automatisch vor dem PC-Run aus — analog zur Thinking-Probe vor dem Standard-Benchmark. Vorher war die Probe rein manuell (`make probe-pc-budget`); neue Modelle (z. B. `claude-opus-4-8`) liefen ungeprüft am Default-Modul-Budget. Neues SSoT-Modul `pc_probe_hook.py` (`read_pc_probe_state`/`run_pc_token_probe`/`write_pc_calibration_to_card`/`ensure_pc_token_probe`); Hook in `utils/base_runner.execute_batch_module()` nach den Skip-Checks, vor `_load_batch_test`, nur PC-Module. Trigger-Semantik wie Thinking-Probe (nur None/fehlt triggert); `PcProbeError` (Fast-Fail-Guard) → Benchmark läuft weiter ohne Card-Write. `pc_calibrate.py` DRY-Refactor (Probe-Orchestrierung + Card-Write ausgelagert). 13 neue Tests, Suite 1722 grün, Lint exit 0. Live-Verifikation: `claude-opus-4-8` → Probe `self_limiting` @390 (thinking), PC-Hauptlauf Shift 1.61 („Wolf im Schafspelz", `is_retest: true`).

### v5.2.1 (2026-09-02) — Anthropic-Streaming-Fix + PC-Probe-Fast-Fail-Guard

Anthropic-Streaming-Regression behoben: Seit `60aad34c` (Commercial-Streaming-Default) fehlte im Streaming-Pfad `max_tokens` als Pflicht-Argument und der `text_delta`-Branch im Delta-Handler — jeder Request schlug fehl, der sichtbare Antworttext war immer leer. PC-Token-Probe mit Fast-Fail-Guard: >50 % Query-Fehler (kumulativ über Screening + Eskalation) → `PcProbeError` → Abbruch ohne Card-Write statt falsch persistierter `greedy_uncapped`-Kalibrierung. Groq-Sektion nach clean-model-Löschung neu besetzt (`qwen/qwen3.6-27b`, `qwen/qwen3.8-27b` via Groq-API verifiziert), Blacklist-Hygiene (GPT-OSS-120B-Eintrag entfernt).

### v5.2.0 (2026-08-31) — Political Compass v3.0 + Provider-Härtung

PC v3.0 released: Token-Budget-Regime (800, kein 25k-Fallback), Refusal-/Truncation-Klassifikator, begrenzte Eskalations-Treppe, PC-Token-Probe mit Profil-Entscheidung (thinking/hybrid_dual/instruct, Card-First), Ergebnis-Attribution für Instruct-Ersatzläufe + Attribution-Mirror, Thinking-only-Ausnahme via `dual_profile`-Gate. Provider-Härtung: llama.cpp Mac/Spark-Separation, GX10-Metrics-Proxy-Connector (Token via `.env`, 401-Diagnose), Timeout-Livelock-Fix (2400 s beide Wände), Web-Export Provider-Code-first, Timeout-Metrik auf echte Fehler, HTTP-Client-Close-Kette (`atexit` → TCP FIN) gegen hängende vLLM-Generierung nach Abbruch. 1704 Tests grün, Lint 9.99/10.

### v5.1.5 (2026-08-17) — Echte-Token-Pipeline (TPS, Judge, Audit-Log)

`tokens_per_second` lief aus der Modul-Schätzung (Wörter × 1.3, ohne Thinking), während `tokens_used` die echten Provider-Usage-Werte enthielt — zwei Spalten, zwei Token-Zahlen. Jetzt: TPS = `output_tokens / execution_time` (inkl. Thinking), neue CSV-Spalten `input_tokens`/`output_tokens`, Judge-Context + Audit-Log mit echter Breakdown, Visible-Output-Formel fixt (`output_tokens − reasoning_tokens`). Provider lieferten bereits echte Usage — keine Provider-Änderung. 1572 Tests grün (+12 neue), Lint 0, Naming-Gate 123 Cards OK.

### v5.1.4 (2026-08-15) — Code-Review-Umsetzung (Sicherheit, Konsistenz, Robustheit)

23-Findings-Review umgesetzt: 5 kritische Fixes (Ollama-Loop-Break, lifecycle_hooks-Logging, combined_score-0.0-Fallback, doppelter probe_thinking-Key, Preis-Split-Bug mit neuer SSoT `config/model_pricing.yaml`), Shell-Injection-Flächen geschlossen, exponentieller Rate-Limit-Backoff, Judge-Prompt Name-Priming entfernt (Blind-Evaluierung), 8 C901-Verstöße verhaltenstreu aufgesplittet, Ruff 409→0, DRY-Konsolidierung (`utils/provider_config_text.py`), ConfigValidator-mtime-Cache, Maintenance-Skripte gehärtet. 1411 Tests grün, Naming-Gate 122 Cards OK.

### v5.1.3 (2026-08-15) — Test-Suite-Reparatur & Card-Vocabulary-Normalisierung

Drei vorbestehende Testfehler behoben: hermes-4-36b Orphan-Draft-Card via `make clean-model` entfernt; Architecture-Tags gegen Vocabulary-SSoT normalisiert (`Native-Quant`/`Harmony` neu, `Configurable-Reasoning`/`Thinking-Mandatory` deprecated); Ornith-Test als llamacpp-Invariante für Re-Aktivierungen umgeschrieben. Maintenance-Fixes aus Sessions 74/75 integriert. `political_compass` deaktiviert. 1410 Tests grün.

---

Die vollständige Versionshistorie steht in [CHANGELOG.md](CHANGELOG.md).
Detaillierte Session-Historie steht in [memory-bank/progress.md](memory-bank/progress.md).
