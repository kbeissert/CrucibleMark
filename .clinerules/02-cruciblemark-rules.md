# CrucibleMark — Projektspezifische Regeln

## Architektur & Struktur
- Memory Bank IMMER vor einer neuen Task lesen: ActiveContext.md, progress.md, techContext.md, systemPatterns.md
- Keine Änderungen an BaseTest-Erbschema ohne explizite Bestätigung
- Judge-Phase und Test-Phase strikt trennen – kein gemeinsamer State
- Konfiguration ausschließlich über Config-Files, nie hardcodiert

## Code-Stil
- Type hints in ALLEN neuen Funktionen (Python)
- Bestehende Pytest-Fixtures wiederverwenden, keine Duplikate anlegen
- Modulnamen konsistent mit bestehender Verzeichnisstruktur halten
- Keine neuen Dependencies ohne Rückfrage – requirements.txt ist bewusst schlank

## Judge & Modell-Logik
- LLM-Blind-Evaluierung beibehalten: Judge kennt Modellnamen während Bewertung NICHT
- Scoring-Logik nie stillschweigend verändern – das verfälscht historische Benchmarks
- Bei API-Calls: Rate-Limiting und Retry-Logik immer mitdenken

## Output & Logging
- Timestamps im ISO-Format (UTC) konsistent verwenden
- Kein Löschen von Log-Dateien oder Ergebnis-CSVs ohne explizite Anweisung
- Anomalie-Kommentare in Ergebnis-Outputs beibehalten
