"""
Leaderboard generation package.
Orchestrates data loading, scoring, module integration, and exporting.

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
from .module_integration import enrich_with_module_data
from .formatter import assign_rank_and_badges, print_leaderboard_table
from .exporter import export_to_csv

# pylint: disable=import-error
from utils.module_registry import (
    get_active_modules,
    get_module_test_count,
)  # noqa: E402
from utils.model_utils import format_version_hash_for_display  # noqa: E402
# pylint: enable=import-error

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def _build_modules_config(full_config, registry_func=get_active_modules) -> dict:
    """Helper to build simplified modules_config for score calculator."""
    active_modules_data = registry_func(full_config)
    modules_config = {}

    for mod_id, mod_meta, mod_int_config in active_modules_data:
        # Extract Leaderboard info from Internal Config
        integration = mod_int_config.get("integration", {})
        lb_config = integration.get("leaderboard", {})

        # Determine Display Name
        display_name = mod_meta.get("name", mod_id)
        if lb_config.get("columns"):
            display_name = lb_config.get("columns")[0].get("label", display_name)
        elif mod_int_config.get("metadata", {}).get("name"):
            display_name = mod_int_config.get("metadata", {}).get("name")

        # Scoring Enabled?
        enable_scoring = lb_config.get("enable_scoring", True)
        if (
            mod_meta.get("score_group") == "info"
            or lb_config.get("score_group") == "info"
        ):
            enable_scoring = False

        # Default Contribution
        default_contrib = lb_config.get(
            "default_contribution", {"routine": 0.0, "reasoning": 0.0}
        )

        # Determine Assets Count
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
            "assets_count": assets_count,
            "path": mod_path_val,
            "benchmarks": mod_int_config.get("benchmarks", []),
            "display_test_count": lb_config.get("display_test_count"),
        }

        # Look for prefix
        prefix = mod_int_config.get("metadata", {}).get("prefix")
        if not prefix:
            prefix = mod_meta.get("prefix")
        if prefix:
            mod_entry["prefix"] = prefix

        modules_config[mod_id] = mod_entry

    return modules_config


def _enrich_with_llm_judge(leaderboard: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'LLM Judge Score' column to the leaderboard when per-asset judge scores
    are present in the raw benchmark data.

    The column is only added when at least one row in *df* carries a numeric
    ``llm_judge_score`` value. If the column is absent or entirely empty the
    leaderboard is returned unchanged (non-breaking).
    """
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


from typing import Optional

def main(print_table: bool = True) -> Optional[pd.DataFrame]:
    """Main orchestration function for leaderboard generation."""
    print("Generating Leaderboard with Metrics...")

    # 1. Load Data
    df = load_benchmark_data()
    if df.empty:
        print("No data available for leaderboard.")
        return None

    # 2. Prepare Configs
    # Build simplified module config map for scoring logic
    modules_config = _build_modules_config(config)

    # 3. Calculate Scores & Stats
    leaderboard, _ = calculate_scores(df, modules_config)

    # 3b. Enrich with LLM Judge scores (no-op when column is absent)
    leaderboard = _enrich_with_llm_judge(leaderboard, df)

    # 4. Final Formatting (Rounding etc.)
    # Note: Some rounding happens in formatter/exporter phase or here if needed
    cols_to_round = [
        "Total Score",
        "Overall Score",
        "Performance Ratio",
        "Avg Time (s)",
        "Initial Load Time (s)",
        "P95 Time (s)",
        "Max Time (s)",
        "Routine Score",
        "Reasoning Score",
        "Efficiency_Index",
        "LLM Judge Avg",
    ]
    for col in cols_to_round:
        if col in leaderboard.columns:
            leaderboard[col] = pd.to_numeric(leaderboard[col], errors="coerce").round(2)

    # Round Cost per 1K to 4 places separately
    if "Cost per 1K (USD)" in leaderboard.columns:
        leaderboard["Cost per 1K (USD)"] = pd.to_numeric(
            leaderboard["Cost per 1K (USD)"], errors="coerce"
        ).round(4)

    # Format category columns (rounding)
    cat_cols = []

    # Determine which categories to show (scoring enabled only)
    for _, mod_data in modules_config.items():
        if mod_data.get("enabled") and mod_data.get("enable_scoring", True):
            name = mod_data.get("name")
            if name in leaderboard.columns:
                cat_cols.append(name)

    # Convert numeric module scores and format them
    for col in cat_cols:
        if col in leaderboard.columns:
            leaderboard[col] = pd.to_numeric(leaderboard[col], errors="coerce")
            leaderboard[col] = (
                leaderboard[col].round(2).astype(object).fillna("Pending")
            )

    # 5. Enrich with Custom Data (from other CSVs via module config, e.g. Political Compass)
    leaderboard, cat_cols = enrich_with_module_data(
        leaderboard, cat_cols, modules_config, config
    )

    # 6. Assign badges and ranks dynamically using detected category columns
    leaderboard = assign_rank_and_badges(leaderboard, cat_cols)

    # 7. Model Name & Version Formatting
    def clean_model_name(name):
        name = str(name).replace("*", "").strip()
        # Dates (YYYY-MM-DD or YYYYMMDD)
        name = re.sub(r"[-_]?\d{4}[-_]?\d{2}[-_]?\d{2}$", "", name)
        # Year or YearMonth (like mistral 2411)
        name = re.sub(r"[-_]?\d{4}$", "", name)
        return name

    leaderboard["Model Name"] = leaderboard["model"].apply(clean_model_name)

    def format_version_display(row):
        version = str(row.get("model_version", "k.A."))
        if version in ["unknown", "local", "nohash", "", "nan", "None"]:
            return "k.A."
        # Strip legacy historical behavioral hash (8 char hex string ending)
        version = re.sub(r"-[a-f0-9]{8}$", "", version)

        base_name = str(row.get("model", ""))
        cn = clean_model_name(base_name)
        if version == base_name or version == cn:
            version = "k.A."

        # Keep short hash for local/Ollama models only.
        model_type = str(row.get("type", row.get("Type", ""))).strip().lower()

        return format_version_hash_for_display(version, model_type)

    leaderboard["Version"] = leaderboard.apply(format_version_display, axis=1)

    # Convert LLM Judge Coverage to percentage string format
    if "LLM Judge Coverage" in leaderboard.columns:
        leaderboard["LLM Judge Coverage"] = pd.to_numeric(
            leaderboard["LLM Judge Coverage"], errors="coerce"
        ).apply(lambda x: f"{x * 100:.0f}%" if pd.notnull(x) else "0%")

    # 8. Export and Display
    export_to_csv(leaderboard, cat_cols)

    if print_table:
        print_leaderboard_table(leaderboard)

    return leaderboard


__all__ = ["main"]
