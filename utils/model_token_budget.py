"""Token-Budget-Auflösung: kombiniert Reasoning-, Size-Class- und Card-Informationen.

Importiert aus ``model_card_io``, ``model_thinking`` und ``model_size_class``.
"""
import json
import logging

from utils.model_card_io import _find_card
from utils.model_size_class import get_model_size_class
from utils.model_thinking import (
    _read_max_output_tokens_from_card,
    is_reasoning_model,
    is_thinking_optional_from_card,
    resolve_effective_thinking,
)

logger = logging.getLogger(__name__)


def _apply_provider_thinking_override(
    model: str,
    provider: str | None,
    requested_max_tokens: int | None,
    reasoning: bool,
) -> bool | None:
    """Lädt Provider-Card, wendet ggf. thinking_override an, gibt effektives Reasoning zurück."""
    if not provider:
        return None
    # Option B: Provider-Override gewinnt, wenn aktiv.
    #
    # WARNUNG: Diese Branch lädt über load_vendor_card() die FIRMEN-Karte
    # (z.B. benchmark_scores/vendor_cards/anthropic.json), NICHT die
    # modell-spezifische Config aus provider_config.yaml. resolve_effective_thinking()
    # erwartet einen model_cfg-Block mit optionalem "thinking_override"-Key,
    # der in Firmen-Cards nicht vorhanden ist. Die Branch ist daher
    # funktional, aber der Override-Mechanismus wird nie ausgelöst.
    #
    # TODO: Entweder den provider-Parameter entfernen (kein Caller nutzt ihn),
    # oder das Datenmodell korrigieren: model_cfg aus provider_config.yaml laden
    # statt der Firmen-Card. Bis dahin: graceful fallback auf Card-Probe-Pfad.
    from utils.vendor_card_template import load_vendor_card
    provider_card = load_vendor_card(provider)
    if not provider_card:
        return None

    # Model-Card muss für Probe-SSoT geladen werden.
    model_card_dict: dict = {}
    card_path = _find_card(model)
    if card_path.exists():
        try:
            model_card_dict = json.loads(card_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            model_card_dict = {}

    effective, _source = resolve_effective_thinking(
        model_card=model_card_dict,
        provider_model_cfg=provider_card,
        model_id=model,
    )
    if effective is True or effective is False:
        # Probe ODER Override hat Vorrang vor Trigger-Fallback.
        return bool(effective)
    # effective is None: keine Info → Trigger-Fallback bleibt erhalten.
    return None


def resolve_token_budget(
    model: str,
    requested_max_tokens: int | None,
    config: dict,
    module_key: str | None = None,
    *,
    provider: str | None = None,
) -> tuple[int, bool]:
    """
    Berechnet das effektive Token-Budget für einen API-Request.

    Reasoning-Modelle (z.B. magistral, o1, minimax-m2) verbrauchen interne
    Thinking-Tokens gegen dasselbe max_tokens-Kontingent wie der sichtbare Output.
    Diese Funktion ersetzt das Standard-Budget durch den erhöhten Wert aus
    `token_budgets_reasoning_models` in benchmark_config.yaml.

    SSoT-Auflösung (ab v4.7.1, Option B):
      1. Wenn ``provider`` gesetzt → Provider-Card geladen → optionaler
         ``thinking_override`` angewendet (z.B. ``value:false`` → kein 5x).
      2. Probe-Resultat aus Model-Card (``thinking_probe_detected``) gewinnt
         über Trigger-Liste.
      3. Trigger-Liste (z.B. "magistral", "o1") als Fallback.

    Args:
        model: Modell-ID (z.B. "magistral-medium-latest")
        requested_max_tokens: Vom base_runner injiziertes Modul-Budget (kann None sein)
        config: Vollständige benchmark_config (self.config im Provider)
        module_key: Modul-Schlüssel aus base_runner (z.B. "cultural_intelligence")
        provider: Optional. Wenn gesetzt, wird die Provider-Card geladen und
            ein aktiver ``thinking_override`` angewendet (Cost-Benchmarks,
            A/B-Tests). None (default) = backward-compat: nur Card-Probe +
            Trigger-Fallback via ``is_reasoning_model()``.

    Returns:
        tuple[int, bool]: (effektives_budget, is_reasoning)
    """
    # Backward-compat: aktueller Pfad (Card-Probe via is_reasoning_model,
    # das intern Trigger-Fallback hat).
    reasoning = is_reasoning_model(model)

    # Option B: Provider-Override gewinnt, wenn aktiv.
    override_result = _apply_provider_thinking_override(
        model, provider, requested_max_tokens, reasoning,
    )
    if override_result is not None:
        reasoning = override_result

    explicit_budget = requested_max_tokens is not None
    tokens: int = requested_max_tokens or config.get("defaults", {}).get("generation", {}).get("num_predict", 8192)

    if reasoning and explicit_budget:
        budgets = config.get("token_budgets_reasoning_models", {})
        tokens = budgets[module_key] if (module_key and module_key in budgets) else tokens * 5
    elif reasoning:
        # Ohne explicit_budget: Mindest-Budget für Reasoning-Modelle sicherstellen.
        # max() statt fester Schwelle — robust auch wenn defaults.generation.num_predict
        # in der Config >= 10000 konfiguriert ist.
        tokens = max(tokens, 25000)
    elif is_thinking_optional_from_card(model) and explicit_budget:
        # Thinking-Optional models (e.g. Gemini 2.5 Flash, Qwen3) activate internal
        # thinking adaptively and consume the same max_output_tokens quota.
        # Grant the reasoning budget so visible output is not crowded out.
        budgets = config.get("token_budgets_reasoning_models", {})
        tokens = budgets[module_key] if (module_key and module_key in budgets) else tokens * 2

    elif not reasoning and explicit_budget and module_key:
        # Kleine lokale Modelle (Desktop, Edge, Nano, Workstation): GGUF-Quantisierungen
        # haben strukturell kürzere effektive Ausgabefenster und truncaten bei bestimmten
        # aufwendigen Modulen (z.B. documentation_quality_005, ux_writing).
        # Falls token_budgets_small_models > Standard-Budget → erhöhtes Budget anwenden.
        _size = get_model_size_class(model)
        if _size in ("Nano", "Edge", "Desktop", "Workstation"):
            _small_budgets = config.get("token_budgets_small_models", {})
            _small_budget = _small_budgets.get(module_key)
            if _small_budget and _small_budget > tokens:
                tokens = _small_budget

    # Model-Card-Cap: Wenn die Card ein explizites max_output_tokens definiert,
    # wird das Budget darauf begrenzt. So können modellspezifische API-Limits
    # (z.B. gpt-4o-2024-05-13 akzeptiert max. 4096) ohne Fallback-Retry gesetzt werden.
    card_cap = _read_max_output_tokens_from_card(model)
    if card_cap is not None:
        tokens = min(tokens, card_cap)

    return tokens, reasoning
