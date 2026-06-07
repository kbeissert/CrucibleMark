# CrucibleMark v4.4.0 — CSV Robustness & Leaderboard Pipeline Hardening

## Zusammenfassung
Dieses Release härtet die Datenpipeline gegen CSV-Korruption und verbessert die Leaderboard-Generierung mit robuster ID-Resolution. Das Backup-System nutzt jetzt `load_csv_robust()` mit automatischer Fehlerbehebung.

---

## 🚀 Neue Features

### CSV Robustness
- **`load_csv_robust()`** mit `on_bad_lines="skip"` implementiert
- Korrupte CSV-Zeilen (z.B. durch Audit-Log-Injection) werden automatisch übersprungen
- Strategie: Robust Loader → Standard pandas → Fehlerlogging

### Leaderboard ID Resolution
- **`_resolve_to_canonical_id()`** in `consolidate_csv.py`
- Mapping von Display-Namen zu kanonischen Model-IDs
- Verhindert Duplikate bei abweichenden Namensschreibweisen

### Backup Strategy Hardening
- 2-Stufen-Fallback: utils-Recovery → Standard pandas
- Zeitzone-Fix (`utc=True`) für konsistente Timestamp-Handling
- Backup-Archive jetzt stabil und wiederherstellbar

---

## 🐛 Behobene Probleme

| Problem | Lösung |
|---------|--------|
| CSV-Korruption durch Audit-Log-Injection | `on_bad_lines="skip"` macht Parser resilient |
| Zeitzone-Warnungen bei Backup | `utc=True` in allen pd.to_datetime() Calls |
| Fehlende Modelle im Leaderboard | ID-Resolution für konsistente Einträge |

---

## 📊 Statistiken

- **65 Dateien geändert**
- **55.893 Zeilen hinzugefügt**
- **CSV-Korruption bereinigt:** 79.444 → 14.222 Zeilen
- **Verifiziert:** `qwen3.6-35b-a3b-q8` korrekt im Leaderboard (Rank 32, Score 73.39, 43/43 Tests)

---

## 🔧 Technische Details

### Neue/Geänderte Dateien
- `utils/csv_recovery.py` — Robuster CSV-Loader
- `scripts/maintenance/consolidate_csv.py` — ID Resolution & Fallback-Strategien
- `docs/BACKUP_STRATEGY.md` — Dokumentation der Recovery-Strategie
- `memory-bank/progress.md` & `techContext.md` — v4.4.0 Meilenstein

### Code-Qualität
- Pylint 10.00/10
- Ruff clean
- 227/227 Tests grün

---

**Vollständiger Changelog:** Siehe [CHANGELOG.md](CHANGELOG.md) und [PROJECT_STATUS.md](PROJECT_STATUS.md)

**Commits seit v4.3.2:**
- `ecdd4e8` — chore(release): bump version to 4.4.0
- `4686ebf` — chore(gitignore): add patterns for temp files
