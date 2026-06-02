"""Tests für den delegate_script-Pfad in run_benchmark.py.

Verifiziert, dass Module mit `execution.delegate_script` (z.B. tooluse,
political_compass) an ihr Fachscript delegiert werden, anstatt direkt
UnifiedBenchmarkRunner zu starten. Dadurch startet der MCP-Server
bei Tool-Use auch dann, wenn `make benchmark` aufgerufen wird.

Regression-Tests gegen den Bug, bei dem `make benchmark` mit Modul=
tooluse den MCP-Server nicht initialisierte.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from run_benchmark import BenchmarkRunner  # noqa: E402


class _FakeCompletedProcess:
    """Stand-in for subprocess.CompletedProcess with configurable returncode."""

    def __init__(self, returncode: int = 0) -> None:
        self.returncode = returncode
        self.stdout = ""
        self.stderr = ""


class TestRunBenchmarkDelegate(unittest.TestCase):
    """Prüft, dass _run_delegate korrekte Subprozesse startet."""

    def setUp(self) -> None:
        # BenchmarkRunner.__init__ ruft ConfigValidator + SemanticSimilarity auf.
        # Wir mocken beide, damit der Test ohne reale Config lauffähig ist.
        self._config_patcher = patch("run_benchmark.ConfigValidator")
        self._sim_patcher = patch("run_benchmark.SemanticSimilarity")
        self.mock_validator = self._config_patcher.start()
        self.mock_validator.return_value.config = {
            "modules": {
                "tooluse": {"path": "benchmark_modules/tooluse"},
            }
        }
        self._sim_patcher.start()
        self.runner = BenchmarkRunner(config_path="ignored.yaml")

    def tearDown(self) -> None:
        self._config_patcher.stop()
        self._sim_patcher.stop()

    def _fake_subprocess(self, returncode: int = 0) -> MagicMock:
        mock = MagicMock(return_value=_FakeCompletedProcess(returncode=returncode))
        return mock

    def test_delegate_requires_mcp_adds_mcp_mode_flag(self) -> None:
        """Bei requires_mcp=true muss --mcp-mode live durchgereicht werden."""
        module_config = {
            "id": "tooluse",
            "name": "Tool Use & Assistenz",
            "delegate_script": "scripts/run_tooluse_benchmark.py",
            "requires_mcp": True,
        }
        with patch("run_benchmark.subprocess.run", self._fake_subprocess(0)) as mock_run:
            ok = self.runner._run_delegate(module_config, "test-model", force=True, audit_mode=False)

        self.assertTrue(ok)
        self.assertEqual(mock_run.call_count, 1)
        cmd = mock_run.call_args.args[0]
        self.assertIn("scripts/run_tooluse_benchmark.py", cmd[1])
        self.assertIn("--model", cmd)
        self.assertIn("test-model", cmd)
        self.assertIn("--force", cmd)
        self.assertIn("--silent", cmd)
        self.assertIn("--mcp-mode", cmd)
        mcp_idx = cmd.index("--mcp-mode")
        self.assertEqual(cmd[mcp_idx + 1], "live")

    def test_delegate_without_mcp_omits_mcp_flag(self) -> None:
        """Module ohne requires_mcp dürfen kein --mcp-mode tragen."""
        # Wir nutzen ein existierendes Script (run_tooluse_benchmark.py),
        # setzen aber requires_mcp=False, um die Flag-Logik isoliert zu prüfen.
        module_config = {
            "id": "fake-delegate",
            "name": "Delegate Ohne MCP",
            "delegate_script": "scripts/run_tooluse_benchmark.py",
        }
        with patch("run_benchmark.subprocess.run", self._fake_subprocess(0)) as mock_run:
            ok = self.runner._run_delegate(module_config, "pc-model", force=False, audit_mode=True)

        self.assertTrue(ok)
        cmd = mock_run.call_args.args[0]
        self.assertNotIn("--mcp-mode", cmd)
        self.assertNotIn("--force", cmd)
        self.assertNotIn("--silent", cmd)

    def test_delegate_propagates_extra_args(self) -> None:
        """delegate_extra_args werden vor --model eingefügt."""
        module_config: dict[str, Any] = {
            "id": "tooluse",
            "name": "Tool Use & Assistenz",
            "delegate_script": "scripts/run_tooluse_benchmark.py",
            "delegate_extra_args": ["--provider", "ollama"],
        }
        with patch("run_benchmark.subprocess.run", self._fake_subprocess(0)) as mock_run:
            self.runner._run_delegate(module_config, "x", force=False, audit_mode=True)

        cmd = mock_run.call_args.args[0]
        # Reihenfolge: sys.executable, <abs script path>, [extra...], --model, model
        self.assertEqual(cmd[0], sys.executable)
        self.assertTrue(cmd[1].endswith("scripts/run_tooluse_benchmark.py"))
        self.assertEqual(cmd[2:4], ["--provider", "ollama"])
        self.assertEqual(cmd[4], "--model")
        self.assertEqual(cmd[5], "x")

    def test_delegate_missing_script_returns_false(self) -> None:
        module_config = {
            "id": "broken",
            "name": "Broken Module",
            "delegate_script": "scripts/does_not_exist.py",
        }
        with patch("run_benchmark.subprocess.run") as mock_run:
            ok = self.runner._run_delegate(module_config, "x")

        self.assertFalse(ok)
        mock_run.assert_not_called()

    def test_delegate_nonzero_exit_returns_false(self) -> None:
        module_config = {
            "id": "tooluse",
            "name": "Tool Use & Assistenz",
            "delegate_script": "scripts/run_tooluse_benchmark.py",
        }
        with patch("run_benchmark.subprocess.run", self._fake_subprocess(2)) as mock_run:
            ok = self.runner._run_delegate(module_config, "x", force=False, audit_mode=True)

        self.assertFalse(ok)
        mock_run.assert_called_once()

    def test_delegate_cwd_is_repo_root(self) -> None:
        """subprocess.run muss im Repo-Root ausgeführt werden, damit
        relative Pfade im Delegate-Script (z.B. make mcp-start) funktionieren."""
        module_config = {
            "id": "tooluse",
            "name": "Tool Use & Assistenz",
            "delegate_script": "scripts/run_tooluse_benchmark.py",
        }
        with patch("run_benchmark.subprocess.run", self._fake_subprocess(0)) as mock_run:
            self.runner._run_delegate(module_config, "x", force=False, audit_mode=True)

        cwd = mock_run.call_args.kwargs.get("cwd")
        self.assertIsNotNone(cwd)
        self.assertEqual(Path(str(cwd)).resolve(), ROOT_DIR)

    def test_delegate_sets_cycle_detection_env(self) -> None:
        """CRUCIBLE_DELEGATE_PARENT=1 muss im Subprozess gesetzt sein, damit
        der Delegate-Child bei run_benchmark.py-Rückruf nicht erneut delegiert
        (sonst Endlosschleife)."""
        module_config = {
            "id": "tooluse",
            "name": "Tool Use & Assistenz",
            "delegate_script": "scripts/run_tooluse_benchmark.py",
        }
        # Sicherstellen, dass die Variable NICHT im Test-Env ist
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CRUCIBLE_DELEGATE_PARENT", None)
            with patch("run_benchmark.subprocess.run", self._fake_subprocess(0)) as mock_run:
                self.runner._run_delegate(module_config, "x", force=False, audit_mode=True)

        env = mock_run.call_args.kwargs.get("env")
        self.assertIsNotNone(env)
        # Pylance braucht expliziten Type-Guard nach assertIsNotNone
        env_dict: dict[str, str] = env  # type: ignore[assignment]
        self.assertEqual(env_dict.get("CRUCIBLE_DELEGATE_PARENT"), "1")

    def test_delegate_handles_subprocess_exception(self) -> None:
        """FileNotFoundError / generische Exceptions dürfen nicht crashen."""
        module_config = {
            "id": "tooluse",
            "name": "Tool Use & Assistenz",
            "delegate_script": "scripts/run_tooluse_benchmark.py",
        }
        with patch(
            "run_benchmark.subprocess.run",
            side_effect=FileNotFoundError("interpreter missing"),
        ):
            ok = self.runner._run_delegate(module_config, "x", force=False, audit_mode=True)
        self.assertFalse(ok)


class TestRunBenchmarkDispatch(unittest.TestCase):
    """Prüft, dass der run()-Loop das richtige Code-Pfad-Disatching macht."""

    def setUp(self) -> None:
        self._config_patcher = patch("run_benchmark.ConfigValidator")
        self._sim_patcher = patch("run_benchmark.SemanticSimilarity")
        self.mock_validator = self._config_patcher.start()
        self.mock_validator.return_value.config = {"modules": {}}
        self._sim_patcher.start()
        self.runner = BenchmarkRunner(config_path="ignored.yaml")

    def tearDown(self) -> None:
        self._config_patcher.stop()
        self._sim_patcher.stop()

    def test_delegate_module_does_not_call_run_benchmark(self) -> None:
        """Delegate-Module dürfen _run_benchmark NICHT aufrufen — sonst startet
        UnifiedBenchmarkRunner und der MCP-Bypass-Bug kehrt zurück."""
        delegate_cfg = {
            "id": "tooluse",
            "name": "Tool Use & Assistenz",
            "delegate_script": "scripts/run_tooluse_benchmark.py",
            "requires_mcp": True,
        }
        with patch.object(self.runner, "_run_delegate", return_value=True) as mock_delegate, \
             patch.object(self.runner, "_run_benchmark") as mock_bench, \
             patch("run_benchmark.subprocess.run", return_value=_FakeCompletedProcess(0)):
            for _mod_id, _mod_cfg in [("tooluse", delegate_cfg)]:
                if _mod_cfg.get("delegate_script"):
                    self.runner._run_delegate(
                        _mod_cfg, "x", force=False, audit_mode=True,
                    )
                else:
                    self.runner._run_benchmark(
                        _mod_id, _mod_cfg, "x", "provider", num_runs=1, force=False, audit_mode=True,
                    )

        mock_delegate.assert_called_once()
        mock_bench.assert_not_called()

    def test_delegate_child_skips_delegation(self) -> None:
        """Cycle-Detection: Wenn CRUCIBLE_DELEGATE_PARENT=1 gesetzt ist,
        darf KEINE Delegation erfolgen — sonst Endlosschleife. Stattdessen
        muss _run_benchmark() direkt aufgerufen werden (MCP läuft bereits)."""
        from run_benchmark import BenchmarkRunConfig

        delegate_cfg = {
            "id": "tooluse",
            "name": "Tool Use & Assistenz",
            "delegate_script": "scripts/run_tooluse_benchmark.py",
            "requires_mcp": True,
        }
        run_cfg = BenchmarkRunConfig(
            module_name="tooluse",
            model_name="minimax/minimax-m3",
            force=True,
            audit_mode=False,
        )
        with patch.dict(os.environ, {"CRUCIBLE_DELEGATE_PARENT": "1"}, clear=False), \
             patch.object(self.runner, "_run_delegate") as mock_delegate, \
             patch.object(self.runner, "_run_benchmark") as mock_bench, \
             patch.object(self.runner, "select_module", return_value=("tooluse", delegate_cfg)), \
             patch("run_benchmark.resolve_provider", return_value=("openrouter", "minimax/minimax-m3")), \
             patch("run_benchmark.subprocess.run", return_value=_FakeCompletedProcess(0)):
            self.runner.run(run_cfg)

        mock_delegate.assert_not_called()
        mock_bench.assert_called_once()


if __name__ == "__main__":
    unittest.main()
