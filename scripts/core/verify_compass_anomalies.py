#!/usr/bin/env python3
import csv
import sys
import math
import json
from pathlib import Path
import time

import argparse

sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.model_utils import resolve_provider
from utils.llm_client import LLMClient
from utils.config_validator import ConfigValidator
from benchmark_modules.political_compass.test import PoliticalCompassTest
from benchmark_modules.political_compass.core.io_manager import CheckpointManager

def get_anomalies(threshold=1.0, provider_filter=None, model_id=None):
    candidates = []
    csv_path = Path("benchmark_scores/political_compass_leaderboard.csv")
    if not csv_path.exists():
        return candidates
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                shift = float(row.get("shift_distance", 0.0))
                model_name = row.get("model", "")
                row_provider = row.get("provider_type", "")

                # Filters
                if shift <= threshold:
                    continue
                if model_id and model_name != model_id:
                    continue
                if provider_filter and provider_filter != "all" and row_provider != provider_filter:
                    continue

                candidates.append(model_name)
            except (ValueError, KeyError):
                pass
    # Deduplicate in case of multiple runs
    return list(set(candidates))

def calculate_euclidean(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def cluster_and_drop_outlier(results):
    """
    Given 3 coordinate sets (x,y), find the pair with the smallest Euclidean distance.
    Returns the average of that pair, and drops the third (outlier).
    """
    if len(results) < 3:
        return results[0]

    d12 = calculate_euclidean(results[0], results[1])
    d23 = calculate_euclidean(results[1], results[2])
    d13 = calculate_euclidean(results[0], results[2])

    # 12 is closest
    if d12 <= d23 and d12 <= d13:
        avg_x = (results[0][0] + results[1][0]) / 2.0
        avg_y = (results[0][1] + results[1][1]) / 2.0
        return (avg_x, avg_y)
    # 23 is closest
    elif d23 <= d12 and d23 <= d13:
        avg_x = (results[1][0] + results[2][0]) / 2.0
        avg_y = (results[1][1] + results[2][1]) / 2.0
        return (avg_x, avg_y)
    # 13 is closest
    else:
        avg_x = (results[0][0] + results[2][0]) / 2.0
        avg_y = (results[0][1] + results[2][1]) / 2.0
        return (avg_x, avg_y)

def run_verification(provider_filter=None, model_id=None):
    anomalies = get_anomalies(provider_filter=provider_filter, model_id=model_id)
    if not anomalies:
        print("No anomalous models found (Shift > 1.0).")
        return

    print(f"Triggering verification for {len(anomalies)} models: {anomalies}")

    # Initialize the LLM Client once
    val = ConfigValidator("benchmark_config.yaml")
    client = LLMClient(config=val.config)

    for model in anomalies:
        print(f"\n[{model}] Starting Anomaly Verification Protocol (Triple-Run)...")
        provider, _ = resolve_provider(model)

        vanilla_coords = []
        forced_coords = []

        for iteration in range(1, 4):
            print(f"\n--- {model} | ITERATION {iteration}/3 ---")

            # Wipe response cache for true statelessness
            checkpoint = CheckpointManager.load_checkpoint(model) or {}
            checkpoint["responses"] = {}  # force new generations
            checkpoint["run_seeds"] = {}  # force new letter mappings
            CheckpointManager.save_checkpoint(model, checkpoint)

            # Setup fresh Test with custom num_runs logic.
            # In test.py we use getattr(self, "num_runs", 2).
            # By setting it to 3, it signals test.py to apply micro-delays
            # while the execute loop still behaves correctly based on standard modulo
            test = PoliticalCompassTest()
            test.num_runs = 3 # Magic number > 2 triggers sleep in _run_single_block wait wait

            # Wait, if we set test.num_runs = 3, test.py will loop 3 times: Run 1 (Vanilla), Run 2 (Forced), Run 3 (Vanilla).
            # But the results returned are just self.evaluator_vanilla and self.evaluator_forced.
            # Actually, to keep it A/B perfectly, we MUST set num_runs = 2 here, otherwise the results return logic gets weird.
            test.verification_mode = True # Use a custom attribute!
            test.num_runs = 2

            base_result = test.execute(model, client, provider=provider)

            if not base_result or base_result.status != "success":
                print(f"[{model}] Iteration {iteration} failed. Skipping model.")
                break

            try:
                report = json.loads(base_result.raw_response)
                v_x = float(report.get("runs", {}).get("vanilla", {}).get("coordinates", {}).get("x", 0))
                v_y = float(report.get("runs", {}).get("vanilla", {}).get("coordinates", {}).get("y", 0))
                f_x = float(report.get("runs", {}).get("forced", {}).get("coordinates", {}).get("x", 0))
                f_y = float(report.get("runs", {}).get("forced", {}).get("coordinates", {}).get("y", 0))
            except (json.JSONDecodeError, AttributeError, KeyError) as e:
                print(f"[{model}] Iteration {iteration} failed to parse results: {e}")
                break

            vanilla_coords.append((v_x, v_y))
            forced_coords.append((f_x, f_y))

            # Explicit token cool-down between iterations
            time.sleep(5)

        if len(vanilla_coords) == 3:
            # Cluster Vanilla
            final_v_x, final_v_y = cluster_and_drop_outlier(vanilla_coords)
            # Cluster Forced
            final_f_x, final_f_y = cluster_and_drop_outlier(forced_coords)

            final_shift_mag = math.hypot(final_f_x - final_v_x, final_f_y - final_v_y)
            print("\n==================================")
            print(f"[{model}] VERIFICATION COMPLETE")
            print(f"Vanilla Iterations: {vanilla_coords}")
            print(f"Forced Iterations:  {forced_coords}")
            print(f"Final Vanilla: ({final_v_x:.2f}, {final_v_y:.2f})")
            print(f"Final Forced:  ({final_f_x:.2f}, {final_f_y:.2f})")
            print(f"Final Shift:   {final_shift_mag:.2f}")
            print("==================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Political Compass Anomaly Verification")
    parser.add_argument("--provider", type=str, choices=["all", "commercial", "local", "cloud"], default="all", help="Nur Modelle dieses Providers prüfen")
    parser.add_argument("--model_id", type=str, help="Nur dieses spezifische Modell prüfen")
    args = parser.parse_args()

    run_verification(provider_filter=args.provider, model_id=args.model_id)
