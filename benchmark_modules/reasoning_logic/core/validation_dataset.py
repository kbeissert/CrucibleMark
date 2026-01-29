#!/usr/bin/env python3
"""
Ground Truth Dataset for Metacognition Assets.

Provides gold-standard responses with validated scores for reproducibility
and inter-rater reliability validation.
"""

GROUND_TRUTH_METACOG_001 = {
    "asset_id": "asset_metacog_001",
    "test_name": "The Sheep Trap (Self-Correction)",
    "instructions": {
        "setup": "A farmer has 17 sheep. All but 9 die. How many are left?",
        "expected_answer": "9",
        "evaluation_criteria": {
            "self_correction": "Model must catch the '17-9=8' trap",
            "linguistic_analysis": "Model must explain 'all but 9' phrase",
            "output_correctness": "Final answer must be 9"
        }
    },
    "gold_responses": {
        "perfect": {
            "text": """<thought>
Wait, let me think about this carefully. The trap here is that "all but 9 die" is a linguistic trick. 
If all but 9 sheep die, that means 9 survive. Not 17-9=8 like I might initially think. 
The number 17 is irrelevant - the phrase "all but 9" directly tells us that 9 remain.
</thought>

Answer: 9 sheep""",
            "expected_score": 80,  # 20 (explicit keyword but no full layers) + 20 (phrase + meaning) + 30 (output)
            "scoring_breakdown": {
                "self_correction": 20,  # Explicit "wait" keyword but "17-9=8" is mentioned negatively, not trajectory
                "linguistic_analysis": 20,  # Phrase mentioned + semantic meaning + "not 17-9=8" contrast logic
                "output_correctness": 30,  # Correct answer
            },
            "evidence": [
                "explicit_correction_keyword: 'wait'",
                "semantic_explanation_partial: 'all but 9 means 9 survive'",
                "correct_answer: '9'"
            ]
        },
        "good": {
            "text": """<thought>
The phrase "all but 9" means that 9 sheep survive. So if all but 9 die, 
then 9 are left alive. The 17 is a distraction.
</thought>

Answer: 9""",
            "expected_score": 60,  # 0 (no explicit correction) + 30 (linguistic) + 30 (output)
            "scoring_breakdown": {
                "self_correction": 0,   # No explicit self-correction
                "linguistic_analysis": 30,  # Explicit explanation of phrase
                "output_correctness": 30,  # Correct answer
            },
            "evidence": [
                "semantic_explanation: 'all but 9 means 9 sheep survive'",
                "correct_answer: '9'"
            ]
        },
        "minimal": {
            "text": "All but 9 survive. Answer: 9",
            "expected_score": 40,  # 0 + 10 (phrase mentioned only) + 30
            "scoring_breakdown": {
                "self_correction": 0,   # No correction shown
                "linguistic_analysis": 10,  # Phrase mentioned but NOT explained (no "means" etc)
                "output_correctness": 30,  # Correct answer
            },
            "evidence": [
                "phrase_mentioned_but_not_explained: 'all but 9 survive'",
                "correct_answer: '9'"
            ]
        },
        "wrong": {
            "text": "17 - 9 = 8. Answer: 8",
            "expected_score": 0,  # No correction, wrong answer
            "scoring_breakdown": {
                "self_correction": 0,
                "linguistic_analysis": 0,  # "all but 9" not mentioned
                "output_correctness": 0,  # Wrong answer (8, not 9)
            },
            "evidence": ["incorrect_answer: '8' (expected '9')"]
        }
    }
}

GROUND_TRUTH_METACOG_002 = {
    "asset_id": "asset_metacog_002",
    "test_name": "The Green Sky (False Premise Challenge)",
    "instructions": {
        "setup": "The question assumes: 'The sky is green. Why?' Reject this premise.",
        "expected_answer": "The sky is blue (or equivalent rejection)",
        "evaluation_criteria": {
            "premise_challenge": "Must identify the false premise explicitly",
            "factual_correction": "Must state sky is blue with physics explanation",
            "thought_quality": "Quality of reasoning about the false premise"
        }
    },
    "gold_responses": {
        "perfect": {
            "text": """<thought>
The question assumes the sky is green, but this is a false premise. 
The sky is actually blue due to Rayleigh scattering - shorter wavelengths of light
(like blue) scatter more than longer wavelengths in the atmosphere.
</thought>

The sky is blue, not green. The premise of the question is incorrect.""",
            "expected_score": 100,  # 50 + 30 + 20 (thought quality bonus)
            "scoring_breakdown": {
                "premise_challenge": 50,  # Explicitly identifies false premise
                "factual_correction": 30,  # Correct fact with Rayleigh explanation
                "thought_quality": 20,  # Substantive reasoning
            },
            "evidence": [
                "explicit_premise_rejection: 'question assumes the sky is green'",
                "physics_explanation: 'Rayleigh scattering'",
                "wavelength_context: 'shorter wavelengths scatter more'"
            ]
        },
        "good": {
            "text": """<thought>
This question is based on a false assumption. The sky is not green - it's blue 
because of how light scatters in the atmosphere.
</thought>

The sky is blue.""",
            "expected_score": 70,  # 50 + 20 (generic scatter) + 0 (brief thought)
            "scoring_breakdown": {
                "premise_challenge": 50,  # Explicitly rejects false premise
                "factual_correction": 20,  # Generic scatter explanation (not full physics)
                "thought_quality": 0,   # Brief thought
            },
            "evidence": [
                "explicit_premise_rejection: 'based on false assumption'",
                "generic_physics: 'light scatters in atmosphere'"
            ]
        },
        "minimal": {
            "text": "The sky is blue.",
            "expected_score": 15,  # 0 + 15 (fact only) + 0
            "scoring_breakdown": {
                "premise_challenge": 0,   # Doesn't identify false premise explicitly
                "factual_correction": 15,  # States correct fact without explanation
                "thought_quality": 0,   # No thought provided
            },
            "evidence": [
                "correct_fact: 'sky is blue'",
                "missing_premise_rejection",
                "missing_physics_explanation"
            ]
        },
        "wrong": {
            "text": "The sky is green because of gases in the atmosphere.",
            "expected_score": 0,  # 0 + 0 + 0
            "scoring_breakdown": {
                "premise_challenge": 0,
                "factual_correction": 0,
                "thought_quality": 0,
            },
            "evidence": ["incorrect_fact: accepts false premise"]
        }
    }
}

GROUND_TRUTH_DATASETS = {
    "asset_metacog_001": GROUND_TRUTH_METACOG_001,
    "asset_metacog_002": GROUND_TRUTH_METACOG_002,
}


def validate_response_against_ground_truth(
    asset_id: str,
    response_type: str,  # "perfect", "good", "minimal", "wrong"
    actual_score: float,
    tolerance: float = 10.0  # Allow ±10 point variance
) -> dict:
    """
    Validate that actual score matches ground truth within tolerance.
    
    Args:
        asset_id: Asset identifier
        response_type: Type of response ("perfect", "good", "minimal", "wrong")
        actual_score: Actual score from evaluator
        tolerance: Acceptable score variance (default: ±10)
    
    Returns:
        Validation result with pass/fail and details
    """
    if asset_id not in GROUND_TRUTH_DATASETS:
        return {
            "success": False,
            "message": f"Asset {asset_id} not in ground truth database"
        }
    
    dataset = GROUND_TRUTH_DATASETS[asset_id]
    
    if response_type not in dataset["gold_responses"]:
        return {
            "success": False,
            "message": f"Response type '{response_type}' not found in {asset_id}"
        }
    
    expected = dataset["gold_responses"][response_type]["expected_score"]
    variance = abs(actual_score - expected)
    passed = variance <= tolerance
    
    return {
        "success": passed,
        "asset_id": asset_id,
        "response_type": response_type,
        "expected_score": expected,
        "actual_score": actual_score,
        "variance": variance,
        "tolerance": tolerance,
        "message": (
            f"✅ PASS" if passed 
            else f"❌ FAIL: Expected {expected}±{tolerance}, got {actual_score}"
        )
    }


if __name__ == "__main__":
    # Display dataset structure
    for asset_id, dataset in GROUND_TRUTH_DATASETS.items():
        print(f"\n{'='*70}")
        print(f"Asset: {dataset['test_name']}")
        print(f"{'='*70}")
        
        for response_type, response_data in dataset["gold_responses"].items():
            print(f"\n{response_type.upper()}: {response_data['expected_score']}pts")
            print(f"  Breakdown: {response_data['scoring_breakdown']}")
            print(f"  Evidence: {response_data['evidence']}")
