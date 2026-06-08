"""
Tests fuer Phase 9: Hard-Fail-Guard in ResultManager._validate_row_for_write.

Prueft, dass _write_to_csv() korrupte Zeilen (Header-Repeat, narrative
Asset-ID, ungueltige Modelle) VOR dem Schreiben filtert und ueberspringt.
Damit ist garantiert, dass zukuenftige Module oder manuelle Edits nicht
stillen Muell in die CSV schreiben koennen.
"""
import csv
import logging
import os
import sys
from pathlib import Path

import pytest

# Add root explicitly to allow importing utils and scripts
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.result_manager import ResultManager


class MockConfigValidator:
    def __init__(self, config: dict):
        self.config = config


@pytest.fixture
def temp_result_manager():
    """Erstellt einen ResultManager mit tmp-CSV-Pfaden."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        config = {
            "output": {
                "local_models_csv": str(tmp_path / "local.csv"),
                "commercial_csv": str(tmp_path / "commercial.csv"),
            }
        }
        rm = ResultManager(config_validator=MockConfigValidator(config))  # type: ignore[arg-type]
        yield rm, tmp_path


def test_validate_row_rejects_narrative_asset_id(temp_result_manager):
    """Narrative Asset-IDs werden via ValueError abgelehnt."""
    rm, _ = temp_result_manager
    row = {
        "model": "valid_model",
        "asset_id": "The Final Result is a long sentence with many words that exceed asset_id max",
        "status": "success",
    }
    with pytest.raises(ValueError, match="Narrative Asset-ID"):
        rm._validate_row_for_write(row, fieldnames=["model", "asset_id"])


def test_validate_row_rejects_header_repeat(temp_result_manager):
    """Header-Repeat (asset_id == 'asset_id' als String) wird abgelehnt."""
    rm, _ = temp_result_manager
    row = {
        "model": "valid_model",
        "asset_id": "asset_id",  # Header-Repeat-Pattern
        "status": "success",
    }
    with pytest.raises(ValueError, match="Header-Repeat"):
        rm._validate_row_for_write(row, fieldnames=["model", "asset_id"])


def test_validate_row_rejects_boolean_model(temp_result_manager):
    """Boolean-Modelle ('true'/'false') werden abgelehnt."""
    rm, _ = temp_result_manager
    for bad_model in ["True", "true", "False", "false", "TRUE"]:
        row = {
            "model": bad_model,
            "asset_id": "asset_a",
            "status": "success",
        }
        with pytest.raises(ValueError, match="Ungültiges Model"):
            rm._validate_row_for_write(row, fieldnames=["model", "asset_id"])


def test_validate_row_rejects_empty_model(temp_result_manager):
    """Leere/NaN-Modelle werden abgelehnt."""
    rm, _ = temp_result_manager
    for bad_model in ["", "nan", "null", "none"]:
        row = {
            "model": bad_model,
            "asset_id": "asset_a",
            "status": "success",
        }
        with pytest.raises(ValueError, match="Ungültiges Model"):
            rm._validate_row_for_write(row, fieldnames=["model", "asset_id"])


def test_validate_row_accepts_clean_row(temp_result_manager):
    """Saubere Zeile passiert die Validierung ohne Fehler."""
    rm, _ = temp_result_manager
    row = {
        "model": "gpt-4o-2024-08-06",
        "asset_id": "code_quality_005",
        "status": "success",
        "percentage": 85.0,
    }
    # Sollte nicht raisen
    rm._validate_row_for_write(row, fieldnames=["model", "asset_id", "status", "percentage"])


def test_write_to_csv_skips_corrupt_rows(temp_result_manager, caplog):
    """_write_to_csv() ueberspringt korrupte Zeilen und loggt eine Warnung."""
    rm, tmp_path = temp_result_manager

    # 3 Ergebnisse: 1 sauber, 1 mit narrativer Asset-ID, 1 mit Boolean-Model
    results = [
        {
            "model": "gpt-4o-2024-08-06",
            "asset_id": "code_quality_005",
            "status": "success",
            "percentage": "85.0",
        },
        {
            "model": "gpt-4o-2024-08-06",
            "asset_id": "The Final Result is a long sentence that exceeds normal asset_id length limits",
            "status": "success",
            "percentage": "75.0",
        },
        {
            "model": "True",
            "asset_id": "asset_b",
            "status": "success",
            "percentage": "50.0",
        },
    ]

    with caplog.at_level(logging.WARNING):
        rm.save_results(results, result_type="local")

    # Re-Read und pruefe
    csv_file = tmp_path / "local.csv"
    with csv_file.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Nur die saubere Zeile sollte geschrieben sein
    assert len(rows) == 1, f"Erwarte 1 Zeile, gefunden: {len(rows)}"
    assert rows[0]["model"] == "gpt-4o-2024-08-06"
    assert rows[0]["asset_id"] == "code_quality_005"

    # Logging pruefen
    log_text = caplog.text
    assert "Hard-Fail-Guard" in log_text, "Erwarte Hard-Fail-Guard-Log-Eintrag"
    assert "Narrative" in log_text or "Ungültiges Model" in log_text


def test_save_results_resilient_with_mixed_corruption(temp_result_manager):
    """Save-Operation laeuft durch, obwohl einzelne Zeilen korrupt sind (resilient)."""
    rm, tmp_path = temp_result_manager

    # Nur 1 saubere + 1 korrupte Zeile — Save darf NICHT komplett fehlschlagen
    results = [
        {
            "model": "gpt-4o-2024-08-06",
            "asset_id": "code_quality_005",
            "status": "success",
            "percentage": "85.0",
        },
        {
            "model": "True",
            "asset_id": "asset_b",
            "status": "success",
            "percentage": "50.0",
        },
    ]

    # Darf keine Exception werfen
    csv_path = rm.save_results(results, result_type="local")

    assert csv_path is not None, "save_results muss trotz korrupter Zeilen einen Pfad liefern"
    assert csv_path.exists()
    # CSV enthaelt nur die saubere Zeile
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["asset_id"] == "code_quality_005"
