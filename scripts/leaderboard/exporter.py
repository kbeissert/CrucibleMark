"""
Leaderboard export functionality.
Handles saving the final leaderboard to CSV or other formats.
"""

from typing import List

import pandas as pd

from .config import OUTPUT_CSV


def _format_judge_stars(df: pd.DataFrame) -> pd.DataFrame:
    """
    Formats the 'LLM Judge Avg' column as '<value> ★' (e.g. '3.8 ★').
    Preserves the 0–5 scale; the star symbol signals the alternative rating
    dimension without conflating it with the percentage-based Total Score.
    """
    if "LLM Judge Avg" not in df.columns:
        return df
    df = df.copy()

    def _fmt(val: object) -> object:
        try:
            n = float(val)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return val
        if pd.isna(n):
            return val
        return f"{n:.1f} \u2605"

    df["LLM Judge Avg"] = df["LLM Judge Avg"].apply(_fmt)  # type: ignore[call-overload]
    return df


def _format_tokens_k(df: pd.DataFrame) -> pd.DataFrame:
    """
    Formats token columns for human readability in the CSV output.
    'Tokens Total' and 'Tokens: <Module>' are displayed as e.g. '12.3K'
    instead of 12300. The internal DataFrame is not modified — a copy is
    returned with the display-only formatted string column.
    Numbers below 1000 are shown as plain integers (e.g. '847').
    """
    token_cols = [c for c in df.columns if c == "Tokens Total" or c.startswith("Tokens: ")]
    if not token_cols:
        return df
    df = df.copy()
    for col in token_cols:
        def _fmt(val: object) -> object:
            try:
                n = float(val)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return val
            if pd.isna(n):
                return val
            if n >= 1000:
                return f"{n / 1000:.1f}K"
            return str(int(n))
        df[col] = df[col].apply(_fmt)  # type: ignore[call-overload]
    return df


def export_leaderboard_compact(leaderboard: pd.DataFrame, cat_cols: List[str]) -> None:
    """
    Exports the COMPACT leaderboard (human-readable, ~20 columns).
    Excludes verbose metrics like P95, redundant speed columns, etc.

    SSoT: Spalten-Reihenfolge ist fix:
        Rank, Model Name (display_name), Model ID (model_id), Version, ...
    """
    df_export = leaderboard.copy()

    # Compact display: combine 'Version' and 'Provider Code' into a single column (e.g. "k2/OR")
    if "Provider Code" in df_export.columns and "Version" in df_export.columns:
        def _combine_version_code(row: pd.Series) -> str:
            ver = str(row["Version"])
            code = str(row["Provider Code"])
            if code and code not in ("k.A.", "nan", "") and ver not in ("k.A.", "nan", ""):
                return f"{ver}/{code}"
            return ver
        df_export["Version"] = df_export.apply(_combine_version_code, axis=1)

    # Clean up Score columns
    if "Overall Score" in df_export.columns:
        if "Total Score" in df_export.columns:
            df_export = df_export.drop(columns=["Overall Score"])
        else:
            df_export = df_export.rename(columns={"Overall Score": "Total Score"})

    # Compact Column List — Reihenfolge:
    # Rank, Model Name, Model ID, Version, Badge, Speed Profile, ...
    cols = [
        "Rank",
        "Model Name",  # display_name aus der Model Card
        "Model ID",    # kanonische model_id aus der Model Card
        "Version",
        "Badge",
        "Speed Profile",
        "Total Score",
        "Tokens/s",
        "Avg Task Duration (s)",
        "Tokens Total",
        "Cost per 1K (USD)",
        "Benchmark Cost (USD)",
        "LLM Judge Avg",
        "LLM Judge Coverage",
        "Size Class",
        "Type",
    ]

    final_cols = []
    for c in cols:
        if c in df_export.columns:
            final_cols.append(c)

    for c in cat_cols:
        if c in df_export.columns:
            final_cols.append(c)

    if "Tests Run" in df_export.columns:
        final_cols.append("Tests Run")

    existing_cols = [c for c in final_cols if c in df_export.columns]
    df_export = df_export[existing_cols]
    df_export = _format_tokens_k(df_export)
    df_export = _format_judge_stars(df_export)

    try:
        df_export.to_csv(OUTPUT_CSV, index=False)
        print(f"Compact Leaderboard saved to: {OUTPUT_CSV}")
    except (IOError, PermissionError) as e:
        print(f"⚠️ Error saving compact leaderboard: {e}")


def export_leaderboard_detailed(leaderboard: pd.DataFrame, cat_cols: List[str]) -> None:
    """
    Exports the DETAILED leaderboard (26+ cols).
    Includes P95, Max Time, Timeout Count, Routine/Reasoning aggregates.
    """
    df_export = leaderboard.copy()

    detailed_csv = OUTPUT_CSV.parent / f"{OUTPUT_CSV.stem}_detailed{OUTPUT_CSV.suffix}"

    if "Overall Score" in df_export.columns:
        if "Total Score" not in df_export.columns:
            df_export = df_export.rename(columns={"Overall Score": "Total Score"})

    # Expose raw model ID as SSOT for downstream tools (web_export, dir lookups)
    if "model" in df_export.columns:
        df_export["model_id_raw"] = df_export["model"]

    # Vendor field: read from model card (SSoT) via model_id lookup
    _cards_dir = OUTPUT_CSV.parent.parent / "benchmark_scores" / "model_cards"
    _vendor_map: dict = {}
    import json as _json
    import re as _re
    if _cards_dir.exists():
        for _cf in _cards_dir.glob("*.json"):
            if _cf.name == "_index.json":
                continue
            try:
                _cd = _json.loads(_cf.read_text(encoding="utf-8"))
                _mid = _cd.get("model_id", "")
                _v = _cd.get("vendor")
                if _mid and _v:
                    _vendor_map[_mid] = _v
            except Exception:
                pass

    def _lookup_vendor(raw_mid: str) -> str:
        if raw_mid in _vendor_map:
            return _vendor_map[raw_mid]
        stripped = _re.sub(r"-\d{4,8}$", "", raw_mid)
        return _vendor_map.get(stripped, "")

    if "Model ID" in df_export.columns:
        df_export["Vendor"] = df_export["Model ID"].apply(
            lambda x: _lookup_vendor(str(x)) if pd.notna(x) else ""
        )

    # Spalten-Reihenfolge: Rank, Model Name, Model ID, Version, ...
    cols = [
        "Rank",
        "Model Name",     # display_name aus der Model Card
        "Model ID",       # kanonische model_id aus der Model Card
        "model_id_raw",   # rohe model_id aus den CSV-Daten (für Debugging)
        "Version",
        "Provider Code",
        "Badge",
        "Speed Profile",
        "Performance Tier",
        "Total Score",
        "Tokens/s",
        "Avg Task Duration (s)",
        "Initial Load Time (s)",
        "P95 Time (s)",
        "Max Time (s)",
        "Timeout Count",
        "Tokens Total",
        "Cost per 1K (USD)",
        "Benchmark Cost (USD)",
        "LLM Judge Avg",
        "LLM Judge Avg (raw)",
        "LLM Judge Coverage",
        "Routine Score",
        "Reasoning Score",
        "Vendor",
        "Size Class",
        "Type",
    ]

    if "LLM Judge Avg" in df_export.columns:
        df_export["LLM Judge Avg (raw)"] = pd.to_numeric(
            df_export["LLM Judge Avg"], errors="coerce"
        )

    final_cols = []
    for c in cols:
        if c in df_export.columns:
            final_cols.append(c)

    for c in cat_cols:
        if c in df_export.columns:
            final_cols.append(c)

    token_module_cols = sorted([c for c in df_export.columns if c.startswith("Tokens: ")])
    for c in token_module_cols:
        final_cols.append(c)

    if "Tests Run" in df_export.columns:
        final_cols.append("Tests Run")

    existing_cols = [c for c in final_cols if c in df_export.columns]
    df_export = df_export[existing_cols]
    df_export = _format_tokens_k(df_export)
    df_export = _format_judge_stars(df_export)

    try:
        df_export.to_csv(detailed_csv, index=False)
        print(f"Detailed Leaderboard saved to: {detailed_csv}")
    except (IOError, PermissionError) as e:
        print(f"⚠️ Error saving detailed leaderboard: {e}")


def export_to_csv(leaderboard: pd.DataFrame, cat_cols: List[str]) -> None:
    """
    Legacy entry point - calls both exports.
    """
    export_leaderboard_compact(leaderboard, cat_cols)
    export_leaderboard_detailed(leaderboard, cat_cols)
