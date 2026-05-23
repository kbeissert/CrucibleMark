#!/usr/bin/env python3
"""One-time migration script: add `vendor` field to all model cards.

vendor = normalised vendor/provider name used as UI filter label "Familie".
Schema convention: `vendor` in code/JSON/CSV — "Familie"/"Anbieter-Familie" in UI
(analogue to size_class → "Größe").

Run:
    .venv/bin/python scripts/dev/add_vendor_field.py [--dry-run]
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CARDS_DIR = ROOT / "benchmark_scores" / "model_cards"

# ── Canonical vendor values ──────────────────────────────────────────────────
# key = model_id as stored in the JSON card
VENDOR_MAP: dict[str, str] = {
    # Anthropic
    "claude-haiku-4-5-20251001":    "Anthropic",
    "claude-sonnet-4-5-20250929":   "Anthropic",
    "claude-sonnet-4-6":            "Anthropic",
    "claude-opus-4-5-20251101":     "Anthropic",
    "claude-opus-4-6":              "Anthropic",
    "claude-opus-4-7":              "Anthropic",
    # OpenAI
    "gpt-4o":                       "OpenAI",
    "gpt-4o-mini":                  "OpenAI",
    "gpt-5":                        "OpenAI",
    "gpt-5-mini":                   "OpenAI",
    "gpt-5.4":                      "OpenAI",
    "gpt-5.4-mini":                 "OpenAI",
    "gpt-oss:120b-cloud":           "OpenAI",
    "gpt-oss:20b-cloud":            "OpenAI",
    "o1":                           "OpenAI",
    "o3-mini":                      "OpenAI",
    "o4-mini":                      "OpenAI",
    # Google
    "gemini-2.5-flash":             "Google",
    "gemini-2.5-pro":               "Google",
    "gemini-3-flash-preview":       "Google",
    "gemini-3.1-pro-preview":       "Google",
    "gemma3:4b":                    "Google",
    "gemma3:12b":                   "Google",
    "gemma4:e2b":                   "Google",
    "gemma4:E4B":                   "Google",
    "gemma4:26b":                   "Google",
    "gemma4:31b-cloud":             "Google",
    # Mistral AI
    "mistral-large-latest":         "Mistral AI",
    "mistral-medium-latest":        "Mistral AI",
    "mistral-small-latest":         "Mistral AI",
    "codestral-latest":             "Mistral AI",
    "magistral-medium-latest":      "Mistral AI",
    "magistral-small-latest":       "Mistral AI",
    "ministral-3:8b":               "Mistral AI",
    "ministral-3:14b":              "Mistral AI",
    # xAI
    "grok-3":                       "xAI",
    "grok-3-mini":                  "xAI",
    "grok-4-fast-non-reasoning":    "xAI",
    "grok-4-1-fast-reasoning":      "xAI",
    "grok-4.3":                     "xAI",
    "grok-4.20-0309-non-reasoning": "xAI",
    "grok-4.20-0309-reasoning":     "xAI",
    # DeepSeek
    "deepseek-r1:8b":               "DeepSeek",
    "deepseek-v3.1:671b-cloud":     "DeepSeek",
    "deepseek-v3.2:cloud":          "DeepSeek",
    "deepseek/deepseek-v4-flash":   "DeepSeek",
    "deepseek/deepseek-v4-pro":     "DeepSeek",
    # Meta
    "llama-3.3-70b-versatile":              "Meta",
    "meta-llama/llama-4-scout-17b-16e-instruct": "Meta",
    # NousResearch
    "hermes3:8b":                   "NousResearch",
    "nousresearch/hermes-4-70b":    "NousResearch",
    "nousresearch/hermes-4-405b":   "NousResearch",
    "hf.co_bartowski_NousResearch_Hermes-4-14B-GGUF_Q4_K_M": "NousResearch",
    # Zhipu AI
    "z-ai/glm-4.6":                 "Zhipu AI",
    "z-ai/glm-4.7":                 "Zhipu AI",
    "z-ai/glm-5-20260211":          "Zhipu AI",
    "z-ai/glm-5-turbo-20260315":    "Zhipu AI",
    "z-ai/glm-5.1-20260406":        "Zhipu AI",
    # Moonshot AI
    "moonshotai/kimi-k2":                   "Moonshot AI",
    "moonshotai/kimi-k2-thinking-20251106": "Moonshot AI",
    "moonshotai/kimi-k2.5-0127":            "Moonshot AI",
    "moonshotai/kimi-k2.6":                 "Moonshot AI",
    # MiniMax
    "minimax/minimax-m2.7-20260318": "MiniMax",
    # Alibaba
    "qwen/qwen3-32b":               "Alibaba",
    "qwen2.5:3b":                   "Alibaba",
    "qwen2.5-coder:7b":             "Alibaba",
    "qwen3:4b":                     "Alibaba",
    "qwen3:14b":                    "Alibaba",
    "qwen3.5:9b":                   "Alibaba",
    "qwen3.5:397b-cloud":           "Alibaba",
    # Community (abliterated / fine-tuned derivatives)
    "dolphin-mistral-nemo:latest":  "Community",
    "hf.co_mradermacher_Ministral-3-14B-abliterated-GGUF_Q8_0": "Community",
}


def patch_cards(dry_run: bool = False) -> None:
    cards = sorted(f for f in CARDS_DIR.glob("*.json") if f.name != "_index.json")
    patched = skipped = unknown = 0

    for card_path in cards:
        data = json.loads(card_path.read_text(encoding="utf-8"))
        model_id = data.get("model_id", "")

        vendor = VENDOR_MAP.get(model_id)
        if vendor is None:
            print(f"  [WARN] Kein Mapping für: {model_id!r} ({card_path.name})")
            vendor = "Community"
            unknown += 1

        if data.get("vendor") == vendor:
            skipped += 1
            continue

        data["vendor"] = vendor

        if not dry_run:
            card_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        patched += 1
        print(f"  {'[DRY]' if dry_run else '[OK] '} {card_path.name}: vendor = {vendor!r}")

    print(
        f"\nFertig: {patched} gepatcht, {skipped} bereits aktuell, "
        f"{unknown} ohne Mapping (→ 'Community')."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add vendor field to all model cards.")
    parser.add_argument("--dry-run", action="store_true", help="Nur anzeigen, nicht schreiben.")
    args = parser.parse_args()
    patch_cards(dry_run=args.dry_run)
