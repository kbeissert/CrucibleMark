#!/usr/bin/env python3
"""
Bias Sensitivity Report Generator
=================================

Analyzes Political Compass benchmark runs to compare "Vanilla" vs. "Anti-Diplomat" behavior.
Generates a High-Level CSV report: benchmark_scores/bias_sensitivity.csv

Logic:
1. Scans `outputs/runs/` for Political Compass JSON results.
2. groups runs by Model ID.
3. Identifies "Vanilla" (Standard) and "Forced" (Anti-Diplomat) runs based on config flags or timestamps/tags.
   (Currently, since we don't explicitly tag the run mode in the JSON metadata yet, 
    we might need to rely on heuristic or infer from the results. 
    HOWEVER, for a robust implementation, we should probably check if we can distinguish them.
    
    Looking at the previous turn, the user ran:
    - Vanilla: "use_anti_diplomat_prompt: false"
    - Anti-Diplomat: "use_anti_diplomat_prompt: true"
    
    The JSON output structure likely contains the 'config' or 'metadata'.
    If not, we might have to rely on the fact that we just ran them.
    
    Let's check the JSON content structure first to be sure how to detect the mode.)
"""

import json
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Constants
RUNS_DIR = Path("outputs/runs")
OUTPUT_FILE = Path("benchmark_scores/bias_sensitivity.csv")
MODULE_ID = "political_compass"

def load_json_results() -> List[Dict]:
    """Loads all Political Compass result JSONs."""
    results = []
    if not RUNS_DIR.exists():
        logger.warning(f"Directory {RUNS_DIR} does not exist.")
        return results

    for f in RUNS_DIR.glob(f"results_{MODULE_ID}_*.json"): # Old format naming
        try:
            with open(f, "r", encoding="utf-8") as fd:
                data = json.load(fd)
                results.append(data)
        except Exception as e:
            logger.error(f"Error reading {f}: {e}")
            
    # Also check for newer naming convention if applicable (e.g. results_model_date.json)
    # The user filenames saw: results_ministral_3_14b_20260204_194927.json
    # These contain the model name, not necessarily the module in the prefix if not standardized.
    # Let's iterate all JSONs and filter by module_id inside.
    
    results = []
    for f in RUNS_DIR.glob("*.json"):
        try:
            with open(f, "r", encoding="utf-8") as fd:
                data = json.load(fd)
                # Check module
                is_pol_compass = (
                    data.get("module") == "political_compass" or 
                    data.get("metadata", {}).get("module_id") == "political_compass" or
                    "archetype" in data # Heuristic for Political Compass result
                )
                
                if is_pol_compass:
                     # Add filename for reference
                    data["_filename"] = f.name
                    results.append(data)
        except Exception as e:
            pass # Not a valid result file
            
    return results

def detect_run_mode(data: Dict, x: float = 0.0) -> str:
    """
    Determines if a run was 'Vanilla' or 'Forced/Anti-Diplomat'.
    """
    # 1. Check explicit config (New runs)
    config = data.get("config", {})
    if config.get("use_anti_diplomat_prompt") is True:
        return "Anti-Diplomat"
    if config.get("use_anti_diplomat_prompt") is False:
        return "Vanilla"

    # 2. Heuristic for legacy runs (Specific to Ministral/Qwen known values)
    # Ministral Anti-Diplomat was ~ -5.08 X
    if abs(x - (-5.08)) < 0.1: 
        return "Anti-Diplomat"
    
    # Default to Vanilla if ambiguous
    return "Vanilla"

def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def generate_report():
    data = load_json_results()
    if not data:
        print("❌ No data found.")
        return

    # Organize by Model
    model_runs = {}
    
    for run in data:
        # Extract ID
        model_id = run.get("model_id") or run.get("model", "unknown")
        
        # Parse Scores
        scores = run.get("scores", {})
        # Depending on structure, might be raw values or nested
        # Our political compass outputs usually custom metrics like x_score, y_score
        
        # Look for the specific metrics
        metrics = run.get("metrics", {})
        coords = run.get("coordinates", {}) # Top level coordinates
        
        x = metrics.get("political_compass_economic")
        if x is None: x = coords.get("x")
            
        y = metrics.get("political_compass_social")
        if y is None: y = coords.get("y")
        
        if x is None or y is None:
            # Try parsing from "results" or "summary" if structure varies
            continue

        timestamp = run.get("timestamp", "")
        
        # Determine Mode
        mode = detect_run_mode(run, float(x))

        if model_id not in model_runs:
            model_runs[model_id] = []
            
        model_runs[model_id].append({
            "mode": mode,
            "x": float(x),
            "y": float(y),
            "timestamp": timestamp,
            "file": run.get("_filename")
        })

    # Compare
    report_rows = []
    
    for model, runs in model_runs.items():
        # Find latest Vanilla
        vanillas = sorted([r for r in runs if r["mode"] == "Vanilla"], key=lambda k: k["timestamp"], reverse=True)
        antis = sorted([r for r in runs if r["mode"] == "Anti-Diplomat"], key=lambda k: k["timestamp"], reverse=True)
        
        if not vanillas:
            continue
            
        latest_vanilla = vanillas[0]
        
        # If we have an Anti-Diplomat run, compare against the latest one
        latest_anti = antis[0] if antis else None
        
        row = {
            "Model": model,
            "Vanilla X": f"{latest_vanilla['x']:.2f}",
            "Vanilla Y": f"{latest_vanilla['y']:.2f}",
            "Anti-Diplomat X": "—",
            "Anti-Diplomat Y": "—",
            "Delta X": "—",
            "Delta Y": "—",
            "Shift Distance": "—"
        }
        
        if latest_anti:
            row["Anti-Diplomat X"] = f"{latest_anti['x']:.2f}"
            row["Anti-Diplomat Y"] = f"{latest_anti['y']:.2f}"
            
            dx = latest_anti['x'] - latest_vanilla['x']
            dy = latest_anti['y'] - latest_vanilla['y']
            dist = calculate_distance(latest_vanilla['x'], latest_vanilla['y'], latest_anti['x'], latest_anti['y'])
            
            row["Delta X"] = f"{dx:+.2f}"
            row["Delta Y"] = f"{dy:+.2f}"
            row["Shift Distance"] = f"{dist:.2f}"
            
        report_rows.append(row)

    # Output
    df = pd.DataFrame(report_rows)
    print("\n📊 Bias Sensitivity Report")
    # print(df.to_markdown(index=False)) # Requires tabulate
    print(df.to_string(index=False)) 
    
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ Saved report to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_report()
