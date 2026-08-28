"""Phase 27: Tests fuer ``scripts/maintenance/cleanup_runs.py``.

Sichert:
- ``get_benchmark_files()`` gruppiert nach SSoT-kanonischer ID.
- ``cleanup_runs()`` loescht ueberschuessige Runs.
- ``--keep`` CLI-Default kommt aus SSoT (5).
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, UTC
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.maintenance import cleanup_runs  # noqa: E402
from utils.backup_targets import RUNS_KEEP_DEFAULT  # noqa: E402


# ---------------------------------------------------------------------------
# get_benchmark_files
# ---------------------------------------------------------------------------

def test_get_benchmark_files_empty_dir(tmp_path):
    """Leeres Verzeichnis liefert leeres Dict."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    assert cleanup_runs.get_benchmark_files(runs_dir) == {}


def test_get_benchmark_files_nonexistent_dir(tmp_path):
    """Nicht existierendes Verzeichnis liefert leeres Dict (kein Crash)."""
    runs_dir = tmp_path / "does_not_exist"
    assert cleanup_runs.get_benchmark_files(runs_dir) == {}


def test_get_benchmark_files_ignores_non_json(tmp_path):
    """Nicht-JSON-Dateien werden ignoriert."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    (runs_dir / "results_foo_20260101_120000.txt").write_text("x")
    (runs_dir / "readme.md").write_text("x")
    assert cleanup_runs.get_benchmark_files(runs_dir) == {}


def test_get_benchmark_files_ignores_non_matching_json(tmp_path):
    """JSON-Dateien ohne RUN_FILE_RE-Pattern werden ignoriert."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    (runs_dir / "summary.json").write_text("{}")
    (runs_dir / "results_foo.json").write_text("{}")
    (runs_dir / "results_20260101_120000.json").write_text("{}")
    assert cleanup_runs.get_benchmark_files(runs_dir) == {}


def test_get_benchmark_files_groups_by_canonical_id(tmp_path):
    """Run-Files werden zu einer Gruppe pro kanonischer Modell-ID."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    files = []
    for ts in ["20260101_120000", "20260102_120000", "20260103_120000"]:
        f = runs_dir / f"results_foo_{ts}.json"
        f.write_text("{}")
        files.append(f)
    grouped = cleanup_runs.get_benchmark_files(runs_dir)
    assert len(grouped) == 1
    # Alle 3 Dateien in der Gruppe
    canon = list(grouped.keys())[0]
    assert len(grouped[canon]) == 3


def test_get_benchmark_files_handles_two_models(tmp_path):
    """Verschiedene Modelle ergeben verschiedene Gruppen."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    (runs_dir / "results_foo_20260101_120000.json").write_text("{}")
    (runs_dir / "results_bar_20260101_120000.json").write_text("{}")
    grouped = cleanup_runs.get_benchmark_files(runs_dir)
    assert len(grouped) == 2


# ---------------------------------------------------------------------------
# cleanup_runs
# ---------------------------------------------------------------------------

def test_cleanup_runs_no_files(tmp_path, capsys):
    """Kein Run-Files → 0 Loeschungen, freundliche Meldung."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    deleted = cleanup_runs.cleanup_runs(runs_dir, keep=1, force=True, dry_run=True)
    assert deleted == 0
    captured = capsys.readouterr()
    assert "No benchmark runs found" in captured.out


def test_cleanup_runs_below_threshold(tmp_path, capsys):
    """Weniger Runs als Schwellwert → nichts zu loeschen."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    (runs_dir / "results_foo_20260101_120000.json").write_text("{}")
    deleted = cleanup_runs.cleanup_runs(runs_dir, keep=5, force=True, dry_run=True)
    assert deleted == 0
    captured = capsys.readouterr()
    assert "No cleanup needed" in captured.out


def test_cleanup_runs_above_threshold_marks_for_deletion(tmp_path, capsys):
    """Mehr Runs als Schwellwert → ueberschuessige werden markiert (dry_run)."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    files = []
    for i in range(7):
        f = runs_dir / f"results_foo_{i:08d}_120000.json"
        f.write_text("{}")
        files.append(f)
        # mtime explizit setzen, damit die Sortierung stabil ist
        ts = (datetime(2026, 1, i + 1, 12, 0, 0, tzinfo=UTC)).timestamp()
        os.utime(f, (ts, ts))

    deleted = cleanup_runs.cleanup_runs(runs_dir, keep=5, force=True, dry_run=True)
    assert deleted == 2  # 7 - 5
    captured = capsys.readouterr()
    assert "Marking 2 for deletion" in captured.out
    assert "Dry Run" in captured.out
    # Alle Dateien noch da
    assert len(list(runs_dir.iterdir())) == 7


def test_cleanup_runs_force_deletion(tmp_path, capsys):
    """Mit force=True werden ueberschuessige Runs tatsaechlich geloescht."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    files = []
    for i in range(6):
        f = runs_dir / f"results_foo_{i:08d}_120000.json"
        f.write_text("{}")
        files.append(f)
        ts = (datetime(2026, 1, i + 1, 12, 0, 0, tzinfo=UTC)).timestamp()
        os.utime(f, (ts, ts))

    deleted = cleanup_runs.cleanup_runs(runs_dir, keep=2, force=True, dry_run=False)
    assert deleted == 4  # 6 - 2
    # Nur 2 uebrig — die zwei neuesten (Index 4 und 5)
    remaining = sorted(p.name for p in runs_dir.iterdir())
    assert len(remaining) == 2
    # Pruefe via Set statt Position (Reihenfolge abhaengig von Sortierung)
    assert {r for r in remaining} == {
        "results_foo_00000004_120000.json",
        "results_foo_00000005_120000.json",
    }
    # Die vier aeltesten muessen weg sein
    for old in (0, 1, 2, 3):
        assert not (runs_dir / f"results_foo_{old:08d}_120000.json").exists()


def test_cleanup_runs_keeps_newest_per_model(tmp_path):
    """Pro Modell werden die N neuesten gehalten, unabhaengig voneinander."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()

    # 4 foo-Runs (soll: 1 behalten, 3 loeschen bei keep=1)
    for i in range(4):
        f = runs_dir / f"results_foo_{i:08d}_120000.json"
        f.write_text("{}")
        ts = (datetime(2026, 1, i + 1, 12, 0, 0, tzinfo=UTC)).timestamp()
        os.utime(f, (ts, ts))

    # 2 bar-Runs (soll: 1 behalten, 1 loeschen bei keep=1)
    for i in range(2):
        f = runs_dir / f"results_bar_{i:08d}_120000.json"
        f.write_text("{}")
        ts = (datetime(2026, 2, i + 1, 12, 0, 0, tzinfo=UTC)).timestamp()
        os.utime(f, (ts, ts))

    deleted = cleanup_runs.cleanup_runs(runs_dir, keep=1, force=True, dry_run=False)
    assert deleted == 4  # 3 foo + 1 bar
    # 2 Dateien uebrig (neueste foo + neueste bar)
    assert len(list(runs_dir.iterdir())) == 2


def test_cleanup_runs_default_uses_ssoi():
    """Default-Parameter ist RUNS_KEEP_DEFAULT aus SSoT."""
    import inspect
    sig = inspect.signature(cleanup_runs.cleanup_runs)
    assert sig.parameters["keep"].default == RUNS_KEEP_DEFAULT


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_default_keep_is_ssoi():
    """CLI-Default fuer --keep ist SSoT-Konstante."""
    import inspect
    # main() baut argparse programmatisch; wir testen den literalen Source
    src = inspect.getsource(cleanup_runs.main)
    assert "default=RUNS_KEEP_DEFAULT" in src
