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


# ── Atomic Write Tests (Session 29: Kill/Crash-Resilienz) ──────────────────


def test_full_rewrite_preserves_existing_rows_not_revalidated(temp_result_manager):
    """Bestehende Zeilen werden beim Full-Rewrite NICHT erneut validiert.

    Wenn eine CSV existiert und ein Full-Rewrite stattfindet (z.B. wegen
    Header-Mismatch durch neue Spalten), müssen alle existierenden Zeilen
    erhalten bleiben — auch wenn sie von einer älteren Code-Version stammen.
    """
    rm, tmp_path = temp_result_manager
    csv_file = tmp_path / "local.csv"

    # Schreibe eine CSV mit "altem" Schema (wenige Spalten)
    old_fields = ["model", "asset_id", "execution_time"]
    with csv_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=old_fields)
        writer.writeheader()
        writer.writerow({"model": "m1", "asset_id": "a1", "execution_time": "1.5"})
        writer.writerow({"model": "m1", "asset_id": "a2", "execution_time": "2.0"})

    # Neues Ergebnis mit neuen Spalten (erzwingt Full-Rewrite weil Header-Mismatch)
    new_result = {
        "model": "m2",
        "asset_id": "a3",
        "execution_time": "3.0",
        "reasoning_tokens": 1500,
        "think_content": "Some reasoning text",
    }
    rm.save_results([new_result], result_type="local")

    # Prüfe: alle 3 Zeilen müssen vorhanden sein
    with csv_file.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 3, f"Erwarte 3 Zeilen (2 alt + 1 neu), gefunden: {len(rows)}"
    asset_ids = {r["asset_id"] for r in rows}
    assert asset_ids == {"a1", "a2", "a3"}
    # Alte Zeilen haben reasoning_tokens="" (neue Spalte, aber nicht re-validiert)
    m1_rows = [r for r in rows if r["model"] == "m1"]
    assert len(m1_rows) == 2


def test_atomic_write_no_corruption_on_header_mismatch(temp_result_manager):
    """Full-Rewrite bei Header-Mismatch schreibt atomar (keine Datenkorruption)."""
    rm, tmp_path = temp_result_manager
    csv_file = tmp_path / "local.csv"

    # Schreibe initiale Daten
    fields = ["model", "asset_id", "score"]
    with csv_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for i in range(100):
            writer.writerow({"model": "m1", "asset_id": f"a{i}", "score": str(i)})

    # Neues Ergebnis mit neuer Spalte → Full-Rewrite
    new_result = {
        "model": "m2",
        "asset_id": "a_new",
        "score": "999",
        "new_column": "new_value",
    }
    rm.save_results([new_result], result_type="local")

    # CSV muss konsistent sein: 101 Zeilen, Header enthält neue Spalte
    with csv_file.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    assert len(rows) == 101
    assert "new_column" in fieldnames
    # Alle alten Zeilen haben new_column=""
    old_rows = [r for r in rows if r["model"] == "m1"]
    assert len(old_rows) == 100
    # Keine .tmp-Datei übrig
    assert not list(tmp_path.glob("*.tmp")), "Keine .tmp-Dateien übrig"


def test_write_through_fast_path_single_result(temp_result_manager):
    """Write-Through (single-result) nutzt den Fast-Path (O(1) Append)."""
    rm, tmp_path = temp_result_manager
    csv_file = tmp_path / "commercial.csv"

    # Erste Zeile erstellt die CSV
    result1 = {"model": "m1", "asset_id": "a1", "score": "10"}
    rm.save_results([result1], result_type="commercial")

    # Zweite Zeile mit gleichem Header → Fast-Path Append
    result2 = {"model": "m1", "asset_id": "a2", "score": "20"}
    rm.save_results([result2], result_type="commercial")

    with csv_file.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    assert rows[0]["asset_id"] == "a1"
    assert rows[1]["asset_id"] == "a2"


def test_upsert_dedup_replaces_existing_row(temp_result_manager):
    """Upsert: gleiche (model, asset_id) Kombination wird ersetzt, nicht dupliziert."""
    rm, tmp_path = temp_result_manager
    csv_file = tmp_path / "commercial.csv"

    # Erste Version
    result_v1 = {"model": "m1", "asset_id": "a1", "score": "10"}
    rm.save_results([result_v1], result_type="commercial")

    # Zweite Version (gleiche Kombination → Upsert)
    result_v2 = {"model": "m1", "asset_id": "a1", "score": "99"}
    rm.save_results([result_v2], result_type="commercial")

    with csv_file.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1, f"Erwarte 1 Zeile (Upsert), gefunden: {len(rows)}"
    assert rows[0]["score"] == "99"
