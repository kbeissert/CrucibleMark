"""Shared model discovery utilities for benchmark worker scripts.

Extrahiert aus run_score_benchmark.py und run_political_compass_benchmark.py
(identische Implementierungen) — DRY-Konsolidierung gemäß SSOT-Regel.
"""

from __future__ import annotations

from typing import Any

from utils.model_utils import get_commercial_models_from_config, get_ollama_models_info


def discover_local_models(config: dict[str, Any]) -> list[str]:
    """Gibt alle lokalen Modell-IDs zurück (Ollama + llamacpp)."""
    models: list[str] = []

    # Dynamische Ollama-Discovery
    for item in get_ollama_models_info():
        name = item.get("name")
        if isinstance(name, str) and name:
            models.append(name)

    # Explizite llamacpp-Modellliste
    lcpp_cfg = config.get("providers", {}).get("local", {}).get("llamacpp", {})
    if lcpp_cfg.get("enabled", False):
        for m in lcpp_cfg.get("models", []):
            mid = m.get("id") if isinstance(m, dict) else None
            if isinstance(mid, str) and mid:
                models.append(mid)

    return list(dict.fromkeys(models))


def discover_commercial_models(config: dict[str, Any]) -> list[str]:
    """Gibt alle kommerziellen Modell-IDs aus der Config zurück."""
    tuples = get_commercial_models_from_config(config)
    ids = [mid for mid, _, _ in tuples if mid]
    return list(dict.fromkeys(ids))


def discover_models(provider_filter: str, config: dict[str, Any]) -> list[str]:
    """Gibt Modell-IDs gefiltert nach Provider-Scope zurück.

    Args:
        provider_filter: "local", "commercial" oder "all"
        config: Benchmark-Konfiguration

    Returns:
        Deduplizierte Liste von Modell-IDs.
    """
    if provider_filter == "local":
        return discover_local_models(config)
    if provider_filter == "commercial":
        return discover_commercial_models(config)

    # "all": beide Quellen zusammenführen
    models = discover_local_models(config)
    models.extend(discover_commercial_models(config))
    return list(dict.fromkeys(models))
