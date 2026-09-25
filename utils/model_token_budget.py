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

# --- Budget-Multiplikatoren (Review 2026-08-15: vorher Magic Numbers) ---------
# Reasoning-Modelle mit explizitem Budget, aber ohne modulspezifischen
# token_budgets_reasoning_models-Eintrag: 5x-Multiplikator (Chain-of-Thought
# konsumiert das gleiche Ausgabefenster wie die sichtbare Antwort).
REASONING_BUDGET_MULTIPLIER = 5

# Thinking-Optional-Modelle (adaptive interne Planung im Standard-Modus):
# 2x-Multiplikator, damit die sichtbare Ausgabe nicht verdrängt wird.
THINKING_OPTIONAL_BUDGET_MULTIPLIER = 2

# Mindest-Budget für Reasoning-Modelle ohne explizites Budget — stellt
# sicher, dass Chain-of-Thought nicht am Default-num_predict truncatet.
REASONING_MIN_BUDGET_TOKENS = 25000


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


def _reasoning_module_budget(
    config: dict,
    module_key: str | None,
    pc_calibrated_budget: int | None,
) -> int | None:
    """Modul-Budget für Reasoning-/Thinking-Optional-Pfade (PC-Card-First).

    PC v3: Eine Card-Kalibrierung (Token-Probe) gewinnt über den Config-
    Eintrag (Card-First-Lookup-Pattern wie thinking_probe_detected).
    """
    if pc_calibrated_budget is not None:
        return pc_calibrated_budget
    if module_key:
        return config.get("token_budgets_reasoning_models", {}).get(module_key)
    return None


def _small_model_budget_boost(
    tokens: int, model: str, config: dict, module_key: str | None,
) -> int:
    """Erhöhtes Budget für kleine lokale Modelle (GGUF-Ausgabefenster).

    Kleine lokale Modelle (Nano, Edge, Desktop, Workstation): GGUF-Quantisierungen
    haben strukturell kürzere effektive Ausgabefenster und truncaten bei bestimmten
    aufwendigen Modulen (z.B. documentation_quality_005, ux_writing).
    """
    if get_model_size_class(model) not in ("Nano", "Edge", "Desktop", "Workstation"):
        return tokens
    small_budget = config.get("token_budgets_small_models", {}).get(module_key)
    if small_budget and small_budget > tokens:
        return small_budget
    return tokens


def _apply_cot_calibration_floor(tokens: int, model: str, module_key: str | None) -> int:
    """Eskalationsleiter Card-First (2026-09-19): persistierte Kalibrierung hebt Stufe 1 an.

    Eine persistierte ``cot_budget_calibration`` (geschrieben von
    ``base_runner._persist_cot_calibration_if_earned`` nach einer erfolgreichen
    Eskalationsstufe) wird via ``max()`` zum Start-Budget — kein erneutes
    Durchklettern der Stufen bei Folgeläufen (Muster: pc_token_calibration
    Card-First). Gilt für alle Module außer PC (die eigene v3-Leiter mit
    Thinking-Off ist dort autoritativ); Dual-Profile teilen die Card
    (``card_model_id``), die Kalibrierung gilt also für beide Profile.
    """
    if module_key == "political_compass":
        return tokens
    cot_calibrated = get_calibrated_cot_budget(model)
    if cot_calibrated is not None and cot_calibrated > tokens:
        return cot_calibrated
    return tokens


def resolve_token_budget(
    model: str,
    requested_max_tokens: int | None,
    config: dict,
    module_key: str | None = None,
    *,
    provider: str | None = None,
    exact: bool = False,
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

    PC v3 Token-Probe (2026-08-29):
      - Für ``module_key="political_compass"`` gewinnt eine Card-Kalibrierung
        (``pc_token_calibration.budget`` aus dem Token-Probe) über den
        Config-Modul-Budget-Eintrag (Card-First-Lookup-Pattern).
      - ``exact=True`` umgeht Modul-Budget/Multiplikator komplett — der
        angefragte Wert gewinnt exakt (nur der Card-Cap bleibt). Genutzt vom
        PC-Token-Probe für Stufen unterhalb des Modul-Budgets.

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

    # PC v3 Token-Probe: Exact-Modus umgeht Modul-Budget/Multiplikator komplett
    # (Probe-Stufen 300/600 liegen UNTER dem Modul-Budget — max()-Semantik würde
    # sie still anheben und die Stufen-Differenzierung zerstören).
    if exact and explicit_budget:
        card_cap = _read_max_output_tokens_from_card(model)
        if card_cap is not None:
            tokens = min(tokens, card_cap)
        return tokens, reasoning

    # PC v3 Token-Probe: Card-Kalibrierung gewinnt über den Config-Modul-Eintrag
    # (Card-First-Lookup-Pattern wie thinking_probe_detected).
    pc_calibrated_budget = (
        get_calibrated_pc_budget(model) if module_key == "political_compass" else None
    )

    if reasoning and explicit_budget:
        module_budget = _reasoning_module_budget(config, module_key, pc_calibrated_budget)
        if module_budget is not None:
            # Modul-Budget ist das MINIMUM (Comparability über Provider hinweg —
            # der Standard-Pfad vom base_runner requested exakt diesen Wert).
            # Explizit höhere Requests gewinnen (PC v3 Truncation-Re-Ask:
            # Budget-×2-Eskalation muss das Modul-Budget durchbrechen können).
            tokens = max(module_budget, tokens)
        else:
            tokens = tokens * REASONING_BUDGET_MULTIPLIER
    elif reasoning:
        # Ohne explicit_budget: Mindest-Budget für Reasoning-Modelle sicherstellen.
        # max() statt fester Schwelle — robust auch wenn defaults.generation.num_predict
        # in der Config >= 10000 konfiguriert ist.
        tokens = max(tokens, REASONING_MIN_BUDGET_TOKENS)
    elif is_thinking_optional_from_card(model) and explicit_budget:
        # Thinking-Optional models (e.g. Gemini 2.5 Flash, Qwen3) activate internal
        # thinking adaptively and consume the same max_output_tokens quota.
        # Grant the reasoning budget so visible output is not crowded out.
        # Gleiche max()-Semantik wie oben: Modul-Budget als Minimum, explizite
        # Eskalation (PC v3 Re-Ask) gewinnt.
        module_budget = _reasoning_module_budget(config, module_key, pc_calibrated_budget)
        if module_budget is not None:
            tokens = max(module_budget, tokens)
        else:
            tokens = tokens * THINKING_OPTIONAL_BUDGET_MULTIPLIER

    elif not reasoning and explicit_budget and module_key:
        tokens = _small_model_budget_boost(tokens, model, config, module_key)

    # Eskalationsleiter Card-First (2026-09-19): Eine persistierte
    # cot_budget_calibration hebt Stufe 1 an — max(Modul-Budget, Kalibrierung).
    tokens = _apply_cot_calibration_floor(tokens, model, module_key)

    # Model-Card-Cap: Wenn die Card ein explizites max_output_tokens definiert,
    # wird das Budget darauf begrenzt. So können modellspezifische API-Limits
    # (z.B. gpt-4o-2024-05-13 akzeptiert max. 4096) ohne Fallback-Retry gesetzt werden.
    card_cap = _read_max_output_tokens_from_card(model)
    if card_cap is not None:
        tokens = min(tokens, card_cap)

    return tokens, reasoning


def read_pc_calibration(model_id: str) -> dict | None:
    """Liest ``pc_token_calibration`` aus der Model Card (PC v3 Token-Probe).

    Erwartetes Card-Feld (geschrieben von scripts/tools/pc_calibrate.py --probe):
        {"budget": int | None, "classification": "self_limiting" | "inconsistent" |
         "greedy_uncapped", "tested": ISO-Datum, "converged_stage": int | None,
         "notes": str}

    Returns:
        Kalibrierungs-Dict oder None (keine Card / kein Feld / Lesefehler).
    """
    card_path = _find_card(model_id)
    if not card_path.exists():
        return None
    try:
        data = json.loads(card_path.read_text(encoding="utf-8"))
        cal = data.get("pc_token_calibration")
        if isinstance(cal, dict) and cal.get("classification"):
            return cal
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Card-Lesefehler (pc_token_calibration) für %s: %s", card_path, exc)
    return None


def get_calibrated_pc_budget(model_id: str) -> int | None:
    """Kalibriertes PC-Budget aus der Card — nur für konvergente Klassifikationen.

    ``greedy_uncapped``-Modelle bekommen bewusst KEIN erhöhtes Budget (None):
    ihr CoT terminiert nicht — mehr Budget verbrennt nur Zeit (Kalibrierungs-
    befund Gemma-4: 800/4000/8000 jeweils voll ausgeschöpft). Diese Modelle
    laufen im Instruct-Modus bzw. mit dem Config-Modul-Budget weiter.
    """
    cal = read_pc_calibration(model_id)
    if cal is None:
        return None
    if cal.get("classification") not in ("self_limiting", "inconsistent"):
        return None
    budget = cal.get("budget")
    if isinstance(budget, int) and budget > 0:
        return budget
    return None


def read_pc_profile_flag(model_id: str) -> bool:
    """Liest ``pc_profile_forced_instruct`` aus der Model Card.

    Card-getriebener Transparenz-Pfad für Instruct-Ersatz-Läufe nach der
    Coverage-Regel (Konzept-Doc Abschn. 11) — unabhängig vom Token-Probe:
    Das Modell läuft aus Verlustgründen im Instruct-Modus, nicht wegen einer
    ``greedy_uncapped``-Klassifikation. Der Flag landet im PC-Report
    (``statistics.pc_calibration``) und in der Bias-Report-Annotation.
    """
    card_path = _find_card(model_id)
    if not card_path.exists():
        return False
    try:
        data = json.loads(card_path.read_text(encoding="utf-8"))
        return bool(data.get("pc_profile_forced_instruct"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Card-Lesefehler (pc_profile_forced_instruct) für %s: %s", card_path, exc)
        return False


def read_cot_calibration(model_id: str) -> dict | None:
    """Liest ``cot_budget_calibration`` aus der Model Card (Eskalationsleiter).

    Erwartetes Card-Feld (geschrieben von
    ``base_runner._persist_cot_calibration_if_earned`` nach einer erfolgreichen
    Eskalationsstufe):
        {"calibrated_budget": int, "stage": int, "tested": ISO-Datum,
         "model_version": str | None, "notes": str}

    Returns:
        Kalibrierungs-Dict oder None (keine Card / kein Feld / Lesefehler).
    """
    card_path = _find_card(model_id)
    if not card_path.exists():
        return None
    try:
        data = json.loads(card_path.read_text(encoding="utf-8"))
        cal = data.get("cot_budget_calibration")
        if isinstance(cal, dict) and cal.get("calibrated_budget"):
            return cal
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Card-Lesefehler (cot_budget_calibration) für %s: %s", card_path, exc)
    return None


def get_calibrated_cot_budget(model_id: str) -> int | None:
    """Kalibriertes CoT-Start-Budget aus der Card (Eskalationsleiter, Card-First).

    Muster: ``get_calibrated_pc_budget``. Die Kalibrierung gilt global für alle
    Module außer ``political_compass`` (dort ist die PC-v3-Leiter mit
    Thinking-Off autoritativ). Dual-Profile teilen die Card (``card_model_id``)
    → die Kalibrierung gilt für beide Profile.
    """
    cal = read_cot_calibration(model_id)
    if cal is None:
        return None
    budget = cal.get("calibrated_budget")
    if isinstance(budget, int) and budget > 0:
        return budget
    return None
