"""
Zentrales Modul für das Speichern von Benchmark-Ergebnissen.
Stellt sicher, dass alle CSVs im konfigurierten Output-Verzeichnis landen.

Defense-in-Depth (Phase 9): Validierung in _write_to_csv() wirft ValueError
wenn eine Zeile mit korruptem Inhalt (Header-Repeat, narrative Asset-ID,
ungültigem Model) geschrieben werden würde. Verhindert, dass ein zukünftiges
Modul Müll in die CSV schreibt.

Atomare Schreibvorgänge: Full-Rewrites schreiben zuerst in eine .tmp-Datei
und ersetzen die Originaldatei per os.replace() (atomar auf POSIX).
Verhindert Datenverlust bei Kill/Crash während des Schreibens.
"""

import sys
import csv
import logging
import os
import tempfile
from pathlib import Path
from typing import Any
from utils.config_validator import ConfigValidator
from utils.constants import (
    MODEL_TYPE_OPEN_WEIGHTS_CLOUD,
    RESULT_TYPE_LOCAL,
    RESULT_TYPE_CLOUD,
    RESULT_TYPE_COMMERCIAL,
)
from utils.model_utils import enforce_card_first, resolve_model_cfg_for
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

    def _find_model_cfg(self, model_id: str) -> dict[str, Any] | None:
        """Sucht den model_cfg-Eintrag für ``model_id`` in der expandierten Config.

        Wird für ``card_model_id``-Redirects benötigt (z.B. Thinking-Profile):
        der generierte ``{id}-thinking``-Eintrag trägt ``card_model_id``, das
        ``enforce_card_first`` nutzen soll, um die Original-Card wiederzuverwenden
        statt eine Platzhalter-Card anzulegen.

        Delegiert an die SSoT ``resolve_model_cfg_for`` (utils/model_utils.py).
        """
        return resolve_model_cfg_for(model_id, self.config)

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
                # model_cfg aus der expandierten Config nachschlagen, damit
                # card_model_id-Redirects (z.B. Thinking-Profile) funktionieren:
                # enforce_card_first → resolve_canonical_model_id → _find_card
                # nutzt card_model_id für den Card-Lookup statt eine neue
                # Platzhalter-Card anzulegen.
                _model_cfg = self._find_model_cfg(r["model"])
                canonical, _has_card = enforce_card_first(r["model"], model_cfg=_model_cfg)
                r["model"] = canonical

        # Automatisches Ermitteln des result_type anhand des ersten Eintrags, falls nicht explizit übergeben
        if not result_type and results:
            provider = results[0].get("provider", "unknown")
            model_name = results[0].get("model", "")

            if provider in ("ollama", "llamacpp", "llamacpp_spark", "llama_cpp", "llamacpp_local", "vllm_spark"):
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
            logger.error("❌ Fehler beim Erstellen des Verzeichnisses: %s", e)
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
            # Fast-path: Single-result write-through (append-only, O(1)).
            # Used by the write-through pattern in _handle_single_asset().
            # Falls back to full rewrite for multi-result saves or when
            # header needs updating (new columns).
            if (
                len(results) == 1
                and file_exists
                and clean_existing_rows == existing_rows  # no dedup needed
                and self._csv_header_matches(csv_path, fieldnames)
            ):
                self._append_single_row(csv_path, fieldnames, results[0])
                return csv_path

            self._write_to_csv(csv_path, fieldnames, results, clean_existing_rows)

            return csv_path
        except (OSError, csv.Error) as e:
            logger.error("Failed to save results to %s: %s", csv_path, e)
            logger.error("❌ Fehler beim Speichern: %s", e)
            return None

    def _write_to_csv(
        self,
        csv_path: Path,
        fieldnames: list[str],
        new_results: list[dict[str, Any]],
        existing_rows: list[dict[str, Any]],
    ) -> None:
        """Schreibt die kombinierten Daten in die CSV-Datei (Rewrite mit Deduplizierung).

        Defense-in-Depth (Phase 9): Neue Zeilen werden VOR dem Write validiert.
        Bestehende Zeilen (bereits in der CSV) werden NICHT erneut validiert —
        sie waren beim ersten Schreiben valide und eine erneute Validierung
        könnte Zeilen verwerfen, wenn sich die Validierungslogik geändert hat.

        Atomare Schreibvorgänge: Schreibt zuerst in eine .tmp-Datei im selben
        Verzeichnis und ersetzt die Originaldatei per os.replace() (atomar auf
        POSIX). Verhindert Datenverlust bei Kill/Crash während des Schreibens.
        """
        # Validierung: nur neue Zeilen filtern (existing rows waren bereits valide)
        valid_new: list[dict[str, Any]] = []
        skipped_new = 0
        for r in new_results:
            try:
                self._validate_row_for_write(r, fieldnames)
                valid_new.append(r)
            except ValueError as e:
                logger.warning("[Hard-Fail-Guard] %s", e)
                skipped_new += 1

        if skipped_new:
            logger.info(
                f"   🛡️  Hard-Fail-Guard: {skipped_new} neue Zeile(n) übersprungen"
            )

        all_rows = existing_rows + valid_new

        # Atomare Schreibvorgänge: erst .tmp, dann os.replace()
        tmp_fd = None
        tmp_path = None
        try:
            tmp_fd, tmp_path_str = tempfile.mkstemp(
                suffix=".csv.tmp", dir=str(csv_path.parent)
            )
            tmp_path = Path(tmp_path_str)
            os.close(tmp_fd)
            tmp_fd = None  # fd geschlossen, nicht doppelt schließen

            with tmp_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(all_rows)

            # Atomarer Rename (POSIX: os.replace ist atomar wenn src/dst auf gleichem FS)
            os.replace(str(tmp_path), str(csv_path))
            tmp_path = None  # erfolgreich ersetzt, nicht löschen

            logger.info(
                f"\n💾 Ergebnisse gespeichert in: {csv_path} "
                f"(Upsert: {len(valid_new)} neu/updated, {skipped_new} übersprungen)"
            )
        except (OSError, csv.Error) as e:
            logger.error("Failed to write CSV atomically to %s: %s", csv_path, e)
            logger.error("❌ Fehler beim atomaren Schreiben: %s", e)
            # Cleanup: tmp-Datei löschen wenn vorhanden
            if tmp_fd is not None:
                try:
                    os.close(tmp_fd)
                except OSError:
                    pass
            if tmp_path is not None and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            raise  # Caller (save_results) fängt OSError/csv.Error ab

    @staticmethod
    def _csv_header_matches(csv_path: Path, fieldnames: list[str]) -> bool:
        """Check if the existing CSV header exactly matches the expected fieldnames.

        Exact match is required for the fast-path (append) because
        DictWriter writes one value per fieldname — a mismatched header
        would produce rows with wrong column count.
        Falls back to _write_to_csv (atomic full rewrite) when columns
        are added, removed, or reordered.
        """
        try:
            with csv_path.open("r", encoding="utf-8") as f:
                reader = csv.reader(f)
                existing_header = next(reader)
            return existing_header == fieldnames
        except (OSError, csv.Error, StopIteration):
            return False

    def _append_single_row(
        self,
        csv_path: Path,
        fieldnames: list[str],
        row: dict[str, Any],
    ) -> None:
        """Append a single validated row to CSV (O(1), no full rewrite).

        Only used by the write-through path when no dedup or header update
        is needed. Validates the row before writing.
        """
        self._validate_row_for_write(row, fieldnames)
        with csv_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writerow(row)
        logger.debug("Appended single row to %s (asset=%s)", csv_path, row.get("asset_id"))

    def update_leaderboard(self):
        """Triggert das Update des Leaderboards."""
        try:
            # Import hier, um Zirkelbezüge zu vermeiden und Skript-Charakter zu nutzen
            # pylint: disable=import-outside-toplevel
            from scripts.core import generate_leaderboard

            logger.info("🔄 Aktualisiere Leaderboard...")
            sys.stdout.flush()
            # Suppress console output for automation calls
            generate_leaderboard.main(print_table=False)
            sys.stdout.flush()
        except (ImportError, OSError, ValueError) as e:
            logger.error("Failed to update leaderboard: %s", e)
            logger.warning("⚠️  Konnte Leaderboard nicht aktualisieren: %s", e)
