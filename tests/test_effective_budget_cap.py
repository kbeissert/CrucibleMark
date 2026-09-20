"""Tests für den wirksamen Budget-Cap der Eskalationsleiter (Session 110).

Befund: Der senkende Override ``z-ai/glm-5.3: 24000`` cappte die Card-
Kalibrierung (32000) und Stufe-3-Re-Asks STILL auf 24000 — der Cap-Block-Guard
sah nur den Card-Cap, nicht den Provider-Override. „Re-Ask mit 32000" war
faktisch ein identischer 24000-Request (Erfolg nur durch Modell-Varianz).

Fix: ``BaseProviderClient._resolve_effective_budget_cap`` = Kaskaden-SSoT
(min(Override ?? Provider-Default, Card-Cap)) — die Leiter sieht den Cap, unter
dem sie faktisch requestet, und der Cap-Block-Guard feuert sichtbar.

SSoT: ``utils/providers/base.py::_resolve_effective_budget_cap``.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.providers.base import BaseProviderClient  # noqa: E402
from utils.providers.openrouter import OpenRouterClient  # noqa: E402


class _CapClient(BaseProviderClient):
    """Stub mit konfigurierbarer Provider-Config."""

    PROVIDER_NAMES = ["testcap"]

    def __init__(self, provider_cfg: dict):
        super().__init__(config={})
        self._provider_cfg = provider_cfg

    def _get_provider_cfg(self) -> dict:
        return self._provider_cfg


def _patch_card_cap(monkeypatch: pytest.MonkeyPatch, cap: int | None) -> None:
    monkeypatch.setattr(
        "utils.model_thinking._read_max_output_tokens_from_card", lambda m: cap,
    )


def test_cap_cascade_provider_default(monkeypatch):
    """Ohne Override/Card-Cap gilt der Provider-Default."""
    _patch_card_cap(monkeypatch, None)
    client = _CapClient({"max_tokens": 32768, "model_max_tokens": {}})
    assert client._resolve_effective_budget_cap("some/model") == 32768


def test_cap_cascade_override_wins(monkeypatch):
    """Senkender Override schlägt den Provider-Default."""
    _patch_card_cap(monkeypatch, None)
    client = _CapClient(
        {"max_tokens": 32768, "model_max_tokens": {"some/model": 24000}},
    )
    assert client._resolve_effective_budget_cap("some/model") == 24000


def test_cap_cascade_card_cap_limits(monkeypatch):
    """Card-Cap (max_output_tokens) begrenzt zusätzlich — min()-Semantik."""
    _patch_card_cap(monkeypatch, 16384)
    client = _CapClient({"max_tokens": 32768, "model_max_tokens": {}})
    assert client._resolve_effective_budget_cap("some/model") == 16384


def test_cap_cascade_card_cap_below_override(monkeypatch):
    """Der WIRKSAME Cap ist das Minimum aus Override und Card-Cap."""
    _patch_card_cap(monkeypatch, 12000)
    client = _CapClient(
        {"max_tokens": 32768, "model_max_tokens": {"some/model": 24000}},
    )
    assert client._resolve_effective_budget_cap("some/model") == 12000


def test_cap_cascade_config_form_lookup(monkeypatch):
    """Override-Lookup funktioniert über Internal-Form → Config-Form
    (Underscore→Dot in Version-Segmenten, echtes GLM-Beispiel)."""
    _patch_card_cap(monkeypatch, None)
    client = _CapClient(
        {"max_tokens": 32768, "model_max_tokens": {"z-ai/glm-5.3": 24000}},
    )
    assert client._resolve_effective_budget_cap("z-ai/glm-5_3") == 24000


def test_ladder_cap_block_guard_sees_override(monkeypatch, caplog):
    """Integritäts-Nachweis: Stufen-Ziel über dem wirksamen Cap → Cap-Block-Guard
    feuert SICHTBAR (statt still identischer Re-Requests)."""
    import logging

    _patch_card_cap(monkeypatch, None)
    client = _CapClient(
        {
            "max_tokens": 32768,
            "model_max_tokens": {"some/model": 24000},
        },
    )
    # reasoning_reask gehört in die benchmark_config (self.config), nicht in die
    # Provider-Config — LR deaktiviert, damit der Cap-Block-Guard isoliert getestet
    # wird (das LR-Verhalten bei Cap-Block hat eigene Tests in test_last_resort_mode).
    client.config = {
        "reasoning_reask": {
            "ceilings": [24000, 32000], "max_escalations": 2, "last_resort_budget": 0,
        },
    }
    client.last_response_metadata = {
        "finish_reason": "length",
        "token_limit_used": 24000,
        "think_content": "x",
        "reasoning_tokens": 24000,
    }
    calls: list[dict] = []

    def _query(**kwargs) -> str:
        calls.append(kwargs)
        return ""

    with caplog.at_level(logging.WARNING, logger="utils.providers.base"):
        result = client._maybe_reask_reasoning_truncation(
            content="", model="some/model", prompt="P", temperature=1.0,
            stream_handler=None, kwargs={"_module_key": "code_quality"},
            query=_query, budget_cap=client._resolve_effective_budget_cap("some/model"),
        )

    assert result == ""
    assert calls == []  # kein stiller identischer Zweit-Request
    assert any("blockiert" in r.getMessage() for r in caplog.records)


def test_openrouter_query_uses_effective_cap(monkeypatch):
    """OpenRouter-Verdrahtung reicht den WIRKSAMEN Cap (nicht nur den Card-Cap)
    an die Leiter durch — der Session-110-Bug (Override unsichtbar) ist behoben."""
    conn = object.__new__(OpenRouterClient)
    conn._client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **k: "resp")),
    )
    conn.last_response_metadata = {
        "finish_reason": "length",
        "token_limit_used": 20000,
        "think_content": "x",
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
        conn, "_get_provider_cfg",
        lambda: {"max_tokens": 32768, "model_max_tokens": {"z-ai/glm-5.3": 24000}},
    )
    monkeypatch.setattr(
        "utils.model_thinking._read_max_output_tokens_from_card", lambda m: None,
    )
    captured: dict = {}

    def _fake_reask(**kwargs):
        captured.update(kwargs)
        return "ESKALIERT"

    monkeypatch.setattr(conn, "_maybe_reask_reasoning_truncation", _fake_reask)

    conn.query(model="z-ai/glm-5.3", prompt="P", temperature=1.0, stream_handler=None)

    # Wirksamer Cap = Override 24000 (nicht Provider-Default 32768, nicht nur Card-Cap)
    assert captured["budget_cap"] == 24000
