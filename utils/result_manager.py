"""
Zentrales Modul für das Speichern von Benchmark-Ergebnissen.
Stellt sicher, dass alle CSVs im konfigurierten Output-Verzeichnis landen.
"""

import sys
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
        self.output_dir = Path(
            self.config.get("output", {}).get("directory", "benchmark_scores")
        )

    def _get_csv_path(self, result_type: str) -> Path:
        """Ermittelt den Pfad zur CSV-Datei basierend auf dem Typ."""
        # result_type: 'local', 'commercial', 'golden'

        if result_type == "local":
            key = "local_models_csv"
            default = "benchmark_scores/local_models_benchmark.csv"
        elif result_type == "commercial":
            key = "commercial_csv"
            default = "benchmark_scores/commercial_models_benchmark.csv"
        else:
            raise ValueError(f"Unknown result type: {result_type}")

        filename = self.config.get("output", {}).get(key, default)
        return Path(filename)

    def _get_updated_fieldnames(self, csv_path: Path, new_keys: set[str]) -> list[str]:
        """Liest existierende Header und fügt neue Spalten hinzu.
        Garantiert immer die Existenz der llm_judge_* Spalten am Ende."""
        judge_fields = [
            "llm_judge_score",
            "llm_judge_reasoning",
            "llm_judge_latency_ms",
            "llm_judge_provider_used",
            "llm_judge_model_used",
            "llm_judge_parse_success",
            "scoring_method",
            "judge_task_compliance",
            "judge_output_quality",
            "judge_standard_adherence",
            "thought_tag_compliance",
            "finish_reason",
            "token_limit_cutoff",
            "token_limit_fallback",
            "token_limit_used",
        ]

        new_keys.update(judge_fields)

        if not csv_path.exists():
            base_keys = sorted([k for k in new_keys if k not in judge_fields])
            return base_keys + judge_fields

        try:
            with csv_path.open("r", encoding="utf-8") as f:
                reader = csv.reader(f)
                try:
                    existing_keys = next(reader)
                except StopIteration:
                    base_keys = sorted([k for k in new_keys if k not in judge_fields])
                    return base_keys + judge_fields
        except (OSError, csv.Error) as e:
            logger.warning("Could not read header from %s: %s", csv_path, e)
            base_keys = sorted([k for k in new_keys if k not in judge_fields])
            return base_keys + judge_fields

        # Neue Keys anhängen (behält Reihenfolge der alten bei)
        existing_set = set(existing_keys)
        normal_added = sorted(
            [k for k in new_keys if k not in existing_set and k not in judge_fields]
        )
        judge_added = [jf for jf in judge_fields if jf not in existing_set]

        return list(existing_keys) + normal_added + judge_added

    def save_results(
        self, results: list[dict[str, Any]], result_type: str
    ) -> Path | None:
        """Speichert Ergebnisse in die entsprechende CSV-Datei."""
        if not results:
            return None

        csv_path = self._get_csv_path(result_type)

        # Sicherstellen, dass das Verzeichnis existiert
        try:
            csv_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error("Could not create directory %s: %s", csv_path.parent, e)
            print(f"❌ Fehler beim Erstellen des Verzeichnisses: {e}")
            return None

        # Collect keys from current results
        current_keys = set().union(*(d.keys() for d in results))

        # Bestimme finale Feldnamen
        fieldnames = self._get_updated_fieldnames(csv_path, current_keys)
        file_exists = csv_path.exists() and csv_path.stat().st_size > 0

        # Wir lesen IMMER die existierenden Zeilen, um Duplikate zu entfernen (Upsert-Pattern)
        existing_rows = []

        if file_exists:
            try:
                with csv_path.open("r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    existing_rows = list(reader)
            except (OSError, csv.Error):
                # Falls Fehler beim Lesen, fangen wir "frisch" an (überschreiben korrupte Datei)
                existing_rows = []

        # Deduplizierung: Entferne Zeilen aus 'existing_rows', wenn (model, asset_id) in 'results' enthalten ist
        # Wir bauen ein Set von (model, asset_id) der neuen Ergebnisse
        new_keys_combo = {(r.get("model", ""), r.get("asset_id", "")) for r in results}

        # Behalte nur Zeilen, die NICHT überschrieben werden
        clean_existing_rows = [
            row
            for row in existing_rows
            if (row.get("model", ""), row.get("asset_id", "")) not in new_keys_combo
        ]

        try:
            self._write_to_csv(csv_path, fieldnames, results, clean_existing_rows)

            return csv_path
        except (OSError, csv.Error) as e:
            logger.error("Failed to save results to %s: %s", csv_path, e)
            print(f"❌ Fehler beim Speichern: {e}")
            return None

    def _write_to_csv(
        self,
        csv_path: Path,
        fieldnames: list[str],
        new_results: list[dict[str, Any]],
        existing_rows: list[dict[str, Any]],
    ) -> None:
        """Schreibt die kombinierten Daten in die CSV-Datei (Rewrite mit Deduplizierung)."""
        # Wir kombinieren alte (gefilterte) Zeilen und neue Zeilen
        all_rows = existing_rows + new_results

        # Komplettes Neuschreiben
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(all_rows)

        print(
            f"\n💾 Ergebnisse gespeichert in: {csv_path} (Upsert: {len(new_results)} neu/updated)"
        )

    def update_leaderboard(self):
        """Triggert das Update des Leaderboards."""
        try:
            # Import hier, um Zirkelbezüge zu vermeiden und Skript-Charakter zu nutzen
            # pylint: disable=import-outside-toplevel
            from scripts.core import generate_leaderboard

            print("🔄 Aktualisiere Leaderboard...")
            sys.stdout.flush()
            # Suppress console output for automation calls
            generate_leaderboard.main(print_table=False)
            sys.stdout.flush()
        except (ImportError, OSError, ValueError) as e:
            logger.error("Failed to update leaderboard: %s", e)
            print(f"⚠️  Konnte Leaderboard nicht aktualisieren: {e}")
