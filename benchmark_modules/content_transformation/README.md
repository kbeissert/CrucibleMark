# Content Transformation & Adaption Module

Dieses Modul bewertet die Fähigkeit von LLMs, Inhalte von einem Format in ein anderes zu transformieren und dabei Stil, Tonalität und Struktur anzupassen.

## Übersicht

- **Ziel:** Testen von Kreativität, Anpassungsfähigkeit und Einhaltung von Formatvorgaben.
- **Methodik:** Tiered Difficulty Scoring (Labeled -> Expert Issues) + Solution Quality.
- **Assets:** 5 Szenarien (Landing Page, Twitter Thread, Glossar, Video Script, Newsletter).

## Kategorien

1. **Structure & Format (25%)**: Einhaltung des Zielformats (z.B. Thread-Struktur, Script-Timing).
2. **Content Quality & Clarity (25%)**: Informationsdichte, Verständlichkeit.
3. **Engagement & Emotion (25%)**: Emotionaler Hook, Storytelling.
4. **Conversion & Actionability (25%)**: Call-to-Action, Nutzenargumentation.

## Scoring

Das Scoring basiert auf zwei Hauptkomponenten (Total: 100 Punkte):

1. **Error Detection / Constraint Adherence (40 Punkte)**
   - Prüft, ob das Modell die Transformations-Regeln einhält und typische Fehler vermeidet.
   - Unterteilt in 4 Schwierigkeitsstufen (Labeled, Standard, Advanced, Expert).

2. **Solution Quality (60 Punkte)**
   - Bewertet die Qualität des generierten Outputs anhand von Keywords und Best Practices.
   - Fokus auf Benefit-Clarity, Structure und Engagement.

## Assets

| ID | Name | Transformation | Difficulty |
|----|------|----------------|------------|
| 001 | Landing Page Copy | Feature List -> Hero Section | Tiered |
| 002 | Social Media Thread | Blogpost -> Twitter Thread | Tiered |
| 003 | Glossary Simplification | Jargon -> Plain Language | Tiered |
| 004 | Video Script | Outline -> Spoken Word Script | Tiered |
| 005 | Newsletter Adaptation | Case Study -> Email | Tiered |
