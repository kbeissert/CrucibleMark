#!/usr/bin/env python3
"""
Provider Card Generator
=======================
Generiert pro bekanntem Provider eine strukturierte JSON-Karte mit:
- Redaktionellen Metadaten (Firmenbeschreibung, Herkunft, Datenschutz) via LLM
- Gemessenen Performance-Statistiken aus provider_leaderboard.csv (hartcodierte Fakten)

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

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CARDS_DIR = ROOT_DIR / "benchmark_scores" / "provider_cards"
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

JSON-Schema (alle Felder Pflicht):
{{
  "provider_id": "{provider_id}",
  "display_name": "Offizieller Anzeigename (z.B. 'Anthropic', 'Mistral AI', 'Google DeepMind')",
  "company": "Vollständiger rechtlicher Unternehmensname (z.B. 'Anthropic PBC', 'Mistral AI SAS')",
  "origin_country": "Herkunftsland des Unternehmens (z.B. 'USA', 'France', 'China')",
  "headquarters": "Sitz des Unternehmens (Stadt, Land; z.B. 'San Francisco, CA, USA')",
  "founding_year": 2021,
  "developer_jurisdiction": "Rechtlicher Hauptsitz: 'US' | 'EU' | 'CN' | 'Unknown'",

  "pricing_model": "Eines dieser Werte: 'pay-per-token' | 'subscription' | 'free' | 'free-tier+pay-per-token' | 'open-source-self-hosted'",
  "api_base_url": "Offizielle API-URL (z.B. 'https://api.anthropic.com') oder null wenn nicht vorhanden",

  "deployment": {{
    "cloud_act_exposure": "true | false. true = US-Unternehmen oder US-Tochter, bei dem US-Behörden Zugriff verlangen können.",
    "applicable_law": "Primär anwendbares Recht für API-Calls: 'US (CLOUD Act)' | 'EU (GDPR)' | 'China (PIPL/CSL/DSL)' | 'N/A (lokal only)' | 'Unknown'",
    "data_residency": "Wo werden Daten physisch verarbeitet? z.B. 'USA' | 'EU' | 'USA + EU' | 'Unknown' | 'N/A (lokal only)'",
    "gdpr_dpa_available": "Gibt es einen Data Processing Agreement für EU-Kunden? true | false | 'unknown'",
    "eu_adequacy_decision": "Gibt es einen Angemessenheitsbeschluss oder SCCs für EU-Transfers? true | false | 'unknown'",
    "data_retention_days": "Wie lange werden API-Request-Daten gespeichert? Zahl in Tagen, 0 = keine Speicherung laut ToS, -1 = unknown",
    "chinese_nsl_risk": "none | low | high. 'high' = Unternehmen mit Sitz in China oder chinesischer Muttergesellschaft. 'low' = bekannte chinesische Investorenbeteiligung ohne Kontrolle. 'none' = kein China-Bezug."
  }},

  "summary": "Exakt 280-320 Zeichen. Fließtext. Nennt: Hintergrund des Unternehmens, Positionierung im Markt, wofür der Provider bekannt ist. Kein Marketing-Sprech.",
  "privacy_note": "1-2 Sätze für europäische Nutzer: Welches Datenschutzrisiko besteht konkret bei API-Nutzung dieses Providers? Nur Deployment-Risiko, kein Weights-Risiko.",

  "strengths": ["Stärke 1", "Stärke 2", "Stärke 3"],
  "known_limitations": ["Einschränkung 1", "Einschränkung 2"],
  "notable_models": ["Bekanntes Modell 1", "Bekanntes Modell 2"],

  "unknown": false
}}

Wichtige Hinweise:
- Anthropic, OpenAI, Google, Meta, Microsoft, x.AI = US-Unternehmen → cloud_act_exposure: true, applicable_law: 'US (CLOUD Act)'
- Mistral AI = französisches Unternehmen → cloud_act_exposure: false, applicable_law: 'EU (GDPR)'
- Alibaba Cloud, DeepSeek, MiniMax, Baidu, ByteDance = chinesische Unternehmen → chinese_nsl_risk: 'high'
- Groq = US-Unternehmen (Inference-Hardware-Spezialist) → cloud_act_exposure: true
- Ollama = Open-Source-Framework, kein Cloud-Provider → applicable_law: 'N/A (lokal only)', data_retention_days: 0, cloud_act_exposure: false

Falls du den Provider nicht kennst, setze "unknown": true und befülle die anderen Felder mit sinnvollen Platzhaltern."""


def _safe_id(name: str) -> str:
    """Konvertiert einen Provider-Namen in einen sicheren Dateinamen / ID."""
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


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


def _validate_card(card: dict[str, Any], provider_id: str) -> dict[str, Any]:
    """Prüft Pflichtfelder, ergänzt fehlende mit Platzhaltern."""
    required = [
        "provider_id", "display_name", "company", "origin_country",
        "headquarters", "founding_year", "developer_jurisdiction",
        "pricing_model", "deployment",
        "summary", "privacy_note", "strengths", "known_limitations", "notable_models",
    ]
    for field in required:
        if field not in card:
            logger.warning("Feld '%s' fehlt in Provider Card '%s' – wird mit Platzhalter befüllt.", field, provider_id)
            card[field] = "n/a"

    summary_len = len(card.get("summary", ""))
    if not (280 <= summary_len <= 320) and not card.get("unknown"):
        logger.warning(
            "summary für '%s' hat %d Zeichen (erwartet 280-320).",
            provider_id, summary_len,
        )

    card["provider_id"] = provider_id
    if "unknown" not in card:
        card["unknown"] = False

    return card


def _generate_card(
    provider_name: str,
    provider_id: str,
    stats: dict[str, Any],
    client: LLMClient,
    llm_provider: str,
    llm_model: str,
) -> dict[str, Any]:
    """Generiert eine Provider Card: LLM-Teil + Stats-Injektion."""
    prompt = USER_PROMPT_TEMPLATE.format(
        provider_name=provider_name,
        provider_id=provider_id,
    )

    logger.info("Generiere Provider Card für '%s' via %s/%s ...", provider_name, llm_provider, llm_model)

    fallback: dict[str, Any] = {
        "provider_id": provider_id,
        "display_name": provider_name,
        "company": "n/a",
        "origin_country": "n/a",
        "headquarters": "n/a",
        "founding_year": None,
        "developer_jurisdiction": "Unknown",
        "pricing_model": "unknown",
        "api_base_url": None,
        "privacy_assessment": {
            "cloud_api_jurisdiction": "Unknown",
            "gdpr_dpa_available": "unknown",
            "data_retention_policy": "unknown",
            "chinese_national_security_law_risk": "none",
            "sovereign_risk_level": "medium",
            "sovereign_risk_rationale": "Keine Daten verfügbar.",
        },
        "summary": "Keine Informationen verfügbar.",
        "privacy_note": "Keine Informationen verfügbar.",
        "strengths": [],
        "known_limitations": [],
        "notable_models": [],
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
        card = fallback
        card["summary"] = f"Karte konnte nicht generiert werden (LLM-Fehler: {str(e)[:80]})."
        card["stats"] = stats
        card["generated_at"] = datetime.now(timezone.utc).isoformat()
        return card

    try:
        card = _parse_json_from_response(response)
    except (ValueError, json.JSONDecodeError) as e:
        logger.error("JSON-Parse fehlgeschlagen für '%s': %s", provider_name, e)
        card = fallback

    card = _validate_card(card, provider_id)
    # Stats aus CSV injizieren – diese Werte kommen immer aus echter Messung, nie vom LLM
    card["stats"] = stats
    card["generated_at"] = datetime.now(timezone.utc).isoformat()
    return card


def _write_card(card: dict[str, Any]) -> Path:
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    path = CARDS_DIR / f"{card['provider_id']}.json"
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
    logger.info("_index.json aktualisiert (%d Provider Cards).", len(cards))


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
        _rebuild_index()

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
