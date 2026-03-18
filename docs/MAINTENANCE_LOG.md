# CrucibleMark Maintenance: Test Count & Aggregation

## Leaderboard Numerator Fix (v2.2)

**Date:** 2026-03-16
**Status:** Resolved

### Problem Description

Even after decoupling the Political Compass, the `Tests Run` fraction still showed an inflated numerator (e.g., "44/43"). This occurred because `scripts/leaderboard/score_calculator.py` iterated blindly over all unique categories present in the data to build the `logical_count` (numerator), without checking if `enable_scoring: false` was set in the module configs, inadvertently picking up Political Compass or System Probe test artifacts.

### Resolution

1. **Category Filtering:** Added a `counting_cats` Set to `_calculate_run_counts` in `score_calculator.py`. Only modules that actually yield a score (`enable_scoring: True`) or strictly declare a custom `display_test_count` are evaluated.
2. **Docs Cleanup:** Purged leftover `display_test_count: 9` artifacts from module READMEs and Development Guides to prevent future confusion.

***

## Political Compass Architecture Decoupling (v2.1)

**Date:** 2026-03-14
**Status:** Resolved

### Problem Description

The logic that appended the Political Compass module into the main dataframes ('Ghost Rows') to register it as a "completed test" led to mathematically inaccurate UI metadata ("Test Runs: 165/156"). By having an informational-only ethical survey integrated inside the primary dataframe structure, the purity of the code-quality test counts and time-benchmarks was hindered.

### Resolution

1. **Full Decoupling:** Removed standard Data Loader ghost row injection routines (`scripts/leaderboard/data_loader.py`) for the PC module, and detached its config `display_test_count`.
2. **Isolating Outputs:** Split outputs elegantly into "Wolf in Sheep's Clothing" logic—producing `benchmark_scores/political_compass_results.csv` (run records) & `benchmark_scores/political_compass_leaderboard.csv` (shift aggregations).
3. **Post-Evaluation Stitching:** Altered the final steps of `generate_leaderboard.py` to extract only the Vanilla alignment tag and distance Shift string as a standalone right-aligned text column, ignoring `score_calculator.py`.

***

## Ghost Entries & Versioning Refactor

**Date:** 2026-02-06
**Status:** Resolved

### Problem Description

The leaderboard showed duplicate entries for single models (e.g., "Claude Haiku"). One entry contained benchmark scores, while a second "Ghost Entry" contained only Political Compass results.
**Root Cause:** Inconsistent version strings between the Benchmark Runner (`8717af19`) and the Political Compass Runner (`unknown`).

### Resolution

1. **Centralization:** Version logic moved to `utils/model_utils.py` (`get_model_version`) as SSOT.
1. **Deterministic Mapping:** Removed behavioral hash fingerprinting to prevent ghost duplicates.
1. **Data Patch:** Merged split entries in CSVs and aligned historical cache entries.
1. **Golden Standard Optimization:** Excluded Political Compass from Golden Standard generation (Methodology Update).

## Aggregation Verification Report

**Date:** 2026-02-04
**Status:** Resolved

### Summary of Findings

The leaderboard previously displayed "46/37 Tests Run". This discrepancy was caused by the `Political Compass` module contributing to the **Numerator** (Count of completed tests) via an explicit override (9 logical tests), but being excluded from the **Denominator** (Expected tests) because scoring was disabled (`enable_scoring: false`).

### Verification Data

```python
aggregation_report = {
    "total_unique_assets_in_csv": 38,
    "breakdown": {
        "scoring_assets": 37,
        "political_compass_rows": 1
    },
    "logical_test_counts": {
        "scoring_tests": 37,
        "political_compass_logical": 9,
        "total_logical": 46
    },
    "previous_display": "46/37",
    "fixed_display": "46/46",

    "aggregation_rules": {
        "method": "last-value-wins",
        "implementation": "df.drop_duplicates(subset=[model, version, asset_id], keep='last')",
        "models_with_duplicates": "All (Historical runs are preserved in raw CSV, filtered at load time)",
        "duplicate_runs_intentional": True
    }
}
```

### Corrective Actions

1. **Code Update:** Modified `scripts/leaderboard/score_calculator.py` to include modules in the "Expected Count" (Denominator) if they have an explicit `display_test_count`, even if scoring is disabled.

   - *Result:* Denominator increased from 37 to 46. Leaderboard will now show "46/46".

1. **Duplicate Handling:** Verified that `data_loader.py` correctly handles multiple runs by selecting the latest entry based on timestamp.

   - *Result:* Users can re-run benchmarks safely; the leaderboard always reflects the current state.

### How to Reproduce

Run the verification script:

```bash
python scripts/maintenance/verify_counts.py
```


***

## API Timeout & Nested Pydantic Serialization (v3.0.0)

**Date:** 2026-03-18
**Status:** Resolved

### Problem Description

Two structural issues blocked the continuous evaluation of strict or censored models (like Gemini/Claude) inside the Political Compass:
1.  **Refusal Stalling:** Models returning "Sorry, I can't answer this" triggered instant failure in metric parsing, crashing the batch evaluation sequence instead of trying varying permutations.
2.  **Verify Anomalies Crashes:** Checking shift values natively crashed with `AttributeError`. It attempted to call `.get()` natively on the Pydantic schema return (`base_result.raw_response`), which is strictly stored as a JSON string, not a generic dict.

### Resolution

1.  **3-Tier Refusal Loop:** We introduced a robust `while True` loop with progressive temperature checks (`0.1`, `0.4`, `0.7`) mapping hard limits inside the specific run execution (`_run_single_block` in `political_compass/test.py`). This systematically breaks censorship filters autonomously.
2.  **Pydantic Deserialize:** Shifted all `raw_response` reads across verify scripts to `json.loads(str)` forcing dict compliance before accessing nested variables (Vanilla/Forced).
