"""Thinking/Probe: Chain-of-Thought-Erkennung und Override-Auflösung.

Importiert aus ``model_card_io`` für Card-Lookups.
"""
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from utils.model_card_io import _find_card

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Thinking Probe
# ---------------------------------------------------------------------------
# Multi-Prompt-Discovery: drei Probe-Prompts (Mathe / Code / Decision),
# um familien-spezifische CoT-Patterns zuverlaessig zu erkennen. Manche
# Modelle zeigen CoT nur bei ethischen/Decision-Fragen, andere nur bei
# Code-Reasoning, wieder andere nur bei Mathematik.
# Discovery-Skript: scripts/tools/discover_thinking_tags.py
_PROBE_PROMPTS: dict[str, str] = {
    "math": (
        "Solve step by step: A train travels 120 km in 1.5 hours. "
        "What is its average speed in km/h? Show your reasoning."
    ),
    "code": (
        "Sort this list step by step and explain your algorithm: "
        "[3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]"
    ),
    "decision": (
        "Should an autonomous car swerve to avoid a pedestrian "
        "even if it risks the passenger's life? Think through the "
        "ethical considerations before answering."
    ),
}
# Backward-compat: alter Single-Prompt-Slot (Card-First-Hook).
_PROBE_PROMPT = _PROBE_PROMPTS["math"]
# Token-Budget fuer den Reasoning-Probe. Muss gross genug sein, dass ein
# Hybrid-Thinking-Modell (z. B. Qwen3.6-27B) seine interne Reasoning-Phase
# abschliesst UND sichtbaren Content emittiert. 512 (alter Wert) reichte
# nur fuer Reasoning, nicht fuer Output → Cold-Start-Guard klassifizierte
# Budget-Erschöpfung falsch als "0 chars output" (Qwen3.6-27B-VSPK, 2026-07-07).
# 4096 deckt typische Reasoning-Phasen (800-2500 Tokens) + Antwort ab.
_PROBE_MAX_TOKENS = 4096
# Schwelle (Anteil an _PROBE_MAX_TOKENS), ab der leerer Output + hohe
# reasoning_tokens als Budget-Erschöpfung (Thinking-Nachweis) gilt statt
# als Cold-Start-Artefakt. 90 % toleriert Off-by-one in Usage-Reporting.
_PROBE_BUDGET_EXHAUSTION_RATIO = 0.9

# Erweiterte Tag-Liste basierend auf Modell-Familien-Inventar.
# Quellen: Qwen 3/3.5/3.6, DeepSeek R1/V3, OpenAI OSS (gpt-oss),
# Anthropic Extended Thinking, Meta Llama 4, NousResearch Hermes,
# Mistral Magistral, GLM, Kimi, Gemma 4 (Channel-Tokens). Bei neu
# entdeckten Tags: hier ergaenzen + Test in tests/test_thinking_probe_families.py.
_THINK_TAGS: tuple[str, ...] = (
    "<think>", "<thinking>", "<thought>",            # Qwen 3/3.5/3.6, Magistral, GLM
    "<|thinking|>", "<|reasoning|>",                 # OpenAI OSS (gpt-oss)
    "<|channel|>",                                   # Gemma 4 (Channel-Token: <|channel|>analysis/thought/final)
    "<reasoning>", "<reason>",                       # DeepSeek R1/V3
    "<reflection>",                                  # Meta Llama 4 (Reflektion)
    "<analysis>", "<plan>",                          # Anthropic Extended Thinking
    "<scratchpad>",                                  # NousResearch Hermes
    "<solution>",                                    # Mistral Reasoning
    "<cot>",                                         # Custom / Future
)

# Inline-CoT-Detection: heuristisches Signal C fuer Modelle, die --reasoning off
# ignorieren und Chain-of-Thought direkt im content-Feld produzieren.
# Beobachtung: Gemma 4 26B-A4B mit llama.cpp --reasoning off liefert
# z.B. "OK, das ist eine einfache Geschwindigkeitsberechnung.
# v = s/t = 120/1.5 = 80. Die Antwort ist 80 km/h." (~1142 Zeichen).
# Eine direkte Antwort "v = s/t = 120/1.5 = 80 km/h" ist <100 Zeichen.
# Trigger: Antwort > Schwellwert UND mind. 2 Berechnungs-Operatoren.
_INLINE_COT_LENGTH_THRESHOLD = 200
_INLINE_COT_OPS = (" = ", " * ", " / ", "**", " + ", " - ")
# Mindestanzahl an Berechnungs-Operatoren, ab der inline CoT angenommen wird.
# 2 schliesst versehentliche '=' in Prosa aus (z. B. 'speed = distance / time').
_INLINE_COT_MIN_OPS = 2


def _has_inline_cot(text: str) -> bool:
    """Heuristik fuer Chain-of-Thought inline im content-Feld.

    Trigger-Bedingung: Antwort laenger als Schwellwert UND mindestens
    _INLINE_COT_MIN_OPS Berechnungs-Operatoren (z. B. ' = ', ' * ').
    Reduziert False-Positives bei langen aber mathe-freien Antworten
    (Code-Outputs, Prosa).
    """
    if not text or len(text) <= _INLINE_COT_LENGTH_THRESHOLD:
        return False
    op_count = sum(text.count(op) for op in _INLINE_COT_OPS)
    return op_count >= _INLINE_COT_MIN_OPS


def _find_think_tags(text: str) -> tuple[str, ...]:
    """Gibt alle in text gefundenen Think-Tags zurueck (lowercase match)."""
    if not text:
        return ()
    lower = text.lower()
    return tuple(tag for tag in _THINK_TAGS if tag in lower)


# Marker-Familie (ab v4.7.1 Card-Feld "cot_marker_family"):
# Heuristik-Mapping Tag-Set -> Familien-Kennung. Wird in Card geschrieben,
# damit Web-Export + Audit + Review einheitlich filtern koennen.
# Reihenfolge der Familien ist signifikant (erster Match gewinnt).
#
# WICHTIG: "think-xml" deckt ALLE Modelle ab, die <think>/<thought> nutzen —
# darunter Qwen 3/3.5/3.6 UND Magistral (Mistral Reasoning). Da beide
# Familien denselben Tag verwenden, ist eine tag-basierte Unterscheidung
# nicht moeglich. Die Familie heisst bewusst generisch "think-xml" statt
# "qwen-think", um die Irreführung zu vermeiden.
_COT_FAMILY_MAP: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("think-xml", ("<think>", "<thought>")),        # Qwen 3/3.5/3.6 + Magistral
    ("openai-oss", ("<|thinking|>", "<|reasoning|>")),
    ("channel-tags", ("<|channel|>",)),              # Gemma 4 (Channel-Token-Format)
    ("deepseek-reasoning", ("<reasoning>", "<reason>")),
    ("llama-cot", ("<reflection>",)),
    ("anthropic-extended", ("<analysis>", "<plan>")),
    ("hermes-scratchpad", ("<scratchpad>",)),
    ("mistral-reasoning", ("<solution>",)),
    ("glm-cot", ("<thinking>",)),
    ("generic-cot", ("<cot>",)),
)


def classify_cot_marker_family(tags_found: tuple[str, ...] | list[str] | None) -> str:
    """Leitet die CoT-Marker-Familie aus den gefundenen Tags ab.

    Eingabe: Tuple/Liste der Tags aus _find_think_tags() (lowercase).
    Ausgabe: Eine der Familien-Kennungen aus _COT_FAMILY_MAP, oder "none"
    wenn keine Tags erkannt wurden.

    Die Zuordnung erfolgt in der Reihenfolge von _COT_FAMILY_MAP; erste
    Familie, fuer die mindestens ein Tag aus dem Input passt, gewinnt.
    """
    if not tags_found:
        return "none"
    tag_set = {t.lower() for t in tags_found}
    for family, members in _COT_FAMILY_MAP:
        if tag_set.intersection(members):
            return family
    return "none"


@dataclass
class ThinkingProbeResult:
    detected: bool
    evidence: str
    confidence: Literal["high", "medium", "low"]
    # Multi-Prompt-Metadaten (Defaults erhalten Backward-Compat).
    prompts_used: tuple[str, ...] = ()
    tags_found: tuple[str, ...] = ()


def _is_budget_exhaustion(reasoning_tokens: int, actual_max_tokens: int, raw: str) -> bool:
    """True wenn reasoning_tokens das Budget vollständig verbraucht haben."""
    if reasoning_tokens <= 0 or raw.strip():
        return False
    budget_threshold = int(actual_max_tokens * _PROBE_BUDGET_EXHAUSTION_RATIO)
    return reasoning_tokens >= budget_threshold


def _classify_probe_response(
    raw: str,
    reasoning_tokens: int,
    actual_max_tokens: int,
    prompt_name: str,
) -> ThinkingProbeResult:
    """Klassifiziert eine Probe-Response anhand der Signale A/B/C.

    Returns:
        ThinkingProbeResult mit ``detected``, ``evidence`` und ``confidence``.
    """
    # Signal A -- explicit think-tags (high confidence)
    tags_found = _find_think_tags(raw)
    if tags_found:
        return ThinkingProbeResult(
            detected=True,
            evidence=(
                f"[{prompt_name}] Think-tag(s) gefunden: "
                f"{', '.join(tags_found)}. First 200 chars: {raw[:200]}"
            ),
            confidence="high",
            prompts_used=(prompt_name,),
            tags_found=tags_found,
        )

    # Signal B -- provider metadata reports reasoning tokens (medium)
    # Differenzierung bei leerem Output: zwei Szenarien erzeugen dasselbe
    # Pattern (reasoning_tokens > 0 + raw.strip() == ""), muessen aber
    # entgegengesetzt bewertet werden:
    #   (a) Echter Cold-Start (z. B. llama.cpp Gemma 4 26B-A4B-QAT beim
    #       ersten Request): reasoning_tokens deutlich < max_tokens, leerer
    #       Output wegen KV-Cache-Aufbau → kein Thinking-Nachweis (low).
    #   (b) Budget-Erschöpfung (z. B. Qwen3.6-27B Hybrid-Thinking): das
    #       Modell verbraucht das gesamte max_tokens-Budget fuer Reasoning
    #       (reasoning_tokens ≈ max_tokens) und emittiert 0 sichtbare
    #       Zeichen → STARKES Thinking-Signal (medium).
    # Unterscheidungskriterium: Verhaeltnis reasoning_tokens / max_tokens.
    # Ab _PROBE_BUDGET_EXHAUSTION_RATIO (90 %) liegt Fall (b) vor.
    if reasoning_tokens > 0:
        if not raw.strip():
            if _is_budget_exhaustion(reasoning_tokens, actual_max_tokens, raw):
                return ThinkingProbeResult(
                    detected=True,
                    evidence=(
                        f"[{prompt_name}] reasoning_tokens={reasoning_tokens} "
                        f"bei max_tokens={actual_max_tokens} — Budget vollständig "
                        f"für Reasoning verbraucht (0 chars sichtbarer Output). "
                        f"Budget-Erschöpfung = Thinking-Nachweis, kein Cold-Start."
                    ),
                    confidence="medium",
                    prompts_used=(prompt_name,),
                    tags_found=(),
                )
            # Genuine cold-start: reasoning_tokens deutlich unter Budget
            return ThinkingProbeResult(
                detected=False,
                evidence=(
                    f"[{prompt_name}] reasoning_tokens={reasoning_tokens} "
                    f"aber 0 chars output — Cold-Start-Verdacht "
                    f"(reasoning_tokens << max_tokens={actual_max_tokens}), "
                    f"kein Thinking-Nachweis."
                ),
                confidence="low",
                prompts_used=(prompt_name,),
                tags_found=(),
            )
        return ThinkingProbeResult(
            detected=True,
            evidence=(
                f"[{prompt_name}] reasoning_tokens={reasoning_tokens} "
                f"in provider metadata. First 200 chars: {raw[:200]}"
            ),
            confidence="medium",
            prompts_used=(prompt_name,),
            tags_found=(),
        )

    # Signal C -- inline CoT im content-Feld (medium)
    # Beobachtung: llama.cpp --reasoning off wird von manchen Modellen
    # (z.B. Gemma 4 26B-A4B) ignoriert; sie produzieren Chain-of-Thought
    # trotzdem direkt im content. Heuristik: lange Antwort + Berechnungen.
    if _has_inline_cot(raw):
        op_count = sum(raw.count(op) for op in _INLINE_COT_OPS)
        return ThinkingProbeResult(
            detected=True,
            evidence=(
                f"[{prompt_name}] Inline CoT im content-Feld: "
                f"Antwort {len(raw)} chars (>{_INLINE_COT_LENGTH_THRESHOLD}) "
                f"mit {op_count} Berechnungs-Operatoren. "
                f"First 200 chars: {raw[:200]}"
            ),
            confidence="medium",
            prompts_used=(prompt_name,),
            tags_found=(),
        )

    # No CoT signals detected
    return ThinkingProbeResult(
        detected=False,
        evidence=(
            f"[{prompt_name}] No CoT signals found "
            f"(A: no think-tags, B: reasoning_tokens=0, "
            f"C: len={len(raw)}<={_INLINE_COT_LENGTH_THRESHOLD} "
            f"or <{_INLINE_COT_MIN_OPS} ops). "
            f"Response length: {len(raw)} chars"
        ),
        confidence="low",
        prompts_used=(prompt_name,),
        tags_found=(),
    )


def _probe_single(
    model_id: str,
    provider_key: str,
    config: dict,
    prompt_name: str,
    prompt_text: str,
) -> ThinkingProbeResult:
    """Einzel-Probe: ein Prompt, ein ThinkingProbeResult.

    Raises:
        RuntimeError: wenn der API-Call fehlschlaegt.
    """
    from utils.llm_client import LLMClient  # local import to avoid circular deps

    logger.info(
        "[ThinkingProbe] Probing %s via %s (prompt=%s, %d chars) ...",
        model_id, provider_key, prompt_name, len(prompt_text),
    )
    print(
        f"   \u23f3 Sende Reasoning-Probe an '{model_id}' (prompt={prompt_name})...",
        flush=True,
    )

    client = LLMClient(config)
    try:
        raw = client.query(
            model=model_id,
            prompt=prompt_text,
            provider=provider_key,
            max_tokens=_PROBE_MAX_TOKENS,
        )
        print(
            f"   \u2713 Antwort erhalten ({len(raw)} Zeichen) -- analysiere...",
            flush=True,
        )
    except Exception as exc:
        raise RuntimeError(
            f"ThinkingProbe: API call failed for model '{model_id}' "
            f"(prompt={prompt_name}): {exc}"
        ) from exc

    reasoning_tokens: int = int(
        (client.last_response_metadata or {}).get("reasoning_tokens") or 0
    )
    # Tatsaechlich gesendetes max_tokens (kann < _PROBE_MAX_TOKENS sein, wenn
    # der Provider einen per-Modell-Cap oder Token-Fallback angewendet hat).
    # Wird fuer die Budget-Erschöpfungs-Schwelle benoetigt, damit die
    # Erkennung auch bei Models mit niedrigem max_tokens-Cap funktioniert.
    actual_max_tokens: int = int(
        (client.last_response_metadata or {}).get("token_limit_used")
        or _PROBE_MAX_TOKENS
    )

    return _classify_probe_response(raw, reasoning_tokens, actual_max_tokens, prompt_name)


def probe_thinking_model(
    model_id: str,
    provider_key: str,
    config: dict,
    *,
    prompts: dict[str, str] | str | None = None,
) -> ThinkingProbeResult:
    """
    Sends one or more reasoning prompts to the model and inspects the responses
    for Chain-of-Thought signals.

    Signal hierarchy:
      - high:  <think>/<thinking>/<thought>/<|...|>/<reason>/<reflection>/<analysis>/...
               tags present in response
      - medium: reasoning_tokens metadata > 0 (mit sichtbarem Output)
      - medium: Budget-Erschöpfung — reasoning_tokens >= 90 % von
               _PROBE_MAX_TOKENS bei leerem Output (Modell hat das gesamte
               Budget fuer Reasoning verbraucht; z. B. Qwen3.6-27B)
      - medium: inline CoT im content-Feld (Antwort >200 chars + mind. 2 Ops)
      - low:    no signal found (oder Cold-Start: reasoning_tokens > 0 +
               leerer Output, aber reasoning_tokens << max_tokens)

    detected = True if confidence in ("high", "medium")

    Args:
        model_id:     Modell-ID
        provider_key: Provider-Key (z.B. 'llamacpp', 'openrouter')
        config:       Vollstaendige benchmark_config
        prompts:      Probe-Prompts. None=alle 3 aus _PROBE_PROMPTS (math/code/decision).
                      str=Einzel-Prompt (backward-compat). dict={name: prompt} fuer
                      explizite Auswahl.

    Multi-Prompt-Aggregation: hoechste Confidence gewinnt. Wenn irgendein
    Prompt detected=True liefert, ist das Gesamtergebnis detected=True mit
    aggregierter Evidence.

    Raises:
        RuntimeError: wenn der API-Call fehlschlaegt (Card-First-Hook-Gate)
                      oder alle Multi-Prompts fehlschlagen.
    """
    # Backward-compat: str -> dict
    if prompts is None:
        prompts = _PROBE_PROMPTS
    elif isinstance(prompts, str):
        prompts = {"custom": prompts}

    # Single-Prompt-Pfad (Card-First-Hook, Test-Backward-Compat)
    if len(prompts) == 1:
        name, text = next(iter(prompts.items()))
        return _probe_single(model_id, provider_key, config, name, text)

    # Multi-Prompt: aggregiere
    results: list[ThinkingProbeResult] = []
    failures: list[Exception] = []
    for name, text in prompts.items():
        try:
            results.append(
                _probe_single(model_id, provider_key, config, name, text)
            )
        except RuntimeError as exc:
            logger.warning(
                "[ThinkingProbe] Probe '%s' failed for %s: %s",
                name, model_id, exc,
            )
            failures.append(exc)

    if not results:
        raise RuntimeError(
            f"ThinkingProbe: ALL {len(prompts)} probes failed for '{model_id}'. "
            f"First error: {failures[0] if failures else 'unknown'}"
        )

    # Confidence-Ranking
    rank = {"high": 3, "medium": 2, "low": 1}
    best = max(results, key=lambda r: rank[r.confidence])

    if any(r.detected for r in results):
        all_tags: tuple[str, ...] = tuple({
            tag for r in results for tag in r.tags_found
        })
        detected_lines = "\n".join(
            f"  - {r.prompts_used[0] if r.prompts_used else '?'}: {r.evidence}"
            for r in results if r.detected
        )
        return ThinkingProbeResult(
            detected=True,
            evidence=(
                f"Multi-Probe ({len(prompts)} prompts, "
                f"{sum(1 for r in results if r.detected)} detected, "
                f"best confidence={best.confidence}):\n{detected_lines}"
            ),
            confidence=best.confidence,
            prompts_used=tuple(prompts.keys()),
            tags_found=all_tags,
        )

    return ThinkingProbeResult(
        detected=False,
        evidence=(
            f"Multi-Probe ({len(prompts)} prompts, 0 detected, "
            f"best confidence={best.confidence}). "
            f"Best evidence: {best.evidence}"
        ),
        confidence=best.confidence,
        prompts_used=tuple(prompts.keys()),
        tags_found=(),
    )


# ---------------------------------------------------------------------------
# Thinking-SSoT-Auflösung (ab v4.7.1)
# ---------------------------------------------------------------------------
# Architektur (Option C): Thinking-Probe-Resultat aus der Model Card ist
# SSoT. Optionaler thinking_override in der provider_config.yaml ist
# ein expliziter Escape-Hatch für Spezialfälle (Cost-Benchmarks, A/B-Tests)
# mit Pflicht-Begründung und optionalem Expiry-Datum.
#
# Auflösungspriorität:
#   1. Aktiver Override (active_until nicht überschritten) → Override-Wert
#   2. Card-Probe-Ergebnis (thinking_probe_detected)
#   3. None (keine Information verfügbar)
#
# Audit: bei jeder Override-Anwendung wird ein Eintrag geloggt
# (Tag "thinking_override_applied" mit model_id, reason, card_value, override_value).


def _is_override_active(
    override: dict,
    now: datetime | None = None,
) -> bool:
    """
    Prüft, ob ein thinking_override aktuell aktiv ist.

    Inaktiv wenn:
      - `value` fehlt oder nicht bool
      - `reason` fehlt oder nur Whitespace (Pflichtfeld)
      - `active_until` gesetzt und in der Vergangenheit
    """
    if not isinstance(override, dict):
        return False
    if "value" not in override or not isinstance(override["value"], bool):
        return False
    reason = override.get("reason")
    if not reason or not str(reason).strip():
        return False

    active_until = override.get("active_until")
    if active_until:
        try:
            expiry = datetime.fromisoformat(str(active_until).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return False
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=UTC)
        check_now = now or datetime.now(UTC)
        if check_now >= expiry:
            return False
    return True


def resolve_effective_thinking(
    model_card: dict,
    provider_model_cfg: dict | None = None,
    *,
    model_id: str | None = None,
    now: datetime | None = None,
) -> tuple[bool | None, str]:
    """
    Loest das effektive Thinking-Flag fuer ein Modell auf.

    SSoT-Pfad: Card (Probe). Opt-in Override in provider_config.yaml
    gewinnt, wenn aktiv (siehe _is_override_active()).

    Args:
        model_card:           Model Card als dict.
        provider_model_cfg:   Optional: model_cfg-Block aus
                              config/provider_config.yaml. Erwartet
                              optionalen Key 'thinking_override'.
        model_id:             Optional: nur fuer Audit-Log (model_id).
        now:                  Optional: jetzt-Zeitpunkt (fuer Tests).

    Returns:
        Tuple (effective, source) mit:
          effective: True | False | None
            - True/False:  explizit gesetzt (durch Override oder Probe)
            - None:        keine Information (Card-Probe fehlt, kein Override)
          source:       "override" | "card_probe" | "none"
    """
    # 1. Override-Pfad
    if provider_model_cfg and isinstance(provider_model_cfg, dict):
        override = provider_model_cfg.get("thinking_override")
        if isinstance(override, dict) and _is_override_active(override, now=now):
            logger.info(
                "[ThinkingOverride] %s: override active (value=%s, reason=%s)",
                model_id or model_card.get("model_id", "?"),
                override["value"],
                override.get("reason"),
            )
            return (override["value"], "override")

    # 2. Card-Probe-Pfad (SSoT)
    detected = model_card.get("thinking_probe_detected")
    if detected is True or detected is False:
        return (detected, "card_probe")

    # 3. Keine Information
    return (None, "none")


def is_reasoning_model_from_card(model_id: str) -> bool | None:
    """
    Reads `thinking_probe_detected` from an existing model card JSON.

    Returns:
        True/False if the field is set; None if no card exists or field is missing.
    """
    card_path = _find_card(model_id)
    if not card_path.exists():
        return None
    try:
        data = json.loads(card_path.read_text(encoding="utf-8"))
        val = data.get("thinking_probe_detected")
        if val is None:
            return None
        return bool(val)
    except Exception:
        return None


def is_reasoning_model(model_name: str) -> bool:
    """
    Checks if the model is a reasoning model (Chain-of-Thought).
    Card lookup takes priority over string triggers; falls back to heuristic triggers.

    Args:
        model_name: Name of the model

    Returns:
        bool: True if it is a reasoning model
    """
    card_result = is_reasoning_model_from_card(model_name)
    if card_result is not None:
        return card_result
    # Fallback: Trigger-Liste aus config/card_vocabulary.yaml (SSoT).
    # Damit bleibt die Liste der Heuristik-Substrings konsistent mit der
    # Registry und kann zentral erweitert werden (siehe Reasoning-Trigger-
    # Sektion in der YAML).
    from utils.card_utils import get_reasoning_triggers
    triggers = get_reasoning_triggers()
    return any(t in model_name.lower() for t in triggers)


def is_thinking_optional_from_card(model_id: str) -> bool:
    """
    Returns True if the model card for *model_id* contains the tag
    ``"Thinking-Optional"`` in its ``architecture_tags`` list.

    Used by ``resolve_token_budget()`` to grant Thinking-Optional models the
    elevated reasoning budget — their internal thinking tokens consume the same
    ``max_output_tokens`` quota as the visible output.

    Returns False if no card exists, the field is absent, or the tag is not set.
    """
    card_path = _find_card(model_id)
    if not card_path.exists():
        return False
    try:
        data = json.loads(card_path.read_text(encoding="utf-8"))
        tags = data.get("architecture_tags", [])
        return "Thinking-Optional" in (tags or [])
    except Exception:
        return False


def _read_max_output_tokens_from_card(model_id: str) -> int | None:
    """
    Liest ``max_output_tokens`` aus der Model Card.

    Gibt den Wert zurück, wenn er als positive Ganzzahl in der Card vorhanden ist,
    sonst None. Wird von ``resolve_token_budget()`` als harte Obergrenze verwendet,
    damit modellspezifische API-Limits (z.B. gpt-4o-2024-05-13: max 4096) direkt
    im ersten Request gesetzt werden und der Fallback-Retry entfällt.
    """
    card_path = _find_card(model_id)
    if not card_path.exists():
        return None
    try:
        data = json.loads(card_path.read_text(encoding="utf-8"))
        val = data.get("max_output_tokens")
        if isinstance(val, int) and val > 0:
            return val
    except Exception:
        pass
    return None
