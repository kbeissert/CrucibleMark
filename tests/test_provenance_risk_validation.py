"""
Test für weights_provenance_risk Auto-Validierung.

Regel 1: proprietary + origin_country=(USA|China) → Risk ≥ "medium"
Regel 2: open-weights + origin_country=(USA|China) + deployment_type=cloud-only → Risk ≥ "medium"

Hintergrund: CLOUD Act (USA), Cyber Security Law (China) ermöglichen Datenzugriff.
"""

from pathlib import Path

from scripts.dev.validate_model_cards import check_card


def test_provenance_risk_proprietary_usa_low_triggers_error() -> None:
    """Proprietary USA-Modell mit risk='low' muss Fehler werfen."""
    data = {
        "model_id": "test-model",
        "display_name": "Test Model",
        "weights_license_tier": "proprietary",
        "license": "Proprietary",
        "commercial_use_allowed": True,
        "use_case_primary": "general",
        "parameter_architecture": "dense",
        "origin_country": "USA",
        "weights_provenance_risk": "low",
    }
    issues = check_card(Path("test.json"), data)

    # Muss Fehler enthalten
    assert any("[PROVENANCE RISK]" in issue for issue in issues), \
        f"Erwartet [PROVENANCE RISK] Fehler, bekommen: {issues}"
    assert any("USA" in issue for issue in issues)


def test_provenance_risk_proprietary_china_low_triggers_error() -> None:
    """Proprietary China-Modell mit risk='low' muss Fehler werfen."""
    data = {
        "model_id": "test-model",
        "display_name": "Test Model",
        "weights_license_tier": "proprietary",
        "license": "Proprietary",
        "commercial_use_allowed": True,
        "use_case_primary": "general",
        "parameter_architecture": "dense",
        "origin_country": "China",
        "weights_provenance_risk": "low",
    }
    issues = check_card(Path("test.json"), data)

    assert any("[PROVENANCE RISK]" in issue for issue in issues)
    assert any("China" in issue for issue in issues)


def test_provenance_risk_proprietary_usa_medium_ok() -> None:
    """Proprietary USA-Modell mit risk='medium' ist OK."""
    data = {
        "model_id": "test-model",
        "display_name": "Test Model",
        "weights_license_tier": "proprietary",
        "license": "Proprietary",
        "commercial_use_allowed": True,
        "use_case_primary": "general",
        "parameter_architecture": "dense",
        "origin_country": "USA",
        "weights_provenance_risk": "medium",
    }
    issues = check_card(Path("test.json"), data)

    # Keine PROVENANCE RISK Fehler
    assert not any("[PROVENANCE RISK]" in issue for issue in issues), \
        f"Keine Provenance-Fehler erwartet, bekommen: {issues}"


def test_provenance_risk_proprietary_usa_high_ok() -> None:
    """Proprietary USA-Modell mit risk='high' ist OK."""
    data = {
        "model_id": "test-model",
        "display_name": "Test Model",
        "weights_license_tier": "proprietary",
        "license": "Proprietary",
        "commercial_use_allowed": True,
        "use_case_primary": "general",
        "parameter_architecture": "dense",
        "origin_country": "USA",
        "weights_provenance_risk": "high",
    }
    issues = check_card(Path("test.json"), data)

    assert not any("[PROVENANCE RISK]" in issue for issue in issues)


def test_provenance_risk_proprietary_eu_low_ok() -> None:
    """Proprietary EU-Modell mit risk='low' ist OK (kein CLOUD Act)."""
    data = {
        "model_id": "test-model",
        "display_name": "Test Model",
        "weights_license_tier": "proprietary",
        "license": "Proprietary",
        "commercial_use_allowed": True,
        "use_case_primary": "general",
        "parameter_architecture": "dense",
        "origin_country": "France",
        "weights_provenance_risk": "low",
    }
    issues = check_card(Path("test.json"), data)

    assert not any("[PROVENANCE RISK]" in issue for issue in issues)


def test_provenance_risk_open_weights_cloud_only_usa_low_triggers_error() -> None:
    """Open-Weights Cloud-Only USA-Modell mit risk='low' muss Fehler werfen."""
    data = {
        "model_id": "test-model",
        "display_name": "Test Model",
        "weights_license_tier": "open-weights",
        "license": "Apache 2.0",
        "commercial_use_allowed": True,
        "use_case_primary": "general",
        "parameter_architecture": "dense",
        "origin_country": "USA",
        "deployment_type": "cloud-only",
        "weights_provenance_risk": "low",
    }
    issues = check_card(Path("test.json"), data)

    assert any("[PROVENANCE RISK]" in issue for issue in issues)
    assert any("cloud-only" in issue for issue in issues)


def test_provenance_risk_open_weights_local_usa_low_ok() -> None:
    """Open-Weights Local-Runnable USA-Modell mit risk='low' ist OK."""
    data = {
        "model_id": "test-model",
        "display_name": "Test Model",
        "weights_license_tier": "open-weights",
        "license": "Apache 2.0",
        "commercial_use_allowed": True,
        "use_case_primary": "general",
        "parameter_architecture": "dense",
        "origin_country": "USA",
        "deployment_type": "local-runnable",
        "weights_provenance_risk": "low",
    }
    issues = check_card(Path("test.json"), data)

    # Keine PROVENANCE RISK Fehler (local-runnable → kein CLOUD Act-Zugriff)
    assert not any("[PROVENANCE RISK]" in issue for issue in issues)


def test_provenance_risk_missing_fields_no_crash() -> None:
    """Fehlende Felder dürfen nicht zum Crash führen."""
    data = {
        "model_id": "test-model",
        "display_name": "Test Model",
        "weights_license_tier": "proprietary",
        "license": "Proprietary",
        "commercial_use_allowed": True,
        "use_case_primary": "general",
        "parameter_architecture": "dense",
        # origin_country, weights_provenance_risk fehlen
    }
    issues = check_card(Path("test.json"), data)

    # Keine PROVENANCE RISK Fehler bei fehlenden Feldern
    assert not any("[PROVENANCE RISK]" in issue for issue in issues)
