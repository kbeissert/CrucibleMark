#!/usr/bin/env python3
"""
Recover Political Compass Results
================================
Scans the 'outputs/runs' directory for Political Compass JSON logs
and reconstructs the 'benchmark_scores/political_compass_results.csv' file.

This allows updating the leaderboard without re-running the benchmark.
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Setup
ROOT_DIR = Path(__file__).parent.parent.parent
LOGS_DIR = ROOT_DIR / "outputs" / "runs"
TARGET_CSV = ROOT_DIR / "benchmark_scores" / "political_compass_results.csv"

def get_pc_logs() -> List[Path]:
    """Find all potential Political Compass JSON logs."""
    if not LOGS_DIR.exists():
        print(f"❌ Directory not found: {LOGS_DIR}")
        return []
    return list(LOGS_DIR.glob("*.json"))

def parse_log(filepath: Path) -> Dict[str, Any] | None:
    """Extracts PC data from a single log file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check if it is a PC result
        if "coordinates" not in data or "archetype" not in data:
            return None

        # Validate internal structure
        if "x" not in data["coordinates"] or "label" not in data["archetype"]:
            return None

        # Build Data Object (Standard v3)
        data_object = {
            "coordinates": {
                "x": data["coordinates"].get("x"),
                "y": data["coordinates"].get("y"),
                "formatted": f"({data['coordinates'].get('x')}, {data['coordinates'].get('y')})"
            },
            "labels": {
                "x": data["archetype"].get("x_label", "Unknown"),
                "y": data["archetype"].get("y_label", "Unknown"),
                "archetype": data["archetype"].get("label", "Unknown")
            },
            "display": {
                 "ideology": f"{data['archetype'].get('x_label', '?')} ({data['coordinates'].get('x')})",
                 "stance": f"{data['archetype'].get('y_label', '?')} ({data['coordinates'].get('y')})"
            },
            "extremism": data.get("extremism", { "count": 0, "rate": 0.0 })
        }

        # Extract Fields
        return {
            "model": data.get("model", "unknown"),
            "model_version": data.get("model_version", "unknown"),
            "run_id": "AVG",
            "x_coordinate": data["coordinates"].get("x"),
            "y_coordinate": data["coordinates"].get("y"),
            "x_label": data["archetype"].get("x_label", ""),
            "y_label": data["archetype"].get("y_label", ""),
            "timestamp": data.get("test_date", datetime.now().isoformat()),
            "metrics_json": json.dumps(data_object, ensure_ascii=False),
            "source_file": filepath.name
        }

    except Exception as e:
        print(f"⚠️ Error parsing {filepath.name}: {e}")
        return None

def main():
    print(f"🔍 Scanning {LOGS_DIR} for Political Compass logs...")

    logs = get_pc_logs()
    results = []

    for log_file in logs:
        entry = parse_log(log_file)
        if entry:
            results.append(entry)
            print(f"✅ Found: {entry['model']} (File: {entry['source_file']})")

    if not results:
        print("❌ No valid Political Compass logs found.")
        return

    # Sort by timestamp to keep latest last (deduplication strategy often keeps last)
    results.sort(key=lambda x: x["timestamp"])

    # Prepare for CSV
    # We remove 'source_file' before writing to match expected schema
    csv_rows = []
    for r in results:
        row = r.copy()
        del row["source_file"]
        csv_rows.append(row)

    # Ensure Target Directory
    TARGET_CSV.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    fieldnames = [
        "model", "model_version", "run_id", 
        "x_coordinate", "y_coordinate", "x_label", "y_label", 
        "metrics_json", "timestamp"
    ]

    try:
        with open(TARGET_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)

        print(f"\n💾 Successfully recovered {len(results)} entries to:")
        print(f"   {TARGET_CSV}")
        print("\n👉 You can now run 'make leaderboard' to update the table.")

    except Exception as e:
        print(f"❌ Error writing CSV: {e}")

if __name__ == "__main__":
    main()
