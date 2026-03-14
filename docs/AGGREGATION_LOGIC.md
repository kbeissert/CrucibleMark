# CrucibleMark Aggregation & Counting Logic Report

## 1. Test Count Discrepancy ("46/37")

The observed "46/37" test count in the leaderboard is **intentional behavior** resulting from the configuration of the "Political Compass" module, but presents a confusing User Interface.

### Breakdown

- **Denominator (37):** Represents the total number of **Scoring Assets**.
  - Code Quality: 5
  - UX Writing: 5
  - Documentation: 5
  - Content: 6
  - Cultural: 5
  - Reasoning: 11
  - **Total:** 37
- **Numerator (46):** Represents the "Logical Run Count" of completed tests.
  - Completed Scoring Assets: 37
  - Political Compass Override: **+9**
  - **Total:** 46

### Why 9?

The `Political Compass` module is configured in `benchmark_modules/political_compass/config.yaml` with `display_test_count: 9`. This override is applied to the performed test count to represent the semantic complexity of the module (which evaluates ~88 questions across multiple axes), even though technically it runs as a single batch process producing 1 result row.

### Why not in Denominator?

The Political Compass module has `enable_scoring: false` in its configuration (as it provides bias info, not a quality score). The denominator calculation currently sums only assets from **scoring-enabled** modules.

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

## 3. Recommendation

To fix the confusing "46/37" display, we have two options:

1. **Semantic Fix (Recommended for Status Quo):** Keep as is, acknowledging that "Extra Credit" or "Non-Scoring" modules add to the completed count but not the required scoring baseline.
1. **Display Fix:** Update `score_calculator.py` to include `display_test_count` overrides in the expected total (Denominator), even if scoring is disabled. This would result in "46/46".

**Current Status:** Valid & Safe. No critical data bug found.

______________________________________________________________________

## 4. Stability Score

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
