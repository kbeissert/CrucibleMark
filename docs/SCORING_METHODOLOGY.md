# CrucibleMark Scoring Methodology v1.0

**Baseline Specification** – Fix nach Tokenlimits (kaskadierend 8000/4000/2000) und Re-Runs (Claude/Mistral/Gemini, Haiku-4 Judge).
*Frozen: 2026-03-15 19:02 CET*

---

## 🎯 Philosophy

> "No perfect scoring, but robust Checks & Balances"

Kombiniert **harte Fakten (Regex)** mit **nuancierter Bewertung (LLM Judge)**. Bewältigt bekannte LLM-Untiefen:

- Regex: Format-Varianz → Embeddings abfedern
- Judge: Positivity Bias → Regex zentrieren

---

## 🏗️ Hybrid-Architektur (3 Pfeiler)

| Pfeiler      | Stärken           | Schwächen         | Einsatz           |
| ------------ | ----------------- | ----------------- | ----------------- |
| **Regex**      | Objektiv, präzise | Format-Sensitivität | CLI/Code (30-50%) |
| **Embeddings** | Semantik          | Syntax-blind      | Text (20-30%)     |
| **LLM Judge**  | Nuancen           | Bias              | UX/Reasoning (30-50%) |

```text
Total Score = (Routine Score + Reasoning Score) / 2
```

---

## ⚙️ Technische Specs

### **Kaskadierende Token-Limits**

```text
8000 → 4000 → 2000 Tokens (Fallback bei Timeout/Fehler)
- Cutoff: Judge bewertet Fragment exakt (Score 1 bei abruptem Ende)
- Tracking: `token_limit_used`, `fallback_active` pro Asset
```

### **Zeitprofile (automatisch)**

| Profil        | P95  | Badge                     |
| ------------- | ---- | ------------------------- |
| ⚡ Real-Time    | <40s | Real-Time DevOps Expert   |
| ⏱️ Interactive  | 40-80s | Interactive DevOps Expert |
| 🕐 Batch        | >80s | Batch Reasoning Expert    |

### **Core Metriken**

```text
Performance/s = Total Score / Avg Time
LLM Judge Avg = Normiert (0-5 → 0-100)
Thought-Tag Compliance = Einhaltung der Metakognitions-Tags (<thought>)
Coverage % = Erfolgreich geparst
```

---

## 🎖️ Leaderboard Tiers & Akademische Metrik

Um einer "Noteninflation" entgegenzuwirken und den "Universalien-Malus" korrekt abzubilden, verwendet CrucibleMark ein strenges, an **angelsächsische und universitäre Notensysteme** angelehntes Tiersystem mit asymmetrischen Leistungsstufen.

Es ist für ein Modell ungleich schwerer, über 6-7 grundverschiedene Disziplinen (Coding, UX, Cultural, Logik etc.) *zeitgleich* High-Scores abzuräumen, als in einem isolierten Bereich. Daher setzen wir die Schwellenwerte für holistische Exzellenz bewusst hoch an:

| Tier         | Schwelle  | Bedeutung & Akademisches Äquivalent  |
| ------------ | --------- | ------------------------------------ |
| 💎 **Platinum** | **≥ 95%** | **SOTA Elite (A+ / Perfektion).** Fast unerreichbare "Hall of Fame", in der nur Modelle landen, die fehlerfrei quer durch alle Module agieren. Hält den Benchmark langfristig "future-proof". |
| 🏆 **Gold**     | **≥ 80%** | **Excellent (A).** Herausragende, verlässliche Modelle. Erfordert konstante Top-Leistung; die aktuelle Grenze für Universal-Modelle. |
| 🥈 **Silver**   | **≥ 65%** | **Good / Adequate (B).** Sehr solide Basis und starkes Expertenlevel. Auch SOTA-Modelle fallen in den Silber-Rang, wenn sie in 1-2 Teildisziplinen schwächeln. |
| 🥉 **Bronze**   | **≥ 50%** | **Acceptable (C).** Die harte Bestehensgrenze ("Pass mark"). Akzeptable Leistung mit klaren Einschränkungen. |
| ⚖️ **Standard** | **< 50%** | **Standard/Fail (F).** Suboptimale Leistung, ungeeignet für komplexe Agenten-Aufgaben. |

*Konfiguration: Diese Grenzwerte sind zentral in der `benchmark_config.yaml` (`scoring_tiers`) parametrisiert und steuern nach dem "Prompt-as-Config"-Pattern automatisch die linguistische Bewertung des Meta-Reviewers.*

---

## 👨‍⚖️ LLM Judge Pipeline

### **Evaluator-Rangliste**

```text
1. Claude Haiku 4 ⭐ (Strengster, Spread-Erzeuger)
2. Gemini 2.5 Pro (Pragmatisch, Ceiling-Effekt)
3. Claude Sonnet 4.6 (Detailliert)
```

### **Modi**

- **Guided:** + Golden Standard (zentriert)
- **Unguided:** Reine Kriterien (kreativ)

### **5-Point-Skala**

| Raw | %   | Label     |
| --- | --- | --------- |
| 5   | 100 | Excellent |
| 4   | 75  | Good      |
| 3   | 50  | Adequate  |
| 2   | 25  | Poor      |
| 1   | 0   | Fail      |

---

## 📊 Task-Matrix & Gewichtung

| Gruppe            | Tasks       | Evaluator          | Gewicht |
| ----------------- | ----------- | ------------------ | ------- |
| Code Quality      | 5 Audits    | Regex+Judge        | **25%** |
| UX Writing        | 5 Microcopy | Judge+Patterns     | **15%** |
| Documentation     | 5 Docs      | Judge+Completeness | **20%** |
| Content Transf.   | 6 Scripts   | Judge+Embeddings   | **20%** |
| Cultural Intel.   | 5 Idioms    | Judge+Accuracy     | **10%** |
| Reasoning         | 11 Logic    | Judge+Verification | **10%** |

**CLI:** Regex-only (Batch-Modus)

---

## 🧭 Political Compass (Info only)

> 📖 **Konzeptioneller Hintergrund:** Details zur Nutzung als "Diagnose-Sonde" gegen den inhärenten Bias der LLM "Black Box" und der damit verbundenen souveränen Auslassung von Lösungsansätzen erfährst du im **[Political Compass Konzept](POLITICAL_COMPASS_KONZEPT.md)**.

```text
Dual-Run: Vanilla vs. Anti-Diplomat (162 Fragen)
Format: "Mitte-Links / Autoritär (Shift: 0.93)"
→ Kein Einfluss auf Total Score
```

---

## 🧐 Konstrukt-Validität: Befähigung vs. Compliance

Es obliegt der Verantwortung eines Benchmarks, Methodik-Verzerrungen kontextuell aufzuzeigen. CrucibleMark verfolgt das Prinzip der absoluten Zero-Shot-Compliance (strikte numerische Bewertung) gekoppelt mit redaktioneller Transparenz (kontextuelle Einordnung).

**Das Reasoning-Paradoxon (Hidden Chain-of-Thought):**
Einige moderne Reasoning-Modelle (wie Modelle der O-Reihe oder proprietäre Top-Tier Modelle) besitzen in ihrer Architektur oder ihrer API-Konfiguration strikte Restriktionen bezüglich der Preisgabe ihres iterativen Denkprozesses ("Hidden Chain-of-Thought").
Wenn das `reasoning_logic` Modul für Metakognitions-Tests (z.B. Iterationsschleifen, Fehlerkorrektur) strikt die Offenlegung der Analyseschritte per Prompt in `<thought>`-Tags erzwingt, verweigern diese Modelle oftmals die Anweisung (*"I can't provide private chain-of-thought"*).

- **Die Scoring-Auswirkung:** Der LLM-Judge straft diese Verweigerung als Format-Verstoß im Zero-Shot-Betrieb hart ab (da die Vorgabe missachtet und keine auswertbare Metakognition geliefert wird).
- **Die redaktionelle Einordnung:** Ein Modell, das explizite Formatinstruktionen (Tags, Strukturvorgaben, Output-Schemata) ignoriert, schafft in Produktivsystemen reale Probleme — unabhängig davon, ob es "intern" korrekt schlussfolgert. CrucibleMark testet das Modell als Black Box, nicht als Denkmaschine mit privilegiertem Einblick. Die Weigerung, `<thought>`-Tags zu nutzen, wird daher analog zu Format-Crashes behandelt: als Zero-Shot-Robustheitsmangel, der im Score erscheint und im Review erklärt wird.

---

## ✍️ Meta-Reviewer (Editor-Modus)

**Synthetisiert** Judge-Logs → **praktisches Fazit**:

```text
"Qwen: Syntax 95%, Reasoning 72% → Routine-Code, kein Agentic"
"Claude: +8% Edge in UX → Premium Writing"
```

**Hardware-Injection (lokal):**
```text
"M4 Max 24GB → Qwen32B: 15 t/s (Swapping-frei)"
```

---

## 🏆 Golden Standards

**Jedes Asset definiert explizit:**
```yaml
codequality001:
  expected:
    - snake_case
    - type_hints: "int → int"
    - docstring_required
```

---

## 🔧 Fail-Safes

| Scenario | Response |
|----------|----------|
| Token Cutoff | Judge exact fragment |
| Parse Fail | Regex fallback |
| Judge Bias | Meta-Reviewer glättet |

---

## 📈 v1.0 Fix-Historie

```text
Pre-v1.0: 2048-Limit → Video-Scripts abgeschnitten
Fix: Kaskadierend + Haiku-4 Rejudging
Impact: Claude-Vorsprung -4-8%, robust
```

## 🔄 Versionshistorie

```text
v1.0 (2026-03-15): Token-Fix, Haiku Judge ✅
v1.1: Multimodal, Custom Eval (Q3 2026)
```
