from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..models.enums import RepositoryStatus, TutorialLevel


class RepoCreate(BaseModel):
    # Plain `str`, not `HttpUrl`. Pydantic's HttpUrl accepts any scheme-valid URL
    # — including http://169.254.169.254/ — so it reads as validation while
    # providing none of the checks that matter here. `normalise_repo_url` in the
    # service does the real work: https only, github.com only, owner/repo shape.
    github_url: str = Field(min_length=1, max_length=500)


class RepoResponse(BaseModel):
    repo_id: UUID
    github_url: str
    name: str | None = None
    description: str | None = None
    # Real types, not `str`. The old response declared `created_at: str` and each
    # handler called `.isoformat()` by hand; pydantic serialises datetimes and
    # enums correctly on its own.
    status: RepositoryStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TutorialBrief(BaseModel):
    tutorial_id: UUID
    level: TutorialLevel
    title: str

    model_config = ConfigDict(from_attributes=True)


class RepoDetailResponse(BaseModel):
    repository: RepoResponse
    tutorials: list[TutorialBrief]


class FileTreeNode(BaseModel):
    name: str
    path: str
    type: str
    children: list["FileTreeNode"] | None = None


class RepoFileTreeResponse(BaseModel):
    tree: list[FileTreeNode]


class RepoFileContentResponse(BaseModel):
    content: str
    path: str
    size: int
