"""Tests for resolve_canonical_model_id() SSoT-Funktion.

Diese Tests verlassen sich auf echte Model-Cards in
``benchmark_scores/model_cards/`` (glob-fallback Card-Alias, Card-Lookup
fuer qwen/qwen3* etc.) und sind daher mit ``@pytest.mark.uses_real_cards``
markiert, damit die globale CARD_DIR-Isolation in ``conftest.py``
uebersprungen wird.
"""

from __future__ import annotations

import pytest

from utils.model_utils import resolve_canonical_model_id

pytestmark = pytest.mark.uses_real_cards


@pytest.mark.parametrize(
    "input_id, expected, description",
    [
        # Punkt → Underscore via Card-Lookup (Hauptanwendungsfall)
        ("qwen3.5-35b-a3b-q4", "qwen3_5-35b-a3b-q4", "Q4 dot→underscore via Card-Lookup"),
        ("qwen3.5-35b-a3b-q8", "qwen3_5-35b-a3b-q8", "Q8 dot→underscore via Card-Lookup"),
        # Punkt bleibt erhalten: Card-Dateiname = Underscore, model_id IN der Card = Punkt-Form
        # (OpenAI akzeptiert gpt-5_4-nano nicht, aber gpt-5.4-nano → model_id muss Punkt-Form sein)
        ("gpt-5.4-nano", "gpt-5.4-nano", "gpt-5.4-nano: Card via safe_name, model_id=dot-form"),
        ("gpt-5_4-nano", "gpt-5.4-nano", "gpt-5_4-nano: Card direkt, model_id=dot-form"),
        # qwen3.5-35b-a3b-q6 ist kein aktives Modell (kein Card-Eintrag) →
        # Fallback: _safe_name(base) → Punkte werden zu Underscores (systemweite Konvention).
        ("qwen3.5-35b-a3b-q6", "qwen3_5-35b-a3b-q6", "Q6 kein Card → _safe_name Fallback"),
        ("qwen3.5-9b", "qwen3_5-9b", "9B dot→underscore via Card-Lookup"),
        ("qwen3.5-4b-q4", "qwen3_5-4b-q4", "4B Q4 dot→underscore via Card-Lookup"),
        # Bereits kanonisch (Underscore) → unverändert
        ("qwen3_5-35b-a3b-q4", "qwen3_5-35b-a3b-q4", "Bereits kanonisch"),
        # hf.co/AUTHOR/ Prefix strippen
        (
            "hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M",
            "NousResearch_Hermes-4-14B-GGUF:Q4_K_M",
            "hf.co Prefix strippen",
        ),
        # Card-Alias via glob-fallback (claude-haiku-4-5 → claude-haiku-4-5-20251001)
        (
            "claude-haiku-4-5",
            "claude-haiku-4-5-20251001",
            "glob-fallback Card-Alias",
        ),
        # Edge cases
        ("", "", "Empty input"),
        ("unbekanntes-modell", "unbekanntes-modell", "No card → safe_name fallback"),
        # Namespaced IDs bleiben unverändert (OpenRouter-Routing)
        ("qwen/qwen3-32b", "qwen/qwen3-32b", "Namespaced bleibt namespaced"),
        # Suffixe bleiben unverändert (Card-Lookup findet qwen_qwen3_6-plus.json
        # und gibt deren model_id unverändert zurück — semantische IDs)
        (
            "qwen/qwen3.6-plus:free",
            "qwen/qwen3.6-plus:free",
            "Card-Lookup liefert kanonische model_id der Card",
        ),
    ],
)
def test_resolve_canonical_model_id(input_id, expected, description):
    """Prüft dass die SSoT-Auflösung für alle bekannten Schreibweisen funktioniert."""
    actual = resolve_canonical_model_id(input_id)
    assert actual == expected, (
        f"{description}: resolve_canonical_model_id({input_id!r}) = {actual!r}, "
        f"erwartet: {expected!r}"
    )


def test_resolve_canonical_model_id_idempotent():
    """Zweimaliges Auflösen muss dasselbe Ergebnis liefern."""
    test_ids = [
        "qwen3.5-35b-a3b-q4",
        "qwen3_5-35b-a3b-q4",
        "claude-haiku-4-5",
        "hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M",
    ]
    for mid in test_ids:
        first = resolve_canonical_model_id(mid)
        second = resolve_canonical_model_id(first)
        assert first == second, (
            f"Idempotenz verletzt für {mid!r}: {first!r} != {second!r}"
        )
