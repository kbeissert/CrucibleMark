# AGENTS.md

> Projektweite Anweisungen für Kilo und andere AI-Agenten. Diese Datei ist die generische SSoT für Arbeitsweise, Architektur und Sicherheitsregeln.
> Dynamischer Projektstatus steht in `memory-bank/`.

## Projekt

CrucibleMark ist ein modulares LLM-Benchmark-Framework für Python 3.12. Es testet AI-Modelle gegen praxisnahe Aufgaben, bewertet Antworten blind über einen unabhängigen LLM-Judge und generiert Leaderboards.

**Stand:** v5.3.0 · 2026-09-16 · Production-Ready

## Session-Start

Vor jeder neuen Task diese Dateien lesen:

1. `memory-bank/activeContext.md` — aktueller Fokus und offene Punkte
2. `memory-bank/progress.md` — Release-Historie
3. `memory-bank/systemPatterns.md` — Architektur-Regeln, SSoT-Brücken und Pitfalls
4. `memory-bank/corrections.md` — dokumentierte Fehler/Korrekturen/modell-spezifische Anomalien

Regel: Nur aktive, ungelöste Themen als Baustelle melden. Abgeschlossene Integrationen, akzeptierte Known Limitations und BACKLOG-Items sind keine Baustellen.

## Quick Commands

```bash
make benchmark-auto            # Vollautomatischer Batch-Run
make lint                      # Lint-Gate (Ruff C901≤12 + Pylint E-Level) — make validate ist nur Asset-Check!
make validate-naming           # Naming-Validator (Publication-Gate)
make validate-csv              # CSV-Sanitizer
make test                      # Full Test Suite (pytest)
make leaderboard               # Leaderboard regenerieren
make tooluse-leaderboard       # ToolUse-Leaderboard aggregieren
make web-export                # Web-Export-Pipeline (Hard-Gate)
make web-export-dev            # Export ins Dev-Frontend (Warn-only)
make model-cards MODEL=<id>    # Neues Model-Card-Template
make probe-thinking MODEL=<id> # Thinking-Probe für ein Modell
make clean-model MODEL=<id>    # Modell vollständig entfernen
make mcp-start / mcp-stop      # Benchmark-MCP-Server starten oder stoppen
make docs-version-check        # Doku-Stempel-Drift prüfen
make docs-version-sync YES=1   # Doku-Stempel angleichen
```

## Architektur-Regeln (unverhandelbar)

1. **Separation of Concerns:** Measurement arbeitet autonom und ausfallsicher. Publishing arbeitet strikt offline.
2. **SSoT, DRY und SRP:** Eine Funktionalität gehört in ein Modul. Fail-Fast ohne versteckte Fallbacks. Import statt Duplikation.
3. **Config-Driven, No Magic Numbers:** Regeln, Zahlen und Limits stehen in YAML. Die zyklomatische Komplexität bleibt bei höchstens 12 (`ruff.toml`, C901).
4. **Anti-God-Script:** Logische Submodule auslagern. Hauptskripte bleiben schlank.

## Design-Constraints (nicht optimierbar)

- **Sequenzielle Modell-Abarbeitung:** Modelle einzeln nacheinander testen, Server zwischen Modellen neu starten und Cooldown einhalten. Nicht parallelisieren.
- **Judge-Reset zwischen Tasks:** Jede Bewertung ist ein frischer API-Call. Kein Judge-Caching.
- **Blind-Evaluierung:** Der Judge kennt die Modellnamen nicht.
- **Kein Judge-Fallback:** Anthropic-Overloads nur mit Exponential-Backoff-Retry behandeln. Nie ein anderes LLM als Ersatz-Judge verwenden.
- **Judge-Prompts unveränderlich halten:** Änderungen während laufender Tests brechen die Vergleichbarkeit.
- **Scoring-Logik nicht stillschweigend ändern:** Das verfälscht historische Benchmarks.
- **`vllm-start` nicht als idempotent behandeln:** Vor einem Modellwechsel den Server über `vllm-stop` stoppen. Die Details stehen in `memory-bank/reference/architecture.md`.
- **vLLM-Server nicht unnötig neu starten:** Der Start kann mehrere Minuten dauern. Während Diagnose und Tests gegen den laufenden Server arbeiten.
- **Reports als flüchtig behandeln:** Benchmark-Reports werden pro Lauf überschrieben. Verbindlich sind die versionierten Ergebnisdateien in `outputs/runs/`.
- **ToolUse-Leaderboard bereinigen:** `tooluse_leaderboard.csv` ist ein Upsert-File. Bei Modell-ID-Renames alte IDs vor der Aggregation entfernen.
- **Blacklist blockt nur den Web-Export:** `config/web_export_blacklist.yaml` wird von `benchmark-auto` nicht gelesen — ein Modell wirklich aus dem Batch nehmen heißt: zusätzlich seinen Entry in `provider_config.yaml` auskommentieren oder deaktivieren.
- **Dual-Profile-Expansion hat kein Ein-Profil-Opt-out (2026-09-23):** Ein Eintrag mit `enable_thinking: true` erzeugt Standard + `-thinking` aus EINER Config-Zeile — „nur ein Profil aus dem Batch nehmen" per Auskommentieren killt beide Profile; stattdessen Export-Seite filtern (Blacklist, Konvention: stärkstes Profil bleibt) oder bewusst auf ein Single-Profil migrieren (`chat_template_kwargs`).
- **`unknown`-Vendor-Cards erzeugen hängende `vendor_card_ref`s (Session 104):** Der Export filtert `unknown: true`-Cards aus `vendor_cards.json`, die Taxonomy setzt den `vendor_card_ref` am Modell aber trotzdem (Fall `agentionai`/signal-3-8-27b) — neue Hersteller-Cards also verifizieren (Flag aufheben, Konvention: `unsloth.json`) bevor die Taxonomy-Verknüpfung entsteht.
- **`save_results`-Simulationen nicht gegen echte CSVs laufen lassen:** `benchmark_scores/*.csv` ist gitignored — es gibt kein Git-Sicherheitsnetz für Benchmark-Daten. In Tests und Simulationen `config['output']` explizit auf Temp-Pfade umleiten.
- **Selektives Reasoning beachten:** Modelle, die selbst entscheiden, wann sie denken, dürfen keine Always-Thinking-Konfiguration erhalten. `enable_thinking: true` kann sonst eine falsche Dual-Profile-Expansion auslösen.
- **`# noqa: C901` nicht verwenden:** Die CC-≤-12-Regel bleibt verbindlich. Stattdessen Methoden nach Pfaden aufteilen.
- **File-level `# ruff: noqa: F401` nur in `__init__.py`:** In anderen Modulen verbirgt es tote Imports und Redefinitions. Stattdessen gezielte `# noqa: F401` an Re-Export-Zeilen oder gar keine verwenden.
- **Versions-Labels konsistent halten (Session 87):** Der Web-Export liest `model_version` pro Datenquelle (Leaderboard aus der Card, Political Compass aus `political_compass_results.csv`) — ein veraltetes `k.A.` in einer Ergebnis-CSV wird als Versions-Widerspruch auf der Modellseite sichtbar. `model_version`-Änderungen immer in Card UND allen Ergebnis-CSVs zusammen synchronisieren.
- **Card-Preise nur via Pricing-Table befüllen (Session 88):** `input_price_per_1m`/`output_price_per_1m` nie manuell in der Card setzen — erst `config/model_pricing.yaml` pflegen, dann `scripts/update_model_pricing.py` laufen lassen. Varianten-IDs brauchen dort exakte Keys (`…-thinking-…`, `…-pro`), sonst prefix-matched die Variante auf die Basis-ID und erbt deren Preis.
- **OpenRouter-Reasoning deckelt Output (Session 89):** OpenRouter rechnet Reasoning-Tokens gegen `max_tokens` — Thinking-Modelle mit nicht-terminierendem CoT verbrennen sonst das komplette Budget (0 sichtbarer Output). Per-Modell über `model_reasoning_config` (Unified-Parameter `reasoning.max_tokens`) deckeln; ein reiner `model_max_tokens`-Override reicht nicht.
- **Reasoning-Cap strikt unter dem Modul-Budget halten (2026-08-28):** Alibaba-Upstream (qwen3.8-flash) lehnt `thinking_budget >= max_completion_tokens` mit HTTP 400 ab — der Connector reduziert das Cap automatisch auf die Hälfte des Output-Budgets (`_clamp_reasoning_budget`). „Budget/Quota erschöpft"-Abbrüche können False Positives sein; der Original-Fehler wird seit 2026-08-28 im Fast-Fail-Log mitgeschrieben.
- **llama.cpp-Timeouts: zwei Keys, zwei Wände (2026-08-30):** Chat-Requests laufen über den OpenAI-Connector und lesen den Provider-Key `request_timeout` (Default 600 s) — `read_timeout` deckt nur die Server-Verwaltung ab. Zusätzlich hat der Metrics-Proxy auf der GX10 ein eigenes `request_timeout_s` (`/home/kay_beissert/ai/metrics/config/metrics-proxy.json`). Wird eine der beiden Wände nicht angehoben, livelockt jeder Task, der länger als das Cap rechnet: Retry startet die Generierung bei Null. Beide seit 2026-08-30 auf 2400 s für `llamacpp_spark`.
- **Card-`model_id` muss exakt der provider_config-ID entsprechen (2026-08-30):** `--SPRK`/`--VSPK` ist reine Dateinamen-Konvention — weicht der interne `model_id` ab, skippt der Batch das Modell still mit „no model_file configured" (Fall fable-fusion).
- **HTTP-Clients schließen statt fallen lassen (2026-08-31):** vLLM 0.27 nightly erkennt einen client-seitig abgebrochenen Request ohne TCP FIN nicht und generiert bis zum OS-Keepalive (~2 h) weiter — Connectoren schließen via `close()`-Kette (`LLMClient.close` + `atexit`, Override in vllm/llamacpp); `self._client = None` ohne `close()` ist ein Bug. Bei SIGKILL hilft nur der Server-Stop.
- **Judge-Kontext-Prädikat folgt dem effektiven Text (2026-09-17):** `reasoning_trace_context` greift seit dem Review-Fix bei jedem Denkblock im zur Bewertung übergebenen Text (`has_reasoning_channel`), nicht nur bei injiziertem `think_content` — Judge-Läufe von Inline-CoT-Modellen nach diesem Datum sind nicht 1:1 mit historischen vergleichbar (CHANGELOG [Unreleased]).
- **Kein Agent-Loop als Messgegenstand (2026-09-18):** CrucibleMark misst rohe LLM-Endpoints — der Hermes-Agentic-Track (Connector, Wizard-Typ „agentic", D6/D9-Hooks) wurde nach dem Erstlauf (Lift −7,82 = Profilverschiebung, Loop stript CoT) vollständig entfernt. Harness-Messung bräuchte ein eigenes Modul mit ausführungsverifizierten Deliverables; die generischen Reste (Sektions-Walk-SSoT, `token_param_name`-Passthrough, `reasoning_effort`-Erkennung, Kanal-Bias-Fix) sind bewusst behalten.
- **Anthropic-Streaming-Pfad: `max_tokens` + `text_delta` selbst setzen (2026-09-02):** `_execute_with_token_fallback` injiziert `max_tokens` nur im Non-Streaming-Pfad — der Streaming-Pfad muss das Pflicht-Argument selbst setzen und der Delta-Handler muss `text_delta` verarbeiten, sonst Totalausfall mit leerem Antworttext (Regression `60aad34c`, 5 Tage unentdeckt).
- **`make clean-model` bricht Card-abhängige Tests (2026-09-02):** `tests/test_resolve_canonical_model_id.py` (Marker `uses_real_cards`) löst Model-IDs via Card-Lookup auf — nach einer clean-model-Löschung brechen die Testfälle des gelöschten Modells (Fallback `_safe_name` statt namespaced/Card-ID). Gelöschte Modelle, die in Tests referenziert sind, dort durch ein aktives Modell ersetzen (Session 97: `qwen/qwen3-32b` → `qwen/qwen3.8-flash`).
- **PC-Token-Probe ist Card-First-automatisch (2026-09-03):** Hat die Model Card keinen Eintrag (`pc_profile` fehlt/null), führt der PC-Benchmark-Runner die Probe automatisch vor dem PC-Run aus (Hook in `utils/base_runner.execute_batch_module`, SSoT `benchmark_modules/political_compass/core/pc_probe_hook.py`) — analog Thinking-Probe vor dem Standard-Benchmark. `make probe-pc-budget` dient nur der manuellen Kalibrierung/Wiederholung. `PcProbeError` (Fast-Fail-Guard) → Benchmark läuft weiter ohne Card-Write (nächster Lauf wiederholt die Probe).
- **Bias-Report-Badges folgen der Reviewer-σ-Konvention (2026-09-03):** Die Schwellen der Sektion-2.5-Badges (Topic-Shift-σ) lesen aus `config.shadow_metrics` in `political_compass/config.yaml` und sind an `config/meta_reviewer_prompt.yaml` gekoppelt (σ < 1,5 stabil, σ > 2,0 Chaos) — Prompt-Konvention ändern heißt Config-Schwellen nachziehen (Fall c7d56979: Code triggerte 🚨 bei > 1,0).
 - **Size-Class folgt `params_total_b` — auch bei MoE (2026-09-09):** Das vollständige Modell muss in den RAM/VRAM geladen werden, aktive Parameter beschleunigen nur. Card-`size_class` wird vom Card-Validator gegen `config/classification_taxonomy.json#size_class.classification_rules` geprüft (Hard-Fail); die Kaskade (`model_size_class.py`) nutzt Card-params vor dem Name-Regex — nie `params_active_b` zur Tier-Einordnung einsetzen.
- **Frontier-Preisgrenze $50/1M Output = Hyper-Premium-Ausschluss (2026-09-24):** Modelle mit Output-Preis über $50/€50 pro 1M Tokens sind keine Frontier-Alltagsmodelle, sondern Frontier-Hyper-Premium-Modelle — philosophische Ausschlusskategorie für CrucibleMark: zu teuer für ernsthafte kommerzielle Anwendung, kein Benchmark-Testkandidat (Nutzer-Grundsatz; Beispiele: GPT-Pro-Tier $180/1M). Praktischer Test-Filter des Nutzers liegt zusätzlich bei 30 €/1M Output.
- **Frontier-Grenze 768B = Datacenter-Niveau (2026-09-14):** Frontier gilt nur noch für `params_total_b > 768B` (≈ 460 GB Q4 — über der 512GB-Single-Box-Klasse, z. B. Mac Studio Ultra) oder unbekannte Parameterzahl bei proprietären/API-only-Modellen. Open-Weights ohne `params_total_b` erzeugen eine Validator-WARN statt stillen Frontier-Fallbacks — Parameterzahl recherchieren und eintragen (Datenlücken-Regel). Migration Session 105: `scripts/dev/migrate_size_class_768b.py` (Preflight gegen laufende Benchmarks).
- **Card-Dateien mit leerem JSON-Diff, aber Git-Status `M` (2026-09-09):** Ursache war eine Writer-Divergenz (model_card_io ohne vs. card_utils mit Trailing-Newline) — Root Cause gefixt in c4c94a86, Normalisierung committet in f195763a. Tritt es trotzdem auf: erst die Quelle finden (neuer Writer-Divergenz-Fall), nicht blind restaurieren.
- **llama.cpp-Ports: `base_url` = Benchmark-Port, `server_port` = Server-Bind (2026-09-11):** Benchmarks laufen über den Metrics-Proxy (`base_url :2234`, mappt auf llama-server `:1234`). `server_port` auf die Proxy-Port zu setzen startet den Server kollidierend in den Proxy und lässt den Cold-Start erst nach 180 s Readiness-Timeout scheitern.
- **Mac-llama.cpp: Stop-Kommandos port-gescoped, Installation unter `~/ai/services` (2026-09-23):** Der Benchmark-Host (M4 MacBook) betreibt neben dem Benchmark-Server (:1235) eigenständige llama-server-Dienste (Dictation :1240, Embedding :1230) — `server_stop_cmd`/Cleanup nie mit blanket `pkill -f llama-server`, immer auf den Port filtern. Die llama.cpp-Installation liegt unter `~/ai/services/llama.cpp` (nicht `~/ai/llama.cpp`) — Start-Pfade in Provider-Configs dagegen prüfen.
- **OpenRouter-Modelle auf den Hersteller-Host pinnen (2026-09-22):** OpenRouter routet pro Request auf wechselnde Upstream-Hosts desselben Modells — deren Antwortstil variiert messbar (Sprachtreue, Reasoning-Verhalten, Format; Ursachenanalyse Leaderboard-Shift, `docs/reports/2026-09-22_leaderboard-shift-host-routing.md`). Regel: `provider_routing` in `config/provider_config.yaml` pinnt jedes Modell mit verfügbarem First-Party-Host auf den Hersteller (`allow_fallbacks: false` = Fail-Fast). Modelle ohne Hersteller-Host laufen bewusst im Pool (im Config-Kommentar dokumentiert). Der bedienende Host wird pro Request in der CSV-Spalte `upstream_provider` protokolliert — bei Auffälligkeiten zuerst diese Spalte prüfen, bevor eine Modell-Degradation vermutet wird. Gepinnte Läufe sind nicht 1:1 mit Pool-Läufen vor dem 22.09.2026 vergleichbar.
- **`BenchmarkResult` ist Pydantic — neue Metadaten-Felder immer zuerst im Schema deklarieren (2026-09-19):** Das Setzen undeklarierter Attribute (z. B. `exec_result.reasoning_reask`) wirft ValueError — still verwandelt in `„Test execution failed"`-Error-Rows (❌ 0.0 %), weil `_execute_test_with_timing` die Exception schluckt und `_process_single_test` die Meldung überschreibt. Symptom tritt erst auf, wenn der Code-Pfad feuert (hier: nur nach erfolgreichem Re-Ask).

## Security

- API-Keys niemals in Code, Logs, Kommentaren oder Git speichern. Ausschließlich `.env` verwenden.
- Lokale Proxy-Auth-Tokens (z.B. GX10-Metrics-Proxy) stehen ebenfalls in `.env` (seit 2026-08-31, Variable `DGX_AUTH_TOKEN`) — `provider_config.yaml` referenziert sie per `${DGX_AUTH_TOKEN}`-Syntax, die Connectoren lösen sie zur Laufzeit auf (`BaseProviderClient._resolve_env_ref`). Keine Tokens mehr im Git.
- `.env` muss in `.gitignore` stehen. Vor jedem Commit prüfen.
- Tests dürfen keine Live-Endpoints aufrufen. Mocks verwenden.

## Datenschutz und API-Nutzung

- Datenschutzsensible Tasks bevorzugt mit europäischen oder lokalen Modellen ausführen.
- Öffentliche Cloud-Provider nur für nicht sensible Daten verwenden.
- Bei API-Fehlern standardmäßig Retry mit Exponential-Backoff einsetzen.
- Neue Prompts auf Token-Verbrauch prüfen und das Budget dokumentieren.

## Konfig-Hierarchie

1. `benchmark_config.yaml` — Token-Budgets, Module und Runner-Environment (SSoT für Modul-Aktivierung)
2. `config/provider_config.yaml` — Modelle, Provider, Hardware-Profile und Sampling
3. Modul-`config.yaml` — modulspezifische Einstellungen
4. `.env` — API-Keys außerhalb von Git
5. `config/web_export_blacklist.yaml` — Web-Export-Sperren

## Arbeitsweise für Agenten

- Bestehende Fixtures und SSoT-Funktionen wiederverwenden. Keine parallelen Sonderlösungen einführen.
- Den beschriebenen Auftrag bearbeiten. Kein unangefordertes Refactoring und kein Gold-Plating.
- Erklärungen kompakt halten und technische Entscheidungen direkt dokumentieren.
- Bei Problemen außerhalb des Scopes nur den Befund nennen. Nicht eigenständig den Scope erweitern.
- Vor Änderungen an laufenden Benchmarks die Race-Condition-Regel beachten: Core-Module während eines Runs nicht verändern.

## Memory-Bank vs. Kilo-Local-Memory

`memory-bank/` ist die **einzige Content-SSoT** für dauerhaftes Projektwissen und für alle Agenten sichtbar. Kilo-Local-Memory ist nur Index und Zeiger.

- Durable Inhalte wie Facts, Decisions, Corrections und Patterns → `memory-bank/systemPatterns.md` bzw. `memory-bank/progress.md`
- Kilo-Local-Memory → Session-Digests, dünne Zeiger sowie operative Pfade und Commands

## Referenzen

- [memory-bank/reference/architecture.md](memory-bank/reference/architecture.md) — SSoT-Brücken, BaseTest und Token-Budget
- [memory-bank/reference/code-style.md](memory-bank/reference/code-style.md) — Python 3.12, Type Hints, Verbote und Pytest-Fixtures
- [memory-bank/reference/data-pipeline.md](memory-bank/reference/data-pipeline.md) — CSV-Atomic-Writes, `save_results()` und Konsolidierung
- [memory-bank/reference/provider-models.md](memory-bank/reference/provider-models.md) — Provider-Konnektoren, Thinking und Model-Card-Workflow
- [memory-bank/reference/web-export-cleanup.md](memory-bank/reference/web-export-cleanup.md) — WebExport, Cleanup und Migration
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Layer-Architektur und Provider-Abstraktion
- [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) — Entwicklerhandbuch
- [CHANGELOG.md](CHANGELOG.md) — Vollständige Versionshistorie
