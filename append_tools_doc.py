with open("docs/USER_GUIDE.md", "a") as f:
    f.write("\n## F. Tooling & Maintenance Parameter\n\n")
    f.write("CrucibleMark bietet ein umfangreiches Repertoire an Tools, um das Framework sauber und aktuell zu halten:\n\n")
    
    f.write("### 1. Zusätzliche Benchmark- & Test-Aufrufe\n")
    f.write("Neben den regulären `make benchmark` Befehlen existieren folgende Ergänzungen:\n")
    f.write("- **`make run-benchmark`**: Öffnet einen rein interaktiven Terminal-Wizard zur geführten Modellauswahl.\n")
    f.write("- **`make benchmark-cross-model MODULE=name`**: Evaluiert alle bekannten Modelle zwingend gegen *ein einziges* Modul (hilfreich bei der Modul-Entwicklung).\n")
    f.write("- **`make test`**: Startet via `pytest` alle internen Unit-Tests des Frameworks.\n\n")

    f.write("### 2. Systemgesundheit & Validierung\n")
    f.write("- **`make judge-health`**: Führt Connectivity-Pings gegen die konfigurierten Provider (OpenAI, Anthropic, lokales Ollama) durch, um API-Keys zu testen.\n")
    f.write("- **`make list-modules`**: Listet alle momentan aktivierten Benchmark-Kategorien auf.\n")
    f.write("- **`make validate`** / **`make validate-single ASSET=pfad`**: Validiert das YAML-Schema der hinterlegten Tests.\n")
    f.write("- **`make validate-structure`**: Testet, ob das Verzeichnis-Layout den Architekturvorgaben entspricht.\n")
    f.write("- **`make audit-markdown`**: Durchsucht und bereinigt (mit optionalem Flag `FIX=1`) fehlerhafte Formatierungen (wie Trailing Whitespaces) in Dokumenten.\n\n")

    f.write("### 3. Projekt-Hygiene & Cleanup-Befehle\n")
    f.write("- **`make clean`**: Löscht Caches und temporäre Dateileichen (z.B. Python Bytecode).\n")
    f.write("- **`make clean-runs`**: Bereinigt ausufernde Run-Ordner und behält standardmäßig nur die aktuellsten Backups je Modell.\n")
    f.write("- **`make consolidate-csv`**: Aggregiert zersplitterte CSV-Auszüge zurück in kompakte Tabellen.\n")
    f.write("- **`make clean-all`**: Radikal-Reset. Löscht zusätzlich zur Cache-Leerung alle bisherigen Benchmark-Tabellen.\n")

print("Doc written")
