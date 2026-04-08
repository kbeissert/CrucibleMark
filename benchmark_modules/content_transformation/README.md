# Content Transformation

> Bewertet, ob ein LLM Inhalte format- und zielgruppengerecht transformieren
> kann — ohne den Kerninhalt zu verfälschen. Das Modul prüft sechs Szenarien
> aus Marketing, technischem Schreiben und professioneller Kommunikation.

**Modul-ID:** `content_transformation` | **Klasse:** `ContentTransformationTest` | **Version:** 1.0.0
**Assets:** 6 | **Sprache:** Deutsch (teilweise EN) | **Scoring:** Hybrid (Regex + LLM-Judge)

---

## Warum dieses Modul?

Content Transformation ist mehr als Umschreiben. Jedes Zielformat hat eigene
strukturelle und tonale Anforderungen, die ein Modell kennen und einhalten muss:
Ein Twitter-Thread ohne Nummerierung ist falsches Format. Eine Landing Page ohne
CTA ist eine verpasste Opportunity. Ein Incident Report mit durchschimmerndem
Sarkasmus ist inakzeptabel in B2B-Kommunikation. Das Modul testet, ob Modelle
diese Anforderungen ohne explizite Vorgabe erkennen und umsetzen.

Assets 001–005 erzwingen `language: de`. Asset 006 ist auf Englisch
(typischer Business-Kommunikationskontext in internationalen Teams).
Wortlimit-Constraints (Assets 003, 004) sind harte Bewertungskriterien.

---

## Scoring-Methodik

Standard-Fallback: `regex: 0.20 / judge: 0.80`.

| Dimension | Gewicht | Beschreibung |
|---|---|---|
| **Fehler-Erkennung** | 70 % | Erkennt das Modell die Transformations-Anforderungen? Gestaffelt: Labeled → Expert |
| **Lösungsqualität** | 30 % | Kreativität, Format-Compliance, Actionability, Professionalität |

Score-Contribution: `routine: 1.0 / reasoning: 0.0` (alle Assets).

---

## Test Assets

### `content_transformation_001` — Landing Page Hero
```
Typ:       Feature-Liste → konversionsorientierte Hero-Section
Kontext:   Conversion Copywriter für B2B-SaaS "TaskFlow Pro".
           Problem: Aktuelle TP ist feature-lastig, kein Nutzen kommuniziert.
Input:     5 Feature-Bullet-Points (Unlimited Projects, Real-time Collaboration,
           Analytics Dashboard, 99.9% Uptime SLA, SOC 2 Type II)
Aufgabe:   Zweistufig: [1] Analyse (warum funktioniert Feature-Liste nicht?),
           [2] Hero-Section erstellen.
Anforderungen:
  - Headline: Hauptnutzen emotional kommuniziert, keine reinen Features
  - Subheadline: Erklärt wie das Produkt Headline einlöst
  - CTA: Handlungsorientierter Button-Text (nicht "Submit")
  - Social Proof/Trust-Element integriert (aus SLA/Security-Features)
  - Risk Reversal integriert (z. B. No-Risk-Garantie)
Scoring:   Format-Validierung (Sections vorhanden) + Judge für Conversion-Qualität
```

---

### `content_transformation_002` — Twitter Thread
```
Typ:       Blog-Artikel → viraler Twitter-Thread (1/x-Format)
Kontext:   Social Media Strategist, Tech-Startup-Kunden.
           Blogpost "Why Async Communication Beats Meetings" hat schlechte
           Social-Media-Performance trotz gutem Inhalt.
Input:     300-Wörter-Ausschnitt des Blogposts
Anforderungen:
  - Sequenzielle Nummerierung: "1/5" bis "5/5" (strikt, per Regex geprüft)
  - Max. 280 Zeichen pro Tweet
  - Engagement-Hook im ersten Tweet
  - Expert-Level: Open Loops (Cliffhanger), Engagement Question am Ende
Scoring:   Nummerierung + Zeichenlimit per Regex; Virality-Potential per Judge
```

---

### `content_transformation_003` — Glossary Simplification
```
Typ:       Fachvokabular-Vereinfachung (Juristisch → Alltagssprache)
Input:     Juristische Fachbegriffe (z. B. "Kontradiktorisches Verfahren",
           "Dispositionsmaxime", "Rechtskraft")
Aufgabe:   Je Begriff: vereinfachte Erklärung in max. X Wörtern
           (Wortlimit ist Teil der Aufgabenstellung)
Scoring:   Vereinfachung geprüft (keine Fachbegriffe im Output) +
           Wortlimit per Regex validiert + inhaltliche Korrektheit per Judge
```

---

### `content_transformation_004` — Video Script Tutorial
```
Typ:       Tutorial → gesprochenes Video-Script
Kontext:   Technisches Tutorial (schriftlich) soll zu
           einem natürlich wirkenden Erklärfilm-Script werden.
Anforderungen:
  - Kurze Sätze (Sprechrhythmus)
  - Direkte Ansprache (du/Sie je nach Kontext)
  - Pausen-Markierungen (z. B. "[Pause]", "[Screenshot zeigen]")
  - Konversationeller Ton, keine "Prosa-Blöcke"
Scoring:   Strukturelle Markers per Regex + Ton-Analyse per Judge
```

---

### `content_transformation_005` — Newsletter Adaptation
```
Typ:       Corporate-Text → Newsletter (engagierend, persönlich)
Input:     Formeller Corporate-Fließtext
Anforderungen:
  - Betreffzeile vorhanden
  - Persönliche Ansprache
  - Klarer CTA
  - Keine Passivsätze
Scoring:   Struktur-Elemente per Regex + Ton per Judge
```

---

### `content_transformation_006` — Sarcasm Shield
```
Typ:       Sarkastische Slack-Nachricht → formeller Incident Report
Kontext:   Communications Lead, schreibt Bericht für CTO.
Input:     "Great job deploying on Friday, geniuses. The real-time database
           is now as consistent as my horoscope. And the latency spikes are
           so high I had time to make a coffee while waiting for the dashboard
           to load. We need to rollback the 'optimization' before the customers
           wake up."
Aufgabe:
  1. Sarkasmus und passiv-aggressiven Ton vollständig entfernen
  2. Technische Fakten beibehalten
  3. Metaphern korrekt interpretieren ("horoscope" = unzuverlässig/random)
  4. Vollständig professionellen Ton
Scoring:   Professionalismus-Score muss > 0.8 liegen.
           Verbleibende sarkastische Elemente → Penalty.
           Sachliche Fakten beibehalten → positive Bewertung.
Sprache:   Englisch (asset-seitig; Kontext ist internationales Team)
```

---

## Technischer Aufbau

Sub-Evaluatoren in `core/evaluators/`:

| Klasse / Datei | Aufgabe |
|---|---|
| `TieredScoringEngine` (`tiered_scoring.py`) | Labeled → Expert Hybrid-Matching |
| `FormatValidator` (`format_validator.py`) | Twitter-Nummerierung, Landing-Page-Sections |
| `ToneEvaluator` (`tone_evaluator.py`) | Formalitätsskala 0,0–1,0, Professionalismus-Score |
| `ContentQualityEvaluator` (`content_quality.py`) | Kreativität, Actionability |
| `SemanticMatcher` (`semantic_matcher.py`) | Sentence-Transformer-Fallback |

---

## Konfiguration

```yaml
# config.yaml (Auszug)
config:
  categories:
    structure_format:
      weight: 0.25
    content_quality:
      weight: 0.35
    tone_style:
      weight: 0.25
    solution_effectiveness:
      weight: 0.15

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
  content_transformation: 3500    # 2× Modul-Median
```

Schöpft ein Modell das Budget vollständig aus (`finish_reason: length`), injiziert das Framework einen `> [!NOTE]`-Block ins Audit-Log (`benchmark_utils.py`). Score-Penalties für strukturell übermäßige Verbosity sind für v3.4.x geplant.
