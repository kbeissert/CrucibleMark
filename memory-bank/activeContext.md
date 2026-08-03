# Active Context

## Session-Start-Anweisungen

Beim Session-Start diese Dateien lesen:
1. `memory-bank/activeContext.md` — aktueller Fokus
2. `memory-bank/progress.md` — Historie
3. `memory-bank/systemPatterns.md` — Architektur, Patterns

Regel: Nur aktive, ungelöste Themen als Baustelle melden. Abgeschlossene Integrationen, akzeptierte Known Limitations (progress.md Session 62) und BACKLOG-Items (progress.md Ende) sind KEINE Baustellen.

---

## Aktueller Status (2026-08-03, Session 78)

- **Erledigt:** vLLM-Connector CC-Refactoring (`vllm_base.py`). `start_server` (CC 19→8) in Dispatch-Shell + 9 Pfad-Methoden zerlegt, `query` (CC 16→7) Streaming in `_consume_stream` ausgelagert, Reasoning-Fallback in `_apply_reasoning_fallback` dedupliziert (DRY). Alle `# noqa: C901` entfernt. Verhaltenserhaltend — 115 Tests grün, Ruff 0 violations. Versionssynchro v5.1.2 (7/7 Stellen).
- Nächster Schritt: Commit ausstehen — Code-Änderung uncommitted (`vllm_base.py`).
- Offen/Risiko: Keine.
