## SESSION START INSTRUCTIONS

On every new session, read these files in this order:
1. `memory-bank/activeContext.md`  — current focus and open questions
2. `memory-bank/progress.md`       — what is done, what is blocked
3. `memory-bank/systemPatterns.md` — architecture, stack, patterns

Do NOT auto-read reference files. Only load a reference file when the current
task explicitly requires it. Check `memory-bank/reference/_index.md`
to know what reference files exist.

---

# Active Context

## Aktueller Status (2026-06-20)

- **Session 25 abgeschlossen (2026-06-20) — Card-Research Force-Run + Template-Cleanup:**
  - **110/110 Cards `profile_verified=true`** — vollständiger Force-Run aller Model Cards.
  - **Template-Änderungen (required → optional):** `params_total_b`, `params_active_b`, `knowledge_cutoff`, `license_url`, `input_price_per_1m`, `output_price_per_1m`. Grund: Beschreibungen sagten "null wenn X" aber `required: true` — Widerspruch.
  - **`MAX_CARDS=N`** implementiert: `make card-research MODEL=all MAX_CARDS=10` für Batch-Verarbeitung. Fortschrittsanzeige am Ende.
  - **`MODEL=all`** gefixt: Early-Validation und `_discover_research_targets()` erkennen jetzt `all` als "alle Cards".
  - **`probe_thinking.py`** Path-Bug gefixt: `card_path.relative_to(ROOT_DIR)` Crash bei relativen Pfaden.
  - **Thinking-Probe Platzhalter:** 9 lokale Modelle (Ollama entfernt) → manuell sinnvolle Werte gesetzt basierend auf Modellfamilie (Qwen3 = thinking detected, Gemma 4 = not detected).
  - **Lizenz-String-Konsistenz:** `Apache-2.0` vs `Apache 2.0` — LLM erkennt das als Lizenz-Wechsel und rewrite't alle Textfelder. Führt zu vielen roten Findings aber korrektem Ergebnis.
  - **Parse-Fehler:** 1× `qwen3_5-9b` (LLM lieferte kein valides JSON) → Retry erfolgreich.
  - **Claude `license_url`:** Manuell auf `https://www.anthropic.com/legal/terms` gesetzt für `claude-sonnet-4-5-20250929`.
  - **`thinking_probe_at` Timestamp:** 7 Cards hatten Probe-Ergebnisse aber keinen Timestamp → nachgetragen.
  - **`supports_tool_use`:** `gemma-4-26B-A4B-it-UD-Q8_K_XL` hatte kein `supports_tool_use` → `False` gesetzt.
  - **Dokumentation aktualisiert:** `docs/DEVELOPER_GUIDE.md` (optional-Felder markiert), `docs/ARCHITECTURE.md` (Card-Research Flow + optionale Template-Felder), `CLAUDE.md` (6 neue Pitfalls), `Makefile` (probe-thinking Hilfe).

- **Session 24 abgeschlossen (2026-06-19) — Card-Research MCP Tool-Use + Lizenz-Heuristik + GGUF-Fixes:**
  - `manage_model_cards.py --mode research` kann jetzt über MCP `web_search` + `fetch` im Internet recherchieren.
  - Architektur: JSON-RPC 2.0 HTTP POST zum bestehenden MCP-Server (`:8765`), keine Änderungen am MCP-Server nötig.
  - Neue Funktionen: `_parse_tool_call()`, `_call_mcp_tool()`, `_extract_tool_content()`
  - Neue Methode: `Researcher._research_tooluse_one()` — Multi-Step-Loop (max. 3 Runden)
  - Neue CLI-Flags: `--tooluse` (nur mit `--mode research`), `--mcp-url` (Default: `http://localhost:8765`)
  - Makefile: `TOOLUSE=1` Flag an `card-research` Target
  - Lizenz-Heuristik: `_KNOWN_LICENSE_MAPPINGS` (Gemma/Qwen/Llama), `_KNOWN_COMMUNITY_GROUPS`, `_match_family()`, `_check_license_consistency()`, `_check_community()`, `_check_license_text_fields()` (Pre-Finding), `_check_license_cascade()` (Post-Merge), `_ensure_license_consistency()`
  - GGUF-Fixes: `_is_gguf_model()`, `_ensure_gguf_conventions()` (Post-Apply: deployment_type, params_active_b, Preise)
  - `profile_verified`-Fix: Validiert finale Karte statt Findings-Historie
  - MCP Auto-Lifecycle: `_ensure_mcp_running()` + `_stop_mcp_server()` + `_reset_llama_context()` + `_check_health()`
  - Usage: `make card-research MODEL=gemma-4-12b-it-ud-q8_k_xl TOOLUSE=1` (MCP auto-start/stop)

- **Session 23 abgeschlossen (2026-06-17) — Review-Auto-Fixes + MTP-Modell + 128 GB-Korrektur + (GGUF)-Cleanup:**
  - **Bug 1 (Python 3.14 @dataclass-Crash):** `scripts/analysis/generate_review.py` `_load_card_module()` lud Modul via `module_from_spec` ohne `sys.modules`-Registrierung. Fix: `sys.modules[module_name] = module` VOR `exec_module`. Hintergrund: Python 3.14 `@dataclass` ruft `sys.modules[cls.__module__].__dict__` für KW_ONLY-Detection → NoneType-AttributeError ohne Registrierung.
  - **Bug 2 (`outputs/audit_logs/test/`-Stub):** `test_pipeline_integration.py` instanziiert `UnifiedBenchmarkRunner("test")` und ruft `_process_single_test()` auf. `save_audit_log(model="test", ...)` schreibt real nach `outputs/audit_logs/test/asset_1.md` (mit MagicMock-Content). Fix 1: Test patched jetzt `utils.scoring.judge_evaluator.save_audit_log` in `mock_dependencies`-Fixture. Fix 2 (Defense in Depth): Neue Helper `_is_valid_audit_dir()` in `generate_review.py` mit Zwei-Pfad-Heuristik — entweder (a) Slug-File vorhanden ODER (b) Ordnername sieht aus wie Modellname (>4 Zeichen, Bindestrich/Underscore, keine Punkte). Schließt `test/`, `foo/`, `.DS_Store` aus, behält `gpt-5_4/`, `qwen3_5-9b/` etc. 103 gültige Audit-Ordner erkannt (104 total - 1 test stub).
  - **DGX-Spark-Modell-Liste konsolidiert:** `provider_config.yaml` `llamacpp_spark` auf 7 aktive Modelle reduziert (gemma-4-31B-it-Q8_0-MTP, gemma-4-26B-A4B-it-UD-Q8_K_XL, hermes-4.3-36b-q6, gemma-4-31B-it-UD-Q8_K_XL, **qwen3_6-35b-a3b-mtp-ud-q8** (NEU), qwen3_5-35b-a3b-q8, qwen3-coder-next-q4). Nicht-vorhandene Quantisierungen/Modelle auskommentiert mit Begründung.
  - **MTP-Support (Qwen 3.6 Multi-Token Prediction):** Neue `extra_server_args`-Verarbeitung in `utils/providers/llamacpp_base.py` `_build_server_cmd()` — übergibt beliebige llama.cpp-Flags (`--spec-type draft-mtp`, `--spec-draft-n-max 2`). 2 neue Model Cards: `qwen3_6-35b-a3b-mtp-ud-q4.json` + `qwen3_6-35b-a3b-mtp-ud-q8.json` mit Custom-Params (temperature=0.7, top_p=0.8, top_k=20, presence_penalty=1.5, repeat_penalty=1.0, **enable_thinking: false**). 2 neue Whitelist-Tags in `card_vocabulary.yaml`: `MTP` + `Speculative-Decoding` (v4.10.0).
  - **128 GB Unified Memory für DGX Spark:** 28 Referenzen "115 GB" / "120 GB" in 15 Model Cards + `_index.json` auf 128 GB korrigiert. "DGX10 Spark" → "DGX Spark" (10 ist Hostname gx10-b20a.local, kein Modellteil). "Desktop" → "Workstation" für 36B+ Klassen.
  - **"(GGUF)"-Cleanup:** Aus User-UI-Feldern (`display_name`, `summary`, `judge_context_hint`, `strengths`, `known_limitations`, `weights_provenance_risk_rationale`) entfernt. Quantisierungssuffix (Q4_K_M, Q8_K_XL etc.) impliziert GGUF → redundante Container-Info raus. Technische Felder (`model_id`, `model_version`, `name` in provider_config, `model_file`, `license_url`) behalten GGUF. 181 Updates in 31/5/16 Dateien, 106/106 JSON valide.
  - **2 neue OpenRouter-Modelle provider_config:** `z-ai/glm-5.2` + `moonshotai/kimi-k2.7-code`.
  - **`cost_tracker.py` Log-Message präzisiert:** Trennt jetzt klar "Card vorhanden, aber keine Preise (lokales Modell)" (DEBUG) von "Keine Model Card" (WARNING).
  - **Tests:** 814/814 grün.

- **Session 22 abgeschlossen (2026-06-14) — PC Re-Run + Bias-Review nemotron-3-ultra:**

- **Session 22 abgeschlossen (2026-06-14) — PC Re-Run + Bias-Review nemotron-3-ultra:**
  - **PC-Re-Run abgeschlossen:** `nvidia/nemotron-3-ultra-550b-a55b` mit `--force` re-gerunnt (3 Runs × 79 Fragen via OpenRouter). Neues Results-File: `outputs/runs/results_nvidia_nemotron_3_ultra_550b_a55b_20260614_124002.json`.
  - **Neuer Bias-Report (echte Daten):** `outputs/audit_logs/nvidia_nemotron-3-ultra-550b-a55b/00_bias_report.md` — 136KB, erstellt 14:40, kein `[REKONSTRUIERTER BERICHT]`-Flag. Enthält Einzelfragen-Protokolle.
  - **Bias-Review generiert:** `docs/reviews/nvidia_nemotron-3-ultra-550b-a55b/bias_review_20260614_144114.md` via GPT-5.4.
  - **Checkpoint-Behavior dokumentiert:** `--force` umgeht nur den PC-Leaderboard-Skip-Check, löscht NICHT den Session-Checkpoint. `io_manager.load_checkpoint(force_new=False)` = Checkpoint bleibt. `force_new=True` (separater Parameter) = Checkpoint gelöscht.
  - **Makefile-Klarstellung:** `make reviews-auto FORCE=1 TYPE=tooluse` → NEIN (`reviews-auto` hardcoded `--type all`). Korrekt: `make review TYPE=tooluse ALL=1 FORCE=1`.

- **Session 21 abgeschlossen (2026-06-14) — Benchmark-Audit nach Auto-Run:**
  - **PC-Run vollständig:** 118 Einträge in `political_compass_leaderboard.csv`. Alle 5 neuen Modelle korrekt eingetragen (Xiaomi MiMo V2.5-Pro, V2.5, V2-Flash; NVIDIA Llama-3.3-Nemotron-Super-49b, Nemotron-3-Nano-30B).
  - **Dot-Naming-Pitfall (kritisch, behoben):** `audit_logger.py` + `test.py` Fix: `.replace(".", "_")` ergänzt. Bias-Reviews generiert für xiaomi-mimo-v2_5, mimo-v2-flash, nemotron-3-nano-30b-a3b.
  - **5 neue Model Cards erstellt:** `xiaomi_mimo-v2_5-pro.json`, `xiaomi_mimo-v2_5.json`, `xiaomi_mimo-v2-flash.json`, `nvidia_llama-3_3-nemotron-super-49b-v1_5.json`, `nvidia_nemotron-3-nano-30b-a3b.json` (alle `card_status: "minimal"`).
  - **11 Review-Dirs ohne Full Review** (bekannte + neue Backlog-Fälle).
  - **PC-Plausibilität:** Alle Koordinaten valide, 1 hohe Flip-Rate: `gemini-3-flash-preview` (50%) — inhaltlich korrekt (Narr-Typ).

- **Session 20 abgeschlossen (2026-06-13) — Web-Export PC-Bugs + PC-Ghost-Model + Bias-Reviews + Vendor-Card-Dedup:**
  - **Bug 1 (Commit 994d447):** `political_compass.json`-Einträge hatten kein `card_id`-Feld — nur `slug`. Fix: `_build_compass_entry()` um Parameter `card_id: str | None = None` + Feld `"card_id": card_id` erweitert; Main-Loop übergibt `card.get("model_id")`.
  - **Bug 2 (Commit 994d447):** `pc_leaderboard.csv` hat undatierte Modellnamen (z. B. `moonshotai/kimi-k2.5`), Main-Loop verarbeitet datierte IDs (z. B. `moonshotai/kimi-k2.5-0127`). Slug `kimi-k2-5-0127` trifft nie auf Key `kimi-k2-5` → `lb_row = None` → vanilla_x/forced_x = null. Fix: Datum-Fallback nach dem Slug-Lookup: `re.sub(r'-\d{4,8}$', '', _pc_slug)`.
  - **Echte Datenlücken** (Benchmark-Re-Run nötig): claude-opus-4-5, claude-haiku-4-5, glm-5-1, minimax-m2-7. ~~glm-5-20260211~~ → behoben (siehe unten).
  - **Ghost-Model-Fix (z-ai/glm-5-20260211):** April-2026-Run hatte `z-ai/glm-5` (undatiert) als Leaderboard-Eintrag. `base_runner.py` normalisiert via `re.sub(r'-\d{8}$', '', ...)` → `z-ai/glm-5-20260211` trifft auf alten Eintrag → false-positive Skip. Fix: PC-Benchmark mit `--force` re-gerunnt (2026-06-13). Ghost-Eintrag via UPSERT überschrieben + altes `k.A.`-Entry aus `political_compass_results.csv` manuell gelöscht.
  - **28 Bias-Reviews generiert (Commit 8e02609):** Fehlende `00_bias_report.md` aus CSV-Daten synthetisiert → `generate_review.py -t bias` für alle betroffenen Modelle. `docs/reviews/` vollständig befüllt.
  - **Alibaba Vendor-Card-Dedup (Commit 9c38063):** `alibaba_cloud.json` + `alibaba_group_qwen_team.json` (auto-generierte Orphan-Dateien vom 2026-06-12) gelöscht. `alibaba_group_qwen_team_hauhaucs_community_fine_tune.json` erhält `card_subtype: "community"`. `web_export.py`: `vendor_cards.json` filtert jetzt Community-Cards (`card_subtype != "community"`). Ergebnis: 3 → 1 Alibaba-Eintrag, 24 → 18 Einträge in `vendor_cards.json`.
  - **42/42 Web-Export-Tests grün.**

- **Session 19 abgeschlossen (2026-06-13) — Model Card Publish-Audit:**
  - **Kontext:** User fragte ob Cards ohne Falschinformationen publishbar sind.
  - **4 fehlerhafte Cards korrigiert (Commit 1dc07a5):** `google_gemma-4-31b-it` (summary behauptete Weights nicht öffentlich → falsch), `magistral-small-latest`, `deepseek_deepseek-v4-flash`, `deepseek_deepseek-v4-pro` (alle: `local_deployment_possible: false → true`, Cloud-Only-Formulierungen entfernt).
  - **`mistral-large-2411` geprüft (Commit 5e33133):** `restricted-weights` bestätigt (Weights auf HuggingFace unter MRL), Hardware-Hinweis ergänzt: >300 GB GPU-VRAM (aus offiziellem HF Model Card).
  - **`verify_model_cards.py` ausgeführt + 2 Fixes (Commit fd4ebaf):**
    - 20 lokale Open-Weights-Modelle: `input_price_per_1m/output_price_per_1m: null → 0.0` (gemma-4 Quants, hermes, qwen3-lokal, codestral-latest)
    - `verify_model_cards.py` Bug: Dot-vs-Underscore-Normalisierung fehlte → 18 false-positive „fehlende Cards". Fix: `_normalize(mid)` in der Config-vs-Card-Comparison.
  - **Verbleibende ⚠️-Warnungen sind legitim:** `params_total_b: null` für geschlossene Modelle (Parameteranzahl nicht öffentlich), `thinking_probe_*: null` für neue ungeprüfte Modelle, `license_url: null` für proprietäre Modelle.
  - **Endstatus:** `✅ Alle 99 Konfigurationsmodelle haben Cards.` — keine echten fehlenden Cards, keine Falschinformationen.

- **Session 18 abgeschlossen (2026-06-13) — Deployment-Badge-Refactoring (Two-Layer):**
  - **Kontext:** Scoreboard zeigte für lokale llamacpp-Modelle keinen Badge. Clarification: „lokal" = gesamtes Intranet (M4 MacBook, DGX Spark, Gaming-PC RTX 4070), nicht nur Ollama.
  - **Architektur-Entscheidung:** Zweischichtiges Deployment-Identifikations-System — Deployment-Category als primärer Badge + Hardware-Profile als Tooltip/Detail.
  - **`config/provider_config.yaml`:** Neuer Top-Level-Abschnitt `hardware_profiles` (3 Einträge: `m4_macbook_pro_metal`, `dgx_spark_cuda`, `rtx4070_cuda`). Alle Provider erhalten `deployment_category` (api/cloud/local). `llamacpp.short_code` M4APL → LCL; `llamacpp_spark.short_code` SPRK → LCL.
  - **`utils/model_utils.py`:** 3 neue Dicts: `_PROVIDER_DEPLOYMENT_CATEGORY`, `_PROVIDER_HARDWARE_PROFILES`, sowie 2 neue Funktionen: `get_deployment_category(provider) → str`, `get_hardware_profile(provider) → str | None`.
  - **`scripts/leaderboard/__init__.py`:** 2 neue Spalten: `Deployment Category` + `Hardware Profile`.
  - **`scripts/web_export.py`:** 3 neue JSON-Felder pro Modell: `provider_code`, `deployment_category`, `hardware_profile`.
  - **`docs/MODEL_CLASSIFICATION.md`:** Sektion „Provider-Kategorien" → „Provider-Kategorien & Deployment-Badges" komplett neu geschrieben (Two-Layer-Architektur, Hardware-Profil-Tabelle, Schritt-für-Schritt-Anleitung für neue Hardware).

- **Session 17 abgeschlossen (2026-06-12) — 4 SSoT-Robustness-Fixes (Commits e5799bb, 3225a78, 4aaf450, 411e5e3):**
  - **Architektur-Prinzip etabliert:** `model_id` aus der Model Card ist der einzige SSOT-Kommunikations-Anker für alle Lookups — niemals Display-Namen oder abgeleitete Strings.
  - **e5799bb — Hardware-Kontext SSOT:** `SystemContextManager` las Mac-Profil statt Testsystem. Fix: `hardware_profile_key` aus `provider_config.yaml` (SSoT) → Profil-Lookup via `benchmark_config.yaml → runner_environment.profiles`. Neue Funktion `_get_hardware_profile_for_model()`. 2 neue Profile: `dgx_spark_cuda` + `m4_macbook_pro_metal`.
  - **3225a78 — Tooluse-Reviews per-model Modus:** Tooluse-Leaderboard-IDs (Ollama-Format `gemma3:12b`) passten nicht zu Audit-Log-Slugs → Tooluse-Schritt aus dem per-model-Loop herausgenommen, läuft nach dem Loop mit `model=None`.
  - **4aaf450 — Web-Export PC-Lookup:** `_lookup_pc_row` nutzte Display-Namen statt `raw_model_id`. Fix: `_pc_id = raw_model_id`, `_pc_slug = slugify(_pc_id)`.
  - **411e5e3 — Blacklist-Check Tooluse-Reviews:** Guard 2 lädt Model Card einmal, liest `model_id`, prüft via ID gegen Blacklist (nicht via Slug/Name).
- **MiniMax M3 Klassifizierung korrigiert (2026-06-12):** Model Card `weights_license_tier: "proprietary"` → `"restricted-weights"` (Gewichte verfügbar unter MiniMax Open License). Auch `local_deployment_possible: false` → `true` korrigiert. Leaderboard neu generiert. Commit ausstehend.
- **v4.9.5 abgeschlossen (2026-06-12):** Auto-Review Webexport-Blacklist Integration. `scripts/analysis/generate_review.py`: Neue Funktion `_load_webexport_blacklist()`, Skip-Checks in `_run_per_model_all_reviews()` + `_run_audit_reviews()` (nur `--auto`-Modus). Dokumentation in `docs/AUDIT_AND_METAREVIEW.md` Sektion 2 ergänzt. Memory Bank aktualisiert. Commit 909cf59.
- **v4.9.4 abgeschlossen (2026-06-12):** Model Card Verification v1.1.0 vollständig durchgeführt. 98/98 Model Cards auf `profile_verified: true` und `profile_verified_at: "2026-06-12"` gesetzt. Korrekturen: 14 `supports_tool_use: null` → `true` (Cloud/agentic-fähige Modelle), 7 → `false` (lokale GGUF), 4 `model_version: "k.A."` → korrekte Versionsnummer, 19 open-weights/localweights Preise `0/0.0` → `null`, 9 Karten `community: "Unsloth"`, 1 `community: "HauhauCS"`. Index-Rebuild via SSoT-Tool. Backup in `benchmark_scores/model_cards/.backup_pre_verification/`.
- **v4.9.3 abgeschlossen (2026-06-12):** `description`-Feld in Vendor Card Template ergänzt (Template v1.1.0, Constraints min 240/max 480/target 360). `config/editor_prompts.yaml` Pfad- und Feldname-Fixes (`vendor_cards/`, `vendor_id`). Tests grün. Commits `871fa8c` + `2b4a433` gepusht.
- **v4.9.2 abgeschlossen (2026-06-12):** `card_subtype`-Feld in Vendor Card Template.
- **v4.9.1 abgeschlossen (2026-06-12):** Provider Cards → Vendor Cards vollständiges Rename-Refactoring (50 Files). Commit `570bc0f`.
- **Session 16 + Provider Card Cleanup abgeschlossen (2026-06-12):** Card-Datenpflege-System v4.9.0 vollständig abgeschlossen. Provider Cards konsolidiert (20 → 17 Einträge), `_index.json` neugebaut, Commits `4233671` + `9e7fb0a` gepusht.
  - v4.9.0 Vendor-Kanonisierung + profile_verified + Editor-Prompt (Commit 4233671)
  - Provider Card Cleanup (Commit 9e7fb0a): gelöscht: `nous_research`, `todo`; umbenannt: `alibaba_cloud→alibaba`, `mistral_ai_base_model_mradermacher_gguf_conversion_abliteration→mradermacher`, `cognitive_computations_eric_hartford→cognitive_computations`; `nvidia` neu in _index.json
- **Session 15 abgeschlossen (2026-06-12):** 3 Robustness-Fixes implementiert (v4.8.6). Alle 52 Tests grün. Dokumentation aktualisiert (MAINTENANCE_LOG, TOOLUSE_MODULE, SCORING_METHODOLOGY, ActiveContext).
  - Fix 1: Judge-Skip-Zeilen aus Coverage-Berechnung gefiltert (`score_calculator.py`)
  - Fix 2: Draft-Card-Warning im Leaderboard (`scripts/leaderboard/__init__.py`)
  - Fix 3a/3b/3c: ToolUse P1/P2 als Card-SSoT (`model_utils.py` + `tooluse_exporter.py`)
- **Codebase stabil.** Alle Tests grün. 28/28 Backup-Tests grün.
- **heritage_ids-Fallback vollständig implementiert (Commit 81b8cd4).**
- **ToolUse P1/P2-NaN-Bug behoben (Session 7):** `unified_runner.py` + `tooluse_exporter.py` + Direkt-Patch Leaderboard.
- **ToolUse-Sanierungen abgeschlossen (Session 8):** 5 Modelle mit gültigen live-Daten bestätigt; deepseek-r1:8b + gpt-5_5 + korrupte Zeilen aus `tooluse_leaderboard.csv` gelöscht; Leaderboard neu generiert.
- **Backup-System-Audit abgeschlossen (Session 9):** 3 SSoT-Abweichungen behoben — `cleanup_reviews.py`, `test_backup_targets.py`, `BACKUP_STRATEGY.md`.
- **Session 10 abgeschlossen:** CHANGELOG v4.8.3–v4.8.5 ergänzt, Memory Bank aktualisiert, alle Änderungen committed (v4.7.9–v4.8.5 in einem Commit). `scripts/update_model_pricing.py` NEU — 11 Modellkarten-Preise auf Stand Juni 2026 aktualisiert.
- **gpt-5_5 ToolUse-404-Fix (Session 11):** `utils/providers/openai.py` — `_OPENAI_ID_ALIASES`-Dict + `api_model = _OPENAI_ID_ALIASES.get(model, model)` in `query()`. Grund: OpenAI-API akzeptiert `gpt-5_5` (Underscore) nicht, erwartet `gpt-5.5` (Punkt). Failed-Zeilen aus `commercial_models_benchmark.csv` + `tooluse_leaderboard.csv` bereinigt. Re-Run ausstehend.
- **LLM Judge Coverage Audit + Cleanup (Session 12, 2026-06-11):** 46 fehlerhafte Einträge aus 3 CSVs entfernt. Coverage jetzt 100% bei allen 94 Modellen. Details: `progress.md`.
- **Session 13 abgeschlossen (2026-06-11):** Signal-B Cold-Start-Fix + gemma-4-26B-A4B-it-qat-ud-q4 Card finalisiert (`card_status: complete`, `supports_tool_use: true`, ToolUse P1=88.33/P2=63.33, `tooluse_recommendation: PRODUCTION`).
- **Neues Pitfall (tooluse_exporter):** `update_model_card_tooluse_fields()` in `finalize_model()` wird auf DEBUG-Level abgefangen — Card-Update kann still scheitern. Manueller Python-Call als Workaround nötig.
- **Session 14 abgeschlossen (2026-06-12):** Leaderboard-Audit nach benchmark-auto. Befunde + Fixes: (1) gemma-4-31B-it-qat-ud-q4 Draft-Card → `card_status: complete`, `Restricted Weights`, ToolUse P1=90.0/P2=56.67/Combined=73.0; (2) qwen3-coder-next-q8 P1/P2-NaN gepatcht (p1=90.00, p2=59.17, mcp_mode=live, hallucination_flag=true in tooluse_leaderboard.csv); (3) Judge-Coverage 98%→100% bei qwen3.5-397b + gemma-4-26B-A4B — je 1 `skip`-Zeile entfernt (cultural_intel_005 / ux_writing_002). Beide Modelle jetzt 42/43. Neues ThinkingProbe-Pitfall: Signal-C-Detection (Antwortlänge+Operatoren) fälschlicherweise als detected=true − manuell auf false korrigiert in gemma-4-31b-it-qat-ud-q4.json.

## Vendor Card Architektur (wichtig für neue Sessions) — v4.9.3

**Terminologie-Klarstellung (endgültig ab v4.9.1):**
- **Provider** = API-Laufzeitumgebung (Ollama, Anthropic API, DGX Spark etc.) → bleibt als `provider`-Feld in Model Cards + `utils/providers/`
- **Vendor Card** = Hersteller-/Community-Profil-Karte → heißt jetzt konsequent "Vendor Card"

**Struktur:**
- Vendor Cards: `benchmark_scores/vendor_cards/` (17 kanonische JSON-Dateien + Community-Cards, `vendor_id`-Feld)
- `vendor_cards.json` Web-Export: 18 Einträge (kanonische Vendors, Community-Cards herausgefiltert via `card_subtype != "community"`)
- Template: `config/card_template_vendor.yaml` (`card_type: "vendor"`, v1.1.0 — inkl. `description`-Feld seit v4.9.3)
- Model Cards verwenden `vendor`-Feld (normalisiert via `classification_taxonomy.json → manufacturers`)
- **SSoT-Verknüpfung (v4.9.1):** `classification_taxonomy.json → manufacturers[x].vendor_card_id` zeigt auf Vendor Card
- **Web-Export:** jede Modell-`data.json` enthält `vendor_card_ref` (vendor_card_id aus Taxonomy)
- **Verify-Check:** `verify_model_cards.py` warnt `🗂️` wenn vendor_card_id in Taxonomy, aber Datei fehlt

- Kanonische Vendor-IDs (17): `alibaba`, `anthropic`, `cognitive_computations`, `deepseek`, `google_deepmind`, `llamacpp`, `meta`, `minimax`, `mistral_ai`, `moonshot_ai`, `mradermacher`, `nousresearch`, `nvidia`, `openai`, `unknown`, `xai`, `zhipu_ai`

## Fokus für nächste Session

Falls keine neue User-Direktive: **stabile Codebasis pflegen, keine proaktiven Änderungen.**

Mögliche Anlässe für User-Aktivität (alle aus dem Backlog):
- Reasoning-Aware-Benchmark (zurückgestellt, siehe `reference/decisions-log.md`)
- 10 Modelle mit `Tests Run < 43` re-testen (Coverage-Cleanup Session 12)
- PC-Re-Run fortsetzen
- deepseek-r1:8b ToolUse Re-Run (mock-Zeile gelöscht, Session 8 — Benchmark startklar)
- **gpt-5_5 Re-Run** (code_quality_001 + documentation_quality_004 fehlen, 41/43)
- Gemma-4-12B + NVIDIA Nemotron Cultural Intelligence Re-Run (token_budget fix war 500→1000)

## Offene Tasks (Bullet-Liste, siehe `progress.md` für Details)

- **Modelle mit Tests Run < 43 re-testen** (Stand 2026-06-12):
  - hermes-4.3-36b-q6: **37/43** (code_quality_001, doc_003/004, wcag_audit, security_audit + 1 weitere) — Lokal SPRK
  - gemma-4-12b-it-ud-q6_k_xl: **38/43** (ux_writing_002/003/005, asset_001_error_messages, asset_5b + 1 weitere) — Lokal M4APL
  - gemma-4-12b-it-ud-q8_k_xl: **41/43** (ux_writing_002 + 1 weitere) — Lokal M4APL
  - gemma-4-12b-it-ud-q4_k_xl: **42/43** (documentation_quality_005) — Lokal M4APL
  - qwen3.5-397b-a17b: **42/43** (cultural_intel_005 — skip deleted Session 14) — Cloud OR
  - gemma-4-26B-A4B-it-qat-ud-q4: **42/43** (ux_writing_002 — skip deleted Session 14) — Lokal SPRK
  - ~~magistral-small-latest~~: jetzt 43/43 ✓
  - ~~z-ai/glm-5-20260211~~: jetzt 43/43 ✓
  - ~~z-ai/glm-4.7~~: jetzt 43/43 ✓
  - ~~magistral-medium-latest~~: jetzt 43/43 ✓
  - ~~gpt-5_5~~: jetzt 43/43 ✓
  - NEU: gemma-4-31B-it-qat-ud-q4: 43/43 (neu, Card complete) — Lokal SPRK
- PC-Re-Run: 31 Modelle ohne Leaderboard-Eintrag (letzter Lauf abgebrochen, Exit 130)
- ~~Qwen-Retest~~ — abgeschlossen (2026-06-10)
- ~~qwen3-coder-next-q8 ToolUse~~ — abgeschlossen (2026-06-10, Session 7)
- ~~5 weitere ToolUse-Sanierungen~~ — abgeschlossen (2026-06-10, Session 8); deepseek-r1:8b Re-Run durch User ausstehend
- ~~Backup-System-Audit~~ — abgeschlossen (2026-06-10, Session 9)
- ~~LLM Judge Coverage Audit~~ — abgeschlossen (2026-06-11, Session 12)
- ~~gemma-4-26B-A4B-it-qat-ud-q4 Card~~ — abgeschlossen (2026-06-11, Session 13)
- Reasoning-Aware-Benchmark (BACKLOG) — Re-Aktivierungs-Bedingung dokumentiert

## Letzte Änderungen

- **2026-06-20 (Session 25, Runde 2):** Web-Export Nullwert-Entfernung. `web_export.py`: `_strip_none()` Helper — entfernt `None`-Werte rekursiv aus Dicts vor JSON-Export. Angewendet auf `_build_leaderboard_entry()`, `_build_compass_entry()`, `model_card`-Sub-Dict, `data.json`-Write. Neue Export-Felder: `profile_verified_by`, `last_modified_at`. Tests: 818/818 grün. 93 Modelle exportiert, 0 None-Werte.
- **2026-06-19 (Session 24):** Card-Research MCP Tool-Use + Lizenz-Heuristik + GGUF-Konventionen + MCP Auto-Lifecycle. `manage_model_cards.py`: neue Imports (urllib, subprocess), Tool-Schemas, MCP-Helfer (`_parse_tool_call`, `_call_mcp_tool`, `_extract_tool_content`), `Researcher._research_tooluse_one()` (Multi-Step-Loop, max. 3 Runden), CLI-Flags `--tooluse` + `--mcp-url`. Makefile: `TOOLUSE=1` Flag. Lizenz-Heuristik: `_KNOWN_LICENSE_MAPPINGS`, `_KNOWN_COMMUNITY_GROUPS`, `_match_family()`, `_check_license_consistency()`, `_check_community()`, `_check_license_text_fields()` (Pre-Finding), `_check_license_cascade()` (Post-Merge), `_ensure_license_consistency()`. GGUF: `_is_gguf_model()`, `_ensure_gguf_conventions()`. `_commit_card()`: iteriert `report.findings`, `profile_verified` via finale-Karte-Validierung. MCP Auto-Lifecycle: `_ensure_mcp_running()`, `_stop_mcp_server()`, `_reset_llama_context()`, `_check_health()`. System-Prompt Regel 5: Textfelder bei Lizenz-Wechsel.
- **2026-06-13 (Session 20 — Commits 994d447 + 8e02609 + 9c38063):** PC-Coverage vollständig. `web_export.py`: `card_id`-Feld + Datum-Fallback-Lookup. 28 Bias-Reviews generiert. Ghost-Model `z-ai/glm-5` (April-2026) via `--force`-Re-Run überschrieben. 2 Orphan-Vendor-Cards gelöscht (`alibaba_cloud.json`, `alibaba_group_qwen_team.json`), hauhaucs `card_subtype: "community"` gesetzt, Community-Filter in `web_export.py`. Web-Export: 24 → 18 Vendor-Einträge.
- **2026-06-13 (Session 18):** Deployment-Badge-Refactoring. `provider_config.yaml`: `hardware_profiles`-Block + `deployment_category` pro Provider + LCL-Shortcodes (M4APL→LCL, SPRK→LCL). `model_utils.py`: `_PROVIDER_DEPLOYMENT_CATEGORY`, `_PROVIDER_HARDWARE_PROFILES`, `get_deployment_category()`, `get_hardware_profile()`. Leaderboard: 2 neue Spalten. Web-Export: 3 neue Felder. `MODEL_CLASSIFICATION.md` neu geschrieben.
- **2026-06-12 (Session 17):** 4 SSoT-Robustness-Fixes. `generate_review.py`: Tooluse-Schritt nach Loop mit `model=None` (3225a78), Blacklist-Check via `model_id` (411e5e3). `web_export.py`: PC-Lookup via `raw_model_id` statt Display-Name (4aaf450). `system_context.py` + `generate_review.py`: Hardware-Profil aus `provider_config.yaml` SSoT (e5799bb). Architektur-Prinzip: `model_id` = einziger Kommunikations-Anker. Memory Bank aktualisiert.
- **2026-06-12 (v4.9.5):** Auto-Review Webexport-Blacklist Integration. `generate_review.py`: `_load_webexport_blacklist()` + Skip-Checks (nur `--auto`-Modus). `AUDIT_AND_METAREVIEW.md` Sektion 2 ergänzt. Memory Bank aktualisiert.
- **2026-06-12 (v4.9.3):** `description`-Feld in Vendor Card Template (v1.1.0). `editor_prompts.yaml` Pfad+Feldname-Fix. Commits `871fa8c` + `2b4a433`. README, CHANGELOG, PROJECT_STATUS, Memory Bank, CARD_MANAGEMENT, REF_TODO synchronisiert.
- **2026-06-12 (v4.9.1):** Provider Cards → Vendor Cards vollständiges Rename-Refactoring. Commit `570bc0f` gepusht. 50 Files geändert (26 Renames + Content-Updates). 803 Tests grün. Details: `progress.md`.
- **2026-06-12 (Session 16 + Cleanup):** Provider Cards konsolidiert: 20 → 17 Einträge. Commit `9e7fb0a` gepusht. v4.9.0 Card-Datenpflege-System vollständig abgeschlossen.
- **2026-06-12 (Session 16):** v4.9.0 Card-Datenpflege-System vollständig abgeschlossen + dokumentiert. README `Recent Versions` auf v4.9.0/v4.8.6/v4.7.4 aktualisiert. PROJECT_STATUS, REF_TODO, progress.md synchronisiert. Commit `4233671` (149 Files, inkl. `nvidia.json`, `editor_prompts.yaml`) gepusht nach `origin/main`.
- **2026-06-12 (Session 15):** v4.8.6 Robustness-Fixes — Fix 1: Judge-Skip-Zeilen aus Coverage gefiltert (`score_calculator.py`). Fix 2: Draft-Card-Warning im Leaderboard (`__init__.py`). Fix 3a/3b/3c: ToolUse P1/P2 als Card-SSoT (`model_utils.py` + `tooluse_exporter.py`). Alle Projektdateien auf v4.8.6 synchronisiert (README, PROJECT_STATUS, REF_TODO, MAINTENANCE_LOG, TOOLUSE_MODULE, SCORING_METHODOLOGY). 52/52 Tests grün. Details: `progress.md`.
- **2026-06-11 (Session 13):** Signal-B Cold-Start-Fix (`utils/model_utils.py` `_probe_single()`) + gemma-4-26B-A4B-it-qat-ud-q4 Card finalisiert. ToolUse-Benchmark gelaufen (DGX Spark, live MCP). Details: `progress.md`.
- **2026-06-11 (Session 12 cont.):** Small-Model-Token-Budget-Feature + Card-Fixes. `token_budgets_small_models` in `benchmark_config.yaml`. `resolve_token_budget()` in `model_utils.py`: neuer Branch für Nano/Edge/Desktop/Workstation (nicht-reasoning). Judge-Context-Injection (`small_model_token_context`) in `judge_evaluator.py` + `judge_prompt_builder.py`. 2 neue Model-Cards ausgefüllt: `anthropic_claude-haiku-4-5` + `gemma-3-12b-it-spark`. Provider-Config: Gemma 3 12B Spark-Modelle aktiviert. `web_export_blacklist.yaml`: 5 Modelle blacklisted. audit_logs `gpt-5.4-nano` → `gpt-5_4-nano` umbenannt. **801/801 Tests grün.**
- **2026-06-11 (Session 12):** LLM Judge Coverage Audit — 46 fehlerhafte Einträge aus 3 CSVs entfernt (12 local, 26 cloud, 8 commercial). Coverage nach Cleanup: 100% bei allen 94 Modellen. Backups: `*.bak_judge_cleanup_20260611_073204`. Details in `progress.md`.
- **2026-06-10 (Session 9):** Backup-System-Audit — `cleanup_reviews.py` nutzt jetzt `REVIEWS_KEEP_PER_CATEGORY` aus SSoT; `test_backup_targets.py` `audit_logs_legacy_backup_*` ergänzt; `BACKUP_STRATEGY.md` Abschnitt 4.3 aktualisiert.
- **2026-06-10 (Session 7):** ToolUse P1/P2-NaN-Bug behoben — `score_contributions` deprecated, Flat-Column-Pattern eingeführt. CRUCIBLE_DELEGATE_PARENT-Fix. MCP `idle_timeout_seconds: 0`. `token_budgets.cultural_intelligence: 1000`.

## Nächste Schritte (wenn User kommt)

1. **Bei Architektur-Frage:** `systemPatterns.md` lesen
2. **Bei Bug-Report:** Similarity zu `reference/pitfall-diagnoses.md` prüfen
3. **Bei Schema-Frage:** `reference/data-schema.md` konsultieren
4. **Bei "warum haben wir X?"-Frage:** `reference/decisions-log.md` durchsuchen
