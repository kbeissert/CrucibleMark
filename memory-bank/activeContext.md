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

## Aktueller Status (2026-06-12)

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
- Vendor Cards: `benchmark_scores/vendor_cards/` (17 JSON-Dateien, `vendor_id`-Feld)
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
