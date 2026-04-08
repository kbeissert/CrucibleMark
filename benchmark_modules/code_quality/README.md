# Code Quality

> Bewertet, ob ein LLM Code wirklich *versteht* — nicht nur syntaktisch liest.
> Das Modul stellt fünf Code-Review-Aufgaben mit echter Fehlerdichte aus den
> Bereichen Accessibility, Security, Performance, API-Design und Code-Wartbarkeit.

**Modul-ID:** `code_quality` | **Klasse:** `CodeQualityTest` | **Version:** 0.2.0-beta
**Assets:** 5 | **Sprache:** Deutsch | **Scoring:** Hybrid (Regex + LLM-Judge)

---

## Warum dieses Modul?

Die entscheidende Frage ist: Unterscheidet das Modell zwischen „funktionierendem"
und „richtigem" Code? Ein SQL-Query kann syntaktisch korrekt sein und trotzdem
eine Injection-Lücke enthalten. Ein Button kann visuell sauber aussehen und
trotzdem WCAG 2.2 verletzen. Diese Lücke — zwischen Code, der läuft, und Code,
der korrekt ist — ist für reale Code-Reviews entscheidend.

Alle Assets enthalten Fehler in vier Kategorien:
- **Labeled**: Im Code als TODO/Kommentar markiert (offensichtlich)
- **Standard**: Bekannte Fehler ohne Markierung (z. B. OWASP Top 10)
- **Subtile**: Sprachspezifische oder logische Schwachstellen
- **Expert**: Architektonische Probleme mit tiefem Framework-Verständnis

Nur Modelle, die alle vier Kategorien erkennen, erzielen den Maximal-Score.

**Score-Contribution:** `routine: 0.0 / reasoning: 1.0` — Code-Review gilt
ausschließlich als Reasoning-Aufgabe.

---

## Scoring-Methodik

Standard-Fallback: `regex: 0.15 / judge: 0.85`.
Generation-Parameter: `temperature: 0.3, top_p: 0.9, num_predict: 8192`.

| Dimension | Gewicht | Beschreibung |
|---|---|---|
| **Fehler-Erkennung** | 60 % | Wie viele der eingebetteten Probleme werden korrekt identifiziert? Gestaffelt nach Kategorie: Labeled (25 Pkt.) → Standard (25 Pkt.) → Advanced (25 Pkt.) → Expert (25 Pkt.). Bonuspunkte für Extra-Findings bis +10 Pkt. |
| **Lösungsqualität** | 30 % | Sind vorgeschlagene Fixes korrekt und vollständig? Code-Validierung, semantische Ähnlichkeit zur Referenzlösung |
| **Formatierung & Expertise** | 10 % | Markdown-Struktur, WCAG/OWASP-Referenzen, klare Erklärungen |

---

## Test Assets

### `code_quality_001` — WCAG 2.2 Audit
```
Typ:       Accessibility Code Review (HTML/React)
Kontext:   Senior Frontend Developer mit WCAG 2.2 Zertifizierung.
           Review einer E-Commerce Produktkarten-Komponente,
           die Screen-Reader- und Keyboard-Probleme verursacht.
Input:     HTML-Komponente mit TODOs und versteckten ARIA-Fehlern.
           (sticky header ohne focus management, onclick statt button,
            fehlende alt-Texte, Badge ohne semantischen Kontext, u. v. m.)
Abgedeckte WCAG-Kriterien:
  - 1.1.1 Non-text Content (Alt-Texte)
  - 1.3.1 Info and Relationships (Semantik)
  - 2.1.1 Keyboard Accessible
  - 2.4.3 Focus Order
  - 2.4.11 Focus Not Obscured (NEU in 2.2)
  - 2.5.8 Target Size Minimum (NEU in 2.2)
  - 4.1.3 Status Messages
Scoring:   Tiered Difficulty: Labeled (25) + Standard (30) + Advanced (25) + Expert (20)
```

---

### `code_quality_002` — Security Audit
```
Typ:       Security Code Review (PHP Legacy)
Kontext:   Senior Security Engineer, Audit einer Legacy-PHP-Anwendung.
           Code enthält markierte UND versteckte Sicherheitslücken.
Input:     PHP-Code mit aktiviertem error_reporting (debug in prod),
           SQL-Queries, Authentifizierungs-Logik, E-Mail-Versand, Cookies.
Enthaltene Vulnerabilities:
  Explizit markiert (bestätigen):
    - SQL Injection (nicht parametrisierte Queries)
    - XSS (unkontrollierte Echo-Ausgaben)
  Implizit versteckt (eigenständig finden):
    - Mail Header Injection
    - User Enumeration (unterschiedliche Fehlermeldungen je Fehlertyp)
    - Unsafe Cookie-Konfiguration (kein HttpOnly/Secure)
    - Debug-Informationen in Production
    - Password-Handling ohne Hashing
Scoring:   Alle 7 Vulnerabilities müssen erkannt werden;
           Critical/High/Medium-Priorisierung wird bewertet.
```

---

### `code_quality_003` — Performance Audit
```
Typ:       Web Performance Review (HTML/JavaScript)
Kontext:   Performance Engineer, E-Commerce-Produktseite mit schlechten
           Core Web Vitals (LCP: 4.2s, CLS: 0.28).
Input:     HTML/JS-Code mit Performance-Problemen auf 3 Ebenen.
Enthaltene Probleme:
  Markiert:
    - Render-blocking Resources (synchrones CSS/JS im head)
    - Fehlende Bildoptimierung (kein lazy loading, keine modernen Formate)
  Standard:
    - Zu große JavaScript-Bundles (kein Code-Splitting)
    - Fehlende font-display Direktive
  Subtil:
    - JavaScript-basierende Layout Shifts (CLS durch dynamisches DOM)
    - N+1-ähnliche API-Calls im Frontend-Rendering
Scoring:   Priorisierung nach Core Web Vitals Impact (LCP/CLS/FID) wird bewertet.
```

---

### `code_quality_004` — REST API Design Audit
```
Typ:       API-Design Review (Python/Flask)
Kontext:   Senior Backend Engineer, Review eines Junior-Developer-Entwurfs.
           Code ist funktionstüchtig, verletzt aber REST-Prinzipien.
Input:     Flask-API-Endpunkte für ein Ressourcen-Management-System.
Enthaltene Design-Fehler:
  Markiert:
    - Falsche HTTP-Methoden (POST statt PUT/DELETE)
  Standard:
    - Fehlende Status-Codes (alles 200er)
    - Inkonsistente Ressourcen-Benennung (Verben in URLs)
  Subtil:
    - Fehlende Idempotenz bei Create-Operationen
    - Keine API-Versionierung
    - Sensible Daten in URL-Parametern statt Body/Header
Scoring:   REST-Prinzipien-Kenntnis über reine Syntax-Checks hinaus bewertet.
```

---

### `code_quality_005` — Code Smells Audit
```
Typ:       Code-Qualitäts-Review (JavaScript Legacy)
Kontext:   Senior Developer, Code-Review einer Legacy-UserManager-Komponente.
Input:     JavaScript-Klasse mit Wartbarkeitsproblemen auf 4 Ebenen.
Enthaltene Smells:
  Markiert (TODOs im Code):
    - Long Method (einzelne Methode >100 Zeilen)
    - Magic Numbers (hardcodierte Werte ohne Semantik)
  Standard:
    - God Object (eine Klasse verantwortlich für zu viel)
    - Duplicate Code
  Subtil:
    - Feature Envy (Methoden operieren hauptsächlich auf fremden Daten)
    - Excessive Coupling
  Expert:
    - Primitive Obsession
    - Shotgun Surgery (Änderung eines Konzepts erfordert viele Dateianpassungen)
Scoring:   Erkennungstiefe + Qualität der Refactoring-Vorschläge.
```

---

## Technischer Aufbau

Module in `core/`:

| Datei | Funktion |
|---|---|
| `evaluators.py` | Facade: orchestriert alle Sub-Evaluatoren |
| `error_detection.py` | Keyword- und Regex-basierte Fehlererkennung, Set-Lookup O(n) |
| `scoring_helpers.py` | Semantic Similarity (Sentence-Transformers), Code-Validierung, Markdown-Prüfung |
| `constants.py` | Similarity-Threshold: 0.78 (kalibriert gegen Mistral Large Golden Standard) |

---

## Konfiguration

```yaml
# config.yaml (Auszug)
generation:
  temperature: 0.3      # Niedrig: reproduzierbare analytische Antworten
  num_predict: 8192     # Erhöht für lange Code-Review-Outputs

scoring:
  fallback_weights:
    regex: 0.15
    judge: 0.85

integration:
  leaderboard:
    default_contribution:
      routine: 0.0
      reasoning: 1.0    # Zählt ausschließlich zum Reasoning-Score
```

---

## Token-Budget

Dieses Modul unterliegt dem **Token-Budget-System** (ab v3.4.0). Das Framework setzt einen direkten `max_tokens`-API-Parameter, um Provider-übergreifende Vergleichbarkeit sicherzustellen. Der Wert ist auf 2× Modul-Median kalibriert und wird von `base_runner.py` aus `benchmark_config.yaml` gelesen — unabhängig von der modulinternen `generation`-Config.

```yaml
# benchmark_config.yaml (Framework-Level)
token_budgets:
  code_quality: 6000    # 2× Modul-Median; long-form Code-Reviews brauchen Spielraum
```

Schöpft ein Modell das Budget vollständig aus (`finish_reason: length`), injiziert das Framework einen `> [!NOTE]`-Block ins Audit-Log (`benchmark_utils.py`). Score-Penalties für strukturell übermäßige Verbosity sind für v3.4.x geplant.
