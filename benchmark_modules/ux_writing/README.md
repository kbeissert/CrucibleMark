# UX Writing

> Bewertet, ob ein LLM Microcopy schreiben kann — präzise, handlungsleitend
> und empathisch. Das Modul prüft fünf UX-Writing-Aufgaben mit realen
> Interface-Szenarien aus E-Commerce, Enterprise und Health.

**Modul-ID:** `ux_writing` | **Klasse:** `UXWritingTest` | **Version:** 1.0.0
**Assets:** 5 | **Sprache:** Deutsch (erzwungen) | **Scoring:** Hybrid (Regex + LLM-Judge)

---

## Warum dieses Modul?

UX Writing ist eine der praktisch relevantesten Schreibdisziplinen für
Software-Produkte: Fehlermeldungen, Button-Labels und Onboarding-Texte
beeinflussen direkt die Nutzbarkeit eines Produkts. Viele LLMs produzieren
grammatikalisch korrekte, aber für echte Nutzer unbrauchbare Texte —
zu technisch, zu vage, ohne Handlungsaufforderung. Dieses Modul testet das
in kontextspezifischen Szenarien mit echten Designproblemen als Input.

Alle Assets sind so konstruiert, dass sie einen **mehrstufigen Prozess** erfordern:
Erst Analyse der Probleme, dann Lösung. Modelle, die direkt zur Lösung springen
ohne Analyse, erhalten einen Punktabzug.

**Language Compliance:** `language: de` für alle Assets.
**Scoring:** `regex: 0.10 / judge: 0.90` — UX-Tonalität und Empathie lassen sich
nicht zuverlässig per Keyword messen. Der LLM-Judge bewertet gegen definierte Rubriken.

---

## Scoring-Methodik

Gewichtungsschema: **60/30/10**

| Dimension | Gewicht | Beschreibung |
|---|---|---|
| **Fehler-Erkennung** | 60 % | Findet das Modell die UX-Probleme im Input? Gestaffelt: Labeled → Standard → Advanced → Expert |
| **Lösungsqualität** | 30 % | Ist die vorgeschlagene Lösung tatsächlich besser? Ton, Struktur, Handlungsleitend |
| **Formatierung** | 10 % | Korrekte Markdown-Tabellenstruktur mit allen geforderten Spalten |

Score-Contribution im Leaderboard: `routine: 1.0 / reasoning: 0.0` (alle Assets).

---

## Test Assets

### `ux_writing_001` — Error Messages
```
Typ:       Fehlermeldungs-Rewrite (technisch → nutzerfreundlich)
Kontext:   Senior UX Writer für eine E-Commerce-Plattform.
           Zielgruppe: Durchschnittliche Online-Käufer (kein Tech-Wissen).
Input:     6 technische Fehlermeldungen (z. B. "Error: Database connection timeout
           (code: ETIMEDOUT)", "Authentication failed: JWT token expired")
Aufgabe:   Markdown-Tabelle: Original | Verbesserung | Begründung.
           Analyse zuerst (3–4 Sätze), dann Tabelle.
Anforderungen:
  - Technischen Jargon vollständig entfernen (Error Codes, Variablennamen)
  - Konkrete Handlungsanweisung in jeder Verbesserung
  - Keine Schuldzuweisung ("Du hast falsch eingegeben" = Fehler)
  - Jede Begründung nennt das angewendete UX-Prinzip
  - Expert-Level: Erkennt Dead Ends und fehlende Empathie in Standardfloskeln
Scoring:   Tiered Issue Detection (Labeled → Basic → Standard → Expert)
```

---

### `ux_writing_002` — Button Labels
```
Typ:       CTA-Optimierung (Call-to-Action, kontext-sensitiv)
Kontext:   UX Writer, spezialisiert auf Conversion-Optimierung.
           6 Kontexte: E-Commerce, Newsletter, Enterprise SaaS,
           Banking, Health App, Mobile Game.
Input:     4 konkrete Szenarien mit problematischen Button-Labels
           (z. B. "OK" bei €234,50 Checkout, 117-Zeichen-Newsletter-Button,
            "Upload" für Vertragsupload, "Löschen" ohne Kontext)
Aufgabe:   Zweistufig: [SCHRITT 1] Analyse der Schwächen (3–4 Sätze),
           [SCHRITT 2] Markdown-Tabelle: Szenario | Original | Optimierung | Begründung.
Anforderungen:
  - MAXIMAL 25 Zeichen pro Label (Mobile-First-Constraint)
  - Starkes aktives Verb am Anfang
  - Tonalität exakt zum beschriebenen Kontext
  - Expert-Level: Conversion-Hypothese begründen
Scoring:   Tiered; 25-Zeichen-Constraint per Regex geprüft
```

---

### `ux_writing_003` — Onboarding Flow
```
Typ:       Onboarding-Überarbeitung (5-Schritt-Flow)
Kontext:   Senior UX Writer für eine Projektmanagement-SaaS.
           Feature "Automatische Workflows" soll für nicht-technische PM zugänglich sein.
           Problematisch: Kognitive Überlastung, technischer Jargon (Trigger/Conditions/
           Actions, IF/THEN, Task.Priority == 'Hoch').
Aufgabe:   5-stufigen Onboarding-Text überarbeiten: Progressive Disclosure,
           kein Tech-Jargon, klare Fortschrittsmarkierung.
Scoring-Rubrik (4×25 Punkte):
  1. Struktur-Compliance (alle geforderten Sections vorhanden)
  2. Inhaltliche Vollständigkeit (Abdeckung aller Anforderungen)
  3. Beispiel-Qualität (konkrete, logische Beispiele vs. generisches Blabla)
  4. Ton/Sprache (Zielgruppe PM ohne Programmierkenntnisse)
```

---

### `ux_writing_004` — Accessibility Labels
```
Typ:       ARIA-Label-Optimierung (Screen-Reader-Texte)
Kontext:   UX Writer mit Accessibility-Expertise für Enterprise-Dashboard.
           Zielgruppe: Screen-Reader-Nutzer (NVDA, JAWS, VoiceOver).
Input:     6 UI-Elemente mit problematischen ARIA-Labels
           (Icon-Button ohne Label, Filter-Dropdown mit technischem ID als Label,
            Suchfeld mit redundantem Label, Dark-Mode-Toggle ohne Zustandsinfo,
            Pagination ohne Kontext, Live-Ticker ohne aria-live)
Anforderungen:
  - Funktion beschreiben, nicht Aussehen ("Löschen" nicht "Mülleimer")
  - Keine Redundanz (nicht "Button" im Label wiederholen)
  - Zustandsinformationen wo nötig
  - Expert: aria-pressed, aria-expanded, aria-live korrekt einsetzen
Scoring:   required_ratio: 1.0 — WCAG-Konformität ist Pflicht, nicht Optional
           (alle 6 Elemente müssen korrekt sein)
```

---

### `ux_writing_005` — Microcopy Audit
```
Typ:       Umfassender Microcopy-Audit (Health App)
Kontext:   Senior UX Writer, Medikamenten-Management-App.
           Zielgruppe: Ältere Nutzer (60+), chronisch Kranke.
           Tone of Voice: empathisch & beruhigend, klar & sicher, respektvoll.
Input:     4 Screens mit problematischer Microcopy
           (Dosierungs-Input mit Mehrdeutigkeit, alarmierende Push-Notification
           "Medikament fällig!", Schuldzuweisung bei vergessener Einnahme,
            Empty State ohne klare Handlungsanweisung)
Anforderungen:
  - Medizinische Angaben müssen absolut eindeutig sein
  - Keine alarmierenden Begriffe ("fällig", "verpasst", "Warnung")
  - Wortlimit: max. 150 Wörter pro Label
  - Expert: terminologische Konsistenz über alle Screens prüfen
Scoring:   Tiered; Wortlimit per Regex validiert
```

---

## Technischer Aufbau

Evaluatoren in `core/evaluators/`:

| Klasse / Datei | Aufgabe |
|---|---|
| `EvaluatorFactory` (`factory.py`) | Dispatch: Kriteriumstyp → zuständiger Evaluator |
| `KeywordEvaluator` (`keyword.py`) | `keyword_presence`, `keyword_absence` — Set-Lookup O(n) |
| `StructureEvaluator` (`structure.py`) | `regex`, `code_block`, `markdown_table` |
| `ValidationEvaluator` (`validation.py`) | `length_validation`, WCAG-Regex-Fallback |
| `IssueEvaluator` (`base.py`) | String-Matching + semantische Ähnlichkeit (Sentence-Transformers) |

Weitere Dienste: `services.py` (Aggregation), `io_manager.py` (YAML-Parsing),
`models.py` (Dataclasses), `constants.py` (Thresholds).

---

## Konfiguration

```yaml
# config.yaml (Auszug)
scoring:
  fallback_weights:
    regex: 0.10
    judge: 0.90

integration:
  leaderboard:
    columns:
      - id: "ux_writing_score"
        label: "UX Writing & Microcopy"
        weight: 1.0
```

```python
# core/constants.py (Auszug)
SIMILARITY_THRESHOLD = 0.78   # Sentence-Transformer Cosine-Ähnlichkeit
WCAG_REQUIRED_RATIO = 1.0     # Asset 004: alle Kriterien müssen erfüllt sein
BUTTON_LABEL_MAX_CHARS = 25   # Asset 002: Mobile-First-Constraint
```
