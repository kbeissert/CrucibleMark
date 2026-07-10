#!/usr/bin/env python3
"""
Reasoning-Erkennung (Thinking-Probe)
=====================================
Führt empirische Reasoning-Erkennung für ein oder mehrere Modelle durch
und schreibt das Ergebnis direkt in die jeweilige Model Card.

Verwendung:
    # Einzelnes Modell proben (Provider aus config ableiten)
    .venv/bin/python scripts/tools/probe_thinking.py --model moonshotai/kimi-k2.5

    # Alle Cards ohne Probe-Feld aktualisieren
    .venv/bin/python scripts/tools/probe_thinking.py --missing

    # Alle bekannten Cards (auch bestehende Probe-Felder überschreiben)
    .venv/bin/python scripts/tools/probe_thinking.py --all

    # Mit explizitem Provider
    .venv/bin/python scripts/tools/probe_thinking.py --model qwen3:14b --provider ollama
"""

import argparse
import json
import logging
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.card_utils import ensure_card
from utils.config_validator import ConfigValidator
from utils.model_utils import (
    ThinkingProbeResult,
    _find_card,
    probe_thinking_model,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CARDS_DIR = ROOT_DIR / "benchmark_scores" / "model_cards"


def _load_config() -> dict[str, Any]:
    """Lädt benchmark_config.yaml + provider_config.yaml (gemerged).

    Delegiert an ``ConfigValidator`` (SSoT für den Config-Merge inkl.
    Fehlerbehandlung + Duplicate-ID-Warnung). Ohne diesen Merge fehlen
    vllm_spark/llamacpp_spark-Provider-Configs (``base_url``/``server_start_cmd``)
    → Probe-Script defaultet auf ``127.0.0.1`` und hält endlos im
    Cold-Start-Wait fest.
    """
    return ConfigValidator(str(ROOT_DIR / "benchmark_config.yaml")).config


def _infer_provider(model_id: str, config: dict[str, Any]) -> str:
    """
    Leitet den Provider aus der Config ab. Heuristik:
      - Config-Lookup zuerst (exakter Treffer in providers.commercial)
      - model_id enthält '/' → Cloud-Modell, Fallback openrouter
      - model_id enthält ':' aber kein '/' → Ollama-Format (name:tag)
      - Kein Separator → check Config, Fallback Ollama
    """
    commercial = config.get("providers", {}).get("commercial", {})
    for provider_key, provider_cfg in commercial.items():
        for model in provider_cfg.get("models", []):
            if model.get("id") == model_id:
                return provider_key

    # Modell-ID hat '/' → sicheres Zeichen für Cloud-Modell
    if "/" in model_id:
        return "openrouter"

    # Ollama-Format: 'name:tag' oder nur 'name' ohne Slash
    return "ollama"


def _probe_fields_to_dict(probe: ThinkingProbeResult) -> dict[str, Any]:
    from utils.model_utils import classify_cot_marker_family

    fields: dict[str, Any] = {
        "thinking_probe_detected": probe.detected,
        "thinking_probe_evidence": probe.evidence,
        "thinking_probe_confidence": probe.confidence,
        "thinking_probe_at": datetime.now(UTC).isoformat(),
    }
    # v4.7.1 CoT-Quartett: Marker-Familie + Tag-Liste nur setzen, wenn
    # tatsaechlich Tags gefunden wurden. Sonst bleiben die Felder null
    # (verhindert noise im Web-Export).
    if probe.tags_found:
        fields["cot_marker_family"] = classify_cot_marker_family(probe.tags_found)
        fields["cot_tags_detected"] = list(probe.tags_found)
    return fields


def _write_probe_to_card(
    model_id: str,
    probe: ThinkingProbeResult,
    *,
    provider: str | None = None,
) -> Path:
    """Schreibt Probe-Ergebnis in Card (vollständige Struktur wird sichergestellt).

    Bestehende Cards werden **in place** aktualisiert: ``_find_card`` löst die
    SUFFIX-Form (``--VSPK``/``--SPRK``/…) auf und ``ensure_card(card_path=...)``
    überschreibt diese ohne Unique-ID-Resolver (der nur für Neuerstellung
    gedacht ist und sonst ``-2``-Duplikate erzeugt). Fehlt die Card komplett,
    wird sie via ``ensure_card(provider=...)`` mit korrektem SUFFIX angelegt.
    """
    existing_path = _find_card(model_id)
    if existing_path.exists():
        card_path = ensure_card(model_id, card_path=existing_path)
    else:
        card_path = ensure_card(model_id, provider=provider)

    probe_fields = _probe_fields_to_dict(probe)

    card: dict[str, Any] = json.loads(card_path.read_text(encoding="utf-8"))
    card.update(probe_fields)

    # Thinking-Tag in architecture_tags setzen wenn erkannt und noch nicht vorhanden
    if probe.detected:
        tags: list[str] = card.get("architecture_tags") or []
        if "Thinking" not in tags:
            card["architecture_tags"] = ["Thinking"] + [t for t in tags if t != "General"]

    card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2), encoding="utf-8")
    return card_path


def run_probe(
    model_id: str,
    provider_key: str,
    config: dict[str, Any],
    force: bool = False,
) -> bool:
    """
    Führt den Probe für ein Modell aus und schreibt das Ergebnis in die Card.

    Args:
        model_id:     Modell-ID
        provider_key: Provider-Key (z.B. 'ollama', 'openrouter', 'anthropic')
        config:       Vollständige benchmark_config
        force:        Bestehende Probe-Felder überschreiben

    Returns:
        True wenn Probe erfolgreich, False bei Fehler
    """
    # SUFFIX-SSoT: _find_card findet provider-spezifische Cards (SPRK/VSPK/…)
    # ohne expliziten Provider. Die alte {safe}.json-Logik traf nur unprefixed
    # Cards und übersah --VSPK/--SPRK-Varianten (Skip-Check falsch-negativ).
    card_path = _find_card(model_id)

    if not force and card_path.exists():
        try:
            existing = json.loads(card_path.read_text(encoding="utf-8"))
            if "thinking_probe_detected" in existing:
                logger.info(
                    "⏭  Übersprungen (Probe-Feld vorhanden): %s "
                    "(detected=%s, confidence=%s)",
                    model_id,
                    existing["thinking_probe_detected"],
                    existing.get("thinking_probe_confidence", "?"),
                )
                return True
        except Exception:
            pass

    logger.info("🔍 Reasoning-Erkennung: %s via %s …", model_id, provider_key)
    try:
        probe = probe_thinking_model(model_id, provider_key, config)
    except RuntimeError as e:
        logger.error("❌ Probe fehlgeschlagen für '%s': %s", model_id, e)
        return False

    card_path = _write_probe_to_card(model_id, probe, provider=provider_key)
    icon = "🧠" if probe.detected else "💬"
    try:
        display_path = card_path.resolve().relative_to(ROOT_DIR)
    except ValueError:
        display_path = card_path
    logger.info(
        "%s  %s → detected=%s (confidence=%s)\n   Evidence: %s\n   Card: %s",
        icon,
        model_id,
        probe.detected,
        probe.confidence,
        probe.evidence[:120],
        display_path,
    )
    return True


def _collect_all_card_models() -> list[str]:
    """Gibt alle model_ids aus bestehenden Card-JSONs zurück."""
    models: list[str] = []
    for p in sorted(CARDS_DIR.glob("*.json")):
        if p.name.startswith("_"):
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            mid = data.get("model_id")
            if mid:
                models.append(mid)
        except Exception:
            pass
    return models


def _collect_missing_probe_models() -> list[str]:
    """Gibt alle model_ids zurück, deren Card kein thinking_probe_detected-Feld hat."""
    missing: list[str] = []
    for p in sorted(CARDS_DIR.glob("*.json")):
        if p.name.startswith("_"):
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if "thinking_probe_detected" not in data:
                mid = data.get("model_id")
                if mid:
                    missing.append(mid)
        except Exception:
            pass
    return missing


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Führt Reasoning-Erkennung durch und aktualisiert Model Cards."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--model",
        type=str,
        help="Einzelnes Modell proben (Model-ID, z.B. 'moonshotai/kimi-k2.5')",
    )
    group.add_argument(
        "--missing",
        action="store_true",
        help="Alle Cards ohne thinking_probe_detected-Feld aktualisieren",
    )
    group.add_argument(
        "--all",
        action="store_true",
        dest="all_cards",
        help="Alle bekannten Cards proben (überschreibt bestehende Probe-Felder)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="Provider-Key überschreiben (z.B. 'ollama', 'openrouter', 'anthropic')",
    )
    args = parser.parse_args()

    config = _load_config()

    if args.model:
        model_ids = [args.model]
        force = True  # Einzelner expliziter Aufruf → immer ausführen
    elif args.missing:
        model_ids = _collect_missing_probe_models()
        force = False
        logger.info("Modelle ohne Probe-Feld: %d", len(model_ids))
    else:  # --all
        model_ids = _collect_all_card_models()
        force = True
        logger.info("Alle Card-Modelle: %d", len(model_ids))

    if not model_ids:
        print("✅ Keine Modelle zu proben.")
        return

    ok = 0
    fail = 0
    for mid in model_ids:
        provider = args.provider or _infer_provider(mid, config)
        success = run_probe(mid, provider, config, force=force)
        if success:
            ok += 1
        else:
            fail += 1

    print(f"\n📊 Fertig: {ok} erfolgreich, {fail} fehlgeschlagen.")
    # Nur bei explizitem --model Aufruf mit Exit-Code 1 bei Fehler
    if fail and args.model:
        sys.exit(1)


if __name__ == "__main__":
    main()
