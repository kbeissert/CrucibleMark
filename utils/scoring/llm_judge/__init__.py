"""
LLM Judge scoring extension for CrucibleMark.

Public API::

    from utils.scoring.llm_judge import JudgeRunner, LLMJudgeConfig

    config = LLMJudgeConfig.from_dict(yaml_data)
    runner = JudgeRunner(config)
    result = runner.score(task_prompt, model_response, golden_standard, module_id)
"""

from .judge_config import LLMJudgeConfig
from .judge_parser import JudgeResult, parse
from .judge_runner import JudgeRunner
from .providers.base_provider import JudgeProviderResponse, LLMJudgeProvider

__all__ = [
    "JudgeRunner",
    "LLMJudgeConfig",
    "JudgeResult",
    "JudgeProviderResponse",
    "LLMJudgeProvider",
    "parse",
]
