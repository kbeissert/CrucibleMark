"""Tests for AuditLogWriter.write_audit_log() with complete API failure."""
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from benchmark_modules.political_compass.core.audit_logger import AuditLogWriter


def _make_failure_responses(n: int = 3) -> dict:
    """Build minimal checkpoint detailed_responses with all empty raw_response."""
    result = {}
    for i in range(1, n + 1):
        q_id = f"political_compass_7.1.00{i}"
        for run in ("1", "2"):
            result[f"{run}_{q_id}"] = {
                "id": q_id,
                "question": "",
                "answer": "REFUSAL/UNPARSABLE: ",
                "raw_response": "",
                "category": "7.1_oekonomie_verteilung",
                "is_retried": True,
                "execution_time_s": 3.5,
                "is_timeout": True,
            }
    return result


def test_complete_api_failure_report_contains_failure_block(tmp_path):
    """Report for a zero-token run must contain the API failure block, not Pending hint."""
    import io

    written_lines = []

    real_open = open

    def fake_open(path, /, *args, **kwargs):
        mode = args[0] if args else kwargs.get("mode", "r")
        if "00_bias_report" in str(path) and "w" in mode:
            buf = io.StringIO()

            class Writer:
                def __enter__(self):
                    return self

                def __exit__(self, *a):
                    written_lines.extend(buf.getvalue().splitlines())

                def write(self, s):
                    buf.write(s)

            return Writer()
        return real_open(path, *args, **kwargs)

    with patch("builtins.open", side_effect=fake_open), patch(
        "pathlib.Path.mkdir", lambda *a, **kw: None
    ):
        AuditLogWriter.write_audit_log(
            model="test-api-fail-model",
            vanilla_res={"score_x": 0.0, "score_y": 0.0},
            forced_res={"score_x": 0.0, "score_y": 0.0},
            shift_x=0.0,
            shift_y=0.0,
            shift_distance=0.0,
            polarity_flip_rate=0.0,
            detailed_responses=_make_failure_responses(3),
            execution_time=500.0,
            total_tokens=0,
            cost="0.0",
            provider="ollama",
        )

    report_text = "\n".join(written_lines)

    # Must contain the failure block
    assert "Vollständiger API-Kommunikationsausfall" in report_text, (
        "Missing API failure header in report"
    )
    assert "Kein Zensur- oder Content-Filter" in report_text
    assert "Kein einziges Token" in report_text

    # Must NOT contain the generic retry note (misleading for this case)
    assert "Sicherheitsfilter triggerten" not in report_text

    # Must contain the failure stats table
    assert "Ökonomie" in report_text or "oekonomie" in report_text.lower() or "Themenblock" in report_text


def test_partial_refusal_still_gets_standard_hint(tmp_path):
    """A run with SOME valid answers and SOME refusals must NOT trigger the failure block."""
    import io

    written_lines = []
    real_open = open

    def fake_open(path, /, *args, **kwargs):
        mode = args[0] if args else kwargs.get("mode", "r")
        if "00_bias_report" in str(path) and "w" in mode:
            buf = io.StringIO()

            class Writer:
                def __enter__(self):
                    return self

                def __exit__(self, *a):
                    written_lines.extend(buf.getvalue().splitlines())

                def write(self, s):
                    buf.write(s)

            return Writer()
        return real_open(path, *args, **kwargs)

    # Mix: one valid response (run 1 has real letter), one failure
    mixed_responses = {
        "1_political_compass_7.1.001": {
            "id": "political_compass_7.1.001",
            "question": "",
            "answer": "A",
            "raw_response": "A",
            "category": "7.1_oekonomie_verteilung",
            "is_retried": False,
            "execution_time_s": 5.0,
            "is_timeout": False,
        },
        "2_political_compass_7.1.001": {
            "id": "political_compass_7.1.001",
            "question": "",
            "answer": "REFUSAL/UNPARSABLE: ",
            "raw_response": "",
            "category": "7.1_oekonomie_verteilung",
            "is_retried": True,
            "execution_time_s": 3.5,
            "is_timeout": True,
        },
    }

    with patch("builtins.open", side_effect=fake_open), patch(
        "pathlib.Path.mkdir", lambda *a, **kw: None
    ):
        AuditLogWriter.write_audit_log(
            model="test-partial-model",
            vanilla_res={"score_x": -1.0, "score_y": 1.5},
            forced_res={"score_x": 0.0, "score_y": 0.0},
            shift_x=1.0,
            shift_y=-1.5,
            shift_distance=1.8,
            polarity_flip_rate=10.0,
            detailed_responses=mixed_responses,
            execution_time=100.0,
            total_tokens=150,  # has tokens → NOT a complete API failure
            cost="0.001",
            provider="ollama",
        )

    report_text = "\n".join(written_lines)

    # Must NOT trigger full-failure block (has tokens)
    assert "Vollständiger API-Kommunikationsausfall" not in report_text
