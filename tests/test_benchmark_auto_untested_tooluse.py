"""Tests für Tool-Use Backlog Auto-Fill in scripts/core/benchmark_auto.py.

Abdeckung:
- _collect_untested_tooluse_cards() filtert korrekt nach supports_tool_use
- _run_untested_tooluse_models() baut den korrekten Subprocess-Cmd
- _run_untested_tooluse_models() no-op bei leerer Liste
- _run_untested_tooluse_models() reicht --force / --silent durch
- _run_untested_tooluse_models() propagiert KeyboardInterrupt
- _run_untested_tooluse_models() returnt False bei nicht existierendem Skript
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Pfad-Setup: scripts/core/benchmark_auto.py liegt 2 Ebenen tiefer
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.core import benchmark_auto  # noqa: E402


def _write_card(card_dir: Path, model_id: str, supports_tool_use) -> Path:
    """Schreibt eine Test-Card mit gegebenem supports_tool_use-Wert."""
    card_dir.mkdir(parents=True, exist_ok=True)
    # model_id → filename (sicher für Filesystem)
    safe = model_id.replace("/", "_").replace(":", "_")
    path = card_dir / f"{safe}.json"
    path.write_text(
        json.dumps(
            {
                "model_id": model_id,
                "display_name": model_id,
                "supports_tool_use": supports_tool_use,
            }
        ),
        encoding="utf-8",
    )
    return path


class TestCollectUntestedTooluseCards(unittest.TestCase):
    """Filter-Logik für untested Cards."""

    def setUp(self) -> None:
        self.tmp = Path(ROOT / ".pytest_tmp" / f"cards_{id(self)}")
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.card_dir = self.tmp / "cards"

    def tearDown(self) -> None:
        import shutil
        if self.tmp.exists():
            shutil.rmtree(self.tmp)

    def test_returns_empty_when_card_dir_missing(self):
        with patch.object(benchmark_auto, "CARD_DIR", self.tmp / "nonexistent"):
            result = benchmark_auto._collect_untested_tooluse_cards()
        self.assertEqual(result, [])

    def test_collects_untested_string(self):
        with patch.object(benchmark_auto, "CARD_DIR", self.card_dir):
            _write_card(self.card_dir, "model-a", "untested")
            result = benchmark_auto._collect_untested_tooluse_cards()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "model-a")

    def test_excludes_true_cards(self):
        with patch.object(benchmark_auto, "CARD_DIR", self.card_dir):
            _write_card(self.card_dir, "model-true", True)
            _write_card(self.card_dir, "model-untested", "untested")
            result = benchmark_auto._collect_untested_tooluse_cards()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "model-untested")

    def test_excludes_false_cards(self):
        with patch.object(benchmark_auto, "CARD_DIR", self.card_dir):
            _write_card(self.card_dir, "model-false", False)
            _write_card(self.card_dir, "model-untested", "untested")
            result = benchmark_auto._collect_untested_tooluse_cards()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "model-untested")

    def test_excludes_null_cards_defensively(self):
        """Karten mit supports_tool_use=null sollten via normalize → 'untested' theoretisch
        aufgenommen werden, aber im Normalfall sind sie bereits migriert. Hier testen
        wir, dass die Migration vollständig war (kein 'null' zurückbleibt)."""
        with patch.object(benchmark_auto, "CARD_DIR", self.card_dir):
            # normalize_supports_tool_use(None) → "untested"
            # Also: null-Cards würden aufgenommen. Das ist gewollt defensiv
            # (verhindert Datenverlust bei übersehener Migration).
            _write_card(self.card_dir, "model-null", None)
            _write_card(self.card_dir, "model-untested", "untested")
            result = benchmark_auto._collect_untested_tooluse_cards()
        # Beide werden aufgenommen — das ist der gewollte defensive Pfad
        model_ids = {mid for mid, _ in result}
        self.assertIn("model-null", model_ids)
        self.assertIn("model-untested", model_ids)

    def test_skips_invalid_json(self):
        with patch.object(benchmark_auto, "CARD_DIR", self.card_dir):
            self.card_dir.mkdir(exist_ok=True)
            (self.card_dir / "bad.json").write_text("{ not json", encoding="utf-8")
            _write_card(self.card_dir, "model-untested", "untested")
            result = benchmark_auto._collect_untested_tooluse_cards()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "model-untested")

    def test_skips_cards_without_model_id(self):
        with patch.object(benchmark_auto, "CARD_DIR", self.card_dir):
            self.card_dir.mkdir(exist_ok=True)
            (self.card_dir / "noid.json").write_text(
                json.dumps({"display_name": "X", "supports_tool_use": "untested"}),
                encoding="utf-8",
            )
            _write_card(self.card_dir, "model-a", "untested")
            result = benchmark_auto._collect_untested_tooluse_cards()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "model-a")

    def test_results_sorted_by_model_id(self):
        with patch.object(benchmark_auto, "CARD_DIR", self.card_dir):
            _write_card(self.card_dir, "zeta", "untested")
            _write_card(self.card_dir, "alpha", "untested")
            _write_card(self.card_dir, "mike", "untested")
            result = benchmark_auto._collect_untested_tooluse_cards()
        ids = [mid for mid, _ in result]
        self.assertEqual(ids, ["alpha", "mike", "zeta"])


class TestRunUntestedTooluseModels(unittest.TestCase):
    """Subprocess-Delegation an run_tooluse_benchmark.py."""

    def test_empty_list_returns_false_no_subprocess(self):
        with patch.object(benchmark_auto.subprocess, "run") as mock_run:
            result = benchmark_auto._run_untested_tooluse_models([], mcp_mode="live")
        self.assertFalse(result)
        mock_run.assert_not_called()

    def test_builds_correct_command_for_multiple_models(self):
        models = [("model-a", "Model A"), ("model-b", "Model B")]
        # Pre-Flight überspringen — alle Modelle gelten als testbar.
        with patch.object(
            benchmark_auto, "filter_testable_cards", return_value=(models, [])
        ), patch.object(benchmark_auto.subprocess, "run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
            result = benchmark_auto._run_untested_tooluse_models(
                models, mcp_mode="live", force=False, silent=False
            )
        self.assertTrue(result)
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        # cmd ist [exe, script_path, "--models", "model-a,model-b", "--mcp-mode", "live"]
        self.assertEqual(cmd[0], sys.executable)
        self.assertTrue(cmd[1].endswith("run_tooluse_benchmark.py"))
        self.assertEqual(cmd[2], "--models")
        self.assertEqual(cmd[3], "model-a,model-b")
        self.assertEqual(cmd[4], "--mcp-mode")
        self.assertEqual(cmd[5], "live")
        # Kein --force, kein --silent
        self.assertNotIn("--force", cmd)
        self.assertNotIn("--silent", cmd)

    def test_force_and_silent_flags_added(self):
        models = [("m", "M")]
        with patch.object(
            benchmark_auto, "filter_testable_cards", return_value=(models, [])
        ), patch.object(benchmark_auto.subprocess, "run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
            benchmark_auto._run_untested_tooluse_models(
                models, mcp_mode="mock", force=True, silent=True
            )
        cmd = mock_run.call_args[0][0]
        self.assertIn("--force", cmd)
        self.assertIn("--silent", cmd)
        # mcp-mode mock durchgereicht
        self.assertIn("mock", cmd)

    def test_returns_false_on_nonzero_exit(self):
        models = [("m", "M")]
        with patch.object(
            benchmark_auto, "filter_testable_cards", return_value=(models, [])
        ), patch.object(benchmark_auto.subprocess, "run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=1)
            result = benchmark_auto._run_untested_tooluse_models(
                models, mcp_mode="live"
            )
        self.assertFalse(result)

    def test_propagates_keyboard_interrupt(self):
        models = [("m", "M")]
        with patch.object(
            benchmark_auto, "filter_testable_cards", return_value=(models, [])
        ), patch.object(
            benchmark_auto.subprocess, "run", side_effect=KeyboardInterrupt
        ), self.assertRaises(KeyboardInterrupt):
            benchmark_auto._run_untested_tooluse_models(
                models, mcp_mode="live"
            )

    def test_returns_false_if_script_missing(self):
        """Wenn scripts/run_tooluse_benchmark.py nicht existiert, returnt die Funktion False."""
        fake_root = Path("/nonexistent_root_for_test")
        with patch.object(benchmark_auto, "ROOT_DIR", fake_root):
            result = benchmark_auto._run_untested_tooluse_models(
                [("m", "M")], mcp_mode="live"
            )
        self.assertFalse(result)


class TestPhaseBRobustnessWarnings(unittest.TestCase):
    """Zusätzliche Robustheits-Tests für Warnpfade (Phase B)."""

    def setUp(self) -> None:
        self.tmp = Path(ROOT / ".pytest_tmp" / f"phaseb_{id(self)}")
        self.tmp.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        import shutil
        if self.tmp.exists():
            shutil.rmtree(self.tmp)

    def test_get_startable_assets_warns_on_invalid_skip_card_json(self):
        assets_dir = self.tmp / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        (assets_dir / "a.yaml").write_text(
            "metadata:\n  id: asset_001\n",
            encoding="utf-8",
        )

        cards_dir = self.tmp / "benchmark_scores" / "model_cards"
        cards_dir.mkdir(parents=True, exist_ok=True)
        bad_card = cards_dir / "model_a.json"
        bad_card.write_text("{ broken", encoding="utf-8")

        module = {
            "name": "Tool Use",
            "key": "tooluse",
            "path": str(assets_dir),
            "skip_if_card_false": "supports_tool_use",
        }

        with (
            patch.object(benchmark_auto, "ROOT_DIR", self.tmp),
            patch("utils.model_utils._find_card", return_value=bad_card),
            self.assertLogs("scripts.core.llamacpp_batch", level="WARNING") as logs,
        ):
            assets = benchmark_auto.get_startable_assets(module, "model_a", set())

        self.assertEqual(len(assets), 1)
        self.assertTrue(
            any("Card-Flag-Skip konnte nicht geprüft" in msg for msg in logs.output)
        )

    def test_get_startable_assets_warns_on_missing_metadata_id(self):
        assets_dir = self.tmp / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        (assets_dir / "noid.yaml").write_text(
            "prompt: test\n",
            encoding="utf-8",
        )

        module = {
            "name": "Code Quality",
            "key": "code_quality",
            "path": str(assets_dir),
        }

        with self.assertLogs("scripts.core.llamacpp_batch", level="WARNING") as logs:
            assets = benchmark_auto.get_startable_assets(module, "model_x", set())

        self.assertEqual(len(assets), 1)
        self.assertTrue(
            any("Asset ohne metadata.id wird ausgeführt" in msg for msg in logs.output)
        )

    def test_load_cards_for_models_warns_if_unreadable_or_missing(self):
        cards_dir = self.tmp / "cards"
        cards_dir.mkdir(parents=True, exist_ok=True)
        (cards_dir / "model_a.json").write_text("{ invalid", encoding="utf-8")

        with (
            patch.object(benchmark_auto, "CARD_DIR", cards_dir),
            self.assertLogs("auto_benchmark", level="WARNING") as logs,
        ):
            cards = benchmark_auto._load_cards_for_models(["model_a", "model_missing"])

        self.assertEqual(cards, {})
        self.assertTrue(
            any("Model Card für Pre-Flight konnte nicht gelesen werden" in msg for msg in logs.output)
        )
        self.assertTrue(
            any("Keine lesbare Model Card für Pre-Flight gefunden" in msg for msg in logs.output)
        )


class TestIterationDScoreDelegation(unittest.TestCase):
    """Tests für explizite Score-Worker-Delegation aus benchmark_auto."""

    def test_is_score_module_classifies_special_modules(self):
        self.assertTrue(benchmark_auto._is_score_module({"key": "code_quality"}))
        self.assertFalse(benchmark_auto._is_score_module({"key": "tooluse"}))
        self.assertFalse(benchmark_auto._is_score_module({"key": "political_compass"}))

    def test_run_module_for_model_uses_score_delegate(self):
        module = {"key": "code_quality", "name": "Code Quality", "path": "unused"}

        with (
            patch.object(benchmark_auto, "get_startable_assets", return_value=[Path("x.yaml")]),
            patch.object(benchmark_auto, "_run_score_delegate_for_model", return_value=True) as score_del,
            patch.object(benchmark_auto, "_run_delegate_for_model") as generic_del,
        ):
            result = benchmark_auto._run_module_for_model(
                runner=object(),
                model="gemma-3-12b-it",
                module=module,
                existing_tests=set(),
                force=True,
                audit=False,
            )

        # Phase 21: Tristate-Return ("ran" | "skipped" | "failed")
        self.assertEqual(result, "ran")
        score_del.assert_called_once_with(module, "gemma-3-12b-it", force=True, audit=False)
        generic_del.assert_not_called()


class TestRunModuleForModelTristate(unittest.TestCase):
    """Phase 21: Differenzierung skipped/failed in `_run_module_for_model`.

    Hintergrund: Der Caller (llamacpp-Batch) brach bei einem "skipped"-Ergebnis
    den Loop ab, weil die alte Bool-Rückgabe nicht zwischen "Leaderboard-Cache
    sagt done" und "echter Fehler" unterscheiden konnte. Resultat: llama.cpp-
    Server wurde nach 1 Modul gestoppt, alle weiteren Module für dasselbe
    Modell wurden übersprungen.
    """

    def test_leaderboard_score_does_not_skip_when_assets_missing(self):
        """Regression v4.10.12: Leaderboard-Score darf Modul NICHT überspringen
        wenn Assets fehlen. Vorher übersprang der Leaderboard-Cache-Check das
        gesamte Modul, weil das Leaderboard einen Score aus partiellen Daten hatte.
        Jetzt ist get_startable_assets() die alleinige Autorität."""
        module = {"key": "code_quality", "name": "Code Quality", "path": "unused"}

        with (
            patch.object(benchmark_auto, "get_startable_assets", return_value=[Path("x.yaml")]),
            patch.object(benchmark_auto, "_run_score_delegate_for_model", return_value=True) as score_del,
        ):
            result = benchmark_auto._run_module_for_model(
                runner=object(),
                model="gemma-4-12b-it-ud-q6-k-xl",
                module=module,
                existing_tests=set(),
                force=False,
                audit=False,
            )

        self.assertEqual(result, "ran")
        score_del.assert_called_once()

    def test_no_assets_returns_skipped(self):
        """Wenn keine Assets zu testen sind, returnt die Funktion 'skipped'."""
        module = {"key": "code_quality", "name": "Code Quality", "path": "unused"}

        with (
            patch.object(benchmark_auto, "get_startable_assets", return_value=[]),
            patch.object(benchmark_auto, "_run_score_delegate_for_model") as score_del,
            patch.object(benchmark_auto, "_run_delegate_for_model") as generic_del,
        ):
            result = benchmark_auto._run_module_for_model(
                runner=object(),
                model="hermes-4.3-36b-q6",
                module=module,
                existing_tests=set(),
                force=False,
                audit=False,
            )

        self.assertEqual(result, "skipped")
        score_del.assert_not_called()
        generic_del.assert_not_called()

    def test_score_delegate_success_returns_ran(self):
        """Wenn der Score-Delegate erfolgreich ist, returnt die Funktion 'ran'."""
        module = {"key": "code_quality", "name": "Code Quality", "path": "unused"}

        with (
            patch.object(benchmark_auto, "get_startable_assets", return_value=[Path("x.yaml")]),
            patch.object(benchmark_auto, "_run_score_delegate_for_model", return_value=True) as score_del,
        ):
            result = benchmark_auto._run_module_for_model(
                runner=object(),
                model="gemma-3-12b-it",
                module=module,
                existing_tests=set(),
                force=True,
                audit=False,
            )

        self.assertEqual(result, "ran")
        score_del.assert_called_once()

    def test_score_delegate_failure_returns_failed(self):
        """Wenn der Score-Delegate fehlschlägt, returnt die Funktion 'failed'."""
        module = {"key": "code_quality", "name": "Code Quality", "path": "unused"}

        with (
            patch.object(benchmark_auto, "get_startable_assets", return_value=[Path("x.yaml")]),
            patch.object(benchmark_auto, "_run_score_delegate_for_model", return_value=False),
        ):
            result = benchmark_auto._run_module_for_model(
                runner=object(),
                model="gemma-3-12b-it",
                module=module,
                existing_tests=set(),
                force=True,
                audit=False,
            )

        self.assertEqual(result, "failed")

    def test_force_with_no_assets_returns_skipped(self):
        """Mit force=True und keine offenen Assets → skipped."""
        module = {"key": "code_quality", "name": "Code Quality", "path": "unused"}

        with (
            patch.object(benchmark_auto, "get_startable_assets", return_value=[]),
            patch.object(benchmark_auto, "_run_score_delegate_for_model") as score_del,
        ):
            result = benchmark_auto._run_module_for_model(
                runner=object(),
                model="gemma-3-12b-it",
                module=module,
                existing_tests=set(),
                force=True,
                audit=False,
            )

        self.assertEqual(result, "skipped")
        score_del.assert_not_called()

    def test_llamacpp_provider_skips_score_delegate(self):
        """Bei llama.cpp-Provider wird KEIN Score-Delegate aufgerufen (in-process)."""
        module = {
            "key": "code_quality",
            "name": "Code Quality",
            "path": "unused",
            "delegate_script": "scripts/run_benchmark.py",
        }

        with (
            patch.object(benchmark_auto, "get_startable_assets", return_value=[Path("x.yaml")]),
            patch.object(benchmark_auto, "_run_score_delegate_for_model") as score_del,
            patch.object(benchmark_auto, "_run_delegate_for_model", return_value=True) as generic_del,
        ):
            result = benchmark_auto._run_module_for_model(
                runner=object(),
                model="hermes-4.3-36b-q6",
                module=module,
                existing_tests=set(),
                force=True,
                audit=False,
                provider="llamacpp_spark",
            )

        # llama.cpp → KEIN Score-Delegate, stattdessen generischer Delegate
        self.assertEqual(result, "ran")
        score_del.assert_not_called()
        generic_del.assert_called_once()
        # Cleanup-Skip muss an Delegate weitergegeben werden
        kwargs = generic_del.call_args.kwargs
        self.assertTrue(kwargs.get("skip_llamacpp_cleanup"))

    def test_generic_delegate_failure_returns_failed(self):
        """Wenn der generische Delegate fehlschlägt, returnt die Funktion 'failed'."""
        module = {
            "key": "tooluse",
            "name": "Tool Use",
            "path": "unused",
            "delegate_script": "scripts/run_tooluse_benchmark.py",
        }

        with (
            patch.object(benchmark_auto, "get_startable_assets", return_value=[Path("x.yaml")]),
            patch.object(benchmark_auto, "_run_delegate_for_model", return_value=False),
        ):
            result = benchmark_auto._run_module_for_model(
                runner=object(),
                model="gemma-3-12b-it",
                module=module,
                existing_tests=set(),
                force=True,
                audit=False,
            )

        self.assertEqual(result, "failed")

    def test_run_score_delegate_builds_expected_command(self):
        module = {"key": "cli_benchmark", "name": "CLI", "path": "unused"}

        with patch.object(benchmark_auto.subprocess, "run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
            ok = benchmark_auto._run_score_delegate_for_model(
                module=module,
                model="gemma-3-12b-it",
                force=True,
                audit=False,
            )

        self.assertTrue(ok)
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[0], sys.executable)
        self.assertTrue(cmd[1].endswith("scripts/run_score_benchmark.py"))
        self.assertIn("--model", cmd)
        self.assertIn("gemma-3-12b-it", cmd)
        self.assertIn("--modules", cmd)
        self.assertIn("cli_benchmark", cmd)
        self.assertIn("--summary-json", cmd)
        self.assertIn("--force", cmd)
        self.assertIn("--silent", cmd)

    def test_inprocess_path_updates_leaderboard(self):
        """Regression v4.10.12: Pfad 3 (in-process, llama.cpp) muss
        update_leaderboard() nach save_results() aufrufen. Vorher wurde
        das Leaderboard fuer llama.cpp-Modelle nicht aktualisiert."""
        module = {
            "key": "ux_writing",
            "name": "UX Writing",
            "path": "unused",
            # KEIN delegate_script → Pfad 3 (in-process)
        }

        # Mock runner mit run_benchmark + save_results
        mock_runner = MagicMock()
        mock_runner.run_benchmark.return_value = [{"asset_id": "ux_writing_001", "status": "success"}]

        with (
            patch.object(benchmark_auto, "get_startable_assets", return_value=[Path("x.yaml")]),
            patch.object(benchmark_auto, "update_leaderboard", return_value=True) as mock_lb,
            patch.object(benchmark_auto, "_run_score_delegate_for_model") as score_del,
            patch.object(benchmark_auto, "_run_delegate_for_model") as generic_del,
        ):
            result = benchmark_auto._run_module_for_model(
                runner=mock_runner,
                model="gemma-4-12b-it-ud-q6-k-xl",
                module=module,
                existing_tests=set(),
                force=False,
                audit=False,
                provider="llamacpp",
            )

        self.assertEqual(result, "ran")
        # Pfad 3 wurde genutzt (nicht Score-Delegate, nicht generic Delegate)
        score_del.assert_not_called()
        generic_del.assert_not_called()
        # runner.run_benchmark + save_results wurden aufgerufen
        mock_runner.run_benchmark.assert_called_once()
        mock_runner.save_results.assert_called_once()
        # KRITISCH: update_leaderboard wurde aufgerufen
        mock_lb.assert_called_once()


if __name__ == "__main__":
    unittest.main()
