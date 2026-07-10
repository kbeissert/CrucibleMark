#!/usr/bin/env python3
"""
Einmalig-Script: Fügt license, license_url, commercial_use_allowed
in alle Model Cards ein.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# (license, license_url, commercial_use_allowed)
# commercial_use_allowed:
#   True  = explizit erlaubt (Apache 2.0, MIT, kostenpflichtige proprietäre API)
#   False = explizit verboten (Forschungs-Lizenzen wie GLM-4)
#   None  = eingeschränkt, skalenabhängig oder unklar
LICENSE_MAP: dict[str, tuple] = {
    # Anthropic
    "claude-haiku-4-5-20251001": ("Proprietary", None, True),
    "claude-opus-4-5-20251101": ("Proprietary", None, True),
    "claude-opus-4-6": ("Proprietary", None, True),
    "claude-opus-4-7": ("Proprietary", None, True),
    "claude-sonnet-4-5-20250929": ("Proprietary", None, True),
    "claude-sonnet-4-6": ("Proprietary", None, True),
    # OpenAI
    "gpt-4o": ("Proprietary", None, True),
    "gpt-4o-mini": ("Proprietary", None, True),
    "gpt-5": ("Proprietary", None, True),
    "gpt-5-mini": ("Proprietary", None, True),
    "gpt-5.4": ("Proprietary", None, True),
    "gpt-5.4-mini": ("Proprietary", None, True),
    "gpt-oss:120b-cloud": ("Proprietary", None, True),
    "gpt-oss:20b-cloud": ("Proprietary", None, True),
    "o1": ("Proprietary", None, True),
    "o3-mini": ("Proprietary", None, True),
    "o4-mini": ("Proprietary", None, True),
    # Google
    "gemini-2.5-flash": ("Proprietary", None, True),
    "gemini-2.5-pro": ("Proprietary", None, True),
    "gemini-3-flash-preview": ("Proprietary", None, True),
    "gemini-3.1-pro-preview": ("Proprietary", None, True),
    "gemma4:31b-cloud": ("Google Gemma Terms of Use", "https://ai.google.dev/gemma/terms", None),
    # xAI
    "grok-3": ("Proprietary", None, True),
    "grok-3-mini": ("Proprietary", None, True),
    "grok-4-1-fast-reasoning": ("Proprietary", None, True),
    "grok-4-fast-non-reasoning": ("Proprietary", None, True),
    # Mistral AI (closed models)
    "codestral-latest": ("Mistral Codestral License", "https://mistral.ai/licenses/MCSL-0.1.md", None),
    "magistral-medium-latest": ("Proprietary", None, True),
    "magistral-small-latest": ("Proprietary", None, True),
    "mistral-large-latest": ("Proprietary", None, True),
    "mistral-medium-latest": ("Proprietary", None, True),
    # MiniMax
    "minimax_minimax-m2.7": ("Proprietary", None, True),
    # Moonshot AI (API-only)
    "moonshotai_kimi-k2.5": ("Proprietary", None, True),
    # Alibaba (cloud-only variant)
    "qwen3.5:397b-cloud": ("Proprietary", None, True),
    # Zhipu AI – GLM-5 (proprietär, kein Weight-Release)
    "z-ai_glm-5": ("Proprietary", None, True),
    "z-ai_glm-5-turbo": ("Proprietary", None, True),
    "z-ai_glm-5.1": ("Proprietary", None, True),
    "z-ai/glm-5-20260211": ("Proprietary", None, True),
    "z-ai/glm-5-turbo-20260315": ("Proprietary", None, True),
    "z-ai/glm-5.1-20260406": ("Proprietary", None, True),
    # DeepSeek (cloud/unbekannt)
    "deepseek/deepseek-v4-flash": ("DeepSeek License", "https://github.com/deepseek-ai/DeepSeek-V3/blob/main/LICENSE", None),
    "deepseek/deepseek-v4-pro": ("DeepSeek License", "https://github.com/deepseek-ai/DeepSeek-V3/blob/main/LICENSE", None),
    # Open-Weights (selbst hostbar)
    "CognitiveComputations_dolphin-mistral-nemo_latest": ("Apache-2.0", "https://www.apache.org/licenses/LICENSE-2.0", True),
    "dolphin-mistral-nemo:latest": ("Apache-2.0", "https://www.apache.org/licenses/LICENSE-2.0", True),
    "gemma4:E4B": ("Google Gemma Terms of Use", "https://ai.google.dev/gemma/terms", None),
    "hermes3:8b": ("Meta Llama Community License", "https://www.llama.com/llama3/license/", None),
    "hf.co_bartowski_NousResearch_Hermes-4-14B-GGUF_Q4_K_M": ("Apache-2.0", "https://www.apache.org/licenses/LICENSE-2.0", True),
    "hf.co_mradermacher_Ministral-3-14B-abliterated-GGUF_Q8_0": ("Mistral Research License", "https://mistral.ai/licenses/MRL-0.1.md", None),
    "Ministral-3-14B-abliterated-GGUF:Q8_0": ("Mistral Research License", "https://mistral.ai/licenses/MRL-0.1.md", None),
    "NousResearch_Hermes-4-14B-GGUF:Q4_K_M": ("Apache-2.0", "https://www.apache.org/licenses/LICENSE-2.0", True),
    "nousresearch/hermes-4-405b": ("Meta Llama Community License", "https://www.llama.com/llama3/license/", None),
    "nousresearch/hermes-4-70b": ("Meta Llama Community License", "https://www.llama.com/llama3/license/", None),
    "z-ai/glm-4.6": ("GLM-4 License", "https://huggingface.co/THUDM/glm-4-9b/blob/main/LICENSE", False),
    # Open-Weights + Cloud-Available
    "deepseek-r1:8b": ("MIT", "https://opensource.org/licenses/MIT", True),
    "deepseek-v3.1:671b-cloud": ("DeepSeek License", "https://github.com/deepseek-ai/DeepSeek-V3/blob/main/LICENSE", None),
    "deepseek-v3.2:cloud": ("DeepSeek License", "https://github.com/deepseek-ai/DeepSeek-V3/blob/main/LICENSE", None),
    "gemma3:12b": ("Google Gemma Terms of Use", "https://ai.google.dev/gemma/terms", None),
    "gemma3:4b": ("Google Gemma Terms of Use", "https://ai.google.dev/gemma/terms", None),
    "gemma4:26b": ("Google Gemma Terms of Use", "https://ai.google.dev/gemma/terms", None),
    "gemma4:e2b": ("Google Gemma Terms of Use", "https://ai.google.dev/gemma/terms", None),
    "llama-3.3-70b-versatile": ("Meta Llama Community License", "https://www.llama.com/llama3/license/", None),
    "meta-llama/llama-4-scout-17b-16e-instruct": ("Meta Llama Community License", "https://www.llama.com/llama4/license/", None),
    "minimax/minimax-m2.7-20260318": (None, None, None),
    "ministral-3:14b": ("Mistral Research License", "https://mistral.ai/licenses/MRL-0.1.md", None),
    "ministral-3:8b": ("Mistral Research License", "https://mistral.ai/licenses/MRL-0.1.md", None),
    "mistral-small-latest": ("Apache-2.0", "https://www.apache.org/licenses/LICENSE-2.0", True),
    "moonshotai/kimi-k2": ("Moonshot AI License", "https://huggingface.co/moonshotai/Kimi-K2-Instruct/blob/main/LICENSE", None),
    "moonshotai/kimi-k2-thinking-20251106": ("Moonshot AI License", "https://huggingface.co/moonshotai/Kimi-K2-Instruct/blob/main/LICENSE", None),
    "moonshotai/kimi-k2.5-0127": ("Moonshot AI License", "https://huggingface.co/moonshotai/Kimi-K2-Instruct/blob/main/LICENSE", None),
    "moonshotai/kimi-k2.6": ("Moonshot AI License", "https://huggingface.co/moonshotai/Kimi-K2-Instruct/blob/main/LICENSE", None),
    "qwen/qwen3-32b": ("Apache-2.0", "https://www.apache.org/licenses/LICENSE-2.0", True),
    "qwen2.5-coder:7b": ("Apache-2.0", "https://www.apache.org/licenses/LICENSE-2.0", True),
    "qwen3:14b": ("Apache-2.0", "https://www.apache.org/licenses/LICENSE-2.0", True),
    "qwen3:4b": ("Apache-2.0", "https://www.apache.org/licenses/LICENSE-2.0", True),
    "qwen3.5:9b": ("Apache-2.0", "https://www.apache.org/licenses/LICENSE-2.0", True),
    "z-ai/glm-4.7": ("GLM-4 License", "https://huggingface.co/THUDM/glm-4-9b/blob/main/LICENSE", False),
    "qwen2.5:3b": ("Apache-2.0", "https://www.apache.org/licenses/LICENSE-2.0", True),
}


def main() -> None:
    cards = sorted((ROOT / "benchmark_scores" / "model_cards").glob("*.json"))
    updated = 0
    unmatched: list[str] = []

    for c in cards:
        d = json.loads(c.read_text(encoding="utf-8"))
        if not isinstance(d, dict):
            continue
        mid = d.get("model_id", "")
        if mid in LICENSE_MAP:
            lic, lic_url, commercial = LICENSE_MAP[mid]
        else:
            lic, lic_url, commercial = None, None, None
            unmatched.append(mid)
        d["license"] = lic
        d["license_url"] = lic_url
        d["commercial_use_allowed"] = commercial
        c.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        updated += 1

    print(f"Aktualisiert: {updated} Karten")
    if unmatched:
        print(f"Ohne Mapping ({len(unmatched)} — null gesetzt):")
        for m in unmatched:
            print(f"  {m}")
    else:
        print("Alle Karten haben ein Lizenz-Mapping.")


if __name__ == "__main__":
    main()
