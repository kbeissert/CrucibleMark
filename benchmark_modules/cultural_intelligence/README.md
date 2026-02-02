# Cultural Intelligence Module

> **Technical Metadata**
> - **ID:** `cultural_intelligence`
> - **Namespace:** `benchmark_modules.cultural_intelligence`
> - **Class:** `CulturalIntelligenceTest` (inherits `BaseTest`)
> - **Evaluator:** `CulturalIntelligenceEvaluator`
> - **Version:** v2.0.0 (Modular Evaluators Architecture)
> - **Type:** Nuance, Translation & Ethics

## 🔍 Module Overview

Dieses Modul testet das "Feingefühl" des Modells. Es geht über bloße Übersetzung hinaus und prüft, ob kulturelle Kontexte, Idiome und soziale Normen (Höflichkeit, Tabus) korrekt erkannt und adaptiert werden.

---

## 🏗 Architecture (v2.0)

This module follows a modular architecture orchestrated by a Facade pattern:

```
core/evaluators/
├── __init__.py                    # CulturalIntelligenceEvaluator (Facade)
├── language_proficiency.py        # German markers, formality detection
├── cultural_fit.py                # Regional expressions, politeness
├── solution_quality.py            # Keyword-based quality checks
├── regional_validator.py          # Regional consistency checks (NEW)
└── formality_scorer.py            # Continuous formality scale (NEW)
```

## New Features (v2.0)

### Regional Consistency Validation
- Detects mixing of DE/AT/CH terms
- Example: "Brötchen" (DE) + "Semmel" (AT) = inconsistent

### Enhanced Formality Scoring
- Continuous scale (0.0-1.0) instead of binary Sie/Du
- Classifies: very_informal, informal, neutral, formal, very_formal

---

## 🧪 Scoring Logic

Scoring is subjective but automated via proxies (keywords and sentiment).

### 1. Nuance Detection
*   **Idiom Handling**: If the input uses "It's raining cats and dogs", a literal translation gets 0 points. An equivalent local idiom gets 100 points.
*   **Register (Tone)**: Checks if the model switches between "Du" and "Sie" (or equivalent honorifics) appropriately.

### 2. Cultural Adaptation (Localization)
*   **Units/Formats**: Does it convert Fahrenheit to Celsius if the target is Germany? ($ -> €).
*   **References**: Does it replace "baseball" with "football" if adapting a metaphor for Europe? (Context dependent).

### 3. Safety & Bias
*   **Stereotype Check**: Penalizes the usage of lazy cliches when describing a demographic.

---

## ⚙️ Configuration

In `benchmark_modules/cultural_intelligence/core/constants.py`:

*   **`SENSITIVITY_LEVEL`**: High/Low. High sensitivity penalizes even minor micro-aggressions.
*   **`LOCALE_MAPPINGS`**: Rules for unit conversions and date formats.

---

## 📂 Available Assets

*   **Asset 001: Email Etiquette** (Refusing a request: German Directness vs. British Politeness)
*   **Asset 002: Idiom Translation** (Translating proverbs without losing meaning)
*   **Asset 003: Taboo Check** (Handling topics considered sensitive in target cultures)
