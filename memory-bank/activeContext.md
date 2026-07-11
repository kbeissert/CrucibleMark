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
## Aktueller Status (2026-07-11, Session 59 — v4.10.18 committed)

- **v4.10.18 (DONE, committed):** Framework-Refactoring (Sektion A–M) — `model_utils` in 7 Submodule + Bridge, `web_export.py`→Package, Helper-SSoT, `yaml.safe_load`→`ConfigValidator`, 131 `print`→`logging`, C901/Ruff 0-Violations, 27 Legacy-Skripte verschoben. Bugfix: `ensure_card_structure` Duplicate-Base-Cards. Web LCL-Duplikation via `is_local_provider`-Macro. Doku-Sync auf Package-Struktur. Verhaltenserhaltend.
- **v4.10.17 (DONE, committed):** Web-Export Datenqualitäts-Fixes, Vendor-Taxonomy, variantenbewusster `display_name`.

### Aktueller Zustand
- **Working Tree:** clean. Docs-Sync committed (`57147cdb`). Memory-Bank-Update committed.
- **Version:** v4.10.18 — Production-Ready. 24 Commits seit v4.10.17.
- **Tests:** 1316 passed, 21 skipped, 0 failed. Ruff: 0 Violations.
- **Export-Stats:** 88 Modelle, 23 blacklisted, 9 Score-Keys, 0 Vendor-Warnungen.
- **Branch:** 25 Commits ahead of `origin/main` (unpushed).

### Offen/Risiko
- 7 vLLM + 2 SPRK Modelle ohne Political Compass (Nutzer-Aktion — vLLM-Compass-Daten erfassen, nicht code-seitig lösbar).
- Branch ist 25 Commits ahead of `origin/main` — Push ausstehend.

### Nächster Schritt
- Kein offener Dev-Auftrag. Political-Compass-Daten für vLLM durch Nutzer erfassen. Push nach `origin/main` bei Freigabe.
