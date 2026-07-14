# Plan: Memory-Bank-Baustellen-Cleanup (Session 62)

## Kontext & Befunde (verifiziert am 2026-07-13)

Vier Baustellen aus der Session-61-Zusammenfassung sollen so aufgelöst werden,
dass sie nicht mehr als *offene* Baustellen in der Memory Bank stehen. Reale
Lage (gegenüber Memory Bank):

- **#3 Ungepushter Zustand — BEREITS ERLEDIGT.** `git status` = clean,
  `0 commits ahead of origin/main`, alles gepusht (Head `0554ce59` = Session 61).
  Memory-Bank-Behauptung "5 ahead / uncommitted" ist veraltet.
- **#4 Flaky ToolUse-Test — NICHT REPRODUZIERBAR.** Full Suite:
  `1320 passed, 22 skipped, 0 failed` (deterministisch; `pytest-randomly` nicht
  installiert). Tooluse-spezifisch: 78 passed. Behauptung "1462 passed / 1 flaky"
  ist veraltet/inkorrekt.
- **#1 Widerspruch PC-Lücken — im Log bereits korrigiert.** Session 60 nennt
  "3 weitere Modelle ohne PC-Daten" inkl. `qwen3_6-27B-thinking`; Session 61
  korrigiert per Nachtrag (das Modell hat seit 07-12 PC-Daten, 8 nicht 9 fehlen).
  Session-60-Eintrag trägt den Nachtrag. Widerspruch ist historisch aufgelöst.
- **#2 8 PC-Lücken — REAL, bestätigt.** Alle 8 Modelle haben 0 Einträge in
  `political_compass_results.csv`. Lokale Modelle (llama.cpp / vllm_spark); PC-Runs
  brauchen Hardware + geladene Gewichte. **Nutzer-Entscheidung: als Known
  Limitation akzeptiert, keine Runs.**

## Ziel

Memory Bank (activeContext + progress) spiegelt die Realität; die vier Punkte
stehen nicht mehr als *offene/aktive* Baustellen. Historische Log-Einträge
(Session 60/61) bleiben unverändert (Nachtrag als Korrektur erhalten).

## Aufgaben (nur Memory-Bank-Doku, kein Code)

### 1. `memory-bank/activeContext.md` neu fassen
Aktuelle Datei ist 28 Zeilen, "Offen/Risiko"-Sektion trägt 3 veraltete Punkte.
Vollständiger Ersatz durch Fassung mit:

- **Aktueller Status (2026-07-13, Session 62 — Baustellen-Reconciliation):**
  - Git: clean, `0 commits ahead of origin/main`, alles gepusht (Head `0554ce59`).
  - Full Suite verifiziert: `1320 passed, 22 skipped, 0 failed` (deterministisch).
  - Flaky-Test-Behauptung (Session 61) war veraltet — nicht reproduzierbar.
- **Abgeschlossen (Session 62):** Reconciliation der 4 Baustellen aus
  Session-61-Zusammenfassung; Memory-Bank-Sync auf Real-Zustand.
- **Nächster Schritt:** Clean slate — bereit für nächste Dev-Aufgabe. Kein offener
  Auftrag.
- **Known Limitations (akzeptiert, nicht blockierend):**
  - **8 Modelle ohne Political Compass** (bewusst nicht PC-getestet, deferralbar):
    `Gemma-4-26B-thinking`, `Gemma-4-31B`, `gemma-4-31b-it-creative-wordsmith-q8`,
    `Gemma-4-31B-thinking`, `ornith-1_0-35B-FP8-thinking`, `qwable-3_6-27b-q4`,
    `qwable-3_6-35b-q5`, `qwen3_6-27B`. Können jederzeit via
    `run_political_compass_benchmark` nachgeholt werden; kein Code-Blocker.
  - Keine PC-Daten → kein Bias-Review für diese 8 (by Design: PC ist
    Vorbedingung, siehe `progress.md` Session 60).
- **Verifikation:** `pytest tests/ -q` → 1320 passed/22 skipped/0 failed;
  `git status` clean; `git rev-list --count origin/main..HEAD` = 0.

### 2. `memory-bank/progress.md` — Session-62-Eintrag anhängen
Neuer Eintrag *oben* (vor Session 61), Format analog bestehender Einträge:

- **Titel:** `### 2026-07-13 (Session 62) — Baustellen-Reconciliation [DONE, uncommitted]`
- **Auslöser:** Vier Baustellen aus Session-61-Zusammenfassung sollten geschlossen
  werden.
- **Geliefert (kein Code):**
  - #3 Ungepusht: verifiziert clean + gepusht (`0554ce59`, 0 ahead). War bereits
    erledigt; Memory-Bank war veraltet.
  - #4 Flaky ToolUse-Test: nicht reproduzierbar. Full Suite 1320 passed/22
    skipped/0 failed (deterministisch, kein pytest-randomly). Behauptung entfernt.
  - #1 Widerspruch PC-Lücken: historisch bereits via Session-60-Nachtrag
    korrigiert; Session-60/61-Einträge bleiben unverändert. Kein aktiver
    Widerspruch mehr in activeContext.
  - #2 8 PC-Lücken: per Nutzer-Entscheidung als Known Limitation akzeptiert
    (keine Runs). In activeContext aus "Offen/Risiko" → "Known Limitations"
    verschoben.
- **Status:** Working Tree, uncommitted (nur Memory-Bank-Doku).

### 3. Historische Einträge NICHT anfassen
- `progress.md` Session 60 (inkl. Nachtrag) und Session 61 unverändert lassen —
  historisches Log, Korrektur durch Nachtrag ist Bestandteil der Aufzeichnung.

## Out of Scope
- Keine Code-Änderungen, kein Release-Bump (bleibt v4.10.18).
- Keine PC-Benchmark-Runs (Nutzer-Entscheidung: Known Limitation).
- Kein automatischer Commit (nur auf ausdrücklichen Nutzerwunsch; CLAUDE.md:
  "NEVER commit unless explicitly asked"). Plan endet mit uncommitted Doku-Änderung.

## Validierung
1. `pytest tests/ -q` → erwartet `1320 passed, 22 skipped, 0 failed`.
2. `git status` → nur `memory-bank/activeContext.md` + `memory-bank/progress.md`
   modified.
3. `git rev-list --count origin/main..HEAD` → `0`.
4. Grep-Check: `activeContext.md` enthält keine der veralteten Aussagen
   ("5 Commits ahead", "flaky", "1462 passed") mehr.
5. `activeContext.md` enthält Sektion "Known Limitations" mit den 8 PC-Modellen.

## Risiken
- **Gering.** Nur Doku; kein Verhaltens-/Score-Einfluss. Historische Log-Integrität
  gewahrt (keine History-Rewrites).
- Falls später doch PC-Runs gewünscht: Known-Limitations-Sektion nennt den
  Run-Befehl; jederzeit nachholbar ohne Code-Änderung.
