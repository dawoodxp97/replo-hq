"""Phase 3: Typed step contracts for the generation pipeline.

Each step defines explicit input/output schemas via Pydantic. This replaces the
implicit dict-passing pattern and makes failures from renamed keys visible at startup.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StepFailureReason(str, Enum):
    """Categorized failure reasons for per-step retry logic."""

    LLM_INVALID_JSON = "llm_invalid_json"
    LLM_RATE_LIMITED = "llm_rate_limited"
    LLM_API_ERROR = "llm_api_error"
    REPO_CLONE_FAILED = "repo_clone_failed"
    REPO_TOO_LARGE = "repo_too_large"
    REPO_NOT_FOUND = "repo_not_found"
    CREDENTIAL_EXPIRED = "credential_expired"
    CREDENTIAL_INVALID = "credential_invalid"
    INPUT_VALIDATION = "input_validation"
    INTERNAL = "internal"


class BaseStepInput(BaseModel):
    """Common fields all steps receive."""

    repo_url: str | None = None
    instance_id: str | None = None  # UUID as string
    execution_id: str | None = None  # UUID as string
    user_id: str | None = None  # UUID as string
    difficulty: str | None = None  # User's chosen difficulty level


class BaseStepOutput(BaseModel):
    """Common fields all steps may emit."""

    status: str = "success"
    error_reason: StepFailureReason | None = None
    error_message: str | None = None
    checkpoint: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# AnalyzeRepoStep
# =============================================================================


class RepoAnalysis(BaseModel):
    entry_points: list[str] = Field(default_factory=list)
    core_features: list[str] = Field(default_factory=list)
    architecture_pattern: str = ""
    tutorial_flow: list[dict[str, str]] = Field(default_factory=list)
    primary_language: str = ""
    repo_description: str = ""


class AnalyzeRepoStepInput(BaseStepInput):
    """Input for the repo analysis step."""

    repo_url: str
    instance_id: str


class AnalyzeRepoStepOutput(BaseStepOutput):
    """Output for the repo analysis step."""

    analysis: RepoAnalysis | None = None
    repo_path: str | None = None
    key_files_content: str = ""
    file_tree: list[dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# GenerateOutlineStep
# =============================================================================


class OutlineChapter(BaseModel):
    title: str
    sections: list[str] = Field(default_factory=list)


class TutorialOutline(BaseModel):
    title: str
    estimated_duration: str = "30 mins"
    chapters: list[OutlineChapter] = Field(default_factory=list)


class GenerateOutlineStepInput(BaseStepInput):
    """Input for the outline generation step."""

    analysis: RepoAnalysis | None = None
    key_files_content: str = ""


class GenerateOutlineStepOutput(BaseStepOutput):
    """Output for the outline generation step."""

    outline: TutorialOutline | None = None


# =============================================================================
# GenerateContentStep
# =============================================================================


class GeneratedModule(BaseModel):
    title: str
    content: str
    order: int


class GenerateContentStepInput(BaseStepInput):
    """Input for the content generation step."""

    outline: TutorialOutline | None = None
    key_files_content: str = ""


class GenerateContentStepOutput(BaseStepOutput):
    """Output for the content generation step."""

    modules: list[GeneratedModule] = Field(default_factory=list)


# =============================================================================
# RefineStep
# =============================================================================


class RefineStepInput(BaseStepInput):
    """Input for the refinement step."""

    modules: list[GeneratedModule] = Field(default_factory=list)


class RefineStepOutput(BaseStepOutput):
    """Output for the refinement step."""

    modules: list[GeneratedModule] = Field(default_factory=list)


# =============================================================================
# SaveTutorialStep
# =============================================================================


class TutorialSaveResult(BaseModel):
    tutorial_id: str
    module_count: int = 0


class SaveTutorialStepInput(BaseStepInput):
    """Input for the save step."""

    title: str = ""
    overview: str = ""
    modules: list[GeneratedModule] = Field(default_factory=list)
    repo_id: str | None = None


class SaveTutorialStepOutput(BaseStepOutput):
    """Output for the save step."""

    result: TutorialSaveResult | None = None
