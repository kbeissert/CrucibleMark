---
description: Analysiert Git-Änderungen und erstellt eine Commit-Message
---

Analysiere die ausstehenden Git-Änderungen und erstelle eine
Commit-Message. Führe keinen Commit aus. Gib ausschließlich
die fertige Commit-Message als Codeblock aus.

## Analyse

Prüfe in dieser Reihenfolge:

1. Ausstehende Änderungen ermitteln:
   Führe `git status` aus und erfasse alle geänderten,
   hinzugefügten oder gelöschten Dateien.

2. Diff der geänderten Dateien abrufen:
   Führe `git diff` (und `git diff --staged`, falls nötig) aus
   und analysiere den Inhalt der Änderungen.

3. Letzte Commits als Stilreferenz prüfen:
   Führe `git log --oneline -n 5` aus, um den Stil der letzten
   Commit-Messages als Orientierung zu nutzen.

Identifiziere aus Status und Diff:
- Welche Dateien wurden geändert, hinzugefügt (`A`) oder
  gelöscht (`D`)?
- Welcher Änderungstyp passt:
  Neues Feature / Bugfix / Dokumentation / Formatierung /
  Refactoring / Konfiguration?
- Welcher Bereich oder Modul ist betroffen
  (z. B. `src/pages/scoreboard`, `.kilo/command`,
  `memory-bank`)?
- Gibt es Breaking Changes (entfernte Klassen, geänderte
  Dateinamen, strukturelle Umbauten)?

## Commit-Message-Format

Orientiere dich am Stil der letzten vorhandenen Commit-Messages
(`git log --oneline -n 5`). Das Projekt folgt Conventional
Commits. Falls keine klare Konvention erkennbar ist, nutze
dieses Format:

```
<type>(<scope>): <Kurzbeschreibung der Änderung>

- Detail 1
- Detail 2
```

Erlaubte Typen: `feat`, `fix`, `docs`, `style`, `refactor`,
`perf`, `test`, `build`, `ci`, `chore`, `content`.

Regeln:å
- Erste Zeile (Subject): max. 72 Zeichen, Imperativ,
  kein Punkt am Ende
- Body nur bei mehreren unabhängigen Änderungen
- Sprache: Deutsch (entsprechend dem Projektkontext)
- Kein Kommentar, keine Erklärung der Entscheidungen
- Keine Co-Authored-by-Zeilen und keine Issue-Referenzen
  ergänzen, sofern nicht aus dem Diff eindeutig ableitbar
