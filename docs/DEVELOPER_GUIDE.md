# Entwicklerhandbuch: CrucibleMark erweitern

**Zielgruppe:** Entwickler, die neue Test-Module erstellen oder das Scoring-System erweitern wollen.

**Inhalt:**

- Quick Start: Neues Modul in 15 Minuten
- Asset-Format & YAML-Schema
- Scoring-Logik implementieren
- CSV-Output & Leaderboard-Integration
- Tests & Validierung

> **Voraussetzung:** Grundkenntnisse in Python, YAML und Regex.

---

## 🛑 WICHTIG: Die 4 Design-Gesetze von CrucibleMark

Vor dem Schreiben eines neuen Moduls oder dem Erweitern von bestehendem Code **müssen** die obersten Architekturregeln dieses Projekts respektiert werden:

1. **Strict Separation of Concerns:** Die Datenmessung (Benchmark Loop) ist heilig, autark und darf NIEMALS durch Publishing-Funktionen blockiert werden.
2. **SSOT & DRY:** Jede Funktion hat **genau ein** Modul. Kein Code-Kopieren! Erweitere existierende Module (Open/Closed Principle).
3. **No Magic Numbers:** Alles läuft über YAML (Config-First). Keine hardkodierten Parameter im Code.
4. **Anti-God-Script:** Schütze das System vor monolithischen Skripten. Nutze gezielte Submodul-Breakouts.

> 📖 **Details zu diesen Regeln:** [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Quick Start: Neues Modul erstellen

### Option 1: Generator (empfohlen)

```bash
make create-module
```

**Der Wizard fragt:**

1. Modul-ID (z. B. `api_design`)
2. Score Group (`routine`, `reasoning`, `info`)
3. Anzeigename (z. B. "API Design Review")

**Output:**

- Vollständige Ordnerstruktur
- Template `test.py` mit Basis-Code
- `config.yaml` vorkonfiguriert
- Dummy-Assets zum Testen

**Zeit:** ca. zwei Minuten bis zum ersten Test-Run

---

### Development Loop & Testing

Für schnelle Iterationen ohne lange Wartezeiten den **Dev-Modus** nutzen:

```bash
# Startet Benchmark mit verkürzten Pausen (5-10s statt 20-30s)
make benchmark-dev
```

Oder direkt über das CLI:

```bash
python run_benchmark.py --dev --model ministral:8b
```

**Adaptive Pausen:**
Das Framework nutzt `utils/adaptive_pause.py` für dynamische Erholungspausen (wichtig für Mac M-Chips mit Unified Memory). Im Dev-Modus sind diese Pausen kürzer – das kann Performance-Messungen leicht verfälschen, reduziert aber die Entwicklungszeit erheblich.

---

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

---

## Modul-Anatomie

### Verzeichnis-Struktur

```text
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

---

## Reasoning-Modelle: Reasoning-Erkennung & Card-First Workflow

CrucibleMark erkennt ab v3.5.8 Reasoning-Modelle empirisch statt rein heuristisch. Diese Erkennung bestimmt das Token-Budget, die LLM-Judge-Bewertung und die Audit-Log-Ausgabe.

### Wann wird der Probe ausgelöst?

`_ensure_model_card()` in `scripts/core/unified_runner.py` wird **vor dem ersten Run** eines Modells aufgerufen:

```
┌────────────────────────────────────────────────────────┐
│ Card vorhanden + thinking_probe_detected feld          │
│ → Skip (kein API-Call)                                 │
├────────────────────────────────────────────────────────┤
│ Card vorhanden, aber Feld fehlt                        │
│ → Probe → Feld in bestehende Card schreiben            │
├────────────────────────────────────────────────────────┤
│ Keine Card                                             │
│ → Probe → Minimal-Card erstellen (card_status: minimal)│
├────────────────────────────────────────────────────────┤
│ Probe-Fehler (429 / 403 / sonstiger API-Fehler)        │
│ → ⚠️ Clean Warning, Modell in _probed_models (kein    │
│   Retry), Benchmark läuft weiter                       │
└────────────────────────────────────────────────────────┘
```

### Signale der Reasoning-Erkennung (ThinkingProbe)

`probe_thinking_model(model_id, provider_key, config)` in `utils/model_utils.py` schickt einen deterministischen Reasoning-Prompt (Zugproblem) und wertet aus:

| Signal | Kriterium | Konfidenz |
|--------|-----------|-----------|
| A | `<think>` / `<thinking>` / `<thought>`-Tags im Response | `high` |
| B | `reasoning_tokens > 0` in API-Metadaten | `medium` |

> **Signal C (Response-Länge) existiert nicht** — Instruction-Following-Modelle produzieren auf Reasoning-Prompts ebenfalls lange Antworten. Response-Länge darf nicht als CoT-Indikator verwendet werden.

Das Ergebnis landet als JSON in `benchmark_scores/model_cards/<model_id>.json`:

```json
{
  "thinking_probe_detected": true,
  "thinking_probe_evidence": "Signal A: <think> tags detected in response body",
  "thinking_probe_confidence": "high",
  "thinking_probe_manual_override": false
}
```

### `is_reasoning_model()` Lookup-Hierarchie

Die Funktion in `utils/model_utils.py` verwendet immer zuerst die Card:

```
1. is_reasoning_model_from_card(model_id)
   ├── Card + Feld vorhanden → Feldwert zurückgeben
   └── Fehlt Card oder Feld → None (kein False-Positive)

2. String-Trigger-Heuristik (Fallback)
   └── deepseek-r1, reasoning, phi4, qwq, o1, o3,
       magistral, glm-5, minimax-m2, gemini-2.5, kimi-k2
```

### Retroaktiver Probe (CLI)

Für bereits laufende Benchmark-Setups ohne Card-Felder:

```bash
# Einzelnes Modell
make probe-thinking MODEL=gemini-2.5-flash

# Alle Cards ohne thinking_probe_detected-Feld
make probe-all-thinking

# Direkter CLI-Aufruf mit Provider-Override
.venv/bin/python scripts/tools/probe_thinking.py --model <model-id> --provider openrouter
```

`scripts/tools/probe_thinking.py` unterstützt zusätzlich `--missing` (Batch: nur Cards ohne Feld) und `--all` (Force-Rescan aller Cards).

### Sonderfall: OpenAI o-Series (manueller Override)

o1, o3-mini, o4-mini verbergen Reasoning-Tokens intern. Die API liefert keine `<think>`-Tags und keine `reasoning_tokens`. Der Probe gibt `detected=False` zurück — fälschlicherweise.

Für diese Modelle wird die Card **manuell** gesetzt:

```bash
# benchmark_scores/model_cards/o1.json bearbeiten:
{
  "thinking_probe_detected": true,
  "thinking_probe_manual_override": true
}
```

**Neue Modelle ergänzen:** Wenn ein Anbieter Reasoning intern verbirgt, immer beide Felder manuell eintragen und `make probe-thinking MODEL=<id>` nicht als Quelle verwenden.

---

## Modell-IDs, Card-Benennung & Versionierung

Dieser Abschnitt beschreibt das vollständige System: von der Konfiguration einer Modell-ID bis zur gespeicherten Model Card und dem Leaderboard-Eintrag.

---

### Konzept: Was ist eine Modell-ID?

Die **Modell-ID** ist die kanonische Kennung eines Modells — die genaue Zeichenfolge, die in der API-Anfrage verwendet wird. Sie ist die einzige Quelle der Wahrheit für:

- den **Dateinamen der Model Card** (`benchmark_scores/model_cards/`) — bei `-latest`-Aliases mit bekannter Version weicht der Dateiname vom Alias ab (z. B. `mistral-large-latest` → `mistral-large-3.json`); `model_id` *in der Card* bleibt immer der API-Alias
- die **CSV-Spalte `model`** in allen drei Benchmark-CSVs
- den **Lookup** von Versionsinformationen und Reasoning-Flags

**SSoT:** `benchmark_config.yaml` → `providers.<section>.<provider>.models[].id`

#### Pinned IDs vs. Floating Aliases

| Typ | Beispiel | Risiko |
|---|---|---|
| **Pinned (Checkpoint-Slug)** | `moonshotai/kimi-k2-0711` | Kein Risiko — Modell ändert sich nie |
| **Floating Alias** | `mistral-large-latest` | Provider kann Silent Update durchführen — Card wird unter versionsspezifischem Namen gespeichert |

**Regel:** Wo ein Provider versionierte Slugs anbietet (typisch für OpenRouter: `model-YYYYMMDD`), **müssen** diese verwendet werden. Für Provider, die keine Versionskennung mitliefern (Anthropic, OpenAI, Google, Mistral Direct-API, Groq), ist die Floating-Alias-ID der korrekte Eintrag in Config und CSV — die Card hingegen wird unter `{base}-{version}.json` gespeichert, sobald die Version bekannt ist. Ist die Version (noch) nicht bekannt, bleibt der Alias als Dateiname (`codestral-latest.json`). Solange der Alias nicht von anderen Providern genutzt wird, entsteht keine Kollision.

---

### Vom Config-Eintrag zur Card-Datei: Vier Naming-Regeln

Die Funktion `_card_path(model_id, provider, *, for_write, resolved_version)` in `utils/model_utils.py` ist die einzige Stelle, die den Dateinamen einer Model Card berechnet. Sie implementiert vier Regeln — Regel 4 hat die höchste Priorität und wird vor allen anderen geprüft:

#### Regel 4 (höchste Priorität): `-latest`-Aliases → versionsspezifischer Dateiname

**Problem:** Floating Aliases wie `mistral-large-latest` sind *volatile* — derselbe Alias zeigt nach einem Provider-Update auf eine neue Modellversion. Eine Card unter dem Alias-Namen würde veraltete Metadaten für das neue Modell liefern (falsche Reasoning-Flags, falsche Kategorisierung).

**Lösung:** Ist die konkrete Modellversion bekannt (`resolved_version` ≠ stale), setzt sich der Dateiname aus Basis-Name + Version zusammen:

```
mistral-large-latest  + version="3"    →   mistral-large-3.json
mistral-medium-latest + version="2312" →   mistral-medium-2312.json
mistral-small-latest  + version="3"    →   mistral-small-3.json
codestral-latest      + version=stale  →   codestral-latest.json   (Fallback auf Regel 2)
```

**Stale-Versionen** (deaktivieren Regel 4): `"latest"`, `"unknown"`, `"k.A."`, `""`.

**Wichtig:** Die `model_id` *in der Card* bleibt immer der API-Alias — sie wird für API-Calls und CSV-Lookups verwendet. Nur der Dateiname ist versionsspezifisch.

Angewendet auf: alle Modell-IDs die auf `-latest` oder `:latest` enden, wenn `get_model_version()` einen nicht-stalen Wert liefert.

---

#### Regel 1: Namespaced IDs (enthalten `/`)

Der Provider-Namespace ist bereits in der ID eingebettet. Kein Prefix nötig.

```
moonshotai/kimi-k2-0711   →   moonshotai_kimi-k2-0711.json
z-ai/glm-5.1-20260406     →   z-ai_glm-5_1-20260406.json
qwen/qwen3-32b            →   qwen_qwen3-32b.json
meta-llama/llama-4-scout-17b-16e-instruct  →  meta-llama_llama-4-scout-17b-16e-instruct.json
```

Angewendet auf: OpenRouter-Modelle, namespaced Groq-Modelle, alle Modelle mit `/` in der ID.

#### Regel 2: Direkte API-Provider (`API`-Shortcode)

Proprietäre Modellnamen sind global eindeutig. Kein Prefix nötig.

```
claude-sonnet-4-6          →   claude-sonnet-4-6.json
gpt-5                      →   gpt-5.json
gemini-2.5-pro             →   gemini-2_5-pro.json
codestral-latest           →   codestral-latest.json   (version unbekannt → Alias bleibt)
grok-3-mini                →   grok-3-mini.json
```

Angewendet auf: `anthropic`, `openai`, `google`, `xai`, `mistral` (alle mit Shortcode `API`) — sofern nicht Regel 4 greift (bekannte Version bei `-latest`-Alias).

#### Regel 3: Nicht-namespaced + nicht-API → Provider-Prefix

**Problem:** Die gleiche bare ID (`llama3.3:70b`) kann sowohl via Ollama als auch via Groq laufen. Ohne Prefix würden sich beide Cards gegenseitig überschreiben — ein **Ghost-Benchmark**: Die Card des einen Providers wird fälschlich für den anderen verwendet, Reasoning-Flags und size_class sind falsch.

**Lösung:** Prefix mit Provider-Shortcode.

```
# via ollama_local (Shortcode: LCL)
llama3.3:70b         →   LCL_llama3_3_70b.json

# via groq (Shortcode: GR), nicht-namespaced
llama-3.3-70b-versatile  →   GR_llama-3_3-70b-versatile.json
```

**Backward-Compat:** Bestehende Cards ohne Prefix (vor dieser Konvention angelegt) werden beim Read-Lookup als Fallback gefunden — `_card_path(for_write=False)` versucht zuerst `LCL_*`, fällt dann auf die unpräfixierte Datei zurück. Beim Schreiben (`for_write=True`) wird immer der präfixierte Pfad verwendet.

#### Entscheidungsbaum

```
model_id  +  resolved_version
   │
   ├── -latest/‌:latest Alias + resolved_version ≠ stale?
   │        └── JA ──► {safe_name(base)}-{version}.json              (Regel 4)
   │
   ├── enthält "/"?  ─── JA ──► safe_name(model_id).json             (Regel 1)
   │
   └── NEIN
         │
         ├── Provider-Shortcode == "API"?  ─── JA ──► safe_name(model_id).json  (Regel 2)
         │
         └── NEIN (LCL, GR)
               │
               └── for_write=True  ──► {SHORTCODE}_safe_name.json    (Regel 3)
               └── for_write=False ──► Prefixed? → Prefixed-Pfad
                                       Sonst     → Unprefixed (Legacy-Fallback)
```

---

### Helper-Funktionen als SSoT (`utils/model_utils.py`)

Alle Card-Pfadoperationen **müssen** diese Funktionen verwenden. Inline `Path(...) / f"{re.sub(...)}.json"` ist verboten — es würde die Vier-Regeln-Logik umgehen.

```python
from utils.model_utils import _safe_name, _card_path, _find_card, CARD_DIR
```

#### `_safe_name(model_id: str) → str`

Kanonische Dateiname-Transformation. Ersetzt alle Zeichen aus `[:/.\ ]` durch `_`.

```python
_safe_name("gemini-2.5-flash")                 # → "gemini-2_5-flash"
_safe_name("deepseek-r1:8b")                   # → "deepseek-r1_8b"
_safe_name("moonshotai/kimi-k2-0711")          # → "moonshotai_kimi-k2-0711"
_safe_name("z-ai/glm-5.1-20260406")            # → "z-ai_glm-5_1-20260406"

# FALSCH — führt zu Lookup-Miss ohne Fehlermeldung:
"gemini-2.5-flash".replace("/", "_")  # → "gemini-2.5-flash" (Punkt bleibt!)
```

#### `_card_path(model_id, provider=None, *, for_write=False, resolved_version=None) → Path`

Berechnet den vollständigen Pfad der Card-Datei nach den Vier Regeln.

```python
# Regel 4: -latest Alias mit bekannter Version → versionsspezifischer Dateiname
_card_path("mistral-large-latest", "mistral", for_write=True, resolved_version="3")
# → benchmark_scores/model_cards/mistral-large-3.json

# Regel 4: version ist stale → Fallback auf Regel 2 (Alias bleibt)
_card_path("codestral-latest", "mistral", for_write=True, resolved_version="latest")
# → benchmark_scores/model_cards/codestral-latest.json

# Regel 1: Namespaced
_card_path("moonshotai/kimi-k2-0711")
# → benchmark_scores/model_cards/moonshotai_kimi-k2-0711.json

# Regel 2: API-Provider
_card_path("claude-sonnet-4-6", "anthropic")
# → benchmark_scores/model_cards/claude-sonnet-4-6.json

# Regel 3: LCL — Read (Fallback auf Legacy)
_card_path("llama3.3:70b", "ollama_local")
# → benchmark_scores/model_cards/llama3_3_70b.json  (falls kein LCL_* existiert)

# Regel 3: LCL — Write (immer Prefix)
_card_path("llama3.3:70b", "ollama_local", for_write=True)
# → benchmark_scores/model_cards/LCL_llama3_3_70b.json
```

> **Wann `for_write=True`?** Nur beim Anlegen oder Überschreiben einer Card — also im Template-Generator `generate_model_cards.py`. Alle Lookup-Funktionen verwenden `for_write=False` (Default).

#### `_find_card(model_id: str) → Path`

Findet eine bestehende Card ohne Kenntnis des Providers. Nützlich in Utility-Funktionen, die nur die model_id kennen.

```python
# Nicht-namespaced (LCL/GR): LCL_deepseek-r1_8b.json → dann deepseek-r1_8b.json (Legacy)
path = _find_card("deepseek-r1:8b")
if path.exists():
    card = json.loads(path.read_text())

# -latest Alias: Fallback 3 — findet versionsspezifische Card via get_model_version()
path = _find_card("mistral-large-latest")
# → mistral-large-3.json  (wenn get_model_version("mistral-large-latest") == "3")
```

Lookup-Reihenfolge (vier Schritte):
1. **Namespaced IDs** (`/` im model_id) → direkt `safe_name.json`
2. **Prefixed Kandidaten** (`LCL_*`, `GR_*`) — erster existierender Treffer
3. **Unpräfixierter Pfad** (Legacy-Fallback) — existiert evtl. nicht
4. **`-latest` Version-Fallback** — ruft `get_model_version(model_id, provider="api")` auf und sucht `{base}-{version}.json`; Rückfall auf unpräfixierten Pfad wenn version stale

Rückgabewert ist immer ein `Path` — Aufrufer müssen `.exists()` prüfen.

#### `CARD_DIR: Path`

Konstante für das Card-Verzeichnis. Nie als `Path("benchmark_scores/model_cards")` inline schreiben.

```python
CARD_DIR  # → Path("benchmark_scores/model_cards")
```

#### `get_use_case_primary(model_id: str, card_data: dict | None = None) → str`

Liefert `use_case_primary` aus der Card mit Fallback `"generalist"`. Niemals direkt `.get("use_case_primary")` ohne Fallback aufrufen.

```python
get_use_case_primary("qwen2.5vl:7b")          # → "vision-language"
get_use_case_primary("codestral-latest")       # → "coding"
get_use_case_primary("unknown-model")          # → "generalist" (Fallback)
```

---

### Provider-Shortcodes

Shortcodes sind an zwei Stellen synchron gepflegt:

1. **`utils/model_utils.py`** → `_PROVIDER_SHORTCODES: dict[str, str]` + `get_provider_shortcode(provider)`
2. **`benchmark_config.yaml`** → `providers.<section>.<provider>.short_code`

| Shortcode | Bedeutung | Provider-Schlüssel |
|---|---|---|
| `API` | Proprietäre Direkt-API | `anthropic`, `openai`, `google`, `xai`, `mistral` |
| `OR` | OpenRouter (Routing-Layer) | `openrouter` |
| `GR` | Groq (Inferenz-Dienst) | `groq` |
| `LCL` | Lokales Ollama-Modell | `ollama_local`, `ollama`, `local` |

Der Shortcode erscheint im Leaderboard als Suffix der Versionsspalte (`k2/OR`, `4-mini/API`, `4760c3/LCL`).

---

### Versionsermittlung

`get_model_version(model_name, provider, client)` in `utils/model_utils.py` liefert die **nackte Version** — ohne Provider-Suffix. Die Kombination mit dem Shortcode für die Anzeige übernimmt `scripts/leaderboard/exporter.py`.

#### Lookup-Hierarchie (in dieser Reihenfolge)

1. **Card-First:** `model_version`-Feld in der JSON-Card → hat immer Vorrang. Nützlich für manuelle Korrekturen oder Modelle mit ungewöhnlichen ID-Formaten.

2. **Ollama-Hash (nur bei lokalen Providern):** `ollama list` → 7-stelliger Hex-Hash (z.B. `4760c3`). Erkennt Silent Updates sofort am Hash-Wechsel.

3. **Regex/Mapping für kommerzielle APIs:**

   | Familie | Beispiel-ID | Ergebnis |
   |---|---|---|
   | Anthropic | `claude-sonnet-4-6` | `4.6` |
   | Anthropic (datiert) | `claude-haiku-4-5-20251001` | `20251001` |
   | OpenAI | `gpt-4o` | `2024-05-13` |
   | OpenAI o-Serie | `o4-mini` | `4-mini` |
   | Mistral | `mistral-large-latest` | `2411` |
   | Codestral/Magistral | `magistral-medium-latest` | `latest` |
   | Google | `gemini-2.5-pro` | `2.5-pro` |
   | xAI | `grok-3-mini` | `3-mini` |
   | OpenRouter (namespaced) | `moonshotai/kimi-k2-0711` | `k2-0711` |
   | OpenRouter (namespaced) | `z-ai/glm-5.1-20260406` | `5.1-20260406` |
   | OpenRouter (namespaced) | `minimax/minimax-m2.7-20260318` | `m2.7-20260318` |
   | Groq (namespaced) | `qwen/qwen3-32b` | `3-32B` |

4. **Fallback:** `"latest"` wenn kein Muster greift.

---

### Vollständiger Prozess: Von der Config-ID zur Leaderboard-Zeile

```
benchmark_config.yaml
  providers.commercial.openrouter.models[].id = "moonshotai/kimi-k2-0711"
       │
       │  Benchmark-Run
       ▼
cloud_models_benchmark.csv
  model = "moonshotai/kimi-k2-0711"
  version = "k2-0711"          ← get_model_version() → Regex → "k2-0711"
  provider = "openrouter"
       │
       │  make leaderboard
       ▼
benchmark_leaderboard.csv
  Model Name = "Kimi K2 Thinking"       ← display_name aus Model Card
  Version    = "k2-0711/OR"             ← version + "/" + shortcode
       │
       │  _card_path("moonshotai/kimi-k2-0711", "openrouter")
       ▼
benchmark_scores/model_cards/moonshotai_kimi-k2-0711.json
  → Regel 1: namespaced → kein Prefix
  → Dateiname: moonshotai_kimi-k2-0711.json
```

---

### Card-Generierung

`scripts/analysis/generate_model_cards.py` erstellt ein leeres Template für eine neue Model Card — ohne LLM-Call, ohne API-Zugriff. Es ist der Einstiegspunkt für jede neue Modellaufnahme.

```bash
make model-cards MODEL=claude-opus-4-7              # Card-Template anlegen
make model-card  MODEL=qwen3:14b PROVIDER=ollama_local  # mit Provider-Präfix (LCL_*)
make model-cards                                    # interaktive Eingabe
```

1. Berechne `_card_path(model_id, provider_key, for_write=True)` → kanonischer Pfad
2. Falls Datei existiert und `--force` nicht gesetzt → Fehler (kein versehentliches Überschreiben)
3. Template mit allen Pflichtfeldern als `"TODO"`-Platzhalter + automatisch berechnetem `size_class` schreiben
4. `_index.json` neu aufbauen

**Nach der Template-Erstellung:** Alle `"TODO"`-Felder manuell befüllen, dann `card_status` auf `"complete"` setzen. Der Thinking-Probe-Workflow (`make probe-thinking MODEL=...`) ergänzt die `thinking_probe_*`-Felder automatisch vor dem ersten Benchmark-Run.

---

### Historische Daten: Migration

Veraltete `k.A.`-Werte in Benchmark-CSVs können mit dem Migrations-Skript bereinigt werden:

```bash
.venv/bin/python scripts/maintenance/migrate_model_versions.py
```

Das Skript legt `.bak`-Backups aller drei Benchmark-CSVs an und füllt leere / `k.A.`-Versionswerte über `get_model_version()` nach.

---

### Model Card Schema — Pflichtfelder

Jede Model Card JSON muss folgende Felder enthalten. Cards mit `card_status: "draft"` sind manuell erstellte Templates (via `make model-card`) und dürfen `"TODO"`-Platzhalter enthalten. `card_status: "minimal"` kennzeichnet automatisch durch den ThinkingProbe-Hook angelegte Minimal-Cards (nur Probe-Felder befüllt). `card_status: "complete"` signalisiert, dass alle Pflichtfelder befüllt sind.

#### Kern-Identität

| Feld | Typ | Beschreibung |
|---|---|---|
| `model_id` | string | Kanonische API-ID (z. B. `"mistral-large-2411"`, `"hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M"`) — SSoT für alle Lookups |
| `display_name` | string | Anzeigename im Frontend |
| `vendor` | string | API-Anbieter (z. B. `"Mistral AI"`, `"OpenAI"`) |
| `card_status` | string | `"draft"` / `"minimal"` / `"complete"` — steuert Vollständigkeits-Guards |
| `heritage_ids` | list[string] | Frühere Model-IDs / Alias-Namen, unter denen Review-Dirs abgelegt wurden. Web-Exporter fällt bei fehlender primärer Dir auf diese zurück. |

#### Architektur & Deployment

| Feld | Typ | Werte / Format | Beschreibung |
|---|---|---|---|
| `parameter_architecture` | string | `dense` / `moe` | Dense = alle Parameter aktiv; MoE = nur Teilnetzwerke aktiv |
| `params_total_b` | float | z. B. `14.0` | Gesamtparameter in Milliarden |
| `params_active_b` | float | z. B. `3.5` | Aktive Parameter (MoE); bei MoE ist dies der relevante Vergleichswert |
| `context_window_k` | integer | z. B. `128` | Maximales Kontextfenster in Kilotoken |
| `knowledge_cutoff` | string | `YYYY-MM` | Trainingsdaten-Stichtag |
| `size_class` | string | `Nano` / `Edge` / `Desktop` / `Workstation` / `Server` / `Frontier` | Hardware-Tier — abgeleitet aus Parameteranzahl oder API-Only-Status |
| `deployment_type` | string | `api_only` / `local_weights` | Ob das Modell lokal deploybar ist |
| `supports_tool_use` | boolean | `true` / `false` | Function-Calling-Unterstützung |
| `use_case_primary` | string | `generalist` / `coding` / `reasoning` / `vision-language` / `agentic` | Steuert den Reviewer-Bewertungsrahmen |

#### Lizenz & Kategorisierung

| Feld | Typ | Beschreibung |
|---|---|---|
| `weights_license_tier` | string | `proprietary` / `restricted-weights` / `open-weights` — Bestimmt die Kategorie-Anzeige via `get_model_category()` |
| `license` | string | SPDX-ID oder Kurzname (z. B. `"Apache-2.0"`, `"Meta Community License"`) |
| `license_url` | string | URL zur Volllizenz |
| `commercial_use_allowed` | boolean / null | `true` = frei kommerziell nutzbar; `false` = verboten; `null` = skalenabhängig / unklar |
| `weights_provenance_risk_rationale` | string | Begründung für Lizenz-/Herkunftsrisiken (z. B. CNKI-Verbindungen, dual-use) |

#### Pricing (SSoT)

| Feld | Typ | Beschreibung |
|---|---|---|
| `input_price_per_1m` | float | Preis pro 1M Input-Tokens in USD |
| `output_price_per_1m` | float | Preis pro 1M Output-Tokens in USD |

**Wichtig:** Preise gehören ausschließlich in die Model Card. `cost_limits.yaml` ist Legacy-Fallback für die wenigen Modelle ohne Card — dort nichts Neues eintragen.

#### Thinking Probe

| Feld | Typ | Beschreibung |
|---|---|---|
| `thinking_probe_capable` | boolean | Ob das Modell Chain-of-Thought-Denken zeigt |
| `thinking_probe_evidence` | string | Erklärung der Evidenz (Signal A / B) |
| `thinking_probe_manual_override` | boolean | `true` wenn Wert manuell gesetzt (z. B. OpenAI o-Series ohne `reasoning_tokens`) |
| `thinking_probe_at` | string | ISO-Timestamp des letzten Probe-Runs |

**Signals:** Signal A = `<think>`-Tags in Antwort, Signal B = `reasoning_tokens > 0`. Response-Länge ist kein Signal (ThinkingProbe Signal-C-Verbot, siehe CLAUDE.md).

---

**Taxonomy-SSoT:** Die erlaubten Werte für `use_case_primary` und `size_class` (inkl. `reviewer_guidance` pro Wert) liegen in `config/classification_taxonomy.json`. Dieses File wird von `generate_review.py` beim Start eingelesen und als `{use_case_classification_context}` in den Reviewer-Prompt injiziert.

**Hilfsfunktionen:**
- `get_use_case_primary(model_id, card_data=None)` → `use_case_primary` mit Fallback `"generalist"`
- `get_model_category(model_id, card_data=None)` → **einziger** Einstiegspunkt für Display-Kategorie-Strings; liefert `"Proprietär"` / `"Restricted Weights"` / `"Open Weights"` — niemals selbst ableiten oder hardcoden

### Migration: Neue Card-Felder nachpflegen

Wenn neue Pflichtfelder eingeführt werden, stehen dedizierte Migrationsskripte bereit:

```bash
# use_case_primary in alle bestehenden Cards eintragen
python scripts/dev/migrate_use_case_primary.py --dry-run   # Vorschau
python scripts/dev/migrate_use_case_primary.py             # Ausführen

# context_window_k und knowledge_cutoff nachpflegen
python scripts/dev/migrate_context_fields.py --dry-run
python scripts/dev/migrate_context_fields.py
```

Die Skripte überspringen Cards, die das Feld bereits haben, und geben einen tabellarischen Report aus (Modell | Assigned Value | Basis der Zuweisung).

### Modell vollständig entfernen

`make clean-model MODEL=<id>` (via `scripts/maintenance/clean_results.py`) entfernt seit v3.8.1 alle Spuren eines Modells in einem einzigen Schritt:

- CSV-Zeilen aus allen Benchmark- und PC-CSVs
- `outputs/audit_logs/<dir>/`, `outputs/comparisons/<dir>/`, `outputs/runs/<dir>/`
- `docs/reviews/<dir>/`
- Model Card JSON (`benchmark_scores/model_cards/<card>.json`)
- Political-Compass-Session-Checkpoint (`outputs/temp/session_*.json`)

```bash
make clean-model MODEL="mistral-large-2411"       # Löschen
make clean-model MODEL="mistral-large-2411" DRY=1 # Vorschau
```

Verwaiste Verzeichnisse (kein Leaderboard-Eintrag mehr, aber Dir noch vorhanden) lassen sich mit `make clean-model PRUNE_ORPHANS=1` aufspüren und entfernen.

### SSOT Prinzip (Single Source of Truth)

Die `config.yaml` gliedert sich in **zwei Bereiche**:

#### 1. GLOBAL (Mandatory) – Framework-Contract

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

---

### OUTPUT CONTRACT: BENCHMARK RESULT

---

Jeder Controller (`test.py`) muss ein `BenchmarkResult`-Objekt zurückgeben. Dieses strikt typisierte DTO stellt sicher, dass alle Module kompatible Daten für das Leaderboard liefern.

Das Result Schema (`schemas/result.py`) enthält:

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

`load_time` lässt sich in `execute()` wie folgt befüllen:

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
    status: str = "success"           # success | error | truncated | verbose_outlier | language_mismatch
    primary_score: Optional[float]    # 0.0 - 100.0 (ranking)
    rendered_value: str = "N/A"       # Display string ("85.5 %")

    # Execution Metrics
    execution_time: float             # Seconds
    tokens_used: int                  # Estimated token count
    cost_usd: float                   # Estimated cost
    raw_response: str                 # The full LLM output text

    # Identification
    model_version: str                # Nackte Version, z.B. "4.6", "k2", "latest" (kein Shortcode-Suffix)

    # Deep Data
    data: Dict[str, Any] = {}         # Module-specific details metrics
    meta: Dict[str, Any] = {}         # Context (timestamp, prompt_len)
```

**Warum strikt typisiert?**
Frühere Versionen gaben lose Dictionaries zurück. Das führte zu chaotischen CSV-Spalten (`score` vs. `total_score` vs. `result`). Die `BenchmarkResult`-Klasse erzwingt einen einzigen Standard.

---

#### 2. LOKAL (Optional) – Modul-spezifische Config

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

---

### Execution Modes

| Mode | Verhalten | Use Case |
|------|-----------|----------|
| **`standard`** | Framework lädt Assets einzeln, instanziiert Test pro Asset | Code Quality, UX Writing (isolierte Tests) |
| **`batch`** | Framework übergibt alle Assets, Test kontrolliert Loop | Political Compass (3× Runs), Custom Aggregation |

---

### Kaskadierende Score-Contributions

Das Framework berechnet **Routine Score** und **Reasoning Score** automatisch als Durchschnitt der entsprechenden Module.

1. **Asset-Level** (höchste Priorität):

   ```yaml
   - id: "reasoning_5d_002"
     score_contribution:
       reasoning: 1.0  # Ordnet dieses Asset dem Reasoning Score zu
   ```

2. **Modul-Level** (Standard):
   Definiert in `config.yaml` → `integration` → `default_contribution`.

   - `routine: 1.0` → Zählt zum „Routine Score" (z. B. Documentation, UX)
   - `reasoning: 1.0` → Zählt zum „Reasoning Score" (z. B. Logical Reasoning)

3. **Total Score Berechnung:**

   ```python
   Total Score = (Routine Score + Reasoning Score) / 2
   ```

---

## Asset-Format (YAML-Schema)

### Namenskonvention & Gruppierung (Last-Hyphen-Rule)

Das Framework ermittelt die Anzahl der Tests anhand der Dateinamen im `assets/`-Ordner. Die Logik basiert auf dem **letzten Bindestrich (`-`)**:

- Alles **vor** dem letzten Bindestrich (gefolgt von Ziffern) gilt als **Gruppen-ID**.
- Alles **danach** ist die Variante und zählt nicht separat.

| Dateiname | Erkannte Gruppe | Zählt als... |
|-----------|-----------------|--------------|
| `test_001.yaml` | `test_001` (Ganze Datei) | **1 Test** |
| `pol_axis1-001.yaml` | `pol_axis1` | **1 Test** (zusammen mit -002) |
| `pol_axis1-002.yaml` | `pol_axis1` | (Variante, zählt nicht extra) |

---

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

# Hard Constraints (optional) ─────────────────────────────────────────
# Werden NACH dem inhaltlichen Scoring ausgewertet. Ein Verstoß löst
# eine automatische Penalty aus (unabhängig von der inhaltlichen Qualität).
constraints:
  max_expected_words: 150              # Wortanzahl-Obergrenze (progressiv)
  # Penalty-Stufen: ≤120% kein Abzug | 121–200% −20% | 201–300% −40% | >300% −60%
  # Trigger und Stufe werden als > [!WARNING] ins Audit-Log geschrieben.

# Metadaten (optional, für Sprach-Constraint) ──────────────────────────
metadata:
  language: "de"                       # "de" → Language-Mismatch-Check aktiv
  # Das Framework prüft per DE/EN-Marker-Heuristik, ob die Antwort
  # in der Zielsprache verfasst ist. Bei EN-Antwort auf DE-Task:
  # status = "language_mismatch" (kein Score-Abzug, separater Status-Flag).
```

---

### Info-Module (Structured Output)

Für Module ohne Scoring (z. B. Political Compass):

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

---

## Scoring-Logik implementieren

### Architektur-Prinzip: MVC

```text
test.py (Controller)
   ↓ delegiert an
core/evaluators.py (Model/Logic)
   ↓ nutzt
core/constants.py (Config/Data)
```

**Regel:** `test.py` darf **keine** Scoring-Logik enthalten. Es orchestriert nur den Aufruf und verpackt das Ergebnis in `BenchmarkResult`.

### Der Controller (`test.py`)

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

---

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

---

## CSV-Output & Leaderboard

### Automatische Spalten

| Spalte | Typ | Quelle |
|--------|-----|--------|
| `asset_id` | String | Dateiname |
| `model` | String | Parameter |
| `timestamp` | DateTime | System |
| `execution_time` | Float | `BenchmarkResult.execution_time` |
| `total_score` | Float | `BenchmarkResult.primary_score` |
| `percentage` | Float | Normalisiert (0–100) |
| `routine_contribution` | Float | config.yaml |
| `reasoning_contribution` | Float | config.yaml |

---

### Custom Spalten

Das Framework schreibt automatisch die Werte aus `BenchmarkResult.data` in die CSV, sofern sie flach genug sind.

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

---

## Tests & Validierung

### Asset-Schema prüfen

```bash
make validate-assets
```

### Modul-Isolations-Test

```bash
# Nur dein Modul in benchmark_config.yaml aktivieren
make benchmark-single MODEL=qwen2.5:7b MODULE=your_module
```

### Leaderboard-Integration

```bash
make leaderboard
# Prüfen: Ist die Spalte da? Sind die Werte korrekt?
```

---

## Best Practices

### DO's ✅

1. **MVC-Trennung:** test.py = Controller, evaluators.py = Logik
2. **Determinismus:** Fixe Seeds, kein Random ohne Seed
3. **Config-First:** Schwellenwerte in config.yaml
4. **Dokumentation:** README.md nach Template

### DON'Ts ❌

1. **Keine LLM-Calls in Evaluators**
2. **Keine Modell-spezifischen Hacks** (unfairer Boost)
3. **Keine Silent Failures** (Exceptions loggen!)

---

## Fehlerbehebung

### „Scores are always 0%"

Debug-Checklist:

1. Nimmt `score_response()` ein `BenchmarkResult` an und gibt es zurück?
2. Wird `score_dict["score"]` zu `result.primary_score` übertragen?
3. Keywords case-sensitive?

Debug-Tool:

```bash
python run_benchmark.py --debug-responses
```

---

## Weiterführende Ressourcen

- **ARCHITECTURE.md** – System-Design & MVC-Patterns
- **USER_GUIDE.md** – Wie Nutzende Module ausführen
- **GOLDEN_STANDARDS.md** – Referenz-Methodik

---

**Dokumenten-Version:** 3.8.1 (Überarbeitung Mai 2026)\
**Kompatibel mit:** CrucibleMark v3.8.2+
