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

from scripts.web_export import _build_leaderboard_entry  # noqa: E402

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
        "params_active_b": None,
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
# Test 5: None-Card bleibt model_card: None (kein Crash, keine leere Dict)
# ---------------------------------------------------------------------------

def test_model_card_is_none_when_card_missing(sample_row) -> None:
    """Wenn load_model_card() None liefert, ist model_card: None (kein leeres Dict)."""
    entry = _build_leaderboard_entry(
        row=sample_row, card=None, slug="missing", vendor=None,
        thinking_mode="standard", model_type="Proprietär",
        has_report=False, has_review=False,
        review_published_at=None, review_updated_at=None,
        benchmark_run_at=None, inference_provider=None,
    )
    assert entry["model_card"] is None


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
