"""Model metrics and card context retrieval for the review pipeline."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.model_utils import _find_card
from utils.scoring_utils import normalize_model_name


def _flatten_strings(items: object) -> list[str]:
    """Toleriert flache Listen und versehentlich verschachtelte Wrapper-Schichten
    (z. B. ``[["a", "b"]]`` statt ``["a", "b"]``). Nicht-String-Einträge werden
    stillschweigend übersprungen.
    """
    if not isinstance(items, list):
        return []
    if len(items) == 1 and isinstance(items[0], list):
        return [s for s in items[0] if isinstance(s, str)]
    return [s for s in items if isinstance(s, str)]


def get_model_metrics(model_name: str) -> dict:
    """Read model stats from benchmark_leaderboard_detailed.csv."""
    detailed_csv = ROOT_DIR / "benchmark_scores" / "benchmark_leaderboard_detailed.csv"
    if not detailed_csv.exists():
        return {}

    norm_target = normalize_model_name(model_name)
    norm_target_stripped = re.sub(r"_\d{8}$", "", norm_target)

    def matches(norm_t: str, norm_c: str) -> bool:
        return (
            norm_t == norm_c
            or norm_t.startswith(f"{norm_c}_")
            or norm_t.endswith(f"_{norm_c}")
        )

    try:
        with open(detailed_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                norm_csv = normalize_model_name(row.get("Model ID", row.get("model_id", "")))
                if matches(norm_target, norm_csv) or matches(norm_target_stripped, norm_csv):
                    return row
    except Exception:
        pass
    return {}


def get_model_card_context(model_id: str) -> str:
    """Format model card data as a Markdown context block."""
    card_path = _find_card(model_id)
    if not card_path.exists():
        return ""

    try:
        card = json.loads(card_path.read_text(encoding="utf-8"))
    except Exception:
        return ""

    if card.get("unknown"):
        return ""

    strengths = ", ".join(_flatten_strings(card.get("strengths", [])))
    limitations = ", ".join(_flatten_strings(card.get("known_limitations", [])))
    hint = card.get("judge_context_hint", "")

    arch = card.get("parameter_architecture", "")
    total_b = card.get("params_total_b")
    active_b = card.get("params_active_b")
    if total_b and active_b:
        params_str = f"{total_b}B total / {active_b}B aktiv ({arch})"
    elif total_b:
        params_str = f"{total_b}B ({arch})" if arch else f"{total_b}B"
    elif arch:
        params_str = arch
    else:
        params_str = "unbekannt"

    ctx_k = card.get("context_window_k")
    cutoff = card.get("knowledge_cutoff")
    price_in = card.get("input_price_per_1m")
    price_out = card.get("output_price_per_1m")
    price_str = f"${price_in}/1M input, ${price_out}/1M output" if price_in and price_out else None

    lines = [
        f"### Modell-Info: {card.get('display_name', model_id)}",
        f"- **Entwickler:** {card.get('developer', 'n/a')} ({card.get('origin_country', 'n/a')})",
        f"- **Use Case:** {card.get('use_case_primary', 'n/a')} | "
        f"**Size Class:** {card.get('size_class', 'n/a')} | "
        f"**Parameter:** {params_str}",
    ]
    if ctx_k:
        lines.append(f"- **Kontextfenster:** {ctx_k}K Tokens")
    if cutoff:
        lines.append(f"- **Trainings-Cutoff:** {cutoff}")
    if price_str:
        lines.append(f"- **Preis:** {price_str}")
    # Lizenz-Zeile: weights_license_tier (Kategorie) + konkreter Lizenzname + kommerzielle Nutzung
    license_name = card.get("license")
    commercial = card.get("commercial_use_allowed")
    license_parts = [
        f"**Lizenz-Kategorie:** {card.get('weights_license_tier', 'n/a')}",
        f"**Deployment:** {card.get('deployment_type', 'n/a')}",
    ]
    if license_name:
        license_parts.insert(0, f"**Lizenz:** {license_name}")
    if commercial is not None:
        license_parts.append(f"**Kommerzielle Nutzung:** {'Ja' if commercial else 'Nein'}")
    lines.append(
        f"- **Familie:** {card.get('model_family', 'n/a')} | "
        + " | ".join(license_parts)
    )

    # Weights-Provenienz: explizit für den Reviewer (nicht nur im berechneten Sovereign Risk)
    wprov = card.get("weights_provenance_risk")
    wprov_rationale = card.get("weights_provenance_risk_rationale")
    if wprov:
        lines.append(
            f"- **Weights-Provenienz-Risiko:** `{wprov.upper()}` — {wprov_rationale or '(keine Rationale)'}"
        )

    lines.append(f"- **Zusammenfassung:** {card.get('summary', '')}")
    if strengths:
        lines.append(f"- **Stärken:** {strengths}")
    if limitations:
        lines.append(f"- **Einschränkungen:** {limitations}")
    if hint:
        lines.append(f"- **Bewertungshinweis:** {hint}")

    # Thinking-Probe-Ergebnis: ob das Modell im Benchmark mit Thinking-Tokens arbeitete
    probe_detected = card.get("thinking_probe_detected")
    probe_conf = card.get("thinking_probe_confidence")
    cot_family = card.get("cot_marker_family")
    if probe_detected is not None:
        probe_str = f"{'Ja' if probe_detected else 'Nein'} (Konfidenz: {probe_conf or 'n/a'})"
        if cot_family:
            probe_str += f" | CoT-Familie: `{cot_family}`"
        lines.append(f"- **Thinking-Probe:** {probe_str}")

    return "\n".join(lines)


def format_classification_context(
    use_case: str, size_class: str, param_arch: str, taxonomy: dict
) -> str:
    """Render taxonomy as Markdown tables with the model's values highlighted."""
    lines: list[str] = []

    use_case_def = taxonomy.get("use_case", {})
    size_class_def = taxonomy.get("size_class", {})
    param_arch_def = taxonomy.get("parameter_architecture", {})

    lines.append("#### Use-Case-Klassifikation (Optimierungsschwerpunkt)")
    lines.append("")
    lines.append("| Marker | Use Case | Beschreibung | Reviewer-Hinweis |")
    lines.append("|---|---|---|---|")
    for key, entry in use_case_def.get("values", {}).items():
        marker = "▶ **DIESES MODELL**" if key == use_case else ""
        label = f"**{entry['label']}**" if key == use_case else entry["label"]
        lines.append(f"| {marker} | {label} | {entry['description']} | {entry['reviewer_guidance']} |")

    lines.append("")
    lines.append("#### Size-Class-Klassifikation (Hardware-Tier)")
    lines.append("")
    lines.append("| Marker | Size Class | Beschreibung | Reviewer-Hinweis |")
    lines.append("|---|---|---|---|")
    for key, entry in size_class_def.get("values", {}).items():
        marker = "▶ **DIESES MODELL**" if key == size_class else ""
        label = f"**{entry['label']}**" if key == size_class else entry["label"]
        lines.append(f"| {marker} | {label} | {entry['description']} | {entry['reviewer_guidance']} |")

    lines.append("")
    lines.append("#### Parameter-Architektur (Strukturprinzip)")
    lines.append("")
    lines.append("| Marker | Architektur | Beschreibung | Reviewer-Hinweis |")
    lines.append("|---|---|---|---|")
    for key, entry in param_arch_def.get("values", {}).items():
        marker = "▶ **DIESES MODELL**" if key == param_arch else ""
        label = f"**{entry['label']}**" if key == param_arch else entry["label"]
        lines.append(f"| {marker} | {label} | {entry['description']} | {entry['reviewer_guidance']} |")

    lines.append("")
    lines.append(
        f"**Einordnung dieses Modells:** `use_case_primary = {use_case}` | "
        f"`size_class = {size_class}` | `parameter_architecture = {param_arch}`"
    )

    return "\n".join(lines)
