# Corrections

Dokumentierte Fehler, Korrekturen und Modell-spezifische Verhaltens-Anomalien,
die in zukünftigen Sessions erkannt werden müssen, ohne die Diagnose zu wiederholen.

---

## Anthropic: Safety-Refusals bei Opus 5 (2026-08-19)

**Befund:** Claude Opus 5 produziert für bestimmte harmlose Code-Review-Tests einen
Safety-Refusal (`finish_reason="refusal"`), obwohl die Aufgabe inhaltlich unverfänglich ist.

**Beispiel 1:** `benchmark_modules/reasoning_logic/assets/asset_5a_error_recovery.yaml`
(Reasoning 5A: Code Logic Debugging — "Infinite Loop Detection"). Prompt enthält die
Schlüsselbegriffe "freeze", "hangs", "infinite loop", "invalid". Opus 5 refuset
mit `finish_reason="refusal"`, leerem Content, `output_tokens=0`.

**Beispiel 2:** `benchmark_modules/reasoning_logic/assets/asset_5e_nested_paradox.yaml`
(Reasoning 5E: The Nested Transaction Paradox). Distributed-Systems-Architektur-Frage
mit den Schlüsselbegriffen "transaction commit", "async operations", "blocking",
"cleanup jobs". Identisches Symptom (`finish_reason=refusal`, `output_tokens=0`),
anderes Prompt-Pattern — stützt die Hypothese, dass Opus 5 **mehrere**
Code-/System-Patterns triggert (nicht nur ein einzelnes Schlüsselwort-Muster).

**Vergleich Opus 4.7 auf demselben Test:** `percentage=81%`, `tokens_used=1405`,
`finish_reason="end_turn"` → kein Refusal. Verhalten ist **modell-spezifisch**, nicht
test-spezifisch.

**Hypothese:** Anthropic hat die Safety-Filter der Opus-5-Generation strenger kalibriert
als in Opus 4.x. Bestimmte Schlüsselbegriff-Muster (Code mit "endless loop", "freeze",
"hangs") triggern den Filter, obwohl die Aufgabe ein Standard-Code-Review ohne
Boshaftigkeit ist.

**Folge für den Benchmark:**
- Tests mit solchen Pattern-Begriffen können für Opus 5 nicht ausgewertet werden
  (`refusal_flag=true`, `percentage=0`, `judge_progress_status="⚠️ Judge: skip"`).
- Cross-Modell-Vergleiche bleiben valide — die anderen Modelle (Sonnet 4.5/4.6/5,
  Opus 4.5/4.6/4.7/4.8) zeigen das Verhalten nicht.
- Leaderboard-Aggregation mittelt das konsequent; keine Korrektur nötig.

**Was NICHT zu tun ist:**
- Test-Prompts nicht umformulieren, um den Refusal zu umgehen — das wäre ein
  Bias und würde Cross-Run-Vergleichbarkeit zerstören.
- Connector nicht ändern, um `think_content` als Fallback zu nutzen — der
  Refusal ist eine bewusste Modell-Entscheidung, kein technischer Defekt.

**Connector-Stand:** `utils/providers/anthropic.py:152-160` macht bei
`stop_reason == "refusal"` `return ""`. `think_content` wird zwar via
`_extract_think_content(response.content)` extrahiert, aber durch den frühen
`return ""` verworfen (landet nur in `last_response_metadata`, nicht in
ExecResult/CSV). Das ist akzeptiert — die fehlende Sicht auf den Thinking-Trace
ist eine bewusste Konsequenz der Refusal-Behandlung.

**Verifikations-Datum:** 2026-08-19 (zweiter Fall 5E am gleichen Tag bestätigt)

---

## Anthropic: `temperature` deprecated für Opus 5 / Sonnet 5 / Opus 4.7+ (2026-08-19)

**Befund:** API liefert HTTP 400 — `invalid_request_error — 'temperature' is deprecated for this model`.

**Ursache:** Adaptive Thinking (alle Modelle ab Opus 4.7, Sonnet 4.6, alle 5er) deprecated den `temperature`-Parameter.

**Lösung:** `claude-opus-5` in `utils/constants.py:ANTHROPIC_NO_TEMPERATURE_MODELS` ergänzt.
Der Connector prüft diese Liste in `utils/providers/anthropic.py:124` und überspringt
`temperature` für gelistete Modelle.

**Pflege:** Bei jedem neuen Anthropic-Modell mit Adaptive Thinking MUSS die Liste erweitert
werden — sonst 400-Fehler bei allen API-Calls (ThinkingProbe + Benchmark).

**Verifikations-Datum:** 2026-08-19

---
