#!/usr/bin/env python3
"""Score Benchmark Worker.

Dedicated worker for scoring modules (module 1-7) with a stable orchestrator
contract. Excludes political_compass and tooluse by design.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.core.model_discovery import discover_models  # noqa: E402
from scripts.core.runner_contract import write_run_summary  # noqa: E402
from utils.config_validator import ConfigValidator  # noqa: E402

EXCLUDED_MODULES = {"political_compass", "tooluse"}


def _get_score_modules(config: dict[str, Any], modules_arg: str | None) -> list[str]:
    if modules_arg:
        requested = [m.strip() for m in modules_arg.split(",") if m.strip()]
        return [m for m in requested if m not in EXCLUDED_MODULES]

    module_cfg = config.get("modules", {})
    score_modules: list[str] = []
    for key, entry in module_cfg.items():
        if key in EXCLUDED_MODULES:
            continue
        if isinstance(entry, dict) and entry.get("enabled", False):
            score_modules.append(key)
    return score_modules


def _run_module_for_model(model_id: str, module_key: str, force: bool, silent: bool) -> bool:
    cmd = [
        sys.executable,
        "run_benchmark.py",
        "--module",
        module_key,
        "--model",
        model_id,
    ]
    if force:
        cmd.append("--force")
    if silent:
        cmd.append("--silent")

    env = dict(os.environ)
    env["CRUCIBLE_DELEGATE_PARENT"] = "1"

    result = subprocess.run(cmd, cwd=str(ROOT_DIR), env=env, check=False)
    return result.returncode == 0


def _run_score_batch(
    model_ids: list[str],
    module_keys: list[str],
    force: bool,
    silent: bool,
) -> dict[str, Any]:
    failed_tasks: list[dict[str, str]] = []
    tasks_total = len(model_ids) * len(module_keys)
    tasks_successful = 0

    for midx, model_id in enumerate(model_ids, 1):
        print(f"\n=== Model {midx}/{len(model_ids)}: {model_id} ===")
        for module_key in module_keys:
            print(f"  -> Module: {module_key}")
            ok = _run_module_for_model(model_id, module_key, force=force, silent=silent)
            if ok:
                tasks_successful += 1
            else:
                failed_tasks.append({"model": model_id, "module": module_key})

    return {
        "models_total": len(model_ids),
        "modules_total": len(module_keys),
        "tasks_total": tasks_total,
        "tasks_successful": tasks_successful,
        "tasks_failed": len(failed_tasks),
        "failed_tasks": failed_tasks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Score Benchmark Worker")
    parser.add_argument("--model", type=str, help="Ein einzelnes Modell ausführen")
    parser.add_argument("--models", type=str, help="Kommagetrennte Modellliste")
    parser.add_argument("--all", action="store_true", help="Alle Modelle ausführen")
    parser.add_argument(
        "--provider",
        default="all",
        choices=["all", "local", "commercial"],
        help="Modellscope für Batch-Läufe",
    )
    parser.add_argument(
        "--modules",
        type=str,
        help="Kommagetrennte Modulkeys (Default: alle aktivierten Score-Module)",
    )
    parser.add_argument("--force", action="store_true", help="Cache ignorieren")
    parser.add_argument("--silent", action="store_true", help="Audit-Logs unterdrücken")
    parser.add_argument(
        "--summary-json",
        type=str,
        help="Optionaler Pfad für strukturiertes Run-Summary JSON (Orchestrator-Rückkanal).",
    )
    args = parser.parse_args()

    config = ConfigValidator().config
    module_keys = _get_score_modules(config, args.modules)

    if not module_keys:
        write_run_summary(
            args.summary_json,
            {
                "runner": "score_benchmark",
                "status": "failed",
                "mode": "unknown",
                "message": "Keine Score-Module verfügbar/ausgewählt",
            },
        )
        print("Keine Score-Module verfügbar/ausgewählt.")
        sys.exit(1)

    try:
        if args.model:
            summary = _run_score_batch([args.model], module_keys, force=args.force, silent=args.silent)
            status = "success" if summary["tasks_failed"] == 0 else "partial"
            write_run_summary(
                args.summary_json,
                {
                    "runner": "score_benchmark",
                    "status": status,
                    "mode": "single",
                    **summary,
                },
            )
            sys.exit(0 if summary["tasks_failed"] == 0 else 1)

        if args.models:
            model_ids = [m.strip() for m in args.models.split(",") if m.strip()]
            if not model_ids:
                write_run_summary(
                    args.summary_json,
                    {
                        "runner": "score_benchmark",
                        "status": "failed",
                        "mode": "models",
                        "message": "Leere Modellliste über --models",
                    },
                )
                print("Keine Modelle in --models angegeben.")
                sys.exit(1)

            summary = _run_score_batch(model_ids, module_keys, force=args.force, silent=args.silent)
            status = "success" if summary["tasks_failed"] == 0 else "partial"
            write_run_summary(
                args.summary_json,
                {
                    "runner": "score_benchmark",
                    "status": status,
                    "mode": "models",
                    **summary,
                },
            )
            sys.exit(0 if summary["tasks_failed"] == 0 else 1)

        if args.all or args.provider != "all":
            model_ids = discover_models(args.provider, config)
            if not model_ids:
                write_run_summary(
                    args.summary_json,
                    {
                        "runner": "score_benchmark",
                        "status": "success",
                        "mode": "all" if args.all else "provider",
                        "models_total": 0,
                        "modules_total": len(module_keys),
                        "tasks_total": 0,
                        "tasks_successful": 0,
                        "tasks_failed": 0,
                        "failed_tasks": [],
                        "message": f"Keine Modelle gefunden (provider={args.provider})",
                    },
                )
                print(f"Keine Modelle gefunden (provider={args.provider}).")
                sys.exit(0)

            summary = _run_score_batch(model_ids, module_keys, force=args.force, silent=args.silent)
            status = "success" if summary["tasks_failed"] == 0 else "partial"
            write_run_summary(
                args.summary_json,
                {
                    "runner": "score_benchmark",
                    "status": status,
                    "mode": "all" if args.all else "provider",
                    **summary,
                },
            )
            sys.exit(0 if summary["tasks_failed"] == 0 else 1)

        # Compatibility fallback: preserve legacy interactive behavior.
        cmd = [sys.executable, "run_benchmark.py"]
        if args.modules and "," not in args.modules:
            cmd += ["--module", args.modules]
        if args.force:
            cmd.append("--force")
        if args.silent:
            cmd.append("--silent")

        env = dict(os.environ)
        env["CRUCIBLE_DELEGATE_PARENT"] = "1"

        result = subprocess.run(cmd, cwd=str(ROOT_DIR), env=env, check=False)
        write_run_summary(
            args.summary_json,
            {
                "runner": "score_benchmark",
                "status": "success" if result.returncode == 0 else "failed",
                "mode": "wizard",
                "modules_total": len(module_keys),
            },
        )
        sys.exit(result.returncode)

    except KeyboardInterrupt:
        write_run_summary(
            args.summary_json,
            {
                "runner": "score_benchmark",
                "status": "aborted",
                "mode": "unknown",
            },
        )
        print("\n\nScore Benchmark abgebrochen.")
        sys.exit(130)


if __name__ == "__main__":
    main()
