# UX Writing & Microcopy Test Module

## Übersicht

Dieses Modul bewertet die Fähigkeit von LLMs, nutzerfreundliche, barrierefreie und kontextgerechte UX-Texte zu erstellen.

## Assets

1. **Error Messages** - Technische Fehler → Nutzerfreundlich
2. **Button Labels** - Kontextbasierte CTAs (E-Commerce, Enterprise, Banking)
3. **Onboarding Flow** - 3-Step Tutorial für komplexes Feature
4. **Accessibility Labels** - ARIA-Labels für Screen-Reader
5. **Microcopy Audit** - Real-World Gesundheits-App (Compliance-kritisch)

## Scoring-Dimensionen

| Kategorie | Gewichtung | Beschreibung |
|-----------|------------|--------------|
| **Problem-Erkennung** | 60 Punkte | Erkennung von UX-Writing-Problemen (Tiered) |
| **Lösungs-Qualität** | 30 Punkte | Verständlichkeit, Tonalität, Handlungsanweisungen |
| **Formatierung** | 10 Punkte | A11y-Konformität, Struktur |

## Erwartete Ergebnisse

- **Claude 3.5 Sonnet**: 88-95 Punkte
- **GPT-4**: 82-90 Punkte
- **Qwen 2.5 14B**: 70-80 Punkte
- **Mistral Nemo**: 60-72 Punkte

## Verwendung

```
python run_benchmark.py

# Wähle:
# 1. Modul: UX Writing & Microcopy
# 2. Provider: Ollama / Commercial
# 3. Modell: qwen2.5:14b (oder anderes)
```

## Besonderheiten

- **Compliance-Awareness**: Asset 005 testet medizinischen Kontext (Fehldosierung = Critical)
- **A11y-Fokus**: ARIA-Labels, Screen-Reader-Kompatibilität
- **Mobile-First**: Button-Limits (50 Zeichen), Step-Limits (80 Wörter)

## Schwierigkeits-Level

1. **Labeled (Easy)**: Probleme sind explizit markiert (z.B. "TODO: Zu technisch").
2. **Standard (Medium)**: Offensichtliche Verstöße gegen UX-Writing-Regeln (z.B. Passiv, Jargon).
3. **Advanced (Hard)**: Subtile Tonalitäts-Probleme oder fehlende Kontext-Sensitivität.
4. **Expert (Very Hard)**: Komplexe Compliance-Risiken, inkonsistente Terminologie über Screens hinweg oder Accessibility-Edge-Cases.
