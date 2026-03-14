import pytest
import csv
import pandas as pd
from pathlib import Path
import tempfile
import sys
import os

# Add root explicitly to allow importing utils and scripts
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.result_manager import ResultManager
from scripts.leaderboard.score_calculator import _aggregate_basic_stats


class MockConfigValidator:
    def __init__(self, config):
        self.config = config


@pytest.fixture
def temp_result_manager():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        config = {
            "output": {
                "local_models_csv": str(tmp_path / "local.csv"),
                "commercial_csv": str(tmp_path / "commercial.csv"),
            }
        }
        rm = ResultManager(config_validator=MockConfigValidator(config))
        yield rm, tmp_path


def test_old_csv_loads_without_judge_columns(temp_result_manager):
    rm, tmp_path = temp_result_manager
    csv_file = tmp_path / "local.csv"

    # Create an "old" CSV manually without judge columns
    old_fields = ["model", "asset_id", "execution_time"]
    with csv_file.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=old_fields)
        writer.writeheader()
        writer.writerow({"model": "m1", "asset_id": "a1", "execution_time": "1.5"})

    # Now we save a new result using ResultManager, which should merge old + new keys
    # and guarantee the 5 judge columns are present at the end.
    new_result = {
        "model": "m1",
        "asset_id": "a2",
        "execution_time": "2.0",
        # No judge columns explicitly in the result dictionary
    }
    rm.save_results([new_result], result_type="local")

    # Verify the resulted CSV has the old data, the new data, and all judge columns are present and empty (None/empty str)
    with csv_file.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        assert "llm_judge_score" in fieldnames
        assert "llm_judge_latency_ms" in fieldnames

        rows = list(reader)
        assert len(rows) == 2
        # First row from old schema
        assert rows[0]["model"] == "m1"
        assert rows[0]["asset_id"] == "a1"
        assert rows[0]["llm_judge_score"] == ""
        # Second row
        assert rows[1]["model"] == "m1"
        assert rows[1]["asset_id"] == "a2"
        assert rows[1]["llm_judge_score"] == ""


def test_new_csv_preserves_judge_columns(temp_result_manager):
    rm, tmp_path = temp_result_manager

    result = {
        "model": "m2",
        "asset_id": "a1",
        "execution_time": 1.0,
        "llm_judge_score": 5,
        "llm_judge_reasoning": "Good",
        "llm_judge_latency_ms": 100,
        "llm_judge_provider_used": "openai",
        "llm_judge_parse_success": True,
    }

    rm.save_results([result], result_type="local")

    csv_file = tmp_path / "local.csv"
    with csv_file.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames

        # Verify the 10 judge fields exist in the appended set. They might not be exactly strictly the last 10
        # depending on sorting logic, but they are guaranteed to be in fieldnames.
        # Actually our implementation `base_keys + judge_fields` makes them exactly the last N fields!
        assert fields[-14:] == [
            "llm_judge_score",
            "llm_judge_reasoning",
            "llm_judge_latency_ms",
            "llm_judge_provider_used",
            "llm_judge_model_used",
            "llm_judge_parse_success",
            "scoring_method",
            "judge_task_compliance",
            "judge_output_quality",
            "judge_standard_adherence",
            "finish_reason",
            "token_limit_cutoff",
            "token_limit_fallback",
            "token_limit_used",
        ]

        rows = list(reader)
        row = rows[0]
        assert row["llm_judge_score"] == "5"
        assert row["llm_judge_reasoning"] == "Good"


def test_leaderboard_aggregation_with_partial_judge_data():
    df = pd.DataFrame(
        [
            # Model 1 has full judge data
            {
                "model": "M1",
                "model_version": "v1",
                "type": "local",
                "category": "Scoring",
                "execution_time": 1.0,
                "llm_judge_score": 4.0,
                "asset_id": "a1",
                "percentage": 100,
            },
            {
                "model": "M1",
                "model_version": "v1",
                "type": "local",
                "category": "Scoring",
                "execution_time": 1.0,
                "llm_judge_score": 5.0,
                "asset_id": "a2",
                "percentage": 100,
            },
            # Model 2 has partial judge data
            {
                "model": "M2",
                "model_version": "v1",
                "type": "local",
                "category": "Scoring",
                "execution_time": 1.0,
                "llm_judge_score": 2.0,
                "asset_id": "a1",
                "percentage": 100,
            },
            {
                "model": "M2",
                "model_version": "v1",
                "type": "local",
                "category": "Scoring",
                "execution_time": 1.0,
                "llm_judge_score": None,
                "asset_id": "a2",
                "percentage": 100,
            },  # NaN
            # Model 3 has no judge data
            {
                "model": "M3",
                "model_version": "v1",
                "type": "local",
                "category": "Scoring",
                "execution_time": 1.0,
                "asset_id": "a1",
                "percentage": 100,
            },
        ]
    )

    # We can invoke _aggregate_basic_stats directly
    modules_config = {
        "Scoring": {"enable_scoring": True, "name": "Scoring", "enabled": True}
    }

    agg_df = _aggregate_basic_stats(df, modules_config)

    # Verify outputs
    m1_stats = agg_df[agg_df["model"] == "M1"].iloc[0]
    assert m1_stats["llm_judge_avg"] == 4.5
    assert m1_stats["judge_coverage"] == 1.0

    m2_stats = agg_df[agg_df["model"] == "M2"].iloc[0]
    assert m2_stats["llm_judge_avg"] == 2.0
    assert m2_stats["judge_coverage"] == 0.5

    m3_stats = agg_df[agg_df["model"] == "M3"].iloc[0]
    assert pd.isna(m3_stats["llm_judge_avg"])
    assert m3_stats["judge_coverage"] == 0.0
