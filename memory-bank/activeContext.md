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
## Aktueller Status (2026-07-07, Session 49 abgeschlossen + Folge-Commits)

- Abgeschlossen: **Session 49 (v4.10.14) — Card-Naming SUFFIX-SSoT + model_version-Migration** (commits `f154d99`, `a415a31`, `454d6db`). **Folge-Commits heute:** (`2146a25`) F1 Slug-Collision-Fix in `web_export.py` — 15 Collisionen (10 Modell-Gruppen) mit provider_code-Suffix uniquifiziert, `leaderboard.json`/`data.json` provider_code-Konsistenz hergestellt. (`da4f2a5`) Scores-Contract + stu=null — alle 10 Modul-Keys immer in `data.json.leaderboard.scores` (auch null), 2 VSPK-Cards (`Gemma-4-31B--VSPK`, `ornith-1_0-35B-FP8--VSPK`) `supports_tool_use=true→null` (VSPK-Variante nicht getestet). (`d0ad62f`) SSoT-Refactor — `_SCORE_COLUMN_TO_KEY` als einzige Score-Keys-Quelle (eliminiert Triplikat-Definition). (`cc65a34`) Skill→Command-Migration + `scripts/core/vllm_batch.py` (Multi-Modell-Batch mit vLLM-Containern) + `benchmark_auto.py` Idempotenz (auto-stop bei Modell-Konflikt, 72h-Timeout). Verifikation: 1056 passed (2 pre-existing), `check:coverage` ✅ (stu-Blocker 0), `make validate` clean.
- Nächster Schritt: Keine offenen Tasks aus Session 49. Optional: v4.10.15-Version-Bump für die 3 Folge-Commits (Scores-Contract + SSoT-Refactor + vllm_batch). Backup `.bak_model_version_migration_20260707_085031/` entfernen (nicht committet).
- Offen/Risiko: 2 pre-existing pytest failures (`test_card_vocabulary_ssot::test_all_model_cards_pass_tag_whitelist` — "Dense"/"Tool-Use" Tags; `test_clean_results_arch_coverage::test_dry_run_mentions_all_csv_files` — gemma_leaderboard.csv) — unverändert, nicht durch Session 49 verursacht. 3 pre-existing `check:drift` True-Mismatches (`Gemma-4-31B`, `gemini-3.5-flash`, `moonshotai/kimi-k2`) — genuine Naming-Differences, manuelles Review.
