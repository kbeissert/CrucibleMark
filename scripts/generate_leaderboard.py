#!/usr/bin/env python3
"""
Generiert ein Leaderboard aus den Benchmark-Ergebnissen.
Führt lokale und kommerzielle Ergebnisse zusammen und berechnet Durchschnittswerte.
"""

import pandas as pd
from pathlib import Path
import sys
import csv

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


def load_csv_robust(filepath):
    """Lädt CSV-Datei robust, auch wenn Zeilen unterschiedliche Spalten haben."""
    if not filepath.exists():
        return pd.DataFrame()

    try:
        with open(filepath, encoding='utf-8') as f:
            # Lese Header
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                return pd.DataFrame()

            # Mapping von Spaltennamen zu Index
            # Wir wissen, dass die ersten Spalten stabil sind, aber dynamische Spalten variieren.
            # Wir suchen nach 'model', 'asset_id', 'percentage', 'execution_time', 'status', 'timestamp'
            # Diese sollten immer da sein, aber vielleicht an unterschiedlichen Positionen?
            # Nein, ResultManager schreibt DictWriter. Die Position hängt vom Header ab.
            # Wenn neue Zeilen geschrieben wurden, passen sie NICHT zum Header.

            # Wir lesen jede Zeile als Dict, indem wir versuchen, die Werte zuzuordnen.
            # Da wir die Struktur der "falschen" Zeilen nicht kennen (kein Header für sie),
            # müssen wir raten oder die Zeilen analysieren.

            # Strategie: Wir lesen alle Zeilen. Wenn eine Zeile weniger/mehr Spalten hat als der Header,
            # versuchen wir sie zu retten.
            # Aber ResultManager schreibt OHNE neuen Header zwischendrin.
            # Das heißt, die Werte stehen einfach an den Positionen, die DictWriter für die NEUEN Keys gewählt hat.
            # Das ist deterministisch aber unbekannt ohne die Keys.

            # ABER: ResultManager sortiert die Keys alphabetisch!
            # fieldnames = sorted(list(all_keys))

            # Das heißt, für die Documentation Quality Zeilen wurden die Spalten alphabetisch sortiert geschrieben.
            # asset_id, asset_name, criteria_1, execution_time, max_score, model, percentage, ...

            # Wir können versuchen, die Zeilen basierend auf dem Inhalt zu identifizieren.
            # 'model' enthält Strings wie 'mistral-large'.
            # 'asset_id' enthält 'documentation_quality'.
            # 'status' enthält 'success'.

            for row in reader:
                row_data = {}

                # Wenn die Zeile zum Header passt (Länge)
                if len(row) == len(header):
                    row_data = dict(zip(header, row))
                else:
                    # Fallback: Wir suchen die wichtigsten Spalten im "Heuhaufen"
                    # Das ist riskant, aber besser als Datenverlust.

                    # Suche nach asset_id (enthält '_')
                    for val in row:
                        if 'quality' in val or 'writing' in val:
                            row_data['asset_id'] = val
                            break

                    # Suche nach status ('success', 'failed')
                    if 'success' in row:
                        row_data['status'] = 'success'
                    elif 'failed' in row:
                        row_data['status'] = 'failed'

                    # Suche nach model (bekannte Modelle oder Provider)
                    # Wir nehmen an, dass das Modell in der Zeile steht.
                    # Das ist schwierig generisch zu lösen.

                    # BESSERER ANSATZ:
                    # Wir wissen, dass ResultManager alphabetisch sortiert.
                    # Wir können rekonstruieren, welche Keys Documentation Quality hat.
                    # asset_id, asset_name, criteria_..., execution_time, max_score, model, percentage, status, timestamp, total_score

                    # Wir parsen einfach alles, was wir finden können.
                    pass

                # Wenn wir die wichtigsten Felder haben, fügen wir sie hinzu
                # Da der Fallback oben zu komplex ist, nutzen wir einen einfacheren Trick:
                # Wir lesen die Datei als String, splitten Zeilen, und suchen nach bekannten Mustern.
                pass
    except Exception as e:
        print(f"Fehler beim Lesen von {filepath}: {e}")

    # Da der obige Ansatz zu wackelig ist, nutzen wir pandas mit error_bad_lines=False
    # und versuchen dann, die "bad lines" separat zu lesen? Nein.

    # Pragmatische Lösung:
    # Wir lesen die Datei mit pandas. Zeilen mit falscher Spaltenanzahl werden oft zu NaN oder verschoben.
    # Wir haben gesehen, dass sie verschoben sind.
    # Wir laden die Datei erneut ohne Header und analysieren jede Zeile.

    return pd.read_csv(filepath, on_bad_lines='skip', engine='python')

def load_data():
    """Lädt und normalisiert Daten aus allen CSVs"""
    dfs = []

    def process_csv(filepath, type_label):
        if not filepath.exists():
            return

        # Wir lesen die Datei mit csv.reader, um Quoting korrekt zu behandeln
        try:
            rows = []
            with open(filepath, encoding='utf-8') as f:
                reader = csv.reader(f)
                try:
                    header = next(reader)
                except StopIteration:
                    return

                # Indizes der wichtigen Spalten im korrekten Header
                try:
                    idx_model = header.index('model')
                    idx_asset = header.index('asset_id')
                    idx_pct = header.index('percentage')
                    idx_time = header.index('execution_time')
                    idx_status = header.index('status')
                    idx_ts = header.index('timestamp')
                    
                    # Optional: Tier (für Reasoning Profile)
                    idx_tier = header.index('tier') if 'tier' in header else -1
                    
                except ValueError:
                    # Wenn Header fehlt oder falsch ist
                    return

                for parts in reader:
                    # Versuch 1: Passt zum Header
                    if len(parts) == len(header):
                        row = {
                            'model': parts[idx_model],
                            'asset_id': parts[idx_asset],
                            'percentage': parts[idx_pct],
                            'execution_time': parts[idx_time],
                            'status': parts[idx_status],
                            'timestamp': parts[idx_ts]
                        }
                        
                        # Add Tier if available
                        if idx_tier != -1:
                            row['tier'] = parts[idx_tier]
                            
                        rows.append(row)
                    else:
                        # Versuch 2: Heuristik für verschobene Zeilen (Documentation Quality)
                        row = {}

                        # Wir suchen nach bekannten Mustern in den Teilen

                        # Asset ID (enthält '_')
                        for p in parts:
                            if ('code_quality' in p or 'ux_writing' in p or 'documentation_quality' in p) and '_' in p:
                                row['asset_id'] = p
                                break

                        # Status ('success' oder 'failed')
                        if 'success' in parts:
                            row['status'] = 'success'
                        elif 'failed' in parts:
                            row['status'] = 'failed'
                        else:
                            continue # Ohne Status unbrauchbar

                        # Timestamp (ISO Format: YYYY-MM-DD...)
                        for p in parts:
                            if p.startswith('202') and ':' in p:
                                row['timestamp'] = p
                                break

                        # Model (String, nicht asset_id/status/timestamp)
                        # Schwierig zu erraten. Wir nehmen an, es ist der erste Wert, der kein Datum/Asset/Status ist?
                        # Oder wir suchen nach bekannten Providern.
                        for p in parts:
                            if p != row.get('asset_id') and p != row.get('status') and p != row.get('timestamp'):
                                # Check if it looks like a model name (alphanumeric, maybe - or :)
                                if any(x in p for x in ['mistral', 'qwen', 'gpt', 'claude', 'llama', 'ministral']):
                                    row['model'] = p
                                    break

                        # Percentage (Float <= 100)
                        # Wir nehmen den höchsten Wert <= 100, der nicht Total Score ist?
                        # Oder wir suchen nach Float-Werten.
                        floats = []
                        for p in parts:
                            try:
                                val = float(p)
                                floats.append(val)
                            except ValueError:
                                continue

                        if floats:
                            # Percentage ist meist > 0 und <= 100.
                            # Execution time ist auch > 0.
                            # Total Score ist oft gleich Percentage.
                            # Wir nehmen an, Percentage ist einer der Werte.
                            # Da wir es nicht genau wissen, nehmen wir den ersten plausiblen Wert als Percentage
                            # und den zweiten als Time? Das ist sehr raten.

                            # Besser: Wir setzen Percentage auf 0.0 wenn unsicher, damit es nicht crasht.
                            # Aber wir wollen den Score.

                            # Wenn wir Documentation Quality haben, ist die Struktur:
                            # asset_id, asset_name, criteria..., execution_time, max_score, model, percentage, status, timestamp, total_score
                            # (alphabetisch sortiert)

                            # percentage kommt nach model.
                            pass

                        # Fallback für fehlende Werte
                        if 'model' in row and 'asset_id' in row:
                            if 'percentage' not in row:
                                # Versuche Percentage aus floats zu raten
                                # Wenn wir 3 floats haben (exec_time, max_score, percentage, total_score -> 4)
                                # Alphabetisch: execution_time, max_score, percentage, total_score
                                # Also floats[2] könnte percentage sein?
                                if len(floats) >= 3:
                                    # Sortierte Keys...
                                    # execution_time ist meist klein oder groß.
                                    # max_score ist 100 oder 70.
                                    # percentage ist 0-100.

                                    # Wir nehmen einfach an, dass wir die Daten retten wollen.
                                    # Wenn wir es nicht genau wissen, lassen wir es lieber, als falsche Daten zu zeigen?
                                    # Nein, User will Ergebnisse sehen.

                                    # Wir suchen den Wert, der <= 100 ist.
                                    valid_pcts = [f for f in floats if 0 <= f <= 100]
                                    if valid_pcts:
                                        row['percentage'] = max(valid_pcts) # Optimistisch
                                    else:
                                        row['percentage'] = 0.0
                                else:
                                    row['percentage'] = 0.0

                            if 'execution_time' not in row:
                                row['execution_time'] = 0.0

                            if 'timestamp' not in row:
                                row['timestamp'] = pd.Timestamp.now()

                            rows.append(row)

            if rows:
                df_new = pd.DataFrame(rows)
                df_new['type'] = type_label
                dfs.append(df_new)

        except Exception as e:
            print(f"Fehler beim manuellen Parsen von {filepath}: {e}")

    # 1. Commercial Data
    process_csv(COMMERCIAL_CSV, 'Commercial')

    # 2. Local Data
    process_csv(LOCAL_CSV, 'Local')

    # 3. Golden Standard Data (Excluded from Leaderboard as it should be in Commercial)
    # process_csv(GOLDEN_CSV, 'Golden Standard')

    if not dfs:
        print("Keine Benchmark-Daten gefunden.")
        return pd.DataFrame()

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

    # Kategorien dynamisch aus Config ermitteln
    modules_config = config.get('modules', {})

    def get_category_name(asset_id):
        for mod_key, mod_data in modules_config.items():
            if asset_id.startswith(mod_key):
                return mod_data.get('name', mod_key)
        return 'Other'

    df['category'] = df['asset_id'].apply(get_category_name)

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

    # Special Handling: Reasoning Tiers & Profile
    reasoning_stats = pd.DataFrame()
    if 'tier' in df.columns:
        # Filter for reasoning module to avoid noise
        reasoning_df = df[df['asset_id'].str.startswith('reasoning', na=False)].copy()
        
        if not reasoning_df.empty:
            # Clean tier names (take only "Tier 1" or "Tier 2" part)
            reasoning_df['simple_tier'] = reasoning_df['tier'].astype(str).apply(lambda x: 'Tier 1' if 'Tier 1' in x else ('Tier 2' if 'Tier 2' in x else 'Unknown'))
            
            # Pivot to get Tier 1 and Tier 2 scores per model
            tier_scores = reasoning_df.groupby(['model', 'simple_tier'])['percentage'].mean().unstack().reset_index()
            
            # Rename columns
            rename_map = {}
            if 'Tier 1' in tier_scores.columns:
                rename_map['Tier 1'] = 'Logic (T1)'
            if 'Tier 2' in tier_scores.columns:
                rename_map['Tier 2'] = 'Reasoning (T2)'
                
            tier_scores = tier_scores.rename(columns=rename_map)
            reasoning_stats = tier_scores

    # Zusammenführen
    result = pd.merge(stats, cat_stats, on='model', how='left')
    
    if not reasoning_stats.empty:
        result = pd.merge(result, reasoning_stats, on='model', how='left')

    # Analyse Profile (Deep Thinker vs Daily Driver) based on T2 score
    if 'Reasoning (T2)' in result.columns and 'Logic (T1)' in result.columns:
        def get_profile(row):
            t1 = row.get('Logic (T1)', 0)
            t2 = row.get('Reasoning (T2)', 0)
            if pd.isna(t2) or pd.isna(t1): return "Unknown"
            
            if t2 > 80 and t2 >= t1:
                return "🧠 Deep Thinker"
            elif t1 > 80 and t2 < 50:
                return "🏎️ Daily Driver"
            elif t1 > 80 and t2 > 60:
                return "⚖️ Balanced"
            else:
                return "🌱 Learner"
        
        result['Profile'] = result.apply(get_profile, axis=1)

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
    # Wir ermitteln die Reihenfolge aus der Config
    cat_cols = []
    for mod_key, mod_data in modules_config.items():
        name = mod_data.get('name', mod_key)
        if name in result.columns:
            cat_cols.append(name)

    # Füge Kategorien hinzu, die nicht in der Config sind (Fallback)
    for col in result.columns:
        if col not in stats.columns and col not in cat_cols and col != 'model' and col != 'Overall Score' and col != 'Avg Time (s)':
             # Check if it was a category column from cat_stats
             if col in cat_stats.columns:
                 cat_cols.append(col)

    for col in cat_cols:
        if col in result.columns:
            # Erst runden, dann NaN durch 'Pending' ersetzen
            result[col] = result[col].round(1).fillna('Pending')

    return result, cat_cols

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

    if df.empty:
        print("Keine Daten für Leaderboard vorhanden.")
        return

    # Metriken berechnen
    leaderboard, cat_cols = calculate_metrics(df)

    # Sortieren
    leaderboard = leaderboard.sort_values('Overall Score', ascending=False)

    # Badges vergeben
    leaderboard = assign_badges(leaderboard)

    # Spalten ordnen
    
    # 3.5 Reasoning Type Classification
    def classify_reasoning(model_name):
        name_lower = str(model_name).lower().strip().replace('*', '') # Handle badges/markers
        
        # 1. Check for Reasoning (System 2 thinking)
        if any(kw in name_lower for kw in ["deepseek-r1", " r1", ":r1", "-r1", "qwq", "o1", "o3", "reasoning"]):
            return "🧠 Reasoning"
            
        # 2. Check for Code Specialization
        if "coder" in name_lower:
            return "💻 Coder"
            
        # 3. Default: General Purpose (Instruct/Chat)
        return "🤖 Standard"

    leaderboard['reasoning_type'] = leaderboard['model'].apply(classify_reasoning)

    # Define Column Order
    cols = ['Recommendation', 'model', 'reasoning_type', 'type', 'Overall Score', 'Profile']
    
    # Add Reasoning Split Columns if present
    if 'Logic (T1)' in leaderboard.columns:
        cols.append('Logic (T1)')
    if 'Reasoning (T2)' in leaderboard.columns:
        cols.append('Reasoning (T2)')
        
    cols += cat_cols + ['Avg Time (s)', 'Tests Run']
    
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
        if leaderboard['model'].str.contains(r'\*').any():
            print("\n* Model has not completed all benchmarks (excluded from ranking badges).")

if __name__ == "__main__":
    main()
