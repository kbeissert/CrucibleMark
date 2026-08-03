---
name: Tool Use Modul — Architektur, Pitfalls, kritische Fixes
description: Technische Details zum Tool Use Benchmark-Modul v3.11.0 — alle Bugfixes, Golden Standard v1.3.0, MCP-Config
type: project
originSessionId: b9258989-bd9b-4649-9011-4094a5265c62
---
# Tool Use Modul v3.11.0 — Kritische Details

**Why:** Dieses Modul hat mehrere nicht-offensichtliche Bugs gehabt und wurde kalibriert. Details für zukünftige Sessions.

## Golden Standard v1.3.0 — AKTUELL (2026-05-24)

**tooluse001** — Must: EU multimodal (Llama 4, Vision) vs. textbasiert (Llama 3.1/3.2) unterscheiden + URL-Zitat.
**tooluse002** — Must: Llama 4 Scout/Maverick als primäre Familie (stehen prominent oben), Llama Guard als Safety. Keywords: `["llama 4", "scout", "llama guard", "hugging"]`. Llama 3.2 ist Legacy — kein Pflicht-Keyword mehr.
**tooluse003** — Must: Tool-Attribution + kein Inhalt erfunden. Jede Aussage über Seiteninhalte = HARD FAIL.

**Wichtig:** assets/ ist gitignored. `combined_assets.yaml` im Module-Root ist tracked SSoT.

## AUTHORIZED_TOOLS — Vollständige Aliases (tool_adapter_audit.py)

```python
AUTHORIZED_TOOLS = {
    "web_search": ["web_search", "search", "websearch", "web-such-tool", "web_such_tool"],
    "http_fetch": ["http_fetch", "fetch", "http", "fetch_url", "get_url",
                   "http_fetch_and_extract", "fetch_http", "http-fetch-tool", "http_fetch_tool"],
}
```

- `fetch_http`: Magistral Small verwendet diese invertierte Variante
- `web-such-tool`: Llama 3.3 70B übernimmt deutschen Prompt-Begriff buchstäblich
- `http_fetch_and_extract`: Gemini-Kompatibilität

## MCP-Konfiguration (cruciblemark-mcp/config/mcp_config.yaml)

- `max_chars: 8000` (war 500 — kritischer Truncation-Bug, alle Modelle sahen nur HTML-Head)
- Mock-Fixture für `huggingface.co/meta-llama` vorhanden (Llama 4 Scout/Maverick/Guard/3.x)
- Whitelist: llama.meta.com, huggingface.co, raw.githubusercontent.com, httpbin.org
- Nach Config-Änderungen MCP-Server neu starten (kein Hot-Reload)

## P1 Scoring Stufen (evaluators.py)

| Bedingung | Score |
|---|---|
| Kein Tool-Aufruf | 0 |
| Falsches Tool | 20 |
| Richtiges Tool, non-200 oder leerer Content | 40 |
| Richtiges Tool + korrekter Status | 80 |
| Richtiges Tool + Status + content_excerpt ≥ 100 Zeichen¹ | 100 |

¹ Nur für http_fetch Non-Failure. Bei web_search und failure_test gilt max P1=80.

## discover_assets() — Wichtig für combined_assets.yaml

`utils/benchmark_utils.py:85`: `path.glob("*.yaml")` — kein Filter.
`combined_assets.yaml` MUSS im Module-Root bleiben, NICHT in assets/, sonst läuft tooluse001 doppelt (4 statt 3 Assets).

## Diagnostics Schwellen (diagnostics.py)

- `excerpt_quality = "full"`: total_bytes > 2000
- `excerpt_quality = "partial"`: total_bytes > 500
- `excerpt_quality = "minimal"`: total_bytes > 50

## Kalibrierungsergebnisse (v1.2.0 Baseline — vor MCP-Fix)

| Modell | P1 | P2 | Combined |
|---|---|---|---|
| Sonnet 4.6 | 95 | 65.0 | 80.0 |
| Sonnet 4.5 | 85 | 70.3 | 77.6 |
| Opus 4.6 | 85 | 68.6 | 76.8 |
| Hermes 4 70B | 90 | 62.7 | 76.3 |
| Haiku 4.5 | 85 | 62.8 | 73.9 |
| Gemini 2.5 Pro | 85 | 61.8 | 73.4 |
| Gemini 3 Flash | 85 | 57.8 | 71.4 |
| GPT-5.4 | 75 | 65.0 | 70.0 |

P2-Spread v1.2.0: 57.8–70.3 (+12.5). Nach MCP-Fix erwarten sich höhere P2-Werte (body content statt head-only).

## Sovereignty Gap Formel (SSoT)

`gap = local_avg − all_avg` — positiv = local lead, negativ = cloud lead.

## tool_call_attempts Aggregation

`tool_call_attempts` = **max** über alle Assets (nicht sum).

## MCP-Server Lifecycle

- `make mcp-start` idempotent (Health-Check vor Start)
- `make mcp-stop` stale-PID-sicher
- Batch-Runner startet MCP zwischen jedem Modell neu (Fairness)
