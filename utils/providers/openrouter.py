"""
OpenRouter Provider Client
OpenAI-compatible endpoint — https://openrouter.ai/api/v1
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


class OpenRouterClient(BaseProviderClient):
    """OpenRouter Provider Client (OpenAI-compatible)"""

    PROVIDER_NAMES = ["openrouter"]

    def __init__(self, config: dict):
        super().__init__(config)
        self._client = None

    @property
    def client(self):
        """Lazy-loaded OpenRouter Client using OpenAI wrapper"""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("Library 'openai' not installed.")

            import httpx
            from utils.env_utils import get_required_env

            api_key = get_required_env(
                "OPENROUTER_API_KEY", "OPENROUTER_API_KEY environment variable not set"
            )

            timeout_config = httpx.Timeout(
                connect=10.0, read=180.0, write=180.0, pool=180.0
            )

            self._client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                timeout=timeout_config,
                default_headers={
                    "HTTP-Referer": "https://github.com/cruciblemark",
                    "X-Title": "CrucibleMark Benchmark",
                },
            )

        return self._client

    def is_accessible(self) -> bool:
        """Prüft Zugang zur OpenRouter API via Key-Validation (kein Chat-Request)."""
        try:
            import httpx
            from utils.env_utils import get_required_env

            api_key = get_required_env(
                "OPENROUTER_API_KEY", "OPENROUTER_API_KEY environment variable not set"
            )
            # Lightweight key-validation: GET /auth/key returns 200 with valid key,
            # 401 with invalid. Avoids rate-limited free-tier model probes.
            with httpx.Client(timeout=10.0) as http:
                resp = http.get(
                    "https://openrouter.ai/api/v1/auth/key",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
            return resp.status_code == 200
        except Exception as e:
            logger.debug("OpenRouter Access Check Failed: %s", e)
            return False

    def query(
        self,
        model: str,
        prompt: str,
        temperature: float,
        stream_handler=None,
        **kwargs,
    ) -> str:
        """Query OpenRouter API"""
        try:
            params = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            }

            from utils.model_utils import is_reasoning_model
            is_reasoning = is_reasoning_model(model)

            req_tokens = kwargs.get("max_tokens")
            explicit_budget = req_tokens is not None
            if not req_tokens:
                req_tokens = self.config.get("defaults", {}).get("generation", {}).get("num_predict", 8192)

            if is_reasoning and explicit_budget:
                # Reasoning-Modelle: erhöhtes Budget lesen (Thinking-Tokens zählen gegen max_tokens).
                _reasoning_budgets = self.config.get("token_budgets_reasoning_models", {})
                _module_key = kwargs.get("_module_key")
                if _module_key and _module_key in _reasoning_budgets:
                    req_tokens = _reasoning_budgets[_module_key]
                else:
                    req_tokens = req_tokens * 5
            elif is_reasoning and req_tokens < 10000:
                req_tokens = 25000

            params["max_tokens"] = req_tokens

            if stream_handler:
                params["stream"] = True

            # Ausführen mit Token-Fallback Kaskade
            response, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=self.client.chat.completions.create,
                token_param_name="max_tokens",
                initial_max_tokens=req_tokens,
                error_keywords=["maximum context length", "max_tokens", "context window", "context_length"],
                func_kwargs=params,
            )

            if stream_handler:
                full_content = ""
                for chunk in response:
                    if hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content:
                        content_piece = chunk.choices[0].delta.content
                        full_content += content_piece
                        stream_handler(content_piece)

                self.last_response_metadata = {
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "token_limit_used": used_max_tokens,
                    "token_limit_fallback": fallback_triggered,
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
            logger.debug(f"OpenRouter API Error: {str(e)}")
            raise

    def get_available_models(self) -> list:
        try:
            models = self.client.models.list()
            return [m.id for m in models.data]
        except Exception:
            return []
