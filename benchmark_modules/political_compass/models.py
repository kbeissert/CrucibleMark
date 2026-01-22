# benchmark_modules/political_compass/models.py
"""
Political Model Definitions
===========================

Data classes strictly for data storage of Questions and Analysis Results.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from .config import EXTREMISM_THRESHOLD

@dataclass
class Question:
    """Repräsentiert eine Political Compass Frage."""
    id: str
    module: str
    axis: str  # 'x', 'y', or 'both'
    topic: str
    context: str
    question: str
    options: Dict[str, dict]  # A/B/C/D mit text, value_x, value_y
    extremism_warning: bool = False

    def get_option_text(self, choice: str) -> str:
        """Gibt den Text einer Option zurück."""
        return self.options.get(choice, {}).get('text', '')

    def get_values(self, choice: str) -> Tuple[float, float]:
        """Gibt (value_x, value_y) für eine gewählte Option zurück."""
        opt = self.options.get(choice, {})

        # Explicit values take precedence
        val_x = opt.get('value_x')
        val_y = opt.get('value_y')

        # Generic value fallback based on axis
        val_generic = opt.get('value')

        final_x = 0.0
        final_y = 0.0

        if val_x is not None:
            final_x = float(val_x)
        elif self.axis == 'x' and val_generic is not None:
            final_x = float(val_generic)

        if val_y is not None:
            final_y = float(val_y)
        elif self.axis == 'y' and val_generic is not None:
            final_y = float(val_generic)

        return (final_x, final_y)

    def is_extremist(self, choice: str) -> bool:
        """Prüft, ob die gewählte Option extremistisch ist (±8 bis ±10)."""
        value_x, value_y = self.get_values(choice)
        return abs(value_x) >= EXTREMISM_THRESHOLD or abs(value_y) >= EXTREMISM_THRESHOLD


@dataclass
class ExtremismDetail:
    """Details einer extremistischen Antwort."""
    question_id: str
    module: str
    choice: str
    option_text: str
    value_x: float
    value_y: float
    category: str
    legal_warning: Optional[str] = None
