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
        version = row.get("model_version", "unknown")
        
        # Extract Date (Month/Year) if available
        date_suffix = ""
        raw_ts = row.get("timestamp")
        if pd.notna(raw_ts):
            try:
                ts = pd.to_datetime(raw_ts)
                date_suffix = ts.strftime("%b %Y")
            except (ValueError, TypeError):
                pass
        
        # Smart formatting
        display_ver = str(version)
        if version and version != "unknown":
            # Sólo Hash-Werte kürzen (z.B. Ollama Digest oder Git SHA)
            # Namen wie "mistral-medium-latest" sollen erhalten bleiben
            import re
            is_probably_hash = bool(re.match(r'^[a-f0-9]{10,}$', display_ver) or (':' in display_ver and 'sha256' in display_ver))
            
            if is_probably_hash:
                display_ver = display_ver[:7]
            elif len(display_ver) > 25:
                # Lange Namen sanft kürzen
                display_ver = display_ver[:22] + "..."
        
        if date_suffix:
            return f"{display_ver} ({date_suffix})"
        return display_ver

    leaderboard["Version"] = leaderboard.apply(format_version_display, axis=1)

    # 8. Export and Display
    export_to_csv(leaderboard, cat_cols)

    if print_table:
        print_leaderboard_table(leaderboard)


__all__ = ["main"]
