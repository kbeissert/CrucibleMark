# Code Quality Module

> **Technical Metadata**
> - **ID:** `code_quality`
> - **Namespace:** `benchmark_modules.code_quality`
> - **Class:** `CodeQualityTest` (inherits `BaseTest`)
> - **Evaluator:** `CodeQualityEvaluator`
> - **Version:** v1.0.0 (Clean Architecture)
> - **Type:** Engineering & Static Analysis

## 🔍 Module Overview

Dieses Modul bewertet die Fähigkeit von LLMs, Code-Reviews durchzuführen, Fehler zu finden und qualitativ hochwertige Verbesserungsvorschläge zu liefern. Ein besonderer Fokus liegt auf **Deep Reasoning**: Können Modelle den Unterschied zwischen "funktionierendem" und "sicherem/barrierefreiem" Code erkennen?

---

## 🏗 Architecture (Core/MVC)

This module follows the **Core/MVC** standard pattern enforced across the framework:

- **`test.py` (The Runner)**:
    - Acts as the entry point and "Controller".
    - Handles the LLM execution (API query, timing, token counting).
    - Delegates the complex scoring logic to `core/evaluators.py`.
- **`core/evaluators.py` (The Logic)**:
    - Contains `CodeQualityEvaluator` class.
    - Implements the Facade Pattern to orchestrate sub-scorers (`_score_error_detection`, `_score_solution_quality`, `_score_expertise`).
    - Handles `<think>` tag stripping for reasoning models.
- **`core/constants.py` (Configuration)**:
    - Defines thresholds, weights, and error messages.
    - Single source of truth for tuning sensitivity.
- **`assets/*.yaml` (Data)**:
    - Test cases defined in YAML. Contains prompt, context, and expected scoring rules.

---

## 🧪 Scoring Logic

The module uses a strictly deterministic scoring engine powered by the `CodeQualityEvaluator`.

### 1. Pre-Processing (Think-Tag Cleaning)
For reasoning models (e.g., DeepSeek R1), the evaluator strips out `<think>...</think>` blocks. This prevents the system from grading the model's internal monologue (which often contains "hallucinated faults" during brainstorming) and focuses purely on the final output.

### 2. Tiered Difficulty Scoring
The evaluation logic supports dynamic difficulty levels defined in `assets/*.yaml`:

*   **Level 1: Labeled Issues** (Easy): Explicitly marked errors (e.g., `// TODO`).
*   **Level 2: Standard Issues** (Medium): Common OWASP/WCAG violations.
*   **Level 3: Advanced Issues** (Hard): Subtile logical flaws or edge cases.
*   **Level 4: Expert Issues** (Deep Reasoning): Complex architectural flaws requiring context.

### 3. Scoring Dimensions (Total: 100)
1.  **Error Detection (Startwert 60p)**: Finds specific anti-patterns or bugs via keyword/regex matching.
2.  **Solution Quality (30p)**: Evaluates the proposed fix (Code validation, Syntax correctness).
3.  **Formatting/Expertise (10p)**: Checks for professional structure (Markdown, ARIA references).

---

## ⚙️ Configuration & Tuning

To adjust the module's sensitivity without changing code logic, edit `benchmark_modules/code_quality/core/constants.py`:

*   **`DEFAULT_TEMPERATURE`**: Controls generation determinism (default: `0.1`).
*   **`SIMILARITY_THRESHOLD`**: Adjusts how close a text must be to count as a match in semantic checks.
*   **Weights**: Adjust scoring ratios in `assets/*.yaml` directly.

---

## 📂 Available Assets

*   **Asset 001: WCAG Audit** (Accessibility Button implementation)
*   **Asset 002: Security Review** (SQL Injection & XSS)
*   **Asset 003: Performance** (React Renders & Queries)

