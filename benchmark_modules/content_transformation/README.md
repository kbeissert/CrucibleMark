# Content Transformation & Adaption Module

> **Technical Metadata**
> - **ID:** `content_transformation`
> - **Namespace:** `benchmark_modules.content_transformation`
> - **Class:** `ContentTransformationTest` (inherits `BaseTest`)
> - **Version:** v0.9.5 (Optimized)
> - **Type:** Creative Writing & Adaptation

## 🔍 Module Overview

Dieses Modul bewertet die Fähigkeit von LLMs, Inhalte von einem Format in ein anderes zu transformieren und dabei Stil, Tonalität und Struktur anzupassen. Es prüft, ob Modelle den Kern einer Botschaft verstehen und ihn zielgruppengerecht (z.B. als Landing Page oder Video Script) neu verpacken können, ohne zu halluzinieren oder den Ton zu verfehlen.

---

## 🏗 Architektur & Scoring-Logik (v0.9.x Update)

Nach intensiven Tests mit Qwen 2.5, DeepSeek V3 und lokalen Modellen (Dolphin) zeigte sich, dass "semantische Nähe" allein oft zu False Positives führt. Modelle mogelten sich durch, indem sie Keywords nannten, aber den **Tone** nicht trafen (z.B. blieb Sarkasmus erhalten, obwohl er entfernt werden sollte).

Daher wurde für Expert-Assets (wie Asset 006 "Sarcasm Shield") eine **gehärtete Hybrid-Logik** eingeführt:

### 1. Hybrid Scoring (Logic Branching)
Das System entscheidet dynamisch, wie streng es bewertet, basierend auf dem Tier:

- **Standard/Advanced Tier**: 
  - **Logik**: `Exact Match OR Semantic Match`.
  - Wenn das Keyword exakt fehlt, reicht eine semantische Ähnlichkeit (Threshold 0.45). Das verzeiht kreatives Umformulieren.

- **Expert Tier (The "Qwen Fix")**:
  - **Logik**: `Strict Coverage + High-Threshold Semantics`.
  - **Full Coverage**: Es wird erwartet, dass *alle* kritischen Aspekte adressiert werden (100% Keyword Coverage Ziel).
  - **Härterer Threshold**: Wenn ein Keyword fehlt, muss der Ersatz semantisch extrem nah an der erwarteten Lösung sein (**Threshold 0.55** statt 0.45).
  - **Grund**: Dies verhindert, dass Modelle punkten, die nur "ungefähr" vom Thema sprechen, aber die spezifische Nuance (z.B. "Deeskalation") verfehlen.

### 2. Das "Audit & Transform" Pattern
Alle Assets zwingen das Modell in einen zweistufigen Prozess:
1.  **Analysieren**: Das Modell muss explizit auflisten, was am Quelltext schlecht ist (z.B. "Zu passiv", "Sarkastisch").
2.  **Transformieren**: Erst dann folgt der Rewrite.
-> Der Benchmark scannt primär den "Rewrite"-Teil, nutzt aber die Analyse, um das "Verständnis" zu prüfen (Error Detection Score).

---

## 📊 Scoring Komponenten

Das Scoring (Total: 100 Punkte) setzt sich zusammen aus:

1. **Error Detection / Constraint Adherence (40 Punkte)**
   - Hat das Modell die Probleme im Source-Text erkannt?
   - Wurde der Sarkasmus identifiziert? Wurde das fehlende CTA bemerkt?

2. **Solution Quality (60 Punkte)**
   - Wie gut ist der Rewrite?
   - Werden die "Expected Keywords" (oder deren semantische Zwillinge) genutzt?
   - Stimmt die Struktur (z.B. Markdown-Tabelle, Tweet-Länge)?

---

## 📂 Assets

| ID | Name | Transformation | Difficulty | Highlight |
|----|------|----------------|------------|-----------|
| 001 | Landing Page Copy | Feature List -> Hero Section | Tiered | Prüft Conversion-Fokus |
| 002 | Social Media Thread | Blogpost -> Twitter Thread | Tiered | Prüft Thread-Struktur (1/x) |
| 003 | Glossary Simplification | Jargon -> Plain Language | Tiered | Prüft "Oma-Test" (Einfachheit) |
| 004 | Video Script | Outline -> Spoken Word Script | Tiered | Prüft Sprachrhythmus |
| 005 | Newsletter Adaptation | Case Study -> Email | Tiered | Prüft Betreffzeilen & Hooks |
| **006**| **Sarcasm Shield** | **Passive-Aggressive -> Neutral** | **Expert** | **Hardened Semantics Test** |

---

> **Wartungshinweis für LLMs:**
> Sollte in Zukunft ein Modell bei Asset 006 wieder 100% erreichen, obwohl der Output sarkastisch ist: Erhöhe den `semantic_threshold` in `test.py` für `expert` Issues auf 0.60 oder 0.65. Dies zwingt das Modell zu präziseren Formulierungen.

