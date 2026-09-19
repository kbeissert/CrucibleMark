"""
Tests für den Observability-Fix im unified_runner (Session 110).

Altlast (Session 109, AGENTS-Constraint 2026-09-19): ``_execute_test_with_timing``
fängt eine Exception ab und liefert ``(error_result_mit_str(e), None)`` — aber
``_process_single_test`` überschrieb dieses Error-Result im
``test_instance is None``-Zweig mit dem generischen „Test execution failed".
Die echte Meldung (z. B. die Pydantic-ValueError-Meldung der Re-Ask-Regression)
war dadurch in der CSV unsichtbar und kostete Debugging-Zeit.

SSoT: ``scripts/core/unified_runner.py::_process_single_test``.
"""

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.core import unified_runner as ur  # noqa: E402
from scripts.core.unified_runner import UnifiedBenchmarkRunner  # noqa: E402


def _runner_with_stubbed_execution(
    monkeypatch: pytest.MonkeyPatch, execute_result: Any
) -> UnifiedBenchmarkRunner:
    """Runner-Stub: Vorstufen von _process_single_test neutralisiert."""
    runner = object.__new__(UnifiedBenchmarkRunner)
    runner.force = True  # Cache-Lookup skipped ohne _get_existing_for_model-Zugriff
    monkeypatch.setattr(
        ur, "load_asset_yaml", lambda _p: {"metadata": {"id": "ux_writing_002"}},
    )
    monkeypatch.setattr(
        runner, "_ensure_llamacpp_server", lambda *a, **k: None,
    )
    monkeypatch.setattr(
        runner, "_execute_test_with_timing", lambda *a, **k: execute_result,
    )
    return runner


def test_real_exception_message_survives(monkeypatch, tmp_path):
    """Exception-Pfad: das Error-Result mit der echten Meldung (str(e)) wird
    durchgereicht statt mit „Test execution failed" überschrieben."""
    error_result = {
        "status": "error",
        "error_message": "ValueError: exec_result.reasoning_reask is not a valid field",
        "asset_id": "ux_writing_002",
        "model": "m",
        "provider": "vllm_spark",
    }
    runner = _runner_with_stubbed_execution(monkeypatch, (error_result, None))

    result = runner._process_single_test(
        model="m",
        provider="vllm_spark",
        asset_path=tmp_path / "ux_writing_002.yaml",
        benchmark_info={"id": "ux_writing"},
        is_local=True,
    )

    assert result["status"] == "error"
    assert "reasoning_reask" in result["error_message"]
    assert result["error_message"] != "Test execution failed"


def test_generic_fallback_without_error_result(monkeypatch, tmp_path):
    """Defensiver Fallback: ein (exec_result, None)-Ergebnis OHNE Error-Status
    (unerwarteter Zustand) liefert weiterhin die generische Meldung."""
    weird_result = {"status": "ok", "raw_response": "x"}
    runner = _runner_with_stubbed_execution(monkeypatch, (weird_result, None))

    result = runner._process_single_test(
        model="m",
        provider="vllm_spark",
        asset_path=tmp_path / "ux_writing_002.yaml",
        benchmark_info={"id": "ux_writing"},
        is_local=True,
    )

    assert result["status"] == "error"
    assert result["error_message"] == "Test execution failed"


def test_endpoint_conflict_path_unchanged(monkeypatch, tmp_path):
    """Endpoint-Konflikt (exec_result is None) läuft weiterhin in den
    Passthrough-Zweig — Verhalten unverändert zum Stand vor dem Fix."""
    runner = _runner_with_stubbed_execution(monkeypatch, (None, None))
    calls: list = []

    def _capture(asset_id, msg, model="", provider=""):
        calls.append(msg)
        return {"status": "error", "error_message": msg}

    monkeypatch.setattr(runner, "_create_error_result", _capture)

    result = runner._process_single_test(
        model="m",
        provider="vllm_spark",
        asset_path=tmp_path / "ux_writing_002.yaml",
        benchmark_info={"id": "ux_writing"},
        is_local=True,
    )

    assert calls == ["endpoint conflict"]
    assert result["error_message"] == "endpoint conflict"
