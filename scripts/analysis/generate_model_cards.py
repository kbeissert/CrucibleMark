#!/usr/bin/env python3
"""
Model Card Generator
====================
Generiert pro konfiguriertem Modell eine strukturierte JSON-Karte mit Metadaten
(Entwickler, Herkunft, Stärken, Zusammenfassung) als Grundlage für:
- Meta-Reviewer Kontext (Einbettung in generate_review.py)
- Website-Visitenkarte (JSON-API via _index.json)
- Report-Header (_all_cards.md)

Verwendung:
    python scripts/analysis/generate_model_cards.py            # Alle fehlenden Karten
    python scripts/analysis/generate_model_cards.py --model qwen3:14b
    python scripts/analysis/generate_model_cards.py --force    # Alle neu generieren
    python scripts/analysis/generate_model_cards.py --format json
"""

import argparse
import csv
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.llm_client import LLMClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CARDS_DIR = ROOT_DIR / "benchmark_scores" / "model_cards"

SYSTEM_PROMPT = (
    "Du bist ein KI-Modell-Archivar. Erstelle eine präzise Model Card für das angegebene LLM. "
    "Antworte ausschließlich als valides JSON-Objekt. Keine Erklärungen, kein Markdown drumherum."
)

USER_PROMPT_TEMPLATE = """Erstelle eine Model Card für: {model_id}

JSON-Schema (alle Felder Pflicht):
{{
  "model_id": "{model_id}",
  "display_name": "Leserfreundlicher Name (z.B. 'Qwen 3 14B')",
  "developer": "Organisation oder Unternehmen",
  "origin_country": "Herkunftsland (z.B. 'China', 'USA', 'France')",
  "model_family": "Modell-Familie (z.B. 'Qwen', 'Claude', 'Mistral')",
  "primary_focus": "Einen dieser Werte: 'reasoning' | 'coding' | 'instruction-following' | 'multilingual' | 'general' | 'creative'",
  "summary": "Exakt 280-320 Zeichen. Fließtext. Nennt: Herkunft, Trainings-Schwerpunkt, typische Stärken, und warum das Modell entwickelt wurde. Kein Marketing-Sprech.",
  "strengths": ["Stärke 1", "Stärke 2", "Stärke 3"],
  "known_limitations": ["Einschränkung 1", "Einschränkung 2"],
  "judge_context_hint": "1 Satz für den Benchmark-Judge: Was muss er bei der Bewertung dieses Modells im Kopf haben?",
  "unknown": false
}}

Falls du das Modell nicht kennst, setze "unknown": true und befülle die anderen Felder mit sinnvollen Platzhaltern."""


def _safe_name(model_id: str) -> str:
    """Konvertiert eine Model-ID in einen sicheren Dateinamen."""
    return re.sub(r"[:/.]", "_", model_id)


def _load_config() -> dict[str, Any]:
    config_path = ROOT_DIR / "benchmark_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _collect_configured_model_ids(config: dict[str, Any]) -> list[str]:
    """
    Liest alle statisch konfigurierten Model-IDs aus benchmark_config.yaml.
    Auto-discover-Sektionen (ollama local/cloud) werden aus dem Leaderboard ergänzt.
    """
    ids: list[str] = []

    # Statische Provider-Sektionen unter providers.commercial
    commercial = config.get("providers", {}).get("commercial", {})
    for provider_cfg in commercial.values():
        for model in provider_cfg.get("models", []):
            mid = model.get("id")
            if mid:
                ids.append(mid)

    # Dynamische Modelle (ollama local + cloud): aus Leaderboard lesen
    leaderboard_csv = ROOT_DIR / "benchmark_scores" / "benchmark_leaderboard.csv"
    if leaderboard_csv.exists():
        try:
            with open(leaderboard_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    mid = row.get("Model Name", "").strip()
                    if mid and mid not in ids:
                        ids.append(mid)
        except Exception as e:
            logger.warning("Leaderboard konnte nicht gelesen werden: %s", e)

    return ids


def _parse_json_from_response(response: str) -> dict[str, Any]:
    """Extrahiert JSON aus LLM-Antwort (mit oder ohne Markdown-Fence)."""
    # Markdown-Fence entfernen
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
    if fence_match:
        raw = fence_match.group(1)
    else:
        # Erstes { ... } direkt nehmen
        brace_match = re.search(r"\{.*\}", response, re.DOTALL)
        if not brace_match:
            raise ValueError("Kein JSON-Objekt in der LLM-Antwort gefunden.")
        raw = brace_match.group(0)

    return json.loads(raw)


def _validate_card(card: dict[str, Any], model_id: str) -> dict[str, Any]:
    """Prüft Pflichtfelder und Zeichenlänge von summary. Ergänzt fehlende Felder."""
    required = [
        "model_id", "display_name", "developer", "origin_country",
        "model_family", "primary_focus", "summary", "strengths",
        "known_limitations", "judge_context_hint",
    ]
    for field in required:
        if field not in card:
            logger.warning("Feld '%s' fehlt in Karte für %s — wird mit Platzhalter befüllt.", field, model_id)
            card[field] = "n/a" if isinstance(card.get(field, ""), str) else []

    # summary Länge prüfen (nur warnen, nicht abbrechen)
    summary_len = len(card.get("summary", ""))
    if not (280 <= summary_len <= 320) and not card.get("unknown"):
        logger.warning(
            "summary für %s hat %d Zeichen (erwartet 280-320).",
            model_id, summary_len,
        )

    # model_id erzwingen
    card["model_id"] = model_id

    # unknown-Flag sicherstellen
    if "unknown" not in card:
        card["unknown"] = False

    return card


def _generate_card(model_id: str, client: LLMClient, provider: str, model_name: str) -> dict[str, Any]:
    """Generiert eine Model Card via LLM-Call."""
    prompt = USER_PROMPT_TEMPLATE.format(model_id=model_id)

    logger.info("Generiere Karte für '%s' via %s/%s ...", model_id, provider, model_name)
    try:
        response = client.query(
            model=model_name,
            prompt=prompt,
            provider=provider,
            system=SYSTEM_PROMPT,
            temperature=0.2,
        )
    except Exception as e:
        logger.error("LLM-Call fehlgeschlagen für '%s': %s", model_id, e)
        return {
            "model_id": model_id,
            "display_name": model_id,
            "developer": "n/a",
            "origin_country": "n/a",
            "model_family": "n/a",
            "primary_focus": "general",
            "summary": f"Karte konnte nicht generiert werden (LLM-Fehler: {str(e)[:80]}).",
            "strengths": [],
            "known_limitations": [],
            "judge_context_hint": "",
            "unknown": True,
        }

    try:
        card = _parse_json_from_response(response)
    except (ValueError, json.JSONDecodeError) as e:
        logger.error("JSON-Parse fehlgeschlagen für '%s': %s", model_id, e)
        card = {
            "model_id": model_id,
            "display_name": model_id,
            "developer": "n/a",
            "origin_country": "n/a",
            "model_family": "n/a",
            "primary_focus": "general",
            "summary": "Karte konnte nicht generiert werden (JSON-Parse-Fehler).",
            "strengths": [],
            "known_limitations": [],
            "judge_context_hint": "",
            "unknown": True,
        }

    card = _validate_card(card, model_id)
    card["generated_at"] = datetime.now(timezone.utc).isoformat()
    return card


def _write_card(card: dict[str, Any]) -> Path:
    """Schreibt eine einzelne JSON-Karte auf Disk."""
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    path = CARDS_DIR / f"{_safe_name(card['model_id'])}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(card, f, ensure_ascii=False, indent=2)
    return path


def _rebuild_index() -> None:
    """Baut _index.json aus allen vorhandenen Einzelkarten neu auf."""
    cards = []
    for p in sorted(CARDS_DIR.glob("*.json")):
        if p.name == "_index.json":
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                cards.append(json.load(f))
        except Exception as e:
            logger.warning("Konnte %s nicht lesen: %s", p.name, e)

    index_path = CARDS_DIR / "_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)
    logger.info("_index.json aktualisiert (%d Karten).", len(cards))


def _rebuild_markdown() -> None:
    """Baut _all_cards.md aus allen vorhandenen Einzelkarten neu auf."""
    index_path = CARDS_DIR / "_index.json"
    if not index_path.exists():
        return

    with open(index_path, "r", encoding="utf-8") as f:
        cards = json.load(f)

    lines = ["# Model Cards – Alle Modelle\n"]
    for card in cards:
        if card.get("unknown"):
            continue
        strengths = " · ".join(card.get("strengths", []))
        limitations = " · ".join(card.get("known_limitations", []))
        lines.append(f"### {card.get('display_name', card['model_id'])}")
        lines.append(
            f"**Entwickler:** {card.get('developer', 'n/a')} · "
            f"**Herkunft:** {card.get('origin_country', 'n/a')} · "
            f"**Fokus:** {card.get('primary_focus', 'n/a')}\n"
        )
        lines.append(card.get("summary", ""))
        lines.append("")
        if strengths:
            lines.append(f"**Stärken:** {strengths}")
        if limitations:
            lines.append(f"**Einschränkungen:** {limitations}")
        lines.append("\n---\n")

    md_path = CARDS_DIR / "_all_cards.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info("_all_cards.md aktualisiert.")


def generate(
    model_ids: list[str],
    client: LLMClient,
    provider: str,
    model_name: str,
    force: bool = False,
    output_format: str = "both",
) -> None:
    """Hauptloop: generiert Karten für alle übergebenen Model-IDs."""
    generated = 0
    skipped = 0

    for model_id in model_ids:
        card_path = CARDS_DIR / f"{_safe_name(model_id)}.json"

        if card_path.exists() and not force:
            logger.info("Übersprungen (Cache): %s", model_id)
            skipped += 1
            continue

        card = _generate_card(model_id, client, provider, model_name)
        _write_card(card)
        generated += 1
        logger.info(
            "✅ Karte gespeichert: %s (unknown=%s, summary=%d Zeichen)",
            card["model_id"],
            card.get("unknown"),
            len(card.get("summary", "")),
        )

    if generated > 0 or (force and skipped == 0):
        _rebuild_index()
        if output_format in ("both", "markdown"):
            _rebuild_markdown()

    print(f"\n📊 Fertig: {generated} generiert, {skipped} übersprungen.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generiert Model Cards für alle konfigurierten LLMs."
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Nur für dieses eine Modell generieren (z.B. qwen3:14b)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bestehende Karten überschreiben",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="both",
        help="Ausgabeformat (default: both)",
    )
    args = parser.parse_args()

    config = _load_config()

    # LLM-Provider aus llm_review-Sektion bestimmen
    review_cfg = config.get("llm_review", {})
    if not review_cfg.get("enabled", True):
        logger.warning("llm_review ist in benchmark_config.yaml deaktiviert. Trotzdem fortfahren.")
    provider_cfg = review_cfg.get("provider", {})
    provider = provider_cfg.get("name", "google")
    model_name = provider_cfg.get("model", "gemini-2.5-pro")
    max_tokens = provider_cfg.get("max_tokens", 2048)

    logger.info("Model Card Provider: %s / %s", provider, model_name)

    client = LLMClient(config=config)

    if args.model:
        model_ids = [args.model]
    else:
        model_ids = _collect_configured_model_ids(config)
        logger.info("%d Modelle aus Konfiguration geladen.", len(model_ids))

    generate(
        model_ids=model_ids,
        client=client,
        provider=provider,
        model_name=model_name,
        force=args.force,
        output_format=args.format,
    )


if __name__ == "__main__":
    main()
