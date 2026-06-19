#!/usr/bin/env python3
"""create_model_card.py — Legt eine neue Model Card aus provider_config.yaml an.

Verwendung:
    # Standard: Skeleton aus Template + Pre-Fill aus provider_config.yaml
    .venv/bin/python scripts/dev/create_model_card.py --model claude-sonnet-4-6

    # Vorschau ohne Schreiben
    .venv/bin/python scripts/dev/create_model_card.py --model claude-sonnet-4-6 --dry-run

    # Provider-Key explizit (sonst Auto-Detect)
    .venv/bin/python scripts/dev/create_model_card.py --model claude-sonnet-4-6 --provider anthropic

Verhalten:
- Validiert die Model-ID (Schutz vor Slug-Mismatch-Bug bei Punkten).
- Sucht die Model-ID in ``config/provider_config.yaml`` (via ConfigValidator).
  Falls gefunden: ``name`` -> ``display_name``, ``<provider.name>`` -> ``developer``.
- Ruft ``utils.card_utils.ensure_card()`` auf (SSoT fuer Skeleton-Erstellung,
  inkl. ``profile_verified=False`` Lock-Default).
- Aktualisiert display_name / developer, falls sie aus provider_config ermittelt
  wurden (ueberschreibt nur, wenn aktueller Wert == ``"TODO"``).
- Schreibt nichts, wenn die Card bereits existiert (use ``make card-research``
  bzw. ``make card-validate`` fuer Updates).
- Bei ``--dry-run`` wird nur der Plan ausgegeben.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.card_template import rebuild_card_index  # noqa: E402
from utils.card_utils import ensure_card, load_taxonomy  # noqa: E402
from utils.config_validator import ConfigValidator  # noqa: E402
from utils.model_utils import _card_path  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("create_model_card")


def _validate_id(model_id: str) -> None:
    """Prueft die Model-ID auf Slug-Mismatch-Risiken.

    Punkte (``.``) fuehren zu Dateinamen-Konflikten weil ``_safe_name`` sie
    zu Underscores konvertiert — eine Card mit ``z-ai/glm-5.2`` wird zu
    ``z-ai_glm-5_2.json``. Slashes sind als Namespace-Trenner erlaubt.
    Doppelpunkte (Ollama-Tag-Schema, z.B. ``qwen2.5:14b``) sind ebenfalls
    erlaubt, weil ``_safe_name`` und ``_card_path`` das korrekt behandeln.
    """
    if not model_id:
        raise SystemExit("❌ Model-ID darf nicht leer sein.")
    if "." in model_id:
        raise SystemExit(
            f"❌ Card-ID '{model_id}' enthaelt einen Punkt. "
            "Punkte verursachen Slug-Mismatches zwischen API-IDs "
            "(vendor/model-v1) und Dateinamen (vendor_model-v1). "
            "Bitte verwende Slashes fuer Vendor-Präfixe "
            "(z.B. 'z-ai/glm-5.2' statt 'z-ai.glm-5.2') "
            "oder fuege einen Alias via heritage_ids hinzu."
        )


def _lookup_provider_info(
    config: dict[str, Any], model_id: str
) -> tuple[str | None, str | None, str | None]:
    """Sucht die Model-ID in providers.commercial / providers.local.

    Returns:
        (provider_key, display_name, developer) — alle None wenn nicht gefunden.
    """
    providers = config.get("providers", {})
    for section_key in ("commercial", "local"):
        section = providers.get(section_key, {})
        if not isinstance(section, dict):
            continue
        for prov_key, prov_cfg in section.items():
            if not isinstance(prov_cfg, dict):
                continue
            for model in prov_cfg.get("models", []) or []:
                if not isinstance(model, dict):
                    continue
                if model.get("id") == model_id:
                    return (
                        f"{section_key}/{prov_key}",
                        model.get("name"),
                        prov_cfg.get("name"),
                    )
    return None, None, None


def _known_vendor_set() -> set[str]:
    """Lädt die kanonischen Vendor-Namen aus der Taxonomie."""
    try:
        taxonomy = load_taxonomy()
        return set(taxonomy.get("manufacturers", {}).get("values", {}).keys())
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.warning(
            "Taxonomie nicht verfügbar (%s) — Vendor-Prüfung übersprungen.",
            exc,
        )
        return set()


def _post_fill_card(card_path: Path, display_name: str | None, developer: str | None) -> bool:
    """Ueberschreibt display_name / developer falls aktueller Wert == 'TODO'.

    Returns:
        True wenn die Card aktualisiert wurde.
    """
    try:
        card = json.loads(card_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Kann bestehende Card nicht lesen: %s", exc)
        return False

    changed = False
    if display_name and card.get("display_name") == "TODO":
        card["display_name"] = display_name
        changed = True
    if developer and card.get("developer") == "TODO":
        card["developer"] = developer
        changed = True

    if changed:
        card_path.write_text(
            json.dumps(card, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return changed


def _sample_model_ids(config: dict[str, Any]) -> list[str]:
    """Sammelt verfuegbare Model-IDs aus provider_config fuer Fehlermeldungen."""
    ids: list[str] = []
    for section in ("commercial", "local"):
        section_cfg = config.get("providers", {}).get(section, {})
        if not isinstance(section_cfg, dict):
            continue
        for prov_cfg in section_cfg.values():
            if isinstance(prov_cfg, dict):
                for model in prov_cfg.get("models", []) or []:
                    if isinstance(model, dict) and model.get("id"):
                        ids.append(model["id"])
    return sorted(set(ids))[:10]


def _raise_no_match_error(model_id: str, config: dict[str, Any]) -> None:
    """Wirft einen SystemExit mit Beispiel-IDs wenn das Modell nicht in der Config ist."""
    sample = ", ".join(_sample_model_ids(config))
    raise SystemExit(
        f"❌ Model '{model_id}' nicht in config/provider_config.yaml gefunden.\n"
        f"   Beispiele verfuegbarer IDs: {sample}"
    )


def _check_existing_card(target_path: Path, yes: bool) -> None:
    """Wirft SystemExit wenn die Card existiert und --yes nicht gesetzt ist."""
    if not target_path.exists():
        return
    msg = f"⚠️  Card existiert bereits: {target_path}"
    if yes:
        logger.warning("%s — wird trotzdem ueberschrieben (--yes).", msg)
        return
    raise SystemExit(
        f"{msg}\n"
        "   Verwende 'make card-research' fuer inhaltliche Updates "
        "oder 'make card-validate' fuer Struktur-Sync.\n"
        "   Mit '--yes' wird die bestehende Card ueberschrieben."
    )


def main() -> int:  # noqa: C901 — Komplexitaet akzeptabel nach Split in Hilfefunktionen
    parser = argparse.ArgumentParser(
        description=(
            "Legt eine neue Model Card aus provider_config.yaml an. "
            "Skeleton via SSoT (utils.card_utils.ensure_card) + "
            "Pre-Fill aus config/provider_config.yaml."
        ),
    )
    parser.add_argument("--model", required=True, help="Model-ID (z.B. claude-sonnet-4-6).")
    parser.add_argument(
        "--provider",
        help=(
            "Provider-Key fuer ensure_card (z.B. anthropic, ollama). "
            "Optional — wird sonst aus provider_config ermittelt oder "
            "weggelassen (Default-Pfad)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Vorschau — keine Card schreiben.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Bestaetigung fuer vorhandene Cards uebergehen (ohne diesen Flag: SystemExit).",
    )
    args = parser.parse_args()

    _validate_id(args.model)

    # Provider-Lookup via ConfigValidator (SSoT fuer benchmark + provider_config)
    try:
        config = ConfigValidator().config
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        raise SystemExit(f"❌ ConfigValidator fehlgeschlagen: {exc}") from exc

    provider_key, display_name, developer = _lookup_provider_info(config, args.model)

    # Hersteller (developer) gegen Taxonomy-Mapping pruefen (exact match).
    # Wenn developer NICHT in den kanonischen Vendor-Namen steht, bleibt der
    # Wert stehen (kein Mapping-Fuzzy) — der Operator entscheidet manuell.
    if developer:
        known_vendors = _known_vendor_set()
        if known_vendors and developer not in known_vendors:
            logger.info(
                "ℹ️  Hersteller '%s' ist nicht in classification_taxonomy.json#manufacturers. "
                "Bleibt als display-Wert stehen.",
                developer,
            )

    if provider_key is None and display_name is None:
        _raise_no_match_error(args.model, config)

    # Pfad bestimmen (schreibt nicht)
    try:
        target_path = _card_path(args.model, provider=args.provider, for_write=True)
    except (ValueError, FileNotFoundError, OSError) as exc:
        raise SystemExit(f"❌ Pfad-Aufloesung fehlgeschlagen: {exc}") from exc

    logger.info("Modell:        %s", args.model)
    logger.info("Provider:      %s", provider_key or "(kein Match)")
    logger.info("display_name:  %s", display_name or "(TODO)")
    logger.info("developer:     %s", developer or "(TODO)")
    logger.info("Pfad:          %s", target_path)

    _check_existing_card(target_path, args.yes)

    if args.dry_run:
        logger.info("[DRY-RUN] Wuerde Card anlegen.")
        return 0

    # Skeleton via SSoT — erzeugt alle Template-Felder + provider-Konflikt-Resolver.
    try:
        ensure_card(args.model, provider=args.provider)
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"❌ ensure_card fehlgeschlagen: {exc}") from exc

    # Pre-Fill: display_name / developer ueberschreiben (nur falls TODO).
    updated = _post_fill_card(target_path, display_name, developer)
    if updated:
        logger.info("✅ Pre-Fill angewendet: display_name / developer.")
    else:
        logger.info("ℹ️  Keine Pre-Fill-Aenderung noetig (Werte bereits gesetzt).")

    rebuild_card_index("model")
    logger.info("✅ Card erstellt: %s", target_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
