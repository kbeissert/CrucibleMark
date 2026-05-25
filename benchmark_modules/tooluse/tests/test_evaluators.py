"""Tests for ToolUseEvaluator — Phase 1, Phase 2, combined_score, build_audit_block.
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
            "expected_tool": "fetch",
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


ASSET_002 = {
    "is_failure_test": False,
    "evaluation": {
        "phase1": {
            "expected_tool": "fetch",
            "expected_status_code": 200,
        },
        "phase2": {
            "keywords": ["llama 4", "code llama", "llama guard", "lizenz", "hugging"],
            "golden_answer": (
                "Auf der Meta-Llama-Seite bei Hugging Face werden mehrere Modellfamilien aufgeführt. "
                "Dazu gehören Llama 4 als aktuelle multimodale Familie, Llama 3.2 für textbasierte "
                "Modelle sowie Code Llama für Programmieraufgaben. Llama Guard dient der "
                "Sicherheitsklassifikation. Die Modelle sind nur nach Akzeptanz der "
                "Lizenzbedingungen zugänglich."
            ),
            "requires_structured_output": True,
            "min_length": 40,
        },
    },
    "forbidden_patterns": [],
}


@pytest.fixture
def evaluator():
    return ToolUseEvaluator(BASE_CONFIG)


# ---------------------------------------------------------------------------
# Test 1: phase1 — web_search, correct domain → 100 pts
# ---------------------------------------------------------------------------

def test_phase1_websearch_correct_domain(evaluator):
    # tool type correct (40) + results ≥1 → 40pts result + 2 results → 20pts source = 100
    transcript = {
        "tool_type_called": "web_search",
        "status": "success",
        "status_code": 200,
        "results": [
            {"url": "https://llama.meta.com/docs/eu-usage", "excerpt": "EU policy..."},
            {"url": "https://huggingface.co/meta-llama", "excerpt": "Llama models"},
        ],
        "provider": "tavily",
    }
    score = evaluator.score_phase1(transcript, ASSET_001)
    assert score == 100.0


# ---------------------------------------------------------------------------
# Test 2: phase1 — web_search, no relevant domain → 80 pts
# ---------------------------------------------------------------------------

def test_phase1_websearch_no_relevant_domain(evaluator):
    # tool type correct (40) + results present (40) + only 1 result → 10pts source = 90
    transcript = {
        "tool_type_called": "web_search",
        "status": "success",
        "status_code": 200,
        "results": [{"url": "https://random.com/article", "excerpt": "Some content..."}],
        "provider": "duckduckgo",
    }
    score = evaluator.score_phase1(transcript, ASSET_001)
    assert score == 90.0


# ---------------------------------------------------------------------------
# Test 2b: phase1 — web_search, status=success but 0 results → 80 pts (empty_result state)
# ---------------------------------------------------------------------------

def test_phase1_websearch_empty_result_state(evaluator):
    # tool type correct (40) + status=success/0 results → call-execution pts (40) + source quality 0 = 80
    transcript = {
        "tool_type_called": "web_search",
        "status": "success",
        "results": [],
        "provider": "tavily",
    }
    score = evaluator.score_phase1(transcript, ASSET_001)
    assert score == 80.0


# ---------------------------------------------------------------------------
# Test 3: phase1 — sandbox violation → hard fail 0
# ---------------------------------------------------------------------------

def test_phase1_sandbox_violation(evaluator):
    transcript = {
        "tool_type_called": "fetch",
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
        "tool_type_called": "fetch",
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
        "tool_type_called": "fetch",
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
# Test 8: combined_score — weighting correct (normal case, tool_call_valid=True)
# ---------------------------------------------------------------------------

def test_combined_score_weighting(evaluator):
    # Normal case: p1=80, p2=60, weights 0.5/0.5 → 80*0.5 + 60*0.5 = 70
    result = evaluator.combined_score(80.0, 60.0, tool_call_valid=True)
    assert result == 70.0


# Test 8b: combined_score — hard fail when tool_call_valid=False
# ---------------------------------------------------------------------------

def test_combined_score_hard_fail_tool_invalid(evaluator):
    # Hard fail: tool_call_valid=False → capped at 60 regardless of p2
    result = evaluator.combined_score(40.0, 100.0, tool_call_valid=False)
    assert result == 60.0


# Test 8c: combined_score — hard fail when p1=0
# ---------------------------------------------------------------------------

def test_combined_score_hard_fail_p1_zero(evaluator):
    # Hard fail: p1=0 → base=50 (0*0.5 + 100*0.5), capped at 60 → 50
    result = evaluator.combined_score(0.0, 100.0, tool_call_valid=True)
    assert result == 50.0


# Test 8d: combined_score — malus when p1 < 40
# ---------------------------------------------------------------------------

def test_combined_score_malus_p1_below_40(evaluator):
    # p1=30, p2=100, tool_call_valid=True → base 30*0.5 + 100*0.5 = 65 - 10 = 55
    result = evaluator.combined_score(30.0, 100.0, tool_call_valid=True)
    assert result == 55.0


# Test 8e: combined_score — malus when p1 < 60 (but >= 40)
# ---------------------------------------------------------------------------

def test_combined_score_malus_p1_below_60(evaluator):
    # p1=50, p2=100, tool_call_valid=True → base 50*0.5 + 100*0.5 = 75 - 3 = 72
    result = evaluator.combined_score(50.0, 100.0, tool_call_valid=True)
    assert result == 72.0


# Test 8f: combined_score — no malus when p1 >= 60
# ---------------------------------------------------------------------------

def test_combined_score_no_malus_p1_above_60(evaluator):
    # p1=70, p2=80, tool_call_valid=True → base 70*0.5 + 80*0.5 = 75 + 0 = 75
    result = evaluator.combined_score(70.0, 80.0, tool_call_valid=True)
    assert result == 75.0


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
# Test 10: http_fetch P1 — usable content → 100 pts
# ---------------------------------------------------------------------------

def test_phase1_http_fetch_with_usable_content(evaluator):
    # tool type correct (40) + status 200 (40) + content ≥100 chars (20) = 100
    transcript = {
        "tool_type_called": "fetch",
        "status": "success",
        "status_code": 200,
        "content_excerpt": "A" * 150,
        "provider": "mock",
    }
    score = evaluator.score_phase1(transcript, ASSET_002, excerpt_quality="full")
    assert score == 100.0


# ---------------------------------------------------------------------------
# Test 11: http_fetch P1 — empty content → 80 pts
# ---------------------------------------------------------------------------

def test_phase1_http_fetch_empty_content(evaluator):
    # tool type correct (40) + status 200 (40) + content too short (0) = 80
    transcript = {
        "tool_type_called": "fetch",
        "status": "success",
        "status_code": 200,
        "content_excerpt": None,
        "provider": "mock",
    }
    score = evaluator.score_phase1(transcript, ASSET_002)
    assert score == 80.0


# ---------------------------------------------------------------------------
# Test 13: min_length penalty
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
