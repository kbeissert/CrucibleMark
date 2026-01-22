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
    if 'embed' in name_lower:
        return False
    if '-vl' in name_lower:
        return False
    if 'vision' in name_lower:
        return False

    # Add more exclusion criteria here if needed in the future

    return True


def is_reasoning_model(model_name: str) -> bool:
    """
    Checks if the model is a reasoning model (Chain-of-Thought).
    These models often require higher token limits or specific handling.

    Args:
        model_name: Name of the model

    Returns:
        bool: True if it is a reasoning model
    """
    triggers = ['deepseek-r1', 'reasoning', 'phi4', 'qwq', 'o1', 'o3']
    return any(t in model_name.lower() for t in triggers)
