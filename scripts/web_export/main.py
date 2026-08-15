# ruff: noqa: E402
from __future__ import annotations

import argparse
import datetime
import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from utils.config_validator import ConfigValidator
from utils.io_helpers import atomic_write_json as _atomic_write_json
from utils.model_id_base import strip_date_suffix
from utils.model_utils import WEIGHTS_TIER_DISPLAY, _safe_name
from utils.text_helpers import (
    normalize_pending,
    slugify,
    strip_emojis as _strip_emojis,
    strip_none as _strip_none,
)

from .constants import (
    LdbCols,
    _SCORES_CONTRACT_KEYS,
)

from .entry_builders import (
    _BENCHMARK_COST_MAX,
    _build_compass_entry,
    _build_leaderboard_entry,
    _build_tooluse_entry,
    _lookup_pc_row,
    load_model_card,
)
from .filters import (
    _build_community_alias_map,
    _build_community_card_id_lookup,
    _build_vendor_alias_map,
    _build_vendor_card_id_lookup,
    _is_blacklisted,
    _load_export_blacklist,
    _normalize_community,
    _normalize_vendor,
)
from .loader import (
    _build_pc_lookups,
    _load_pc_block_meta,
    _load_sources,
    build_provider_map,
    resolve_inference_provider,
)
from .top_level import (
    _build_benchmark_run_dates,
    _export_model_files,
    _resolve_dir,
    _review_date_range,
    _setup_output_dirs,
    _write_top_level_outputs,
)

def _init_export_context(
    root_dir: Path,
    scores_dir: Path,
    comparisons_path: Path,
) -> dict[str, Any]:
    """Lädt alle Datenquellen und baut Lookup-Maps auf."""
    _vendor_alias_map = _build_vendor_alias_map(root_dir / "config")
    _vendor_card_id_lookup = _build_vendor_card_id_lookup(root_dir / "config")
    _community_alias_map = _build_community_alias_map(root_dir / "config")
    _community_card_id_lookup = _build_community_card_id_lookup(root_dir / "config")

    provider_map = build_provider_map(root_dir / "benchmark_config.yaml")
    ldb, pc, pc_lb = _load_sources(scores_dir)
    if ldb is None:
        logging.error("❌ Failed to load required benchmark_leaderboard_detailed.csv. Exiting.")
        sys.exit(1)

    pc_lb_map, pc_lb_slug_map = _build_pc_lookups(pc_lb)
    block_meta = _load_pc_block_meta(root_dir / "benchmark_modules" / "political_compass" / "config.yaml")
    _benchmark_run_map = _build_benchmark_run_dates(root_dir / "outputs" / "runs")

    audit_logs_path = root_dir / "outputs" / "audit_logs"
    audit_dirs = {slugify(d.name): d for d in audit_logs_path.iterdir() if d.is_dir()} if audit_logs_path.exists() else {}
    comp_dirs = {slugify(d.name): d for d in comparisons_path.iterdir() if d.is_dir()} if comparisons_path.exists() else {}

    _bl_exact, _bl_pattern, _bl_total, _bl_loaded = _load_export_blacklist(root_dir=root_dir)
    if _bl_loaded and _bl_total:
        logging.info(
            f"  Blacklist: {_bl_total} Eintra(e)ge geladen "
            f"({len(_bl_exact)} exakt, {len(_bl_pattern)} Pattern)"
        )
    elif _bl_loaded:
        logging.info("  Blacklist: Datei geladen, leer.")

    # Provider-Config für card_model_id-Redirect (Dual-Thinking-Profile).
    # Graceful degradation: ohne Config bleibt load_model_card wie bisher.
    _provider_config: dict | None = None
    try:
        _provider_config = ConfigValidator().config
    except (OSError, ValueError, yaml.YAMLError) as exc:
        logging.debug("Provider-Config nicht ladbar — load_model_card ohne Redirect: %s", exc)

    # benchmark_cost-Sentinel-Threshold aus benchmark_config.yaml (SSoT,
    # Config-Driven). Fallback: _BENCHMARK_COST_MAX aus entry_builders.
    _benchmark_cost_max = _load_benchmark_cost_max(root_dir)

    return {
        "root_dir": root_dir,
        "comparisons_path": comparisons_path,
        "vendor_alias_map": _vendor_alias_map,
        "vendor_card_id_lookup": _vendor_card_id_lookup,
        "community_alias_map": _community_alias_map,
        "community_card_id_lookup": _community_card_id_lookup,
        "provider_map": provider_map,
        "provider_config": _provider_config,
        "ldb": ldb,
        "pc": pc,
        "pc_lb_map": pc_lb_map,
        "pc_lb_slug_map": pc_lb_slug_map,
        "block_meta": block_meta,
        "benchmark_run_map": _benchmark_run_map,
        "audit_dirs": audit_dirs,
        "comp_dirs": comp_dirs,
        "bl_exact": _bl_exact,
        "bl_pattern": _bl_pattern,
        "bl_total": _bl_total,
        "benchmark_cost_max": _benchmark_cost_max,
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
    }


def _load_benchmark_cost_max(root_dir: Path) -> float:
    """Liest web_export.benchmark_cost_max_usd aus benchmark_config.yaml.

    Fallback bei fehlender/unlesbarer Config oder ungültigem Wert:
    _BENCHMARK_COST_MAX (entry_builders) — der Export bricht nicht.
    """
    try:
        cfg = ConfigValidator(str(root_dir / "benchmark_config.yaml")).config
        value = float(cfg.get("web_export", {}).get("benchmark_cost_max_usd", _BENCHMARK_COST_MAX))
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        logging.debug("benchmark_cost_max nicht lesbar — Fallback %s: %s", _BENCHMARK_COST_MAX, exc)
        return _BENCHMARK_COST_MAX
    if value <= 0:
        logging.warning(
            "benchmark_cost_max_usd=%s ungültig (<= 0) — Fallback %s", value, _BENCHMARK_COST_MAX,
        )
        return _BENCHMARK_COST_MAX
    return value


def _audit_has_benchmark(model_audit_src: Path | None) -> bool:
    """True wenn das Audit-Quellverzeichnis echte Judge-Logs enthaelt.

    ``00_bias_report.md`` ist kein Modul-Benchmark und wird ignoriert.
    Genutzt von _should_skip_model (Skip-Entscheidung) und zur Ableitung
    von ``report_available`` OHNE die Logs ins Web-Repo zu kopieren.
    """
    return (
        model_audit_src is not None
        and model_audit_src.exists()
        and any(f.name != "00_bias_report.md" for f in model_audit_src.glob("*.md"))
    )


def _should_skip_model(
    *,
    model_name: str,
    raw_model_id: str,
    row: Any,
    model_audit_src: Path | None,
    count: int,
    total: int,
    bl_exact: set[str],
    bl_pattern: set[str],
) -> str | None:
    """Entscheidet ob ein Model in der Leaderboard-Iteration uebersprungen wird.

    Returns:
        None     — Model wird verarbeitet
        "no_benchmark" — weder Audit-Log noch CSV-Score vorhanden
        "blacklisted"   — raw_model_id matcht Web-Export-Blacklist
    """
    has_raw = bool(raw_model_id) and raw_model_id != "nan"

    # Skip 1: kein Benchmark (weder Audit-Log noch CSV-Score).
    # SSoT: normalize_pending() kennt alle Sentinel-Werte (inkl. En-Dash U+2013).
    _audit_has_bench = _audit_has_benchmark(model_audit_src)
    _csv_has_benchmark = normalize_pending(row.get(LdbCols.TOTAL_SCORE)) is not None
    if not _audit_has_bench and not _csv_has_benchmark:
        logging.debug("  [%s/%s] %s -> SKIP (nur PC-Daten, kein Benchmark)", count, total, model_name)
        return "no_benchmark"

    # Skip 2: Web-Export-Blacklist
    if has_raw and _is_blacklisted(raw_model_id, bl_exact, bl_pattern):
        logging.info("  [%s/%s] %s -> SKIP (blacklisted: %s)", count, total, model_name, raw_model_id)
        return "blacklisted"

    return None


def _resolve_model_dirs_and_card(
    *,
    model_name: str,
    raw_model_id: str,
    slug: str,
    card_lookup: Callable[[str], dict | None],
    audit_dirs: dict[str, Path],
    comp_dirs: dict[str, Path],
    count: int,
    total: int,
) -> tuple[dict | None, Path | None, Path | None]:
    """Loest Model-Card und Audit-/Comparison-Verzeichnisse auf.

    Reihenfolge:
    1. Card-Lookup mit raw_model_id, fallback model_name.
    2. Audit-Dir via dir_slug (slugify(raw_model_id) oder slug).
    3. Audit-Dir via _safe_name(raw_model_id) (Card-Konvention).
    4. Audit-Dir via heritage_ids aus Card (Mehrfach-Versuche bis Treffer).

    Returns: (card, model_audit_src, model_comp_src) — jedes None wenn nicht aufgeloest.
    """
    has_raw = bool(raw_model_id) and raw_model_id != "nan"
    dir_slug = slugify(raw_model_id) if has_raw else slug

    # Card-Resolution: raw_model_id zuerst, fallback model_name
    card = card_lookup(raw_model_id) if has_raw else None
    if card is None:
        card = card_lookup(model_name)

    # Warning fuer fehlende Card wird im Caller (_process_leaderboard) NACH
    # der Skip-Pruefung geloggt — sonst spammen geskippte Modelle das Log.
    # Audit/Comp-Dir via dir_slug
    model_audit_src = _resolve_dir(audit_dirs, dir_slug)
    model_comp_src = _resolve_dir(comp_dirs, dir_slug)

    # Fallback: _safe_name(raw_model_id) (Card-Konvention)
    if has_raw:
        safe_dir_slug = slugify(_safe_name(raw_model_id))
        if safe_dir_slug != dir_slug:
            if model_audit_src is None:
                model_audit_src = _resolve_dir(audit_dirs, safe_dir_slug)
            if model_comp_src is None:
                model_comp_src = _resolve_dir(comp_dirs, safe_dir_slug)

    # Fallback: heritage_ids aus Card
    if card:
        for h_id in card.get("heritage_ids", []):
            for h_slug in dict.fromkeys([slugify(h_id), slugify(_safe_name(h_id))]):
                if model_audit_src is None:
                    model_audit_src = _resolve_dir(audit_dirs, h_slug)
                if model_comp_src is None:
                    model_comp_src = _resolve_dir(comp_dirs, h_slug)
            if model_audit_src is not None and model_comp_src is not None:
                break

    return card, model_audit_src, model_comp_src


def _row_identity(row: Any) -> tuple[str, str, bool, str] | None:
    model_name = str(row.get(LdbCols.MODEL_NAME, ""))
    if not model_name or str(model_name) == "nan":
        return None
    raw_model_id = str(row.get(LdbCols.MODEL_ID, row.get("model_id_raw", row.get("model_id", "")))).strip()
    has_raw = bool(raw_model_id) and raw_model_id != "nan"
    slug = slugify(raw_model_id) if has_raw else slugify(model_name)
    return model_name, raw_model_id, has_raw, slug


def _dedupe_slug(slug: str, row: Any, seen_slugs: set[str], count: int, total: int, raw_model_id: str) -> str:
    if slug not in seen_slugs:
        seen_slugs.add(slug)
        return slug
    provider_code = str(row.get(LdbCols.PROVIDER_CODE, "")).strip().lower()
    base = f"{slug}-{provider_code}" if provider_code else f"{slug}-2"
    n = 2
    candidate = base
    while candidate in seen_slugs:
        n += 1
        candidate = f"{slug}-{provider_code}-{n}" if provider_code else f"{slug}-{n}"
    logging.warning(
        "  [WARN] [%s/%s] Slug-Collision: %r → %r (model_id=%s, provider=%s)",
        count, total, slug, candidate, raw_model_id, provider_code or "?",
    )
    seen_slugs.add(candidate)
    return candidate


def _resolve_thinking_mode(row: Any, card: dict | None, raw_model_id: str) -> str:
    arch_tags: list = (card.get("architecture_tags") or []) if card else []
    csv_thinking = str(row.get(LdbCols.THINKING_MODE, "")).strip().lower()
    if csv_thinking in ("thinking", "standard"):
        return csv_thinking
    if card and card.get("dual_profile"):
        card_mid = str(card.get("model_id", "")).strip()
        return "standard" if raw_model_id == card_mid else "thinking"
    if "Thinking-Optional" in arch_tags:
        return "partial"
    if "Thinking" in arch_tags:
        return "thinking"
    return "standard"


def _build_row_entry(
    *,
    row: Any,
    card: dict | None,
    slug: str,
    raw_model_id: str,
    model_name: str,
    model_audit_src: Path | None,
    model_comp_src: Path | None,
    model_out: Path,
    ctx: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str | None], bool, bool, str | None]:
    comp_files_dict = _export_model_files(model_out, model_comp_src)
    has_report = _audit_has_benchmark(model_audit_src)
    has_review = comp_files_dict["review"] is not None or comp_files_dict["bias_review"] is not None
    review_published_at, review_updated_at = _review_date_range(model_comp_src) if model_comp_src else (None, None)
    vendor = _normalize_vendor(card.get("vendor") if card else None, ctx["vendor_alias_map"])
    raw_community = card.get("community") if card else None
    community = _normalize_community(raw_community, ctx["community_alias_map"])
    community_card_ref = ctx["community_card_id_lookup"].get(community) if community else None
    card_tier = card.get("weights_license_tier") if card else None
    model_type = (WEIGHTS_TIER_DISPLAY.get(card_tier) if card_tier else None) or str(row.get(LdbCols.TYPE, ""))
    thinking_mode = _resolve_thinking_mode(row, card, raw_model_id)
    benchmark_run_at = ctx["benchmark_run_map"].get(model_name) or ctx["benchmark_run_map"].get(raw_model_id)
    entry = _build_leaderboard_entry(
        row=row,
        card=card,
        slug=slug,
        vendor=vendor,
        thinking_mode=thinking_mode,
        model_type=model_type,
        has_report=has_report,
        has_review=has_review,
        review_published_at=review_published_at,
        review_updated_at=review_updated_at,
        benchmark_run_at=benchmark_run_at,
        inference_provider=resolve_inference_provider(
            raw_model_id if raw_model_id and raw_model_id != "nan" else model_name,
            ctx["provider_map"],
        ),
        vendor_card_ref=ctx["vendor_card_id_lookup"].get(vendor) if vendor else None,
        community=community,
        community_card_ref=community_card_ref,
        benchmark_cost_max=ctx["benchmark_cost_max"],
    )
    return entry, comp_files_dict, has_report, has_review, model_type


def _build_row_compass_data(
    *,
    ctx: dict[str, Any],
    raw_model_id: str,
    model_name: str,
    slug: str,
    card: dict | None,
    model_type: str,
) -> dict[str, Any] | None:
    pc = ctx["pc"]
    if pc is None or "model" not in pc.columns or "run_id" not in pc.columns:
        return None
    pc_id = raw_model_id if raw_model_id and raw_model_id != "nan" else model_name
    pc_slug = slugify(pc_id)
    pc_row = _lookup_pc_row(pc_id, pc_slug, pc)
    if pc_row is None:
        return None
    # Lookup-Key normalisieren: strip_date_suffix, damit die Maps (die vom
    # CSV-Writer ebenfalls date-stripped werden) konsistent gematcht werden.
    # Beispiel: pc_id="z-ai/glm-5.1-20260406" → Key "z-ai/glm-5.1".
    pc_id_canonical = strip_date_suffix(pc_id)
    lb_row = ctx["pc_lb_map"].get(pc_id_canonical)
    if lb_row is None:
        lb_row = ctx["pc_lb_slug_map"].get(slugify(pc_id_canonical))
    card_id = (card.get("model_id") if card else None) or (raw_model_id if raw_model_id and raw_model_id != "nan" else None)
    # Dual-Profile-Thinking-Varianten (Slug endet auf "-thinking") teilen sich
    # die Card mit der Standard-Variante → card_id ist identisch. Wenn BEIDE
    # Modi einen eigenen Political-Compass-Datensatz haben, kollidieren die
    # card_ids in political_compass.json (last-write-wins im Web-Frontend:
    # Thinking überschreibt Standard). Fix: Thinking-Varianten erhalten eine
    # distinkte card_id mit "--thinking"-Suffix. Doppeltstrich trennt den
    # Modus eindeutig vom Modell-Namen (verhindert Kollision mit Modellen,
    # die "-thinking" im Namen tragen). Konvention: card_id + "--" + mode.
    # Analog zu _is_dual_thinking in _build_leaderboard_entry (entry_builders.py:328).
    if slug.endswith("-thinking") and card_id and not card_id.endswith("--thinking"):
        card_id = f"{card_id}--thinking"
    return _build_compass_entry(pc_row, lb_row, slug, model_name, model_type, ctx["block_meta"], card_id=card_id)


def _write_model_data(
    *,
    model_out: Path,
    entry: dict[str, Any],
    compass_data: dict[str, Any] | None,
    comp_files_dict: dict[str, str | None],
    tooluse_entry: dict[str, Any] | None,
) -> None:
    model_json: dict[str, Any] = {
        "leaderboard": entry,
        "political_compass": compass_data,
        "files": {"comparisons": comp_files_dict},
        "tooluse": tooluse_entry,
    }
    model_data = _strip_emojis(_strip_none(model_json))
    lb = model_data.get("leaderboard")
    if isinstance(lb, dict):
        scores = lb.get("scores")
        if isinstance(scores, dict):
            for key in _SCORES_CONTRACT_KEYS:
                scores.setdefault(key, None)
        else:
            lb["scores"] = dict.fromkeys(_SCORES_CONTRACT_KEYS, None)
    _atomic_write_json(model_out / "data.json", model_data)


def _process_leaderboard(
    ctx: dict[str, Any],
    filter_slug: str | None,
    models_dir: Path,
) -> dict[str, Any]:
    root_dir: Path = ctx["root_dir"]
    ldb = ctx["ldb"]
    models_list: list[dict[str, Any]] = []
    pc_list: list[dict[str, Any]] = []
    models_with_reports = 0
    models_with_reviews = 0
    models_skipped_blacklist = 0
    seen_slugs: set[str] = set()
    count = 0
    total = len(ldb)

    for _, row in ldb.iterrows():
        identity = _row_identity(row)
        if identity is None:
            continue
        count += 1
        model_name, raw_model_id, has_raw, slug = identity
        if filter_slug and slugify(filter_slug) != slug:
            continue
        card, model_audit_src, model_comp_src = _resolve_model_dirs_and_card(
            model_name=model_name,
            raw_model_id=raw_model_id,
            slug=slug,
            card_lookup=lambda mid: load_model_card(mid, root_dir, config=ctx.get("provider_config")),
            audit_dirs=ctx["audit_dirs"],
            comp_dirs=ctx["comp_dirs"],
            count=count,
            total=total,
        )
        skip_reason = _should_skip_model(
            model_name=model_name,
            raw_model_id=raw_model_id,
            row=row,
            model_audit_src=model_audit_src,
            count=count,
            total=total,
            bl_exact=ctx["bl_exact"],
            bl_pattern=ctx["bl_pattern"],
        )
        if skip_reason == "no_benchmark":
            continue
        if skip_reason == "blacklisted":
            models_skipped_blacklist += 1
            continue
        # Slug-Dedupe NACH der Skip-Pruefung: geblacklistete/geskippte Modelle
        # konsumieren keine Slugs — sonst erhalten behaltene Modelle bei
        # Kollision mit toten Slugs unnötig Provider-/Counter-Suffixe.
        slug = _dedupe_slug(slug, row, seen_slugs, count, total, raw_model_id)
        if card is None:
            logging.warning(
                "  [WARN] [%s/%s] %s (raw_model_id=%s): keine Model Card gefunden. "
                "Web-Export liefert model_card=null.",
                count, total, model_name, raw_model_id or "?",
            )
        logging.info("  [%s/%s] %s -> OK", count, total, model_name)
        model_out = models_dir / slug
        model_out.mkdir(exist_ok=True)
        entry, comp_files_dict, has_report, has_review, model_type = _build_row_entry(
            row=row,
            card=card,
            slug=slug,
            raw_model_id=raw_model_id,
            model_name=model_name,
            model_audit_src=model_audit_src,
            model_comp_src=model_comp_src,
            model_out=model_out,
            ctx=ctx,
        )
        models_list.append(entry)
        if has_report:
            models_with_reports += 1
        if has_review:
            models_with_reviews += 1
        compass_data = _build_row_compass_data(
            ctx=ctx,
            raw_model_id=raw_model_id,
            model_name=model_name,
            slug=slug,
            card=card,
            model_type=model_type,
        )
        if compass_data is not None:
            pc_list.append(compass_data)
        tooluse_entry = (
            _build_tooluse_entry(raw_model_id if has_raw else model_name, root_dir)
            if (card and card.get("supports_tool_use") is True)
            else None
        )
        _write_model_data(
            model_out=model_out,
            entry=entry,
            compass_data=compass_data,
            comp_files_dict=comp_files_dict,
            tooluse_entry=tooluse_entry,
        )

    return {
        "models_list": models_list,
        "pc_list": pc_list,
        "models_with_reports": models_with_reports,
        "models_with_reviews": models_with_reviews,
        "models_skipped_blacklist": models_skipped_blacklist,
    }


def main() -> None:
    """Orchestriert den Web-Export-Pipeline."""
    try:
        config = ConfigValidator().config
        default_out = config.get("output", {}).get("web_export_dir", "./web_export")
    except (OSError, ValueError, yaml.YAMLError):
        default_out = "./web_export"

    parser = argparse.ArgumentParser(description="Export CrucibleMark data for Web")
    parser.add_argument("--output", default=default_out, type=str, help="Target directory for web data")
    parser.add_argument("--model", type=str, help="Export only a specific model slug")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s"
    )

    out_dir, models_dir, root_dir = _setup_output_dirs(args)
    scores_dir = root_dir / "benchmark_scores"
    comparisons_path = root_dir / "docs" / "reviews"

    logging.info("🌐 Starting Web Export Pipeline...")

    ctx = _init_export_context(root_dir, scores_dir, comparisons_path)
    result = _process_leaderboard(ctx, args.model, models_dir)

    if args.model:
        # Partial-Export: Top-Level-Index-Files NICHT überschreiben — sie
        # würden sonst auf einen 1-Eintrag-Index schrumpfen und den
        # kompletten Web-Bestand unbrauchbar machen.
        logging.info(
            "Partial-Export abgeschlossen (%s Modell(e)) — Top-Level-Files "
            "nicht überschrieben. Für einen vollständigen Bestand: "
            "make web-export ohne --model.", len(result["models_list"]),
        )
        return

    _write_top_level_outputs(
        out_dir=out_dir,
        generated_at=ctx["generated_at"],
        models_list=result["models_list"],
        pc_list=result["pc_list"],
        root_dir=root_dir,
        comparisons_path=comparisons_path,
        models_with_reports=result["models_with_reports"],
        models_with_reviews=result["models_with_reviews"],
        models_skipped_blacklist=result["models_skipped_blacklist"],
        blacklist_total_entries=ctx["bl_total"],
        blacklist_source="config/web_export_blacklist.yaml",
    )
    logging.info("✅ Export completed to -> %s", out_dir)

