"""Tests: OpenRouter Host-Pinning + Upstream-Provider-Metadaten (Session 113).

Reproduzierbarkeits-Features nach der Leaderboard-Shift-Ursachenanalyse
(2026-09-22): OpenRouter routet pro Request auf wechselnde Upstream-Hosts mit
messbar unterschiedlichem Antwortstil. Diese Tests decken ab:

1. ``provider_routing``-Config wird als ``provider``-Parameter injiziert
2. Ohne Config-Eintrag wird NICHT gepinnt (Pool-Verhalten unverändert)
3. Der Upstream-Host wird aus Blocking- und Streaming-Responses extrahiert
4. ``_inject_client_metadata`` überträgt ihn ins BenchmarkResult
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from schemas.result import BenchmarkResult
from utils.base_runner import BaseBenchmarkRunner
from utils.providers.openrouter import OpenRouterClient

ROUTING_CFG = {
    "providers": {
        "commercial": {
            "openrouter": {
                "name": "OpenRouter",
                "api_type": "openrouter",
                "token_param_name": "max_tokens",
                "provider_routing": {
                    "xiaomi/mimo-v2.5": {
                        "order": ["Xiaomi"],
                        "allow_fallbacks": False,
                    },
                    "xiaomi_mimo_v2_5": {
                        "order": ["Xiaomi"],
                        "allow_fallbacks": False,
                    },
                },
            }
        }
    }
}


@pytest.fixture
def client():
    c = OpenRouterClient({})
    c._get_provider_cfg = lambda: ROUTING_CFG["providers"]["commercial"]["openrouter"]
    return c


class TestRoutingInjection:
    """provider_routing → OpenRouter unified parameter ``provider``."""

    def test_pinned_model_gets_provider_param(self, client):
        params, _, _ = client._build_openrouter_params(
            "xiaomi/mimo-v2.5", "prompt", 0.7, {}, None
        )
        assert params["extra_body"]["provider"] == {
            "order": ["Xiaomi"],
            "allow_fallbacks": False,
        }

    def test_internal_id_form_resolves_routing(self, client):
        params, _, _ = client._build_openrouter_params(
            "xiaomi_mimo_v2_5", "prompt", 0.7, {}, None
        )
        assert params["extra_body"]["provider"]["order"] == ["Xiaomi"]

    def test_unpinned_model_gets_no_provider_param(self, client):
        params, _, _ = client._build_openrouter_params(
            "z-ai/glm-5.3", "prompt", 0.7, {}, None
        )
        assert "provider" not in params["extra_body"]

    def test_empty_order_is_ignored(self, client):
        cfg = dict(ROUTING_CFG["providers"]["commercial"]["openrouter"])
        cfg["provider_routing"] = {"z-ai/glm-5.3": {"order": []}}
        client._get_provider_cfg = lambda: cfg
        params, _, _ = client._build_openrouter_params(
            "z-ai/glm-5.3", "prompt", 0.7, {}, None
        )
        assert "provider" not in params["extra_body"]

    def test_allow_fallbacks_defaults_to_absent(self, client):
        cfg = dict(ROUTING_CFG["providers"]["commercial"]["openrouter"])
        cfg["provider_routing"] = {"z-ai/glm-5.3": {"order": ["DeepInfra"]}}
        client._get_provider_cfg = lambda: cfg
        params, _, _ = client._build_openrouter_params(
            "z-ai/glm-5.3", "prompt", 0.7, {}, None
        )
        assert params["extra_body"]["provider"] == {"order": ["DeepInfra"]}


class TestUpstreamExtraction:
    """Upstream-Host aus OpenRouter-Responses (Feld ``provider``)."""

    def test_direct_attribute(self, client):
        resp = SimpleNamespace(provider="DeepInfra")
        assert client._extract_upstream_provider(resp) == "DeepInfra"

    def test_model_extra_dict(self, client):
        resp = SimpleNamespace(model_extra={"provider": "GMICloud"})
        assert client._extract_upstream_provider(resp) == "GMICloud"

    def test_missing_field_returns_none(self, client):
        resp = SimpleNamespace(model_extra={})
        assert client._extract_upstream_provider(resp) is None

    def test_non_string_provider_returns_none(self, client):
        resp = SimpleNamespace(provider=42)
        assert client._extract_upstream_provider(resp) is None

    def test_blocking_response_sets_metadata(self, client):
        msg = SimpleNamespace(content="Antwort", reasoning=None)
        resp = SimpleNamespace(
            choices=[SimpleNamespace(message=msg, finish_reason="stop")],
            usage=SimpleNamespace(
                total_tokens=10, prompt_tokens=5, completion_tokens=5
            ),
            provider="Venice",
        )
        client._process_openrouter_blocking(resp, 12000, False)
        assert client.last_response_metadata["upstream_provider"] == "Venice"

    def test_stream_response_sets_metadata_from_chunk(self, client):
        delta = SimpleNamespace(content="ok")
        chunk = SimpleNamespace(
            usage=None, choices=[SimpleNamespace(delta=delta, finish_reason=None)]
        )
        provider_chunk = SimpleNamespace(usage=None, choices=[], provider="Novita")
        with patch.object(
            OpenRouterClient, "_extract_reasoning_tokens", return_value=None
        ):
            client._process_openrouter_stream(
                [chunk, provider_chunk], 12000, False, stream_handler=MagicMock()
            )
        assert client.last_response_metadata["upstream_provider"] == "Novita"


class TestMetadataInjection:
    """upstream_provider fließt via _inject_client_metadata ins Result."""

    def test_inject_transfers_upstream_provider(self):
        runner = BaseBenchmarkRunner.__new__(BaseBenchmarkRunner)
        runner.client = SimpleNamespace(
            last_response_metadata={
                "finish_reason": "stop",
                "upstream_provider": "Minimax",
            },
            last_input_tokens=0,
            last_output_tokens=0,
        )
        result = BenchmarkResult(
            model="minimax/minimax-m3", module="cli_benchmark", task_id="t1"
        )
        runner._inject_client_metadata(result)
        assert result.upstream_provider == "Minimax"

    def test_inject_without_upstream_keeps_none(self):
        runner = BaseBenchmarkRunner.__new__(BaseBenchmarkRunner)
        runner.client = SimpleNamespace(
            last_response_metadata={"finish_reason": "stop"},
            last_input_tokens=0,
            last_output_tokens=0,
        )
        result = BenchmarkResult(
            model="z-ai/glm-5.3", module="code_quality", task_id="t1"
        )
        runner._inject_client_metadata(result)
        assert result.upstream_provider is None

    def test_build_base_result_includes_upstream_provider(self):
        """CSV-Spalten (dynamisch): upstream_provider landet im Result-Dict."""
        runner = BaseBenchmarkRunner.__new__(BaseBenchmarkRunner)
        runner.validator = SimpleNamespace(config={})
        exec_result = BenchmarkResult()
        exec_result.upstream_provider = "Xiaomi"

        row = runner.build_base_result(
            "xiaomi/mimo-v2.5",
            {"metadata": {"id": "code_quality_001", "name": "PHP Audit"}},
            exec_result,
            "openrouter",
        )

        assert row["upstream_provider"] == "Xiaomi"
