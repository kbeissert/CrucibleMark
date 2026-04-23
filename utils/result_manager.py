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
from utils.constants import (
    MODEL_TYPE_OPEN_WEIGHTS_CLOUD,
    RESULT_TYPE_LOCAL,
    RESULT_TYPE_CLOUD,
    RESULT_TYPE_COMMERCIAL,
)

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

        if result_type == RESULT_TYPE_LOCAL:
            key = "local_models_csv"
            default = "benchmark_scores/local_models_benchmark.csv"
        elif result_type == RESULT_TYPE_CLOUD:
            key = "cloud_models_csv"
            default = "benchmark_scores/cloud_models_benchmark.csv"
        elif result_type == RESULT_TYPE_COMMERCIAL:
            key = "commercial_csv"
            default = "benchmark_scores/commercial_models_benchmark.csv"
        else:
            raise ValueError(f"Unknown result type: {result_type}")

        filename = self.config.get("output", {}).get(key, default)
        return Path(filename)

    def _get_updated_fieldnames(self, csv_path: Path, new_keys: set[str]) -> list[str]:
        """Liest existierende Header und fügt neue Spalten hinzu.
        Garantiert immer die Existenz der llm_judge_* Spalten am Ende."""
        import dataclasses
        from schemas.result import BenchmarkResult
        from utils.scoring.llm_judge.judge_parser import JudgeResult

        # 1. Metriken und Judge-Suffixe aus dem Pydantic Benchmark Schema extrahieren
        schema_props = list(BenchmarkResult.model_fields.keys())
        end_metrics = [
            k for k in schema_props
            if "compliance" in k
            or k.startswith("token_limit_")
            or k == "finish_reason"
            or k.startswith("judge_")
        ]

        # 2. Spezifische flache Judge-Felder generieren (gemäß judge_evaluator.py)
        calc_judge_fields = []
        for f in dataclasses.fields(JudgeResult):
            name = f.name
            if name.startswith("judge_"):
                if name not in end_metrics:
                    calc_judge_fields.append(f"llm_{name}")
            else:
                calc_judge_fields.append(f"llm_judge_{name}")

        combined_fields = calc_judge_fields + end_metrics
        if "scoring_method" not in combined_fields:
            combined_fields.append("scoring_method")
        # Refusal-Metadaten (audit-empfohlen: dokumentiert Ablehnungen als Qualitätsmerkmal)
        for _rf in ("refusal_flag", "refusal_type", "refusal_note"):
            if _rf not in combined_fields:
                combined_fields.append(_rf)

        # 3. Deduplizieren und Reihenfolge in judge_fields festhalten
        judge_fields = []
        seen = set()
        for field in combined_fields:
            if field not in seen:
                judge_fields.append(field)
                seen.add(field)

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
        self, results: list[dict[str, Any]], result_type: str | None = None
    ) -> Path | None:
        """Speichert Ergebnisse in die entsprechende CSV-Datei."""
        if not results:
            return None

        # Automatisches Ermitteln des result_type anhand des ersten Eintrags, falls nicht explizit übergeben
        if not result_type and results:
            provider = results[0].get("provider", "unknown")
            model_name = results[0].get("model", "")

            if provider == "ollama":
                if ":cloud" in model_name.lower() or model_name.lower().endswith("-cloud"):
                    result_type = RESULT_TYPE_CLOUD
                else:
                    result_type = RESULT_TYPE_LOCAL
            else:
                # Prüfe in Config, ob es Cloud/Open-Weights ist
                provider_config = self.config.get("providers", {}).get("commercial", {}).get(provider, {})
                model_type = provider_config.get("model_type", "")
                if model_type == MODEL_TYPE_OPEN_WEIGHTS_CLOUD:
                    result_type = RESULT_TYPE_CLOUD
                else:
                    result_type = RESULT_TYPE_COMMERCIAL

        # Fallback
        if not result_type:
            result_type = RESULT_TYPE_COMMERCIAL

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
