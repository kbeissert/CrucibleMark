"""
Tests für utils/provider_selector.py — Agentic-Loop-Pfad (Hermes-Track, D5/D6).

Deckt ab:
    - select_provider()              (Menü-Option + Typ-Routing auf agentic)
    - D6-Batch-Grenze                (Agentic-Track bleibt auch bei enabled: true
                                      außerhalb von --all/benchmark-auto)
    - _collect_agentic_providers()   (api_type-Erkennung über BEIDE Sektionen,
                                      enabled/disabled-Aufteilung, Fremd-Provider ignoriert)
    - _select_agentic_model()        (Modell-Liste, Rückgabe (provider, id),
                                      Fail-Fast bei deaktiviertem Provider / leeren Modellen)

Kein Netzwerk, kein interaktiver Prompt — select_from_list wird gemockt.
"""

from __future__ import annotations

import pytest

from utils import provider_selector as ps
from utils.provider_selector import ProviderSelector


HERMES_CFG = {
    "name": "Hermes Agent (CrucibleMark-Profil)",
    "api_type": "hermes",
    "model_type": "open_weights_local",
    "enabled": True,
    "hermes_provider": "gx10-vllm",
    "models": [
        {
            "id": "qwen3_8-27b-nvfp4-hermes",
            "name": "Qwen 3.8 27B NVFP4 (Hermes-Loop, vLLM gx10)",
            "hermes_model": "Qwen3.8-27B-NVFP4",
        }
    ],
}


def _config(enabled: bool = True) -> dict:
    """Minimal-Config mit hermes unter commercial (Plan: D6-Platzierung)."""
    cfg = {**HERMES_CFG, "enabled": enabled, "models": [dict(m) for m in HERMES_CFG["models"]]}
    return {
        "providers": {
            "commercial": {"openrouter": {"name": "OR", "enabled": True, "models": []}, "hermes": cfg},
            "local": {"vllm_spark": {"name": "vLLM", "api_type": "vllm", "enabled": True, "models": []}},
        }
    }


@pytest.fixture
def captured(monkeypatch):
    """Fängt select_from_list-Aufrufe ab; .choice steuert das Auswahl-Ergebnis."""

    class Capture:
        def __init__(self):
            self.calls: list[dict] = []
            self.choice = None
            self.abort = False  # bricht nach Aufnahme ab (Listen-Inspektion)

        def __call__(self, items, display_func, prompt, title):  # noqa: D102
            self.calls.append({"items": items, "prompt": prompt, "title": title})
            if self.abort:
                raise SystemExit(0)
            return self.choice

    cap = Capture()
    monkeypatch.setattr(ps, "select_from_list", cap)
    return cap


class TestCollectAgenticProviders:
    def test_findet_hermes_unter_commercial(self):
        enabled, disabled = ProviderSelector._collect_agentic_providers(_config())
        assert [k for k, _ in enabled] == ["hermes"]
        assert disabled == []

    def test_deaktivierter_provider_landet_bei_disabled(self):
        enabled, disabled = ProviderSelector._collect_agentic_providers(_config(enabled=False))
        assert enabled == []
        assert [k for k, _ in disabled] == ["hermes"]

    def test_fremde_providerwerden_ignoriert(self):
        cfg = _config()
        cfg["providers"]["local"]["ollama_local"] = {"name": "O", "enabled": True, "models": []}
        enabled, _ = ProviderSelector._collect_agentic_providers(cfg)
        assert [k for k, _ in enabled] == ["hermes"]

    def test_erkennt_agentic_auch_unter_local_sektion(self):
        cfg = _config(enabled=False)
        cfg["providers"]["local"]["hermes_lab"] = dict(HERMES_CFG, enabled=True)
        enabled, disabled = ProviderSelector._collect_agentic_providers(cfg)
        assert [k for k, _ in enabled] == ["hermes_lab"]
        assert [k for k, _ in disabled] == ["hermes"]


class TestSelectAgenticModel:
    def test_gibt_provider_key_und_modell_id_zurueck(self, captured):
        captured.choice = {
            "provider": "hermes",
            "id": "qwen3_8-27b-nvfp4-hermes",
            "name": "Qwen 3.8 27B NVFP4 (Hermes-Loop, vLLM gx10)",
        }
        assert ProviderSelector(_config())._select_agentic_model() == (
            "hermes",
            "qwen3_8-27b-nvfp4-hermes",
        )

    def test_listet_nur_agentic_modelle_mit_loop_mapping(self, captured):
        captured.abort = True  # Abbruch nach Aufnahme der Liste
        with pytest.raises(SystemExit):
            ProviderSelector(_config())._select_agentic_model()
        items = captured.calls[0]["items"]
        assert [i["id"] for i in items] == ["qwen3_8-27b-nvfp4-hermes"]
        assert items[0]["loop_model"] == "Qwen3.8-27B-NVFP4"
        assert items[0]["provider"] == "hermes"

    def test_deaktivierter_provider_fail_fast_mit_hinweis(self, captured, caplog):
        with pytest.raises(SystemExit) as exc:
            ProviderSelector(_config(enabled=False))._select_agentic_model()
        assert exc.value.code == 1
        assert captured.calls == []

    def test_aktiviert_ohne_modelle_fail_fast(self, captured):
        cfg = _config()
        cfg["providers"]["commercial"]["hermes"]["models"] = []
        with pytest.raises(SystemExit) as exc:
            ProviderSelector(cfg)._select_agentic_model()
        assert exc.value.code == 1


class TestProviderTypeRouting:
    def test_menu_bietet_agentic_typ_an(self, captured):
        captured.choice = None  # Auswahl abbrechen → select_provider exitet
        with pytest.raises(SystemExit):
            ProviderSelector(_config()).select_provider(None)
        options = captured.calls[0]["items"]
        assert "agentic" in [key for key, _ in options]

    def test_typ_agentic_routet_auf_agentic_auswahl(self, monkeypatch):
        called = {}

        def fake(self):  # noqa: ANN001
            called["hit"] = True
            return "hermes", "qwen3_8-27b-nvfp4-hermes"

        monkeypatch.setattr(ProviderSelector, "_select_agentic_model", fake)
        assert ProviderSelector(_config()).select_provider("agentic") == (
            "hermes",
            "qwen3_8-27b-nvfp4-hermes",
        )
        assert called.get("hit") is True


class TestBatchExclusionD6:
    """D6: enabled: true macht den Agentic-Track bereit, aber kein Batch-Modell."""

    def test_commercial_discovery_ignoriert_agentic(self):
        from utils.model_id_base import get_commercial_models_from_config

        ids = [t[0] for t in get_commercial_models_from_config(_config())]
        assert "qwen3_8-27b-nvfp4-hermes" not in ids

    def test_batch_discovery_ignoriert_agentic(self):
        from scripts.core.model_discovery import discover_models

        assert "qwen3_8-27b-nvfp4-hermes" not in discover_models("commercial", _config())
        assert "qwen3_8-27b-nvfp4-hermes" not in discover_models("all", _config())

    def test_benchmark_auto_provider_filter_ignoriert_agentic(self):
        import types

        from scripts.core.benchmark_auto import _resolve_active_commercial_providers

        active = _resolve_active_commercial_providers(types.SimpleNamespace(config=_config()))
        assert "hermes" not in active
