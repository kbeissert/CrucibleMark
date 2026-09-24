#!/usr/bin/env python3
"""
Refusal-Probe: Testet eine Modell-ID gegen die Reasoning-/Metacog-Assets,
an denen claude-opus-5 serverseitig verweigert (deterministisch, 2 Läufe:
2026-09-20 und 2026-09-24 — 8/11 Assets, stop_reason=refusal, 0 Output-Tokens).

Diagnostisches Tool — KEIN Benchmark-Bestandteil, schreibt keine CSVs/Cards.
Entscheidungsgrundlage: Kooperiert ein Nachfolger-Modell, bevor der
add-model-Workflow läuft (Nutzer-Entscheidung 2026-09-24)?

Prompt-Framing ist identisch zum Modul-Lauf: System-Prompt und Temperatur
werden direkt aus der Modul-SSoT importiert (core/constants/base.py),
User-Prompts aus den Asset-YAMLs gelesen.

Usage:
    .venv/bin/python scripts/tools/refusal_probe.py --model claude-opus-5-5
    .venv/bin/python scripts/tools/refusal_probe.py --model claude-opus-5-5 --positive-control
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from utils.constants import ANTHROPIC_NO_TEMPERATURE_MODELS  # noqa: E402

ASSETS_DIR = ROOT_DIR / "benchmark_modules" / "reasoning_logic" / "assets"
CONSTANTS_PATH = (
    ROOT_DIR / "benchmark_modules" / "reasoning_logic" / "core" / "constants" / "base.py"
)

# Refused-Set claude-opus-5 (Evidenz: commercial_models_benchmark.csv,
# 2026-09-20 + 2026-09-24, refusal_type=content_safety). Kontrollen: liefen
# bei opus-5 immer durch — zeigen, ob ein Modell generell antwortet.
REFUSED_IDS = [
    "reasoning_5a_001",
    "reasoning_5d_001",
    "reasoning_5e_001",
    "reasoning_metacog_001",
    "reasoning_metacog_002",
    "reasoning_metacog_003",
    "reasoning_metacog_004",
    "reasoning_metacog_005",
]
CONTROL_IDS = ["reasoning_001_river", "reasoning_5b_001", "reasoning_5c_001"]
POSITIVE_CONTROL_MODEL = "claude-opus-5"
POSITIVE_CONTROL_IDS = ["reasoning_5a_001", "reasoning_metacog_001"]
MAX_TOKENS = 4096
REQUEST_PAUSE_S = 1.0
PREVIEW_CHARS = 90


@dataclass
class ProbeResult:
    asset_id: str
    group: str
    stop_reason: str | None
    output_tokens: int
    response_len: int
    elapsed_s: float
    preview: str

    @property
    def refused(self) -> bool:
        return self.stop_reason == "refusal"

    @property
    def errored(self) -> bool:
        return self.stop_reason is None or self.stop_reason.startswith("API-")


def _load_module_constants() -> tuple[str, float]:
    """Importiert SYSTEM_PROMPT_REASONING + DEFAULT_TEMPERATURE aus der Modul-SSoT."""
    spec = importlib.util.spec_from_file_location("reasoning_constants", CONSTANTS_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.SYSTEM_PROMPT_REASONING, mod.DEFAULT_TEMPERATURE


def _load_assets() -> dict[str, str]:
    """Liest asset_id → prompt aus den Asset-YAMLs."""
    assets: dict[str, str] = {}
    for path in sorted(ASSETS_DIR.glob("*.yaml")):
        data: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
        assets[data["metadata"]["id"]] = data["prompt"]
    return assets


def _load_env() -> None:
    """Lädt .env manuell (KEY=VALUE), wenn der Key nicht schon exportiert ist."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def _probe_model(client: Any, model: str, assets: dict[str, str], system: str,
                 temperature: float, asset_ids: list[str] | None = None) -> list[ProbeResult]:
    """Führt die Probes für ein Modell aus (non-streaming, stop_reason direkt)."""
    import anthropic

    results: list[ProbeResult] = []
    targets = asset_ids or (REFUSED_IDS + CONTROL_IDS)
    send_temperature = model not in ANTHROPIC_NO_TEMPERATURE_MODELS
    for asset_id in targets:
        group = "CONTROL" if asset_id in CONTROL_IDS else "REFUSED-SET"
        start = time.monotonic()
        try:
            kwargs: dict[str, Any] = {
                "model": model,
                "system": system,
                "messages": [{"role": "user", "content": assets[asset_id]}],
                "max_tokens": MAX_TOKENS,
            }
            if send_temperature:
                kwargs["temperature"] = temperature
            try:
                response = client.messages.create(**kwargs)
            except anthropic.APIStatusError as exc:
                # Temperatur-Deprecation (neue Modelle): 1x ohne temperature wiederholen
                if exc.status_code == 400 and "temperature" in str(exc) and send_temperature:
                    send_temperature = False
                    kwargs.pop("temperature", None)
                    response = client.messages.create(**kwargs)
                else:
                    raise
            text = "".join(
                getattr(block, "text", "") for block in response.content
            )
            result = ProbeResult(
                asset_id=asset_id,
                group=group,
                stop_reason=response.stop_reason,
                output_tokens=getattr(response.usage, "output_tokens", 0),
                response_len=len(text.strip()),
                elapsed_s=time.monotonic() - start,
                preview=text.strip().replace("\n", " ")[:PREVIEW_CHARS],
            )
        except anthropic.APIStatusError as exc:
            result = ProbeResult(
                asset_id=asset_id, group=group, stop_reason=f"API-{exc.status_code}",
                output_tokens=0, response_len=0, elapsed_s=time.monotonic() - start,
                preview=str(exc)[:PREVIEW_CHARS],
            )
        marker = "🚫 REFUSAL" if result.refused else "✅"
        print(
            f"  {marker}  {result.asset_id:28} stop={result.stop_reason!s:12} "
            f"out_tok={result.output_tokens:5} len={result.response_len:5} "
            f"t={result.elapsed_s:5.1f}s  {result.preview}"
        )
        results.append(result)
        time.sleep(REQUEST_PAUSE_S)
    return results


def _summary(model: str, results: list[ProbeResult]) -> None:
    refused = [r for r in results if r.refused]
    errors = [r for r in results if r.errored]
    refused_set = [r for r in refused if r.group == "REFUSED-SET"]
    controls = [r for r in results if r.group == "CONTROL"]
    controls_refused = [r for r in controls if r.refused]
    print(f"\n── Ergebnis {model}: {len(refused)}/{len(results)} Verweigerungen, "
          f"{len(errors)} API-Fehler "
          f"(Refused-Set: {len(refused_set)}/{len(REFUSED_IDS)}, "
          f"Kontrollen: {len(controls_refused)}/{len(controls)})")
    if errors:
        print("   → Aussage unzuverlässig: API-Fehler zuerst klären (Request-Shape).")
    elif not refused:
        print("   → Modell kooperiert auf allen getesteten Assets.")
    else:
        print("   → Teil-/Komplett-Verweigerung: Benchmark-Integration kritisch prüfen.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Ziel-Modell-ID (z. B. claude-opus-5-5)")
    parser.add_argument("--positive-control", action="store_true",
                        help=f"Vorab 2 bekannte Refusal-Assets gegen {POSITIVE_CONTROL_MODEL} "
                             f"(validiert die Probe, ~2 Calls)")
    args = parser.parse_args()

    _load_env()
    import anthropic

    client = anthropic.Anthropic(max_retries=3)
    system, temperature = _load_module_constants()
    assets = _load_assets()
    missing = [a for a in REFUSED_IDS + CONTROL_IDS if a not in assets]
    if missing:
        print(f"❌ Assets fehlen: {missing}", file=sys.stderr)
        return 1

    if args.positive_control:
        print(f"── Positiv-Kontrolle ({POSITIVE_CONTROL_MODEL}, bekannt refusierend):")
        control = _probe_model(client, POSITIVE_CONTROL_MODEL, assets, system,
                               temperature, POSITIVE_CONTROL_IDS)
        _summary(POSITIVE_CONTROL_MODEL, control)
        print()

    print(f"── Ziel-Modell: {args.model} (System-Prompt/Temperatur aus Modul-SSoT, "
          f"max_tokens={MAX_TOKENS}, temp={temperature}):")
    results = _probe_model(client, args.model, assets, system, temperature)
    _summary(args.model, results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
