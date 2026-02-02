"""
Provider-spezifische LLM Clients
Getrennte Implementierungen für Ollama, Anthropic, Mistral
"""

import os
import logging
from typing import Any, List, Optional, Callable, Dict

from utils.ollama_config import CODING_BENCHMARK_OPTIONS, CREATIVE_BENCHMARK_OPTIONS
from utils.constants import MAX_TOKENS_ANTHROPIC, DEFAULT_MISTRAL_MODEL
from utils.env_utils import get_required_env
from utils.model_utils import is_reasoning_model
from utils.fingerprinting import ModelFingerprinter, get_official_version

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
            options["num_predict"] = 32768
            logger.debug(
                "Boosting token limit for reasoning model '%s' to 32768", model
            )

        return options

    def _handle_streaming(
        self,
        model: str,
        prompt: str,
        options: Dict[str, Any],
        stream_handler: Callable[[str], None],
    ) -> str:
        """Behandelt Streaming-Response von Ollama."""
        response = self.client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options=options,
            stream=True,
        )
        full_content = ""
        full_thinking = ""

        for chunk in response:
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
            logger.warning("Model name '%s' contains spaces. This may cause 'model is required' errors in Ollama.", model)

        try:
            options = self._get_options(model, temperature)

            # Handle max_tokens override (Ollama uses num_predict)
            if "max_tokens" in kwargs:
                options["num_predict"] = kwargs["max_tokens"]

            if stream_handler:
                return self._handle_streaming(model, prompt, options, stream_handler)

            # Standard Blocking Call
            try:
                response = self.client.chat(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    options=options,
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

            msg = response.get("message", {})
            # Handle diff response formats (dict vs object)
            if isinstance(msg, dict):
                content = msg.get("content", "")
            else:
                content = getattr(msg, "content", "")

            thinking = ""
            if hasattr(msg, "thinking"):
                thinking = msg.thinking
            elif isinstance(msg, dict):
                thinking = msg.get("thinking", "")

            if not content:
                done_reason = response.get("done_reason")
                if done_reason == "length":
                    logger.debug(
                        "Ollama generation stopped due to token limit. (num_predict=%s)",
                        options.get("num_predict"),
                    )
                    if thinking:
                        logger.debug(
                            "Returning partial 'thinking' content as fallback."
                        )
                        return thinking
                    raise ValueError("Empty response from Ollama (Token limit reached)")

                if thinking:
                    logger.debug("Received 'thinking' but no 'content'. Fallback.")
                    return thinking

                logger.error("Empty content received. Full response: %s", response)
                raise ValueError("Received empty response from Ollama")

            return content
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
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error listing Ollama models: %s", e)
            return []


class AnthropicClient(BaseProviderClient):
    """Anthropic Claude Provider Client"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._client = None

    @property
    def client(self):
        """Lazy-loaded Anthropic Client"""
        if self._client is None:
            if anthropic is None:
                raise ImportError("Library 'anthropic' not installed.")

            api_key = get_required_env(
                "ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY environment variable not set"
            )
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def is_accessible(self) -> bool:
        """Prüft Zugang zu Anthropic API durch Test-Request."""
        try:
            # Versuche minimale Generierung (Cheap & Fast)
            self.client.messages.create(
                model="claude-3-haiku-20240307",  # Günstigstes Modell für Test
                max_tokens=1,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except Exception as e:
            logger.warning("Anthropic Access Check Failed: %s", e)
            return False

    def _resolve_model(self, model: str) -> str:
        """Löst Modell-Name auf (Config-Fallback)"""
        # Nur wenn kein Modell oder der generische Provider-Name übergeben wurde, Fallback nutzen.
        if not model or model == "claude":
            return self.config.get("anthropic", {}).get(
                "model", "claude-3-5-sonnet-20241022"
            )
        return model

    def _get_fingerprint(self, model: str) -> str:
        """Generates fingerprint for Anthropic Model."""
        if model in self.fingerprint_cache:
            return self.fingerprint_cache[model]

        official_version = get_official_version("anthropic", model)
        # Use simple model type (claude-3-opus)
        model_type = model.replace("claude-", "claude").replace("-", "").replace(":", "") 
        
        behavioral_hash = ModelFingerprinter.generate_behavioral_hash(
            client=self,
            model_name=model  
        )
        
        fingerprint = ModelFingerprinter.create_fingerprint(
            provider="anthropic",
            model_name=model_type,
            official_version=official_version,
            behavioral_hash=behavioral_hash
        )
        self.fingerprint_cache[model] = fingerprint
        return fingerprint

    def query(
        self,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> str:
        """Query Anthropic API"""
        try:
            model = self._resolve_model(model)
            skip_fingerprint = kwargs.pop("skip_fingerprint", False)

            # Default to config, but override with kwargs if present
            max_tokens = kwargs.get("max_tokens")
            if not max_tokens:
                max_tokens = self.config.get("anthropic", {}).get(
                    "max_tokens", MAX_TOKENS_ANTHROPIC
                )

            # Note: Streaming not implemented yet for Anthropic in this wrapper
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            # Capture Metadata
            self.last_response_metadata = {
                "model": response.model,
                "id": response.id,
                "usage": response.usage,
            }

            if not skip_fingerprint:
                fp = self._get_fingerprint(model)
                self.last_response_metadata["model_fingerprint"] = fp
                self.last_response_metadata["system_fingerprint"] = fp

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
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
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
            self._client = Mistral(api_key=api_key)
        return self._client

    def is_accessible(self) -> bool:
        """Prüft Zugang zu Mistral API."""
        try:
            # Mistral client usually supports listing models as a cheap check
            self.client.models.list()
            return True
        except Exception as e:
            logger.warning("Mistral Access Check Failed: %s", e)
            return False

    def _resolve_model(self, model: str) -> str:
        """Löst Modell-Name auf (Config-Fallback)"""
        # Nur wenn kein Modell oder der generische Provider-Name übergeben wurde, Fallback nutzen.
        if not model or model == "mistral":
            return self.config.get("mistral", {}).get("model", DEFAULT_MISTRAL_MODEL)
        return model

    def _get_fingerprint(self, model: str) -> str:
        """Generates fingerprint for Mistral Model."""
        if model in self.fingerprint_cache:
            return self.fingerprint_cache[model]

        official_version = get_official_version("mistral", model)
        # Use simple model type name for fingerprinting
        model_type = model.replace("mistral-", "").split("-")[0]
        
        # NOTE: self passed as client. query() must handle skip_fingerprint kwarg
        behavioral_hash = ModelFingerprinter.generate_behavioral_hash(
            client=self,
            model_name=model  
        )
        
        fingerprint = ModelFingerprinter.create_fingerprint(
            provider="mistral",
            model_name=model_type,
            official_version=official_version,
            behavioral_hash=behavioral_hash
        )
        self.fingerprint_cache[model] = fingerprint
        return fingerprint

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
            skip_fingerprint = kwargs.pop("skip_fingerprint", False)

            # Mistral supports max_tokens
            max_tokens = kwargs.get("max_tokens")

            # Note: Streaming not implemented yet for Mistral in this wrapper
            response = self.client.chat.complete(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                random_seed=42,  # Ensure deterministic output
                max_tokens=max_tokens, # Pass None if not provided (SDK default)
            )

            # Capture Metadata
            self.last_response_metadata = {
                "model": response.model,
                "id": response.id,
                "usage": response.usage,
            }

            if not skip_fingerprint:
                # Calculate fingerprint (this might call query recursively with skip_fingerprint=True)
                fp = self._get_fingerprint(model)
                self.last_response_metadata["model_fingerprint"] = fp
                self.last_response_metadata["system_fingerprint"] = fp # Alias for runner compatibility

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
            self._client = OpenAI(api_key=api_key)
        return self._client

    def is_accessible(self) -> bool:
        """Prüft Zugang zu OpenAI API (inkl. Quota Check)."""
        try:
            # list() reicht nicht für Quota Check (gibt oft success bei leerem Quota).
            # Daher führen wir eine minimale Generierung durch, um Billing-Status zu prüfen.
            self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            # Fängt InsufficientQuotaError, AuthenticationError, etc.
            logger.warning("OpenAI Access Check Failed: %s", e)
            return False

    def _get_fingerprint(self, model: str) -> str:
        """Generates fingerprint for OpenAI Model."""
        if model in self.fingerprint_cache:
            return self.fingerprint_cache[model]

        official_version = get_official_version("openai", model)
        # Use simple model type name for fingerprinting
        model_type = model.replace("gpt-", "gpt").split("-")[0]
        
        behavioral_hash = ModelFingerprinter.generate_behavioral_hash(
            client=self,
            model_name=model  
        )
        
        fingerprint = ModelFingerprinter.create_fingerprint(
            provider="openai",
            model_name=model_type,
            official_version=official_version,
            behavioral_hash=behavioral_hash
        )
        self.fingerprint_cache[model] = fingerprint
        return fingerprint

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
            skip_fingerprint = kwargs.pop("skip_fingerprint", False)
            params = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            }
            if "max_tokens" in kwargs:
                params["max_tokens"] = kwargs["max_tokens"]

            # Note: Streaming not implemented yet for OpenAI in this wrapper
            response = self.client.chat.completions.create(**params)

            # Capture Metadata
            self.last_response_metadata = {
                "model": response.model,
                "id": response.id,
                "system_fingerprint": getattr(response, "system_fingerprint", None),
                "usage": response.usage,
            }

            if not skip_fingerprint:
                 # Calculate custom fingerprint
                fp = self._get_fingerprint(model)
                self.last_response_metadata["model_fingerprint"] = fp
                
                # OpenAI already has system_fingerprint, but we overwrite/augment it 
                # if we want consistent behavioral fingerprint across providers.
                # OpenAI's system_fingerprint changes frequently.
                # Ours is stable per behavioral hash logic.
                # Let's use ours as the primary "version" for benchmark tracking.
                self.last_response_metadata["system_fingerprint"] = fp

            content = response.choices[0].message.content or ""

            if stream_handler and content:
                stream_handler(content)

            return content
        except Exception as e:
            logger.error("OpenAI query failed: %s", e)
            raise

    def get_available_models(self) -> List[str]:
        """List available OpenAI models"""
        return ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
