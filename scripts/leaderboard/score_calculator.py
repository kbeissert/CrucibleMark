"""
Core scoring and aggregation logic for leaderboard.
Calculates Routine vs Reasoning scores, aggregates stats, and classifies models.
"""

import json
import logging
import sys
from typing import Any

import pandas as pd
import yaml

# Import constants and config logic
from .config import ROOT_DIR, config

# Ensure root dir in path for local imports
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Removed unused imports from utils.module_registry as functionality is passed via config


# ==============================================================================
# 1b. PRICE LOOKUP (from model cards, cost_limits.yaml as legacy fallback)
# ==============================================================================

# Whitelist der "rein lokalen" deployment_types. Hybrid-Typen wie
# "open-weights-cloud-available" oder "cloud-and-local" zählen NICHT als
# lokal — diese Modelle haben einen Cloud-Preis und sollen nur diesen zeigen.
_LOCAL_DEPLOYMENT_TYPES = frozenset({"localweights", "local-weights"})


def _load_card_prices(lookup: dict[str, float]) -> None:
    """Reads model cards (primary SSoT) and populates lookup in-place."""
    import json as _json

    card_dir = ROOT_DIR / "benchmark_scores" / "model_cards"
    for card_path in card_dir.glob("*.json"):
        try:
            with open(card_path, encoding="utf-8") as f:
                card = _json.load(f)
            if not isinstance(card, dict):
                continue
            model_id = card.get("model_id")
            if not model_id:
                continue
            price_per_m = card.get("output_price_per_1m")
            if isinstance(price_per_m, (int, float)):
                lookup[model_id] = float(price_per_m) / 1000.0
            elif card.get("deployment_type") in _LOCAL_DEPLOYMENT_TYPES:
                # Lokales Modell ohne expliziten Preis → 0.0 (Defense-in-Depth)
                lookup[model_id] = 0.0
        except (OSError, _json.JSONDecodeError):
            continue


def _load_cost_limits_prices(lookup: dict[str, float]) -> None:
    """Legacy fallback: cost_limits.yaml entries for models not yet in a card."""
    cost_limits_path = ROOT_DIR / "config" / "cost_limits.yaml"
    try:
        with open(cost_limits_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        providers = data.get("providers", {})
        for _provider, models in providers.items():
            if not isinstance(models, dict):
                continue
            for model_name, model_data in models.items():
                if not isinstance(model_data, dict):
                    continue
                price = model_data.get("output_cost_per_1k")
                if isinstance(price, (int, float)) and model_name not in lookup:
                    lookup[model_name] = float(price)
    except (OSError, yaml.YAMLError):
        pass


def _build_price_lookup() -> dict[str, float]:
    """
    Builds a flat {model_id: output_cost_per_1k} dict.

    Primary source: model card JSON files (benchmark_scores/model_cards/*.json).
    Legacy fallback: cost_limits.yaml entries for models without a card yet.
    Card prices take precedence; cost_limits.yaml is only used for models
    not yet covered by a card (e.g. cloud proxies, uncommon models).

    Defense-in-Depth: Cards with deployment_type in LOCAL_DEPLOYMENT_TYPES
    (e.g. "localweights") default to 0.0 if output_price_per_1m is missing
    or null. Lokale Modelle haben keine API-Kosten — eine leere Preis-Zelle
    verfälscht die Benchmark-Cost-Berechnung.
    """
    lookup: dict[str, float] = {}
    _load_card_prices(lookup)
    _load_cost_limits_prices(lookup)
    return lookup


def _lookup_price(model_ver: str, model_name: str, lookup: dict[str, float]) -> float | None:
    """
    Resolves output_cost_per_1k for a model.

    Match priority:
      1. Exact match on model_version
      2. Exact match on full model name (e.g. 'z-ai/glm-5-turbo-20260315')
      3. Prefix match on full model name, longest key first
         (e.g. 'z-ai/glm-5-turbo-20260315' → 'z-ai/glm-5-turbo')
    """
    if model_ver and model_ver in lookup:
        return lookup[model_ver]
    if model_name and model_name in lookup:
        return lookup[model_name]
    if model_name:
        for key in sorted(lookup.keys(), key=len, reverse=True):
            if model_name.startswith(key):
                return lookup[key]
    return None

_PRICE_LOOKUP: dict[str, float] | None = None


def _get_price_lookup() -> dict[str, float]:
    """Returns cached price lookup dict (lazy init)."""
    # pylint: disable=global-statement
    global _PRICE_LOOKUP  # noqa: PLW0603
    if _PRICE_LOOKUP is None:
        _PRICE_LOOKUP = _build_price_lookup()
    return _PRICE_LOOKUP


# ==============================================================================
# 1c. COVERAGE STATUS CLASSIFICATION (v5.0 — Coverage-aware Scoring)
# ==============================================================================
#
# v5.0 generalisiert die Modul-Abdeckungs-Logik auf ALLE Scoring-Module.
# Ein Modul kann pro Modell einen von 6 Status haben:
#   present      — ≥1 gültige Row (status ∈ _VALID_STATUSES) → trägt zum Score bei
#   missing      — keine gültigen Rows, Modul anwendbar → Malus (im Nenner, nicht im Zähler)
#   unknown      — keine gültigen Rows, capability_field fehlt in Card → wie missing + WARNING
#   incapable    — capability_field explizit false in Card → exempt (aus Nenner entfernt)
#   not_deployed — Modul hat 0 Daten für alle Modelle → für alle aus Nenner entfernt
#   rolling_out  — Modul hat Daten für < deployment_threshold der Modelle → für alle aus Nenner entfernt
#
# SSoT für incapable/incapable-Erkennung sind die Model Cards
# (benchmark_scores/model_cards/*.json). CARD_DIR wird respektiert (test-isolierbar).

_coverage_logger = logging.getLogger(__name__)

# Capability-Werte, die ein Modell als strukturell "incapable" markieren.
# Ein FEHLENDES Feld ist NICHT incapable (→ unknown), sondern muss explizit false sein.
_INCAPABLE_VALUES = frozenset({False, "false", "not_applicable"})

# Cache für alle Model Cards: {model_id: card_dict}. Invalide bei CARD_DIR-Wechsel.
_CARDS_CACHE: dict[str, dict[str, Any]] | None = None
_CARDS_CACHE_DIR: Any = None


def _load_all_cards() -> dict[str, dict[str, Any]]:
    """Lädt alle Model Cards in {model_id: card_dict}. Lazy-cached, CARD_DIR-aware.

    Respektiert utils.model_card_io.CARD_DIR (von conftest auf tmp_path umgelenkt),
    sodass Tests mit synthetischen Cards isoliert laufen. Der Cache invalide
    automatisch, sobald CARD_DIR sich ändert.
    """
    # pylint: disable=import-outside-toplevel,global-statement
    global _CARDS_CACHE, _CARDS_CACHE_DIR
    from pathlib import Path as _Path

    from utils.model_card_io import CARD_DIR as _card_dir

    card_dir = _Path(_card_dir)
    if _CARDS_CACHE is not None and card_dir == _CARDS_CACHE_DIR:
        return _CARDS_CACHE

    cards: dict[str, dict[str, Any]] = {}
    if card_dir.exists():
        for card_path in card_dir.glob("*.json"):
            if card_path.name == "_index.json":
                continue
            try:
                with open(card_path, encoding="utf-8") as f:
                    card = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(card, dict) and card.get("model_id"):
                cards[card["model_id"]] = card

    _CARDS_CACHE = cards
    _CARDS_CACHE_DIR = card_dir
    return cards


def clear_cards_cache() -> None:
    """Invalidiert den Model-Card-Cache (`_CARDS_CACHE`).

    Aufrufen, wenn Model Cards zur Laufzeit hinzugefügt/geändert/entfernt werden
    (z.B. in langlaufenden Prozessen oder Services). Im Batch-Benchmark-Pattern
    (start → compute → exit) nicht nötig — der Cache invalide automatisch bei
    CARD_DIR-Wechsel.
    """
    # pylint: disable=global-statement
    global _CARDS_CACHE, _CARDS_CACHE_DIR
    _CARDS_CACHE = None
    _CARDS_CACHE_DIR = None


def _resolve_canonical(model_str: str) -> str:
    """Löst einen rohen Model-String auf die kanonische Card model_id auf.

    Nutzt die SSoT-Funktion _resolve_to_canonical_id aus module_integration.
    Fallback: der Input-String selbst (wenn keine Card gefunden wird).
    """
    # pylint: disable=import-outside-toplevel
    try:
        from .module_integration import _resolve_to_canonical_id
    except ImportError:
        return str(model_str)
    return _resolve_to_canonical_id(str(model_str))


def _get_incapable_models(modules_config: dict[str, Any]) -> dict[str, set[str]]:
    """Returns {category_name: set_of_model_ids} für strukturell incapable Modelle.

    Ein Modell ist "incapable" für ein Modul, wenn die Card das capability_field
    EXPLIZIT auf einen Wert in _INCAPABLE_VALUES ({False, "false",
    "not_applicable"}) setzt. Ein fehlendes Feld ist NICHT incapable (→ unknown,
    separat in _classify_module_status erkannt).

    Nur Scoring-Module mit gesetztem capability_field werden ausgewertet.
    """
    cards = _load_all_cards()
    incapable_map: dict[str, set[str]] = {}
    for mod_key, mod_data in modules_config.items():
        if not mod_data.get("enable_scoring", True):
            continue
        cap_field = mod_data.get("capability_field")
        if not cap_field:
            continue
        cat_name = mod_data.get("name", mod_key)
        incapable_ids: set[str] = set()
        for model_id, card in cards.items():
            if cap_field in card and card[cap_field] in _INCAPABLE_VALUES:
                incapable_ids.add(model_id)
        incapable_map[cat_name] = incapable_ids
    return incapable_map


def _get_deployed_scoring_modules(
    df_success: pd.DataFrame,
    modules_config: dict[str, Any],
    total_model_count: int,
    deployment_threshold: float = 0.10,
) -> tuple[set[str], set[str]]:
    """Returns (deployed_modules, rolling_out_modules) anhand der Deployment-Schwelle.

    - deployed: ≥ deployment_threshold × total_model_count Modelle haben gültige
      Daten → missing/unknown-Modelle werden bestraft.
    - rolling_out: > 0 aber < threshold → für alle aus Nenner entfernt (INFO-Log).
    - not_deployed (0 Daten): implizit ausgeschlossen (nicht in beiden Sets).
    """
    deployed: set[str] = set()
    rolling_out: set[str] = set()
    for mod_key, mod_data in modules_config.items():
        if not mod_data.get("enable_scoring", True):
            continue
        cat = mod_data.get("name", mod_key)
        if "category" in df_success.columns:
            module_df = df_success[df_success["category"] == cat]
        else:
            module_df = pd.DataFrame()
        model_count = module_df["model"].nunique() if not module_df.empty else 0
        if model_count == 0:
            continue  # not_deployed → für alle ausgeschlossen
        ratio = model_count / total_model_count if total_model_count > 0 else 0.0
        if ratio >= deployment_threshold:
            deployed.add(cat)
        else:
            rolling_out.add(cat)
            _coverage_logger.info(
                "Module '%s' has data for %d/%d models (< threshold %.2f), "
                "treating as rolling_out — excluded from scoring",
                cat, model_count, total_model_count, deployment_threshold,
            )
    return deployed, rolling_out


def _classify_module_status(
    model_str: str,
    model_version: str,
    category: str,
    present_set: set[tuple[str, str, str]],
    incapable_map: dict[str, set[str]],
    modules_config: dict[str, Any],
    attempted_set: set[tuple[str, str, str]] | None = None,
) -> str:
    """Klassifiziert den Status eines Moduls für ein Modell.

    Returns: 'present' | 'missing' | 'unknown' | 'incapable'

    - present: (model, model_version, category) hat ≥1 gültige Row (status in _VALID_STATUSES)
    - incapable: keine Rows überhaupt (auch keine error-Rows) UND model in incapable_map[category]
      (capability_field explizit false in Card). Wurde das Modell getestet (≥1 Row
      jeglichen Status), ist es NICHT incapable sondern missing — getestet und
      durchgefallen ist kein Capability-Mangel.
    - unknown: keine Rows UND capability_field konfiguriert UND Feld fehlt in Card
      → WARNING-Log
    - missing: keine validen Rows, fähig (Feld present+true, oder kein capability_field)

    v5.1: attempted_set (aus df_all, inkl. error-Rows) verhindert, dass Modelle
    mit error-Rows als incapable eingestuft werden. Ein Modell, das angetreten
    ist und durchgefallen ist, ist missing, nicht incapable.
    """
    if (str(model_str), str(model_version), category) in present_set:
        return "present"

    incapable_ids = incapable_map.get(category, set())
    canonical = _resolve_canonical(model_str)
    if canonical in incapable_ids:
        # v5.1: Wenn das Modell Rows für diese Category hat (auch error-Rows),
        # wurde es getestet → nicht incapable, sondern missing.
        if attempted_set is not None and (
            str(model_str), str(model_version), category
        ) in attempted_set:
            _coverage_logger.info(
                "Model '%s' is marked incapable for module '%s' but has "
                "attempted rows — classifying as missing (tested, not incapable)",
                model_str, category,
            )
            # Fall through to missing/unknown-Logik unten
        else:
            return "incapable"

    # unknown-Detection: capability_field konfiguriert, aber Feld fehlt in Card
    mod_data = _find_mod_data_by_category(modules_config, category)
    cap_field = mod_data.get("capability_field") if mod_data else None
    if cap_field:
        cards = _load_all_cards()
        card = cards.get(canonical)
        if card is None or cap_field not in card:
            _coverage_logger.warning(
                "Model '%s' has no capability_field '%s' in card for module "
                "'%s' — treating as missing with warning",
                model_str, cap_field, category,
            )
            return "unknown"

    return "missing"


def _find_mod_data_by_category(
    modules_config: dict[str, Any], category: str
) -> dict[str, Any] | None:
    """Findet den mod_data-Eintrag für einen Kategorienamen."""
    for _mk, _md in modules_config.items():
        if _md.get("name", _mk) == category:
            return _md
    return None


# ==============================================================================
# 2. HELPERS: SCORING (Granular Contribution)
# ==============================================================================


def _get_row_contribution(
    row: pd.Series,
    asset_contrib_map: dict[str, dict[str, float]],
    cat_to_config: dict[str, Any],
) -> tuple[float, float, float, float]:
    """
    Helper to calculate routine/reasoning contribution AND weights for a single row.
    Returns: (contrib_routine, contrib_reasoning, weight_routine, weight_reasoning)
    """

    # Helper to get weights
    def get_weights_from_map_or_fallback():
        asset_id = row.get("asset_id")
        if asset_id in asset_contrib_map:
            c = asset_contrib_map[asset_id]
            return float(c.get("routine", 0.0)), float(c.get("reasoning", 0.0))

        # Module-Level Default
        cat = row.get("category", "")
        mod_conf = cat_to_config.get(cat, {})
        def_contrib = mod_conf.get("default_contribution", {})
        return float(def_contrib.get("routine", 0.0)), float(
            def_contrib.get("reasoning", 0.0)
        )

    w_routine, w_reasoning = get_weights_from_map_or_fallback()
    pct = float(row.get("percentage", 0))

    # 1. Try CSV Values first
    try:
        r_raw = row.get("routine_contribution")
        l_raw = row.get("reasoning_contribution")

        if (
            pd.notna(r_raw)
            and pd.notna(l_raw)
            and str(r_raw).strip()
            and str(l_raw).strip()
        ):
            # SUCCESS: Use pre-calculated values
            # Return weights from config map because extracting them from contrib/pct is unsafe if pct=0
            return float(r_raw), float(l_raw), w_routine, w_reasoning
    except (ValueError, TypeError):
        pass

    # 2. Variable Calculation Fallback
    return pct * w_routine, pct * w_reasoning, w_routine, w_reasoning


def _calculate_group_scores(
    df: pd.DataFrame, modules_config: dict[str, Any]
) -> pd.DataFrame:
    """
    Calculates Routine vs Reasoning scores using granular contributions (v3 logic).
    Returns DataFrame with [model, model_version, Routine Score, Reasoning Score].
    """
    df_calc = df.copy()

    # 1. Active Modules Filter
    cat_to_config = {
        mod_data.get("name", k): mod_data
        for k, mod_data in modules_config.items()
        if mod_data.get("enabled", True)
    }

    active_cats = set(cat_to_config.keys())
    df_calc = df_calc[df_calc["category"].isin(active_cats)]

    # Filter out non-scoring modules
    df_calc = df_calc[
        df_calc["category"].apply(
            lambda c: cat_to_config.get(c, {}).get("enable_scoring", True)
        )
    ]

    if df_calc.empty:
        return pd.DataFrame()

    # 2. Build Asset Map
    asset_contrib_map = {}
    for mod_data in cat_to_config.values():
        for b in mod_data.get("benchmarks", []):
            if "score_contribution" in b and "id" in b:
                asset_contrib_map[b["id"]] = b["score_contribution"]

    # 2b. Build module-weight scale factors (self-normalizing, Subset-safe)
    # module_weight / sum_of_config_weights_in_that_module → scale per asset row.
    # Falls module_weight=None (kein Eintrag), scale=1.0 (Rückwärtskompatibilität).
    # Nutzt die SSoT-Funktion _compute_module_scale_factors (Drift-Schutz gemeinsam
    # mit _compute_expected_module_weights für den Coverage-Malus).
    def _module_scale(mod_data: dict[str, Any]) -> float:
        return _compute_module_scale_factors(mod_data)[0]

    module_weight_scales: dict[str, float] = {
        cat_name: _module_scale(mod_data)
        for cat_name, mod_data in cat_to_config.items()
    }

    # 3. Apply Scoring
    contribs = df_calc.apply(
        lambda r: _get_row_contribution(r, asset_contrib_map, cat_to_config),
        axis=1,
        result_type="expand",
    )

    if contribs.empty:
        df_calc["final_routine"] = 0.0
        df_calc["final_reasoning"] = 0.0
        df_calc["weight_routine"] = 0.0
        df_calc["weight_reasoning"] = 0.0
    else:
        # Apply module-weight scaling so that module_weight controls relative influence,
        # independent of asset count. Result stays 0–100 (self-normalizing via weighted avg).
        scale = df_calc["category"].map(lambda c: module_weight_scales.get(c, 1.0))
        df_calc["final_routine"] = contribs[0] * scale
        df_calc["final_reasoning"] = contribs[1] * scale
        df_calc["weight_routine"] = contribs[2] * scale
        df_calc["weight_reasoning"] = contribs[3] * scale

    # 4. Aggregation: Sum / Sum of Weights
    scores = (
        df_calc.groupby(["model", "model_version"])
        .agg(
            sum_routine=("final_routine", "sum"),
            sum_reasoning=("final_reasoning", "sum"),
            total_weight_routine=("weight_routine", "sum"),
            total_weight_reasoning=("weight_reasoning", "sum"),
            count=("asset_id", "count"),
        )
        .reset_index()
    )

    # Calculate Total Weight (Global denominator for components)
    scores["total_weight_global"] = (
        scores["total_weight_routine"] + scores["total_weight_reasoning"]
    )

    # Calculate Component Scores (Weighted Contribution to Total)
    # This ensures Routine Score + Reasoning Score = Total Score
    scores["Routine Score"] = scores.apply(
        lambda x: (
            x["sum_routine"] / x["total_weight_global"]
            if x["total_weight_global"] > 0
            else 0
        ),
        axis=1,
    )
    scores["Reasoning Score"] = scores.apply(
        lambda x: (
            x["sum_reasoning"] / x["total_weight_global"]
            if x["total_weight_global"] > 0
            else 0
        ),
        axis=1,
    )

    # Return intermediate sums for weighted total calculation
    return scores[
        [
            "model",
            "model_version",
            "Routine Score",
            "Reasoning Score",
            "sum_routine",
            "sum_reasoning",
            "total_weight_routine",
            "total_weight_reasoning",
        ]
    ]


# ==============================================================================
# 3. HELPERS: STATS AGGREGATION
# ==============================================================================


def _build_scoring_category_map(
    modules_config: dict[str, Any]
) -> dict[str, bool]:
    """Maps module category name → enable_scoring flag."""
    return {
        mod_data.get("name", mod_key): mod_data.get("enable_scoring", True)
        for mod_key, mod_data in modules_config.items()
    }


def _normalize_numeric_columns(df: pd.DataFrame) -> None:
    """Coerce numeric aggregation columns in-place; prevents string-concat in sum."""
    cols_to_numeric = [
        "execution_time",
        "cost_usd",
        "tokens_used",
        "tokens_per_second",
        "load_time",
    ]
    for col in cols_to_numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if "llm_judge_score" in df.columns:
        df["llm_judge_score"] = pd.to_numeric(df["llm_judge_score"], errors="coerce")


def _agg_standard_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates standard metrics (execution_time, cost, tokens) excluding 'System'."""
    df_metrics = df[df["category"] != "System"].copy()
    base_aggs = {"execution_time": "mean", "asset_id": "count"}

    if "cost_usd" in df_metrics.columns:
        base_aggs["cost_usd"] = "sum"
    if "tokens_used" in df_metrics.columns:
        base_aggs["tokens_used"] = "sum"
    if "tokens_per_second" in df_metrics.columns:
        df_metrics["tokens_per_second"] = pd.to_numeric(
            df_metrics["tokens_per_second"], errors="coerce"
        )
        base_aggs["tokens_per_second"] = "mean"

    return (
        df_metrics.groupby(["model", "model_version", "type"])
        .agg(base_aggs)
        .reset_index()
    )


def _agg_load_time(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates max load_time per (model, version, type); empty DF if no column."""
    if "load_time" not in df.columns:
        return pd.DataFrame()
    return (
        df.groupby(["model", "model_version", "type"])["load_time"]
        .max()
        .reset_index()
    )


def _agg_time_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregates rigorous execution_time stats (mean, max, p95, p99, timeouts)."""

    def p95(x):
        return x.quantile(0.95)

    def p99(x):
        return x.quantile(0.99)

    def count_timeouts(x):
        return (x > 120.0).sum()

    return (
        df.groupby(["model", "model_version", "type"])["execution_time"]
        .agg(
            Avg_Time="mean",
            Max_Time="max",
            P95_Time=p95,
            P99_Time=p99,
            Timeout_Count=count_timeouts,
        )
        .reset_index()
    )


def _merge_scoring_stats(
    base_stats: pd.DataFrame,
    df: pd.DataFrame,
    scoring_df: pd.DataFrame,
) -> pd.DataFrame:
    """Merges scoring-only percentage stats into base_stats; fills default 0.0 fallback."""
    if not scoring_df.empty:
        score_aggs = {"percentage": "mean"}
        if "performance_ratio" in df.columns:
            score_aggs["performance_ratio"] = "mean"

        score_stats = (
            scoring_df.groupby(["model", "model_version", "type"])
            .agg(score_aggs)
            .reset_index()
        )
        stats = pd.merge(
            base_stats, score_stats, on=["model", "model_version", "type"], how="left"
        )
    else:
        stats = base_stats.copy()
        stats["percentage"] = 0.0
        if "performance_ratio" in df.columns:
            stats["performance_ratio"] = 0.0

    if "percentage" in stats.columns:
        stats["percentage"] = stats["percentage"].fillna(0.0)
    if "performance_ratio" in stats.columns:
        stats["performance_ratio"] = stats["performance_ratio"].fillna(0.0)
    return stats


def _build_judge_applicable_categories(
    modules_config: dict[str, Any]
) -> set[str]:
    """Returns set of category names whose module UUID is in llm_judge.applicable_modules."""
    llm_judge_cfg = config.get("llm_judge", {})
    applicable_modules = llm_judge_cfg.get("applicable_modules", [])
    applicable_categories: set[str] = set()
    for mod_key, mod_data in modules_config.items():
        if mod_key in applicable_modules:
            name = mod_data.get("name", mod_key)
            applicable_categories.add(name)
    return applicable_categories


def _merge_judge_stats(
    stats: pd.DataFrame,
    df: pd.DataFrame,
    modules_config: dict[str, Any],
) -> pd.DataFrame:
    """Merges llm_judge avg+coverage stats; skips rows with judge_progress_status=skip."""
    if "llm_judge_score" not in df.columns:
        stats["llm_judge_avg"] = None
        stats["judge_coverage"] = 0.0
        return stats

    applicable_categories = _build_judge_applicable_categories(modules_config)
    df_judge = df[df["category"].isin(applicable_categories)]

    # Judge-Skip-Zeilen aus Coverage-Berechnung ausschließen:
    # judge_progress_status=⚠️ Judge: skip (zu kurz/abgelehnt) bedeutet absichtlich
    # übersprungen, nicht fehlgeschlagen → zählt nicht gegen Coverage.
    if "judge_progress_status" in df_judge.columns:
        df_judge = df_judge[
            ~df_judge["judge_progress_status"].str.contains("skip", na=False, case=False)
        ]

    def calc_coverage(x):
        return x.notna().sum() / len(x) if len(x) > 0 else 0.0

    judge_stats = (
        df_judge.groupby(["model", "model_version", "type"])["llm_judge_score"]
        .agg(llm_judge_avg="mean", judge_coverage=calc_coverage)
        .reset_index()
    )
    stats = pd.merge(
        stats, judge_stats, on=["model", "model_version", "type"], how="left"
    )
    # Ensure we fill judge_coverage with 0.0 if not available for a model
    stats["judge_coverage"] = stats["judge_coverage"].fillna(0.0)
    return stats


def _aggregate_basic_stats(
    df: pd.DataFrame, modules_config: dict[str, Any]
) -> pd.DataFrame:
    """Aggregates percentage, time and counts. Handles non-scoring modules correctly."""

    cat_to_scoring = _build_scoring_category_map(modules_config)

    def is_scoring_asset(row):
        cat = row.get("category", "")
        return cat_to_scoring.get(cat, True)

    _normalize_numeric_columns(df)

    # 1. Base Stats (Presence, Time) - From ALL valid runs (scoring + info)

    # SPLIT AGGREGATION:
    # - Execution Time: Excluding "System" probes (to avoid skewing averages with 0.1s dummy values)
    # - Load Time: Using ALL rows (System probe carries the Max Load Time)

    # A) Standard Metrics (without System Probe)
    stats_metrics = _agg_standard_metrics(df)

    # B) Load Time (Include System Probe because it has the Cold Start data)
    stats_load = _agg_load_time(df)

    # Merge results if load stats exist
    if not stats_load.empty:
        base_stats = pd.merge(
            stats_metrics, stats_load, on=["model", "model_version", "type"], how="left"
        )
    else:
        base_stats = stats_metrics

    # Calculate rigorous time stats
    time_stats = _agg_time_stats(df)
    # Merge time stats into base stats
    base_stats = pd.merge(base_stats, time_stats, on=["model", "model_version", "type"])

    # 2. Scoring Stats (Percentage) - From SCORING runs only
    scoring_df = df[df.apply(is_scoring_asset, axis=1)]
    stats = _merge_scoring_stats(base_stats, df, scoring_df)

    # 3. Judge Stats - From valid/applicable runs only
    return _merge_judge_stats(stats, df, modules_config)


def _logical_run_count_for_group(
    sub_df: pd.DataFrame,
    counting_cats: set[str],
    name_to_override: dict[str, int],
) -> int:
    """Berechnet die logische Test-Anzahl für eine Modell-Gruppe.

    v5.0: Nur Rows mit gültigem Status zählen (konsistent mit der Scoring-Basis
    df_success). Error-Rows produzieren keinen Score und dürfen "Tests Run" nicht
    als komplett ausweisen (z.B. llama-4-scout mit 6 ToolUse-Errors → 43/49
    incomplete, nicht 49/49).
    """
    count = 0
    valid_df = sub_df[sub_df["status"].isin(_VALID_STATUSES)]
    cats = valid_df["category"].unique()
    for cat in cats:
        if cat not in counting_cats:
            continue
        row_count = len(valid_df[valid_df["category"] == cat])
        if cat in name_to_override:
            if row_count > 0:
                count += name_to_override[cat]
        else:
            count += row_count
    return count


def _expected_assets_for_model(
    model_str: str,
    expected_assets: int,
    incapable_map: dict[str, set[str]],
    cat_assets: dict[str, int],
    attempted_canonical_cats: set[tuple[str, str]] | None = None,
) -> int:
    """v5.0: Per-Modell expected_assets — incapable-Module werden abgezogen.

    v5.1: Ein Modell, das Rows für ein Module hat (auch error-Rows), wurde
    getestet → nicht incapable → kein Abzug. Nur Modelle ohne jegliche Rows
    für das incapable-Module bekommen den Abzug.
    """
    canonical = _resolve_canonical(str(model_str))
    reduction = 0
    for _cat, incapable_ids in incapable_map.items():
        if canonical in incapable_ids:
            # v5.1: Wenn das Modell Rows für diese Category hat, wurde es
            # getestet → nicht incapable → kein Abzug.
            if attempted_canonical_cats is not None and (
                canonical, _cat
            ) in attempted_canonical_cats:
                continue
            reduction += cat_assets.get(_cat, 0)
    return expected_assets - reduction


def _calculate_run_counts(
    df: pd.DataFrame,
    modules_config: dict[str, Any],
    incapable_map: dict[str, set[str]] | None = None,
) -> pd.DataFrame:
    """Calculates 'Tests Run' using logic overrides (e.g. PC = 9 tests).

    v5.0: `incapable_map` kann vom Caller übergeben werden (vermeidet doppelte
    Berechnung — wird auch in _apply_coverage_malus benötigt). Bei None wird es
    hier berechnet (Rückwärtskompatibilität für externe Caller).
    """

    name_to_override = {}
    expected_assets = 0
    counting_cats = set()

    for _, mod_data in modules_config.items():
        if not mod_data.get("enabled", True):
            continue

        name = mod_data.get("name")
        # Only count assets towards expected total if scoring is enabled OR if explicit display count is set
        if mod_data.get("enable_scoring", True) or mod_data.get("display_test_count"):
            expected_assets += mod_data.get("assets_count", 0)
            counting_cats.add(name)

        if mod_data.get("display_test_count"):
            name_to_override[name] = int(mod_data.get("display_test_count"))

    run_counts = (
        df.groupby(["model", "model_version", "type"])
        .apply(
            lambda sub: _logical_run_count_for_group(
                sub, counting_cats, name_to_override
            )
        )
        .reset_index(name="logical_count")
    )

    # v5.0: Per-Modell expected_assets — incapable-Module werden abgezogen,
    # damit incapable-Modelle nicht als "incomplete" markiert werden.
    # v5.1: Modelle mit Rows (auch error) sind nicht incapable → kein Abzug.
    if incapable_map is None:
        incapable_map = _get_incapable_models(modules_config)
    cat_assets: dict[str, int] = {}
    for _mk, _md in modules_config.items():
        _cat = _md.get("name", _mk)
        if _md.get("enable_scoring", True) or _md.get("display_test_count"):
            cat_assets[_cat] = int(_md.get("assets_count", 0))

    # v5.1: attempted_canonical_cats — (canonical_id, category) für alle Modelle
    # mit ≥1 Row (inkl. error). Verhindert expected_assets-Abzug für getestete
    # Modelle, deren Card fälschlich supports_tool_use:false sagt.
    attempted_canonical_cats: set[tuple[str, str]] = set()
    if not df.empty and "category" in df.columns:
        for _, _row in df[["model", "category"]].iterrows():
            _canon = _resolve_canonical(str(_row["model"]))
            attempted_canonical_cats.add((_canon, str(_row["category"])))

    run_counts["expected_assets"] = run_counts["model"].apply(
        lambda m: _expected_assets_for_model(
            m, expected_assets, incapable_map, cat_assets,
            attempted_canonical_cats,
        )
    )

    return run_counts


def _calculate_stability_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates stability score based on average Category Variance Coefficient.
    CV = StdDev / Mean.
    Higher Score (>0.5) = High Variance (Unstable/Variable).
    Lower Score (<0.3) = Low Variance (Stable).
    """
    # 1. Filter valid execution times
    # Ensure numeric
    df_perf = df.copy()
    if "execution_time" not in df_perf.columns:
        return pd.DataFrame()

    df_perf["execution_time"] = pd.to_numeric(
        df_perf["execution_time"], errors="coerce"
    )
    df_perf = df_perf[df_perf["execution_time"] > 0]

    if df_perf.empty:
        return pd.DataFrame()

    # 2. Calculate PER-ASSET Stats (Mean, Std)
    # Group by Model, Version, Type AND Asset ID (compare runs of same asset)
    # v3.1 Fix: Use per-asset variance instead of per-category to avoid flagging models
    # as unstable simply because they have diverse task durations (e.g. 5s vs 50s tasks).
    asset_stats = (
        df_perf.groupby(["model", "model_version", "type", "asset_id"])[
            "execution_time"
        ]
        .agg(asset_mean="mean", asset_std="std")
        .reset_index()
    )

    # Handle single-item variance (std is NaN) -> CV is 0 (Stable)
    asset_stats["asset_std"] = asset_stats["asset_std"].fillna(0)

    # 3. Calculate normalized variability per asset.
    #    Uses σ / global_mean instead of CV (σ/μ) to avoid penalizing
    #    inherently fast tasks (e.g. 0.1s ± 0.05s CV=0.5 vs 10s ± 1s CV=0.1).
    global_mean = df_perf["execution_time"].mean()
    if global_mean > 0:
        asset_stats["asset_nv"] = asset_stats["asset_std"] / global_mean
    else:
        asset_stats["asset_nv"] = 0.0

    # 4. Average the normalized variabilities across all assets (Asset-Aware Stability)
    stability_stats = (
        asset_stats.groupby(["model", "model_version", "type"])["asset_nv"]
        .agg(stability_score="mean")
        .reset_index()
    )

    # stability_score is e.g. 0.26 (26%), 0.69 (69%)
    return stability_stats


# ==============================================================================
# 4. MAIN ORCHESTRATOR
# ==============================================================================


# Statuses counted as valid completions (treated as non-error by the runner).
_VALID_STATUSES = frozenset(
    {"success", "language_mismatch", "truncated", "verbose_outlier", "refusal"}
)


def _resolve_category_for_asset(asset_id: str, modules_config: dict[str, Any]) -> str:
    """Map asset_id to its module category name; special-case System probes."""
    # Special Case: System Probes
    if asset_id in ("system_warmup_probe", "warmup_probe"):
        return "System"

    for mod_key, mod_data in modules_config.items():
        if "prefix" in mod_data and str(asset_id).startswith(
            str(mod_data["prefix"])
        ):
            return str(mod_data.get("name", mod_key))
        if str(asset_id).startswith(mod_key):
            return str(mod_data.get("name", mod_key))
    return "Other"


def _prepare_input_data(
    df: pd.DataFrame, modules_config: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Returns (df_all, df_success, scoring_df) after category+status filtering.

    - df_all: all rows with assigned category and 'Other' filtered out
    - df_success: subset with status in _VALID_STATUSES, plus performance_ratio
    - scoring_df: subset of df_success with enable_scoring=True (same base as Total Score)
    """
    df_all = df.copy()
    df_all["category"] = df_all["asset_id"].apply(
        lambda aid: _resolve_category_for_asset(aid, modules_config)
    )
    # Filter "Other" but KEEP "System"
    df_all = df_all[df_all["category"] != "Other"]

    df_success = df_all[df_all["status"].isin(_VALID_STATUSES)].copy()
    # Performance Ratio (kept equal to percentage; preserved for downstream compat)
    df_success["performance_ratio"] = df_success["percentage"]

    # scoring_df: only assets from modules with enable_scoring=True (same base as Total Score)
    cat_to_scoring = _build_scoring_category_map(modules_config)
    scoring_df = df_success[
        df_success["category"].map(lambda c: cat_to_scoring.get(c, True))
    ]
    return df_all, df_success, scoring_df


def _finalize_completion_status(result: pd.DataFrame) -> pd.DataFrame:
    """Set is_complete + 'Tests Run' string column from expected_assets/logical_count.

    v5.0: expected_assets ist nun per-Modell (incapable-Modelle haben reduzierte
    Erwartung). 'Tests Run' nutzt den per-Modell-Wert, is_complete den globalen
    Max-Wert (damit ein incapable-Modell mit 43/43 als 'complete' gilt, aber ein
    present-Modell mit 43/49 nicht).
    """
    expected_max = (
        result["expected_assets"].max() if "expected_assets" in result.columns else 0
    )
    # is_complete: ein Modell ist komplett wenn es SEINE eigene Erwartung erfüllt
    if "expected_assets" in result.columns:
        result["is_complete"] = result["logical_count"] >= result["expected_assets"]
        result["Tests Run"] = result.apply(
            lambda r: str(int(r["logical_count"])) + "/" + str(int(r["expected_assets"])),
            axis=1,
        )
    else:
        result["is_complete"] = result["logical_count"] >= expected_max
        result["Tests Run"] = result["logical_count"].apply(
            lambda x: str(int(x)) + "/" + str(expected_max)
        )
    if "expected_assets" in result.columns:
        result = result.drop(columns=["expected_assets"])
    return result


def _add_category_breakdown(
    result: pd.DataFrame, df_success: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Adds per-category percentage breakdown; returns (result, cat_stats)."""
    cat_stats = (
        df_success.groupby(["model", "model_version", "category"])["percentage"]
        .mean()
        .unstack()
        .reset_index()
    )
    result = pd.merge(result, cat_stats, on=["model", "model_version"], how="left")
    return result, cat_stats


def _override_tokens_with_scoring_only(
    result: pd.DataFrame, scoring_df: pd.DataFrame
) -> pd.DataFrame:
    """Override tokens_used total with scoring-only sum (same base as Total Score).

    _aggregate_basic_stats() sums tokens across ALL non-system rows (incl. Political
    Compass). Overwrite here with scoring-only sum so that Tokens Total has the same
    static base as Total Score — re-test runs (e.g. Political Compass retests) don't
    distort the value.
    """
    if "tokens_used" in scoring_df.columns and "tokens_used" in result.columns:
        token_totals = (
            scoring_df.groupby(["model", "model_version"])["tokens_used"]
            .sum()
            .reset_index()
        )
        result = result.drop(columns=["tokens_used"])
        result = pd.merge(result, token_totals, on=["model", "model_version"], how="left")
    return result


def _add_token_breakdown(
    result: pd.DataFrame, scoring_df: pd.DataFrame
) -> pd.DataFrame:
    """Adds per-module token breakdown; excludes non-scoring modules for static totals."""
    if "tokens_used" not in scoring_df.columns:
        return result
    token_by_module = (
        scoring_df.groupby(["model", "model_version", "category"])["tokens_used"]
        .sum()
        .unstack()
        .reset_index()
    )
    token_by_module.columns = [
        f"Tokens: {col}" if col not in ("model", "model_version") else col
        for col in token_by_module.columns
    ]
    return pd.merge(result, token_by_module, on=["model", "model_version"], how="left")


def _calc_weighted_total(row: pd.Series) -> float:
    """Volume-weighted total score from routine+reasoning contributions."""
    w_routine = row.get("total_weight_routine", 0)
    w_reasoning = row.get("total_weight_reasoning", 0)
    sum_routine = row.get("sum_routine", 0)
    sum_reasoning = row.get("sum_reasoning", 0)

    total_weight = w_routine + w_reasoning
    total_sum = sum_routine + sum_reasoning

    if total_weight > 0:
        return total_sum / total_weight
    # Fallback if no weights (should not happen)
    return 0.0


def _calc_cost_per_1k_tokens_row(
    row: pd.Series, price_lookup: dict[str, float]
) -> float | None:
    """Match by model_version, then full model name, then prefix (longest key first)."""
    model_ver = str(row.get("model_version", "") or "").strip()
    model_name = str(row.get("model", "") or "").strip()
    return _lookup_price(model_ver, model_name, price_lookup)


def _calc_benchmark_cost_row(row: pd.Series) -> float | None:
    """Absolute benchmark cost in USD.

    Primary:  (Tokens Total / 1000) × Cost per 1K (USD)
    Fallback: cost_usd (sum from benchmark CSVs) for date-suffixed OpenRouter models
              and any other model whose name doesn't match the price lookup exactly.
    """
    price = row.get("Cost per 1K (USD)")
    tokens = row.get("tokens_used")
    try:
        price_f = float(price)  # type: ignore[arg-type]
        tokens_f = float(tokens)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        price_f = float("nan")
        tokens_f = float("nan")
    if not pd.isna(price_f) and not pd.isna(tokens_f) and tokens_f > 0:
        return round((tokens_f / 1000) * price_f, 4)
    # Fallback: use recorded cost_usd sum (covers OpenRouter + date-suffix models)
    try:
        fallback = float(row.get("cost_usd") or 0)  # type: ignore[arg-type]
        return round(fallback, 4) if fallback > 0 else None
    except (TypeError, ValueError):
        return None


def _calc_efficiency_index(row: pd.Series) -> float:
    """Routine Score per second of Avg Task Duration; 0 if execution_time missing/0."""
    exec_time = row.get("execution_time", 0)
    if exec_time > 0:
        return row["Routine Score"] / exec_time
    return 0.0


def _merge_granular_scores(
    result: pd.DataFrame,
    df_success: pd.DataFrame,
    modules_config: dict[str, Any],
) -> pd.DataFrame:
    """Merges Routine/Reasoning granular scores; guarantees non-NaN columns."""
    granular_scores = _calculate_group_scores(df_success, modules_config)

    if not granular_scores.empty:
        result = pd.merge(
            result, granular_scores, on=["model", "model_version"], how="left"
        )
    else:
        # Fallback if granular calc fails (should not happen)
        result["Routine Score"] = 0.0
        result["Reasoning Score"] = 0.0

    result["Routine Score"] = result["Routine Score"].fillna(0.0)
    result["Reasoning Score"] = result["Reasoning Score"].fillna(0.0)
    return result


def _merge_stability_score(
    result: pd.DataFrame, df_success: pd.DataFrame
) -> pd.DataFrame:
    """Merges stability score (v3.1 per-asset variability); sets 0.0 default fallback."""
    stability = _calculate_stability_score(df_success)
    if not stability.empty:
        result = pd.merge(
            result, stability, on=["model", "model_version", "type"], how="left"
        )
    else:
        result["stability_score"] = 0.0
    return result


# ==============================================================================
# 4b. COVERAGE MALUS (v5.0 — Generalized Coverage-aware Scoring)
# ==============================================================================


def _compute_module_scale_factors(
    mod_data: dict[str, Any],
) -> tuple[float, float, float]:
    """Berechnet (scale, config_weight_routine, config_weight_reasoning) für ein Modul.

    SSoT für die Scale-Logik — wird sowohl von `_module_scale` (present-Module)
    als auch von `_compute_expected_module_weights` (Malus für missing/unknown)
    genutzt, damit beide identische Gewichte produzieren (Drift-Schutz).

    - module_weight=None → scale=1.0 (Rückwärtskompatibilität)
    - config_weight_sum<=0 → Fallback über assets_count × default_sum
    """
    module_weight = mod_data.get("module_weight")
    benchmarks = mod_data.get("benchmarks", [])
    default_contrib = mod_data.get(
        "default_contribution", {"routine": 0.0, "reasoning": 0.0}
    )
    default_r = float(default_contrib.get("routine", 0.0))
    default_re = float(default_contrib.get("reasoning", 0.0))
    default_sum = default_r + default_re

    config_weight_r = 0.0
    config_weight_re = 0.0
    for b in benchmarks:
        sc = b.get("score_contribution")
        if sc:
            config_weight_r += float(sc.get("routine", 0.0))
            config_weight_re += float(sc.get("reasoning", 0.0))
        else:
            config_weight_r += default_r
            config_weight_re += default_re

    config_weight_sum = config_weight_r + config_weight_re
    if module_weight is None:
        scale = 1.0
    else:
        if config_weight_sum <= 0:
            config_weight_sum = max(
                float(mod_data.get("assets_count", 1)) * max(default_sum, 1.0), 1.0
            )
        scale = float(module_weight) / config_weight_sum
    return scale, config_weight_r, config_weight_re


def _compute_expected_module_weights(
    mod_data: dict[str, Any],
) -> tuple[float, float]:
    """Berechnet die routine/reasoning-Gewichte, die ein voll present-Modul zum
    Nenner beitragen würde. Nutzt die SSoT-Funktion `_compute_module_scale_factors`.

    Returns: (expected_w_routine, expected_w_reasoning)

    Bei module_weight=None: scale=1.0, Gewichte = Σ(contributions).
    Bei gesetztem module_weight: scale × config_weight_sum = module_weight.
    """
    scale, config_weight_r, config_weight_re = _compute_module_scale_factors(mod_data)
    return scale * config_weight_r, scale * config_weight_re


def _build_model_category_set(
    df: pd.DataFrame | None,
) -> set[tuple[str, str, str]]:
    """Baut ein Set von (model, model_version, category)-Tuples aus einem DataFrame.

    Wird für present_set (aus df_success) und attempted_set (aus df_all) genutzt.
    """
    if df is None or df.empty or "category" not in df.columns:
        return set()
    mv_col = (
        df["model_version"].astype(str)
        if "model_version" in df.columns
        else pd.Series([""] * len(df), index=df.index)
    )
    tuples_df = pd.DataFrame(
        {
            "m": df["model"].astype(str),
            "mv": mv_col,
            "cat": df["category"].astype(str),
        }
    )
    return set(tuples_df.itertuples(index=False, name=None))


def _apply_coverage_malus(
    result: pd.DataFrame,
    df_success: pd.DataFrame,
    modules_config: dict[str, Any],
    deployment_threshold: float = 0.10,
    incapable_map: dict[str, set[str]] | None = None,
    df_all: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """v5.0: Generalisierter Coverage-Malus.

    Für jedes Modell werden missing/unknown Scoring-Module (deployed aber keine
    gültigen Daten, nicht incapable) identifiziert. Ihre erwarteten Gewichte
    werden zum Nenner addiert OHNE Zähler-Beitrag → Score-Reduktion.

    Incapable-Module werden komplett aus dem Nenner entfernt.
    Not-deployed und rolling_out-Module werden für alle Modelle ausgeschlossen.

    Berechnet coverage_ratio = Σ(present weights) / Σ(present + missing + unknown).

    v5.1: df_all (inkl. error-Rows) wird genutzt, um attempted_set zu bauen.
    Ein Modell mit error-Rows für ein Module wurde getestet → missing, nicht
    incapable. Nur Modelle mit 0 Rows überhaupt können incapable sein.

    KRITISCH: Recomputiert Routine Score und Reasoning Score nach Modifikation der
    Gewichte, da _calculate_group_scores() sie mit dem Original-Nenner berechnet.
    Ohne Recomputation wäre die Invariante Routine + Reasoning = Total verletzt.
    """
    if result.empty:
        result["coverage_ratio"] = 1.0
        return result

    total_model_count = result["model"].nunique()
    deployed, _rolling_out = _get_deployed_scoring_modules(
        df_success, modules_config, total_model_count, deployment_threshold
    )
    if incapable_map is None:
        incapable_map = _get_incapable_models(modules_config)

    # present_set: (model, model_version, category) mit ≥1 gültiger Row
    present_set = _build_model_category_set(df_success)

    # v5.1: attempted_set aus df_all (inkl. error-Rows) — für striktere
    # incapable-Klassifikation. Ein Modell mit error-Rows wurde getestet.
    attempted_set = _build_model_category_set(df_all) if df_all is not None else set()

    # Erwartete Gewichte pro deployed Scoring-Modul vorab berechnen
    expected_weights: dict[str, tuple[float, float]] = {}
    deployed_module_cats: list[tuple[str, dict[str, Any]]] = []
    for mod_key, mod_data in modules_config.items():
        if not mod_data.get("enable_scoring", True):
            continue
        cat = mod_data.get("name", mod_key)
        if cat not in deployed:
            continue
        expected_weights[cat] = _compute_expected_module_weights(mod_data)
        deployed_module_cats.append((cat, mod_data))

    # coverage_ratio-Spalte initialisieren
    result["coverage_ratio"] = 1.0

    for idx, row in result.iterrows():
        model = str(row.get("model", ""))
        mver = str(row.get("model_version", ""))
        added_routine = 0.0
        added_reasoning = 0.0
        present_weight = 0.0
        denom_weight = 0.0

        for cat, _mod_data in deployed_module_cats:
            exp_r, exp_re = expected_weights.get(cat, (0.0, 0.0))
            mw_total = exp_r + exp_re
            status = _classify_module_status(
                model, mver, cat, present_set, incapable_map, modules_config,
                attempted_set,
            )
            if status == "present":
                present_weight += mw_total
                denom_weight += mw_total
            elif status in ("missing", "unknown"):
                added_routine += exp_r
                added_reasoning += exp_re
                denom_weight += mw_total
            # incapable: weder Zähler noch Nenner

        # Gewichte aktualisieren
        new_tw_r = float(row.get("total_weight_routine", 0.0)) + added_routine
        new_tw_re = float(row.get("total_weight_reasoning", 0.0)) + added_reasoning
        result.at[idx, "total_weight_routine"] = new_tw_r
        result.at[idx, "total_weight_reasoning"] = new_tw_re

        # Routine/Reasoning/coverage_ratio recomputieren
        tw_global = new_tw_r + new_tw_re
        sum_r = float(row.get("sum_routine", 0.0))
        sum_re = float(row.get("sum_reasoning", 0.0))
        if tw_global > 0:
            result.at[idx, "Routine Score"] = sum_r / tw_global
            result.at[idx, "Reasoning Score"] = sum_re / tw_global
        else:
            result.at[idx, "Routine Score"] = 0.0
            result.at[idx, "Reasoning Score"] = 0.0

        result.at[idx, "coverage_ratio"] = (
            present_weight / denom_weight if denom_weight > 0 else 0.0
        )

    return result


def _add_cost_columns(
    result: pd.DataFrame, price_lookup: dict[str, float]
) -> pd.DataFrame:
    """Adds Cost per 1K (USD) and Benchmark Cost (USD) columns to result in-place."""
    # Cost per 1K Output Tokens — from model cards (cost_limits.yaml as legacy fallback).
    # Uses the published output_price_per_1m for each known model, converted to per-1K.
    # Local-only models (deployment_type ∈ {"localweights", "local-weights"}) default to 0.0
    # even without an explicit price (see _build_price_lookup Defense-in-Depth).
    # Models without a card price AND not marked local-only (e.g. cloud-only,
    # hybrid cloud-and-local) receive None → empty in the leaderboard.
    result["Cost per 1K (USD)"] = result.apply(
        lambda r: _calc_cost_per_1k_tokens_row(r, price_lookup), axis=1
    )

    # Benchmark Cost (USD) — absolute cost for the full benchmark run.
    if "tokens_used" in result.columns:
        result["Benchmark Cost (USD)"] = result.apply(
            _calc_benchmark_cost_row, axis=1
        )

    return result


def _add_efficiency_index(result: pd.DataFrame) -> pd.DataFrame:
    """Adds Efficiency_Index column (Routine Score / execution_time)."""
    result["Efficiency_Index"] = result.apply(_calc_efficiency_index, axis=1)
    return result


def _finalize_leaderboard_columns(result: pd.DataFrame) -> pd.DataFrame:
    """Drops temp columns, renames to display labels, and sorts by Total Score."""
    # Remove temporary calculation columns
    cols_to_drop = [
        "sum_routine",
        "sum_reasoning",
        "total_weight_routine",
        "total_weight_reasoning",
        "Avg_Time",
    ]
    result = result.drop(columns=[c for c in cols_to_drop if c in result.columns])

    # Cleanup Renaming
    result = result.rename(
        columns={
            "percentage": "Overall Score",
            "performance_ratio": "Performance Ratio",
            "execution_time": "Avg Task Duration (s)",
            "load_time": "Initial Load Time (s)",
            "Max_Time": "Max Time (s)",
            "P95_Time": "P95 Time (s)",
            "P99_Time": "P99 Time (s)",
            "Timeout_Count": "Timeout Count",
            "type": "Type",
            "llm_judge_avg": "LLM Judge Avg",
            "judge_coverage": "LLM Judge Coverage",
            "tokens_used": "Tokens Total",
            "tokens_per_second": "Tokens/s",
        }
    )

    # Sort by Total Score (v1.1)
    if "Total Score" in result.columns:
        return result.sort_values("Total Score", ascending=False)
    if "Overall Score" in result.columns:
        return result.sort_values("Overall Score", ascending=False)
    return result


def calculate_scores(
    df: pd.DataFrame, modules_config: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main entry point for scoring calculations.

    Args:
        df: Raw benchmark data (pandas DataFrame)
        modules_config: Configuration dictionary for active modules

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]:
            1. Main leaderboard stats (model-level)
            2. Category stats (stats per module category)
    """
    df_all, df_success, scoring_df = _prepare_input_data(df, modules_config)

    # v5.0: incapable_map einmal berechnen und an run_counts + malus durchreichen
    # (vermeidet doppelte Card-Iteration in beiden Funktionen).
    _incapable_map = _get_incapable_models(modules_config)

    # Aggregation
    stats = _aggregate_basic_stats(df_success, modules_config)
    # Note: uses Full DF (incl non-scoring)
    run_counts = _calculate_run_counts(df_all, modules_config, _incapable_map)

    # Merge Counts
    result = pd.merge(
        stats, run_counts, on=["model", "model_version", "type"], how="left"
    )

    # Completion Status
    result = _finalize_completion_status(result)

    # Category Stats
    result, cat_stats = _add_category_breakdown(result, df_success)

    # Tokens: override total + per-module breakdown
    result = _override_tokens_with_scoring_only(result, scoring_df)
    result = _add_token_breakdown(result, scoring_df)

    # Routine vs Reasoning (v2.1: Granular Weights)
    result = _merge_granular_scores(result, df_success, modules_config)

    # v5.0: Generalized Coverage Malus (missing/unknown → penalize, incapable → exempt)
    _lb_cfg = config.get("leaderboard", {}) if isinstance(config, dict) else {}
    _deployment_threshold = float(
        _lb_cfg.get(
            "deployment_threshold", config.get("deployment_threshold", 0.10)
        )
    )
    result = _apply_coverage_malus(
        result, df_success, modules_config, _deployment_threshold, _incapable_map,
        df_all,
    )

    # Stability Score (v3.1 Logic)
    result = _merge_stability_score(result, df_success)

    # Total Score Calculation (Volume-Weighted)
    result["Total Score"] = result.apply(_calc_weighted_total, axis=1)

    # Cost columns from model cards + cost_limits.yaml fallback
    result = _add_cost_columns(result, _get_price_lookup())

    # Efficiency Index
    result = _add_efficiency_index(result)

    # Cleanup + Rename + Sort
    result = _finalize_leaderboard_columns(result)

    return result, cat_stats
