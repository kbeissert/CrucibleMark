# Editorial Audit Report — 2026-04-07

**Scope:** Alle 7 Benchmark-Module (44 Assets)  
**Durchgeführt von:** GitHub Copilot (Claude Sonnet 4.6) im Auftrag des Projekt-Maintainers  
**Validierung:** `make validate` — 44/44 ✓, 0 Invalid

---

## 1. Executive Summary

Der Editorial Audit hat systematisch alle YAML-Assets aller 7 CrucibleMark-Benchmark-Module auf Prompt-Qualität, Constraint-Schärfe und redaktionelle Konsistenz geprüft. Dabei wurden **30 Einzeländerungen in 21 Assets** umgesetzt. Kein Asset wurde inhaltlich verändert: alle Änderungen betreffen ausschließlich Instruktions-Formulierungen, nie Golden Standards oder Scoring-Logik.

Es wurden drei systemische Befundmuster identifiziert, die auf Gemini-generierte Ursprungsversionen der Assets zurückzuführen sind. Diese Muster schwächen Prompt-Constraints ab und wurden vollständig bereinigt.

---

## 2. Modul-Übersicht

| Modul | Assets gesamt | Assets geändert | Änderungen | Befund-Kategorien |
|---|---|---|---|---|
| `cultural_intelligence` | 5 | 4 | 5 | Befund C (Pseudolabel), Befund D (Kyrillisch), Befund E (GS-Grammatik) |
| `ux_writing` | 5 | 5 | 12 | Befund A (Bitte), Befund B (Token-Limit-Leak), Befund F (Erfülle-Floskel) |
| `content_transformation` | 6 | 5 | 6 | Befund A (Bitte), Befund B (Token-Limit-Leak) + 1 Tippfehler |
| `documentation_quality` | 5 | 4 | 4 | Befund A (Bitte), Befund B (Token-Limit-Leak) |
| `reasoning_logic` | 11 | 0 | 0 | Kein Befund |
| `code_quality` | 5 | 3 | 3 | Befund B (Token-Limit-Leak) |
| `cli_benchmark` | 6 | 0 | 0 | Kein Befund |
| **Gesamt** | **43** | **21** | **30** | |

---

## 3. Systemische Befunde

### Befund A — Höflichkeitsformel „Bitte" in imperativen Instruktionen

**Betroffene Module:** `ux_writing`, `content_transformation`, `documentation_quality`  
**Anzahl Treffer:** 13

**Muster:**
```
WICHTIG: Bitte liste zuerst explizit alle gefundenen Probleme auf …
```

**Problem:** Die Konjunktion „Bitte" signalisiert Anfrage statt Constraint. In imperativen Prompt-Instruktionen schwächt sie das Gewicht der Anforderung ab. LLMs mit niedrigerem Instruction-Following behandeln höfliche Formulierungen als optional.

**Fix:** Konjunktion gestrichen. Imperativform direkt und ohne Einleitung.

---

### Befund B — Token-Limit-Leak

**Betroffene Module:** `ux_writing`, `content_transformation`, `documentation_quality`, `code_quality`  
**Anzahl Treffer:** 13

**Muster (Varianten):**
```
… um Token-Limits nicht zu überschreiten/sprengen.
… um Token-Limits für die finale Version nicht zu gefährden.
… um Puffer für das finale Resultat und die Token-Limits zu bewahren.
… um Token-Limits sicher einzuhalten.
… um Output-Token-Limits zu respektieren.
… um keine Token zu verschwenden.
```

**Problem:** Die interne Begründung (`um Token-Limits …`) wird an das Modell weitergegeben. Damit wird das technische Implementierungsdetail des Benchmark-Systems Teil des Prompts. Das hat zwei negative Effekte: (1) Das Modell lernt, dass der Prompt unter Ressourcendruck steht, und kürzt möglicherweise inhaltlich relevante Ausgaben pauschal. (2) Die Formulierung erzeugt keine messbare Constraint — sie liefert einen vagen Wunsch ohne operationale Schranke.

**Fix:** Interne Begründung vollständig entfernt, stattdessen direkte quantitative Schranke formuliert (z. B. `Analyse: maximal 3–4 Sätze.`).

---

### Befund C — Gemini-Pseudolabels als Prompt-Strukturelemente

**Betroffene Module:** `cultural_intelligence`  
**Anzahl Treffer:** 2

**Muster:**
```
Mission: Remove ALL corporate buzzwords. Output must sound …
TASK: Convert all formal language …
```

**Problem:** `Mission:` und `TASK:` sind strukturelle Artefakte aus Gemini-generierten Prompts, die in anderen Kontexten (z. B. System-Prompt-Templates) verwendet werden. Als Präfixe in Aufgabenbeschreibungen sind sie redundant und erzeugen unnötige semantische Hierarchien, die bei anderen Modellen zu Verwirrung über Prompt-Struktur führen können.

**Fix:** Label gestrichen, Aufgabenbeschreibung direkt als Imperativsatz formuliert.

---

### Befund D — Kyrillische Unicode-Artefakte

**Betroffene Module:** `cultural_intelligence` (asset_6a)  
**Anzahl Treffer:** 3 Zeichen (1 Fundstelle)

**Muster:**
```
Idioматisches  →  Idiomatisches
       ^^^
       U+043C (м), U+0430 (а), U+0442 (т) — kyrillisch
```

**Problem:** Das Wort `Idiomatisches` enthielt drei kyrillische Zeichen, die optisch mit den lateinischen Entsprechenden identisch aussehen. Die Zeichenmenge `м а т` (Kyrillisch) und `m a t` (Latein) sind in den meisten Schriftarten nicht unterscheidbar. Als Originalquelle ist Gemini bekannt, das gelegentlich bei der Verarbeitung gemischter Skript-Kontexte falsche Unicode-Blöcke verwendet. Das Artefakt bleibt ohne Scan unentdeckt und kann Tokenizer-Verhalten, Matching und Scoring beeinflussen.

**Fix:** Drei kyrillische Zeichen durch korrekte lateinische ersetzt. Aktiver Scan mit `ord(ch) in range(0x400, 0x500)` auf alle Module ausgeweitet — alle übrigen 42 Assets clean.

---

### Befund E — Golden Standard Grammatikfehler

**Betroffene Module:** `cultural_intelligence` (asset_6e)  
**Anzahl Treffer:** 1

**Muster:**
```
ein negatives Entwicklung  →  eine negative Entwicklung
```

**Problem:** Falscher Artikel im deutschen Golden Standard. Da der Golden Standard die Referenz für die automatische Bewertung durch den LLM-Judge ist, kann ein Grammatikfehler darin — je nach Judge-Modell — zu fehlerhafter Bewertung von korrekten Kandidaten-Outputs führen.

**Fix:** Artikel und Adjektivflexion korrigiert.

---

### Befund F — „Erfülle dabei strikt"-Floskel

**Betroffene Module:** `ux_writing`  
**Anzahl Treffer:** 5

**Muster:**
```
Erfülle dabei strikt die folgenden Anforderungen:
```

**Problem:** Die Konstruktion `Erfülle dabei strikt … die folgenden Anforderungen:` ist semantisch schwach. „Dabei" ist ein kontextueller Füllbegriff ohne Referenzpunkt. Die Formulierung imitiert Autorität, ohne sie zu erzeugen. Direktere Constraint-Formulierungen haben messbar bessere Instruction-Following-Quoten.

**Fix:** Ersetzt durch `Anforderungen (strikt einhalten):` — kompakter, direkter, ohne Füllwort.

---

## 4. Empfehlungen für zukünftige Asset-Erstellung

### 4.1 Keine Token-Budget-Hinweise im Prompt
Interne System-Constraints (Kontextfenster, Ausgabelänge) gehören nicht in den Prompt. Stattdessen: direkte quantitative Schranke definieren (`Analyse: max. 3 Sätze.`). Das Modell muss den Grund nicht kennen.

### 4.2 Kyrillisch-Scan nach AI-generiertem Content
Nach jeder AI-gestützten Asset-Erstellung (insbesondere durch Gemini) sollte ein automatischer Scan auf kyrillische Unicode-Codepoints (`U+0400–U+04FF`) laufen. Empfehlung: als Pre-Commit-Hook oder in `make validate` integrieren.

### 4.3 Imperative Instruktionen ohne Höflichkeitsformeln
In WICHTIG/HINWEIS-Blöcken gilt: kein `Bitte`, kein `Würdest du`, kein `Wenn möglich`. Instruktionen sind Constraints, keine Anfragen. Direktform.

### 4.4 Gemini-Strukturlabels als Review-Signal
Vorkommen von `TASK:`, `Mission:`, `Step N:` als eigenständige Prefixe (nicht als Markdown-Strukturelement) sind ein zuverlässiger Indikator für unrevidierte Gemini-Output-Fragmente. Review gezielt auf diese Muster trimmen.

### 4.5 Golden Standards gegen Sprachfehler reviewen
Golden Standards sind die Bewertungsreferenz. Ein einziger Grammatikfehler darin kann die Judge-Bewertung systematisch verzerren. Empfehlung: GS-Texte beim Asset-Review immer explizit auf Sprachkorrektheit prüfen — besonders bei Assets mit mehrsprachigem Kontext.

---

*Audit abgeschlossen: 2026-04-07 — 44/44 Assets validiert, 0 Fehler.*
