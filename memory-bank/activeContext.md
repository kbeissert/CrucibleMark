## SESSION START INSTRUCTIONS

On every new session, read these files in this order:
1. `memory-bank/activeContext.md`  — current focus and open questions
2. `memory-bank/progress.md`       — what is done, what is blocked
3. `memory-bank/systemPatterns.md` — architecture, stack, patterns

Do NOT auto-read reference files. Only load a reference file when the current
task explicitly requires it. Check `memory-bank/reference/_index.md`
to know what reference files exist.

---

# Active Context
## Aktueller Status (2026-07-09, Session 56 — Hardware-Context-Fix)

- **Session 56 (DONE, uncommitted):** `{hardware_context}`-Datenfeld korrekt pro-Modell befüllt. Vier Fixes:
  1. **Fehlendes Profil:** `asus_gx10_blackwell` (vllm_spark) fehlte in `benchmark_config.yaml` → Fallback auf M4. Hinzugefügt + `dgx_spark_cuda`-Beschreibung aktualisiert ("kein praktisches Speicherlimit").
  2. **Local-Template konditional:** `system_context.py` bei `ram_gb < 64` → "Swapping-Risiken" (M4); bei `ram_gb >= 64` → "Speicher ist hier kein Engpass" (Spark/GX10).
  3. **CSV-Fallback:** `_get_hardware_profile_from_csv()` in `generate_review.py` — liest `hardware_profile` aus roher CSV wenn Provider-Config-Lookup leer (auskommentierte Modelle).
  4. **Example-Datei:** `benchmark_config.example.yaml` um Spark/GX10-Profile ergänzt.
- **Externe Audit-Analyse (Session 56):** Reviews für Spark/GX10-Modelle zitierten "Apple Silicon M4, 24GB Unified Memory". Ursache: `asus_gx10_blackwell`-Profil fehlte → Fallback auf `active_profile`. Die Sperrklausel im Prompt war korrekt, aber das Datenfeld lieferte die falsche Hardware.
- **Tests:** 1125 passed, 1 skipped, 1 pre-existing failure (`qwen3_5-35b-a3b-q8`). `make validate` exit 0.
- **Session 55 (DONE, uncommitted):** `thinking_mode` dreifach sichtbar (CSV, Audit-Log, Review-Prompt).
- **Session 54 (DONE, uncommitted):** Display-Name-Fix + `thinking_mode`-Spalte + `-thinking`-Suffix-Fallback.
- **Session 53 (DONE, uncommitted):** card_model_id-Drift im Web-Export behoben.
- **Session 52 (DONE, uncommitted):** vLLM Dual-Thinking-Profile implementiert.
- **Nächster Schritt:** Working Tree committen (Session-52 bis 56, v4.10.15-Bump). Thematische Aufteilung, nur auf explizite Anfrage.
- **Offen/Risiko:** Working Tree uncommitted (alle 6 Sessions). vLLM-TOML-Änderung auf GX10 (`--default-chat-template-kwargs` entfernt, nicht im Git). Pre-existing uncommitted: `qwen3_5-35b-a3b-q8` + `gemma-4-26B-A4B-it-UD-Q8_K_XL` auskommentiert.
