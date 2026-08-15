#!/usr/bin/env python3
import sys
import math
import json
import logging
from pathlib import Path
import time


sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.model_utils import resolve_provider
from utils.llm_client import LLMClient
from utils.config_validator import ConfigValidator
from benchmark_modules.political_compass.test import PoliticalCompassTest
from benchmark_modules.political_compass.core.io_manager import CheckpointManager

logger = logging.getLogger(__name__)


def get_anomalies(threshold=1.0, provider_filter=None, model_id=None):
    latest_shifts = {}
    runs_dir = Path("outputs/runs")

    if not runs_dir.exists():
        return []

    model_files = {}
    for json_file in runs_dir.glob("results_*.json"):
        try:
            with open(json_file, encoding="utf-8") as f:
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
            if provider_filter and provider_filter not in ("all", row_provider):
                continue

            model_files.setdefault(model_name, []).append((json_file.stat().st_mtime, data))
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.debug("Ergebnis-Datei übersprungen (Parse-Fehler): %s", exc)

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

def _run_one_verification_iteration(
    model: str,
    iteration: int,
    client,
    provider: str,
) -> tuple[tuple[float, float], tuple[float, float], object] | None:
    """Eine einzelne Iteration ausfuehren. Gibt (vanilla, forced, base_result) zurueck oder None bei Fehler."""
    print(f"\n--- {model} | ITERATION {iteration}/3 ---")

    checkpoint = CheckpointManager.load_checkpoint(model) or {}
    checkpoint["responses"] = {}
    checkpoint["run_seeds"] = {}
    CheckpointManager.save_checkpoint(model, checkpoint)

    test = PoliticalCompassTest()
    test.verification_mode = True
    test.num_runs = 2

    base_result = test.execute(model, client, provider=provider)

    if not base_result or base_result.status != "success":
        print(f"[{model}] Iteration {iteration} failed. Skipping model.")
        return None

    try:
        report = json.loads(base_result.raw_response)
        v_x = float(report.get("runs", {}).get("vanilla", {}).get("coordinates", {}).get("x", 0))
        v_y = float(report.get("runs", {}).get("vanilla", {}).get("coordinates", {}).get("y", 0))
        f_x = float(report.get("runs", {}).get("forced", {}).get("coordinates", {}).get("x", 0))
        f_y = float(report.get("runs", {}).get("forced", {}).get("coordinates", {}).get("y", 0))
    except (json.JSONDecodeError, AttributeError, KeyError) as e:
        print(f"[{model}] Iteration {iteration} failed to parse results: {e}")
        return None

    time.sleep(5)
    return (v_x, v_y), (f_x, f_y), base_result


def _run_triple_iterations(model: str, client, provider: str) -> tuple[list[tuple[float, float]], list[tuple[float, float]], object]:
    vanilla_coords: list[tuple[float, float]] = []
    forced_coords: list[tuple[float, float]] = []
    last_base_result = None
    for iteration in range(1, 4):
        result = _run_one_verification_iteration(model, iteration, client, provider)
        if result is None:
            break
        vanilla_coords.append(result[0])
        forced_coords.append(result[1])
        last_base_result = result[2]
    return vanilla_coords, forced_coords, last_base_result


def _print_verification_summary(
    model: str,
    vanilla_coords: list[tuple[float, float]],
    forced_coords: list[tuple[float, float]],
    final_v: tuple[float, float],
    final_f: tuple[float, float],
    final_shift_mag: float,
) -> None:
    print("\n==================================")
    print(f"[{model}] VERIFICATION COMPLETE")
    print(f"Vanilla Iterations: {vanilla_coords}")
    print(f"Forced Iterations:  {forced_coords}")
    print(f"Final Vanilla: ({final_v[0]:.2f}, {final_v[1]:.2f})")
    print(f"Final Forced:  ({final_f[0]:.2f}, {final_f[1]:.2f})")
    print(f"Final Shift:   {final_shift_mag:.2f}")
    print("==================================\n")


def _update_run_coordinates(run_data: dict, x: float, y: float) -> None:
    coords = run_data.get("coordinates")
    if not isinstance(coords, dict):
        coords = {}
        run_data["coordinates"] = coords
    coords["x"] = x
    coords["y"] = y


def _inject_verified_coordinates(safe_report: dict, final_v: tuple[float, float], final_f: tuple[float, float]) -> None:
    final_v_x, final_v_y = round(final_v[0], 2), round(final_v[1], 2)
    final_f_x, final_f_y = round(final_f[0], 2), round(final_f[1], 2)

    if "runs" in safe_report:
        vanilla_run = safe_report["runs"].get("vanilla")
        forced_run = safe_report["runs"].get("forced")
        if isinstance(vanilla_run, dict):
            _update_run_coordinates(vanilla_run, final_v_x, final_v_y)
        if isinstance(forced_run, dict):
            _update_run_coordinates(forced_run, final_f_x, final_f_y)

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


def _set_shift_block(safe_report: dict, final_v: tuple[float, float], final_f: tuple[float, float], final_shift_mag: float) -> float:
    orig_polarity_flip_rate = safe_report.get("shift", {}).get("polarity_flip_rate", 0.0)
    safe_report["shift"] = {
        "x": round(final_f[0] - final_v[0], 2),
        "y": round(final_f[1] - final_v[1], 2),
        "distance": round(final_shift_mag, 2),
        "polarity_flip_rate": orig_polarity_flip_rate,
    }
    safe_report["is_retest"] = True
    return float(orig_polarity_flip_rate)


def _write_audit_log_and_csv(
    model: str,
    safe_report: dict,
    final_v: tuple[float, float],
    final_f: tuple[float, float],
    final_shift_mag: float,
    polarity_flip_rate: float,
) -> None:
    from benchmark_modules.political_compass.core.audit_logger import AuditLogWriter

    vanilla_run_data = safe_report.get("runs", {}).get("vanilla", {})
    forced_run_data = safe_report.get("runs", {}).get("forced", {})
    vanilla_res_for_audit = {
        "score_x": vanilla_run_data.get("coordinates", {}).get("x", final_v[0]),
        "score_y": vanilla_run_data.get("coordinates", {}).get("y", final_v[1]),
    }
    forced_res_for_audit = {
        "score_x": forced_run_data.get("coordinates", {}).get("x", final_f[0]),
        "score_y": forced_run_data.get("coordinates", {}).get("y", final_f[1]),
    }

    AuditLogWriter.write_audit_log(
        model=model,
        vanilla_res=vanilla_res_for_audit,
        forced_res=forced_res_for_audit,
        shift_x=float(final_f[0] - final_v[0]),
        shift_y=float(final_f[1] - final_v[1]),
        shift_distance=float(final_shift_mag),
        polarity_flip_rate=polarity_flip_rate,
        detailed_responses=safe_report.get("detailed_responses", {}),
        verification_mode=True,
    )

    try:
        from benchmark_modules.political_compass.core.io_manager import PoliticalCompassResultManager
        from pathlib import Path

        out_dir = Path("benchmark_scores")
        PoliticalCompassResultManager.save_leaderboard_csv(safe_report, out_dir)
        PoliticalCompassResultManager.save_json(safe_report, Path("outputs/runs"))
        print(f"[{model}] Werte im JSON/Cache Cache (outputs/runs/) gesichert.")
        print(f"[{model}] Werte in political_compass_leaderboard.csv aktualisiert.")
    except Exception as e:
        print(f"[{model}] Fehler beim Aktualisieren des Leaderboards: {e}")


def _regenerate_leaderboard_and_review(model: str) -> None:
    import subprocess
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
        check=True,
    )


def _verify_single_model(
    model: str,
    vanilla_coords: list[tuple[float, float]],
    forced_coords: list[tuple[float, float]],
    last_base_result,
) -> None:
    if len(vanilla_coords) != 3:
        return

    final_v = cluster_and_drop_outlier(vanilla_coords)
    final_f = cluster_and_drop_outlier(forced_coords)
    final_shift_mag = math.hypot(final_f[0] - final_v[0], final_f[1] - final_v[1])
    _print_verification_summary(model, vanilla_coords, forced_coords, final_v, final_f, final_shift_mag)

    try:
        all_zero = all(x == 0.0 and y == 0.0 for x, y in vanilla_coords + forced_coords)
        if all_zero:
            print(f"[{model}] Alle Iterationen lieferten (0.0, 0.0) — keine validen Daten, Audit-Log wird übersprungen.")
            return

        print(f"[{model}] Generiere konsolidiertes Audit-Protokoll...")

        raw = getattr(last_base_result, "raw_response", None)
        if not raw:
            print(f"[{model}] raw_response ist None — Audit-Log wird übersprungen.")
            return

        safe_report = json.loads(raw)
        _inject_verified_coordinates(safe_report, final_v, final_f)
        polarity_flip_rate = _set_shift_block(safe_report, final_v, final_f, final_shift_mag)
        _write_audit_log_and_csv(model, safe_report, final_v, final_f, final_shift_mag, polarity_flip_rate)
        _regenerate_leaderboard_and_review(model)
    except Exception as e:
        print(f"[{model}] Fehler beim Generieren des Reviews/Protokolls: {e}")


def run_verification(provider_filter=None, model_id=None, threshold=1.0):
    anomalies = get_anomalies(threshold=threshold, provider_filter=provider_filter, model_id=model_id)
    if not anomalies:
        print("No anomalous models found (Shift > 1.0).")
        return

    print(f"Triggering verification for {len(anomalies)} models: {anomalies}")

    val = ConfigValidator("benchmark_config.yaml")
    client = LLMClient(config=val.config)

    for model in anomalies:
        print(f"\n[{model}] Starting Anomaly Verification Protocol (Triple-Run)...")
        provider, _ = resolve_provider(model)
        vanilla_coords, forced_coords, last_base_result = _run_triple_iterations(model, client, provider)
        _verify_single_model(model, vanilla_coords, forced_coords, last_base_result)


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
