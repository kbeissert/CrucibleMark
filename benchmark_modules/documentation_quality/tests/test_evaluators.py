
import sys
from pathlib import Path
from textwrap import dedent
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from benchmark_modules.documentation_quality.core.evaluators import (
    StructureValidator,
    ReadabilityScorer,
    CompletenessChecker,
    SemanticMatcher
)

def test_structure_validator():
    markdown = dedent("""
    # Title
    ## Section 1
    Some text
    ```python
    code here
    ```
    """)
    result = StructureValidator.validate_markdown_structure(markdown, "readme")
    assert result["stats"]["code_block_count"] == 1
    assert result["stats"]["heading_count"] == 2
    print("✓ StructureValidator test passed")

def test_readability_scorer():
    text = "This is a simple sentence. It is easy to read."
    result = ReadabilityScorer.calculate_readability(text)
    assert result["flesch_reading_ease"] > 80  # Should be "easy"
    print("✓ ReadabilityScorer test passed")

def test_completeness_checker():
    markdown = dedent("""
    # Installation
    pip install package
    # Usage
    import package
    """)
    result = CompletenessChecker.check_completeness(markdown, "readme")
    assert "installation" in result["present_sections"]
    assert "examples" in result["missing_sections"]  # Missing from README schema
    print("✓ CompletenessChecker test passed")

def test_semantic_matcher():
    response = "Missing installation instructions and setup guide"
    keywords = ["installation", "setup"]
    assert SemanticMatcher.check_match(response, keywords, 2, "asset_001") == True
    print("✓ SemanticMatcher test passed")

if __name__ == "__main__":
    test_structure_validator()
    test_readability_scorer()
    test_completeness_checker()
    test_semantic_matcher()
    print("\n✅ All tests passed!")
