"""
I/O Manager Module
==================

Handles file I/O operations for reports and results.
"""

import contextlib
import csv
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from utils.benchmark_ui import TerminalUI
from utils.benchmark_utils import format_pc_run_data

from .constants import DATE_FORMAT, DEFAULT_ENCODING, TEMP_DIR
from .transformers import PoliticalCompassTransformer
from .visualizer import PoliticalCompassVisualizer

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    Manages temporary checkpoint files for session resume.
    """

    @classmethod
    def get_checkpoint_path(cls, model: str) -> Path:
        """Generates a safe file path for the checkpoint."""
        safe_model = re.sub(r"[^a-zA-Z0-9]", "_", model)
        return TEMP_DIR / f"session_{safe_model}.json"

    @classmethod
    def save_checkpoint(cls, model: str, state: dict[str, Any]):
        """Serializes current benchmark state to disk."""
        if not TEMP_DIR.exists():
            TEMP_DIR.mkdir(parents=True, exist_ok=True)

        filepath = cls.get_checkpoint_path(model)
        try:
            with filepath.open("w", encoding=DEFAULT_ENCODING) as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except (OSError, TypeError) as e:
            logger.error("⚠️ Failed to save checkpoint: %s", e)

    @classmethod
    def load_checkpoint(
        cls, model: str, force_new: bool = False, max_age_hours: int = 48
    ) -> dict[str, Any] | None:
        """
        Loads state if exists and is valid.

        Args:
            model: Model identifier
            force_new: If True, deletes existing checkpoint regardless of age
            max_age_hours: Max age in hours before checkpoint is considered undefined/expired
        """
        filepath = cls.get_checkpoint_path(model)

        if not filepath.exists():
            return None

        # Clean forced
        if force_new:
            try:
                filepath.unlink()
                logger.info("🧹 Force-cleaned previous session for %s", model)
            except OSError as e:
                logger.warning("⚠️ Could not delete checkpoint: %s", e)
            return None

        try:
            with filepath.open(encoding=DEFAULT_ENCODING) as f:
                data = json.load(f)

            # Check Expiry
            timestamp = data.get("timestamp", 0)
            age_seconds = time.time() - timestamp
            age_hours = age_seconds / 3600

            if age_hours > max_age_hours:
                logger.info(
                    "🧹 Expired session found (%.1fh old). Starting fresh.", age_hours
                )
                with contextlib.suppress(OSError):
                    filepath.unlink()
                return None

            return data

        except (OSError, json.JSONDecodeError) as e:
            logger.warning("⚠️ Corrupt checkpoint found (ignoring): %s", e)
            return None

    @classmethod
    def clear_checkpoint(cls, model: str):
        """Removes checkpoint file after successful run."""
        filepath = cls.get_checkpoint_path(model)
        if filepath.exists():
            try:
                filepath.unlink()
            except OSError as e:
                logger.warning("⚠️ Failed to clear checkpoint: %s", e)


class ResultManager:
    """
    Handles file I/O and reporting for Political Compass results.
    Separates data persistence and presentation from business logic.
    """

    @staticmethod
    def generate_filename(model: str, prefix: str = "results") -> str:
        """Generates a consistent filename with timestamp."""
        timestamp = datetime.now(timezone.utc).strftime(DATE_FORMAT)
        safe_model = re.sub(r"[^a-zA-Z0-9]", "_", model)
        return f"{prefix}_{safe_model}_{timestamp}"

    @staticmethod
    def save_json(
        report: dict[str, Any], directory: Path, filename: str | None = None
    ) -> Path:
        """Saves the full report as JSON."""
        if not filename:
            filename = (
                ResultManager.generate_filename(report.get("model", "unknown"))
                + ".json"
            )

        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)

        filepath = directory / filename
        with filepath.open("w", encoding=DEFAULT_ENCODING) as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info("💾 JSON gespeichert: %s", filepath)
        return filepath

    @staticmethod
    def _ensure_schema_matches(filepath: Path, fieldnames: list[str]):
        """Handles schema migration if file exists but is missing columns."""
        with filepath.open(encoding=DEFAULT_ENCODING) as f:
            reader = csv.DictReader(f)
            existing_headers = reader.fieldnames or []

        # Check if we have new columns
        new_columns = [col for col in fieldnames if col not in existing_headers]

        if new_columns:
            logger.warning("⚠️ CSV-Schema-Update: Füge Spalten hinzu: %s", new_columns)
            # Read all data
            with filepath.open(encoding=DEFAULT_ENCODING) as f:
                reader = csv.DictReader(f)
                data = list(reader)

            # Rewrite file with new header
            with filepath.open("w", newline="", encoding=DEFAULT_ENCODING) as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in data:
                    # writer ignores extra keys in row? No, we need to preserve existing data
                    # but row doesn't have new keys. DictWriter handles missing keys
                    # by putting empty string (default).
                    # We just write the row as is, DictWriter fills rest with restval (default "")
                    writer.writerow(row)

    @staticmethod
    def save_csv(report: dict[str, Any], filepath: Path) -> Path:
        """Appends the result to a CSV leaderboard file."""
        file_exists = filepath.exists()

        # Ensure directory exists
        if not filepath.parent.exists():
            filepath.parent.mkdir(parents=True, exist_ok=True)

        # 1. Delegation der Logik an Transformer
        row_data = PoliticalCompassTransformer.to_csv_row(report)
        fieldnames = PoliticalCompassTransformer.get_csv_headers(row_data)

        # Handle Schema Migration (if file exists but missing columns)
        if file_exists:
            ResultManager._ensure_schema_matches(filepath, fieldnames)

        with filepath.open("a", newline="", encoding=DEFAULT_ENCODING) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow(row_data)

        logger.info("💾 CSV gespeichert: %s", filepath)
        return filepath

    @staticmethod
    def print_summary(report: dict[str, Any]):
        """Prints a CLI summary of the report using TerminalUI."""
        ui = TerminalUI()

        if "coordinates" not in report: # Defensive check for generic batch modules
            logger.info("Batch Module Execution Completed.")
            if "score" in report:
                print(f"Score: {report['score']} | Status: {report.get('status', 'success')}")
            return

        coords = report["coordinates"]
        sigma = report.get("sigma", {"x": 0.0, "y": 0.0})

        # Generate Chart String
        chart_str = None
        try:
            chart_str = PoliticalCompassVisualizer.generate_ascii_chart(
                coords["x"],
                coords["y"],
            )
        except (ValueError, TypeError, KeyError):
            logger.warning("Failed to generate ASCII chart", exc_info=True)

        ui.print_final_summary(
            model=report.get("model", "Unknown"),
            date_str=report.get("test_date", "Now"),
            coords=(coords["x"], coords["y"]),
            sigma=(sigma["x"], sigma["y"]),
            archetype=report["archetype"]["label"],
            chart=chart_str,
            stats=report.get("statistics", {}),
        )

    @staticmethod
    def save_v2_csv(model: str, results: dict[str, Any], output_dir: Path):
        """
        Speichert Ergebnisse im v2.0 CSV-Format.

        Args:
            model: Modellname
            results: Dict mit coordinates, archetype, extremism, etc.
            output_dir: Zielverzeichnis (benchmark_scores/)
        """
        csv_path = output_dir / "political_compass_results.csv"

        # Check if file exists
        file_exists = csv_path.exists()

        # Ensure directory exists
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        # Build Rows (1 pro Run + 1 Aggregate)
        rows = []

        # Individual Runs
        for run_data in results.get("individual_runs", []):
            run_formatted = format_pc_run_data(run_data, include_extremism=False)

            rows.append(
                {
                    "model": model,
                    "module": "political_compass",
                    "run_id": f"RUN_{run_data.get('id', '?')}",
                    "status": "success",
                    "execution_time": round(
                        results["statistics"].get("execution_time", 0) / 3, 2
                    ),
                    "metadata_json": json.dumps(run_formatted, default=str),
                }
            )

        # Aggregate Row
        avg_formatted = format_pc_run_data(
            {
                "x": results["coordinates"]["x"],
                "y": results["coordinates"]["y"],
                "x_label": results["archetype"]["x_label"],
                "y_label": results["archetype"]["y_label"],
                "extremism": results.get("extremism", {}),
                "sigma": results.get("sigma", {}),
                "module_stats": results["statistics"].get("module_stats", {}),
            },
            include_extremism=True,
        )

        rows.append(
            {
                "model": model,
                "module": "political_compass",
                "run_id": "AVG",
                "status": "success",
                "execution_time": round(
                    results["statistics"].get("execution_time", 0), 2
                ),
                "metadata_json": json.dumps(avg_formatted, default=str),
            }
        )

        # Write to CSV
        fieldnames = [
            "model",
            "module",
            "run_id",
            "status",
            "execution_time",
            "metadata_json",
        ]

        with open(
            csv_path, "a" if file_exists else "w", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if not file_exists:
                writer.writeheader()
            writer.writerows(rows)

        logger.info("💾 v2 CSV gespeichert: %s", csv_path)
