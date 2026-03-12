from benchmark_modules.ux_writing.core.models import UXCriterion
from benchmark_modules.ux_writing.core.evaluators import (
    KeywordPresenceEvaluator,
    KeywordAbsenceEvaluator,
    MarkdownTableEvaluator,
    RegexEvaluator,
    LengthValidationEvaluator,
)


def test_keyword_presence():
    evaluator = KeywordPresenceEvaluator()
    criterion = UXCriterion(
        id="test",
        name="Test",
        points=10.0,
        check_method="keyword_presence",
        keywords=["foo", "bar"],
        min_keywords=1,
    )
    score, msg = evaluator.evaluate("This text has foo.", criterion)
    assert score == 10.0
    assert "✓" in msg

    score, msg = evaluator.evaluate("This text has nothing.", criterion)
    assert score == 0.0
    assert "✗" in msg


def test_keyword_absence():
    evaluator = KeywordAbsenceEvaluator()
    criterion = UXCriterion(
        id="test",
        name="Test",
        points=10.0,
        check_method="keyword_absence",
        forbidden_keywords=["bad"],
        max_violations=0,
    )
    score, msg = evaluator.evaluate("This is good.", criterion)
    assert score == 10.0

    score, msg = evaluator.evaluate("This is bad.", criterion)
    assert score == 0.0


def test_markdown_table():
    evaluator = MarkdownTableEvaluator()
    criterion = UXCriterion(
        id="test",
        name="Test",
        points=10.0,
        check_method="markdown_table_validation",
        min_rows=2,
    )
    table = "| Col1 | Col2 |\n|---|---|\n| Val1 | Val2 |\n| Val3 | Val4 |"
    score, msg = evaluator.evaluate(table, criterion)
    assert score == 10.0

    no_table = "Just text"
    score, msg = evaluator.evaluate(no_table, criterion)
    assert score == 0.0


def test_regex():
    evaluator = RegexEvaluator()
    criterion = UXCriterion(
        id="test", name="Test", points=10.0, check_method="regex", check_pattern=r"\d+"
    )
    # Default min regex matches is 4 in constants
    text = "1 2 3 4"
    score, msg = evaluator.evaluate(text, criterion)
    assert score == 10.0

    text = "1 2"
    score, msg = evaluator.evaluate(text, criterion)
    assert score < 10.0
    assert score > 0.0


def test_length_validation():
    evaluator = LengthValidationEvaluator()
    criterion = UXCriterion(
        id="test", name="Test", points=10.0, check_method="length_validation"
    )
    # Max length is 50
    text = "Click 'Short Button'"
    score, msg = evaluator.evaluate(text, criterion)
    assert score == 10.0

    text = "Click 'This is a very very very very very very very very long button label'"
    score, msg = evaluator.evaluate(text, criterion)
    assert score == 5.0  # Partial points
