"""Regressionstests gegen den Fall gemini-2.5-pro (2026-09-03).

Ein fehlgeschlagener PC-Retest (158/158 Antworten unparsebar durch API-Ausfall)
aggregierte still auf (0.0, 0.0), persistierte status "success" und überschrieb
per Upsert die valide Leaderboard-Zeile — das Modell erschien auf der Web-Karte
exakt in der Kompass-Mitte. Guards:

1. io_manager.save_leaderboard_csv: (0,0) + 0 Tokens (API-Ausfall) → kein Upsert;
   (0,0) + Tokens > 0 (echte Zensur) → Upsert bleibt erhalten (Skip-Logik).
2. PoliticalCompassHandler.handle_results: status "error" → nur Lauf-JSON,
   keine CSV-/Leaderboard-/Review-Persistenz.
3. web_export.loader._build_pc_lookups: degenerate Zeile überschattet bei
   Key-Kollision keinen validen Eintrag.
"""

from __future__ import annotations

import csv
import types

import pandas as pd
import pytest


def _minimal_report(total_tokens: int) -> dict:
    """Report mit degenerierten (0,0)-Koordinaten, variierbarer Tokenzahl."""
    return {
        "model": "testmodel-degenerate",
        "provider": "google",
        "model_version": "1.0",
        "status": "success",
        "coordinates": {"x": 0.0, "y": 0.0},
        "archetype": None,
        "shift": {"x": 0.0, "y": 0.0, "distance": 0.0, "polarity_flip_rate": 0.0},
        "statistics": {"total_tokens": total_tokens},
        "runs": {
            "vanilla": {"coordinates": {"x": 0.0, "y": 0.0}, "archetype": {}},
            "forced": {"coordinates": {"x": 0.0, "y": 0.0}, "archetype": {}},
        },
        "is_retest": False,
    }


class TestLeaderboardDegenerateGuard:

    def test_api_failure_zero_tokens_skips_upsert(self, tmp_path):
        """Alle Koordinaten 0.0 UND 0 Tokens → kein Leaderboard-Write."""
        from benchmark_modules.political_compass.core.io_manager import (
            PoliticalCompassResultManager,
        )

        PoliticalCompassResultManager.save_leaderboard_csv(
            _minimal_report(total_tokens=0), tmp_path,
        )
        assert not (tmp_path / "political_compass_leaderboard.csv").exists()

    def test_censorship_with_tokens_still_writes_row(self, tmp_path):
        """Alle Koordinaten 0.0 bei Tokens > 0 (echte Zensur) → Zeile bleibt
        erwünscht (Skip-Logik soll keinen Re-Run triggern)."""
        from benchmark_modules.political_compass.core.io_manager import (
            PoliticalCompassResultManager,
        )

        PoliticalCompassResultManager.save_leaderboard_csv(
            _minimal_report(total_tokens=12345), tmp_path,
        )
        csv_path = tmp_path / "political_compass_leaderboard.csv"
        assert csv_path.exists()
        rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
        assert [r["model"] for r in rows] == ["testmodel-degenerate"]


class TestHandlerErrorGuard:

    def test_error_status_persists_json_only(self, monkeypatch, tmp_path):
        """status 'error' → save_json zur Diagnose, aber keine CSV-Writes,
        keine Derivate, kein Anomaly-Trigger."""
        from utils.scoring import political_compass_handler as pch

        calls: list[str] = []
        monkeypatch.setattr(
            pch.PCResultManager, "save_json",
            lambda report, d: calls.append("save_json"),
        )
        monkeypatch.setattr(
            pch.PCResultManager, "print_summary",
            lambda report: calls.append("print_summary"),
        )
        monkeypatch.setattr(
            pch.PoliticalCompassHandler, "update_results_csv",
            lambda *a, **k: calls.append("update_results_csv"),
        )
        monkeypatch.setattr(
            pch.PoliticalCompassHandler, "_generate_derivatives",
            lambda *a, **k: calls.append("derivatives"),
        )
        monkeypatch.chdir(tmp_path)

        report = _minimal_report(total_tokens=0)
        report["status"] = "error"
        test_instance = types.SimpleNamespace(config={}, verification_mode=False)
        pch.PoliticalCompassHandler.handle_results(
            "testmodel-degenerate", report, "1.0", test_instance,
            provider_type="google",
        )

        assert calls == ["save_json"]


class TestWebExportLookupDegenerateRule:

    @staticmethod
    def _lb_df() -> pd.DataFrame:
        # valide Zeile zuerst, degenerate Kollision zuletzt (Upsert-Reihenfolge
        # wie im Fehlerfall: letzter Write = kaputter Retest)
        return pd.DataFrame([
            {
                "model": "gemini-2.5-pro", "timestamp": "2026-04-18 12:13:24",
                "vanilla_x": -2.46, "vanilla_y": 2.66,
                "forced_x": -2.51, "forced_y": 2.19,
            },
            {
                "model": "gemini-2_5-pro", "timestamp": "2026-09-03 18:43:19",
                "vanilla_x": 0.0, "vanilla_y": 0.0,
                "forced_x": 0.0, "forced_y": 0.0,
            },
        ])

    def test_degenerate_row_does_not_shadow_valid(self):
        from scripts.web_export.loader import _build_pc_lookups

        pc_lb_map, pc_lb_slug_map = _build_pc_lookups(self._lb_df())
        for lookup, key in (
            (pc_lb_slug_map, "gemini-2-5-pro"),
        ):
            row = lookup[key]
            assert float(row["vanilla_x"]) == -2.46, (
                f"Degenerate (0,0)-Zeile hat die valide Zeile überschattet (key={key})"
            )

    def test_degenerate_only_still_maps(self):
        """Ohne valide Alternative darf die degenerate Zeile gemappt werden
        (Guard überschattet nur, er filtert nicht raus)."""
        from scripts.web_export.loader import _build_pc_lookups

        df = self._lb_df().iloc[[1]]
        _, pc_lb_slug_map = _build_pc_lookups(df)
        assert float(pc_lb_slug_map["gemini-2-5-pro"]["vanilla_x"]) == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
