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
## Aktueller Status (2026-07-07)

- Abgeschlossen: **Session 49 (v4.10.14) — Card-Naming SUFFIX-SSoT-Alignment + `model_version`-Pollution-Migration.** (1) `_card_path(for_write=True)` auf SUFFIX `{base}--{shortcode}.json` umgestellt (aligniert mit `build_card_id()`), 13 Karten per `git mv` umbenannt, 2 Auto-Duplikate gelöscht, `generate_review.py` repariert, 12 neue Regressionstests. (2) Neues Feld `model_variant` in `_CARD_TEMPLATE`; atome Migration von 33 Karten + 1498 CSV-Zeilen (Quant/Variant-Tokens aus `model_version` → `quantization_format`/`model_variant`); 2 vorgängige CSV/Card-Splits geheilt. Verifikation: `audit_model_versions.py` 0 flagged (vorher 31), `make leaderboard` 0 Split-Rows, `make validate` 0 invalid, `pytest` 1054 passed (2 pre-existing failures unverändert). Version v4.10.14 in alle 7 Stellen synchronisiert.
- Nächster Schritt: Session 49-Änderungen als coherent commit committen (card-naming SSoT + model_version migration). Backup `.bak_model_version_migration_20260707_085031/` vor Commit prüfen (nicht committen — `.gitignore` oder manuell ausschließen).
- Offen/Risiko: 2 pre-existing ruff-Fehler in `benchmark_auto.py` (F401 `canonical_lookup_keys`, F841 `module_key`) — nicht durch Session 49 verursacht. 2 pre-existing pytest failures (`test_card_vocabulary_ssot::test_all_model_cards_pass_tag_whitelist` — "Dense"/"Tool-Use" Tags nicht in Whitelist; `test_clean_results_arch_coverage::test_dry_run_mentions_all_csv_files` — gemma_leaderboard.csv) — nicht durch Session 49 verursacht.
