"""Pre/Post-Run-Hooks for benchmark_auto (Tool-Use-Backlog as Phase 0).

Phase 0 (pre-run, before _run_main_benchmark_phases):
    collect_untested_tooluse_cards
      -> filter_untested_with_caches (pre-flight + leaderboard cache)
      -> print_untested_summary
      -> write_unreachable_report
      -> dispatch_tooluse_subprocess (from delegate_runner)

CARD_DIR and ROOT_DIR are looked up via deferred import from benchmark_auto,
so tests can keep patching them via patch.object(benchmark_auto, ...).
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.model_utils import (
    SUPPORT_TOOL_USE_UNTESTED,
    normalize_supports_tool_use,
)

logger = logging.getLogger("auto_benchmark")


def _card_dir() -> Path:
    """Deferred lookup -- tests patch benchmark_auto.CARD_DIR."""
    from scripts.core.benchmark_auto import CARD_DIR
    return CARD_DIR

def collect_untested_tooluse_cards() -> list[tuple[str, str]]:
    """Load all model cards with supports_tool_use == 'untested'."""
    card_dir = _card_dir()
    untested: list[tuple[str, str]] = []
    if not card_dir.exists():
        return untested
    for card_path in sorted(card_dir.glob("*.json")):
        if card_path.name == "_index.json":
            continue
        try:
            card: dict[str, Any] = json.loads(card_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning("Model Card konnte nicht gelesen werden: %s", card_path)
            continue
        if not isinstance(card, dict):
            logger.warning("Model Card hat ungültiges Format (kein Objekt): %s", card_path)
            continue
        if normalize_supports_tool_use(card.get("supports_tool_use")) != SUPPORT_TOOL_USE_UNTESTED:
            continue
        model_id = card.get("model_id")
        if not model_id:
            logger.warning("Untested Card ohne model_id wird übersprungen: %s", card_path)
            continue
        if model_id == "test" and str(card.get("card_status", "")).lower() == "draft":
            logger.info("Überspringe Platzhalter-Card im Tool-Use-Backlog: %s", card_path)
            continue
        display_name = card.get("display_name") or model_id
        untested.append((model_id, display_name))
    return untested


def load_cards_for_models(model_ids: list[str]) -> dict[str, dict[str, Any]]:
    """Load card dicts for given model_ids from CARD_DIR (SSoT)."""
    card_dir = _card_dir()
    cards: dict[str, dict[str, Any]] = {}
    for mid in model_ids:
        candidates = [
            card_dir / f"{mid}.json",
            card_dir / f"{mid.replace(':', '_')}.json",
            card_dir / f"{mid.replace('/', '_').replace(':', '_')}.json",
            card_dir / f"{mid.replace('/', '_').replace(':', '_').replace('.', '_')}.json",
        ]
        loaded: dict[str, Any] = {}
        for path in candidates:
            if path.exists():
                try:
                    loaded = json.loads(path.read_text(encoding="utf-8"))
                    break
                except (json.JSONDecodeError, OSError) as exc:
                    logger.warning(
                        "Model Card für Pre-Flight konnte nicht gelesen werden "
                        "(model=%s, candidate=%s): %s",
                        mid,
                        path,
                        exc,
                    )
                    continue
        if loaded:
            cards[mid] = loaded
        else:
            logger.warning(
                "Keine lesbare Model Card für Pre-Flight gefunden (model=%s)",
                mid,
            )
    return cards


def write_unreachable_report(
    unreachable: list[tuple[str, str, str]],
    testable: list[tuple[str, str]],
    total: int,
) -> Path | None:
    """Write a report about unreachable untested cards."""
    from scripts.core.benchmark_auto import ROOT_DIR

    if not unreachable:
        return None
    report_dir = ROOT_DIR / "outputs"
    report_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = report_dir / f"tooluse_unreachable_{timestamp}.json"
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "total_untested": total,
            "testable": len(testable),
            "unreachable": len(unreachable),
        },
        "unreachable": [
            {"model_id": mid, "display_name": name, "reason": reason}
            for mid, name, reason in unreachable
        ],
    }
    try:
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError as exc:
        print(f"   ⚠️  Report-Datei konnte nicht geschrieben werden: {exc}")
        return None
    return report_path


def filter_untested_with_caches(
    models: list[tuple[str, str]],
    validator: Any | None,
    force: bool,
) -> tuple[list[tuple[str, str]], list[tuple[str, str, str]]]:
    """Pre-flight filter: testable cards + ToolUse leaderboard cache."""
    from scripts.core.benchmark_auto import filter_testable_cards

    model_ids = [mid for mid, _ in models]
    card_lookup = load_cards_for_models(model_ids)
    testable, unreachable = filter_testable_cards(models, card_lookup=card_lookup)

    if force or validator is None:
        return testable, unreachable

    try:
        from scripts.core.tooluse_exporter import ToolUseExporter
        exporter = ToolUseExporter(validator.config)
    except ImportError as exc:
        # Import-Fehler dürfen nicht still verschluckt werden — sonst laufen
        # Cache-Treffer unbeabsichtigt doppelt (Double-Runs im Leaderboard).
        print(
            f"   ⚠️  ToolUseExporter nicht importierbar ({exc}) — "
            "Leaderboard-Cache-Filter deaktiviert, alle testbaren Modelle laufen."
        )
        return testable, unreachable
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(
            f"   ⚠️  ToolUseExporter-Init fehlgeschlagen ({exc}) — "
            "Leaderboard-Cache-Filter deaktiviert, alle testbaren Modelle laufen."
        )
        return testable, unreachable

    filtered: list[tuple[str, str]] = []
    skipped_cached: list[tuple[str, str]] = []
    for mid, dname in testable:
        if exporter.model_has_results(mid):
            skipped_cached.append((mid, dname))
        else:
            filtered.append((mid, dname))
    if skipped_cached:
        print(
            f"   ⏩  {len(skipped_cached)} Modell(e) bereits im ToolUse-Leaderboard "
            "(Cache-Treffer, kein Re-Run):"
        )
        for mid, dname in skipped_cached:
            print(f"      • {dname}  ({mid})")
    return filtered, unreachable


def print_untested_summary(
    models: list[tuple[str, str]],
    testable: list[tuple[str, str]],
    unreachable: list[tuple[str, str, str]],
) -> None:
    """Backlog overview: total, testable, unreachable (with explanation)."""
    print(f"   📊 Tool-Use Backlog: {len(models)} untested Card(s) gefunden")
    for mid, dname in models:
        print(f"      • {dname}  ({mid})")
    if unreachable:
        print(f"   ⚠️  {len(unreachable)} untested Card(s) sind aktuell nicht testbar:")
        print("      Hinweis: 'ollama_model_not_installed:*' bedeutet: lokales Ollama-Modell wurde entfernt oder ist nicht mehr installiert.")
        print("      (Also nicht API/Netzwerk, sondern fehlendes lokales Modellartefakt.)")
        for mid, dname, reason in unreachable:
            print(f"      ✗ {dname}  ({mid})  →  {reason}")


def run_untested_tooluse_models(
    models: list[tuple[str, str]],
    validator: Any | None = None,
    mcp_mode: str = "live",
    force: bool = False,
    silent: bool = False,
) -> bool:
    """Delegate Tool-Use-Benchmarks for untested cards to run_tooluse_benchmark.py.

    Runs a pre-flight check before the subprocess:
        1. Card lookup per model_id
        2. validate_untested_card() verifies provider reachability
        3. Unreachable cards are logged to outputs/tooluse_unreachable_*.json
        4. Only testable cards are delegated to the subprocess

    Returns:
        True if run was started successfully. False for empty list,
        missing script, or subprocess error.
    """
    from scripts.core.benchmark_auto import ROOT_DIR
    from scripts.core.delegate_runner import dispatch_tooluse_subprocess

    if not models:
        return False
    script = ROOT_DIR / "scripts" / "run_tooluse_benchmark.py"
    if not script.exists():
        print("   ⚠️  scripts/run_tooluse_benchmark.py nicht gefunden — überspringe.")
        return False

    testable, unreachable = filter_untested_with_caches(
        models, validator, force,
    )
    print_untested_summary(models, testable, unreachable)

    if not testable:
        write_unreachable_report(unreachable, testable, len(models))
        return True

    report_path = write_unreachable_report(unreachable, testable, len(models))
    if report_path:
        print(f"   📝 Unreachables-Report: {report_path.relative_to(ROOT_DIR)}")

    return dispatch_tooluse_subprocess(
        script=script, testable=testable, mcp_mode=mcp_mode,
        force=force, silent=silent,
    )


def run_tooluse_backlog_phase(
    validator: Any,
    args: Any,
) -> bool:
    """Phase 0: Tool-Use-Backlog (untested cards). Returns True if aborted."""
    from scripts.core.llamacpp_batch import stop_llamacpp_provider_server

    untested_cards = collect_untested_tooluse_cards()
    if not untested_cards:
        print("\n🔧 [0/2] TOOL-USE BACKLOG: keine untested Cards — nichts zu tun.")
        return False

    print("\n🔧 [0/2] TOOL-USE BACKLOG (untested Cards)")
    print(f"{'=' * 40}")
    stop_llamacpp_provider_server(validator.config)
    aborted = False
    try:
        run_untested_tooluse_models(
            untested_cards,
            validator=validator,
            mcp_mode=args.mcp_mode,
            force=args.force,
            silent=not args.audit,
        )
    except KeyboardInterrupt:
        aborted = True
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"   ⚠️  Tool-Use-Backlog fehlgeschlagen (nicht fatal): {e}")
    return aborted
