# CrucibleMark MCP Server

## 1. Zweck

Der CrucibleMark MCP Server ist ein minimaler, lokal laufender HTTP-Dienst, der das `tooluse`-Benchmark-Modul mit kontrollierten Tool-Calls versorgt.

**Warum existiert er?**

Damit Benchmark-Ergebnisse vergleichbar und reproduzierbar sind, müssen alle getesteten Modelle exakt dieselben externen Bedingungen vorfinden — denselben Such-Provider, dieselben Timeouts, dieselbe Whitelist. Würde jedes Modell direkt auf externe APIs zugreifen, wären Ergebnisse nicht mehr vergleichbar (unterschiedliche Antwortzeiten, unterschiedliche Suchergebnisse je nach Zeitpunkt, unterschiedliche Fehlerbehandlung).

Der Server löst das durch:
- **Reproduzierbarkeit** — Mock-Modus liefert immer dieselben Fixture-Responses
- **Fairness** — alle Modelle erhalten dieselben Inputs und dieselbe Infrastruktur
- **Audit-Fähigkeit** — jeder Tool-Call wird mit `request_id`, Timestamp, Provider und Status geloggt

## 2. Voraussetzungen

---

## Design-Prinzip: MCP-Standard-Konformität

Die Tool-Namen dieses Servers orientieren sich am offiziellen **Model Context Protocol (MCP)**,
das von Anthropic definiert und als Open Standard veröffentlicht wurde
([modelcontextprotocol.io](https://modelcontextprotocol.io)).

**Warum ist das relevant für den Benchmark?**

CrucibleMark misst, wie zuverlässig Modelle Tools in realen MCP-Umgebungen einsetzen können —
nicht ob sie mit projektinternen Namenskonventionen umgehen können. Ein Modell, das `fetch`
aufruft, demonstriert MCP-Kompetenz. Würde der Benchmark ein nicht-standardkonformes
`http_fetch` erzwingen, bestraft er Modelle dafür, dass sie den Standard korrekt kennen.

**Konkrete Entscheidungen daraus:**

| Tool | Name in diesem Server | Begründung |
|---|---|---|
| HTTP-Fetch | `fetch` | Entspricht `@modelcontextprotocol/server-fetch` (Anthropic-Referenzimplementierung) |
| Web-Suche | `web_search` | Weit verbreiteter, deskriptiver Name — kein einheitlicher MCP-Standard für Search-Tools |

Das Prinzip gilt für alle künftigen Tool-Erweiterungen: Tool-Namen richten sich nach dem
MCP-Standard oder, wo kein Standard existiert, nach dem de-facto-Konsens in der MCP-Ökosystem.

---

- **Python 3.12** (identisch mit dem CrucibleMark-Hauptprojekt)
- **PyYAML** — bereits in `requirements.txt` enthalten (`pyyaml>=6.0`)
- Keine weiteren Dependencies für Mock-Modus
- Für Live-Modus mit DuckDuckGo: kein zusätzlicher Package nötig (nutzt `urllib`)
- Optionale API-Keys (nur Live-Modus mit serpapi/brave):
  - `SERPAPI_KEY` — wenn `provider: serpapi` in `mcp_config.yaml`

---

## 3. Schnellstart

```bash
# Server im Mock-Modus starten (Standard)
make mcp-start

# Status prüfen
make mcp-health

# Server stoppen
make mcp-stop

# Explizit Mock-Modus
make mcp-mock
```

Manuell:

```bash
# Mock-Modus
python cruciblemark-mcp/server.py --mode mock

# Live-Modus
python cruciblemark-mcp/server.py --mode live

# Anderen Port verwenden
python cruciblemark-mcp/server.py --mode mock --port 9000
```

---

## 4. Modi

### Mock-Modus (`--mode mock`, Standard)

- Alle Calls geben gecachte Fixture-Responses zurück
- Kein echter Netzaufruf, kein API-Key erforderlich
- Deterministische, immer identische Antworten
- **Für CI, lokale Entwicklung und alle Benchmark-Runs empfohlen**

### Live-Modus (`--mode live`)

- `web_search`: echter Aufruf gegen die DuckDuckGo Instant Answer API via `urllib`
- `http_fetch`: echter HTTP-GET gegen die erlaubten Whitelist-Domains
- Ergebnisse variieren je nach Zeitpunkt und Netzwerk
- **Nur für explorative Tests oder manuelle Verifikation**

Der aktive Modus wird im `/health`-Endpoint ausgewiesen: `"mode": "mock"` bzw. `"mode": "live"`.

---

## 5. Konfiguration

Alle Einstellungen in `cruciblemark-mcp/config/mcp_config.yaml`:

```yaml
server:
  host: localhost      # Nur lokale Verbindungen — kein externer Zugriff
  port: 8765           # Standard-Port
  mode: mock           # Startmodus: mock | live

web_search:
  provider: duckduckgo # Aktiver Such-Provider: duckduckgo | serpapi | brave
  max_results: 3       # Maximale Ergebnisse pro Suche (kann per Request überschrieben werden)
  timeout_seconds: 10  # Timeout für Live-Requests
  api_key_env: SERPAPI_KEY  # Env-Var-Name für API-Key (nur serpapi/brave)

http_fetch:
  timeout_seconds: 8   # Timeout für Live-HTTP-Requests
  max_chars: 500        # Maximale Zeichen im content_excerpt
  whitelist:            # Erlaubte Domains (nur diese Hosts dürfen gefetcht werden)
    - llama.meta.com
    - huggingface.co
    - raw.githubusercontent.com
    - httpbin.org

logging:
  log_file: logs/mcp_server.log   # Pfad relativ zum Projekt-Root
  log_level: INFO                 # DEBUG | INFO | WARNING | ERROR
```

**Wichtig:** Alle Werte werden ausschließlich aus dieser YAML-Datei geladen. Es gibt keine hardcodierten Fallbacks im Python-Code.

---

## 6. Protokoll: JSON-RPC 2.0

Der Server implementiert das **Model Context Protocol (MCP)** über JSON-RPC 2.0. Er verhält
sich protokollidentisch zu einem echten MCP-Server wie Claude Desktop oder der VS Code
MCP-Extension — inklusive `initialize`-Handshake, `tools/list` und `tools/call`. Das ist
kein benutzerdefiniertes REST-API, sondern der offizielle Standard.

Alle Requests gehen an einen einzigen POST-Endpunkt (`http://localhost:8765/`).
Der Health-Check bleibt als `GET /health` für interne Nutzung erhalten.

### Unterstützte JSON-RPC Methoden

| Methode | Beschreibung |
|---|---|
| `initialize` | Verbindungsaufbau; gibt `protocolVersion`, `capabilities`, `serverInfo` zurück |
| `notifications/initialized` | Client-Bestätigung nach `initialize` — keine Antwort nötig (204) |
| `tools/list` | Gibt die Tool-Definitionen mit `inputSchema` zurück |
| `tools/call` | Führt ein Tool aus; `params.name` + `params.arguments` |

Unbekannte Methoden und Tools antworten mit dem JSON-RPC Standardfehler:
```json
{"jsonrpc": "2.0", "id": 1, "error": {"code": -32601, "message": "Method not found: xyz"}}
```

### Beispiel-Kommunikation

```bash
# Tool-Liste abfragen
curl -s -X POST http://localhost:8765/ \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# web_search ausführen
curl -s -X POST http://localhost:8765/ \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call",
       "params":{"name":"web_search","arguments":{"query":"llm benchmarks","max_results":3}}}'

# fetch ausführen
curl -s -X POST http://localhost:8765/ \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call",
       "params":{"name":"fetch","arguments":{"url":"https://huggingface.co/","max_length":2000}}}'
```

---

## 7. Tool-Referenz

Die Tool-Definitionen orientieren sich am Anthropic MCP-Standard. `fetch` ist
**1:1 identisch** mit `@modelcontextprotocol/server-fetch` (Referenzimplementierung) —
inklusive Parameternamen. Modelle, die mit echten MCP-Servern trainiert wurden, kennen
exakt diese Parameter.

### `web_search`

**Request-Parameter** (`params.arguments`):
```json
{
  "query": "string (Pflicht)",
  "max_results": 3
}
```

**Result** (im Feld `result` des JSON-RPC Response):
```json
{
  "status": "success",
  "results": [
    {"url": "https://...", "title": "string", "excerpt": "string (max 300 Zeichen)"}
  ],
  "content": [{"type": "text", "text": "Ergebnis 1: ..."}],
  "isError": false,
  "request_id": "uuid-v4",
  "provider": "tavily",
  "timestamp": "2024-01-01T00:00:00+00:00"
}
```

---

### `fetch`

`fetch` entspricht der offiziellen Anthropic-Referenzimplementierung
`@modelcontextprotocol/server-fetch`. Die Parameternamen sind identisch — Modelle, die
mit Claude Desktop oder der VS Code MCP-Extension trainiert wurden, senden exakt
diese Felder.

**Request-Parameter** (`params.arguments`):

| Parameter | Typ | Pflicht | Default | Beschreibung |
|---|---|---|---|---|
| `url` | string | ✓ | — | Ziel-URL |
| `max_length` | integer | — | 5000 | Max. Zeichen im Content |
| `start_index` | integer | — | 0 | Startposition (Pagination für große Seiten) |
| `raw` | boolean | — | false | Rohen HTML-Content statt aufbereitetem Text |

**Result**:
```json
{
  "status": "success",
  "status_code": 200,
  "content_excerpt": "string (max 200 Zeichen Vorschau)",
  "content": [{"type": "text", "text": "Vollständiger extrahierter Text..."}],
  "isError": false,
  "source_url": "https://...",
  "request_id": "uuid-v4",
  "timestamp": "2024-01-01T00:00:00+00:00"
}
```

**Fehlerstatus:**

| `status` | `status_code` | Bedeutung |
|---|---|---|
| `success` | 200 | Inhalt erfolgreich abgerufen |
| `error` | 404, 403, ... | HTTP-Fehler vom Ziel-Server |
| `blocked` | `null` | Domain nicht in Whitelist — kein Netzaufruf |

---

### `GET /health`

```json
{"status": "ok", "mode": "mock", "version": "1.0.0"}
```

---

## 8. Tool-Name-Normalisierung

Modelle, die auf unterschiedlichen MCP-Umgebungen fine-getuned wurden, können alternative
Tool-Namen verwenden (z. B. `http_fetch` statt `fetch`). Der Benchmark normalisiert bekannte
Varianten automatisch in `benchmark_modules/tooluse/core/tool_adapter_audit.py` und markiert
sie als `is_anomaly = True` im Audit-Log — statt in einem `parse_error` zu enden.

| Kanonischer Name | Akzeptierte Varianten |
|---|---|
| `web_search` | `web_search`, `web.search`, `search` |
| `fetch` | `fetch`, `http_fetch`, `fetch_url`, `get_url`, `web_fetch`, `url_fetch`, `read_url` |

Ein Modell, das `http_fetch` aufruft, läuft korrekt durch — mit `is_anomaly`-Flag.
Ein völlig unbekannter Name (z. B. `tavily_search`) landet in einem `parse_error` — das
ist ein valides Benchmark-Signal für fehlende Tool-Conformance.

---

## 9. Idle-Timeout: Auto-Shutdown bei Inaktivität

Der Server beendet sich automatisch, wenn er für eine konfigurierbare Zeitspanne keine
Anfragen erhalten hat — analog zu Ollamas Modell-Unloading nach Inaktivität. Das verhindert
verwaiste Hintergrundprozesse und offene Ports nach Benchmark-Runs.

**Verhalten:**
- Jede eingehende Anfrage (Health-Check, `tools/list`, `tools/call`) setzt den Timer zurück
- Watchdog-Thread prüft alle `idle_timeout / 5` Sekunden (mind. 2 s, max. 30 s)
- Bei Ablauf: sauberes `server.shutdown()` → PID-File wird gelöscht → Port freigegeben
- Benchmark-Runs laufen durch: `_call_mcp_tool()` schickt bei jedem Asset eine Anfrage

**Konfiguration:**

```yaml
# cruciblemark-mcp/config/mcp_config.yaml
server:
  idle_timeout_seconds: 300  # 5 Minuten (Standard)
  # 0 = deaktiviert — Server läuft bis manueller Stop
```

```bash
# CLI-Override (hat Vorrang vor YAML)
.venv/bin/python cruciblemark-mcp/server.py --idle-timeout 600   # 10 Minuten
.venv/bin/python cruciblemark-mcp/server.py --idle-timeout 0     # deaktiviert
```

---

## 10. Whitelist-Policy

Die Whitelist in `mcp_config.yaml` definiert, welche Domains über `http_fetch` erreichbar sind. Jede Anfrage an eine nicht gelistete Domain wird sofort mit `status: "blocked"` abgelehnt, ohne Netzaufruf.

**Warum eine Whitelist?**

- Verhindert versehentlichen Zugriff auf interne Ressourcen oder sensitive URLs
- Stellt sicher, dass alle Modelle dieselben Ziel-URLs sehen können
- Macht das Testset deterministisch (nur bekannte Domains, keine Überraschungen)

**Whitelist erweitern:**

1. Domain zu `http_fetch.whitelist` in `mcp_config.yaml` hinzufügen
2. Entsprechendes Mock-Fixture in `tools/mock_provider.py` → `_FIXTURE_FETCH` ergänzen
3. Test-Asset in den `tooluse`-Assets aktualisieren (separater Task)

---

## 11. Logging

Jeder Tool-Call schreibt einen JSON-Eintrag in `logs/mcp_server.log` (relativ zum Projekt-Root).

**Format:**
```
2024-01-01T12:00:00 INFO {"request_id": "...", "timestamp": "...", "tool_type": "web_search", "status": "success", "provider": "tavily", "query": "..."}
```

**Felder:**

| Feld | Beschreibung |
|---|---|
| `request_id` | UUID-v4, eindeutig pro Call |
| `timestamp` | ISO8601 UTC |
| `tool_type` | `web_search` oder `fetch` |
| `status` | `success`, `error` oder `blocked` |
| `provider` | Aktiver Such-Provider (nur web_search) |
| `url` | Ziel-URL (nur fetch) |

Die `request_id` ist identisch im Server-Log und in der JSON-Response — das verknüpft Benchmark-Audit-Logs mit Server-Logs.

---

## 12. Abgrenzung (Scope Fence)

Der Server ist ein reines Transport-Werkzeug. Explizit **nicht** Teil seines Scopes:

- **Kein Agent-Framework** — kein LangChain, LlamaIndex oder ähnliches
- **Kein Tool-Chaining** — Sequenzierung liegt beim Modell, nicht beim Server
- **Keine Authentifizierung** — der Server lauscht ausschließlich auf `localhost`
- **Kein Live-Caching** — Live-Requests werden nicht gecacht; Reproduzierbarkeit erfolgt über fixe Asset-Prompts
- **Keine Ergebnis-Interpretation** — Raw-Daten werden zurückgegeben; Bewertung erfolgt in `core/evaluators.py`
- **Kein eigener Scoring-Anteil** — der Server beeinflusst kein Benchmark-Ergebnis
- **Kein Statemanagement** zwischen Calls — jeder Request ist atomar und unabhängig

---

## 13. Integration mit dem `tooluse`-Modul

`scripts/run_tooluse_benchmark.py` (aufgerufen via `make benchmark-tooluse`) verwaltet
den MCP-Server-Lifecycle **vollständig automatisch** — kein manuelles `mcp-start`/`mcp-stop`
nötig.

**Automatischer Ablauf:**

```bash
# Einziger Befehl — MCP Start/Stop ist eingebettet
make benchmark-tooluse
make benchmark-tooluse MODEL=gemma3:4b
make benchmark-tooluse MCP_MODE=mock FORCE=1
```

**Lifecycle im Detail:**
1. Script prüft ob Server bereits läuft (`/health`)
2. Falls nicht: `_start_mcp_for_run(mode)` startet ihn und setzt ein internes Flag
3. Benchmark läuft durch
4. `atexit`-Handler ruft `_stop_mcp_if_managed()` auf — egal ob normaler Exit oder Exception
5. Ctrl+C (`KeyboardInterrupt`): laufender Subprocess wird via `SIGTERM` beendet,
   MCP Server wird gestoppt, Exit-Code 130

**Ist der Server bereits manuell gestartet**, wird er **nicht** automatisch gestoppt
(Flag bleibt `False`). Der Idle-Timeout übernimmt als Fallback.

`mcp-start` / `mcp-stop` direkt verwenden nur für:
- Entwicklung / manuelle Tests
- `make tooluse-run` (Legacy-Target, ohne Wizard)
- CI-Pipelines mit explizitem Lifecycle-Management

Detaillierte Integration: `docs/DEVELOPER_GUIDE.md` → Abschnitt "tooluse-Modul".
