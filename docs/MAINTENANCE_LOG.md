# CrucibleMark Maintenance: Test Count & Aggregation

## Ghost Entries & Versioning Refactor

**Date:** 2026-02-06
**Status:** Resolved

### Problem Description

The leaderboard showed duplicate entries for single models (e.g., "Claude Haiku"). One entry contained benchmark scores, while a second "Ghost Entry" contained only Political Compass results.
**Root Cause:** Inconsistent version strings between the Benchmark Runner (`8717af19`) and the Political Compass Runner (`unknown`).

### Resolution

1. **Centralization:** Refactored `utils/fingerprinting.py` to be the Single Source of Truth (SSOT).
1. **Dual-Versioning:** Implemented unified format `{OFFICIAL_ID}-{BEHAVIORAL_HASH}` enforced across all scripts.
1. **Data Patch:** Merged split entries in CSVs.
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
