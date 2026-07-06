"""Smoke-Test für den vllm_spark-Connector.

Verifiziert End-to-End:
1. Server-Start via ``vllm-start --config <TOML>`` (per SSH)
2. Readiness-Probe (Chat-Completion mit winzigem Payload)
3. Eigentliche Test-Query
4. Server-Stop via ``vllm-stop`` (per SSH)

Nutzung::

    .venv/bin/python scripts/tools/smoketest_vllm_spark.py
    .venv/bin/python scripts/tools/smoketest_vllm_spark.py --model Qwen2.5-0.5B

Setzt voraus:
- ``providers.local.vllm_spark.enabled = true`` in provider_config.yaml
- SSH-Key-Auth zu asusGX10 konfiguriert (BatchMode=yes)
- ``vllm-start`` und ``vllm-stop`` im Remote-PATH
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Projekt-Root auf sys.path, damit utils.* importierbar ist
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import yaml  # noqa: E402

from utils.providers.vllm_spark import VllmSparkClient  # noqa: E402


DEFAULT_MODEL = "Qwen2.5-0.5B"
PROMPT = "Was ist 2+2? Antworte in einem Wort."


def main() -> int:
    parser = argparse.ArgumentParser(description="vllm_spark Smoke-Test")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"TOML-Name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--prompt",
        default=PROMPT,
        help="Test-Prompt (default: 'Was ist 2+2? Antworte in einem Wort.')",
    )
    parser.add_argument(
        "--skip-start",
        action="store_true",
        help="Überspringe Server-Start (Server läuft bereits)",
    )
    parser.add_argument(
        "--skip-stop",
        action="store_true",
        help="Überspringe Server-Stop am Ende",
    )
    args = parser.parse_args()

    config_path = ROOT / "config" / "provider_config.yaml"
    with open(config_path, encoding="utf-8") as fh:
        config = yaml.safe_load(fh)

    provider_cfg = config.get("providers", {}).get("local", {}).get("vllm_spark", {})
    if not provider_cfg.get("enabled", False):
        print("❌ vllm_spark ist nicht aktiviert (enabled: false).")
        print(f"   Setze 'providers.local.vllm_spark.enabled: true' in {config_path}.")
        return 2

    client = VllmSparkClient(config)
    print(f"📡 vllm_spark-Endpoint: {client._base_url()}")
    print(f"🎯 Modell: {args.model}")
    print()

    # 1. Server starten (oder Adopt)
    if not args.skip_start:
        print(f"🚀 Starte Server: {client._build_server_cmd(args.model)}")
        t_start = time.time()
        if not client.start_server(args.model):
            print("❌ Server konnte nicht innerhalb des Timeouts gestartet werden.")
            return 3
        print(f"✅ Server bereit nach {time.time() - t_start:.1f}s")
        print()

    # 2. Test-Query
    print(f"💬 Query: {args.prompt!r}")
    try:
        t_start = time.time()
        response = client.query(
            model=args.model,
            prompt=args.prompt,
            temperature=0.0,
        )
        duration = time.time() - t_start
        print(f"🤖 Response ({duration:.1f}s): {response!r}")
        print()

        usage = client.last_response_metadata.get("usage")
        if usage:
            print(f"📊 Token-Nutzung: {usage}")
    except Exception as exc:
        print(f"❌ Query fehlgeschlagen: {type(exc).__name__}: {exc}")
        return 4

    # 3. Server stoppen
    if not args.skip_stop:
        print("🛑 Stoppe Server...")
        client.stop_server()
        print("✅ Server gestoppt.")

    print()
    print("🎉 Smoke-Test erfolgreich.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
