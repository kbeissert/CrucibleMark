---
agent: agent
description: "CrucibleMark: Memory Bank nach Session aktualisieren (Qualität vor Vollständigkeit)"
---

Aktualisiere das Projekt-Wissen für CrucibleMark. **Qualität vor Vollständigkeit —
lieber nichts schreiben als etwas Falsches oder Triviales.**

## 0. Versionssynchro (immer zuerst, wenn eine neue Version vergeben wurde)

Wurde in dieser Session eine neue Versionsnummer vergeben (erkennbar an einem neuen
`[v3.x.y]`-Block im CHANGELOG oder an einem neuen Meilenstein in `progress.md`)?
Dann **alle sieben Stellen synchron** auf die neue Versionsnummer bringen:

| Datei | Stelle |
|---|---|
| `README.md` | Version-Badge `version-X.Y.Z` + Footer `Status: ✅ Production-Ready (vX.Y.Z)` |
| `PROJECT_STATUS.md` | `**Current Version:**` + `**Last Updated:**` |
| `CHANGELOG.md` | Neuer `## [vX.Y.Z] - DATUM`-Block ganz oben |
| `REF_TODO.md` | Neuer Abschnitt `### <Titel> (vX.Y.Z – DD.MM.YY)` unter "Abgeschlossen" |
| `scripts/web_export.py` | `"cruciblemark_version": "X.Y.Z"` (Zeile ~554) |
| `memory-bank/activeContext.md` | Versionsnennung im Abgeschlossen-Block |
| `memory-bank/progress.md` | Neuer `[DONE] vX.Y.Z`-Meilenstein-Eintrag |

Keine neue Version in dieser Session? → diesen Schritt überspringen.

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

**Vollständig überschreiben** mit folgendem Schema:

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

Bestätige abschließend mit: **"Memory updated ✓"**
