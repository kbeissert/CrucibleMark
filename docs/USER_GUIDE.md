# Benutzerhandbuch: Benchmarking-Workflow

**Zielgruppe:** Alle, die CrucibleMark nutzen wollen – ohne Code-Kenntnisse erforderlich.

**Inhalt:**

- Quick Start (drei Befehle bis zum ersten Ergebnis)
- Benchmark-Steuerung (Modus-Auswahl, Modell-Filter)
- Auswertung & Leaderboard
- Fehlerbehebung

> **Voraussetzung:** Installation abgeschlossen (`make install` ausgeführt).

## Besonderheit für Windows/Linux mit NVIDIA GPU (CUDA)

Für maximale Geschwindigkeit im Semantic Mode vor `make install` die native PyTorch-Variante für CUDA installieren, andernfalls nutzt PyTorch als Fallback die langsamere CPU.

```bash
# Beispiel für CUDA 12.1 (Windows/Linux)
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

---

🛑 **Vor dem ersten Start** den [Setup-Guide (SETUP_GUIDE.md)](SETUP_GUIDE.md) lesen. Dort müssen API-Keys, Module und Hardware eingetragen werden, sonst kommt es zu Fehlern.

---

## Quick Start (3 Befehle)

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

**Fertig.** Die Ergebnisse liegen in `benchmark_scores/benchmark_leaderboard.csv`.

---

## Der Interaktive Wizard

Der einfachste Weg, Benchmarks zu starten:

```bash
make benchmark
```

### Was passiert?

1. **Modus wählen:**

   - **Single Model** – ein spezifisches Modell testen (z. B. nur Qwen 2.5)
   - **Batch Mode** – alle verfügbaren Modelle auf einmal testen

2. **Modell auswählen:**

   - Liste aller lokalen (Ollama) und kommerziellen Modelle
   - Mit Connectivity-Check (✅ verfügbar oder ❌ offline)

3. **Module aktivieren:**

   - Code Quality, UX Writing, Reasoning, u. a.
   - Oder „All" für vollständigen Test

4. **Automatischer Start:**

   - Progress-Bar zeigt Fortschritt
   - Ergebnisse werden live in CSV geschrieben

---

## Benchmark-Modi im Detail

### A. Single Model (Fokussiert)

**Wann nutzen?**

- Schneller Test eines neuen Modells
- Debugging (wenn ein Modell unerwartete Scores hat)
- API-Kosten sparen (nur ein Modell testen)

```bash
make benchmark MODEL=qwen2.5:14b
```

**Optional: Nur ein Modul testen:**

```bash
make benchmark MODEL=qwen2.5:14b MODULE=code_quality
```

---

### B. Batch-Modus (Vollständig)

**Wann nutzen?**

- Leaderboard-Update (alle Modelle auf neuesten Stand bringen)
- Vergleich zwischen lokalen, Cloud-Open-Weights- und kommerziellen Closed-Source-Modellen
- Overnight-Run (dauert zwei bis sechs Stunden je nach Anzahl)

```bash
make benchmark-auto
```

**Was ist „auto"?**

- **Zweck:** `benchmark_auto` ist ein Meta-Orchestrator zum Auffüllen fehlender Benchmark-Ergebnisse über alle aktiven Module und Provider hinweg.
- **Smart Skipping:** Überspringt bereits vorhandene und gültige Ergebnisse (Autofill-Logik), damit keine unnötigen Re-Runs stattfinden.
- **Auto-Retry:** Führt fehlgeschlagene Tests erneut aus
- **Kosten-Effizienz:** Keine doppelten API-Calls

**Welche Modelle werden getestet?**

- Die Menge der zu testenden LLMs wird in `config/provider_config.yaml` gesteuert.
- `benchmark_auto` nutzt die dort aktivierten Provider und deren Modell-Listen als Single Source of Truth.
- Du kannst die Menge direkt über die Config verändern, z. B. durch Ein-/Auskommentieren einzelner Modell-Einträge oder über `enabled`-Flags.

**Forced Re-Run (alles neu testen):**

```bash
make benchmark-auto FORCE=1
```

⚠️ **Warnung:** `FORCE=1` schaltet die Skip-Logik aus (ignoriert vorhandene Ergebnisse) und kann deutlich mehr API-Credits verbrauchen.

---

### C. Political Compass & Safety-Tests

Das `political_compass`-Modul nutzt eine eigenständige Sicherheitsarchitektur und speichert nach jedem Block einen Zwischenstand (Checkpointing). Das ist bei über 70 Fragen elementar.

- **Standard-Lauf (Resume/Caching):**
  ```bash
  make political-compass MODEL=modell_name
  ```
  Setzt einen abgebrochenen Run exakt dort fort, wo er aufgehört hat. Bereits gespeicherte Blöcke überspringt das System.

- **Kompletter Neustart (Forced-Run):**
  ```bash
  make political-compass MODEL=modell_name FORCE=1
  ```
  Verwirft sämtliche bisherigen Caches und startet den vollen Test (Vanilla und Forced Modus) von vorne.

- **Anomalie- & Sicherheitsprüfung:**
  ```bash
  make political-compass-safe MODEL=modell_name
  ```
  Startet den ausgedehnten „Safe-Run" (Triple-Run). Das Modell durchläuft den Testablauf zwingend drei Mal. Die Pipeline mittelt die korrekten Vektoren und sortiert halluzinierte Extreme aus.

- **Human Baseline:**
  ```bash
  make benchmark-human
  ```
  Startet das interaktive Terminal-Interface, in dem ein menschlicher Tester den Political Compass beantwortet und als Referenzwert (`Human Baseline`) in den Auswertungen erscheint.

---

### D. Meta-Reviews (Magazin-Style) generieren

```bash
# Review für ein konkretes Modell erstellen
make review MODEL="meta-llama/Llama-3.1-8B-Instruct"

# Reviews für ALLE kürzlich getesteten Modelle erstellen
make review ALL=1

# Speziellen Bias/Safety-Review für ein Modell erstellen
make review MODEL="meta-llama/Llama-3.1-8B-Instruct" TYPE="bias"

# Spezielle Bias/Safety-Reviews für ALLE Modelle erstellen
make review ALL=1 TYPE="bias"
```

**Model Cards & Vendor Cards** liefern dem Meta-Reviewer strukturierten Kontext zu Herkunft, Stärken und — besonders relevant für europäische Akteure — Datenschutzstandards:

```bash
make model-cards MODEL=<id>  # Neues Model Card Template anlegen (dann manuell befüllen)
make vendor-cards   # Vendor Cards generieren (CLOUD Act, GDPR DPA, Datenstandort, Retention)
```

Jeder generierten Review enthält einen **Datenschutz-Abschnitt** mit einer Sovereign-Risk-Einschätzung (`low` / `medium` / `high`), die aus Weights-Herkunft und Deployment-Jurisdiktion des Providers kombiniert wird. Das ermöglicht eine direkte Compliance-Einordnung ohne externen Rechercheaufwand.

> Weitere Details: [AUDIT_AND_METAREVIEW.md](AUDIT_AND_METAREVIEW.md).

---

### E. Analysen & Modell-Vergleiche (Diff Results)

```bash
make diff-results
```

Der interaktive UI-Assistent sammelt alle existierenden JSON-Resultate aus `outputs/runs/` und bietet drei Vergleichs-Modi:

1. **Interner Vergleich:** Prüft, ob sich dasselbe Modell gegenüber einem früheren Lauf verschlechtert hat.
2. **Modell-Vergleich:** Zwei unterschiedliche Modelle direkt gegeneinander.
3. **Manuelle Auswahl:** Referenz- und Test-Datei frei bestimmen.

Alternativ direkt mit Dateipfaden:

```bash
make diff-results REF=outputs/runs/v1.json TEST=outputs/runs/v2.json THRESH=0.15
```

---

### F. Tooling & Wartung

#### 1. Zusätzliche Benchmark- & Test-Aufrufe

- **`make run-benchmark`**: Öffnet einen interaktiven Terminal-Wizard zur geführten Modellauswahl.
- **`make benchmark-cross-model MODULE=name`**: Evaluiert alle bekannten Modelle gegen ein einziges Modul.
- **`make test`**: Startet alle internen Unit-Tests des Frameworks via `pytest`.

#### 2. Systemgesundheit & Validierung

- **`make judge-health`**: Connectivity-Pings gegen konfigurierte Provider, um API-Keys zu testen.
- **`make list-modules`**: Listet alle momentan aktivierten Benchmark-Kategorien auf.
- **`make validate`** oder **`make validate-single ASSET=pfad`**: Validiert das YAML-Schema der hinterlegten Tests.
- **`make validate-structure`**: Testet, ob das Verzeichnis-Layout den Architekturvorgaben entspricht.
- **`make audit-markdown`**: Durchsucht und bereinigt (mit optionalem Flag `FIX=1`) fehlerhafte Formatierungen in Dokumenten.
- **`make sync-cost-limits`**: Prüft, ob alle konfigurierten Modelle einen Preiseintrag in ihrer Model Card haben (`benchmark_scores/model_cards/*.json`, Felder `input_price_per_1m` / `output_price_per_1m`). Zeigt fehlende Modelle als Bericht.

#### 3. Projekt-Hygiene & Cleanup-Befehle

- **`make clean-wizard`**: Startet den interaktiven Cleanup-Wizard. (Empfohlen)
- **`make clean`**: Löscht Caches und temporäre Dateileichen. (Kombinierbar mit Flags: `make clean MODEL=Name`, `make clean MODULE=Key`)
- **`make clean-sessions`**: Löscht temporäre Session-Zwischenspeicher.
- **`make clean-runs`**: Bereinigt Run-Ordner und behält standardmäßig nur den aktuellsten Run pro Modell. (`FORCE=1` überspringt Nachfragen)
- **`make clean-csv`**: Löscht alle generierten Benchmark-CSV-Dateien.
- **`make clean-all`**: Radikal-Reset. Löscht zusätzlich alle bisherigen Run-Ordner und CSV-Scores. **DANGER.**

---

## Scoring im Überblick (v1.1)

CrucibleMark nutzt unterschiedliche Scoring-Mechanismen:

### 1. Granular Rubric Scoring (Reasoning)

Für komplexe Evaluierungen nutzt das Framework den **LLM-Judge** und strukturierte Rubrics für faire Teilpunkte.

**Beispiel (Scheduling Paradox):**

- **Problem Detection (20 Pkt):** ✅ Erkannt (20/20)
- **Refusal (40 Pkt):** ❌ Versuch einer Lösung (0/40)
- **Analysis (25 Pkt):** ✅ Korrekte Logik (15/25)
- **Total:** 35/100 (statt 0)

### 2. Hybrid Scoring (General)

Standard-Module nutzen eine Mischung aus **40 % Keyword-Matching** und **60 % Semantic Similarity** zum Gold Standard.

> **ℹ️ Info zur Semantic Similarity:** CrucibleMark nutzt das lokale KI-Modell **`all-MiniLM-L6-v2`** (via `sentence-transformers`), um die inhaltliche Bedeutung der Antworten mit der Musterlösung zu vergleichen.
>
> - **Vorteil:** Antwortet das Modell korrekt, aber mit anderen Worten als die Musterlösung, erkennt das System das.
> - **Setup:** Das Modell (~80 MB) lädt `make install` einmalig herunter und cached es lokal.

### 3. Audit-Logs & Protokolle

Der **Audit-Modus** bietet ein klares, lückenloses Verständnis der Benchmarks von der Eingabe bis zur Auswertung. Er generiert zu jedem getesteten Asset eine strukturierte Markdown-Datei mit:

1. Dem vollständig evaluierten **Prompt**, der an das Modell ging.
2. Der unverfälschten **Antwort** des bewerteten Modells.
3. Der detaillierten Herleitung der Bewertung (inkl. Metadaten, Token-Limits und Judge-Reasoning).

Die Audit-Logs sind **standardmäßig aktiv** und werden bei jedem Lauf geschrieben. Zum Deaktivieren (z. B. in Entwicklungs- oder Testläufen):

```bash
make benchmark MODEL=modell_name SILENT=1
# oder direkt:
python run_benchmark.py --module code_quality --model modell_name --silent
```

Alle Markdown-Files liegen in `outputs/audit_logs/`.

### 4. Metadaten-Tracking (Token-Limits / „Kopfnoten")

Nicht jeder LLM-Provider erlaubt beliebige Output-Längen. Verweigert ein Modell ein Asset mit bis zu 8192 Token, greift ein **kaskadierendes Fallback** (z. B. auf 4096, dann 2048 Token).

- **Pro Asset:** Jeder Audit-Log und jede Testzeile weist den final verwendeten Token-Wert als Info-Feld aus.
- **LLM Judge:** Der Judge bewertet isoliert den Output-String ohne Bias bezüglich der Konfiguration.

### 5. Editor-Auswertung für System-Integration (Wrapper)

Diese Meta-Informationen spielen im finalen Editor-Bericht eine prominente Rolle. Ein Modell mit perfektem Score, das aber auf 2048 Token zugeschnürt werden musste, eignet sich oft nicht als Document-Analysis-Agent. Diese „Kopfnoten" schützen vor unliebsamen „Generation Cutoffs" in eigenen Projekten.

---

## Leaderboard generieren

```bash
make leaderboard
```

Der Befehl generiert **zwei CSV-Dateien** in `benchmark_scores/`:

1. **`benchmark_leaderboard.csv` (Standard / Compact)**
   Für die tägliche Ansicht, Dashboards und kurze Vergleiche.
2. **`benchmark_leaderboard_detailed.csv` (Detailed)**
   Für tiefgreifende Architekturanalysen und Latenz-Audits. Enthält Metriken wie `P95 Time`, `Max Time`, `Timeout Counts` sowie `Routine Score` und `Reasoning Score` separat. Enthält außerdem `model_id` (rohe Config-ID, SSOT für den Web-Export).

### Was zeigen die Leaderboard Metriken?

| Metrik (Auszug) | Zu finden in | Bedeutung |
|-----------------|--------------|-----------|
| **Badge** | Beide | Qualitäts-Tier (💎 Platinum, 🏆 Gold, 🥈 Silver, 🥉 Bronze, ⚖️ Standard) |
| **Speed Profile** | Beide | Mix aus Speed & Skill (z. B. ⚡ Real-Time DevOps) |
| **Total Score** | Beide | 50/50 Gewichtung aus Routine & Reasoning |
| **Tokens Total** | Beide | Kumulierte Output-Token über alle bewerteten Module (gleiche Basis wie Total Score) |
| **Cost per 1K (USD)** | Beide | Hochgerechnete API-Kosten pro 1.000 Anfragen. Bei Cloud Open-Weights-Modellen (z. B. Groq) wird der Paid-Tier-Preis nach Free-Tier-Ablauf zugrunde gelegt — als Referenz für den kommerziellen Produktionseinsatz. |
| **Routine Score** | Detailed | Leistung bei einfachen Tasks |
| **Reasoning Score** | Detailed | Leistung bei Logik-Rätseln & Systemarchitektur |
| **model_id** | Detailed | Rohe Config-ID (z. B. `moonshotai/kimi-k2-thinking-20251106`) — SSOT für Web-Export und Verzeichnis-Lookup |
| **Tokens: \<Modul\>** | Detailed | Output-Token pro Modul (z. B. `Tokens: Code Quality`, `Tokens: UX Writing`) |
| **P95 Time (s)** | Detailed | Latenz-Spitze: Dauer der langsamsten 5 % der Requests |
| **Max Time (s)** | Detailed | Dauer des extremsten Einzelausreißers |
| **Timeout Count** | Detailed | Anzahl der erzwungenen Abbrüche |

---

## Badges & Klassen

### 1. Quality Tiers (Absolute Standards)

Die kanonischen Schwellenwerte stammen aus `benchmark_config.yaml` (`scoring_tiers`). Details: [SCORING_METHODOLOGY.md](SCORING_METHODOLOGY.md).

| Badge | Score Hürde | Bedeutung |
|-------|-------------|-----------|
| 💎 **Platinum** | ≥ 95 % | SOTA Elite, nahezu perfekte Gesamtleistung |
| 🏆 **Gold** | ≥ 80 % | Exzellent, konstant top über alle Disziplinen |
| 🥈 **Silver** | ≥ 65 % | Production-ready, gute Balance |
| 🥉 **Bronze** | ≥ 50 % | Akzeptable Leistung, klare Einschränkungen |
| ⚖️ **Standard** | < 50 % | Eingeschränkt, nicht für komplexe Agenten |

### 2. Speed Classes

| Klasse | Zeitlimit | Use Case |
|--------|-----------|----------|
| ⚡ **Fast** | < 40s | Autocomplete, Chat, Realtime |
| ⏱️ **Medium** | 40s–80s | Code Review, Doku, Interaktiv |
| 🐢 **Slow** | > 80s | Batch Processing, Deep Analysis |

### 3. Skill Profiles (Beispiele)

- **Fast All-Rounder:** Schnell & gut in allem (z. B. Mistral Large)
- **Fast Code Reviewer:** Spezialist für Code, sehr schnell (z. B. Qwen 2.5 Coder)
- **Slow Deep Thinker:** Stark im Reasoning, aber langsam (z. B. Phi-4)

---

## Performance-Metriken

CrucibleMark unterscheidet präzise zwischen **Ladezeit** und **Ausführungszeit**:

1. **Phase 1: Warm-up Probe (Kaltstart-Messung)**
   Vor jedem Benchmark sendet der Runner eine „Ping"-Anfrage (`system_warmup_probe`), um zu messen, wie lange das Modell braucht, um in den VRAM zu laden. Dieser Wert erscheint als `Initial Load` im Leaderboard, fließt aber **nicht** in die Durchschnitts-Geschwindigkeit ein.

2. **Phase 2: Benchmark (Warmzustand)**
   Die eigentlichen Tests laufen auf dem bereits geladenen Modell. **Execution Time** ist die reine Rechenzeit für die Antwortgenerierung.

> **Hinweis:** Diese Werte sind **hardwareabhängige Momentaufnahmen**. Sie evaluieren nicht das isolierte Modell, sondern das Zusammenspiel aus Modellarchitektur und der spezifischen Hardwareumgebung (RAM, GPU).

---

## Crash Recovery & Sessions

### Was passiert bei Absturz?

CrucibleMark speichert den Fortschritt automatisch:

1. **Checkpoint erstellt:** Nach jedem abgeschlossenen Asset
2. **Session-Datei:** `outputs/temp/session_<model>.json`
3. **Auto-Resume:** Beim nächsten Start kommt die Abfrage:
   ```
   🔄 Found existing session for qwen2.5:14b (45% complete).
   Resume? [Y/n]
   ```

Sessions älter als 48 Stunden werden verworfen, um versehentliches Fortsetzen veralteter Tests zu vermeiden.

```bash
# Alle Sessions löschen (Fresh Start)
make clean-sessions
```

---

## Fehlerbehebung

### Problem: „Model not found"

```bash
# Prüfen, ob Modell verfügbar ist
make list-models

# Falls nicht da (Ollama):
ollama pull qwen2.5:14b
```

---

### Problem: „API Rate Limit" (kommerzielle Modelle)

```text
❌ Error: 429 Too Many Requests
```

60 Sekunden warten. CrucibleMark hat **automatisches Retry** mit Exponential Backoff. Bei wiederholten Fehlern: API-Key-Limit prüfen.

---

### Problem: Scores sind 0 % (obwohl Antwort gut aussieht)

```bash
python run_benchmark.py --debug-responses
```

---

### Problem: Benchmark hängt bei „Generating response..."

**Mögliche Ursachen:**

1. **Ollama offline:** `ollama list` testen
2. **Modell zu groß:** RAM voll (prüfen via `htop` oder Task Manager)
3. **API-Timeout:** Kommerzielle Modelle > 120 s Response-Zeit

```bash
# Ollama neustarten
ollama restart

# Kleineres Modell testen
make benchmark MODEL=qwen2.5:7b
```

---

## Daten-Management

### Wo werden Ergebnisse gespeichert?

```text
benchmark_scores/
├── local_models_benchmark.csv       # Rohdaten (lokale Modelle)
├── cloud_models_benchmark.csv       # Rohdaten (Cloud Open-Weights)
├── commercial_models_benchmark.csv  # Rohdaten (Closed-Source API-Modelle)
├── benchmark_leaderboard.csv        # Aggregierte Rankings
├── political_compass_results.csv    # Spezial-Modul (Koordinaten)
```

---

### Backup erstellen

```bash
make backup
```

**Was gesichert wird:**

- Alle CSV-Dateien
- Konfigurationen
- Golden Standards
- Archiviert als: `backups/cruciblemark_backup_YYYYMMDD.tar.gz`

---

### Daten bereinigen

⚠️ **Vorsicht:** Diese Befehle löschen Daten unwiderruflich.

```bash
# Einzelnes Modell entfernen
make clean-model MODEL=mistral:latest

# Modul-Ergebnisse entfernen (alle Modelle)
make clean-module MODULE=ux_writing

# Alles löschen (Komplett-Reset)
make clean-csv
```

---

## Fortgeschrittene Nutzung

### Preisliste mit konfigurierten Modellen abgleichen

Preise sind ausschließlich in den **Model Cards** (`benchmark_scores/model_cards/*.json`) gespeichert — als `input_price_per_1m` und `output_price_per_1m` (je USD pro 1 Million Tokens).

Der folgende Befehl zeigt alle Modelle ohne Preis:

```bash
make sync-cost-limits
```

Für ein neues Modell die Card um die Preisfelder ergänzen:

```json
// benchmark_scores/model_cards/<model-id>.json
{
  "input_price_per_1m":  1.0,
  "output_price_per_1m": 5.0
}
```

---

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

---

### Nur fehlgeschlagene Tests wiederholen

```bash
make benchmark-auto
```

(Smart-Skip überspringt erfolgreiche Tests automatisch)

---

### Custom-Module aktivieren/deaktivieren

```yaml
modules:
  political_compass:
    enabled: false  # Modul überspringen
```

```bash
make leaderboard  # Leaderboard neu generieren
```

---

## Hilfe & Support

### Logs prüfen

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
make validate
```

---

### Community & Docs

- **GitHub Issues:** [github.com/kbeissert/cruciblemark/issues](https://github.com/kbeissert/cruciblemark/issues)
- **Developer Guide:** Siehe `docs/DEVELOPER_GUIDE.md` (für Modul-Entwicklung)
- **Architecture:** Siehe `docs/ARCHITECTURE.md` (für System-Design)

---

## Nächste Schritte

**Nach dem ersten Benchmark:**

1. ✅ Leaderboard studieren (`benchmark_leaderboard.csv`)
2. ✅ Badge-Kategorien verstehen (Platinum bis Standard)
3. ✅ Modell für den eigenen Use Case wählen

**Für Fortgeschrittene:**

- Eigene Module erstellen (siehe `DEVELOPER_GUIDE.md`)
- Neues Modul initialisieren (`make create-module`)
- Custom Scoring-Logik implementieren

---

## Neue Tests erstellen (v3.0+)

Alle neuen Reasoning-Tests **müssen** das v3.0-Rubrik-Scoring verwenden. Das Legacy-System ist deprecated.

### 1. Rubrik in `evaluators.py` definieren

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

### 2. `scoring_version` im YAML-Asset setzen

```yaml
metadata:
  scoring_version: 2.0
```

### 3. Lokal testen

```bash
make benchmark MODEL=your-test-model
```

---

**Dokumenten-Version:** 3.1.0 (Überarbeitung März 2026)\
**Kompatibel mit:** CrucibleMark v3.4.3+
