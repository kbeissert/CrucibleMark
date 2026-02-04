#!/usr/bin/env python3
"""
List Modules Script
===================
Lists all enabled modules from the configuration file.
"""

from pathlib import Path
import sys

# Add root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# pylint: disable=wrong-import-position, wrong-import-order
import yaml
from utils.module_registry import get_active_modules # noqa: E402
# pylint: enable=wrong-import-position, wrong-import-order

CONFIG_PATH = Path("benchmark_config.yaml")


def main():
    """Reads config and prints enabled modules (via Registry)."""
    if not CONFIG_PATH.exists():
        print("❌ benchmark_config.yaml not found at root.")
        return

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        print("\n📋 Checking Active Modules:")
        active = get_active_modules(config)
        
        for i, (mod_id, meta, internal) in enumerate(active, 1):
             metadata = internal.get("metadata", {})
             name = metadata.get("name", meta.get("name", mod_id))
             desc = metadata.get("description", meta.get("description", ""))
             
             print(f"  {i}. {mod_id}: {name}")
             if desc:
                 print(f"     -> {desc}")

    except Exception as e:
        print(f"❌ Error reading config: {e}")


if __name__ == "__main__":
    main()
