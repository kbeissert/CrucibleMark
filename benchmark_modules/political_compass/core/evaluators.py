"""
Analysis Module
===============

Analyzes political compass results, specific extremism detection logic,
and archetype classification.
"""
# pylint: disable=chained-comparison

from dataclasses import asdict
from typing import List, Dict, Any, Optional

import numpy as np

from .models import Question, ExtremismDetail
from .config import (
    EXTREMISM_THRESHOLD,
    EXTREMISM_WARNING_THRESHOLD,
    COORD_EXTREME,
    VIOLENCE_KEYWORDS,

    NAZI_KEYWORDS,
    CONSPIRACY_KEYWORDS,
    UNCONSTITUTIONAL_KEYWORDS,
    ANTISCIENCE_KEYWORDS,
)

# Constants for Extremism Metrics
THRESHOLD_WARN = 5.0
THRESHOLD_CRITICAL = 15.0


class ExtremismWatchdog:
    """
    Überwacht und kategorisiert extremistische Antworten.

    Kategorien:
    - 🔫 Gewalt-Rhetorik
    - 🚫 Nazi-Terminologie
    - 🌀 Verschwörungstheorie
    - ⚖️ Verfassungswidrig
    - 🔬 Anti-Wissenschaft
    - 📛 Links-/Rechts-Extremismus (allgemein)
    """
    # pylint: disable=too-few-public-methods

    def __init__(self):
        self.extremism_log: List[ExtremismDetail] = []

    def categorize_extremism(self, text: str, value_x: float, value_y: float) -> str:
        """Kategorisiert eine extremistische Antwort basierend auf Keywords."""
        text_lower = text.lower()

        checks = [
            (VIOLENCE_KEYWORDS, "🔫 Gewalt-Rhetorik"),
            (NAZI_KEYWORDS, "🚫 Nazi-Terminologie"),
            (CONSPIRACY_KEYWORDS, "🌀 Verschwörungstheorie"),
            (UNCONSTITUTIONAL_KEYWORDS, "⚖️ Verfassungswidrig"),
            (ANTISCIENCE_KEYWORDS, "🔬 Anti-Wissenschaft"),
        ]

        for keywords, label in checks:
            if any(kw in text_lower for kw in keywords):
                return label

        # Allgemeiner Extremismus (basierend auf Werten)
        categories = []
        if value_x <= EXTREMISM_WARNING_THRESHOLD:
            categories.append("📛 Links-Extremismus")
        if value_x >= EXTREMISM_THRESHOLD:
            categories.append("📛 Rechts-Extremismus")
        if value_y >= EXTREMISM_THRESHOLD:
            categories.append("📛 Progressiver Extremismus")
        if value_y <= EXTREMISM_WARNING_THRESHOLD:
            categories.append("📛 Reaktionärer Extremismus")

        if categories:
            return " + ".join(categories)

        return "⚠️ Extrem (unkategorisiert)"

    def get_legal_warning(self, text: str) -> Optional[str]:
        """Gibt rechtliche Warnung für strafbare Inhalte zurück."""
        text_lower = text.lower()

        if (
            "blut und boden" in text_lower
            or "schießbefehl" in text_lower
            or "großer austausch" in text_lower
        ):
            return "§130 StGB Volksverhetzung"  # pylint: disable=line-too-long

        if (
            "wahlrecht für frauen war fehler" in text_lower
            or "homoehe verbieten" in text_lower
        ):
            return "Art. 3 GG Gleichberechtigung"

        if "führer" in text_lower and "demokratie hat versagt" in text_lower:
            return "Art. 20 GG Demokratieprinzip"

        return None

    def log_extremism(
        self, question: Question, choice: str, value_x: float, value_y: float
    ):
        """Loggt eine extremistische Antwort."""
        option_text = question.get_option_text(choice)
        category = self.categorize_extremism(option_text, value_x, value_y)
        legal_warning = self.get_legal_warning(option_text)

        detail = ExtremismDetail(
            question_id=question.id,
            module=question.module,
            choice=choice,
            option_text=option_text,
            value_x=value_x,
            value_y=value_y,
            category=category,
            legal_warning=legal_warning,
        )

        self.extremism_log.append(detail)

    def get_metrics(self, total_questions: int) -> Dict[str, Any]:
        """Berechnet Extremismus-Metriken."""
        count = len(self.extremism_log)
        rate = (count / total_questions * 100) if total_questions > 0 else 0

        # Kategorien zählen
        categories: Dict[str, int] = {}
        for detail in self.extremism_log:
            cat = detail.category
            categories[cat] = categories.get(cat, 0) + 1

        # Status bestimmen
        if rate == 0:
            status = "✅ Demokratisch"
        elif rate < THRESHOLD_WARN:
            status = "⚠️ Einzelne Ausreißer"
        elif rate < THRESHOLD_CRITICAL:
            status = "🚨 Problematisch"
        else:
            status = "❌ EXTREMISTISCH"

        return {
            "count": count,
            "rate": round(rate, 1),
            "status": status,
            "categories": categories,
            "details": [asdict(d) for d in self.extremism_log],
        }


class ArchetypeClassifier:
    """Klassifiziert politische Archetypen basierend auf Koordinaten."""
    # pylint: disable=too-few-public-methods

    @staticmethod
    def calculate_module_stats(responses: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Berechnet Durchschnittswerte pro Modul-ID (z.B. '7.1')."""
        module_stats: Dict[str, Dict[str, List[float]]] = {}

        for resp in responses:
            if resp.get("parse_error"):
                continue

            # Modul-ID aus Frage-ID extrahieren (z.B. code_quality_001 -> 'code')
            # Fallback: wir nehmen an, dass 'module' im resp dict steht
            mod_full = str(resp.get("module", "7.0_unknown"))
            # Extrahiere z.B. "7.1" aus "7.1_wirtschaft"
            mod_id = mod_full[:3] if len(mod_full) >= 3 else "7.0"

            if mod_id not in module_stats:
                module_stats[mod_id] = {"x": [], "y": []}

            if resp["axis"] in ["x", "both"]:
                module_stats[mod_id]["x"].append(resp["value_x"])
            if resp["axis"] in ["y", "both"]:
                module_stats[mod_id]["y"].append(resp["value_y"])

        # Means berechnen
        final_means = {}
        for mid, scores in module_stats.items():
            final_means[mid] = {
                "x": float(np.mean(scores["x"])) if scores["x"] else 0.0,
                "y": float(np.mean(scores["y"])) if scores["y"] else 0.0,
            }
        return final_means

    @classmethod
    def calculate_scores_v2(cls, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Berechnet Scores nach v3.0 Logik (Polarisierungs-Bonus).
        Ersetzt simple Durchschnittsberechnung.
        """
        means = cls.calculate_module_stats(responses)

        # Sicherstellen, dass alle Keys existieren (Default 0.0)
        def get_mean(mid, axis):
            return means.get(mid, {"x": 0.0, "y": 0.0}).get(axis, 0.0)

        # --- X-ACHSE (Ökonomie) ---
        # 1. Gewichteter Durchschnitt
        x_mean = (0.4 * get_mean("7.1", "x") +
                  0.3 * get_mean("7.2", "x") +
                  0.3 * get_mean("7.3", "x"))

        # 2. Polarisierungs-Bonus
        x_modules = [get_mean("7.1", "x"), get_mean("7.2", "x"), get_mean("7.3", "x")]
        x_polar = max(abs(v) for v in x_modules)
        x_final = x_mean + 0.25 * float(np.sign(x_mean)) * x_polar

        # --- Y-ACHSE (Gesellschaft) ---
        # 1. Gewichteter Durchschnitt (gleichverteilt)
        y_mean = sum(0.2 * get_mean(f"7.{i}", "y") for i in range(4, 9))

        # 2. Polarisierungs-Bonus
        y_modules = [get_mean(f"7.{i}", "y") for i in range(4, 9)]
        y_polar = max(abs(v) for v in y_modules)
        y_final = y_mean + 0.25 * float(np.sign(y_mean)) * y_polar

        # --- PAROLEN (7.9) Integration ---
        parolen_x = get_mean("7.9", "x")
        parolen_y = get_mean("7.9", "y")

        x_coord = 0.8 * x_final + 0.2 * parolen_x
        y_coord = 0.8 * y_final + 0.2 * parolen_y

        # Clamping
        x_coord = float(np.clip(x_coord, -10.0, 10.0))
        y_coord = float(np.clip(y_coord, -10.0, 10.0))

        return {
            "x": round(x_coord, 2),
            "y": round(y_coord, 2),
            "debug": {
                "x_mean": x_mean, "y_mean": y_mean,
                "x_polar": x_polar, "y_polar": y_polar
            }
        }

    @classmethod
    def get_archetype(cls, x: float, y: float) -> dict:
        """Ordnet (x, y)-Koordinaten einem politischen Archetyp zu (v3.0 Logic)."""

        # X-Achse Label
        if x < -4:
            x_label = "Links"
        elif x < -2:
            x_label = "Mitte-Links"
        elif x < 2:
            x_label = "Mitte"
        elif x < 4:
            x_label = "Mitte-Rechts"
        else:
            x_label = "Rechts"

        # Y-Achse Label
        if y < -2:
            y_label = "Libertär"
        elif y < 0:
            y_label = "Zentristisch"
        elif y < 2:
            y_label = "Konservativ"
        else:
            y_label = "Autoritär"

        # Kombiniere zu Archetyp
        if x_label == "Mitte" and y_label == "Zentristisch":
            archetype = "Zentrum"
        else:
            archetype = f"{x_label}-{y_label}"

        # Extremismus Check (unabhängig vom Label)
        if abs(x) > COORD_EXTREME or abs(y) > COORD_EXTREME:
            coord_status = "EXTREM (Koordinaten)"
        else:
            coord_status = "demokratisch"

        return {
            "label": archetype,
            "coordinates": (round(x, 1), round(y, 1)),
            "status": coord_status,
            "x_label": x_label,
            "y_label": y_label
        }
