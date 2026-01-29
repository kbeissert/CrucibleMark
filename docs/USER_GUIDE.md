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
Sucht nach installierten Modellen, die noch **nicht** vollständig getestet wurden, und führt fehlende Benchmarks aus. Ideal, um Lücken in der Datenbasis zu schließen.
```bash
make benchmark-auto
```

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
