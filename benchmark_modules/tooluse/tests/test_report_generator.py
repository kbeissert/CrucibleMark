"""Tests for scripts/analysis/generate_tooluse_report.py (ToolUseReportGenerator).
"""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pandas as pd

from scripts.analysis.generate_tooluse_report import (
    ToolUseReportGenerator,
    _build_deployment_recommendation,
    _build_strengths,
    _build_weaknesses,
    _score_label,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_REPORT_CONFIG = {
    "report": {
        "version": "1.0",
        "date_format": "%Y-%m-%d",
        "score_labels": {
            "excellent": 85.0,
            "good": 70.0,
            "moderate": 55.0,
            "weak": 0.0,
        },
        "latency_labels": {
            "fast": 3.0,
            "medium": 10.0,
            "slow": 99.0,
        },
        "parse_error_threshold": 0.0,
    },
}


def _make_generator(tmp_path: Path) -> ToolUseReportGenerator:
    gen = ToolUseReportGenerator(_REPORT_CONFIG)
    gen.root = tmp_path
    return gen


def _make_leaderboard_csv(tmp_path: Path, rows: list[dict]) -> Path:
    """Write a minimal tooluse_leaderboard.csv to tmp_path/benchmark_scores/."""
    scores_dir = tmp_path / "benchmark_scores"
    scores_dir.mkdir(parents=True, exist_ok=True)
    csv_path = scores_dir / "tooluse_leaderboard.csv"

    if not rows:
        csv_path.write_text("", encoding="utf-8")
        return csv_path

    fieldnames = list(rows[0].keys())
    import csv as _csv
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = _csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


def _default_row(model="test-model", **overrides) -> dict:
    row = {
        "model": model,
        "display_name": model,
        "vendor": "TestVendor",
        "sizeclass": "Medium",
        "deployment_type": "apionly",
        "model_version": "1.0",
        "timestamp": "2026-05-23",
        "mcp_mode": "mock",
        "p1_score": "80.00",
        "p2_score": "75.00",
        "combined_score": "77.50",
        "tool_call_valid": "true",
        "tool_call_attempts": "1",
        "retry_required": "false",
        "hallucination_flag": "false",
        "call1_time_s": "1.20",
        "mcp_latency_s": "0.30",
        "call2_time_s": "0.80",
        "total_time_s": "6.90",
        "call1_tokens": "50",
        "call2_tokens": "60",
        "total_tokens": "330",
        "cost_usd": "0.003",
        "assets_run": "3",
        "assets_error": "0",
        "fleet_group": "full_fleet",
        "sovereignty_gap": "",
    }
    row.update(overrides)
    return row


# ---------------------------------------------------------------------------
# Test 1: generate_model_report — returns non-empty string with key sections
# ---------------------------------------------------------------------------

def test_generate_model_report_key_sections(tmp_path):
    """generate_model_report returns string with required section headers."""
    gen = _make_generator(tmp_path)
    _make_leaderboard_csv(tmp_path, [_default_row()])

    report = gen.generate_model_report("test-model")

    assert isinstance(report, str)
    assert len(report) > 0
    assert "Tool Use Review" in report
    assert "Score Overview" in report
    assert "Asset Breakdown" in report


# ---------------------------------------------------------------------------
# Test 2: _get_score_label — 85.0 → "Excellent"
# ---------------------------------------------------------------------------

def test_score_label_excellent():
    thresholds = {"excellent": 85.0, "good": 70.0, "moderate": 55.0, "weak": 0.0}
    assert _score_label(85.0, thresholds) == "Excellent"
    assert _score_label(90.0, thresholds) == "Excellent"


# ---------------------------------------------------------------------------
# Test 3: _get_score_label — 63.5 → "Moderate"
# ---------------------------------------------------------------------------

def test_score_label_moderate():
    thresholds = {"excellent": 85.0, "good": 70.0, "moderate": 55.0, "weak": 0.0}
    assert _score_label(63.5, thresholds) == "Moderate"


# ---------------------------------------------------------------------------
# Test 4: _get_score_label — 40.0 → "Weak"
# ---------------------------------------------------------------------------

def test_score_label_weak():
    thresholds = {"excellent": 85.0, "good": 70.0, "moderate": 55.0, "weak": 0.0}
    assert _score_label(40.0, thresholds) == "Weak"


# ---------------------------------------------------------------------------
# Test 5: _build_strengths — p1≥80, tool_call_valid, attempts=1
# ---------------------------------------------------------------------------

def test_build_strengths_valid_tool_call():
    row = {
        "p1_score": "82.0",
        "p2_score": "72.0",
        "tool_call_valid": "true",
        "tool_call_attempts": "1",
        "hallucination_flag": "false",
        "total_time_s": "4.0",
    }
    asset_details = [{"asset_id": "tooluse001"}]
    strengths = _build_strengths(row, asset_details)

    labels = " ".join(strengths)
    assert "valide Tool-Call" in labels or "Direkter valider" in labels


# ---------------------------------------------------------------------------
# Test 6: _build_weaknesses — p2<55 → Synthesequalität
# ---------------------------------------------------------------------------

def test_build_weaknesses_low_p2():
    row = {
        "p2_score": "45.0",
        "retry_required": "false",
        "hallucination_flag": "false",
        "total_time_s": "5.0",
        "call1_tokens": "50",
    }
    weaknesses = _build_weaknesses(row)
    assert any("Synthesequalität" in w for w in weaknesses)


# ---------------------------------------------------------------------------
# Test 7: _build_weaknesses — hallucination_flag=True → ⚠ Halluzination
# ---------------------------------------------------------------------------

def test_build_weaknesses_hallucination():
    row = {
        "p2_score": "70.0",
        "retry_required": "false",
        "hallucination_flag": "true",
        "total_time_s": "5.0",
        "call1_tokens": "50",
    }
    weaknesses = _build_weaknesses(row)
    assert any("Halluzination" in w for w in weaknesses)


# ---------------------------------------------------------------------------
# Test 8: _build_deployment_recommendation — combined≥70, no hallucination
# ---------------------------------------------------------------------------

def test_deployment_recommendation_geeignet():
    row = {"combined_score": "77.5", "hallucination_flag": "false"}
    rec = _build_deployment_recommendation(row)
    assert "Geeignet" in rec or "✅" in rec


# ---------------------------------------------------------------------------
# Test 9: _build_deployment_recommendation — hallucination_flag=True
# ---------------------------------------------------------------------------

def test_deployment_recommendation_not_recommended():
    row = {"combined_score": "80.0", "hallucination_flag": "true"}
    rec = _build_deployment_recommendation(row)
    assert "Nicht empfohlen" in rec or "❌" in rec


# ---------------------------------------------------------------------------
# Test 10: generate_web_json — all required top-level keys
# ---------------------------------------------------------------------------

def test_generate_web_json_required_keys(tmp_path):
    gen = _make_generator(tmp_path)
    _make_leaderboard_csv(tmp_path, [_default_row()])

    data = gen.generate_web_json("test-model")

    required = {"scores", "performance", "reliability", "assets", "assessment"}
    assert required.issubset(data.keys())


# ---------------------------------------------------------------------------
# Test 11: generate_fleet_summary — contains "Sovereignty Gap" with 2 models
# ---------------------------------------------------------------------------

def test_generate_fleet_summary_sovereignty_gap(tmp_path):
    gen = _make_generator(tmp_path)
    rows = [
        _default_row("model-a", combined_score="80.00", fleet_group="local_sovereign"),
        _default_row("model-b", combined_score="90.00", fleet_group="full_fleet"),
    ]
    _make_leaderboard_csv(tmp_path, rows)

    summary = gen.generate_fleet_summary()

    assert "Sovereignty Gap" in summary


# ---------------------------------------------------------------------------
# Test 12: save_model_report — file created at expected path
# ---------------------------------------------------------------------------

def test_save_model_report_creates_file(tmp_path):
    gen = _make_generator(tmp_path)
    _make_leaderboard_csv(tmp_path, [_default_row()])

    path = gen.save_model_report("test-model")

    assert path.exists()
    assert path.suffix == ".md"
    assert "tooluse_review_" in path.name


# ---------------------------------------------------------------------------
# Test 13: load_leaderboard — returns empty DataFrame when CSV missing
# ---------------------------------------------------------------------------

def test_load_leaderboard_missing_csv(tmp_path):
    gen = _make_generator(tmp_path)
    df = gen.load_leaderboard()

    assert isinstance(df, pd.DataFrame)
    assert df.empty
