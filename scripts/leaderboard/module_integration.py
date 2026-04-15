"""
Integration of external module data into leaderboard.
Handles generic CSV merging and value extraction based on module configuration.
"""

import json
import sys
from typing import Any, Dict, List, Tuple

import pandas as pd

# Import constants and config logic
from .config import ROOT_DIR, SCORES_DIR

# Ensure root dir in path for local imports
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# pylint: disable=import-error
try:
    from utils.module_registry import get_active_modules
except ImportError:
    pass
# pylint: enable=import-error


def _enrich_from_csv_source(
    result: pd.DataFrame, label: str, source_config: Dict[str, Any]
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
            source_df = source_df.drop_duplicates(
                subset=["model", "model_version"], keep="last"
            )

        # 4. Value Construction (JSON Object Access OR Templating)
        template = source_config.get("value_template")
        json_key = source_config.get("key")

        def safe_format(row):
            try:
                # Option A: JSON Object Access (Structured Data)
                # Check for either metadata_json (Standard v2) or metrics_json (Legacy)
                json_col = None
                if "metadata_json" in row:
                    json_col = "metadata_json"
                elif "metrics_json" in row:
                    json_col = "metrics_json"

                if json_key and json_col:
                    try:
                        metrics = json.loads(row[json_col])
                        # Support dot notation (e.g. "labels.x")
                        val = metrics
                        for k in json_key.split("."):
                            if isinstance(val, dict):
                                val = val.get(k, {})
                            else:
                                return "Error (Struct)"

                        if isinstance(val, (dict, list)):
                            return json.dumps(val, ensure_ascii=False)

                        # Store raw value in temp variable for template
                        # We cannot modify 'row' here safely for the pandas apply context?
                        # Actually we are processing one row.
                        # But wait, 'template' option below uses row.to_dict().
                        # If we want to support 'format' combining JSON value with other things,
                        # we need to be clever.

                        # Current Logic: Either JSON Access OR Template.
                        # User wants {value} ({x}).
                        # This suggests we need formatting AFTER extraction.

                        extracted_val = str(val) if val is not None else ""

                        # NEW: Check if there is an additional format string in config
                        fmt = source_config.get("format")
                        if fmt:
                            # We can try to make a context dict.
                            # Standard context: row + 'value'
                            ctx = row.to_dict()
                            ctx["value"] = extracted_val

                            # Flatten JSON for context?
                            if isinstance(metrics, dict):
                                # Flatten top level keys
                                for mk, mv in metrics.items():
                                    if isinstance(mv, (str, int, float)):
                                        ctx[mk] = mv
                                    elif isinstance(mv, dict):
                                        # One level deep flattening (e.g. coordinates.x -> x)
                                        for subk, subv in mv.items():
                                            if isinstance(subv, (str, int, float)):
                                                ctx[subk] = subv

                            try:
                                return fmt.format(**ctx)
                            except KeyError:
                                return extracted_val  # Fallback to raw value

                        return extracted_val

                    except (json.JSONDecodeError, AttributeError):
                        return "Error (JSON)"

                # Option B: Legacy String Templating (No JSON key)
                if template:
                    # Convert row to dict, ensure all values are strings for safe substitution
                    data = row.to_dict()
                    rendered = template.format(**data)
                    # Degenerate case: vanilla_label was empty (e.g. censored/refused PC run)
                    # produces leading whitespace before "(Shift:" → treat as missing
                    if rendered.strip().startswith("(Shift:"):
                        return fallback
                    return rendered

                return ""
            except KeyError:
                return "Error (Key)"
            except Exception:  # pylint: disable=broad-exception-caught
                return "Error"

        if template or json_key:
            source_df[label] = source_df.apply(safe_format, axis=1)
        else:
            source_df[label] = ""

        # 5. Merge Strategy (Exact + Fallback)
        cols_to_merge = ["model", "model_version", label]

        # Check if columns exist
        available_cols = [c for c in cols_to_merge if c in source_df.columns]
        if len(available_cols) < 3:  # Need at least model keys + target
            return result

        merge_subset = source_df[available_cols]

        # Drop if exists in result (overwrite logic)
        if label in result.columns:
            result = result.drop(columns=[label])

        # A) Try Exact Match
        result = result.merge(merge_subset, on=["model", "model_version"], how="left")

        # B) Try Fallback (Match on model only - Relaxed)
        # Identify rows that failed the exact match
        missing_mask = result[label].isna()
        if missing_mask.any():
            # RELAXED: Use any version from source, removing duplicates by keeping last
            # This allows matching 'gpt-4o' (ver A) with 'gpt-4o' (ver B) if exact match failed
            fallback_source = source_df[["model", label]].drop_duplicates(
                subset=["model"], keep="last"
            )

            if not fallback_source.empty:
                # Rename col to avoid collision during merge
                fallback_source = fallback_source.rename(
                    columns={label: label + "_fallback"}
                )

                # Merge on model only
                result = result.merge(fallback_source, on="model", how="left")

                # Fill NaNs in main column with fallback (only where matching failed)
                result[label] = result[label].fillna(result[label + "_fallback"])

                # Cleanup
                if (label + "_fallback") in result.columns:
                    result = result.drop(columns=[label + "_fallback"])

        # Fill Missing
        fallback = source_config.get("missing_value", "Pending")
        result[label] = result[label].fillna(fallback)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Generic CSV Merge Error ({filename}): {e}")
        if label not in result.columns:
            result[label] = "Error"

    return result


def enrich_with_module_data(
    result: pd.DataFrame,
    cat_cols: List[str],
    modules_config: Dict[str, Any],
    full_config: Dict[str, Any],
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Merges custom/additional data columns for modules defined in their config.
    Iterates over all enabled modules and checks for 'source' definition in 'columns'.

    Args:
        result: Leaderboard DataFrame
        cat_cols: List of category columns (will be updated)
        modules_config: Simplified modules config (from score_calculator)
        full_config: Full benchmark config (for re-loading detailed integrations)

    Returns:
        Tuple of (Enriched DataFrame, Updated Category Columns list)
    """

    if result.empty:
        return result, cat_cols

    # Access full registry configuration to get deep 'integration' block
    active_modules_data = get_active_modules(full_config)

    for mod_id, _, mod_int_config in active_modules_data:
        # Check if enabled
        if not mod_int_config.get("enabled", True):
            # Check modules_config as secondary enabled check (if passed)
            if modules_config and not modules_config.get(mod_id, {}).get(
                "enabled", True
            ):
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
