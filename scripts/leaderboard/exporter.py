"""
Leaderboard export functionality.
Handles saving the final leaderboard to CSV or other formats.
"""
from typing import List

import pandas as pd

from .config import OUTPUT_CSV



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
        "Rank", "Model Name", "Version", "Badge",
        "Speed Profile",  # Merged column
        "Total Score", "Performance/s", "Avg Time (s)",
        "Cost per 1K (USD)", "Type"
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
        "Rank", "Model Name", "Version", "Badge",
        "Speed Profile", "Performance Tier",  # Keep raw tier for analysis
        "Total Score", "Performance/s", 
        "Avg Time (s)", "Initial Load Time (s)", "P95 Time (s)", "Max Time (s)", "Timeout Count",
        "Cost per 1K (USD)", 
        "Routine Score", "Reasoning Score", "Type"
    ]
    
    final_cols = []
    for c in cols:
        if c in df_export.columns:
            final_cols.append(c)
            
    for c in cat_cols:
        if c in df_export.columns:
            final_cols.append(c)
            
    if "Tests Run" in df_export.columns:
        final_cols.append("Tests Run")

    # Select and Save
    existing_cols = [c for c in final_cols if c in df_export.columns]
    df_export = df_export[existing_cols]

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
