"""
Foundation module: ID manipulation, provider lookup, and config helpers.

Keine Cross-Cluster-Importe — bildet das Fundament der DAG.
Enthält reine ID-Manipulations- und Provider-Lookup-Funktionen plus ihre Konstanten.

Submodule: model_id_base → model_card_io → {model_version, model_size_class, model_thinking}
→ {model_id, model_token_budget}
"""

import logging
import re
from pathlib import Path
from typing import Any, TypeVar

import yaml

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Provider short codes — mirrors benchmark_config.yaml → providers.<name>.short_code
# ---------------------------------------------------------------------------
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
# ID normalization helpers (SSoT for filesystem-safe model IDs)
# ---------------------------------------------------------------------------

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


def resolve_model_cfg_for(
    model_id: str,
    config: dict[str, Any],
) -> dict[str, Any] | None:
    """SSoT: Löst den ``model_cfg``-Eintrag für ``model_id`` aus der expandierten Config auf.

    Iteriert über die ``commercial``- und ``local``-Provider-Sections und nutzt
    ``find_model_in_provider_cfg`` für den normalisierten Lookup (Underscore↔Dot).

    Wird benötigt, damit Aufrufer den ``card_model_id``-Redirect für
    Dual-Thinking-Profile (vLLM) konsistent weiterreichen können — ohne an
    jeder Aufrufstelle den Section-Loop zu duplizieren.

    Ersetzt die bisher inline duplizierten Loops in:
    - ``result_manager.ResultManager._find_model_cfg``
    - ``base_runner.BaseTest._resolve_thinking_mode``

    Args:
        model_id: Interne Modell-ID (z.B. ``ornith-1_0-35B-FP8-thinking``).
        config:   Die vollständige Config (wie ``ConfigValidator().config``).

    Returns:
        Den Model-Eintrag-Dict wenn gefunden, sonst ``None``.
    """
    providers = config.get("providers", {})
    for section in ("commercial", "local"):
        section_cfg = providers.get(section, {})
        if not isinstance(section_cfg, dict):
            continue
        for prov_cfg in section_cfg.values():
            if not isinstance(prov_cfg, dict):
                continue
            entry = find_model_in_provider_cfg(prov_cfg, model_id)
            if entry is not None:
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


def is_cloud_model(model_name: str, size_gb: float | None = None) -> bool:
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


def _load_provider_sources() -> list[dict]:
    """Sammelt Provider-Configs aus ConfigValidator (primär) und YAML-Fallbacks.

    ConfigValidator sieht auch generierte ``{id}-thinking``-Profile
    (thinking-expandierte Config). Fallback auf direktes YAML-Lesen für
    Edge-Cases, in denen ConfigValidator nicht instanziierbar ist.
    """
    sources: list[dict] = []
    try:
        from utils.config_validator import ConfigValidator  # noqa: PLC0415
        _validator_cfg = ConfigValidator().config
        sources.append(_validator_cfg.get("providers", {}))
    except Exception:  # noqa: BLE001
        pass

    if not sources:
        for _config_path in [Path("benchmark_config.yaml"), Path("config/provider_config.yaml")]:
            if not _config_path.exists():
                continue
            try:
                with open(_config_path, encoding="utf-8") as _f:
                    _cfg = yaml.safe_load(_f)
                sources.append(_cfg.get("providers", {}))
            except Exception:  # noqa: BLE001
                pass
    return sources


def _lookup_model_in_section(
    section_cfg: dict,
    model_name: str,
    config_form: str,
) -> tuple[str, str] | None:
    """Sucht *model_name* in einer Provider-Section (commercial oder local).

    Returns ``(prov_key, model_name)`` on hit, ``None`` on miss.
    """
    for _prov_key, _prov_cfg in section_cfg.items():
        if not isinstance(_prov_cfg, dict):
            continue
        for _m in _prov_cfg.get("models", []):
            if isinstance(_m, dict):
                _m_id = _m.get("id", "")
                if _m_id == model_name or _m_id == config_form:
                    return _prov_key, model_name
    return None


def _resolve_provider_from_config(model_name: str, config_form: str) -> tuple[str, str] | None:
    """Resolve provider from config sources (ConfigValidator + YAML fallback).

    Returns ``(provider_key, model_name)`` on hit, ``None`` on miss.
    """
    for _providers in _load_provider_sources():
        if not isinstance(_providers, dict):
            continue
        for section_name in ("commercial", "local"):
            section = _providers.get(section_name, {})
            if not isinstance(section, dict):
                continue
            hit = _lookup_model_in_section(section, model_name, config_form)
            if hit is not None:
                return hit
    return None


def _resolve_provider_by_heuristic(model_name: str, name_lower: str) -> tuple[str, str]:
    """Fallback: Prefix-Matching für nicht konfigurierte Modelle."""
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

    # Config-Quellen: zuerst ConfigValidator (merged + thinking-expandierte
    # Config — sieht auch generierte ``{id}-thinking``-Profile), danach
    # Fallback auf direktes YAML-Lesen (falls ConfigValidator fehlschlägt).
    config_hit = _resolve_provider_from_config(model_name, _model_name_config_form)
    if config_hit is not None:
        return config_hit

    # Fallback: Präfix-Matching für nicht konfigurierte Modelle
    name_lower = model_name.lower()
    return _resolve_provider_by_heuristic(model_name, name_lower)
