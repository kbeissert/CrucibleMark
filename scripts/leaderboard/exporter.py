"""
Leaderboard export functionality.
Handles saving the final leaderboard to CSV or other formats.
"""

from typing import List

import pandas as pd

from .config import OUTPUT_CSV


def _format_judge_stars(df: pd.DataFrame) -> pd.DataFrame:
    """
    Formats the 'LLM Judge Avg' column as '<value> ★' (e.g. '3.8 ★').
    Preserves the 0–5 scale; the star symbol signals the alternative rating
    dimension without conflating it with the percentage-based Total Score.
    """
    if "LLM Judge Avg" not in df.columns:
        return df
    df = df.copy()

    def _fmt(val: object) -> object:
        try:
            n = float(val)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return val
        if pd.isna(n):
            return val
        return f"{n:.1f} \u2605"

    df["LLM Judge Avg"] = df["LLM Judge Avg"].apply(_fmt)
    return df


def _format_tokens_k(df: pd.DataFrame) -> pd.DataFrame:
    """
    Formats token columns for human readability in the CSV output.
    'Tokens Total' and 'Tokens: <Module>' are displayed as e.g. '12.3K'
    instead of 12300. The internal DataFrame is not modified — a copy is
    returned with the display-only formatted string column.
    Numbers below 1000 are shown as plain integers (e.g. '847').
    """
    token_cols = [c for c in df.columns if c == "Tokens Total" or c.startswith("Tokens: ")]
    if not token_cols:
        return df
    df = df.copy()
    for col in token_cols:
        def _fmt(val: object) -> object:
            try:
                n = float(val)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return val
            if pd.isna(n):
                return val
            if n >= 1000:
                return f"{n / 1000:.1f}K"
            return str(int(n))
        df[col] = df[col].apply(_fmt)
    return df


def export_leaderboard_compact(leaderboard: pd.DataFrame, cat_cols: List[str]) -> None:
    """
    Exports the COMPACT leaderboard (human-readable, ~20 columns).
    Excludes verbose metrics like P95, redundant speed columns, etc.
    """
    df_export = leaderboard.copy()

    # Clean up Score columns
    if "Overall Score" in df_export.columns:
        if "Total Score" in df_export.columns:
            df_export = df_export.drop(columns=["Overall Score"])
        else:
            df_export = df_export.rename(columns={"Overall Score": "Total Score"})

    # Compact Column List
    cols = [
        "Rank",
        "Model Name",
        "Version",
        "Badge",
        "Speed Profile",  # Merged column
        "Total Score",
        "Tokens/s",
        "Avg Task Duration (s)",
        "Tokens Total",
        "Cost per 1K (USD)",
        "Benchmark Cost (USD)",
        "LLM Judge Avg",
        "LLM Judge Coverage",
        "Type",
    ]

    final_cols = []

    # 1. Standard Cols
    for c in cols:
        if c in df_export.columns:
            final_cols.append(c)

    # 2. Category Cols (Code Quality, etc.)
    for c in cat_cols:
        if c in df_export.columns:
            final_cols.append(c)

    # 3. Meta
    if "Tests Run" in df_export.columns:
        final_cols.append("Tests Run")

    # Select and Save
    # Drop columns that don't exist to avoid key error
    existing_cols = [c for c in final_cols if c in df_export.columns]
    df_export = df_export[existing_cols]
    df_export = _format_tokens_k(df_export)
    df_export = _format_judge_stars(df_export)

    try:
        df_export.to_csv(OUTPUT_CSV, index=False)
        print(f"Compact Leaderboard saved to: {OUTPUT_CSV}")
    except (IOError, PermissionError) as e:
        print(f"⚠️ Error saving compact leaderboard: {e}")


def export_leaderboard_detailed(leaderboard: pd.DataFrame, cat_cols: List[str]) -> None:
    """
    Exports the DETAILED leaderboard (26+ cols).
    Includes P95, Max Time, Timeout Count, Routine/Reasoning aggregates.
    """
    df_export = leaderboard.copy()

    # Detailed output should have distinct file name
    # OUTPUT_CSV is a Path object
    detailed_csv = OUTPUT_CSV.parent / f"{OUTPUT_CSV.stem}_detailed{OUTPUT_CSV.suffix}"

    # Ensure Score columns exist
    if "Overall Score" in df_export.columns:
        if "Total Score" not in df_export.columns:
            df_export = df_export.rename(columns={"Overall Score": "Total Score"})

    cols = [
        "Rank",
        "Model Name",
        "Version",
        "Badge",
        "Speed Profile",
        "Performance Tier",  # Keep raw tier for analysis
        "Total Score",
        "Tokens/s",
        "Avg Task Duration (s)",
        "Initial Load Time (s)",
        "P95 Time (s)",
        "Max Time (s)",
        "Timeout Count",
        "Tokens Total",
        "Cost per 1K (USD)",
        "Benchmark Cost (USD)",
        "LLM Judge Avg",
        "LLM Judge Avg (raw)",
        "LLM Judge Coverage",
        "Routine Score",
        "Reasoning Score",
        "Type",
    ]

    # Preserve full-precision judge avg before star formatting
    if "LLM Judge Avg" in df_export.columns:
        df_export["LLM Judge Avg (raw)"] = pd.to_numeric(
            df_export["LLM Judge Avg"], errors="coerce"
        )

    final_cols = []
    for c in cols:
        if c in df_export.columns:
            final_cols.append(c)

    for c in cat_cols:
        if c in df_export.columns:
            final_cols.append(c)

    # Token columns per module (e.g. "Tokens: Code Quality")
    token_module_cols = sorted([c for c in df_export.columns if c.startswith("Tokens: ")])
    for c in token_module_cols:
        final_cols.append(c)

    if "Tests Run" in df_export.columns:
        final_cols.append("Tests Run")

    # Select and Save
    existing_cols = [c for c in final_cols if c in df_export.columns]
    df_export = df_export[existing_cols]
    df_export = _format_tokens_k(df_export)
    df_export = _format_judge_stars(df_export)

    try:
        df_export.to_csv(detailed_csv, index=False)
        print(f"Detailed Leaderboard saved to: {detailed_csv}")
    except (IOError, PermissionError) as e:
        print(f"⚠️ Error saving detailed leaderboard: {e}")


def export_to_csv(leaderboard: pd.DataFrame, cat_cols: List[str]) -> None:
    """
    Legacy entry point - calls both exports.
    """
    export_leaderboard_compact(leaderboard, cat_cols)
    export_leaderboard_detailed(leaderboard, cat_cols)
