"""
Benchmark Result Schema
=======================
Defines the strictly typed Data Transfer Object (DTO) for all benchmark results.
Ensures consistency between Modules, Runners, and the Leaderboard.
"""

from typing import Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class BenchmarkResult(BaseModel):
    """
    Standardized result object returned by every Benchmark Module.
    Encapsulates both execution metrics and scoring results.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "primary_score": 85.5,
                "rendered_value": "85.5 %",
                "data": {
                    "raw_score": 0.855,
                    "subscores": {"routine": 1.0, "reasoning": 0.5},
                    "display": {"summary": "Good Performance"},
                },
                "meta": {"model": "gpt-4", "timestamp": "2026-01-31T12:00:00Z"},
            }
        }
    )

    # --- Status ---
    status: str = Field(
        default="success", description="Status of the run (success, error, skipped)"
    )

    # --- Scoring ---
    primary_score: float | None = Field(
        default=None,
        description="The main numerical score (0.0-100.0) for ranking. 'None' implies purely informational or pending scoring.",
    )

    max_score: float = Field(
        default=100.0, description="The maximum possible score for this specific task."
    )

    tier: str = Field(
        default="Tier 1 (Undefined)", description="The assigned reasoning tier classification based on performance."
    )

    rendered_value: str = Field(
        default="N/A", description="Display string for leaderboard (e.g., '85.5 %')."
    )

    # --- Execution Metrics (Standardized) ---
    execution_time: float = Field(default=0.0, description="Runtime in seconds")
    load_time: float = Field(
        default=0.0, description="Model loading time in seconds (cold start)"
    )
    tokens_used: int = Field(default=0, description="Total tokens consumed (input + output, real provider usage when available)")
    input_tokens: int = Field(default=0, description="Real prompt tokens from provider usage (0 if not reported)")
    output_tokens: int = Field(default=0, description="Real completion tokens from provider usage, includes reasoning/thinking tokens (0 if not reported)")
    tokens_per_second: float = Field(default=0.0, description="Output speed in t/s based on real output tokens (incl. thinking); wall-time based, includes prefill. Falls back to module estimate when the provider reports no usage.")
    tps_eval: float | None = Field(default=None, description="Native generation speed: eval_count / eval_duration from Ollama (excludes prefill). None if not available (e.g. cloud proxy).")
    cost_usd: float = Field(default=0.0, description="Estimated cost in USD")
    finish_reason: str | None = Field(default=None, description="The reason the model stopped generating (e.g. length/max_tokens)")
    upstream_provider: str | None = Field(default=None, description="Tatsächlich bedienender Upstream-Host (Gateway-Routing, z.B. OpenRouter provider-Feld: 'DeepInfra', 'Xiaomi', 'Minimax'). None wenn der Provider keines liefert — Reproduzierbarkeits-Evidenz für Cloud-Messungen (Session 113, Host-Routing-Varianz).")
    reasoning_tokens: int | None = Field(default=None, description="Reasoning/thinking tokens used internally by the model (not returned in content). Counted against max_tokens budget on OpenRouter.")
    token_limit_cutoff: bool = Field(default=False, description="Flag indicating if the response was cut off due to max_token limits")
    token_limit_fallback: bool = Field(default=False, description="Flag indicating if the system dynamically lowered the requested max_tokens to accommodate model constraints (e.g. 8192 -> 4096)")
    token_limit_used: int | None = Field(default=None, description="The actual max_tokens value used for the successful generation (metadata/Kopfnote)")
    reasoning_reask: bool = Field(default=False, description="Flag: Reasoning-only Truncation Re-Ask — Erstversuch verbrannte das Budget ohne sichtbaren Output, Eskalationsleiter lief (SSoT: BaseProviderClient._maybe_reask_reasoning_truncation)")
    reasoning_reask_initial_budget: int | None = Field(default=None, description="Token-Budget des Erstversuchs (Stufe 1) vor der Leiter-Eskalation")
    reasoning_reask_stage: int = Field(default=0, description="Höchster erreichter Leiter-Versuch (1 = Erstversuch, 2/3 = Eskalationsstufen; 0 = keine Eskalation)")
    reasoning_reask_exhausted: bool = Field(default=False, description="Flag: höchste Eskalationsstufe lieferte weiterhin 0 sichtbaren Output — Messgrenze (nicht-terminierendes CoT), kein Modellversagen")
    reasoning_reask_final_budget: int | None = Field(default=None, description="Token-Budget der letzten Eskalationsstufe (Basis für den Card-Write cot_budget_calibration)")
    cot_calibrated_start: bool = Field(default=False, description="Flag: Stufe 1 startete aus Card-Kalibrierung (cot_budget_calibration) statt beim Modul-Budget")
    reasoning_last_resort: bool = Field(default=False, description="Flag: Last-Resort-Stufe der Eskalationsleiter aktiv — Budget nach Erschöpfung deutlich geöffnet (bewusst KEINE Card-Kalibrierung, nur Report-Hervorhebung; Einsatzkosten = Preispunkt)")
    reasoning_last_resort_budget: int | None = Field(default=None, description="Token-Budget des Last-Resort-Requests (über der höchsten regulären Leiter-Stufe)")
    reasoning_loop_suspected: bool = Field(default=False, description="Flag: Eskalations-Request wurde vom Denkzeit-Wächter abgebrochen — das Zeitbudget der Eskalationsphase (reasoning_reask.escalation_time_limit_s) war erschöpft, ohne dass das Modell terminierte. Loop-Verdacht (nicht-terminierende Thinking-Kette), abgegrenzt zur Budget-Erschöpfung (reasoning_reask_exhausted)")
    reasoning_loop_stage: int = Field(default=0, description="Leiter-Stufe, in der der Denkzeit-Abbruch erfolgte (0 = kein Abbruch)")
    reasoning_loop_elapsed_s: float | None = Field(default=None, description="Verbrauchte Eskalationszeit in Sekunden bis zum Denkzeit-Abbruch")
    refusal_retry_used: bool = Field(default=False, description="Flag: Safety-Refusal-Retry — Erstversuch wurde serverseitig verweigert (finish_reason=refusal), zweiter Versuch lief mit tag-freier Prompt-Fassung (refusal_retry_prompt im Asset; SSoT: BaseBenchmarkRunner._maybe_refusal_retry). Score bezieht sich auf den Retry; das Refusal-Verhalten bleibt über dieses Flag dokumentiert.")
    raw_response: str = Field(default="", description="The raw string output from the model")
    evaluated_prompt: str = Field(
        default="",
        description="The actual prompt that was sent to the model after evaluation/variable substitution",
    )

    run_id: str | None = Field(
        default=None,
        description="Unique identifier linking all tasks of a single model benchmark run",
    )

    # --- Judge Sub-Scores ---
    judge_task_compliance: float | None = Field(default=None, description="Task Compliance sub-score from LLM Judge (0-5)")
    judge_output_quality: float | None = Field(default=None, description="Output Quality sub-score from LLM Judge (0-5)")
    judge_standard_adherence: float | None = Field(default=None, description="Standard Adherence sub-score from LLM Judge (0-5)")
    thought_tag_compliance: float | None = Field(default=None, description="Score for compliance with thinking tag constraints")
    think_content: str | None = Field(default=None, description="Internal reasoning content from ThinkChunks (e.g. Magistral Small). Not scored; surfaced in audit log only.")

    # --- Identification ---
    model_version: str = Field(
        default="unknown", description="Fingerprint or version string of the model"
    )

    # --- Details ---
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Module-specific detailed metrics, sub-scores, and artifacts.",
    )

    meta: dict[str, Any] = Field(
        default_factory=dict, description="Contextual metadata (timestamp, flags)."
    )

    # --- Validators ---

    @field_validator("model_version", mode="before")
    @classmethod
    def set_model_version_unknown_if_none(cls, v: Any) -> str:
        if v is None:
            return "unknown"
        return str(v)

    @field_validator("data")
    @classmethod
    def validate_nested_depth(cls, v: dict[str, Any]) -> dict[str, Any]:
        """
        Performance Guard: Prevents excessively deep nesting in the metrics object,
        which could cause issues with serialization or the Leaderboard parser.
        Max Depth: 5 Levels.
        """

        def check_depth(obj: Any, depth: int = 0):
            if depth > 5:
                raise ValueError(
                    "Structure too deep: 'data' object exceeds 5 levels of nesting. Please flatten the structure."
                )

            if isinstance(obj, dict):
                for val in obj.values():
                    check_depth(val, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    check_depth(item, depth + 1)

        check_depth(v)
        return v
