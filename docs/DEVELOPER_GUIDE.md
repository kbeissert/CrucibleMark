# Developer Guide: Extending CrucibleMark

**Zielgruppe:** Entwickler, die neue Test-Module erstellen oder das Scoring-System erweitern wollen.

**Was Sie hier finden:**

- Quick Start: Neues Modul in 15 Minuten
- Asset-Format & YAML-Schema
- Scoring-Logik implementieren
- CSV-Output & Leaderboard-Integration
- Testing & Validation

> **Voraussetzung:** Grundkenntnisse in Python, YAML und Regex.

______________________________________________________________________

## ⚡ Quick Start: Neues Modul erstellen

### Option 1: Generator (Empfohlen)

```bash
make create-module
```

**Der Wizard fragt:**

1. Modul-ID (z.B. `api_design`)
1. Score Group (`routine`, `reasoning`, `info`)
1. Anzeigename (z.B. "API Design Review")

**Output:**

- Vollständige Ordnerstruktur
- Template `test.py` mit Basis-Code
- `config.yaml` vorkonfiguriert
- Dummy-Assets zum Testen

**Zeit:** ~2 Minuten bis zum ersten Test-Run

______________________________________________________________________

### 🚀 Development Loop & Testing

Für schnelle Iterationen ohne lange Wartezeiten (Memory Recovery) nutzen Sie den **Dev-Modus**:

```bash
# Startet Benchmark mit verkürzten Pausen (5-10s statt 20-30s)
make benchmark-dev
```

Oder direkt über das CLI:

```bash
python run_benchmark.py --dev --model ministral:8b
```

**Adaptive Pausen:**
Das Framework nutzt `utils/adaptive_pause.py`, um dynamische Erholungspausen einzulegen (wichtig für Mac M-Chips mit Unified Memory). Im Dev-Modus sind diese Pausen aggressiver verkürzt, was zu leicht verfälschter Performance führen kann, aber die Entwicklungszeit drastisch reduziert.

______________________________________________________________________

### Option 2: Manuell (für volle Kontrolle)

```bash
# Struktur erstellen
mkdir -p benchmark_modules/your_module/{assets,core}
touch benchmark_modules/your_module/{__init__.py,test.py,config.yaml,README.md}
touch benchmark_modules/your_module/core/{__init__.py,evaluators.py,constants.py}
```

**Minimale Dateien:**

- `config.yaml` – Metadaten & Leaderboard-Config
- `test.py` – Runner (Controller)
- `core/evaluators.py` – Scoring-Logik
- `assets/*.yaml` – Test-Cases

______________________________________________________________________

## 📁 Modul-Anatomie

### Verzeichnis-Struktur

```
benchmark_modules/
└── your_module/
    ├── README.md              # Dokumentation (Template siehe unten)
    ├── config.yaml            # ⚙️ SSOT (Single Source of Truth)
    ├── test.py                # 🎮 Controller (LLM-Ausführung)
    ├── assets/                # 📦 Test-Fixtures
    │   ├── your_module_001_task.yaml
    │   ├── your_module_002_task.yaml
    │   └── ...
    └── core/                  # 🧠 Business Logic
        ├── __init__.py
        ├── evaluators.py      # Scoring-Engine
        └── constants.py       # Schwellenwerte, Regex-Patterns
```

______________________________________________________________________

## 🏷️ Model Versioning

CrucibleMark nutzt eine deterministische, provider-spezifische Versionsermittlung.

### Aktuelle Regeln

1. **Kommerzielle Modelle:**

  - Versionen werden über feste Regex-Muster und statische Mappings aus dem Modellnamen abgeleitet.
  - Beispiele: `claude-sonnet-4-6` -> `4.6`, `gpt-4o` -> `2024-05-13`, `mistral-large-latest` -> `2411`.

1. **Lokale Ollama-Modelle:**

  - Versionen werden zur Laufzeit aus `ollama list` gelesen.
  - Verwendet wird die tatsächliche Ollama-ID des installierten Modells (Hash/ID-Spalte).
  - Für lokale Modelle ist die gespeicherte Version ausschließlich dieser Hash, um Silent Updates direkt am ID-Wechsel zu erkennen.

### Implementation

Die SSOT liegt in `utils/model_utils.py` in `get_model_version(model_name, provider, client)`.
Ein separates Fingerprinting-Modul wird nicht mehr verwendet.

______________________________________________________________________

## ⚙️ Konfiguration: `config.yaml`

### SSOT Prinzip (Single Source of Truth)

Die `config.yaml` ist in **zwei Bereiche** unterteilt:

#### 1. GLOBAL (Mandatory) – Framework-Contract

Diese Blöcke sind **Pflicht** und werden vom Framework gelesen:

```yaml
# ====================================================================
# GLOBAL CONFIGURATION (Required by Framework)
# ====================================================================

metadata:
  id: "your_module"                    # Eindeutige ID (Dateiname-Prefix)
  name: "Your Module Name"             # Anzeigename im Leaderboard
  version: "1.0.0"                     # SemVer
  description: "What this module tests"

integration:
  leaderboard:
    enable_scoring: true               # false = Info-Modul (kein Ranking)

    # Fallback für alle Assets ohne eigene Definition
    default_contribution:
      routine: 1.0                     # 100% Routine-Anteil
      reasoning: 0.0                   # 0% Reasoning-Anteil

    # Spalten im Leaderboard (optional)
    columns:
      - id: "your_score"
      - label: "Your Score"
    # (AVG(Routine) + AVG(Reasoning) / 2).
    # Dieses Modul liefert seinen Score an die entsprechende Kategorie.


execution:
  test_class: "YourModuleTest"         # Klassenname in test.py
  execution_mode: "standard"           # "standard" oder "batch"
  assets_dir: "assets"                 # Verzeichnis mit YAML-Files

# ====================================================================
# BENCHMARK DEFINITIONS (Cascading Scoring)
# ====================================================================

benchmarks:
  # Fall A: Standard (erbt default_contribution)
  - id: "your_module_001"
    name: "Basic Task"
    tier: 1

  # Fall B: Ausnahme (überschreibt Default)
  - id: "your_module_002"
    name: "Complex Puzzle"
    tier: 3
    score_contribution:
      routine: 0.2                     # 20% Routine
      reasoning: 0.8                   # 80% Reasoning
```

# ====================================================================

# OUTPUT CONTRACT: BENCHMARK RESULT

# ====================================================================

Every module's Controller (test.py) must return a `BenchmarkResult` object.
This strictly typed DTO ensures all modules provide compatible data for the Leaderboard.

The Result Schema (`schemas/result.py`) now includes:

```python
class BenchmarkResult(BaseModel):
    status: str
    primary_score: Optional[float]
    rendered_value: str

    # Execution Metrics
    execution_time: float   # Total runtime (Inference + Latency)
    load_time: float        # Cold Start / Loading to VRAM (Ollama specific)

    # ...
```

When implementing `execute()`, ensure you populate `load_time` if available via `llm_client.last_response_metadata["load_duration"]`.

```python
# Example in your Controller (test.py)
load_time = getattr(llm_client, "last_response_metadata", {}).get("load_duration", 0.0)

return BenchmarkResult(
    # ...
    load_time=load_time,
    # ...
)
```

```python
from schemas.result import BenchmarkResult

# The Object Schema
class BenchmarkResult(BaseModel):
    status: str = "success"           # success, error
    primary_score: Optional[float]    # 0.0 - 100.0 (ranking)
    rendered_value: str = "N/A"       # Display string ("85.5 %")

    # Execution Metrics
    execution_time: float             # Seconds
    tokens_used: int                  # Estimated token count
    cost_usd: float                   # Estimated cost
    raw_response: str                 # The full LLM output text

    # Identification
    model_version: str                # e.g., "gpt-4-0613"

    # Deep Data
    data: Dict[str, Any] = {}         # Module-specific details metrics
    meta: Dict[str, Any] = {}         # Context (timestamp, prompt_len)
```

**Why strict typing?**
Previous versions returned loose Dictionaries, leading to chaotic CSV columns (`score` vs `total_score` vs `result`). The `BenchmarkResult` class enforces a single standard.

______________________________________________________________________

#### 2. LOKAL (Optional) – Modul-spezifische Config

Beliebige eigene Blöcke für Ihre Scoring-Logik:

```yaml
# ====================================================================
# LOCAL CONFIGURATION (Module-specific, ignored by framework)
# ====================================================================

config:
  keyword_threshold: 0.4               # Min. 40% Keywords gefunden
  semantic_threshold: 0.78             # Semantische Ähnlichkeit

parameters:
  max_response_length: 2000
  timeout_seconds: 30

interpretation:
  tier1_description: "Labeled errors (easy)"
  tier2_description: "Obvious issues (medium)"
```

**Zugriff in test.py:**

```python
self.config = self.load_config()
threshold = self.config['config']['keyword_threshold']
```

______________________________________________________________________

### Execution Modes

| Mode | Verhalten | Use Case |
|------|-----------|----------|
| **`standard`** | Framework lädt Assets einzeln, instanziiert Test pro Asset | Code Quality, UX Writing (isolierte Tests) |
| **`batch`** | Framework übergibt alle Assets, Test kontrolliert Loop | Political Compass (3x Runs), Custom Aggregation |

______________________________________________________________________

### Kaskadierende Score-Contributions

**Ab v1.1:** Das Framework berechnet den **Routine Score** und **Reasoning Score** automatisch als Durchschnitt der entsprechenden Module. Die Unterscheidung findet primär auf **Modul-Level** statt (Mapping via Config), aber granulare Contributions sind weiterhin unterstützt.

1. **Asset-Level** (höchste Priorität):

   ```yaml
   - id: "reasoning_5d_002"
     score_contribution:
       reasoning: 1.0  # Ordnet dieses Asset dem Reasoning Score zu
   ```

1. **Modul-Level** (Standard):
   Definiert in `config.yaml` → `integration` → `default_contribution`.

   - `routine: 1.0` → Zählt zum "Routine Score" (z.B. Documentation, UX)
   - `reasoning: 1.0` → Zählt zum "Reasoning Score" (z.B. Logical Reasoning)

1. **Total Score Berechnung:**

   ```python
   Total Score = (Routine Score + Reasoning Score) / 2
   ```

   Dies belohnt Spezialisten und verhindert, dass reine Routine-Modelle durch Masse (viele einfache Tests) den Score verzerren.

______________________________________________________________________

## 📝 Asset-Format (YAML-Schema)

### Namenskonvention & Gruppierung (Last-Hyphen-Rule)

Das Framework ermittelt die Anzahl der Tests (für das Leaderboard) automatisch anhand der Dateinamen im `assets/` Ordner. Dabei unterscheiden wir zwischen **Einzeltests** und **Test-Gruppen** (z.B. ein Test mit mehreren Teilaufgaben).

**Das Schema:**
`{Modul}_{OptionalerName}_{Gruppe}-{Variante}.yaml`

Die Logik basiert auf dem **letzten Bindestrich (`-`)**:

- Alles **vor** dem letzten Bindestrich (gefolgt von Ziffern) wird als **Gruppen-ID** gewertet.
- Alles **danach** ist die Variante (z.B. Frage-Nummer) und wird nicht separat gezählt.

**Beispiele:**

| Dateiname | Erkannte Gruppe | Zählt als... |
|-----------|-----------------|--------------|
| `test_001.yaml` | `test_001` (Ganze Datei) | **1 Test** |
| `pol_axis1-001.yaml` | `pol_axis1` | **1 Test** (zusammen mit -002) |
| `pol_axis1-002.yaml` | `pol_axis1` | (Variante, zählt nicht extra) |

______________________________________________________________________

### Standard-Assets

```yaml
meta:
  id: "your_module_001"                # Muss mit Dateiname übereinstimmen
  difficulty: 2                        # Tier (1-4)
  name: "Descriptive Task Name"
  tags: ["category", "subcategory"]    # Optional

input:
  prompt: |
    Your instruction to the LLM.
    Can be multi-line.

  context: |                           # Optional: Zusätzlicher Context
    Background information...

evaluation:
  # Keyword-basierte Bewertung
  keywords:
    - "expected_term_1"
    - "expected_term_2"

  # Semantische Referenz (optional)
  golden_answer: |
    The ideal response should explain...

  # Strukturelle Anforderungen (optional)
  min_length: 100
  max_length: 500
  required_format: "markdown"          # markdown, json, code, text
```

______________________________________________________________________

### Info-Module (Structured Output)

Für Module ohne Scoring (z.B. Political Compass):

```yaml
meta:
  id: "political_compass_q001"

input:
  prompt: "Statement: Free markets solve all problems."

evaluation:
  # Keine Keywords! Stattdessen:
  output_type: "coordinate"            # coordinate, label, json
  expected_structure:
    x_range: [-10, 10]                 # Wirtschaftliche Achse
    y_range: [-10, 10]                 # Soziale Achse
```

______________________________________________________________________

## 🧠 Scoring-Logik implementieren

### Architektur-Prinzip: MVC

```
test.py (Controller)
   ↓ delegiert an
core/evaluators.py (Model/Logic)
   ↓ nutzt
core/constants.py (Config/Data)
```

**Regel:** `test.py` darf **keine** Scoring-Logik enthalten! Es orchestriert nur den Aufruf und verpackt das Ergebnis in `BenchmarkResult`.

### Der Controller (`test.py`)

Implementation des `execute`-Contracts:

```python
from schemas.result import BenchmarkResult

def execute(self, model: str, llm_client: Any, **kwargs) -> BenchmarkResult:
    # 1. Run LLM
    start_time = time.time()
    response_text = llm_client.query(prompt, ...)
    elapsed_time = time.time() - start_time

    # 2. Return pre-scored BenchmarkResult
    return BenchmarkResult(
        status="success",
        raw_response=response_text,
        execution_time=elapsed_time,
    )

def score_response(self, result: BenchmarkResult) -> BenchmarkResult:
    # 3. Delegate to pure text Evaluator
    evaluator = CodeQualityEvaluator(self.asset)
    scoring_result = evaluator.score_response(result.raw_response)

    # 4. Map Dict to the BenchmarkResult fields
    result.primary_score = scoring_result.get("score")
    result.tier = scoring_result.get("tier", "Tier 1 (Undefined)")
    result.data = scoring_result
    result.rendered_value = f"{result.primary_score} %" if result.primary_score is not None else "N/A"

    return result
```

______________________________________________________________________

### Beispiel: `core/evaluators.py`

```python
# Scoring Logic for Your Module

from typing import Dict, Any
import re

class YourEvaluator:
    # Evaluates LLM responses against criteria

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.keyword_threshold = self.config.get('keyword_threshold', 0.4)

    def evaluate(self, response_text: str, asset: Dict) -> Dict[str, Any]:
        # Main entry point
        # Args: response_text (raw LLM output), asset (YAML definition)
        # Returns: dict with score, details, passed flag

        # 1. Preprocessing
        clean_text = self._clean_response(response_text)

        # 2. Component Scoring
        keyword_score = self._check_keywords(clean_text, asset)
        structure_score = self._check_structure(clean_text, asset)

        # 3. Weighted Aggregation
        total_score = (keyword_score * 0.7) + (structure_score * 0.3)

        return {
            "score": total_score,
            "details": {
                "keywords": keyword_score,
                "structure": structure_score
            },
            "passed": total_score >= 50.0
        }

    def _clean_response(self, text: str) -> str:
        # Remove thinking tags, normalize whitespace
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        return text.strip()

    def _check_keywords(self, text: str, asset: Dict) -> float:
        # Keyword matching with threshold
        # Returns: 0-100 based on percentage of keywords found
        keywords = asset.get('evaluation', {}).get('keywords', [])
        if not keywords:
            return 100.0

        found = sum(1 for kw in keywords if kw.lower() in text.lower())
        percentage = (found / len(keywords))

        if percentage >= self.keyword_threshold:
            return 100.0 * percentage
        else:
            return 0.0

    def _check_structure(self, text: str, asset: Dict) -> float:
        # Check formatting requirements
        min_len = asset.get('evaluation', {}).get('min_length', 0)

        if len(text) >= min_len:
            return 100.0
        else:
            return (len(text) / min_len) * 100.0
```

______________________________________________________________________

## 📊 CSV-Output & Leaderboard

### Automatische Spalten

Diese Spalten werden vom Framework gefüllt:

| Spalte | Typ | Quelle |
|--------|-----|--------|
| `asset_id` | String | Dateiname |
| `model` | String | Parameter |
| `timestamp` | DateTime | System |
| `execution_time` | Float | `BenchmarkResult.execution_time` |
| `total_score` | Float | `BenchmarkResult.primary_score` |
| `percentage` | Float | Normalisiert (0-100) |
| `routine_contribution` | Float | config.yaml |
| `reasoning_contribution` | Float | config.yaml |

______________________________________________________________________

### Custom Spalten

Das Framework schreibt automatisch die Werte aus `BenchmarkResult.data` in die CSV, sofern sie flach genug sind.

In `test.py` (via Evaluator):

```python
# Evaluator return
return {
    "score": 85.0,
    "details": {
        "keyword_match": 100.0,    # Wird CSV-Spalte
        "structure_score": 70.0    # Wird CSV-Spalte
    }
}
```

Die `BenchmarkResult`-Validierung stellt sicher, dass keine zu tief verschachtelten Objekte (max 5 Levels) zurückgegeben werden.

______________________________________________________________________

## 🧪 Testing & Validation

### Asset-Schema prüfen

```bash
make validate-assets
```

### Modul-Isolations-Test

```bash
# Nur Ihr Modul in benchmark_config.yaml aktivieren
make benchmark-single MODEL=qwen2.5:7b MODULE=your_module
```

### Leaderboard-Integration

```bash
make leaderboard
# Prüfen: Ist Ihre Spalte da? Werte korrekt?
```

______________________________________________________________________

## 📐 Best Practices

### DO's ✅

1. **MVC-Trennung:** test.py = Controller, evaluators.py = Logik
1. **Determinismus:** Fixe Seeds, keine Random ohne Seed
1. **Config-First:** Schwellenwerte in config.yaml
1. **Dokumentation:** README.md nach Template

### DON'Ts ❌

1. **Keine LLM-Calls in Evaluators**
1. **Keine Modell-spezifischen Hacks** (Unfairer Boost)
1. **Keine Silent Failures** (Exceptions loggen!)

______________________________________________________________________

## 🆘 Troubleshooting

### "Scores are always 0%"

Debug-Checklist:

1. Nimmst du ein `BenchmarkResult` in `score_response()` an und retournierst es wieder?
1. Überträgst du `score_dict["score"]` zu `result.primary_score` in `score_response()`?
1. Keywords case-sensitive?

Debug-Tool:

```bash
python scripts/run_local_benchmark.py --debug-responses
# Prüfe: benchmark_scores/debug_responses/
```

______________________________________________________________________

## 📚 Weiterführende Ressourcen

- **ARCHITECTURE.md** – System-Design & MVC-Patterns
- **USER_GUIDE.md** – Wie Nutzer Module ausführen
- **GOLDEN_STANDARDS.md** – Referenz-Methodik

______________________________________________________________________

**Happy Coding! 🚀**

**Dokumenten-Version:** 1.0.0 (Rewrite Feb 2026)\
**Kompatibel mit:** CrucibleMark v0.9.5+
