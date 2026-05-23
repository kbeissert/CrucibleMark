"""Language mismatch detection for benchmark responses.

Extracted from unified_runner._process_single_test() to satisfy
Anti-God-Script and Separation-of-Concerns rules.
"""

from __future__ import annotations

import logging

from utils.constants import (
    LANGUAGE_DE_MARKERS,
    LANGUAGE_EN_DE_RATIO,
    LANGUAGE_EN_MARKERS,
    LANGUAGE_EN_MIN_COUNT,
    LANGUAGE_MIN_WORDS,
)

logger = logging.getLogger(__name__)


class LanguageValidator:
    """Heuristic language mismatch detector using marker-word frequency."""

    def detect_mismatch(
        self, response: str, expected_lang: str
    ) -> dict | None:
        """Check whether the response is in the expected language.

        Returns a dict with mismatch metadata if a mismatch is detected,
        or None if the response is acceptable.

        Only 'de' (German) detection is currently implemented; all other
        expected_lang values return None (no mismatch).
        """
        if not expected_lang or len(response.split()) <= LANGUAGE_MIN_WORDS:
            return None

        if expected_lang != "de":
            return None

        words_lower = response.lower().split()
        de_count = sum(1 for w in words_lower if w in LANGUAGE_DE_MARKERS)
        en_count = sum(1 for w in words_lower if w in LANGUAGE_EN_MARKERS)

        if en_count > de_count * LANGUAGE_EN_DE_RATIO and en_count > LANGUAGE_EN_MIN_COUNT:
            logger.warning(
                "Language mismatch: expected=%s, DE=%d, EN=%d", expected_lang, de_count, en_count
            )
            return {
                "language_mismatch": True,
                "detected_language": "en",
                "de_marker_count": de_count,
                "en_marker_count": en_count,
            }

        return None
