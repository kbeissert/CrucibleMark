"""Phase 27: Tests fuer die ID-Normalisierung in ``consolidate_csv.py``.

Sichert:
- ``_normalize_model_column()`` nutzt die ID-SSoT.
- IDs mit unterschiedlichen Schreibweisen werden zusammengefuehrt.
- Phase-9 Defense-in-Depth (Sanitizer) bleibt aktiv (siehe
  ``test_consolidate_csv_validates.py``).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.maintenance import consolidate_csv as cc  # noqa: E402
from utils.backup_targets import CSV_FILES  # noqa: E402


# ---------------------------------------------------------------------------
# _normalize_model_column
# ---------------------------------------------------------------------------

def test_normalize_model_column_passthrough_when_no_model():
    """Wenn 'model'-Spalte fehlt, wird der DataFrame unveraendert zurueckgegeben."""
    df = pd.DataFrame({"foo": ["a", "b"], "bar": [1, 2]})
    result = cc._normalize_model_column(df)
    assert result.equals(df)


def test_normalize_model_column_handles_empty_df():
    """Leere DataFrames werden klaglos zurueckgegeben."""
    df = pd.DataFrame(columns=["model", "asset_id"])
    result = cc._normalize_model_column(df)
    assert result.empty


def test_normalize_model_column_normalizes_special_chars():
    """Sonderzeichen in 'model' werden via SSoT ersetzt (kein direkter re.sub)."""
    # Werte, die KEINE Karte haben → fallen auf _safe_name zurueck
    df = pd.DataFrame({
        "model": ["foo/bar", "foo:bar", "foo.bar", "foo bar"],
        "asset_id": ["a1", "a2", "a3", "a4"],
    })
    result = cc._normalize_model_column(df)
    models = result["model"].tolist()
    # _safe_name ersetzt :, /, ., Space durch _
    for m in models:
        assert "/" not in m
        assert ":" not in m
        assert "." not in m
    # Mindestens die _safe_name-Form erreicht
    assert "foo_bar" in models


def test_normalize_model_column_keeps_already_safe_names():
    """Bereits kanonische Namen ohne Card-Match bleiben unveraendert."""
    # Wir nutzen Modellnamen OHNE existierende Card, damit die SSoT-Funktion
    # auf den _safe_name-Fallback laeuft (kein Card-Lookup-Drift).
    df = pd.DataFrame({
        "model": ["my-test-model-001", "another-fake-model-002"],
        "asset_id": ["a1", "a2"],
    })
    result = cc._normalize_model_column(df)
    models = result["model"].tolist()
    # Keine Sonderzeichen → _safe_name-Fallback aendert nichts
    assert "my-test-model-001" in models
    assert "another-fake-model-002" in models


def test_normalize_model_column_returns_copy_not_view():
    """Original-DataFrame wird nicht mutiert."""
    df = pd.DataFrame({"model": ["foo/bar"], "asset_id": ["a1"]})
    df_original = df.copy()
    cc._normalize_model_column(df)
    assert df.equals(df_original)


def test_normalize_model_column_handles_none_values():
    """None/NaN-Werte in model-Spalte crashen nicht und werden zu NaN."""
    import numpy as np
    df = pd.DataFrame({
        "model": [None, "valid"],
        "asset_id": ["a1", "a2"],
    })
    result = cc._normalize_model_column(df)
    # Pandas konvertiert None zu NaN (float-Representation).
    # Wichtig: kein Crash, und der gueltige Wert bleibt unveraendert.
    assert pd.isna(result["model"].iloc[0])  # NaN-Vergleich (None wird zu NaN)
    assert result["model"].iloc[1] == "valid"


# ---------------------------------------------------------------------------
# consolidate_file — End-to-End mit ID-Normalisierung
# ---------------------------------------------------------------------------

def test_consolidate_file_dedupes_after_normalize(tmp_path, caplog):
    """Doppelte Eintraege mit Schreibweisenvarianten werden zu einem zusammengefuehrt."""
    import logging
    csv_path = tmp_path / "test.csv"
    rows = [
        "timestamp,model,asset_id,status,percentage",
        # Variante 1: foo/bar (wird zu foo_bar)
        "2026-01-01 10:00:00,foo/bar,asset_a,success,80.0",
        # Variante 2: foo_bar (bereits kanonisch)
        "2026-01-01 09:00:00,foo_bar,asset_a,success,75.0",
    ]
    csv_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

    with caplog.at_level(logging.INFO):
        cc.consolidate_file(csv_path, key_cols=("model", "asset_id"))

    df_after = pd.read_csv(csv_path)
    # Nach Normalisierung: beide Zeilen ergeben dasselbe model → nur 1 Zeile
    assert len(df_after) == 1
    # Neueste (2026-01-01 10:00:00) gewinnt
    assert "80.0" in str(df_after.iloc[0]["percentage"]) or df_after.iloc[0]["percentage"] == 80.0


def test_consolidate_file_uses_tuple_key_cols(tmp_path, caplog):
    """Signatur akzeptiert tuple (nicht list) fuer key_cols."""
    import logging
    csv_path = tmp_path / "test.csv"
    csv_path.write_text(
        "timestamp,model,asset_id,status\n"
        "2026-01-01 10:00:00,foo,asset_a,success\n",
        encoding="utf-8",
    )
    with caplog.at_level(logging.INFO):
        cc.consolidate_file(csv_path, key_cols=("model", "asset_id"))  # tuple
    # Sollte ohne Crash durchlaufen
    assert "SSoT" in caplog.text or "Verarbeite" in caplog.text or "Bereinigt" in caplog.text or "Keine Duplikate" in caplog.text


def test_consolidate_file_no_duplicates_keeps_file_unchanged(tmp_path):
    """CSV ohne Duplikate wird nicht ueberschrieben."""
    csv_path = tmp_path / "clean.csv"
    original = (
        "timestamp,model,asset_id,status\n"
        "2026-01-01 10:00:00,foo,asset_a,success\n"
    )
    csv_path.write_text(original, encoding="utf-8")
    cc.consolidate_file(csv_path, key_cols=("model", "asset_id"))
    # Datei-Inhalt bleibt
    assert csv_path.read_text(encoding="utf-8") == original


# ---------------------------------------------------------------------------
# CSV_FILES SSoT
# ---------------------------------------------------------------------------

def test_csv_files_imported_from_backup_targets():
    """CSV_FILES kommt aus utils.backup_targets (SSoT)."""
    # Wenn das Modul sauber ist, ist die Liste identisch mit dem SSoT
    assert cc.CSV_FILES == CSV_FILES


def test_csv_files_have_valid_key_cols():
    """Jede CSV hat einen gueltigen Schluessel (model oder (model, asset_id))."""
    for _path, keys in cc.CSV_FILES:
        assert len(keys) >= 1
        assert "model" in keys
