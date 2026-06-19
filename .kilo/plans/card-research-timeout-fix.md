# Plan: card-research Timeout-Fix & Pause zwischen Cards

## Problem

`make card-research` ist bei Card [10/15] `gemma-4-31B-it-UD-Q8_K_XL-mtp` hängen geblieben:
- 23:05:07 — 1. LLM-Timeout (Versuch 1/3), Retry in 2.0s
- 23:11:11 — 2. LLM-Timeout (Versuch 2/3), **~6 Min. statt 2s**
- User hat `^C` gedrückt

**Ursache:** Der HTTP-Timeout von 120s (`PER_CALL_TIMEOUT_S`) wird vom httpx-Transport im OpenAI-SDK möglicherweise nicht korrekt als Gesamt-Timeout interpretiert. Der Server `100.89.110.0:1235` antwortet nicht, und der Client wartet minutenlang.

## Änderungen

### 1. Timeout auf httpx-Ebene erzwingen (`manage_model_cards.py:166-183`)

**Aktuell:**
```python
class LLMSession:
    def __init__(self, ..., timeout_s: int, ...) -> None:
        kwargs: dict[str, Any] = {"timeout": float(timeout_s)}
        ...
        self._client = OpenAI(**kwargs)
```

**Neu:** Explizites `httpx.Timeout` setzen, das alle Phasen abdeckt (connect + read + pool):
```python
import httpx

class LLMSession:
    def __init__(self, ..., timeout_s: int, ...) -> None:
        timeout = httpx.Timeout(timeout=timeout_s, connect=10.0, read=timeout_s, pool=timeout_s)
        kwargs: dict[str, Any] = {"timeout": timeout}
        ...
        self._client = OpenAI(**kwargs)
```
- `connect=10.0`: Schneller Fehler bei Erreichbarkeitsproblemen
- `read=timeout_s`: Max. Wartezeit auf Server-Antwort
- `pool=timeout_s`: Max. Zeit für Connection-Pool-Operationen

### 2. Default-Timeout reduzieren (`manage_model_cards.py:62`)

**Aktuell:** `PER_CALL_TIMEOUT_S = 120`
**Neu:** `PER_CALL_TIMEOUT_S = 60`

120s ist zu lang für einen nicht-antwortenden Server. 60s ist responsiv genug für lokale LLMs (die typisch 10–45s pro Response brauchen) und schnell genug, um fehlzuschlagen wenn der Server hangt.

### 3. Pause zwischen Cards (`manage_model_cards.py:594-597`)

Zwischen jeder Card-Verarbeitung eine kurze Pause einfügen, um den Server zu entlasten:

```python
for idx, (mid, path) in enumerate(targets, 1):
    if idx > 1:
        pause = getattr(self.args, 'pause', 1.0)
        time.sleep(pause)
    print(f"\n[{idx}/{len(targets)}] {mid}")
    ...
```

Makefile-Integration:
```makefile
card-research:
	@$(PYTHON) scripts/manage_model_cards.py --mode research \
		$(if $(MODEL),--card "$(MODEL)",) \
		$(if $(FORCE),--force,) \
		$(if $(DRY),--dry-run,) \
		$(if $(PAUSE),--pause "$(PAUSE)",)
```

Neues Flag in `khelp`: `PAUSE=sek` — Pause zwischen Cards (Default: 1.0s)

### 4. CLI-Argument für Timeout (`manage_model_cards.py`)

Bestehendes `--timeout-s` beibehalten, aber Default auf 60 setzen (bereits in Zeile 1029: `default=PER_CALL_TIMEOUT_S` — ändert sich automatisch mit Konstante).

## Zusammenfassung der Änderungen

| Datei | Zeile | Änderung |
|-------|-------|----------|
| `manage_model_cards.py` | 31 | `import httpx` hinzufügen |
| `manage_model_cards.py` | 62 | `PER_CALL_TIMEOUT_S = 60` (von 120) |
| `manage_model_cards.py` | 166–183 | `LLMSession.__init__` mit `httpx.Timeout` |
| `manage_model_cards.py` | 594–597 | Pause zwischen Cards in `Researcher.run()` |
| `manage_model_cards.py` | 1028 | `--pause` CLI-Argument hinzufügen |
| `Makefile` | 170–178 | `PAUSE`-Variable im Makefile-Target |

## Nicht geändert (begründet)

- **Thread-Parallelisierung:** Dein lokaler LLM-Server (GGUF/single-process) wird wahrscheinlich keine parallelen Requests gut verarbeiten. Erst stabilisieren, dann evaluieren.
- **Kontextfenster:** Kein Problem — jeder Card-Call ist isoliert, kein Conversation-History.
