#!/usr/bin/env python3
"""Asset Validator für LLM Benchmark Suite."""

import sys
from pathlib import Path
from typing import Any, Dict, Tuple

# pylint: disable=import-error
import yaml


# Add project root to path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from utils.asset_validator import AssetValidator

# Constants
MIN_CLI_ARGS = 2

class CLIAssetValidator:
    """CLI Wrapper for Asset Validator."""

    def __init__(self):
        self.validator = AssetValidator()

    def validate_path(self, path: Path) -> dict[str, Any]:
        """Validiert Datei oder Verzeichnis."""
        results = {"valid": 0, "invalid": 0, "details": []}

        if path.is_file():
            is_valid, error = self.validator._validate_file_internal(path)
            results["details"].append(
                {
                    "path": str(path),
                    "status": "valid" if is_valid else "invalid",
                    "error": error,
                }
            )
            if is_valid:
                results["valid"] += 1
            else:
                results["invalid"] += 1
        elif path.is_dir():
            # Skip political_compass as it uses a custom schema v2.0
            if "political_compass" in path.parts:
                return results

            for file_path in path.rglob("*.yaml"):
                # Ignore files in ignored directories (starting with . or _)
                if any(part.startswith((".", "_")) for part in file_path.parts):
                    continue

                is_valid, error = self.validator._validate_file_internal(file_path)
                results["details"].append(
                    {
                        "path": str(file_path),
                        "status": "valid" if is_valid else "invalid",
                        "error": error,
                    }
                )
                if is_valid:
                    results["valid"] += 1
                else:
                    results["invalid"] += 1

        return results
                weight = category_data["weight"]
                if not isinstance(weight, (int, float)):
                    errors.append(f"scoring.{category_name}.weight muss Zahl sein")
                else:
                    total_weight += weight

            if "criteria" in category_data:
                if not isinstance(category_data["criteria"], list):
                    errors.append(f"scoring.{category_name}.criteria muss Liste sein")

        if total_weight != TOTAL_SCORING_WEIGHT:
            errors.append(
                f"scoring weights müssen {TOTAL_SCORING_WEIGHT} ergeben, sind {total_weight}"
            )

        return errors


    def validate_all_modules(self) -> dict[str, Any]:
        """Validiert alle in benchmark_config.yaml definierten Module."""
        config_path = Path("benchmark_config.yaml")
        if not config_path.exists():
            print("❌ benchmark_config.yaml nicht gefunden.")
            sys.exit(1)

        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        aggregated_results: Dict[str, Any] = {"valid": 0, "invalid": 0, "details": []}

        print(f"Lese Konfiguration: {config_path}")

        for module_key, module_data in config.get("modules", {}).items():
            if not module_data.get("enabled", False):
                continue

            module_path = Path(module_data["path"]) / "assets"
            print(f"\nPrüfe Modul: {module_data['name']} ({module_key})")

            if not module_path.exists():
                print(f"⚠️  Asset-Ordner fehlt: {module_path}")
                continue

            module_results = self.validate_path(module_path)
            aggregated_results["valid"] += module_results["valid"]
            aggregated_results["invalid"] += module_results["invalid"]
            aggregated_results["details"].extend(module_results["details"])

        return aggregated_results


def _print_report(results: Dict[str, Any]) -> None:
    """Pretty prints the validation report."""
    print("=" * 60)
    print("ASSET VALIDATION REPORT")
    print("=" * 60)
    print(f"Total Assets: {results['valid'] + results['invalid']}")
    print(f"✓ Valid: {results['valid']}")
    print(f"✗ Invalid: {results['invalid']}")

    if results["invalid"] > 0:
        print("\nFehlerhafte Assets:")
        for detail in results["details"]:
            if detail["status"] == "invalid":
                print(f"✗ {detail['path']}")
                print(f"  - {detail['error']}")

    if results["valid"] > 0:
        print("\nValide Assets:")
        for detail in results["details"]:
            if detail["status"] == "valid":
                print(f"✓ {detail['path']}")


def main():
    """CLI Entry Point."""
    validator = AssetValidator()

    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        results = validator.validate_all_modules()
    elif len(sys.argv) >= MIN_CLI_ARGS:
        path = Path(sys.argv[1])
        if not path.exists():
            print(f"❌ Pfad nicht gefunden: {path}")
            sys.exit(1)
        print(f"Validiere: {path}\n")
        results = validator.validate_path(path)
    else:
        print("Usage: python validate_assets.py <path> OR --all")
        print("\nPath kann sein:")
        print("  - Einzelne Asset-Datei (.yaml)")
        print("  - Verzeichnis mit Assets")
        sys.exit(1)

    _print_report(results)

    if results["invalid"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
