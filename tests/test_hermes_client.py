"""Tests für den Hermes-Gateway-Connector (Agentic Track).

Verifiziert (nur Mocks — keine Live-Endpoints, Security-Regel AGENTS.md):
- Auto-Registry bindet HermesClient an ``hermes``
- Modell-Mapping via ``hermes_model``: Fail-Fast ohne Silent-Fallback
- H1-Body-Fields: ``model`` (Hermes-Name) + ``provider`` (Gateway-ID)
- Frische X-Hermes-Session-Id pro Request (D7, Einzigartigkeit)
- Hermes-Fail-Fast-Signatur: HTTP 200 + usage=0 → RuntimeError
- Usage-/Think-Extraktion aus gemockten Chunks (inkl. ``reasoning``-Field)
- is_accessible-Semantik (Health down/401/usage=0 → False; ok+Probe → True)
- close()-Kette (TCP-FIN-Regel)
- token_param_name-Weitergabe, Probe-Timeout, Hermes-Extras im Streaming-Pfad
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from utils.providers.base import BaseProviderClient
from utils.providers.hermes import HermesClient, PROBE_TIMEOUT_SEC


HERMES_BASE_URL: str = "http://localhost:8642/v1"
HERMES_MODEL_ID: str = "qwen3_8-27b-nvfp4-hermes"
HERMES_MODEL_NAME: str = "Qwen3.8-27B-NVFP4"
HERMES_PROVIDER_ID: str = "gx10-vllm"
TOKEN_CAP: int = 16384


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _provider_config() -> dict:
    """Minimale Config mit hermes-Provider (strukturell wie provider_config.yaml)."""
    return {
        "providers": {
            "commercial": {
                "hermes": {
                    "name": "Hermes Agent (CrucibleMark-Profil)",
                    "api_type": "hermes",
                    "model_type": "open_weights_local",
                    "enabled": True,
                    "base_url": HERMES_BASE_URL,
                    "api_key": "${API_SERVER_KEY}",
                    "request_timeout": 2400,
                    "token_param_name": "max_tokens",
                    "hermes_provider": HERMES_PROVIDER_ID,
                    "models": [
                        {
                            "id": HERMES_MODEL_ID,
                            "name": "Qwen 3.8 27B NVFP4 (Hermes-Loop, vLLM gx10)",
                            "hermes_model": HERMES_MODEL_NAME,
                        },
                    ],
                },
            },
        },
    }


@pytest.fixture
def client(monkeypatch):
    """HermesClient mit aufgelöstem Env-Key und gestubbtem Token-Budget."""
    monkeypatch.setenv("API_SERVER_KEY", "test-key-123")
    hc = HermesClient(_provider_config())
    monkeypatch.setattr(
        HermesClient, "_resolve_request_tokens",
        lambda self, model, kwargs: ("max_tokens", TOKEN_CAP),
    )
    return hc


def _fake_response(content: str, total_tokens: int, finish_reason: str = "stop") -> SimpleNamespace:
    """Blocking-Response-Objekt (OpenAI-SDK-Struktur, minimale Felder)."""
    return SimpleNamespace(
        id="chatcmpl-test",
        # Realistisch: der Gateway echo't das servierte Modell (Hermes-Name),
        # nicht unsere CrucibleMark-Benchmark-ID (Echo-Guard-Referenz).
        model=HERMES_MODEL_NAME,
        choices=[SimpleNamespace(
            message=SimpleNamespace(content=content, reasoning=None),
            finish_reason=finish_reason,
        )],
        usage=SimpleNamespace(
            prompt_tokens=120, completion_tokens=20, total_tokens=total_tokens,
            completion_tokens_details=None,
        ),
    )


def _fake_chunk(delta=None, usage=None, finish_reason=None, chunk_id="chatcmpl-s") -> SimpleNamespace:
    """SSE-Chunk-Objekt (OpenAI-SDK-Struktur, minimale Felder)."""
    return SimpleNamespace(
        id=chunk_id, model=HERMES_MODEL_NAME,
        choices=[SimpleNamespace(delta=delta or SimpleNamespace(content=None), finish_reason=finish_reason)],
        usage=usage,
    )


# ---------------------------------------------------------------------------
# Registry & Config
# ---------------------------------------------------------------------------

class TestRegistry:
    def test_auto_registry_binding(self):
        assert BaseProviderClient._registry["hermes"] is HermesClient

    def test_api_key_fail_fast_without_env(self, monkeypatch):
        monkeypatch.delenv("API_SERVER_KEY", raising=False)
        hc = HermesClient(_provider_config())
        with pytest.raises(ValueError, match="API_SERVER_KEY"):
            _ = hc._api_key()


# ---------------------------------------------------------------------------
# Modell-Mapping (Fail-Fast, H1-Fields)
# ---------------------------------------------------------------------------

class TestModelMapping:
    def test_maps_via_hermes_model_field(self, client):
        assert client._map_hermes_model(HERMES_MODEL_ID) == HERMES_MODEL_NAME

    def test_missing_hermes_model_field_fails_fast(self, client):
        client.config["providers"]["commercial"]["hermes"]["models"][0].pop("hermes_model")
        with pytest.raises(ValueError, match="hermes_model"):
            client._map_hermes_model(HERMES_MODEL_ID)

    def test_unknown_model_fails_fast(self, client):
        with pytest.raises(ValueError, match="hermes_model"):
            client._map_hermes_model("does-not-exist")

    def test_model_payload_carries_h1_fields(self, client):
        payload = client._model_payload(HERMES_MODEL_ID)
        assert payload["model"] == HERMES_MODEL_NAME
        assert payload["extra_body"] == {"provider": HERMES_PROVIDER_ID}

    def test_reasoning_effort_maps_to_model_options(self, client):
        client.config["providers"]["commercial"]["hermes"]["models"][0]["reasoning_effort"] = "medium"
        payload = client._model_payload(HERMES_MODEL_ID)
        assert payload["extra_body"]["model_options"] == {
            "reasoning": {"enabled": True, "effort": "medium"},
        }

    def test_without_reasoning_effort_no_model_options(self, client):
        assert "model_options" not in client._model_payload(HERMES_MODEL_ID)["extra_body"]


# ---------------------------------------------------------------------------
# Session-Isolation (D7)
# ---------------------------------------------------------------------------

class TestSessionIsolation:
    def test_fresh_session_id_per_request(self, client):
        params_one = client._build_chat_params(HERMES_MODEL_ID, "p1", None)
        params_two = client._build_chat_params(HERMES_MODEL_ID, "p2", None)
        sid_one = params_one["extra_headers"]["X-Hermes-Session-Id"]
        sid_two = params_two["extra_headers"]["X-Hermes-Session-Id"]
        assert sid_one != sid_two
        assert len(sid_one) == 36

    def test_session_header_reaches_sdk_call(self, client):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _fake_response("OK", 200)
        client._client = mock_client
        client.query(HERMES_MODEL_ID, "ping", temperature=0.1)
        kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert "X-Hermes-Session-Id" in kwargs["extra_headers"]
        assert kwargs["model"] == HERMES_MODEL_NAME
        assert kwargs["extra_body"]["provider"] == HERMES_PROVIDER_ID


# ---------------------------------------------------------------------------
# Hermes-Fail-Fast-Signatur
# ---------------------------------------------------------------------------

class TestHermesFailureSignature:
    def test_zero_usage_raises(self, client):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _fake_response(
            "⚠️ Provider authentication failed: Unknown provider 'x'.", 0)
        client._client = mock_client
        with pytest.raises(RuntimeError, match="ohne Token-Verbrauch"):
            client.query(HERMES_MODEL_ID, "ping", temperature=0.1)

    def test_stream_zero_usage_raises(self, client):
        chunks = [
            _fake_chunk(delta=SimpleNamespace(content="⚠️ error")),
            _fake_chunk(usage=SimpleNamespace(total_tokens=0), finish_reason="stop"),
        ]
        client._client = MagicMock()
        client._client.chat.completions.create.return_value = iter(chunks)
        with pytest.raises(RuntimeError, match="ohne Token-Verbrauch"):
            client.query(HERMES_MODEL_ID, "ping", temperature=0.1, stream_handler=lambda s: None)


# ---------------------------------------------------------------------------
# Usage-/Think-Extraktion
# ---------------------------------------------------------------------------

class TestExtraction:
    def test_blocking_metadata_content_and_usage(self, client):
        response = _fake_response("Antwort", 140)
        response.choices[0].message.reasoning = "Gedanke"
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = response
        client._client = mock_client
        result = client.query(HERMES_MODEL_ID, "ping", temperature=0.1)
        assert result == "Antwort"
        meta = client.last_response_metadata
        assert meta["usage"].total_tokens == 140
        assert meta["think_content"] == "Gedanke"
        assert meta["token_limit_used"] == TOKEN_CAP

    def test_stream_content_usage_and_reasoning(self, client):
        usage = SimpleNamespace(prompt_tokens=100, completion_tokens=40, total_tokens=140,
                                completion_tokens_details=None)
        chunks = [
            _fake_chunk(delta=SimpleNamespace(content="Hello ", reasoning=None)),
            _fake_chunk(delta=SimpleNamespace(content=None, reasoning="Denkschritt")),
            _fake_chunk(delta=SimpleNamespace(content="world", reasoning=None)),
            _fake_chunk(usage=usage, finish_reason="stop"),
        ]
        client._client = MagicMock()
        client._client.chat.completions.create.return_value = iter(chunks)
        parts: list[str] = []
        result = client.query(HERMES_MODEL_ID, "ping", temperature=0.1,
                              stream_handler=parts.append)
        assert result == "Hello world"
        assert "".join(parts) == "Hello world"
        meta = client.last_response_metadata
        assert meta["usage"].total_tokens == 140
        assert meta["think_content"] == "Denkschritt"
        assert meta["finish_reason"] == "stop"


# ---------------------------------------------------------------------------
# is_accessible
# ---------------------------------------------------------------------------

class TestIsAccessible:
    def test_true_when_health_and_probe_ok(self, client, monkeypatch):
        monkeypatch.setattr(client, "_is_gateway_healthy", lambda: True)
        monkeypatch.setattr(client, "_probe_completion", lambda model: True)
        assert client.is_accessible() is True

    def test_false_when_health_down(self, client, monkeypatch):
        monkeypatch.setattr(client, "_is_gateway_healthy", lambda: False)
        assert client.is_accessible() is False

    def test_false_when_probe_fails(self, client, monkeypatch):
        monkeypatch.setattr(client, "_is_gateway_healthy", lambda: True)
        monkeypatch.setattr(client, "_probe_completion", lambda model: False)
        assert client.is_accessible() is False

    def test_probe_uses_first_configured_model(self, client):
        seen: list[str] = []
        client._client = MagicMock()
        client._client.chat.completions.create.return_value = _fake_response("Hi", 50)
        original = client._model_payload

        def _spy(model):
            seen.append(model)
            return original(model)

        client._model_payload = _spy  # type: ignore[method-assign]
        assert client._probe_completion(HERMES_MODEL_ID) is True
        assert seen == [HERMES_MODEL_ID]
        kwargs = client._client.chat.completions.create.call_args.kwargs
        assert kwargs["extra_body"]["provider"] == HERMES_PROVIDER_ID

    def test_get_available_models_from_config(self, client):
        assert client.get_available_models() == [HERMES_MODEL_ID]


# ---------------------------------------------------------------------------
# Framework-Verdrahtung (token_param_name, Probe-Timeout, Stream-Extras)
# ---------------------------------------------------------------------------

class TestFrameworkWiring:
    def test_token_param_name_from_config_reaches_sdk(self, client, monkeypatch):
        """Resolve-Wert wird durchgereicht, nicht 'max_tokens' hardcodiert."""
        monkeypatch.setattr(
            HermesClient, "_resolve_request_tokens",
            lambda self, model, kwargs: ("max_completion_tokens", TOKEN_CAP),
        )
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _fake_response("OK", 200)
        client._client = mock_client
        client.query(HERMES_MODEL_ID, "ping", temperature=0.1)
        kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert kwargs["max_completion_tokens"] == TOKEN_CAP
        assert "max_tokens" not in kwargs

    def test_probe_completion_carries_fresh_session_header(self, client):
        """Accessibility-Probe läuft über den Session-Header-Pfad (AGENTS 2026-09-16).

        Ohne Header mappt der Gateway den Request per Fingerabdruck auf eine
        bestehende Session — die Probe würde dann History anhängen.
        """
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _fake_response("Hi", 40)
        client._client = mock_client
        assert client._probe_completion(HERMES_MODEL_ID) is True
        first = mock_client.chat.completions.create.call_args.kwargs["extra_headers"]
        assert "X-Hermes-Session-Id" in first

        client._probe_completion(HERMES_MODEL_ID)
        second = mock_client.chat.completions.create.call_args.kwargs["extra_headers"]
        assert second["X-Hermes-Session-Id"] != first["X-Hermes-Session-Id"]

    def test_thinking_mode_records_reasoning_effort(self, monkeypatch):
        """Agentic-Track: reasoning_effort ist Thinking-Konfiguration (kein enable_thinking-Toggle).

        Rein protokollierend — thinking_mode geht nur in Audit-Log, Leaderboard-Spalte
        und Web-Export, nicht in Judge-Prompt oder Scoring.
        """
        import types

        from utils import base_runner as br

        cfg = {"providers": {"commercial": {"hermes": {"models": [
            {"id": HERMES_MODEL_ID, "reasoning_effort": "medium"},
        ]}}}}
        stub = types.SimpleNamespace(validator=types.SimpleNamespace(config=cfg))
        monkeypatch.setattr(br, "resolve_model_cfg_for", lambda mid, c: {"reasoning_effort": "medium"})
        assert br.BaseBenchmarkRunner._resolve_thinking_mode(stub, HERMES_MODEL_ID, "hermes") == "Thinking"

        # Control: ohne jeden Thinking-Hinweis bleibt n/a (Cloud-Provider)
        monkeypatch.setattr(br, "resolve_model_cfg_for", lambda mid, c: {"temperature": 0.7})
        assert br.BaseBenchmarkRunner._resolve_thinking_mode(stub, "x", "mistral") == "n/a"

        # Control: dual-profile-Eintrag wird weiterhin vom früheren Zweig entschieden
        monkeypatch.setattr(br, "resolve_model_cfg_for", lambda mid, c: {
            "chat_template_kwargs": {"enable_thinking": False}, "reasoning_effort": "medium"})
        assert br.BaseBenchmarkRunner._resolve_thinking_mode(stub, "qwen_raw", "vllm_spark") == "Standard"

    def test_probe_completion_uses_probe_timeout(self, client):
        """is_accessible-Probe darf nicht an der 2400-s-Lese-Wand hängen."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _fake_response("Hi", 50)
        client._client = mock_client
        assert client._probe_completion(HERMES_MODEL_ID) is True
        kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert kwargs["timeout"] == PROBE_TIMEOUT_SEC

    def test_stream_captures_hermes_extras_and_incomplete_warning(self, client, caplog):
        """Hermes-Extras (completed=False) werden auch im Streaming-Pfad sichtbar."""
        usage = SimpleNamespace(prompt_tokens=100, completion_tokens=40, total_tokens=140,
                                completion_tokens_details=None)
        chunks = [
            _fake_chunk(delta=SimpleNamespace(content="Antwort", reasoning=None)),
            _fake_chunk(usage=usage, finish_reason="stop"),
        ]
        # Hermes-Extras hängen am Final-Chunk (SDK behält unbekannte Felder)
        chunks[-1].hermes = {"tool_calls": 3}
        chunks[-1].completed = False
        client._client = MagicMock()
        client._client.chat.completions.create.return_value = iter(chunks)
        with caplog.at_level("WARNING"):
            result = client.query(HERMES_MODEL_ID, "ping", temperature=0.1,
                                  stream_handler=lambda s: None)
        assert result == "Antwort"
        meta = client.last_response_metadata
        assert meta["hermes_extras"] == {"tool_calls": 3}
        assert meta["hermes_completed"] is False
        assert any("nicht komplett abgeschlossen" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# close()-Kette
# ---------------------------------------------------------------------------

class TestClose:
    def test_close_releases_client(self, client):
        mock_client = MagicMock()
        client._client = mock_client
        client.close()
        mock_client.close.assert_called_once()
        assert client._client is None

    def test_close_is_idempotent(self, client):
        client._client = MagicMock()
        client.close()
        client.close()
        assert client._client is None


# ---------------------------------------------------------------------------
# Echo-Guard (Miss-Labeling-Schutz, direct_model_requests: true)
# ---------------------------------------------------------------------------

class TestEchoGuard:
    """Abweichendes Gateway-Echo muss laut scheitern, fehlendes Echo bleibt prüfbar-los."""

    def test_blocking_mismatch_raises(self, client):
        mock_client = MagicMock()
        resp = _fake_response("Antwort", 140)
        resp.model = "qwen3.8-flash"          # anderes Modell als gemappt
        mock_client.chat.completions.create.return_value = resp
        client._client = mock_client
        with pytest.raises(ValueError, match="Gateway-Echo"):
            client.query(HERMES_MODEL_ID, "ping", temperature=0.1)

    def test_stream_mismatch_raises(self, client):
        chunks = [
            _fake_chunk(delta=SimpleNamespace(content="Text")),
            _fake_chunk(
                delta=SimpleNamespace(content=""),
                usage=SimpleNamespace(
                    prompt_tokens=120, completion_tokens=20, total_tokens=140,
                    completion_tokens_details=None,
                ),
                finish_reason="stop",
            ),
        ]
        for ch in chunks:
            ch.model = "ein-anderes-modell"
        client._client = MagicMock()
        client._client.chat.completions.create.return_value = iter(chunks)
        with pytest.raises(ValueError, match="Gateway-Echo"):
            client.query(HERMES_MODEL_ID, "ping", temperature=0.1, stream_handler=lambda s: None)

    def test_missing_echo_is_tolerated(self, client):
        """Gateway ohne model-Feld darf nicht brechen — nicht prüfbar ist nicht falsch."""
        mock_client = MagicMock()
        resp = _fake_response("Antwort", 140)
        resp.model = None
        mock_client.chat.completions.create.return_value = resp
        client._client = mock_client
        assert client.query(HERMES_MODEL_ID, "ping", temperature=0.1) == "Antwort"

    def test_case_insensitive_echo_passes(self, client):
        mock_client = MagicMock()
        resp = _fake_response("Antwort", 140)
        resp.model = HERMES_MODEL_NAME.lower()
        mock_client.chat.completions.create.return_value = resp
        client._client = mock_client
        assert client.query(HERMES_MODEL_ID, "ping", temperature=0.1) == "Antwort"

    def test_correct_echo_lands_in_metadata(self, client):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _fake_response("Antwort", 140)
        client._client = mock_client
        client.query(HERMES_MODEL_ID, "ping", temperature=0.1)
        assert client.last_response_metadata["model"] == HERMES_MODEL_NAME
