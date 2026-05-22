"""
Migrates all model cards to add context_window_k and knowledge_cutoff.

Usage:
    python scripts/dev/migrate_context_fields.py --dry-run
    python scripts/dev/migrate_context_fields.py
"""

import json
import sys
from pathlib import Path

CARDS_DIR = Path("benchmark_scores/model_cards")

# (context_window_k: int|None, knowledge_cutoff: str|None)
# context_window_k = context window in thousands of tokens (128 = 128K tokens)
# knowledge_cutoff = "YYYY-MM" training data cutoff, null if not publicly disclosed
ASSIGNMENTS: dict[str, tuple[int | None, str | None]] = {
    # ── Anthropic / Claude (200K context, early 2025 cutoff) ───────────────
    "claude-haiku-4-5-20251001":        (200, "2025-01"),
    "claude-opus-4-5-20251101":         (200, "2025-01"),
    "claude-opus-4-6":                  (200, "2025-01"),
    "claude-opus-4-7":                  (200, "2025-01"),
    "claude-sonnet-4-5-20250929":       (200, "2025-01"),
    "claude-sonnet-4-6":                (200, "2025-01"),
    # ── OpenAI ─────────────────────────────────────────────────────────────
    "gpt-4o":                           (128, None),
    "gpt-4o-mini":                      (128, None),
    "gpt-5":                            (None, None),
    "gpt-5-mini":                       (None, None),
    "gpt-5.4":                          (None, None),
    "gpt-5.4-mini":                     (None, None),
    "gpt-oss:20b-cloud":                (None, None),
    "gpt-oss:120b-cloud":               (None, None),
    "o1":                               (200, None),
    "o3-mini":                          (200, None),
    "o4-mini":                          (None, None),
    # ── Google / Gemini ────────────────────────────────────────────────────
    "gemini-2.5-flash":                 (1000, None),   # 1M tokens
    "gemini-2.5-pro":                   (1000, None),   # 1M tokens
    "gemini-3-flash-preview":           (None, None),
    "gemini-3.1-pro-preview":           (None, None),
    # ── Google / Gemma 3 ───────────────────────────────────────────────────
    "gemma3:4b":                        (128, None),
    "gemma3:12b":                       (128, None),
    # ── Google / Gemma 4 ───────────────────────────────────────────────────
    "gemma4:26b":                       (128, None),
    "gemma4:31b-cloud":                 (128, None),
    "gemma4:E4B":                       (128, None),
    "gemma4:e2b":                       (128, None),
    # ── xAI / Grok ─────────────────────────────────────────────────────────
    "grok-3":                           (131, None),    # 131K
    "grok-3-mini":                      (131, None),
    "grok-4-1-fast-reasoning":          (None, None),
    "grok-4-fast-non-reasoning":        (None, None),
    "grok-4.20-0309-non-reasoning":     (None, None),
    "grok-4.20-0309-reasoning":         (None, None),
    "grok-4.3":                         (None, None),
    # ── Mistral AI ─────────────────────────────────────────────────────────
    "codestral-latest":                 (256, None),    # Codestral 25.01: 256K
    "magistral-medium-latest":          (None, None),
    "magistral-small-latest":           (None, None),
    "ministral-3:8b":                   (128, None),
    "ministral-3:14b":                  (128, None),
    "mistral-large-2411":               (128, "2024-11"),
    "mistral-medium-2312":              (32,  "2023-12"),
    "mistral-medium-3-5":               (None, None),
    "mistral-small-2503":               (32,  None),
    "mistral-small-2603":               (32,  None),
    # ── Meta / Llama ───────────────────────────────────────────────────────
    "llama-3.3-70b-versatile":          (128, "2024-12"),
    "meta-llama/llama-4-scout-17b-16e-instruct": (10000, None),  # 10M tokens
    # ── NousResearch / Hermes ──────────────────────────────────────────────
    "hermes3:8b":                       (128, None),    # Llama 3.1 8B base
    "hf.co_bartowski_NousResearch_Hermes-4-14B-GGUF_Q4_K_M": (None, None),
    "hf.co_mradermacher_Ministral-3-14B-abliterated-GGUF_Q8_0": (128, None),
    "nousresearch/hermes-4-70b":        (None, None),
    "nousresearch/hermes-4-405b":       (None, None),
    # ── CognitiveComputations ──────────────────────────────────────────────
    "dolphin-mistral-nemo:latest":      (128, None),    # Mistral-Nemo base
    # ── DeepSeek ───────────────────────────────────────────────────────────
    "deepseek-r1:8b":                   (128, None),    # Qwen 2.5 7B base
    "deepseek-v3.1:671b-cloud":         (128, "2025-01"),
    "deepseek-v3.2:cloud":              (128, "2025-01"),
    "deepseek/deepseek-v4-flash":       (None, None),
    "deepseek/deepseek-v4-pro":         (None, None),
    # ── Moonshot AI / Kimi ─────────────────────────────────────────────────
    "moonshotai/kimi-k2":               (128, None),
    "moonshotai/kimi-k2.5-0127":        (128, None),
    "moonshotai/kimi-k2.6":             (128, None),
    "moonshotai/kimi-k2-thinking-20251106": (128, None),
    # ── Alibaba / Qwen ─────────────────────────────────────────────────────
    "qwen2.5:3b":                       (32,  "2024-09"),
    "qwen2.5-coder:7b":                 (32,  "2024-09"),
    "qwen2.5vl:7b":                     (32,  "2024-09"),
    "qwen3:4b":                         (32,  None),
    "qwen3:14b":                        (32,  None),
    "qwen/qwen3-32b":                   (32,  None),
    "qwen3.5:9b":                       (32,  None),
    "qwen3.5:397b-cloud":               (None, None),
    "qwen/qwen3.6-plus":                (None, None),
    "qwen/qwen3.7-max":                 (None, None),
    # ── Zhipu AI / GLM ─────────────────────────────────────────────────────
    "z-ai/glm-4.6":                     (128, None),
    "z-ai/glm-4.7":                     (128, None),
    "z-ai/glm-5-20260211":              (None, None),
    "z-ai/glm-5-turbo-20260315":        (None, None),
    "z-ai/glm-5.1-20260406":            (None, None),
    # ── MiniMax ────────────────────────────────────────────────────────────
    "minimax/minimax-m2.7-20260318":    (None, None),
}

DRY_RUN = "--dry-run" in sys.argv


def main() -> int:
    if not CARDS_DIR.exists():
        print(f"ERROR: {CARDS_DIR} nicht gefunden.", file=sys.stderr)
        return 2

    updated = 0
    skipped = 0
    unmatched: list[str] = []

    for path in sorted(CARDS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue

        mid = data.get("model_id", "")
        if mid not in ASSIGNMENTS:
            unmatched.append(f"  {path.name} (model_id={mid!r})")
            continue

        ctx_k, cutoff = ASSIGNMENTS[mid]

        changed = False
        if "context_window_k" not in data:
            data["context_window_k"] = ctx_k
            changed = True
        if "knowledge_cutoff" not in data:
            data["knowledge_cutoff"] = cutoff
            changed = True

        if not changed:
            skipped += 1
            continue

        ctx_str = f"{ctx_k}K" if ctx_k else "null"
        cut_str = cutoff or "null"
        print(f"  {path.name:52s}  ctx={ctx_str:6s}  cutoff={cut_str}")

        if not DRY_RUN:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            updated += 1

    if unmatched:
        print(f"\n⚠ KEINE ZUWEISUNG für {len(unmatched)} Cards:")
        for u in unmatched:
            print(u)

    print(f"\n{'[DRY RUN] ' if DRY_RUN else ''}Fertig — "
          f"{updated if not DRY_RUN else len(ASSIGNMENTS) - skipped} Cards aktualisiert, "
          f"{skipped} bereits gesetzt.")
    return 1 if unmatched else 0


if __name__ == "__main__":
    sys.exit(main())
