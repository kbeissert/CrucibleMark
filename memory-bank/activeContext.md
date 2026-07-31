# Active Context

## Session-Start-Anweisungen

Beim Session-Start diese Dateien lesen:
1. `memory-bank/activeContext.md` — aktueller Fokus + offene Fragen
2. `memory-bank/progress.md` — erledigt, blockiert
3. `memory-bank/systemPatterns.md` — Architektur, Stack, Patterns

Keine Referenzdateien auto-laden. Nur laden wenn aktuelle Aufgabe explizit eine Reference benötigt.

---

# Active Context
## Aktueller Status (2026-07-31, Session 73 — Laguna S 2.1 selektives Reasoning)

- Abgeschlossen: Laguna S 2.1 als selektives Reasoning-Modell identifiziert (denkt pro Request selbst, nicht immer wie Qwen3.6). `enable_thinking: true` aus `provider_config.yaml` entfernt → kein Dual-Profile mehr. `dual_profile` in Card auf `null` gesetzt. Alle Laguna-CSV-Einträge aus 4 CSVs entfernt (60+2+2+1=65 Zeilen). `add-model`-Skill um Modell-Klassen-Tabelle ergänzt (Always-Thinking vs. selektiv). CLAUDE.md + systemPatterns.md um Fallstrick ergänzt.
- Nächster Schritt: Laguna-S-2_1-NVFP4 Benchmark-Run (einzelnes Profil, Thinking serverseitig ON via TOML), danach `make leaderboard` + `make tooluse-leaderboard` neu generieren.
- Offen/Risiko: `judge_context_hint` in Laguna-Card erwähnt noch "Thinking- und No-Thinking-Modus" — sollte nach dem Run auf selektives Reasoning aktualisiert werden.
