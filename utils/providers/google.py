# pyright: reportPrivateImportUsage=false

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
    pass
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

from utils.providers.base import BaseProviderClient
class GoogleClient(BaseProviderClient):
    """Google Gemini Provider Client"""
    PROVIDER_NAMES = ["google"]
    PROVIDER_CONFIG_KEY = "google"
    DEFAULT_TOKEN_PARAM = "max_tokens"

    def __init__(self, config: dict[str, Any]):
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
        stream_handler: Callable[[str], None] | None = None,
        **kwargs,
    ) -> str:
        """Query Google Gemini API"""
        if not genai:
            raise ImportError("Google Generative AI library not installed.")
        try:
            generation_config, gemini_model, initial_max_tokens = self._build_google_request(
                model, prompt, temperature, kwargs,
            )
            func_kwargs = {}
            if stream_handler:
                func_kwargs["stream"] = True
            response_or_stream, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=lambda max_tokens, **gen_kwargs: self._invoke_google_generator(
                    gemini_model, prompt, generation_config, max_tokens, **gen_kwargs,
                ),
                token_param_name="max_tokens",
                initial_max_tokens=initial_max_tokens,
                error_keywords=["400 bad request", "invalid argument", "maximum context length", "too large"],
                func_kwargs=func_kwargs
            )
            if stream_handler:
                return self._process_google_stream(
                    response_or_stream, used_max_tokens, fallback_triggered,
                )
            return self._process_google_blocking(
                response_or_stream, used_max_tokens, fallback_triggered,
            )
        except Exception as e:
            logger.error(f"Google Gemini query failed: {e}")
            raise

    def _build_google_request(
        self,
        model: str,
        prompt: str,
        temperature: float,
        kwargs: dict[str, Any],
    ) -> tuple[Any, Any, int]:
        """Baut GenerationConfig, Gemini-Model und liefert initial_max_tokens."""
        generation_config = genai.types.GenerationConfig(temperature=temperature)
        if "max_tokens" in kwargs:
            # Gemini uses max_output_tokens
            generation_config.max_output_tokens = kwargs["max_tokens"]
        if "top_p" in kwargs:
            generation_config.top_p = kwargs["top_p"]
        if "top_k" in kwargs:
            generation_config.top_k = kwargs["top_k"]
        _system = kwargs.get("system")
        from utils.model_utils import internal_id_to_config_form
        api_model = internal_id_to_config_form(model)
        gemini_model = genai.GenerativeModel(
            model_name=api_model,
            **({"system_instruction": _system} if _system else {}),
        )
        _token_param_name, initial_max_tokens = self._resolve_request_tokens(model, kwargs)
        return generation_config, gemini_model, initial_max_tokens

    def _invoke_google_generator(
        self,
        gemini_model: Any,
        prompt: str,
        generation_config: Any,
        max_tokens: int,
        **gen_kwargs: Any,
    ) -> Any:
        """Hüllt den Gemini-Aufruf in eine Lambda-kompatible Form für Token-Fallback."""
        generation_config.max_output_tokens = max_tokens
        return gemini_model.generate_content(
            prompt, generation_config=generation_config, **gen_kwargs,
        )

    def _process_google_stream(
        self,
        response: Any,
        used_max_tokens: int,
        fallback_triggered: bool,
    ) -> str:
        """Verarbeitet die Gemini-Streaming-Antwort."""
        full_text = ""
        from utils.providers.base import ThinkAccumulator
        think = ThinkAccumulator()
        self.last_response_metadata = {
            "token_limit_fallback": fallback_triggered,
            "token_limit_used": used_max_tokens,
        }
        for chunk in response:
            full_text = self._apply_google_stream_chunk(chunk, full_text, think)
        if think.has_content:
            self.last_response_metadata["think_content"] = think.content
        return full_text

    def _apply_google_stream_chunk(
        self,
        chunk: Any,
        full_text: str,
        think: Any,
    ) -> str:
        """Verarbeitet einen einzelnen Gemini-Stream-Chunk und liefert aktualisierten Text."""
        # chunk.text can throw if blocked by safety settings
        text_chunk = ""
        try:
            text_chunk = chunk.text
        except ValueError:
            logger.warning("Gemini chunk blocked (safety filters).")
        if text_chunk:
            stream_handler(text_chunk)
            full_text += text_chunk
        # Metadata Extraction (if available in chunk)
        if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
            um = chunk.usage_metadata
            thoughts = getattr(um, "thoughts_token_count", None)
            self.last_response_metadata["reasoning_tokens"] = thoughts if thoughts else 0
            self.last_response_metadata["usage"] = um
        if hasattr(chunk, "candidates") and chunk.candidates:
            fr = chunk.candidates[0].finish_reason
            if fr:
                self.last_response_metadata["finish_reason"] = getattr(fr, "name", str(fr))
            for part in getattr(chunk.candidates[0], "content", None).parts if hasattr(chunk.candidates[0], "content") else []:
                if hasattr(part, "thinking") and part.thinking:
                    think.add(part.thinking)
        return full_text

    def _process_google_blocking(
        self,
        response: Any,
        used_max_tokens: int,
        fallback_triggered: bool,
    ) -> str:
        """Verarbeitet die Gemini-Blocking-Antwort."""
        self.last_response_metadata = {
            "token_limit_fallback": fallback_triggered,
            "token_limit_used": used_max_tokens,
        }
        self._populate_google_blocking_candidate_metadata(response)
        self._populate_google_usage_metadata(response)
        try:
            return response.text
        except ValueError:
            logger.warning(f"Gemini check blocked: {response.prompt_feedback}")
            self.last_response_metadata["finish_reason"] = "SAFETY"
            return "Error: Content blocked by safety filters."

    def _populate_google_blocking_candidate_metadata(self, response: Any) -> None:
        """Schreibt finish_reason und think_content aus dem ersten Candidate."""
        from utils.providers.base import ThinkAccumulator

        if not (hasattr(response, "candidates") and response.candidates):
            return
        fr = response.candidates[0].finish_reason
        if fr:
            self.last_response_metadata["finish_reason"] = getattr(fr, "name", str(fr))
        think = ThinkAccumulator()
        for part in getattr(response.candidates[0], "content", None).parts if hasattr(response.candidates[0], "content") else []:
            if hasattr(part, "thinking") and part.thinking:
                think.add(part.thinking)
        if think.has_content:
            self.last_response_metadata["think_content"] = think.content

    def _populate_google_usage_metadata(self, response: Any) -> None:
        """Schreibt reasoning_tokens + usage aus response.usage_metadata."""
        if not (hasattr(response, "usage_metadata") and response.usage_metadata):
            return
        um = response.usage_metadata
        thoughts = getattr(um, "thoughts_token_count", None)
        self.last_response_metadata["reasoning_tokens"] = thoughts if thoughts else 0
        self.last_response_metadata["usage"] = um
    def get_available_models(self) -> list[str]:
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
