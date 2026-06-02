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
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Import constants and config logic
from .config import ROOT_DIR, SCORES_DIR

# Ensure root dir in path for local imports
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# pylint: disable=import-error
try:
    from utils.module_registry import get_active_modules
    from utils.model_utils import _find_card
except ImportError:
    get_active_modules = None  # type: ignore
    _find_card = None  # type: ignore
# pylint: enable=import-error


def _build_card_lookups() -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    SSoT: Liest alle Model Cards und baut zwei Lookups:
    1. {beliebiger_model_string → kanonische_model_id}
    2. {kanonische_model_id → display_name}

    Returns:
        Tuple von (id_lookup, display_lookup)
    """
    import re as _re_card
    id_lookup: Dict[str, str] = {}
    display_lookup: Dict[str, str] = {}
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
        except (json.JSONDecodeError, OSError):
            continue

    return id_lookup, display_lookup


# Backward compat wrapper
def _build_model_id_lookup() -> Dict[str, str]:
    """Legacy: gibt nur den ID-Lookup zurück."""
    id_lookup, _ = _build_card_lookups()
    return id_lookup


# Global caches (lazy init)
_ID_LOOKUP: Optional[Dict[str, str]] = None
_DISPLAY_LOOKUP: Optional[Dict[str, str]] = None


def _get_lookups() -> Tuple[Dict[str, str], Dict[str, str]]:
    global _ID_LOOKUP, _DISPLAY_LOOKUP
    if _ID_LOOKUP is None or _DISPLAY_LOOKUP is None:
        _ID_LOOKUP, _DISPLAY_LOOKUP = _build_card_lookups()
    return _ID_LOOKUP, _DISPLAY_LOOKUP


def _get_model_id_lookup() -> Dict[str, str]:
    """Legacy: gibt nur den ID-Lookup zurück."""
    return _get_lookups()[0]


def _resolve_to_canonical_id(model_str: str) -> str:
    """
    SSoT-Resolver: Bildet einen beliebigen Model-String auf die kanonische
    `model_id` aus der Model Card ab.

    Wichtig: Es wird NIE stille gekürzt — wenn keine Card gefunden wird,
    wird der Original-String zurückgegeben (Fallback). Der Caller entscheidet
    dann, wie damit umzugehen ist.
    """
    if not model_str or pd.isna(model_str):
        return ""
    raw = str(model_str).strip()
    if not raw:
        return ""

    id_lookup, _ = _get_lookups()

    # 1. Exakter Match
    if raw in id_lookup:
        return id_lookup[raw]

    # 2. Vendor-Prefix entfernen
    if "/" in raw:
        bare = raw.rsplit("/", 1)[-1]
        if bare in id_lookup:
            return id_lookup[bare]

    # 3. Suffix-Strip als letzter Fallback (z.B. -20250929, -0127)
    import re as _re_resolve
    stripped = _re_resolve.sub(r"-\d{4,8}$", "", raw)
    if stripped in id_lookup:
        return id_lookup[stripped]
    if "/" in stripped:
        stripped_bare = stripped.rsplit("/", 1)[-1]
        if stripped_bare in id_lookup:
            return id_lookup[stripped_bare]

    # 4. Fallback: Original zurückgeben (SSoT-Prinzip: keine stille Mutation)
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


def _enrich_from_csv_source(
    result: pd.DataFrame, label: str, source_config: Dict[str, Any]
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

    try:
        source_df = pd.read_csv(file_path)

        # 1. SSoT: Map both sides to canonical model_id (no string truncation)
        if "model" in source_df.columns:
            if "model_version" not in source_df.columns:
                source_df["model_version"] = "unknown"
            source_df["model_version"] = source_df["model_version"].fillna("unknown")
            source_df["model"] = source_df["model"].apply(_resolve_to_canonical_id)

        if "model" in result.columns:
            result["_model_canonical"] = result["model"].apply(_resolve_to_canonical_id)
        else:
            result["_model_canonical"] = result.index.astype(str)

        # 2. Key Filtering
        filters = source_config.get("filter", {})
        for col, val in filters.items():
            if col in source_df.columns:
                source_df = source_df[source_df[col] == val]

        # 3. Deduplicate
        if "model" in source_df.columns:
            source_df = source_df.drop_duplicates(
                subset=["model", "model_version"], keep="last"
            )

        # 4. Value Construction
        template = source_config.get("value_template")
        json_key = source_config.get("key")
        fallback = source_config.get("missing_value", "Pending")

        def safe_format(row):
            try:
                not_capable_col = source_config.get("not_capable_column")
                if not_capable_col and not_capable_col in row.index:
                    if str(row[not_capable_col]).lower() in ("false", "0", "no", "n"):
                        return source_config.get("not_capable_value", "n/a")

                json_col = None
                if "metadata_json" in row:
                    json_col = "metadata_json"
                elif "metrics_json" in row:
                    json_col = "metrics_json"

                if json_key and json_col:
                    try:
                        metrics = json.loads(row[json_col])
                        val = metrics
                        for k in json_key.split("."):
                            if isinstance(val, dict):
                                val = val.get(k, {})
                            else:
                                return "Error (Struct)"
                        if isinstance(val, (dict, list)):
                            return json.dumps(val, ensure_ascii=False)
                        extracted_val = str(val) if val is not None else ""
                        fmt = source_config.get("format")
                        if fmt:
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
                        return extracted_val
                    except (json.JSONDecodeError, AttributeError):
                        return "Error (JSON)"

                if template:
                    data = row.to_dict()
                    rendered = template.format(**data)
                    if rendered.strip().startswith("(Shift:"):
                        return fallback
                    return rendered
                return ""
            except KeyError:
                return "Error (Key)"
            except Exception:
                return "Error"

        if template or json_key:
            source_df[label] = source_df.apply(safe_format, axis=1)
        else:
            source_df[label] = ""

        # 5. Merge on canonical model_id
        if "model" in source_df.columns:
            merge_source = source_df[["model", label]].rename(
                columns={"model": "_model_canonical"}
            ).drop_duplicates(subset=["_model_canonical"], keep="last")

            if label in result.columns:
                result = result.drop(columns=[label])

            result = result.merge(merge_source, on="_model_canonical", how="left")

        if "_model_canonical" in result.columns:
            result = result.drop(columns=["_model_canonical"])

        result[label] = result[label].fillna(fallback)

        # Model-card-based not-capable check
        not_capable_card_key = source_config.get("not_capable_card_key")
        not_capable_value = source_config.get("not_capable_value", "n/a")
        if not_capable_card_key and _find_card is not None:
            card_dir = ROOT_DIR / "benchmark_scores" / "model_cards"
            fallback_mask = result[label] == fallback
            if fallback_mask.any():
                for idx in result[fallback_mask].index:
                    model_id = str(result.at[idx, "model"])
                    card_path = _find_card(model_id, card_dir=card_dir)
                    if card_path.exists():
                        try:
                            card = json.loads(card_path.read_text())
                            if card.get(not_capable_card_key) is False:
                                result.at[idx, label] = not_capable_value
                        except Exception:
                            pass

    except Exception as e:
        print(f"Generic CSV Merge Error ({filename}): {e}")
        if label not in result.columns:
            result[label] = "Error"

    return result


def enrich_with_module_data(
    result: pd.DataFrame,
    cat_cols: List[str],
    modules_config: Dict[str, Any],
    full_config: Dict[str, Any],
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Merges custom/additional data columns for modules defined in their config.
    """
    if result.empty:
        return result, cat_cols

    if get_active_modules is None:
        return result, cat_cols

    active_modules_data = get_active_modules(full_config)

    for mod_id, _, mod_int_config in active_modules_data:
        if not mod_int_config.get("enabled", True):
            if modules_config and not modules_config.get(mod_id, {}).get(
                "enabled", True
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
