from utils.scoring.llm_judge.judge_prompt_builder import _SYSTEM_TEMPLATE
print(_SYSTEM_TEMPLATE.safe_substitute(domain="Test", scale=5))
