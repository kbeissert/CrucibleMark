# Lokaler MCP-Webserver (Rig Setup)

Dieser MCP-Server laeuft lokal auf deinem Rechner und stellt Web-Recherche-Tools fuer lokale Modelle bereit.

> **Hinweis:** CrucibleMark betreibt **zwei** unabhaengige MCP-Server mit unterschiedlichen Aufgaben. Dieser Rig-Server (`scripts/mcp/local_rig_server.py`, STDIO-Protokoll) versorgt lokale Modelle im Editor-Workflow (z.B. Cline) mit Web-Tools. Der Benchmark-MCP-Server (`cruciblemark-mcp/server.py`, HTTP JSON-RPC 2.0) versorgt das `tooluse`-Benchmark-Modul mit reproduzierbaren Tool-Calls. Siehe `cruciblemark-mcp/README.md` fuer den Benchmark-Server.

## Enthaltene Tools

- `web_search(query, max_results=5)`: Web-Suche ohne API-Key (DuckDuckGo HTML)
- `fetch_url(url, max_chars=12000)`: Webseite abrufen und als lesbaren Text extrahieren
- `ping(message="pong")`: Health-Check
- `now_iso()`: Aktueller UTC-Timestamp in ISO-8601
- `system_info()`: Basisinfos zu Maschine, Python und Workspace
- `list_workspace_entries(limit=30)`: Top-Level-Dateien und Ordner im Workspace-Root

## Server-Datei

- `scripts/mcp/local_rig_server.py`

## Cline MCP Konfiguration

In deiner Cline-Konfiguration muss unter `mcpServers` ein Eintrag enthalten sein:

```json
"local-web-research": {
  "command": "uv",
  "args": [
    "--directory",
    "/Users/kbeissert/_PROJEKTE/Entwicklung/cruciblemark",
    "run",
    "--with",
    "mcp",
    "scripts/mcp/local_rig_server.py"
  ]
}
```

## Manuelles Starten (optional)

```bash
cd /Users/kbeissert/_PROJEKTE/Entwicklung/cruciblemark
uv run --with mcp scripts/mcp/local_rig_server.py
```

Wichtig fuer STDIO-Server: Keine `print()`-Ausgaben auf stdout verwenden.

## Zielbild

Damit verfuegt dein lokales Modell ueber einen MCP-Server fuer:

- Suche im Web
- Abruf und Extraktion von Seiteninhalten
- anschliessende Zusammenfassung/Analyse durch das Modell
