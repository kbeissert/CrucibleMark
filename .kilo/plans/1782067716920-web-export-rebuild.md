# Web Export Rebuild Plan

## Problem

Der letzte Web-Export ist vom **27. März 2026** (2+ Monate alt) und enthält nur **51 Modelle** statt der aktuellen **95 Modelle** im Leaderboard.

### Bekannte Diskrepanzen
- 44 Modelle fehlen im Export (95 aktuell vs 51 im Export)
- `meta.json` referenziert `bias_sensitivity.csv` als Quelle — diese Datei existiert nicht mehr
- Namenskonventionen haben sich geändert (Version-Suffixe, Namespace-Präfixe)
- `config/web_export_blacklist.yaml` listet 21 Modelle (wurde nach dem letzten Export eingeführt)

## Ziel

Neuen Web-Export generieren, der vollständig mit dem aktuellen Leaderboard (21. Juni 2026) konsistent ist.

## Vorgehen

### Phase 1: Debug-Run (Ursachenanalyse)

```bash
python scripts/web_export.py --output ./web_export_debug --verbose 2>&1 | tee web_export_debug.log
```

**Was geprüft wird:**
- Alle 95 Modelle werden verarbeitet (keine unerwarteten Skipps)
- Model Cards werden korrekt aufgelöst (`resolve_canonical_model_id`)
- Audit-Logs und Reviews werden gefunden
- Blacklist-Filter funktioniert korrekt (21 Modelle sollten übersprungen werden)
- `data.json` enthält Scores und alle erwarteten Felder
- Warnungen zu fehlenden Model Cards werden protokolliert

**Erwartete Ausgabe:**
- ~95 Modelle verarbeitet
- ~21 Modelle als "SKIP (blacklisted)" markiert
- ~74 Modelle als "OK" markiert
- Gegebenenfalls Warnungen zu Modellen ohne Model Card

### Phase 2: Rebuild

```bash
make web-export
```

**Was passiert:**
1. `_setup_output_dirs()` löscht `web_export/models/` komplett (`shutil.rmtree`)
2. `_process_leaderboard()` liest `benchmark_leaderboard_detailed.csv` (95 Modelle)
3. Für jedes nicht-blacklisted Modell:
   - Model Card wird geladen (via `resolve_canonical_model_id`)
   - Audit-Logs werden kopiert (`outputs/audit_logs/`)
   - Reviews werden kopiert (`docs/reviews/`)
   - `models/<slug>/data.json` wird geschrieben
   - `leaderboard.json` wird aktualisiert
   - `political_compass.json` wird aktualisiert
4. `_write_top_level_outputs()` schreibt:
   - `leaderboard.json`
   - `political_compass.json`
   - `provider_stats.json`
   - `vendor_cards.json`
   - `community_cards.json`
   - `meta.json` (mit korrekten Quellen)

### Phase 3: Validierung

```bash
python3 -c "
import json, os

# meta.json prüfen
with open('web_export/meta.json') as f:
    meta = json.load(f)
print(f'generated_at: {meta[\"generated_at\"]}')
print(f'total_models: {meta[\"total_models\"]}')
print(f'models_with_reports: {meta[\"models_with_reports\"]}')
print(f'models_with_reviews: {meta[\"models_with_reviews\"]}')
print(f'card_count: {meta.get(\"card_count\", \"N/A\")}')
print(f'audit_log_count: {meta.get(\"audit_log_count\", \"N/A\")}')
print(f'blacklist: {meta.get(\"blacklist\", {})}')
print(f'sources: {meta.get(\"sources\", {})}')

# leaderboard.json prüfen
with open('web_export/leaderboard.json') as f:
    lb = json.load(f)
print(f'leaderboard models: {len(lb[\"models\"])}')

# data.json Samples prüfen
models_dir = 'web_export/models'
empty = 0
for slug in os.listdir(models_dir):
    data_path = os.path.join(models_dir, slug, 'data.json')
    with open(data_path) as f:
        data = json.load(f)
    score = data.get('leaderboard', {}).get('total_score')
    if not score:
        empty += 1
print(f'data.json mit leerem Score: {empty}/{len(os.listdir(models_dir))}')
"
```

**Erwartete Werte:**
- `total_models`: ~74 (95 minus 21 blacklisted)
- `models_with_reports`: > 0
- `models_with_reviews`: > 0
- Alle `data.json` haben `leaderboard.total_score`

## Risiken

1. **Fehlende Model Cards**: Einige der 95 Modelle haben möglicherweise keine Model Card. Die Pipeline erzeugt dann `model_card: null` in data.json mit einer WARNING.
2. **Namensauflösung**: `resolve_canonical_model_id()` muss alle neuen Model IDs korrekt auflösen. Bei Fehlschlag: Fallback auf Display-Name.
3. **Audit-Log-Pfade**: Neue Model IDs müssen in `outputs/audit_logs/` gefunden werden. `_safe_name()` und `slugify()` müssen konsistent sein.

## Offene Fragen

- Soll der Debug-Run in einem separaten Verzeichnis (`web_export_debug/`) erfolgen, um den bestehenden `web_export/` nicht zu überschreiben? **Empfehlung: Ja.**
