"""
Model fingerprinting utilities for commercial API models.

Provides version tracking and change detection for models that don't
expose native hash IDs (Mistral AI, OpenAI, Anthropic).
"""

import hashlib
import logging
import re
import subprocess
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
    def get_unified_version(
            provider: str,
            model_name: str,
            client=None
    ) -> str:
        """
        Global SSOT for Model Versioning (Local & Commercial).

        Strict Format: {OFFICIAL_ID}-{BEHAVIORAL_HASH}

        - OFFICIAL_ID:
             commercial -> Date-based snapshot (e.g. 2024-05-13)
             local      -> Ollama Digest Short-Hash (e.g. 8f4d1a) or 'local'
        - BEHAVIORAL_HASH:
             8-char hex derived from deterministic prompts (e.g. 8717af19)

        Returns:
             "2024-05-13-8717af19" or "8f4d1a-8717af19"
        """
        # 1. Determine Official Identifier
        official_id = "unknown"

        if provider in ["ollama", "local"]:
            # Try to fetch Ollama digest
            official_id = ModelFingerprinter._get_ollama_digest(model_name)
        else:
            # Commercial provider lookup
            official_id = get_official_version(provider, model_name)

        if not official_id:
            official_id = "v0"  # Placeholder if totally unknown

        # 2. Generate Behavioral Hash (ALWAYS, if possible)
        # Assuming client is passed. If not, we skip hash (return 'nohash')
        behavioral_hash = "nohash"

        if client:
            try:
                # Cache checking could happen here if 'client' had a cache registry,
                # but simplistic approach is robust: check if client has cached it internally.
                if hasattr(client, "fingerprint_cache") and model_name in client.fingerprint_cache:
                    return client.fingerprint_cache[model_name]

                behavioral_hash = ModelFingerprinter.generate_behavioral_hash(
                    client, model_name
                )
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning("Could not generate behavioral hash: %s", e)

        # 3. Combine Logic (Hybrid Approach)
        
        # Case A: Local/Ollama Models
        # Strategy: Use the official Digest/Hash only.
        # Rationale: Local models verify via hash (like git/docker). 
        # Adding "-nohash" or behavioral hashes is redundant and confusing for users.
        if provider in ["ollama", "local"]:
             if official_id not in ["unknown", "local", "v0"] and official_id:
                  final_version = official_id
             else:
                  # Fallback if we couldn't get a proper digest
                  final_version = f"local-{behavioral_hash}" if behavioral_hash != "nohash" else "local"

        # Case B: Commercial Models (Date already in name)
        # Strategy: Use Behavioral Hash only to avoid redundancy.
        # Example: "claude-20241022" -> version "8717af19" (Cleaner than "20241022-8717af19")
        elif (official_id in model_name and 
              behavioral_hash != "nohash" and 
              provider not in ["ollama", "local"]):
             final_version = behavioral_hash

        # Case C: Standard Commercial (Date + Behavioral Hash)
        # Example: "gpt-4o" -> "2024-05-13-8717af19"
        else:
             final_version = f"{official_id}-{behavioral_hash}"

        # Cache back if possible
        if client and hasattr(client, "fingerprint_cache"):
            client.fingerprint_cache[model_name] = final_version

        return final_version

    @staticmethod
    def _get_ollama_digest(model_name: str) -> str:
        """Helper to get short digest from Ollama CLI."""
        try:
            # Run 'ollama list' gives digests properly
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # Parse table: NAME ID SIZE MODIFIED
                # skip header
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 2:
                        m_name = parts[0]
                        m_id = parts[1]
                        if m_name == model_name or m_name.startswith(model_name + ":"):
                            return m_id[:12]  # Short ID
            return "local"
        except Exception:  # pylint: disable=broad-exception-caught
            return "local"

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
        # pylint: disable=unused-argument
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

            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning("Fingerprinting probe failed: %s", e)
                responses.append("")

                # Try fallback call style if repeated error handled logic existed
                # Simplified for linting cleanliness

        # Combine all responses and hash
        combined = "|".join(responses)
        hash_full = hashlib.sha256(combined.encode()).hexdigest()

        return hash_full[:8]

    @staticmethod
    def create_fingerprint(
            provider: str,  # pylint: disable=unused-argument
            model_name: str,  # pylint: disable=unused-argument
            official_version: Optional[str] = None,
            behavioral_hash: Optional[str] = None
    ) -> str:
        """
        DEPRECATED: Use get_unified_version() instead.
        Legacy wrapper to maintain compatibility during refactor.
        """
        # If we have both, construct the V2 format manually
        if official_version and behavioral_hash:
            return f"{official_version}-{behavioral_hash}"

        # Otherwise fallback to new system logic
        parts = []
        if official_version:
            parts.append(official_version)
        if behavioral_hash:
            parts.append(behavioral_hash)
        if not parts:
            return "unknown"

        return "-".join(parts)


# Official snapshot ID mappings (Only for generic aliases that mask the real date)
OFFICIAL_SNAPSHOTS = {
    "mistral": {
        "mistral-large-latest": "2411",
        "mistral-medium-latest": "2312",
        "mistral-small-latest": "2402",
        "open-mistral-7b": "v0.3",
        "ministral-3b-latest": "2410",
        "ministral-8b-latest": "2410"
    },
    "openai": {
        "gpt-4-turbo": "2024-04-09",
        "gpt-4o": "2024-05-13",
        "gpt-4o-mini": "2024-07-18",
        "gpt-3.5-turbo": "0125",
        "o3-mini": "2026-01-30"
    },
    "anthropic": {
        "claude-3-5-sonnet-latest": "20241022",
        "claude-3-5-sonnet-20241022": "20241022",
        "claude-3-opus-20240229": "20240229",
        "claude-3-haiku-20240307": "20240307"
    }
}


def get_official_version(provider: str, model_name: str) -> Optional[str]:
    """
    Get official identifiers for a model.
    Prioritizes:
    1. Hardcoded mapping (for generic aliases like 'latest')
    2. Regex extraction of date-strings from model name (e.g. '...-20250929')
    3. Cleaned model name as fallback
    """
    # 1. Hardcoded Lookup (for aliases)
    provider_snapshots = OFFICIAL_SNAPSHOTS.get(provider, {})
    if model_name in provider_snapshots:
        return provider_snapshots[model_name]

    # 2. Dynamic Regex Extraction (YYYYMMDD or YYYY-MM-DD)
    # Matches: 20240229, 2025-09-29, 2411 (Mistral style YYMM)

    # Look for YYYYMMDD or YYYY-MM-DD at the end or preceded by separator
    date_match = re.search(r'(?:^|[-_])(\d{4}[-_]?\d{2}[-_]?\d{2})(?:$|[-_])', model_name)
    if date_match:
        # User preference: Keep original format found in name (e.g. 2024-04-09 or 20241022)
        # ensuring consistency with OFFICIAL_SNAPSHOTS style for that provider.
        return date_match.group(1)

    # Look for Mistral-style YYMM (e.g. 2411) at end of string
    mistral_match = re.search(r'(?:^|[-_])(\d{4})(?:$)', model_name)
    if mistral_match:
        return mistral_match.group(1)

    # 3. Fallback: Use Model Name (sanitized) to ensure we always have a base
    # This prevents "unknown-hash" and keeps differentiation for new models
    # e.g. "my-custom-finetune" -> "my-custom-finetune"
    return model_name.replace(":", "-").split("/")[-1]
