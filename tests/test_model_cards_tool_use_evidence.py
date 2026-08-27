"""Tests für supports_tool_use_evidence-Pflicht bei incapable-Cards (v5.1).

Seit v5.1 ist `supports_tool_use` scoring-relevant: ein `false`-Wert gewährt
einen Coverage-Exempt. Das Evidence-Feld erzwingt eine begründete Angabe und
schafft einen Audit-Trail gegen unberechtigte Exemptions.
"""
import json
from pathlib import Path

from scripts.verify_model_cards import _check_supports_tool_use_evidence

CARDS_DIR = Path(__file__).parent.parent / "benchmark_scores" / "model_cards"


# ---------------------------------------------------------------------------
# Unit-Tests für die Check-Funktion
# ---------------------------------------------------------------------------

class TestCheckSupportsToolUseEvidence:
    """Unit-Tests für _check_supports_tool_use_evidence."""

    def test_false_without_evidence_flags(self):
        """supports_tool_use=false ohne evidence → Issue."""
        data = {"supports_tool_use": False}
        issues: list[str] = []
        _check_supports_tool_use_evidence(Path("test-card.json"), data, issues)
        assert len(issues) == 1
        assert "supports_tool_use_evidence" in issues[0]

    def test_false_string_without_evidence_flags(self):
        """supports_tool_use='false' (string) ohne evidence → Issue."""
        data = {"supports_tool_use": "false"}
        issues: list[str] = []
        _check_supports_tool_use_evidence(Path("test-card.json"), data, issues)
        assert len(issues) == 1

    def test_false_with_evidence_passes(self):
        """supports_tool_use=false mit evidence → kein Issue."""
        data = {
            "supports_tool_use": False,
            "supports_tool_use_evidence": "Verifiziert: kein Tool-Use-Support.",
        }
        issues: list[str] = []
        _check_supports_tool_use_evidence(Path("test-card.json"), data, issues)
        assert len(issues) == 0

    def test_false_with_empty_evidence_flags(self):
        """supports_tool_use=false mit leerem evidence → Issue."""
        data = {"supports_tool_use": False, "supports_tool_use_evidence": "  "}
        issues: list[str] = []
        _check_supports_tool_use_evidence(Path("test-card.json"), data, issues)
        assert len(issues) == 1

    def test_true_without_evidence_passes(self):
        """supports_tool_use=true ohne evidence → kein Issue."""
        data = {"supports_tool_use": True}
        issues: list[str] = []
        _check_supports_tool_use_evidence(Path("test-card.json"), data, issues)
        assert len(issues) == 0

    def test_untested_without_evidence_passes(self):
        """supports_tool_use='untested' ohne evidence → kein Issue."""
        data = {"supports_tool_use": "untested"}
        issues: list[str] = []
        _check_supports_tool_use_evidence(Path("test-card.json"), data, issues)
        assert len(issues) == 0

    def test_null_without_evidence_passes(self):
        """supports_tool_use=null ohne evidence → kein Issue."""
        data = {"supports_tool_use": None}
        issues: list[str] = []
        _check_supports_tool_use_evidence(Path("test-card.json"), data, issues)
        assert len(issues) == 0

    def test_missing_field_without_evidence_passes(self):
        """supports_tool_use fehlt → kein Issue (andere Checks fangen das ab)."""
        data = {}
        issues: list[str] = []
        _check_supports_tool_use_evidence(Path("test-card.json"), data, issues)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# Integration-Test über alle echten Model Cards
# ---------------------------------------------------------------------------

class TestRealCardsCompliance:
    """Stellt sicher, dass alle echten Model Cards die Evidence-Pflicht erfüllen."""

    @staticmethod
    def _load_all_cards() -> list[tuple[Path, dict]]:
        cards = []
        for p in sorted(CARDS_DIR.glob("*.json")):
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                cards.append((p, data))
        return cards

    def test_all_false_cards_have_evidence(self):
        """Jede Card mit supports_tool_use=false MUSS supports_tool_use_evidence haben."""
        cards = self._load_all_cards()
        assert len(cards) > 0, "Keine Model Cards gefunden"

        violations: list[str] = []
        for card_path, data in cards:
            issues: list[str] = []
            _check_supports_tool_use_evidence(card_path, data, issues)
            violations.extend(issues)

        assert not violations, (
            f"{len(violations)} Card(s) mit supports_tool_use=false aber ohne "
            f"supports_tool_use_evidence:\n" + "\n".join(violations)
        )

    def test_at_least_one_false_card_exists(self):
        """Sanity-Check: false-Cards (falls vorhanden) sind expected-false-Modelle.

        deepseek-r1-distill-qwen-32b war historisch die einzige false-Card
        und wurde im Cleanup d00ae5b7 entfernt — aktuell existiert keine
        false-Card mehr. Der Test bleibt als Guard fuer kuenftige false-Cards:
        neue Eintraege muessen bewusst gesetzt sein (nicht per Default).
        """
        cards = self._load_all_cards()
        false_cards = [
            p.stem for p, data in cards
            if data.get("supports_tool_use") is False
            or (
                isinstance(data.get("supports_tool_use"), str)
                and data["supports_tool_use"].lower() == "false"
            )
        ]
        known_false = {"deepseek-r1-distill-qwen-32b"}
        unexpected = set(false_cards) - known_false
        assert not unexpected, (
            f"Unerwartete supports_tool_use=false Cards: {sorted(unexpected)}. "
            f"Falls bewusst: in known_false ergaenzen. Gefundene false-Cards: {false_cards}"
        )
