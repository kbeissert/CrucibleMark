"""Tests for canonical_lookup_keys — SSoT für Defense-in-Depth Cache-Lookups.

Score-Cache-Hardening Phase 9: der Cache-Lookup muss unabhängig von der
Schreibweise des Modellnamens funktionieren, weil Orchestrator, Config und
Leaderboard jeweils unterschiedliche Formen liefern können (Punkt vs.
Underscore, hf.co-Prefix, Datumssuffix).
"""
from __future__ import annotations

import pytest

from scripts.core.llamacpp_batch import canonical_lookup_keys


@pytest.mark.parametrize(
    "model_id,expected_subset",
    [
        # Hauptbug: Roh-Name mit Punkt + kanonische Form mit Underscore
        ("qwen2.5-coder-7b", {"qwen2.5-coder-7b", "qwen2_5-coder-7b"}),
        # Vendor-Prefix (Slash) ohne hf.co: normalize_model_id lässt raw
        # unverändert (kein hf.co-Prefix), _safe_name macht Slash → Underscore
        (
            "meta-llama/Llama-3.1-8B-Instruct",
            {
                "meta-llama/Llama-3.1-8B-Instruct",
                "meta-llama_Llama-3_1-8B-Instruct",
            },
        ),
        # hf.co/-Prefix wird komplett gestrippt (inkl. Vendor-Prefix),
        # plus _safe_name-Form der no-hf-Variante
        (
            "hf.co/meta-llama/Llama-3.1-8B",
            {
                "hf.co/meta-llama/Llama-3.1-8B",
                "Llama-3.1-8B",
                "Llama-3_1-8B",
            },
        ),
        # Datumssuffix wird gestrippt (sowohl raw als auch no_hf)
        (
            "gpt-5-20251201",
            {"gpt-5-20251201", "gpt-5"},
        ),
        # Ollama-Tag-Form (Doppelpunkt)
        (
            "gemma3:12b",
            {"gemma3:12b", "gemma3_12b"},
        ),
        # Komplexer Fall: Vendor-Prefix (qwen/) + Punkt + Datumssuffix.
        # normalize_model_id strippt nur hf.co/-Prefix, NICHT qwen/.
        # Daher: raw == normalize. Varianten entstehen durch _safe_name
        # und strip_date_suffix.
        (
            "qwen/qwen3.5-35b-a3b-q4-20251001",
            {
                "qwen/qwen3.5-35b-a3b-q4-20251001",
                "qwen/qwen3.5-35b-a3b-q4",
                "qwen_qwen3_5-35b-a3b-q4-20251001",
                "qwen_qwen3_5-35b-a3b-q4",
            },
        ),
    ],
)
def test_canonical_lookup_keys_returns_expected_variants(
    model_id: str, expected_subset: set[str]
) -> None:
    """Alle kanonischen Varianten müssen im Ergebnis enthalten sein."""
    result = canonical_lookup_keys(model_id)
    assert expected_subset.issubset(result), (
        f"Erwartet {expected_subset} ⊆ {result}"
    )


@pytest.mark.parametrize(
    "model_id",
    [
        "",
        "   ",
        None,
        123,
        [],
        {},
    ],
)
def test_canonical_lookup_keys_handles_invalid_input(model_id: object) -> None:
    """Leere/None/nicht-string-Inputs geben leeres Set zurück (kein Crash)."""
    result = canonical_lookup_keys(model_id)
    assert result == set()


def test_canonical_lookup_keys_strips_whitespace() -> None:
    """Führende/nachfolgende Whitespace wird ignoriert."""
    result = canonical_lookup_keys("  qwen2.5-coder-7b  ")
    assert "qwen2.5-coder-7b" in result
    assert "qwen2_5-coder-7b" in result
    assert "" not in result


def test_canonical_lookup_keys_is_idempotent() -> None:
    """Zwei Aufrufe mit derselben Eingabe liefern dasselbe Set."""
    first = canonical_lookup_keys("qwen2.5-coder-7b")
    second = canonical_lookup_keys("qwen2.5-coder-7b")
    assert first == second


def test_canonical_lookup_keys_handles_qwen_coder_real_case() -> None:
    """Regression-Test für den ursprünglichen Bug: qwen2.5-coder-7b (Punkt) muss
    die kanonische Form qwen2_5-coder-7b (Underscore) im Ergebnis haben, damit
    der Leaderboard-Cache-Lookup im Auto-Orchestrator funktioniert."""
    result = canonical_lookup_keys("qwen2.5-coder-7b")
    assert "qwen2.5-coder-7b" in result  # roh
    assert "qwen2_5-coder-7b" in result  # kanonisch (via _safe_name)


# ---------------------------------------------------------------------------
# Asymmetrische Bruecke Underscore -> Punkt
# ---------------------------------------------------------------------------
# _safe_name ist destruktiv (Punkt -> Underscore), aber die Multi-Key-Brücke
# muss in BEIDE Richtungen funktionieren, weil das Leaderboard die Underscore-
# Form speichert, der spaetere Caller aber oft die Rohform mit Punkt liefert.


def test_canonical_lookup_keys_underscore_input_generates_dotted_variant() -> None:
    """Aus 'qwen2_5-coder-7b' (Underscore, wie im Leaderboard) muss
    'qwen2.5-coder-7b' (Punkt) als Lookup-Variante entstehen."""
    result = canonical_lookup_keys("qwen2_5-coder-7b")
    assert "qwen2_5-coder-7b" in result  # roh
    assert "qwen2.5-coder-7b" in result  # asymmetrische Bruecke


def test_canonical_lookup_keys_underscore_input_qwen35() -> None:
    """qwen3_5-4b-q4 (Underscore) muss qwen3.5-4b-q4 (Punkt) erzeugen."""
    result = canonical_lookup_keys("qwen3_5-4b-q4")
    assert "qwen3_5-4b-q4" in result
    assert "qwen3.5-4b-q4" in result


def test_canonical_lookup_keys_underscore_input_does_not_affect_no_digit_groups() -> None:
    """Wenn keine Ziffer_Ziffer-Sequenz im Namen steckt, wird KEINE zusaetzliche
    dotted-Variante erzeugt (kein False-Positive fuer Namen wie 'claude-haiku-4-5')."""
    result = canonical_lookup_keys("claude-haiku-4-5")
    # Roh: 'claude-haiku-4-5' (kein '_', also keine dotted-Heuristik)
    assert "claude-haiku-4-5" in result
    # _safe_name macht '-' NICHT zu '_' (Pattern [:/.\ ]), daher bleibt es raw.
    # Wichtig: KEINE dotted-Variante (4_5 wuerde zu 4.5, aber wir haben 4-5).
    assert "claude-haiku.4.5" not in result
    assert "claude.haiku.4.5" not in result
