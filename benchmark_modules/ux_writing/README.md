# UX Writing Module

> **Technical Metadata**
> - **ID:** `ux_writing`
> - **Namespace:** `benchmark_modules.ux_writing`
> - **Class:** `UXWritingTest` (inherits `BaseTest`)
> - **Evaluator:** `UXWritingEvaluator`
> - **Version:** v1.0.0 (Clean Architecture)
> - **Type:** Content Strategy & Microcopy

## 🔍 Module Overview

Dieses Modul prüft die Kompetenz von LLMs im Bereich **User Experience Writing**. Es geht nicht um lange Texte, sondern um präzise, handlungsleitende und empathische Microcopy (Buttons, Fehlermeldungen, Onboarding-Screens).

---

## 🏗 Architecture (Core/MVC)

This module follows the **Core/MVC** standard pattern enforced across the framework:

- **`test.py` (The Runner)**:
    - Handles prompt injection for specific Personas (e.g., "Voice: Helpful but concise").
    - Delegates analysis to `core/evaluators.py`.
- **`core/evaluators.py` (The Logic)**:
    - Contains `UXWritingEvaluator`.
    - Features specialized **Text Stat Analyzers** (Flesch-Reading-Ease, Character Count).
    - Checks for **Tone Consistency**.
- **`core/constants.py` (Configuration)**:
    - Defines character limits for specific UI elements (e.g., "Button Label" < 20 chars).
    - Stores "Banned Words" lists (e.g., technical jargon like "Fatal Error").
- **`assets/*.yaml` (Data)**:
    - Scenarios defining the User Journey and the required UI component.

---

## 🧪 Scoring Logic

The `UXWritingEvaluator` combines hard metrics (Length) with soft metrics (Sentiment).

### 1. Brevity & Constraints (The "Mobile First" Check)
UX Writing often has hard limits.
*   **Characters**: If the output exceeds the limit defined in `constants.py` for the component type, the score drops drastically.
*   **Structure**: Does it use bullet points where requested?

### 2. Tone & Voice Analysis
*   **Sentiment Analysis**: Verifies if the error message is "blameless" (User-Centric) or "accusatory" (System-Centric).
*   **Clarity**: Measures reading level. Lower grade level = Better UX Score.

### 3. Jargon Detection
*   Scans for technical terms ("Database Exception", "Null Pointer") that should never appear in user-facing copy.

---

## ⚙️ Configuration

In `benchmark_modules/ux_writing/core/constants.py`:

*   **`COMPONENT_LIMITS`**: Dictionary mapping UI types to max lengths (e.g., `{'button': 25, 'toast': 60}`).
*   **`TONE_GUIDELINES`**: Defines positive/negative word lists for sentiment scoring.

---

## 📂 Available Assets

*   **Asset 001: 404 Page** (Creative yet helpful dead-end handling)
*   **Asset 002: Success Toast** (Confirmation message logic)
*   **Asset 003: Critical Error** (Payment failure handling - empathy check)
