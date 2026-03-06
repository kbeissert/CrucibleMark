"""
Utility functions for model management and filtering.
"""

import shutil
import subprocess
from typing import Dict

# Late import to avoid circular dependencies if any (though currently safe)
try:
    from utils.fingerprinting import ModelFingerprinter
except ImportError:
    # Fallback if utils package structure is not ready
    ModelFingerprinter = None


def get_model_version(model_name: str, provider: str = "ollama", client=None) -> str:
    """
    Retrieves the unique version/digest of a model.
    SSOT (Single Source of Truth) via ModelFingerprinter.
    
    Args:
        model_name: Name of the model
        provider: Provider name
        client: Optional LLMClient for behavioral hashing

    Returns:
        str: Unified version string (e.g. '2411-nohash' or '8f3d1a-nohash')
    """
    if ModelFingerprinter:
        return ModelFingerprinter.get_unified_version(provider, model_name, client=client)
        
    return "unknown"


def get_ollama_model_info(model_name: str) -> Dict[str, str]:
    """Holt Details (ID/Digest) zu einem bestimmten Ollama-Modell via CLI."""
    try:
        ollama_path = shutil.which("ollama")
        if not ollama_path:
            return {}

        # 'ollama list' ist effizienter als 'ollama show' für die ID
        result = subprocess.run(
            [ollama_path, "list"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        
        for line in result.stdout.strip().split("\n")[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[0] == model_name:
                return {"id": parts[1], "size": parts[2]}
                
        return {}

    except Exception:
        return {}


def is_model_suitable_for_benchmark(model_name: str) -> bool:
    """
    Determines if a model is suitable for text generation benchmarks.
    Filters out embedding models and other non-generative models.

    Args:
        model_name: Name of the model (e.g., 'nomic-embed-text:latest', 'llama3:8b')

    Returns:
        bool: True if model is suitable, False otherwise.
    """
    name_lower = model_name.lower()

    # Filter criteria
    if "embed" in name_lower:
        return False
    if "-vl" in name_lower:
        return False
    if "vision" in name_lower:
        return False

    # Add more exclusion criteria here if needed in the future

    return True


def get_ollama_models_info() -> list[dict]:
    """Holt und normalisiert Ollama-Modelle."""
    try:
        import ollama

        # Handle simplified response type if necessary or generic object access
        response = ollama.list()
        models = (
            response.models if hasattr(response, "models") else response.get("models", [])
        )
        
        results = []
        for m in models:
            # Access attributes safely (pydantic model vs dict)
            name = m.model if hasattr(m, "model") else m.get("name", "")
            if not is_model_suitable_for_benchmark(name):
                continue
                
            size = m.size if hasattr(m, "size") else m.get("size", 0)
            modified = m.modified_at if hasattr(m, "modified_at") else m.get("modified_at", "N/A")
            
            # Simple normalization
            modified_str = str(modified)[:10] if modified != "N/A" else "N/A"
            size_gb = (size or 0) / (1024**3)
            
            results.append({
                "name": name,
                "size_gb": size_gb,
                "modified": modified_str,
                "original": m # keep object if needed
            })
        
        return sorted(results, key=lambda x: x["name"])
            
    except (ImportError, Exception):
        return []


def get_commercial_models_from_config(config: Dict) -> list[tuple[str, str, str]]:
    """
    Extracts enabled commercial models from the configuration dictionary.
    
    Args:
        config (Dict): The loaded benchmark_config.yaml content.

    Returns:
        List[Tuple[str, str, str]]: List of (model_id, pretty_name, provider_key)
    """
    models = []
    providers = config.get("providers", {}).get("commercial", {})
    
    for p_key, p_config in providers.items():
        if p_config.get("enabled", False):
            for m in p_config.get("models", []):
                # model_id, name, provider
                models.append((m["id"], m["name"], p_key))
    
    return models


def resolve_provider(model_name: str) -> tuple[str, str]:
    """Ermittelt Provider basierend auf Modell-Präfix."""
    
    # Determine if likely Ollama (contains tag separator)
    if ":" in model_name:
        return "ollama", model_name

    name_lower = model_name.lower()
    if name_lower.startswith(("mistral-", "open-mixtral", "ministral")):
        return "mistral", model_name
    if name_lower.startswith(("gpt-", "o1-")):
        return "openai", model_name
    if name_lower.startswith("claude-"):
        return "anthropic", model_name
    # Default to local
    return "ollama", model_name


def is_cloud_model(model_name: str, size_gb: float = None) -> bool:
    """
    SSOT: Determines if an Ollama model is a cloud proxy model.
    
    This is the canonical definition used across the entire codebase:
    - UI filtering (run_benchmark.py)
    - Data loading (data_loader.py)
    - Model categorization (get_model_category)
    
    Args:
        model_name: Name of the model (e.g., 'minimax-m2:cloud')
        size_gb: Optional model size in GB (if available)
    
    Returns:
        bool: True if model is a cloud proxy model
    
    Detection Rules:
        1. Model name contains ':cloud' tag (e.g., 'minimax-m2:cloud')
        2. Model name ends with '-cloud' suffix (e.g., 'gpt-oss:120b-cloud')
        3. Model size is extremely small (< 0.01 GB = proxy, not locally stored)
    """
    model_lower = model_name.lower()
    
    # Rule 1 & 2: Name-based detection
    if ":cloud" in model_lower or model_lower.endswith("-cloud"):
        return True
    
    # Rule 3: Size-based heuristic (proxy models have minimal/no local storage)
    if size_gb is not None and size_gb < 0.01:
        return True
    
    return False


def get_model_category(model_name: str, source_file: str = "local", size_gb: float = None) -> str:
    """
    Central SSOT for model categorization.
    Determines whether a model is Commercial, Local, or Local Cloud.
    
    Args:
        model_name: Name of the model (e.g., 'ministral-3:14b', 'gpt-oss:120b-cloud')
        source_file: Source CSV file ('local' or 'commercial')
        size_gb: Optional model size in GB (for better cloud detection)
    
    Returns:
        str: 'Commercial', 'Local', or 'Local Cloud'
    
    Examples:
        >>> get_model_category('ministral-3:14b', 'local')
        'Local'
        >>> get_model_category('minimax-m2:cloud', 'local')
        'Local Cloud'
        >>> get_model_category('gpt-oss:120b-cloud', 'local')
        'Local Cloud'
        >>> get_model_category('claude-sonnet-4', 'commercial')
        'Commercial'
    """
    # Rule 1: Commercial CSV → Always Commercial
    if source_file == "commercial":
        return "Commercial"
    
    # Rule 2: Local CSV → Check if it's a cloud proxy using canonical logic
    if is_cloud_model(model_name, size_gb):
        return "Local Cloud"
    
    # Rule 3: Everything else from Local CSV → Local
    return "Local"


def is_reasoning_model(model_name: str) -> bool:
    """
    Checks if the model is a reasoning model (Chain-of-Thought).
    These models often require higher token limits or specific handling.

    Args:
        model_name: Name of the model

    Returns:
        bool: True if it is a reasoning model
    """
    triggers = ["deepseek-r1", "reasoning", "phi4", "qwq", "o1", "o3"]
    return any(t in model_name.lower() for t in triggers)
