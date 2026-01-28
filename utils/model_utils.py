"""
Utility functions for model management and filtering.
"""


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


def is_reasoning_model(model_name: str) -> bool:
    """Checks if a model is a reasoning model (CoT)."""
    name_lower = model_name.lower()
    return "deepseek-r1" in name_lower or "reasoning" in name_lower


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


def resolve_provider(model_name: str) -> tuple[str, str]:
    """Ermittelt Provider basierend auf Modell-Präfix."""
    name_lower = model_name.lower()
    if name_lower.startswith(("mistral-", "open-mixtral", "ministral")):
        return "mistral", model_name
    if name_lower.startswith(("gpt-", "o1-")):
        return "openai", model_name
    if name_lower.startswith("claude-"):
        return "anthropic", model_name
    # Default to local
    return "ollama", model_name


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
