"""
Gemeinsame llama.cpp-Batch-Orchestrierung für benchmark_auto.py und run_score_benchmark.py.

Zweiteilige Architektur:
- Lifecycle-Helper: Server-Start/Stop/Cleanup, Provider-Kontext
- Context-Manager: Sichere Session-Verwaltung mit Exception-basierter Fehlerbehandlung
- Cache-Helper: Existing-Results und Asset-Ermittlung

Der Modul-Executor wird als Callback übergeben, damit der Aufrufer die volle
Kontrolle über Modulfilter, Asset-Ermittlung, Delegation und Fehlerpolitik behält.
"""

import json
import re
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from collections.abc import Generator
import subprocess
import time
import pandas as pd
import yaml

from utils.model_id_base import _PROVIDER_ALIAS_MAP

logger = logging.getLogger(__name__)

# ROOT_DIR für absolute Pfade
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Konstante für Socket-Release-Zeit nach Server-Stop
LLAMACPP_STOP_SETTLE_SEC: int = 3


# =============================================================================
# EXCEPTIONS
# =============================================================================

class LlamaCppSessionError(Exception):
    """Fehler beim Starten oder Verwalten einer llama.cpp-Server-Session."""


# =============================================================================
# EBENE 1: Lifecycle-Helper (keine Benchmark-Logik)
# =============================================================================

def is_llamacpp_provider(provider_key: str) -> bool:
    """Returns True for local llama.cpp-style provider keys.

    Phase 19: Aliase `llama_cpp` und `llamacpp_local` entfernt.
    Jeder Provider hat jetzt seinen eigenen eindeutigen Schlüssel
    (`llamacpp` = M4 MacBook, `llamacpp_spark` = DGX Spark).
    """
    return provider_key in {"llamacpp", "llamacpp_spark"}


def get_enabled_llamacpp_providers(config: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Returns enabled local llama.cpp-style providers in config order."""
    local_cfg = config.get("providers", {}).get("local", {})
    enabled: list[tuple[str, dict[str, Any]]] = []
    for provider_key, provider_cfg in local_cfg.items():
        if not isinstance(provider_cfg, dict):
            continue
        if provider_cfg.get("api_type") != "llamacpp":
            continue
        if not provider_cfg.get("enabled", False):
            continue
        enabled.append((provider_key, provider_cfg))
    return enabled


def set_llamacpp_provider_context(client: Any, provider_key: str) -> None:
    """Configures the shared llama.cpp client instance for the requested provider key."""
    setter = getattr(client, "_set_provider_context", None)
    if callable(setter):
        setter(provider_key)


def stop_llamacpp_provider_server(
    config: dict[str, Any],
    provider_key: str | None = None,
) -> None:
    """Stops llama.cpp server(s) - prophylactic or specific provider.

    Args:
        config: Vollständige Config (für Provider-Lookup)
        provider_key: Optional - nur diesen Provider stoppen
    """
    enabled_llamacpp = get_enabled_llamacpp_providers(config)
    if not enabled_llamacpp:
        return

    if provider_key is not None:
        enabled_llamacpp = [(k, v) for k, v in enabled_llamacpp if k == provider_key]
        if not enabled_llamacpp:
            return

    print("   🧹 Stoppe laufende llama-server (prophylaktisch) ...")
    seen_cmds: set[str] = set()
    for _pkey, provider_cfg in enabled_llamacpp:
        stop_cmd = str(provider_cfg.get("server_stop_cmd", "pkill -f llama-server")).strip()
        if not stop_cmd or stop_cmd in seen_cmds:
            continue
        seen_cmds.add(stop_cmd)
        # shell=True ist hier bewusst: server_stop_cmd ist ein vom Operator
        # konfiguriertes Shell-Kommando (Trust-Boundary: provider_config.yaml).
        subprocess.run(stop_cmd, shell=True, check=False, capture_output=True)

    time.sleep(LLAMACPP_STOP_SETTLE_SEC)


def run_llamacpp_provider_cleanup(provider_key: str, provider_cfg: dict[str, Any]) -> None:
    """Führt End-of-Batch Cleanup für einen llama.cpp-Provider aus.

    Wird nach dem Server-Stop aufgerufen (post_stop_cmd, Cache-Bereinigung).
    """
    if not provider_cfg.get("cleanup_on_exit", False):
        return

    post_stop_cmd = provider_cfg.get("server_post_stop_cmd")
    if not post_stop_cmd:
        return

    print(f"   🧹 Post-Stop Cleanup für '{provider_key}' ...")
    try:
        subprocess.run(post_stop_cmd, shell=True, check=False)
    except Exception as exc:
        print(f"   ⚠️ Post-Stop Cleanup fehlgeschlagen: {exc}")


# =============================================================================
# EBENE 2: Context-Manager (Sichere Session-Verwaltung)
# =============================================================================

@contextmanager
def llamacpp_model_session(
    runner: Any,  # UnifiedBenchmarkRunner
    provider_key: str,
    provider_cfg: dict[str, Any],
    model_id: str,
) -> Generator[Any, None, None]:
    """Context-Manager für llama.cpp-Modell-Session mit automatischem Cleanup.

    Stellt sicher, dass der Server nach der Verwendung immer gestoppt wird,
    auch bei Exceptions oder KeyboardInterrupt.

    Raises:
        LlamaCppSessionError: Wenn der Server nicht gestartet werden kann
            oder der Client nicht im Registry gefunden wird.

    Usage:
        try:
            with llamacpp_model_session(runner, provider_key, provider_cfg, model_id) as client:
                for module in modules:
                    results = runner.run_benchmark(...)
        except LlamaCppSessionError as e:
            print(f"Session-Fehler: {e}")
            continue  # Nächstes Modell

    Args:
        runner: UnifiedBenchmarkRunner-Instanz (muss _skip_llamacpp_cleanup=True haben)
        provider_key: z.B. "llamacpp_spark"
        provider_cfg: Provider-Konfiguration aus config
        model_id: Modell-ID aus provider_config.yaml

    Yields:
        LlamaCppClient-Instanz
    """
    lcpp_client = runner.client.clients.get(provider_key)
    if lcpp_client is None:
        raise LlamaCppSessionError(
            f"LlamaCppClient '{provider_key}' nicht im Client-Registry gefunden."
        )

    set_llamacpp_provider_context(lcpp_client, provider_key)

    # Server starten
    if not lcpp_client.start_server(model_id):
        raise LlamaCppSessionError(
            f"Server für '{model_id}' konnte nicht gestartet werden."
        )

    try:
        yield lcpp_client
    finally:
        print("\n   🛑 Stoppe llama.cpp Server...")
        lcpp_client.stop_server()
        run_llamacpp_provider_cleanup(provider_key, provider_cfg)


# =============================================================================
# EBENE 3: Cache-Helper (Existing Results)
# =============================================================================

def get_existing_results(
    csv_path: Path,
    force: bool = False,
    provider_key: str | None = None,
) -> set[tuple[str, str]]:
    """Lädt Set von (Model, AssetID) für bereits existierende Tests.

    Berücksichtigt alle drei Haupt-CSVs (local, cloud, commercial)
    sowie Political Compass Leaderboard.

    Args:
        csv_path: Pfad zur primären CSV-Datei (wird ignoriert wenn force=True)
        force: Wenn True, leeres Set zurückgeben (Cache ignorieren)
        provider_key: Optional — Provider-Scoping (Separation-Fix 2026-08-28).
            Nur Zeilen dieses Providers werden gecacht. Alte Ergebnisse eines
            ANDEREN Providers mit identischer kanonischer Modell-ID
            (Mac ``qwen3.5-4b-q8`` ↔ Spark ``qwen3_5-4b-q8``) suppressen
            den Batch dann nicht mehr. None = provider-blind (Legacy,
            z.B. Commercial-Batch mit eindeutigen Modell-IDs).

    Returns:
        Set von (model_id, asset_id) Tupeln
    """
    from utils.config_validator import ConfigValidator

    cache: set[tuple[str, str]] = set()
    if force:
        return cache

    # ConfigValidator ist verpflichtend (kein defensiver Fallback).
    # Performance (Review 2026-08-15): ConfigValidator hat jetzt einen
    # mtime-invalidierten Klassen-Cache — mehrfaches Instanziieren pro
    # Batch-Loop ist kein YAML-Re-Parse mehr. Der innere pd-Import entfiel
    # (pd ist bereits auf Modulebene importiert).
    validator = ConfigValidator()
    output_cfg = validator.config.get("output", {})

    csv_paths = [
        Path(output_cfg.get("local_models_csv", "benchmark_scores/local_models_benchmark.csv")),
        Path(output_cfg.get("cloud_models_csv", "benchmark_scores/cloud_models_benchmark.csv")),
        Path(output_cfg.get("commercial_models_csv", "benchmark_scores/commercial_models_benchmark.csv")),
    ]

    for path in csv_paths:
        if not path.exists():
            continue
        try:
            df = pd.read_csv(path)
            _add_existing_result_rows(cache, df, provider_key)
        except Exception as e:
            print(f"⚠️ Warnung beim Lesen von {path}: {e}")

    # Political Compass Leaderboard
    pc_csv = ROOT_DIR / "benchmark_scores" / "political_compass_leaderboard.csv"
    if pc_csv.exists():
        try:
            df_pc = pd.read_csv(pc_csv)
            _add_political_compass_rows(cache, df_pc, provider_key)
        except Exception as e:
            print(f"⚠️ Warnung beim Lesen von {pc_csv}: {e}")

    return cache


def _normalize_provider_key(provider: Any) -> str:
    """Normalisiert Provider-Bezeichner aus CSV-Zeilen/Config für den Vergleich.

    Nutzt die SSoT-Alias-Map (``llama_cpp``/``llamacpp_local`` → ``llamacpp``,
    ``ollama`` → ``ollama_local``), damit Legacy-Zeilen mit alten Aliasen
    weiterhin zum richtigen Provider matchen.
    """
    key = str(provider or "").strip().lower()
    return _PROVIDER_ALIAS_MAP.get(key, key)


def _provider_row_matches(df: Any, row: Any, provider_key: str | None) -> bool:
    """True wenn die CSV-Zeile zum angeforderten Provider passt (Separation).

    Provider-Spalte: ``provider`` (Benchmark-CSVs) bzw. ``provider_type``
    (Political Compass). Ohne provider_key (None) matcht alles (Legacy).
    Fehlt die Spalte, ist die Zeile im gescopeten Modus nicht attribuierbar
    → nicht cachen (lieber neu laufen lassen als fremde Results suppressen).
    """
    if provider_key is None:
        return True
    column = "provider" if "provider" in df.columns else "provider_type"
    if column not in df.columns:
        return False
    return _normalize_provider_key(row.get(column)) == _normalize_provider_key(provider_key)


def _add_existing_result_rows(
    cache: set[tuple[str, str]],
    df: Any,
    provider_key: str | None = None,
) -> None:
    """Adds completed (model, asset_id) entries from a benchmark CSV into the cache.

    Fügt jede kanonische Lookup-Variante des Modellnamens hinzu, damit der
    Cache-Lookup unabhängig von der Schreibweise des Callers funktioniert
    (Defense-in-Depth gegen Punkt/Underscore- und Suffix-Mismatch).
    """
    required = {"model", "asset_id"}
    if not required.issubset(df.columns):
        return

    completed_statuses = {"success", "language_mismatch", "truncated", "refusal"}
    for _, row in df.iterrows():
        if "status" in df.columns:
            status = str(row.get("status", "")).lower()
            if status not in completed_statuses:
                continue
        if not _provider_row_matches(df, row, provider_key):
            continue

        model_str = str(row["model"])
        asset_str = str(row["asset_id"])
        for variant in canonical_lookup_keys(model_str):
            cache.add((variant, asset_str))


def _add_political_compass_rows(
    cache: set[tuple[str, str]],
    df: Any,
    provider_key: str | None = None,
) -> None:
    """Adds political-compass leaderboard rows to the cache using the batch ID.

    Multi-Key: alle kanonischen Lookup-Varianten des Modellnamens werden
    gecacht, damit der Cache-Lookup unabhängig von der Schreibweise des
    Callers funktioniert. Provider-Scoping analog zu _add_existing_result_rows.
    """
    if "model" not in df.columns:
        return

    for _, row in df.iterrows():
        if not _provider_row_matches(df, row, provider_key):
            continue
        model_str = str(row["model"])
        for variant in canonical_lookup_keys(model_str):
            cache.add((variant, "political_compass_v3"))


def canonical_lookup_keys(model: Any) -> set[str]:
    """SSoT: Alle äquivalenten Lookup-Key-Varianten für einen Modellnamen.

    Defense-in-Depth gegen Identifier-Mismatch: ein Cache-Lookup soll
    funktionieren, egal in welcher Schreibweise der Caller den Namen
    liefert. Typische Mismatches:

    - Roh-Name aus Config: ``qwen2.5-coder-7b`` (Punkt)
    - Kanonische Form:      ``qwen2_5-coder-7b`` (Underscore, via ``_safe_name``)
    - Vendor-Prefix:        ``meta-llama/Llama-3.1-8B`` (Slash) vs.
                             ``meta-llama_Llama-3_1-8B`` (Underscore)
    - hf.co-Prefix:         ``hf.co/...`` → wird gestrippt
    - Datumssuffix:         ``gpt-5-20251001`` → ``gpt-5``

    Beide Seiten des Cache-Lookups (Reader und Lookup-Site) MÜSSEN diese
    Funktion nutzen — sonst gibt es wieder einen Mismatch.

    Args:
        model: Beliebiger Identifier (str, ``None`` oder nicht-string).

    Returns:
        Set äquivalenter String-Varianten (dedupliziert, ohne Leerstrings).
    """
    from utils.model_utils import _safe_name, normalize_model_id, strip_date_suffix

    variants: set[str] = set()
    if not isinstance(model, str):
        return variants
    raw = model.strip()
    if not raw:
        return variants

    variants.add(raw)

    # Schritt 1: hf.co/-Prefix strippen
    no_hf = normalize_model_id(raw)
    if no_hf and no_hf != raw:
        variants.add(no_hf)

    # Schritt 2: Datumssuffix strippen (auf beiden Varianten)
    for v in list(variants):
        no_date = strip_date_suffix(v)
        if no_date and no_date != v:
            variants.add(no_date)

    # Schritt 3: _safe_name auf jede Variante anwenden
    for v in list(variants):
        safe = _safe_name(v)
        if safe and safe != v:
            variants.add(safe)

    # Schritt 4: Asymmetrische Bruecke Underscore -> Punkt.
    # Wenn der Caller einen Underscore-Namen liefert (z. B. 'qwen2_5-coder-7b',
    # wie er im Leaderboard steht), soll der Cache-Lookup auch dann greifen,
    # wenn der spaetere Aufrufer den Namen mit Punkt schreibt ('qwen2.5-coder-7b').
    # _safe_name ist destruktiv (Punkt -> Underscore), daher koennen wir den
    # Schritt nicht 1:1 umkehren. Heuristik: Ziffer_Ziffer -> Ziffer.Ziffer trifft
    # typische Versions-/Groessenangaben (qwen2.5, qwen3.5, llama3.3 etc.).
    for v in list(variants):
        if "_" not in v:
            continue
        dotted = re.sub(r"(\d)_(\d)", r"\1.\2", v)
        if dotted and dotted != v:
            variants.add(dotted)

    return variants


# =============================================================================
# EBENE 4: Asset-Ermittlung (vollständig aus benchmark_auto.py extrahiert)
# =============================================================================

def get_startable_assets(
    module: dict[str, Any],
    model: str,
    existing_tests: set[tuple[str, str]],
) -> list[Path]:
    """Ermittelt Asset-Pfade, die für dieses Modell noch nicht getestet wurden.

    VOLLSTÄNDIGE Version mit:
    - skip_if_card_false (Tool-Use-Card-State)
    - Batch-Module-Sonderbehandlung (political_compass)
    - YAML-Parsing und Cache-Check
    """
    assets_path = module.get("path", "")
    if not assets_path:
        return []

    if _should_skip_due_to_card(module, model):
        return []
    if _is_batch_module_done(module, model, existing_tests):
        return []

    p = Path(assets_path)
    if not p.exists():
        return []

    return _resolve_uncached_assets(p, model, existing_tests)


# -- Phase 3G: Helfer für get_startable_assets ------------------------------------

def _should_skip_due_to_card(module: dict[str, Any], model: str) -> bool:
    """Prüft skip_if_card_false (z. B. Tool-Use: Card-Wert false/untested).

    True → Modell soll das Modul überspringen (Card-Wert: false / not_applicable).
    False → normal weiter (Card-Wert: true / "untested" / Card fehlt).
    """
    from utils.model_utils import (
        normalize_supports_tool_use,
        _find_card as _fc,
    )
    skip_card_key = module.get("skip_if_card_false")
    if not skip_card_key:
        return False
    card_dir = ROOT_DIR / "benchmark_scores" / "model_cards"
    card_path = _fc(model, card_dir=card_dir)
    if not card_path.exists():
        return False
    try:
        card = json.loads(card_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning(
            "Card-Flag-Skip konnte nicht geprüft werden "
            "(model=%s, module=%s, card=%s): %s",
            model, module.get("key", module.get("name", "unknown")),
            card_path, exc,
        )
        return False

    raw_val = card.get(skip_card_key)
    norm_val = normalize_supports_tool_use(raw_val)
    if norm_val is False or raw_val == "not_applicable":
        reason = "not_applicable" if raw_val == "not_applicable" else "false"
        print(
            f"   ⏩ Bench: {module.get('name', module.get('key'))} "
            f"({skip_card_key}={reason} in Card — übersprungen)"
        )
        return True
    return False


def _is_batch_module_done(
    module: dict[str, Any],
    model: str,
    existing_tests: set[tuple[str, str]],
) -> bool:
    """True wenn das Batch-Modul (z. B. political_compass) bereits einen Score hat."""
    is_batch = module.get("execution_mode") == "batch" or module.get("key") == "political_compass"
    if not is_batch:
        return False
    batch_id = "political_compass_v3"
    return any(
        (variant, batch_id) in existing_tests
        for variant in canonical_lookup_keys(model)
    )


def _resolve_uncached_assets(
    assets_dir: Path,
    model: str,
    existing_tests: set[tuple[str, str]],
) -> list[Path]:
    """Lädt alle Asset-YAMLs und filtert die bereits im Cache vorhandenen heraus."""
    asset_files = sorted(assets_dir.glob("*.yaml"))
    if not asset_files:
        return []

    assets_todo: list[Path] = []
    for asset_f in asset_files:
        if _is_asset_uncached(asset_f, model, existing_tests):
            assets_todo.append(asset_f)
    return assets_todo


def _is_asset_uncached(
    asset_f: Path,
    model: str,
    existing_tests: set[tuple[str, str]],
) -> bool:
    """Lädt asset_id aus YAML. Defensiv: Parse-Error → als uncached behandeln."""
    try:
        with open(asset_f, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        asset_id = data.get("metadata", {}).get("id")
    except (OSError, yaml.YAMLError) as exc:
        logger.warning(
            "Asset konnte nicht geparst werden, wird defensiv ausgeführt "
            "(model=%s, module=%s, asset=%s): %s",
            model, "<module>", asset_f, exc,
        )
        return True

    if not asset_id:
        logger.warning(
            "Asset ohne metadata.id wird ausgeführt "
            "(model=%s, module=%s, asset=%s)",
            model, "<module>", asset_f,
        )
        return True

    return not any(
        (variant, asset_id) in existing_tests
        for variant in canonical_lookup_keys(model)
    )


# =============================================================================
# EBENE 4b: Leaderboard-Cache (zweite Verteidigungslinie)
# =============================================================================

# Mapping module-key → Spalte in benchmark_leaderboard.csv
LEADERBOARD_COLUMN_FOR_MODULE: dict[str, str] = {
    "code_quality": "Code Quality Audit",
    "cli_benchmark": "CLI Badge",
    "reasoning_logic": "Logical Reasoning",
    "ux_writing": "UX Writing & Microcopy",
    "documentation_quality": "Documentation Quality",
    "content_transformation": "Content Transformation & Adaption",
    "cultural_intelligence": "Cultural Intelligence",
}


def get_leaderboard_scored_modules(
    leaderboard_path: Path | None = None,
    force: bool = False,
) -> set[tuple[str, str]]:
    """Lädt Set von (model_id, module_key) für Modelle/Module mit gültigem Leaderboard-Score.

    Zweite Verteidigungslinie gegen veraltete Score-CSVs: wenn das Leaderboard
    für ein (Modell, Modul)-Paar einen non-Pending Score zeigt, soll das Auto-
    Skript keinen Subprozess starten, auch wenn die Detail-CSV Inkonsistenzen
    enthält.
    """
    cache: set[tuple[str, str]] = set()
    if force:
        return cache

    if leaderboard_path is None:
        leaderboard_path = ROOT_DIR / "benchmark_scores" / "benchmark_leaderboard.csv"
    if not leaderboard_path.exists():
        return cache

    try:
        df = pd.read_csv(leaderboard_path)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning(
            "Leaderboard-Cache deaktiviert — CSV nicht lesbar (%s): %s",
            leaderboard_path, exc,
        )
        return cache

    if "Model ID" not in df.columns:
        return cache

    for _, row in df.iterrows():
        model_id = _extract_model_id_from_row(row)
        if not model_id:
            continue
        _add_scored_modules_for_model(cache, df, row, model_id)
    return cache


# -- Phase 3G: Helfer für get_leaderboard_scored_modules ---------------------------

def _extract_model_id_from_row(row: Any) -> str:
    """Liest Model-ID aus Leaderboard-Zeile. Empty String wenn ungültig."""
    raw = row.get("Model ID", "")
    if pd.isna(raw):
        return ""
    model_id = str(raw).strip()
    if not model_id or model_id.lower() == "nan":
        return ""
    return model_id


def _add_scored_modules_for_model(
    cache: set[tuple[str, str]],
    df: Any,
    row: Any,
    model_id: str,
) -> None:
    """Pro (Modul, Leaderboard-Spalte): wenn gescored, alle Lookup-Varianten cachen."""
    for module_key, column in LEADERBOARD_COLUMN_FOR_MODULE.items():
        if column not in df.columns:
            continue
        if not _is_module_scored(row, column):
            continue
        for variant in canonical_lookup_keys(model_id):
            cache.add((variant, module_key))


def _is_module_scored(row: Any, column: str) -> bool:
    """True wenn Leaderboard-Zelle einen gültigen (non-Pending) Score enthält."""
    val = row.get(column)
    if val is None:
        return False
    val_str = str(val).strip()
    return bool(val_str) and val_str not in {"Pending", "–", "-", "nan"}


# =============================================================================
# EBENE 5: Registry-Helper (für run_score_benchmark.py)
# =============================================================================

def load_modules_for_keys(config: dict[str, Any], module_keys: list[str]) -> list[dict[str, Any]]:
    """Lädt Modul-Konfigurationen für die angegebenen Keys aus der Registry.

    SSOT-paritätisch mit benchmark_auto.py get_all_modules() und run_benchmark.py
    benchmark_info-Struktur.

    Args:
        config: Vollständige Config (von ConfigValidator)
        module_keys: Liste von Modul-Keys (z.B. ["cli_benchmark", "code_quality"])

    Returns:
        Liste von Modul-Konfigurationen im exakten Format von get_all_modules()
    """
    from utils.module_registry import get_active_modules

    active_modules = get_active_modules(config)
    modules_by_key = {key: (meta, internal) for key, meta, internal in active_modules}

    result: list[dict[str, Any]] = []
    for key in module_keys:
        if key not in modules_by_key:
            continue
        meta, internal = modules_by_key[key]

        # SSOT-paritätisch mit benchmark_auto.py get_all_modules()
        metadata = internal.get("metadata", {})
        execution = internal.get("execution", {})

        module_dict = {
            # Identität
            "id": key,
            "key": key,
            "name": metadata.get("name", meta.get("name", key)),
            "description": metadata.get("description", meta.get("description", "")),

            # Pfade
            "path": f"{meta['path']}/assets",
            "module_path": meta["path"],

            # Ausführung
            "test_class": execution.get("test_class", meta.get("test_class", "CodeQualityTest")),
            "execution_mode": execution.get("execution_mode", meta.get("execution_mode", "standard")),
            "min_runs": execution.get("min_runs", meta.get("min_runs", 1)),

            # Delegate/MCP (aus execution)
            "requires_mcp": execution.get("requires_mcp", False),
            "skip_if_card_false": execution.get("skip_if_card_false"),
            "delegate_script": execution.get("delegate_script"),
            "delegate_extra_args": execution.get("delegate_extra_args", []) or [],

            # Benchmarks/Scoring (aus internal_config)
            "benchmarks": internal.get("benchmarks", []),
            "scoring": internal.get("scoring", {}),
        }

        result.append(module_dict)

    return result
