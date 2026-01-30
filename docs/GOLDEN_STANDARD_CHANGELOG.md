# Golden Standard Changelog

Documentation of Manual Updates to the CrucibleMark Golden Standard.

> **Hinweis zur Versionierung:**
> Diese Versionierung (z.B. v2.1) bezieht sich ausschließlich auf die Referenz-Datensätze (Golden Standards). Sie ist unabhängig von der Software-Version des Frameworks (CrucibleMark SemVer). Änderungen hier signalisieren eine Verschiebung des "Nullpunkts", gegen den alle Modelle gemessen werden.

## v2.1.0 (2026-01-30)

*   **Model:** `mistral-large-latest`
*   **Reasoning Score (RCI):** 87.40
*   **Routine Score:** 82.59
*   **Changes:**
    *   Added **Reasoning 5C-2** (The Monitoring Paradox).
    *   Added **Reasoning 5D-2** (The Hidden Dependency Chain).
    *   Updated Scoring Logic for `5c_001` (Scheduling Paradox) from ~49% (bugged) to 100% (fixed).
    *   Updated Reasoning Weighting: Tier 2 (60%) / Tier 3 (40%).
*   **Note:** This update resets the "Performance Ratio" calculation. Scores >100% in previous runs are now normalized relative to this baseline.

## v2.0.0 (2026-01-22)

*   **Model:** `mistral-large-latest`
*   **Reasoning Score (RCI):** ~81.25 (Retroactive Estimate)
*   **Changes:**
    *   Initial Stable Release of Reasoning Module v1.
    *   Defined "Tier 1", "Tier 2", "Tier 3" taxonomy.
