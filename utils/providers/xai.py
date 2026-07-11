"""
Provider-spezifische LLM Clients
Getrennte Implementierungen für Ollama, Anthropic, Mistral
"""
import logging
from typing import Any
# Optional Provider Imports
try:
    pass
except ImportError:
    ollama = None
try:
    pass
except ImportError:
    anthropic = None
try:
    pass
except ImportError:
    Mistral = None
try:
    pass
except ImportError:
    OpenAI = None
# Configure logging
logger = logging.getLogger(__name__)

# Configure logging
logger = logging.getLogger(__name__)

from utils.providers.base import BaseProviderClient
class XAIClient(BaseProviderClient):
    """XAI Provider Client"""
    PROVIDER_NAMES = ["xai"]
    PROVIDER_CONFIG_KEY = "xai"
    DEFAULT_TOKEN_PARAM = "max_completion_tokens"

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
            from openai import OpenAI, AuthenticationError, PermissionDeniedError, NotFoundError, RateLimitError
            check_client = OpenAI(api_key=self.client.api_key, base_url="https://api.x.ai/v1", max_retries=0)
            check_client.chat.completions.create(
                model="grok-3-mini",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
            )
            return True
        except AuthenticationError as e:
            logger.warning("XAI Access Check: Authentifizierung fehlgeschlagen: %s", e)
            return False
        except PermissionDeniedError as e:
            logger.warning("XAI Access Check: Zugriff verweigert (Budget/Permissions): %s", e)
            return False
        except NotFoundError as e:
            # Testmodell nicht gefunden, aber API selbst ist erreichbar
            logger.warning("XAI Access Check: Testmodell nicht gefunden, API aber erreichbar: %s", e)
            return True
        except RateLimitError as e:
            logger.warning("XAI Access Check: Rate Limit — API erreichbar: %s", e)
            return True
        except Exception as e:
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
            params, token_param_name, req_tokens = self._build_xai_params(
                model, prompt, temperature, kwargs, stream_handler,
            )
            response, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=self.client.chat.completions.create,
                token_param_name=token_param_name,
                initial_max_tokens=req_tokens,
                error_keywords=["maximum context length", "max_tokens", "max_completion_tokens"],
                func_kwargs=params
            )
            if stream_handler:
                return self._process_xai_stream(response, used_max_tokens, fallback_triggered, stream_handler)
            return self._process_xai_blocking(response, used_max_tokens, fallback_triggered)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error("XAI API Error: %s", e)
            raise e

    def _build_xai_params(
        self,
        model: str,
        prompt: str,
        temperature: float,
        kwargs: dict,
        stream_handler,
    ) -> tuple[dict, str, int]:
        """Baut die XAI-Request-Parameter (messages, token-param, stream-flag)."""
        from utils.model_utils import internal_id_to_config_form
        _system = kwargs.get("system")
        api_model = internal_id_to_config_form(model)
        params = {
            "model": api_model,
            "messages": (
                [{"role": "system", "content": _system}] if _system else []
            ) + [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        token_param_name, req_tokens = self._resolve_request_tokens(model, kwargs)
        params[token_param_name] = req_tokens
        if stream_handler:
            params["stream"] = True
        return params, token_param_name, req_tokens

    def _process_xai_stream(
        self,
        response: Any,
        used_max_tokens: int,
        fallback_triggered: bool,
        stream_handler=None,
    ) -> str:
        """Verarbeitet den XAI-Streaming-Response."""
        full_content = ""
        from utils.providers.base import ThinkAccumulator
        think = ThinkAccumulator()
        stream_usage = None
        self.last_response_metadata = {
            "token_limit_fallback": fallback_triggered,
            "token_limit_used": used_max_tokens,
        }
        for chunk in response:
            self._capture_xai_chunk_metadata(chunk)
            if hasattr(chunk, "usage") and chunk.usage:
                stream_usage = chunk.usage
            if chunk.choices:
                delta = chunk.choices[0].delta
                if hasattr(delta, "content") and delta.content:
                    stream_handler(delta.content)
                    full_content += delta.content
                reasoning_piece = (
                    getattr(delta, "reasoning", None)
                    or getattr(delta, "reasoning_content", None)
                )
                if reasoning_piece:
                    think.add(reasoning_piece)
        if stream_usage:
            self.last_response_metadata["usage"] = stream_usage
            rt = self._extract_reasoning_tokens(stream_usage)
            if rt is not None:
                self.last_response_metadata["reasoning_tokens"] = rt
        if think.has_content:
            self.last_response_metadata["think_content"] = think.content
        return full_content

    def _capture_xai_chunk_metadata(self, chunk: Any) -> None:
        """Schreibt id/model/finish_reason aus einem XAI-Stream-Chunk."""
        if not self.last_response_metadata.get("id") and chunk.id:
            self.last_response_metadata["id"] = chunk.id
        if not self.last_response_metadata.get("model") and chunk.model:
            self.last_response_metadata["model"] = chunk.model
        if chunk.choices and hasattr(chunk.choices[0], "finish_reason") and chunk.choices[0].finish_reason:
            self.last_response_metadata["finish_reason"] = chunk.choices[0].finish_reason

    def _process_xai_blocking(
        self,
        response: Any,
        used_max_tokens: int,
        fallback_triggered: bool,
    ) -> str:
        """Verarbeitet den XAI-Blocking-Response."""
        raw_text = response.choices[0].message.content
        msg = response.choices[0].message if response.choices else None
        reasoning = self._extract_think_from_message(msg)
        self.last_response_metadata = {
            "token_limit_fallback": fallback_triggered,
            "token_limit_used": used_max_tokens,
            "id": getattr(response, "id", None),
            "model": getattr(response, "model", None),
            "finish_reason": response.choices[0].finish_reason if response.choices else None,
        }
        if hasattr(response, "usage") and response.usage:
            usage = response.usage
            self.last_response_metadata["usage"] = usage
            rt = self._extract_reasoning_tokens(usage)
            if rt is not None:
                self.last_response_metadata["reasoning_tokens"] = rt
        if reasoning:
            self.last_response_metadata["think_content"] = reasoning
        return raw_text if raw_text else ""

    def get_available_models(self) -> list:
        try:
            models = self.client.models.list()
            return [m.id for m in models.data]
        except Exception:
            return ["grok-3", "grok-3-mini"]
