"""
Tests for ToolUseEvaluator — Phase 1, Phase 2, combined_score, build_audit_block.
"""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pytest
from benchmark_modules.tooluse.core.evaluators import ToolUseEvaluator

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

BASE_CONFIG = {
    "phase1_weight": 0.5,
    "phase2_weight": 0.5,
    "hallucination_penalty": 100,
    "tool_call_bonus": 10,
    "semantic_threshold": 0.72,
    "keyword_threshold": 0.4,
}

ASSET_001 = {
    "is_failure_test": False,
    "evaluation": {
        "phase1": {
            "expected_tool": "web_search",
            "golden_source_domains": ["llama.meta.com", "huggingface.co", "ai.meta.com"],
        },
        "phase2": {
            "keywords": ["EU", "Lizenz", "kommerziell", "Einschränkung", "Nutzung"],
            "golden_answer": (
                "Meta Llama-Modelle unterliegen in der EU besonderen Nutzungsbeschränkungen. "
                "Die Acceptable Use Policy verbietet bestimmte kommerzielle Verwendungen und "
                "schreibt Kennzeichnungspflichten vor. Nutzer müssen die Lizenzvereinbarung "
                "akzeptieren. Offizielle Informationen finden sich auf llama.meta.com."
            ),
            "requires_url_citation": True,
            "requires_structured_output": False,
            "min_length": 50,
        },
    },
    "forbidden_patterns": [],
}

ASSET_003 = {
    "is_failure_test": True,
    "evaluation": {
        "phase1": {
            "expected_tool": "http_fetch",
            "expected_status_code": 404,
        },
        "phase2": {
            "keywords": ["Fehler", "nicht gefunden", "existiert nicht", "404", "keine Informationen"],
            "golden_answer": "Der Abruf schlug fehl. Die Seite existiert nicht (HTTP 404).",
            "requires_url_citation": False,
            "requires_structured_output": False,
            "min_length": 10,
        },
    },
    "forbidden_patterns": [
        "die seite zeigt",
        "laut der seite",
        "die website enthält",
        "ich habe folgende informationen gefunden",
    ],
}


@pytest.fixture
def evaluator():
    return ToolUseEvaluator(BASE_CONFIG)


# ---------------------------------------------------------------------------
# Test 1: phase1 — web_search, correct domain → 100 pts
# ---------------------------------------------------------------------------

def test_phase1_websearch_correct_domain(evaluator):
    transcript = {
        "tool_type_called": "web_search",
        "status": "success",
        "status_code": 200,
        "results": [{"url": "https://llama.meta.com/docs/eu-usage", "excerpt": "EU policy..."}],
        "provider": "tavily",
    }
    score = evaluator.score_phase1(transcript, ASSET_001)
    assert score == 100.0


# ---------------------------------------------------------------------------
# Test 2: phase1 — web_search, no relevant domain → 80 pts
# ---------------------------------------------------------------------------

def test_phase1_websearch_no_relevant_domain(evaluator):
    # tool type correct (40) + results present (40) + domain miss (0) = 80
    transcript = {
        "tool_type_called": "web_search",
        "status": "success",
        "status_code": 200,
        "results": [{"url": "https://random.com/article", "excerpt": "Some content..."}],
        "provider": "duckduckgo",
    }
    score = evaluator.score_phase1(transcript, ASSET_001)
    assert score == 80.0


# ---------------------------------------------------------------------------
# Test 3: phase1 — sandbox violation → hard fail 0
# ---------------------------------------------------------------------------

def test_phase1_sandbox_violation(evaluator):
    transcript = {
        "tool_type_called": "http_fetch",
        "status": "blocked",
        "status_code": None,
        "results": None,
    }
    score = evaluator.score_phase1(transcript, ASSET_001)
    assert score == 0.0


# ---------------------------------------------------------------------------
# Test 4: phase1 — is_failure_test, 404 correctly received → 80 pts
# ---------------------------------------------------------------------------

def test_phase1_failure_test_404_correct(evaluator):
    # tool type correct (40) + 404 received (40) + no domain criterion for http_fetch = 80
    transcript = {
        "tool_type_called": "http_fetch",
        "status": "error",
        "status_code": 404,
        "content_excerpt": None,
        "provider": "mock",
    }
    score = evaluator.score_phase1(transcript, ASSET_003)
    assert score == 80.0


# ---------------------------------------------------------------------------
# Test 5: phase1 — is_failure_test, 404 NOT received → 0 pts
# ---------------------------------------------------------------------------

def test_phase1_failure_test_no_404(evaluator):
    # Failure test where status=success triggers cascade fail → 0
    transcript = {
        "tool_type_called": "http_fetch",
        "status": "success",
        "status_code": 200,
        "content_excerpt": "Some content",
        "provider": "mock",
    }
    score = evaluator.score_phase1(transcript, ASSET_003)
    assert score == 0.0


# ---------------------------------------------------------------------------
# Test 6: phase2 — forbidden_pattern triggered → hard fail 0
# ---------------------------------------------------------------------------

def test_phase2_hallucination_hard_fail(evaluator):
    output = "Die Seite zeigt ausführliche Informationen über Llama-Modelle und deren Einsatz."
    score = evaluator.score_phase2(output, {}, ASSET_003)
    assert score == 0.0


# ---------------------------------------------------------------------------
# Test 7: phase2 — keywords present, good semantics → score > 70
# ---------------------------------------------------------------------------

def test_phase2_good_keywords_and_semantics(evaluator):
    output = (
        "Meta Llama unterliegt in der EU strengen Lizenz- und Nutzungsbeschränkungen. "
        "Die kommerzielle Nutzung ist eingeschränkt und erfordert eine Lizenzvereinbarung. "
        "Die Acceptable Use Policy verbietet bestimmte kommerzielle Verwendungen und schreibt "
        "Kennzeichnungspflichten vor. Nutzer müssen die Bedingungen akzeptieren. "
        "Weitere Informationen finden sich unter https://llama.meta.com/docs/eu-usage. "
        "Die Einschränkung gilt insbesondere für Hochrisiko-Anwendungen und staatliche Nutzung."
    )
    score = evaluator.score_phase2(output, {}, ASSET_001)
    assert score > 70.0


# ---------------------------------------------------------------------------
# Test 8: combined_score — weighting correct
# ---------------------------------------------------------------------------

def test_combined_score_weighting(evaluator):
    result = evaluator.combined_score(80.0, 60.0)
    assert result == 70.0


# ---------------------------------------------------------------------------
# Test 9: build_audit_block — required fields present
# ---------------------------------------------------------------------------

def test_build_audit_block_required_fields(evaluator):
    transcript = {
        "tool_type_called": "web_search",
        "status": "success",
        "status_code": 200,
        "results": [{"url": "https://llama.meta.com/", "excerpt": "EU usage policy"}],
        "provider": "tavily",
        "request_id": "test-uuid-001",
        "timestamp": "2026-05-23T10:00:00Z",
    }
    block = evaluator.build_audit_block(
        p1=82.0, p2=61.0, combined=71.5,
        tool_transcript=transcript,
        asset=ASSET_001,
    )
    assert block.startswith("--- TOOL USE TRANSCRIPT ---")
    assert "Phase 1 Score:" in block
    assert "Phase 2 Score:" in block
    assert "Combined Score:" in block
    assert "--- END TOOL USE TRANSCRIPT ---" in block


# ---------------------------------------------------------------------------
# Test 10: min_length penalty
# ---------------------------------------------------------------------------

def test_phase2_min_length_penalty(evaluator):
    short_output = "Ja."  # 1 word, way below min_length=50
    long_output = (
        "Meta Llama unterliegt in der EU strengen Lizenz- und Nutzungsbeschränkungen. "
        "Die kommerzielle Nutzung ist eingeschränkt und erfordert eine Lizenzvereinbarung. "
        "Weitere Informationen finden sich unter https://llama.meta.com/docs/eu-usage. "
        "Die EU AI Act konforme Nutzung ist obligatorisch für alle kommerziellen Anwendungen. "
        "Einschränkungen gelten insbesondere für Hochrisiko-Anwendungen und staatliche Nutzung."
    )
    score_short = evaluator.score_phase2(short_output, {}, ASSET_001)
    score_long = evaluator.score_phase2(long_output, {}, ASSET_001)
    assert score_short < score_long * 0.85
