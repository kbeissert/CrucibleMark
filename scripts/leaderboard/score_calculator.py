"""
Core scoring and aggregation logic for leaderboard.
Calculates Routine vs Reasoning scores, aggregates stats, and classifies models.
"""

import sys
from typing import Any

import pandas as pd
import yaml

# Import constants and config logic
from .config import ROOT_DIR, config

# Ensure root dir in path for local imports
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Removed unused imports from utils.module_registry as functionality is passed via config


# ==============================================================================
# 1b. PRICE LOOKUP (from model cards, cost_limits.yaml as legacy fallback)
# ==============================================================================

def _build_price_lookup() -> dict[str, float]:
    """
    Builds a flat {model_id: output_cost_per_1k} dict.

    Primary source: model card JSON files (benchmark_scores/model_cards/*.json).
    Legacy fallback: cost_limits.yaml entries for models without a card yet.
    Card prices take precedence; cost_limits.yaml is only used for models
    not yet covered by a card (e.g. cloud proxies, uncommon models).

    Defense-in-Depth: Cards with deployment_type in LOCAL_DEPLOYMENT_TYPES
    (e.g. "localweights") default to 0.0 if output_price_per_1m is missing
    or null. Lokale Modelle haben keine API-Kosten — eine leere Preis-Zelle
    verfälscht die Benchmark-Cost-Berechnung.
    """
    import json as _json

    # Whitelist der "rein lokalen" deployment_types. Hybrid-Typen wie
    # "open-weights-cloud-available" oder "cloud-and-local" zählen NICHT als
    # lokal — diese Modelle haben einen Cloud-Preis und sollen nur diesen zeigen.
    LOCAL_DEPLOYMENT_TYPES = frozenset({"localweights", "local-weights"})

    card_dir = ROOT_DIR / "benchmark_scores" / "model_cards"
    lookup: dict[str, float] = {}

    # 1. Model cards (primary SSoT)
    for card_path in card_dir.glob("*.json"):
        try:
            with open(card_path, encoding="utf-8") as f:
                card = _json.load(f)
            if not isinstance(card, dict):
                continue
            model_id = card.get("model_id")
            if not model_id:
                continue
            price_per_m = card.get("output_price_per_1m")
            if isinstance(price_per_m, (int, float)):
                lookup[model_id] = float(price_per_m) / 1000.0
            elif card.get("deployment_type") in LOCAL_DEPLOYMENT_TYPES:
                # Lokales Modell ohne expliziten Preis → 0.0 (Defense-in-Depth)
                lookup[model_id] = 0.0
        except (OSError, _json.JSONDecodeError):
            continue

    # 2. cost_limits.yaml legacy fallback (models not yet in a card)
    cost_limits_path = ROOT_DIR / "config" / "cost_limits.yaml"
    try:
        with open(cost_limits_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        providers = data.get("providers", {})
        for _provider, models in providers.items():
            if not isinstance(models, dict):
                continue
            for model_name, model_data in models.items():
                if not isinstance(model_data, dict):
                    continue
                price = model_data.get("output_cost_per_1k")
                if isinstance(price, (int, float)) and model_name not in lookup:
                    lookup[model_name] = float(price)
    except (OSError, yaml.YAMLError):
        pass

    return lookup


def _lookup_price(model_ver: str, model_name: str, lookup: dict[str, float]) -> float | None:
    """
    Resolves output_cost_per_1k for a model.

    Match priority:
      1. Exact match on model_version
      2. Exact match on full model name (e.g. 'z-ai/glm-5-turbo-20260315')
      3. Prefix match on full model name, longest key first
         (e.g. 'z-ai/glm-5-turbo-20260315' → 'z-ai/glm-5-turbo')
    """
    if model_ver and model_ver in lookup:
        return lookup[model_ver]
    if model_name and model_name in lookup:
        return lookup[model_name]
    if model_name:
        for key in sorted(lookup.keys(), key=len, reverse=True):
            if model_name.startswith(key):
                return lookup[key]
    return None

_PRICE_LOOKUP: dict[str, float] | None = None


def _get_price_lookup() -> dict[str, float]:
    """Returns cached price lookup dict (lazy init)."""
    # pylint: disable=global-statement
    global _PRICE_LOOKUP  # noqa: PLW0603
    if _PRICE_LOOKUP is None:
        _PRICE_LOOKUP = _build_price_lookup()
    return _PRICE_LOOKUP


# ==============================================================================
# 2. HELPERS: SCORING (Granular Contribution)
# ==============================================================================


def _get_row_contribution(
    row: pd.Series,
    asset_contrib_map: dict[str, dict[str, float]],
    cat_to_config: dict[str, Any],
) -> tuple[float, float, float, float]:
    """
    Helper to calculate routine/reasoning contribution AND weights for a single row.
    Returns: (contrib_routine, contrib_reasoning, weight_routine, weight_reasoning)
    """

    # Helper to get weights
    def get_weights_from_map_or_fallback():
        asset_id = row.get("asset_id")
        if asset_id in asset_contrib_map:
            c = asset_contrib_map[asset_id]
            return float(c.get("routine", 0.0)), float(c.get("reasoning", 0.0))

        # Module-Level Default
        cat = row.get("category", "")
        mod_conf = cat_to_config.get(cat, {})
        def_contrib = mod_conf.get("default_contribution", {})
        return float(def_contrib.get("routine", 0.0)), float(
            def_contrib.get("reasoning", 0.0)
        )

    w_routine, w_reasoning = get_weights_from_map_or_fallback()
    pct = float(row.get("percentage", 0))

    # 1. Try CSV Values first
    try:
        r_raw = row.get("routine_contribution")
        l_raw = row.get("reasoning_contribution")

        if (
            pd.notna(r_raw)
            and pd.notna(l_raw)
            and str(r_raw).strip()
            and str(l_raw).strip()
        ):
            # SUCCESS: Use pre-calculated values
            # Return weights from config map because extracting them from contrib/pct is unsafe if pct=0
            return float(r_raw), float(l_raw), w_routine, w_reasoning
    except (ValueError, TypeError):
        pass

    # 2. Variable Calculation Fallback
    return pct * w_routine, pct * w_reasoning, w_routine, w_reasoning


def _calculate_group_scores(
    df: pd.DataFrame, modules_config: dict[str, Any]
) -> pd.DataFrame:
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
    df_calc = df_calc[
        df_calc["category"].apply(
            lambda c: cat_to_config.get(c, {}).get("enable_scoring", True)
        )
    ]

    if df_calc.empty:
        return pd.DataFrame()

    # 2. Build Asset Map
    asset_contrib_map = {}
    for mod_data in cat_to_config.values():
        for b in mod_data.get("benchmarks", []):
            if "score_contribution" in b and "id" in b:
                asset_contrib_map[b["id"]] = b["score_contribution"]

    # 2b. Build module-weight scale factors (self-normalizing, Subset-safe)
    # module_weight / sum_of_config_weights_in_that_module → scale per asset row.
    # Falls module_weight=None (kein Eintrag), scale=1.0 (Rückwärtskompatibilität).
    def _module_scale(mod_data: dict[str, Any]) -> float:
        module_weight = mod_data.get("module_weight")
        if module_weight is None:
            return 1.0
        benchmarks = mod_data.get("benchmarks", [])
        default_contrib = mod_data.get("default_contribution", {"routine": 0.0, "reasoning": 0.0})
        default_sum = float(default_contrib.get("routine", 0.0)) + float(default_contrib.get("reasoning", 0.0))
        config_weight_sum = 0.0
        for b in benchmarks:
            sc = b.get("score_contribution")
            if sc:
                config_weight_sum += float(sc.get("routine", 0.0)) + float(sc.get("reasoning", 0.0))
            else:
                config_weight_sum += default_sum
        if config_weight_sum <= 0:
            config_weight_sum = max(float(mod_data.get("assets_count", 1)) * max(default_sum, 1.0), 1.0)
        return float(module_weight) / config_weight_sum

    module_weight_scales: dict[str, float] = {
        cat_name: _module_scale(mod_data)
        for cat_name, mod_data in cat_to_config.items()
    }

    # 3. Apply Scoring
    contribs = df_calc.apply(
        lambda r: _get_row_contribution(r, asset_contrib_map, cat_to_config),
        axis=1,
        result_type="expand",
    )

    if contribs.empty:
        df_calc["final_routine"] = 0.0
        df_calc["final_reasoning"] = 0.0
        df_calc["weight_routine"] = 0.0
        df_calc["weight_reasoning"] = 0.0
    else:
        # Apply module-weight scaling so that module_weight controls relative influence,
        # independent of asset count. Result stays 0–100 (self-normalizing via weighted avg).
        scale = df_calc["category"].map(lambda c: module_weight_scales.get(c, 1.0))
        df_calc["final_routine"] = contribs[0] * scale
        df_calc["final_reasoning"] = contribs[1] * scale
        df_calc["weight_routine"] = contribs[2] * scale
        df_calc["weight_reasoning"] = contribs[3] * scale

    # 4. Aggregation: Sum / Sum of Weights
    scores = (
        df_calc.groupby(["model", "model_version"])
        .agg(
            sum_routine=("final_routine", "sum"),
            sum_reasoning=("final_reasoning", "sum"),
            total_weight_routine=("weight_routine", "sum"),
            total_weight_reasoning=("weight_reasoning", "sum"),
            count=("asset_id", "count"),
        )
        .reset_index()
    )

    # Calculate Total Weight (Global denominator for components)
    scores["total_weight_global"] = (
        scores["total_weight_routine"] + scores["total_weight_reasoning"]
    )

    # Calculate Component Scores (Weighted Contribution to Total)
    # This ensures Routine Score + Reasoning Score = Total Score
    scores["Routine Score"] = scores.apply(
        lambda x: (
            x["sum_routine"] / x["total_weight_global"]
            if x["total_weight_global"] > 0
            else 0
        ),
        axis=1,
    )
    scores["Reasoning Score"] = scores.apply(
        lambda x: (
            x["sum_reasoning"] / x["total_weight_global"]
            if x["total_weight_global"] > 0
            else 0
        ),
        axis=1,
    )

    # Return intermediate sums for weighted total calculation
    return scores[
        [
            "model",
            "model_version",
            "Routine Score",
            "Reasoning Score",
            "sum_routine",
            "sum_reasoning",
            "total_weight_routine",
            "total_weight_reasoning",
        ]
    ]


# ==============================================================================
# 3. HELPERS: STATS AGGREGATION
# ==============================================================================


def _aggregate_basic_stats(
    df: pd.DataFrame, modules_config: dict[str, Any]
) -> pd.DataFrame:
    """Aggregates percentage, time and counts. Handles non-scoring modules correctly."""

    # Filter for scoring assets only
    cat_to_scoring = {}
    for mod_key, mod_data in modules_config.items():
        name = mod_data.get("name", mod_key)
        cat_to_scoring[name] = mod_data.get("enable_scoring", True)

    def is_scoring_asset(row):
        cat = row.get("category", "")
        return cat_to_scoring.get(cat, True)

    # Ensure numeric columns for aggregation (Fix: prevent string concatenation in sum)
    cols_to_numeric = ["execution_time", "cost_usd", "tokens_used", "tokens_per_second", "load_time"]
    for col in cols_to_numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "llm_judge_score" in df.columns:
        df["llm_judge_score"] = pd.to_numeric(df["llm_judge_score"], errors="coerce")

    # 1. Base Stats (Presence, Time) - From ALL valid runs (scoring + info)

    # SPLIT AGGREGATION:
    # - Execution Time: Excluding "System" probes (to avoid skewing averages with 0.1s dummy values)
    # - Load Time: Using ALL rows (System probe carries the Max Load Time)

    # A) Standard Metrics (without System Probe)
    df_metrics = df[df["category"] != "System"].copy()

    base_aggs = {"execution_time": "mean", "asset_id": "count"}

    if "cost_usd" in df_metrics.columns:
        base_aggs["cost_usd"] = "sum"
    if "tokens_used" in df_metrics.columns:
        base_aggs["tokens_used"] = "sum"
    if "tokens_per_second" in df_metrics.columns:
        df_metrics["tokens_per_second"] = pd.to_numeric(
            df_metrics["tokens_per_second"], errors="coerce"
        )
        base_aggs["tokens_per_second"] = "mean"

    stats_metrics = (
        df_metrics.groupby(["model", "model_version", "type"])
        .agg(base_aggs)
        .reset_index()
    )

    # B) Load Time (Include System Probe because it has the Cold Start data)
    stats_load = pd.DataFrame()
    if "load_time" in df.columns:
        stats_load = (
            df.groupby(["model", "model_version", "type"])["load_time"]
            .max()
            .reset_index()
        )

    # Merge results if load stats exist
    if not stats_load.empty:
        base_stats = pd.merge(
            stats_metrics, stats_load, on=["model", "model_version", "type"], how="left"
        )
    else:
        base_stats = stats_metrics

    # Enhanced Time Stats (Max, P95, P99, Timeouts)
    # Define custom aggregation functions
    def p95(x):
        return x.quantile(0.95)

    def p99(x):
        return x.quantile(0.99)

    def count_timeouts(x):
        return (x > 120.0).sum()

    # Create separate stats for time to avoid complex multi-index flattening
    # time_aggs = {
    #    "execution_time": ["mean", "max", p95, p99, count_timeouts]
    # }

    # Calculate rigorous time stats
    time_stats = (
        df.groupby(["model", "model_version", "type"])["execution_time"]
        .agg(
            Avg_Time="mean",
            Max_Time="max",
            P95_Time=p95,
            P99_Time=p99,
            Timeout_Count=count_timeouts,
        )
        .reset_index()
    )

    # Merge time stats into base stats
    base_stats = pd.merge(base_stats, time_stats, on=["model", "model_version", "type"])

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
        stats = pd.merge(
            base_stats, score_stats, on=["model", "model_version", "type"], how="left"
        )
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

    # 3. Judge Stats - From valid/applicable runs only
    if "llm_judge_score" in df.columns:
        # Load applicable_modules from config
        llm_judge_cfg = config.get("llm_judge", {})
        applicable_modules = llm_judge_cfg.get("applicable_modules", [])

        # Map module UUIDs to their category names
        applicable_categories = set()
        for mod_key, mod_data in modules_config.items():
            if mod_key in applicable_modules:
                name = mod_data.get("name", mod_key)
                applicable_categories.add(name)

        # Filter dataframe for coverage and mean computation
        df_judge = df[df["category"].isin(applicable_categories)]

        # Judge-Skip-Zeilen aus Coverage-Berechnung ausschließen:
        # judge_progress_status=⚠️ Judge: skip (zu kurz/abgelehnt) bedeutet absichtlich
        # übersprungen, nicht fehlgeschlagen → zählt nicht gegen Coverage.
        if "judge_progress_status" in df_judge.columns:
            df_judge = df_judge[
                ~df_judge["judge_progress_status"].str.contains("skip", na=False, case=False)
            ]

        def calc_coverage(x):
            return x.notna().sum() / len(x) if len(x) > 0 else 0.0

        judge_stats = (
            df_judge.groupby(["model", "model_version", "type"])["llm_judge_score"]
            .agg(llm_judge_avg="mean", judge_coverage=calc_coverage)
            .reset_index()
        )
        stats = pd.merge(
            stats, judge_stats, on=["model", "model_version", "type"], how="left"
        )
        # Ensure we fill judge_coverage with 0.0 if not available for a model
        stats["judge_coverage"] = stats["judge_coverage"].fillna(0.0)
    else:
        stats["llm_judge_avg"] = None
        stats["judge_coverage"] = 0.0

    return stats


def _calculate_run_counts(
    df: pd.DataFrame, modules_config: dict[str, Any]
) -> pd.DataFrame:
    """Calculates 'Tests Run' using logic overrides (e.g. PC = 9 tests)."""

    name_to_override = {}
    expected_assets = 0
    counting_cats = set()

    for _, mod_data in modules_config.items():
        if not mod_data.get("enabled", True):
            continue

        name = mod_data.get("name")
        # Only count assets towards expected total if scoring is enabled OR if explicit display count is set
        if mod_data.get("enable_scoring", True) or mod_data.get("display_test_count"):
            expected_assets += mod_data.get("assets_count", 0)
            counting_cats.add(name)

        if mod_data.get("display_test_count"):
            name_to_override[name] = int(mod_data.get("display_test_count"))

    def calculate_logical_run_count(sub_df):
        count = 0
        cats = sub_df["category"].unique()
        for cat in cats:
            if cat not in counting_cats:
                continue
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


def _calculate_stability_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates stability score based on average Category Variance Coefficient.
    CV = StdDev / Mean.
    Higher Score (>0.5) = High Variance (Unstable/Variable).
    Lower Score (<0.3) = Low Variance (Stable).
    """
    # 1. Filter valid execution times
    # Ensure numeric
    df_perf = df.copy()
    if "execution_time" not in df_perf.columns:
        return pd.DataFrame()

    df_perf["execution_time"] = pd.to_numeric(
        df_perf["execution_time"], errors="coerce"
    )
    df_perf = df_perf[df_perf["execution_time"] > 0]

    if df_perf.empty:
        return pd.DataFrame()

    # 2. Calculate PER-ASSET Stats (Mean, Std)
    # Group by Model, Version, Type AND Asset ID (compare runs of same asset)
    # v3.1 Fix: Use per-asset variance instead of per-category to avoid flagging models
    # as unstable simply because they have diverse task durations (e.g. 5s vs 50s tasks).
    asset_stats = (
        df_perf.groupby(["model", "model_version", "type", "asset_id"])[
            "execution_time"
        ]
        .agg(asset_mean="mean", asset_std="std")
        .reset_index()
    )

    # Handle single-item variance (std is NaN) -> CV is 0 (Stable)
    asset_stats["asset_std"] = asset_stats["asset_std"].fillna(0)

    # 3. Calculate normalized variability per asset.
    #    Uses σ / global_mean instead of CV (σ/μ) to avoid penalizing
    #    inherently fast tasks (e.g. 0.1s ± 0.05s CV=0.5 vs 10s ± 1s CV=0.1).
    global_mean = df_perf["execution_time"].mean()
    if global_mean > 0:
        asset_stats["asset_nv"] = asset_stats["asset_std"] / global_mean
    else:
        asset_stats["asset_nv"] = 0.0

    # 4. Average the normalized variabilities across all assets (Asset-Aware Stability)
    stability_stats = (
        asset_stats.groupby(["model", "model_version", "type"])["asset_nv"]
        .agg(stability_score="mean")
        .reset_index()
    )

    # stability_score is e.g. 0.26 (26%), 0.69 (69%)
    return stability_stats


# ==============================================================================
# 4. MAIN ORCHESTRATOR
# ==============================================================================


def calculate_scores(
    df: pd.DataFrame, modules_config: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
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

    df_all = df.copy()

    # --- Assign Categories ---
    def get_category_name(asset_id: str) -> str:
        # Special Case: System Probes
        if asset_id in ("system_warmup_probe", "warmup_probe"):
            return "System"

        for mod_key, mod_data in modules_config.items():
            if "prefix" in mod_data and str(asset_id).startswith(
                str(mod_data["prefix"])
            ):
                return str(mod_data.get("name", mod_key))
            if str(asset_id).startswith(mod_key):
                return str(mod_data.get("name", mod_key))
        return "Other"

    df_all["category"] = df_all["asset_id"].apply(get_category_name)
    # Filter "Other" but KEEP "System"
    df_all = df_all[(df_all["category"] != "Other")]

    # pylint: disable=too-many-locals,too-many-statements
    # Include all valid completions in scoring (not just 'success').
    # language_mismatch, truncated, verbose_outlier all carry real scores
    # and are treated as non-error by the runner (unified_runner.py).
    _valid_statuses = {"success", "language_mismatch", "truncated", "verbose_outlier", "refusal"}
    df_success = df_all[df_all["status"].isin(_valid_statuses)].copy()
    # --- Performance Ratio Calculation (Removed, using raw) ---
    df_success["performance_ratio"] = df_success["percentage"]

    # --- Aggregation ---
    stats = _aggregate_basic_stats(df_success, modules_config)
    # Note: uses Full DF (incl non-scoring)
    run_counts = _calculate_run_counts(df_all, modules_config)

    # scoring_df: only assets from modules with enable_scoring=True (same base as Total Score)
    cat_to_scoring = {
        mod_data.get("name", mod_key): mod_data.get("enable_scoring", True)
        for mod_key, mod_data in modules_config.items()
    }
    scoring_df = df_success[df_success["category"].map(lambda c: cat_to_scoring.get(c, True))]

    # Merge Counts
    result = pd.merge(
        stats, run_counts, on=["model", "model_version", "type"], how="left"
    )

    # Completion Status
    # Using 'max' of expected_assets column, as it's constant
    expected = (
        result["expected_assets"].max() if "expected_assets" in result.columns else 0
    )
    result["is_complete"] = result["logical_count"] >= expected
    # Mypy safely converts logical count to string through apply to avoid + Series warning
    result["Tests Run"] = result["logical_count"].apply(lambda x: str(int(x)) + "/" + str(expected))
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

    # --- Override tokens_used with scoring-only total ---
    # _aggregate_basic_stats() sums tokens across ALL non-system rows (incl. Political Compass).
    # Overwrite here with scoring-only sum so that Tokens Total has the same static base
    # as Total Score — re-test runs (e.g. Political Compass retests) don't distort the value.
    if "tokens_used" in scoring_df.columns and "tokens_used" in result.columns:
        token_totals = (
            scoring_df.groupby(["model", "model_version"])["tokens_used"]
            .sum()
            .reset_index()
        )
        result = result.drop(columns=["tokens_used"])
        result = pd.merge(result, token_totals, on=["model", "model_version"], how="left")

    # --- Token Stats per Module ---
    # Uses scoring_df (same base as Total Score) to ensure a static, comparable
    # token count. Political Compass and other non-scoring modules are excluded
    # because they have variable re-test counts, which would distort cross-model
    # comparisons.
    if "tokens_used" in scoring_df.columns:
        token_by_module = (
            scoring_df.groupby(["model", "model_version", "category"])["tokens_used"]
            .sum()
            .unstack()
            .reset_index()
        )
        token_by_module.columns = [
            f"Tokens: {col}" if col not in ("model", "model_version") else col
            for col in token_by_module.columns
        ]
        result = pd.merge(result, token_by_module, on=["model", "model_version"], how="left")

    # --- Routine vs Reasoning (v2.1: Granular Weights) ---
    # Calculates scores based on per-asset routine/reasoning split
    granular_scores = _calculate_group_scores(df_success, modules_config)

    if not granular_scores.empty:
        # Merge granular scores
        result = pd.merge(
            result, granular_scores, on=["model", "model_version"], how="left"
        )
    else:
        # Fallback if granular calc fails (should not happen)
        result["Routine Score"] = 0.0
        result["Reasoning Score"] = 0.0

    # Ensure they are not NaNs
    result["Routine Score"] = result["Routine Score"].fillna(0.0)
    result["Reasoning Score"] = result["Reasoning Score"].fillna(0.0)

    # --- Stability Score (New v3.1 Logic) ---
    stability = _calculate_stability_score(df_success)
    if not stability.empty:
        result = pd.merge(
            result, stability, on=["model", "model_version", "type"], how="left"
        )
    else:
        result["stability_score"] = 0.0

    # Total Score Calculation (Volume-Weighted)
    # Uses the actual weight of routine vs reasoning tasks in the run benchmark
    def calc_weighted_total(row):
        w_routine = row.get("total_weight_routine", 0)
        w_reasoning = row.get("total_weight_reasoning", 0)
        sum_routine = row.get("sum_routine", 0)
        sum_reasoning = row.get("sum_reasoning", 0)

        total_weight = w_routine + w_reasoning
        total_sum = sum_routine + sum_reasoning

        if total_weight > 0:
            return total_sum / total_weight
        else:
            # Fallback if no weights (should not happen)
            return 0.0

    result["Total Score"] = result.apply(calc_weighted_total, axis=1)

    # Cost per 1K Output Tokens — from model cards (cost_limits.yaml as legacy fallback).
    # Uses the published output_price_per_1m for each known model, converted to per-1K.
    # Local-only models (deployment_type ∈ {"localweights", "local-weights"}) default to 0.0
    # even without an explicit price (see _build_price_lookup Defense-in-Depth).
    # Models without a card price AND not marked local-only (e.g. cloud-only,
    # hybrid cloud-and-local) receive None → empty in the leaderboard.
    price_lookup = _get_price_lookup()

    def calc_cost_per_1k_tokens(row: pd.Series) -> float | None:
        # Match by model_version, then full model name, then prefix (longest key first)
        model_ver = str(row.get("model_version", "") or "").strip()
        model_name = str(row.get("model", "") or "").strip()
        return _lookup_price(model_ver, model_name, price_lookup)

    result["Cost per 1K (USD)"] = result.apply(calc_cost_per_1k_tokens, axis=1)

    # Benchmark Cost (USD) — absolute cost for the full benchmark run.
    # Primary:  (Tokens Total / 1000) × Cost per 1K (USD)  [known price from model card or cost_limits.yaml]
    # Fallback: cost_usd (sum from benchmark CSVs) — covers date-suffixed OpenRouter models
    #           and any other model whose name doesn't match the price lookup exactly.
    if "tokens_used" in result.columns:
        def calc_benchmark_cost(row: pd.Series) -> float | None:
            price = row.get("Cost per 1K (USD)")
            tokens = row.get("tokens_used")
            try:
                price_f = float(price)  # type: ignore[arg-type]
                tokens_f = float(tokens)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                price_f = float("nan")
                tokens_f = float("nan")
            if not pd.isna(price_f) and not pd.isna(tokens_f) and tokens_f > 0:
                return round((tokens_f / 1000) * price_f, 4)
            # Fallback: use recorded cost_usd sum (covers OpenRouter + date-suffix models)
            try:
                fallback = float(row.get("cost_usd") or 0)  # type: ignore[arg-type]
                return round(fallback, 4) if fallback > 0 else None
            except (TypeError, ValueError):
                return None

        result["Benchmark Cost (USD)"] = result.apply(calc_benchmark_cost, axis=1)

    # Efficiency Index
    result["Efficiency_Index"] = result.apply(
        lambda row: (
            row["Routine Score"] / row["execution_time"]
            if row.get("execution_time", 0) > 0
            else 0
        ),
        axis=1,
    )

    # Remove temporary calculation columns
    cols_to_drop = [
        "sum_routine",
        "sum_reasoning",
        "total_weight_routine",
        "total_weight_reasoning",
        "Avg_Time",
    ]
    result = result.drop(columns=[c for c in cols_to_drop if c in result.columns])

    # --- Cleanup Renaming ---
    result = result.rename(
        columns={
            "percentage": "Overall Score",
            "performance_ratio": "Performance Ratio",
            "execution_time": "Avg Task Duration (s)",
            "load_time": "Initial Load Time (s)",
            "Max_Time": "Max Time (s)",
            "P95_Time": "P95 Time (s)",
            "P99_Time": "P99 Time (s)",
            "Timeout_Count": "Timeout Count",
            "type": "Type",
            "llm_judge_avg": "LLM Judge Avg",
            "judge_coverage": "LLM Judge Coverage",
            "tokens_used": "Tokens Total",
            "tokens_per_second": "Tokens/s",
        }
    )

    # Sort by Total Score (v1.1)
    if "Total Score" in result.columns:
        result = result.sort_values("Total Score", ascending=False)
    elif "Overall Score" in result.columns:
        result = result.sort_values("Overall Score", ascending=False)

    return result, cat_stats
