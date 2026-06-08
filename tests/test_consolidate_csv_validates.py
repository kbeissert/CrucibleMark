"""
Tests fuer Phase 9: Defense-in-Depth in consolidate_csv.py.

Prueft, dass die Sanitizer-Heuristiken beim Konsolidieren angewendet werden,
BEVOR die CSV zurueckgeschrieben wird. Verhindert, dass Header-Repeats,
narrative Asset-IDs und ungueltige Modelle nach einer Konsolidierung
weiterleben.

Diese Tests sind die Regressions-Sicherung fuer das SSoT-Versprechen von
Phase 8 (Sanitizer-Phase).
"""
import logging
import sys
import os
from pathlib import Path

import pandas as pd
import pytest

# Add root explicitly to allow importing utils and scripts
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.maintenance import consolidate_csv as cc


@pytest.fixture
def sample_corrupt_csv(tmp_path: Path) -> Path:
    """Baut eine CSV mit verschiedenen Korruptions-Mustern.

    Inhalt (4 Zeilen, 1 sauber, 3 korrupt):
      - saubere Zeile (model1, asset_a)
      - Header-Repeat (model-Spalte = 'asset_id' als String-Daten)
      - narrative Asset-ID ('The Final Result...')
      - Boolean-Model (model = 'True')
    """
    csv_path = tmp_path / "corrupt.csv"
    rows = [
        # Saubere Header-Zeile
        "timestamp,model,asset_id,status,percentage",
        # Saubere Daten-Zeile
        "2026-01-01 10:00:00,model1,asset_a,success,85.0",
        # Korrupt 1: Header-Repeat (die Zeile sieht aus wie der CSV-Header)
        "2026-01-01 10:01:00,model1,asset_id,success,90.0",
        # Korrupt 2: narrative Asset-ID
        "2026-01-01 10:02:00,model1,The Final Result is a long sentence with many words,success,75.0",
        # Korrupt 3: Boolean-Modell
        "2026-01-01 10:03:00,True,asset_b,success,50.0",
    ]
    csv_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return csv_path


def test_filter_corrupt_rows_drops_header_repeat(sample_corrupt_csv):
    """Header-Repeat-Zeilen (asset_id-Spalte enthaelt 'asset_id'-String) werden rausgefiltert."""
    df = pd.read_csv(sample_corrupt_csv)
    df_clean, stats = cc._filter_corrupt_rows(df, key_cols=["model", "asset_id"])

    assert stats["header_repeat"] == 1, "Erwarte genau 1 Header-Repeat-Drop"
    assert "asset_id" not in df_clean["asset_id"].astype(str).values or (
        df_clean["asset_id"].astype(str) == "asset_id"
    ).sum() == 0


def test_filter_corrupt_rows_drops_narrative_asset_id(sample_corrupt_csv):
    """Narrative Asset-IDs werden via _is_narrative_asset_id erkannt und rausgefiltert."""
    df = pd.read_csv(sample_corrupt_csv)
    df_clean, stats = cc._filter_corrupt_rows(df, key_cols=["model", "asset_id"])

    assert stats["narrative_asset_id"] == 1, "Erwarte genau 1 narrative-Asset-ID-Drop"
    # Pruefe: die narrative Zeile ist weg
    remaining = df_clean["asset_id"].astype(str).tolist()
    assert not any("The Final" in str(a) for a in remaining)


def test_filter_corrupt_rows_drops_invalid_model(sample_corrupt_csv):
    """Boolean-Modelle ('True'/'False') werden rausgefiltert."""
    df = pd.read_csv(sample_corrupt_csv)
    df_clean, stats = cc._filter_corrupt_rows(df, key_cols=["model", "asset_id"])

    assert stats["invalid_model"] == 1, "Erwarte genau 1 invalid-model-Drop"
    # Pruefe: kein 'True'/'False' mehr im model-Feld
    models = df_clean["model"].astype(str).str.lower().tolist()
    assert "true" not in models, "Boolean-Modell 'True' sollte raus sein"
    assert "false" not in models, "Boolean-Modell 'False' sollte raus sein"


def test_filter_corrupt_rows_keeps_clean_rows(sample_corrupt_csv):
    """Saubere Zeile bleibt erhalten."""
    df = pd.read_csv(sample_corrupt_csv)
    df_clean, _ = cc._filter_corrupt_rows(df, key_cols=["model", "asset_id"])

    assert len(df_clean) == 1, "Erwarte genau 1 saubere Zeile"
    assert df_clean.iloc[0]["model"] == "model1"
    assert df_clean.iloc[0]["asset_id"] == "asset_a"


def test_filter_corrupt_rows_handles_empty_dataframe():
    """Leere DataFrames werden ohne Fehler zurueckgegeben."""
    df = pd.DataFrame()
    df_clean, stats = cc._filter_corrupt_rows(df, key_cols=["model", "asset_id"])

    assert df_clean.empty
    assert stats == {
        "header_repeat": 0,
        "narrative_asset_id": 0,
        "invalid_model": 0,
    }


def test_filter_corrupt_rows_handles_missing_columns(tmp_path):
    """Wenn 'asset_id' oder 'model' fehlen, werden die Pruefungen uebersprungen."""
    csv_path = tmp_path / "no_model_col.csv"
    csv_path.write_text(
        "timestamp,foo,bar\n2026-01-01 10:00:00,x,y\n",
        encoding="utf-8",
    )
    df = pd.read_csv(csv_path)
    df_clean, stats = cc._filter_corrupt_rows(df, key_cols=["foo", "bar"])

    # Keine der 3 Heuristiken matcht (Spalten fehlen) → keine Drops
    assert sum(stats.values()) == 0
    assert len(df_clean) == 1


def test_consolidate_file_e2e_filters_corruption(tmp_path, caplog):
    """End-to-End: consolidate_file() filtert korrupte Zeilen vor dem Write."""
    csv_path = tmp_path / "e2e_corrupt.csv"
    rows = [
        "timestamp,model,asset_id,status,percentage",
        "2026-01-01 10:00:00,model1,asset_a,success,85.0",
        "2026-01-01 10:01:00,model1,asset_id,success,90.0",  # Header-Repeat
        "2026-01-01 10:02:00,True,asset_b,success,50.0",  # Boolean-Model
    ]
    csv_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    with caplog.at_level(logging.INFO):
        cc.consolidate_file(csv_path, key_cols=["model", "asset_id"])

    # Re-Read und pruefe
    df_after = pd.read_csv(csv_path)
    assert len(df_after) == 1, "Erwarte nur die saubere Zeile"
    assert df_after.iloc[0]["model"] == "model1"
    assert df_after.iloc[0]["asset_id"] == "asset_a"
    # Logging-Output pruefen
    log_text = caplog.text
    assert "Korrupt-Drop" in log_text or "Bereinigt" in log_text


def test_consolidate_file_handles_missing_file(tmp_path, caplog):
    """Fehlende Datei wird sauber uebersprungen."""
    csv_path = tmp_path / "does_not_exist.csv"
    with caplog.at_level(logging.INFO):
        cc.consolidate_file(csv_path, key_cols=["model", "asset_id"])
    assert "nicht gefunden" in caplog.text or "überspringe" in caplog.text.lower()


def test_filter_corrupt_rows_mixed_corruption_patterns():
    """Komplexer Test: mehrere Korruptions-Muster in einer Zeile — wird bei der ersten Heuristik gedroppt."""
    df = pd.DataFrame(
        {
            "model": ["True"],  # invalid_model matched first
            "asset_id": ["asset_id"],  # also header_repeat
            "status": ["success"],
            "timestamp": ["2026-01-01"],
        }
    )
    df_clean, stats = cc._filter_corrupt_rows(df, key_cols=["model", "asset_id"])

    # Die Zeile wird genau 1x gedroppt (egal welche Heuristik zuerst matched).
    # Wichtig: die Summe der Drops darf nicht > 1 sein.
    assert sum(stats.values()) == 1
    assert df_clean.empty
