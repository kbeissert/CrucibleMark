import logging
from utils.llm_client import LLMClient

class UXMockLLMService:
    """Mock service providing realistic UX Writing responses."""

    def query(self, prompt: str) -> str:
        # Check prompts to return relevant mock data
        if "Fehlermeldungen" in prompt:
            return """
| Original | Verbesserung | Begründung |
|---|---|---|
| Error 500 | Ups, da ist etwas schiefgelaufen. | Freundlicher Ton. |
| Invalid input | Bitte überprüfen Sie Ihre Eingabe. | Handlungsanweisung. |

Step 1: Klicken Sie auf Reset.
Step 2: Versuchen Sie es erneut.
"""
        if "Button" in prompt:
            return "Button: 'Jetzt kaufen' (12 Zeichen)"

        return "Generic UX writing response with some **markdown** and clear instructions."

class UXLLMService:
    """
    Handles LLM communication for UX Writing benchmark.
    """
    def __init__(self, model_name: str, provider: str = "ollama"):
        self.model_name = model_name
        self.provider = provider
        self.client = LLMClient() # Assuming this exists in utils
        self.logger = logging.getLogger(__name__)

    def query(self, prompt: str) -> str:
        """Sends the prompt to the configured LLM."""
        if self.model_name == "mock":
            return UXMockLLMService().query(prompt)

        try:
            # Reusing the generic client from utils
            # Note: Adapting to whatever interface LLMClient has.
            # Assuming query(prompt, model, provider, ...)
            response = self.client.query(
                prompt=prompt,
                model=self.model_name,
                provider=self.provider,
                temperature=0.3 # Low temp for consistency in writing tasks
            )
            return response
        except Exception as e:
            self.logger.error(f"LLM Query failed: {e}")
            return f"Error: {str(e)}"
