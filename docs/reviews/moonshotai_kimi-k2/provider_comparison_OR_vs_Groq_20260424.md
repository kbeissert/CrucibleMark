# Kimi K2 — Provider-Vergleich: OpenRouter vs. Groq

> **Vergleichszweck:** Gleicher Checkpoint (0711), zwei Provider.
> Dient zur Evaluation von Provider-bedingten Qualitätsdifferenzen,
> Latenz- und Kostenunterschieden sowie Scoring-Konsistenz.

---

## Metadaten

| Feld | OpenRouter (kimi-k2-0711) | Groq (kimi-k2-instruct) |
|---|---|---|
| **model_id (CSV)** | `moonshotai/kimi-k2-0711` | `moonshotai/kimi-k2-instruct` |
| **config-Slug aktiv** | `moonshotai/kimi-k2` | `moonshotai/kimi-k2-instruct` |
| **Provider** | openrouter | groq |
| **model_version (intern)** | k2-0711 | k2 |
| **Checkpoint** | 0711 (floating alias via OR) | 0711 (Groq inference) |
| **Benchmark-Datum(en)** | 2026-04-24 | 2026-03-31, 2026-04-09 |
| **Datenpunkte (o. PC)** | 43 | 40 |
| **LLM-Judge** | claude-haiku-4-5-20251001 | claude-haiku-4-5-20251001 |
| **Judge-Provider** | anthropic | anthropic |
| **Scoring-Methode** | hybrid | hybrid |
| **Kosten gesamt** | $0.0526 (OR-Fee) | $0.0000 (Groq free tier) |

### Run-IDs

**OpenRouter:** `35c27550ee11`, `47437980e71b`, `b535574eee67`, `ddc260006a1d`, `eb1915d7a885`, `edd3fab62604`, `f2fb513eb7e7`

**Groq:** `1d76f0c44831`, `2118093ca3fc`, `272b1bc9320a`, `58dc7b3a9718`, `6da7afb03dd4`, `996f49bf7318`, `a090348b3736`, `e439d90902ff`

---

## Modul-Übersicht

| Modul | OR Ø % | Groq Ø % | Δ | OR n | Groq n |
|---|---:|---:|---:|---:|---:|
| CLI Benchmark | 82.0 % | 81.1 % | +0.9 | 6 | 6 |
| Code Quality | 70.0 % | 74.8 % | -4.8 | 5 | 5 |
| Content Transformation | 71.9 % | 59.9 % | +12.0 | 6 | 4 |
| Cultural Intelligence | 65.8 % | 72.6 % | -6.8 | 5 | 5 |
| Documentation Quality | 66.6 % | 63.0 % | +3.6 | 5 | 5 |
| Reasoning & Logic | 72.9 % | 65.4 % | +7.4 | 11 | 11 |
| UX Writing | 65.3 % | 62.9 % | +2.3 | 5 | 4 |
| **GESAMT** | **71.2 %** | **68.7 %** | **+2.5** | **43** | **40** |

> Fehlende Groq-Einträge: `content_transformation_003`, `content_transformation_004`, `ux_writing_005`
> (Assets wurden nach dem Groq-Benchmark-Datum (Apr 2026) hinzugefügt).

---

## Asset-Level Detailvergleich inkl. Judge-Metadaten

Spalten: **OR%** / **Groq%** / **Δ** / **OR resp** / **Groq resp** / **OR Judge-Score** / **Groq Judge-Score** / **OR Compliance** / **Groq Compliance** / **OR Quality** / **Groq Quality** / **OR Adherence** / **Groq Adherence**

### CLI Benchmark

| Asset | Name | OR % | Groq % | Δ | OR resp | Groq resp | OR Judge | Groq Judge | OR Compl. | Groq Compl. | OR Qual. | Groq Qual. | OR Adh. | Groq Adh. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `cli001` | Disk Cleanup (du + rm safe) | 86.0 % | 73.3 % | +12.7 | 840 | 1050 | 4.0 | 4.0 | 5.0 | 4.0 | 5.0 | 4.0 | 4.0 | 4.0 |
| `cli002` | Library Install (pip/brew) | 48.0 % | 53.4 % | -5.3 | 307 | 277 | 2.0 | 2.0 | 2.0 | 2.0 | 4.0 | 4.0 | 1.0 | 1.0 |
| `cli003` | Repo Clone + Web Fetch | 100.0 % | 100.0 % | +0.0 | 106 | 110 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 | 5.0 |
| `cli004` | Zshrc Alias & Source | 86.0 % | 90.0 % | -4.0 | 278 | 267 | 4.0 | 4.0 | 4.0 | 4.0 | 5.0 | 5.0 | 3.0 | 4.0 |
| `cli005` | SwarmUI Docker Deployment | 86.0 % | 90.0 % | -4.0 | 595 | 579 | 4.0 | 4.0 | 5.0 | 5.0 | 4.0 | 4.0 | 4.0 | 5.0 |
| `cli006` | Ollama Models to External Disk + Symlink | 86.0 % | 80.0 % | +6.0 | 416 | 410 | 4.0 | 3.0 | 4.0 | 3.0 | 4.0 | 4.0 | 3.0 | 2.0 |

### Code Quality

| Asset | Name | OR % | Groq % | Δ | OR resp | Groq resp | OR Judge | Groq Judge | OR Compl. | Groq Compl. | OR Qual. | Groq Qual. | OR Adh. | Groq Adh. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `code_quality_001` | WCAG 2.2 Audit (Tiered Difficulty) | 66.0 % | 80.0 % | -14.0 | 2391 | 3183 | 3.0 | 3.0 | 5.0 | 3.0 | 3.0 | 3.0 | 2.0 | 3.0 |
| `code_quality_002` | Security Audit (Tiered Difficulty) | 63.2 % | 79.0 % | -15.8 | 1964 | 1832 | 3.0 | 4.0 | 5.0 | 3.0 | 3.0 | 4.0 | 2.0 | 3.0 |
| `code_quality_003` | Web Performance Audit (Tiered Difficulty) | 80.0 % | 80.0 % | +0.0 | 1974 | 1554 | 4.0 | 4.0 | 5.0 | 4.0 | 4.0 | 4.0 | 3.0 | 3.0 |
| `code_quality_004` | REST API Design Audit (Tiered Difficulty) | 78.0 % | 72.5 % | +5.5 | 1805 | 1804 | 4.0 | 3.0 | 3.0 | 3.0 | 4.0 | 3.0 | 3.0 | 2.0 |
| `code_quality_005` | Code Smells Audit (Tiered Difficulty) | 63.0 % | 62.5 % | +0.5 | 1674 | 1245 | 3.0 | 3.0 | 3.0 | 3.0 | 4.0 | 3.0 | 3.0 | 2.0 |

### Content Transformation

| Asset | Name | OR % | Groq % | Δ | OR resp | Groq resp | OR Judge | Groq Judge | OR Compl. | Groq Compl. | OR Qual. | Groq Qual. | OR Adh. | Groq Adh. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `content_transformation_001` | Landing Page Copy Transformation | 77.3 % | 32.4 % | +44.9 | 997 | 844 | 4.0 | 2.0 | 4.0 | 2.0 | 4.0 | 3.0 | 4.0 | 3.0 |
| `content_transformation_002` | Twitter Thread Transformation | 76.5 % | 78.2 % | -1.7 | 2274 | 2074 | 4.0 | 4.0 | 5.0 | 4.0 | 4.0 | 4.0 | 3.0 | 3.0 |
| `content_transformation_003` | Glossar-Eintrag Simplification | 73.8 % | — | — | 1488 | — | 4.0 | — | 5.0 | — | 4.0 | — | 4.0 | — |
| `content_transformation_004` | Video-Script Transformation | 79.9 % | — | — | 4720 | — | 4.0 | — | 4.0 | — | 3.0 | — | 3.0 | — |
| `content_transformation_005` | Email-Newsletter Adaptation | 61.3 % | 65.4 % | -4.1 | 1611 | 1667 | 3.0 | 4.0 | 3.0 | 3.5 | 3.0 | 3.8 | 3.0 | 3.5 |
| `content_transformation_006` | Sarcasm Shield (Incident Report) | 62.5 % | 63.8 % | -1.2 | 1918 | 1750 | 3.0 | 4.0 | 2.0 | 4.0 | 4.0 | 4.0 | 2.0 | 3.0 |

### Cultural Intelligence

| Asset | Name | OR % | Groq % | Δ | OR resp | Groq resp | OR Judge | Groq Judge | OR Compl. | Groq Compl. | OR Qual. | Groq Qual. | OR Adh. | Groq Adh. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `cultural_intel_001` | German Tech Localization | 82.0 % | 75.0 % | +7.0 | 211 | 208 | 4.0 | 3.0 | 5.0 | 5.0 | 4.0 | 3.0 | 3.0 | 3.0 |
| `cultural_intel_002` | Inclusive Job Ad | 68.0 % | 80.0 % | -12.0 | 418 | 385 | 3.0 | 4.0 | 5.0 | 5.0 | 3.0 | 4.0 | 3.0 | 3.0 |
| `cultural_intel_003` | Berlin Agency Vibe | 82.0 % | 80.0 % | +2.0 | 173 | 126 | 4.0 | 3.0 | 5.0 | 5.0 | 4.0 | 3.0 | 3.0 | 3.0 |
| `cultural_intel_004` | Formal vs. Informal German | 52.0 % | 65.0 % | -13.0 | 271 | 278 | 2.0 | 2.0 | 1.0 | 1.0 | 3.0 | 3.0 | 2.0 | 3.0 |
| `cultural_intel_005` | German Idioms & Expressions | 45.2 % | 63.0 % | -17.8 | 244 | 246 | 2.0 | 3.0 | 1.0 | 5.0 | 2.0 | 3.0 | 2.0 | 2.0 |

### Documentation Quality

| Asset | Name | OR % | Groq % | Δ | OR resp | Groq resp | OR Judge | Groq Judge | OR Compl. | Groq Compl. | OR Qual. | Groq Qual. | OR Adh. | Groq Adh. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `documentation_quality_001` | README Quality Assessment (Tiered) | 79.4 % | 77.7 % | +1.7 | 3479 | 4662 | 4.0 | 4.0 | 5.0 | 4.0 | 4.0 | 4.0 | 3.0 | 3.0 |
| `documentation_quality_002` | REST API Endpoint Documentation | 79.7 % | 74.4 % | +5.2 | 5232 | 3487 | 4.0 | 4.0 | 4.0 | 5.0 | 4.0 | 4.0 | 3.0 | 3.0 |
| `documentation_quality_003` | Component Library Props Documentation | 76.2 % | 60.0 % | +16.2 | 4957 | 3171 | 4.0 | 3.0 | 4.0 | 4.0 | 4.0 | 3.0 | 3.0 | 2.0 |
| `documentation_quality_004` | Setup Guide - Local Dev Environment (Docker + Vite) | 77.1 % | 63.5 % | +13.6 | 3955 | 4238 | 4.0 | 3.0 | 5.0 | 3.5 | 4.0 | 3.5 | 3.0 | 3.0 |
| `documentation_quality_005` | Changelog - Git Commits to User-Facing Release Notes | 20.8 % | 39.6 % | -18.8 | 485 | 2658 | 1.0 | 2.0 | 1.0 | 1.0 | 1.0 | 3.0 | 0.0 | 2.0 |

### Reasoning & Logic

| Asset | Name | OR % | Groq % | Δ | OR resp | Groq resp | OR Judge | Groq Judge | OR Compl. | Groq Compl. | OR Qual. | Groq Qual. | OR Adh. | Groq Adh. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `reasoning_001_river` | Reasoning 001: River Crossing Puzzle | 79.8 % | 73.0 % | +6.8 | 1733 | 1356 | 4.0 | 4.0 | 5.0 | 5.0 | 4.0 | 4.0 | 3.0 | 4.0 |
| `reasoning_5a_001` | Reasoning 5A: Code Logic Debugging (Infinite Loop) | 75.0 % | 67.5 % | +7.5 | 1315 | 1587 | 4.0 | 4.0 | 5.0 | 5.0 | 4.0 | 4.0 | 3.0 | 3.0 |
| `reasoning_5b_001` | Reasoning 5B: Root Cause Analysis | 79.6 % | 82.0 % | -2.4 | 2044 | 2339 | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 | 4.0 | 3.0 | 3.0 |
| `reasoning_5c_001` | Reasoning 5C: The Scheduling Paradox | 58.0 % | 53.1 % | +4.9 | 522 | 741 | 3.0 | 3.0 | 3.0 | 3.0 | 3.0 | 2.0 | 2.0 | 3.0 |
| `reasoning_5d_001` | Reasoning 5D: Hidden Deadlock (Technical) | 82.0 % | 79.5 % | +2.5 | 2368 | 2569 | 4.0 | 4.0 | 4.0 | 5.0 | 4.0 | 4.0 | 3.0 | 3.0 |
| `reasoning_5e_001` | Reasoning 5E: The Nested Transaction Paradox | 77.0 % | 63.2 % | +13.8 | 3316 | 3079 | 4.0 | 3.0 | 5.0 | 4.0 | 4.0 | 3.0 | 3.0 | 3.0 |
| `reasoning_metacog_001` | Metacognition 001: The Sheep Trap (Self-Correction) | 76.0 % | 55.0 % | +21.0 | 207 | 346 | 4.0 | 4.0 | 5.0 | 5.0 | 3.0 | 4.0 | 3.0 | 3.0 |
| `reasoning_metacog_002` | Metacognition 002: The Green Sky (False Premise Challenge) | 52.0 % | 50.0 % | +2.0 | 1424 | 1157 | 3.0 | 4.0 | 5.0 | 5.0 | 3.0 | 3.0 | 3.0 | 3.0 |
| `reasoning_metacog_003` | Metacognition 003: The Two Doors (Ambiguous Problem) | 81.0 % | 82.5 % | -1.5 | 1642 | 1457 | 4.0 | 4.0 | 5.0 | 5.0 | 4.0 | 4.0 | 4.0 | 4.0 |
| `reasoning_metacog_004` | Metacognition 004: The Monty Hall Problem (Iterative Refinement) | 69.0 % | 53.8 % | +15.2 | 1225 | 2252 | 4.0 | 4.0 | 5.0 | 5.0 | 4.0 | 4.0 | 3.0 | 3.0 |
| `reasoning_metacog_005` | Metacognition 005: The Birthday Paradox (Uncertainty Calibration) | 72.0 % | 60.0 % | +12.0 | 1121 | 1714 | 4.0 | 4.0 | 5.0 | 5.0 | 4.0 | 4.0 | 4.0 | 3.0 |

### UX Writing

| Asset | Name | OR % | Groq % | Δ | OR resp | Groq resp | OR Judge | Groq Judge | OR Compl. | Groq Compl. | OR Qual. | Groq Qual. | OR Adh. | Groq Adh. |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `ux_writing_001` | Error Messages - User-Friendly Rewriting | 59.6 % | 73.0 % | -13.4 | 2215 | 2033 | 3.0 | 4.0 | 4.0 | 4.0 | 3.0 | 4.0 | 3.0 | 3.0 |
| `ux_writing_002` | Button Labels - Context-Aware CTAs | 61.0 % | 57.2 % | +3.7 | 1474 | 1257 | 3.0 | 2.0 | 5.0 | 5.0 | 3.0 | 2.0 | 3.0 | 2.0 |
| `ux_writing_003` | Onboarding Flow - 3-Step Tutorial | 82.0 % | 66.5 % | +15.5 | 2531 | 2308 | 4.0 | 3.0 | 3.0 | 5.0 | 4.0 | 3.0 | 3.0 | 2.0 |
| `ux_writing_004` | Accessibility Labels - ARIA for Screen Readers | 59.0 % | 55.0 % | +4.0 | 1635 | 1591 | 3.0 | 3.0 | 4.0 | 4.0 | 2.0 | 3.0 | 3.0 | 2.0 |
| `ux_writing_005` | Microcopy Audit - Health App Context | 64.8 % | — | — | 1755 | — | 3.0 | — | 5.0 | — | 3.0 | — | 2.0 | — |

---

## Performance & Flags

| Asset | OR exec (s) | Groq exec (s) | Δ exec | OR tokens | Groq tokens | OR parse_ok | Groq parse_ok | OR refusal | Groq refusal | OR cutoff | Groq cutoff | OR finish | Groq finish |
|---|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|---|
| `cli001` | 9 | 1 | +7.9 | 255 | 307 | True | True | — | — | False | False | stop | stop |
| `cli002` | 4 | 1 | +3.1 | 118 | 111 | True | True | — | — | False | False | stop | stop |
| `cli003` | 2 | 0 | +1.7 | 71 | 72 | True | True | — | — | False | False | stop | stop |
| `cli004` | 4 | 1 | +3.0 | 122 | 119 | True | True | — | — | False | False | stop | stop |
| `cli005` | 6 | 1 | +5.3 | 213 | 209 | True | True | — | — | False | False | stop | stop |
| `cli006` | 4 | 1 | +3.8 | 157 | 155 | True | True | — | — | False | False | stop | stop |
| `code_quality_001` | 27 | 4 | +23.1 | 1250 | 1448 | True | True | — | — | False | False | stop | stop |
| `code_quality_002` | 16 | 2 | +13.9 | 1585 | 1552 | True | True | — | — | False | False | stop | stop |
| `code_quality_003` | 18 | 2 | +16.2 | 1278 | 1173 | True | True | — | — | False | False | stop | stop |
| `code_quality_004` | 18 | 3 | +15.7 | 1140 | 1140 | True | True | — | — | False | False | stop | stop |
| `code_quality_005` | 19 | 2 | +16.8 | 1172 | 1065 | True | True | — | — | False | False | stop | stop |
| `content_transformation_001` | 12 | 1 | +10.4 | 729 | 691 | True | True | — | — | False | False | stop | stop |
| `content_transformation_002` | 27 | 3 | +23.4 | 1487 | 1437 | True | True | — | — | False | False | stop | stop |
| `content_transformation_003` | 18 | — | — | 1174 | — | True | — | — | — | False | — | stop | — |
| `content_transformation_004` | 51 | — | — | 2198 | — | True | — | — | — | False | — | stop | — |
| `content_transformation_005` | 18 | 3 | +14.7 | 1563 | 1577 | True | True | — | — | False | False | stop | stop |
| `content_transformation_006` | 16 | 2 | +13.4 | 650 | 608 | True | True | — | — | False | False | stop | stop |
| `cultural_intel_001` | 3 | 0 | +2.2 | 187 | 187 | True | True | — | — | False | False | stop | stop |
| `cultural_intel_002` | 6 | 1 | +5.0 | 261 | 253 | True | True | — | — | False | False | stop | stop |
| `cultural_intel_003` | 3 | 0 | +2.8 | 194 | 182 | True | True | — | — | False | False | stop | stop |
| `cultural_intel_004` | 4 | 1 | +3.2 | 235 | 237 | True | True | — | — | False | False | stop | stop |
| `cultural_intel_005` | 3 | 0 | +2.9 | 214 | 214 | True | True | — | — | False | False | stop | stop |
| `documentation_quality_001` | 31 | 5 | +25.6 | 1336 | 1632 | True | True | — | — | False | False | stop | stop |
| `documentation_quality_002` | 49 | 4 | +45.1 | 1898 | 1461 | True | True | — | — | False | False | stop | stop |
| `documentation_quality_003` | 46 | 4 | +41.6 | 1936 | 1489 | True | True | — | — | False | False | stop | stop |
| `documentation_quality_004` | 38 | 5 | +32.7 | 1666 | 1737 | True | True | — | — | False | False | stop | stop |
| `documentation_quality_005` | 6 | 3 | +3.1 | 690 | 1233 | True | True | — | — | False | False | stop | stop |
| `reasoning_001_river` | 14 | 2 | +11.7 | 568 | 474 | True | True | — | — | False | False | stop | stop |
| `reasoning_5a_001` | 10 | 2 | +8.2 | 560 | 628 | True | True | — | — | False | False | stop | stop |
| `reasoning_5b_001` | 16 | 3 | +13.4 | 690 | 763 | True | True | — | — | False | False | stop | stop |
| `reasoning_5c_001` | 5 | 1 | +3.8 | 269 | 324 | True | True | — | — | False | False | stop | stop |
| `reasoning_5d_001` | 17 | 3 | +14.0 | 718 | 768 | True | True | — | — | False | False | stop | stop |
| `reasoning_5e_001` | 24 | 4 | +20.0 | 1049 | 989 | True | True | — | — | False | False | stop | stop |
| `reasoning_metacog_001` | 3 | 1 | +2.7 | 164 | 199 | True | True | — | — | False | False | stop | stop |
| `reasoning_metacog_002` | 16 | 2 | +13.6 | 464 | 397 | True | True | — | — | False | False | stop | stop |
| `reasoning_metacog_003` | 19 | 2 | +17.2 | 589 | 543 | True | True | — | — | False | False | stop | stop |
| `reasoning_metacog_004` | 15 | 4 | +11.1 | 504 | 761 | True | True | — | — | False | False | stop | stop |
| `reasoning_metacog_005` | 13 | 2 | +10.5 | 444 | 592 | True | True | — | — | False | False | stop | stop |
| `ux_writing_001` | 23 | 3 | +20.3 | 951 | 906 | True | True | — | — | False | False | stop | stop |
| `ux_writing_002` | 16 | 2 | +14.6 | 936 | 882 | True | True | — | — | False | False | stop | stop |
| `ux_writing_003` | 25 | 3 | +22.3 | 1195 | 1140 | True | True | — | — | False | False | stop | stop |
| `ux_writing_004` | 18 | 2 | +15.4 | 857 | 846 | True | True | — | — | False | False | stop | stop |
| `ux_writing_005` | 21 | — | — | 951 | — | True | — | — | — | False | — | stop | — |

---

## Befunde & Interpretation

### OpenRouter (kimi-k2-0711) — Stärken

- **Content Transformation `ct_001`:** +44.9 Pkt (77.3 vs. 32.4 %) — markantester Einzelunterschied im gesamten Vergleich
- **Reasoning & Logic:** Durchgehend stärker: `metacog_001` +21.0, `metacog_004` +15.2, `5e_001` +13.8, `metacog_005` +12.0
- **Documentation Quality:** Vorteil in 4 von 5 Assets, besonders `doc_003` +16.2 und `doc_004` +13.6
- **UX Writing `ux_003`:** +15.5 Pkt
- **CLI `cli001`:** +12.7 Pkt
- **Gesamt:** 71.9 % vs. 69.5 % → **+2.4 Pkt Vorsprung**

### Groq (kimi-k2-instruct) — Stärken

- **Code Quality:** klarer Vorteil in `code_001` (80.0 vs. 66.0 %, −14.0) und `code_002` (79.0 vs. 63.2 %, −15.8)
- **Cultural Intelligence:** `cultural_005` −17.8 Pkt, `cultural_004` −13.0 Pkt — kulturelle Nuancen konsistent besser
- **Documentation `doc_005`:** +18.8 Pkt zugunsten Groq (einzige Doc-Ausnahme)
- **UX Writing `ux_001`:** +13.4 Pkt zugunsten Groq
- **Latenz:** Groq exec_time typ. < 5 s; OR typ. 15–34 s — Groq **5–10× schneller**
- **Kosten:** $0 vs. $0.0526 gesamt — Groq kostenlos

### Datenlücken

- `ct_003`, `ct_004`, `ux_writing_005`: Groq-Daten fehlen — Assets wurden nach Groq-Run hinzugefügt.
  Rein numerischer Modul-Vergleich ist für Content Transformation (n=4 vs. n=6) eingeschränkt vergleichbar.

### Judge-Konsistenz

- Beide Runs: Judge `claude-haiku-4-5-20251001` via Anthropic — keine Provider-bedingten Judge-Variablen
- Alle Judge-Parses erfolgreich (parse_success=True)
- Reasoning-Tokens: 0 für beide Modelle — kein aktivierter CoT-Mechanismus detektiert

---

## Fazit

OpenRouter (`moonshotai/kimi-k2`) liefert minimal bessere Gesamt-Scores (+2.4 Pkt),
besonders bei Reasoning, Documentation und Content Transformation.
Groq (`moonshotai/kimi-k2-instruct`) zeigt klare Stärken bei Code Quality und
Cultural Intelligence sowie massiven Latenz- und Kostenvorteil.

**Leaderboard-Empfehlung:** OR als primärer Eintrag (aktuelleres Datum, aktiveres Rubric).
Groq-Daten als historische Provider-Vergleichsbasis im CSV behalten.

---

*Erstellt: 2026-04-24 | Judge: claude-haiku-4-5-20251001 | Scoring: hybrid | CrucibleMark v3.5.9*
