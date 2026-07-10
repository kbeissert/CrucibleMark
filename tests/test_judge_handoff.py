"""
Unit tests for judge_handoff.py.

Covers:
- response_time_ms is immutable after creation (ValueError on overwrite)
- save_pending() / load_pending() round-trip JSON serialization
- to_final_result() with missing judge fields returns None gracefully
- frozen_response_time_ms property
- is_complete() reflects Phase-3 readiness
"""

import json
import tempfile
from pathlib import Path

import pytest

from utils.scoring.llm_judge.judge_handoff import (
    PendingJudgeResult,
    load_pending,
    save_pending,
)


def _make_pending(
    task_id: str = "task_001",
    response_time_ms: float = 1234.5,
    hybrid_score: float = 72.0,
) -> PendingJudgeResult:
    """Build a minimal PendingJudgeResult for testing."""
    return PendingJudgeResult(
        task_id=task_id,
        module_id="ux_writing",
        task_prompt="Write a cancel button label.",
        model_response="Cancel",
        golden_standard="Cancel subscription",
        hybrid_score=hybrid_score,
        response_time_ms=response_time_ms,
    )


class TestResponseTimeFrozen:
    """response_time_ms must not be overwritable after __post_init__."""

    def test_overwrite_raises_value_error(self):
        p = _make_pending(response_time_ms=500.0)
        with pytest.raises(ValueError, match="frozen"):
            p.response_time_ms = 999.0

    def test_original_value_preserved(self):
        p = _make_pending(response_time_ms=500.0)
        assert p.response_time_ms == 500.0

    def test_frozen_response_time_ms_property(self):
        p = _make_pending(response_time_ms=321.0)
        assert p.frozen_response_time_ms == 321.0

    def test_other_fields_can_be_set(self):
        """Phase-3 fields must remain mutable."""
        p = _make_pending()
        p.judge_score = 4
        p.judge_reasoning = "Good output."
        p.judge_latency_ms = 450.0
        p.judge_parse_success = True
        p.judge_provider_used = "anthropic"
        assert p.judge_score == 4
        assert p.judge_provider_used == "anthropic"


class TestSaveAndLoadPending:
    """Round-trip JSON persistence via save_pending / load_pending."""

    def test_save_creates_file(self):
        p = _make_pending()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "result.json"
            save_pending(p, dest)
            assert dest.exists()

    def test_load_restores_fields(self):
        p = _make_pending(task_id="my_task", response_time_ms=999.9, hybrid_score=88.0)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "result.json"
            save_pending(p, dest)
            restored = load_pending(dest)

        assert restored.task_id == "my_task"
        assert restored.response_time_ms == pytest.approx(999.9)
        assert restored.hybrid_score == pytest.approx(88.0)
        assert restored.module_id == "ux_writing"

    def test_response_time_frozen_after_load(self):
        p = _make_pending(response_time_ms=777.0)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "result.json"
            save_pending(p, dest)
            restored = load_pending(dest)

        with pytest.raises(ValueError, match="frozen"):
            restored.response_time_ms = 0.0

    def test_phase3_fields_persisted(self):
        p = _make_pending()
        p.judge_score = 3
        p.judge_reasoning = "Adequate."
        p.judge_latency_ms = 200.0
        p.judge_parse_success = True
        p.judge_provider_used = "mistral"

        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "result.json"
            save_pending(p, dest)
            restored = load_pending(dest)

        assert restored.judge_score == 3
        assert restored.judge_reasoning == "Adequate."
        assert restored.judge_latency_ms == pytest.approx(200.0)
        assert restored.judge_parse_success is True
        assert restored.judge_provider_used == "mistral"

    def test_load_missing_required_field_raises(self):
        bad_json = {"task_id": "x", "module_id": "y"}  # missing many required fields
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "bad.json"
            dest.write_text(json.dumps(bad_json))
            with pytest.raises(ValueError, match="missing required fields"):
                load_pending(dest)

    def test_save_creates_parent_directories(self):
        p = _make_pending()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "nested" / "deep" / "result.json"
            save_pending(p, dest)
            assert dest.exists()


class TestToFinalResult:
    """to_final_result() serialises correctly, including None Phase-3 fields."""

    def test_to_final_result_before_phase3(self):
        p = _make_pending(task_id="x", response_time_ms=200.0, hybrid_score=65.0)
        result = p.to_final_result()
        # All Phase-3 fields should be None (not absent)
        assert result["judge_score"] is None
        assert result["judge_reasoning"] is None
        assert result["judge_latency_ms"] is None
        assert result["judge_parse_success"] is None
        assert result["judge_provider_used"] is None

    def test_to_final_result_after_phase3(self):
        p = _make_pending(task_id="x", response_time_ms=200.0)
        p.judge_score = 5
        p.judge_reasoning = "Excellent."
        p.judge_parse_success = True
        p.judge_provider_used = "openai"
        result = p.to_final_result()
        assert result["judge_score"] == 5
        assert result["judge_reasoning"] == "Excellent."
        assert result["judge_parse_success"] is True
        assert result["judge_provider_used"] == "openai"

    def test_to_final_result_contains_response_time(self):
        p = _make_pending(response_time_ms=123.4)
        result = p.to_final_result()
        assert result["response_time_ms"] == pytest.approx(123.4)

    def test_to_final_result_is_json_serialisable(self):
        """Verify the dict can be serialised to JSON without errors."""
        p = _make_pending()
        p.judge_score = 4
        result = p.to_final_result()
        dumped = json.dumps(result)
        loaded = json.loads(dumped)
        assert loaded["judge_score"] == 4


class TestIsComplete:
    """is_complete() reflects whether Phase 3 has been applied."""

    def test_not_complete_before_phase3(self):
        p = _make_pending()
        assert p.is_complete() is False

    def test_not_complete_with_partial_fields(self):
        p = _make_pending()
        p.judge_score = 3  # parse_success still None
        assert p.is_complete() is False

    def test_complete_when_both_populated(self):
        p = _make_pending()
        p.judge_score = 3
        p.judge_parse_success = True
        assert p.is_complete() is True

    def test_complete_with_none_score_but_parse_success_set(self):
        """A failed parse (score=None, parse_success=False) is still 'complete'."""
        p = _make_pending()
        p.judge_score = None
        p.judge_parse_success = False
        assert p.is_complete() is True
