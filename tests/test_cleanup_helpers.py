"""Phase 27: Tests fuer ``scripts/maintenance/cleanup_helpers.py``.

Sichert die ID-SSoT-Bruecke:

- ``canonical_model_slug()`` normalisiert Slugs via SSoT.
- ``canonicalize_run_grouping()`` gruppiert Run-Files nach kanonischer ID.
- ``pre_backup_hygiene()`` raeumt vor dem tar-Snapshot auf.
- ``run_pre_backup_hygiene()`` ist der Convenience-Wrapper.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.maintenance import cleanup_helpers  # noqa: E402


# ---------------------------------------------------------------------------
# canonical_model_slug
# ---------------------------------------------------------------------------

def test_canonical_model_slug_handles_empty():
    """Leere Eingabe wird leer zurueckgegeben."""
    assert cleanup_helpers.canonical_model_slug("") == ""


def test_canonical_model_slug_handles_none_like():
    """None-aehnliche Eingaben crashen nicht."""
    # _safe_name ersetzt Whitespace durch _ → zwei Spaces werden zu zwei Underscores
    assert cleanup_helpers.canonical_model_slug("  ") == "__"
    # Auch mehrfacher Whitespace wird ersetzt
    assert cleanup_helpers.canonical_model_slug(" ") == "_"


def test_canonical_model_slug_falls_back_to_safe_name():
    """Unbekanntes Modell faellt auf _safe_name zurueck."""
    raw = "unbekanntes-test-modell-xyz"
    result = cleanup_helpers.canonical_model_slug(raw)
    # _safe_name macht daraus "unbekanntes-test-modell-xyz" (keine Sonderzeichen)
    assert result == raw


def test_canonical_model_slug_handles_special_chars():
    """Sonderzeichen werden in _safe_name-Form ueberfuehrt."""
    # Wir muessen einen Fallback-Pfad nehmen, da die SSoT-Funktion
    # auf eine Card zurueckgreift die hier nicht existiert.
    # _safe_name("foo/bar") = "foo_bar"
    raw = "foo/bar:baz"
    result = cleanup_helpers.canonical_model_slug(raw)
    # safe_name -> "foo_bar_baz" (entweder via Card oder Fallback)
    assert "foo" in result and "bar" in result and "baz" in result
    assert "/" not in result
    assert ":" not in result


# ---------------------------------------------------------------------------
# canonicalize_run_grouping
# ---------------------------------------------------------------------------

def test_canonicalize_run_grouping_empty_list():
    """Leere Inputliste ergibt leeres Dict."""
    assert cleanup_helpers.canonicalize_run_grouping([]) == {}


def test_canonicalize_run_grouping_skips_non_matching(tmp_path):
    """Dateien ohne RUN_FILE_RE-Pattern werden ignoriert."""
    (tmp_path / "random.json").write_text("{}")
    (tmp_path / "results_foo_20260101_120000.json").write_text("{}")
    result = cleanup_helpers.canonicalize_run_grouping(
        [tmp_path / "random.json", tmp_path / "results_foo_20260101_120000.json"]
    )
    assert len(result) == 1


def test_canonicalize_run_grouping_groups_by_slug(tmp_path):
    """Mehrere Runs fuer ein Modell werden zusammengefasst."""
    files = []
    for i in range(3):
        f = tmp_path / f"results_foo_{i:08d}_120000.json"
        f.write_text("{}")
        files.append(f)
    result = cleanup_helpers.canonicalize_run_grouping(files)
    assert len(result) == 1
    # Innerhalb der Gruppe sind 3 Dateien
    canon = list(result.keys())[0]
    assert len(result[canon]) == 3


def test_canonicalize_run_grouping_separates_models(tmp_path):
    """Verschiedene Modelle bekommen verschiedene Gruppen."""
    f1 = tmp_path / "results_modelA_20260101_120000.json"
    f1.write_text("{}")
    f2 = tmp_path / "results_modelB_20260101_120000.json"
    f2.write_text("{}")
    result = cleanup_helpers.canonicalize_run_grouping([f1, f2])
    assert len(result) == 2


def test_canonicalize_run_grouping_sorts_newest_first(tmp_path):
    """Innerhalb jeder Gruppe ist die Reihenfolge mtime-absteigend."""
    f_old = tmp_path / "results_foo_20260101_120000.json"
    f_old.write_text("{}")
    # mtime explizit setzen (aelter)
    old_time = (datetime.now(tz=timezone.utc) - timedelta(days=2)).timestamp()
    os.utime(f_old, (old_time, old_time))

    f_new = tmp_path / "results_foo_20260103_120000.json"
    f_new.write_text("{}")
    new_time = (datetime.now(tz=timezone.utc) - timedelta(hours=1)).timestamp()
    os.utime(f_new, (new_time, new_time))

    result = cleanup_helpers.canonicalize_run_grouping([f_old, f_new])
    canon = list(result.keys())[0]
    assert result[canon][0] == f_new
    assert result[canon][1] == f_old


# ---------------------------------------------------------------------------
# pre_backup_hygiene
# ---------------------------------------------------------------------------

def test_pre_backup_hygiene_creates_safety_dir(tmp_path):
    """Safety-Archiv wird erzeugt (auch ohne zu loeschende Files)."""
    (tmp_path / "outputs").mkdir()
    stats = cleanup_helpers.pre_backup_hygiene(tmp_path, dry_run=False)
    # Es wird ein _pre_clean_* Unterordner in backups/ angelegt
    assert any(p.name.startswith("_pre_clean_") for p in (tmp_path / "backups").iterdir())
    assert stats["unreachable_logs_deleted"] == 0
    assert stats["legacy_backups_moved"] == 0
    assert stats["temp_files_deleted"] == 0


def test_pre_backup_hygiene_dry_run_does_not_modify(tmp_path):
    """Im dry_run-Modus wird nichts verschoben/geloescht."""
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    f = outputs / "tooluse_unreachable_20260101.json"
    f.write_text("{}")
    old_time = (datetime.now(tz=timezone.utc) - timedelta(days=10)).timestamp()
    os.utime(f, (old_time, old_time))

    stats = cleanup_helpers.pre_backup_hygiene(tmp_path, dry_run=True)
    assert stats["unreachable_logs_deleted"] == 1
    # Datei existiert noch
    assert f.exists()


def test_pre_backup_hygiene_deletes_old_unreachable_logs(tmp_path):
    """Alte tooluse_unreachable_*.json werden geloescht."""
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    f_old = outputs / "tooluse_unreachable_20260101.json"
    f_old.write_text("{}")
    old_time = (datetime.now(tz=timezone.utc) - timedelta(days=10)).timestamp()
    os.utime(f_old, (old_time, old_time))

    f_new = outputs / "tooluse_unreachable_20260601.json"
    f_new.write_text("{}")
    new_time = datetime.now(tz=timezone.utc).timestamp()
    os.utime(f_new, (new_time, new_time))

    stats = cleanup_helpers.pre_backup_hygiene(tmp_path, dry_run=False)
    assert stats["unreachable_logs_deleted"] == 1
    assert not f_old.exists()
    assert f_new.exists()


def test_pre_backup_hygiene_moves_legacy_backups(tmp_path):
    """Legacy-Backup-Patterns werden nach backups/_pre_clean_*/ verschoben."""
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    legacy = outputs / "audit_logs_legacy_backup_20260101.tar.gz"
    legacy.write_text("data")
    spurious = outputs / "audit_logs_spurious_archive"
    spurious.mkdir()
    (spurious / "old.txt").write_text("x")

    stats = cleanup_helpers.pre_backup_hygiene(tmp_path, dry_run=False)
    assert stats["legacy_backups_moved"] >= 1
    # Source ist weg
    assert not legacy.exists()
    assert not spurious.exists()
    # Safety-Archiv enthaelt die Files
    backups = tmp_path / "backups"
    safety_dirs = [p for p in backups.iterdir() if p.name.startswith("_pre_clean_")]
    assert len(safety_dirs) == 1
    moved_files = list(safety_dirs[0].iterdir())
    moved_names = {f.name for f in moved_files}
    assert "audit_logs_legacy_backup_20260101.tar.gz" in moved_names


def test_pre_backup_hygiene_deletes_temp_sessions(tmp_path):
    """outputs/temp/session_*.json werden aufgeraeumt."""
    outputs = tmp_path / "outputs"
    temp_dir = outputs / "temp"
    temp_dir.mkdir(parents=True)
    f = temp_dir / "session_abc123.json"
    f.write_text("{}")

    stats = cleanup_helpers.pre_backup_hygiene(tmp_path, dry_run=False)
    assert stats["temp_files_deleted"] >= 1
    assert not f.exists()


def test_pre_backup_hygiene_handles_missing_outputs(tmp_path):
    """Fehlende outputs/-Verzeichnis wird klaglos behandelt."""
    # Kein outputs/ anlegen
    stats = cleanup_helpers.pre_backup_hygiene(tmp_path, dry_run=False)
    # Kein Crash, alle Zaehler 0
    assert stats["unreachable_logs_deleted"] == 0
    assert stats["legacy_backups_moved"] == 0
    assert stats["temp_files_deleted"] == 0


def test_pre_backup_hygiene_returns_expected_keys(tmp_path):
    """Rueckgabe-Dict hat exakt die drei erwarteten Keys."""
    stats = cleanup_helpers.pre_backup_hygiene(tmp_path, dry_run=False)
    assert set(stats.keys()) == {
        "unreachable_logs_deleted",
        "legacy_backups_moved",
        "temp_files_deleted",
    }
    for v in stats.values():
        assert isinstance(v, int)
        assert v >= 0


def test_run_pre_backup_hygiene_is_convenience_wrapper(tmp_path, caplog):
    """run_pre_backup_hygiene() delegiert an pre_backup_hygiene()."""
    import logging
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    f = outputs / "tooluse_unreachable_20260101.json"
    f.write_text("{}")
    old_time = (datetime.now(tz=timezone.utc) - timedelta(days=10)).timestamp()
    os.utime(f, (old_time, old_time))

    with caplog.at_level(logging.INFO):
        stats = cleanup_helpers.run_pre_backup_hygiene(tmp_path, dry_run=False)
    assert stats["unreachable_logs_deleted"] == 1
    assert "Hygiene abgeschlossen" in caplog.text
    assert not f.exists()


# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

def test_run_file_re_matches_valid_filename():
    """RUN_FILE_RE matcht gueltige results-Dateinamen."""
    assert cleanup_helpers.RUN_FILE_RE.match("results_foo_20260101_120000.json")
    assert cleanup_helpers.RUN_FILE_RE.match("results_qwen3.5-35b_20260101_120000.json")


def test_run_file_re_rejects_invalid_filenames():
    """RUN_FILE_RE matcht NICHT ungueltige Namen."""
    assert not cleanup_helpers.RUN_FILE_RE.match("results_foo.json")
    assert not cleanup_helpers.RUN_FILE_RE.match("foo_20260101_120000.json")
    assert not cleanup_helpers.RUN_FILE_RE.match("results__20260101_120000.json")


def test_run_file_re_captures_model_and_timestamp():
    """Gruppen 1 (slug) und 2 (timestamp) sind korrekt extrahiert."""
    m = cleanup_helpers.RUN_FILE_RE.match("results_qwen3.5-35b_20260101_120000.json")
    assert m.group(1) == "qwen3.5-35b"
    assert m.group(2) == "20260101_120000"
