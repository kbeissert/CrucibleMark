"""
Integration of external module data into leaderboard.
Handles generic CSV merging and value extraction based on module configuration.

SSoT (Single Source of Truth):
- Die kanonische Model-Identität lebt in `benchmark_scores/model_cards/*.json` (Feld `model_id`).
- Alle Cross-File-Mappings (z.B. tooluse_leaderboard.csv → benchmark_leaderboard) laufen
  über die `_resolve_to_canonical_id()` Funktion, die den Input-String auf die
  kanonische `model_id` aus der Model Card auflöst.
- KEINE String-Kürzung im Code — der Original-String bleibt erhalten, wenn keine
  Card gefunden wird (Fallback).
- Der `display_name` aus der Model Card wird über `_resolve_to_display_name()`
  als separater Anzeigename aufgelöst.
"""

import json
import sys
from typing import Any

import pandas as pd

# Import constants and config logic
from .config import ROOT_DIR, SCORES_DIR

# Ensure root dir in path for local imports
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# pylint: disable=import-error
try:
    from utils.module_registry import get_active_modules
    from utils.model_utils import _find_card, resolve_canonical_model_id, _safe_name
    from utils.config_validator import ConfigValidator
except ImportError:
    get_active_modules = None  # type: ignore
    _find_card = None  # type: ignore
    resolve_canonical_model_id = None  # type: ignore
    _safe_name = None  # type: ignore
    ConfigValidator = None  # type: ignore
# pylint: enable=import-error


def _build_card_lookups() -> tuple[dict[str, str], dict[str, str]]:
    """
    SSoT: Liest alle Model Cards und baut zwei Lookups:
    1. {beliebiger_model_string → kanonische_model_id}
    2. {kanonische_model_id → display_name}

    Returns:
        Tuple von (id_lookup, display_lookup)
    """
    import re as _re_card
    id_lookup: dict[str, str] = {}
    display_lookup: dict[str, str] = {}
    card_dir = ROOT_DIR / "benchmark_scores" / "model_cards"
    if not card_dir.exists():
        return id_lookup, display_lookup

    for card_path in card_dir.glob("*.json"):
        if card_path.name == "_index.json":
            continue
        try:
            card = json.loads(card_path.read_text(encoding="utf-8"))
            canonical_id = card.get("model_id")
            display_name = card.get("display_name")
            if not canonical_id:
                continue

            # Display-Lookup: nur für kanonische IDs
            if display_name:
                display_lookup[canonical_id] = display_name

            # ID-Lookup: alle Repräsentationen mappen
            # 1. Exakte model_id
            id_lookup[canonical_id] = canonical_id
            # 2. Display-Name → kanonische ID
            if display_name:
                id_lookup[display_name] = canonical_id
            # 3. Card-Dateiname
            id_lookup[card_path.stem] = canonical_id
            # 4. Suffix-strip
            stripped = _re_card.sub(r"-\d{4,8}$", "", canonical_id)
            if stripped != canonical_id:
                id_lookup[stripped] = canonical_id
            # 5. Vendor-Prefix-strip
            if "/" in canonical_id:
                bare = canonical_id.rsplit("/", 1)[-1]
                id_lookup[bare] = canonical_id
                bare_stripped = _re_card.sub(r"-\d{4,8}$", "", bare)
                if bare_stripped != bare:
                    id_lookup[bare_stripped] = canonical_id
            # Hinweis: Ein Dot↔Underscore-Bridge ist NICHT mehr nötig, weil
            # die model_id bereits zentral in ``unified_runner.py`` via
            # ``resolve_canonical_model_id()`` kanonisiert wird, bevor sie
            # jemals die CSVs oder den Leaderboard-Pfad erreicht.
        except (json.JSONDecodeError, OSError):
            continue

    return id_lookup, display_lookup


def _add_thinking_profile_names(
    id_lookup: dict[str, str],
    display_lookup: dict[str, str],
) -> None:
    """Ergänzt display_lookup für Thinking-Profile (card_model_id-Redirect).

    Thinking-Profile haben keine eigene Card — sie teilen sich die Card des
    Original-Modells via ``card_model_id``. Daher findet ``_build_card_lookups()``
    keinen Eintrag für ``{id}-thinking``. Diese Funktion lädt die expandierte
    Config und trägt den Display-Namen aus der geteilten Card ein — derselbe
    Name wie das Original-Modell. Die Unterscheidung erfolgt über die
    ``thinking_mode``-Spalte, nicht über den Display-Namen.
    """
    if ConfigValidator is None or _safe_name is None:
        return
    try:
        config = ConfigValidator(str(ROOT_DIR / "benchmark_config.yaml")).config
    except Exception:  # pylint: disable=broad-except
        return
    # Provider sind verschachtelt: providers.local.<provider_key>.models[]
    local_providers = config.get("providers", {}).get("local", {})
    for _provider_key, provider_data in local_providers.items():
        if not isinstance(provider_data, dict):
            continue
        for model_cfg in provider_data.get("models", []):
            if "card_model_id" not in model_cfg:
                continue
            profile_id = _safe_name(model_cfg["id"])
            # Display-Name aus der geteilten Card übernehmen (gleicher Name)
            card_ref = _safe_name(model_cfg["card_model_id"])
            if card_ref in display_lookup:
                display_lookup[profile_id] = display_lookup[card_ref]
            elif profile_id not in display_lookup:
                display_lookup[profile_id] = card_ref
            id_lookup[profile_id] = profile_id


# Backward compat wrapper
def _build_model_id_lookup() -> dict[str, str]:
    """Legacy: gibt nur den ID-Lookup zurück."""
    id_lookup, _ = _build_card_lookups()
    return id_lookup


# Global caches (lazy init)
_ID_LOOKUP: dict[str, str] | None = None
_DISPLAY_LOOKUP: dict[str, str] | None = None


def _get_lookups() -> tuple[dict[str, str], dict[str, str]]:
    global _ID_LOOKUP, _DISPLAY_LOOKUP
    if _ID_LOOKUP is None or _DISPLAY_LOOKUP is None:
        _ID_LOOKUP, _DISPLAY_LOOKUP = _build_card_lookups()
        _add_thinking_profile_names(_ID_LOOKUP, _DISPLAY_LOOKUP)
    return _ID_LOOKUP, _DISPLAY_LOOKUP


def _get_model_id_lookup() -> dict[str, str]:
    """Legacy: gibt nur den ID-Lookup zurück."""
    return _get_lookups()[0]


def _resolve_to_canonical_id(model_str: str) -> str:
    """
    Bridge zur kanonischen SSoT in ``utils.model_utils.resolve_canonical_model_id``.

    Die ehemalige Inline-Lookup-Tabelle (Display-Name, Suffix-Strip, Vendor-Prefix)
    lebt jetzt vollständig in der SSoT — diese Funktion ist ein dünner Adapter
    für die Bulk-Lookup-Semantik (ganze CSV-Spalten), die Card-Lookup-Tabelle
    bleibt über ``_build_card_lookups()`` für ``_resolve_to_display_name()``
    erhalten.
    """
    if not model_str or pd.isna(model_str):
        return ""
    raw = str(model_str).strip()
    if not raw:
        return ""

    if resolve_canonical_model_id is None:
        # Import-Fallback: kein utils-Modul verfügbar → kein Lookup möglich
        return raw

    # 1. Primärweg: SSoT (Card-Lookup, Suffix-Strip, safe_name-Fallback)
    canonical = resolve_canonical_model_id(raw)
    if canonical and canonical != raw:
        return canonical

    # 2. Fallback: lokaler Display-Name/Vendor-Prefix/Suffix-Lookup für
    #    Bulk-IDs (z.B. "Claude Sonnet 4.5" oder "gpt-4o" → kanonische ID)
    id_lookup, _ = _get_lookups()
    if raw in id_lookup:
        return id_lookup[raw]
    if "/" in raw:
        bare = raw.rsplit("/", 1)[-1]
        if bare in id_lookup:
            return id_lookup[bare]
    import re as _re_resolve
    stripped = _re_resolve.sub(r"-\d{4,8}$", "", raw)
    if stripped in id_lookup:
        return id_lookup[stripped]
    if "/" in stripped:
        stripped_bare = stripped.rsplit("/", 1)[-1]
        if stripped_bare in id_lookup:
            return id_lookup[stripped_bare]

    # 3. Letzter Fallback: Original-String (SSoT-Prinzip: keine stille Mutation)
    return raw


def _resolve_to_display_name(model_str: str) -> str:
    """
    SSoT-Resolver: Bildet einen beliebigen Model-String auf den `display_name`
    aus der Model Card ab.

    Returns: Der `display_name` aus der Model Card (z.B. "Claude Sonnet 4.5"),
             oder der Original-String als Fallback wenn keine Card gefunden wird.
    """
    canonical_id = _resolve_to_canonical_id(model_str)
    if not canonical_id:
        return ""
    _, display_lookup = _get_lookups()
    if canonical_id in display_lookup:
        return display_lookup[canonical_id]
    return canonical_id  # Fallback: model_id als Anzeigename


def _canonicalize_source_df(source_df: pd.DataFrame) -> pd.DataFrame:
    """SSoT: Map source_df 'model' to canonical model_id, fillna model_version."""
    if "model" in source_df.columns:
        if "model_version" not in source_df.columns:
            source_df["model_version"] = "unknown"
        source_df["model_version"] = source_df["model_version"].fillna("unknown")
        source_df["model"] = source_df["model"].apply(_resolve_to_canonical_id)
    return source_df


def _attach_canonical_key(result: pd.DataFrame) -> pd.DataFrame:
    """Adds '_model_canonical' join key on result for matching canonical IDs."""
    if "model" in result.columns:
        result["_model_canonical"] = result["model"].apply(_resolve_to_canonical_id)
    else:
        result["_model_canonical"] = result.index.astype(str)
    return result


def _apply_source_filters(
    source_df: pd.DataFrame, filters: dict[str, Any]
) -> pd.DataFrame:
    """Applies key filters (col == val) from source_config.filter."""
    for col, val in filters.items():
        if col in source_df.columns:
            source_df = source_df[source_df[col] == val]
    return source_df


def _dedupe_source_df(source_df: pd.DataFrame) -> pd.DataFrame:
    """Drop duplicate (model, model_version) entries, keep 'last'."""
    if "model" not in source_df.columns:
        return source_df
    return source_df.drop_duplicates(
        subset=["model", "model_version"], keep="last"
    )


def _check_not_capable(row: pd.Series, source_config: dict[str, Any]) -> str | None:
    """Returns not_capable_value if row's not_capable column is false-y, else None."""
    not_capable_col = source_config.get("not_capable_column")
    if (
        not_capable_col
        and not_capable_col in row.index
        and str(row[not_capable_col]).lower() in ("false", "0", "no", "n")
    ):
        return source_config.get("not_capable_value", "n/a")
    return None


def _resolve_json_value(
    row: pd.Series, json_col: str, json_key: str
) -> str:
    """Extracts dotted-json path value, returns empty/error string on failure."""
    try:
        metrics = json.loads(row[json_col])
    except (json.JSONDecodeError, AttributeError):
        return "Error (JSON)"

    val = metrics
    for k in json_key.split("."):
        if isinstance(val, dict):
            val = val.get(k, {})
        else:
            return "Error (Struct)"
    if isinstance(val, (dict, list)):
        return json.dumps(val, ensure_ascii=False)
    return str(val) if val is not None else ""


def _render_format_template(
    row: pd.Series, metrics: Any, extracted_val: str, source_config: dict[str, Any]
) -> str:
    """Renders fmt.format() with row + metrics context; returns extracted_val on KeyError."""
    fmt = source_config.get("format")
    if not fmt:
        return extracted_val
    ctx = row.to_dict()
    ctx["value"] = extracted_val
    if isinstance(metrics, dict):
        for mk, mv in metrics.items():
            if isinstance(mv, (str, int, float)):
                ctx[mk] = mv
            elif isinstance(mv, dict):
                for subk, subv in mv.items():
                    if isinstance(subv, (str, int, float)):
                        ctx[subk] = subv
    try:
        return fmt.format(**ctx)
    except KeyError:
        return extracted_val


def _render_template_string(
    row: pd.Series, template: str, fallback: str
) -> str:
    """Renders plain .format() template; returns fallback on empty/'(Shift:' prefix."""
    data = row.to_dict()
    cleaned = {k: ("" if pd.isna(v) else v) for k, v in data.items()}
    rendered = template.format(**cleaned)
    if not rendered.strip():
        return fallback
    if rendered.strip().startswith("(Shift:"):
        return fallback
    return rendered


def _safe_format_value(row: pd.Series, source_config: dict[str, Any]) -> str:
    """Top-level per-row formatter for enrichment (JSON or template branch).

    Decision order: not_capable > JSON path > template > ""; any error path
    yields a stable error marker.
    """
    try:
        not_capable = _check_not_capable(row, source_config)
        if not_capable is not None:
            return not_capable

        json_col = None
        if "metadata_json" in row:
            json_col = "metadata_json"
        elif "metrics_json" in row:
            json_col = "metrics_json"

        json_key = source_config.get("key")
        template = source_config.get("value_template")
        fallback = source_config.get("missing_value", "Pending")

        if json_key and json_col:
            extracted_val = _resolve_json_value(row, json_col, json_key)
            if extracted_val.startswith("Error"):
                return extracted_val
            metrics = json.loads(row[json_col])
            return _render_format_template(row, metrics, extracted_val, source_config)

        if template:
            return _render_template_string(row, template, fallback)
        return ""
    except KeyError:
        return "Error (Key)"
    except Exception:
        return "Error"


def _build_enrichment_column(
    source_df: pd.DataFrame, label: str, source_config: dict[str, Any]
) -> pd.DataFrame:
    """Sets source_df[label] via per-row formatting; empty string when no template/key."""
    template = source_config.get("value_template")
    json_key = source_config.get("key")
    if template or json_key:
        source_df[label] = source_df.apply(
            lambda r: _safe_format_value(r, source_config), axis=1
        )
    else:
        source_df[label] = ""
    return source_df


def _merge_enrichment_into(
    result: pd.DataFrame, source_df: pd.DataFrame, label: str
) -> pd.DataFrame:
    """Left-joins source_df label column on canonical model_id; cleans join helper."""
    if "model" not in source_df.columns:
        return result

    merge_source = (
        source_df[["model", label]]
        .rename(columns={"model": "_model_canonical"})
        .drop_duplicates(subset=["_model_canonical"], keep="last")
    )

    if label in result.columns:
        result = result.drop(columns=[label])

    result = result.merge(merge_source, on="_model_canonical", how="left")
    return result


def _apply_not_capable_card_check(
    result: pd.DataFrame, label: str, source_config: dict[str, Any], fallback: str
) -> pd.DataFrame:
    """Model-card state machine: false/'not_applicable' → not_capable_value override.

    State Machine für supports_tool_use:
    - false / "not_applicable" → Modell kann KEINE Tools → "n/a" im Leaderboard
    - true / "tested" → Scores vorhanden → Wert anzeigen
    - "untested" / anderer Wert → noch nicht getestet → "–" (missing_value)
    """
    not_capable_card_key = source_config.get("not_capable_card_key")
    not_capable_value = source_config.get("not_capable_value", "n/a")
    if not (not_capable_card_key and _find_card is not None):
        return result

    card_dir = ROOT_DIR / "benchmark_scores" / "model_cards"
    fallback_mask = result[label] == fallback
    if not fallback_mask.any():
        return result

    for idx in result[fallback_mask].index:
        model_id = str(result.at[idx, "model"])
        card_path = _find_card(model_id, card_dir=card_dir)
        if not card_path.exists():
            continue
        try:
            card = json.loads(card_path.read_text())
            card_val = card.get(not_capable_card_key)
            if card_val is False or card_val == "not_applicable":
                result.at[idx, label] = not_capable_value
        except Exception:
            pass
    return result


def _enrich_from_csv_source(
    result: pd.DataFrame, label: str, source_config: dict[str, Any]
) -> pd.DataFrame:
    """
    Generic Enrichment: Loads data from a custom CSV based on Config.
    Supports joining, filtering, and value templating.

    SSoT: Model-Identifikation läuft über die `model_id` aus den Model Cards
    via `_resolve_to_canonical_id()`. KEINE direkte String-Normalisierung.
    """
    filename = source_config.get("file")
    if not filename:
        return result

    file_path = SCORES_DIR / filename
    if not file_path.exists():
        fallback = source_config.get("missing_value", "Pending")
        result[label] = fallback
        return result

    fallback = source_config.get("missing_value", "Pending")
    try:
        source_df = pd.read_csv(file_path)

        # 1. SSoT: Map both sides to canonical model_id (no string truncation)
        source_df = _canonicalize_source_df(source_df)
        result = _attach_canonical_key(result)

        # 2. Key Filtering
        source_df = _apply_source_filters(source_df, source_config.get("filter", {}))

        # 3. Deduplicate
        source_df = _dedupe_source_df(source_df)

        # 4. Value Construction
        source_df = _build_enrichment_column(source_df, label, source_config)

        # 5. Merge on canonical model_id
        result = _merge_enrichment_into(result, source_df, label)
        if "_model_canonical" in result.columns:
            result = result.drop(columns=["_model_canonical"])

        result[label] = result[label].fillna(fallback)

        # Model-card-based not-capable check
        result = _apply_not_capable_card_check(result, label, source_config, fallback)

    except Exception as e:
        print(f"Generic CSV Merge Error ({filename}): {e}")
        if label not in result.columns:
            result[label] = "Error"

    return result


def enrich_with_module_data(
    result: pd.DataFrame,
    cat_cols: list[str],
    modules_config: dict[str, Any],
    full_config: dict[str, Any],
) -> tuple[pd.DataFrame, list[str]]:
    """
    Merges custom/additional data columns for modules defined in their config.
    """
    if result.empty:
        return result, cat_cols

    if get_active_modules is None:
        return result, cat_cols

    active_modules_data = get_active_modules(full_config)

    for mod_id, _, mod_int_config in active_modules_data:
        if (
            not mod_int_config.get("enabled", True)
            and modules_config
            and not modules_config.get(mod_id, {}).get("enabled", True)
        ):
            continue

        integration = mod_int_config.get("integration", {})
        lb_config = integration.get("leaderboard", {})
        columns_def = lb_config.get("columns", [])

        for col_def in columns_def:
            source = col_def.get("source")
            if source:
                label = col_def.get("label", col_def.get("id"))
                result = _enrich_from_csv_source(result, label, source)
                if label not in cat_cols:
                    cat_cols.append(label)

    return result, cat_cols
