"""
Provider-spezifische LLM Clients
Getrennte Implementierungen für Ollama, Anthropic, Mistral
"""

import os
import logging
from typing import Dict, Any, List, Optional

from utils.ollama_config import BENCHMARK_OPTIONS

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TEMPERATURE = 0.3
MAX_TOKENS_ANTHROPIC = 4000
DEFAULT_MISTRAL_MODEL = 'mistral-large-latest'

class BaseProviderClient:
    """Basis-Klasse für Provider-spezifische Clients"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def query(self, model: str, prompt: str, temperature: float) -> str:
        """
        Query API
        
        Args:
            model: Modell-Name
            prompt: Prompt-Text
            temperature: Temperature
            
        Returns:
            Response-Text
        """
        raise NotImplementedError
    
    def get_available_models(self) -> List[str]:
        """Listet verfügbare Modelle"""
        raise NotImplementedError

class OllamaClient(BaseProviderClient):
    """Ollama Provider Client"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._client = None
    
    @property
    def client(self):
        """Lazy-loaded Ollama Client"""
        if self._client is None:
            import ollama
            self._client = ollama
        return self._client
    
    def query(self, model: str, prompt: str, temperature: float) -> str:
        """Query Ollama API"""
        try:
            response = self.client.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}],
                options=BENCHMARK_OPTIONS  # Zentrale Config mit temperature=0.1
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"Ollama query failed: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
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
            logger.error(f"Error listing Ollama models: {e}")
            return []

class AnthropicClient(BaseProviderClient):
    """Anthropic Claude Provider Client"""
    
    def __init__(self, config: Dict[str, Any]):
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
            logger.error(f"Anthropic query failed: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Listet verfügbare Claude-Modelle"""
        return [
            'claude-3-5-sonnet-20241022',
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229'
        ]

class MistralClient(BaseProviderClient):
    """Mistral AI Provider Client"""
    
    def __init__(self, config: Dict[str, Any]):
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
                temperature=temperature
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Mistral query failed: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Listet verfügbare Mistral-Modelle"""
        return [
            'mistral-large-latest',
            'mistral-medium-latest',
            'mistral-small-latest',
            'open-mistral-7b'
        ]
