# Neue Test-Module hinzufügen

Dieses Framework folgt einer strikten **Core/MVC-Architektur**. Ein Modul besteht aus einem Runner (`test.py`) und einer Business-Logik (`core/evaluators.py`).

## Übersicht der Struktur

```
benchmark_modules/
  └─ your_module/
     ├─ test.py               # CONTROLLER: Führt LLM aus, misst Zeit
     ├─ config.yaml           # Metadaten (ID, Name, Version)
     ├─ README.md             # Doku nach Standard-Template
     ├─ assets/               # DATA: YAML-Dateien mit Testfällen
     │  ├─ asset_001_*.yaml
     │  └─ ...
     └─ core/                 # MODEL & LOGIC
        ├─ __init__.py
        ├─ evaluators.py      # Die eigentliche Scoring-Logik
        └─ constants.py       # Schwellenwerte, Regex-Pattern, Config
```

---

## 🚀 Quick Start (Empfohlen)

Statt alles manuell anzulegen, nutze den Generator:

```bash
make create-module
```

Das Skript führt dich interaktiv durch die Einrichtung:
1.  **Modul-Name** (z.B. `context_awareness`)
2.  **Score Group** (Wichtig für Leaderboard: `routine`, `reasoning` oder `info`)
3.  Erstellt automatisch alle Ordner, `config.yaml`, `test.py` und Dummy-Evaluatoren.
4.  Gibt dir den Block für die `benchmark_config.yaml` aus.

Danach kannst du direkt bei **Schritt 2** (Logic implementieren) weitermachen.

---

## Manuelle Einrichtung (Reference)

### 1. Verzeichnisse erstellen

```bash
mkdir -p benchmark_modules/your_module/{assets,core}
touch benchmark_modules/your_module/{__init__.py,test.py,config.yaml,README.md}
touch benchmark_modules/your_module/core/{__init__.py,evaluators.py,constants.py}
```

### 2. Konfiguration (`config.yaml`) - SSOT v3.1

Definiere Metadaten und Leaderboard-Verhalten nach dem neuen **Kaskadierenden Scoring-Modell**.

> **⚠️ WICHTIG: Globale vs. Lokale Konfiguration**
> Die `config.yaml` ist in zwei Bereiche unterteilt:
> 1.  **GLOBAL (Mandatory):** Die Blöcke `metadata`, `integration` und `execution`. Diese werden vom zentralen Runner benötigt und **müssen** vorhanden sein.
> 2.  **LOKAL (Optional):** Modulentwickler können beliebige eigene Blöcke (z.B. `config`, `parameters`, `interpretation`) hinzufügen. Diese werden vom Framework ignoriert und stehen nur der lokalen `test.py` zur Verfügung.

```yaml
metadata:
  id: "your_module"
  name: "Your Module Name"
  version: "1.0.0"
  description: "..."
  
integration:
  leaderboard:
    enable_scoring: true   # Setze 'false' für reine Info-Module (z.B. Political Compass)

execution:
  test_class: "CodeQualityTest"     # Name der Klasse in test.py
  execution_mode: "standard"        # "standard" (pro Asset) oder "batch" (alle Assets auf einmal)
  assets_dir: "assets"

    # Fallback-Strategie: Gilt für alle Assets, die keine direkte Definition haben
    default_contribution:
      routine: 1.0        # Standard für dieses Modul (z.B. 100% Routine)
      reasoning: 0.0      

    columns:
      - id: "your_score"
        label: "Your Score"
```

### ⚙️ Execution Modes

*   **`standard` (Default):** Der Runner lädt Assets einzeln und instanziiert den Test für jedes Asset neu. Ideal für isolierte Unit-Tests (z.B. Code Quality, Reasoning).
*   **`batch`:** Der Runner lädt *alle* Assets auf einmal und übergibt das Verzeichnis an die Test-Klasse. Die Test-Klasse kontrolliert den Loop über die Assets. Ideal für Module, die Zustände über mehrere Fragen hinweg halten müssen oder eigene Looping-Strategien (z.B. 3x Wiederholung aller Fragen beim Political Compass) verfolgen.

# 🆕 Kaskadierendes Scoring (Management by Exception)
benchmarks:
  # Fall A: Standard (Erbt default_contribution: Routine 1.0)
  - id: "your_module_001"
    name: "Standard Task"
    tier: 1

  # Fall B: Ausnahme (Überschreibt Default)
  - id: "your_module_002"
    name: "Complex Puzzle"
    tier: 3
    score_contribution:
      routine: 0.2    # Ein bisschen Routine (Formatting)
      reasoning: 0.8  # Hauptsächlich Logik
```

### 🧠 Das Konzept der Kaskadierung

Um Redundanz und Fehler zu vermeiden, folgt die Config einer strikten Hierarchie:

1.  **Granulares Asset-Level (Höchste Priorität):**
    Wenn ein Benchmark (unter `benchmarks:`) ein `score_contribution` Feld hat, gelten exakt diese Werte. Nutze dies für Ausnahmen (z.B. ein Logik-Rätsel in einem sonstigen Routine-Modul).

2.  **Modul-Level Default (Fallback):**
    Wenn ein Benchmark *keine* Werte definiert, greift `integration.leaderboard.default_contribution`.
    Das spart Tipparbeit: Definiere oben einmal den Standard (z.B. 100% Reasoning) und lasse die Felder in den Assets leer.

3.  **Globales Scoring (An/Aus):**
    Mit `enable_scoring: false` schaltest du das Modul komplett aus der *Total Score* Berechnung aus (ideal für rein informative Module oder Anomalie-Erkennung). Die Ergebnis-Spalte bleibt im Leaderboard aber sichtbar. 

### ℹ️ Spezialfall: Info-Module (Anomalie-Module)

Es gibt Module, die **keine Leistung bewerten** (gut/schlecht), sondern **Eigenschaften messen** (z.B. politische Ausrichtung, Antwort-Latenz, Halluzinations-Rate). Diese werden als **"Anomalie-Module"** behandelt.

Setze hierfür einfach:
```yaml
integration:
  leaderboard:
    enable_scoring: false
```

**Wann ist ein Modul "Info"?**
*   Es gibt kein "Richtig" oder "Falsch" (nur Koordinaten, Zeit, Anzahl).
*   Das Modul soll **NICHT** in den Routine- oder Reasoning-Score einfließen.

**Konfiguration (Unterschiede zum Standard):**
```yaml
integration:
  leaderboard:
    enable_scoring: false  # Modul zählt nicht zum Gesamt-Score
    
    columns:
      # Option 1: Standard (Manuell oder via Score)
      - id: "measure_a"
        label: "Einfacher Wert"
        weight: 0.0      

      # Option 2: Data Object Access (Structured Data)
      # Greift auf das interne JSON-Datenobjekt zu (Best Practice!)
      - id: "measure_b"
        label: "Komplexe Daten"
        type: "label"
        source:
          file: "your_module_results.csv"        # Dateiname in benchmark_scores/
          filter: { "run_id": "AVG" }            # Filter: Zeile wählen
          key: "display.ideology"                # Pfad im JSON-Datenobjekt (dot.notation)
          missing_value: "Ausstehend"            # Fallback
```

**Erklärung Data Object Access:**
Anstatt Werte mühsam im Framework zusammenzubauen (String Interpolation), speichert das Modul ein **strukturiertes Datenobjekt** in der Spalte `metrics_json`.
Das Leaderboard greift via `key` direkt auf die vorbereiteten Werte zu (z.B. `display.ideology` oder `raw.count`).
Das verlagert die Formatierungs-Logik sauber zurück ins Modul (Transformer).


### 3. Die Logic (`core/evaluators.py`)

Zuerst implementieren wir **nur** die Bewertunglogik. Sie sollte nichts von LLMs oder API-Calls wissen.

```python
"""
Scoring Logic for Your Module.
"""
from typing import Dict, Any

class YourEvaluator:
    """Evaluates the model response against criteria."""
    
    def evaluate(self, response_text: str, asset: Dict) -> Dict[str, Any]:
        """
        Main entry point for scoring.
        
        Args:
            response_text: The LLM output
            asset: The asset definition (metadata, expected answers)
            
        Returns:
            Dict containing scores and details.
        """
        # 1. Cleaning (e.g. strip <think> tags)
        clean_text = self._clean_response(response_text)
        
        # 2. Score Components
        score_a = self._check_keywords(clean_text, asset.get('keywords', []))
        score_b = self._check_length(clean_text)
        
        # 3. Aggregate
        total_score = (score_a * 0.7) + (score_b * 0.3)
        
        return {
            "score": total_score,
            "details": {
                "keyword_match": score_a,
                "length_check": score_b
            }
        }

    def _clean_response(self, text: str) -> str:
        return text.strip()
        
    def _check_keywords(self, text: str, keywords: list) -> float:
        # Implementation...
        return 100.0
```

### 3. Der Runner (`test.py`)

Der Runner verbindet das Framework mit deiner Logik. Er erbt von `BaseTest`.

```python
"""
Benchmark Runner for Your Module.
"""
import sys
from pathlib import Path
from typing import Dict, Any

# Ensure correct path for imports
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from benchmark_modules.base_test import BaseTest
from benchmark_modules.your_module.core.evaluators import YourEvaluator

class YourModuleTest(BaseTest):
    """Controller class for Your Module."""
    
    def __init__(self):
        super().__init__()
        self.evaluator = YourEvaluator() # Inject Logic
    
    def execute(self, model: str, llm_client, provider: str = 'ollama') -> Dict:
        """
        Orchestrates the test execution.
        """
        # 1. Prepare Prompt
        prompt = self.asset['prompt']
        
        # 2. Run LLM
        start_time = time.time()
        response = llm_client.generate(model=model, prompt=prompt)
        duration = time.time() - start_time
        
        # 3. Build Result
        return {
            "raw_response": response,
            "execution_time": duration,
            # ... other standard fields ...
        }

    def score_response(self, response: Dict) -> float:
        """
        Delegates scoring to the core evaluator.
        """
        result = self.evaluator.evaluate(
            response_text=response['raw_response'],
            asset=self.asset
        )
        
        # Store detailed breakdown for CSV output
        self.latest_score_details = result['details']
        
        # Return main float score
        return result['score']
```

### 4. Registrierung (`benchmark_config.yaml`)

Damit das Framework dein Modul findet und korrekt im Leaderboard anzeigt, trage es in die Haupt-Config ein.
**Wichtig:** Seit v0.9.6 (Config-First Leaderboard) sind `score_group` und `assets_count` Pflichtfelder für die korrekte Berechnung der Scores und des "Pending"-Status.

```yaml
modules:
  your_module:
    name: "Your Module Name"  # Anzeigename im Leaderboard
    description: "Kurze Beschreibung was getestet wird"
    test_class: "YourModuleTest"  # Name der Klasse in test.py
    enabled: true
    
    # Leaderboard Konfiguration (Wichtig!)
    assets_count: 5          # Anzahl der erwarteten Assets (für Progress-Bar/Status)
    score_group: "routine"   # Zählt zu: "routine" | "reasoning" | "info"
    
    tags:
      - tag1
      - tag2
```

*   **`score_group`**:
    *   `routine`: Alltagsaufgaben (Writing, Doku, Transformation). Beeinflusst den "Routine Score".
    *   `reasoning`: Logik, Code, Mathe. Beeinflusst den "Reasoning Score".
    *   `info`: Rein informativ (z.B. Political Compass). Beeinflusst keinen Score und blockiert nicht den Abschluss-Status.


### 5. Assets (`assets/*.yaml`)

Erstelle Testfälle im YAML-Format:

```yaml
meta:
  id: "your_module_001"
  difficulty: 2
  name: "Basic Test"

input:
  prompt: "Write a poem about rust."

evaluation:
  keywords: ["iron", "oxidize"]
  min_lines: 4
```

---

## Checkliste vor dem Commit

1.  ✅ **Clean Architecture**: Importiert `test.py` Logik aus `core/`?
2.  ✅ **Determinismus**: Sind die Scores bei gleichem Input immer gleich?
3.  ✅ **Namespace**: Haben die Klassen eindeutige Namen (`YourModuleTest`)?
