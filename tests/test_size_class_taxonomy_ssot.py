"""SSoT-Tests fuer die Size-Class-Taxonomie in config/classification_taxonomy.json.

Sichert:
- Taxonomy-Loader liest die korrekte Struktur (thresholds_b, tier_order, values).
- _param_b_to_size_class() liefert fuer bekannte Parameterwerte die gleichen
  Ergebnisse wie der fruehere hartkodierte Code.
- Card-Vocabulary-Whitelist wird aus der Taxonomy abgeleitet, nicht mehr
  dupliziert gepflegt.
- get_model_size_class() bleibt black-box-stabil fuer bekannte Modellnamen
  (Regression-Schutz fuer historische Benchmark-Tier-Zuordnungen).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.model_utils import (
    _param_b_to_size_class,
    _load_size_class_taxonomy,
    get_model_size_class,
)

ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = ROOT / "config" / "classification_taxonomy.json"


# ---------------------------------------------------------------------------
# 1. Taxonomy-Loader: Struktur & Konsistenz
# ---------------------------------------------------------------------------

def test_taxonomy_loader_returns_complete_structure():
    """Loader liefert thresholds_b, tier_order und alle 6 Tier-Values."""
    sc = _load_size_class_taxonomy()
    assert sc["tier_order"] == [
        "Nano", "Edge", "Desktop", "Workstation", "Server", "Frontier",
    ]
    assert sc["thresholds_b"] == [4, 9, 22, 35, 75]
    assert len(sc["values"]) == 6
    for tier in sc["tier_order"]:
        assert tier in sc["values"], f"Tier '{tier}' fehlt in size_class.values"
        assert "label" in sc["values"][tier]
        assert "reviewer_guidance" in sc["values"][tier]


def test_taxonomy_tiers_have_param_ranges():
    """Jeder Tier ausser Frontier hat min/max_params_b, Frontier hat max_params_b=null."""
    sc = _load_size_class_taxonomy()
    for tier in sc["tier_order"]:
        entry = sc["values"][tier]
        if tier == "Frontier":
            assert entry["max_params_b"] is None
        else:
            assert isinstance(entry["min_params_b"], int)
            assert isinstance(entry["max_params_b"], int)
            assert entry["min_params_b"] < entry["max_params_b"]


def test_taxonomy_thresholds_match_param_ranges():
    """thresholds_b und tier_order[0..-1] muessen konsistent sein."""
    sc = _load_size_class_taxonomy()
    non_fallback_tiers = sc["tier_order"][:-1]  # alles ausser Frontier
    assert len(sc["thresholds_b"]) == len(non_fallback_tiers)
    for threshold, tier in zip(sc["thresholds_b"], non_fallback_tiers):
        assert threshold == sc["values"][tier]["max_params_b"], (
            f"thresholds_b-Eintrag {threshold} passt nicht zu {tier}.max_params_b="
            f"{sc['values'][tier]['max_params_b']}"
        )


def test_taxonomy_is_cached():
    """lru_cache: zweiter Aufruf gibt dasselbe dict-Objekt zurueck (kein Reload)."""
    a = _load_size_class_taxonomy()
    b = _load_size_class_taxonomy()
    assert a is b


# ---------------------------------------------------------------------------
# 2. _param_b_to_size_class: Regression gegen den frueheren Hardcode
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("param_b, expected", [
    (0.5, "Nano"),
    (3.0, "Nano"),
    (4.0, "Nano"),        # inklusive Grenze
    (4.5, "Edge"),        # erste Param-Stelle > Nano-Schwelle
    (7.0, "Edge"),
    (9.0, "Edge"),        # inklusive Grenze
    (9.5, "Desktop"),
    (14.0, "Desktop"),
    (22.0, "Desktop"),    # inklusive Grenze
    (22.5, "Workstation"),
    (32.0, "Workstation"),
    (35.0, "Workstation"),  # inklusive Grenze
    (35.5, "Server"),
    (70.0, "Server"),
    (75.0, "Server"),     # inklusive Grenze
    (75.5, "Frontier"),
    (120.0, "Frontier"),
    (405.0, "Frontier"),  # Llama 3.1 405B
])
def test_param_b_to_size_class(param_b: float, expected: str):
    assert _param_b_to_size_class(param_b) == expected


# ---------------------------------------------------------------------------
# 3. get_model_size_class: Black-Box-Stabilitaet fuer bekannte Modellnamen
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("model_name, expected", [
    # Ollama-Colon-Tags
    ("qwen3:4b", "Nano"),
    ("qwen2.5:3b", "Nano"),
    ("mistral:7b", "Edge"),
    ("phi3.5:3.8b", "Nano"),
    # Edge-Prefix (z.B. Gemma 4 E-Varianten)
    ("gemma4:E4B", "Nano"),
    # Dash-Suffix
    ("qwen3-14b", "Desktop"),
    ("qwen3-32b", "Workstation"),
    ("llama-3.3-70b", "Server"),
    # Frontier / API-only (kein Size-Tag)
    ("claude-sonnet-4-6", "Frontier"),
    ("gpt-5", "Frontier"),
    ("gemini-2.5-pro", "Frontier"),
])
def test_get_model_size_class_known_models(model_name: str, expected: str):
    assert get_model_size_class(model_name) == expected


def test_get_model_size_class_returns_taxonomy_known_value():
    """Ergebnis MUSS aus tier_order stammen, niemals ein unbekannter String."""
    sc = _load_size_class_taxonomy()
    valid = set(sc["tier_order"])
    for name in [
        "qwen3:4b", "mistral:7b", "qwen3-14b", "qwen3-32b",
        "llama-3.3-70b", "claude-sonnet-4-6", "gpt-5",
    ]:
        result = get_model_size_class(name)
        assert result in valid, f"{name} lieferte {result!r}, nicht in tier_order"


# ---------------------------------------------------------------------------
# 4. Card-Vocabulary-Whitelist aus Taxonomy ableiten
# ---------------------------------------------------------------------------

def test_card_vocabulary_size_class_uses_taxonomy():
    """Card-Vocab-Loader zieht size_class-Werte aus der Taxonomy, nicht aus YAML-Duplikat."""
    try:
        from utils.card_utils import load_vocabulary
    except ImportError:
        pytest.skip("utils.card_utils nicht importierbar in dieser Umgebung")

    vocab = load_vocabulary()
    taxonomy = _load_size_class_taxonomy()
    vocab_size = vocab.get("controlled_fields", {}).get("size_class", {})
    vocab_values = set(vocab_size.get("values", []))
    assert vocab_values == set(taxonomy["tier_order"]), (
        f"Card-Vocab-Whitelist {vocab_values} weicht von tier_order "
        f"{set(taxonomy['tier_order'])} ab"
    )


def test_card_vocabulary_size_class_marker_uses_taxonomy():
    """Wenn values_from gesetzt ist, MUSS der Loader daraus ableiten."""
    raw = yaml_text = (ROOT / "config" / "card_vocabulary.yaml").read_text(encoding="utf-8")
    assert "values_from" in raw, "card_vocabulary.yaml enthaelt keinen values_from-Hinweis"
    assert "tier_order" in raw, "card_vocabulary.yaml verweist nicht auf tier_order"


# ---------------------------------------------------------------------------
# 5. Taxonomy-Datei selbst: harte Konsistenz-Pruefung
# ---------------------------------------------------------------------------

def test_taxonomy_json_is_valid_and_consistent():
    """JSON-Datei selbst muss gueltig sein und alle Felder liefern."""
    assert TAXONOMY_PATH.exists(), f"{TAXONOMY_PATH} fehlt"
    data = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    sc = data["size_class"]
    assert "thresholds_b" in sc, "thresholds_b fehlt in classification_taxonomy.json"
    assert "tier_order" in sc, "tier_order fehlt in classification_taxonomy.json"
    # Alle Tier-Keys muessen in tier_order vorkommen
    assert set(sc["values"].keys()) == set(sc["tier_order"]), (
        "Keys in size_class.values und tier_order sind nicht identisch"
    )