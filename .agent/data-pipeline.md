# Data Pipeline

Regeln und Pitfalls für CSV-IO, Ergebnis-Persistenz, Konsolidierung.

## CSV-Semantik (idempotente Schichten)

- **`save_results()`** ist **Upsert** — gleiche `(model, asset_id)` wird ersetzt.
- **`data_loader.py`** dedupliziert via `drop_duplicates(keep="last")` nach Timestamp.
- **`consolidate_csv.py`** reduziert physisch auf 1 Zeile pro Key.
- Alle drei Schichten sind idempotent.

## CSV Write-Through (ab v4.10.2)

`_handle_single_asset()` in `unified_runner.py` schreibt jedes Ergebnis **SOFORT** per `save_results([result])` in die CSV.

- Vorher: Batch-Write erst am Ende des Runs — bei Crash/Kill/Timeout waren ALLE Ergebnisse des Runs verloren.
- Caller (`benchmark_auto.py:498`, `run_score_benchmark.py:180`) behält finalen `save_results(results)` als Safety-Netz (Upsert ist idempotent).

## CSV-Write-Through atomar (v4.10.4)

`_write_to_csv()` nutzt `tempfile.mkstemp()` + `os.replace()` — Originaldatei bleibt intakt bei Kill/Crash.

- NIEMALS `"w"` (truncate) zum Überschreiben verwenden.
- Bestehende Zeilen werden beim Full-Rewrite NICHT re-validiert — nur neue Zeilen gehen durch Hard-Fail-Guard.
- Recovery-Sequenz: `make backup` → tar (Snapshot) → `consolidate-csv` (Dedup latest-per-key) → bereinigte Live-CSV.

## CSV-Korruption & Audit-Trennung

- Audit-Logs niemals direkt in CSV schreiben — immer separate Dateien.
- Bei Korruption: `load_csv_robust()` mit `on_bad_lines="skip"`.

## CSV-Spalten-Erweiterung

Neue dynamische Spalten in `result_manager.py` → `_get_updated_fieldnames` eintragen. Sonst stillschweigend ignoriert.

## Asset Schema

Jede YAML-Aufgabe braucht zwingend `prompt`/`prompts`-Feld.

## Judge Parser

Bei Parse-Fehler `parse_success=False` (niemals Exception schlucken).

## Political-Compass Runtime

- **PC Skip-Logic Gap:** `execute_batch_module()` prüft nur 3 Standard-CSVs — nach Leaderboard-Reset explizit `political_compass_leaderboard.csv` als Fallback prüfen.
- **Modellnamen-Normalisierung:** `save_leaderboard_csv()` in `io_manager.py` schneidet Datumssuffixe (`-YYYYMMDD` und `-MMDD` OpenRouter-Stil) automatisch ab — Modellnamen in der PC-Leaderboard-CSV sind immer suffix-frei.
