"""
Semantic Similarity Utility
Provides functions to calculate semantic similarity between texts using embeddings.
"""

import logging
import os
import contextlib
from pathlib import Path
from typing import List, Optional
import numpy as np  # pylint: disable=import-error

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

# Configure logging
logger = logging.getLogger(__name__)


class SemanticSimilarity:
    """
    Calculates semantic similarity between texts.
    Uses 'all-MiniLM-L6-v2' model which is fast and effective.
    """

    _model = None
    _warning_logged = False

    @classmethod
    def check_availability(cls):
        """
        Checks if sentence-transformers is installed and logs a warning if not.
        Should be called once at application startup.
        """
        if not HAS_TRANSFORMERS and not cls._warning_logged:
            logger.warning(
                "⚠️  sentence-transformers not installed. Semantic similarity disabled.\n"
                "   This may slightly reduce scores as fuzzy matching fallback is unavailable.\n"
                "   Install with: pip install sentence-transformers"
            )
            cls._warning_logged = True

    @classmethod
    def get_model(cls) -> Optional[object]:
        """Lazy loading of the model."""
        if not HAS_TRANSFORMERS:
            if not cls._warning_logged:
                cls.check_availability()
            return None

        if cls._model is None:
            try:
                logger.info("Loading sentence-transformer model 'all-MiniLM-L6-v2'...")
                # Suppress verbose output from huggingface/transformers
                logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

                # Suppress stdout/stderr during loading to avoid progress bars
                # This is a bit hacky but necessary to keep the CLI clean
                with contextlib.redirect_stdout(Path(os.devnull).open('w', encoding='utf-8')), \
                     contextlib.redirect_stderr(Path(os.devnull).open('w', encoding='utf-8')):
                    cls._model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Failed to load sentence-transformer model: %s", e)
                return None
        return cls._model

    @classmethod
    def calculate_similarity(cls, text1: str, text2: str) -> float:
        """
        Calculates cosine similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score between 0.0 and 1.0
        """
        model = cls.get_model()
        if model is None:
            return 0.0

        try:
            embeddings = model.encode([text1, text2])
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(similarity)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error calculating similarity: %s", e)
            return 0.0

    @classmethod
    def check_similarity_threshold(cls, text: str, reference: str, threshold: float = 0.7) -> bool:
        """
        Checks if similarity is above a threshold.

        Args:
            text: Text to check
            reference: Reference text
            threshold: Minimum similarity score (0.0 - 1.0)

        Returns:
            True if similarity >= threshold
        """
        score = cls.calculate_similarity(text, reference)
        return score >= threshold

    @classmethod
    def find_best_match(cls, query: str, candidates: List[str]) -> float:
        """
        Finds the highest similarity score between query and a list of candidates.

        Args:
            query: The text to search for
            candidates: List of candidate texts (e.g. keywords or phrases)

        Returns:
            Highest similarity score found
        """
        model = cls.get_model()
        if model is None or not candidates:
            return 0.0

        try:
            query_embedding = model.encode([query])
            candidate_embeddings = model.encode(candidates)

            similarities = cosine_similarity(query_embedding, candidate_embeddings)[0]
            return float(np.max(similarities))
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error finding best match: %s", e)
            return 0.0
