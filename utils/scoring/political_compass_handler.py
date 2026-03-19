"""
Handler for Political Compass outputs to enforce Separation of Concerns.
Extracts Political Compass result generation and persistence from core runners.
"""

import csv
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from utils.benchmark_utils import (
    format_pc_run_data,
    format_political_compass_data,
    prepare_pc_csv_row,
)

# pylint: disable=invalid-name,broad-exception-caught

logger = logging.getLogger(__name__)

# Optional bindings to Political Compass modules
try:
    from benchmark_modules.political_compass.core.io_manager import (
        PoliticalCompassResultManager as PCResultManager,
    )
    from benchmark_modules.political_compass.core.audit_logger import (
        AuditLogWriter as PCAuditLogWriter,
    )
except ImportError:
    PCResultManager = None  # type: ignore
    PCAuditLogWriter = None  # type: ignore


class PoliticalCompassHandler:
    """Delegates reporting and file-writing for the Political Compass module."""

    @staticmethod
    def is_political_compass(benchmark_info: Dict[str, Any]) -> bool:
        """Determines if the benchmark is the Political Compass module."""
        module_id = benchmark_info.get("id", "")
        return (
            module_id in ["political_compass", "political_compass_v3"]
            or benchmark_info.get("name", "") == "Political Compass"
        )

    @classmethod
    def handle_results(
        cls,
        model: str,
        report: Dict[str, Any],
        model_version: str,
        test_instance: Any,
        audit_mode: bool = False,
        provider_type: str = "ollama",
    ) -> None:
        """
        End-to-end processing of Political Compass outputs.
        Replaces the verbose procedural reporting in both local and commercial runners.
        """
        if not PCResultManager:
            logger.warning(
                "PoliticalCompassResultManager could not be imported. Skipping PC outputs."
            )
            return

        try:
            PCResultManager.print_summary(report)
            output_dir = Path("outputs/runs")
            output_dir.mkdir(exist_ok=True, parents=True)
            PCResultManager.save_json(report, output_dir)
        except Exception as e:
            logger.error("Political compass manager print/JSON failed: %s", e)

        try:
            if provider_type == "ollama":
                cls._update_local_pc_csv(model, report, model_version)
            else:
                cls._update_commercial_pc_csv(model, report, model_version)
        except Exception as e:
            logger.error("Political compass CSV update failed: %s", e)

        try:
            cls._generate_derivatives(
                model, report, test_instance, audit_mode, provider_type
            )
        except Exception as e:
            logger.error("Political compass derivatives failed: %s", e)

        # Trigger automatic verification on high shifts
        try:
            is_retest = report.get("is_retest", getattr(test_instance, "verification_mode", False))
            shift_dist = float(report.get("shift", {}).get("distance", 0.0))
            config = getattr(test_instance, "config", {})
            threshold = float(config.get("anomaly_shift_threshold", 1.0))
            if shift_dist > threshold and not is_retest:
                import subprocess, sys
                print(f"\n🚨 [SAFETY ALERT] Automatischer Sicherheits-Trigger: Shift ({shift_dist:.2f} > {threshold}) bei '{model}' erkannt!")
                print("🛡️  Starte Anomaly Verification Protocol (Triple-Run Verification)...\n")
                subprocess.run(
                    [sys.executable, "scripts/core/verify_compass_anomalies.py", "--model", model, "--threshold", str(threshold)],
                    check=False
                )
        except Exception as e:
            logger.error("Political compass anomaly trigger failed: %s", e)

    @staticmethod
    def _update_local_pc_csv(
        model: str, report: Dict[str, Any], model_version: str
    ) -> None:
        """Original append-only logic for local runner."""
        pc_csv = Path("benchmark_scores/political_compass_results.csv")
        pc_csv.parent.mkdir(exist_ok=True, parents=True)

        fieldnames = [
            "model",
            "model_version",
            "run_id",
            "x_coordinate",
            "y_coordinate",
            "x_label",
            "y_label",
            "metrics_json",
            "timestamp",
        ]
        file_exists = pc_csv.exists() and pc_csv.stat().st_size > 0
        rows_to_write = []
        timestamp_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")

        if "individual_runs" in report:
            for i, run in enumerate(report["individual_runs"], 1):
                run_formatted = format_pc_run_data(run, include_extremism=False)
                rows_to_write.append(
                    {
                        "model": model,
                        "model_version": model_version,
                        "run_id": f"RUN_{run.get('id', i)}",
                        "x_coordinate": run.get("x", 0.0),
                        "y_coordinate": run.get("y", 0.0),
                        "x_label": run.get("x_label", ""),
                        "y_label": run.get("y_label", ""),
                        "metrics_json": json.dumps(
                            run_formatted, ensure_ascii=False
                        ),
                        "timestamp": timestamp_str,
                    }
                )

        avg_formatted = format_pc_run_data(
            {
                "x": report.get("coordinates", {}).get("x", 0.0),
                "y": report.get("coordinates", {}).get("y", 0.0),
                "x_label": report.get("archetype", {}).get("x_label", ""),
                "y_label": report.get("archetype", {}).get("y_label", ""),
                "extremism": report.get("extremism", {}),
                "sigma": report.get("sigma", {}),
                "module_stats": report.get("statistics", {}).get("module_stats", {}),
            },
            include_extremism=True,
        )

        rows_to_write.append(
            {
                "model": model,
                "model_version": model_version,
                "run_id": "AVG",
                "x_coordinate": report.get("coordinates", {}).get("x", 0.0),
                "y_coordinate": report.get("coordinates", {}).get("y", 0.0),
                "x_label": report.get("archetype", {}).get("x_label", ""),
                "y_label": report.get("archetype", {}).get("y_label", ""),
                "metrics_json": json.dumps(avg_formatted, ensure_ascii=False),
                "timestamp": timestamp_str,
            }
        )

        with open(pc_csv, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if not file_exists:
                writer.writeheader()
            writer.writerows(rows_to_write)

    @staticmethod
    def _update_commercial_pc_csv(
        model: str, report: Dict[str, Any], model_version: str
    ) -> None:
        """Original read-replace-write logic for commercial runner."""
        pc_csv = Path("benchmark_scores/political_compass_results.csv")
        pc_csv.parent.mkdir(exist_ok=True, parents=True)

        fieldnames = [
            "model",
            "model_version",
            "run_id",
            "x_coordinate",
            "y_coordinate",
            "x_label",
            "y_label",
            "metrics_json",
            "timestamp",
        ]
        pc_rows = []
        if pc_csv.exists():
            with open(pc_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                pc_rows = list(reader)
                if reader.fieldnames:
                    for col in reader.fieldnames:
                        if col not in fieldnames:
                            fieldnames.append(col)

        pc_rows = [r for r in pc_rows if r.get("model") != model]

        data_object = format_political_compass_data(report)
        new_row = prepare_pc_csv_row(
            model, report, data_object, model_version=model_version
        )
        new_row["timestamp"] = datetime.now().isoformat()
        pc_rows.append(new_row)

        with open(pc_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(pc_rows)

    @staticmethod
    def _generate_derivatives(
        model: str,
        report: Dict[str, Any],
        test_instance: Any,
        audit_mode: bool,
        provider_type: str,
    ) -> None:
        """Generates audit logs and leaderboard CSV if applicable."""
        runs = report.get("runs", {})
        vanilla_run = runs.get("vanilla", {})
        forced_run = runs.get("forced", {})
        shift = report.get("shift", {})

        if audit_mode and PCAuditLogWriter:
            try:
                vanilla_for_audit = {
                    "score_x": vanilla_run.get("coordinates", {}).get("x", 0.0),
                    "score_y": vanilla_run.get("coordinates", {}).get("y", 0.0),
                }
                forced_for_audit = {
                    "score_x": forced_run.get("coordinates", {}).get("x", 0.0),
                    "score_y": forced_run.get("coordinates", {}).get("y", 0.0),
                }
                verification_mode = getattr(test_instance, "verification_mode", False)
                safety_metadata = getattr(test_instance, "safety_metadata", None)
                PCAuditLogWriter.write_audit_log(
                    model=model,
                    vanilla_res=vanilla_for_audit,
                    forced_res=forced_for_audit,
                    shift_x=float(shift.get("x", 0.0)),
                    shift_y=float(shift.get("y", 0.0)),
                    shift_distance=float(shift.get("distance", 0.0)),
                    detailed_responses=report.get("detailed_responses", {}),
                    verification_mode=verification_mode,
                    safety_metadata=safety_metadata,
                )
            except Exception as e:
                logger.error("Political Compass Audit Error: %s", e)

        if PCResultManager:
            try:
                PCResultManager.save_leaderboard_csv(report, Path("benchmark_scores"))
            except Exception as e:
                logger.error("Political Compass Leaderboard Error: %s", e)
