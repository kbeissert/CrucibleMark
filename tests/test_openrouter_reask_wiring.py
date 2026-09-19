"""Regression: OpenRouter muss an die Eskalationsleiter angebunden sein.

Befund (Session 110, Code-Quality-Lauf z-ai/glm-5.3 via OpenRouter):
001 WCAG brannte 20000 Tokens bei ``finish_reason=length`` mit 0 sichtbarem
Output → Judge 0.0 → 0 %, weil ``openrouter.py`` als einziger Thinking-Provider
nicht an den Shared-Re-Ask (``BaseProviderClient._maybe_reask_reasoning_truncation``)
angebunden war — die Leiter war nur in vllm_base/llamacpp_base/openai verdrahtet.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.providers.openrouter import OpenRouterClient  # noqa: E402


def _connector_with_truncation(monkeypatch: pytest.MonkeyPatch, card_cap: int | None) -> OpenRouterClient:
    """OpenRouter-Stub: Truncation-Metadata, interne Pfade gestubbt."""
    from types import SimpleNamespace

    conn = object.__new__(OpenRouterClient)
    # Lazy-Property `client` muss ohne API-Key auflösbar sein — der create-Aufruf
    # wird als Argument in query() evaluiert, bevor die Stubs greifen.
    conn._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **k: "resp")),
    )
    conn.last_response_metadata = {
        "finish_reason": "length",
        "token_limit_used": 20000,
        "think_content": "Let me audit this thoroughly...",
        "reasoning_tokens": 20000,
    }
    monkeypatch.setattr(
        conn, "_build_openrouter_params", lambda *a, **k: ({}, "max_tokens", 20000),
    )
    monkeypatch.setattr(
        conn, "_execute_with_token_fallback", lambda **k: ("resp", 20000, False),
    )
    monkeypatch.setattr(
        conn, "_process_openrouter_blocking", lambda *a, **k: "",
    )
    monkeypatch.setattr(
        conn, "_get_provider_cfg", lambda: {},
    )
    monkeypatch.setattr(
        "utils.model_thinking._read_max_output_tokens_from_card", lambda m: card_cap,
    )
    return conn


def test_openrouter_query_wires_reask_ladder(monkeypatch):
    """Truncation (leer + length + Reasoning-Signal) → query() betritt den
    Shared-Re-Ask mit Card-Cap als Eskalations-Limit."""
    conn = _connector_with_truncation(monkeypatch, card_cap=32768)
    captured: dict = {}

    def _fake_reask(**kwargs):
        captured.update(kwargs)
        return "ESKALIERTE ANTWORT"

    monkeypatch.setattr(conn, "_maybe_reask_reasoning_truncation", _fake_reask)

    result = conn.query(model="z-ai/glm-5.3", prompt="P", temperature=1.0, stream_handler=None)

    assert result == "ESKALIERTE ANTWORT"
    assert captured["budget_cap"] == 32768
    assert captured["content"] == ""
    assert captured["model"] == "z-ai/glm-5.3"
    assert captured["query"] == conn.query


def test_openrouter_query_passes_content_without_reask(monkeypatch):
    """Sichtbarer Output + finish_reason=stop → query() liefert direkt; die
    ECHTE Leiter wird durchlaufen, eskaliert aber nicht (zweiter Request fehlt)."""
    conn = _connector_with_truncation(monkeypatch, card_cap=32768)
    conn.last_response_metadata = {"finish_reason": "stop", "token_limit_used": 12000}
    monkeypatch.setattr(
        conn, "_process_openrouter_blocking", lambda *a, **k: "VOLLSTÄNDIGE ANTWORT",
    )
    calls: list[int] = []

    def _counting_execute(**kwargs):
        calls.append(1)
        return ("resp", 20000, False)

    monkeypatch.setattr(conn, "_execute_with_token_fallback", _counting_execute)

    result = conn.query(model="z-ai/glm-5.3", prompt="P", temperature=1.0, stream_handler=None)

    assert result == "VOLLSTÄNDIGE ANTWORT"
    assert len(calls) == 1  # kein eskalierter Zweit-Request


def test_openrouter_reask_kwargs_reach_request_params(monkeypatch):
    """End-to-End über die echte query()-Kette: Der Ladder-Loop setzt
    kwargs['max_tokens']=24000 und _build_openrouter_params bekommt sie —
    die base.py-Kaskade (resolve_token_budget → Provider-Cap) gewinnt sie."""
    conn = _connector_with_truncation(monkeypatch, card_cap=None)
    seen_kwargs: list[dict] = []
    call_state = {"n": 0}

    real_params = conn._build_openrouter_params

    def _recording_params(model, prompt, temperature, kwargs, stream_handler):
        seen_kwargs.append(dict(kwargs))
        return real_params(model, prompt, temperature, kwargs, stream_handler)

    monkeypatch.setattr(conn, "_build_openrouter_params", _recording_params)

    responses = iter(["", "SUCCESS AT 24K"])

    def _stateful_process(*a, **k):
        call_state["n"] += 1
        return next(responses)

    monkeypatch.setattr(conn, "_process_openrouter_blocking", _stateful_process)

    result = conn.query(model="z-ai/glm-5.3", prompt="P", temperature=1.0, stream_handler=None)

    assert result == "SUCCESS AT 24K"
    assert call_state["n"] == 2
    assert seen_kwargs[1]["max_tokens"] == 24000
