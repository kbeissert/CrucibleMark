#!/usr/bin/env python3
"""Asset Validator für LLM Benchmark Suite."""

import sys
from pathlib import Path
from typing import Any

# pylint: disable=import-error
import yaml

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from utils.asset_validator import AssetValidator  # noqa: E402


class CLIAssetValidator:
    """CLI Wrapper for Asset Validator."""

    def __init__(self):
        self.validator = AssetValidator()

    def validate_path(self, path: Path) -> dict[str, Any]:
        """Validiert Datei oder Verzeichnis."""
        results: dict[str, Any] = {"valid": 0, "invalid": 0, "details": []}

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
            for file_path in path.rglob("*.yaml"):
                # Ignore files in ignored directories (starting with . or _) or named "backup"
                if any(
                    part.startswith((".", "_")) or "backup" in part.lower()
                    for part in file_path.parts
                ):
                    continue

                # Ignore config and template files
                if file_path.name in [
                    "config.yaml",
                    "MODULE_SCHEMA_TEMPLATE.yaml",
                    "local_override.yaml",
                ]:
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

    def validate_all_modules(self) -> dict[str, Any]:
        """Validiert alle in benchmark_config.yaml definierten Module."""
        config_path = Path("benchmark_config.yaml")
        if not config_path.exists():
            print("❌ benchmark_config.yaml nicht gefunden.")
            sys.exit(1)

        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        aggregated_results: dict[str, Any] = {"valid": 0, "invalid": 0, "details": []}

        print(f"Lese Konfiguration: {config_path}")

        for module_key, module_data in config.get("modules", {}).items():
            if not module_data.get("enabled", False):
                continue

            module_path = Path(module_data["path"]) / "assets"
            print(
                f"\nPrüfe Modul: {module_data.get('name', module_key)} ({module_key})"
            )

            if not module_path.exists():
                print(f"⚠️  Asset-Ordner fehlt: {module_path}")
                continue

            module_results = self.validate_path(module_path)
            aggregated_results["valid"] += module_results["valid"]
            aggregated_results["invalid"] += module_results["invalid"]
            aggregated_results["details"].extend(module_results["details"])

        return aggregated_results


def _print_report(results: dict[str, Any]) -> None:
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
    import argparse  # pylint: disable=import-outside-toplevel
    parser = argparse.ArgumentParser(
        description="Asset Validator: prueft YAML-Asset-Dateien (Schema, Pflichtfelder, Refs).",
    )
    parser.add_argument(
        "path", nargs="?",
        help="Pfad zu einer Asset-Datei (.yaml) oder Verzeichnis mit Assets. "
             "Kann weggelassen werden, wenn --all genutzt wird.",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Alle Module aus der Config validieren (Default-Modus fuer 'make validate').",
    )
    args = parser.parse_args()

    if not args.path and not args.all:
        parser.error(
            "Entweder PATH oder --all angeben. "
            "Beispiel: validate_assets.py benchmark_modules/tooluse/assets"
        )

    validator = CLIAssetValidator()

    if args.all:
        results = validator.validate_all_modules()
    else:
        path = Path(args.path)
        if not path.exists():
            print(f"❌ Pfad nicht gefunden: {path}")
            sys.exit(1)
        print(f"Validiere: {path}\n")
        results = validator.validate_path(path)

    _print_report(results)

    if results["invalid"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
