"""
Test Assets Module
==================

Enthält Test-Definitionen (YAML) für verschiedene Benchmark-Kategorien.
"""

from pathlib import Path
from typing import List, Optional
import yaml


def discover_assets(category: Optional[str] = None, asset_paths: Optional[List[str]] = None) -> List[Path]:
    """
    Findet alle Test-Assets
    
    Args:
        category: Optionale Kategorie zum Filtern
        asset_paths: Optionale spezifische Asset-Pfade
        
    Returns:
        Liste von Asset-Pfaden
    """
    if asset_paths:
        return [Path(p) for p in asset_paths if Path(p).exists()]
    
    assets_dir = Path(__file__).parent
    
    if category:
        category_dir = assets_dir / category
        if not category_dir.exists():
            return []
        return list(category_dir.glob('asset_*.yaml'))
    
    # Alle Assets über alle Kategorien
    return list(assets_dir.rglob('asset_*.yaml'))


def load_asset(asset_path: Path) -> dict:
    """
    Lädt ein Asset aus einer YAML-Datei
    
    Args:
        asset_path: Pfad zur Asset-Datei
        
    Returns:
        Asset-Daten als Dictionary
    """
    with open(asset_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_asset_category(asset_path: Path) -> str:
    """
    Extrahiert die Kategorie aus dem Asset-Pfad
    
    Args:
        asset_path: Pfad zur Asset-Datei
        
    Returns:
        Kategorie-Name
    """
    # Annahme: test_modules/test_assets/category/asset_xxx.yaml
    return asset_path.parent.name


__all__ = [
    'discover_assets',
    'load_asset',
    'get_asset_category'
]
