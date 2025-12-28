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
