"""
OpenRouter Provider Client
OpenAI-compatible endpoint — https://openrouter.ai/api/v1
"""

import logging
from typing import Any
from utils.providers.base import BaseProviderClient

# Optional Provider Imports
try:
    from openai import OpenAI  # pylint: disable=unused-import
except ImportError:
    OpenAI = None

# Configure logging
logger = logging.getLogger(__name__)

# Einige Model-IDs haben Ambiguität zwischen Bindestrich und Underscore
# (z.B. z-ai/glm_5_2: das _ zwischen glm und 5 war ein Bindestrich).
# interal_id_to_config_form() löst Versions-Underscores (5_2→5.2), aber
# nicht Bindestrich-Underscore-Ambiguität. Alias-Dict als Fallback.
_OPENROUTER_ID_ALIASES: dict[str, str] = {
    "z-ai/glm_5_2": "z-ai/glm-5.2",
    "z-ai/glm_5_1-20260406": "z-ai/glm-5.1-20260406",
    "z-ai/glm_4_7": "z-ai/glm-4.7",
    "z-ai/glm_4_6": "z-ai/glm-4.6",
}


class OpenRouterClient(BaseProviderClient):
    """OpenRouter Provider Client (OpenAI-compatible)"""

    PROVIDER_NAMES = ["openrouter"]
    PROVIDER_CONFIG_KEY = "openrouter"
    DEFAULT_TOKEN_PARAM = "max_tokens"

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
                connect=10.0, read=600.0, write=600.0, pool=600.0
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
            params, token_param_name, req_tokens = self._build_openrouter_params(
                model, prompt, temperature, kwargs, stream_handler,
            )

            # Ausführen mit Token-Fallback Kaskade
            response, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=self.client.chat.completions.create,
                token_param_name=token_param_name,
                initial_max_tokens=req_tokens,
                error_keywords=["maximum context length", "max_tokens", "context window", "context_length"],
                func_kwargs=params,
            )

            if stream_handler:
                return self._process_openrouter_stream(response, used_max_tokens, fallback_triggered, stream_handler)
            return self._process_openrouter_blocking(response, used_max_tokens, fallback_triggered)

        except Exception as e:
            logger.debug(f"OpenRouter API Error: {str(e)}")
            raise

    def _build_openrouter_params(
        self,
        model: str,
        prompt: str,
        temperature: float,
        kwargs: dict,
        stream_handler,
    ) -> tuple[dict, str, int]:
        """Baut die OpenRouter-Request-Parameter (messages, token-param, data_collection)."""
        from utils.model_utils import internal_id_to_config_form
        _system = kwargs.get("system")
        api_model = _OPENROUTER_ID_ALIASES.get(model) or internal_id_to_config_form(model)
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
        # Alibaba Cloud (Qwen) und andere Anbieter erfordern explizite Zustimmung
        # zur Datenverarbeitung — per-Request-Override der Account-Policy.
        params["extra_body"] = {"data_collection": "allow"}
        # Per-Modell Reasoning-Config (OpenRouter Unified-Parameter `reasoning`).
        # Begrenzt das Thinking-Budget separat vom Output-Budget — bei Modellen
        # mit nicht-terminierendem CoT frisst sonst das Reasoning das komplette
        # max_tokens (0 sichtbarer Output).
        reasoning_cfg = self._resolve_reasoning_config(model, api_model)
        if reasoning_cfg:
            params["extra_body"]["reasoning"] = reasoning_cfg
        return params, token_param_name, req_tokens

    def _resolve_reasoning_config(self, model: str, api_model: str) -> dict[str, Any] | None:
        """Löst die Per-Modell Reasoning-Config aus provider_config.yaml.

        Lookup-Key ist die Modell-ID (Config-Form oder Internal-Form), analog zu
        ``model_max_tokens`` in ``_resolve_request_tokens()``.
        """
        cfg_map = self._get_provider_cfg().get("model_reasoning_config", {})
        return cfg_map.get(model) or cfg_map.get(api_model)

    def _process_openrouter_stream(
        self,
        response: Any,
        used_max_tokens: int,
        fallback_triggered: bool,
        stream_handler=None,
    ) -> str:
        """Verarbeitet den OpenRouter-Streaming-Response."""
        full_content = ""
        from utils.providers.base import ThinkAccumulator
        think = ThinkAccumulator()
        stream_usage = None
        for chunk in response:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                content_piece = delta.content
                full_content += content_piece
                stream_handler(content_piece)
            # Reasoning/Thinking extrahieren (GLM 5.x: "reasoning")
            reasoning_piece = (
                getattr(delta, "reasoning", None)
                or getattr(delta, "reasoning_content", None)
            )
            if reasoning_piece:
                think.add(reasoning_piece)
            # Usage kommt im letzten Streaming-Chunk
            if hasattr(chunk, "usage") and chunk.usage:
                stream_usage = chunk.usage

        meta = {
            "total_tokens": stream_usage.total_tokens if stream_usage else 0,
            "prompt_tokens": stream_usage.prompt_tokens if stream_usage else 0,
            "completion_tokens": stream_usage.completion_tokens if stream_usage else 0,
            "token_limit_used": used_max_tokens,
            "token_limit_fallback": fallback_triggered,
        }
        if think.has_content:
            meta["think_content"] = think.content
        if stream_usage:
            meta["usage"] = stream_usage
            # reasoning_tokens via SSoT-Helper
            rt = self._extract_reasoning_tokens(stream_usage)
            if rt is not None:
                meta["reasoning_tokens"] = rt
        self.last_response_metadata = meta
        return full_content

    def _process_openrouter_blocking(
        self,
        response: Any,
        used_max_tokens: int,
        fallback_triggered: bool,
    ) -> str:
        """Verarbeitet den OpenRouter-Blocking-Response."""
        msg = response.choices[0].message if response.choices else None
        result = (msg.content or "") if msg else ""
        # Reasoning/Thinking-Content extrahieren
        reasoning = self._extract_think_from_message(msg)
        usage = response.usage
        if usage:
            reasoning_tokens = self._extract_reasoning_tokens(usage)
            meta = {
                "total_tokens": usage.total_tokens,
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "token_limit_used": used_max_tokens,
                "token_limit_fallback": fallback_triggered,
                "finish_reason": response.choices[0].finish_reason if response.choices else None,
                "reasoning_tokens": reasoning_tokens,
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
