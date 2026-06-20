#!/usr/bin/env python3
"""LLM-gestütztes Model-Card-Management.

Drei Modi:

- ``--mode check`` — bestehende Cards inhaltlich vom LLM prüfen lassen, Bericht
  ausgeben (oder mit ``--fix`` die vorgeschlagenen Korrekturen direkt anwenden).
- ``--mode make``  — fehlende/ungültige Felder einer Card vom LLM ausfüllen
  lassen und die Card zurückschreiben.
- ``--mode research`` — inhaltliche Recherche via LLM (Preise, Beschreibung,
  Sonderzeichen-Erkennung) mit ``profile_verified``-Lock-Mechanismus.

Folgt den Architekturprinzipien von ``scripts/analysis/generate_review.py``
(Card-für-Card, Retry, Logging, SSoT-Lookups). API-Zugriff läuft direkt über
die ``openai``-Python-SDK, damit ``OPENAI_API_KEY`` und ``OPENAI_BASE_URL``
nativ unterstützt werden und jedes OpenAI-kompatible Endpoint (llama-server,
OpenRouter, Groq) angesprochen werden kann.

Dry-Run als Default — keine Schreibvorgänge an Produktions-Cards ohne
explizite Bestätigung (``--fix`` bzw. ``--write``).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import httpx
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Optional

import yaml

try:
    from openai import OpenAI
except ImportError as exc:  # pragma: no cover - ImportError wird zur Laufzeit abgefangen
    raise SystemExit(
        "❌ Das 'openai' Python-Paket ist nicht installiert. "
        "Installiere es via `pip install openai` (siehe requirements.txt)."
    ) from exc
import openai  # noqa: PLC0415 — needed for exception types

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.card_template import (  # noqa: E402
    CardTemplate,
    cards_dir,
    load_card_template,
    rebuild_card_index,
)
from utils.model_utils import _card_path, _find_card


MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0
PER_CALL_TIMEOUT_S = 60

EDITOR_PROMPTS_PATH = ROOT_DIR / "config" / "editor_prompts.yaml"
LOG_PATH = ROOT_DIR / "logs" / "manage_model_cards.log"

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


@dataclass
class CardFinding:
    field: str
    severity: str
    message: str
    current: Any = None
    suggested: Any = None


@dataclass
class CardCheckReport:
    model_id: str
    card_path: Path
    findings: list[CardFinding] = field(default_factory=list)
    summary: str = ""
    raw_response: str = ""
    parse_error: Optional[str] = None
    error: Optional[str] = None
    would_write: bool = False


@dataclass
class CardMakeReport:
    model_id: str
    card_path: Path
    new_card: dict = field(default_factory=dict)
    raw_response: str = ""
    parse_error: Optional[str] = None
    error: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    would_write: bool = False
    wrote: bool = False


@dataclass
class RunSummary:
    processed: int = 0
    skipped: int = 0
    errors: int = 0
    check_reports: list[CardCheckReport] = field(default_factory=list)
    make_reports: list[CardMakeReport] = field(default_factory=list)
    research_reports: list[ResearchReport] = field(default_factory=list)


@dataclass
class ResearchReport:
    model_id: str
    card_path: Path
    findings: list[CardFinding] = field(default_factory=list)
    summary: str = ""
    raw_response: str = ""
    parse_error: Optional[str] = None
    error: Optional[str] = None
    locked: bool = False
    unlocked: bool = False
    would_write: bool = False
    wrote: bool = False
    profile_verified: bool = False
    backup_path: Optional[Path] = None


@dataclass
class LLMSpec:
    provider_name: str
    model: str
    base_url: str
    api_key: Optional[str]
    max_tokens: int
    temperature: float


class LLMSession:
    def __init__(
        self,
        model: str,
        base_url: str,
        api_key: Optional[str],
        max_retries: int,
        timeout_s: int,
    ) -> None:
        self.model = model
        self.max_retries = max_retries
        self.timeout_s = timeout_s
        kwargs: dict[str, Any] = {}
        if base_url:
            kwargs["base_url"] = base_url
        if api_key:
            kwargs["api_key"] = api_key
        self._client = OpenAI(**kwargs)

    def query(self, system: str, user: str, temperature: float) -> str:
        last_exc: Optional[Exception] = None
        timeout = httpx.Timeout(timeout=self.timeout_s, connect=10.0, read=self.timeout_s, pool=self.timeout_s)
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=temperature,
                    timeout=timeout,
                )
                content = response.choices[0].message.content or ""
                return content
            except openai.APIError as exc:  # noqa: BLE001 — wir retryen alle API-Fehler
                last_exc = exc
                if attempt >= self.max_retries:
                    break
                backoff = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    "LLM-Aufruf fehlgeschlagen (Versuch %d/%d): %s — retry in %.1fs",
                    attempt, self.max_retries, exc, backoff,
                )
                time.sleep(backoff)
        assert last_exc is not None
        raise last_exc


logger = logging.getLogger("manage_model_cards")


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
    path = ROOT_DIR / "benchmark_config.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


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
    with open(EDITOR_PROMPTS_PATH, "r", encoding="utf-8") as f:
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


def _parse_tool_call(text: str) -> tuple[dict[str, Any] | None, str | None]:
    stripped = re.sub(r"```(?:json)?\s*", "", text)
    stripped = stripped.replace("```", "")
    candidates = re.findall(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}", stripped, re.DOTALL)
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if "tool_call" in parsed and isinstance(parsed["tool_call"], dict):
                return parsed["tool_call"], None
            if "name" in parsed and "parameters" in parsed:
                return {"name": parsed["name"], "parameters": parsed["parameters"]}, None
            if "name" in parsed and "arguments" in parsed:
                return {"name": parsed["name"], "parameters": parsed["arguments"]}, None
        except (json.JSONDecodeError, ValueError):
            continue
    depth = 0
    start = None
    for i, ch in enumerate(stripped):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                fragment = stripped[start : i + 1]
                try:
                    parsed = json.loads(fragment)
                    if "tool_call" in parsed and isinstance(parsed["tool_call"], dict):
                        return parsed["tool_call"], None
                    if "name" in parsed and "parameters" in parsed:
                        return {"name": parsed["name"], "parameters": parsed["parameters"]}, None
                    if "name" in parsed and "arguments" in parsed:
                        return {"name": parsed["name"], "parameters": parsed["arguments"]}, None
                except (json.JSONDecodeError, ValueError):
                    pass
                start = None
    return None, "No valid tool_call JSON found"


def _call_mcp_tool(base_url: str, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": params,
        },
    }).encode("utf-8")
    req = urllib.request.Request(
        base_url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            rpc_response = json.loads(resp.read().decode("utf-8"))
        if "error" in rpc_response:
            err = rpc_response["error"]
            return {"status": "error", "status_code": err.get("code"), "error": err.get("message", "JSON-RPC error")}
        return rpc_response.get("result", {})
    except urllib.error.HTTPError as exc:
        return {"status": "error", "status_code": exc.code, "error": str(exc)}
    except urllib.error.URLError as exc:
        return {"status": "error", "status_code": None, "error": str(exc.reason)}
    except Exception as exc:
        return {"status": "error", "status_code": None, "error": str(exc)}


def _extract_tool_content(transcript: dict[str, Any]) -> str:
    content_list = transcript.get("content")
    if content_list and isinstance(content_list, list):
        for item in content_list:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text", "").strip()
                if text:
                    return text
    results = transcript.get("results")
    if results and isinstance(results, list):
        parts = []
        for r in results:
            if not isinstance(r, dict):
                continue
            title = r.get("title", "")
            url = r.get("url", "")
            excerpt = r.get("excerpt") or r.get("content", "")
            line = "\n".join(filter(None, [title, url, excerpt]))
            if line.strip():
                parts.append(line.strip())
        if parts:
            return "\n\n".join(parts)
    excerpt = transcript.get("content_excerpt")
    if excerpt:
        return str(excerpt)
    status = transcript.get("status", "unknown")
    error = transcript.get("error", "")
    return f"[Tool status: {status}]" + (f" — {error}" if error else "")

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


def _extract_json_object(text: str) -> Optional[dict]:
    if not text:
        return None
    m = _JSON_FENCE_RE.search(text)
    if m:
        candidate = m.group(1)
    else:
        first = text.find("{")
        last = text.rfind("}")
        if first == -1 or last == -1 or last <= first:
            return None
        candidate = text[first:last + 1]
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return parsed
    # Fallback: text might contain multiple JSON objects; try extracting nested ones
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
                inner = text[start : i + 1]
                try:
                    inner_parsed = json.loads(inner)
                    if isinstance(inner_parsed, dict):
                        return inner_parsed
                except json.JSONDecodeError:
                    pass
                start = None
    return None


def _parse_check_response(text: str) -> tuple[list[CardFinding], str, Optional[str]]:
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


def _parse_make_response(text: str) -> tuple[Optional[dict], Optional[str]]:
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


# ---------------------------------------------------------------------------
# Server lifecycle helpers (MCP + llama.cpp)
# ---------------------------------------------------------------------------

def _server_root_url(base_url: str) -> str:
    """Extract root URL from OpenAI-compatible base_url (strip /v1)."""
    return base_url.rstrip("/").removesuffix("/v1")


def _check_health(url: str, name: str, timeout: float = 3.0) -> bool:
    """Generic health check via GET. Returns True if server responds 200."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
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


class Researcher:
    """Recherchiert Card-Inhalte via LLM mit profile_verified-Lock-Mechanismus.

    Lock-Phase: ``profile_verified`` wird auf ``False`` gesetzt (Resumption-Marker
    bei Abbruch). Bei Erfolg wird es wieder auf ``True`` gesetzt, inkl.
    ``profile_verified_at`` und ``profile_verified_by``.

    Backup: vor dem Schreiben wird ``<card>.pre-research.bak`` angelegt und
    bei Erfolg geloescht (Sicherheitsnetz fuer Diff-Inspektion).
    """

    BACKUP_SUFFIX = ".pre-research.bak"

    def __init__(
        self,
        args: argparse.Namespace,
        session: LLMSession,
        template: CardTemplate,
        editor_prompt: str,
        llm_spec: LLMSpec,
    ) -> None:
        self.args = args
        self.session = session
        self.template = template
        self.editor_prompt = editor_prompt
        self.llm_spec = llm_spec
        self.summary = RunSummary()

    # ------------------------------------------------------------------
    # Shared helpers for lock / backup / commit / findings extraction
    # ------------------------------------------------------------------

    def _load_card(self, path: Path, report: ResearchReport) -> dict | None:
        """Load card JSON or set report.error and return None."""
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            report.error = f"Card nicht lesbar: {exc}"
            self.summary.errors += 1
            self.summary.research_reports.append(report)
            return None

    def _apply_lock(
        self, original: dict, path: Path, report: ResearchReport
    ) -> bool:
        """Set profile_verified=False on disk. Returns False on failure."""
        if self.args.dry_run:
            return True
        locked = dict(original)
        locked["profile_verified"] = False
        locked["profile_verified_at"] = None
        locked["profile_verified_by"] = None
        locked["last_modified_at"] = date.today().isoformat()
        try:
            path.write_text(
                json.dumps(locked, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report.locked = True
            logger.info("    🔓 Lock geoeffnet: %s (profile_verified=false)", path.name)
            return True
        except OSError as exc:
            report.error = f"Lock fehlgeschlagen: {exc}"
            self.summary.errors += 1
            self.summary.research_reports.append(report)
            return False

    def _create_backup(
        self, path: Path, report: ResearchReport
    ) -> Path | None:
        """Create .pre-research.bak if not dry_run. Returns backup path."""
        if self.args.dry_run:
            return None
        backup_path = path.with_name(path.name + self.BACKUP_SUFFIX)
        try:
            backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            report.backup_path = backup_path
            return backup_path
        except OSError as exc:
            logger.warning("    ⚠️ Backup fehlgeschlagen: %s — weiter ohne.", exc)
            return None

    def _extract_findings(
        self, parsed: dict, report: ResearchReport, *, text_only: bool = True
    ) -> None:
        """Append LLM findings from parsed JSON to report.

        Args:
            text_only: If True, discard findings for structural fields
                (only keep _LLM_TEXT_FIELDS). Used in non-tooluse mode where
                the LLM cannot actually search the web.
        """
        findings_raw = parsed.get("findings", [])
        if not isinstance(findings_raw, list):
            return
        for item in findings_raw:
            if not isinstance(item, dict):
                continue
            field_name = str(item.get("field", ""))
            if text_only and field_name not in _LLM_TEXT_FIELDS:
                logger.debug("    🗑️ LLM-Finding verworfen (strukturelles Feld): %s", field_name)
                continue
            suggested = item.get("suggested")
            if suggested is None or (isinstance(suggested, str) and not suggested.strip()):
                logger.debug("    🗑️ LLM-Finding verworfen (kein suggested): %s", field_name)
                continue
            report.findings.append(CardFinding(
                field=field_name,
                severity=str(item.get("severity", "info")),
                message=str(item.get("message", "")),
                current=item.get("current"),
                suggested=suggested,
            ))
        report.summary = str(parsed.get("summary", ""))

    def _commit_card(
        self,
        original: dict,
        parsed: dict,
        path: Path,
        report: ResearchReport,
        backup_path: Path | None,
    ) -> None:
        """Merge, validate and write (or dry-run) the card. Unlocks on success."""
        merged = dict(original)
        for f in report.findings:
            if f.suggested is not None and f.field:
                merged[f.field] = f.suggested
        merged = _ensure_license_consistency(merged)
        merged = _ensure_gguf_conventions(merged)
        report.findings.extend(_check_license_cascade(merged))
        merged = _preserve_operator_fields(original, merged)
        cleaned, warnings = _validate_against_template(merged, self.template)
        for w in warnings:
            logger.info("    · %s", w)
            report.findings.append(CardFinding(
                field=w.split(":")[0].strip() if ":" in w else w,
                severity="warning",
                message=w,
                current=None,
                suggested=None,
            ))

        report.would_write = True
        if self.args.dry_run:
            logger.info(
                "    [DRY-RUN] Wuerde %s aktualisieren (%d Felder, %d Findings).",
                path.name, len(cleaned), len(report.findings),
            )
        else:
            final = dict(cleaned)
            final_checks: list[CardFinding] = []
            final_checks.extend(_check_license_consistency(dict(final)))
            final_checks.extend(_check_license_text_fields(dict(final)))
            final_checks.extend(_check_community(dict(final)))
            pflicht_warnings = [w for w in warnings if "Pflichtfeld" in w]
            has_remaining_errors = (
                any(f.severity == "error" for f in final_checks)
                or len(pflicht_warnings) > 0
            )
            if has_remaining_errors:
                err_count = len([f for f in final_checks if f.severity == "error"]) + len(pflicht_warnings)
                logger.warning("    ⚠️ profile_verified bleibt false — %d verbleibende Probleme.", err_count)
                final["profile_verified"] = False
                final["profile_verified_at"] = None
                final["profile_verified_by"] = None
            else:
                final["profile_verified"] = True
                final["profile_verified_at"] = date.today().isoformat()
                final["profile_verified_by"] = f"llm:{self.llm_spec.model}"
            final["last_modified_at"] = date.today().isoformat()
            path.write_text(
                json.dumps(final, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report.unlocked = True
            report.wrote = True
            report.profile_verified = bool(final.get("profile_verified", False))
            logger.info("    🔒 Lock geschlossen: %s (profile_verified=%s)", path.name, report.profile_verified)
            if backup_path and backup_path.exists():
                try:
                    backup_path.unlink()
                    report.backup_path = None
                except OSError as exc:
                    logger.warning("    ⚠️ Backup loeschen fehlgeschlagen: %s", exc)

        self.summary.processed += 1

    def _handle_research_error(
        self, exc: Exception, path: Path, report: ResearchReport
    ) -> None:
        """Common error handler for research exceptions."""
        report.error = str(exc)
        logger.error("    🔓 Lock bleibt offen: %s (Fehler: %s)", path.name, exc)
        self.summary.errors += 1
        self.summary.research_reports.append(report)

    def run(self) -> RunSummary:
        targets = _discover_research_targets(self.args)
        if not targets:
            logger.info("⚠️  Keine Ziel-Cards gefunden (alle bereits verifiziert?).")
            return self.summary

        tooluse = getattr(self.args, "tooluse", False)
        mcp_url = getattr(self.args, "mcp_url", "http://localhost:8765")
        mcp_started_by_us = False

        if tooluse:
            mcp_started_by_us = _ensure_mcp_running(mcp_url)
            if not mcp_started_by_us and not _check_health(f"{mcp_url}/health", "MCP"):
                logger.error("❌ MCP-Server nicht erreichbar — Abbruch.")
                return self.summary
            logger.info(
                "🔬 Card-Researcher Tool-Use: %s/%s (MCP=%s)",
                self.llm_spec.provider_name, self.llm_spec.model, mcp_url,
            )
        else:
            logger.info(
                "🔬 Card-Researcher LLM: %s/%s (base_url=%s)",
                self.llm_spec.provider_name, self.llm_spec.model, self.llm_spec.base_url,
            )
        logger.info("📦 %d Card(s) zu recherchieren.", len(targets))

        max_cards = getattr(self.args, "max_cards", 0)
        if max_cards > 0:
            targets = targets[:max_cards]
            logger.info("    🔢 Limitiert auf %d Cards pro Run.", max_cards)

        llm_root = _server_root_url(self.llm_spec.base_url)
        try:
            for idx, (mid, path) in enumerate(targets, 1):
                if idx > 1:
                    pause = getattr(self.args, 'pause', 1.0)
                    time.sleep(pause)
                    logger.info("    ⏸ Pause %.1fs vor nächster Card.", pause)

                if not _check_health(f"{llm_root}/health", "llama.cpp", timeout=5):
                    logger.error("    ❌ llama.cpp nicht erreichbar — überspringe %s.", mid)
                    self.summary.errors += 1
                    continue

                print(f"\n[{idx}/{len(targets)}] {mid}")
                logger.info("[%d/%d] %s — %s", idx, len(targets), mid, path.name)
                if tooluse:
                    self._research_tooluse_one(mid, path, idx, len(targets))
                else:
                    self._research_one(mid, path, idx, len(targets))

                _reset_llama_context(self.llm_spec.base_url)
        finally:
            if mcp_started_by_us:
                _stop_mcp_server()

        remaining = len(_discover_research_targets(self.args))
        if remaining > 0:
            logger.info(
                "📊 Fortschritt: %d verarbeitet, %d noch offen. "
                "Server neustarten und erneut laufen lassen.",
                self.summary.processed, remaining,
            )

        return self.summary

    def _research_one(self, mid: str, path: Path, idx: int, total: int) -> ResearchReport:
        report = ResearchReport(model_id=mid, card_path=path)

        original = self._load_card(path, report)
        if original is None:
            return report

        original = _prefill_template_fields(original, self.template)

        pre_findings = _check_murks(original)
        pre_findings.extend(_check_license_consistency(original))
        pre_findings.extend(_check_community(original))
        pre_findings.extend(_check_license_text_fields(original))
        report.findings.extend(pre_findings)

        if not self._apply_lock(original, path, report):
            return report

        backup_path = self._create_backup(path, report)

        try:
            user_prompt = _build_research_user_prompt(original, self.editor_prompt, pre_findings)
            response = self.session.query(
                system=_RESEARCH_SYSTEM_INSTRUCTION,
                user=user_prompt,
                temperature=self.llm_spec.temperature,
            )
            report.raw_response = response

            parsed = _extract_json_object(response)
            if parsed is None:
                report.parse_error = f"Kein parsebares JSON: {response[:200]}…"
                logger.error("    ❌ Recherche fehlgeschlagen — Lock bleibt offen.")
                self.summary.errors += 1
                self.summary.research_reports.append(report)
                return report

            self._extract_findings(parsed, report)
            self._commit_card(original, parsed, path, report, backup_path)
        except (OSError, json.JSONDecodeError, openai.APIError, ValueError) as exc:  # noqa: BLE001
            self._handle_research_error(exc, path, report)
            return report

        self.summary.research_reports.append(report)
        return report

    def _research_tooluse_one(self, mid: str, path: Path, idx: int, total: int) -> ResearchReport:
        report = ResearchReport(model_id=mid, card_path=path)
        mcp_url = getattr(self.args, "mcp_url", "http://localhost:8765")

        original = self._load_card(path, report)
        if original is None:
            return report

        original = _prefill_template_fields(original, self.template)

        pre_findings = _check_murks(original)
        pre_findings.extend(_check_license_consistency(original))
        pre_findings.extend(_check_community(original))
        pre_findings.extend(_check_license_text_fields(original))
        report.findings.extend(pre_findings)

        if not self._apply_lock(original, path, report):
            return report

        backup_path = self._create_backup(path, report)

        tool_schema_json = json.dumps(TOOL_SCHEMAS, ensure_ascii=False, indent=2)
        system_prompt = (
            "Du bist ein Card-Researcher mit Internetzugang.\n\n"
            "Verfügbare Tools:\n"
            f"{tool_schema_json}\n\n"
            "Arbeitsablauf:\n"
            "1. Wenn du Informationen recherchieren musst, antworte AUSSCHLIESSLICH mit:\n"
            '   {"tool_call": {"name": "web_search", "parameters": {"query": "..."}}}\n'
            "   ODER\n"
            '   {"tool_call": {"name": "fetch", "parameters": {"url": "...", "max_chars": 3000}}}\n'
            "2. Ich liefere dir das Tool-Ergebnis zurueck.\n"
            "3. Wiederhole Schritt 1-2 bis du genug Informationen hast.\n"
            '4. Wenn du fertig bist, antworte AUSSCHLIESSLICH mit einem JSON-Objekt:\n'
            '{"findings": [...], "summary": "..."}\n\n'
            "Pflicht-Pruefungen:\n"
            "1. Lizenz: Recherchiere die korrekte Lizenz (z.B. Gemma 4 = Apache 2.0).\n"
            "2. Community: Wenn community nicht in [Unsloth, mradermacher, HauhauCS, ARA-APEX],\n"
            "   recherchiere auf HuggingFace ob eine Gruppe mit diesem Namen existiert.\n"
            "   Wenn nicht gefunden: community=null, in known_limitations dokumentieren.\n"
            "3. GGUF-Konsistenz: deployment_type=localweights, Preise=0.0 bei GGUF-Modellen.\n"
            "4. Preise, Context-Window, Knowledge-Cutoff, Display-Name, Summary.\n"
            "5. TEXTFELDER BEI LIZENZ-WECHSEL: Wenn sich die Lizenz aendert (erkennbar\n"
            "   an Pre-Findings), MUESSEN ALLE Textfelder aktualisiert werden, die die\n"
            "   alte Lizenz referenzieren: summary, strengths, known_limitations,\n"
            "   judge_context_hint, weights_provenance_risk_rationale. Jedes dieser\n"
            "   Felder braucht ein Finding mit einem KOMPLETT NEU GESCHRIEBENEN Text\n"
            "   als suggested-Wert. Nur einzelne Woerter ersetzen reicht NICHT.\n\n"
            "Regeln:\n"
            "- Nutze web_search um Preise, Context-Window, Knowledge-Cutoff etc. zu finden.\n"
            "- Nutze fetch um konkrete URLs (Hersteller-Seiten, HF-Cards) zu lesen.\n"
            "- Antworte NUR mit JSON — kein Markdown-Fence, keine Kommentare, kein Text davor oder danach.\n"
            "- Erfinde keine Inhalte — alles muss aus Tool-Ergebnissen stammen.\n"
            "- Fuer JEDES Finding MUSS ein 'suggested'-Wert angegeben werden.\n"
            "- WICHTIG: Deine Antwort MUSS ein gueltiges JSON-Objekt sein. Kein Fliesstext."
        )

        tool_results: list[str] = []
        max_tool_rounds = 3
        final_parsed: dict | None = None

        try:
            for round_num in range(1, max_tool_rounds + 1):
                text_card = {k: v for k, v in original.items() if k in _LLM_TEXT_FIELDS}
                structural_card = {k: v for k, v in original.items() if k not in _LLM_TEXT_FIELDS}
                parts = [
                    self.editor_prompt,
                    "",
                    "## Strukturelle Felder (vom Script validiert)",
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
                    parts.append("## Heuristische Pre-Findings")
                    for f in pre_findings:
                        parts.append(f"- `{f.field}` [{f.severity}]: {f.message}")
                if tool_results:
                    parts.append("")
                    parts.append("## Tool-Ergebnisse bisher")
                    for i, tr in enumerate(tool_results, 1):
                        parts.append(f"### Ergebnis {i}")
                        parts.append(tr)
                user_prompt = "\n".join(parts)

                try:
                    response = self.session.query(
                        system=system_prompt,
                        user=user_prompt,
                        temperature=self.llm_spec.temperature,
                    )
                except Exception as exc:
                    logger.error("    ❌ LLM-Call fehlgeschlagen (Runde %d): %s", round_num, exc)
                    report.error = f"LLM-Call Runde {round_num}: {exc}"
                    self.summary.errors += 1
                    self.summary.research_reports.append(report)
                    return report

                if round_num == max_tool_rounds:
                    report.raw_response = response

                tool_call, parse_err = _parse_tool_call(response)
                if tool_call is not None:
                    tool_name = tool_call.get("name", "")
                    tool_params = tool_call.get("parameters", {})
                    logger.info("    🔧 Runde %d: Tool-Call '%s' mit params=%s", round_num, tool_name, json.dumps(tool_params, ensure_ascii=False)[:200])
                    transcript = _call_mcp_tool(mcp_url, tool_name, tool_params)
                    content = _extract_tool_content(transcript)
                    tool_results.append(f"Tool: {tool_name}\n{content}")
                    logger.info("    📥 Runde %d: Tool-Ergebnis (%d chars)", round_num, len(content))
                    continue

                if parse_err:
                    if round_num < max_tool_rounds:
                        logger.warning("    ⚠️ Runde %d: Kein Tool-Call, kein findings-JSON — retry: %s | Response: %s", round_num, parse_err[:100], response[:300])
                        continue
                    else:
                        report.parse_error = f"Kein parsebares JSON nach {max_tool_rounds} Runden: {parse_err[:200]}"
                        logger.error("    ❌ Keine finale Antwort nach %d Runden. Response: %s", round_num, response[:1500])
                        self.summary.errors += 1
                        self.summary.research_reports.append(report)
                        return report

                final_parsed = _extract_json_object(response)
                if final_parsed is None:
                    report.parse_error = f"Kein parsebares JSON: {response[:200]}…"
                    logger.error("    ❌ Runde %d: Kein parsebares JSON.", round_num)
                    self.summary.errors += 1
                    self.summary.research_reports.append(report)
                    return report

                if "findings" in final_parsed:
                    break

            if final_parsed is None:
                final_parsed = {}

            self._extract_findings(final_parsed, report, text_only=False)
            self._commit_card(original, final_parsed, path, report, backup_path)
        except (OSError, json.JSONDecodeError, openai.APIError, ValueError) as exc:  # noqa: BLE001
            self._handle_research_error(exc, path, report)

        self.summary.research_reports.append(report)
        return report


def _render_research_markdown_report(reports: list[ResearchReport], today: str) -> str:
    lines: list[str] = [
        f"# Model Card Research Report — {today}",
        "",
        "**Modus:** research",
        f"**Verarbeitet:** {sum(1 for r in reports if not r.error and r.parse_error is None)}"
        f" · **Recherche-Fehler:** {sum(1 for r in reports if r.error or r.parse_error)}"
        f" · **Murks-Findings:** "
        f"{sum(1 for r in reports for f in r.findings if f.severity == 'error')}",
        "",
    ]
    for r in reports:
        lines.append(f"## {r.model_id}")
        lines.append("")
        if r.error:
            lines.append(f"- ❌ Fehler: {r.error}")
        elif r.parse_error:
            lines.append(f"- ⚠️ Parse-Fehler: {r.parse_error}")
        elif not r.findings:
            lines.append("- ✅ keine Findings")
        else:
            errors = sum(1 for f in r.findings if f.severity == "error")
            warnings = sum(1 for f in r.findings if f.severity == "warning")
            infos = sum(1 for f in r.findings if f.severity == "info")
            lines.append(
                f"- 🔍 {len(r.findings)} Findings "
                f"({errors} errors, {warnings} warnings, {infos} info)"
            )
            for f in r.findings:
                icon = {"error": "🔴", "warning": "🟡", "info": "ℹ️"}.get(f.severity, "•")
                lines.append(f"  - {icon} `{f.field}` — {f.message}")
        if r.summary:
            lines.append(f"  - _{r.summary}_")
        if r.locked and not r.unlocked:
            lines.append("  - _🔓 Lock offen (profile_verified=false) — bei naechstem Lauf Resumption_")
        elif r.unlocked:
            if r.profile_verified:
                lines.append("  - _🔒 Lock geschlossen (profile_verified=true)_")
            else:
                lines.append("  - _🔒 Lock geschlossen (profile_verified=false) — error-Findings vorhanden_")
        lines.append("")
    return "\n".join(lines)


def _discover_targets(
    args: argparse.Namespace,
) -> list[tuple[str, Path]]:
    if args.card:
        if args.mode == "check":
            path = _find_card(args.card)
            if not path.exists():
                raise SystemExit(f"❌ Card nicht gefunden: {args.card}")
            return [(args.card, path)]
        path = _card_path(args.card, for_write=True)
        if not path.exists():
            logger.info("ℹ️  Card existiert nicht: %s — wird im 'make'-Modus erzeugt.", args.card)
        return [(args.card, path)]

    return _glob_model_cards(args.force)


def _render_markdown_report(
    reports: list[CardCheckReport], today: str, *, mode_label: str = "check (dry-run)"
) -> str:
    lines: list[str] = [
        f"# Model Card Check Report — {today}",
        "",
        f"**Modus:** {mode_label}",
        f"**Verarbeitet:** {sum(1 for r in reports if not r.error and r.parse_error is None)}"
        f" · **Übersprungen:** 0"
        f" · **Fehler:** {sum(1 for r in reports if r.error or r.parse_error)}",
        "",
    ]
    for r in reports:
        lines.append(f"## {r.model_id}")
        lines.append("")
        if r.error:
            lines.append(f"- ❌ Fehler: {r.error}")
        elif r.parse_error:
            lines.append(f"- ⚠️ Parse-Fehler: {r.parse_error}")
        elif not r.findings:
            lines.append("- ✅ keine Findings")
        else:
            errors = sum(1 for f in r.findings if f.severity == "error")
            warnings = sum(1 for f in r.findings if f.severity == "warning")
            infos = sum(1 for f in r.findings if f.severity == "info")
            lines.append(
                f"- 🔍 {len(r.findings)} Findings "
                f"({errors} errors, {warnings} warnings, {infos} info)"
            )
            for f in r.findings:
                icon = {"error": "🔴", "warning": "🟡", "info": "ℹ️"}.get(f.severity, "•")
                lines.append(f"  - {icon} `{f.field}` — {f.message}")
        if r.summary:
            lines.append(f"  - _{r.summary}_")
        lines.append("")
    return "\n".join(lines)


class CardManager:
    def __init__(
        self,
        args: argparse.Namespace,
        session: LLMSession,
        template: CardTemplate,
        editor_prompt: str,
        llm_spec: LLMSpec,
    ) -> None:
        self.args = args
        self.session = session
        self.template = template
        self.editor_prompt = editor_prompt
        self.llm_spec = llm_spec
        self.summary = RunSummary()

    def run(self) -> RunSummary:
        targets = _discover_targets(self.args)
        if not targets:
            logger.info("⚠️  Keine Ziel-Cards gefunden.")
            return self.summary

        logger.info(
            "🔧 Card-Manager LLM: %s/%s (base_url=%s)",
            self.llm_spec.provider_name, self.llm_spec.model, self.llm_spec.base_url,
        )
        logger.info("📦 %d Card(s) zu verarbeiten.", len(targets))

        for idx, (mid, path) in enumerate(targets, 1):
            print(f"\n[{idx}/{len(targets)}] {mid}")
            logger.info("[%d/%d] %s — %s", idx, len(targets), mid, path.name)
            if self.args.mode == "check":
                self._check_one(mid, path, idx, len(targets))
            else:
                self._make_one(mid, path, idx, len(targets))
        return self.summary

    def _check_one(
        self, mid: str, path: Path, idx: int, total: int
    ) -> CardCheckReport:
        report = CardCheckReport(model_id=mid, card_path=path)
        try:
            card = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            report.error = f"Card nicht lesbar: {exc}"
            self.summary.errors += 1
            self.summary.check_reports.append(report)
            return report

        user_prompt = _build_check_user_prompt(card, self.editor_prompt)
        try:
            response = self.session.query(
                system=_CHECK_SYSTEM_INSTRUCTION,
                user=user_prompt,
                temperature=self.llm_spec.temperature,
            )
        except (openai.APIError, ValueError) as exc:  # noqa: BLE001
            report.error = str(exc)
            self.summary.errors += 1
            self.summary.check_reports.append(report)
            return report

        report.raw_response = response
        findings, summary, parse_err = _parse_check_response(response)
        report.findings = findings
        report.summary = summary
        report.parse_error = parse_err
        if parse_err:
            self.summary.errors += 1
        else:
            self.summary.processed += 1
            if findings:
                err_n = sum(1 for f in findings if f.severity == "error")
                warn_n = sum(1 for f in findings if f.severity == "warning")
                print(f"  ⚠  {len(findings)} Findings ({err_n} errors, {warn_n} warnings)")

        if self.args.fix and report.parse_error is None and not report.error:
            merged = _apply_check_fixes(card, report)
            merged = _preserve_operator_fields(card, merged)
            cleaned, warnings = _validate_against_template(merged, self.template)
            for w in warnings:
                logger.info("    · %s", w)
                report.findings.append(CardFinding(
                    field=w.split(":")[0].strip() if ":" in w else w,
                    severity="warning",
                    message=w,
                    current=None,
                    suggested=None,
                ))
            report.would_write = True
            if self.args.dry_run:
                logger.info("    [DRY-RUN] Würde %s aktualisieren.", path.name)
            else:
                path.write_text(
                    json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                rebuild_card_index("model")
                logger.info("    ✅ %s aktualisiert.", path.name)
        elif self.args.fix and (report.parse_error or report.error):
            logger.info("    [FIX übersprungen] %s", report.parse_error or report.error)

        self.summary.check_reports.append(report)
        return report

    def _make_one(
        self, mid: str, path: Path, idx: int, total: int
    ) -> CardMakeReport:
        report = CardMakeReport(model_id=mid, card_path=path)
        existing: dict = {}
        if path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Bestehende Card nicht lesbar (%s) — neu aufbauen.", exc)

        user_prompt = _build_make_user_prompt(
            self.template, existing, self.editor_prompt,
        )
        try:
            response = self.session.query(
                system=_MAKE_SYSTEM_INSTRUCTION,
                user=user_prompt,
                temperature=self.llm_spec.temperature,
            )
        except (openai.APIError, ValueError, json.JSONDecodeError) as exc:  # noqa: BLE001
            report.error = str(exc)
            self.summary.errors += 1
            self.summary.make_reports.append(report)
            return report

        report.raw_response = response
        new_card, parse_err = _parse_make_response(response)
        if parse_err or new_card is None:
            report.parse_error = parse_err
            self.summary.errors += 1
            self.summary.make_reports.append(report)
            return report

        new_card = _preserve_operator_fields(existing or {}, new_card)
        cleaned, warnings = _validate_against_template(new_card, self.template)
        report.warnings = warnings
        report.new_card = cleaned
        self.summary.processed += 1

        report.would_write = True
        if self.args.dry_run:
            logger.info("    [DRY-RUN] Würde %s neu schreiben (%d Felder).", path.name, len(cleaned))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            rebuild_card_index("model")
            report.wrote = True
            logger.info("    ✅ %s geschrieben.", path.name)
        for w in warnings:
            logger.info("    · %s", w)

        self.summary.make_reports.append(report)
        return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "LLM-gestütztes Model-Card-Management. "
            "Prüft (check) oder ergänzt (make) Cards via LLM."
        ),
    )
    parser.add_argument(
        "--mode", required=True, choices=["check", "make", "research"],
        help="check: Findings-Report (optional mit --fix). make: Card regenerieren. research: LLM-Recherche mit profile_verified-Lock.",
    )
    parser.add_argument("--card", type=str, help="Nur diese eine Card verarbeiten.")
    parser.add_argument(
        "--force", action="store_true",
        help="Auch verifizierte Cards einbeziehen.",
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="(check) Vorgeschlagene Korrekturen direkt anwenden.",
    )
    parser.add_argument(
        "--write", action="store_true",
        help="(make) Card tatsächlich schreiben — sonst Dry-Run.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Explizit kein Schreibvorgang (Standard für make).",
    )
    parser.add_argument("--model", type=str, help="LLM-Modell (überschreibt Config).")
    parser.add_argument(
        "--base-url", type=str,
        help="OpenAI-kompatibler Endpoint (z.B. http://localhost:1234/v1).",
    )
    parser.add_argument(
        "--api-key-env", type=str, default=None,
        help="Name der Env-Variable mit dem API-Key (Default: aus Config oder OPENAI_API_KEY).",
    )
    parser.add_argument(
        "--provider", type=str, help="Provider-Label (informational).",
    )
    parser.add_argument("--max-retries", type=int, default=MAX_RETRIES)
    parser.add_argument("--timeout-s", type=int, default=PER_CALL_TIMEOUT_S)
    parser.add_argument("--pause", type=float, default=1.0,
                        help="Pause in Sekunden zwischen jeder Card (Default: 1.0).")
    parser.add_argument("--max-cards", type=int, default=0,
                        help="Max. Cards pro Run (0=alle). Bei llama.cpp-Speicherproblemen nutzen.")
    parser.add_argument(
        "--tooluse", action="store_true",
        help="Tool-Use-Modus: LLM recherchiert via MCP (web_search/fetch).",
    )
    parser.add_argument(
        "--mcp-url", type=str, default="http://localhost:8765",
        help="MCP-Server URL (Default: http://localhost:8765).",
    )
    args = parser.parse_args()

    _setup_logging()

    if args.fix and args.mode != "check":
        raise SystemExit("❌ --fix ist nur mit --mode check erlaubt.")
    if args.card and args.mode == "check":
        if not _find_card(args.card).exists():
            raise SystemExit(f"❌ Card nicht gefunden: {args.card}")
    if args.card and args.mode == "research":
        if args.card.lower() != "all" and not _find_card(args.card).exists():
            raise SystemExit(f"❌ Card nicht gefunden: {args.card}")
    if args.write and args.dry_run:
        raise SystemExit("❌ --write und --dry-run sind nicht kombinierbar.")
    if getattr(args, "tooluse", False) and args.mode != "research":
        raise SystemExit("❌ --tooluse ist nur mit --mode research erlaubt.")

    if args.mode == "make" and not args.write:
        args.dry_run = True

    config = _load_benchmark_config()
    llm_spec = _resolve_llm_spec(args, config)

    if not llm_spec.api_key:
        raise SystemExit(
            f"❌ Kein API-Key gefunden. Setze die Env-Variable "
            f"{args.api_key_env!r} (oder via --api-key-env überschreiben)."
        )

    template = load_card_template("model")
    editor_prompt = _load_editor_prompt()

    session = LLMSession(
        model=llm_spec.model,
        base_url=llm_spec.base_url,
        api_key=llm_spec.api_key,
        max_retries=args.max_retries,
        timeout_s=args.timeout_s,
    )

    if args.mode == "research":
        researcher = Researcher(args, session, template, editor_prompt, llm_spec)
        summary = researcher.run()
    else:
        manager = CardManager(args, session, template, editor_prompt, llm_spec)
        summary = manager.run()

    print()
    if args.mode == "check" and not args.fix:
        today = date.today().isoformat()
        print(_render_markdown_report(summary.check_reports, today))
    elif args.mode == "check" and args.fix:
        today = date.today().isoformat()
        print(_render_markdown_report(summary.check_reports, today, mode_label="check (fix)"))
    elif args.mode == "research":
        today = date.today().isoformat()
        print(_render_research_markdown_report(summary.research_reports, today))

    print(
        f"✅ Fertig: {summary.processed} verarbeitet, "
        f"{summary.errors} Fehler."
    )
    return 0 if summary.errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
