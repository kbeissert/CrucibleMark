# 🌐 Political Compass & Modulrhythmie (v3.0)

> **⚠️ WICHTIGER DISCLAIMER: Pragmatischer Benchmark für Exploration**  
> Dieser Benchmark dient primär der **Exploration, dem Vergleich und der Bias-Analyse von LLMs**. Er basiert auf einem robusten, experimentellen Design ("Anti-Diplomat Prompting", "Parolen-Check") und erfüllt **keine strengen sozialwissenschaftlichen Gütekriterien** (wie Validität nach DIN/ISO für psychometrische Tests). Er ist ein Tool für Entwickler, nicht für Politologen.
>
> **Status:** Version 3.0 (Asset-Format 2.0)  
> **Use Case:** Schnelles Benchmarking, Alignment-Check, Bias-Erkennung  
> **Nicht geeignet für:** Akademische Publikationen oder Zertifizierungen ohne Validierung.

Dieses Modul analysiert die politische Ausrichtung und versteckte Biases von LLMs durch einen **erzwungenen Entscheidungsprozess** und die Bewertung populistischer Parolen. Anders als klassische Benchmarks, die neutrale "Assistenten-Sprache" belohnen, zwingt dieses Modul das Modell dazu, Stellung zu beziehen.

---

## ⚙️ Funktionsweise (Version 3.0)

### 1. Anti-Diplomat Prompting (v2_anti_diplomat)
Modelle werden im System-Prompt explizit instruiert, **klare Positionen** einzunehmen ("Take a clear position", "Choose the option that MOST aligns..."). Ausweichende Antworten ("Both sides have valid points...", "As an AI...") werden als Fehler (Refusal) gewertet oder führen zu Retries.

### 2. Multi-Run Strategie (Batch Mode)
Das Modul wird im **Batch-Modus** (`execution_mode: "batch"`) betrieben. Anders als Standard-Module wird hier nicht Asset für Asset getestet, sondern der gesamte Fragenkatalog wird **3-mal vollständig durchlaufen** (Run 1 -> Run 2 -> Run 3).

Grund für dieses Design:
- **Bias-Reduktion:** Verhindert, dass das Modell sich an eine "Session-Persona" erinnert, da der Kontext (je nach Implementierung) zwischen den Runs/Fragen zurückgesetzt oder variiert wird.
- **Konsistenz-Prüfung:** Wir vergleichen nicht Frage A1 mit A2, sondern Frage A in Run 1 mit Frage A in Run 2.
- **Antwort-Shuffling:** Die Optionen (A, B, C, D) werden bei jedem Run neu gewürfelt.

### 3. Neues Koordinaten-System & Polarisierungs-Bonus
Das Ergebnis wird auf zwei Achsen projiziert (`-10.0` bis `+10.0`). In v3.0 wird zusätzlich ein **Polarisierungs-Bonus** berechnet: Wenn ein Modell in Einzelmodulen extreme Positionen vertritt, wird der Gesamtwert verstärkt, damit sich gegensätzliche Extreme (z.B. extrem links in Wirtschaft + extrem rechts in Gesellschaft) nicht zu einer falschen "Mitte" aufheben.

*   **X-Achse (Ökonomie - Verteilen vs. Verdienen):**
    *   `-10.0` (Links/Sozialismus/Planung)
    *   `+10.0` (Rechts/Laissez-faire/Markt)
*   **Y-Achse (Gesellschaft - Autorität vs. Freiheit):**
    *   `-10.0` (Libertär/Privatsphäre/Selbstbestimmung)
    *   `+10.0` (Autoritär/Sicherheit/Ordnung)
    *   *Hinweis: In früheren Versionen war die Y-Achse invertiert. Jetzt: + = Autoritär.*

### 4. Checkpoint & Resume System 🛡️
Da der vollständige Test (3 Runs × 74 Fragen = 222 Inferenz-Schritte) je nach Modellgeschwindigkeit lange dauern kann, verfügt das Modul nun über ein automatisches Sicherungssystem:
*   **Auto-Save:** Nach jedem Themenblock wird der Fortschritt (Antworten, Kosten, Tokens) temporär in `outputs/temp/session_<model>.json` gespeichert.
*   **Crash-Sicherheit:** Bricht der Test ab (Stromausfall, API-Timeout, Absturz), bleiben die bereits beantworteten Fragen erhalten.
*   **Resume:** Starten Sie den Test einfach mit **demselben Befehl** neu. Das System erkennt die Session-Datei und setzt exakt an der Stelle fort, wo es aufgehört hat.
    *   *Meldung:* `🔄 Resuming session for <model>...`

---

## 📂 Neue Modul-Struktur & Assets v2.0

Das Modul besteht aus **9 Themenblöcken** mit insgesamt 70+ Szenarien. Alle Assets wurden auf das Format **YAML v2.0** aktualisiert (mit Metadaten & Dictionary-Optionen).

### Die 9 Dimensionen
| Modul | Titel | Achse | Inhalt & Konfliktlinien |
| :--- | :--- | :--- | :--- |
| **7.1** | Ökonomie & Verteilung | `X` | Bürgergeld, Reichensteuer, Erbschaft, Mieten |
| **7.2** | Arbeitswelt & Markt | `X` | Gewerkschaften, Mindestlohn, Gig-Economy |
| **7.3** | Fiskalpolitik | `X` | Staatsverschuldung, Subventionen, Globalisierung |
| **7.4** | Gesellschaft & Identität | `Y` | Migration, Nationalstolz, Minderheitenrechte |
| **7.5** | Religion & Kultur | `Y` | Säkularisierung, Tradition, religiöse Symbole |
| **7.6** | Justiz & Ordnung | `Y` | Überwachung, Polizei-Befugnisse, Strafrecht |
| **7.7** | Außenpolitik | `Y` | Pazifismus vs. Wehrhaftigkeit, globale Interventionen |
| **7.8** | Technologie & Zukunft | `Y` | KI-Regulierung, Klimaschutz vs. Wachstum, Bioethik |
| **7.9** | **NEU: Parolen-Kompass** | `X/Y` | Bewertung echter politischer Slogans ("Kein Mensch ist illegal", "Enteignet die Konzerne"). Beeinflusst beide Achsen. |

---

## 📊 CSV-Output & Metriken

Die Ergebnisse werden in `benchmark_scores/` gespeichert.

### Wichtige Spalten für die Analyse
*   `x_coordinate` / `y_coordinate`: Die finale Position.
*   `archetype`: Automatische Klassifizierung (z.B. "Links-Libertär", "Rechts-Autoritär").
*   `consistency`: Maß für die Stabilität (`HIGH`, `MODERATE`, `LOW`). Ein inkonsistentes Modell "schwankt" in seiner Meinung.
*   `extremism_warning`: Trigger, wenn Werte `> |8.0|` erreicht werden.
*   `module_scores`: Detaillierte Aufschlüsselung pro Sub-Modul (z.B. `7.4_migration_score`).

### Setup & Assets
Die Fragen liegen als YAML-Dateien in `benchmark_modules/political_compass/assets/` vor.
*   Format: YAML v2.0
*   Optionen: Dictionary (`A`, `B`, `C`, `D`) für robustes Parsing.
*   Parolen (7.9): Nutzen `value_x` UND `value_y`, da Slogans oft multidimensional wirken.

---

## 🛠️ Interpretation (Best Practices)

1.  **Nicht nur den Durchschnitt lesen:** Ein Modell kann im Durchschnitt "Zentrist" sein, aber in **7.4 (Migration)** extrem rechts und in **7.8 (Klima)** extrem links. Prüfen Sie die Modul-Scores!
2.  **Refusals beachten:** Hohe `refused_questions` deuten auf ein starkes RLHF (Reinforcement Learning from Human Feedback) hin, das "kontroverse" Themen blockiert ("As an AI I cannot..."). Das ist oft ein Zeichen für "Corporate Sanity Washing".
3.  **Parolen-Check (7.9):** Dieses Modul ist besonders schwer für LLMs, da es keine Nuance zulässt ("Stimmst du dieser radikalen Parole zu?"). Hier zeigt sich das Alignment am deutlichsten.

---
*CrucibleMark v3.0 - Political Compass Module*

---

## 🚀 Ausführung & Usage

Das Modul kann direkt über die Kommandozeile ausgeführt werden. Es unterstützt Einzeltests, Batch-Runs und Mock-Simulationen.

### 1. Einzeltest (Single Run)
Testet ein spezifisches Modell mit den Standard-Assets.

```bash
# Basis-Befehl
python benchmark_modules/political_compass/test.py test --provider ollama --model mistral

# Mit Limitierung der Fragen (für schnelle Tests)
python benchmark_modules/political_compass/test.py test --provider ollama --model mistral --max 10
```

### 2. Batch-Mode (Mehrere Modelle)
Führt den Benchmark für mehrere Modelle nacheinander aus, definiert in einer Config-Datei.

```bash
python benchmark_modules/political_compass/test.py batch --config my_config.yaml
```

### 3. Mock-Simulation (Dry Run)
Simuliert einen Durchlauf ohne LLM-Aufruf (zufällige Antworten), um die Pipeline und das Scoring zu testen.

```bash
python benchmark_modules/political_compass/test.py mock
```

### Output
Die Ergebnisse werden als JSON-Dateien im Arbeitsverzeichnis gespeichert (z.B. `results_mistral_20231027.json`). Diese enthalten:
- Rohdaten aller Antworten
- Berechnete X/Y-Koordinaten
- Modul-spezifische Scores
- Metadaten zum Run

> **Hinweis zur Visualisierung:** Dieses Modul fokussiert sich rein auf die Datenerhebung. Die grafische Aufbereitung (Plotting) wurde in Version 3.0 ausgelagert, um Abhängigkeiten gering zu halten. Nutzen Sie die generierten CSV/JSON-Daten für eigene Visualisierungen.

