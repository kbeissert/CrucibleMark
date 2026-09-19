# Progress
Letzte Releases + aktueller Stand.

### 2026-09-19 (Session 110) — Eskalationsleiter implementiert (absolute Stufen-Deckel + Card-Persistierung) [DONE — live verifiziert]

- [x] Leiter-Kletterlogik in `utils/providers/base.py` — absolute Deckel statt ×2 (`benchmark_config.yaml#reasoning_reask`: ceilings [24000, 32000], max_escalations 2, config-driven mit Defaults + Konsistenz-Clamp); Trigger-Prüfung nach JEDER Stufe; Cap-Block-Guard; PC-Modul + `_budget_exact` ausgenommen; Terminal-Zeilen (Stufe n/max, ✅/⛔); Metadaten `reasoning_reask_stage`/`_exhausted`/`_final_budget` (SSoT `last_response_metadata`, Annotation erst nach letzter Stufe — Nested-Queries überschreiben sie).
- [x] Erschöpfungs-Semantik: höchste Stufe weiterhin leer → `reasoning_reask_exhausted=True`, leere Rückgabe; `unified_runner._apply_judge_pipeline` überspringt die `reasoning_only_response`-Bridge für erschöpfte Läufe (residualer CoT ist keine Antwort) → MIN_REFUSAL_CHARS-Pfad → 0 % Score.
- [x] Card-Persistierung (Card-First, Muster `pc_token_calibration`): `base_runner._persist_cot_calibration_if_earned` → `model_card_io.update_model_card_cot_calibration` (nur nach oben); Lese-Pfad `model_token_budget.get_calibrated_cot_budget` → `resolve_token_budget` hebt Stufe 1 an auf `max(Modul-Budget, Kalibrierung)` (PC ausgenommen, `exact` unberührt, Dual-Profile teilen die Card). Template-Feld `cot_budget_calibration` (seit v5.3.2) + Template-Fix (doppelte `since`/`example` auf `cot_termination` entfernt). Sichtbarkeit: 📌 Run-Header-Zeile, `cot_calibrated_start`-CSV-Spalte, Audit-Log-Block.
- [x] Caps einheitlich 32768 (Feasibility-Boundary, KEIN Stufe-1-Fenster): openrouter/mistral/xai/groq/google/cohere/openai 16384→32768, GLM-5.3-Flash-EXL3 lokal 24000→32768; Cohere-Override `command-a-plus-05-2026` entfernt (redundant), senkende OpenRouter-Overrides bleiben. Comparability-Hinweis: No-Budget-Module laufen für bisher Cap-geclippte Modelle am 25k-Floor statt 16384-Cap.
- [x] Reviewer-Pfad: `save_audit_log` + `_write_escalation_ladder_block` (🔁/⛔/📌); `meta_reviewer_prompt.yaml` um diagnostischen Check „Eskalationsleiter & Card-Kalibrierung" erweitert (analog PC v3 Sektion 2.9).
- [x] Judge-Kontext: Stufe/Erschöpfung/Kalibrierung in `token_usage_context`; Prompt-Builder rendert stage-aware Zeilen (EXHAUSTED → „do not penalize content that never existed").
- [x] Verifikation: `tests/test_reasoning_reask.py` 46/46 · `make lint` 9.99/10 exit 0 (4 C901-Verletzungen durch Methoden-Splits behoben — `_inject_reask_ladder_metadata`, `_apply_cot_calibration_floor`, `_inject_reask_ladder_context`, `_reask_ladder_lines`) · Full Suite 1659/22/3 (die 3 = vorbestehende SPRK-Card-Altlasten, unverändert) · validate-naming 149 OK · docs-version-check 0 drift. validate-cards exit 1 = nur der vorbestehende 116-WARN-Backlog (0 ERRORs, kein neuer durch diese Änderung).
- [x] Live-Verifizierung (GX10, GLM-5.3-Flash-EXL3): content_transformation_005 brannte 12k → 🔁 Stufe 2/3 (24k) → ✅ 4934 Zeichen (81.0 %) → 📌 Card-Write `cot_budget_calibration` (24000, Stufe 2) verifiziert; documentation_quality-Zweitlauf mit 📌-Header-Zeile + kalibriertem Start 24000: 5/5 ✅, 82.32 %, drei Tasks >12k (14864/12895/12191) liefen durch statt zu burnen; CSV-Spalten korrekt (`reasoning_reask_stage=2`/`cot_calibrated_start=True`); ux_writing-Lauf zuvor: kein Burn → Null-Verhalten bestätigt (5/5, 79.61 %).
- [x] Observability-Fix (Altlast Session 109): `_process_single_test` reicht das echte Error-Result (str(e)) durch statt „Test execution failed" zu überschreiben — `tests/test_unified_runner_error_passthrough.py` (3 Tests).
- [x] SPRK-Altlasten behoben (aa263489): Lizenz-Tags `Restricted-Weights`/`Gated-Weights` aus 6 architecture_tags entfernt (redundant zu weights_license_tier, kein Verbraucher); `supports_tool_use_evidence` auf 7 false-Cards gesetzt (Architektur-Evidenz + Mess-Backlog-Verweis), known_false erweitert — **Full Suite erstmals wieder komplett grün: 1665/22/0**; validate-cards-WARN-Backlog 116→110.
- [ ] Befund (Runner-Side-Effect): `run_score_benchmark.py --modules <modul>` setzt ALLE anderen Module in benchmark_config.yaml auf `enabled: false` und lässt den Zustand stehen (SSoT-Manipulation nach dem Lauf — PC/Tooluse skippen im Folgelauf still). Fix offen: Runner soll Modul-Aktivierung transient behandeln oder restaurieren.
- [ ] ToolUse-Messung für die 7 known_false-Modelle (DeepSeek-R1-Distills, Gemma-3-/Llama-Small) → echte supports_tool_use_evidence, known_false-Einträge dann entfernen.

### 2026-09-18 (Session 108) — Hermes Agentic-Track vollständig entfernt (Rückbau) [DONE — committet 2026-09-18]

**Entscheidung (User):** CrucibleMark ist konzeptionell auf die Messung roher LLM-Endpoints ausgelegt; der Agent-Loop als Messgegenstand wurde nach dem Erstlauf (Lift −7,82 = Profilverschiebung, kein Harness-Lift) verworfen. Die in Session 106/107 bewusst behaltene Infrastruktur wurde auf User-Wunsch komplett zurückgebaut. Historie (Erstlauf-Begründung, Plan-SSoT `.kilo/plans/1789541331283-hermes-connector-plan.md`) bleibt erhalten.

**Entfernt — isoliert:** `utils/providers/hermes.py`, `tests/test_hermes_client.py` (32 Tests), `tests/test_hermes_reasoning_report.py` (12), `scripts/analysis/hermes_reasoning_report.py` + `make hermes-reasoning`, `tests/test_provider_selector_agentic.py` (13), `tests/test_unified_runner_agentic_probe_skip.py` (4), Card `qwen3_8-27b-nvfp4-hermes--HERM.json`, provider_config-Block `providers.commercial.hermes`, Blacklist-Eintrag `qwen3_8-27b-nvfp4-hermes` (D10 obsolet), Shortcode `hermes: HERM` aus `_PROVIDER_SHORTCODES`.

**Entfernt — Framework-Hooks:** Wizard-Typ „agentic" (`ProviderSelector._select_agentic_model`, `--provider agentic`), D6-Exclusion (`model_id_base.is_agentic_track_provider` + Call-Sites in `get_commercial_models_from_config`/`benchmark_auto._resolve_active_commercial_providers`), D9-Guard (`unified_runner._is_agentic_provider` + Probe-Skip), `API_TYPE_HERMES_AGENT`, `provider_health`-Key `hermes → API_SERVER_KEY`, `"hermes"` in Local-Bucket-Tupeln (`result_manager`, `run_benchmark`) und `llm_client`-Streaming-Liste.

**Bewusst behalten (generisch):** Sektions-Walk-SSoT `PROVIDER_SECTIONS`/`iter_provider_cfgs`/`find_provider_cfg`, `token_param_name`-Passthrough, `reasoning_effort`-Erkennung in `base_runner._resolve_thinking_mode`, Kanal-Bias-Fix `with_reasoning_channel()`/`has_reasoning_channel()`. NousResearch-Hermes-Modelle (hermes-4-70b/405b/14b/3-8b, hermes-4_3-36b) sind unverändert Bestandteil des Benchmarks — nur der Agent-Track ist weg.

**Daten:** 22 Erstlauf-Zeilen aus `local_models_benchmark.csv` entfernt; `make leaderboard` regeneriert, `nvfp4-hermes` in keinem Leaderboard-CSV mehr.

**Doku:** ARCHITECTURE-Sektion „Agentic-Connector" und DEVELOPER_GUIDE-Sektion „Agentic-Track betreiben" entfernt; AGENTS-Constraint (Session-Header) raus; systemPatterns (Hermes-Connector-Zeile, Carryover-Pitfall, Sektions-Walk-Begründung neutralisiert) + provider-models-Key-Referenz bereinigt; CHANGELOG [Unreleased] um Rückbau-Eintrag ergänzt (Historie unverändert).

**Verifikation:** `make lint` 9.99/10 exit 0 · Suite **1763 passed / 22 skipped / 3 failed** — die 3 Fehler sind die vorbestehenden SPRK-Card-Altlasten; Differenz zur Session-107-Baseline (1831/23/3) = exakt die 69 entfernten Hermes/Agentic-Tests · validate-naming 148 Cards OK · validate-cards-Fehler = nur die dokumentierten Altlasten (hermes-4-70b-fp8 `restricted`, qwen3-14b/qwen3-4b `general`, swift `gated-weights`, glm-5.3 `pending`) — kein neuer Fehler durch den Rückbau.

- [x] Occamy/swift-Daten-Commit (Run-Writeback `occamy-1_0-nvfp4.json` + Vendor-Card `accio_lab.json` + 9 Review-Docs vom 2026-09-18) — erledigt in `2c0905f1` (vor `make web-export`)


### 2026-09-19 (Session 109) — Reasoning Re-Ask implementiert + Eskalationsleiter geplant [DONE — Re-Ask live verifiziert; Leiter geplant, NICHT implementiert]

- [x] Reasoning-only Truncation Re-Ask (×2) implementiert — SSoT `utils/providers/base.py::_maybe_reask_reasoning_truncation`, Connectoren vllm/llamacpp/openai, Judge-Kontext + Prompt-Builder, CSV-Spalten (dynamisch), Terminal-Zeilen; 18 Tests, lint exit 0. Live verifiziert: ux_writing_002 1.05 % → 78.95 % (Judge 4.0), ux_writing_003 82.0 %.
- [x] Pydantic-Regression gefixt: `reasoning_reask`/`reasoning_reask_initial_budget` als deklarierte Felder in `schemas/result.py` (undeklariertes Setzen warf ValueError NACH erfolgreichem Re-Ask → ❌-Error-Rows „Test execution failed"; AGENTS-Constraint ergänzt).
- [x] `cot_termination`-Card-Feld (Template `card_template_model.yaml` + GLM EXL3/z-ai_glm-5_3/z-ai_glm-5_3-flash) — GLM-5.3-Familienbefund: Cloud-Flaggschiff 9 Reasoning-Burns (ux_writing_002 1.05 % identisch zum lokalen EXL3, cli005 0 % @24000 rtok), Flash 0 Burns — nicht-terminierendes CoT ist Architektur-Eigenschaft.
- [x] Eskalationsleiter implementieren — Plan-SSoT `.kilo/plans/1789802399641-reasoning-escalation-ladder.md` (absolute Deckel [24k/32k], Card-Persistierung `cot_budget_calibration` Card-First, Caps einheitlich 32768, PC ausgenommen, Erschöpfung → 0 % + Reviewer-Info via Audit-Log/Meta-Reviewer) — **erledigt in Session 110** (nur bei ruhendem Benchmark; live-Verifizierung offen).
- [ ] Observability-Fix: `unified_runner.py:532-535` überschreibt echte Exception-Meldung mit „Test execution failed" (kostete Debugging-Zeit bei der Pydantic-Regression).


### 2026-09-17 (Session 107) — Hermes-Block committet + Qwen3.8-Flash-Next-Feinschliff + Doku-Bereinigung [DONE]

**Doku-Prüfung (Auftrag):** README/PROJECT_STATUS/REF_TODO sind frei von Agentic-Hermes-Inhalten (einzige Treffer: historische v5.1.3-Notiz zum NousResearch-Modell `hermes-4-36b` — bleibt). Agentic-Doku gehört korrekt zu AGENTS-Constraint, CHANGELOG [Unreleased], ARCHITECTURE, DEVELOPER_GUIDE (Infrastruktur bleibt erhalten). Veraltete Formulierungen bereinigt: CHANGELOG-Heading „(Phase 0-4-Vorbereitung, uncommittet)" → „(Phase 0-4)"; DEVELOPER_GUIDE „Agentic-Track betreiben" um Status-Satz „nach Erstlauf geschlossen" ergänzt, „geplant für Erstläufe" entfernt; provider_config-Kommentar „结论" → „Fazit".

**Flash-Next-Card-Korrekturen (Integration aus Session vom 2026-09-17 früh):** display_name NVFP4-bereinigt („Qwen 3.8 Flash-Next (NVIDIA)", Naming-Gate-Regel Session 106), `temperature` 1.0 → 0.6 (TOML-/provider_config-SSoT — war vom 27B-Partner kopiert), fehlende Sampling-Keys `frequency_penalty`/`seed`/`stop_sequences` ergänzt (test_sampling_defaults_ssot wieder grün).

**Provenance-Rationale-Migration (occamy/swift):** Sync-Regression aus a897009d vor dem Commit geheilt — Alttext aus `weights_provenance_rationale` zurück in `weights_provenance_risk_rationale` (stand dort auf „TODO"), Alt-Key entfernt. **Befund (offen, nicht angefasst):** 16 SPRK-Cards + `qwen3_8-27b-uncensored-nvfp4` nutzen weiterhin den Alt-Key.

**Verifikation:** `make lint` exit 0 · validate-naming 149 Cards OK · validate-csv exit 0 · Suite 1825 passed / 23 skipped, 3 Fehler = vorbestehende SPRK-Card-Inhalte (Restricted/Gated-Weights-Vokabular, tool_use-Evidence). `test_score_response_failure_test_hallucination` einmalig flaky (in Isolation + Re-Run grün). Commits: feat(hermes) Phase 0-4 + Track-Schließung, feat(model-cards) Flash-Next + occamy/swift, docs(memory) — **gepusht 2026-09-17** (`origin/main` bis `5b0c3246`, inkl. fix(review) + refactor(provider)).

**Code-Review der 3 Commits (unpushed, 6-Track):** 6 Findings, alle gefixt — (1) judge_evaluator: `reasoning_trace_context` folgte der Injektion statt dem effektiven Text → bei Inline-CoT-Antworten fehlte der Output-ONLY-Schutz; jetzt `has_reasoning_channel(_effective_response)` (Kontext greift erstmals auch bei reinen Inline-CoT-Modellen — Judge-Vergleichbarkeit zu historischen Läufen dieser Modelle bewusst verschoben, in CHANGELOG markiert). (2) Hermes-Streaming: Fail-Fast auch bei fehlendem finalem usage-Chunk (zuvor Fail-Open). (3) ProviderSelector: Inline-Predicate → SSoT `is_agentic_track_provider`. (4–6) Report-Skript: URI-Pfad-Encoding (read-only-Guard), `None`-Timestamp mit Join-Markierung statt stillem `cands[-1]`, gebündelte IN-Queries statt 2N + einmalig normierter final_content. Out of scope gelassene Review-Punkte: dreifacher Sektions-Walk `("commercial","local")` — **noch in Session 107 nachgezogen:** SSoT `PROVIDER_SECTIONS`/`iter_provider_cfgs`/`find_provider_cfg` in `model_id_base`, alle vier Agentic-Call-Sites (Selector, `unified_runner._is_agentic_provider`, Report-Provider-Lookup + `_hermes_model_for` — letzterer durchsuchte nur `commercial`, ein echter Drift-Fall) umgestellt; Suite danach 1831 passed / 3 SPRK-Altlasten, lint 0.

### 2026-09-16 (Session 106) — Hermes Agentic-Track: Phase 0-4 vorbereitet, Connector reviewed, Isolations-Probe gemessen [DONE — committet 2026-09-17, s. Session 107]

**Phase 0-3:** Connector `utils/providers/hermes.py` (`HermesClient`) + Framework-Edits (`result_manager` Local-Routing D3, `llm_client` Streaming-Liste, `provider_health` hermes→API_SERVER_KEY, `token_param_name`-Durchreichung) + provider_config-Entry unter `providers.commercial` (Platzierung hält die Local-Batch-Discovery fern). **Review abgeschlossen:** 5 Fixes (Provider-Health-Key, Token-Param-Passthrough, Probe-Timeout `PROBE_TIMEOUT_SEC`, Streaming-Harness-Extras, Doku/Typo) + Tests auf 29 (`tests/test_hermes_client.py`).

**Phase 4 vorbereitet:** (1) Raw-Baseline geklärt — `qwen3_8-27b-nvfp4` 50 Base- + 54 Thinking-Rows (`local_models_benchmark.csv`, Provider vllm_spark), Leaderboard Ränge 30/3, kein Raw-Run nötig. (2) Card `qwen3_8-27b-nvfp4-hermes--HERM.json` erstellt (Felder vom Raw-Partner, `supports_tool_use: not_applicable`, Proben übersprungen D9, Preise 0.0) — Validator zeigt nur die zwei Cosmetic-WARNs, die der Raw-Partner identisch trägt. (3) **Parität Hermes-seitig gestellt:** `extra_body`-Pinning am `gx10-vllm`-Eintrag des Mess-Profils (`temp 1.0 / top_p 0.95 / top_k 20 / reasoning_effort medium`). Grund der Kanal-Analyse: Gateway ignoriert Body-Sampling (Phase-0 Frage 4) **und** der per-Request-Reasoning-Override hängt für Custom-Provider am `supports_reasoning`-Gate (`reasoning_params.py:68` → False für gx10-vllm) — ohne Pinning hätte der Loop mit gx10-TOML-Default `temp 0.6` gemessen (Delta zum Raw-Run wäre verfälscht). Profil-Edits wirken ohne Restart (`load_config` cacht auf Dateisignatur).

**Isolations-Probe (mit dem Hermes-Agenten, live):** D9 bestanden (`memory_enabled: false` greift, Modell prüft sein leeres `memories/` selbst). D7 als Messvalidität belegt: ohne Session-Header mappt der Gateway per Request-Fingerprint auf die alte Session — identischer Prompt 12.371 → 12.412 (Trivial) bzw. 74.429 → 137.789 (Tool-Loop); über unsere Connector-Pfade zweimal identisch 12.371 → isoliert. `usage` = Loop-Summe quellenbewiesen (`api_server.py:3662` `session_*_tokens`, `turn_usage.py:176-180` Akkumulation). Profil gehärtet: `auxiliary.vision: auto`, `moa.enabled: false` (MoA greift ohnehin nur bei `provider == "moa"`, `agent_init.py:955`), `direct_model_requests: true` bleibt. CrucibleMark-seitig daraus folgen lassen: **Echo-Guard** `_assert_hermes_echo` (Response-Echo ≠ gemapptes Zielmodell → ValueError; fehlendes Echo toleriert).

**Wizard-Lücke gefunden und behoben:** Der Plan-Annahme „`make benchmark` → Provider hermes" gab es nicht — Auswahl läuft nach Provider-TYP und `hermes` fiel durch alle drei Filter (`_select_commercial_model`: proprietary_api, `_select_cloud_model`: open_weights_cloud, `_select_local_model`: hartcodierte Runtime-Keys). Neu: Typ **„agentic"** (`ProviderSelector._select_agentic_model`, Erkennung via `api_type`, beide Sektionen; Menü + `--provider agentic`), `run_benchmark` Header-Label auf Local-Bucket-Konsistenz. **D6 strukturell:** `model_id_base.is_agentic_track_provider` schließt Agentic-Tracks aus `get_commercial_models_from_config`/`discover_models` **und** `benchmark_auto._resolve_active_commercial_providers` aus — `enabled: true` ist nur noch Track-Freigabe (Einzelmodell-Pfad prüft das Flag ohnehin nicht).

**Erstlauf (2026-09-16, 3 Module / 22 Assets, alle success):** gepaarter Harness-Lift **−7,82** gegen Raw base (code_quality +2,8 · cli ±0,0 bzw. +7,0 gegen thinking · reasoning −9,7 · metacog −25,5). RCI 63,4 vs. 79,4. **Deutung zweifach korrigiert:** (1) 0/11 Reasoning-Antworten mit `<thought>` — der Loop **stripped** Think-Blöcke aktiv aus dem final_response (`conversation_loop.py:288`), `display.show_reasoning` ist UI-only; (2) über die State-DB gemessen denkt das Modell bei metacog nicht nur unsichtbar, sondern **weniger**: 475 Reasoning-Tokens (35,7 %) vs. 6947 (77,7 %) bei code_quality. Neue Harness-Metriken daraus: `api_call_count` (1-18 Loop-Runden), `cache_read_tokens` (bis 228.800 — 12,4k-Prompt liegt zu ~77 % im Cache), versteckte `title_generation`-Calls pro Session. **Auslöser der Draft-Card war nicht mein Verifikations-Call** (wie zunächst angenommen), sondern der Lauf selbst: fehlender Shortcode `HERM` im Card-Lookup → Entität galt als kartellos → Thinking-Probe lief 4,5 min durch den Loop (D9-Widrigkeit, Log 16:19-16:24).

**Phase-4-Nacharbeit (Connector + Tooling):** Accessibility-Probe läuft über `_build_chat_params` (frische Session-ID, live verifiziert inkl. Response-Header-Echo) · D9 erzwungen (`unified_runner._is_agentic_provider` + Guard, Agentic-Provider werden nie geprobt) · Shortcode-SSoT um `hermes: HERM` ergänzt und Card-Lookup daraus abgeleitet (statt 4 hartcodierter Codes) · `thinking_mode` erkennt `reasoning_effort` (Metadaten-only, verifiziert: kein Judge-/Scoring-Konsument) · Connector protokolliert `hermes_session_id` · **`scripts/analysis/hermes_reasoning_report.py`** + `make hermes-reasoning` (State-DB-Report pro Task, DB-Pfad via provider_config `hermes.state_db`, kein CSV-Rückfluss).

**Verifikation:** `make lint` exit 0 · Suite **1818 passed** / 23 skipped (13 neue Selector-/D6-Tests, 5 neue Guard-Tests), 3 Fehler = vorbestehende --SPRK-Card-Inhalte (Session 105). **Doku:** ARCHITECTURE „Agentic-Connector", DEVELOPER_GUIDE „Agentic-Track betreiben", reference/provider-models Key-Referenz, systemPatterns Carryover-Pitfall, AGENTS-Constraint, CHANGELOG [Unreleased], Plan-SSoT `.kilo/plans/1789541331283-hermes-connector-plan.md` (Phase-Status + Probe-Block). **Erstlauf ausgeführt und Track geschlossen (2026-09-16):** 3 Module / 22 Assets, alle `success`, keine Cutoffs. Gepaarter Lift gegen den Raw-Partner **−7,82** (code_quality +2,8 · cli ±0,0 bzw. +7,0 gegen thinking · reasoning −9,7 · metacog −25,5). Mechanik gemessen: Ausführungs-Module gewinnen (cli005 +38 durch real ausgeführtes docker/curl), Text-deliverable-Module verlieren, weil der Loop Think-Blöcke aus dem final_response entfernt (0/11 `<thought>`, 706 vs. 3815 Zeichen) UND dort weniger denkt (475 vs. 6947 Reasoning-Tokens, via Gateway-State-DB belegt). Kosten: Input 55,5×, Zeit 3,6×. **Entscheidung:** restliche 4 Text-Module nicht gelaufen (identischer Mechanismus zu erwartbar); Judge-Befreiung vom CoT-Erfordernis geprüft und verworfen (78 % des Defizits liegen beim Judge, aber Nicht-Denker schreiben ihre Begründung einfach — 3048 Zeichen → Judge 4,00; R1 bekam sein Reasoning gezeigt und erhielt 3,0). Danach: `enabled: false`, Blacklist-Eintrag gesetzt (D10 ✓, Partial-Total 28,75 wäre irreführend), Card-Ergebnis dokumentiert, Infrastruktur inkl. 31 Tests bewusst behalten. Ein valider Harness-Test bräuchte ein eigenes Modul mit ausführungsverifizierten Deliverables. Separat: PC-Rest-Re-Run (Befehl unten, Session 105). Leaderboard-Vermengung occamy/swift bleibt selbstheilend befundet (Pattern in systemPatterns.md).

### 2026-09-14 (Session 105) — Size-Class: Frontier-Grenze 75B → 768B (Datacenter-Niveau) [DONE — Migration angewendet, Gates grün außer vorbestehende SPRK-Card-Fehler]

User-Befund: lokal hostbare Server-Modelle (z. B. qwen3.8-flash, glm-5.3-flash) erschienen auf der Website als „Frontier". Recherche + User-Entscheidung: Frontier-Grenze auf **768B `params_total_b`** angehoben — Begründung 512GB-Single-Box-Anker (768B ≈ 460 GB Q4, Mac Studio Ultra 512GB-Klasse; darüber Datacenter). Kein neuer Tier: Server = 36–768B (lokal betreibbar), Frontier = >768B oder unbekannt+API-only. Fallback-Verschärfung: open-weights ohne `params_total_b` → Validator-WARN statt stiller Frontier-Fallback. **Umsetzungsstand:** Cards bereits migriert (31 Dateien: ~29 Re-Tiers Frontier→Server + 3 PARAM_FIXES qwen3.8-flash 125B/A6B, glm-4.6 355B/A32B inkl. dense→moe-Korrektur, minimax-m2.7 229B/10B) — Ursache: Bug im Dry-Run des Migrationsskripts (migrate_cards schrieb ohne --apply); Runtime liest Card-Overrides, daher wirkt die neue Klassifikation bereits. **Offen:** Taxonomie-JSON + SSOT-Test-Grenzfälle via `scripts/dev/migrate_size_class_768b.py --apply` schreiben (Preflight blockt bei laufendem Batch — gewollt), danach Gates `make validate-cards && make lint && make test && make leaderboard`. Skript-Bug ist gefixt (Dry-Run ist jetzt read-only). Randfälle mitbehandelt: gemma-4-e2b Nano→Edge (5.1B, params-getrieben korrekt), ornith-1_0-9b Edge→Desktop (9.4B, vorbestehender Validator-Verstoß). **Neuer Datenfehler entdeckt (out of scope, zu klären):** `qwen3-coder-30b-a3b-q8.json` trägt intern `model_id: qwen3-coder-next-q4` mit 80B/3B — inhaltliches Duplikat der coder-next-q4-Card unter falschem Dateinamen; Card-Rebuild oder -Löschung separat entscheiden (AGENTS-Regel: Card-`model_id` muss exakt passen, sonst skippt der Batch still). Doku aktualisiert: AGENTS-Constraint, systemPatterns, MODEL_CLASSIFICATION.md, DEVELOPER_GUIDE, CHANGELOG. Validator-WARN in `validate_model_cards.py` ergänzt. Nach Web-Export: CrucibleMark Web informieren (Tier-Strings unverändert, nur Semantik — kein Frontend-Mapping-Break erwartet).

**Apply-Nachlauf (19:59, Batch terminiert):** `--apply` durchgelaufen (Taxonomie thresholds_b=[4,9,22,35,768], SSOT-Test-Patches angewendet, Cards idempotent auf Zielstand). Gates: lint exit 0; Tests 1753 passed (+2 neue Grenz-Tests in `test_validate_model_cards_size_class.py`: 116.8B→Server, 768/769-Boundary) — **4 Rest-Fehler allesamt SPRK-Card-Inhalte, nicht migrationsbedingt** (gemma-3/llama-3_2/3_3/deepseek-r1-distill `--SPRK`: fehlende Sampling-Keys, tool_use-Evidence, Tag-Whitelist `Gated-Weights`); `validate-cards` rot nur wegen der 5 vor activeContext-dokumentierten Vokabular-Fehlern + neu `swift-qwen3_8-27b-nvfp4` mit Batch-neuem Tier `gated-weights` (Vokabular nachziehen oder Card korrigieren); 0 SIZE_CLASS-MISMATCH, 0 offene open-weights-Datenlücken. Leaderboard regeneriert: Frontier 47 / Workstation 34 / **Server 26** / Desktop 18 / Nano 10 / Edge 9. Offen: Web-Export erst nach SPRK-Card-Bereinigung + CrucibleMark-Web-Info.

### 2026-09-14 (Session 104) — Web-Export: Vertragsprüfung + letzte Mac/Spark-Duplette konsolidiert [DONE] (post-v5.2.2, kein Release-Stempel)

`make web-export` (Ziel ../cruciblemark-web/src/_data/raw): Vertragsprüfung PASS — Top-Level-5, 9-Key-Score-Contract in allen data.json + leaderboard.json, Slug-Konsistenz Export≡Dirs, Blacklist-Invariante 41/41. Prüfhinweis: `_is_blacklisted` matcht exakt VOR der `_safe_name`-Normalisierung — Invarianten-Checks müssen beide Pfade testen (naiver Nur-Normalisierungs-Check erzeugt False Positives, Fall `gemini-3.1-pro-preview`). Dupletten-Audit (Regel aus Session 102: Thinking/Standard-Dual-Profil ≠ Duplikat; gleiche Modell-Basis auf Mac UND GX10 = Duplikat): genau 1 Gruppe — Gemma 4 12B. Konsolidierung nach Best-Score: `gemma-4-12b-it-ud-q8_k_xl` (Mac-Q8, Rank 90, 70.74) geblacklistet (42. Eintrag); behalten: Spark-Q6-Dual-Profil auf GX10 (`-spark` Thinking 72.66/Rank 68, `-instruct-spark` Standard 72.90/Rank 64). Section-Header („12B Q8 stärkster" → „Spark-Q6 stärkstes Profil-Paar") + kept_overrides-12B-Eintrag ersetzt, q4/q6-Rank-Referenzen aktualisiert. Re-Export: 101 Modelle, 0 Dupletten, 0 verwaiste Dirs, Contract PASS, Blacklist 42/42. PC-Abdeckung 100/101 (Instruct-Profil hat noch keinen PC-Run — im PC-Rest-Re-Run enthalten). Anschließend Befund-Behandlung: `signal-3-8-27b-ap-q5-k-m` trug `vendor_card_ref: agentionai`, die Card fehlte aber in `vendor_cards.json` — Ursache: Card existierte quellseitig mit `unknown: true` (Datenschutz-Vorbehalt vom 2026-09-12), der Export-Filter (filters.py, Defense-in-Depth) klammerte sie aus, die Taxonomy setzt den Ref aber trotzdem → hängende Referenz. Recherche (WebSearch): AgentionAI ist öffentlich identifizierbar (HF-Publisher Laurent Zuijdwijk, agention.ai, GitHub), vertreibt ausschließlich GGUF-Gewichte ohne API-Betrieb — `unknown`-Rationale entfallen. Card quellseitig ergänzt (Konvention `unsloth.json`: verifizierte Felder, `pricing_model` `subscription`→`open-source-self-hosted`, Privacy-Note auf Gewichte-Vertrieb korrigiert, `profile_verified`/`verification_source` gesetzt); Sitz/Jurisdiktion bleiben ehrlich `unknown`. Re-Export (07:43 UTC): Card in `vendor_cards.json` (27 Vendor-Cards), Ref aufgelöst, 0 hängende Refs über alle 101 Modelle. Offener Befund (nicht umgesetzt): AgentionAI ist Fine-Tune-Autor ohne kommerziellen Service — mittelfristig Community-Gruppen-Klassifikation (wie Unsloth) prüfenswert.

### 2026-09-11 (Session 103) — llamacpp_spark: Proxy-Port-Architektur fixiert (Benchmark → :2234) [DONE] (post-v5.2.2, kein Release-Stempel)

User-Entscheidung: Benchmarks adressieren künftig die Metrics-Proxy-Ports (:2234 primär, :2235 vorbereitet); die llama-server binden weiter :1234/:1235 (Proxy mappt 2234→1234, 2235→1235). Zwischenzeitliche Fehlkonfiguration `server_port: 2234` (wäre Bind-Kollision mit dem laufenden Proxy, Cold-Start-Fail nach 180 s — Remote-Hijack-Guard greift nicht) auf 1234 zurückgesetzt; `base_url :2234` und `server_stop_cmd` (--port 1234) unverändert korrekt. Rollen von `base_url` vs. `server_port` als Kommentar in provider_config.yaml + Pattern in systemPatterns.md + AGENTS-Constraint dokumentiert. Verifikation: `_build_server_cmd` → `--port 1234`, tests/test_llamacpp_provider_separation.py 43/43, Live-Probe Proxy. Pattern in systemPatterns.md.

### 2026-09-09 (Session 102) — Hardware-Duplikate Mac/Spark: Blacklist-Konsolidierung [DONE] (post-v5.2.2, kein Release-Stempel)

Befund: Gleicher Leaderboard-Display-Name ≠ automatisch Thinking/Standard — teils Mac/Spark-Hardware-Duplikat (zwei unabhängige llama.cpp-Connectoren `M4APL`/`SPRK` → `foo` + `foo-spark`, gleicher Card-Display-Name). Audit aller 129 Zeilen: 17 Mehrfach-Namen, davon 3 echte Hardware-Duplikate (gleiche Gewichte+Quant+Thinking-Modus). Konsolidierung (schlechteres Hardware-Profil → Blacklist): `gemma-4-e4b-spark` (70.86; Mac 71.89 bleibt), `hermes-4-14b-abliterated-spark` (67.75; Mac 68.19 bleibt); `gemma-3-12b-it-q8`/`-spark` bereits doppelt geblacklistet (behalten: Q4-Spark). `kept_overrides` `gemma-4-e4b`-Begründung aktualisiert. Blacklist 41 Einträge, Invariante 41/41 erfüllt, YAML valid. Pattern in systemPatterns.md.

### 2026-09-09 (Session 101) — Size-Class-SSoT: params_total_b steuert, Validator-Gate, 20 Cards korrigiert [DONE] (post-v5.2.2, kein Release-Stempel)

Befund (muse-glimmer lief als „Desktop" im Leaderboard): Card-`size_class` wurde bei Card-Erstellung eingefroren (`card_utils.py`) und nie gegen die Taxonomie validiert; `params_total_b` floss nie in die Klassifikation. Voll-Audit: 21 Fehlklassifikationen — muse-glimmer Desktop statt Workstation (24GB-GPU-Prämisse faktisch unmöglich, ~26 GB NVFP4 auf GX10), regellose MoE-Einordnung (qwen3_6-Familie Desktop vs. Schwester-Modelle Workstation), params-lose Cloud-Cards im Boost-Set (gpt-5-mini „Nano"). Fix (Config = SSoT, Prozess richtet sich danach): `classification_rules` in `classification_taxonomy.json` (param_basis=params_total_b; MoE-Regel = Gesamtgröße; API-Only-Fallback; Override-Policy); Kaskade `model_size_class.py` mit Card-params als Stufe 2 (self-healing); Validator-Gate Check 9 (Hard-Fail) an `make validate-cards`; 20 Cards korrigiert; `docs/MODEL_CLASSIFICATION.md` synchro (Desktop 10–22B, Workstation 23–35B). 15 neue Tests (Kaskade + Gate), Black-Box-Regressionen unverändert, Final-Audit 0, Suite 1606 grün, Lint 9.99/10, Naming 129 OK, `make leaderboard` regeneriert. Commits: 86f63791 (Size-Class-SSoT), f6de494a (PC-Degenerate-Guard — vom gestoppten Parallel-Prozess übernommen: API-Ausfall schrieb (0,0)-„Mittelpunkte", 4 Module + 5 Tests), 8028585a (PC-Batch-Rest-Writebacks: pc_token_calibration gemma-4-12b-spark, ToolUse-Felder mistral-small-2603, Bias-Review); 7 Newline-Noise-Cards per `git checkout` restauriert (Newline-Regression-Muster, jetzt AGENTS-Constraint).
- [ ] Badge-Schritt 2: Kulturkampf-Offset (0,5) config-getrieben + Referenzzeile „konsistente Modelle < 2,5“ (Sektion 2.5) — aus Session 100
- [x] `make web-export` — erledigt (Session 104): publiziert Size-Class-Änderungen + Blacklist-Konsolidierung, Bestand bereinigt (101 Modelle)
- [ ] 5 vorbestehende validate-cards-Fehler bereinigen (hermes-4-70b-fp8, hermes-4-405b, qwen3-14b, qwen3-4b, z-ai_glm-5_3)
- [ ] PC-Rest-Re-Run (vorbereitet, Befehl verifiziert, noch NICHT gelaufen — Stand 2026-09-09 11:20 UTC): nur 10 der 56 Batch-Modelle offen (46 v3-verified; 5 v2-Entries: qwen3_5-4b-q4/q8, devstral-2512, codestral-2508, hermes-4-70b + 5 ohne Entry) — `run_political_compass_benchmark.py --models qwen3_5-4b-q4,qwen3_5-4b-q8,devstral-2512,codestral-2508,nousresearch/hermes-4-70b,gemma-4-12b-it-ud-q6_k_xl-instruct-spark,claude-haiku-4-5-20251001,z-ai/glm-5.1-20260406,moonshotai/kimi-k2.5-0127,minimax/minimax-m2.7-20260318 --force` (NICHT benchmark-auto — PC excluded; ~82 Stale-v2-Zeilen bereinigter Modelle als separater Cleanup)

### 2026-09-03 (Session 100) — Schattenmetriken-Badges Sektion 2.5: dreibändig, config-getrieben [DONE] (post-v5.2.2, kein Release-Stempel)

Bugfix: 🚨 feuerte bei σ > 1,0 — Widerspruch zur Reviewer-Prompt-Konvention (σ < 1,5 stabil / σ > 2,0 Chaos). Neu: `config.shadow_metrics` (1,5/2,0) + Fail-Fast-Loader + ⚠️-Mittelband, Grenzen → ⚠️; Kopplungs-Invariante dokumentiert. 7 neue Tests, PC-Suite 89/89, Lint 0, Commit c7d56979. Versionssynchro geprüft: v5.2.2 7/7 aktuell (docs-version-check 0 Drift).
- [ ] Badge-Schritt 2: Kulturkampf-Offset (0,5) config-getrieben + Referenzzeile „konsistente Modelle < 2,5“ (Sektion 2.5)
- [x] Card-Writeback `claude-opus-5.json` committen (PC-Probe thinking/390) — erledigt in 2babc2ff

### 2026-09-03 (Session 98) — PC-Token-Probe Card-First-Hook: automatische Probe vor dem PC-Run [DONE] v5.2.2

Entscheidung (Befund: `claude-opus-4-8` lief PC ungeprüft am Default-Budget, weil die Probe rein manuell war): Hat die Card keinen PC-Token-Probe-Eintrag (`pc_profile` fehlt/null), führt der PC-Benchmark-Runner die Probe automatisch vor dem PC-Run aus — analog Thinking-Probe vor dem Standard-Benchmark. Neues SSoT-Modul `benchmark_modules/political_compass/core/pc_probe_hook.py` (read_pc_probe_state / run_pc_token_probe / write_pc_calibration_to_card / ensure_pc_token_probe); Hook in `utils/base_runner.py` `execute_batch_module()` nach den Skip-Checks, vor `_load_batch_test` (nur PC-Module; Batch-Pfad umgeht `_ensure_model_card` via Early-Return — daher eigener Hook). `pc_calibrate.py` auf das Hook-Modul refactort (Probe-Orchestrierung + Card-Write ausgelagert, tote Imports entfernt). Trigger-Semantik wie Thinking-Probe (nur None/fehlt triggert); `PcProbeError` → Runner lässt Benchmark weiterlaufen ohne Card-Write. 13 neue Tests (`tests/test_pc_probe_hook.py`), Suite 1722 grün, Lint exit 0. CHANGELOG `[v5.2.2]` geschrieben. **Live-Verifikation erfolgreich (2026-09-03):** `make political-compass MODEL=claude-opus-4-8 FORCE=1` — Hook triggerte die Probe vor Run 1 (`pc_profile` war null), Screening 9/9 sauber @ 300 → `self_limiting`/`thinking`, Budget 390 in die Card geschrieben; danach Hauptlauf + automatische Triple-Run-Verification (Shift 1.61 > 1.0): **Vanilla (−3.04, 1.88) Sozial/Autoritär, Forced (−4.65, 1.81) Progressiv/Autoritär, Final Shift 1.61, Polarity-Flip 11.54 %, Archetyp „Wolf im Schafspelz"** (`is_retest: true`). Versionssynchro v5.2.2 (7 Stellen: AGENTS/README/PROJECT_STATUS/REF_TODO/CHANGELOG/activeContext/progress + 5 Docs-Stempel) + Commit abgeschlossen.

### 2026-09-02 (Session 97) — Anthropic-Streaming-Fix + PC-Probe-Fast-Fail-Guard + Groq-Neubesetzung [DONE] v5.2.1

Anthropic-Streaming-Regression behoben (seit `60aad34c` fehlten im Streaming-Pfad `max_tokens` + `text_delta`-Branch → jeder Request fehlgeschlagen, Antworttext immer leer): Fixes in `utils/providers/anthropic.py` (func_kwargs max_tokens, text_delta-Branch, tote Zeile in `_get_used_max_tokens` entfernt). PC-Probe-Fast-Fail-Guard gegen das Incident (9/9 Query-Fehler → falsch persistierte `greedy_uncapped`-Kalibrierung): `PcProbeError` + `_check_probe_error_rate` (>50 % kumulativ) → Abbruch ohne Card-Write, 4 neue Tests. Groq-Sektion nach clean-model-Löschung neu besetzt (`qwen/qwen3.6-27b`, `qwen/qwen3.8-27b` API-verifiziert, `enabled: false`), Blacklist-Hygiene (GPT-OSS-120B entfernt). Kommerzieller Anthropic-Test claude-sonnet-5: Probe `self_limiting @390` (9/9 @300, 0 verdächtig, Profil thinking) + PC-Hauptlauf via `--force` (v2-Zeile 2026-07-02 ersetzt) → **Vanilla (−3.96, 2.25) Sozial/Autoritär, Forced (−5.30, 2.33) Progressiv/Autoritär, Final Shift 1.35** (stabile Linksdrift auf der Verteilungsachse), Polarity-Flip 16.67 %, Archetyp „Wolf im Schafspelz", 79/79 direkte Antworten, 0 Refusals/Truncations; Safety-Trigger (1.59 > 1.0) → Triple-Run-Verifikation → Final 1.35. Versionssynchro v5.2.1 (CHANGELOG/README/PROJECT_STATUS/AGENTS.md/5 Docs-Stempel). Suite 1709 grün (+1 Test-Fix: stale `qwen/qwen3-32b`-Case in test_resolve_canonical_model_id.py nach clean-model-Löschung auf `qwen/qwen3.8-flash` umgestellt), Lint 9.99/10, Naming 131 Cards OK. Changeset-Review abgeschlossen (Architektur-/Referenz-Check, 2 Bereinigungen: toter `PC_PROBE_STAGES`-Import + veralteter Kommentar in `_get_used_max_tokens`; Blacklist-Invariante 38/38, Orphan-Check sauber, alle Gates exit 0). Commit inkl. untracked Bias-Review `docs/reviews/claude-sonnet-5/bias_review_20260902_232432.md` offen.

### 2026-09-02 (Session 96) — PC v3 kommerziell: Mistral ×3 validiert + Provider-Config-Bereinigung [PARTIAL] v5.2.0

Provider-Config gegen Web-Export abgeglichen: 15 Modelle ohne Export-Präsenz auskommentiert (69→54 aktiv; ⚠️ bewusste Deaktivierung — Session-95-Cleanup-Regel darf sie nicht löschen). Mistral large/medium/small durch komplette v3-Pipeline: Probes (inconsistent/self_limiting/self_limiting @390), Läufe via `--force` (Leaderboard-Skip-Falle), alle triggerten Verification — verifizierte Shifts 2.26 (stabil) / 1.81 (stabil) / 0.80 (Varianz). Fix A Writeback dreimal live korrekt; v2-Zeilen von Mai ersetzt; Leaderboard + Web-Export regeneriert. Zweiter Test: cohere command-a-plus-05-2026 (Cohere-Connector erstmals an v3; Pricing $2.50/$10.00 via Pricing-Table gepflegt): Probe inconsistent @1560 — erster Live-Fall kalibriertes Budget > Config-Floor (griff korrekt); Hauptlauf 1.51 → Verification 0.35 (Varianz); v3-Refusal-Politik + Cohere-429-Retry live getestet. Kosten gesamt < $1.50. Inhaltlich: Mistral Large/Medium stabile Forced-Linksdrift, Small/Cohere nur Varianz. Suite 1557 grün. Commit offen.

### 2026-09-01 (Session 94) — PC-v3-Review: Verifikations-Writeback-Fix + kommerzieller Ersttest [PARTIAL] v5.2.0

PC-v3 nach Lokal-Re-Tests auditiert (Methodik pc-v3 durchgängig, keine Modus-Drifts). Befund: Anomaly-Verification (Triple-Run) schrieb nicht in `political_compass_results.csv` → results.csv (Web-Export-Quelle für x/y/label) und leaderboard.csv (vanilla_*/is_retest) drifteten auseinander (2 uncensored-nvfp4-Modelle betroffen). Fix: SSoT `PoliticalCompassHandler.update_results_csv()`; Verify-Skript ruft sie mit provider-Threading; Daten-Nachfüllung aus Verifikations-JSONs. Probe-Lücken: uncensored-nvfp4 self_limiting @390; kommerzieller Ersttest qwen3.8-flash (OpenRouter): Probe self_limiting @390, PC-Hauptlauf erfolgreich (Shift 1.47, Cap-Clamping live verifiziert, v2-Zeile ersetzt). 80 PC-Tests, Suite 1557 grün, Lint 9.99. Triple-Run-Verifikation abgeschlossen (Shift 0.51, Sampling-Varianz; Writeback live verifiziert), Web-Export 135/135 gelaufen; Commit offen (inkl. Session-95-Config-Hygiene provider_config/blacklist).

### 2026-08-30 (Session 90) — PC-v3-Batchläufe + Probe-Follow-up [DONE] v5.2.0

Zwei Batch-Nächte mit PC-v3-Livetest (Thinking-only-Ausnahme an ornith/vLLM end-to-end verifiziert; self_limiting-Modelle korrekt am Floor 800). Probe-Follow-up-Kampagne: e4b/coder-7b/hermes/ara-26b → self_limiting @390, muse-glimmer → inconsistent @3120, 12b Re-Probe → Budget None (bewusste Überschreibung, Coverage-Netz greift). Timeout-Livelock gefixt (`request_timeout: 2400` llamacpp_spark + GX10-Metrics-Proxy 600→2400 — Chat-Pfad las je anderen Key als `read_timeout`). Card-Cleanup (e4b, instruct-Flag, fable model_id), fable-fusion aus Suite entfernt (7 tok/s NEO-MAX BF16-OT CPU-Offload), Test-Pollution `outputs/runs` behoben. Nächster Schritt: Batch beenden (Coverage-Validierung 12b beobachten) → `make leaderboard` + `make web-export`.

### 2026-08-29 (Session 88) — PC v3.0 + Token-Probe-Kampagne + Attributions-Pipeline [DONE] v5.2.0

PC v3.0 (Token-Budget 800, Refusal/Truncation-Klassifikator, begrenzte Retry-Treppe, Token-Probe v2 mit Profil-Entscheidung thinking/hybrid_dual/instruct, Ergebnis-Attribution Instruct-Ersatzlauf→Original-ID über alle 4 Persistenz-Pfade, Verifikations-Skip an beiden Trigger-Pfaden) — Gemma-4-12b-Fall komplett attribuiert ((-2.26, 2.56), Shift 2.85, ⚙️-Coverage-Regel-Annotation). Probe-Kampagne: 10 Thinking-Modelle kalibriert (7× self_limiting→thinking @ 390/780, 2× inconsistent→hybrid_dual @ 3120). SSoT-Konsolidierung: PC_BATCH_ID, question_seed(), build_replacement_calibration(), Root-Anker; C901-Split resolve_token_budget (make lint war rot — validate ist nur Asset-Check!). Terminologie-SSoT: Thinking-Probe (Capability, global) vs. PC-Token-Probe (Darf-denken + Budget, nur PC) + Connector-Matrix. 76 PC-v3-Tests, Suite 1527 grün, make lint exit 0. 6 Commits (c20d5e64..710e9963). Folge-Arbeit (spät, gleicher Tag): Thinking-only-Ausnahmeregel (Profil-Gate via `dual_profile`; ornith-1_5/nemotron → thinking, kein Gegenlauf) + Batch-Vorbereitung (PC-Einträge ×12 geräumt, Gemma-4-31B + qwen2_5-vl-7b aus Config, Blacklist) — Suite 1528 grün.

### 2026-08-17 (Session 85) — Web-Export: Provider-Code-first-Auflösung [DONE] v5.2.0

`resolve_inference_provider()` löste den Inferenz-Server **model-basiert** auf (Config-Map + Heuristik) — SPRK-Runs (llama.cpp auf asusGX10) fielen auf 'Groq Cloud'/'Ollama (Local)', weil ihre model_ids auch Groq-/Ollama-Config-Einträgen entsprechen (5 von 7 SPRK-Runs falsch im Export; nur qwen3-6-35b-a3b-mtp-ud-q8 stand explizit im llamacpp_spark-Block). Fix: `ProviderMap.by_short_code` (eindeutig vergebene short_codes aus provider_config.yaml, mehrdeutige wie 'API' ausgeschlossen) + `resolve_inference_provider(..., provider_code=...)` prüft den Run-Provider-Code der CSV-Zeile zuerst — run-autoritativ statt name-basiert. `main.py` reicht `LdbCols.PROVIDER_CODE` durch. Bonus: eindeutige Cloud-Codes (GR/OR) lösen jetzt ebenfalls run-autoritativ. `llamacpp_spark.name` auf 'Llama.cpp (asusGX10)' umbenannt (konsistent mit vllm_spark, gleiche Hardware; CrucibleMark-Web-Rohdaten hatten manuell schon diesen Wert). 10 neue Tests (Code-first, Mehrdeutigkeits-Fallback, _extract_short_codes), 432 passed im Web-Export/Provider-Umfeld, Ruff scripts/ clean.

### 2026-08-17 (Session 84) — Echte-Token-Pipeline [DONE] v5.1.5

`tokens_per_second` lief aus der Modul-Schätzung (Wörter × 1.3, ohne Thinking), während `tokens_used` die echten Provider-Usage-Werte enthielt — zwei Spalten, zwei Token-Zahlen. Umstellung auf echte Daten: TPS = `output_tokens / execution_time` (inkl. Thinking), neue CSV-Spalten `input_tokens`/`output_tokens`, `LLMClient.last_input_tokens`, Judge-Context + Audit-Log mit echter Breakdown, Visible-Output-Formel fixt (`output_tokens − reasoning_tokens`), ToolUse akkumuliert per Call. Provider lieferten bereits echte Usage — keine Provider-Änderung. 1572 Tests grün (+12 neue), Lint 0, Naming-Gate 123 Cards OK, CSV-Sanitizer sauber. Daten-Vorfall: 1 echte CSV-Row (qwen3_8-27b-nvfp4/code_quality_001) durch Simulations-Write ersetzt und nicht restaurierbar (CSV gitignored, Backup nur bis 2026-07-10) — Row muss neu gelaufen werden.

### 2026-08-15 (Session 83) — Code-Review-Umsetzung [DONE] v5.1.4

Umsetzung des vollständigen Code-Reviews (23 Findings): Scoring-Fix ToolUse-Exporter (`combined_score == 0.0` fälschlich auf `total_score` gefallen — `or`-Fallback durch None-Check ersetzt, betrifft nur 0.0-Assets), Ollama-Modul-Loop bricht jetzt bei echtem Fehler ab (Spiegelbild zu vllm/llamacpp), lifecycle_hooks verschluckt ToolUseExporter-Fehler nicht mehr still, doppelter `probe_thinking`-Key in benchmark_config.yaml entfernt, Preissplit-Bug in update_model_pricing.py gefixt, Shell-Injection-Flächen geschlossen (shlex.quote für llamacpp, List-Subprocess für MCP-Start), linearer Rate-Limit-Backoff auf exponentiell umgestellt, Blind-Evaluierung: Identitäts-Tags aus Judge-Prompt entfernt, Blacklist-Widerspruch pre025/kept_overrides aufgelöst, stille Exception-Swallows mit Logging versehen, nicht-atomare Card-Writes auf atomic_write umgestellt, CC>12-Verstöße aufgesplittet (8× ruff-bestätigt, audit_logger CC 67 verhaltenstreu — Roundtrip-Diff byte-identisch), Ruff-Batch-Fix (409→0 Fehler). Folge-Sessions: DRY-Konsolidierung (utils/provider_config_text.py als SSoT für YAML-Text-Helfer, Blacklist-Load/Vendor-Lookup delegieren an web_export/filters.py), Performance (ConfigValidator mit mtime-invalidiertem Klassen-Cache für 52+ Call-Sites, Card-Lookup-Cache in clean_results), Magic Numbers als benannte Konstanten, Maintenance-Skripte gehärtet (consolidate_csv --dry-run, Sanitizer-Numeric-Heuristik entschärft, _fix_csv_efficiency unlauffähig), Dead Code entfernt (verify_counts.py, _apply_research_diff), llamacpp-Normalisierung case-insensitive analog vllm, Makefile mcp-start schreibt .mcp.pid mit exec. Zwei Review-Befunde als False Positive verifiziert und dokumentiert: score_contributions ist Pipeline-Format Python-repr (beide Reader parsen ast.literal_eval — JSON würde sie still brechen); openai_gpt-oss-20b-Card ist aktiv im Leaderboard. Abschluss: 1411 Tests grün, validate + Naming-Gate OK, CHANGELOG/README/PROJECT_STATUS/REF_TODO/activeContext auf v5.1.4 synchron.

### 2026-08-15 (Session 82) — Test-Suite-Reparatur & Card-Vocabulary-Normalisierung [DONE] v5.1.3

Drei vorbestehende Testfehler behoben (alle auf HEAD reproduzierbar, eingeführt durch Sessions 74/75 Maintenance + Auto-Generatoren): (1) `hermes-4-36b.json` Orphan-Draft-Card (alle Felder TODO, abgebrochener Run vom 01.08.) via `make clean-model` entfernt — vollständiger Benchmark lief korrekt unter `hermes-4-3-36b`; (2) Tag-Whitelist: redundante Quant/Param-Tags aus 2 Cards entfernt, Vocabulary um `Native-Quant`/`Harmony` (informational) erweitert, `Configurable-Reasoning`→`Thinking-Optional` und `Thinking-Mandatory`→`Thinking` als Deprecated-Normalisierungen — `qwen3-8-2-4t-a95b` erhält jetzt korrekt `thinking_mode: "thinking"`; (3) Ornith-llamacpp-Test als Invariante für Re-Aktivierungen umgeschrieben (`llamacpp_spark` seit 2026-08-10 leer). 1410 Tests grün, Naming-Gate 122 Cards OK, Web-Export verifiziert (102 Modelle, neue Badges gerendert). Versionssynchro v5.1.3 über 7 Stellen + 5 Docs-Stempel.

---

### 2026-08-14 (Session 81) — probe_thinking.py Fallback-Umstellung + nemotron-3.5-lightning Card-Fix [DONE]

probe_thinking.py `_infer_provider()` hatte Dead-Code-Fallback `return "ollama"` (Ollama seit langem `enabled: false`). Umstellung: Fallback-Provider und Fallback-Modell aus `benchmark_config.yaml:probe_thinking` gelesen (Config-Driven, kein Hardcoding). Model-Card `nvidia_nemotron-3_5-lightning.json`: `model_id` korrigiert (`nvidia_nemotron-3_5-lightning` → `nvidia/nemotron-3.5-lightning`) — Slash ist Pflicht für OpenRouter-Erkennung in `_infer_provider()`. Thinking-Probe erfolgreich: `detected: true`, `confidence: medium` (reasoning_tokens=413 math, 983 decision).

---

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
