"""
Tests for scripts/core/tooluse_exporter.py (ToolUseExporter).
"""

import csv
import sys
from pathlib import Path
from unittest.mock import patch

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pytest
from schemas.result import BenchmarkResult
from scripts.core.tooluse_exporter import ToolUseExporter, get_fleet_group
from benchmark_modules.tooluse.core.constants import CSV_COLUMNS


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_exporter(tmp_path: Path) -> ToolUseExporter:
    exp = ToolUseExporter({})
    exp.CSV_PATH = tmp_path / "tooluse_leaderboard.csv"
    return exp


def _success_result(**data_overrides) -> BenchmarkResult:
    data = {
        "tool_transcript": {"status": "success", "provider": "tavily"},
        "p1_score": 80.0,
        "p2_score": 70.0,
        "combined_score": 75.0,
        "hallucination_flag": False,
        "call1_time_s": 1.0,
        "mcp_latency_s": 0.2,
        "call2_time_s": 0.8,
        "total_time_s": 2.0,
        "call1_tokens": 50,
        "call2_tokens": 50,
        "total_tokens": 100,
        "cost_usd": 0.001,
        "tool_call_attempts": 1,
        "parse_error_flag": False,
    }
    data.update(data_overrides)
    return BenchmarkResult(status="success", raw_response="ok", data=data)


def _read_rows(csv_path: Path):
    with csv_path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Test 1: export_result + finalize_model writes row to CSV
# ---------------------------------------------------------------------------

def test_export_result_writes_row(tmp_path):
    """export_result + finalize_model creates CSV with exactly 1 data row."""
    exporter = _make_exporter(tmp_path)
    with patch("scripts.core.tooluse_exporter._load_card_data", return_value={}):
        exporter.export_result(_success_result(), "test-model")
        exporter.finalize_model("test-model")

    assert exporter.CSV_PATH.exists()
    rows = _read_rows(exporter.CSV_PATH)
    assert len(rows) == 1
    assert rows[0]["model"] == "test-model"


# ---------------------------------------------------------------------------
# Test 2: second finalize_model with same model_id updates in place
# ---------------------------------------------------------------------------

def test_export_result_no_duplicate(tmp_path):
    """Two export_result calls + one finalize_model → aggregated into 1 row."""
    exporter = _make_exporter(tmp_path)
    with patch("scripts.core.tooluse_exporter._load_card_data", return_value={}):
        exporter.export_result(_success_result(), "test-model")
        exporter.export_result(_success_result(), "test-model")
        exporter.finalize_model("test-model")

    rows = _read_rows(exporter.CSV_PATH)
    assert len(rows) == 1


# ---------------------------------------------------------------------------
# Test 3: fleet_group — localweights + Desktop → local_sovereign
# ---------------------------------------------------------------------------

def test_fleet_group_local_sovereign():
    assert get_fleet_group("Desktop", "localweights") == "local_sovereign"


# ---------------------------------------------------------------------------
# Test 4: fleet_group — apionly → full_fleet
# ---------------------------------------------------------------------------

def test_fleet_group_full_fleet():
    assert get_fleet_group("Frontier", "apionly") == "full_fleet"


# ---------------------------------------------------------------------------
# Test 5: calculate_sovereignty_gap — 2 models (1 local, 1 commercial)
# ---------------------------------------------------------------------------

def test_calculate_sovereignty_gap(tmp_path):
    """
    modelA: combined=80, local_sovereign
    modelB: combined=90, full_fleet
    avg_all=85, avg_local=80 → gap = local - all = -5.0 (cloud leads)
    """
    exporter = _make_exporter(tmp_path)
    rows = [
        {col: "" for col in CSV_COLUMNS} | {
            "model": "modelA", "combined_score": "80.00", "fleet_group": "local_sovereign",
        },
        {col: "" for col in CSV_COLUMNS} | {
            "model": "modelB", "combined_score": "90.00", "fleet_group": "full_fleet",
        },
    ]
    exporter._write_rows(rows)

    gap = exporter.calculate_sovereignty_gap()
    assert gap == -5.0


# ---------------------------------------------------------------------------
# Test 6: calculate_sovereignty_gap — < 2 models → None
# ---------------------------------------------------------------------------

def test_calculate_sovereignty_gap_too_few(tmp_path):
    exporter = _make_exporter(tmp_path)
    rows = [
        {col: "" for col in CSV_COLUMNS} | {
            "model": "modelA", "combined_score": "80.00", "fleet_group": "local_sovereign",
        },
    ]
    exporter._write_rows(rows)

    gap = exporter.calculate_sovereignty_gap()
    assert gap is None


# ---------------------------------------------------------------------------
# Test 7: get_summary — all required keys present
# ---------------------------------------------------------------------------

def test_get_summary_required_fields(tmp_path):
    exporter = _make_exporter(tmp_path)
    summary = exporter.get_summary()

    required = {
        "total_models", "local_sovereign_count", "full_fleet_count",
        "fleet_avg_local", "fleet_avg_all", "sovereignty_gap",
        "top_local_model", "top_overall_model",
    }
    assert required.issubset(summary.keys())


# ---------------------------------------------------------------------------
# Test 8: CSV header matches CSV_COLUMNS order exactly
# ---------------------------------------------------------------------------

def test_csv_header_order(tmp_path):
    exporter = _make_exporter(tmp_path)
    with patch("scripts.core.tooluse_exporter._load_card_data", return_value={}):
        exporter.export_result(_success_result(), "test-model")
        exporter.finalize_model("test-model")

    with exporter.CSV_PATH.open(encoding="utf-8") as f:
        header = f.readline().strip().split(",")
    assert header == CSV_COLUMNS


# ---------------------------------------------------------------------------
# Test 9: Model Card fallback — _load_card_data returns None → no crash
# ---------------------------------------------------------------------------

def test_export_result_no_card_fallback(tmp_path):
    """No card → display_name=model_id, vendor='Unknown', no exception."""
    exporter = _make_exporter(tmp_path)
    with patch("scripts.core.tooluse_exporter._load_card_data", return_value=None):
        exporter.export_result(_success_result(), "no-card-model")
        exporter.finalize_model("no-card-model")

    rows = _read_rows(exporter.CSV_PATH)
    assert len(rows) == 1
    assert rows[0]["display_name"] == "no-card-model"
    assert rows[0]["vendor"] == "Unknown"


# ---------------------------------------------------------------------------
# Test 10: status=error → row written with blank scores, assets_error=1
# ---------------------------------------------------------------------------

def test_export_result_error_status(tmp_path):
    """BenchmarkResult status=error → p1/combined empty, assets_error='1'."""
    exporter = _make_exporter(tmp_path)
    error_result = BenchmarkResult(status="error", raw_response="", data={})

    with patch("scripts.core.tooluse_exporter._load_card_data", return_value={}):
        exporter.export_result(error_result, "error-model")
        exporter.finalize_model("error-model")

    rows = _read_rows(exporter.CSV_PATH)
    assert len(rows) == 1
    assert rows[0]["p1_score"] == ""
    assert rows[0]["combined_score"] == ""
    assert rows[0]["assets_error"] == "1"


# ---------------------------------------------------------------------------
# Test 11: call1_time_s aggregation = mean across assets
# ---------------------------------------------------------------------------

def test_finalize_call1_time_mean(tmp_path):
    """call1_time_s across 2 assets is averaged (2.0 and 4.0 → 3.0)."""
    exporter = _make_exporter(tmp_path)
    with patch("scripts.core.tooluse_exporter._load_card_data", return_value={}):
        exporter.export_result(_success_result(call1_time_s=2.0, total_time_s=3.0), "m1")
        exporter.export_result(_success_result(call1_time_s=4.0, total_time_s=5.0), "m1")
        exporter.finalize_model("m1")

    rows = _read_rows(exporter.CSV_PATH)
    assert float(rows[0]["call1_time_s"]) == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# Test 12: total_time_s aggregation = sum across assets
# ---------------------------------------------------------------------------

def test_finalize_total_time_sum(tmp_path):
    """total_time_s across 3 assets is summed (5+7+8 = 20.0)."""
    exporter = _make_exporter(tmp_path)
    with patch("scripts.core.tooluse_exporter._load_card_data", return_value={}):
        for t in [5.0, 7.0, 8.0]:
            exporter.export_result(_success_result(total_time_s=t), "m2")
        exporter.finalize_model("m2")

    rows = _read_rows(exporter.CSV_PATH)
    assert float(rows[0]["total_time_s"]) == pytest.approx(20.0)


# ---------------------------------------------------------------------------
# Test 13: parse_error_flag = True if any asset had a parse error
# ---------------------------------------------------------------------------

def test_finalize_parse_error_flag_any(tmp_path):
    """parse_error_flag=True if any asset had it, even if others did not."""
    exporter = _make_exporter(tmp_path)
    with patch("scripts.core.tooluse_exporter._load_card_data", return_value={}):
        exporter.export_result(_success_result(parse_error_flag=False), "m3")
        exporter.export_result(_success_result(parse_error_flag=True), "m3")
        exporter.export_result(_success_result(parse_error_flag=False), "m3")
        exporter.finalize_model("m3")

    rows = _read_rows(exporter.CSV_PATH)
    assert rows[0]["parse_error_flag"] == "true"


# ---------------------------------------------------------------------------
# Test 14: tool_call_valid all-true → true
# ---------------------------------------------------------------------------

def test_finalize_tool_call_valid_all_true(tmp_path):
    """All 3 assets have valid tool calls → tool_call_valid='true'."""
    exporter = _make_exporter(tmp_path)
    with patch("scripts.core.tooluse_exporter._load_card_data", return_value={}):
        for _ in range(3):
            exporter.export_result(_success_result(), "m4")
        exporter.finalize_model("m4")

    rows = _read_rows(exporter.CSV_PATH)
    assert rows[0]["tool_call_valid"] == "true"


# ---------------------------------------------------------------------------
# Test 15: tool_call_valid 1-of-3 false → false
# ---------------------------------------------------------------------------

def test_finalize_tool_call_valid_one_false(tmp_path):
    """One of 3 assets has parse_error transcript → tool_call_valid='false'."""
    exporter = _make_exporter(tmp_path)
    with patch("scripts.core.tooluse_exporter._load_card_data", return_value={}):
        exporter.export_result(_success_result(), "m5")
        exporter.export_result(
            _success_result(
                tool_transcript={"status": "parse_error", "provider": "mock"}
            ),
            "m5",
        )
        exporter.export_result(_success_result(), "m5")
        exporter.finalize_model("m5")

    rows = _read_rows(exporter.CSV_PATH)
    assert rows[0]["tool_call_valid"] == "false"


# ---------------------------------------------------------------------------
# Test 16: cost_usd = sum across assets
# ---------------------------------------------------------------------------

def test_finalize_cost_sum(tmp_path):
    """cost_usd across 3 assets is summed (0.001 × 3 = 0.003)."""
    exporter = _make_exporter(tmp_path)
    with patch("scripts.core.tooluse_exporter._load_card_data", return_value={}):
        for _ in range(3):
            exporter.export_result(_success_result(cost_usd=0.001), "m6")
        exporter.finalize_model("m6")

    rows = _read_rows(exporter.CSV_PATH)
    assert float(rows[0]["cost_usd"]) == pytest.approx(0.003)
