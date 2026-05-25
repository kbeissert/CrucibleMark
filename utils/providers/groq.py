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
            _system = kwargs.get("system")
            params = {
                "model": model,
                "messages": (
                    [{"role": "system", "content": _system}] if _system else []
                ) + [{"role": "user", "content": prompt}],
                "temperature": temperature,
            }

            req_tokens = kwargs.get("max_tokens")
            if not req_tokens:
                req_tokens = self.config.get("defaults", {}).get("generation", {}).get("num_predict", 8192)

            params["max_completion_tokens"] = req_tokens

            if stream_handler:
                params["stream"] = True

            # Ausführen mit Token-Fallback Kaskade
            response, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=self.client.chat.completions.create,
                token_param_name="max_completion_tokens",
                initial_max_tokens=req_tokens,
                error_keywords=["maximum context length", "max_tokens", "max_completion_tokens", "context window"],
                func_kwargs=params
            )

            if stream_handler:
                full_content = ""
                for chunk in response:
                    # Groq returns similar chunk structure to OpenAI
                    if hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content:
                        content_piece = chunk.choices[0].delta.content
                        full_content += content_piece
                        stream_handler(content_piece)

                # Fetch metadata from response logic if possible (Groq may not provide usage in stream, but we handle it gracefully)
                self.last_response_metadata = {
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "token_limit_used": used_max_tokens,
                    "token_limit_fallback": fallback_triggered
                }
                return full_content

            else:
                result = response.choices[0].message.content or ""

                usage = response.usage
                if usage:
                    self.last_response_metadata = {
                        "total_tokens": usage.total_tokens,
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "token_limit_used": used_max_tokens,
                        "token_limit_fallback": fallback_triggered,
                        "finish_reason": response.choices[0].finish_reason if response.choices else None,
                    }

                return result

        except Exception as e:
            logger.debug(f"Groq API Error: {str(e)}")
            raise

    def get_available_models(self) -> list:
        try:
            models = self.client.models.list()
            return [m.id for m in models.data]
        except Exception:
            return []
