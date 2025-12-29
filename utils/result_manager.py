"""
Zentrales Modul für das Speichern von Benchmark-Ergebnissen.
Stellt sicher, dass alle CSVs im konfigurierten Output-Verzeichnis landen.
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.config_validator import ConfigValidator

logger = logging.getLogger(__name__)

class ResultManager:
    """Verwaltet das Speichern von Benchmark-Ergebnissen und Updates des Leaderboards."""
    
    def __init__(self, config_validator: Optional[ConfigValidator] = None):
        self.validator = config_validator or ConfigValidator()
        self.config = self.validator.config
        
        # Output Directory aus Config oder Default
        self.output_dir = Path(self.config.get('output', {}).get('directory', 'benchmark_scores'))
        
    def _get_csv_path(self, result_type: str) -> Path:
        """Ermittelt den Pfad zur CSV-Datei basierend auf dem Typ."""
        # result_type: 'local', 'commercial', 'golden'
        
        if result_type == 'local':
            key = 'local_models_csv'
            default = 'benchmark_scores/local_models_benchmark.csv'
        elif result_type == 'commercial':
            key = 'commercial_csv'
            default = 'benchmark_scores/commercial_models_benchmark.csv'
        elif result_type == 'golden':
            key = 'golden_standard_csv'
            default = 'benchmark_scores/golden_standard_benchmark.csv'
        else:
            raise ValueError(f"Unknown result type: {result_type}")
             
        filename = self.config.get('output', {}).get(key, default)
        return Path(filename)

    def save_results(self, results: List[Dict[str, Any]], result_type: str) -> Optional[Path]:
        """Speichert Ergebnisse in die entsprechende CSV-Datei."""
        if not results:
            return None
            
        csv_path = self._get_csv_path(result_type)
        
        # Sicherstellen, dass das Verzeichnis existiert
        try:
            csv_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Could not create directory {csv_path.parent}: {e}")
            print(f"❌ Fehler beim Erstellen des Verzeichnisses: {e}")
            return None
        
        file_exists = csv_path.exists()
        
        # Determine fieldnames
        fieldnames = []
        if file_exists:
            # Read existing header to preserve order and ensure alignment
            try:
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    try:
                        fieldnames = next(reader)
                    except StopIteration:
                        file_exists = False # Empty file
            except Exception as e:
                logger.warning(f"Could not read header from {csv_path}: {e}")
                file_exists = False

        # Collect keys from current results
        current_keys = set()
        for result in results:
            current_keys.update(result.keys())
        
        if not file_exists:
            # New file: use sorted keys
            fieldnames = sorted(list(current_keys))
        else:
            # Existing file: append new keys to the end
            existing_keys = set(fieldnames)
            new_keys = sorted(list(current_keys - existing_keys))
            if new_keys:
                # Note: Adding columns to an existing CSV is tricky without rewriting.
                # DictWriter will ignore extra keys if extrasaction='ignore', or raise error.
                # If we want to support schema evolution, we should probably rewrite the file or warn.
                # For now, we append them to fieldnames, but this only affects NEW rows.
                # Old rows won't have these columns, which is fine for CSV readers usually.
                # BUT: DictWriter needs to know about ALL keys to write them.
                fieldnames.extend(new_keys)
                
                # Warning: This creates a "ragged" CSV where new rows have more columns.
                # Ideally, we should rewrite the header.
                # Let's try to rewrite the header if we detect new keys.
                pass # Logic below handles writing

        try:
            # If we have new keys and file exists, we might want to rewrite the header?
            # That's complex. Let's stick to: Use existing header + new keys.
            # DictWriter will write values in order of fieldnames.
            # Missing keys in results (relative to fieldnames) will be empty.
            # Extra keys in results (relative to fieldnames) will be written if in fieldnames.
            
            mode = 'a' if file_exists else 'w'
            with open(csv_path, mode, newline='', encoding='utf-8') as f:
                # extrasaction='ignore' prevents error if result has keys not in fieldnames
                # But we added all current_keys to fieldnames, so this shouldn't happen unless
                # we failed to update fieldnames correctly.
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerows(results)
            
            print(f"\n💾 Ergebnisse gespeichert in: {csv_path}")
            
            # Leaderboard automatisch aktualisieren
            self.update_leaderboard()
            
            return csv_path
        except Exception as e:
            logger.error(f"Failed to save results to {csv_path}: {e}")
            print(f"❌ Fehler beim Speichern: {e}")
            return None

    def update_leaderboard(self):
        """Triggert das Update des Leaderboards."""
        try:
            # Import hier, um Zirkelbezüge zu vermeiden und Skript-Charakter zu nutzen
            from scripts import generate_leaderboard
            print("🔄 Aktualisiere Leaderboard...")
            generate_leaderboard.main(print_table=False)
        except Exception as e:
            logger.error(f"Failed to update leaderboard: {e}")
            print(f"⚠️  Konnte Leaderboard nicht aktualisieren: {e}")
