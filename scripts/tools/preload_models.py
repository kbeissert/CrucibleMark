#!/usr/bin/env python3
"""
Preload AI Models
=================
Downloads the 'sentence-transformers' model to the local cache.
Used during installation to ensure offline capability.
"""

import sys


def preload_similarity_model():
    """Downloads the 'all-MiniLM-L6-v2' model."""
    try:
        # Import lazily to avoid import errors if package is missing
        from sentence_transformers import SentenceTransformer

        print("\n⏳ Downloading Semantic Model (all-MiniLM-L6-v2) to local cache...")
        print("   (This prevents timeouts during benchmark execution)")

        # This triggers the download
        model = SentenceTransformer("all-MiniLM-L6-v2")

        print("✅ Model downloaded successfully (Cached).")
        return True
    except ImportError:
        print("⚠️  sentence-transformers not installed. Skipping model download.")
        return False
    except Exception as e:
        print(f"❌ Failed to download model: {e}")
        return False


if __name__ == "__main__":
    success = preload_similarity_model()
    if not success:
        sys.exit(1)
