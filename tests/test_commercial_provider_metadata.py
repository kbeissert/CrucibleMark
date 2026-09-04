"""Probe-relevante Response-Metadaten der Commercial-Connectoren.

Incident 2026-09-04 (PC-Token-Probe, erste kommerzielle Modelle): Der
OpenRouter-Streaming-Handler setzte ``finish_reason`` nie — die
Truncation-Erkennung der PC-Token-Probe (``truncated`` =
finish_reason in length/max_tokens) und die token_limit_cutoff-Flags
der PC-Runs waren für alle OpenRouter-Modelle blind (nachgewiesen in
den PC-Runs 2026-09-03: finish_reason=null auf 100 % der Responses).
Der Google-Blocking-Pfad maskierte zusätzlich echtes MAX_TOKENS als
"SAFETY", wenn der Candidate keine Text-Parts hatte (Thinking-only-
Truncation). Diese Tests sichern beide Fixes regressionsfrei ab.
"""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.providers.google import GoogleClient  # noqa: E402
from utils.providers.openrouter import OpenRouterClient  # noqa: E402


# --- OpenRouter Streaming ---------------------------------------------------


def _or_stream_chunks():
    """Typischer OpenRouter-Stream: Content-Chunk, Truncation-Chunk, Usage-Only-Chunk."""
    return [
        SimpleNamespace(
            choices=[SimpleNamespace(
                delta=SimpleNamespace(content="B", reasoning=None),
                finish_reason=None,
            )],
            usage=None,
        ),
        SimpleNamespace(
            choices=[SimpleNamespace(
                delta=SimpleNamespace(content=None, reasoning="weil "),
                finish_reason="length",
            )],
            usage=None,
        ),
        # Finaler Usage-Only-Chunk: choices LEER (hat vorher IndexError verursacht)
        SimpleNamespace(
            choices=[],
            usage=SimpleNamespace(
                total_tokens=10,
                prompt_tokens=4,
                completion_tokens=6,
                completion_tokens_details=SimpleNamespace(reasoning_tokens=3),
            ),
        ),
    ]


def test_openrouter_stream_captures_finish_reason():
    """Truncation (finish_reason='length') muss in die Metadata wandern."""
    client = OpenRouterClient(config={})
    received: list[str] = []
    text = client._process_openrouter_stream(
        iter(_or_stream_chunks()), used_max_tokens=300,
        fallback_triggered=False, stream_handler=received.append,
    )
    meta = client.last_response_metadata
    assert meta["finish_reason"] == "length"
    assert meta["token_limit_used"] == 300
    assert meta["token_limit_fallback"] is False
    assert text == "B"
    assert received == ["B"]


def test_openrouter_stream_usage_only_chunk_no_crash():
    """Leere choices-Liste (Usage-Only-Chunk) darf keinen IndexError werfen."""
    client = OpenRouterClient(config={})
    text = client._process_openrouter_stream(
        iter(_or_stream_chunks()), used_max_tokens=300,
        fallback_triggered=False, stream_handler=lambda _: None,
    )
    meta = client.last_response_metadata
    assert text == "B"
    assert meta["usage"] is not None
    assert meta["completion_tokens"] == 6
    assert meta["reasoning_tokens"] == 3
    assert meta["think_content"] == "weil "


def test_openrouter_stream_no_finish_reason_when_clean_stop():
    """Ohne Truncation (kein finish_reason im Stream) bleibt das Feld weg."""
    chunks = [SimpleNamespace(
        choices=[SimpleNamespace(
            delta=SimpleNamespace(content="A", reasoning=None),
            finish_reason="stop",
        )],
        usage=None,
    )]
    client = OpenRouterClient(config={})
    client._process_openrouter_stream(
        iter(chunks), used_max_tokens=300,
        fallback_triggered=False, stream_handler=lambda _: None,
    )
    assert client.last_response_metadata["finish_reason"] == "stop"


# --- Google Blocking --------------------------------------------------------


class _TextRaisingResponse:
    """Fake-Response: Candidate vorhanden, aber response.text raises ValueError
    (Thinking-only-Truncation — alle Tokens im Thinking-Budget verbraucht)."""

    def __init__(self, finish_reason_name: str | None) -> None:
        fr = SimpleNamespace(name=finish_reason_name) if finish_reason_name else None
        self.candidates = [SimpleNamespace(
            finish_reason=fr, content=SimpleNamespace(parts=[]),
        )]
        self.prompt_feedback = None
        self.usage_metadata = None

    @property
    def text(self) -> str:
        raise ValueError("no text parts in candidate")


@pytest.fixture(name="google_client")
def _google_client(monkeypatch: pytest.MonkeyPatch) -> GoogleClient:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    return GoogleClient(config={})


def test_google_blocking_max_tokens_not_masked_as_safety(google_client):
    """MAX_TOKENS bei Thinking-only-Truncation darf nicht zu SAFETY werden."""
    resp = _TextRaisingResponse("MAX_TOKENS")
    result = google_client._process_google_blocking(resp, 300, False)
    meta = google_client.last_response_metadata
    assert meta["finish_reason"] == "MAX_TOKENS"
    assert result.startswith("Error: Content blocked")


def test_google_blocking_safety_when_no_finish_reason(google_client):
    """Ohne Candidate-Finish-Reason (echter Block) greift SAFETY wie bisher."""
    resp = _TextRaisingResponse(None)
    google_client._process_google_blocking(resp, 300, False)
    assert google_client.last_response_metadata["finish_reason"] == "SAFETY"
