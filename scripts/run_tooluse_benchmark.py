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

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.core.tooluse_exporter import ToolUseExporter
from utils.config_validator import ConfigValidator

CARD_DIR = _ROOT / "benchmark_scores" / "model_cards"
TIMEOUT_PER_MODEL = 300  # 5 Minuten
MCP_STARTUP_WAIT = 1.5   # Sekunden nach mcp-start

_SEP = "═" * 54
_SEP_THIN = "─" * 54


# ---------------------------------------------------------------------------
# MCP lifecycle
# ---------------------------------------------------------------------------

def _restart_mcp(mode: str = "live") -> None:
    """Stop current MCP server and start a fresh one. ~1.5s overhead."""
    subprocess.run(
        ["make", "mcp-stop"],
        cwd=str(_ROOT), capture_output=True, check=False,
    )
    subprocess.run(
        ["make", "mcp-start", f"MODE={mode}"],
        cwd=str(_ROOT), capture_output=True, check=False,
    )
    time.sleep(MCP_STARTUP_WAIT)


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
    """Führt run_benchmark.py --module tooluse --model <id> aus. True = Erfolg."""
    cmd = [sys.executable, "run_benchmark.py", "--module", "tooluse", "--model", model_id]
    if force:
        cmd.append("--force")
    if silent:
        cmd.append("--silent")
    try:
        subprocess.run(cmd, check=True, timeout=TIMEOUT_PER_MODEL)
        return True
    except subprocess.CalledProcessError as exc:
        print(f"  [FAIL] exit code {exc.returncode}")
        return False
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] exceeded {TIMEOUT_PER_MODEL}s")
        return False
    except Exception as exc:  # noqa: BLE001 — pylint: disable=broad-exception-caught
        print(f"  [ERROR] {exc}")
        return False


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
) -> None:
    restart_note = "MCP-Neustart pro Modell" if restart_mcp else "kein MCP-Neustart"
    print(_SEP)
    print("  Tool Use Benchmark — Batch Run")
    print(f"  Provider: {provider_label}  |  MCP: {mcp_mode}  |  {restart_note}")
    print(f"  Modelle: {len(models)}")
    print(_SEP)

    success: list[str] = []
    failed: list[str] = []

    for i, (model_id, display_name) in enumerate(models, 1):
        if restart_mcp:
            print(f"\n  ↻ MCP-Neustart vor [{i}/{len(models)}]...")
            _restart_mcp(mcp_mode)
        print(f"\n[{i}/{len(models)}] {display_name}")
        if _run_model(model_id, force=force, silent=silent):
            success.append(model_id)
        else:
            failed.append(model_id)

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

    # Leaderboard automatisch aktualisieren
    try:
        config = ConfigValidator().config
        exporter = ToolUseExporter(config)
        written = exporter.aggregate_from_benchmark_csvs()
        if written > 0:
            exporter.calculate_sovereignty_gap()
            print(f"  Leaderboard aktualisiert: {written} Modell(e) → tooluse_leaderboard.csv")
        else:
            print("  Leaderboard: keine tooluse-Ergebnisse in Benchmark-CSVs gefunden.")
    except Exception as exc:  # noqa: BLE001 — leaderboard update must not crash CLI
        print(f"  [WARN] Leaderboard-Update fehlgeschlagen: {exc}")  # noqa: T201


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
    import argparse  # pylint: disable=import-outside-toplevel

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
    args = parser.parse_args()

    if args.model:
        ok = _run_model(args.model, force=args.force, silent=args.silent)
        sys.exit(0 if ok else 1)

    elif args.models:
        wanted_ids = {m.strip() for m in args.models.split(",")}
        all_models = get_tool_use_models("all")
        models = [(mid, dname) for mid, dname in all_models if mid in wanted_ids]
        if not models:
            print(f"Keine Modelle gefunden aus: {args.models}")
            sys.exit(1)
        _run_batch(
            models, "custom",
            force=args.force, silent=args.silent,
            mcp_mode=args.mcp_mode, restart_mcp=args.restart_mcp,
        )

    elif args.all or args.provider != "all":
        models = get_tool_use_models(args.provider)
        if not models:
            print(f"Keine Modelle gefunden (supports_tool_use: true, provider: {args.provider})")
            sys.exit(0)
        _run_batch(
            models, args.provider,
            force=args.force, silent=args.silent,
            mcp_mode=args.mcp_mode, restart_mcp=args.restart_mcp,
        )

    else:
        _interactive_wizard(
            force=args.force, silent=args.silent,
            mcp_mode=args.mcp_mode, restart_mcp=args.restart_mcp,
        )


if __name__ == "__main__":
    main()
