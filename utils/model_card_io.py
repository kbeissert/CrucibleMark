"""Card-Filesystem-IO: Pfad-Konstruktion, Card-Suche, Tool-Use-Persistenz.

Importiert aus ``model_id_base`` (Fundament: keine Cross-Cluster-Importe).
"""
import json
import logging
import re
from pathlib import Path
from typing import Any

from utils.model_id_base import _safe_name, get_provider_shortcode

logger = logging.getLogger(__name__)

# SSoT: alle Card-Pfade laufen über ``benchmark_scores/model_cards`` relativ
# zum Repo-Root. ``_card_path()`` und ``build_card_id()`` sind die einzigen
# Stellen, die diese Konvention anwenden.
CARD_DIR = Path("benchmark_scores/model_cards")

# Stale-Versions, die wie "latest" behandelt werden sollen (kein echter
# Versionsstempel, sondern Alias oder "unbekannt"). SSoT für Suffix-Stripping
# und Card-Lookup-Fallback.
_STALE_VERSIONS: frozenset[str] = frozenset({"latest", "unknown", "k.A.", ""})


# ---------------------------------------------------------------------------
# Card-ID-Generator + Konflikt-Resolver
# ---------------------------------------------------------------------------
# SSoT fuer die ID-Form NEUER Model Cards. Aeltere Karten behalten ihren
# Namen und werden ueber den Multi-Key-Helper `canonical_lookup_keys` gefunden.
# Wenn die gewuenschte ID bereits existiert, wird ein numerisches Suffix
# (``-2``, ``-3`` …) angehaengt und ein WARNING geloggt.

_id_logger = logging.getLogger(__name__)


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


def _try_namespaced_lookup(lookup_id: str, safe: str, card_dir: Path) -> Path | None:
    """Schneller Pfad für namespaced IDs: nur unprefixed Variante, mit Date-Suffix-Fallback."""
    unprefixed = card_dir / f"{safe}.json"
    if unprefixed.exists():
        return unprefixed
    # Glob fallback for date-suffixed cards (e.g. z-ai_glm-5-20260211.json).
    # Only matches suffixes that start with a digit to avoid collisions with
    # sibling models that share a common prefix (e.g. glm-5 vs glm-5-turbo).
    candidates = sorted(card_dir.glob(f"{safe}-[0-9]*.json"))
    if candidates:
        import logging as _logging
        _logging.debug("_find_card: glob fallback matched '%s' for input '%s'", candidates[-1].name, lookup_id)
        return candidates[-1]  # most recent when multiple versions exist
    return None


def _try_versioned_latest_lookup(lookup_id: str, safe: str, card_dir: Path) -> Path | None:
    """Wenn ID auf ``-latest``/``:latest`` endet → versionierte Card suchen."""
    if not (lookup_id.endswith("-latest") or lookup_id.endswith(":latest")):
        return None
    from utils.model_version import get_model_version  # noqa: PLC0415
    ver = get_model_version(lookup_id, provider="api")
    if not ver or ver.strip() in _STALE_VERSIONS:
        return None
    base = re.sub(r"[:-]latest$", "", lookup_id)
    versioned = card_dir / f"{_safe_name(base)}-{ver.strip()}.json"
    if versioned.exists():
        return versioned
    return None


def _try_dot_to_hyphen_lookup(lookup_id: str, safe: str, card_dir: Path) -> Path | None:
    """API-Modell-IDs mit Punkten können auf Karten mit Bindestrich-Variante liegen."""
    if "." not in lookup_id:
        return None
    unprefixed = card_dir / f"{safe}.json"
    if unprefixed.exists():
        return None
    hyphen_id = lookup_id.replace(".", "-")
    if hyphen_id == lookup_id:
        return None
    hyphen_safe = _safe_name(hyphen_id)
    hyphen_path = card_dir / f"{hyphen_safe}.json"
    if hyphen_path.exists():
        import logging as _logging
        _logging.debug(
            "_find_card: dot→hyphen fallback matched '%s' for input '%s'",
            hyphen_path.name, lookup_id,
        )
        return hyphen_path
    return None


def _try_thinking_suffix_lookup(lookup_id: str, card_dir: Path) -> Path | None:
    """Wenn die ID auf ``-thinking`` endet, probiere die Basis-Card."""
    if not lookup_id.endswith("-thinking"):
        return None
    base_id = lookup_id[: -len("-thinking")]
    if not base_id or base_id == lookup_id:
        return None
    base_path = _find_card(base_id, card_dir=card_dir)
    if base_path.exists():
        import logging as _logging
        _logging.debug(
            "_find_card: -thinking suffix fallback matched '%s' for input '%s'",
            base_path.name, lookup_id,
        )
        return base_path
    return None


# Bekannte Quantizer-Suffixe, die in provider_config.yaml als kanonische
# Card-IDs verwendet werden (z.B. ``ornith-1_5-35b-a3b-nvfp4``).
# Wenn die Input-ID KEINEN Suffix trägt, soll die Variante MIT Suffix gefunden
# werden, damit Served-Name (``ornith-1.5-35b-a3b``) und Config-ID
# (``ornith-1_5-35b-a3b-nvfp4``) auf dieselbe Card mappen.
_KNOWN_QUANTIZER_SUFFIXES: tuple[str, ...] = (
    "-nvfp4",
    "-fp8",
    "-mxfp4",
    "-int4",
    "-int8",
    "-q4",
    "-q5",
    "-q6",
    "-q8",
)


def _try_quantizer_suffix_lookup(lookup_id: str, safe: str, card_dir: Path) -> Path | None:
    """Wenn die ID keinen bekannten Quantizer-Suffix traegt, probiere suffixed Varianten.

    Hintergrund: provider_config.yaml fuehrt Modelle mit kanonischem Suffix
    (``ornith-1_5-35b-a3b-nvfp4``), waehrend der Served-Name auf vLLM diesen
    Suffix nicht enthaelt (``ornith-1.5-35b-a3b``). Ohne diesen Fallback
    wuerde der Served-Name-Pfad eine Skeleton-Card anlegen und die
    nachfolgenden ``_safe_name``-Lookups die ``-nvfp4``-Card nie finden.
    """
    lower = lookup_id.lower()
    for suffix in _KNOWN_QUANTIZER_SUFFIXES:
        if lower.endswith(suffix):
            return None  # ID hat schon Suffix — kein Fallback noetig
    for suffix in _KNOWN_QUANTIZER_SUFFIXES:
        candidate = card_dir / f"{safe}{suffix}.json"
        if candidate.exists():
            import logging as _logging
            _logging.debug(
                "_find_card: quantizer-suffix fallback matched '%s' for input '%s'",
                candidate.name, lookup_id,
            )
            return candidate
    return None


def _try_prefixed_shortcode_lookup(safe: str, card_dir: Path) -> Path | None:
    """Suffixed- und Legacy-Prefix-Pfade für non-namespaced IDs durchsuchen.

    SSoT: SUFFIX-Form ({base}--{shortcode}.json) ist die kanonische Konvention
    (definiert durch build_card_id). Diese wird zuerst gesucht.
    OR models are always namespaced, so the local-server prefixes are enough.
    Includes VSPK for vllm_spark (asusGX10) since Phase 48.

    Backward-compat: ältere Karten nutzten PREFIX-Form ({shortcode}_{base}.json).
    Diese Form wird beim Lesen noch gefunden, aber nie mehr zum Schreiben verwendet.
    """
    for shortcode in ("M4APL", "SPRK", "VSPK", "GR"):
        candidate = card_dir / f"{safe}--{shortcode}.json"
        if candidate.exists():
            return candidate
    for shortcode in ("M4APL", "SPRK", "VSPK", "GR"):
        candidate = card_dir / f"{shortcode}_{safe}.json"
        if candidate.exists():
            return candidate
    return None


def _try_glob_date_suffix(lookup_id: str, safe: str, card_dir: Path) -> Path | None:
    """Glob-Fallback für non-namespaced IDs mit Datumssuffix (z. B. claude-haiku-4-5-20251001.json)."""
    unprefixed = card_dir / f"{safe}.json"
    if unprefixed.exists():
        return None
    candidates = sorted(card_dir.glob(f"{safe}-[0-9]*.json"))
    if candidates:
        import logging as _logging
        _logging.debug("_find_card: glob fallback matched '%s' for input '%s'", candidates[-1].name, lookup_id)
        return candidates[-1]
    return None


def _find_card(
    model_id: str,
    card_dir: Path | None = None,
    model_cfg: dict[str, Any] | None = None,
) -> Path:
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
    model_cfg:
        Optional model_cfg-Block (z.B. aus ``provider_config.yaml``). Wenn
        gesetzt und ``card_model_id`` enthalten ist, wird DIESER Wert als
        Card-Lookup-Basis verwendet statt ``model_id``. Ermöglicht
        Profil-Entries (``{id}-thinking``), die auf die Card der
        zugrundeliegenden Modell-ID zeigen (vLLM Dual-Thinking-Profile).
    """
    _cd = card_dir if card_dir is not None else CARD_DIR

    # Profil-Redirect: card_model_id im model_cfg überschreibt die model_id
    # für den Lookup. Deterministisch (kein Suffix-Stripping), kein
    # Re-Entry der Funktion → verhindert Endlos-Rekursion, falls ein
    # profile-Eintrag selbst wieder card_model_id trägt.
    lookup_id = model_id
    if model_cfg is not None:
        card_model_id = model_cfg.get("card_model_id")
        if isinstance(card_model_id, str) and card_model_id:
            lookup_id = card_model_id

    safe = _safe_name(lookup_id)
    unprefixed = _cd / f"{safe}.json"

    # Namespaced IDs (OpenRouter, Groq namespaced, …) only ever use the unprefixed path
    if "/" in lookup_id:
        hit = _try_namespaced_lookup(lookup_id, safe, _cd)
        if hit is not None:
            return hit
        return unprefixed

    prefixed_hit = _try_prefixed_shortcode_lookup(safe, _cd)
    if prefixed_hit is not None:
        return prefixed_hit

    # Version-aware fallback: card was renamed from alias to version-specific file
    # e.g. "mistral-large-latest" → "mistral-large-3.json"
    versioned_hit = _try_versioned_latest_lookup(lookup_id, safe, _cd)
    if versioned_hit is not None:
        return versioned_hit

    # Glob fallback for non-namespaced IDs with date-suffix (e.g. claude-haiku-4-5-20251001.json)
    glob_hit = _try_glob_date_suffix(lookup_id, safe, _cd)
    if glob_hit is not None:
        return glob_hit

    # Dot-to-hyphen fallback: API model IDs with dots (e.g. "grok-4.1-fast-reasoning")
    # may have cards named with hyphens (e.g. "grok-4-1-fast-reasoning.json") when the
    # provider_config entry uses hyphens.  _safe_name converts dots to underscores, so the
    # primary lookup misses the hyphen-named card.  Try the hyphen variant as a last resort.
    hyphen_hit = _try_dot_to_hyphen_lookup(lookup_id, safe, _cd)
    if hyphen_hit is not None:
        return hyphen_hit

    # Thinking-Profile-Fallback: Wenn die model_id auf ``-thinking`` endet und
    # keine eigene Card existiert (Thinking-Profile teilen sich die Card des
    # Basis-Modells via ``card_model_id``), streife das Suffix ab und suche
    # nach der Basis-Card. Dies ist ein deterministischer Fallback (kein
    # Heuristik-Raten) — analog zu ``strip_date_suffix``.
    # Greift NUR wenn ``model_cfg`` nicht übergeben wurde (sonst übernimmt
    # ``card_model_id``-Redirect den Lookup bereits deterministisch).
    if model_cfg is None:
        thinking_hit = _try_thinking_suffix_lookup(lookup_id, _cd)
        if thinking_hit is not None:
            return thinking_hit

    # Quantizer-Suffix-Fallback: Wenn die Input-ID keinen bekannten
    # Quantizer-Suffix traegt (z.B. ``ornith-1_5-35b-a3b``), probiere
    # suffixed Varianten (``ornith-1_5-35b-a3b-nvfp4.json``). Stellt sicher,
    # dass Served-Name und Config-ID auf dieselbe Card mappen.
    quantizer_hit = _try_quantizer_suffix_lookup(lookup_id, safe, _cd)
    if quantizer_hit is not None:
        return quantizer_hit

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


def _persist_tooluse_data(
    data: dict[str, Any],
    effective_profile_id: str,
    tested_at: str | None,
    p1_score: float | None,
    p2_score: float | None,
) -> None:
    """Persistiert tooluse_runs (nested) und ggf. Legacy-Felder in *data* (in-place)."""
    # SSoT: Per-Profil-Run-State unter tooluse_runs.{profile_id} (nested).
    # Verhindert Race Condition zwischen Standard- und Thinking-Profil, die sich
    # eine Card teilen (card_model_id-Redirect). Legacy-Felder tooluse_tested_at,
    # tooluse_score_p1, tooluse_score_p2 werden nur noch als Fallback für
    # noch-nicht-migrierte Cards geschrieben — bei Migration verschwinden sie.
    tooluse_runs = data.get("tooluse_runs") or {}
    if not isinstance(tooluse_runs, dict):
        tooluse_runs = {}

    if tested_at is None:
        # Profile-spezifischer Eintrag entfernen, falls vorhanden
        tooluse_runs.pop(effective_profile_id, None)
    else:
        run_entry = tooluse_runs.get(effective_profile_id) or {}
        run_entry["tested_at"] = tested_at
        if p1_score is not None:
            run_entry["score_p1"] = round(float(p1_score), 2)
        if p2_score is not None:
            run_entry["score_p2"] = round(float(p2_score), 2)
        tooluse_runs[effective_profile_id] = run_entry

    if tooluse_runs:
        data["tooluse_runs"] = tooluse_runs
    else:
        data.pop("tooluse_runs", None)

    # Backwards-Compat-Schreiber: flache Legacy-Felder werden NUR dann
    # synchron gehalten, wenn sie bereits in der Card existieren (d.h. die
    # Card wurde noch nicht migriert). Migrierte Cards (flache Felder
    # entfernt) bekommen sie NICHT re-kreiert — sonst würde die Migration
    # permanent sabotiert (siehe migrate_tooluse_runs_nested.py).
    # Pitfall-Diagnose 2026-07-10: unbedingter Schreiber re-kreierte
    # flache Felder nach jeder Migration → 103/108 Cards hatten BEIDE
    # Schemata. Fix: konditionaler Schreiber (nur wenn Feld vorhanden).
    if tested_at is None:
        data.pop("tooluse_tested_at", None)
        data.pop("tooluse_score_p1", None)
        data.pop("tooluse_score_p2", None)
    else:
        # Legacy-Felder werden NUR dann aktualisiert, wenn der Run zur
        # Basis-ID der Card gehört (kein Thinking-Profil) UND die Felder
        # bereits existieren (Card noch nicht migriert).
        base_id = data.get("model_id")
        if base_id and effective_profile_id == base_id:
            if "tooluse_tested_at" in data:
                data["tooluse_tested_at"] = tested_at
            if "tooluse_score_p1" in data and p1_score is not None:
                data["tooluse_score_p1"] = round(float(p1_score), 2)
            if "tooluse_score_p2" in data and p2_score is not None:
                data["tooluse_score_p2"] = round(float(p2_score), 2)


def update_model_card_tooluse_fields(
    model_id: str,
    supports_tool_use: bool | str,
    tested_at: str | None,
    p1_score: float | None = None,
    p2_score: float | None = None,
    *,
    profile_id: str | None = None,
    preserve_supports_tool_use: bool = False,
) -> bool:
    """Schreibt Tooluse-Benchmark-Ergebnisse direkt in die Model Card.

    Wird von ``tooluse_exporter.finalize_model()`` (Path A) und von
    ``aggregate_from_benchmark_csvs()`` (Path B) nach erfolgreichen
    Tool-Use-Runs aufgerufen, damit die Card immer den aktuellen verifizierten
    Stand widerspiegelt.

    Tri-State-Semantik für ``supports_tool_use`` (Capability-Flag, flach):
    - ``True``         — Modell kann Tools aufrufen (Capability oder empirisch verifiziert).
    - ``False``        — Modell kann keine Tools aufrufen (Capability oder empirisch verifiziert).
    - ``"untested"``   — noch kein Tool-Use-Benchmark gelaufen.
                         ``tested_at`` ist in diesem Fall ``None`` und der
                         entsprechende ``tooluse_runs.{profile_id}``-Eintrag
                         wird aus der Card entfernt.

    Pro-Profil-Run-State (nested unter ``tooluse_runs``):
    - ``tooluse_runs.{profile_id}.tested_at``     : ISO-8601-Timestamp
    - ``tooluse_runs.{profile_id}.score_p1``      : mittlerer P1-Score (Phase 1)
    - ``tooluse_runs.{profile_id}.score_p2``      : mittlerer P2-Score (Phase 2)

    Args:
        model_id: Kanonische Modell-ID (SSoT für Card-Lookup, bleibt unverändert).
        profile_id: Kanonische Profil-ID des konkreten Runs. Default = ``model_id``.
                    Für Dual-Thinking-Profile (z.B. ``qwen3_6-27B-thinking``)
                    MUSS die Profil-ID übergeben werden, damit Standard- und
                    Thinking-Run getrennt persistiert werden und sich nicht
                    gegenseitig überschreiben. ``qwen3_6-27B-thinking`` und
                    ``qwen3_6-27B`` schreiben in zwei separate Slots auf der
                    SELBEN Card.
        preserve_supports_tool_use: Wenn True, wird der bestehende
            ``supports_tool_use``-Wert der Card beibehalten. Path B
            (Re-Aggregation) nutzt das, weil ein Mock-Run mit p1=0 nicht
            bedeutet dass das Modell keine Tools kann (Capability-Flag aus
            dem Card-Setup ist die maßgebliche Quelle). Path A (finalize_model)
            setzt False (Default) und überschreibt das Flag mit dem verifizierten
            Test-Result.

    Returns:
        True wenn die Card erfolgreich aktualisiert wurde, False bei Fehler.
    """
    if supports_tool_use not in _SUPPORT_TOOL_USE_VALUES:
        raise ValueError(
            f"supports_tool_use muss True, False oder {SUPPORT_TOOL_USE_UNTESTED!r} sein, "
            f"bekommen: {supports_tool_use!r}"
        )

    effective_profile_id = profile_id if profile_id else model_id

    card_path = _find_card(model_id)
    if not card_path.exists():
        logger.debug("update_model_card_tooluse_fields: Keine Card gefunden für '%s'", model_id)
        return False
    try:
        data = json.loads(card_path.read_text(encoding="utf-8"))
        if not preserve_supports_tool_use:
            data["supports_tool_use"] = (
                supports_tool_use
                if not isinstance(supports_tool_use, str)
                else SUPPORT_TOOL_USE_UNTESTED
            )
        # Sonst: bestehenden Wert in data["supports_tool_use"] unverändert lassen.
        # Wenn die Card noch kein Feld hat (Draft), bleibt sie flag-los — das ist
        # OK weil tooluse_runs.{profile_id}.tested_at der Test-Indikator ist.

        _persist_tooluse_data(data, effective_profile_id, tested_at, p1_score, p2_score)

        card_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.debug(
            "Model Card aktualisiert: model=%s profile=%s → supports_tool_use=%s, "
            "tooluse_runs[%s]=%s",
            model_id, effective_profile_id, supports_tool_use,
            effective_profile_id, data.get("tooluse_runs", {}).get(effective_profile_id),
        )
        return True
    except Exception:
        logger.warning("Konnte Model Card nicht aktualisieren für '%s'", model_id, exc_info=True)
        return False
