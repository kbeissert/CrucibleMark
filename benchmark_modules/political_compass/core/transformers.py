"""
Transformers Module
===================

Provides classes for transforming data between different formats (e.g. JSON to CSV).
"""

import json
from typing import Any


class PoliticalCompassTransformer:
    """Transformiert Benchmark-Reports für verschiedene Ausgabeformate."""

    @staticmethod
    def to_csv_row(report: dict[str, Any]) -> dict[str, Any]:
        """Flacht einen verschachtelten Report in eine CSV-Zeile ab."""

        # 1. Strukturiertes Daten-Objekt erstellen (Data Object Pattern)
        # Dieses Objekt enthält ALLE relevanten Metriken in strukturierter Form.
        # Es dient als SSOT für Leaderboard-Zugriffe via 'metrics.key'.
        data_object = {
            "coordinates": {
                "x": report["coordinates"]["x"],
                "y": report["coordinates"]["y"],
                "formatted": f"({report['coordinates']['x']}, {report['coordinates']['y']})",
            },
            "labels": {
                "x": report["archetype"].get("x_label", "Unknown"),
                "y": report["archetype"].get("y_label", "Unknown"),
                "archetype": report["archetype"]["label"],
            },
            "display": {
                "ideology": f"{report['archetype'].get('x_label', '?')} ({report['coordinates']['x']})",
                "stance": f"{report['archetype'].get('y_label', '?')} ({report['coordinates']['y']})",
            },
            "extremism": {
                "is_extremist": report["extremism"]["count"] > 0,
                "count": report["extremism"]["count"],
                "rate": report["extremism"]["rate"],
            },
        }

        # 2. CSV Flattening
        row_data = {
            "model": report["model"],
            "model_version": report.get(
                "model_version", "unknown"
            ),  # Ensure versioning
            "run_id": report.get("run_id", "Run 1"),
            "test_date": report["test_date"],
            # Legacy Columns (für direkte Lesbarkeit im CSV)
            "x_coordinate": report["coordinates"]["x"],
            "y_coordinate": report["coordinates"]["y"],
            "x_label": report["archetype"].get("x_label", "Unknown"),
            "y_label": report["archetype"].get("y_label", "Unknown"),
            "archetype": report["archetype"]["label"],
            # THE NEW STANDARD: JSON-Serialized Metrics Object
            "metrics_json": json.dumps(data_object, ensure_ascii=False),
        }

        # Add Token Efficiency Data (Legacy Flattening)
        module_stats = report.get("statistics", {}).get("module_stats", {})
        for mod_id in sorted(module_stats.keys()):
            tokens = module_stats[mod_id]["tokens"]
            count = module_stats[mod_id]["count"]
            tpg = round(tokens / count, 2) if count > 0 else 0.0

            row_data[f"module_{mod_id}_tokens"] = tokens
            row_data[f"module_{mod_id}_tpg"] = tpg

        return row_data

    @staticmethod
    def get_csv_headers(row_data: dict[str, Any]) -> list[str]:
        """Ermittelt die CSV-Header basierend auf den Daten."""
        base_headers = [
            "model",
            "model_version",
            "run_id",
            "test_date",
            "x_coordinate",
            "y_coordinate",
            "x_label",
            "y_label",
            "metrics_json",  # <-- New Standard Column
            "archetype",
        ]

        # Add dynamic keys that are not in base_headers
        other_keys = [k for k in row_data.keys() if k not in base_headers]
        return base_headers + sorted(other_keys)
