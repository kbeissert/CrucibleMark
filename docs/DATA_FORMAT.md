# CSV Data Format Documentation

Dieses Dokument beschreibt die Struktur der generierten CSV-Dateien und die Bedeutung der einzelnen Spalten.

## 1. Rohdaten (Raw Benchmark Results)
Dateien: `benchmark_scores/local_models_benchmark.csv` und `benchmark_scores/commercial_models_benchmark.csv`

Diese Dateien enthalten die Ergebnisse jedes einzelnen Testdurchlaufs pro Asset.

| Spalte | Typ | Beschreibung |
| :--- | :--- | :--- |
| `asset_id` | String | Eindeutige ID des Testfalls (z.B. `reasoning_001_river`). |
| `model` | String | Technischer Identifier des Modells (z.B. `mistral:latest`, `gpt-4`). |
| `percentage` | Float | Erreichter Score für dieses Asset (0-100). Wird auch als "Raw Score" bezeichnet. |
| `execution_time` | Float | Benötigte Zeit für die Generierung der Antwort in Sekunden. |
| `tier` | String | Klassifizierung der Komplexität. Wichtig für Meta-Scores. <br>• `Tier 1 (Operational Logic)`: Standardaufgaben. Fließt in *Routine Score* ein.<br>• `Tier 2 (Deep Reasoning)`: Komplexe Logik. Fließt in *Reasoning Score* ein. |
| `status` | String | Status des Durchlaufs (`success`, `failed`). |
| `timestamp` | DateTime | Zeitpunkt der Durchführung. |
| `error_detection` | String | (Optional) Teil-Score für Fehlererkennung (Format: `Punkte / Max`). |
| `solution_quality`| String | (Optional) Teil-Score für Lösungsqualität. |
| `consistency` | Float | (Optional) Teil-Score für Konsistenz. |
| `total_score` | Float | Summe der gewichteten Teil-Scores (Redundant zu `percentage`, aber oft als absolute Zahl). |
| `details` | String | JSON-ähnlicher String mit weiteren Metadaten. |

---

## 2. Leaderboard (Aggregated Ranking)
Datei: `benchmark_scores/benchmark_leaderboard.csv`

Diese Datei wird vom Skript `scripts/generate_leaderboard.py` generiert. Sie aggregiert alle Rohdaten und berechnet Durchschnitte.

### Haupt-Metriken

| Spalte | Berechnung | Beschreibung |
| :--- | :--- | :--- |
| `Rank` | Index | Platzierung basierend auf dem `Total Score`. |
| `Model Name` | String | Name des Modells für die Anzeige. Identisch mit `model` aus Rohdaten. |
| `Total Score` | Avg(`percentage`) | Durchschnittswert **aller** erfolgreichen Tests über alle Kategorien hinweg. |
| `Avg Time (s)` | Avg(`execution_time`) | Durchschnittliche Antwortzeit pro Asset. |
| `Routine Score` | Avg(`percentage`) | Durchschnitt aller Aufgaben der Klasse **Tier 1** (Standard, Fleißaufgaben). |
| `Reasoning Score`| Avg(`percentage`) | Durchschnitt aller Aufgaben der Klasse **Tier 2** (Komplexe Logik, Paradoxien). |
| `Badge` | Logik | Vergebener Titel basierend auf Schwellenwerten (z.B. "🏎️ Daily Driver", "⚖️ Standard"). |
| `Type` | String | `Local` oder `Commercial`. |
| `Efficiency_Index` | `Routine Score` / `Time` | Experimentell: Wie viel "Routine-Leistung" pro Sekunde Rechenzeit? |

### Modul-Spalten
Zusätzlich werden Spalten für jedes Benchmark-Modul hinzugefügt (z.B. `Code Quality Audit`, `Logical Reasoning`). Diese enthalten den Durchschnittsscore des Modells in der jeweiligen Disziplin.

## 3. Tier-Definitionen

Die Zuordnung, welcher Test in welchen Score einfließt, ist in der Test-Logik (`test.py`) definiert.

*   **Routine Score (Tier 1)**:
    *   Umfasst die meisten "normalen" Aufgaben (Texterstellung, einfache Code-Auditierung, Standard-Regeln).
    *   Ziel: Misst die Verlässlichkeit im täglichen Betrieb.
*   **Reasoning Score (Tier 2)**:
    *   Umfasst Aufgaben, die *mehrschrittiges, abstraktes Denken* erfordern.
    *   Aktuelle Beispiele: `reasoning_5a` (Infinite Loop Debugging), `reasoning_5c` (Konflikt-Lösung), `reasoning_5d` (Hidden Deadlock).
    *   Ziel: Misst "Intelligenz" bei neuartigen Problemen.
