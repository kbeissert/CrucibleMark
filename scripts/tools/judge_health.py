#!/usr/bin/env python3
"""
LLM Judge Provider Health Check.

Pings all providers configured in llm_judge via config.example.yaml (or a
custom path provided via --config) and reports their status.

Usage:
    .venv/bin/python scripts/tools/judge_health.py
    .venv/bin/python scripts/tools/judge_health.py --config path/to/custom.yaml
"""

import argparse
import logging
import sys
from pathlib import Path

# Ensure project root is in path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    import yaml
except ImportError as exc:
    print(f"ERROR: 'pyyaml' not installed. Run: pip install pyyaml\n{exc}")
    sys.exit(1)

from utils.scoring.llm_judge.judge_config import (
    DEFAULT_OLLAMA_BASE_URL,
    LLMJudgeConfig,
    ProviderName,
)
from utils.scoring.llm_judge.judge_runner import _build_provider

logging.basicConfig(level=logging.WARNING, format="%(message)s")

_DEFAULT_CONFIG = ROOT_DIR / "benchmark_config.yaml"

_ALL_PROVIDERS: list[ProviderName] = ["anthropic", "mistral", "openai", "ollama"]


def _check_provider(name: ProviderName, config: LLMJudgeConfig) -> tuple[str, bool, str]:
    """
    Attempt to instantiate and health-check a single provider.

    Returns:
        Tuple of (provider_name, is_healthy, status_message).
    """
    import copy

    cfg_copy = config.model_copy(deep=True)
    cfg_copy.provider.name = name  # type: ignore[assignment]

    # Map name to proper model based on config first, then defaults
    if name == config.provider.name:
        cfg_copy.provider.model = config.provider.model
    elif config.provider.fallback and name == config.provider.fallback.name:
        cfg_copy.provider.model = config.provider.fallback.model
    else:
        if name == "anthropic":
            from utils.scoring.llm_judge.judge_config import DEFAULT_ANTHROPIC_MODEL
            cfg_copy.provider.model = DEFAULT_ANTHROPIC_MODEL  # type: ignore[assignment]
        elif name == "mistral":
            from utils.scoring.llm_judge.judge_config import DEFAULT_MISTRAL_MODEL
            cfg_copy.provider.model = DEFAULT_MISTRAL_MODEL  # type: ignore[assignment]
        elif name == "openai":
            from utils.scoring.llm_judge.judge_config import DEFAULT_OPENAI_MODEL
            cfg_copy.provider.model = DEFAULT_OPENAI_MODEL  # type: ignore[assignment]
        elif name == "ollama":
            from utils.scoring.llm_judge.judge_config import DEFAULT_OLLAMA_MODEL
            cfg_copy.provider.model = DEFAULT_OLLAMA_MODEL  # type: ignore[assignment]
            
    if name == "ollama" and not cfg_copy.provider.base_url:
        cfg_copy.provider.base_url = DEFAULT_OLLAMA_BASE_URL  # type: ignore[assignment]

    try:
        provider = _build_provider(cfg_copy)
        healthy = provider.health_check()
        msg = "OK" if healthy else "UNREACHABLE or MODEL NOT FOUND"
        return name, healthy, msg
    except ImportError as exc:
        return name, False, f"MISSING SDK – {exc}"
    except ValueError as exc:
        return name, False, f"CONFIG ERROR – {exc}"
    except Exception as exc:  # pylint: disable=broad-exception-caught
        return name, False, f"ERROR – {exc}"


def main() -> None:
    """Run health checks against all LLM Judge providers."""
    parser = argparse.ArgumentParser(description="LLM Judge provider health check")
    parser.add_argument(
        "--config",
        type=Path,
        default=_DEFAULT_CONFIG,
        help="Path to a llm_judge YAML config file.",
    )
    parser.add_argument(
        "--provider",
        choices=list(_ALL_PROVIDERS),
        default=None,
        help="Check a single provider instead of all.",
    )
    args = parser.parse_args()

    if args.config.exists():
        raw = yaml.safe_load(args.config.read_text(encoding="utf-8"))
        if not raw or "llm_judge" not in raw:
            print(f"ERROR: Could not read llm_judge from {args.config}")
            sys.exit(1)
        config = LLMJudgeConfig.from_dict(raw)
    else:
        print(f"ERROR: Config not found at {args.config}.")
        sys.exit(1)

    providers_to_check: list[ProviderName] = (
        [args.provider] if args.provider else list(_ALL_PROVIDERS)  # type: ignore[list-item]
    )

    print("\nLLM Judge – Provider Health Check")
    print("=" * 40)
    all_ok = True
    for name in providers_to_check:
        _, healthy, msg = _check_provider(name, config)
        status = "PASS" if healthy else "FAIL"
        icon = "" if healthy else ""
        print(f"  {icon} [{status}] {name:12s} → {msg}")
        if not healthy:
            all_ok = False

    print("=" * 40)
    if all_ok:
        print("All provider checks passed.")
    else:
        print("Some providers are unavailable. Check API keys or connectivity.")
    print()
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
