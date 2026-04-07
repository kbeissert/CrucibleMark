from utils.constants import MS_PER_SECOND
import logging
import time
import json
import traceback
from typing import Dict, Any, Optional

from utils.scoring.llm_judge.judge_config import LLMJudgeConfig
from utils.scoring.llm_judge.judge_runner import JudgeRunner
from utils.scoring_utils import calculate_hybrid_score, calculate_score_contributions
from utils.scoring.exceptions import JudgeUnavailableError
from utils.scoring.exceptions import JudgeUnavailableError
from utils.benchmark_utils import save_audit_log

def evaluate_with_judge(
    result: Dict[str, Any],
    response: str,
    asset_data: Dict[str, Any],
    judge_cfg_dict: Dict[str, Any],
    eval_module_id: str,
    model: str,
    asset_cfg: Optional[Dict[str, Any]],
    benchmark_info: Dict[str, Any],
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes the LLM Judge scoring methodology and updates the result dictionary.
    """
    time.sleep(0.5)

    try:
        judge_config = LLMJudgeConfig.from_dict(judge_cfg_dict)
        # Apply optional per-module override
        if asset_cfg and "llm_judge_model" in asset_cfg:
            judge_config.module_judge_model = asset_cfg["llm_judge_model"]
        elif "llm_judge_model" in benchmark_info:
            judge_config.module_judge_model = benchmark_info["llm_judge_model"]

        runner = JudgeRunner(judge_config)

        raw_prompt = asset_data.get("prompt", asset_data.get("instruction", ""))
        golden = asset_data.get("golden_standard", asset_data.get("golden", ""))
        if isinstance(golden, dict):
            # Format dict for the judge as string if text not present
            golden_text = golden.get("text", "")
            if not golden_text:
                import json
                golden_text = json.dumps(golden, indent=2)
            golden = golden_text
        golden = str(golden)

        # Build kwargs for .score(), keeping it provider-agnostic
        required_language = asset_data.get("metadata", {}).get("language")
        language_weight = asset_data.get("metadata", {}).get("language_weight", 0.20)
        kwargs = {
            "task_prompt": raw_prompt,
            "model_response": response,
            "golden_standard": golden,
            "module_id": eval_module_id,
            "rubric_override": asset_data.get("scoring", {}).get("rubric"),
            "tested_model_id": model,
            "response_time_ms": result.get("execution_time", 0) * MS_PER_SECOND,
            "required_language": required_language,
            "language_weight": language_weight,
        }
        if provider:
            kwargs["tested_model_provider"] = provider

        judge_res = runner.score(**kwargs)

        # Merge fields
        result["llm_judge_score"] = judge_res.score
        result["llm_judge_reasoning"] = judge_res.reasoning
        result["llm_judge_latency_ms"] = judge_res.judge_latency_ms
        result["llm_judge_provider_used"] = judge_res.judge_provider_used
        result["llm_judge_model_used"] = judge_res.judge_model_used
        result["llm_judge_parse_success"] = judge_res.parse_success

        # Add sub-scores
        result["judge_task_compliance"] = judge_res.judge_task_compliance
        result["judge_output_quality"] = judge_res.judge_output_quality
        result["judge_standard_adherence"] = judge_res.judge_standard_adherence

        if judge_res.parse_success and judge_res.score is not None:
            judge_scale = judge_config.scoring.scale
            judge_pct = (
                (judge_res.score / judge_scale) * 100
                if judge_scale > 0
                else 0.0
            )

            # Hybrid Score berechnen
            regex_pct = result.get("percentage", 0.0)
            hybrid_score = calculate_hybrid_score(
                regex_score=regex_pct,
                judge_score=judge_pct,
                asset_config=asset_cfg,
                module_config=benchmark_info,
                judge_enabled=judge_config.enabled,
            )

            if eval_module_id == "cli_benchmark":
                # Ensure safety and tool penalties from regex phase apply to judge!
                data_dict = result.get("data", {})
                if isinstance(data_dict, dict):
                    details = data_dict.get("details", {})
                    safety = details.get("safety", 100.0)
                    tool_f1 = details.get("tool_call_f1", 100.0)
                    if safety == 0.0:
                        hybrid_score = 0.0
                        result["judge_progress_status"] = f"⚖️ Judge: 0/{judge_scale} (Safety Penalty)"
                    elif tool_f1 < 50.0:
                        hybrid_score *= 0.6
                        result["judge_progress_status"] = f"⚖️ Judge: {judge_res.score}/{judge_scale} (Tool Penalty)"

            result["total_score"] = hybrid_score
            result["percentage"] = hybrid_score
            result["scoring_method"] = "hybrid"
            result["judge_progress_status"] = (
                f"⚖️ Judge: {judge_res.score}/{judge_scale} (Hybrid)"
            )

            # RECALCULATE contributions based on the new Hybrid score
            result = calculate_score_contributions(result, asset_cfg)
        else:
            result["judge_progress_status"] = "❌ Judge: failed"

    except JudgeUnavailableError:
        # Re-raise so the runner can abort the benchmark fully
        raise
    except JudgeUnavailableError:
        # Re-raise so the runner can abort the benchmark fully
        raise
    except Exception as e:  # pylint: disable=broad-exception-caught
        traceback.print_exc()
        logging.error(f"LLM Judge execution failed: {e}")
        result["judge_progress_status"] = "❌ Judge: failed"

    return result

def generate_audit_log(
    result: Dict[str, Any],
    exec_result: Any,
    asset_data: Dict[str, Any],
    response: str,
    score: Dict[str, Any]
) -> None:
    """
    Generates and saves the audit log based on configuration.
    """
    rp_fallback = asset_data.get(
        "prompt", asset_data.get("instruction", "No prompt found")
    )
    rp = getattr(exec_result, "evaluated_prompt", "") or rp_fallback

    if result.get("scoring_method") in ["llm_judge", "hybrid"]:
        judge_provider = result.get("llm_judge_provider_used", "unknown")
        judge_model = result.get("llm_judge_model_used", "unknown")

        # Fetch module-level category scores that are logged to CSV
        cat_section = ""
        cat_scores = score.get("category_scores", {})
        if cat_scores:
            cat_section = "\n\n### Category Scores (Rule-based / CSV)\n"
            for cat_name, cat_vals in cat_scores.items():
                cat_section += f"- **{cat_name}:** {cat_vals.get('achieved', 0)} / {cat_vals.get('max', 0)}\n"
            cat_section += f"\n**Rule-based Total Score:** {score.get('total_score', 0)} / {score.get('max_score', 0)}"

        # Also capture any detail/reasoning arrays generated by the regex scorer
        details_section = ""
        if "details" in score and score["details"]:
            details_section = "\n\n### Rule-based Evaluation Details\n"
            details_data = score["details"]
            if isinstance(details_data, list):
                details_section += "\n".join([f"- {d}" for d in details_data])
            else:
                details_section += str(details_data)

        # Capture Sub-Scores if present
        subscore_section = ""
        if result.get("judge_task_compliance") is not None:
            subscore_section = (
                "\n\n**Judge Sub-Scores:**\n"
                "| Dimension | Score |\n"
                "|---|---|\n"
                f"| Task Compliance | {result.get('judge_task_compliance')}/5 |\n"
                f"| Output Quality | {result.get('judge_output_quality')}/5 |\n"
                f"| Standard Adherence | {result.get('judge_standard_adherence')}/5 |"
            )

        meta_block = (
            "> [!NOTE]\n"
            "> **Evaluation Metadata**\n"
            f"> - **Evaluated by:** {judge_provider} / {judge_model}\n"
        )
        if result.get("scoring_method") == "hybrid":
            meta_block += f"> - **Hybrid Score:** {result.get('percentage', 'N/A')}%\n"
            meta_block += f"> - **LLM Judge Score (Raw):** {result.get('llm_judge_score', 'N/A')}"
        else:
            meta_block += f"> - **LLM Judge Score:** {result.get('llm_judge_score', 'N/A')}"

        judge_resp = f"{meta_block}\n\n**LLM Judge Reasoning:**\n{result.get('llm_judge_reasoning', 'No reasoning provided.')}{subscore_section}{cat_section}{details_section}"
    else:
        details_str = ""
        if "details" in score and score.get("details"):
            if isinstance(score["details"], list):
                details_str = "\n".join([str(d) for d in score["details"]])
            else:
                details_str = str(score["details"])

        judge_resp = f"**Regex / Rule Scorer ({result.get('scoring_method', 'unknown')}):**\n\n**Score:** {result.get('total_score', 0)} / {result.get('max_score', 0)}\n\n**Details:**\n\n{details_str}\n\n**Raw JSON:**\n```json\n{json.dumps(score, indent=2, ensure_ascii=False)}\n```"

    save_audit_log(
        model=result["model"],
        asset_id=result["asset_id"],
        prompt=rp,
        response=response,
        judge_response=judge_resp,
        token_limit_cutoff=result.get("token_limit_cutoff", False),
        token_limit_fallback=result.get("token_limit_fallback", False),
        execution_time=result.get("execution_time"),
        tokens_used=result.get("tokens_used"),
        tokens_per_second=result.get("tokens_per_second"),
        cost=result.get("cost_usd"),
        provider=result.get("provider"),
    )
