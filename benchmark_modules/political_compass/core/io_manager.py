"""
I/O Manager Module
==================

Handles file I/O operations for reports and results.
"""

import contextlib
import csv
import io
import json
import logging
import re
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from utils.benchmark_ui import TerminalUI
from utils.io_helpers import atomic_write_text
from utils.model_id_base import strip_date_suffix

from .constants import DATE_FORMAT, DEFAULT_ENCODING, TEMP_DIR
from .evaluators import classify_behavior_archetype
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
        state_to_save = dict(state)
        state_to_save["timestamp"] = time.time()
        try:
            with filepath.open("w", encoding=DEFAULT_ENCODING) as f:
                json.dump(state_to_save, f, indent=2, ensure_ascii=False)
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


class PoliticalCompassResultManager:
    """
    Handles file I/O and reporting for Political Compass results.
    Separates data persistence and presentation from business logic.
    """

    @staticmethod
    def generate_filename(model: str, prefix: str = "results") -> str:
        """Generates a consistent filename with timestamp."""
        timestamp = datetime.now(UTC).strftime(DATE_FORMAT)
        safe_model = re.sub(r"[^a-zA-Z0-9]", "_", model)
        return f"{prefix}_{safe_model}_{timestamp}"

    @staticmethod
    def save_json(
        report: dict[str, Any], directory: Path, filename: str | None = None
    ) -> Path:
        """Saves the full report as JSON."""
        if not filename:
            filename = (
                PoliticalCompassResultManager.generate_filename(report.get("model", "unknown"))
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
            PoliticalCompassResultManager._ensure_schema_matches(filepath, fieldnames)

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

        if "coordinates" not in report:  # Defensive check for generic batch modules
            logger.info("Batch Module Execution Completed.")
            if "score" in report:
                print(
                    f"Score: {report['score']} | Status: {report.get('status', 'success')}"
                )
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
    def save_leaderboard_csv(report: dict[str, Any], output_dir: Path):
        """
        Speichert die Makro-Resultate in der political_compass_leaderboard.csv.
        Eine Zeile pro Modell (Upsert). Vanilla vs. Forced + Shift-Delta.
        """
        csv_path = output_dir / "political_compass_leaderboard.csv"
        output_dir.mkdir(parents=True, exist_ok=True)

        fieldnames = [
            "timestamp", "model", "model_category", "provider_type", "model_version",
            "vanilla_x", "vanilla_y", "vanilla_label",
            "forced_x", "forced_y", "forced_label",
            "shift_x", "shift_y", "shift_distance", "polarity_flip_rate",
            "behavior_archetype", "is_retest",
        ]

        # Normalisierung: OpenRouter-Datumssuffixe abschneiden — verhindert Ghost-Duplikate.
        # SSoT: utils.model_id_base.strip_date_suffix (-/YYYYMMDD und -/MMDD).
        raw_model = report.get("model", "unknown")
        model = strip_date_suffix(raw_model)

        raw_provider = report.get("provider", "unknown")

        try:
            from utils.model_utils import get_model_category as _gmc
            model_category = _gmc(
                model,
                source_file="commercial" if raw_provider != "ollama" else "local",
                provider=raw_provider,
            )
        except Exception:
            model_category = "Open Weights" if raw_provider == "ollama" else "Proprietär"

        runs = report.get("runs", {})
        v_coords = runs.get("vanilla", {}).get("coordinates", {})
        f_coords = runs.get("forced", {}).get("coordinates", {})
        v_archetype = runs.get("vanilla", {}).get("archetype", {})
        f_archetype = runs.get("forced", {}).get("archetype", {})
        shift = report.get("shift", {})

        # Degenerate-Guard: Modell hat alle politischen Fragen verweigert (Zensur).
        # Eintrag wird trotzdem geschrieben, damit die Skip-Logik keinen Re-Run auslöst.
        if all(
            val == 0.0
            for val in (v_coords.get("x", 0.0), v_coords.get("y", 0.0),
                        f_coords.get("x", 0.0), f_coords.get("y", 0.0))
        ):
            logger.warning(
                "⚠️  Degeneriertes PC-Ergebnis für '%s': Alle Koordinaten 0.0 — "
                "Modell hat wahrscheinlich alle politischen Fragen verweigert.",
                model,
            )

        row = {
            "timestamp": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
            "model": model,
            "model_category": model_category,
            "provider_type": raw_provider,
            "model_version": report.get("model_version", ""),
            "vanilla_x": round(float(v_coords.get("x", 0.0)), 2),
            "vanilla_y": round(float(v_coords.get("y", 0.0)), 2),
            "vanilla_label": (
                f"{v_archetype.get('x_label', '')} / {v_archetype.get('y_label', '')}".strip(" /")
            ),
            "forced_x": round(float(f_coords.get("x", 0.0)), 2),
            "forced_y": round(float(f_coords.get("y", 0.0)), 2),
            "forced_label": (
                f"{f_archetype.get('x_label', '')} / {f_archetype.get('y_label', '')}".strip(" /")
            ),
            "shift_x": round(float(shift.get("x", 0.0)), 2),
            "shift_y": round(float(shift.get("y", 0.0)), 2),
            "shift_distance": round(float(shift.get("distance", 0.0)), 2),
            "polarity_flip_rate": round(float(shift.get("polarity_flip_rate", 0.0)), 2),
            "behavior_archetype": classify_behavior_archetype(
                shift_distance=float(shift.get("distance", 0.0)),
                polarity_flip_rate=float(shift.get("polarity_flip_rate", 0.0)),
                vanilla_x=float(v_coords.get("x", 0.0)),
                vanilla_y=float(v_coords.get("y", 0.0)),
                forced_x=float(f_coords.get("x", 0.0)),
                forced_y=float(f_coords.get("y", 0.0)),
            ),
            "is_retest": str(report.get("is_retest", "False")).lower(),
        }

        # Upsert: bestehenden Eintrag für dieses Modell ersetzen
        existing_rows: list[dict] = []
        if csv_path.exists():
            try:
                with open(csv_path, encoding="utf-8") as f:
                    existing_rows = [r for r in csv.DictReader(f) if r.get("model") != model]
            except Exception as e:
                logger.warning("Fehler beim Lesen der PC-Leaderboard-CSV, überschreibe: %s", e)

        existing_rows.append(row)

        # Atomar schreiben (Regel data-pipeline.md v4.10.4: NIEMALS 'w'/truncate
        # zum Überschreiben). Die PC-Leaderboard-CSV ist Upsert-File und
        # Primärquelle des Web-Exports — bei Crash mid-write bleibt die
        # alte Datei intakt.
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(existing_rows)
        atomic_write_text(csv_path, buffer.getvalue())

        logger.info("💾 Leaderboard CSV gespeichert: %s", csv_path)
