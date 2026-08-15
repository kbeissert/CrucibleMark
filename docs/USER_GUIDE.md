# Benutzerhandbuch: Benchmarking-Workflow

**Stand: v5.1.0 · 2026-07-14**

**Zielgruppe:** Alle, die CrucibleMark produktiv nutzen möchten, ohne in den Code einzusteigen.
**Inhalt:**

- Quick Start in drei Befehlen
- Benchmark-Steuerung (Modi, Modell-Filter)
- Auswertung und Leaderboard
- Fehlerbehebung und Daten-Management

> **Voraussetzung:** Python 3.10+ und venv eingerichtet (siehe [README.md](../README.md) und [SETUP_GUIDE.md](SETUP_GUIDE.md)).
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> pip install -r requirements.txt
> ```

## CUDA-Beschleunigung (Windows und Linux mit NVIDIA-GPU)

Für maximale Geschwindigkeit im Semantic Mode vor `pip install -r requirements.txt` die native PyTorch-Variante für CUDA installieren. Andernfalls fällt PyTorch auf die CPU-Variante zurück.

```bash
# Beispiel für CUDA 12.1 (Windows und Linux)
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

> 🛑 Vor dem ersten Start den [Setup-Guide](SETUP_GUIDE.md) lesen. Ohne eingetragene API-Keys, Module und Hardware-Profil bricht der erste Lauf mit Konfigurationsfehlern ab.

---

## Quick Start (drei Befehle)

```bash
# 1. Verfügbare Modelle prüfen
make list-models

# 2. Benchmark starten (Production-Modus)
make benchmark
# Schneller Dev-Modus für Tests:
make benchmark-dev

# 3. Leaderboard erzeugen
make leaderboard
```

Die Ergebnisse landen in `benchmark_scores/benchmark_leaderboard.csv`.

---

## Der interaktive Wizard

```bash
make benchmark
```

Der Wizard führt in vier Schritten durch den ersten Lauf:

1. **Modus wählen** — Single Model für gezielte Tests, Batch Mode für die volle Palette.
2. **Modell auswählen** — Liste aller lokalen und kommerziellen Modelle mit Connectivity-Check.
3. **Module aktivieren** — Code Quality, UX Writing, Reasoning oder "All".
4. **Start** — Progress-Anzeige, Live-Schreiben in die CSV.

---

## Benchmark-Modi

### A — Single Model (fokussiert)

Einsatz: schneller Test eines neuen Modells, Debugging bei unerwarteten Scores, gezielte Kostenkontrolle.

```bash
make benchmark MODEL=qwen2.5:14b
# Nur ein einzelnes Modul:
make benchmark MODEL=qwen2.5:14b MODULE=code_quality
```

### B — Batch-Modus (vollständig)

Einsatz: Leaderboard-Update, Vergleich zwischen lokalen und Cloud-Modellen, Overnight-Run.

```bash
make benchmark-auto
```

`benchmark-auto` ist ein Meta-Orchestrator. Er füllt fehlende Benchmark-Ergebnisse über alle aktiven Module und Provider nach. Die Smart-Skip-Logik überspringt vorhandene valide Ergebnisse, Auto-Retry fängt Fehlschläge erneut ab. Die Modell-Menge wird in `config/provider_config.yaml` gesteuert.

```bash
# Erzwungener Re-Run über alles (deaktiviert die Skip-Logik):
make benchmark-auto FORCE=1
```

> ⚠️ `FORCE=1` ignoriert vorhandene Ergebnisse und kann deutlich mehr API-Credits verbrauchen.

### C — Political Compass und Safety-Tests

Das `political_compass`-Modul nutzt eine eigenständige Sicherheitsarchitektur mit Block-Level-Checkpointing. Bei über 70 Fragen ist das elementar.

```bash
# Standard-Lauf mit Resume/Caching:
make political-compass MODEL=modell_name

# Kompletter Neustart (verwirft Caches):
make political-compass MODEL=modell_name FORCE=1

# Anomalie- und Sicherheitsprüfung (Triple-Run):
make political-compass-safe MODEL=modell_name

# Menschliche Baseline:
make benchmark-human
```

### D — Meta-Reviews generieren

```bash
make review MODEL="meta-llama/Llama-3.1-8B-Instruct"
make review ALL=1
make review MODEL="meta-llama/Llama-3.1-8B-Instruct" TYPE="bias"
make review ALL=1 TYPE="bias"
```

Model Cards und Vendor Cards liefern dem Meta-Reviewer strukturierten Kontext zu Herkunft, Stärken und Datenschutzstandards:

```bash
make model-cards MODEL=<id>
make vendor-cards
```

Seit v4.10.0 kapseln drei dedizierte Lifecycle-Targets Erstellung, Struktur-Sync und inhaltliche LLM-Recherche:

```bash
make card-create MODEL=<id>
make card-validate [MODEL=<id>]
make card-research [MODEL=<id>]
```

Details: [CARD_MANAGEMENT.md](CARD_MANAGEMENT.md#card-lifecycle-v2-ab-v4100).

Jede generierte Review enthält einen Datenschutz-Abschnitt mit Sovereign-Risk-Einschätzung (`low`, `medium`, `high`), die aus Weights-Herkunft und Deployment-Jurisdiktion kombiniert wird. Damit lässt sich eine direkte Compliance-Einordnung ohne externe Recherche treffen.

> Details: [AUDIT_AND_METAREVIEW.md](AUDIT_AND_METAREVIEW.md).

### E — Analysen und Modell-Vergleiche

```bash
make diff-results
```

Der UI-Assistent sammelt alle existierenden JSON-Resultate aus `outputs/runs/` und bietet drei Vergleichs-Modi:

1. **Interner Vergleich** — Prüfung, ob dasselbe Modell sich gegenüber einem früheren Lauf verschlechtert hat.
2. **Modell-Vergleich** — zwei Modelle direkt gegeneinander.
3. **Manuelle Auswahl** — Referenz- und Test-Datei frei bestimmen.

Alternativ direkt mit Dateipfaden:

```bash
make diff-results REF=outputs/runs/v1.json TEST=outputs/runs/v2.json THRESH=0.15
```

### F — Tooling und Wartung

#### Benchmark- und Test-Aufrufe

- **`make run-benchmark`** — interaktiver Wizard zur geführten Modellauswahl.
- **`make benchmark-cross-model MODULE=name`** — alle bekannten Modelle gegen ein Modul.
- **`make test`** — alle internen Unit-Tests via `pytest`.

#### Systemgesundheit und Validierung

- **`make judge-health`** — Connectivity-Pings gegen konfigurierte Provider.
- **`make list-modules`** — alle aktivierten Benchmark-Kategorien.
- **`make validate`** oder **`make validate-single ASSET=pfad`** — YAML-Schema-Validierung.
- **`make validate-structure`** — Verzeichnis-Layout gegen Architekturvorgaben.
- **`make audit-markdown`** — fehlerhafte Formatierungen in Dokumenten, optional mit `FIX=1`.
- **`make sync-cost-limits`** — Preiseinträge in den Model Cards prüfen (`input_price_per_1m`, `output_price_per_1m`).

#### Projekt-Hygiene

- **`make clean-wizard`** — interaktiver Cleanup-Wizard (empfohlen).
- **`make clean`** — Caches und temporäre Dateileichen; kombinierbar mit `MODEL=`, `MODULE=`.
- **`make clean-sessions`** — temporäre Session-Zwischenspeicher.
- **`make clean-runs`** — Run-Ordner, behält standardmäßig nur den aktuellsten Run pro Modell.
- **`make clean-csv`** — alle generierten Benchmark-CSV-Dateien.
- **`make clean-all`** — vollständiger Reset inklusive CSV-Scores. **Vorsicht.**

---

## Scoring im Überblick

CrucibleMark kombiniert vier Bewertungsmechanismen.

### 1 — Granular Rubric Scoring (Reasoning)

Komplexe Evaluierungen laufen über einen LLM-Judge und strukturierte Rubrics für faire Teilpunkte.

**Beispiel (Scheduling-Paradox):**

- **Problem Detection (20 Pkt):** erkannt (20/20)
- **Refusal (40 Pkt):** versuchte Lösung statt Verweigerung (0/40)
- **Analysis (25 Pkt):** korrekte Logik (15/25)
- **Total:** 35/100 statt 0

### 2 — Hybrid Scoring (General)

Standard-Module mischen 40 % Keyword-Matching mit 60 % Semantic Similarity zum Golden Standard.

> **ℹ️ Semantic Similarity:** Das lokale Modell `all-MiniLM-L6-v2` (über `sentence-transformers`) vergleicht die inhaltliche Bedeutung der Antwort mit der Musterlösung. Bei korrekter Antwort in anderen Worten erkennt das System das. Das Modell (~80 MB) lädt beim ersten Lauf einmalig und wird lokal gecacht.

### 3 — Audit-Logs und Protokolle

Der Audit-Modus erzeugt zu jedem Asset eine Markdown-Datei mit:

1. dem vollständigen Prompt an das Modell,
2. der unverfälschten Modellantwort,
3. der detaillierten Bewertungsherleitung (Metadaten, Token-Limits, Judge-Reasoning).

Audit-Logs sind standardmäßig aktiv und werden bei jedem Lauf geschrieben. Deaktivieren mit `SILENT=1` oder `--silent`:

```bash
make benchmark MODEL=modell_name SILENT=1
python run_benchmark.py --module code_quality --model modell_name --silent
```

Alle Markdown-Dateien liegen in `outputs/audit_logs/`.

### 4 — Token-Metadaten als Hinweisgrößen

Bei harten Provider-Token-Limits (etwa 8192 Token) greift ein kaskadierendes Fallback (4096, 2048 Token). Pro Asset weisen Audit-Log und Testzeile den final verwendeten Token-Wert aus. Der Judge bewertet isoliert den Output-String ohne Bias bezüglich der Konfiguration.

Modelle, die wegen Token-Limit gekürzte Antworten produzieren, eignen sich oft nicht als Document-Analysis-Agent. Diese Hinweisgrößen schützen vor unliebsamen Generation Cutoffs in eigenen Projekten.

---

## Leaderboard erzeugen

```bash
make leaderboard
```

Der Befehl erzeugt zwei CSV-Dateien in `benchmark_scores/`:

1. **`benchmark_leaderboard.csv`** (Standard, Compact) — tägliche Ansicht, Dashboards, kurze Vergleiche.
2. **`benchmark_leaderboard_detailed.csv`** (Detailed) — Architekturanalysen und Latenz-Audits. Enthält `P95 Time`, `Max Time`, `Timeout Counts`, `Routine Score` und `Reasoning Score` getrennt sowie `model_id` als rohe Config-ID (Single Source of Truth für den Web-Export).

### Spalten und Metriken

| Metrik | Datei | Bedeutung |
|---|---|---|
| **Badge** | Beide | Qualitäts-Tier (Platinum, Gold, Silver, Bronze, Standard) |
| **Speed Profile** | Beide | Mix aus Speed und Skill (etwa Real-Time DevOps) |
| **Total Score** | Beide | 50/50-Gewichtung aus Routine und Reasoning |
| **Tokens Total** | Beide | kumulierte Output-Token über alle bewerteten Module |
| **Cost per 1K (USD)** | Beide | hochgerechnete API-Kosten pro 1.000 Anfragen |
| **Routine Score** | Detailed | Leistung bei einfachen Tasks |
| **Reasoning Score** | Detailed | Leistung bei Logik-Rätseln und Systemarchitektur |
| **model_id** | Detailed | rohe Config-ID, SSOT für Web-Export und Verzeichnis-Lookup |
| **Tokens: \<Modul\>** | Detailed | Output-Token pro Modul |
| **P95 Time (s)** | Detailed | 95.-Perzentil der Antwortzeit |
| **Max Time (s)** | Detailed | extremster Einzelausreißer |
| **Timeout Count** | Detailed | Anzahl erzwungener Abbrüche |

---

## Badges und Klassen

### Quality Tiers (absolute Standards)

Die kanonischen Schwellenwerte stehen in `benchmark_config.yaml` (`scoring_tiers`). Detail-Begründung: [SCORING_METHODOLOGY.md](SCORING_METHODOLOGY.md).

| Badge | Schwelle | Bedeutung |
|---|---|---|
| 💎 **Platinum** | ≥ 95 % | SOTA Elite, nahezu perfekte Gesamtleistung |
| 🏆 **Gold** | ≥ 80 % | exzellent, konstant über alle Disziplinen |
| 🥈 **Silver** | ≥ 65 % | production-ready, gute Balance |
| 🥉 **Bronze** | ≥ 50 % | akzeptabel mit klaren Einschränkungen |
| ⚖️ **Standard** | < 50 % | eingeschränkt, nicht für komplexe Agenten |

### Speed Classes

| Klasse | Zeitlimit | Use Case |
|---|---|---|
| ⚡ **Fast** | < 40 s | Autocomplete, Chat, Realtime |
| ⏱️ **Medium** | 40–80 s | Code Review, Dokumentation, interaktiv |
| 🐢 **Slow** | > 80 s | Batch Processing, Deep Analysis |

### Skill Profiles (Beispiele)

- **Fast All-Rounder** — schnell und gut in allem (etwa Mistral Large)
- **Fast Code Reviewer** — Code-Spezialist, sehr schnell (etwa Qwen 2.5 Coder)
- **Slow Deep Thinker** — stark im Reasoning, aber langsam (etwa Phi-4)

---

## Performance-Metriken

CrucibleMark trennt präzise zwischen Ladezeit und Ausführungszeit.

**Phase 1 — Warm-up Probe (Kaltstart-Messung):** Vor jedem Benchmark sendet der Runner eine Probe-Anfrage (`system_warmup_probe`), um die VRAM-Ladezeit zu messen. Dieser Wert erscheint als `Initial Load` im Leaderboard und fließt nicht in die Durchschnittsgeschwindigkeit ein.

**Phase 2 — Benchmark (Warmzustand):** Die eigentlichen Tests laufen auf dem bereits geladenen Modell. `Execution Time` misst die reine Rechenzeit für die Antwortgenerierung.

> **Hinweis:** Die Werte sind hardwareabhängige Momentaufnahmen. Sie bewerten das Zusammenspiel aus Modellarchitektur und Hardwareumgebung (RAM, GPU), nicht das isolierte Modell.

---

## Crash Recovery und Sessions

### Verhalten bei Absturz

CrucibleMark sichert den Fortschritt automatisch:

1. **Checkpoint** nach jedem abgeschlossenen Asset
2. **Session-Datei** unter `outputs/temp/session_<model>.json`
3. **Auto-Resume** beim nächsten Start mit Abfrage:
   ```
   🔄 Found existing session for qwen2.5:14b (45% complete).
   Resume? [Y/n]
   ```

Sessions älter als 48 Stunden werden verworfen, um versehentliches Fortsetzen veralteter Tests zu vermeiden.

```bash
make clean-sessions
```

---

## Fehlerbehebung

### "Model not found"

```bash
make list-models
# Falls nicht da (Ollama):
ollama pull qwen2.5:14b
```

### API Rate Limit (kommerzielle Modelle)

```text
❌ Error: 429 Too Many Requests
```

60 Sekunden warten. CrucibleMark hat automatisches Retry mit Exponential Backoff. Bei wiederholten Fehlern das API-Key-Limit prüfen.

### Scores sind 0 %, obwohl die Antwort gut aussieht

```bash
python run_benchmark.py --debug-responses
```

### Benchmark hängt bei "Generating response…"

Mögliche Ursachen:

1. **Ollama offline** — `ollama list` testen.
2. **Modell zu groß** — RAM voll (prüfen via `htop` oder Task Manager).
3. **API-Timeout** — kommerzielle Modelle mit mehr als 120 s Antwortzeit.

```bash
ollama restart
# Kleineres Modell testen:
make benchmark MODEL=qwen2.5:7b
```

---

## Daten-Management

### Speicherorte

```text
benchmark_scores/
├── local_models_benchmark.csv       # Rohdaten lokale Modelle
├── cloud_models_benchmark.csv       # Rohdaten Cloud Open-Weights
├── commercial_models_benchmark.csv  # Rohdaten Closed-Source API
├── benchmark_leaderboard.csv        # aggregierte Rankings
├── political_compass_results.csv    # Spezial-Modul
```

### Backup

```bash
make backup
```

Gesichert werden alle CSV-Dateien, Konfigurationen und Golden Standards als `backups/cruciblemark_backup_YYYYMMDD.tar.gz`.

### Bereinigung

> ⚠️ Die folgenden Befehle löschen Daten unwiderruflich.

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

Preise stehen ausschließlich in den Model Cards (`benchmark_scores/model_cards/*.json`) als `input_price_per_1m` und `output_price_per_1m` (USD pro 1 Million Token).

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

### Kosten schätzen (vor Batch-Run)

```bash
make analyze-costs
```

Ausgabe:

```text
Estimated API costs:
- Mistral Large: $12.50 (500 requests)
- GPT-4: $28.00 (500 requests)
Total: $40.50
```

### Fehlgeschlagene Tests wiederholen

```bash
make benchmark-auto
```

Smart-Skip überspringt erfolgreiche Tests automatisch.

### Module aktivieren und deaktivieren

```yaml
modules:
  political_compass:
    enabled: false
```

```bash
make leaderboard
```

---

## Hilfe

### Logs prüfen

```bash
tail -f logs/crucible.log
```

### Projekt validieren

```bash
make validate-structure
make validate
```

### Community und Docs

- **GitHub Issues:** [github.com/kbeissert/cruciblemark/issues](https://github.com/kbeissert/cruciblemark/issues)
- **Entwicklerhandbuch:** [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- **Architektur:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Glossar:** [GLOSSAR.md](GLOSSAR.md)

---

## Nächste Schritte

Nach dem ersten Benchmark:

1. Leaderboard studieren (`benchmark_scores/benchmark_leaderboard.csv`).
2. Badge-Kategorien verstehen (Platinum bis Standard).
3. Modell für den eigenen Use Case wählen.

Für eigene Module: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md).

---

## Neue Tests erstellen (v3.0+)

Alle neuen Reasoning-Tests verwenden das v3.0-Rubrik-Scoring. Das Legacy-System ist deprecated.

### 1 — Rubrik in `evaluators.py` definieren

```python
RUBRICS = {
    'your_test_001': {
        'dimension_name': {
            'weight': 25,
            'description': 'What this dimension measures',
            'keywords': ['keyword1', 'keyword2', ...]
        }
    }
}
```

### 2 — `scoring_version` im YAML-Asset setzen

```yaml
metadata:
  scoring_version: 2.0
```

### 3 — Lokal testen

```bash
make benchmark MODEL=your-test-model
```

---

**Dokumenten-Version:** 5.1.3 (Ueberarbeitung 2026-08)
**Kompatibel mit:** CrucibleMark v4.10.x und v5.x