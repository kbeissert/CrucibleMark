"""v4.7.7: Web-Exporter Card-Field-Coverage-Tests.

Prueft, dass alle Felder der standardisierten Model-Cards, die laut
card_template_model.yaml als web_export-consumer markiert sind, auch
tatsaechlich im `model_card` sub-dict der data.json landen.

Regression-Schutz fuer den Audit 2026-06-10 (siehe
outputs/audits/web_export_compatibility_2026-06-10.md), der 8 fehlende
Felder identifiziert hatte.
"""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.web_export import _build_leaderboard_entry, _strip_none  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "config" / "card_template_model.yaml"


# ---------------------------------------------------------------------------
# Helper: SSoT-Template-Felder mit consumers: [web_export, ...]
# ---------------------------------------------------------------------------

def _load_web_export_consumer_fields() -> set[str]:
    """Liest config/card_template_model.yaml und sammelt alle Felder (required
    + optional), die web_export als Consumer haben UND im Export immer vorhanden
    sein muessen.

    Ausnahme: cot_marker_family / cot_tags_detected sind conditional (nur wenn
    in der Card gesetzt — Sonde schreibt sie nur bei detektiertem CoT).
    """
    _CONDITIONAL = {"cot_marker_family", "cot_tags_detected"}
    with TEMPLATE_PATH.open(encoding="utf-8") as f:
        tmpl = yaml.safe_load(f)
    fields: set[str] = set()
    for group in ("required_fields", "optional_fields"):
        for spec in tmpl.get(group, []):
            if "web_export" in (spec.get("consumers") or []):
                if spec["name"] not in _CONDITIONAL:
                    fields.add(spec["name"])
    return fields


def _load_all_required_template_fields() -> set[str]:
    """Alle required_fields laut Template (fuer self-contained sub-dict Check)."""
    with TEMPLATE_PATH.open(encoding="utf-8") as f:
        tmpl = yaml.safe_load(f)
    return {spec["name"] for spec in tmpl.get("required_fields", [])}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_card() -> dict:
    """Vollstaendige Card mit allen Template-Pflichtfeldern."""
    return {
        "model_id": "test-model-7b",
        "model_version": "7",
        "unknown": False,
        "display_name": "Test Model 7B",
        "developer": "TestCorp",
        "origin_country": "USA",
        "developer_jurisdiction": "US",
        "deployment_type": "open-weights",
        "local_deployment_possible": True,
        "weights_provenance_risk": "low",
        "weights_provenance_risk_rationale": "Open-source release on HuggingFace.",
        "vendor": "TestCorp",
        "architecture_tags": ["General", "Instruct"],
        "primary_focus": "general",
        "thinking_probe_detected": False,
        "thinking_probe_confidence": "low",
        "thinking_probe_evidence": "No CoT signals found.",
        "thinking_probe_manual_override": False,
        "thinking_probe_at": "2026-05-01T12:00:00+00:00",
        "model_family": "Test",
        "use_case_primary": "generalist",
        "parameter_architecture": "dense",
        "params_total_b": 7.0,
        "params_active_b": 7.0,
        "context_window_k": 32,
        "knowledge_cutoff": "2025-09",
        "input_modalities": ["text", "image"],
        "output_modalities": ["text"],
        "summary": "Test-Model ist ein kompaktes 7B-Generalsmodell.",
        "judge_context_hint": "Modell ist auf Standardfaelle optimiert.",
        "strengths": ["Schnell", "Kosteneffizient"],
        "known_limitations": ["Schwacher Code"],
        "card_status": "complete",
        "generated_at": "2026-05-01T12:00:00+00:00",
        "license": "Apache 2.0",
        "license_url": "https://example.com/license",
        "commercial_use_allowed": True,
        "weights_license_tier": "open-weights",
        "input_price_per_1m": 0.0,
        "output_price_per_1m": 0.0,
        "supports_tool_use": True,
        "size_class": "Desktop",
        "community": "TestCommunity",
        "profile_verified": True,
        "profile_verified_at": "2026-06-20",
        "profile_verified_by": "card-research",
        "last_modified_at": "2026-06-20",
        # v4.10.14: Quant/Variant-Separierung (model_version = reine Versionsnummer)
        "quantization_format": "Q8_0 GGUF",
        "model_variant": "MTP",
        # Optional v4.7.1: hier ungesetzt (kein Probe-Quartett)
    }


@pytest.fixture
def sample_row() -> pd.Series:
    """Minimaler Leaderboard-CSV-Row (pd.Series) fuer _build_leaderboard_entry."""
    return pd.Series({
        "Model Name": "Test Model 7B",
        "Model ID": "test-model-7b",
        "model_id_raw": "test-model-7b",
        "Version": "7",
        "Provider Code": "API",
        "Badge": "Silver",
        "Speed Profile": "Real-Time",
        "Performance Tier": "Standard",
        "Total Score": 65.0,
        "Routine Score": 40.0,
        "Reasoning Score": 25.0,
        "Tokens/s": 100.0,
        "Avg Task Duration (s)": 5.0,
        "P95 Time (s)": 12.0,
        "Max Time (s)": 15.0,
        "Timeout Count": 0,
        "Tokens Total": "30K",
        "Cost per 1K (USD)": 0.0,
        "Benchmark Cost (USD)": 0.0,
        "LLM Judge Avg (raw)": 3.5,
        "LLM Judge Coverage": "100%",
        "Tests Run": "43/43",
        "Size Class": "Medium",
        "Type": "Offen",
    })


# ---------------------------------------------------------------------------
# Test 1: Alle Template-Pflichtfelder landen im sub-dict (self-contained)
# ---------------------------------------------------------------------------

def test_model_card_subdict_covers_all_required_template_fields(sample_card, sample_row) -> None:
    """Sicherstellt: alle 38 Template-Pflichtfelder sind im model_card sub-dict."""
    entry = _build_leaderboard_entry(
        row=sample_row,
        card=sample_card,
        slug="test-model-7b",
        vendor="TestCorp",
        thinking_mode="standard",
        model_type="Offen",
        has_report=True,
        has_review=True,
        review_published_at="2026-05-01",
        review_updated_at=None,
        benchmark_run_at="2026-05-01",
        inference_provider="TestCorp",
    )
    sub = entry["model_card"]
    assert sub is not None

    required = _load_all_required_template_fields()
    actual = set(sub.keys())
    missing = required - actual
    assert not missing, f"Pflichtfelder fehlen im model_card sub-dict: {sorted(missing)}"


# ---------------------------------------------------------------------------
# Test 2: Alle web_export-consumer-Felder landen im sub-dict
# ---------------------------------------------------------------------------

def test_model_card_subdict_covers_all_web_export_consumer_fields(sample_card, sample_row) -> None:
    """Sicherstellt: alle Felder mit consumers: [web_export, ...] sind enthalten."""
    entry = _build_leaderboard_entry(
        row=sample_row,
        card=sample_card,
        slug="test-model-7b",
        vendor="TestCorp",
        thinking_mode="standard",
        model_type="Offen",
        has_report=True,
        has_review=True,
        review_published_at="2026-05-01",
        review_updated_at=None,
        benchmark_run_at="2026-05-01",
        inference_provider="TestCorp",
        community="TestCommunity",
    )
    sub = entry["model_card"]
    assert sub is not None

    expected = _load_web_export_consumer_fields()
    actual = set(sub.keys())
    missing = expected - actual
    assert not missing, (
        f"web_export-consumer-Felder fehlen im model_card sub-dict: {sorted(missing)}"
    )


# ---------------------------------------------------------------------------
# Test 3: Kritische Modalitaeten (input_modalities / output_modalities) korrekt
# ---------------------------------------------------------------------------

def test_model_card_subdict_exposes_modalities(sample_card, sample_row) -> None:
    """input_modalities / output_modalities (v4.7.0) muessen 1:1 aus der Card kommen."""
    sample_card["input_modalities"] = ["text", "image", "audio"]
    sample_card["output_modalities"] = ["text", "audio"]

    entry = _build_leaderboard_entry(
        row=sample_row, card=sample_card, slug="t", vendor="v",
        thinking_mode="standard", model_type="Offen",
        has_report=False, has_review=False,
        review_published_at=None, review_updated_at=None,
        benchmark_run_at=None, inference_provider=None,
    )
    sub = entry["model_card"]
    assert sub["input_modalities"] == ["text", "image", "audio"]
    assert sub["output_modalities"] == ["text", "audio"]


# ---------------------------------------------------------------------------
# Test 4: Pflicht-Tri-State-Felder korrekt durchgereicht
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field", [
    "judge_context_hint",
    "primary_focus",
    "unknown",
    "generated_at",
    "model_id",
    "model_version",
])
def test_model_card_subdict_passes_through_required_text_fields(field, sample_card, sample_row) -> None:
    """Text-Felder muessen unveraendert durchgereicht werden (kein Normalisierungs-Bug)."""
    sample_card[field] = f"TEST_VALUE_FOR_{field}"

    entry = _build_leaderboard_entry(
        row=sample_row, card=sample_card, slug="t", vendor="v",
        thinking_mode="standard", model_type="Offen",
        has_report=False, has_review=False,
        review_published_at=None, review_updated_at=None,
        benchmark_run_at=None, inference_provider=None,
    )
    assert entry["model_card"][field] == f"TEST_VALUE_FOR_{field}"


# ---------------------------------------------------------------------------
# Test 4b (v4.10.14): Quant/Variant-Separierung — Pass-Through + None-Stripping
# ---------------------------------------------------------------------------

def test_model_card_passes_through_quant_and_variant(sample_card, sample_row) -> None:
    """v4.10.14: quantization_format + model_variant muessen 1:1 aus der Card
    kommen. Regressionsschutz fuer die model_version-Pollution-Migration, die
    Quant/Variant-Tokens aus model_version in diese Felder ausgelagert hat."""
    entry = _build_leaderboard_entry(
        row=sample_row, card=sample_card, slug="t", vendor="v",
        thinking_mode="standard", model_type="Offen",
        has_report=False, has_review=False,
        review_published_at=None, review_updated_at=None,
        benchmark_run_at=None, inference_provider=None,
    )
    sub = entry["model_card"]
    assert sub["quantization_format"] == "Q8_0 GGUF"
    assert sub["model_variant"] == "MTP"
    # model_version bleibt reine Versionsnummer (kein Quant-Token mehr)
    assert sub["model_version"] == "7"


def test_model_card_strips_none_quant_for_cloud_models(sample_card, sample_row) -> None:
    """Cloud/Commercial-Modelle ohne Quantisierung: quantization_format=None
    darf NICHT als null im Export landen (_strip_none entfernt den Key)."""
    sample_card["quantization_format"] = None
    sample_card["model_variant"] = None

    entry = _build_leaderboard_entry(
        row=sample_row, card=sample_card, slug="t", vendor="v",
        thinking_mode="standard", model_type="Proprietär",
        has_report=False, has_review=False,
        review_published_at=None, review_updated_at=None,
        benchmark_run_at=None, inference_provider=None,
    )
    sub = entry["model_card"]
    assert "quantization_format" not in sub, "None-Quant darf nicht als null exportiert werden"
    assert "model_variant" not in sub, "None-Variant darf nicht als null exportiert werden"


# ---------------------------------------------------------------------------
# Test 5: None-Card bleibt model_card: None (kein Crash, keine leere Dict)
# ---------------------------------------------------------------------------

def test_model_card_is_none_when_card_missing(sample_row) -> None:
    """Wenn load_model_card() None liefert, wird model_card komplett entfernt (kein null im JSON)."""
    entry = _build_leaderboard_entry(
        row=sample_row, card=None, slug="missing", vendor=None,
        thinking_mode="standard", model_type="Proprietär",
        has_report=False, has_review=False,
        review_published_at=None, review_updated_at=None,
        benchmark_run_at=None, inference_provider=None,
    )
    assert "model_card" not in entry


# ---------------------------------------------------------------------------
# Test 6: Card-Lookup hat sich nicht verschoben (Regression-Schutz)
# ---------------------------------------------------------------------------

def test_real_export_data_json_contains_all_required_fields() -> None:
    """Integrations-Check: nach make web_export enthaelt jede data.json alle
    8 neu hinzugefuegten Pflichtfelder im model_card sub-dict.

    Voraussetzung: outputs/web_export_check/raw/models/ ist aus einem frischen
    Export (vom Test-Setup oder manuell via `make web-export`).
    """
    base = ROOT / "outputs" / "web_export_check" / "raw" / "models"
    if not base.exists():
        pytest.skip("Kein Web-Export vorhanden (outputs/web_export_check/raw/models/)")
    data_files = list(base.glob("*/data.json"))
    if not data_files:
        pytest.skip("Keine data.json-Dateien im Web-Export-Output")

    required = _load_all_required_template_fields()
    failed: list[tuple[str, set[str]]] = []

    for df in data_files:
        data = json.loads(df.read_text(encoding="utf-8"))
        sub = data.get("leaderboard", {}).get("model_card")
        if sub is None:
            continue  # Modelle ohne Card sind erlaubt (z.B. gpt-5_4)
        missing = required - set(sub.keys())
        if missing:
            failed.append((df.parent.name, missing))

    assert not failed, (
        "Folgende Modelle haben unvollstaendige model_card sub-dicts: "
        + ", ".join(f"{slug}:{sorted(m)}" for slug, m in failed[:5])
    )


# ---------------------------------------------------------------------------
# Test 5: None-Werte werden aus dem Export entfernt
# ---------------------------------------------------------------------------

def test_model_card_strips_none_values(sample_card, sample_row) -> None:
    """None-Werte duerfen NICHT im Web-Export landen (Nullwert-Entfernung)."""
    sample_card["params_active_b"] = None
    sample_card["knowledge_cutoff"] = None
    sample_card["license_url"] = None

    entry = _build_leaderboard_entry(
        row=sample_row,
        card=sample_card,
        slug="test-model-7b",
        vendor="TestCorp",
        thinking_mode="standard",
        model_type="Offen",
        has_report=False,
        has_review=False,
        review_published_at=None,
        review_updated_at=None,
        benchmark_run_at=None,
        inference_provider=None,
    )
    sub = entry["model_card"]
    assert sub is not None

    none_keys = [k for k, v in sub.items() if v is None]
    assert not none_keys, f"None-Werte im model_card sub-dict: {none_keys}"

    assert "params_active_b" not in sub
    assert "knowledge_cutoff" not in sub
    assert "license_url" not in sub
    assert "params_total_b" in sub  # Hat Wert → bleibt


# ---------------------------------------------------------------------------
# Test 6: _strip_none Unit-Tests
# ---------------------------------------------------------------------------

def test_strip_none_removes_none_values():
    assert _strip_none({"a": 1, "b": None, "c": "x"}) == {"a": 1, "c": "x"}

def test_strip_none_preserves_false_and_zero():
    assert _strip_none({"a": 0, "b": False, "c": "", "d": []}) == {"a": 0, "b": False, "c": "", "d": []}

def test_strip_none_nested():
    data = {"outer": {"inner": None, "keep": 42}, "list": [1, None, 3]}
    result = _strip_none(data)
    assert result == {"outer": {"keep": 42}, "list": [1, None, 3]}

def test_strip_none_returns_non_dict_unchanged():
    assert _strip_none(None) is None
    assert _strip_none([1, 2]) == [1, 2]
    assert _strip_none("hello") == "hello"
