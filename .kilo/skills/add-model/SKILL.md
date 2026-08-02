---
name: add-model
description: >-
  Neues Modell in CrucibleMark integrieren: Card erstellen, strukturelle Felder
  manuell füllen, LLM-Recherche laufen lassen, Thinking-Probe durchführen,
  validieren. Reproduzierbarer Workflow für jede neue Modell-Integration.
---

Du bist jetzt Model-Integration-Assistent. Folge diesem Workflow strikt.

## Workflow: Neues Modell integrieren

### 1. provider_config.yaml ergänzen

Eintrag unter `providers.local.vllm.models` hinzufügen:

```yaml
- id: <slug-id>
  name: <Menschenlesbarer Name>
  config: <TOML-Filename-mit-Punkten>
  max_tokens: 16384
  temperature: 1.0
  top_p: 0.95
  top_k: 20
  enable_thinking: true   # nur bei Always-Thinking-Modellen (siehe unten)
```

**Wichtig:**
- `id` = Slug ohne Punkte (Punkte führen zu Slug-Mismatches). Slashes als Vendor-Präfix erlaubt. Doppelpunkte (Ollama) OK.
- `config` = TOML-Filename exakt so wie remote (`~/ai/shared/configs/vllm/models/<config>.toml`)
- Sampling-Params (temperature, top_p, top_k) spiegeln TOML-Defaults wider

**`enable_thinking` — zwei Modell-Klassen:**

| Modell-Klasse | Beispiele | `enable_thinking` | Verhalten |
|---|---|---|---|
| **Always-Thinking** | Qwen3.6, Ornith | `true` | Dual-Profile-Expansion: Standard-Profil erzwingt `enable_thinking:false`, Thinking-Profil `enable_thinking:true`. Beide Profile werden benchmarked. |
| **Selektives Reasoning** | Laguna S 2.1 | **weglassen** | KEIN Dual-Profile. TOML setzt `--default-chat-template-kwargs {"enable_thinking":true}` serverseitig. Das Modell entscheidet pro Request selbst, ob es denkt. Ein Non-Thinking-Profil würde eine Kernfähigkeit künstlich unterdrücken und verzerrt den Benchmark. |

Entscheidungskriterium: Denkt das Modell **immer** (wie Qwen3.6) oder **nur bei Bedarf** (wie Laguna S 2.1)? Bei selektiven Reasoning-Modellen `enable_thinking` weglassen — das Thinking-Profil enthält bereits Non-Thinking-Antworten (Modell-Entscheidung).

### 2. Model Card Skeleton erstellen

```bash
.venv/bin/python scripts/dev/create_model_card.py --model <slug-id>
```

Dies erstellt `benchmark_scores/model_cards/<slug-id>.json` mit TODOs und Pre-Fills aus provider_config.yaml (display_name, developer).

**Fallback:** Falls Card schon existiert, neu generieren:
```bash
.venv/bin/python scripts/analysis/generate_model_cards.py --model-id <slug-id> --force
```

### 3. Strukturelle Felder manuell füllen

Die folgenden Felder werden vom LLM **NICHT** gefüllt (werden als "already validated" behandelt). Sie müssen **vor** dem card-research-Lauf manuell gesetzt werden:

- `origin_country` — Land der Entwicklung (z.B. "CN", "US", "CH")
- `developer` — Entwickler-Unternehmen/Labor
- `vendor` — Vertriebskanal (z.B. "Alibaba Cloud", "OpenAI")
- `model_family` — Modellfamilie (z.B. "Qwen3.6", "GPT-5")
- `params` — Parameteranzahl (z.B. "35B", "9B")
- `architecture` — Architektur-Typ (z.B. "MoE", "Dense")
- `license` — Lizenz (z.B. "Apache-2.0", "Proprietary")
- `inference_engine` — Inferenz-Engine (z.B. "vLLM")
- `quantization_format` — Quantisierung (z.B. "NVFP4")
- `context_window` — Kontextfenster (z.B. 32768)
- `training_cutoff_date` — Stichtag Training (z.B. "2025-06")
- `status` — `"draft"` oder `"complete"`
- `created_at`, `updated_at` — ISO-Datumsstrings

**Namenskonventionen:** Siehe `memory-bank/reference/data-schema.md` (Feldbeschreibungen fuer `display_name` und `model_version`). Diese Datei ist die SSoT — hier NICHT aendern.

### 4. LLM-Recherche laufen lassen

```bash
make card-research MODEL=<slug-id>
```

Dies ruft `scripts/manage_model_cards.py --mode research` auf und nutzt ein LLM (gemini-2.5-pro via OpenRouter), um **nur** folgende 5 Text-Felder zu füllen:

1. `summary` — Zusammenfassung des Modells
2. `strengths` — Stärken (als JSON-Array)
3. `known_limitations` — Bekannte Limitierungen (als JSON-Array)
4. `judge_context_hint` — Hinweise für den Judge
5. `weights_provenance_risk_rationale` — Begründung für Risikobewertung

**Strukturelle Felder bleiben unverändert.** Die Card wird nach dem LLM-Aufruf geschrieben.

**Hinweis zum _reset_llama_context-Fehler:** Am Ende von card-research erscheint manchmal ein Fehler `_reset_llama_context` (llama.cpp Slot-Reset auf vLLM-Server). Dies ist ein nicht-kritisches Cleanup-Problem — die Card wurde bereits erfolgreich geschrieben.

### 5. Thinking-Probe durchführen

```bash
make probe-thinking MODEL=<slug-id>
```

Füllt die `thinking_probe_*`-Felder (die nach card-research noch null bleiben).

### 6. Validierung

```bash
make validate-cards MODEL=<slug-id>
```

Prüft Schema-Konformität und Pflichtfeld-Abdeckung.

## Wichtige Skripte & ihre Rollen

| Skript | Rolle |
|---|---|
| `scripts/dev/create_model_card.py` | Erstellt Skeleton mit TODOs aus provider_config.yaml |
| `scripts/analysis/generate_model_cards.py` | Regeneriert Templates (gleiche Ausgabe wie create) |
| `scripts/manage_model_cards.py --mode research` | LLM-Recherche — füllt nur 5 Text-Felder |
| `scripts/analysis/sync_cards.py` | Synchronisiert fehlende Template-Felder (kein LLM) |
| `scripts/tools/probe_thinking.py` | Thinking-Probe für `thinking_probe_*`-Felder |
| `utils/card_utils.ensure_card()` | Interner Aufruf von create_model_card.py |

## Häufige Fallstricke

- **Punkte in Model-ID:** `create_model_card.py` wirft explizit einen Fehler. Slashes oder Underscores verwenden.
- **Structural fields werden vom LLM ignoriert:** Nur die 5 Text-Felder werden gefüllt. Alle anderen müssen manuell gesetzt werden.
- **Card bereits existiert:** `create_model_card.py` schreibt nichts. Nutze `generate_model_cards.py --force` oder `card-validate` für Updates.
- **TOML-Dateien liegen remote:** Nicht im Repo. Informationen aus der Remote-Quelle (`~/ai/shared/configs/vllm/models/`) beziehen.
- **vLLM-Connector nutzt OpenAI-kompatible API:** `/v1/chat/completions` Endpunkt.
