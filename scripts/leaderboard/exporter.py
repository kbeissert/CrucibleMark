"""
Leaderboard export functionality.
Handles saving the final leaderboard to CSV or other formats.
"""
from typing import List

import pandas as pd

from .config import OUTPUT_CSV


def export_to_csv(leaderboard: pd.DataFrame, cat_cols: List[str]) -> None:
    """
    Exports the leaderboard DataFrame to a CSV file.
    Formats column names and selection before writing.
    
    Args:
        leaderboard: The prepared leaderboard DataFrame.
        cat_cols: List of dynamic category columns to include.
    """
    
    # Create copy to avoid mutating the display DataFrame
    df_export = leaderboard.copy()
    
    # Rename for export if not already done (though main script does it)
    if "Overall Score" in df_export.columns:
        df_export = df_export.rename(columns={"Overall Score": "Total Score"})

    cols = [
        "Rank",
        "Recommendation",
        "Model Name",
        "Version",
        "Generation",
        "Total Score",
        "Performance Ratio",
        "Avg Time (s)",
        "Badge",
        "Routine Score",
        "Reasoning Score",
        "Type",
    ]

    final_cols = []
    
    # Add standard cols if they exist
    for c in cols:
        if c in df_export.columns:
            final_cols.append(c)
            
    # Add dynamic category cols
    for c in cat_cols:
        if c in df_export.columns:
            final_cols.append(c)
            
    # Add Tests Run count
    if "Tests Run" in df_export.columns:
        final_cols.append("Tests Run")

    # Select columns
    df_export = df_export[final_cols]
    
    try:
        df_export.to_csv(OUTPUT_CSV, index=False)
        print(f"Leaderboard saved to: {OUTPUT_CSV}")
    except (IOError, PermissionError) as e:
        print(f"⚠️ Error saving leaderboard to {OUTPUT_CSV}: {e}")
