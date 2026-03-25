"""
Provider-spezifische LLM Clients
Getrennte Implementierungen für Ollama, Anthropic, Mistral
"""
import time
import logging
from typing import Any, List, Optional, Callable
logger = logging.getLogger(__name__)
class BaseProviderClient:
    """Basis-Klasse für Provider-spezifische Clients"""
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
        stream_handler: Optional[Callable[[str], None]] = None,
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
    def get_available_models(self) -> List[str]:
        """Listet verfügbare Modelle"""
        raise NotImplementedError
    def is_accessible(self) -> bool:
        """
        Prüft, ob der Provider zugänglich ist (API Key, Budget/Quota).
        Standardmäßig True, sollte von Subklassen überschrieben werden.
        """
        return True
    def _execute_with_token_fallback(
        self,
        func: Callable,
        token_param_name: str,
        initial_max_tokens: int,
        error_keywords: List[str],
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
