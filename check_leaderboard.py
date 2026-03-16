import csv
with open('benchmark_scores/benchmark_leaderboard.csv', 'r') as f:
    reader = csv.DictReader(f)
    print(f"{'Model':<30} | {'Version':<20} | {'Score'}")
    print("-" * 65)
    for row in reader:
        print(f"{row['model']:<30} | {row['model_version']:<20} | {row['total_score']}")
