---
description: >-
  Komprimierte Zusammenfassung des Projekts generieren. Architektonische
  Entscheidungen, kritische Bugs, offene Todos — gruppiert und verdichtet.
subtask: true
---

## Zweck
Wird der Nutzer-Kontext zu groß oder unübersichtlich, ruft der Nutzer
diesen Befehl explizit auf. Er ersetzt kein automatisches System-Feature,
sondern liefert auf Anfrage eine verdichtete Zusammenfassung.

## Ablauf bei Aufruf
1. Durchsuche PROJECT_STATUS.md und README.md (sowie relevante CSVs, falls
   Datenstruktur-Fragen offen sind).
2. Extrahiere ausschließlich:
   - architektonische Entscheidungen (SSoT-Prinzipien, Card-First, Tiers)
   - kritische Bugs mit Ursache + Fix (kein Rohlog, keine Commit-Hashes)
   - offene Todos / Roadmap-Punkte
3. Verwerfe: Versionsnummern-Rauschen, Testzähler, Zeilen-Diffs, Wortlaut-
   Zitate aus Changelogs.
4. Ausgabe als max. 15 Bulletpoints, gruppiert in drei Abschnitte:
   Architektur / Bugs / Todos.

## Wann nutzen
- Vor dem Start einer neuen Session zu Web-Frontend-Arbeit.
- Wenn die History zu lang für schnelle Orientierung wird.
- Nicht automatisch — nur auf expliziten Aufruf.
