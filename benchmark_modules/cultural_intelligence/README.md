# Cultural Intelligence Module

> **Technical Metadata**
> - **ID:** `cultural_intelligence`
> - **Namespace:** `benchmark_modules.cultural_intelligence`
> - **Class:** `CulturalIntelligenceTest` (inherits `BaseTest`)
> - **Evaluator:** `CulturalEvaluator`
> - **Version:** v1.0.0 (Clean Architecture)
> - **Type:** Nuance, Translation & Ethics

## 🔍 Module Overview

Dieses Modul testet das "Feingefühl" des Modells. Es geht über bloße Übersetzung hinaus und prüft, ob kulturelle Kontexte, Idiome und soziale Normen (Höflichkeit, Tabus) korrekt erkannt und adaptiert werden.

---

## 🏗 Architecture (Core/MVC)

This module follows the **Core/MVC** standard pattern enforced across the framework:

- **`test.py` (The Runner)**:
    - Provides scenarios with heavy cultural context (e.g., business etiquette in Japan vs. USA).
    - Delegates nuance analysis to `core/evaluators.py`.
- **`core/evaluators.py` (The Logic)**:
    - Contains `CulturalEvaluator`.
    - Uses **Lambda Scoring** (dynamic small functions to check specific nuance triggers).
    - Checks for **Stereotyping** via negative keyword lists.
- **`core/constants.py` (Configuration)**:
    - Definitions of "Cultural Markers" (e.g., bowing vs. handshaking).
    - Lists of offensive terms/tropes per region.
- **`assets/*.yaml` (Data)**:
    - Scenarios: Source culture, Target culture, and the "Situation".

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
