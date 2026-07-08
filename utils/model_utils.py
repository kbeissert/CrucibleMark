"""
Utility functions for model management and filtering.
"""

import json
import logging
import re
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Any, Literal, Optional, TypeVar

import yaml
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)
from utils.constants import (
    MODEL_TYPE_OPEN_WEIGHTS_CLOUD,
    TIMEOUT_OLLAMA_VERSION,
    TIMEOUT_OLLAMA_LIST,
)

T = TypeVar("T")

# Provider short codes — mirrors benchmark_config.yaml → providers.<name>.short_code
# This dict provides fast in-process lookup without YAML I/O on every call.
#
# Schema-Konvention für lokale Inference-Provider (max. 4 Zeichen):
#   Optionaler Engine-Prefix (1 Zeichen) + Hardware-Kürzel (max. 3 Zeichen)
#     V=vLLM, kein Prefix=llama.cpp → Engine über Präfix unterscheidbar
#     M4xx = Apple M4 (MacBook Pro)
#     SPK  = DGX Spark / asusGX10
# Beispiel:
#     M4APL = Mac M4 Apple + llama.cpp
#     SPRK  = Spark + llama.cpp
#     VSPK  = vLLM + Spark
#     VM4   = vLLM + Mac (hypothetisch zukünftig)
# API-Provider und Cloud-Proxies folgen einer einfacheren Regel: 2–3 Buchstaben
# (API, OR, GR) — dort ist die Engine fix (HTTP-JSON).
_PROVIDER_SHORTCODES: dict[str, str] = {
    # Proprietary direct APIs (HTTP-JSON, keine Engine-Diskrimination nötig)
    "anthropic": "API",
    "openai": "API",
    "google": "API",
    "xai": "API",
    "mistral": "API",
    # Cloud inference proxies (HTTP-JSON)
    "openrouter": "OR",
    "groq": "GR",
    # Local runtime (Ollama, LM Studio, etc.)
    "ollama": "LCL",
    "ollama_local": "LCL",
    "local": "LCL",
    # llama.cpp local inference server (OpenAI-compatible) — kein V-Prefix
    "llamacpp": "M4APL",        # Mac M4 Apple + llama.cpp
    "llamacpp_spark": "SPRK",   # DGX Spark + llama.cpp
    "llama_cpp": "M4APL",       # Alias
    "llamacpp_local": "M4APL",  # Alias
    # vLLM local inference server (OpenAI-compatible) — V-Prefix für Engine
    "vllm_spark": "VSPK",       # asusGX10/DGX Spark + vLLM
    # Ollama as cloud proxy (e.g. qwen3.5:397b-cloud via remote Ollama endpoint)
    "ollama_cloud": "CLD",
}


def get_provider_shortcode(provider: str) -> str:
    """Returns the configured short code for a provider (e.g. 'openrouter' → 'OR').

    SSoT: benchmark_config.yaml → providers.<name>.short_code.
    Falls back to the provider name uppercased (max 4 chars) if not in the mapping.
    """
    return _PROVIDER_SHORTCODES.get(str(provider).lower().strip(), str(provider).upper()[:4])


# ---------------------------------------------------------------------------
# Hardware profile lookup — SSoT for local provider hardware identification
# ---------------------------------------------------------------------------

_LOCAL_PROVIDER_NAMES: tuple[str, ...] = (
    "ollama", "llamacpp", "llamacpp_spark", "llama_cpp", "llamacpp_local",
    "vllm_spark",
)

_PROVIDER_ALIAS_MAP: dict[str, str] = {
    "llama_cpp": "llamacpp",
    "llamacpp_local": "llamacpp",
    "ollama": "ollama_local",
}


def get_hardware_profile(config: dict, provider: str) -> str | None:
    """Returns the hardware_profile key for a local provider from config.

    SSoT: providers.local.<provider>.hardware_profile in benchmark_config.yaml.
    Returns None for cloud/commercial providers or on error.

    Args:
        config: The full benchmark config dict (benchmark_config.yaml).
        provider: Provider name (e.g. 'llamacpp', 'ollama').
    """
    provider_l = str(provider).lower().strip()
    if provider_l not in _LOCAL_PROVIDER_NAMES:
        return None

    provider_key = _PROVIDER_ALIAS_MAP.get(provider_l, provider_l)

    try:
        local_cfg = config.get("providers", {}).get("local", {})
        profile = local_cfg.get(provider_key, {}).get("hardware_profile")
        if profile:
            return profile
        # Backward-compatible fallback for older configs.
        return local_cfg.get("config", {}).get("hardware_profile")
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# model_version Pollution Audit (Phase 48)
# ---------------------------------------------------------------------------
# Quant/Format-Token, die im ``model_version``-Feld nichts zu suchen haben.
# Das Feld soll reine Versions-/Datums-Infos tragen (z.B. "3.5", "4.0",
# "20251001"). Tokens wie "Q4_K_XL", "FP8", "GGUF" sind Engine-/Format-Infos
# und gehören in das separate ``quantization_format``-Feld der Card.
#
# Achtung: Bestehende Cards tragen diese Tokens oft im model_version (Audit
# ergab ~30 Karten, Stand Phase 48). Diese Funktion ändert KEINE Bestandsdaten
# — das würde die Leaderboard-Groupby-Continuity brechen (model_version ist
# Groupby-Key in score_calculator.py). Sie ist defensiv für NEUE Schreibvorgänge
# und Grundlage für den Audit-Report.
_QUANT_FORMAT_TOKENS: tuple[str, ...] = (
    "GGUF", "Q2_K", "Q3_K", "Q4_0", "Q4_1", "Q4_K", "Q4_K_M", "Q4_K_S",
    "Q5_0", "Q5_1", "Q5_K", "Q5_K_M", "Q5_K_S", "Q6_K", "Q8_0", "Q8_K",
    "FP8", "FP16", "FP32", "BF16", "INT4", "INT8", "AWQ", "GPTQ", "NVFP4",
    "QAT", "UD", "MTP", "MLX",
)


def model_version_has_quant_pollution(value: str | None) -> bool:
    """True wenn *value* Quant/Format-Tokens enthält.

    Use Cases:
    - Audit-Script: scannt Cards und meldet, wo model_version quantifiziert ist.
    - Card-Generator (Zukunft): kann warnen, wenn ein neuer Generator-Wert
      Tokens enthält, die in ``quantization_format`` gehören.
    - Read-Side: defensive Validierung für Werte aus user-editierten Cards.

    Pure-Version-Werte wie ``"3.5"``, ``"4.0"``, ``"20251001"``, ``"latest"``
    liefern False. Werte wie ``"4 (Q4_K_XL GGUF)"``, ``"1.0-FP8"``,
    ``"UD-Q8_K_XL (GGUF)"`` liefern True.
    """
    if not value:
        return False
    upper = str(value).upper()
    return any(token in upper for token in _QUANT_FORMAT_TOKENS)


# ---------------------------------------------------------------------------
# Card path helpers — SSoT for all model card filename operations
# ---------------------------------------------------------------------------

CARD_DIR = Path("benchmark_scores/model_cards")

# Matches Ollama's HuggingFace registry prefix: hf.co/AUTHOR/model:tag
_HF_OLLAMA_RE = re.compile(r"^hf\.co/[^/]+/(.+)$")


def normalize_model_id(model_id: str) -> str:
    """Strip Ollama HuggingFace registry prefix for stable canonical IDs.

    hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M
        → NousResearch_Hermes-4-14B-GGUF:Q4_K_M

    All other model IDs are returned unchanged. This keeps filesystem paths,
    CSV rows, and card filenames consistent regardless of whether the full
    Ollama hf.co/AUTHOR/ prefix was used at invocation time.
    """
    m = _HF_OLLAMA_RE.match(model_id)
    return m.group(1) if m else model_id


def _safe_name(model_id: str) -> str:
    """Canonical filename-safe transformation for model IDs.

    Normalizes HuggingFace Ollama IDs first (strips hf.co/AUTHOR/ prefix),
    then replaces every character in ``[:/.  ]`` (colon, slash, dot, space) with an underscore.
    SSoT — used by all card path helpers in this module and in generation scripts.
    """
    return re.sub(r"[:/. ]", "_", normalize_model_id(model_id))


# --- Public SSoT-Wrapper (Phase 1) ------------------------------------------------
# Thin wrappers over _safe_name/slugify for use cases that have semantically distinct
# intents but currently spread the _safe_name() call across 5+ files.
# The wrappers make intent explicit at the call site and centralize any future change.


def safe_name_for_filesystem(model_id: str) -> str:
    """SSoT-Wrapper: _safe_name() für Filesystem-Pfade.

    Verwendungszweck: Card-Files, Audit-Log-Dirs, Review-Ordner — überall wo
    ein Model-ID als Filesystem-Pfad-Komponente genutzt wird.
    Zentralisiert die Normalisierung an einer Stelle, sodass zukünftige
    Änderungen an der Normalisierung (z.B. neue Zeichen) nur hier gemacht werden.
    """
    return _safe_name(model_id)


def safe_slugify(model_id: str) -> str:
    """SSoT-Wrapper: slugify(_safe_name(...)) für URL- und Review-Ordner-Slugs.

    Konvertiert einen Model-ID in einen URL-/Ordner-Slug (lowercase, Bindestriche,
    keine Sonderzeichen). Wird in web_export.py für Review-Dir-Auflösung und in
    Hugo-Linking-Logik verwendet.
    """
    # Inline-Implementation statt Import aus scripts.web_export, um Zirkular-Imports
    # zu vermeiden (scripts/ hängt bereits von utils/ ab).
    name = str(model_id).rsplit("/", maxsplit=1)[-1].lower()
    slug = re.sub(r"[:/. ]", "-", name)
    return re.sub(r"-+", "-", slug).strip("-")


def normalize_for_comparison(model_id: str) -> str:
    """SSoT-Wrapper: Normalisierung für Cross-List-Vergleiche.

    Verwendungszweck: Blacklist-Matching, Set-Lookups, Deduplizierung über
    mehrere Datenquellen hinweg. Lowercase + _safe_name() damit
    ``deepseek/deepseek-chat-v3.1`` und ``DeepSeek-DeepSeek-Chat-V3_1``
    als gleichwertig erkannt werden.
    """
    return _safe_name(model_id).lower()


# --- End SSoT-Wrapper ----------------------------------------------------------------


# Version-Segment-Pattern: v + Ziffer + Underscore + Ziffer ODER
# Bindestrich + Ziffer + Underscore + Ziffer (aber NICHT reine Wort-Underscores)
_VERSION_UNDERSCORE_RE = re.compile(
    r"(?<=\d)_(?=\d)"          # digit_digit (z.B. 5_5, 3_3)
    r"|(?<=v\d)_(?=\d)"        # v + digit_digit (z.B. v2_5)
)


def internal_id_to_config_form(model_id: str) -> str:
    """Normalisiert interne Underscore-Model-IDs für Config-Lookups.

    Die kanonische interne Form nutzt Underscores statt Punkte
    (``_safe_name()``-Konvention: ``gpt-5_5-pro``, ``mimo-v2_5-pro``).
    Config-Einträge in ``provider_config.yaml`` können however Punkte
    in Versions-Segmenten nutzen (``gpt-5.5-pro``).

    Diese Funktion konvertiert Versions-Underscores zurück zu Punkten,
    damit Modell-IDs gegen Config-Einträge gematcht werden können.

    Beispiele::

        >>> internal_id_to_config_form("gpt-5_5-pro")
        'gpt-5.5-pro'
        >>> internal_id_to_config_form("gpt-5.5-pro")
        'gpt-5.5-pro'
        >>> internal_id_to_config_form("mimo-v2_5-pro")
        'mimo-v2.5-pro'
        >>> internal_id_to_config_form("grok-4_1-fast")
        'grok-4.1-fast'
        >>> internal_id_to_config_form("claude-sonnet-4-5-20250929")
        'claude-sonnet-4-5-20250929'
        >>> internal_id_to_config_form("llama-3_3-nemotron")
        'llama-3.3-nemotron'
    """
    base = model_id.rsplit(".json", 1)[0] if model_id.endswith(".json") else model_id
    return _VERSION_UNDERSCORE_RE.sub(".", base)


def find_model_in_provider_cfg(
    provider_cfg: dict[str, Any],
    model_id: str,
) -> dict[str, Any] | None:
    """Findet einen Model-Eintrag in der Provider-Config (SSoT für Config-Lookups).

    Vergleicht die übergebene ``model_id`` (interne Underscore-Form) gegen
    Config-Einträge, wobei Versions-SegmenteUnderscore→Dot normalisiert werden.

    Args:
        provider_cfg: Der Provider-Abschnitt aus ``provider_config.yaml``
            (z.B. ``config["providers"]["commercial"]["openai"]``).
        model_id: Die interne Modell-ID (z.B. ``gpt-5_5-pro``).

    Returns:
        Den Model-Eintrag-Dict wenn gefunden, sonst ``None``.
    """
    config_form = internal_id_to_config_form(model_id)
    for entry in provider_cfg.get("models", []):
        if isinstance(entry, dict):
            entry_id = entry.get("id", "")
            if entry_id == model_id or entry_id == config_form:
                return entry
    return None


def strip_date_suffix(model_id: str) -> str:
    """Entfernt Datums-/Monatssuffixe am Ende einer Model-ID (SSoT).

    Unterstuetzte Suffixe:
    - ``-YYYYMMDD`` (8-stellig, z.B. ``kimi-k2-20260211``)
    - ``-MMDD`` mit gueltigem Monat 01-12 (z.B. ``kimi-k2-0127``)

    SSoT -- ersetzt die verstreuten re.sub-Aufrufe in benchmark_auto.py,
    llamacpp_batch.py und ggf. weiteren Stellen.
    """
    if not model_id:
        return model_id
    cleaned = re.sub(r"-\d{8}$", "", model_id)
    cleaned = re.sub(r"-(0[1-9]|1[0-2])\d{2}$", "", cleaned)
    return cleaned


def resolve_canonical_model_id(model_id: str) -> str:
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
    try:
        card_path = _find_card(base)
    except Exception:  # noqa: BLE001
        card_path = None
    if card_path is not None and card_path.exists():
        try:
            data = json.loads(card_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                canonical = data.get("model_id")
                if isinstance(canonical, str) and canonical:
                    return canonical
        except (OSError, json.JSONDecodeError):  # noqa: PERF203
            pass
    # Fallback: _safe_name anwenden (systemweite Konvention: Punkte/Doppelpunkte/Slashes → Underscores).
    # Modelle MIT Card nutzen card.model_id (Pfad 3), das auch Punkte enthalten kann
    # (z.B. gpt-5.4-nano, wenn die Card das explizit so definiert).
    # Der Fallback betrifft nur Modelle ohne Card — dort ist die Underscore-Form
    # konsistent mit CSVs, Card-Dateinamen und Leaderboard-Einträgen.
    return _safe_name(base)


def enforce_card_first(model_id: str) -> tuple[str, bool]:
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
    canonical = resolve_canonical_model_id(model_id)
    try:
        card_path = _find_card(canonical)
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


_STALE_VERSIONS: frozenset[str] = frozenset({"latest", "unknown", "k.A.", ""})

# SSoT: weights_license_tier → display string.
# Exported so callers (e.g. scripts/web_export.py) can import without duplicating the mapping.
WEIGHTS_TIER_DISPLAY: dict[str, str] = {
    "proprietary": "Proprietär",
    "restricted-weights": "Restricted Weights",
    "open-weights": "Open Weights",
}


def _card_path(
    model_id: str,
    provider: str | None = None,
    *,
    for_write: bool = False,
    resolved_version: str | None = None,
) -> Path:
    """Returns the canonical Path for the model card of *model_id*.

    Naming rules
    ------------
    1. **Namespaced IDs** (contain ``/``): ``safe_name.json``
       The provider namespace is already embedded in the ID (e.g. ``moonshotai/kimi-k2-0711``).
    2. **Commercial direct-API IDs** (shortcode == ``'API'``): ``safe_name.json``
       Brand names are globally unique (``claude-sonnet-4-6``, ``gpt-5``, …).
    3. **Non-namespaced + non-API** (``LCL``, ``GR``, …): ``safe_name--{SHORTCODE}.json``
       These model IDs are *not* globally unique — the same bare name (e.g.
       ``llama3.3:70b``) can be served by multiple providers.

       SSoT: ``build_card_id()`` definiert ``{base}--{shortcode}`` als Schema.
       ``_card_path(for_write=True)`` produziert dieselbe Form, damit beide
       SSoT-Funktionen konsistent sind.

       - ``for_write=False`` (read/lookup): tries the suffixed path first; falls back
         to the legacy prefixed path (``{SHORTCODE}_safe_name.json``), then to the
         legacy unprefixed path for cards created before this convention.
       - ``for_write=True`` (card creation): always returns the suffixed path so new
         cards are stored at the canonical location.

    Parameters
    ----------
    model_id:
        The model identifier as stored in config / CSV.
    provider:
        Provider key (e.g. ``'ollama_local'``, ``'groq'``, ``'anthropic'``) or its
        shortcode.  ``None`` → treated as API / no prefix (backward compatible).
    for_write:
        When ``True``, always returns the canonical (potentially prefixed) path even
        if a legacy unprefixed file already exists — intended for card-generation code.
    resolved_version:
        When provided and the model_id ends with ``-latest`` or ``:latest``, the card
        is stored/looked up under ``{base}-{resolved_version}.json`` instead of the
        alias filename.  Ignored when version is stale (``'latest'``, ``'unknown'``, …).
    """
    # Version-specific filename for -latest aliases when version is resolved
    if (
        resolved_version
        and resolved_version.strip() not in _STALE_VERSIONS
        and (model_id.endswith("-latest") or model_id.endswith(":latest"))
    ):
        base = re.sub(r"[:-]latest$", "", model_id)
        return CARD_DIR / f"{_safe_name(base)}-{resolved_version.strip()}.json"

    safe = _safe_name(model_id)

    # Rule 1: namespaced IDs are globally unique — no prefix needed
    if "/" in model_id:
        return CARD_DIR / f"{safe}.json"

    shortcode: str | None = None
    if provider:
        shortcode = get_provider_shortcode(provider)

    # Rule 2: commercial API models or unknown provider → no prefix
    if not shortcode or shortcode == "API":
        return CARD_DIR / f"{safe}.json"

    # Rule 3: non-namespaced, non-API → provider-suffixed
    # SSoT: build_card_id() definiert {base}--{shortcode} als kanonische Form.
    # _card_path(for_write=True) muss dieselbe Form produzieren, sonst
    # widersprechen sich die beiden SSoT-Funktionen und erzeugen Duplikate.
    suffixed = CARD_DIR / f"{safe}--{shortcode}.json"
    unprefixed = CARD_DIR / f"{safe}.json"
    # Legacy: ältere Karten nutzten PREFIX-Form ({shortcode}_{safe}.json).
    # Diese Form wird beim Lesen noch gefunden, aber nie mehr zum Schreiben verwendet.
    legacy_prefixed = CARD_DIR / f"{shortcode}_{safe}.json"

    if for_write:
        return suffixed  # new cards always go to the canonical suffixed location

    # Read: prefer suffixed (new SSoT), then legacy prefixed, then unprefixed
    if suffixed.exists():
        return suffixed
    if legacy_prefixed.exists():
        return legacy_prefixed
    return unprefixed  # caller must check .exists()


# ---------------------------------------------------------------------------
# Card-ID-Generator + Konflikt-Resolver
# ---------------------------------------------------------------------------
# SSoT fuer die ID-Form NEUER Model Cards. Aeltere Karten behalten ihren
# Namen und werden ueber den Multi-Key-Helper `canonical_lookup_keys` gefunden.
# Wenn die gewuenschte ID bereits existiert, wird ein numerisches Suffix
# (``-2``, ``-3`` …) angehaengt und ein WARNING geloggt.

import logging as _logging_id  # noqa: E402

_id_logger = _logging_id.getLogger(__name__)


def build_card_id(model_id: str, provider: str | None = None) -> str:
    """Baut die ID einer NEUEN Model Card.

    Schema: ``{model_base}--{shortcode}``
    - ``model_base`` ist alles NACH dem letzten ``/`` (Namespace wird
      abgeschnitten, der Provider steckt schon im Suffix).
    - Quantisierung/Groesse sind im ``model_base`` enthalten
      (z. B. ``qwen3.5-35b-a3b-q4``, ``gemma3:9b``).
    - Der Suffix-Teil verwendet den Provider-Shortcode
      (``anthropic``, ``openrouter``, ``M4APL``, ``SPRK`` etc.).

    Beispiele
    ---------
    ``qwen/qwen3.5-35b-a3b-q4`` + ``openrouter`` → ``qwen3.5-35b-a3b-q4--OR``
    ``claude-sonnet-4-5-20250929`` + ``anthropic`` → ``claude-sonnet-4-5-20250929--anthropic``
    ``gemma3:9b`` + ``llamacpp_spark`` → ``gemma3:9b--SPRK``
    ``NousResearch_Hermes-4-14B-GGUF:Q4_K_M`` + ``ollama`` → ``NousResearch_Hermes-4-14B-GGUF:Q4_K_M--ollama``
    """
    if not model_id:
        return model_id
    base = model_id.rsplit("/", 1)[-1]  # alles vor+inkl. letztem '/' weg
    if not provider:
        return base
    shortcode = get_provider_shortcode(provider)
    # API-Modelle sind per Brand-Name global eindeutig (claude-sonnet-4-5, gpt-5, ...),
    # daher ist der Provider-Name als Suffix lesbarer als der technische 'API'-Shortcode.
    suffix = provider.lower().strip() if shortcode == "API" else shortcode
    return f"{base}--{suffix}"


def resolve_unique_card_id(desired_id: str, card_dir: Path | None = None) -> str:
    """Stellt sicher, dass die gewuenschte Card-ID im Zielverzeichnis eindeutig ist.

    Falls ``card_dir/{safe_name(desired_id)}.json`` bereits existiert, wird ein
    numerisches Suffix ``-2``, ``-3`` … an ``desired_id`` angehaengt, bis ein
    freier Name gefunden wird. Loggt ein WARNING beim ersten Konflikt.

    Der Datei-Check verwendet ``_safe_name(desired_id)``, weil ``_card_path`` die
    selbe Normalisierung anwendet (``qwen3.5-9b--SPRK`` → ``qwen3_5-9b--SPRK.json``).
    Ohne diesen Schritt wuerde der Resolver Konflikte uebersehen, sobald die
    build_card_id-Form Punkte enthaelt, die real auf der Disk als Underscores
    liegen.

    Parameters
    ----------
    desired_id:
        Die bevorzugte Card-ID (Ergebnis von ``build_card_id``).
    card_dir:
        Optionaler Override des Card-Verzeichnisses. ``None`` (Default)
        verwendet das modulweite ``CARD_DIR``.

    Returns
    -------
    Eindeutige Card-ID (kann vom Input abweichen, falls Konflikt).
    """
    _cd = card_dir if card_dir is not None else CARD_DIR
    if not desired_id:
        return desired_id
    candidate = desired_id
    suffix = 2
    while (_cd / f"{_safe_name(candidate)}.json").exists():
        collision_id = candidate
        candidate = f"{desired_id}-{suffix}"
        suffix += 1
        _id_logger.warning(
            "Card-ID-Konflikt: '%s.json' existiert bereits. "
            "Verwende '%s' als eindeutige Variante. "
            "Bitte prüfen, ob die alte Karte zusammengefuehrt werden kann.",
            _safe_name(collision_id), candidate,
        )
    return candidate


def _find_card(model_id: str, card_dir: Path | None = None) -> Path:
    """Finds an existing model card for *model_id* without knowing the provider.

    When a provider is not available at the call site (e.g. inside utility
    functions that receive only the model name), this helper tries all possible
    provider-prefixed variants in addition to the canonical unprefixed path.

    Returns the first existing path found, or the unprefixed path (which may
    not exist) as a sentinel — callers must always check ``.exists()``.

    OR-models are always namespaced (contain ``/``) and use only the unprefixed
    path; they are handled first as a fast-path.

    Parameters
    ----------
    card_dir:
        Override the card directory. ``None`` (default) uses the module-level
        ``CARD_DIR`` constant. Pass an explicit path when the caller resolves
        paths relative to a root directory (e.g. in ``scripts/web_export.py``).
    """
    _cd = card_dir if card_dir is not None else CARD_DIR
    safe = _safe_name(model_id)
    unprefixed = _cd / f"{safe}.json"

    # Namespaced IDs (OpenRouter, Groq namespaced, …) only ever use the unprefixed path
    if "/" in model_id:
        if unprefixed.exists():
            return unprefixed
        # Glob fallback for date-suffixed cards (e.g. z-ai_glm-5-20260211.json).
        # Only matches suffixes that start with a digit to avoid collisions with
        # sibling models that share a common prefix (e.g. glm-5 vs glm-5-turbo).
        candidates = sorted(_cd.glob(f"{safe}-[0-9]*.json"))
        if candidates:
            import logging as _logging
            _logging.debug("_find_card: glob fallback matched '%s' for input '%s'", candidates[-1].name, model_id)
            return candidates[-1]  # most recent when multiple versions exist
        return unprefixed

    # SSoT: SUFFIX-Form ({base}--{shortcode}.json) ist die kanonische Konvention
    # (definiert durch build_card_id). Diese wird zuerst gesucht.
    # OR models are always namespaced, so the local-server prefixes are enough.
    # Includes VSPK for vllm_spark (asusGX10) since Phase 48.
    for shortcode in ("M4APL", "SPRK", "VSPK", "GR"):
        candidate = _cd / f"{safe}--{shortcode}.json"
        if candidate.exists():
            return candidate

    # Backward-compat: ältere Karten nutzten PREFIX-Form ({shortcode}_{base}.json).
    # Diese Form wird beim Lesen noch gefunden, aber nie mehr zum Schreiben verwendet.
    for shortcode in ("M4APL", "SPRK", "VSPK", "GR"):
        candidate = _cd / f"{shortcode}_{safe}.json"
        if candidate.exists():
            return candidate

    # Version-aware fallback: card was renamed from alias to version-specific file
    # e.g. "mistral-large-latest" → "mistral-large-3.json"
    if model_id.endswith("-latest") or model_id.endswith(":latest"):
        ver = get_model_version(model_id, provider="api")
        if ver and ver.strip() not in _STALE_VERSIONS:
            base = re.sub(r"[:-]latest$", "", model_id)
            versioned = _cd / f"{_safe_name(base)}-{ver.strip()}.json"
            if versioned.exists():
                return versioned

    # Glob fallback for non-namespaced IDs with date-suffix (e.g. claude-haiku-4-5-20251001.json)
    if not unprefixed.exists():
        candidates = sorted(_cd.glob(f"{safe}-[0-9]*.json"))
        if candidates:
            import logging as _logging
            _logging.debug("_find_card: glob fallback matched '%s' for input '%s'", candidates[-1].name, model_id)
            return candidates[-1]

    # Dot-to-hyphen fallback: API model IDs with dots (e.g. "grok-4.1-fast-reasoning")
    # may have cards named with hyphens (e.g. "grok-4-1-fast-reasoning.json") when the
    # provider_config entry uses hyphens.  _safe_name converts dots to underscores, so the
    # primary lookup misses the hyphen-named card.  Try the hyphen variant as a last resort.
    if not unprefixed.exists() and "." in model_id:
        hyphen_id = model_id.replace(".", "-")
        if hyphen_id != model_id:
            hyphen_safe = _safe_name(hyphen_id)
            hyphen_path = _cd / f"{hyphen_safe}.json"
            if hyphen_path.exists():
                import logging as _logging
                _logging.debug(
                    "_find_card: dot→hyphen fallback matched '%s' for input '%s'",
                    hyphen_path.name, model_id,
                )
                return hyphen_path

    return unprefixed  # May or may not exist — caller checks


def find_card_by_heritage_id(legacy_id: str, card_dir: Path | None = None) -> Path | None:
    """Findet die Card, die *legacy_id* in ihren ``heritage_ids`` listet.

    Wird benötigt, wenn ein Modell umbenannt wurde: Die Audit-Log-Dirs und
    Review-Dirs tragen die alte ID, aber die Card existiert nur noch unter
    der neuen kanonischen ID. Mit diesem Reverse-Lookup können
    ``generate_review.py`` und ``web_export.py`` die richtige Card finden.

    Vergleicht ``_safe_name``-normalisiert, damit API-IDs (``vendor/model``)
    und Dateiname-Slugs (``vendor_model``) korrekt gematcht werden:
    ``_safe_name("vendor/model-v1") == _safe_name("vendor_model-v1") == "vendor_model-v1"``

    Returns
    -------
    Path zur gefundenen Card, oder ``None`` wenn keine Übereinstimmung.

    Notes
    -----
    Durchsucht alle ``*.json``-Dateien in *card_dir* und ist damit O(n) in der
    Anzahl der Cards. Da der Fallback-Pfad selten getriggert wird, ist das
    Performance-technisch irrelevant.
    """
    _cd = card_dir if card_dir is not None else CARD_DIR
    legacy_safe = _safe_name(legacy_id)
    for card_file in sorted(_cd.glob("*.json")):
        if card_file.name.startswith("_"):
            continue  # Index-/Meta-Dateien überspringen (_index.json, _all_cards.md etc.)
        try:
            data = json.loads(card_file.read_text(encoding="utf-8"))
            for h_id in data.get("heritage_ids") or []:
                if isinstance(h_id, str) and _safe_name(h_id) == legacy_safe:
                    return card_file
        except (OSError, json.JSONDecodeError):
            continue
    return None


def _extract_ollama_id(model_name: str, ollama_output: str) -> Optional[str]:
    """Extracts a model hash/ID from `ollama list` output for an exact model name match."""
    candidates = [model_name]
    if model_name.startswith("ollama/"):
        candidates.append(model_name.replace("ollama/", "", 1))

    for raw_line in ollama_output.splitlines():
        line = raw_line.strip()
        if not line or line.lower().startswith("name"):
            continue

        parts = line.split()
        if len(parts) < 2:
            continue

        listed_name = parts[0]
        listed_id = parts[1]

        if listed_name in candidates:
            return listed_id

    return None


def _get_local_model_hash_version(model_name: str) -> str:
    """Returns the local model hash (Ollama ID) as version; never a semantic label."""
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        return "k.A."

    try:
        result = subprocess.run(
            [ollama_path, "list"],
            capture_output=True,
            text=True,
            check=True,
            timeout=TIMEOUT_OLLAMA_VERSION,
        )
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        return "k.A."

    model_id = _extract_ollama_id(model_name=model_name, ollama_output=result.stdout)
    if model_id and re.fullmatch(r"[a-f0-9]{6,64}", model_id):
        return model_id

    return "k.A."


def get_model_version(model_name: str, provider: str = "ollama", client=None) -> str:
    """
    Retrieves the uniform version mapping of a model without unpredictable fallback fingerprints.
    """
    _ = client  # API compatibility: kept for unchanged call sites.
    p_lower = str(provider).lower().strip()
    prefix = model_name.split("/")[0].lower() if "/" in model_name else ""

    # Card-First: optional override via `model_version` field in model card
    card_path = _card_path(model_name, provider)
    if card_path.exists():
        try:
            card_data = json.loads(card_path.read_text(encoding="utf-8"))
            card_version = card_data.get("model_version")
            if card_version and str(card_version).strip():
                return str(card_version).strip()
        except Exception:
            pass  # malformed card → fall through to regex logic

    # Attempt Local Ollama Logic if provider implies local, or no explicit provider is given
    is_local_attempt = (p_lower in {"ollama", "local"} or prefix in {"ollama", "local"} or p_lower == "ollama")

    if is_local_attempt:
        local_hash = _get_local_model_hash_version(model_name=model_name)
        if local_hash != "k.A.":
            return local_hash

    # Commercial Model Logic
    if "claude" in model_name:
        match = re.search(r"claude-\d+(?:-\w+)?-(202\d{5})", model_name)
        if match: return match.group(1)
        if "-4-7" in model_name: return "4.7"
        if "-4-6" in model_name: return "4.6"
        if "-4-5" in model_name: return "4.5"
        if "3-5" in model_name: return "3.5"
        if "haiku-20240307" in model_name: return "20240307"
    if "gpt" in model_name:
        match = re.search(r"-(202\d{5})$|-(0\d{3})$", model_name)
        if match: return match.group(1) or match.group(2)
        if "gpt-5.4" in model_name: return "5.4"
        if "gpt-5" in model_name: return "5.0"
        if "gpt-4o-mini" in model_name: return "2024-07-18"
        if "gpt-4o" in model_name: return "2024-05-13"
        return "latest"
    if "gemini" in model_name:
        if "3.1" in model_name: return "3.1-pro-preview"
        if "3-flash-preview" in model_name: return "3-flash-preview"
        if "flash" in model_name: return "2.5-flash"
        if "pro" in model_name: return "2.5-pro"
        return model_name.split("-")[-1]
    if "mistral" in model_name or "pixtral" in model_name or "codestral" in model_name or "magistral" in model_name:
        # magistral is a distinct reasoning model family — don't match mistral version heuristics
        if "magistral" in model_name:
            return "latest"
        match = re.search(r"-(24\d{2})$", model_name)
        if match: return match.group(1)
        if "large" in model_name: return "3"   # mistral-large-latest → Mistral Large 3 (open-weights)
        if "small" in model_name: return "3"   # mistral-small-latest → Mistral Small 3 (open-weights)
        if "medium" in model_name: return "2312"
        return "latest"  # covers -latest suffix (e.g. codestral-latest, magistral-small-latest)
    if "grok" in model_name:
        match = re.search(r"grok-([0-9]+(?:\.[0-9]+)?(?:-[0-9]+)?)(?:-([^/]+))?", model_name)
        if match:
            version = match.group(1)
            suffix = match.group(2) or ""
            if "mini" in suffix:
                return f"{version}-mini"
            if "reasoning" in suffix and "non-reasoning" not in suffix:
                return f"{version}-reasoning"
            return version
        return "latest"
    if "kimi" in model_name:
        # Match kimi variants: k2, k2.5, k2-0905, k2-thinking, k2-instruct, k2-dev
        match = re.search(r"kimi-(k[\d\.]+(?:-(?:\d{4}|thinking|instruct|dev))?)", model_name.lower())
        if match:
            return match.group(1)
        return "latest"
    if "qwen" in model_name.lower():
        match = re.search(r"qwen(\d+(?:\.\d+)?)-?(\d+b)?", model_name.lower())
        if match:
            version = match.group(1)
            size = match.group(2)
            return f"{version}-{size.upper()}" if size else version
        return "latest"
    if "glm" in model_name.lower():
        match = re.search(r"glm-(\d+(?:\.\d+)?(?:-[a-z]+)?)", model_name.lower())
        if match:
            return match.group(1)
        return "latest"
    if "minimax" in model_name.lower():
        match = re.search(r"minimax-(m[\d\.]+)", model_name.lower())
        if match:
            return match.group(1)
        return "latest"
    if "llama" in model_name.lower():
        match = re.search(r"llama-?(\d+(?:\.\d+)?)-?(\d+b)?", model_name.lower())
        if match:
            version = match.group(1)
            size = match.group(2)
            if size:
                return f"{version}-{size.upper()}"
            return version
        return "latest"

    if "lfm" in model_name:
        return "latest"
    if "o4" in model_name or "o1" in model_name or "o3" in model_name:
        match = re.search(r"o[134](?:-[a-z]+)*-(\d{4}-\d{2}-\d{2})", model_name)
        if match:
            return match.group(1)
        if "o4-mini" in model_name: return "4-mini"
        if "o4" in model_name: return "4"
        if "o3-mini" in model_name:
            return "2025-01-31"
        if model_name == "o1" or model_name.endswith("/o1"):
            return "2024-12-17"
        return "latest"
    return "k.A."


def format_version_hash_for_display(version: str, model_type: str = "") -> str:
    """
    Truncates local/Ollama model hashes to 6 characters for display purposes.
    Nur für die Anzeige im Leaderboard. Format: 6 Zeichen hex.
    """
    version = str(version).strip()
    m_type = str(model_type).strip().lower()

    # Check if we should treat it as a local/Ollama model (e.g. "Local", "Local Cloud")
    is_local_variant = ("local" in m_type or "ollama" in m_type or not m_type)

    if is_local_variant and len(version) > 6 and re.match(r"^[a-f0-9]+$", version):
        return version[:6]

    return version


def get_ollama_model_info(model_name: str) -> dict[str, Any]:
    """Holt Details (ID/Digest) zu einem bestimmten Ollama-Modell via CLI."""
    try:
        ollama_path = shutil.which("ollama")
        if not ollama_path:
            return {}

        # 'ollama list' ist effizienter als 'ollama show' für die ID
        result = subprocess.run(
            [ollama_path, "list"],
            capture_output=True,
            text=True,
            check=True,
            timeout=TIMEOUT_OLLAMA_LIST,
        )

        for line in result.stdout.strip().split("\n")[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[0] == model_name:
                return {"id": parts[1], "size": parts[2]}

        return {}

    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        return {}


def is_model_suitable_for_benchmark(model_name: str) -> bool:
    """
    Determines if a model is suitable for text generation benchmarks.
    Filters out embedding models and other non-generative models.

    Args:
        model_name: Name of the model (e.g., 'nomic-embed-text:latest', 'llama3:8b')

    Returns:
        bool: True if model is suitable, False otherwise.
    """
    name_lower = model_name.lower()

    # Filter criteria
    if "embed" in name_lower:
        return False
    if "-vl" in name_lower:
        return False
    if "vision" in name_lower:
        return False

    # Add more exclusion criteria here if needed in the future

    return True


def get_ollama_models_info() -> list[dict[str, Any]]:
    """Holt und normalisiert Ollama-Modelle."""
    try:
        import ollama

        # Handle simplified response type if necessary or generic object access
        response = ollama.list()
        models = (
            response.models
            if hasattr(response, "models")
            else response.get("models", [])
        )

        results: list[dict[str, Any]] = []
        for m in models:
            # Access attributes safely (pydantic model vs dict)
            name = str(m.model) if hasattr(m, "model") else str(m.get("name", ""))
            if not is_model_suitable_for_benchmark(name):
                continue

            size = m.size if hasattr(m, "size") else m.get("size", 0)
            modified = (
                m.modified_at
                if hasattr(m, "modified_at")
                else m.get("modified_at", "N/A")
            )

            # Simple normalization
            modified_str = str(modified)[:10] if modified != "N/A" else "N/A"
            size_gb = (size or 0) / (1024**3)

            results.append(
                {
                    "name": name,
                    "size_gb": size_gb,
                    "modified": modified_str,
                    "original": m,  # keep object if needed
                }
            )

        return sorted(results, key=lambda x: x["name"])

    except (
        ImportError,
        subprocess.CalledProcessError,
        OSError,
        subprocess.TimeoutExpired,
    ):
        return []


def get_commercial_models_from_config(
    config: dict[str, Any],
) -> list[tuple[str, str, str]]:
    """
    Extracts enabled commercial models from the configuration dictionary.

    Args:
        config (dict): The loaded benchmark_config.yaml content.

    Returns:
        List[Tuple[str, str, str]]: List of (model_id, pretty_name, provider_key)
    """
    models: list[tuple[str, str, str]] = []
    providers = config.get("providers", {}).get("commercial", {})

    for p_key, p_config in providers.items():
        if p_config.get("enabled", False):
            for m in p_config.get("models", []):
                # model_id, name, provider
                models.append((m["id"], m["name"], p_key))

    return models


def resolve_provider(model_name: str) -> tuple[str, str]:
    """Ermittelt Provider basierend auf benchmark_config.yaml (SSOT), Fallback: Modell-Präfix."""

    # Determine if likely Ollama: tag separator ":" present AND no namespace "/" prefix.
    # OpenRouter free-tier IDs use "vendor/model:free" — must NOT be routed to Ollama.
    if ":" in model_name and "/" not in model_name:
        return "ollama", model_name

    # SSoT: Version-Underscore→Dot normalisieren (qwen3_5-… → qwen3.5-…),
    # damit kanonisierte IDs aus resolve_canonical_model_id() gegen Config-Einträge
    # mit Dot-Versionen in provider_config.yaml matchen. Pattern ist identisch zu
    # find_model_in_provider_cfg() und wird bereits von allen Provider-Konnektoren
    # (openai/openrouter/groq/google/xai) angewendet.
    _model_name_config_form = internal_id_to_config_form(model_name)
    # SSOT: Lookup in benchmark_config.yaml AND config/provider_config.yaml (merged)
    _config_paths = [Path("benchmark_config.yaml"), Path("config/provider_config.yaml")]
    for _config_path in _config_paths:
        if not _config_path.exists():
            continue
        try:
            with open(_config_path, encoding="utf-8") as _f:
                _cfg = yaml.safe_load(_f)
            _providers = _cfg.get("providers", {})
            # Check commercial providers first
            _commercial = _providers.get("commercial", {})
            if isinstance(_commercial, dict):
                for _prov_key, _prov_cfg in _commercial.items():
                    if not isinstance(_prov_cfg, dict):
                        continue
                    for _m in _prov_cfg.get("models", []):
                        if isinstance(_m, dict):
                            _m_id = _m.get("id", "")
                            if _m_id == model_name or _m_id == _model_name_config_form:
                                return _prov_key, model_name
            # Check local providers (llamacpp, ollama, etc.)
            _local = _providers.get("local", {})
            if isinstance(_local, dict):
                for _prov_key, _prov_cfg in _local.items():
                    if not isinstance(_prov_cfg, dict):
                        continue
                    for _m in _prov_cfg.get("models", []):
                        if isinstance(_m, dict):
                            _m_id = _m.get("id", "")
                            if _m_id == model_name or _m_id == _model_name_config_form:
                                return _prov_key, model_name
        except Exception:
            pass

    # Fallback: Präfix-Matching für nicht konfigurierte Modelle
    name_lower = model_name.lower()
    if name_lower.startswith(("mistral-", "open-mixtral", "ministral")):
        return "mistral", model_name
    if name_lower.startswith(("gpt-", "o1-", "o3-")) or name_lower in ("o1", "o3-mini"):
        return "openai", model_name
    if name_lower.startswith("claude-"):
        return "anthropic", model_name
    if name_lower.startswith("gemini-"):
        return "google", model_name
    if name_lower.startswith("grok-"):
        return "xai", model_name
    if name_lower.startswith("command-"):
        return "cohere", model_name
    # "vendor/model" → OpenRouter (incl. ":free" suffix); bare model names → Groq.
    # Heuristik: enthält "/" → OpenRouter-Namespace-Format (nie lokale Ollama-IDs).
    if "/" in name_lower:
        return "openrouter", model_name
    if name_lower.startswith(("qwen", "llama", "moonshot")):
        return "groq", model_name

    # Default to llamacpp if active in config, otherwise ollama
    _config_path = Path("benchmark_config.yaml")
    if _config_path.exists():
        try:
            with open(_config_path, encoding="utf-8") as _f:
                _cfg = yaml.safe_load(_f)
            _llamacpp = (
                _cfg.get("providers", {})
                .get("local", {})
                .get("llamacpp", {})
            )
            if _llamacpp.get("enabled", False):
                return "llamacpp", model_name
        except Exception:
            pass

    return "ollama", model_name


def is_cloud_model(model_name: str, size_gb: Optional[float] = None) -> bool:
    """
    SSOT: Determines if an Ollama model is a cloud proxy model.

    This is the canonical definition used across the entire codebase:
    - UI filtering (run_benchmark.py)
    - Data loading (data_loader.py)
    - Model categorization (get_model_category)

    Args:
        model_name: Name of the model (e.g., 'minimax-m2:cloud')
        size_gb: Optional model size in GB (if available)

    Returns:
        bool: True if model is a cloud proxy model

    Detection Rules:
        1. Model name contains ':cloud' tag (e.g., 'minimax-m2:cloud')
        2. Model name ends with '-cloud' suffix (e.g., 'gpt-oss:120b-cloud')
        3. Model size is extremely small (< 0.01 GB = proxy, not locally stored)
    """
    model_lower = model_name.lower()

    # Rule 1 & 2: Name-based detection
    if ":cloud" in model_lower or model_lower.endswith("-cloud"):
        return True

    # Rule 3: Size-based heuristic (proxy models have minimal/no local storage)
    if size_gb is not None and size_gb < 0.01:
        return True

    return False


def get_model_category(
    model_name: str, source_file: str = "local", size_gb: Optional[float] = None, provider: Optional[str] = None
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
    try:
        import json as _json
        card_path = _find_card(model_name)
        if card_path.exists():
            card_data = _json.loads(card_path.read_text(encoding="utf-8"))
            tier = card_data.get("weights_license_tier")
            if tier and tier in WEIGHTS_TIER_DISPLAY:
                return WEIGHTS_TIER_DISPLAY[tier]
    except Exception:
        pass

    if provider:
        try:
            from utils.config_validator import ConfigValidator
            config = ConfigValidator().config
            commercial_providers = config.get("providers", {}).get("commercial", {})
            if provider in commercial_providers:
                provider_config = commercial_providers[provider]
                m_type = provider_config.get("model_type", "")

                # Per-model override: check if this specific model has a model_type set
                for model_entry in provider_config.get("models", []):
                    if isinstance(model_entry, dict) and model_entry.get("id") == model_name:
                        override = model_entry.get("model_type")
                        if override:
                            m_type = override
                        break

                if m_type == MODEL_TYPE_OPEN_WEIGHTS_CLOUD:
                    return "Open Weights"
                elif m_type == "proprietary_api":
                    return "Proprietär"
                elif m_type == "cloud":
                    return "Open Weights"
        except Exception:
            pass

    # Fallback: derive from source_file / model_name heuristics (no card available)
    if source_file == "cloud" or (source_file == "local" and ("cloud" in model_name.lower() or (size_gb is not None and size_gb < 0.01))):
        return "Open Weights"

    # Rule 1: Commercial CSV → Always Proprietär
    if source_file == "commercial":
        return "Proprietär"

    # Rule 2: Local CSV → cloud proxy check
    if is_cloud_model(model_name, size_gb):
        return "Open Weights"

    # Rule 3: Everything else from Local CSV → Open Weights
    return "Open Weights"


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
        import json as _json
        card_path = _find_card(model_id)
        if card_path.exists():
            card = _json.loads(card_path.read_text(encoding="utf-8"))
            return card.get("use_case_primary", "generalist")
    except Exception:
        pass

    return "generalist"


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
    if provider:
        from utils.vendor_card_template import load_vendor_card
        provider_card = load_vendor_card(provider)
        if provider_card:
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
                reasoning = bool(effective)
            # effective is None: keine Info → Trigger-Fallback bleibt erhalten.

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


def is_thinking_optional_from_card(model_id: str) -> bool:
    """
    Returns True if the model card for *model_id* contains the tag
    ``"Thinking-Optional"`` in its ``architecture_tags`` list.

    Used by ``resolve_token_budget()`` to grant Thinking-Optional models the
    elevated reasoning budget — their internal thinking tokens consume the same
    ``max_output_tokens`` quota as the visible output.

    Returns False if no card exists, the field is absent, or the tag is not set.
    """
    card_path = _find_card(model_id)
    if not card_path.exists():
        return False
    try:
        data = json.loads(card_path.read_text(encoding="utf-8"))
        tags = data.get("architecture_tags", [])
        return "Thinking-Optional" in (tags or [])
    except Exception:
        return False


def _read_max_output_tokens_from_card(model_id: str) -> int | None:
    """
    Liest ``max_output_tokens`` aus der Model Card.

    Gibt den Wert zurück, wenn er als positive Ganzzahl in der Card vorhanden ist,
    sonst None. Wird von ``resolve_token_budget()`` als harte Obergrenze verwendet,
    damit modellspezifische API-Limits (z.B. gpt-4o-2024-05-13: max 4096) direkt
    im ersten Request gesetzt werden und der Fallback-Retry entfällt.
    """
    card_path = _find_card(model_id)
    if not card_path.exists():
        return None
    try:
        data = json.loads(card_path.read_text(encoding="utf-8"))
        val = data.get("max_output_tokens")
        if isinstance(val, int) and val > 0:
            return val
    except Exception:
        pass
    return None


SUPPORT_TOOL_USE_UNTESTED = "untested"
SUPPORT_TOOL_USE_NOT_APPLICABLE = "not_applicable"
_SUPPORT_TOOL_USE_VALUES = (True, False, SUPPORT_TOOL_USE_UNTESTED, SUPPORT_TOOL_USE_NOT_APPLICABLE)


def normalize_supports_tool_use(value: object) -> bool | str:
    """Normalisiert ``supports_tool_use`` aus einer Card auf einen der drei
    kanonischen Zustände.

    Returns:
        ``True`` wenn das Modell Tool-Use unterstützt, ``False`` wenn nicht,
        ``"untested"`` wenn kein verifizierter Benchmark-Wert vorliegt.
        ``None`` und unbekannte Werte werden als ``"untested"`` interpretiert.
    """
    if value is True:
        return True
    if value is False:
        return False
    if isinstance(value, str) and value.strip().lower() == SUPPORT_TOOL_USE_UNTESTED:
        return SUPPORT_TOOL_USE_UNTESTED
    return SUPPORT_TOOL_USE_UNTESTED


def update_model_card_tooluse_fields(
    model_id: str,
    supports_tool_use: bool | str,
    tested_at: str | None,
    p1_score: float | None = None,
    p2_score: float | None = None,
) -> bool:
    """Schreibt Tooluse-Benchmark-Ergebnisse direkt in die Model Card.

    Wird von ``tooluse_exporter.finalize_model()`` nach jedem erfolgreichen
    Benchmark-Run aufgerufen, damit die Card immer den aktuellen verifizierten
    Stand widerspiegelt.

    Tri-State-Semantik für ``supports_tool_use``:
    - ``True``         — Tool-Use funktioniert (empirisch verifiziert, mean P1 > 0).
    - ``False``        — Modell kann keine Tools aufrufen (empirisch verifiziert).
    - ``"untested"``   — noch kein Tool-Use-Benchmark gelaufen.
                         ``tested_at`` ist in diesem Fall ``None`` und das Feld
                         ``tooluse_tested_at`` wird aus der Card entfernt.

    Felder, die aktualisiert werden:
    - ``supports_tool_use``  : True / False / "untested"
    - ``tooluse_tested_at``  : ISO-8601-Timestamp (oder Feld entfernt)
    - ``tooluse_score_p1``   : mittlerer P1-Score (Phase 1), optional
    - ``tooluse_score_p2``   : mittlerer P2-Score (Phase 2), optional

    Returns:
        True wenn die Card erfolgreich aktualisiert wurde, False bei Fehler.
    """
    if supports_tool_use not in _SUPPORT_TOOL_USE_VALUES:
        raise ValueError(
            f"supports_tool_use muss True, False oder {SUPPORT_TOOL_USE_UNTESTED!r} sein, "
            f"bekommen: {supports_tool_use!r}"
        )

    card_path = _find_card(model_id)
    if not card_path.exists():
        logger.debug("update_model_card_tooluse_fields: Keine Card gefunden für '%s'", model_id)
        return False
    try:
        data = json.loads(card_path.read_text(encoding="utf-8"))
        data["supports_tool_use"] = (
            supports_tool_use
            if not isinstance(supports_tool_use, str)
            else SUPPORT_TOOL_USE_UNTESTED
        )
        if tested_at is None:
            data.pop("tooluse_tested_at", None)
        else:
            data["tooluse_tested_at"] = tested_at
        # Scores persistent schreiben — SSoT für spätere aggregate_from_benchmark_csvs()-Läufe.
        # Verhindert, dass Leaderboard-Regenerierung manuell validierte Werte überschreibt.
        if p1_score is not None:
            data["tooluse_score_p1"] = round(float(p1_score), 2)
        if p2_score is not None:
            data["tooluse_score_p2"] = round(float(p2_score), 2)
        card_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.debug(
            "Model Card aktualisiert: %s → supports_tool_use=%s, tooluse_tested_at=%s, p1=%s, p2=%s",
            model_id, supports_tool_use, tested_at, p1_score, p2_score,
        )
        return True
    except Exception:
        logger.warning("Konnte Model Card nicht aktualisieren für '%s'", model_id, exc_info=True)
        return False


def is_reasoning_model_from_card(model_id: str) -> bool | None:
    """
    Reads `thinking_probe_detected` from an existing model card JSON.

    Returns:
        True/False if the field is set; None if no card exists or field is missing.
    """
    card_path = _find_card(model_id)
    if not card_path.exists():
        return None
    try:
        data = json.loads(card_path.read_text(encoding="utf-8"))
        val = data.get("thinking_probe_detected")
        if val is None:
            return None
        return bool(val)
    except Exception:
        return None


def is_reasoning_model(model_name: str) -> bool:
    """
    Checks if the model is a reasoning model (Chain-of-Thought).
    Card lookup takes priority over string triggers; falls back to heuristic triggers.

    Args:
        model_name: Name of the model

    Returns:
        bool: True if it is a reasoning model
    """
    card_result = is_reasoning_model_from_card(model_name)
    if card_result is not None:
        return card_result
    # Fallback: Trigger-Liste aus config/card_vocabulary.yaml (SSoT).
    # Damit bleibt die Liste der Heuristik-Substrings konsistent mit der
    # Registry und kann zentral erweitert werden (siehe Reasoning-Trigger-
    # Sektion in der YAML).
    from utils.card_utils import get_reasoning_triggers
    triggers = get_reasoning_triggers()
    return any(t in model_name.lower() for t in triggers)


_SIZE_CLASS_VALID = {"Nano", "Edge", "Desktop", "Workstation", "Server", "Frontier"}

# Parameter-to-size-class mapping (upper bound in billions, class name).
# Reflects real-world RAM requirements at Q4 quantization; order matters (smallest first).
_SIZE_CLASS_THRESHOLDS: tuple[tuple[float, str], ...] = (
    (4.0, "Nano"),
    (9.0, "Edge"),
    (22.0, "Desktop"),
    (35.0, "Workstation"),
    (75.0, "Server"),
)


def _param_b_to_size_class(param_b: float) -> str:
    return next(
        (cls for threshold, cls in _SIZE_CLASS_THRESHOLDS if param_b <= threshold),
        "Frontier",
    )


def get_model_size_class(model_name: str) -> str:
    """
    Determines the hardware-deployment size class of a model based on its name tag.

    Priority:
        1. Model-Card field ``size_class`` (single source of truth for overrides)
        2. Ollama-style tag regex (e.g. 'qwen3:4b', 'phi3.5:3.8b', 'gemma4:E4B')
        3. Dash/dot-separated size suffix (e.g. 'llama-3.3-70b', 'qwen3-32b')
        4. Fallback: 'Frontier' (API-only or size unknown)

    Tiers reflect real-world RAM requirements at Q4 quantization:

        Nano        ≤ 4B    < 4 GB    Smartphone, Raspberry Pi, autocomplete-only
        Edge        5–9B    4–8 GB    Any laptop, MacBook Air M-Series
        Desktop     10–22B  8–16 GB   MacBook Pro, 14–36 GB Unified Memory
        Workstation 20–35B  14–24 GB  M4 Pro/Max, RTX 4090, high-end consumer
        Server      36–75B  24–48 GB  Mac Studio, dedicated GPU node
        Frontier    >75B / API-only   Cloud-only, no practical local deployment

    Args:
        model_name: Raw model name string (e.g. 'qwen3:4b', 'mistral-large-latest')

    Returns:
        One of: 'Nano', 'Edge', 'Desktop', 'Workstation', 'Server', 'Frontier'
    """
    # 1. Model-Card override (SSoT for models whose name doesn't carry a clear size tag)
    card_path = _find_card(model_name)
    if card_path.exists():
        try:
            card = json.loads(card_path.read_text(encoding="utf-8"))
            sc = card.get("size_class")
            if isinstance(sc, str) and sc in _SIZE_CLASS_VALID:
                return sc
        except (json.JSONDecodeError, OSError):
            pass

    # 2. Ollama-style colon tag: 'model:e?<N>b' (case-insensitive for edge-prefix)
    match = re.search(r":e?(\d+(?:\.\d+)?)[bB]", model_name, re.IGNORECASE)
    if match:
        try:
            return _param_b_to_size_class(float(match.group(1)))
        except ValueError:
            pass

    # 3. Dash/dot-separated suffix: 'llama-3.3-70b', 'qwen3-32b', 'scout-17b-16e'
    match = re.search(r"(?:[\-_\.])(\d+(?:\.\d+)?)[bB](?:[\-_\.]|$)", model_name, re.IGNORECASE)
    if match:
        try:
            return _param_b_to_size_class(float(match.group(1)))
        except ValueError:
            pass

    # No size tag → API-only or very large (commercial model, cloud proxy)
    return "Frontier"


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


# ---------------------------------------------------------------------------
# Thinking Probe
# ---------------------------------------------------------------------------
# Multi-Prompt-Discovery: drei Probe-Prompts (Mathe / Code / Decision),
# um familien-spezifische CoT-Patterns zuverlaessig zu erkennen. Manche
# Modelle zeigen CoT nur bei ethischen/Decision-Fragen, andere nur bei
# Code-Reasoning, wieder andere nur bei Mathematik.
# Discovery-Skript: scripts/tools/discover_thinking_tags.py
_PROBE_PROMPTS: dict[str, str] = {
    "math": (
        "Solve step by step: A train travels 120 km in 1.5 hours. "
        "What is its average speed in km/h? Show your reasoning."
    ),
    "code": (
        "Sort this list step by step and explain your algorithm: "
        "[3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]"
    ),
    "decision": (
        "Should an autonomous car swerve to avoid a pedestrian "
        "even if it risks the passenger's life? Think through the "
        "ethical considerations before answering."
    ),
}
# Backward-compat: alter Single-Prompt-Slot (Card-First-Hook).
_PROBE_PROMPT = _PROBE_PROMPTS["math"]
# Token-Budget fuer den Reasoning-Probe. Muss gross genug sein, dass ein
# Hybrid-Thinking-Modell (z. B. Qwen3.6-27B) seine interne Reasoning-Phase
# abschliesst UND sichtbaren Content emittiert. 512 (alter Wert) reichte
# nur fuer Reasoning, nicht fuer Output → Cold-Start-Guard klassifizierte
# Budget-Erschöpfung falsch als "0 chars output" (Qwen3.6-27B-VSPK, 2026-07-07).
# 4096 deckt typische Reasoning-Phasen (800-2500 Tokens) + Antwort ab.
_PROBE_MAX_TOKENS = 4096
# Schwelle (Anteil an _PROBE_MAX_TOKENS), ab der leerer Output + hohe
# reasoning_tokens als Budget-Erschöpfung (Thinking-Nachweis) gilt statt
# als Cold-Start-Artefakt. 90 % toleriert Off-by-one in Usage-Reporting.
_PROBE_BUDGET_EXHAUSTION_RATIO = 0.9

# Erweiterte Tag-Liste basierend auf Modell-Familien-Inventar.
# Quellen: Qwen 3/3.5/3.6, DeepSeek R1/V3, OpenAI OSS (gpt-oss),
# Anthropic Extended Thinking, Meta Llama 4, NousResearch Hermes,
# Mistral Magistral, GLM, Kimi, Gemma 4 (Channel-Tokens). Bei neu
# entdeckten Tags: hier ergaenzen + Test in tests/test_thinking_probe_families.py.
_THINK_TAGS: tuple[str, ...] = (
    "<think>", "<thinking>", "<thought>",            # Qwen 3/3.5/3.6, Magistral, GLM
    "<|thinking|>", "<|reasoning|>",                 # OpenAI OSS (gpt-oss)
    "<|channel|>",                                   # Gemma 4 (Channel-Token: <|channel|>analysis/thought/final)
    "<reasoning>", "<reason>",                       # DeepSeek R1/V3
    "<reflection>",                                  # Meta Llama 4 (Reflektion)
    "<analysis>", "<plan>",                          # Anthropic Extended Thinking
    "<scratchpad>",                                  # NousResearch Hermes
    "<solution>",                                    # Mistral Reasoning
    "<cot>",                                         # Custom / Future
)

# Inline-CoT-Detection: heuristisches Signal C fuer Modelle, die --reasoning off
# ignorieren und Chain-of-Thought direkt im content-Feld produzieren.
# Beobachtung: Gemma 4 26B-A4B mit llama.cpp --reasoning off liefert
# z.B. "OK, das ist eine einfache Geschwindigkeitsberechnung.
# v = s/t = 120/1.5 = 80. Die Antwort ist 80 km/h." (~1142 Zeichen).
# Eine direkte Antwort "v = s/t = 120/1.5 = 80 km/h" ist <100 Zeichen.
# Trigger: Antwort > Schwellwert UND mind. 2 Berechnungs-Operatoren.
_INLINE_COT_LENGTH_THRESHOLD = 200
_INLINE_COT_OPS = (" = ", " * ", " / ", "**", " + ", " - ")
# Mindestanzahl an Berechnungs-Operatoren, ab der inline CoT angenommen wird.
# 2 schliesst versehentliche '=' in Prosa aus (z. B. 'speed = distance / time').
_INLINE_COT_MIN_OPS = 2


def _has_inline_cot(text: str) -> bool:
    """Heuristik fuer Chain-of-Thought inline im content-Feld.

    Trigger-Bedingung: Antwort laenger als Schwellwert UND mindestens
    _INLINE_COT_MIN_OPS Berechnungs-Operatoren (z. B. ' = ', ' * ').
    Reduziert False-Positives bei langen aber mathe-freien Antworten
    (Code-Outputs, Prosa).
    """
    if not text or len(text) <= _INLINE_COT_LENGTH_THRESHOLD:
        return False
    op_count = sum(text.count(op) for op in _INLINE_COT_OPS)
    return op_count >= _INLINE_COT_MIN_OPS


def _find_think_tags(text: str) -> tuple[str, ...]:
    """Gibt alle in text gefundenen Think-Tags zurueck (lowercase match)."""
    if not text:
        return ()
    lower = text.lower()
    return tuple(tag for tag in _THINK_TAGS if tag in lower)


# Marker-Familie (ab v4.7.1 Card-Feld "cot_marker_family"):
# Heuristik-Mapping Tag-Set -> Familien-Kennung. Wird in Card geschrieben,
# damit Web-Export + Audit + Review einheitlich filtern koennen.
# Reihenfolge der Familien ist signifikant (erster Match gewinnt).
#
# WICHTIG: "think-xml" deckt ALLE Modelle ab, die <think>/<thought> nutzen —
# darunter Qwen 3/3.5/3.6 UND Magistral (Mistral Reasoning). Da beide
# Familien denselben Tag verwenden, ist eine tag-basierte Unterscheidung
# nicht moeglich. Die Familie heisst bewusst generisch "think-xml" statt
# "qwen-think", um die Irreführung zu vermeiden.
_COT_FAMILY_MAP: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("think-xml", ("<think>", "<thought>")),        # Qwen 3/3.5/3.6 + Magistral
    ("openai-oss", ("<|thinking|>", "<|reasoning|>")),
    ("channel-tags", ("<|channel|>",)),              # Gemma 4 (Channel-Token-Format)
    ("deepseek-reasoning", ("<reasoning>", "<reason>")),
    ("llama-cot", ("<reflection>",)),
    ("anthropic-extended", ("<analysis>", "<plan>")),
    ("hermes-scratchpad", ("<scratchpad>",)),
    ("mistral-reasoning", ("<solution>",)),
    ("glm-cot", ("<thinking>",)),
    ("generic-cot", ("<cot>",)),
)


def classify_cot_marker_family(tags_found: tuple[str, ...] | list[str] | None) -> str:
    """Leitet die CoT-Marker-Familie aus den gefundenen Tags ab.

    Eingabe: Tuple/Liste der Tags aus _find_think_tags() (lowercase).
    Ausgabe: Eine der Familien-Kennungen aus _COT_FAMILY_MAP, oder "none"
    wenn keine Tags erkannt wurden.

    Die Zuordnung erfolgt in der Reihenfolge von _COT_FAMILY_MAP; erste
    Familie, fuer die mindestens ein Tag aus dem Input passt, gewinnt.
    """
    if not tags_found:
        return "none"
    tag_set = {t.lower() for t in tags_found}
    for family, members in _COT_FAMILY_MAP:
        if tag_set.intersection(members):
            return family
    return "none"


@dataclass
class ThinkingProbeResult:
    detected: bool
    evidence: str
    confidence: Literal["high", "medium", "low"]
    # Multi-Prompt-Metadaten (Defaults erhalten Backward-Compat).
    prompts_used: tuple[str, ...] = ()
    tags_found: tuple[str, ...] = ()


def _probe_single(
    model_id: str,
    provider_key: str,
    config: dict,
    prompt_name: str,
    prompt_text: str,
) -> ThinkingProbeResult:
    """Einzel-Probe: ein Prompt, ein ThinkingProbeResult.

    Raises:
        RuntimeError: wenn der API-Call fehlschlaegt.
    """
    from utils.llm_client import LLMClient  # local import to avoid circular deps

    logger.info(
        "[ThinkingProbe] Probing %s via %s (prompt=%s, %d chars) ...",
        model_id, provider_key, prompt_name, len(prompt_text),
    )
    print(
        f"   \u23f3 Sende Reasoning-Probe an '{model_id}' (prompt={prompt_name})...",
        flush=True,
    )

    client = LLMClient(config)
    try:
        raw = client.query(
            model=model_id,
            prompt=prompt_text,
            provider=provider_key,
            max_tokens=_PROBE_MAX_TOKENS,
        )
        print(
            f"   \u2713 Antwort erhalten ({len(raw)} Zeichen) -- analysiere...",
            flush=True,
        )
    except Exception as exc:
        raise RuntimeError(
            f"ThinkingProbe: API call failed for model '{model_id}' "
            f"(prompt={prompt_name}): {exc}"
        ) from exc

    reasoning_tokens: int = int(
        (client.last_response_metadata or {}).get("reasoning_tokens") or 0
    )
    # Tatsaechlich gesendetes max_tokens (kann < _PROBE_MAX_TOKENS sein, wenn
    # der Provider einen per-Modell-Cap oder Token-Fallback angewendet hat).
    # Wird fuer die Budget-Erschöpfungs-Schwelle benoetigt, damit die
    # Erkennung auch bei Models mit niedrigem max_tokens-Cap funktioniert.
    actual_max_tokens: int = int(
        (client.last_response_metadata or {}).get("token_limit_used")
        or _PROBE_MAX_TOKENS
    )

    # Signal A -- explicit think-tags (high confidence)
    tags_found = _find_think_tags(raw)
    if tags_found:
        return ThinkingProbeResult(
            detected=True,
            evidence=(
                f"[{prompt_name}] Think-tag(s) gefunden: "
                f"{', '.join(tags_found)}. First 200 chars: {raw[:200]}"
            ),
            confidence="high",
            prompts_used=(prompt_name,),
            tags_found=tags_found,
        )

    # Signal B -- provider metadata reports reasoning tokens (medium)
    # Differenzierung bei leerem Output: zwei Szenarien erzeugen dasselbe
    # Pattern (reasoning_tokens > 0 + raw.strip() == ""), muessen aber
    # entgegengesetzt bewertet werden:
    #   (a) Echter Cold-Start (z. B. llama.cpp Gemma 4 26B-A4B-QAT beim
    #       ersten Request): reasoning_tokens deutlich < max_tokens, leerer
    #       Output wegen KV-Cache-Aufbau → kein Thinking-Nachweis (low).
    #   (b) Budget-Erschöpfung (z. B. Qwen3.6-27B Hybrid-Thinking): das
    #       Modell verbraucht das gesamte max_tokens-Budget fuer Reasoning
    #       (reasoning_tokens ≈ max_tokens) und emittiert 0 sichtbare
    #       Zeichen → STARKES Thinking-Signal (medium).
    # Unterscheidungskriterium: Verhaeltnis reasoning_tokens / max_tokens.
    # Ab _PROBE_BUDGET_EXHAUSTION_RATIO (90 %) liegt Fall (b) vor.
    if reasoning_tokens > 0:
        if not raw.strip():
            budget_threshold = int(actual_max_tokens * _PROBE_BUDGET_EXHAUSTION_RATIO)
            if reasoning_tokens >= budget_threshold:
                return ThinkingProbeResult(
                    detected=True,
                    evidence=(
                        f"[{prompt_name}] reasoning_tokens={reasoning_tokens} "
                        f"bei max_tokens={actual_max_tokens} — Budget vollständig "
                        f"für Reasoning verbraucht (0 chars sichtbarer Output). "
                        f"Budget-Erschöpfung = Thinking-Nachweis, kein Cold-Start."
                    ),
                    confidence="medium",
                    prompts_used=(prompt_name,),
                    tags_found=(),
                )
            # Genuine cold-start: reasoning_tokens deutlich unter Budget
            return ThinkingProbeResult(
                detected=False,
                evidence=(
                    f"[{prompt_name}] reasoning_tokens={reasoning_tokens} "
                    f"aber 0 chars output — Cold-Start-Verdacht "
                    f"(reasoning_tokens << max_tokens={actual_max_tokens}), "
                    f"kein Thinking-Nachweis."
                ),
                confidence="low",
                prompts_used=(prompt_name,),
                tags_found=(),
            )
        return ThinkingProbeResult(
            detected=True,
            evidence=(
                f"[{prompt_name}] reasoning_tokens={reasoning_tokens} "
                f"in provider metadata. First 200 chars: {raw[:200]}"
            ),
            confidence="medium",
            prompts_used=(prompt_name,),
            tags_found=(),
        )

    # Signal C -- inline CoT im content-Feld (medium)
    # Beobachtung: llama.cpp --reasoning off wird von manchen Modellen
    # (z.B. Gemma 4 26B-A4B) ignoriert; sie produzieren Chain-of-Thought
    # trotzdem direkt im content. Heuristik: lange Antwort + Berechnungen.
    if _has_inline_cot(raw):
        op_count = sum(raw.count(op) for op in _INLINE_COT_OPS)
        return ThinkingProbeResult(
            detected=True,
            evidence=(
                f"[{prompt_name}] Inline CoT im content-Feld: "
                f"Antwort {len(raw)} chars (>{_INLINE_COT_LENGTH_THRESHOLD}) "
                f"mit {op_count} Berechnungs-Operatoren. "
                f"First 200 chars: {raw[:200]}"
            ),
            confidence="medium",
            prompts_used=(prompt_name,),
            tags_found=(),
        )

    # No CoT signals detected
    return ThinkingProbeResult(
        detected=False,
        evidence=(
            f"[{prompt_name}] No CoT signals found "
            f"(A: no think-tags, B: reasoning_tokens=0, "
            f"C: len={len(raw)}<={_INLINE_COT_LENGTH_THRESHOLD} "
            f"or <{_INLINE_COT_MIN_OPS} ops). "
            f"Response length: {len(raw)} chars"
        ),
        confidence="low",
        prompts_used=(prompt_name,),
        tags_found=(),
    )


def probe_thinking_model(
    model_id: str,
    provider_key: str,
    config: dict,
    *,
    prompts: dict[str, str] | str | None = None,
) -> ThinkingProbeResult:
    """
    Sends one or more reasoning prompts to the model and inspects the responses
    for Chain-of-Thought signals.

    Signal hierarchy:
      - high:  <think>/<thinking>/<thought>/<|...|>/<reason>/<reflection>/<analysis>/...
               tags present in response
      - medium: reasoning_tokens metadata > 0 (mit sichtbarem Output)
      - medium: Budget-Erschöpfung — reasoning_tokens >= 90 % von
               _PROBE_MAX_TOKENS bei leerem Output (Modell hat das gesamte
               Budget fuer Reasoning verbraucht; z. B. Qwen3.6-27B)
      - medium: inline CoT im content-Feld (Antwort >200 chars + mind. 2 Ops)
      - low:    no signal found (oder Cold-Start: reasoning_tokens > 0 +
               leerer Output, aber reasoning_tokens << max_tokens)

    detected = True if confidence in ("high", "medium")

    Args:
        model_id:     Modell-ID
        provider_key: Provider-Key (z.B. 'llamacpp', 'openrouter')
        config:       Vollstaendige benchmark_config
        prompts:      Probe-Prompts. None=alle 3 aus _PROBE_PROMPTS (math/code/decision).
                      str=Einzel-Prompt (backward-compat). dict={name: prompt} fuer
                      explizite Auswahl.

    Multi-Prompt-Aggregation: hoechste Confidence gewinnt. Wenn irgendein
    Prompt detected=True liefert, ist das Gesamtergebnis detected=True mit
    aggregierter Evidence.

    Raises:
        RuntimeError: wenn der API-Call fehlschlaegt (Card-First-Hook-Gate)
                      oder alle Multi-Prompts fehlschlagen.
    """
    # Backward-compat: str -> dict
    if prompts is None:
        prompts = _PROBE_PROMPTS
    elif isinstance(prompts, str):
        prompts = {"custom": prompts}

    # Single-Prompt-Pfad (Card-First-Hook, Test-Backward-Compat)
    if len(prompts) == 1:
        name, text = next(iter(prompts.items()))
        return _probe_single(model_id, provider_key, config, name, text)

    # Multi-Prompt: aggregiere
    results: list[ThinkingProbeResult] = []
    failures: list[Exception] = []
    for name, text in prompts.items():
        try:
            results.append(
                _probe_single(model_id, provider_key, config, name, text)
            )
        except RuntimeError as exc:
            logger.warning(
                "[ThinkingProbe] Probe '%s' failed for %s: %s",
                name, model_id, exc,
            )
            failures.append(exc)

    if not results:
        raise RuntimeError(
            f"ThinkingProbe: ALL {len(prompts)} probes failed for '{model_id}'. "
            f"First error: {failures[0] if failures else 'unknown'}"
        )

    # Confidence-Ranking
    rank = {"high": 3, "medium": 2, "low": 1}
    best = max(results, key=lambda r: rank[r.confidence])

    if any(r.detected for r in results):
        all_tags: tuple[str, ...] = tuple({
            tag for r in results for tag in r.tags_found
        })
        detected_lines = "\n".join(
            f"  - {r.prompts_used[0] if r.prompts_used else '?'}: {r.evidence}"
            for r in results if r.detected
        )
        return ThinkingProbeResult(
            detected=True,
            evidence=(
                f"Multi-Probe ({len(prompts)} prompts, "
                f"{sum(1 for r in results if r.detected)} detected, "
                f"best confidence={best.confidence}):\n{detected_lines}"
            ),
            confidence=best.confidence,
            prompts_used=tuple(prompts.keys()),
            tags_found=all_tags,
        )

    return ThinkingProbeResult(
        detected=False,
        evidence=(
            f"Multi-Probe ({len(prompts)} prompts, 0 detected, "
            f"best confidence={best.confidence}). "
            f"Best evidence: {best.evidence}"
        ),
        confidence=best.confidence,
        prompts_used=tuple(prompts.keys()),
        tags_found=(),
    )


# ---------------------------------------------------------------------------
# Thinking-SSoT-Auflösung (ab v4.7.1)
# ---------------------------------------------------------------------------
# Architektur (Option C): Thinking-Probe-Resultat aus der Model Card ist
# SSoT. Optionaler thinking_override in der provider_config.yaml ist
# ein expliziter Escape-Hatch für Spezialfälle (Cost-Benchmarks, A/B-Tests)
# mit Pflicht-Begründung und optionalem Expiry-Datum.
#
# Auflösungspriorität:
#   1. Aktiver Override (active_until nicht überschritten) → Override-Wert
#   2. Card-Probe-Ergebnis (thinking_probe_detected)
#   3. None (keine Information verfügbar)
#
# Audit: bei jeder Override-Anwendung wird ein Eintrag geloggt
# (Tag "thinking_override_applied" mit model_id, reason, card_value, override_value).


def _is_override_active(
    override: dict,
    now: datetime | None = None,
) -> bool:
    """
    Prüft, ob ein thinking_override aktuell aktiv ist.

    Inaktiv wenn:
      - `value` fehlt oder nicht bool
      - `reason` fehlt oder nur Whitespace (Pflichtfeld)
      - `active_until` gesetzt und in der Vergangenheit
    """
    if not isinstance(override, dict):
        return False
    if "value" not in override or not isinstance(override["value"], bool):
        return False
    reason = override.get("reason")
    if not reason or not str(reason).strip():
        return False

    active_until = override.get("active_until")
    if active_until:
        try:
            expiry = datetime.fromisoformat(str(active_until).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return False
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        check_now = now or datetime.now(timezone.utc)
        if check_now >= expiry:
            return False
    return True


def resolve_effective_thinking(
    model_card: dict,
    provider_model_cfg: dict | None = None,
    *,
    model_id: str | None = None,
    now: datetime | None = None,
) -> tuple[bool | None, str]:
    """
    Loest das effektive Thinking-Flag fuer ein Modell auf.

    SSoT-Pfad: Card (Probe). Opt-in Override in provider_config.yaml
    gewinnt, wenn aktiv (siehe _is_override_active()).

    Args:
        model_card:           Model Card als dict.
        provider_model_cfg:   Optional: model_cfg-Block aus
                              config/provider_config.yaml. Erwartet
                              optionalen Key 'thinking_override'.
        model_id:             Optional: nur fuer Audit-Log (model_id).
        now:                  Optional: jetzt-Zeitpunkt (fuer Tests).

    Returns:
        Tuple (effective, source) mit:
          effective: True | False | None
            - True/False:  explizit gesetzt (durch Override oder Probe)
            - None:        keine Information (Card-Probe fehlt, kein Override)
          source:       "override" | "card_probe" | "none"
    """
    # 1. Override-Pfad
    if provider_model_cfg and isinstance(provider_model_cfg, dict):
        override = provider_model_cfg.get("thinking_override")
        if isinstance(override, dict) and _is_override_active(override, now=now):
            logger.info(
                "[ThinkingOverride] %s: override active (value=%s, reason=%s)",
                model_id or model_card.get("model_id", "?"),
                override["value"],
                override.get("reason"),
            )
            return (override["value"], "override")

    # 2. Card-Probe-Pfad (SSoT)
    detected = model_card.get("thinking_probe_detected")
    if detected is True or detected is False:
        return (detected, "card_probe")

    # 3. Keine Information
    return (None, "none")
