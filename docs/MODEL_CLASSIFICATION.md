# Model Classification & Badge System

**Zielgruppe:** Alle, die verstehen wollen, wie CrucibleMark Modelle klassifiziert und bewertet.

**Was Sie hier finden:**

- Badge-System (Standard, Bronze, Silver, Gold)
- Speed Classes (Fast, Medium, Slow)
- Skill Profiles (automatische Kategorisierung)
- Reasoning Score Interpretation
- Best Practices für neue Modelle

______________________________________________________________________

## 🏅 Badge-System

Badges reflektieren die **Gesamt-Performance** über alle Module hinweg.

### Klassifizierung nach Total Score

| Badge | Score Range | Beschreibung | Beispiele (Feb 2026) |
|-------|-------------|--------------|----------------------|
| 🥇 **Gold** | ≥ 85.0 | Elite-Performance, Cloud-Niveau | *(Noch nicht erreicht)* |
| 🥈 **Silver** | 70.0 - 84.9 | Production-ready, gute Balance | Mistral Large (78.8), Ministral-3:14b (77.6), Cogito:14b (72.5) |
| 🥉 **Bronze** | 60.0 - 69.9 | Solide Basis, spezialisiert | Qwen 2.5:14b (69.4), DeepSeek-R1 (65.1) |
| ⚖️ **Standard** | < 60.0 | Entwicklungs-Stadium, limitiert | Dolphin-Llama3:8b (44.4) |

**Aktuelle Verteilung (16 Modelle):**

- Gold: 0
- Silver: 8 (50%)
- Bronze: 7 (44%)
- Standard: 1 (6%)

______________________________________________________________________

## 🌐 Provider-Kategorien

CrucibleMark unterscheidet drei Arten von Modell-Providern basierend auf ihrer Infrastruktur und Zugriffsmethode.

### Kategorien

| Kategorie | Beschreibung | Beispiele | Charakteristik |
|-----------|--------------|-----------|----------------|
| **Commercial** | Cloud-basierte kommerzielle APIs | Claude (Anthropic), Gemini (Google), GPT (OpenAI), Mistral AI | Kosten pro Token, API-Keys erforderlich, keine lokale Installation |
| **Local** | Vollständig lokal ausgeführte Modelle | Qwen 2.5, DeepSeek-R1, Ministral-3 (via Ollama) | Keine Kosten, volle Privatsphäre, lokale GPU/CPU |
| **Local Cloud** | Cloud-Modelle über Ollama Proxy | MiniMax-M2, GPT-OSS (via Ollama Cloud) | Ollama leitet Anfragen zu Cloud-Diensten weiter, erkennbar am `:cloud` Suffix |

### Erkennung (SSOT: `utils/model_utils.py::get_model_category()`)

Die Kategorisierung erfolgt automatisch beim Laden der Benchmark-Daten basierend auf zwei Faktoren:

1. **Quelldatei**: Aus welcher CSV stammen die Daten?

   - `commercial_models_benchmark.csv` → Immer **Commercial**
   - `local_models_benchmark.csv` → Weiter zu Regel 2

1. **Modellname**: Enthält der Name das Suffix `:cloud`?

   - Ja (z.B. `minimax-m2:cloud`) → **Local Cloud**
   - Nein (z.B. `ministral-3:14b`) → **Local**

**Beispiele:**

```python
get_model_category('claude-sonnet-4', 'commercial')    # → 'Commercial'
get_model_category('ministral-3:14b', 'local')         # → 'Local'
get_model_category('minimax-m2:cloud', 'local')        # → 'Local Cloud'
```

**Hinweis:** Local Cloud-Modelle sind technisch Cloud-Dienste, werden aber über die lokale Ollama-Installation als Proxy aufgerufen. Sie bieten Zugang zu externen APIs mit der Benutzerfreundlichkeit von Ollama.

______________________________________________________________________

## ⚡ Speed Classes

Speed Classes kategorisieren Modelle nach ihrer **durchschnittlichen Inferenz-Zeit** über alle 37 Tests.

### Klassifizierung

| Class | Symbol | Avg Time | Beschreibung | Use Case |
|-------|--------|----------|--------------|----------|
| **Fast** | ⚡ | < 30s | Instant-Gefühl, interaktive Nutzung | Autocomplete, Chat, Prototyping |
| **Medium** | ⏱️ | 30-60s | Spürbare Latenz, akzeptabel | Deep-Work Sessions, Batch Processing |
| **Slow** | 🐢 | > 60s | "Kaffeepause"-Modell | Hintergrund-Jobs, nächtliche Analysen |

**Beispiele:**

- **Fast:** Mistral Large (25.4s), Qwen 2.5-Coder:7b (17.9s)
- **Medium:** Cogito:14b (62.2s), Mistral-Nemo (60.0s)
- **Slow:** Ministral-3:14b (168s), Gemma3:12b (100.7s)

**Wichtig:** Speed ≠ Quality! Ministral-3:14b ist Slow, aber Rang 4 im Leaderboard.

______________________________________________________________________

## 🎯 Skill Profiles

Skill Profiles beschreiben die **Stärken-Kombination** eines Modells basierend auf Performance-Clustering.

### Profil-Typen

#### 1. **Fast Specialist**

- **Speed:** Fast (< 30s)
- **Stärken:** Code Quality + Reasoning
- **Beispiele:** Mistral Large (83.6 Code, 67.7 Reasoning)

#### 2. **Fast Content Adapter**

- **Speed:** Fast (< 30s)
- **Stärken:** Content Transformation + Cultural Intelligence
- **Beispiele:** Qwen 2.5-Coder:14b (77.1 Content, 63.0 Cultural)

#### 3. **Fast Code Reviewer**

- **Speed:** Fast (< 30s)
- **Stärken:** Code Quality (> 85) + Documentation
- **Beispiele:** Mistral Medium (90.2 Code, 70.9 Docs)

#### 4. **Balanced Specialist**

- **Speed:** Medium
- **Stärken:** Gleichmäßig über alle Module
- **Beispiele:** Cogito:14b (82.4 Code, 70.1 Reasoning)

#### 5. **Slow Specialist**

- **Speed:** Slow (> 60s)
- **Stärken:** Einzelne Domäne (meist Reasoning oder Cultural)
- **Beispiele:** Ministral-3:8b (71.5 Reasoning, 86.0 Cultural)

#### 6. **Slow Content Adapter**

- **Speed:** Slow (> 60s)
- **Stärken:** Content + Cultural Intelligence
- **Beispiele:** Ministral-3:14b (85.3 Content, 83.4 Cultural)

**Automatische Erkennung:** Basiert auf Top-2-Kategorien + Speed Class.

______________________________________________________________________

## 📊 Performance/s = "Qualität pro Sekunde"

**Performance/s sagt:**\
"Wie effizient ist das Modell in Bezug auf Wartezeit?"

### Formel

```
Performance/s = Total Score ÷ Avg Time (s)
```

**Was es misst:** Wie viel Leistung (Score) du **pro Sekunde Wartezeit** bekommst.

______________________________________________________________________

## 🎯 Interpretation

### Top-Performer (Efficiency-Könige)

| Model | Total Score | Zeit | Performance/s | Bedeutung |
|-------|-------------|------|---------------|-----------|
| **Mistral Large** | 78.84 | 25.4s | **3.10** | Schnell & stark → Ideal für Echtzeit |
| **Dolphin-Llama3** | 47.56 | 20.7s | **2.30** | Schnell, aber schwach → Nur für Simple Tasks |
| **Qwen 2.5:14b** | 70.29 | 32.4s | **2.17** | Guter Kompromiss |

### Slow Thinkers (Quality über Speed)

| Model | Total Score | Zeit | Performance/s | Bedeutung |
|-------|-------------|------|---------------|-----------|
| **Ministral-3:14b** | 77.63 | 167.95s | **0.46** | Langsam, aber Rang 2! → Batch-Jobs |
| **Ministral-3:8b** | 75.19 | 106.0s | **0.71** | Mittellangsam, stark |
| **Gemma3:12b** | 72.11 | 100.7s | **0.72** | Ähnlich wie Ministral-3:8b |

______________________________________________________________________

## 💡 Use Cases nach Performance/s

### 🚀 Hoch (> 3.0) - "Echtzeit-Klasse"

**Use Case:** Chat, Autocomplete, interaktive UIs\
**Beispiel:** Mistral Large (3.10)\
**Trade-off:** Meist Commercial oder schwächere Modelle

### ⚡ Mittel (1.0 - 3.0) - "Deep-Work-Klasse"

**Use Case:** Code-Reviews, Dokumentations-Analysen\
**Beispiel:** Qwen 2.5:14b (2.17), Cogito:14b (1.16)\
**Trade-off:** Spürbare Latenz, aber akzeptabel

### 🐢 Niedrig (< 1.0) - "Batch-Klasse"

**Use Case:** Nächtliche Scans, Background-Jobs\
**Beispiel:** Ministral-3:14b (0.46)\
**Trade-off:** Zu langsam für interaktive Nutzung, aber oft **höchste Quality**

______________________________________________________________________

## 📊 Reasoning Score Interpretation

Der **Reasoning Score** ist der härteste Test in CrucibleMark.

### Score-Bereiche & Bedeutung

| Score | Klassifizierung | Fähigkeiten | Beispiele |
|-------|-----------------|-------------|-----------|
| **35-40** | Elite | Tier 2 (Deep Reasoning) konstant > 70%, Tier 3 (Metacognition) > 50% | Mistral Medium (39.8) |
| **31-34** | Production-Ready | Tier 2 > 60%, Tier 3 variabel | Ministral-3:14b (36.4), Cogito (35.0) |
| **26-30** | Entwicklung | Tier 2 > 50%, Tier 3 schwach | Gemma2:9b (26.6), Mistral-Nemo (30.4) |
| **< 26** | Limitiert | Tier 2 inkonsistent, Tier 3 Fail | Dolphin-Llama3 (17.6) |

### Warum sind die Scores niedrig?

**Das ist gewollt!** CrucibleMark misst **operatives Reasoning** (Deadlock-Detection, Root-Cause-Analyse), nicht "wie viel schreibt das Modell".

**Tier-Breakdown:**

- **Tier 0 (Sanity Check):** 80% schaffen 60+ Punkte
- **Tier 2 (Deep Reasoning):** 50% schaffen 70+ Punkte
- **Tier 3 (Metacognition):** 20% schaffen 70+ Punkte

**Referenz:** Selbst DeepSeek-R1 (Marketing: "Reasoning Model") erreicht nur **31.6** → Das zeigt, dass Tier 2/3 **wirklich schwer** sind.

______________________________________________________________________

## 🔍 Routine vs. Reasoning Score

### Unterschied

| Metrik | Misst | Gewichtung | Beispiel-Tasks |
|--------|-------|------------|----------------|
| **Routine Score** | Alltags-Produktivität | Code (20%), UX (15%), Docs (20%), Content (20%), Cultural (25%) | Code-Audits, Button-Labels, README-Qualität |
| **Reasoning Score** | Kognitive Tiefe | Tier 0 (10%), Tier 2 (50%), Tier 3 (40%) | Deadlock-Erkennung, Paradox-Lösung, Selbstkorrektur |

**Warum beide?**

- **Routine:** Zeigt "Kann ich damit arbeiten?"
- **Reasoning:** Zeigt "Kann es komplexe Probleme lösen?"

**Beispiel:** Ministral-3:14b hat **41.3 Routine** (Rang 4) aber **36.4 Reasoning** (Rang 1 lokal) → Gut für Alltag UND tiefes Denken.

______________________________________________________________________

## 🛠️ Workflow: Neue Modelle hinzufügen

### 1. Benchmark ausführen

```bash
python test.py --model neues-modell:14b --runs 1
```

### 2. Leaderboard generieren

```bash
make leaderboard
```

### 3. Automatische Klassifizierung prüfen

Das System vergibt automatisch:

- **Badge:** Basierend auf Total Score
- **Speed Class:** Basierend auf Avg Time
- **Skill Profile:** Basierend auf Top-2-Kategorien

### 4. Manuelle Review (optional)

**Überprüfe, ob:**

- Badge passt zur erwarteten Performance
- Speed Class korrekt ist (manchmal langsame Runs durch System-Load)
- Skill Profile Sinn macht (z.B. "Fast Code Reviewer" sollte > 80 Code Quality haben)

**Bei Unstimmigkeiten:**

- Check `validation_dataset.py` → Sind alle Tests ausgeführt?
- Check `benchmark_leaderboard.csv` → Fehlerhafte Daten?

______________________________________________________________________

## 📈 Performance-Ratio & Vergleich mit Golden Standards

### Was sind Golden Standards?

**Golden Standards** sind **kommerzielle Referenz-Modelle** (aktuell: Mistral Large/Medium), gegen die alle lokalen Modelle gemessen werden.

**Performance-Ratio Formel:**

```
Performance Ratio = (Local Model Score / Golden Standard Score) × 100
```

**Beispiel:**

```
Ministral-3:14b: 77.6 Total Score
Mistral Large: 78.8 Total Score
→ Performance Ratio = (77.6 / 78.8) × 100 = 98.5%
```

**Interpretation:**

- **≥ 95%:** "Cloud-Niveau" erreicht
- **85-94%:** "Sehr nah", praxistauglich
- **75-84%:** "Gute Alternative", mit Einschränkungen
- **< 75%:** "Deutlicher Abstand"

**Aktuell:**

- Ministral-3:14b erreicht **98.5%** von Mistral Large → Fast identisch!

______________________________________________________________________

## 🚧 Qualitative Indikatoren (Meta-Analyse)

Neben den numerischen Scores (0-100%) gibt es **binäre Ausschlusskriterien**, die oft nicht direkt im Score ersichtlich sind, aber die Tauglichkeit eines Modells für Automatisierungsprozesse massiv einschränken.

### Das "Struktur-Paradoxon" (Tabellen & Formate)

Ein wichtiger Indikator ist die Fähigkeit, komplexe Markdown-Strukturen (wie Tabellen mit Pipes `|`) fehlerfrei zu generieren.

> **Design-Prinzip:** Tabellen sind kein "Nice-to-have" Formatierungs-Feature, sondern ein harter Filter für Modell-Qualität.

**Erkenntnis aus der Praxis:**
"Wenn ein Modell daran scheitert (z.B. indem es die Tabellenstruktur als Stop-Signal missinterpretiert oder inkohärent wird), zeigt das **fundamentale Schwächen** in der 'Instruction Following'-Fähigkeit oder im Training auf strukturierten Daten. Ein Modell, das keine saubere Tabelle generieren kann, ist für professionelle Automatisierung (Reporting, Daten-Extraktion) ungeeignet."

Dies betrifft beispielsweise ältere oder schlecht quantisierte Modelle (z.B. WizardLM-2:7b unter bestimmten Bedingungen). Solche Modelle mögen zwar "kreativ" sein und hohe Scores in einfachen Q&A Tasks erreichen, scheitern aber als zuverlässiges Backend-Tool für strukturierte Datenverarbeitung.

______________________________________________________________________

## 🎯 Best Practices

### DO's ✅

1. **Badge als Schnell-Indikator nutzen:** Silver = Production-ready
1. **Speed Class für Use-Case wählen:** Autocomplete = Fast, Deep-Work = Medium/Slow okay
1. **Skill Profile beachten:** Brauchst du Code-Reviewer oder Content-Adapter?
1. **Reasoning Score ernst nehmen:** < 30 = schwach bei komplexen Problemen

### DON'Ts ❌

1. **Nicht nur Badge anschauen:** Silver-Modelle haben unterschiedliche Stärken
1. **Nicht Speed ignorieren:** Ein 168s-Modell ist unbrauchbar für Autocomplete
1. **Nicht nur Reasoning:** Ein Modell mit 40 Reasoning aber 30 Routine ist unpraktisch
1. **Nicht Commercial blind vertrauen:** Mistral Large ist nur 1.2 Punkte besser als Ministral-3:14b (lokal!)

______________________________________________________________________

## 📊 Aktuelle Leaderboard-Highlights (Feb 2026)

### Top 5 Models

1. **Mistral Medium** (Commercial) → 81.3 Total, 39.8 Reasoning, Fast
1. **Mistral Large** (Commercial) → 78.8 Total, 35.6 Reasoning, Fast
1. **Ministral-3:14b** (Local) → 77.6 Total, 36.4 Reasoning, Slow ← **Bestes lokales Modell!**
1. **Ministral-3:8b** (Local) → 75.2 Total, 34.6 Reasoning, Slow
1. **Cogito:14b** (Local) → 72.5 Total, 35.0 Reasoning, Medium

### Key Insights

- **Gap Commercial → Local:** Nur **3.7 Punkte** (Mistral Medium vs. Ministral-3:14b)
- **Bestes Reasoning (lokal):** Ministral-3:14b (36.4) übertrifft DeepSeek-R1 (31.6)!
- **Schnellstes Production-Modell:** Qwen 2.5-Coder:7b (17.9s, Bronze)
- **Bester Allrounder:** Cogito:14b (Balanced Specialist, 62.2s)

______________________________________________________________________

## 🔗 Verwandte Dokumentation

- **ARCHITECTURE.md** – Technische Details zu Modulen & Scoring
- **USER_GUIDE.md** – Wie man Tests ausführt und interpretiert
- **README.md** – Übersicht & Quick Start

______________________________________________________________________

## 📜 Änderungshistorie

**v2.0.0 (Feb 2026):**

- Badge-System vereinfacht (RCI entfernt, Total Score maßgeblich)
- Speed Classes hinzugefügt
- Skill Profiles automatisiert
- Golden Standard Performance-Ratio integriert
- Reasoning Score Interpretation erweitert

**v1.0.0 (Jan 2026):**

- Initiale Version mit RCI (Reasoning Complexity Index)
- Generation-Klassifizierung (Gen 1/2/3)

______________________________________________________________________

**Dokumenten-Version:** 2.0.0 (Feb 2026)\
**Kompatibel mit:** CrucibleMark v0.9.5+\
**Lizenz:** Apache License 2.0
