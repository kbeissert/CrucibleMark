"""Tests for the Political Compass leaderboard repair migration.

Validates the idempotent behavior of scripts/maintenance/repair_pc_leaderboard.py
and guards against regression of the voreiliger-Cache-Hit bug fixed in
utils/base_runner.py.
"""

import csv
import json
import sys
from pathlib import Path
from unittest.mock import patch

# Add root directory to sys.path so we can import from scripts
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from scripts.maintenance.repair_pc_leaderboard import (  # noqa: E402
    LEADERBOARD_FIELDS,
    _module_block_coords,
    _reconstruct_leaderboard_row,
    _strip_date_suffixes,
    main as repair_main,
)


def _write_results_csv(path: Path, rows: list[dict]) -> None:
    """Schreibt eine pc_results.csv mit den gegebenen AVG-Zeilen."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["model", "model_version", "run_id", "x_coordinate",
                        "y_coordinate", "x_label", "y_label", "metrics_json",
                        "timestamp"],
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_leaderboard_csv(path: Path, rows: list[dict]) -> None:
    """Schreibt eine pc_leaderboard.csv mit den gegebenen Zeilen."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LEADERBOARD_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _sample_avg_row(model: str = "test/sample:14b",
                    model_version: str = "abc1234",
                    vanilla_x: float = -3.0,
                    vanilla_y: float = 2.5,
                    forced_x: float = -5.0,
                    forced_y: float = 1.0) -> dict:
    """Erzeugt eine AVG-Zeile mit korrekt strukturiertem metrics_json."""
    module_stats = {
        "vanilla": {f"7.{i}": {"x": vanilla_x + i * 0.1, "y": vanilla_y} for i in range(1, 10)},
        "forced": {f"7.{i}": {"x": forced_x + i * 0.1, "y": forced_y} for i in range(1, 10)},
    }
    metrics = {"module_stats": module_stats, "display": {"polarity_flip_rate": 12.5}}
    return {
        "model": model,
        "model_version": model_version,
        "run_id": "AVG",
        "x_coordinate": (vanilla_x + forced_x) / 2,
        "y_coordinate": (vanilla_y + forced_y) / 2,
        "x_label": "Sozial",
        "y_label": "Autoritär",
        "metrics_json": json.dumps(metrics, ensure_ascii=False),
        "timestamp": "2026-04-15T10:00:00.000000",
    }


def test_strip_date_suffixes_strips_openrouter_dates():
    """OpenRouter-Datums-Suffixe (-YYYYMMDD, -MMDD) müssen entfernt werden."""
    assert _strip_date_suffixes("kimi/k2-20251106") == "kimi/k2"
    assert _strip_date_suffixes("kimi/k2-0127") == "kimi/k2"  # Jan 27
    # Versions-Suffixe (-2503, -2411) bleiben erhalten
    assert _strip_date_suffixes("kimi/k2-2503") == "kimi/k2-2503"


def test_module_block_coords_returns_mean_over_blocks():
    """Mittelwert über 9 PC-Blöcke (7.1-7.9) für x und y Achse."""
    block = {
        "7.1": {"x": 1.0, "y": 2.0},
        "7.2": {"x": 3.0, "y": 4.0},
        "7.3": {"x": 5.0, "y": 6.0},
    }
    assert _module_block_coords(block, "x") == 3.0
    assert _module_block_coords(block, "y") == 4.0
    assert _module_block_coords({}, "x") is None
    assert _module_block_coords(None, "x") is None


def test_reconstruct_leaderboard_row_normalizes_hf_prefix():
    """hf.co/bartowski/-Präfix wird über normalize_model_id gestrippt."""
    row = _sample_avg_row(model="hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M")
    reconstructed = _reconstruct_leaderboard_row(row)
    assert reconstructed is not None
    assert reconstructed["model"] == "NousResearch_Hermes-4-14B-GGUF:Q4_K_M"


def test_reconstruct_leaderboard_row_computes_shift():
    """Shift-Distanz wird aus vanilla/forced Hauptkoordinaten berechnet."""
    row = _sample_avg_row(
        vanilla_x=0.0, vanilla_y=0.0, forced_x=3.0, forced_y=4.0,
    )
    reconstructed = _reconstruct_leaderboard_row(row)
    assert reconstructed is not None
    assert reconstructed["shift_x"] == 3.0
    assert reconstructed["shift_y"] == 4.0
    # sqrt(9+16) = 5.0
    assert reconstructed["shift_distance"] == 5.0


def test_repair_script_is_idempotent(tmp_path):
    """Idempotenz-Garantie: 2. Lauf ändert nichts am Leaderboard."""
    results_csv = tmp_path / "political_compass_results.csv"
    leaderboard_csv = tmp_path / "political_compass_leaderboard.csv"

    _write_results_csv(results_csv, [_sample_avg_row(model="vendor/model-a")])
    _write_leaderboard_csv(leaderboard_csv, [])

    with patch("sys.argv", ["repair_pc_leaderboard"]), \
         patch("scripts.maintenance.repair_pc_leaderboard.PC_RESULTS_CSV", results_csv), \
         patch("scripts.maintenance.repair_pc_leaderboard.PC_LEADERBOARD_CSV", leaderboard_csv):
        rc1 = repair_main()
        assert rc1 == 0

        # Zweiter Lauf: Eintrag existiert bereits → keine Änderung
        rc2 = repair_main()
        assert rc2 == 0

    with leaderboard_csv.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["model"] == "vendor/model-a"


def test_repair_dry_run_does_not_write(tmp_path):
    """--dry-run zeigt die geplanten Änderungen, schreibt aber nicht."""
    results_csv = tmp_path / "political_compass_results.csv"
    leaderboard_csv = tmp_path / "political_compass_leaderboard.csv"

    _write_results_csv(results_csv, [_sample_avg_row(model="vendor/model-x")])
    _write_leaderboard_csv(leaderboard_csv, [])

    with patch("sys.argv", ["repair_pc_leaderboard", "--dry-run"]), \
         patch("scripts.maintenance.repair_pc_leaderboard.PC_RESULTS_CSV", results_csv), \
         patch("scripts.maintenance.repair_pc_leaderboard.PC_LEADERBOARD_CSV", leaderboard_csv):
        rc = repair_main()
        assert rc == 0

    with leaderboard_csv.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 0


def test_repair_skips_runs_non_avg(tmp_path):
    """RUN_1/RUN_2-Zeilen dürfen NICHT als Leaderboard-Eintrag landern."""
    results_csv = tmp_path / "political_compass_results.csv"
    leaderboard_csv = tmp_path / "political_compass_leaderboard.csv"

    runs = [
        {**_sample_avg_row(model="vendor/model-z"), "run_id": "RUN_1"},
        {**_sample_avg_row(model="vendor/model-z"), "run_id": "RUN_2"},
        {**_sample_avg_row(model="vendor/model-z"), "run_id": "AVG"},
    ]
    _write_results_csv(results_csv, runs)
    _write_leaderboard_csv(leaderboard_csv, [])

    with patch("sys.argv", ["repair_pc_leaderboard"]), \
         patch("scripts.maintenance.repair_pc_leaderboard.PC_RESULTS_CSV", results_csv), \
         patch("scripts.maintenance.repair_pc_leaderboard.PC_LEADERBOARD_CSV", leaderboard_csv):
        rc = repair_main()
        assert rc == 0

    # Genau 1 Eintrag (nur die AVG-Zeile), nicht 3
    with leaderboard_csv.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1


def test_execute_batch_module_fix_in_source():
    """Statischer Regression-Test: sichert den Fix in utils/base_runner.py ab.

    Hintergrund: Vor 2026-06-03 führte der voreilige Cache-Hit auf
    `(model, batch_asset_id)` zum early-return, bevor PoliticalCompassHandler
    aufgerufen wurde. Der Fix schließt PC-Module explizit vom 3-CSV-Fast-Path
    aus und überlässt die Skip-Entscheidung dem pc_leaderboard.csv Check.

    Dieser Test liest den Quellcode direkt und verifiziert, dass die korrekte
    Bedingung vorhanden ist. Mock-basiertes Testen von execute_batch_module
    ist zu komplex (viele interne Mocks nötig); der statische Test ist die
    robustere Absicherung gegen versehentliche Regressions.
    """
    base_runner_path = Path(__file__).parent.parent / "utils" / "base_runner.py"
    source = base_runner_path.read_text(encoding="utf-8")

    # Der Fix: PC-Cache-Hit darf NICHT zum early-return führen
    assert "PoliticalCompassHandler.is_political_compass(benchmark_info)" in source, (
        "PC-Spezialfall im 3-CSV-Cache-Check fehlt — "
        "voreiliger Cache-Hit-Bug ist möglicherweise zurück!"
    )
    # Die ursprüngliche fehlerhafte Bedingung darf NICHT mehr existieren
    assert (
        'if cached_res:\n                print(f"⏩ Überspringe' not in source
    ), (
        "Alter voreiliger Cache-Hit-Code gefunden — bitte execute_batch_module prüfen!"
    )
