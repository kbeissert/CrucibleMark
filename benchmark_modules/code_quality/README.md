# Code Quality Test Module

Dieses Modul bewertet die Fähigkeit von LLMs, Code-Reviews durchzuführen, Fehler zu finden und qualitativ hochwertige Verbesserungsvorschläge zu liefern. Es verwendet ein flexibles, Asset-basiertes System, das verschiedene Domänen der Softwareentwicklung abdeckt.

## 🏗 Architektur

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

## 🛠 Konfiguration neuer Assets

Neue Tests können einfach durch Erstellen einer YAML-Datei in `assets/` hinzugefügt werden. Die Scoring-Logik wird über das Feld `check_method` gesteuert.

### Verfügbare `check_method` Typen

| Methode | Beschreibung | Parameter |
| :--- | :--- | :--- |
| **`keyword_presence`** | Prüft, ob bestimmte Wörter im Text vorkommen. | `keywords` (Liste), `min_keywords` (Int) |
| **`regex`** | Prüft auf RegEx-Muster (z.B. für spezifische Formate). | `check_pattern` (Regex-String), `min_occurrences` (Int), `count_unique` (Bool) |
| **`code_validation`** | Zählt und validiert Code-Blöcke. | `required_elements` (Liste, z.B. `["\`\`\`php"]`), `min_code_blocks` (Int) |
| **`markdown_table_validation`** | Prüft auf Markdown-Tabellen. | `min_rows` (Int) |
| **`list_detection`** | Prüft auf Listen (Aufzählungszeichen). | `min_items` (Int), `section_keywords` (Liste) |
| **`context_awareness`** | Prüft auf Kontext-Verständnis (ähnlich Keyword). | `indicators` (Liste), `min_indicators` (Int) |

### Beispiel-Konfiguration (Auszug)

```yaml
solution_quality:
  criteria:
    - id: "SQ-001"
      name: "Prepared Statements genutzt"
      points: 8
      check_method: "regex"
      check_pattern: '(?i)(prepared.?statement|bind_param)'
      min_occurrences: 1

    - id: "SQ-002"
      name: "Code-Beispiele vorhanden"
      points: 5
      check_method: "code_validation"
      required_elements: ["```php"]
      min_code_blocks: 3
```

## 📂 Verfügbare Assets

| ID | Name | Fokus | Schwierigkeit |
| :--- | :--- | :--- | :--- |
| **001** | WCAG Accessibility Audit | Barrierefreiheit (HTML/CSS), WCAG 2.1/2.2 | Mittel |
| **002** | Security Audit | OWASP Top 10, PHP Vulnerabilities | **Tiered (1-3)** |
| **003** | Performance Audit | Core Web Vitals, Frontend-Optimierung | Mittel |
| **004** | API Design Audit | RESTful Principles, HTTP-Standards | Mittel-Hoch |
| **005** | Code Smells Audit | Clean Code, Refactoring, JS Legacy Code | Mittel |

## 🚀 Verwendung

### Über das Haupt-Skript (Empfohlen)

```bash
# Interaktiver Modus
python scripts/run_local_benchmark.py
```

### Manuelle Ausführung (Development)

```python
from benchmark_modules.code_quality.test import CodeQualityTest
from pathlib import Path

# Test laden
test = CodeQualityTest(Path("benchmark_modules/code_quality/assets/asset_001_wcag_audit.yaml"))

# Ausführen (benötigt LLM Client)
# result = test.execute("model_name", llm_client)
```
