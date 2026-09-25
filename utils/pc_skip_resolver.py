"""PC-Leaderboard-Cache und Batch-Skip-Resolver.

Separation-of-Concerns: Measurement-Layer (base_runner.py) soll nicht direkt
Leaderboard-CSVs lesen. Dieses Modul kapselt die Publishing-Operationen des
Political-Compass-Caches und wird von ``BaseBenchmarkRunner.execute_batch_module``
als Callback aufgerufen.
"""

import csv as _csv
import logging
import re as _re_pc
from pathlib import Path
from typing import Any

from benchmark_modules.political_compass.core.pc_probe_hook import (
    ensure_pc_token_probe as _ensure_pc_token_probe_hook,
)
from utils.scoring.political_compass_handler import PoliticalCompassHandler

logger = logging.getLogger(__name__)


def ensure_pc_token_probe(model: str, provider: str, client: Any) -> None:
    """Card-First-Hook: PC-Token-Probe vor dem PC-Run, wenn die Card keinen Eintrag hat.

    Pattern: Thinking-Probe (``unified_runner._ensure_model_card``). Die
    Probe läuft einmalig; das Ergebnis wird in die Model Card persistiert
    (``pc_token_calibration`` + ``pc_profile``), nachfolgende Läufe
    überspringen sie. Bei Probe-Fehlern (Fast-Fail-Guard) läuft der
    Benchmark weiter ohne Card-Write (nächster Lauf wiederholt die Probe).
    """
    try:
        _ensure_pc_token_probe_hook(model, provider, client)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning(
            "[Card-First] PC-Token-Probe für '%s' übersprungen: %s — "
            "Benchmark läuft weiter.",
            model, exc,
        )


def check_batch_cache_skip(
    model: str,
    batch_asset_id: str,
    benchmark_info: dict,
    existing_benchmarks: dict | None,
    force: bool,
) -> list | None:
    """Prüft den 3-CSV-Cache auf einen vorhandenen Batch-Eintrag.

    Returns:
        Liste mit Kopie des Cache-Eintrags bei Skip (nicht-PC-Module),
        sonst None — fällt zur PC-Leaderboard-Prüfung durch.
    """
    if not existing_benchmarks or force:
        return None

    cached_res = existing_benchmarks.get((model, batch_asset_id))
    if cached_res is None:
        return None

    if not PoliticalCompassHandler.is_political_compass(benchmark_info):
        logger.warning(
            f"⏩ Überspringe {benchmark_info.get('name', '')} "
            "(Batch-Modus; Bereits im Cache vorhanden)"
        )
        return [cached_res.copy()]

    logger.debug(
        "PC-Cache-Treffer in 3-CSVs für %s — prüfe pc_leaderboard.csv als SSoT.",
        model,
    )
    return None


def check_pc_leaderboard_skip(model: str, benchmark_info: dict, force: bool) -> bool:
    """Prüft das autarke PC-Leaderboard (SSoT für Political-Compass-Cache)."""
    if force or not PoliticalCompassHandler.is_political_compass(benchmark_info):
        return False

    pc_leaderboard = Path("benchmark_scores/political_compass_leaderboard.csv")
    if not pc_leaderboard.exists():
        return False

    try:
        model_normalized = _re_pc.sub(r"-\d{8}$", "", model)
        model_normalized = _re_pc.sub(
            r"-(0[1-9]|1[0-2])\d{2}$", "", model_normalized,
        )
        with pc_leaderboard.open("r", encoding="utf-8") as _f:
            pc_models = {row.get("model") for row in _csv.DictReader(_f)}
        if model in pc_models or model_normalized in pc_models:
            logger.warning(
                f"⏩ Überspringe {benchmark_info.get('name', '')} "
                f"(PC-Leaderboard; {model} bereits bewertet)"
            )
            return True
    except (OSError, _csv.Error):
        pass
    return False
