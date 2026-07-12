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
## Aktueller Status (2026-07-12, Session 60 — WordSmith Bias-Reviews nachgeholt)

- **Session 60 (DONE, uncommitted):** WordSmith-NVFP4 Bias-Reviews nachgeholt (Standard + Thinking). Card-Fix: `origin_country` + `developer_jurisdiction` auf US/USA (Basis Google DeepMind). 3 weitere Modelle (`Gemma-4-31B` Basis, `qwen3_6-27B`, `qwen3_6-27B-thinking`) ohne PC-Daten → Bias-Review nicht möglich, Skript-Skip sauber. Review-Skript fehlerfrei (Dry-Run + Live + Skip-Pfade verifiziert).

### Aktueller Zustand
- **Working Tree:** uncommitted (Session 60: Card-Fix + 2 Bias-Reviews).
- **Version:** v4.10.18 — Production-Ready.
- **Tests:** Review-Tests 32/32 grün; Full Suite 1462 passed, 1 pre-existing flaky ToolUse-Test.
- **Export-Stats:** 88 Modelle, 23 blacklisted, 9 Score-Keys.
- **Bias-Reviews neu:** 2 (WordSmith-NVFP4 Standard + Thinking).
- **Branch:** 25+ Commits ahead of `origin/main` (unpushed).

### Offen/Risiko
- 7 vLLM + 2 SPRK Modelle ohne Political Compass (Nutzer-Aktion — vLLM-Compass-Daten erfassen, nicht code-seitig lösbar).
- 3 Modelle ohne PC-Daten → ohne Bias-Review: `Gemma-4-31B` (Basis), `qwen3_6-27B`, `qwen3_6-27B-thinking`.
- Branch ist 25+ Commits ahead of `origin/main` — Push ausstehend.

### Nächster Schritt
- Kein offener Dev-Auftrag. Bias-Review-Gaps nicht code-seitig lösbar (brauchen PC-Läufe). Push nach `origin/main` bei Freigabe.
