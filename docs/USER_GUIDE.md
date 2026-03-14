# User Guide: Benchmarking Workflow

**Zielgruppe:** Alle, die CrucibleMark nutzen wollen – ohne Code-Kenntnisse erforderlich.

**Was Sie hier finden:**

- Quick Start (3 Befehle bis zum ersten Ergebnis)
- Benchmark-Steuerung (Modus-Auswahl, Modell-Filter)
- Auswertung & Leaderboard
- Troubleshooting

> **Voraussetzung:** Installation abgeschlossen (`make install` ausgeführt).

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
make benchmark-single MODEL=qwen2.5:14b
```

**Optional: Nur ein Modul testen:**

```bash
make benchmark-single MODEL=qwen2.5:14b MODULE=code_quality
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

Für komplexe Reasoning-Aufgaben nutzen wir **v2.0 Granular Rubrics** für faire Teilpunkte.

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

### 3. Audit Mode (Log-Protokoll)

Der **Audit Mode** generiert zu jedem getesteten Asset eine übersichtliche Markdown-Datei. Diese Dateien protokollieren exakt:
1. Den vollständig evaluierten **Prompt**, der an das Modell geschickt wurde.
2. Die **Antwort** des bewerteten Modells.
3. Die detaillierte Herleitung der Bewertung (sowohl Regex-Details als auch LLM-Judge Reasoning).

Um den Modus zu aktivieren:
```bash
make benchmark-audit
```
Alle generierten Markdown-Files findest du im Ordner `outputs/audit_logs/`. Dieser Modus ist besonders hilfreich, wenn du analysieren möchtest, *warum* ein Modell eine bestimmte (oder unerwartete) Punktzahl bekommen hat oder wenn du System-Prompts finetunen möchtest.

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

**Output:** `benchmark_scores/benchmark_leaderboard.csv`

### Was zeigt das Leaderboard?

Das Leaderboard ist ein **Decision-Making Tool**, nicht nur ein Ranking. Es berücksichtigt immer nur den **letzten lokalen Run** pro Modell, sodass Hardware-Upgrades (z.B. SSD statt HDD) sofort sichtbar werden.

| Spalte | Bedeutung | |--------|-----------| | **Badge** | Qualitäts-Tier (🏆 Gold, 🥈 Silver, 🥉 Bronze, ⚖️ Standard) | | **Speed Class** | ⚡ Fast (\<40s), ⏱️ Medium, 🐢 Slow (>80s) | | **Initial Load** | **Cold Start Zeit** aus der separaten Warm-up Phase. Verfälscht nicht den Average. | | **Performance/s** | Speed-Quality Tradeoff (höher ist besser) | | **Cost per 1K** | Echte API-Kosten pro 1000 Tests (nur kommerziell) | | **Total Score** | (Routine Score + Reasoning Score) / 2 |

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

```
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
- Pfad: `benchmark_scores/debug_responses/<model>_<asset>.txt`
- Enthält: Score, Reasoning, ungekürzte Antwort

**Automatisch aktiviert bei:**

- Scores < 30% (Asset wird automatisch geloggt)

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
make benchmark-single MODEL=qwen2.5:7b
```

______________________________________________________________________

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

```
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
make validate-assets
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
- Golden Standard aktualisieren (`make generate-golden`)
- Custom Scoring-Logik implementieren

______________________________________________________________________

## 🏗️ Creating New Tests (v2.1+)

All new reasoning tests **must** use v2.1 rubric-based scoring. The legacy system is deprecated.

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
make benchmark-single MODEL=your-test-model
```

______________________________________________________________________

**Happy Benchmarking! 🚀**

______________________________________________________________________

**Dokumenten-Version:** 1.0.0 (Rewrite Feb 2026)\
**Kompatibel mit:** CrucibleMark v0.9.5+
