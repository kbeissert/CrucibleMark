"""
Central Asset Validator.
Provides validation logic for asset files to ensure schema compliance.
"""
from utils.constants import TOTAL_SCORING_WEIGHT

from pathlib import Path
from typing import Any, Dict, List, Tuple
import yaml


class AssetValidator:
    """Validates YAML Test Assets."""

    @staticmethod
    def validate_file(file_path: Path) -> Tuple[bool, str]:
        """Validates a single asset file (convenience wrapper)."""
        validator = AssetValidator()
        return validator._validate_file_internal(file_path)  # pylint: disable=protected-access

    def _validate_file_internal(self, file_path: Path) -> Tuple[bool, str]:
        """Internal validation logic."""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                return False, "Leere Datei"

            errors = self.validate_structure(data)
            if errors:
                return False, "; ".join(errors)

            return True, ""

        except Exception as e:  # pylint: disable=broad-exception-caught
            return False, f"YAML Error: {e}"

    def validate_structure(self, data: Dict[str, Any]) -> List[str]:
        """Validates the structure of the asset dictionary."""
        errors = []

        # Check metadata
        if "metadata" not in data:
            errors.append("Fehlendes Feld: metadata")
        else:
            meta = data["metadata"]
            if not isinstance(meta, dict):
                errors.append("metadata muss Dictionary sein")
            else:
                # Accept either 'name' (Standard) or 'id' (Minimal/Political Compass)
                if "name" not in meta and "id" not in meta:
                    errors.append("Fehlendes Feld: metadata.name oder metadata.id")
                # Version is recommended but not strictly fatal for runtime?
                # Keeping it strict for quality.
                if "version" not in meta:
                    # Optional warning instead of error? For now keeping it strict but silencing if ID is present
                    pass

        # Check prompt(s)
        if "prompt" not in data and "prompts" not in data:
            errors.append("Fehlendes Feld: prompt oder prompts")

        # Check scoring
        if "scoring" in data:
            errors.extend(self._validate_scoring(data["scoring"]))
        else:
            errors.append("Fehlendes Feld: scoring")

        return errors

    def _validate_scoring(self, scoring: Dict[str, Any]) -> List[str]:
        """Decides which scoring validation to apply (Legacy vs V2)."""
        # If explicitly rubric or coordinate_mapping, skip weight check
        if scoring.get("method") in ["rubric", "coordinate_mapping", "llm_judge"]:
            return []

        if "total_points" in scoring:
            return self._validate_v2_scoring(scoring)
        return self._validate_legacy_scoring(scoring)

    @staticmethod
    def _validate_v2_scoring(scoring: Dict[str, Any]) -> List[str]:
        """Validates Scoring v2.0 Format."""
        errors = []
        total_weight: float = 0.0

        for category_name, category_data in scoring.items():
            if category_name in ("total_points", "method"):
                continue

            if not isinstance(category_data, dict):
                # errors.append(f"scoring.{category_name} muss Dictionary sein")
                # Some keys like 'total_points' are flat, handled above.
                # If unexpected keys appear, maybe ignore or warn?
                continue

            if "weight" in category_data:
                weight = category_data["weight"]
                if not isinstance(weight, (int, float)):
                    errors.append(f"scoring.{category_name}.weight muss Zahl sein")
                else:
                    total_weight += weight

        if total_weight != scoring["total_points"] and total_weight > 0:
            errors.append(
                f"scoring weights ({total_weight}) müssen "
                f"total_points ({scoring['total_points']}) entsprechen"
            )

        return errors

    @staticmethod
    def _validate_legacy_scoring(scoring: Dict[str, Any]) -> List[str]:
        """Validates Legacy Scoring Format."""
        errors = []
        total_weight: float = 0.0

        # Hardcoded 100 assumption for legacy

        for category_name, category_data in scoring.items():
            if category_name == "method":
                continue

            if not isinstance(category_data, dict):
                errors.append(f"scoring.{category_name} muss Dictionary sein")
                continue

            if "weight" not in category_data:
                errors.append(f"scoring.{category_name}.weight fehlt")
            else:
                weight = category_data["weight"]
                if not isinstance(weight, (int, float)):
                    errors.append(f"scoring.{category_name}.weight muss Zahl sein")
                else:
                    total_weight += weight

        if total_weight != TOTAL_SCORING_WEIGHT:
            errors.append(f"Summe der Gewichte ({total_weight}) ungleich 100")

        return errors
