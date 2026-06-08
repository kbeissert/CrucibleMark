"""Tool Use Benchmark Runner — CrucibleMark
=========================================
Interactive wizard (no flags) oder direkte Ausführung (Flags).

Modi:
  make benchmark-tooluse              → Wizard: Provider + Modell/Alle wählen
  make benchmark-tooluse MODEL=x      → Einzelnes Modell direkt
  make benchmark-tooluse PROVIDER=ollama → Batch alle Ollama-Modelle
  make benchmark-tooluse ALL=1        → Batch alle Provider
"""

from __future__ import annotations

import argparse
import atexit
import json
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

import yaml  # noqa: E402

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.core.tooluse_exporter import ToolUseExporter  # noqa: E402
from scripts.core.runner_contract import write_run_summary  # noqa: E402
from utils.config_validator import ConfigValidator  # noqa: E402

CARD_DIR = _ROOT / "benchmark_scores" / "model_cards"
_MCP_HEALTH_URL = "http://localhost:8765/health"


def _load_tooluse_timeouts() -> dict[str, float]:
    """Lädt Timeouts aus config/tooluse_report_config.yaml."""
    config_path = _ROOT / "config" / "tooluse_report_config.yaml"
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        return dict(data.get("report", {}).get("timeouts", {}))
    except Exception:  # noqa: BLE001
        return {}


_TIMEOUTS = _load_tooluse_timeouts()
TIMEOUT_PER_MODEL = int(_TIMEOUTS.get("per_model", 600))
INACTIVITY_TIMEOUT = int(_TIMEOUTS.get("inactivity", 180))
_MCP_HEALTH_TIMEOUT = float(_TIMEOUTS.get("mcp_health", 0.5))
_MCP_STARTUP_TIMEOUT = float(_TIMEOUTS.get("mcp_startup", 8.0))
_MCP_STARTUP_RETRY_TIMEOUT = float(_TIMEOUTS.get("mcp_startup_retry", 5.0))
_MCP_SHUTDOWN_TIMEOUT = float(_TIMEOUTS.get("mcp_shutdown", 3.0))

_SEP = "═" * 54
_SEP_THIN = "─" * 54
_mcp_managed: list[bool] = [False]  # True wenn dieser Prozess den Server gestartet hat


# ---------------------------------------------------------------------------
# MCP lifecycle
# ---------------------------------------------------------------------------

def _mcp_is_up() -> bool:
    """True if MCP health endpoint responds within configured timeout."""
    try:
        urllib.request.urlopen(_MCP_HEALTH_URL, timeout=_MCP_HEALTH_TIMEOUT)
        return True
    except Exception:
        return False


def _wait_mcp_down(timeout: float | None = None) -> None:
    """Block until port 8765 stops responding, then force-kill if needed."""
    timeout = timeout if timeout is not None else _MCP_SHUTDOWN_TIMEOUT
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not _mcp_is_up():
            return
        time.sleep(0.2)
    # Still up after timeout — force kill
    subprocess.run(
        ["pkill", "-9", "-f", "cruciblemark-mcp/server.py"],
        check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(0.3)


def _wait_mcp_up(timeout: float | None = None) -> bool:
    """Poll until server is ready. Returns True on success."""
    timeout = timeout if timeout is not None else _MCP_STARTUP_TIMEOUT
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _mcp_is_up():
            return True
        time.sleep(0.3)
    return False


def _restart_mcp(mode: str = "live") -> None:
    """Stop current MCP server and start a fresh one with verified readiness."""
    subprocess.run(
        ["make", "mcp-stop"],
        cwd=str(_ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )
    _wait_mcp_down()  # ensure port is free before starting new server
    subprocess.run(
        ["make", "mcp-start", f"MODE={mode}"],
        cwd=str(_ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )
    if not _wait_mcp_up():
        # Retry once
        subprocess.run(
            ["make", "mcp-start", f"MODE={mode}"],
            cwd=str(_ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        )
        if not _wait_mcp_up(timeout=_MCP_STARTUP_RETRY_TIMEOUT):
            print("  [WARN] MCP server did not start after restart")


def _start_mcp_for_run(mode: str) -> None:
    """Startet den MCP-Server für diesen Benchmark-Run.

    Falls der Server bereits läuft (manuell gestartet), wird er nicht angefasst
    und _mcp_managed bleibt False (kein Auto-Stop am Ende).
    """
    if _mcp_is_up():
        print(f"  MCP Server läuft bereits — bestehende Instanz wird genutzt (mode={mode})")
        return
    print(f"  Starte MCP Server (mode={mode})...")
    _restart_mcp(mode)
    if _mcp_is_up():
        _mcp_managed[0] = True
        print("  MCP Server bereit.")
    else:
        print("  [WARN] MCP Server konnte nicht gestartet werden — Benchmark läuft trotzdem.")


def _stop_mcp_if_managed() -> None:
    """Beendet den MCP-Server, falls dieser Prozess ihn gestartet hat."""
    if not _mcp_managed[0]:
        return
    _mcp_managed[0] = False  # Idempotenz: verhindert Doppel-Stop
    try:
        subprocess.run(
            ["make", "mcp-stop"],
            cwd=str(_ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        )
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# Card loading + provider classification
# ---------------------------------------------------------------------------

def _classify_provider(model_id: str) -> str:
    from utils.model_utils import (
        resolve_provider,  # pylint: disable=import-outside-toplevel
    )
    try:
        provider_key, _ = resolve_provider(model_id)
        return provider_key
    except Exception:  # noqa: BLE001 — pylint: disable=broad-exception-caught
        if ":" in model_id or model_id.startswith("hf.co/"):
            return "ollama"
        return "unknown"


def _load_all_tool_use_cards() -> list[tuple[str, str, str]]:
    """(model_id, display_name, provider) für alle Cards mit supports_tool_use: true."""
    results = []
    for card_path in sorted(CARD_DIR.glob("*.json")):
        try:
            card: dict[str, Any] = json.loads(card_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(card, dict):
            continue
        if not card.get("supports_tool_use"):
            continue
        model_id = card.get("model_id", "")
        if not model_id:
            continue
        display_name = card.get("display_name") or model_id
        provider = _classify_provider(model_id)
        results.append((model_id, display_name, provider))
    return results


def get_tool_use_models(provider_filter: str = "all") -> list[tuple[str, str]]:
    """Gibt (model_id, display_name) gefiltert nach Provider zurück."""
    all_cards = _load_all_tool_use_cards()
    if provider_filter == "all":
        return [(mid, dname) for mid, dname, _ in all_cards]
    wanted = {p.strip().lower() for p in provider_filter.split(",")}
    return [(mid, dname) for mid, dname, prov in all_cards if prov in wanted]


# ---------------------------------------------------------------------------
# Single-model execution
# ---------------------------------------------------------------------------

def _run_model(model_id: str, force: bool = False, silent: bool = False) -> bool:
    """Führt run_benchmark.py --module tooluse --model <id> aus. True = Erfolg.

    Watchdog: kills process group if no stdout for INACTIVITY_TIMEOUT seconds.
    Hard cap: kills after TIMEOUT_PER_MODEL seconds regardless.
    
    Prüft vor Ausführung ob das Modell bereits im ToolUse-Leaderboard existiert
    (außer bei force=True).
    """
    # SSoT: Kanonische model_id resolven, damit der Cache-Check auf die
    # gleiche Schreibweise wie im Leaderboard matcht (qwen3.5-… → qwen3_5-…).
    from utils.model_utils import resolve_canonical_model_id
    canonical_id = resolve_canonical_model_id(model_id)
    if canonical_id != model_id:
        print(f"  [SSoT] model_id kanonisiert: '{model_id}' → '{canonical_id}'")
        model_id = canonical_id

    # Cache-Check: Überspringe wenn Modell bereits im ToolUse-Leaderboard
    if not force:
        try:
            from scripts.core.tooluse_exporter import ToolUseExporter
            from utils.config_validator import ConfigValidator
            config = ConfigValidator().config
            exporter = ToolUseExporter(config)
            if exporter.model_has_results(model_id):
                print(f"  ⏩ Überspringe {model_id} — bereits im ToolUse-Leaderboard vorhanden")
                return True  # Als Erfolg werten, da Ergebnis bereits existiert
        except Exception:
            # Bei Fehler im Cache-Check defensiv weitermachen (Benchmark ausführen)
            pass

    cmd = [sys.executable, "run_benchmark.py", "--module", "tooluse", "--model", model_id]
    if force:
        cmd.append("--force")
    if silent:
        cmd.append("--silent")

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"  [ERROR] failed to start process: {exc}")
        return False

    # ── Watchdog state ────────────────────────────────────────────────────────
    last_output_time: list[float] = [time.monotonic()]
    watchdog_triggered: list[bool] = [False]

    def _watchdog() -> None:
        while proc.poll() is None:
            time.sleep(5)
            elapsed = time.monotonic() - last_output_time[0]
            if elapsed >= INACTIVITY_TIMEOUT:
                watchdog_triggered[0] = True
                print(
                    f"  [WATCHDOG] no output for {elapsed:.0f}s — "
                    f"model appears hung, killing process group"
                )
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except Exception:
                    proc.kill()
                return

    wt = threading.Thread(target=_watchdog, daemon=True)
    wt.start()

    # ── Stream stdout to console ──────────────────────────────────────────────
    try:
        for line in proc.stdout:  # type: ignore[union-attr]
            last_output_time[0] = time.monotonic()
            print(line, end="", flush=True)
    except KeyboardInterrupt:
        # Ctrl+C: Subprocess läuft in eigenem Session → muss explizit beendet werden
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:  # noqa: BLE001
            proc.terminate()
        proc.wait()
        raise
    except Exception:  # noqa: BLE001
        pass

    # ── Wait for process exit (hard cap) ─────────────────────────────────────
    try:
        proc.wait(timeout=TIMEOUT_PER_MODEL)
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] exceeded {TIMEOUT_PER_MODEL}s — killing process group")
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:  # noqa: BLE001
            proc.kill()
        proc.wait()
        return False
    except KeyboardInterrupt:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:  # noqa: BLE001
            proc.kill()
        proc.wait()
        raise

    if watchdog_triggered[0]:
        return False

    if proc.returncode != 0:
        print(f"  [FAIL] exit code {proc.returncode}")
        return False

    return True


# ---------------------------------------------------------------------------
# Batch run
# ---------------------------------------------------------------------------

def _run_batch(
    models: list[tuple[str, str]],
    provider_label: str,
    force: bool,
    silent: bool,
    mcp_mode: str,
    restart_mcp: bool = True,
) -> dict[str, Any]:
    restart_note = "MCP-Neustart pro Modell" if restart_mcp else "kein MCP-Neustart"
    print(_SEP)
    print("  Tool Use Benchmark — Batch Run")
    print(f"  Provider: {provider_label}  |  MCP: {mcp_mode}  |  {restart_note}")
    print(f"  Modelle: {len(models)}")
    print(_SEP)

    success: list[str] = []
    failed: list[str] = []

    for i, (model_id, display_name) in enumerate(models, 1):
        # MCP health-gated restart: only restart if server is down or explicitly requested
        if restart_mcp:
            if not _mcp_is_up():
                print(f"\n  ↻ MCP nicht erreichbar — Neustart vor [{i}/{len(models)}]...")
                _restart_mcp(mcp_mode)
            # else: server is healthy, skip restart
        print(f"\n[{i}/{len(models)}] {display_name}")
        if _run_model(model_id, force=force, silent=silent):
            success.append(model_id)
        else:
            failed.append(model_id)

        # Mid-run leaderboard update (every 5 models or at end)
        if i % 5 == 0 or i == len(models):
            try:
                config = ConfigValidator().config
                exporter = ToolUseExporter(config)
                # Nur die bisher getesteten Modelle anzeigen
                tested_so_far = success + failed
                written = exporter.aggregate_from_benchmark_csvs(target_model_ids=tested_so_far)
                if written > 0:
                    print(f"  ↻ Leaderboard zwischenstand: {written} Modell(e) | {i}/{len(models)} abgeschlossen")
            except Exception:  # noqa: BLE001
                pass

    print(f"\n{_SEP}")
    print("  Tool Use Benchmark — Batch Run Complete")
    print(_SEP)
    print(f"  Models found (supports_tool_use): {len(models):>5}")
    print(f"  Provider filter:                  {provider_label}")
    print(f"  Successful:                       {len(success):>5}")
    print(f"  Failed/Skipped:                   {len(failed):>5}")
    if failed:
        print()
        print("  Failed models:")
        for m in failed:
            print(f"    - {m}")
    print(_SEP)
    print()

    # ToolUse-Leaderboard automatisch aktualisieren
    leaderboard_updated = False
    try:
        config = ConfigValidator().config
        exporter = ToolUseExporter(config)
        # Nur die tatsächlich getesteten Modelle anzeigen/aktualisieren
        tested_model_ids = success + failed
        written = exporter.aggregate_from_benchmark_csvs(target_model_ids=tested_model_ids)
        if written > 0:
            exporter.calculate_sovereignty_gap()
            print(f"  ToolUse-Leaderboard aktualisiert: {written} Modell(e) → tooluse_leaderboard.csv")
            leaderboard_updated = True
        else:
            print("  ToolUse-Leaderboard: keine Ergebnisse in Benchmark-CSVs gefunden.")
    except Exception as exc:  # noqa: BLE001 — leaderboard update must not crash CLI
        print(f"  [WARN] ToolUse-Leaderboard-Update fehlgeschlagen: {exc}")  # noqa: T201

    return {
        "models_total": len(models),
        "models_successful": len(success),
        "models_failed": len(failed),
        "failed_model_ids": failed,
        "leaderboard_updated": leaderboard_updated,
    }


# ---------------------------------------------------------------------------
# Interactive wizard
# ---------------------------------------------------------------------------

def _pick(prompt: str, max_val: int, default: int) -> int:
    raw = input(f"  {prompt} [{default}]: ").strip() or str(default)
    try:
        val = int(raw)
        return val if 1 <= val <= max_val else default
    except ValueError:
        return default


def _interactive_wizard(force: bool, silent: bool, mcp_mode: str, restart_mcp: bool = True) -> None:
    all_cards = _load_all_tool_use_cards()
    if not all_cards:
        print("Keine Modelle mit supports_tool_use: true in benchmark_scores/model_cards/")
        return

    # Group by provider
    by_provider: dict[str, list[tuple[str, str]]] = {}
    for model_id, display_name, provider in all_cards:
        by_provider.setdefault(provider, []).append((model_id, display_name))

    provider_list = sorted(by_provider.keys())

    # ── Step 1: Provider selection ──────────────────────────────────────────
    print()
    print(_SEP)
    print("  Tool Use Benchmark — Provider-Auswahl")
    print(_SEP)
    for i, p in enumerate(provider_list, 1):
        count = len(by_provider[p])
        print(f"  {i}) {p}  ({count} Modell{'e' if count != 1 else ''})")
    all_idx = len(provider_list) + 1
    all_count = len(all_cards)
    print(f"  {all_idx}) Alle Provider  ({all_count} Modelle)")
    print()

    prov_choice = _pick("Provider wählen", all_idx, all_idx)

    if 1 <= prov_choice <= len(provider_list):
        selected_provider = provider_list[prov_choice - 1]
        candidate_models = by_provider[selected_provider]
        provider_label = selected_provider
    else:
        selected_provider = "all"
        candidate_models = [(mid, dname) for mid, dname, _ in all_cards]
        provider_label = "all"

    # ── Step 2: Model selection ─────────────────────────────────────────────
    print()
    print(_SEP)
    print(f"  Modell-Auswahl  [{provider_label}]")
    print(_SEP)
    for i, (_, display_name) in enumerate(candidate_models, 1):
        print(f"  {i}) {display_name}")
    batch_idx = len(candidate_models) + 1
    print(f"  {batch_idx}) Alle ({len(candidate_models)} Modelle)")
    print()

    model_choice = _pick("Modell wählen", batch_idx, batch_idx)

    if 1 <= model_choice <= len(candidate_models):
        selected_model_id, selected_display = candidate_models[model_choice - 1]
        print(f"\n  Starte: {selected_display}")
        print(f"  MCP-Modus: {mcp_mode}")
        print()
        ok = _run_model(selected_model_id, force=force, silent=silent)
        status = "✅ Erfolgreich" if ok else "❌ Fehlgeschlagen"
        print(f"\n  {status}: {selected_display}")
    else:
        _run_batch(
            candidate_models,
            provider_label,
            force=force,
            silent=silent,
            mcp_mode=mcp_mode,
            restart_mcp=restart_mcp,
        )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Tool Use Benchmark Runner")
    parser.add_argument("--model", type=str, help="Einzelnes Modell direkt ausführen")
    parser.add_argument("--models", type=str, help="Komma-liste von Modell-IDs (z.B. model1,model2,model3)")
    parser.add_argument("--all", action="store_true", help="Batch: alle tool-fähigen Modelle")
    parser.add_argument(
        "--provider",
        default="all",
        help="Provider-Filter: all | ollama | openai | anthropic | ... (kommasepariert)",
    )
    parser.add_argument("--force", action="store_true", help="Cache ignorieren (--force)")
    parser.add_argument("--silent", action="store_true", help="Audit-Logs unterdrücken")
    parser.add_argument("--mcp-mode", default="live", dest="mcp_mode", help="MCP-Modus (info)")
    parser.add_argument(
        "--no-restart-mcp",
        action="store_false",
        dest="restart_mcp",
        help="MCP-Neustart zwischen Modellen deaktivieren (schneller, aber weniger fair)",
    )
    parser.add_argument(
        "--summary-json",
        type=str,
        help="Optionaler Pfad für strukturiertes Run-Summary JSON (Orchestrator-Rückkanal).",
    )
    args = parser.parse_args()

    # MCP Server starten (falls nicht bereits aktiv) + Cleanup bei Abbruch sicherstellen
    _start_mcp_for_run(args.mcp_mode)
    atexit.register(_stop_mcp_if_managed)

    try:
        if args.model:
            ok = _run_model(args.model, force=args.force, silent=args.silent)
            # ToolUse-Leaderboard nach Einzellauf aktualisieren
            try:
                config = ConfigValidator().config
                exporter = ToolUseExporter(config)
                written = exporter.aggregate_from_benchmark_csvs(target_model_ids=[args.model])
                if written > 0:
                    print(f"  ToolUse-Leaderboard aktualisiert: {written} Modell(e) → tooluse_leaderboard.csv")
            except Exception as exc:  # noqa: BLE001
                print(f"  [WARN] ToolUse-Leaderboard-Update fehlgeschlagen: {exc}")
            write_run_summary(
                args.summary_json,
                {
                    "runner": "tooluse",
                    "status": "success" if ok else "failed",
                    "mode": "single",
                    "models_total": 1,
                    "models_successful": 1 if ok else 0,
                    "models_failed": 0 if ok else 1,
                    "failed_model_ids": [] if ok else [args.model],
                },
            )
            sys.exit(0 if ok else 1)

        elif args.models:
            wanted_ids = {m.strip() for m in args.models.split(",")}
            all_models = get_tool_use_models("all")
            models = [(mid, dname) for mid, dname in all_models if mid in wanted_ids]
            if not models:
                write_run_summary(
                    args.summary_json,
                    {
                        "runner": "tooluse",
                        "status": "failed",
                        "mode": "models",
                        "models_total": 0,
                        "models_successful": 0,
                        "models_failed": 0,
                        "failed_model_ids": [],
                        "message": f"Keine Modelle gefunden aus: {args.models}",
                    },
                )
                print(f"Keine Modelle gefunden aus: {args.models}")
                sys.exit(1)
            batch_summary = _run_batch(
                models, "custom",
                force=args.force, silent=args.silent,
                mcp_mode=args.mcp_mode, restart_mcp=args.restart_mcp,
            )
            status = "success" if batch_summary["models_failed"] == 0 else "partial"
            write_run_summary(
                args.summary_json,
                {
                    "runner": "tooluse",
                    "status": status,
                    "mode": "models",
                    **batch_summary,
                },
            )

        elif args.all or args.provider != "all":
            models = get_tool_use_models(args.provider)
            if not models:
                write_run_summary(
                    args.summary_json,
                    {
                        "runner": "tooluse",
                        "status": "success",
                        "mode": "all" if args.all else "provider",
                        "models_total": 0,
                        "models_successful": 0,
                        "models_failed": 0,
                        "failed_model_ids": [],
                        "message": f"Keine Modelle gefunden (provider: {args.provider})",
                    },
                )
                print(f"Keine Modelle gefunden (supports_tool_use: true, provider: {args.provider})")
                sys.exit(0)
            batch_summary = _run_batch(
                models, args.provider,
                force=args.force, silent=args.silent,
                mcp_mode=args.mcp_mode, restart_mcp=args.restart_mcp,
            )
            status = "success" if batch_summary["models_failed"] == 0 else "partial"
            write_run_summary(
                args.summary_json,
                {
                    "runner": "tooluse",
                    "status": status,
                    "mode": "all" if args.all else "provider",
                    **batch_summary,
                },
            )

        else:
            _interactive_wizard(
                force=args.force, silent=args.silent,
                mcp_mode=args.mcp_mode, restart_mcp=args.restart_mcp,
            )
            write_run_summary(
                args.summary_json,
                {
                    "runner": "tooluse",
                    "status": "success",
                    "mode": "wizard",
                },
            )

    except KeyboardInterrupt:
        write_run_summary(
            args.summary_json,
            {
                "runner": "tooluse",
                "status": "aborted",
                "mode": "unknown",
            },
        )
        print("\n\n  Benchmark abgebrochen (Ctrl+C). MCP Server wird beendet...")
        _stop_mcp_if_managed()
        sys.exit(130)


if __name__ == "__main__":
    main()
