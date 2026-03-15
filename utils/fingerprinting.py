"""
Model fingerprinting utilities for API models.
"""

import logging
import re
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

OFFICIAL_SNAPSHOTS = {
    "mistral": {
        "mistral-large-latest": "2411",
        "mistral-medium-latest": "2312",
        "mistral-small-latest": "2402",
        "open-mistral-7b": "v0.3",
        "ministral-3b-latest": "2410",
        "ministral-8b-latest": "2410",
    },
    "openai": {
        "gpt-4-turbo": "2024-04-09",
        "gpt-4o": "2024-05-13",
        "gpt-4o-mini": "2024-07-18",
        "gpt-3.5-turbo": "0125",
        "o3-mini": "2026-01-30",
    },
    "anthropic": {
        "claude-3-5-sonnet-latest": "20241022",
        "claude-3-5-sonnet-20241022": "20241022",
        "claude-3-opus-latest": "20240229",
        "claude-3-haiku-20240307": "20240307",
        "claude-sonnet-4-6": "4.6",
        "claude-opus-4-6": "4.6",
        "claude-opus-4-5-20251101": "20251101",
        "claude-sonnet-4-5-20250929": "20250929",
        "claude-haiku-4-5-20251001": "20251001"
    },
    "google": {
        "gemini-2.5-pro": "k.A.",
        "gemini-3.1-pro-preview": "k.A."
    },
    "xai": {
        "grok-3-latest": "k.A.",
        "grok-4-latest": "k.A."
    }
}

def get_official_version(provider: str, model_name: str) -> str:
    provider_snapshots = OFFICIAL_SNAPSHOTS.get(provider, {})
    if model_name in provider_snapshots:
        return provider_snapshots[model_name]

    date_match = re.search(
        r"(?:^|[-_])(\d{4}[-_]?\d{2}[-_]?\d{2})(?:$|[-_])", model_name
    )
    if date_match:
        return date_match.group(1)

    mistral_match = re.search(r"(?:^|[-_])(\d{4})(?:$)", model_name)
    if mistral_match:
        return mistral_match.group(1)

    return "k.A."

class ModelFingerprinter:
    @staticmethod
    def get_unified_version(provider: str, model_name: str, client=None) -> str:
        if provider in ["ollama", "local"]:
            official_id = ModelFingerprinter._get_ollama_digest(model_name)
            return official_id if official_id and official_id != "local" else "k.A."
        
        return get_official_version(provider, model_name)

    @staticmethod
    def _get_ollama_digest(model_name: str) -> str:
        try:
            result = subprocess.run(
                ["ollama", "list"], capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 2:
                        m_name = parts[0]
                        m_id = parts[1]
                        if m_name == model_name or m_name.startswith(model_name + ":"):
                            return m_id[:12]
            return "local"
        except Exception:
            return "local"

    @staticmethod
    def create_fingerprint(
        provider: str,
        model_name: str,
        official_version: Optional[str] = None,
        behavioral_hash: Optional[str] = None,
    ) -> str:
        return official_version or "k.A."
