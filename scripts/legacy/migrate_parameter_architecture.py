"""
Migrates all model cards to add parameter_architecture, params_total_b, params_active_b.

Usage:
    python scripts/dev/migrate_parameter_architecture.py --dry-run
    python scripts/dev/migrate_parameter_architecture.py
"""

import json
import sys
from pathlib import Path

CARDS_DIR = Path("benchmark_scores/model_cards")

# (parameter_architecture, params_total_b, params_active_b)
# None = leave field absent (only params_active_b for dense models)
ASSIGNMENTS: dict[str, tuple[str, float | None, float | None]] = {
    # ── Anthropic / Claude ──────────────────────────────────────────────────
    "claude-haiku-4-5-20251001":        ("dense", None, None),
    "claude-opus-4-5-20251101":         ("dense", None, None),
    "claude-opus-4-6":                  ("dense", None, None),
    "claude-opus-4-7":                  ("dense", None, None),
    "claude-sonnet-4-5-20250929":       ("dense", None, None),
    "claude-sonnet-4-6":                ("dense", None, None),
    # ── OpenAI / GPT ───────────────────────────────────────────────────────
    "gpt-4o":                           ("dense", None, None),
    "gpt-4o-mini":                      ("dense", None, None),
    "gpt-5":                            ("dense", None, None),
    "gpt-5-mini":                       ("dense", None, None),
    "gpt-5.4":                          ("dense", None, None),
    "gpt-5.4-mini":                     ("dense", None, None),
    "gpt-oss:20b-cloud":                ("dense", 20.0, None),
    "gpt-oss:120b-cloud":               ("dense", 120.0, None),
    "o1":                               ("dense", None, None),
    "o3-mini":                          ("dense", None, None),
    "o4-mini":                          ("dense", None, None),
    # ── Google / Gemini ────────────────────────────────────────────────────
    "gemini-2.5-flash":                 ("dense", None, None),
    "gemini-2.5-pro":                   ("dense", None, None),
    "gemini-3-flash-preview":           ("dense", None, None),
    "gemini-3.1-pro-preview":           ("dense", None, None),
    # ── Google / Gemma 3 (dense) ───────────────────────────────────────────
    "gemma3:4b":                        ("dense", 4.0, None),
    "gemma3:12b":                       ("dense", 12.0, None),
    # ── Google / Gemma 4 (dense large variants) ────────────────────────────
    "gemma4:26b":                       ("dense", 27.0, None),
    "gemma4:31b-cloud":                 ("dense", 31.0, None),
    # gemma4:E4B and gemma4:e2b already updated manually → hybrid
    "gemma4:E4B":                       ("hybrid", 8.0, 4.5),
    "gemma4:e2b":                       ("hybrid", 5.1, 2.3),
    # ── xAI / Grok ─────────────────────────────────────────────────────────
    "grok-3":                           ("dense", None, None),
    "grok-3-mini":                      ("dense", None, None),
    "grok-4-1-fast-reasoning":          ("dense", None, None),
    "grok-4-fast-non-reasoning":        ("dense", None, None),
    "grok-4.20-0309-non-reasoning":     ("dense", None, None),
    "grok-4.20-0309-reasoning":         ("dense", None, None),
    "grok-4.3":                         ("dense", None, None),
    # ── Mistral AI ─────────────────────────────────────────────────────────
    "codestral-latest":                 ("dense", 22.0, None),
    "magistral-medium-latest":          ("dense", None, None),
    "magistral-small-latest":           ("dense", None, None),
    "ministral-3:8b":                   ("dense", 8.0, None),
    "ministral-3:14b":                  ("dense", 14.0, None),
    "mistral-large-2411":               ("dense", 123.0, None),
    "mistral-medium-2312":              ("dense", None, None),
    "mistral-medium-3-5":               ("dense", None, None),
    "mistral-small-2503":               ("dense", 24.0, None),
    "mistral-small-2603":               ("dense", 24.0, None),
    # ── Meta / Llama ───────────────────────────────────────────────────────
    "llama-3.3-70b-versatile":          ("dense", 70.0, None),
    "meta-llama/llama-4-scout-17b-16e-instruct": ("moe", 109.0, 17.0),
    # ── NousResearch / Hermes ──────────────────────────────────────────────
    "hermes3:8b":                               ("dense", 8.0, None),
    "hf.co_bartowski_NousResearch_Hermes-4-14B-GGUF_Q4_K_M": ("dense", 14.0, None),
    "hf.co_mradermacher_Ministral-3-14B-abliterated-GGUF_Q8_0": ("dense", 14.0, None),
    "nousresearch/hermes-4-70b":               ("dense", 70.0, None),
    "nousresearch/hermes-4-405b":              ("dense", 405.0, None),
    # ── CognitiveComputations ──────────────────────────────────────────────
    "dolphin-mistral-nemo:latest":      ("dense", 12.0, None),
    # ── DeepSeek ───────────────────────────────────────────────────────────
    "deepseek-r1:8b":                   ("dense", 8.0, None),   # distilled → dense
    "deepseek-v3.1:671b-cloud":         ("moe", 671.0, 37.0),
    "deepseek-v3.2:cloud":              ("moe", 671.0, 37.0),
    "deepseek/deepseek-v4-flash":       ("moe", None, None),
    "deepseek/deepseek-v4-pro":         ("moe", None, None),
    # ── Moonshot AI / Kimi ─────────────────────────────────────────────────
    "moonshotai/kimi-k2":               ("moe", 1000.0, 32.0),
    "moonshotai/kimi-k2.5-0127":        ("moe", 1000.0, 32.0),
    "moonshotai/kimi-k2.6":             ("moe", 1000.0, 32.0),
    "moonshotai/kimi-k2-thinking-20251106": ("moe", 1000.0, 32.0),
    # ── Alibaba / Qwen ─────────────────────────────────────────────────────
    "qwen2.5:3b":                       ("dense", 3.0, None),
    "qwen2.5-coder:7b":                 ("dense", 7.0, None),
    "qwen2.5vl:7b":                     ("dense", 7.0, None),
    "qwen3:4b":                         ("dense", 4.0, None),
    "qwen3:14b":                        ("dense", 14.0, None),
    "qwen/qwen3-32b":                   ("dense", 32.0, None),
    "qwen3.5:9b":                       ("dense", 9.0, None),
    "qwen3.5:397b-cloud":               ("moe", 397.0, None),
    "qwen/qwen3.6-plus":                ("hybrid", None, None),  # linear attention + sparse MoE
    "qwen/qwen3.7-max":                 ("moe", None, None),
    # ── Zhipu AI / GLM ─────────────────────────────────────────────────────
    "z-ai/glm-4.6":                     ("dense", None, None),
    "z-ai/glm-4.7":                     ("dense", None, None),
    "z-ai/glm-5-20260211":              ("dense", None, None),
    "z-ai/glm-5-turbo-20260315":        ("dense", None, None),
    "z-ai/glm-5.1-20260406":            ("dense", None, None),
    # ── MiniMax ────────────────────────────────────────────────────────────
    "minimax/minimax-m2.7-20260318":    ("moe", None, None),
}

VALID_ARCH = {"dense", "moe", "hybrid"}
DRY_RUN = "--dry-run" in sys.argv


def _card_model_id(data: dict) -> str:
    return data.get("model_id", "")


def main() -> int:
    if not CARDS_DIR.exists():
        print(f"ERROR: {CARDS_DIR} nicht gefunden.", file=sys.stderr)
        return 2

    rows: list[tuple[str, str, str, str]] = []  # (filename, model_id, arch, note)
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

        mid = _card_model_id(data)
        if mid not in ASSIGNMENTS:
            unmatched.append(f"  {path.name} (model_id={mid!r})")
            continue

        arch, total, active = ASSIGNMENTS[mid]

        if data.get("parameter_architecture") == arch and "params_total_b" in data:
            skipped += 1
            rows.append((path.name, mid, arch, "bereits vorhanden — skip"))
            continue

        data["parameter_architecture"] = arch
        if total is not None:
            data["params_total_b"] = total
        else:
            data.setdefault("params_total_b", None)

        if active is not None:
            data["params_active_b"] = active
        # dense: don't add params_active_b at all (not meaningful)

        note = f"{arch}"
        if total:
            note += f", {total}B total"
        if active:
            note += f", {active}B active"
        rows.append((path.name, mid, arch, note))

        if not DRY_RUN:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            updated += 1

    print(f"{'[DRY RUN] ' if DRY_RUN else ''}Parameter-Architektur-Migration")
    print(f"{'─' * 70}")
    for fn, mid, arch, note in rows:
        print(f"  {fn:52s}  {note}")

    if unmatched:
        print(f"\n⚠ KEINE ZUWEISUNG für {len(unmatched)} Cards:")
        for u in unmatched:
            print(u)

    print(f"\n{'─' * 70}")
    if DRY_RUN:
        print(f"Dry-run abgeschlossen — {len(rows)} Cards würden aktualisiert, {skipped} bereits korrekt.")
    else:
        print(f"Fertig — {updated} Cards aktualisiert, {skipped} bereits korrekt.")

    return 1 if unmatched else 0


if __name__ == "__main__":
    sys.exit(main())
