# Documentation Quality Module

> **Technical Metadata**
> - **ID:** `documentation_quality`
> - **Namespace:** `benchmark_modules.documentation_quality`
> - **Class:** `DocumentationQualityTest` (inherits `BaseTest`)
> - **Evaluator:** `DocumentationEvaluator`
> - **Version:** v2.0.0 (Modular Evaluators Architecture)
> - **Type:** Technical Writing & Education

## 🔍 Module Overview

Dieses Modul prüft die Fähigkeit von LLMs, technische Konzepte zu erklären, API-Dokumentationen zu erstellen oder komplexe Prozesse in verständliche Anleitungen zu überführen. Es unterscheidet strikt zwischen Marketing-Blabla und nutzbarem technischem Content.

---

## 🏗 Architecture (v2.0)

This module follows the **Core/MVC** standard pattern enforced across the framework:

```
core/evaluators/
├── __init__.py              # DocumentationEvaluator (Facade)
├── semantic_matcher.py      # Hybrid keyword + semantic matching
├── tiered_scoring.py        # Tiered difficulty engine
├── solution_quality.py      # Criteria-based quality checks
├── structure_validator.py   # Markdown format validation (NEW)
├── readability_scorer.py    # Flesch-Kincaid metrics (NEW)
└── completeness_checker.py  # Required sections detection (NEW)
```

## New Features (v2.0)

### Structure Validation
- Heading hierarchy checks (H1 → H2 → H3)
- Code block counting
- Required sections detection (per doc_type)

### Readability Scoring
- Flesch Reading Ease (0-100 scale)
- Average sentence length
- Grade level estimation

### Completeness Checking
- Fuzzy matching for section names
- Doc-type specific requirements (README vs API vs Setup Guide)

## Old Architecture

- **`test.py` (The Runner)**:
    - Provides code snippets or architecture diagrams as context.
    - Delegates content analysis to `core/evaluators.py`.
- **`core/evaluators.py` (The Logic)**:
    - Contains `DocumentationEvaluator`.
    - Implements **Structure Matching** (does it have Prerequisites, Steps, Troubleshooting?).
    - Uses **Hybrid Semantic Search** to verify coverage of key concepts.
- **`core/constants.py` (Configuration)**:
    - Defines required sections for different doc types (e.g., "API Reference" must have "Parameters" and "Returns").
- **`assets/*.yaml` (Data)**:
    - Raw code inputs and expected documentation outputs.

---

## 🧪 Scoring Logic

The scoring is based on the "Information Architecture" principles.

### 1. Structural Completeness (The Skeleton)
Does the generated markdown follow the standard template?
*   Checks for headers (`#`, `##`).
*   Checks for code blocks where expected three backticks.
*   Checks for list items (steps).

### 2. Concept Coverage (Hybrid Semantic)
Using simple keyword matching *and* embedding similarity (via `utils.similarity`):
*   **Essential Concepts**: If the doc explains "OAuth" but misses "Tokens", it loses points.
*   **Hallucination Check**: Does it document parameters that don't exist in the input code?

### 3. Clarity & Examples
*   **Example Density**: High score requires providing concrete code examples, not just abstract descriptions.
*   **Formatting**: Proper use of bolding, italics, and warning blocks (`> Warning`).

---

## ⚙️ Configuration

In `benchmark_modules/documentation_quality/core/constants.py`:

*   **`REQUIRED_SECTIONS`**: Map of doc-types to mandatory headers.
*   **`MIN_EXAMPLE_COUNT`**: Minimum number of code blocks required for a full score.

---

## 📂 Available Assets

*   **Asset 001: API Endpoint** (Documenting a Python Flask route)
*   **Asset 002: Installation Guide** (Docker setup instructions)
*   **Asset 003: Architecture Explain** (System Design textual description)

