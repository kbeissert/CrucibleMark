"""Regressionstests für scripts/tools/probe_thinking.py.

Abgedeckte Bugfixes:
- Fix 1: ``_load_config`` merged ``config/provider_config.yaml`` (SCSS-Partial-
  Prinzip). Ohne Merge fehlt ``vllm_spark``-Config → ``base_url`` defaultet
  auf ``127.0.0.1`` → Probe hält endlos im Cold-Start-Wait fest.
- Fix 2: ``_write_probe_to_card`` aktualisiert bestehende SUFFIX-Cards
  (``--VSPK``/``--SPRK``) in place via ``_find_card`` + ``ensure_card(card_path=)``
  statt ein unprefixed Duplikat oder eine ``-2``-Kollisionsvariante anzulegen.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from utils import model_utils as model_utils_module
import utils.model_card_io as model_card_io_module
from utils.card_utils import ensure_card
from utils.model_utils import ThinkingProbeResult, _find_card

# Modul-Lazy-Import: probe_thinking importiert transitive utils.* zur Laufzeit
ROOT_DIR = Path(__file__).resolve().parent.parent


class TestLoadConfigMergesProviderConfig:
    """Fix 1: _load_config muss provider_config.yaml einblenden."""

    def test_vllm_spark_config_present_after_merge(self) -> None:
        from scripts.tools.probe_thinking import _load_config

        cfg = _load_config()
        vllm = cfg.get("providers", {}).get("local", {}).get("vllm_spark", {})
        assert vllm, "vllm_spark-Provider fehlt — provider_config.yaml nicht gemerged"
        assert "base_url" in vllm, "base_url fehlt in vllm_spark-Config"
        assert vllm["base_url"] != "", "base_url ist leer"
        # server_start_cmd muss vorhanden sein (SSH-Wrapper für vllm-start)
        assert vllm.get("server_start_cmd"), "server_start_cmd fehlt"


class TestWriteProbeToCardSuffixSsot:
    """Fix 2: bestehende SUFFIX-Cards in place aktualisieren, keine Duplikate."""

    @pytest.fixture
    def isolated_card_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        """Biegt CARD_DIR auf tmp_path um (wie test_card_path_suffix_ssot)."""
        card_dir = tmp_path / "cards"
        card_dir.mkdir()
        monkeypatch.setattr(model_utils_module, "CARD_DIR", card_dir)
        monkeypatch.setattr(model_card_io_module, "CARD_DIR", card_dir)
        return card_dir

    @staticmethod
    def _mock_probe() -> ThinkingProbeResult:
        return ThinkingProbeResult(
            detected=True,
            evidence="mock probe evidence",
            confidence="medium",
            prompts_used=("math",),
            tags_found=(),
        )

    def test_updates_existing_suffix_card_in_place(
        self, isolated_card_dir: Path
    ) -> None:
        """Bestehende --VSPK-Card wird aktualisiert, kein Duplikat, kein -2-Suffix."""
        from scripts.tools.probe_thinking import _write_probe_to_card

        # Bestehende SUFFIX-Card anlegen (simuliert qwen3_6-27B--VSPK.json)
        ensure_card("qwen3_6-27B", provider="vllm_spark")
        suffix_card = _find_card("qwen3_6-27B")
        assert suffix_card.exists()
        assert "--VSPK" in suffix_card.name

        before = sorted(p.name for p in isolated_card_dir.glob("*.json"))

        written = _write_probe_to_card(
            "qwen3_6-27B", self._mock_probe(), provider="vllm_spark"
        )

        after = sorted(p.name for p in isolated_card_dir.glob("*.json"))

        # Geschrieben in die bestehende SUFFIX-Card (kein -2, kein unprefixed)
        assert written == suffix_card
        assert before == after, f"Duplikat entstanden: {after}"

    def test_no_unprefixed_duplicate_for_existing_suffix(
        self, isolated_card_dir: Path
    ) -> None:
        """Regression: ensure_card(provider=) allein erzeugt -2-Duplikat bei
        bestehender Card. _write_probe_to_card muss das verhindern."""
        from scripts.tools.probe_thinking import _write_probe_to_card

        ensure_card("qwen3_6-27B", provider="vllm_spark")

        _write_probe_to_card(
            "qwen3_6-27B", self._mock_probe(), provider="vllm_spark"
        )

        cards = sorted(p.name for p in isolated_card_dir.glob("*.json"))
        # Genau eine Card, SUFFIX-Form, kein -2
        assert len(cards) == 1
        assert not cards[0].endswith("-2.json")
        assert "--VSPK" in cards[0]

    def test_creates_suffix_card_when_missing(
        self, isolated_card_dir: Path
    ) -> None:
        """Fehlt die Card komplett, wird sie mit korrektem SUFFIX angelegt."""
        from scripts.tools.probe_thinking import _write_probe_to_card

        assert not _find_card("qwen3_6-27B").exists()

        written = _write_probe_to_card(
            "qwen3_6-27B", self._mock_probe(), provider="vllm_spark"
        )

        assert written.exists()
        assert "--VSPK" in written.name
