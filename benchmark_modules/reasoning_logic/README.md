# Reasoning Logic Module

> **Technical Metadata**
> - **ID:** `reasoning_logic`
> - **Namespace:** `benchmark_modules.reasoning_logic`
> - **Class:** `ReasoningLogicTest` (inherits `BaseTest`)
> - **Version:** 0.9.6 (DeepSeek R1 Support)
> - **Type:** Cognitive Functionality (System 2 Thinking)

## 🔍 Module Overview

This module evaluates Large Language Models (LLMs) on **deep logical reasoning**, **constraint satisfaction**, and **deadlock detection**. Unlike other modules that focus on output format or style, this module strictly penalizes "hallucinated solutions" to impossible problems and supports both **Implicit** (Instruction) and **Explicit** (Chain-of-Thought) reasoning models.

### Core Objectives
1.  **Distinguish System 1 vs. System 2:** Separate models that rely on pattern matching (System 1) from those capable of multi-step deduction (System 2).
2.  **Explicit Reasoning Support:** Handles `<think>...</think>` tags from models like **DeepSeek R1** to score only the final output while measuring reasoning capability.
3.  **Adversarial Robustness:** Test if models can "refuse" invalid user instructions when logical constraints make them impossible.
4.  **Strict Validation:** Use deterministic scoring (regex/keyword) over purely semantic similarity to avoid "vibe checking".

## 📂 Verfügbare Test-Assets & Tiers

The module classifies tasks into tiers to separate basic sanity checks from advanced cognitive tests.

| Tier | ID | Name | Focus | Changes (v0.9.6) |
|---|----|------|-------|---|
| **Tier 0** | 001 | **River Crossing** | Sanity Check (Intelligence Floor) | Reclassified as "Tier 0 Sanity Check". |
| **Tier 1** | 5a | **Error Recovery** | Code Logic Debugging | Standard scoring. |
| **Tier 1** | 5c | **Adversarial** | Physics Paradox (Refusal) | Validates "Refusal" vs "Hallucinated Solution". |
| **Tier 2** | 5b | **Complex Chains** | Cross-Domain Deduction | **Updated:** Concept-based scoring (Option C) to allow narrative variance. |
| **Tier 2** | 5d | **Circular Dependency** | Deadlock Detection | **Updated:** Partial credit (100/70/40) for diverse deadlock warnings. |

---

## 🚀 Key Updates (v0.9.6)

### 1. DeepSeek R1 & Reasoning Model Support
*   **Tag Stripping:** The scorer now automatically removes `<think>...</think>` blocks from responses before analysis. This prevents internal brainstorms (which often contain wrong turns) from triggering false negative keyword matches.
*   **Capability Metrics:** The test now outputs a `reasoning_capability_score` in metadata:
    *   **100% (Explicit):** DeepSeek R1 (uses `<think>` tags).
    *   **70% (Implicit):** Qwen / CoT-trained models (strong reasoning but no tags).
    *   **20% (Pattern Matching):** Standard Instruction models (Dolphin, Llama).

### 2. Robust Scoring Logic (Asset 5D)
Moved from binary (All-or-Nothing) to graded scoring for "Impossible" tasks:
*   **100 pts:** Explicit "Feasibility: 0" OR strong "Impossible" declaration.
*   **70 pts:** "Feasibility: 1-3" OR identifying "Circular Dependency" (Correct logic but slight optimism).
*   **40 pts:** "Feasibility: 4-5" OR identifying "Risk/Complexity" (Weak detection).
*   **0 pts:** "Feasibility: >5" (Optimism Bias failure).

### 3. Narrative Flexibility (Asset 5B)
Updated matching logic to look for **Concepts** rather than exact strings.
*   *Example:* Recognizes "Dependency Mismatch" as equivalent to "Inconsistent Versioning".
*   Scoring requires finding specific **Concept Combinations** (e.g., Domain + Alignment Issue) rather than just keyword "Cross-Domain".

---

## 📂 File Structure & Architecture

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

The module classifies tasks into tiers based on cognitive load.

### Tier 0: Sanity Check
*   **River Crossing (Asset 001):** The "Hello World" of logic.
    *   *Purpose:* Filters out models incapable of basic constraint planning before running expensive Tier 2 tests.
    *   *Logic:* Pre-categorical basic intelligence test.

### Tier 1: Operational Logic (Standard)
Solvable problems requiring strict adherence to constraints.

*   **Error Recovery (Asset 5A):** Identifying and fixing breaks in a logical chain.
*   **The Scheduling Paradox (Asset 5C):**
    *   *Input:* "Paint walls on Tuesday, Build walls on Wednesday."
    *   *Success Condition:* Refusal or explicit validation failure.
    *   *Failure Mode:* Hallucinating a valid schedule.

### Tier 2: Deep Reasoning (Advanced)
"Impossible" problems requiring System 2 thinking to override instruction-following bias.

*   **Complex Chains (Asset 5B):** Cross-domain Root Cause Analysis (Code + Docs + UX).
    *   *Metric:* Requires linking concepts across 3 different domains into one unified policy solution.
    *   *Update:* Matches concepts like "Alignment" and "Governance" dynamically.

*   **The Hidden Deadlock (Asset 5D):**
    *   *Input:* Circular dependency chain (A waits for B, B for C, C for A).
    *   *Success Condition:* Answer must start with **"Feasibility: 0"** (or very low score).
    *   *Scoring Logic:* Tiered partial credit (100/70/40/0) based on awareness level.

---

## 🧠 Scoring Deep Dive: Binary vs. Open-Ended Problems

A crucial aspect of this module is understanding why some models achieve 100% on certain tasks (like Asset 5C) but fail on others (like Asset 5B).

### Why Dolphin (Pattern Matcher) scores 100% on Asset 5C (Paradox)
**Asset 5C (Scheduling Paradox)** is effectively a **Binary Problem** (True/False).
*   **The Problem:** "3 days needed, 3 days available, but dependency requires 5 days total."
*   **Math:** Simple arithmetic ($3+2 > 3$).
*   **Decision:** The model only needs to detect the contradiction and say "Impossible".
*   **Result:** Even Instruction models like Dolphin can detect this explicit contradiction via keyword matching, achieving 100%.

### Why Dolphin scores lower on Asset 5B (Complex Chains)
**Asset 5B (Cross-Domain Root Cause)** is an **Open-Ended Problem** (Essay type).
*   **The Problem:** Analyze conflicting signals across Code, Documentation, and UX to find a root cause and propose a strategy.
*   **No Math:** Requires narrative reasoning, not arithmetic.
*   **Requirement:** Identify concepts AND structure a prioritized solution (Steps 1-3).
*   **Result:** Dolphin often finds the concepts (Pattern Matching "Policy", "Alignment") but lacks the **System 2** capability to prioritize and structure the solution correctly. The scoring rewards structure, leading to a realistic <100% score for non-reasoning models.

### Evidence: Processing Time
The difference is visible in the compute time (Tokens/Time):
*   **Asset 5C:** DeepSeek R1 takes ~124s (Over-thinking a binary problem). Dolphin takes ~6s.
*   **Asset 5B:** DeepSeek R1 takes ~35s (Appropriate depth). Dolphin takes ~7.5s (Too fast for deep analysis).
*   **Conclusion:** DeepSeek engages deeper reasoning even for simple tasks, while Dolphin relies on surface-level heuristics. The benchmark is designed to reveal exactly this distinction.

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
