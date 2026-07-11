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
## Aktueller Status (2026-07-11, Session 59 — ensure_card_structure Duplicate-Fix)

- **Abgeschlossen:** `ensure_card_structure.py` Duplicate-Base-Card-Fix — `run_for_card()` reicht `card_path` an `ensure_card()` durch (in-place statt Neu-Erstellung), `--model`-Modus via `_find_card()` vereinheitlicht, Filename-Fallback stript Provider-Shortcodes. 7 Regression-Tests neu, 1316 passed/0 failed, ruff clean. **Uncommitted.**
- **v4.10.17 (DONE, committed `933d33d`):** Web-Export Datenqualitäts-Fixes, Vendor-Taxonomy, Dead-Code-Bug, variantenbewusster `display_name`, Framework-Refactoring-Plan.

### Aktueller Zustand
- **Working Tree:** `scripts/dev/ensure_card_structure.py` modifiziert + `tests/test_ensure_card_structure.py` neu (uncommitted). Keine JSON-Dateien in `model_cards/` verändert.
- **Version:** v4.10.17 — Production-Ready.
- **Export-Stats:** 88 Modelle, 23 blacklisted, 9 Score-Keys, 0 Vendor-Warnungen.

### Offen/Risiko
- 7 vLLM + 2 SPRK Modelle ohne Political Compass (Nutzer fügt vLLM-Compass hinzu).
- Web-Projekt: LCL-Code-Duplikation in 3 Templates (Suggestion: `is_local_code()`-Macro extrahieren).

### Nächster Schritt
- ensure_card_structure-Fix committen. Framework-Refactoring bei Bedarf starten.
