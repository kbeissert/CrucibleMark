# Thinking-Tag-Inventar pro Modell-Familie

Automatisch generiert via `scripts/tools/discover_thinking_tags.py` —  **read-only Discovery**, keine Card-Updates.

- **Lauf-Start:** 2026-06-09T21:59:03.618354+00:00
- **Lauf-Ende:** 2026-06-09T22:01:48.570246+00:00
- **Modelle insgesamt:** 3
- **Davon Thinking erkannt:** 3 (100%)

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

## DeepSeek

**1/1 Modelle zeigen Thinking.** Gefundene Tags in Familie: _keine_

| Modell | Provider | Detected | Confidence | Signal | Tags |
|---|---|---|---|---|---|
| `deepseek/deepseek-chat-v3.1` | openrouter | ✅ | medium | `Inline CoT in: math, code, decision` | - |

<details>
<summary>Roh-Antworten (gekuerzt auf 300 chars/Prompt)</summary>

### `deepseek/deepseek-chat-v3.1` (openrouter)

- **math** (666 chars, tags=[], reasoning_t=0, inline_cot=True):
  ```
  Alright, let's go step-by-step.    ---  **Step 1: Identify the given values**   - Distance traveled: \( 120 \ \text{km} \)   - Time taken: \( 1.5 \ \text{hours} \)    ---  **Step 2: Recall the formula for average speed**   \[ \text{Average speed} = \frac{\text{Total distance}}{\text{Total time}} \] ...
  ```
- **code** (1306 chars, tags=[], reasoning_t=0, inline_cot=True):
  ```
  Let's sort the list step by step using the **Insertion Sort** algorithm. Insertion Sort works by building a sorted portion of the list and inserting each unsorted element into its correct position in the sorted part.  **Initial list:** [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]  We'll traverse from the secon...
  ```
- **decision** (2412 chars, tags=[], reasoning_t=0, inline_cot=True):
  ```
  This is one of the core ethical dilemmas in autonomous vehicle (AV) programming, often called the "trolley problem" in modern form. There's no universally agreed-upon answer, as it involves deep value conflicts. Let's break down the ethical considerations.  ### Key Ethical Frameworks in Play  1.  **...
  ```

</details>

## Kimi

**1/1 Modelle zeigen Thinking.** Gefundene Tags in Familie: _keine_

| Modell | Provider | Detected | Confidence | Signal | Tags |
|---|---|---|---|---|---|
| `moonshotai/kimi-k2-thinking-20251106` | openrouter | ✅ | medium | `reasoning_tokens=4503` | - |

<details>
<summary>Roh-Antworten (gekuerzt auf 300 chars/Prompt)</summary>

### `moonshotai/kimi-k2-thinking-20251106` (openrouter)

- **math** (652 chars, tags=[], reasoning_t=355, inline_cot=True):
  ```
  Here is the step-by-step solution:  **Step 1: Identify the formula for average speed.** Average speed is calculated by dividing the total distance traveled by the total time taken. Average Speed = Total Distance / Total Time  **Step 2: Substitute the given values into the formula.** - Total Distance...
  ```
- **code** (2547 chars, tags=[], reasoning_t=4503, inline_cot=True):
  ```
  I'll sort this list using **Insertion Sort**, which is intuitive like sorting playing cards in your hand. Here's the step-by-step process:  ### Algorithm Explanation Insertion Sort builds a sorted portion from left to right. For each element, it finds the correct position in the already-sorted left ...
  ```
- **decision** (2361 chars, tags=[], reasoning_t=806, inline_cot=True):
  ```
  This is one of the most challenging ethical questions in autonomous vehicle design, with no consensus answer. Here are the key considerations:  **Core Ethical Tensions:**  1. **Utilitarian vs. Deontological Ethics**: A utilitarian approach would minimize total lives lost (swerve if it saves more peo...
  ```

</details>

## NVIDIA

**1/1 Modelle zeigen Thinking.** Gefundene Tags in Familie: _keine_

| Modell | Provider | Detected | Confidence | Signal | Tags |
|---|---|---|---|---|---|
| `nvidia/nemotron-3-ultra-550b-a55b` | openrouter | ✅ | medium | `reasoning_tokens=444` | - |

<details>
<summary>Roh-Antworten (gekuerzt auf 300 chars/Prompt)</summary>

### `nvidia/nemotron-3-ultra-550b-a55b` (openrouter)

- **math** (746 chars, tags=[], reasoning_t=46, inline_cot=True):
  ```
  **Step 1: Identify the formula for average speed.** The formula for average speed is: \[ \text{Average Speed} = \frac{\text{Total Distance}}{\text{Total Time}} \]  **Step 2: Identify the given values.** *   Total Distance = 120 km *   Total Time = 1.5 hours  **Step 3: Substitute the values into the ...
  ```
- **code** (770 chars, tags=[], reasoning_t=265, inline_cot=True):
  ```
  I will use the **Merge Sort** algorithm. It is a classic "Divide and Conquer" algorithm that is stable, efficient ($O(n \log n)$), and very intuitive to visualize step-by-step.  ---  ### **Algorithm: Merge Sort**  **Core Concept:** 1.  **Divide:** Recursively split the list in half until every sub-l...
  ```
- **decision** (792 chars, tags=[], reasoning_t=444, inline_cot=True):
  ```
  This is the central dilemma of algorithmic ethics in transportation, often framed as a modern "trolley problem." There is no universal consensus, but the ethical landscape can be mapped through several competing frameworks.  **Utilitarianism (Consequentialism)** From a strict utilitarian view, the c...
  ```

</details>

## Cross-Family Statistik

| Familie | Modelle | Thinking erkannt | Anteil | Typische Tags |
|---|---|---|---|---|
| DeepSeek | 1 | 1 | 100% | _-_ |
| Kimi | 1 | 1 | 100% | _-_ |
| NVIDIA | 1 | 1 | 100% | _-_ |
