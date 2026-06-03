from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import run_score_benchmark as score_worker


class _DummyCfg:
    def __init__(self) -> None:
        self.config = {
            "modules": {
                "code_quality": {"enabled": True},
                "cli_benchmark": {"enabled": True},
                "political_compass": {"enabled": True},
                "tooluse": {"enabled": True},
            },
            "providers": {"local": {}, "commercial": {}},
        }


def test_single_model_runs_score_modules_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def _fake_run(cmd, cwd=None, env=None, check=False):
        calls.append(cmd)

        class _R:
            returncode = 0

        return _R()

    monkeypatch.setattr(score_worker.subprocess, "run", _fake_run)
    monkeypatch.setattr(score_worker, "ConfigValidator", _DummyCfg)

    summary = tmp_path / "score_single_summary.json"
    argv = [
        "run_score_benchmark.py",
        "--model",
        "gemma3:12b",
        "--summary-json",
        str(summary),
    ]
    monkeypatch.setattr(score_worker.sys, "argv", argv)

    with pytest.raises(SystemExit) as exc:
        score_worker.main()

    assert exc.value.code == 0
    payload = json.loads(summary.read_text(encoding="utf-8"))
    assert payload["schema"] == "crucible.runner_summary.v1"
    assert payload["runner"] == "score_benchmark"
    assert payload["status"] == "success"
    assert payload["tasks_total"] == 2

    assert len(calls) == 2
    cmd_blob = " ".join(" ".join(cmd) for cmd in calls)
    assert "--module code_quality" in cmd_blob
    assert "--module cli_benchmark" in cmd_blob
    assert "political_compass" not in cmd_blob
    assert "--module tooluse" not in cmd_blob


def test_models_list_partial_status(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    count = {"n": 0}

    def _fake_run(cmd, cwd=None, env=None, check=False):
        count["n"] += 1

        class _R:
            returncode = 0 if count["n"] == 1 else 1

        return _R()

    monkeypatch.setattr(score_worker.subprocess, "run", _fake_run)
    monkeypatch.setattr(score_worker, "ConfigValidator", _DummyCfg)

    summary = tmp_path / "score_models_summary.json"
    argv = [
        "run_score_benchmark.py",
        "--models",
        "m1,m2",
        "--modules",
        "code_quality",
        "--summary-json",
        str(summary),
    ]
    monkeypatch.setattr(score_worker.sys, "argv", argv)

    with pytest.raises(SystemExit) as exc:
        score_worker.main()

    assert exc.value.code == 1
    payload = json.loads(summary.read_text(encoding="utf-8"))
    assert payload["status"] == "partial"
    assert payload["tasks_total"] == 2
    assert payload["tasks_successful"] == 1
    assert payload["tasks_failed"] == 1
    assert payload["failed_tasks"] == [{"model": "m2", "module": "code_quality"}]
