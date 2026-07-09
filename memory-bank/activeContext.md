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
## Aktueller Status (2026-07-08, Session 53 — Dual-Profile card_model_id-Drift behoben)

- **Dual-Profile card_model_id-Drift behoben (Session 53, DONE, uncommitted):** Neuer SSoT-Helper `resolve_model_cfg_for(model_id, config)` ersetzt inline-Loops in `result_manager._find_model_cfg` + `base_runner._resolve_thinking_mode`. 4 Drift-Stellen reichen jetzt `model_cfg` an `_find_card`/`resolve_canonical_model_id` durch: `data_loader.py` (Version-Spalte), `unified_runner.py:_resolve_model_card_path` + `_canonicalize_and_probe`, `web_export.py:load_model_card`. Edge-Case in `_write_probe_to_card`: bei fehlender Shared-Card wird sie unter Basis-ID angelegt (keine Drift-Card). Drift-Card `ornith-1_0-35B-FP8-thinking.json` entfernt (Artefakt: `medium`-Confidence statt `high`, `TODO`-Placeholder).
- **Live verifiziert:** Ornith Thinking-Profile zeigt im Leaderboard `1.0/VSPK` (vorher: `k.A.`), Web-Export hat `model_card.thinking_probe_confidence: "high"` und `weights_license_tier: "open-weights"` (vorher: fehlend). Keine Drift-Card neu erstellt.
- **Tests:** 1124 passed, 1 skipped, 1 pre-existing failure (`qwen3_5-35b-a3b-q8` GGUF fehlt).
- **Nächster Schritt:** Working Tree committen (Session-50 + Session-51 + Session-52 + Session-53 Code, v4.10.15-Bump). Thematische Aufteilung, nur auf explizite Anfrage.
- **Offen/Risiko:** Working Tree uncommitted. vLLM-TOML-Änderung auf GX10 (`--default-chat-template-kwargs` entfernt, nicht im Git). Pre-existing uncommitted: `qwen3_5-35b-a3b-q8` + `gemma-4-26B-A4B-it-UD-Q8_K_XL` auskommentiert (GGUF fehlt auf Spark).
