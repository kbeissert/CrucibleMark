"""
Provider-spezifische LLM Clients
Getrennte Implementierungen für Ollama, Anthropic, Mistral
"""
import logging
from typing import Any
from collections.abc import Callable
logger = logging.getLogger(__name__)


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
        from utils.model_utils import resolve_token_budget, internal_id_to_config_form

        provider_cfg = self._get_provider_cfg()
        token_param_name = provider_cfg.get("token_param_name", self.DEFAULT_TOKEN_PARAM)

        # 1. Reasoning-/Thinking-Budget auflösen
        req_tokens, _ = resolve_token_budget(
            model, kwargs.get("max_tokens"), self.config, kwargs.get("_module_key")
        )

        # 2. Zweistufige Token-Kaskade:
        #    Provider-Default → Per-Model Override (überschreibt Default)
        #    Config-Form normalisieren (Underscore→Dot in Version-Segmenten)
        provider_cap = provider_cfg.get("max_tokens")
        model_limits = provider_cfg.get("model_max_tokens", {})
        config_form = internal_id_to_config_form(model)
        model_cap = model_limits.get(model)
        if model_cap is None:
            model_cap = model_limits.get(config_form)
        effective_cap = model_cap if model_cap is not None else provider_cap

        if effective_cap is not None:
            req_tokens = min(req_tokens, effective_cap)

        return token_param_name, req_tokens

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
                    budget_keywords = [
                        "quota", "budget", "billing", "credit", "insufficient_funds",
                        "payment", "402 payment required", "exceeded your current quota"
                    ]
                    if any(kw in err_str for kw in budget_keywords):
                        logger.error("💸 Budget/Quota erschöpft! API-Anfrage sofort abgebrochen (kein Token-Fallback).")
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
