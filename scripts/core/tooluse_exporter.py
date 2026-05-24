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
from datetime import datetime, timezone
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
from benchmark_modules.tooluse.core.io_manager import ToolUseIOManager
from schemas.result import BenchmarkResult

logger = logging.getLogger(__name__)


_LOCAL_DEPLOYMENT_TYPES = {"localweights", "open-weights-cloud-available"}


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
        """Buffer per-asset result. Call finalize_model() to write the CSV row."""
        self._buffer.setdefault(model_id, []).append(result)

    def finalize_model(self, model_id: str) -> None:
        """Aggregate all buffered assets for model_id, write one CSV row."""
        results = self._buffer.pop(model_id, [])
        if not results:
            return

        card = _load_card_data(model_id) or {}
        display_name: str = card.get("display_name") or model_id
        vendor: str = card.get("vendor") or "Unknown"
        sizeclass: str = card.get("size_class") or "Unknown"
        deployment_type: str = card.get("deployment_type") or "apionly"
        model_version: str = card.get("model_version") or "unknown"

        p1_scores: list[float] = []
        p2_scores: list[float] = []
        combined_scores: list[float] = []
        call1_times: list[float] = []
        mcp_latencies: list[float] = []
        call2_times: list[float] = []
        total_times: list[float] = []
        call1_tokens_sum = 0
        call2_tokens_sum = 0
        cost_usd_sum = 0.0
        tool_call_valid_all = True
        parse_error_any = False
        hallucination_any = False
        tool_call_attempts_max = 0
        mcp_mode = "mock"
        assets_error = 0
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        for result in results:
            if result.status == "error":
                assets_error += 1
                tool_call_valid_all = False
                try:
                    tool_call_attempts_max = max(tool_call_attempts_max, int(result.data.get("tool_call_attempts", 0)))
                except (ValueError, TypeError):
                    pass
                if result.data.get("parse_error_flag"):
                    parse_error_any = True
                continue

            data = result.data

            # Scores
            for lst, key in [
                (p1_scores, FIELD_P1_SCORE),
                (p2_scores, FIELD_P2_SCORE),
                (combined_scores, FIELD_COMBINED_SCORE),
            ]:
                v = data.get(key)
                if v is not None:
                    try:
                        lst.append(float(v))
                    except (ValueError, TypeError):
                        pass

            # Transcript / flags
            transcript = data.get("tool_transcript") or {}
            if transcript.get("status") in ("parse_error", "blocked", None, ""):
                tool_call_valid_all = False
            provider_val = transcript.get("provider") or "mock"
            if provider_val != "mock":
                mcp_mode = "live"

            if data.get(FIELD_HALLUCINATION_FLAG):
                hallucination_any = True
            if data.get("parse_error_flag"):
                parse_error_any = True

            # Timing (per-call → mean; total → sum)
            for lst, key in [
                (call1_times, "call1_time_s"),
                (mcp_latencies, "mcp_latency_s"),
                (call2_times, "call2_time_s"),
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
                    total_times.append(float(v))
                except (ValueError, TypeError):
                    pass

            # Tokens (sum)  # noqa: ERA001
            try:
                call1_tokens_sum += int(data.get("call1_tokens", 0))
            except (ValueError, TypeError):
                pass
            try:
                call2_tokens_sum += int(data.get("call2_tokens", 0))
            except (ValueError, TypeError):
                pass

            # Cost (sum)  # noqa: ERA001
            try:
                cost_usd_sum += float(data.get("cost_usd", 0.0))
            except (ValueError, TypeError):
                pass

            # Reliability
            try:
                tool_call_attempts_max = max(tool_call_attempts_max, int(data.get("tool_call_attempts", 1)))
            except (ValueError, TypeError):
                tool_call_attempts_max = max(tool_call_attempts_max, 1)

        fleet_group = get_fleet_group(sizeclass, deployment_type)

        def _mean(lst: list[float]) -> float | None:
            return sum(lst) / len(lst) if lst else None

        row: dict[str, Any] = {
            "model": model_id,
            "display_name": display_name,
            "vendor": vendor,
            "sizeclass": sizeclass,
            "deployment_type": deployment_type,
            "model_version": model_version,
            "timestamp": timestamp,
            "mcp_mode": mcp_mode,
            "p1_score": _fmt_score(_mean(p1_scores)),
            "p2_score": _fmt_score(_mean(p2_scores)),
            "combined_score": _fmt_score(_mean(combined_scores)),
            "tool_call_valid": str(tool_call_valid_all).lower(),
            "tool_call_attempts": tool_call_attempts_max,
            "parse_error_flag": str(parse_error_any).lower(),
            "hallucination_flag": str(hallucination_any).lower(),
            "call1_time_s": _fmt_score(_mean(call1_times)),
            "mcp_latency_s": _fmt_score(_mean(mcp_latencies)),
            "call2_time_s": _fmt_score(_mean(call2_times)),
            "total_time_s": _fmt_score(sum(total_times) if total_times else None),
            "call1_tokens": call1_tokens_sum,
            "call2_tokens": call2_tokens_sum,
            "total_tokens": call1_tokens_sum + call2_tokens_sum,
            "cost_usd": f"{cost_usd_sum:.6f}" if cost_usd_sum else "",
            "assets_run": len(results),
            "assets_error": assets_error,
            "fleet_group": fleet_group,
            "sovereignty_gap": "",
        }

        self._upsert_row(row, model_id)
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
    ) -> int:
        """Reads per-asset tooluse rows from the main benchmark CSVs, aggregates
        by model, and writes one row per model to tooluse_leaderboard.csv.

        Returns the number of model rows written.
        """
        if csv_paths is None:
            csv_paths = [
                Path("benchmark_scores/local_models_benchmark.csv"),
                Path("benchmark_scores/cloud_models_benchmark.csv"),
                Path("benchmark_scores/commercial_models_benchmark.csv"),
            ]

        # model_id → list of per-asset row dicts
        per_model: dict[str, list[dict[str, Any]]] = {}

        for csv_path in csv_paths:
            if not csv_path.exists():
                continue
            try:
                with csv_path.open("r", newline="", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        if not str(row.get("asset_id", "")).startswith("tooluse"):
                            continue
                        model_id = row.get("model", "")
                        if not model_id:
                            continue
                        per_model.setdefault(model_id, []).append(row)
            except (OSError, csv.Error) as exc:
                logger.warning("Could not read %s: %s", csv_path, exc)

        written = 0
        for model_id, asset_rows in per_model.items():
            row = self._aggregate_asset_rows(model_id, asset_rows)
            self._upsert_row(row, model_id)
            ToolUseIOManager.print_run_summary_from_row(row, model_id)
            written += 1

        return written

    def _aggregate_asset_rows(
        self, model_id: str, rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Build one leaderboard row from per-asset CSV rows for the same model."""
        card = _load_card_data(model_id) or {}
        display_name = card.get("display_name") or model_id
        vendor = card.get("vendor") or "Unknown"
        sizeclass = card.get("size_class") or "Unknown"
        deployment_type = card.get("deployment_type") or "apionly"
        model_version = card.get("model_version") or "unknown"

        p1_scores: list[float] = []
        p2_scores: list[float] = []
        combined_scores: list[float] = []
        call1_times: list[float] = []
        mcp_latencies: list[float] = []
        call2_times: list[float] = []
        total_times: list[float] = []
        call1_tokens_sum = 0
        call2_tokens_sum = 0
        cost_usd_sum = 0.0
        hallucination_any = False
        tool_call_valid_all = True
        parse_error_any = False
        tool_call_attempts_max = 0
        mcp_mode = "mock"
        assets_error = 0
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        for row in rows:
            if row.get("status") == "error":
                assets_error += 1
                tool_call_valid_all = False

            # Parse scores from score_contributions column (Python repr dict)
            data_dict: dict[str, Any] = {}
            raw_data = row.get("score_contributions", "")
            if raw_data:
                try:
                    data_dict = ast.literal_eval(raw_data)
                except (ValueError, SyntaxError):
                    pass

            if data_dict.get("p1_score") is not None:
                try:
                    p1_scores.append(float(data_dict["p1_score"]))
                except (ValueError, TypeError):
                    pass
            if data_dict.get("p2_score") is not None:
                try:
                    p2_scores.append(float(data_dict["p2_score"]))
                except (ValueError, TypeError):
                    pass

            # combined_score: prefer data_dict, fallback to total_score column
            combined_raw = data_dict.get("combined_score") or row.get("total_score")
            if combined_raw is not None:
                try:
                    combined_scores.append(float(combined_raw))
                except (ValueError, TypeError):
                    pass

            if data_dict.get("hallucination_flag"):
                hallucination_any = True

            transcript = data_dict.get("tool_transcript") or {}
            if transcript.get("status") in ("parse_error", "blocked", None, ""):
                tool_call_valid_all = False
            provider_val = transcript.get("provider", "mock")
            if provider_val and provider_val != "mock":
                mcp_mode = "live"

            # Performance metrics
            for lst, key in [
                (call1_times, "call1_time_s"),
                (mcp_latencies, "mcp_latency_s"),
                (call2_times, "call2_time_s"),
            ]:
                v = data_dict.get(key)
                if v is not None:
                    try:
                        lst.append(float(v))
                    except (ValueError, TypeError):
                        pass
            v = data_dict.get("total_time_s")
            if v is not None:
                try:
                    total_times.append(float(v))
                except (ValueError, TypeError):
                    pass

            try:
                call1_tokens_sum += int(data_dict.get("call1_tokens", 0))
            except (ValueError, TypeError):
                pass
            try:
                call2_tokens_sum += int(data_dict.get("call2_tokens", 0))
            except (ValueError, TypeError):
                pass
            try:
                cost_usd_sum += float(data_dict.get("cost_usd", 0.0))
            except (ValueError, TypeError):
                pass

            if data_dict.get("parse_error_flag"):
                parse_error_any = True
            try:
                tool_call_attempts_max = max(tool_call_attempts_max, int(data_dict.get("tool_call_attempts", 1)))
            except (ValueError, TypeError):
                tool_call_attempts_max = max(tool_call_attempts_max, 1)

        fleet_group = get_fleet_group(sizeclass, deployment_type)

        def _mean(lst: list[float]) -> float | None:
            return sum(lst) / len(lst) if lst else None

        return {
            "model": model_id,
            "display_name": display_name,
            "vendor": vendor,
            "sizeclass": sizeclass,
            "deployment_type": deployment_type,
            "model_version": model_version,
            "timestamp": timestamp,
            "mcp_mode": mcp_mode,
            "p1_score": _fmt_score(_mean(p1_scores)),
            "p2_score": _fmt_score(_mean(p2_scores)),
            "combined_score": _fmt_score(_mean(combined_scores)),
            "tool_call_valid": str(tool_call_valid_all).lower(),
            "tool_call_attempts": tool_call_attempts_max,
            "parse_error_flag": str(parse_error_any).lower(),
            "hallucination_flag": str(hallucination_any).lower(),
            "call1_time_s": _fmt_score(_mean(call1_times)),
            "mcp_latency_s": _fmt_score(_mean(mcp_latencies)),
            "call2_time_s": _fmt_score(_mean(call2_times)),
            "total_time_s": _fmt_score(sum(total_times) if total_times else None),
            "call1_tokens": call1_tokens_sum,
            "call2_tokens": call2_tokens_sum,
            "total_tokens": call1_tokens_sum + call2_tokens_sum,
            "cost_usd": f"{cost_usd_sum:.6f}" if cost_usd_sum else "",
            "assets_run": len(rows),
            "assets_error": assets_error,
            "fleet_group": fleet_group,
            "sovereignty_gap": "",
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _upsert_row(self, new_row: dict[str, Any], model_id: str) -> None:
        self.CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        existing = self._read_rows()
        filtered = [r for r in existing if r.get("model") != model_id]
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
    errors = sum(1 for r in rows if r.get("parse_error_flag") == "true")
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
