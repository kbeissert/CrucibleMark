#!/usr/bin/env python3
"""
Verify Counts Script
checks the raw CSV and simulates the aggregation logic to confirm counts.
"""

import sys
from pathlib import Path

# Add root to python path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Import logic (re-implementing simplified version to verify)
from scripts.leaderboard.data_loader import load_benchmark_data  # noqa: E402
from scripts.leaderboard.config import config  # noqa: E402
from utils.module_registry import get_active_modules  # noqa: E402


def _build_modules_config_local(full_config):
    """Local implementation of config building to mirror leaderboard script"""
    active_modules_data = get_active_modules(full_config)
    modules_config = {}

    for mod_id, mod_meta, mod_int_config in active_modules_data:
        integration = mod_int_config.get("integration", {})
        lb_config = integration.get("leaderboard", {})

        display_name = mod_meta.get("name", mod_id)
        if mod_int_config.get("metadata", {}).get("name"):
            display_name = mod_int_config.get("metadata", {}).get(
                "name"
            )  # Prefer internal name

        modules_config[mod_id] = {
            "name": display_name,
            "mod_key": mod_id,
            "enabled": True,
            "path": mod_meta.get("path"),
            "display_test_count": lb_config.get("display_test_count"),
        }
    return modules_config


def print_module_counts(modules_config):
    print("\n=== Module Asset Verification ===")
    print(f"{'Module':<30} | {'Raw':<3} | {'Grp':<3} | {'Over':<5} | {'COUNT'}")
    print("-" * 60)

    # Logic from module_registry.py
    # 2. Smart Grouping & 3. Dynamic Count
    # Strategy: "Last Hyphen Rule"
    # If filename ends with "-{digits}.yaml", treat everything before as Group ID.
    import re

    group_regex = re.compile(r"(.+)-\d+\.yaml$")

    for _, mod_data in modules_config.items():
        if not mod_data.get("enabled", True):
            continue

        name = mod_data.get("name")
        mod_type = mod_data.get("mod_key", "<unknown>")

        # 1. Override
        override = mod_data.get("display_test_count")

        # 2. File Scan
        mod_path_str = mod_data.get("path", "")
        if not mod_path_str:
            mod_path_str = f"benchmark_modules/{mod_type}"

        assets_dir = ROOT_DIR / mod_path_str / "assets"

        calculated_count = 0
        file_count = 0
        groups_found = set()

        if assets_dir.exists():
            files = [f for f in assets_dir.glob("*.yaml") if not f.name.startswith(".")]
            file_count = len(files)

            ungrouped_count = 0
            for f in files:
                match = group_regex.search(f.name)
                if match:
                    groups_found.add(match.group(1))
                else:
                    ungrouped_count += 1
            calculated_count = len(groups_found) + ungrouped_count

        final_count = override if override else calculated_count

        print(
            f"Module: {name:<30} | Files: {file_count:<3} | Groups: {len(groups_found):<3} | Override: {str(override):<5} | FINAL: {final_count}"
        )

    print("-" * 60)


def verify_counts():
    # Load Configs
    modules_config = _build_modules_config_local(config)

    print_module_counts(modules_config)

    print("Loading Benchmark Data...")

    df = load_benchmark_data()

    if df.empty:
        print("No data found.")
        return

    print(f"\nTotal Loaded & Deduplicated Rows: {len(df)}")

    # Check per model
    models = df["model"].unique()

    print("\n--- Breakdown per Model ---")
    for model in models:
        sub_df = df[df["model"] == model]
        versions = sub_df["model_version"].unique()

        for v in versions:
            v_df = sub_df[sub_df["model_version"] == v]

            # Asset Count
            assets = v_df["asset_id"].unique()
            count = len(assets)

            # Check for Political Compass
            has_pc = any(
                "political_compass" in str(row.get("asset_id", ""))
                or "Political Compass" in str(row.get("asset_name", ""))
                for _, row in v_df.iterrows()
            )

            # Count Categories
            # Replicate simple categorization
            # categories = []
            scoring_count = 0

            for _, row in v_df.iterrows():
                aid = str(row.get("asset_id", ""))
                # Quick heuristic for category
                if "code_quality" in aid:
                    cat = "Code"
                elif (
                    "political" in aid
                    or "political" in str(row.get("asset_name", "")).lower()
                ):
                    cat = "Political"
                elif "river" in aid or "metacog" in aid or "_5" in aid:
                    cat = "Reasoning"  # Simple check
                else:
                    cat = "Other"

                if cat != "Political":
                    scoring_count += 1

            print(f"Model: {model:<25} Version: {v:<15} Unique Assets: {count}")
            print(f"  -> Scoring Assets (Est): {scoring_count}")
            print(f"  -> Has Political Compass: {has_pc}")

            # Calculate "Logical" Count
            logical = scoring_count + (9 if has_pc else 0)
            print(f"  -> Calculated Logical Count: {logical}")
            print("-" * 40)


if __name__ == "__main__":
    verify_counts()
