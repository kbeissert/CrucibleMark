"""
Leaderboard formatting and display logic.
Handles badge assignment and console output of the leaderboard.
"""
import pandas as pd

# Import constants
from .config import DEFAULT_THRESHOLDS, config

# Load thresholds from config or use defaults
lb_config = config.get("leaderboard", {}).get("thresholds", DEFAULT_THRESHOLDS)

def _get_badge(row: pd.Series) -> str:
    """Ermittelt das Badge basierend auf den Scores."""
    routine = row.get("Routine Score", 0)
    reasoning = row.get("Reasoning Score", 0)

    # Handle NaNs
    routine = 0 if pd.isna(routine) else routine
    reasoning = 0 if pd.isna(reasoning) else reasoning

    # Get Thresholds from Config
    t_god_r = lb_config.get("god_mode_routine", 85)
    t_god_l = lb_config.get("god_mode_reasoning", 80)
    t_deep = lb_config.get("deep_thinker_reasoning", 80)
    t_daily = lb_config.get("daily_driver_routine", 80)

    is_god_mode = (reasoning > t_god_l and routine > t_god_r)

    if is_god_mode:
        return "👑 God Mode"
    if reasoning > t_deep:
        return "🧠 Deep Thinker"
    if routine > t_daily:
        return "🏎️ Daily Driver"
    return "⚖️ Standard"


def assign_rank_and_badges(df: pd.DataFrame) -> pd.DataFrame:
    """Vergibt Rank und Empfehlungs-Badges."""
    if df.empty:
        return df
        
    # Rank assignment (assuming df is already sorted)
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    df["Rank"] = df.index
    
    # Badge (Category) Assignment
    df["Badge"] = df.apply(_get_badge, axis=1)
    
    # Recommendation Assignment
    df["Recommendation"] = ""

    # Ensure is_complete is boolean (Fill NaNs with False)
    if "is_complete" in df.columns:
        df["is_complete"] = df["is_complete"].fillna(False).astype(bool)
    else:
        df["is_complete"] = False

    incomplete_mask = ~df["is_complete"]
    if incomplete_mask.any():
        df.loc[incomplete_mask, "model"] = df.loc[incomplete_mask, "model"] + " *"
        df.loc[incomplete_mask, "Recommendation"] = "(Pending)"

    complete_df = df[df["is_complete"]]
    if complete_df.empty:
        return df

    comm_mask = complete_df["Type"] == "Commercial"
    if comm_mask.any():
        best_comm = complete_df.loc[comm_mask].sort_values(
            "Overall Score", ascending=False
        )
        if not best_comm.empty:
            best_model = best_comm.iloc[0]["model"]
            idx = df[df["model"] == best_model].index[0]
            df.loc[idx, "Recommendation"] = "🏆 Best Commercial"

    local_mask = complete_df["Type"] == "Local"
    if local_mask.any():
        best_local = complete_df.loc[local_mask].sort_values(
            "Overall Score", ascending=False
        )
        if not best_local.empty:
            best_model = best_local.iloc[0]["model"]
            idx = df[df["model"] == best_model].index[0]
            current = df.loc[idx, "Recommendation"]
            df.loc[idx, "Recommendation"] = f"{current} 🥇 Best Local".strip()

    return df


def print_leaderboard_table(leaderboard: pd.DataFrame) -> None:
    """Gibt das Leaderboard gruppiert nach Badges aus."""
    print("\n--- Benchmark Leaderboard ---\n")
    badges_order = ["👑 God Mode", "🏎️ Daily Driver", "🧠 Deep Thinker", "⚖️ Standard"]
    display_fields = [
        "Rank",
        "Recommendation",
        "Model Name",
        "Version",
        "Generation",
        "Total Score",
        "Avg Time (s)",
        "Routine Score",
        "Reasoning Score",
    ]

    for badge in badges_order:
        group = leaderboard[leaderboard["Badge"] == badge]
        if not group.empty:
            print(f"=== {badge.upper()} ===")
            d_cols = [c for c in display_fields if c in group.columns]
            print(group[d_cols].to_string(index=False))
            print("")

    remaining = leaderboard[~leaderboard["Badge"].isin(badges_order)]
    if not remaining.empty:
        print("=== OTHER ===")
        d_cols = [c for c in display_fields if c in remaining.columns]
        print(remaining[d_cols].to_string(index=False))
        print("")

    if "Model Name" in leaderboard.columns and leaderboard["Model Name"].str.contains(r"\*").any():
        print(
            "\n* Model has not completed all benchmarks (excluded from ranking badges)."
        )
