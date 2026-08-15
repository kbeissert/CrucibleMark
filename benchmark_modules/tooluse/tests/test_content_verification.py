"""Unit tests for ToolAdapterAudit.run_content_verification() — all 4 states.

Covers: State A (no cap), B1 (cap=50), B2 (cap=35), C (cap=20), failure-test exempt.
Tests are deterministic — no model runs, no network, no file I/O.
"""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from benchmark_modules.tooluse.core.tool_adapter_audit import ToolAdapterAudit

# ---------------------------------------------------------------------------
# Constants (explicit, independent of scoring.yaml file I/O)
# ---------------------------------------------------------------------------

_CAPS = {
    "cap_B1_transparent": 50,
    "cap_B2_parametric": 35,
    "cap_C_no_tool": 20,
}

_ASSET_NORMAL = {"is_failure_test": False}
_ASSET_FAILURE = {"is_failure_test": True}

# Realistic content excerpt (mirrors the Quake-series mock fixture in mock_provider.py)
_QUAKE_EXCERPT = (
    "Quake (series) — Wikipedia\n\n"
    "The Quake series is a franchise of first-person shooter video games developed by id Software.\n"
    "Quake (1996)\n"
    "Quake is a first-person shooter released in 1996 by id Software. "
    "It marked a significant shift to full 3D environments.\n"
    "Quake II (1997)\n"
    "Quake II abandoned the dark fantasy themes and introduced a science fiction setting."
)

_EMPTY_EXCERPT = ""
_HTML_HEAD_ONLY = "<html><head><title>403 Forbidden</title><meta charset='utf-8'></head></html>"


# ---------------------------------------------------------------------------
# State A — content usable, phrase overlap confirmed
# ---------------------------------------------------------------------------

def test_state_a_overlap_confirmed():
    """State A: content usable AND 3-word verbatim match in model output → no cap."""
    transcript = {"content_excerpt": _QUAKE_EXCERPT}
    # "quake series is" — exact 3-word window from excerpt, verbatim in output
    output = (
        "Basierend auf der Seite: Die Quake series is a franchise of first-person shooters "
        "von id Software, erschienen ab 1996."
    )
    p2_final, cv = ToolAdapterAudit.run_content_verification(
        transcript, output, _ASSET_NORMAL, p1_score=100.0, p2_raw=80.0, caps=_CAPS
    )
    assert cv["state"] == "A"
    assert cv["p2_cap_applied"] is None
    assert cv["parametric_response_detected"] is False
    assert p2_final == 80.0  # no cap applied


# ---------------------------------------------------------------------------
# State B1 — content NOT usable, model transparently acknowledges it
# ---------------------------------------------------------------------------

def test_state_b1_german_transparency_signal():
    """State B1: empty content + German transparency signal → cap=50."""
    transcript = {"content_excerpt": _EMPTY_EXCERPT}
    output = "Leider konnte ich die Seite nicht laden und habe keine Informationen verfügbar."
    p2_final, cv = ToolAdapterAudit.run_content_verification(
        transcript, output, _ASSET_NORMAL, p1_score=100.0, p2_raw=80.0, caps=_CAPS
    )
    assert cv["state"] == "B1"
    assert cv["transparency_signal"] is True
    assert cv["content_usable"] is False
    assert cv["p2_cap_applied"] == 50
    assert p2_final == 50.0


def test_state_b1_english_transparency_signal():
    """State B1: HTML-head-only content + English transparency signal → cap=50."""
    transcript = {"content_excerpt": _HTML_HEAD_ONLY}
    output = "Unfortunately, I could not access the page content and have no information."
    p2_final, cv = ToolAdapterAudit.run_content_verification(
        transcript, output, _ASSET_NORMAL, p1_score=100.0, p2_raw=90.0, caps=_CAPS
    )
    assert cv["state"] == "B1"
    assert cv["transparency_signal"] is True
    assert cv["p2_cap_applied"] == 50
    assert p2_final == 50.0


# ---------------------------------------------------------------------------
# State B2 — content usable but NO phrase overlap (parametric response)
# ---------------------------------------------------------------------------

def test_state_b2_no_overlap_despite_usable_content():
    """State B2: content usable but model output has NO key tokens from excerpt → cap=35.

    Simuliert ein Modell das den Tool-Call ignoriert und stattdessen eine
    allgemeine thematisch-ähnliche Antwort gibt — ohne Namen, Jahre oder
    spezifische Begriffe aus dem Inhalt.
    """
    transcript = {"content_excerpt": _QUAKE_EXCERPT}
    # Generic gaming answer with no names/years/tokens from the excerpt
    output = "Dieser Shooter gehört zu den bekanntesten seiner Zeit und hat viele Nachfolger hervorgebracht."
    p2_final, cv = ToolAdapterAudit.run_content_verification(
        transcript, output, _ASSET_NORMAL, p1_score=100.0, p2_raw=80.0, caps=_CAPS
    )
    assert cv["state"] == "B2"
    assert cv["parametric_response_detected"] is True
    assert cv["transparency_signal"] is False
    assert cv["p2_cap_applied"] is None  # B2 cap removed — judge evaluates grounding
    assert p2_final == 80.0  # p2_raw returned unchanged


# ---------------------------------------------------------------------------
# State C — no tool call (P1 = 0)
# ---------------------------------------------------------------------------

def test_state_c_no_tool_call():
    """State C: P1=0 → cap=20 regardless of content or output."""
    transcript = {"content_excerpt": _QUAKE_EXCERPT}
    output = "Quake ist eine Spieleserie von id Software."
    p2_final, cv = ToolAdapterAudit.run_content_verification(
        transcript, output, _ASSET_NORMAL, p1_score=0.0, p2_raw=80.0, caps=_CAPS
    )
    assert cv["state"] == "C"
    assert cv["p2_cap_applied"] == 20
    assert p2_final == 20.0


def test_state_c_raw_below_cap_not_boosted():
    """State C: if p2_raw < cap_C, p2_final must not be raised."""
    transcript = {"content_excerpt": _EMPTY_EXCERPT}
    output = "Keine Antwort möglich."
    p2_final, cv = ToolAdapterAudit.run_content_verification(
        transcript, output, _ASSET_NORMAL, p1_score=0.0, p2_raw=10.0, caps=_CAPS
    )
    assert cv["state"] == "C"
    assert p2_final == 10.0  # min(10.0, 20) = 10.0


# ---------------------------------------------------------------------------
# Failure-test exempt — is_failure_test=True always yields State A
# ---------------------------------------------------------------------------

def test_failure_test_exempt_always_state_a():
    """is_failure_test=True → State A, no cap, p2_raw unchanged even with empty content."""
    transcript = {"content_excerpt": _EMPTY_EXCERPT}
    output = "Die Seite ist nicht erreichbar — das ist das erwartete Ergebnis."
    p2_final, cv = ToolAdapterAudit.run_content_verification(
        transcript, output, _ASSET_FAILURE, p1_score=100.0, p2_raw=75.0, caps=_CAPS
    )
    assert cv["state"] == "A"
    assert cv["p2_cap_applied"] is None
    assert p2_final == 75.0
