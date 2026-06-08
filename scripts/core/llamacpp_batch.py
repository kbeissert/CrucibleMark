"""
Gemeinsame llama.cpp-Batch-Orchestrierung für benchmark_auto.py und run_score_benchmark.py.

Zweiteilige Architektur:
- Lifecycle-Helper: Server-Start/Stop/Cleanup, Provider-Kontext
- Context-Manager: Sichere Session-Verwaltung mit Exception-basierter Fehlerbehandlung
- Cache-Helper: Existing-Results und Asset-Ermittlung

Der Modul-Executor wird als Callback übergeben, damit der Aufrufer die volle
Kontrolle über Modulfilter, Asset-Ermittlung, Delegation und Fehlerpolitik behält.
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set, Tuple
import re
import subprocess
import time
import json
import yaml
import os
import pandas as pd

# ROOT_DIR für absolute Pfade
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Konstante für Socket-Release-Zeit nach Server-Stop
LLAMACPP_STOP_SETTLE_SEC: int = 3


# =============================================================================
# EXCEPTIONS
# =============================================================================

class LlamaCppSessionError(Exception):
    """Fehler beim Starten oder Verwalten einer llama.cpp-Server-Session."""
    pass


# =============================================================================
# EBENE 1: Lifecycle-Helper (keine Benchmark-Logik)
# =============================================================================

def is_llamacpp_provider(provider_key: str) -> bool:
    """Returns True for local llama.cpp-style provider aliases."""
    return provider_key in {"llamacpp", "llamacpp_spark", "llama_cpp", "llamacpp_local"}


def get_enabled_llamacpp_providers(config: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    """Returns enabled local llama.cpp-style providers in config order."""
    local_cfg = config.get("providers", {}).get("local", {})
    enabled: List[Tuple[str, Dict[str, Any]]] = []
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
    config: Dict[str, Any],
    provider_key: Optional[str] = None,
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
    seen_cmds: Set[str] = set()
    for _pkey, provider_cfg in enabled_llamacpp:
        stop_cmd = str(provider_cfg.get("server_stop_cmd", "pkill -f llama-server")).strip()
        if not stop_cmd or stop_cmd in seen_cmds:
            continue
        seen_cmds.add(stop_cmd)
        subprocess.run(stop_cmd, shell=True, check=False, capture_output=True)

    time.sleep(LLAMACPP_STOP_SETTLE_SEC)


def run_llamacpp_provider_cleanup(provider_key: str, provider_cfg: Dict[str, Any]) -> None:
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
    provider_cfg: Dict[str, Any],
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
) -> Set[Tuple[str, str]]:
    """Lädt Set von (Model, AssetID) für bereits existierende Tests.
    
    Berücksichtigt alle drei Haupt-CSVs (local, cloud, commercial)
    sowie Political Compass Leaderboard.
    
    Args:
        csv_path: Pfad zur primären CSV-Datei (wird ignoriert wenn force=True)
        force: Wenn True, leeres Set zurückgeben (Cache ignorieren)
    
    Returns:
        Set von (model_id, asset_id) Tupeln
    """
    import pandas as pd
    from utils.model_utils import normalize_model_id
    from utils.config_validator import ConfigValidator
    
    cache: Set[Tuple[str, str]] = set()
    if force:
        return cache

    # ConfigValidator ist verpflichtend (kein defensiver Fallback)
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
            _add_existing_result_rows(cache, df)
        except Exception as e:
            print(f"⚠️ Warnung beim Lesen von {path}: {e}")

    # Political Compass Leaderboard
    pc_csv = ROOT_DIR / "benchmark_scores" / "political_compass_leaderboard.csv"
    if pc_csv.exists():
        try:
            df_pc = pd.read_csv(pc_csv)
            _add_political_compass_rows(cache, df_pc)
        except Exception as e:
            print(f"⚠️ Warnung beim Lesen von {pc_csv}: {e}")

    return cache


def _add_existing_result_rows(cache: Set[Tuple[str, str]], df: Any) -> None:
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

        model_str = str(row["model"])
        asset_str = str(row["asset_id"])
        for variant in canonical_lookup_keys(model_str):
            cache.add((variant, asset_str))


def _add_political_compass_rows(cache: Set[Tuple[str, str]], df: Any) -> None:
    """Adds political-compass leaderboard rows to the cache using the batch ID.

    Multi-Key: alle kanonischen Lookup-Varianten des Modellnamens werden
    gecacht, damit der Cache-Lookup unabhängig von der Schreibweise des
    Callers funktioniert.
    """
    if "model" not in df.columns:
        return

    for _, row in df.iterrows():
        model_str = str(row["model"])
        for variant in canonical_lookup_keys(model_str):
            cache.add((variant, "political_compass_v3"))


def canonical_lookup_keys(model: Any) -> Set[str]:
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

    variants: Set[str] = set()
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
    module: Dict[str, Any],
    model: str,
    existing_tests: Set[Tuple[str, str]],
) -> List[Path]:
    """Ermittelt Asset-Pfade, die für dieses Modell noch nicht getestet wurden.
    
    VOLLSTÄNDIGE Version mit:
    - skip_if_card_false (Tool-Use-Card-State)
    - Batch-Module-Sonderbehandlung (political_compass)
    - YAML-Parsing und Cache-Check
    
    Args:
        module: Modul-Konfiguration (mit 'path', 'key', 'skip_if_card_false')
        model: Modell-ID
        existing_tests: Cache von (model, asset_id) Tupeln (aus get_existing_results)
    
    Returns:
        Liste der zu testenden Asset-Pfade (leer wenn übersprungen oder vorhanden)
    """
    from utils.model_utils import (
        normalize_model_id,
        normalize_supports_tool_use,
        strip_date_suffix,
        SUPPORT_TOOL_USE_UNTESTED,
        _find_card as _fc,
    )
    
    assets_path = module.get("path", "")
    if not assets_path:
        return []
    
    # -------------------------------------------------------
    # CARD-BASED SKIP (skip_if_card_false)
    # -------------------------------------------------------
    skip_card_key = module.get("skip_if_card_false")
    if skip_card_key:
        card_dir = ROOT_DIR / "benchmark_scores" / "model_cards"
        card_path = _fc(model, card_dir=card_dir)
        if card_path.exists():
            try:
                card = json.loads(card_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
            else:
                raw_val = card.get(skip_card_key)
                norm_val = normalize_supports_tool_use(raw_val)
                
                # Fall 1: Modell kann KEINE Tools → SKIP
                if norm_val is False or raw_val == "not_applicable":
                    reason = "not_applicable" if raw_val == "not_applicable" else "false"
                    print(f"   ⏩ Bench: {module.get('name', module.get('key'))} ({skip_card_key}={reason} in Card — übersprungen)")
                    return []
                
                # Fall 2: "untested" → Test ausführen (nicht skippen)
                # Fall 3: true ("tested") → weiter zum normalen Cache-Check
    
    # -------------------------------------------------------
    # SPECIAL HANDLING FOR BATCH MODULES (e.g. Political Compass)
    # -------------------------------------------------------
    if module.get("execution_mode") == "batch" or module.get("key") == "political_compass":
        batch_id = "political_compass_v3"
        if any(
            (variant, batch_id) in existing_tests
            for variant in canonical_lookup_keys(model)
        ):
            return []

    # -------------------------------------------------------
    # ASSET-DATEIEN ERMITTELN
    # -------------------------------------------------------
    p = Path(assets_path)
    if not p.exists():
        return []

    asset_files = sorted(list(p.glob("*.yaml")))
    if not asset_files:
        return []

    assets_todo = []
    for asset_f in asset_files:
        try:
            with open(asset_f, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                asset_id = data.get("metadata", {}).get("id")

            if not asset_id:
                assets_todo.append(asset_f)
                continue

            if any(
                (variant, asset_id) in existing_tests
                for variant in canonical_lookup_keys(model)
            ):
                continue

            assets_todo.append(asset_f)
        except (OSError, yaml.YAMLError):
            assets_todo.append(asset_f)

    return assets_todo


# =============================================================================
# EBENE 4b: Leaderboard-Cache (zweite Verteidigungslinie)
# =============================================================================

# Mapping module-key → Spalte in benchmark_leaderboard.csv
LEADERBOARD_COLUMN_FOR_MODULE: Dict[str, str] = {
    "code_quality": "Code Quality Audit",
    "cli_benchmark": "CLI Badge",
    "reasoning_logic": "Logical Reasoning",
    "ux_writing": "UX Writing & Microcopy",
    "documentation_quality": "Documentation Quality",
    "content_transformation": "Content Transformation & Adaption",
    "cultural_intelligence": "Cultural Intelligence",
}


def get_leaderboard_scored_modules(
    leaderboard_path: Optional[Path] = None,
    force: bool = False,
) -> Set[Tuple[str, str]]:
    """Lädt Set von (model_id, module_key) für Modelle/Module mit gültigem Leaderboard-Score.

    Zweite Verteidigungslinie gegen veraltete Score-CSVs: wenn das Leaderboard
    für ein (Modell, Modul)-Paar einen non-Pending Score zeigt, soll das Auto-
    Skript keinen Subprozess starten, auch wenn die Detail-CSV Inkonsistenzen
    enthält.

    Args:
        leaderboard_path: Pfad zu benchmark_leaderboard.csv (Default: ROOT_DIR/benchmark_scores/)
        force: Wenn True, leeres Set zurückgeben

    Returns:
        Set von (model_id, module_key) Tupeln mit gültigem Score
    """
    cache: Set[Tuple[str, str]] = set()
    if force:
        return cache

    if leaderboard_path is None:
        leaderboard_path = ROOT_DIR / "benchmark_scores" / "benchmark_leaderboard.csv"
    if not leaderboard_path.exists():
        return cache

    try:
        df = pd.read_csv(leaderboard_path)
    except Exception:  # pylint: disable=broad-exception-caught
        return cache

    if "Model ID" not in df.columns:
        return cache

    for _, row in df.iterrows():
        model_id_raw = row.get("Model ID", "")
        if pd.isna(model_id_raw):
            continue
        model_id = str(model_id_raw).strip()
        if not model_id or model_id.lower() == "nan":
            continue
        for module_key, column in LEADERBOARD_COLUMN_FOR_MODULE.items():
            if column not in df.columns:
                continue
            val = row.get(column)
            if val is None:
                continue
            val_str = str(val).strip()
            # Pending, Em-Dash, leer, NaN → nicht gescored
            if not val_str or val_str in {"Pending", "–", "-", "nan"}:
                continue
            # Multi-Key: jede kanonische Lookup-Variante cachen
            for variant in canonical_lookup_keys(model_id):
                cache.add((variant, module_key))

    return cache


# =============================================================================
# EBENE 5: Registry-Helper (für run_score_benchmark.py)
# =============================================================================

def load_modules_for_keys(config: Dict[str, Any], module_keys: List[str]) -> List[Dict[str, Any]]:
    """Lädt Modul-Konfigurationen für die angegebenen Keys aus der Registry.
    
    SSOT-paritätisch mit benchmark_auto.py get_all_modules() und run_benchmark.py
    benchmark_info-Struktur.
    
    Args:
        config: Vollständige Config (von ConfigValidator)
        module_keys: Liste von Modul-Keys (z.B. ["cli_benchmark", "code_quality"])
    
    Returns:
        Liste von Modul-Konfigurationen im exakten Format von get_all_modules()
    """
    from utils.module_registry import get_active_modules, load_module_config
    
    active_modules = get_active_modules(config)
    modules_by_key = {key: (meta, internal) for key, meta, internal in active_modules}
    
    result: List[Dict[str, Any]] = []
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