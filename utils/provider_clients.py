"""
Provider-spezifische LLM Clients
Getrennte Implementierungen für Ollama, Anthropic, Mistral
"""

import os
import time
import logging
from typing import Any, List, Optional, Callable, Dict

from utils.ollama_config import CODING_BENCHMARK_OPTIONS, CREATIVE_BENCHMARK_OPTIONS
from utils.constants import MAX_TOKENS_ANTHROPIC, DEFAULT_MISTRAL_MODEL
from utils.env_utils import get_required_env
from utils.model_utils import is_reasoning_model

# Optional Provider Imports
try:
    import ollama
except ImportError:
    ollama = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    from mistralai import Mistral
except ImportError:
    Mistral = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

import warnings

try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import google.generativeai as genai
except ImportError:
    genai = None

# Configure logging
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


class OllamaClient(BaseProviderClient):
    """Ollama Provider Client"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._client = None

    @property
    def client(self):
        """Lazy-loaded Ollama Client"""
        if self._client is None:
            if ollama is None:
                raise ImportError("Library 'ollama' not installed. Please install it.")
            self._client = ollama
        return self._client

    def _get_options(self, model: str, temperature: float) -> Dict[str, Any]:
        """Konfiguriert Optionen basierend auf Temperatur und Modell-Typ."""
        # Select options based on temperature
        if temperature >= 0.3:
            options = CREATIVE_BENCHMARK_OPTIONS.copy()
        else:
            options = CODING_BENCHMARK_OPTIONS.copy()

        # Ensure the requested temperature is actually used
        options["temperature"] = temperature

        # SPECIAL HANDLING for Reasoning Models (e.g. DeepSeek-R1)
        if is_reasoning_model(model):
            # Reduced to 8192 to prevent excessive unified memory swapping
            # (which causes system-wide freezes on Mac when 32768 context explodes VRAM)
            options["num_predict"] = 8192
            if "num_ctx" not in options:
                options["num_ctx"] = 8192
            logger.debug(
                "Boosting token limit for reasoning model '%s' to 8192 to prevent memory freezes",
                model,
            )

        return options

    def _handle_streaming(
        self,
        model: str,
        prompt: str,
        options: Dict[str, Any],
        stream_handler: Callable[[str], None],
        system_prompt: Optional[str] = None,
    ) -> str:
        """Behandelt Streaming-Response von Ollama."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        full_content = ""
        full_thinking = ""

        try:
            response = self.client.chat(
                model=model,
                messages=messages,
                options=options,
                stream=True,
            )

            for chunk in response:
                if chunk.get("done"):
                    # Extract metrics from final chunk
                    total_ns = chunk.get("total_duration") or 0
                    load_ns = chunk.get("load_duration") or 0
                    eval_ns = chunk.get("eval_duration") or 0
                    prompt_eval_ns = chunk.get("prompt_eval_duration") or 0

                    metrics = {
                        "total_duration": total_ns / 1e9,
                        "load_duration": load_ns / 1e9,
                        "eval_duration": eval_ns / 1e9,
                        "prompt_eval_duration": prompt_eval_ns / 1e9,
                        "finish_reason": chunk.get("done_reason"),
                    }
                    metrics["pure_execution_time"] = (
                        metrics["total_duration"] - metrics["load_duration"]
                    )
                    self.last_response_metadata = metrics
                    continue

                msg = chunk.get("message", {})
                # Handle diff response formats (dict vs object)
                if isinstance(msg, dict):
                    val_content = msg.get("content", "")
                else:
                    val_content = getattr(msg, "content", "")

                # Try to extract thinking
                val_thinking = ""
                if hasattr(msg, "thinking"):
                    val_thinking = msg.thinking
                elif isinstance(msg, dict):
                    val_thinking = msg.get("thinking", "")

                if val_thinking:
                    stream_handler(val_thinking)
                    full_thinking += val_thinking

                if val_content:
                    stream_handler(val_content)
                    full_content += val_content

        except Exception as e:
            # Emergency Recovery for Ollama Parser Errors (e.g. XML in JSON)
            # "error parsing tool call: raw='<thought>...'"
            err_str = str(e)
            if "error parsing tool call" in err_str and "raw='" in err_str:
                logger.warning(f"Ollama Parser Error Recovery active for: {model}")
                try:
                    # Extract content between raw=' and ', err=
                    import re

                    match = re.search(r"raw='(.*?)', err=", err_str, re.DOTALL)
                    if match:
                        recovered_content = match.group(1)
                        # Fix escaped quotes if strictly necessary, but usually raw is just string
                        full_content += "\n" + recovered_content
                        # Stream it out for UI
                        stream_handler(recovered_content)
                        logger.info(
                            "Successfully recovered content from Ollama parser error."
                        )
                        return full_content
                except Exception as ex:
                    logger.error(f"Failed to recover from parser error: {ex}")

            # If not recoverable, re-raise
            raise e

        if not full_content and full_thinking:
            logger.debug(
                "Ollama streaming returned thinking but no content. Using thinking as fallback."
            )
            return full_thinking

        return full_content

    def query(
        self,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> str:
        """Query Ollama API"""
        # Validate inputs early to prevent opaque 400 errors from backend
        if not model:
            raise ValueError("OllamaClient.query called with empty 'model' parameter.")
        if " " in model:
            logger.warning(
                "Model name '%s' contains spaces. This may cause 'model is required' errors in Ollama.",
                model,
            )

        try:
            options = self._get_options(model, temperature)

            # Handle max_tokens override (Ollama uses num_predict)
            if "max_tokens" in kwargs:
                options["num_predict"] = kwargs["max_tokens"]

            # 🟢 Allow Overrides from kwargs (Benchmark Module Config)
            # This allows modules to define specific params like repeat_penalty in their config.yaml
            allowed_overrides = [
                "repeat_penalty",
                "top_k",
                "top_p",
                "seed",
                "num_predict",
                "num_ctx",
            ]
            for key in allowed_overrides:
                if key in kwargs:
                    options[key] = kwargs[key]

            # Prepare messages list
            messages = []

            # Check for system prompt in kwargs
            system_prompt = kwargs.get("system")
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            # Force Streaming Mode to avoid "error parsing tool call" with reasoning models
            # that output XML <thought> tags which confuse Ollama's blocking parser.
            try:
                handler = stream_handler if stream_handler else lambda x: None
                return self._handle_streaming(
                    model, prompt, options, handler, system_prompt=system_prompt
                )
            except Exception as e:
                # Catch specific Ollama 400 errors to inform user
                err_str = str(e)
                if "model is required" in err_str:
                    raise ValueError(
                        f"Ollama rejected the request for model='{model}'. "
                        "Check if the model name is correct and has no illegal characters (spaces, etc.)."
                    ) from e
                raise e
        except Exception as e:
            logger.error("Ollama query failed: %s", e)
            raise

    def get_available_models(self) -> List[str]:
        """Listet verfügbare Ollama-Modelle"""
        try:
            response = self.client.list()
            # Handle both object and dict response formats
            models = (
                response.models
                if hasattr(response, "models")
                else response.get("models", [])
            )
            return [
                model.model if hasattr(model, "model") else model.get("name", "unknown")
                for model in models
            ]
        except (ConnectionError, OSError, RuntimeError) as e:
            logger.error("Error listing Ollama models: %s", e)
            return []


class AnthropicClient(BaseProviderClient):
    """Anthropic Claude Provider Client"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._client = None
        self.last_request_time = 0
        self.min_request_interval = self.config.get("anthropic", {}).get(
            "min_request_interval", 0.2
        )  # Default: 0.2s between requests

    @property
    def client(self):
        """Lazy-loaded Anthropic Client"""
        if self._client is None:
            if anthropic is None:
                raise ImportError("Library 'anthropic' not installed.")

            api_key = get_required_env(
                "ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY environment variable not set"
            )
            # timeout raised to 600s because huge 8000+ token generations can easily take 3-5 minutes
            self._client = anthropic.Anthropic(api_key=api_key, timeout=600.0)
        return self._client

    def is_accessible(self) -> bool:
        """Prüft Zugang zu Anthropic API durch Test-Request."""
        try:
            # Versuche minimale Generierung (Cheap & Fast) mit max_retries=0
            check_client = anthropic.Anthropic(
                api_key=self.client.api_key, max_retries=0
            )
            check_client.messages.create(
                model="claude-3-haiku-20240307",  # Günstigstes Modell für Test
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return True
        except Exception as e:
            logger.debug("Anthropic Access Check Failed: %s", e)
            return False

    def _resolve_model(self, model: str) -> str:
        """Löst Modell-Name auf (Config-Fallback)"""
        # Nur wenn kein Modell oder der generische Provider-Name übergeben wurde, Fallback nutzen.
        if not model or model == "claude":
            return self.config.get("anthropic", {}).get(
                "model", "claude-3-5-sonnet-20241022"
            )
        return model

    def query(
        self,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> str:
        """Query Anthropic API"""
        # Rate Limit Protection
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            logger.debug(f"⏱️ Rate limit protection: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

        try:
            model = self._resolve_model(model)

            # Default to config, but override with kwargs if present
            max_tokens = kwargs.get("max_tokens")
            if not max_tokens:
                max_tokens = self.config.get("anthropic", {}).get(
                    "max_tokens", MAX_TOKENS_ANTHROPIC
                )

            # Note: Streaming not implemented yet for Anthropic in this wrapper
            func_kwargs = {
                "model": model,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }

            response, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=self.client.messages.create,
                token_param_name="max_tokens",
                initial_max_tokens=max_tokens,
                error_keywords=["max_tokens"],
                func_kwargs=func_kwargs
            )

            # Capture Metadata
            self.last_response_metadata = {
                "model": response.model,
                "id": response.id,
                "usage": response.usage,
                "finish_reason": getattr(response, "stop_reason", None),
                "token_limit_fallback": fallback_triggered,
                "token_limit_used": used_max_tokens,
            }

            if (
                stream_handler
                and response.content
                and hasattr(response.content[0], "text")
            ):
                stream_handler(response.content[0].text)

            return response.content[0].text
        except Exception:
            # Let RetryHandler handle logging
            raise

    def get_available_models(self) -> List[str]:
        """Listet verfügbare Claude-Modelle"""
        return [
            "claude-sonnet-4-5-20250929",
            "claude-opus-4-5-20251101",
            "claude-3-haiku-20240307",
        ]


class MistralClient(BaseProviderClient):
    """Mistral AI Provider Client"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._client = None

    @property
    def client(self):
        """Lazy-loaded Mistral Client"""
        if self._client is None:
            if Mistral is None:
                raise ImportError("Library 'mistralai' not installed.")

            # Support both MISTRAL_API_KEY and CODESTRAL_API_KEY
            # Using basic retrieval since OR logic prevents simple get_required_env usage
            api_key = os.environ.get("MISTRAL_API_KEY") or os.environ.get(
                "CODESTRAL_API_KEY"
            )
            if not api_key:
                raise ValueError(
                    "MISTRAL_API_KEY or CODESTRAL_API_KEY environment variable not set"
                )
            # Set explicit timeout (120s) to avoid indefinite hangs on API congestion
            self._client = Mistral(api_key=api_key, timeout_ms=120000)
        return self._client

    def is_accessible(self) -> bool:
        """Prüft Zugang zu Mistral API."""
        try:
            # Mistral client usually supports listing models as a cheap check
            self.client.models.list()
            return True
        except Exception as e:
            logger.debug("Mistral Access Check Failed: %s", e)
            return False

    def _resolve_model(self, model: str) -> str:
        """Löst Modell-Name auf (Config-Fallback)"""
        # Nur wenn kein Modell oder der generische Provider-Name übergeben wurde, Fallback nutzen.
        if not model or model == "mistral":
            return self.config.get("mistral", {}).get("model", DEFAULT_MISTRAL_MODEL)
        return model

    def query(
        self,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> str:
        """Query Mistral API"""
        try:
            model = self._resolve_model(model)

            # Mistral supports max_tokens
            max_tokens = kwargs.get("max_tokens")
            if not max_tokens:
                max_tokens = self.config.get("defaults", {}).get("generation", {}).get("num_predict", 8192)

            # Note: Streaming not implemented yet for Mistral in this wrapper
            func_kwargs = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "random_seed": 42,
            }

            response, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=self.client.chat.complete,
                token_param_name="max_tokens",
                initial_max_tokens=max_tokens,
                error_keywords=["maximum context length", "max_tokens", "too large"],
                func_kwargs=func_kwargs
            )

            # Capture Metadata
            self.last_response_metadata = {
                "model": response.model,
                "id": response.id,
                "usage": response.usage,
                "token_limit_fallback": fallback_triggered,
                "token_limit_used": used_max_tokens,
                "finish_reason": getattr(response.choices[0], "finish_reason", None) if response.choices else None,
            }

            content = response.choices[0].message.content
            if stream_handler and content:
                stream_handler(content)

            return content
        except Exception:
            # Let RetryHandler handle logging
            raise

    def get_available_models(self) -> List[str]:
        """Listet verfügbare Mistral-Modelle"""
        return [
            "mistral-large-latest",
            "mistral-medium-latest",
            "mistral-small-latest",
            "open-mistral-7b",
        ]


class OpenAIClient(BaseProviderClient):
    """OpenAI Provider Client"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._client = None

    @property
    def client(self):
        """Lazy-loaded OpenAI Client"""
        if self._client is None:
            if OpenAI is None:
                raise ImportError("Library 'openai' not installed.")

            api_key = get_required_env(
                "OPENAI_API_KEY", "OPENAI_API_KEY environment variable not set"
            )

            # Configure explicit Timeout object for better handling of TTFT vs Connection
            # read=180.0s allows up to 3 mins wait for TTFT or between chunks
            # Note: httpx.Timeout does not accept 'total' argument in this version's constructor apparently,
            # or the way OpenAI client passes it down is specific.
            # Using connect/read/write/pool is standard for httpx used by OpenAI.

            import httpx

            timeout_config = httpx.Timeout(
                connect=10.0, read=180.0, write=180.0, pool=180.0
            )

            self._client = OpenAI(api_key=api_key, timeout=timeout_config)
        return self._client

    def is_accessible(self) -> bool:
        """Prüft Zugang zu OpenAI API (inkl. Quota Check)."""
        try:
            # list() reicht nicht für Quota Check (gibt oft success bei leerem Quota).
            # Daher führen wir eine minimale Generierung durch, um Billing-Status zu prüfen.
            # Eigener Client mit max_retries=0 um "Retrying..." Logs im Terminal zu vermeiden
            check_client = OpenAI(api_key=self.client.api_key, max_retries=0)
            check_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
            )
            return True
        except Exception as e:
            # Fängt InsufficientQuotaError, AuthenticationError, etc.
            logger.debug("OpenAI Access Check Failed: %s", e)
            return False

    def query(
        self,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> str:
        """Query OpenAI API"""
        try:
            params = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
            }

            # Reasoning models (o1, o3) and some newer minis often don't support temperature
            # or have strict fixed values.
            is_reasoning = (
                model.startswith("o1") or model.startswith("o3") or "gpt-5" in model
            )
            if not is_reasoning:
                params["temperature"] = temperature

            token_param_name = "max_completion_tokens"  # OpenAI now universally prefers max_completion_tokens for newer models
            req_tokens = kwargs.get("max_tokens")
            if not req_tokens:
                req_tokens = self.config.get("defaults", {}).get("generation", {}).get("num_predict", 8192)

            if is_reasoning and req_tokens < 10000:
                initial_tokens_to_try = 25000
            else:
                initial_tokens_to_try = req_tokens

            if stream_handler:
                params["stream"] = True
                # Request usage info in stream (OpenAI feature)
                params["stream_options"] = {"include_usage": True}

            response_or_stream, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=self.client.chat.completions.create,
                token_param_name=token_param_name,
                initial_max_tokens=initial_tokens_to_try,
                error_keywords=["maximum context length", "max_tokens", "max_completion_tokens", "too large"],
                func_kwargs=params
            )

            if stream_handler:
                response_stream = response_or_stream
                full_content = ""
                self.last_response_metadata = {
                    "token_limit_fallback": fallback_triggered,
                    "token_limit_used": used_max_tokens,
                }

                for chunk in response_stream:
                    # Capture basic metadata from chunks
                    if not self.last_response_metadata.get("id") and chunk.id:
                        self.last_response_metadata["id"] = chunk.id
                    if not self.last_response_metadata.get("model") and chunk.model:
                        self.last_response_metadata["model"] = chunk.model
                    if getattr(chunk, "system_fingerprint", None):
                        self.last_response_metadata["system_fingerprint"] = (
                            chunk.system_fingerprint
                        )

                    # Capture Usage (usually in last chunk)
                    if hasattr(chunk, "usage") and chunk.usage:
                        self.last_response_metadata["usage"] = chunk.usage

                    if chunk.choices and hasattr(chunk.choices[0], "finish_reason") and chunk.choices[0].finish_reason:
                        self.last_response_metadata["finish_reason"] = chunk.choices[0].finish_reason

                    # Content
                    if chunk.choices:
                        delta = chunk.choices[0].delta.content
                        if delta:
                            stream_handler(delta)
                            full_content += delta

                return full_content

            # Blocking Call (Legacy / No Stream)
            response = response_or_stream

            # Capture Metadata
            self.last_response_metadata = {
                "model": response.model,
                "id": response.id,
                "system_fingerprint": getattr(response, "system_fingerprint", None),
                "usage": response.usage,
                "finish_reason": getattr(response.choices[0], "finish_reason", None) if response.choices else None,
                "token_limit_fallback": fallback_triggered,
                "token_limit_used": used_max_tokens,
            }

            content = response.choices[0].message.content or ""

            # Ensure we don't call stream_handler twice if falling back to blocking
            # The original code called it here, but since we have a dedicated stream branch,
            # this is only for the non-streaming case.
            # However, if the caller PROVIDED a stream_handler but somehow we ended up here
            # (which we shouldn't given the if above), we should call it.
            # But the 'if stream_handler' block handles that.

            return content
        except Exception as e:
            logger.error("OpenAI query failed: %s", e)
            raise

    def get_available_models(self) -> List[str]:
        """List available OpenAI models"""
        return ["gpt-5.2-pro", "gpt-5-mini", "o3-mini", "gpt-4o"]


class GoogleClient(BaseProviderClient):
    """Google Gemini Provider Client"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = get_required_env("GOOGLE_API_KEY")
        if genai:
            genai.configure(api_key=self.api_key)
        else:
            logger.warning(
                "Google Generative AI library (google-generativeai) not installed."
            )

    def is_accessible(self) -> bool:
        """Prüft, ob der API Key gültig ist."""
        if not genai:
            print("❌ Google Generative AI (google-generativeai) nicht installiert.")
            return False

        try:
            # Minimaler Check: ListModels
            # List models, limit to 1 to check auth
            # Note: genai.list_models() returns a generator
            next(genai.list_models(), None)
            return True
        except Exception as e:
            logger.debug(f"Google Access Check Failed: {e}")
            return False

    def query(
        self,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> str:
        """Query Google Gemini API"""
        if not genai:
            raise ImportError("Google Generative AI library not installed.")

        try:
            # Configure Generation Config
            generation_config = genai.types.GenerationConfig(temperature=temperature)

            if "max_tokens" in kwargs:
                # Gemini uses max_output_tokens
                generation_config.max_output_tokens = kwargs["max_tokens"]

            if "top_p" in kwargs:
                generation_config.top_p = kwargs["top_p"]

            if "top_k" in kwargs:
                generation_config.top_k = kwargs["top_k"]

            # Initialize Model
            gemini_model = genai.GenerativeModel(model_name=model)

            initial_max_tokens = kwargs.get("max_tokens", self.config.get("defaults", {}).get("generation", {}).get("num_predict", 8192))

            def _google_generator(max_tokens, **gen_kwargs):
                generation_config.max_output_tokens = max_tokens
                return gemini_model.generate_content(prompt, generation_config=generation_config, **gen_kwargs)

            func_kwargs = {}
            if stream_handler:
                func_kwargs["stream"] = True

            response_or_stream, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=_google_generator,
                token_param_name="max_tokens",
                initial_max_tokens=initial_max_tokens,
                error_keywords=["400 bad request", "invalid argument", "maximum context length", "too large"],
                func_kwargs=func_kwargs
            )

            # Streaming Support
            if stream_handler:
                response = response_or_stream

                full_text = ""
                self.last_response_metadata = {
                    "token_limit_fallback": fallback_triggered,
                    "token_limit_used": used_max_tokens,
                }

                for chunk in response:
                    # chunk.text can throw if blocked by safety settings
                    text_chunk = ""
                    try:
                        text_chunk = chunk.text
                    except ValueError:
                        # Handle safety filter blocking
                        logger.warning("Gemini chunk blocked (safety filters).")

                    if text_chunk:
                        stream_handler(text_chunk)
                        full_text += text_chunk

                    # Metadata Extraction (if available in chunk)
                    if hasattr(chunk, "usage_metadata"):
                        # Gemini usage is cumulative in last chunk usually
                        # Convert proto to dict if needed, or use object
                        # We just store it for now
                        pass

                    if hasattr(chunk, "candidates") and chunk.candidates:
                        fr = chunk.candidates[0].finish_reason
                        if fr:
                            # Usually an enum, convert to string
                            self.last_response_metadata["finish_reason"] = getattr(fr, "name", str(fr))

                return full_text

            # Blocking Call
            response = response_or_stream

            self.last_response_metadata = {
                "token_limit_fallback": fallback_triggered,
                "token_limit_used": used_max_tokens,
            }
            if hasattr(response, "candidates") and response.candidates:
                fr = response.candidates[0].finish_reason
                if fr:
                    self.last_response_metadata["finish_reason"] = getattr(fr, "name", str(fr))

            try:
                return response.text
            except ValueError:
                # Often happens if content was blocked
                logger.warning(f"Gemini check blocked: {response.prompt_feedback}")
                return "Error: Content blocked by safety filters."

        except Exception as e:
            logger.error(f"Google Gemini query failed: {e}")
            raise

    def get_available_models(self) -> List[str]:
        """List available Gemini models"""
        if not genai:
            return []
        try:
            models = genai.list_models()
            # Filter for generateContent support
            return [
                m.name.replace("models/", "")
                for m in models
                if "generateContent" in m.supported_generation_methods
            ]
        except Exception:
            return []


class XAIClient(BaseProviderClient):
    """XAI Provider Client"""

    def __init__(self, config: dict):
        super().__init__(config)
        self._client = None

    @property
    def client(self):
        """Lazy-loaded XAI Client using OpenAI wrapper"""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("Library 'openai' not installed.")

            import httpx
            from utils.env_utils import get_required_env

            api_key = get_required_env(
                "XAI_API_KEY", "XAI_API_KEY environment variable not set"
            )

            timeout_config = httpx.Timeout(
                connect=10.0, read=180.0, write=180.0, pool=180.0
            )

            self._client = OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1",
                timeout=timeout_config
            )
        return self._client

    def is_accessible(self) -> bool:
        """Prüft Zugang zu XAI API."""
        try:
            from openai import OpenAI
            check_client = OpenAI(api_key=self.client.api_key, base_url="https://api.x.ai/v1", max_retries=0)
            check_client.chat.completions.create(
                model="grok-beta",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
            )
            return True
        except Exception as e:
            from utils.logging_config import setup_logging
            logger = setup_logging()
            logger.debug("XAI Access Check Failed: %s", e)
            return False

    def query(
        self,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler = None,
        **kwargs,
    ) -> str:
        """Query XAI API"""
        try:
            from utils.logging_config import setup_logging
            logger = setup_logging()
            params = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            }

            req_tokens = kwargs.get("max_tokens")
            if not req_tokens:
                req_tokens = self.config.get("defaults", {}).get("generation", {}).get("num_predict", 8192)

            params["max_completion_tokens"] = req_tokens

            if stream_handler:
                params["stream"] = True

            response, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=self.client.chat.completions.create,
                token_param_name="max_completion_tokens",
                initial_max_tokens=req_tokens,
                error_keywords=["maximum context length", "max_tokens", "max_completion_tokens"],
                func_kwargs=params
            )

            if stream_handler:
                full_content = ""
                self.last_response_metadata = {
                    "token_limit_fallback": fallback_triggered,
                    "token_limit_used": used_max_tokens,
                }

                for chunk in response:
                    if not self.last_response_metadata.get("id") and chunk.id:
                        self.last_response_metadata["id"] = chunk.id
                    if not self.last_response_metadata.get("model") and chunk.model:
                        self.last_response_metadata["model"] = chunk.model

                    if chunk.choices and hasattr(chunk.choices[0], "finish_reason") and chunk.choices[0].finish_reason:
                        self.last_response_metadata["finish_reason"] = chunk.choices[0].finish_reason

                    if chunk.choices:
                        delta = chunk.choices[0].delta.content
                        if delta:
                            stream_handler(delta)
                            full_content += delta

                return full_content
            else:
                raw_text = response.choices[0].message.content

                self.last_response_metadata = {
                    "token_limit_fallback": fallback_triggered,
                    "token_limit_used": used_max_tokens,
                    "id": getattr(response, "id", None),
                    "model": getattr(response, "model", None),
                    "finish_reason": response.choices[0].finish_reason if response.choices else None,
                }

                if hasattr(response, "usage") and response.usage:
                    self.last_response_metadata["usage"] = response.usage

                return raw_text if raw_text else ""

        except Exception as e:
            from utils.logging_config import setup_logging
            logger = setup_logging()
            logger.error("XAI API Error: %s", e)
            raise e

    def get_available_models(self) -> list:
        try:
            models = self.client.models.list()
            return [m.id for m in models.data]
        except Exception:
            return ["grok-2-latest", "grok-3-latest"]
