"""Tool Adapter Audit — Diagnose Tool-Name und Call-Format Mismatches.

Problem bei tooluse002 & Claude Sonnet 4.6 (vor MCP-Standard-Alignment):
- Model returned: {"tool_call": {"name": "fetch", ...}}
- Expected: {"tool_call": {"name": "fetch", ...}}  ← jetzt korrekt (MCP Standard)
- MCP routes to: /tools/fetch

Diese Audit prüft:
1. Tool-Name Validierung (MCP-Standard: fetch, web_search)
2. Tool-Call-Format Validierung
3. MCP Endpoint Routing
4. Response Structure Mapping
5. Content Verification Gate (Drei-Zustands-Framework)
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml

from .constants import (
    CV_CAP_B1_KEY,
    CV_CAP_B2_KEY,
    CV_CAP_C_KEY,
    CV_CAP_DEFAULTS,
)

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[3]

# Authorized tool names — aligned with Anthropic MCP standard.
# fetch: matches @modelcontextprotocol/server-fetch reference implementation.
AUTHORIZED_TOOLS = {
    "web_search": ["web_search"],
    "fetch": ["fetch"],
}

# Canonical tool names (what we expect)
CANONICAL_TOOLS = {
    "web_search": "web_search",
    "fetch": "fetch",
}

# -----------------------------------------------------------------------
# Content Verification — private helpers
# -----------------------------------------------------------------------

# HTML structural tags that signal a head-only / non-body response
_HTML_HEAD_RE = re.compile(
    r"<(?:html|head|meta|link|title|script|style|!doctype)[^>]*>",
    re.IGNORECASE,
)

# Minimum visible-text length to consider content usable
_VISIBLE_TEXT_MIN = 80

# Transparency signals: model explicitly acknowledges missing/unusable content
_TRANSPARENCY_SIGNALS = (
    "kein inhalt",
    "keine informationen",
    "konnte nicht laden",
    "nicht zugänglich",
    "keine nutzbare",
    "nicht verfügbar",
    "fehler beim laden",
    "konnte die seite nicht",
    "inhalt nicht",
    "no content",
    "could not load",
    "unable to extract",
    "no useful content",
    "page not available",
    "content not available",
    "no information",
    "could not access",
    "unfortunately",          # English fallback signal
    "leider",                 # German fallback signal
    "keine relevanten",
    "nicht abrufen",
    "nicht geladen",
    # Model explicitly falls back to parametric knowledge (specific compound phrases only)
    "meinem trainingswissen",             # "based on my training knowledge"
    "meinem wissensstand",                # "as of my knowledge cutoff"
    "nur metadaten",                      # "only metadata" — tool returned no usable body content
    "mit meinem trainingswissen",         # "combining with my training knowledge"
    "mit meinem wissensstand",            # "combining with my knowledge base"
    "my training knowledge",              # English equivalent
    "my training data",                   # English equivalent
    "as of my knowledge",                 # English equivalent
    "based on my training",               # English equivalent
    "supplement with my",                 # English: "supplement with my [training] knowledge"
)

# Minimum consecutive words that must appear verbatim (case-insensitive)
# in model output to count as a content-overlap signal
_OVERLAP_WINDOW = 4


def _load_scoring_caps() -> dict[str, int]:
    """Lädt Content-Verification-Cap-Werte aus config/scoring.yaml.

    Fällt auf CV_CAP_DEFAULTS zurück wenn Datei nicht vorhanden oder
    fehlerhaft ist.
    """
    cfg_path = _ROOT / "config" / "scoring.yaml"
    try:
        raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        caps = raw.get("tool_use", {}).get("content_verification", {})
        if caps:
            # Merge mit Defaults damit fehlende Keys abgefangen sind
            merged = dict(CV_CAP_DEFAULTS)
            merged.update({k: int(v) for k, v in caps.items() if k in CV_CAP_DEFAULTS})
            return merged
    except FileNotFoundError:
        pass
    except Exception:  # noqa: BLE001 — yaml/filesystem boundary
        logger.warning("Could not load scoring caps from config", exc_info=True)
    return dict(CV_CAP_DEFAULTS)


def _check_content_usable(content_excerpt: str | None) -> bool:
    """Heuristik: True wenn content_excerpt sichtbaren Body-Text enthält.

    Nicht binär — ein Wert von True bedeutet "wahrscheinlich nützlich",
    False bedeutet "wahrscheinlich nur Boilerplate / leer / nur HTML-Head".
    Die Schwelle ist bewusst niedrig angesetzt (robuste Heuristik):
    Lieber einen False Negative (State B2 statt A) als einen False Positive
    (State A bei nutzlosem Content).
    """
    if not content_excerpt:
        return False
    stripped = content_excerpt.strip()
    if len(stripped) < 50:  # noqa: PLR2004 — min content threshold
        return False
    # Strip HTML tags to get visible text
    visible = _HTML_HEAD_RE.sub("", stripped)
    visible = re.sub(r"<[^>]+>", "", visible).strip()
    return len(visible) >= _VISIBLE_TEXT_MIN


def _has_transparency_signal(model_output: str) -> bool:
    """True wenn Modell explizit auf fehlenden/unbrauchbaren Content hinweist."""
    lower = model_output.lower()
    return any(sig in lower for sig in _TRANSPARENCY_SIGNALS)


def _has_content_overlap(model_output: str, content_excerpt: str) -> bool:
    """True wenn model_output spezifische Phrasen aus content_excerpt enthält.

    Gleitet mit Fenstergröße _OVERLAP_WINDOW über content_excerpt-Wörter.
    Mindestens ein Treffer genügt. Heuristik: längere Phrasen reduzieren
    False-Positive-Rate (Zufallsüberlappung durch Allgemeinwörter).
    """
    if not content_excerpt or not model_output:
        return False
    words = content_excerpt.lower().split()
    output_lower = model_output.lower()
    for i in range(len(words) - _OVERLAP_WINDOW + 1):
        phrase = " ".join(words[i : i + _OVERLAP_WINDOW])
        # Skip phrases that are all short common words (avoid false positives)
        if all(len(w) <= 3 for w in words[i : i + _OVERLAP_WINDOW]):  # noqa: PLR2004
            continue
        if phrase in output_lower:
            return True
    return False


# -----------------------------------------------------------------------
# Main audit class
# -----------------------------------------------------------------------


class ToolAdapterAudit:
    """Audit Tool-Adapter layer for name/format mismatches."""

    @staticmethod
    def normalize_tool_name(raw_name: str) -> tuple[str, bool]:
        """Normalize raw tool name from model to canonical form.

        Returns: (canonical_name, is_anomaly)
        - is_anomaly = True if raw_name needed normalization
        """
        raw_lower = str(raw_name).lower().strip()

        for canonical, variants in AUTHORIZED_TOOLS.items():
            if raw_lower in variants:
                is_anomaly = raw_lower != canonical
                return canonical, is_anomaly

        # Unknown tool
        return raw_lower, True

    @staticmethod
    def validate_tool_call(tool_call: dict[str, Any]) -> dict[str, Any]:
        """Validate and normalize tool call structure.

        Returns audit dict with findings.
        """
        audit = {
            "raw_name": tool_call.get("name", "unknown"),
            "canonical_name": "unknown",
            "is_anomaly": False,
            "format_valid": False,
            "has_parameters": False,
            "error": None,
        }

        # Validate structure
        if not isinstance(tool_call, dict):
            audit["error"] = "tool_call is not a dict"
            return audit

        if "name" not in tool_call:
            audit["error"] = "tool_call missing 'name' field"
            return audit

        # Normalize name
        canonical, is_anomaly = ToolAdapterAudit.normalize_tool_name(
            tool_call.get("name"),
        )
        audit["canonical_name"] = canonical
        audit["is_anomaly"] = is_anomaly

        # Validate parameters
        params = tool_call.get("parameters", {})
        audit["has_parameters"] = isinstance(params, dict) and len(params) > 0

        # Format valid if canonical name found and has parameters
        audit["format_valid"] = (
            canonical in CANONICAL_TOOLS.values()
            and audit["has_parameters"]
        )

        if is_anomaly:
            audit["warning"] = (
                f"Tool name normalized: '{tool_call.get('name')}' → '{canonical}'"
            )

        return audit

    @staticmethod
    def audit_mcp_routing(
        tool_name: str,
        tool_transcript: dict[str, Any],
    ) -> dict[str, Any]:
        """Audit MCP routing layer.

        Checks if tool_transcript indicates routing anomalies.
        """
        audit = {
            "tool_name": tool_name,
            "mcp_endpoint": f"/tools/{tool_name}",
            "transcript_status": tool_transcript.get("status"),
            "has_error": tool_transcript.get("status") in ("error", "blocked"),
            "status_code": tool_transcript.get("status_code"),
            "anomalies": [],
        }

        # Check for routing anomalies
        if "source_url" in tool_transcript:
            source = tool_transcript.get("source_url")
            if source is None or source == "n/a":
                audit["anomalies"].append(
                    f"source_url missing (expected for successful {tool_name})",
                )

        if tool_transcript.get("status") == "error" and not tool_transcript.get(
            "error",
        ):
            audit["anomalies"].append(
                "error status but no error message in transcript",
            )

        # Check for empty results
        results = tool_transcript.get("results")
        if isinstance(results, list) and len(results) == 0:
            audit["anomalies"].append("results array is empty")

        return audit

    @staticmethod
    def diagnose_p1_zero_case(
        tool_call_dict: dict[str, Any] | None,
        tool_transcript: dict[str, Any],
        asset: dict[str, Any],
        p1_score: float,
    ) -> dict[str, Any]:
        """Diagnose why P1 = 0.0 occurred.

        Returns diagnostic findings.
        """
        diagnosis = {
            "p1_score": p1_score,
            "is_hard_fail": p1_score == 0.0,
            "likely_cause": "unknown",
            "audit_details": {},
        }

        if not diagnosis["is_hard_fail"]:
            return diagnosis

        # Audit tool call
        if tool_call_dict:
            tool_audit = ToolAdapterAudit.validate_tool_call(tool_call_dict)
            diagnosis["audit_details"]["tool_call"] = tool_audit

            if tool_audit["is_anomaly"]:
                diagnosis["likely_cause"] = "tool_name_normalization"

        # Audit MCP routing
        if "tool_type_called" in tool_transcript:
            tool_name = tool_transcript["tool_type_called"]
            routing_audit = ToolAdapterAudit.audit_mcp_routing(
                tool_name, tool_transcript,
            )
            diagnosis["audit_details"]["mcp_routing"] = routing_audit

            if routing_audit["anomalies"]:
                if diagnosis["likely_cause"] == "unknown":
                    diagnosis["likely_cause"] = "mcp_routing_issue"

        # Check for sandbox violation
        if tool_transcript.get("status") == "blocked":
            diagnosis["likely_cause"] = "sandbox_violation"

        # Check expected tool type
        expected_tool = asset.get("evaluation", {}).get("phase1", {}).get("expected_tool")
        actual_tool = tool_transcript.get("tool_type_called")

        if expected_tool and actual_tool and expected_tool != actual_tool:
            diagnosis["audit_details"]["tool_mismatch"] = {
                "expected": expected_tool,
                "actual": actual_tool,
            }
            if diagnosis["likely_cause"] == "unknown":
                diagnosis["likely_cause"] = "tool_type_mismatch"

        return diagnosis

    @staticmethod
    def run_content_verification(
        tool_transcript: dict[str, Any],
        model_output: str,
        asset: dict[str, Any],
        p1_score: float,
        p2_raw: float,
        caps: dict[str, int] | None = None,
    ) -> tuple[float, dict[str, Any]]:
        """Content-Verification-Gate: bestimmt State und deckelt P2-Score.

        Drei-Zustands-Framework:
          A  — Content nutzbar + Overlap mit Modellantwort → kein Cap
          B1 — Content nicht nutzbar, Modell transparent → cap_B1
          B2 — Content nicht nutzbar ODER kein Overlap, kein Hinweis → cap_B2
          B3 — Nicht programmatisch detektierbar → Default B2
          C  — Kein Tool-Call (p1=0) → cap_C

        Failure-Tests (tooluse003) sind exempt: State A, p2_raw unverändert.

        Returns:
            (p2_final, content_verification_block)
        """
        # Failure tests: abweichende Scoring-Logik, exempt von CV
        if asset.get("is_failure_test", False):
            return p2_raw, {
                "state": "A",
                "content_usable": None,
                "parametric_response_detected": False,
                "transparency_signal": False,
                "p2_cap_applied": None,
                "state_rationale": "Failure test exempt from content verification.",
            }

        if caps is None:
            caps = _load_scoring_caps()

        content_excerpt: str = str(tool_transcript.get("content_excerpt") or "")
        if not content_excerpt:
            # web_search stores results in results[], not content_excerpt
            results = tool_transcript.get("results") or []
            if results and isinstance(results[0], dict):
                content_excerpt = str(
                    results[0].get("excerpt") or results[0].get("content", "")
                )

        # State C: kein Tool-Call
        if p1_score == 0.0:
            cap = caps[CV_CAP_C_KEY]
            p2_final = min(p2_raw, float(cap))
            return p2_final, {
                "state": "C",
                "content_usable": False,
                "parametric_response_detected": True,
                "transparency_signal": False,
                "p2_cap_applied": cap,
                "state_rationale": "P1=0: no tool call — response is fully parametric.",
            }

        content_usable = _check_content_usable(content_excerpt)
        transparency = _has_transparency_signal(model_output)

        if not content_usable:
            if transparency:
                state = "B1"
                cap_key = CV_CAP_B1_KEY
                rationale = (
                    "Content not usable; model transparently acknowledged "
                    "missing or unusable tool content."
                )
            else:
                state = "B2"
                cap_key = CV_CAP_B2_KEY
                rationale = (
                    "Content not usable; model answered without signalling "
                    "content absence — likely parametric response."
                )
        else:
            # Content usable: prüfe Overlap
            if _has_content_overlap(model_output, content_excerpt):
                state = "A"
                cap_key = None
                rationale = (
                    "Content usable and model output contains specific phrases "
                    "from tool response — sourced response confirmed."
                )
            else:
                state = "B2"
                cap_key = CV_CAP_B2_KEY
                rationale = (
                    "Content usable but no phrase overlap detected — "
                    "model likely answered from parametric knowledge."
                )

        if cap_key is not None:
            cap = caps[cap_key]
            p2_final = min(p2_raw, float(cap))
        else:
            cap = None
            p2_final = p2_raw

        return p2_final, {
            "state": state,
            "content_usable": content_usable,
            "parametric_response_detected": state in ("B2", "B3"),
            "transparency_signal": transparency,
            "p2_cap_applied": cap,
            "state_rationale": rationale,
        }

    @staticmethod
    def log_audit(audit: dict[str, Any], context: str = "") -> None:
        """Log audit findings."""
        msg = f"[TOOL_ADAPTER_AUDIT] {context} — {json.dumps(audit, ensure_ascii=False)}"
        if audit.get("anomalies") or audit.get("is_anomaly"):
            logger.warning(msg)
        else:
            logger.debug(msg)
