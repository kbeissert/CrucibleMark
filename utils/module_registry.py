"""
Module Registry Utility
Handles the discovery and loading of active benchmark modules and their configurations.
Applies the "Inversion of Control" principle: The framework asks the modules how they want to be integrated.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple

def load_module_config(module_path: Path) -> Dict[str, Any]:
    """
    Loads the module-specific config.yaml.
    """
    config_file = module_path / "config.yaml"
    if not config_file.exists():
        # Fallback: check if it's inside the module directory but named differently? 
        # No, strict convention: config.yaml
        return {}
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Could not load config for module at {module_path}: {e}")
        return {}

def get_active_modules(benchmark_config: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any], Dict[str, Any]]]:
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
