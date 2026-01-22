"""
Provider-spezifische LLM Clients
Getrennte Implementierungen für Ollama, Anthropic, Mistral
"""

import os
import logging
from typing import Any

from utils.ollama_config import CODING_BENCHMARK_OPTIONS, CREATIVE_BENCHMARK_OPTIONS

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TEMPERATURE = 0.3
MAX_TOKENS_ANTHROPIC = 4000
DEFAULT_MISTRAL_MODEL = 'mistral-large-latest'


class BaseProviderClient:
    """Basis-Klasse für Provider-spezifische Clients"""

    def __init__(self, config: dict[str, Any]):
        self.config = config

    def query(self, model: str, prompt: str, temperature: float, stream_handler=None) -> str:
        """
        Query API

        Args:
            model: Modell-Name
            prompt: Prompt-Text
            temperature: Temperature
            stream_handler: Optional callback for streaming output chunks

        Returns:
            Response-Text
        """
        raise NotImplementedError

    def get_available_models(self) -> list[str]:
        """Listet verfügbare Modelle"""
        raise NotImplementedError


class OllamaClient(BaseProviderClient):
    """Ollama Provider Client"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._client = None

    @property
    def client(self):
        """Lazy-loaded Ollama Client"""
        if self._client is None:
            import ollama
            self._client = ollama
        return self._client

    def query(self, model: str, prompt: str, temperature: float, stream_handler=None) -> str:
        """Query Ollama API"""
        try:
            # Select options based on temperature
            # If temp >= 0.3, use creative options (better for UX/Writing)
            # If temp < 0.3, use coding options (better for Logic/Code)
            if temperature >= 0.3:
                options = CREATIVE_BENCHMARK_OPTIONS.copy()
            else:
                options = CODING_BENCHMARK_OPTIONS.copy()

            # Ensure the requested temperature is actually used
            options['temperature'] = temperature

            # SPECIAL HANDLING for Reasoning Models (e.g. DeepSeek-R1)
            # These models generate thousands of "thinking" tokens before the actual answer.
            # We explicitly boost the token limit prevents premature cutoff.
            is_reasoning = 'deepseek-r1' in model or 'reasoning' in model or 'qwen3' in model
            if is_reasoning:
                options['num_predict'] = 32768  # 32k tokens allow for extensive reasoning chains
                logger.debug(f"Boosting token limit for reasoning model '{model}' to 32768")

            # Handle Streaming
            if stream_handler:
                response = self.client.chat(
                    model=model,
                    messages=[{'role': 'user', 'content': prompt}],
                    options=options,
                    stream=True
                )
                full_content = ""
                full_thinking = ""
                
                for chunk in response:
                    val_content = chunk['message'].get('content', '')
                    val_thinking = ""
                    
                    # Try to extract thinking if provided separately (Ollama experimental)
                    if hasattr(chunk['message'], 'thinking'):
                         val_thinking = chunk['message'].thinking
                    elif isinstance(chunk['message'], dict):
                         val_thinking = chunk['message'].get('thinking', '')

                    if val_thinking:
                        # Visualize thinking if stream handler supports it (or just dump it)
                        stream_handler(val_thinking) # Just treat as text for now
                        full_thinking += val_thinking
                    
                    if val_content:
                        stream_handler(val_content)
                        full_content += val_content
                
                # Reconstruct return value (ignoring distinct thinking for return, just content)
                # Unless we want to return thinking? The caller expects content.
                return full_content

            # Standard Blocking Call
            response = self.client.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}],
                options=options
            )

            content = response['message']['content']
            
            # Special handling for reasoning models (e.g. DeepSeek-R1)
            # that separate 'thinking' from content
            thinking = ""
            if 'message' in response and hasattr(response['message'], 'get'):
                 # Dictionary access if it's a dict
                 thinking = response['message'].get('thinking', '')
            elif hasattr(response['message'], 'thinking'):
                 # Attribute access if it's an object (ollama-python 0.6+ might return objects)
                 thinking = response['message'].thinking

            if not content:
                done_reason = response.get('done_reason')
                
                if done_reason == 'length':
                    # Log as debug to avoid cluttering the terminal progress bars
                    logger.debug(f"Ollama generation stopped due to token limit. (num_predict={options.get('num_predict')})")
                    if thinking:
                         logger.debug("Returning partial 'thinking' content as fallback.")
                         return thinking
                    raise ValueError("Empty response from Ollama (Token limit reached)")
                
                if thinking:
                    logger.debug("Received 'thinking' but no 'content'. Using thinking as fallback.")
                    return thinking
                    
                logger.error(f"Empty content received. Full response: {response}")
                raise ValueError("Received empty response from Ollama")

            return content
        except Exception as e:
            logger.error("Ollama query failed: %s", e)
            raise

    def get_available_models(self) -> list[str]:
        """Listet verfügbare Ollama-Modelle"""
        try:
            response = self.client.list()
            # Handle both object and dict response formats
            models = response.models if hasattr(response, 'models') else response.get('models', [])
            return [
                model.model if hasattr(model, 'model') else model.get('name', 'unknown')
                for model in models
            ]
        except Exception as e:
            logger.error("Error listing Ollama models: %s", e)
            return []


class AnthropicClient(BaseProviderClient):
    """Anthropic Claude Provider Client"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._client = None

    @property
    def client(self):
        """Lazy-loaded Anthropic Client"""
        if self._client is None:
            import anthropic
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def _resolve_model(self, model: str) -> str:
        """Löst Modell-Name auf (Config-Fallback)"""
        if not model or model.startswith('claude'):
            return self.config.get('anthropic', {}).get('model', 'claude-3-5-sonnet-20241022')
        return model

    def query(self, model: str, prompt: str, temperature: float) -> str:
        """Query Anthropic API"""
        try:
            model = self._resolve_model(model)
            max_tokens = self.config.get('anthropic', {}).get('max_tokens', MAX_TOKENS_ANTHROPIC)

            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text
        except Exception as e:
            logger.error("Anthropic query failed: %s", e)
            raise

    def get_available_models(self) -> list[str]:
        """Listet verfügbare Claude-Modelle"""
        return [
            'claude-3-5-sonnet-20241022',
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229'
        ]


class MistralClient(BaseProviderClient):
    """Mistral AI Provider Client"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._client = None

    @property
    def client(self):
        """Lazy-loaded Mistral Client"""
        if self._client is None:
            from mistralai import Mistral
            # Support both MISTRAL_API_KEY and CODESTRAL_API_KEY
            api_key = os.environ.get('MISTRAL_API_KEY') or os.environ.get('CODESTRAL_API_KEY')
            if not api_key:
                raise ValueError("MISTRAL_API_KEY or CODESTRAL_API_KEY environment variable not set")
            self._client = Mistral(api_key=api_key)
        return self._client

    def _resolve_model(self, model: str) -> str:
        """Löst Modell-Name auf (Config-Fallback)"""
        if not model or model.startswith('mistral'):
            return self.config.get('mistral', {}).get('model', DEFAULT_MISTRAL_MODEL)
        return model

    def query(self, model: str, prompt: str, temperature: float) -> str:
        """Query Mistral API"""
        try:
            model = self._resolve_model(model)

            response = self.client.chat.complete(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                random_seed=42  # Ensure deterministic output
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error("Mistral query failed: %s", e)
            raise

    def get_available_models(self) -> list[str]:
        """Listet verfügbare Mistral-Modelle"""
        return [
            'mistral-large-latest',
            'mistral-medium-latest',
            'mistral-small-latest',

            'open-mistral-7b'
        ]


class OpenAIClient(BaseProviderClient):
    """OpenAI Provider Client"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._client = None

    @property
    def client(self):
        """Lazy-loaded OpenAI Client"""
        if self._client is None:
            from openai import OpenAI
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self._client = OpenAI(api_key=api_key)
        return self._client

    def query(self, model: str, prompt: str, temperature: float) -> str:
        """Query OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("OpenAI query failed: %s", e)
            raise

    def get_available_models(self) -> list[str]:
        """Listet verfügbare OpenAI-Modelle"""
        return [
            'gpt-4o',
            'gpt-4o-mini',
            'gpt-4-turbo',
            'gpt-3.5-turbo',
            'o1-mini',
            'o1-preview'
        ]
