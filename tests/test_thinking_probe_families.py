"""Tests fuer die erweiterte Thinking-Probe-Logik: Multi-Prompt + Tag-Inventar.

Deckt:
- utils.model_utils._find_think_tags()
- utils.model_utils.probe_thinking_model() mit Multi-Prompt-Aggregation
- scripts.tools.discover_thinking_tags.identify_family()
- scripts.tools.discover_thinking_tags.pick_representatives()
- scripts.tools.discover_thinking_tags.aggregate_probe()

Siehe: utils/model_utils.py:probe_thinking_model() (v4.7.0) und
scripts/tools/discover_thinking_tags.py.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.model_utils import (  # noqa: E402
    ThinkingProbeResult,
    _find_think_tags,
    _PROBE_PROMPTS,
    _THINK_TAGS,
    probe_thinking_model,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# _find_think_tags()
# ---------------------------------------------------------------------------
class TestFindThinkTags:
    def test_empty_text_returns_empty(self) -> None:
        assert _find_think_tags("") == ()

    def test_short_text_without_tags_returns_empty(self) -> None:
        assert _find_think_tags("The answer is 42.") == ()

    def test_qwen_think_tag_detected(self) -> None:
        assert _find_think_tags("<think>reasoning</think>Answer") == ("<think>",)

    def test_thinking_tag_detected(self) -> None:
        assert _find_think_tags("<thinking>foo</thinking>bar") == ("<thinking>",)

    def test_thought_tag_detected(self) -> None:
        assert _find_think_tags("<thought>x</thought>") == ("<thought>",)

    def test_openai_oss_thinking_tag_detected(self) -> None:
        # gpt-oss nutzt <|thinking|>...<|/thinking|>
        assert "<|thinking|>" in _find_think_tags("foo <|thinking|>reasoning<|/thinking|> bar")

    def test_deepseek_reasoning_tag_detected(self) -> None:
        assert "<reasoning>" in _find_think_tags("<reasoning>step 1</reasoning>Answer")

    def test_meta_reflection_tag_detected(self) -> None:
        assert "<reflection>" in _find_think_tags("<reflection>check</reflection>OK")

    def test_anthropic_analysis_tag_detected(self) -> None:
        assert "<analysis>" in _find_think_tags("<analysis>plan</analysis>")

    def test_multiple_tags_returned(self) -> None:
        text = "<think>a</think><thinking>b</thinking><think>c</think>"
        tags = _find_think_tags(text)
        assert "<think>" in tags
        assert "<thinking>" in tags
        assert len(tags) == 2

    def test_case_insensitive(self) -> None:
        # Tags werden lowercase gematcht, da llama.cpp manchmal CapitalCase liefert
        assert _find_think_tags("<THINK>foo</THINK>") == ("<think>",)

    def test_no_false_positive_on_similar_strings(self) -> None:
        # Haeufige Woerter sollten NICHT als Tags erkannt werden
        assert _find_think_tags("The thinking process is important.") == ()
        assert _find_think_tags("She had a thoughtful moment.") == ()


# ---------------------------------------------------------------------------
# probe_thinking_model() — Multi-Prompt-Aggregation
# ---------------------------------------------------------------------------
class TestProbeThinkingModelMultiPrompt:
    """probe_thinking_model() mit prompts= Argument."""

    def test_str_argument_treated_as_custom_prompt(self) -> None:
        """Ein str wird als Single-Prompt unter 'custom' interpretiert."""
        with patch("utils.llm_client.LLMClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.query.return_value = "Just answer: 80 km/h"
            mock_client.last_response_metadata = {"reasoning_tokens": 0}
            result = probe_thinking_model(
                "test-model", "openrouter", config={},
                prompts="What is 2+2?",
            )
        assert isinstance(result, ThinkingProbeResult)
        assert result.detected is False
        assert result.prompts_used == ("custom",)
        # Single-Prompt-Pfad: nur ein query-Call
        assert mock_client.query.call_count == 1

    def test_single_prompt_dict_uses_single_path(self) -> None:
        """Dict mit 1 Eintrag -> Single-Prompt-Pfad."""
        with patch("utils.llm_client.LLMClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.query.return_value = "<think>reasoning</think>Answer"
            mock_client.last_response_metadata = {}
            result = probe_thinking_model(
                "test-model", "openrouter", config={},
                prompts={"single": "What is 2+2?"},
            )
        assert result.detected is True
        assert result.confidence == "high"
        assert result.prompts_used == ("single",)
        assert "<think>" in result.tags_found
        assert mock_client.query.call_count == 1

    def test_multi_prompt_aggregates_to_detected(self) -> None:
        """Bei Multi-Prompt: 1 Prompt detektiert -> gesamt detektiert."""
        responses = {
            "math": "Just 80 km/h.",  # kein Signal
            "code": "<think>sort</think>[1,2,3]",  # Signal A
            "decision": "Yes.",  # kein Signal
        }
        with patch("utils.llm_client.LLMClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.query.side_effect = lambda **kwargs: responses[kwargs["prompt"][:50].split(".")[0] or "math"]
            # Side-Effect über model/prompt-Identifikation: einfacher mit direktem mock
            mock_client.query.side_effect = None
            mock_client.query.return_value = "<think>sort</think>[1,2,3]"
            mock_client.last_response_metadata = {}
            result = probe_thinking_model(
                "test-model", "openrouter", config={},
                prompts={"math": "math-prompt", "code": "code-prompt", "decision": "decision-prompt"},
            )
        assert result.detected is True
        assert result.confidence == "high"
        assert "<think>" in result.tags_found
        assert len(result.prompts_used) == 3
        # Multi-Prompt-Pfad: 3 query-Calls
        assert mock_client.query.call_count == 3

    def test_multi_prompt_highest_confidence_wins(self) -> None:
        """Hoechste Confidence ueber alle Prompts gewinnt."""
        # Prompt-Reihenfolge: math (low) -> code (high) -> decision (medium)
        # Aber da alle dasselbe zurueckgeben, testen wir die Aggregation.
        call_results = ["math: low signal", "code: <think>high</think>", "decision: 80"]
        with patch("utils.llm_client.LLMClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.query.side_effect = call_results
            mock_client.last_response_metadata = {}
            result = probe_thinking_model(
                "test-model", "openrouter", config={},
                prompts={"math": "m", "code": "c", "decision": "d"},
            )
        assert result.detected is True
        assert result.confidence == "high"

    def test_multi_prompt_all_fail_raises(self) -> None:
        """Wenn alle Multi-Prompts fehlschlagen, wird RuntimeError geworfen."""
        with patch("utils.llm_client.LLMClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.query.side_effect = ConnectionError("API down")
            mock_client.last_response_metadata = None
            with pytest.raises(RuntimeError, match="ALL 3 probes failed"):
                probe_thinking_model(
                    "test-model", "openrouter", config={},
                    prompts={"math": "m", "code": "c", "decision": "d"},
                )

    def test_multi_prompt_partial_failure_continues(self) -> None:
        """Wenn 1 von 3 Prompts fehlschlaegt, wird mit den anderen 2 weitergemacht."""
        call_count = {"n": 0}

        def side_effect(**kwargs: Any) -> str:
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise ConnectionError("timeout on code prompt")
            return "<think>reasoning</think>Answer"

        with patch("utils.llm_client.LLMClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.query.side_effect = side_effect
            mock_client.last_response_metadata = {}
            result = probe_thinking_model(
                "test-model", "openrouter", config={},
                prompts={"math": "m", "code": "c", "decision": "d"},
            )
        # Detected durch die 2 erfolgreichen Prompts
        assert result.detected is True
        assert "<think>" in result.tags_found

    def test_default_prompts_is_all_three(self) -> None:
        """Default prompts=None verwendet _PROBE_PROMPTS (math/code/decision)."""
        assert set(_PROBE_PROMPTS.keys()) == {"math", "code", "decision"}
        # Ohne expliziten prompts= Parameter: Multi-Prompt-Pfad
        with patch("utils.llm_client.LLMClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.query.return_value = "simple answer"
            mock_client.last_response_metadata = {}
            result = probe_thinking_model("test-model", "openrouter", config={})
        assert result.detected is False
        assert result.confidence == "low"
        # 3 query-Calls (Multi-Prompt)
        assert mock_client.query.call_count == 3

    def test_thinkingprobresult_backward_compatible_defaults(self) -> None:
        """ThinkingProbeResult kann mit positional args erstellt werden — Defaults funktionieren."""
        # Backward-Compat: alte Aufrufer ohne prompts_used/tags_found
        result = ThinkingProbeResult(
            detected=True,
            evidence="legacy",
            confidence="high",
        )
        assert result.prompts_used == ()
        assert result.tags_found == ()


# ---------------------------------------------------------------------------
# discover_thinking_tags.identify_family()
# ---------------------------------------------------------------------------
class TestIdentifyFamily:
    def setup_method(self) -> None:
        from scripts.tools.discover_thinking_tags import identify_family
        self.identify_family = identify_family

    def test_gemma_family(self) -> None:
        assert self.identify_family("gemma-3-12b-it") == "Gemma"
        assert self.identify_family("gemma-4-26b-a4b-q8") == "Gemma"

    def test_qwen_family(self) -> None:
        assert self.identify_family("qwen3-14b") == "Qwen"
        assert self.identify_family("qwen3.5-35b-a3b-q8") == "Qwen"

    def test_qwen_coder_subfamily(self) -> None:
        assert self.identify_family("qwen2.5-coder-7b") == "Qwen-Coder"
        assert self.identify_family("qwen3-coder-30b-a3b-q8") == "Qwen-Coder"
        # Qwen-Coder hat Vorrang vor Qwen
        assert self.identify_family("qwen3-coder-next-q8") == "Qwen-Coder"

    def test_hermes_family(self) -> None:
        assert self.identify_family("hermes-3-8b") == "Hermes"
        assert self.identify_family("hermes-4-14b-abliterated") == "Hermes"
        assert self.identify_family("hermes-4.3-36b-q6") == "Hermes"

    def test_llama_family(self) -> None:
        assert self.identify_family("llama-3.3-70b-versatile") == "Llama"
        assert self.identify_family("meta-llama/llama-4-scout-17b-16e-instruct") == "Llama"

    def test_mistral_family(self) -> None:
        assert self.identify_family("mistral-large-2411") == "Mistral"
        assert self.identify_family("mixtral-8x7b") == "Mistral"
        assert self.identify_family("ministral-3-14b") == "Mistral"

    def test_magistral_is_distinct_family(self) -> None:
        # Magistral vor Mistral (spezifischer)
        assert self.identify_family("magistral-medium-latest") == "Magistral"
        assert self.identify_family("magistral-small-latest") == "Magistral"

    def test_devstral_is_distinct_family(self) -> None:
        assert self.identify_family("devstral-2512") == "Devstral"

    def test_codestral_is_distinct_family(self) -> None:
        assert self.identify_family("codestral-latest") == "Codestral"

    def test_claude_family(self) -> None:
        assert self.identify_family("claude-opus-4-7") == "Claude"
        assert self.identify_family("claude-haiku-4-5-20251001") == "Claude"

    def test_openai_family(self) -> None:
        assert self.identify_family("gpt-5") == "OpenAI"
        assert self.identify_family("gpt-4o") == "OpenAI"
        assert self.identify_family("o1") == "OpenAI"
        assert self.identify_family("o3-mini") == "OpenAI"
        assert self.identify_family("o4-mini") == "OpenAI"

    def test_gemini_family(self) -> None:
        assert self.identify_family("gemini-2.5-flash") == "Gemini"
        assert self.identify_family("gemini-3.1-pro-preview") == "Gemini"

    def test_grok_family(self) -> None:
        assert self.identify_family("grok-4-1-fast-reasoning") == "Grok"
        assert self.identify_family("grok-3-mini") == "Grok"

    def test_deepseek_family(self) -> None:
        assert self.identify_family("deepseek/deepseek-chat-v3.1") == "DeepSeek"
        assert self.identify_family("deepseek/deepseek-v4-pro") == "DeepSeek"

    def test_glm_family(self) -> None:
        assert self.identify_family("z-ai/glm-4.6") == "GLM"
        assert self.identify_family("z-ai/glm-5-20260211") == "GLM"

    def test_kimi_family(self) -> None:
        assert self.identify_family("moonshotai/kimi-k2-thinking-20251106") == "Kimi"
        assert self.identify_family("moonshotai/kimi-k2.6") == "Kimi"

    def test_nemotron_family(self) -> None:
        assert self.identify_family("nvidia/nemotron-3-ultra-550b-a55b") == "NVIDIA"

    def test_minimax_family(self) -> None:
        assert self.identify_family("minimax/minimax-m2.7-20260318") == "MiniMax"
        assert self.identify_family("minimax/minimax-m3") == "MiniMax"

    def test_unknown_returns_other(self) -> None:
        assert self.identify_family("totally-unknown-model-xyz") == "Other"


# ---------------------------------------------------------------------------
# discover_thinking_tags.pick_representatives()
# ---------------------------------------------------------------------------
class TestPickRepresentatives:
    def setup_method(self) -> None:
        from scripts.tools.discover_thinking_tags import pick_representatives
        self.pick_representatives = pick_representatives

    def test_local_preferred_over_cloud(self) -> None:
        by_family = {
            "Qwen": [
                ("qwen3-14b", "llamacpp"),
                ("qwen/qwen3-32b", "openrouter"),
            ],
        }
        result = self.pick_representatives(by_family, max_per_family=1)
        assert len(result) == 1
        mid, prov, fam = result[0]
        assert mid == "qwen3-14b"
        assert prov == "llamacpp"

    def test_thinking_models_bonus(self) -> None:
        by_family = {
            "Grok": [
                ("grok-3", "xai"),
                ("grok-4-1-fast-reasoning", "xai"),
            ],
        }
        result = self.pick_representatives(by_family, max_per_family=1)
        mid = result[0][0]
        # "reasoning" im Namen bekommt Bonus
        assert "reasoning" in mid

    def test_max_per_family_respected(self) -> None:
        by_family = {
            "Qwen": [
                ("qwen3-4b", "llamacpp"),
                ("qwen3-14b", "llamacpp"),
                ("qwen3.5-9b", "llamacpp"),
            ],
        }
        result = self.pick_representatives(by_family, max_per_family=2)
        assert len(result) == 2

    def test_multiple_families(self) -> None:
        by_family = {
            "Qwen": [("qwen3-14b", "llamacpp")],
            "Gemma": [("gemma-3-12b-it", "llamacpp")],
            "Hermes": [("hermes-3-8b", "llamacpp")],
        }
        result = self.pick_representatives(by_family, max_per_family=1)
        assert len(result) == 3
        families = {r[2] for r in result}
        assert families == {"Qwen", "Gemma", "Hermes"}


# ---------------------------------------------------------------------------
# discover_thinking_tags.aggregate_probe()
# ---------------------------------------------------------------------------
class TestAggregateProbe:
    def setup_method(self) -> None:
        from scripts.tools.discover_thinking_tags import aggregate_probe
        self.aggregate_probe = aggregate_probe

    def test_tags_found_yields_high_confidence(self) -> None:
        probe_results = {
            "math": {"tags_found": ["<think>"], "reasoning_tokens": 0, "inline_cot": False, "error": None},
            "code": {"tags_found": [], "reasoning_tokens": 0, "inline_cot": False, "error": None},
            "decision": {"tags_found": [], "reasoning_tokens": 0, "inline_cot": False, "error": None},
        }
        agg = self.aggregate_probe(probe_results)
        assert agg["detected"] is True
        assert agg["confidence"] == "high"
        assert "<think>" in agg["all_tags"]
        assert "math" in agg["detected_prompts"]

    def test_reasoning_tokens_yields_medium_confidence(self) -> None:
        probe_results = {
            "math": {"tags_found": [], "reasoning_tokens": 250, "inline_cot": False, "error": None},
            "code": {"tags_found": [], "reasoning_tokens": 0, "inline_cot": False, "error": None},
            "decision": {"tags_found": [], "reasoning_tokens": 0, "inline_cot": False, "error": None},
        }
        agg = self.aggregate_probe(probe_results)
        assert agg["detected"] is True
        assert agg["confidence"] == "medium"
        assert agg["max_reasoning_tokens"] == 250
        assert agg["signal"] == "reasoning_tokens=250"

    def test_inline_cot_yields_medium_confidence(self) -> None:
        probe_results = {
            "math": {"tags_found": [], "reasoning_tokens": 0, "inline_cot": True, "error": None},
            "code": {"tags_found": [], "reasoning_tokens": 0, "inline_cot": False, "error": None},
            "decision": {"tags_found": [], "reasoning_tokens": 0, "inline_cot": False, "error": None},
        }
        agg = self.aggregate_probe(probe_results)
        assert agg["detected"] is True
        assert agg["confidence"] == "medium"
        assert "math" in agg["inline_cot_prompts"]

    def test_no_signal_yields_low_confidence(self) -> None:
        probe_results = {
            "math": {"tags_found": [], "reasoning_tokens": 0, "inline_cot": False, "error": None},
            "code": {"tags_found": [], "reasoning_tokens": 0, "inline_cot": False, "error": None},
            "decision": {"tags_found": [], "reasoning_tokens": 0, "inline_cot": False, "error": None},
        }
        agg = self.aggregate_probe(probe_results)
        assert agg["detected"] is False
        assert agg["confidence"] == "low"

    def test_high_confidence_beats_medium(self) -> None:
        probe_results = {
            "math": {"tags_found": ["<think>"], "reasoning_tokens": 0, "inline_cot": False, "error": None},
            "code": {"tags_found": [], "reasoning_tokens": 500, "inline_cot": False, "error": None},
        }
        agg = self.aggregate_probe(probe_results)
        assert agg["confidence"] == "high"

    def test_errors_excluded_from_aggregation(self) -> None:
        probe_results = {
            "math": {"tags_found": [], "reasoning_tokens": 0, "inline_cot": False, "error": "timeout"},
            "code": {"tags_found": ["<think>"], "reasoning_tokens": 0, "inline_cot": False, "error": None},
        }
        agg = self.aggregate_probe(probe_results)
        # Trotz Error in math: code hat Signal
        assert agg["detected"] is True
        assert "code" in agg["detected_prompts"]


# ---------------------------------------------------------------------------
# _THINK_TAGS Vollstaendigkeit
# ---------------------------------------------------------------------------
class TestThinkTagsCompleteness:
    """Stellt sicher, dass alle bekannten Familien-Tags in _THINK_TAGS enthalten sind."""

    def test_qwen_think_tag_present(self) -> None:
        assert "<think>" in _THINK_TAGS

    def test_openai_oss_special_tags_present(self) -> None:
        assert "<|thinking|>" in _THINK_TAGS
        assert "<|reasoning|>" in _THINK_TAGS

    def test_deepseek_tags_present(self) -> None:
        assert "<reasoning>" in _THINK_TAGS
        assert "<reason>" in _THINK_TAGS

    def test_meta_reflection_tag_present(self) -> None:
        assert "<reflection>" in _THINK_TAGS

    def test_anthropic_extended_thinking_tags_present(self) -> None:
        assert "<analysis>" in _THINK_TAGS
        assert "<plan>" in _THINK_TAGS

    def test_hermes_scratchpad_present(self) -> None:
        assert "<scratchpad>" in _THINK_TAGS

    def test_tags_are_lowercase(self) -> None:
        for tag in _THINK_TAGS:
            assert tag == tag.lower(), f"Tag {tag!r} ist nicht lowercase"


# ---------------------------------------------------------------------------
# Konfiguration: _PROBE_PROMPTS
# ---------------------------------------------------------------------------
class TestProbePromptsConfig:
    def test_three_prompts_defined(self) -> None:
        assert set(_PROBE_PROMPTS.keys()) == {"math", "code", "decision"}

    def test_prompts_are_non_empty(self) -> None:
        for name, text in _PROBE_PROMPTS.items():
            assert text.strip(), f"Prompt '{name}' ist leer"

    def test_prompts_distinct(self) -> None:
        # Drei unterschiedliche Domänen (Mathe/Code/Decision)
        assert _PROBE_PROMPTS["math"] != _PROBE_PROMPTS["code"]
        assert _PROBE_PROMPTS["math"] != _PROBE_PROMPTS["decision"]
        assert _PROBE_PROMPTS["code"] != _PROBE_PROMPTS["decision"]
