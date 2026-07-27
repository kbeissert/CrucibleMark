# Pitfall-Diagnosen

Detaillierte Bug-Diagnosen und Lösungen aus konkreten Vorfällen. Bei Similarity zum aktuellen Fehlerbild: hier nachschlagen.

---

## Qwen 3.6 — CLI-Benchmark Hang bei Test 2 (2026-06-07)

**Symptom:** `qwen3.6-35b-a3b-q8` auf `llamacpp_spark` hängt bei CLI-Benchmark Test 2 (`Cli002 Library`). Gemma 4 26B-A4B durchläuft denselben Benchmark problemlos.

**Root Cause:** Vier zusammenspielende Faktoren:
1. **Model Card Tag falsch:** `architecture_tags` enthielt `"Thinking"` statt `"Thinking-Optional"` → `is_thinking_optional_from_card()` gab `False` zurück.
2. **Kein Token-Budget für cli_benchmark:** `token_budgets` und `token_budgets_reasoning_models` hatten keinen Eintrag → Fallback auf `num_predict: 8192`.
3. **Qwen 3.6 nicht in `is_reasoning_model()`:** String-Trigger-Array enthielt keine Qwen-Einträge.
4. **`enable_thinking: false` allein reicht in llama.cpp NICHT:** llama.cpp ignoriert `--chat-template-kwargs '{"enable_thinking": false}'` allein. Qwen denkt trotzdem weiter. Zusätzlich braucht man `--reasoning-budget 0`.

**Kaskade:** Qwen 3.6 startet trotz fehlendem Tag im Thinking-Modus → 8192 Tokens Budget → ~5000+ Tokens für interne Reasoning-Kette → ~3000 Tokens reichen nicht für sichtbaren Output → llama.cpp Server generiert bis zum Limit → HTTP-Request hängt im 300s-Timeout.

**Fixes:**
1. `qwen3_6-35b-a3b-q8.json`: `architecture_tags: ["Thinking-Optional", "Multimodal", "MoE"]`
2. `benchmark_config.yaml`: `token_budgets.cli_benchmark: 4000`, `token_budgets_reasoning_models.cli_benchmark: 16000`
3. `utils/model_utils.py` `is_reasoning_model()`: Trigger-Array um `"qwen3.6", "qwen3-coder"` erweitert
4. `config/provider_config.yaml`: `enable_thinking: false` für ALLE Qwen-Modelle in `llamacpp` und `llamacpp_spark`
5. `utils/providers/llamacpp.py` `_build_server_cmd()`: `--chat-template-kwargs '{"enable_thinking": false}'` für Qwen-Modelle

**Pitfall:** System-Prompt-Workaround ("Do NOT use thinking tags...") verursacht Hängen! NIE verwenden.
**Pitfall:** `--reasoning-budget 0` blockiert Server-Start auf älteren llama.cpp-Versionen (z.B. `94a220c`). NIE ohne Versionsprüfung verwenden.

**Warum Gemma 4 funktionierte:** Gemma 4 hat keinen Thinking-Modus → kein interner Token-Verbrauch → 8192 Tokens reichen vollständig.

---

## llamacpp_spark — Timeout-Diagnose (v4.3.8 → v4.3.9, 2026-06-07)

**Symptom:** Benchmark schien bei `qwen3.6-35b-a3b-q8` auf `llamacpp_spark` zu "hängen".

**Root Cause (v4.3.8):** Kein Bug — Timeout durch lange Ausführungszeit:
- SSH-Remote-Server-Start: ~20s
- Modell-Ladung (35B-A3B MoE): ~15s
- Test-Ausführung selbst: variabel
- **Gesamt:** Benchmark braucht mehrere Minuten pro Asset, erscheint "stehend"

**Root Cause (v4.3.9 — erweitert):** Connection-Leak + Adaptive Pause:
- **Connection-Leak:** Der httpx-Client hielt Verbindungen im Keep-Alive-Zustand, der Server schloss sie nach langen Requests, der Client merkte es nicht → CLOSE_WAIT-Sockets
- **Adaptive Pause:** 25-32s Memory Recovery zwischen Tests (normal, aber wirkt wie Hang)
- **Gesamt pro Test:** ~70-90s (Test + Pause)

**Fixes:**
1. `utils/providers/llamacpp.py`:
   - `self._client = None` nach jedem `query()` — frische Verbindung pro Request
   - `httpx.Limits(max_keepalive_connections=0)` — Keep-Alive deaktiviert
   - `_is_model_ready()` zusätzlich zu `_is_healthy()` in `query()`
2. `scripts/core/unified_runner.py`: `import os` hinzugefügt (NameError in `_cleanup_local_provider`)
3. `scripts/run_score_benchmark.py`: 3s Pause zwischen Modulen

**Verifikation (Gemma 4 26B-A4B Q8):** Alle 6 CLI-Tests erfolgreich, Durchschnitt 93.7 %.

**Empfehlung:** `nohup make benchmark &` oder `screen` für Hintergrund-Ausführung. Oder `server_ready_timeout_sec: 600` erhöhen.

**Pitfall:** "Hang" bei Remote-llama.cpp-Providern ist oft ein Timeout-Problem, kein Deadlock. Immer Server-Logs prüfen (`tail -f ~/ai/llama-lab-spark.log`) und Benchmark-Fortschritt beobachten, bevor Code-Fixes implementiert werden.

---

## Hermes 4.3 36B — Connection-Resets nach Heavy-Tasks (2026-06-09)

**Symptom:** `Retrying request to /chat/completions`-Meldungen am OpenAI-Client, vor allem nach Heavy-Tasks (>200s).

**Diagnose (`/Users/kbeissert/ai/llama-lab-spark.log`):**
- `n_ctx_train = 524288` (512K) — Hermes 4.3 ist **Hybrid-Mode Reasoning** (ByteDance Seed 36B) mit SWA/Hybrid-Attention
- llama.cpp hat trotz Config `context_window=65536` auf `n_ctx=16384` runterreguliert (Memory-Fit bei 4× parallel)
- Hunderte `forcing full prompt re-processing due to lack of cache data (likely due to SWA or hybrid/recurrent memory)`-Warnungen
- Decoding-Speed 5.83-5.92 t/s (vs. 43-44 t/s für Gemma 4 26B-A4B auf demselben Server)
- 4 parallele Slots + SWA-Re-Processings + 8 GB Prompt-Cache-Limit → sporadische Connection-Resets nach Heavy-Tasks

**Root Cause:** Hybrid-Attention (Recurrent-Layer können nicht im KV-Cache persistiert werden) + 4 parallele Slots in der Recovery-Phase nach langen Heavy-Tasks.

**Lösung (Per-Modell-Override statt globaler Reduktion):**
1. `utils/providers/llamacpp_base.py:_build_server_cmd()` — `parallel` wird jetzt zuerst aus `model_cfg` gelesen
2. `config/provider_config.yaml` `hermes-4.3-36b-q6`: `context_length: 16384`, `parallel: 1`
3. Andere Spark-Modelle (Qwen 3.5/3.6, Gemma 4) bleiben unangetastet auf 4 parallel

**Verifikation:** Server-Command korrekt: `--ctx-size 16384 --parallel 1`. 0 Retries im Lauf. Decoding-Tempo stabil bei 5.86-5.98 t/s.

**Lesson Learned:** Per-Modell-Override ist der richtige Pattern für Hardware-spezifische Tuning-Parameter. Hybrid-Mode-Modelle (SWA/Recurrent) sind im KV-Cache-Limit pro Slot doppelt teuer — `parallel=1` ist für Hybrid-Modelle oft der richtige Default.

**Nicht behoben:** 8 GB Prompt-Cache (`--cache-ram 8192` Default) bleibt aktiv. `--cache-ram 0` würde 8 GB Memory sparen, ist aber ein Server-Start-Flag, das nicht per-Modell überschrieben werden kann.

---

## ToolUse-Leaderboard P1/P2-NaN durch fehlende Flat-Columns (2026-06-10)

**Symptom:** Neu getestetes Modell (`qwen3-coder-next-q8`) zeigt `P1/P2=NaN` im `tooluse_leaderboard`, Combined-Score ist korrekt (74.62).

**Root Cause:** `_aggregate_asset_rows()` in `scripts/core/tooluse_exporter.py` liest P1/P2 aus dem `score_contributions`-Feld der Benchmark-CSVs. Seit dem Writer-Redesign (post-commit d82996f) schreibt `_build_result_envelope()` in `unified_runner.py` das `score_contributions`-Feld **nicht mehr** → bei allen neuen CSV-Zeilen ist `score_contributions` leer.

Combined-Score hatte davon abweichend einen separaten Fallback via `row.get("total_score")` → Combined korrekt aggregiert. P1/P2 und Timing-Felder hatten keinen Flat-Column-Fallback → immer `""` → NaN im Leaderboard.

**Fix (drei Stellen):**
1. `scripts/core/unified_runner.py` `_build_result_envelope()`: Tooluse-spezifische Felder als **flache CSV-Spalten** aus `exec_result.data` promoten. Duck-Typing: `"p1_score" in exec_result.data` als Trigger, um nur ToolUse-Results zu betreffen. Felder: `p1_score`, `p2_score`, `combined_score`, `mcp_mode`, `tool_call_valid`, `tool_call_attempts`, `mcp_latency_s`, `call1_time_s`, `call2_time_s`, `total_time_s`, `call1_tokens`, `call2_tokens`, `hallucination_flag`.
2. `scripts/core/tooluse_exporter.py` `_aggregate_asset_rows()`: **Flat-Column-Fallback** nach dem `score_contributions`-Parsing — wenn `data_dict` leer, direkt aus Flat-Spalten lesen + Boolean-Konvertierung + `mcp_mode`-Fallback via `row.get("mcp_mode") == "live"`.
3. `benchmark_scores/tooluse_leaderboard.csv`: Direkt-Patch für qwen3-coder-next-q8 mit aus Benchmark-Output rekonstruierten Werten (p1=90.00, p2=59.17, combined=74.62, mcp_mode=live, hallucination_flag=true).

**Lesson Learned:**
- `score_contributions` ist als Datenquelle für neue Zeilen **deprecated** — wird seit dem Writer-Redesign nicht mehr befüllt. Legacy-Rows (vor d82996f) haben dieses Feld, neue Rows nicht.
- **Flache CSV-Spalten** sind das neue Pattern für modulspezifische Metriken — robuster und direkt lesbar.
- Asymmetrischer Fallback (Combined hatte Fallback, P1/P2 nicht) erzeugt stille Bugs, die erst im Leaderboard auffallen.

**Detection:** `tooluse_leaderboard.csv` in Texteditor → `NaN` in `p1_score`/`p2_score`-Spalten bei Modellen, die nach dem Writer-Redesign (post-commit d82996f) neu getestet wurden.

**Anti-Pattern:** `score_contributions` als einzige Datenquelle für ToolUse-Metriken ist ein Single-Point-of-Failure. Flat-Column-Pattern ist die robustere Alternative.

---

## ToolUse-Leaderboard Sanierung — 8 Modelle (2026-06-09)

**Symptom (User-Feedback):** „Wenn du die Werte aus dem CSV entfernt hast, sollte es nach einer Regeneration des Leaderboards hier auch nur einfache Striche geben. Ich sehe aber immer noch die alten Values."

**Erste (unvollständige) Sanierung:** Quell-CSV-Zeilen entfernt + Card-Reset. Aber: nach `make tooluse-leaderboard` waren 4 Modelle **wieder im Leaderboard** (95 Zeilen, +2 trotz Entfernung).

**Wurzelursache (kritisch):** `aggregate_from_benchmark_csvs()` benutzt `_upsert_row()` statt die CSV zu überschreiben. `_upsert_row()` löscht keine Zeilen für Modelle, die nicht (mehr) in den Quell-CSVs stehen.

**Zweite (vollständige) Sanierung:**
- 1 Modell kehrte nach erster Sanierung zurück (`gemini-3.5-flash` mit combined=71.00)
- Sanitizer hatte Underscore-Variante `gemini-3_5-flash` in `commercial_models_benchmark.csv` nicht gefunden (String-Drift: Punkt vs. Underscore)
- Exakter String-Vergleich vs. `_safe_name()`-normalisierter Vergleich

**Vollständige Sanierung (8 Modelle, alle 8 weg nach `make tooluse-leaderboard`):**
1. Card-Reset: 5 Modelle via `update_model_card_tooluse_fields(model, "untested", None)`
2. 6 tooluse-Audit-Files pro Modell aus `outputs/audit_logs/<dir>/tooluse00*.md` gelöscht
3. Quell-CSV-Bereinigung: 18 cloud + 18 commercial tooluse-Zeilen entfernt
4. 6 tooluse-Zeilen für `gemini-3_5-flash` (Underscore-Variante) aus `commercial_models_benchmark.csv` entfernt
5. Leaderboard-Zeile explizit gelöscht VOR `make tooluse-leaderboard`
6. `make tooluse-leaderboard` → 91 → 84 Zeilen, 0 problematische Modelle

**Lesson Learned — Erweiterte 4-Schritt-Pflicht (künftige Sanierung):**
1. Card auf `untested`
2. Tooluse-Audit-Files löschen
3. Quell-CSV-Zeilen entfernen — UND zwar in ALLEN Schreibweisen (Punkt, Underscore, Slash). Sanitizer muss `_safe_name()`-normalisiert vergleichen.
4. Leaderboard-Zeile explizit löschen (vor `make tooluse-leaderboard`)
5. `make tooluse-leaderboard` — verifizieren, dass 0 Zeilen mit den Modell-IDs vorhanden sind
6. Wenn ein Modell nach `make tooluse-leaderboard` zurückkommt: prüfen, ob es im Quell-CSV noch tooluse-Zeilen unter einer String-Drift-Variante gibt.

**Anti-Pattern vermieden:** Sanitizer mit `model == "<id>"` (exakter String-Vergleich) ist fehleranfällig. Stattdessen `model == _safe_name(id) or model == id or _safe_name(model) == _safe_name(id)`.

---

## ToolUse-Leaderboard — Legacy-Zeilen ohne score_contributions (2026-06-05)

**Symptom:** Modelle zeigen `MCP-Modus: mock`, `P1/P2 = 0.0` im Tool-Use-Leaderboard, obwohl `supports_tool_use: true` in der Model Card steht.

**Ursache:** Modelle, die VOR dem Scoring-Redesign (commit d82996f, 25.05.2026) getestet wurden, haben kein `score_contributions`-Feld. Der Exporter liest `p1_score`, `p2_score` und `mcp_latency_s` ausschließlich aus diesem Feld.

**Erkennung:** `score_contributions`-Feld in den Benchmark-CSVs leer bei `asset_id` startend mit `tooluse`.

**Fix:** `python scripts/run_tooluse_benchmark.py --force --model <model_id>` für jedes betroffene Modell.

**Betroffene Modelle (Stand 26.05.2026):** kimi-k2.5-0127, deepseek-v4-pro, deepseek-v4-flash, hermes-4-405b, hermes-4-70b, mistral-medium-3-5, mistral-small-2603, mistral-large-2512, devstral-2512, gemini-3.5-flash, gpt-5.5

---

## hermes-4-70b ToolUse-Sanierung (Diagnose, 2026-06-09)

**Symptom:** Leaderboard-Zeile zeigte `p1=,,p2=,,combined=71.54` (P1/P2 leer, Combined gültig). User-Frage: „Warum steht NAN im Leaderboard, wenn die Audits vollständig sind?"

**Diagnose-Befund:**
- 6 ToolUse-Zeilen in `cloud_models_benchmark.csv` vom 26.05.2026 (vor `commit d82996f`)
- `total_score = 76, 80, 83.75, 62, 67.5, 60` → Mittelwert 71.54 (gültig)
- `score_contributions = ''` (Pre-Redesign-Writer hat es nicht persistiert)
- `p1_score` / `p2_score` als **Spalte nicht vorhanden**

**Architektur-Schwächen (zwei):**
1. **Asymmetrischer Fallback** in `scripts/core/tooluse_exporter.py:425-457`:
   - `combined` hat Fallback auf `row.total_score` → 71.54 wird korrekt aggregiert
   - `p1`/`p2` haben NUR Fallback auf `row.get("p1_score")` (Spalte) → leer
2. **Keine In-Stream-Schema-Validierung:** Exporter akzeptiert CSV-Zeilen ohne P1/P2-Felder stillschweigend.

**Makefile-Lücke (zusätzlich entdeckt):** `make tooluse-run` ruft `run_benchmark.py --module tooluse`, NICHT `scripts/run_tooluse_benchmark.py`. Damit greift `FORCE=1` nicht durch. Für `FORCE` IMMER den direkten CLI-Pfad nutzen.

**Sanierung (gpt-5_5-Muster):**
1. `update_model_card_tooluse_fields('nousresearch/hermes-4-70b', 'untested', None)`
2. `tooluse_leaderboard.csv`: Zeile entfernt
3. 6 tooluse-Audits in `outputs/audit_logs/nousresearch_hermes-4-70b/tooluse00*.md` gelöscht
4. Re-Test: `.venv/bin/python3 scripts/run_tooluse_benchmark.py --force --model nousresearch/hermes-4-70b`

---

## Race-Condition Lesson Learned — ID-SSoT-Phasen (2026-06-08)

**Symptom:** `make benchmark-auto` lief seit 11:05 (Hermes 4.3 36B auf DGX Spark). User meldete: Tests 1+2 mit 0 Tokens / 0.0s, Test 3 OK, Test 4 hing.

**Root Cause:** Während ID-SSoT-Phasen 1–9 (gleicher Tag) wurden mehrere Core-Module modifiziert UND auf Filesystem-Ebene Karten hinzugefügt/umbenannt/gelöscht. Python cache `import`s in `sys.modules` — laufender Prozess sah keine Code-Änderungen, aber jede `_find_card()`-Aufruf las frisch vom Filesystem → Race Condition.

**Lesson Learned (goldene Regel):**
- **NIEMALS während eines laufenden Benchmarks Core-Module modifizieren oder Filesystem-Operationen auf `benchmark_scores/` durchführen.**
- Vor jedem `make benchmark-auto`: `git status` und `git diff --stat` prüfen — wenn seit dem letzten `make benchmark` Core-Dateien geändert wurden, vorher committen und sauberen Stand herstellen.

---

## Voreiliger Cache-Hit in Batch-Modulen (Pitfall, 2026-06-03)

**Anti-Pattern:** `BaseBenchmarkRunner.execute_batch_module()` hatte einen 3-CSV-Cache-Hit auf `(model, batch_asset_id)`. Wenn der Eintrag in `cloud_models_benchmark.csv` mit `asset_id="political_compass"` existierte, wurde die gesamte Batch-Logik per `return [cached_res.copy()]` übersprungen — **einschließlich `PoliticalCompassHandler.handle_results()` und damit `save_leaderboard_csv()`**.

**Symptom:** Modell hat vollständige PC-Daten in `political_compass_results.csv` (RUN_1/RUN_2/AVG mit Koordinaten, Shift, Archetyp), aber **kein** Eintrag in `political_compass_leaderboard.csv`. Im Hauptboard → "Pending" in Spalte "Political Bias".

**Fix:** `execute_batch_module` schließt PC-Module explizit vom 3-CSV-Fast-Path aus. Cache-Hit → `pc_leaderboard.csv` Check → nur dort skippen, sonst PC-Test tatsächlich ausführen.

**Generalisierte Lektion:** Bei Batch-/Diagnose-Modulen (PC, Tool-Use, Bias) NIEMALS auf aggregierte Standard-CSVs als Skip-Beweis vertrauen. Immer das modul-spezifische Leaderboard/Output-File als SSoT prüfen.

---

## Review-Generator Test-Artefakt-Cleanup (ab 2026-06-03)

**Problem:** `scripts/analysis/generate_review.py::_run_tooluse_reviews()` erstellt Tool-Use-Reviews unter `docs/reviews/{slug}` mit `slug = _safe_name(model_id)`. Bei manuellen Tests mit ungewöhnlichen oder numerischen Modell-IDs entstehen Test-Artefakt-Ordner ohne echtes Modell:
- `9` (Normalisierung von numerischer ID)
- `leet`, `e`, `2026-06-02T07_42_52Z` (Test-Slugs)

**Lösung:** Ordner manuell löschen. Diese Artefakte entstehen NUR durch direktes Skript-Testen mit nicht-produktiven Modell-IDs.

**Prävention:** Bei zukünftigen manuellen Review-Tests sicherstellen, dass `--model`-Parameter ein echter, in der Config registrierter Modellname ist (z.B. `gpt-4o`, `claude-opus-4-5`), nicht numerisch oder aus Tests.

---

## Voreiliger Cache-Hit beim Provider-Health-Preflight (2026-06-09)

**Symptom:** `validate_untested_card()` returnte `(False, "missing_provider")` obwohl Modelle in `config/provider_config.yaml` konfiguriert sind und die API direkt antwortet.

**Betroffene Modelle:** `nvidia_nemotron-3-ultra-550b-a55b`, `z-ai_glm-5-20260211`

**Root Cause:** Model Cards hatten `model_id` in **Underscore-Form** statt **Slash-Form**:
- Card: `"nvidia_nemotron-3-ultra-550b-a55b"`
- Config (SSoT): `"nvidia/nemotron-3-ultra-550b-a55b"`

`validate_untested_card()` versucht Provider-Inferenz in zwei Stufen:
1. **Exakter Config-Lookup** in `_infer_provider_from_config()`: vergleicht byte-genau → FAIL (Underscore ≠ Slash)
2. **Heuristik-Fallback** via `resolve_provider()`: greift nur bei `:` ODER `/` im model_id → FAIL

**Lösung:** Model Card `model_id` auf exakte Form aus `config/provider_config.yaml` bringen. Dateinamen bleiben gleich (`_safe_name()` konvertiert Slashes zu Underscores).

**Zusätzlicher Pitfall — OpenRouter Free-Tier + Data-Policy:**
- `nvidia/nemotron-3-ultra-550b-a55b:free` (Free-Tier) gibt **HTTP 404** mit `No endpoints available matching your guardrail restrictions and data policy`
- Kommerzieller Endpunkt funktioniert (z.B. `nvidia/nemotron-3-ultra-550b-a55b-20260604` über Provider `DeepInfra`)
- **Lösung:** Free-Karte löschen, kommerziellen Endpunkt nutzen.

**Lesson Learned:** Bei neuen OpenRouter/Groq-Model-Cards IMMER `model_id` mit Slash setzen, damit exakter Config-Lookup greift. Dateinamen werden ohnehin durch `_safe_name()` normalisiert.

---

## Python 3.14 `sys.path`-Workaround für Skript-Modus

**Problem:** Bei `python scripts/core/foo.py` (Skript-Modus, NICHT `python -m`) setzt Python 3.14 `sys.path[0] = scripts/.../foo.py` Verzeichnis. `Path(".")` als `sys.path[0]` reicht NICHT für relative Package-Imports wie `from utils.constants import ...`.

**Ursache:** Skript-Verzeichnis hat Vorrang vor CWD-basierten Imports, und `Path("scripts/.../__init__.py").parent.parent.parent` liefert `Path(".")` (relativ), was Python 3.14 nicht als gültigen Pfad für Package-Discovery akzeptiert.

**Fix:**
```python
import sys
from pathlib import Path

# VOR allen `from package...` Imports:
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
```

**`.resolve()`** ist kritisch — liefert den absoluten Pfad statt `Path(".")`.

**Workaround-Pattern:** `python -m scripts.core.benchmark_auto` (Modul-Modus) umgeht das Problem, aber das Makefile ruft `python scripts/core/benchmark_auto.py` (Skript-Modus), was kompatibel mit venv-Setups ohne `PYTHONPATH` ist.

---

## Pylint/Pylance Pitfalls

- **Makefile:** Strings müssen in Anführungszeichen enden. Tabs (nicht Spaces) als Einrückung. Doppelte `""` am Zeilenende verursachen zsh-Syntaxfehler.
- **try/except ImportError:** Bei Fallback im `except`-Block MUSS die Variable explizit auf `None` gesetzt werden, sonst meckert Pylance. Type-Guard vor Aufruf einbauen.
- **Linter-Cache:** VS Code Pylance/Pylant zeigt stale Warnungen — nach IDE-Restart (`Developer: Reload Window`) verschwinden diese.
- **Mypy conditional expressions:** Komplexe nested ternaries in Dict-Literalen verursachen oft Mypy-Probleme → in Helper-Funktion auslagern.
- **`_find_card()` Glob-Fallback:** Matcht nur Suffixe die mit Ziffer beginnen (z.B. `-20250929`), um Kollisionen mit ähnlichen Modellnamen zu vermeiden.
- **`assertIsNotNone()` reicht Pylance nicht:** Nach `assertIsNotNone(env)` bleibt der Typ für Pylance `Optional[...]`. Für `.get()`, `[key]` etc. muss explizit gecastet werden.
- **Pylint W0611 (unused-import):** Jeder neu hinzugefügte Import muss sofort verwendet werden — sonst Linter-Warnung.
- **Ruff `SIM103` mit `--unsafe-fixes`:** Oft zu aggressiv. Lösung: Variable extrahieren ODER die gesamte Bedingung negieren (`return not any(...)` ist die idiomatische Form).
- **Mypy-Stub für `pandas.isna()`:** Braucht expliziten None-Check vor `str(val).strip()` — Pandas-Reihen mit `NaN` werden sonst zu `"nan"`-Strings.

---

## llama.cpp Server-Timeout durch model_file-Tippfehler (2026-06-10)

**Symptom:** `make benchmark-auto` lief in Modul 1b (Lokale Modelle, llama.cpp M4) auf Modell `gemma-4-12b-it-ud-q4_k_xl` und hing 180s in `server_ready_timeout_sec`, bevor es mit "did not become ready within 180 s." übersprungen wurde. Die anderen Gemma-4-Varianten (Q6_K_XL, Q8_K_XL) starteten danach problemlos.

**Root Cause:** Tippfehler in `config/provider_config.yaml` Zeile 363:
- **Config-Eintrag:** `model_file: gemma-4-12b-it-UD-Q4_K_X.gguf` (ohne `L`)
- **Tatsächliche Datei auf Disk:** `gemma-4-12b-it-UD-Q4_K_XL.gguf` (mit `L`)

Der llama-server startete sich, versuchte das Modell zu laden, scheiterte sofort mit `gguf_init_from_file: failed to open GGUF file ... (No such file or directory)`, und beendete sich. Das Python-Skript pollt 180s lang `/health` (das nie 200 zurückgibt) → Timeout. Erst beim 5. Modell (Q6_K_XL) lief alles normal — der User nahm das als "Test des Nix Modells" wahr, weil der Server scheinbar "aus dem Nichts" für das nächste korrekt konfigurierte Modell startete.

**Lessons Learned:**
1. **Tippfehler in `model_file` kosten 180s pro Modell.** Bei vielen Modellen mit ähnlichen Namen (gemma-3 vs. gemma-4, Q4 vs. Q6 vs. Q8, _X vs. _XL) ist das ein realer Wartungs-Pitfall.
2. **Nicht jeder Server-Start-Fehler ist ein llama.cpp-Bug.** Bei `exit: exiting due to model loading error` immer zuerst `model_file`-Pfad prüfen.
3. **Bei M4-Batch mit 16 Modellen** können sich 180s-Timeouts schnell zu 30+ Minuten verschwendeter Zeit summieren.

**Fixes (zwei Schritte):**
1. `config/provider_config.yaml` Zeile 363: `gemma-4-12b-it-UD-Q4_K_X.gguf` → `gemma-4-12b-it-UD-Q4_K_XL.gguf` (Tippfehler-Korrektur).
2. `utils/providers/llamacpp_base.py`: Neue Methode `_preflight_check_model_file(model_id) -> (bool, str)` prüft VOR dem `subprocess.Popen()`, ob die model_file auf der Disk existiert. In `start_server()` Pfad 4 (Cold-Start) wird der Check aufgerufen — bei False wird der Server-Start sofort mit klarer Fehlermeldung (`"Model-Datei nicht gefunden für '...': '<pfad>'. Prüfe model_file in providers.local.<key>.models."`) abgebrochen, statt 180s in Timeout zu laufen.
   - Pfad 1/2/3 (Server läuft bereits, Adopt-Pfad, Restart) sind NICHT betroffen — der Check gilt nur für echte Cold-Starts.
   - 6 neue Tests in `tests/test_llamacpp_provider_separation.py`: Happy-Path, Tippfehler-Pitfall (exakt dieser Q4_K_X vs. XL Fall), leerer `model_file`-Eintrag, korrekter Provider-Key in der Fehlermeldung, kein `Popen`-Aufruf bei fehlgeschlagenem Check, Happy-Path mit Popen-Aufruf.

**Pitfall-Verallgemeinerung:** Bei jedem "Server startet nicht"-Timeout zuerst `model_file`-Existenz auf Disk prüfen, BEVOR man llama.cpp-Versionen, GPU-Layer-Settings oder Token-Budgets verdächtigt. `Path(model_path).is_file()` kostet <1ms.


## Card-First-Probe wird durch `null`-Wert in Draft-Card umgangen (2026-06-10)

**Symptom:** Reasoning-Modelle (z.B. `gemma-4-12b-it-ud-q6_k_xl`) bekommen nur 8192 Tokens Budget statt 40960 (5x-Reasoning-Budget), obwohl der Card-First-Hook eigentlich die Thinking-Probe ausführen sollte, die das 5x-Budget freischaltet. Folgewirkung: lange CoT-Antworten werden truncated oder schlagen ganz fehl (5B-Test, Root-Cause-Analysis mit ~4300 Tokens Output scheiterte).

**Root Cause:** Bug in `scripts/core/unified_runner.py` (`_read_card_probe_state`, Zeile ~186):

```python
# BUG:
if "thinking_probe_detected" not in loaded:
    needs_probe = True
```

`ensure_card()` (`utils/card_utils.py`, `_CARD_TEMPLATE`) erzeugt Draft-Cards mit **explizit `None`-Wert** für alle Felder:

```python
"thinking_probe_detected": None,
"thinking_probe_evidence": None,
"thinking_probe_confidence": None,
"thinking_probe_at": None,
```

`"thinking_probe_detected" not in loaded` prüft nur, ob der **Key** existiert — nicht ob der **Wert** truthy ist. `None` ist ein existierender Key, also `not in loaded` ist `False` → `needs_probe` bleibt `False` → Probe wird **nie ausgeführt** → Card bleibt dauerhaft auf `null` → `resolve_effective_thinking()` returnt `(None, "none")` → **kein 5x-Budget**.

**Effekt:** Alle Modelle, die nur via Config ergänzt wurden (nicht manuell mit echter Probe), bleiben im Draft-Stub-Zustand hängen — Reasoning-Budget ist blockiert.

**Fix (1 Zeile):** `scripts/core/unified_runner.py` Zeile 186:

```python
# VORHER (Bug):
if "thinking_probe_detected" not in loaded:
    needs_probe = True

# NACHHER (Fix):
probe_state = loaded.get("thinking_probe_detected")
if probe_state is None:
    needs_probe = True
```

`is None` deckt **beide** Fälle ab: Key fehlt komplett ODER Wert ist `null`. `True` und `False` triggern **keinen** Re-Probe (würde Endlos-Probe-Loop verursachen).

**Verifikation:** 7 Unit-Tests in `tests/test_card_first_probe_trigger.py` decken alle 4 Probe-States (null / missing / True / False) ab, sowie fehlende/fehlerhafte Card-Dateien.

**Pitfall-Verallgemeinerung:** Bei jedem `not in dict` Check, der eigentlich "Wert fehlt" bedeuten soll, IMMER `dict.get(key) is None` verwenden — `not in` unterscheidet nicht zwischen "Key fehlt" und "Wert ist null", aber Generatoren wie `ensure_card()` setzen explizit `None` für alle Felder. Dies ist ein klassischer Python-Idiom-Fehler mit Daten-Konsequenzen.

**Auswirkung auf Gemma 4 (und ähnliche Modelle):** Nach dem nächsten Benchmark-Lauf wird `_read_card_probe_state` → `needs_probe=True` → `probe_thinking_model()` läuft → `thinking_probe_detected` wird in die Card geschrieben → `resolve_token_budget` aktiviert 5x-Budget (z.B. 8192 → 40960) → CoT-Antworten bekommen genug Platz.

---


## Test-Card-Leichen in `benchmark_scores/model_cards/` durch unautouse-Fixture (2026-06-10)

**Symptom:** Nach `pytest`-Läufen fanden sich Test-Artefakte wie `m1.json`, `m2.json`, `True.json` im **echten** `benchmark_scores/model_cards/`-Ordner. Diese waren:
- ungültige Karten mit Platzhalter-Feldern (`model_id: "m1"`, `display_name: "TODO"`, `card_status: "draft"`)
- wurden von Web-Export und `score_calculator` als „bekannte Modelle" interpretiert
- führten zu Schreibzugriffen in `web_export/raw/models/...` und fehlerhaften Leaderboard-Einträgen

**Root Cause:** `tests/conftest.py` existierte nicht. Zwei Worker-Tests riefen `worker.main()` direkt auf und monkeypatchten `CARD_DIR` NICHT:
- `tests/test_run_score_benchmark.py` (Test 1+2: `--model gemma3:12b`, `--models m1,m2`)
- `tests/test_run_political_compass_benchmark.py` (Test 1+2: `--model gemma3:12b`, `--models m1,m2`)

Code-Pfade wie `discover_models()`, `enforce_card_first()` oder Card-Lookups in `UnifiedBenchmarkRunner` griffen via `CARD_DIR = Path("benchmark_scores/model_cards")` auf den **echten** Ordner zu. `ensure_card()` legte für unbekannte Model-IDs (`m1`, `m2`, `True`) Stub-Karten an.

**Fix:**
1. Neue Datei `tests/conftest.py` mit `autouse=True`-Fixture `_isolate_card_dir`:
   - `monkeypatch.setattr("utils.model_utils.CARD_DIR", tmp_path)` für jeden Test
   - Custom-Marker `pytest.mark.uses_real_cards` für Tests, die echte Cards brauchen (z.B. `test_resolve_canonical_model_id.py` mit glob-fallback Card-Alias)
   - Marker-Registrierung via `pytest_configure()` → keine `PytestUnknownMarkWarning`
2. `tests/test_resolve_canonical_model_id.py` mit `pytestmark = pytest.mark.uses_real_cards` markiert

**Konvention:** `CARD_DIR = tmp_path` (nicht `tmp_path / "model_cards"`) — identisch zu den bestehenden Fixtures in `test_enforce_card_first.py`, `test_id_ssot_invariants.py`, `test_benchmark_auto_untested_tooluse.py`. `monkeypatch` restauriert am Ende alle setattrs auf den Originalwert, daher kein Konflikt bei Mehrfach-Patching.

**Lokale `CARD_DIR`-Konstanten** in anderen Modulen (`scripts.core.benchmark_auto.CARD_DIR`, `scripts.run_tooluse_benchmark.CARD_DIR`) sind separate Modul-Attribute und werden NICHT beeinflusst — Tests, die diese monkeypatchen, funktionieren weiterhin.

**Verifikation:**
- 4 betroffene Tests (`test_run_score_benchmark.py`, `test_run_political_compass_benchmark.py`) grün
- Voller Test-Run: 15 failed, 900 passed — exakt gleiche Failures mit und ohne `conftest.py` (0 Regressionen, 15 pre-existierend: 14 MCP-network + 1 audit-logs safe-name)
- `ls benchmark_scores/model_cards/ | grep -E "^(m1|m2|True)\.json"` ist nach Test-Run LEER (kein Leichen-Effekt mehr)

**Pitfall-Verallgemeinerung:** Jeder Test, der `worker.main()` oder `subprocess.run` mit dem ECHTEN Projekt-Pfad aufruft, MUSS `CARD_DIR` (und vergleichbare Pfad-Konstanten) per `monkeypatch` auf `tmp_path` umlenken — sonst entstehen Leichen im Produktionsordner. Eine zentrale `conftest.py`-autouse-Fixture ist der saubere Weg.


## Leaderboard zeigt "TODO" / "k.A." für neue Modelle wegen Draft-Cards (2026-06-10)

**Symptom:** Nach `make benchmark` + `make leaderboard` erscheint das neue Modell im Leaderboard, aber mit:
- `Model Name = "TODO"`
- `Version = "k.A."`
- Falscher/fehlender `Type` (z.B. "Open Weights" statt "Restricted Weights")
- Fehlende Felder (`Cost`, `Vendor`, `weights_license_tier`)

Konkretes Beispiel 2026-06-10: `gemma-4-12b-it-ud-q8_k_xl` lief 32 Tests erfolgreich (Score 70.89, 97% Coverage), Leaderboard-Eintrag Rank 50 zeigte aber `TODO/k.A./Open Weights`.

**Root Cause:** `make benchmark` ruft `unified_runner.py` auf, das via `utils.card_utils.ensure_card()` automatisch eine Draft-Card für unbekannte Model-IDs anlegt — mit `display_name="TODO"`, `card_status="draft"`, `model_version=null` und allen anderen Feldern auf "TODO" / null. Das ist by design (verhindert Hard-Fail bei fehlender Card), aber:
1. **`make leaderboard` liest `display_name` und `model_version` direkt aus der Card** (SSoT in `scripts/leaderboard/__init__.py` Zeile 208-243 + `data_loader.py` Zeile 215-241)
2. **Draft-Cards liefern "TODO" und `null`** → Leaderboard zeigt diese Platzhalter
3. **`make model-cards` regeneriert nur das Template** — befüllt keine Felder, setzt nur `action="rebuilt"` und Status `draft`

Der Benchmark-Lauf selbst ist NICHT betroffen — Score, Judge, Tokens landen korrekt in der CSV. Nur die **Anzeige** im Leaderboard ist entstellt, bis die Card manuell befüllt wird.

**Fix:** Card manuell ausfüllen — nicht `make model-cards` (das hilft nicht). Vorlage: ein vergleichbares Modell mit gleicher Quantisierung / gleichem Provider kopieren und Felder anpassen. Nach dem Befüllen:
```bash
.venv/bin/python -c "from utils.card_template import rebuild_card_index; rebuild_card_index('model')"
make leaderboard
```

**Konkretes Beispiel 2026-06-10:** `gemma-4-12b-it-ud-q8_k_xl.json` (Draft) → manuell befüllt (analog `gemma-4-12b-it-ud-q6_k_xl.json`, `model_version="4 (Q8_K_XL GGUF)"`, `display_name="Gemma 4 12B Instruct Q8_K_XL (GGUF, UndiX-Derivative)"`, `weights_license_tier="restricted-weights"`, `card_status="complete"`) → Leaderboard-Eintrag: korrekt mit `Restricted Weights`, `4 (Q8_K_XL GGUF)/M4APL`, vollständigem Display Name.

**Detection-Befehl für andere Draft-Cards:**
```bash
.venv/bin/python -c "
import json
from pathlib import Path
for p in Path('benchmark_scores/model_cards').glob('*.json'):
    if p.name == '_index.json': continue
    try:
        d = json.loads(p.read_text(encoding='utf-8'))
        if d.get('card_status') == 'draft':
            print(f'  {p.name:50s} display_name={d.get(\"display_name\",\"\")!r}')
    except: pass
"
```

**Detection im Leaderboard:**
```bash
grep "TODO" benchmark_scores/benchmark_leaderboard.csv
```

**Pitfall-Verallgemeinerung:** Die Card-SSoT-Architektur garantiert, dass das Leaderboard KEINE Halluzinationen über Card-Felder macht — gleichzeitig bedeutet das, dass **unbefüllte Draft-Cards sichtbar im Output landen**. Empfehlung für künftige Verbesserungen: `make leaderboard` könnte (a) `card_status != "complete"` als Warnung loggen, oder (b) Draft-Modelle aus dem Leaderboard ausschließen mit Hinweis "Card pending". Aktuell ist die manuelle Card-Pflege der einzige Workflow.

**Verifikation:** Nach dem Fix:
- `grep "TODO" benchmark_scores/benchmark_leaderboard.csv` → leer
- Gemma 4 12B Q8_K_XL: Rank 50, korrekter Display Name + Version + Type "Restricted Weights"
- Tests grün: 57/57 in test_generate_model_cards + test_card_template + test_card_first_probe_trigger

---

## Dual-Thinking-Profile kollabieren zu Basis-Modell (2026-07-10)

**Symptom:** Tool-Use-Lauf für `qwen3_6-27B-thinking` schreibt CSV-Zeilen mit `model=qwen3_6-27B` (Basis-Modell) statt mit der Thinking-Profil-ID. Leaderboard-Liste zeigt `qwen3_6-27B-thinking` gar nicht an. `tooluse_tested_at` in der Card bleibt `null` trotz erfolgreichem Run.

**Root Cause — zwei separate Bugs:**

1. **Profil-ID-Kollaps in `_read_card_probe_state`** (`scripts/core/unified_runner.py`): Methode lud die Card für `qwen3_6-27B-thinking` per Thinking-Suffix-Fallback, übernahm aber `loaded["model_id"] = "qwen3_6-27B"` als canonical. Folge: Sampling-Params des Standard-Profils wurden geladen, `enable_thinking=True` ging verloren, alle CSV-Zeilen unter Basis-ID geschrieben.

2. **Path B No-Op-Failure-Mode** (`scripts/core/tooluse_exporter.py:aggregate_from_benchmark_csvs`): Active Code-Path aktualisierte die Card gar nicht — `update_model_card_tooluse_fields()` wurde nur von `finalize_model()` (Path A, deprecated) aufgerufen. Folge: `tooluse_tested_at` blieb über Monate `null` für alle Standard-Modelle.

**Zusätzlich strukturelles Problem:** Card ist SSoT für mehrere Profil-Runs (Standard + Thinking), hatte aber nur einen flachen Slot für `tooluse_tested_at`/`tooluse_score_p1`/`tooluse_score_p2`. Race Condition bei sequentiellen Profil-Runs — letzter überschreibt vorherigen.

**Fixes (v4.10.16):**
1. `_read_card_probe_state` behält Profil-ID bei `card_model_id`-Redirect oder `-thinking`-Suffix (`scripts/core/unified_runner.py:170`).
2. Per-Profil-Card-State unter `tooluse_runs.{profile_id}` (nested statt flat) — `update_model_card_tooluse_fields(model_id, profile_id, ...)` in `utils/model_utils.py:1594`.
3. Path B schreibt Card nach Aggregation — `_write_card_from_aggregated_row` in `scripts/core/tooluse_exporter.py:431`.
4. Migration-Script `scripts/dev/migrate_tooluse_runs_nested.py` konvertiert flache Top-Level-Felder in nested.
5. Regression-Test `tests/test_supports_tool_use_tri_state.py::TestUpdateModelCardTooluseFields::test_dual_profile_persistence` als Lock gegen Wiederholung.

**Card-Schema (neu):**
```json
{
  "supports_tool_use": true,
  "tooluse_runs": {
    "qwen3_6-27B": {"tested_at": "...", "score_p1": 72.5, "score_p2": 56.67},
    "qwen3_6-27B-thinking": {"tested_at": "...", "score_p1": 19.17, "score_p2": 22.5}
  }
}
```

**Lessons Learned:**
- **Card-First-Vertrag ist heikel bei Shared Cards:** Wenn `card_model_id`-Redirect aktiv ist, MUSS die Card-Lookup-Funktion den Profil-Identifier als Input-Argument durchreichen, sonst kollabieren alle Profile zur Basis.
- **Path B muss Card syncen:** Aggregations-Pfad ist der einzige aktive Write-Pfad für Tool-Use-Tests. Card-Update darf nicht nur im deprecated Path A leben.
- **Nested statt flat für Multi-Run-State:** Flache Felder mit Suffix-Schema (`_p1_thinking`) skalieren nicht. Nested-Dict mit Profil-ID als Key ist die einzige Lösung, die mit `card_model_id`-Redirect harmoniert.

**Verifikation:** 105 Modelle nach Re-Aggregation korrekt persistiert; 107 Cards via Migration konvertiert. `qwen3_6-27B-thinking` hat jetzt eigenen Leaderboard-Eintrag (19.92% combined) und Card-State. Test-Sweep: 1126 passed, 1 pre-existing failure (qwen3_5-35b-a3b-q8).

---

## Path B überschreibt Capability-Flag mit Mock-Test-Result (2026-07-10)

**Symptom:** Nach v4.10.16 Path-B-Aggregation zeigen Karten wie `openai_gpt-oss-20b.json` und `command-a-plus-05-2026.json` plötzlich `supports_tool_use=false`, obwohl die Capability im Card-Setup `true` war. Ursache war ein Mock-Run mit p1=0 (kein echter Tool-Server) — Path B interpretierte das als empirische Verifikation "kann keine Tools".

**Root Cause:** `_write_card_from_aggregated_row()` (`scripts/core/tooluse_exporter.py:443`) leitete `supports_tool_use` heuristisch aus `p1 > 0` ab und reichte diesen Wert an `update_model_card_tooluse_fields()` weiter. Dieser Helper unterschied nicht zwischen Capability-Aussage und Test-Result.

**Fix (v4.10.16+):**
- `update_model_card_tooluse_fields(..., preserve_supports_tool_use: bool = False)` — neuer Parameter. Bei `True` wird der bestehende `supports_tool_use`-Wert der Card unverändert gelassen.
- Path B reicht `preserve_supports_tool_use=True` durch. Setzt nur `tooluse_runs.{profile_id}` und schreibt keine Capability-Aussage.
- Path A (`finalize_model`) bleibt unverändert: überschreibt das Flag weiterhin mit Test-Result (empirische Verifikation).
- Repair-Script (`repair_tooluse_card_fields.py`) respektiert jetzt bestehende `true`/`false`-Werte und fixt nur `null`/`"untested"`-Cards.

**Kardinalregel:** `supports_tool_use` ist Capability-Flag, NICHT Test-Result. Test-Result lebt in `tooluse_runs.{profile_id}.tested_at` + Score-Feldern. Ein Mock-Run oder fehlgeschlagener Real-Test bedeutet nicht "Modell kann keine Tools", sondern nur "dieser spezifische Test hat p1=0 produziert".

**Regression-Tests:**
- `tests/test_supports_tool_use_tri_state.py::test_preserve_supports_tool_use_keeps_capability` — Capability=True bleibt nach p1=0-Run
- `tests/test_supports_tool_use_tri_state.py::test_preserve_false_keeps_capability` — Capability=False bleibt nach beliebigem Run
- `tests/test_supports_tool_use_tri_state.py::test_no_preserve_overwrites_capability` — Path A-Verhalten bleibt korrekt
