# Active Context

## Session-Start-Anweisungen

Beim Session-Start diese Dateien lesen:
1. `memory-bank/activeContext.md` — aktueller Fokus
2. `memory-bank/progress.md` — Historie
3. `memory-bank/systemPatterns.md` — Architektur, Patterns

Regel: Nur aktive, ungelöste Themen als Baustelle melden. Abgeschlossene Integrationen, akzeptierte Known Limitations (progress.md Session 62) und BACKLOG-Items (progress.md Ende) sind KEINE Baustellen.

---

## Aktueller Status (2026-08-03, Session 79)

- **Erledigt:** Web-Export-Code-Review gegen Architekturregeln — 10 Befunde umgesetzt (B1–B10): Safety-Gate `assert`→`raise` vor `shutil.rmtree`, Monkeypatching-Mechanismus aus `__init__.py` entfernt, Magic-String `__fallbacks__`→`ProviderMap`-NamedTuple, duplizierte Pending-Sentinels→SSoT `normalize_pending()`, breite `except Exception`→konkret, sys.path-Bootstrap zentralisiert, `_build_model_card_subdict` ausgelagert (SRP). 9 Dateien, Ruff 0 violations, 172 Tests grün, Dry-Run 95 Modelle exportiert.
- Nächster Schritt: Commit ausstehen — Web-Export-Refactoring (`scripts/web_export/` + `tests/test_web_export_blacklist.py`).
- Offen/Risiko: Keine.
