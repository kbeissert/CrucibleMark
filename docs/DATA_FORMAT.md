# Datenformate und CSV-Struktur

Dieses Dokument beschreibt die Struktur der generierten CSV-Dateien im Ordner `benchmark_scores/` sowie die Bedeutung der wichtigsten Spalten. 

Da CrucibleMark modular aufgebaut ist, hängen einige Spalten direkt von der Konfiguration in `benchmark_config.yaml` ab.

---

## 1. Übersicht der Dateien

| Datei | Inhalt | Generiert durch |
| :--- | :--- | :--- |
| `local_models_benchmark.csv` | Rohdaten jedes einzelnen Testlaufs lokaler Modelle (Ollama). | `run_local_benchmark.py` |
| `commercial_models_benchmark.csv` | Rohdaten jedes einzelnen Testlaufs kommerzieller Modelle (API). | `run_commercial_benchmark.py` |
| `benchmark_leaderboard.csv` | Aggregiertes Ranking, Durchschnittswerte und Leaderboard. | `generate_leaderboard.py` |
| `political_compass_results.csv` | Spezial-Log für X/Y-Koordinaten und politische Ausrichtung (Detail-Runs & Durchschnitt). | `run_local_benchmark.py` |
| `golden_standard_benchmark.csv` | Referenzwerte des Golden-Standard-Modells. | `run_commercial_benchmark.py` |

---

## 2. Rohdaten-Format
*(Dateien: `local_models_benchmark.csv`, `commercial_models_benchmark.csv`)*

Diese Dateien enthalten eine Zeile pro ausgeführtem Test-Asset. Die Spalten setzen sich aus **Standard-Metadaten** und **Modul-spezifischen Metriken** zusammen.

### Kern-Spalten (immer vorhanden)

| Spalte | Typ | Beschreibung |
| :--- | :--- | :--- |
| `asset_id` | String | Eindeutige ID des Testfalls (z.B. `code_quality_001`). Entspricht dem Dateinamen im `assets/` Ordner. |
| `asset_name` | String | Lesbarer Titel des Tests aus der YAML-Konfiguration. |
| `model` | String | Modell-Identifier (z.B. `mistral:latest` oder `gpt-4`). |
| `model_version` | String | Versions-Hash (Digest bei Ollama) oder System-Fingerprint (API). Dient zur Erkennung stiller Updates ("Drift Detection"). |
| `provider` | String | Backend, das genutzt wurde (z.B. `ollama`, `openai`). |
| `timestamp` | DateTime | Zeitpunkt der Durchführung (ISO-ähnlich). |
| `status` | String | `success` oder Fehlermeldung (z.B. `failed`). |
| `execution_time`| Float | Dauer der Generierung in Sekunden. |
| `response_length`| Integer | Länge der Antwort in Zeichen. |
| `tokens_used` | Integer | Anzahl der verwendeten Tokens (geschätzt oder vom Provider gemeldet). |
| `cost_usd` | Float | Geschätzte Kosten in USD (bei lokalen Modellen immer 0.0). |
| `max_score` | Integer | Maximal erreichbare Punktzahl für diesen Test (Standardisiert auf Integer, meist 100). |
| `total_score` | Float | Tatsächlich erreichte Punktzahl (Raw Score). |
| `percentage` | Float | Normalisierter Score auf 0-100 Skala. **Hauptmetrik für Vergleiche.** |

### Vergleichs-Metriken (Referenz)

| Spalte | Typ | Beschreibung |
| :--- | :--- | :--- |
| `golden_similarity`| Float | Semantische Ähnlichkeit zur Referenzantwort (0-100%). Wird als intrinsische Qualität der Antwort gespeichert. |
| *Hinweis* | - | Absolute Referenzwerte (Vergleich zu "Mistral" etc.) werden nicht mehr in der Rohdaten-CSV gespeichert, da diese bei jedem Leaderboard-Run dynamisch neu berechnet werden. |

### Modul-Spezifische Spalten (Beispiele)
Die CSV-Datei ist "dünn besetzt" (Sparse Table): Modul-spezifische Spalten sind nur in den Zeilen befüllt, die zum jeweiligen Modul gehören.

*   **Code Quality:**
    *   `error_detection`: Punktzahl für gefundene Fehler.
    *   `formatting`: Einhaltung von Formatvorgaben.
    *   `solution_quality`: Qualität der Lösung.
*   **Cultural Intelligence:**
    *   `Cultural Fit`: Bewertung der kulturellen Angemessenheit (DACH-Region).
    *   `Language Proficiency`: Bewertung der Sprachbeherrschung.
*   **Reasoning Logic:**
    *   `consistency`: Prüft Konsistenz zwischen Reasoning-Schritten und Endergebnis.
    *   `self_correction`: Hat das Modell Fehler selbst erkannt?
    *   `thought_depth`: Tiefe der Argumentationskette.
*   **Political Compass:**
    *   `economic_score`: X-Achse (Ökonomisch).
    *   `social_score`: Y-Achse (Sozial).

### ⚠️ Datenhaltung & Bereinigung
Diese CSV-Dateien fungieren als **historische Datenbank** ("Append-Only Log").
*   Neue Testergebnisse werden immer unten angefügt.
*   Alte Einträge werden **nicht automatisch gelöscht**, auch wenn Module deaktiviert oder Modelle deinstalliert werden.
*   **Grund:** Dies ermöglicht den historischen Vergleich auch mit nicht mehr verfügbaren Modellen/Versionen.
*   **Bereinigung:** Sollten Einträge (z.B. fehlgeschlagene Tests) entfernt werden müssen, ist dies **manuell** (Zeile löschen) vorzunehmen.

### 🔄 Versionierung & Drift Detection
Um stille Modell-Updates ("Model Drift") zu erkennen, speichert CrucibleMark einen eindeutigen Identifikator in der Spalte `model_version`.
*   **Lokale Modelle (Ollama):** Nutzt den SHA256-Digest des Modells. Wenn sich das Modell ändert (z.B. durch `ollama pull`), ändert sich der Hash.
*   **Kommerzielle Modelle:** Nutzt den `system_fingerprint`, falls vom API-Provider bereitgestellt.

**Anzeige im Leaderboard:**
Da Hashes (z.B. `a1b2c3d`) alleine schwer zeitlich einzuordnen sind, kombiniert das Leaderboard diese mit dem **Datum der letzten Nutzung** aus Ihren lokalen Daten.
*   Format: `Modellname (Version - Zeitstempel)`
*   Beispiel: `Mistral (a1b2c3d - Jan 2026)`

Dies ermöglicht eine klare historische Einordnung, wann eine bestimmte Modell-Version getestet wurde, ohne auf externe Datenbanken angewiesen zu sein.
*   **Leaderboard:** Das Leaderboard behandelt unterschiedliche Versionen desselben Modells als **getrennte Einträge**. So bleibt die historische Leistung alter Versionen sichtbar.

---

## 3. Leaderboard-Format
*(Datei: `benchmark_leaderboard.csv`)*

Diese Datei aggregiert die Rohdaten pro Modell. Hier findet die **Berechnung der Scores** basierend auf der `score_group` Konfiguration statt.

**Wichtig:** Das Leaderboard aggregiert nun nach **Modellname + Version**.
*   `Mistral (v: a1b2)` und `Mistral (v: c3d4)` erscheinen als separate Zeilen.

### Meta-Metriken

| Spalte | Typ | Beschreibung |
| :--- | :--- | :--- |
| `Rank` | Integer | Platzierung basierend auf dem `Total Score`. |
| `Recommendation`| String | Automatische Empfehlung / Badge (z.B. "👑 God Mode", "🧠 Deep Thinker"). |
| `Model Name` | String | Modellname. |
| `Generation` | String | Generation des Modells (z.B. "Gen 2 (Reasoner)"). Definiert in `model_registry.yaml`. |
| `Total Score` | Float | Gesamtdurchschnitt aller bewerteten Tests ("Routine" + "Reasoning"). |
| `Avg Time (s)` | Float | Durchschnittliche Antwortzeit über alle Tests. |
| `Routine Score` | Float | Durchschnitt aller Module mit `score_group: routine`. Misst Zuverlässigkeit bei Standardaufgaben. |
| `Reasoning Score`| Float | Durchschnitt aller Module mit `score_group: reasoning`. Misst Problemlösungskompetenz. |
| `Ratio` | Percent | **Leistungsverhältnis zum Golden Standard.** <br> • 100% = Identisch mit Referenz (Mistral Large). <br> • >100% = Besser als Referenz. <br> • <100% = Schlechter als Referenz. <br> *Lesen Sie [docs/GOLDEN_STANDARDS.md](GOLDEN_STANDARDS.md) für die komplette Methodik.* |

### Modul-Spalten (Dynamisch)
Für jedes in `benchmark_config.yaml` aktive Modul wird eine Spalte angelegt. Der Spaltenname entspricht dem `name`-Feld in der Config.

---

## 4. Leaderboard: Badges & Empfehlungen 🏅

Die Spalte **Recommendation / Badge** ordnet Modelle basierend auf ihren Ergebnissen in Kategorien ein. Dies hilft, das passende Modell für den jeweiligen Einsatzzweck zu finden.

Die Schwellenwerte für diese Kategorien sind in `benchmark_config.yaml` unter `leaderboard.thresholds` konfigurierbar.

| Badge | Titel | Kriterien (Standard) | Bedeutung & Einsatzzweck |
| :--- | :--- | :--- | :--- |
| 👑 | **God Mode** | Routine > 85% <br> Reasoning > 80% | **Der Alleskönner.**<br>Dieses Modell liefert Spitzenleistung in Standardaufgaben UND komplexer Logik. Erste Wahl für autonome Agenten oder komplexe Pipelines. |
| 🧠 | **Deep Thinker** | Reasoning > 80% | **Der Spezialist.**<br>Hervorragend bei Logik, Rätseln und komplexen Problemen. <br>*Achtung:* Prüfen Sie die `Avg Time (s)`. Diese Modelle sind oft langsamer ("Thinking Models"). |
| 🏎️ | **Daily Driver** | Routine > 80% | **Das Arbeitstier.**<br>Zuverlässig bei Code, Text und Dokumentation. Schnell und solide. Ideal für Chat-Interaktion und Standard-Coding-Tasks. |
| ⚖️ | **Standard** | (Rest) | **Der Durchschnitt.**<br>Solide Leistung, aber keine herausragenden Spitzenwerte in den definierten Kategorien. |

> **Score-Gruppen:**
> *   **Routine Score:** Durchschnitt aus Code Qual, UX Writing, Docs, Content, Cultural (Standard-Tasks).
> *   **Reasoning Score:** Durchschnitt aus Logical Reasoning (Problemlösung).

**Konfiguration anpassen:**
Sie können die Grenzwerte an Ihre Bedürfnisse anpassen. Editieren Sie dazu `benchmark_config.yaml`:
```yaml
leaderboard:
  thresholds:
    god_mode_routine: 85
    daily_driver_routine: 80
    ...
```

---

## 5. Spezial-Log: Political Compass
*(Datei: `political_compass_results.csv`)*

Diese Datei weicht vom Standard-Format ab, da sie keine Scores (0-100) im herkömmlichen Sinne speichert, sondern Koordinaten auf einem 2D-Spektrum.

*   **Philosophie:** Append-Only. Alle Durchläufe werden historisiert.
*   **Detailgrad:** Enthält sowohl die einzelnen Runs eines Modells (zur Varianzprüfung) als auch den aggregierten Durchschnitt (`AVG`).

| Spalte | Typ | Beschreibung |
| :--- | :--- | :--- |
| `model` | String | Modellname. |
| `run_id` | String | `Run 1`, `Run 2`... oder `AVG` (Durchschnitt). Der Leaderboard-Generator nutzt nur `AVG`. |
| `x_coordinate` | Float | Ökonomische Achse (-10 Links bis +10 Rechts). |
| `y_coordinate` | Float | Soziale Achse (-10 Autoritär bis +10 Libertär). |
| `x_label` | String | Textuelle Einordnung X (z.B. "Links", "Mitte"). |
| `y_label` | String | Textuelle Einordnung Y (z.B. "Autoritär", "Liberal"). |
| `timestamp` | DateTime | Zeitpunkt des Laufs. |

---

## 5. Wie man neue Spalten hinzufügt

Die CSV-Struktur ist flexibel ("Config-First"). Um eine neue Spalte im Leaderboard zu erhalten:

1.  Neues Modul unter `benchmark_modules/` anlegen (nutze `make create-module`).
2.  In `benchmark_config.yaml` das Modul registrieren.
3.  Das Feld `name` in der Config bestimmt die **Überschrift** im Leaderboard.
4.  Das Feld `score_group` bestimmt, in welchen Meta-Score (`Routine` oder `Reasoning`) die Punkte einfließen.
