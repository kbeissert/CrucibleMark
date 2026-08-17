# PROJECT_STATUS.md

> **Interner Statusbericht.** Diese Datei dokumentiert den Projektfortschritt für Maintainer und Contributor. Sie ist nicht Teil der öffentlichen Dokumentation. Aktuelle, kuratierte Release-Informationen stehen in [README.md](README.md) (Recent Versions) und [CHANGELOG.md](CHANGELOG.md).

**Last Updated:** 2026-08-17
**Current Version:** 5.1.5 — Echte-Token-Pipeline (TPS, Judge, Audit-Log)
**Status:** Production-Ready

---

## Executive Summary

CrucibleMark v5.1.5 ist ein production-ready LLM-Benchmark-Framework mit 120+ getesteten Modellen über 11 Provider. Das Framework misst praxisnahe Leistung (Code-Reviews, UX-Texte, Reasoning, Tool-Use) mit blindem LLM-Judge und generiert Leaderboards mit License-/Sovereign-Filtern.

**Aktueller Stand (2026-08-17):**
- **120+ Modelle** im Leaderboard (Naming-Gate: 123 Cards OK), Web-Export nach Blacklist-Reduktion (Quant-Vergleichstests, experimentelle Modelle, superseded vLLM-Versionen).
- **11 Provider:** OpenAI, Anthropic, Google, Mistral, xAI, OpenRouter, Cohere, Ollama, Llama.cpp, Spark (llamacpp), vLLM (Spark).
- **8 Scoring-Module:** Code Quality, CLI Operations, Reasoning & Logik, UX Writing, Cultural Intelligence, Documentation Quality, Content Transformation, Tool Use. Political Compass seit v5.1.3 deaktiviert (`enabled: false`).
- **1572 Tests** grün, Ruff 0-Violations, Pylint ≥ 9.99/10.

**Aktuelle Modell-Integrationen (Sessions 82–84):**
- **Qwen 3.8 27B NVFP4** (lokal, vLLM gx10) — Standard-Profil Rank 63, Score 72.25, Silver Badge. Thinking-Profil im Benchmark (Dual-Profile-Expansion).
- **Qwen3.8 2.4T A95B** (OpenRouter, Cloud) — Rank 115, Score 67.23, Silver Badge.
- **Echte-Token-Pipeline (v5.1.5):** TPS, Judge-Context und Audit-Log laufen jetzt auf echten Provider-Usage-Werten (`input_tokens`/`output_tokens`).

**Known Limitations (akzeptiert, nicht blockierend):**
- **TPS-Semantik-Wechsel v5.1.5:** Historische CSV-Zeilen behalten Schätzwerte (Upsert rechnet nicht neu durch) — Leaderboard mischt alte/neue TPS, bis Modelle neu gelaufen sind.
- **Political Compass deaktiviert (seit v5.1.3):** 8 Modelle ohne PC-Daten; Re-Aktivierung via `benchmark_config.yaml` + `run_political_compass_benchmark`.
- **Datenlücke:** qwen3_8-27b-nvfp4 / code_quality_001-Row fehlt (durch Simulations-Write ersetzt, nicht restaurierbar) — Modul-Neulauf ausstehend.
- Web-Frontend (separates Repo): `price-comparison-row.njk` Null-Guard, `model-header.njk` Doppel-Rendering, Frontend stu=false-Score-Anzeige.

---

## Recent Releases

### v5.1.5 (2026-08-17) — Echte-Token-Pipeline (TPS, Judge, Audit-Log)

`tokens_per_second` lief aus der Modul-Schätzung (Wörter × 1.3, ohne Thinking), während `tokens_used` die echten Provider-Usage-Werte enthielt — zwei Spalten, zwei Token-Zahlen. Jetzt: TPS = `output_tokens / execution_time` (inkl. Thinking), neue CSV-Spalten `input_tokens`/`output_tokens`, Judge-Context + Audit-Log mit echter Breakdown, Visible-Output-Formel fixt (`output_tokens − reasoning_tokens`). Provider lieferten bereits echte Usage — keine Provider-Änderung. 1572 Tests grün (+12 neue), Lint 0, Naming-Gate 123 Cards OK.

### v5.1.4 (2026-08-15) — Code-Review-Umsetzung (Sicherheit, Konsistenz, Robustheit)

23-Findings-Review umgesetzt: 5 kritische Fixes (Ollama-Loop-Break, lifecycle_hooks-Logging, combined_score-0.0-Fallback, doppelter probe_thinking-Key, Preis-Split-Bug mit neuer SSoT `config/model_pricing.yaml`), Shell-Injection-Flächen geschlossen, exponentieller Rate-Limit-Backoff, Judge-Prompt Name-Priming entfernt (Blind-Evaluierung), 8 C901-Verstöße verhaltenstreu aufgesplittet, Ruff 409→0, DRY-Konsolidierung (`utils/provider_config_text.py`), ConfigValidator-mtime-Cache, Maintenance-Skripte gehärtet. 1411 Tests grün, Naming-Gate 122 Cards OK.

### v5.1.3 (2026-08-15) — Test-Suite-Reparatur & Card-Vocabulary-Normalisierung

Drei vorbestehende Testfehler behoben: hermes-4-36b Orphan-Draft-Card via `make clean-model` entfernt; Architecture-Tags gegen Vocabulary-SSoT normalisiert (`Native-Quant`/`Harmony` neu, `Configurable-Reasoning`/`Thinking-Mandatory` deprecated); Ornith-Test als llamacpp-Invariante für Re-Aktivierungen umgeschrieben. Maintenance-Fixes aus Sessions 74/75 integriert. `political_compass` deaktiviert. 1410 Tests grün.

---

Die vollständige Versionshistorie steht in [CHANGELOG.md](CHANGELOG.md).
Detaillierte Session-Historie steht in [memory-bank/progress.md](memory-bank/progress.md).
