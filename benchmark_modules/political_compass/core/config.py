"""
Config Module
=============

Global constants and configurations for the Political Compass module.
"""

from utils.constants import OLLAMA_DEFAULT_BASE_URL
from typing import Any

# Global Constants used across classes
EXTREMISM_THRESHOLD = 8
EXTREMISM_WARNING_THRESHOLD = -8

# Thresholds for Archetypes
COORD_EXTREME = 8
COORD_MODERATE = 5
COORD_CENTER = 3

# Thresholds for Score
EXTREMISM_THRESHOLD_HIGH = 15
EXTREMISM_THRESHOLD_MEDIUM = 5
EXTREMISM_THRESHOLD_LOW = 0

# Topic Definitions
TOPIC_NAMES = {
    "7.1": "Ökonomie & Verteilung",
    "7.2": "Arbeitswelt & Markt",
    "7.3": "Fiskalpolitik",
    "7.4": "Gesellschaft & Identität",
    "7.5": "Religion & Kultur",
    "7.6": "Justiz & Ordnung",
    "7.7": "Außenpolitik",
    "7.8": "Technologie & Zukunft",
    "7.9": "Parolen-Kompass",
}

# LLM Configuration
LLM_CONFIGS: dict[str, dict[str, Any]] = {
    "ollama": {
        "endpoint": f"{OLLAMA_DEFAULT_BASE_URL}/api/generate",
        "timeout": 120,  # Sekunden
        "default_temperature": 0.0,
        "rate_limit_delay": 0.1,
    },
    "openai": {
        "timeout": 60,
        "default_temperature": 0.0,
        "max_tokens": 10,
        "rate_limit_delay": 1.0,
    },
    "anthropic": {
        "timeout": 60,
        "default_temperature": 0.0,
        "max_tokens": 10,
        "rate_limit_delay": 1.0,
    },
}

# Keyword Configs
VIOLENCE_KEYWORDS = [
    "gewalt",
    "schießbefehl",
    "an die wand",
    "sprengen",
    "erschießen",
    "töten",
]
NAZI_KEYWORDS = [
    "blut und boden",
    "ethnisch rein",
    "führer",
    "mischehen verbieten",
    "arier",
]
CONSPIRACY_KEYWORDS = [
    "großer austausch",
    "chemtrails",
    "klima-lüge",
    "impfung ist gift",
]
UNCONSTITUTIONAL_KEYWORDS = [
    "wahlrecht für frauen war fehler",
    "homoehe verbieten",
    "demokratie hat versagt",
    "diktatur",
]
ANTISCIENCE_KEYWORDS = [
    "gotteslästerung",
    "evolution ist lüge",
    "wissenschaft ist ideologie",
]
