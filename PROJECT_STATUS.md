# PROJECT_STATUS.md

> **Interner Statusbericht.** Diese Datei dokumentiert den Projektfortschritt für Maintainer und Contributor. Sie ist nicht Teil der öffentlichen Dokumentation. Aktuelle, kuratierte Release-Informationen stehen in [README.md](README.md) (Recent Versions) und [CHANGELOG.md](CHANGELOG.md).

**Last Updated:** 2026-08-02
**Current Version:** 5.1.0 — Striktere Incapable-Klassifikation + Coverage-Malus-Bugfix + Prozessdisziplin Model Cards
**Status:** Production-Ready

---

## Executive Summary

CrucibleMark v5.1.0 ist ein production-ready LLM-Benchmark-Framework mit 110+ getesteten Modellen über 11 Provider. Das Framework misst praxisnahe Leistung (Code-Reviews, UX-Texte, Reasoning, Tool-Use, Political Compass) mit blindem LLM-Judge und generiert Leaderboards mit License-/Sovereign-Filtern.

**Aktueller Stand (2026-08-02):**
- **110+ Modelle** im Leaderboard, davon 88 im Web-Export (restliche geblacklisted: Quant-Vergleichstests, experimentelle Modelle, superseded vLLM-Versionen).
- **11 Provider:** OpenAI, Anthropic, Google, Mistral, xAI, OpenRouter, Cohere, Ollama, Llama.cpp, Spark (llamacpp), vLLM (Spark).
- **8 Scoring-Module** + Political Compass (separat): Code Quality, CLI Operations, Reasoning & Logik, UX Writing, Cultural Intelligence, Documentation Quality, Content Transformation, Tool Use.
- **Web-Export:** 88 Modelle, 0 Vendor-Warnungen, 9 Score-Keys, Eleventy-Build 366 Dateien, 0 Errors.
- **1316+ Tests** grün, Ruff 0-Violations, Pylint ≥ 9.99/10.

**Aktuelle Modell-Integrationen (Sessions 73–75):**
- **Laguna S 2.1 NVFP4** — selektives Reasoning-Modell (Rank 92, Score 69.1%, Silver Badge). Dual-Profile entfernt: Laguna denkt pro Request selbst, kein Always-Thinking.
- **Hermes 4.3 36B (Seed-OSS)** — Dual-Profile (Standard Rank 98, Thinking Rank 103). Apache-2.0, 36B Dense, BF16, vLLM.
- **qwen3_6-27B → qwen3_6-27B-pre025** — historischer Rename für vLLM-Versionsmarker. ToolUse-Timestamp-Bugfix (Path B überschrieb `tested_at` nicht mehr).

**Known Limitations (akzeptiert, nicht blockierend):**
- 8 Modelle ohne Political Compass-Daten (Gemma-4-26B-thinking, Gemma-4-31B, gemma-4-31b-it-creative-wordsmith-q8, Gemma-4-31B-thinking, ornith-1_0-35B-FP8-thinking, qwable-3_6-27b-q4, qwable-3_6-35b-q5, qwen3_6-27B). Deferralbar via `run_political_compass_benchmark`.
- Political Compass `raw_response` trunciert auf 2–3 Zeichen (nur `answer`-Feld vertrauen).
- Web-Frontend (separates Repo): `price-comparison-row.njk` Null-Guard, `model-header.njk` Doppel-Rendering, Frontend stu=false-Score-Anzeige.

---

## Recent Releases

### v5.1.0 (2026-07-14) — Striktere Incapable-Klassifikation

Fixt einen Design-Defekt aus v5.0: Modelle mit `supports_tool_use: false` wurden pauschal als "incapable" exempt, selbst wenn sie getestet wurden und fehlschlugen. Jetzt gilt "incapable" nur, wenn das Modell null Rows für das Modul hat. `attempted_set` aus `df_all` prüft, ob ein Modell angetreten ist. Zwei Cards korrigiert (Command A+ und GPT-OSS 20B). Command A+ fällt von Rang 62 auf Rang 104.

⚠️ **Breaking Change.** Total Scores und Rankings ändern sich für betroffene Modelle.

### v5.0.0 (2026-07-13) — Generalized Coverage Scoring + ToolUse Integration

ToolUse wird als vollwertiges achtes Scoring-Modul integriert (`enable_scoring: true`, `module_weight: 1.0`). Die Coverage-Logik wurde generalisiert: missing- und unknown-Module lösen einen Malus aus, incapable-Modelle bleiben exempt, rolling_out- und not_deployed-Module sind für alle ausgeschlossen. Neue `coverage_ratio`-Spalte. Per-Modell-`Tests Run`-Erwartung (incapable reduziert). Invariante `Routine + Reasoning = Total` erhalten.

⚠️ **Breaking Change.** Total Scores und Rankings ändern sich.

### v4.10.18 (2026-07-11) — Framework-Refactoring + Ruff 0-Violations

Systematisches Refactoring gegen die Architektur-Regeln: `model_utils.py` zerlegt in sieben Submodule mit Re-Export-Bridge, `web_export.py` als Package, `yaml.safe_load` durch `ConfigValidator` in 15 Skripten ersetzt, 131 `print`-Aufrufe auf `logging` migriert. 27 Legacy-Skripte nach `scripts/legacy/` verschoben. Ruff-Verstöße 252 → 0. Bugfix für doppelte Base-Cards bei suffixed Modellen. 1316 Tests grün, verhaltenserhaltend.

---

Die vollständige Versionshistorie steht in [CHANGELOG.md](CHANGELOG.md).
Detaillierte Session-Historie steht in [memory-bank/progress.md](memory-bank/progress.md).
