"""UX Writing Data Models."""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class UXIssue:
    """Represents a specific issue to detect in the response."""

    issue: str
    points: float = 0.0
    keywords: list[str] = field(default_factory=list)
    inverse_match: bool = False
    severity: str = "medium"
    explanation: str = ""
    # For specific checks
    check_method: str | None = None
    required_ratio: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UXIssue":
        # Handles optional fields safely
        return cls(
            issue=data.get("issue", "Unknown Issue"),
            points=float(data.get("points", 0.0)),
            keywords=data.get("keywords", []),
            inverse_match=data.get("inverse_match", False),
            severity=data.get("severity", "medium"),
            explanation=data.get("explanation", ""),
            check_method=data.get("check_method"),
            required_ratio=data.get("required_ratio"),
        )


@dataclass
class UXCriterion:
    """Represents a generic scoring criterion for solution quality or formatting."""

    id: str
    name: str
    points: float
    check_method: str
    keywords: list[str] = field(default_factory=list)
    min_keywords: int = 1
    forbidden_keywords: list[str] = field(default_factory=list)
    max_violations: int = 0
    # Specific params for different checks
    min_rows: int = 0
    required_structure: list[str] = field(default_factory=list)
    check_pattern: str = ""
    required_elements: list[str] = field(default_factory=list)
    min_code_blocks: int = 0
    indicators: list[str] = field(default_factory=list)
    min_indicators: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UXCriterion":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Unnamed Criterion"),
            points=float(data.get("points", 0.0)),
            check_method=data.get("check_method", "keyword_presence"),
            keywords=data.get("keywords", []),
            min_keywords=data.get("min_keywords", 1),
            forbidden_keywords=data.get("forbidden_keywords", []),
            max_violations=data.get("max_violations", 0),
            min_rows=data.get("min_rows", 0),
            required_structure=data.get("required_structure", []),
            check_pattern=data.get("check_pattern", ""),
            required_elements=data.get("required_elements", []),
            min_code_blocks=data.get("min_code_blocks", 0),
            indicators=data.get("indicators", []),
            min_indicators=data.get("min_indicators", 0),
        )


@dataclass
class UXErrorDetectionSection:
    weight: float
    description: str
    default_required_ratio: float | None = None
    labeled_issues: list[UXIssue] = field(default_factory=list)
    standard_issues: list[UXIssue] = field(default_factory=list)
    advanced_issues: list[UXIssue] = field(default_factory=list)
    expert_issues: list[UXIssue] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UXErrorDetectionSection":
        return cls(
            weight=float(data.get("weight", 0.0)),
            description=data.get("description", ""),
            default_required_ratio=data.get("default_required_ratio"),
            labeled_issues=[
                UXIssue.from_dict(i) for i in data.get("labeled_issues", [])
            ],
            standard_issues=[
                UXIssue.from_dict(i) for i in data.get("standard_issues", [])
            ],
            advanced_issues=[
                UXIssue.from_dict(i) for i in data.get("advanced_issues", [])
            ],
            expert_issues=[UXIssue.from_dict(i) for i in data.get("expert_issues", [])],
        )


@dataclass
class UXScoringSection:
    weight: float
    description: str
    criteria: list[UXCriterion] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UXScoringSection":
        return cls(
            weight=float(data.get("weight", 0.0)),
            description=data.get("description", ""),
            criteria=[UXCriterion.from_dict(c) for c in data.get("criteria", [])],
        )


@dataclass
class UXScoringConfig:
    total_points: float
    error_detection: UXErrorDetectionSection | None = None
    solution_quality: UXScoringSection | None = None
    formatting: UXScoringSection | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UXScoringConfig":
        obj = cls(total_points=float(data.get("total_points", 100.0)))
        if "error_detection" in data:
            obj.error_detection = UXErrorDetectionSection.from_dict(
                data["error_detection"]
            )
        if "solution_quality" in data:
            obj.solution_quality = UXScoringSection.from_dict(data["solution_quality"])
        if "formatting" in data:
            obj.formatting = UXScoringSection.from_dict(data["formatting"])
        return obj


@dataclass
class UXAssetMetadata:
    id: str
    name: str
    version: str
    category: str
    subcategory: str
    difficulty: str
    estimated_time_seconds: int
    tags: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UXAssetMetadata":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            version=data.get("version", "1.0.0"),
            category=data.get("category", "ux_writing"),
            subcategory=data.get("subcategory", ""),
            difficulty=data.get("difficulty", "medium"),
            estimated_time_seconds=int(data.get("estimated_time_seconds", 0)),
            tags=data.get("tags", []),
        )


@dataclass
class UXScenario:
    """Represents a full test scenario loaded from an asset yaml."""

    metadata: UXAssetMetadata
    context: str
    prompt_template: str
    requirements: list[str]
    input_text: str
    testdata_issues: list[dict[str, Any]]  # Keeping raw for now or model if needed
    scoring: UXScoringConfig

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UXScenario":
        return cls(
            metadata=UXAssetMetadata.from_dict(data.get("metadata", {})),
            context=data.get("context", ""),
            prompt_template=data.get("prompt", ""),
            requirements=data.get("requirements", []),
            input_text=data.get("input_text", ""),
            testdata_issues=data.get("testdata", {}).get("issues", []),
            scoring=UXScoringConfig.from_dict(data.get("scoring", {})),
        )

    def to_prompt(self) -> str:
        """Generates the full prompt for the LLM."""
        req_str = "\n".join([f"- {req}" for req in self.requirements])
        # Simple string formatting based on template
        # The template has {input_text} and {requirements} placeholders
        prompt = self.prompt_template.replace("{input_text}", self.input_text)
        prompt = prompt.replace("{requirements}", req_str)

        full_system_prompt = f"{self.context}\n\n{prompt}"
        return full_system_prompt
