"""
Zentrales Modul für das Speichern von Benchmark-Ergebnissen.
Stellt sicher, dass alle CSVs im konfigurierten Output-Verzeichnis landen.

Defense-in-Depth (Phase 9): Validierung in _write_to_csv() wirft ValueError
wenn eine Zeile mit korruptem Inhalt (Header-Repeat, narrative Asset-ID,
ungültigem Model) geschrieben werden würde. Verhindert, dass ein zukünftiges
Modul Müll in die CSV schreibt.
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
from utils.model_utils import enforce_card_first
from scripts.maintenance.sanitize_benchmark_csvs import (
    _is_header_repeat,
    _is_narrative_asset_id,
    _is_invalid_model,
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

    def _validate_row_for_write(self, row: dict[str, Any], fieldnames: list[str]) -> None:
        """Validiert eine Zeile VOR dem CSV-Write (Phase 9, Hard-Fail-Guard).

        Wirft ValueError, wenn die Zeile Header-Repeat, narrative Asset-ID oder
        ungültiges Model enthält. Verhindert dass ein zukünftiges Modul Müll
        in die CSV schreibt. Testet die gleichen Heuristiken wie
        ``sanitize_benchmark_csvs._filter_rows``.

        Args:
            row: Eine Ergebnis-Dict-Zeile (kann new oder existing sein).
            fieldnames: Tatsächlicher Header der Zieldatei (für Index-Lookup).

        Raises:
            ValueError: Bei erkannter Korruption. Die Exception enthält Zeilen-Index,
                Asset-ID und Grund; der Caller soll den Fehler loggen und ggf. die
                Zeile überspringen statt die ganze Save-Operation abzubrechen.
        """
        # Header-Repeat: parts[0] == 'asset_id' (gilt nur wenn asset_id-Spalte der
        # erste Eintrag im Header ist). Wir checken pragmatisch auf das Vorhandensein
        # des Header-Werts in der asset_id-Spalte — gleiche Heuristik wie im Sanitizer.
        asset_id_value = str(row.get("asset_id", "") or "")
        if _is_header_repeat([asset_id_value] if asset_id_value else []):
            raise ValueError(
                f"Header-Repeat erkannt: asset_id='{asset_id_value}'. "
                "Zeile wird nicht geschrieben — wahrscheinlich Datenkorruption."
            )

        # Narrative Asset-ID
        if _is_narrative_asset_id(asset_id_value):
            raise ValueError(
                f"Narrative Asset-ID erkannt: '{asset_id_value[:80]}...'. "
                "Zeile wird nicht geschrieben — sieht nach LLM-Rohtext aus."
            )

        # Ungültiges Model
        is_invalid, reason = _is_invalid_model(str(row.get("model", "") or ""))
        if is_invalid:
            raise ValueError(
                f"Ungültiges Model erkannt: reason='{reason}', "
                f"value='{row.get('model', '')}'. "
                "Zeile wird nicht geschrieben — SSoT-Verletzung."
            )

    def save_results(
        self, results: list[dict[str, Any]], result_type: str | None = None
    ) -> Path | None:
        """Speichert Ergebnisse in die entsprechende CSV-Datei."""
        if not results:
            return None

        # Card-First-Vertrag: kanonische model_id garantieren und Card-Pflicht durchsetzen
        # (WARNING + ensure_card() bei fehlender Card; kein Hard-Fail)
        for r in results:
            if "model" in r:
                canonical, _has_card = enforce_card_first(r["model"])
                r["model"] = canonical

        # Automatisches Ermitteln des result_type anhand des ersten Eintrags, falls nicht explizit übergeben
        if not result_type and results:
            provider = results[0].get("provider", "unknown")
            model_name = results[0].get("model", "")

            if provider in ("ollama", "llamacpp", "llamacpp_spark", "llama_cpp", "llamacpp_local"):
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
        """Schreibt die kombinierten Daten in die CSV-Datei (Rewrite mit Deduplizierung).

        Phase 9 (Defense-in-Depth): Jede Zeile wird VOR dem Write validiert.
        Korrupte Zeilen werden geloggt und ÜBERSPRUNGEN (kein Hard-Fail der ganzen
        Save-Operation). Damit bleibt das Benchmark resilient, aber der Müll wird
        nicht in die CSV geschrieben. Im Fehlerfall hilft der Sanitizer beim
        Aufräumen bestehender Altlasten.
        """
        # Validierung: new + existing filtern
        valid_new: list[dict[str, Any]] = []
        skipped = 0
        for r in new_results:
            try:
                self._validate_row_for_write(r, fieldnames)
                valid_new.append(r)
            except ValueError as e:
                logger.warning("[Hard-Fail-Guard] %s", e)
                skipped += 1

        valid_existing: list[dict[str, Any]] = []
        for r in existing_rows:
            try:
                self._validate_row_for_write(r, fieldnames)
                valid_existing.append(r)
            except ValueError as e:
                logger.warning("[Hard-Fail-Guard] %s", e)
                skipped += 1

        if skipped:
            print(
                f"   🛡️  Hard-Fail-Guard: {skipped} korrupte Zeile(n) übersprungen"
            )

        all_rows = valid_existing + valid_new

        # Komplettes Neuschreiben
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(all_rows)

        print(
            f"\n💾 Ergebnisse gespeichert in: {csv_path} (Upsert: {len(valid_new)} neu/updated, {skipped} übersprungen)"
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
