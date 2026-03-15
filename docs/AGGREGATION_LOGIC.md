# CrucibleMark Aggregation & Counting Logic Report

## 1. Test Count Discrepancy & Political Compass

**Update v2.1:** The "Political Compass" module has been **fully decoupled** from the main benchmark scoring and test counts.

### Previous Behavior (Pre-v2.1)
The leaderboard previously showed a discrepancy (e.g., "46/37" tests run). This was because the Political Compass module injected "Ghost Rows" into the dataset to register as completed (adding `+9` to the numerator) without contributing to the score denominator. This caused mathematical confusion.

### Current Behavior (v2.1+)
The Political Compass is now strictly an informational metadata module:
- It **does not** inject ghost rows into the main dataframes (`local_models_benchmark.csv` / `commercial_models_benchmark.csv`).
- It **does not** artificially inflate the `Tests Run` counter (e.g. 44/43). The score calculator explicitly ignores non-scoring modules for both the numerator and the denominator, unless a `display_test_count` is defined.
- It operates entirely autarkic, saving its detailed runs directly into `benchmark_scores/political_compass_details.csv` and its aggregates into `benchmark_scores/political_compass_leaderboard.csv`.
- The `generate_leaderboard.py` script simply checks the final `political_compass_leaderboard.csv` to append a simple `Political Bias` text column to the final display table, injecting purely informational tags without touching the core mathematics of the benchmark.

______________________________________________________________________

## 2. Duplicate Handling & Data Integrity

### Observation

The raw file `benchmark_scores/local_models_benchmark.csv` contains multiple entries for the same model and asset (e.g. 288 rows for ~38 assets).

### Logic Verification

The system uses a **"Last-Win" Strategy** (Overwrite), not Averaging.

**Code Evidence (`scripts/leaderboard/data_loader.py`):**

```python
# Sort by timestamp to ensure 'last' is actually the most recent
df = df.sort_values("timestamp")

# Drop duplicates keeping the LAST entry
df = df.drop_duplicates(subset=["model", "model_version", "type", "asset_id"], keep="last")
```

### Conclusion

- **Data Integrity:** The leaderboard generation is **robust** against duplicates. It explicitly cleans the data before calculation.
- **Stability Testing:** Running benchmarks multiple times is safe; the system will simply report the latest result for each asset.
- **History:** The `csv` acts as a historical log. This is a feature, not a bug.

______________________________________________________________________

## 3. Stability Score

To ensure fair stability measurement across diverse tasks with naturally varying execution times (e.g., a fast translation vs. long documentation tasks), the system uses a **Category-Aware Variance** logic.

Stability is calculated based on the **Coefficient of Variation (CV)** *within* each category, and then those CVs are averaged.

1. **Calculate CV per Category**:
   $CV\_{cat} = \\frac{\\sigma\_{cat}}{\\mu\_{cat}}$
   (Standard Deviation divided by Mean for that category)

1. **Average Stability Score**:
   $Score\_{stability} = \\frac{1}{N} \\sum CV\_{cat}$

### Thresholds

- **< 0.35 (35%)**: **STABLE** (Normal variance)
- **0.35 - 0.50 (35-50%)**: **MODERATE** (High natural variance or slight instability)
- **> 0.50 (50%)**: **UNSTABLE** (Significant unpredictability)

This ensures that a model performing consistently strictly within its categories (e.g. always fast on translations, always slow on docs) receives a good stability score.
