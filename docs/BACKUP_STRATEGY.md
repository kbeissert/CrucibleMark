# CrucibleMark: Daten-Retention & Backup-Strategie

**Zielgruppe:** Alle, die verstehen wollen, wie CrucibleMark mit Daten umgeht.

**Inhalt:**

- Philosophie: „Live vs. History"
- Backup-Lifecycle (Snapshot → Prune → Consolidate)
- Workflow-Implikationen
- Technische Implementierung

---

## 1. Philosophie & Zweck

CrucibleMark ist ein Werkzeug zum Vergleich von Modellen (Leaderboard) – kein Monitoring-Tool für Modell-Veränderungen über die Zeit.

Das **Live-System** (`benchmark_scores/*.csv`) braucht keine Historie. Es braucht den **aktuellsten, validen Zustand** eines jeden Modells.

---

### Warum diese Unterscheidung wichtig ist

**Static Weights:**

- Lokale Modelle (z. B. `llama3:8b-q4_K_M`) sind statische Dateien.
- Ihre Performance ändert sich nicht über die Zeit.

**Locked APIs:**

- Kommerzielle Modelle sind an spezifische Versionen gepinnt (z. B. `gpt-4-0613`).
- Das gewährleistet Reproduzierbarkeit.

Redundante historische Daten im aktiven Workspace blähen das System auf. Für den primären Use Case (Modell A vs. Modell B vergleichen) bieten sie keinen Mehrwert.

---

## 2. Der Backup-Lifecycle

Um Datensicherheit mit Workspace-Hygiene zu verbinden, implementiert CrucibleMark einen **„Snapshot & Prune"-Workflow**.

```bash
make backup
```

---

### Phase 1: The Archive (unveränderliche Historie)

**Aktion:** Erstelle einen `.tar.gz`-Snapshot des gesamten Workspace.

**Pfad:** `backups/cruciblemark_backup_YYYYMMDD_HHMMSS.tar.gz`

**Inhalt:**

- Alle CSV-Scores
- Vollständige JSON-Run-Logs
- Modul-Konfigurationen
- Golden Standards

**Regel:** Dies ist das **System of Record**. Historische Analysen (z. B. „Wie performte GPT-4 vor einem Jahr?") kommen aus diesen Archiven.

---

### Phase 2: JSON-Cleanup (Hygiene)

**Aktion:** `scripts/cleanup_runs.py` ausführen.

**Ziel:** `outputs/runs/**/*.json`

**Regel:** Nur die **letzten fünf Runs** pro Modell behalten.

JSON-Logs enthalten vollständige Rohdaten (Prompts, Responses, Timestamps) und sind sehr detailliert (mehrere MB pro Run). Ältere Logs liegen sicher im Archive aus Phase 1.

---

### Phase 3: CSV-Konsolidierung (The „Latest Only" Rule)

**Aktion:** `scripts/consolidate_csv.py` ausführen.

**Ziel:** `benchmark_scores/*.csv`

**Logik:**

1. Kumulative CSV-Datei laden
2. Nach Timestamp sortieren (neueste zuerst)
3. Nach eindeutigem Key gruppieren: `(Model Name, Asset ID)`
4. **Deduplizieren:** Nur den einzelnen neuesten Eintrag behalten
5. Alle älteren Duplikate entfernen

**Ergebnis:** Die CSV-Datei enthält exakt **einen validen Score** pro Test-Case.

---

## 3. Workflow-Implikationen

### Continuous Benchmarking („Rolling Updates")

Weil CSV-Dateien auf den neuesten Stand konsolidiert werden:

1. **Optimierung:** Bei `make benchmark-auto` nach einem Backup erkennt das System, dass die neuesten Testergebnisse bereits in der CSV vorliegen.
2. **Effizienz:** Es überspringt alle erfolgreich getesteten Assets.
3. **Updates:** Es führt nur Tests für neue Modelle oder neue Assets aus.

Das spart API-Kosten und Zeit.

---

### Manuelle Refreshes

Um einen Re-Run eines spezifischen Modells zu erzwingen, ohne die gesamte Historie zu löschen:

1. **Relevante Zeilen aus der CSV löschen:**

   ```bash
   # Alle Zeilen mit "qwen2.5:14b" entfernen (Beispiel für ein lokales Modell)
   grep -v "qwen2.5:14b" benchmark_scores/local_models_benchmark.csv > temp.csv
   mv temp.csv benchmark_scores/local_models_benchmark.csv
   ```

2. **Benchmark starten:**

   ```bash
   make benchmark-auto
   ```

3. **System-Reaktion:**

   - Erkennt fehlenden Eintrag
   - Führt Test neu aus
   - Fügt neues Ergebnis zur CSV hinzu

4. **Nächstes Backup:**

   - Konsolidiert das Ergebnis
   - Entfernt ggf. ältere Einträge

---

## 4. Technische Implementierung

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

---

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

---

#### `cleanup_reviews.py`

Bereinigt `docs/reviews/` und behält pro Modell-Verzeichnis je einen Benchmark-Review, einen Bias-Review und einen Tool-Use-Review. Ältere Duplikate werden entfernt (Dry-Run via `make clean-reviews`, Löschen mit `FORCE=1`).

| Dateiname-Pattern | Kategorie |
|---|---|
| `review_YYYYMMDD_HHMMSS.md` | Benchmark-Review |
| `bias_review_YYYYMMDD_HHMMSS.md` | PC-Bias-Review |
| `tooluse_narrative_review_YYYYMMDD_HHMMSS.md` | Tool-Use-Review |

#### `consolidate_csv.py`

Verarbeitet alle Benchmark- und Leaderboard-CSVs mit robustem CSV-Parsing (ab v4.4.0).

**Robuster CSV-Loader (Fallback-Strategien):**
1. **Strategie 1:** `utils.csv_recovery.load_csv_robust()` — nutzt `on_bad_lines="skip"`
2. **Strategie 2:** `pd.read_csv(on_bad_lines="skip", engine="python")` — Fallback
3. **Timezone-Fix:** `utc=True` für Mixed-Timezone-Probleme bei Timestamps

**Deduplizierungs-Logik:**

| Datei | Deduplizierungs-Schlüssel |
|---|---|
| `*_models_benchmark.csv` (3×) | `model` + `asset_id` |
| `tooluse_leaderboard.csv` | `model` |

```python
# Benchmark-CSVs: neueste Zeile pro (Modell, Asset) behalten
df_sorted = df.sort_values('timestamp', ascending=False)
df_latest = df_sorted.drop_duplicates(subset=['model', 'asset_id'], keep='first')

# tooluse_leaderboard.csv: neueste Zeile pro Modell behalten
df_latest = df_sorted.drop_duplicates(subset=['model'], keep='first')
```

**Hinweis:** Das Skript toleriert jetzt korrupte CSV-Dateien (z.B. durch eingemischte Audit-Logs) und lädt trotzdem alle validen Zeilen.

---

## 5. Best Practices

### Wann Backup ausführen?

✅ **Empfohlen:**

- Vor großen Batch-Runs (viele Modelle auf einmal)
- Nach dem Hinzufügen neuer Module
- Vor Config-Änderungen (neue Scoring-Logik)
- Monatlich als Routine

❌ **Nicht nötig:**

- Nach jedem einzelnen Benchmark
- Bei kleinen Test-Runs (ein bis zwei Modelle)

---

### Backup-Rotation

Das `backups/`-Verzeichnis wächst andernfalls unbegrenzt. Empfehlung: manuelle Rotation nach der 3-Monats-Regel.

```bash
# Alte Backups (> 90 Tage) löschen
find backups/ -name "*.tar.gz" -mtime +90 -delete
```

**Automation (optional):**

```bash
# In crontab eintragen (monatliches Backup)
0 0 1 * * cd /path/to/cruciblemark && make backup
```

---

## 6. Recovery-Szenarien

### Szenario 1: CSV korrupt

**Problem:** CSV-Datei beschädigt (z. B. durch Skript-Crash).

```bash
# Neuestes Backup extrahieren
tar -xzf backups/cruciblemark_backup_YYYYMMDD.tar.gz

# Nur eine spezifische CSV wiederherstellen
cp backups/backup_20240315_143022/local_models_benchmark.csv benchmark_scores/
```

---

### Szenario 2: Falsches Scoring-Ergebnis

**Problem:** Bug im Evaluator führte zu falschen Scores.

1. Backup erstellen (aktuellen Zustand sichern)
2. Evaluator fixen
3. Betroffene Zeilen aus CSV löschen
4. `make benchmark-auto` ausführen (Re-Run nur betroffener Tests)

---

### Szenario 3: Vollständiger Datenverlust

**Problem:** Festplatten-Crash, alle lokalen Daten weg.

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

---

## 7. Daten-Governance

### Was wird NICHT gesichert?

- **Temporary Session Files:** `outputs/temp/session_*.json` (nur für Crash-Recovery)
- **Python Cache:** `__pycache__/`, `.pyc`-Dateien

Diese Daten sind ephemeral und lassen sich regenerieren.

---

### Langzeit-Archivierung

Für langfristige Aufbewahrung (> 1 Jahr):

```bash
# Cloud-Upload (Beispiel: AWS S3)
aws s3 cp backups/cruciblemark_backup_20260201.tar.gz \
    s3://my-bucket/cruciblemark-archives/

# Oder: Externe Festplatte
rsync -avz backups/ /mnt/external-drive/cruciblemark-backups/
```

---

## Verwandte Dokumentation

- **USER_GUIDE.md** – Befehle für Daten-Management (`make clean-model`, u. a.)
- **ARCHITECTURE.md** – Data Persistence Layer (Layer 4)

---

**Dokumenten-Version:** 3.1.0 (Überarbeitung März 2026)\
**Kompatibel mit:** CrucibleMark v3.4.3+
