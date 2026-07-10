"""
Backfill für input_modalities / output_modalities (Pflicht seit v4.7.0).

Leitet Defaults aus model_id, model_family, architecture_tags und
summary/strengths ab. Nicht-deterministische Defaults (z.B. Audio) werden
per Konsole markiert, damit sie manuell geprüft werden können.

Heuristik:
- Audio: nur Gemma 4 12B nativ (per bekannter Info)
- Image: architecture_tags enthält "Multimodal" oder "Vision-Capable" ODER
  model_id matcht ['*-4o*', '*-opus-4*', '*-sonnet-4*', 'gemini-*', '*-vl-*',
  'qwen*-vl-*', 'pixtral-*', 'gemma-3-*', 'gemma-4-*', '*-ara-*', '*-it']
- Text-only: alles andere
- Output: meist text; "text" + ggf. "image" wenn model_id "image-gen" enthält

Idempotent: Karten mit bereits gesetzten Feldern werden nicht überschrieben.

Verwendung:
    .venv/bin/python scripts/dev/backfill_modalities.py --dry-run
    .venv/bin/python scripts/dev/backfill_modalities.py --apply
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

logger = logging.getLogger(__name__)

CARDS_DIR = Path("benchmark_scores/model_cards")

# Modell-IDs mit nativer Audio-Fähigkeit
AUDIO_CAPABLE_MODEL_PATTERNS = [
    r"gemma-?4-?12b",
    r"gemma-4-12b-it-ud",
]

# Modell-IDs mit nativer Vision-/Bild-Fähigkeit
VISION_CAPABLE_MODEL_PATTERNS = [
    r"gpt-4o",
    r"gpt-4\.1",
    r"gpt-5($|[^_])",  # gpt-5, gpt-5-mini, gpt-5_4-mini etc.
    r"gpt-5_[0-9]+-(pro|nano|mini)",
    r"claude-(opus|sonnet|haiku)-4",  # Claude 4.x alle vision
    r"gemini-",
    r"gemma-3-",
    r"gemma-4-",
    r"gemma-?4_E",  # Gemma 4 E-Varianten (Edge, Effizient)
    r"gemma-4-31b",
    r"pixtral",
    r"qwen.*-vl-",
    r"qwen.*vl",
    r"ministral",
    r"mistral-small-2603",
    r"devstral",
    r"-it$",  # instruct-tuned Qwen/Google oft mit Vision
    r"-ara-",  # Gemma Ara-Variante
    r"kimi-k2",  # Kimi mit Vision
    r"deepseek-v3",  # DeepSeek V3+ mit Vision
    r"deepseek-v4",
    r"o3-mini",  # o3-mini hat Vision
    r"o4-mini",
    r"llama-4",
    r"magistral",
    r"nemotron",
]

# Modell-IDs mit Bild-Output (selten)
IMAGE_OUTPUT_MODEL_PATTERNS = [
    r"image-gen",
    r"dall-?e",
    r"imagen",
    r"flux",
    r"sdxl",
    r"stable-diffusion",
    r"midjourney",
]


def derive_modalities(data: dict) -> tuple[list[str], list[str] | None, str | None]:
    """Returns (input_modalities, output_modalities_or_None_if_skip, reason)."""
    model_id = data.get("model_id", "")
    display = data.get("display_name", "")
    arch_tags = data.get("architecture_tags", []) or []
    summary = (data.get("summary", "") or "").lower()
    strengths = " ".join(data.get("strengths", []) or []).lower()

    # Bereits gesetzt? Nicht überschreiben.
    if data.get("input_modalities") is not None and data.get("output_modalities") is not None:
        return [], None, "bereits gesetzt"

    has_vision_tag = any(t in arch_tags for t in ("Multimodal", "Vision-Capable"))
    has_vision_text = any(
        kw in (summary + " " + strengths) for kw in (
            "vision", "bild", "image", "multimodal", "screenshot", "diagram",
        )
    )
    has_audio_text = any(
        # "sprache" bewusst NICHT dabei (false-positive bei "Sprachverständnis" = multilingual)
        kw in (summary + " " + strengths) for kw in ("audio", "speech", "asr", "tts", "audio-fähig", "audiofähig", "audioingabe", "audioausgabe")
    )

    # Audio-Check (explizit nur für Gemma 4 12B nativ)
    has_audio = any(re.search(p, model_id, re.IGNORECASE) for p in AUDIO_CAPABLE_MODEL_PATTERNS) or has_audio_text

    # Vision-Check
    pattern_match = any(
        re.search(p, model_id, re.IGNORECASE) for p in VISION_CAPABLE_MODEL_PATTERNS
    )
    has_vision = has_vision_tag or has_vision_text or pattern_match

    # Output-Bild
    has_image_output = any(
        re.search(p, model_id, re.IGNORECASE) for p in IMAGE_OUTPUT_MODEL_PATTERNS
    )

    if has_audio:
        input_mods = ["text", "image", "audio"]
        reason = "Audio + Vision (Pattern-/Text-Match)"
    elif has_vision:
        input_mods = ["text", "image"]
        reason = "Vision (Pattern-/Text-Match)"
    else:
        input_mods = ["text"]
        reason = "Text-only (kein Vision-Indikator)"

    if has_image_output:
        output_mods = ["text", "image"]
    else:
        output_mods = ["text"]

    return input_mods, output_mods, reason


def backfill_card(path: Path, apply: bool = False) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    changes: list[str] = []
    name = data.get("display_name", data.get("model_id", path.stem))

    in_mods, out_mods, reason = derive_modalities(data)
    if out_mods is None:
        return []  # Skip — bereits gesetzt

    # input_modalities
    if data.get("input_modalities") is None:
        changes.append(f"{name}: input_modalities={in_mods} (Grund: {reason})")
        if apply:
            data["input_modalities"] = in_mods

    # output_modalities
    if data.get("output_modalities") is None:
        changes.append(f"{name}: output_modalities={out_mods}")
        if apply:
            data["output_modalities"] = out_mods

    if apply and changes:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill für Modalitäten-Felder")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--file", type=str, help="Nur eine einzelne Datei")
    args = parser.parse_args()
    apply = args.apply
    if apply:
        args.dry_run = False

    if args.file:
        paths = [Path(args.file)]
    else:
        if not CARDS_DIR.exists():
            print(f"ERROR: {CARDS_DIR} nicht gefunden.", file=sys.stderr)
            return 2
        paths = sorted(CARDS_DIR.glob("*.json"))

    total_changes = 0
    cards_changed = 0
    skipped = 0
    for path in paths:
        if path.name == "_index.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue

        # Schon beides gesetzt? Skip
        if data.get("input_modalities") is not None and data.get("output_modalities") is not None:
            skipped += 1
            continue

        changes = backfill_card(path, apply=apply)
        if changes:
            cards_changed += 1
            total_changes += len(changes)
            for change in changes:
                prefix = "APPLY" if apply else "DRY-RUN"
                print(f"  [{prefix}] {change}")

    mode = "ANGEWENDET" if apply else "DRY-RUN"
    print(f"\n{mode}: {total_changes} Änderungen in {cards_changed} Karten ({skipped} bereits komplett)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
