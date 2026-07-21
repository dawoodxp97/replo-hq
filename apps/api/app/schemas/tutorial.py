"""Tutorial schemas.

These were eight Pydantic classes declared at the top of `routers/tutorial.py`.
Moved here so the worker, the services and eventually the generated TypeScript
client all share one definition of the shape.

Note the field types: the old models declared `generated_at: str` and every
handler called `.isoformat()` by hand while building a dict. Pydantic serialises
`datetime` and `StrEnum` correctly on its own, and `from_attributes` means an ORM
row converts directly with no intermediate dict.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..models.enums import QuestionType, RunStatus, TutorialLevel, TutorialVisibility


class QuizOption(BaseModel):
    """One selectable answer, **stripped of the answer key**.

    `quizzes.options` is freeform JSONB and the option dicts written by
    `routers/author.py` carry `is_correct` — that flag *is* the answer key
    (`correct_answer` is derived from it, `quiz.correct_answer = the option whose
    is_correct is true`).

    Omitting the `correct_answer` column is therefore not enough on its own: the
    old inline schema declared `options: list[dict]` and passed the raw JSONB
    straight through, so every quiz shipped its own answer to the browser before
    the question was attempted.

    This model is an allowlist — `extra="ignore"` means any key not named below is
    dropped on the way out, so a new answer-revealing field added to the JSON
    later cannot leak by default. It fails closed.
    """

    id: str | None = None
    text: str

    model_config = ConfigDict(extra="ignore")


class QuizResponse(BaseModel):
    quiz_id: UUID
    question_text: str
    question_type: QuestionType
    options: list[QuizOption] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ModuleResponse(BaseModel):
    module_id: UUID
    title: str
    order_index: int
    content_markdown: str
    file_path: str | None = None
    code_snippet: str | None = None
    diagram_mermaid: str | None = None
    quiz: QuizResponse | None = None

    model_config = ConfigDict(from_attributes=True)


class TutorialResponse(BaseModel):
    tutorial_id: UUID
    repo_id: UUID
    level: TutorialLevel
    title: str
    overview: str | None = None
    overview_diagram_mermaid: str | None = None
    visibility: TutorialVisibility
    slug: str | None = None
    published_at: datetime | None = None
    generated_at: datetime
    modules: list[ModuleResponse]
    repo_name: str | None = None
    repo_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TutorialListItem(BaseModel):
    tutorial_id: UUID
    repo_id: UUID
    level: TutorialLevel
    title: str
    overview: str | None = None
    visibility: TutorialVisibility
    slug: str | None = None
    generated_at: datetime
    module_count: int = 0
    completed_modules: int = 0
    progress_percentage: int = 0
    repo_name: str | None = None
    repo_url: str | None = None


class VisibilityUpdate(BaseModel):
    visibility: TutorialVisibility


class GenerateRequest(BaseModel):
    # camelCase because the existing frontend sends it. Renaming is a Phase 4
    # concern, once the generated client owns the contract.
    repoUrl: str = Field(min_length=1, max_length=500)  # noqa: N815
    difficulty: TutorialLevel = TutorialLevel.INTERMEDIATE
    focus: list[str] | None = None
    description: str | None = Field(default=None, max_length=2000)


class GenerateResponse(BaseModel):
    instance_id: UUID
    status: RunStatus


class StatusResponse(BaseModel):
    status: RunStatus
    current_step: str | None = None
    step_status: RunStatus | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class GenerationStatusResponse(BaseModel):
    """Frontend-compatibility shape, camelCase and uppercase status.

    Kept verbatim so the legacy client keeps working through the rewrite. It is
    the one place uppercase status strings survive; everything else uses the
    lowercase enum values.
    """

    isGenerating: bool  # noqa: N815
    generationStep: int  # noqa: N815
    generationProgress: int  # noqa: N815
    generationId: str | None = None  # noqa: N815
    repoId: str | None = None  # noqa: N815
    status: str
    errorMessage: str | None = None  # noqa: N815
