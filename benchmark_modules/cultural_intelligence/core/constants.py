"""
Configuration constants for Cultural Intelligence module.

German Language Markers:
- GERMAN_WORD_MARKERS: Common German words that indicate language proficiency
- FORMAL_MARKERS: Sie/Ihnen/Ihr indicators
- INFORMAL_MARKERS: Du/Dir/Dein indicators

Regional Markers:
- REGIONAL_EXPRESSIONS: DE/AT/CH specific terms
- POLITENESS_MARKERS: Höflichkeitsformen

Scoring:
- DEFAULT_WEIGHTS: Language (40%), Cultural (30%), Quality (30%)
"""

# Token approximation multiplier
TOKEN_MULTIPLIER = 1.3

# Default temperature for cultural content
DEFAULT_TEMPERATURE = 0.3

# German Language Markers
GERMAN_WORD_MARKERS = [
    # Common German words
    "aber",
    "auch",
    "bei",
    "durch",
    "für",
    "gegen",
    "jedoch",
    "nicht",
    "oder",
    "sondern",
    "sowie",
    "über",
    "während",
    "zwischen",
    # Verbs
    "haben",
    "sein",
    "werden",
    "können",
    "müssen",
    "sollen",
    # Conjunctions
    "obwohl",
    "weil",
    "dass",
    "damit",
    "falls",
    "nachdem",
    # Articles
    "der",
    "die",
    "das",
    "den",
    "dem",
    "des",
]

# Formality Markers
FORMAL_MARKERS = {
    "pronouns": ["sie", "ihnen", "ihr", "ihre"],
    "verbs": ["möchten", "würden", "könnten"],
    "phrases": ["sehr geehrte", "mit freundlichen grüßen", "hochachtungsvoll"],
}

INFORMAL_MARKERS = {
    "pronouns": ["du", "dir", "dein", "deine"],
    "verbs": ["willst", "kannst", "magst"],
    "phrases": ["hallo", "tschüss", "liebe grüße"],
}

# Regional Expressions (DE/AT/CH)
REGIONAL_EXPRESSIONS = {
    "de": {
        "food": ["brötchen", "frikadelle", "pfannkuchen"],
        "phrases": ["guten tag", "tschüss", "moin"],
        "vocab": ["handy", "führerschein", "abitur"],
    },
    "at": {
        "food": ["semmel", "faschiertes", "palatschinken"],
        "phrases": ["grüß gott", "baba", "servus"],
        "vocab": ["jänner", "erdäpfel", "matura"],
    },
    "ch": {
        "food": ["brötli", "gehacktes", "omeletten"],
        "phrases": ["grüezi", "ade", "merci"],
        "vocab": ["natel", "velo", "parkierung"],
    },
}

# Politeness Markers
POLITENESS_MARKERS = [
    "bitte",
    "danke",
    "entschuldigung",
    "gerne",
    "freundlich",
    "höflich",
    "respektvoll",
    "zuvorkommend",
]

# Default scoring weights
DEFAULT_WEIGHTS = {
    "language_proficiency": 0.40,  # 40 points
    "cultural_fit": 0.30,  # 30 points
    "solution_quality": 0.30,  # 30 points
}

# Minimum keyword matches for language proficiency
MIN_GERMAN_WORDS = 5  # At least 5 German markers to count as proficient

# Formality threshold (% of formal markers vs informal)
FORMALITY_THRESHOLD = 0.6  # 60% formal markers = considered formal
