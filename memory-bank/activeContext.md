# Active Context

## Session-Start-Anweisungen

Beim Session-Start diese Dateien lesen:
1. `memory-bank/activeContext.md` — aktueller Fokus + offene Fragen
2. `memory-bank/progress.md` — erledigt, blockiert
3. `memory-bank/systemPatterns.md` — Architektur, Stack, Patterns

Keine Referenzdateien auto-laden. Nur laden wenn aktuelle Aufgabe explizit eine Reference benötigt.

---

# Active Context
## Aktueller Status (2026-07-19, Session 67 — Hermes 4.3 36B Integration)

- Abgeschlossen: Hermes 4.3 36B (Seed-OSS) als vLLM-Modell integriert — Config-Eintrag, Model Card mit dual_profile, card-research abgeschlossen.
- Abgeschlossen: Web-Export verifiziert — 92/92 Modelle vorhanden, 5 vermeintlich "fehlende" (qwen3_6-27b-nvfp4, qwen3_6-27b-nvfp4-thinking, qwen3_6-35b-a3b-nvfp4, qwen3_6-35b-a3b-nvfp4-thinking, grok-4.20-0309-reasoning) waren Artefakt eines unvollständigen Vorlaufs (108 statt 92).
- Nächster Schritt: vLLM-Server auf Hermes 4.3 36B swappen, Thinking-Probe laufen lassen, card_status auf "complete" setzen.
- Offen/Risiko: Thinking-Probe ausstehend (benötigt Server-Swap), card_status bleibt "draft" bis Probe erfolgreich.
