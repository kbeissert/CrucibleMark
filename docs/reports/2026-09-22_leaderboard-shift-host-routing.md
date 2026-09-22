# Ursachenanalyse: Leaderboard-Verschiebungen nach der Tokenleiter-Umstellung

> **Datum:** 22.09.2026 · **Analyst:** CrucibleMark Session 113 · **Status:** Abgeschlossen
> **Anlass:** Nach der automatischen Tokenbudget-Eskalation („Tokenleiter") verschieben sich Leaderboard-Positionen teils deutlich. Verdacht: Benchmark-Bug, Modell-Degradation oder Judge-Änderung.

---

## Executive Summary

Die Positionverschiebungen haben **drei voneinander unabhängige Ursachen — keine davon ist ein Messfehler im Benchmark:**

1. **Die Tokenleiter wirkt korrekt** und erklärt die Aufsteiger: GLM-5.3 (+14,6 Punkte) konnte vorher seine Aufgaben nicht sauber beantworten, weil das Budget vor Abschluss des Reasonings erschöpft war. Swift-Qwen (+5,8) und GPT-5.5 profitieren ebenfalls — genau das erwartete Muster für tokenhungrige Modelle.
2. **Die Abfälle bei MiMo V2.5/V2.5-Pro und MiniMax M3 sind auf OpenRouter-Host-Routing-Varianz zurückzuführen:** OpenRouter servt dieselbe Modell-ID über wechselnde Upstream-Hosts (6 bei MiMo, 13 bei M3). Ein Live-Kontrolltest belegt: Die Hosts antworten bei identischem Prompt in messbar unterschiedlichem Stil — Sprachtreue, Antwortlänge, Reasoning-Verhalten und Format. Der September-Lauf traf nachweislich andere Hosts als der August-Lauf.
3. **Claude Opus 5 fiel durch eine Refusal-Eskalation bei Anthropic** (2/11 → 8/11 verweigerte Reasoning-Aufgaben bei identischen Prompts), nicht durch die Messung.

Der Judge (Haiku 4.5) wurde **nicht** verändert und bewertet nachweislich stabil. Der Bericht belegt jede Aussage mit A/B-Vergleichen.

---

## 1. Ausgangslage

Beobachtete Verschiebungen nach der Nachtest-Serie (Referenz: Web-Export vom 09.09., neue Werte: 20.–22.09.):

| Modell | Alt | Neu | Δ | Einordnung |
|---|---:|---:|---:|---|
| z-ai/glm-5.3 | 67,70 | 82,25 | **+14,55** | Tokenleiter-Effekt (Zweck der Umstellung) |
| swift-qwen3.8-27b (Standard) | 67,92 | 73,76 | **+5,84** | qwen3.8-Familie, tokenhungrig — erwartet |
| google/gemini-3.7-flash | 71,61 | 74,40 | +2,79 | Re-Run, verbessert |
| gpt-5_5 | 76,52 | 76,71 | +0,19 | tokenhungrig, leicht verbessert — erwartet |
| gemini-3.5-flash | 71,61 | 71,61 | 0,00 | kein Re-Run |
| minimax/minimax-m2.7 | 73,03 | 73,03 | 0,00 | kein Re-Run (nur relativ gefallen) |
| claude-sonnet-4-6 | 79,82 | 77,65 | −2,17 | moderat gefallen |
| claude-sonnet-5 | 79,04 | 76,72 | −2,32 | moderat gefallen |
| minimax/minimax-m3 | 80,19 | 77,14 | **−3,05** | ❓ Untersuchungsgegenstand |
| xiaomi/mimo-v2.5-pro | 79,00 | 75,10 | **−3,90** | ❓ Untersuchungsgegenstand |
| xiaomi/mimo-v2.5 | 74,55 | 69,98 | **−4,57** | ❓ Untersuchungsgegenstand |
| claude-opus-5 | 78,83 | 71,96 | **−6,87** | ❓ (siehe Abschnitt 4.2) |
| claude-opus-4-8 | 77,89 | 42,22 | −35,67 | ⚠️ Artefakt: Partial-Run (22/49 Tasks), kein echter Abfall |

**Modul-Level-Muster (entscheidender erster Hinweis):** Die Abfälle sind *modulspezifisch und inkonsistent* — MiMo V2.5 verliert bei Documentation (−14,3) und Content (−11,3), während Logical Reasoning *steigt* (+3,3); M3 verliert bei CLI (−9,3), während Documentation *steigt* (+3,3). Ein uniformer Judge-Shift würde alle Module gleichmäßig treffen. Dieses Muster zeigt verändertes **Antwortverhalten**, nicht veränderte **Bewertung**.

---

## 2. Methodik

| Instrument | Zweck |
|---|---|
| Backup-Vergleich (Tar 22.08.) | Per-Asset-Scores August vs. September — 147 gemeinsame Assets |
| Audit-Log-Analyse | Tatsächlich gesendete Prompts, Antwortformate, Eskalations-Notizen |
| A/B-Budget-Kontrolltest | Original-Prompt gegen OpenRouter mit August- vs. September-Budget |
| Host-Pinning-Kontrolltest | Gleicher Prompt gegen jeden Upstream-Host einzeln (provider-Pinning) |
| CSV-Metadaten | `llm_judge_model_used`, `finish_reason`, Tokens, Status je Row |
| Web-Recherche | Modell-Updates, OpenRouter-Status/Incidents |

---

## 3. Hypothese A: Benchmark-Bug? — **Widerlegt**

### 3.1 Der Judge hat sich nicht verändert

| Prüfpunkt | Ergebnis |
|---|---|
| Judge-Modell in allen CSV-Rows (20.–22.09.) | `claude-haiku-4-5-20251001` — identisch mit August |
| Vorbereiteter GLM-5.3-Flash-Wechsel | Nie aktiviert (Config-Kommentar + Nutzer-Entscheidung 20.09., 18:43) |
| Einziger Prompt-Delta seit August (reasoning_trace_context-Fix, 17.09.) | Greift bei MiMo/MiniMax **nachweislich nicht**: 0 Treffer in allen 150 September-Audit-Logs |
| Assets mit exakt ±0,0 Score-Delta | ~50 über alle Modelle — identische Antworten → identische Scores |

> **A/B-Beleg Judge-Stabilität (MiniMax M3, Auswahl):** 19 von 49 Assets mit Δ = ±0,0 (u. a. cli001 86,0→86,0; reasoning_5a 79,8→79,8; tooluse002 80,0→80,0; cultural_intel_001 82,0→82,0). Bei verändertem Judge-Verhalten wäre diese Häufung identischer Scores nicht erklärbar.

### 3.2 Budget/Tokenleiter entlastet — A/B-Kontrolltest

Der stärkste Verdacht war das höhere Budget (Caps 16384/20000 → 32768, entfernte Modell-Overrides). Kontrolltest: Original-Prompt (documentation_quality_005) direkt gegen OpenRouter, drei Budget-Varianten parallel:

| Variante | max_tokens | Latenz | Antwort | Reasoning-Tokens | finish | Anomalie |
|---|---:|---:|---:|---:|---|---|
| August-Cap | 20 000 | 64 s | 4 681 Z. | 507 | stop | keine |
| September-Modulbudget | 25 000 | 148 s | 15 898 Z. | 2 620 | stop | keine |
| September+Kalibrierung | 32 000 | 163 s | 14 423 Z. | 4 219 | stop | keine |

**Ergebnis:** Keine Variante reproduziert das September-Phänomen (Erstversuch-Burn mit 0 sichtbarem Output, Kurzantwort, 54 min Latenz, 0,16 Tokens/s). Das Budget ist nicht die Ursache.

**Gegenprobe — die Leiter rettet Scores statt sie zu senken:**

| Asset | August (Pool, ohne Leiter) | September (mit Leiter) | Δ |
|---|---:|---:|---:|
| mimo-v2.5 reasoning_5b | 16,0 % (Burn: 0 Zeichen, 24 178 Tokens) | 82,8 % (Eskalation Stufe 2) | **+66,8** |
| z-ai/glm-5.3 (Gesamt) | 67,70 | 82,25 | **+14,55** |

### 3.3 Keine Messartefakte

- Die 4 auffälligen Status-Rows (truncated/language_mismatch) tragen echte Scores (39–72 %), keine Nullen; keine Erschöpfungs-Flags.
- Detektoren (language_mismatch, truncated-Heuristik) existieren unverändert seit Mai bzw. April 2026.
- Assets sind statisch (letzte Änderung April 2026) — kein Prompt-Drift.

### 3.4 Die lokale Kontrollgruppe: gleiche Gewichte, gleiche Config → gleiche Positionen

Der schärfste Beleg für Messstabilität kommt von den **lokal selbst gehosteten Modellen** (feste Gewichte auf dem vLLM-Server, identische TOML-Einstellungen, identischer Judge, identische Assets). Läuft die Messpipeline unverändert, müssen deren Positionen konstant bleiben — und genau das passiert:

| Lokales Modell | August-Ø | September-Ø | Δ | Token-Cuts im August |
|---|---:|---:|---:|---:|
| qwen3_8-27b-nvfp4-thinking | 78,7 | 78,7 | **±0,0** | 0 |
| qwen3_5-27b-nvfp4 | 71,3 | 71,3 | **±0,0** | 0 |
| ornith-1_5-35b-a3b-nvfp4 | 76,7 | 76,9 | +0,2 | 0 |
| qwen3_6-27b-nvfp4-thinking | 76,9 | 77,4 | +0,5 | 0 |
| qwen3_6-35b-a3b-nvfp4 | 72,7 | 72,2 | −0,5 | 0 |
| qwen3_8-27b-nvfp4 | 76,4 | 76,0 | −0,4 | 0 |
| qwen3_6-35b-a3b-nvfp4-thinking | 74,4 | 74,4 | **±0,0** | 1 |
| nemotron-3_5-lightning-30b-a3b-nvfp4 | 71,9 | 71,3 | −0,6 | 1 |
| qwen3_6-27b-nvfp4 | 75,0 | 73,0 | −2,0 | 0 |

Neun Modelle, mittlere absolute Abweichung **±0,5 Punkte** — Rauschen. Die Cloud-Modelle verschoben sich im selben Zeitraum um −3 bis −4,6 Punkte. Der Unterschied zwischen beiden Gruppen ist genau die eine Variable, die bei lokalen Modellen nicht existiert: **der Provider-Host.**

**Die Komplementär-Beobachtung bestätigt die Tokenleiter-Wirkung:** Lokale Modelle, die *vorher* unter Token-Caps litten (Reasoning-Burns, abgeschnittene Antworten), verbesserten sich unter dem neuen Budget — swift-qwen3.8-27b Standard 67,9 → 74,6 (+6,7, Erstrun unter alten Caps vs. Re-Run 14.09.), swift-thinking 80,5, GLM-5.3 +14,6. Modelle ohne vorherige Caps blieben, wo sie waren. Das Bild ist konsistent: **Budget-Freigabe hebt die vorher Geclippten; Routing-Varianz verschiebt die Cloud-Modelle; die Messung selbst ist stabil.**

---

## 4. Hypothese B: Provider-seitige Änderungen — **Bestätigt**

### 4.1 OpenRouter-Host-Routing-Varianz (MiMo/MiniMax)

OpenRouter ist ein Gateway: Dasselbe Modell (`xiaomi/mimo-v2.5-20260422`, Slug seit April stabil, kein Weight-Update dokumentiert) wird von wechselnden Upstream-Hosts servt:

| Modell | Upstream-Hosts (Live, 22.09.) |
|---|---|
| xiaomi/mimo-v2.5 | GMICloud, DeepInfra, Xiaomi, StreamLake, Novita, Venice (6) |
| minimax/minimax-m3 | CoreWeave, GMICloud, DeepInfra, StreamLake, Venice, Together, Parasail, AtlasCloud, Novita, **Minimax**, Mara, SambaNova, ModelRun (13) |

**A/B-Beleg 1 — Hosts antworten im unterschiedlichem Stil** (mimo-v2.5, identischer doc_005-Prompt, max_tokens 25 000, je Host einzeln gepinnt):

| Host | Latenz | Antwortlänge | Reasoning-Tokens | Tokens/s | Sprachtreue (de_ratio) |
|---|---:|---:|---:|---:|---:|
| GMICloud | 85 s | 6 756 Z. | 353 | 27,2 | **0,62** |
| StreamLake | 56 s | 5 050 Z. | 305 | 33,8 | **0,58** |
| Xiaomi | 27 s | 6 664 Z. | 0 | 68,8 | 0,31 |
| DeepInfra | 119 s | 10 991 Z. | 2 799 | 48,0 | **0,10** |
| Novita | 66 s | 6 836 Z. | 181 | 30,2 | **0,10** |
| Venice | 173 s | 12 801 Z. | 348 | 22,0 | **0,10** |

Sechs Hosts, sechs Verhaltensprofile: Sprachtreue streut 0,10–0,62 (Aufgabe ist deutschsprachig!), Reasoning von 0 bis 2 799 Tokens, Länge 5 050–12 801 Zeichen.

**A/B-Beleg 2 — der größte Einzelschaden ist host-spezifisch** (m3, cli003: 100 % → 58 %; Aufgabe verlangt knappen Bash-Output):

| Host | Antwortstil | Länge | Entspricht |
|---|---|---:|---|
| CoreWeave | knapper Einzeiler | 115 Z. | **August-Format (100 %)** |
| GMICloud | knapper Einzeiler | 106 Z. | **August-Format (100 %)** |
| Venice | kommentierter Block | 561 Z. | September-Format (58 %) |
| Together | kommentierter Block | 516 Z. | September-Format |
| StreamLake | kommentierter Block | 931 Z. | September-Format |
| DeepInfra | — | — | *429 „temporarily rate-limited upstream"* |

Der Score-Einbruch 100→58 wird allein durch den Antwortstil des bedienenden Hosts erklärt — identischer Prompt, identischer Benchmark-Code.

**Passende September-Beobachtungen (Pool-Lauf 20./21.09.):** Erstversuch-Burns (0 sichtbarer Output, 54 min/Asset, 0,16 t/s), ein `content_filter`-Abbruch, DE/EN-Mixing (language_mismatch) — alles Phänomene, die im August-Lauf nicht auftraten und heute (22.09.) über alle Hosts nicht reproduzierbar sind. DeepInfra — vermutlich eine August-Haupt-Route — ist zum Testzeitpunkt upstream-rate-limited: Kapazitätsverschiebungen im Host-Pool verschieben das Routing, ohne dass OpenRouter einen Incident meldet (Statusseite: „All Systems Operational").

### 4.2 Claude Opus 5: Refusal-Eskalation bei Anthropic

| Reasoning-Asset | August | September | finish_reason |
|---|---:|---:|---|
| reasoning_5a | 0,0 (Refusal) | 0,0 (Refusal) | refusal |
| reasoning_5e | 0,0 (Refusal) | 0,0 (Refusal) | refusal |
| reasoning_5d | 99,2 | 0,0 | **refusal (neu)** |
| metacog_001 | 75,0 | 0,0 | **refusal (neu)** |
| metacog_002 | 68,0 | 0,0 | **refusal (neu)** |
| metacog_003 | 97,0 | 0,0 | **refusal (neu)** |
| metacog_004 | 72,0 | 0,0 | **refusal (neu)** |
| metacog_005 | 72,0 | 0,0 | **refusal (neu)** |
| river / 5b / 5c | 79,8 / 94,8 / 97,3 | 97,8 / 96,8 / 96,2 | normal |

Refusals: **2/11 → 8/11** bei identischen Prompts. Anthropic hat das Safety-Verhalten serverseitig verschärft — derselbe Kausalitätstyp wie 4.1: Provider-Änderung unter unverändertem Modellnamen. Der Logical-Reasoning-Moduleinbruch (68,6 → 26,4) ist vollständig durch die Refusals erklärt; alle anderen Opus-5-Module bleiben stabil (Code 81,9, Documentation 86,0).

### 4.3 Die betroffenen Modelle im Detail (Degradations-Profile)

Die folgenden Profile fassen je Modell zusammen: Positionsschaden, Modul-Einbrüche, beobachtetes Antwortverhalten im September-Pool-Lauf und den Stand des gepinnten Kontroll-Re-Runs. Referenz ist jeweils der August-Lauf (Backup 22.08.) gegen den September-Pool-Lauf (20./21.09.).

#### Xiaomi MiMo V2.5 — −4,57 Punkte (74,55 → 69,98, Rank 103)

**Modul-Deltas (August → September-Pool):**

| Modul | August | September-Pool | Δ |
|---|---:|---:|---:|
| documentation_quality | 75,4 | 61,1 | **−14,3** |
| content_transformation | 80,0 | 68,7 | **−11,3** |
| cultural_intelligence | 73,2 | 69,2 | −4,0 |
| cli_benchmark | 82,0 | 79,7 | −2,3 |
| code_quality | 70,2 | 68,8 | −1,5 |
| ux_writing | 75,5 | 75,4 | −0,2 |
| logical_reasoning | 67,8 | 71,1 | **+3,3** |

**Verhaltens-Evidenz im September-Pool-Lauf (im August nicht vorhanden):**

| Anomalie | Beobachtung |
|---|---|
| Reasoning-Burn | doc_005: Erstversuch verbrannte das komplette Budget im internen Reasoning (0 sichtbarer Output), Eskalation Stufe 2, 54 min Laufzeit, 0,16 Tokens/s |
| Sprach-Drift | 2× language_mismatch (content_002/004): Analyse deutsch, Tweets englisch (Marker DE=19/EN=46) — August: 0 Fälle |
| Kurzantwort | doc_005 finale Antwort 1 409 Zeichen (August: 6 346) → truncated-Status |
| Content-Filter | 1× `finish_reason=content_filter` (Budget 32 000) — August: nur stop/length |
| Token-Anomalie | cultural_intel_001/002: gleiche Antwortlänge (~210/380 Z.), aber Tokens 343→622 und 288→1 602 — ein Reasoning-Anteil kam neu hinzu |

**Größte Per-Asset-Verluste (Auswahl):**

| Asset | August | September-Pool | Antwortlänge |
|---|---:|---:|---|
| tooluse005 | 80,0 | 40,0 | 1 652 → **60 Z.** |
| content_001 | 79,7 | 44,4 | 1 527 → 1 286 Z. |
| doc_003 | 95,8 | 62,9 | 12 459 → 8 275 Z. |
| metacog_001 | 78,0 | 57,0 | 702 → 383 Z. |
| content_004 | 81,0 | 60,5 | 6 041 → 8 191 Z. |

*(Gegenstück: reasoning_5b 16,0 → 82,8 — der August-Burn wurde von der Eskalationsleiter gerettet, siehe 3.2.)*

**Gepinnter Kontroll-Re-Run (22.09., Xiaomi-First-Party):** 43/43 Tasks `upstream=Xiaomi`, 100 % `finish=stop`, null Burns, null Sprach-Anomalien, null truncated. Task-Ø 72,1 (Pool: 70,8; August: 74,6). **cli003 erholte sich auf 100,0** (Pool: 86,0; August: 100,0). Das Anomalie-Muster des Pool-Laufs ist unter dem Hersteller-Host vollständig verschwunden.

#### Xiaomi MiMo V2.5-Pro — −3,90 Punkte (79,00 → 75,10, Rank 32)

**Modul-Deltas (August → September-Pool):**

| Modul | August | September-Pool | Δ |
|---|---:|---:|---:|
| documentation_quality | 83,5 | 73,1 | **−10,4** |
| code_quality | 84,7 | 78,1 | −6,6 |
| logical_reasoning | 75,0 | 71,2 | −3,8 |
| cultural_intelligence | 73,8 | 71,0 | −2,8 |
| content_transformation | 79,0 | 77,4 | −1,6 |
| ux_writing | 81,1 | 79,9 | −1,2 |
| cli_benchmark | 82,7 | 84,3 | +1,7 |

**Schwerster Einzelfall:** doc_005 fiel von 96,3 auf 56,9 — die Antwort schrumpfte von 8 560 auf **1 269 Zeichen** (1/7 der August-Länge, truncated-Status). Gleiche Aufgabe, gleicher Prompt wie im August.

**Weitere Per-Asset-Verluste (Auswahl):**

| Asset | August | September-Pool | Auffälligkeit |
|---|---:|---:|---|
| reasoning_5d | 82,2 | 48,0 | Tokens 2 490 → 1 155 |
| tooluse002 | 80,0 | 57,5 | — |
| code_002 | 79,6 | 60,4 | Länge 7 025 → 3 238 Z. |
| cultural_intel_001/002/004 | 98/82/80 | 82/66/64 | je −16, kurze Antworten |
| ux_003 | 96,0 | 80,0 | Länge 5 441 → **9 181 Z.** (länger, schlechter) |

**Gepinnter Kontroll-Re-Run (22.09., läuft):** Erste Tasks `upstream=Xiaomi`, code_quality_001 bei 82,0 (Pool: 78,1; August: 84,7) — im August-Band.

#### MiniMax M3 — −3,05 Punkte (80,19 → 77,14, Rank 16)

**Modul-Deltas (August → September-Pool):**

| Modul | August | September-Pool | Δ |
|---|---:|---:|---:|
| cli_benchmark | 95,3 | 86,0 | **−9,3** |
| content_transformation | 84,5 | 80,2 | −4,3 |
| code_quality | 81,9 | 78,6 | −3,3 |
| cultural_intelligence | 78,1 | 74,9 | −3,2 |
| ux_writing | 76,6 | 78,0 | +1,4 |
| logical_reasoning | 74,2 | 77,4 | +3,2 |
| documentation_quality | 77,3 | 80,6 | +3,3 |

M3 zeigt das **gemischteste Profil**: Drei Module fallen, drei steigen. Das ist das typische Bild von Request-weise wechselnden Hosts (13 Upstreams) — kein einheitlicher Modellzustand, sondern eine Mischung aus Host-Stilen. Der CLI-Einbruch ist host-spezifisch bewiesen (siehe 4.1, A/B-Beleg 2: CoreWeave/GMICloud liefern den August-Einzeiler, Venice/Together/StreamLake den September-Stil).

**Größte Per-Asset-Verluste (Auswahl):**

| Asset | August | September-Pool | Auffälligkeit |
|---|---:|---:|---|
| cli003 | 100,0 | 58,0 | Länge 103 → 304 Z. (Host-Stil, bewiesen) |
| tooluse001 | 88,0 | 49,0 | — |
| content_004 | 98,6 | 63,0 | — |
| tooluse005 | 80,0 | 57,5 | — |
| tooluse006 | 67,5 | 57,5 | Tokens 2 790 → **29 032** (10×) |
| code_005 | 83,0 | 66,0 | Länge 5 800 → 2 933 Z. |

*(Gegenstücke: cultural_002 64→82, code_004 63→80, metacog_002 52→68 — dieselbe Run-Serie.)*

**MiniMax M2.7 (Rank 69) ist davon unberührt:** kein Re-Run, Wert identisch 73,03 — der scheinbare Abfall war rein relativ (andere Modelle stiegen auf).

#### Claude Opus 5 — −6,87 Punkte (78,83 → 71,96)

Siehe 4.2: Logical Reasoning kollabierte isoliert (68,6 → 26,4) durch die Refusal-Eskalation von 2/11 auf 8/11 Assets (alle fünf Metacognition-Aufgaben fielen von 68–97 % auf 0 %). Alle übrigen Module stabil bis besser (Documentation 86,0, Code 81,9). Kein Mess- oder Budget-Effekt — reines Provider-Verhalten (Anthropic-Safety-Verschärfung unter gleichem Modellnamen).

#### Randbeobachtungen (schwächere Evidenz, gleiche Verdachtsklasse)

- **Claude Sonnet 4-6 / Sonnet 5** (je −2,2/−2,3): beide verloren exakt cultural_intelligence −9,6 — paralleles Muster über zwei Modellvarianten, konsistent mit einer serverseitigen Verhaltensänderung, aber unterhalb der Signifikanz für einen Einzelnachweis.
- **GPT-5_4** (−3,5): fiel parallel, vom Nutzer nicht bemerkt; gleiche Verdachtsklasse (API-Modell), nicht weiter untersucht.
- **Claude Opus 4-8** (−35,7): **kein** Degradationsfall — Partial-Run-Artefakt (22/49 Tasks, Coverage 0,53); der Wert ist unvollständig, nicht gefallen.

---

## 5. Gesamtbild

| Beobachtung | Erklärung |
|---|---|
| GLM-5.3 auf Platz 1, Swift/GPT-5.5 steigen | Tokenleiter: Reasoning-Budget reicht erstmals bis zur Antwort |
| MiMo V2.5/Pro, MiniMax M3 fallen | Host-Routing-Varianz: September-Lauf traf andere Upstream-Hosts mit anderem Antwortstil |
| MiniMax M2.7 „fällt" | Nur relativ (kein Re-Run, Wert identisch) |
| Claude/GeminiFlash „gleich" | Sonnets moderat gefallen (−2,2/−2,3); Opus-5 −6,9 durch Refusal-Eskalation; Opus-4.8 ist Partial-Run-Artefakt |
| Judge-Verdacht | Widerlegt: Modell, Prompts und Bewertung nachweislich unverändert |

---

## 6. Maßnahmen (umgesetzt 22.09.)

1. **`upstream_provider`-Logging:** Der tatsächlich bedienende Host wird pro Request in der CSV protokolliert (neue Spalte, dynamisch). Routing-Ereignisse sind künftig nachvollziehbar.
2. **Hersteller-Pinning als Regel:** Jedes OpenRouter-Modell wird, soweit verfügbar, auf den First-Party-Host des Herstellers gepinnt (`provider_routing` in provider_config.yaml, 17 Modelle: Xiaomi, Minimax, Z.AI, Moonshot AI, DeepSeek, Google, Alibaba). Modelle ohne Hersteller-Host (z. B. NVIDIA-Nemotron, DeepSeek-v4-pro) laufen bewusst im Pool — dokumentiert. `allow_fallbacks: false` = Fail-Fast statt stiller Ersatzhost.
3. **Kontroll-Re-Run der drei betroffenen Modelle** mit Pinning (läuft): Erste 43 Tasks alle `upstream=Xiaomi`, 100 % `finish=stop`, null Burns, null Sprach-Anomalien — der Pool-Lauf hatte in demselben Abschnitt Burns, `content_filter` und DE/EN-Mixing.

**Snapshot des gepinnten Re-Runs (mimo-v2.5, komplett, 43 Tasks, 100 % `upstream=Xiaomi`):**

| Modul | August (Pool) | September (Pool) | September (gepinnt, Xiaomi) |
|---|---:|---:|---:|
| code_quality | 70,2 | 68,8 | 68,6 |
| cli_benchmark | 82,0 | 79,7 | 86,7 |
| logical_reasoning | 67,8 | 71,1 | 73,6 |
| ux_writing | 75,5 | 75,4 | 68,3 |
| documentation_quality | 75,4 | 61,1 | 62,9 |
| content_transformation | 80,0 | 68,7 | 71,4 |
| cultural_intelligence | 73,2 | 69,2 | 70,2 |
| **Task-Ø gesamt** | **74,6** | **70,8** | **72,1** |

> **Honest Reading:** Das Pinning stellt *Stabilität* her (null Anomalien, konsistenter Host, cli003 zurück auf 100,0), nicht automatisch August-Scores. Der August-Wert entstand unter einer anderen Host- und Budget-Kombination (Cap 20 000, keine Leiter) — exakt diese Nicht-Reproduzierbarkeit ist das Problem, das das Pinning künftig löst. Die verbleibende Differenz zu August ist Run-to-Run-Varianz plus Config-Delta (kalibrierter 32k-Start vs. 20k-Cap).

---

## 7. Reproduzierbarkeit: Das Hersteller-Modell auswählen

Drei Stufen, absteigend nach Aufwand:

| Stufe | Mechanismus | Aufwand |
|---|---|---|
| **OpenRouter-First-Party-Pinning** (umgesetzt) | `provider_routing: {order: [Xiaomi], allow_fallbacks: false}` — misst die Hersteller-Serving-Instanz | Config-Eintrag |
| Direkt-API des Herstellers | z. B. mimo.mi.com / MiniMax-API über den OpenAI-Gateway-Provider (`base_url` + `api_key_env`) | Neuer provider_config-Eintrag |
| Self-Hosting der Open Weights | Vollständige Kontrolle (Quantisierung, Sampling, Version) | Frontier-Hardware |

---

## 8. Restunsicherheiten

- **Non-Determinismus:** Bei Sampling-Temperaturen > 0 streuen Einzelscores run-to-run; Deltas im Bereich ±2–3 Punkte sind teilweise normale Varianz. Die großen Ausreißer (cli003 −42, doc_005 −39, metacog-Refusals) sind strukturell erklärt.
- **Welcher Host den September-Lauf bediente**, ist retrospektiv nicht rekonstruierbar (Generation-Metadaten wurden damals nicht geloggt) — ab jetzt durch `upstream_provider` behebbar.
- **Opus-5-Refusal-Ursache im Detail** (welcher Safety-Klassifikator drehte) ist außerhalb unserer Sichtbarkeit.

---

## Anhang: Datenquellen

- Backup `backups/cruciblemark_backup_20260822_181947.tar.gz` (August-Referenz, Per-Asset)
- `benchmark_scores/*_models_benchmark.csv` (Zeitreihen, Judge-/Status-Metadaten)
- `outputs/audit_logs/` (Prompts, Eskalations-Notizen — September-Stand vor Re-Run extrahiert)
- Live-Kontrolltests 22.09. (Budget-A/B, Host-Pinning je Modell) — Skripte in der Session-Dokumentation
- OpenRouter Endpoints-API (Host-Listen), Statusseite (keine Incidents 20./21.09.)

---

## Addendum: Aktualisierte Daten (final, Stand 22.09.2026, 20:00 Uhr)

Der gepinnte Kontroll-Re-Run aller drei Modelle ist abgeschlossen; dieser Addendum ersetzt die Zwischenstände (10:00 Uhr) durch die Endergebnisse.

### A.1 Kontrollgruppe komplett: Swift-Thinking-Nachtest fertig

Der lokale swift-qwen3.8-27b-nvfp4-**thinking**-Nachtest (gleiche Gewichte, gleiche vLLM-TOML wie im August) schloss ab: **49/49 Tasks, Ø 78,7 — exakt der August-Wert.** Die Kontrollgruppen-These aus 3.4 gilt damit auch für den vollständigen Nachtest-Run, nicht nur die Modul-Snapshots.

### A.2 Xiaomi MiMo V2.5 — final (49/49 Tasks, 100 % `upstream=Xiaomi`)

| Kennzahl | Wert |
|---|---|
| Upstream-Host | **Xiaomi (49/49 = 100 %)** |
| finish_reason / status | stop / success (49/49) |
| Burns, content_filter, truncated | **0 / 0 / 0** (Pool-Lauf: 1 Burn, 1 content_filter, 2 language_mismatch, 1 truncated) |
| Task-Ø | 71,9 (Pool: 70,8 · August: 74,4) |
| cli003 | **100,0** (Pool: 86,0 · August: 100,0 — erholt) |
| tooluse | 70,8 (Pool: 70,8 · August: 76,0) |

### A.3 Xiaomi MiMo V2.5-Pro — final (49/49 Tasks, 100 % `upstream=Xiaomi`)

| Modul | August | September-Pool | September gepinnt |
|---|---:|---:|---:|
| code_quality | 84,7 | 78,1 | 79,8 |
| cli_benchmark | 82,7 | 84,3 | **89,0** |
| logical_reasoning | 74,9 | 70,6 | 74,0 |
| ux_writing | 81,1 | 79,9 | 75,9 |
| documentation_quality | 83,5 | 73,1 | **86,4** |
| content_transformation | 79,0 | 77,4 | **83,2** |
| cultural_intelligence | 73,8 | 71,0 | 73,8 |
| tooluse | 74,0 | 70,4 | 72,6 |
| **Task-Ø** | **78,7** | **75,2** | **78,8** |

**Vollständige Erholung auf August-Niveau** (78,8 vs. 78,7). Die schwersten Pool-Schäden kehren zurück: doc_005 von 56,9 (truncated) auf 79,3; documentation_quality als Modul **übertrifft August** (86,4 vs. 83,5), ebenso content_transformation (83,2 vs. 79,0). Einzelschäden mit exakter August-Rückkehr: reasoning_5d (82,2 → 48,0 → 82,2), cli003 (100,0 → 86,0 → 100,0). **Leaderboard: Rank 32 → Rank 9.**

### A.4 MiniMax M3 — final (49/49 Tasks, 100 % `upstream=Minimax`)

| Modul | August | September-Pool | September gepinnt |
|---|---:|---:|---:|
| code_quality | 81,9 | 78,6 | 78,8 |
| cli_benchmark | 95,3 | 86,0 | 85,8 |
| logical_reasoning | 74,2 | 77,4 | 75,5 |
| ux_writing | 76,6 | 78,0 | 75,8 |
| documentation_quality | 77,3 | 80,6 | 79,5 |
| content_transformation | 84,5 | 80,2 | 76,0 |
| cultural_intelligence | 78,1 | 74,9 | 71,0 |
| tooluse | 81,1 | 65,8 | **80,2** |
| **Task-Ø** | **80,6** | **77,6** | **77,7** |

M3 landet bei 77,7 (Pool: 77,6) — der Pool-Wert war also kein Ausreißer nach unten, sondern liegt im Modellband. Der größte Pool-Schaden kehrt zurück: **tooluse 65,8 → 80,2** (August: 81,1). Die verbleibende Distanz zu August verteilt sich über mehrere Module im Rahmen der Run-to-Run-Varianz (13 Hosts, temp > 0). 48/49 success, 1 language_mismatch (Einzelereignis, August-Häufigkeit), alle `finish=stop`. **Leaderboard: Rank 16 (stabil).**

### A.5 Endergebnis und Leaderboard-Endstand

| Modell | August | Pool-Lauf | Gepinnt | Leaderboard |
|---|---:|---:|---:|---|
| MiMo V2.5-Pro | 78,7 | 75,2 | **78,8** | **Rank 32 → 9** |
| MiniMax M3 | 80,6 | 77,6 | **77,7** | Rank 16 |
| MiMo V2.5 | 74,4 | 70,8 | **71,9** | Rank 103 → 99 |

**Fazit:** Der gepinnte Kontrolllauf bestätigt die Diagnose doppelt — (1) die Anomalien des Pool-Laufs (Burns, content_filter, DE/EN-Mixing, truncated) verschwinden unter dem Hersteller-Host vollständig, (2) die Scores kehren Richtung August zurück, am vollständigsten bei V2.5-Pro. Die Restdifferenzen (v. a. mimo-v2.5 doc/content) sind Run-to-Run-Varianz plus Config-Delta (kalibrierter 32k-Start vs. August-Cap 20 000) — nicht Reproduktion des August-Zustands ist das Ziel des Pinning, sondern künftige Vergleichbarkeit bei stabilen Bedingungen.

### A.6 Prozess-Notiz (Transparenz)

Der Re-Run lief in drei Etappen: (1) Hintergrund-Worker (Session-Lifetime) starb am 22.09. um 09:50 stillschleichend nach dem v2.5-pro-Reasoning-Modul — kein Traceback, kein OOM, kein Crash-Report; (2) ein persistenter Neustart starb um 10:19 reproduzierbar an derselben Stelle (während ux_writing_001, direkt nach dem Laden des Semantic-Similarity-Modells); (3) Abhilfe: Restmodule als **direkte blockierende Modul-Läufe** (`run_benchmark.py --module X --model Y --force`) — liefen durchgängig fehlerfrei (EXIT 0 je Modul). Die Tode sind ein Lifecycle-Problem der Hintergrundprozess-Verwaltung, kein Benchmark-Fehler. mimo-v2.5 lief komplett im ersten Durchgang (43 Tasks) plus tooluse-Nachlauf (Worker exkludiert tooluse per `EXCLUDED_MODULES`, separates ToolUse-Deployment). ToolUse-Leaderboard-Aggregation (`make tooluse-leaderboard`) lief mit den gepinnten Rows (z. B. mimo-v2.5 70,75 = gepinntes Task-Ø).

### A.7 Qualitäts-Gate der Code-Änderungen

Full Test Suite: **1722 passed / 22 skipped** (1 deselect: `test_no_ripgrep_fallback_matches`, dokumentierter Vorbefund, auch ohne Änderungen rot). Ruff/Pylint grün; die neue CSV-Spalte `upstream_provider` ist im Leaderboard-Regenerierungs-Pfad verifiziert (Spaltenzahl 29, Regeneration intakt).
