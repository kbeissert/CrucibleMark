"""
Module Loader Utility
Handles dynamic loading of test modules.
"""

import importlib.util
import sys
from pathlib import Path

def load_test_class(module_path: Path, class_name: str) -> type:
    """
    Dynamically loads a test class from a python file.
    
    Args:
        module_path: Path to the python file containing the class
        class_name: Name of the class to load
        
    Returns:
        The loaded class
        
    Raises:
        FileNotFoundError: If the module file does not exist
        AttributeError: If the class is not found in the module
        ImportError: If the module cannot be imported
    """
    if not module_path.exists():
        raise FileNotFoundError(f"Test module file not found: {module_path}")
    
    module_name = module_path.stem
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for module: {module_path}")
        
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    
    if not hasattr(module, class_name):
        raise AttributeError(f"Class '{class_name}' not found in {module_path}")
        
    return getattr(module, class_name)
