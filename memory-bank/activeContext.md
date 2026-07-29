# Active Context

## Session-Start-Anweisungen

Beim Session-Start diese Dateien lesen:
1. `memory-bank/activeContext.md` — aktueller Fokus + offene Fragen
2. `memory-bank/progress.md` — erledigt, blockiert
3. `memory-bank/systemPatterns.md` — Architektur, Stack, Patterns

Keine Referenzdateien auto-laden. Nur laden wenn aktuelle Aufgabe explizit eine Reference benötigt.

---

# Active Context
## Aktueller Status (2026-07-29, Session 71 — vLLM-Connector Thinking-Profile-Adoption-Fix)

- Abgeschlossen: Bug-Fix in `utils/providers/vllm_base.py` — zwei gekoppelte Bugs beim Starten des Thinking-Profils (Eintrag 12: `qwen3_6-35b-a3b-nvfp4-thinking`), wenn der Server bereits mit `Qwen3.6-35B-NVFP4` lief. Commit `fd386047` auf main.
  - **Bug 1 (Root Cause):** `_adopt_matches()` erkannte das Thinking-Profil nicht als dasselbe Backend (Substring-Match scheiterte an `a3b`/`thinking`-Segmenten) → unnötiger Stop+Restart (Pfad 2c). Fix: zusätzlicher Match gegen den Config/TOML-Namen (`_config_arg`).
  - **Bug 2 (sekundär, latent):** Post-Stop-Verifikation prüfte `_probe_status() == "down"`, was bei permanentem Proxy (4300→3300) nie eintritt (502→`"loading"`). Fix: neue Methode `_backend_stopped()` kombiniert `_probe_status()` mit `_remote_chat_server_running()` (SSH-Prozess-Check). Eingebaut in Pfad 2c, Pfad 3, `swap_model`.
- Validiert: Smoketest-Adoption in 0.6s (vs. 5-10min Restart), Benchmark `code_quality`-Modul läuft fehlerfrei über Server-Start-Phase. 120 Tests grün (6 neue Regression-Tests + 1 Integrationstest).
- Nächster Schritt: Hermes 4.3 36B Thinking-Probe (Server-Swap Ornith → Hermes 4.3 36B via `vllm-stop` + `vllm-start --config Hermes4.3-36B`, dann `make probe-thinking MODEL=hermes-4-3-36b PROVIDER=vllm`), card_status → "complete".
- Offen/Risiko: Hermes 4.3 36B card_status "draft" (Thinking-Probe ausstehend); 4 Model Cards ohne Benchmark-Daten (hermes-4-3-36b, hermes-4-70b-fp8, qwen3-coder-30b-a3b-q8, qwen3_5-397b-cloud); 12 Commits unpushed.
