"""
Benchmark Result Schema
=======================
Defines the strictly typed Data Transfer Object (DTO) for all benchmark results.
Ensures consistency between Modules, Runners, and the Leaderboard.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

class BenchmarkResult(BaseModel):
    """
    Standardized result object returned by every Benchmark Module.
    """
    
    primary_score: Optional[float] = Field(
        None, 
        description="The main numerical score (0.0-100.0) for ranking. 'None' implies an informational module (Info-Module)."
    )
    
    rendered_value: str = Field(
        ..., 
        description="The pre-formatted display string for the leaderboard (e.g., '85.5 %', 'Links (-4.0)', 'FAILED')."
    )
    
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="The structured data payload containing all detailed metrics, sub-scores, and raw values. Leaderboard can query this using dot-notation."
    )
    
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contextual metadata (e.g., model version, timestamp, cost, validation flags)."
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

    class Config:
        json_schema_extra = {
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
