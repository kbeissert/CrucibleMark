# card-cleanup — Bereinigung von display_name und model_version

Prüft alle Model Cards auf Verletzungen der Namenskonventionen und bereinigt sie.

## Automatischer Pre-Check

`make web-export` fuehrt automatisch `validate_naming.py` als Pre-Gate aus (Exit 1 bei Verstoesse).
`make web-export-dev` verwendet `--warn-only` (Exit 0, nur Warnung).
Standalone: `make validate-naming` oder `make validate-naming WARN_ONLY=1`.

## Konventionen

- **`display_name`** = `{Basismodellname} ({Community-Gruppe ODER Variante})`
  - **NICHT**: Quantisierung (NVFP4, FP8, MXFP4), Deployment (vLLM, GGUF), Architektur (Dense, MoE, MTP, DFlash)
  - z.B. `"Qwen 3.6 35B-A3B"`, `"Gemma 4 31B (Unsloth)"`, `"Hermes 4 14B (Abliterated)"`
- **`model_version`** = Reine Versionsnummer
  - **NICHT**: Parameteranzahl (27B, 120B), Quantisierung (FP8, NVFP4), Variante (Instruct, Coder), Community-Gruppe
  - z.B. `"3.6"`, `"4"`, `"5.4"`, `"2.1"`

## Schritte (interaktiver Fix-Workflow)

1. Lese `config/card_template_model.yaml` — Feldbeschreibungen fuer aktuelle Konvention
2. Extrahiere alle Cards mit Problemen:
   ```bash
   jq -r 'select(.display_name != null) | "\(.model_id)\t\(.display_name)\t\(.model_version)"' benchmark_scores/model_cards/*.json
   ```
3. Identifiziere Verletzungen:
   - `display_name` enthaelt: `vLLM`, `NVFP4`, `MXFP4`, `MTP`, `Dense`, `MoE`, `DFlash`, `FP8`
   - `model_version` enthaelt: `27B`, `35B`, `70B`, `120B`, `20B`, `FP8`, `NVFP4`, `MXFP4`, `Instruct`, `Coder`
4. Zeige die betroffenen Cards mit aktuellen Werten und vorgeschlagenen Korrekturen
5. Warte auf Bestatigung des Users
6. Fuehre die Aenderungen durch
7. Baue den Web-Export neu: `make web-export`
8. Validiere den Export:
   ```bash
   python3 -c "
   import json
   with open('/Users/kbeissert/_PROJEKTE/Entwicklung/cruciblemark-web/src/_data/raw/leaderboard.json') as f:
       data = json.load(f)
   models = data['models']
   # Check display_name
   bad_names = [m for m in models if any(x in m.get('display_name','').upper() for x in ['VLLM','NVFP4','MXFP4','MTP','DFLASH'])]
   # Check version
   bad_versions = [m for m in models if any(x in str(m.get('version','')).upper() for x in ['B','FP','NVFP','MXFP','MTP','DENSE','MOE','INSTRUCT'])]
   print(f'display_name Fehler: {len(bad_names)}')
   print(f'version Fehler: {len(bad_versions)}')
   if bad_names: [print(f'  {m[\"model_id\"]}: {m[\"display_name\"]}') for m in bad_names]
   if bad_versions: [print(f'  {m[\"model_id\"]}: {m[\"version\"]}') for m in bad_versions]
   print('VERTRAG:', 'ERFUULLT' if not bad_names and not bad_versions else 'NICHT ERFUULLT')
   "
   ```

## SSoT

Die Konventionen sind definiert in:
- `memory-bank/reference/data-schema.md` — Feldbeschreibungen fuer `display_name` und `model_version`
- `config/card_template_model.yaml` — Template-Feldbeschreibungen
- `config/editor_prompts.yaml` — LLM-Recherche-Anweisungen
- `scripts/analysis/validate_naming.py` — automatisierter Validator (Pre-Gate in `make web-export`)
