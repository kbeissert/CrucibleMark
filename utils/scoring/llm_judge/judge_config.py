"""
Pydantic configuration model for the LLM Judge.
All defaults and valid values live here — never in runner or prompt code.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# Valid literals — changing these here is the single source of truth
ProviderName = Literal["anthropic", "mistral", "ollama", "openai"]
JudgeMode = Literal["complement", "replace"]
ScoreScale = Literal[3, 5, 10]

# Default values
DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5"
DEFAULT_MISTRAL_MODEL = "mistral-small-latest"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OLLAMA_MODEL = "llama3.2"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_UNLOAD_DELAY_MS = 500


class FallbackProviderConfig(BaseModel):
    """
    Optional fallback provider used when the primary provider is unavailable.

    Fallback triggers when:
      - primary provider health_check() returns False, OR
      - primary provider raises a connection/timeout exception during complete().

    Parse errors do NOT trigger the fallback (that is a prompt problem, not a
    provider problem).
    """

    name: ProviderName = Field(..., description="Fallback provider identifier.")
    model: str = Field(..., description="Fallback model ID or tag.")
    temperature: float = Field(DEFAULT_TEMPERATURE, ge=0.0, le=1.0)
    max_tokens: int = Field(DEFAULT_MAX_TOKENS, gt=0)
    timeout_seconds: int = Field(DEFAULT_TIMEOUT_SECONDS, gt=0)
    base_url: Optional[str] = Field(
        None,
        description="Required for Ollama fallback (e.g. http://localhost:11434).",
    )


class ProviderConfig(BaseModel):
    """Configuration for the concrete LLM provider used for judging."""

    name: ProviderName = Field("anthropic", description="Provider identifier.")
    model: str = Field(DEFAULT_ANTHROPIC_MODEL, description="Model ID or tag.")
    temperature: float = Field(DEFAULT_TEMPERATURE, ge=0.0, le=1.0)
    max_tokens: int = Field(DEFAULT_MAX_TOKENS, gt=0)
    timeout_seconds: int = Field(DEFAULT_TIMEOUT_SECONDS, gt=0)
    base_url: Optional[str] = Field(
        None,
        description="Only required for Ollama (e.g. http://localhost:11434).",
    )
    unload_delay_ms: int = Field(
        DEFAULT_UNLOAD_DELAY_MS,
        ge=0,
        description=(
            "Milliseconds to wait after an Ollama model unload is confirmed "
            "before the judge model is loaded. Ignored for cloud providers."
        ),
    )
    fallback: Optional[FallbackProviderConfig] = Field(
        None,
        description=(
            "Optional fallback provider. When absent, a primary failure is "
            "logged and the result carries score=None."
        ),
    )


class ScoringConfig(BaseModel):
    """Scoring behaviour for the judge."""

    scale: ScoreScale = Field(5, description="Point scale: 3, 5, or 10.")
    require_reasoning: bool = Field(
        True, description="Judge must emit REASONING: before SCORE:."
    )
    fail_on_parse_error: bool = Field(
        False,
        description=(
            "If True, a parse failure raises an exception. "
            "If False, returns JudgeResult(score=None, parse_success=False)."
        ),
    )


class LLMJudgeConfig(BaseModel):
    """Root configuration object for the LLM Judge extension."""

    enabled: bool = Field(True, description="Master switch for the judge.")
    mode: JudgeMode = Field(
        "complement",
        description=(
            "complement: both scorers run, results are merged. "
            "replace: LLM Judge replaces the hybrid scorer for applicable modules."
        ),
    )
    provider: ProviderConfig = Field(default_factory=ProviderConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    applicable_modules: List[str] = Field(
        default_factory=lambda: [
            "ux_writing",
            "documentation_quality",
            "content_transformation",
            "reasoning_logic",
        ],
        description="Benchmark module IDs where the LLM Judge is activated.",
    )
    module_judge_model: Optional[str] = Field(
        None,
        description="Optional module-specific override for the fallback judge model."
    )

    @classmethod
    def from_dict(cls, data: dict) -> "LLMJudgeConfig":
        """
        Build LLMJudgeConfig from a nested dict (e.g. loaded from YAML).

        The expected top-level key is 'llm_judge'. If absent, the raw dict
        is used directly so callers can pass either form.
        """
        payload = data.get("llm_judge", data)
        return cls.model_validate(payload)
