"""
Zentrales Modul für das Speichern von Benchmark-Ergebnissen.
Stellt sicher, dass alle CSVs im konfigurierten Output-Verzeichnis landen.
"""

import csv
import logging
from pathlib import Path
from typing import Any
from utils.config_validator import ConfigValidator

logger = logging.getLogger(__name__)


class ResultManager:
    """Verwaltet das Speichern von Benchmark-Ergebnissen und Updates des Leaderboards."""

    def __init__(self, config_validator: ConfigValidator | None = None):
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

    def _get_updated_fieldnames(self, csv_path: Path, new_keys: set[str]) -> list[str]:
        """Liest existierende Header und fügt neue Spalten hinzu."""
        if not csv_path.exists():
            return sorted(new_keys)

        try:
            with csv_path.open('r', encoding='utf-8') as f:
                reader = csv.reader(f)
                try:
                    existing_keys = next(reader)
                except StopIteration:
                    return sorted(new_keys)
        except Exception as e:
            logger.warning("Could not read header from %s: %s", csv_path, e)
            return sorted(new_keys)

        # Neue Keys anhängen (behält Reihenfolge der alten bei)
        existing_set = set(existing_keys)
        added_keys = sorted([k for k in new_keys if k not in existing_set])
        return existing_keys + added_keys

    def save_results(self, results: list[dict[str, Any]], result_type: str) -> Path | None:
        """Speichert Ergebnisse in die entsprechende CSV-Datei."""
        if not results:
            return None

        csv_path = self._get_csv_path(result_type)

        # Sicherstellen, dass das Verzeichnis existiert
        try:
            csv_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error("Could not create directory %s: %s", csv_path.parent, e)
            print(f"❌ Fehler beim Erstellen des Verzeichnisses: {e}")
            return None

        # Collect keys from current results
        current_keys = set().union(*(d.keys() for d in results))

        # Bestimme finale Feldnamen
        fieldnames = self._get_updated_fieldnames(csv_path, current_keys)
        file_exists = csv_path.exists() and csv_path.stat().st_size > 0

        try:
            mode = 'a' if file_exists else 'w'
            with csv_path.open(mode, newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')

                if not file_exists:
                    writer.writeheader()

                writer.writerows(results)

            print(f"\n💾 Ergebnisse gespeichert in: {csv_path}")

            # Leaderboard automatisch aktualisieren
            self.update_leaderboard()

            return csv_path
        except Exception as e:
            logger.error("Failed to save results to %s: %s", csv_path, e)
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
            logger.error("Failed to update leaderboard: %s", e)
            print(f"⚠️  Konnte Leaderboard nicht aktualisieren: {e}")
