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
## Aktueller Status (2026-07-10, Session 57 — Local-Model Price = 0.0)

- **Session 57 (DONE, uncommitted):** Local-Model-Preis-Bug behoben. 3 Cards (`Gemma-4-26B`, `Gemma-4-31B`, `qwen3_6-27B`) hatten `output_price_per_1m=null` + Whitelist-fremdes `deployment_type="local-weights"`. Leaderboard zeigte leere Cost-Spalte. Fixes:
  1. **Cards:** `output_price_per_1m` + `input_price_per_1m` = 0.0; `deployment_type` → `"localweights"`.
  2. **Defense-in-Depth** (`scripts/leaderboard/score_calculator.py:_build_price_lookup`): Whitelist `LOCAL_DEPLOYMENT_TYPES = {"localweights", "local-weights"}` → Karte mit lokalem Typ aber fehlendem Preis → `lookup[model_id] = 0.0`. Hybrid (`cloud-only`/`cloud-and-local`/`open-weights-cloud-available`) bleibt korrekt **leer**.
  3. **Test-Suite NEU** (`tests/test_score_calculator_price_lookup.py`, 12 Tests): lokale Karten mit/ohne Preis (beide Schreibweisen), Cloud/Hybrid-Karten, Edge Cases (kein model_id), 3 Regressionstests auf echte Cards, Cloud-Sanity.
- **Code-Quality "Pending" geklärt — KEIN Orchestrator-Bug:** Die 08:59-Session war separater `scripts/run_tooluse_benchmark.py`. `code_quality` wurde nie für Thinking-Profile geplant. Drei separate Runner (`run_score_benchmark.py` / `run_tooluse_benchmark.py` / `run_political_compass_benchmark.py`). Partielle Runs → stille Coverage-Lücken.
- **Tests:** 1148 passed (+12 neu), 1 skipped, 1 pre-existing failure (`qwen3_5-35b-a3b-q8`, dokumentiert). `make validate` exit 0.
- **Session 56 (DONE, uncommitted):** `{hardware_context}`-Datenfeld pro-Modell korrekt befüllt.
- **Session 55 (DONE, uncommitted):** `thinking_mode` dreifach sichtbar (CSV, Audit-Log, Review-Prompt).
- **Session 54 (DONE, uncommitted):** Display-Name-Fix + `thinking_mode`-Spalte + `-thinking`-Suffix-Fallback.
- **Session 53 (DONE, uncommitted):** card_model_id-Drift im Web-Export behoben.
- **Session 52 (DONE, uncommitted):** vLLM Dual-Thinking-Profile implementiert.
- **Session 57 Folge-Auftrag (DONE, uncommitted):** Kosmetische `deployment_type`-Migration für 5 Cards (`local-weights` → `localweights`) + `ornith-1-0-35b` auf `localweights` (nur lokal getestet via llamacpp_spark). `command-a-plus-05-2026` NICHT geändert (nur Cohere Cloud).
- **Nächster Schritt:** Working Tree committen (Sessions 52–57-Folge, v4.10.15-Bump). Thematische Aufteilung, nur auf explizite Anfrage.
- **Offen/Risiko:** Working Tree uncommitted (alle 7+ Sessions, jetzt ~7 Tage alt). 3 Gemma Thinking-Profile brauchen `code_quality`-Re-Run (operativ, dokumentiert in progress.md Session 57). Pre-existing uncommitted: `qwen3_5-35b-a3b-q8` + `gemma-4-26B-A4B-it-UD-Q8_K_XL` auskommentiert.
