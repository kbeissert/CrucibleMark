---
name: session-commit
description: >-
  CrucibleMark Memory Bank nach Session aktualisieren. Synchronisiert
  Versionsnummern mit CHANGELOG und aktualisiert activeContext, progress,
  systemPatterns, techContext und copilot-instructions. Qualität vor
  Vollständigkeit — lieber nichts schreiben als etwas Falsches oder Triviales.
---

Aktualisiere das Projekt-Wissen für CrucibleMark. **Qualität vor Vollständigkeit —
lieber nichts schreiben als etwas Falsches oder Triviales.**


## 0. Versionssynchro (immer zuerst ausführen)

**Aktiv prüfen:** Durchsuche `CHANGELOG.md` nach dem neuesten `## [v`-Block und
`memory-bank/progress.md` nach dem neuesten Meilenstein. Wurde dabei eine Version
identifiziert, die noch **nicht** in allen sieben Stellen eingetragen ist?

Wenn ja → alle sieben Stellen synchron auf die neue Versionsnummer bringen:

| Datei | Stelle |
|---|---|
| `README.md` | Version-Badge `version-X.Y.Z` + Footer `Status: ✅ Production-Ready (vX.Y.Z)` |
| `PROJECT_STATUS.md` | `**Current Version:**` + `**Last Updated:**` |
| `CHANGELOG.md` | Neuer `## [vX.Y.Z] - YYYY-MM-DD`-Block ganz oben (ISO-Datum) |
| `REF_TODO.md` | Neuer Abschnitt `### <Titel> (vX.Y.Z – DD.MM.YY)` unter "Abgeschlossen" |
| `scripts/web_export.py` | String `"cruciblemark_version":` suchen und Wert anpassen |
| `memory-bank/activeContext.md` | Versionsnennung im Abgeschlossen-Block |
| `memory-bank/progress.md` | Bestehenden Meilenstein als `[DONE] vX.Y.Z` markieren |

**Abschluss-Check:** Liste nach der Synchro explizit alle sieben Dateien mit ✅ oder ⏭️ (übersprungen) auf, bevor du weitermachst.

Alle Stellen bereits aktuell? → Schritt überspringen, kurz bestätigen: *"Version bereits synchron."*


## Schreibfilter (vor jedem Eintrag prüfen)

Nur dokumentieren wenn **mindestens eines** zutrifft:
- Es war ein nicht-offensichtliches Problem, das Zeit gekostet hat
- Es ist eine Entscheidung, die man in 3 Monaten nicht mehr rekonstruieren kann
- Es beeinflusst direkt den nächsten Schritt

Nicht dokumentieren:
- Standard-Python- oder Framework-Verhalten
- Dinge, die im Code selbst bereits klar ersichtlich sind
- Einzel-Fixes ohne Wiederholungsrisiko

---

## 1. `.github/copilot-instructions.md` — Fallstricke & Verbote

Nur ergänzen wenn ein **neuer, nicht-offensichtlicher Fallstrick** aufgetreten ist,
der noch nicht im Conventions-Abschnitt steht. Max. 1–2 Sätze, ein Satz pro Eintrag.
Kein neuer Fallstrick? → Nicht anfassen.


## 2. `memory-bank/systemPatterns.md` — Architekturentscheidungen

Nur ergänzen wenn heute eine **neue Architekturentscheidung** getroffen wurde
oder ein bestehendes Pattern sich als falsch erwiesen hat.
Kein struktureller Wandel? → Nicht anfassen.


## 3. `memory-bank/activeContext.md` — Aktueller Stand

**Vollständig überschreiben** (vorheriger Inhalt wird ersetzt — stelle sicher,
dass "Nächster Schritt" aus dem alten Stand nicht verloren geht, falls er noch relevant ist):

```
- Abgeschlossen: [was — max. 2 Zeilen]
- Nächster Schritt: [konkret, ein Satz]
- Offen/Risiko: [was — oder "keine"]
```


## 4. `memory-bank/progress.md` — Nur aktueller Zustand

- Laufende Tasks: Status aktualisieren (`[ ]` → `[DONE]` oder Fortschritt ergänzen)
- Abgeschlossene Meilensteine: **Nicht neu anlegen** — nur bestehende als `[DONE]` markieren
- Neue Tasks **nur** ergänzen wenn sie den nächsten logischen Schritt darstellen
- Kein Changelog, keine Erklärungen — nur Status


## 5. `memory-bank/techContext.md` — Stack & Tools

Nur anfassen bei **neuer Dependency**, geändertem Build-Befehl oder neuem Tool.
Sonst: nicht ändern.

---

Bestätige abschließend mit: **"Memory updated ✓"** + einer einzeiligen Summary
was geändert wurde (z.B. *"v3.5.0 sync: 7/7 ✅ | activeContext überschrieben | 1 neuer Task in progress.md"*).
