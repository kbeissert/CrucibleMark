#!/usr/bin/env python3
"""PC-v3.1-Recompute: Koordinaten aus Checkpoint-Rohdaten neu auswerten.

Kontext (2026-09-24, Befund claude-opus-5-5): PC-v3 scorete Non-Answer-Finals
(Refusal-/Format-Essays) ueber den Loose-Parse-Fallback als Zufallsantworten in
die Koordinaten. PC v3.1 (Commit ddc1732e) schliesst das aus — historische
Laeufe sind aus Checkpoint-Rohdaten recomputbar (run_seeds deterministisch,
keine Neu-Query noetig).

Weg: Pro Frage wird das Runtime-Mapping rekonstruiert (question_seed +
_build_prompt), NUR classification == "answer" Finals werden gescoret (strict
verifiziert), anschliessend Intersection-Filter und Aggregation wie in
execute(). Persistenz ausschliesslich ueber die SSoT-Pfade:
PoliticalCompassHandler.update_results_csv (CSV-Upsert) und
PoliticalCompassResultManager.save_json (Lauf-JSON).

Bewusst NICHT verwendet: PoliticalCompassHandler.handle_results — es wuerde
bei shift > 1.0 autonom die Anomaly-Triple-Verifikation (Neu-Queries) triggern
und Derivate (Audit-Log/Bias-Review) generieren. Der Recompute ist rein
rechnerisch.

Nutzung:
    python scripts/dev/recompute_pc_v31.py --model claude-opus-5-5           # Dry-Run
    python scripts/dev/recompute_pc_v31.py --model claude-opus-5-5 --write  # CSV + JSON
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import re
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from benchmark_modules.political_compass.core.evaluators import (  # noqa: E402
    PoliticalCompassEvaluator,
)
from benchmark_modules.political_compass.core.io_manager import (  # noqa: E402
    PoliticalCompassResultManager,
)
from benchmark_modules.political_compass.test import (  # noqa: E402
    PoliticalCompassTest,
    question_seed,
)
from utils.scoring.political_compass_handler import (  # noqa: E402
    PoliticalCompassHandler,
)

TEMP_DIR = ROOT_DIR / "outputs" / "temp"
RUNS_DIR = ROOT_DIR / "outputs" / "runs"


def _safe_name(model: str) -> str:
    """Checkpoint-/Results-Dateinamen-Konvention (wie CheckpointManager)."""
    return re.sub(r"[^a-zA-Z0-9]", "_", model)


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _verify_asset_integrity(test: PoliticalCompassTest, detailed: dict[str, Any]) -> None:
    """Fail-Fast: Checkpoint-Fragen muessen in den aktuellen Assets existieren.

    Assets sind gitignored (AGENTS.md) — nach ID-Umbenennungen/-Loeschungen
    seit dem Lauf wuerde der Recompute mit falschem Asset-Stand scoren und
    still vom Original-Lauf divergieren (Review-F4). Zusatzwarnung, wenn die
    Assets Fragen OHNE Checkpoint-Eintrag enthalten (die erscheinen als
    skipped['missing'] und schmaelern die Vergleichbarkeit).
    """
    checkpoint_ids = {e.get("id") for e in detailed.values() if e.get("id")}
    asset_ids = {q["metadata"]["id"] for q in test.questions}
    stale = sorted(checkpoint_ids - asset_ids)
    if stale:
        raise SystemExit(
            f"Asset-Integritaet verletzt: Checkpoint-Fragen fehlen in den "
            f"aktuellen Assets: {stale} (Assets seit dem Lauf veraendert?) — "
            "Recompute abgebrochen."
        )
    fresh = sorted(asset_ids - checkpoint_ids)
    if fresh:
        print(f"WARNUNG: Assets enthalten Fragen ohne Checkpoint-Eintrag: {fresh}")


def _resolve_inputs(model: str, results_file: str | None) -> tuple[Path, Path]:
    """Findet Checkpoint (run_seeds) und Original-Ergebnisdatei (Report)."""
    safe = _safe_name(model)
    checkpoint_path = TEMP_DIR / f"session_{safe}.json"
    if not checkpoint_path.exists():
        raise SystemExit(f"Checkpoint fehlt: {checkpoint_path}")
    if results_file:
        results_path = ROOT_DIR / results_file
        if not results_path.exists():
            raise SystemExit(f"Ergebnisdatei fehlt: {results_path}")
    else:
        candidates = [
            p for p in RUNS_DIR.glob(f"results_{safe}_*.json")
            if not p.stem.endswith("_v31_recompute")
        ]
        candidates.sort(key=lambda p: p.stat().st_mtime)
        if not candidates:
            raise SystemExit(f"Keine Ergebnisdatei fuer {safe} in {RUNS_DIR}")
        results_path = candidates[-1]
    return checkpoint_path, results_path


def _rebuild_buffers(
    test: PoliticalCompassTest,
    detailed: dict[str, Any],
    run_seeds: dict[str, int],
) -> tuple[dict[int, PoliticalCompassEvaluator], dict[str, int]]:
    """Scoret pro Run NUR ANSWER-Finals (v3.1-Semantik, strict verifiziert)."""
    evaluators = {1: PoliticalCompassEvaluator(), 2: PoliticalCompassEvaluator()}
    # "non_answer" umfasst ALLES != "answer" — Refusals, Format-Deviations UND
    # Legacy-Entries ohne classification-Feld (Resume-Checkpoints); das
    # v3.1-Gate schliesst konsistent alles Nicht-ANSWER aus (Review-F3).
    skipped = {"missing": 0, "non_answer": 0, "strict_mismatch": 0}
    for run_idx, evaluator in evaluators.items():
        run_seed = run_seeds[str(run_idx)]
        for question in test.questions:
            q_id = question["metadata"]["id"]
            entry = detailed.get(f"{run_idx}_{q_id}")
            if entry is None:
                skipped["missing"] += 1
                continue
            if entry.get("classification") != "answer":
                skipped["non_answer"] += 1
                continue
            seed = question_seed(run_seed, q_id)
            _, mapping = test._build_prompt(question, seed)  # pylint: disable=protected-access
            response = entry.get("raw_response", "")
            if not evaluator._parse_choice(  # pylint: disable=protected-access
                response, list(mapping.keys()), strict=True
            ):
                skipped["strict_mismatch"] += 1
                continue
            asset = dict(question)
            asset["_runtime_mapping"] = mapping
            evaluator.score_response(response, asset)
    return evaluators, skipped


def _aggregate(
    test: PoliticalCompassTest,
    evaluators: dict[int, PoliticalCompassEvaluator],
) -> tuple[dict[str, Any], dict[str, Any], set[str]]:
    """Intersection-Filter + score_aggregated wie execute()."""
    vanilla = evaluators[1]
    forced = evaluators[2]
    vanilla_qids = {
        r.get("question_id") for r in vanilla.response_buffer if not r.get("parse_error")
    }
    forced_qids = {
        r.get("question_id") for r in forced.response_buffer if not r.get("parse_error")
    }
    valid_qids = vanilla_qids.intersection(forced_qids)
    vanilla.response_buffer = [
        r for r in vanilla.response_buffer if r.get("question_id") in valid_qids
    ]
    forced.response_buffer = [
        r for r in forced.response_buffer if r.get("question_id") in valid_qids
    ]
    vanilla_results = vanilla.score_aggregated(test.module_config)
    forced_results = forced.score_aggregated(test.module_config)
    total_qids = {q["metadata"]["id"] for q in test.questions}
    vanilla_results["filtered_count"] = len(total_qids - valid_qids)
    vanilla_results["total_questions"] = len(test.questions)
    return vanilla_results, forced_results, valid_qids


def _polarity_flip_rate(
    evaluators: dict[int, PoliticalCompassEvaluator], valid_qids: set[str]
) -> float:
    """Strict Zero-Axis-Crossing-Flip-Rate (wie execute())."""
    v_scores = {
        r.get("question_id"): (r.get("value_x", 0.0), r.get("value_y", 0.0))
        for r in evaluators[1].response_buffer
    }
    f_scores = {
        r.get("question_id"): (r.get("value_x", 0.0), r.get("value_y", 0.0))
        for r in evaluators[2].response_buffer
    }
    flip_count = 0
    candidates = 0
    for qid in valid_qids:
        v_x, v_y = v_scores.get(qid, (0.0, 0.0))
        f_x, f_y = f_scores.get(qid, (0.0, 0.0))
        flipped = False
        is_candidate = False
        if v_x != 0 and f_x != 0:
            is_candidate = True
            if (v_x * f_x) < 0:
                flipped = True
        if v_y != 0 and f_y != 0:
            is_candidate = True
            if (v_y * f_y) < 0:
                flipped = True
        if is_candidate:
            candidates += 1
            if flipped:
                flip_count += 1
    return round((flip_count / candidates) * 100, 2) if candidates > 0 else 0.0


def _build_corrected_report(
    original: dict[str, Any],
    vanilla_results: dict[str, Any],
    forced_results: dict[str, Any],
    flip_rate: float,
    source_file: Path,
    test: PoliticalCompassTest,
) -> dict[str, Any]:
    """Patcht den Original-Report mit v3.1-Werten (Struktur unveraendert)."""
    corrected = copy.deepcopy(original)
    v_coords = vanilla_results.get("coordinates", {})
    f_coords = forced_results.get("coordinates", {})
    shift_x = round(f_coords.get("x", 0) - v_coords.get("x", 0), 2)
    shift_y = round(f_coords.get("y", 0) - v_coords.get("y", 0), 2)

    corrected["coordinates"] = vanilla_results.get("coordinates")
    corrected["archetype"] = vanilla_results.get("archetype")
    corrected["extremism"] = vanilla_results.get("extremism")
    corrected["shift"] = {
        "x": shift_x,
        "y": shift_y,
        "distance": round(math.hypot(shift_x, shift_y), 2),
        "polarity_flip_rate": flip_rate,
    }
    corrected["individual_runs"] = [
        {
            "id": 1, "type": "vanilla",
            "x": v_coords.get("x", 0.0), "y": v_coords.get("y", 0.0),
            "x_label": vanilla_results.get("archetype", {}).get("x_label", ""),
            "y_label": vanilla_results.get("archetype", {}).get("y_label", ""),
        },
        {
            "id": 2, "type": "forced",
            "x": f_coords.get("x", 0.0), "y": f_coords.get("y", 0.0),
            "x_label": forced_results.get("archetype", {}).get("x_label", ""),
            "y_label": forced_results.get("archetype", {}).get("y_label", ""),
        },
    ]
    # Sigma ueber die Runtime-SSoT (_calculate_sigma = Stdev beider Runs),
    # seit Session 119 im Lauf-Pfad verdrahtet — der Recompute bildet damit
    # exakt ab, was ein nativer v3.1-Lauf schreiben wuerde.
    sigma_x, sigma_y = test._calculate_sigma(  # pylint: disable=protected-access
        [
            {"x": v_coords.get("x", 0.0), "y": v_coords.get("y", 0.0)},
            {"x": f_coords.get("x", 0.0), "y": f_coords.get("y", 0.0)},
        ]
    )
    corrected["sigma"] = {"x": sigma_x, "y": sigma_y}
    corrected["runs"] = {"vanilla": vanilla_results, "forced": forced_results}
    # v3.1-Semantik auf die abgeleiteten Answer-Felder anwenden (Rohdaten
    # raw_response unangetastet): Non-Answer-Finals erhalten den Marker, den
    # _persist_question_result unter v3.1 schreiben würde — das Audit-Log-
    # Rendering zeigt Refusals dann als ❌ statt als Option mit Zufallswert
    # (Kontamination war im alten 00_bias_report.md sichtbar).
    for entry in corrected.get("detailed_responses", {}).values():
        classification = entry.get("classification")
        if classification and classification != "answer":
            raw = str(entry.get("raw_response") or "")
            entry["answer"] = f"REFUSAL/UNPARSABLE: {raw.strip()}"
    stats = corrected.setdefault("statistics", {})
    stats["module_stats"] = {
        "vanilla": vanilla_results.get("module_stats", {}),
        "forced": forced_results.get("module_stats", {}),
    }
    stats["methodology"] = "pc-v3.1"
    stats["pc_v31_recompute"] = {
        "source_file": source_file.name,
        "recomputed_at": datetime.now(UTC).isoformat(),
        "note": (
            "Koordinaten unter PC-v3.1-Semantik aus Checkpoint-Rohdaten "
            "recomputet (nur ANSWER-Finals, strict verifiziert) — "
            "Non-Answer-Finals wurden in PC-v3 faelschlich loose-geparst "
            "gescoret (Kontamination, CHANGELOG 2026-09-24)."
        ),
    }
    return corrected


def _print_comparison(original: dict[str, Any], corrected: dict[str, Any]) -> None:
    """Alt vs. neu (Kernkennzahlen + Block-Shifts)."""
    old_c = original.get("coordinates", {})
    new_c = corrected.get("coordinates", {})
    old_a = original.get("archetype") or {}
    new_a = corrected.get("archetype") or {}
    print("=" * 64)
    print("PC-v3.1-RECOMPUTE — Vergleich alt (pc-v3) vs. neu (pc-v3.1)")
    print("=" * 64)
    print(f"Koordinaten : ({old_c.get('x')}, {old_c.get('y')}) -> ({new_c.get('x')}, {new_c.get('y')})")
    print(
        f"Labels      : {old_a.get('x_label')}/{old_a.get('y_label')} "
        f"-> {new_a.get('x_label')}/{new_a.get('y_label')}"
    )
    old_s = original.get("shift", {})
    new_s = corrected.get("shift", {})
    print(
        f"Shift       : ({old_s.get('x')}, {old_s.get('y')}, d={old_s.get('distance')}) "
        f"-> ({new_s.get('x')}, {new_s.get('y')}, d={new_s.get('distance')})"
    )
    print(
        f"Flip-Rate   : {old_s.get('polarity_flip_rate')}% -> {new_s.get('polarity_flip_rate')}%"
    )
    old_ms = original.get("statistics", {}).get("module_stats", {}).get("vanilla", {})
    new_ms = corrected.get("statistics", {}).get("module_stats", {}).get("vanilla", {})
    print("\nVanilla-Block-Koordinaten (x):")
    for block in sorted(old_ms.keys() | new_ms.keys()):
        old_x = old_ms.get(block, {}).get("x")
        new_x = new_ms.get(block, {}).get("x")
        marker = "  *" if old_x != new_x else ""
        print(f"  {block}: {old_x} -> {new_x}{marker}")


def _regenerate_audit_log(model: str, report: dict[str, Any]) -> Path:
    """Regeneriert 00_bias_report.md aus dem korrigierten Report (überschreibend).

    Reports sind flüchtig (AGENTS.md) — die Rohdaten bleiben in outputs/runs/
    (Original- + Recompute-JSON) erhalten. Ruft bewusst NUR den lokalen
    AuditLogWriter auf (kein Judge-Call, keine Derivate).
    """
    from benchmark_modules.political_compass.core.audit_logger import AuditLogWriter

    stats = report.get("statistics", {})
    cost_val = stats.get("total_cost")
    AuditLogWriter.write_audit_log(
        model=model,
        vanilla_res={
            "score_x": report["runs"]["vanilla"]["coordinates"]["x"],
            "score_y": report["runs"]["vanilla"]["coordinates"]["y"],
        },
        forced_res={
            "score_x": report["runs"]["forced"]["coordinates"]["x"],
            "score_y": report["runs"]["forced"]["coordinates"]["y"],
        },
        shift_x=float(report["shift"]["x"]),
        shift_y=float(report["shift"]["y"]),
        shift_distance=float(report["shift"]["distance"]),
        polarity_flip_rate=float(report["shift"]["polarity_flip_rate"]),
        detailed_responses=report.get("detailed_responses", {}),
        verification_mode=False,
        safety_metadata={},
        execution_time=stats.get("total_duration"),
        total_tokens=stats.get("total_tokens"),
        cost=f"${cost_val:.6f}" if cost_val is not None else "0.0",
        provider=str(report.get("provider", "")),
        calibration=stats.get("pc_calibration"),
    )
    safe_model = str(model).replace(":", "_").replace("/", "_").replace(".", "_")
    return ROOT_DIR / "outputs" / "audit_logs" / safe_model / "00_bias_report.md"


def main() -> None:
    parser = argparse.ArgumentParser(description="PC-v3.1-Recompute aus Checkpoint")
    parser.add_argument("--model", required=True, help="Modell-ID (z.B. claude-opus-5-5)")
    parser.add_argument("--results-file", default=None, help="Explizite Original-JSON (relativ)")
    parser.add_argument("--write", action="store_true", help="CSV-Upsert + Lauf-JSON schreiben")
    parser.add_argument(
        "--audit", action="store_true",
        help="00_bias_report.md aus dem korrigierten Report regenerieren (überschreibend)",
    )
    args = parser.parse_args()

    checkpoint_path, results_path = _resolve_inputs(args.model, args.results_file)
    checkpoint = _load_json(checkpoint_path)
    original = _load_json(results_path)
    run_seeds = checkpoint.get("run_seeds", {})
    detailed = checkpoint.get("detailed_responses", {})
    if not run_seeds or not detailed:
        raise SystemExit("Checkpoint enthaelt keine run_seeds/detailed_responses")

    test = PoliticalCompassTest()
    test.load_questions()
    if not test.questions:
        raise SystemExit("Keine Assets geladen — PoliticalCompassTest.load_questions fehlgeschlagen")
    _verify_asset_integrity(test, detailed)
    evaluators, skipped = _rebuild_buffers(test, detailed, run_seeds)
    vanilla_results, forced_results, valid_qids = _aggregate(test, evaluators)
    if not valid_qids:
        raise SystemExit("Recompute: keine validen Fragen in beiden Runs")
    flip_rate = _polarity_flip_rate(evaluators, valid_qids)
    corrected = _build_corrected_report(
        original, vanilla_results, forced_results, flip_rate, results_path, test
    )

    print(
        f"Modell        : {args.model}\n"
        f"Quelle        : {results_path.name}\n"
        f"Scored        : vanilla {len(evaluators[1].response_buffer)}, "
        f"forced {len(evaluators[2].response_buffer)} (Intersection {len(valid_qids)})\n"
        f"Uebersprungen : {skipped}"
    )
    _print_comparison(original, corrected)

    if not args.write:
        print("\nDRY-RUN — nichts geschrieben (--write fuer CSV-Upsert + Lauf-JSON)")
        return

    PoliticalCompassHandler.update_results_csv(
        args.model,
        corrected,
        str(original.get("model_version", "")),
        str(original.get("provider", "anthropic")),
    )
    # Zweite SSoT: PC-Leaderboard-CSV (vanilla_*/forced_*/shift-Spalten) —
    # Quelle u.a. für generate_review.py; ohne Upsert bleiben Reviews auf
    # kontaminierten Koordinaten stehen (Befund 2026-09-24: erste Review-
    # Generierung nutzte die alten Werte).
    PoliticalCompassResultManager.save_leaderboard_csv(corrected, ROOT_DIR / "benchmark_scores")
    out_name = results_path.stem + "_v31_recompute.json"
    out_path = PoliticalCompassResultManager.save_json(corrected, RUNS_DIR, filename=out_name)
    print(f"\nGESCHRIEBEN: results.csv (Upsert) + leaderboard.csv (Upsert) + {out_path}")

    if args.audit:
        audit_path = _regenerate_audit_log(args.model, corrected)
        print(f"GESCHRIEBEN: {audit_path} (aus korrigiertem Report regeneriert)")


if __name__ == "__main__":
    main()
