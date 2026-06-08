from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import run_political_compass_benchmark as pc_worker


class _DummyCfg:
    def __init__(self) -> None:
        self.config = {"providers": {"local": {}, "commercial": {}}}


def test_single_model_writes_summary_and_sets_cycle_guard(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    def _fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, "kwargs": kwargs})

        class _R:
            returncode = 0
            stderr = ""
            stdout = ""

        return _R()

    monkeypatch.setattr(pc_worker.subprocess, "run", _fake_run)
    monkeypatch.setattr(pc_worker, "ConfigValidator", _DummyCfg)

    summary = tmp_path / "pc_single_summary.json"
    argv = [
        "run_political_compass_benchmark.py",
        "--model",
        "gemma3:12b",
        "--summary-json",
        str(summary),
    ]
    monkeypatch.setattr(pc_worker.sys, "argv", argv)

    with pytest.raises(SystemExit) as exc:
        pc_worker.main()

    assert exc.value.code == 0
    assert summary.exists()

    payload = json.loads(summary.read_text(encoding="utf-8"))
    assert payload["schema"] == "crucible.runner_summary.v1"
    assert payload["runner"] == "political_compass"
    assert payload["status"] == "success"
    assert payload["mode"] == "single"

    # Der erste subprocess-Aufruf ist der Benchmark-Delegate; nachgelagerte
    # Aufrufe (z.B. update_leaderboard) interessieren hier nicht.
    assert calls, "Es wurde kein subprocess-Aufruf registriert"
    first = calls[0]
    cmd = first["cmd"]
    assert isinstance(cmd, list)
    assert "run_benchmark.py" in cmd
    assert "--module" in cmd
    assert "political_compass" in cmd
    assert "--model" in cmd
    assert "gemma3:12b" in cmd

    kwargs = first["kwargs"]
    assert isinstance(kwargs, dict)
    env = kwargs.get("env")
    assert isinstance(env, dict)
    assert env.get("CRUCIBLE_DELEGATE_PARENT") == "1"


def test_models_list_partial_status(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = {"n": 0}

    def _fake_run(cmd, **kwargs):
        calls["n"] += 1

        class _R:
            returncode = 0 if calls["n"] == 1 else 1
            stderr = ""
            stdout = ""

        return _R()

    monkeypatch.setattr(pc_worker.subprocess, "run", _fake_run)
    monkeypatch.setattr(pc_worker, "ConfigValidator", _DummyCfg)

    summary = tmp_path / "pc_models_summary.json"
    argv = [
        "run_political_compass_benchmark.py",
        "--models",
        "m1,m2",
        "--summary-json",
        str(summary),
    ]
    monkeypatch.setattr(pc_worker.sys, "argv", argv)

    with pytest.raises(SystemExit) as exc:
        pc_worker.main()

    assert exc.value.code == 1
    payload = json.loads(summary.read_text(encoding="utf-8"))
    assert payload["status"] == "partial"
    assert payload["models_total"] == 2
    assert payload["models_successful"] == 1
    assert payload["models_failed"] == 1
    assert payload["failed_model_ids"] == ["m2"]
