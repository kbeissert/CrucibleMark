# Active Context

## Session-Start-Anweisungen

Beim Session-Start diese Dateien lesen:
1. `memory-bank/activeContext.md` — aktueller Fokus + offene Fragen
2. `memory-bank/progress.md` — erledigt, blockiert
3. `memory-bank/systemPatterns.md` — Architektur, Stack, Patterns

Keine Referenzdateien auto-laden. Nur laden wenn aktuelle Aufgabe explizit eine Reference benötigt.

---

# Active Context
## Aktueller Status (2026-07-13, Session 63 — v5.0 Coverage Scoring + ToolUse Integration)

### Verifizierter Real-Zustand (Git + Suite)
- **Git:** Working Tree uncommitted — v5.0.0-Implementierung (Plan `1783970064583-tooluse-scoring-integration-v5.md`).
- **Full Suite:** `1346 passed, 22 skipped, 0 failed` (+26 neue Coverage-Tests).
- **make validate:** exit 0, Ruff 0-Violations.
- **Leaderboard:** 110 Modelle, `coverage_ratio`-Spalte, Invariante Routine+Reasoning=Total erhalten.

### Abgeschlossen (Session 63)
- **v5.0 Generalized Coverage Scoring:** ToolUse als 8. Scoring-Modul (`module_weight: 1.0`). Coverage-aware Formel (missing→Malus, incapable→exempt, rolling_out/not_deployed→excluded). 6-Status-Taxonomie. `deployment_threshold: 0.10`. `coverage_ratio`-Spalte. Per-Modell `Tests Run`. Tasks 1–7 + Doku D1–D4.

### Nächster Schritt
- **Web-Frontend Tasks 8–10** (separates Repo `CrucibleMark-Web`, laut Plan out of scope für Backend): `tooluse_combined` aus agentic-Profilen entfernen, p1/p2 rebalancieren, Coverage-Badge (optional), resolveScore-Kommentar. Vote-on-merge.
- Commit der v5.0-Änderungen steht aus (Nutzer-Entscheidung).

### Known Limitations (akzeptiert, nicht blockierend)
- **8 Modelle ohne Political Compass** (bewusst nicht PC-getestet, jederzeit deferralbar):
  `Gemma-4-26B-thinking`, `Gemma-4-31B`, `gemma-4-31b-it-creative-wordsmith-q8`, `Gemma-4-31B-thinking`, `ornith-1_0-35B-FP8-thinking`, `qwable-3_6-27b-q4`, `qwable-3_6-35b-q5`, `qwen3_6-27B`. Kein PC-Daten → kein Bias-Review (by Design).
- Keine Code-Blocker. Keine offenen Risikopunkte.
