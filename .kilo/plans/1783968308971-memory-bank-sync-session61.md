# Plan: Memory-Bank-Sync nach PC-Nachhol-Aktion (Session 61)

## Kontext

Der Nutzer hat am 2026-07-11/12 Political-Compass-Daten für mehrere Modelle
nachgeholt und neue Modelle (`z-ai/glm-5.2`, `moonshotai/kimi-k2.7-code`) ins
Leaderboard integriert. Die Memory-Bank (`activeContext.md`, `progress.md`)
spiegelt diesen Stand **nicht** wider und enthält veraltete/falsche Aussagen.
Dieser Plan sync-t ausschließlich die Doku auf den verifizierten Ist-Stand.
**Keine Code-Änderung, keine Card-Änderung, kein Benchmark-Lauf.**

## Verifizierte Fakten (Grundlage für die Doku)

1. **`qwen3_6-27B-thinking` — PC-Baustelle GESCHLOSSEN:**
   - PC-Eintrag `2026-07-12T15:53` in `political_compass_results.csv`.
   - Bias-Review existiert: `docs/reviews/qwen3_6-27B-thinking/bias_review_20260713_002833.md`.
   - Memory-Bank-Behauptung (activeContext:29, progress Session 60) "3 Modelle
     ohne PC-Daten … qwen3_6-27B-thinking" → **veraltet/falsch**.

2. **Neue PC-Einträge 2026-07-11/12 (in Doku nachziehen):**
   - `Gemma-4-31B-Wordsmith-NVFP4` + `-thinking` (07-11) — Bias-Reviews
     Session-60 bereits gezogen.
   - `grok-4.20-0309-reasoning` (07-11) — Bias-Review `20260712_124109`.
   - `moonshotai/kimi-k2.7-code` (07-12) — Re-Run Bias-Review + Review +
     ToolUse-Narrative (untracked).
   - `z-ai/glm-5.2` (07-12) — neues Modell: PC + Bias-Review + Review +
     ToolUse-Narrative (untracked). Bereits im Leaderboard (Score 74.06).

3. **Git-State korrigieren:** activeContext:25 behauptet "25+ Commits ahead of
   `origin/main`". Realität: **nur 5 Commits ahead** (`[voraus 5]`).

4. **Tatsächlich verbleibende PC-Lücken (Leaderboard, 8 Modelle — nicht 9):**
   - `Gemma-4-26B-thinking`
   - `Gemma-4-31B` (Basis)
   - `gemma-4-31b-it-creative-wordsmith-q8`
   - `Gemma-4-31B-thinking`
   - `ornith-1_0-35B-FP8-thinking`
   - `qwable-3_6-27b-q4`
   - `qwable-3_6-35b-q5`
   - `qwen3_6-27B` (Basis)
   - (Hinweis: ID-Varianten wie `grok-4_20-0309-reasoning` vs `grok-4.20-...`
     bereits via PC-Daten abgedeckt, keine echte Lücke.)

5. **Working-Tree-Status (uncommitted):**
   - 29 modifizierte Model-Cards (Card-Manager-Recherche, nicht Session-60-Only).
   - Neue untracked Reviews für `kimi-k2.7-code`, `qwen3_6-27B-thinking`,
     `z-ai/glm-5.2`.
   - activeContext-Behauptung "1 Card + 2 Reviews" → unvollständig.

## Aufgaben (Reihenfolge einhalten)

### Aufgabe 1 — `memory-bank/activeContext.md` aktualisieren
- Header-Datum/status auf "Session 61 (2026-07-13) — PC-Nachhol-Verifikation"
  setzen.
- "Aktueller Zustand" korrigieren:
  - Working Tree: 29 modifizierte Cards + neue untracked Reviews (nicht "1 Card
    + 2 Reviews").
  - Branch: **5 Commits ahead of `origin/main`** (nicht 25+).
  - Bias-Reviews neu: WordSmith-NVFP4 (Standard+Thinking), grok-4.20-reasoning,
    kimi-k2.7-code (Re-Run), glm-5.2 (neu), qwen3_6-27B-thinking (neu).
- "Offen/Risiko" korrigieren:
  - PC-Lücken-Liste von "9 (7 VSPK + 2 SPRK)" → **8 Modelle** (siehe Fakt 4).
  - `qwen3_6-27B-thinking` aus der "3 Modelle ohne Bias-Review"-Liste
    **streichen** (PC + Bias-Review vorhanden).
  - Verbleibend ohne Bias-Review (PC fehlt): `Gemma-4-26B-thinking`,
    `Gemma-4-31B`, `gemma-4-31b-it-creative-wordsmith-q8`, `Gemma-4-31B-thinking`,
    `ornith-1_0-35B-FP8-thinking`, `qwable-3_6-27b-q4`, `qwable-3_6-35b-q5`,
    `qwen3_6-27B`.
- "Nächster Schritt" anpassen: kein offener Dev-Auftrag; bei Freigabe Push nach
  `origin/main`. Neue Modelle `glm-5.2`/`kimi-k2.7-code` sind bereits
  integriert (kein Folge-Schritt nötig).

### Aufgabe 2 — `memory-bank/progress.md` Session-61-Eintrag vorne anfügen
- Neuer Abschnitt "### 2026-07-13 (Session 61) — PC-Nachhol-Verifikation +
  Memory-Bank-Sync [DONE, uncommitted]".
- Inhalt (kompakt):
  - Auslöser: Nutzer-Vermerk, PC gestern nachgeholt; Memory-Bank veraltet.
  - Verifikation gegen CSV/Audit-Logs (kein Code-Run).
  - Ergebnis: `qwen3_6-27B-thinking` PC-Lücke geschlossen (07-12); neue PC-Daten
    für WordSmith-NVFP4 (±thinking), grok-4.20-reasoning, kimi-k2.7-code,
    glm-5.2; 8 (nicht 9) verbleibende PC-Lücken; Branch 5 (nicht 25+) ahead.
  - Neue Modelle im Leaderboard: `z-ai/glm-5.2` (74.06), `moonshotai/kimi-k2.7-code`
    (77.15), `grok-4.20-0309-reasoning` (69.4) — bereits integriert.
  - Keine Code-Änderung; reiner Doku-Sync.
- Im bestehenden Session-60-Eintrag einen **"Nachtrag Session 61"-Hinweis** mit
  Verweis setzen, dass die dortigen "3 Modelle ohne PC"-Liste teilweise
  überholt ist (`qwen3_6-27B-thinking` inzwischen mit PC).

### Aufgabe 3 — Konsistenzprüfung (nicht-mutierend)
- Nach den Edits: `grep -n "25+\|9 vLLM\|7 vLLM\|qwen3_6-27B-thinking" memory-bank/*.md`
  — darf keine veralteten Behauptungen mehr liefern (außer im gekennzeichneten
  historischen Session-60-Text mit Nachtrag).
- Sicherstellen, dass keine Quelldatei außerhalb `memory-bank/` berührt wird.

## Out of Scope
- Keine PC-Läufe für die 8 verbleibenden Modelle (Nutzer-Entscheidung /
  Nutzer-Aktion).
- Keine Card-Migration oder Review-Generierung.
- Kein Commit/Push (nur bei expliziter Nutzerfreigabe).
- Keine Aktualisierung von README/CHANGELOG (kein Release).

## Validierung
- `activeContext.md` und `progress.md` widersprechen sich nicht mehr.
- Alle numerischen Behauptungen (Commits-ahead, PC-Lücken-Anzahl) stimmen mit
  `git status -sb` bzw. CSV-Vergleich überein.
- `qwen3_6-27B-thinking` erscheint nirgendwo mehr als "ohne PC/Bias-Review".

## Offene Fragen
- Keine (Scope via Nutzer klar: Memory-Bank-Sync only).
