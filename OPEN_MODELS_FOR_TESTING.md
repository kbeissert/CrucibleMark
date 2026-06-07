# Noch zu testende Modelle (Stand: 2026-06-07)

**Zusammenfassung:**
- Konfiguriert: 85 Modelle
- Bereits getestet: 80 Modelle
- **Noch offen: 39 Modelle**
- Abdeckung: 94,1%

---

## ANTHROPIC (4 Modelle)
- claude-opus-4-7
- claude-opus-4-6
- claude-sonnet-4-6
- claude-opus-4-5-20251101

## GOOGLE (3 Modelle)
- gemini-3.5-flash
- gemini-3.1-pro-preview
- gemini-3-flash-preview

## GROQ (2 Modelle)
- meta-llama/llama-4-scout-17b-16e-instruct
- llama-3.3-70b-versatile

## LLAMACPP (13 Modelle) - MacBook Pro
- gemma-3-12b-it
- gemma-3-12b-it-q8
- hermes-3-8b
- hermes-4-14b-abliterated
- hermes-4-14b-q4
- qwen2.5-coder-7b
- qwen3-14b
- qwen3.5-4b-q4
- qwen3.5-4b-q6
- qwen3.5-4b-q8
- qwen3.5-9b

## LLAMACPP_SPARK (7 Modelle) - DGX Spark
- qwen3.6-35b-a3b-q8
- qwen3.6-35b-a3b-uncensored
- qwen3.5-35b-a3b-q8
- qwen3.5-35b-a3b-q4
- qwen3-coder-30b-a3b-q8
- qwen3-coder-next-q4
- gemma-4-26b-a4b-q8
- hermes-4.3-36b-q6

## MISTRAL (1 Modell)
- mistral-small-2503

## OPENROUTER (6 Modelle)
- deepseek/deepseek-v4-pro
- deepseek/deepseek-v4-flash
- z-ai/glm-4.6
- z-ai/glm-4.7
- moonshotai/kimi-k2.6
- moonshotai/kimi-k2-thinking-20251106

## XAI (3 Modelle)
- grok-4.20-0309-reasoning
- grok-4-1-fast-reasoning
- grok-3-mini

---

## Test-Befehl

```bash
make benchmark-auto
```

Dies startet den automatischen Benchmark für alle noch nicht getesteten Modelle.

**Optionale Parameter:**
- `AUTO=1` - Überspringt Bestätigungsabfragen
- `FORCE=1` - Erzwingt Re-Tests bereits getesteter Modelle
- `PROVIDER=<name>` - Testet nur Modelle eines Providers

**Beispiel für spezifischen Provider:**
```bash
make benchmark-auto PROVIDER=llamacpp_spark
```
