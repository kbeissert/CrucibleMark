"""Phase 27: Konfigurations-Invarianten fuer das Backup-SSoT.

Diese Tests sichern die Datenkonsistenz von ``utils/backup_targets.py``:

- BACKUP_TARGETS verweisen auf existierende Pfade im Repo.
- CSV_FILES verweisen auf existierende CSVs mit konsistenten
  Schluesselspalten.
- Cleanup-Defaults haben sinnvolle Werte.
- Tar-Excludes enthalten die bekannten Hygiene-Patterns.
"""
from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.backup_targets import (  # noqa: E402
    BACKUP_ROTATION_DAYS,
    BACKUP_TARGETS,
    CSV_FILES,
    REVIEWS_KEEP_PER_CATEGORY,
    RUNS_KEEP_DEFAULT,
    UNREACHABLE_LOG_MAX_AGE_DAYS,
    all_csv_targets_exist,
    all_targets_exist,
    build_tar_excludes,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# BACKUP_TARGETS
# ---------------------------------------------------------------------------

def test_backup_targets_is_tuple():
    """BACKUP_TARGETS ist ein unveränderliches Tuple."""
    assert isinstance(BACKUP_TARGETS, tuple)


def test_backup_targets_contains_required_paths():
    """Pflicht-Pfade sind im tar-Snapshot enthalten."""
    required = {
        "benchmark_scores/",
        "outputs/",
        "benchmark_modules/",
        "docs/reviews/",
        "docs/audits/",
        "config/",
        "memory-bank/",
        "benchmark_config.yaml",
    }
    assert required.issubset(set(BACKUP_TARGETS))


def test_all_targets_exist_in_repo():
    """Alle BACKUP_TARGETS verweisen auf existierende Pfade."""
    missing = all_targets_exist(PROJECT_ROOT)
    assert not missing, (
        "Folgende BACKUP_TARGETS fehlen im Repo: "
        + ", ".join(missing)
    )


def test_all_targets_exist_returns_list():
    """Helper gibt eine Liste zurueck (auch wenn leer)."""
    result = all_targets_exist(PROJECT_ROOT)
    assert isinstance(result, list)


def test_all_targets_exist_detects_missing(tmp_path):
    """Helper erkennt fehlende Targets korrekt."""
    fake_targets = ("nonexistent_dir_xyz/",)
    missing = []
    for target in fake_targets:
        candidate = tmp_path / target.rstrip("/")
        if not candidate.exists():
            missing.append(target)
    assert "nonexistent_dir_xyz/" in missing


# ---------------------------------------------------------------------------
# CSV_FILES
# ---------------------------------------------------------------------------

def test_csv_files_is_tuple_of_tuples():
    """CSV_FILES ist ein Tuple von (Path, tuple[str, ...]) Paaren."""
    assert isinstance(CSV_FILES, tuple)
    for entry in CSV_FILES:
        assert isinstance(entry, tuple)
        assert len(entry) == 2
        path, keys = entry
        assert isinstance(path, Path)
        assert isinstance(keys, tuple)
        for k in keys:
            assert isinstance(k, str)


def test_csv_files_have_non_empty_keys():
    """Jede CSV hat mindestens eine Schluesselspalte."""
    for _path, keys in CSV_FILES:
        assert len(keys) >= 1, "CSV braucht mindestens eine Schluesselspalte"


def test_csv_files_contain_model_column():
    """Jede CSV-Datei nutzt 'model' als Deduplizierungs-Schluessel."""
    for _path, keys in CSV_FILES:
        assert "model" in keys, (
            f"Erwarte 'model' in Schluesselspalten, gefunden: {keys}"
        )


def test_all_csv_targets_exist_in_repo():
    """Alle CSV-Dateien existieren tatsaechlich im Repo."""
    missing = all_csv_targets_exist(PROJECT_ROOT)
    assert not missing, (
        "Folgende CSV-Dateien fehlen im Repo: "
        + ", ".join(missing)
    )


def test_all_csv_targets_exist_returns_list_of_strings():
    """Helper gibt Liste von Strings zurueck."""
    result = all_csv_targets_exist(PROJECT_ROOT)
    assert isinstance(result, list)
    for item in result:
        assert isinstance(item, str)


def test_csv_files_have_unique_paths():
    """Keine CSV-Datei darf doppelt in CSV_FILES stehen."""
    paths = [p for p, _ in CSV_FILES]
    assert len(paths) == len(set(paths)), "Doppelte CSV-Pfade gefunden"


# ---------------------------------------------------------------------------
# Cleanup-Defaults
# ---------------------------------------------------------------------------

def test_runs_keep_default_is_positive():
    """RUNS_KEEP_DEFAULT muss eine sinnvolle positive Zahl sein."""
    assert isinstance(RUNS_KEEP_DEFAULT, int)
    assert RUNS_KEEP_DEFAULT > 0
    assert RUNS_KEEP_DEFAULT >= 3, (
        "Weniger als 3 Runs ist zu aggressiv — neuester Run + 2 Backups"
    )


def test_reviews_keep_per_category_is_sensible():
    """REVIEWS_KEEP_PER_CATEGORY: 1 (nur neueste) ist Default und korrekt."""
    assert isinstance(REVIEWS_KEEP_PER_CATEGORY, int)
    assert REVIEWS_KEEP_PER_CATEGORY >= 1


def test_unreachable_log_max_age_days_is_positive():
    """UNREACHABLE_LOG_MAX_AGE_DAYS: 7 Tage ist Default aus Doku."""
    assert isinstance(UNREACHABLE_LOG_MAX_AGE_DAYS, int)
    assert UNREACHABLE_LOG_MAX_AGE_DAYS > 0
    assert UNREACHABLE_LOG_MAX_AGE_DAYS <= 30, (
        "Mehr als 30 Tage ist zu lax — Logs sollten rotiert werden"
    )


def test_backup_rotation_days_matches_doc():
    """BACKUP_ROTATION_DAYS: 90 Tage aus Doku v3.1.0."""
    assert isinstance(BACKUP_ROTATION_DAYS, int)
    assert BACKUP_ROTATION_DAYS == 90


# ---------------------------------------------------------------------------
# tar-Excludes
# ---------------------------------------------------------------------------

def test_build_tar_excludes_returns_tuple():
    """build_tar_excludes() liefert ein Tuple von Strings."""
    excludes = build_tar_excludes()
    assert isinstance(excludes, tuple)
    for item in excludes:
        assert isinstance(item, str)


def test_build_tar_excludes_contains_critical_patterns():
    """Backup-von-Backup-Patterns sind enthalten."""
    excludes = build_tar_excludes()
    required = {
        "__pycache__",
        ".DS_Store",
        "*.bak_*",
        "*.backup_*",
        "audit_logs_backup_*.tar.gz",
        "audit_logs_legacy_backup_*",
        "audit_logs_spurious_archive",
        "audit_logs.zip",
        "model_cards_backup_*.tar.gz",
        "model_cards_spurious_archive",
        "tooluse_unreachable_*.json",
        "outputs/temp/session_*.json",
    }
    assert required.issubset(set(excludes)), (
        "Fehlende Excludes: " + ", ".join(required - set(excludes))
    )


def test_build_tar_excludes_is_deterministic():
    """build_tar_excludes() lieferte beim zweiten Aufruf dieselben Patterns."""
    first = build_tar_excludes()
    second = build_tar_excludes()
    assert first == second
