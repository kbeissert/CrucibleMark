# Cultural Intelligence

> Bewertet, ob ein LLM kulturelle Kontexte wirklich versteht — nicht nur übersetzt.
> Im Mittelpunkt steht die Fähigkeit, sprachliche Register, regionale Konventionen
> und soziokulturelle Feinheiten korrekt zu treffen.

**Modul-ID:** `cultural_intelligence` | **Klasse:** `CulturalIntelligenceTest` | **Version:** 2.0.0
**Assets:** 5 | **Sprache:** Deutsch (erzwungen) | **Scoring:** Hybrid (Regex + LLM-Judge)

---

## Warum dieses Modul?

Sprachliche Korrektheit und kulturelle Angemessenheit sind zwei verschiedene Dinge.
Ein Modell kann grammatikalisch einwandfreies Deutsch schreiben und dabei trotzdem
den falschen Ton treffen, unpassende Idiome wählen oder Regionen-Varianten mischen.
Für reale Anwendungsfälle — Content-Lokalisierung, Kundenservice, HR-Kommunikation —
ist beides erforderlich. Dieses Modul misst die Lücke zwischen „korrekt übersetzt"
und „kulturell passend".

**Language Compliance:** Alle Assets erzwingen `language: de`. Deutschsprachige
Antworten werden nach inhaltlicher Qualität bewertet; Antworten in anderen Sprachen
gelten unabhängig vom Inhalt als nicht-konform und erhalten einen gewichteten Abzug
(`language_weight: 0.20`).

---

## Scoring-Methodik

Jedes Asset wird mit einem **Hybrid-Score** (Regex/Keyword-Check + LLM-Judge)
bewertet. Der Standard-Fallback ist `regex: 0.20 / judge: 0.80`. Assets mit
stark subjektivem Inhalt (z. B. kreative Tonalität in Asset 003) verwenden
`regex: 0.10 / judge: 0.90`.

Der LLM-Judge bewertet nach einem definierten Rubrik-System mit vier Dimensionen:

| Dimension | Gewicht | Beschreibung |
|---|---|---|
| **Kulturelle Adaption** | 40 % | Ton, Register, kulturelle Erwartungen des Zielpublikums |
| **Sprachliche Kompetenz** | 30 % | Grammatik, idiomatische Flüssigkeit, native-wirkende Formulierungen |
| **Lösungsqualität** | 30 % | Vollständigkeit, Keyword-Übereinstimmung mit Golden Standard |

Bonuspunkte (bis +10) für das aktive Erkennen und Vermeiden kultureller Stereotypen.

**Golden Standards:** Für jedes Asset existiert ein `golden_standard`-Feld im YAML
mit einer Referenzantwort und expliziten Begründungen zu stilistischen Entscheidungen.
Der LLM-Judge erhält diese Referenz, jedoch nicht das Modell selbst — bewusste
Trennung von Training-Signal und Bewertungsgrundlage.

**Score-Contribution im Leaderboard:**
- Assets 001, 004, 005 → `routine: 1.0 / reasoning: 0.0`
- Asset 002 → `routine: 0.5 / reasoning: 0.5`
- Asset 003 → `routine: 0.4 / reasoning: 0.6`

---

## Test Assets

### `cultural_intel_001` — German Tech Localization
```
Typ:       Fachübersetzung (Developer-Changelog EN → DE)
Schwierigkeitsgrad: Tier 3
Input:     Englischer Changelog-Text mit 10 Tech-Anglizismen
           (push, commit, remote, repository, merge, build, issue, branch, pull, cache)
Aufgabe:   Übersetze in natürliches deutsches Entwickler-Deutsch.
           Anglizismen sollen beibehalten werden, wo sie im DE-Kontext Standard sind.
Scoring:   10-Punkt-Glossar-Check: Je Anglizismus wird geprüft, ob korrekte
           deutsche Grammatik (Artikel, Konjugation) angewendet wurde.
           Beispiel: "pushen" ✓ — "push" ✗ (nicht konjugiert)
```
*Warum:* Zeigt, ob ein Modell zwischen "blinder Beibehaltung" und "sinnvollem
Einbetten" von Anglizismen in deutschen Text unterscheiden kann — ein häufiges
Praxisproblem in Dev-Teams.

---

### `cultural_intel_002` — Inclusive Job Ad
```
Typ:       Text-Rewrite (exklusive → inklusive Stellenanzeige)
Schwierigkeitsgrad: Tier 3
Input:     Englischer Stellenanzeigen-Ausschnitt mit 10 problematischen Begriffen
           (5 toxische Ausdrücke: "Ninja", "kill the competition", "manly courage" etc.
            5 geschlechtsspezifische Begriffe: "Craftsman", "Manpower", "guy" etc.)
Aufgabe:   Umschreiben in inklusives, professionelles Deutsch.
Scoring:   10-Punkt-Check — je entfernter toxischer/gendered Begriff: +10 Pkt.
           Prüft, ob alle Probleme erkannt UND korrekt gelöst wurden.
```
*Warum:* Inklusive Sprache in HR-Texten ist ein zentrales Praxisthema im
deutschsprachigen Raum. Modelle, die Anglizismen unkritisch übernehmen oder
stereotyp-beladene Begriffe nicht erkennen, scheitern hier.

---

### `cultural_intel_003` — Berlin Agency Vibe
```
Typ:       Tonalitäts-Umschreibung (Korporat-Sprache → Berliner Agentur-Ton)
Schwierigkeitsgrad: Tier 3
Input:     Englischer Text mit 10 Corporate-Buzzwords
           ("holistic ecosystem", "synergy", "paradigm-shift", "gamechanger",
            "deep-dive", "next-level", "disruptive", "360-degree", "drive", "solutions")
Aufgabe:   Umschreiben in authentisches Berliner Agentur-Deutsch (Du-Tonalität,
           kurze Sätze, direkter Stil — keine aufgesetzte Kreativ-Sprache).
Scoring:   10-Punkt-Penalty-Check: +10 für jeden entfernten Buzzword.
           Judge bewertet zusätzlich Authentizität des Zieltexts.
Scoring-Gewichtung: regex: 0.10 / judge: 0.90 (Ton ist schwer per Keyword messbar)
```
*Warum:* Demonstriert Register-Bewusstsein. Ein typischer Fehler ist, alte
Buzzwords durch neue zu ersetzen (z. B. "holistisch" statt "holistic"). Modelle
müssen echte stilistische Transformation leisten.

---

### `cultural_intel_004` — Formal vs. Informal German
```
Typ:       Register-Wechsel (Sie → Du in Kundenservice-E-Mail)
Schwierigkeitsgrad: Tier 2
Input:     Formelle Kundenservice-E-Mail auf Deutsch (Sie-Form)
Aufgabe:   Vollständig in informelle Du-Tonalität umschreiben,
           alle Sachinformationen beibehalten.
Scoring:   10-Punkt-Register-Check (Sie/Ihr → du/dein konvertiert,
           Anrede, Grußformel, Verben, Pronomen).
```
*Warum:* Die Sie/Du-Grenze ist im deutschen Geschäftsleben kulturell signifikant.
Viele Modelle machen inkonsistente Wechsel (z. B. "Du"-Anrede aber weiterhin
"Ihre Anfrage") — diese werden erkannt und bewertet.

---

### `cultural_intel_005` — German Idioms
```
Typ:       Idiom-Übersetzung (EN → DE, kulturell äquivalent)
Schwierigkeitsgrad: Tier 3
Input:     Englischer Business-Text mit 6 Idiomen
           ("went south", "think outside the box", "game plan",
            "touch base", "get the ball rolling", "drop the ball")
Aufgabe:   Idiome durch authentische deutsche Äquivalente ersetzen —
           keine wörtlichen Übersetzungen (z. B. "ging nach Süden" = Fehler).
Scoring:   12-Punkt-Check (6 Idiome × 2 Pkt. je):
           Je Idiom: +1 für Erkennung, +1 für korrekte DE-Alternative.
```
*Warum:* Wörtliche Idiom-Übersetzungen sind ein häufiges LLM-Muster und ein
deutliches Qualitätsmerkmal. Erwartet werden z. B. "den Bach runtergehen",
"über den Tellerrand schauen", "die Sache ins Rollen bringen".

---

## Technischer Aufbau

Evaluatoren in `core/evaluators/`:

| Klasse | Datei | Aufgabe |
|---|---|---|
| `LanguageProficiencyEvaluator` | `language_proficiency.py` | Grammatik, Vokabular |
| `CulturalFitEvaluator` | `cultural_fit.py` | Idiome, Höflichkeitsnormen |
| `SolutionQualityEvaluator` | `solution_quality.py` | Keyword-Matching, Vollständigkeit |
| `RegionalValidator` | `regional_validator.py` | Kein Mischen von DE/AT/CH |
| `FormalityScorer` | `formality_scorer.py` | Formalitätsskala 0,0–1,0 |

Konfiguration in `core/constants.py`.
Vollständige Asset-Definitionen inkl. Golden Standards in `assets/`.

---

## Konfiguration

```yaml
# config.yaml (Auszug)
config:
  temperature: 0.5
  top_p: 0.7
  scoring:
    pass_threshold: 0.7

scoring:
  fallback_weights:
    regex: 0.20
    judge: 0.80
```

---

## Token-Budget

Dieses Modul unterliegt dem **Token-Budget-System** (ab v3.4.0). Das Framework setzt einen direkten `max_tokens`-API-Parameter, um Provider-übergreifende Vergleichbarkeit sicherzustellen.

```yaml
# benchmark_config.yaml (Framework-Level)
token_budgets:
  cultural_intelligence: 500    # 2× Modul-Median; bewusst eng — präzise Kulturanpassungen erfordern keine Romane
```

Das Budget von 500 Tokens ist das engste im gesamten Framework und spiegelt die erwartete Antwortlänge bei fokussierten Lokalisierungsaufgaben wider. Modelle, die dieses Budget regelmäßig ausschöpfen, werden durch den `> [!NOTE]`-Block im Audit-Log markiert. Die Token-Effizienz-Ratio fließt ab v3.4.0 in die Meta-Reviewer-Analyse ein.
