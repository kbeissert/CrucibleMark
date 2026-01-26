# Neue Test-Module hinzufügen

Dieses Framework ist modular aufgebaut und ermöglicht das einfache Hinzufügen neuer Test-Module.

## Übersicht

Ein Test-Modul folgt einer klaren Trennung zwischen Interface und Implementierung ("Clean Architecture"):

```
benchmark_modules/
  └─ your_module/
     ├─ test.py               # Entry-Point (Test-Klasse, erbt von BaseTest)
     ├─ config.yaml           # Modul-Konfiguration
     ├─ README.md             # Dokumentation
     ├─ assets/               # Test-Assets (Testfälle als YAML)
     │  ├─ asset_001_*.yaml
     │  └─ ...
     ├─ core/                 # [NEU] Interne Business Logic & Helfer
     │  ├─ __init__.py
     │  ├─ models.py          # Datenstrukturen / Pydantic Models
     │  ├─ services.py        # Logik, Berechnungen
     │  └─ io.py              # File Helper
     └─ scripts/              # [NEU] Wartungs- & Export-Skripte (Standalone)
        └─ export_debug.py
```

## Schritt-für-Schritt Guide

### 1. Modul-Struktur erstellen

```bash
# Erstelle Verzeichnisse
mkdir -p benchmark_modules/your_module/{assets,core,scripts}
cd benchmark_modules/your_module

# Erstelle Dateien
touch __init__.py test.py config.yaml README.md
touch core/__init__.py core/models.py
```

### 2. Test-Klasse implementieren (`test.py`)

Deine Test-Klasse muss von `BaseTest` erben und die `execute`-Methode implementieren. Zusätzlich solltest du eine `score_response`-Methode für die Bewertung hinzufügen.

```python
"""Your Module Test Implementation."""

import sys
import time
from pathlib import Path
from typing import Dict, Any

# Import BaseTest
# Ensure root directory is in sys.path for imports
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from benchmark_modules.base_test import BaseTest

class YourModuleTest(BaseTest):
    """Test-Klasse für dein Modul."""
    
    def execute(self, model: str, llm_client, provider: str = 'ollama') -> Dict:
        """
        Führt den Test aus (LLM Query).
        
        Args:
            model: Modell-Name
            llm_client: Client Wrapper
            provider: 'ollama' oder 'mistral'/'anthropic'
            
        Returns:
            Dict mit raw_response und Metadaten
        """
        prompt = self.asset['prompt']
        
        # Optional: Context hinzufügen
        if 'context' in self.asset:
            full_prompt = f"{self.asset['context']}\n\n{prompt}"
        else:
            full_prompt = prompt
            
        start = time.time()
        try:
            # LLM Aufruf
            response = llm_client.query(model, full_prompt, provider=provider)
            elapsed = time.time() - start
            
            return {
                'raw_response': response,
                'execution_time': elapsed,
                'metadata': {
                    'model': model,
                    'asset_id': self.asset['metadata']['id']
                }
            }
        except Exception as e:
            return {
                'raw_response': f"ERROR: {str(e)}",
                'execution_time': 0.0,
                'metadata': {'error': str(e)}
            }
    
    def score_response(self, response: str) -> Dict[str, Any]:
        """
        Bewertet die LLM-Antwort.
        
        Args:
            response: Die Antwort des LLMs
        
        Returns:
            Dict mit Scores, Details und Status
        """
        if not response or response.startswith("ERROR:"):
            return {'status': 'error', 'total_score': 0}

        # 1. Scoring Logik implementieren
        # Tipp: Nutze self.asset['scoring'] für Konfiguration
        
        error_score = self._score_error_detection(response)
        solution_score = self._score_solution_quality(response)
        
        total_score = error_score + solution_score
        
        return {
            'status': 'success',
            'total_score': total_score,
            'max_score': 100,
            'category_scores': {
                'error_detection': {'achieved': error_score, 'max': 60},
                'solution_quality': {'achieved': solution_score, 'max': 40}
            },
            'details': ["Detail 1", "Detail 2"]
        }

    def _score_error_detection(self, response: str) -> int:
        # Implementiere deine Logik hier (z.B. Keyword Matching)
        return 0
        
    def _score_solution_quality(self, response: str) -> int:
        # Implementiere deine Logik hier
        return 0
```

### 3. Asset-Struktur (Tiered Difficulty)

Wir nutzen ein **Tiered Difficulty System**. Dein Asset sollte so aussehen:

```yaml
metadata:
  id: "001"
  name: "My Test Asset"
  difficulty: "Tiered (1-3)"

test_data:
  labeled_issues:    # Level 1 (Easy)
    - id: "L1"
      pattern: "TODO: Fix this"
      
  standard_issues:   # Level 2 (Medium)
    - id: "S1"
      pattern: "obvious_error()"
      
  advanced_issues:   # Level 3 (Hard)
    - id: "A1"
      pattern: "subtle_logic_bug"
```
        
        Returns:
            Dict mit:
            - total_score: Gesamtpunktzahl
            - max_score: Maximale Punktzahl
            - category_scores: Dict mit Kategorie-Scores
        """
        # Lade Scoring-Config aus Asset
        asset = self.load_asset()
        scoring_config = asset.get('scoring', {})
        categories = scoring_config.get('categories', {})
        
        # Implementiere deine Scoring-Logik
        category_scores = {}
        total_score = 0
        max_score = 0
        
        for cat_name, cat_config in categories.items():
            cat_max = cat_config.get('max_score', 10)
            
            # TODO: Implementiere Kategorie-spezifisches Scoring
            # Beispiel: Suche nach Keywords in Response
            cat_achieved = self._score_category(response, cat_name, cat_config)
            
            category_scores[cat_name] = {
                'achieved': cat_achieved,
                'max': cat_max
            }
            
            total_score += cat_achieved
            max_score += cat_max
        
        return {
            'total_score': total_score,
            'max_score': max_score,
            'category_scores': category_scores
        }
    
    def _score_category(self, response: str, category: str, config: dict) -> float:
        """
        Hilfsmethode: Bewertet einzelne Kategorie.
        
        Implementiere hier deine spezifische Logik.
        """
        # Beispiel: Zähle gefundene Items
        keywords = config.get('keywords', [])
        found_count = sum(1 for kw in keywords if kw.lower() in response.lower())
        
        return min(found_count, config.get('max_score', 10))
```

**Wichtige Methoden:**

- `__init__(asset_path)` - Konstruktor, ruft `super().__init__()` auf
- `execute(model, llm_client, provider)` - Führt Test aus, gibt Response + Zeit zurück
- `score_response(response)` - Bewertet Antwort, gibt Scores zurück
- `compare_to_golden_standard(response, golden_path)` - Optional, für Similarity (geerbt von BaseTest)

### 3. Modul-Config erstellen (`config.yaml`)

```yaml
# Metadaten
metadata:
  name: "Your Module Name"
  version: "0.1.0-alpha"
  description: "Beschreibung deines Moduls"
  author: "Dein Name"
  created: "2024-12-27"

# Modul-spezifische Einstellungen
module:
  test_class: "YourModuleTest"  # Name deiner Test-Klasse
  base_class: "BaseTest"

# Test-Assets
assets:
  path: "assets"
  count: 3  # Anzahl deiner Assets
  types:
    - type1
    - type2
    - type3

# Scoring-Kategorien
categories:
  category1:
    name: "Category 1 Name"
    weight: 1.0
    max_score: 10
  
  category2:
    name: "Category 2 Name"
    weight: 1.0
    max_score: 10

# Output-Konfiguration
output:
  format: "detailed"
  include_raw_response: false

# Golden Standards (optional)
golden_standards:
  enabled: true
  provider: "mistral"
  model: "mistral-large-latest"

# Tags für Filterung
tags:
  - your_tag1
  - your_tag2
```

### 4. Assets erstellen (`assets/*.yaml`)

Jedes Asset ist eine YAML-Datei mit folgendem Format:

```yaml
metadata:
  id: "your_module_001"
  name: "Test Name"
  version: "0.1.0-alpha"
  category: "your_module"
  description: "Was dieser Test prüft"

prompt:
  system: "Du bist ein Experte für..."
  user: |
    Analysiere folgenden Code:
    
    ```python
    # Dein Test-Code hier
    ```
    
    Finde alle Probleme in diesen Kategorien:
    1. Category 1
    2. Category 2
    
    Format: JSON mit Array 'issues'

expected_output:
  type: "json"
  schema:
    type: "object"
    properties:
      issues:
        type: "array"

scoring:
  categories:
    category1:
      name: "Category 1"
      weight: 1.0
      max_score: 10
      keywords: ["keyword1", "keyword2"]
    
    category2:
      name: "Category 2"
      weight: 1.0
      max_score: 10
      keywords: ["keyword3", "keyword4"]

# Golden Standard Config (optional)
golden_standard:
  generate_with:
    - provider: "mistral"
      model: "mistral-large-latest"
```

### 5. README erstellen (`README.md`)

```markdown
# Your Module Name

## Übersicht
Beschreibung was dein Modul testet.

## Test-Kategorien

### 1. Test Name (asset_001)
**Ziel:** Was wird getestet

**Testet:**
- Item 1
- Item 2
- Item 3

**Score:** 10 Items = 100%

## Verwendung

\```bash
# Mit globalem Benchmark
python run_benchmark.py

# Mit Make
make benchmark-module MODULE=your_module
\```

## Ergebnisse

Wie werden Ergebnisse interpretiert?

## Modul erweitern

Wie können weitere Assets hinzugefügt werden?
```

### 6. Modul in Config registrieren

Bearbeite `benchmark_config.yaml` im Root:

```yaml
modules:
  # Bestehende Module...
  
  your_module:
    name: "Your Module Name"
    description: "Kurze Beschreibung"
    path: "test_modules/your_module"
    test_class: "YourModuleTest"
    version: "0.1.0-alpha"
    enabled: true  # true = verfügbar im Benchmark
    assets_count: 3
    tags:
      - your_tag1
      - your_tag2
```

### 7. Testen

```bash
# Modul-Struktur prüfen
ls -la test_modules/your_module/

# Assets validieren (falls validator vorhanden)
make validate

# Benchmark ausführen
make benchmark-module MODULE=your_module

# Oder interaktiv
python run_benchmark.py
# Dann Modul auswählen
```

## Best Practices

### Code-Qualität

✅ **DO:**
- Erbe von `BaseTest`
- Implementiere alle erforderlichen Methoden
- Nutze Type Hints
- Schreibe Docstrings
- Handle Exceptions gracefully
- Teste mit mehreren Modellen

❌ **DON'T:**
- Hardcode keine Pfade
- Verlasse dich nicht auf externe APIs ohne Fallback
- Ignoriere keine Fehler
- Mische keine Test-Logik mit Scoring-Logik

### Asset-Design

✅ **DO:**
- Klare, präzise Prompts
- Strukturierte Output-Formate (JSON/YAML)
- Realistische Test-Daten
- Konsistente Kategorien
- Dokumentiere erwartete Ergebnisse

❌ **DON'T:**
- Zu triviale Tests
- Zu komplexe Tests (split in mehrere Assets)
- Ambigue Anweisungen
- Inkonsistente Scoring-Logik

### Dokumentation

✅ **DO:**
- README mit Übersicht und Beispielen
- Config mit klaren Kommentaren
- Inline-Dokumentation in Code
- Beispiele für Verwendung

❌ **DON'T:**
- Annahmen über Vorwissen
- Technischer Jargon ohne Erklärung
- Veraltete Dokumentation

## Beispiel-Modul

Schaue dir das `code_quality` Modul an:

```
test_modules/code_quality/
  ├─ __init__.py
  ├─ test.py              # ~600 Zeilen, vollständige Implementierung
  ├─ config.yaml          # Kategorie-Definitionen
  ├─ README.md            # Umfassende Doku
  └─ assets/
     ├─ asset_001_wcag_audit.yaml
     ├─ asset_002_security_audit.yaml
     ├─ asset_003_performance_audit.yaml
     ├─ asset_004_api_design_audit.yaml
     └─ asset_005_code_smells_audit.yaml
```

## Troubleshooting

### Modul wird nicht erkannt

**Problem:** `python run_benchmark.py` zeigt Modul nicht an

**Lösung:**
1. Prüfe `benchmark_config.yaml` - ist `enabled: true`?
2. Existiert `test_modules/your_module/test.py`?
3. Ist Test-Klasse korrekt benannt in config?

### Import-Fehler

**Problem:** `ModuleNotFoundError: No module named 'test_modules'`

**Lösung:**
```python
# In test.py ganz oben:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

### Scoring funktioniert nicht

**Problem:** `total_score` ist immer 0

**Lösung:**
- Debugge `score_response()` Methode
- Prüfe ob Response das erwartete Format hat
- Logge Kategorie-Scores einzeln

## Support

Bei Fragen oder Problemen:
- Schaue in `test_modules/code_quality/` für vollständiges Beispiel
- Lese `docs/CODE_QUALITY.md` für Details
- Erstelle GitHub Issue mit:
  - Modul-Name
  - Fehlermeldung
  - Asset-Beispiel (wenn relevant)

## Lizenz

Alle neuen Module unterliegen der MIT License des Frameworks.
