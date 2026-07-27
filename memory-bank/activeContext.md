# Active Context

## Session-Start-Anweisungen

Beim Session-Start diese Dateien lesen:
1. `memory-bank/activeContext.md` — aktueller Fokus + offene Fragen
2. `memory-bank/progress.md` — erledigt, blockiert
3. `memory-bank/systemPatterns.md` — Architektur, Stack, Patterns

Keine Referenzdateien auto-laden. Nur laden wenn aktuelle Aufgabe explizit eine Reference benötigt.

---

# Active Context
## Aktueller Status (2026-07-19, Session 68 — Batch Card Refinements + vLLM Fixes)

- Abgeschlossen: Batch-Commit `43d60237` — 29 Model Cards verfeinert (summary refinements, data quality fixes), 3 Bias-Reviews (qwen3_6-27b-nvfp4, -thinking, 35b-a3b-nvfp4), vLLM-Batch-Fixes (provider context handling, session cleanup), Provider-Config-Update. Origin/main gepusht.
- Abgeschlossen: Web-Export verifiziert — 92/92 Modelle vorhanden (Session 67). 2 Modelle ohne Political Compass-Daten (qwen3_6-27b, gemma-4-31b-it-creative-wordsmith-q8) — 0 PC-Einträge, bekannt, nicht blockierend.
- Offen: Hermes 4.3 36B Thinking-Probe ausstehend (benötigt Server-Swap Ornith → Hermes 4.3 36B). card_status bleibt "draft".
- Risiko: 4 Model Cards ohne Benchmark-Daten: hermes-4-3-36b (in progress), hermes-4-70b-fp8, qwen3-coder-30b-a3b-q8, qwen3_5-397b-cloud.
- Nächster Schritt: vLLM-Server auf Hermes 4.3 36B swappen, Thinking-Probe laufen lassen, card_status auf "complete" setzen.
