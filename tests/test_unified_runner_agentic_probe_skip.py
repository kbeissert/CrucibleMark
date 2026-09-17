"""
Thinking-Probe-Guard für Agentic-Provider (D9) — scripts/core/unified_runner.py.

Im Agent-Loop ist der Reasoning-Kanal nicht observierbar (der Loop entfernt
Think-Blöcke aus dem final_response, der Gateway exportiert keine
reasoning-Felder). Eine Probe wäre dort weder verlässlich noch billig —
Capability kommt per Vererbung aus der Raw-Partner-Card.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts.core.unified_runner import UnifiedBenchmarkRunner

AGENTIC_CFG = {
    "providers": {
        "commercial": {
            "hermes": {"api_type": "hermes", "enabled": True, "models": []},
            "mistral": {"api_type": "openai_compatible", "enabled": True, "models": []},
        },
        "local": {"vllm_spark": {"api_type": "vllm", "enabled": True, "models": []}},
    }
}


@pytest.fixture
def runner():
    r = UnifiedBenchmarkRunner.__new__(UnifiedBenchmarkRunner)
    r.validator = SimpleNamespace(config=AGENTIC_CFG)
    r._probed_models = set()
    return r


class TestIsAgenticProvider:
    @pytest.mark.parametrize(
        "provider,expected",
        [("hermes", True), ("mistral", False), ("vllm_spark", False), ("unbekannt", False)],
    )
    def test_erkennt_nur_agentic_blocke(self, runner, provider, expected):
        assert runner._is_agentic_provider(provider) is expected

    def test_findet_agentic_auch_unter_local_sektion(self, runner):
        cfg = {"providers": {"local": {"hermes_lab": {"api_type": "hermes"}}}}
        runner.validator = SimpleNamespace(config=cfg)
        assert runner._is_agentic_provider("hermes_lab") is True


class TestProbeSkipForAgentic:
    def test_agentic_probe_wird_nicht_gesendet(self, runner, monkeypatch):
        calls = []
        monkeypatch.setattr(
            "scripts.core.unified_runner.probe_thinking_model",
            lambda *a, **k: calls.append(a),
        )
        assert runner._run_thinking_probe_or_skip("qwen3_8-27b-nvfp4-hermes", "hermes") is None
        assert calls == [], "Agentic-Entität darf keine Thinking-Probe senden (D9)"
        assert "qwen3_8-27b-nvfp4-hermes" in runner._probed_models

    def test_normaler_provider_probt_weiter(self, runner, monkeypatch):
        probe = SimpleNamespace(detected=True, confidence="high")
        monkeypatch.setattr(
            "scripts.core.unified_runner.probe_thinking_model",
            lambda *a, **k: probe,
        )
        assert runner._run_thinking_probe_or_skip("mistral-large", "mistral") is probe
