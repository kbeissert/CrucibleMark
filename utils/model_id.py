"""Canonical/Identity: kanonische Model-IDs, Kategorisierung, Identität.

Importiert aus ``model_card_io`` und ``model_id_base``. ``model_thinking``-
Importe sind einseitig (kein Zyklus).
"""
import json
import logging
from typing import Any

from utils.model_card_io import _find_card
from utils.model_id_base import _safe_name, is_cloud_model, normalize_model_id
from utils.model_thinking import is_reasoning_model

logger = logging.getLogger(__name__)

# SSoT: weights_license_tier → display string.
# Exported so callers (e.g. scripts/web_export.py) can import without duplicating the mapping.
WEIGHTS_TIER_DISPLAY: dict[str, str] = {
    "proprietary": "Proprietär",
    "restricted-weights": "Restricted Weights",
    "open-weights": "Open Weights",
}


def resolve_canonical_model_id(
    model_id: str,
    *,
    model_cfg: dict[str, Any] | None = None,
) -> str:
    """SSoT für alle model_id-Auflösungen.

    Liefert die kanonische Schreibweise einer Model-ID, identisch mit der
    ``model_id``-Spalte in den CSVs, den Card-Dateinamen und den
    Leaderboard-Zeilen. Eingaben dürfen beliebige Schreibweisen sein
    (Punkte, Underscores, hf.co/AUTHOR/ Prefixe, Doppelpunkte).

    Pipeline
    --------
    1. ``normalize_model_id`` (strippt hf.co/AUTHOR/ Prefix)
    2. Card-Lookup: findet auch Karten, deren Dateinamen eine andere
       Schreibweise haben als die Eingabe (Punkt vs. Underscore)
    3. Wenn Card gefunden: gibt die ``model_id`` der Card zurück
       (= kanonische Form, identisch zur CSV-Spalte)
    4. Sonst: ``_safe_name(base)`` — Punkte, Doppelpunkte und Slashes
       werden zu Underscores (konventionell; Dateiname-sichere Form).

    Warum SSoT
    ---------
    Bisher wurde ``model_id`` direkt durch die Pipeline gereicht, was zu
    Mismatch zwischen CLI-Eingabe (``qwen3.5-35b-a3b-q8``) und gespeicherten
    Werten (``qwen3_5-35b-a3b-q8``) führte. Diese Funktion löst das
    Problem EINMAL an der Quelle (``UnifiedBenchmarkRunner.run_benchmark``,
    ``run_benchmark.py`` Entry-Point, ``run_tooluse_benchmark.py`` Cache-Check)
    statt punktuell in jedem Modul einen Bridge-Patch einzustreuen.

    Warum _safe_name als Fallback
    ----------------------------
    Die systemweite Konvention ist: Punkte/Doppelpunkte/Slashes in Model-IDs
    werden zu Underscores. Für Modelle MIT Card liefert ``card.model_id``
    die kanonische Form (kann auch Punkte enthalten, z.B. ``gpt-5.4-nano``
    wenn die Card das explizit so definiert). Der Fallback betrifft nur
    Modelle ohne Card — dort ist die Underscore-Form konsistent mit CSVs,
    Card-Dateinamen und Leaderboard-Einträgen.

    Beispiele
    ---------
    ``qwen3.5-35b-a3b-q8``        → ``qwen3_5-35b-a3b-q8`` (via Card-Lookup)
    ``qwen3_5-35b-a3b-q8``        → ``qwen3_5-35b-a3b-q8`` (Card direkt gefunden)
    ``gpt-5.4-nano``              → ``gpt-5.4-nano``          (via Card; card.model_id=dot-form)
    ``gpt-5_4-nano``              → ``gpt-5.4-nano``          (via Card; _safe_name findet gpt-5_4-nano.json)
    ``hf.co/x/y:Q4_K_M``          → ``y_Q4_K_M``              (kein Card → _safe_name)
    ``claude-haiku-4-5``          → ``claude-haiku-4-5-20251001`` (glob fallback)
    ``unbekanntes-modell``        → ``unbekanntes-modell``    (kein Card → _safe_name, no special chars)
    """
    if not model_id:
        return model_id
    base = normalize_model_id(model_id)

    # card_model_id-Redirect: Wenn model_cfg ein card_model_id-Feld enthält,
    # wird _find_card die Card der ORIGINAL-Modell-ID finden. Der Redirect
    # dient NUR der Card-Existenz-Prüfung — die kanonische ID des Profils
    # (z.B. ``{id}-thinking``) bleibt unverändert. Andernfalls würde
    # resolve_canonical_model_id die Original-ID zurückgeben und die
    # CSV-Spalte überschreiben (Plan: "CSV model_id bleibt {...}-thinking").
    _used_card_redirect = (
        model_cfg is not None
        and isinstance(model_cfg.get("card_model_id"), str)
        and bool(model_cfg["card_model_id"])
        and model_cfg["card_model_id"] != model_id
    )

    # Dual-Profile-Erkennung (v4.10.18):
    # SSoT für "diese Card ist Shared zwischen Standard- und Thinking-Profil"
    # ist das Card-Feld ``dual_profile: true``. Es wird vom Config-Expander
    # gesetzt und ersetzt die frühere ``-thinking``-Suffix-Heuristik.
    # model_cfg.dual_profile hat Priorität (Runtime-Config), danach Card-Feld.
    _is_dual_profile = False
    if model_cfg is not None and model_cfg.get("dual_profile"):
        _is_dual_profile = True

    try:
        card_path = _find_card(base, model_cfg=model_cfg)
    except Exception:  # noqa: BLE001
        card_path = None
    if card_path is not None and card_path.exists():
        # Card laden — wird für dual_profile-Check und model_id benötigt.
        try:
            data = json.loads(card_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):  # noqa: PERF203
            data = None

        # Card-Feld dual_profile als Fallback wenn model_cfg fehlt
        if not _is_dual_profile and isinstance(data, dict) and data.get("dual_profile"):
            _is_dual_profile = True

        # Bei Dual-Profile (Shared-Card): kanonische ID ist die EIGENE
        # Profil-ID, NICHT card.model_id der Basis-Card. Sonst verschmelzen
        # Basis- und Thinking-Profil im Leaderboard zu einer ID.
        if _used_card_redirect or _is_dual_profile:
            return _safe_name(base)

        # Standalone-Card: card.model_id zurückgeben (kanonische Form)
        if isinstance(data, dict):
            canonical = data.get("model_id")
            if isinstance(canonical, str) and canonical:
                return canonical
    # Fallback: _safe_name anwenden (systemweite Konvention: Punkte/Doppelpunkte/Slashes → Underscores).
    # Modelle MIT Card nutzen card.model_id (Pfad 3), das auch Punkte enthalten kann
    # (z.B. gpt-5.4-nano, wenn die Card das explizit so definiert).
    # Der Fallback betrifft nur Modelle ohne Card — dort ist die Underscore-Form
    # konsistent mit CSVs, Card-Dateinamen und Leaderboard-Einträgen.
    return _safe_name(base)


def enforce_card_first(
    model_id: str,
    *,
    model_cfg: dict[str, Any] | None = None,
) -> tuple[str, bool]:
    """Card-First-Vertrag: stellt sicher, dass jede geschriebene model_id eine
    Model Card besitzt.

    Pipeline
    --------
    1. ``resolve_canonical_model_id`` → kanonische Schreibweise.
    2. ``_find_card`` → Card vorhanden?
       - Ja: ``(canonical, True)``
       - Nein: ``ensure_card()`` wird aufgerufen (legt eine Card mit
         Template-Platzhaltern an), WARNING wird geloggt.
         Rückgabe ``(canonical, False)``.

    Diese Funktion ist die SSoT-Stelle, an der die Garantie
    "CSV-model == Card-model_id" erzwungen wird, ohne den Benchmark-Lauf
    abzubrechen (kein Hard-Fail). Aufrufer sollen den Rückgabewert
    ``has_card`` für Diagnose / Aggregation nutzen.

    Returns
    -------
    (canonical_model_id, has_card)
    """
    if not model_id:
        return model_id, False
    canonical = resolve_canonical_model_id(model_id, model_cfg=model_cfg)
    try:
        card_path = _find_card(canonical, model_cfg=model_cfg)
    except Exception:  # noqa: BLE001
        card_path = None
    if card_path is not None and card_path.exists():
        return canonical, True
    try:
        # Lokaler Import, um Circular-Import mit card_utils zu vermeiden.
        from utils.card_utils import ensure_card  # noqa: PLC0415
        ensure_card(canonical)
        logger.warning(
            "Card-First-Vertrag: Keine Card für '%s' gefunden → Platzhalter-Card angelegt. "
            "Bitte manuell mit echten Werten ergänzen.", canonical,
        )
        return canonical, False
    except Exception as exc:  # noqa: BLE001
        logger.error("Card-First-Vertrag: ensure_card für '%s' fehlgeschlagen: %s", canonical, exc)
        return canonical, False


def _category_from_card(model_name: str) -> str | None:
    """Liest ``weights_license_tier`` aus der Card und mappt auf Display-String."""
    card_path = _find_card(model_name)
    if not card_path.exists():
        return None
    try:
        card_data = json.loads(card_path.read_text(encoding="utf-8"))
        tier = card_data.get("weights_license_tier")
        if tier and tier in WEIGHTS_TIER_DISPLAY:
            return WEIGHTS_TIER_DISPLAY[tier]
    except Exception:
        return None
    return None


def _category_from_provider_config(
    model_name: str,
    provider: str,
) -> str | None:
    """Mappt ``model_type`` aus provider_config.yaml auf Display-String."""
    try:
        from utils.config_validator import ConfigValidator
        config = ConfigValidator().config
        commercial_providers = config.get("providers", {}).get("commercial", {})
        if provider not in commercial_providers:
            return None
        provider_config = commercial_providers[provider]
        m_type = provider_config.get("model_type", "")

        # Per-model override: check if this specific model has a model_type set
        for model_entry in provider_config.get("models", []):
            if isinstance(model_entry, dict) and model_entry.get("id") == model_name:
                override = model_entry.get("model_type")
                if override:
                    m_type = override
                break

        from utils.constants import MODEL_TYPE_OPEN_WEIGHTS_CLOUD
        if m_type == MODEL_TYPE_OPEN_WEIGHTS_CLOUD:
            return "Open Weights"
        if m_type == "proprietary_api":
            return "Proprietär"
        if m_type == "cloud":
            return "Open Weights"
    except Exception:
        return None
    return None


def _category_from_heuristics(
    model_name: str,
    source_file: str,
    size_gb: float | None,
) -> str:
    """Heuristik-Fallback für Modelle ohne Card/Config-Eintrag."""
    if source_file == "cloud" or (
        source_file == "local"
        and ("cloud" in model_name.lower() or (size_gb is not None and size_gb < 0.01))
    ):
        return "Open Weights"

    # Rule 1: Commercial CSV → Always Proprietär
    if source_file == "commercial":
        return "Proprietär"

    # Rule 2: Local CSV → cloud proxy check
    if is_cloud_model(model_name, size_gb):
        return "Open Weights"

    # Rule 3: Everything else from Local CSV → Open Weights
    return "Open Weights"


def get_model_category(
    model_name: str, source_file: str = "local", size_gb: float | None = None, provider: str | None = None
) -> str:
    """
    Central SSOT for model categorization.
    Returns one of three display strings based on weights_license_tier in model card (primary)
    or config/source heuristics (fallback).

    Args:
        model_name: Name of the model (e.g., 'ministral-3:14b', 'gpt-oss:120b-cloud')
        source_file: Source CSV file ('local' or 'commercial')
        size_gb: Optional model size in GB (for better cloud detection)
        provider: Optional provider name (from config or CSV) to determine exact grouping

    Returns:
        str: 'Proprietär' | 'Restricted Weights' | 'Open Weights'
    """
    # SSOT: Model card weights_license_tier has priority over all heuristics
    card_cat = _category_from_card(model_name)
    if card_cat is not None:
        return card_cat

    if provider:
        cfg_cat = _category_from_provider_config(model_name, provider)
        if cfg_cat is not None:
            return cfg_cat

    return _category_from_heuristics(model_name, source_file, size_gb)


def get_use_case_primary(model_id: str, card_data: dict | None = None) -> str:
    """
    Returns use_case_primary for a model, with 'generalist' as fallback.

    Args:
        model_id: Model identifier (used to locate card if card_data not provided)
        card_data: Pre-loaded card dict; if None, card is loaded from disk

    Returns:
        str: one of 'generalist' | 'coding' | 'reasoning' | 'vision-language' | 'agentic'
    """
    if card_data is not None:
        return card_data.get("use_case_primary", "generalist")

    try:
        card_path = _find_card(model_id)
        if card_path.exists():
            card = json.loads(card_path.read_text(encoding="utf-8"))
            return card.get("use_case_primary", "generalist")
    except Exception:
        pass

    return "generalist"


def get_model_identity(full_model_string: str) -> dict[str, Any]:
    """
    Parses a raw API model string and extracts friendly metadata for UI and Judge Context.
    Strips provider repository paths while retaining technical suffixes.
    Extracts tags based on model name substrings to provide additional context.

    Returns:
        dict: {
            "raw": full_model_string,
            "display_name": stripped_name,
            "tags": list_of_tags
        }
    """
    name_lower = full_model_string.lower()

    # Extract identity by stripping everything before the last slash
    display_name = full_model_string.rsplit('/', 1)[-1]

    tags = []

    # Specializations
    if any(x in name_lower for x in ["coder", "-code", "code-"]):
        tags.append("Coder")

    if is_reasoning_model(full_model_string) or any(x in name_lower for x in ["thinking"]):
        tags.append("Thinking")

    if "abliterated" in name_lower:
        tags.append("Uncensored-Abliterated")

    if "dolphin" in name_lower or "uncensored" in name_lower or "hermes" in name_lower:
        tags.append("Uncensored-Finetuned")

    if any(x in name_lower for x in ["instruct", "-it", "chat"]):
        tags.append("Instruct")

    if any(x in name_lower for x in ["preview", "experimental", "-exp"]):
        tags.append("Preview")

    # Agentic Orchestrator: Claude Opus models are designed as multi-agent orchestrators
    if "claude-opus" in name_lower:
        tags.append("Agentic-Orchestrator")

    # Thinking-Optional: Models that support toggleable extended thinking but run in standard mode
    if any(x in name_lower for x in ["qwen3", "gemini-2.5"]):
        tags.append("Thinking-Optional")

    if not tags:
        tags.append("General")

    return {
        "raw": full_model_string,
        "display_name": display_name,
        "tags": tags
    }


def get_model_specialization(model_name: str) -> str:
    """
    Classifies models by their primary training specialization.
    Used for context in Bias-Reviews to apply appropriate leniency.

    Returns: Command separated string of specializations from get_model_identity
    """
    identity = get_model_identity(model_name)
    return ", ".join(identity["tags"])
