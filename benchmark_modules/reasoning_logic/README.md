# Reasoning Logic Module

> **Technical Metadata**
> - **ID:** `reasoning_logic`
> - **Namespace:** `benchmark_modules.reasoning_logic`
> - **Class:** `ReasoningLogicTest` (inherits `BaseTest`)
> - **Evaluator:** `ReasoningEvaluator`
> - **Version:** v1.0.0 (Clean Architecture)
> - **Type:** Cognitive & Logic Processing

## 🔍 Module Overview

Dieses Modul testet die reine Logik- und Schlussfolgerungsfähigkeit von LLMs. Anders als bei Code- oder Text-Tests gibt es hier oft nur **eine korrekte Antwort**, aber **viele Wege**, diese herzuleiten. Das Modul bewertet nicht nur das Ergebnis, sondern (bei Reasoning-Modellen) auch den Weg dorthin.

---

## 🏗 Architecture (Core/MVC)

This module follows the **Core/MVC** standard pattern enforced across the framework:

- **`test.py` (The Runner)**:
    - Handles the LLM execution and raw input/output.
    - Delegates scoring to `core/evaluators.py`.
- **`core/evaluators.py` (The Logic)**:
    - Contains `ReasoningEvaluator`.
    - Implements **Tiered Step-by-Step Verification** (checking if intermediate logical steps are present).
    - Strips `<think>` tags for result validation but optionally segments them for analysis.
- **`core/constants.py` (Configuration)**:
    - Defines logical fallacies to check for.
    - Configures strictness of "Exact Match" vs. "Semantic Match".
- **`assets/*.yaml` (Data)**:
    - Logic puzzles, syllogisms, and lateral thinking problems.

---

## 🧪 Scoring Logic

The scoring engine (`ReasoningEvaluator`) is designed to distinguish between "Lucky Guesses" and "True Understanding".

### 1. Three-Tier Verification Logic
The evaluator checks three distinct layers of the response:

*   **Tier 1: Final Answer Correctness (50p)**
    *   Example: "The answer is 42."
    *   Checked via regex or exact string matching defined in `expected_output`.
*   **Tier 2: Key Reasoning Steps (30p)**
    *   Example: "Because X is greater than Y..."
    *   The evaluator looks for specific intermediate conclusions required to solve the puzzle.
*   **Tier 3: Fallacy Check (20p)**
    *   Negative scoring: Does the model use banned arguments? (e.g., circular reasoning, ad hominem).

### 2. Think-Tag Handling
For models like **DeepSeek R1**:
*   The content within `<think>` tags is analyzed for **Reasoning Trace**.
*   The content *outside* tags is analyzed for **Final Answer**.
*   *Note: If a model gets the right answer but the reasoning trace contradicts it, the "Reasoning Steps" score is penalized.*

---

## ⚙️ Configuration

In `benchmark_modules/reasoning_logic/core/constants.py`:

*   **`FORBIDDEN_PHRASES`**: List of phrases that trigger immediate penalty (e.g., "I cannot answer this").
*   **`PARTIAL_CREDIT_ENABLED`**: If `True`, gives points for getting some steps right even if final answer is wrong.

---

## 📂 Available Assets

*   **Asset 001: Lateral Thinking** (The "Two Coins" Riddle)
*   **Asset 002: Syllogism Chain** (Multi-hop logic)
*   **Asset 003: Cognitive Bias Test** (Sunk Cost Fallacy scenarios)
