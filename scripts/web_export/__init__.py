# ruff: noqa: E402,F401
"""Web-Export-Package: aggregiert Leaderboard, Political-Compass, Vendor-Cards
und Model-Cards zu einem Datenpaket für das externe Frontend (cruciblemark-web).

Re-Exportiert die Namen der Submodule für bequemen Zugriff aus Tests und
externen Callern. Submodule sollten direkt importiert werden, wenn nur eine
einzelne Funktion benötigt wird.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT_DIR = Path(__file__).resolve().parents[2]
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

from utils.io_helpers import (
    atomic_copy as _atomic_copy,
    atomic_write_json as _atomic_write_json,
    atomic_write_text as _atomic_write_text,
)
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

from .constants import (
    LdbCols,
    _BLACKLIST_PATH,
    _ROOT_DIR,
    _SCORES_CONTRACT_KEYS,
    _SCORE_COLUMN_TO_KEY,
)
from .entry_builders import (
    _build_block_scores,
    _build_characteristics,
    _build_compass_entry,
    _build_leaderboard_entry,
    _build_model_card_subdict,
    _build_tooluse_entry,
    _lookup_pc_row,
    _normalize_export_tags,
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
    ProviderMap,
    _build_pc_lookups,
    _load_pc_block_meta,
    _load_sources,
    build_provider_map,
    load_csv_with_fallback,
    resolve_inference_provider,
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


__all__ = [
    # Öffentliche API
    "LdbCols",
    "ProviderMap",
    "build_provider_map",
    "resolve_inference_provider",
    "load_csv_with_fallback",
    "load_model_card",
    "compute_is_retest",
    "find_latest_markdown",
    "parse_tests_run",
]
