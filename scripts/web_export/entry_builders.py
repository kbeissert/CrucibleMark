# ruff: noqa: E402
from __future__ import annotations

import json
import logging
import math
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_ROOT_DIR = Path(__file__).resolve().parents[2]
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from utils.card_utils import get_tag_display_roles, get_tag_labels, normalize_tags
from utils.model_id_base import strip_date_suffix
from utils.model_utils import WEIGHTS_TIER_DISPLAY, _find_card, _safe_name
from utils.text_helpers import (
    extract_badge_tier,
    extract_version,
    normalize_pending,
    parse_compact_number,
    parse_int,
    parse_percent,
    parse_star_float,
    slugify,
    strip_none as _strip_none,
)
from .constants import LdbCols, _SCORE_COLUMN_TO_KEY


def _normalize_export_tags(tags: list[str]) -> list[str]:
    """Filtert deprecated Tags aus architecture_tags für den Web-Export."""
    if not tags:
        return tags
    return normalize_tags(tags)[0]

def parse_tests_run(val) -> dict | None:
    if pd.isna(val) or not isinstance(val, str):
        return None
    match = re.search(r'(\d+)\s*/\s*(\d+)', val)
    if match:
        return {"completed": int(match.group(1)), "total": int(match.group(2))}
    return None


def load_model_card(
    model_name: str,
    root_dir: Path,
    config: dict | None = None,
) -> dict | None:
    """Loads the model card JSON for *model_name*.

    SSoT: Delegates to resolve_canonical_model_id() (utils/model_utils.py) for
    the full Card-Lookup-Pipeline (Card-Filenames + _safe_name-Fallback + Slug
    Derivation), then applies web-export-specific fallbacks for display-name
    vs. model_id mismatches (e.g. "kimi-k2.5" → "moonshotai/kimi-k2.5-0127").

    Args:
        config: Optional Provider-Config (wie ``ConfigValidator().config``).
            Wenn gesetzt, wird ``resolve_model_cfg_for`` genutzt, um den
            ``card_model_id``-Redirect für Dual-Thinking-Profile aufzulösen,
            damit Thinking-Profile die geteilte Card finden.
    """
    from utils.model_utils import resolve_canonical_model_id

    card_dir = root_dir / "benchmark_scores" / "model_cards"

    def _try_load(path: Path) -> dict | None:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    # card_model_id-Redirect für Dual-Thinking-Profile auflösen.
    _model_cfg: dict | None = None
    if config is not None:
        from utils.model_utils import resolve_model_cfg_for  # noqa: PLC0415
        _model_cfg = resolve_model_cfg_for(model_name, config)

    # SSoT-Brücke: kanonische ID auflösen (Card-Lookup + Slug-Derivation)
    canonical = resolve_canonical_model_id(model_name, model_cfg=_model_cfg)
    path = _find_card(canonical, card_dir=card_dir, model_cfg=_model_cfg)
    if path.exists():
        return _try_load(path)

    # Web-export fallback: leaderboard uses display names (e.g. "kimi-k2.5") while cards
    # are filed under the full namespaced model_id (e.g. "moonshotai/kimi-k2.5-0127").
    # Full directory scan matching stripped model_id.
    safe = _safe_name(canonical)
    display_norm = canonical.lower()

    def _sep_norm(s: str) -> str:
        """Normalisiert Punkte und Underscores zu Bindestrichen für Fuzzy-Vergleich."""
        return re.sub(r'[._]', '-', s).lower()

    display_norm_sep = _sep_norm(display_norm)
    for card_file in sorted(card_dir.glob("*.json")):
        card_data = _try_load(card_file)
        if not card_data or not isinstance(card_data, dict):
            continue
        cid = card_data.get("model_id", "")
        base = cid.split("/", 1)[1] if "/" in cid else cid
        base = re.sub(r"-\d{4,8}$", "", base)
        # Exakter Match oder separator-normalisierter Match (Punkte/Underscores ↔ Bindestriche)
        if base.lower() == display_norm or _sep_norm(base) == display_norm_sep:
            logging.debug(
                "load_model_card: Fallback-Match '%s' für '%s' (base='%s', separator-normalisiert)",
                card_file.name, model_name, cid,
            )
            return card_data

    # Web-export fallback: hf.co / HuggingFace GGUF — card is "hf_co_<org>_<safe>.json"
    # while model_name is just "<safe>".
    for candidate in card_dir.glob(f"*_{safe}.json"):
        result = _try_load(candidate)
        if result:
            return result

    return None


def _build_block_scores(module_stats: dict, block_meta: dict) -> dict:
    """Baut das blocks-Dict aus den module_stats (vanilla/forced) für political_compass.json."""
    vanilla = module_stats.get("vanilla", {})
    forced = module_stats.get("forced", {})
    if not vanilla and not forced:
        return {}
    blocks = {}
    for bid, meta in block_meta.items():
        v = vanilla.get(bid, {})
        f = forced.get(bid, {})
        axis = meta["axis"]
        if axis == "both":
            blocks[bid] = {
                "label": meta["label"],
                "axis": "both",
                "vanilla_x": round(v.get("x", 0.0), 2),
                "vanilla_y": round(v.get("y", 0.0), 2),
                "forced_x": round(f.get("x", 0.0), 2),
                "forced_y": round(f.get("y", 0.0), 2),
            }
        else:
            blocks[bid] = {
                "label": meta["label"],
                "axis": axis,
                "vanilla": round(v.get(axis, 0.0), 2),
                "forced": round(f.get(axis, 0.0), 2),
            }
    return blocks


_THINKING_LABELS: dict[str, str] = {
    "thinking": "Thinking",
    "partial": "Adaptive Thinking",
    "standard": "Standard",
}

_USE_CASE_LABELS: dict[str, str] = {
    "generalist": "Generalist",
    "coding": "Coder",
    "reasoning": "Reasoning",
    "vision-language": "Vision-Language",
    "agentic": "Agentic",
}

_PARAM_ARCH_LABELS: dict[str, str] = {
    "dense": "Dense",
    "moe": "MoE",
    "hybrid": "Hybrid",
}


_MODALITY_LABELS: dict[str, str] = {
    "text": "Text",
    "image": "Vision",
    "audio": "Audio",
    "video": "Video",
}


def _build_characteristics(
    card: dict | None,
    thinking_mode: str,
    architecture_tags: list[str],
) -> dict[str, Any]:
    """Baut das rollen-gekennzeichnete characteristics-Objekt.

    Args:
        card: Model Card Dict (oder None wenn keine Card gefunden).
        thinking_mode: Bereits abgeleiteter thinking_mode-Wert
            ('standard' | 'thinking' | 'partial').
        architecture_tags: Bereits normalisierte Tag-Liste aus der Card.

    Returns:
        Dict mit 'categories' (Filter-Facetten) und 'features' (Badges).
        Leere features-Liste wenn keine Badges vorhanden.
    """
    display_roles = get_tag_display_roles()
    tag_labels = get_tag_labels()

    # ── categories: Filter-Facetten aus dedizierten Card-Feldern ──
    categories: dict[str, Any] = {}

    thinking_value = thinking_mode or "standard"
    categories["thinking"] = _strip_none({
        "value": thinking_value,
        "label": _THINKING_LABELS.get(thinking_value, thinking_value.title()),
    })

    if card:
        use_case = card.get("use_case_primary")
        if use_case:
            categories["use_case"] = _strip_none({
                "value": use_case,
                "label": _USE_CASE_LABELS.get(use_case, use_case.title()),
            })

        param_arch = card.get("parameter_architecture")
        if param_arch:
            categories["architecture"] = _strip_none({
                "value": param_arch,
                "label": _PARAM_ARCH_LABELS.get(param_arch, param_arch.title()),
            })

        license_tier = card.get("weights_license_tier")
        if license_tier:
            categories["license"] = _strip_none({
                "value": license_tier,
                "label": WEIGHTS_TIER_DISPLAY.get(license_tier, license_tier.title()),
            })

        modalities = card.get("input_modalities")
        if isinstance(modalities, list) and modalities:
            mod_items = [
                {"slug": m, "label": _MODALITY_LABELS[m]}
                for m in modalities
                if m in _MODALITY_LABELS
            ]
            if mod_items:
                categories["modalities"] = mod_items

    # ── features: Display-Badges aus architecture_tags (nur display_role=badge) ──
    # De-Duplizierung: Feature-Badges deren Label mit einem bereits gerenderten
    # Modality-Label kollidiert, werden unterdrückt. Verhindert doppelte Badges
    # (z.B. Vision-Capable + image→"Vision" → "Vision" erscheint nur als graue
    # Modality-Kategorie, nicht zusätzlich als transparentes Feature-Badge).
    modality_labels = {
        mod["label"] for mod in categories.get("modalities", [])
    }
    features: list[dict[str, str]] = []
    for tag in architecture_tags:
        role = display_roles.get(tag, "badge")
        if role != "badge":
            continue
        label = tag_labels.get(tag, tag)
        if label in modality_labels:
            continue
        features.append({
            "slug": tag,
            "label": label,
        })

    return {
        "categories": categories,
        "features": features,
    }


# Sentinel-Threshold für benchmark_cost: jeder Wert > 1e6 USD ist ein
# Datenfehler (Overflow in der Benchmark-Pipeline, siehe Session-60-Audit:
# 5 Modelle mit Werten bis 1e+156). Solche Werte werden im Web-Export zu
# None normalisiert, damit die UI keinen literalen "$6.003e+143" rendert.
_BENCHMARK_COST_MAX = 1_000_000.0  # 1 Mio. USD pro Benchmark — weit über jedem realistischen Wert


def _sanitize_cost(val: Any) -> float | None:
    """Defense-in-Depth: filtert Sentinel-/Overflow-Werte aus benchmark_cost.

    normalize_pending() konvertiert nur nan → None, lässt aber extreme endliche
    Werte (z.B. 6e+143 aus Token-Accumulator-Overflow) und ±inf durch. Diese
    würden im Web-Frontend als literaler Exponential-String gerendert.

    Schwellwert: 1 Mio. USD pro Benchmark — alles darüber ist ein Datenfehler.
    """
    if val is None:
        return None
    if isinstance(val, str):
        return None
    if not math.isfinite(float(val)):
        return None
    if float(val) > _BENCHMARK_COST_MAX:
        return None
    return float(val)


def _build_leaderboard_entry(
    row: pd.Series,
    card: dict | None,
    slug: str,
    vendor: str | None,
    thinking_mode: str,
    model_type: str,
    has_report: bool,
    has_review: bool,
    review_published_at: str | None,
    review_updated_at: str | None,
    benchmark_run_at: str | None,
    inference_provider: str | None,
    vendor_card_ref: str | None = None,
    community: str | None = None,
    community_card_ref: str | None = None,
) -> dict[str, Any]:
    """Builds the leaderboard entry dict for a single model."""
    _card_version = extract_version(card.get("model_version")) if card else None
    _csv_version = extract_version(row.get(LdbCols.VERSION))
    _raw_model_id = str(row.get(LdbCols.MODEL_ID, row.get("model_id_raw", row.get("model_id", "")))).strip()
    _normalized_tags = _normalize_export_tags(card.get("architecture_tags") or []) if card else []
    _characteristics = _build_characteristics(card, thinking_mode, _normalized_tags)
    # Variant-aware display name: Dual-Profile-Thinking-Varianten (Slug endet
    # auf "-thinking") bekommen " (Thinking)"-Suffix, um sie im Scoreboard von
    # der Standard-Variante zu unterscheiden. Thinking-only Modelle (Claude
    # Opus 4.8, o4-mini, etc.) haben keinen Standard-Gegenpart und brauchen
    # keinen Suffix — ihr Slug endet nicht auf "-thinking".
    _base_name = (card.get("display_name") if card else None) or str(row.get(LdbCols.MODEL_NAME, ""))
    _is_dual_thinking = thinking_mode == "thinking" and slug.endswith("-thinking")
    _display_name = f"{_base_name} (Thinking)" if _is_dual_thinking else _base_name
    # synthesis_quality (ToolUse P1) und tool_execution (ToolUse P2) werden
    # datenbasiert exportiert: sobald das Modell einen Wert im Leaderboard
    # hat, wird der Score gezeigt — unabhaengig vom supports_tool_use-Flag.
    # supports_tool_use bleibt separates Capability-Indikator (s. supports_tool_use-
    # Feld unten und supports_tool_use_state im Web-Frontend).
    # Verhindert inkonsistente "8 Scores ohne synthesis_quality"-Befunde fuer
    # Modelle, die getestet wurden (Daten in tooluse_leaderboard.csv) aber
    # supports_tool_use=false tragen. Der detail-ToolUse-Block (data.json.
    # tooluse) bleibt weiterhin an supports_tool_use=true gebunden, weil er
    # Frontend-Navigationsauswirkungen hat (Session-44-Design).
    _entry = _strip_none({
        "slug": slug,
        "model_id": (card.get("model_id") if card else None) or (_raw_model_id or None),
        "model_name": (card.get("display_name") if card else None) or str(row.get(LdbCols.MODEL_NAME, "")),
        "display_name": _display_name,
        "vendor": vendor,
        # SSoT-Link zum Vendor-Profil (v4.9.1): vendor_card_id aus classification_taxonomy.json
        "vendor_card_ref": vendor_card_ref,
        # Community-Distributor/Fine-Tuner (v4.9.2): kanonischer Name + Card-Referenz
        "community": community,
        "community_card_ref": community_card_ref,
        "version": _card_version or _csv_version,
        "badge": str(row.get(LdbCols.BADGE, "")),
        "badge_tier": extract_badge_tier(row.get(LdbCols.BADGE)),
        "size_class": (card.get("size_class") if card else None) or str(row.get(LdbCols.SIZE_CLASS, "Frontier")),
        "speed_profile": str(row.get(LdbCols.SPEED_PROFILE, "")),
        "performance_tier": str(row.get(LdbCols.PERFORMANCE_TIER, "")) or None,
        "type": model_type,
        "thinking_mode": thinking_mode,
        "characteristics": _characteristics,
        "deployment_type": card.get("deployment_type") if card else None,
        "weights_license_tier": card.get("weights_license_tier") if card else None,
        "inference_provider": inference_provider,
        "provider_code": str(row.get(LdbCols.PROVIDER_CODE, "")) or None,
        "hardware_profile": str(row.get(LdbCols.HARDWARE_PROFILE, "")) or None,
        "total_score": normalize_pending(row.get(LdbCols.TOTAL_SCORE)),
        "routine_score": normalize_pending(row.get(LdbCols.ROUTINE_SCORE)),
        "reasoning_score": normalize_pending(row.get(LdbCols.REASONING_SCORE)),
        "tokens_per_s": normalize_pending(row.get(LdbCols.TOKENS_PER_S)),
        "avg_task_duration_s": normalize_pending(row.get(LdbCols.AVG_TASK_DURATION)),
        "p95_time_s": normalize_pending(row.get(LdbCols.P95_TIME, row.get(LdbCols.P95_LEGACY, None))),
        "max_time_s": normalize_pending(row.get(LdbCols.MAX_TIME)),
        "timeout_count": parse_int(row.get(LdbCols.TIMEOUT_COUNT)),
        "tokens_total": parse_compact_number(row.get(LdbCols.TOKENS_TOTAL)),
        "cost_per_1k": normalize_pending(row.get(LdbCols.COST_PER_1K)),
        "benchmark_cost": _sanitize_cost(normalize_pending(row.get(LdbCols.BENCHMARK_COST))),
        "llm_judge_avg": normalize_pending(row.get(LdbCols.LLM_JUDGE_RAW)) or parse_star_float(row.get(LdbCols.LLM_JUDGE_DISPLAY)),
        "llm_judge_coverage": parse_percent(row.get(LdbCols.LLM_JUDGE_COVERAGE)),
        "tests_run": parse_tests_run(row.get(LdbCols.TESTS_RUN)),
        "coverage_ratio": normalize_pending(row.get(LdbCols.COVERAGE_RATIO)),
        "scores": {
            key: normalize_pending(row.get(_col))
            for _col, key in _SCORE_COLUMN_TO_KEY.items()
        },
        "tokens_per_module": {
            "code_quality": parse_compact_number(row.get("Tokens: Code Quality Audit")),
            "cli_benchmark": parse_compact_number(row.get("Tokens: CLI Badge")),
            "ux_writing": parse_compact_number(row.get("Tokens: UX Writing & Microcopy")),
            "documentation_quality": parse_compact_number(row.get("Tokens: Documentation Quality")),
            "content_transformation": parse_compact_number(row.get("Tokens: Content Transformation & Adaption")),
            "cultural_intelligence": parse_compact_number(row.get("Tokens: Cultural Intelligence")),
            "logical_reasoning": parse_compact_number(row.get("Tokens: Logical Reasoning")),
            "system": parse_compact_number(row.get("Tokens: System")),
        },
        "report_available": has_report,
        "review_available": has_review,
        "benchmark_run_at": benchmark_run_at,
        "report_published_at": review_published_at,
        "report_updated_at": review_updated_at if review_updated_at != review_published_at else None,
        "last_activity_at": max(filter(None, [
            benchmark_run_at,
            review_published_at,
            review_updated_at if review_updated_at != review_published_at else None,
        ]), default=None),
        "model_card": _strip_none({
            # Identitaet (self-contained sub-dict, spiegelt Card-Sicht)
            "model_id": card.get("model_id"),
            "model_version": card.get("model_version"),
            # v4.10.14: Quant/Variant-Separierung — model_version ist reine
            # Versionsnummer; Quant/Format-Token und interne Variant-Namen
            # wurden aus model_version ausgelagert (Migration siehe
            # scripts/maintenance/migrate_model_versions_pollution.py).
            "quantization_format": card.get("quantization_format"),
            "model_variant": card.get("model_variant"),
            "unknown": card.get("unknown"),
            "display_name": card.get("display_name"),
            "developer": card.get("developer"),
            "origin_country": card.get("origin_country"),
            "developer_jurisdiction": card.get("developer_jurisdiction"),
            "deployment_type": card.get("deployment_type"),
            "local_deployment_possible": card.get("local_deployment_possible"),
            "weights_provenance_risk": card.get("weights_provenance_risk"),
            "weights_provenance_risk_rationale": card.get("weights_provenance_risk_rationale"),
            # Normalisierter Hersteller-Name (SSoT: kanonischer Name aus classification_taxonomy.json,
            # identisch mit Top-Level vendor-Feld — kein Raw-Wert aus der Card).
            "vendor": vendor,
            "architecture_tags": _normalized_tags,
            "primary_focus": card.get("primary_focus"),
            "thinking_probe_detected": card.get("thinking_probe_detected"),
            "thinking_probe_confidence": card.get("thinking_probe_confidence"),
            "thinking_probe_evidence": card.get("thinking_probe_evidence"),
            "thinking_probe_manual_override": card.get("thinking_probe_manual_override"),
            "thinking_probe_at": card.get("thinking_probe_at"),
            "model_family": card.get("model_family"),
            "use_case_primary": card.get("use_case_primary"),
            "parameter_architecture": card.get("parameter_architecture"),
            "params_total_b": card.get("params_total_b"),
            "params_active_b": card.get("params_active_b"),
            "context_window_k": card.get("context_window_k"),
            "knowledge_cutoff": card.get("knowledge_cutoff"),
            "size_class": card.get("size_class"),
            # Modalitaeten (required since v4.7.0, consumers: [web_export, ...])
            "input_modalities": card.get("input_modalities"),
            "output_modalities": card.get("output_modalities"),
            "summary": card.get("summary"),
            "judge_context_hint": card.get("judge_context_hint"),
            "strengths": card.get("strengths"),
            "known_limitations": card.get("known_limitations"),
            "card_status": card.get("card_status"),
            "generated_at": card.get("generated_at"),
            "license": card.get("license"),
            "license_url": card.get("license_url"),
            "commercial_use_allowed": card.get("commercial_use_allowed"),
            "weights_license_tier": card.get("weights_license_tier"),
            "input_price_per_1m": card.get("input_price_per_1m"),
            "output_price_per_1m": card.get("output_price_per_1m"),
            "supports_tool_use": card.get("supports_tool_use"),
            # Heritage-IDs (v4.8.0): frühere kanonische model_ids — leer wenn nicht gesetzt.
            "heritage_ids": card.get("heritage_ids") or [],
            # Community-Distributor (v4.9.2): kanonischer Name aus classification_taxonomy.json
            "community": community,
            # Profil-Verifikation (v4.9.0): wurde die Card manuell geprüft?
            "profile_verified": card.get("profile_verified"),
            "profile_verified_at": card.get("profile_verified_at"),
            "profile_verified_by": card.get("profile_verified_by"),
            "last_modified_at": card.get("last_modified_at"),
            # Optional v4.7.1 Thinking-Probe-Quartett: nur exportieren wenn gesetzt
            # (Sonde schreibt die Felder nur bei detektiertem CoT; sonst noise vermeiden).
            **(
                {"cot_marker_family": card["cot_marker_family"]}
                if card.get("cot_marker_family") is not None
                else {}
            ),
            **(
                {"cot_tags_detected": card["cot_tags_detected"]}
                if card.get("cot_tags_detected") is not None
                else {}
            ),
            # Tri-State-Semantik für 11ty-Frontend:
            #   "true"      — Tool-Use funktioniert (empirisch verifiziert)
            #   "false"     — Modell kann keine Tools (empirisch verifiziert)
            #   "untested"  — noch kein Tool-Use-Benchmark gelaufen
            "supports_tool_use_state": (
                _supports_tool_use_state(card.get("supports_tool_use"))
                if card is not None
                else None
            ),
        }) if card else None,
    })
    return _entry


def _lookup_pc_row(
    model_name: str,
    slug: str,
    pc: pd.DataFrame,
) -> pd.Series | None:
    """Returns the AVG row for a model from political_compass_results.csv.

    SSoT: Matcht via URL-Slug (slugify) — bewusst KEIN _safe_name, weil PC-CSVs
    den vollen Vendor-Prefix (z.B. ``anthropic/claude-sonnet-4-5-20250929``) tragen
    und der Frontend-Slug dieselbe Konvention nutzt (Bindestriche).

    Strategy:
    1. Exact match (display-name Gleichheit)
    2. Exact slug match
    3. Date-suffix-aware slug match: ``strip_date_suffix`` auf beiden Seiten.
       Matcht dated IDs (``claude-sonnet-4-5`` ↔ ``claude-sonnet-4-5-20250929``)
       OHNE False-Positives bei Varianten-Suffixen (``Gemma-4-31B`` ↔
       ``gemma-4-31B-it-qat-ud-q4`` oder ``qwen3_6-27B`` ↔
       ``qwen3_6-27B-thinking``).
    4. Returns None → caller decides what to do (PC-only models werden uebersprungen).
    """
    avg_rows = pc[pc["run_id"] == "AVG"]
    exact = avg_rows[avg_rows["model"] == model_name]
    if not exact.empty:
        return exact.iloc[0]
    canonical_slug = strip_date_suffix(slug)
    for _pc_model in avg_rows["model"].unique():
        _pc_slug = slugify(str(_pc_model))
        if _pc_slug == slug:
            rows = avg_rows[avg_rows["model"] == _pc_model]
            if not rows.empty:
                return rows.iloc[0]
        # Date-suffix-aware match: strippt -YYYYMMDD / -MMDD auf beiden Seiten.
        # Verhindert False-Positives wie Gemma-4-31B → gemma-4-31B-it-qat-ud-q4
        # (früher via startswith gematcht) oder qwen3_6-27B → qwen3_6-27B-thinking.
        if strip_date_suffix(_pc_slug) == canonical_slug:
            rows = avg_rows[avg_rows["model"] == _pc_model]
            if not rows.empty:
                return rows.iloc[0]
    return None


def compute_is_retest(lb_row):
    """SSoT: Bestimmt ob ein Modell ein Retest ist.

    Returns None wenn lb_row None ist, True/False sonst.
    """
    if lb_row is None:
        return None
    val = lb_row.get("is_retest")
    if pd.isna(val):
        return None
    return bool(val)


def _build_compass_entry(
    pc_row: pd.Series,
    lb_row: pd.Series | None,
    slug: str,
    model_name: str,
    model_type: str,
    block_meta: dict,
    card_id: str | None = None,
) -> dict[str, Any]:
    """Builds the political_compass entry dict for a single model.

    card_id: kanonische model_id aus der Model-Card (SSoT für Frontend-Matching).
    Für Dual-Profile-Thinking-Varianten wird "--thinking" angehängt (siehe
    _build_row_compass_data in main.py), um card_id-Kollisionen in
    political_compass.json zu verhindern, wenn beide Modi eigene Compass-Daten
    haben. Das Web-Frontend matcht zunehmend per slug (einzigartig), card_id
    bleibt als Label erhalten.
    """
    archetype: str | None = None
    extremism: str | None = None
    metrics: dict = {}
    metrics_json_str = str(pc_row.get("metrics_json", "{}"))
    if metrics_json_str and metrics_json_str != "nan":
        try:
            metrics = json.loads(metrics_json_str)
            archetype = metrics.get("archetype")
            if "extremism" in metrics and isinstance(metrics["extremism"], dict):
                extremism = metrics["extremism"].get("status")
            else:
                extremism = metrics.get("extremism.status")
        except json.JSONDecodeError as exc:
            logging.debug("PC-Metriken JSON kaputt: %s", exc)

    def _lb_num(key: str) -> float | None:
        if lb_row is None:
            return None
        val = normalize_pending(lb_row.get(key))
        if val is None or isinstance(val, str):
            return None
        return val

    def _lb_str(key: str) -> str | None:
        return str(lb_row.get(key, "")) if lb_row is not None else None

    return _strip_none({
        "card_id": card_id,
        "slug": slug,
        "name": model_name,
        "version": extract_version(pc_row.get("model_version")),
        "type": model_type,
        "x": normalize_pending(pc_row.get("x_coordinate")),
        "y": normalize_pending(pc_row.get("y_coordinate")),
        "label": str(pc_row.get("x_label", "")) + " - " + str(pc_row.get("y_label", "")),
        "vanilla_x": _lb_num("vanilla_x"),
        "vanilla_y": _lb_num("vanilla_y"),
        "vanilla_label": _lb_str("vanilla_label"),
        "forced_x": _lb_num("forced_x"),
        "forced_y": _lb_num("forced_y"),
        "forced_label": _lb_str("forced_label"),
        "shift_distance": _lb_num("shift_distance"),
        "shift_x": _lb_num("shift_x"),
        "shift_y": _lb_num("shift_y"),
        "polarity_flip_rate": _lb_num("polarity_flip_rate"),
        "behavior_archetype": _lb_str("behavior_archetype"),
        "model_category": model_type,
        "is_retest": compute_is_retest(lb_row),
        "archetype": archetype,
        "extremism_status": extremism,
        "blocks": _build_block_scores(metrics.get("module_stats", {}), block_meta),
    })


def _supports_tool_use_state(value: object) -> str | None:
    """Normalisiert supports_tool_use für den Web-Export.

    State-Machine für Frontend:
        "true"  → Modell kann Tools (verifiziert)
        "false" → Modell kann KEINE Tools (false oder not_applicable)
        None    → Nicht getestet (untested, None, unbekannt)

    Returns:
        "true", "false" oder None
    """
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        val_lower = value.strip().lower()
        if val_lower in ("true", "tested"):
            return "true"
        if val_lower in ("false", "not_applicable"):
            return "false"
        # "untested" und alle anderen → None
    return None


def _read_latest_tooluse_narrative(review_dir: Path) -> str | None:
    """Return content of the most recently modified tooluse_narrative_review_*.md."""
    if not review_dir.exists():
        return None
    candidates = list(review_dir.glob("tooluse_narrative_review_*.md"))
    if not candidates:
        return None
    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    return latest.read_text(encoding="utf-8")


def _build_tooluse_entry(model_id: str, root_dir: Path) -> dict[str, Any] | None:
    """Return tooluse data dict for data.json, or None if model has no tooluse data.

    SSoT: Nutzt resolve_canonical_model_id() + _safe_name() fuer die Review-Dir-Aufloesung.
    Direkter Lookup ueber raw model_id ist fragil, weil ToolUse-Web-Data und
    Review-Verzeichnisse unterschiedliche ID-Konventionen nutzen koennen.
    """
    try:
        from utils.export.tooluse_context import get_tooluse_web_data
        from utils.model_utils import _safe_name, resolve_canonical_model_id
    except ImportError:
        logging.debug("tooluse_context not importable — skipping tooluse entry")
        return None

    # Kanonische ID fuer Card-/Provider-Mapping (ToolUse-Web-Data-Key)
    canonical = resolve_canonical_model_id(model_id)
    data = get_tooluse_web_data(canonical)
    if data is None:
        return None

    # Review-Dir-Pfad via _safe_name (Card-/Review-Ordner-Konvention)
    slug = _safe_name(canonical)
    review_dir = root_dir / "docs" / "reviews" / slug
    data["narrative_review"] = _read_latest_tooluse_narrative(review_dir)
    return data

