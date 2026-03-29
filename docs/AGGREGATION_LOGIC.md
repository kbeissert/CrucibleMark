# CrucibleMark: Aggregation & Test-Zählung

## 1. Test-Zählung & Political Compass

**Update v2.6:** Das Modul "Political Compass" ist vollständig vom Benchmark-Scoring und der Test-Zählung entkoppelt.

### Verhalten vor v2.6

Das Leaderboard zeigte eine Diskrepanz (z. B. "46/37"). Das Political Compass Modul injizierte "Ghost Rows" in den Datensatz, erhöhte damit den Numerator um +9 und leistete keinen Beitrag zum Score-Denominator. Das erzeugte mathematische Verwirrung.

### Aktuelles Verhalten (v2.6+)

Das Political Compass ist ein rein informatives Metadaten-Modul:
- Es injiziert keine Ghost Rows in die Haupt-DataFrames (`local_models_benchmark.csv`, `cloud_models_benchmark.csv` und `commercial_models_benchmark.csv`).
- Es verfälscht den `Tests Run`-Zähler nicht. Der Score Calculator ignoriert explizit alle nicht-wertenden Module für Zähler und Nenner, sofern kein `display_test_count` definiert ist.
- Das Modul speichert Ergebnisse autark in `benchmark_scores/political_compass_results.csv` und aggregiert sie in `benchmark_scores/political_compass_leaderboard.csv`.
- Das Skript `generate_leaderboard.py` liest `political_compass_leaderboard.csv` und ergänzt die finale Anzeige um eine informative `Political Bias`-Textspalte – ohne die Benchmark-Mathematik zu berühren.

______________________________________________________________________

## 2. Duplikate & Datenintegrität

### Beobachtung

Die Rohdatei `benchmark_scores/local_models_benchmark.csv` enthält mehrere Einträge für dasselbe Modell und Asset (z. B. 288 Zeilen für ca. 38 Assets).

### Logik-Verifikation

Das System nutzt eine **„Last-Win"-Strategie** (Überschreiben, kein Mitteln).

**Code-Beleg (`scripts/leaderboard/data_loader.py`):**

```python
# Sort by timestamp to ensure 'last' is actually the most recent
df = df.sort_values("timestamp")

# Drop duplicates keeping the LAST entry
df = df.drop_duplicates(subset=["model", "model_version", "type", "asset_id"], keep="last")
```

### Fazit

- **Datenintegrität:** Die Leaderboard-Generierung bereinigt Duplikate explizit vor jeder Berechnung.
- **Stabilitäts-Tests:** Mehrfach-Runs sind sicher. Das System zeigt stets das neueste Ergebnis pro Asset.
- **Historie:** Die CSV dient als historisches Log. Das ist kein Bug, sondern ein Feature.

______________________________________________________________________

## 3. Stabilitäts-Score

Um faire Stabilitätsmessungen über inhärent unterschiedlich schnelle Aufgaben zu gewährleisten (z. B. schnelle Übersetzung vs. lange Dokumentationsaufgabe), nutzt das System eine **kategoriebewusste Varianz-Logik**.

Die Stabilitätsberechnung basiert auf dem **Variationskoeffizient (VK)** innerhalb jeder Kategorie. Diese VKs werden anschließend gemittelt.

1. **VK pro Kategorie berechnen:**
   $VK\_{cat} = \\frac{\\sigma\_{cat}}{\\mu\_{cat}}$
   (Standardabweichung dividiert durch Mittelwert der Kategorie)

2. **Durchschnittlicher Stabilitäts-Score:**
   $Score\_{stability} = \\frac{1}{N} \\sum VK\_{cat}$

### Schwellenwerte

- **< 0,35 (35 %):** **STABLE** (normale Varianz)
- **0,35–0,50 (35–50 %):** **MODERATE** (hohe natürliche Varianz oder leichte Instabilität)
- **> 0,50 (50 %):** **UNSTABLE** (signifikante Unvorhersehbarkeit)

Ein Modell, das innerhalb seiner Kategorien konsistent bleibt (z. B. immer schnell bei Übersetzungen, immer langsam bei Docs), erhält damit trotzdem einen guten Stabilitäts-Score.
