# Active Context
Aktueller Stand und nächste Schritte.

- **Abgeschlossen:** Agent-Memory-Konsolidierung komplett — `.agent/` (5 Dateien) nach `memory-bank/reference/` migriert und `_index.md` ergänzt; `.kilo` bereinigt (6 stale Worktrees + 7 gemergte/obsolete Branches entfernt, `plans/` und vestigiale `node_modules` gelöscht, `compress-project` in `session-start` konsolidiert); `.kilo/kilo.jsonc` wegen API-Key aus Git ungetrackt und in `.kilo/.gitignore` aufgenommen; `agent-manager.json` von toten Worktree-Einträgen befreit. Alle aktiven `.agent`-Referenzen (AGENTS.md, Commands, `vllm_base.py`) umgestellt — historische Erwähnungen in CHANGELOG/progress.md bewusst unverändert.
- **Nächster Schritt:** Keiner aus dieser Konsolidierung — reguläre Projektarbeit.
- **Offen/Risiko:** `kilo.jsonc`-API-Key bleibt in der Git-Historie (lokaler Netzwerk-Endpoint 100.89.110.0:2230) — bei erhöhten Anforderungen Key rotieren oder History-Rewrite; sonst akzeptiertes Restrisiko.
