# Thinking-Tag-Inventar pro Modell-Familie

Automatisch generiert via `scripts/tools/discover_thinking_tags.py` —  **read-only Discovery**, keine Card-Updates.

- **Lauf-Start:** 2026-06-09T21:49:37.969514+00:00
- **Lauf-Ende:** 2026-06-09T21:53:45.758214+00:00
- **Modelle insgesamt:** 4
- **Davon Thinking erkannt:** 4 (100%)

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
| `gemma-3-12b-it` | llamacpp | ✅ | medium | `Inline CoT in: math, code, decision` | - |

<details>
<summary>Roh-Antworten (gekuerzt auf 300 chars/Prompt)</summary>

### `gemma-3-12b-it` (llamacpp)

- **math** (518 chars, tags=[], reasoning_t=0, inline_cot=True):
  ```
  Here's how to solve the problem step-by-step:  **1. Understand the Concept of Average Speed**  *   Average speed is calculated by dividing the total distance traveled by the total time taken. *   Formula: Average Speed = Total Distance / Total Time  **2. Identify the Given Information**  *   Total D...
  ```
- **code** (1086 chars, tags=[], reasoning_t=0, inline_cot=True):
  ```
  Okay, let's sort the list `[3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]` using the **Bubble Sort** algorithm. I'll explain each step.  **1. Understanding Bubble Sort**  Bubble Sort is a simple sorting algorithm that repeatedly steps through the list, compares adjacent elements, and swaps them if they are in th...
  ```
- **decision** (2568 chars, tags=[], reasoning_t=0, inline_cot=True):
  ```
  Okay, let's break down this incredibly complex ethical dilemma. The question of whether an autonomous car should swerve to avoid a pedestrian, even at the risk of the passenger's life, is a cornerstone of the ethical debate surrounding self-driving vehicles. There's no easy answer, and different eth...
  ```

</details>

## Hermes

**1/1 Modelle zeigen Thinking.** Gefundene Tags in Familie: _keine_

| Modell | Provider | Detected | Confidence | Signal | Tags |
|---|---|---|---|---|---|
| `hermes-3-8b` | llamacpp | ✅ | medium | `Inline CoT in: math` | - |

<details>
<summary>Roh-Antworten (gekuerzt auf 300 chars/Prompt)</summary>

### `hermes-3-8b` (llamacpp)

- **math** (400 chars, tags=[], reasoning_t=0, inline_cot=True):
  ```
  To find the average speed of the train, we need to divide the total distance traveled by the total time taken.  Given: - Distance traveled = 120 km - Time taken = 1.5 hours  Average speed = Distance ÷ Time  Step 1: Substitute the given values into the formula. Average speed = 120 km ÷ 1.5 hours  Ste...
  ```
- **code** (1048 chars, tags=[], reasoning_t=0, inline_cot=False):
  ```
  To sort the list [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5] step by step, we can use the Bubble Sort algorithm. Here's how it works:  1. Compare the first two elements of the list. If the first element is greater than the second element, swap them. 2. Move to the next pair of adjacent elements and repeat ste...
  ```
- **decision** (1795 chars, tags=[], reasoning_t=0, inline_cot=False):
  ```
  This is a complex moral dilemma that highlights the "trolley problem" in the context of autonomous vehicles. There are a few key considerations to weigh:  1. Duty to protect human life: The primary moral imperative is to minimize harm to human life. Swerving to avoid the pedestrian would save the pe...
  ```

</details>

## Qwen

**1/1 Modelle zeigen Thinking.** Gefundene Tags in Familie: _keine_

| Modell | Provider | Detected | Confidence | Signal | Tags |
|---|---|---|---|---|---|
| `qwen3-14b` | llamacpp | ✅ | medium | `Inline CoT in: math, code, decision` | - |

<details>
<summary>Roh-Antworten (gekuerzt auf 300 chars/Prompt)</summary>

### `qwen3-14b` (llamacpp)

- **math** (578 chars, tags=[], reasoning_t=0, inline_cot=True):
  ```
  To find the **average speed** of the train, we use the formula:  $$ \text{Average Speed} = \frac{\text{Total Distance}}{\text{Total Time}} $$  ---  ### **Step 1: Identify the given values**  - **Total Distance** = 120 km   - **Total Time** = 1.5 hours  ---  ### **Step 2: Plug the values into the for...
  ```
- **code** (1872 chars, tags=[], reasoning_t=0, inline_cot=True):
  ```
  Sure! Let's walk through the process of **sorting** the list:  ### Original List: ``` [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5] ```  ---  ## Step 1: Choose a Sorting Algorithm  We'll use the **Bubble Sort** algorithm for this explanation. It's a simple and intuitive algorithm that repeatedly steps through t...
  ```
- **decision** (4619 chars, tags=[], reasoning_t=0, inline_cot=True):
  ```
  The question of whether an autonomous car should swerve to avoid a pedestrian even if it risks the passenger's life is a deeply complex ethical dilemma that involves multiple philosophical, legal, and societal considerations. Here's a structured analysis of the key ethical considerations involved:  ...
  ```

</details>

## Qwen-Coder

**1/1 Modelle zeigen Thinking.** Gefundene Tags in Familie: _keine_

| Modell | Provider | Detected | Confidence | Signal | Tags |
|---|---|---|---|---|---|
| `qwen2.5-coder-7b` | llamacpp | ✅ | medium | `Inline CoT in: math, code, decision` | - |

<details>
<summary>Roh-Antworten (gekuerzt auf 300 chars/Prompt)</summary>

### `qwen2.5-coder-7b` (llamacpp)

- **math** (552 chars, tags=[], reasoning_t=0, inline_cot=True):
  ```
  To find the average speed of the train, we can use the formula:  \[ \text{Average Speed} = \frac{\text{Total Distance}}{\text{Total Time}} \]  Given: - Total Distance = 120 km - Total Time = 1.5 hours  Now, let's plug these values into the formula:  \[ \text{Average Speed} = \frac{120 \text{ km}}{1....
  ```
- **code** (975 chars, tags=[], reasoning_t=0, inline_cot=True):
  ```
  Sure, I'll sort the list using the Bubble Sort algorithm, which is a simple sorting algorithm that repeatedly steps through the list, compares adjacent elements, and swaps them if they are in the wrong order. The pass through the list is repeated until the list is sorted.  ### Step-by-Step Bubble So...
  ```
- **decision** (2589 chars, tags=[], reasoning_t=0, inline_cot=True):
  ```
  The question of whether an autonomous car should swerve to avoid a pedestrian, even if it risks the passenger's life, is a complex ethical dilemma that involves balancing various factors. Here are some key considerations:  1. **Safety and Responsibility**: Autonomous vehicles are designed to priorit...
  ```

</details>

## Cross-Family Statistik

| Familie | Modelle | Thinking erkannt | Anteil | Typische Tags |
|---|---|---|---|---|
| Gemma | 1 | 1 | 100% | _-_ |
| Hermes | 1 | 1 | 100% | _-_ |
| Qwen | 1 | 1 | 100% | _-_ |
| Qwen-Coder | 1 | 1 | 100% | _-_ |
