#!/usr/bin/env python3
"""
Debug Ollama Connection
=======================
Simple script to test connectivity and query capability of Ollama
using the project's LLMClient.
"""

import sys
import time
from pathlib import Path

# Add root to path
# pylint: disable=wrong-import-position
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# pylint: disable=import-error
from utils.llm_client import LLMClient
# pylint: enable=import-error, wrong-import-position


def test_ollama_query():
    """Executes a test query against Ollama."""
    client = LLMClient()
    model = "qwen2.5:14b-instruct"  # Updated default model

    # Load prompt from asset 002
    asset_path = "benchmark_modules/ux_writing/assets/asset_002_button_labels.yaml"
    try:
        with open(asset_path, encoding='utf-8') as f:
            # pylint: disable=import-outside-toplevel, import-error
            import yaml
            data = yaml.safe_load(f)
            prompt = data["prompt"]
            context = data.get("context", "")
            full_prompt = f"{context}\n\n{prompt}"
    except (OSError, ImportError) as e:
        print(f"❌ Setup Error: {e}")
        return

    print(f"Querying {model} with prompt length {len(full_prompt)}...")
    start = time.time()
    try:
        response = client.query(model, full_prompt, provider="ollama")
        elapsed = time.time() - start
        print(f"Response received in {elapsed:.2f}s")
        print(f"Response length: {len(response)}")
        print(f"Response preview: {response[:100]}...")

        if not response:
            print("WARNING: Empty response received!")

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"ERROR: {e}")


if __name__ == "__main__":
    test_ollama_query()
