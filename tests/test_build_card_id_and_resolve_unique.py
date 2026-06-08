"""Tests fuer `build_card_id` und `resolve_unique_card_id` — neue ID-Pipeline
fuer Model Cards.

Score-Cache-Hardening Phase B: der Konflikt-Resolver garantiert, dass jede
neu generierte Card-Datei einen eindeutigen Namen traegt. Die Tests hier
sichern das ID-Schema und das Resolver-Verhalten ab.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from utils.model_utils import build_card_id, resolve_unique_card_id


# ---------------------------------------------------------------------------
# build_card_id
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "model_id,provider,expected",
    [
        # OpenRouter: Namespace wird abgeschnitten, Shortcode angehaengt
        ("qwen/qwen3.5-35b-a3b-q4", "openrouter", "qwen3.5-35b-a3b-q4--OR"),
        # Anthropic: Provider-Name statt "API"-Shortcode (lesbarer)
        ("claude-sonnet-4-5-20250929", "anthropic", "claude-sonnet-4-5-20250929--anthropic"),
        # Ollama: Local-Variante mit Shortcode
        ("gemma3:9b", "ollama", "gemma3:9b--LCL"),
        # llama.cpp Spark: SPRK-Shortcode
        ("gemma3:9b", "llamacpp_spark", "gemma3:9b--SPRK"),
        # hf.co/ Namespace wird NICHT abgeschnitten (kein '/' im 'cleanen' Sinn)
        # normalize_model_id ist hier nicht aktiv; build_card_id strippt nur den letzten '/'.
        ("NousResearch_Hermes-4-14B-GGUF:Q4_K_M", "ollama", "NousResearch_Hermes-4-14B-GGUF:Q4_K_M--LCL"),
        # Quantisierungs-Varianten
        ("qwen3.5-4b-q4", "llamacpp_spark", "qwen3.5-4b-q4--SPRK"),
        ("qwen3.5-4b-q6", "llamacpp_spark", "qwen3.5-4b-q6--SPRK"),
        ("qwen3.5-4b-q8", "llamacpp_spark", "qwen3.5-4b-q8--SPRK"),
        # OpenRouter free-tier
        ("qwen/qwen3.6-plus:free", "openrouter", "qwen3.6-plus:free--OR"),
    ],
)
def test_build_card_id_returns_expected_format(
    model_id: str, provider: str, expected: str
) -> None:
    """ID-Format: {model_base_nach_letztem_slash}--{shortcode/provider_name}."""
    assert build_card_id(model_id, provider) == expected


def test_build_card_id_without_provider_returns_base() -> None:
    """Ohne Provider wird nur der Model-Base-Name zurueckgegeben (kein Suffix)."""
    assert build_card_id("qwen2.5-coder-7b") == "qwen2.5-coder-7b"
    assert build_card_id("qwen/qwen3.5-4b-q4") == "qwen3.5-4b-q4"


@pytest.mark.parametrize("empty", ["", None])
def test_build_card_id_handles_empty_input(empty: object) -> None:
    """Leere/None-Eingabe wird unveraendert zurueckgegeben (kein Crash)."""
    assert build_card_id(empty) == empty  # type: ignore[arg-type]


def test_build_card_id_strips_only_last_slash() -> None:
    """Nur der LETZTE '/' wird als Namespace-Trenner behandelt."""
    # Doppel-Slashes (z. B. hf.co/Author/model) wuerden 'Author/model' als base
    # liefern — wir wollen aber den LETZTEN Slash-Strip anwenden, um den
    # eigentlichen Model-Namen zu extrahieren.
    assert build_card_id("foo/bar/baz", "anthropic") == "baz--anthropic"


# ---------------------------------------------------------------------------
# resolve_unique_card_id
# ---------------------------------------------------------------------------

def test_resolve_unique_card_id_no_conflict(tmp_path: Path) -> None:
    """Wenn die ID nicht existiert, wird sie unveraendert zurueckgegeben."""
    assert resolve_unique_card_id("new_model", card_dir=tmp_path) == "new_model"


def test_resolve_unique_card_id_single_conflict(tmp_path: Path) -> None:
    """Bei einem Konflikt wird ein Suffix '-2' angehaengt."""
    (tmp_path / "clash.json").write_text("{}", encoding="utf-8")
    result = resolve_unique_card_id("clash", card_dir=tmp_path)
    assert result == "clash-2"


def test_resolve_unique_card_id_multi_conflict(tmp_path: Path) -> None:
    """Bei mehreren Konflikten wird inkrementiert (-2, -3, ...)."""
    (tmp_path / "m.json").write_text("{}", encoding="utf-8")
    (tmp_path / "m-2.json").write_text("{}", encoding="utf-8")
    (tmp_path / "m-3.json").write_text("{}", encoding="utf-8")
    result = resolve_unique_card_id("m", card_dir=tmp_path)
    assert result == "m-4"


def test_resolve_unique_card_id_empty_input(tmp_path: Path) -> None:
    """Leere Eingabe wird unveraendert zurueckgegeben."""
    assert resolve_unique_card_id("", card_dir=tmp_path) == ""


def test_resolve_unique_card_id_logs_warning_on_conflict(tmp_path: Path, caplog) -> None:
    """Konflikt loest ein WARNING-Log aus, das den Operator auf den Merge hinweist."""
    import logging as _logging
    (tmp_path / "dup.json").write_text("{}", encoding="utf-8")
    with caplog.at_level(_logging.WARNING, logger="utils.model_utils"):
        resolve_unique_card_id("dup", card_dir=tmp_path)
    assert any("Card-ID-Konflikt" in rec.message for rec in caplog.records)


def test_resolve_unique_card_id_no_log_when_no_conflict(tmp_path: Path, caplog) -> None:
    """Ohne Konflikt wird KEIN WARNING-Log geschrieben."""
    import logging as _logging
    with caplog.at_level(_logging.WARNING, logger="utils.model_utils"):
        resolve_unique_card_id("fresh", card_dir=tmp_path)
    assert not any("Card-ID-Konflikt" in rec.message for rec in caplog.records)


# ---------------------------------------------------------------------------
# Integration: build_card_id + resolve_unique_card_id
# ---------------------------------------------------------------------------

def test_build_then_resolve_no_conflict(tmp_path: Path) -> None:
    """End-to-End: frische ID wird ohne Konflikt akzeptiert."""
    desired = build_card_id("qwen/qwen3.5-4b-q4", "openrouter")
    assert resolve_unique_card_id(desired, card_dir=tmp_path) == desired


def test_build_then_resolve_with_existing_card(tmp_path: Path) -> None:
    """End-to-End: wenn die Card schon existiert (z. B. durch Re-Run), wird
    ein Suffix angehaengt und der Operator gewarnt."""
    desired = build_card_id("claude-sonnet-4-5-20250929", "anthropic")
    # Vorhandene Card simulieren
    (tmp_path / f"{desired}.json").write_text("{}", encoding="utf-8")
    result = resolve_unique_card_id(desired, card_dir=tmp_path)
    assert result == f"{desired}-2"
