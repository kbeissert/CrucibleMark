# Active Context

## Session-Start-Anweisungen

Beim Session-Start diese Dateien lesen:
1. `memory-bank/activeContext.md` — aktueller Fokus + offene Fragen
2. `memory-bank/progress.md` — erledigt, blockiert
3. `memory-bank/systemPatterns.md` — Architektur, Stack, Patterns

Keine Referenzdateien auto-laden. Nur laden wenn aktuelle Aufgabe explizit eine Reference benötigt.

---

# Active Context
## Aktueller Status (2026-07-30, Session 72 — qwen3_6-27B-pre025 Rename + ToolUse Timestamp-Bugfix)

- Abgeschlossen: Historische `qwen3_6-27B`-ID zu `qwen3_6-27B-pre025` umbenannt (CSV 99 Zeilen, Card, Blacklist, Audit-Logs, Reviews, Runs, Tests). Bug fix: `tooluse_exporter.py` Path B überschrieb `tested_at` in 107 Cards mit `datetime.now()` — jetzt wird der existierende Card-Wert bewahrt. 1553 Tests grün, Webexport erfolgreich (pre025 blacklisted, nvfp4 exportiert).
- Nächster Schritt: Commit der uncommitteten Änderungen (Rename + Bugfix + Memory-Bank), dann Push der 13+ unpushed Commits.
- Offen/Risiko: `gemma-4-31b-it-creative-wordsmith-q8` steht in `kept_overrides` (nicht blacklist) → wird exportiert. Falls Blacklist gewünscht, muss ID in aktive `blacklist`-Sektion verschoben werden.
