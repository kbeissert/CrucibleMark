# Active Context

## Session-Start-Anweisungen

Beim Session-Start diese Dateien lesen:
1. `memory-bank/activeContext.md` — aktueller Fokus + offene Fragen
2. `memory-bank/progress.md` — erledigt, blockiert
3. `memory-bank/systemPatterns.md` — Architektur, Stack, Patterns

Keine Referenzdateien auto-laden. Nur laden wenn aktuelle Aufgabe explizit eine Reference benötigt.

---

# Active Context
## Aktueller Status (2026-07-13, Session 64 — v5.0 Code-Review + Commit)

### Verifizierter Real-Zustand (Git + Suite)
- **Git:** `5a330906 feat(scoring): v5.0.0 Generalized Coverage Scoring + ToolUse Integration` auf `main` (13 Dateien, +1336/−69). Working Tree clean (außer `.kilo/plans/` Working-Notes, by Design untracked).
- **Full Suite:** `1346 passed, 22 skipped, 0 failed`.
- **make validate:** exit 0, Ruff 0-Violations.

### Abgeschlossen (Session 64)
- **Code-Review v5.0** (6 parallele Sub-Agenten, security clean): 1 WARNING (dead code `_find_mod_data_by_category`) + 3 SUGGESTIONS (scale-duplication, `_get_incapable_models` 2× berechnet, kein `clear_cards_cache`) — alle behoben.
- **Review-Fixes angewendet:**
  1. Dead code wired → `_find_mod_data_by_category` ersetzt inline-Loop in `_classify_module_status`.
  2. SSoT `_compute_module_scale_factors` extrahiert → genutzt von nested `_module_scale` UND `_compute_expected_module_weights` (Drift-Schutz).
  3. `incapable_map` einmal in `calculate_scores` berechnet + durchgereicht an `_calculate_run_counts` und `_apply_coverage_malus`.
  4. `clear_cards_cache()` für langlaufende Prozesse hinzugefügt.
- **Re-Validation:** Ruff clean, 1346 passed, Leaderboard-Regen: 110 Modelle, 0 Invariant-Verletzungen, `coverage_ratio` korrekt (109× 1.0, 1× 0.87).

### Nächster Schritt
- **Web-Frontend Tasks 8–10** (separates Repo `CrucibleMark-Web`, laut Plan out of scope für Backend): `tooluse_combined` aus agentic-Profilen entfernen, p1/p2 rebalancieren, Coverage-Badge (optional), resolveScore-Kommentar. Vote-on-merge.

### Known Limitations (akzeptiert, nicht blockierend)
- **8 Modelle ohne Political Compass** (bewusst nicht PC-getestet, jederzeit deferralbar):
  `Gemma-4-26B-thinking`, `Gemma-4-31B`, `gemma-4-31b-it-creative-wordsmith-q8`, `Gemma-4-31B-thinking`, `ornith-1_0-35B-FP8-thinking`, `qwable-3_6-27b-q4`, `qwable-3_6-35b-q5`, `qwen3_6-27B`. Kein PC-Daten → kein Bias-Review (by Design).
- Keine Code-Blocker. Keine offenen Risikopunkte.

---

# Active Context
## Aktueller Status (2026-07-13, Session 63 — v5.0 Coverage Scoring + ToolUse Integration) [ARCHIVIERT — superseded by Session 64 Commit]

Vollständiger Eintrag siehe `progress.md` Session 63. Headlines:
- v5.0 Generalized Coverage Scoring implementiert (Tasks 1–7 + Doku D1–D4)
- 1346 passed, Ruff clean, 110 Modelle, Invariante erhalten
- Commit erfolgt in Session 64 (`5a330906`)
