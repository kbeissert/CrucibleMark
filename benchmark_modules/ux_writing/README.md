# UX Writing & Microcopy Module

> **Technical Metadata**
> - **ID:** `ux_writing`
> - **Namespace:** `benchmark_modules.ux_writing`
> - **Class:** `UXWritingTest` (inherits `BaseTest`)
> - **Version:** v0.9.5 (Hardened)
> - **Type:** User Experience & Microcopy

## 🔍 Module Overview

Dieses Modul bewertet die Fähigkeit von LLMs, nutzerfreundliche, barrierefreie und kontextgerechte UX-Texte zu erstellen. Ein besonderer Fokus liegt auf der **Gratwanderung zwischen technischer Präzision und menschlicher Nähe** (Tone of Voice).

---

## 🏗 Architektur & High-Performance Calibration

Bei der Entwicklung dieses Moduls zeigte sich, dass moderne High-End-Modelle (Qwen 2.5, DeepSeek V3) einfache UX-Aufgaben oft zu leicht lösen und an die "100%-Decke" stoßen (Ceiling Effect).

Um die Leistungsfähigkeit der Modelle wirklich differenzieren zu können, wurde insbesondere beim Expert-Level (Asset 005) eine spezielle Bewertungslogik implementiert.

### Das "Microux"-Dilemma (Asset 005)
Hier müssen Modelle komplexe, verschachtelte Fehlermeldungen in **menschenlesbare, extrem kurze Microcopy** übersetzen, ohne relevante Details zu verlieren.

**Die Bewertungslogik beinhaltet:**
1.  **Inverse Härtung**: Das Modell bekommt *Abzug*, wenn es bestimmte, eigentlich korrekte aber "faule" Standardfloskeln verwendet (z.B. "Ein Fehler ist aufgetreten" -> zu generisch).
2.  **Length Constraints**: Harte Zeichen-Limits für Buttons (max 20-30 Zeichen) und Headlines. Modelle, die schwafeln, verlieren massiv Punkte.
3.  **Semantic Density**: Es wird geprüft, ob trotz der Kürze *alle* kritischen Infos (Was ist passiert? Wie geht es weiter?) enthalten sind.
4.  **Tone-Check**: Unterscheidung zwischen "Roboter-Deutsch" und empathischer Ansprache.

> **Warum ist Qwen hier nicht bei 100%?**
> Selbst Top-Modelle neigen dazu, UX-Texte zu "über-erklären". Unser Benchmark bestraft *Verbosity* (Geschwätzigkeit) in Microcopy-Kontexten rigoros. Nur wer **kurz AND präzise** ist, erreicht den Top-Score.

---

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
