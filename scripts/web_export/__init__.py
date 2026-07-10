# ruff: noqa: E402,F401
from __future__ import annotations

import sys
from pathlib import Path

_ROOT_DIR = Path(__file__).resolve().parents[2]
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from utils.io_helpers import atomic_copy as _atomic_copy, atomic_write_json as _atomic_write_json, atomic_write_text as _atomic_write_text
from utils.text_helpers import (
    extract_badge_tier,
    extract_version,
    normalize_pending,
    parse_star_float,
    sanitize_audit_log,
    slugify,
    strip_emojis as _strip_emojis,
    strip_none as _strip_none,
)

from . import constants as _constants
from . import entry_builders as _entry_builders
from . import filters as _filters
from . import loader as _loader
from . import main as _main_module
from . import top_level as _top_level
from .entry_builders import (
    _normalize_export_tags,
    _build_block_scores,
    _build_characteristics,
    _build_compass_entry,
    _build_leaderboard_entry,
    _build_tooluse_entry,
    _lookup_pc_row,
    _read_latest_tooluse_narrative,
    _supports_tool_use_state,
    compute_is_retest,
    load_model_card,
    parse_tests_run,
)
from .filters import (
    _PLACEHOLDER_VENDOR_IDS,
    _build_community_alias_map,
    _build_community_card_id_lookup,
    _build_vendor_alias_map,
    _build_vendor_card_id_lookup,
    _collect_community_cards,
    _collect_vendor_cards,
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
    load_csv_with_fallback,
    resolve_inference_provider,
)
from .constants import (
    LdbCols,
    _BLACKLIST_PATH,
    _SCORES_CONTRACT_KEYS,
    _SCORE_COLUMN_TO_KEY,
    _ROOT_DIR,
)
from .main import (
    _audit_has_benchmark,
    _build_row_compass_data,
    _build_row_entry,
    _dedupe_slug,
    _init_export_context,
    _process_leaderboard,
    _resolve_model_dirs_and_card,
    _resolve_thinking_mode,
    _row_identity,
    _should_skip_model,
    _write_model_data,
)
from .top_level import (
    _build_benchmark_run_dates,
    _export_model_files,
    _read_version,
    _resolve_dir,
    _review_date_range,
    _setup_output_dirs,
    _write_top_level_outputs,
    find_latest_markdown,
)

_PATCHABLE_NAMES = (
    "_setup_output_dirs",
    "_load_sources",
    "_build_pc_lookups",
    "_load_pc_block_meta",
    "_build_benchmark_run_dates",
    "build_provider_map",
    "load_model_card",
    "_resolve_dir",
    "_export_model_files",
    "_build_leaderboard_entry",
    "_build_tooluse_entry",
    "_write_top_level_outputs",
    "_is_blacklisted",
    "_should_skip_model",
    "_resolve_model_dirs_and_card",
    "_atomic_write_json",
)


def _sync_package_patches() -> dict[tuple[object, str], object]:
    modules = (_main_module, _entry_builders, _filters, _loader, _top_level)
    originals: dict[tuple[object, str], object] = {}
    for name in _PATCHABLE_NAMES:
        value = globals().get(name)
        for module in modules:
            if hasattr(module, name):
                originals[(module, name)] = getattr(module, name)
                setattr(module, name, value)
    return originals


def _restore_module_attrs(originals: dict[tuple[object, str], object]) -> None:
    for (module, name), value in originals.items():
        setattr(module, name, value)


def main() -> None:
    originals = _sync_package_patches()
    try:
        return _main_module.main()
    finally:
        _restore_module_attrs(originals)


__all__ = [name for name in globals() if not name.startswith("__")]
