# Lokaler MCP-Webserver (Rig Setup)

Dieser MCP-Server laeuft lokal auf deinem Rechner und stellt Web-Recherche-Tools fuer lokale Modelle bereit.

## Enthaltene Tools

- `web_search(query, max_results=5)`: Web-Suche ohne API-Key (DuckDuckGo HTML)
- `fetch_url(url, max_chars=12000)`: Webseite abrufen und als lesbaren Text extrahieren
- `ping(message="pong")`: Health-Check
- `system_info()`: Basisinfos zu Maschine, Python und Workspace

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
