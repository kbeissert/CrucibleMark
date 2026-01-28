import json
import csv
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

class UXResultManager:
    """
    Handles file I/O and reporting for UX Writing results.
    Separates data persistence and presentation from business logic.
    """

    @staticmethod
    def generate_filename(model: str, scenario_id: str, prefix: str = "ux_result") -> str:
        """Generates a consistent filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_model = re.sub(r"[^a-zA-Z0-9]", "_", model)
        safe_scenario = re.sub(r"[^a-zA-Z0-9]", "_", scenario_id)
        return f"{prefix}_{safe_model}_{safe_scenario}_{timestamp}"

    @staticmethod
    def save_json(report: Dict[str, Any], directory: Path, filename: str | None = None) -> Path:
        """Saves the full report as JSON."""
        if not filename:
            filename = UXResultManager.generate_filename(
                report.get("model", "unknown"),
                report.get("scenario_id", "unknown")
            ) + ".json"
        
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)

        filepath = directory / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"💾 JSON gespeichert: {filepath}")
        return filepath

    @staticmethod
    def save_csv(report: Dict[str, Any], filepath: Path) -> Path:
        """Appends the result to a CSV leaderboard file."""
        file_exists = filepath.exists()
        
        # Ensure directory exists
        if not filepath.parent.exists():
            filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "a", newline="", encoding="utf-8") as f:
            fieldnames = [
                "model",
                "test_date",
                "scenario_id",
                "scenario_name",
                "total_score",
                "error_detection_score",
                "solution_quality_score",
                "formatting_score",
                "bonus_score"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()
            
            # Extract scores safely
            scores = report.get("scores", {})
            writer.writerow(
                {
                    "model": report.get("model", "unknown"),
                    "test_date": report.get("timestamp", datetime.now().isoformat()),
                    "scenario_id": report.get("scenario_id", "unknown"),
                    "scenario_name": report.get("scenario_name", "unknown"),
                    "total_score": scores.get("total", 0.0),
                    "error_detection_score": scores.get("error_detection", 0.0),
                    "solution_quality_score": scores.get("solution_quality", 0.0),
                    "formatting_score": scores.get("formatting", 0.0),
                    "bonus_score": scores.get("bonus", 0.0)
                }
            )

        print(f"💾 CSV gespeichert: {filepath}")
        return filepath

    @staticmethod
    def print_summary(report: Dict[str, Any]):
        """Prints a CLI summary of the report."""
        scores = report.get("scores", {})
        print("\n" + "=" * 80)
        print(f"UX WRITING TEST - {report.get('scenario_name', 'Unknown')}")
        print("=" * 80)
        print(f"Modell: {report.get('model', 'unknown')}")
        print(f"Datum: {report.get('timestamp', 'unknown')}")
        print(f"Scenario ID: {report.get('scenario_id', 'unknown')}")
        print("-" * 80)
        print(f"GESAMTPUNKTZAHL: {scores.get('total', 0.0):.1f} / 100")
        print("-" * 80)
        print(f"  • Error Detection:  {scores.get('error_detection', 0.0):.1f}")
        print(f"  • Solution Quality: {scores.get('solution_quality', 0.0):.1f}")
        print(f"  • Formatting:       {scores.get('formatting', 0.0):.1f}")
        print(f"  • Bonus:            {scores.get('bonus', 0.0):.1f}")
        print("=" * 80)
