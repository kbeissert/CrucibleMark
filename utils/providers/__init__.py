import pkgutil
import importlib
from pathlib import Path
from .base import BaseProviderClient

# Lade automatisch alle Provider-Module im aktuellen Verzeichnis
package_dir = Path(__file__).resolve().parent
for _, module_name, _ in pkgutil.iter_modules([str(package_dir)]):
    if module_name != "base":
        importlib.import_module(f".{module_name}", package="utils.providers")

__all__ = ["BaseProviderClient"]
