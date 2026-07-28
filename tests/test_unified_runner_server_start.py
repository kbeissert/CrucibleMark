"""Tests für ``UnifiedBenchmarkRunner._ensure_llamacpp_server``.

Verifiziert:
- ``start_server() == False`` (z. B. Pfad 2c Endpoint-Konflikt in
  ``vllm_base.py``) wirft ``RuntimeError`` mit der Phrase
  ``"endpoint conflict or startup failure"`` — der bestehende
  Exception-Handler in ``_run_asset_loop`` (``unified_runner.py``)
  erkennt diese Phrase und bricht den Modullauf ab. Damit werden
  fehlerhafte 0%-Einträge in der CSV verhindert.
- Exception aus ``start_server()`` wird als ``RuntimeError`` mit
  ``from``-Chain gewrapped.
- Provider außerhalb ``("llamacpp", "llamacpp_spark", "vllm_spark")``
  ist no-op (returnt ``None``).
- Client fehlt im Registry → Error-Result (Asset-spezifisch, nicht
  fatal — kann theoretisch pro Asset variieren).
"""
from unittest.mock import MagicMock

import pytest

from scripts.core.unified_runner import UnifiedBenchmarkRunner


def _make_runner(client: MagicMock | None) -> UnifiedBenchmarkRunner:
    runner = UnifiedBenchmarkRunner.__new__(UnifiedBenchmarkRunner)
    runner.client = MagicMock()
    runner.client.clients = {"vllm_spark": client} if client else {}
    return runner


class TestEnsureLlamaCppServer:
    def test_raises_when_start_server_returns_false(self):
        """Regression: Pfad 2c in vllm_base.py (Endpoint-Konflikt) → Fatal.

        Vorher: Error-Result → Loop lief weiter → 5× 0% in CSV.
        Nachher: RuntimeError mit Magic-Phrase → _run_asset_loop bricht ab.
        """
        client = MagicMock()
        client.start_server.return_value = False
        runner = _make_runner(client)

        with pytest.raises(
            RuntimeError,
            match="endpoint conflict or startup failure",
        ):
            runner._ensure_llamacpp_server(
                model="qwen3_6-27b-nvfp4-thinking",
                provider="vllm_spark",
                asset_id="001",
            )

    def test_wraps_start_server_exception_with_from_chain(self):
        """Connector-Exception wird als RuntimeError gewrapped (raise from)."""
        client = MagicMock()
        client.start_server.side_effect = ConnectionError("ssh timeout")
        runner = _make_runner(client)

        with pytest.raises(RuntimeError) as excinfo:
            runner._ensure_llamacpp_server(
                model="my-model",
                provider="vllm_spark",
                asset_id="002",
            )
        assert "endpoint conflict or startup failure" in str(excinfo.value)
        assert "ssh timeout" in str(excinfo.value)
        assert isinstance(excinfo.value.__cause__, ConnectionError)

    def test_returns_none_when_provider_is_not_local(self):
        """Nur llama.cpp-/vLLM-Provider gehen durch start_server-Pfad."""
        runner = _make_runner(MagicMock())
        assert runner._ensure_llamacpp_server(
            model="gpt-4", provider="openai", asset_id="x",
        ) is None

    def test_returns_error_result_when_client_missing_from_registry(self):
        """Provider-Client fehlt → Asset-spezifisches Error-Result (kein Fatal).

        Begründung: Wenn z. B. ein einzelnes Asset auf einen anderen Provider
        zugreifen will als die anderen, ist das Asset-spezifisch behandelbar.
        Ein Fatal wäre hier zu hart — unterscheidet sich vom start_server-Fail
        (Lifecycle-Problem, alle Assets betroffen).
        """
        runner = _make_runner(client=None)
        result = runner._ensure_llamacpp_server(
            model="x", provider="vllm_spark", asset_id="003",
        )
        assert result is not None
        assert result.get("status") == "error"
        assert "nicht im LLMClient-Registry" in result.get("error_message", "")

    def test_returns_none_when_start_succeeds(self):
        """Happy-Path: start_server True → None (Loop läuft normal weiter)."""
        client = MagicMock()
        client.start_server.return_value = True
        runner = _make_runner(client)

        assert runner._ensure_llamacpp_server(
            model="x", provider="vllm_spark", asset_id="004",
        ) is None
        client.start_server.assert_called_once_with("x")

    @pytest.mark.parametrize("provider", ["llamacpp", "llamacpp_spark", "vllm_spark"])
    def test_local_providers_all_go_through_start_server(self, provider):
        """Alle drei OpenAI-kompatiblen lokalen Provider nutzen start_server."""
        client = MagicMock()
        client.start_server.return_value = True
        runner = _make_runner(client)
        runner.client.clients = {provider: client}

        runner._ensure_llamacpp_server(
            model="m", provider=provider, asset_id="x",
        )
        client.start_server.assert_called_once_with("m")
