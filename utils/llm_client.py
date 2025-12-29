"""
LLM Client Wrapper
Unified Interface für Ollama und Anthropic Claude API
"""

import logging
import yaml
from pathlib import Path
from typing import Any

from utils.provider_clients import OllamaClient, AnthropicClient, MistralClient
from utils.retry_handler import RetryHandler

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_RETRIES = 3
TOKEN_ESTIMATE_RATIO = 4

class LLMClient:
    """
    Universal LLM Client für Ollama, Anthropic und Mistral
    
    Features:
    - Unified Interface für alle Provider
    - Automatisches Fallback bei Fehlern
    - Token-Counting (approximiert)
    - Retry-Logik mit Exponential Backoff
    - Delegation an provider-spezifische Clients
    """
    
    def __init__(self, config_path: str | None = None):
        """
        Initialisiert LLM Client
        
        Args:
            config_path: Pfad zur Config-Datei (optional, für Legacy-Support)
        """
        self.config: dict[str, Any] = {}
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, encoding='utf-8') as f:
                    self.config = yaml.safe_load(f) or {}
            except Exception as e:
                logger.error("Failed to load config from %s: %s", config_path, e)
        
        # Initialize provider clients
        self.clients = {
            'ollama': OllamaClient(self.config),
            'anthropic': AnthropicClient(self.config),
            'mistral': MistralClient(self.config)
        }
        
        # Initialize retry handler
        self.retry_handler = RetryHandler(max_retries=DEFAULT_MAX_RETRIES)
    
    def query(
        self, 
        model: str, 
        prompt: str, 
        provider: str = 'ollama',
        temperature: float | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES
    ) -> str:
        """
        Universelle Query-Methode mit Delegation an Provider-Clients
        
        Args:
            model: Modell-Name
            prompt: Prompt-Text
            provider: 'ollama', 'anthropic' oder 'mistral'
            temperature: Temperature (optional, nutzt Config-Default)
            max_retries: Maximum Anzahl Retry-Versuche
            
        Returns:
            Response-Text
            
        Raises:
            ValueError: Bei unbekanntem Provider
            Exception: Bei fehlgeschlagener Query nach Retries
        """
        if provider not in self.clients:
            valid_providers = list(self.clients.keys())
            logger.error("Unknown provider: %s. Available: %s", provider, valid_providers)
            raise ValueError(f"Unknown provider: {provider}. Available: {valid_providers}")
        
        if temperature is None:
            temperature = self.config.get('ollama', {}).get('default_temperature', DEFAULT_TEMPERATURE)
        
        # Update retry handler with custom max_retries
        self.retry_handler.max_retries = max_retries
        
        logger.info("Querying %s model '%s' (temp=%s)", provider, model, temperature)
        
        # Delegate to provider-specific client with retry logic
        return self.retry_handler.execute_with_retry(
            lambda: self.clients[provider].query(model, prompt, temperature)
        )
    
    def estimate_tokens(self, text: str) -> int:
        """
        Approximiert Token-Count
        
        Args:
            text: Text
            
        Returns:
            Geschätzte Anzahl Tokens (grobe Schätzung: 1 Token ≈ 4 Zeichen)
        """
        if not text:
            return 0
        return len(text) // TOKEN_ESTIMATE_RATIO
    
    def get_available_models(self, provider: str = 'ollama') -> list[str]:
        """
        Listet verfügbare Modelle
        
        Args:
            provider: 'ollama', 'anthropic' oder 'mistral'
            
        Returns:
            Liste von Modell-Namen
        """
        if provider in self.clients:
            try:
                return self.clients[provider].get_available_models()
            except Exception as e:
                logger.error("Failed to get models for %s: %s", provider, e)
                return []
        return []

