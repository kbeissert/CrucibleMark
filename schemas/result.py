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
                    "display": {"summary": "Good Performance"}
                },
                "meta": {
                    "model": "gpt-4",
                    "timestamp": "2026-01-31T12:00:00Z"
                }
            }
        }
    )

    # --- Status ---
    status: str = Field("success", description="Status of the run (success, error, skipped)")
    
    # --- Scoring ---
    primary_score: Optional[float] = Field(
        None, 
        description="The main numerical score (0.0-100.0) for ranking. 'None' implies purely informational or pending scoring."
    )
    
    rendered_value: str = Field(
        "N/A", 
        description="Display string for leaderboard (e.g., '85.5 %')."
    )
    
    # --- Execution Metrics (Standardized) ---
    execution_time: float = Field(0.0, description="Runtime in seconds")
    load_time: float = Field(0.0, description="Model loading time in seconds (cold start)")
    tokens_used: int = Field(0, description="Total tokens consumed")
    cost_usd: float = Field(0.0, description="Estimated cost in USD")
    raw_response: str = Field("", description="The raw string output from the model")
    evaluated_prompt: str = Field("", description="The actual prompt that was sent to the model after evaluation/variable substitution")
    
    # --- Identification ---
    model_version: str = Field("unknown", description="Fingerprint or version string of the model")
    
    # --- Details ---
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Module-specific detailed metrics, sub-scores, and artifacts."
    )
    
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contextual metadata (timestamp, flags)."
    )
    
    # --- Validators ---
    
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
                raise ValueError("Structure too deep: 'data' object exceeds 5 levels of nesting. Please flatten the structure.")
            
            if isinstance(obj, dict):
                for val in obj.values():
                    check_depth(val, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    check_depth(item, depth + 1)
                    
        check_depth(v)
        return v

