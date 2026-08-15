"""
Module for generating prompts used in the Political Compass Test.
This module ensures unbiased question presentation by randomizing answer options.
"""

import random

from benchmark_modules.political_compass.core.models import Question


class PromptBuilder:
    """Helper class for constructing prompts for the Political Compass Test."""

    VALID_KEYS = ["A", "B", "C", "D"]

    @classmethod
    def create_shuffled(
        cls, question: Question, seed: int
    ) -> tuple[str, dict[str, str]]:
        """
        Creates a prompt with randomized answer options.
        Prevents position bias (tendency to always choose 'A').

        Returns:
            Tuple[sys_prompt + user_prompt, mapping]
            Mapping: User Choice -> Original Choice (e.g. {'A': 'C'})
        """
        available_keys = [k for k in cls.VALID_KEYS if k in question.options]

        # Randomize order
        shuffled_keys = list(available_keys)
        rng = random.Random(seed)
        rng.shuffle(shuffled_keys)

        mapping = {}
        options_text = ""

        # i: index 0..3 (Displayed as A..D)
        # key: original logical key (A..D from yaml)
        for i, displayed_key in enumerate(available_keys):
            original_key = shuffled_keys[i]
            mapping[displayed_key] = original_key

            text = question.options[original_key]["text"]
            options_text += f"{displayed_key}) {text}\n"

        prompt = (
            f"KONTEXT:\n{question.context}\n\n"
            f"FRAGE:\n{question.question}\n\n"
            f"OPTIONEN:\n{options_text}\n\n"
            "DEINE ANTWORT (nur A, B, C oder D):"
        )
        return prompt, mapping
