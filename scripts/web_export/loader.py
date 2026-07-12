# ruff: noqa: E402
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd
import yaml

_ROOT_DIR = Path(__file__).resolve().parents[2]
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from utils.model_id_base import strip_date_suffix
from utils.text_helpers import slugify

def build_provider_map(config_path: Path) -> dict[str, str]:
    """Builds a model_id → provider display name map from benchmark_config.yaml.

    Falls back to resolve_provider() for models not listed in the config
    (e.g. auto-discovered Ollama models). The returned name is the human-readable
    provider label (e.g. "Groq Cloud", "Ollama (Local)"), not the api_type key.
    """
    mapping: dict[str, str] = {}

    try:
        from utils.config_validator import ConfigValidator
        cfg = ConfigValidator(str(config_path)).config
    except (OSError, FileNotFoundError):
        return mapping

    providers_block = cfg.get("providers", {})
    # Build fallback map from config provider names (SSOT — no hardcoded strings)
    _fallbacks: dict[str, str] = {}
    for _tier_key, tier_val in providers_block.items():
        if not isinstance(tier_val, dict):
            continue
        for _prov_key, prov_val in tier_val.items():
            if not isinstance(prov_val, dict):
                continue
            if "name" not in prov_val:
                continue  # Skip config/settings sub-blocks (e.g. local.config)
            display_name: str = prov_val["name"]
            _fallbacks[_prov_key] = display_name
            for model_entry in prov_val.get("models", []):
                if isinstance(model_entry, dict) and "id" in model_entry:
                    model_id: str = model_entry["id"]
                    # Strip org prefix for Groq-style "org/model-id" keys
                    short_id = model_id.rsplit("/", maxsplit=1)[-1]
                    mapping[model_id] = display_name
                    if short_id != model_id:
                        mapping[short_id] = display_name

    # resolve_provider() returns "ollama" for all local models — alias to ollama_local name
    if "ollama" not in _fallbacks:
        _fallbacks["ollama"] = _fallbacks.get("ollama_local", "Ollama")

    # Store fallback names so callers can use them without importing model_utils
    mapping["__fallbacks__"] = _fallbacks  # type: ignore[assignment]
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


def load_csv_with_fallback(path: Path) -> pd.DataFrame | None:
    try:
        return pd.read_csv(path)
    except (OSError, pd.errors.ParserError) as e:
        logging.warning("  [WARN] Could not load %s: %s", path.name, e)
        return None


def _load_sources(scores_dir: Path) -> tuple[
    pd.DataFrame | None,
    pd.DataFrame | None,
    pd.DataFrame | None,
]:
    """Loads all source CSVs. Returns (ldb, pc, pc_lb)."""
    return (
        load_csv_with_fallback(scores_dir / "benchmark_leaderboard_detailed.csv"),
        load_csv_with_fallback(scores_dir / "political_compass_results.csv"),
        load_csv_with_fallback(scores_dir / "political_compass_leaderboard.csv"),
    )


def _build_pc_lookups(
    pc_lb: pd.DataFrame | None,
) -> tuple[dict, dict]:
    """Builds model-name → PC-leaderboard-row dicts (canonical-keyed).

    Keys sind ``strip_date_suffix(model)`` bzw. ``slugify(strip_date_suffix(model))`` —
    identisch zur Normalisierung, die ``io_manager.save_leaderboard_csv`` beim
    Schreiben der CSV anwendet. Dadurch matching der Lookup-Seite (Web-Export)
    konsistent mit der Writer-Seite (Benchmark-Pipeline), unabhängig davon ob
    eine Model-ID ein Datumssuffix trägt (z.B. ``z-ai/glm-5.1-20260406`` →
    Key ``z-ai/glm-5.1``).
    """
    pc_lb_map: dict = {}
    pc_lb_slug_map: dict = {}
    if pc_lb is not None and "model" in pc_lb.columns:
        for _, _row in pc_lb.iterrows():
            m = str(_row.get("model", ""))
            if m and m != "nan":
                canonical = strip_date_suffix(m)
                pc_lb_map[canonical] = _row
                pc_lb_slug_map[slugify(canonical)] = _row
    return pc_lb_map, pc_lb_slug_map


def _load_pc_block_meta(config_path: Path) -> dict:
    """Loads Political Compass block metadata from config.yaml.

    Falls back to a static dict if the config is unavailable or missing the blocks key.
    """
    _fallback: dict = {
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
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        blocks = data.get("blocks", {})
        if blocks:
            return {str(k): v for k, v in blocks.items()}
    except (OSError, yaml.YAMLError) as exc:
        logging.warning("PC-Block-Meta konnte nicht geladen werden: %s — verwende Fallback", exc)
    return _fallback

