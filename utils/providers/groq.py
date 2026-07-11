"""
Groq Provider Client
Ollama / OpenAI compatible endpoint
"""

import logging

# Optional Provider Imports
try:
    from openai import OpenAI  # pylint: disable=unused-import
except ImportError:
    OpenAI = None

# Configure logging
logger = logging.getLogger(__name__)

from utils.providers.base import BaseProviderClient


class GroqClient(BaseProviderClient):
    """Groq Provider Client"""

    PROVIDER_NAMES = ["groq"]
    PROVIDER_CONFIG_KEY = "groq"
    DEFAULT_TOKEN_PARAM = "max_completion_tokens"

    def __init__(self, config: dict):
        super().__init__(config)
        self._client = None

    @property
    def client(self):
        """Lazy-loaded Groq Client using OpenAI wrapper"""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("Library 'openai' not installed.")

            import httpx
            from utils.env_utils import get_required_env

            api_key = get_required_env(
                "GROQ_API_KEY", "GROQ_API_KEY environment variable not set"
            )

            timeout_config = httpx.Timeout(
                connect=10.0, read=180.0, write=180.0, pool=180.0
            )

            self._client = OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1",
                timeout=timeout_config
            )

        return self._client


    def is_accessible(self) -> bool:
        """Prüft Zugang zu Groq API."""
        try:
            from openai import OpenAI, AuthenticationError, PermissionDeniedError, NotFoundError, RateLimitError
            check_client = OpenAI(api_key=self.client.api_key, base_url="https://api.groq.com/openai/v1", max_retries=0)
            check_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
            )
            return True
        except AuthenticationError as e:
            logger.warning("Groq Access Check: Authentifizierung fehlgeschlagen: %s", e)
            return False
        except PermissionDeniedError as e:
            logger.warning("Groq Access Check: Zugriff verweigert (Budget/Permissions): %s", e)
            return False
        except NotFoundError as e:
            # Testmodell nicht gefunden, aber API selbst ist erreichbar
            logger.warning("Groq Access Check: Testmodell nicht gefunden, API aber erreichbar: %s", e)
            return True
        except RateLimitError as e:
            logger.warning("Groq Access Check: Rate Limit — API erreichbar: %s", e)
            return True
        except Exception as e:
            logger.debug("Groq Access Check Failed: %s", e)
            return False


    def query(
        self,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler = None,
        **kwargs,
    ) -> str:
        """Query Groq API"""
        try:
            params, token_param_name, req_tokens = self._build_groq_params(
                model, prompt, temperature, kwargs, stream_handler,
            )

            # Ausführen mit Token-Fallback Kaskade
            response, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=self.client.chat.completions.create,
                token_param_name=token_param_name,
                initial_max_tokens=req_tokens,
                error_keywords=["maximum context length", "max_tokens", "max_completion_tokens", "context window"],
                func_kwargs=params
            )

            if stream_handler:
                return self._process_groq_stream(response, used_max_tokens, fallback_triggered)
            return self._process_groq_blocking(response, used_max_tokens, fallback_triggered)

        except Exception as e:
            logger.debug(f"Groq API Error: {str(e)}")
            raise

    def _build_groq_params(
        self,
        model: str,
        prompt: str,
        temperature: float,
        kwargs: dict,
        stream_handler,
    ) -> tuple[dict, str, int]:
        """Erstellt die Groq-Request-Parameter (messages, token-param, stream-flag)."""
        _system = kwargs.get("system")
        from utils.model_utils import internal_id_to_config_form
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

    def _process_groq_stream(
        self,
        response: Any,
        used_max_tokens: int,
        fallback_triggered: bool,
    ) -> str:
        """Verarbeitet den Groq-Streaming-Response."""
        full_content = ""
        from utils.providers.base import ThinkAccumulator
        think = ThinkAccumulator()
        stream_usage = None
        for chunk in response:
            if hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content:
                content_piece = chunk.choices[0].delta.content
                full_content += content_piece
                stream_handler(content_piece)
            reasoning_piece = (
                getattr(chunk.choices[0].delta, "reasoning", None)
                or getattr(chunk.choices[0].delta, "reasoning_content", None)
            )
            if reasoning_piece:
                think.add(reasoning_piece)
            if hasattr(chunk, "usage") and chunk.usage:
                stream_usage = chunk.usage

        meta = {
            "total_tokens": stream_usage.total_tokens if stream_usage else 0,
            "prompt_tokens": stream_usage.prompt_tokens if stream_usage else 0,
            "completion_tokens": stream_usage.completion_tokens if stream_usage else 0,
            "token_limit_used": used_max_tokens,
            "token_limit_fallback": fallback_triggered,
        }
        if stream_usage:
            rt = self._extract_reasoning_tokens(stream_usage)
            if rt is not None:
                meta["reasoning_tokens"] = rt
            meta["usage"] = stream_usage
        if think.has_content:
            meta["think_content"] = think.content
        self.last_response_metadata = meta
        return full_content

    def _process_groq_blocking(
        self,
        response: Any,
        used_max_tokens: int,
        fallback_triggered: bool,
    ) -> str:
        """Verarbeitet den Groq-Blocking-Response."""
        result = response.choices[0].message.content or ""
        msg = response.choices[0].message if response.choices else None
        reasoning = self._extract_think_from_message(msg)
        usage = response.usage
        if usage:
            rt = self._extract_reasoning_tokens(usage)
            meta = {
                "total_tokens": usage.total_tokens,
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "token_limit_used": used_max_tokens,
                "token_limit_fallback": fallback_triggered,
                "finish_reason": response.choices[0].finish_reason if response.choices else None,
                "reasoning_tokens": rt,
                "usage": usage,
            }
            if reasoning:
                meta["think_content"] = reasoning
            self.last_response_metadata = meta
        return result

    def get_available_models(self) -> list:
        try:
            models = self.client.models.list()
            return [m.id for m in models.data]
        except Exception:
            return []
