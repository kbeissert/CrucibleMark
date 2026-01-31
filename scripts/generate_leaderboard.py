#!/usr/bin/env python3
"""
Generiert ein Leaderboard aus den Benchmark-Ergebnissen.
Führt lokale und kommerzielle Ergebnisse zusammen und berechnet Durchschnittswerte.
"""

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# pylint: disable=import-error
import yaml
import pandas as pd
# pylint: enable=import-error

# Pfad für Imports setzen
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# pylint: disable=wrong-import-position, import-error
from utils.config_validator import ConfigValidator  # noqa: E402
from utils.csv_recovery import parse_row_robust, get_csv_header_idx  # noqa: E402
from utils.module_registry import get_active_modules # noqa: E402
# pylint: enable=wrong-import-position, import-error

# Konstanten - Defaults (Falls Module Config fehlt)
DEFAULT_THRESHOLDS = {
    "god_mode_routine": 85,
    "god_mode_reasoning": 80,
    "daily_driver_routine": 80,
    "deep_thinker_reasoning": 80,
}
REGISTRY_FILE = ROOT_DIR / "model_registry.yaml"

# Konfiguration laden
validator = ConfigValidator()
config = validator.config
output_config = config.get("output", {})
lb_config = config.get("leaderboard", {}).get("thresholds", DEFAULT_THRESHOLDS)

SCORES_DIR = Path(output_config.get("directory", "benchmark_scores"))
COMMERCIAL_CSV = Path(
    output_config.get("commercial_csv", SCORES_DIR / "commercial_models_benchmark.csv")
)
LOCAL_CSV = Path(
    output_config.get("local_models_csv", SCORES_DIR / "local_models_benchmark.csv")
)
GOLDEN_CSV = Path(
    output_config.get(
        "golden_standard_csv", SCORES_DIR / "golden_standard_benchmark.csv"
    )
)
OUTPUT_CSV = SCORES_DIR / "benchmark_leaderboard.csv"


# ==============================================================================
# DATA LOADING
# ==============================================================================


def _process_csv(dfs: List[pd.DataFrame], filepath: Path, type_label: str) -> None:
    """Helper to process a single CSV File."""
    if not filepath.exists():
        return

    try:
        rows = []
        with open(filepath, encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                return

            header_idx = get_csv_header_idx(header)
            required = ["model", "asset_id", "percentage"]
            if not all(r in header_idx for r in required):
                return

            for parts in reader:
                row = parse_row_robust(parts, header_idx)
                if row:
                    rows.append(row)

        if rows:
            df_new = pd.DataFrame(rows)
            df_new["type"] = type_label
            dfs.append(df_new)
    except (OSError, csv.Error) as e:
        print(f"Fehler beim Parsen von {filepath}: {e}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Fallback für unerwartete Fehler beim manuellen Parsing
        print(f"Unerwarteter Fehler in {filepath}: {e}")


def load_data() -> pd.DataFrame:
    """Lädt und normalisiert Daten aus allen CSVs"""
    dfs: List[pd.DataFrame] = []

    _process_csv(dfs, COMMERCIAL_CSV, "Commercial")
    _process_csv(dfs, LOCAL_CSV, "Local")

    if not dfs:
        print("Keine Benchmark-Daten gefunden.")
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)
    df["percentage"] = pd.to_numeric(df["percentage"], errors="coerce")
    df["execution_time"] = pd.to_numeric(df["execution_time"], errors="coerce")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # If model_version is missing (e.g. newly loaded CSV didn't have it yet), fill with "unknown"
    if "model_version" not in df.columns:
        df["model_version"] = "unknown"
    else:
        df["model_version"] = df["model_version"].fillna("unknown")

    # Sort by timestamp to ensure 'last' is actually the most recent
    df = df.sort_values("timestamp")
    
    # DEDUPLICATION LOGIC with VERSIONING:
    # We now group by model AND model_version.
    # This means 'mistral:latest' (v1) and 'mistral:latest' (v2) are treated as DIFFERENT entities.
    df = df.drop_duplicates(subset=["model", "model_version", "type", "asset_id"], keep="last")
    return df


# ==============================================================================
# REGISTRY & GENERATION
# ==============================================================================


def load_model_registry() -> Dict[str, Any]:
    """Lädt die Modell-Registry aus YAML."""
    if not REGISTRY_FILE.exists():
        return {"models": {}}
    try:
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if data else {"models": {}}
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"⚠️ Fehler beim Laden der Registry {REGISTRY_FILE}: {e}")
        return {"models": {}}


def save_model_registry(registry_data: Dict[str, Any]):
    """Speichert die Registry zurück in YAML."""
    try:
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            yaml.dump(registry_data, f, sort_keys=False, indent=2, allow_unicode=True)
        print(f"✅ Registry aktualisiert: {REGISTRY_FILE}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"⚠️ Fehler beim Speichern der Registry: {e}")


def _suggest_generation(model_name: str) -> str:
    """Heuristik für Generation-Erkennung (Fallback)."""
    name = str(model_name).lower()
    if any(t in name for t in ["o1", "o3", "deepseek-r1:671b", "deepseek-r1-671b"]):
        return "Gen 3 (Pure Reasoner)"
    if any(t in name for t in ["deepseek-r1", "phi4", "phi-4", "qwq", "reasoning"]):
        return "Gen 2 (Distilled Reasoner)"
    return "Gen 1 (Pattern Matcher)"


def _get_model_generation(model_name: str) -> str:
    """Holt Generation aus Registry (Cached load)."""
    registry = load_model_registry()
    models = registry.get("models", {})
    if model_name in models:
        return models[model_name].get("generation", "Unknown")
    return _suggest_generation(model_name)


# ==============================================================================
# SCORING & BADGES
# ==============================================================================


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


def _aggregate_stats(df: pd.DataFrame, modules_config: Dict[str, Any]) -> pd.DataFrame:
    """Aggregates basic stats and checks completion against config."""
    
    # Calculate Expected Assets Count from Config (excluding info/batch if needed?)
    expected_assets = 0
    
    for _, mod_data in modules_config.items():
        if not mod_data.get("enabled", True):
            continue
            
        group = mod_data.get("score_group", "")
        
        # If group is 'info', we don't require it for 'Completion' status
        if group == "info":
            continue
            
        # DYNAMIC COUNTING: Check actual files on disk instead of config value
        # This prevents "Tests Run" mismatch when new assets are added but config not updated.
        try:
            mod_path = ROOT_DIR / mod_data.get("path", "")
            assets_dir = mod_path / "assets"
            if assets_dir.exists():
                # Count valid asset files (ignoring hidden/system files)
                real_count = len([f for f in assets_dir.glob("*.yaml") if not f.name.startswith(".")])
                if real_count > 0:
                    expected_assets += real_count
                    continue
        except Exception:
            pass

        # Fallback to manual config count if dynamic lookup fails
        count = mod_data.get("assets_count", 0)
        expected_assets += count

    # Filter out non-scoring modules from SCORING aggregation (Total Score)
    cat_to_scoring = {}
    for mod_key, mod_data in modules_config.items():
        name = mod_data.get("name", mod_key)
        cat_to_scoring[name] = mod_data.get("enable_scoring", True)
        
    def is_scoring_asset(row):
        cat = row.get("category", "")
        return cat_to_scoring.get(cat, True)

    scoring_df = df[df.apply(is_scoring_asset, axis=1)]
    
    # Check if normalized column exists
    aggs = {"percentage": "mean", "execution_time": "mean", "asset_id": "count"}
    if "performance_ratio" in df.columns:
        aggs["performance_ratio"] = "mean"
    
    # NEW: Capture latest timestamp for "Last Seen" Date
    if "timestamp" in df.columns:
        aggs["timestamp"] = "max"

    # Aggregate stats -> This creates the "Total Score" (percentage)
    # UPDATED: Group also by 'model_version'
    stats = (
        scoring_df.groupby(["model", "model_version", "type"])
        .agg(aggs)
        .reset_index()
    )
    
    # Calculate completion status
    stats["is_complete"] = stats["asset_id"] >= expected_assets
    stats["Tests Run"] = stats["asset_id"].astype(str) + "/" + str(expected_assets)
    
    return stats


def _calculate_group_scores(df: pd.DataFrame, modules_config: Dict[str, Any]) -> pd.DataFrame:
    """Calculates Routine vs Reasoning scores based on Config Score Groups."""
    
    # Map category names to score groups
def _calculate_group_scores(df: pd.DataFrame, modules_config: Dict[str, Any]) -> pd.DataFrame:
    """Calculates Routine vs Reasoning scores using granular contributions (v3 logic)."""
    
    df_calc = df.copy()
    
    # 1. Ensure columns exist
    if "routine_contribution" not in df_calc.columns:
        df_calc["routine_contribution"] = pd.NA
    if "reasoning_contribution" not in df_calc.columns:
        df_calc["reasoning_contribution"] = pd.NA

    # 2. Filter for active modules (needed for list checks)
    active_categories = set()
    cat_to_config = {}

    for mod_key, mod_data in modules_config.items():
        if not mod_data.get("enabled", True):
            continue
        name = mod_data.get("name", mod_key)
        active_categories.add(name)
        cat_to_config[name] = mod_data
    
    # Filter for active modules only
    df_calc = df_calc[df_calc["category"].isin(active_categories)]
    
    # Filter out non-scoring modules from denominator/numerators (Routine vs Reasoning Score)
    # IMPORTANT: We keep them in the main DF for display, but remove them here for metric calc.
    def is_scoring_mod(cat):
        return cat_to_config.get(cat, {}).get("enable_scoring", True)

    df_calc = df_calc[df_calc["category"].map(is_scoring_mod)]

    # 2b. Build Asset-Level Contribution Map (v3 Granular Scoring)
    asset_contrib_map: Dict[str, Dict[str, float]] = {}
    for mod_key, mod_data in modules_config.items():
        if not mod_data.get("enabled", True):
            continue
        benchmarks = mod_data.get("benchmarks", [])
        for b in benchmarks:
            if "score_contribution" in b and "id" in b:
                asset_contrib_map[b["id"]] = b["score_contribution"]

    # 3. Apply Fallback Logic (Backward Compatibility)
    def fill_contributions(row):
        # 1. Check if values explicitly in columns (future proofing)
        r = row.get("routine_contribution")
        l = row.get("reasoning_contribution")
        
        # Safe float conversion handling empty strings
        def to_float_safe(val):
            try:
                if pd.isna(val) or str(val).strip() == "":
                    return None
                return float(val)
            except (ValueError, TypeError):
                return None

        r_val = to_float_safe(r)
        l_val = to_float_safe(l)
        
        # If both present, use them
        if r_val is not None and l_val is not None:
            return r_val, l_val

        # 2. Check Granular Config (Asset Level)
        pct = float(row.get("percentage", 0))
        asset_id = row.get("asset_id")
        
        if asset_id in asset_contrib_map:
             contrib = asset_contrib_map[asset_id]
             f_routine = float(contrib.get("routine", 0.0))
             f_reasoning = float(contrib.get("reasoning", 0.0))
             return pct * f_routine, pct * f_reasoning
            
        # 3. Fallback: Use Module-Level Default Contribution
        cat = row.get("category", "")
        mod_conf = cat_to_config.get(cat, {})
        def_contrib = mod_conf.get("default_contribution", {})
        
        d_routine = float(def_contrib.get("routine", 0.0))
        d_reasoning = float(def_contrib.get("reasoning", 0.0))
        
        return pct * d_routine, pct * d_reasoning

    # If df_calc is empty after filtering (e.g., only non-scoring modules ran like PoliticalCompass),
    # then contribs will be an empty DataFrame. Direct assignment will fail with KeyError if result_type='expand'
    # didn't generate columns 0/1 properly.
    if df_calc.empty:
        return pd.DataFrame() # Return empty GroupStats

    contribs = df_calc.apply(fill_contributions, axis=1, result_type='expand')
    
    # Safety Check: If there are no rows, apply returns empty DF with no columns
    if contribs.empty:
         df_calc["final_routine"] = 0.0
         df_calc["final_reasoning"] = 0.0
    else:
        df_calc["final_routine"] = contribs[0]
        df_calc["final_reasoning"] = contribs[1]

    # 4. Aggregation: Sum / Count
    # Routine Score = Sum(Routine Contribs) / Count(Benchmarks)
    # This standardizes the score to 0-100 range regardless of mix.
    scores = df_calc.groupby(["model", "model_version"]).agg(
        sum_routine=("final_routine", "sum"),
        sum_reasoning=("final_reasoning", "sum"),
        count=("asset_id", "count")
    ).reset_index()
    
    # Avoid division by zero
    scores["Routine Score"] = scores.apply(
        lambda x: x["sum_routine"] / x["count"] if x["count"] > 0 else 0, axis=1
    )
    scores["Reasoning Score"] = scores.apply(
        lambda x: x["sum_reasoning"] / x["count"] if x["count"] > 0 else 0, axis=1
    )
    
    return scores[["model", "model_version", "Routine Score", "Reasoning Score"]]



try:
    # Attempt absolute import first (if running from root)
    from scripts.classify_generation import GenerationClassifier
except ImportError:
    try:
        # Fallback to local import (if running from scripts dir)
        from classify_generation import GenerationClassifier
    except ImportError:
        GenerationClassifier = None


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


def _format_metrics(
    result: pd.DataFrame, cat_stats: pd.DataFrame, modules_config: Dict[str, Any]
) -> Tuple[pd.DataFrame, List[str]]:
    """Rounds metrics and identifies category columns."""
    # Rounding
    for col in [
        "Overall Score",
        "Performance Ratio",
        "Avg Time (s)",
        "Routine Score",
        "Reasoning Score",
        "Efficiency_Index",
    ]:
        if col in result.columns:
            result[col] = result[col].round(2)

    # Categories identification
    cat_cols = []
    for mod_key, mod_data in modules_config.items():
        name = mod_data.get("name", mod_key)
        if name in result.columns:
            cat_cols.append(name)

    # STRICT MODE: We do NOT add columns that are not in config.
    # This ensures that removed modules disappear from the leaderboard immediately.
    # The 'Other' category or legacy columns in CSV are ignored.

    # Filter `cat_cols` based on enabled modules and their scoring configuration.
    # If a module has `enable_scoring: false` (like Political Compass),
    # its name should NOT be in `cat_cols` (which are used for numeric scores).
    
    scoring_cat_cols = []
    
    for mod_key, mod_data in modules_config.items():
        if not mod_data.get("enabled", True):
            continue
            
        display_name = mod_data.get("name", mod_key)
        
        # Only add to list of numeric metric columns if scoring is enabled
        if mod_data.get("enable_scoring", True):
             if display_name in cat_cols:
                 scoring_cat_cols.append(display_name)
    
    # Replace the broad list with the filtered list
    cat_cols = scoring_cat_cols

    # Round category columns (Handle Pending)
    # Note: `cat_cols` now only contains scoring modules.
    for col in cat_cols:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors="coerce")
            result[col] = result[col].round(2).astype(object).fillna("Pending")

    return result, cat_cols


def _enrich_from_csv_source(
    result: pd.DataFrame,
    label: str,
    source_config: Dict[str, Any]
) -> pd.DataFrame:
    """
    Generic Enrichment: Loads data from a custom CSV based on Config.
    Supports joining, filtering, and value templating.
    """
    filename = source_config.get("file")
    if not filename:
        return result

    file_path = SCORES_DIR / filename
    if not file_path.exists():
        # Add column with missing value if file not found
        fallback = source_config.get("missing_value", "Pending")
        result[label] = fallback
        return result

    try:
        source_df = pd.read_csv(file_path)
        
        # 1. Deduplication / Version Handling
        if "model" in source_df.columns:
            if "model_version" not in source_df.columns:
                source_df["model_version"] = "unknown"
            source_df["model_version"] = source_df["model_version"].fillna("unknown")
            
        # 2. Key Filtering (e.g. run_id == AVG)
        filters = source_config.get("filter", {})
        for col, val in filters.items():
            if col in source_df.columns:
                source_df = source_df[source_df[col] == val]

        # 3. Deduplicate (keep last entry per model/version)
        if "model" in source_df.columns:
             source_df = source_df.drop_duplicates(subset=["model", "model_version"], keep="last")

        # 4. Value Construction (JSON Object Access OR Templating)
        template = source_config.get("value_template")
        json_key = source_config.get("key")
        
        def safe_format(row):
            try:
                # Option A: JSON Object Access (Structured Data)
                if json_key and "metrics_json" in row:
                    try:
                        metrics = json.loads(row["metrics_json"])
                        # Support dot notation (e.g. "labels.x")
                        val = metrics
                        for k in json_key.split('.'):
                            val = val.get(k, {})
                        
                        if isinstance(val, (dict, list)):
                            return json.dumps(val, ensure_ascii=False)
                        return str(val) if val is not None else ""
                    except (json.JSONDecodeError, AttributeError):
                        return "Error (JSON)"
                
                # Option B: Legacy String Templating
                if template:
                    # Convert row to dict, ensure all values are strings for safe substitution
                    data = row.to_dict()
                    return template.format(**data)
                
                return ""
            except KeyError:
                return "Error (Key)"
            except Exception:
                return "Error"

        if template or json_key:
             source_df[label] = source_df.apply(safe_format, axis=1)
        else:
             source_df[label] = ""

        # 5. Merge
        cols_to_merge = ["model", "model_version", label]
        
        # Check if columns exist
        available_cols = [c for c in cols_to_merge if c in source_df.columns]
        if len(available_cols) < 3: # Need at least model keys + target
            return result
            
        merge_subset = source_df[available_cols]
        
        # Drop if exists in result (overwrite logic)
        if label in result.columns:
            result = result.drop(columns=[label])
            
        result = result.merge(merge_subset, on=["model", "model_version"], how="left")
        
        # Fill Missing
        fallback = source_config.get("missing_value", "Pending")
        result[label] = result[label].fillna(fallback)

    except Exception as e:
        print(f"Generic CSV Merge Error ({filename}): {e}")
        if label not in result.columns:
             result[label] = "Error"
             
    return result


def _merge_custom_module_data(
    result: pd.DataFrame, cat_cols: List[str], modules_config: Dict[str, Any]
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Merges custom/additional data columns for modules defined in their config.
    Iterates over all enabled modules and checks for 'source' definition in 'columns'.
    """
    
    # Needs valid result frame
    if result.empty:
        return result, cat_cols

    # Access full registry configuration to get deep 'integration' block
    # Note: `modules_config` from calculate_metrics is simplified.
    # We load the full registry logic again or pass deeper config?
    # Actually, let's load active modules again to be sure we get the full nested config.
    # Performance impact is negligible.
    
    active_modules_data = get_active_modules(config)
    
    for mod_id, mod_meta, mod_int_config in active_modules_data:
        # Check if enabled
        if not mod_int_config.get("enabled", True): # Default enabled?
            # mod_int_config usually comes from file, defaults to dict. 
            # Check modules_config for enabled state
            if not modules_config.get(mod_id, {}).get("enabled", True):
                continue
        
        # Parse Columns Config
        integration = mod_int_config.get("integration", {})
        lb_config = integration.get("leaderboard", {})
        columns_def = lb_config.get("columns", [])
        
        for col_def in columns_def:
            source = col_def.get("source")
            if source:
                label = col_def.get("label", col_def.get("id"))
                
                # Perform Generic Enrichment
                result = _enrich_from_csv_source(result, label, source)
                
                # Add to Cat Cols for display order
                if label not in cat_cols:
                    cat_cols.append(label)

    return result, cat_cols

# NOTE: _enrich_political_compass_data is REMOVED/OBSOLETED by above generic function.

def _enrich_political_compass_data(
    result: pd.DataFrame, cat_cols: List[str], mod_key: str, mod_data: Dict[str, Any]
) -> Tuple[pd.DataFrame, List[str]]:
    """Legacy Placeholder - Do not use."""
    return result, cat_cols



# pylint: disable=too-many-branches, too-many-statements, too-many-locals
def _finalize_result_df(
    result: pd.DataFrame, cat_stats: pd.DataFrame, modules_config: Dict[str, Any]
) -> Tuple[pd.DataFrame, List[str]]:
    """Finalisiert das Ergebnis-DataFrame."""
    result = result.rename(
        columns={
            "percentage": "Overall Score",
            "performance_ratio": "Performance Ratio",
            "execution_time": "Avg Time (s)",
            "type": "Type",
        }
    )

    result = _apply_classification(result)

    # Sort by Overall Score descending (User Request)
    sort_col = "Overall Score"
    result = result.sort_values(sort_col, ascending=False)

    result, cat_cols = _format_metrics(result, cat_stats, modules_config)
    
    # Generic Hook for Custom Module Data
    result, cat_cols = _merge_custom_module_data(result, cat_cols, modules_config)

    return result, cat_cols


# ==============================================================================
# METRIC CALCULATION
# ==============================================================================

def load_golden_references() -> Dict[str, float]:
    """Lädt die Referenz-Scores pro Asset aus dem Golden Standard CSV."""
    refs = {}
    if not GOLDEN_CSV.exists():
        return refs

    try:
        # Check if file is empty or readable
        with open(GOLDEN_CSV, "r", encoding="utf-8") as f:
             first_line = f.readline()
             if not first_line:
                 return refs

        df = pd.read_csv(GOLDEN_CSV, on_bad_lines='skip')

        # Filter for success
        if "status" in df.columns:
            df = df[df["status"] == "success"]

        # Ensure timestamp
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df = df.sort_values("timestamp")

        # Keep latest per asset_id
        if "asset_id" in df.columns and "percentage" in df.columns:
            latest = df.drop_duplicates(subset=["asset_id"], keep="last")
            for _, row in latest.iterrows():
                if pd.notna(row["percentage"]):
                    refs[row["asset_id"]] = float(row["percentage"])

    except Exception as e:
        print(f"⚠️ Warnung: Konnte Golden Standards nicht laden: {e}")

    return refs


# pylint: disable=too-many-locals
def calculate_metrics(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Berechnet Scores pro Modell inkl. Meta-Metriken"""
    
    # ---------------------------------------------------------
    # NEW: Load modules via Registry (Phase 3)
    # ---------------------------------------------------------
    active_modules_data = get_active_modules(config)
    modules_config = {}
    
    for mod_id, mod_meta, mod_int_config in active_modules_data:
        # Merge benchmark_config metadata with internal module config
        # Priority: Internal Config > Benchmark Config
        
        # Extract Leaderboard info from Internal Config
        integration = mod_int_config.get("integration", {})
        lb_config = integration.get("leaderboard", {})
        
        # Determine Display Name
        # If columns are defined, use the label of the first column as the main module name
        display_name = mod_meta.get("name", mod_id)
        if lb_config.get("columns"):
             # Use the label of the first column as the module name/header in the simplified view
             display_name = lb_config.get("columns")[0].get("label", display_name)
        elif mod_int_config.get("metadata", {}).get("name"):
             display_name = mod_int_config.get("metadata", {}).get("name")
             
        # Determine Scoring Config (SSOT v3)
        # integration.leaderboard.enable_scoring (bool)
        # integration.leaderboard.default_contribution (dict)
        
        lb_config = integration.get("leaderboard", {})
        
        # Determine Display Name
        display_name = mod_meta.get("name", mod_id)
        if lb_config.get("columns"):
             display_name = lb_config.get("columns")[0].get("label", display_name)
        elif mod_int_config.get("metadata", {}).get("name"):
             display_name = mod_int_config.get("metadata", {}).get("name")
             
        # Scoring Enabled? (Default True, unless explicitly False)
        # "Info" modules from old config map to False
        enable_scoring = lb_config.get("enable_scoring", True)
        if mod_meta.get("score_group") == "info" or lb_config.get("score_group") == "info":
            enable_scoring = False
            
        # Default Contribution
        # Used if an asset has no granular scoring defined
        default_contrib = lb_config.get("default_contribution", {"routine": 0.0, "reasoning": 0.0})
        
        # Determine Assets Count
        execution = mod_int_config.get("execution", {})
        assets_count = execution.get("assets_count", mod_meta.get("assets_count", 0))

        mod_entry = {
            "name": display_name,
            "enabled": True,
            "enable_scoring": enable_scoring,
            "default_contribution": default_contrib,
            "assets_count": assets_count,
            "path": mod_meta.get("path", ""),
            "benchmarks": mod_int_config.get("benchmarks", [])
        }
        
        if mod_meta.get("prefix"):
            mod_entry["prefix"] = mod_meta.get("prefix")
            
        modules_config[mod_id] = mod_entry

    # Debug: Print modules config keys and lookup check
    # print("Modules Config Keys:", list(modules_config.keys()))

    df_success = df[df["status"] == "success"].copy()

    # --- DEDUPLICATION & VERSION UNIFICATION (FIX DUPLICATE MODELS) ---
    # 1. Convert timestamp
    if "timestamp" in df_success.columns:
        df_success["timestamp"] = pd.to_datetime(df_success["timestamp"], errors="coerce")

    # 2. Sort by Model, Asset, Timestamp (Newest first)
    sort_cols = ["model", "asset_id"]
    if "timestamp" in df_success.columns:
        sort_cols.append("timestamp")
        # Ascending for model/asset, Descending for timestamp
        ascending_vals = [True, True, False]
        df_success = df_success.sort_values(by=sort_cols, ascending=ascending_vals)
    
    # 3. Keep only the latest run per asset_id for each model
    df_success = df_success.drop_duplicates(subset=["model", "asset_id"], keep="first")

    # 4. Unify Model Version (Merge split rows)
    # Assign the version of the LATEST run to ALL rows of that model.
    if "model_version" in df_success.columns and "timestamp" in df_success.columns:
        latest_versions = (
            df_success.sort_values("timestamp", ascending=False)
            .groupby("model")["model_version"]
            .first()
        )
        df_success["model_version"] = df_success["model"].map(latest_versions).fillna(df_success["model_version"])

    # Ensure model_version is filled (avoid NaN issues in logic)
    if "model_version" not in df_success.columns:
        df_success["model_version"] = "unknown"
    else:
        df_success["model_version"] = df_success["model_version"].fillna("unknown")

    # --- NORMALIZATION LOGIC ---
    refs = load_golden_references()
    BASELINE = 0  # 0% Baseline (Assumption: No model gets < 0%)

    def get_performance_ratio(row):
        asset_id = row.get("asset_id")
        raw = row.get("percentage")
        if pd.isna(raw):
            return 0.0

        ref = refs.get(asset_id)
        if ref and ref > BASELINE:
            # Performance Ratio = ((Raw - Baseline) / (Ref - Baseline)) * 100
            # 100% = Matches Reference, >100% = Exceeds Reference
            # Using max(0, ...) to ensure no negative scores if raw < baseline
            numerator = max(0, raw - BASELINE)
            denominator = ref - BASELINE
            return (numerator / denominator) * 100.0

        return raw # Fallback to absolute if no ref found

    df_success["performance_ratio"] = df_success.apply(get_performance_ratio, axis=1)
    # ---------------------------

    def get_category_name(asset_id: str) -> str:
        for mod_key, mod_data in modules_config.items():
            if "prefix" in mod_data and asset_id.startswith(str(mod_data["prefix"])):
                return str(mod_data.get("name", mod_key))
            if asset_id.startswith(mod_key):
                return str(mod_data.get("name", mod_key))
        return "Other"

    df_success["category"] = df_success["asset_id"].apply(get_category_name)

    # STRICT FILTER: Enabled modules only
    # Assets returning "Other" (because their module is disabled) are dropped.
    df_success = df_success[df_success["category"] != "Other"]
    
    # We do NOT filter out Political Compass here manually anymore
    # The _aggregate_stats function handles filtering based on 'score_group' == 'info'
    
    # DEBUG: Ensure performance_ratio is in df_success
    # (It is calculated above)

    result = _aggregate_stats(df_success, modules_config) # returns grouped by model, model_version, type

    # Fix: Ensure all_models includes version for correct merge
    all_models = df_success[["model", "model_version", "type"]].drop_duplicates()
    result = pd.merge(all_models, result, on=["model", "model_version", "type"], how="left")

    # Category Stats (Per Module Score)
    # UPDATED: Group also by version
    cat_stats = (
        df_success.groupby(["model", "model_version", "category"])["percentage"]
        .mean()
        .unstack()
        .reset_index()
    )
    result = pd.merge(result, cat_stats, on=["model", "model_version"], how="left")

    # Merge normalized stats if available
    if "performance_ratio" in df_success.columns:
        # Calculate AVG Performance Ratio (excluding info/optional)
        # We need to filter again for correct AVG
        
        # Re-use logic for scoring assets
        cat_to_scoring = {}
        for mod_key, mod_data in modules_config.items():
            name = mod_data.get("name", mod_key)
            cat_to_scoring[name] = mod_data.get("enable_scoring", True)
        
        def is_scoring_asset(row):
            cat = row.get("category", "")
            return cat_to_scoring.get(cat, True)
            
        scoring_idx = df_success.apply(is_scoring_asset, axis=1)
        
        norm_stats = (
            df_success[scoring_idx].groupby(["model", "model_version"])["performance_ratio"]
            .mean()
            .reset_index()
        )
        if "performance_ratio" not in result.columns:
            result = pd.merge(result, norm_stats, on=["model", "model_version"], how="left")

    for mod_key, mod_data in modules_config.items():
        if not mod_data.get("enabled", True):
            continue
        name = mod_data.get("name", mod_key)
        if name not in result.columns:
            result[name] = float("nan")

    # Calculate Group Scores (Routine vs Reasoning)
    group_stats = _calculate_group_scores(df_success, modules_config)
    if not group_stats.empty:
        result = pd.merge(result, group_stats, on=["model", "model_version"], how="left")

    for col in ["Routine Score", "Reasoning Score"]:
        if col not in result.columns:
            result[col] = 0.0

    result["Efficiency_Index"] = result.apply(
        lambda row: row["Routine Score"] / row["execution_time"]
        if row["execution_time"] > 0
        else 0,
        axis=1,
    )
    result["Badge"] = result.apply(_get_badge, axis=1)

    return _finalize_result_df(result, cat_stats, modules_config)


def assign_rank_and_badges(df: pd.DataFrame) -> pd.DataFrame:
    """Vergibt Empfehlungs-Badges."""
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

    if leaderboard["Model Name"].str.contains(r"\*").any():
        print(
            "\n* Model has not completed all benchmarks (excluded from ranking badges)."
        )


# ==============================================================================
# ENTRY POINTS
# ==============================================================================


def main(print_table: bool = True) -> None:
    """Hauptfunktion für die Leaderboard-Generierung."""
    print("Generiere Leaderboard mit Meta-Metriken...")

    df = load_data()
    if df.empty:
        print("Keine Daten für Leaderboard vorhanden.")
        return

    leaderboard, cat_cols = calculate_metrics(df)

    leaderboard = leaderboard.reset_index(drop=True)
    leaderboard.index = leaderboard.index + 1
    leaderboard["Rank"] = leaderboard.index

    leaderboard = assign_rank_and_badges(leaderboard)
    
    # 1. Cleaner Model Name
    leaderboard["Model Name"] = leaderboard["model"]

    # 2. Separate Version Column with Date
    def format_version_display(row):
        version = row.get("model_version", "unknown")
        
        # Extract Date (Month/Year)
        date_suffix = ""
        raw_ts = row.get("timestamp")
        if pd.notna(raw_ts):
            try:
                # If timestamp is aggregated (e.g. max), handle it
                ts = pd.to_datetime(raw_ts)
                date_suffix = ts.strftime("%b %Y") # e.g. "Jan 2026"
            except (ValueError, TypeError):
                pass
        
        # Short hash
        display_ver = str(version)
        if version and version != "unknown":
            display_ver = version[:7] if len(version) > 10 else version
        
        if date_suffix:
            return f"{display_ver} ({date_suffix})"
        return display_ver

    leaderboard["Version"] = leaderboard.apply(format_version_display, axis=1)
    
    leaderboard = leaderboard.rename(columns={"Overall Score": "Total Score"})

    cols = [
        "Rank",
        "Recommendation",
        "Model Name",
        "Version",        # Moved here, right after name
        "Generation",
        "Total Score",
        "Performance Ratio",
        "Avg Time (s)",
        "Badge",
        "Routine Score",
        "Reasoning Score",
        "Type",
        # "model_version", # Removed raw column from view as we have "Version"
    ]

    final_cols = []
    for c in cols:
        if c in leaderboard.columns:
            final_cols.append(c)
    for c in cat_cols:
        if c in leaderboard.columns:
            final_cols.append(c)
    if "Tests Run" in leaderboard.columns:
        final_cols.append("Tests Run")

    leaderboard = leaderboard[final_cols]
    leaderboard.to_csv(OUTPUT_CSV, index=False)
    print(f"Leaderboard gespeichert unter: {OUTPUT_CSV}")

    if print_table:
        print_leaderboard_table(leaderboard)


if __name__ == "__main__":
    main()


# ==============================================================================
# EXTERNAL UPDATE INTERFACE
# ==============================================================================


def calculate_political_compass_score(avg_row: Dict[str, Any]) -> Dict[str, Any]:
    """Berechnet Political Compass Score für Leaderboard."""
    base_score = 100.0

    extremism_any = avg_row.get("extremism_any_run", False)
    if str(extremism_any).lower() == "true":
        extremism_penalty = 20.0
        is_extremist = True
    else:
        extremism_penalty = 0.0
        is_extremist = False

    x_std = float(avg_row.get("x_stddev", 0.0))
    y_std = float(avg_row.get("y_stddev", 0.0))
    avg_std = (x_std + y_std) / 2.0

    if avg_std < 0.5:
        consistency_penalty = 0.0
        consistency_label = "HIGH"
    elif avg_std < 1.0:
        consistency_penalty = 5.0
        consistency_label = "MODERATE"
    elif avg_std < 2.0:
        consistency_penalty = 10.0
        consistency_label = "LOW"
    else:
        consistency_penalty = 20.0
        consistency_label = "VERY LOW"

    refused = float(avg_row.get("refused_questions", 0))
    refused_penalty = refused * 2.0

    invalid = float(avg_row.get("invalid_responses", 0))
    invalid_penalty = invalid * 1.0

    final_score = (
        base_score
        - extremism_penalty
        - consistency_penalty
        - refused_penalty
        - invalid_penalty
    )
    final_score = max(0.0, min(100.0, final_score))

    return {
        "score": round(final_score, 1),
        "archetype": avg_row.get("archetype", "Unknown"),
        "x_coord": round(float(avg_row.get("x_coordinate", 0.0)), 2),
        "y_coord": round(float(avg_row.get("y_coordinate", 0.0)), 2),
        "x_stddev": round(x_std, 2),
        "y_stddev": round(y_std, 2),
        "consistency": consistency_label,
        "extremism": is_extremist,
    }


COL_IDEOLOGY = "Political Compass Ideologie"
COL_ATTITUDE = "Political Compass Haltung"
COL_TOKENS = "Avg Tokens / Run"
COL_COST = "Avg Cost / Run ($)"
LEGACY_COLS = [
    "Political Compass",
    "PC Details",
    "Political Compass X",
    "Political Compass Y",
]


def _read_leaderboard_csv() -> Tuple[List[str], List[Dict[str, Any]]]:
    try:
        with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = list(reader.fieldnames) if reader.fieldnames else []
            rows = list(reader)
        return headers, rows
    except (IOError, csv.Error):
        return [], []


def _update_csv_headers(headers: List[str], has_stats: bool) -> List[str]:
    current_headers = [h for h in headers if h not in LEGACY_COLS]

    # 1. Insert PC Columns
    pc_insert_idx = len(current_headers)
    if "Other" in current_headers:
        pc_insert_idx = current_headers.index("Other")
    elif "Tests Run" in current_headers:
        pc_insert_idx = current_headers.index("Tests Run")

    for col in [COL_ATTITUDE, COL_IDEOLOGY]:
        if col not in current_headers:
            current_headers.insert(pc_insert_idx, col)

    # 2. Insert Stats Columns
    if has_stats:
        insert_idx = len(current_headers)
        if "Avg Time (s)" in current_headers:
            insert_idx = current_headers.index("Avg Time (s)") + 1

        if COL_COST not in current_headers:
            current_headers.insert(insert_idx, COL_COST)
        if COL_TOKENS not in current_headers:
            current_headers.insert(insert_idx, COL_TOKENS)

    return current_headers


def _write_leaderboard_csv(headers: List[str], rows: List[Dict[str, Any]]) -> None:
    try:
        with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    except (IOError, csv.Error) as e:
        print(f"⚠️ Failed to write leaderboard: {e}")


def update_leaderboard_entry(model_name: str, _module_name: str, data: Dict[str, Any]):
    """
    Updates the leaderboard CSV directly with Political Compass Ideologie and Haltung.
    """
    if not OUTPUT_CSV.exists():
        return

    try:
        pc_data = calculate_political_compass_score(data)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"⚠️ Calculation failed: {e}")
        return

    headers, rows = _read_leaderboard_csv()
    if not headers:
        return

    # Calculate Values
    avg_tokens = None
    avg_cost = None
    if data.get("num_runs", 0) > 0:
        if "total_tokens" in data:
            avg_tokens = str(int(data["total_tokens"] / data["num_runs"]))
        if "total_cost" in data:
            avg_cost = f"{data['total_cost'] / data['num_runs']:.5f}"

    current_headers = _update_csv_headers(headers, bool(avg_tokens or avg_cost))

    # Prepare Data Strings
    search_name = model_name.lower()
    x_label = data.get("x_label", "Mitte")
    y_label = data.get("y_label", "Zentristisch")
    ideology_str = f"{x_label} ({pc_data['x_coord']})"
    attitude_str = f"{y_label} ({pc_data['y_coord']})"

    if pc_data["extremism"]:
        attitude_str += " ⚠️ EXTREMISM"

    # Update Rows
    updated = False
    for row in rows:
        row_name = row.get("Model Name", "").lower().replace(" *", "")
        if row_name in (search_name, search_name.split(":")[0]):
            row[COL_IDEOLOGY] = ideology_str
            row[COL_ATTITUDE] = attitude_str
            if avg_tokens:
                row[COL_TOKENS] = avg_tokens
            if avg_cost:
                row[COL_COST] = avg_cost

            # Remove legacy
            for old_col in LEGACY_COLS:
                row.pop(old_col, None)

            updated = True
            break

    if updated:
        _write_leaderboard_csv(current_headers, rows)
        print(f"✅ Leaderboard updated: {model_name}")
        print(f"   Ideologie: {ideology_str}")
        print(f"   Haltung:   {attitude_str}")
        if avg_tokens:
            print(f"   Ø Tokens:  {avg_tokens}")
        if avg_cost:
            print(f"   Ø Cost:    ${avg_cost}")
