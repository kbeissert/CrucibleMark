"""Tests für Connector-Fix: think_content wird als <think>-Block in model_response gewrappt.

Der Judge-Prompt bleibt unverändert — nur die model_response wird im Connector
(_build_judge_kwargs) angereichert, sodass der Judge das Thinking als Teil der
Response in bekannten <think>-Tags sieht.
"""
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from utils.scoring.llm_judge.judge_prompt_builder import build_prompts


class TestConnectorThinkWrapping:
    """Tests für _build_judge_kwargs: think_content wird in <think>-Tags gewrappt."""

    def _make_result(self, think_content=None, **overrides):
        result = {
            "model": "test-model",
            "asset_id": "test_001",
            "execution_time": 1.0,
            "tokens_used": 500,
            "reasoning_tokens": 300,
            "token_limit_used": 8000,
        }
        if think_content is not None:
            result["think_content"] = think_content
        result.update(overrides)
        return result

    def _make_asset_data(self):
        return {
            "prompt": "Write a greeting.",
            "golden_standard": "Hello!",
            "metadata": {"language": "en", "language_weight": 0.2},
            "scoring": {},
        }

    def test_think_content_wrapped_in_think_tags(self):
        """think_content present → model_response contains <think> block before visible answer."""
        from utils.scoring.judge_evaluator import _build_judge_kwargs

        result = self._make_result(think_content="Let me think about this...")
        kwargs = _build_judge_kwargs(
            result=result,
            response="Hello!",
            asset_data=self._make_asset_data(),
            eval_module_id="cultural_intelligence",
            model="test-model",
            asset_cfg=None,
            provider=None,
        )
        model_response = kwargs["model_response"]
        assert "<think>" in model_response
        assert "</think>" in model_response
        assert "Let me think about this..." in model_response
        assert "Hello!" in model_response
        # <think> block must come BEFORE the visible response
        idx_think = model_response.index("<think>")
        idx_response = model_response.index("Hello!")
        assert idx_think < idx_response

    def test_no_think_content_no_wrapping(self):
        """No think_content → model_response is just the visible response, no <think> tags."""
        from utils.scoring.judge_evaluator import _build_judge_kwargs

        result = self._make_result()
        kwargs = _build_judge_kwargs(
            result=result,
            response="Hello!",
            asset_data=self._make_asset_data(),
            eval_module_id="cultural_intelligence",
            model="test-model",
            asset_cfg=None,
            provider=None,
        )
        assert kwargs["model_response"] == "Hello!"
        assert "<think>" not in kwargs["model_response"]

    def test_empty_think_content_no_wrapping(self):
        """Empty think_content → no wrapping."""
        from utils.scoring.judge_evaluator import _build_judge_kwargs

        result = self._make_result(think_content="")
        kwargs = _build_judge_kwargs(
            result=result,
            response="Hello!",
            asset_data=self._make_asset_data(),
            eval_module_id="cultural_intelligence",
            model="test-model",
            asset_cfg=None,
            provider=None,
        )
        assert kwargs["model_response"] == "Hello!"

    def test_whitespace_think_content_no_wrapping(self):
        """Whitespace-only think_content → no wrapping."""
        from utils.scoring.judge_evaluator import _build_judge_kwargs

        result = self._make_result(think_content="   \n  \t  ")
        kwargs = _build_judge_kwargs(
            result=result,
            response="Hello!",
            asset_data=self._make_asset_data(),
            eval_module_id="cultural_intelligence",
            model="test-model",
            asset_cfg=None,
            provider=None,
        )
        assert kwargs["model_response"] == "Hello!"

    def test_think_tags_survive_normalize_response(self):
        """<think> tags in model_response must survive _normalize_response in build_prompts."""
        wrapped = "<think>\nInternal reasoning here.\n</think>\n\nVisible answer."
        _, user_prompt = build_prompts(
            task_prompt="test",
            model_response=wrapped,
            golden_standard="ref",
            module_id="cultural_intelligence",
            scale=5,
        )
        assert "<think>" in user_prompt
        assert "</think>" in user_prompt
        assert "Internal reasoning here." in user_prompt
        assert "Visible answer." in user_prompt

    def test_think_wrapping_for_all_modules(self):
        """think_content wrapping works for ALL modules, not just reasoning."""
        from utils.scoring.judge_evaluator import _build_judge_kwargs

        for module_id in [
            "cultural_intelligence", "code_quality", "ux_writing",
            "documentation_quality", "content_transformation", "cli_benchmark",
            "reasoning",
        ]:
            result = self._make_result(think_content="Thinking for " + module_id)
            kwargs = _build_judge_kwargs(
                result=result,
                response="Answer",
                asset_data=self._make_asset_data(),
                eval_module_id=module_id,
                model="test-model",
                asset_cfg=None,
                provider=None,
            )
            assert "<think>" in kwargs["model_response"], (
                f"think_content not wrapped for module {module_id}"
            )


class TestJudgePromptUnchanged:
    """Verify the judge prompt builder is back to original state (no think_content param)."""

    def test_build_prompts_signature_has_no_think_content(self):
        """build_prompts must NOT accept think_content parameter."""
        import inspect
        from utils.scoring.llm_judge.judge_prompt_builder import build_prompts
        sig = inspect.signature(build_prompts)
        assert "think_content" not in sig.parameters

    def test_reasoning_tokens_shown_in_token_usage(self):
        """_format_token_usage_lines must show reasoning_tokens (original behavior restored)."""
        from utils.scoring.llm_judge.judge_prompt_builder import _format_token_usage_lines

        ctx = {
            "tokens_used": 1196,
            "reasoning_tokens": 976,
            "token_budget": 8000,
        }
        lines = _format_token_usage_lines(ctx)
        joined = "\n".join(lines)
        assert "976" in joined, "reasoning_tokens count must be shown"
        assert "reasoning tokens" in joined.lower(), "reasoning_tokens label must be shown"

    def test_thinking_bullet_in_token_usage_guidance(self):
        """_append_token_usage_block must contain thinking-tokens bullet (original restored)."""
        from utils.scoring.llm_judge.judge_prompt_builder import _append_token_usage_block

        result = _append_token_usage_block("Base.", {"tokens_used": 100, "token_budget": 1000})
        assert "thinking tokens are very high" in result


class TestReasoningTraceNote:
    """Tests für den konditionalen REASONING TRACE NOTE-Block."""

    def _base_kwargs(self):
        return {
            "task_prompt": "test",
            "model_response": "Hello!",
            "golden_standard": "ref",
            "module_id": "cultural_intelligence",
            "scale": 5,
        }

    def test_reasoning_trace_note_added_when_flag_true(self):
        """reasoning_trace_context=True → System-Prompt enthält REASONING TRACE NOTE."""
        system_prompt, _ = build_prompts(**self._base_kwargs(), reasoning_trace_context=True)
        assert "REASONING TRACE NOTE" in system_prompt
        assert "NOT part of the user-facing output" in system_prompt

    def test_reasoning_trace_note_absent_when_flag_false(self):
        """reasoning_trace_context=False → kein REASONING TRACE NOTE-Block."""
        system_prompt, _ = build_prompts(**self._base_kwargs(), reasoning_trace_context=False)
        assert "REASONING TRACE NOTE" not in system_prompt

    def test_reasoning_trace_note_absent_by_default(self):
        """Ohne Parameter → kein REASONING TRACE NOTE-Block (Non-Thinking-Modelle)."""
        system_prompt, _ = build_prompts(**self._base_kwargs())
        assert "REASONING TRACE NOTE" not in system_prompt

    def test_reasoning_trace_note_references_think_tag(self):
        """Block-Text referenziert <think> und </think>."""
        system_prompt, _ = build_prompts(**self._base_kwargs(), reasoning_trace_context=True)
        assert "<think>" in system_prompt
        assert "</think>" in system_prompt

    def test_reasoning_trace_note_references_token_usage(self):
        """Block-Text referenziert 'Thinking / reasoning tokens' aus dem TOKEN USAGE-Block."""
        system_prompt, _ = build_prompts(**self._base_kwargs(), reasoning_trace_context=True)
        assert "Thinking / reasoning tokens" in system_prompt

    def test_build_judge_kwargs_sets_flag_when_think_content(self):
        """_build_judge_kwargs mit think_content → reasoning_trace_context=True."""
        from utils.scoring.judge_evaluator import _build_judge_kwargs

        result = {
            "model": "test-model",
            "asset_id": "test_001",
            "execution_time": 1.0,
            "tokens_used": 500,
            "reasoning_tokens": 300,
            "token_limit_used": 8000,
            "think_content": "Let me reason about this...",
        }
        asset_data = {
            "prompt": "Write a greeting.",
            "golden_standard": "Hello!",
            "metadata": {"language": "en", "language_weight": 0.2},
            "scoring": {},
        }
        kwargs = _build_judge_kwargs(
            result=result,
            response="Hello!",
            asset_data=asset_data,
            eval_module_id="cultural_intelligence",
            model="test-model",
            asset_cfg=None,
            provider=None,
        )
        assert kwargs.get("reasoning_trace_context") is True

    def test_build_judge_kwargs_no_flag_without_think_content(self):
        """_build_judge_kwargs ohne think_content → kein reasoning_trace_context-Key."""
        from utils.scoring.judge_evaluator import _build_judge_kwargs

        result = {
            "model": "test-model",
            "asset_id": "test_001",
            "execution_time": 1.0,
            "tokens_used": 500,
            "reasoning_tokens": 0,
            "token_limit_used": 8000,
        }
        asset_data = {
            "prompt": "Write a greeting.",
            "golden_standard": "Hello!",
            "metadata": {"language": "en", "language_weight": 0.2},
            "scoring": {},
        }
        kwargs = _build_judge_kwargs(
            result=result,
            response="Hello!",
            asset_data=asset_data,
            eval_module_id="cultural_intelligence",
            model="test-model",
            asset_cfg=None,
            provider=None,
        )
        assert "reasoning_trace_context" not in kwargs

    def test_build_judge_kwargs_no_flag_empty_think_content(self):
        """_build_judge_kwargs mit leerem think_content → kein Flag."""
        from utils.scoring.judge_evaluator import _build_judge_kwargs

        result = {
            "model": "test-model",
            "asset_id": "test_001",
            "execution_time": 1.0,
            "tokens_used": 500,
            "reasoning_tokens": 0,
            "token_limit_used": 8000,
            "think_content": "",
        }
        asset_data = {
            "prompt": "Write a greeting.",
            "golden_standard": "Hello!",
            "metadata": {"language": "en", "language_weight": 0.2},
            "scoring": {},
        }
        kwargs = _build_judge_kwargs(
            result=result,
            response="Hello!",
            asset_data=asset_data,
            eval_module_id="cultural_intelligence",
            model="test-model",
            asset_cfg=None,
            provider=None,
        )
        assert "reasoning_trace_context" not in kwargs
