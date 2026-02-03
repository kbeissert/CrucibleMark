"""
Leaderboard formatting and display logic.
Handles badge assignment, speed classification, skill profiling, and console output.
"""
import pandas as pd

# Import constants (could be moved to config, but defined here for now as per spec)
BADGE_GOLD_THRESHOLD = 85.0
BADGE_SILVER_THRESHOLD = 70.0
BADGE_BRONZE_THRESHOLD = 55.0

SPEED_FAST_THRESHOLD = 40.0
SPEED_MEDIUM_THRESHOLD = 80.0

def get_quality_badge(total_score: float) -> str:
    """
    Strict quality tiers based on absolute performance.

    Args:
        total_score: The Total Score of the model.

    Returns:
        Badge emoji and name.
    """
    # Handle NaNs or invalid input
    if pd.isna(total_score):
        return "⚖️ Standard"

    if total_score >= BADGE_GOLD_THRESHOLD:
        return "🏆 Gold"
    if total_score >= BADGE_SILVER_THRESHOLD:
        return "🥈 Silver"
    if total_score >= BADGE_BRONZE_THRESHOLD:
        return "🥉 Bronze"
    return "⚖️ Standard"

def get_speed_class(avg_time: float) -> str:
    """
    Speed classification for use-case recommendations.

    Args:
        avg_time: Average execution time in seconds.

    Returns:
        Speed class label with emoji.
    """
    if pd.isna(avg_time) or avg_time == 0:
        return "-" # Unknown or cached

    if avg_time < SPEED_FAST_THRESHOLD:
        return "⚡ Fast"
    if avg_time < SPEED_MEDIUM_THRESHOLD:
        return "⏱️ Medium"
    return "🐢 Slow"

def generate_skill_profile(row: pd.Series) -> str:
    """
    Generate human-readable use-case recommendation.

    Args:
        row: A row from the leaderboard DataFrame containing scores and speed.

    Returns:
        A short descriptive profile string.
    """
    # Extract scores - adapting column names to match what is likely in the DF
    # The DF columns usually match the "name" in module config.
    # We try to map them safely.
    categories = {
        'Code Quality': row.get('Code Quality Audit', 0),
        'UX Writing': row.get('UX Writing & Microcopy', 0),
        'Documentation': row.get('Documentation Quality', 0),
        'Content': row.get('Content Transformation & Adaption', 0),
        'Cultural': row.get('Cultural Intelligence', 0),
        'Reasoning': row.get('Logical Reasoning', 0)
    }

    # Clean up NaNs and ensure floats
    valid_categories = {}
    for k, v in categories.items():
        try:
            val = float(v)
            if not pd.isna(val) and val > 0:
                valid_categories[k] = val
        except (ValueError, TypeError):
            continue

    if not valid_categories:
        return "Unknown"

    # Find top category
    # If all are close, it's an all-rounder.

    top_cat = max(valid_categories, key=valid_categories.get)
    # top_score = valid_categories[top_cat]

    # Check if all-rounder (all present categories within 10 points)
    # Using 10 points as range based on spec "within 10% range" (assuming points scale 0-100)
    vals = list(valid_categories.values())
    score_range = max(vals) - min(vals)
    is_all_rounder = score_range < 10

    # Speed context
    speed = row.get("Speed Class", "")
    speed_label = "Fast" if "⚡" in speed else "Slow" if "🐢" in speed else "Balanced"

    total_score = row.get("Total Score", 0)

    # Generate profile
    if is_all_rounder:
        if total_score >= 75:
            return f"{speed_label} All-Rounder"
        return f"{speed_label} Generalist"

    # Specialist mapping
    specialist_map = {
        'Code Quality': f"{speed_label} Code Reviewer",
        'UX Writing': f"{speed_label} UX Writer",
        'Documentation': f"{speed_label} Doc Writer",
        'Content': f"{speed_label} Content Adapter",
        'Reasoning': f"Reasoning Specialist ({speed_label.lower()})"
    }

    if top_cat in specialist_map:
        return specialist_map[top_cat]

    return f"{speed_label} Specialist"

def calculate_performance_per_second(total_score: float, avg_time: float) -> float:
    """
    Higher = better value (good score, fast response).
    """
    if pd.isna(avg_time) or avg_time <= 0:
        return 0.0
    if pd.isna(total_score):
        return 0.0

    return round(total_score / avg_time, 2)

def assign_rank_and_badges(df: pd.DataFrame) -> pd.DataFrame:
    """
    Vergibt Rank, Badges, Speed Class und Skill Profile.
    Updates the DataFrame in place / returns modified DF.
    """
    if df.empty:
        return df

    # Rank assignment (assuming df is already sorted by Total Score)
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    df["Rank"] = df.index

    # 1. Badge Assignment
    df["Badge"] = df["Total Score"].apply(get_quality_badge)

    # 2. Speed Class
    df["Speed Class"] = df["Avg Time (s)"].apply(get_speed_class)

    # 3. Apply Skill Profile (requires Speed Class to be present)
    df["Skill Profile"] = df.apply(generate_skill_profile, axis=1)

    # 4. Performance per Second
    df["Performance/s"] = df.apply(
        lambda row: calculate_performance_per_second(row.get("Total Score"), row.get("Avg Time (s)")),
        axis=1
    )

    # Ensure is_complete is boolean
    if "is_complete" in df.columns:
        df["is_complete"] = df["is_complete"].fillna(False).astype(bool)
    else:
        df["is_complete"] = False

    # Mark incomplete
    incomplete_mask = ~df["is_complete"]
    if incomplete_mask.any():
        # Only append * if not already there
        # Check if column is string before using string methods
        df.loc[incomplete_mask, "model"] = df.loc[incomplete_mask, "model"].astype(str).apply(lambda x: x if x.endswith("*") else f"{x} *")

    return df


def print_leaderboard_table(leaderboard: pd.DataFrame) -> None:
    """
    Outputs the leaderboard grouped by Badges using new columns.
    """
    print("\n--- Benchmark Leaderboard (v1.1) ---\n")

    # Desired column order for display
    display_fields = [
        "Rank", "Model Name", "Version", "Badge", "Speed Class", "Skill Profile",
        "Total Score", "Performance/s", "Avg Time (s)", "Cost per 1K",
        "Routine Score", "Reasoning Score", "Tests Run"
    ]

    badges_order = ["🏆 Gold", "🥈 Silver", "🥉 Bronze", "⚖️ Standard"]

    for badge in badges_order:
        group = leaderboard[leaderboard["Badge"] == badge]
        if not group.empty:
            print(f"=== {badge.upper()} ===")
            # Select only columns that exist
            cols = [c for c in display_fields if c in leaderboard.columns]
            print(group[cols].to_string(index=False))
            print("")

    # Handle others (e.g. if badge logic fails or new badges added)
    remaining = leaderboard[~leaderboard["Badge"].isin(badges_order)]
    if not remaining.empty:
        print("=== OTHER ===")
        cols = [c for c in display_fields if c in leaderboard.columns]
        print(remaining[cols].to_string(index=False))
        print("")

    if "Model Name" in leaderboard.columns and leaderboard["Model Name"].str.contains(r"\*").any():
        print(
            "\n* Model has not completed all benchmarks (excluded from strict ranking)."
        )
