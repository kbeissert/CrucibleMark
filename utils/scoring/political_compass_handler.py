"""
Handler for Political Compass outputs to enforce Separation of Concerns.
Extracts Political Compass result generation and persistence from core runners.
"""

import csv
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any

from utils.module_registry import load_module_config
from utils.benchmark_utils import (
    format_pc_run_data,
    format_political_compass_data,
    prepare_pc_csv_row,
)

# pylint: disable=invalid-name,broad-exception-caught

logger = logging.getLogger(__name__)

# Optional bindings to Political Compass modules
try:
    from benchmark_modules.political_compass.core.io_manager import (
        PoliticalCompassResultManager as PCResultManager,
    )
    from benchmark_modules.political_compass.core.audit_logger import (
        AuditLogWriter as PCAuditLogWriter,
    )
except ImportError:
    PCResultManager = None  # type: ignore
    PCAuditLogWriter = None  # type: ignore


class PoliticalCompassHandler:
    """Delegates reporting and file-writing for the Political Compass module."""

    @staticmethod
    def is_political_compass(benchmark_info: dict[str, Any]) -> bool:
        """Determines if the benchmark is the Political Compass module."""
        module_id = benchmark_info.get("id", "")
        return (
            module_id in ["political_compass", "political_compass_v3", "political_compass_v4"]
            or benchmark_info.get("name", "") == "Political Compass"
        )

    @staticmethod
    def build_replacement_calibration(note_suffix: str = "") -> dict[str, Any]:
        """Baut das pc_calibration-Transparenz-Flag für Coverage-Regel-Ersatzläufe.

        SSoT für Handler und Verifikationsskript — verhindert Struktur-/Text-
        Drift zwischen den beiden Injektionsstellen.
        """
        notes = (
            "Instruct-Ersatzlauf laut Coverage-Regel (Konzept-Doc Abschn. 11): "
            "Thinking-Run wegen Truncation-Verlusten abgebrochen, Ergebnis "
            "unter der Original-Modell-ID attribuiert."
        )
        if note_suffix:
            notes = f"{notes} {note_suffix}"
        return {
            "classification": "instruct_profile",
            "budget": None,
            "tested": None,
            "pc_profile_forced_instruct": True,
            "notes": notes,
        }

    @staticmethod
    def _load_result_attribution_mapping() -> dict[str, str]:
        """Lädt das Attribution-Mapping aus der PC-Modul-Config (SSoT)."""
        try:
            # Root-Anker statt CWD-relativ: bei Aufruf aus anderem Verzeichnis
            # würde ein relativer Pfad stille {} liefern (Attribution aus).
            _module_dir = (
                Path(__file__).resolve().parents[2]
                / "benchmark_modules" / "political_compass"
            )
            module_config = load_module_config(_module_dir)
            mapping = (module_config.get("config") or {}).get("result_attribution") or {}
            return {str(k): str(v) for k, v in mapping.items()}
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.debug("Result-Attribution konnte nicht geladen werden: %s", e)
            return {}

    @classmethod
    def _resolve_result_attribution(cls, model: str) -> str | None:
        """Löst die Ergebnis-Attribution für Coverage-Regel-Ersatzläufe auf.

        Mapping in der PC-Modul-Config (``config.result_attribution``):
        Instruct-Profil-ID → Original-Modell-ID. Ein Treffer bedeutet: Der
        Lauf ist ein Instruct-Ersatzlauf, dessen Ergebnis unter der
        Original-ID persistiert wird (ein Leaderboard-Eintrag pro Modell).
        """
        attributed = cls._load_result_attribution_mapping().get(model)
        return attributed or None

    @classmethod
    def _is_attributed_target(cls, model: str) -> bool:
        """True, wenn ``model`` ein Attributions-Ziel (Original-ID) ist.

        Ergebnisse unter dieser ID stammen aus einem Instruct-Ersatzlauf —
        die Shift-Verifikation darf sie nicht mit einem Thinking-Triple-Run
        überschreiben (Coverage-Regel, Konzept-Doc Abschn. 11).
        """
        return model in set(cls._load_result_attribution_mapping().values())

    @classmethod
    def handle_results(
        cls,
        model: str,
        report: dict[str, Any],
        model_version: str,
        test_instance: Any,
        audit_mode: bool = False,
        provider_type: str = "ollama",
    ) -> None:
        """
        End-to-end processing of Political Compass outputs.
        Replaces the verbose procedural reporting in both local and commercial runners.
        """
        if PCResultManager is None:
            logger.warning(
                "PoliticalCompassResultManager could not be imported. Skipping PC outputs."
            )
            return

        # Coverage-Regel-Ersatzlauf (Konzept-Doc Abschn. 11): Ergebnisse eines
        # Instruct-Ersatzlaufs werden unter der ORIGINAL-Modell-ID attribuiert
        # (ein Leaderboard-Eintrag pro Modell). Die methodische Abweichung bleibt
        # transparent: pc_calibration in metrics_json + ⚙️-Annotation im Report.
        attribution = cls._resolve_result_attribution(model)
        if attribution:
            stats = report.setdefault("statistics", {})
            if not stats.get("pc_calibration"):
                stats["pc_calibration"] = cls.build_replacement_calibration()
            logger.info(
                "[PC] Ergebnis von Ersatzlauf '%s' wird unter Original-ID '%s' attribuiert.",
                model, attribution,
            )
            report["model"] = attribution
            model = attribution
            # Versions-Label konsistent halten (AGENTS.md, Session 87):
            # model_version aus der Card der Original-ID auflösen — die
            # Ersatzlauf-Profil-ID hat keine eigene Card und würde als
            # 'k.A.'-Widerspruch auf der Modellseite sichtbar.
            try:
                from utils.model_version import get_model_version
                model_version = get_model_version(attribution, provider_type)
                report["model_version"] = model_version
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.debug("model_version-Re-Resolution fehlgeschlagen: %s", e)

        try:
            PCResultManager.print_summary(report)
            output_dir = Path("outputs/runs")
            output_dir.mkdir(exist_ok=True, parents=True)
            PCResultManager.save_json(report, output_dir)
        except Exception as e:
            logger.error("Political compass manager print/JSON failed: %s", e)

        try:
            if provider_type == "ollama":
                cls._update_local_pc_csv(model, report, model_version)
            else:
                cls._update_commercial_pc_csv(model, report, model_version)
        except Exception as e:
            logger.error("Political compass CSV update failed: %s", e)

        try:
            cls._generate_derivatives(
                model, report, test_instance, audit_mode, provider_type
            )
        except Exception as e:
            logger.error("Political compass derivatives failed: %s", e)

        # Trigger automatic verification on high shifts
        try:
            is_retest = report.get("is_retest", getattr(test_instance, "verification_mode", False))
            shift_dist = float(report.get("shift", {}).get("distance", 0.0))
            config = getattr(test_instance, "config", {})
            threshold = float(config.get("anomaly_shift_threshold", 1.0))
            # Coverage-Regel (Konzept-Doc Abschn. 11): Attribuierte Ersatz-
            # Läufe nicht verifizieren — der Triple-Run würde das Thinking-
            # Profil fahren und das Ersatzlauf-Ergebnis überschreiben.
            if shift_dist > threshold and not is_retest and not attribution:
                import subprocess
                import sys
                print(f"\n🚨 [SAFETY ALERT] Automatischer Sicherheits-Trigger: Shift ({shift_dist:.2f} > {threshold}) bei '{model}' erkannt!")
                print("🛡️  Starte Anomaly Verification Protocol (Triple-Run Verification)...\n")
                subprocess.run(
                    [sys.executable, "scripts/core/verify_compass_anomalies.py", "--model", model, "--threshold", str(threshold)],
                    check=False
                )
        except Exception as e:
            logger.error("Political compass anomaly trigger failed: %s", e)

    @staticmethod
    def _update_local_pc_csv(
        model: str, report: dict[str, Any], model_version: str
    ) -> None:
        """Upsert logic for local runner (replaces previous entries for this model)."""
        pc_csv = Path("benchmark_scores/political_compass_results.csv")
        pc_csv.parent.mkdir(exist_ok=True, parents=True)

        fieldnames = [
            "model",
            "model_version",
            "run_id",
            "x_coordinate",
            "y_coordinate",
            "x_label",
            "y_label",
            "metrics_json",
            "timestamp",
        ]
        timestamp_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")

        rows_to_write = []

        if "individual_runs" in report:
            for i, run in enumerate(report["individual_runs"], 1):
                run_formatted = format_pc_run_data(run, include_extremism=False)
                rows_to_write.append(
                    {
                        "model": model,
                        "model_version": model_version,
                        "run_id": f"RUN_{run.get('id', i)}",
                        "x_coordinate": run.get("x", 0.0),
                        "y_coordinate": run.get("y", 0.0),
                        "x_label": run.get("x_label", ""),
                        "y_label": run.get("y_label", ""),
                        "metrics_json": json.dumps(
                            run_formatted, ensure_ascii=False
                        ),
                        "timestamp": timestamp_str,
                    }
                )

        avg_formatted = format_pc_run_data(
            {
                "x": report.get("coordinates", {}).get("x", 0.0),
                "y": report.get("coordinates", {}).get("y", 0.0),
                "x_label": report.get("archetype", {}).get("x_label", ""),
                "y_label": report.get("archetype", {}).get("y_label", ""),
                "extremism": report.get("extremism", {}),
                "sigma": report.get("sigma", {}),
                "module_stats": report.get("statistics", {}).get("module_stats", {}),
            },
            include_extremism=True,
        )
        _calibration = report.get("statistics", {}).get("pc_calibration")
        if _calibration:
            avg_formatted["pc_calibration"] = _calibration

        rows_to_write.append(
            {
                "model": model,
                "model_version": model_version,
                "run_id": "AVG",
                "x_coordinate": report.get("coordinates", {}).get("x", 0.0),
                "y_coordinate": report.get("coordinates", {}).get("y", 0.0),
                "x_label": report.get("archetype", {}).get("x_label", ""),
                "y_label": report.get("archetype", {}).get("y_label", ""),
                "metrics_json": json.dumps(avg_formatted, ensure_ascii=False),
                "timestamp": timestamp_str,
            }
        )

        # Upsert: remove existing rows for this model, then append new rows
        existing_rows = []
        if pc_csv.exists() and pc_csv.stat().st_size > 0:
            with open(pc_csv, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                existing_rows = [r for r in reader if r.get("model") != model]
                if reader.fieldnames:
                    for col in reader.fieldnames:
                        if col not in fieldnames:
                            fieldnames.append(col)

        existing_rows.extend(rows_to_write)

        with open(pc_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(existing_rows)

    @staticmethod
    def _update_commercial_pc_csv(
        model: str, report: dict[str, Any], model_version: str
    ) -> None:
        """Original read-replace-write logic for commercial runner."""
        pc_csv = Path("benchmark_scores/political_compass_results.csv")
        pc_csv.parent.mkdir(exist_ok=True, parents=True)

        fieldnames = [
            "model",
            "model_version",
            "run_id",
            "x_coordinate",
            "y_coordinate",
            "x_label",
            "y_label",
            "metrics_json",
            "timestamp",
        ]
        pc_rows = []
        if pc_csv.exists():
            with open(pc_csv, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                pc_rows = list(reader)
                if reader.fieldnames:
                    for col in reader.fieldnames:
                        if col not in fieldnames:
                            fieldnames.append(col)

        pc_rows = [r for r in pc_rows if r.get("model") != model]

        data_object = format_political_compass_data(report)
        data_object["module_stats"] = report.get("statistics", {}).get("module_stats", {})
        _calibration = report.get("statistics", {}).get("pc_calibration")
        if _calibration:
            data_object["pc_calibration"] = _calibration
        new_row = prepare_pc_csv_row(
            model, report, data_object, model_version=model_version
        )
        new_row["timestamp"] = datetime.now().isoformat()
        pc_rows.append(new_row)

        with open(pc_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(pc_rows)

    @staticmethod
    def _generate_derivatives(
        model: str,
        report: dict[str, Any],
        test_instance: Any,
        audit_mode: bool,
        provider_type: str,
    ) -> None:
        """Generates audit logs and leaderboard CSV if applicable."""
        runs = report.get("runs", {})
        vanilla_run = runs.get("vanilla", {})
        forced_run = runs.get("forced", {})
        shift = report.get("shift", {})

        if audit_mode and PCAuditLogWriter is not None:
            try:
                vanilla_for_audit = {
                    "score_x": vanilla_run.get("coordinates", {}).get("x", 0.0),
                    "score_y": vanilla_run.get("coordinates", {}).get("y", 0.0),
                }
                forced_for_audit = {
                    "score_x": forced_run.get("coordinates", {}).get("x", 0.0),
                    "score_y": forced_run.get("coordinates", {}).get("y", 0.0),
                }
                verification_mode = getattr(test_instance, "verification_mode", False)
                safety_metadata = getattr(test_instance, "safety_metadata", {})

                stats = report.get("statistics", {})
                cost_val = stats.get("total_cost")
                cost_str = f"${cost_val:.6f}" if cost_val is not None else "0.0"

                PCAuditLogWriter.write_audit_log(
                    model=model,
                    vanilla_res=vanilla_for_audit,
                    forced_res=forced_for_audit,
                    shift_x=float(shift.get("x", 0.0)),
                    shift_y=float(shift.get("y", 0.0)),
                    shift_distance=float(shift.get("distance", 0.0)),
                    polarity_flip_rate=float(shift.get("polarity_flip_rate", 0.0)),
                    detailed_responses=report.get("detailed_responses", {}),
                    verification_mode=verification_mode,
                    safety_metadata=safety_metadata,
                    execution_time=stats.get("total_duration"),
                    total_tokens=stats.get("total_tokens"),
                    cost=cost_str,
                    provider=provider_type,
                    calibration=stats.get("pc_calibration"),
                )
            except Exception as e:
                logger.error("Political Compass Audit Error: %s", e)

        if PCResultManager is not None:
            try:
                PCResultManager.save_leaderboard_csv(report, Path("benchmark_scores"))
            except Exception as e:
                logger.error("Political Compass Leaderboard Error: %s", e)
