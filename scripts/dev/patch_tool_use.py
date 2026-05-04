"""One-shot migration: adds supports_tool_use to all existing model cards.

Usage:
    .venv/bin/python scripts/dev/patch_tool_use.py [--dry-run]

Decision rules:
  true  = confirmed Function Calling / Tool Use support per provider docs
  false = confirmed no tool support (abliterated, R1-base local, old Mistral-Nemo)
  null  = not yet assessed (not written — field stays absent until generate_review re-generates card)

After running, check with:
    grep -L "supports_tool_use" benchmark_scores/model_cards/*.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
CARDS_DIR = ROOT_DIR / "benchmark_scores" / "model_cards"

# Keyed by exact JSON filename (case-sensitive)
TOOL_USE_MAP: dict[str, bool | None] = {
    # ── Anthropic (all support tool use) ───────────────────────────────────
    "claude-haiku-4-5-20251001.json": True,
    "claude-opus-4-5-20251101.json": True,
    "claude-opus-4-6.json": True,
    "claude-opus-4-7.json": True,
    "claude-sonnet-4-5-20250929.json": True,
    "claude-sonnet-4-6.json": True,
    # ── Mistral (cloud) ────────────────────────────────────────────────────
    "codestral-latest.json": True,
    "magistral-medium-latest.json": True,
    "magistral-small-latest.json": True,
    "mistral-large-latest.json": True,
    "mistral-medium-latest.json": True,
    "mistral-small-latest.json": True,
    # ── DeepSeek (cloud) ───────────────────────────────────────────────────
    "deepseek-v3_1_671b-cloud.json": True,
    "deepseek-v3_2_cloud.json": True,
    "deepseek_deepseek-v4-flash.json": True,
    "deepseek_deepseek-v4-pro.json": True,
    # ── Google ─────────────────────────────────────────────────────────────
    "gemini-2_5-flash.json": True,
    "gemini-2_5-pro.json": True,
    "gemini-3-flash-preview.json": True,
    "gemini-3_1-pro-preview.json": True,
    # ── OpenAI ─────────────────────────────────────────────────────────────
    "gpt-4o-mini.json": True,
    "gpt-4o.json": True,
    "gpt-5-mini.json": True,
    "gpt-5.json": True,
    "gpt-5_4-mini.json": True,
    "gpt-5_4.json": True,
    "gpt-oss_120b-cloud.json": True,
    "gpt-oss_20b-cloud.json": True,
    "o1.json": True,        # supported since 2024-11 update
    "o3-mini.json": True,
    "o4-mini.json": True,
    # ── xAI Grok ───────────────────────────────────────────────────────────
    "grok-3-mini.json": True,
    "grok-3.json": True,
    "grok-4-1-fast-reasoning.json": True,
    "grok-4-fast-non-reasoning.json": True,
    # ── Meta / Groq ────────────────────────────────────────────────────────
    "llama-3_3-70b-versatile.json": True,
    "meta-llama_llama-4-scout-17b-16e-instruct.json": True,
    # ── MiniMax ────────────────────────────────────────────────────────────
    "minimax_minimax-m2_7-20260318.json": True,
    "minimax_minimax-m2_7.json": True,
    # ── Moonshot Kimi K2 ───────────────────────────────────────────────────
    "moonshotai_kimi-k2-thinking-20251106.json": True,
    "moonshotai_kimi-k2.json": True,
    "moonshotai_kimi-k2_5-0127.json": True,
    "moonshotai_kimi-k2_5.json": True,
    "moonshotai_kimi-k2_6.json": True,
    # ── NousResearch (cloud/OR) ────────────────────────────────────────────
    "nousresearch_hermes-4-405b.json": True,
    "nousresearch_hermes-4-70b.json": True,
    # ── Zhipu GLM ──────────────────────────────────────────────────────────
    "z-ai_glm-4_6.json": True,
    "z-ai_glm-4_7.json": True,
    "z-ai_glm-5-20260211.json": True,
    "z-ai_glm-5-turbo-20260315.json": True,
    "z-ai_glm-5-turbo.json": True,
    "z-ai_glm-5.json": True,
    "z-ai_glm-5_1-20260406.json": True,
    "z-ai_glm-5_1.json": True,
    # ── Qwen (cloud / OR) ──────────────────────────────────────────────────
    "qwen3_5_397b-cloud.json": True,
    "qwen_qwen3-32b.json": True,
    # ── Local Ollama — supports tool use ──────────────────────────────────
    "gemma3_12b.json": True,      # Gemma 3 supports FC
    "gemma3_4b.json": True,
    "gemma4_26b.json": True,
    "gemma4_31b-cloud.json": True,
    "gemma4_E4B.json": True,
    "gemma4_e2b.json": True,
    "hermes3_8b.json": True,       # Hermes 3 explicitly trained with FC
    "NousResearch_Hermes-4-14B-GGUF_Q4_K_M.json": True,
    "hf_co_bartowski_NousResearch_Hermes-4-14B-GGUF_Q4_K_M.json": True,
    "qwen3_14b.json": True,
    "qwen3_4b.json": True,
    "qwen3_5_9b.json": True,
    "qwen2_5_3b.json": True,       # Qwen2.5 supports FC across sizes
    "qwen2_5-coder_7b.json": True, # Qwen2.5-Coder supports FC
    "ministral-3_8b.json": True,   # Ministral 8B supports FC in Ollama
    "ministral-3_14b.json": True,  # Ministral 14B supports FC in Ollama
    # ── Local Ollama — does NOT support tool use ───────────────────────────
    "deepseek-r1_8b.json": False,  # R1-base Ollama: no FC support
    # Abliterated/uncensored — FC templates stripped
    "CognitiveComputations_dolphin-mistral-nemo_latest.json": False,
    "dolphin-mistral-nemo_latest.json": False,
    "Ministral-3-14B-abliterated-GGUF_Q8_0.json": False,
    "hf_co_mradermacher_Ministral-3-14B-abliterated-GGUF_Q8_0.json": False,
}


def patch_cards(dry_run: bool) -> None:
    patched = skipped = unknown = 0

    for card_file in sorted(CARDS_DIR.glob("*.json")):
        name = card_file.name
        if name.startswith("_"):
            continue  # _index.json, _all_cards.md

        if name not in TOOL_USE_MAP:
            print(f"  [?] {name} — not in map, skipping (will stay without field)")
            unknown += 1
            continue

        value = TOOL_USE_MAP[name]
        try:
            data = json.loads(card_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            print(f"  [ERR] {name}: {exc}")
            skipped += 1
            continue

        if "supports_tool_use" in data:
            print(f"  [=] {name} — already has supports_tool_use={data['supports_tool_use']!r}, skipping")
            skipped += 1
            continue

        data["supports_tool_use"] = value
        label = "true " if value is True else ("false" if value is False else "null ")
        print(f"  [+] {name} → supports_tool_use: {label}")

        if not dry_run:
            card_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        patched += 1

    print(f"\nDone: {patched} patched, {skipped} skipped, {unknown} unknown (no field added).")
    if dry_run:
        print("(dry-run — no files written)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Add supports_tool_use to all model cards.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    args = parser.parse_args()
    patch_cards(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
