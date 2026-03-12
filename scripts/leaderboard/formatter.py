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


def get_performance_tier(avg_time: float) -> str:
    """
    Classifies the model into a performance tier based on average execution time.

    Tiers:
    - ⚡ Real-Time (< 20s): Suitable for autocomplete/copilot
    - ⏱️ Interactive (20s - 45s): Suitable for chat
    - 🕐 Batch (45s - 120s): Background tasks only
    - ❌ Unusable (>= 120s): Disqualified for production
    """
    if pd.isna(avg_time) or avg_time <= 0:
        return "Unknown"

    if avg_time < 20.0:
        return "⚡ Real-Time"
    if avg_time < 45.0:
        return "⏱️ Interactive"
    if avg_time < 120.0:
        return "🕐 Batch"
    return "❌ Unusable"


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
        return "-"  # Unknown or cached

    if avg_time < SPEED_FAST_THRESHOLD:
        return "⚡ Fast"
    if avg_time < SPEED_MEDIUM_THRESHOLD:
        return "⏱️ Medium"
    return "🐢 Slow"


def get_skill_role(row: pd.Series, cat_cols: list) -> str:
    """
    Determine the skill role (Specialist/All-Rounder type) based on dynamic category scores.
    """
    # Extract dynamic scores
    categories = {col: row.get(col, 0) for col in cat_cols}

    # Clean up NaNs and ensure floats
    valid_categories = {}
    for k, v in categories.items():
        try:
            val = float(v)
            if not pd.isna(val) and val > 0:
                valid_categories[k] = val
        except (ValueError, TypeError):
            continue

    role = "Specialist"  # Default

    if valid_categories:
        # Check if all-rounder
        vals = list(valid_categories.values())
        score_range = max(vals) - min(vals)
        is_all_rounder = score_range < 12  # Slightly looser than 10

        if is_all_rounder:
            role = "All-Rounder"
        else:
            # Find top category dynamically
            top_cat = max(valid_categories, key=valid_categories.get)

            # Simple heuristic mapping for dynamic categories
            name_lower = top_cat.lower()
            if "code" in name_lower:
                role = "Code Reviewer"
            elif "ux" in name_lower:
                role = "UX Writer"
            elif "doc" in name_lower:
                role = "Doc Writer"
            elif "content" in name_lower:
                role = "Content Adapter"
            elif "reasoning" in name_lower:
                role = "Reasoning Expert"
            elif "cultur" in name_lower:
                role = "Cultural Expert"
            elif "cli" in name_lower or "devops" in name_lower:
                role = "DevOps Expert"
            elif "politi" in name_lower:
                role = "Policy Expert"
            else:
                # Dynamically generate role name from category (e.g. "Security Check" -> "Security Expert")
                first_word = top_cat.split(" ")[0]
                role = f"{first_word} Expert"

    return role


def format_speed_profile(row: pd.Series) -> str:
    """
    Generate merged 'Speed Profile' (Tier Emoji + Tier Name + Role + Warnings).
    """
    tier_raw = str(row.get("Performance Tier", ""))
    role = str(row.get("Skill Profile", ""))

    # Extract Emoji and Base Tier Name
    parts = tier_raw.split(maxsplit=1)
    emoji = parts[0] if parts else ""
    tier_name = parts[1] if len(parts) > 1 else ""

    # Construct Base Profile
    if tier_name and role:
        profile = f"{emoji} {tier_name} {role}"
    else:
        profile = f"{tier_raw} {role}".strip()

    # Add Stability Warning (v3.1 Category-Aware Variance)
    try:
        stability = float(row.get("stability_score", 0.0))

        # Thresholds: > 50% (0.5) is UNSTABLE (High Variance)
        # 30-50% is MODERATE (Normal for diverse local benchmarks)
        if stability >= 0.5:
            profile += " ❌ UNSTABLE"
        elif stability >= 0.35:
            # Only flag heavily if variance is significant but not critical
            pass

    except (ValueError, TypeError):
        pass

    return profile


def calculate_performance_per_second(total_score: float, avg_time: float) -> float:
    """
    Higher = better value (good score, fast response).
    """
    if pd.isna(avg_time) or avg_time <= 0:
        return 0.0
    if pd.isna(total_score):
        return 0.0

    return round(total_score / avg_time, 2)


def assign_rank_and_badges(df: pd.DataFrame, cat_cols: list = None) -> pd.DataFrame:
    """
    Vergibt Rank, Badges und Speed Profile.
    Updates the DataFrame in place / returns modified DF.
    """
    if df.empty:
        return df

    if cat_cols is None:
        cat_cols = []

    # Rank assignment (assuming df is already sorted by Total Score)
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    df["Rank"] = df.index

    # 1. Badge Assignment
    df["Badge"] = df["Total Score"].apply(get_quality_badge)

    # 2. Performance Tier (Calculated but not always displayed raw)
    # Using Avg Time column name safely
    if "Avg Time (s)" in df.columns:
        df["Performance Tier"] = df["Avg Time (s)"].apply(get_performance_tier)

    # 3. Skill Profile (Role Only)
    df["Skill Profile"] = df.apply(lambda row: get_skill_role(row, cat_cols), axis=1)

    # 4. Speed Profile (Merged Tier + Skill + Warnings)
    df["Speed Profile"] = df.apply(format_speed_profile, axis=1)

    # 5. Performance per Second
    df["Performance/s"] = df.apply(
        lambda row: calculate_performance_per_second(
            row.get("Total Score"), row.get("Avg Time (s)")
        ),
        axis=1,
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
        df.loc[incomplete_mask, "model"] = (
            df.loc[incomplete_mask, "model"]
            .astype(str)
            .apply(lambda x: x if x.endswith("*") else f"{x} *")
        )

    return df


def print_leaderboard_table(leaderboard: pd.DataFrame) -> None:
    """
    Outputs the leaderboard grouped by Badges using new columns.
    Optimized for ~120 char width.
    """
    print("\n--- Benchmark Leaderboard (v1.2) ---\n")

    # Compact column list for main display
    display_fields = [
        "Rank",
        "Model Name",
        "Version",
        "Badge",
        "Speed Profile",
        "Total Score",
        "Performance/s",
        "Avg Time (s)",
        # Note: Cost, specific scores, etc. hidden to fit width
        # But user requested Cost per 1K in text description, let's keep it if possible
    ]

    # Add Cost if space suggests, but 120 chars is tight. Try adding it.
    display_fields.append("Cost per 1K")
    display_fields.append("LLM Judge Avg")
    display_fields.append("LLM Judge Coverage")

    # We remove Routine/Reasoning Score from main view as requested

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

    if (
        "Model Name" in leaderboard.columns
        and leaderboard["Model Name"].str.contains(r"\*").any()
    ):
        print(
            "\n* Model has not completed all benchmarks (excluded from strict ranking)."
        )
