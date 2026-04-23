# Modellklassifizierung & Badge-System

**Zielgruppe:** Alle, die verstehen wollen, wie CrucibleMark Modelle klassifiziert und bewertet.

**Inhalt:**

- Badge-System (Standard, Bronze, Silver, Gold, Platinum)
- Size-Class-System (Nano / Edge / Desktop / Workstation / Server / Frontier)
- Speed-Klassen (Fast, Medium, Slow)
- Skill-Profile (automatische Kategorisierung)
- Reasoning-Score-Interpretation
- Best Practices für neue Modelle

---

## Badge-System

Badges reflektieren die **Gesamt-Performance** über alle Module hinweg. Die kanonischen Schwellenwerte stehen in `benchmark_config.yaml` (`scoring_tiers`) – die folgende Tabelle gibt den aktuellen Stand wieder. Detaillierte Begründung: [SCORING_METHODOLOGY.md](SCORING_METHODOLOGY.md).

### Klassifizierung nach Total Score

| Badge | Score Range | Beschreibung | Beispiele (Feb 2026) |
|-------|-------------|--------------|----------------------|
| 💎 **Platinum** | ≥ 95,0 | SOTA Elite – unerreichter Maßstab | *(noch nicht erreicht)* |
| 🏆 **Gold** | ≥ 80,0 | Exzellente Gesamtleistung | Mistral Medium (81,3) |
| 🥈 **Silver** | 65,0–79,9 | Production-ready, gute Balance | Mistral Large (78,8), Ministral-3:14b (77,6), Cogito:14b (72,5) |
| 🥉 **Bronze** | 50,0–64,9 | Solide Basis, spezialisiert | *(abhängig vom aktuellen Leaderboard)* |
| ⚖️ **Standard** | < 50,0 | Entwicklungs-Stadium, limitiert | Dolphin-Llama3:8b (44,4) |

**Aktuelle Verteilung (16 Modelle):**

- Platinum: 0
- Gold: 1 (Mistral Medium, 6 %)
- Silver: ca. 10 (63 %)
- Bronze: ca. 4 (25 %)
- Standard: 1 (6 %)

---

## Size-Class-System (Deployment-Tiers)

CrucibleMark klassifiziert Modelle nach ihrer **Hardware-Deployment-Realität** — nicht nach abstrakten Capability-Scores. Die `Size Class`-Spalte im Leaderboard gibt an, auf welcher Hardware ein Modell praktisch einsetzbar ist.

**Erkennung:** Regex auf Ollama-Style-Tags (z. B. `qwen3:4b`, `cogito:14b`). Modelle ohne Size-Tag (kommerzielle APIs, Cloud-Proxies) landen automatisch in `Frontier`.

| Tier | Parameter | RAM (Q4) | Deployment-Realität |
|---|---|---|---|
| **Nano** | ≤ 4B | < 4 GB | Smartphone, Raspberry Pi, Autocomplete-only |
| **Edge** | 5–9B | 4–8 GB | Jeder aktuelle Laptop, MacBook Air M-Series |
| **Desktop** | 10B–19B | 8–14 GB | MacBook Pro, 14 GB Unified Memory |
| **Workstation** | 20B–35B | 14–24 GB | M4 Pro/Max, RTX 4090, High-End Consumer |
| **Server** | 36–75B | 24–48 GB | Mac Studio, Dedicated GPU-Node |
| **Frontier** | API-only / > 75B | — | Cloud-only, keine lokale Deployment-Option |

**Scope:** Alle Tiers durchlaufen exakt dieselben 44 Tasks mit derselben Bewertungsmethodik. Die Badge-Schwellen (Bronze, Silver, …) gelten unverändert — `Size Class` signalisiert ausschließlich die Hardwareanforderung, nicht eine separate Wertungsskala.

### Methodologie: Warum diese Tier-Grenzen?

Die Grenzen basieren auf dem **realen RAM-Bedarf bei Q4-Quantisierung** plus Betriebssystem-Overhead — nicht auf abstrakten Capability-Scores oder Marketingkategorien.

**Nano (≤ 4B / < 4 GB)**
Das ist die Grenze für Geräteklassen ohne dedizierten ML-Arbeitsspeicher. Auf Smartphones und Raspberry Pi sind 4 GB typischerweise das Maximum, das nach OS-Overhead noch für ein Modell übrig bleibt. Diese Modelle eignen sich für Autocomplete und Edge-Inferenz, nicht für komplexe Reasoning-Tasks.

**Edge (5–9B / 4–8 GB)**
Jeder aktuelle Consumer-Laptop mit mindestens 8 GB RAM kann ein 7B-Modell in Q4 flüssig betreiben (~4–5 GB). Das MacBook Air M-Series ist der Referenzpunkt: günstigste, am weitesten verbreitete Geräteklasse mit Unified Memory.

**Desktop (10–19B / 8–14 GB)**
Die obere RAM-Grenze liegt bewusst bei 14 GB statt 12 GB. Hintergrund: Q4-Quantisierung für 14B-Modelle benötigt realistisch 9–10 GB — auf einer 12-GB-GPU ist das machbar, aber auf einem Laptop (Unified Memory) fehlt danach Headroom für Betriebssystem und Anwendungen. 12 GB VRAM (diskret) ist eine andere Rechnung als 12 GB Unified Memory. Der Referenzpunkt „MacBook Pro mit 14 GB" ist deshalb treffender als eine GPU-Aussage.

**Workstation (20–35B / 14–24 GB)**
Der Tier beginnt bei 20B. Ein M4 Pro/Max mit 18 GB RAM ist eine **Betriebsgrenze**, keine Tier-Grenze — ein 20B-Modell gehört konzeptuell in Workstation, auch wenn es auf einem 18-GB-Gerät eng werden kann. Die Parametergrenze bei 35B reflektiert, dass 32B-Modelle (z. B. Qwen3:32b) auf einem RTX 4090 (24 GB) oder M4 Max (36–48 GB) noch lokal laufen.

**Server (36–75B / 24–48 GB)**
Hier beginnt die Klasse, die dedizierte Hardware voraussetzt: Mac Studio (64–192 GB Unified Memory) oder einen dedizierten GPU-Node mit ≥ 24 GB VRAM. Consumer-Hardware fällt aus. Die Grenze bei 75B ist hart, weil ein 70B-Modell in Q4 ~40–42 GB benötigt und damit auf einem Mac Studio mit 64 GB noch komfortabel läuft.

**Frontier (API-only / > 75B)**
Das primäre Kriterium ist **API-only**, nicht die Parameterzahl. Modelle wie Llama 3.1 405B laufen theoretisch lokal — auf Multi-GPU-Server-Rigs. Praktisch ist das keine Deployment-Option für Einzelpersonen oder kleine Teams. „API-only" kommuniziert die Realität direkter als eine Parameterschwelle. Frontier-Modelle (kommerzielle APIs, Cloud-Proxies) erhalten keinen Size-Tag und werden automatisch in diesen Tier eingestuft.

**Badge-Marker:** Nano-Modelle (≤ 4B) erhalten einen `🔬`-Suffix am Badge (z. B. `🥉 Bronze 🔬`) — als visuelles Signal für den Floor-Tier. Edge-Modelle und größer erscheinen ohne Suffix.

| Beispiel | Size Class | Erwarteter Badge-Bereich |
|---------|-----------|--------------------------|
| `qwen3:4b` | Nano | ⚖️ Standard 🔬 – 🥉 Bronze 🔬 |
| `qwen2.5:3b` | Nano | ⚖️ Standard 🔬 |
| `mistral:7b` | Edge | *(normales Badge)* |
| `cogito:14b` | Desktop | *(normales Badge)* |
| `ministral-3:14b` | Desktop | *(normales Badge)* |
| `llama3.3:70b` | Server | *(normales Badge)* |
| `claude-sonnet-4-6` | Frontier | *(normales Badge)* |
| `gemini-2.5-pro` | Frontier | *(normales Badge)* |

---

## Provider-Kategorien

CrucibleMark verwendet eine dynamische, zentrale Konfiguration (`benchmark_config.yaml`), um Provider und Kategorie-Zuordnungen als Single Source of Truth (SSOT) zu verwalten. Dies macht das System flexibel erweiterbar, ohne dass Hardcodings im Analyse-Code nötig sind.

Aktuell unterscheidet CrucibleMark drei wesentliche Arten von Modell-Kategorien:

| Kategorie | Beschreibung | Beispiele / Provider | Charakteristik |
|-----------|--------------|-----------|----------------|
| **Commercial** | Cloud-basierte kommerzielle APIs | Anthropic, Google, OpenAI, Mistral | Proprietäre Modelle. Direkte Kosten pro Token, API-Keys erforderlich |
| **Cloud (Open-Weights)** | Cloud-gehostete Open-Weights Modelle | Groq, Ollama (mit `:cloud`-Suffix) | Modelle, die über APIs (oder Proxies) laufen, aber offen (open-weights) sind. |
| **Local** | Vollständig lokal ausgeführte Modelle | Ollama (lokal) | Ausführung auf eigener Hardware. Keine Provider-Kosten, volle Privatsphäre |

### Erkennung & Erweiterung (SSOT: `benchmark_config.yaml`)

Die Kategorisierung wird zentral über `utils/model_utils.py::get_model_category()` gesteuert. Die Funktion liest die Einstellungen dynamisch aus der Datei `benchmark_config.yaml` aus:

1. **Prüfung über Provider-Konfiguration (`benchmark_config.yaml`):**
   Das System gleicht den in den Rohdaten hinterlegten Provider-Namen (`provider`) gegen die globalen Konfigurationsbäume (`providers.commercial`, `providers.open_weights_cloud`, `providers.local`) ab.
   - Provider unter `providers.commercial` definiert (z. B. `anthropic`) → **Commercial**
   - Provider unter `providers.open_weights_cloud` definiert (z. B. `groq`) → **Cloud (Open-Weights)**
   - Provider unter `providers.local` definiert (z. B. `ollama`) → Prüfung nach Regel 2.

2. **Zusatzprüfung für Suffixe / Altlasten (Legacy-Modus):**
   Wenn aus historischen Gründen ein Modell in der lokalen CSV liegt oder Provider und Suffix auf eine API hindeuten, wird abschließend das Suffix inspiziert:
   - Enthält der Name `:cloud` (z. B. `minimax-m2:cloud`) → **Cloud (Open-Weights)**
   - Sonstiges Modell (z. B. `ministral-3:14b`) → **Local**

#### Einen neuen Provider hinzufügen

Um einen neuen Model-Provider zu ergänzen (z. B. einen weiteren Open-Weights Hoster), genügen wenige Handgriffe, da das System vollkommen dynamisch geparst wird:

1. **Konfiguration anpassen:** Öffne `benchmark_config.yaml` (und synchronisiere es idealerweise auch im Template `benchmark_config.example.yaml`).
2. **Provider eintragen:** Ergänze den String-Namen des Providers (z.B. `together_ai` oder `vllm`) im passenden Kategorien-Array in der Sektion `providers`:

```yaml
providers:
  commercial:
    - anthropic
    - google
    - openai
    - mistral
  open_weights_cloud:
    - groq
    # - together_ai  <-- Hier neuen Hoster ergänzen
  local:
    - ollama
    # - vllm         <-- Hier neuen lokalen Runner ergänzen
```
3. Fertig! Ab dem nächsten Benchmark-, CLI- oder Leaderboard-Lauf überträgt sich die neue Provider-Einordnung fehlerfrei bis in die finalen Score-Tabellen und Metareviews des Judges.

---

## Speed-Klassen

Speed Classes kategorisieren Modelle nach ihrer **durchschnittlichen Inferenz-Zeit** über alle 37 Tests.

| Class | Symbol | Avg Time | Beschreibung | Use Case |
|-------|--------|----------|--------------|----------|
| **Fast** | ⚡ | < 30s | Instant-Gefühl, interaktive Nutzung | Autocomplete, Chat, Prototyping |
| **Medium** | ⏱️ | 30–60s | Spürbare Latenz, akzeptabel | Deep-Work Sessions, Batch Processing |
| **Slow** | 🐢 | > 60s | „Kaffeepause"-Modell | Hintergrund-Jobs, nächtliche Analysen |

**Beispiele:**

- **Fast:** Mistral Large (25,4s), Qwen 2.5-Coder:7b (17,9s)
- **Medium:** Cogito:14b (62,2s), Mistral-Nemo (60,0s)
- **Slow:** Ministral-3:14b (168s), Gemma3:12b (100,7s)

**Wichtig:** Speed ≠ Quality. Ministral-3:14b ist Slow, aber Rang 3 im Leaderboard.

---

## Skill-Profile

Skill Profiles beschreiben die **Stärken-Kombination** eines Modells basierend auf Performance-Clustering.

#### 1. Fast Specialist
- **Speed:** Fast (< 30s) | **Stärken:** Code Quality + Reasoning
- **Beispiel:** Mistral Large (83,6 Code, 67,7 Reasoning)

#### 2. Fast Content Adapter
- **Speed:** Fast (< 30s) | **Stärken:** Content Transformation + Cultural Intelligence
- **Beispiel:** Qwen 2.5-Coder:14b (77,1 Content, 63,0 Cultural)

#### 3. Fast Code Reviewer
- **Speed:** Fast (< 30s) | **Stärken:** Code Quality (> 85) + Documentation
- **Beispiel:** Mistral Medium (90,2 Code, 70,9 Docs)

#### 4. Balanced Specialist
- **Speed:** Medium | **Stärken:** gleichmäßig über alle Module
- **Beispiel:** Cogito:14b (82,4 Code, 70,1 Reasoning)

#### 5. Slow Specialist
- **Speed:** Slow (> 60s) | **Stärken:** einzelne Domäne (meist Reasoning oder Cultural)
- **Beispiel:** Ministral-3:8b (71,5 Reasoning, 86,0 Cultural)

#### 6. Slow Content Adapter
- **Speed:** Slow (> 60s) | **Stärken:** Content + Cultural Intelligence
- **Beispiel:** Ministral-3:14b (85,3 Content, 83,4 Cultural)

**Automatische Erkennung:** basiert auf Top-2-Kategorien und Speed Class.

---

## Tokens/s – Technische Generierungsgeschwindigkeit

```text
Tokens/s = Mittelwert der tokens_per_second über alle Nicht-System-Assets
```

> **Hinweis:** Der frühere „Efficiency Score" (Total Score ÷ Avg Task Duration) wurde in v3.4.3 entfernt.
> Er kombinierte Qualität und Speed opak in einer Zahl und war neben `Cost per 1K (USD)` redundant.
> Stattdessen drei saubere, unabhängige Dimensionen: `Total Score`, `Avg Task Duration (s)`, `Tokens/s`.

---

## Reasoning-Score-Interpretation

Der **Reasoning Score** ist der härteste Test in CrucibleMark.

| Score | Klassifizierung | Fähigkeiten | Beispiele |
|-------|-----------------|-------------|-----------|
| **35–40** | Elite | Tier 2 (Deep Reasoning) konstant > 70 %, Tier 3 (Metacognition) > 50 % | Mistral Medium (39,8) |
| **31–34** | Production-Ready | Tier 2 > 60 %, Tier 3 variabel | Ministral-3:14b (36,4), Cogito (35,0) |
| **26–30** | Entwicklung | Tier 2 > 50 %, Tier 3 schwach | Gemma2:9b (26,6), Mistral-Nemo (30,4) |
| **< 26** | Limitiert | Tier 2 inkonsistent, Tier 3 Fail | Dolphin-Llama3 (17,6) |

**Warum sind die Scores niedrig?** CrucibleMark misst **operatives Reasoning** (Deadlock-Detection, Root-Cause-Analyse), nicht Textvolumen. Selbst DeepSeek-R1 (Marketing: „Reasoning Model") erreicht nur **31,6** – das zeigt, dass Tier 2/3 wirklich schwer sind.

---

## Routine vs. Reasoning Score

| Metrik | Misst | Gewichtung | Beispiel-Tasks |
|--------|-------|------------|----------------|
| **Routine Score** | Alltags-Produktivität | Code (20 %), UX (15 %), Docs (20 %), Content (20 %), Cultural (25 %) | Code-Audits, Button-Labels, README-Qualität |
| **Reasoning Score** | Kognitive Tiefe | Tier 0 (10 %), Tier 2 (50 %), Tier 3 (40 %) | Deadlock-Erkennung, Paradox-Lösung, Selbstkorrektur |

Ministral-3:14b hat **41,3 Routine** (Rang 4) und **36,4 Reasoning** (Rang 1 lokal) – gut für Alltag und tiefes Denken.

---

## Workflow: Neue Modelle hinzufügen

### 1. Benchmark ausführen

```bash
python test.py --model neues-modell:14b --runs 1
```

### 2. Leaderboard generieren

```bash
make leaderboard
```

### 3. Automatische Klassifizierung prüfen

Das System vergibt automatisch Badge, Speed Class und Skill Profile.

### 4. Manuelle Review (optional)

Prüfen, ob Badge zur erwarteten Performance passt, Speed Class korrekt ist und Skill Profile Sinn macht.

---

## Performance-Ratio & Vergleich mit Golden Standards

**Performance-Ratio Formel:**

```text
Performance Ratio = (Local Model Score / Golden Standard Score) × 100
```

**Beispiel:**

```text
Ministral-3:14b: 77,6 Total Score
Mistral Large: 78,8 Total Score
→ Performance Ratio = (77,6 / 78,8) × 100 = 98,5 %
```

**Interpretation:**

- **≥ 95 %:** Cloud-Niveau erreicht
- **85–94 %:** Sehr nah, praxistauglich
- **75–84 %:** Gute Alternative, mit Einschränkungen
- **< 75 %:** Deutlicher Abstand

Ministral-3:14b erreicht **98,5 %** von Mistral Large – fast identisch.

---

## Qualitative Indikatoren (Meta-Analyse)

Neben numerischen Scores gibt es **binäre Ausschlusskriterien**, die oft nicht direkt im Score erscheinen, aber die Tauglichkeit für Automatisierungsprozesse massiv einschränken.

### Das „Struktur-Paradoxon" (Tabellen & Formate)

> **Design-Prinzip:** Tabellen sind kein Nice-to-have – sie sind ein harter Filter für Modell-Qualität.

Scheitert ein Modell daran, komplexe Markdown-Strukturen (wie Tabellen mit Pipes `|`) fehlerfrei zu generieren, zeigt das fundamentale Schwächen im Instruction Following. Ein Modell, das keine saubere Tabelle generieren kann, ist für professionelle Automatisierung (Reporting, Daten-Extraktion) ungeeignet.

---

## Reasoning-Erkennung: Card-First Workflow (ab v3.5.8)

CrucibleMark erkennt Reasoning-Modelle seit v3.5.8 **empirisch statt nur heuristisch**. Das Token-Budget-System und der LLM-Judge bauen darauf auf.

### ThinkingProbe

`probe_thinking_model(model_id, provider_key, config)` in `utils/model_utils.py` sendet einen deterministischen Reasoning-Prompt an die API und wertet zwei Signale aus:

| Signal | Erkennungsmerkmal | Konfidenz |
|--------|-------------------|-----------|
| A | `<think>` / `<thinking>` / `<thought>`-Tags im Response-Body | `high` |
| B | `reasoning_tokens > 0` in der API-Metadaten-Antwort | `medium` |

> **Wichtig:** Response-Länge ist kein zuverlässiges Signal (Instruction-Following-Modelle erzeugen auf Reasoning-Prompts ebenfalls lange Antworten). Signal C ist bewusst nicht implementiert.

Das Ergebnis wird als JSON-Felder in die Model-Card (`benchmark_scores/model_cards/*.json`) geschrieben:

```json
{
  "thinking_probe_detected": true,
  "thinking_probe_evidence": "Signal A: <think> tags detected in response body",
  "thinking_probe_confidence": "high",
  "thinking_probe_manual_override": false
}
```

**Sonderfall OpenAI o-Series:** o1, o3-mini, o4-mini verbergen Reasoning-Tokens intern vor der API. Für diese Modelle wird `thinking_probe_detected: true` manuell mit `thinking_probe_manual_override: true` gesetzt.

### `is_reasoning_model()` Lookup-Hierarchie

```
1. is_reasoning_model_from_card(model_id)
   └── Card vorhanden + thinking_probe_detected Feld → verwende Feld-Wert
   └── Card fehlt oder Feld fehlt → None (kein False-Positive)

2. String-Trigger-Heuristik (Fallback)
   └── deepseek-r1, reasoning, phi4, qwq, o1, o3,
       magistral, glm-5, minimax-m2, gemini-2.5, kimi-k2
```

Card-Lookup hat immer Vorrang. Bei Diskrepanz zwischen Card und Trigger-String gilt die Card.

### Card-First-Hook beim Benchmark-Run

`_ensure_model_card()` in `scripts/core/unified_runner.py` wird vor dem ersten Run eines Modells aufgerufen:

- Card mit `thinking_probe_detected` → sofort weiter (kein API-Call)
- Card ohne Feld → Probe ausführen → Feld eintragen
- Keine Card → Probe ausführen → Minimal-Card erstellen (`card_status: "minimal"`)
- Probe-Fehler → `RuntimeError` (Benchmark-Abbruch, kein stilles Überspringen)

### Retroaktiver Probe (CLI)

```bash
# Einzelnes Modell
make probe-thinking MODEL=gemini-2.5-flash

# Alle Cards ohne thinking_probe_detected
make probe-all-thinking

# Direktaufruf mit Provider-Override
.venv/bin/python scripts/tools/probe_thinking.py --model <model-id> --provider openrouter
```

`scripts/tools/probe_thinking.py` unterstützt zusätzlich `--missing` (Batch ohne bestehende Probes) und `--all` (Force-Rescan aller Cards).

---

## Best Practices

### DO's ✅

1. **Badge als Schnell-Indikator nutzen:** Silver = Production-ready
2. **Speed Class für Use-Case wählen:** Autocomplete = Fast, Deep-Work = Medium/Slow okay
3. **Skill Profile beachten:** Code-Reviewer oder Content-Adapter?

### DON'Ts ❌

1. **Nicht nur Badge anschauen:** Silver-Modelle haben unterschiedliche Stärken
2. **Nicht Speed ignorieren:** Ein 168-Sekunden-Modell ist unbrauchbar für Autocomplete
3. **Nicht nur Reasoning:** Ein Modell mit 40 Reasoning und 30 Routine ist unpraktisch
4. **Nicht Commercial blind vertrauen:** Mistral Large liegt nur 1,2 Punkte über Ministral-3:14b (lokal)

---

## Aktuelle Leaderboard-Highlights (Feb 2026)

### Top 5 Modelle

1. **Mistral Medium** (Commercial) → 81,3 Total, 39,8 Reasoning, Fast 🏆 Gold
2. **Mistral Large** (Commercial) → 78,8 Total, 35,6 Reasoning, Fast
3. **Ministral-3:14b** (Local) → 77,6 Total, 36,4 Reasoning, Slow ← **Bestes lokales Modell!**
4. **Ministral-3:8b** (Local) → 75,2 Total, 34,6 Reasoning, Slow
5. **Cogito:14b** (Local) → 72,5 Total, 35,0 Reasoning, Medium

### Key Insights

- **Gap Commercial → Local:** nur **3,7 Punkte** (Mistral Medium vs. Ministral-3:14b)
- **Bestes Reasoning (lokal):** Ministral-3:14b (36,4) übertrifft DeepSeek-R1 (31,6)
- **Schnellstes Production-Modell:** Qwen 2.5-Coder:7b (17,9s, Bronze)
- **Bester Allrounder:** Cogito:14b (Balanced Specialist, 62,2s)

---

## Verwandte Dokumentation

- **ARCHITECTURE.md** – Technische Details zu Modulen & Scoring
- **USER_GUIDE.md** – Tests ausführen und interpretieren
- **README.md** – Übersicht & Quick Start
- **SCORING_METHODOLOGY.md** – Kanonische Tier-Schwellenwerte

---

**Dokumenten-Version:** 2.1.0 (Überarbeitung März 2026)\
**Kompatibel mit:** CrucibleMark v3.4.3+
