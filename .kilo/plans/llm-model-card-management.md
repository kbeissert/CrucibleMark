# Plan: `scripts/manage_model_cards.py` — LLM-gestütztes Model-Card-Management

## Ziel

Ein einziges Python-Script, das zwei Modi unterstützt:

- **`--mode check`** — bestehende Cards inhaltlich vom LLM prüfen lassen, Bericht ausgeben
  (oder mit `--fix` die vorgeschlagenen Korrekturen direkt anwenden).
- **`--mode make`** — fehlende/ungültige Felder einer Card vom LLM ausfüllen lassen
  und die Card zurückschreiben.

Folgt den Architekturprinzipien von `scripts/analysis/generate_review.py` (Card-für-Card,
Retry, Logging, SSoT-Lookups) und nutzt die bestehende Infrastruktur (`utils.llm_client`,
`utils.card_template`, `utils.model_utils`) so weit wie möglich.

**Dry-Run als Default** — keine Schreibvorgänge an Produktions-Cards ohne explizite
Bestätigung (`--write`).

## Designentscheidungen (vorab geklärt)

1. **API-Zugriff:** Direkter Aufruf der `openai`-Python-SDK (kompatibel mit OpenAI
   *und* jedem OpenAI-kompatiblen Endpoint wie llama-server, OpenRouter, Groq).
   Begründung: native Unterstützung für `OPENAI_API_KEY` und `OPENAI_BASE_URL`,
   keine Abhängigkeit von der internen `LLMClient`-Konfig-Layout. Eigener Retry-
   Decorator (3 Versuche, exponentielles Backoff, 120s Timeout) gemäß Spec.
2. **SSoT-LLM-Config:** Wie Judge und Reviewer wird auch der Model-Card-Generator
   in `benchmark_config.yaml` als top-level-Sektion konfiguriert (siehe
   `llm_judge` und `llm_review` als Referenz). Neue Sektion: `llm_card_manager`
   (s. Abschnitt "Config-Änderung an benchmark_config.yaml"). Die Default-Werte
   werden aus dieser Sektion gelesen, nicht hardcoded. CLI-Flags und
   `OPENAI_BASE_URL` überschreiben die Config (Override-Hierarchie:
   **CLI > Env > benchmark_config.yaml > interner Fallback**).
3. **SSoT-Template:** `utils.card_template.load_card_template("model")` liefert
   `required_fields` + `optional_fields` (Typ, Default, Whitelist-Hinweise).
   Eigener Validator droppt unbekannte Felder und prüft Pflichtfelder.
4. **Operator-geschützte Felder:** Modul-Level-Konstante `OPERATOR_PROTECTED_FIELDS`
   (aus dem bestehenden mechanischen Script übernommen, exakt die im Auftrag
   gelisteten Namen). Werden vor jedem Schreibvorgang aus dem Original wieder
   eingespielt — das LLM darf sie nicht überschreiben.
5. **LLM-Response-Format:** Wir wrappen den Editor-Prompt mit einer kompakten
   System-Instruction, die ein deterministisches Format erzwingt:
   - **`check`:** JSON-Objekt `{"findings": [{"field": "...", "severity":
     "error|warning|info", "message": "...", "current": "...", "suggested": ...}],
     "summary": "..."}`.
   - **`make`:** Komplette JSON-Card (alle Felder aus dem Template, Operator-
     geschützte Felder dürfen weggelassen werden — wir setzen sie selbst).
6. **Dry-Run-Default:** Modi `check` und `make` geben ohne `--write` bzw. `--fix`
   nur Berichte aus und schreiben **nichts**. Bei `make` heißt das Flag `--write`,
   bei `check` heißt es (wie in der Aufgabe) `--fix`.

## Verzeichnis-Layout & Imports

```
scripts/manage_model_cards.py          (neu, ~500–650 Zeilen)
benchmark_config.yaml                  (geändert: neue Sektion llm_card_manager)
```

Imports (alle existieren bereits):

- `argparse`, `json`, `logging`, `os`, `re`, `sys`, `time`
- `pathlib.Path`
- `datetime.datetime` (für `profile_verified_at`)
- `yaml` (für `editor_prompts.yaml` + SSoT-Reads)
- `openai` (Python-SDK; ImportError abfangen mit klarer Meldung)
- `from utils.card_template import load_card_template, cards_dir, rebuild_card_index`
- `from utils.model_utils import _find_card, _card_path`
- `from utils.vendor_card_template import _safe_id`

ROOT_DIR-Bootstrap identisch zu `generate_review.py:23-25`.

## Config-Änderung an `benchmark_config.yaml`

Analog zu den bestehenden Sektionen `llm_judge` und `llm_review` (siehe
`benchmark_config.yaml:30-71`) wird eine neue Sektion **`llm_card_manager`**
hinzugefügt. Initial mit `gpt-5.4` befüllt — selber Default wie der Reviewer
(damit nicht zwei verschiedene Modelle für „verwandte" redaktionelle Aufgaben
konfiguriert werden müssen, und ein Wechsel auf einen anderen Editor-Stack
einmalig ist).

Geplant (einzufügen **nach** `llm_review`, **vor** `defaults`):

```yaml
# LLM-Card-Manager: Recherchiert und verifiziert Model Cards
# (manage_model_cards.py → --mode check / --mode make)
llm_card_manager:
  enabled: true
  provider:
    name: openai
    model: gpt-5.4
    max_tokens: 32768
    # Alternativen: google/gemini-3.1-pro-preview, anthropic/claude-sonnet-4-6
  # System-Prompt-Sektion in config/editor_prompts.yaml → model_card_verification
  # wird unverändert verwendet; nur die LLM-Auswahl ist hier konfigurierbar.
```

Override-Reihenfolge im Script (siehe `_resolve_llm_config()`):

```
1. CLI-Flag           (--model, --base-url, --api-key-env)
2. Env-Variable       (OPENAI_BASE_URL, OPENAI_API_KEY)
3. benchmark_config   (llm_card_manager.provider.*)
4. Interner Fallback  ("openai" / "gpt-5.4" / OpenAI-Default-Base-URL)
```

## Klassenstruktur (Top-Down)

```
scripts/manage_model_cards.py
├── CONSTANTS
│   ├── OPERATOR_PROTECTED_FIELDS: set[str]   (aus Aufgabe, exakt)
│   ├── MAX_RETRIES = 3
│   ├── RETRY_BACKOFF_BASE = 2.0              (Sekunden, exp: 2, 4, 8)
│   ├── PER_CALL_TIMEOUT_S = 120
│   ├── CARD_TEMPLATES_PATH  = "config/card_template_model.yaml"
│   ├── EDITOR_PROMPTS_PATH  = "config/editor_prompts.yaml"
│   ├── MODEL_CARDS_DIR      = benchmark_scores/model_cards/
│   └── LOG_PATH             = logs/manage_model_cards.log
│
├── dataclass CardFinding
│     field: str
│     severity: str         ("error" | "warning" | "info")
│     message: str
│     current: Any
│     suggested: Any | None
│
├── dataclass CardCheckReport
│     model_id: str
│     card_path: Path
│     findings: list[CardFinding]
│     raw_response: str
│     parse_error: str | None
│
├── class LLMSession
│     """Thin wrapper around openai.OpenAI client with retry+backoff."""
│     def __init__(self, model, base_url, api_key, max_retries, timeout_s)
│     def query(self, system: str, user: str) -> str
│         - raises after max_retries exhausted
│
├── dataclass LLMSpec
│     """Aufgelöste LLM-Provider-Konfiguration (post Override-Hierarchie)."""
│     provider_name: str
│     model: str
│     base_url: str
│     api_key: str | None
│     max_tokens: int
│     temperature: float
│
├── def _resolve_llm_spec(args, config: dict) -> LLMSpec
│     """Liest LLM-Config mit Override-Hierarchie CLI > Env > benchmark_config > Fallback.
│     Liefert ein vollständig aufgelöstes LLMSpec; das eigentliche Benchmark-Config-Layout
│     bleibt SSoT, alle anderen Stellen (Reviewer, Judge, Card-Manager) lesen daraus.
│     """
│
├── class CardManager
│     """High-level orchestrator for check/make passes."""
│     def __init__(self, args, session, template, editor_prompt)
│     def run(self) -> Summary
│         - target_cards = self._discover_targets(args)
│         - for idx, (mid, path) in enumerate(target_cards, 1):
│             print(f"[{idx}/{len}] {mid}")
│             if args.mode == "check": self._check_one(mid, path, idx)
│             else:                     self._make_one(mid, path, idx)
│         - return Summary(processed, skipped, errors, report)
│
│     def _discover_targets(args) -> list[(model_id, Path)]
│         - if args.card:                  _find_card(args.card) → 1 Eintrag
│         - elif args.mode == "check":     glob model_cards/*.json
│                                        where profile_verified != true
│                                        (oder alle wenn --force)
│         - elif args.mode == "make":      gleiche Logik
│         - skip _index.json
│
│     def _check_one(mid, path, idx) -> CardCheckReport
│         - load card JSON
│         - build user prompt: card als JSON-Block + Editor-Prompt-Excerpt
│         - session.query(system="check-instr", user=...)
│         - _parse_check_response(text)  → CardCheckReport
│         - print("  ⚠ 3 issues, 1 error" o.ä.)
│         - log finding count
│         - if args.fix and report.parse_error is None:
│             merged = self._apply_check_fixes(card, report)
│             merged = _preserve_operator_fields(card, merged)
│             merged = _validate_against_template(merged, template)
│             path.write_text(json.dumps(merged, ensure_ascii=False, indent=2))
│             rebuild_card_index("model")
│         - return report
│
│     def _make_one(mid, path, idx) -> CardCheckReport
│         - load existing card (oder {} wenn nicht existent)
│         - build user prompt: template-field-list + existing card JSON
│         - session.query(system="make-instr", user=...)
│         - new_card = _parse_make_response(text, template)
│         - new_card = _preserve_operator_fields(existing_or_template, new_card)
│         - new_card = _validate_against_template(new_card, template)
│         - if not args.dry_run: write
│         - rebuild_card_index("model")
│
├── Helper-Funktionen (modul-level)
│   def _setup_logging(log_path: Path) -> logging.Logger
│   def _load_editor_prompt() -> str
│         - liest editor_prompts.yaml → model_card_verification.prompt
│   def _build_check_user_prompt(card: dict, editor_prompt: str) -> str
│   def _build_make_user_prompt(template, existing: dict, editor_prompt: str) -> str
│   def _parse_check_response(text: str) -> tuple[list[CardFinding], str|None, str]
│         - extrahiert JSON-Block (regex oder markdown-fence)
│         - returnt findings, summary, parse_error
│   def _parse_make_response(text: str) -> tuple[dict|None, str|None]
│         - extrahiert JSON-Block
│         - returnt card, parse_error
│   def _preserve_operator_fields(original: dict, new: dict) -> dict
│         - für jedes Feld in OPERATOR_PROTECTED_FIELDS:
│             new[k] = original.get(k, None)
│         - return new
│   def _validate_against_template(card: dict, template) -> tuple[dict, list[str]]
│         - drop keys not in template.all_field_names → log warning
│         - für jedes required_field: wenn value None / "TODO" / "" → log warning
│         - return cleaned_card, warnings
│   def _render_markdown_report(reports: list[CardCheckReport]) -> str
│   def _print_summary(stats: Summary)
│
└── def main()
    - argparse mit allen CLI-Args
    - config = _load_benchmark_config()  # SSoT: liest benchmark_config.yaml
    - llm_spec = _resolve_llm_spec(args, config)  # CLI > Env > Config > Fallback
    - session = LLMSession(model=llm_spec.model, base_url=llm_spec.base_url,
                            api_key=llm_spec.api_key, ...)
    - template = load_card_template("model")
    - editor_prompt = _load_editor_prompt()
    - print("🔧 Card-Manager LLM: {llm_spec.provider_name}/{llm_spec.model}")
    - manager = CardManager(args, session, template, editor_prompt)
    - summary = manager.run()
    - if args.mode == "check" and not args.fix:
          print(_render_markdown_report(summary.reports))
      _print_summary(summary)
```

## Datenfluss

### Modus `check`

```
target_cards = [(mid, path), ...]
for each card:
    user_prompt = f"""
        {editor_prompt}
        
        ## Zu prüfende Card
        ```json
        {json.dumps(card, ensure_ascii=False, indent=2)}
        ```
        """
    system = "Du bist ein Card-Reviewer. Antworte NUR mit JSON:
              {\"findings\":[{\"field\":\"...\",\"severity\":\"error|warning|info\",
               \"message\":\"...\",\"current\":...,\"suggested\":...}],
               \"summary\":\"...\"}"
    response = session.query(system, user_prompt)
    report = _parse_check_response(response)
    if args.fix:
        merged = _apply_check_fixes(card, report)  # spielt suggested-Werte ein
        merged = _preserve_operator_fields(card, merged)
        merged, warns = _validate_against_template(merged, template)
        path.write_text(json.dumps(merged, ensure_ascii=False, indent=2))
    reports.append(report)
print(_render_markdown_report(reports))   # nur ohne --fix
```

### Modus `make`

```
for each card:
    user_prompt = f"""
        {editor_prompt}
        
        ## Template-Felder
        {template.required_field_names + template.optional_field_names}
        
        ## Bestehende Card (kann leer sein)
        ```json
        {json.dumps(existing, ensure_ascii=False, indent=2)}
        ```
        """
    system = "Du bist ein Card-Generator. Antworte NUR mit einer einzelnen
              JSON-Datei, die exakt die Template-Felder enthält. Keine fremden
              Felder. Keine Kommentare. Keine Markdown-Fences."
    response = session.query(system, user_prompt)
    new_card, err = _parse_make_response(response)
    if new_card is None: skip + log
    new_card = _preserve_operator_fields(existing_or_template_defaults, new_card)
    new_card, warns = _validate_against_template(new_card, template)
    if not args.dry_run:
        path.write_text(json.dumps(new_card, ensure_ascii=False, indent=2))
        rebuild_card_index("model")
```

## CLI-Interface

```
python scripts/manage_model_cards.py --mode check
python scripts/manage_model_cards.py --mode check --fix
python scripts/manage_model_cards.py --mode check --force
python scripts/manage_model_cards.py --mode make
python scripts/manage_model_cards.py --mode make --card claude-sonnet-4-6
python scripts/manage_model_cards.py --mode make --force
python scripts/manage_model_cards.py --mode make --model gpt-5.4-mini
python scripts/manage_model_cards.py --mode make --base-url http://localhost:1234/v1
python scripts/manage_model_cards.py --mode make --write          # explizit erlauben
python scripts/manage_model_cards.py --mode make --dry-run        # default
python scripts/manage_model_cards.py --mode check --provider openrouter
python scripts/manage_model_cards.py --mode check --api-key-env MY_KEY
```

Argparse:

- `--mode {check,make}` (required)
- `--card MODEL_ID` (nur `make`: einzelne Card)
- `--force` (auch verifizierte Cards einbeziehen)
- `--fix` (nur `check`: Korrekturen anwenden — sonst nur Report)
- `--write` (nur `make`: Card tatsächlich schreiben — sonst Dry-Run)
- `--dry-run` (Default für `make`; für `check` ohne `--fix` immer)
- `--model MODEL_NAME` (LLM-Modell, Default `gpt-5.4`)
- `--base-url URL` (Default `os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")`)
- `--api-key-env NAME` (Default `"OPENAI_API_KEY"`)
- `--provider NAME` (informational, Default `openai`)
- `--max-retries N` (Default 3)
- `--timeout-s N` (Default 120)

## Fehlerbehandlung — Konkrete Regeln

| Situation                                       | Verhalten                                                |
| ----------------------------------------------- | -------------------------------------------------------- |
| LLM gibt kein parsebares JSON zurück            | `parse_error` setzen, Card überspringen, Warnung loggen  |
| LLM gibt Feld zurück das nicht im Template ist  | Feld aus `new_card` entfernen, Warnung loggen            |
| Pflichtfeld nach LLM-Verarbeitung null/"TODO"   | `profile_verified: false` lassen (nicht auf true setzen) |
| Operator-geschütztes Feld vom LLM geändert      | Original-Wert wiederherstellen, kein Log                 |
| API-Error nach max_retries                      | Exception loggen, Card zählt als Fehler, Loop läuft weiter|
| Timeout > 120s                                  | Retry, nach max_retries Fehler wie oben                   |
| Card-Datei nicht lesbar                         | Skip, Error-Statistik                                    |
| `_index.json` wird mitgezählt                    | Filtern via `_index.json`-Name                           |

## Logging

- `logs/manage_model_cards.log` (mit Timestamp, append mode)
- Format: `%(asctime)s [%(levelname)s] %(message)s`
- Stdout: Fortschritt (`[3/12] claude-sonnet-4-6 ...`), Findings-Count, Summary
- Bei `check` ohne `--fix`: zusätzlich Markdown-Bericht nach stdout

## Beispiel-Output (check ohne --fix)

```markdown
# Model Card Check Report — 2026-06-18

**Modus:** check (dry-run)  
**Verarbeitet:** 12 · **Übersprungen:** 2 · **Fehler:** 1

## claude-sonnet-4-6

- 🔴 `summary` (3 errors, 2 warnings)
  - error: `summary` enthält em-Dash (—) als Aufzählungszeichen, Z. 4
  - warning: `input_price_per_1m` (3.00) ist veraltet — aktuell 3.00 seit 2025-11, ok
  - info: `community` ist null, prüfe ob Distribution über Community

## gpt-5_4-mini

- ✅ keine Findings

## _SUMMARY

- 1 Card fehlerfrei
- 1 Card mit Findings
```

## Tests (manuell / smoke)

Nach Implementierung:

1. `python scripts/manage_model_cards.py --mode check --dry-run` (mit Default-Config)
   - Erwartung: log zeigt "Card-Manager LLM: openai/gpt-5.4", Discovery + per-Card-Versuche,
     schreibt keine Dateien.
2. `python scripts/manage_model_cards.py --mode make --card claude-sonnet-4-6 --dry-run`
   - Erwartung: zeigt Vorschau-JSON, schreibt nicht.
3. Override-Hierarchie verifizieren:
   - `--model gpt-5.4-mini` → nutzt gpt-5.4-mini (überschreibt Config)
   - `--base-url http://localhost:1234/v1` → llama-server statt OpenAI
   - ohne Flags → liest aus `benchmark_config.yaml#llm_card_manager.provider`
4. `python scripts/manage_model_cards.py --mode make --card nonexistent --dry-run`
   - Erwartung: klare Fehlermeldung "Card nicht gefunden".
5. Mit `--base-url http://localhost:1234/v1` gegen llama-server: smoke gegen lokales
   Modell, prüfen ob Retry/Backoff funktioniert.

## Offene Fragen an den User

1. **Operator-geschützte Felder — Quelle:** Die Liste im Auftrag enthält `thinking_probe_*`
   und `cot_*` — diese sind im aktuellen Template als required markiert
   (`thinking_probe_detected`, `thinking_probe_evidence`, `thinking_probe_confidence`,
   `thinking_probe_at`, `cot_marker_family`, `cot_tags_detected`). Frage: Sollen die
   `cot_*`-Felder auch geschützt sein (sind sie automatisch von der Probe gesetzt)?
   Mein Vorschlag: **Ja, exakt die Liste aus dem Auftrag übernehmen** (das LLM darf
   diese nicht überschreiben, da sie automatisch gesetzt werden).
2. **Index-Rebuild:** Nach `--fix` / `--write` — soll `rebuild_card_index("model")`
   aufgerufen werden? Mein Vorschlag: **Ja**, analog zu `_rebuild_index()`-Aufruf
   in `generate_review.py:200`.
3. **Beim Dry-Run von `check` ohne `--fix`:** soll zusätzlich zu Markdown-Report
   ein JSON-File (`logs/manage_model_cards_report.json`) für CI-Parsing geschrieben
   werden? Mein Vorschlag: **Nein**, erstmal nur Markdown (YAGNI; kann später
   ergänzt werden).
4. **`llm_card_manager` Sektion in `benchmark_config.yaml` — Struktur:** Spiegel
   der bestehenden `llm_review`-Sektion (`provider.name`, `provider.model`,
   `provider.max_tokens`). Soll `temperature` auch konfigurierbar sein
   (wie bei `llm_judge`)? Mein Vorschlag: **Ja, mit Default `0.0`** —
   deterministischere Recherche-Ergebnisse sind hier wertvoller als beim Reviewer
   (der kreative Prosa schreibt). Falls nicht gewünscht: weglassen, dann Fallback
   auf `0.0` im Script.
5. **Sektion-Name:** `llm_card_manager` vs. `llm_card_generator` vs.
   `model_card_llm`? Mein Vorschlag: **`llm_card_manager`** — passt zum Script-
   Namen `manage_model_cards.py` und bleibt neutral (deckt `check` + `make` ab).

## Implementierungs-Reihenfolge (nach Freigabe)

1. **`benchmark_config.yaml`:** Neue Sektion `llm_card_manager` einfügen
   (siehe Abschnitt "Config-Änderung").
2. CLI-Parser + Logging-Setup + Konstanten.
3. `_load_benchmark_config()` + `_resolve_llm_spec()` mit Override-Hierarchie.
4. `LLMSession` mit Retry-Decorator (eigenständig testbar).
5. Editor-Prompt-Loader + Template-Loader.
6. `_discover_targets` + `_parse_*_response` (JSON-Extraktion).
7. `_validate_against_template` + `_preserve_operator_fields`.
8. `CardManager._check_one` (Dry-Run-Pfad zuerst).
9. `CardManager._make_one`.
10. Markdown-Report-Generator.
11. End-to-End-Test mit Dry-Run (siehe nächster Abschnitt).

Geschätzter Umfang: 550–700 Zeilen Python, davon ~30% Docstring/Kommentar-frei
(gemäß Code-Style-Guideline: keine Kommentare).

## Tests (manuell / smoke)

Nach Implementierung:

1. `python scripts/manage_model_cards.py --mode check --dry-run` (mit Default-Config)
   - Erwartung: log zeigt "Card-Manager LLM: openai/gpt-5.4", Discovery + per-Card-Versuche,
     schreibt keine Dateien.
2. `python scripts/manage_model_cards.py --mode make --card claude-sonnet-4-6 --dry-run`
   - Erwartung: zeigt Vorschau-JSON, schreibt nicht.
3. Override-Hierarchie verifizieren:
   - `--model gpt-5.4-mini` → nutzt gpt-5.4-mini (überschreibt Config)
   - `--base-url http://localhost:1234/v1` → llama-server statt OpenAI
   - ohne Flags → liest aus `benchmark_config.yaml#llm_card_manager.provider`
4. `python scripts/manage_model_cards.py --mode make --card nonexistent --dry-run`
   - Erwartung: klare Fehlermeldung "Card nicht gefunden".
5. Mit `--base-url http://localhost:1234/v1` gegen llama-server: smoke gegen lokales
   Modell, prüfen ob Retry/Backoff funktioniert.
