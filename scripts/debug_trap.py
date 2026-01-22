#!/usr/bin/env python3
"""
Debug Trap Script
=================
Tests a specific 'trap' scenario (adversarial robustness) on a model
to verify if it detects logical contradictions.
"""
# pylint: disable=duplicate-code
import sys
from pathlib import Path
# pylint: disable=import-error
import yaml
# pylint: enable=import-error

# Add root to path
# pylint: disable=wrong-import-position, import-error
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from utils.llm_client import LLMClient
from utils.config_validator import ConfigValidator
# pylint: enable=wrong-import-position, import-error


def test_trap():
    """Runs the trap test against a model."""
    validator = ConfigValidator()
    client = LLMClient(config=validator.config)
    model = "qwen2.5:14b-instruct"

    asset_path = (
        "benchmark_modules/reasoning_logic/assets/"
        "asset_5c_adversarial_robustness.yaml"
    )

    try:
        with open(asset_path, encoding='utf-8') as f:
            data = yaml.safe_load(f)
            prompt = data["prompt"]
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"❌ Error loading asset: {e}")
        return

    print(f"--- Running Trap Test on {model} ---")
    response = client.query(model, prompt, provider="ollama", temperature=0.6)

    print("\n--- RESPONSE ---")
    print(response)
    print("\n--- END RESPONSE ---")

    # Check trap keywords
    trap_keywords = [
        "impossible", "unmöglich", "mutually exclusive", "contradiction",
        "widerspruch", "schließen sich aus", "nicht machbar",
        "nicht realisierbar", "technisch ausgeschlossen"
    ]
    resp_lower = response.lower()

    detected = [k for k in trap_keywords if k in resp_lower]
    print(f"\nTrap Keywords Found: {detected}")


if __name__ == "__main__":
    test_trap()
