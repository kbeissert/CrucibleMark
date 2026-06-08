#!/usr/bin/env python3
"""Political Compass Benchmark Worker.

Dedicated worker for political_compass execution with a stable orchestrator
contract. Supports single model, explicit model list, and all models.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.core.model_discovery import discover_models  # noqa: E402
from scripts.core.runner_contract import write_run_summary, update_leaderboard  # noqa: E402
from utils.config_validator import ConfigValidator  # noqa: E402


def _run_single_model(model_id: str, force: bool, silent: bool) -> bool:
    cmd = [
        sys.executable,
        "run_benchmark.py",
        "--module",
        "political_compass",
        "--model",
        model_id,
    ]
    if force:
        cmd.append("--force")
    if silent:
        cmd.append("--silent")

    # Prevent run_benchmark.py from delegating back to this worker (cycle guard).
    env = dict(os.environ)
    env["CRUCIBLE_DELEGATE_PARENT"] = "1"

    result = subprocess.run(cmd, cwd=str(ROOT_DIR), env=env, check=False)
    return result.returncode == 0


def _run_batch(model_ids: list[str], force: bool, silent: bool) -> tuple[list[str], list[str]]:
    success: list[str] = []
    failed: list[str] = []

    total = len(model_ids)
    for idx, model_id in enumerate(model_ids, 1):
        print(f"\n[{idx}/{total}] Political Compass: {model_id}")
        if _run_single_model(model_id, force=force, silent=silent):
            success.append(model_id)
        else:
            failed.append(model_id)

    return success, failed


def main() -> None:
    parser = argparse.ArgumentParser(description="Political Compass Benchmark Worker")
    parser.add_argument("--model", type=str, help="Ein einzelnes Modell ausführen")
    parser.add_argument("--models", type=str, help="Kommagetrennte Modellliste")
    parser.add_argument("--all", action="store_true", help="Alle Modelle ausführen")
    parser.add_argument(
        "--provider",
        default="all",
        choices=["all", "local", "commercial"],
        help="Modellscope für Batch-Läufe",
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

    try:
        if args.model:
            ok = _run_single_model(args.model, force=args.force, silent=args.silent)
            update_leaderboard(ROOT_DIR)
            write_run_summary(
                args.summary_json,
                {
                    "runner": "political_compass",
                    "status": "success" if ok else "failed",
                    "mode": "single",
                    "models_total": 1,
                    "models_successful": 1 if ok else 0,
                    "models_failed": 0 if ok else 1,
                    "failed_model_ids": [] if ok else [args.model],
                },
            )
            sys.exit(0 if ok else 1)

        if args.models:
            model_ids = [m.strip() for m in args.models.split(",") if m.strip()]
            if not model_ids:
                write_run_summary(
                    args.summary_json,
                    {
                        "runner": "political_compass",
                        "status": "failed",
                        "mode": "models",
                        "models_total": 0,
                        "models_successful": 0,
                        "models_failed": 0,
                        "failed_model_ids": [],
                        "message": "Leere Modellliste über --models",
                    },
                )
                print("Keine Modelle in --models angegeben.")
                sys.exit(1)

            success, failed = _run_batch(model_ids, force=args.force, silent=args.silent)
            update_leaderboard(ROOT_DIR)
            write_run_summary(
                args.summary_json,
                {
                    "runner": "political_compass",
                    "status": "success" if not failed else "partial",
                    "mode": "models",
                    "models_total": len(model_ids),
                    "models_successful": len(success),
                    "models_failed": len(failed),
                    "failed_model_ids": failed,
                },
            )
            sys.exit(0 if not failed else 1)

        if args.all or args.provider != "all":
            model_ids = discover_models(args.provider, config)
            if not model_ids:
                write_run_summary(
                    args.summary_json,
                    {
                        "runner": "political_compass",
                        "status": "success",
                        "mode": "all" if args.all else "provider",
                        "models_total": 0,
                        "models_successful": 0,
                        "models_failed": 0,
                        "failed_model_ids": [],
                        "message": f"Keine Modelle gefunden (provider={args.provider})",
                    },
                )
                print(f"Keine Modelle gefunden (provider={args.provider}).")
                sys.exit(0)

            success, failed = _run_batch(model_ids, force=args.force, silent=args.silent)
            update_leaderboard(ROOT_DIR)
            write_run_summary(
                args.summary_json,
                {
                    "runner": "political_compass",
                    "status": "success" if not failed else "partial",
                    "mode": "all" if args.all else "provider",
                    "models_total": len(model_ids),
                    "models_successful": len(success),
                    "models_failed": len(failed),
                    "failed_model_ids": failed,
                },
            )
            sys.exit(0 if not failed else 1)

        # Compatibility fallback: preserve legacy interactive behavior.
        cmd = [sys.executable, "run_benchmark.py", "--module", "political_compass"]
        if args.force:
            cmd.append("--force")
        if args.silent:
            cmd.append("--silent")

        env = dict(os.environ)
        env["CRUCIBLE_DELEGATE_PARENT"] = "1"

        result = subprocess.run(cmd, cwd=str(ROOT_DIR), env=env, check=False)
        update_leaderboard(ROOT_DIR)
        write_run_summary(
            args.summary_json,
            {
                "runner": "political_compass",
                "status": "success" if result.returncode == 0 else "failed",
                "mode": "wizard",
            },
        )
        sys.exit(result.returncode)

    except KeyboardInterrupt:
        write_run_summary(
            args.summary_json,
            {
                "runner": "political_compass",
                "status": "aborted",
                "mode": "unknown",
            },
        )
        print("\n\nPolitical Compass Benchmark abgebrochen.")
        sys.exit(130)


if __name__ == "__main__":
    main()
