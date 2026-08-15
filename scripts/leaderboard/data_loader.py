"""
Data loading and CSV parsing for leaderboard generation.
Handles reading commercial, local, and golden standard benchmark results.
"""

import csv
import logging
from pathlib import Path

import pandas as pd

# pylint: disable=import-error
from utils.csv_recovery import get_csv_header_idx, parse_row_robust

# pylint: enable=import-error

# Import configuration and constants
from .config import COMMERCIAL_CSV, LOCAL_CSV, CLOUD_CSV

# pylint: disable=import-error
try:
    from utils.model_utils import (
        get_model_category,
        resolve_canonical_model_id,
        resolve_model_cfg_for,
        strip_date_suffix,
    )
except ImportError:
    # Fallback if import fails (should match SSOT logic in model_utils.py)
    def get_model_category(
        model_name: str, source_file: str = "local", size_gb: float | None = None, provider: str | None = None
    ) -> str:
        """Fallback categorization matching SSOT."""
        if source_file == "commercial":
            return "Proprietär"
        return "Open Weights"

    def strip_date_suffix(model_id):  # type: ignore[no-redef]
        """Fallback: entfernt 8-stellige YYYYMMDD-Suffixe (kein MMDD-Strip)."""
        if not model_id:
            return model_id
        import re as _re
        return _re.sub(r"-\d{8}$", "", str(model_id))

    def resolve_canonical_model_id(model_id):  # type: ignore[no-redef]
        """Fallback: gibt die Eingabe zurück (kein Card-Lookup möglich)."""
        return model_id

    def resolve_model_cfg_for(model_id, config):  # type: ignore[no-redef]
        """Fallback: kein Config-Lookup möglich."""
        return None


# pylint: enable=import-error


logger = logging.getLogger(__name__)


def _extract_scores_from_df(df: pd.DataFrame) -> dict[str, float]:
    """Helper to extract latest scores per asset from a DataFrame."""
    refs = {}
    if "status" in df.columns:
        df = df[df["status"] == "success"]

    # Ensure timestamp
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.sort_values("timestamp")

    # Keep latest per asset_id
    if "asset_id" in df.columns and "percentage" in df.columns:
        latest = df.drop_duplicates(subset=["asset_id"], keep="last")
        for _, row in latest.iterrows():
            if pd.notna(row["percentage"]):
                refs[row["asset_id"]] = float(row["percentage"])
    return refs


def _resolve_source_context(type_label: str) -> str:
    """Mappe type_label aus dem CSV auf den Quell-Kontext für get_model_category."""
    if type_label == "Proprietär":
        return "commercial"
    if type_label == "Open Weights (Cloud)":
        return "cloud"
    return "local"


def _annotate_type_column(df_new: pd.DataFrame, type_label: str) -> pd.DataFrame:
    """Fügt source- und type-Spalten gemäß SSOT get_model_category() hinzu."""
    if "model" not in df_new.columns:
        df_new["type"] = type_label
        return df_new

    source_context = _resolve_source_context(type_label)
    df_new["source"] = source_context

    if "provider" in df_new.columns:
        df_new["type"] = df_new.apply(
            lambda row: get_model_category(
                row["model"], source_context, provider=row.get("provider")
            ),
            axis=1,
        )
    else:
        df_new["type"] = df_new["model"].apply(
            lambda m: get_model_category(m, source_context)
        )
    return df_new


def _process_csv(dfs: list[pd.DataFrame], filepath: Path, type_label: str) -> None:
    """
    Helper to process a single CSV File and append to list of DataFrames.

    Args:
        dfs: List to append the resulting DataFrame to.
        filepath: Path to the CSV file.
        type_label: Label for the 'type' column (e.g., 'Commercial', 'Local').
    """
    if not filepath.exists():
        return

    try:
        rows = []
        with open(filepath, encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                return

            header_idx = get_csv_header_idx(header)
            required = ["model", "asset_id", "percentage"]
            if not all(r in header_idx for r in required):
                return

            for parts in reader:
                row = parse_row_robust(parts, header_idx)
                if row:
                    rows.append(row)

        if rows:
            df_new = pd.DataFrame(rows)
            df_new = _annotate_type_column(df_new, type_label)
            dfs.append(df_new)
    except (OSError, csv.Error) as e:
        print(f"Error parsing {filepath}: {e}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        # Fallback for unexpected errors during manual parsing
        print(f"Unexpected error in {filepath}: {e}")


def _coerce_dataframe_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Numeric/Timestamp coercion und model_version-Default-Setzung.

    _process_csv() lädt via csv.reader + pd.DataFrame(rows) → alle Spalten sind
    str (object dtype). Nur explizit hier aufgeführte Spalten werden zu numeric
    coercet. Fehlt eine Spalte, führt pandas .sum()/.mean() auf str-Spalten zu
    String-Konkatenation statt arithmetischer Aggregation (Root Cause des
    Token-Overflow-Bugs: tokens_used wurde als str konkateniert statt summiert).
    """
    df["percentage"] = pd.to_numeric(df["percentage"], errors="coerce")
    df["execution_time"] = pd.to_numeric(df["execution_time"], errors="coerce")
    if "cost_usd" in df.columns:
        df["cost_usd"] = pd.to_numeric(df["cost_usd"], errors="coerce").fillna(0.0)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)

    # Numeric coercion for metric columns used in aggregations (.sum()/.mean()).
    # Without this, str columns get concatenated instead of summed.
    _numeric_cols = [
        "tokens_used",
        "tokens_per_second",
        "load_time",
        "response_length",
        "max_score",
        "total_score",
        "token_limit_used",
        "llm_judge_score",
        "llm_judge_latency_ms",
        "judge_task_compliance",
        "judge_output_quality",
        "judge_standard_adherence",
    ]
    for col in _numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # If model_version is missing (e.g. newly loaded CSV didn't have it yet), fill with "unknown"
    if "model_version" not in df.columns:
        df["model_version"] = "unknown"
    else:
        df["model_version"] = df["model_version"].fillna("unknown")
    return df


def _strip_date_suffixes(df: pd.DataFrame) -> pd.DataFrame:
    r"""Normalize model_version: Remove date suffix via SSoT `strip_date_suffix()`.
    SSoT unterstuetzt -YYYYMMDD (8-stellig) und -MMDD mit gueltigem Monat 01-12.
    Damit decken wir OpenRouter-Datesuffixes (z.B. kimi-k2-20260211) ab, die
    der alte regex -\d{4}-\d{2}-\d{2}$ nicht gefunden hat.
    """
    if "model_version" in df.columns:
        df["model_version"] = df["model_version"].astype(str).apply(strip_date_suffix)
    if "model" in df.columns:
        df["model"] = df["model"].astype(str).apply(strip_date_suffix)
    return df


def _load_config_or_none() -> dict | None:
    """Lädt die Config für card_model_id-Redirect (Dual-Thinking-Profile).
    Graceful degradation: ohne Config bleibt der Lookup wie bisher (kein Redirect).
    """
    try:
        from utils.config_validator import ConfigValidator  # noqa: PLC0415
        return ConfigValidator().config
    except Exception as exc:  # pylint: disable=broad-except
        logger.debug("ConfigValidator-Load fehlgeschlagen (Graceful Degradation): %s", exc)
        return None


def _build_card_version_map(df: pd.DataFrame, cfg: dict | None) -> dict[str, str]:
    """Iteriert über alle Modell-Cards und sammelt model_version-Overrides."""
    import json as _json_card  # noqa: PLC0415
    from utils.model_utils import _find_card as _find_model_card  # noqa: PLC0415
    _card_dir = Path(__file__).resolve().parents[2] / "benchmark_scores" / "model_cards"

    card_version_map: dict = {}
    for model_id in df["model"].unique():
        _model_cfg = resolve_model_cfg_for(str(model_id), cfg) if cfg else None
        card_path = _find_model_card(str(model_id), card_dir=_card_dir, model_cfg=_model_cfg)
        if card_path and card_path.exists():
            try:
                card = _json_card.loads(card_path.read_text(encoding="utf-8"))
                if isinstance(card, dict):
                    version = card.get("model_version")
                    if version and str(version).strip():
                        card_version_map[str(model_id)] = str(version).strip()
            except Exception:  # pylint: disable=broad-exception-caught
                pass
    return card_version_map


def _apply_card_version_overrides(df: pd.DataFrame) -> pd.DataFrame:
    """Model-Card-Normalisierung (SSoT) für model_id und model_version.
    1. model_id ueber resolve_canonical_model_id() aus SSoT. Macht Card-Lookup +
       Alias-Resolution (hf.co-Prefix-Strip, safe_name-Fallback). Damit ist die
       'model'-Spalte nach diesem Schritt garantiert in kanonischer Schreibweise.
    2. model_version-Override via Card-Lookup: ueberschreibt den Runtime-Wert
       mit dem Card-Wert (falls vorhanden).
    """
    if "model" not in df.columns:
        return df
    df["model"] = df["model"].astype(str).apply(resolve_canonical_model_id)

    cfg = _load_config_or_none()
    card_version_map = _build_card_version_map(df, cfg)
    if card_version_map:
        df["model_version"] = df.apply(
            lambda r: card_version_map.get(
                str(r["model"]), r.get("model_version", "unknown")
            ),
            axis=1,
        )
    return df


def load_benchmark_data() -> pd.DataFrame:
    """
    Loads and normalizes data from commercial and local CSVs.

    Returns:
        pd.DataFrame: Concatenated and deduplicated benchmark results.
                      Returns empty DataFrame if no data found.
    """
    dfs: list[pd.DataFrame] = []

    _process_csv(dfs, COMMERCIAL_CSV, "Proprietär")
    _process_csv(dfs, CLOUD_CSV, "Open Weights (Cloud)")
    _process_csv(dfs, LOCAL_CSV, "Open Weights (Local)")

    if not dfs:
        print("No benchmark data found.")
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)

    # Boundary: proprietäre Modelle dürfen nicht aus der local-CSV kommen.
    # Die früheren "Open Weights (Cloud)" / "Open Weights (Local)"-Filter wurden
    # entfernt — get_model_category() gibt seit der SSOT-Migration ausschließlich
    # "Open Weights" zurück (kein Suffix). Das source-Feld wird in _process_csv()
    # direkt aus dem CSV-Pfad gesetzt und ist daher bereits korrekt geroutet.
    df = df[
        (df["type"] != "Proprietär") | (df["source"].isin(["commercial", "cloud"]))
    ]

    # Drop spurious header-repetition rows (CSV written with header twice)
    if "model" in df.columns:
        df = df[df["model"] != "model"]

    df = _coerce_dataframe_metrics(df)

    # Sort by timestamp to ensure 'last' is actually the most recent
    df = df.sort_values("timestamp")

    df = _strip_date_suffixes(df)

    # --- DEDUPLICATION (Latest Run Only) ---
    # Crucial for accurate metrics (e.g. Load Time on new hardware):
    # We only want the LATEST run for each unique (model, version, asset).
    # Since df is already sorted by timestamp (asc), 'keep=last' preserves the most recent.
    if "asset_id" in df.columns:
        df = df.drop_duplicates(
            subset=["model", "model_version", "asset_id"], keep="last"
        )

    df = _apply_card_version_overrides(df)

    df = df.drop_duplicates(
        subset=["model", "model_version", "type", "asset_id"], keep="last"
    )
    return df
