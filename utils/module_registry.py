"""
Module Registry Utility
Handles the discovery and loading of active benchmark modules and their configurations.
Applies the "Inversion of Control" principle:
The framework asks the modules how they want to be integrated.
"""

from pathlib import Path
from typing import Any
import yaml  # pylint: disable=import-error


def load_module_config(module_path: Path) -> dict[str, Any]:
    """
    Loads the module-specific config.yaml.
    """
    config_file = module_path / "config.yaml"
    if not config_file.exists():
        # Fallback: check if it's inside the module directory but named differently?
        # No, strict convention: config.yaml
        return {}

    try:
        with open(config_file, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Warning: Could not load config for module at {module_path}: {e}")
        return {}


def get_active_modules(
    benchmark_config: dict[str, Any],
) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    """
    Returns a list of active modules in the order defined in benchmark_config.yaml.

    Args:
        benchmark_config: The dictionary loaded from benchmark_config.yaml

    Returns:
        List of tuples: (module_id, benchmark_config_entry, module_internal_config)

    The result preserves the order defined in benchmark_config.yaml.
    """
    active_modules = []

    # Iterate over modules defined in the main config (preserving order)
    modules_section = benchmark_config.get("modules", {})

    for module_id, meta in modules_section.items():
        if not meta.get("enabled", True):
            continue

        # Determine path
        module_path_str = meta.get("path")
        if not module_path_str:
            # Fallback default
            module_path_str = f"benchmark_modules/{module_id}"

        module_path = Path(module_path_str)

        # Load internal config
        internal_config = load_module_config(module_path)

        active_modules.append((module_id, meta, internal_config))

    return active_modules


def get_module_test_count(module_path: Path, internal_config: dict[str, Any]) -> int:
    """
    Calculates the expected number of tests for a module.

    Logic Priorities:
    1. Explicit Override: 'integration.leaderboard.display_test_count'
       (Used for aggregated modules like Political Compass where 81 files = 9 axes)

    2. Grouping Strategy: Automatic detection of 'Group ID' in filename
       (e.g. 'political_compass_7.1.001.yaml' -> Group '7.1')
       If a group ID like 'X.Y' is detected, assets are grouped by it.

    3. Dynamic Count: Number of .yaml files in assets/ directory
       (Standard for file-based benchmarks)

    4. Config Fallback: 'execution.assets_count'
       (Legacy or specific manual setting)
    """
    # 1. Explicit Override
    integration = internal_config.get("integration", {})
    lb_config = integration.get("leaderboard", {})
    if "display_test_count" in lb_config:
        try:
            return int(lb_config["display_test_count"])
        except (ValueError, TypeError):
            pass

    assets_dir = module_path / "assets"

    if assets_dir.exists():
        import re

        files = [f for f in assets_dir.glob("*.yaml") if not f.name.startswith(".")]
        if not files:
            # Fallback to Config below if no files found
            pass
        else:
            # 2. Smart Grouping & 3. Dynamic Count
            # Strategy: "Last Hyphen Rule"
            # If filename ends with "-{digits}.yaml", treat everything before as Group ID.
            # Example: "pol_7.1-001.yaml" -> Group "pol_7.1"

            unique_groups = set()
            ungrouped_count = 0

            # Pattern: Capture anything greedy (.+) before a hyphen and digits at the end
            group_regex = re.compile(r"(.+)-\d+\.yaml$")

            for f in files:
                match = group_regex.search(f.name)
                if match:
                    # Found a grouped asset
                    unique_groups.add(match.group(1))
                else:
                    # Standard asset (no variant ID found)
                    ungrouped_count += 1

            # Total = Number of unique groups + Number of standalone assets
            total_count = len(unique_groups) + ungrouped_count
            return total_count

    # 4. Configuration Fallback

    # 3. Configuration Fallback
    execution = internal_config.get("execution", {})
    # Check execution.assets_count or root-level assets_count (legacy)
    count = execution.get("assets_count")
    if count is None:
        count = internal_config.get("assets_count", 0)

    return int(count)


def load_active_benchmarks(config: dict[str, Any]) -> dict[str, Any]:
    """Load active benchmark modules in runner-compatible format.

    Reads benchmark_config.yaml (via passed config dict) and converts enabled modules
    into the format expected by BenchmarkRunner.

    Args:
        config: Loaded benchmark_config.yaml data

    Returns:
        Dict mapping module_id to benchmark info:
        {
            'code_quality': {
                'name': 'Code Quality',
                'description': '...',
                'path': 'benchmark_modules/code_quality/assets',
                'module_path': 'benchmark_modules/code_quality',
                'test_class': 'CodeQualityTest',
                'execution_mode': 'standard',
                'min_runs': 1,
                'benchmarks': [...]
            },
            ...
        }
    """
    benchmark_categories = {}
    active_modules = get_active_modules(config)

    for key, mod, internal in active_modules:
        metadata = internal.get("metadata", {})
        execution = internal.get("execution", {})

        benchmark_categories[key] = {
            "id": key,
            "name": metadata.get("name", mod.get("name", key)),
            "description": metadata.get("description", mod.get("description", "")),
            "path": f"{mod['path']}/assets",
            "module_path": mod["path"],
            "test_class": execution.get(
                "test_class", mod.get("test_class", "CodeQualityTest")
            ),
            "execution_mode": execution.get(
                "execution_mode", mod.get("execution_mode", "standard")
            ),
            "min_runs": execution.get("min_runs", mod.get("min_runs", 1)),
            "benchmarks": internal.get("benchmarks", []),
            "scoring": internal.get("scoring", {}),
        }

    return benchmark_categories
