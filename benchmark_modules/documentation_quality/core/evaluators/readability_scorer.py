"""
Readability Scorer module.
Calculates Flesch-Kincaid Reading Ease and other metrics.
"""

import re
from typing import Any


class ReadabilityScorer:
    """
    Evaluates text readability using standard metrics.
    """

    @staticmethod
    def calculate_readability(response: str) -> dict[str, Any]:
        """
        Calculates Flesch Reading Ease score and statistics.
        """
        # Clean text (remove code blocks for readability analysis)
        clean_text = re.sub(r"```.*?```", "", response, flags=re.DOTALL)

        sentences = re.findall(r"[.!?]+", clean_text)
        words = re.findall(r"\b\w+\b", clean_text)

        num_sentences = max(1, len(sentences))
        num_words = max(1, len(words))

        syllables = sum(ReadabilityScorer._count_syllables(w) for w in words)

        score = ReadabilityScorer._flesch_reading_ease(
            num_sentences, num_words, syllables
        )
        grade = ReadabilityScorer.get_grade_level(score)

        return {
            "flesch_reading_ease": round(score, 2),
            "avg_sentence_length": round(num_words / num_sentences, 2),
            "avg_word_length": round(sum(len(w) for w in words) / num_words, 2),
            "grade_level": grade,
        }

    @staticmethod
    def _flesch_reading_ease(
        num_sentences: int, num_words: int, num_syllables: int
    ) -> float:
        """
        Formula: 206.835 - 1.015(words/sentences) - 84.6(syllables/words)
        """
        asl = num_words / num_sentences
        asw = num_syllables / num_words
        score = 206.835 - (1.015 * asl) - (84.6 * asw)
        return min(100.0, max(0.0, score))  # Clamp 0-100

    @staticmethod
    def _count_syllables(word: str) -> int:
        """
        Count vowel groups in a word.
        Heuristic: consecutive vowels count as one.
        """
        word = word.lower()
        if len(word) <= 3:
            return 1

        # Remove trailing 'e' (usually silent)
        if word.endswith("e"):
            word = word[:-1]

        vowels = "aeiouy"
        count = 0
        if word[0] in vowels:
            count += 1

        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] not in vowels:
                count += 1

        return max(1, count)

    @staticmethod
    def get_grade_level(flesch_score: float) -> str:
        """
        Maps Flesch score to education level.
        """
        grades = [
            (90, "Elementary"),
            (80, "6th Grade"),
            (70, "7th Grade"),
            (60, "High School"),
            (50, "Some College"),
            (30, "College Graduate"),
        ]

        for threshold, label in grades:
            if flesch_score >= threshold:
                return label
        return "Professional"
