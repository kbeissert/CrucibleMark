from unittest.mock import patch
from benchmark_modules.ux_writing.core.models import UXIssue
from benchmark_modules.ux_writing.core.evaluators import IssueEvaluator


def test_check_issue_mentioned_simple():
    text = "this is a test text"
    keywords = ["test"]
    assert IssueEvaluator.check_issue_mentioned(text, keywords) is True

    keywords = ["missing"]
    assert IssueEvaluator.check_issue_mentioned(text, keywords) is False


def test_check_issue_mentioned_wcag():
    text = "referencing wcag 1.4.3"
    keywords = ["1.4.3"]
    assert IssueEvaluator.check_issue_mentioned(text, keywords) is True


def test_evaluate_positive_match():
    issue = UXIssue(
        issue="Test Issue", points=10.0, keywords=["found"], inverse_match=False
    )
    points, msg, matched = IssueEvaluator.evaluate("keyword found", issue)
    assert points == 10.0
    assert matched is True


def test_evaluate_negative_match():
    issue = UXIssue(
        issue="Forbidden Term", points=10.0, keywords=["forbidden"], inverse_match=True
    )
    # Case 1: Forbidden term present -> 0 points
    points, msg, matched = IssueEvaluator.evaluate("this is forbidden", issue)
    assert points == 0.0
    assert matched is True  # It matched the keyword, which is bad

    # Case 2: Forbidden term absent -> 10 points
    points, msg, matched = IssueEvaluator.evaluate("this is clean", issue)
    assert points == 10.0
    assert matched is False  # It did NOT match the keyword, which is good


def test_evaluate_ratio():
    # If I use ratio 1.0. 3 * 1.0 = 3 matches needed.
    issue = UXIssue(
        issue="Strict Issue",
        points=10.0,
        keywords=["one", "two", "three"],
        required_ratio=1.0,
    )

    # Patch similarity to ensure we only test keyword ratio logic
    with patch(
        "benchmark_modules.ux_writing.core.evaluators.base.SemanticSimilarity.find_best_match",
        return_value=0.0,
    ):
        points, msg, matched = IssueEvaluator.evaluate("one two", issue)
        assert matched is False  # Missing "three"

        points, msg, matched = IssueEvaluator.evaluate("one two three", issue)
        assert matched is True
