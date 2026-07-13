"""Tests für die v5.0 Coverage-Logik in scripts/leaderboard/score_calculator.py.

Deckt die generalisierte Coverage-Status-Klassifikation (present/missing/unknown/
incapable/rolling_out/not_deployed), den Coverage-Malus, die Invariante
Routine+Reasoning=Total, coverage_ratio und die per-Modell Tests-Run-Erwartung ab.

Die globalen Card-Caches (score_calculator._CARDS_CACHE und
module_integration._ID_LOOKUP) werden pro Test zurückgesetzt, damit synthetische
Cards im tmp_path (CARD_DIR wird von conftest umgelenkt) isoliert laufen.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from scripts.leaderboard import score_calculator as sc  # noqa: E402
from scripts.leaderboard import module_integration as mi  # noqa: E402

_VALID = frozenset({"success", "language_mismatch", "truncated", "verbose_outlier", "refusal"})


@pytest.fixture(autouse=True)
def _reset_caches():
    """Setzt Card-Caches zurück, damit jeder Test frisch lädt."""
    sc._CARDS_CACHE = None
    sc._CARDS_CACHE_DIR = None
    mi._ID_LOOKUP = None
    mi._DISPLAY_LOOKUP = None
    yield
    sc._CARDS_CACHE = None
    sc._CARDS_CACHE_DIR = None
    mi._ID_LOOKUP = None
    mi._DISPLAY_LOOKUP = None


def _write_card(card_dir: Path, model_id: str, **extra) -> None:
    """Schreibt eine synthetische Model Card."""
    payload = {"model_id": model_id, "display_name": model_id}
    payload.update(extra)
    safe = model_id.replace("/", "_")
    (card_dir / f"{safe}.json").write_text(json.dumps(payload), encoding="utf-8")


def _modules_config(
    cats: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Baut eine synthetische modules_config.

    Jeder Eintrag: {id, name, weight, default, capability_field, assets}
    """
    if cats is None:
        cats = [
            {"id": "mod_a", "name": "Mod A", "weight": 1.0, "routine": 1.0, "reasoning": 0.0, "assets": 3},
            {"id": "mod_b", "name": "Mod B", "weight": 1.0, "routine": 0.0, "reasoning": 1.0, "assets": 2},
        ]
    cfg: dict[str, Any] = {}
    for c in cats:
        cfg[c["id"]] = {
            "name": c["name"],
            "enabled": True,
            "enable_scoring": c.get("scoring", True),
            "default_contribution": {"routine": c.get("routine", 0.0), "reasoning": c.get("reasoning", 0.0)},
            "module_weight": c.get("weight"),
            "assets_count": c.get("assets", 0),
            "benchmarks": [{"id": f"{c['id']}_{i}"} for i in range(c.get("assets", 0))],
            "capability_field": c.get("capability_field"),
        }
    return cfg


def _success_df(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Baut ein df_success mit model/model_version/category/status/percentage."""
    full = []
    for r in rows:
        full.append(
            {
                "model": r["model"],
                "model_version": r.get("version", "v1"),
                "type": r.get("type", "local"),
                "category": r["category"],
                "status": r.get("status", "success"),
                "percentage": r.get("pct", 80.0),
                "asset_id": r.get("asset", "a1"),
                "execution_time": r.get("exec", 1.0),
            }
        )
    return pd.DataFrame(full)


# =============================================================================
# 1. _get_incapable_models
# =============================================================================


def test_incapable_models_detected_from_card(tmp_path: Path):
    _write_card(tmp_path, "m_inc", supports_tool_use=False)
    _write_card(tmp_path, "m_ok", supports_tool_use=True)
    cfg = _modules_config(
        [{"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 2, "capability_field": "supports_tool_use"}]
    )
    inc = sc._get_incapable_models(cfg)
    assert "m_inc" in inc["Tool"]
    assert "m_ok" not in inc["Tool"]


def test_incapable_ignores_missing_field(tmp_path: Path):
    """Ein FEHLENDES capability_field ist NICHT incapable (→ unknown)."""
    _write_card(tmp_path, "m_nofield")  # supports_tool_use fehlt
    cfg = _modules_config(
        [{"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 2, "capability_field": "supports_tool_use"}]
    )
    inc = sc._get_incapable_models(cfg)
    assert inc.get("Tool", set()) == set()


def test_incapable_no_capability_field_configured(tmp_path: Path):
    """Modul ohne capability_field → keine incapable-Einträge."""
    _write_card(tmp_path, "m1", supports_tool_use=False)
    cfg = _modules_config([{"id": "m", "name": "M", "weight": 1.0, "routine": 1.0, "reasoning": 0.0, "assets": 1}])
    inc = sc._get_incapable_models(cfg)
    assert inc == {}


# =============================================================================
# 2. _classify_module_status
# =============================================================================


def test_classify_present(tmp_path: Path):
    _write_card(tmp_path, "m1", supports_tool_use=True)
    cfg = _modules_config(
        [{"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 2, "capability_field": "supports_tool_use"}]
    )
    present = {("m1", "v1", "Tool")}
    status = sc._classify_module_status("m1", "v1", "Tool", present, {}, cfg)
    assert status == "present"


def test_classify_missing(tmp_path: Path):
    _write_card(tmp_path, "m1", supports_tool_use=True)
    cfg = _modules_config(
        [{"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 2, "capability_field": "supports_tool_use"}]
    )
    status = sc._classify_module_status("m1", "v1", "Tool", set(), {}, cfg)
    assert status == "missing"


def test_classify_unknown_warns(tmp_path: Path, caplog):
    """capability_field fehlt in Card → unknown + WARNING-Log."""
    _write_card(tmp_path, "m1")  # supports_tool_use fehlt
    cfg = _modules_config(
        [{"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 2, "capability_field": "supports_tool_use"}]
    )
    with caplog.at_level("WARNING", logger=sc._coverage_logger.name):
        status = sc._classify_module_status("m1", "v1", "Tool", set(), {}, cfg)
    assert status == "unknown"
    assert any("capability_field" in rec.message for rec in caplog.records)


def test_classify_incapable(tmp_path: Path):
    _write_card(tmp_path, "m1", supports_tool_use=False)
    cfg = _modules_config(
        [{"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 2, "capability_field": "supports_tool_use"}]
    )
    inc = sc._get_incapable_models(cfg)
    status = sc._classify_module_status("m1", "v1", "Tool", set(), inc, cfg)
    assert status == "incapable"


def test_classify_incapable_with_error_rows_becomes_missing(tmp_path: Path):
    """v5.1: Ein Modell mit supports_tool_use:false UND error-Rows (attempted_set)
    ist 'missing', nicht 'incapable' — es wurde getestet, nur durchgefallen."""
    _write_card(tmp_path, "m1", supports_tool_use=False)
    cfg = _modules_config(
        [{"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 2, "capability_field": "supports_tool_use"}]
    )
    inc = sc._get_incapable_models(cfg)
    # attempted_set enthält (model, version, category) — selbst error-Rows zählen
    attempted = {("m1", "v1", "Tool")}
    status = sc._classify_module_status("m1", "v1", "Tool", set(), inc, cfg, attempted)
    assert status == "missing"


def test_classify_incapable_no_attempted_set_still_incapable(tmp_path: Path):
    """v5.1: Ohne attempted_set (None) bleibt altes Verhalten — incapable."""
    _write_card(tmp_path, "m1", supports_tool_use=False)
    cfg = _modules_config(
        [{"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 2, "capability_field": "supports_tool_use"}]
    )
    inc = sc._get_incapable_models(cfg)
    status = sc._classify_module_status("m1", "v1", "Tool", set(), inc, cfg, None)
    assert status == "incapable"


def test_expected_assets_incapable_with_rows_no_reduction(tmp_path: Path):
    """v5.1: Ein Modell mit supports_tool_use:false aber Rows für das Module
    bekommt keinen expected_assets-Abzug — es wurde getestet."""
    _write_card(tmp_path, "m1", supports_tool_use=False)
    cfg = _modules_config(
        [{"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 6, "capability_field": "supports_tool_use"}]
    )
    inc = sc._get_incapable_models(cfg)
    cat_assets = {"Tool": 6}
    # attempted_canonical_cats: (canonical_id, category) — Modell hat Rows
    attempted = {("m1", "Tool")}
    result = sc._expected_assets_for_model("m1", 49, inc, cat_assets, attempted)
    assert result == 49  # kein Abzug — wurde getestet


def test_expected_assets_incapable_without_rows_still_reduced(tmp_path: Path):
    """v5.1: Ein Modell mit supports_tool_use:false und KEINEN Rows bekommt
    weiterhin den Abzug — legitim incapable."""
    _write_card(tmp_path, "m1", supports_tool_use=False)
    cfg = _modules_config(
        [{"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 6, "capability_field": "supports_tool_use"}]
    )
    inc = sc._get_incapable_models(cfg)
    cat_assets = {"Tool": 6}
    attempted = set()  # keine Rows
    result = sc._expected_assets_for_model("m1", 49, inc, cat_assets, attempted)
    assert result == 43  # Abzug von 6


def test_classify_no_capability_field_all_missing(tmp_path: Path):
    """Modul ohne capability_field → nie incapable/unknown, immer missing wenn keine Daten."""
    _write_card(tmp_path, "m1")
    cfg = _modules_config([{"id": "m", "name": "M", "weight": 1.0, "routine": 1.0, "reasoning": 0.0, "assets": 1}])
    status = sc._classify_module_status("m1", "v1", "M", set(), {}, cfg)
    assert status == "missing"


# =============================================================================
# 3. _get_deployed_scoring_modules
# =============================================================================


def test_deployed_module(tmp_path: Path):
    cfg = _modules_config()
    df = _success_df([{"model": f"m{i}", "category": "Mod A"} for i in range(20)])
    deployed, rolling = sc._get_deployed_scoring_modules(df, cfg, 20, 0.10)
    assert "Mod A" in deployed
    assert rolling == set()


def test_not_deployed_module_excluded(tmp_path: Path):
    cfg = _modules_config(
        [
            {"id": "mod_a", "name": "Mod A", "weight": 1.0, "routine": 1.0, "reasoning": 0.0, "assets": 3},
            {"id": "mod_b", "name": "Mod B", "weight": 1.0, "routine": 0.0, "reasoning": 1.0, "assets": 2},
        ]
    )
    # Mod B hat 0 Daten
    df = _success_df([{"model": f"m{i}", "category": "Mod A"} for i in range(20)])
    deployed, rolling = sc._get_deployed_scoring_modules(df, cfg, 20, 0.10)
    assert "Mod A" in deployed
    assert "Mod B" not in deployed
    assert "Mod B" not in rolling


def test_rolling_out_module_excluded(tmp_path: Path, caplog):
    cfg = _modules_config()
    # Mod B hat Daten für 2/20 = 0.10 → genau Threshold → deployed (inklusiv)
    # Mod A hat 1/20 → rolling_out
    rows = [{"model": "m0", "category": "Mod A"}]
    rows += [{"model": f"m{i}", "category": "Mod B"} for i in range(2)]
    df = _success_df(rows)
    with caplog.at_level("INFO", logger=sc._coverage_logger.name):
        deployed, rolling = sc._get_deployed_scoring_modules(df, cfg, 20, 0.10)
    assert "Mod B" in deployed  # 2/20 = 0.10 ≥ threshold → deployed
    assert "Mod A" in rolling  # 1/20 = 0.05 < threshold
    assert any("rolling_out" in rec.message for rec in caplog.records)


def test_deployment_threshold_boundary(tmp_path: Path):
    """11/110 = 0.10 → deployed (inklusiv); 10/110 = 0.091 → rolling_out."""
    cfg = _modules_config([{"id": "m", "name": "M", "weight": 1.0, "routine": 1.0, "reasoning": 0.0, "assets": 1}])
    # 11/110
    df = _success_df([{"model": f"m{i}", "category": "M"} for i in range(11)])
    deployed, _ = sc._get_deployed_scoring_modules(df, cfg, 110, 0.10)
    assert "M" in deployed
    # 10/110
    df2 = _success_df([{"model": f"m{i}", "category": "M"} for i in range(10)])
    deployed2, rolling2 = sc._get_deployed_scoring_modules(df2, cfg, 110, 0.10)
    assert "M" not in deployed2
    assert "M" in rolling2


# =============================================================================
# 4. _compute_expected_module_weights
# =============================================================================


def test_expected_weights_with_module_weight():
    cfg = _modules_config(
        [{"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 6}]
    )
    exp_r, exp_re = sc._compute_expected_module_weights(cfg["tu"])
    # module_weight=1.0, all default 0.5/0.5, 6 assets → sum=6.0, scale=1/6
    # exp_r = (1/6)*3.0 = 0.5 ; exp_re = 0.5
    assert exp_r == pytest.approx(0.5)
    assert exp_re == pytest.approx(0.5)


def test_expected_weights_module_weight_none():
    cfg = _modules_config(
        [{"id": "m", "name": "M", "weight": None, "routine": 1.0, "reasoning": 0.0, "assets": 3}]
    )
    exp_r, exp_re = sc._compute_expected_module_weights(cfg["m"])
    # scale=1.0, config_weight_r = 3*1.0 = 3.0
    assert exp_r == pytest.approx(3.0)
    assert exp_re == pytest.approx(0.0)


# =============================================================================
# 5. _apply_coverage_malus — Invarianten + coverage_ratio
# =============================================================================


def _build_result_for_malus(models: list[dict[str, Any]]) -> pd.DataFrame:
    """Baut ein result-DataFrame mit den Spalten, die _apply_coverage_malus braucht."""
    rows = []
    for m in models:
        rows.append(
            {
                "model": m["model"],
                "model_version": m.get("version", "v1"),
                "sum_routine": m.get("sum_r", 0.0),
                "sum_reasoning": m.get("sum_re", 0.0),
                "total_weight_routine": m.get("tw_r", 0.0),
                "total_weight_reasoning": m.get("tw_re", 0.0),
                "Routine Score": m.get("rs", 0.0),
                "Reasoning Score": m.get("res", 0.0),
            }
        )
    return pd.DataFrame(rows)


def test_malus_present_model_unchanged(tmp_path: Path):
    """Present-Modell: kein Malus, coverage_ratio=1.0, Invariante erhalten."""
    _write_card(tmp_path, "m1", supports_tool_use=True)
    _write_card(tmp_path, "m2", supports_tool_use=True)
    cfg = _modules_config(
        [
            {"id": "mod_a", "name": "Mod A", "weight": 1.0, "routine": 1.0, "reasoning": 0.0, "assets": 3},
            {"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 2, "capability_field": "supports_tool_use"},
        ]
    )
    # Beide Modelle haben Daten für beide Module
    df = _success_df(
        [
            {"model": "m1", "category": "Mod A", "asset": "a1"},
            {"model": "m1", "category": "Tool", "asset": "t1"},
            {"model": "m2", "category": "Mod A", "asset": "a1"},
            {"model": "m2", "category": "Tool", "asset": "t1"},
        ]
    )
    # Mod A: weight 1.0, routine-only → tw_r=1.0; Tool: weight 1.0, 0.5/0.5 → tw_r=0.5, tw_re=0.5
    result = _build_result_for_malus(
        [{"model": "m1", "sum_r": 70.0, "sum_re": 60.0, "tw_r": 1.5, "tw_re": 0.5}]
    )
    out = sc._apply_coverage_malus(result, df, cfg, 0.10)
    # Kein Malus → Gewichte unverändert
    assert out["total_weight_routine"].iloc[0] == pytest.approx(1.5)
    assert out["total_weight_reasoning"].iloc[0] == pytest.approx(0.5)
    assert out["coverage_ratio"].iloc[0] == pytest.approx(1.0)
    # Invariante
    rs = out["Routine Score"].iloc[0]
    res = out["Reasoning Score"].iloc[0]
    total = (out["sum_routine"].iloc[0] + out["sum_reasoning"].iloc[0]) / (out["total_weight_routine"].iloc[0] + out["total_weight_reasoning"].iloc[0])
    assert rs + res == pytest.approx(total, abs=0.01)


def test_malus_missing_model_penalized(tmp_path: Path):
    """Missing-Modell (ToolUse-Daten fehlen, fähig) → Malus, coverage_ratio<1.0."""
    _write_card(tmp_path, "m1", supports_tool_use=True)
    _write_card(tmp_path, "m2", supports_tool_use=True)
    cfg = _modules_config(
        [
            {"id": "mod_a", "name": "Mod A", "weight": 1.0, "routine": 1.0, "reasoning": 0.0, "assets": 3},
            {"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 2, "capability_field": "supports_tool_use"},
        ]
    )
    # m2 hat KEINE Tool-Daten (missing)
    df = _success_df(
        [
            {"model": "m1", "category": "Mod A"},
            {"model": "m1", "category": "Tool"},
            {"model": "m2", "category": "Mod A"},
        ]
    )
    result = _build_result_for_malus(
        [
            {"model": "m1", "sum_r": 70.0, "sum_re": 60.0, "tw_r": 1.5, "tw_re": 0.5},
            {"model": "m2", "sum_r": 70.0, "sum_re": 0.0, "tw_r": 1.0, "tw_re": 0.0},
        ]
    )
    out = sc._apply_coverage_malus(result, df, cfg, 0.10)
    # m1: present → unverändert
    assert out[out["model"] == "m1"]["coverage_ratio"].iloc[0] == pytest.approx(1.0)
    # m2: missing Tool → expected weights 0.5/0.5 addiert
    row2 = out[out["model"] == "m2"].iloc[0]
    assert row2["total_weight_routine"] == pytest.approx(1.5)  # 1.0 + 0.5
    assert row2["total_weight_reasoning"] == pytest.approx(0.5)  # 0.0 + 0.5
    assert row2["coverage_ratio"] < 1.0
    # Invariante für m2
    total = (row2["sum_routine"] + row2["sum_reasoning"]) / (row2["total_weight_routine"] + row2["total_weight_reasoning"])
    assert row2["Routine Score"] + row2["Reasoning Score"] == pytest.approx(total, abs=0.01)


def test_malus_incapable_exempt(tmp_path: Path):
    """Incapable-Modell → kein Malus, coverage_ratio=1.0, Modul aus Nenner entfernt."""
    _write_card(tmp_path, "m1", supports_tool_use=True)
    _write_card(tmp_path, "m_inc", supports_tool_use=False)
    cfg = _modules_config(
        [
            {"id": "mod_a", "name": "Mod A", "weight": 1.0, "routine": 1.0, "reasoning": 0.0, "assets": 3},
            {"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 2, "capability_field": "supports_tool_use"},
        ]
    )
    df = _success_df(
        [
            {"model": "m1", "category": "Mod A"},
            {"model": "m1", "category": "Tool"},
            {"model": "m_inc", "category": "Mod A"},
        ]
    )
    result = _build_result_for_malus(
        [
            {"model": "m1", "sum_r": 70.0, "sum_re": 60.0, "tw_r": 1.5, "tw_re": 0.5},
            {"model": "m_inc", "sum_r": 70.0, "sum_re": 0.0, "tw_r": 1.0, "tw_re": 0.0},
        ]
    )
    out = sc._apply_coverage_malus(result, df, cfg, 0.10)
    row_inc = out[out["model"] == "m_inc"].iloc[0]
    # Incapable → keine Gewichte addiert
    assert row_inc["total_weight_routine"] == pytest.approx(1.0)
    assert row_inc["total_weight_reasoning"] == pytest.approx(0.0)
    assert row_inc["coverage_ratio"] == pytest.approx(1.0)


def test_malus_unknown_penalized_and_warned(tmp_path: Path, caplog):
    """Unknown (capability_field fehlt in Card) → wie missing bestraft + WARNING."""
    _write_card(tmp_path, "m1", supports_tool_use=True)
    _write_card(tmp_path, "m_unk")  # supports_tool_use fehlt
    cfg = _modules_config(
        [
            {"id": "mod_a", "name": "Mod A", "weight": 1.0, "routine": 1.0, "reasoning": 0.0, "assets": 3},
            {"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 2, "capability_field": "supports_tool_use"},
        ]
    )
    df = _success_df(
        [
            {"model": "m1", "category": "Mod A"},
            {"model": "m1", "category": "Tool"},
            {"model": "m_unk", "category": "Mod A"},
        ]
    )
    result = _build_result_for_malus(
        [
            {"model": "m_unk", "sum_r": 70.0, "sum_re": 0.0, "tw_r": 1.0, "tw_re": 0.0},
        ]
    )
    with caplog.at_level("WARNING", logger=sc._coverage_logger.name):
        out = sc._apply_coverage_malus(result, df, cfg, 0.10)
    row = out.iloc[0]
    assert row["total_weight_routine"] == pytest.approx(1.5)  # Malus addiert
    assert row["coverage_ratio"] < 1.0
    assert any("capability_field" in rec.message for rec in caplog.records)


def test_malus_routine_reasoning_recomputed(tmp_path: Path):
    """Routine/Reasoning Score müssen nach Malus recomputiert werden (Invariante)."""
    _write_card(tmp_path, "m1", supports_tool_use=True)
    _write_card(tmp_path, "m_fill", supports_tool_use=True)
    cfg = _modules_config(
        [
            {"id": "mod_a", "name": "Mod A", "weight": 1.0, "routine": 1.0, "reasoning": 0.0, "assets": 3},
            {"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 2, "capability_field": "supports_tool_use"},
        ]
    )
    # m_fill hat beide Module (damit Tool deployed ist); m1 fehlt Tool
    df = _success_df(
        [
            {"model": "m1", "category": "Mod A"},
            {"model": "m_fill", "category": "Mod A"},
            {"model": "m_fill", "category": "Tool"},
        ]
    )
    result = _build_result_for_malus(
        [
            {"model": "m1", "sum_r": 80.0, "sum_re": 0.0, "tw_r": 1.0, "tw_re": 0.0},
            {"model": "m_fill", "sum_r": 80.0, "sum_re": 60.0, "tw_r": 1.5, "tw_re": 0.5},
        ]
    )
    out = sc._apply_coverage_malus(result, df, cfg, 0.10)
    row = out[out["model"] == "m1"].iloc[0]
    # Nach Malus: tw_r=1.5, tw_re=0.5, tw_global=2.0
    assert row["Routine Score"] == pytest.approx(80.0 / 2.0)
    assert row["Reasoning Score"] == pytest.approx(0.0)
    # Invariante
    total = (row["sum_routine"] + row["sum_reasoning"]) / (row["total_weight_routine"] + row["total_weight_reasoning"])
    assert row["Routine Score"] + row["Reasoning Score"] == pytest.approx(total, abs=0.01)


def test_malus_multiple_missing_cumulative(tmp_path: Path):
    """2 fehlende Module → kumulativer Malus."""
    _write_card(tmp_path, "m1")
    _write_card(tmp_path, "m_fill")
    cfg = _modules_config(
        [
            {"id": "mod_a", "name": "Mod A", "weight": 1.0, "routine": 1.0, "reasoning": 0.0, "assets": 3},
            {"id": "mod_b", "name": "Mod B", "weight": 1.0, "routine": 0.0, "reasoning": 1.0, "assets": 2},
            {"id": "mod_c", "name": "Mod C", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 2},
        ]
    )
    # m_fill hat alle Module (deployed); m1 hat nur Mod A
    df = _success_df(
        [
            {"model": "m1", "category": "Mod A"},
            {"model": "m_fill", "category": "Mod A"},
            {"model": "m_fill", "category": "Mod B"},
            {"model": "m_fill", "category": "Mod C"},
        ]
    )
    result = _build_result_for_malus(
        [{"model": "m1", "sum_r": 90.0, "sum_re": 0.0, "tw_r": 1.0, "tw_re": 0.0}]
    )
    out = sc._apply_coverage_malus(result, df, cfg, 0.10)
    row = out.iloc[0]
    # Mod B missing: exp_r=0, exp_re=1.0; Mod C missing: exp_r=0.5, exp_re=0.5
    assert row["total_weight_routine"] == pytest.approx(1.5)  # 1.0 + 0 + 0.5
    assert row["total_weight_reasoning"] == pytest.approx(1.5)  # 0 + 1.0 + 0.5
    assert row["coverage_ratio"] < 0.5  # nur 1 von 3 Modulen present


def test_malus_extreme_low_coverage(tmp_path: Path):
    """Modell mit nur 1 von 3 Modulen present → sehr niedrige coverage_ratio."""
    _write_card(tmp_path, "m1")
    _write_card(tmp_path, "m_fill")
    cfg = _modules_config(
        [
            {"id": "mod_a", "name": "Mod A", "weight": 1.0, "routine": 1.0, "reasoning": 0.0, "assets": 3},
            {"id": "mod_b", "name": "Mod B", "weight": 1.0, "routine": 0.0, "reasoning": 1.0, "assets": 2},
            {"id": "mod_c", "name": "Mod C", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 2},
        ]
    )
    df = _success_df(
        [
            {"model": "m1", "category": "Mod A"},
            {"model": "m_fill", "category": "Mod A"},
            {"model": "m_fill", "category": "Mod B"},
            {"model": "m_fill", "category": "Mod C"},
        ]
    )
    result = _build_result_for_malus(
        [{"model": "m1", "sum_r": 100.0, "sum_re": 0.0, "tw_r": 1.0, "tw_re": 0.0}]
    )
    out = sc._apply_coverage_malus(result, df, cfg, 0.10)
    row = out.iloc[0]
    # present_weight = 1.0 (Mod A), denom = 3.0 → coverage_ratio ≈ 0.333
    assert row["coverage_ratio"] == pytest.approx(1.0 / 3.0, abs=0.01)
    # Score massiv reduziert: 100/3.0 ≈ 33.3
    total = (row["sum_routine"] + row["sum_reasoning"]) / (row["total_weight_routine"] + row["total_weight_reasoning"])
    assert total < 40.0


def test_malus_coverage_ratio_zero(tmp_path: Path):
    """Modell hat 0 present-Module (alle missing) → coverage_ratio=0.0, Score=0.0."""
    _write_card(tmp_path, "m1")
    _write_card(tmp_path, "m_fill")
    cfg = _modules_config(
        [
            {"id": "mod_a", "name": "Mod A", "weight": 1.0, "routine": 1.0, "reasoning": 0.0, "assets": 3},
            {"id": "mod_b", "name": "Mod B", "weight": 1.0, "routine": 0.0, "reasoning": 1.0, "assets": 2},
        ]
    )
    # m_fill hat beide Module (deployed); m1 hat keine (0 present)
    df = _success_df(
        [
            {"model": "m_fill", "category": "Mod A"},
            {"model": "m_fill", "category": "Mod B"},
        ]
    )
    result = _build_result_for_malus(
        [{"model": "m1", "sum_r": 0.0, "sum_re": 0.0, "tw_r": 0.0, "tw_re": 0.0}]
    )
    out = sc._apply_coverage_malus(result, df, cfg, 0.10)
    row = out.iloc[0]
    assert row["coverage_ratio"] == pytest.approx(0.0)
    # Score = 0 (sum=0, weights>0 after malus)
    tw = row["total_weight_routine"] + row["total_weight_reasoning"]
    assert tw > 0
    assert row["sum_routine"] + row["sum_reasoning"] == pytest.approx(0.0)


def test_malus_rolling_out_excluded_for_all(tmp_path: Path):
    """Rolling-out-Modul → für alle Modelle aus Nenner entfernt."""
    _write_card(tmp_path, "m1", supports_tool_use=True)
    cfg = _modules_config(
        [
            {"id": "mod_a", "name": "Mod A", "weight": 1.0, "routine": 1.0, "reasoning": 0.0, "assets": 3},
            {"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 2, "capability_field": "supports_tool_use"},
        ]
    )
    # Tool hat nur 1/20 Daten → rolling_out
    rows = [{"model": "m1", "category": "Mod A"}]
    rows += [{"model": "m1", "category": "Tool"}]  # nur m1 hat Tool
    df = _success_df(rows)
    result = _build_result_for_malus(
        [{"model": "m1", "sum_r": 80.0, "sum_re": 0.0, "tw_r": 1.0, "tw_re": 0.0}]
    )
    out = sc._apply_coverage_malus(result, df, cfg, 0.10)
    row = out.iloc[0]
    # Tool ist rolling_out → kein Malus, keine coverage-Auswirkung
    assert row["total_weight_routine"] == pytest.approx(1.0)
    assert row["coverage_ratio"] == pytest.approx(1.0)


# =============================================================================
# 6. Per-Modell Tests-Run-Erwartung (Task 5)
# =============================================================================


def test_expected_assets_incapable_reduced(tmp_path: Path):
    """Incapable-Modell → expected_assets um Tool-Assets reduziert."""
    _write_card(tmp_path, "m_inc", supports_tool_use=False)
    cfg = _modules_config(
        [
            {"id": "mod_a", "name": "Mod A", "weight": 1.0, "routine": 1.0, "reasoning": 0.0, "assets": 5},
            {"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 6, "capability_field": "supports_tool_use"},
        ]
    )
    result = sc._expected_assets_for_model("m_inc", 11, sc._get_incapable_models(cfg), {"Mod A": 5, "Tool": 6})
    assert result == 5  # 11 - 6


def test_expected_assets_present_full(tmp_path: Path):
    """Present-Modell → volle expected_assets."""
    _write_card(tmp_path, "m_ok", supports_tool_use=True)
    cfg = _modules_config(
        [
            {"id": "mod_a", "name": "Mod A", "weight": 1.0, "routine": 1.0, "reasoning": 0.0, "assets": 5},
            {"id": "tu", "name": "Tool", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 6, "capability_field": "supports_tool_use"},
        ]
    )
    result = sc._expected_assets_for_model("m_ok", 11, sc._get_incapable_models(cfg), {"Mod A": 5, "Tool": 6})
    assert result == 11


# =============================================================================
# 7. Integration: calculate_scores end-to-end (Invariante über alle Status)
# =============================================================================


def test_calculate_scores_invariant_all_statuses(tmp_path: Path):
    """End-to-End: Routine+Reasoning=Total für present/missing/incapable."""
    _write_card(tmp_path, "m_present", supports_tool_use=True)
    _write_card(tmp_path, "m_missing", supports_tool_use=True)
    _write_card(tmp_path, "m_inc", supports_tool_use=False)
    cfg = _modules_config(
        [
            {"id": "code_quality", "name": "Code Quality Audit", "weight": 1.0, "routine": 1.0, "reasoning": 0.0, "assets": 2},
            {"id": "tu", "name": "Tool Execution", "weight": 1.0, "routine": 0.5, "reasoning": 0.5, "assets": 2, "capability_field": "supports_tool_use"},
        ]
    )
    rows = []
    # m_present: beide Module
    rows += [{"model": "m_present", "category": "Code Quality Audit", "asset": "code_quality_1", "pct": 80.0}]
    rows += [{"model": "m_present", "category": "Code Quality Audit", "asset": "code_quality_2", "pct": 90.0}]
    rows += [{"model": "m_present", "category": "Tool Execution", "asset": "tu_1", "pct": 70.0}]
    rows += [{"model": "m_present", "category": "Tool Execution", "asset": "tu_2", "pct": 75.0}]
    # m_missing: nur Code Quality (Tool fehlt)
    rows += [{"model": "m_missing", "category": "Code Quality Audit", "asset": "code_quality_1", "pct": 80.0}]
    rows += [{"model": "m_missing", "category": "Code Quality Audit", "asset": "code_quality_2", "pct": 90.0}]
    # m_inc: nur Code Quality (Tool incapable)
    rows += [{"model": "m_inc", "category": "Code Quality Audit", "asset": "code_quality_1", "pct": 80.0}]
    rows += [{"model": "m_inc", "category": "Code Quality Audit", "asset": "code_quality_2", "pct": 90.0}]
    df = _success_df(rows)
    # calculate_scores expects 'percentage' and 'status' and 'asset_id'
    result, _ = sc.calculate_scores(df, cfg)
    # Invariante: Routine + Reasoning = Total (temp columns already dropped by finalize)
    for _, row in result.iterrows():
        assert row["Routine Score"] + row["Reasoning Score"] == pytest.approx(
            row["Total Score"], abs=0.05
        )
    # coverage_ratio checks
    present = result[result["model"] == "m_present"].iloc[0]
    missing = result[result["model"] == "m_missing"].iloc[0]
    inc = result[result["model"] == "m_inc"].iloc[0]
    assert present["coverage_ratio"] == pytest.approx(1.0)
    assert missing["coverage_ratio"] < 1.0
    assert inc["coverage_ratio"] == pytest.approx(1.0)
    # incapable wird NICHT bestraft (Tool aus Nenner entfernt) → Score = reine
    # Code-Quality-Normalisierung (85). missing WIRD bestraft (Tool im Nenner) →
    # niedriger als inc bei identischen Code-Quality-Daten.
    assert inc["Total Score"] == pytest.approx(85.0, abs=0.05)
    assert missing["Total Score"] < inc["Total Score"]
