#!/usr/bin/env python3
"""
Structure Validator Script
==========================

Validates that all benchmark modules comply with the project structure guidelines defined in ADDING_MODULES.md.
Ref: docs/ADDING_MODULES.md
"""

import os
import sys
from pathlib import Path
from typing import List, Set

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
    "requirements.txt"    # Optional requirements
}

MANDATORY_DIRS = {
    "assets",
    "core"  # Now mandatory for ALL modules (MVC Standard)
}

# Strict mode enforces 'core' folder and strict root file cleaner
STRICT_MODE_MODULES = {"*"} # All modules are strict now


def get_modules(root: Path) -> List[Path]:
    """Returns a list of module directories."""
    modules = []
    if not root.exists():
        print(f"Error: {root} not found.")
        return []

    for item in root.iterdir():
        if item.is_dir() and item.name not in IGNORED_DIRS:
            # Check if it looks like a module (has __init__.py or test.py)
            if (item / "__init__.py").exists() or (item / "test.py").exists():
                modules.append(item)
    return sorted(modules)


def validate_module(module_path: Path) -> List[str]:
    """Validates a single module against the rules."""
    errors = []
    
    # 1. Check Mandatory Directories
    for d in MANDATORY_DIRS:
        if not (module_path / d).is_dir():
            errors.append(f"❌ Missing mandatory directory: '{d}/'")

    # 2. Check for Clean Root (Files)
    # We check if unnecessary python files are cluttering the root
    for item in module_path.iterdir():
        if item.is_file():
            if item.name in IGNORED_FILES:
                continue
                
            if item.name not in ALLOWED_ROOT_FILES:
                # If it's a python file not in allowed list, it's likely a violation
                if item.suffix == ".py":
                    errors.append(f"⚠️  File '{item.name}' should likely be moved to 'core/' or 'scripts/'.")
                else:
                    # Non-python files might be acceptable, but warn just in case
                    pass

    # 3. Check for Core directory (The "MVC Standard")
    if not (module_path / "core").is_dir():
        errors.append("❌ CRITICAL: Missing 'core/' directory. Module violates MVC Architecture.")
        
    # 4. Check for Evaluator in Core
    if (module_path / "core").is_dir():
        if not (module_path / "core" / "evaluators.py").exists():
             errors.append("❌ CRITICAL: Missing 'core/evaluators.py'. Logic must be decoupled.")
    
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
