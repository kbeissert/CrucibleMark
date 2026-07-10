"""
Semantic Similarity Utility
Provides functions to calculate semantic similarity between texts using embeddings.
"""

import logging
import os
import contextlib
from pathlib import Path
from typing import Any
import numpy as np  # pylint: disable=import-error

try:
    import importlib.util

    if importlib.util.find_spec("sentence_transformers") is not None:
        HAS_TRANSFORMERS = True
    else:
        HAS_TRANSFORMERS = False
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
    def get_model(cls) -> Any | None:
        """Lazy loading of the model."""
        if not HAS_TRANSFORMERS:
            if not cls._warning_logged:
                cls.check_availability()
            return None

        if cls._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info(
                    "⏳ Lade KI-Modell für semantische Vergleiche (kann beim ersten Mal dauern)..."
                )

                # Suppress stdout/stderr during loading to avoid progress bars
                # This is a bit hacky but necessary to keep the CLI clean
                with (
                    contextlib.redirect_stdout(
                        Path(os.devnull).open("w", encoding="utf-8")
                    ),
                    contextlib.redirect_stderr(
                        Path(os.devnull).open("w", encoding="utf-8")
                    ),
                ):
                    cls._model = SentenceTransformer("all-MiniLM-L6-v2")
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

        # Type safety check
        if not isinstance(text1, str) or not isinstance(text2, str):
            logger.warning(
                "Invalid input types for similarity: %s, %s", type(text1), type(text2)
            )
            return 0.0

        try:
            from sklearn.metrics.pairwise import cosine_similarity

            embeddings = model.encode([text1, text2])
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(similarity)
        except ImportError:
            logger.error("Error: sklearn is required for cosine similarity.")
            return 0.0
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error calculating similarity: %s", e)
            return 0.0

    @classmethod
    def check_similarity_threshold(
        cls, text: str, reference: str, threshold: float = 0.7
    ) -> bool:
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
    def find_best_match(cls, query: str, candidates: list[str]) -> float:
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

        # Type safety check
        if not isinstance(query, str):
            logger.warning("Invalid query type: %s", type(query))
            return 0.0

        cleaned_candidates = [c for c in candidates if isinstance(c, str)]
        if not cleaned_candidates:
            return 0.0

        try:
            from sklearn.metrics.pairwise import cosine_similarity

            query_embedding = model.encode([query])
            candidate_embeddings = model.encode(candidates)

            similarities = cosine_similarity(query_embedding, candidate_embeddings)[0]
            return float(np.max(similarities))
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error finding best match: %s", e)
            return 0.0
