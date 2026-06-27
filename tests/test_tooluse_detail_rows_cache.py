"""Tests für ToolUseExporter.has_detail_rows() und Cache-Check-Logik (v4.10.12).

Stellt sicher, dass der Cache-Check im ToolUse-Runner nicht nur das Leaderboard
prüft, sondern auch die Per-Asset-Detailzeilen in den Benchmark-CSVs.
Verhindert, dass Modelle mit fehlenden Detailzeilen (Legacy-Pfad A) übersprungen werden.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.core.tooluse_exporter import ToolUseExporter


@pytest.fixture
def exporter(tmp_path, monkeypatch):
    """ToolUseExporter mit tmp_path als ROOT."""
    config = {"output": {"directory": str(tmp_path)}}
    exp = ToolUseExporter(config)

    # Patch _BENCHMARK_CSV_PATHS auf tmp_path
    monkeypatch.setattr(
        exp, "_BENCHMARK_CSV_PATHS",
        (str(tmp_path / "local.csv"), str(tmp_path / "cloud.csv"), str(tmp_path / "commercial.csv")),
    )
    return exp


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class TestHasDetailRows:
    """Tests für ToolUseExporter.has_detail_rows()."""

    def test_no_csvs_returns_false(self, exporter, tmp_path):
        """Keine CSVs existieren → False."""
        assert exporter.has_detail_rows("any/model") is False

    def test_no_tooluse_rows_returns_false(self, exporter, tmp_path):
        """CSV existiert, aber keine tooluse*-Zeilen → False."""
        _write_csv(tmp_path / "cloud.csv", [
            {"asset_id": "code_quality_001", "model": "test/model", "score": "80"},
        ])
        assert exporter.has_detail_rows("test/model") is False

    def test_with_tooluse_rows_returns_true(self, exporter, tmp_path):
        """CSV hat tooluse*-Zeilen für das Modell → True."""
        _write_csv(tmp_path / "cloud.csv", [
            {"asset_id": "tooluse001", "model": "test/model", "p1_score": "100"},
            {"asset_id": "tooluse002", "model": "test/model", "p1_score": "80"},
        ])
        assert exporter.has_detail_rows("test/model") is True

    def test_min_assets_threshold(self, exporter, tmp_path):
        """min_assets=3 erfordert mindestens 3 Zeilen."""
        _write_csv(tmp_path / "cloud.csv", [
            {"asset_id": "tooluse001", "model": "test/model", "p1_score": "100"},
            {"asset_id": "tooluse002", "model": "test/model", "p1_score": "80"},
        ])
        assert exporter.has_detail_rows("test/model", min_assets=2) is True
        assert exporter.has_detail_rows("test/model", min_assets=3) is False

    def test_model_id_mismatch_returns_false(self, exporter, tmp_path):
        """tooluse*-Zeilen für ein anderes Modell → False."""
        _write_csv(tmp_path / "cloud.csv", [
            {"asset_id": "tooluse001", "model": "other/model", "p1_score": "100"},
        ])
        assert exporter.has_detail_rows("test/model") is False

    def test_multiple_csvs_aggregated(self, exporter, tmp_path):
        """Zeilen über mehrere CSVs verteilt → True wenn Summe >= min_assets."""
        _write_csv(tmp_path / "local.csv", [
            {"asset_id": "tooluse001", "model": "test/model", "p1_score": "100"},
        ])
        _write_csv(tmp_path / "commercial.csv", [
            {"asset_id": "tooluse002", "model": "test/model", "p1_score": "80"},
        ])
        assert exporter.has_detail_rows("test/model", min_assets=2) is True

    def test_corrupted_csv_skipped(self, exporter, tmp_path):
        """Korrupte CSV wird übersprungen, andere CSV wird gelesen."""
        (tmp_path / "local.csv").write_text("not valid csv\n\x00\x00", encoding="utf-8")
        _write_csv(tmp_path / "cloud.csv", [
            {"asset_id": "tooluse001", "model": "test/model", "p1_score": "100"},
        ])
        assert exporter.has_detail_rows("test/model") is True


class TestExportResultDeprecation:
    """Tests für Pfad-A-Deprecation-Warning."""

    def test_export_result_logs_warning(self, exporter):
        """export_result() soll eine Deprecation-Warning loggen."""
        from schemas.result import BenchmarkResult
        with patch("scripts.core.tooluse_exporter.logger") as mock_logger:
            result = BenchmarkResult(
                model="test/model",
                asset_id="tooluse001",
                status="success",
                data={"p1_score": 100.0},
            )
            exporter.export_result(result, "test/model")
            mock_logger.warning.assert_called_once()
            call_args = str(mock_logger.warning.call_args)
            assert "deprecated" in call_args.lower() or "Pfad A" in call_args
