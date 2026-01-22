#!/usr/bin/env python3
"""
List Modules Script
===================
Lists all enabled modules from the configuration file.
"""

from pathlib import Path
# pylint: disable=import-error
import yaml
# pylint: enable=import-error

CONFIG_PATH = Path("benchmark_config.yaml")


def main():
    """Reads config and prints enabled modules."""
    if not CONFIG_PATH.exists():
        print("❌ benchmark_config.yaml not found at root.")
        return

    try:
        with open(CONFIG_PATH, "r", encoding='utf-8') as f:
            config = yaml.safe_load(f)

        modules = config.get("modules", {})
        enabled_modules = [
            (k, v) for k, v in modules.items() if v.get("enabled", True)
        ]

        # Sort by 'order' if available, else key
        enabled_modules.sort(key=lambda x: x[1].get("order", 999))

        for i, (key, data) in enumerate(enabled_modules, 1):
            print(f"  {i}. {key}: {data.get('name', key)}")

    except (OSError, yaml.YAMLError) as e:
        print(f"❌ Error reading config: {e}")


if __name__ == "__main__":
    main()
