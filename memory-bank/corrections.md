# Corrections

Dokumentierte Fehler, Korrekturen und Modell-spezifische Verhaltens-Anomalien,
die in zukünftigen Sessions erkannt werden müssen, ohne die Diagnose zu wiederholen.

---

## Anthropic: Safety-Refusals bei Opus 5 (2026-08-19)

**Befund:** Claude Opus 5 produziert für bestimmte harmlose Code-Review-Tests einen
Safety-Refusal (`finish_reason="refusal"`), obwohl die Aufgabe inhaltlich unverfänglich ist.

**Beispiel 1:** `benchmark_modules/reasoning_logic/assets/asset_5a_error_recovery.yaml`
(Reasoning 5A: Code Logic Debugging — "Infinite Loop Detection"). Prompt enthält die
Schlüsselbegriffe "freeze", "hangs", "infinite loop", "invalid". Opus 5 refuset
mit `finish_reason="refusal"`, leerem Content, `output_tokens=0`.

**Beispiel 2:** `benchmark_modules/reasoning_logic/assets/asset_5e_nested_paradox.yaml`
(Reasoning 5E: The Nested Transaction Paradox). Distributed-Systems-Architektur-Frage
mit den Schlüsselbegriffen "transaction commit", "async operations", "blocking",
"cleanup jobs". Identisches Symptom (`finish_reason=refusal`, `output_tokens=0`),
anderes Prompt-Pattern — stützt die Hypothese, dass Opus 5 **mehrere**
Code-/System-Patterns triggert (nicht nur ein einzelnes Schlüsselwort-Muster).

**Vergleich Opus 4.7 auf demselben Test:** `percentage=81%`, `tokens_used=1405`,
`finish_reason="end_turn"` → kein Refusal. Verhalten ist **modell-spezifisch**, nicht
test-spezifisch.

**Hypothese:** Anthropic hat die Safety-Filter der Opus-5-Generation strenger kalibriert
als in Opus 4.x. Bestimmte Schlüsselbegriff-Muster (Code mit "endless loop", "freeze",
"hangs") triggern den Filter, obwohl die Aufgabe ein Standard-Code-Review ohne
Boshaftigkeit ist.

**Folge für den Benchmark:**
- Tests mit solchen Pattern-Begriffen können für Opus 5 nicht ausgewertet werden
  (`refusal_flag=true`, `percentage=0`, `judge_progress_status="⚠️ Judge: skip"`).
- Cross-Modell-Vergleiche bleiben valide — die anderen Modelle (Sonnet 4.5/4.6/5,
  Opus 4.5/4.6/4.7/4.8) zeigen das Verhalten nicht.
- Leaderboard-Aggregation mittelt das konsequent; keine Korrektur nötig.

**Was NICHT zu tun ist:**
- Test-Prompts nicht umformulieren, um den Refusal zu umgehen — das wäre ein
  Bias und würde Cross-Run-Vergleichbarkeit zerstören.
- Connector nicht ändern, um `think_content` als Fallback zu nutzen — der
  Refusal ist eine bewusste Modell-Entscheidung, kein technischer Defekt.

**Connector-Stand:** `utils/providers/anthropic.py:152-160` macht bei
`stop_reason == "refusal"` `return ""`. `think_content` wird zwar via
`_extract_think_content(response.content)` extrahiert, aber durch den frühen
`return ""` verworfen (landet nur in `last_response_metadata`, nicht in
ExecResult/CSV). Das ist akzeptiert — die fehlende Sicht auf den Thinking-Trace
ist eine bewusste Konsequenz der Refusal-Behandlung.

**Verifikations-Datum:** 2026-08-19 (zweiter Fall 5E am gleichen Tag bestätigt)

---

## Anthropic: `temperature` deprecated für Opus 5 / Sonnet 5 / Opus 4.7+ (2026-08-19)

**Befund:** API liefert HTTP 400 — `invalid_request_error — 'temperature' is deprecated for this model`.

**Ursache:** Adaptive Thinking (alle Modelle ab Opus 4.7, Sonnet 4.6, alle 5er) deprecated den `temperature`-Parameter.

**Lösung:** `claude-opus-5` in `utils/constants.py:ANTHROPIC_NO_TEMPERATURE_MODELS` ergänzt.
Der Connector prüft diese Liste in `utils/providers/anthropic.py:124` und überspringt
`temperature` für gelistete Modelle.

**Pflege:** Bei jedem neuen Anthropic-Modell mit Adaptive Thinking MUSS die Liste erweitert
werden — sonst 400-Fehler bei allen API-Calls (ThinkingProbe + Benchmark).

**Verifikations-Datum:** 2026-08-19

---

## OpenRouter: „Budget/Quota erschöpft" als False Positive bei HTTP 400 thinking_budget (2026-08-28)

**Befund:** Benchmark-Abbruch qwen/qwen3.8-flash (ux_writing u.a.) mit „💸 Budget/Quota erschöpft!" trotz ausreichender OpenRouter-Credits (~$12.70 Rest verifiziert).

**Ursache (zweifach):** (1) Der Alibaba-Upstream lehnt Requests mit `thinking_budget >= max_completion_tokens` strikt ab — Modul-Budget (12000) == Reasoning-Cap (12000) → HTTP 400 `invalid_parameter_error` („max_completion_tokens [12000] must be greater than thinking_budget [12000]"). (2) Der Budget-Fast-Fail in `utils/providers/base.py` matchte per Substring; `thinking_budget` enthält `budget` → der Parameter-Fehler wurde als Budget-Erschöpfung fehlklassifiziert. Die Frühdiagnose „transienter Upstream-Fehler" war falsch: Die 429-Rate-Limits des Alibaba-Shared-Pools sind real (~40% der Test-Requests), aber nicht abort-ursächlich.

**Lösung:** `_clamp_reasoning_budget()` (openrouter.py) reduziert das Reasoning-Cap auf `req_tokens // 2`, nur wenn die Invariante verletzt wäre; Budget-Erkennung (base.py) auf Word-Boundary-Regex + `status_code == 402` umgestellt; der Fast-Fail loggt jetzt den Original-Fehlertext (erste 300 Zeichen).

**Pflege:** Bei scheinbaren Budget-Abbrüchen immer den Original-Fehler im Log prüfen (seit 2026-08-28 mitgeloggt). Module mit 12000-Budget laufen qwen3.8-flash mit reduzierten 6000 Reasoning-Tokens — ausreichend, bei Score-Auffälligkeiten Modul-Budget oder Cap adjustieren.

**Verifikations-Datum:** 2026-08-28 (Live-Repro 12000/12000 → HTTP 400, 12000/6000 → OK; 45 Tests grün, Ruff clean)

---
## llama.cpp Mac ↔ Spark: Separation brach außerhalb der Connectoren (2026-08-28)

**Befund:** benchmark-auto konnte mit gleichzeitig aktiviertem Mac-llama.cpp und GX10-Spark-llama.cpp die Provider nicht trennen; die 3 kanonisch kollidierenden Spark-Modelle (`qwen3_5-4b-q4`, `qwen3_5-4b-q8`, `qwen2_5-coder-7b`) wurden kommentarlos als „bereits benchmarked" übersprungen (alte Mac-Rows in derselben CSV). Workaround war, den Mac-Provider zu deaktivieren.

**Ursache (vierfach, alle außerhalb der Connector-Klassen):** (1) `get_existing_results()` cachte `(model, asset)`-Keys provider-blind; `canonical_lookup_keys()` normalisiert Dot↔Underscore, sodass Mac `qwen3.5-4b-q8` und Spark `qwen3_5-4b-q8` identische Keys erzeugen — auch Political-Compass (`provider_type`-Spalte) war betroffen. (2) `resolve_provider()` matchte config_form-Bridge im ersten Provider-Treffer → Spark-IDs routeten zum Mac (Config-Reihenfolge). (3) `_detected_matches_model()` matchte bidirektional per Substring → `gemma-4-e4b` adoptierte `gemma-4-e4b-spark`. (4) `start_server()` Konfliktpfad rekursierte endlos bei unkillbarem Konflikt-Endpoint (VS-Code-Port-Forward Mac:1235→GX10:1234, live reproduziert 2026-08-28: Code Helper PID 22404 auf 127.0.0.1:1235).

**Lösung:** (1) `get_existing_results(..., provider_key=)` filtert Benchmark- und Political-Compass-Zeilen provider-scoped (Alias-normalisiert via `_PROVIDER_ALIAS_MAP`); llamacpp-/vllm-/ollama-Batches in benchmark_auto.py übergeben ihren provider_key. (2) `_resolve_provider_from_config()` zwei Durchläufe: exakte Config-ID über alle Provider zuerst, config_form-Bridge danach. (3) `_detected_matches_model()` strikte normalisierte Gleichheit. (4) `_conflict_retry`-Guard terminiert den Konflikt-Restart; `_port_listener_output()`/`_local_endpoint_owned_by_llama_server()` (lsof-Ownership) + `_foreign_process_owns_port()` (Pre-Bind-Check im Cold-Start: fremd belegter Port → Fail-Fast <1s statt 180s Timeout). Pfad 2/4 zur CC-Entlastung in `_adopt_running_server`/`_adopt_matching_model`/`_cold_start_server` aufgeteilt.

**Pflege:** Beide llama.cpp-Provider können jetzt gleichzeitig aktiviert sein; künstliche ID-Unterscheidung (Underscores/-spark-Suffix) ist nicht mehr die Trennursache, bleibt aber aus Card-/CSV-Konsistenz bestehen. Vor einem Mac-Batch muss der VS-Code-Port-Forward auf 1235 entfernt werden — der Connector meldet das jetzt Fail-Fast. Ursache des Forwards identifiziert (2026-08-28): Die NVIDIA-Sync-App (`com.nvidia.nvidia-sync`) hält die llama-server auf der GX10 (Ports 1234+1235) am Leben; das VS-Code-Remote-Fenster (ssh-remote+Asus_Ascent_GX10) auto-forwardiert diese Remote-Ports — Remote:1234 landet lokal auf 1235, weil lokal 1234 vom Mac-Preset-Server belegt ist (Remote:1235 → lokal 1236). Prozedur (Entscheidung Laguna 2026-08-28): Vor Mac-Testläufen NVIDIA Sync manuell deaktivieren; Forward-Setup und Mac-Port 1235 bleiben unverändert. `run_score_benchmark.py` nutzt weiterhin den provider-blinden Cache (bewusst, gemischte Modell-Listen).

**Verifikations-Datum:** 2026-08-28 (37 Separation-Tests + 96 kombiniert grün; Live-Check echte CSV: Spark-Assets offen, Mac-Assets gecached; Routing `qwen3_5-4b-q8`→llamacpp_spark, `qwen3.5-4b-q8`→llamacpp; Full Suite 1591 passed, 2 Card-Fehler sind Bestand)

---
## llama.cpp Spark via Metrics-Proxy: base_url :2234, Bearer-Probes, server_port-Override (2026-08-28)

**Setup:** Der Spark-llama.cpp-Provider läuft seit 2026-08-28 durch den authentifizierenden `metrics_proxy` (Python, GX10 :2234, Bearer aus `LLAMA_PROXY_BEARER_TOKEN`), damit die generierten Tokens des Benchmarks erfasst werden. `base_url` zeigt auf den Proxy; der llama-server selbst bindet weiter :1234.

**Pitfalls (beide hätten die Proxy-Umstellung gebrochen):** (1) `_is_healthy()`/`_query_active_model()` sendeten keinen Authorization-Header — der Proxy verlangt Bearer auf ALLEN Pfaden (401), der Connector hätte einen laufenden Server permanent für down gehalten und endlos Cold-Starts versucht. (2) `_build_server_cmd()` leitet `--port` aus der `base_url` ab — ohne Override hätte der SSH-Start den llama-server auf :2234 starten wollen und mit dem Proxy kollidiert (180s Readiness-Timeout).

**Lösung:** `_auth_headers()` (Bearer aus `api_key`) auf allen Probes — harmlos für direkte llama-server ohne `--api-key`; neuer config-getriebener `server_port`-Override in `_build_server_cmd()` entkoppelt Bind-Port (:1234) von der base_url (:2234). Config: `server_port: 1234` im llamacpp_spark-Block; `server_stop_cmd` (pkill `--port 1234`) unverändert gültig.

**Pflege:** Proxy-Token steht bewusst direkt in provider_config.yaml (lokales Infrastruktur-Token `sk-local-mg2026`, kein Cloud-Secret). Bei Proxy-Port- oder Token-Änderung: `base_url`/`api_key` UND Proxy-Env (`LLAMA_PROXY_BEARER_TOKEN`) synchron halten. Der Token-Capture funktioniert nur, wenn der Benchmark-Traffic durch :2234 fließt — direkte Calls auf :1234 umgehen die Erfassung.

**Verifikations-Datum:** 2026-08-28 (Live: /health 200, Adoption 0,4s, Query 'OK' via Proxy; 41 Separation-Tests grün, Ruff clean)
