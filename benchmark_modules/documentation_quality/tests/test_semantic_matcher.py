import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from benchmark_modules.documentation_quality.core.evaluators.semantic_matcher import (
    SemanticMatcher,
)


def test_semantic_match_simple():
    response = "<think>hmm</think>Missing installation steps and setup guide"
    keywords = ["installation", "setup", "guide"]
    # Should match 2 keywords ("installation", "setup")
    assert SemanticMatcher.check_match(response, keywords, 2, "asset_001") is True
    print("test_semantic_match_simple Passed")


if __name__ == "__main__":
    test_semantic_match_simple()
