"""
Tests fuer WEBEXP-009: Prober schreibt cot_marker_family / cot_tags_detected.

Abdeckung:
  - classify_cot_marker_family() Heuristik (alle Familien + 'none')
  - _probe_fields_to_dict() aus scripts/tools/probe_thinking.py schreibt
    cot_marker_family + cot_tags_detected nur bei tags_found != ()
  - Bestehende Tests (z. B. fuer ThinkingProbeResult) bleiben unberuehrt
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from utils.model_utils import (
    ThinkingProbeResult,
    classify_cot_marker_family,
)


# ---------------------------------------------------------------------------
# classify_cot_marker_family — Heuristik
# ---------------------------------------------------------------------------

class TestClassifyCotMarkerFamily:
    """Prueft alle Familien-Mappings + Edge-Cases."""

    @pytest.mark.parametrize(
        "tags,expected",
        [
            # Qwen-Think / OpenAI-OSS / DeepSeek-Familie
            (("<think>",), "think-xml"),
            (("<thought>",), "think-xml"),
            (("<|thinking|>",), "openai-oss"),
            (("<|reasoning|>",), "openai-oss"),
            (("<reasoning>",), "deepseek-reasoning"),
            (("<reason>",), "deepseek-reasoning"),
            # Llama / Anthropic / Hermes / Mistral
            (("<reflection>",), "llama-cot"),
            (("<analysis>",), "anthropic-extended"),
            (("<plan>",), "anthropic-extended"),
            (("<scratchpad>",), "hermes-scratchpad"),
            (("<solution>",), "mistral-reasoning"),
            # GLM
            (("<thinking>",), "glm-cot"),
            # Generic
            (("<cot>",), "generic-cot"),
            # Edge-Cases
            ((), "none"),
            ([], "none"),
            (None, "none"),
            (("unbekannter-tag",), "none"),
            # Mehrere Tags: erster Match gewinnt (think-xml > glm-cot, da think-xml zuerst)
            (("<thinking>", "<think>"), "think-xml"),
        ],
    )
    def test_classify_cot_marker_family(self, tags, expected):
        assert classify_cot_marker_family(tags) == expected

    def test_classify_accepts_list_input(self):
        """Auch Python-list wird akzeptiert (nicht nur tuple)."""
        assert classify_cot_marker_family(["<think>"]) == "think-xml"

    def test_classify_case_insensitive(self):
        """Tags werden case-insensitive verarbeitet (lowercased)."""
        assert classify_cot_marker_family(["<THINK>"]) == "think-xml"


# ---------------------------------------------------------------------------
# _probe_fields_to_dict — schreibt CoT-Quartett nur bei tags_found
# ---------------------------------------------------------------------------

class TestProbeFieldsToDict:
    """Prueft, dass das CLI-Skript (probe_thinking.py) die richtigen Felder setzt."""

    def _call(self, probe: ThinkingProbeResult) -> dict:
        """Lazy-Import, weil probe_thinking.py ein CLI-Skript ist (kein Package)."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_probe_thinking_mod",
            Path(__file__).resolve().parent.parent
            / "scripts" / "tools" / "probe_thinking.py",
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod._probe_fields_to_dict(probe)

    def test_no_cot_fields_when_tags_empty(self):
        """Bei leeren tags_found bleiben CoT-Felder weg."""
        probe = ThinkingProbeResult(
            detected=False, evidence="...", confidence="low", tags_found=(),
        )
        fields = self._call(probe)
        assert fields["thinking_probe_detected"] is False
        assert fields["thinking_probe_confidence"] == "low"
        assert "thinking_probe_at" in fields
        assert "cot_marker_family" not in fields
        assert "cot_tags_detected" not in fields

    def test_cot_fields_written_when_tags_present(self):
        """Bei tags_found werden Familie + Tag-Liste geschrieben."""
        probe = ThinkingProbeResult(
            detected=True,
            evidence="...",
            confidence="high",
            tags_found=("<think>",),
        )
        fields = self._call(probe)
        assert fields["cot_marker_family"] == "think-xml"
        assert fields["cot_tags_detected"] == ["<think>"]

    def test_cot_fields_with_multiple_tags(self):
        """Mehrere Tags werden komplett gelistet (Heuristik waehlt Familie)."""
        probe = ThinkingProbeResult(
            detected=True,
            evidence="...",
            confidence="high",
            tags_found=("<think>", "<thought>"),
        )
        fields = self._call(probe)
        # think-xml gewinnt (steht zuerst in _COT_FAMILY_MAP, <think> + <thought> sind beide think-xml)
        assert fields["cot_marker_family"] == "think-xml"
        assert set(fields["cot_tags_detected"]) == {"<think>", "<thought>"}

    def test_cot_fields_unknown_family(self):
        """Unbekannte Tags -> cot_marker_family='none'."""
        probe = ThinkingProbeResult(
            detected=True,
            evidence="...",
            confidence="medium",
            tags_found=("<<unmapped>>",),
        )
        fields = self._call(probe)
        assert fields["cot_marker_family"] == "none"
        assert fields["cot_tags_detected"] == ["<<unmapped>>"]


# ---------------------------------------------------------------------------
# Unified-Runner Probe-Write-Pfad
# ---------------------------------------------------------------------------

class TestUnifiedRunnerProbeWrite:
    """Prueft, dass _write_probe_to_card das CoT-Quartett mitschreibt."""

    def _make_runner(self):
        """Minimale Runner-Instanz ohne __init__-Side-Effects."""
        from scripts.core import unified_runner as ur
        runner = ur.UnifiedBenchmarkRunner.__new__(ur.UnifiedBenchmarkRunner)
        return runner

    def test_write_probe_to_card_sets_cot_fields_when_tags_present(self, tmp_path):
        """Bei tags_found!=() werden cot_marker_family + cot_tags_detected gesetzt."""
        runner = self._make_runner()
        card_path = tmp_path / "test_model.json"
        card_path.write_text(
            json.dumps({"model_id": "test-model", "architecture_tags": []}),
            encoding="utf-8",
        )

        probe = ThinkingProbeResult(
            detected=True,
            evidence="think-tag found",
            confidence="high",
            tags_found=("<|thinking|>",),
        )

        # ensure_card() Mocks (sonst wuerde es an den echten CARD_DIR schreiben)
        with patch("scripts.core.unified_runner.ensure_card", return_value=card_path):
            runner._write_probe_to_card("test-model", card_path, probe, card_loaded=True)

        saved = json.loads(card_path.read_text(encoding="utf-8"))
        assert saved["cot_marker_family"] == "openai-oss"
        assert saved["cot_tags_detected"] == ["<|thinking|>"]
        assert saved["thinking_probe_detected"] is True
        assert "Thinking" in saved["architecture_tags"]

    def test_write_probe_to_card_skips_cot_fields_when_tags_empty(self, tmp_path):
        """Bei tags_found=() bleiben CoT-Felder weg (verhindert noise im Web-Export)."""
        runner = self._make_runner()
        card_path = tmp_path / "test_model.json"
        card_path.write_text(
            json.dumps({"model_id": "test-model", "architecture_tags": []}),
            encoding="utf-8",
        )

        probe = ThinkingProbeResult(
            detected=False,
            evidence="no signal",
            confidence="low",
            tags_found=(),
        )

        with patch("scripts.core.unified_runner.ensure_card", return_value=card_path):
            runner._write_probe_to_card("test-model", card_path, probe, card_loaded=True)

        saved = json.loads(card_path.read_text(encoding="utf-8"))
        assert "cot_marker_family" not in saved
        assert "cot_tags_detected" not in saved
        assert saved["thinking_probe_detected"] is False
        # architecture_tags bleibt unveraendert (kein Thinking-Tag)
        assert "Thinking" not in saved["architecture_tags"]
