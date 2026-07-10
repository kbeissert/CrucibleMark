# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.card_template import CardTemplate, cards_dir
from utils.model_utils import _find_card
from .models import (
    CardCheckReport,
    CardFinding,
    LLMSpec,
    logger,
)

EDITOR_PROMPTS_PATH = ROOT_DIR / "config" / "editor_prompts.yaml"
LOG_PATH = ROOT_DIR / "logs" / "manage_model_cards.log"
_HTTP_OK = 200

OPERATOR_PROTECTED_FIELDS: tuple[str, ...] = (
    "model_id",
    "generated_at",
    "card_status",
    "unknown",
    "size_class",
    "thinking_probe_detected",
    "thinking_probe_evidence",
    "thinking_probe_confidence",
    "thinking_probe_at",
    "cot_marker_family",
    "cot_tags_detected",
    "tooluse_tested_at",
    "tooluse_score_p1",
    "tooluse_score_p2",
    "tooluse_runs",
    "dual_profile",
    "tooluse_recommendation",
    "temperature",
    "top_p",
    "top_k",
    "repetition_penalty",
    "frequency_penalty",
    "presence_penalty",
    "seed",
    "stop_sequences",
    "system_prompt_override",
    "heritage_ids",
)


TOOL_SCHEMA_WEB_SEARCH = {
    "name": "web_search",
    "description": "Sucht im Web nach aktuellen Informationen.",
    "parameters": {
        "query": {"type": "string", "description": "Der Suchbegriff"},
        "max_results": {"type": "integer", "description": "Anzahl der Ergebnisse (max. 3)", "default": 3},
    },
}

TOOL_SCHEMA_HTTP_FETCH = {
    "name": "fetch",
    "description": "Lädt den Inhalt einer URL.",
    "parameters": {
        "url": {"type": "string", "description": "Die zu ladende URL"},
        "max_chars": {"type": "integer", "description": "Maximale Zeichenanzahl", "default": 3000},
    },
}

TOOL_SCHEMAS = [TOOL_SCHEMA_WEB_SEARCH, TOOL_SCHEMA_HTTP_FETCH]


def _setup_logging() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    if not logger.handlers:
        file_handler = logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8")
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(fmt)
        logger.addHandler(stream_handler)


def _load_benchmark_config() -> dict:
    from utils.config_validator import ConfigValidator
    path = ROOT_DIR / "benchmark_config.yaml"
    return ConfigValidator(str(path)).config


def _resolve_llm_spec(args: argparse.Namespace, config: dict) -> LLMSpec:
    section = config.get("llm_card_manager", {}).get("provider", {})
    provider_name = section.get("name", "openai")
    model = section.get("model", "gpt-5.4")
    max_tokens = int(section.get("max_tokens", 32768))
    temperature = float(section.get("temperature", 0.0))

    if getattr(args, "model", None):
        model = args.model
    if getattr(args, "provider", None):
        provider_name = args.provider

    config_base = section.get("base_url")
    env_base = os.environ.get("OPENAI_BASE_URL")
    base_url = config_base or env_base or "https://api.openai.com/v1"
    if getattr(args, "base_url", None):
        base_url = args.base_url

    config_key_env = section.get("api_key_env")
    api_key_env = getattr(args, "api_key_env", None) or config_key_env or "OPENAI_API_KEY"
    api_key = os.environ.get(api_key_env)

    return LLMSpec(
        provider_name=provider_name,
        model=model,
        base_url=base_url,
        api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
    )


def _load_editor_prompt() -> str:
    with open(EDITOR_PROMPTS_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    prompt = data.get("model_card_verification", {}).get("prompt", "")
    if not prompt:
        raise SystemExit(
            f"❌ 'model_card_verification.prompt' fehlt in {EDITOR_PROMPTS_PATH}."
        )
    return prompt


_CHECK_SYSTEM_INSTRUCTION = (
    "Du bist ein Card-Reviewer. Prüfe die unten angegebene Model Card kritisch. "
    "Antworte AUSSCHLIESSLICH mit einem einzigen JSON-Objekt der Form:\n"
    "{\n"
    '  "findings": [\n'
    '    {"field": "<feldname>", "severity": "error|warning|info", '
    '"message": "<kurze Erklärung>", "current": <aktueller Wert oder null>, '
    '"suggested": <vorgeschlagener Wert oder null>}\n'
    "  ],\n"
    '  "summary": "<kurze Zusammenfassung in 1-2 Sätzen>"\n'
    "}\n"
    "Felder, die du nicht beurteilen kannst, lasse weg oder nenne sie mit "
    "severity: \"info\". Antworte NUR mit dem JSON-Objekt — kein Markdown-Fence, "
    "keine Kommentare, keine zusätzlichen Erklärungen."
)

_MAKE_SYSTEM_INSTRUCTION = (
    "Du bist ein Card-Generator. Liefere AUSSCHLIESSLICH eine einzige JSON-Datei, "
    "die exakt die Template-Felder enthält. Keine fremden Felder, keine "
    "Kommentare, kein Markdown-Fence, keine zusätzlichen Erklärungen. "
    "Antworte NUR mit dem JSON-Objekt."
)

_LLM_TEXT_FIELDS = frozenset({
    "summary",
    "strengths",
    "known_limitations",
    "judge_context_hint",
    "weights_provenance_risk_rationale",
})

_RESEARCH_SYSTEM_INSTRUCTION = (
    "Du bist ein Card-Researcher. Deine Aufgabe ist es, die TEXTFELDER der "
    "Model Card auf inhaltliche Korrektheit zu pruefen und bei Bedarf neu zu "
    "schreiben.\n\n"
    "DEIN FOKUS — nur diese Felder darfst du pruefen/ändern:\n"
    "- summary\n"
    "- strengths\n"
    "- known_limitations\n"
    "- judge_context_hint\n"
    "- weights_provenance_risk_rationale\n\n"
    "NICHT DEIN FOKUS — diese Felder wurden bereits validiert:\n"
    "- Lizenz-Felder (license, license_url, weights_license_tier, commercial_use_allowed)\n"
    "- Strukturfelder (deployment_type, params_active_b, params_total_b,\n"
    "  input_price_per_1m, output_price_per_1m, community, display_name,\n"
    "  developer, model_version, context_window_k, knowledge_cutoff)\n"
    "Diese Felder sind vom Script geprueft und korrekt. Ueberschreibe sie NICHT.\n\n"
    "WANN DU AKTIONIERST:\n"
    "- Wenn Pre-Findings einen Lizenz-Wechsel anzeigen, muessen ALLE 5 Textfelder\n"
    "  komplett neu geschrieben werden (nicht nur Woerter ersetzen).\n"
    "- Wenn Murks (CJK, em-dash) erkannt wurde, das betroffene Feld neu schreiben.\n"
    "- Wenn ein Text inhaltlich falsch ist (z.B. falsche Lizenz im Text), korrigieren.\n"
    "- Wenn alles korrekt ist, antworte mit einem leeren findings-Array.\n"
    "- Wenn du keinen konkreten Verbesserungstext hast, erzeuge KEIN Finding.\n"
    "  Leere findings-Arrays sind erwuenscht wenn alles korrekt ist.\n\n"
    "WICHTIG: Fuer JEDES Finding MUSS ein \"suggested\"-Wert mit dem komplett\n"
    "neu geschriebenen Text angegeben werden. Findings ohne suggested-Wert\n"
    "werfen verworfen.\n\n"
    "Antworte AUSSCHLIESSLICH mit JSON:\n"
    '{"findings": [{"field": ..., "severity": "error|warning|info", '
    '"message": ..., "current": ..., "suggested": ...}], '
    '"summary": "..."}. '
    "Antworte NUR mit dem JSON-Objekt — kein Markdown-Fence, keine Kommentare."
)


def _build_tooluse_system_instruction(tool_schemas: list[dict]) -> str:
    tool_schema_json = json.dumps(tool_schemas, ensure_ascii=False, indent=2)
    return (
        "Du bist ein Card-Researcher mit Internetzugang.\n\n"
        "Verfügbare Tools:\n"
        f"{tool_schema_json}\n\n"
        "Arbeitsablauf:\n"
        "1. Wenn du Informationen recherchieren musst, antworte AUSSCHLIESSLICH mit:\n"
        '   {"tool_call": {"name": "web_search", "parameters": {"query": "..."}}}\n'
        "   ODER\n"
        '   {"tool_call": {"name": "fetch", "parameters": {"url": "...", "max_chars": 3000}}}\n'
        "2. Ich liefere dir das Tool-Ergebnis zurück.\n"
        "3. Wiederhole Schritt 1-2 bis du genug Informationen hast.\n"
        '4. Wenn du fertig bist, antworte AUSSCHLIESSLICH mit einem JSON-Objekt:\n'
        '{"findings": [...], "summary": "..."}\n\n'
        "FOKUS — diese Felder prioritaetisch pruefen:\n"
        "- summary, strengths, known_limitations, judge_context_hint,\n"
        "  weights_provenance_risk_rationale (Textfelder)\n\n"
        "ZUSATZLICH — diese Felder koennen bei Bedarf recherchiert werden:\n"
        "- Lizenz (license, license_url, weights_license_tier)\n"
        "- Preise (input_price_per_1m, output_price_per_1m)\n"
        "- Context-Window, Knowledge-Cutoff\n\n"
        "Regeln:\n"
        "- Nutze web_search um Preise, Context-Window, Knowledge-Cutoff etc. zu finden.\n"
        "- Nutze fetch um konkrete URLs (Hersteller-Seiten, HF-Cards) zu lesen.\n"
        "- TEXTFELDER BEI LIZENZ-WECHSEL: Wenn sich die Lizenz aendert, MUESSEN\n"
        "  ALLE Textfelder aktualisiert werden mit komplett neu geschriebenen Texten.\n"
        "- Fuer JEDES Finding MUSS ein suggested-Wert angegeben werden.\n"
        "  Ohne suggested-Wert wird das Finding verworfen.\n"
        "- Wenn alles korrekt ist, antworte mit einem leeren findings-Array.\n"
        "- Antworte NUR mit JSON — kein Markdown-Fence, keine Kommentare.\n"
        "- Erfinde keine Inhalte — alles muss aus Tool-Ergebnissen stammen."
    )


_TOOL_CALL_CANDIDATE_RE = re.compile(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}", re.DOTALL)


def _strip_json_markdown(text: str) -> str:
    return re.sub(r"```(?:json)?\s*", "", text).replace("```", "")


def _coerce_tool_call(parsed: dict[str, Any]) -> dict[str, Any] | None:
    if "tool_call" in parsed and isinstance(parsed["tool_call"], dict):
        return parsed["tool_call"]
    if "name" in parsed and "parameters" in parsed:
        return {"name": parsed["name"], "parameters": parsed["parameters"]}
    if "name" in parsed and "arguments" in parsed:
        return {"name": parsed["name"], "parameters": parsed["arguments"]}
    return None


def _iter_balanced_json_candidates(text: str):
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                yield text[start : i + 1]
                start = None


def _parse_tool_call_candidate(candidate: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(candidate)
    except (json.JSONDecodeError, ValueError):
        return None
    if isinstance(parsed, dict):
        return _coerce_tool_call(parsed)
    return None


def _parse_tool_call(text: str) -> tuple[dict[str, Any] | None, str | None]:
    stripped = _strip_json_markdown(text)
    candidates = list(_TOOL_CALL_CANDIDATE_RE.findall(stripped))
    candidates.extend(_iter_balanced_json_candidates(stripped))
    for candidate in candidates:
        tool_call = _parse_tool_call_candidate(candidate)
        if tool_call is not None:
            return tool_call, None
    return None, "No valid tool_call JSON found"


def _json_dict_from_candidate(candidate: str) -> dict | None:
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _iter_json_object_candidates(text: str):
    if not text:
        return
    match = _JSON_FENCE_RE.search(text)
    if match:
        yield match.group(1)
    else:
        first = text.find("{")
        last = text.rfind("}")
        if first != -1 and last != -1 and last > first:
            yield text[first:last + 1]
    yield from _iter_balanced_json_candidates(text)


def _extract_json_object(text: str) -> dict | None:
    for candidate in _iter_json_object_candidates(text):
        parsed = _json_dict_from_candidate(candidate)
        if parsed is not None:
            return parsed
    return None


def _collect_pre_findings(card: dict) -> list[CardFinding]:
    findings = _check_murks(card)
    findings.extend(_check_license_consistency(card))
    findings.extend(_check_community(card))
    findings.extend(_check_license_text_fields(card))
    return findings


_CJK_RANGES: tuple[tuple[int, int], ...] = (
    (0x4E00, 0x9FFF),    # CJK Unified Ideographs
    (0x3400, 0x4DBF),    # CJK Extension A
    (0x3040, 0x309F),    # Hiragana
    (0x30A0, 0x30FF),    # Katakana
    (0xAC00, 0xD7AF),    # Hangul Syllables
)

# --- Lizenz-Mappings (SSoT für Heuristik-Checks) ---
_KNOWN_LICENSE_MAPPINGS: dict[str, dict] = {
    "gemma-4": {
        "license": "Apache 2.0",
        "license_url": "https://ai.google.dev/gemma/apache_2",
        "weights_license_tier": "open-weights",
    },
    "gemma-3": {
        "license": "Google Gemma Terms of Use",
        "license_url": "https://ai.google.dev/gemma/terms",
        "weights_license_tier": "restricted-weights",
    },
    "gemma-2": {
        "license": "Google Gemma Terms of Use",
        "license_url": "https://ai.google.dev/gemma/terms",
        "weights_license_tier": "restricted-weights",
    },
    "qwen3": {
        "license": "Apache 2.0",
        "license_url": "https://www.apache.org/licenses/LICENSE-2.0",
        "weights_license_tier": "open-weights",
    },
    "qwen3_5": {
        "license": "Apache 2.0",
        "license_url": "https://www.apache.org/licenses/LICENSE-2.0",
        "weights_license_tier": "open-weights",
    },
    "qwen2_5": {
        "license": "Apache 2.0",
        "license_url": "https://www.apache.org/licenses/LICENSE-2.0",
        "weights_license_tier": "open-weights",
    },
    "llama-4": {
        "license": "Llama 4 Community License",
        "license_url": "https://github.com/meta-llama/llama-models/blob/main/models/llama4/LICENSE",
        "weights_license_tier": "restricted-weights",
    },
    "llama-3": {
        "license": "Llama 3 Community License",
        "license_url": "https://github.com/meta-llama/llama-models/blob/main/models/llama3/LICENSE",
        "weights_license_tier": "restricted-weights",
    },
}


_KNOWN_COMMUNITY_GROUPS: frozenset[str] = frozenset([
    "Unsloth", "mradermacher", "HauhauCS", "ARA-APEX",
])


def _match_family(model_id: str, family: str) -> tuple[str, dict] | None:
    """Longest-prefix match on model_id/family against _KNOWN_LICENSE_MAPPINGS.

    Returns ``(key, mapping)`` or None. Keys like ``'gemma-4'`` must match
    before ``'gemma'`` — sorted longest-first.
    """
    model_id = model_id.lower()
    family = family.lower()
    if not model_id and not family:
        return None
    for key in sorted(_KNOWN_LICENSE_MAPPINGS.keys(), key=len, reverse=True):
        if key in model_id or key in family:
            return key, _KNOWN_LICENSE_MAPPINGS[key]
    return None


def _check_license_consistency(card: dict) -> list[CardFinding]:
    """Heuristik: Lizenz-Felder gegen bekannte Mappings pruefen."""
    findings: list[CardFinding] = []
    model_id = card.get("model_id", "")
    family = card.get("model_family", "")
    matched = _match_family(model_id, family)
    if matched is None:
        return findings
    key, mapping = matched
    license_val = card.get("license")
    if license_val and license_val != mapping["license"]:
        findings.append(CardFinding(
            field="license",
            severity="error",
            message=f"Lizenz {license_val!r} widerspricht bekanntem Mapping fuer {key}: '{mapping['license']}'",
            current=license_val,
            suggested=mapping["license"],
        ))
    tier = card.get("weights_license_tier")
    if tier and tier != mapping["weights_license_tier"]:
        findings.append(CardFinding(
            field="weights_license_tier",
            severity="error",
            message=f"weights_license_tier '{tier}' widerspricht bekanntem Mapping fuer {key}: '{mapping['weights_license_tier']}'",
            current=tier,
            suggested=mapping["weights_license_tier"],
        ))
    return findings


def _check_community(card: dict) -> list[CardFinding]:
    """Pruefe ob community-Wert in kontrollierter Taxonomie liegt.

    Unbekannte Werte sind Fehler. suggested=None — LLM/Distributor soll
    den korrekten Namen erausfinden (via HuggingFace-Recherche im Tool-Use-Modus).
    """
    findings: list[CardFinding] = []
    community = card.get("community")
    if community and community not in _KNOWN_COMMUNITY_GROUPS:
        findings.append(CardFinding(
            field="community",
            severity="error",
            message=f"Community {community!r} ist nicht in der kontrollierten Taxonomie. Erlaubt: {', '.join(sorted(_KNOWN_COMMUNITY_GROUPS))}",
            current=community,
            suggested=None,
        ))
    return findings


def _check_license_text_fields(card: dict) -> list[CardFinding]:
    """Pre-finding: Textfelder pruefen, die alte Lizenz-Referenzen enthalten.

    Laeuft VOR dem LLM-Call auf der ORIGINAL-Card.
    Wenn die Lizenz laut Mapping geaendert werden muss, pruefe ob Textfelder
    noch die alte (falsche) Lizenz referenzieren. LLM MUSS diese Felder dann
    mit korrektem Text als suggested-Wert liefern.
    """
    findings: list[CardFinding] = []
    model_id = card.get("model_id", "")
    family = card.get("model_family", "")
    matched = _match_family(model_id, family)
    if matched is None:
        return findings
    key, mapping = matched
    current_license = str(card.get("license", ""))
    expected_license = mapping["license"]
    if current_license == expected_license:
        return findings

    is_expected_open = "Apache" in expected_license
    keywords = _RESTRICTED_KEYWORDS if is_expected_open else _OPEN_KEYWORDS

    for field_name in _LICENSE_CASCADE_FIELDS:
        val = card.get(field_name)
        if val is None:
            continue
        texts: list[str] = []
        if isinstance(val, str):
            texts.append(val)
        elif isinstance(val, list):
            texts.extend(str(item) for item in val if isinstance(item, str))
        else:
            continue
        for text in texts:
            for kw in keywords:
                if kw.lower() in text.lower():
                    findings.append(CardFinding(
                        field=field_name,
                        severity="error",
                        message=(
                            f"Text enthaelt '{kw}', aber Lizenz muss laut {key}-Mapping "
                            f"zu '{expected_license}' geaendert werden. "
                            f"Textfeld muss komplett neu geschrieben werden — "
                            f"suggested-Wert mit korrigiertem Text ist PFLICHT."
                        ),
                        current=kw,
                        suggested=None,
                    ))
                    break
            else:
                continue
            break
    return findings


def _ensure_license_consistency(card: dict) -> dict:
    """Konsistenz-Korrektur nach _apply_research_diff: wenn license geaendert
    wurde, pruefe ob weights_license_tier noch passt."""
    license_val = str(card.get("license", ""))
    tier = card.get("weights_license_tier")
    if "Apache" in license_val and tier == "restricted-weights":
        card["weights_license_tier"] = "open-weights"
    if "Terms of Use" in license_val and tier == "open-weights":
        card["weights_license_tier"] = "restricted-weights"
    return card


def _is_gguf_model(model_id: str, card: dict | None = None) -> bool:
    """Erkennt GGUF-Modelle anhand von Namensmustern oder Card-Feldern."""
    mid = model_id.lower()
    if re.search(r"q[2-8]_[k0-9]", mid):
        return True
    if "gguf" in mid:
        return True
    if re.search(r"(?:^|[-_])ud(?:[-_]|$)", mid):
        return True
    if card:
        mv = str(card.get("model_version", "")).lower()
        if "gguf" in mv:
            return True
        mfile = str(card.get("model_file", "")).lower()
        if "gguf" in mfile or re.search(r"q[2-8]_[k0-9]", mfile):
            return True
    return False


def _ensure_gguf_conventions(card: dict) -> dict:
    """Post-Apply GGUF-Korrektur: deployment_type, params_active_b, Preise.

    Läuft NACH allen Findings in _commit_card, um LLM-Korrekturen
    (z.B. Falschwert open-weights statt localweights) zuverlässig zu
    überschreiben.
    """
    model_id = str(card.get("model_id", ""))
    if not _is_gguf_model(model_id, card):
        return card

    changed: list[str] = []

    if card.get("deployment_type") != "localweights":
        card["deployment_type"] = "localweights"
        changed.append("deployment_type=localweights")

    if card.get("params_active_b") is None and card.get("parameter_architecture") == "dense":
        total = card.get("params_total_b")
        if total is not None:
            card["params_active_b"] = total
            changed.append(f"params_active_b={total}")

    if card.get("input_price_per_1m") is None:
        card["input_price_per_1m"] = 0.0
        changed.append("input_price_per_1m=0.0")
    if card.get("output_price_per_1m") is None:
        card["output_price_per_1m"] = 0.0
        changed.append("output_price_per_1m=0.0")

    if changed:
        logger.info("    🔧 GGUF-Konventionen: %s", ", ".join(changed))

    return card


_LICENSE_CASCADE_FIELDS = ("summary", "strengths", "known_limitations", "judge_context_hint", "weights_provenance_risk_rationale")

_RESTRICTED_KEYWORDS = ("restriktiv", "restricted", "Terms of Use", "mit Auflagen", "Gemma-Lizenz", "Gemma License")
_OPEN_KEYWORDS = ("Apache 2.0", "open-weights", "uneingeschraenkt")


def _check_license_cascade(card: dict) -> list[CardFinding]:
    """Pruefe ob Textfelder noch alte Lizenz-Referenzen enthalten nach Lizenz-Wechsel.

    Läuft NACH Lizenz-Korrektur (suggested-Werte bereits angewandt).
    Erkennt Inkonsistenzen zwischen dem neuen Lizenz-Wert und Texten.
    Prüft sowohl String-Felder als auch Listen von Strings.
    """
    findings: list[CardFinding] = []
    license_val = str(card.get("license", ""))
    is_open = "Apache" in license_val
    keywords = _RESTRICTED_KEYWORDS if is_open else _OPEN_KEYWORDS
    expected_severity = "error" if is_open else "warning"

    for field_name in _LICENSE_CASCADE_FIELDS:
        val = card.get(field_name)
        if val is None:
            continue
        texts: list[str] = []
        if isinstance(val, str):
            texts.append(val)
        elif isinstance(val, list):
            texts.extend(str(item) for item in val if isinstance(item, str))
        else:
            continue
        for text in texts:
            for kw in keywords:
                if kw.lower() in text.lower():
                    findings.append(CardFinding(
                        field=field_name,
                        severity=expected_severity,
                        message=f"Text enthaelt '{kw}', aber Lizenz ist '{license_val}'. Text muss aktualisiert werden.",
                        current=kw,
                        suggested=None,
                    ))
                    break
            else:
                continue
            break
    return findings


def _build_check_user_prompt(card: dict, editor_prompt: str) -> str:
    return (
        f"{editor_prompt}\n\n"
        "## Zu prüfende Card\n"
        "```json\n"
        f"{json.dumps(card, ensure_ascii=False, indent=2)}\n"
        "```\n"
    )


def _build_make_user_prompt(
    template: CardTemplate,
    existing: dict,
    editor_prompt: str,
) -> str:
    required = ", ".join(template.required_field_names)
    optional_names: tuple[str, ...] = tuple(f.name for f in template.optional_fields)
    optional = ", ".join(optional_names)
    return (
        f"{editor_prompt}\n\n"
        "## Pflichtfelder (alle ausfüllen, sofern nicht explizit null erlaubt)\n"
        f"{required}\n\n"
        "## Optionale Felder (nur falls passend)\n"
        f"{optional}\n\n"
        "## Bestehende Card (kann leer oder unvollständig sein)\n"
        "```json\n"
        f"{json.dumps(existing, ensure_ascii=False, indent=2)}\n"
        "```\n"
    )


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _parse_check_response(text: str) -> tuple[list[CardFinding], str, str | None]:
    parsed = _extract_json_object(text)
    if parsed is None:
        return [], "", f"Kein parsebares JSON in der LLM-Antwort: {text[:200]}…"
    findings: list[CardFinding] = []
    raw_findings = parsed.get("findings", [])
    if isinstance(raw_findings, list):
        for item in raw_findings:
            if not isinstance(item, dict):
                continue
            findings.append(CardFinding(
                field=str(item.get("field", "")),
                severity=str(item.get("severity", "info")),
                message=str(item.get("message", "")),
                current=item.get("current"),
                suggested=item.get("suggested"),
            ))
    summary = str(parsed.get("summary", ""))
    return findings, summary, None


def _parse_make_response(text: str) -> tuple[dict | None, str | None]:
    parsed = _extract_json_object(text)
    if parsed is None:
        return None, f"Kein parsebares JSON in der LLM-Antwort: {text[:200]}…"
    return parsed, None


def _preserve_operator_fields(original: dict, new: dict) -> dict:
    for k in OPERATOR_PROTECTED_FIELDS:
        if k in original:
            new[k] = original[k]
    return new


def _prefill_template_fields(card: dict, template: CardTemplate) -> dict:
    """Füllt alle Template-Felder (required + optional) mit Defaults auf.

    Wird VOR dem LLM-Call ausgeführt, damit das LLM eine vollständige
    Card-Struktur sieht und fehlende Felder (z.B. community) erkennt.
    """
    result = dict(card)
    added: list[str] = []
    for spec in template.required_fields + template.optional_fields:
        if spec.name not in result:
            result[spec.name] = spec.default
            added.append(spec.name)
    if added:
        logger.info("    📋 Template-Prefill: %d Felder ergänzt: %s", len(added), ", ".join(added))
    return result


def _validate_against_template(
    card: dict, template: CardTemplate
) -> tuple[dict, list[str]]:
    warnings: list[str] = []
    cleaned: dict[str, Any] = {}
    for k, v in card.items():
        if template.is_known(k):
            cleaned[k] = v
        else:
            warnings.append(f"Unbekanntes Feld verworfen: {k!r}")
    for spec in template.required_fields:
        if spec.name not in cleaned or spec.is_unknown_sentinel(cleaned.get(spec.name)):
            warnings.append(
                f"Pflichtfeld fehlt/leer: {spec.name!r} (type={spec.type})"
            )
    return cleaned, warnings


def _apply_check_fixes(card: dict, report: CardCheckReport) -> dict:
    merged = dict(card)
    for finding in report.findings:
        if finding.suggested is None:
            continue
        if finding.field and finding.field in merged:
            merged[finding.field] = finding.suggested
    return merged


def _check_murks(card: dict) -> list[CardFinding]:
    """Heuristik: CJK-Zeichen und em-dash in redaktionellen Texten.

    Wird VOR dem LLM-Call ausgefuehrt, damit die Findings dem LLM als
    zusaetzlicher Kontext mitgegeben werden koennen (Phase 3) und der
    Operator sie im Report sieht.
    """
    findings: list[CardFinding] = []
    for field in ("summary", "strengths", "known_limitations", "judge_context_hint"):
        val = card.get(field)
        if not isinstance(val, str):
            continue
        for ch in val:
            if any(lo <= ord(ch) <= hi for lo, hi in _CJK_RANGES):
                findings.append(CardFinding(
                    field=field,
                    severity="error",
                    message=(
                        f"CJK-Zeichen gefunden: {ch!r} (U+{ord(ch):04X}) — "
                        "redaktioneller Text sollte lateinische Schrift verwenden"
                    ),
                    current=ch,
                    suggested=None,
                ))
                break
        if field == "summary" and "—" in val:
            findings.append(CardFinding(
                field=field,
                severity="error",
                message="em-dash (—) im summary gefunden — laut Prompt Schritt 5 verboten",
                current="—",
                suggested=None,
            ))
    return findings


def _glob_model_cards(force: bool) -> list[tuple[str, Path]]:
    """Scannt alle Model-Cards im cards-Verzeichnis.

    Cards mit ``profile_verified=True`` werden übersprungen, es sei denn
    ``force`` ist ``True``.
    """
    base = cards_dir("model")
    targets: list[tuple[str, Path]] = []
    for p in sorted(base.glob("*.json")):
        if p.name == "_index.json":
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Konnte %s nicht laden: %s", p.name, exc)
            continue
        if not isinstance(data, dict):
            continue
        model_id = data.get("model_id") or p.stem
        if not force and data.get("profile_verified") is True:
            continue
        targets.append((model_id, p))
    return targets


def _discover_research_targets(args: argparse.Namespace) -> list[tuple[str, Path]]:
    """Targets fuer den Research-Modus (profile_verified-aware).

    - ``--card``: einzelne Card (Error wenn nicht existent).
    - sonst: alle Cards mit ``profile_verified != True``. Mit ``--force``
      werden auch verifizierte Cards einbezogen.
    """
    if args.card and args.card.lower() != "all":
        path = _find_card(args.card)
        if not path.exists():
            raise SystemExit(f"❌ Card nicht gefunden: {args.card}")
        return [(args.card, path)]
    return _glob_model_cards(args.force)


def _apply_research_diff(original: dict, response: dict) -> dict:
    """Uebertraegt die LLM-vorgeschlagenen Werte aus ``findings`` in die Card.

    Pro Finding wird ``suggested`` uebernommen wenn nicht None.
    Neue Felder (die noch nicht in der Card existieren) werden hinzugefuegt.
    """
    findings = response.get("findings", [])
    if not isinstance(findings, list):
        return original
    merged = dict(original)
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        suggested = finding.get("suggested")
        if suggested is None:
            continue
        field = finding.get("field")
        if not field:
            continue
        merged[field] = suggested
    return merged


def _build_research_user_prompt(card: dict, editor_prompt: str, pre_findings: list[CardFinding]) -> str:
    """User-Prompt fuer den Research-Modus: Card + Editor-Prompt + Pre-Findings."""
    text_card = {k: v for k, v in card.items() if k in _LLM_TEXT_FIELDS}
    structural_card = {k: v for k, v in card.items() if k not in _LLM_TEXT_FIELDS}

    parts: list[str] = [
        editor_prompt,
        "",
        "## Strukturelle Felder (bereits validiert — nicht aendern)",
        "```json",
        json.dumps(structural_card, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Zu pruefende Textfelder",
        "```json",
        json.dumps(text_card, ensure_ascii=False, indent=2),
        "```",
    ]
    if pre_findings:
        parts.append("")
        parts.append("## Heuristische Pre-Findings (vom Script gefunden)")
        parts.append(
            "Diese Befunde wurden vor dem LLM-Call erkannt. Behandle sie als "
            "zusaetzlichen Kontext:"
        )
        for f in pre_findings:
            parts.append(f"- `{f.field}` [{f.severity}]: {f.message}")
    return "\n".join(parts)


def _server_root_url(base_url: str) -> str:
    """Extract root URL from OpenAI-compatible base_url (strip /v1)."""
    return base_url.rstrip("/").removesuffix("/v1")


def _check_health(url: str, name: str, timeout: float = 3.0) -> bool:
    """Generic health check via GET. Returns True if server responds 200."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == _HTTP_OK
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def _reset_llama_context(base_url: str) -> None:
    """Reset llama.cpp KV cache via POST /slots/{id}?action=reset.

    Best-effort: Die OpenAI-compatible API ist stateless (kein Context-Leak
    zwischen Requests). Der Reset ist nur beim nativen /completion-Endpoint
    mit cache_prompt=true relevant.
    """
    root = _server_root_url(base_url)
    try:
        slots_url = f"{root}/slots"
        req = urllib.request.Request(slots_url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            slots = json.loads(resp.read())
        if not isinstance(slots, list):
            return
        for slot in slots:
            slot_id = slot.get("id", 0)
            reset_url = f"{slots_url}/{slot_id}?action=reset"
            reset_req = urllib.request.Request(reset_url, method="POST")
            urllib.request.urlopen(reset_req, timeout=5)
            logger.info("    🔄 Context-Reset: Slot %d", slot_id)
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        logger.debug("    ℹ️ Context-Reset uebersprungen: %s", exc)


def _ensure_mcp_running(mcp_url: str) -> bool:
    """Start MCP server if not already running. Returns True if available."""
    health_url = f"{mcp_url}/health"
    if _check_health(health_url, "MCP"):
        logger.info("    MCP-Server bereits aktiv (%s).", mcp_url)
        return True

    logger.info("    🚀 Starte MCP-Server (%s)...", mcp_url)
    subprocess.Popen(
        "source ~/.api_keys 2>/dev/null; python3 cruciblemark-mcp/server.py --mode live",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        cwd=str(Path(__file__).parent.parent),
    )
    for _ in range(30):
        time.sleep(1)
        if _check_health(health_url, "MCP"):
            logger.info("    ✅ MCP-Server gestartet.")
            return True
    logger.error("    ❌ MCP-Server start fehlgeschlagen (30s Timeout).")
    return False


def _stop_mcp_server() -> None:
    """Stop MCP server process."""
    try:
        subprocess.run(
            ["pkill", "-f", "cruciblemark-mcp/server.py"],
            capture_output=True, timeout=5,
        )
        logger.info("    🛑 MCP-Server gestoppt.")
    except (subprocess.TimeoutExpired, OSError) as exc:
        logger.warning("    ⚠️ MCP-Server stop fehlgeschlagen: %s", exc)

