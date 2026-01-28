#!/usr/bin/env python3
"""
Generiert ein Leaderboard aus den Benchmark-Ergebnissen.
Führt lokale und kommerzielle Ergebnisse zusammen und berechnet Durchschnittswerte.
"""

import csv
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# pylint: disable=import-error
import yaml
import pandas as pd
# pylint: enable=import-error

# Suppress FutureWarning about downcasting
pd.set_option("future.no_silent_downcasting", True)

# Pfad für Imports setzen
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# pylint: disable=wrong-import-position, import-error
from utils.config_validator import ConfigValidator  # noqa: E402
from utils.csv_recovery import parse_row_robust, get_csv_header_idx  # noqa: E402
# pylint: enable=wrong-import-position, import-error

# Konstanten
THRESHOLD_GOD_MODE_ROUTINE = 85
THRESHOLD_GOD_MODE_REASONING = 80
THRESHOLD_DAILY_DRIVER = 80
THRESHOLD_DEEP_THINKER = 80
REGISTRY_FILE = ROOT_DIR / "model_registry.yaml"

# Konfiguration laden
validator = ConfigValidator()
config = validator.config
output_config = config.get("output", {})

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

    df = df.sort_values("timestamp")
    df = df.drop_duplicates(subset=["model", "type", "asset_id"], keep="last")
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

    if pd.isna(routine):
        routine = 0
    if pd.isna(reasoning):
        reasoning = 0

    is_god_mode = (
        reasoning > THRESHOLD_GOD_MODE_REASONING
        and routine > THRESHOLD_GOD_MODE_ROUTINE
    )

    if is_god_mode:
        return "👑 God Mode"
    if reasoning > THRESHOLD_DEEP_THINKER:
        return "🧠 Deep Thinker"
    if routine > THRESHOLD_DAILY_DRIVER:
        return "🏎️ Daily Driver"
    return "⚖️ Standard"


def _aggregate_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregiert Basis-Statistiken pro Modell."""
    total_unique_assets = df["asset_id"].nunique()
    
    # Check if normalized column exists
    aggs = {"percentage": "mean", "execution_time": "mean", "asset_id": "count"}
    if "performance_ratio" in df.columns:
        aggs["performance_ratio"] = "mean"
        
    stats = (
        df.groupby(["model", "type"])
        .agg(aggs)
        .reset_index()
    )

    stats["is_complete"] = stats["asset_id"] >= total_unique_assets
    stats["Tests Run"] = stats["asset_id"].astype(str) + "/" + str(total_unique_assets)
    return stats


def _calculate_tier_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Berechnet separate Statistik für Tier 1 und Tier 2."""
    if "tier" not in df.columns:
        return pd.DataFrame()

    def get_tier_simple(t: Any) -> Optional[str]:
        s = str(t)
        if "Tier 1" in s:
            return "Tier 1"
        if "Tier 2" in s:
            return "Tier 2"
        return None

    df_copy = df.copy()
    df_copy["simple_tier"] = df_copy["tier"].apply(get_tier_simple)
    tier_means = (
        df_copy.groupby(["model", "simple_tier"])["percentage"]
        .mean()
        .unstack()
        .reset_index()
    )

    return tier_means.rename(
        columns={"Tier 1": "Routine Score", "Tier 2": "Reasoning Score"}
    )


try:
    # pylint: disable=import-outside-toplevel
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

    for col in result.columns:
        if col in cat_stats.columns and col not in cat_cols and col != "model":
            cat_cols.append(col)

    # Round category columns (Handle Pending)
    pc_labels = [
        "Political Compass Ideologie",
        "Political Compass Haltung",
        "Political Compass",
    ]
    for col in cat_cols:
        if col in result.columns and col not in pc_labels:
            result[col] = pd.to_numeric(result[col], errors="coerce")
            result[col] = result[col].round(2).astype(object).fillna("Pending")

    return result, cat_cols


def _merge_political_compass(
    result: pd.DataFrame, cat_cols: List[str]
) -> Tuple[pd.DataFrame, List[str]]:
    """Merges Political Compass results into the leaderboard."""
    pc_csv = SCORES_DIR / "political_compass_results.csv"

    if "Political Compass" in result.columns:
        result = result.drop(columns=["Political Compass"])
    if "Political Compass" in cat_cols:
        cat_cols.remove("Political Compass")

    for col_name in ["Political Compass Ideologie", "Political Compass Haltung"]:
        if col_name not in result.columns:
            result[col_name] = ""
        if col_name not in cat_cols:
            cat_cols.append(col_name)

    if pc_csv.exists():
        try:
            pc_df = pd.read_csv(pc_csv)
            if "run_id" in pc_df.columns:
                pc_df = pc_df[pc_df["run_id"] == "AVG"]

            if "x_coordinate" in pc_df.columns and "x_label" in pc_df.columns:
                pc_df["Political Compass Ideologie"] = (
                    pc_df["x_label"] + " (" + pc_df["x_coordinate"].astype(str) + ")"
                )
            if "y_coordinate" in pc_df.columns and "y_label" in pc_df.columns:
                pc_df["Political Compass Haltung"] = (
                    pc_df["y_label"] + " (" + pc_df["y_coordinate"].astype(str) + ")"
                )

            if "model" in pc_df.columns:
                pc_df = pc_df.drop_duplicates(subset=["model"], keep="last")

            result.set_index("model", inplace=True)
            try:
                pc_df.set_index("model", inplace=True)
                for col_name in [
                    "Political Compass Ideologie",
                    "Political Compass Haltung",
                ]:
                    if col_name in pc_df.columns:
                        result.update(pc_df[[col_name]])
            except Exception as update_err:  # pylint: disable=broad-exception-caught
                print(f"Pt. Failure PC update: {update_err}")
            finally:
                result.reset_index(inplace=True)

        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Warning: Failed to merge Political Compass details: {e}")
            if result.index.name == "model":
                result.reset_index(inplace=True)

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
    
    # Sort by Performance Ratio if available (fairer ranking), otherwise Overall
    sort_col = "Performance Ratio" if "Performance Ratio" in result.columns else "Overall Score"
    result = result.sort_values(sort_col, ascending=False)

    result, cat_cols = _format_metrics(result, cat_stats, modules_config)
    result, cat_cols = _merge_political_compass(result, cat_cols)

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
    modules_config = config.get("modules", {})
    df_success = df[df["status"] == "success"].copy()

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
    df_for_score = df_success[df_success["category"] != "Political Compass"]
    
    # DEBUG: Ensure performance_ratio is in df_for_score
    if "performance_ratio" in df_success.columns:
        # Explicitly copy it over if it got lost in filtering (it shouldn't, but safe)
        df_for_score = df_for_score.copy()
        df_for_score["performance_ratio"] = df_success.loc[df_for_score.index, "performance_ratio"]
        
    result = _aggregate_stats(df_for_score)

    all_models = df_success[["model", "type"]].drop_duplicates()
    result = pd.merge(all_models, result, on=["model", "type"], how="left")

    cat_stats = (
        df_success.groupby(["model", "category"])["percentage"]
        .mean()
        .unstack()
        .reset_index()
    )
    result = pd.merge(result, cat_stats, on="model", how="left")
    
    # Merge normalized stats if available
    if "performance_ratio" in df_success.columns:
        norm_stats = (
            df_success.groupby(["model"])["performance_ratio"]
            .mean()
            .reset_index()
        )
        if "performance_ratio" not in result.columns:
            result = pd.merge(result, norm_stats, on="model", how="left")

    for mod_key, mod_data in modules_config.items():
        name = mod_data.get("name", mod_key)
        if name not in result.columns:
            result[name] = float("nan")

    tier_stats = _calculate_tier_stats(df_success)
    if not tier_stats.empty:
        result = pd.merge(result, tier_stats, on="model", how="left")

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
    leaderboard = leaderboard.rename(columns={"model": "Model Name"})
    leaderboard = leaderboard.rename(columns={"Overall Score": "Total Score"})

    cols = [
        "Rank",
        "Recommendation",
        "Model Name",
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

    rows = []
    headers = []

    try:
        with open(OUTPUT_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = list(reader.fieldnames) if reader.fieldnames else []
            rows = list(reader)
    except (IOError, csv.Error):
        return

    col_ideology = "Political Compass Ideologie"
    col_attitude = "Political Compass Haltung"
    col_tokens = "Avg Tokens / Run"
    col_cost = "Avg Cost / Run ($)"

    new_pc_cols = [col_ideology, col_attitude]
    legacy_cols = [
        "Political Compass",
        "PC Details",
        "Political Compass X",
        "Political Compass Y",
    ]

    current_headers = [h for h in headers if h not in legacy_cols]

    # Calculate Values (if passed)
    avg_tokens_val = None
    avg_cost_val = None
    if "total_tokens" in data and "num_runs" in data and data["num_runs"] > 0:
        avg_tokens_val = str(int(data["total_tokens"] / data["num_runs"]))
    if "total_cost" in data and "num_runs" in data and data["num_runs"] > 0:
        avg_cost_val = f"{data['total_cost'] / data['num_runs']:.5f}"

    # 1. Insert PC Columns (Ideology, Haltung)
    pc_insert_idx = len(current_headers)
    if "Other" in current_headers:
        pc_insert_idx = current_headers.index("Other")
    elif "Tests Run" in current_headers:
        pc_insert_idx = current_headers.index("Tests Run")

    for col in reversed(new_pc_cols):
        if col not in current_headers:
            current_headers.insert(pc_insert_idx, col)

    # 2. Insert Cost/Token Columns (After Avg Time)
    if avg_tokens_val or avg_cost_val:
        insert_idx_stats = len(current_headers)
        if "Avg Time (s)" in current_headers:
            insert_idx_stats = current_headers.index("Avg Time (s)") + 1

        # Insert Cost first, then Tokens at same index -> Result: Time, Tokens, Cost
        # (Insert pushes existing elements right, so inserting at X puts element at X)
        # 1. Insert Cost at X -> [Time, Cost, ...]
        # 2. Insert Tokens at X -> [Time, Tokens, Cost, ...]
        if col_cost not in current_headers:
            current_headers.insert(insert_idx_stats, col_cost)
        if col_tokens not in current_headers:
            current_headers.insert(insert_idx_stats, col_tokens)

    search_name = model_name.lower()
    updated = False

    x_label = data.get("x_label", "Mitte")
    y_label = data.get("y_label", "Zentristisch")
    x_val = pc_data["x_coord"]
    y_val = pc_data["y_coord"]
    ideology_str = f"{x_label} ({x_val})"
    attitude_str = f"{y_label} ({y_val})"

    if pc_data["extremism"]:
        attitude_str += " ⚠️ EXTREMISM"

    for row in rows:
        row_name = row.get("Model Name", "").lower().replace(" *", "")
        if row_name in (search_name, search_name.split(":")[0]):
            row[col_ideology] = ideology_str
            row[col_attitude] = attitude_str

            if avg_tokens_val:
                row[col_tokens] = avg_tokens_val
            if avg_cost_val:
                row[col_cost] = avg_cost_val

            for old_col in legacy_cols:
                if old_col in row:
                    del row[old_col]
            updated = True
            break

    if updated:
        try:
            with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(
                    f, fieldnames=current_headers, extrasaction="ignore"
                )
                writer.writeheader()
                writer.writerows(rows)
            print(f"✅ Leaderboard updated: {model_name}")
            print(f"   Ideologie: {ideology_str}")
            print(f"   Haltung:   {attitude_str}")
            if avg_tokens_val:
                print(f"   Ø Tokens:  {avg_tokens_val}")
            if avg_cost_val:
                print(f"   Ø Cost:    ${avg_cost_val}")
        except (IOError, csv.Error) as e:
            print(f"⚠️ Failed to write leaderboard: {e}")
