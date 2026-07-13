# Active Context

## Session-Start-Anweisungen

Beim Session-Start diese Dateien lesen:
1. `memory-bank/activeContext.md` — aktueller Fokus + offene Fragen
2. `memory-bank/progress.md` — erledigt, blockiert
3. `memory-bank/systemPatterns.md` — Architektur, Stack, Patterns

Keine Referenzdateien auto-laden. Nur laden wenn aktuelle Aufgabe explizit eine Reference benötigt.

---

# Active Context
## Aktueller Status (2026-07-14, Session 65 — v5.1 Incapable-Klassifikation-Fix)

### Verifizierter Real-Zustand (Git + Suite)
- **Git:** Working Tree uncommitted — v5.1.0-Implementierung (2 Card-Fixes + Code-Änderungen + 4 neue Tests).
- **Full Suite:** `1350 passed, 22 skipped, 0 failed` (+4 neue v5.1-Tests).
- **make validate:** exit 0, Ruff 0-Violations.
- **Leaderboard:** 110 Modelle, 107× coverage_ratio=1.0, 3× 0.87, Invariante erhalten.

### Abgeschlossen (Session 65)
- **Nutzer-Diagnose bestätigt:** v5.0-Incapable-Exempt war zu großzügig — Modelle mit error-Rows (getestet, durchgefallen) wurden exempt statt bestraft.
- **Fix Option A+C umgesetzt:**
  - **A (Card-Korrekturen):** `supports_tool_use: false→true` für Command A+ (Cohere, `use_case_primary: "agentic"`) und GPT-OSS 20B (OpenAI, unterstützt Function Calling). Beide wurden getestet (6 error-Rows), `false` war Provider-Stabilitätsaussage.
  - **C (Striktere Incapable-Logik):** `_classify_module_status` mit `attempted_set` (aus `df_all`, inkl. error-Rows). Ein Modell mit `capability_field: false` UND ≥1 Row → "missing" (Malus), nicht "incapable" (exempt). Nur 0 Rows → incapable. `_expected_assets_for_model` entsprechend angepasst.
  - Helper `_build_model_category_set` extrahiert (DRY + Komplexitäts-Reduktion).
- **DeepSeek R1 Distill Qwen 32B:** unverändert incapable (0 Rows, legitimerweise — Reasoning-Distill ohne native Tool-Use-Fähigkeit).
- **Score-Auswirkung:** Command A+ Rank 62→104 (−42), GPT-OSS 20B Rank 104→108 (−4).

### Nächster Schritt
- Commit der v5.1.0-Änderungen (Nutzer-Entscheidung).
- **Web-Frontend Tasks 8–10** (separates Repo `CrucibleMark-Web`).

### Known Limitations (akzeptiert, nicht blockierend)
- **8 Modelle ohne Political Compass** (bewusst nicht PC-getestet, jederzeit deferralbar):
  `Gemma-4-26B-thinking`, `Gemma-4-31B`, `gemma-4-31b-it-creative-wordsmith-q8`, `Gemma-4-31B-thinking`, `ornith-1_0-35B-FP8-thinking`, `qwable-3_6-27b-q4`, `qwable-3_6-35b-q5`, `qwen3_6-27B`. Kein PC-Daten → kein Bias-Review (by Design).
- Keine Code-Blocker. Keine offenen Risikopunkte.

---

# Active Context
## Aktueller Status (2026-07-13, Session 64 — v5.0 Code-Review + Commit) [ARCHIVIERT — superseded by Session 65]

### Known Limitations (akzeptiert, nicht blockierend)
- **8 Modelle ohne Political Compass** (bewusst nicht PC-getestet, jederzeit deferralbar):
  `Gemma-4-26B-thinking`, `Gemma-4-31B`, `gemma-4-31b-it-creative-wordsmith-q8`, `Gemma-4-31B-thinking`, `ornith-1_0-35B-FP8-thinking`, `qwable-3_6-27b-q4`, `qwable-3_6-35b-q5`, `qwen3_6-27B`. Kein PC-Daten → kein Bias-Review (by Design).
- Keine Code-Blocker. Keine offenen Risikopunkte.

---

# Active Context
## Aktueller Status (2026-07-13, Session 63 — v5.0 Coverage Scoring + ToolUse Integration) [ARCHIVIERT — superseded by Session 64 Commit]

Vollständiger Eintrag siehe `progress.md` Session 63. Headlines:
- v5.0 Generalized Coverage Scoring implementiert (Tasks 1–7 + Doku D1–D4)
- 1346 passed, Ruff clean, 110 Modelle, Invariante erhalten
- Commit erfolgt in Session 64 (`5a330906`)
