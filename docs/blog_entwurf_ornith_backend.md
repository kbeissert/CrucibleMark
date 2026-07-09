# Der Vogel, der zweimal flog — Was passiert, wenn derselbe Benchmark zwei Backends testet

*Entwurf für cruciblemark.com/magazine — Juli 2026*

---

## Einleitung: Die Ausgangslage

Ornith 1.0 35B ist ein lokales Sprachmodell, das auf dem Qwen3-Architektur-Stack
basiert. Wie viele moderne Modelle seiner Klasse verfügt es über eine
"Thinking"-Fähigkeit: Das Modell kann vor der eigentlichen Antwort eine
interne Reasoning-Phase durchlaufen — einen Gedankenprozess, der im Output
als `<think〉`-Block erscheint und vom Modell selbst generiert wird.

Für CrucibleMark bedeutete das ein Problem. Thinking-Modelle verbrauchen
massiv mehr Token, brauchen länger, und ihre Reasoning-Phase kann bei
bestimmten Aufgabentypen in Endlosschleifen geraten. Eine frühe Messung
des Ornith-Modells auf ux_writing-Aufgaben hatte einen Score von 1,1 Prozent
ergeben — nicht weil das Modell inkompetent war, sondern weil es sein gesamtes
Token-Budget für internes Reasoning verbrauchte, bevor es zur Antwort kam.

Die Lösung schien einfach: Thinking abschalten. Beide Backends — llama.cpp
und vLLM — boten dafür einen Konfigurationsparameter. Beide wurden auf
"Thinking OFF" gesetzt. Der Benchmark lief. Die Ergebnisse schienen plausibel.

Bis sie es nicht mehr taten.

---

## Teil 1: Das Experiment

### Die Frage

Wenn dasselbe Modell auf derselben Hardware mit denselben Sampling-Parametern
auf zwei verschiedenen Inference-Backends läuft — wie unterschiedlich sind
dann die Ergebnisse?

Die Konfiguration war so synchronisiert wie möglich:

| Parameter | llama.cpp | vLLM |
|---|---|---|
| Modell | Ornith 1.0 35B Q8_0 (GGUF) | Ornith 1.0 35B FP8 (Safetensors) |
| Quantisierung | Q8_0 (8-bit, bartowski) | FP8 (8-bit, NVIDIA Modelopt) |
| temperature | 0.6 | 0.6 |
| top_p | 0.95 | 0.95 |
| top_k | 20 | 20 |
| max_tokens | 8192 | 8192 |
| Thinking | `--reasoning off` | `enable_thinking: false` |
| Hardware | RTX 4070 (Spark) | RTX 4070 (Spark) |

Die Hypothese: Beide Backends sollten ähnliche Ergebnisse liefern. FP8
und Q8_0 sind beide 8-bit-Quantisierungen. Die Architektur-Unterschiede
zwischen llama.cpp und vLLM sollten sich vor allem in der Geschwindigkeit
äußern, nicht in der Ergebnisqualität.

### Die Überraschung

Die ersten zwei Module liefen deutlich schlechter auf vLLM. Der komplette
Benchmark bestätigte den Trend:

| Backend | Ø Score | Code Quality | CLI | Reasoning | Cultural Intel | Tool Exec |
|---|---|---|---|---|---|---|
| llama.cpp (Q8_0) | **76,3 %** | 73,7 | 93,0 | 77,8 | 76,6 | 89,2 |
| vLLM (FP8) | **73,9 %** | 67,2 | 86,2 | 79,5 | 67,2 | 80,8 |
| Delta | −2,4 pp | −6,5 | −6,8 | +1,7 | −9,4 | −8,4 |

2,4 Prozentpunkte Gesamtabstand. Bei einzelnen Modulen bis zu 9,4 pp
(Cultural Intelligence). Das ist nicht Rauschen. Das ist ein systematischer
Effekt.

---

## Teil 2: Die Hypothesen

### Hypothese A: Die Quantisierung

Die naheliegendste Erklärung: Die FP8-Quantisierung ist schlechter als
die Q8_0-GGUF. Bartowski's GGUF-Quantisierungen haben einen exzellenten
Ruf; NVIDIA's Modelopt-FP8 ist ein automatisierter Prozess, der möglicherweise
bei bestimmten Modellarchitekturen suboptimal abschneidet.

Diese Hypothese hätte bedeutet: Der Benchmark misst einen echten
Qualitätsunterschied zwischen zwei Quantisierungsverfahren.

### Hypothese B: Der Thinking-Modus

Die alternative Erklärung: Die beiden Backends unterdrücken Thinking
unterschiedlich gut. Wenn llama.cpp's "Thinking OFF" nicht wirklich
funktioniert, das Modell also heimlich weiterdenkt, dann sind die besseren
Ergebnisse kein Quantisierungs-Vorteil — sondern ein unbeabsichtigter
Thinking-Bonus.

---

## Teil 3: Die Untersuchung

### Der Smoke-Test

Der erste Test war ein direkter API-Call gegen beide Server mit einem
komplexen Reasoning-Prompt (ein Farmer-Optimierungsproblem). Das Ergebnis:

- **vLLM:** `reasoning: null`, keine `<think〉`-Tags, `finish_reason: "stop"`
  → Thinking definitiv OFF.
- **llama.cpp:** `reasoning_content` gefüllt mit "Here's a thinking process:..."

Das war unerwartet. `--reasoning off` sollte Thinking unterdrücken.
Stattdessen generierte das Modell weiterhin Reasoning — nur nicht in
`<think〉`-Tags, sondern als Klartext.

### Die systematische Analyse

Die CSV-Daten bestätigten das Muster über alle 50 Benchmark-Tasks:

| Metrik | llama.cpp | vLLM |
|---|---|---|
| Tasks mit Think-Content | **22 / 50 (44 %)** | **0 / 49 (0 %)** |
| Ø Score MIT Think-Content | 80,98 % | — |
| Ø Score OHNE Think-Content | 75,39 % | 75,55 % |

Die Zahlen sind eindeutig:

1. **llama.cpp denkt mit** — in 44 % der Tasks generiert das Modell
   Reasoning-Content, obwohl `--reasoning off` gesetzt ist.
2. **vLLM denkt nicht** — in 0 % der Tasks erscheint Think-Content.
3. **Ohne Thinking sind beide nahezu identisch** — 75,39 % vs 75,55 %
   (Delta +0,16 pp). Die Quantisierung ist **nicht** der Faktor.

Der gesamte Score-Unterschied von 2,4 pp kommt von den 22 Tasks, in denen
llama.cpp heimlich weitergedacht hat. Diese Tasks sind überwiegend
Reasoning-Aufgaben (Metacognition, Logische Rätsel) und CLI-Aufgaben
(das Modell analysiert die Aufgabe vor dem Codieren).

---

## Teil 4: Warum `--reasoning off` nicht tut, was es sagt

### Drei Konfigurationsschichten

Die Ursache liegt darin, wie die beiden Backends Thinking steuern:

**vLLM** nutzt die Chat-Template-Variable `enable_thinking`:
```
--default-chat-template-kwargs '{"enable_thinking":false}'
```
Diese Variable geht an das Chat-Template (`chat_template.jinja`). Bei
`enable_thinking=false` emittiert das Template einen leeren
`<think〉\n\n`-Block. Das Modell sieht: "Thinking-Block ist leer, ich
überspringe Reasoning." Das funktioniert zuverlässig.

**llama.cpp** nutzt den Server-Flag `--reasoning off`:
```
--reasoning off
```
Dieser Flag steuert, wie der Server `<think〉`-Tags in der Modell-Antwort
**parst** — nicht, ob das Modell **generiert**. `--reasoning off` bedeutet:
"Extrahiere keine `<think〉`-Tags in ein separates `reasoning_content`-Feld."
Aber das Modell generiert trotzdem Reasoning. Der Server gibt es als
`reasoning_content` zurück (oder lässt es im Haupt-Content).

Das ist kein Bug im engeren Sinne — es ist eine Semantik-Falle.
"Reasoning off" klingt nach "das Modell denkt nicht". Tatsächlich heißt
es nur "der Server parst keine Tags".

### Der praktische Effekt

Ein Nutzer, der llama.cpp mit `--reasoning off` startet, bekommt:

- Bessere Ergebnisse (das Modell denkt mit, ohne dass der Nutzer es weiß)
- Langsamere Responses (Reasoning braucht Zeit)
- Höheren Token-Verbrauch (Reasoning kostet Token)

Ist das schlecht? Aus Nutzersicht: Nein. Der Nutzer will gute Ergebnisse.
Wenn das Modell "heimlich" nachdenkt und dadurch bessere Antworten gibt,
ist das ein Feature, kein Bug.

Aus Benchmark-Sicht: Es ist ein Problem. Denn der Benchmark sollte
kontrollierte Bedingungen schaffen. "Thinking OFF" auf beiden Backends
sollte dasselbe bedeuten. Tut es aber nicht.

---

## Teil 5: Die Entscheidung

### Benchmark oder Realität?

Die zentrale Frage: Soll der Benchmark künstliche Fairness herstellen
(both backends truly thinking-off), oder soll er abbilden, was reale
Nutzer erleben?

Die Antwort: **Beides ist legitim — aber man muss wissen, was man misst.**

Ein Benchmark, der "Thinking OFF" misst, braucht vLLM (das einzige
Backend, das es zuverlässig unterdrückt). Ein Benchmark, der "was bekommt
ein realer Nutzer" misst, braucht llama.cpp (das ist, was Nutzer lokal
einsetzen).

Für CrucibleMark fiel die Entscheidung auf **Realität**:

- llama.cpp ist der primäre Backend für lokale Single-User-Modelle.
- vLLM's Stärken (Continuous Batching, Multi-Sequence-Throughput) bringen
  Single-User nichts.
- Das "geleckte" Thinking IST die Realität für jeden, der llama.cpp
  lokal nutzt. Es zu "reparieren" würde die Ergebnisse künstlich
  verschlechtern — ohne dass reale Nutzer davon profitieren.
- vLLM bleibt als Connector im Framework, für zukünftige Safetensors-Modelle
  (z.B. sehr große Modelle wie Kimi K2, für die es keine GGUF-Quantisierung
  gibt).

### Was mit dem Ornith-Ergebnis passiert

Beide Ergebnisse bleiben im Leaderboard:

- **llama.cpp (76,3 %):** Das echte Nutzer-Erlebnis. Thinking leckt durch,
  das Modell ist besser als konfiguriert.
- **vLLM (73,9 %):** Die saubere Thinking-OFF-Messung. Referenzwert für
  faire Vergleiche.

Wer das Modell lokal einsetzen will, sieht: 76,3 % ist, was er bekommt.
Wer eine Produktion mit Thinking-Suppression plant, sieht: 73,9 % ist,
was übrig bleibt.

---

## Teil 6: Die größere Lektion

### Backend-Transparenz

Der Benchmark zeigt: Die Wahl des Inference-Backends ist nicht nur eine
Performance-Entscheidung. Sie beeinflusst die Ergebnisqualität — manchmal
massiv. Ein Modell, das auf llama.cpp 76 % erreicht, kann auf vLLM 74 %
erreichen, nicht weil vLLM schlechter ist, sondern weil es Thinking
konsequenter unterdrückt.

Das ist kein Defekt. Es ist Information. Und genau diese Information
sollte ein Benchmark liefern.

### Die `<think〉`-Falle

Die Geschichte von `--reasoning off` ist ein Lehrstück über
Konfigurations-Semantik. Ein Parameter, der "off" heißt, sollte das
Gewünschte auch tun. Wenn er nur das Parsen abschaltet, nicht die
Generierung, sollte er `--reasoning-parse off` heißen — oder
`--no-think-tag-extraction`.

In der Praxis vertrauen Nutzer auf Parameternamen. `--reasoning off`
klingt eindeutig. Die Implementierung ist es nicht. Das ist nicht
llama.cpp's Schuld — es ist eine Erinnerung daran, dass Konfiguration
immer verifiziert werden muss, nicht nur gesetzt.

### Was CrucibleMark daraus lernt

1. **Backend-spezifische Effekte sind real.** Ein Benchmark, der nur
   einen Backend pro Modell testet, blendet diese Effekte aus.
2. **Thinking ist keine binäre Größe.** Zwischen "ON" und "OFF" liegt
   ein Spektrum: voll aktiviert, adaptiv (Modell entscheidet selbst),
   "leaked" (Backend unterdrückt nicht zuverlässig), wirklich aus.
3. **Die beste Messung ist die realistischste.** Wenn 90 % der Nutzer
   llama.cpp einsetzen, ist der llama.cpp-Score der relevante Wert —
   auch wenn er "unfair" ist gegenüber vLLM.

---

## Fazit

Ornith 1.0 35B ist ein gutes Modell. Auf llama.cpp erreicht es 76,3 %,
auf vLLM 73,9 %. Beide Zahlen sind richtig. Sie messen nur unterschiedliche
Dinge.

Der 2,4-Punkte-Unterschied ist nicht die Quantisierung. Er ist das
Denken, das durch die Hintertür hereinkommt. Manchmal ist die beste
Optimierung die, die man nicht selbst vornimmt — sondern die das System
für einen erledigt.

Und manchmal ist ein Parameter, der "off" heißt, einfach nur ein
Wort.

---

*CrucibleMark ist ein unabhängiges Benchmark-Framework für Sprachmodelle.
Alle Testergebnisse und Modell-Reviews sind öffentlich einsehbar unter
cruciblemark.com.*

---

## Anhang: Technische Details

### Datenpunkte

| Metrik | llama.cpp Q8_0 | vLLM FP8 |
|---|---|---|
| Ø Score (Leaderboard) | 76,3 % | 73,9 % |
| Ø Score (alle Tasks, roh) | 77,9 % | 75,6 % |
| Tasks mit Think-Content | 22/50 (44 %) | 0/49 (0 %) |
| Ø Score MIT Think-Content | 80,98 % | — |
| Ø Score OHNE Think-Content | 75,39 % | 75,55 % |
| Think-Content Format | Klartext ("Here's a thinking process:...") | — |
| Reasoning-Tokens | nicht gemeldet | `reasoning: null` |

### Konfiguration

**llama.cpp Server-Start:**
```bash
llama-server --model ornith-1.0-35b-Q8_0.gguf \
  --reasoning off \
  --temp 0.6 --top-p 0.95 --top-k 20 \
  --ctx-size 131072
```

**vLLM TOML:**
```toml
model_path = "ornith-1.0-35B-FP8"
max_model_len = 131072
extra_args = [
  "--default-chat-template-kwargs {\"enable_thinking\":false}",
  "--reasoning-parser qwen3",
  "--max-num-seqs 1",
]
```

**Aufrufbeispiele (für später, ohne Server-Restart):**
```bash
# Default: no thinking
curl -X POST http://localhost:3300/v1/chat/completions -d '{
  "model": "ornith-1.0-35B-FP8",
  "messages": [{"role":"user","content":"..."}],
  "temperature": 0.6, "top_p": 0.95, "top_k": 20
}'

# Thinking on (pro Request):
curl -X POST http://localhost:3300/v1/chat/completions -d '{
  "model": "ornith-1.0-35B-FP8",
  "messages": [{"role":"user","content":"..."}],
  "temperature": 0.6, "top_p": 0.95, "top_k": 20,
  "chat_template_kwargs": {"enable_thinking": true}
}'
```

### Think-Content-Beispiel (llama.cpp, reasoning_metacog_001)

```
Here's a thinking process:

1.  **Analyze User Input:**
   - **Problem:** A farmer has 17 sheep. All but 9 die. How many sheep are left?
   - **Constraints:**
     - System prompt says: "You are a logic expert. Solve the given problem
       step-by-step. Show your reasoning process clearly ('Chain of Thought').
       Finally, provide the clear Answer."
     - Example format requires `<thought>` tags before the answer.
     - Language: "Antworte auf Deutsch." (Answer in German)
   - **Key Phrase:** "All but 9 die."
```

Dies ist **kein** `<think〉`-Tag-Content. Es ist Klartext, den das Modell
als Teil seiner regulären Antwort generiert. Der llama.cpp-Server gibt
ihn als `reasoning_content` im API-Response zurück.
