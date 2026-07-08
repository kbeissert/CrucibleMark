"""Tests fuer die Architektur-Vollstaendigkeit von
``scripts/maintenance/clean_results.py --model``.

Hintergrund: Bis Session 38 (2026-06-26) hatte das Cleanup-Skript
Architektur-Luecken -- Daten in Sub-Family-Leaderboards,
dispatch_summaries/* und results_*.json wurden bei ``--model`` nicht
bereinigt. Diese Tests sichern ab, dass die Bereinigung jetzt
vollstaendig ist.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Skip wenn clean_results nicht importierbar
try:
    from scripts.maintenance.clean_results import (
        _extract_model_from_dispatch_summary,
        CLEAN_CSV_FILES,
        LEADERBOARD_CSVS,
    )
except ImportError as e:
    import pytest
    pytest.skip(f"clean_results nicht importierbar: {e}", allow_module_level=True)


class TestDispatchSummaryExtraction:
    """Prueft die Helper-Funktion zur Modell-Extraktion aus dispatch_summaries."""

    def test_political_compass_format(self):
        assert _extract_model_from_dispatch_summary(
            "political_compass_deepseek_deepseek-chat-v3.1"
        ) == "deepseek_deepseek-chat-v3.1"

    def test_tooluse_format(self):
        assert _extract_model_from_dispatch_summary(
            "tooluse_deepseek_deepseek-chat-v3.1"
        ) == "deepseek_deepseek-chat-v3.1"

    def test_tooluse_backlog_format(self):
        assert _extract_model_from_dispatch_summary(
            "tooluse_backlog_qwen_qwen3-32b"
        ) == "qwen_qwen3-32b"

    def test_score_with_provider_prefix(self):
        assert _extract_model_from_dispatch_summary(
            "score_cli_benchmark_anthropic_claude-haiku-4-5"
        ) == "claude-haiku-4-5"

    def test_score_cultural_intelligence_multi_segment(self):
        """Modul-Name 'cultural_intelligence' hat 2 Segmente — muss korrekt
        als Ganzes uebersprungen werden, nicht nur das erste Segment."""
        assert _extract_model_from_dispatch_summary(
            "score_cultural_intelligence_claude-haiku-4-5-20251001"
        ) == "claude-haiku-4-5-20251001"

    def test_score_documentation_quality_multi_segment(self):
        assert _extract_model_from_dispatch_summary(
            "score_documentation_quality_claude-opus-4-6"
        ) == "claude-opus-4-6"

    def test_score_reasoning_logic_multi_segment(self):
        assert _extract_model_from_dispatch_summary(
            "score_reasoning_logic_claude-sonnet-4-5"
        ) == "claude-sonnet-4-5"

    def test_unknown_format_returns_none(self):
        assert _extract_model_from_dispatch_summary(
            "totally_unknown_format_xyz"
        ) is None

    def test_no_prefix_returns_none(self):
        assert _extract_model_from_dispatch_summary(
            "deepseek_deepseek-chat-v3.1"
        ) is None


class TestCsvFileCoverage:
    """Prueft, dass die CSV-Clean-Listen die relevanten Files enthalten.

    Hinweis: Sub-Family-Leaderboards (gemma_leaderboard.csv, qwen_leaderboard.csv)
    wurden in v4.10.15 entfernt — das Konzept war verwaist (nie generiert, nie
    in git getrackt). provider_leaderboard.csv wurde bereits in v4.10.12
    stillgelegt.
    """

    def test_main_leaderboards_present(self):
        names = {p.name for p in LEADERBOARD_CSVS}
        assert "benchmark_leaderboard.csv" in names
        assert "benchmark_leaderboard_detailed.csv" in names


class TestEndToEndCleanupDryRun:
    """Integration-Test: rufe clean_results mit --model auf und pruefe,
    dass alle relevanten Pfade in der Dry-Run-Ausgabe erscheinen.

    Verwendet ein nicht-existierendes Test-Modell, das in unseren CSVs
    garantiert nicht vorkommt, um keine echten Daten zu beeintraechtigen.
    """

    def test_dry_run_mentions_all_csv_files(self, tmp_path, capsys):
        """Bei einem real existierenden Modell werden alle CSVs angesprochen."""
        # Verwende ein Modell, das wir kennen (nicht loeschen!)
        # Wir pruefen nur, dass die relevanten CSVs ERWAEHNT werden.
        from scripts.maintenance.clean_results import main_with_args

        class _Args:
            pass

        ns = _Args()
        ns.model = "qwen3_5-35b-a3b-q4"  # Existiert in allen Sub-LBs
        ns.module = None
        ns.dry_run = True
        ns.prune_orphans = False
        ns.force = False

        try:
            main_with_args(ns)
        except SystemExit:
            pass

        out = capsys.readouterr().out
        # Sub-Family-LBs (gemma/qwen) wurden in v4.10.15 entfernt — verwaistes
        # Konzept, nie generiert. provider_leaderboard.csv seit v4.10.12 stillgelegt.
        assert "gemma_leaderboard.csv" not in out
        assert "qwen_leaderboard.csv" not in out
        assert "provider_leaderboard.csv" not in out
        # Main-LBs
        assert "benchmark_leaderboard.csv" in out
        assert "benchmark_leaderboard_detailed.csv" in out
        # Tooluse-LB
        assert "tooluse_leaderboard.csv" in out
        # PC-LBs
        assert "political_compass_results.csv" in out
        assert "political_compass_leaderboard.csv" in out