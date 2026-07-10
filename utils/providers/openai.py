"""
Provider-spezifische LLM Clients
Getrennte Implementierungen für Ollama, Anthropic, Mistral
"""
import logging
from typing import Any
from collections.abc import Callable
from utils.env_utils import get_required_env
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
    from openai import OpenAI
except ImportError:
    OpenAI = None
# Configure logging
logger = logging.getLogger(__name__)

from utils.providers.base import BaseProviderClient
class OpenAIClient(BaseProviderClient):
    """OpenAI Provider Client"""
    PROVIDER_NAMES = ["openai"]
    PROVIDER_CONFIG_KEY = "openai"
    DEFAULT_TOKEN_PARAM = "max_completion_tokens"

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._client = None

    def _is_completions_only(self, model: str) -> bool:
        """Prüft ob Modell die Legacy /v1/completions Endpoint braucht.

        Liest ``completions_only: true`` aus dem Model-Eintrag in
        provider_config.yaml. Fallback: ``False`` (Chat-Endpoint).

        Nutzt ``find_model_in_provider_cfg()`` für normalisierten Lookup
        (Underscore→Dot in Version-Segmenten).
        """
        from utils.model_utils import find_model_in_provider_cfg
        provider_cfg = self._get_provider_cfg()
        entry = find_model_in_provider_cfg(provider_cfg, model)
        return bool(entry.get("completions_only", False)) if entry else False

    def _is_responses_only(self, model: str) -> bool:
        """Prüft ob Modell die Responses API (/v1/responses) braucht.

        Reasoning-Modelle wie gpt-5.x-pro unterstützen weder chat noch
        completions — nur die Responses API. Liest ``responses_only: true``
        aus dem Model-Eintrag in provider_config.yaml.
        """
        from utils.model_utils import find_model_in_provider_cfg
        provider_cfg = self._get_provider_cfg()
        entry = find_model_in_provider_cfg(provider_cfg, model)
        return bool(entry.get("responses_only", False)) if entry else False

    def _build_completions_params(
        self, model: str, api_model: str, prompt: str, system: str | None,
    ) -> tuple[dict[str, Any], str]:
        """Baut Params für Legacy /v1/completions Endpoint.

        Returns (params_dict, token_param_name).
        """
        combined = (system + "\n\n" + prompt) if system else prompt
        return {"model": api_model, "prompt": combined}, "max_tokens"

    def _build_chat_params(
        self, model: str, api_model: str, prompt: str, system: str | None,
    ) -> tuple[dict[str, Any], str]:
        """Baut Params für /v1/chat/completions Endpoint.

        Returns (params_dict, token_param_name).
        """
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return {"model": api_model, "messages": messages}, "max_completion_tokens"

    def _build_responses_params(
        self, model: str, api_model: str, prompt: str, system: str | None,
    ) -> tuple[dict[str, Any], str]:
        """Baut Params für /v1/responses Endpoint (Reasoning-Modelle).

        Returns (params_dict, token_param_name).
        """
        params: dict[str, Any] = {"model": api_model, "input": prompt}
        if system:
            params["instructions"] = system
        return params, "max_output_tokens"

    def _process_blocking_responses(
        self, response: Any, fallback_triggered: bool, used_max_tokens: int,
    ) -> str:
        """Verarbeitet Blocking-Response für /v1/responses (Reasoning-Modelle)."""
        content = response.output_text if hasattr(response, "output_text") else ""
        usage = response.usage
        reasoning_tokens = None
        if usage and hasattr(usage, "output_tokens_details") and usage.output_tokens_details:
            reasoning_tokens = getattr(usage.output_tokens_details, "reasoning_tokens", None)
        self.last_response_metadata = {
            "model": getattr(response, "model", None),
            "id": getattr(response, "id", None),
            "usage": usage,
            "token_limit_fallback": fallback_triggered,
            "token_limit_used": used_max_tokens,
            "reasoning_tokens": reasoning_tokens,
        }
        return content

    def _process_stream(
        self, response_stream: Any, use_completions: bool,
        stream_handler: Callable[[str], None], fallback_triggered: bool,
        used_max_tokens: int,
    ) -> str:
        """Verarbeitet Streaming-Response (chat oder completions)."""
        from utils.providers.base import ThinkAccumulator

        full_content = ""
        think = ThinkAccumulator()
        stream_usage = None
        self.last_response_metadata = {
            "token_limit_fallback": fallback_triggered,
            "token_limit_used": used_max_tokens,
        }
        for chunk in response_stream:
            if not self.last_response_metadata.get("id") and chunk.id:
                self.last_response_metadata["id"] = chunk.id
            if not self.last_response_metadata.get("model") and chunk.model:
                self.last_response_metadata["model"] = chunk.model
            if getattr(chunk, "system_fingerprint", None):
                self.last_response_metadata["system_fingerprint"] = chunk.system_fingerprint
            if hasattr(chunk, "usage") and chunk.usage:
                stream_usage = chunk.usage
            if chunk.choices and hasattr(chunk.choices[0], "finish_reason") and chunk.choices[0].finish_reason:
                self.last_response_metadata["finish_reason"] = chunk.choices[0].finish_reason
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if use_completions:
                text_piece = getattr(delta, "text", None)
                if text_piece:
                    stream_handler(text_piece)
                    full_content += text_piece
            else:
                if hasattr(delta, "content") and delta.content:
                    stream_handler(delta.content)
                    full_content += delta.content
                reasoning_piece = getattr(delta, "reasoning", None) or getattr(delta, "reasoning_content", None)
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

    def _process_blocking_completions(
        self, response: Any, fallback_triggered: bool, used_max_tokens: int,
    ) -> str:
        """Verarbeitet Blocking-Response für Legacy /v1/completions."""
        content = (response.choices[0].text or "") if response.choices else ""
        usage = response.usage
        self.last_response_metadata = {
            "model": response.model,
            "id": response.id,
            "system_fingerprint": getattr(response, "system_fingerprint", None),
            "usage": usage,
            "finish_reason": getattr(response.choices[0], "finish_reason", None) if response.choices else None,
            "token_limit_fallback": fallback_triggered,
            "token_limit_used": used_max_tokens,
            "reasoning_tokens": self._extract_reasoning_tokens(usage) if usage else None,
        }
        return content

    def _process_blocking_chat(
        self, response: Any, fallback_triggered: bool, used_max_tokens: int,
    ) -> str:
        """Verarbeitet Blocking-Response für /v1/chat/completions."""
        msg = response.choices[0].message if response.choices else None
        content = (msg.content or "") if msg else ""
        reasoning = self._extract_think_from_message(msg)
        usage = response.usage
        reasoning_tokens = self._extract_reasoning_tokens(usage) if usage else None
        self.last_response_metadata = {
            "model": response.model,
            "id": response.id,
            "system_fingerprint": getattr(response, "system_fingerprint", None),
            "usage": usage,
            "finish_reason": getattr(response.choices[0], "finish_reason", None) if response.choices else None,
            "token_limit_fallback": fallback_triggered,
            "token_limit_used": used_max_tokens,
            "reasoning_tokens": reasoning_tokens,
        }
        if reasoning:
            self.last_response_metadata["think_content"] = reasoning
        return content
    @property
    def client(self):
        """Lazy-loaded OpenAI Client"""
        if self._client is None:
            if OpenAI is None:
                raise ImportError("Library 'openai' not installed.")
            api_key = get_required_env(
                "OPENAI_API_KEY", "OPENAI_API_KEY environment variable not set"
            )
            import httpx
            provider_cfg = self._get_provider_cfg()
            # Configurable read timeout — reasoning models need more time (default 600s = 10 min)
            read_timeout = float(provider_cfg.get("request_timeout", 600.0))
            timeout_config = httpx.Timeout(
                connect=10.0, read=read_timeout, write=180.0, pool=180.0
            )
            # max_retries=0: SDK-Retries deaktiviert — unsere eigene Retry-Logik
            # (RetryHandler + _execute_with_token_fallback) ist ausreichend.
            # SDK-Retries erzeugen bei Responses API jedes Mal eine neue Reasoning-Request
            # und verbrennen unnötig Quota.
            self._client = OpenAI(
                api_key=api_key, timeout=timeout_config, max_retries=0,
            )
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
        stream_handler: Callable[[str], None] | None = None,
        **kwargs,
    ) -> str:
        """Query OpenAI API (responses, chat, or legacy completions endpoint)"""
        try:
            from utils.model_utils import internal_id_to_config_form
            _system = kwargs.get("system")
            api_model = internal_id_to_config_form(model)
            use_responses = self._is_responses_only(model)
            use_completions = not use_responses and self._is_completions_only(model)

            if use_responses:
                params, token_param_name = self._build_responses_params(model, api_model, prompt, _system)
            elif use_completions:
                params, token_param_name = self._build_completions_params(model, api_model, prompt, _system)
            else:
                params, token_param_name = self._build_chat_params(model, api_model, prompt, _system)

            is_reasoning = use_responses or (
                model.startswith("o1") or model.startswith("o3") or model.startswith("o4") or "gpt-5" in model
            )
            if not is_reasoning:
                params["temperature"] = temperature

            _, initial_tokens_to_try = self._resolve_request_tokens(model, kwargs)

            if use_responses:
                api_func = self.client.responses.create
            elif use_completions:
                api_func = self.client.completions.create
            else:
                api_func = self.client.chat.completions.create

            if stream_handler:
                params["stream"] = True
                if not use_completions and not use_responses:
                    params["stream_options"] = {"include_usage": True}

            response_or_stream, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=api_func,
                token_param_name=token_param_name,
                initial_max_tokens=initial_tokens_to_try,
                error_keywords=["maximum context length", "max_tokens", "max_completion_tokens", "max_output_tokens", "too large"],
                func_kwargs=params,
            )

            if stream_handler and not use_responses:
                return self._process_stream(
                    response_or_stream, use_completions, stream_handler,
                    fallback_triggered, used_max_tokens,
                )

            response = response_or_stream
            if use_responses:
                return self._process_blocking_responses(response, fallback_triggered, used_max_tokens)
            if use_completions:
                return self._process_blocking_completions(response, fallback_triggered, used_max_tokens)
            return self._process_blocking_chat(response, fallback_triggered, used_max_tokens)
        except Exception as e:
            logger.error("OpenAI query failed: %s", e)
            raise

    def get_available_models(self) -> list[str]:
        """List available OpenAI models"""
        return ["gpt-5.2-pro", "gpt-5-mini", "o3-mini", "gpt-4o"]
