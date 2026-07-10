# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import sys
from pathlib import Path
from typing import Any

_ROOT_DIR = Path(__file__).resolve().parents[2]
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from utils.io_helpers import atomic_copy as _atomic_copy, atomic_write_json as _atomic_write_json
from utils.model_utils import _safe_name
from utils.text_helpers import strip_emojis as _strip_emojis
from .filters import _collect_vendor_cards
from .constants import _SCORES_CONTRACT_KEYS

def _read_version(root_dir: Path) -> str:
    """Reads project version from README.md badge line."""
    try:
        readme = root_dir / "README.md"
        for line in readme.read_text(encoding="utf-8").splitlines()[:10]:
            m = re.search(r"version-(\d+\.\d+\.\d+)-", line)
            if m:
                return m.group(1)
    except OSError as exc:
        logging.debug("Konnte Version aus README.md nicht lesen: %s", exc)
    return "unknown"


def find_latest_markdown(dir_path: Path, prefix: str = "") -> Path | None:
    if not dir_path.exists() or not dir_path.is_dir():
        return None
    md_files = list(dir_path.glob(f'{prefix}*.md'))
    return max(md_files, key=lambda p: p.stat().st_mtime) if md_files else None


def _review_date_range(dir_path: Path, prefix: str = "review_") -> tuple[str | None, str | None]:
    """
    Returns (published_at, updated_at) as ISO-8601 date strings (YYYY-MM-DD)
    derived from review filenames matching review_YYYYMMDD_HHMMSS.md.
    published_at = oldest file, updated_at = newest file.
    Returns (None, None) if no files found or no parseable date in filename.
    """
    if not dir_path or not dir_path.exists():
        return None, None
    dates: list[str] = []
    for f in dir_path.glob(f"{prefix}*.md"):
        m = re.search(r"_(\d{8})_", f.name)
        if m:
            raw = m.group(1)
            dates.append(f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}")
    if not dates:
        return None, None
    dates.sort()
    return dates[0], dates[-1]


def _build_benchmark_run_dates(runs_dir: Path) -> dict[str, str]:
    """
    Builds model_id → earliest benchmark_run_at (ISO date YYYY-MM-DD) from
    outputs/runs/results_*_YYYYMMDD_HHMMSS.json.
    Each JSON must have a 'model' field with the raw model_id.
    """
    result: dict[str, str] = {}
    if not runs_dir.exists():
        return result
    for f in runs_dir.glob("results_*.json"):
        m = re.search(r"_(\d{8})_\d{6}\.json$", f.name)
        if not m:
            continue
        raw = m.group(1)
        date_str = f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            mid: str = data.get("model", "") if isinstance(data, dict) else ""
            if not mid:
                continue
            if mid not in result or date_str < result[mid]:
                result[mid] = date_str
        except (json.JSONDecodeError, OSError) as exc:
            logging.debug("Unerwartete dispatch_summary-Eintragsform: %s", exc)
    return result


def _resolve_dir(dirs: dict[str, Path], raw_slug: str) -> Path | None:
    """Resolve a model-ID slug to a local directory path.

    Primary: direct match (SSOT — same transform as benchmark_utils.py).
    Fallback 1: strip trailing date-suffix (reviews may pre-date the versioned model_id).
    Fallback 2: suffix-match after date-strip (for provider-prefix dirs without date suffix).
    Fallback 3: -latest alias → versioned folder (e.g. "mistral-large-latest" → "mistral-large-3").
    """
    if raw_slug in dirs:
        return dirs[raw_slug]
    stripped = re.sub(r'-\d{4,8}$', '', raw_slug)
    if stripped != raw_slug and stripped in dirs:
        return dirs[stripped]
    if stripped != raw_slug:
        suffix_key = stripped.split('-', 1)[-1] if '-' in stripped else stripped
        suffix_matches = [v for k, v in dirs.items() if k.endswith(suffix_key)]
        if len(suffix_matches) == 1:
            return suffix_matches[0]
    if raw_slug.endswith("-latest") or raw_slug.endswith(":latest"):
        try:
            from utils.model_utils import get_model_version as _gmv
            _ver = _gmv(raw_slug, provider="api")
        except ImportError:
            _ver = None
        if _ver and _ver.strip() not in {"latest", "unknown", "k.A.", ""}:
            _vslug = re.sub(r"[:-]latest$", f"-{_ver.strip()}", raw_slug)
            if _vslug in dirs:
                return dirs[_vslug]
    return None


def _setup_output_dirs(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    """Sets up and validates output directories.

    Safety: only the models/ subdirectory of out_dir may be deleted.
    Returns (out_dir, models_dir, root_dir).
    """
    out_dir = Path(args.output).resolve()
    # Ensure we always write into a raw/ subdirectory (safety guard)
    if out_dir.name != "raw":
        out_dir = out_dir / "raw"
    models_dir = out_dir / "models"
    assert models_dir == (out_dir / "models"), "Safety check failed: rmtree target is not models/"
    out_dir.mkdir(parents=True, exist_ok=True)
    if models_dir.exists():
        shutil.rmtree(models_dir)
    models_dir.mkdir(exist_ok=True)
    root_dir = _ROOT_DIR
    return out_dir, models_dir, root_dir


def _export_model_files(
    model_out: Path,
    comp_src: Path | None,
) -> dict[str, str | None]:
    """Kopiert die Comparison-Markdown-Dateien (Review + Bias-Review) eines Modells.

    Audit-Logs (Judge-Logs pro Task) werden NICHT mehr exportiert — sie werden
    im Web-Frontend nirgends gerendert und waren toter Ballast (~35 MB).
    ``report_available`` wird stattdessen aus der Existenz des Audit-Quellverzeichnisses
    abgeleitet (siehe _audit_has_benchmark), ohne die Dateien zu kopieren.

    Returns:
        comp_files_dict mit Keys 'review' und 'bias_review' (jeweils Dateiname
        oder None).
    """
    comp_files_dict: dict[str, str | None] = {"review": None, "bias_review": None}
    if comp_src and comp_src.exists():
        out_comp = model_out / "comparisons"
        out_comp.mkdir(exist_ok=True)
        latest_review = find_latest_markdown(comp_src, prefix="review_")
        latest_bias = find_latest_markdown(comp_src, prefix="bias_review_")
        if latest_review:
            _atomic_copy(latest_review, out_comp / latest_review.name)
            comp_files_dict["review"] = latest_review.name
        if latest_bias:
            _atomic_copy(latest_bias, out_comp / latest_bias.name)
            comp_files_dict["bias_review"] = latest_bias.name

    return comp_files_dict


def _write_top_level_outputs(
    out_dir: Path,
    generated_at: str,
    models_list: list[dict[str, Any]],
    pc_list: list[dict[str, Any]],
    root_dir: Path,
    comparisons_path: Path,
    models_with_reports: int,
    models_with_reviews: int,
    models_skipped_blacklist: int = 0,
    blacklist_total_entries: int = 0,
    blacklist_source: str = "config/web_export_blacklist.yaml",
) -> None:
    """Writes leaderboard.json, political_compass.json, meta.json,
    und vendor_cards.json mit Souveraenitaets-/GDPR-Metadaten pro Vendor.

    models_skipped_blacklist: Anzahl Modelle, die in diesem Run durch die Blacklist
        geblockt wurden. Plus blacklist_total_entries (SSoT-Anzahl in der Config)
        und blacklist_source (Dateipfad) landen im meta.json fuer Audit-Zwecke.
    """
    # Scores-Contract für leaderboard.json durchsetzen: _strip_none hat null-Werte
    # aus den Model-Einträgen entfernt, aber der Contract verlangt alle 9 Score-Keys
    # (auch null) — sonst sieht das Frontend im Leaderboard-Index 7-9 Keys statt 10.
    for _m in models_list:
        _scores = _m.get("scores")
        if isinstance(_scores, dict):
            for _k in _SCORES_CONTRACT_KEYS:
                _scores.setdefault(_k, None)
        elif _scores is None:
            _m["scores"] = dict.fromkeys(_SCORES_CONTRACT_KEYS, None)

    _atomic_write_json(
        out_dir / "leaderboard.json",
        _strip_emojis({"generated_at": generated_at, "total_models": len(models_list), "models": models_list}),
    )

    if pc_list:
        _atomic_write_json(
            out_dir / "political_compass.json",
            _strip_emojis({
                "generated_at": generated_at,
                "axes": {"x": "Ideologie (Links -> Rechts)", "y": "Haltung (Libertär -> Autoritär)"},
                "models": pc_list,
            }),
        )

    # BEFUND 4 Fix: Alle Vendor-Cards EINMAL lesen, dann in Memory splitten.
    # Vorher: _collect_vendor_cards(exclude_community=True) + _collect_community_cards()
    # lasen beide das gesamte Verzeichnis (54 File-Reads statt 27).
    all_vendor_cards = _collect_vendor_cards(root_dir)
    vendor_cards = [c for c in all_vendor_cards if c.get("card_subtype") != "community"]
    community_cards = [c for c in all_vendor_cards if c.get("card_subtype") == "community"]
    if vendor_cards:
        _atomic_write_json(
            out_dir / "vendor_cards.json",
            _strip_emojis({"generated_at": generated_at, "vendors": vendor_cards}),
        )
    if community_cards:
        _atomic_write_json(
            out_dir / "community_cards.json",
            _strip_emojis({"generated_at": generated_at, "communities": community_cards}),
        )

    # SSoT-Sanity-Counts: Filesystem vs. Leaderboard-Konsistenz
    card_dir = root_dir / "benchmark_scores" / "model_cards"
    audit_logs_path = root_dir / "outputs" / "audit_logs"
    card_count = len(list(card_dir.glob("*.json"))) if card_dir.exists() else 0
    # audit_log_count: NUR Audit-Logs fuer exportierte Modelle (Semantik-Konsistenz).
    # Zaehlt alle .md-Files in outputs/audit_logs/ wäre ein anderer Wert als das,
    # was im Webexport ankommt (dort nur Modelle aus dem Leaderboard).
    exported_slugs = {_safe_name(m.get("model_id") or m.get("slug", "")) for m in models_list}
    audit_log_count = 0
    if audit_logs_path.exists():
        for d in audit_logs_path.iterdir():
            if not d.is_dir():
                continue
            if _safe_name(d.name) in exported_slugs:
                audit_log_count += len(list(d.glob("*.md")))

    _atomic_write_json(
        out_dir / "meta.json",
        {
            "generated_at": generated_at,
            "cruciblemark_version": _read_version(root_dir),
            "total_models": len(models_list),
            "models_with_reports": models_with_reports,
            "models_with_reviews": models_with_reviews,
            "card_count": card_count,
            "audit_log_count": audit_log_count,
            "vendor_card_count": len(vendor_cards),
            "blacklist": {
                "source": blacklist_source,
                "total_entries": blacklist_total_entries,
                "skipped_in_run": models_skipped_blacklist,
            },
            "sources": {
                "leaderboard": "benchmark_scores/benchmark_leaderboard_detailed.csv",
                "political_compass": "benchmark_scores/political_compass_results.csv",
                "model_cards": "benchmark_scores/model_cards/",
                "vendor_cards": "benchmark_scores/vendor_cards/",
                "audit_logs": "outputs/audit_logs/",
            },
        },
    )

