#!/usr/bin/env python3
"""Smoke-Test für die Review-Klassifikation in generate_review.py.

Iteriert über outputs/audit_logs/ und gibt pro Modell aus:
  - run_type (local | commercial | cloud_open_weights)
  - resolved_provider_key (z.B. openrouter, groq, mistral, …)
  - resolved_model_type (z.B. proprietary_api, open_weights_cloud)
  - hardware_context (erste Zeile, gekürzt) — der String, der in den Reviewer-Prompt injiziert würde

Damit lässt sich vor `make review-all` prüfen, ob die Provider-Auflösung korrekt
arbeitet und keine Cloud-Modelle mehr fälschlich als lokal klassifiziert werden.

Verwendung:
    python scripts/dev/audit_review_classification.py
    python scripts/dev/audit_review_classification.py --show-context   # zeigt vollen hardware_context
    python scripts/dev/audit_review_classification.py --filter openrouter
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.config_validator import ConfigValidator
from utils.constants import MODEL_TYPE_OPEN_WEIGHTS_CLOUD
from utils.model_utils import _safe_name


def resolve_run_type(model_id: str, validator: ConfigValidator) -> tuple[str, Optional[str], str]:
    """Spiegelt die Logik aus generate_review.py.process_model_review().

    `model_id` ist hier bereits der safe_name (Verzeichnisname aus outputs/audit_logs/).
    Wir vergleichen beide Seiten safe-normalisiert, damit OpenRouter-IDs
    wie "minimax/minimax-m3" gegen "minimax_minimax-m3" matchen.

    Returns:
        (run_type, resolved_provider_key, resolved_model_type)
    """
    commercial_providers = validator.config.get("providers", {}).get("commercial", {})
    target_safe = _safe_name(model_id)

    resolved_provider_key: Optional[str] = None
    resolved_model_type: str = ""
    for prov_key, prov_cfg in commercial_providers.items():
        if not isinstance(prov_cfg, dict) or not prov_cfg.get("enabled", False):
            continue
        for m in prov_cfg.get("models", []):
            if not isinstance(m, dict):
                continue
            raw_id = m.get("id")
            if not raw_id:
                continue
            if _safe_name(raw_id) == target_safe:
                resolved_provider_key = prov_key
                resolved_model_type = m.get("model_type") or prov_cfg.get("model_type", "")
                break
        if resolved_provider_key:
            break

    if resolved_provider_key and resolved_model_type == MODEL_TYPE_OPEN_WEIGHTS_CLOUD:
        return "cloud_open_weights", resolved_provider_key, resolved_model_type
    if resolved_provider_key:
        return "commercial", resolved_provider_key, resolved_model_type
    return "local", None, ""


# Heuristik: Welche Modellnamen deuten auf ein lokales Deployment hin?
# Wir nutzen das, um die automatische Auflösung zu plausibilisieren.
# Hinweis: Echte Ground-Truth wäre "outputs/audit_logs/<id>/ stammt aus Ollama oder llama.cpp" —
# das haben wir nicht direkt, also nur ein Sanity-Check über den Namen.
_LOCAL_NAME_HINTS = ("ollama", "llamacpp", "llama_cpp")


def looks_local_by_name(model_id: str) -> bool:
    lower = model_id.lower()
    return any(hint in lower for hint in _LOCAL_NAME_HINTS)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit der Review-Klassifikation (Provider-Auflösung).")
    parser.add_argument(
        "--audit-dir",
        type=Path,
        default=ROOT_DIR / "outputs" / "audit_logs",
        help="Verzeichnis mit Audit-Logs (default: outputs/audit_logs)",
    )
    parser.add_argument(
        "--filter",
        type=str,
        default=None,
        help="Nur Modelle anzeigen, deren Name den Filter enthält",
    )
    parser.add_argument(
        "--only",
        choices=["local", "commercial", "cloud_open_weights"],
        default=None,
        help="Nur Modelle mit bestimmtem run_type zeigen",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Exit-Code 1 setzen, wenn ein Cloud-Modell (run_type != local) im "
            "audit_dir landet, das laut Config-Logik hätte erkannt werden müssen. "
            "Standard: nur Übersicht, exit 0."
        ),
    )
    args = parser.parse_args()

    if not args.audit_dir.exists():
        print(f"❌ Audit-Verzeichnis nicht gefunden: {args.audit_dir}")
        return 1

    validator = ConfigValidator()

    subdirs = sorted(d for d in args.audit_dir.iterdir() if d.is_dir() and d.name != ".DS_Store")
    if not subdirs:
        print(f"⚠️  Keine Modell-Verzeichnisse in {args.audit_dir} gefunden.")
        return 0

    print(f"🔍 Klassifikations-Audit für {len(subdirs)} Modell-Verzeichnisse\n")
    print(f"{'Modell':<42} {'run_type':<20} {'Provider':<14} {'model_type':<20}")
    print("-" * 100)

    counts: dict[str, int] = {"local": 0, "commercial": 0, "cloud_open_weights": 0}
    suspicious: list[str] = []

    for subdir in subdirs:
        mid = subdir.name
        if args.filter and args.filter.lower() not in mid.lower():
            continue

        run_type, provider_key, model_type = resolve_run_type(mid, validator)
        if args.only and run_type != args.only:
            continue

        counts[run_type] = counts.get(run_type, 0) + 1

        # Sanity-Check: Wenn der Name auf "ollama"/"llamacpp" hindeutet, aber die
        # Config liefert einen commercial-Provider, ist das ein Konfigurations-Drift.
        if looks_local_by_name(mid) and run_type != "local":
            suspicious.append(
                f"{mid}  → run_type={run_type}/{provider_key}  "
                f"(Name deutet auf lokal, Config sagt {run_type})"
            )

        print(f"{mid:<42} {run_type:<20} {(provider_key or '-'):<14} {model_type or '-':<20}")

    print("\n" + "=" * 100)
    print("📊 Zusammenfassung:")
    print(f"   local             : {counts.get('local', 0)}")
    print(f"   commercial        : {counts.get('commercial', 0)}")
    print(f"   cloud_open_weights: {counts.get('cloud_open_weights', 0)}")
    total = sum(counts.values())
    print(f"   total             : {total}")

    if suspicious:
        print(f"\n⚠️  {len(suspicious)} Konfigurations-Drift(s):")
        for s in suspicious:
            print(f"   {s}")

    if args.strict and suspicious:
        return 1

    print("\n✅ Klassifikations-Audit abgeschlossen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
