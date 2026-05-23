# CrucibleMark MCP — Manuelle Test-Prompts

Voraussetzung: Server läuft (`make mcp-start` oder `make mcp-mock`)

---

## 1. Health Check

```bash
curl http://localhost:8765/health
```

Erwartetes Ergebnis:
```json
{"status": "ok", "mode": "mock", "version": "1.0.0"}
```

---

## 2. Web Search — Mock-Modus

```bash
curl -X POST http://localhost:8765/tools/web_search \
  -H "Content-Type: application/json" \
  -d '{"query": "Meta Llama EU commercial restriction", "max_results": 3}'
```

Erwartetes Ergebnis:
- `status: "success"`
- mind. 1 result mit `url`, `title`, `excerpt`
- `request_id` vorhanden (UUID-Format)

---

## 3. Web Search — Live-Modus (Tavily)

Voraussetzung: `TAVILY_API_KEY` gesetzt, Server mit `make mcp-start MODE=live` gestartet

```bash
curl -X POST http://localhost:8765/tools/web_search \
  -H "Content-Type: application/json" \
  -d '{"query": "Meta Llama EU commercial restriction license", "max_results": 3}'
```

Erwartetes Ergebnis:
- `status: "success"`
- mind. 2 results mit echten URLs
- `"provider": "tavily"` im Response

Fallback-Test (ohne Key):

```bash
# TAVILY_API_KEY ungesetzt lassen, dann:
curl -X POST http://localhost:8765/tools/web_search \
  -H "Content-Type: application/json" \
  -d '{"query": "open source llm benchmark", "max_results": 2}'
```

Erwartetes Ergebnis:
- `"provider": "duckduckgo"` (automatischer Fallback)
- Log-Eintrag: `[MCP] Tavily key not found, falling back to DuckDuckGo`

---

## 4. HTTP Fetch — Erfolgreiche URL (Mock)

```bash
curl -X POST http://localhost:8765/tools/http_fetch \
  -H "Content-Type: application/json" \
  -d '{"url": "https://huggingface.co/", "max_chars": 500}'
```

Erwartetes Ergebnis:
- `status: "success"`
- `status_code: 200`
- `content_excerpt` nicht leer

---

## 5. HTTP Fetch — 404-Simulation (Mock)

```bash
curl -X POST http://localhost:8765/tools/http_fetch \
  -H "Content-Type: application/json" \
  -d '{"url": "https://httpbin.org/status/404", "max_chars": 500}'
```

Erwartetes Ergebnis:
- `status: "error"`
- `status_code: 404`
- `content_excerpt: null` ← **KRITISCH: kein erfundener Inhalt**

---

## 6. Whitelist-Blockierung

```bash
curl -X POST http://localhost:8765/tools/http_fetch \
  -H "Content-Type: application/json" \
  -d '{"url": "https://google.com", "max_chars": 500}'
```

Erwartetes Ergebnis:
- `status: "blocked"`
- `status_code: null`
- `content_excerpt: null`

---

## 7. Logging prüfen

```bash
tail -20 logs/mcp_server.log
```

Erwartetes Ergebnis:
- Jeder Call aus Tests 1–6 erscheint als Log-Eintrag
- Jeder Eintrag enthält: `timestamp`, `request_id`, `tool_type`, `status`
- Bei Fallback auf DuckDuckGo: `WARNING`-Eintrag mit `[MCP] Tavily key not found`

---

## Hinweise

- Mock-Modus (`make mcp-start`): Kein Netzaufruf, deterministische Fixture-Responses
- Live-Modus (`make mcp-start MODE=live`): Echter Netzaufruf, braucht ggf. `TAVILY_API_KEY`
- Port 8765 ist der Standard — nicht mit dem Test-Port 8766 verwechseln
