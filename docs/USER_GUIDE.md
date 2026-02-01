# User Guide: Benchmarking Workflow

**Zielgruppe:** Alle, die CrucibleMark nutzen wollen – ohne Code-Kenntnisse erforderlich.

**Was Sie hier finden:**
- Quick Start (3 Befehle bis zum ersten Ergebnis)
- Benchmark-Steuerung (Modus-Auswahl, Modell-Filter)
- Auswertung & Leaderboard
- Troubleshooting

> **Voraussetzung:** Installation abgeschlossen (`make install` ausgeführt).

---

## ⚡ Quick Start (3 Befehle)

```bash
# 1. Installation prüfen
make list-models

# 2. Ersten Benchmark starten (Interaktiver Wizard)
make benchmark

# 3. Ergebnisse als Leaderboard anzeigen
make leaderboard
```

**Fertig!** Die Ergebnisse finden Sie in `benchmark_scores/benchmark_leaderboard.csv`.

---

## 🎮 Der Interaktive Wizard

Der einfachste Weg, Benchmarks zu starten:

```bash
make benchmark
```

### Was passiert?

1. **Modus wählen:**
   - **Single Model** – Testen Sie ein spezifisches Modell (z.B. nur Qwen 2.5)
   - **Batch Mode** – Testen Sie alle verfügbaren Modelle auf einmal

2. **Modell auswählen:**
   - Liste aller lokalen (Ollama) und kommerziellen Modelle
   - Mit Connectivity-Check (✅ verfügbar / ❌ offline)

3. **Module aktivieren:**
   - Code Quality, UX Writing, Reasoning, etc.
   - Oder "All" für vollständigen Test

4. **Automatischer Start:**
   - Progress-Bar zeigt Fortschritt
   - Ergebnisse werden live in CSV geschrieben

---

## 🎯 Benchmark-Modi im Detail

### A. Single Model (Fokussiert)

**Wann nutzen?**
- Schneller Test eines neuen Modells
- Debugging (wenn ein Modell unerwartete Scores hat)
- API-Kosten sparen (nur 1 Modell testen)

**Befehl:**
```bash
make benchmark-single MODEL=qwen2.5:14b
```

**Optional: Nur ein Modul testen:**
```bash
make benchmark-single MODEL=qwen2.5:14b MODULE=code_quality
```

---

### B. Batch Mode (Vollständig)

**Wann nutzen?**
- Leaderboard-Update (alle Modelle auf neuesten Stand bringen)
- Vergleich zwischen lokalen und kommerziellen Modellen
- Overnight-Run (dauert 2-6 Stunden je nach Anzahl)

**Befehl:**
```bash
make benchmark-auto
```

**Was ist "auto"?**
- **Smart Skipping:** Überspringt bereits getestete Assets
- **Auto-Retry:** Führt fehlgeschlagene Tests erneut aus
- **Kosten-Effizienz:** Keine doppelten API-Calls

**Forced Re-Run (alles neu testen):**
```bash
python scripts/benchmark_auto.py --force
```
⚠️ **Warnung:** Dies ignoriert vorherige Ergebnisse und kostet API-Credits!

---

## 🏆 Leaderboard generieren

Nach dem Benchmark-Run:

```bash
make leaderboard
```

**Output:** `benchmark_scores/benchmark_leaderboard.csv`

### Was zeigt das Leaderboard?

| Spalte | Bedeutung |
|--------|-----------|
| **Rank** | Platzierung (nach Total Score) |
| **Model Name** | Modellname + Version |
| **Badge** | Klassifizierung (God Mode, Daily Driver, Deep Thinker) |
| **Total Score** | Gesamtdurchschnitt (0-100%) |
| **Routine Score** | Performance bei Standardaufgaben (Doku, UX Writing) |
| **Reasoning Score** | Performance bei Logik-Rätseln (Code Quality, Deadlocks) |
| **Ratio** | Vergleich zum Golden Standard (100% = wie Mistral Large) |
| **Avg Time** | Durchschnittliche Antwortzeit in Sekunden |

**Module-Spalten:**
- Jedes aktive Modul bekommt eine eigene Spalte (z.B. "Code Quality: 85%")

---

## 🏅 Badges erklärt

Das Leaderboard vergibt **4 Kategorien** basierend auf Performance:

| Badge | Kriterien | Bedeutung |
|-------|-----------|-----------|
| 👑 **God Mode** | Routine >85% + Reasoning >80% | Alleskönner – perfekt für autonome Agenten |
| 🧠 **Deep Thinker** | Reasoning >80% | Spezialist für komplexe Logik (langsam, aber präzise) |
| 🏎️ **Daily Driver** | Routine >80% | Zuverlässig bei Alltags-Tasks (schnell, solide) |
| ⚖️ **Standard** | Rest | Durchschnittliche Leistung |

**Tipp:** Wählen Sie Modelle basierend auf Ihrem Use Case:
- **Chat & Coding:** Daily Driver (schnell, zuverlässig)
- **Research & Analysis:** Deep Thinker (gründlich, langsam)
- **Production Systems:** God Mode (beides)

---

## 🛡️ Crash Recovery & Sessions

### Was passiert bei Absturz?

CrucibleMark speichert den Fortschritt automatisch:

1. **Checkpoint erstellt:** Nach jedem abgeschlossenen Asset
2. **Session-Datei:** `outputs/temp/session_<model>.json`
3. **Auto-Resume:** Beim nächsten Start wird gefragt:
   ```
   🔄 Found existing session for qwen2.5:14b (45% complete).
   Resume? [Y/n]
   ```

### Session-Verfallsdatum

- **48 Stunden:** Sessions älter als 2 Tage werden verworfen
- **Grund:** Verhindert versehentliches Fortsetzen veralteter Tests

### Manuelle Session-Bereinigung

```bash
# Alle Sessions löschen (Fresh Start)
make clean-sessions
```

---

## 🔍 Troubleshooting

### Problem: "Model not found"

**Lösung:**
```bash
# Prüfen, ob Modell verfügbar ist
make list-models

# Falls nicht da (Ollama):
ollama pull qwen2.5:14b
```

---

### Problem: "API Rate Limit" (kommerzielle Modelle)

**Symptom:**
```
❌ Error: 429 Too Many Requests
```

**Lösung:**
- Warten Sie 60 Sekunden
- CrucibleMark hat **automatisches Retry** mit Exponential Backoff
- Bei wiederholten Fehlern: API-Key-Limit prüfen

---

### Problem: Scores sind 0% (obwohl Antwort gut aussieht)

**Debug-Modus aktivieren:**
```bash
python scripts/run_local_benchmark.py --debug-responses
```

**Was passiert:**
- Vollständige Modell-Antworten werden gespeichert
- Pfad: `benchmark_scores/debug_responses/<model>_<asset>.txt`
- Enthält: Score, Reasoning, ungekürzte Antwort

**Automatisch aktiviert bei:**
- Scores < 30% (Asset wird automatisch geloggt)

---

### Problem: Benchmark hängt bei "Generating response..."

**Mögliche Ursachen:**
1. **Ollama offline:** `ollama list` testen
2. **Modell zu groß:** RAM voll (prüfen Sie `htop` / Task Manager)
3. **API-Timeout:** Kommerzielle Modelle > 120s Response-Zeit

**Lösung:**
```bash
# Ollama neustarten
ollama restart

# Kleineres Modell testen
make benchmark-single MODEL=qwen2.5:7b
```

---

## 📊 Daten-Management

### Wo werden Ergebnisse gespeichert?

```
benchmark_scores/
├── local_models_benchmark.csv       # Rohdaten (jeder einzelne Test)
├── commercial_models_benchmark.csv  # Rohdaten (API-Modelle)
├── benchmark_leaderboard.csv        # Aggregierte Rankings
├── political_compass_results.csv    # Spezial-Modul (Koordinaten)
└── debug_responses/                 # Debug-Logs (optional)
```

---

### Backup erstellen

**Empfehlung:** Vor großen Änderungen (neue Module, Config-Updates):

```bash
make backup
```

**Was wird gesichert:**
- Alle CSV-Dateien
- Konfigurationen
- Golden Standards
- Archiviert als: `backups/cruciblemark_backup_YYYYMMDD.tar.gz`

---

### Daten bereinigen

⚠️ **Vorsicht:** Diese Befehle löschen Daten unwiderruflich!

```bash
# Einzelnes Modell entfernen
make clean-model MODEL=mistral:latest

# Modul-Ergebnisse entfernen (alle Modelle)
make clean-module MODULE=ux_writing

# Alles löschen (Komplett-Reset)
make clean-csv
```

**Wann nutzen?**
- Fehlerhafter Test-Run (falsche Config)
- Modell wurde neu trainiert
- Modul-Assets wurden geändert (alte Scores nicht mehr vergleichbar)

---

## 📈 Fortgeschrittene Nutzung

### Kosten schätzen (vor Batch-Run)

```bash
make analyze-costs
```

**Output:**
```
Estimated API costs:
- Mistral Large: $12.50 (500 requests)
- GPT-4: $28.00 (500 requests)
Total: $40.50
```

---

### Nur fehlgeschlagene Tests wiederholen

```bash
make benchmark-auto
```
(Smart-Skip überspringt erfolgreiche Tests automatisch)

---

### Custom Module aktivieren/deaktivieren

**Datei:** `benchmark_config.yaml`

```yaml
modules:
  political_compass:
    enabled: false  # Modul überspringen
```

Nach Änderung:
```bash
make leaderboard  # Leaderboard neu generieren
```

---

## 🆘 Hilfe & Support

### Logs prüfen

**Konsole:** Zeigt nur wichtige Meldungen (User-freundlich)

**Vollständiges Log:**
```bash
tail -f logs/crucible.log
```
(Enthält alle technischen Details, Warnings, Tracebacks)

---

### Projekt validieren

```bash
# Struktur prüfen
make validate-structure

# Assets prüfen (YAML-Schema)
make validate-assets
```

---

### Community & Docs

- **GitHub Issues:** [github.com/yourusername/cruciblemark/issues](https://github.com/yourusername/cruciblemark/issues)
- **Discussions:** [github.com/yourusername/cruciblemark/discussions](https://github.com/yourusername/cruciblemark/discussions)
- **Developer Guide:** Siehe `docs/DEVELOPER_GUIDE.md` (für Modul-Entwicklung)
- **Architecture:** Siehe `docs/ARCHITECTURE.md` (für System-Design)

---

## 🎓 Nächste Schritte

**Nach dem ersten Benchmark:**
1. ✅ Leaderboard studieren (`benchmark_leaderboard.csv`)
2. ✅ Badge-Kategorien verstehen (God Mode vs Daily Driver)
3. ✅ Modell für Ihren Use Case wählen

**Für Fortgeschrittene:**
- Eigene Module erstellen (siehe `DEVELOPER_GUIDE.md`)
- Golden Standard aktualisieren (`make generate-golden`)
- Custom Scoring-Logik implementieren

---

**Happy Benchmarking! 🚀**

---

**Dokumenten-Version:** 1.0.0 (Rewrite Feb 2026)  
**Kompatibel mit:** CrucibleMark v0.9.5+
