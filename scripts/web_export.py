#!/usr/bin/env python3
"""
CrucibleMark Web Export Pipeline
Transforms benchmark data into structured JSON/Markdown for the 11ty web project.
"""

import sys
import json
import shutil
import logging
import argparse
import datetime
import math
import re
from pathlib import Path
import pandas as pd
import yaml
from utils.config_validator import ConfigValidator


def build_provider_map(config_path: Path) -> dict[str, str]:
    """Builds a model_id → provider display name map from benchmark_config.yaml.

    Falls back to resolve_provider() for models not listed in the config
    (e.g. auto-discovered Ollama models). The returned name is the human-readable
    provider label (e.g. "Groq Cloud", "Ollama (Local)"), not the api_type key.
    """
    _FALLBACK_NAMES: dict[str, str] = {
        "ollama": "Ollama",
        "groq": "Groq Cloud",
        "mistral": "Mistral AI",
        "anthropic": "Anthropic",
        "openai": "OpenAI",
        "google": "Google Gemini",
        "xai": "xAI (Grok)",
    }
    mapping: dict[str, str] = {}

    try:
        with config_path.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    except (OSError, yaml.YAMLError):
        return mapping

    providers_block = cfg.get("providers", {})
    for _tier_key, tier_val in providers_block.items():
        if not isinstance(tier_val, dict):
            continue
        for _prov_key, prov_val in tier_val.items():
            if not isinstance(prov_val, dict):
                continue
            display_name: str = prov_val.get("name", _prov_key)
            for model_entry in prov_val.get("models", []):
                if isinstance(model_entry, dict) and "id" in model_entry:
                    model_id: str = model_entry["id"]
                    # Strip org prefix for Groq-style "org/model-id" keys
                    short_id = model_id.rsplit("/", maxsplit=1)[-1]
                    mapping[model_id] = display_name
                    if short_id != model_id:
                        mapping[short_id] = display_name

    # Store fallback names so callers can use them without importing model_utils
    mapping["__fallbacks__"] = _FALLBACK_NAMES  # type: ignore[assignment]
    return mapping


def resolve_inference_provider(model_name: str, provider_map: dict[str, str]) -> str | None:
    """Returns the display name of the inference provider for a given model.

    Lookup order:
    1. Exact match in config map
    2. Strip org prefix and retry
    3. resolve_provider() heuristic → map to display name via fallback table
    """
    if model_name in provider_map:
        return provider_map[model_name]
    short = model_name.rsplit("/", maxsplit=1)[-1]
    if short in provider_map:
        return provider_map[short]

    # Heuristic fallback
    try:
        from utils.model_utils import resolve_provider as _rp
        api_type, _ = _rp(model_name)
    except Exception:
        api_type = "ollama"

    fallbacks: dict[str, str] = provider_map.get("__fallbacks__", {})  # type: ignore[arg-type]
    return fallbacks.get(api_type)


def slugify(model_name: str) -> str:
    """Normalizes model names to URL-safe slugs."""
    name = str(model_name).rsplit('/', maxsplit=1)[-1].lower()
    return re.sub(r'[^a-z0-9]+', '-', name).strip('-')

def sanitize_audit_log(content: str) -> str:
    """Removes Section 3 (LLM-Judge evaluation) from audit logs before web export.
    Preserves header, prompt, model response, and Modul-Metriken block.
    Handles two cases: section 3 followed by Modul-Metriken, or section 3 at EOF."""
    # Case 1: Modul-Metriken block follows section 3
    result = re.sub(
        r'## 3\. Evaluation / LLM-Judge / Scorer.*?(?=\n---\n\n### 📦 Modul-Metriken)',
        '', content, flags=re.DOTALL
    )
    # Case 2: section 3 runs to EOF (no Modul-Metriken block)
    result = re.sub(
        r'\n*## 3\. Evaluation / LLM-Judge / Scorer.*$',
        '', result, flags=re.DOTALL
    )
    return result

def parse_tests_run(val) -> dict | None:
    if pd.isna(val) or not isinstance(val, str): return None
    match = re.search(r'(\d+)\s*/\s*(\d+)', val)
    if match: return {"completed": int(match.group(1)), "total": int(match.group(2))}
    return None

def normalize_pending(val):
    if pd.isna(val): return None
    val_str = str(val).strip()
    if val_str in ("Pending", "—", ""): return None
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return val_str

def parse_star_float(val) -> float | None:
    """Parst '4.0 ★' oder '3.8 ★' zu einem float. Gibt None bei fehlenden Werten zurück."""
    if pd.isna(val): return None
    val_str = str(val).strip().replace('★', '').strip()
    if val_str in ("Pending", "—", ""): return None
    try:
        f = float(val_str)
        return None if math.isnan(f) else f
    except (ValueError, TypeError):
        return None

def extract_badge_tier(val) -> str | None:
    if pd.isna(val) or not str(val).strip(): return None
    val_str = str(val).strip()
    return val_str.rsplit(' ', maxsplit=1)[-1] if ' ' in val_str else val_str

def extract_version(val) -> str | None:
    if pd.isna(val): return None
    v = str(val).strip()
    return None if not v or v == "unknown" else v

def clean_float(val):
    v = normalize_pending(val)
    return float(v) if v is not None else None


def load_model_card(model_name: str, root_dir: Path) -> dict | None:
    """Loads the model card JSON for *model_name* using the same lookup logic as _find_card().

    Replicates the 3-rule card-naming convention from utils/model_utils.py without
    importing from there (avoids CWD dependency of the module-level CARD_DIR path).
    """
    card_dir = root_dir / "benchmark_scores" / "model_cards"
    safe = re.sub(r"[:/.\ ]", "_", model_name)
    unprefixed = card_dir / f"{safe}.json"

    def _try_load(path: Path) -> dict | None:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    if "/" in model_name:
        # Rule 1: namespaced IDs (org/model) — globally unique, no prefix
        if unprefixed.exists():
            return _try_load(unprefixed)
        return None

    # Rule 3: non-namespaced — try provider-prefixed variants first (LCL_, GR_)
    for shortcode in ("LCL", "GR"):
        candidate = card_dir / f"{shortcode}_{safe}.json"
        if candidate.exists():
            return _try_load(candidate)

    # Rule 2: commercial API or legacy unprefixed card
    if unprefixed.exists():
        return _try_load(unprefixed)

    # Fallback: versioned card names (e.g. "claude-sonnet-4-5-20250929.json" for "claude-sonnet-4-5")
    versioned = sorted(card_dir.glob(f"{safe}-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if versioned:
        return _try_load(versioned[0])

    # Fallback: leaderboard stores short display names (e.g. "kimi-k2.5") while cards are
    # filed under the full namespaced model_id (e.g. "moonshotai/kimi-k2.5-0127").
    # Match by stripping the org-prefix and date/version suffix from each card's model_id.
    display_norm = model_name.lower()
    for card_file in sorted(card_dir.glob("*.json")):
        card_data = _try_load(card_file)
        if not card_data or not isinstance(card_data, dict):
            continue
        cid = card_data.get("model_id", "")
        # Strip org prefix (everything before first '/')
        base = cid.split("/", 1)[1] if "/" in cid else cid
        # Strip trailing date (-YYYYMMDD) or version (-NNNN) suffix
        base = re.sub(r"-\d{4,8}$", "", base)
        if base.lower() == display_norm:
            return card_data

    return None


def _read_version(root_dir: Path) -> str:
    """Reads project version from README.md badge line."""
    try:
        readme = root_dir / "README.md"
        for line in readme.read_text(encoding="utf-8").splitlines()[:10]:
            m = re.search(r"version-(\d+\.\d+\.\d+)-", line)
            if m:
                return m.group(1)
    except OSError:
        pass
    return "unknown"


_BLOCK_META: dict = {
    "7.1": {"label": "Ökonomie & Verteilung",   "axis": "x"},
    "7.2": {"label": "Arbeitswelt & Markt",      "axis": "x"},
    "7.3": {"label": "Fiskalpolitik",            "axis": "x"},
    "7.4": {"label": "Gesellschaft & Identität", "axis": "y"},
    "7.5": {"label": "Religion & Kultur",        "axis": "y"},
    "7.6": {"label": "Justiz & Ordnung",         "axis": "y"},
    "7.7": {"label": "Außenpolitik",             "axis": "y"},
    "7.8": {"label": "Technologie & Zukunft",    "axis": "y"},
    "7.9": {"label": "Parolen-Kompass",          "axis": "both"},
}


def _build_block_scores(module_stats: dict) -> dict:
    """Baut das blocks-Dict aus den module_stats (vanilla/forced) für political_compass.json."""
    vanilla = module_stats.get("vanilla", {})
    forced = module_stats.get("forced", {})
    if not vanilla and not forced:
        return {}
    blocks = {}
    for bid, meta in _BLOCK_META.items():
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


def extract_audit_category(filename: str) -> str:
    """Extracts category prefix from audit log filename."""
    name = filename.replace('.md', '')

    # Explicit mapping for known exceptions
    mapping = {
        "00_bias_report": "bias",
        "00_bias": "bias",
    }
    if name in mapping:
        return mapping[name]

    # Strip leading numbers/underscores (e.g., '00_bias_report' generic fallback)
    name = re.sub(r'^\d+_', '', name)

    # Find anything before first number or first underscore followed by number
    match = re.match(r'^([a-zA-Z_]+?)(?:_?\d+.*|$)', name)
    if match:
        cat = match.group(1).rstrip('_').lower()
        if cat:
            return cat

    return "other"

def find_latest_markdown(dir_path: Path, prefix: str = "") -> Path | None:
    if not dir_path.exists() or not dir_path.is_dir(): return None
    md_files = list(dir_path.glob(f'{prefix}*.md'))
    return max(md_files, key=lambda p: p.stat().st_mtime) if md_files else None

def load_csv_with_fallback(path: Path):
    try:
        return pd.read_csv(path)
    except Exception as e:
        logging.warning(f"  [WARN] Could not load {path.name}: {e}")
        return None

def main() -> None:
    # Load config SSOT
    try:
        config = ConfigValidator().config
        default_out = config.get("output", {}).get("web_export_dir", "./web_export")
    except Exception:
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

    # -------------------------------------------------------------------------
    # Safety guard: web_export darf nur innerhalb raw/ operieren
    # -------------------------------------------------------------------------
    out_dir = Path(args.output).resolve()
    ALLOWED_SUBDIR = "raw"

    if out_dir.name != ALLOWED_SUBDIR:
        # Wenn der konfigurierte Pfad nicht auf raw/ endet,
        # hänge raw/ automatisch an, um externe Daten zu schützen
        out_dir = out_dir / ALLOWED_SUBDIR

    # Explizite Whitelist: nur diese drei Top-Level-Files dürfen überschrieben werden
    ALLOWED_FILES = {"leaderboard.json", "political_compass.json", "meta.json", "provider_stats.json", "provider_landscape_review.md"}

    # models/ ist der einzige Unterordner der gelöscht werden darf
    ALLOWED_RMTREE = out_dir / "models"
    assert ALLOWED_RMTREE == (out_dir / "models"), "Safety check failed: rmtree target is not models/"

    out_dir.mkdir(parents=True, exist_ok=True)

    # Modelle-Ordner separat neu generieren
    if ALLOWED_RMTREE.exists():
        shutil.rmtree(ALLOWED_RMTREE)
    ALLOWED_RMTREE.mkdir(exist_ok=True)
    models_dir = ALLOWED_RMTREE

    root_dir = Path(__file__).resolve().parent.parent
    scores_dir = root_dir / "benchmark_scores"

    logging.info("🌐 Starting Web Export Pipeline...")

    # Build provider map from config (model_id → display name)
    _config_path = root_dir / "benchmark_config.yaml"
    provider_map = build_provider_map(_config_path)

    # Load Source CSVs
    ldb = load_csv_with_fallback(scores_dir / "benchmark_leaderboard_detailed.csv")
    pc = load_csv_with_fallback(scores_dir / "political_compass_results.csv")
    pc_lb = load_csv_with_fallback(scores_dir / "political_compass_leaderboard.csv")
    bias_df = load_csv_with_fallback(scores_dir / "bias_sensitivity.csv")
    provider_df = load_csv_with_fallback(scores_dir / "provider_leaderboard.csv")

    if ldb is None:
        logging.error("❌ Failed to load required benchmark_leaderboard_detailed.csv. Exiting.")
        sys.exit(1)

    # Build PC-Leaderboard lookup: model name -> row (vanilla/forced/shift fields)
    # Key by both exact name AND slugified name for fuzzy fallback
    pc_lb_map: dict = {}
    pc_lb_slug_map: dict = {}
    if pc_lb is not None and 'model' in pc_lb.columns:
        for _, _lb_row in pc_lb.iterrows():
            _m = str(_lb_row.get('model', ''))
            if _m and _m != 'nan':
                pc_lb_map[_m] = _lb_row
                pc_lb_slug_map[slugify(_m)] = _lb_row

    generated_at = datetime.datetime.now(datetime.UTC).isoformat()
    models_list = []
    pc_list = []

    models_with_reports = 0
    models_with_reviews = 0

    audit_logs_path = root_dir / "outputs" / "audit_logs"
    comparisons_path = root_dir / "docs" / "reviews"

    # Directory mapping: internal model ID (dir name slug) -> Path
    # The directory name is the SSOT; CSV display names may differ via provider prefix or version suffix.
    audit_dirs = {slugify(d.name): d for d in audit_logs_path.iterdir() if d.is_dir()} if audit_logs_path.exists() else {}
    comp_dirs = {slugify(d.name): d for d in comparisons_path.iterdir() if d.is_dir()} if comparisons_path.exists() else {}

    def _resolve_dir(dirs: dict, raw_slug: str) -> "Path | None":
        """Resolve raw model-ID slug to a local directory path.

        Primary: direct match via model_id slug (SSOT — same transform as benchmark_utils.py).
        Fallback 1: strip trailing date-suffix (reviews may pre-date the versioned model_id).
        Fallback 2: suffix-match after date-strip (for provider-prefix dirs without date suffix).
        """
        if raw_slug in dirs:
            return dirs[raw_slug]
        # Fallback 1: review dirs created before date-suffix was added to model_id
        stripped = re.sub(r'-\d{4,8}$', '', raw_slug)
        if stripped != raw_slug and stripped in dirs:
            return dirs[stripped]
        # Fallback 2: provider-prefix dir (e.g. z-ai_glm-5-turbo) matched via suffix
        if stripped != raw_slug:
            suffix_matches = [v for k, v in dirs.items() if k.endswith(stripped.split('-', 1)[-1] if '-' in stripped else stripped)]
            if len(suffix_matches) == 1:
                return suffix_matches[0]
        return None

    count = 0
    total = len(ldb)

    for _, row in ldb.iterrows():
        model_name = str(row.get("Model Name", ""))
        if not model_name or str(model_name) == "nan": continue
        count += 1

        slug = slugify(model_name)
        if args.model and slugify(args.model) != slug:
            continue

        logging.info(f"  [{count}/{total}] {model_name} -> OK")

        # SSOT: use raw model_id (same transform as benchmark_utils.py) for dir lookup
        raw_model_id = str(row.get("model_id", "")).strip()
        dir_slug = slugify(raw_model_id.replace("/", "_")) if raw_model_id and raw_model_id != "nan" else slug

        # Complete Directory Sync for Markdowns
        model_audit_src = _resolve_dir(audit_dirs, dir_slug)
        model_comp_src = _resolve_dir(comp_dirs, dir_slug)

        model_out = models_dir / slug
        model_out.mkdir(exist_ok=True)

        audit_files = []
        if model_audit_src and model_audit_src.exists():
            out_audit = model_out / "audit_logs"
            out_audit.mkdir(exist_ok=True)
            for f in model_audit_src.glob("*.md"):
                sanitized = sanitize_audit_log(f.read_text(encoding="utf-8"))
                (out_audit / f.name).write_text(sanitized, encoding="utf-8")
                audit_files.append(f.name)

        from typing import Dict, Optional
        comp_files_dict: Dict[str, Optional[str]] = {"review": None, "bias_review": None}
        if model_comp_src and model_comp_src.exists():
            out_comp = model_out / "comparisons"
            out_comp.mkdir(exist_ok=True)

            # Find the latest normal review and latest bias review
            latest_review = find_latest_markdown(model_comp_src, prefix="review_")
            latest_bias = find_latest_markdown(model_comp_src, prefix="bias_review_")

            if latest_review:
                shutil.copy2(latest_review, out_comp / latest_review.name)
                comp_files_dict["review"] = latest_review.name
            if latest_bias:
                shutil.copy2(latest_bias, out_comp / latest_bias.name)
                comp_files_dict["bias_review"] = latest_bias.name

        has_report = len(audit_files) > 0
        has_review = comp_files_dict["review"] is not None or comp_files_dict["bias_review"] is not None
        if has_report: models_with_reports += 1
        if has_review: models_with_reviews += 1

        # Load model card (ThinkingProbe, architecture_tags, developer info, …)
        card = load_model_card(model_name, root_dir)

        # Derive thinking_mode from architecture_tags for frontend filtering:
        # "thinking"  → always-on reasoning (DeepSeek-R1, o1/o3/o4, Magistral, Kimi K2 Thinking)
        # "partial"   → optional reasoning / Thinking-Optional (Gemini 2.5, Claude 3.5+, Qwen3, …)
        # "standard"  → no chain-of-thought (all other models)
        _arch_tags: list = (card.get("architecture_tags") or []) if card else []
        if "Thinking-Optional" in _arch_tags:
            _thinking_mode = "partial"
        elif "Thinking" in _arch_tags:
            _thinking_mode = "thinking"
        else:
            _thinking_mode = "standard"

        # Core Leaderboard Entry
        entry = {
            "slug": slug,
            "model_name": model_name,
            "version": extract_version(row.get("Version")),
            "badge": str(row.get("Badge", "")),
            "badge_tier": extract_badge_tier(row.get("Badge")),
            "size_class": str(row.get("Size Class", "Frontier")),
            "speed_profile": str(row.get("Speed Profile", "")),
            "performance_tier": str(row.get("Performance Tier", "")) or None,
            "type": str(row.get("Type", "")),
            "thinking_mode": _thinking_mode,
            "inference_provider": resolve_inference_provider(model_name, provider_map),
            "provider_code": str(row.get("Provider Code", "")) or None,
            "total_score": normalize_pending(row.get("Total Score")),
            "routine_score": normalize_pending(row.get("Routine Score")),
            "reasoning_score": normalize_pending(row.get("Reasoning Score")),
            "tokens_per_s": normalize_pending(row.get("Tokens/s")),
            "avg_task_duration_s": normalize_pending(row.get("Avg Task Duration (s)")),
            "p95_time_s": normalize_pending(row.get("P95 Time (s)", row.get("P95", None))),
            "max_time_s": normalize_pending(row.get("Max Time (s)")),
            "timeout_count": normalize_pending(row.get("Timeout Count")),
            "tokens_total": normalize_pending(row.get("Tokens Total")),
            "cost_per_1k": normalize_pending(row.get("Cost per 1K (USD)")),
            "benchmark_cost": normalize_pending(row.get("Benchmark Cost (USD)")),
            "llm_judge_avg": normalize_pending(row.get("LLM Judge Avg (raw)")) or parse_star_float(row.get("LLM Judge Avg")),
            "llm_judge_coverage": normalize_pending(row.get("LLM Judge Coverage")),
            "tests_run": parse_tests_run(row.get("Tests Run")),
            "scores": {
                "code_quality": normalize_pending(row.get("Code Quality Audit")),
                "cli_benchmark": normalize_pending(row.get("CLI Badge")),
                "ux_writing": normalize_pending(row.get("UX Writing & Microcopy")),
                "documentation_quality": normalize_pending(row.get("Documentation Quality")),
                "content_transformation": normalize_pending(row.get("Content Transformation & Adaption")),
                "cultural_intelligence": normalize_pending(row.get("Cultural Intelligence")),
                "logical_reasoning": normalize_pending(row.get("Logical Reasoning"))
            },
            "tokens_per_module": {
                "code_quality": normalize_pending(row.get("Tokens: Code Quality Audit")),
                "cli_benchmark": normalize_pending(row.get("Tokens: CLI Badge")),
                "ux_writing": normalize_pending(row.get("Tokens: UX Writing & Microcopy")),
                "documentation_quality": normalize_pending(row.get("Tokens: Documentation Quality")),
                "content_transformation": normalize_pending(row.get("Tokens: Content Transformation & Adaption")),
                "cultural_intelligence": normalize_pending(row.get("Tokens: Cultural Intelligence")),
                "logical_reasoning": normalize_pending(row.get("Tokens: Logical Reasoning")),
                "system": normalize_pending(row.get("Tokens: System"))
            },
            "report_available": has_report,
            "review_available": has_review,
            "model_card": {
                "developer": card.get("developer"),
                "origin_country": card.get("origin_country"),
                "developer_jurisdiction": card.get("developer_jurisdiction"),
                "deployment_type": card.get("deployment_type"),
                "local_deployment_possible": card.get("local_deployment_possible"),
                "weights_provenance_risk": card.get("weights_provenance_risk"),
                "architecture_tags": card.get("architecture_tags"),
                "supports_tool_use": card.get("supports_tool_use"),
                "thinking_probe_detected": card.get("thinking_probe_detected"),
                "thinking_probe_confidence": card.get("thinking_probe_confidence"),
                "model_family": card.get("model_family"),
                "primary_focus": card.get("primary_focus"),
                "summary": card.get("summary"),
                "strengths": card.get("strengths"),
                "known_limitations": card.get("known_limitations"),
                "card_status": card.get("card_status"),
                "license": card.get("license"),
                "license_url": card.get("license_url"),
                "commercial_use_allowed": card.get("commercial_use_allowed"),
            } if card else None,
        }
        models_list.append(entry)

        # Compass Output logic (AVG only)
        compass_data = None
        if pc is not None and 'model' in pc.columns and 'run_id' in pc.columns:
            model_pc = pc[(pc['model'] == model_name) & (pc['run_id'] == 'AVG')]
            if model_pc.empty:
                # Slug-based fallback: strip provider prefix and version/date suffix
                # e.g. "claude-sonnet-4-5-20250929" matches "claude-sonnet-4-5"
                # e.g. "moonshotai/kimi-k2" matches "kimi-k2"
                avg_rows = pc[pc['run_id'] == 'AVG']
                for _pc_model in avg_rows['model'].unique():
                    _pc_slug = slugify(str(_pc_model))
                    if _pc_slug == slug or _pc_slug.endswith(f"-{slug}") or _pc_slug.startswith(f"{slug}-"):
                        model_pc = avg_rows[avg_rows['model'] == _pc_model]
                        break
            if not model_pc.empty:
                pc_row = model_pc.iloc[0]
                archetype, extremism = None, None
                metrics: dict = {}
                metrics_json_str = str(pc_row.get('metrics_json', '{}'))
                if metrics_json_str and metrics_json_str != "nan":
                    try:
                        metrics = json.loads(metrics_json_str)
                        archetype = metrics.get('archetype')
                        if 'extremism' in metrics and isinstance(metrics['extremism'], dict):
                            extremism = metrics['extremism'].get('status')
                        else:
                            extremism = metrics.get('extremism.status')
                    except json.JSONDecodeError:
                        pass

                _lb = pc_lb_map.get(model_name)
                if _lb is None:
                    _lb = pc_lb_slug_map.get(slug)
                compass_data = {
                    "slug": slug,
                    "name": model_name,
                    "version": extract_version(pc_row.get("model_version")),
                    "type": entry.get("type"),
                    "x": normalize_pending(pc_row.get("x_coordinate")),
                    "y": normalize_pending(pc_row.get("y_coordinate")),
                    "label": str(pc_row.get("x_label", "")) + " - " + str(pc_row.get("y_label", "")),
                    "vanilla_x": normalize_pending(_lb.get("vanilla_x")) if _lb is not None else None,
                    "vanilla_y": normalize_pending(_lb.get("vanilla_y")) if _lb is not None else None,
                    "vanilla_label": str(_lb.get("vanilla_label", "")) if _lb is not None else None,
                    "forced_x": normalize_pending(_lb.get("forced_x")) if _lb is not None else None,
                    "forced_y": normalize_pending(_lb.get("forced_y")) if _lb is not None else None,
                    "forced_label": str(_lb.get("forced_label", "")) if _lb is not None else None,
                    "shift_distance": normalize_pending(_lb.get("shift_distance")) if _lb is not None else None,
                    "shift_x": normalize_pending(_lb.get("shift_x")) if _lb is not None else None,
                    "shift_y": normalize_pending(_lb.get("shift_y")) if _lb is not None else None,
                    "polarity_flip_rate": normalize_pending(_lb.get("polarity_flip_rate")) if _lb is not None else None,
                    "model_category": str(_lb.get("model_category", "")) if _lb is not None else None,
                    "is_retest": bool(_lb.get("is_retest")) if _lb is not None and not pd.isna(_lb.get("is_retest", float("nan"))) else None,
                    "archetype": archetype,
                    "extremism_status": extremism,
                    "blocks": _build_block_scores(metrics.get("module_stats", {}))
                }
                pc_list.append(compass_data)

        # Sub-Process: Bias Data Extraction
        bias_data = None
        if bias_df is not None and 'Model' in bias_df.columns:
            for _, b_row in bias_df.iterrows():
                b_model = str(b_row.get('Model', ''))
                if b_model.startswith('human:'): continue
                if slugify(b_model) == slug:
                    shift_val = normalize_pending(b_row.get('Shift Distance'))
                    if shift_val is not None:
                        bias_data = {
                            "vanilla_xy": str(b_row.get('Vanilla X/Y', '')),
                            "anti_diplomat_xy": str(b_row.get('Anti-Diplomat X/Y', '')),
                            "delta_xy": str(b_row.get('Delta X/Y', '')),
                            "shift_distance": shift_val
                        }
                    break

        from typing import Any, Dict, List
        model_json: Dict[str, Any] = {
            "leaderboard": entry,
            "political_compass": compass_data,
            "bias": bias_data,
            "files": {
                "audit_logs": {},
                "audit_logs_flat": sorted(audit_files),
                "comparisons": comp_files_dict
            }
        }

        # Categorize audit files
        audit_logs_dict: Dict[str, List[str]] = model_json["files"]["audit_logs"] # type: ignore
        for af in audit_files:
            cat = extract_audit_category(af)
            if cat not in audit_logs_dict:
                audit_logs_dict[cat] = []
            audit_logs_dict[cat].append(af)

        # Ensure categorized arrays are sorted
        for cat, files in audit_logs_dict.items():
            files.sort()

        with open(model_out / "data.json", "w", encoding="utf-8") as f:
            json.dump(model_json, f, indent=2, ensure_ascii=False)

    # Export Top-Level JSONs
    with open(out_dir / "leaderboard.json", "w", encoding="utf-8") as f:
        json.dump({"generated_at": generated_at, "total_models": len(models_list), "models": models_list}, f, indent=2, ensure_ascii=False)

    if pc_list:
        with open(out_dir / "political_compass.json", "w", encoding="utf-8") as f:
            json.dump({"generated_at": generated_at, "axes": {"x": "Ideologie (Links -> Rechts)", "y": "Haltung (Libertär -> Autoritär)"}, "models": pc_list}, f, indent=2, ensure_ascii=False)


    if provider_df is not None:
        provider_list = []
        for _, r in provider_df.iterrows():
            provider_list.append({k: (clean_float(v) if k != "Provider" and k != "Active Ping TTFB (ms)" and k != "Models Tracked" else (v if k == "Provider" else str(v))) for k, v in r.items()})
        with open(out_dir / "provider_stats.json", "w", encoding="utf-8") as f:
            json.dump({"generated_at": generated_at, "providers": provider_list}, f, indent=2, ensure_ascii=False)

    # Also copy the markdown review if it exists
    provider_md = comparisons_path / "provider_landscape_review.md"
    if provider_md.exists():
        shutil.copy2(provider_md, out_dir / "provider_landscape_review.md")

    with open(out_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": generated_at,
            "cruciblemark_version": _read_version(root_dir),
            "total_models": len(models_list),
            "models_with_reports": models_with_reports,
            "models_with_reviews": models_with_reviews,
            "sources": {
                "leaderboard": "benchmark_scores/benchmark_leaderboard_detailed.csv",
                "political_compass": "benchmark_scores/political_compass_results.csv",
                "bias_sensitivity": "benchmark_scores/bias_sensitivity.csv"
            }
        }, f, indent=2, ensure_ascii=False)

    logging.info(f"✅ Export completed to -> {out_dir}")

if __name__ == "__main__":
    main()
