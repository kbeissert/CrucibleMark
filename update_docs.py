from pathlib import Path
d = Path("docs/USER_GUIDE.md")
with open(d, "r") as f:
    text = f.read()

replacement = """### 3. Projekt-Hygiene & Cleanup-Befehle (Konsolidiert)

Die Cleanup-Prozesse wurden in einem zentralen, interaktiven System zusammengefasst.

- **`make clean-wizard`**: Startet den interaktiven Cleanup-Wizard im Terminal, über den du flexibel Caches, Runs oder Ergebnisse einzelner Modelle sicher und geführt bereinigen kannst. (Empfohlen)
- **`make clean`**: Löscht Caches und temporäre Dateileichen (z.B. Python Bytecode, `__pycache__`, alte Reports, Audit-Logs). (Kann kombiniert werden mit Flags: `make clean MODEL=Name`, `make clean MODULE=Key`)
- **`make clean-sessions`**: Löscht temporäre Session-Zwischenspeicher.
- **`make clean-runs`**: Bereinigt ausufernde Run-Ordner und behält standardmäßig nur den 1 aktuellsten Run pro Modell. (`make clean-runs FORCE=1` überspringt Nachfragen).
- **`make clean-csv`**: Löscht alle standardmäßig generierten Benchmark-CSV Dateien.
- **`make clean-all`**: Radikal-Reset. Löscht zusätzlich zur Standard-Cache-Leerung **alle** bisherigen Benchmark-Run Ordner und CSV-Scores. DANGER.
"""

new_text = text.split("### 3. Projekt-Hygiene")[0] + replacement
with open(d, "w") as f:
    f.write(new_text)
print("Updated successfully.")