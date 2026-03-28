# pyright: reportPrivateImportUsage=false

"""
Provider-spezifische LLM Clients
Getrennte Implementierungen für Ollama, Anthropic, Mistral
"""
import logging
from typing import Any, List, Optional, Callable, Dict
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

    def __init__(self, config: Dict[str, Any]):
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
        stream_handler: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> str:
        """Query Google Gemini API"""
        if not genai:
            raise ImportError("Google Generative AI library not installed.")
        try:
            # Configure Generation Config
            generation_config = genai.types.GenerationConfig(temperature=temperature)
            if "max_tokens" in kwargs:
                # Gemini uses max_output_tokens
                generation_config.max_output_tokens = kwargs["max_tokens"]
            if "top_p" in kwargs:
                generation_config.top_p = kwargs["top_p"]
            if "top_k" in kwargs:
                generation_config.top_k = kwargs["top_k"]
            # Initialize Model
            gemini_model = genai.GenerativeModel(model_name=model)
            initial_max_tokens = kwargs.get("max_tokens", self.config.get("defaults", {}).get("generation", {}).get("num_predict", 8192))
            def _google_generator(max_tokens, **gen_kwargs):
                generation_config.max_output_tokens = max_tokens
                return gemini_model.generate_content(prompt, generation_config=generation_config, **gen_kwargs)
            func_kwargs = {}
            if stream_handler:
                func_kwargs["stream"] = True
            response_or_stream, used_max_tokens, fallback_triggered = self._execute_with_token_fallback(
                func=_google_generator,
                token_param_name="max_tokens",
                initial_max_tokens=initial_max_tokens,
                error_keywords=["400 bad request", "invalid argument", "maximum context length", "too large"],
                func_kwargs=func_kwargs
            )
            # Streaming Support
            if stream_handler:
                response = response_or_stream
                full_text = ""
                self.last_response_metadata = {
                    "token_limit_fallback": fallback_triggered,
                    "token_limit_used": used_max_tokens,
                }
                for chunk in response:
                    # chunk.text can throw if blocked by safety settings
                    text_chunk = ""
                    try:
                        text_chunk = chunk.text
                    except ValueError:
                        # Handle safety filter blocking
                        logger.warning("Gemini chunk blocked (safety filters).")
                    if text_chunk:
                        stream_handler(text_chunk)
                        full_text += text_chunk
                    # Metadata Extraction (if available in chunk)
                    if hasattr(chunk, "usage_metadata"):
                        # Gemini usage is cumulative in last chunk usually
                        # Convert proto to dict if needed, or use object
                        # We just store it for now
                        pass
                    if hasattr(chunk, "candidates") and chunk.candidates:
                        fr = chunk.candidates[0].finish_reason
                        if fr:
                            # Usually an enum, convert to string
                            self.last_response_metadata["finish_reason"] = getattr(fr, "name", str(fr))
                return full_text
            # Blocking Call
            response = response_or_stream
            self.last_response_metadata = {
                "token_limit_fallback": fallback_triggered,
                "token_limit_used": used_max_tokens,
            }
            if hasattr(response, "candidates") and response.candidates:
                fr = response.candidates[0].finish_reason
                if fr:
                    self.last_response_metadata["finish_reason"] = getattr(fr, "name", str(fr))
            try:
                return response.text
            except ValueError:
                # Often happens if content was blocked
                logger.warning(f"Gemini check blocked: {response.prompt_feedback}")
                return "Error: Content blocked by safety filters."
        except Exception as e:
            logger.error(f"Google Gemini query failed: {e}")
            raise
    def get_available_models(self) -> List[str]:
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
