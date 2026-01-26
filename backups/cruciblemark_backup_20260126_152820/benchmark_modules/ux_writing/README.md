# UX Writing & Microcopy Module

> **Technical Metadata**
> - **ID:** `ux_writing`
> - **Namespace:** `benchmark_modules.ux_writing`
> - **Class:** `UXWritingTest` (inherits `BaseTest`)
> - **Version:** 0.9.0-beta
> - **Type:** User Experience & Microcopy

## 🔍 Module Overview

Dieses Modul bewertet die Fähigkeit von LLMs, nutzerfreundliche, barrierefreie und kontextgerechte UX-Texte zu erstellen.

## 📂 Verfügbare Test-Assets

| ID | Name | Focus |
|----|------|-------|
| 001 | **Error Messages** | Technische Fehler → Nutzerfreundlich |
| 002 | **Button Labels** | Kontextbasierte CTAs |
| 003 | **Onboarding Flow** | 3-Step Tutorials |
| 004 | **Accessibility Labels** | ARIA-Labels für Screen-Reader |
| 005 | **Microcopy Audit** | Compliance & Safety (Medical) |

## 📊 Scoring-Dimensionen

| Kategorie | Gewichtung | Beschreibung |
|-----------|------------|--------------|
| **Problem-Erkennung** | 60 Punkte | Erkennung von UX-Writing-Problemen (Tiered) |
| **Lösungs-Qualität** | 30 Punkte | Verständlichkeit, Tonalität, Handlungsanweisungen |
| **Formatierung** | 10 Punkte | A11y-Konformität, Struktur |

## 🧠 Besonderheiten

- **Compliance-Awareness**: Asset 005 testet medizinischen Kontext (Fehldosierung = Critical)
- **A11y-Fokus**: ARIA-Labels, Screen-Reader-Kompatibilität
- **Mobile-First**: Button-Limits (50 Zeichen), Step-Limits (80 Wörter)

### Schwierigkeits-Level

1. **Labeled (Easy)**: Probleme sind explizit markiert (z.B. "TODO: Zu technisch").
2. **Standard (Medium)**: Offensichtliche Verstöße gegen UX-Writing-Regeln (z.B. Passiv, Jargon).

**Hinweis zum Prompt-Design:**
Um eine faire Bewertung zu gewährleisten, erzwingen alle UX-Writing-Prompts eine strikte Trennung in **Schritt 1: Analyse** (Problem-Identifikation) und **Schritt 2: Optimierung**. Modelle, die diesen Schritt überspringen, verlieren signifikant Punkte in der *Problem-Erkennung*.
