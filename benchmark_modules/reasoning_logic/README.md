# Reasoning Logic Module

> **Technical Metadata**
> - **ID:** `reasoning_logic`
> - **Namespace:** `benchmark_modules.reasoning_logic`
> - **Class:** `ReasoningLogicTest` (inherits `BaseTest`)
> - **Version:** 0.5.0-beta
> - **Type:** Cognitive Functionality (System 2 Thinking)

## 🔍 Module Overview

This module evaluates Large Language Models (LLMs) on **deep logical reasoning**, **constraint satisfaction**, and **deadlock detection**. Unlike other modules that focus on output format or style, this module strictly penalizes "hallucinated solutions" to impossible problems.

### Core Objectives
1.  **Distinguish System 1 vs. System 2:** Separate models that rely on pattern matching (System 1) from those capable of multi-step deduction (System 2).
2.  **Adversarial Robustness:** Test if models can "refuse" invalid user instructions when logical constraints make them impossible.
3.  **Strict Validation:** Use deterministic scoring (regex/keyword) over purely semantic similarity to avoid "vibe checking".

## 📂 Verfügbare Test-Assets

| ID | Name | Focus | Difficulty |
|----|------|-------|------------|
| 001 | **River Crossing** | Classic Logic Puzzle | Hard |
| 5a | **Error Recovery** | Self-Correction | Tiered |
| 5b | **Complex Chains** | Multi-hop Deduction | Tiered |
| 5c | **Adversarial** | Prompt Injection Resistance | Tiered |
| 5d | **Circular Dependency** | Deadlock Detection | Tiered |

---

## 📂 File Structure & Architecture

The module follows a **Strategy Pattern** for scoring to handle different reasoning tiers.

| File | Role | Description |
| :--- | :--- | :--- |
| `test.py` | **Controller** | Main execution logic. Contains `score_response` which acts as a Facade, dispatching to specific scoring methods (e.g., `_score_5c_paradox`). |
| `constants.py` | **Configuration** | **Single Source of Truth** for keywords, scoring weights, and thresholds. Edit this file to tune sensitivity. |
| `assets/*.yaml` | **Data** | Test cases defined in YAML. Contains `prompt`, `metadata`, and `expected_output`. |
| `config.yaml` | **Registry** | Module registration info for the main benchmark runner. |

---

## 🧠 Test Scenarios (Tiers)

The module classifies tasks into two complexity tiers.

### Tier 1: Operational Logic (Standard)
Solvable problems requiring strict adherence to constraints.

*   **River Crossing (Asset 001):** Sequential planning with exclusion constraints.
*   **Error Recovery (Asset 5A):** Identifying and fixing breaks in a logical chain.
*   **Multi-Hop Deduction (Asset 5B):** Linking fragmented evidence to find a conclusion.

### Tier 2: Deep Reasoning (Advanced/Adversarial)
"Impossible" problems designed to trigger **Optimism Bias** in weak models.

*   **The Scheduling Paradox (Asset 5C):**
    *   *Input:* "Paint walls on Tuesday, Build walls on Wednesday."
    *   *Success Condition:* Model must **REFUSE** the detailed plan or explicitly flag the dependency violation.
    *   *Failure Mode:* Creating a schedule that includes painting before building.
    *   *Scoring Logic:* Checks for existence of `ASSET_5C_REFUSAL_KEYWORDS` vs `ASSET_5C_ILLEGAL_MOVES`.

*   **The Hidden Deadlock (Asset 5D):**
    *   *Input:* Circular dependency chain (A waits for B, B for C, C for A) + "Rate feasibility 0-10".
    *   *Success Condition:* Answer must start with **"Feasibility: 0"** (or very low score).
    *   *Failure Mode:* Answering "YES" or providing a timeline (detects LLM "fear of saying no").
    *   *Scoring Logic:* Regex extraction of feasibility score (`re.search(r'feasibility:\s*(\d+)')`). Scores > 2 result in 0 points.

---

## 📊 Scoring Mechanism

Scoring is **deterministic** and defined in `constants.py`.

### Weights
*   **Error Detection (40%):** Did the model notice the logical trap?
*   **Solution Quality (50%):** Is the resulting answer/refusal logically sound and structured?
*   **Consistency (10%):** Does the explanation match the verdict?

### Constants Reference (`constants.py`)
To adjust sensitivity, modify these lists:
*   `ASSET_5D_POSITIVE_TOKENS`: List of words indicating successful deadlock detection (e.g., "impossible", "nein").
*   `ASSET_5D_NEGATIVE_TOKENS`: List of words indicating failure (e.g., "possible", "ja").
*   `WEIGHT_*`: Point distribution constants.

---

## 🛠 Extension Guide for Agents/Co-Pilot

If you are an AI assistant tasked with extending this module:

1.  **Adding a New Asset:**
    *   Create `assets/asset_00X_name.yaml`.
    *   Add specific keywords to `constants.py` if generic scoring is insufficient.
    *   Register a new specific handler in `test.py` -> `score_response` **only if** the logic differs significantly from standard pattern matching.

2.  **Modifying Scoring:**
    *   **Do not** modify `test.py` for threshold changes. Go to `constants.py`.
    *   Ensure `MAX_SCORE` remains `100.0`.

3.  **Refactoring:**
    *   Keep logic and data separated.
    *   Any text string used for validation **MUST** be a constant in `constants.py`.
