# Plan: Card-Research mit MCP Tool-Use (Web-Zugang)

## Ziel

Card-Research-Modus soll über MCP `web_search` + `fetch` im Internet recherchieren können — ohne Änderungen am tooluse MCP oder Benchmark-Code. **Alle Änderungen ausschließlich in `manage_model_cards.py` + Makefile.**

## Architektur

```
Card-Research (manage_model_cards.py)
    │
    │  HTTP POST (JSON-RPC 2.0)
    ▼
MCP Server :8765  (unverändert!)
    ├── web_search  (Tavily / DuckDuckGo)
    └── fetch       (HTTP + HTML-to-text)
```

Der bestehende MCP-Server bleibt **unberührt**. `manage_model_cards.py` ruft ihn nur via HTTP POST auf — exakt wie der tooluse Benchmark es auch tut.

## Änderungen

### 1. Neue Imports (`manage_model_cards.py`)

```python
import urllib.error
import urllib.request
```

### 2. MCP-Tool-Schemas (neue Konstanten)

```python
TOOL_SCHEMA_WEB_SEARCH = {
    "name": "web_search",
    "description": "Sucht im Web nach aktuellen Informationen.",
    "parameters": {
        "query": {"type": "string", "description": "Der Suchbegriff"},
        "max_results": {"type": "integer", "description": "Anzahl der Ergebnisse (max. 3)", "default": 3},
    },
}

TOOL_SCHEMA_HTTP_FETCH = {
    "name": "fetch",
    "description": "Lädt den Inhalt einer URL.",
    "parameters": {
        "url": {"type": "string", "description": "Die zu ladende URL"},
        "max_chars": {"type": "integer", "description": "Maximale Zeichenanzahl", "default": 3000},
    },
}
```

### 3. MCP-Helferfunktionen (neue private Functions)

**`_call_mcp_tool(base_url, tool_name, params) -> dict`**
- POST JSON-RPC 2.0 `tools/call` an MCP-Server (wie `tooluse/test.py:619-648`)
- Timeout: 15s
- Gibt Transcript-Dict zurück, nie Exception

**`_parse_tool_call(text) -> tuple[dict | None, str | None]`**
- Exakt wie `tooluse/test.py:577-616`
- Sucht `{"tool_call": {"name": ..., "parameters": {...}}}` im LLM-Output
- Ignoriert Markdown-Fences

**`_extract_tool_content(transcript) -> str`**
- Wie `tooluse/test.py:651-689`
- Extrahiert lesbaren Text aus MCP-Transcript

### 4. Research-System-Prompt mit Tool-Use

**Neuer Prompt `_RESEARCH_TOOLUSE_SYSTEM_INSTRUCTION`:**

```
Du bist ein Card-Researcher mit Internetzugang.

Verfügbare Tools:
{tool_schema_json}

Arbeitsablauf:
1. Wenn du Informationen recherchieren musst, antworte AUSSCHLIESSLICH mit:
   {"tool_call": {"name": "web_search", "parameters": {"query": "..."}}}
   ODER
   {"tool_call": {"name": "fetch", "parameters": {"url": "...", "max_chars": 3000}}}
2. Ich liefere dir das Tool-Ergebnis zurück.
3. Wiederhole Schritt 1-2 bis du genug Informationen hast.
4. Wenn du fertig bist, antworte AUSSCHLIESSLICH mit einem JSON-Objekt:
   {"findings": [...], "summary": "..."}

Regeln:
- Nutze web_search um Preise, Context-Window, Knowledge-Cutoff etc. zu finden.
- Nutze fetch um konkrete URLs (Hersteller-Seiten, HF-Cards) zu lesen.
- Antworte NUR mit JSON — kein Markdown-Fence, keine Kommentare.
- Erfinde keine Inhalte — alles muss aus Tool-Ergebnissen stammen.
```

### 5. Research-Loop in `Researcher._research_one()`

**Neue Methode `Researcher._research_tooluse_one(mid, path, idx, total)`:**

```
1. Card laden + Pre-Check-Heuristik (Murks/CJK)
2. Lock setzen (profile_verified=false)
3. Loop (max. 3 Tool-Call-Runden):
   a. Prompt bauen: Card-JSON + Tool-Schemas + Tool-Ergebnisse bisher
   b. LLM-Call mit _RESEARCH_TOOLUSE_SYSTEM_INSTRUCTION
   c. Antwort parsen:
      - Enthält "tool_call" → MCP-Tool ausführen → Ergebnis sammeln → nächste Runde
      - Enthält "findings" → Finale findings → Loop beenden
      - Kein beides → Retry (max. 1x)
4. Findings auf Card anwenden
5. Unlock (profile_verified=true)
```

**Max. 3 Tool-Call-Runden** (verhindert Endlosschleife bei kaputtem Modell).

### 6. `--tooluse` CLI-Flag

```
--tooluse           Tool-Use-Modus: LLM recherchiert via MCP (web_search/fetch)
```

**Verhalten:**
- `--mode research` (Default): Single-Call, kein MCP (aktuelles Verhalten)
- `--mode research --tooluse`: Multi-Step mit MCP-Tool-Use

### 7. Makefile-Integration

```makefile
card-research:
	@$(PYTHON) scripts/manage_model_cards.py --mode research \
		$(if $(MODEL),--card "$(MODEL)",) \
		$(if $(FORCE),--force,) \
		$(if $(DRY),--dry-run,) \
		$(if $(PAUSE),--pause "$(PAUSE)",) \
		$(if $(TOOLUSE),--tooluse,)
```

Neues Flag in `help`: `TOOLUSE=1` — Tool-Use-Modus (MCP web_search/fetch)

### 8. MCP-Server-URL konfigurierbar

```
--mcp-url    MCP-Server URL (Default: http://localhost:8765)
```

### Zusammenfassung der Dateien

| Datei | Änderung |
|-------|----------|
| `manage_model_cards.py` | Neue Imports, Tool-Schemas, MCP-Helfer, Tool-Use-Prompt, `--tooluse` Flag, `_research_tooluse_one()` |
| `Makefile` | `--tooluse` Flag, `TOOLUSE` in help |

**Nicht berührt:**
- `cruciblemark-mcp/` — 0 Änderungen
- `benchmark_modules/tooluse/` — 0 Änderungen
- Alle anderen Scripts — 0 Änderungen
