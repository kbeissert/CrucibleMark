#!/usr/bin/env python3
"""
Generiert ein Leaderboard aus den Benchmark-Ergebnissen.
Führt lokale und kommerzielle Ergebnisse zusammen und berechnet Durchschnittswerte.
"""

import pandas as pd
from pathlib import Path
import sys

# Pfad für Imports setzen
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from utils.config_validator import ConfigValidator  # noqa: E402

# Konfiguration laden
validator = ConfigValidator()
config = validator.config
output_config = config.get('output', {})

SCORES_DIR = Path(output_config.get('directory', 'benchmark_scores'))
COMMERCIAL_CSV = Path(output_config.get('commercial_csv', SCORES_DIR / 'commercial_models_benchmark.csv'))
LOCAL_CSV = Path(output_config.get('local_models_csv', SCORES_DIR / 'local_models_benchmark.csv'))
GOLDEN_CSV = Path(output_config.get('golden_standard_csv', SCORES_DIR / 'golden_standard_benchmark.csv'))
OUTPUT_CSV = SCORES_DIR / "benchmark_leaderboard.csv"

def load_data():
    """Lädt und normalisiert Daten aus allen CSVs"""
    dfs = []
    
    # 1. Commercial Data
    if COMMERCIAL_CSV.exists():
        try:
            df_comm = pd.read_csv(COMMERCIAL_CSV)
            if not df_comm.empty:
                # Relevante Spalten auswählen und normalisieren
                if 'timestamp' not in df_comm.columns:
                    df_comm['timestamp'] = pd.Timestamp.now()
                df_comm = df_comm[['model', 'asset_id', 'percentage', 'execution_time', 'status', 'timestamp']]
                df_comm['type'] = 'Commercial'
                dfs.append(df_comm)
        except Exception as e:
            print(f"Warnung: Konnte {COMMERCIAL_CSV} nicht lesen: {e}")

    # 2. Local Data
    if LOCAL_CSV.exists():
        try:
            df_local = pd.read_csv(LOCAL_CSV)
            if not df_local.empty:
                # Relevante Spalten auswählen und normalisieren
                if 'timestamp' not in df_local.columns:
                    df_local['timestamp'] = pd.Timestamp.now()
                df_local = df_local[['model', 'asset_id', 'percentage', 'execution_time', 'status', 'timestamp']]
                df_local['type'] = 'Local'
                dfs.append(df_local)
        except Exception as e:
            print(f"Warnung: Konnte {LOCAL_CSV} nicht lesen: {e}")

    # 3. Golden Standard Data (Excluded from Leaderboard)
    # if GOLDEN_CSV.exists():
    #     try:
    #         df_golden = pd.read_csv(GOLDEN_CSV)
    #         if not df_golden.empty:
    #             # Relevante Spalten auswählen und normalisieren
    #             if 'timestamp' not in df_golden.columns:
    #                 df_golden['timestamp'] = pd.Timestamp.now()
    #             df_golden = df_golden[['model', 'asset_id', 'percentage', 'execution_time', 'status', 'timestamp']]
    #             df_golden['type'] = 'Golden Standard'
    #             dfs.append(df_golden)
    #     except Exception as e:
    #         print(f"Warnung: Konnte {GOLDEN_CSV} nicht lesen: {e}")
            
    if not dfs:
        print("Keine Benchmark-Daten gefunden.")
        sys.exit(1)
        
    df = pd.concat(dfs, ignore_index=True)
    
    # Datentypen erzwingen
    df['percentage'] = pd.to_numeric(df['percentage'], errors='coerce')
    df['execution_time'] = pd.to_numeric(df['execution_time'], errors='coerce')
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    # Duplikate entfernen (nur den neuesten Run pro Asset behalten)
    # Sortieren nach Timestamp, dann Drop Duplicates
    df = df.sort_values('timestamp')
    df = df.drop_duplicates(subset=['model', 'type', 'asset_id'], keep='last')
    
    return df

def calculate_metrics(df):
    """Berechnet Scores pro Modell"""
    # Gesamtanzahl einzigartiger Assets im Datensatz ermitteln (als Referenz für "Vollständigkeit")
    total_unique_assets = df['asset_id'].nunique()
    
    # Nur erfolgreiche Runs werten
    df = df[df['status'] == 'success'].copy()
    
    # Kategorien identifizieren
    df['category'] = df['asset_id'].apply(lambda x: 'Code Quality' if 'code_quality' in x else 'UX Writing')
    
    # Aggregation
    stats = df.groupby(['model', 'type']).agg({
        'percentage': 'mean',
        'execution_time': 'mean',
        'asset_id': 'count'  # Anzahl der Tests
    }).reset_index()
    
    # Vollständigkeit prüfen
    stats['is_complete'] = stats['asset_id'] >= total_unique_assets
    stats['Tests Run'] = stats['asset_id'].astype(str) + '/' + str(total_unique_assets)
    
    # Kategorie-Scores berechnen (ohne fill_value=0, um fehlende Tests zu erkennen)
    cat_stats = df.groupby(['model', 'category'])['percentage'].mean().unstack().reset_index()
    
    # Zusammenführen
    result = pd.merge(stats, cat_stats, on='model', how='left')
    
    # Spalten umbenennen und formatieren
    result = result.rename(columns={
        'percentage': 'Overall Score',
        'execution_time': 'Avg Time (s)'
    })
    
    # Runden der Haupt-Metriken
    for col in ['Overall Score', 'Avg Time (s)']:
        if col in result.columns:
            result[col] = result[col].round(1)

    # Kategorie-Spalten formatieren (NaN -> Pending)
    cat_cols = ['Code Quality', 'UX Writing']
    for col in cat_cols:
        if col in result.columns:
            # Erst runden, dann NaN durch 'Pending' ersetzen
            result[col] = result[col].round(1).fillna('Pending')
            
    return result

def assign_badges(df):
    """Vergibt Empfehlungs-Badges (nur an vollständige Modelle)"""
    df['Recommendation'] = ''
    
    # Markiere unvollständige Modelle
    incomplete_mask = ~df['is_complete']
    if incomplete_mask.any():
        df.loc[incomplete_mask, 'model'] = df.loc[incomplete_mask, 'model'] + ' *'
        df.loc[incomplete_mask, 'Recommendation'] = '(Incomplete)'
    
    # Nur vollständige Modelle für Badges berücksichtigen
    complete_df = df[df['is_complete']]
    
    if complete_df.empty:
        return df
        
    # Best Commercial
    comm_mask = complete_df['type'] == 'Commercial'
    if comm_mask.any():
        # Finde den Index im Original-DataFrame
        best_comm_model = complete_df.loc[comm_mask].sort_values('Overall Score', ascending=False).iloc[0]['model']
        idx = df[df['model'] == best_comm_model].index[0]
        df.loc[idx, 'Recommendation'] = '🏆 Best Commercial'
        
    # Best Local
    local_mask = complete_df['type'] == 'Local'
    if local_mask.any():
        best_local_model = complete_df.loc[local_mask].sort_values('Overall Score', ascending=False).iloc[0]['model']
        idx = df[df['model'] == best_local_model].index[0]
        
        current = df.loc[idx, 'Recommendation']
        df.loc[idx, 'Recommendation'] = f"{current} 🥇 Best Local".strip()
        
    # Efficiency Star (Schnellstes Modell mit Score > 80)
    good_models = complete_df[complete_df['Overall Score'] > 80]
    if not good_models.empty:
        fastest_model = good_models.sort_values('Avg Time (s)', ascending=True).iloc[0]['model']
        idx = df[df['model'] == fastest_model].index[0]
        
        current = df.loc[idx, 'Recommendation']
        # if "Best" not in current: # Nur wenn nicht schon Hauptgewinner
        df.loc[idx, 'Recommendation'] = f"{current} ⚡ Efficient".strip()
            
    return df

def main(print_table=True):
    print("Generiere Leaderboard...")
    
    # Daten laden
    df = load_data()
    
    # Metriken berechnen
    leaderboard = calculate_metrics(df)
    
    # Sortieren
    leaderboard = leaderboard.sort_values('Overall Score', ascending=False)
    
    # Badges vergeben
    leaderboard = assign_badges(leaderboard)
    
    # Spalten ordnen
    cols = ['Recommendation', 'model', 'type', 'Overall Score', 'Code Quality', 'UX Writing', 'Avg Time (s)', 'Tests Run']
    # Sicherstellen, dass alle Spalten existieren (falls z.B. UX Writing fehlt)
    cols = [c for c in cols if c in leaderboard.columns]
    leaderboard = leaderboard[cols]
    
    # Speichern
    leaderboard.to_csv(OUTPUT_CSV, index=False)
    print(f"Leaderboard gespeichert unter: {OUTPUT_CSV}")
    
    if print_table:
        # Vorschau in Konsole
        print("\n--- Benchmark Leaderboard ---")
        print(leaderboard.to_string(index=False))
        
        # Hinweis auf unvollständige Modelle
        if leaderboard['model'].str.contains('\*').any():
            print("\n* Model has not completed all benchmarks (excluded from ranking badges).")

if __name__ == "__main__":
    main()
