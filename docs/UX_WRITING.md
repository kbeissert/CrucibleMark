# UX Writing & Microcopy Module - Dokumentation

## Übersicht

Das UX Writing Module bewertet die Fähigkeit von LLMs, nutzerfreundliche, barrierefreie und kontextgerechte Texte für Benutzeroberflächen zu erstellen. Es prüft nicht nur die sprachliche Korrektheit, sondern auch Tonalität, Barrierefreiheit (A11y) und Compliance.

---

## Test Assets

Das Modul umfasst 5 Assets mit gestaffelter Schwierigkeit (Tier 1-4):

| Asset | Fokus | Beschreibung |
| :--- | :--- | :--- |
| **001 Error Messages** | User-Friendly Rewriting | Verwandlung technischer Fehlermeldungen ("Error 500: Database Connection Failed") in hilfreiche Nutzer-Texte. |
| **002 Button Labels** | Context-Aware CTAs | Erstellung von handlungsorientierten Button-Texten für verschiedene Kontexte (E-Commerce, Banking, Enterprise). |
| **003 Onboarding Flow** | Step-by-Step Guidance | Erklärung komplexer Features in kurzen, verständlichen Schritten (Mobile-First). |
| **004 Accessibility Labels** | ARIA & Screen Reader | Erstellung von unsichtbaren Labels für Screen-Reader (aria-label, alt-text). |
| **005 Microcopy Audit** | Real-World Compliance | Audit einer Gesundheits-App auf verständliche und rechtssichere Sprache. |

---

## Schwierigkeits-Stufen (Tiers)

1.  **Labeled (Easy)**: Probleme sind explizit markiert (z.B. `<!-- TODO: Zu technisch -->`).
2.  **Standard (Medium)**: Offensichtliche Verstöße gegen UX-Writing-Regeln (z.B. Passiv, Jargon, "Click here").
3.  **Advanced (Hard)**: Subtile Tonalitäts-Probleme, Inkonsistenzen oder fehlende Kontext-Sensitivität.
4.  **Expert (Very Hard)**: Komplexe Compliance-Risiken (z.B. medizinische Falschberatung), inkonsistente Terminologie über Screens hinweg oder Accessibility-Edge-Cases.

---

## Scoring-Dimensionen

Die Bewertung erfolgt hybrid (Keywords + Semantische Ähnlichkeit zum Golden Standard):

| Kategorie | Gewichtung | Beschreibung |
| :--- | :--- | :--- |
| **Problem-Erkennung** | 35% | Identifiziert das Modell die UX-Probleme (z.B. "Schuldzuweisung an Nutzer")? |
| **Lösungs-Qualität** | 35% | Sind die Vorschläge kurz, prägnant und handlungsorientiert? |
| **Fachkompetenz** | 15% | Werden Prinzipien wie "Front-Loading" oder "Plain Language" angewandt? |
| **Formatierung** | 15% | Werden ARIA-Attribute und HTML-Strukturen korrekt eingehalten? |

---

## Erwartete Benchmarks

Basierend auf ersten Tests mit Version 1.0.0:

*   **Claude 3.5 Sonnet**: ~90-95% (Sehr stark in Nuancen und Tonalität)
*   **GPT-4o**: ~85-90% (Sehr solide, manchmal etwas zu wortreich)
*   **Mistral Large**: ~80-85% (Gut, aber manchmal zu technisch)
*   **Qwen 2.5 14B**: ~70-80% (Überraschend gut für ein lokales Modell)
*   **Llama 3 8B**: ~60-70% (Grundlagen vorhanden, scheitert an komplexen Kontexten)
