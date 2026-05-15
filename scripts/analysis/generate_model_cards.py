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
from utils.model_utils import (
    ThinkingProbeResult,
    _card_path,
    _find_card,
    get_model_size_class,
    probe_thinking_model,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

CARDS_DIR = ROOT_DIR / "benchmark_scores" / "model_cards"

SYSTEM_PROMPT = (
    "Du bist ein KI-Modell-Archivar mit Spezialisierung auf Datenschutz und KI-Regulierung. "
    "Erstelle eine präzise, faktisch korrekte Model Card für das angegebene LLM. "
    "Antworte ausschließlich als valides JSON-Objekt. Keine Erklärungen, kein Markdown drumherum. "
    "Bei Unsicherheit über rechtliche Details: konservativ schätzen und 'unknown' verwenden."
)

USER_PROMPT_TEMPLATE = """Erstelle eine Model Card für: {model_id}

JSON-Schema (alle Felder Pflicht):
{{
  "model_id": "{model_id}",
  "display_name": "Leserfreundlicher Name (z.B. 'Qwen 3 14B')",
  "developer": "Organisation oder Unternehmen (z.B. 'Alibaba Cloud', 'Anthropic', 'Mistral AI')",
  "origin_country": "Herkunftsland des Entwicklers (z.B. 'China', 'USA', 'France')",
  "developer_jurisdiction": "Rechtlicher Sitz des Unternehmens: 'CN' | 'US' | 'EU' | 'Unknown'",
  "deployment_type": "Einen dieser Werte: 'cloud-only' | 'open-weights' | 'open-weights-cloud-available'. 'open-weights' = Gewichte öffentlich, lokal betreibbar. 'cloud-only' = nur über API/SaaS nutzbar.",
  "local_deployment_possible": true,

  "weights_provenance_risk": "Eines dieser Werte: 'high' | 'medium' | 'low'. NUR auf Basis der Weights-Herkunft, NICHT des Deployments. 'high' = Entwickler unterliegt chinesischem NSL oder vergleichbarer Sicherheitsgesetzgebung. 'medium' = US-Unternehmen (CLOUD Act nur bei API-Nutzung relevant). 'low' = EU-Entwickler oder kein staatlicher Zugriff auf Weights bekannt.",
  "weights_provenance_risk_rationale": "1 Satz: Warum dieser Wert? Nur Weights-Herkunft, kein Deployment.",

  "model_family": "Modell-Familie (z.B. 'Qwen', 'Claude', 'Mistral', 'Gemma')",
  "vendor": "Normalisierter Hersteller-Name für den UI-Filter 'Familie'. Einen dieser Werte: 'Anthropic' | 'OpenAI' | 'Google' | 'Mistral AI' | 'xAI' | 'DeepSeek' | 'Meta' | 'NousResearch' | 'Zhipu AI' | 'Moonshot AI' | 'MiniMax' | 'Alibaba' | 'Community'. Community = abliterated/fine-tuned Derivate ohne eigenen Hersteller.",
  "primary_focus": "Einen dieser Werte: 'reasoning' | 'coding' | 'instruction-following' | 'multilingual' | 'general' | 'creative'",

  "summary": "Exakt 280-320 Zeichen. Fließtext. Nennt: Herkunft, Trainings-Schwerpunkt, typische Stärken, und warum das Modell entwickelt wurde. Kein Marketing-Sprech.",
  "strengths": ["Stärke 1", "Stärke 2", "Stärke 3"],
  "known_limitations": ["Einschränkung 1", "Einschränkung 2"],
  "judge_context_hint": "1 Satz für den Benchmark-Judge: Was muss er bei der Bewertung dieses Modells im Kopf haben? (Kein Datenschutz-Aspekt, nur Qualitäts-/Verhaltenshinweis)",
  "architecture_tags": ["General"],
  "supports_tool_use": true,
  "unknown": false
}}

Feld supports_tool_use:
- true  = Modell unterstützt Function Calling / Tool Use per API (kann als Agentenmotor eingesetzt werden)
- false = Modell unterstützt keine Tool Calls (z.B. reine Basis-/Reasoning-Modelle ohne FC-Support, abliterierte Varianten)
- null  = unbekannt / nicht verifiziert
Faustregel: Aktuelle Cloud-Frontier-Modelle (Anthropic, OpenAI, Google, xAI, Mistral, Qwen 3+, Kimi K2, GLM 5+, Llama 3.3+) → true.
Lokale uncensored/abliterated Varianten, DeepSeek-R1-Basis-Modelle → false.

Verfügbare architecture_tags (ein oder mehrere, als JSON-Array):
- "General" — Allround-Modell ohne besondere Spezialisierung (Default, wenn nichts anderes zutrifft)
- "Coder" — Primär für Code-Generierung/Coding-Aufgaben trainiert (z.B. Codestral, DeepSeek-Coder)
- "Thinking" — Festes Chain-of-Thought, immer aktiv (z.B. DeepSeek-R1, o1, o3, QwQ) — sichtbare <thinking>-Blöcke
- "Thinking-Optional" — Extended Thinking per API an-/abschaltbar, Standard-Modus ist ohne Thinking (z.B. Qwen3, Gemini 2.5, Grok 3)
- "Instruct" — Optimiert auf direktes Instruction-Following, kurze präzise Antworten (z.B. Llama-Instruct, Gemma-it)
- "Preview" — Beta/experimentelle Version, Leistungsschwankungen erwartet
- "Uncensored-Abliterated" — Zensur chirurgisch aus Gewichten entfernt
- "Uncensored-Finetuned" — Zensur via Datensatz konditioniert (z.B. Dolphin, Hermes)
- "Agentic-Orchestrator" — Für Multi-Agent-Orchestrierung optimiert, delegiert Subtasks (z.B. Claude Opus, Kimi K2)

Wichtig: Setze architecture_tags NUR wenn du das Modell kennst. Bei Unsicherheit: ["General"].

Klassifikationsregeln für weights_provenance_risk:
- Alibaba, DeepSeek, MiniMax, Zhipu, ByteDance, Moonshot, Baidu, Tencent → 'high' (NSL)
- OpenAI, Anthropic, Google, Meta, Microsoft, x.AI → 'medium' (US-Unternehmen, CLOUD Act nur bei API)
- Mistral AI, Aleph Alpha → 'low' (EU-Jurisdiktion)
- Unbekannte Herkunft → 'medium' (konservativ)
- Open-Weights-Modell ohne bekannten kommerziellen Hintergrund → 'low'

Falls du das Modell nicht kennst, setze "unknown": true und befülle die anderen Felder mit sinnvollen Platzhaltern."""


def _probe_fields_to_dict(
    probe: ThinkingProbeResult,
) -> dict[str, Any]:
    """Wandelt ein ThinkingProbeResult in persistierbare Card-Felder um."""
    return {
        "thinking_probe_detected": probe.detected,
        "thinking_probe_evidence": probe.evidence,
        "thinking_probe_confidence": probe.confidence,
        "thinking_probe_at": datetime.now(timezone.utc).isoformat(),
    }


def _create_minimal_card(
    model_id: str,
    provider_key: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """
    Erstellt eine Minimal-Card aus dem Thinking-Probe-Ergebnis.
    Kein LLM-Call für Metadaten — nur empirische Probe-Daten.

    Raises:
        RuntimeError: wenn der Probe-API-Call fehlschlägt (Readiness-Gate).
    """
    probe = probe_thinking_model(model_id, provider_key, config)  # raises on failure
    tags = ["Thinking"] if probe.detected else ["General"]
    card: dict[str, Any] = {
        "model_id": model_id,
        "display_name": model_id,
        "developer": "n/a",
        "architecture_tags": tags,
        "card_status": "minimal",
        "size_class": get_model_size_class(model_id),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    card.update(_probe_fields_to_dict(probe))
    return card


def _load_config() -> dict[str, Any]:
    config_path = ROOT_DIR / "benchmark_config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _collect_configured_model_ids(
    config: dict[str, Any],
) -> tuple[list[str], dict[str, str]]:
    """
    Liest alle statisch konfigurierten Model-IDs aus benchmark_config.yaml.
    Auto-discover-Sektionen (ollama local/cloud) werden aus dem Leaderboard ergänzt.

    Returns
    -------
    model_ids:
        Geordnete Liste aller konfigurierten Modell-IDs.
    model_providers:
        Mapping model_id → provider_key (z.B. ``'ollama_local'``, ``'groq'``).
        Modelle ohne expliziten Eintrag fehlen im Dict — gilt als ``None``
        (API-Modell oder auto-discovered ohne Provider-Kontext).
    """
    ids: list[str] = []
    providers: dict[str, str] = {}

    # Statische Provider-Sektionen unter providers.commercial
    commercial = config.get("providers", {}).get("commercial", {})
    for provider_key, provider_cfg in commercial.items():
        for model in provider_cfg.get("models", []):
            mid = model.get("id")
            if mid and mid not in ids:
                ids.append(mid)
                providers[mid] = provider_key

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
                        # Provider-Kontext aus Leaderboard-Zeile, falls vorhanden
                        p = row.get("Provider", "").strip()
                        if p:
                            providers[mid] = p
        except Exception as e:
            logger.warning("Leaderboard konnte nicht gelesen werden: %s", e)

    return ids, providers


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
        "developer_jurisdiction", "deployment_type", "local_deployment_possible",
        "weights_provenance_risk", "weights_provenance_risk_rationale",
        "model_family", "primary_focus", "summary",
        "strengths", "known_limitations", "judge_context_hint",
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
    card["card_status"] = "complete"
    if "size_class" not in card:
        card["size_class"] = get_model_size_class(model_id)

    # Probe-Felder aus bestehender Karte erhalten (z.B. bei --force)
    existing_path = _find_card(model_id)
    if existing_path.exists():
        try:
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
            for probe_field in (
                "thinking_probe_detected",
                "thinking_probe_evidence",
                "thinking_probe_confidence",
                "thinking_probe_at",
            ):
                if probe_field in existing and probe_field not in card:
                    card[probe_field] = existing[probe_field]
        except Exception:
            pass  # Kein bestehender Card-State — kein Problem

    return card


def _write_card(card: dict[str, Any], model_provider: str | None = None) -> Path:
    """Schreibt eine einzelne JSON-Karte auf Disk.

    Parameters
    ----------
    card:
        Fertig validierte Model Card als Dict.
    model_provider:
        Provider-Schlüssel des *benchmarkierten* Modells (nicht der Judge-Provider).
        ``None`` → verhält sich wie bisher (kein Präfix).
    """
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    _ver = str(card.get("model_version") or "").strip()
    _stale = {"latest", "unknown", "k.A.", ""}
    resolved_ver = _ver if _ver not in _stale else None
    path = _card_path(card["model_id"], model_provider, for_write=True, resolved_version=resolved_ver)
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
    model_providers: dict[str, str] | None = None,
) -> None:
    """Hauptloop: generiert Karten für alle übergebenen Model-IDs.

    Parameters
    ----------
    model_ids:
        Liste der zu generierenden Modell-IDs.
    client:
        Konfigurierter LLMClient (für den *Judge*-Provider).
    provider:
        Judge-Provider-Schlüssel (z.B. ``'google'``).
    model_name:
        Judge-Modell (z.B. ``'gemini-2.5-pro'``).
    force:
        Bestehende Karten überschreiben.
    output_format:
        ``'json'``, ``'markdown'`` oder ``'both'``.
    model_providers:
        Mapping model_id → Deployment-Provider-Schlüssel des *benchmarkierten* Modells.
        Wird für provider-qualifizierte Dateinamen verwendet (z.B. ``LCL_llama3_4b.json``).
        ``None`` → kein Präfix (backward-kompatibel).
    """
    generated = 0
    skipped = 0

    for model_id in model_ids:
        model_provider = (model_providers or {}).get(model_id)
        card_path = _card_path(model_id, model_provider)

        if card_path.exists() and not force:
            logger.info("Übersprungen (Cache): %s", model_id)
            skipped += 1
            continue

        card = _generate_card(model_id, client, provider, model_name)
        _write_card(card, model_provider=model_provider)
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
        model_providers: dict[str, str] = {}
    else:
        model_ids, model_providers = _collect_configured_model_ids(config)
        logger.info("%d Modelle aus Konfiguration geladen.", len(model_ids))

    generate(
        model_ids=model_ids,
        client=client,
        provider=provider,
        model_name=model_name,
        force=args.force,
        output_format=args.format,
        model_providers=model_providers,
    )


if __name__ == "__main__":
    main()
