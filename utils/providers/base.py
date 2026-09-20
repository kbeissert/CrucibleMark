"""
Provider-spezifische LLM Clients
Getrennte Implementierungen für Ollama, Anthropic, Mistral
"""
import logging
import os
import re
from typing import Any
from collections.abc import Callable
logger = logging.getLogger(__name__)

# Budget-/Quota-Fehlererkennung mit Word-Boundaries: Substring-Matching
# (``"budget" in err_str``) matcht fälschlich Parameternamen wie
# ``thinking_budget`` (Alibaba/Qwen-HTTP-400: "max_completion_tokens must be
# greater than thinking_budget") — Underscore ist ein Word-Charakter, daher
# greift \b dort nicht. Phrasen ohne Ambiguität bleiben Substring-Matches.
_BUDGET_ERROR_PATTERN = re.compile(r"\b(quota|budget|billing|credits?|payment)\b")
_BUDGET_ERROR_PHRASES = (
    "insufficient_funds",
    "402 payment required",
    "exceeded your current quota",
)


class ThinkAccumulator:
    """Streaming-Helper für Think-Content-Akkumulation (SSoT).

    Alle Provider, die Reasoning/Thinking-Content im Streaming-Modus
    empfangen, nutzen diesen Accumulator statt eigener ``think_parts: list[str]``.

    Usage::

        think = ThinkAccumulator()
        for chunk in response:
            think.add(getattr(chunk.choices[0].delta, "reasoning", None))
        if think.has_content:
            meta["think_content"] = think.content
    """

    __slots__ = ("_parts",)

    def __init__(self) -> None:
        self._parts: list[str] = []

    def add(self, text: str | None) -> None:
        """Einzelnes Chunk anhängen (None/leer wird ignoriert)."""
        if text:
            self._parts.append(str(text))

    @property
    def content(self) -> str | None:
        """Zusammengesetzter Think-Content oder None."""
        return "".join(self._parts) if self._parts else None

    @property
    def has_content(self) -> bool:
        return bool(self._parts)
class BaseProviderClient:
    """Basis-Klasse für Provider-spezifische Clients"""

    # Liste der logischen Provider-Namen, für die dieser Client verantwortlich ist (z.B. ["openai"])
    PROVIDER_NAMES: list[str] = []

    # Config-Key unter providers.commercial (z.B. "openrouter", "openai", "anthropic").
    # Subklassen setzen diesen Wert, damit _resolve_request_tokens() die richtige
    # Provider-Config laden kann. None = kein Provider-Config-Lookup (z.B. Ollama).
    PROVIDER_CONFIG_KEY: str | None = None

    # Standard-Token-Parametername, falls nicht in der Config definiert.
    DEFAULT_TOKEN_PARAM: str = "max_tokens"

    # Registry aller Clients
    _registry: dict[str, type] = {}

    def __init_subclass__(cls, **kwargs):
        """Automatische Registrierung von Subklassen"""
        super().__init_subclass__(**kwargs)
        for name in getattr(cls, "PROVIDER_NAMES", []):
            BaseProviderClient._registry[name] = cls

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.last_response_metadata = {}
        self.fingerprint_cache = {}

    @staticmethod
    def _resolve_env_ref(raw: str, default: str = "sk-local") -> str:
        """Löst ``${VAR}``-Referenzen in Config-Werten über die Umgebung auf.

        SSoT für die api_key-Auflösung der lokalen Server-Connectoren
        (llama.cpp, vLLM): Tokens stehen in ``.env``, nicht im Git-tracked
        Config-File. Fehlt die Variable, greift der Default (lokaler
        Proxy-Fallback) — Fail-Soft analog zur bisherigen vllm_base-Logik.
        """
        if isinstance(raw, str) and raw.startswith("${") and raw.endswith("}"):
            return os.environ.get(raw[2:-1], default)
        return raw
    def get_fingerprint(self, model: str) -> str:
        """
        Retrieves or generates a fingerprint for the given model.
        Should be implemented/used by subclasses for commercial models.
        """
        # Default behavior: return model version from API or unknown
        # Since local Ollama models have their own mechanism in provider_clients?
        # Actually Ollama fingerprint is generated in get_model_version inside model_utils.py.
        # But we want to unify this if possible or just use this for commercial.
        return "unknown"
    def query(
        self,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler: Callable[[str], None] | None = None,
        **kwargs,
    ) -> str:
        """
        Query API
        Args:
            model: Modell-Name
            prompt: Prompt-Text
            temperature: Temperature
            stream_handler: Optional callback for streaming output chunks
            **kwargs: Extra arguments (e.g. max_tokens)
        Returns:
            Response-Text
        """
        raise NotImplementedError
    def get_available_models(self) -> list[str]:
        """Listet verfügbare Modelle"""
        raise NotImplementedError
    def close(self) -> None:
        """Schließt dauerhafte HTTP-Connections des Providers (Default: nichts).

        Subklassen mit gecachten OpenAI-/httpx-Clients überschreiben dies,
        damit beim Programm-Ende (Ctrl+C, sys.exit, Exception) ein TCP FIN an
        den Server geht. Sonst erkennt z. B. vLLM einen client-seitig
        abgebrochenen Request nicht und generiert weiter, bis das
        OS-TCP-Keepalive greift (Linux-Default ~2 h).
        """
    def is_accessible(self) -> bool:
        """
        Prüft, ob der Provider zugänglich ist (API Key, Budget/Quota).
        Standardmäßig True, sollte von Subklassen überschrieben werden.
        """
        return True

    def _get_provider_cfg(self) -> dict[str, Any]:
        """Lädt die Provider-Config aus provider_config.yaml (commercial-Pfad).

        Returns {} wenn PROVIDER_CONFIG_KEY nicht gesetzt ist oder die Config fehlt.
        """
        key = self.PROVIDER_CONFIG_KEY
        if not key:
            return {}
        return self.config.get("providers", {}).get("commercial", {}).get(key, {})

    def _resolve_request_tokens(
        self,
        model: str,
        kwargs: dict,
    ) -> tuple[str, int]:
        """Zentrale Token-Budget-Auflösung für alle API-Provider (SSoT).

        Zweistufige Kaskade (Config-Driven):
          1. ``resolve_token_budget()`` — Reasoning-/Thinking-Erkennung + Modul-Budgets
             aus benchmark_config.yaml
          2. Provider-Default ``max_tokens`` — Obergrenze für ALLE Modelle dieses Providers
          3. Per-Model Override ``model_max_tokens[model_id]`` — überschreibt den Provider-Default
             für einzelne Modelle (z.B. kimi-k2.7-code braucht mehr als der Standard)

        Die Kaskade ist: ``min(resolve_budget, model_override ?? provider_default)``.
        Modelle ohne expliziten Override erben den Provider-Standard.

        Args:
            model: Modell-ID (z.B. "moonshotai/kimi-k2.6")
            kwargs: Query-Kwargs (enthält ``max_tokens`` und ``_module_key``)

        Returns:
            (token_param_name, effective_tokens)
        """
        from utils.model_utils import resolve_token_budget

        provider_cfg = self._get_provider_cfg()
        token_param_name = provider_cfg.get("token_param_name", self.DEFAULT_TOKEN_PARAM)

        # 1. Reasoning-/Thinking-Budget auflösen
        req_tokens, _ = resolve_token_budget(
            model, kwargs.get("max_tokens"), self.config, kwargs.get("_module_key"),
            exact=bool(kwargs.get("_budget_exact")),
        )

        # 2. Wirksamer Cap (Kaskaden-SSoT: _resolve_effective_budget_cap)
        #    AUSNAHME Last-Resort (``_cap_bypass=True``): Der letzte Leiter-
        #    Versuch überspringt die Kaskade bewusst — das geöffnete Budget
        #    (reasoning_reask.last_resort_budget) muss ankommen. Der Bypass ist
        #    auf den einzelnen Request beschränkt und wird geloggt.
        if kwargs.get("_cap_bypass"):
            logger.warning(
                "   🚨 Cap-Bypass aktiv (Last-Resort): Budget %s wird OHNE "
                "Provider-/Card-Cap gesendet (dokumentierter Ausnahmelauf).",
                kwargs.get("max_tokens"),
            )
        else:
            effective_cap = self._resolve_effective_budget_cap(model)
            if effective_cap is not None:
                req_tokens = min(req_tokens, effective_cap)

        return token_param_name, req_tokens

    def _resolve_effective_budget_cap(self, model: str) -> int | None:
        """Wirksamer Request-Cap für ein Modell (Kaskaden-SSoT, Session 110).

        Kaskade:
          1. Per-Model Override ``model_max_tokens[model_id]`` (Config- oder
             Internal-Form) — überschreibt den Provider-Default
          2. Provider-Default ``max_tokens``
          3. Card-Cap ``max_output_tokens`` (modellspezifische API-Grenze)

        Rückgabe = ``min(Override ?? Provider-Default, Card-Cap)``. Die
        Eskalationsleiter MUSS diesen wirksamen Cap sehen (``budget_cap``) —
        sonst sind still gecappte Re-Asks sinnlose Zweit-Requests mit
        identischem Budget (Befund Session 110: Override 24000 cappte den
        „Re-Ask mit 32000" unsichtbar; Erfolg nur durch Modell-Varianz).
        """
        from utils.model_thinking import _read_max_output_tokens_from_card
        from utils.model_utils import internal_id_to_config_form

        provider_cfg = self._get_provider_cfg()
        # `or {}` — eine leere YAML-Struktur (`model_max_tokens:`) liefert None,
        # und der .get()-Default greift nur bei fehlendem, nicht bei None-Wert.
        model_limits = provider_cfg.get("model_max_tokens") or {}
        config_form = internal_id_to_config_form(model)
        cap = model_limits.get(model)
        if cap is None:
            cap = model_limits.get(config_form)
        if cap is None:
            cap = provider_cfg.get("max_tokens")

        card_cap = _read_max_output_tokens_from_card(model)
        if card_cap is None:
            return cap
        if cap is None:
            return card_cap
        return min(cap, card_cap)

    # ── Reasoning/Thinking Extraction Utilities (SSoT) ──────────────────

    @staticmethod
    def _extract_reasoning_tokens(usage: Any) -> int | None:
        """Extrahiert reasoning_tokens aus einem Usage-Objekt (provider-agnostisch).

        Prüft der Reihe nach:
        1. ``usage.completion_tokens_details.reasoning_tokens`` (OpenAI-kompatibel:
           OpenAI, Groq, xAI, OpenRouter, Mistral, llama.cpp)
        2. ``usage.output_tokens_details.reasoning_tokens`` (Anthropic)
        3. ``usage.reasoning_tokens`` (Mistral-Fallback)

        Returns ``None`` wenn kein Feld vorhanden oder ``usage`` falsy.
        """
        if not usage:
            return None
        # Pfad 1: OpenAI-kompatibel (completion_tokens_details)
        details = getattr(usage, "completion_tokens_details", None)
        if details:
            rt = getattr(details, "reasoning_tokens", None)
            if rt is not None:
                return rt
        # Pfad 2: Anthropic (output_tokens_details)
        out_details = getattr(usage, "output_tokens_details", None)
        if out_details:
            rt = getattr(out_details, "reasoning_tokens", None)
            if rt is not None:
                return rt
        # Pfad 3: Mistral-Fallback (direktes Feld auf usage)
        return getattr(usage, "reasoning_tokens", None)

    @staticmethod
    def _estimate_reasoning_tokens(
        completion_tokens: int,
        content: str,
        reasoning: str,
    ) -> int | None:
        """Schätzt reasoning_tokens wenn der Server sie nicht liefert (vLLM 0.25.1).

        vLLM 0.22+ benennt das Feld ``reasoning_content`` → ``reasoning`` um und
        befüllt ``completion_tokens_details.reasoning_tokens`` nicht zuverlässig.
        Diese Heuristik wird nur als Fallback verwendet, wenn
        ``_extract_reasoning_tokens()`` ``None`` zurückgibt.

        Strategie:
        1. Kein Reasoning-Text → 0 (kein Thinking stattgefunden)
        2. Kein Content-Text → completion_tokens (alles ist Reasoning)
        3. Beide vorhanden → completion_tokens − geschätzte Content-Tokens
           (Content-Tokens ≈ len(content) / 4, grobe Char-to-Token-Ratio)

        Args:
            completion_tokens: ``usage.completion_tokens`` vom Server
            content: Sichtbarer Antwort-Text (``message.content``)
            reasoning: Thinking-Text (``message.reasoning`` / ``reasoning_content``)

        Returns:
            Geschätzte Reasoning-Token-Anzahl oder ``None`` bei unzureichenden Daten
        """
        if not reasoning:
            return 0
        if not content or not content.strip():
            return completion_tokens or 0
        if not completion_tokens:
            return None
        estimated_content_tokens = max(1, len(content) // 4)
        return max(0, completion_tokens - estimated_content_tokens)

    @staticmethod
    def _extract_think_from_message(
        msg: Any,
        field_names: tuple[str, ...] = ("reasoning", "reasoning_content", "think_content"),
    ) -> str | None:
        """Extrahiert Think-Content aus einer Message (provider-agnostisch).

        Versucht ``getattr(msg, field)`` für jedes ``field_names``-Element.
        Returns den ersten nicht-leeren Treffer oder ``None``.

        Args:
            msg: OpenAI-kompatibles Message-Objekt (``.reasoning``, ``.reasoning_content``, etc.)
            field_names: Zu prüfende Attributnamen (Reihenfolge = Priorität)
        """
        if not msg:
            return None
        for field in field_names:
            val = getattr(msg, field, None)
            if val:
                return str(val)
        return None

    # ── Token Fallback ─────────────────────────────────────────────────

    def _execute_with_token_fallback(
        self,
        func: Callable,
        token_param_name: str,
        initial_max_tokens: int,
        error_keywords: list[str],
        func_kwargs: dict
    ) -> tuple[Any, int, bool]:
        """
        Führt einen API-Aufruf mit kaskadierendem Token-Fallback aus ("Kopfnoten"-Tracking).
        Gibt (Response, used_max_tokens, fallback_triggered) zurück.
        """
        # Globale Fallback-Kaskade laden (z.B. [4096, 2048, 1024])
        cascade = self.config.get("defaults", {}).get("token_limits", {}).get(
            "fallback_cascade", [8192, 4096, 2048, 1024]
        )
        # Liste der zu probierenden Limits aufbauen (absteigend, strikt kleiner als initial_max_tokens)
        valid_cascade = [t for t in cascade if t < initial_max_tokens]
        tokens_to_try = [initial_max_tokens] + valid_cascade
        fallback_triggered = False
        last_exception = None
        for current_tokens in tokens_to_try:
            if current_tokens < initial_max_tokens:
                fallback_triggered = True
                logger.warning(
                    f"⚠️ Token limit rejected. Retrying with fallback limit: {current_tokens} tokens."
                )
            func_kwargs[token_param_name] = current_tokens
            max_rate_limit_retries = 3
            rate_limit_attempts = 0
            while rate_limit_attempts < max_rate_limit_retries:
                try:
                    response = func(**func_kwargs)
                    return response, current_tokens, fallback_triggered
                except Exception as e:
                    err_str = str(e).lower()
                    # --- Timeout / Rate-Limit Auto-Pause (z.B. Gemini Quota mit delay) ---
                    import re
                    match_seconds = re.search(r'retry_delay\s*\{\s*seconds:\s*(\d+)\s*\}', err_str)
                    if match_seconds:
                        wait_seconds = int(match_seconds.group(1)) + 5
                        # Schwellenwert: retry_delay > 300 s = Tages-Quota-Erschöpfung (z.B. Google
                        # Daily Quota, Reset Mitternacht Pacific). Kein Warten — Fast-Fail wie Budget.
                        if wait_seconds > 300:
                            logger.error(
                                "💸 Tages-Quota erschöpft (retry_delay=%ds > 300s Schwellenwert). "
                                "Fast-Fail — kein %d-Stunden-Wait.",
                                wait_seconds, wait_seconds // 3600,
                            )
                            raise RuntimeError(f"exceeded your current quota (retry_delay={wait_seconds}s)")
                        logger.warning(f"⏳ Quota/Rate Limit erreicht! Warte {wait_seconds} Sekunden... (Versuch {rate_limit_attempts + 1}/{max_rate_limit_retries})")
                        import time
                        time.sleep(wait_seconds)
                        rate_limit_attempts += 1
                        continue # Retry in the inner while-loop
                    # --- FAST FAIL für Budget/Quota-Fehler ---
                    # Status 402 ist immer Budget; sonst Word-Boundary-Matching
                    # (verhindert False-Positives auf Parameternamen wie
                    # ``thinking_budget`` bei HTTP-400-Parameterfehlern).
                    status_code = getattr(e, "status_code", None)
                    is_budget_error = (
                        status_code == 402
                        or bool(_BUDGET_ERROR_PATTERN.search(err_str))
                        or any(p in err_str for p in _BUDGET_ERROR_PHRASES)
                    )
                    if is_budget_error:
                        logger.error(
                            "💸 Budget/Quota erschöpft! API-Anfrage sofort abgebrochen "
                            "(kein Token-Fallback). Original-Fehler: %s",
                            str(e)[:300],
                        )
                        raise e
                    # --- Token-Fallback Check ---
                    is_token_error = any(kw.lower() in err_str for kw in error_keywords)
                    if is_token_error:
                        last_exception = e
                        break  # Break inner loop, trigger next limit in cascade
                    else:
                        # Ein nicht-Token bezogener Fehler (z.B. Timeout, Parsing)
                        raise e
        logger.error("❌ All token limits in the cascade were rejected by the provider API.")
        raise last_exception or Exception("Token fallback cascade failed unexpectedly.")

    # ── Reasoning Truncation Re-Ask: Eskalationsleiter ─────────────────

    # Config-Defaults, wenn benchmark_config.yaml keine reasoning_reask-Sektion hat
    _REASK_DEFAULT_CEILINGS: tuple[int, ...] = (24000, 32000)
    _REASK_DEFAULT_MAX_ESCALATIONS = 2
    # Last-Resort (letzte Leiter-Stufe): Deutlich geöffnetes Budget für die
    # vereinzelten erschöpften Fragen — dokumentiert im Report, bewusst KEINE
    # Card-Kalibrierung. 0 deaktiviert den Modus.
    _REASK_DEFAULT_LAST_RESORT = 48000

    def _maybe_reask_reasoning_truncation(
        self,
        content: str,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler: Callable[[str], None] | None,
        kwargs: dict[str, Any],
        query: Callable[..., str],
        budget_cap: int | None = None,
    ) -> str:
        """Reasoning-only Truncation erkennen und über die Eskalationsleiter klettern.

        Trigger (alle Bedingungen müssen erfüllt sein):
        1. Noch nicht eskaliert (``kwargs['_reasoning_reask']``-Guard — die
           Leiter klettert selbst in dieser Methode; Nested-Query-Aufrufe
           dürfen nicht erneut eskalieren).
        2. Kein PC-Modul (``kwargs['_module_key']`` — PC v3 hat seine eigene
           Leiter mit Thinking-Off, die dort autoritativ ist).
        3. ``finish_reason == "length"`` — der Request wurde am Token-Limit
           abgeschnitten.
        4. Sichtbarer Content leer — nur dann wird eskaliert. Teilweiser
           sichtbarer Output wird akzeptiert (Comparability: kein "best of 2
           Versuche" gegen Modelle mit nur einem Versuch).
        5. Reasoning-Signal vorhanden (``think_content`` oder
           ``reasoning_tokens > 0``) — die Truncation muss in der Thinking-Kette
           passiert sein, nicht an einem leeren/gestörten Request.
        6. Kein Exact-Modus (``kwargs['_budget_exact']`` — PC-Token-Probe,
           pc_calibrate): Diese Queries messen Truncation-Verhalten — eine
           Eskalation würde die Stufen-Semantik der Probe verfälschen.

        Mechanismus (absolute Stufen-Deckel, config-driven): Pro Stufe wird
        der nächste Ceiling ÜBER dem aktuellen Budget als Ziel-Budget verwendet
        (keine Multiplikatoren — kalibrierte Starts würden explodieren). Nach
        jeder Stufe wird der Trigger erneut geprüft (leer → nächste Stufe;
        Teil-Output → fertig). Kein Ceiling darüber oder Cap-Block → Leiter
        erschöpft. Stufe 1 kann aus der Card-Kalibrierung starten
        (``cot_budget_calibration``, SSoT: ``utils/model_token_budget.py``).

        Metadaten (SSoT ``last_response_metadata``): ``reasoning_reask`` (bool),
        ``reasoning_reask_initial_budget`` (Stufe-1-Budget),
        ``reasoning_reask_stage`` (höchster erreichter Versuch: 2/3),
        ``reasoning_reask_exhausted`` (finale Stufe trotzdem leer) und
        ``reasoning_reask_final_budget`` (Budget der letzten Stufe — Basis für
        den Card-Write). Basis für Judge-Kontext
        (``judge_evaluator._inject_token_usage_context``), Report und CSV.

        Args:
            content: Extrahierter sichtbarer Antwort-Text des Erstversuchs
            model: Modell-ID
            prompt: Original-Prompt (für den Re-Request)
            temperature: Original-Sampling-Temperatur
            stream_handler: Optionaler Stream-Handler (wird unverändert durchgereicht)
            kwargs: Original-Query-Kwargs (wird kopiert, nicht mutiert)
            query: Die Query-Methode des Connectors (für den Re-Request)
            budget_cap: Optionales hartes Budget-Limit des Connectors (z.B.
                ``model_cfg.max_tokens`` der Provider-Config). Ein Stufen-Ziel
                über dem Cap wird verweigert (Cap-Block-Guard, sichtbare
                Log-Zeile).

        Returns:
            Die (ggf. eskalierte) Antwort. Bei Triggern ohne erfolgreiche
            Eskalation wird die (leere) Antwort der höchsten Stufe
            zurückgegeben — der Erstversuch ist dann verfallen, was gewollt
            ist: Ein leerer Erstversuch ist kein messbarer Output.
        """
        if content and content.strip():
            return content
        if kwargs.get("_reasoning_reask"):
            return content
        if kwargs.get("_budget_exact"):
            return content
        if kwargs.get("_module_key") == "political_compass":
            return content
        meta = getattr(self, "last_response_metadata", {}) or {}
        if not self._reask_metadata_indicates_truncation(meta):
            return content

        ceilings, max_escalations = self._load_reask_ladder_config()
        ladder = self._run_reask_ladder(
            model=model,
            prompt=prompt,
            temperature=temperature,
            stream_handler=stream_handler,
            kwargs=kwargs,
            query=query,
            initial_budget=int(meta["token_limit_used"]),
            ceilings=ceilings,
            max_escalations=max_escalations,
            budget_cap=budget_cap,
        )
        self._finalize_reask_metadata(ladder)
        return ladder["content"]

    def _reask_metadata_indicates_truncation(self, meta: dict[str, Any]) -> bool:
        """Prüft die Response-Metadata auf eine Reasoning-only Truncation.

        Gemeinsame Trigger-Logik für den Erstversuch und die Re-Prüfung nach
        jeder Leiter-Stufe (Plan: Trigger-Prüfung nach JEDER Stufe erneut).
        """
        if meta.get("finish_reason") != "length":
            return False
        used = meta.get("token_limit_used")
        if not isinstance(used, int) or used <= 0:
            return False
        return bool(meta.get("think_content")) or (
            (meta.get("reasoning_tokens") or 0) > 0
        )

    def _load_reask_ladder_config(self) -> tuple[list[int], int]:
        """Liest ceilings/max_escalations aus benchmark_config.yaml (config-driven).

        Defaults ohne Sektion; ``max_escalations`` wird hart auf
        ``len(ceilings)`` gedeckelt (Konsistenz-Regel — mehr Eskalationen als
        Deckel wären tote Schleifen-Iterationen).
        """
        section = (getattr(self, "config", None) or {}).get("reasoning_reask") or {}
        raw_ceilings = section.get("ceilings")
        ceilings = sorted({
            int(c) for c in (raw_ceilings or self._REASK_DEFAULT_CEILINGS) if int(c) > 0
        }) or list(self._REASK_DEFAULT_CEILINGS)
        max_escalations = section.get(
            "max_escalations", self._REASK_DEFAULT_MAX_ESCALATIONS
        )
        if not isinstance(max_escalations, int) or max_escalations < 1:
            max_escalations = self._REASK_DEFAULT_MAX_ESCALATIONS
        if max_escalations > len(ceilings):
            logger.warning(
                "reasoning_reask.max_escalations (%d) > len(ceilings) (%d) — "
                "hart auf %d gedeckelt.",
                max_escalations, len(ceilings), len(ceilings),
            )
            max_escalations = len(ceilings)
        return ceilings, max_escalations

    @staticmethod
    def _next_reask_ceiling(current_budget: int, ceilings: list[int]) -> int | None:
        """Nächster absoluter Stufen-Deckel ÜBER dem aktuellen Budget (None = erschöpft)."""
        for ceiling in ceilings:
            if ceiling > current_budget:
                return ceiling
        return None

    # pylint: disable=too-many-arguments, too-many-positional-arguments, too-many-locals
    def _run_reask_ladder(
        self,
        *,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler: Callable[[str], None] | None,
        kwargs: dict[str, Any],
        query: Callable[..., str],
        initial_budget: int,
        ceilings: list[int],
        max_escalations: int,
        budget_cap: int | None,
    ) -> dict[str, Any]:
        """Klettert die Deckel-Leiter hoch (Stufen-Loop statt Rekursion).

        Returns:
            Dict mit ``content`` (letzte Antwort), ``stage`` (höchster
            Versuch: 1 = Erstversuch, 2/3 = Eskalationsstufen),
            ``initial_budget``, ``final_budget`` (Budget der letzten
            Eskalationsstufe oder None) und ``exhausted`` (True wenn mind.
            eine Eskalation lief und der finale Output trotzdem leer blieb).
        """
        reask_kwargs = dict(kwargs)
        # Nested-Query-Aufrufe dürfen nicht selbst eskalieren — die Leiter
        # hier draußen kontrolliert alle Stufen zentral.
        reask_kwargs["_reasoning_reask"] = True

        content = ""
        stage = 1
        final_budget: int | None = None
        current_budget = initial_budget
        for _ in range(max_escalations):
            target = self._next_reask_ceiling(current_budget, ceilings)
            if target is None:
                logger.debug(
                    "Eskalationsleiter: kein Ceiling über %d — Leiter endet.",
                    current_budget,
                )
                break
            if budget_cap is not None and target > budget_cap:
                logger.warning(
                    "   ⛔ Eskalationsdeckel %d über Budget-Cap %s blockiert — "
                    "Leiter stoppt (Cap-Block-Guard).",
                    target, budget_cap,
                )
                break
            attempt = stage + 1
            logger.warning(
                "   🔁 Tokenbudget erhöht (Stufe %d/%d, %s): %d Tokens verbrannt, "
                "0 sichtbarer Output → Re-Ask mit %d Tokens.",
                attempt, max_escalations + 1, model, current_budget, target,
            )
            reask_kwargs["max_tokens"] = target
            content = query(
                model=model,
                prompt=prompt,
                temperature=temperature,
                stream_handler=stream_handler,
                **reask_kwargs,
            )
            stage = attempt
            final_budget = target
            if content and content.strip():
                logger.info(
                    "   ✅ Re-Ask erfolgreich (Stufe %d): %d Zeichen sichtbarer "
                    "Output (Budget %d).",
                    attempt, len(content), target,
                )
                break
            logger.warning(
                "   ⛔ Stufe %d erneut leer (%d Tokens).", attempt, target,
            )
            # Trigger nach jeder Stufe erneut prüfen: Die neue Metadata muss
            # weiterhin eine Reasoning-only Truncation zeigen, sonst (z.B.
            # finish_reason=stop bei leerem Output = stiller Refusal) klettert
            # die Leiter nicht weiter.
            re_meta = getattr(self, "last_response_metadata", {}) or {}
            if not self._reask_metadata_indicates_truncation(re_meta):
                break
            current_budget = target

        exhausted = stage >= 2 and not (content and content.strip())

        # Last-Resort (letzte Stufe der Leiter, Session 110): Nach Erschöpfung,
        # Cap-Block oder fehlendem Ceiling — immer wenn die Leiter ohne
        # sichtbaren Output endete UND der Truncation-Trigger weiterhin aktiv
        # ist (bei stillem Refusal/finish_reason=stop hilft mehr Budget nicht —
        # konsistent mit der Leiter-Trigger-Logik) — EIN finaler Versuch mit
        # deutlich geöffnetem Budget. Bewusst KEINE Card-Kalibrierung (nur
        # Report-Hervorhebung): Der Last-Resort ist ein bewertender
        # Ausnahmelauf, keine Kalibrierungs-Evidenz — sonst würde Stufe 1
        # künftiger Läufe auf das geöffnete Budget springen und das Budget für
        # ALLE Fragen öffnen.
        last_resort = False
        last_resort_budget: int | None = None
        re_meta = getattr(self, "last_response_metadata", {}) or {}
        if not (content and content.strip()) and self._reask_metadata_indicates_truncation(re_meta):
            lrb = self._load_reask_last_resort_budget()
            if lrb:
                content, stage, final_budget, last_resort, last_resort_budget, exhausted = (
                    self._run_last_resort_attempt(
                        model=model,
                        prompt=prompt,
                        temperature=temperature,
                        stream_handler=stream_handler,
                        reask_kwargs=reask_kwargs,
                        query=query,
                        stage=stage,
                        final_budget=final_budget,
                        exhausted=exhausted,
                        last_resort_budget=lrb,
                    )
                )

        if exhausted:
            logger.warning(
                "   ⛔ Leiter erschöpft: Stufe %d (%s Tokens) ohne sichtbaren "
                "Output — Messgrenze dokumentiert (reasoning_reask_exhausted).",
                stage, final_budget,
            )
        return {
            "content": content,
            "stage": stage,
            "initial_budget": initial_budget,
            "final_budget": final_budget,
            "exhausted": exhausted,
            "last_resort": last_resort,
            "last_resort_budget": last_resort_budget,
        }

    def _load_reask_last_resort_budget(self) -> int | None:
        """Last-Resort-Budget aus benchmark_config.yaml (letzte Leiter-Stufe).

        ``last_resort_budget: 48000`` (Default) öffnet nach erschöpfter Leiter
        das Budget DEUTLICH für genau diese eine Frage — dokumentiert im Report
        (Audit-Log, CSV, Judge-Kontext, Meta-Reviewer), bewusst OHNE Card-
        Kalibrierung. ``0``/``null`` deaktiviert den Modus.
        """
        section = (getattr(self, "config", None) or {}).get("reasoning_reask") or {}
        raw = section.get("last_resort_budget", self._REASK_DEFAULT_LAST_RESORT)
        try:
            budget = int(raw)
        except (TypeError, ValueError):
            return int(self._REASK_DEFAULT_LAST_RESORT)
        return budget if budget > 0 else None

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def _run_last_resort_attempt(
        self,
        *,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler: Callable[[str], None] | None,
        reask_kwargs: dict[str, Any],
        query: Callable[..., str],
        stage: int,
        final_budget: int | None,
        exhausted: bool,
        last_resort_budget: int,
    ) -> tuple[str, int, int | None, bool, int | None, bool]:
        """Führt den Last-Resort-Request aus (letzte Leiter-Stufe, Cap-Bypass).

        Der Request läuft mit ``_cap_bypass=True`` — der wirksame Budget-Cap
        (Provider-Default/Override/Card-Cap) wird für GENAU diesen Request
        übersprungen, damit das geöffnete Budget tatsächlich ankommt. Der
        Bypass ist bewusst und wird geloggt; die Stufen-Nummerierung zählt
        weiter (Last-Resort = Versuch nach der höchsten regulären Stufe).
        """
        attempt = stage + 1
        logger.warning(
            "   🚨 Last-Resort (letzte Stufe, %s): Leiter endete ohne sichtbaren "
            "Output (Stufe %d, %s Tokens) — Budget für DIESE Frage geöffnet "
            "(dokumentiert im Report; KEINE Card-Kalibrierung).",
            f"{last_resort_budget} Tokens", stage, final_budget,
        )
        reask_kwargs = dict(reask_kwargs)
        reask_kwargs["max_tokens"] = last_resort_budget
        reask_kwargs["_cap_bypass"] = True
        content = query(
            model=model,
            prompt=prompt,
            temperature=temperature,
            stream_handler=stream_handler,
            **reask_kwargs,
        )
        stage = attempt
        final_budget = last_resort_budget
        if content and content.strip():
            logger.warning(
                "   ✅ Last-Resort erfolgreich (Stufe %d): %d Zeichen sichtbarer "
                "Output (Budget %d) — Antwort bewertbar, Token-Hunger wird im "
                "Report ausgewiesen (Einsatzkosten: Erstversuch + Leiter + "
                "Last-Resort).",
                attempt, len(content), last_resort_budget,
            )
            return content, stage, final_budget, True, last_resort_budget, False
        logger.warning(
            "   ⛔ Auch Last-Resort (Stufe %d, %d Tokens) ohne sichtbaren Output "
            "— Messgrenze endgültig dokumentiert.",
            attempt, last_resort_budget,
        )
        return content, stage, final_budget, True, last_resort_budget, True

    def _finalize_reask_metadata(self, ladder: dict[str, Any]) -> None:
        """Schreibt die Leiter-Metadata in ``last_response_metadata`` (SSoT).

        Erst nach der letzten Stufe — jede Nested-Query überschreibt die
        Metadata, die Annotation muss auf dem finalen Stand passieren. Ohne
        Eskalationsversuch (stage < 2, kein Last-Resort) bleibt alles beim
        Alt-Verhalten.
        """
        if ladder["stage"] < 2 and not ladder.get("last_resort"):
            return
        meta = getattr(self, "last_response_metadata", {}) or {}
        meta["reasoning_reask"] = True
        meta["reasoning_reask_initial_budget"] = ladder["initial_budget"]
        meta["reasoning_reask_stage"] = ladder["stage"]
        if ladder["final_budget"] is not None:
            meta["reasoning_reask_final_budget"] = ladder["final_budget"]
        if ladder["exhausted"]:
            meta["reasoning_reask_exhausted"] = True
        if ladder.get("last_resort"):
            meta["reasoning_last_resort"] = True
            if ladder.get("last_resort_budget") is not None:
                meta["reasoning_last_resort_budget"] = int(ladder["last_resort_budget"])
