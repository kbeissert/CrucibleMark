# Code Quality Module

> **Technical Metadata**
> - **ID:** `code_quality`
> - **Namespace:** `benchmark_modules.code_quality`
> - **Class:** `CodeQualityTest` (inherits `BaseTest`)
> - **Version:** 0.9.0-rc
> - **Type:** Engineering & Static Analysis

## 🔍 Module Overview

Dieses Modul bewertet die Fähigkeit von LLMs, Code-Reviews durchzuführen, Fehler zu finden und qualitativ hochwertige Verbesserungsvorschläge zu liefern. Es verwendet ein flexibles, Asset-basiertes System, das verschiedene Domänen der Softwareentwicklung abdeckt.

### 🏗 Architektur

Das Modul trennt strikt zwischen Test-Logik (`test.py`) und Test-Daten (`assets/*.yaml`).

*   **`test.py`**: Die generische Test-Engine. Sie lädt ein YAML-Asset, führt den Prompt gegen das LLM aus und bewertet die Antwort basierend auf den im Asset definierten Regeln.
*   **`assets/*.yaml`**: Definieren den Kontext, den Prompt, den zu analysierenden Code und die spezifischen Scoring-Regeln.

## 📊 Scoring-System

Jeder Test ist in 3 Gewichtungskategorien unterteilt (Total: 100 Punkte):

1.  **Error Detection (60 Punkte)**:
    *   Erkennt das Modell die versteckten Fehler/Issues im Code?
    *   **Dynamische Kategorien**: Unterstützt gestaffelte Schwierigkeitsgrade (z.B. *Labeled*, *Standard*, *Advanced*, *Expert*).
    *   Bewertung durch Keyword-Matching und Schwellenwerte.

2.  **Solution Quality (30 Punkte)**:
    *   Sind die Lösungsvorschläge korrekt und hilfreich?
    *   Werden Best Practices (z.B. `defer/async`, `Prepared Statements`) genannt?
    *   Sind Code-Beispiele syntaktisch korrekt?

3.  **Formatting (10 Punkte)**:
    *   Ist die Ausgabe gut strukturiert (Markdown)?
    *   Werden Tabellen, Header und Code-Blöcke korrekt verwendet?

## 🧠 Schwierigkeits-Level (Tiered Difficulty)

Um die Spreu vom Weizen zu trennen, nutzen fortgeschrittene Assets (wie `asset_002_security_audit`) ein gestaffeltes System:

*   **Level 1: Labeled Issues (Einfach)**
    *   Fehler sind im Code explizit markiert (z.B. `// ISSUE: SQL Injection`).
    *   Testet die Fähigkeit, Anweisungen zu folgen und einfache Fixes zu generieren.
    *   *Jedes Modell sollte hier punkten.*

*   **Level 2: Standard Issues (Mittel)**
    *   Klassische Fehler (z.B. OWASP Top 10), die nicht markiert sind.
    *   Testet solides Basiswissen und Mustererkennung.
    *   *Gute Modelle finden diese zuverlässig.*

*   **Level 3: Advanced / Hidden Issues (Schwer)**
    *   Subtile Logikfehler, sprachspezifische Eigenheiten (z.B. PHP Type Juggling, Weak Randomness) oder Konfigurationsfehler.
    *   Testet tiefes Code-Verständnis und Expertenwissen.
    *   *Nur Spitzen-Modelle finden diese Fehler.*

## 📂 Verfügbare Test-Assets

| ID | Name | Focus Area | Difficulty |
|----|------|------------|------------|
| 001 | **WCAG Accessibility** | HTML Structure, ARIA, Semantics | Tiered (1-4) |
| 002 | **Security Audit** | OWASP Top 10, Injection, Auth | Tiered (1-4) |
| 003 | **Performance Audit** | Big O, Loops, Memory Leaks | Tiered (1-4) |
| 004 | **API Design** | RESTful Principles, Status Codes | Tiered (1-4) |
| 005 | **Code Smells** | Clean Code, DRY, SOLID | Tiered (1-4) |

