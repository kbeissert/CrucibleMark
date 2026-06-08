"""SSoT: Backup-Targets, Excludes und Cleanup-Defaults.

Seit Phase 27 (Backup-System SSoT-Refactor) ist dies die einzige Quelle der
Wahrheit fuer:

- Welche Verzeichnisse / Dateien das `make backup`-tar einschliesst.
- Welche Pfade vom tar ausgeschlossen werden (Cache, Backups-von-Backups,
  Spurious-Archive, alte Crash-Logs).
- Welche CSVs die CSV-Konsolidierung verarbeitet und mit welchem
  Deduplizierungs-Schluessel.
- Welche Pfade vor dem Backup aufgeraeumt werden (backup_prep).

Vorher waren diese Listen ueber vier Skripte verstreut
(``scripts/maintenance/cleanup_runs.py``,
``scripts/maintenance/consolidate_csv.py``,
``scripts/maintenance/cleanup_reviews.py``,
``scripts/maintenance/prune_orphaned_reports.py``) und das
``Makefile::backup``-Recipe dupliziert.

Diese Konstanten sind bewusst reine Daten — keine Funktionen, keine
Imports aus Skripten — damit sie zirkelfrei in SSoT-Tests importiert
werden koennen.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# tar-Snapshot: was wird gesichert?
# ---------------------------------------------------------------------------

#: Verzeichnisse und Top-Level-Dateien, die im tar-Snapshot landen.
#: Reihenfolge ist signifikant fuer lesbare Listings, nicht fuer tar selbst.
BACKUP_TARGETS: tuple[str, ...] = (
    "benchmark_scores/",
    "outputs/",
    "benchmark_modules/",
    "docs/reviews/",
    "docs/audits/",
    "config/",
    "memory-bank/",
    "benchmark_config.yaml",
)


def build_tar_excludes() -> tuple[str, ...]:
    """Zentrale tar-Excludes.

    Wird sowohl vom ``make backup``-Recipe als auch von
    :func:`scripts.maintenance.cleanup_helpers.pre_backup_hygiene` genutzt,
    damit Archiv und Quell-Repo beim Cleanup identisch handeln.

    Returns:
        Tuple von tar-Globs. Reihenfolge ist irrelevant (tar akkumuliert).
    """
    return (
        "__pycache__",
        ".DS_Store",
        # .bak_* und .backup_* werden vom clean-bak-Target entsorgt
        "*.bak_*",
        "*.backup_*",
        # Backups-von-Backups (wuerden das Archiv aufblasen)
        "audit_logs_backup_*.tar.gz",
        "audit_logs_legacy_backup_*",
        "audit_logs_spurious_archive",
        "audit_logs.zip",
        "model_cards_backup_*.tar.gz",
        "model_cards_spurious_archive",
        "tooluse_unreachable_*.json",
        # temporaere Session-Files (PC-Wizard)
        "outputs/temp/session_*.json",
    )


# ---------------------------------------------------------------------------
# CSV-Konsolidierung
# ---------------------------------------------------------------------------

#: CSV-Dateien + Deduplizierungs-Schluessel. Wird von
#: ``scripts/maintenance/consolidate_csv.py`` und von der
#: Konfigurations-Invariante in ``tests/test_backup_targets.py`` genutzt.
CSV_FILES: tuple[tuple[Path, tuple[str, ...]], ...] = (
    (Path("benchmark_scores/local_models_benchmark.csv"), ("model", "asset_id")),
    (Path("benchmark_scores/cloud_models_benchmark.csv"), ("model", "asset_id")),
    (Path("benchmark_scores/commercial_models_benchmark.csv"), ("model", "asset_id")),
    (Path("benchmark_scores/tooluse_leaderboard.csv"), ("model",)),
)


# ---------------------------------------------------------------------------
# Cleanup-Defaults
# ---------------------------------------------------------------------------

#: Anzahl Benchmark-Runs, die pro Modell behalten werden. Aus Doku
#: ``docs/BACKUP_STRATEGY.md`` v3.1.0 uebernommen.
#: Wird vom ``make backup``-Recipe ueber ``--runs $(RUNS_KEEP)`` genutzt.
RUNS_KEEP_DEFAULT: int = 5

#: Anzahl Reviews pro Modell und Kategorie (Benchmark, Bias, Tool-Use),
#: die behalten werden. Standard: 1 (nur das neueste).
REVIEWS_KEEP_PER_CATEGORY: int = 1

#: Schwellwert in Tagen, ab dem ``outputs/tooluse_unreachable_*.json`` als
#: veraltet gilt und vor dem Backup aufgeraeumt wird.
UNREACHABLE_LOG_MAX_AGE_DAYS: int = 7

#: Schwellwert in Tagen, ab dem ``backups/*.tar.gz``-Snapshots in der
#: Empfehlung zur Rotation erwaehnt werden (aus Doku v3.1.0 uebernommen).
BACKUP_ROTATION_DAYS: int = 90


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def all_targets_exist(root: Path) -> list[str]:
    """Prueft, ob alle :data:`BACKUP_TARGETS` im Repo existieren.

    Wird vom Konfigurations-Test genutzt, um Drift frueh zu erkennen
    (z.B. wenn ein Verzeichnis umbenannt wurde).

    Args:
        root: Projekt-Wurzelverzeichnis.

    Returns:
        Liste der Targets, die NICHT existieren (leer = alles ok).
    """
    missing: list[str] = []
    for target in BACKUP_TARGETS:
        candidate = root / target.rstrip("/")
        if not candidate.exists():
            missing.append(target)
    return missing


def all_csv_targets_exist(root: Path) -> list[str]:
    """Prueft, ob alle :data:`CSV_FILES` im Repo existieren.

    Liefert fuer die Konfig-Invariante in ``tests/test_backup_targets.py``.

    Args:
        root: Projekt-Wurzelverzeichnis.

    Returns:
        Liste der relativen Pfade, die NICHT existieren.
    """
    missing: list[str] = []
    for path, _ in CSV_FILES:
        candidate = root / path
        if not candidate.exists():
            missing.append(str(path))
    return missing
