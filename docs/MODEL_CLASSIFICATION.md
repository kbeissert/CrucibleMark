# Model Classification & RCI (Reasoning Complexity Index)

**Zielgruppe:** Alle, die verstehen wollen, wie CrucibleMark Modelle in "Generationen" einteilt.

**Was Sie hier finden:**
- RCI (Reasoning Complexity Index) erklärt
- 3 Generationen von LLMs (Pattern Matcher → Reasoning → Distilled)
- Hybrid-Klassifizierungs-System (Auto + Manual)
- Wie man neue Modelle pflegt

---

## 📊 Der Reasoning Complexity Index (RCI)

Der RCI ist die zentrale Metrik zur Bewertung der **kognitiven Tiefe** eines Modells.

**Skala:** 0% bis 100%

### Berechnung

Der Score setzt sich aus zwei Faktoren zusammen:

```
RCI = (Avg_Tier1_2_Score × 0.6) + (Avg_Tier3_Score × 0.4)
```

**Komponenten:**
1. **Operationale Logik (60%):** Kann das Modell komplexe Rätsel lösen? (Tier 1 & 2)
2. **Metakognition (40%):** Reflektiert das Modell über seinen eigenen Denkprozess? (Tier 3)

**Siehe:** `ARCHITECTURE.md` für Details zu den Tiers.

---

### Klassifizierung basierend auf RCI

| Kategorie | RCI Bereich | Beschreibung | Beispiel |
|-----------|-------------|--------------|----------|
| **Standard** | < 50% | Löst Standard-Tasks, scheitert an Selbstreflexion | Dolphin 8B (~42%) |
| **Silver** | >> 70% | Gute Logik (Routine + Standard Reasoning) | Qwen 2.5 (~65%) |
| **Gold** | > 85% | Exzellente Logik + aktive Selbstkorrektur | DeepSeek R1 (~87%) |

Anmerkung: Die RCI-Werte korrelieren stark mit den **Leaderboard Badges** (Standard, Bronze, Silver, Gold).


---

## 🧬 3 Generationen von LLMs

CrucibleMark unterscheidet Modelle nach ihrer **Trainings-Architektur**:

### Gen 1: Pattern Matcher (Standard-LLMs)

**Training:** Supervised Fine-Tuning auf Text-Completion

**Charakteristik:**
- Schnell (< 10s Antwortzeit) → Siehe **Speed Class: Fast**
- Niedrige Reasoning Scores (< 70%) → Siehe **Badge: Bronze/Standard**
- Gut bei Routine-Tasks (Code, Doku, UX Writing)

**Beispiele:**
- Llama 3.1 8B
- Mistral 7B
- Qwen 2.5 14B (Base)

---

### Gen 2: Reasoning Models (mit <think> Tags)

**Training:** Reinforcement Learning auf Reasoning-Traces

**Charakteristik:**
- Langsam (> 30s Antwortzeit) → Siehe **Speed Class: Slow/Medium**
- Hohe Reasoning Scores (> 80%) → Siehe **Badge: Silver/Gold**
- Zeigen Denkprozess in `<think>` Tags
- Gut bei Logik-Rätseln, Mathematik, Constraint-Solving

**Beispiele:**
- DeepSeek R1
- Phi-4 14B
- Llama-R1 (Reasoning-Variant)

**Erkennung:** Framework parst `<think>` Tags automatisch

---

### Gen 3: Distilled Reasoning (o1-Preview-Style)

**Training:** Destillation von Gen 2 Modellen (ohne Traces)

**Charakteristik:**
- Mittelschnell (15-25s) → Siehe **Speed Class: Fast/Medium**
- Hohe Reasoning Scores (> 75%) → Siehe **Badge: Silver/Gold**
- **KEINE** `<think>` Tags (unsichtbares Reasoning)
- Nicht automatisch erkennbar

**Beispiele:**
- o1-preview (OpenAI)
- o1-mini (OpenAI)

**Problem:** Gen 3 ist **nicht unterscheidbar** von gut getunetem Gen 1 ohne Insider-Wissen!

---

## 🛠️ Hybrid-Klassifizierungs-System

### Problem: Automatik allein reicht nicht

**Warum?**
- Gen 3 (o1) ist unsichtbar (keine `<think>` Tags)
- Langsames Gen 1 Modell sieht aus wie Gen 2 (False Positive)
- Neue Modell-Familien erscheinen wöchentlich

**Lösung:** Kombination aus Auto-Detection + Manual Override

---

## 🚀 Workflow: Neue Modelle pflegen

### Dein täglicher Workflow

1. **Leaderboard generieren:**
   ```bash
   make leaderboard
   ```

2. **Auf Warnungen achten:**
   ```
   ⚠️  REVIEW NEEDED: neues-modell:14b
       → Metrics indicate Reasoning model but name unknown
   ```

3. **Entscheiden:**
   - **Fall A:** Standard-Modell (nur langsam oder Glückstreffer)
     → Eintrag in `model_overrides.yaml`

   - **Fall B:** Echtes Gen 2 Modell (neue Reasoning-Familie)
     → Eintrag in `generation_heuristics.yaml` (wenn Familie)  
     → Oder `model_overrides.yaml` (wenn Einzelfall)

---

## ⚙️ Konfigurations-Dateien

### 1. `model_overrides.yaml` (Dein Cockpit)

**Zweck:** Einzelentscheidungen für spezifische Modelle

**Priorität:** Höchste (überschreibt alles)

**Beispiel:**

```yaml
overrides:
  # Standard-Modell, das fälschlicherweise als Gen 2 erkannt wurde
  qwen3:8b:
    generation: Gen 1 (Pattern Matcher)
    reason: Standard Model, just slow execution time
    last_reviewed: '2026-02-01'

  # Unbekanntes Modell, dessen Herkunft unklar ist
  cogito:14b:
    generation: Gen 1 (Pattern Matcher)
    reason: High score but no evidence of reasoning training
    last_reviewed: '2026-02-01'

  # o1-Modell (Gen 3 - nicht automatisch erkennbar)
  o1-preview:
    generation: Gen 3 (Distilled Reasoner)
    reason: OpenAI o1 family - RL training without traces
    last_reviewed: '2026-02-01'
```

---

### 2. `generation_heuristics.yaml` (System-Update)

**Zweck:** Patterns für ganze Modell-Familien

**Wann bearbeiten:** Nur wenn eine **neue Klasse** von Modellen erscheint

**Beispiel:**

```yaml
patterns:
  gen2_names:
    - "phi4"           # Matches phi4:14b, phi4-medium, etc.
    - "r1"             # Matches deepseek-r1, llama-r1, etc.
    - "reasoning"      # Matches any model with "reasoning" in name
    - "think"          # Matches qwen-think, mistral-think, etc.
```

**Wenn du hier `- "gemma4"` hinzufügst:**
- Alle Gemma 4 Varianten (8b, 27b, instruction) werden automatisch als Gen 2 erkannt

---

## 🧠 Auto-Detection-Logik

Das Skript `scripts/classify_generation.py` nutzt eine 3-Stufen-Hierarchie:

### Stufe 1: Override Check (Höchste Priorität)

```python
if model in model_overrides:
    return model_overrides[model]['generation']
```

**Wenn Modell in `model_overrides.yaml`:** Nimm diesen Wert (Ende).

---

### Stufe 2: Auto-Metrik Check (High Confidence)

```python
if avg_time > 40 and reasoning_score > 70:
    # Sehr langsam + sehr schlau = vermutlich Gen 2
    if model_name_matches_pattern():
        return "Gen 2 (Reasoner)"
    else:
        # Flag for review
        return "Gen 1 (Pattern Matcher)" + WARNING
```

**Kriterien:**
- Durchschnittliche Antwortzeit > 40s
- Reasoning Score > 70%
- Name enthält bekannte Pattern (r1, phi4, etc.)

---

### Stufe 3: Heuristik Check

```python
if any(pattern in model_name for pattern in gen2_patterns):
    return "Gen 2 (Reasoner)"
```

**Wenn Name Pattern matched:** Automatisch Gen 2.

---

### Stufe 4: Fallback / Review

```python
# Metriken deuten auf Gen 2 hin, aber Name unbekannt
if metrics_indicate_gen2() and not name_known():
    print("⚠️  REVIEW NEEDED: " + model)
    return "Gen 1 (Pattern Matcher)"  # Safe Default
```

**Warnung im Terminal:** Du musst manuell entscheiden.

---

## ❓ FAQ: Wann was nutzen?

### Q: Wann `model_overrides.yaml`?

**A:** Immer, wenn du **sofort** handeln musst:
- Neues Modell getestet, Klassifizierung falsch
- Einzelfall (nicht ganze Familie)
- Unsicher → lieber Override (kann später in Heuristics verschoben werden)

---

### Q: Wann `generation_heuristics.yaml`?

**A:** Nur wenn eine **ganze Familie** erscheint:
- Gemma 4 führt Reasoning ein
- Neue Mistral-Serie mit `<think>` Tags
- Qwen 3 hat neue Reasoning-Variante

**Faustregel:** Wenn du denkst "Das wird öfter vorkommen" → Heuristics

---

### Q: Was ist mit o1-Modellen?

**A:** **Immer manuell** in `model_overrides.yaml` eintragen.

**Grund:** Gen 3 ist nicht automatisch erkennbar (keine `<think>` Tags, mittlere Speed).

---

## 🎯 Best Practices

### DO's ✅

1. **Leaderboard regelmäßig prüfen** (nach jedem Batch-Run)
2. **Warnungen ernst nehmen** (Review Needed = Handlungsbedarf)
3. **Overrides dokumentieren** (Feld `reason` ausfüllen)
4. **Date tracken** (`last_reviewed` Datum setzen)

---

### DON'Ts ❌

1. **Nicht alle Modelle manuell eintragen** (Heuristics nutzen!)
2. **Nicht raten** (Lieber Gen 1 Default + Warning)
3. **Nicht Pattern-Spam** (Zu generische Pattern wie "llama" vermeiden)

---

## 🔗 Verwandte Dokumentation

- **ARCHITECTURE.md** – Wie Klassifizierung technisch funktioniert
- **GOLDEN_STANDARDS.md** – Performance Ratio & Benchmarking
- **USER_GUIDE.md** – Wie Leaderboard-Badges vergeben werden

---

## 📜 Lizenz-Hinweis

Die Klassifizierungs-Logik und Config-Dateien sind Teil von CrucibleMark und unterliegen der **Apache License 2.0**.

**Siehe:** `LICENSE` für Details.

---

**Dokumenten-Version:** 1.0.0 (Rewrite Feb 2026)  
**Kompatibel mit:** CrucibleMark v0.9.5+
