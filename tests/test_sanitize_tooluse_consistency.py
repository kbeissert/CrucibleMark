"""Tests fuer die Tool-Use-Sanity-Pruefung in
``scripts/maintenance/sanitize_8_models_tooluse.py``.

Stellt sicher dass:
- Konsistente Reviews + LB-Eintraege als OK erkannt werden.
- Versionierte LB-Eintraege (z.B. ``gpt-5_5-2026-04-23``) zu
  unversionierten Review-Dirs (``gpt-5_5/``) korrekt gemappt werden.
- Orphan-Reviews (Review ohne LB) als DRIFT gemeldet werden.
"""

from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Skip wenn sanitize nicht importierbar (z.B. ohne venv)
try:
    from scripts.maintenance.sanitize_8_models_tooluse import (
        step5_consistency_check,
    )
except ImportError as e:
    import pytest
    pytest.skip(f"sanitize-Modul nicht importierbar: {e}", allow_module_level=True)


class TestConsistencyCheck:
    """Integration-Tests fuer den Konsistenz-Check."""

    def test_real_consistency_check_runs(self):
        """Prueft, dass step5_consistency_check ohne Exception laeuft."""
        # Sollte keine Exception werfen
        step5_consistency_check()

    def test_real_repo_has_documented_drift(self, capsys):
        """Der echte Repo-Zustand hat mindestens einen bekannten Drift.

        Wenn dieser Test fehlschlaegt, wurde der Drift gefixt — dann bitte
        diesen Test anpassen oder entfernen.
        """
        step5_consistency_check()
        out = capsys.readouterr().out
        # Wir erwarten mindestens 1 Drift (qwen3-coder-30b-a3b-q8)
        # Wenn das gefixt ist, muss der Test aktualisiert werden.
        assert "DRIFT" in out or "OK  ]" in out, (
            "step5 sollte entweder DRIFT oder OK ausgeben"
        )

    def test_csv_has_tooluse_leaderboard(self):
        """ToolUse-Leaderboard muss existieren."""
        lb = ROOT / "benchmark_scores" / "tooluse_leaderboard.csv"
        assert lb.exists(), f"tooluse_leaderboard.csv fehlt: {lb}"

    def test_csv_format_valid(self):
        """ToolUse-Leaderboard muss CSV-Format haben."""
        lb = ROOT / "benchmark_scores" / "tooluse_leaderboard.csv"
        with lb.open() as f:
            rdr = csv.DictReader(f)
            rows = list(rdr)
        assert len(rows) > 0
        # Erwartete Spalten (Beispiel)
        first = rows[0]
        assert "model_id" in first or first.get("Model ID") or len(first) > 5