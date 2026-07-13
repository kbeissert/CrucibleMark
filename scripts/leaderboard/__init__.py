"""
Leaderboard generation package.
Orchestrates data loading, scoring, module integration, and exporting.

SSoT (Single Source of Truth):
- Die kanonische Model-Identität lebt in `benchmark_scores/model_cards/*.json` (Feld `model_id`).
- Im Leaderboard gibt es zwei Spalten:
  - "Model Name" = `display_name` aus der Model Card (z.B. "Claude Sonnet 4.5")
  - "Model ID" = kanonische `model_id` aus der Model Card (z.B. "claude-sonnet-4-5-20250929")
- KEINE Kürzung — beide Werte bleiben voll erhalten.

Usage:
    from scripts.leaderboard import main
    main()
"""

from pathlib import Path

import pandas as pd
import re

# Import internal modules
from .config import config
from .data_loader import load_benchmark_data
from .score_calculator import calculate_scores
from .module_integration import (
    enrich_with_module_data,
    _resolve_to_canonical_id,
    _resolve_to_display_name,
)
from .formatter import assign_rank_and_badges, print_leaderboard_table
from .exporter import export_to_csv

# pylint: disable=import-error
from utils.module_registry import (
    get_active_modules,
    get_module_test_count,
)  # noqa: E402
from utils.model_utils import (
    format_version_hash_for_display,
    get_model_size_class,
    get_provider_shortcode,
)  # noqa: E402
# pylint: enable=import-error

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def _build_modules_config(full_config, registry_func=get_active_modules) -> dict:
    """Helper to build simplified modules_config for score calculator."""
    active_modules_data = registry_func(full_config)
    modules_config = {}

    for mod_id, mod_meta, mod_int_config in active_modules_data:
        integration = mod_int_config.get("integration", {})
        lb_config = integration.get("leaderboard", {})

        display_name = mod_meta.get("name", mod_id)
        if lb_config.get("columns"):
            display_name = lb_config.get("columns")[0].get("label", display_name)
        elif mod_int_config.get("metadata", {}).get("name"):
            display_name = mod_int_config.get("metadata", {}).get("name")

        enable_scoring = lb_config.get("enable_scoring", True)
        if (
            mod_meta.get("score_group") == "info"
            or lb_config.get("score_group") == "info"
        ):
            enable_scoring = False

        default_contrib = lb_config.get(
            "default_contribution", {"routine": 0.0, "reasoning": 0.0}
        )

        mod_path_val = mod_meta.get("path", "")
        if not mod_path_val:
            mod_path_val = f"benchmark_modules/{mod_id}"

        module_path = ROOT_DIR / mod_path_val
        assets_count = get_module_test_count(module_path, mod_int_config)

        mod_entry = {
            "name": display_name,
            "enabled": True,
            "enable_scoring": enable_scoring,
            "default_contribution": default_contrib,
            "module_weight": lb_config.get("module_weight"),
            "capability_field": lb_config.get("capability_field"),
            "assets_count": assets_count,
            "path": mod_path_val,
            "benchmarks": mod_int_config.get("benchmarks", []),
            "display_test_count": lb_config.get("display_test_count"),
        }

        prefix = mod_int_config.get("metadata", {}).get("prefix")
        if not prefix:
            prefix = mod_meta.get("prefix")
        if prefix:
            mod_entry["prefix"] = prefix

        modules_config[mod_id] = mod_entry

    return modules_config


def _enrich_with_llm_judge(leaderboard: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    if "llm_judge_score" not in df.columns:
        return leaderboard

    judge_df = df[df["llm_judge_score"].notna()].copy()
    if judge_df.empty:
        return leaderboard

    judge_df["llm_judge_score"] = pd.to_numeric(
        judge_df["llm_judge_score"], errors="coerce"
    )
    judge_agg = (
        judge_df.groupby(["model", "model_version"])["llm_judge_score"]
        .mean()
        .reset_index()
        .rename(columns={"llm_judge_score": "LLM Judge Score"})
    )
    leaderboard = pd.merge(
        leaderboard, judge_agg, on=["model", "model_version"], how="left"
    )
    return leaderboard


def _reattach_provider(leaderboard: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    if "provider" in df.columns and "provider" not in leaderboard.columns:
        provider_map = (
            df.groupby("model")["provider"]
            .agg(lambda s: s.mode().iloc[0] if not s.mode().empty else "")
            .reset_index()
        )
        leaderboard = leaderboard.merge(provider_map, on="model", how="left")
    return leaderboard


def _thinking_mode_agg(s: pd.Series) -> str:
    explicit = s[s.isin(["Thinking", "Standard"])]
    if not explicit.empty:
        return explicit.mode().iloc[0]
    return "n/a"


def _reattach_thinking_mode(leaderboard: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    # "n/a" und Leerstring bedeuten "nicht konfiguriert" (alte Runs vor
    # Dual-Profile-Config) — sie dürfen einen expliziten "Standard"/"Thinking"-
    # Wert nicht überstimmen. Daher: nur explizite Werte für die Mode nutzen.
    if "thinking_mode" in df.columns and "thinking_mode" not in leaderboard.columns:
        mode_map = (
            df.groupby("model")["thinking_mode"]
            .agg(_thinking_mode_agg)
            .reset_index()
        )
        leaderboard = leaderboard.merge(mode_map, on="model", how="left")
    return leaderboard


def _round_score_columns(leaderboard: pd.DataFrame) -> pd.DataFrame:
    cols_to_round = [
        "Total Score",
        "Overall Score",
        "Performance Ratio",
        "Avg Task Duration (s)",
        "Initial Load Time (s)",
        "P95 Time (s)",
        "Max Time (s)",
        "Routine Score",
        "Reasoning Score",
        "Efficiency_Index",
        "Tokens/s",
        "LLM Judge Avg",
        "coverage_ratio",
    ]
    for col in cols_to_round:
        if col in leaderboard.columns:
            leaderboard[col] = pd.to_numeric(leaderboard[col], errors="coerce").round(2)

    if "Cost per 1K (USD)" in leaderboard.columns:
        leaderboard["Cost per 1K (USD)"] = pd.to_numeric(
            leaderboard["Cost per 1K (USD)"], errors="coerce"
        ).round(4)
    return leaderboard


def _collect_category_columns(leaderboard: pd.DataFrame, modules_config: dict) -> list[str]:
    cat_cols: list[str] = []
    for _, mod_data in modules_config.items():
        if mod_data.get("enabled") and mod_data.get("enable_scoring", True):
            name = mod_data.get("name")
            if name in leaderboard.columns:
                cat_cols.append(name)
    return cat_cols


def _format_category_columns(leaderboard: pd.DataFrame, cat_cols: list[str]) -> pd.DataFrame:
    for col in cat_cols:
        if col in leaderboard.columns:
            leaderboard[col] = pd.to_numeric(leaderboard[col], errors="coerce")
            leaderboard[col] = (
                leaderboard[col].round(2).astype(object).fillna("Pending")
            )
    return leaderboard


def _model_id_ssot(name: str) -> str:
    return _resolve_to_canonical_id(str(name).replace("*", "").strip())


def _model_name_ssot(name: str) -> str:
    return _resolve_to_display_name(str(name).replace("*", "").strip())


def _add_model_card_identity(leaderboard: pd.DataFrame) -> pd.DataFrame:
    # SSoT: Beide Spalten kommen aus `benchmark_scores/model_cards/*.json`:
    #   - "Model Name" = display_name (z.B. "Claude Sonnet 4.5")
    #   - "Model ID"   = kanonische model_id (z.B. "claude-sonnet-4-5-20250929")
    leaderboard["Model ID"] = leaderboard["model"].apply(_model_id_ssot)
    leaderboard["Model Name"] = leaderboard["model"].apply(_model_name_ssot)
    return leaderboard


def _check_draft_cards(leaderboard: pd.DataFrame) -> None:
    # Draft-Card-Check: Warnt wenn Modelle mit display_name="TODO" im Leaderboard
    # erscheinen. ensure_card() legt draft-Karten automatisch mit display_name="TODO"
    # an — diese müssen vor der Publikation manuell vervollständigt werden.
    import logging as _lb_logging  # noqa: PLC0415
    _lb_logger = _lb_logging.getLogger(__name__)
    _draft_mask = leaderboard["Model Name"].str.upper().str.strip() == "TODO"
    if _draft_mask.any():
        _draft_ids = leaderboard.loc[_draft_mask, "Model ID"].tolist()
        _draft_msg = (
            f"⚠️  WARNUNG: {len(_draft_ids)} Draft Card(s) im Leaderboard"
            f" (display_name='TODO'):\n"
            + "\n".join(f"   → {m}" for m in _draft_ids)
        )
        print(_draft_msg)
        _lb_logger.warning("Draft Cards im Leaderboard: %s", _draft_ids)


def _reorder_leaderboard_columns(leaderboard: pd.DataFrame) -> pd.DataFrame:
    # Reorder: Model Name zuerst (Spalte 2), Model ID als Spalte 3
    # Wir verschieben die Spalten so, dass die Reihenfolge passt
    if "Rank" in leaderboard.columns:
        new_order = ["Rank", "Model Name", "Model ID"]
        for col in leaderboard.columns:
            if col not in new_order:
                new_order.append(col)
        leaderboard = leaderboard[new_order]
    return leaderboard


def _format_version_column(leaderboard: pd.DataFrame) -> pd.DataFrame:
    # 9. Size class
    leaderboard["Size Class"] = leaderboard["model"].apply(get_model_size_class)

    def format_version_display(row):
        version = str(row.get("model_version", "k.A."))
        if version in ["unknown", "local", "nohash", "", "nan", "None"]:
            return "k.A."
        version = re.sub(r"-[a-f0-9]{8}$", "", version)

        base_name = str(row.get("model", ""))
        canonical_name = _resolve_to_canonical_id(base_name)
        if version in (base_name, canonical_name):
            version = "k.A."

        model_type = str(row.get("type", row.get("Type", ""))).strip().lower()
        return format_version_hash_for_display(version, model_type)

    leaderboard["Version"] = leaderboard.apply(format_version_display, axis=1)
    return leaderboard


def _add_provider_code(leaderboard: pd.DataFrame) -> pd.DataFrame:
    from utils.model_utils import is_cloud_model as _is_cloud_model

    if "provider" in leaderboard.columns:
        def _provider_code(row: pd.Series) -> str:
            code = get_provider_shortcode(str(row.get("provider", "")))
            if code == "LCL" and _is_cloud_model(str(row.get("model", ""))):
                return "CLD"
            return code

        leaderboard["Provider Code"] = leaderboard.apply(_provider_code, axis=1)
    else:
        leaderboard["Provider Code"] = "k.A."
    return leaderboard


def _format_judge_coverage(leaderboard: pd.DataFrame) -> pd.DataFrame:
    if "LLM Judge Coverage" in leaderboard.columns:
        leaderboard["LLM Judge Coverage"] = pd.to_numeric(
            leaderboard["LLM Judge Coverage"], errors="coerce"
        ).apply(lambda x: f"{x * 100:.0f}%" if pd.notnull(x) else "0%")
    return leaderboard


def main(print_table: bool = True) -> pd.DataFrame | None:
    """Main orchestration function for leaderboard generation."""
    print("Generating Leaderboard with Metrics...")

    # 1. Load Data
    df = load_benchmark_data()
    if df.empty:
        print("No data available for leaderboard.")
        return None

    # 2. Prepare Configs
    modules_config = _build_modules_config(config)

    # 3. Calculate Scores & Stats
    leaderboard, _ = calculate_scores(df, modules_config)

    # 3a. Re-attach provider column
    leaderboard = _reattach_provider(leaderboard, df)

    # 3a.1 Re-attach thinking_mode column (vLLM dual-profile / llama.cpp)
    leaderboard = _reattach_thinking_mode(leaderboard, df)

    # 3b. Enrich with LLM Judge scores
    leaderboard = _enrich_with_llm_judge(leaderboard, df)

    # 4. Final Formatting (Rounding)
    leaderboard = _round_score_columns(leaderboard)

    # 5. Format category columns
    cat_cols = _collect_category_columns(leaderboard, modules_config)
    leaderboard = _format_category_columns(leaderboard, cat_cols)

    # 6. Enrich with Custom Data
    leaderboard, cat_cols = enrich_with_module_data(
        leaderboard, cat_cols, modules_config, config
    )

    # 7. Assign badges and ranks
    leaderboard = assign_rank_and_badges(leaderboard, cat_cols)

    # 8. Model Name & Model ID (zwei separate Spalten, beide aus der Model Card)
    leaderboard = _add_model_card_identity(leaderboard)
    _check_draft_cards(leaderboard)
    leaderboard = _reorder_leaderboard_columns(leaderboard)

    # 9. Size class & version
    leaderboard = _format_version_column(leaderboard)

    # 10. Provider Code
    leaderboard = _add_provider_code(leaderboard)

    # LLM Judge Coverage
    leaderboard = _format_judge_coverage(leaderboard)

    # 11. Export and Display
    export_to_csv(leaderboard, cat_cols)

    if print_table:
        print_leaderboard_table(leaderboard)

    return leaderboard


__all__ = ["main"]
