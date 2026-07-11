"""ToolUse Leaderboard Exporter — CrucibleMark
Writes tooluse_leaderboard.csv from BenchmarkResult objects.
Buffer/finalize pattern: export_result() buffers per-asset data,
finalize_model() aggregates and writes one row per model.
No LLM calls, no MCP calls.
"""

from __future__ import annotations

import ast
import csv
import json
import logging
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from benchmark_modules.tooluse.core.constants import (
    CSV_COLUMNS,
    FIELD_COMBINED_SCORE,
    FIELD_HALLUCINATION_FLAG,
    FIELD_P1_SCORE,
    FIELD_P2_SCORE,
)
from benchmark_modules.tooluse.core.constants import (
    CSV_PATH as _CSV_PATH_STR,
)
from benchmark_modules.tooluse.core.io_manager import ToolUseIOManager, _log_metrics_to_json
from schemas.result import BenchmarkResult
from utils.model_utils import resolve_canonical_model_id, update_model_card_tooluse_fields

logger = logging.getLogger(__name__)


_LOCAL_DEPLOYMENT_TYPES = {"open-weights", "localweights", "open-weights-cloud-available"}


def get_fleet_group(sizeclass: str, deployment_type: str) -> str:
    """local_sovereign: open-weights or localweights deployment + not Frontier
    full_fleet: Frontier, apionly, restricted-weights, etc.
    """
    if deployment_type in _LOCAL_DEPLOYMENT_TYPES and sizeclass != "Frontier":
        return "local_sovereign"
    return "full_fleet"


class ToolUseExporter:
    """Writes benchmark/scores/tooluse_leaderboard.csv from BenchmarkResult objects.
    Upsert on model_id — no duplicates, always fresh data per model.
    """

    CSV_PATH: Path = Path(_CSV_PATH_STR)

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self._buffer: dict[str, list[BenchmarkResult]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def export_result(self, result: BenchmarkResult, model_id: str) -> None:
        """Buffer per-asset result. Call finalize_model() to write the CSV row.

        .. deprecated:: v4.10.12
            Dieser Pfad (Pfad A) schreibt NUR in ``tooluse_leaderboard.csv``,
            nicht in die Benchmark-CSVs. Die Per-Asset-Detailzeilen gehen verloren
            und der Web-Export kann sie nicht anzeigen.
            **SSoT ist Pfad B:** ``unified_runner._handle_single_asset()`` →
            ``ResultManager.save_results()`` → Benchmark-CSVs, gefolgt von
            ``aggregate_from_benchmark_csvs()`` fuer das Leaderboard.
            Pfad A wird nur noch von Legacy-Code verwendet.
        """
        logger.warning(
            "ToolUseExporter.export_result() ist deprecated (Pfad A). "
            "Verwende stattdessen unified_runner + aggregate_from_benchmark_csvs(). "
            "Detailzeilen fehlen in Benchmark-CSVs bei diesem Pfad."
        )
        self._buffer.setdefault(model_id, []).append(result)

    def finalize_model(self, model_id: str) -> None:
        """Aggregate all buffered assets for model_id, write one CSV row.

        .. deprecated:: v4.10.12
            Siehe :meth:`export_result` — Pfad A ist deprecated.
        """
        results = self._buffer.pop(model_id, [])
        if not results:
            return

        state = self._init_aggregation_state()
        for result in results:
            self._accumulate_buffer_result(result, state)

        card = _load_card_data(model_id) or {}
        row = self._build_leaderboard_row(model_id, results, state, card)

        self._upsert_row(row, model_id)
        try:
            _log_metrics_to_json(model_id, row)
        except Exception:  # noqa: BLE001 — metrics logging must never crash the benchmark
            logger.debug("Metrics logging failed (non-critical)", exc_info=True)

        p1_mean, p2_mean, card_supports = self._compute_card_tooluse_status(
            state["p1_scores"], state["p2_scores"],
        )
        self._persist_card_tooluse(model_id, p1_mean, p2_mean, card_supports, row["timestamp"])

        ToolUseIOManager.print_run_summary(results, model_id)

    def calculate_sovereignty_gap(self) -> float | None:
        """Calculates avg_all - avg_local_sovereign and writes the value
        into every row's sovereignty_gap column. Returns None if < 2 rows
        have valid combined_score values.
        """
        rows = self._read_rows()
        if len(rows) < 2:
            return None

        scores_all: list[float] = []
        scores_local: list[float] = []
        for row in rows:
            try:
                score = float(row.get("combined_score", ""))
            except (ValueError, TypeError):
                continue
            scores_all.append(score)
            if row.get("fleet_group") == "local_sovereign":
                scores_local.append(score)

        if len(scores_all) < 2:
            return None

        avg_all = sum(scores_all) / len(scores_all)
        avg_local = sum(scores_local) / len(scores_local) if scores_local else None
        gap = round(avg_local - avg_all, 2) if avg_local is not None else None

        gap_str = f"{gap:.2f}" if gap is not None else ""
        for row in rows:
            row["sovereignty_gap"] = gap_str
        self._write_rows(rows)

        return gap

    def get_summary(self) -> dict[str, Any]:
        """Returns summary statistics across all rows.
        Core keys: total_models, local_sovereign_count, full_fleet_count,
                   fleet_avg_local, fleet_avg_all, sovereignty_gap,
                   top_local_model, top_overall_model
        Performance keys: avg_call1_time_s, avg_mcp_latency_s, avg_call2_time_s,
                          total_tokens, parse_error_rate
        """
        rows = self._read_rows()
        local_rows = [r for r in rows if r.get("fleet_group") == "local_sovereign"]
        full_rows = [r for r in rows if r.get("fleet_group") == "full_fleet"]

        avg_all = _avg_combined(rows)
        avg_local = _avg_combined(local_rows)
        gap = (
            round(avg_local - avg_all, 2)
            if avg_all is not None and avg_local is not None
            else None
        )

        return {
            "total_models": len(rows),
            "local_sovereign_count": len(local_rows),
            "full_fleet_count": len(full_rows),
            "fleet_avg_local": avg_local,
            "fleet_avg_all": avg_all,
            "sovereignty_gap": gap,
            "top_local_model": _top_model(local_rows),
            "top_overall_model": _top_model(rows),
            "avg_call1_time_s": _avg_float_col(rows, "call1_time_s"),
            "avg_mcp_latency_s": _avg_float_col(rows, "mcp_latency_s"),
            "avg_call2_time_s": _avg_float_col(rows, "call2_time_s"),
            "total_tokens": _sum_int_col(rows, "total_tokens"),
            "parse_error_rate": _parse_error_rate(rows),
        }

    def aggregate_from_benchmark_csvs(
        self,
        csv_paths: list[Path] | None = None,
        target_model_ids: list[str] | None = None,
    ) -> int:
        """Reads per-asset tooluse rows from the main benchmark CSVs, aggregates
        by model, and writes one row per model to tooluse_leaderboard.csv.

        Args:
            csv_paths: Optional list of CSV paths to read from
            target_model_ids: Optional list of model IDs to filter by. If provided,
                            only these models will be updated/shown in output.

        Returns the number of model rows written.
        """
        if csv_paths is None:
            csv_paths = [
                Path("benchmark_scores/local_models_benchmark.csv"),
                Path("benchmark_scores/cloud_models_benchmark.csv"),
                Path("benchmark_scores/commercial_models_benchmark.csv"),
            ]

        best_rows = self._collect_best_rows_from_csvs(csv_paths)
        per_model = self._group_rows_by_model(best_rows)
        if target_model_ids:
            per_model = self._filter_to_target_models(per_model, target_model_ids)
        return self._write_per_model_aggregations(per_model)

    def _write_card_from_aggregated_row(
        self, model_id: str, row: dict[str, Any],
    ) -> None:
        """Persistiert einen aggregierten Tool-Use-Run in der Card (Path B).

        Schreibt nach ``tooluse_runs.{model_id}`` (nested, profil-spezifisch).
        v4.10.16+: ``supports_tool_use`` wird NICHT überschrieben — Capability-Flag
        aus dem Card-Setup (manuell oder auto-generiert) ist die maßgebliche
        Quelle. Ein Mock-Run mit p1=0 (z.B. ``openai/gpt-oss-20b``) bedeutet nicht,
        dass das Modell keine Tools kann — es bedeutet nur, dass der Mock-Test
        keine echten Tool-Calls ausführen konnte. Der Test-Indikator ist
        ``tooluse_runs.{profile_id}.tested_at``: ist er gesetzt, wurde getestet;
        sonst nicht. Das eigentliche Pass/Fail-Signal lebt im Leaderboard.
        """
        try:
            p1 = float(row.get("p1_score", "") or 0.0)
        except (ValueError, TypeError):
            p1 = 0.0
        try:
            p2 = float(row.get("p2_score", "") or 0.0)
        except (ValueError, TypeError):
            p2 = 0.0
        timestamp = row.get("timestamp") or datetime.now(UTC).strftime(
            "%Y-%m-%dT%H:%M:%SZ",
        )

        update_model_card_tooluse_fields(
            model_id=model_id,
            profile_id=model_id,
            # Arg-Wert ist irrelevant bei preserve=True, muss aber einen validen
            # Tri-State-Wert haben damit die Value-Validation in update_model_card_tooluse_fields
            # durchläuft. Wir wählen "untested" als neutralen Default.
            supports_tool_use="untested",
            tested_at=timestamp,
            p1_score=p1,
            p2_score=p2,
            preserve_supports_tool_use=True,
        )

    def _aggregate_asset_rows(
        self, model_id: str, rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build one leaderboard row from per-asset CSV rows for the same model."""
        card = _load_card_data(model_id) or {}
        state = self._init_aggregation_state()
        for row in rows:
            self._accumulate_csv_row(row, state)
        return self._build_leaderboard_row(model_id, rows, state, card)

    # ------------------------------------------------------------------
    # Aggregation helpers (shared by finalize_model + aggregate_from_benchmark_csvs)
    # ------------------------------------------------------------------

    def _init_aggregation_state(self) -> dict[str, Any]:
        return {
            "p1_scores": [], "p2_scores": [], "combined_scores": [],
            "call1_times": [], "mcp_latencies": [], "call2_times": [], "total_times": [],
            "call1_tokens_sum": 0, "call2_tokens_sum": 0, "cost_usd_sum": 0.0,
            "tool_call_valid_all": True, "parse_error_any": False, "hallucination_any": False,
            "tool_call_attempts_max": 0, "mcp_mode": "mock", "assets_error": 0,
        }

    def _accumulate_buffer_result(
        self, result: BenchmarkResult, state: dict[str, Any],
    ) -> None:
        if result.status == "error":
            self._accumulate_buffer_error_result(result, state)
            return
        self._accumulate_data_dict(result.data, state)

    def _accumulate_buffer_error_result(
        self, result: BenchmarkResult, state: dict[str, Any],
    ) -> None:
        state["assets_error"] += 1
        state["tool_call_valid_all"] = False
        try:
            state["tool_call_attempts_max"] = max(
                state["tool_call_attempts_max"],
                int(result.data.get("tool_call_attempts", 0)),
            )
        except (ValueError, TypeError):
            pass
        if result.data.get("retry_required") or result.data.get("parse_error_flag"):
            state["parse_error_any"] = True

    def _accumulate_csv_row(self, row: dict[str, Any], state: dict[str, Any]) -> None:
        if row.get("status") == "error":
            state["assets_error"] += 1
            state["tool_call_valid_all"] = False
        data_dict = self._parse_row_data_dict(row)
        self._accumulate_csv_scores(data_dict, row, state)
        self._accumulate_csv_post_metrics(data_dict, row, state)

    def _accumulate_data_dict(
        self, data_dict: dict[str, Any], state: dict[str, Any],
    ) -> None:
        self._collect_metric_lists(data_dict, state)
        self._collect_transcript_flags(data_dict, state, row=None)
        self._collect_timing_lists(data_dict, state)
        self._collect_sums_and_attempts(data_dict, state)

    def _accumulate_csv_scores(
        self,
        data_dict: dict[str, Any],
        row: dict[str, Any],
        state: dict[str, Any],
    ) -> None:
        """CSV-spezifische Score-Akkumulation mit data_dict→row→total_score Fallbacks."""
        p1 = self._extract_metric_with_fallback(data_dict, row, "p1_score")
        if p1 is not None:
            state["p1_scores"].append(p1)
        p2 = self._extract_metric_with_fallback(data_dict, row, "p2_score")
        if p2 is not None:
            state["p2_scores"].append(p2)
        self._apply_total_score_fallback(row, state, p1, p2)
        self._accumulate_combined_with_row_fallback(data_dict, row, state)

    def _accumulate_csv_post_metrics(
        self,
        data_dict: dict[str, Any],
        row: dict[str, Any],
        state: dict[str, Any],
    ) -> None:
        """Flags + Timing + Sums für CSV-Zeilen (mcp_mode-Fallback via row)."""
        self._collect_transcript_flags(data_dict, state, row=row)
        self._collect_timing_lists(data_dict, state)
        self._collect_sums_and_attempts(data_dict, state)

    def _accumulate_combined_with_row_fallback(
        self,
        data_dict: dict[str, Any],
        row: dict[str, Any],
        state: dict[str, Any],
    ) -> None:
        # combined_score: prefer data_dict, fallback to total_score column.
        # Bewahrt 0.0-Fallback-Bug (0.0 ist falsy → fällt auf total_score zurück) —
        # nicht korrigieren, würde historische Benchmark-Werte verändern.
        combined_raw = data_dict.get("combined_score") or row.get("total_score")
        if combined_raw is not None:
            try:
                state["combined_scores"].append(float(combined_raw))
            except (ValueError, TypeError):
                pass

    def _extract_metric_with_fallback(
        self,
        data_dict: dict[str, Any],
        row: dict[str, Any],
        key: str,
    ) -> float | None:
        val = data_dict.get(key)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                pass
        flat = row.get(key)
        if flat:
            try:
                return float(flat)
            except (ValueError, TypeError):
                pass
        return None

    def _apply_total_score_fallback(
        self,
        row: dict[str, Any],
        state: dict[str, Any],
        p1: float | None,
        p2: float | None,
    ) -> None:
        # total_score Fallback für P1/P2: Wenn weder score_contributions noch
        # flache P1/P2-Spalten vorhanden sind (ältere CSV-Zeilen oder
        # Aggregation aus Haupt-CSV), total_score als Proxy verwenden.
        # total_score = combined_score des Tooluse-Moduls → identisch mit
        # dem Combined-Wert. Ergebnis: P1 ≈ P2 ≈ Combined statt "–".
        ts = row.get("total_score")
        if ts in (None, ""):
            return
        try:
            ts_val = float(ts)
        except (ValueError, TypeError):
            return
        if p1 is None:
            state["p1_scores"].append(ts_val)
        if p2 is None:
            state["p2_scores"].append(ts_val)

    def _parse_row_data_dict(self, row: dict[str, Any]) -> dict[str, Any]:
        """Parse score_contributions Python-repr OR flache CSV-Spalten in ein dict."""
        raw = row.get("score_contributions", "")
        if raw:
            try:
                parsed = ast.literal_eval(raw)
                if parsed:
                    return parsed
            except (ValueError, SyntaxError):
                pass
        return self._parse_flat_columns(row)

    def _parse_flat_columns(self, row: dict[str, Any]) -> dict[str, Any]:
        """Flat-Column-Fallback: wenn score_contributions leer ist (neue Zeilen
        nach dem Redesign des Writers), flache CSV-Spalten als Datenquelle nutzen.
        Ermöglicht korrektes Aggregieren von P1/P2/Timing ohne score_contributions.
        """
        data: dict[str, Any] = {}
        for flat_key in (
            "p1_score", "p2_score", "combined_score",
            "mcp_latency_s", "call1_time_s", "call2_time_s", "total_time_s",
            "call1_tokens", "call2_tokens", "tool_call_attempts",
        ):
            v = row.get(flat_key)
            if v not in (None, ""):
                try:
                    data[flat_key] = float(v)
                except (ValueError, TypeError):
                    pass
        for bk in ("hallucination_flag", "retry_required"):
            bv = row.get(bk)
            if bv not in (None, ""):
                data[bk] = str(bv).lower() == "true"
        # tool_call_valid → tool_transcript-Proxy für die Validierungslogik unten
        tv = row.get("tool_call_valid")
        if tv not in (None, ""):
            status = "success" if str(tv).lower() == "true" else "parse_error"
            data["tool_transcript"] = {"status": status}
        return data

    def _build_leaderboard_row(
        self,
        model_id: str,
        assets: list,
        state: dict[str, Any],
        card: dict[str, Any],
    ) -> dict[str, Any]:
        """Baut eine Leaderboard-Zeile aus aggregiertem State + Card-Daten.

        Shared by finalize_model() und _aggregate_asset_rows(). Reihenfolge und
        Spaltennamen sind SSoT für tooluse_leaderboard.csv.
        """
        display_name: str = card.get("display_name") or model_id
        vendor: str = card.get("vendor") or "Unknown"
        sizeclass: str = card.get("size_class") or "Unknown"
        deployment_type: str = card.get("deployment_type") or "apionly"
        model_version: str = card.get("model_version") or "unknown"
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        fleet_group = get_fleet_group(sizeclass, deployment_type)

        def _mean(lst: list[float]) -> float | None:
            return sum(lst) / len(lst) if lst else None

        # SSoT: Card-Werte für P1/P2 bevorzugen wenn manuell oder per finalize_model()
        # gesetzt. Verhindert dass aggregate_from_benchmark_csvs() validierte Werte
        # überschreibt (z.B. nach Benchmark-Regenerierung).
        # v4.10.16: Per-Profil-Lookup (tooluse_runs.{profile_id}.score_p1) statt
        # flachem Feld — Dual-Thinking-Profile schreiben in separate Slots auf
        # derselben Card.
        p1_card = _get_run_p1_from_card(card, model_id)
        p2_card = _get_run_p2_from_card(card, model_id)
        cost_str = (
            f"{state['cost_usd_sum']:.6f}" if state["cost_usd_sum"]
            else ("local" if deployment_type == "open-weights" else "")
        )

        return {
            "model": model_id,
            "display_name": display_name,
            "vendor": vendor,
            "sizeclass": sizeclass,
            "deployment_type": deployment_type,
            "model_version": model_version,
            "timestamp": timestamp,
            "mcp_mode": state["mcp_mode"],
            "p1_score": (
                _fmt_score(p1_card) if p1_card is not None
                else _fmt_score(_mean(state["p1_scores"]))
            ),
            "p2_score": (
                _fmt_score(p2_card) if p2_card is not None
                else _fmt_score(_mean(state["p2_scores"]))
            ),
            "combined_score": _fmt_score(_mean(state["combined_scores"])),
            "tool_call_valid": str(state["tool_call_valid_all"]).lower(),
            "tool_call_attempts": state["tool_call_attempts_max"],
            "retry_required": str(state["parse_error_any"]).lower(),
            "hallucination_flag": str(state["hallucination_any"]).lower(),
            "call1_time_s": _fmt_score(_mean(state["call1_times"])),
            "mcp_latency_s": _fmt_score(_mean(state["mcp_latencies"])),
            "call2_time_s": _fmt_score(_mean(state["call2_times"])),
            "total_time_s": _fmt_score(sum(state["total_times"]) if state["total_times"] else None),
            "call1_tokens": state["call1_tokens_sum"],
            "call2_tokens": state["call2_tokens_sum"],
            "total_tokens": state["call1_tokens_sum"] + state["call2_tokens_sum"],
            "cost_usd": cost_str,
            "assets_run": len(assets),
            "assets_error": state["assets_error"],
            "fleet_group": fleet_group,
            "sovereignty_gap": "",
        }

    def _compute_card_tooluse_status(
        self,
        p1_scores: list[float],
        p2_scores: list[float],
    ) -> tuple[float | None, float | None, Any]:
        """Tri-State-Semantik für supports_tool_use:
           True       — mittlerer P1-Score > 0 (Modell kann Tool-Calls)
           False      — mittlerer P1-Score == 0 (kein Tool-Call erfolgreich)
           "untested" — keine p1_scores vorhanden (kein Asset gelaufen)
        """
        if not p1_scores:
            return None, None, "untested"
        p1_mean = sum(p1_scores) / len(p1_scores)
        p2_mean = sum(p2_scores) / len(p2_scores) if p2_scores else None
        return p1_mean, p2_mean, p1_mean > 0

    def _persist_card_tooluse(
        self,
        model_id: str,
        p1_mean: float | None,
        p2_mean: float | None,
        card_supports: Any,
        timestamp: str,
    ) -> None:
        """P1/P2 persistent in der Card speichern — SSoT für spätere
        aggregate_from_benchmark_csvs()-Läufe (verhindert Überschreiben).
        v4.10.16: profile_id=model_id für Dual-Thinking-Profile, damit
        Standard- und Thinking-Run getrennte Slots auf der Card nutzen.
        """
        tested_at = timestamp if card_supports != "untested" else None
        try:
            update_model_card_tooluse_fields(
                model_id=model_id,
                profile_id=model_id,
                supports_tool_use=card_supports,
                tested_at=tested_at,
                p1_score=p1_mean,
                p2_score=p2_mean,
            )
        except Exception:  # noqa: BLE001 — Card-Update darf den Benchmark nie crashen
            logger.warning("Model Card tooluse update failed for %s", model_id, exc_info=True)

    # ------------------------------------------------------------------
    # aggregate_from_benchmark_csvs() helpers
    # ------------------------------------------------------------------

    def _collect_best_rows_from_csvs(
        self, csv_paths: list[Path],
    ) -> dict[tuple[str, str], dict[str, Any]]:
        """(model_id, asset_id) → best row: neuester Timestamp gewinnt; bei
        Gleichstand success > error. Verhindert Score-Halbierung wenn dasselbe
        Asset in mehreren CSVs steht (z.B. nach Modell-Migration commercial→cloud
        oder nach fehlgeschlagenem Mock-Run).
        """
        best_rows: dict[tuple[str, str], dict[str, Any]] = {}
        for csv_path in csv_paths:
            if not csv_path.exists():
                continue
            self._collect_best_rows_from_csv(csv_path, best_rows)
        return best_rows

    def _collect_best_rows_from_csv(
        self,
        csv_path: Path,
        best_rows: dict[tuple[str, str], dict[str, Any]],
    ) -> None:
        try:
            with csv_path.open("r", newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    self._maybe_update_best_row(best_rows, row)
        except (OSError, csv.Error) as exc:
            logger.warning("Could not read %s: %s", csv_path, exc)

    def _maybe_update_best_row(
        self,
        best_rows: dict[tuple[str, str], dict[str, Any]],
        row: dict[str, Any],
    ) -> None:
        if not str(row.get("asset_id", "")).startswith("tooluse"):
            return
        model_id = resolve_canonical_model_id(row.get("model", ""))
        if not model_id:
            return
        asset_id = str(row.get("asset_id", ""))
        key = (model_id, asset_id)
        existing = best_rows.get(key)
        if existing is None or row.get("timestamp", "") > existing.get("timestamp", ""):
            best_rows[key] = row
        elif row.get("timestamp", "") == existing.get("timestamp", ""):
            # Gleichzeitig: success > error
            if row.get("status") == "success" and existing.get("status") != "success":
                best_rows[key] = row

    def _group_rows_by_model(
        self, best_rows: dict[tuple[str, str], dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        per_model: dict[str, list[dict[str, Any]]] = {}
        for (model_id, _asset_id), row in best_rows.items():
            per_model.setdefault(model_id, []).append(row)
        return per_model

    def _filter_to_target_models(
        self,
        per_model: dict[str, list[dict[str, Any]]],
        target_model_ids: list[str],
    ) -> dict[str, list[dict[str, Any]]]:
        # SSoT-Bridge: alle IDs werden durch resolve_canonical_model_id() geführt,
        # damit Card-Aliase (claude-haiku-4-5 → claude-haiku-4-5-20251001) und
        # hf.co-Prefixe konsistent aufgelöst werden.
        target_normalized = {resolve_canonical_model_id(m) for m in target_model_ids}
        return {
            mid: rows for mid, rows in per_model.items()
            if resolve_canonical_model_id(mid) in target_normalized
        }

    def _write_per_model_aggregations(
        self, per_model: dict[str, list[dict[str, Any]]],
    ) -> int:
        written = 0
        for model_id, asset_rows in per_model.items():
            row = self._aggregate_asset_rows(model_id, asset_rows)
            self._upsert_row(row, model_id)
            ToolUseIOManager.print_run_summary_from_row(row, model_id)
            # v4.10.16: Card-Update pro Profil-Run, damit die Card-Live-Spiegel
            # des Leaderboards bleibt. Verhindert den No-Op-Failure-Mode
            # (tooluse_tested_at blieb vorher dauerhaft null weil finalize_model
            # nicht in Path B aufgerufen wurde).
            try:
                self._write_card_from_aggregated_row(model_id, row)
            except Exception as exc:  # noqa: BLE001 — Card-Update darf Aggregation nie crashen
                logger.warning(
                    "Card-Update nach Aggregation fehlgeschlagen für %s: %s",
                    model_id, exc,
                )
            written += 1
        return written

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _collect_metric_lists(
        self, data: dict[str, Any], state: dict[str, Any],
    ) -> None:
        for lst, key in [
            (state["p1_scores"], FIELD_P1_SCORE),
            (state["p2_scores"], FIELD_P2_SCORE),
            (state["combined_scores"], FIELD_COMBINED_SCORE),
        ]:
            v = data.get(key)
            if v is not None:
                try:
                    lst.append(float(v))
                except (ValueError, TypeError):
                    pass

    def _collect_transcript_flags(
        self,
        data: dict[str, Any],
        state: dict[str, Any],
        row: dict[str, Any] | None = None,
    ) -> None:
        transcript = data.get("tool_transcript") or {}
        if transcript.get("status") in ("parse_error", "blocked", None, ""):
            state["tool_call_valid_all"] = False
        # mcp_mode: live wenn der MCP-Server tatsächlich aufgerufen wurde
        # (mcp_latency_s > 0), unabhängig vom Tool-Typ (web_search/fetch).
        if (data.get("mcp_latency_s") or 0) > 0:
            state["mcp_mode"] = "live"
        elif row is not None and row.get("mcp_mode") == "live":
            # Flat-Column-Fallback für mcp_mode (wenn mcp_latency_s nicht in data_dict)
            state["mcp_mode"] = "live"
        if data.get(FIELD_HALLUCINATION_FLAG):
            state["hallucination_any"] = True
        if data.get("retry_required") or data.get("parse_error_flag"):
            state["parse_error_any"] = True

    def _collect_timing_lists(
        self, data: dict[str, Any], state: dict[str, Any],
    ) -> None:
        for lst, key in [
            (state["call1_times"], "call1_time_s"),
            (state["mcp_latencies"], "mcp_latency_s"),
            (state["call2_times"], "call2_time_s"),
        ]:
            v = data.get(key)
            if v is not None:
                try:
                    lst.append(float(v))
                except (ValueError, TypeError):
                    pass
        v = data.get("total_time_s")
        if v is not None:
            try:
                state["total_times"].append(float(v))
            except (ValueError, TypeError):
                pass

    def _collect_sums_and_attempts(
        self, data: dict[str, Any], state: dict[str, Any],
    ) -> None:
        try:
            state["call1_tokens_sum"] += int(data.get("call1_tokens", 0))
        except (ValueError, TypeError):
            pass
        try:
            state["call2_tokens_sum"] += int(data.get("call2_tokens", 0))
        except (ValueError, TypeError):
            pass
        try:
            state["cost_usd_sum"] += float(data.get("cost_usd", 0.0))
        except (ValueError, TypeError):
            pass
        try:
            state["tool_call_attempts_max"] = max(
                state["tool_call_attempts_max"],
                int(data.get("tool_call_attempts", 1)),
            )
        except (ValueError, TypeError):
            state["tool_call_attempts_max"] = max(state["tool_call_attempts_max"], 1)

    def _upsert_row(self, new_row: dict[str, Any], model_id: str) -> None:
        self.CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        existing = self._read_rows()
        filtered = [r for r in existing if resolve_canonical_model_id(r.get("model", "")) != model_id]
        self._write_rows(filtered + [new_row])

    def _read_rows(self) -> list[dict[str, Any]]:
        if not self.CSV_PATH.exists() or self.CSV_PATH.stat().st_size == 0:
            return []
        try:
            with self.CSV_PATH.open("r", newline="", encoding="utf-8") as f:
                return list(csv.DictReader(f))
        except (OSError, csv.Error) as exc:
            logger.warning("Could not read %s: %s", self.CSV_PATH, exc)
            return []

    def model_has_results(self, model_id: str) -> bool:
        """Prüft ob ein Modell bereits im ToolUse-Leaderboard vorhanden ist.

        Args:
            model_id: Die Modell-ID (wird durch resolve_canonical_model_id() kanonisiert)

        Returns:
            True wenn das Modell bereits im Leaderboard existiert, False sonst
        """
        rows = self._read_rows()
        normalized_id = resolve_canonical_model_id(model_id)
        for row in rows:
            if resolve_canonical_model_id(row.get("model", "")) == normalized_id:
                return True
        return False

    _BENCHMARK_CSV_PATHS: tuple[str, ...] = (
        "benchmark_scores/local_models_benchmark.csv",
        "benchmark_scores/cloud_models_benchmark.csv",
        "benchmark_scores/commercial_models_benchmark.csv",
    )

    def has_detail_rows(self, model_id: str, *, min_assets: int = 1) -> bool:
        """Prüft ob Per-Asset-Detailzeilen (tooluse*) in Benchmark-CSVs existieren.

        Design-Constraint (v4.10.12): Das ToolUse-Leaderboard wird aus den
        Benchmark-CSVs aggregiert (``aggregate_from_benchmark_csvs()``). Wenn nur
        das Leaderboard existiert, aber die Detailzeilen fehlen (Legacy-Pfad A),
        ist der Cache-Check unvollständig und das Modell muss neu getestet werden.

        Args:
            model_id: Die Modell-ID (wird durch resolve_canonical_model_id() kanonisiert)
            min_assets: Mindestanzahl an tooluse*-Zeilen, die vorhanden sein müssen

        Returns:
            True wenn mindestens ``min_assets`` tooluse*-Zeilen fuer das Modell
            in einer der drei Benchmark-CSVs existieren.
        """
        normalized_id = resolve_canonical_model_id(model_id)
        count = 0
        for csv_rel in self._BENCHMARK_CSV_PATHS:
            csv_path = Path(csv_rel)
            if not csv_path.exists():
                continue
            try:
                with csv_path.open("r", newline="", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        if not str(row.get("asset_id", "")).startswith("tooluse"):
                            continue
                        if resolve_canonical_model_id(row.get("model", "")) == normalized_id:
                            count += 1
                            if count >= min_assets:
                                return True
            except (OSError, csv.Error):
                continue
        return False

    def _write_rows(self, rows: list[dict[str, Any]]) -> None:
        with self.CSV_PATH.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _fmt_score(val: Any) -> str:
    if val is None:
        return ""
    try:
        return f"{float(val):.2f}"
    except (ValueError, TypeError):
        return ""


def _avg_combined(rows: list[dict[str, Any]]) -> float | None:
    scores = []
    for row in rows:
        try:
            scores.append(float(row["combined_score"]))
        except (ValueError, TypeError, KeyError):
            pass
    return round(sum(scores) / len(scores), 2) if scores else None


def _top_model(rows: list[dict[str, Any]]) -> str | None:
    best_model: str | None = None
    best_score = -1.0
    for row in rows:
        try:
            score = float(row.get("combined_score", ""))
        except (ValueError, TypeError):
            continue
        if score > best_score:
            best_score = score
            best_model = row.get("model")
    return best_model


def _avg_float_col(rows: list[dict[str, Any]], col: str) -> float | None:
    vals = []
    for row in rows:
        try:
            v = float(row.get(col, ""))
            if v > 0:
                vals.append(v)
        except (ValueError, TypeError):
            pass
    return round(sum(vals) / len(vals), 2) if vals else None


def _sum_int_col(rows: list[dict[str, Any]], col: str) -> int:
    total = 0
    for row in rows:
        try:
            total += int(row.get(col, 0))
        except (ValueError, TypeError):
            pass
    return total


def _parse_error_rate(rows: list[dict[str, Any]]) -> float | None:
    if not rows:
        return None
    errors = sum(1 for r in rows if r.get("retry_required") == "true")
    return round(errors / len(rows) * 100, 1)


def _load_card_data(model_id: str) -> dict[str, Any] | None:
    """Load model card JSON via _find_card. Returns None if not found."""
    try:
        from utils.model_utils import (
            _find_card,  # pylint: disable=import-outside-toplevel
        )
        card_path = _find_card(model_id)
        if card_path.exists():
            return json.loads(card_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 — card loading boundary (card may not exist)
        logger.debug("Could not load card for %s: %s", model_id, exc)
    return None


def _get_run_p1_from_card(card: dict[str, Any], profile_id: str) -> float | None:
    """Liest P1-Score für ein Profil aus der Card.

    SSoT-Lookup-Reihenfolge:
    1. ``tooluse_runs.{profile_id}.score_p1`` (nested, neuere Schema)
    2. Flach ``tooluse_score_p1`` (Legacy-Fallback, nur für Basis-Profil = Card-Base-ID)
    """
    if not isinstance(card, dict):
        return None
    runs = card.get("tooluse_runs")
    if isinstance(runs, dict):
        run = runs.get(profile_id)
        if isinstance(run, dict):
            val = run.get("score_p1")
            if isinstance(val, (int, float)):
                return float(val)
    # Legacy-Fallback: flaches Feld nur für Basis-Profil (= Card-Base-ID)
    if card.get("model_id") == profile_id:
        val = card.get("tooluse_score_p1")
        if isinstance(val, (int, float)):
            return float(val)
    return None


def _get_run_p2_from_card(card: dict[str, Any], profile_id: str) -> float | None:
    """Liest P2-Score für ein Profil aus der Card. (Siehe _get_run_p1_from_card.)"""
    if not isinstance(card, dict):
        return None
    runs = card.get("tooluse_runs")
    if isinstance(runs, dict):
        run = runs.get(profile_id)
        if isinstance(run, dict):
            val = run.get("score_p2")
            if isinstance(val, (int, float)):
                return float(val)
    if card.get("model_id") == profile_id:
        val = card.get("tooluse_score_p2")
        if isinstance(val, (int, float)):
            return float(val)
    return None
