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
## Aktueller Status (2026-07-10, Session 58 — Web-Export Blacklist-Restructure + Slug-SSoT)

- **Session 58 (DONE, uncommitted):** Web-Export-Qualität verbessert — Blacklist-Restructure, Slug-SSoT, `normalize_pending`-Hardening, `leaderboard.json` Scores-Contract. 4 Änderungen:
  1. **Blacklist-Restructure** (`config/web_export_blacklist.yaml`): Zwei-Sektion-Layout (`blacklist:` 24 aktiv + `kept_overrides:` 22 dokumentierte Ausnahmen in 5 Gruppen). Eliminiert `# -`-Kommentar-Konvention. Loader ignoriert `kept_overrides` (reine Audit-Doku).
  2. **Slug-SSoT** (`scripts/web_export.py:_process_leaderboard`): `slugify(model_name)` → `slugify(raw_model_id)`. `model_id` = stabile Identität (eindeutig pro CSV-Zeile), `model_name` = veränderlicher Display-Wert. Eliminiert 5 Hybrid-Pair-Slug-Kollisionen (Thinking/Standard).
  3. **`normalize_pending()` Hardening**: `_PENDING_SENTINELS` frozenset (En-Dash U+2013, `n/a`, `N/A`, `null`, `None`, `none`, `nan` zusätzlich zu Em-Dash/`Pending`/`""`). O(1)-Lookup. Verhindert String-Leaks im JSON-Export.
  4. **`leaderboard.json` Scores-Contract**: `_write_top_level_outputs` erzwingt 10-Key Contract via `setdefault`/`dict.fromkeys` (zuvor nur `data.json`).
  - **Validierung:** 88 Modelle exportiert, 23 blacklisted, 0 Slug-Kollisionen, 88/88 Scores-Contract, 97 tests passed.
  - **Code-Review:** APPROVE (uncommitted).
- **Session 57 (DONE, uncommitted):** Local-Model-Preis-Bug behoben. 3 Cards (`Gemma-4-26B`, `Gemma-4-31B`, `qwen3_6-27B`) hatten `output_price_per_1m=null` + Whitelist-fremdes `deployment_type="local-weights"`. Leaderboard zeigte leere Cost-Spalte. Defense-in-Depth in `score_calculator.py:_build_price_lookup` + 12 neue Tests.
- **Session 56 (DONE, uncommitted):** `{hardware_context}`-Datenfeld pro-Modell korrekt befüllt.
- **Session 55 (DONE, uncommitted):** `thinking_mode` dreifach sichtbar (CSV, Audit-Log, Review-Prompt).
- **Session 54 (DONE, uncommitted):** Display-Name-Fix + `thinking_mode`-Spalte + `-thinking`-Suffix-Fallback.
- **Session 53 (DONE, uncommitted):** card_model_id-Drift im Web-Export behoben.
- **Session 52 (DONE, uncommitted):** vLLM Dual-Thinking-Profile implementiert.
- **Session 57 Folge-Auftrag (DONE, uncommitted):** Kosmetische `deployment_type`-Migration für 5 Cards (`local-weights` → `localweights`) + `ornith-1-0-35b` auf `localweights`.
- **Nächster Schritt:** Working Tree committen (Sessions 52–58, v4.10.16-Bump). Thematische Aufteilung, nur auf explizite Anfrage. Danach `make web-export-dev` um aktualisierten Export ins Web-Projekt zu pushen.
- **Offen/Risiko:** Working Tree uncommitted (alle 8+ Sessions, jetzt ~8 Tage alt). 3 Gemma Thinking-Profile brauchen `code_quality`-Re-Run (operativ, dokumentiert in progress.md Session 57). Pre-existing uncommitted: `qwen3_5-35b-a3b-q8` + `gemma-4-26B-A4B-it-UD-Q8_K_XL` auskommentiert. Benchmark-Daten-Fixes (nicht Export-Code): Ornith CSV `44/43`→`43/43`, Codestral `thinking_probe_confidence` fehlt, `llm_judge_coverage` 100% uniform verifizieren. 7 vLLM + 2 SPRK Modelle ohne Political Compass.
