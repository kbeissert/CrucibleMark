"""
Core scoring and aggregation logic for leaderboard.
Calculates Routine vs Reasoning scores, aggregates stats, and classifies models.
"""
import sys
from typing import Any, Dict, Tuple

import pandas as pd

# Import constants and config logic
from .config import ROOT_DIR, load_model_registry
from .data_loader import load_golden_references

# Ensure root dir in path for local imports
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Removed unused imports from utils.module_registry as functionality is passed via config

try:
    # Attempt absolute import first (if running from root)
    from scripts.classify_generation import GenerationClassifier
except ImportError:
    try:
        # Fallback to local import (if running from scripts dir)
        from classify_generation import GenerationClassifier
    except ImportError:
        GenerationClassifier = None


# ==============================================================================
# 1. HELPERS: GENERATION CLASSIFICATION
# ==============================================================================

def _suggest_generation(model_name: str) -> str:
    """Heuristic for generation detection (Fallback)."""
    name = str(model_name).lower()
    if any(t in name for t in ["o1", "o3", "deepseek-r1:671b", "deepseek-r1-671b"]):
        return "Gen 3 (Pure Reasoner)"
    if any(t in name for t in ["deepseek-r1", "phi4", "phi-4", "qwq", "reasoning"]):
        return "Gen 2 (Distilled Reasoner)"
    return "Gen 1 (Pattern Matcher)"


def _get_model_generation(model_name: str) -> str:
    """Gets Generation from Registry (Cached load) or suggests it."""
    registry = load_model_registry()
    models = registry.get("models", {})
    if model_name in models:
        return models[model_name].get("generation", "Unknown")
    return _suggest_generation(model_name)


def _apply_classification(result: pd.DataFrame) -> pd.DataFrame:
    """Applies generation classification to the result DataFrame."""
    if "model" not in result.columns:
        return result

    classifier = GenerationClassifier() if GenerationClassifier else None
    if classifier:
        def get_gen(row):
            stats = {
                "avg_time": row.get("Avg Time (s)", 0),
                "reasoning_score": row.get("Reasoning Score", 0),
                "code_quality": row.get("Code Quality Audit", 0),
            }
            res = classifier.classify(row["model"], stats)
            if res.get("flag_for_review"):
                print(f"⚠️  REVIEW NEEDED: {row['model']} -> {res['reason']}")
            return res["generation"]

        result["Generation"] = result.apply(get_gen, axis=1)
    else:
        result["Generation"] = result["model"].apply(_get_model_generation)

    # Reorder Generation column
    cols_order = result.columns.tolist()
    if "Generation" in cols_order and "model" in cols_order:
        cols_order.remove("Generation")
        model_index = cols_order.index("model")
        cols_order.insert(model_index + 1, "Generation")
        result = result[cols_order]

    return result


# ==============================================================================
# 2. HELPERS: SCORING (Granular Contribution)
# ==============================================================================

def _get_row_contribution(
    row: pd.Series,
    asset_contrib_map: Dict[str, Dict[str, float]],
    cat_to_config: Dict[str, Any]
) -> Tuple[float, float]:
    """Helper to calculate routine/reasoning contribution for a single row."""
    # 1. Check if values explicitly in columns
    try:
        r_raw = row.get("routine_contribution")
        if pd.notna(r_raw) and str(r_raw).strip():
            r_val = float(r_raw)
        else:
            r_val = None

        l_raw = row.get("reasoning_contribution")
        if pd.notna(l_raw) and str(l_raw).strip():
            l_val = float(l_raw)
        else:
            l_val = None

        if r_val is not None and l_val is not None:
            return r_val, l_val
    except (ValueError, TypeError):
        pass

    pct = float(row.get("percentage", 0))

    # 2. Check Granular Config (Asset Level)
    asset_id = row.get("asset_id")
    if asset_id in asset_contrib_map:
        contrib = asset_contrib_map[asset_id]
        return pct * float(contrib.get("routine", 0.0)), pct * float(contrib.get("reasoning", 0.0))

    # 3. Fallback: Module-Level Default
    cat = row.get("category", "")
    mod_conf = cat_to_config.get(cat, {})
    def_contrib = mod_conf.get("default_contribution", {})

    return (
        pct * float(def_contrib.get("routine", 0.0)),
        pct * float(def_contrib.get("reasoning", 0.0)),
    )    


def _calculate_group_scores(df: pd.DataFrame, modules_config: Dict[str, Any]) -> pd.DataFrame:
    """
    Calculates Routine vs Reasoning scores using granular contributions (v3 logic).
    Returns DataFrame with [model, model_version, Routine Score, Reasoning Score].
    """
    df_calc = df.copy()

    # 1. Active Modules Filter
    cat_to_config = {
        mod_data.get("name", k): mod_data
        for k, mod_data in modules_config.items()
        if mod_data.get("enabled", True)
    }

    active_cats = set(cat_to_config.keys())
    df_calc = df_calc[df_calc["category"].isin(active_cats)]

    # Filter out non-scoring modules
    df_calc = df_calc[df_calc["category"].apply(
        lambda c: cat_to_config.get(c, {}).get("enable_scoring", True)
    )]

    if df_calc.empty:
        return pd.DataFrame()

    # 2. Build Asset Map
    asset_contrib_map = {}
    for mod_data in cat_to_config.values():
        for b in mod_data.get("benchmarks", []):
            if "score_contribution" in b and "id" in b:
                asset_contrib_map[b["id"]] = b["score_contribution"]

    # 3. Apply Scoring
    contribs = df_calc.apply(
        lambda r: _get_row_contribution(r, asset_contrib_map, cat_to_config),
        axis=1,
        result_type="expand"
    )

    if contribs.empty:
        df_calc["final_routine"] = 0.0
        df_calc["final_reasoning"] = 0.0
    else:
        df_calc["final_routine"] = contribs[0]
        df_calc["final_reasoning"] = contribs[1]

    # 4. Aggregation: Sum / Count
    scores = df_calc.groupby(["model", "model_version"]).agg(
        sum_routine=("final_routine", "sum"),
        sum_reasoning=("final_reasoning", "sum"),
        count=("asset_id", "count")
    ).reset_index()

    scores["Routine Score"] = scores.apply(
        lambda x: x["sum_routine"] / x["count"] if x["count"] > 0 else 0, axis=1
    )
    scores["Reasoning Score"] = scores.apply(
        lambda x: x["sum_reasoning"] / x["count"] if x["count"] > 0 else 0, axis=1
    )

    return scores[["model", "model_version", "Routine Score", "Reasoning Score"]]


# ==============================================================================
# 3. HELPERS: STATS AGGREGATION
# ==============================================================================

def _aggregate_basic_stats(df: pd.DataFrame, modules_config: Dict[str, Any]) -> pd.DataFrame:
    """Aggregates percentage, time and counts. Handles non-scoring modules correctly."""

    # Filter for scoring assets only
    cat_to_scoring = {}
    for mod_key, mod_data in modules_config.items():
        name = mod_data.get("name", mod_key)
        cat_to_scoring[name] = mod_data.get("enable_scoring", True)

    def is_scoring_asset(row):
        cat = row.get("category", "")
        return cat_to_scoring.get(cat, True)

    # 1. Base Stats (Presence, Time) - From ALL valid runs (scoring + info)
    # This ensures models with ONLY info modules (like Political Compass) are listed.
    base_aggs = {
        "execution_time": "mean", 
        "asset_id": "count"
    }
    if "timestamp" in df.columns:
        base_aggs["timestamp"] = "max"

    base_stats = (
        df.groupby(["model", "model_version", "type"])
        .agg(base_aggs)
        .reset_index()
    )

    # 2. Scoring Stats (Percentage) - From SCORING runs only
    scoring_df = df[df.apply(is_scoring_asset, axis=1)]
    
    if not scoring_df.empty:
        score_aggs = {"percentage": "mean"}
        if "performance_ratio" in df.columns:
            score_aggs["performance_ratio"] = "mean"
            
        score_stats = (
            scoring_df.groupby(["model", "model_version", "type"])
            .agg(score_aggs)
            .reset_index()
        )
        # Merge scoring stats into base stats
        stats = pd.merge(base_stats, score_stats, on=["model", "model_version", "type"], how="left")
    else:
        stats = base_stats
        stats["percentage"] = 0.0
        if "performance_ratio" in df.columns:
            stats["performance_ratio"] = 0.0

    # Fill NaNs (for models with only info modules)
    if "percentage" in stats.columns:
        stats["percentage"] = stats["percentage"].fillna(0.0)
    if "performance_ratio" in stats.columns:
        stats["performance_ratio"] = stats["performance_ratio"].fillna(0.0)

    return stats


def _calculate_run_counts(df: pd.DataFrame, modules_config: Dict[str, Any]) -> pd.DataFrame:
    """Calculates 'Tests Run' using logic overrides (e.g. PC = 9 tests)."""

    name_to_override = {}
    expected_assets = 0

    for _, mod_data in modules_config.items():
        if not mod_data.get("enabled", True):
            continue

        name = mod_data.get("name")
        # Only count assets towards expected total if scoring is enabled
        if mod_data.get("enable_scoring", True):
            expected_assets += mod_data.get("assets_count", 0)

        if mod_data.get("display_test_count"):
            name_to_override[name] = int(mod_data.get("display_test_count"))

    def calculate_logical_run_count(sub_df):
        count = 0
        cats = sub_df["category"].unique()
        for cat in cats:
            row_count = len(sub_df[sub_df["category"] == cat])
            if cat in name_to_override:
                if row_count > 0:
                    count += name_to_override[cat]
            else:
                count += row_count
        return count

    run_counts = (
        df.groupby(["model", "model_version", "type"])
        .apply(calculate_logical_run_count)
        .reset_index(name="logical_count")
    )


    run_counts["expected_assets"] = expected_assets
    # Note: adding expected_assets as column for easy merge, though it's constant

    return run_counts


# ==============================================================================
# 4. MAIN ORCHESTRATOR
# ==============================================================================

def calculate_scores(
    df: pd.DataFrame, modules_config: Dict[str, Any]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main entry point for scoring calculations.

    Args:
        df: Raw benchmark data (pandas DataFrame)
        modules_config: Configuration dictionary for active modules

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: 
            1. Main leaderboard stats (model-level)
            2. Category stats (stats per module category)
    """

    df_success = df[df["status"] == "success"].copy()

    # --- Performance Ratio Calculation ---
    refs = load_golden_references()
    baseline = 0

    def get_performance_ratio(row):
        asset_id = row.get("asset_id")
        raw = row.get("percentage")
        if pd.isna(raw):
            return 0.0
        ref = refs.get(asset_id)
        if ref and ref > baseline:
            numerator = max(0, raw - baseline)
            denominator = ref - baseline
            return (numerator / denominator) * 100.0
        return raw

    df_success["performance_ratio"] = df_success.apply(get_performance_ratio, axis=1)

    # --- Assign Categories ---
    def get_category_name(asset_id: str) -> str:
        for mod_key, mod_data in modules_config.items():
            if "prefix" in mod_data and str(asset_id).startswith(str(mod_data["prefix"])):
                return str(mod_data.get("name", mod_key))
            if str(asset_id).startswith(mod_key):
                return str(mod_data.get("name", mod_key))
        return "Other"

    df_success["category"] = df_success["asset_id"].apply(get_category_name)
    df_success = df_success[df_success["category"] != "Other"]

    # --- Aggregation ---
    stats = _aggregate_basic_stats(df_success, modules_config)
    # Note: uses Full DF (incl non-scoring)
    run_counts = _calculate_run_counts(df_success, modules_config)
    
    # Merge Counts
    result = pd.merge(
        stats, 
        run_counts, 
        on=["model", "model_version", "type"], 
        how="left"
    )

    # Completion Status
    # Using 'max' of expected_assets column, as it's constant
    expected = result["expected_assets"].max() if "expected_assets" in result.columns else 0
    result["is_complete"] = result["logical_count"] >= expected
    result["Tests Run"] = result["logical_count"].astype(str) + "/" + str(expected)
    if "expected_assets" in result.columns:
        result = result.drop(columns=["expected_assets"])

    # --- Category Stats ---
    cat_stats = (
        df_success.groupby(["model", "model_version", "category"])["percentage"]
        .mean()
        .unstack()
        .reset_index()
    )
    result = pd.merge(result, cat_stats, on=["model", "model_version"], how="left")

    # --- Routine vs Reasoning ---
    group_stats = _calculate_group_scores(df_success, modules_config)
    if not group_stats.empty:
        result = pd.merge(result, group_stats, on=["model", "model_version"], how="left")
    
    # Fill defaults
    for col in ["Routine Score", "Reasoning Score"]:
        if col not in result.columns:
            result[col] = 0.0

    # Efficiency Index
    result["Efficiency_Index"] = result.apply(
        lambda row: row["Routine Score"] / row["execution_time"]
        if row.get("execution_time", 0) > 0
        else 0,
        axis=1,
    )

    # --- Cleanup Renaming ---
    result = result.rename(
        columns={
            "percentage": "Overall Score",
            "performance_ratio": "Performance Ratio",
            "execution_time": "Avg Time (s)",
            "type": "Type",
        }
    )

    # --- Classification ---
    result = _apply_classification(result)

    # Sort
    if "Overall Score" in result.columns:
        result = result.sort_values("Overall Score", ascending=False)

    return result, cat_stats
