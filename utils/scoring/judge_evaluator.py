import json
import logging
import time
import traceback
from typing import Any

from utils.benchmark_utils import save_audit_log
from utils.constants import MS_PER_SECOND
from utils.scoring.exceptions import JudgeUnavailableError
from utils.scoring.llm_judge.judge_config import LLMJudgeConfig
from utils.scoring.llm_judge.judge_runner import JudgeRunner
from utils.scoring_utils import calculate_hybrid_score, calculate_score_contributions

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Modul-Level-Cache (ersetzt Function-Attribute-Caching)
# ---------------------------------------------------------------------------
# HTTP-Client-Reuse über Tasks hinweg (Connection-Pooling, KEIN
# Evaluation-Context-Caching). JudgeReset-Invariante bleibt intakt:
# jede .score()-Bewertung ist ein frischer API-Call.
_judge_runner_cache: dict[str, Any] = {"runner": None, "cfg_key": None}
_config_cache: dict[str, Any] | None = None


def _get_cached_config() -> dict[str, Any]:
    """Liefert die Benchmark-Config (gecacht auf Modulebene)."""
    global _config_cache
    if _config_cache is None:
        from utils.config_validator import ConfigValidator  # noqa: PLC0415
        _config_cache = ConfigValidator().config
    return _config_cache


def _get_or_create_runner(judge_config: LLMJudgeConfig) -> JudgeRunner:
    """Reuse cached JudgeRunner when config hasn't changed (HTTP-Client-Reuse)."""
    cfg_key = (
        judge_config.provider.name,
        judge_config.provider.model,
        judge_config.module_judge_model,
    )
    cached_runner = _judge_runner_cache["runner"]
    cached_key = _judge_runner_cache["cfg_key"]
    if cached_runner is not None and cached_key == cfg_key:
        cached_runner._config = judge_config
        return cached_runner
    runner = JudgeRunner(judge_config)
    _judge_runner_cache["runner"] = runner
    _judge_runner_cache["cfg_key"] = cfg_key
    return runner


def _resolve_golden_standard(asset_data: dict[str, Any]) -> str:
    """Extrahiert und formatiert den Golden Standard aus Asset-Daten."""
    golden = asset_data.get("golden_standard", asset_data.get("golden", ""))
    if isinstance(golden, dict):
        golden_text = golden.get("text", "")
        if not golden_text:
            golden_text = json.dumps(golden, indent=2)
        golden = golden_text
    return str(golden)


def _inject_token_usage_context(
    kwargs: dict[str, Any],
    result: dict[str, Any],
    eval_module_id: str,
) -> None:
    """Universal token usage context für ALLE Modelle.

    Echte Token-Breakdown (SSoT: LLMClient-Usage): ``tokens_used`` ist die
    Gesamtsumme (Input + Output), ``input_tokens``/``output_tokens`` die
    echten Provider-Werte (Output inkl. Thinking), ``reasoning_tokens``
    der Thinking-Anteil des Outputs.
    """
    _token_usage: dict[str, Any] = {}
    _tokens_used = result.get("tokens_used")
    _reasoning_tokens = result.get("reasoning_tokens")
    _input_tokens = result.get("input_tokens")
    _output_tokens = result.get("output_tokens")
    _token_limit_used = result.get("token_limit_used")
    if _tokens_used is not None:
        _token_usage["tokens_used"] = int(_tokens_used)
    if _reasoning_tokens is not None:
        _token_usage["reasoning_tokens"] = int(_reasoning_tokens)
    if _input_tokens:
        _token_usage["input_tokens"] = int(_input_tokens)
    if _output_tokens:
        _token_usage["output_tokens"] = int(_output_tokens)
    if _token_limit_used is not None:
        _token_usage["token_budget"] = int(_token_limit_used)
    if result.get("token_limit_cutoff"):
        _token_usage["truncated"] = True
    try:
        _cfg = _get_cached_config()
        _module_budget = _cfg.get("token_budgets", {}).get(eval_module_id)
        if _module_budget:
            _token_usage["module_budget"] = int(_module_budget)
    except Exception:  # noqa: BLE001
        pass
    if _token_usage:
        kwargs["token_usage_context"] = _token_usage


def _inject_reasoning_budget_context(
    kwargs: dict[str, Any],
    model: str,
    eval_module_id: str,
) -> None:
    """Token budget context für Reasoning-Modelle (standard vs elevated)."""
    from utils.model_utils import is_reasoning_model  # noqa: PLC0415
    if not is_reasoning_model(model):
        return
    try:
        _cfg = _get_cached_config()
        _standard = _cfg.get("token_budgets", {}).get(eval_module_id)
        _elevated = _cfg.get("token_budgets_reasoning_models", {}).get(eval_module_id)
        if _standard and _elevated and _elevated > _standard:
            kwargs["token_budget_context"] = {"standard": _standard, "elevated": _elevated}
    except Exception:  # noqa: BLE001
        pass


def _inject_small_model_budget_context(
    kwargs: dict[str, Any],
    model: str,
    eval_module_id: str,
) -> None:
    """Small-model token budget context (Nano/Edge/Desktop/Workstation, nicht-Reasoning)."""
    from utils.model_utils import get_model_size_class, is_reasoning_model  # noqa: PLC0415
    if is_reasoning_model(model):
        return
    _size = get_model_size_class(model)
    if _size not in ("Nano", "Edge", "Desktop", "Workstation"):
        return
    try:
        _cfg = _get_cached_config()
        _small = _cfg.get("token_budgets_small_models", {}).get(eval_module_id)
        _standard = _cfg.get("token_budgets", {}).get(eval_module_id)
        if _small and _standard and _small > _standard:
            kwargs["small_model_token_context"] = {
                "size_class": _size,
                "standard_budget": _standard,
                "applied_budget": _small,
            }
    except Exception:  # noqa: BLE001
        pass


def _build_judge_kwargs(
    result: dict[str, Any],
    response: str,
    asset_data: dict[str, Any],
    eval_module_id: str,
    model: str,
    asset_cfg: dict[str, Any] | None,
    provider: str | None,
) -> dict[str, Any]:
    """Build kwargs for JudgeRunner.score(), keeping it provider-agnostic."""
    raw_prompt = asset_data.get("prompt", asset_data.get("instruction", ""))
    golden = _resolve_golden_standard(asset_data)
    required_language = asset_data.get("metadata", {}).get("language")
    language_weight = asset_data.get("metadata", {}).get("language_weight", 0.20)

    # Connector-Fix: Thinking-Content als <think>-Block vor die sichtbare
    # Antwort setzen, damit der Judge das Thinking als Teil der Response sieht
    # und korrekt zwischen internem Reasoning und sichtbarem Output unterscheiden
    # kann. Der Judge-Prompt bleibt unverändert — nur die model_response wird
    # angereichert. Viele Evaluatoren strippen <think>-Tags bereits beim
    # rule-based Scoring.
    _effective_response = response
    _has_think = False
    _think = result.get("think_content")
    if _think and _think.strip():
        _effective_response = f"<think>\n{_think.strip()}\n</think>\n\n{response}"
        # Kontextblock für den Judge: <think> ist internes Reasoning, kein Output-ONLY-Verstoß
        _has_think = True

    kwargs: dict[str, Any] = {
        "task_prompt": raw_prompt,
        "model_response": _effective_response,
        "golden_standard": golden,
        "module_id": eval_module_id,
        "rubric_override": asset_data.get("scoring", {}).get("rubric"),
        "tested_model_id": model,
        "response_time_ms": result.get("execution_time", 0) * MS_PER_SECOND,
        "required_language": required_language,
        "language_weight": language_weight,
    }
    if _has_think:
        kwargs["reasoning_trace_context"] = True
    _inject_token_usage_context(kwargs, result, eval_module_id)
    _inject_reasoning_budget_context(kwargs, model, eval_module_id)
    if provider:
        kwargs["tested_model_provider"] = provider
    if result.get("token_limit_cutoff"):
        kwargs["truncation_context"] = True
    _inject_small_model_budget_context(kwargs, model, eval_module_id)
    return kwargs


def _apply_cli_benchmark_penalties(
    result: dict[str, Any],
    hybrid_score: float,
    judge_score: int | None,
    judge_scale: int,
) -> float:
    """CLI-Benchmark: Safety- und Tool-Penalties auf Hybrid-Score anwenden."""
    data_dict = result.get("data", {})
    if not isinstance(data_dict, dict):
        return hybrid_score
    details = data_dict.get("details", {})
    safety = details.get("safety", 100.0)
    tool_f1 = details.get("tool_call_f1", 100.0)
    if safety == 0.0:
        result["judge_progress_status"] = f"⚖️ Judge: 0/{judge_scale} (Safety Penalty)"
        return 0.0
    if tool_f1 < 50.0:
        result["judge_progress_status"] = f"⚖️ Judge: {judge_score}/{judge_scale} (Tool Penalty)"
        return hybrid_score * 0.6
    return hybrid_score


def _process_judge_result(
    result: dict[str, Any],
    judge_res: Any,
    judge_config: LLMJudgeConfig,
    asset_cfg: dict[str, Any] | None,
    benchmark_info: dict[str, Any],
    eval_module_id: str,
) -> None:
    """Merge judge results into the result dict und berechne Hybrid-Score."""
    result["llm_judge_score"] = judge_res.score
    result["llm_judge_reasoning"] = judge_res.reasoning
    result["llm_judge_latency_ms"] = judge_res.judge_latency_ms
    result["llm_judge_provider_used"] = judge_res.judge_provider_used
    result["llm_judge_model_used"] = judge_res.judge_model_used
    result["llm_judge_parse_success"] = judge_res.parse_success
    result["judge_task_compliance"] = judge_res.judge_task_compliance
    result["judge_output_quality"] = judge_res.judge_output_quality
    result["judge_standard_adherence"] = judge_res.judge_standard_adherence

    if not (judge_res.parse_success and judge_res.score is not None):
        result["judge_progress_status"] = "❌ Judge: failed"
        return

    judge_scale = judge_config.scoring.scale
    judge_pct = (judge_res.score / judge_scale) * 100 if judge_scale > 0 else 0.0
    regex_pct = result.get("percentage", 0.0)
    hybrid_score = calculate_hybrid_score(
        regex_score=regex_pct,
        judge_score=judge_pct,
        asset_config=asset_cfg,
        module_config=benchmark_info,
        judge_enabled=judge_config.enabled,
    )

    if eval_module_id == "cli_benchmark":
        hybrid_score = _apply_cli_benchmark_penalties(
            result, hybrid_score, judge_res.score, judge_scale,
        )

    result["total_score"] = hybrid_score
    result["percentage"] = hybrid_score
    result["scoring_method"] = "hybrid"
    if "judge_progress_status" not in result:
        result["judge_progress_status"] = f"⚖️ Judge: {judge_res.score}/{judge_scale} (Hybrid)"
    result = calculate_score_contributions(result, asset_cfg)


def evaluate_with_judge(
    result: dict[str, Any],
    response: str,
    asset_data: dict[str, Any],
    judge_cfg_dict: dict[str, Any],
    eval_module_id: str,
    model: str,
    asset_cfg: dict[str, Any] | None,
    benchmark_info: dict[str, Any],
    provider: str | None = None,
) -> dict[str, Any]:
    """Executes the LLM Judge scoring methodology and updates the result dictionary."""
    _pre_delay = judge_cfg_dict.get("pre_call_delay_ms", 200)
    if _pre_delay > 0:
        time.sleep(_pre_delay / 1000.0)

    try:
        judge_config = LLMJudgeConfig.from_dict(judge_cfg_dict)
        if asset_cfg and "llm_judge_model" in asset_cfg:
            judge_config.module_judge_model = asset_cfg["llm_judge_model"]
        elif "llm_judge_model" in benchmark_info:
            judge_config.module_judge_model = benchmark_info["llm_judge_model"]

        runner = _get_or_create_runner(judge_config)
        kwargs = _build_judge_kwargs(
            result, response, asset_data, eval_module_id, model, asset_cfg, provider,
        )
        judge_res = runner.score(**kwargs)
        _process_judge_result(
            result, judge_res, judge_config, asset_cfg, benchmark_info, eval_module_id,
        )
    except JudgeUnavailableError:
        raise
    except Exception as e:  # pylint: disable=broad-exception-caught
        traceback.print_exc()
        logging.error(f"LLM Judge execution failed: {e}")
        result["judge_progress_status"] = "❌ Judge: failed"

    return result


def generate_audit_log(
    result: dict[str, Any],
    exec_result: Any,
    asset_data: dict[str, Any],
    response: str,
    score: dict[str, Any],
) -> None:
    """Generates and saves the audit log based on configuration."""
    rp_fallback = asset_data.get(
        "prompt", asset_data.get("instruction", "No prompt found"),
    )
    rp = getattr(exec_result, "evaluated_prompt", "") or rp_fallback

    if result.get("scoring_method") in ["llm_judge", "hybrid"]:
        judge_provider = result.get("llm_judge_provider_used", "unknown")
        judge_model = result.get("llm_judge_model_used", "unknown")

        cat_section = ""
        cat_scores = score.get("category_scores", {})
        if cat_scores:
            cat_section = "\n\n### Category Scores (Rule-based / CSV)\n"
            for cat_name, cat_vals in cat_scores.items():
                cat_section += f"- **{cat_name}:** {cat_vals.get('achieved', 0)} / {cat_vals.get('max', 0)}\n"
            cat_section += f"\n**Rule-based Total Score:** {score.get('total_score', 0)} / {score.get('max_score', 0)}"

        details_section = ""
        if "details" in score and score["details"]:
            details_section = "\n\n### Rule-based Evaluation Details\n"
            details_data = score["details"]
            if isinstance(details_data, list):
                details_section += "\n".join([f"- {d}" for d in details_data])
            else:
                details_section += str(details_data)

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

        judge_resp = f"**Regex / Rule Scorer ({result.get('scoring_method', 'unknown')}):**\n\n**Score:** {result.get('total_score', 0)} / {score.get('max_score', 0)}\n\n**Details:**\n\n{details_str}\n\n**Raw JSON:**\n```json\n{json.dumps(score, indent=2, ensure_ascii=False)}\n```"

    callouts: list[str] = score.get("anomaly_callouts") or []
    if callouts:
        callout_prefix = "\n\n".join(callouts) + "\n\n"
        judge_resp = callout_prefix + judge_resp

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
        reasoning_tokens=result.get("reasoning_tokens"),
        input_tokens=result.get("input_tokens"),
        output_tokens=result.get("output_tokens"),
        think_content=result.get("think_content"),
        thinking_mode=result.get("thinking_mode"),
    )
