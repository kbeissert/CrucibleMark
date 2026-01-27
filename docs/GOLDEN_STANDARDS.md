# Golden Standards Konfiguration

## Konzept

Das Framework erlaubt die Konfiguration **mehrerer kommerzieller LLM-Provider** für Tests und Vergleiche. **Ein Provider** wird als **Golden Standard** markiert und dient als Referenz für alle lokalen Modell-Benchmarks.

## Aufbau

### 1. Provider Konfiguration

In [`benchmark_config.yaml`](../benchmark_config.yaml) wird der Golden Standard separat definiert:

```yaml
# 1. Golden Standard Definition
golden_standard:
  provider: "mistral"              # Referenz auf providers.commercial.mistral
  model: "mistral-medium-latest"   # Spezifisches Modell
  description: "Mistral Medium als schnelle, leistungsstarke Referenz"

# 2. Provider Konfiguration
providers:
  commercial:
    mistral:
      name: "Mistral AI"
      api_type: "mistral"
      enabled: true
      env_var: "MISTRAL_API_KEY"
      models:
        - id: "mistral-large-latest"
          name: "Mistral Large (123B)"
        - id: "mistral-medium-latest"
          name: "Mistral Medium"
    
    openai:
      name: "OpenAI"
      api_type: "openai"
      enabled: true
      env_var: "OPENAI_API_KEY"
      models:
        - id: "gpt-4o"
          name: "GPT-4o"
        - id: "gpt-4o-mini"
          name: "GPT-4o Mini"
        - id: "o1-mini"
          name: "o1 Mini (Reasoning)"

    anthropic:
      name: "Anthropic"
      api_type: "anthropic"
      enabled: true
      env_var: "ANTHROPIC_API_KEY"
      models:
        - id: "claude-3-5-sonnet-20241022"
          name: "Claude 3.5 Sonnet"
```

### 2. Golden Standard Regeln

| Feld | Beschreibung | Pflicht |
|------|-------------|---------|
| `golden_standard.provider` | Name des Providers (muss in `providers` existieren) | ✅ Ja |
| `golden_standard.model` | Modell-ID (muss beim Provider existieren) | ✅ Ja |
| `providers.*.enabled` | Provider muss aktiviert sein | ✅ Ja |

**Wichtig:** 
- ⚠️ Der referenzierte Provider **muss** `enabled: true` sein
- ⚠️ Die Environment Variable **muss** gesetzt sein

## Verwendung

### Golden Standard generieren

Es gibt zwei Methoden, um den Golden Standard zu generieren:

#### 1. Smart Update (Empfohlen)

Generiert nur fehlende Golden Standards. Bereits existierende Ergebnisse werden beibehalten. Ideal für den täglichen Gebrauch oder wenn neue Module hinzugefügt wurden.

```bash
make generate-golden
```

#### 2. Force Update (Neu generieren)

Erzwingt eine komplette Neugenerierung aller Golden Standards. Überschreibt existierende Ergebnisse. Nutzen Sie dies, wenn sich Prompts geändert haben oder das Referenz-Modell aktualisiert wurde.

```bash
make generate-golden-new
```

### Automatische Synchronisierung

Wenn Sie einen normalen kommerziellen Benchmark ausführen (`make benchmark-commercial`) und dabei das Modell wählen, das als Golden Standard definiert ist (z.B. `mistral-large`), werden die Ergebnisse **automatisch** in den Golden Standard übernommen.

### Validierung

Das System validiert automatisch vor jedem Benchmark:

```python
from utils.config_validator import validate_config_quick

if validate_config_quick():
    # Golden Standard ist korrekt konfiguriert
    run_benchmark()
```

**Output bei korrekter Konfiguration:**
```
✅ Golden Standard Provider: Mistral AI
   API Key: MISTRAL_API_KEY... ✓
   Modelle: Mistral Large (123B), Mistral Medium
```

**Output bei Fehler:**
```
❌ Golden Standard Provider 'Mistral AI' nicht konfiguriert:
   Environment Variable 'MISTRAL_API_KEY' ist nicht gesetzt!
   Setze: export MISTRAL_API_KEY='your-api-key'
```

### Lokale Benchmarks mit Golden Standard

Wenn der Golden Standard verfügbar ist, werden lokale Modelle automatisch damit verglichen:

```bash
make benchmark
# → Wähle lokales Modell
# → System lädt Golden Standard Referenzwerte
# → Vergleicht Performance automatisch
```

**Output:**
```
📌 Golden Standard Scores geladen: 5 Assets
   Referenz-Modell: mistral-large-latest (mistral)
   Beispiel-Scores: 97, 80, 75 Punkte...

📊 Lokales Modell: ministral-3:8b
   Asset 001: 75/100 (77% von Golden Standard)
   Asset 002: 62/100 (77% von Golden Standard)
```

## Mehrere Provider testen

Du kannst **mehrere Provider** aktivieren, aber nur **einer** ist der Golden Standard:

```yaml
mistral:
  golden_standard: true   # 🏆 Referenz
  enabled: true

anthropic:
  golden_standard: false  # ✅ Zum Testen
  enabled: true

openai:
  golden_standard: false  # ✅ Zum Testen
  enabled: true
```

**Workflow:**
1. Mistral als Golden Standard → Generiert Referenz-CSV
2. Anthropic/OpenAI testen → Zusätzliche CSV-Dateien
3. Lokale Modelle → Vergleichen mit Mistral (Golden Standard)

## Programmatische Nutzung

### Golden Standard Provider abrufen

```python
from utils.config_validator import ConfigValidator

validator = ConfigValidator()

# Golden Standard Provider finden
provider_key, provider_config = validator.get_golden_standard_provider()
print(f"Golden Standard: {provider_config['name']}")
# → Golden Standard: Mistral AI

# Validieren
is_valid, message = validator.validate_golden_standard()
if not is_valid:
    print(f"Fehler: {message}")
    exit(1)
```

### Alle aktivierten Provider

```python
providers = validator.get_enabled_commercial_providers()

for key, config in providers.items():
    is_golden = config.get('golden_standard', False)
    marker = '🏆 ' if is_golden else '   '
    print(f"{marker}{config['name']}")
```

Output:
```
🏆 Mistral AI
   Anthropic
   OpenAI
```

## Fehlerbehebung

### Problem: "Kein Golden Standard Provider konfiguriert"

**Lösung:** Setze bei **genau einem** Provider `golden_standard: true`

### Problem: "Mehrere Provider als Golden Standard markiert"

**Lösung:** Nur **ein** Provider darf `golden_standard: true` haben. Setze bei anderen auf `false`.

### Problem: "Golden Standard Provider ist deaktiviert"

**Lösung:** Der Golden Standard muss `enabled: true` haben.

### Problem: "Environment Variable nicht gesetzt"

**Lösung:**
```bash
# Prüfe welche Variable benötigt wird
grep env_var benchmark_config.yaml

# Setze sie
export MISTRAL_API_KEY="your-key"

# Persistent machen (optional)
echo 'export MISTRAL_API_KEY="your-key"' >> ~/.zshrc
```

## Best Practices

### 1. Wähle stabilen Golden Standard

- ✅ **Mistral Large** - Konsistent, gute Performance
- ✅ **Claude 3.5 Sonnet** - State of the Art
- ⚠️ Vermeide häufigen Wechsel (historische Vergleichbarkeit)

### 2. Generiere Golden Standard zuerst

```bash
# 1. Erst Golden Standard
python scripts/run_commercial_benchmark.py

# 2. Dann lokale Modelle
make benchmark
```

### 3. Dokumentiere Golden Standard Version

Speichere Metadaten im CSV:
- Datum der Generierung
- Modell-Version (z.B. `mistral-large-latest` am 2025-12-27)
- Durchschnittlicher Score

### 4. Regelmäßige Re-Generierung

Modelle verbessern sich → Re-benchmarke Golden Standard:
- Nach Provider-Updates
- Bei neuen Test-Assets
- Quartalsweise für Konsistenz

## Beispiel-Workflow

```bash
# 1️⃣ Konfiguration
vim benchmark_config.yaml
# → Mistral: golden_standard: true
# → Anthropic: golden_standard: false

# 2️⃣ API Keys setzen
export MISTRAL_API_KEY="..."
export ANTHROPIC_API_KEY="..."

# 3️⃣ Golden Standard generieren
python scripts/run_commercial_benchmark.py
# → Wähle Mistral Large
# → Ergebnis: commercial_models_benchmark.csv

# 4️⃣ Andere Provider testen (optional)
python scripts/run_commercial_benchmark.py
# → Wähle Claude 3.5 Sonnet
# → Ergebnis: anthropic_benchmark.csv

# 5️⃣ Lokale Modelle benchmarken
make benchmark
# → System nutzt Mistral als Referenz automatisch
```

## Technische Details

### ConfigValidator API

```python
class ConfigValidator:
    def get_golden_standard_provider() -> Tuple[str, Dict]:
        """Gibt (key, config) des Golden Standard Providers zurück."""
    
    def validate_golden_standard() -> Tuple[bool, str]:
        """Validiert Golden Standard. Returns (is_valid, message)."""
    
    def get_enabled_commercial_providers() -> Dict[str, Dict]:
        """Alle aktivierten kommerziellen Provider."""
    
    def get_golden_standard_csv() -> Path:
        """Pfad zur Golden Standard CSV-Datei."""
```

### Integration in Benchmark Runner

```python
from utils.config_validator import ConfigValidator

runner = LocalBenchmarkRunner()

# Validierung beim Start
is_valid, message = runner.validator.validate_golden_standard()
print(message)

if not is_valid:
    print("⚠️  Golden Standard nicht verfügbar")
    # Benchmark läuft trotzdem, nur ohne Referenz-Vergleich
```

## Versionierung

- **v0.1.0-alpha**: Initial implementation
  - Einzelner Golden Standard Provider
  - API Key Validierung
  - Automatische Referenz-Erkennung

**Geplant für v0.2.0:**
- Multi-Golden-Standard (z.B. verschiedene Standards für verschiedene Module)
- Historische Golden Standard Versionen
- Automatisches Update-Tracking

## Scoring Methodik & Performance Ratio

### Performance Ratio (Normalisierung)
Um faire Vergleiche zwischen Modellen mit unterschiedlicher Anzahl absolvierter Tests (Runs) zu ermöglichen, nutzt das Leaderboard die **Performance Ratio**.

*   **Formel**: `((Modell Score - Baseline) / (Referenz Score - Baseline)) * 100` (Baseline = 0)
*   **Interpretation**:
    *   **100%**: Leistung identisch mit kommerziellem Referenz-Modell.
    *   **>100%**: Übertrifft die Referenz in den getesteten Disziplinen.
    *   **<100%**: Unterhalb der Referenz.
*   **Vorteil**: Verhindert, dass spezialisierte Modelle bestraft werden, nur weil sie (noch) nicht alle Module absolviert haben. Ein Modell mit 5/29 Tests kann eine Ratio von 99% haben, während ein anderes Modell mit 29/29 Tests vielleicht nur 96% im Durchschnitt erreicht.

### Gap Calculation & Fairness
*   **Percentage Gap**: Abweichungen werden als prozentuale Differenz berechnet (`(Score - Ref) / Ref`), nicht als absolute Punktwerte.
*   **Hybrid Scoring**: Eine Kombination aus striktem Keyword-Matching und semantischem Fallback (Threshold 0.35) stellt sicher, dass auch kleinere Modelle nicht unfair abgestraft werden, wenn sie richtige Konzepte mit synonymen Begriffen ausdrücken.

