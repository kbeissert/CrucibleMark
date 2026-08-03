"""Tests für die Thinking-Profil-Expansion in ConfigValidator.

Hintergrund (Plan: vLLM Dual-Thinking-Profile):
``_expand_thinking_profiles`` expandiert vLLM-Modelle mit
``enable_thinking: true`` in zwei Profile (Standard + Thinking). Die
folgenden Garantien müssen geprüft werden:

1. Expansion erzeugt genau zwei Einträge aus einem
2. Original-Eintrag verliert ``enable_thinking``, bekommt
   ``chat_template_kwargs: {"enable_thinking": False}`` (Default explizit)
3. Thinking-Eintrag hat korrekte ID (``{id}-thinking``), Name (``Thinking``-Suffix),
   ``card_model_id``, ``chat_template_kwargs: {"enable_thinking": True}`` und
   ``max_tokens`` aus ``thinking_max_tokens``
4. Nicht-vLLM-Provider (llama.cpp mit ``enable_thinking`` als Server-Flag)
   werden NICHT expandiert — kritische Regression-Schutz
5. Fehlendes ``thinking_max_tokens`` (weder model_cfg noch Provider-Default)
   löst einen Fehler aus (kein Hardcoding)
6. Per-Modell ``thinking_max_tokens`` schlägt Provider-Default
7. Sampling-Werte (temperature/top_p/top_k) werden vererbt
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from utils.config_validator import ConfigValidator


# Test-Konstanten (vermeidet PLR2004 Magic-Value-Warnungen).
SAMPLING_TEMP: float = 0.6
SAMPLING_TOP_P: float = 0.95
SAMPLING_TOP_K: int = 20
THINKING_MAX_TOKENS: int = 32768
MAX_TOKENS_STANDARD: int = 8192
MAX_TOKENS_DEFAULT: int = 16384


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def vllm_provider_with_thinking() -> dict:
    """Provider-Config mit einem vLLM-Modell, das ``enable_thinking: true`` triggert."""
    return {
        "vllm_spark": {
            "name": "vLLM (asusGX10)",
            "api_type": "vllm",
            "enabled": True,
            "thinking_max_tokens": THINKING_MAX_TOKENS,
            "models": [
                {
                    "id": "ornith-1.0-35B-FP8",
                    "name": "Ornith 1.0 35B FP8",
                    "config": "Ornith1-35B-FP8",
                    "max_tokens": MAX_TOKENS_STANDARD,
                    "temperature": SAMPLING_TEMP,
                    "top_p": SAMPLING_TOP_P,
                    "top_k": SAMPLING_TOP_K,
                    "enable_thinking": True,
                },
                {
                    "id": "untouched-model",
                    "name": "Untouched",
                    "config": "UntouchedTOML",
                    "max_tokens": MAX_TOKENS_DEFAULT,
                },
            ],
        },
    }


@pytest.fixture
def llamacpp_provider_with_thinking() -> dict:
    """llama.cpp-Provider mit ``enable_thinking: true`` — darf NICHT expandiert werden."""
    return {
        "llamacpp_spark": {
            "name": "Llama.cpp (DGX Spark)",
            "api_type": "llamacpp",
            "enabled": True,
            "models": [
                {
                    "id": "qwable-3.6-35b-q5",
                    "name": "Qwable 3.6 35B Q5_K_M",
                    "model_file": "Qwable35b/Qwable-3.6-35b_q5_k_m.gguf",
                    "enable_thinking": True,
                },
            ],
        },
    }


def _run_expand(providers: dict) -> None:
    """Direkt die Expansion ohne File-I/O aufrufen (schnell + isoliert)."""
    validator = object.__new__(ConfigValidator)
    validator._expand_thinking_profiles({"local": providers})


# ---------------------------------------------------------------------------
# 1. Expansion-Grundverhalten
# ---------------------------------------------------------------------------


def test_expansion_produces_two_entries_from_one(vllm_provider_with_thinking):
    """Ein Modell mit ``enable_thinking: true`` wird zu zwei Einträgen expandiert."""
    providers = vllm_provider_with_thinking
    _run_expand(providers)

    models = providers["vllm_spark"]["models"]
    assert len(models) == 3
    ids = [m["id"] for m in models]
    assert "ornith-1.0-35B-FP8" in ids
    assert "ornith-1.0-35B-FP8-thinking" in ids


def test_expansion_preserves_models_without_trigger(vllm_provider_with_thinking):
    """Modelle ohne ``enable_thinking`` bleiben unverändert."""
    providers = vllm_provider_with_thinking
    _run_expand(providers)

    models = providers["vllm_spark"]["models"]
    untouched = next(m for m in models if m["id"] == "untouched-model")
    assert untouched == {
        "id": "untouched-model",
        "name": "Untouched",
        "config": "UntouchedTOML",
        "max_tokens": MAX_TOKENS_DEFAULT,
    }


# ---------------------------------------------------------------------------
# 2. Original-Eintrag: enable_thinking konsumiert + explizit False
# ---------------------------------------------------------------------------


def test_original_entry_drops_enable_thinking(vllm_provider_with_thinking):
    """Original-Eintrag verliert das ``enable_thinking``-Feld."""
    providers = vllm_provider_with_thinking
    _run_expand(providers)

    standard = next(
        m for m in providers["vllm_spark"]["models"] if m["id"] == "ornith-1.0-35B-FP8"
    )
    assert "enable_thinking" not in standard


def test_original_entry_has_explicit_disable_in_chat_template_kwargs(
    vllm_provider_with_thinking,
):
    """Original bekommt ``chat_template_kwargs: {"enable_thinking": False}``."""
    providers = vllm_provider_with_thinking
    _run_expand(providers)

    standard = next(
        m for m in providers["vllm_spark"]["models"] if m["id"] == "ornith-1.0-35B-FP8"
    )
    assert standard["chat_template_kwargs"] == {"enable_thinking": False}


def test_original_entry_preserves_sampling_values(vllm_provider_with_thinking):
    """Sampling-Werte (temperature/top_p/top_k) und max_tokens bleiben am Original."""
    providers = vllm_provider_with_thinking
    _run_expand(providers)

    standard = next(
        m for m in providers["vllm_spark"]["models"] if m["id"] == "ornith-1.0-35B-FP8"
    )
    assert standard["temperature"] == SAMPLING_TEMP
    assert standard["top_p"] == SAMPLING_TOP_P
    assert standard["top_k"] == SAMPLING_TOP_K
    assert standard["max_tokens"] == MAX_TOKENS_STANDARD


# ---------------------------------------------------------------------------
# 3. Thinking-Eintrag: korrekte Felder
# ---------------------------------------------------------------------------


def test_thinking_entry_has_correct_id_suffix(vllm_provider_with_thinking):
    """Thinking-Eintrag hat ID ``{original_id}-thinking``."""
    providers = vllm_provider_with_thinking
    _run_expand(providers)

    thinking = next(
        m for m in providers["vllm_spark"]["models"]
        if m["id"] == "ornith-1.0-35B-FP8-thinking"
    )
    assert thinking["id"] == "ornith-1.0-35B-FP8-thinking"


def test_thinking_entry_has_thinking_name_suffix(vllm_provider_with_thinking):
    """Thinking-Eintrag hat Name ``{original_name} Thinking``."""
    providers = vllm_provider_with_thinking
    _run_expand(providers)

    thinking = next(
        m for m in providers["vllm_spark"]["models"]
        if m["id"] == "ornith-1.0-35B-FP8-thinking"
    )
    assert thinking["name"] == "Ornith 1.0 35B FP8 Thinking"


def test_thinking_entry_has_card_model_id_pointing_to_original(
    vllm_provider_with_thinking,
):
    """Thinking-Eintrag trägt ``card_model_id: {original_id}`` (Card-Lookup-Basis)."""
    providers = vllm_provider_with_thinking
    _run_expand(providers)

    thinking = next(
        m for m in providers["vllm_spark"]["models"]
        if m["id"] == "ornith-1.0-35B-FP8-thinking"
    )
    assert thinking["card_model_id"] == "ornith-1.0-35B-FP8"


def test_thinking_entry_has_enable_thinking_true_in_chat_template_kwargs(
    vllm_provider_with_thinking,
):
    """Thinking-Eintrag aktiviert Reasoning per ``chat_template_kwargs``."""
    providers = vllm_provider_with_thinking
    _run_expand(providers)

    thinking = next(
        m for m in providers["vllm_spark"]["models"]
        if m["id"] == "ornith-1.0-35B-FP8-thinking"
    )
    assert thinking["chat_template_kwargs"] == {"enable_thinking": True}


def test_thinking_entry_uses_thinking_max_tokens(vllm_provider_with_thinking):
    """Thinking-Eintrag übernimmt ``thinking_max_tokens`` aus dem Provider-Default."""
    providers = vllm_provider_with_thinking
    _run_expand(providers)

    thinking = next(
        m for m in providers["vllm_spark"]["models"]
        if m["id"] == "ornith-1.0-35B-FP8-thinking"
    )
    assert thinking["max_tokens"] == THINKING_MAX_TOKENS


def test_thinking_entry_inherits_sampling_values(vllm_provider_with_thinking):
    """Thinking-Eintrag erbt Sampling-Werte vom Original."""
    providers = vllm_provider_with_thinking
    _run_expand(providers)

    thinking = next(
        m for m in providers["vllm_spark"]["models"]
        if m["id"] == "ornith-1.0-35B-FP8-thinking"
    )
    assert thinking["temperature"] == SAMPLING_TEMP
    assert thinking["top_p"] == SAMPLING_TOP_P
    assert thinking["top_k"] == SAMPLING_TOP_K


def test_thinking_entry_shares_config_with_original(vllm_provider_with_thinking):
    """Beide Profile zeigen auf dasselbe ``config:`` (TOML) — kein Container-Swap."""
    providers = vllm_provider_with_thinking
    _run_expand(providers)

    models = providers["vllm_spark"]["models"]
    standard = next(m for m in models if m["id"] == "ornith-1.0-35B-FP8")
    thinking = next(m for m in models if m["id"] == "ornith-1.0-35B-FP8-thinking")
    assert standard["config"] == thinking["config"] == "Ornith1-35B-FP8"


# ---------------------------------------------------------------------------
# 4. Nicht-vLLM-Provider: keine Expansion
# ---------------------------------------------------------------------------


def test_llamacpp_with_enable_thinking_is_not_expanded(llamacpp_provider_with_thinking):
    """llama.cpp nutzt ``enable_thinking`` als Server-Flag mit anderer Semantik.

    Kritische Regression-Schutz: Expansion darf NUR für ``api_type == "vllm"``
    greifen. llama.cpp-Modell bleibt unverändert (mit ``enable_thinking: true``
    als Server-Start-Param).
    """
    providers = llamacpp_provider_with_thinking
    _run_expand(providers)

    models = providers["llamacpp_spark"]["models"]
    assert len(models) == 1
    assert models[0]["id"] == "qwable-3.6-35b-q5"
    assert models[0]["enable_thinking"] is True
    assert "card_model_id" not in models[0]
    assert "chat_template_kwargs" not in models[0]


# ---------------------------------------------------------------------------
# 5. Fehlendes thinking_max_tokens → Fehler
# ---------------------------------------------------------------------------


def test_missing_thinking_max_tokens_raises_error(tmp_path: Path):
    """Ohne thinking_max_tokens (weder model_cfg noch Provider-Default) → ValueError.

    Verhindert stilles Hardcoding eines Default-Werts (AGENTS.md:
    Konfiguration ausschließlich über Config-Files).
    """
    providers = {
        "vllm_spark": {
            "name": "vLLM",
            "api_type": "vllm",
            "enabled": True,
            # KEIN thinking_max_tokens auf Provider-Ebene.
            "models": [
                {
                    "id": "model-no-budget",
                    "name": "M",
                    "config": "MTOML",
                    "enable_thinking": True,
                },
            ],
        },
    }

    with pytest.raises(ValueError, match="thinking_max_tokens"):
        _run_expand(providers)


# ---------------------------------------------------------------------------
# 6. Per-Modell thinking_max_tokens schlägt Provider-Default
# ---------------------------------------------------------------------------


def test_per_model_thinking_max_tokens_overrides_provider_default(tmp_path: Path):
    """Per-Modell ``thinking_max_tokens`` gewinnt gegen Provider-Default."""
    providers = {
        "vllm_spark": {
            "name": "vLLM",
            "api_type": "vllm",
            "enabled": True,
            "thinking_max_tokens": THINKING_MAX_TOKENS,
            "models": [
                {
                    "id": "model-a",
                    "name": "M",
                    "config": "MTOML",
                    "thinking_max_tokens": 65536,  # Override
                    "enable_thinking": True,
                },
            ],
        },
    }
    _run_expand(providers)

    thinking = next(
        m for m in providers["vllm_spark"]["models"] if m["id"] == "model-a-thinking"
    )
    assert thinking["max_tokens"] == 65536


# ---------------------------------------------------------------------------
# 7. Integration: ConfigValidator lädt provider_config.yaml inkl. Expansion
# ---------------------------------------------------------------------------


def test_provider_config_yaml_ornith_is_expanded(tmp_path: Path, monkeypatch):
    """End-to-End: Die echte provider_config.yaml expandiert Ornith korrekt.

    Verifiziert, dass die ``enable_thinking: true``-Zeile am Ornith-vLLM-
    Eintrag tatsächlich zwei Profile erzeugt — und keine Regression
    bestehender Modelle verursacht.
    """
    # benchmark_config.yaml (minimal) in tmp_path schreiben.
    bench_cfg = tmp_path / "benchmark_config.yaml"
    bench_cfg.write_text("golden_standard: {}\n", encoding="utf-8")

    validator = ConfigValidator(config_path=str(bench_cfg))
    models = validator.config["providers"]["local"]["vllm_spark"]["models"]
    ids = {m["id"] for m in models}

    # Ornith muss expandiert sein.
    assert "ornith-1.0-35B-FP8" in ids
    assert "ornith-1.0-35B-FP8-thinking" in ids

    # Standard-Profil: enable_thinking konsumiert, explizit False.
    standard = next(m for m in models if m["id"] == "ornith-1.0-35B-FP8")
    assert "enable_thinking" not in standard
    assert standard["chat_template_kwargs"] == {"enable_thinking": False}

    # Thinking-Profil: card_model_id + enable_thinking=true.
    thinking = next(m for m in models if m["id"] == "ornith-1.0-35B-FP8-thinking")
    assert thinking["card_model_id"] == "ornith-1.0-35B-FP8"
    assert thinking["chat_template_kwargs"] == {"enable_thinking": True}
    assert thinking["max_tokens"] == THINKING_MAX_TOKENS  # 32768 aus Provider-Default

    # Bestehende Modelle ohne Trigger müssen unverändert sein.
    gemma26 = next(m for m in models if m["id"] == "Gemma-4-26B")
    assert "enable_thinking" not in gemma26
    assert "card_model_id" not in gemma26
    assert gemma26["max_tokens"] == 16384  # wie in provider_config.yaml


def test_llamacpp_ornith_in_provider_config_unchanged(tmp_path: Path, monkeypatch):
    """llama.cpp's Ornith (anderes Backend) bleibt unverändert — keine Expansion."""
    bench_cfg = tmp_path / "benchmark_config.yaml"
    bench_cfg.write_text("golden_standard: {}\n", encoding="utf-8")

    validator = ConfigValidator(config_path=str(bench_cfg))
    llamacpp_models = validator.config["providers"]["local"]["llamacpp_spark"]["models"]
    llamacpp_ids = {m["id"] for m in llamacpp_models}

    # llamacpp.ornith-1-0-35b existiert und hat enable_thinking: false (manuell gesetzt).
    ornith_llamacpp = next(m for m in llamacpp_models if m["id"] == "ornith-1-0-35b")
    assert ornith_llamacpp["enable_thinking"] is False

    # Sicherstellen, dass KEIN llama.cpp-Modell ein "*-thinking"-Suffix bekommen hat.
    assert not any(mid.endswith("-thinking") for mid in llamacpp_ids)


# ---------------------------------------------------------------------------
# 8. Expansion ist idempotent
# ---------------------------------------------------------------------------


def test_expansion_is_idempotent(vllm_provider_with_thinking):
    """Zweimaliges Expandieren führt zu keiner weiteren Expansion.

    Beim zweiten Lauf hat das Original-Eintrag bereits kein ``enable_thinking``
    mehr → kein Trigger. Das Thinking-Profil hat ebenfalls kein ``enable_thinking``
    (wurde konsumiert). Ergebnis: keine Änderung beim zweiten Lauf.
    """
    providers = vllm_provider_with_thinking
    _run_expand(providers)
    snapshot_after_first = yaml.safe_load(yaml.safe_dump(providers))

    _run_expand(providers)
    assert providers == snapshot_after_first