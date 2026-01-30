# CrucibleMark Data Retention & Backup Strategy

> **"The Crucible Memory Law"**

## 1. Philosophy & Purpose

The architecture of CrucibleMark follows a specific guiding principle regarding data longevity and history:

> **"Wir bauen hier ein Werkzeug zum Vergleich von Modellen (Leaderboard), kein Werkzeug zum Monitoring von Modell-Veränderungen über die Zeit."**
>
> Daher benötigen wir im **Live-System** (`benchmark_scores/*.csv`) keine Historie. Wir benötigen nur den **aktuellsten, validen Zustand** eines jeden Modells.

This distinction is crucial:
*   **Static Weights:** Local models (e.g., `llama3:8b-q4_K_M`) are static files. Their performance does not change over time.
*   **Locked APIs:** Commercial models are pinned to specific versions (e.g., `gpt-4-0613`) to ensure reproducibility.
*   **Conclusion:** Storing redundant historical data in the active workspace bloats the system without adding value for the primary use case (comparing Model A vs. Model B).

---

## 2. The Backup Lifecycle

To balance data safety with workspace hygiene, CrucibleMark implements a **"Snapshot & Prune"** workflow (`make backup`).

### Phase 1: The Archive (Immutable History)
*   **Action:** Create a `.tar.gz` snapshot of the entire workspace.
*   **Path:** `backups/cruciblemark_backup_YYYYMMDD_HHMMSS.tar.gz`
*   **Content:** Includes all scores, full JSON run logs, and module configurations.
*   **Rule:** This is the *System of Record*. If historical analysis is ever needed (e.g., "How did GPT-4 perform a year ago?"), it is retrieved from these archives.

### Phase 2: JSON Cleanup (Hygiene)
*   **Action:** Execute `scripts/cleanup_runs.py`.
*   **Target:** `outputs/runs/**/*.json`
*   **Rule:** Keep only the **last 5 runs** per model. Older detailed logs are deleted from the live workspace (since they are safely stored in the archive from Phase 1).

### Phase 3: CSV Consolidation (The "Latest Only" Rule)
*   **Action:** Execute `scripts/consolidate_csv.py`.
*   **Target:** `benchmark_scores/*.csv`
*   **Logic:**
    1.  Load the cumulative CSV file.
    2.  Sort by timestamp (newest first).
    3.  Group by unique key: `(Model Name, Asset ID)`.
    4.  **Deduplicate:** Keep **only the single most recent entry**. Remove all older duplicates.
*   **Result:** The CSV file is reset to a "canonical state" containing exactly one valid score per test case.

---

## 3. Workflow Implications

### Continuous Benchmarking ("Rolling Updates")
Because the CSV files are consolidated to the latest state:
1.  **Optimization:** When running `make benchmark-auto` after a backup, the system detects that the latest test results are present in the CSV.
2.  **Efficiency:** It skips all successfully tested assets.
3.  **Updates:** It only executes tests for *new* models or *new* assets added since the last run.

### Manual Refreshes
To force a re-run of a specific model without deleting the entire history:
1.  Delete the relevant lines from the CSV manually.
2.  Run `make benchmark-auto`.
3.  The system sees the missing entry and re-runs the test, appending the new result to the CSV.
4.  The next `make backup` will consolidate this, removing the (now older) previous entry if it was backed up previously.

---

## 4. Technical Implementation

The strategy is enforced via the Makefile:

```makefile
backup:
    # 1. Archive
    @tar -czf backups/... 
    
    # 2. Cleanup Logs
    @scripts/cleanup_runs.py --keep 1 --force
    
    # 3. Consolidate Scores
    @scripts/consolidate_csv.py
```
