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
from .config import COMMERCIAL_CSV, GOLDEN_CSV, LOCAL_CSV


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

    _process_csv(dfs, COMMERCIAL_CSV, "Commercial")
    _process_csv(dfs, LOCAL_CSV, "Local")

    if not dfs:
        print("No benchmark data found.")
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)
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

    # DEDUPLICATION LOGIC with VERSIONING:
    # We now group by model AND model_version.
    # This means 'mistral:latest' (v1) and 'mistral:latest' (v2) are treated as DIFFERENT entities.
    df = df.drop_duplicates(subset=["model", "model_version", "type", "asset_id"], keep="last")
    return df


def load_golden_references() -> Dict[str, float]:
    """
    Loads reference scores per asset from the Golden Standard CSV.

    Returns:
        Dict[str, float]: Mapping of asset_id to percentage score.
    """
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
        print(f"⚠️ Warning: Could not load Golden Standards: {e}")

    return refs
