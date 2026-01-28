# Code Quality Module

> **Technical Metadata**
> - **ID:** `code_quality`
> - **Namespace:** `benchmark_modules.code_quality`
> - **Class:** `CodeQualityTest` (inherits `BaseTest`)
> - **Version:** v0.9.5 (Deep Reasoning Optimized)
> - **Type:** Engineering & Static Analysis

## 🔍 Module Overview

Dieses Modul bewertet die Fähigkeit von LLMs, Code-Reviews durchzuführen, Fehler zu finden und qualitativ hochwertige Verbesserungsvorschläge zu liefern. Ein besonderer Fokus liegt auf **Deep Reasoning**: Können Modelle den Unterschied zwischen "funktionierendem" und "sicherem/barrierefreiem" Code erkennen?

---

## 🏗 Architektur & Härtung (Why it breaks models)

In der Optimierungsphase haben wir das Modul speziell gegen "Lazy Thinking" gehärtet. Frühere Iterationen ließen Modelle durchkommen, die generische "Best Practices" nannten. Die aktuelle Version (v0.9.5) erfordert **Kontext-Verständnis**.

### 1. Facade Pattern Implementation
Die Test-Logik (`test.py`) wurde in private Sub-Scorer refactored (Facade Pattern), um komplexe Bewertungen modular zusammenzusetzen:
- `_score_error_detection`: Sucht kritische Fehler.
- `_score_solution_quality`: Bewertet den Code-Fix.
- `_score_expertise`: Bonus-Punkte für Experten-Wissen (z.B. ARIA-Labels bei Accessibility).

### 2. <think> Tag Cleaning (DeepSeek Support)
Wir haben festgestellt, dass moderne "Reasoning Models" (wie DeepSeek R1) ihren Denkprozess in `<think>`-Tags ausgeben.
- **Problem**: Keywords im Denkprozess führten früher zu False Positives (Modell denkt über Fehler nach, behebt ihn aber im Output nicht).
- **Lösung**: Das Modul entfernt nun aktiv alle `<think>...</think>`-Blöcke *bevor* das Scoring beginnt. Nur der finale Output zählt.

### 3. Tiered Difficulty Scoring
Ähnlich wie bei *Documentation Quality* nutzen wir härtere Thresholds für Experten-Aufgaben:
- Asset 001 (WCAG Audit) bestraft generische Antworten ("Man sollte Alt-Tags nutzen") hart, wenn nicht konkret auf den Code eingegangen wird (`mandatory: true`).
- Die Unterscheidung zwischen **Minor Issues** (Nice to have) und **Critical Security Flaws** (Must catch) wird strikter geprüft.

---

## 🧪 Benchmark-Ablauf (Wie wird verglichen?)

Der Benchmark läuft strikt deterministisch ab:

1.  **Input**: Das Modell erhält einen fehlerhaften Code-Schnipsel (z.B. eine React-Komponente mit Maus-Events ohne Keyboard-Support).
2.  **Generierung mit Low Temp**: Temperature wird auf 0.1-0.3 gezwungen, um reproduzierbare, faktische Antworten zu erhalten.
3.  **Parsing & Scoring**:
    *   **Reasoning Strip**: Denk-Tags werden entfernt.
    *   **Keyword Scan**: Findet das Modell Begriffe wie `onKeyDown`, `aria-label`, `tabIndex`?
    *   **Negative Lookbehind**: Prüft, ob das Modell Fehler *behält* oder *falsch korrigiert*.
4.  **Resultat**: Ein Score von 0-100, wobei >90 nur erreicht wird, wenn Security AND Accessibility perfekt gelöst sind.

---

## 📂 Assets & Domänen (Beispiele)

*   **Asset 001: WCAG Audit (Accessibility)**
    *   Testet Button-Accessibility. Erfordert `onKeyDown` für Keyboard-Nutzer.
*   **Asset 002: Security Review**
    *   Testet auf SQL Injection, XSS oder unsichere Deps.
*   **Asset 003: Performance Optimization**
    *   Testet auf N+1 Queries oder unnötige Re-Renders.

### 🏗 Architektur (Legacy)

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

