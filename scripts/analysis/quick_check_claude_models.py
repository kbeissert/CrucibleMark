import csv
import glob
unique_models = set()
for f in glob.glob('benchmark_scores/*.csv'):
    try:
        with open(f, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row.get('model_name') and 'claude' in row['model_name'].lower():
                    unique_models.add((row['model_name'], row.get('model_version')))
    except Exception:
        pass
for m, v in sorted(unique_models):
    print(f'{m} - {v}')
