# v4.7.4 Heartbeat-Configurable — Implementation Detail

Vollständige Referenz für das v4.7.4 Feature. Hot-Context (systemPatterns.md) zeigt nur die SSoT-Brücke; hier ist der vollständige Code + Config + Test-Coverage.

**Datum:** 2026-06-10
**Status:** Abgeschlossen, additiv ohne API-Bruch

---

## Motivation

Bei mehrstündigen Läufen (z.B. 397B-Modelle mit Refusal-Retries) sieht der Beobachter im Terminal nur die Startmeldung und dann Stille. Lösung: Heartbeat-Thread + Retry-Indikatoren. Hardcodiertes 60s-Intervall spammte das Terminal — User-Praxis-Feedback: 120s gibt Sichtbarkeit ohne Ablenkung.

---

## Architektur

### `UnifiedBenchmarkRunner._get_heartbeat_config()`

```python
def _get_heartbeat_config(self) -> tuple[bool, float]:
    """Liest heartbeat-Konfiguration aus der Benchmark-Config.
    
    Returns: (enabled, interval_seconds)
    Defensiv-Fallback auf (True, 60.0) bei allen Fehlerquellen.
    """
    cfg = self.validator.config.get("heartbeat", {}) or {}
    if not isinstance(cfg, dict):
        return True, 60.0  # Block ist kein Dict
    enabled = bool(cfg.get("enabled", True))
    raw_interval = cfg.get("interval_seconds", 60.0)
    try:
        interval = float(raw_interval)
    except (TypeError, ValueError):
        interval = 60.0  # nicht-numerisch
    if interval <= 0:
        interval = 60.0  # <= 0
    return enabled, interval
```

### Heartbeat-Branch in `_run_asset_loop()`

```python
heartbeat_enabled, heartbeat_interval = self._get_heartbeat_config()  # nach State-Init
...
heartbeat_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
if heartbeat_enabled:
    heartbeat_thread.start()
else:
    # Deaktivierter Heartbeat: Event bleibt gesetzt, damit ggf. join() im
    # finally-Block sauber durchläuft ohne dass der Thread je lief.
    self._heartbeat_stop.set()
    heartbeat_thread = None  # Sentinel: im finally prüfen
...
finally:
    self._heartbeat_stop.set()
    if heartbeat_thread is not None:  # None-Sentinel
        heartbeat_thread.join(timeout=2.0)
    print(" " * 120, end="\r", flush=True)
```

### `_handle_heartbeat_signal()` und `_print_asset_status()`

Status-Icons: ✓ (Erfolg), ❌ (Error), 🔁 (Refusal mit erfolgreichem Retry), ⛔ (Hard Refusal nach 2 Retries). Optional `(×N)`-Suffix zeigt Retry-Counter.

### Integration in `political_compass/test.py`

`_run_single_block()` ruft an 4 strategischen Punkten `self._notify_heartbeat(...)` auf:
- Vor `break` aus der Retry-Loop: `is_retry=False` (Heartbeat wieder auf "Test")
- Beim `refusal_retry_count += 1`: `is_retry=True, retry_info="Retry N/2 temp 0.4"`
- Nach `PC_SLEEP_AFTER_RESPONSE`: nochmal `is_retry=False`
- `_notify_heartbeat()` ruft graceful `self._benchmark_runner._handle_heartbeat_signal(...)` auf — no-op wenn Runner nicht gesetzt, swallowed exceptions

Wiring in `_execute_test_with_timing()`:
```python
if test_instance is not None:
    setattr(test_instance, "_benchmark_runner", self)
```

---

## Konfiguration (`benchmark_config.yaml`)

```yaml
# Heartbeat: Status-Prints während langer Benchmarks (verhindert "hängt das?"-Frage)
# Konfiguriert den Daemon-Thread in scripts/core/unified_runner.py::_run_asset_loop
heartbeat:
  enabled: true              # Komplett ausschalten (z.B. CI-Runs, kurze Tests)
  interval_seconds: 120      # Sekunden zwischen Status-Prints
                             # 60  = Original-Verhalten
                             # 120 = Default (maximale Ruhe bei langen Läufen)
```

Beide Dateien (`benchmark_config.yaml` + `benchmark_config.example.yaml`) wurden aktualisiert.

---

## Defensiv-Fallback-Hierarchie (alle Wege führen zu `(True, 60.0)`)

1. `heartbeat:`-Block fehlt komplett → `(True, 60.0)` (backward-compat)
2. Block ist kein Dict (z.B. String) → `(True, 60.0)`
3. `interval_seconds` nicht-numerisch (z.B. `"abc"`, `None`, `[]`, `{}`) → `60.0`
4. `interval_seconds <= 0` (z.B. `0`, `-1`, `0.0`, `-0.5`) → `60.0`

**Robustheits-Begründung:** Defensiv > strikt. Heartbeat ist nice-to-have, ungültige Config darf den Benchmark nicht abbrechen. `try/except` + `isinstance`-Checks statt `pydantic`-Validation.

**None-Sentinel für optionale Threads:** `finally`-Block muss zwischen "Thread läuft" und "Thread wurde nie gestartet" unterscheiden. `if heartbeat_thread is not None:` Guard vor `join()`.

**Backward-Compat:** `interval=60.0` als Fallback für Configs ohne Block — alte Läufe sehen identisches Verhalten.

---

## Test-Coverage (`tests/test_unified_runner_heartbeat.py`)

- 17 neue Tests in 4 Klassen:
  - `TestGetHeartbeatConfig` (16 parametrisiert): Defaults, explicit, partial, zero/negative, non-numeric, non-dict
  - `TestPrintAssetStatus`, `TestHandleHeartbeatSignal`
  - `TestHeartbeatLifecycle` (bestehend, angepasst)
  - `TestPoliticalCompassHeartbeatIntegration`
  - `TestHeartbeatDisabledInRunAssetLoop::test_disabled_heartbeat_starts_no_thread`

- Bestehende `TestHeartbeatLifecycle` Tests angepasst: `_make_runner()` Helper bekam `validator`-Mock mit leerer Config, damit `validator.config.get(...)` nicht fehlschlägt.

- 33/33 Heartbeat-Tests grün, 603/603 Regression grün (2 pre-existing Failures in `test_id_ssot_invariants.py` + `test_provider_health_preflight.py` nicht durch Heartbeat-Änderung verursacht).

---

## Beispiel-Output

```
⏳ [4/79] political_compass_7.1.004: Test läuft...   [3.5s später]
🔁 [qwen/qwen3.5-397b-a17b] Refusal detected on political_compass_7.1.004. Retrying 1/2 with temp 0.4 (anti-diplomat system-prompt aktiv)…
   💓 ⏱ 00:01:12 elapsed | 4/79 | Test: political_compass_7.1.004 | Retry 1/2 temp 0.4 | Letzte Aktivität: 0s her
   💓 ⏱ 00:02:12 elapsed | 4/79 | Retry: political_compass_7.1.004 | Retry 2/2 temp 0.7 | Letzte Aktivität: 0s her
   💓 ⏱ 00:03:12 elapsed | 4/79 | Test: political_compass_7.1.004 | Letzte Aktivität: 87s her
✓ [4/79] political_compass_7.1.004: 76.0% | 142 T | 87.2s
```

---

## Lessons Learned (goldene Regeln)

1. **Hardcodierte UX-Defaults sind ein Bug** — 60s spammt, 120s passt. User-Praxis-Feedback ist die einzige valide Quelle für Print-Frequenz.
2. **Defensiv-Fallback in SSoT-Helpern > strikte Validierung** — nice-to-have-Features dürfen bei Config-Fehlern nicht abbrechen.
3. **None-Sentinel für optionale Threads** — der `finally`-Block braucht eine explizite Unterscheidung zwischen "Thread läuft" und "Thread wurde nie gestartet".
4. **Additiver Patch ohne API-Bruch** — `_heartbeat_loop`-Output, Thread-Signatur und State-Init bleiben identisch. Kein Migrationsaufwand für bestehende Configs.

---

## Geänderte Dateien

- `scripts/core/unified_runner.py` — `_get_heartbeat_config()` + Heartbeat-Branch
- `benchmark_config.yaml` + `benchmark_config.example.yaml` — neuer `heartbeat:`-Block
- `tests/test_unified_runner_heartbeat.py` — 17 neue Tests + Anpassungen
- `docs/BENCHMARK_SCRIPT_OVERVIEW.md §6` — "Runtime Feedback (Heartbeat)" Sektion
- `CHANGELOG.md` — v4.7.4 Eintrag
- `README.md` — Version-Badge + Feature-Bullet
- `PROJECT_STATUS.md` — Header auf v4.7.4
- `memory-bank/` (vorher) — activeContext, progress, techContext (jetzt: reference/heartbeat-v474-detail.md)
