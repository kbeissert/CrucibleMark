"""Token efficiency context builder for the review pipeline."""

from __future__ import annotations

import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.constants import TOKEN_VERBOSITY_BUDGET_MULTIPLIER
from utils.scoring_utils import normalize_model_name

# Maps asset_id prefixes to module config keys.
# '__exempt__' means the module has no token budget (excluded from overhead analysis).
_MODULE_PREFIX_MAP: dict[str, str] = {
    "cultural_intel": "cultural_intelligence",
    "ux_writing": "ux_writing",
    "content_transf": "content_transformation",
    "documentation_quality": "documentation_quality",
    "code_quality": "code_quality",
    "cli": "cli_benchmark",
    "reasoning_metacog": "__exempt__",
    "reasoning": "__exempt__",
}

_BENCHMARK_CSV_NAMES = (
    "local_models_benchmark.csv",
    "commercial_models_benchmark.csv",
    "cloud_models_benchmark.csv",
)


def _asset_to_module(asset_id: str) -> str | None:
    for prefix, key in _MODULE_PREFIX_MAP.items():
        if asset_id.startswith(prefix):
            return key
    return None


def _collect_fleet_tokens() -> dict[str, dict[str, list[float]]]:
    fleet_per_model: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for csv_name in _BENCHMARK_CSV_NAMES:
        src = ROOT_DIR / "benchmark_scores" / csv_name
        if not src.exists():
            continue
        try:
            with open(src, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    asset_id = row.get("asset_id", "")
                    model_name = row.get("model", "")
                    try:
                        tokens = float(row.get("tokens_used", "") or 0)
                    except (ValueError, TypeError):
                        tokens = 0.0
                    if not asset_id or tokens <= 0 or asset_id.startswith("political_compass"):
                        continue
                    module_key = _asset_to_module(asset_id)
                    if module_key is None:
                        continue
                    fleet_per_model[normalize_model_name(model_name)][module_key].append(tokens)
        except Exception:
            continue
    return fleet_per_model


def _find_target_key(fleet_per_model: dict, norm_target: str) -> str | None:
    return next(
        (k for k in fleet_per_model if k == norm_target or k.startswith(norm_target) or norm_target.startswith(k)),
        None,
    )


def _compute_fleet_median(fleet_per_model: dict, module_key: str) -> float | None:
    fleet_all = [
        statistics.mean(data[module_key])
        for data in fleet_per_model.values()
        if data.get(module_key)
    ]
    if len(fleet_all) < 2:
        return None
    return round(statistics.median(fleet_all), 0)


def _module_status(
    module_key: str,
    target_avg: float,
    fleet_median: float | None,
    token_budgets: dict[str, int],
) -> tuple[str, str, str]:
    """Returns (status, budget_str, overhead_str) for a single module."""
    if module_key == "__exempt__":
        return "⚪ Exempt", "Exempt", "–"

    budget = token_budgets.get(module_key)
    budget_str = str(budget) if budget else "–"
    overhead_str: str
    if fleet_median and fleet_median > 0:
        overhead = round(target_avg / fleet_median, 2)
        overhead_str = f"{overhead}×"
    else:
        overhead_str = "n/a"

    if budget is not None and target_avg > budget * TOKEN_VERBOSITY_BUDGET_MULTIPLIER:
        ratio = round(target_avg / budget, 1)
        status = f"🔴 Verbos ({ratio}× Budget)"
    elif budget is not None and target_avg > budget:
        status = "🟡 Erhöht"
    else:
        status = "🟢 OK"
    return status, budget_str, overhead_str


def _module_display_name(module_key: str) -> str:
    if module_key == "__exempt__":
        return "Reasoning / Metacog"
    return module_key.replace("_", " ").replace("__", "").title()


def build_token_efficiency_context(tested_model_name: str, token_budgets: dict[str, int]) -> str:
    """Compute per-module token overhead vs. fleet median.

    Returns a formatted Markdown table or an informational note if no data is available.
    """
    norm_target = normalize_model_name(tested_model_name)
    fleet_per_model = _collect_fleet_tokens()

    if not fleet_per_model:
        return "*Keine Token-Daten in den Benchmark-CSVs vorhanden.*"

    target_key = _find_target_key(fleet_per_model, norm_target)
    if target_key is None:
        return f"*Kein CSV-Eintrag für `{tested_model_name}` gefunden — Token-Effizienz nicht berechenbar.*"

    all_modules: set[str] = {mod for data in fleet_per_model.values() for mod in data}

    lines = ["### Token-Effizienz pro Modul\n"]
    lines.append("| Modul | Dieses Modell (Ø) | Fleet-Median | Overhead | Budget | Status |")
    lines.append("|-------|:---:|:---:|:---:|:---:|:---:|")

    has_data = False
    for module_key in sorted(all_modules):
        target_vals = fleet_per_model[target_key].get(module_key, [])
        if not target_vals:
            continue
        target_avg = round(statistics.mean(target_vals), 0)
        fleet_median = _compute_fleet_median(fleet_per_model, module_key)
        status, budget_str, overhead_str = _module_status(module_key, target_avg, fleet_median, token_budgets)
        fleet_str = str(int(fleet_median)) if fleet_median else "n/a"
        display_name = _module_display_name(module_key)
        lines.append(f"| {display_name} | {int(target_avg)} | {fleet_str} | {overhead_str} | {budget_str} | {status} |")
        has_data = True

    if not has_data:
        return f"*Keine Modul-Token-Daten für `{tested_model_name}` gefunden.*"

    return "\n".join(lines)
