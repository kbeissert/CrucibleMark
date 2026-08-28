"""Tests for get_leaderboard_scored_modules cache helper.

Score-Cache-Hardening: das Auto-Skript soll KEINEN Subprozess starten,
wenn das Leaderboard bereits einen gültigen (non-Pending) Score für das
(Modell, Modul)-Paar zeigt. Das ist die zweite Verteidigungslinie
gegenüber veralteten Score-CSVs.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.core.llamacpp_batch import (
    LEADERBOARD_COLUMN_FOR_MODULE,
    get_leaderboard_scored_modules,
)


def _write_leaderboard(path: Path, rows: list[dict[str, str]]) -> Path:
    """Schreibt eine Leaderboard-CSV mit minimalen Spalten + Score-Spalten."""
    columns = ["Model ID"] + list(LEADERBOARD_COLUMN_FOR_MODULE.values())
    df = pd.DataFrame(rows, columns=columns)
    df.to_csv(path, index=False)
    return path


def test_returns_empty_when_file_missing(tmp_path: Path) -> None:
    """Wenn die Leaderboard-Datei fehlt, leeres Set zurückgeben."""
    result = get_leaderboard_scored_modules(leaderboard_path=tmp_path / "missing.csv")
    assert result == set()


def test_returns_empty_when_force_true(tmp_path: Path) -> None:
    """force=True umgeht den Cache komplett."""
    _write_leaderboard(
        tmp_path / "lb.csv",
        [
            {
                "Model ID": "m1",
                "Code Quality Audit": "80.0",
            }
        ],
    )
    result = get_leaderboard_scored_modules(
        leaderboard_path=tmp_path / "lb.csv", force=True
    )
    assert result == set()


def test_returns_scored_pairs(tmp_path: Path) -> None:
    """Modelle mit gültigem Score werden in den Cache aufgenommen."""
    _write_leaderboard(
        tmp_path / "lb.csv",
        [
            {
                "Model ID": "gemma3:12b",
                "Code Quality Audit": "80.0",
                "CLI Badge": "Pending",
                "Logical Reasoning": "70.0",
            },
            {
                "Model ID": "qwen3:8b",
                "Code Quality Audit": "65.0",
                "Logical Reasoning": "–",
            },
        ],
    )
    result = get_leaderboard_scored_modules(leaderboard_path=tmp_path / "lb.csv")
    # gemma3:12b: code_quality + reasoning_logic (CLI Badge ist Pending)
    # qwen3:8b: code_quality (Logical Reasoning ist Em-Dash)
    # Multi-Key: jedes gescorte Modell wird unter raw + _safe_name-Form +
    # asymmetrischer Bruecke (Ziffer_Ziffer -> Ziffer.Ziffer) gecacht.
    # Doppeleintraege: (gemma:2 module + qwen:1 module) x 3 Varianten = 9.
    assert ("gemma3:12b", "code_quality") in result
    assert ("gemma3:12b", "reasoning_logic") in result
    assert ("gemma3_12b", "code_quality") in result
    assert ("gemma3_12b", "reasoning_logic") in result
    assert ("gemma3.12b", "code_quality") in result
    assert ("gemma3.12b", "reasoning_logic") in result
    assert ("gemma3:12b", "cli_benchmark") not in result
    assert ("gemma3_12b", "cli_benchmark") not in result
    assert ("gemma3.12b", "cli_benchmark") not in result
    assert ("qwen3:8b", "code_quality") in result
    assert ("qwen3_8b", "code_quality") in result
    assert ("qwen3.8b", "code_quality") in result
    assert ("qwen3:8b", "reasoning_logic") not in result
    assert ("qwen3_8b", "reasoning_logic") not in result
    assert ("qwen3.8b", "reasoning_logic") not in result
    assert len(result) == 9


def test_treats_pending_dash_empty_as_unscored(tmp_path: Path) -> None:
    """Pending, Em-Dash, Bindestrich, leer, NaN zählen als nicht gescored."""
    _write_leaderboard(
        tmp_path / "lb.csv",
        [
            {
                "Model ID": "m1",
                "Code Quality Audit": "Pending",
                "CLI Badge": "–",
                "Logical Reasoning": "-",
                "UX Writing & Microcopy": "",
            }
        ],
    )
    result = get_leaderboard_scored_modules(leaderboard_path=tmp_path / "lb.csv")
    assert result == set()


def test_skips_rows_without_model_id(tmp_path: Path) -> None:
    """Zeilen ohne Model ID werden ignoriert."""
    _write_leaderboard(
        tmp_path / "lb.csv",
        [
            {"Model ID": "", "Code Quality Audit": "80.0"},
            {"Model ID": "  ", "Code Quality Audit": "70.0"},
        ],
    )
    result = get_leaderboard_scored_modules(leaderboard_path=tmp_path / "lb.csv")
    assert result == set()


def test_handles_missing_model_id_column(tmp_path: Path) -> None:
    """Wenn die Spalte 'Model ID' fehlt, leeres Set ohne Fehler."""
    df = pd.DataFrame(
        [{"Other": "x", "Code Quality Audit": "80.0"}]
    )
    csv_path = tmp_path / "lb.csv"
    df.to_csv(csv_path, index=False)
    result = get_leaderboard_scored_modules(leaderboard_path=csv_path)
    assert result == set()


def test_caches_dot_and_underscore_variants(tmp_path: Path) -> None:
    """Multi-Key: Leaderboard speichert 'qwen2_5-coder-7b' (Underscore), aber
    ein Caller, der mit 'qwen2.5-coder-7b' (Punkt) nachschaut, muss den
    Eintrag trotzdem finden — das ist der ursprüngliche Bug-Fix.

    Regression: der Cache-Reader schreibt JEDE kanonische Variante, damit der
    Lookup-Site-Treffer unabhängig von der Schreibweise des Callers gelingt.
    """
    _write_leaderboard(
        tmp_path / "lb.csv",
        [
            {
                "Model ID": "qwen2_5-coder-7b",
                "Code Quality Audit": "80.0",
            }
        ],
    )
    result = get_leaderboard_scored_modules(leaderboard_path=tmp_path / "lb.csv")
    # Beide Schreibweisen müssen im Cache sein
    assert ("qwen2_5-coder-7b", "code_quality") in result
    assert ("qwen2.5-coder-7b", "code_quality") in result


def test_caches_vendor_prefix_variants(tmp_path: Path) -> None:
    """Multi-Key: OpenRouter-Modelle mit Vendor-Prefix (qwen/qwen3-32b) und
    _safe_name-Form (qwen_qwen3-32b) müssen beide im Cache sein."""
    _write_leaderboard(
        tmp_path / "lb.csv",
        [
            {
                "Model ID": "qwen/qwen3-32b",
                "CLI Badge": "85.0",
            }
        ],
    )
    result = get_leaderboard_scored_modules(leaderboard_path=tmp_path / "lb.csv")
    assert ("qwen/qwen3-32b", "cli_benchmark") in result
    assert ("qwen_qwen3-32b", "cli_benchmark") in result
