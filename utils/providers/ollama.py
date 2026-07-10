"""
Provider-spezifische LLM Clients
Getrennte Implementierungen für Ollama, Anthropic, Mistral
"""
import logging
from typing import Any
from collections.abc import Callable
from utils.ollama_config import CODING_BENCHMARK_OPTIONS, CREATIVE_BENCHMARK_OPTIONS, get_num_ctx_for_model
from utils.model_utils import is_reasoning_model
# Optional Provider Imports
try:
    import ollama
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
from utils.providers.base import BaseProviderClient
class OllamaClient(BaseProviderClient):
    """Ollama Provider Client"""
    PROVIDER_NAMES = ["ollama", "ollama_local", "ollama_cloud"]

    def __init__(self, config: dict[str, Any]):
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
    def _get_options(self, model: str, temperature: float) -> dict[str, Any]:
        """Konfiguriert Optionen basierend auf Temperatur und Modell-Typ."""
        # Select options based on temperature
        if temperature >= 0.3:
            options = CREATIVE_BENCHMARK_OPTIONS.copy()
        else:
            options = CODING_BENCHMARK_OPTIONS.copy()
        # Ensure the requested temperature is actually used
        options["temperature"] = temperature
        # Apply per-model num_ctx override (e.g. mistral-nemo native 4096 limit).
        # This makes the real context ceiling explicit so that a context overflow
        # surfaces as token_limit_fallback=True rather than a silent truncation.
        effective_ctx = get_num_ctx_for_model(model)
        if effective_ctx != options.get("num_ctx"):
            options["num_ctx"] = effective_ctx
            logger.debug(
                "Applying model-specific num_ctx=%d for '%s'",
                effective_ctx,
                model,
            )
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
        options: dict[str, Any],
        stream_handler: Callable[[str], None],
        system_prompt: str | None = None,
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
                    eval_count = chunk.get("eval_count") or 0
                    prompt_eval_count = chunk.get("prompt_eval_count") or 0
                    done_reason = chunk.get("done_reason")
                    num_predict = options.get("num_predict") or 0
                    num_ctx = options.get("num_ctx") or 32768
                    is_budget_length = done_reason == "length"
                    # Heuristic: if prompt+output tokens fill ≥95% of num_ctx but finish_reason=length,
                    # the real cause is a num_ctx overflow (context window exhausted),
                    # not a budget hit. Document as fallback, not cutoff.
                    ctx_overflow = is_budget_length and (prompt_eval_count + eval_count) >= num_ctx * 0.95
                    metrics = {
                        "total_duration": total_ns / 1e9,
                        "load_duration": load_ns / 1e9,
                        "eval_duration": eval_ns / 1e9,
                        "prompt_eval_duration": prompt_eval_ns / 1e9,
                        "eval_count": eval_count,
                        "finish_reason": done_reason,
                        "token_limit_used": num_predict if is_budget_length and not ctx_overflow else None,
                        "token_limit_fallback": ctx_overflow,
                    }
                    metrics["pure_execution_time"] = (
                        metrics["total_duration"] - metrics["load_duration"]
                    )
                    # Native generation speed: output tokens / pure eval time (excludes prefill).
                    # None when eval_duration is unavailable (e.g. Ollama cloud proxy).
                    if eval_ns > 0 and eval_count > 0:
                        metrics["tps_eval"] = round(eval_count / (eval_ns / 1e9), 2)
                    else:
                        metrics["tps_eval"] = None
                    # Usage-Objekt für LLMParser.extract_usage_tokens()
                    metrics["usage"] = {
                        "prompt_tokens": prompt_eval_count,
                        "completion_tokens": eval_count,
                        "total_tokens": prompt_eval_count + eval_count,
                    }
                    # Reasoning-Tokens: Ollama liefert keine separate Count,
                    # aber wenn thinking_content vorhanden ist, schätzen wir
                    # reasoning_tokens ≈ eval_count * 0.3 (typischer Anteil)
                    # oder setzen None wenn kein Thinking erkannt wurde.
                    if full_thinking:
                        metrics["reasoning_tokens"] = eval_count
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
        # Store think_content in metadata
        if full_thinking:
            self.last_response_metadata["think_content"] = full_thinking
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
        stream_handler: Callable[[str], None] | None = None,
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
            # Handle max_tokens override (Ollama uses num_predict)
            # Must apply AFTER allowed_overrides so the global token budget takes final precedence
            # over module-level num_predict values from config.yaml
            if "max_tokens" in kwargs:
                options["num_predict"] = kwargs["max_tokens"]
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
            logger.debug("Ollama query failed: %s", e)
            raise
    def get_available_models(self) -> list[str]:
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
