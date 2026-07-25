"""Search service.

Powers the global search box: repositories, tutorials, modules and quizzes the
caller owns, matched by substring.

## What this replaces

The old handler ran four ILIKE searches and then, to build labels, re-queried the
parent rows one map at a time — a tutorial lookup here, a repo lookup there,
several `SELECT ... WHERE id IN (...)` round trips per entity type. Each search
now carries its parent columns in the same query via joins, so the whole endpoint
is four queries flat regardless of how much matches.

Two correctness fixes travelled with it:

- **`module_index` was `order_index - 1`.** `order_index` is 0-based
  (steps/save_tutorial.py, services/author.py), so the first module resolved to
  `-1`, and the player either jumped nowhere or — via Python-style negative
  indexing on the client — to the *last* module.
- **`Tutorial.level` was a search field.** It is an enum of three fixed values;
  matching free text against it only ever produced noise ("nin" matching nothing,
  "beg" surfacing every beginner tutorial). Dropped.

## Ownership

Everything is scoped to `Repository.user_id == user_id`. Search deliberately does
**not** reach public tutorials owned by others — it backs a personal "jump to my
stuff" box, not discovery. Public discovery is `/explore` (apps/site), a separate
surface with its own visibility rules.
"""

import logging
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.modules import Module
from ..models.quizzes import Quiz
from ..models.repositories import Repository
from ..models.tutorials import Tutorial
from ..schemas.search import SearchEntity, SearchEntityKind

logger = logging.getLogger(__name__)

# Per-entity-type caps before merging, then an overall cap. Bounds both the query
# cost and the payload; the box shows a short dropdown, not a results page.
PER_TYPE_LIMIT = 10
TOTAL_LIMIT = 30

# Below this the trigram indexes are not consulted (pg_trgm needs 3 chars), so a
# 1-character query is a full scan of every searchable table. Cheaper to require
# a couple of characters than to scan `modules.content_markdown` for "a".
MIN_QUERY_LENGTH = 2

_QUESTION_PREVIEW = 50


def _pattern(query: str) -> str:
    r"""Escape LIKE metacharacters, then wrap in wildcards.

    Without escaping, a user typing `%` or `_` — or `\` — changes the match
    semantics: `_` becomes "any character" and `50%` matches far more than the
    literal string. The searched text is unfiltered user and repo content, so
    this is not hypothetical.
    """
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _ordered(stmt: Select, order_col) -> Select:
    return stmt.limit(PER_TYPE_LIMIT).order_by(order_col)


async def search_entities(db: AsyncSession, user_id: UUID, query: str) -> list[SearchEntity]:
    query = query.strip()
    if len(query) < MIN_QUERY_LENGTH:
        return []

    pattern = _pattern(query)
    results: list[SearchEntity] = []

    # --- Repositories -------------------------------------------------------
    repos = (
        await db.execute(
            _ordered(
                select(Repository.repo_id, Repository.name, Repository.github_url).where(
                    Repository.user_id == user_id,
                    Repository.name.ilike(pattern)
                    | Repository.github_url.ilike(pattern)
                    | Repository.description.ilike(pattern),
                ),
                Repository.name,
            )
        )
    ).all()
    for repo in repos:
        results.append(
            SearchEntity(
                id=repo.repo_id,
                label=repo.name or repo.github_url.rstrip("/").split("/")[-1].removesuffix(".git"),
                type=SearchEntityKind.REPOSITORY,
            )
        )

    # --- Tutorials ----------------------------------------------------------
    tutorials = (
        await db.execute(
            _ordered(
                select(Tutorial.tutorial_id, Tutorial.title, Repository.name.label("repo_name"))
                .join(Repository, Tutorial.repo_id == Repository.repo_id)
                .where(
                    Repository.user_id == user_id,
                    Tutorial.title.ilike(pattern) | Tutorial.overview.ilike(pattern),
                ),
                Tutorial.title,
            )
        )
    ).all()
    for tut in tutorials:
        label = f"{tut.title} ({tut.repo_name})" if tut.repo_name else tut.title
        results.append(
            SearchEntity(id=tut.tutorial_id, label=label, type=SearchEntityKind.TUTORIAL)
        )

    # --- Modules ------------------------------------------------------------
    modules = (
        await db.execute(
            _ordered(
                select(
                    Module.module_id,
                    Module.title,
                    Module.order_index,
                    Module.tutorial_id,
                    Tutorial.title.label("tutorial_title"),
                    Repository.name.label("repo_name"),
                )
                .join(Tutorial, Module.tutorial_id == Tutorial.tutorial_id)
                .join(Repository, Tutorial.repo_id == Repository.repo_id)
                .where(
                    Repository.user_id == user_id,
                    Module.title.ilike(pattern)
                    | Module.content_markdown.ilike(pattern)
                    | Module.file_path.ilike(pattern),
                ),
                Module.title,
            )
        )
    ).all()
    for mod in modules:
        label = f"{mod.title} — {mod.tutorial_title}" if mod.tutorial_title else mod.title
        if mod.repo_name:
            label = f"{label} ({mod.repo_name})"
        results.append(
            SearchEntity(
                id=mod.module_id,
                label=label,
                type=SearchEntityKind.MODULE,
                tutorial_id=mod.tutorial_id,
                module_index=mod.order_index,
            )
        )

    # --- Quizzes ------------------------------------------------------------
    quizzes = (
        await db.execute(
            _ordered(
                select(
                    Quiz.quiz_id,
                    Quiz.question_text,
                    Module.order_index,
                    Module.title.label("module_title"),
                    Module.tutorial_id,
                )
                .join(Module, Quiz.module_id == Module.module_id)
                .join(Tutorial, Module.tutorial_id == Tutorial.tutorial_id)
                .join(Repository, Tutorial.repo_id == Repository.repo_id)
                .where(
                    Repository.user_id == user_id,
                    Quiz.question_text.ilike(pattern),
                ),
                Quiz.question_text,
            )
        )
    ).all()
    for quiz in quizzes:
        preview = quiz.question_text
        if len(preview) > _QUESTION_PREVIEW:
            preview = preview[:_QUESTION_PREVIEW].rstrip() + "…"
        label = f"{preview} — {quiz.module_title}" if quiz.module_title else preview
        results.append(
            SearchEntity(
                id=quiz.quiz_id,
                label=label,
                type=SearchEntityKind.QUIZ,
                tutorial_id=quiz.tutorial_id,
                module_index=quiz.order_index,
            )
        )

    # Repositories first, then tutorials, modules, quizzes; alphabetical within a
    # type. A stable, predictable order beats relevance ranking here — the set is
    # small and the user is scanning a dropdown, not reading a results page.
    kind_order = {
        SearchEntityKind.REPOSITORY: 0,
        SearchEntityKind.TUTORIAL: 1,
        SearchEntityKind.MODULE: 2,
        SearchEntityKind.QUIZ: 3,
    }
    results.sort(key=lambda e: (kind_order[e.type], e.label.casefold()))
    return results[:TOTAL_LIMIT]
