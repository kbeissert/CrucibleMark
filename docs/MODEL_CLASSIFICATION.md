# Modell-Klassifizierung & RCI (Reasoning Complexity Index)

Dieses Dokument beschreibt das **Hybride Klassifizierungs-System** von CrucibleMark, inklusive des neuen **RCI (Reasoning Complexity Index)**.

## 📊 Der Reasoning Complexity Index (RCI)

Der RCI ist die zentrale Metrik zur Bewertung der kognitiven Tiefe eines Modells. Er reicht von **0% bis 100%**.

### Berechnung
Der Score setzt sich aus zwei Faktoren zusammen (siehe [Benchmark Complexity Tiers](ARCHITECTURE.md#benchmark-complexity-tiers) für Details):
1.  **Operationale Logik (60%)**: Kann das Modell komplexe Rätsel lösen? (Tier 1 & 2)
2.  **Metakognition (40%)**: Reflektiert das Modell über seinen eigenen Denkprozess? (Tier 3)

`RCI = (Avg_Tier1_2_Score * 0.6) + (Avg_Tier3_Score * 0.4)`

### Klassifizierung basierend auf RCI

| Kategorie | RCI Bereich | Beschreibung | Beispiel |
| :--- | :--- | :--- | :--- |
| **Non-Thinking Model** | < 50% | Löst Standard-Tasks, scheitert an Selbstreflexion. | Dolphin 8B (~42%) |
| **Basic Thinking Model** | 50% - 85% | Gute Logik, aber schwache Metakognition. | Qwen 2.5 (~65%) |
| **Deep Thinking Model** | > 85% | Exzellente Logik + aktive Selbstkorrektur. | DeepSeek R1 (~87%) |

---

## 🚀 Schnelleinstieg: Wie pflege ich neue Modelle?

Du musst **nicht** jedes Modell manuell anlegen. Das System arbeitet zu 80-90% automatisch.

### Dein täglicher Workflow

1.  Führe `make leaderboard` aus.
2.  Achte am Ende auf **gelbe Warnungen**:
    ```text
    ⚠️  REVIEW NEEDED: neues-modell:14b -> Metrics indicate Reasoning model but name unknown
    ```
3.  Entscheide:
    *   **Fall A:** Das Modell ist **Gen 1** (Standard), aber einfach nur langsam oder hatte einen Glückstreffer beim Reasoning Score.
        👉 **Lösung:** Eintrag in `model_overrides.yaml`.
    *   **Fall B:** Das Modell ist tatsächlich ein neues **Reasoning Modell (Gen 2)** (z.B. eine neue Version von DeepSeek-R1 oder ein weiterer "Thinking"-Abkömmling).
        👉 **Lösung:** Eintrag in `generation_heuristics.yaml` (wenn es eine ganze Familie ist) ODER temporär in `model_overrides.yaml`.

---

## 🛠 Konfigurations-Dateien

Das System besteht aus zwei Dateien im Root-Verzeichnis, die du bearbeiten kannst.

### 1. `model_overrides.yaml` (Dein Cockpit)

Hier trägst du Einzelentscheidungen ein. Diese Datei hat **höchste Priorität**.
Nutze sie für alles, was schnell gehen muss oder Ausnahmen sind.

```yaml
overrides:
  # BEISPIEL: Ein Standard-Modell, das fälschlicherweise als Reasoner erkannt wurde
  qwen3:8b:
    generation: Gen 1 (Pattern Matcher)
    reason: Standard Model, just slow execution time triggered detection
    last_reviewed: '2026-01-22'

  # BEISPIEL: Ein Modell, dessen Herkunft unklar war
  cogito:14b:
    generation: Gen 1 (Pattern Matcher)
    reason: High score but no evidence of reasoning training found in paper
    last_reviewed: '2026-01-22'
```

### 2. `generation_heuristics.yaml` (System-Update)

Hier definierst du **Patterns (Muster)**. Bearbeite diese Datei nur, wenn eine ganz neue *Klasse* von Modellen erscheint (z.B. "Gemma 4" führt "Thinking" ein).

```yaml
patterns:
  gen2_names:
    - "phi4"
    - "r1"        # Matches 'deepseek-r1', 'llama-r1', etc.
    - "reasoning" # Matches any model with 'reasoning' in name
```

Wenn du hier `- "gemma4"` hinzufügst, werden **ab sofort alle** Gemma 4 Modelle (8b, 27b, instruction, etc.) automatisch als Gen 2 erkannt.

---

## 🧠 Hintergrund: Wie die Automatik funktioniert

Das Skript `scripts/classify_generation.py` nutzt eine 3-Stufen-Logik:

1.  **Override Check:** Steht das Modell in `model_overrides.yaml`? Falls ja -> Nimm diesen Wert.
2.  **Auto-Metrik Check (High Confidence):**
    *   Ist das Modell sehr langsam (>40s) UND hat einen sehr hohen Reasoning Score (>70)?
    *   Passt der Name zu einem bekannten Muster (z.B. "r1")?
    *   -> Wenn beides JA: Automatisch **Gen 2**.
3.  **Heuristik Check:**
    *   Enthält der Name bekannte Pattern aus `generation_heuristics.yaml`?
    *   -> Automatisch **Gen 2**.
4.  **Fallback / Review:**
    *   Wenn die Metriken auf Gen 2 hindeuten (langsam + schlau), aber der Name unbekannt ist -> **FLAG FOR REVIEW**.
    *   Standardmäßig wird dann "Gen 1" angenommen, aber du bekommst die Warnung im Terminal.

### Warum dieser Aufwand?

Warum nicht einfach alles automatisch machen?
*   **Gen 3 (o1) ist unsichtbar:** Man kann am Output nicht erkennen, ob ein Modell "echtes" RL-Reasoning macht oder nur destilliert ist. Das muss man manuell wissen (`overrides`).
*   **False Positives:** Ein langsames Gen 1 Modell (z.B. auf alter Hardware oder unquantisiert) sieht für die Automatik wie ein "nachdenkendes" Gen 2 Modell aus.

Der hybride Ansatz spart dir 90% der Arbeit, lässt dir aber die Kontrolle über die verbleibenden 10%.
