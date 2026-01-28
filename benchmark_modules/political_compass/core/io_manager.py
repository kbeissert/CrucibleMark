"""
I/O Manager Module
==================

Handles file I/O operations for reports and results.
"""
import json
import csv
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from .visualizer import PoliticalCompassVisualizer
from utils.benchmark_ui import TerminalUI

class ResultManager:
    """
    Handles file I/O and reporting for Political Compass results.
    Separates data persistence and presentation from business logic.
    """

    @staticmethod
    def generate_filename(model: str, prefix: str = "results") -> str:
        """Generates a consistent filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_model = re.sub(r"[^a-zA-Z0-9]", "_", model)
        return f"{prefix}_{safe_model}_{timestamp}"

    @staticmethod
    def save_json(report: Dict[str, Any], directory: Path, filename: str | None = None) -> Path:
        """Saves the full report as JSON."""
        if not filename:
            filename = ResultManager.generate_filename(report.get("model", "unknown")) + ".json"

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

        # Prepare Data
        row_data = {
            "model": report["model"],
            "test_date": report["test_date"],
            "x": report["coordinates"]["x"],
            "y": report["coordinates"]["y"],
            "archetype": report["archetype"]["label"],
            "extremism_count": report["extremism"]["count"],
            "extremism_rate": f"{report['extremism']['rate']}%",
            "status": report["extremism"]["status"],
            "final_verdict": report["final_verdict"],
        }

        # Add Token Efficiency Data
        module_stats = report.get("statistics", {}).get("module_stats", {})
        token_fields = []
        for mod_id in sorted(module_stats.keys()):
            tokens = module_stats[mod_id]["tokens"]
            count = module_stats[mod_id]["count"]
            tpg = round(tokens / count, 2) if count > 0 else 0.0

            row_data[f"module_{mod_id}_tokens"] = tokens
            row_data[f"module_{mod_id}_tpg"] = tpg

            token_fields.append(f"module_{mod_id}_tokens")
            token_fields.append(f"module_{mod_id}_tpg")

        fieldnames = [
            "model",
            "test_date",
            "x",
            "y",
            "archetype",
            "extremism_count",
            "extremism_rate",
            "status",
            "final_verdict",
        ] + token_fields

        # Handle Schema Migration (if file exists but missing columns)
        if file_exists:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                existing_headers = reader.fieldnames or []

            # Check if we have new columns
            new_columns = [col for col in fieldnames if col not in existing_headers]

            if new_columns:
                print(f"⚠️  CSV-Schema-Update: Füge Spalten hinzu: {new_columns}")
                # Read all data
                with open(filepath, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    data = list(reader)

                # Rewrite file with new header
                with open(filepath, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in data:
                        # writer ignores extra keys in row? No, we need to preserve existing data
                        # but row doesn't have new keys. DictWriter handles missing keys by putting empty string (default)
                        # We just write the row as is, DictWriter fills rest with restval (default "")
                        writer.writerow(row)

                # Continue execution (file is now migrated)

        with open(filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader()

            writer.writerow(row_data)

        print(f"💾 CSV gespeichert: {filepath}")
        return filepath

    @staticmethod
    def print_summary(report: Dict[str, Any]):
        """Prints a CLI summary of the report using TerminalUI."""
        ui = TerminalUI()

        coords = report['coordinates']
        sigma = report.get('sigma', {'x': 0.0, 'y': 0.0})

        # Generate Chart String
        chart_str = None
        try:
            chart_str = PoliticalCompassVisualizer.generate_ascii_chart(
                coords['x'],
                coords['y']
            )
        except Exception:
            pass

        ui.print_final_summary(
            model=report.get('model', 'Unknown'),
            date_str=report.get('test_date', 'Now'),
            coords=(coords['x'], coords['y']),
            sigma=(sigma['x'], sigma['y']),
            archetype=report['archetype']['label'],
            chart=chart_str,
            stats=report.get('statistics', {})
        )
