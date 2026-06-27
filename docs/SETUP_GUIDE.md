# Konfiguration & Setup-Anleitung

**Zielgruppe:** Alle, die CrucibleMark erstmalig einrichten oder die zentrale Konfiguration anpassen wollen.
**Inhalt:** Hardware-Profil, Provider & API-Keys, LLM-Judge-Konfiguration, Modul-Auswahl

> **Voraussetzung:** Python 3.10+ und venv eingerichtet (siehe README):
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> pip install -r requirements.txt
> ```

Diese Anleitung beschreibt, wie CrucibleMark nach der Installation exakt auf die eigene Hardware und spezifische Anforderungen (Provider, Module, Modelle) zugeschnitten wird.

Wenn `benchmark_config.yaml` noch nicht existiert, kopiere die Vorlage manuell: `cp benchmark_config.example.yaml benchmark_config.yaml`. **Diese Datei ist der zentrale Steuerungshebel für Laufzeit- und Benchmark-Parameter. Sie steht in `.gitignore` und landet nicht im Repository.**

Die **Provider-Konfiguration** (Modell-Listen, API-Keys-Env-Vars, Provider-Flags) liegt getrennt in `config/provider_config.yaml`. `ConfigValidator` merged beide Dateien beim Start transparent — alle Scripts sehen ein einheitliches Config-Objekt. Beim Merge prüft das System automatisch auf doppelte Modell-IDs und gibt eine `WARNING` aus, falls eine ID in mehreren Providern auftaucht (First-Win-Semantik).

Wenn eine Einstellung fehlt oder das System mit „Runtime Errors" abstürzt, liegt das meist an fehlenden API-Credits, zu kleinen Kontext-Fenstern oder falschen Provider-Aktivierungen. Gehe die folgenden vier Schritte durch.

---

## Schritt 1: Das Hardware-Profil aktivieren

Nicht jede Maschine kann jeden lokalen Benchmark flüssig verarbeiten. In der Sektion `runner_environment` wird das primäre Hardware-Profil (`active_profile`) festgelegt.

```yaml
runner_environment:
  active_profile: "apple_silicon_m4"  # Ändere dies z. B. zu "nvidia_rtx4090"
```

Mit einer dedizierten Nvidia-Grafikkarte (`nvidia_rtx4090`) trägt man den Namen exakt so ein, wie er unter `profiles:` in der YAML-Liste steht.

---

## Schritt 2: Provider & API-Keys hinterlegen

Alle Provider und ihre Kategorien (Commercial, Open-Weights Cloud, Local) sind dynamisch als Single Source of Truth in `config/provider_config.yaml` hinterlegt (unter der Sektion `providers`). Wer einen neuen Anbieter nutzen möchte (z. B. `together_ai`), fügt diesen nur dort zur entsprechenden Kategorie hinzu. So werden die Provider auch fehlerfrei im Leaderboard klassifiziert (Details unter [MODEL_CLASSIFICATION.md](MODEL_CLASSIFICATION.md)).

Die Benchmarks nutzen API-Schnittstellen für kommerzielle Modelle oder Cloud-gehostete Open-Weights-Modelle. Nicht jeder Provider muss aktiviert werden.

1. **Provider einrichten:** Die aktuellen Listen finden sich in `config/provider_config.yaml` unter `providers.commercial`, und `providers.local`. Die Listen werden nach Bedarf angepasst.
2. **API-Schlüssel:** API-Keys werden **nicht** in der YAML-Datei hinterlegt. Sie werden direkt in eine `.env`-Datei im Hauptverzeichnis eingetragen:

```env
# .env Datei im CrucibleMark-Hauptverzeichnis
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIzaSy...
MISTRAL_API_KEY=...
OPENROUTER_API_KEY=sk-or-...
```

> **OpenRouter Free Tier:** Free-Tier-Modelle (Modell-ID-Suffix `:free`, z. B. `google/gemma-4-31b-it:free`) nutzen denselben Endpoint und denselben API-Key — kein gesonderter Zugang nötig. Der `:free`-Suffix allein reicht; CrucibleMark wählt automatisch das passende Rate-Limit-Profil (18 RPM statt 60 RPM). Verfügbare Free-Tier-Modelle sind in `config/provider_config.yaml` als Kommentar hinterlegt und können bei Bedarf aktiviert werden.

### Lokale Modelle: 2 Betriebsarten (On-Device vs. Intranet)

CrucibleMark unterstützt unter `config/provider_config.yaml → providers.local` zwei Arten von "lokal":

- **Lokal auf derselben Maschine (On-Device):** `llamacpp`
- **Lokal im Intranet (Remote-Host, aber eigener Betrieb):** `llamacpp_spark`

Dazu kommt optional:

- **`ollama_local`** — `auto_discover: true`, listet laufende Ollama-Modelle automatisch

#### Vergleich: Mac lokal vs. Spark Intranet

| Kriterium | `llamacpp` (Mac, lokal auf gleicher Maschine) | `llamacpp_spark` (Intranet, DGX via SSH) |
| :--- | :--- | :--- |
| Laufort des `llama-server` | Auf dem Benchmark-Host (Mac) | Auf Remote-Intranet-Host (Spark) |
| Steuerung | Direkter lokaler Prozessstart | SSH-Kommandos (`server_start_cmd` / `server_stop_cmd`) |
| `base_url` | `127.0.0.1:<port>/v1` | `http://<intranet-ip>:<port>/v1` |
| `bind_host` (empfohlen) | `127.0.0.1` | `0.0.0.0` |
| Modellwechsel | Stop + Start lokal | Start nur für den eigenen Endpoint; fremde aktive Endpunkte werden nicht überschrieben |
| Fremder aktiver OpenAI-Endpunkt | lokal separat behandeln | Warnung + sauberer Abbruch statt Stop/Overwrite |
| Readiness-Check vor Benchmark | Health + kurzer Probe-Request (`Hallo`) | Health + kurzer Probe-Request (`Hallo`) |
| Ready-Timeout (empfohlen) | kurz (lokal) | länger für große Modelle (`server_ready_timeout_sec`) |
| End-of-Run Cleanup | optional | empfohlen: `cleanup_on_exit: true` + `server_post_stop_cmd` |
| Typischer Einsatz | Desktop-Workflows, Single-Host | zentrale Intranet-GPU für Fleet-Runs |

#### 1) `llamacpp` (Mac, lokal-lokal)

`llamacpp` ist der klassische On-Device-Connector auf derselben Maschine wie der Benchmark-Runner.

- **Start/Load:** Der Connector baut den vollständigen `llama-server`-Befehl aus der Config und lädt das gewünschte GGUF-Modell.
- **Modellwechsel:** Bei Modellwechsel wird der laufende Server gestoppt und mit neuem Modell neu gestartet.
- **Readiness:** Ein Modell gilt erst als bereit, wenn Health-Endpunkt plus kurzer Probe-Request (`Hallo`) erfolgreich sind.
- **Typische Konfig-Felder:** `base_url`, `server_start_cmd`, `server_stop_cmd`, `server_log`, `model_dir`, `bind_host`; pro Modell `id`, `model_file`, `n_gpu_layers` (+ optional `context_length`).

#### 2) `llamacpp_spark` (Intranet-Lokal via SSH)

`llamacpp_spark` ist für einen dedizierten Intranet-LLM-Server (DGX Spark). Der Benchmark läuft lokal auf dem Mac, steuert den Server aber remote.

- **Transport:** Steuerung über SSH (`server_start_cmd` / `server_stop_cmd` sind SSH-Kommandos).
- **Load/Unload:** Das Modell wird per Remote-`llama-server` mit Alias geladen. Ein bereits fremd laufender OpenAI-kompatibler Endpoint auf derselben `base_url` wird nicht automatisch gestoppt oder überschrieben.
- **Readiness vor Benchmark:** Auch hier gilt erst "bereit", wenn Health und kurzer `Hallo`-Probe-Request erfolgreich sind.
- **Timeouts:** Für große Modelle sind provider-spezifische Ready-Timeouts konfigurierbar (`server_ready_timeout_sec`, `server_ready_poll_sec`, `server_ready_probe_timeout_sec`).
- **End-of-Run Cleanup:** Optional automatischer Abschluss-Cleanup (`cleanup_on_exit: true`) mit
  - Server-Stop (`server_stop_cmd`)
  - optionalem Cache-Clear (`server_post_stop_cmd`, z. B. `~/.cache/llama.cpp`, `/tmp/llama.cpp*`).

Seit v4.3.0 wird dieser Cleanup auch im `UnifiedBenchmarkRunner` per `finally` erzwungen. Das gilt sowohl für erfolgreiche Läufe als auch für manuelle Abbrüche (z. B. `Ctrl+C`).

#### Benötigte Spark-Config-Keys

Für den konsolidierten `llamacpp_spark`-Betrieb werden typischerweise nur diese Felder benötigt:

- Verbindungs- und Startdaten: `base_url`, `api_key`, `model_dir`, `server_start_cmd`, `server_stop_cmd`
- Readiness: `server_ready_timeout_sec`, `server_ready_poll_sec`, `server_ready_probe_timeout_sec`
- Laufzeit: `server_log`, `bind_host`, `threads`, `parallel`, `hardware_profile`
- Abschluss-Cleanup: `cleanup_on_exit`, `server_post_stop_cmd`
- Modelle: pro Modell `id`, `name`, `model_file`, `n_gpu_layers`

**Per-Modell Token-Management (ab Session 26):**

Jedes Spark-Modell sollte drei zusätzliche Felder haben:

| Feld | Zweck | Beispiel |
|---|---|---|
| `context_length` | Server-Kontextfenster (`--ctx-size`) | `32768` |
| `max_tokens` | Output-Cap pro Anfrage (HTTP) | `16384` |
| `read_timeout` | httpx Read-Timeout (Provider-Level) | `2400` |

**Zusammenhang:**
- `context_length` = Input + Output gemeinsam (KV-Cache)
- `max_tokens` = nur Output (darf nicht > `context_length` sein)
- `read_timeout` ≥ `max_tokens / tokens_per_second × 1.5`
- `parallel` = gleichzeitige Slots (KV-Cache-Multiplikator); `2` für Benchmark, `1` für Hybrid-Attention

Ohne `max_tokens`-Cap generiert das Modell bis zum Kontextfenster → HTTP-Timeout-Loop. Details: `docs/DEVELOPER_GUIDE.md` → "Spark: Token-Management pro Modell".

Frühere Lifecycle-Schalter wie `always_stop_before_start` sind im aktuellen Connector-Stand nicht mehr erforderlich.

#### Verbindungsbesonderheiten bei Spark (SSH)

- SSH muss non-interaktiv funktionieren (BatchMode/Key-basierter Zugriff empfohlen), sonst blockiert der Runner beim Modellstart.
- Der Remote-Binary-Pfad in `server_start_cmd` muss exakt dem installierten `llama-server` auf dem Spark entsprechen.
- `bind_host` und `base_url` müssen zusammenpassen (z. B. `0.0.0.0` auf dem Spark, Zugriff via Intranet-IP).
- Wenn unter `base_url` bereits ein anderer OpenAI-kompatibler Server läuft, gibt der Connector nur eine Warnung aus und beendet den Benchmark-Lauf sauber.

Alle lokalen Provider haben ein `enabled`-Flag. Ist es `false`, erscheint der Provider nicht im Wizard und nicht im Cross-Model-Benchmark.

---

## Schritt 3: LLM Judge & Meta-Reviewer konfigurieren

Weil CrucibleMark textbasierte Soft-Skill-Vergleiche vornimmt, nutzt das System einen „Meta-Judge" – ein starkes externes Modell, das die Antworten der Kandidaten auswertet und Punkte vergibt.

In der Sektion `llm_judge:` wird festgelegt, welcher Richter verwendet wird. **Anthropic** (mit `claude-haiku`-Modell) oder **Google** (mit `gemini-pro`) sind sehr empfehlenswert. Wer keinerlei API-Kosten generieren will, kann auch ein lokales Ollama-Modell als Judge angeben (z. B. `ministral-3:14b`). Das beansprucht jedoch erheblich mehr Zeit und Kontextfenster.

```yaml
llm_judge:
  enabled: true
  provider:
    name: anthropic
    model: claude-haiku-4-5-20251001
    max_tokens: 8192
```

---

## Schritt 4: Benchmarking-Module auswählen

Nicht alle Test-Module sind für jeden Anwendungsfall relevant. Im Feld `modules` am Ende der `benchmark_config.yaml` wird exakt festgelegt, welche Eigenschaften evaluiert werden sollen.

Für einen schnellen ersten Test empfiehlt sich, nur Code Quality (`coding`), CLI Benchmark (`cli_benchmark`) oder logisches Verständnis (`reasoning`) auf `enabled: true` zu lassen. Soft-Skills (UX-Writing, Cultural Intelligence u. a.) lassen sich zunächst ausklammern.

| Disziplin | Typ | Ziel des Moduls |
| :--- | :--- | :--- |
| **`code_quality`** | Hard Skill | Testet sauberes, deterministisches Programmieren und Code-Erklärung. |
| **`cli_benchmark`** | Hard Skill | Prüft den Umgang mit der Kommandozeile und Terminal-Skripten. |
| **`reasoning`** | Metrik | Kognitiver Stresstest (Logikrätsel, Chain-of-Thought, Systemfehler). |
| **`ux_writing`** | Soft Skill | Testet die Erstellung von UI-Texten, Warnungen und nutzerzentrierter Führung. |
| **`documentation_quality`** | Soft Skill | Analysiert, wie gut APIs, README-Dokumente oder Code dokumentiert werden. |
| **`content_transformation`** | Soft Skill | Ermittelt die Adaptionsfähigkeit von Sprache (Tone of Voice und Zielgruppenwechsel). |
| **`cultural_intelligence`** | Metrik | Bewertet interkulturelle Nuancen, Empathie und Übersetzungspräzision im Kontext. |
| **`political_compass`** | Spezial | Ermittelt die ideologische Ausrichtung (Bias) des Modells anhand politischer Thesen. |

```yaml
  content_transformation:
    path: "benchmark_modules/content_transformation"
    enabled: false
```

Einzelne Module lassen sich auch dann via CLI aufrufen, wenn sie global deaktiviert sind: `make benchmark MODULE=code_quality`.

Nach diesen vier Schritten ist die Konfiguration abgeschlossen und der erste Testlauf kann starten.
