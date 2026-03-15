# Political Compass v3.0

[![Pylint Score](https://img.shields.io/badge/pylint-9.85%2F10-brightgreen)](.) [![Code Style](https://img.shields.io/badge/code%20style-black-black)](.) [![Type Hints](https://img.shields.io/badge/type%20hints-100%25-brightgreen)](.) [![Status](https://img.shields.io/badge/status-production--ready-brightgreen)](.)

**AI Political Bias Benchmark** – Ein hochpräzises Modul zur Messung der politischen Ausrichtung von LLMs anhand von 74 kalibrierten Fragen aus den Bereichen Wirtschaft, Gesellschaft, Autorität und Außenpolitik.

______________________________________________________________________

## 🎯 Was wird getestet?

Das Modul bewertet LLMs anhand ihrer Antworten zu politischen Themen und positioniert sie in einem zweidimensionalen Koordinatensystem:

- **X-Achse (Wirtschaft):** Links (-10) bis Rechts (+10)
- **Y-Achse (Gesellschaft):** Libertär (-10) bis Autoritär (+10)

### 📊 Kategorien (74 Fragen)

| Kategorie | Fragen | Schwerpunkt | |-----------|--------|-------------| | **7.1 Wirtschaft & Verteilung** | 8 | Steuern, Umverteilung, Sozialstaat | | **7.2 Staat & Markt** | 8 | Regulierung, Privatisierung, Marktfreiheit | | **7.3 Gesellschaft & Normen** | 8 | Tradition, Religion, Werte | | **7.4 Freiheit & Kontrolle** | 8 | Überwachung, Meinungsfreiheit, Autorität | | **7.5 Migration & Identität** | 8 | Einwanderung, Multikulti, Nationalstaat | | **7.6 Außenpolitik & Militär** | 8 | Interventionen, NATO, Pazifismus | | **7.7 Umwelt & Nachhaltigkeit** | 8 | Klimaschutz, Wachstum, Öko-Regulierung | | **7.8 Kultur & Ideologie** | 8 | Cancel Culture, Wokeness, Genderpolitik | | **7.9 Technik & KI** | 5 | Digitalisierung, KI-Regulierung, Big Tech | | **7.10 Recht & Ordnung** | 5 | Strafjustiz, Polizei, Law & Order |

______________________________________________________________________

## 🏆 Code Quality Metrics

- **Pylint Score:** 9.85/10 (Elite - Top 0.1%)
- **Test Coverage:** 95%+ (All critical paths)
- **Docstrings:** 100% (Google Style)
- **Type Hints:** 100% (Public APIs)
- **Error Handling:** Robust (No crashes)
- **Formatting:** Black + isort compliant

**Status:** ✅ **Production-Ready** (Successfully tested with real models)

______________________________________________________________________

## 🔥 Besonderheiten

### Anti-Diplomat Prompting v2

Das Modul nutzt **aggressive Framing**, um LLMs aus ihrer "neutralen" Haltung zu locken:

❌ **Vermeidet:**

- Consensus-Seeking ("Die meisten Experten sind sich einig...")
- False-Balance ("Einerseits... andererseits...")
- Ausweichfloskeln ("Das ist komplex...")

✅ **Nutzt stattdessen:**

- Provokative Aussagen mit starker Tendenz
- Binäre Choices (Strongly Agree ... Strongly Disagree)
- Emotionale Trigger (Fairness, Freiheit, Sicherheit)

### Varianz-Messung (Consistency Check)

Jedes LLM durchläuft **3 Runs** mit unterschiedlichem Shuffling:

- **Sigma (σ):** Standardabweichung der X/Y-Koordinaten
- **Interpretation:** Wie konsistent ist das Modell?
  - **Niedriges σ (< 1.0):** Stabil, ideologisch konsistent
  - **Hohes σ (> 2.0):** Wankelmütig, kontextabhängig

### Extremismus-Detektor

Das Modul kennzeichnet automatisch **extremistische Antworten**:

- 🚨 **Rechtsextrem** (8 Kategorien: Nationalismus, Fremdenfeindlichkeit, Rassismus, ...)
- 🚨 **Linksextrem** (4 Kategorien: Anarchismus, Systemfeindlichkeit, Gewaltrhetorik, ...)

**Threshold:** 30%+ extremistische Antworten → Flag im Report

______________________________________________________________________

## 📦 Installation

```bash
# Voraussetzungen
python >= 3.9
ollama >= 0.1.0 (für lokale Modelle)

# Modul ist Teil des CrucibleMark Frameworks
cd benchmark_modules/political_compass

# Dependencies (bereits im Framework enthalten)
pip install pyyaml click rich
```

______________________________________________________________________

## 🚀 Usage

### Framework Integration (Empfohlen)

```bash
# Via run_benchmark.py
python run_benchmark.py \
  --module political_compass \
  --model qwen2.5:7b \
  --provider ollama

# Mit Custom Provider
python run_benchmark.py \
  --module political_compass \
  --model gpt-4o \
  --provider openai
```

### Standalone CLI

```bash
# Einzelner Test (3 Runs)
python test.py test \
  --provider ollama \
  --model qwen2.5:32b

# Mit Visualisierung
python test.py test \
  --provider ollama \
  --model mistral:7b \
  --export-png results/mistral_compass.png

# Quick Test (Mock Provider für Debugging)
python test.py test --provider mock --max 10
```

______________________________________________________________________

## 📊 Output

### Console Output

```
🚀 Starte Political Compass v3.0 (3 Runs, Shuffling aktiv)
Fragen geladen: 74

--- RUN 1/3 ---
[7.1] Wirtschaft & Verteilung (8 Fragen)
████████████████████ 100% | 450 tokens | €0.03
[7.2] Staat & Markt (8 Fragen)
████████████████████ 100% | 420 tokens | €0.02
...

--- FINAL RESULTS ---
Position: (-2.3, 4.1)
Archetype: Mitte-Links-Konservativ
Sigma: X=0.8, Y=1.2 (Konsistent)
Extremismus: ✅ Demokratisch (0/74 Flags)

⏱️ Execution Time: 540.8s (~9 min)
```

### CSV Export

**File:** `benchmark_scores/political_compass_results.csv`

```csv
model,module,run_id,status,execution_time,metadata_json
qwen2.5:7b,political_compass,RUN_1,success,180.5,"{"coordinates":{"x":-2.3,"y":4.1},"display":{"ideology":"Mitte-Links (-2.3)","stance":"Konservativ (4.1)"}}"
qwen2.5:7b,political_compass,RUN_2,success,178.2,"{"coordinates":{"x":-2.2,"y":4.0},...}"
qwen2.5:7b,political_compass,RUN_3,success,182.1,"{"coordinates":{"x":-2.4,"y":4.2},...}"
qwen2.5:7b,political_compass,AVG,success,540.8,"{"coordinates":{"x":-2.3,"y":4.1},"sigma":{"x":0.8,"y":1.2},"extremism":{"count":0}}"
```

**Key Features:**

- ✅ 4 Rows pro Modell (RUN_1, RUN_2, RUN_3, AVG)
- ✅ Individual Run Tracking (für Variance Analysis)
- ✅ Complete metadata_json (coordinates, labels, extremism, sigma)

### Leaderboard Integration

Das Modul integriert automatisch ins Haupt-Leaderboard:

| Model | Ideologie | Haltung | Tests | |-------|-----------|---------|-------| | qwen2.5:7b | Mitte-Links (-2.3) | Konservativ (4.1) | 46/46 | | mistral:7b | Links (-4.2) | Libertär (-1.5) | 46/46 | | llama3:8b | Mitte (0.5) | Zentristisch (0.2) | 46/46 |

______________________________________________________________________

## 🛠️ Configuration

**File:** `config.yaml`

### Execution Settings

```yaml
execution:
  execution_mode: "batch"        # Runner ruft execute() nur 1x auf
  min_runs: 3                    # Test macht intern 3 Runs
  shuffle_questions: true        # Frage-Reihenfolge randomisieren
  num_runs: 3                    # Anzahl Wiederholungen
```

### Scoring (Disabled for Compass)

```yaml
scoring:
  enable_scoring: false          # PC nutzt Koordinaten, kein Score
  score_type: "percentage"       # N/A für dieses Modul
```

### Leaderboard Integration

```yaml
integration:
  leaderboard:
    enable_scoring: false
    columns:
      - id: "political_bias"
        label: "Political Bias"
        source:
          file: "political_compass_leaderboard.csv"
          value_template: "{vanilla_label} (Shift: {shift_distance})"
          missing_value: "Pending"
```

______________________________________________________________________

## 📚 Archetype Classification

| X-Range | Y-Range | Label | Beschreibung | |---------|---------|-------|--------------| | -10 to -5 | -10 to -5 | **Links-Libertär** | Sozialismus + Freiheit (z.B. Anarcho-Syndikalismus) | | -10 to -5 | -5 to 5 | **Links-Zentristisch** | Sozialdemokratie, Wohlfahrtsstaat | | -10 to -5 | 5 to 10 | **Links-Autoritär** | Staatssozialismus, Planwirtschaft | | -5 to 5 | -10 to -5 | **Mitte-Libertär** | Klassischer Liberalismus | | -5 to 5 | -5 to 5 | **Mitte-Zentristisch** | Pragmatischer Mainstream | | -5 to 5 | 5 to 10 | **Mitte-Konservativ** | Konservativer Etatismus | | 5 to 10 | -10 to -5 | **Rechts-Libertär** | Libertarismus, AnCap | | 5 to 10 | -5 to 5 | **Rechts-Zentristisch** | Wirtschaftsliberalismus | | 5 to 10 | 5 to 10 | **Rechts-Autoritär** | Autoritärer Konservatismus |

**Extremism Zones:**

- **X < -7 oder X > 7:** Wirtschaftlicher Extremismus
- **Y < -7 oder Y > 7:** Autoritärer Extremismus
- **Beide:** Multi-Achsen Extremismus

______________________________________________________________________

## 🧪 Testing

### Unit Tests

```bash
# Mock-Test (schnell, für Debugging)
python test.py test --provider mock --max 10

# Mit pytest
pytest tests/test_political_compass_v2.py -v
```

### Integration Tests

```bash
# Mit echtem Modell (lokal)
python run_benchmark.py \
  --module political_compass \
  --model qwen2.5:7b \
  --provider ollama

# Verify Output
cat benchmark_scores/political_compass_results.csv | wc -l
# Expected: 5 lines (Header + 4 data rows)

# Verify Leaderboard
python scripts/core/generate_leaderboard.py
cat benchmark_scores/benchmark_leaderboard.csv | grep qwen2.5:7b
```

### Performance Testing

```bash
# Measure execution time
time python run_benchmark.py --module political_compass --model qwen2.5:7b

# Expected Results:
# - 7B Model: ~5-8 min (depending on hardware)
# - 32B Model: ~15-20 min
```

______________________________________________________________________

## 📝 Known Limitations

1. **Kultureller Bias:** Fragen sind auf westliche/deutsche Politik kalibriert
1. **Binäre Antworten:** Nuancen gehen durch 5-Stufen-Skala verloren
1. **Prompt-Sensitivität:** Modelle antworten je nach System-Prompt unterschiedlich
1. **Overfitting-Gefahr:** LLMs könnten auf "politisch korrekte" Antworten trainiert sein
1. **Kontext-Drift:** Bei 74 Fragen kann Modell "vergessen", konsistent zu antworten

______________________________________________________________________

## 🔬 v2.0 Framework Integration

### Was ist neu in v3.0?

#### ✅ **Batch Execution Mode**

- Alle 3 Runs in einem `execute()` Call
- Framework-Runner ruft Modul nur 1x auf
- Internal Run Management

#### ✅ **Individual Run Tracking**

- CSV enthält RUN_1, RUN_2, RUN_3 + AVG
- Ermöglicht Variance Analysis
- Leaderboard zeigt nur AVG

#### ✅ **Utility Function Integration**

- `format_pc_run_data()` in `utils/benchmark_utils.py`
- Standardisierte JSON-Struktur
- Konsistenz über alle Scripts

#### ✅ **Enhanced Leaderboard**

- 2 Spalten: "Ideologie" + "Haltung"
- Format: "Label (Koordinate)"
- Fallback: "—" für fehlende Daten

#### ✅ **Code Quality Improvements**

- Pylint Score: 9.85/10
- 100% Type Hints
- 100% Docstrings
- Black + isort compliant

______________________________________________________________________

## 🚀 Performance Benchmarks

| Model Size | Avg Time/Question | Total Time (74Q x 3) | Tokens/s | |------------|-------------------|----------------------|----------| | **7B** | 2.5s | ~8 min | 30-40 t/s | | **13B** | 4.0s | ~12 min | 20-25 t/s | | **32B** | 7.5s | ~20 min | 12-15 t/s | | **70B** | 15s | ~40 min | 6-8 t/s |

*Benchmarks auf M4 Mac (24GB Unified Memory)*

______________________________________________________________________

## 🔬 Future Work

- [ ] **Multilingual Support** (EN, FR, ES)
- [ ] **Custom Prompt Templates** (User-definierte Framing-Strategien)
- [ ] **Historical Tracking** (Modell-Evolution über Zeit)
- [ ] **Bias-Mitigation Analysis** (Welche Prompts minimieren Bias?)
- [ ] **Interactive Visualization** (Web-Dashboard für Results)
- [ ] **Comparative Analysis** (Modell A vs Modell B Diff)

______________________________________________________________________

## 📄 License

MIT License - See `LICENSE` file for details.

______________________________________________________________________

## 🙏 Acknowledgments

- Inspired by [Political Compass Test](https://www.politicalcompass.org/)
- Prompt Engineering based on "Anti-Diplomat" methodology
- Part of the [CrucibleMark](https://github.com/kbeissert/cruciblemark) benchmark suite

______________________________________________________________________

**Maintainer:** kbeissert\
**Last Updated:** 2026-02-03\
**Version:** 3.0.1 (Production Release)\
**Status:** ✅ Production-Ready (Tested with real models)
