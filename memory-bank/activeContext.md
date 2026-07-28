# Active Context

## Session-Start-Anweisungen

Beim Session-Start diese Dateien lesen:
1. `memory-bank/activeContext.md` — aktueller Fokus + offene Fragen
2. `memory-bank/progress.md` — erledigt, blockiert
3. `memory-bank/systemPatterns.md` — Architektur, Stack, Patterns

Keine Referenzdateien auto-laden. Nur laden wenn aktuelle Aufgabe explizit eine Reference benötigt.

---

# Active Context
## Aktueller Status (2026-07-28, Session 69 — vLLM-Connector 502-Mehrdeutigkeits-Fix)

- Abgeschlossen: Bug-Fix in `utils/providers/vllm_base.py` — Pfad 3.5 (`start_server`) wartete bei Proxy-502 600 s ohne `vllm-start`-Aufruf, weil `_probe_status()` „Backend down" nicht von „Backend lädt" unterscheiden konnte (Proxy meldet beides als 502). Neue Methode `_remote_chat_server_running()` prüft via SSH `pgrep -af 'vllm serve' | grep -v -- '--runner pooling'`; bei `False` → Cold-Start (Pfad 4). 6 neue Tests + 78 bestehende grün. Uncommitted.
- Abgeschlossen: vLLM-Chat-Server (qwen3.6-27B auf :3300) manuell gestartet — war down (Shutdown 01:45), nur Embed lief.
- Nächster Schritt: Connector-Fix committen; dann Hermes 4.3 36B Thinking-Probe (Server-Swap Ornith → Hermes 4.3 36B, card_status → "complete").
- Offen/Risiko: Hermes 4.3 36B card_status "draft" (Thinking-Probe ausstehend); 4 Model Cards ohne Benchmark-Daten (hermes-4-3-36b, hermes-4-70b-fp8, qwen3-coder-30b-a3b-q8, qwen3_5-397b-cloud).
