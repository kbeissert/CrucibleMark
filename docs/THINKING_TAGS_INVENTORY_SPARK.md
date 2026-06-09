# Thinking-Tag-Inventar pro Modell-Familie

Automatisch generiert via `scripts/tools/discover_thinking_tags.py` —  **read-only Discovery**, keine Card-Updates.

- **Lauf-Start:** 2026-06-09T21:55:13.970230+00:00
- **Lauf-Ende:** 2026-06-09T21:58:25.100881+00:00
- **Modelle insgesamt:** 2
- **Davon Thinking erkannt:** 2 (100%)

## Methodik

Pro Modell werden 3 Probe-Prompts gesendet:
- **math**: `Solve step by step: A train travels 120 km in 1.5 hours. What is its average speed in km/h? Show your reasoning.`
- **code**: `Sort this list step by step and explain your algorithm: [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]`
- **decision**: `Should an autonomous car swerve to avoid a pedestrian even if it risks the passenger's life? Think through the ethical considerations before answering.`

**Signal-Hierarchie** (Confidence):
- **high**: Bekannte Think-Tags in Antwort (`<think>`, `<|thinking|>`, `<reflection>`, ...)
- **medium**: `reasoning_tokens > 0` in Provider-Metadaten ODER Inline-CoT im content-Feld
- **low**: Kein Signal

**Aktuell bekannte Tag-Liste** (SSoT: `utils/model_utils._THINK_TAGS`):

```python
_THINK_TAGS = ['<think>', '<thinking>', '<thought>', '<|thinking|>', '<|reasoning|>', '<reasoning>', '<reason>', '<reflection>', '<analysis>', '<plan>', '<scratchpad>', '<solution>', '<cot>']
```

## Gemma

**1/1 Modelle zeigen Thinking.** Gefundene Tags in Familie: _keine_

| Modell | Provider | Detected | Confidence | Signal | Tags |
|---|---|---|---|---|---|
| `gemma-4-26b-a4b-q8` | llamacpp_spark | ✅ | medium | `Inline CoT in: math, code, decision` | - |

<details>
<summary>Roh-Antworten (gekuerzt auf 300 chars/Prompt)</summary>

### `gemma-4-26b-a4b-q8` (llamacpp_spark)

- **math** (949 chars, tags=[], reasoning_t=0, inline_cot=True):
  ```
  To find the average speed of the train, follow these steps:  ### 1. Identify the given information From the problem, we know: *   **Total Distance ($d$):** $120\text{ km}$ *   **Total Time ($t$):** $1.5\text{ hours}$  ### 2. State the formula The formula for average speed is the total distance trave...
  ```
- **code** (1268 chars, tags=[], reasoning_t=0, inline_cot=True):
  ```
  To sort this list, I will use the **Bubble Sort** algorithm.   ### The Algorithm: Bubble Sort **How it works:** Bubble Sort works by repeatedly stepping through the list, comparing adjacent elements, and swapping them if they are in the wrong order. This process is repeated until the largest numbers...
  ```
- **decision** (2465 chars, tags=[], reasoning_t=0, inline_cot=True):
  ```
  The question of whether an autonomous vehicle (AV) should prioritize the lives of its passengers or pedestrians is a modern iteration of the "Trolley Problem," a classic thought experiment in ethics. There is no single "correct" answer, as the decision depends on which ethical framework one applies....
  ```

</details>

## Hermes

**1/1 Modelle zeigen Thinking.** Gefundene Tags in Familie: _keine_

| Modell | Provider | Detected | Confidence | Signal | Tags |
|---|---|---|---|---|---|
| `hermes-4.3-36b-q6` | llamacpp_spark | ✅ | medium | `Inline CoT in: math` | - |

<details>
<summary>Roh-Antworten (gekuerzt auf 300 chars/Prompt)</summary>

### `hermes-4.3-36b-q6` (llamacpp_spark)

- **math** (439 chars, tags=[], reasoning_t=0, inline_cot=True):
  ```
  To find the average speed of the train, we need to divide the distance traveled by the time taken.  Given: - Distance traveled: 120 km - Time taken: 1.5 hours  Step 1: Set up the equation for average speed. Average speed = Distance ÷ Time  Step 2: Substitute the given values into the equation. Avera...
  ```
- **code** (1068 chars, tags=[], reasoning_t=0, inline_cot=False):
  ```
  To sort the list [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5] using the Bubble Sort algorithm, we will repeatedly compare adjacent elements and swap them if they are in the wrong order. We will continue this process until no more swaps are needed, indicating that the list is sorted.  Step 1: [3, 1, 4, 1, 5, 9,...
  ```
- **decision** (1058 chars, tags=[], reasoning_t=0, inline_cot=False):
  ```
  This is a complex ethical dilemma with no easy answer. Some key considerations:  - Autonomous cars could potentially save many lives overall compared to human drivers, but this specific scenario pits one life against another.  - There's an argument that the car should prioritize the pedestrian since...
  ```

</details>

## Cross-Family Statistik

| Familie | Modelle | Thinking erkannt | Anteil | Typische Tags |
|---|---|---|---|---|
| Gemma | 1 | 1 | 100% | _-_ |
| Hermes | 1 | 1 | 100% | _-_ |
