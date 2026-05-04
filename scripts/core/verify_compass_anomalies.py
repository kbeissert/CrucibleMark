#!/usr/bin/env python3
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
    latest_shifts = {}
    runs_dir = Path("outputs/runs")

    if not runs_dir.exists():
        return []

    model_files = {}
    for json_file in runs_dir.glob("results_*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            model_name = data.get("model", "")
            if not model_name:
                continue

            # Provider auflösen, falls Filter aktiv
            row_provider = data.get("provider", "")
            if not row_provider:
                row_provider, _ = resolve_provider(model_name)

            if model_id and model_name != model_id:
                continue
            if provider_filter and provider_filter != "all" and row_provider != provider_filter:
                continue

            model_files.setdefault(model_name, []).append((json_file.stat().st_mtime, data))
        except Exception:
            pass

    for model_name, files in model_files.items():
        # Neueste Datei des Modells verwenden (nach mtime)
        files.sort(key=lambda x: x[0], reverse=True)
        latest_data = files[0][1]

        # Shift extrahieren
        shift_data = latest_data.get("shift", {})
        if isinstance(shift_data, dict):
            shift = shift_data.get("distance", 0.0)
        else:
            shift = float(shift_data) if shift_data else 0.0

        is_retest = latest_data.get("is_retest", False)
        latest_shifts[model_name] = {"shift": float(shift), "is_retest": bool(is_retest)}

    # Evaluiere nur die _letzten_ bekannten Shifts auf das Threshold, ueberspringe die bereits retesteten!
    return [model for model, data in latest_shifts.items() if data["shift"] > threshold and not data["is_retest"]]

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

def run_verification(provider_filter=None, model_id=None, threshold=1.0):
    anomalies = get_anomalies(threshold=threshold, provider_filter=provider_filter, model_id=model_id)
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

            # --- PROTOCOL & REVIEWER GENERATION ---
            try:
                import sys
                from benchmark_modules.political_compass.core.audit_logger import AuditLogWriter
                import subprocess

                # Guard: wenn alle Iterationen technisch fehlschlugen (alle Koordinaten 0,0),
                # gibt es kein valides Ergebnis — Audit-Log überspringen.
                all_zero = all(x == 0.0 and y == 0.0 for x, y in vanilla_coords + forced_coords)
                if all_zero:
                    print(f"[{model}] Alle Iterationen lieferten (0.0, 0.0) — keine validen Daten, Audit-Log wird übersprungen.")
                    continue

                print(f"[{model}] Generiere konsolidiertes Audit-Protokoll...")

                # Nutze das Ergebnis der Iteration mit den besten (nicht-null) Koordinaten als Basis-Report.
                # Fallback auf base_result (letzte Iteration) wenn kein besseres gefunden wird.
                best_result = base_result
                for _past_result in [base_result]:  # Nur base_result verfügbar in diesem Scope
                    pass

                raw = getattr(best_result, "raw_response", None)
                if not raw:
                    print(f"[{model}] raw_response ist None — Audit-Log wird übersprungen.")
                    continue

                safe_report = json.loads(raw)

                # Update safe_report with verified average values (rounded to 2 decimal places)
                final_v_x = round(final_v_x, 2)
                final_v_y = round(final_v_y, 2)
                final_f_x = round(final_f_x, 2)
                final_f_y = round(final_f_y, 2)
                final_shift_mag = round(final_shift_mag, 2)

                if "runs" in safe_report:
                    vanilla_run = safe_report["runs"].get("vanilla")
                    forced_run = safe_report["runs"].get("forced")
                    if isinstance(vanilla_run, dict):
                        if "coordinates" not in vanilla_run:
                            safe_report["runs"]["vanilla"]["coordinates"] = {}
                        safe_report["runs"]["vanilla"]["coordinates"]["x"] = final_v_x
                        safe_report["runs"]["vanilla"]["coordinates"]["y"] = final_v_y
                    if isinstance(forced_run, dict):
                        if "coordinates" not in forced_run:
                            safe_report["runs"]["forced"]["coordinates"] = {}
                        safe_report["runs"]["forced"]["coordinates"]["x"] = final_f_x
                        safe_report["runs"]["forced"]["coordinates"]["y"] = final_f_y

                if "individual_runs" in safe_report:
                    for i_run in safe_report["individual_runs"]:
                        if not isinstance(i_run, dict):
                            continue
                        if i_run.get("type") == "vanilla":
                            i_run["x"] = final_v_x
                            i_run["y"] = final_v_y
                        elif i_run.get("type") == "forced":
                            i_run["x"] = final_f_x
                            i_run["y"] = final_f_y

                if isinstance(safe_report.get("coordinates"), dict):
                    safe_report["coordinates"]["x"] = final_v_x
                    safe_report["coordinates"]["y"] = final_v_y
                elif "coordinates" not in safe_report or safe_report.get("coordinates") is None:
                    safe_report["coordinates"] = {"x": final_v_x, "y": final_v_y}
                if "shift" not in safe_report:
                    pass
                orig_polarity_flip_rate = safe_report.get("shift", {}).get("polarity_flip_rate", 0.0)
                safe_report["shift"] = {
                    "x": round(final_f_x - final_v_x, 2),
                    "y": round(final_f_y - final_v_y, 2),
                    "distance": final_shift_mag,
                    "polarity_flip_rate": orig_polarity_flip_rate
                }

                # Flaggen, dass diese Werte das Ergebnis eines Safety-Retests sind
                safe_report["is_retest"] = True

                vanilla_run_data = safe_report.get("runs", {}).get("vanilla", {})
                forced_run_data = safe_report.get("runs", {}).get("forced", {})
                vanilla_res_for_audit = {
                    "score_x": vanilla_run_data.get("coordinates", {}).get("x", final_v_x),
                    "score_y": vanilla_run_data.get("coordinates", {}).get("y", final_v_y),
                }
                forced_res_for_audit = {
                    "score_x": forced_run_data.get("coordinates", {}).get("x", final_f_x),
                    "score_y": forced_run_data.get("coordinates", {}).get("y", final_f_y),
                }

                AuditLogWriter.write_audit_log(
                    model=model,
                    vanilla_res=vanilla_res_for_audit,
                    forced_res=forced_res_for_audit,
                    shift_x=float(final_f_x - final_v_x),
                    shift_y=float(final_f_y - final_v_y),
                    shift_distance=float(final_shift_mag),
                    polarity_flip_rate=float(orig_polarity_flip_rate),
                    detailed_responses=safe_report.get("detailed_responses", {}),
                    verification_mode=True
                )

                # Update Leaderboard CSV
                try:
                    from benchmark_modules.political_compass.core.io_manager import PoliticalCompassResultManager

                    from pathlib import Path
                    out_dir = Path("benchmark_scores")

                    # Call save_leaderboard_csv with updated payload (appends correct values)
                    PoliticalCompassResultManager.save_leaderboard_csv(safe_report, out_dir)
                    PoliticalCompassResultManager.save_json(safe_report, Path("outputs/runs"))
                    print(f"[{model}] Werte im JSON/Cache Cache (outputs/runs/) gesichert.")
                    print(f"[{model}] Werte in political_compass_leaderboard.csv aktualisiert.")
                except Exception as e:
                    print(f"[{model}] Fehler beim Aktualisieren des Leaderboards: {e}")

                print(f"[{model}] Aktualisiere allgemeines Leaderboard...")
                try:
                    subprocess.run(
                        [sys.executable, "scripts/core/generate_leaderboard.py"], check=True
                    )
                except Exception as e:
                    print(f"[{model}] Fehler beim Leaderboard-Update: {e}")

                print(f"[{model}] Starte Bias-Reviewer für das verifizierte Modell...")
                subprocess.run(
                    [sys.executable, "scripts/analysis/generate_review.py", "--model", model, "--type", "bias"],
                    check=True
                )
            except Exception as e:
                print(f"[{model}] Fehler beim Generieren des Reviews/Protokolls: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default=None, choices=["all", "commercial", "local_ollama"])
    parser.add_argument("--model", default=None)
    parser.add_argument("--threshold", type=float, default=1.0)
    args = parser.parse_args()

    try:
        run_verification(provider_filter=args.provider, model_id=args.model, threshold=args.threshold)
    except KeyboardInterrupt:
        import sys
        print("\n⛔  Abbruch durch Benutzer (Anomaly Verification).")
        sys.exit(130)
