# Konfiguration und Setup

**Stand: v5.1.0 · 2026-07-14**

**Zielgruppe:** Alle, die CrucibleMark erstmalig einrichten oder die zentrale Konfiguration anpassen.
**Inhalt:** Hardware-Profil, Provider und API-Keys, LLM-Judge-Konfiguration, Modul-Auswahl.

> **Voraussetzung:** Python 3.10+ und venv eingerichtet (siehe [README.md](../README.md)):
> ```bash
> python3 -m venv .venv
> source .venv/bin/activate
> pip install -r requirements.txt
> ```

Diese Anleitung beschreibt, wie CrucibleMark nach der Installation auf die eigene Hardware und spezifische Anforderungen (Provider, Module, Modelle) zugeschnitten wird.

Wenn `benchmark_config.yaml` noch nicht existiert, die Vorlage kopieren:

```bash
cp benchmark_config.example.yaml benchmark_config.yaml
```

Diese Datei ist der zentrale Steuerungshebel für Laufzeit- und Benchmark-Parameter. Sie steht in `.gitignore` und landet nicht im Repository.

Die Provider-Konfiguration (Modell-Listen, API-Key-Env-Vars, Provider-Flags) liegt getrennt in `config/provider_config.yaml`. `ConfigValidator` merged beide Dateien beim Start transparent. Beim Merge prüft das System auf doppelte Modell-IDs und gibt eine Warnung aus, falls eine ID in mehreren Providern auftaucht (First-Win-Semantik).

Wenn eine Einstellung fehlt oder das System mit Runtime-Fehlern abbricht, liegt das meist an fehlenden API-Credits, zu kleinen Kontext-Fenstern oder falschen Provider-Aktivierungen. Die folgenden vier Schritte decken die Standardkonfiguration ab.

---

## Schritt 1 — Hardware-Profil aktivieren

Nicht jede Maschine kann jeden lokalen Benchmark flüssig verarbeiten. In der Sektion `runner_environment` wird das primäre Hardware-Profil (`active_profile`) festgelegt.

```yaml
runner_environment:
  active_profile: "apple_silicon_m4"  # alternativ: "nvidia_rtx4090"
```

Mit einer dedizierten Nvidia-Grafikkarte wird der Name exakt so eingetragen, wie er unter `profiles:` in der YAML-Liste steht.

---

## Schritt 2 — Provider und API-Keys hinterlegen

Alle Provider und ihre Kategorien (Commercial, Open-Weights Cloud, Local) stehen als Single Source of Truth in `config/provider_config.yaml` unter der Sektion `providers`. Wer einen neuen Anbieter hinzufügen möchte (etwa `together_ai`), trägt ihn dort in der entsprechenden Kategorie ein. Die Provider-Klassifikation im Leaderboard übernimmt sich automatisch (Details: [MODEL_CLASSIFICATION.md](MODEL_CLASSIFICATION.md)).

Die Benchmarks nutzen API-Schnittstellen für kommerzielle Modelle oder Cloud-gehostete Open-Weights-Modelle. Nicht jeder Provider muss aktiviert werden.

**Schritte:**

1. **Provider einrichten.** Die aktuellen Listen stehen in `config/provider_config.yaml` unter `providers.commercial` und `providers.local`. Listen nach Bedarf anpassen.
2. **API-Schlüssel.** API-Keys werden **nicht** in der YAML-Datei hinterlegt, sondern in einer `.env`-Datei im Hauptverzeichnis:

```env
# .env im CrucibleMark-Hauptverzeichnis
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIzaSy...
MISTRAL_API_KEY=...
OPENROUTER_API_KEY=sk-or-...
```

> **OpenRouter Free Tier:** Free-Tier-Modelle (Modell-ID-Suffix `:free`, etwa `google/gemma-4-31b-it:free`) nutzen denselben Endpoint und denselben API-Key — kein gesonderter Zugang nötig. Der `:free`-Suffix allein reicht; CrucibleMark wählt automatisch das passende Rate-Limit-Profil (18 RPM statt 60 RPM). Verfügbare Free-Tier-Modelle sind in `config/provider_config.yaml` als Kommentar hinterlegt.

### Lokale Modelle: zwei Betriebsarten

Unter `config/provider_config.yaml → providers.local` unterstützt CrucibleMark zwei Arten von "lokal":

- **Lokal auf derselben Maschine (On-Device)** — `llamacpp`
- **Lokal im Intranet (Remote-Host, eigener Betrieb)** — `llamacpp_spark`

Optional ergänzend:

- **`ollama_local`** — `auto_discover: true`, listet laufende Ollama-Modelle automatisch.

#### Vergleich: Mac lokal vs. Spark Intranet

| Kriterium | `llamacpp` (Mac, lokal auf gleicher Maschine) | `llamacpp_spark` (Intranet, DGX via SSH) |
|---|---|---|
| Laufort des `llama-server` | auf dem Benchmark-Host (Mac) | auf Remote-Intranet-Host (Spark) |
| Steuerung | direkter lokaler Prozessstart | SSH-Kommandos (`server_start_cmd` / `server_stop_cmd`) |
| `base_url` | `127.0.0.1:<port>/v1` | `http://<intranet-ip>:<port>/v1` |
| `bind_host` (empfohlen) | `127.0.0.1` | `0.0.0.0` |
| Modellwechsel | Stop + Start lokal | Start nur für den eigenen Endpoint; fremde aktive Endpoints werden nicht überschrieben |
| Fremder aktiver OpenAI-Endpoint | lokal separat behandelt | Warnung und sauberer Abbruch statt Stop/Overwrite |
| Readiness-Check vor Benchmark | Health und kurzer Probe-Request (`Hallo`) | Health und kurzer Probe-Request (`Hallo`) |
| Ready-Timeout (empfohlen) | kurz (lokal) | länger für große Modelle (`server_ready_timeout_sec`) |
| End-of-Run-Cleanup | optional | empfohlen: `cleanup_on_exit: true` + `server_post_stop_cmd` |
| Typischer Einsatz | Desktop-Workflows, Single-Host | zentrale Intranet-GPU für Fleet-Runs |

#### 1) `llamacpp` (Mac, lokal-lokal)

Der klassische On-Device-Connector auf derselben Maschine wie der Benchmark-Runner.

- **Start/Load:** Der Connector baut den vollständigen `llama-server`-Befehl aus der Config und lädt das gewünschte GGUF-Modell.
- **Modellwechsel:** Bei Modellwechsel wird der laufende Server gestoppt und mit neuem Modell neu gestartet.
- **Readiness:** Ein Modell gilt erst als bereit, wenn Health-Endpunkt und kurzer Probe-Request (`Hallo`) erfolgreich sind.
- **Typische Config-Felder:** `base_url`, `server_start_cmd`, `server_stop_cmd`, `server_log`, `model_dir`, `bind_host`. Pro Modell: `id`, `model_file`, `n_gpu_layers` (+ optional `context_length`).

#### 2) `llamacpp_spark` (Intranet-Lokal via SSH)

Für einen dedizierten Intranet-LLM-Server (DGX Spark). Der Benchmark läuft lokal auf dem Mac, steuert den Server aber remote.

- **Transport:** Steuerung über SSH (`server_start_cmd` / `server_stop_cmd` als SSH-Kommandos).
- **Load/Unload:** Das Modell wird per Remote-`llama-server` mit Alias geladen. Ein bereits fremd laufender OpenAI-kompatibler Endpoint auf derselben `base_url` wird nicht automatisch gestoppt oder überschrieben.
- **Readiness:** Erst bereit, wenn Health und kurzer `Hallo`-Probe-Request erfolgreich sind.
- **Timeouts:** Provider-spezifische Ready-Timeouts sind konfigurierbar (`server_ready_timeout_sec`, `server_ready_poll_sec`, `server_ready_probe_timeout_sec`).
- **End-of-Run-Cleanup:** Optional automatisch (`cleanup_on_exit: true`) mit Server-Stop (`server_stop_cmd`) und optionalem Cache-Clear (`server_post_stop_cmd`, etwa `~/.cache/llama.cpp`, `/tmp/llama.cpp*`).

Seit v4.3.0 wird dieser Cleanup im `UnifiedBenchmarkRunner` per `finally` erzwungen. Das gilt für erfolgreiche Läufe ebenso wie für manuelle Abbrüche (etwa `Ctrl+C`).

#### Benötigte Spark-Config-Keys

Für den konsolidierten `llamacpp_spark`-Betrieb sind typischerweise diese Felder nötig:

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

Zusammenhang:

- `context_length` umfasst Input und Output gemeinsam (KV-Cache).
- `max_tokens` gilt nur für Output und muss kleiner sein als `context_length`.
- `read_timeout` muss `max_tokens / tokens_per_second × 1.5` abdecken.
- `parallel` ist die Anzahl gleichzeitiger Slots (KV-Cache-Multiplikator): 2 für Benchmark, 1 für Hybrid-Attention.

Ohne `max_tokens`-Cap generiert das Modell bis zum Kontextfenster und löst einen HTTP-Timeout-Loop aus. Details: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) → "Spark: Token-Management pro Modell".

Frühere Lifecycle-Schalter wie `always_stop_before_start` sind im aktuellen Connector-Stand nicht mehr erforderlich.

#### Verbindungsbesonderheiten bei Spark (SSH)

- SSH muss non-interaktiv funktionieren (BatchMode/Key-basierter Zugriff empfohlen), sonst blockiert der Runner beim Modellstart.
- Der Remote-Binary-Pfad in `server_start_cmd` muss exakt dem installierten `llama-server` auf dem Spark entsprechen.
- `bind_host` und `base_url` müssen zusammenpassen (etwa `0.0.0.0` auf dem Spark, Zugriff via Intranet-IP).
- Wenn unter `base_url` bereits ein anderer OpenAI-kompatibler Server läuft, gibt der Connector nur eine Warnung aus und beendet den Benchmark sauber.

Alle lokalen Provider haben ein `enabled`-Flag. Ist es `false`, erscheint der Provider weder im Wizard noch im Cross-Model-Benchmark.

---

## Schritt 3 — LLM Judge und Meta-Reviewer konfigurieren

CrucibleMark bewertet textbasierte Soft-Skills über einen Meta-Judge — ein starkes externes Modell, das die Antworten der Kandidaten auswertet und Punkte vergibt.

In der Sektion `llm_judge:` wird der Richter festgelegt. **Anthropic** (mit `claude-haiku`) oder **Google** (mit `gemini-pro`) sind empfehlenswert. Wer keinerlei API-Kosten generieren will, kann auch ein lokales Ollama-Modell als Judge angeben (etwa `ministral-3:14b`). Das beansprucht jedoch erheblich mehr Zeit und Kontextfenster.

```yaml
llm_judge:
  enabled: true
  provider:
    name: anthropic
    model: claude-haiku-4-5-20251001
    max_tokens: 8192
```

---

## Schritt 4 — Benchmarking-Module auswählen

Nicht alle Test-Module sind für jeden Anwendungsfall relevant. Im Feld `modules` am Ende der `benchmark_config.yaml` wird festgelegt, welche Eigenschaften evaluiert werden.

Für einen schnellen ersten Test empfiehlt es sich, nur Code Quality (`coding`), CLI Benchmark (`cli_benchmark`) oder logisches Verständnis (`reasoning`) auf `enabled: true` zu lassen. Soft-Skills (UX-Writing, Cultural Intelligence u. a.) lassen sich zunächst ausklammern.

| Disziplin | Typ | Ziel des Moduls |
|---|---|---|
| **`code_quality`** | Hard Skill | sauberes, deterministisches Programmieren und Code-Erklärung |
| **`cli_benchmark`** | Hard Skill | Umgang mit der Kommandozeile und Terminal-Skripten |
| **`reasoning`** | Metrik | kognitiver Stresstest (Logikrätsel, Chain-of-Thought, Systemfehler) |
| **`ux_writing`** | Soft Skill | UI-Texte, Warnungen und nutzerzentrierte Führung |
| **`documentation_quality`** | Soft Skill | Vollständigkeit und Genauigkeit technischer Dokumentation |
| **`content_transformation`** | Soft Skill | Tone-of-Voice- und Zielgruppenwechsel |
| **`cultural_intelligence`** | Metrik | interkulturelle Nuancen, Empathie, Übersetzungspräzision |
| **`political_compass`** | Spezial | ideologische Ausrichtung (Bias) des Modells |

```yaml
  content_transformation:
    path: "benchmark_modules/content_transformation"
    enabled: false
```

Einzelne Module lassen sich auch dann via CLI aufrufen, wenn sie global deaktiviert sind:

```bash
make benchmark MODULE=code_quality
```

Nach diesen vier Schritten ist die Konfiguration abgeschlossen und der erste Testlauf kann starten.