from __future__ import annotations

import contextlib
import json
from pathlib import Path
from typing import Any

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

    def _fake_run(cmd, **kwargs):
        calls.append(cmd)

        class _R:
            returncode = 0
            stderr = ""
            stdout = ""

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

    # Nur die Benchmark-Subprozess-Aufrufe zählen; update_leaderboard()
    # startet einen weiteren Subprozess, der hier nicht zählt.
    benchmark_calls = [cmd for cmd in calls if any("run_benchmark.py" in c for c in cmd)]
    assert len(benchmark_calls) == 2
    cmd_blob = " ".join(" ".join(cmd) for cmd in benchmark_calls)
    assert "--module code_quality" in cmd_blob
    assert "--module cli_benchmark" in cmd_blob
    assert "political_compass" not in cmd_blob
    assert "--module tooluse" not in cmd_blob


def test_models_list_partial_status(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    count = {"n": 0}

    def _fake_run(cmd, **kwargs):
        count["n"] += 1

        class _R:
            returncode = 0 if count["n"] == 1 else 1
            stderr = ""
            stdout = ""

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


class _FakeInprocessRunner:
    """UnifiedBenchmarkRunner-Stand-in für den llama.cpp-In-Process-Pfad."""

    def __init__(self) -> None:
        self.save_calls: list[list[str]] = []

    def run_benchmark(self, **kwargs: Any) -> list[str]:
        return ["result"]

    def save_results(self, results: list[str]) -> None:
        self.save_calls.append(results)


def test_inprocess_llamacpp_updates_leaderboard_per_module(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Lücke 1: Der llama.cpp-In-Process-Pfad muss das Leaderboard nach
    JEDEM Modul aktualisieren (SSoT-Parität mit benchmark_auto.py Pfad 3
    und run_benchmark.py) — nicht erst einmal am Ende des Worker-Laufs."""
    modules = [
        {"key": "code_quality", "name": "Code Quality",
         "module_path": "benchmark_modules/code_quality"},
        {"key": "cli_benchmark", "name": "CLI",
         "module_path": "benchmark_modules/cli_benchmark"},
    ]
    fake_runner = _FakeInprocessRunner()

    @contextlib.contextmanager
    def _fake_session(*args: Any, **kwargs: Any):
        yield None

    config = {
        "providers": {"local": {"llamacpp": {"name": "Fake llama.cpp"}}},
        "output": {"local_models_csv": str(tmp_path / "local.csv")},
    }

    monkeypatch.setattr(score_worker, "load_modules_for_keys", lambda cfg, keys: modules)
    monkeypatch.setattr(score_worker, "get_existing_results", lambda path, force: set())
    monkeypatch.setattr(score_worker, "llamacpp_model_session", _fake_session)
    monkeypatch.setattr(score_worker, "UnifiedBenchmarkRunner", lambda **kwargs: fake_runner)
    monkeypatch.setattr(score_worker, "get_startable_assets", lambda *args, **kwargs: ["asset_001"])
    monkeypatch.setattr(score_worker.time, "sleep", lambda seconds: None)
    monkeypatch.setattr("utils.module_registry.load_module_config", lambda path: {})

    leaderboard_calls: list[Path] = []
    monkeypatch.setattr(
        score_worker, "update_leaderboard",
        lambda root: leaderboard_calls.append(root),
    )

    results = score_worker._run_modules_inprocess_llamacpp(
        model_id="gemma3:12b",
        provider_key="llamacpp",
        module_keys=["code_quality", "cli_benchmark"],
        force=False,
        silent=True,
        config=config,
    )

    assert results == {"code_quality": True, "cli_benchmark": True}
    assert len(fake_runner.save_calls) == 2
    # Ein Leaderboard-Update pro abgeschlossenem Modul — nicht erst am Batch-Ende.
    assert len(leaderboard_calls) == 2
    assert all(call == score_worker.ROOT_DIR for call in leaderboard_calls)
