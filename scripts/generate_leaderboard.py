#!/usr/bin/env python3
"""
Generiert ein Leaderboard aus den Benchmark-Ergebnissen.
Führt lokale und kommerzielle Ergebnisse zusammen und berechnet Durchschnittswerte.
"""

import csv
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Suppress FutureWarning about downcasting
pd.set_option('future.no_silent_downcasting', True)

# Pfad für Imports setzen
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from utils.config_validator import ConfigValidator  # noqa: E402
from utils.csv_recovery import parse_row_robust, get_csv_header_idx  # noqa: E402

# Konstanten
THRESHOLD_GOD_MODE_ROUTINE = 85
THRESHOLD_GOD_MODE_REASONING = 80
THRESHOLD_DAILY_DRIVER = 80
THRESHOLD_DEEP_THINKER = 80


# Konfiguration laden
validator = ConfigValidator()
config = validator.config
output_config = config.get('output', {})

SCORES_DIR = Path(output_config.get('directory', 'benchmark_scores'))
COMMERCIAL_CSV = Path(output_config.get('commercial_csv',
                                          SCORES_DIR /
                                          'commercial_models_benchmark.csv'))
LOCAL_CSV = Path(output_config.get('local_models_csv',
                                   SCORES_DIR / 'local_models_benchmark.csv'))
GOLDEN_CSV = Path(output_config.get('golden_standard_csv',
                                    SCORES_DIR /
                                    'golden_standard_benchmark.csv'))
OUTPUT_CSV = SCORES_DIR / "benchmark_leaderboard.csv"


def load_data() -> pd.DataFrame:
    """Lädt und normalisiert Daten aus allen CSVs"""
    dfs: List[pd.DataFrame] = []

    def process_csv(filepath: Path, type_label: str) -> None:
        if not filepath.exists():
            return

        try:
            rows = []
            with open(filepath, encoding='utf-8') as f:
                reader = csv.reader(f)
                try:
                    header = next(reader)
                except StopIteration:
                    return

                header_idx = get_csv_header_idx(header)
                required = ['model', 'asset_id', 'percentage']
                if not all(r in header_idx for r in required):
                    return

                for parts in reader:
                    row = parse_row_robust(parts, header_idx)
                    if row:
                        rows.append(row)

            if rows:
                df_new = pd.DataFrame(rows)
                df_new['type'] = type_label
                dfs.append(df_new)
        except (OSError, csv.Error) as e:
            print(f"Fehler beim Parsen von {filepath}: {e}")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Fallback für unerwartete Fehler beim manuellen Parsing
            print(f"Unerwarteter Fehler in {filepath}: {e}")

    process_csv(COMMERCIAL_CSV, 'Commercial')
    process_csv(LOCAL_CSV, 'Local')

    if not dfs:
        print("Keine Benchmark-Daten gefunden.")
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)
    df['percentage'] = pd.to_numeric(df['percentage'], errors='coerce')
    df['execution_time'] = pd.to_numeric(df['execution_time'], errors='coerce')
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    df = df.sort_values('timestamp')
    df = df.drop_duplicates(subset=['model', 'type', 'asset_id'], keep='last')
    return df


def _get_badge(row: pd.Series) -> str:
    """Ermittelt das Badge basierend auf den Scores."""
    routine = row.get('Routine Score', 0)
    reasoning = row.get('Reasoning Score', 0)

    if pd.isna(routine):
        routine = 0
    if pd.isna(reasoning):
        reasoning = 0

    is_god_mode = (
        reasoning > THRESHOLD_GOD_MODE_REASONING and
        routine > THRESHOLD_GOD_MODE_ROUTINE
    )

    if is_god_mode:
        return "👑 God Mode"
    if reasoning > THRESHOLD_DEEP_THINKER:
        return "🧠 Deep Thinker"
    if routine > THRESHOLD_DAILY_DRIVER:
        return "🏎️ Daily Driver"
    return "⚖️ Standard"


def _aggregate_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregiert Basis-Statistiken pro Modell."""
    total_unique_assets = df['asset_id'].nunique()
    stats = df.groupby(['model', 'type']).agg({
        'percentage': 'mean',
        'execution_time': 'mean',
        'asset_id': 'count'
    }).reset_index()

    stats['is_complete'] = stats['asset_id'] >= total_unique_assets
    stats['Tests Run'] = (stats['asset_id'].astype(str) + '/' +
                          str(total_unique_assets))
    return stats


def _calculate_tier_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Berechnet separate Statistik für Tier 1 und Tier 2."""
    if 'tier' not in df.columns:
        return pd.DataFrame()

    def get_tier_simple(t: Any) -> Optional[str]:
        s = str(t)
        if 'Tier 1' in s:
            return 'Tier 1'
        if 'Tier 2' in s:
            return 'Tier 2'
        return None

    df_copy = df.copy()
    df_copy['simple_tier'] = df_copy['tier'].apply(get_tier_simple)
    tier_means = df_copy.groupby(['model', 'simple_tier'])['percentage'] \
        .mean().unstack().reset_index()

    rename_map = {
        'Tier 1': 'Routine Score',
        'Tier 2': 'Reasoning Score'
    }
    return tier_means.rename(columns=rename_map)


def _finalize_result_df(
    result: pd.DataFrame,
    cat_stats: pd.DataFrame,
    modules_config: Dict[str, Any]
) -> Tuple[pd.DataFrame, List[str]]:
    """Finalisiert das Ergebnis-DataFrame (Umbenennen, Runden, Aufräumen)."""
    result = result.rename(columns={
        'percentage': 'Overall Score',
        'execution_time': 'Avg Time (s)',
        'type': 'Type',
    })
    result = result.sort_values('Overall Score', ascending=False)

    cols_to_round = [
        'Overall Score', 'Avg Time (s)', 'Routine Score',
        'Reasoning Score', 'Efficiency_Index'
    ]
    for col in cols_to_round:
        if col in result.columns:
            result[col] = result[col].round(2)

    cat_cols = []
    for mod_key, mod_data in modules_config.items():
        name = mod_data.get('name', mod_key)
        if name in result.columns:
            cat_cols.append(name)

    for col in result.columns:
        if col in cat_stats.columns and col not in cat_cols and col != 'model':
            cat_cols.append(col)

    for col in cat_cols:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors='coerce')
            result[col] = result[col].round(1).astype(object).fillna('Pending')

    return result, cat_cols


def calculate_metrics(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Berechnet Scores pro Modell inkl. Meta-Metriken"""
    modules_config = config.get('modules', {})
    df_success = df[df['status'] == 'success'].copy()

    # Kategorien zuweisen
    def get_category_name(asset_id: str) -> str:
        for mod_key, mod_data in modules_config.items():
            if asset_id.startswith(mod_key):
                return str(mod_data.get('name', mod_key))
        return 'Other'

    df_success['category'] = df_success['asset_id'].apply(get_category_name)
    
    # DEBUG
    print(f"DEBUG: Unique categories found: {df_success['category'].unique()}")
    print(f"DEBUG: Sample asset_ids: {df_success['asset_id'].head().tolist()}")
    
    # 1. Basis-Statistiken
    result = _aggregate_stats(df_success)

    # 2. Kategorie-Statistiken
    cat_stats = df_success.groupby(['model', 'category'])['percentage'] \
        .mean().unstack().reset_index()
    result = pd.merge(result, cat_stats, on='model', how='left')

    # Fehlende Modul-Spalten auffüllen (damit alle in der CSV erscheinen)
    for mod_key, mod_data in modules_config.items():
        name = mod_data.get('name', mod_key)
        if name not in result.columns:
            result[name] = float('nan')

    # 3. Tier-Statistiken (Routine/Reasoning)
    tier_stats = _calculate_tier_stats(df_success)
    if not tier_stats.empty:
        result = pd.merge(result, tier_stats, on='model', how='left')

    # Defaults und abgeleitete Metriken
    for col in ['Routine Score', 'Reasoning Score']:
        if col not in result.columns:
            result[col] = 0.0

    result['Efficiency_Index'] = result.apply(
        lambda row: row['Routine Score'] / row['execution_time']
        if row['execution_time'] > 0 else 0,
        axis=1
    )
    result['Badge'] = result.apply(_get_badge, axis=1)

    return _finalize_result_df(result, cat_stats, modules_config)


def assign_rank_and_badges(df: pd.DataFrame) -> pd.DataFrame:
    """Vergibt Empfehlungs-Badges (nur an vollständige Modelle)"""
    df['Recommendation'] = ''

    incomplete_mask = ~df['is_complete']
    if incomplete_mask.any():
        df.loc[incomplete_mask, 'model'] = \
            df.loc[incomplete_mask, 'model'] + ' *'
        df.loc[incomplete_mask, 'Recommendation'] = '(Pending)'

    complete_df = df[df['is_complete']]
    if complete_df.empty:
        return df

    # Best Commercial
    comm_mask = complete_df['Type'] == 'Commercial'
    if comm_mask.any():
        best_comm = complete_df.loc[comm_mask].sort_values(
            'Overall Score', ascending=False)
        if not best_comm.empty:
            best_model = best_comm.iloc[0]['model']
            idx = df[df['model'] == best_model].index[0]
            df.loc[idx, 'Recommendation'] = '🏆 Best Commercial'

    # Best Local
    local_mask = complete_df['Type'] == 'Local'
    if local_mask.any():
        best_local = complete_df.loc[local_mask].sort_values(
            'Overall Score', ascending=False)
        if not best_local.empty:
            best_model = best_local.iloc[0]['model']
            idx = df[df['model'] == best_model].index[0]
            current = df.loc[idx, 'Recommendation']
            df.loc[idx, 'Recommendation'] = f"{current} 🥇 Best Local".strip()

    return df


def print_leaderboard_table(leaderboard: pd.DataFrame) -> None:
    """Gibt das Leaderboard gruppiert nach Badges aus."""
    print("\n--- Benchmark Leaderboard ---\n")
    badges_order = [
        "👑 God Mode",
        "🏎️ Daily Driver",
        "🧠 Deep Thinker",
        "⚖️ Standard"
    ]
    display_fields = [
        'Rank', 'Model Name', 'Total Score', 'Avg Time (s)',
        'Routine Score', 'Reasoning Score'
    ]

    for badge in badges_order:
        group = leaderboard[leaderboard['Badge'] == badge]
        if not group.empty:
            print(f"=== {badge.upper()} ===")
            d_cols = [c for c in display_fields if c in group.columns]
            print(group[d_cols].to_string(index=False))
            print("")

    remaining = leaderboard[~leaderboard['Badge'].isin(badges_order)]
    if not remaining.empty:
        print("=== OTHER ===")
        d_cols = [c for c in display_fields if c in remaining.columns]
        print(remaining[d_cols].to_string(index=False))
        print("")

    if leaderboard['Model Name'].str.contains(r'\*').any():
        print("\n* Model has not completed all benchmarks "
              "(excluded from ranking badges).")


def main(print_table: bool = True) -> None:
    """Hauptfunktion für die Leaderboard-Generierung."""
    print("Generiere Leaderboard mit Meta-Metriken...")

    df = load_data()
    if df.empty:
        print("Keine Daten für Leaderboard vorhanden.")
        return

    leaderboard, cat_cols = calculate_metrics(df)

    # Sortieren und Rank
    leaderboard = leaderboard.reset_index(drop=True)
    leaderboard.index = leaderboard.index + 1
    leaderboard['Rank'] = leaderboard.index

    # Badges vergeben
    leaderboard = assign_rank_and_badges(leaderboard)

    # Rename model to Model Name for display
    leaderboard = leaderboard.rename(columns={'model': 'Model Name'})

    cols = ['Rank', 'Model Name', 'Total Score', 'Avg Time (s)',
            'Badge', 'Routine Score', 'Reasoning Score', 'Type']
    leaderboard = leaderboard.rename(columns={'Overall Score': 'Total Score'})

    # Spalten zusammenbauen
    final_cols = []
    # Core Columns
    for c in cols:
        if c in leaderboard.columns:
            final_cols.append(c)
    # Category Columns
    for c in cat_cols:
        if c in leaderboard.columns:
            final_cols.append(c)
    # Extra Columns
    for c in ['Tests Run', 'Recommendation']:
        if c in leaderboard.columns:
            final_cols.append(c)

    leaderboard = leaderboard[final_cols]
    leaderboard.to_csv(OUTPUT_CSV, index=False)
    print(f"Leaderboard gespeichert unter: {OUTPUT_CSV}")

    if print_table:
        print_leaderboard_table(leaderboard)


if __name__ == "__main__":
    main()
