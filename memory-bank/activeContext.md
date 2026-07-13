# Active Context

## Session-Start-Anweisungen

Beim Session-Start diese Dateien lesen:
1. `memory-bank/activeContext.md` — aktueller Fokus + offene Fragen
2. `memory-bank/progress.md` — erledigt, blockiert
3. `memory-bank/systemPatterns.md` — Architektur, Stack, Patterns

Keine Referenzdateien auto-laden. Nur laden wenn aktuelle Aufgabe explizit eine Reference benötigt.

---

# Active Context
## Aktueller Status (2026-07-13, Session 62 — Baustellen-Reconciliation)

### Verifizierter Real-Zustand (Git + Suite)
- **Git:** Clean, `0 commits ahead of origin/main`, alles gepusht (Head `0554ce59` = Session 61 Doku-Commit).
- **Full Suite:** `1320 passed, 22 skipped, 0 failed` (deterministisch, kein `pytest-randomly`).
- **Tooluse-Tests:** 78 passed, 0 failures.
- **Flaky-Test-Behauptung** aus Session 61 war veraltet — nicht reproduzierbar.

### Abgeschlossen
- **Session 61 (PC-Nachhol-Verifikation):** Gedocted & gepusht (`0554ce59`). 8 Modelle ohne Political Compass verifiziert, Memory-Bank-Sync auf Real-Zustand.
- **Session 62 (Baustellen-Reconciliation):**
  - #3 Ungepusht → bereits erledigt (verifiziert: clean + gepusht).
  - #4 Flaky Test → nicht reproduzierbar (verifiziert: Full Suite 1320/0).
  - #1 Widerspruch PC-Lücken → im Log bereits via Session-60-Nachtrag historisch korrigiert; kein aktiver Widerspruch in activeContext.
  - #2 8 PC-Lücken → per Nutzer-Entscheidung als Known Limitation akzeptiert (deferralbar).

### Nächster Schritt
- Clean slate — bereit für nächste Dev-Aufgabe. Kein offener Auftrag.

### Known Limitations (akzeptiert, nicht blockierend)
- **8 Modelle ohne Political Compass** (bewusst nicht PC-getestet, jederzeit deferralbar):
  `Gemma-4-26B-thinking`, `Gemma-4-31B`, `gemma-4-31b-it-creative-wordsmith-q8`, `Gemma-4-31B-thinking`, `ornith-1_0-35B-FP8-thinking`, `qwable-3_6-27b-q4`, `qwable-3_6-35b-q5`, `qwen3_6-27B`. Alle 0 Einträge in `political_compass_results.csv`, keine `00_bias_report.md`. Können jederzeit via `run_political_compass_benchmark` nachgeholt werden. Kein PC-Daten → kein Bias-Review (by Design: PC ist Vorbedingung, siehe `progress.md` Session 60).
- Keine Code-Blocker. Keine offenen Risikopunkte.
