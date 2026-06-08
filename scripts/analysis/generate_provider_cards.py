#!/usr/bin/env python3
"""
Provider Card Generator
=======================
Generiert pro bekanntem Provider eine strukturierte JSON-Karte mit:
- Redaktionellen Metadaten (Firmenbeschreibung, Datenschutz) via LLM
- Gemessenen Performance-Statistiken aus provider_leaderboard.csv (hartcodierte Fakten)

Die Card folgt dem kanonischen Schema in :mod:`utils.provider_card_template`.
Modell-spezifische Felder (origin_country, developer_jurisdiction, summary,
strengths, known_limitations) werden NICHT in die Provider Card geschrieben —
diese leben ausschließlich in der Model Card (SSoT-Trennung).

Ausgabe: benchmark_scores/provider_cards/{provider_id}.json
         benchmark_scores/provider_cards/_index.json

Verwendung:
    python scripts/analysis/generate_provider_cards.py            # Alle fehlenden Karten
    python scripts/analysis/generate_provider_cards.py --force    # Alle neu generieren
    python scripts/analysis/generate_provider_cards.py --provider "Anthropic"
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
from utils.provider_card_template import (
    CARDS_DIR,
    _safe_id,
    normalize_provider_card_data,
    rebuild_provider_index,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

LEADERBOARD_CSV = ROOT_DIR / "benchmark_scores" / "provider_leaderboard.csv"

# Provider, die keinen echten Cloud-Anbieter darstellen – werden übersprungen
SKIP_PROVIDERS = {"Other / Unknown"}

SYSTEM_PROMPT = (
    "Du bist ein Cloud-Infrastruktur-Analyst mit Spezialisierung auf KI-Provider, "
    "Datenschutzrecht und API-Architektur. "
    "Erstelle eine präzise, faktisch korrekte Provider Card für den angegebenen KI-API-Anbieter. "
    "Antworte ausschließlich als valides JSON-Objekt. Keine Erklärungen, kein Markdown drumherum. "
    "Bei Unsicherheit über rechtliche Details: konservativ schätzen und 'unknown' verwenden."
)

USER_PROMPT_TEMPLATE = """Erstelle eine Provider Card für: {provider_name}

JSON-Schema (alle Felder Pflicht — Felder außerhalb des Schemas werden verworfen):
{{
  "provider_id": "{provider_id}",
  "display_name": "Offizieller Anzeigename (z.B. 'Anthropic', 'Mistral AI', 'Google DeepMind')",
  "company": "Vollständiger rechtlicher Unternehmensname (z.B. 'Anthropic PBC', 'Mistral AI SAS')",
  "headquarters": "Sitz des Unternehmens (Stadt, Land; z.B. 'San Francisco, CA, USA')",
  "founding_year": 2021,

  "pricing_model": "Eines dieser Werte: 'pay-per-token' | 'subscription' | 'free' | 'free-tier+pay-per-token' | 'open-source-self-hosted'",
  "api_base_url": "Offizielle API-URL (z.B. 'https://api.anthropic.com') oder null wenn nicht vorhanden",
  "api_documentation_url": "URL zur offiziellen API-Dokumentation (z.B. 'https://docs.anthropic.com') oder null",

  "deployment": {{
    "cloud_act_exposure": "true | false. true = US-Unternehmen oder US-Tochter, bei dem US-Behörden Zugriff verlangen können.",
    "applicable_law": "Primär anwendbares Recht für API-Calls: 'US (CLOUD Act)' | 'EU (GDPR)' | 'China (PIPL/CSL/DSL)' | 'N/A (lokal only)' | 'Unknown'",
    "data_residency": "Wo werden Daten physisch verarbeitet? z.B. 'USA' | 'EU' | 'USA + EU' | 'Unknown' | 'N/A (lokal only)'",
    "gdpr_dpa_available": "Gibt es einen Data Processing Agreement für EU-Kunden? true | false | 'unknown'",
    "eu_adequacy_decision": "Gibt es einen Angemessenheitsbeschluss oder SCCs für EU-Transfers? true | false | 'unknown'",
    "data_retention_days": "Wie lange werden API-Request-Daten gespeichert? Zahl in Tagen, 0 = keine Speicherung laut ToS, -1 = unknown",
    "chinese_nsl_risk": "none | low | high. 'high' = Unternehmen mit Sitz in China oder chinesischer Muttergesellschaft. 'low' = bekannte chinesische Investorenbeteiligung ohne Kontrolle. 'none' = kein China-Bezug."
  }},

  "privacy_note": "1-2 Sätze für europäische Nutzer: Welches Datenschutzrisiko besteht konkret bei API-Nutzung dieses Providers? Nur Deployment-Risiko, kein Weights-Risiko.",
  "notable_models": ["Bekanntes Modell 1", "Bekanntes Modell 2"],

  "verification_source": "URL der primären Quelle, aus der die Karten-Daten verifiziert wurden (z.B. 'https://www.anthropic.com/legal/privacy') oder null",

  "unknown": false
}}

Hinweis: Modell-spezifische Felder (origin_country, developer_jurisdiction, summary, strengths, known_limitations) gehören in die Model Card, NICHT hierhin — diese Card ist nur für Provider-/Deployment-Informationen.

Wichtige Hinweise:
- Anthropic, OpenAI, Google, Meta, Microsoft, x.AI = US-Unternehmen → cloud_act_exposure: true, applicable_law: 'US (CLOUD Act)'
- Mistral AI = französisches Unternehmen → cloud_act_exposure: false, applicable_law: 'EU (GDPR)'
- Alibaba Cloud, DeepSeek, MiniMax, Baidu, ByteDance = chinesische Unternehmen → chinese_nsl_risk: 'high'
- Groq = US-Unternehmen (Inference-Hardware-Spezialist) → cloud_act_exposure: true
- Ollama = Open-Source-Framework, kein Cloud-Provider → applicable_law: 'N/A (lokal only)', data_retention_days: 0, cloud_act_exposure: false

Falls du den Provider nicht kennst, setze "unknown": true und befülle die anderen Felder mit sinnvollen Platzhaltern."""


def _load_stats_from_csv() -> dict[str, dict[str, Any]]:
    """Liest gemessene Performance-Statistiken aus provider_leaderboard.csv."""
    if not LEADERBOARD_CSV.exists():
        logger.warning("provider_leaderboard.csv nicht gefunden – Stats werden leer sein. Bitte zuerst 'make provider-stats' ausführen.")
        return {}

    stats: dict[str, dict[str, Any]] = {}
    with open(LEADERBOARD_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row.get("Provider", "").strip()
            if not name:
                continue
            ping_raw = row.get("Active Ping TTFB (ms)", "N/A")
            stats[name] = {
                "models_tracked": int(row.get("Models Tracked", 0) or 0),
                "median_tokens_per_s": float(row.get("Median t/s", 0) or 0),
                "median_avg_task_duration_s": float(row.get("Median Avg Task Duration (s)", 0) or 0),
                "cost_per_1k_median_usd": float(row.get("Cost per 1K (median $)", 0) or 0),
                "active_ping_ttfb_ms": int(ping_raw) if str(ping_raw).isdigit() else None,
            }
    return stats


def _load_config() -> dict[str, Any]:
    config_path = ROOT_DIR / "benchmark_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _parse_json_from_response(response: str) -> dict[str, Any]:
    """Extrahiert JSON aus LLM-Antwort (mit oder ohne Markdown-Fence)."""
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
    if fence_match:
        raw = fence_match.group(1)
    else:
        brace_match = re.search(r"\{.*\}", response, re.DOTALL)
        if not brace_match:
            raise ValueError("Kein JSON-Objekt in der LLM-Antwort gefunden.")
        raw = brace_match.group(0)
    return json.loads(raw)


def _generate_card(
    provider_name: str,
    provider_id: str,
    stats: dict[str, Any],
    client: LLMClient,
    llm_provider: str,
    llm_model: str,
) -> dict[str, Any]:
    """Generiert eine Provider Card: LLM-Teil + Stats-Injektion + Normalisierung.

    Returns:
        Normalisiertes Dict (Reihenfolge wie im Template). Redundante Felder
        (origin_country, developer_jurisdiction, summary, strengths,
        known_limitations, developer) werden durch ``normalize_provider_card_data``
        verworfen.
    """
    prompt = USER_PROMPT_TEMPLATE.format(
        provider_name=provider_name,
        provider_id=provider_id,
    )

    logger.info("Generiere Provider Card für '%s' via %s/%s ...", provider_name, llm_provider, llm_model)

    # Minimales Fallback-Dict — wird durch normalize_provider_card_data mit
    # allen Template-Defaults aufgefüllt.
    fallback: dict[str, Any] = {
        "provider_id": provider_id,
        "display_name": provider_name,
        "unknown": True,
    }

    try:
        response = client.query(
            model=llm_model,
            prompt=prompt,
            provider=llm_provider,
            system=SYSTEM_PROMPT,
            temperature=0.2,
        )
    except Exception as e:
        logger.error("LLM-Call fehlgeschlagen für '%s': %s", provider_name, e)
        card = normalize_provider_card_data(fallback)
        card["privacy_note"] = f"Card konnte nicht generiert werden (LLM-Fehler: {str(e)[:80]})."
        card["stats"] = stats
        return card

    try:
        raw_card = _parse_json_from_response(response)
    except (ValueError, json.JSONDecodeError) as e:
        logger.error("JSON-Parse fehlgeschlagen für '%s': %s", provider_name, e)
        raw_card = fallback

    # Stats aus CSV injizieren – diese Werte kommen immer aus echter Messung, nie vom LLM
    raw_card["stats"] = stats
    raw_card["provider_id"] = provider_id

    # Normalisierung gegen Template: entfernt redundante Felder, ergänzt fehlende
    return normalize_provider_card_data(raw_card)


def _write_card(card: dict[str, Any]) -> Path:
    """Schreibt eine normalisierte Provider-Card auf Platte."""
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    path = CARDS_DIR / f"{_safe_id(card['provider_id'])}.json"
    path.write_text(
        json.dumps(card, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def generate(
    provider_names: list[str],
    all_stats: dict[str, dict[str, Any]],
    client: LLMClient,
    llm_provider: str,
    llm_model: str,
    force: bool = False,
) -> None:
    generated = 0
    skipped = 0

    for name in provider_names:
        if name in SKIP_PROVIDERS:
            logger.info("Übersprungen (kein echter Provider): %s", name)
            skipped += 1
            continue

        provider_id = _safe_id(name)
        card_path = CARDS_DIR / f"{provider_id}.json"

        if card_path.exists() and not force:
            logger.info("Übersprungen (Cache): %s", name)
            skipped += 1
            continue

        stats = all_stats.get(name, {})
        card = _generate_card(name, provider_id, stats, client, llm_provider, llm_model)
        path = _write_card(card)
        generated += 1
        logger.info("Karte gespeichert: %s → %s", name, path.name)

    if generated > 0:
        count = rebuild_provider_index()
        logger.info("_index.json aktualisiert (%d Provider Cards).", count)

    print(f"\nFertig: {generated} generiert, {skipped} übersprungen.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generiert Provider Cards für alle bekannten API-Anbieter."
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="Nur für diesen Provider generieren (exakter Name aus provider_leaderboard.csv, z.B. 'Anthropic')",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bestehende Karten überschreiben",
    )
    args = parser.parse_args()

    config = _load_config()
    all_stats = _load_stats_from_csv()

    if not all_stats:
        logger.error("Keine Provider-Stats gefunden. Bitte zuerst 'make provider-stats' ausführen.")
        sys.exit(1)

    # LLM-Provider aus benchmark_config.yaml (gleiche Sektion wie model-cards)
    review_cfg = config.get("llm_review", {})
    provider_cfg = review_cfg.get("provider", {})
    llm_provider = provider_cfg.get("name", "google")
    llm_model = provider_cfg.get("model", "gemini-2.5-pro")

    logger.info("Provider Card LLM: %s / %s", llm_provider, llm_model)

    client = LLMClient(config=config)

    if args.provider:
        provider_names = [args.provider]
    else:
        provider_names = list(all_stats.keys())
        logger.info("%d Provider aus provider_leaderboard.csv geladen.", len(provider_names))

    generate(
        provider_names=provider_names,
        all_stats=all_stats,
        client=client,
        llm_provider=llm_provider,
        llm_model=llm_model,
        force=args.force,
    )


if __name__ == "__main__":
    main()
