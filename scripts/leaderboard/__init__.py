"""
Leaderboard generation package.
Orchestrates data loading, scoring, module integration, and exporting.

Usage:
    from scripts.leaderboard import main
    main()
"""
try:
    from pathlib import Path
    import pandas as pd
except ImportError:
    pass

# Import internal modules
from .config import config
from .data_loader import load_benchmark_data
from .score_calculator import calculate_scores
from .module_integration import enrich_with_module_data
from .formatter import assign_rank_and_badges, print_leaderboard_table
from .exporter import export_to_csv

# pylint: disable=import-error
try:
    from utils.module_registry import get_active_modules, get_module_test_count  # noqa: E402
except ImportError:
    pass
# pylint: enable=import-error

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def _build_modules_config(full_config, registry_func=get_active_modules) -> dict:
    """Helper to build simplified modules_config for score calculator."""
    active_modules_data = registry_func(full_config)
    modules_config = {}
    
    for mod_id, mod_meta, mod_int_config in active_modules_data:
        # Extract Leaderboard info from Internal Config
        integration = mod_int_config.get("integration", {})
        lb_config = integration.get("leaderboard", {})
        
        # Determine Display Name
        display_name = mod_meta.get("name", mod_id)
        if lb_config.get("columns"):
            display_name = lb_config.get("columns")[0].get("label", display_name)
        elif mod_int_config.get("metadata", {}).get("name"):
            display_name = mod_int_config.get("metadata", {}).get("name")
             
        # Scoring Enabled?
        enable_scoring = lb_config.get("enable_scoring", True)
        if mod_meta.get("score_group") == "info" or lb_config.get("score_group") == "info":
            enable_scoring = False
            
        # Default Contribution
        default_contrib = lb_config.get("default_contribution", {"routine": 0.0, "reasoning": 0.0})
        
        # Determine Assets Count
        mod_path_val = mod_meta.get("path", "")
        if not mod_path_val: 
            mod_path_val = f"benchmark_modules/{mod_id}"
            
        module_path = ROOT_DIR / mod_path_val
        assets_count = get_module_test_count(module_path, mod_int_config)

        mod_entry = {
            "name": display_name,
            "enabled": True,
            "enable_scoring": enable_scoring,
            "default_contribution": default_contrib,
            "assets_count": assets_count,
            "path": mod_path_val,
            "benchmarks": mod_int_config.get("benchmarks", []),
            "display_test_count": lb_config.get("display_test_count"),
        }
        
        # Look for prefix
        prefix = mod_int_config.get("metadata", {}).get("prefix")
        if not prefix:
            prefix = mod_meta.get("prefix")
        if prefix:
            mod_entry["prefix"] = prefix
            
        modules_config[mod_id] = mod_entry
        
    return modules_config


def main(print_table: bool = True) -> None:
    """Main orchestration function for leaderboard generation."""
    print("Generating Leaderboard with Metrics...")

    # 1. Load Data
    df = load_benchmark_data()
    if df.empty:
        print("No data available for leaderboard.")
        return
        
    # 2. Prepare Configs
    # Build simplified module config map for scoring logic
    modules_config = _build_modules_config(config)

    # 3. Calculate Scores & Stats
    leaderboard, _ = calculate_scores(df, modules_config)
    
    # 4. Final Formatting (Rounding etc.)
    # Note: Some rounding happens in formatter/exporter phase or here if needed
    cols_to_round = [
        "Overall Score", 
        "Performance Ratio", 
        "Avg Time (s)", 
        "Routine Score", 
        "Reasoning Score", 
        "Efficiency_Index"
    ]
    for col in cols_to_round:
        if col in leaderboard.columns:
            leaderboard[col] = leaderboard[col].round(2)
            
    # Format category columns (rounding)
    cat_cols = []
    
    # Determine which categories to show (scoring enabled only)
    for _, mod_data in modules_config.items():
        if mod_data.get("enabled") and mod_data.get("enable_scoring", True):
            name = mod_data.get("name")
            if name in leaderboard.columns:
                cat_cols.append(name)
                
    for col in cat_cols:
        if col in leaderboard.columns:
            leaderboard[col] = pd.to_numeric(leaderboard[col], errors="coerce")
            leaderboard[col] = leaderboard[col].round(2).astype(object).fillna("Pending")
            
    # 5. Enrich with Custom Data (from other CSVs via module config)
    leaderboard, cat_cols = enrich_with_module_data(leaderboard, cat_cols, modules_config, config)
    
    # 6. Assign badges and ranks
    leaderboard = assign_rank_and_badges(leaderboard)
    
    # 7. Model Name & Version Formatting
    leaderboard["Model Name"] = leaderboard["model"]
    
    def format_version_display(row):
        version = str(row.get("model_version", "unknown"))
        model_name = str(row.get("model", ""))
        
        # 1. Strip Model Name from Version if it starts with it
        # Exact match check
        if version.startswith(model_name + "-"):
            display_ver = version[len(model_name)+1:]
        # Case insensitive check
        elif version.lower().startswith(model_name.lower() + "-"):
            display_ver = version[len(model_name)+1:]
        elif model_name and model_name in version:
            # If model name is part of version but not perfectly at start or casing differs slightly
             display_ver = version.replace(model_name, "").strip("-")
        else:
            display_ver = version

        # 2. Extract specific parts if it looks like a fingerprint
        # Format: {official}-{hash}-{date} or {hash}-{date}
        # Example: 2411-7f3a9c2b-2026-02-02
        parts = display_ver.split("-")
        
        # If we have a hash-like part, keep it short
        import re
        
        final_parts = []
        for p in parts:
            # Check for behavioral hash (8 char hex) or ollama hash (12+ hex)
            if re.match(r'^[a-f0-9]{8}$', p) or re.match(r'^[a-f0-9]{12,}$', p):
                 final_parts.append(p[:7])
            # Check for date (YYYY-MM-DD or YYYYMMDD) -> maybe remove or format?
            # User wants version number. Date is usually extra info.
            # But the previous code added date suffix from timestamp column.
            elif re.match(r'^\d{4}-\d{2}-\d{2}$', p) and p == datetime.now().strftime("%Y-%m-%d"):
                 # Skip if it is today's date (redundant)
                 pass
            elif re.match(r'^\d{4}$', p): # Year e.g., 2411 (Mistral Version) or 2024
                 final_parts.append(p)
            else:
                 final_parts.append(p)
        
        display_ver = "-".join(final_parts) if final_parts else display_ver

        # 3. Handle 'unknown'
        if display_ver == "unknown":
             # If unknown, we rely on timestamp date
             pass

        # Extract Date (Month/Year) from timestamp for suffix if needed
        date_suffix = ""
        raw_ts = row.get("timestamp")
        if pd.notna(raw_ts):
            try:
                ts = pd.to_datetime(raw_ts)
                date_suffix = ts.strftime("%b %Y")
            except (ValueError, TypeError):
                pass
        
        if display_ver in ["", "unknown"]:
             return f"({date_suffix})" if date_suffix else "unknown"
             
        if date_suffix and date_suffix not in display_ver:
             # Only add if not already in string (e.g. if we kept the date in fingerprint)
            return f"{display_ver} ({date_suffix})"
            
        return display_ver

    leaderboard["Version"] = leaderboard.apply(format_version_display, axis=1)

    # 8. Export and Display
    export_to_csv(leaderboard, cat_cols)

    if print_table:
        print_leaderboard_table(leaderboard)


__all__ = ["main"]
