"""Provider-Detection SSoT (Phase 23).

Einzige Quelle der Wahrheit für die Zuordnung Model-ID-Prefix → Provider-Display-Name.

Vor Phase 23 hatte CrucibleMark drei voneinander unabhängige Provider-Detection-Stellen:

1. ``scripts/analysis/review/risk_calculator.py::_CLOUD_PREFIX_TO_PROVIDER``
   — hardcoded lowercase-Prefix-Map, gibt Display-Namen für Sovereign-Risk zurück.
2. ``utils/model_utils.py::resolve_provider()``
   — Config-basiert + Heuristik, gibt ``(api_type, model_id)``-Tupel zurück.
3. ``scripts/web_export.py::build_provider_map()``
   — baut eine Map aus ``benchmark_config.yaml`` für den Web-Export.

Drei Stellen für die gleiche Logik → Drift-Risiko. Dieses Modul ist die
SSoT für die *Heuristik-Variante* (Prefix → Display-Name), die für
Sovereign-Risk-Berechnung und Reviewer-Prompt gebraucht wird.

Andere Konsumenten mit anderen Anforderungen (z.B. ``resolve_provider``
braucht zusätzlich Config-Resolution, ``build_provider_map`` braucht
Display-Namen aus Config) bleiben eigenständig, nutzen aber bei der
Heuristik diese SSoT.
"""
from __future__ import annotations

# Lowercase-Prefix → Provider-Display-Name.
#
# Matching-Regel (siehe detect_provider_from_model_id): einfacher
# ``startswith``-Check, mit Längste-Prefixes-zuerst-Iteration (greedy).
# Längere Prefixes (z.B. ``"gpt-5-"``) müssen vor kürzeren (z.B. ``"gpt-"``)
# eingetragen sein, damit ``"gpt-5.4"`` korrekt zu ``"gpt-5-"`` mapped und
# nicht zu ``"gpt-"`` fällt.
#
# Eine Wortgrenzen-Logik ("nächste Position ist Trennzeichen oder
# Stringende") wurde evaluiert, aber wieder verworfen: Sie ist mit
# gemischten Modellnamen-Patterns unvereinbar — ``"gpt-4o"`` (Ziffer an
# Position 4) würde matchen, aber ``"claude-haiku-4-5"`` (Lowercase-Letter
# an Position 7 nach ``"claude-"``) würde nicht matchen, obwohl beide
# gültige Modellnamen sind. Die echte Konvention der Provider ist
# konsistent: Familien-Prefix + Subversion, getrennt durch ``-``/``.``/``:``,
# und es gibt keine realistischen False-Positives wie ``"qwenchat"`` → Alibaba
# in den unterstützten Modellnamen. Falls solche False-Positives in Zukunft
# auftauchen, sollte die Liste der erlaubten Modellnamen whitelist-basiert
# gepflegt werden, nicht per Wortgrenzen-Heuristik.
PROVIDER_PREFIX_MAP: dict[str, str] = {
    # OpenAI — längste Prefixes zuerst
    "gpt-oss-": "OpenAI",
    "gpt-5-": "OpenAI",
    "gpt-4-": "OpenAI",
    "gpt-3-": "OpenAI",
    "gpt-": "OpenAI",
    "o1-": "OpenAI",
    "o3-": "OpenAI",
    "o4-": "OpenAI",
    "o1": "OpenAI",
    "o3": "OpenAI",
    "o4": "OpenAI",
    # Anthropic
    "claude-": "Anthropic",
    # Google — längste zuerst
    "gemini-": "Google",
    "gemma-": "Google",
    "gemma": "Google",
    # Mistral AI — längste zuerst
    "codestral-": "Mistral AI",
    "ministral-": "Mistral AI",
    "pixtral-": "Mistral AI",
    "mistral-": "Mistral AI",
    "codestral": "Mistral AI",
    "ministral": "Mistral AI",
    "pixtral": "Mistral AI",
    "mistral": "Mistral AI",
    # xAI
    "grok-": "xAI",
    # DeepSeek
    "deepseek-": "DeepSeek",
    # Alibaba Cloud
    "qwen-": "Alibaba Cloud",
    "qwen": "Alibaba Cloud",
    # Moonshot AI
    "kimi-": "Moonshot AI",
    "kimi": "Moonshot AI",
    # Meta
    "llama-": "Meta",
    "llama": "Meta",
    # MiniMax (Sonderfall: Prefix mit eigener Naming-Konvention)
    "minimax-": "MiniMax",
    "minimax": "MiniMax",
    # Microsoft
    "phi-": "Microsoft",
    "phi": "Microsoft",
    # Cohere
    "command-": "Cohere",
    "command": "Cohere",
    # Perplexity
    "sonar-": "Perplexity",
    "pplx-": "Perplexity",
}


def detect_provider_from_model_id(model_id: str) -> str | None:
    """Mappt eine Model-ID auf den Provider-Display-Namen.

    Args:
        model_id: Model-ID (z.B. ``"gpt-4o"``, ``"claude-3-5-sonnet"``,
                  ``"qwen2.5-14b"``). Case-insensitive.

    Returns:
        Display-Name des Providers (z.B. ``"OpenAI"``, ``"Anthropic"``) oder
        ``None`` wenn kein Match (→ vermutlich lokal gehostetes Modell).

    Note:
        Diese Funktion kennt KEINE benchmark_config.yaml. Sie ist eine reine
        Heuristik für die Sovereign-Risk-Berechnung. Für Config-basierte
        Auflösung siehe ``utils.model_utils.resolve_provider``.
    """
    if not model_id:
        return None
    normalized = model_id.lower()
    for prefix, provider_name in PROVIDER_PREFIX_MAP.items():
        if normalized.startswith(prefix):
            return provider_name
    return None
