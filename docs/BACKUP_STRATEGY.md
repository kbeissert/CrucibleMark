# CrucibleMark: Daten-Retention & Backup-Strategie

**Zielgruppe:** Alle, die verstehen wollen, wie CrucibleMark mit Daten umgeht.

**Inhalt:**

- Philosophie: „Live vs. History"
- Backup-Lifecycle (Snapshot → Prune → Consolidate)
- SSoT-Architektur (Phase 27) — eine Quelle der Wahrheit
- Pre-Backup-Hygiene — automatisches Aufräumen vor dem Snapshot
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
make backup-prep    # Dry-Run / Pre-Backup-Hygiene (Phase 27)
make backup         # Snapshot + Cleanup + Consolidate
```

> **Neu in Phase 27:** `make backup-prep` führt die Pre-Backup-Hygiene als isolierten, optionalen Schritt aus — ideal für CI-Smoke-Tests oder wenn der tar-Snapshot separat erzeugt werden soll.

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
2. **Model-Spalte via ID-SSoT normalisieren** (Phase 27 — verhindert Split bei Schreibweisenvarianten)
3. Nach Timestamp sortieren (neueste zuerst)
4. Nach eindeutigem Key gruppieren: `(Model Name, Asset ID)`
5. **Deduplizieren:** Nur den einzelnen neuesten Eintrag behalten
6. Alle älteren Duplikate entfernen

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

### 4.1 SSoT-Architektur (Phase 27)

Seit Phase 27 ist **eine einzige Datei** die Quelle der Wahrheit für das Backup-System:

**`utils/backup_targets.py`** — Konfigurations-SSoT für:

- `BACKUP_TARGETS` — Verzeichnisse im tar-Snapshot
- `build_tar_excludes()` — zentrale tar-Excludes
- `CSV_FILES` — CSVs der Konsolidierung + Deduplizierungs-Schlüssel
- `RUNS_KEEP_DEFAULT` (5) — Cleanup-Default für alte Runs
- `REVIEWS_KEEP_PER_CATEGORY` (1) — Cleanup-Default für alte Reviews
- `UNREACHABLE_LOG_MAX_AGE_DAYS` (7) — Schwellwert für Crash-Log-Rotation
- `BACKUP_ROTATION_DAYS` (90) — Empfehlung für Snapshot-Rotation

> **Vorteil:** Ein Drift in Cleanup-Defaults, Excludes oder CSV-Listen ist jetzt an *einer* Stelle zu fixen — nicht mehr über vier Skripte verstreut.

### 4.2 Pre-Backup-Hygiene (Phase 27)

Neu in Phase 27: `scripts/maintenance/cleanup_helpers.py::pre_backup_hygiene()` räumt **vor** dem tar-Snapshot auf:

1. **Alte Crash-Logs löschen** — `outputs/tooluse_unreachable_*.json` älter als 7 Tage
2. **Legacy-Backups in Safety-Archiv verschieben** — `audit_logs_backup_*.tar.gz`, `audit_logs_legacy_backup_*`, `audit_logs_spurious_archive`, `audit_logs.zip`, `model_cards_backup_*.tar.gz`, `model_cards_spurious_archive` werden in `backups/_pre_clean_YYYYMMDD_HHMMSS/` verschoben
3. **Temporäre Session-Files löschen** — `outputs/temp/session_*.json`

Aufruf als isolierter Schritt (Dry-Run oder Default):

```bash
make backup-prep              # echter Lauf
DRY_RUN=1 make backup-prep    # nur anzeigen, nichts ändern
```

### 4.3 Makefile-Recipes

```makefile
# Phase 27: Pre-Backup-Hygiene (SSoT-Konstanten via env)
backup-prep:
	@python scripts/maintenance/cleanup_helpers.py $(if $(DRY_RUN),--dry-run,)

# backup haengt automatisch an backup-prep — keine doppelte Logik
backup: backup-prep
	@echo "Creating full backup..."
	@mkdir -p backups
	@tar --exclude='__pycache__' --exclude='.DS_Store' \
	     --exclude='*.bak_*' --exclude='*.backup_*' \
	     --exclude='audit_logs_backup_*.tar.gz' \
	     --exclude='audit_logs_legacy_backup_*' \
	     --exclude='audit_logs_spurious_archive' \
	     --exclude='audit_logs.zip' \
	     --exclude='model_cards_backup_*.tar.gz' \
	     --exclude='model_cards_spurious_archive' \
	     --exclude='tooluse_unreachable_*.json' \
	     --exclude='outputs/temp/session_*.json' \
	     -czf backups/cruciblemark_backup_$(DATE).tar.gz \
	     benchmark_scores/ outputs/ benchmark_modules/ \
	     docs/reviews/ docs/audits/ config/ memory-bank/ \
	     benchmark_config.yaml
	@echo "Backup created."

	# Alte Runs bereinigen (via make clean-runs → scripts/maintenance/clean.py)
	@$(MAKE) clean-runs FORCE=1 RUNS_KEEP=$(RUNS_KEEP)

	# CSVs deduplizieren (via make consolidate-csv)
	@$(MAKE) consolidate-csv

	# Aufräumen: .bak_*-Dateien, alte Reviews, verwaiste Report-Dirs
	@$(MAKE) clean-bak
	@$(MAKE) clean-reviews FORCE=1
	@$(MAKE) prune-orphans FORCE=1
```

> **Defaults:** `RUNS_KEEP ?= 5` im Makefile spiegelt `RUNS_KEEP_DEFAULT` aus `utils/backup_targets.py`.
>
> **Hinweis:** Die Exclude-Liste im tar-Befehl ist identisch mit `build_tar_excludes()` aus `utils/backup_targets.py` (SSoT). Bei neuen Excludes **beide** Stellen aktualisieren.

---

### Skript-Details

#### `cleanup_runs.py`

**Parameter:**

- `--keep N`: Anzahl der zu behaltenden Runs (default: `RUNS_KEEP_DEFAULT = 5` aus SSoT)
- `--force`: Keine Bestätigung erforderlich
- `--dry-run`: Nur anzeigen, nichts löschen

**Logik (Phase 27, ID-SSoT-bewusst):**

```python
# Gruppierung laeuft NICHT mehr ueber den Dateinamen-Slug,
# sondern via resolve_canonical_model_id() (utils.model_utils).
grouped = canonicalize_run_grouping(files)
# qwen3.5-35b-q4 und qwen_qwen3.5-35b-q4 landen in derselben Gruppe.

for model, files in grouped.items():
    if len(files) > keep:
        to_remove = files[keep:]  # neueste zuerst, Rest weg
        for f in to_remove:
            f.unlink()
```

---

#### `cleanup_reviews.py`

Bereinigt `docs/reviews/` und behält pro Modell-Verzeichnis je einen Benchmark-Review, einen Bias-Review und einen Tool-Use-Review. Ältere Duplikate werden entfernt (Dry-Run via `make clean-reviews`, Löschen mit `FORCE=1`).

| Dateiname-Pattern | Kategorie |
|---|---|
| `review_YYYYMMDD_HHMMSS.md` | Benchmark-Review |
| `bias_review_YYYYMMDD_HHMMSS.md` | PC-Bias-Review |
| `tooluse_narrative_review_YYYYMMDD_HHMMSS.md` | Tool-Use-Review |

> **Phase 27:** Verzeichnisnamen werden via `_safe_name` normalisiert, damit `qwen3.5-35b-a3b-q4` und `qwen_qwen3.5-35b-a3b-q4` als dasselbe Modell zählen.

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

> **Phase 27:** `model`-Spalte wird via `resolve_canonical_model_id()` normalisiert, **bevor** dedupliziert wird — `qwen3.5-35b` und `qwen_qwen3.5-35b` werden als dasselbe Modell gezählt.

**Hinweis:** Das Skript toleriert jetzt korrupte CSV-Dateien (z.B. durch eingemischte Audit-Logs) und lädt trotzdem alle validen Zeilen. Defense-in-Depth-Sanitizer (Phase 9) bleibt aktiv.

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
- **Backups-von-Backups:** `audit_logs_backup_*.tar.gz`, `audit_logs_legacy_backup_*`, `model_cards_backup_*.tar.gz` (Phase 27: werden in `backups/_pre_clean_*/` verschoben, nicht ins Archiv aufgenommen)
- **Spurious-Archive:** `audit_logs_spurious_archive/`, `model_cards_spurious_archive/` (Phase 27: gleiche Behandlung)
- **Alte Crash-Logs:** `outputs/tooluse_unreachable_*.json` älter als 7 Tage (Phase 27: werden vor dem tar gelöscht)

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
- **MAINTENANCE_LOG.md** – v4.6.6 Phase 27 Eintrag mit Code-Diffs

---

**Dokumenten-Version:** 3.2.0 (Phase 27, 2026-06-08)\
**Kompatibel mit:** CrucibleMark v4.4.3+
