"""
Leaderboard formatting and display logic.
Handles badge assignment, speed classification, skill profiling, and console output.
"""

import pandas as pd

from pathlib import Path

# Load config (SSoT: ConfigValidator merged benchmark_config + provider_config).
try:
    from utils.config_validator import ConfigValidator
    _config = ConfigValidator(str(Path("benchmark_config.yaml"))).config
    _tiers = _config.get("scoring_tiers", {})
except Exception:
    _tiers = {}

BADGE_PLATINUM_THRESHOLD = _tiers.get("platinum", {}).get("threshold", 95.0)
BADGE_GOLD_THRESHOLD = _tiers.get("gold", {}).get("threshold", 80.0)
BADGE_SILVER_THRESHOLD = _tiers.get("silver", {}).get("threshold", 65.0)
BADGE_BRONZE_THRESHOLD = _tiers.get("bronze", {}).get("threshold", 50.0)

# --- Klassifikations-Schwellwerte (Review 2026-08-15: vorher Magic Numbers) --
# All-Rounder: Score-Range über alle Kategorien < 12 Punkte (bewusst etwas
# lockerer als 10 — historisch gewachsene Kalibrierung, Änderung wäre eine
# Leaderboard-Klassifikationsänderung).
ALL_ROUNDER_MAX_SCORE_RANGE = 12

# Stabilitäts-Klassifikation (relative Score-Varianz):
STABILITY_UNSTABLE_THRESHOLD = 0.5    # >= 50% Varianz → UNSTABLE
STABILITY_MODERATE_THRESHOLD = 0.35   # >= 35% Varianz → MODERATE

BADGE_PLATINUM_ICON = _tiers.get("platinum", {}).get("badge", "💎 Platinum")
BADGE_GOLD_ICON = _tiers.get("gold", {}).get("badge", "🏆 Gold")
BADGE_SILVER_ICON = _tiers.get("silver", {}).get("badge", "🥈 Silver")
BADGE_BRONZE_ICON = _tiers.get("bronze", {}).get("badge", "🥉 Bronze")
BADGE_STANDARD_ICON = _tiers.get("standard", {}).get("badge", "⚖️ Standard")

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
        return BADGE_STANDARD_ICON

    if total_score >= BADGE_PLATINUM_THRESHOLD:
        return BADGE_PLATINUM_ICON
    if total_score >= BADGE_GOLD_THRESHOLD:
        return BADGE_GOLD_ICON
    if total_score >= BADGE_SILVER_THRESHOLD:
        return BADGE_SILVER_ICON
    if total_score >= BADGE_BRONZE_THRESHOLD:
        return BADGE_BRONZE_ICON
    return BADGE_STANDARD_ICON


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


def _filter_valid_categories(categories: dict) -> dict:
    """Clean up NaNs/invalid scores, ensure floats and keep only >0 values."""
    valid_categories: dict = {}
    for k, v in categories.items():
        try:
            val = float(v)
            if not pd.isna(val) and val > 0:
                valid_categories[k] = val
        except (ValueError, TypeError):
            continue
    return valid_categories


def _resolve_role_from_top_category(top_cat: str) -> str:
    """Map a top-scoring category name to a human-readable skill role label."""
    name_lower = top_cat.lower()
    if "code" in name_lower:
        return "Code Reviewer"
    if "ux" in name_lower:
        return "UX Writer"
    if "doc" in name_lower:
        return "Doc Writer"
    if "content" in name_lower:
        return "Content Adapter"
    if "reasoning" in name_lower:
        return "Reasoning Expert"
    if "cultur" in name_lower:
        return "Cultural Expert"
    if "cli" in name_lower or "devops" in name_lower:
        return "DevOps Expert"
    if "politi" in name_lower:
        return "Policy Expert"
    # Dynamically generate role name from category (e.g. "Security Check" -> "Security Expert")
    first_word = top_cat.split(" ")[0]
    return f"{first_word} Expert"


def get_skill_role(row: pd.Series, cat_cols: list) -> str:
    """
    Determine the skill role (Specialist/All-Rounder type) based on dynamic category scores.
    """
    # Extract dynamic scores
    categories = {col: row.get(col, 0) for col in cat_cols}
    valid_categories = _filter_valid_categories(categories)

    role = "Specialist"  # Default

    if not valid_categories:
        return role

    # Check if all-rounder
    vals = list(valid_categories.values())
    score_range = max(vals) - min(vals)
    is_all_rounder = score_range < ALL_ROUNDER_MAX_SCORE_RANGE

    if is_all_rounder:
        return "All-Rounder"

    # Find top category dynamically
    top_cat = max(valid_categories, key=valid_categories.get)
    return _resolve_role_from_top_category(top_cat)


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
    profile = f"{emoji} {tier_name} {role}" if tier_name and role else f"{tier_raw} {role}".strip()

    # Add Stability Warning (v3.1 Category-Aware Variance)
    try:
        stability = float(row.get("stability_score", 0.0))

        # Thresholds: > 50% (0.5) is UNSTABLE (High Variance)
        # 30-50% is MODERATE (Normal for diverse local benchmarks)
        if stability >= STABILITY_UNSTABLE_THRESHOLD:
            profile += " ❌ UNSTABLE"
        elif stability >= STABILITY_MODERATE_THRESHOLD:
            # Only flag heavily if variance is significant but not critical
            pass

    except (ValueError, TypeError):
        pass

    return profile


def assign_rank_and_badges(df: pd.DataFrame, cat_cols: list | None = None) -> pd.DataFrame:
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

    # Append Nano marker for sub-4B models (smartphone/RPi floor tier)
    if "Size Class" in df.columns:
        df.loc[df["Size Class"] == "Nano", "Badge"] = (
            df.loc[df["Size Class"] == "Nano", "Badge"] + " 🔬"
        )

    # 2. Performance Tier (Calculated but not always displayed raw)
    # Using Avg Time column name safely
    if "Avg Task Duration (s)" in df.columns:
        df["Performance Tier"] = df["Avg Task Duration (s)"].apply(get_performance_tier)

    # 3. Skill Profile (Role Only)
    df["Skill Profile"] = df.apply(lambda row: get_skill_role(row, cat_cols), axis=1)

    # 4. Speed Profile (Merged Tier + Skill + Warnings)
    df["Speed Profile"] = df.apply(format_speed_profile, axis=1)

    # 5. Tokens/s already aggregated by score_calculator — no recalculation needed here

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
        "Tokens/s",
        "Avg Task Duration (s)",
        # Note: Cost, specific scores, etc. hidden to fit width
        # But user requested Cost per 1K in text description, let's keep it if possible
    ]

    # Add Cost if space suggests, but 120 chars is tight. Try adding it.
    display_fields.append("Cost per 1K")
    display_fields.append("LLM Judge Avg")
    display_fields.append("LLM Judge Coverage")

    # We remove Routine/Reasoning Score from main view as requested

    badges_order = [BADGE_PLATINUM_ICON, BADGE_GOLD_ICON, BADGE_SILVER_ICON, BADGE_BRONZE_ICON, BADGE_STANDARD_ICON]

    for badge in badges_order:
        # Match both the plain badge and its Nano variant
        nano_badge = f"{badge} 🔬"
        group = leaderboard[leaderboard["Badge"].isin([badge, nano_badge])]
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
