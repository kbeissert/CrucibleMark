"""
Provider & Ollama Health-Checks — Pre-Validierung für Tool-Use-Backlog.

Wird von scripts/core/benchmark_auto.py verwendet, um vor dem Tool-Use-Subprocess
zu prüfen, ob ein untested-Modell überhaupt erreichbar ist. Verhindert, dass
nicht-installierte Ollama-Modelle oder fehlkonfigurierte API-Provider den
gesamten Pre-Step crashen oder in Endlos-Loops hängen.

Funktionen:
    get_installed_ollama_models()  → Set[str]   (case-sensitive Namen)
    is_ollama_model_installed(name, cache) → bool
    is_api_provider_available(provider, env_var) → bool
    validate_untested_card(card) → (ok: bool, reason: str | None)

Cache:    OLLAMA_MODEL_CACHE (dict[str, set])   — pro Prozess, ein 'ollama list' reicht.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

from utils.constants import TIMEOUT_OLLAMA_LIST_FAST
from utils.model_utils import resolve_provider

logger = logging.getLogger(__name__)

# Provider-Name → ENV-Var Mapping. Wird von validate_untested_card() genutzt,
# um vor dem API-Call zu prüfen, ob der Key überhaupt gesetzt ist.
_PROVIDER_ENV_VARS: dict[str, str] = {
    "mistral": "MISTRAL_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "xai": "XAI_API_KEY",
    "groq": "GROQ_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


class _OllamaModelCache:
    """Trivialer Singleton-Container als pylint-saubere Alternative zu `global`."""

    def __init__(self) -> None:
        self.value: set[str] | None = None


_OLLAMA_MODEL_CACHE = _OllamaModelCache()


def _infer_provider_from_config(model_id: str) -> str | None:
    """Infer provider only via exact ID matches in config files (no heuristics)."""
    config_paths = (Path("benchmark_config.yaml"), Path("config/provider_config.yaml"))
    for config_path in config_paths:
        if not config_path.exists():
            continue
        try:
            with config_path.open("r", encoding="utf-8") as handle:
                cfg = yaml.safe_load(handle) or {}
        except (OSError, yaml.YAMLError):
            continue

        providers = cfg.get("providers", {})
        commercial = providers.get("commercial", {})
        if isinstance(commercial, dict):
            for provider_key, provider_cfg in commercial.items():
                if not isinstance(provider_cfg, dict):
                    continue
                for model_entry in provider_cfg.get("models", []):
                    if isinstance(model_entry, dict) and model_entry.get("id") == model_id:
                        return provider_key

        local = providers.get("local", {})
        if isinstance(local, dict):
            for provider_key, provider_cfg in local.items():
                if not isinstance(provider_cfg, dict):
                    continue
                for model_entry in provider_cfg.get("models", []):
                    if isinstance(model_entry, dict) and model_entry.get("id") == model_id:
                        return provider_key

    return None


def get_installed_ollama_models(force_refresh: bool = False) -> set[str]:
    """Gibt die Menge der installierten Ollama-Modellnamen zurück.

    Nutzt prozess-lokalen Cache, um nicht für jede Card einen Subprocess zu starten.
    Bei force_refresh=True wird der Cache ignoriert (z.B. nach 'ollama pull').
    """
    if _OLLAMA_MODEL_CACHE.value is not None and not force_refresh:
        return _OLLAMA_MODEL_CACHE.value

    installed: set[str] = set()
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        logger.debug("Ollama-Binary nicht gefunden — setze installierte Modelle = ∅")
        _OLLAMA_MODEL_CACHE.value = installed
        return installed

    try:
        result = subprocess.run(
            [ollama_path, "list"],
            capture_output=True,
            text=True,
            check=True,
            timeout=TIMEOUT_OLLAMA_LIST_FAST,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        logger.warning("'ollama list' fehlgeschlagen: %s — Cache bleibt leer", exc)
        _OLLAMA_MODEL_CACHE.value = installed
        return installed

    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line or line.lower().startswith("name"):
            continue
        parts = line.split()
        if parts:
            installed.add(parts[0])
    _OLLAMA_MODEL_CACHE.value = installed
    return installed


def is_ollama_model_installed(model_name: str) -> bool:
    """Prüft, ob ein Ollama-Modell lokal installiert ist (case-sensitive).

    Akzeptiert auch Namen mit 'ollama/'-Präfix — wird gestrippt.
    'gemma3:12b' und 'gemma3:12b-q8_0' müssen ganzheitlich erkannt werden.
    """
    if not model_name:
        return False
    bare = model_name
    if bare.startswith("ollama/"):
        bare = bare.replace("ollama/", "", 1)
    return bare in get_installed_ollama_models()


def is_api_provider_available(provider: str) -> bool:
    """Prüft, ob der API-Provider einen gesetzten Key hat und in der Liste ist."""
    env_var = _PROVIDER_ENV_VARS.get(provider.lower())
    if not env_var:
        return False
    return bool(os.environ.get(env_var, "").strip())


def validate_untested_card(card: dict[str, Any]) -> tuple[bool, str | None]:
    """Prüft, ob eine untested-Card prinzipiell testbar ist.

    Returns:
        (True, None) wenn testbar.
        (False, "Grund") wenn nicht erreichbar.
    """
    if not isinstance(card, dict):
        return False, "card_invalid_type"

    model_id = (card.get("model_id") or "").strip()
    if not model_id:
        return False, "missing_model_id"

    provider = (card.get("provider") or "").lower().strip()
    if not provider:
        # 1) Exakter Config-Lookup (SSOT) für lokale/commercial Modell-IDs.
        inferred = _infer_provider_from_config(model_id)
        if inferred:
            provider = inferred

        # 2) Nur für klar erkennbare Namensformate heuristischer Fallback.
        if not provider and (":" in model_id or "/" in model_id):
            try:
                provider, _ = resolve_provider(model_id)
            except Exception:  # pylint: disable=broad-exception-caught
                provider = ""
        if not provider:
            return False, "missing_provider"

    # Lokale Ollama-Modelle: prüfen ob installiert
    if provider in ("ollama", "ollama_local"):
        if not is_ollama_model_installed(model_id):
            return False, f"ollama_model_not_installed:{model_id}"
        return True, None

    # llama.cpp: prüfen ob Binary-Pfad gesetzt (lokale Datei muss existieren)
    if provider in ("llamacpp", "llamacpp_spark"):
        llama_path = (card.get("llama_cpp_path") or "").strip()
        if llama_path and not os.path.exists(llama_path):
            return False, f"llamacpp_path_missing:{llama_path}"
        # Wenn kein expliziter Pfad → wir vertrauen auf Benchmark-Lauf
        return True, None

    # vLLM: lokale Modelle werden über TOML in ~/ai/shared/configs/vllm/models/
    # ausgewählt — die Existenz wird vom vllm-start-Skript geprüft, kein
    # lokaler Datei-Check im Python-Code möglich (TOML liegt auf Remote-Host).
    if provider == "vllm_spark":
        return True, None

    # API-Provider: prüfen ob ENV-Var gesetzt
    if provider in _PROVIDER_ENV_VARS:
        if not is_api_provider_available(provider):
            return False, f"api_key_missing:{_PROVIDER_ENV_VARS[provider]}"
        return True, None

    # OpenRouter ist ein Spezialfall: läuft über openrouter-API-Key,
    # aber Provider-Name in Cards ist 'openrouter' für Modelle wie 'anthropic/claude-...'
    if provider == "openrouter":
        if not is_api_provider_available("openrouter"):
            return False, "api_key_missing:OPENROUTER_API_KEY"
        return True, None

    # Unbekannter Provider → nicht testbar
    return False, f"unknown_provider:{provider}"


def filter_testable_cards(
    cards: list[tuple[str, str]],
    card_lookup: dict[str, dict[str, Any]] | None = None,
) -> tuple[list[tuple[str, str]], list[tuple[str, str, str]]]:
    """Filtert eine Liste von (model_id, display_name) Tupeln nach Erreichbarkeit.

    Args:
        cards: Liste von (model_id, display_name) Tupeln.
        card_lookup: Optional dict[model_id → card-dict]. Wenn None, wird
                     _collect_untested_tooluse_cards() nochmal aufgerufen.

    Returns:
        (testable, unreachable) wobei unreachable = [(model_id, name, reason), ...]
    """
    if card_lookup is None:
        card_lookup = {}
        for mid, _ in cards:
            card_path_candidate = f"benchmark_scores/model_cards/{mid}.json"
            if not os.path.exists(card_path_candidate):
                logger.warning(
                    "Pre-Flight-Card nicht gefunden (model=%s, path=%s) — "
                    "falle auf unknown_provider zurück",
                    mid,
                    card_path_candidate,
                )
                continue
            try:
                import json
                with open(card_path_candidate, encoding="utf-8") as f:
                    card_lookup[mid] = json.load(f)
            except (OSError, ValueError) as exc:
                logger.warning(
                    "Pre-Flight-Card konnte nicht gelesen werden (model=%s, path=%s): %s — "
                    "falle auf unknown_provider zurück",
                    mid,
                    card_path_candidate,
                    exc,
                )
                continue

    testable: list[tuple[str, str]] = []
    unreachable: list[tuple[str, str, str]] = []
    for mid, name in cards:
        card = card_lookup.get(mid, {"model_id": mid, "provider": "unknown"})
        ok, reason = validate_untested_card(card)
        if ok:
            testable.append((mid, name))
        else:
            unreachable.append((mid, name, reason or "unknown"))
    return testable, unreachable
