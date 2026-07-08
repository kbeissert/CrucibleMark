"""Regression test: resolve_provider() muss Version-Underscore→Dot normalisieren.

Hintergrund
-----------
``resolve_canonical_model_id()`` ersetzt Punkte in Version-Segmenten mit
Underscores (z.B. ``ornith-1.0-35B-FP8`` → ``ornith-1_0-35B-FP8``). Die
Einträge in ``config/provider_config.yaml`` nutzen jedoch weiterhin die
Dot-Form (``ornith-1.0-35B-FP8``).

Vor dem Fix (util/model_utils.py:1061) wurde in ``resolve_provider()`` ein
exakter String-Vergleich gegen ``provider_config.yaml`` durchgeführt,
wodurch kanonisierte IDs den falschen Provider-Slot fanden
(``ornith-1_0-35B-FP8`` → ``ollama``, ``qwen3_6-27B`` → ``groq``).

Diese Tests sichern die korrekte Zuteilung mit beiden Schreibweisen ab und
verhindern, dass der nächste Refactor in der SSoT-Pipeline denselben
Mapping-Drift erneut einführt.
"""

from __future__ import annotations

import pytest

from utils.model_utils import resolve_provider


@pytest.mark.parametrize(
    "model_id, expected_provider",
    [
        # Ornith 1.0 35B FP8 — betroffene Regressionsfälle vor dem Fix
        ("ornith-1.0-35B-FP8", "vllm_spark"),
        ("ornith-1_0-35B-FP8", "vllm_spark"),
        # Qwen3.6-27B — Canonicalisierung qwen3_6-27B (Underscore-Form)
        ("qwen3.6-27B", "vllm_spark"),
        ("qwen3_6-27B", "vllm_spark"),
        # llama.cpp Spark — Config-Eintrag nutzt bereits Canonical-Underscore.
        # Verifiziert, dass resolve_provider() exakt matcht (kein Drift).
        ("qwen3_5-35b-a3b-q8", "llamacpp_spark"),
    ],
)
def test_resolve_provider_matches_canonical_underscore_against_dot_config(
    model_id: str, expected_provider: str
) -> None:
    """Canonical Underscore-Form muss gegen Dot-Config-Einträge matchen."""
    provider, _ = resolve_provider(model_id)
    assert provider == expected_provider, (
        f"resolve_provider({model_id!r}) → {provider!r}, expected {expected_provider!r}. "
        "Mapping-Drift zwischen resolve_canonical_model_id() und provider_config.yaml."
    )


@pytest.mark.parametrize(
    "model_id, expected_provider",
    [
        # Gemma-4 enthält keinen Digit-Underscore-Digit-Pattern;
        # dient als Sanity-Check, dass die Normalisierung keine Regression
        # für Modelle ohne Version-Underscore einführt.
        ("Gemma-4-31B", "vllm_spark"),
        ("Gemma-4-26B", "vllm_spark"),
    ],
)
def test_resolve_provider_no_version_pattern_unchanged(
    model_id: str, expected_provider: str
) -> None:
    provider, _ = resolve_provider(model_id)
    assert provider == expected_provider


@pytest.mark.parametrize(
    "model_id, expected_provider",
    [
        # Vorab-Heuristiken dürfen nicht durch den Config-Lookup-Pfad
        # überlagert werden — separater Sanity-Check.
        ("gemma3:12b", "ollama"),                # Tag-Suffix → ollama
        ("minimax/minimax-m3", "openrouter"),     # '/' Prefix → openrouter
    ],
)
def test_resolve_provider_heuristics_preserved(
    model_id: str, expected_provider: str
) -> None:
    provider, _ = resolve_provider(model_id)
    assert provider == expected_provider
