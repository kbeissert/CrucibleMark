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
        
        # Alle Keys sammeln für Header (um sicherzugehen, dass alle Spalten da sind)
        all_keys = set()
        for result in results:
            all_keys.update(result.keys())
        fieldnames = sorted(list(all_keys))
        
        try:
            mode = 'a' if file_exists else 'w'
            with open(csv_path, mode, newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                # Hinweis: Wenn neue Felder hinzukommen, die im existierenden Header fehlen,
                # könnte DictWriter meckern oder sie ignorieren (extrasaction='raise' ist default).
                # Für Robustheit könnten wir extrasaction='ignore' setzen, aber dann fehlen Daten.
                # Besser: Wir nehmen an, das Schema ist stabil oder erweitert sich nur am Ende.
                # Wenn sich das Schema ändert, ist es oft besser, die CSV neu anzulegen (make clean-csv).
                
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
