"""Anthropic-Streaming-Usage: message_delta-Merge-Regression (2026-09-24).

Befund (PC-Lauf claude-opus-5-5): Ladder-output_tokens 2–9 trotz langer
Refusal-Essays, reasoning_tokens 0, Output-Kosten unter-reportet. Ursache:
``_apply_anthropic_message_delta`` suchte usage in ``event.delta`` — dort
existiert das Feld nicht (SDK: delta = {stop_reason, stop_sequence}), die
kumulative output_tokens liegt in ``event.usage``. stream_usage blieb auf
dem message_start-Stand (Initial-output_tokens 2–9).

Der Fix liest ``event.usage`` und merged input_tokens aus message_start
(MessageDeltaUsage.input_tokens ist im Streaming None).
"""
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from anthropic.types import MessageDeltaEvent, MessageDeltaUsage  # noqa: E402

from utils.llm_parser import LLMParser  # noqa: E402
from utils.providers.anthropic import AnthropicClient  # noqa: E402
from utils.providers.base import BaseProviderClient  # noqa: E402


def _client() -> AnthropicClient:
    return AnthropicClient({})


def _state() -> dict:
    return {
        "full_content": "", "think": None, "stream_usage": None,
        "model_name": None, "response_id": None, "stop_reason": None,
    }


def _start_event(input_tokens=950, output_tokens=3, cache_read=0):
    usage = SimpleNamespace(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_input_tokens=cache_read or None,
    )
    return SimpleNamespace(
        type="message_start",
        message=SimpleNamespace(model="claude-opus-5-5", id="msg_1", usage=usage),
    )


def _delta_event(output_tokens=435, stop_reason="end_turn"):
    return SimpleNamespace(
        type="message_delta",
        delta=SimpleNamespace(stop_reason=stop_reason, stop_sequence=None),
        usage=SimpleNamespace(output_tokens=output_tokens),
    )


def _run_events(events) -> dict:
    state = _state()
    client = _client()
    for event in events:
        client._process_anthropic_stream_event(  # pylint: disable=protected-access
            event, state, stream_handler=None
        )
    return state


# ---------------------------------------------------------------------------
# Bug-Vorbedingung: SDK-Struktur (Guard gegen SDK-Regressionen)
# ---------------------------------------------------------------------------

def test_sdk_message_delta_usage_is_sibling_of_delta():
    """Beweist die Bug-Vorbedingung: delta hat KEIN usage-Attribut, event schon."""
    event = MessageDeltaEvent(
        type="message_delta",
        delta={"stop_reason": "end_turn", "stop_sequence": None},
        usage=MessageDeltaUsage(output_tokens=435),
    )
    assert not hasattr(event.delta, "usage")
    assert hasattr(event, "usage")
    assert event.usage.output_tokens == 435


def test_sdk_message_delta_usage_input_tokens_is_none():
    """MessageDeltaUsage.input_tokens existiert, ist aber None (Merge nötig)."""
    usage = MessageDeltaUsage(output_tokens=435)
    assert usage.input_tokens is None


# ---------------------------------------------------------------------------
# Fix: message_delta aktualisiert stream_usage
# ---------------------------------------------------------------------------

def test_stream_usage_merged_after_message_delta():
    """start(950/3) + delta(435) → {input: 950, output: 435, output_tokens_details: None}."""
    state = _run_events([_start_event(), _delta_event(output_tokens=435)])
    assert state["stream_usage"] == {
        "input_tokens": 950, "output_tokens": 435, "output_tokens_details": None,
    }
    assert state["stop_reason"] == "end_turn"


def test_extract_usage_tokens_on_merged_dict():
    state = _run_events([_start_event(), _delta_event(output_tokens=435)])
    assert LLMParser.extract_usage_tokens(state["stream_usage"]) == (950, 435)


def test_cache_read_merged_into_input():
    """Cache-Read-Tokens werden wie im Objekt-Zweig zu input addiert."""
    state = _run_events([
        _start_event(input_tokens=200, cache_read=750),
        _delta_event(output_tokens=435),
    ])
    assert state["stream_usage"] == {
        "input_tokens": 950, "output_tokens": 435, "output_tokens_details": None,
    }


def test_delta_without_usage_keeps_start_usage():
    """message_delta ohne usage-Feld: message_start-Usage bleibt unverändert."""
    event = SimpleNamespace(
        type="message_delta",
        delta=SimpleNamespace(stop_reason="end_turn", stop_sequence=None),
    )
    state = _run_events([_start_event(), event])
    assert state["stream_usage"] is not None
    assert state["stream_usage"].input_tokens == 950


def test_reasoning_extraction_none_for_merged_dict():
    """_extract_reasoning_tokens crasht nicht auf dem Merge-Dict (None)."""
    state = _run_events([_start_event(), _delta_event()])
    assert BaseProviderClient._extract_reasoning_tokens(state["stream_usage"]) is None


def test_reasoning_extraction_from_dict_with_output_tokens_details():
    """_extract_reasoning_tokens findet reasoning_tokens im Merge-Dict (CRIT-01 Fix)."""
    details = SimpleNamespace(reasoning_tokens=2048)
    stream_usage = {
        "input_tokens": 950,
        "output_tokens": 435,
        "output_tokens_details": details,
    }
    assert BaseProviderClient._extract_reasoning_tokens(stream_usage) == 2048


def test_reasoning_extraction_from_dict_without_details():
    """Merge-Dict ohne output_tokens_details → None (kein Crash)."""
    stream_usage = {"input_tokens": 950, "output_tokens": 435}
    assert BaseProviderClient._extract_reasoning_tokens(stream_usage) is None


def test_reasoning_extraction_from_dict_top_level():
    """Merge-Dict mit reasoning_tokens auf Top-Level (Pfad 3)."""
    stream_usage = {
        "input_tokens": 950, "output_tokens": 435, "reasoning_tokens": 1024,
    }
    assert BaseProviderClient._extract_reasoning_tokens(stream_usage) == 1024


def test_extract_usage_tokens_none_input_safe():
    """MessageDeltaUsage (input=None) → (0, output) statt None-Crash im llm_client."""
    usage = MessageDeltaUsage(output_tokens=435)
    assert LLMParser.extract_usage_tokens(usage) == (0, 435)
