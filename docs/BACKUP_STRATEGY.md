# CrucibleMark: Data Retention & Backup Strategy

**Zielgruppe:** Alle, die verstehen wollen, wie CrucibleMark mit Daten umgeht.

**Was Sie hier finden:**

- Philosophie: "Live vs History"
- Backup-Lifecycle (Snapshot → Prune → Consolidate)
- Workflow-Implikationen
- Technische Implementation

______________________________________________________________________

## 1. Philosophie & Purpose

Die Architektur von CrucibleMark folgt einem spezifischen Leitprinzip bezüglich Daten-Langlebigkeit:

> **"Wir bauen hier ein Werkzeug zum Vergleich von Modellen (Leaderboard), kein Werkzeug zum Monitoring von Modell-Veränderungen über die Zeit."**

Daher benötigen wir im **Live-System** (`benchmark_scores/*.csv`) keine Historie. Wir benötigen nur den **aktuellsten, validen Zustand** eines jeden Modells.

______________________________________________________________________

### Warum diese Unterscheidung wichtig ist

**Static Weights:**

- Lokale Modelle (z.B. `llama3:8b-q4_K_M`) sind statische Dateien
- Ihre Performance ändert sich nicht über Zeit

**Locked APIs:**

- Kommerzielle Modelle sind an spezifische Versionen gepinnt (z.B. `gpt-4-0613`)
- Gewährleistet Reproduzierbarkeit

**Fazit:**

- Redundante historische Daten im aktiven Workspace blähen das System auf
- Kein Mehrwert für den primären Use Case (Modell A vs Modell B vergleichen)

______________________________________________________________________

## 2. Der Backup-Lifecycle

Um Daten-Sicherheit mit Workspace-Hygiene zu balancieren, implementiert CrucibleMark einen **"Snapshot & Prune"** Workflow.

**Befehl:**

```bash
make backup
```

______________________________________________________________________

### Phase 1: The Archive (Immutable History)

**Action:** Erstelle einen `.tar.gz` Snapshot des gesamten Workspace

**Pfad:** `backups/cruciblemark_backup_YYYYMMDD_HHMMSS.tar.gz`

**Inhalt:**

- Alle CSV-Scores
- Vollständige JSON-Run-Logs
- Modul-Konfigurationen
- Golden Standards

**Regel:** Dies ist das **System of Record**.

Wenn historische Analysen jemals benötigt werden (z.B. "Wie performte GPT-4 vor einem Jahr?"), werden sie aus diesen Archiven abgerufen.

______________________________________________________________________

### Phase 2: JSON-Cleanup (Hygiene)

**Action:** Führe `scripts/cleanup_runs.py` aus

**Ziel:** `outputs/runs/**/*.json`

**Regel:** Behalte nur die **letzten 5 Runs** pro Modell.

**Warum:**

- JSON-Logs enthalten vollständige Rohdaten (Prompts, Responses, Timestamps)
- Sehr detailliert (mehrere MB pro Run)
- Ältere Logs sind sicher im Archive (Phase 1) gespeichert

______________________________________________________________________

### Phase 3: CSV-Konsolidierung (The "Latest Only" Rule)

**Action:** Führe `scripts/consolidate_csv.py` aus

**Ziel:** `benchmark_scores/*.csv`

**Logik:**

1. Lade kumulative CSV-Datei
1. Sortiere nach Timestamp (neueste zuerst)
1. Gruppiere nach eindeutigem Key: `(Model Name, Asset ID)`
1. **Dedupliziere:** Behalte **nur den einzelnen neuesten Eintrag**
1. Entferne alle älteren Duplikate

**Resultat:**

- CSV-Datei wird auf "kanonischen Zustand" zurückgesetzt
- Enthält exakt **einen validen Score** pro Test-Case

______________________________________________________________________

## 3. Workflow-Implikationen

### Continuous Benchmarking ("Rolling Updates")

Weil CSV-Dateien auf den neuesten Stand konsolidiert werden:

1. **Optimierung:** Bei `make benchmark-auto` nach einem Backup erkennt das System, dass die neuesten Testergebnisse in der CSV vorhanden sind

1. **Effizienz:** Es überspringt alle erfolgreich getesteten Assets

1. **Updates:** Es führt nur Tests für *neue* Modelle oder *neue* Assets aus

**Effekt:** Spart API-Kosten und Zeit.

______________________________________________________________________

### Manuelle Refreshes

Um einen Re-Run eines spezifischen Modells zu erzwingen, ohne die gesamte Historie zu löschen:

1. **Lösche relevante Zeilen** aus der CSV manuell

   ```bash
   # Alle Zeilen mit "qwen2.5:14b" entfernen
   grep -v "qwen2.5:14b" local_models_benchmark.csv > temp.csv
   mv temp.csv local_models_benchmark.csv
   ```

1. **Run Benchmark:**

   ```bash
   make benchmark-auto
   ```

1. **System-Reaktion:**

   - Sieht fehlenden Eintrag
   - Führt Test neu aus
   - Fügt neues Ergebnis zur CSV hinzu

1. **Nächstes Backup:**

   - Konsolidiert dies
   - Entfernt ggf. ältere Einträge (falls vorher gesichert)

______________________________________________________________________

## 4. Technische Implementation

Die Strategie wird über das Makefile durchgesetzt:

```makefile
backup:
    # 1. Archive erstellen
    @echo "📦 Creating snapshot..."
    @tar -czf backups/cruciblemark_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
        benchmark_scores/ \
        outputs/runs/ \
        golden_standards/ \
        benchmark_config.yaml

    # 2. Cleanup Logs
    @echo "🧹 Cleaning old run logs..."
    @python scripts/cleanup_runs.py --keep 5 --force

    # 3. Consolidate Scores
    @echo "📊 Consolidating CSV..."
    @python scripts/consolidate_csv.py

    @echo "✅ Backup complete!"
```

______________________________________________________________________

### Skript-Details

#### `cleanup_runs.py`

**Parameter:**

- `--keep N`: Anzahl der zu behaltenden Runs (default: 5)
- `--force`: Keine Bestätigung erforderlich

**Logik:**

```python
for model_dir in Path('outputs/runs').iterdir():
    json_files = sorted(model_dir.glob('*.json'), key=lambda f: f.stat().st_mtime)

    if len(json_files) > keep_count:
        to_delete = json_files[:-keep_count]  # Alle außer letzte N
        for file in to_delete:
            file.unlink()
```

______________________________________________________________________

#### `consolidate_csv.py`

**Logik:**

```python
import pandas as pd

df = pd.read_csv('benchmark_scores/local_models_benchmark.csv')

# Sortiere nach Timestamp (neueste zuerst)
df_sorted = df.sort_values('timestamp', ascending=False)

# Behalte nur neueste Zeile pro (Model, Asset)
df_latest = df_sorted.drop_duplicates(
    subset=['model', 'asset_id'],
    keep='first'
)

# Überschreibe Original
df_latest.to_csv('benchmark_scores/local_models_benchmark.csv', index=False)
```

______________________________________________________________________

## 5. Best Practices

### Wann Backup ausführen?

✅ **Empfohlen:**

- Vor großen Batch-Runs (viele Modelle auf einmal)
- Nach Hinzufügen neuer Module
- Vor Config-Änderungen (neue Scoring-Logik)
- Monatlich (als Routine)

❌ **Nicht nötig:**

- Nach jedem einzelnen Benchmark
- Bei kleinen Test-Runs (1-2 Modelle)

______________________________________________________________________

### Backup-Rotation

**Problem:** `backups/` Ordner wächst unbegrenzt.

**Lösung:** Manuelle Rotation (empfohlen: 3-Monats-Regel)

```bash
# Alte Backups (> 90 Tage) löschen
find backups/ -name "*.tar.gz" -mtime +90 -delete
```

**Automation (Optional):**

```bash
# In crontab eintragen (monatliches Backup)
0 0 1 * * cd /path/to/cruciblemark && make backup
```

______________________________________________________________________

## 6. Recovery-Szenarios

### Szenario 1: CSV korrupt

**Problem:** CSV-Datei beschädigt (z.B. durch Skript-Crash)

**Lösung:**

```bash
# Neuestes Backup extrahieren
tar -xzf backups/cruciblemark_backup_YYYYMMDD.tar.gz

# Nur CSV wiederherstellen (Rest beibehalten)
cp benchmark_scores/local_models_benchmark.csv benchmark_scores/
```

______________________________________________________________________

### Szenario 2: Falsches Scoring-Ergebnis

**Problem:** Bug in Evaluator führte zu falschen Scores

**Lösung:**

1. Backup erstellen (aktuellen Zustand sichern)
1. Evaluator fixen
1. Betroffene Zeilen aus CSV löschen
1. `make benchmark-auto` (Re-Run nur betroffener Tests)

______________________________________________________________________

### Szenario 3: Vollständiger Datenverlust

**Problem:** Festplatten-Crash, alle lokalen Daten weg

**Lösung:**

```bash
# Neuestes Backup extrahieren
tar -xzf backups/cruciblemark_backup_YYYYMMDD.tar.gz

# Alles wiederherstellen
cp -r benchmark_scores/ benchmark_scores_restored/
cp -r outputs/runs/ outputs/runs_restored/

# Framework neu installieren
make install

# Weiter wie gewohnt
make leaderboard
```

______________________________________________________________________

## 7. Daten-Governance

### Was wird NICHT gesichert?

- **Temporary Session Files:** `outputs/temp/session_*.json` (nur für Crash-Recovery)
- **Debug Responses:** `benchmark_scores/debug_responses/` (optional, nur bei --debug Flag)
- **Python Cache:** `__pycache__/`, `.pyc` Files

**Grund:** Ephemeral Data, kann regeneriert werden.

______________________________________________________________________

### Langzeit-Archivierung

Für langfristige Aufbewahrung (> 1 Jahr):

**Empfehlung:** Externes Backup

```bash
# Cloud-Upload (Beispiel: AWS S3)
aws s3 cp backups/cruciblemark_backup_20260201.tar.gz \
    s3://my-bucket/cruciblemark-archives/

# Oder: Externe Festplatte
rsync -avz backups/ /mnt/external-drive/cruciblemark-backups/
```

______________________________________________________________________

## 🔗 Verwandte Dokumentation

- **USER_GUIDE.md** – Befehle für Daten-Management (`make clean-model`, etc.)
- **ARCHITECTURE.md** – Data Persistence Layer (Layer 4)

______________________________________________________________________

## 📜 Lizenz-Hinweis

Die Backup-Skripte und Strategie sind Teil von CrucibleMark und unterliegen der **Apache License 2.0**.

**Siehe:** `LICENSE` für Details.

______________________________________________________________________

**Dokumenten-Version:** 3.0.0 (Rewrite Mar 2026)\
**Kompatibel mit:** CrucibleMark v3.0.0+
