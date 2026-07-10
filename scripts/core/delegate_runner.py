"""Generischer Subprozess-Wrapper für ToolUse/PC/Score-Delegation in benchmark_auto.

Stellt wiederverwendbare Wrapper um ``subprocess.run`` für die drei
Delegations-Pfade bereit, die ``benchmark_auto.py`` historisch inline
ausgeführt hat:

1. ``run_delegate_for_model`` — für Module mit ``delegate_script``-Key
2. ``run_score_delegate_for_model`` — für Score-Module
3. ``dispatch_tooluse_subprocess`` — für die Tool-Use-Backlog-Phase

Allen gemeinsam:
- ``summary-json``-Pfad-Konvention: ``outputs/runs/dispatch_summaries/``
- Aufruf von ``read_json_summary`` nach ``subprocess.run``
- Konsistente Print-Statusmeldungen
"""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# utils ohne scripts-Abhängigkeit → top-level Import ok.
from utils.model_utils import normalize_model_id  # noqa: E402

logger = logging.getLogger(__name__)


def read_json_summary(summary_path: Path, context_label: str) -> dict[str, Any] | None:
    """Lädt ein dispatch-summary-JSON. Loggt Warning bei Parse-Fehler."""
    if not summary_path.exists():
        return None
    try:
        return json.loads(summary_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.warning("%s konnte nicht gelesen werden: %s", context_label, summary_path)
        return None


def run_delegate_for_model(
    module: dict[str, Any],
    model: str,
    force: bool = False,
    audit: bool = True,
    mcp_mode: str = "live",
    skip_llamacpp_cleanup: bool = False,
) -> bool:
    """Delegiert die Ausführung eines Moduls an das zuständige Fachscript.

    Das Fachscript verantwortet seinen eigenen Lifecycle (inkl. MCP falls nötig).
    Returns True wenn der Prozess erfolgreich beendet wurde (rc == 0).
    """
    # Deferred Import: ROOT_DIR liegt in benchmark_auto; Tests patchen es dort.
    from scripts.core.benchmark_auto import ROOT_DIR

    script = ROOT_DIR / module["delegate_script"]
    extra = list(module.get("delegate_extra_args", []) or [])
    cmd = [sys.executable, str(script)] + extra + ["--model", model]

    safe_model = normalize_model_id(model).replace("/", "_").replace(":", "_")
    summary_dir = ROOT_DIR / "outputs" / "runs" / "dispatch_summaries"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_path = summary_dir / f"{module.get('key', 'module')}_{safe_model}.json"
    cmd += ["--summary-json", str(summary_path)]

    if force:
        cmd.append("--force")
    if not audit:
        cmd.append("--silent")
    if module.get("requires_mcp"):
        cmd += ["--mcp-mode", mcp_mode]

    env = os.environ.copy()
    if skip_llamacpp_cleanup:
        env["CRUCIBLE_SKIP_LLAMACPP_CLEANUP"] = "1"

    result = subprocess.run(cmd, cwd=str(ROOT_DIR), env=env, check=False)

    summary = read_json_summary(summary_path, "Delegate-Summary")
    if summary:
        status = summary.get("status", "unknown")
        mode = summary.get("mode", "unknown")
        print(
            f"   ℹ️ Delegate-Summary: module={module.get('key')} "
            f"model={model} status={status} mode={mode}"
        )
    return result.returncode == 0


def run_score_delegate_for_model(
    module: dict[str, Any],
    model: str,
    force: bool = False,
    audit: bool = True,
) -> bool:
    """Delegiert ein Score-Modul an scripts/run_score_benchmark.py für genau 1 Modell."""
    from scripts.core.benchmark_auto import ROOT_DIR

    module_key = module.get("key")
    if not module_key:
        logger.warning("Score-Delegation ohne module.key möglich: %s", module)
        return False

    script = ROOT_DIR / "scripts" / "run_score_benchmark.py"
    if not script.exists():
        print("   ⚠️  scripts/run_score_benchmark.py nicht gefunden — überspringe.")
        return False

    cmd = [
        sys.executable,
        str(script),
        "--model",
        model,
        "--modules",
        module_key,
    ]

    safe_model = normalize_model_id(model).replace("/", "_").replace(":", "_")
    summary_dir = ROOT_DIR / "outputs" / "runs" / "dispatch_summaries"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_path = summary_dir / f"score_{module_key}_{safe_model}.json"
    cmd += ["--summary-json", str(summary_path)]

    if force:
        cmd.append("--force")
    if not audit:
        cmd.append("--silent")

    result = subprocess.run(cmd, cwd=str(ROOT_DIR), check=False)

    summary = read_json_summary(summary_path, "Score-Delegate-Summary")
    if summary:
        status = summary.get("status", "unknown")
        mode = summary.get("mode", "unknown")
        print(
            f"   ℹ️ Score-Delegate-Summary: module={module_key} "
            f"model={model} status={status} mode={mode}"
        )
    return result.returncode == 0


def dispatch_tooluse_subprocess(
    *,
    script: Path,
    testable: list[tuple[str, str]],
    mcp_mode: str,
    force: bool,
    silent: bool,
) -> bool:
    """Baut den Subprocess-Cmd und ruft run_tooluse_benchmark.py auf."""
    from scripts.core.benchmark_auto import ROOT_DIR

    summary_dir = ROOT_DIR / "outputs" / "runs" / "dispatch_summaries"
    summary_dir.mkdir(parents=True, exist_ok=True)
    summary_path = summary_dir / "tooluse_backlog_dispatch.json"

    cmd = [
        sys.executable, str(script),
        "--models", ",".join(mid for mid, _ in testable),
        "--mcp-mode", mcp_mode,
        "--summary-json", str(summary_path),
    ]
    if force:
        cmd.append("--force")
    if silent:
        cmd.append("--silent")
    print(
        f"   → Delegiere {len(testable)} testbare Modell(e) an run_tooluse_benchmark.py "
        f"(MCP={mcp_mode}, force={force})"
    )
    try:
        result = subprocess.run(cmd, cwd=str(ROOT_DIR), check=False)
    except KeyboardInterrupt:
        print("⛔  Abbruch durch Benutzer (Tool-Use Backlog).")
        raise

    summary = read_json_summary(summary_path, "Tool-Use-Dispatch-Summary")
    if summary:
        print(
            "   ℹ️ Tool-Use-Dispatch-Summary: "
            f"status={summary.get('status', 'unknown')} "
            f"ok={summary.get('models_successful', '?')} "
            f"failed={summary.get('models_failed', '?')}"
        )
    return result.returncode == 0
