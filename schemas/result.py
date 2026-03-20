"""
Benchmark Result Schema
=======================
Defines the strictly typed Data Transfer Object (DTO) for all benchmark results.
Ensures consistency between Modules, Runners, and the Leaderboard.
"""

from typing import Dict, Any, Optional
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
    primary_score: Optional[float] = Field(
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
    tokens_used: int = Field(default=0, description="Total tokens consumed")
    tokens_per_second: float = Field(default=0.0, description="Output speed in t/s")
    cost_usd: float = Field(default=0.0, description="Estimated cost in USD")
    finish_reason: Optional[str] = Field(default=None, description="The reason the model stopped generating (e.g. length/max_tokens)")
    token_limit_cutoff: bool = Field(default=False, description="Flag indicating if the response was cut off due to max_token limits")
    token_limit_fallback: bool = Field(default=False, description="Flag indicating if the system dynamically lowered the requested max_tokens to accommodate model constraints (e.g. 8192 -> 4096)")
    token_limit_used: Optional[int] = Field(default=None, description="The actual max_tokens value used for the successful generation (metadata/Kopfnote)")
    raw_response: str = Field(default="", description="The raw string output from the model")
    evaluated_prompt: str = Field(
        default="",
        description="The actual prompt that was sent to the model after evaluation/variable substitution",
    )

    # --- Judge Sub-Scores ---
    judge_task_compliance: Optional[int] = Field(default=None, description="Task Compliance sub-score from LLM Judge")
    judge_output_quality: Optional[int] = Field(default=None, description="Output Quality sub-score from LLM Judge")
    judge_standard_adherence: Optional[int] = Field(default=None, description="Standard Adherence sub-score from LLM Judge")
    thought_tag_compliance: Optional[float] = Field(default=None, description="Score for compliance with thinking tag constraints")

    # --- Identification ---
    model_version: str = Field(
        default="unknown", description="Fingerprint or version string of the model"
    )

    # --- Details ---
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Module-specific detailed metrics, sub-scores, and artifacts.",
    )

    meta: Dict[str, Any] = Field(
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
    def validate_nested_depth(cls, v: Dict[str, Any]) -> Dict[str, Any]:
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
