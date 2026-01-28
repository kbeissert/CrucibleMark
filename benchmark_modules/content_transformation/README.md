# Content Transformation Module

> **Technical Metadata**
> - **ID:** `content_transformation`
> - **Namespace:** `benchmark_modules.content_transformation`
> - **Class:** `ContentTransformationTest` (inherits `BaseTest`)
> - **Evaluator:** `ContentForEvaluator` (Legacy Naming) -> `TransformationEvaluator`
> - **Version:** v1.0.0 (Clean Architecture)
> - **Type:** Data Processing & ETL

## 🔍 Module Overview

Dieses Modul testet die **Zuverlässigkeit** von LLMs bei der Umwandlung von Datenformaten. Es ist entscheidend für RAG-Pipelines und Agenten, die unstrukturierten Text (PDFs, Mails) in strukturierte Daten (JSON, XML, YAML) wandeln müssen, **ohne** Informationen zu verlieren oder zu erfinden.

---

## 🏗 Architecture (Core/MVC)

This module follows the **Core/MVC** standard pattern enforced across the framework:

- **`test.py` (The Runner)**:
    - Feeds raw unstructured text to the model.
    - Delegates validation to `core/evaluators.py`.
- **`core/evaluators.py` (The Logic)**:
    - Contains `TransformationEvaluator`.
    - Implements **Schema Validation** (using `jsonschema` or equivalent).
    - Checks **Key-Value Integrity**.
- **`core/constants.py` (Configuration)**:
    - Stores expected Schemas (JSON Schemas).
    - Defines "Critical Fields" that must not be hallucinated/missing.
- **`assets/*.yaml` (Data)**:
    - Input text and the target schema definition.

---

## 🧪 Scoring Logic

Scoring is binary-weighted: A syntax error usually results in a 0 score for that section.

### 1. Syntax Compliance (The Gatekeeper)
*   **Validity**: The output must be parseable by standard libraries (`json.loads`, `ET.fromstring`).
*   **Format Check**: If JSON was requested, Markdown code blocks are stripped, but the content must be pure JSON.

### 2. Schema Fidelity
*   **Keys**: Do all keys from the requirement exist?
*   **Types**: Is `age` a number or a string? (Strict typing check).

### 3. Data Integrity (Source of Truth)
*   **Hallucination Check**: If the source text says "John returns on Friday", and the JSON says `{"return_day": "Monday"}`, this is a critical failure.
*   **Omission Check**: Did it drop an item from a list?

---

## ⚙️ Configuration

In `benchmark_modules/content_transformation/core/constants.py`:

*   **`STRICT_MODE`**: If `True`, any extra key not in schema reduces score.
*   **`ALLOW_COMMENTS`**: For JSONC support (usually False for standard JSON).

---

## 📂 Available Assets

*   **Asset 001: Unstructured to JSON** (Extracting order details from an email)
*   **Asset 002: CSV to YAML** (Reformatting a product catalog)
*   **Asset 003: Summary Extraction** (Condensing a report into 5 key bullets)

