"""
Unit tests for judge_parser.py.

Covers:
- Happy path: standard REASONING/SCORE output
- Score wrapped in brackets: SCORE: [4]
- Score as word: SCORE: four
- Score on separate line after label
- Mixed-case SCORE keyword
- Score appended with trailing text
- Missing SCORE (parse_success=False, score=None)
- Missing REASONING (non-fatal)
- Empty input
"""

from utils.scoring.llm_judge.judge_parser import parse


class TestParseHappyPath:
    """Standard well-formed judge output."""

    def test_standard_score_and_reasoning(self):
        raw = "REASONING: The response covers all key points with minor gaps.\nSCORE: 4"
        result = parse(raw)
        assert result.parse_success is True
        assert result.score == 4
        assert "minor gaps" in result.reasoning
        assert result.raw_response == raw

    def test_score_5(self):
        raw = "REASONING: Perfect answer.\nSCORE: 5"
        result = parse(raw)
        assert result.score == 5
        assert result.parse_success is True

    def test_score_1(self):
        raw = "REASONING: Completely off-topic.\nSCORE: 1"
        result = parse(raw)
        assert result.score == 1
        assert result.parse_success is True


class TestBracketAndQuoteVariants:
    """Score presented with surrounding brackets / quotes."""

    def test_score_in_square_brackets(self):
        raw = "REASONING: Mostly correct.\nSCORE: [4]"
        result = parse(raw)
        assert result.score == 4
        assert result.parse_success is True

    def test_score_in_parentheses(self):
        raw = "REASONING: Good attempt.\nSCORE: (3)"
        result = parse(raw)
        assert result.score == 3
        assert result.parse_success is True

    def test_score_in_double_quotes(self):
        raw = 'REASONING: Adequate.\nSCORE: "2"'
        result = parse(raw)
        assert result.score == 2
        assert result.parse_success is True


class TestWordScore:
    """Score given as an English word."""

    def test_four_as_word(self):
        raw = "REASONING: Good.\nSCORE: four"
        result = parse(raw)
        assert result.score == 4

    def test_five_as_word(self):
        raw = "REASONING: Excellent.\nSCORE: FIVE"
        result = parse(raw)
        assert result.score == 5

    def test_one_as_word(self):
        raw = "REASONING: Terrible.\nSCORE: one"
        result = parse(raw)
        assert result.score == 1

    def test_ten_as_word(self):
        raw = "REASONING: Perfect.\nSCORE: ten"
        result = parse(raw)
        assert result.score == 10


class TestCaseInsensitivity:
    """SCORE / REASONING keywords are case-insensitive."""

    def test_lowercase_score(self):
        raw = "reasoning: good.\nscore: 3"
        result = parse(raw)
        assert result.score == 3

    def test_mixed_case(self):
        raw = "Reasoning: decent.\nScore: 4"
        result = parse(raw)
        assert result.score == 4


class TestScoreOnDifferentLine:
    """Score number on a separate line after the SCORE label."""

    def test_score_with_dash(self):
        raw = "REASONING: Some analysis.\nSCORE - 3"
        result = parse(raw)
        assert result.score == 3
        assert result.parse_success is True


class TestMarkdownVariants:
    """Markdown header and bold permutations."""

    def test_parse_markdown_bold_score(self):
        raw = "REASONING: Good.\n**SCORE: 3**"
        result = parse(raw)
        assert result.score == 3
        assert result.parse_success is True

    def test_parse_markdown_header_score(self):
        raw = "REASONING: Okay.\n### **SCORE: 3**"
        result = parse(raw)
        assert result.score == 3
        assert result.parse_success is True

    def test_parse_separator_bold_score(self):
        raw = "REASONING: Fine.\n---\n**SCORE: 3**"
        result = parse(raw)
        assert result.score == 3
        assert result.parse_success is True

    def test_parse_reasoning_stripped_markdown(self):
        raw = "---\n### **REASONING:**\nclean text\n---\n**SCORE: 3**"
        result = parse(raw)
        assert result.score == 3
        assert result.reasoning == "clean text"
        assert result.parse_success is True


class TestMissingScore:
    """When no SCORE marker is found, parse_success is False and score is None."""

    def test_no_score_returns_none(self):
        raw = "REASONING: I couldn't decide on a score."
        result = parse(raw)
        assert result.score is None
        assert result.parse_success is False
        assert "I couldn't decide" in result.reasoning


class TestJsonSubScores:
    """When a SCORE marker is present, parse also looks for embedded JSON for sub_scores."""

    def test_sub_scores_present(self):
        raw = 'REASONING: Good attempt.\nSCORE: 4\n```json\n{"task_compliance": 5, "output_quality": 3, "standard_adherence": 4}\n```'
        result = parse(raw)
        assert result.score == 4
        assert result.parse_success is True
        assert result.judge_task_compliance == 5
        assert result.judge_output_quality == 3
        assert result.judge_standard_adherence == 4

    def test_missing_or_invalid_json(self):
        # Missing keys
        raw = 'REASONING: Good attempt.\nSCORE: 4\n```json\n{"task_compliance": 5}\n```'
        result = parse(raw)
        assert result.score == 4
        assert result.parse_success is True
        assert result.judge_task_compliance is None

    def test_invalid_json_format(self):
        raw = "REASONING: Good attempt.\nSCORE: 4\n```json\n{task_compliance: 5}\n```"
        result = parse(raw)
        assert result.score == 4
        assert result.parse_success is True
        assert result.judge_task_compliance is None

    def test_empty_string(self):
        result = parse("")
        assert result.score is None
        assert result.parse_success is False
        assert result.raw_response == ""

    def test_irrelevant_text(self):
        raw = "The answer looks okay to me. I'd estimate it's pretty good."
        result = parse(raw)
        assert result.score is None
        assert result.parse_success is False


class TestMissingReasoning:
    """Missing REASONING label is non-fatal; reasoning defaults to empty string."""

    def test_score_without_reasoning(self):
        raw = "SCORE: 3"
        result = parse(raw)
        assert result.score == 3
        assert result.reasoning == ""
        assert result.parse_success is True

    def test_reasoning_empty_when_absent(self):
        raw = "Here is my evaluation.\nSCORE: 2"
        result = parse(raw)
        assert result.reasoning == ""
        assert result.score == 2


class TestResultDataclass:
    """JudgeResult dataclass properties."""

    def test_raw_response_preserved(self):
        raw = "REASONING: ok.\nSCORE: 4"
        result = parse(raw)
        assert result.raw_response == raw

    def test_parse_success_flag_true(self):
        result = parse("SCORE: 5")
        assert result.parse_success is True

    def test_parse_success_flag_false(self):
        result = parse("no score here")
        assert result.parse_success is False
