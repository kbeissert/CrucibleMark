# CrucibleMark MCP Server

## 1. Zweck

Der CrucibleMark MCP Server ist ein minimaler, lokal laufender HTTP-Dienst, der das `tooluse`-Benchmark-Modul mit kontrollierten Tool-Calls versorgt.

**Warum existiert er?**

Damit Benchmark-Ergebnisse vergleichbar und reproduzierbar sind, müssen alle getesteten Modelle exakt dieselben externen Bedingungen vorfinden — denselben Such-Provider, dieselben Timeouts, dieselbe Whitelist. Würde jedes Modell direkt auf externe APIs zugreifen, wären Ergebnisse nicht mehr vergleichbar (unterschiedliche Antwortzeiten, unterschiedliche Suchergebnisse je nach Zeitpunkt, unterschiedliche Fehlerbehandlung).

Der Server löst das durch:
- **Reproduzierbarkeit** — Mock-Modus liefert immer dieselben Fixture-Responses
- **Fairness** — alle Modelle erhalten dieselben Inputs und dieselbe Infrastruktur
- **Audit-Fähigkeit** — jeder Tool-Call wird mit `request_id`, Timestamp, Provider und Status geloggt

---

## 2. Voraussetzungen

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

## 6. Tool-Referenz

### `POST /tools/web_search`

**Request:**
```json
{
  "query": "string",
  "max_results": 3
}
```

**Response (success):**
```json
{
  "status": "success",
  "results": [
    {
      "url": "https://...",
      "title": "string",
      "excerpt": "string (max 300 Zeichen)"
    }
  ],
  "request_id": "uuid-v4",
  "provider": "duckduckgo",
  "timestamp": "2024-01-01T00:00:00+00:00"
}
```

**Response (error):**
```json
{
  "status": "error",
  "results": [],
  "request_id": "uuid-v4",
  "provider": "duckduckgo",
  "timestamp": "..."
}
```

---

### `POST /tools/http_fetch`

**Request:**
```json
{
  "url": "https://huggingface.co/",
  "max_chars": 500
}
```

**Response (success):**
```json
{
  "status": "success",
  "status_code": 200,
  "content_excerpt": "string (max max_chars Zeichen)",
  "source_url": "https://...",
  "request_id": "uuid-v4",
  "timestamp": "..."
}
```

**Fehlerstatus:**

| `status`  | `status_code` | Bedeutung                                 |
|-----------|---------------|-------------------------------------------|
| `success` | 200           | Inhalt erfolgreich abgerufen              |
| `error`   | 404, 403, ... | HTTP-Fehler vom Ziel-Server               |
| `blocked` | `null`        | Domain nicht in Whitelist — kein Netzaufruf |

Bei `error` und `blocked` ist `content_excerpt` immer `null`.

---

### `GET /health`

**Response:**
```json
{
  "status": "ok",
  "mode": "mock",
  "version": "1.0.0"
}
```

---

## 7. Whitelist-Policy

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

## 8. Logging

Jeder Tool-Call schreibt einen JSON-Eintrag in `logs/mcp_server.log` (relativ zum Projekt-Root).

**Format:**
```
2024-01-01T12:00:00 INFO {"request_id": "...", "timestamp": "...", "tool_type": "web_search", "status": "success", "provider": "duckduckgo", "query": "..."}
```

**Felder:**

| Feld         | Beschreibung                              |
|--------------|-------------------------------------------|
| `request_id` | UUID-v4, eindeutig pro Call               |
| `timestamp`  | ISO8601 UTC                               |
| `tool_type`  | `web_search` oder `http_fetch`            |
| `status`     | `success`, `error` oder `blocked`         |
| `provider`   | Aktiver Such-Provider (nur web_search)    |
| `url`        | Ziel-URL (nur http_fetch)                 |

Die `request_id` ist identisch im Server-Log und in der JSON-Response — das verknüpft Benchmark-Audit-Logs mit Server-Logs.

---

## 9. Abgrenzung (Scope Fence)

Der Server ist ein reines Transport-Werkzeug. Explizit **nicht** Teil seines Scopes:

- **Kein Agent-Framework** — kein LangChain, LlamaIndex oder ähnliches
- **Kein Tool-Chaining** — Sequenzierung liegt beim Modell, nicht beim Server
- **Keine Authentifizierung** — der Server lauscht ausschließlich auf `localhost`
- **Kein Live-Caching** — Live-Requests werden nicht gecacht; Reproduzierbarkeit erfolgt über fixe Asset-Prompts
- **Keine Ergebnis-Interpretation** — Raw-Daten werden zurückgegeben; Bewertung erfolgt in `core/evaluators.py`
- **Kein eigener Scoring-Anteil** — der Server beeinflusst kein Benchmark-Ergebnis
- **Kein Statemanagement** zwischen Calls — jeder Request ist atomar und unabhängig

---

## 10. Integration mit dem `tooluse`-Modul

Das `tooluse`-Benchmark-Modul startet den MCP-Server vor einem Benchmark-Run und kommuniziert mit ihm über HTTP auf `localhost:8765`.

**Typischer Ablauf:**

```bash
# 1. Server starten (im Hintergrund)
make mcp-start

# 2. Health-Check
make mcp-health

# 3. Benchmark mit tooluse-Modul
make benchmark MODULE=tooluse

# 4. Server stoppen
make mcp-stop
```

Der Benchmark-Runner übergibt die Server-URL an das `tooluse`-Modul via `benchmark_config.yaml` (Schlüssel: `modules.tooluse.mcp_server_url`). Das Modul sendet die Tool-Calls des Modells an den Server und wertet die Responses in `core/evaluators.py` aus.

Detaillierte Integration: `docs/DEVELOPER_GUIDE.md` → Abschnitt "tooluse-Modul".
