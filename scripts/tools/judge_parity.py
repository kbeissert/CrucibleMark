#!/usr/bin/env python3
"""
Judge-Parity-Tool: Bewertet historische Benchmark-Antworten mit zwei
Judge-Modellen und quantifiziert den Score-Drift.

Anlass: Judge-Wechsel 2026-09-20 (claude-haiku-4-5-20251001 →
z-ai/glm-5.3-flash). Historische Rows (mit Haiku-Judge-Score) werden
neu bewertet, um die Vergleichbarkeits-Lücke zu messen.

Datenquelle: outputs/audit_logs/<model>/<asset_id>.md — die Audit-Logs
enthalten Model-Response und Legacy-Judge-Score (CSVs persistieren
raw_response nicht). task_prompt/golden_standard/rubric kommen aus den
Modul-Asset-YAMLs (SSoT: metadata.id = asset_id, Golden-Resolution wie
judge_evaluator._resolve_golden_standard).

Usage:
    .venv/bin/python scripts/tools/judge_parity.py --limit 20
    .venv/bin/python scripts/tools/judge_parity.py --limit 10 --modules ux_writing,documentation_quality
"""

import argparse
import re
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import yaml  # noqa: E402

from utils.io_helpers import atomic_write_text  # noqa: E402
from utils.scoring.llm_judge.judge_config import LLMJudgeConfig  # noqa: E402
from utils.scoring.llm_judge.judge_runner import JudgeRunner  # noqa: E402
from utils.scoring.judge_evaluator import _resolve_golden_standard  # noqa: E402
from utils.benchmark_utils import load_asset_yaml  # noqa: E402

AUDIT_LOG_DIR = "outputs/audit_logs"
SECTION_RESPONSE = "## 2. Model Response / Antwort"
SECTION_EVALUATION = "## 3. Evaluation / LLM-Judge / Scorer"
RE_JUDGE_SCORE = re.compile(r"LLM Judge Score \(Raw\):\**\s*([\d.]+)")
RE_EVALUATED_BY = re.compile(r"\*\*Evaluated by:\*\*\s*(\S+)\s*/\s*(\S+)")
RE_EXECUTION_TIME = re.compile(r"\*\*Execution Time:\*\*\s*([\d.]+)\s*s")
LEGACY_PROVIDER = "anthropic"
LEGACY_MODEL = "claude-haiku-4-5-20251001"
MS_PER_SECOND = 1000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Judge-Parity-Messung.")
    parser.add_argument("--limit", type=int, default=20,
                        help="Max. Anzahl Rows (gleichmäßig über Module verteilt).")
    parser.add_argument("--modules", type=str, default="",
                        help="Komma-separierte Modul-Filter (Default: alle Judge-Module).")
    parser.add_argument("--legacy-provider", type=str, default=LEGACY_PROVIDER)
    parser.add_argument("--legacy-model", type=str, default=LEGACY_MODEL)
    parser.add_argument("--output", type=str, default="",
                        help="Output-CSV (Default: outputs/judge_parity_<ts>.csv).")
    return parser.parse_args()


def load_applicable_modules(config: LLMJudgeConfig, module_filter: str) -> list[str]:
    modules = list(config.applicable_modules)
    if module_filter:
        wanted = {m.strip() for m in module_filter.split(",") if m.strip()}
        unknown = wanted - set(modules)
        if unknown:
            raise SystemExit(f"Unbekannte Module (nicht in llm_judge.applicable_modules): {sorted(unknown)}")
        modules = [m for m in modules if m in wanted]
    return modules


def load_asset_index(
    raw_config: dict[str, Any],
    modules: list[str],
) -> dict[str, tuple[str, dict[str, Any]]]:
    """Mappt asset_id → (module_id, asset_data) über metadata.id der Asset-YAMLs.

    Modul-Pfade kommen aus der Modul-Registry (benchmark_config.yaml#modules),
    nicht aus dem Verzeichnisnamen (Fall: reasoning → reasoning_logic).
    """
    registry: dict[str, str] = raw_config.get("modules", {})
    index: dict[str, tuple[str, dict[str, Any]]] = {}
    for module_id in modules:
        entry = registry.get(module_id)
        if not entry:
            print(f"⚠️  Modul '{module_id}' nicht in der Modul-Registry, übersprungen.")
            continue
        assets_dir = ROOT_DIR / entry["path"] / "assets"
        if not assets_dir.exists():
            print(f"⚠️  Assets-Verzeichnis fehlt für '{module_id}', übersprungen: {assets_dir}")
            continue
        for asset_path in sorted(assets_dir.glob("*.yaml")):
            asset_data = load_asset_yaml(asset_path)
            asset_id = asset_data.get("metadata", {}).get("id")
            if not asset_id:
                raise SystemExit(f"Asset ohne metadata.id: {asset_path}")
            if asset_id in index:
                raise SystemExit(f"Doppelte asset_id: {asset_id}")
            index[asset_id] = (module_id, asset_data)
    return index


def parse_audit_log(path: Path) -> dict[str, str] | None:
    """Extrahiert Model-Response und Legacy-Judge-Daten aus einem Audit-Log."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"⚠️  Audit-Log unlesbar, übersprungen: {path} ({exc})")
        return None
    if SECTION_RESPONSE not in text or SECTION_EVALUATION not in text:
        return None
    response = text.split(SECTION_RESPONSE, 1)[1].split(SECTION_EVALUATION, 1)[0].strip()
    if not response:
        return None
    score_match = RE_JUDGE_SCORE.search(text)
    evaluated = RE_EVALUATED_BY.search(text)
    exec_match = RE_EXECUTION_TIME.search(text)
    return {
        "asset_id": path.stem,
        "model": path.parent.name,
        "raw_response": response,
        "execution_time_s": exec_match.group(1) if exec_match else "0",
        "legacy_judge_score": score_match.group(1) if score_match else "",
        "legacy_judge_provider": evaluated.group(1) if evaluated else "",
        "legacy_judge_model": evaluated.group(2) if evaluated else "",
    }


def collect_rows(
    asset_index: dict[str, tuple[str, dict[str, Any]]],
    legacy_model: str,
    limit: int,
) -> list[dict[str, str]]:
    """Sammelt judge-fähige Audit-Log-Rows, round-robin über Module."""
    audit_root = ROOT_DIR / AUDIT_LOG_DIR
    if not audit_root.exists():
        raise SystemExit(f"Audit-Log-Verzeichnis fehlt: {audit_root}")
    by_module: dict[str, list[dict[str, str]]] = defaultdict(list)
    for model_dir in sorted(audit_root.iterdir()):
        if not model_dir.is_dir():
            continue
        for log_path in sorted(model_dir.glob("*.md")):
            if log_path.stem not in asset_index:
                continue
            parsed = parse_audit_log(log_path)
            if not parsed:
                continue
            if parsed["legacy_judge_model"] != legacy_model:
                continue
            if not parsed["legacy_judge_score"]:
                continue
            module_id = asset_index[parsed["asset_id"]][0]
            by_module[module_id].append(parsed)

    ordered_modules = sorted(by_module)
    selected: list[dict[str, str]] = []
    cursor = 0
    while len(selected) < limit and any(by_module[m] for m in ordered_modules):
        module_id = ordered_modules[cursor % len(ordered_modules)]
        if by_module[module_id]:
            selected.append(by_module[module_id].pop(0))
        cursor += 1
    return selected


def build_judge_configs(args: argparse.Namespace) -> tuple[LLMJudgeConfig, LLMJudgeConfig]:
    with open(ROOT_DIR / "benchmark_config.yaml", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    new_cfg = LLMJudgeConfig.from_dict(raw)
    legacy_cfg = new_cfg.model_copy(deep=True)
    legacy_cfg.provider.name = args.legacy_provider  # type: ignore[assignment]
    legacy_cfg.provider.model = args.legacy_model
    legacy_cfg.provider.base_url = None
    legacy_cfg.provider.api_key_env = None
    return legacy_cfg, new_cfg


def score_row(
    runner: JudgeRunner,
    row: dict[str, str],
    module_id: str,
    asset_data: dict[str, Any],
) -> tuple[float | None, float]:
    result = runner.score(
        task_prompt=asset_data.get("prompt", asset_data.get("instruction", "")),
        model_response=row["raw_response"],
        golden_standard=_resolve_golden_standard(asset_data),
        module_id=module_id,
        rubric_override=asset_data.get("scoring", {}).get("rubric"),
        tested_model_id=row.get("model"),
        response_time_ms=float(row.get("execution_time_s") or 0) * MS_PER_SECOND,
        required_language=asset_data.get("metadata", {}).get("language"),
        language_weight=asset_data.get("metadata", {}).get("language_weight", 0.20),
    )
    return result.score, result.judge_latency_ms


def write_report(
    output_path: Path,
    results: list[dict[str, Any]],
) -> None:
    fieldnames = [
        "module_id", "asset_id", "model", "legacy_judge_model",
        "legacy_score", "new_score", "delta",
        "legacy_latency_ms", "new_latency_ms",
    ]
    lines = [",".join(fieldnames)]
    for r in results:
        lines.append(",".join(str(r.get(k, "")) for k in fieldnames))
    atomic_write_text(output_path, "\n".join(lines) + "\n")


def print_summary(results: list[dict[str, Any]]) -> None:
    by_module: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in results:
        by_module[r["module_id"]].append(r)

    print("\n=== Judge-Parity: Legacy (Haiku 4.5) vs. Neu (GLM 5.3 Flash) ===")
    print(f"{'Modul':<28}{'n':>4}{'Ø legacy':>10}{'Ø neu':>8}{'Ø Δ':>8}{'exact':>8}{'±1':>6}")
    totals: list[dict[str, Any]] = []
    for module_id in sorted(by_module):
        _print_module_row(module_id, by_module[module_id])
        totals.extend(by_module[module_id])
    _print_module_row("GESAMT", totals)
    parse_failures = sum(1 for r in results if r["new_score"] is None)
    if parse_failures:
        print(f"⚠️  {parse_failures} Row(s) mit Parse-Failure (Score=None) — im Report markiert.")


def _print_module_row(label: str, rows: list[dict[str, Any]]) -> None:
    scored = [r for r in rows if r["legacy_score"] is not None and r["new_score"] is not None]
    n = len(scored)
    if n == 0:
        print(f"{label:<28}{len(rows):>4}{'-':>10}{'-':>8}{'-':>8}{'-':>8}{'-':>6}")
        return
    mean_legacy = sum(r["legacy_score"] for r in scored) / n
    mean_new = sum(r["new_score"] for r in scored) / n
    exact = sum(1 for r in scored if r["new_score"] == r["legacy_score"]) / n * 100
    within1 = sum(1 for r in scored if abs(r["new_score"] - r["legacy_score"]) <= 1) / n * 100
    print(
        f"{label:<28}{n:>4}{mean_legacy:>10.2f}{mean_new:>8.2f}"
        f"{mean_new - mean_legacy:>8.2f}{exact:>7.0f}%{within1:>5.0f}%"
    )


def main() -> None:
    args = parse_args()
    start = time.monotonic()

    with open(ROOT_DIR / "benchmark_config.yaml", encoding="utf-8") as f:
        raw_cfg = yaml.safe_load(f)
    judge_cfg = LLMJudgeConfig.from_dict(raw_cfg)
    modules = load_applicable_modules(judge_cfg, args.modules)
    asset_index = load_asset_index(raw_cfg, modules)
    rows = collect_rows(asset_index, args.legacy_model, args.limit)
    if not rows:
        raise SystemExit("Keine judge-fähigen Rows gefunden.")
    print(f"{len(rows)} Rows ausgewählt über {len(sorted({asset_index[r['asset_id']][0] for r in rows}))} Module.")

    legacy_cfg, new_cfg = build_judge_configs(args)
    legacy_runner = JudgeRunner(legacy_cfg)
    new_runner = JudgeRunner(new_cfg)
    print(f"Legacy-Judge: {legacy_cfg.provider.name}:{legacy_cfg.provider.model}")
    print(f"Neuer Judge:  {new_cfg.provider.name}:{new_cfg.provider.model}\n")

    results: list[dict[str, Any]] = []
    for i, row in enumerate(rows, 1):
        module_id, asset_data = asset_index[row["asset_id"]]
        legacy_score, legacy_ms = score_row(legacy_runner, row, module_id, asset_data)
        new_score, new_ms = score_row(new_runner, row, module_id, asset_data)
        delta = (
            new_score - legacy_score
            if legacy_score is not None and new_score is not None
            else ""
        )
        results.append({
            "module_id": module_id,
            "asset_id": row["asset_id"],
            "model": row.get("model", ""),
            "legacy_judge_model": row.get("legacy_judge_model", ""),
            "legacy_score": legacy_score,
            "new_score": new_score,
            "delta": delta,
            "legacy_latency_ms": round(legacy_ms),
            "new_latency_ms": round(new_ms),
        })
        print(f"[{i}/{len(rows)}] {module_id}/{row['asset_id']} ({row.get('model', '')[:30]}): "
              f"legacy={legacy_score} neu={new_score} Δ={delta}")

    output_path = (
        Path(args.output)
        if args.output
        else ROOT_DIR / "outputs"
        / f"judge_parity_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.csv"
    )
    write_report(output_path, results)
    print_summary(results)
    print(f"\nReport: {output_path}")
    print(f"Dauer: {time.monotonic() - start:.0f} s")


if __name__ == "__main__":
    main()
