import csv
import glob
model_versions = {}
files = [f for f in glob.glob('benchmark_scores/*.csv') if 'leaderboard' not in f]
for f in files:
    try:
        with open(f, encoding='utf-8') as csvf:
            reader = csv.DictReader(csvf)
            for row in reader:
                model = row.get('model', row.get('model_name'))
                if not model: continue
                version = row.get('model_version', 'k.A.')
                if not version: version = 'k.A.'
                if model not in model_versions:
                    model_versions[model] = set()
                model_versions[model].add(version)
    except Exception:
        pass

for m, vs in sorted(model_versions.items()):
    print(f"{m}: {vs}")
