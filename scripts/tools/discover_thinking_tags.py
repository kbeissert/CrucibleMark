#!/usr/bin/env python3
"""
Discovery-Skript: Thinking-Tag-Inventar pro Modell-Familie
============================================================

Liest config/provider_config.yaml, waehlt pro Familie 1-2 Repraesentanten
aus, sendet die 3 Probe-Prompts (math/code/decision) und schreibt die
Ergebnisse in docs/THINKING_TAGS_INVENTORY.md.

Read-only: Schreibt KEINE Model Cards. Fuer Card-Updates das bestehende
scripts/tools/probe_thinking.py verwenden.

Verwendung
----------
    # Alle Familien proben
    .venv/bin/python scripts/tools/discover_thinking_tags.py

    # Nur bestimmte Familien
    .venv/bin/python scripts/tools/discover_thinking_tags.py --families Gemma Qwen

    # Nur lokale Modelle (MacBook Pro / DGX Spark)
    .venv/bin/python scripts/tools/discover_thinking_tags.py --provider llamacpp

    # Pro Familie 2 statt 1 Repraesentant
    .venv/bin/python scripts/tools/discover_thinking_tags.py --max-per-family 2

    # Custom Output-Pfad
    .venv/bin/python scripts/tools/discover_thinking_tags.py --output /tmp/probe.md
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.llm_client import LLMClient  # noqa: E402
from utils.model_utils import (  # noqa: E402
    _PROBE_MAX_TOKENS,
    _PROBE_PROMPTS,
    _THINK_TAGS,
    _has_inline_cot,
    _find_think_tags,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CONFIG_PATH = ROOT_DIR / "benchmark_config.yaml"
PROVIDER_CONFIG_PATH = ROOT_DIR / "config" / "provider_config.yaml"
DEFAULT_OUTPUT = ROOT_DIR / "docs" / "THINKING_TAGS_INVENTORY.md"

# Provider-Prioritaet: lokal > openrouter > rest
_LOCAL_PRIORITY = {"llamacpp": 0, "llamacpp_spark": 1, "vllm_spark": 2, "ollama": 3, "ollama_local": 4}
_CLOUD_PRIORITY = {"openrouter": 0, "groq": 1}


# ---------------------------------------------------------------------------
# Familien-Identifikation
# ---------------------------------------------------------------------------
def identify_family(model_id: str) -> str:
    """Identifiziert die Modell-Familie anhand der ID."""
    mid = model_id.lower()
    # Reihenfolge wichtig: spezifischere Marker zuerst
    if "magistral" in mid:
        return "Magistral"
    if "devstral" in mid:
        return "Devstral"
    if "codestral" in mid:
        return "Codestral"
    if "gemma" in mid:
        return "Gemma"
    if "qwen" in mid and "coder" in mid:
        return "Qwen-Coder"
    if "qwen" in mid:
        return "Qwen"
    if "hermes" in mid:
        return "Hermes"
    if "llama" in mid or "meta-llama" in mid:
        return "Llama"
    if any(t in mid for t in ("mistral", "mixtral", "ministral")):
        return "Mistral"
    if "claude" in mid:
        return "Claude"
    if "gpt-" in mid or mid.startswith("o1") or mid.startswith("o3") or mid.startswith("o4"):
        return "OpenAI"
    if "gemini" in mid:
        return "Gemini"
    if "grok" in mid:
        return "Grok"
    if "deepseek" in mid:
        return "DeepSeek"
    if "glm" in mid:
        return "GLM"
    if "kimi" in mid:
        return "Kimi"
    if "nemotron" in mid:
        return "NVIDIA"
    if "minimax" in mid:
        return "MiniMax"
    if "lfm" in mid:
        return "Liquid"
    if "phi" in mid:
        return "Phi"
    return "Other"


# ---------------------------------------------------------------------------
# Config + Modell-Sammlung
# ---------------------------------------------------------------------------
def load_merged_config() -> dict[str, Any]:
    """Laedt benchmark_config.yaml + provider_config.yaml, provider_config hat Vorrang."""
    cfg: dict[str, Any] = {}
    for path in (CONFIG_PATH, PROVIDER_CONFIG_PATH):
        if not path.exists():
            continue
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for section in ("providers", "defaults", "local", "modules", "reasoning"):
            if section in data:
                cfg.setdefault(section, {})
                if isinstance(data[section], dict):
                    for k, v in data[section].items():
                        cfg[section][k] = v
    return cfg


def _is_ollama_cloud_model(entry: dict[str, Any]) -> bool:
    """Prueft, ob ein Provider-Eintrag via Ollama-Cloud-Proxy laeuft."""
    if "api_type" in entry and entry["api_type"] == "ollama":
        # ollama_cloud nutzt :cloud-Tags, hat auto_discover
        return bool(entry.get("auto_discover")) and entry.get("enabled", False)
    return False


def collect_models_by_family(
    config: dict[str, Any],
    families_filter: set[str] | None = None,
    provider_filter: str | None = None,
) -> dict[str, list[tuple[str, str]]]:
    """Sammelt alle Modelle pro Familie: {family: [(model_id, provider_key), ...]}."""
    by_family: dict[str, list[tuple[str, str]]] = {}
    providers = config.get("providers", {})

    for section in ("local", "commercial"):
        section_cfg = providers.get(section, {})
        if not isinstance(section_cfg, dict):
            continue
        for prov_key, prov_cfg in section_cfg.items():
            if not isinstance(prov_cfg, dict):
                continue
            if provider_filter and prov_key != provider_filter:
                continue
            if not prov_cfg.get("enabled", True):
                continue
            for m in prov_cfg.get("models", []):
                if not isinstance(m, dict):
                    continue
                mid = m.get("id")
                if not mid:
                    continue
                fam = identify_family(mid)
                if families_filter and fam not in families_filter:
                    continue
                by_family.setdefault(fam, []).append((mid, prov_key))

    return by_family


def pick_representatives(
    by_family: dict[str, list[tuple[str, str]]],
    max_per_family: int = 1,
) -> list[tuple[str, str, str]]:
    """Waehlt max_per_family Modelle pro Familie aus.

    Prioritaet:
    1. Lokale Modelle (llamacpp > llamacpp_spark > vllm_spark > ollama) — schnell, kostenlos
    2. OpenRouter (breiteste Coverage, oft mit "thinking"-Variante)
    3. Direkt-API (mistral, anthropic, openai, google, xai) — niedrigste Prio
    """
    def sort_key(item: tuple[str, str]) -> tuple[int, int, str]:
        mid, prov = item
        section_prio = 0 if prov in _LOCAL_PRIORITY else (1 if prov in _CLOUD_PRIORITY else 2)
        prov_prio = _LOCAL_PRIORITY.get(prov, _CLOUD_PRIORITY.get(prov, 99))
        # Bevorzuge Modelle mit "thinking"/"reasoning" im Namen
        thinking_bonus = 0 if any(t in mid.lower() for t in ("thinking", "reasoning")) else 1
        return (section_prio, prov_prio + thinking_bonus, mid)

    out: list[tuple[str, str, str]] = []
    for family, models in by_family.items():
        if not models:
            continue
        sorted_models = sorted(models, key=sort_key)
        for mid, prov in sorted_models[:max_per_family]:
            out.append((mid, prov, family))
    return out


# ---------------------------------------------------------------------------
# Probe-Logik
# ---------------------------------------------------------------------------
def run_single_probe(
    client: LLMClient,
    model_id: str,
    provider_key: str,
    prompt_name: str,
    prompt_text: str,
) -> dict[str, Any]:
    """Ein einzelner Probe-Call mit roher Antwort und Metadaten."""
    result: dict[str, Any] = {
        "prompt_name": prompt_name,
        "raw": "",
        "raw_len": 0,
        "reasoning_tokens": 0,
        "tags_found": [],
        "inline_cot": False,
        "error": None,
    }
    try:
        raw = client.query(
            model=model_id,
            prompt=prompt_text,
            provider=provider_key,
            max_tokens=_PROBE_MAX_TOKENS,
        )
    except Exception as exc:
        result["error"] = str(exc)
        return result

    result["raw"] = raw
    result["raw_len"] = len(raw)
    result["tags_found"] = list(_find_think_tags(raw))
    result["inline_cot"] = _has_inline_cot(raw)
    metadata = client.last_response_metadata or {}
    result["reasoning_tokens"] = int(metadata.get("reasoning_tokens") or 0)
    return result


def aggregate_probe(probe_results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Aggregiert Multi-Prompt-Ergebnisse zu einer Gesamtempfehlung."""
    detected_prompts = [name for name, r in probe_results.items() if r["error"] is None and (r["tags_found"] or r["inline_cot"] or r["reasoning_tokens"] > 0)]
    all_tags = sorted({t for r in probe_results.values() for t in r["tags_found"]})
    max_reasoning = max((r["reasoning_tokens"] for r in probe_results.values()), default=0)
    inline_cot_prompts = [name for name, r in probe_results.items() if r["inline_cot"]]

    if all_tags:
        confidence = "high"
        detected = True
        signal = f"Tags: {', '.join(all_tags)}"
    elif max_reasoning > 0:
        confidence = "medium"
        detected = True
        signal = f"reasoning_tokens={max_reasoning}"
    elif inline_cot_prompts:
        confidence = "medium"
        detected = True
        signal = f"Inline CoT in: {', '.join(inline_cot_prompts)}"
    else:
        confidence = "low"
        detected = False
        signal = "no signal"

    return {
        "detected": detected,
        "confidence": confidence,
        "signal": signal,
        "detected_prompts": detected_prompts,
        "all_tags": all_tags,
        "max_reasoning_tokens": max_reasoning,
        "inline_cot_prompts": inline_cot_prompts,
    }


def run_probes(
    representatives: list[tuple[str, str, str]],
    config: dict[str, Any],
    *,
    continue_on_error: bool = True,
) -> list[dict[str, Any]]:
    """Pro Modell: 3 Probe-Prompts senden + aggregieren."""
    results: list[dict[str, Any]] = []
    for mid, prov, family in representatives:
        logger.info("Probing %s (%s, %s) ...", mid, family, prov)
        client = LLMClient(config)
        probe_results: dict[str, dict[str, Any]] = {}
        for prompt_name, prompt_text in _PROBE_PROMPTS.items():
            probe_results[prompt_name] = run_single_probe(
                client, mid, prov, prompt_name, prompt_text
            )
        agg = aggregate_probe(probe_results)

        # Fehler-Status: alle Prompts fehlgeschlagen?
        all_errors = all(r["error"] for r in probe_results.values())
        results.append({
            "model_id": mid,
            "provider": prov,
            "family": family,
            "aggregate": agg,
            "probes": probe_results,
            "all_errors": all_errors,
            "first_error": next(
                (r["error"] for r in probe_results.values() if r["error"]),
                None,
            ),
        })
        if all_errors and not continue_on_error:
            raise RuntimeError(f"All probes failed for {mid}")
    return results


# ---------------------------------------------------------------------------
# Markdown-Output
# ---------------------------------------------------------------------------
def _truncate(s: str, n: int = 300) -> str:
    s = s.replace("\n", " ").replace("|", "\\|").strip()
    return s if len(s) <= n else s[:n] + "..."


def render_markdown(
    results: list[dict[str, Any]],
    *,
    run_started: str,
    run_finished: str,
) -> str:
    """Rendert die Probe-Ergebnisse als Markdown-Report."""
    lines: list[str] = []
    lines.append("# Thinking-Tag-Inventar pro Modell-Familie")
    lines.append("")
    lines.append(
        "Automatisch generiert via `scripts/tools/discover_thinking_tags.py` — "
        " **read-only Discovery**, keine Card-Updates."
    )
    lines.append("")
    lines.append(f"- **Lauf-Start:** {run_started}")
    lines.append(f"- **Lauf-Ende:** {run_finished}")
    lines.append(f"- **Modelle insgesamt:** {len(results)}")
    detected_count = sum(1 for r in results if r["aggregate"]["detected"])
    lines.append(f"- **Davon Thinking erkannt:** {detected_count} ({detected_count * 100 // max(len(results), 1)}%)")
    lines.append("")
    lines.append("## Methodik")
    lines.append("")
    lines.append("Pro Modell werden 3 Probe-Prompts gesendet:")
    for name, text in _PROBE_PROMPTS.items():
        lines.append(f"- **{name}**: `{text}`")
    lines.append("")
    lines.append("**Signal-Hierarchie** (Confidence):")
    lines.append("- **high**: Bekannte Think-Tags in Antwort (`<think>`, `<|thinking|>`, `<reflection>`, ...)")
    lines.append("- **medium**: `reasoning_tokens > 0` in Provider-Metadaten ODER Inline-CoT im content-Feld")
    lines.append("- **low**: Kein Signal")
    lines.append("")
    lines.append("**Aktuell bekannte Tag-Liste** (SSoT: `utils/model_utils._THINK_TAGS`):")
    lines.append("")
    lines.append("```python")
    lines.append(f"_THINK_TAGS = {list(_THINK_TAGS)!r}")
    lines.append("```")
    lines.append("")

    # Gruppierung nach Familie
    by_family: dict[str, list[dict[str, Any]]] = {}
    for r in results:
        by_family.setdefault(r["family"], []).append(r)

    for family in sorted(by_family):
        family_results = by_family[family]
        lines.append(f"## {family}")
        lines.append("")

        # Familien-Summary
        family_detected = sum(1 for r in family_results if r["aggregate"]["detected"])
        all_family_tags = sorted({
            t for r in family_results for t in r["aggregate"]["all_tags"]
        })
        lines.append(
            f"**{family_detected}/{len(family_results)} Modelle zeigen Thinking.** "
            f"Gefundene Tags in Familie: {', '.join(all_family_tags) if all_family_tags else '_keine_'}"
        )
        lines.append("")

        # Tabelle pro Familie
        lines.append("| Modell | Provider | Detected | Confidence | Signal | Tags |")
        lines.append("|---|---|---|---|---|---|")
        for r in family_results:
            agg = r["aggregate"]
            if r["all_errors"]:
                lines.append(
                    f"| `{r['model_id']}` | {r['provider']} | ❌ ERROR | - | "
                    f"`{_truncate(r['first_error'] or '?', 50)}` | - |"
                )
            else:
                tags_str = ", ".join(agg["all_tags"]) if agg["all_tags"] else "-"
                detected_icon = "✅" if agg["detected"] else "❌"
                lines.append(
                    f"| `{r['model_id']}` | {r['provider']} | {detected_icon} | "
                    f"{agg['confidence']} | `{_truncate(agg['signal'], 60)}` | {tags_str} |"
                )
        lines.append("")

        # Roh-Antwort pro Modell (gekuerzt)
        lines.append("<details>")
        lines.append("<summary>Roh-Antworten (gekuerzt auf 300 chars/Prompt)</summary>")
        lines.append("")
        for r in family_results:
            if r["all_errors"]:
                continue
            lines.append(f"### `{r['model_id']}` ({r['provider']})")
            lines.append("")
            for prompt_name, probe in r["probes"].items():
                if probe["error"]:
                    lines.append(f"- **{prompt_name}** ❌ ERROR: `{_truncate(probe['error'], 80)}`")
                else:
                    preview = _truncate(probe["raw"], 300)
                    lines.append(f"- **{prompt_name}** ({probe['raw_len']} chars, "
                                 f"tags={probe['tags_found']}, reasoning_t={probe['reasoning_tokens']}, "
                                 f"inline_cot={probe['inline_cot']}):")
                    lines.append("  ```")
                    lines.append(f"  {preview}")
                    lines.append("  ```")
            lines.append("")
        lines.append("</details>")
        lines.append("")

    # Familien-uebergreifende Statistik
    lines.append("## Cross-Family Statistik")
    lines.append("")
    lines.append("| Familie | Modelle | Thinking erkannt | Anteil | Typische Tags |")
    lines.append("|---|---|---|---|---|")
    for family in sorted(by_family):
        family_results = by_family[family]
        n = len(family_results)
        det = sum(1 for r in family_results if r["aggregate"]["detected"])
        tags = sorted({t for r in family_results for t in r["aggregate"]["all_tags"]})
        lines.append(
            f"| {family} | {n} | {det} | {det * 100 // max(n, 1)}% | "
            f"{', '.join(tags) if tags else '_-_'} |"
        )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover Thinking-Tag-Patterns pro Modell-Familie.",
    )
    parser.add_argument(
        "--families",
        nargs="+",
        default=None,
        help="Nur diese Familien proben (z.B. --families Gemma Qwen Hermes)",
    )
    parser.add_argument(
        "--provider",
        default=None,
        help="Nur Modelle dieses Providers (z.B. llamacpp, openrouter)",
    )
    parser.add_argument(
        "--max-per-family",
        type=int,
        default=1,
        help="Max Modelle pro Familie (default: 1)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output-Pfad (default: {DEFAULT_OUTPUT.relative_to(ROOT_DIR)})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur Config-Inventur anzeigen, keine Probe-Calls",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Bei erstem Fehler abbrechen (default: continue)",
    )
    args = parser.parse_args()

    run_started = datetime.now(UTC).isoformat()
    config = load_merged_config()
    families_filter = set(args.families) if args.families else None

    by_family = collect_models_by_family(
        config,
        families_filter=families_filter,
        provider_filter=args.provider,
    )
    if not by_family:
        print("Keine Modelle gefunden (Filter zu restriktiv?).")
        return

    representatives = pick_representatives(by_family, max_per_family=args.max_per_family)
    print(f"\n{len(representatives)} Repraesentanten aus {len(by_family)} Familien ausgewaehlt:\n")
    for mid, prov, fam in representatives:
        print(f"  - {fam:15s} {prov:15s} {mid}")
    print()

    if args.dry_run:
        print("Dry-Run: keine Probe-Calls.")
        return

    results = run_probes(
        representatives,
        config,
        continue_on_error=not args.fail_fast,
    )

    run_finished = datetime.now(UTC).isoformat()
    markdown = render_markdown(results, run_started=run_started, run_finished=run_finished)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown, encoding="utf-8")

    # Konsole: kurze Zusammenfassung
    print(f"\n{'='*70}")
    try:
        output_rel = args.output.relative_to(ROOT_DIR)
    except ValueError:
        # Output liegt außerhalb von ROOT_DIR (z.B. /tmp/foo.md) — absoluten Pfad zeigen
        output_rel = args.output
    print(f"Fertig: {len(results)} Modelle proben → {output_rel}")
    print(f"{'='*70}")
    detected = sum(1 for r in results if r["aggregate"]["detected"])
    print(f"Thinking erkannt: {detected}/{len(results)}")
    for r in results:
        agg = r["aggregate"]
        if r["all_errors"]:
            print(f"  ❌ {r['model_id']:50s} ERROR: {_truncate(r['first_error'] or '?', 50)}")
        else:
            icon = "🧠" if agg["detected"] else "💬"
            print(f"  {icon} {r['model_id']:50s} {agg['confidence']:6s} {agg['signal']}")


if __name__ == "__main__":
    main()
