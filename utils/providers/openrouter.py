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
            _system = kwargs.get("system")
            params = {
                "model": model,
                "messages": (
                    [{"role": "system", "content": _system}] if _system else []
                ) + [{"role": "user", "content": prompt}],
                "temperature": temperature,
            }

            from utils.model_utils import resolve_token_budget
            _provider_cfg = self.config.get("providers", {}).get("commercial", {}).get("openrouter", {})
            token_param_name = _provider_cfg.get("token_param_name", "max_tokens")
            req_tokens, _ = resolve_token_budget(
                model, kwargs.get("max_tokens"), self.config, kwargs.get("_module_key")
            )
            params[token_param_name] = req_tokens

            if stream_handler:
                params["stream"] = True

            # Alibaba Cloud (Qwen) und andere Anbieter erfordern explizite Zustimmung
            # zur Datenverarbeitung — per-Request-Override der Account-Policy.
            params["extra_body"] = {"data_collection": "allow"}

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
                    reasoning_tokens: int | None = None
                    if hasattr(usage, "completion_tokens_details") and usage.completion_tokens_details:
                        reasoning_tokens = getattr(usage.completion_tokens_details, "reasoning_tokens", None)
                    self.last_response_metadata = {
                        "total_tokens": usage.total_tokens,
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "token_limit_used": used_max_tokens,
                        "token_limit_fallback": fallback_triggered,
                        "finish_reason": response.choices[0].finish_reason if response.choices else None,
                        "reasoning_tokens": reasoning_tokens,
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
