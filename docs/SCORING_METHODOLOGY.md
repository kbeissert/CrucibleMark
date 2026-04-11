# CrucibleMark Scoring Methodology v1.0

**Baseline-Spezifikation** – Fix nach Tokenlimits (kaskadierend 8000/4000/2000) und Re-Runs (Claude/Mistral/Gemini, Haiku-4 Judge).
*Eingefroren: 2026-03-15 19:02 CET*

---

## 🎯 Philosophie

> „Kein perfektes Scoring, aber robuste Checks & Balances"

Das Scoring kombiniert **harte Fakten (Regex)** mit **nuancierter Bewertung (LLM Judge)** und bewältigt typische LLM-Schwachstellen:

- Regex: Format-Varianz → Embeddings abfedern
- Judge: Positivity Bias → Regex zentrieren

---

## 🏗️ Hybrid-Architektur (3 Pfeiler)

| Pfeiler | Stärken | Schwächen | Einsatz |
| ------------ | ----------------- | ----------------- | ----------------- |
| **Regex** | Objektiv, präzise | Format-Sensitivität | CLI/Code (30–50 %) |
| **Embeddings** | Semantik | Syntax-blind | Text (20–30 %) |
| **LLM Judge** | Nuancen | Bias | UX/Reasoning (30–50 %) |

```text
Total Score = Σ(ModuleScore × module_weight) / Σ(module_weight)
```

### Modulgewichtung (`module_weight`)

Ab v3.4.x wird der Total Score über ein **selbstnormalisierendes Gewichtungsschema** berechnet. Jedes Modul trägt mit seinem konfigurierten `module_weight` bei — unabhängig von der Anzahl seiner Assets. Das Ergebnis bleibt immer im Bereich 0–100, egal wie viele Module aktiv sind.

**Default-Werte (alle aktiven Module):**

| Modul | `module_weight` | Einfluss (Standard-Setup) |
|---|---|---|
| Code Quality Audit | 1.0 | ~14.9 % |
| Logical Reasoning | 1.0 | ~14.9 % |
| UX Writing & Microcopy | 1.0 | ~14.9 % |
| Documentation Quality | 1.0 | ~14.9 % |
| Content Transformation | 1.0 | ~14.9 % |
| Cultural Intelligence | 1.0 | ~14.9 % |
| CLI Badge | **0.5** | **~7.7 %** |

CLI ist als leichtgewichtiges Supplement konzipiert (Syntax-Recall-Test, kein tiefes Reasoning) und erhält daher `0.5`. Alle anderen Module sind vollwertige, gleichgewichtete Alltagsdimensionen.

**Konfiguration:** `module_weight` liegt in `benchmark_modules/<id>/config.yaml` unter `integration.leaderboard.module_weight`. Fehlt der Wert, greift Fallback `1.0` (Rückwärtskompatibilität). Der Wert ist rein relativ — er muss nicht zu einer festen Summe aufsummieren.

---

## ⚙️ Technische Specs

### Kaskadierende Token-Limits

```text
8000 → 4000 → 2000 Tokens (Fallback bei Timeout/Fehler)
- Cutoff: Der Judge bewertet das Fragment exakt (Score 1 bei abruptem Ende)
- Tracking: `token_limit_used`, `fallback_active` pro Asset
```

### Token-Budget-System (Output-Cap für Vergleichbarkeit)

Ab v3.4.0 setzt `base_runner.py` für definierte Module einen direkten `max_tokens`-API-Parameter, um Provider-übergreifende Vergleichbarkeit sicherzustellen. Das Budget wird aus `benchmark_config.yaml → token_budgets` gelesen — nur wenn ein Wert gesetzt ist (`None` wird nicht weitergegeben).

```text
Kalibrierte Werte (2× Modul-Median):
  cultural_intelligence:   500 Tokens
  ux_writing:             3500 Tokens
  content_transformation: 3500 Tokens
  documentation_quality:  6000 Tokens
  code_quality:           6000 Tokens
  cli_benchmark:          kein Limit (not set)
  reasoning_logic:        kein Limit (by design)
```

Wenn ein Modell das Budget vollständig ausschöpft (`finish_reason: length`), wird `token_limit_cutoff=True` im `BenchmarkResult` gesetzt und ein `[!NOTE]`-Block ins Audit-Log injiziert.

### Zeitprofile (automatisch)

| Profil | P95 | Badge |
| ------------- | ---- | ------------------------- |
| ⚡ Real-Time | < 40s | Real-Time DevOps Expert |
| ⏱️ Interactive | 40–80s | Interactive DevOps Expert |
| 🕐 Batch | > 80s | Batch Reasoning Expert |

### Core Metriken

```text
Tokens/s = mean(tokens_per_second) über alle Nicht-System-Assets
LLM Judge Avg = Normiert (0-5 → 0-100)
Thought-Tag Compliance = Einhaltung der Metakognitions-Tags (<thought>)
Coverage % = Erfolgreich geparst
```

> **Hinweis:** Der `Efficiency Score` (Total Score / Avg Time) wurde in v3.4.3 entfernt.
> Drei saubere, unabhängige Dimensionen ersetzen ihn: `Total Score`, `Avg Task Duration (s)`, `Tokens/s`.

### Token-Verbrauch im Leaderboard

Ab v3.4.x enthält das Leaderboard zwei neue Spalten für den Token-Verbrauch:

| Spalte | Wo | Beschreibung |
|---|---|---|
| `Tokens Total` | Compact + Detailed | Summe aller Output-Token über den gesamten Benchmark-Lauf |
| `Tokens: <Modul>` | Detailed only | Summe der Output-Token pro Modul (z. B. `Tokens: Code Quality`) |

> **Hinweis zur Datenbasis:** Beide Spalten verwenden ausschließlich Module mit `enable_scoring: true` — dieselbe Basis wie der Total Score. Module mit `enable_scoring: false` (z. B. Political Compass) werden ausgeschlossen, da deren Re-Test-Mengen variieren und ansonsten den Provider-Vergleich verzerren würden.

**Warum Token-Verbrauch relevant ist:**

Bei API-Schnittstellen wie OpenAI (Pay-per-Token) kostet jeder Output-Token Geld — GPT-4o liegt bei ~$15/1M Output-Token. Wenn ein Modell im Benchmark für dieselbe Aufgabe 8.000 statt 1.500 Token produziert, ist das ein **5× Kostenmultiplikator** im Produktionsbetrieb.

Im Gegensatz dazu arbeiten ChatGPT Plus/Pro-Abos mit einer Flat-Rate, bei der der Token-Verbrauch für den Endnutzer nicht direkt sichtbar ist. **Wer KI-APIs kommerziell einsetzt, muss diesen Unterschied kennen.**

Die `Tokens Total`-Spalte macht Token-Hunger direkt sichtbar und ergänzt `Cost per 1K (USD)` als zweite Kostendimension:
- `Cost per 1K (USD)` zeigt den Preis pro 1.000 Token bei API-Modellen
- `Tokens Total` zeigt, wie viele Token ein Modell für den Benchmark insgesamt verbraucht hat

Kombiniert ergibt sich: **Token-hungrige Modelle sind bei API-Nutzung teurer**, auch wenn ihr Score vergleichbar ist.

> **Hinweis zu Cloud Open-Weights Modellen (Groq, DeepSeek, MiniMax):** Für Modelle wie Llama,
> Qwen oder Kimi K2, die direkt über die Groq-Cloud-API laufen, wird der **Paid-Tier-Preis**
> hinterlegt — also der Preis, der bei kommerzieller API-Nutzung nach Ablauf des kostenlosen
> Kontingents anfällt. CrucibleMark selbst nutzt den Free Tier von Groq. Die Kostenangaben
> spiegeln daher den **potenziellen Produktionspreis** wider.
>
> **Ollama als Cloud-Proxy:** Im Benchmark sind einige Modelle mit dem `:cloud`-Tag versehen
> (z. B. `deepseek-v3.2:cloud`, `minimax-m2.7:cloud`, `gpt-oss:120b-cloud`). Diese Modelle
> laufen nicht lokal, sondern nutzen Ollama lediglich als Schnittstellen-Proxy zu den
> jeweiligen Provider-APIs. Interessant dabei: `gpt-oss:120b-cloud` leitet Anfragen intern
> über **Groq’s Inferenz-Infrastruktur** weiter — d. h. zwei scheinbar verschiedene
> Anbieter teilen sich dieselbe Backend-Infrastruktur. Die hinterlegten Preise stammen jeweils
> aus den Paid-Tier-Tarifen der tatsächlichen Provider-APIs (DeepSeek, MiniMax, Groq).

> **Grundannahme Token-Messung:** Die von der API gemeldeten `completion_tokens` entsprechen exakt den abgerechneten Tokens auf dem Provider-Dashboard. CrucibleMark trifft keine eigene Token-Zählung — es verlässt sich auf die Provider-Angabe. Kommerzielle Provider haben keinen Anreiz, Output-Tokens zu verschweigen, da diese direkt abgerechnet werden. Lokale Modelle (Ollama) haben ebenfalls keinen Anreiz zur Verschleierung: Fehlerhafte Token-Zählungen würden durch Community-Tests und reproduzierbare Benchmarks schnell aufgedeckt und das Vertrauen in den Anbieter oder das Modell nachhaltig beschädigen.

---

## 🎖️ Leaderboard Tiers & Akademische Metrik

Um Noteninflation entgegenzuwirken und den „Universalien-Malus" korrekt abzubilden, nutzt CrucibleMark ein strenges, an angelsächsische und universitäre Notensysteme angelehntes Tiersystem mit asymmetrischen Leistungsstufen.

Über sechs bis sieben grundverschiedene Disziplinen (Coding, UX, Cultural, Logik u. a.) zeitgleich High-Scores zu erzielen, ist ungleich schwerer als in einem isolierten Bereich. Daher liegen die Schwellenwerte für holistische Exzellenz bewusst hoch.

| Tier | Schwelle | Bedeutung & Akademisches Äquivalent |
| ------------ | --------- | ------------------------------------ |
| 💎 **Platinum** | **≥ 95 %** | **SOTA Elite (A+ / Perfektion).** Fast unerreichbare „Hall of Fame" für Modelle, die fehlerfrei quer durch alle Module agieren. Hält den Benchmark langfristig „future-proof". |
| 🏆 **Gold** | **≥ 80 %** | **Excellent (A).** Herausragende, verlässliche Modelle. Erfordert konstante Top-Leistung. |
| 🥈 **Silver** | **≥ 65 %** | **Good / Adequate (B).** Sehr solide Basis und starkes Expertenlevel. Auch SOTA-Modelle fallen in den Silver-Rang, wenn sie in ein bis zwei Teildisziplinen schwächeln. |
| 🥉 **Bronze** | **≥ 50 %** | **Acceptable (C).** Die harte Bestehensgrenze. Akzeptable Leistung mit klaren Einschränkungen. |
| ⚖️ **Standard** | **< 50 %** | **Standard/Fail (F).** Suboptimale Leistung, ungeeignet für komplexe Agenten-Aufgaben. |

*Konfiguration: Diese Grenzwerte sind zentral in der `benchmark_config.yaml` (`scoring_tiers`) parametrisiert und steuern nach dem „Prompt-as-Config"-Pattern automatisch die linguistische Bewertung des Meta-Reviewers.*

---

## 👨‍⚖️ LLM Judge Pipeline

### Evaluator-Rangliste

```text
1. Claude Haiku 4 ⭐ (Strengster, Spread-Erzeuger)
2. Gemini 2.5 Pro (Pragmatisch, Ceiling-Effekt)
3. Claude Sonnet 4.6 (Detailliert)
```

### Modi

- **Guided:** mit Golden Standard (zentriert)
- **Unguided:** reine Kriterien (kreativ)

### 5-Punkt-Skala

| Raw | % | Label |
| --- | --- | --------- |
| 5 | 100 | Excellent |
| 4 | 75 | Good |
| 3 | 50 | Adequate |
| 2 | 25 | Poor |
| 1 | 0 | Fail |

---

## 📊 Task-Matrix & Gewichtung

| Gruppe | Tasks | Evaluator | Gewicht |
| ----------------- | ----------- | ------------------ | ------- |
| Code Quality | 5 Audits | Regex + Judge | **25 %** |
| UX Writing | 5 Microcopy | Judge + Patterns | **15 %** |
| Documentation | 5 Docs | Judge + Completeness | **20 %** |
| Content Transf. | 6 Scripts | Judge + Embeddings | **20 %** |
| Cultural Intel. | 5 Idioms | Judge + Accuracy | **10 %** |
| Reasoning | 11 Logic | Judge + Verification | **10 %** |

**CLI:** Regex-only (Batch-Modus)

---

## 🧭 Political Compass (nur informativ)

> 📖 **Konzeptioneller Hintergrund:** Details zur Nutzung als „Diagnose-Sonde" gegen inhärenten Bias und souveräne Auslassung von Lösungsansätzen: [Political Compass Konzept](POLITICAL_COMPASS_KONZEPT.md).

```text
Dual-Run: Vanilla vs. Anti-Diplomat (162 Fragen)
Format: "Mitte-Links / Autoritär (Shift: 0.93)"
→ Kein Einfluss auf Total Score
```

---

## 🧐 Konstrukt-Validität: Befähigung vs. Compliance

CrucibleMark verfolgt das Prinzip der absoluten Zero-Shot-Compliance (strikte numerische Bewertung) kombiniert mit redaktioneller Transparenz (kontextuelle Einordnung).

**Das Reasoning-Paradoxon (Hidden Chain-of-Thought):**
Einige Reasoning-Modelle (z. B. Modelle der O-Reihe oder proprietäre Top-Tier-Modelle) besitzen strikte Restriktionen bezüglich der Preisgabe ihres iterativen Denkprozesses ("Hidden Chain-of-Thought").

Wenn das `reasoning_logic`-Modul für Metakognitions-Tests die Offenlegung der Analyseschritte per Prompt in `<thought>`-Tags erzwingt, verweigern diese Modelle die Anweisung (*„I can't provide private chain-of-thought"*).

- **Scoring-Auswirkung:** Der LLM-Judge straft diese Verweigerung als Format-Verstoß im Zero-Shot-Betrieb hart ab.
- **Redaktionelle Einordnung:** Ein Modell, das explizite Formatinstruktionen (Tags, Strukturvorgaben, Output-Schemata) ignoriert, erzeugt in Produktivsystemen reale Probleme – unabhängig davon, ob es intern korrekt schlussfolgert. CrucibleMark testet das Modell als Black Box, nicht als Denkmaschine mit privilegiertem Einblick. Die Weigerung, `<thought>`-Tags zu nutzen, entspricht damit einem Format-Crash: als Zero-Shot-Robustheitsmangel, der im Score erscheint und im Review erklärt wird.

---

## ✍️ Meta-Reviewer (Editor-Modus)

Der Meta-Reviewer synthetisiert Judge-Logs zu einem praktischen Fazit:

```text
"Qwen: Syntax 95%, Reasoning 72% → Routine-Code, kein Agentic"
"Claude: +8% Edge in UX → Premium Writing"
```

**Hardware-Injection (lokal):**
```text
"M4 Max 24GB → Qwen32B: 15 t/s (Swapping-frei)"
```

**Token-Effizienz-Kontext (ab v3.4.0):**
Vor dem eigentlichen Log-Block erhält der Reviewer modulspezifische Verbosity-Metriken. Liegt die Ratio eines Modells > 1.5× Fleet-Median, ist ein dedizierter Diagnostik-Absatz im Report verpflichtend. Reasoning-Module sind ausgenommen.

---

## 🏆 Golden Standards

Jedes Asset definiert explizit:

```yaml
codequality001:
  expected:
    - snake_case
    - type_hints: "int → int"
    - docstring_required
```

---

## 🔧 Fail-Safes

| Szenario | Reaktion |
|----------|----------|
| Token Cutoff | Judge bewertet Fragment exakt |
| Parse Fail | Regex-Fallback |
| Judge Bias | Meta-Reviewer glättet |

---

## ⚠️ Hard Constraints & Automatische Penalties

Bestimmte Tasks definieren harte Anforderungen, die unabhängig vom inhaltlichen Score bestraft werden. Die Constraints werden über das `constraints`-Feld im Asset-YAML gesteuert.

### Wortanzahl-Constraint (`max_expected_words`)

Aktiv für: `ct003` (150W), `ct004` (600W), `ux_writing_005` (150W).

Die Penalty ist **progressiv gestaffelt** und nicht linear – ein leichtes Überschreiten (Rundungsfehler) wird mild bestraft, ein massives Ignorieren der Vorgabe hart:

| Überschreitung (word\_count / max\_words) | Penalty | Tier-Label im Audit-Log |
|---|---|---|
| ≤ 120% | **0%** | – (Toleranzzone) |
| 121–200% | **–20%** | Mild Overshoot (>120%) |
| 201–300% | **–40%** | Clear Violation (>200%) |
| > 300% | **–60%** | Constraint Ignored (>300%) |

```yaml
# In asset_XXX.yaml
constraints:
  max_expected_words: 150
```

Die Penalty wird auf den `total_achieved`-Score (CT-Evaluator) bzw. `total_score` (UX-Evaluator) angewendet, **nachdem** alle inhaltlichen Kriterien gewertet wurden. Eine 0 ist damit nicht möglich – inhaltliche Qualität bleibt unabhängig messbar.

Im Audit-Log erscheint der Constraint-Trigger als:
```
> [!WARNING]
> **[HARD CONSTRAINT VIOLATION – Constraint Ignored (>300%)]** The model ignored the
> explicit word count limit of 150 words. Word count detected: 674 (449% of limit).
> An automatic 60% deduction (-XX.XX pts) has been applied.
```

### Sprach-Mismatch (`language_mismatch`)

Falls ein Asset `metadata.language: de` deklariert, prüft der `unified_runner.py` die Antwort des Modells nach `score_response()` per heuristischer DE/EN-Marker-Frequenz:

- DE-Marker: `der`, `die`, `das`, `und`, `ist`, `mit`, `für`, u. a.
- EN-Marker: `the`, `and`, `for`, `with`, `that`, `this`, `are`, u. a.

**Trigger-Bedingung:** `en_count > de_count × 2` und `en_count > 8` (bei Antworten > 50 Wörter).

Bei Auslösung wird `result["status"] = "language_mismatch"` gesetzt und ein `> [!WARNING] [LANGUAGE MISMATCH]`-Block ins Audit-Log geschrieben. Die Penalty ist **kein Score-Abzug**, sondern ein isolierter Status-Flag – ein Modell kann gleichzeitig `correct_length` und `language_mismatch` sein; beide Dimensionen werden getrennt erfasst.

### Vollständige Status-Codes

| Status | Beschreibung |
|---|---|
| `success` | Reibungsloser Lauf |
| `error` | Technischer Fehler (API, Parse) |
| `truncated` | Antwort kürzer als Mindestlänge – Modell hat abgebrochen |
| `verbose_outlier` | Antwort massiv über Durchschnitt – mögliche Loop-Halluzination |
| `language_mismatch` | Antwort in falscher Sprache (EN auf DE-Task) |

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
v3.4.0 (2026-04-08): Token-Budget-System (max_tokens API-Cap), Verbosity-Diagnostik in Audit-Logs und Meta-Reviews ✅
v3.4.2 (2026-04-09): Vollständige Preis-Datenbasis in cost_limits.yaml; LLM Judge Avg als ★-Format im Leaderboard ✅
v3.4.3 (2026-04-10): module_weight-System — selbstnormierende Modulgewichtung entkoppelt Total Score von Asset-Anzahl; CLI-Modul als Supplement (0.5) ✅
v3.4.x (geplant): Score-Penalty für Token-Verbosity, Leaderboard-Metriken (avg_tokens, token_efficiency_ratio, est_cost_per_1k_tasks)
```
