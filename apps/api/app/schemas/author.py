"""Authoring schemas.

The old inline models typed the interesting fields as `str` and `list[dict]` and
let Postgres do the validating — which means a `DataError` or a
`CheckViolationError` surfaces as a 500 instead of a 422 naming the field.

Length caps match the column definitions (`title` is `String(255)`); the caps on
the text columns are policy, not schema — `Text` is unbounded, and an authoring
endpoint that accepts an unbounded body is a way to fill the database.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..models.enums import QuestionType, TutorialLevel

MAX_MARKDOWN = 200_000
MAX_SNIPPET = 100_000
MAX_DIAGRAM = 50_000


class AuthorTutorialListItem(BaseModel):
    tutorial_id: UUID
    title: str
    level: TutorialLevel
    overview: str | None = None
    visibility: str
    generated_at: datetime
    updated_at: datetime
    module_count: int = 0
    repo_name: str | None = None
    repo_url: str | None = None


class TutorialUpdate(BaseModel):
    """All fields optional — this is a partial update.

    `level` is typed as the enum rather than `str`. The old handler took a string,
    called `.upper()` on it and wrote `"BEGINNER"`, which the `ck_tutorials_level`
    CHECK constraint rejects — so every save including a level returned a 500.
    Pydantic now rejects an unknown level with a 422 that names the field, and a
    valid one can only be written in the stored lowercase form.
    """

    title: str | None = Field(default=None, min_length=1, max_length=255)
    overview: str | None = Field(default=None, max_length=MAX_MARKDOWN)
    level: TutorialLevel | None = None
    overview_diagram_mermaid: str | None = Field(default=None, max_length=MAX_DIAGRAM)


class TutorialMetaResponse(BaseModel):
    tutorial_id: UUID
    title: str
    level: TutorialLevel
    overview: str | None = None
    overview_diagram_mermaid: str | None = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModuleWrite(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content_markdown: str = Field(min_length=1, max_length=MAX_MARKDOWN)
    # Optional, matching the nullable columns. The old `ModuleUpdate` made
    # `code_snippet` required, so a module without code could not be saved.
    code_snippet: str | None = Field(default=None, max_length=MAX_SNIPPET)
    file_path: str | None = Field(default=None, max_length=255)
    diagram_mermaid: str | None = Field(default=None, max_length=MAX_DIAGRAM)


class ModuleResponse(BaseModel):
    module_id: UUID
    tutorial_id: UUID
    title: str
    order_index: int
    content_markdown: str
    code_snippet: str | None = None
    file_path: str | None = None
    diagram_mermaid: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ModuleReorder(BaseModel):
    module_ids: list[UUID] = Field(min_length=1)


class QuizOptionInput(BaseModel):
    """An option as submitted by the author. `is_correct` is the answer key.

    It is accepted here and stripped on the way out — see
    `schemas/tutorial.py::QuizOption`.
    """

    id: str | None = Field(default=None, max_length=64)
    text: str = Field(min_length=1, max_length=500)
    is_correct: bool = False


class QuizWrite(BaseModel):
    question_text: str = Field(min_length=1, max_length=2000)
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    options: list[QuizOptionInput] = Field(min_length=2, max_length=10)

    @model_validator(mode="after")
    def _check_answer_key(self) -> "QuizWrite":
        """Reject quizzes that cannot be graded coherently.

        The old endpoint validated none of this and stored whatever arrived:

        - **No correct option.** `correct_answer` was only reassigned `if
          correct_answer:`, so the options were replaced while the stored answer
          text kept its previous value — leaving an answer that is no longer one
          of the choices. Unanswerable, and silently so.
        - **Several correct options.** `next()` picked the first; the rest stayed
          flagged in the JSON. The quiz then disagreed with itself, since grading
          compares against `correct_answer`.
        - **Duplicate option text.** Grading matches on *text*, so two options
          reading the same thing make the right answer ambiguous.
        """
        correct = [o for o in self.options if o.is_correct]
        if len(correct) != 1:
            raise ValueError("Exactly one option must be marked is_correct.")

        seen = {o.text.strip().casefold() for o in self.options}
        if len(seen) != len(self.options):
            raise ValueError("Option text must be unique.")

        if self.question_type is QuestionType.TRUE_FALSE and len(self.options) != 2:
            raise ValueError("A true/false question must have exactly two options.")

        return self


class QuizResponse(BaseModel):
    """The authoring view — the owner wrote the answer key, so it is returned.

    This is why it is a separate model from `schemas/tutorial.py::QuizResponse`,
    which is the *learner* view and strips it.
    """

    quiz_id: UUID
    module_id: UUID
    question_text: str
    question_type: QuestionType
    options: list[QuizOptionInput]
    correct_answer: str | None = None

    model_config = ConfigDict(from_attributes=True)
