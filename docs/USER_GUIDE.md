# User Guide: Benchmarking Workflow

Dieser Guide beschreibt Schritt für Schritt, wie Benchmarks in CrucibleMark ausgeführt, gesteuert und ausgewertet werden.

> **Voraussetzung:** Stellen Sie sicher, dass die Installation korrekt durchgeführt wurde (`make install` oder `scripts/setup_env.py`).

---

## 1. Quick Start (Der Wizard) 🧙

Für den einfachsten Einstieg nutzen Sie den interaktiven Wizard. Er führt Sie durch alle notwendigen Schritte: Modellauswahl, Modulauswahl und Validierung.

```bash
make benchmark
```

1.  **Modus wählen:** "Single Model" (fokussierter Test) oder "Batch" (mehrere Modelle).
2.  **Modell wählen:** Liste der verfügbaren lokalen (Ollama) oder kommerziellen Modelle.
3.  **Module wählen:** Aktivieren Sie Test-Kategorien (z.B. Political Compass, Code Quality).
4.  **Starten:** Der Benchmark läuft automatisch ab.

---

## 2. Benchmark-Steuerung via Makefile

Für präzisere Kontrolle oder wiederkehrende Aufgaben nutzen Sie die Makefile-Befehle direkt.

### A. Lokale Modelle (Ollama) auflisten
Prüft die Verbindung zu Ollama und zeigt verfügbare Modelle an.
```bash
make list-models
```

### B. Automatischer "Auffüll-Modus" (Auto-Benchmark)

Der Auto-Benchmark ist für den **täglichen Betrieb** optimiert. Er prüft intelligent, welche Tests wirklich notwendig sind.

```bash
make benchmark-auto
```

**Features:**
*   **Smart Skipping:** Überspringt Tests, die für dieses Modell bereits erfolgreich (`status: success`) absolviert wurden.
*   **Auto-Retry:** Fehlgeschlagene Tests werden automatisch erkannt und neu ausgeführt.
*   **Kosten-Effizienz:** Spart API-Kosten bei kommerziellen Modellen, da keine unnötigen Doppelausführungen stattfinden.

**Erzwungener Neustart (Force Mode):**
Wenn Sie bewusst alle Tests neu ausführen möchten (z.B. nach Änderungen am Code oder Prompting), nutzen Sie das Skript direkt mit dem `--force` Flag:

```bash
python scripts/benchmark_auto.py --force
```
> **Warnung:** Dies führt ALLE Benchmarks erneut aus und verursacht entsprechende API-Kosten!

### C. Einzelnes Modell testen (CLI)
Startet einen gezielten Testlauf für ein spezifisches Modell. Optional kann ein einzelnes Modul isoliert werden.

```bash
# Alle aktiven Module für 'mistral' testen
make benchmark-single MODEL=mistral

# Nur das Modul 'ux_writing' testen
make benchmark-single MODEL=mistral MODULE=ux_writing
```

---

## 3. Crash Recovery & Session Management 🛡️

Besonders das Modul **Political Compass** benötigt aufgrund der vielen Testfragen (viele Runs = lange Laufzeit) Zeit. CrucibleMark besitzt daher ein eingebautes Sicherungssystem.

### Wie Session Resume funktioniert
Wenn ein Benchmark abstürzt, unterbrochen wird (Strg+C) oder der Rechner ausgeht:
1.  Der Fortschritt wird automatisch in `outputs/temp/session_<model>.json` gespeichert.
2.  Starten Sie den Benchmark einfach mit demselben Befehl neu.
3.  Das System meldet: `🔄 Resuming session for <model>...` und setzt exakt dort fort, wo es aufgehört hat.

### Session Expiry (Verfallsdatum)
Um zu verhindern, dass Sie nach Wochen versehentlich einen veralteten Test fortsetzen:
*   Sessions älter als **48 Stunden** werden automatisch verworfen (automatischer Neustart bei 0).

### Manuelles Zurücksetzen (Clean Sessions)
Wenn Sie *trotz* eines vorhandenen Checkpoints frisch von vorne beginnen wollen:

```bash
make clean-sessions
```
Dies löscht alle temporären Speicherstände. Der nächste Benchmark-Start beginnt bei 0.

---

## 4. Auswertung & Leaderboard 🏆

Nachdem die Benchmarks durchgelaufen sind, liegen die Rohdaten in CSV-Dateien im Ordner `benchmark_scores/`. Um diese lesbar aufzubereiten:

```bash
make leaderboard
```

Dies generiert die Datei `benchmark_scores/benchmark_leaderboard.csv` mit:
*   Ranking nach Gesamt-Score
*   Gruppierung nach Modell-Versionen (z.B. "v1" vs "v2")
*   Berechnung von "Routine" vs "Reasoning" Scores
*   Vergabe von Badges (z.B. "Context King")

Mehr Details zum Datenformat finden Sie in [DATA_FORMAT.md](DATA_FORMAT.md).

---

## 5. Troubleshooting & Logging 🔍

CrucibleMark trennt Benutzerinformationen strikt von technischen Details, um die Übersichtlichkeit zu wahren.

### Konsole (Terminal)
Im Terminal sehen Sie nur das Wichtigste:
*   Fortschritt der Tests
*   Ergebnisse und Scores
*   Verständliche Statusmeldungen (z.B. "Lade Modell...")
*   Kein technisches "Rauschen" von Bibliotheken

### Log-Datei (Debugger)
Wenn etwas schiefgeht oder Sie technische Fehler (Tracebacks, HTTP-Timeouts, Warnungen) im Detail sehen wollen, prüfen Sie:
👉 **`logs/crucible.log`**

Diese Datei speichert **alles** (Debug-Level), inklusive der Warnmeldungen externer Bibliotheken (HuggingFace, Ollama, etc.), die im Terminal unterdrückt werden.

---

## 6. Developer & Debug Mode 🛠️

Für tiefere Analysen von Modell-Antworten (z.B. bei unerwarteten 0%-Scores) gibt es einen speziellen Debug-Modus.

### Automatische Debug-Logs
Standardmäßig speichert das System die **vollständigen Antworten** eines Modells automatisch ab, wenn ein Test mit weniger als **30%** bewertet wird. Dies hilft sofort zu erkennen, ob das Modell den Task verweigert hat ("I cannot do this") oder halluziniert hat.

### Manueller Debug-Modus (`--debug-responses`)
Um **alle** Antworten (auch erfolgreiche) zu inspizieren, starten Sie den Benchmark mit dem Debug-Flag oder der Umgebungsvariable:

**Via CLI (Skript):**
```bash
python scripts/run_local_benchmark.py --debug-responses
```

**Via Umgebungsvariable:**
```bash
CRUCIBLE_DEBUG=true make benchmark
```

**Wo finde ich die Ausgaben?**
Die Antworten werden als Textdateien gespeichert unter:
`benchmark_scores/debug_responses/<model>_<asset_id>.txt`

Beispiel: `benchmark_scores/debug_responses/phi4_latest_reasoning_5d_001.txt`
Inhalt:
*   Score & Erklärung des Judges
*   **Vollständige Modell-Antwort** (ungekürzt)

---

## 7. Daten-Management & Bereinigung 🧹

CrucibleMark unterscheidet zwischen **historisch wertvollen Daten** (Benchmarks) und **temporären Caches**.

### Grundregel: "Daten sind heilig" 🛡️
Normalerweise sollten Sie Benchmark-Ergebnisse **nicht löschen**, sondern neue Läufe einfach hinzufügen (History).
*   **Auffüllen:** `make benchmark-auto` (Ergänzt nur Fehlendes)
*   **Neu Messen:** `python scripts/benchmark_auto.py --force` (Erzwingt neue Messung, behält History)

### Gezieltes Löschen (Clean-Up)
Nutzen Sie diese Befehle nur, wenn Sie **fehlerhafte Daten** (z.B. falsche Config) entfernen müssen. Sie löschen die Einträge unwiderruflich aus der Datenbank (CSV).

#### A. Einzelnes Modell bereinigen
Entfernt alle Ergebnisse eines spezifischen Modells aus der CSV sowie dessen temporäre Session-Dateien.
```bash
# Löscht alles zu 'mistral-large'
make clean-model MODEL=mistral-large
```
*Anwendungsfall: Ein Modell wurde neu installiert/trainiert oder lief mit falschen Parametern.*

#### B. Modul-Ergebnisse bereinigen
Entfernt die Ergebnisse eines bestimmten Moduls für **alle** Modelle.
```bash
# Löscht Ergebnisse des Moduls 'ux_writing'
make clean-module MODULE=ux_writing
```
*Anwendungsfall: Sie haben die Test-Assets eines Moduls verändert, wodurch alte Scores nicht mehr vergleichbar sind.*

#### C. Komplett-Reset
Achtung: Dies löscht **alle** Benchmark-Ergebnisse und setzt das Leaderboard auf Null.
```bash
make clean-csv
```

