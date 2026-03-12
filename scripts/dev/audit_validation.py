import pandas as pd
from pathlib import Path

LEADERBOARD_CSV = "benchmark_scores/benchmark_leaderboard.csv"
LOCAL_CSV = "benchmark_scores/local_models_benchmark.csv"
COMMERCIAL_CSV = "benchmark_scores/commercial_models_benchmark.csv"


def colors(text, color):
    codes = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "reset": "\033[0m",
    }
    return f"{codes.get(color, '')}{text}{codes['reset']}"


def check_leaderboard_dtypes():
    print(f"\n--- {colors('Checking Leaderboard Data Types', 'yellow')} ---")
    if not Path(LEADERBOARD_CSV).exists():
        print(colors(f"File not found: {LEADERBOARD_CSV}", "red"))
        return

    df = pd.read_csv(LEADERBOARD_CSV)

    # Check Module Columns
    modules = [
        "Code Quality Audit",
        "UX Writing & Microcopy",
        "Documentation Quality",
        "Content Transformation & Adaption",
        "Cultural Intelligence",
        "Logical Reasoning",
    ]

    for mod in modules:
        if mod in df.columns:
            dtype = df[mod].dtype
            sample = df[mod].iloc[0] if not df.empty else "N/A"
            msg = f"Column '{mod}': Type={dtype}, Sample={sample}"
            if dtype == "object":
                print(colors(msg, "red") + " (Likely contains strings/mixed types)")
            else:
                print(colors(msg, "green"))

    # Check Tests Run
    if "Tests Run" in df.columns:
        print(f"Tests Run Sample: {df['Tests Run'].iloc[0]}")


def check_asset_saturation():
    print(f"\n--- {colors('Checking Asset Saturation (100% Scores)', 'yellow')} ---")

    dfs = []
    if Path(LOCAL_CSV).exists():
        dfs.append(pd.read_csv(LOCAL_CSV))
    if Path(COMMERCIAL_CSV).exists():
        dfs.append(pd.read_csv(COMMERCIAL_CSV))

    if not dfs:
        print("No benchmark CSVs found.")
        return

    df = pd.concat(dfs, ignore_index=True)

    if "asset_id" not in df.columns or "percentage" not in df.columns:
        print("Required columns missing in benchmark CSVs.")
        return

    stats = (
        df.groupby("asset_id")
        .agg(
            count=("asset_id", "count"),
            perfect=("percentage", lambda x: (x >= 100.0).sum()),
        )
        .reset_index()
    )

    stats["rate"] = stats["perfect"] / stats["count"]

    total_runs = stats["count"].sum()
    total_perfect = stats["perfect"].sum()

    print(f"Total Asset Executions Analyzed: {total_runs}")
    print(
        f"Total Perfect Scores (100%): {total_perfect} ({total_perfect/total_runs:.1%})"
    )

    saturated = stats[stats["rate"] > 0.5]
    if not saturated.empty:
        print("\nTop Saturated Assets (>50% perfect):")
        for _, row in saturated.sort_values("rate", ascending=False).iterrows():
            print(
                f"- {row['asset_id']}: {row['rate']:.1%} ({row['perfect']}/{row['count']})"
            )
    else:
        print("\nNo assets > 50% saturation.")


if __name__ == "__main__":
    check_leaderboard_dtypes()
    check_asset_saturation()
