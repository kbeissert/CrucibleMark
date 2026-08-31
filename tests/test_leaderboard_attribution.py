"""Regressionstests fuer das Attribution-Mirror im Leaderboard-Join (2026-08-31).

Hintergrund: Instruct-Ersatzlaeufe der Coverage-Regel (Konzept-Doc Abschn. 11)
werden per ``result_attribution`` unter der Original-Modell-ID persistiert.
Fuehrt das Hauptboard eine eigene Zeile fuer die Profil-ID, blieb deren
Political-Bias-Zelle dauerhaft "Pending", obwohl Daten existierten.
"""
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.leaderboard.module_integration import (  # noqa: E402
    _apply_result_attribution,
    _load_attribution_pairs,
)


def _source_df(model_ids: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "model": model_ids,
            "model_version": ["4"] * len(model_ids),
            "vanilla_label": ["Sozial / Autoritär"] * len(model_ids),
            "shift_distance": [1.72] * len(model_ids),
        }
    )


class TestLoadAttributionPairs:
    def test_reads_real_pc_module_config(self):
        pairs = _load_attribution_pairs("political_compass")
        assert (
            pairs.get("gemma-4-12b-it-ud-q6_k_xl-instruct-spark")
            == "gemma-4-12b-it-ud-q6_k_xl-spark"
        )

    def test_unknown_module_returns_empty(self):
        assert _load_attribution_pairs("modul_gibt_es_nicht") == {}


class TestApplyResultAttribution:
    def test_mirrors_original_row_to_profile_alias(self):
        source = _source_df(["gemma-4-12b-it-ud-q6_k_xl-spark"])
        out = _apply_result_attribution(
            source, {"attribution_module": "political_compass"}
        )
        assert "gemma-4-12b-it-ud-q6_k_xl-instruct-spark" in set(out["model"])
        mirror = out[out["model"] == "gemma-4-12b-it-ud-q6_k_xl-instruct-spark"]
        assert mirror.iloc[0]["shift_distance"] == 1.72

    def test_existing_direct_row_wins_over_alias(self):
        source = _source_df(
            [
                "gemma-4-12b-it-ud-q6_k_xl-spark",
                "gemma-4-12b-it-ud-q6_k_xl-instruct-spark",
            ]
        )
        out = _apply_result_attribution(
            source, {"attribution_module": "political_compass"}
        )
        assert len(out) == 2

    def test_no_source_row_for_original_is_noop(self):
        source = _source_df(["qwen3_5-4b-q6"])
        out = _apply_result_attribution(
            source, {"attribution_module": "political_compass"}
        )
        assert list(out["model"]) == ["qwen3_5-4b-q6"]

    def test_without_config_key_is_noop(self):
        source = _source_df(["gemma-4-12b-it-ud-q6_k_xl-spark"])
        out = _apply_result_attribution(source, {})
        assert len(out) == 1
