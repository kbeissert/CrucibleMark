#!/usr/bin/env python3
"""Asset Validator für LLM Benchmark Suite."""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple

import yaml

# Constants
MIN_CLI_ARGS = 2
TOTAL_SCORING_WEIGHT = 100

class AssetValidator:
    """Validiert Test-Assets (YAML)."""
    
    def validate_path(self, path: Path) -> Dict[str, Any]:
        """Validiert Datei oder Verzeichnis."""
        results = {'valid': 0, 'invalid': 0, 'details': []}
        
        if path.is_file():
            is_valid, error = self.validate_file(path)
            results['details'].append({'path': str(path), 'status': 'valid' if is_valid else 'invalid', 'error': error})
            if is_valid:
                results['valid'] += 1
            else:
                results['invalid'] += 1
        elif path.is_dir():
            for file_path in path.rglob('*.yaml'):
                is_valid, error = self.validate_file(file_path)
                results['details'].append({'path': str(file_path), 'status': 'valid' if is_valid else 'invalid', 'error': error})
                if is_valid:
                    results['valid'] += 1
                else:
                    results['invalid'] += 1
        
        return results

    def validate_file(self, file_path: Path) -> Tuple[bool, str]:
        """Validiert eine einzelne Asset-Datei."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return False, "Leere Datei"
            
            errors = self._validate_structure(data)
            if errors:
                return False, "; ".join(errors)
                
            return True, None
            
        except Exception as e:
            return False, f"YAML Error: {e}"

    def _validate_structure(self, data: Dict[str, Any]) -> List[str]:
        """Prüft die Struktur des Assets."""
        errors = []
        
        # Check metadata
        if 'metadata' not in data:
            errors.append("Fehlendes Feld: metadata")
        else:
            meta = data['metadata']
            if not isinstance(meta, dict):
                errors.append("metadata muss Dictionary sein")
            else:
                if 'name' not in meta:
                    errors.append("Fehlendes Feld: metadata.name")
                if 'version' not in meta:
                    errors.append("Fehlendes Feld: metadata.version")
        
        # Check prompt(s)
        if 'prompt' not in data and 'prompts' not in data:
            errors.append("Fehlendes Feld: prompt oder prompts")
            
        # Check scoring
        if 'scoring' in data:
            errors.extend(self._validate_scoring(data['scoring']))
        else:
            errors.append("Fehlendes Feld: scoring")
            
        return errors

    @staticmethod
    def _validate_v2_scoring(scoring: Dict[str, Any]) -> List[str]:
        """Validiert Scoring v2.0 Format mit total_points als Integer."""
        errors = []
        total_weight = 0
        
        for category_name, category_data in scoring.items():
            if category_name == 'total_points':
                continue
                
            if not isinstance(category_data, dict):
                errors.append(f"scoring.{category_name} muss Dictionary sein")
                continue
            
            if 'weight' in category_data:
                weight = category_data['weight']
                if not isinstance(weight, (int, float)):
                    errors.append(f"scoring.{category_name}.weight muss Zahl sein")
                else:
                    total_weight += weight
        
        if total_weight != scoring['total_points'] and total_weight > 0:
            errors.append(f"scoring weights ({total_weight}) müssen total_points ({scoring['total_points']}) entsprechen")
        
        return errors
    
    @staticmethod
    def _validate_legacy_scoring(scoring: Dict[str, Any]) -> List[str]:
        """Validiert altes Scoring-Format für Backward Compatibility."""
        errors = []
        total_weight = 0
        
        for category_name, category_data in scoring.items():
            if not isinstance(category_data, dict):
                errors.append(f"scoring.{category_name} muss Dictionary sein")
                continue
            
            if 'weight' not in category_data:
                errors.append(f"scoring.{category_name}.weight fehlt")
            else:
                weight = category_data['weight']
                if not isinstance(weight, (int, float)):
                    errors.append(f"scoring.{category_name}.weight muss Zahl sein")
                else:
                    total_weight += weight
            
            if 'criteria' in category_data:
                if not isinstance(category_data['criteria'], list):
                    errors.append(f"scoring.{category_name}.criteria muss Liste sein")
        
        if total_weight != TOTAL_SCORING_WEIGHT:
            errors.append(f"scoring weights müssen {TOTAL_SCORING_WEIGHT} ergeben, sind {total_weight}")
        
        return errors
    
    @staticmethod
    def _validate_scoring(scoring: Dict[str, Any]) -> List[str]:
        """Validiert Scoring-Sektion (unterstützt beide Formate: alt und v2.0)."""
        if not scoring:
            return []
        
        if not isinstance(scoring, dict):
            return ["scoring muss Dictionary sein"]
        
        # Check if new format (v2.0) with total_points as integer
        if 'total_points' in scoring and isinstance(scoring['total_points'], int):
            return AssetValidator._validate_v2_scoring(scoring)
        
        return AssetValidator._validate_legacy_scoring(scoring)

    def validate_all_modules(self) -> Dict[str, Any]:
        """Validiert alle in benchmark_config.yaml definierten Module."""
        config_path = Path("benchmark_config.yaml")
        if not config_path.exists():
            print("❌ benchmark_config.yaml nicht gefunden.")
            sys.exit(1)
            
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        aggregated_results = {'valid': 0, 'invalid': 0, 'details': []}
        
        print(f"Lese Konfiguration: {config_path}")
        
        for module_key, module_data in config.get('modules', {}).items():
            if not module_data.get('enabled', False):
                continue
                
            module_path = Path(module_data['path']) / 'assets'
            print(f"\nPrüfe Modul: {module_data['name']} ({module_key})")
            
            if not module_path.exists():
                print(f"⚠️  Asset-Ordner fehlt: {module_path}")
                continue
                
            module_results = self.validate_path(module_path)
            aggregated_results['valid'] += module_results['valid']
            aggregated_results['invalid'] += module_results['invalid']
            aggregated_results['details'].extend(module_results['details'])
            
        return aggregated_results

def main():
    """CLI Entry Point."""
    validator = AssetValidator()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        results = validator.validate_all_modules()
    elif len(sys.argv) >= MIN_CLI_ARGS:
        path = Path(sys.argv[1])
        if not path.exists():
            print(f"❌ Pfad nicht gefunden: {path}")
            sys.exit(1)
        print(f"Validiere: {path}\n")
        results = validator.validate_path(path)
    else:
        print("Usage: python validate_assets.py <path> OR --all")
        print("\nPath kann sein:")
        print("  - Einzelne Asset-Datei (.yaml)")
        print("  - Verzeichnis mit Assets")
        sys.exit(1)
    
    print("============================================================")
    print("ASSET VALIDATION REPORT")
    print("============================================================")
    print(f"Total Assets: {results['valid'] + results['invalid']}")
    print(f"✓ Valid: {results['valid']}")
    print(f"✗ Invalid: {results['invalid']}")
    
    if results['invalid'] > 0:
        print("\nFehlerhafte Assets:")
        for detail in results['details']:
            if detail['status'] == 'invalid':
                print(f"✗ {detail['path']}")
                print(f"  - {detail['error']}")
                
    if results['valid'] > 0:
        print("\nValide Assets:")
        for detail in results['details']:
            if detail['status'] == 'valid':
                print(f"✓ {detail['path']}")

    if results['invalid'] > 0:
        sys.exit(1)

if __name__ == '__main__':
    main()
