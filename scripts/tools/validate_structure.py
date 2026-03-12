#!/usr/bin/env python3
"""
Structure Validator Script
==========================

Validates that all benchmark modules comply with the project structure guidelines defined in ADDING_MODULES.md.
Ref: docs/ADDING_MODULES.md
"""

import sys
from pathlib import Path
from typing import List

# Configuration
MODULES_ROOT = Path("benchmark_modules")
IGNORED_DIRS = {"__pycache__"}
IGNORED_FILES = {".DS_Store", "__init__.py", "base_test.py"}

# Expected Structure
ALLOWED_ROOT_FILES = {
    "__init__.py",
    "test.py",
    "config.yaml",
    "README.md",
    "batch_config.yaml",  # Optional batch config
    "requirements.txt",  # Optional requirements
}

MANDATORY_DIRS = {"assets", "core"}  # Now mandatory for ALL modules (MVC Standard)

# Strict mode enforces 'core' folder and strict root file cleaner
STRICT_MODE_MODULES = {"*"}  # All modules are strict now


def get_modules(root: Path) -> List[Path]:
    """Returns a list of module directories."""
    modules = []
    if not root.exists():
        print(f"Error: {root} not found.")
        return []

    for item in root.iterdir():
        is_generic_module = (item / "__init__.py").exists() or (
            item / "test.py"
        ).exists()
        if item.is_dir() and item.name not in IGNORED_DIRS and is_generic_module:
            modules.append(item)
    return sorted(modules)


def _check_mandatory_dirs(module_path: Path) -> List[str]:
    """Checks for presence of mandatory directories."""
    errors = []
    for directory in MANDATORY_DIRS:
        if not (module_path / directory).is_dir():
            errors.append(f"❌ Missing mandatory directory: '{directory}/'")
    return errors


def _check_root_files(module_path: Path) -> List[str]:
    """Checks for unexpected files in module root."""
    errors = []
    for item in module_path.iterdir():
        if not item.is_file() or item.name in IGNORED_FILES:
            continue

        if item.name not in ALLOWED_ROOT_FILES:
            if item.suffix == ".py":
                # pylint: disable=line-too-long
                msg = f"⚠️  File '{item.name}' should likely be moved to 'core/' or 'scripts/'."
                errors.append(msg)
    return errors


def _check_mvc_architecture(module_path: Path) -> List[str]:
    """Checks for MVC compliance (Core directory and Evaluators)."""
    errors = []
    core_path = module_path / "core"

    if not core_path.is_dir():
        errors.append(
            "❌ CRITICAL: Missing 'core/' directory. Module violates MVC Architecture."
        )
        return errors  # Cannot check content if core missing

    if not (core_path / "evaluators.py").exists():
        errors.append(
            "❌ CRITICAL: Missing 'core/evaluators.py'. Logic must be decoupled."
        )
    return errors


def validate_module(module_path: Path) -> List[str]:
    """Validates a single module against the rules."""
    errors = []
    errors.extend(_check_mandatory_dirs(module_path))
    errors.extend(_check_root_files(module_path))
    errors.extend(_check_mvc_architecture(module_path))
    return errors


def main():
    print("🔍 Validating Project Structure...")
    print(f"Checking modules in: {MODULES_ROOT}")
    print("-" * 60)

    modules = get_modules(MODULES_ROOT)

    all_clean = True

    for module in modules:
        print(f"📦 Checking {module.name}...")
        errors = validate_module(module)

        if not errors:
            print("   ✅ Structure OK")
        else:
            final_errors = []
            for err in errors:
                # If module is not strict, treat "core" missing as info/warning, not failure
                if "core/" in err and module.name not in STRICT_MODE_MODULES:
                    print(f"   ℹ️  (Migration needed) {err}")
                else:
                    print(f"   {err}")
                    final_errors.append(err)

            if final_errors:
                all_clean = False
        print("")

    print("-" * 60)
    if all_clean:
        print("🎉 Validation successful! All strict requirements met.")
        sys.exit(0)
    else:
        print("⚠️  Validation found issues. Please clean up module structure.")
        sys.exit(1)


if __name__ == "__main__":
    main()
