# User Guide: Benchmarking Workflow

**Zielgruppe:** Alle, die CrucibleMark nutzen wollen – ohne Code-Kenntnisse erforderlich.

**Was Sie hier finden:**

- Quick Start (3 Befehle bis zum ersten Ergebnis)
- Benchmark-Steuerung (Modus-Auswahl, Modell-Filter)
- Auswertung & Leaderboard
- Troubleshooting

> **Voraussetzung:** Installation abgeschlossen (`make install` ausgeführt).

## Besonderheit für Windows/Linux mit NVIDIA GPU (CUDA)
Damit der sogenannte "Semantic Mode" (der für das Text-Scoring die Similarity-Engine auf die Grafikkarte auslagert) rasend schnell läuft, sollte *vor* dem Ausführen von `make install` die native PyTorch-Variante für CUDA installiert werden, andernfalls nutzt PyTorch als Fallback stets die langsamere CPU.
```bash
# Beispiel für CUDA 12.1 (Windows/Linux)
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

______________________________________________________________________

👉 **WICHTIG:** Bevor du blind loslegst, schau einmal in den [Setup-Guide (SETUP_GUIDE.md)](SETUP_GUIDE.md). Im Setup musst du z. B. deine API-Keys, Module und Hardware eintragen, die sonst einen Fehler produzieren!

______________________________________________________________________

## ⚡ Quick Start (3 Befehle)

```bash
# 1. Installation prüfen
make list-models

# 2. Benchmark starten (Production Mode)
make benchmark
# ... oder für schnelle Tests (Dev Mode):
make benchmark-dev

# 3. Ergebnisse als Leaderboard anzeigen
make leaderboard
```

**Fertig!** Die Ergebnisse finden Sie in `benchmark_scores/benchmark_leaderboard.csv`.

______________________________________________________________________

## 🎮 Der Interaktive Wizard

Der einfachste Weg, Benchmarks zu starten:

```bash
make benchmark
```

### Was passiert?

1. **Modus wählen:**

   - **Single Model** – Testen Sie ein spezifisches Modell (z.B. nur Qwen 2.5)
   - **Batch Mode** – Testen Sie alle verfügbaren Modelle auf einmal

1. **Modell auswählen:**

   - Liste aller lokalen (Ollama) und kommerziellen Modelle
   - Mit Connectivity-Check (✅ verfügbar / ❌ offline)

1. **Module aktivieren:**

   - Code Quality, UX Writing, Reasoning, etc.
   - Oder "All" für vollständigen Test

1. **Automatischer Start:**

   - Progress-Bar zeigt Fortschritt
   - Ergebnisse werden live in CSV geschrieben

______________________________________________________________________

## 🎯 Benchmark-Modi im Detail

### A. Single Model (Fokussiert)

**Wann nutzen?**

- Schneller Test eines neuen Modells
- Debugging (wenn ein Modell unerwartete Scores hat)
- API-Kosten sparen (nur 1 Modell testen)

**Befehl:**

```bash
make benchmark MODEL=qwen2.5:14b
```

**Optional: Nur ein Modul testen:**

```bash
make benchmark MODEL=qwen2.5:14b MODULE=code_quality
```

______________________________________________________________________

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

______________________________________________________________________

## 📐 Scoring Explained (v1.1)

CrucibleMark verwendet unterschiedliche Scoring-Mechanismen:

### 1. Granular Rubric Scoring (Reasoning)

Für komplexe Evaluierungen nutzen wir den **LLM-Judge** und strukturierte Rubrics für faire Teilpunkte.

**Beispiel (Scheduling Paradox):**

- **Problem Detection (20 Pkt):** ✅ Erkannt (20/20)
- **Refusal (40 Pkt):** ❌ Versuch einer Lösung (0/40)
- **Analysis (25 Pkt):** ✅ Korrekte Logik (15/25)
- **Total:** 35/100 (statt 0)

### 2. Hybrid Scoring (General)

Standard-Module nutzen eine Mischung aus **40% Keyword-Matching** und **60% Semantic Similarity** zum Gold Standard.

> **ℹ️ Info zur Semantic Similarity:** CrucibleMark nutzt das lokale KI-Modell **`all-MiniLM-L6-v2`** (via `sentence-transformers`), um die inhaltliche Bedeutung der Antworten mit der Musterlösung zu vergleichen.
>
> - **Vorteil:** Antwortet das Modell korrekt, nutzt aber andere Worte als die Musterlösung, wird dies erkannt.
> - **Setup:** Das Modell (~80MB) wird bei der Installation (`make install`) einmalig heruntergeladen und lokal gecached.

### 3. Audit Logs & Protokolle

Aus einem ursprünglichen Entwickler-Tool für das Debugging von Fehlern ist eine umfassende Protokoll-Engine herangewachsen. Der **Audit-Modus** bietet heute ein klares, lückenloses Verständnis der Benchmarks für Mensch und Maschine von der initialen Eingabe bis zur Auswertung.
Er generiert zu jedem getesteten Asset eine perfekt formatierte Markdown-Datei, die streng strukturiert ist. Diese Dateien protokollieren exakt:
1. Den vollständig evaluierten **Prompt**, der an das Modell geschickt wurde.
2. Die unverfälschte **Antwort** des bewerteten Modells.
3. Die detaillierte Herleitung der Bewertung (inklusive Metadaten, Token-Limits und dem logischen Reasoning des LLM-Judges).

Der Audit-Modus ist **standardmäßig aktiv**. Wenn du die Audit-Logs überspringen möchtest, kannst du die Protokollierung beim Benchmark-Start via `SILENT=1` Flag deaktivieren:
```bash
make benchmark MODEL=modell_name SILENT=1
```
Alle generierten Markdown-Files findest du im Ordner `outputs/audit_logs/`. Dieser Modus ist das ideale Werkzeug, wenn du nachvollziehen möchtest, *warum* ein Modell eine bestimmte Punktzahl bekommen hat, ohne dafür manuell im Terminal mitlesen zu müssen.

### 4. Metadaten-Tracking (Token-Limits / "Kopfnoten")

Nicht jeder LLM-Provider kann beliebige Output-Längen realisieren. Erlaubt ein Asset bis zu `8192` Token und das Modell verweigert dies (z.B. OpenAI max_completion_tokens, Anthropic max_tokens), greift ein **kaskadierendes Fallback** im Framework. Es schraubt die Limitanforderung transparent nach unten (z.B. auf 4096, 2048 Token), bis das Modell antwortet.

- **Pro Asset Info**: Jeder Audit-Log und jede Testzeile im Dashboard weist den final verwendeten Token-Wert gesondert als Info-Feld aus. Es verfälscht nicht die Mathe-Note, ist aber entscheidend als "Kopfnote".
- **LLM Judge**: Dem Judge wird diese Kaskade ausgeblendet, er bewertet isoliert den Output-String ohne Bias bezüglich der Konfiguration.

### 5. Editor-Auswertung für System-Integration (Wrappper)

Diese Meta-Informationen spielen im finalen Editor-Bericht eine prominente Rolle. Bevor Entwickler ein hoch-scorendes Modell (wie *Mistral* oder eine *lokale Ollama-Variante*) in eigene Tools (wie **AnythingLLM** oder **WebUI-Wrapper**) einbinden, ist die Information zum Output-Ratio essentiell. Ein Modell mit perfektem Score, das aber im Framework auf 2048 Token "zugeschnürt" werden musste um nicht abzustürzen, eignet sich oft nicht z.B. als Document-Analysis-Agent. Diese "Kopfnoten" bewahren Administratoren in der Praxis vor unliebsamen "Generation Cutoffs" in eigenen Projekten.

______________________________________________________________________

## 🏆 Leaderboard generieren

Nach dem Benchmark-Run:

```bash
make leaderboard
```

Der Befehl generiert **zwei CSV-Dateien** im Ordner `benchmark_scores/`:

1. **`benchmark_leaderboard.csv` (Standard / Compact)**
   - Entwickelt für die tägliche Ansicht, Dashboards, Readmes und kurze Vergleiche.
   - Zeigt nur die wichtigsten aggregierten Score-Säulen und Performance-Ratings an.
2. **`benchmark_leaderboard_detailed.csv` (Detailed)**
   - Entwickelt für tiefgreifende Architekturanalysen, System-Stabilität und Latenz-Audits.
   - Enthält ungefilterte Metriken wie Langzeit-Ausreißer (`P95 Time`), `Max Time`, `Timeout Counts` und strikt getrennte Basis-Scorings (`Routine Score` & `Reasoning Score`), die in der Compact-Version im `Total Score` verdeckt zusammenfließen.

### Was zeigen die Leaderboard Metriken?

Das Leaderboard ist ein **Decision-Making Tool**, nicht nur ein Ranking. Es berücksichtigt immer nur den **letzten lokalen Run** pro Modell.

| Metrik (Auszug) | Zu finden in | Bedeutung |
|-----------------|--------------|-----------|
| **Badge** | Beide | Qualitäts-Tier (🏆 Gold, 🥈 Silver, 🥉 Bronze, ⚖️ Standard) |
| **Speed Profile** | Beide | Mix aus Speed & Skill (z. B. ⚡ Real-Time DevOps) |
| **Total Score** | Beide | 50/50 Gewichtung aus Routine & Reasoning |
| **Routine Score** | Detailed | Leistung bei einfachen Tasks (Tippfehler, UX Text) |
| **Reasoning Score** | Detailed | Leistung bei Logik-Rätseln & System-Architektur |
| **P95 Time (s)** | Detailed | Latenz-Spitze: Dauer der langsamsten 5% der Requests |
| **Max Time (s)** | Detailed | Dauer des extremsten Einzelausreißers |
| **Timeout Count** | Detailed | Anzahl der erzwungenen Abbrüche (API / Lokaler Error) |

______________________________________________________________________

## 🏅 Badges & Klassen

### 1. Quality Tiers (Absolute Standards)

| Badge | Score Hürde | Bedeutung | |-------|-------------|-----------| | 🏆 **Gold** | ≥ 85% | Elite, Production-Ready | | 🥈 **Silver** | ≥ 70% | Solide für die meisten Aufgaben | | 🥉 **Bronze** | ≥ 55% | OK für einfache Tasks | | ⚖️ **Standard** | < 55% | Needs Improvement |

### 2. Speed Classes

| Klasse | Zeitlimit | Use Case | |--------|-----------|----------| | ⚡ **Fast** | < 40s | Autocomplete, Chat, Realtime | | ⏱️ **Medium** | 40s - 80s | Code Review, Doku, Interaktiv | | 🐢 **Slow** | > 80s | Batch Processing, Deep Analysis |

### 3. Skill Profiles (Beispiele)

- **Fast All-Rounder:** Schnell & gut in allem (z.B. Mistral Large)
- **Fast Code Reviewer:** Spezialist für Code, sehr schnell (z.B. Qwen 2.5 Coder)
- **Slow Deep Thinker:** Stark im Reasoning, aber langsam (z.B. Phi-4)

______________________________________________________________________

## ⏱️ Performance Metriken

CrucibleMark unterscheidet präzise zwischen **Ladezeit** und **Ausführungszeit**:

1. **Phase 1: Warm-up Probe (Kaltstart Messung)**

   - Vor jedem Benchmark sendet der Runner eine "Ping"-Anfrage (`system_warmup_probe`).
   - **Ziel:** Messen, wie lange das Modell braucht, um von der Festplatte in den VRAM zu laden (Initial Load).
   - Dieser Wert landet als `Initial Load` im Leaderboard, fließt aber **nicht** in die Durchschnitts-Geschwindigkeit ein.

1. **Phase 2: Benchmark (Warmzustand)**

   - Die eigentlichen Tests laufen auf dem bereits geladenen Modell.
   - **Execution Time:** Die reine Rechenzeit für die Antwort-Generierung (ohne Lade-Latenz).
   - Dies sorgt für faire Messergebnisse der Modell-Geschwindigkeit, unabhängig von der Hardware-Startzeit.

> **Hinweis:** Bitte beachten Sie, dass es sich hierbei um **hardwareabhängige Momentaufnahmen** handelt. Die Werte (`Initial Load` & `Avg Speed`) evaluieren nicht das isolierte Modell, sondern das Zusammenspiel aus Modellarchitektur und der spezifischen Hardwareumgebung (RAM, GPU), auf der der Test ausgeführt wird.

In den CSV-Ausgaben (`local_models_benchmark.csv`) befindet sich eine dedizierte Spalte `load_time`.

______________________________________________________________________

## 🛡️ Crash Recovery & Sessions

### Was passiert bei Absturz?

CrucibleMark speichert den Fortschritt automatisch:

1. **Checkpoint erstellt:** Nach jedem abgeschlossenen Asset
1. **Session-Datei:** `outputs/temp/session_<model>.json`
1. **Auto-Resume:** Beim nächsten Start wird gefragt:
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

______________________________________________________________________

## 🔍 Troubleshooting

### Problem: "Model not found"

**Lösung:**

```bash
# Prüfen, ob Modell verfügbar ist
make list-models

# Falls nicht da (Ollama):
ollama pull qwen2.5:14b
```

______________________________________________________________________

### Problem: "API Rate Limit" (kommerzielle Modelle)

**Symptom:**

```text
❌ Error: 429 Too Many Requests
```

**Lösung:**

- Warten Sie 60 Sekunden
- CrucibleMark hat **automatisches Retry** mit Exponential Backoff
- Bei wiederholten Fehlern: API-Key-Limit prüfen

______________________________________________________________________

### Problem: Scores sind 0% (obwohl Antwort gut aussieht)

**Debug-Modus aktivieren:**

```bash
python scripts/run_local_benchmark.py --debug-responses
```

**Was passiert:**

- Vollständige Modell-Antworten werden gespeichert
- Enthält: Score, Reasoning, ungekürzte Antwort

**Automatisch aktiviert bei:**


______________________________________________________________________

### Problem: Benchmark hängt bei "Generating response..."

**Mögliche Ursachen:**

1. **Ollama offline:** `ollama list` testen
1. **Modell zu groß:** RAM voll (prüfen Sie `htop` / Task Manager)
1. **API-Timeout:** Kommerzielle Modelle > 120s Response-Zeit

**Lösung:**

```bash
# Ollama neustarten
ollama restart

# Kleineres Modell testen
make benchmark MODEL=qwen2.5:7b
```

______________________________________________________________________

## 📊 Daten-Management

### Wo werden Ergebnisse gespeichert?

```text
benchmark_scores/
├── local_models_benchmark.csv       # Rohdaten (jeder einzelne Test)
├── commercial_models_benchmark.csv  # Rohdaten (API-Modelle)
├── benchmark_leaderboard.csv        # Aggregierte Rankings
├── political_compass_results.csv    # Spezial-Modul (Koordinaten)
```

______________________________________________________________________

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

______________________________________________________________________

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

______________________________________________________________________

## 📈 Fortgeschrittene Nutzung

### Kosten schätzen (vor Batch-Run)

```bash
make analyze-costs
```

**Output:**

```text
Estimated API costs:
- Mistral Large: $12.50 (500 requests)
- GPT-4: $28.00 (500 requests)
Total: $40.50
```

______________________________________________________________________

### Nur fehlgeschlagene Tests wiederholen

```bash
make benchmark-auto
```

(Smart-Skip überspringt erfolgreiche Tests automatisch)

______________________________________________________________________

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

______________________________________________________________________

## 🆘 Hilfe & Support

### Logs prüfen

**Konsole:** Zeigt nur wichtige Meldungen (User-freundlich)

**Vollständiges Log:**

```bash
tail -f logs/crucible.log
```

(Enthält alle technischen Details, Warnings, Tracebacks)

______________________________________________________________________

### Projekt validieren

```bash
# Struktur prüfen
make validate-structure

# Assets prüfen (YAML-Schema)
make validate
```

______________________________________________________________________

### Community & Docs

- **GitHub Issues:** [github.com/yourusername/cruciblemark/issues](https://github.com/yourusername/cruciblemark/issues)
- **Discussions:** [github.com/yourusername/cruciblemark/discussions](https://github.com/yourusername/cruciblemark/discussions)
- **Developer Guide:** Siehe `docs/DEVELOPER_GUIDE.md` (für Modul-Entwicklung)
- **Architecture:** Siehe `docs/ARCHITECTURE.md` (für System-Design)

______________________________________________________________________

## 🎓 Nächste Schritte

**Nach dem ersten Benchmark:**

1. ✅ Leaderboard studieren (`benchmark_leaderboard.csv`)
1. ✅ Badge-Kategorien verstehen (God Mode vs Daily Driver)
1. ✅ Modell für Ihren Use Case wählen

**Für Fortgeschrittene:**

- Eigene Module erstellen (siehe `DEVELOPER_GUIDE.md`)
- Neues Modul initialisieren (`make create-module`)
- Custom Scoring-Logik implementieren

______________________________________________________________________

## 🏗️ Creating New Tests (v3.0+)

All new reasoning tests **must** use v3.0 rubric-based scoring. The legacy system is deprecated.

### 1. Define Rubric in `evaluators.py`

```python
RUBRICS = {
    'your_test_001': {
        'dimension_name': {
            'weight': 25,  # Max points (0-100 total)
            'description': 'What this dimension measures',
            'keywords': ['keyword1', 'keyword2', ...]
        },
        # ... more dimensions (must sum to 100)
    }
}
```

### 2. Set scoring_version in YAML Asset

```yaml
metadata:
  scoring_version: 2.0
```

### 3. Test Locally

```bash
make benchmark MODEL=your-test-model
```

______________________________________________________________________

**Happy Benchmarking! 🚀**

______________________________________________________________________

**Dokumenten-Version:** 3.0.0 (Rewrite Mar 2026)\
**Kompatibel mit:** CrucibleMark v3.0.0+


### C. Political Compass & Safety Tests

Das `political_compass` Modul nutzt eine eigenständige Sicherheitsarchitektur und speichert nach jedem Block einen Zwischenstand (Checkpointing). Dies ist bei über 70 Fragen elementar.

- **Standard-Lauf (Resume/Caching):**
  ```bash
  make political-compass MODEL=modell_name
  ```
  Setzt einen abgebrochenen PC-Run exakt dort fort, wo er aufgehört hat. Bereits gespeicherte Blöcke und finale Scores im Cache werden intelligent übersprungen und die noch fehlenden Fragen abgearbeitet.

- **Kompletter Neustart (Forced-Run):**
  ```bash
  make political-compass MODEL=modell_name FORCE=1
  ```
  Erzwingt einen kompletten Neustart des Kompass-Tests. Sämtliche bisherigen Caches für dieses Modell werden verworfen und der volle Test (Vanilla + Forced Modus) wird von vorne begonnen.

- **Anomalie- & Sicherheitsprüfung:**
  ```bash
  make political-compass-safe MODEL=modell_name
  ```
  Startet den ausgedehnten "Safe-Run" (Triple-Run). Hierbei muss das Modell den gesamten Testablauf zwingend drei Mal komplett asynchron durchlaufen. Die Pipeline mittelt die korrekten Vektoren und sortiert mutmaßlich halluzinierte Extreme aus, um auf weichen Vektor-Shifts eine stabile Grund-Ausrichtung zu validieren.

- **Human Baseline:**
  ```bash
  make benchmark-human
  ```
  Startet das interaktive Terminal-Interface, in dem ein menschlicher Benutzer den CrucibleMark Political Compass Test beantworten kann, um als Referenzwert (`Human Baseline`) in den Auswertungen mit aufzutauchen.


### C. Political Compass & Safety Tests

Das `political_compass` Modul nutzt eine eigenständige Sicherheitsarchitektur und speichert nach jedem Block einen Zwischenstand (Checkpointing). Dies ist bei über 70 Fragen elementar.

- **Standard-Lauf (Resume/Caching):**
  ```bash
  make political-compass MODEL=modell_name
  ```
  Setzt einen abgebrochenen PC-Run exakt dort fort, wo er aufgehört hat. Bereits gespeicherte Blöcke und finale Scores im Cache werden intelligent übersprungen und die noch fehlenden Fragen abgearbeitet.

- **Kompletter Neustart (Forced-Run):**
  ```bash
  make political-compass MODEL=modell_name FORCE=1
  ```
  Erzwingt einen kompletten Neustart des Kompass-Tests. Sämtliche bisherigen Caches für dieses Modell werden verworfen und der volle Test (Vanilla + Forced Modus) wird von vorne begonnen.

- **Anomalie- & Sicherheitsprüfung:**
  ```bash
  make political-compass-safe MODEL=modell_name
  ```
  Startet den ausgedehnten "Safe-Run" (Triple-Run). Hierbei muss das Modell den gesamten Testablauf zwingend drei Mal komplett asynchron durchlaufen. Die Pipeline mittelt die korrekten Vektoren und sortiert mutmaßlich halluzinierte Extreme aus, um auf weichen Vektor-Shifts eine stabile Grund-Ausrichtung zu validieren.

- **Human Baseline:**
  ```bash
  make benchmark-human
  ```
  Startet das interaktive Terminal-Interface, in dem ein menschlicher Benutzer den CrucibleMark Political Compass Test beantworten kann, um als Referenzwert (`Human Baseline`) in den Auswertungen mit aufzutauchen.


### C. Political Compass & Safety Tests

Das `political_compass` Modul nutzt eine eigenständige Sicherheitsarchitektur und speichert nach jedem Block einen Zwischenstand (Checkpointing). Dies ist bei über 70 Fragen elementar.

- **Standard-Lauf (Resume/Caching):**
  ```bash
  make political-compass MODEL=modell_name
  ```
  Setzt einen abgebrochenen PC-Run exakt dort fort, wo er aufgehört hat. Bereits gespeicherte Blöcke und finale Scores im Cache werden intelligent übersprungen und die noch fehlenden Fragen abgearbeitet.

- **Kompletter Neustart (Forced-Run):**
  ```bash
  make political-compass MODEL=modell_name FORCE=1
  ```
  Erzwingt einen kompletten Neustart des Kompass-Tests. Sämtliche bisherigen Caches für dieses Modell werden verworfen und der volle Test (Vanilla + Forced Modus) wird von vorne begonnen.

- **Anomalie- & Sicherheitsprüfung:**
  ```bash
  make political-compass-safe MODEL=modell_name
  ```
  Startet den ausgedehnten "Safe-Run" (Triple-Run). Hierbei muss das Modell den gesamten Testablauf zwingend drei Mal komplett asynchron durchlaufen. Die Pipeline mittelt die korrekten Vektoren und sortiert mutmaßlich halluzinierte Extreme aus, um auf weichen Vektor-Shifts eine stabile Grund-Ausrichtung zu validieren.

- **Human Baseline:**
  ```bash
  make benchmark-human
  ```
  Startet das interaktive Terminal-Interface, in dem ein menschlicher Benutzer den CrucibleMark Political Compass Test beantworten kann, um als Referenzwert (`Human Baseline`) in den Auswertungen mit aufzutauchen.

## D. Meta-Reviews (Magazin-Style) generieren

CrucibleMark bietet ein Modul zur Erstellung von redaktionellen Zusammenfassungen, den Meta-Reviews.

Die Erstellung wird über den konsolidierten Befehl `make review` gesteuert, der verschiedene Aufruf-Flags unterstützt:

```bash
# Review für ein konkretes Modell erstellen
make review MODEL="meta-llama/Llama-3.1-8B-Instruct"

# Reviews für ALLE kürzlich getesteten Modelle im Rutsch erstellen
make review ALL=1

# Speziellen Bias/Safety-Review für ein Modell erstellen
make review MODEL="meta-llama/Llama-3.1-8B-Instruct" TYPE="bias"

# Spezielle Bias/Safety-Reviews für ALLE Modelle erstellen
make review ALL=1 TYPE="bias"
```

> **Hinweis:** Weitere Details zur Funktionsweise, Konfiguration und Anpassung des Meta-Reviewers findest du in [AUDIT_AND_METAREVIEW.md](AUDIT_AND_METAREVIEW.md).

## E. Analysen & Modell-Vergleiche (Diff Results)

Hast du zwei verschiedene Benchmark-Läufe, die du miteinander vergleichen möchtest? Das CrucibleMark Framework bietet ein iteratives Comparison-Tool:

```bash
make diff-results
```

Mit Start dieses Befehls öffnet sich ein interaktiver UI-Assistent im Terminal, der automatisch alle existierenden JSON-Resultate aus `outputs/runs/` sammelt und dir verschiedene Vergleichs-Modi anbietet:

1. **Interner Vergleich:** Prüft, ob sich dasselbe Modell im Vergleich zu einem früheren Lauf verschlechtert hat (z. B. nach Anpassung des System-Prompts oder der Framework-Version). Das System schlägt dir automatisch den älteren Lauf als Referenz und den neueren als Test vor.
2. **Modell-Vergleich:** Lässt zwei unterschiedliche Modelle direkt gegeneinander antreten (Referenz-Modell vs. Test-Modell). Auch hier wählt das System jeweils den neuesten Run der beiden gewählten Modelle.
3. **Manuelle Auswahl:** Erlaubt dir, aus allen Dateien individuell und frei die Referenz- und die Test-Datei zu bestimmen.

Alternativ kannst du für schnelle CLI-Automatisierung auch direkt Dateipfade mit optionalem Abweichungsschwellenwert (z.B. `--threshold 0.15` für $\ge 15\%$) via Makefile-Flags mitgeben:

```bash
make diff-results REF=outputs/runs/v1.json TEST=outputs/runs/v2.json THRESH=0.15
```

## F. Tooling & Maintenance Parameter

CrucibleMark bietet ein umfangreiches Repertoire an Tools, um das Framework sauber und aktuell zu halten:

### 1. Zusätzliche Benchmark- & Test-Aufrufe
Neben den regulären `make benchmark` Befehlen existieren folgende Ergänzungen:
- **`make run-benchmark`**: Öffnet einen rein interaktiven Terminal-Wizard zur geführten Modellauswahl.
- **`make benchmark-cross-model MODULE=name`**: Evaluiert alle bekannten Modelle zwingend gegen *ein einziges* Modul (hilfreich bei der Modul-Entwicklung).
- **`make test`**: Startet via `pytest` alle internen Unit-Tests des Frameworks.

### 2. Systemgesundheit & Validierung
- **`make judge-health`**: Führt Connectivity-Pings gegen die konfigurierten Provider (OpenAI, Anthropic, lokales Ollama) durch, um API-Keys zu testen.
- **`make list-modules`**: Listet alle momentan aktivierten Benchmark-Kategorien auf.
- **`make validate`** / **`make validate-single ASSET=pfad`**: Validiert das YAML-Schema der hinterlegten Tests.
- **`make validate-structure`**: Testet, ob das Verzeichnis-Layout den Architekturvorgaben entspricht.
- **`make audit-markdown`**: Durchsucht und bereinigt (mit optionalem Flag `FIX=1`) fehlerhafte Formatierungen (wie Trailing Whitespaces) in Dokumenten.

### 3. Projekt-Hygiene & Cleanup-Befehle (Konsolidiert)

Die Cleanup-Prozesse wurden in einem zentralen, interaktiven System zusammengefasst.

- **`make clean-wizard`**: Startet den interaktiven Cleanup-Wizard im Terminal, über den du flexibel Caches, Runs oder Ergebnisse einzelner Modelle sicher und geführt bereinigen kannst. (Empfohlen)
- **`make clean`**: Löscht Caches und temporäre Dateileichen (z.B. Python Bytecode, `__pycache__`, alte Reports, Audit-Logs). (Kann kombiniert werden mit Flags: `make clean MODEL=Name`, `make clean MODULE=Key`)
- **`make clean-sessions`**: Löscht temporäre Session-Zwischenspeicher.
- **`make clean-runs`**: Bereinigt ausufernde Run-Ordner und behält standardmäßig nur den 1 aktuellsten Run pro Modell. (`make clean-runs FORCE=1` überspringt Nachfragen).
- **`make clean-csv`**: Löscht alle standardmäßig generierten Benchmark-CSV Dateien.
- **`make clean-all`**: Radikal-Reset. Löscht zusätzlich zur Standard-Cache-Leerung **alle** bisherigen Benchmark-Run Ordner und CSV-Scores. DANGER.
