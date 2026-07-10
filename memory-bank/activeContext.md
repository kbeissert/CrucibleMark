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
## Aktueller Status (2026-07-10, Session 58 Folge — v4.10.17 committed)

- **v4.10.17 (DONE, committed `933d33d`):** 9 Folge-Commits nach v4.10.16 — Web-Export Datenqualitäts-Fixes, Vendor-Taxonomy-Korrekturen, Dead-Code-Bug, variantenbewusster `display_name`, Framework-Refactoring-Plan. Alle thematisch committet, Working Tree clean.
- **Session 58 (DONE, committed `ab701fd`):** Web-Export Blacklist-Restructure, Slug-SSoT, `normalize_pending`-Hardening, `leaderboard.json` Scores-Contract. 88 Modelle exportiert, 0 Slug-Kollisionen, 97 tests passed.
- **Sessions 52–57 (DONE, committed):** Local-Model Preis=0.0, `{hardware_context}`, `thinking_mode` dreifach sichtbar, Display-Name-Fix, card_model_id-Drift, vLLM Dual-Thinking-Profile.
- **Doku-Sync (DONE, committed):** CHANGELOG v4.10.17, README Badge+Recent Versions, PROJECT_STATUS Header+Aktueller Stand, REF_TODO Abgeschlossen-Sektion, Memory Bank aktualisiert.

### Aktueller Zustand
- **Working Tree:** clean (alle Sessions 52–58 committed).
- **Version:** v4.10.17 — Production-Ready.
- **Export-Stats:** 88 Modelle, 23 blacklisted, 9 Score-Keys (political_bias entfernt), 0 Vendor-Warnungen, Eleventy-Build 366 Dateien/0 Errors.
- **5 Dual-Profile model_id Paare:** Gemma-4-31B, Gemma-4-26B, Gemma-4-31B-Wordsmith-NVFP4, qwen3_6-27B, ornith-1_0-35B-FP8.
- **12 Thinking-only Modelle** (Claude Opus 4.8, o4-mini, etc.) — kein Suffix nötig.

### Offen/Risiko
- 3 Gemma Thinking-Profile brauchen `code_quality`-Re-Run (operativ): `python scripts/run_score_benchmark.py --models "Gemma-4-31B-thinking,Gemma-4-26B-thinking,Gemma-4-31B-Wordsmith-NVFP4-thinking" --modules code_quality`.
- 7 vLLM + 2 SPRK Modelle ohne Political Compass (Nutzer fügt vLLM-Compass hinzu).
- Web-Projekt: LCL-Code-Duplikation in 3 Templates (Suggestion: `is_local_code()`-Macro extrahieren).
- Framework-Refactoring-Plan existiert (`docs/`), Umsetzung noch nicht begonnen.

### Nächster Schritt
- Kein offener Auftrag. Framework-Refactoring bei Bedarf starten.
