"""
Tests for thinking_override resolution (Option C: Probe SSoT + Escape-Hatch).

API-Realität: ``resolve_effective_thinking`` erwartet die vollständige
Provider-Model-Config (z.B. aus ``config/provider_config.yaml → providers.X
.models[i]``). Der Override wird unter dem Key ``"thinking_override"`` erwartet.

Coverage:
  1. Kein Override, Card-Probe gesetzt → Card gewinnt
  2. Aktiver Override, Card-Probe gesetzt → Override gewinnt (Audit-Log)
  3. Abgelaufener Override (active_until in Vergangenheit) → Card gewinnt
  4. Kein Override, Card-Probe fehlt → (None, 'none')
  5. Override ohne reason → inaktiv (Pflichtfeld)
  6. Override ohne value → inaktiv
  7. Override mit active_until in Zukunft → aktiv
  8. Override mit active_until = naive datetime (kein tz) → wird UTC-konform
  9. Override mit ungültigem active_until → inaktiv
 10. Card mit thinking_probe_detected=null → Fallback auf (None, 'none')
"""

from datetime import datetime, timedelta, UTC

import pytest

from utils.model_utils import (
    _is_override_active,
    resolve_effective_thinking,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _card(detected=None, evidence: str | None = None) -> dict:
    return {
        "model_id": "test-model",
        "thinking_probe_detected": detected,
        "thinking_probe_evidence": evidence,
    }


def _model_cfg(thinking_override: dict | None) -> dict:
    """Provider-Model-Config (so wie sie in config/provider_config.yaml steht)."""
    cfg: dict = {"id": "test-model", "name": "Test Model"}
    if thinking_override is not None:
        cfg["thinking_override"] = thinking_override
    return cfg


# ---------------------------------------------------------------------------
# _is_override_active
# ---------------------------------------------------------------------------


def test_is_override_active_value_and_reason_only():
    """Aktiver Override ohne active_until (immer aktiv)."""
    assert _is_override_active({"value": False, "reason": "Cost-Benchmark"}) is True


def test_is_override_active_requires_value_bool():
    """Ohne 'value' oder mit nicht-bool 'value' ist der Override inaktiv."""
    assert _is_override_active({"reason": "x"}) is False
    assert _is_override_active({"value": "yes", "reason": "x"}) is False
    assert _is_override_active({"value": 1, "reason": "x"}) is False


def test_is_override_active_requires_reason():
    """'reason' ist Pflicht (Audit-Trail), Whitespace-only zählt als leer."""
    assert _is_override_active({"value": True}) is False
    assert _is_override_active({"value": True, "reason": ""}) is False
    assert _is_override_active({"value": True, "reason": "   "}) is False


def test_is_override_active_not_dict():
    """Nicht-dict → inaktiv (defensiv)."""
    assert _is_override_active(None) is False
    assert _is_override_active("not-a-dict") is False
    assert _is_override_active(True) is False


def test_is_override_active_future_expiry_active():
    """active_until in der Zukunft → Override ist aktiv."""
    now = datetime(2026, 6, 10, tzinfo=UTC)
    expiry = (now + timedelta(days=30)).isoformat()
    assert _is_override_active(
        {"value": False, "reason": "test", "active_until": expiry},
        now=now,
    ) is True


def test_is_override_active_past_expiry_inactive():
    """active_until in der Vergangenheit → Override ist abgelaufen."""
    now = datetime(2026, 6, 10, tzinfo=UTC)
    expiry = (now - timedelta(days=1)).isoformat()
    assert _is_override_active(
        {"value": False, "reason": "test", "active_until": expiry},
        now=now,
    ) is False


def test_is_override_active_exact_now_inactive():
    """Exakt-Gleichheit (now == expiry) → Override gilt als abgelaufen."""
    now = datetime(2026, 6, 10, 12, 0, 0, tzinfo=UTC)
    assert _is_override_active(
        {"value": True, "reason": "test", "active_until": now.isoformat()},
        now=now,
    ) is False


def test_is_override_active_naive_datetime_treated_as_utc():
    """Naive Datetime (kein tz) → wird als UTC interpretiert."""
    now = datetime(2026, 6, 10, 12, 0, 0, tzinfo=UTC)
    naive_expiry = "2026-07-10T12:00:00"
    assert _is_override_active(
        {"value": False, "reason": "test", "active_until": naive_expiry},
        now=now,
    ) is True


def test_is_override_active_invalid_iso_inactive():
    """Ungültiges active_until-Format → inaktiv (Fail-Safe)."""
    now = datetime(2026, 6, 10, tzinfo=UTC)
    assert _is_override_active(
        {"value": True, "reason": "test", "active_until": "not-a-date"},
        now=now,
    ) is False
    assert _is_override_active(
        {"value": True, "reason": "test", "active_until": 12345},
        now=now,
    ) is False


def test_is_override_active_z_suffix_accepted():
    """ISO-8601 mit Z-Suffix → korrekt geparst."""
    now = datetime(2026, 6, 10, tzinfo=UTC)
    expiry_z = "2026-07-10T12:00:00Z"
    assert _is_override_active(
        {"value": True, "reason": "test", "active_until": expiry_z},
        now=now,
    ) is True


# ---------------------------------------------------------------------------
# resolve_effective_thinking
# ---------------------------------------------------------------------------


def test_resolve_no_override_card_true():
    """Kein Override, Card-Probe=True → (True, 'card_probe')."""
    eff, src = resolve_effective_thinking(_card(detected=True))
    assert eff is True
    assert src == "card_probe"


def test_resolve_no_override_card_false():
    """Kein Override, Card-Probe=False → (False, 'card_probe')."""
    eff, src = resolve_effective_thinking(_card(detected=False))
    assert eff is False
    assert src == "card_probe"


def test_resolve_no_override_card_null():
    """Kein Override, Card-Probe=None → (None, 'none')."""
    eff, src = resolve_effective_thinking(_card(detected=None))
    assert eff is None
    assert src == "none"


def test_resolve_active_override_overrides_card_true():
    """Aktiver Override=True gewinnt gegen Card-Probe=False."""
    eff, src = resolve_effective_thinking(
        _card(detected=False),
        _model_cfg({"value": True, "reason": "A/B-Test"}),
    )
    assert eff is True
    assert src == "override"


def test_resolve_active_override_overrides_card_true_inverse():
    """Aktiver Override=False gewinnt gegen Card-Probe=True."""
    eff, src = resolve_effective_thinking(
        _card(detected=True),
        _model_cfg({"value": False, "reason": "Cost-Benchmark"}),
    )
    assert eff is False
    assert src == "override"


def test_resolve_expired_override_falls_back_to_card():
    """Abgelaufener Override (active_until in Vergangenheit) → Card gewinnt."""
    now = datetime(2026, 6, 10, tzinfo=UTC)
    expired = (now - timedelta(days=1)).isoformat()
    cfg = _model_cfg(
        {"value": False, "reason": "Cost-Benchmark (expired)", "active_until": expired},
    )
    eff, src = resolve_effective_thinking(
        _card(detected=True), cfg, now=now,
    )
    assert eff is True
    assert src == "card_probe"


def test_resolve_override_without_reason_inactive():
    """Override ohne 'reason' ist inaktiv → Card gewinnt."""
    cfg = _model_cfg({"value": False})  # kein reason
    eff, src = resolve_effective_thinking(_card(detected=True), cfg)
    assert eff is True
    assert src == "card_probe"


def test_resolve_override_without_value_inactive():
    """Override ohne 'value' ist inaktiv → Card gewinnt."""
    cfg = _model_cfg({"reason": "x"})  # kein value
    eff, src = resolve_effective_thinking(_card(detected=False), cfg)
    assert eff is False
    assert src == "card_probe"


def test_resolve_provider_model_cfg_none():
    """provider_model_cfg=None → kein Override-Pfad, nur Card."""
    eff, src = resolve_effective_thinking(
        _card(detected=True), provider_model_cfg=None,
    )
    assert eff is True
    assert src == "card_probe"


def test_resolve_provider_model_cfg_no_override_key():
    """provider_model_cfg ohne 'thinking_override'-Key → Card gewinnt."""
    cfg = {"id": "magistral-medium-latest", "name": "Magistral"}  # kein thinking_override
    eff, src = resolve_effective_thinking(_card(detected=False), cfg)
    assert eff is False
    assert src == "card_probe"


def test_resolve_provider_model_cfg_not_dict():
    """provider_model_cfg kein dict → wird ignoriert, Card gewinnt."""
    eff, src = resolve_effective_thinking(_card(detected=True), "not-a-dict")
    assert eff is True
    assert src == "card_probe"


def test_resolve_audit_log_includes_model_id(caplog):
    """Override-Anwendung wird mit model_id im Log dokumentiert (Audit-Trail)."""
    cfg = _model_cfg({"value": False, "reason": "A/B-Test"})
    with caplog.at_level("INFO"):
        resolve_effective_thinking(
            _card(detected=True),
            cfg,
            model_id="magistral-medium-latest",
        )
    assert any(
        "magistral-medium-latest" in record.message
        and "override active" in record.message
        for record in caplog.records
    )


def test_resolve_audit_log_falls_back_to_card_model_id(caplog):
    """Wenn model_id nicht explizit übergeben → Card.model_id wird genutzt."""
    cfg = _model_cfg({"value": True, "reason": "test"})
    card = _card(detected=False)
    card["model_id"] = "from-card"
    with caplog.at_level("INFO"):
        resolve_effective_thinking(card, cfg)
    assert any(
        "from-card" in record.message
        for record in caplog.records
    )


# ---------------------------------------------------------------------------
# Integration-Smoke: SSoT-Property (Spezifikation Option C)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "card_value,override_value,expected_eff,expected_src",
    [
        (True, None, True, "card_probe"),          # 1. Card gewinnt (kein Override)
        (False, None, False, "card_probe"),
        (True, False, False, "override"),          # 2. Override gewinnt
        (False, True, True, "override"),
        (None, None, None, "none"),                # 3. Nichts gesetzt
        (True, True, True, "override"),            # 4. Override=True, egal was Card sagt
        (False, False, False, "override"),         # 5. Override=False, egal was Card sagt
    ],
)
def test_ssot_resolution_matrix(card_value, override_value, expected_eff, expected_src):
    """Vollständige SSoT-Auflösungsmatrix (Card × Override)."""
    override = (
        {"value": override_value, "reason": "test"}
        if override_value is not None
        else None
    )
    eff, src = resolve_effective_thinking(
        _card(detected=card_value), _model_cfg(override),
    )
    assert (eff, src) == (expected_eff, expected_src)
