"""Regressionstests für die Card-Naming SSoT: SUFFIX-Form ``{base}--{shortcode}.json``.

Hintergrund (Session 49, 2026-07-07):
    ``build_card_id()`` und ``_card_path(for_write=True)`` produzierten
    unterschiedliche Formen (SUFFIX vs PREFIX), was zu Duplikat-Karten führte.
    Seit diesem Fix ist SUFFIX die alleinige SSoT — beide Funktionen
    produzieren ``{base}--{shortcode}.json``.

Diese Tests sichern ab:
    1. ``_card_path(for_write=True, provider=X)`` produziert SUFFIX, nicht PREFIX.
    2. ``_find_card`` findet SUFFIX-Karten vor PREFIX-Legacy-Karten.
    3. ``_find_card`` findet PREFIX-Legacy-Karten als Fallback (backward-compat).
    4. ``_card_path`` und ``build_card_id`` sind konsistent.
"""
from __future__ import annotations

from pathlib import Path

import pytest

import utils.model_utils
import utils.model_card_io as model_card_io_module
from utils.model_utils import _card_path, _find_card, build_card_id


@pytest.fixture
def isolated_card_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Biegt CARD_DIR auf tmp_path um."""
    card_dir = tmp_path / "cards"
    card_dir.mkdir()
    monkeypatch.setattr(utils.model_utils, "CARD_DIR", card_dir)
    monkeypatch.setattr(model_card_io_module, "CARD_DIR", card_dir)
    return card_dir


# ---------------------------------------------------------------------------
# 1. _card_path(for_write=True) produziert SUFFIX
# ---------------------------------------------------------------------------


class TestCardPathWriteProducesSuffix:
    """``_card_path(for_write=True, provider=X)`` muss SUFFIX-Form produzieren."""

    @pytest.mark.parametrize(
        ("model_id", "provider", "shortcode"),
        [
            ("Gemma-4-26B", "vllm_spark", "VSPK"),
            ("gemma3:9b", "llamacpp_spark", "SPRK"),
            ("llama3.3:70b", "ollama_local", "LCL"),
            ("qwen3.5-35b-a3b-q4", "llamacpp", "M4APL"),
        ],
    )
    def test_write_path_is_suffix(
        self,
        isolated_card_dir: Path,
        model_id: str,
        provider: str,
        shortcode: str,
    ) -> None:
        result = _card_path(model_id, provider=provider, for_write=True)
        safe = model_id.replace(":", "_").replace(".", "_").replace(" ", "_")
        expected_name = f"{safe}--{shortcode}.json"
        assert result.name == expected_name, (
            f"_card_path(for_write=True) must produce SUFFIX form, got {result.name!r}"
        )

    def test_write_path_never_produces_prefix(self, isolated_card_dir: Path) -> None:
        """Regression: PREFIX-Form ({shortcode}_{safe}.json) darf NICHT mehr produziert werden."""
        result = _card_path("test-model", provider="vllm_spark", for_write=True)
        assert not result.name.startswith("VSPK_"), (
            f"PREFIX form detected: {result.name!r} — _card_path must use SUFFIX"
        )

    def test_write_path_without_provider_is_unprefixed(self, isolated_card_dir: Path) -> None:
        """Ohne provider bleibt die Form unprefixed (API/default)."""
        result = _card_path("claude-sonnet-4-6", for_write=True)
        assert result.name == "claude-sonnet-4-6.json"


# ---------------------------------------------------------------------------
# 2. _find_card Read-Reihenfolge: SUFFIX first, dann PREFIX (legacy), dann unprefixed
# ---------------------------------------------------------------------------


class TestFindCardReadOrder:
    """``_find_card`` muss SUFFIX-Karten priorisieren über PREFIX-Legacy."""

    def test_suffix_found_first(self, isolated_card_dir: Path) -> None:
        """Wenn sowohl SUFFIX als auch PREFIX existieren, gewinnt SUFFIX."""
        safe = "test-model"
        suffix_path = isolated_card_dir / f"{safe}--VSPK.json"
        prefix_path = isolated_card_dir / f"VSPK_{safe}.json"
        suffix_path.write_text("{}", encoding="utf-8")
        prefix_path.write_text("{}", encoding="utf-8")

        result = _find_card("test-model", card_dir=isolated_card_dir)
        assert result == suffix_path, f"SUFFIX must be found first, got {result.name!r}"

    def test_legacy_prefix_still_found(self, isolated_card_dir: Path) -> None:
        """PREFIX-Legacy-Karten werden noch gefunden (backward-compat)."""
        prefix_path = isolated_card_dir / "VSPK_test-model.json"
        prefix_path.write_text("{}", encoding="utf-8")

        result = _find_card("test-model", card_dir=isolated_card_dir)
        assert result == prefix_path, f"Legacy PREFIX must still be found, got {result.name!r}"

    def test_unprefixed_fallback(self, isolated_card_dir: Path) -> None:
        """Wenn weder SUFFIX noch PREFIX existieren, fällt _find_card auf unprefixed zurück."""
        result = _find_card("test-model", card_dir=isolated_card_dir)
        assert result.name == "test-model.json"
        assert not result.exists()  # caller must check .exists()


# ---------------------------------------------------------------------------
# 3. SSoT-Konsistenz: _card_path und build_card_id
# ---------------------------------------------------------------------------


class TestCardPathBuildCardIdConsistency:
    """``_card_path(for_write=True)`` und ``build_card_id`` müssen dieselbe Form produzieren."""

    @pytest.mark.parametrize(
        ("model_id", "provider"),
        [
            ("Gemma-4-26B", "vllm_spark"),
            ("gemma3:9b", "llamacpp_spark"),
            ("qwen3.5-9b", "llamacpp_spark"),
        ],
    )
    def test_card_path_matches_build_card_id(
        self,
        isolated_card_dir: Path,
        model_id: str,
        provider: str,
    ) -> None:
        """Der Dateiname aus _card_path muss build_card_id + .json entsprechen."""
        built_id = build_card_id(model_id, provider)
        # _safe_name wird auf den built_id angewendet für den Dateinamen
        from utils.model_utils import _safe_name
        expected_filename = f"{_safe_name(built_id)}.json"

        result = _card_path(model_id, provider=provider, for_write=True)
        assert result.name == expected_filename, (
            f"_card_path produces {result.name!r}, but build_card_id + _safe_name "
            f"produces {expected_filename!r} — SSoT mismatch"
        )
