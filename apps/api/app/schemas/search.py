"""Search schemas."""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class SearchEntityKind(StrEnum):
    REPOSITORY = "repository"
    TUTORIAL = "tutorial"
    MODULE = "module"
    QUIZ = "quiz"


class SearchEntity(BaseModel):
    id: UUID
    label: str
    type: SearchEntityKind
    # Present for module and quiz hits — the tutorial to open.
    tutorial_id: UUID | None = None
    # 0-based index of the module within its tutorial, for the player to jump to.
    # The old code sent `order_index - 1`, so the first module (index 0) pointed
    # at -1. `order_index` is already 0-based (see steps/save_tutorial.py).
    module_index: int | None = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchEntity]
