"""
Data loading and CSV parsing for leaderboard generation.
Handles reading commercial, local, and golden standard benchmark results.
"""

import csv
from pathlib import Path
from typing import Dict, List

import pandas as pd

# pylint: disable=import-error
from utils.csv_recovery import get_csv_header_idx, parse_row_robust

# pylint: enable=import-error

# Import configuration and constants
from .config import COMMERCIAL_CSV, LOCAL_CSV, CLOUD_CSV

# pylint: disable=import-error
try:
    from utils.model_utils import get_model_category
except ImportError:
    # Fallback if import fails (should match SSOT logic in model_utils.py)
    def get_model_category(
        model_name: str, source_file: str = "local", size_gb: float | None = None, provider: str | None = None
    ) -> str:
        """Fallback categorization matching SSOT."""
        if source_file == "commercial":
            return "Proprietär"
        model_lower = model_name.lower()
        if ":cloud" in model_lower or model_lower.endswith("-cloud"):
            return "Open Weights (Cloud)"
        if size_gb is not None and size_gb < 0.01:
            return "Open Weights (Cloud)"
        return "Open Weights (Local)"


# pylint: enable=import-error


def _extract_scores_from_df(df: pd.DataFrame) -> Dict[str, float]:
    """Helper to extract latest scores per asset from a DataFrame."""
    refs = {}
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
    return refs


def _process_csv(dfs: List[pd.DataFrame], filepath: Path, type_label: str) -> None:
    """
    Helper to process a single CSV File and append to list of DataFrames.

    Args:
        dfs: List to append the resulting DataFrame to.
        filepath: Path to the CSV file.
        type_label: Label for the 'type' column (e.g., 'Commercial', 'Local').
    """
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

            # SSOT: Centralized Model Categorization
            # Uses get_model_category() from model_utils.py as Single Source of Truth
            if "model" in df_new.columns:
                # Determine source context
                if type_label == "Proprietär":
                    source_context = "commercial"
                elif type_label == "Open Weights (Cloud)":
                    source_context = "cloud"
                else:
                    source_context = "local"

                df_new["source"] = source_context

                if "provider" in df_new.columns:
                    df_new["type"] = df_new.apply(
                        lambda row: get_model_category(row["model"], source_context, provider=row.get("provider")),
                        axis=1
                    )
                else:
                    df_new["type"] = df_new["model"].apply(
                        lambda m: get_model_category(m, source_context)
                    )
            else:
                df_new["type"] = type_label
            dfs.append(df_new)
    except (OSError, csv.Error) as e:
        print(f"Error parsing {filepath}: {e}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Fallback for unexpected errors during manual parsing
        print(f"Unexpected error in {filepath}: {e}")


def load_benchmark_data() -> pd.DataFrame:
    """
    Loads and normalizes data from commercial and local CSVs.

    Returns:
        pd.DataFrame: Concatenated and deduplicated benchmark results.
                      Returns empty DataFrame if no data found.
    """
    dfs: List[pd.DataFrame] = []

    _process_csv(dfs, COMMERCIAL_CSV, "Proprietär")
    _process_csv(dfs, CLOUD_CSV, "Open Weights (Cloud)")
    _process_csv(dfs, LOCAL_CSV, "Open Weights (Local)")

    if not dfs:
        print("No benchmark data found.")
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)

    # Bugfix: Enforce exact routing boundary!
    # Cloud models must EXCLUSIVELY come from cloud_models_benchmark.csv
    # Local models must EXCLUSIVELY come from local_models_benchmark.csv
    # Commercial from commercial_models_benchmark.csv
    valid_mask = (
        ((df["type"] == "Proprietär") & (df["source"] == "commercial")) |
        ((df["type"] == "Cloud-Modelle (Open-Weights)") & (df["source"] == "cloud")) |
        ((df["type"] == "Open Weights (Local)") & (df["source"] == "local"))
    )
    # Behalte Backup-Kategorien wie 'Local Cloud' (falls sie existieren), oder ignoriere?
    # Es ist robuster, einfach zu filtern:
    df = df[
        (df["type"] != "Open Weights (Cloud)") | (df["source"] == "cloud")
    ]
    df = df[
        (df["type"] != "Open Weights (Local)") | (df["source"] == "local")
    ]
    df = df[
        (df["type"] != "Proprietär") | (df["source"].isin(["commercial", "cloud"]))
    ]

    df["percentage"] = pd.to_numeric(df["percentage"], errors="coerce")
    df["execution_time"] = pd.to_numeric(df["execution_time"], errors="coerce")
    if "cost_usd" in df.columns:
        df["cost_usd"] = pd.to_numeric(df["cost_usd"], errors="coerce").fillna(0.0)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", format="mixed")

    # If model_version is missing (e.g. newly loaded CSV didn't have it yet), fill with "unknown"
    if "model_version" not in df.columns:
        df["model_version"] = "unknown"
    else:
        df["model_version"] = df["model_version"].fillna("unknown")

    # Sort by timestamp to ensure 'last' is actually the most recent
    df = df.sort_values("timestamp")

    # Normalize model_version: Remove date suffix (YYYY-MM-DD from fingerprint)
    # to aggregate runs of the same version across different days.
    if "model_version" in df.columns:
        df["model_version"] = (
            df["model_version"]
            .astype(str)
            .str.replace(r"-\d{4}-\d{2}-\d{2}$", "", regex=True)
        )

    # Also normalize model name to remove date suffixes
    if "model" in df.columns:
        df["model"] = (
            df["model"]
            .astype(str)
            .str.replace(r"-\d{4}-\d{2}-\d{2}$", "", regex=True)
        )

    # --- DEDUPLICATION (Latest Run Only) ---
    # Crucial for accurate metrics (e.g. Load Time on new hardware):
    # We only want the LATEST run for each unique (model, version, asset).
    # Since df is already sorted by timestamp (asc), 'keep=last' preserves the most recent.
    if "asset_id" in df.columns:
        df = df.drop_duplicates(
            subset=["model", "model_version", "asset_id"], keep="last"
        )

    # --- VERSION ALIASING/MERGING ---
    # Fix mismatches where some entries use date-strings and others use hashes for the same model.
    # We prefer alphanumeric hashes over pure numeric date-strings if both exist for a model.
    if "model" in df.columns and "model_version" in df.columns:
        pairs = df[["model", "model_version"]].drop_duplicates()
        m_counts = pairs["model"].value_counts()
        multi_ver_models = m_counts[m_counts > 1].index

        version_map = {}
        for m in multi_ver_models:
            vers = pairs[pairs["model"] == m]["model_version"].tolist()
            # Heuristic: Prefer version with letters (e.g. hash) over pure numeric (e.g. date)
            # Exclude 'unknown'/'none' from being considered a valid "alpha" version (target)
            alphas = [
                v
                for v in vers
                if any(c.isalpha() for c in str(v))
                and str(v).lower() not in ["unknown", "none", "nan", ""]
            ]

            # If we have exactly one 'alpha' version and other 'numeric' versions, map all to alpha.
            # If multiple alpha versions exist, we assume they are distinct releases and do NOT merge.
            if len(alphas) == 1:
                best_v = alphas[0]
                for v in vers:
                    if v != best_v:
                        # Only merge if the other version is purely numeric (date-like) or shorter/generic
                        if str(v).replace("-", "").isdigit() or v in [
                            "unknown",
                            "None",
                        ]:
                            version_map[(m, v)] = best_v

        if version_map:
            # print(f"Merging alias versions: {version_map}")
            df["model_version"] = df.apply(
                lambda row: version_map.get(
                    (row["model"], row["model_version"]), row["model_version"]
                ),
                axis=1,
            )

    df = df.drop_duplicates(
        subset=["model", "model_version", "type", "asset_id"], keep="last"
    )
    return df
