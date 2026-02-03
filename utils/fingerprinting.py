"""
Model fingerprinting utilities for commercial API models.

Provides version tracking and change detection for models that don't
expose native hash IDs (Mistral AI, OpenAI, Anthropic).
"""

import hashlib
import logging
from datetime import datetime
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

class ModelFingerprinter:
    """
    Generate and validate fingerprints for commercial API models.

    Combines official snapshot IDs with behavioral testing to create
    unique, reproducible model identifiers.
    """

    # Deterministic calibration prompts for behavioral fingerprinting
    CALIBRATION_PROMPTS = [
        {
            "prompt": "Calculate: 17 * 3. Answer with number only.",
            "expected_format": "number",
            "temperature": 0.0
        },
        {
            "prompt": "What is the capital of France? Answer in one word.",
            "expected_format": "single_word",
            "temperature": 0.0
        },
        {
            "prompt": "First 5 letters of English alphabet. No formatting.",
            "expected_format": "text",
            "temperature": 0.0
        }
    ]

    @staticmethod
    def generate_behavioral_hash(
        client,
        model_name: str,
        temperature: float = 0.0,
        max_retries: int = 2
    ) -> str:
        """
        Generate behavioral fingerprint using deterministic prompts.

        Args:
            client: API client instance (MistralClient, OpenAIClient, etc.)
            model_name: Name of the model to fingerprint.
            temperature: Must be 0.0 for deterministic responses
            max_retries: Retry attempts if API fails

        Returns:
            8-character hex hash of combined responses
        """
        responses = []
        
        # Check available method
        query_method = None
        if hasattr(client, "query"):
            query_method = client.query
        elif hasattr(client, "generate"): 
             query_method = client.generate
        
        if not query_method:
             logger.warning("Client has no query/generate method for fingerprinting")
             return "nohash"

        for test in ModelFingerprinter.CALIBRATION_PROMPTS:
            try:
                # Call client.query(model=model_name, ...)
                if query_method == client.query:
                    response_text = query_method(
                        model=model_name,
                        prompt=test["prompt"],
                        temperature=test["temperature"],
                        max_tokens=20,
                        skip_fingerprint=True  # Prevent recursion
                    )
                else:
                    response_text = query_method(
                        prompt=test["prompt"],
                        temperature=test["temperature"],
                        max_tokens=20 
                    )
                responses.append(response_text.strip().lower())

            except Exception as e:
                logger.warning(f"Fingerprinting probe failed: {e}")
                responses.append("")
                
                if hasattr(client, "model_name") and client.model_name:
                    response_text = query_method(
                        model=client.model_name,
                        prompt=test["prompt"],
                        temperature=test["temperature"],
                        max_tokens=20 
                    )
                    responses.append(response_text.strip().lower())
                else:
                    # Fallback or error
                    responses.append("")

            except Exception as e:
                logger.warning(f"Fingerprinting probe failed: {e}")
                responses.append("")

        # Combine all responses and hash
        combined = "|".join(responses)
        hash_full = hashlib.sha256(combined.encode()).hexdigest()

        return hash_full[:8]

    @staticmethod
    def create_fingerprint(
        provider: str,
        model_name: str,
        official_version: Optional[str] = None,
        behavioral_hash: Optional[str] = None
    ) -> str:
        """
        Create full model fingerprint.

        Format: {provider}-{model_name}-{version}-{behavioral_hash}-{date}
        """
        date_str = datetime.now().strftime("%Y-%m-%d")

        # Normalize model name for fingerprint (remove special chars)
        safe_model = model_name.replace(":", "").replace("/", "").lower()
        
        parts = []
        # We do not prepend provider if the model name already likely contains it or is unique enough
        # But guide says: {provider}-{model_name}...
        
        # If provider is mistral, and model is mistral-large, we get mistral-mistral-large.
        # Let's deduplicate if needed, or just follow guide strictly.
        # Guide: mistral-large-2411... 
        # Code: parts = [provider, model_name] matches valid outputs like mistral-large...
        
        parts.append(provider)
        parts.append(safe_model)

        if official_version:
            parts.append(official_version)
        else:
            parts.append("unknown")

        if behavioral_hash:
            parts.append(behavioral_hash)

        # Remove date from fingerprint to ensure stable versioning across days
        # The timestamp column in results handles the timeline.
        # parts.append(date_str)

        return "-".join(parts)


# Official snapshot ID mappings
OFFICIAL_SNAPSHOTS = {
    "mistral": {
        "mistral-large-latest": "2411",
        "mistral-large-2411": "2411",
        "mistral-medium-latest": "2312",
        "mistral-medium-2312": "2312",
        "mistral-small-latest": "2402",
        "open-mistral-7b": "v0.3",
        "ministral-3b-latest": "2410",
        "ministral-8b-latest": "2410"
    },
    "openai": {
        "gpt-4-turbo": "2024-04-09",
        "gpt-4-turbo-2024-04-09": "2024-04-09",
        "gpt-4o": "2024-05-13",
        "gpt-4o-mini": "2024-07-18",
        "gpt-3.5-turbo": "0125"
    },
    "anthropic": {
        "claude-3-opus-20240229": "20240229",
        "claude-3-5-sonnet-20241022": "20241022",
        "claude-3-5-sonnet-latest": "20241022",
        "claude-3-haiku-20240307": "20240307"
    }
}


def get_official_version(provider: str, model_name: str) -> Optional[str]:
    """Get official snapshot ID for a model."""
    provider_snapshots = OFFICIAL_SNAPSHOTS.get(provider, {})
    return provider_snapshots.get(model_name)
