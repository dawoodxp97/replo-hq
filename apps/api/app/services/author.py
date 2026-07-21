"""Authoring service.

The three `_verify_*_ownership` helpers this router carried are exactly what
`core/ownership.py` exists to replace — same joins, written a third time, with
their own error text.

Beyond the conversion, this slice makes quizzes reachable at all. The pipeline
never creates one (`steps/save_tutorial.py` has a `# Future` comment where the
code would go) and the only quiz endpoint was `PUT /quizzes/{quiz_id}`, which
requires a quiz to already exist. Nothing in the product could create the first
one, so the quiz feature was dead from end to end.
"""

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import InvalidInputError
from ..core.ownership import get_owned_module, get_owned_tutorial
from ..core.pagination import PageParams
from ..models.modules import Module
from ..models.quizzes import Quiz
from ..models.repositories import Repository
from ..models.tutorials import Tutorial
from ..schemas.author import (
    AuthorTutorialListItem,
    ModuleReorder,
    ModuleWrite,
    QuizWrite,
    TutorialUpdate,
)

logger = logging.getLogger(__name__)


# --- Tutorials --------------------------------------------------------------


async def list_authored_tutorials(
    db: AsyncSession, user_id: UUID, params: PageParams
) -> tuple[list[AuthorTutorialListItem], int]:
    """Paginated, one query. Was three queries and an unbounded result."""
    module_count = (
        select(func.count(Module.module_id))
        .where(Module.tutorial_id == Tutorial.tutorial_id)
        .correlate(Tutorial)
        .scalar_subquery()
    )

    base = (
        select(
            Tutorial,
            Repository.name.label("repo_name"),
            Repository.github_url.label("repo_url"),
            module_count.label("module_count"),
        )
        .join(Repository, Tutorial.repo_id == Repository.repo_id)
        .where(Repository.user_id == user_id)
    )

    total = (
        await db.execute(
            select(func.count())
            .select_from(Tutorial)
            .join(Repository, Tutorial.repo_id == Repository.repo_id)
            .where(Repository.user_id == user_id)
        )
    ).scalar_one()

    rows = (
        await db.execute(
            base.order_by(Tutorial.updated_at.desc()).limit(params.limit).offset(params.offset)
        )
    ).all()

    return [
        AuthorTutorialListItem(
            tutorial_id=r.Tutorial.tutorial_id,
            title=r.Tutorial.title,
            level=r.Tutorial.level,
            overview=r.Tutorial.overview,
            visibility=r.Tutorial.visibility,
            generated_at=r.Tutorial.generated_at,
            updated_at=r.Tutorial.updated_at,
            module_count=r.module_count,
            repo_name=r.repo_name,
            repo_url=r.repo_url,
        )
        for r in rows
    ], total


async def update_tutorial(
    db: AsyncSession, tutorial_id: UUID, user_id: UUID, body: TutorialUpdate
) -> Tutorial:
    """Partial update. Only fields explicitly present in the request are touched.

    `exclude_unset` is what makes that true: without it, every omitted field
    arrives as `None` and there is no way to tell "not supplied" from "clear
    this".
    """
    tutorial = await get_owned_tutorial(db, tutorial_id, user_id)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(tutorial, field, value)

    await db.commit()
    await db.refresh(tutorial)
    return tutorial


# --- Modules ----------------------------------------------------------------


async def create_module(
    db: AsyncSession, tutorial_id: UUID, user_id: UUID, body: ModuleWrite
) -> Module:
    """Append a module. There was no way to add one before — authoring could edit
    the pipeline's output but never extend it."""
    await get_owned_tutorial(db, tutorial_id, user_id)

    next_index = (
        await db.execute(
            select(func.coalesce(func.max(Module.order_index) + 1, 0)).where(
                Module.tutorial_id == tutorial_id
            )
        )
    ).scalar_one()

    module = Module(tutorial_id=tutorial_id, order_index=next_index, **body.model_dump())
    db.add(module)
    await db.commit()
    await db.refresh(module)
    return module


async def update_module(
    db: AsyncSession, module_id: UUID, user_id: UUID, body: ModuleWrite
) -> Module:
    module = await get_owned_module(db, module_id, user_id)

    for field, value in body.model_dump().items():
        setattr(module, field, value)

    await db.commit()
    await db.refresh(module)
    return module


async def delete_module(db: AsyncSession, module_id: UUID, user_id: UUID) -> None:
    """Delete a module and close the gap in `order_index`.

    Without the resequence the remaining modules keep indexes like 0,1,3,4. That
    renders fine — everything sorts by `order_index` — but any later code that
    treats the index as a position (a "module 3 of 5" label, an array offset, the
    reorder endpoint's own numbering) is then wrong.
    """
    module = await get_owned_module(db, module_id, user_id)
    tutorial_id = module.tutorial_id

    await db.delete(module)
    await db.flush()

    remaining = (
        (
            await db.execute(
                select(Module).where(Module.tutorial_id == tutorial_id).order_by(Module.order_index)
            )
        )
        .scalars()
        .all()
    )
    for index, row in enumerate(remaining):
        row.order_index = index

    await db.commit()


async def reorder_modules(
    db: AsyncSession, tutorial_id: UUID, user_id: UUID, body: ModuleReorder
) -> list[Module]:
    """Apply a new order. The submitted list must be a **complete permutation**.

    The old check was `len(modules) != len(module_ids)`, which only catches ids
    that do not belong to the tutorial. Submitting a *subset* passed: two of five
    ids were renumbered to 0 and 1 while the other three kept their old indexes,
    producing duplicate `order_index` values and an order that depends on how
    Postgres breaks the tie. Silent, and it corrupts the reading sequence rather
    than failing.
    """
    await get_owned_tutorial(db, tutorial_id, user_id)

    modules = (
        (await db.execute(select(Module).where(Module.tutorial_id == tutorial_id))).scalars().all()
    )

    submitted = list(body.module_ids)
    if len(set(submitted)) != len(submitted):
        raise InvalidInputError("module_ids contains duplicates.")

    if set(submitted) != {m.module_id for m in modules}:
        raise InvalidInputError(
            "module_ids must list every module in this tutorial exactly once "
            f"({len(modules)} expected, {len(submitted)} given)."
        )

    position = {module_id: index for index, module_id in enumerate(submitted)}
    for module in modules:
        module.order_index = position[module.module_id]

    await db.commit()
    return sorted(modules, key=lambda m: m.order_index)


async def list_modules(db: AsyncSession, tutorial_id: UUID, user_id: UUID) -> list[Module]:
    await get_owned_tutorial(db, tutorial_id, user_id)
    return list(
        (
            await db.execute(
                select(Module).where(Module.tutorial_id == tutorial_id).order_by(Module.order_index)
            )
        )
        .scalars()
        .all()
    )


# --- Quizzes ----------------------------------------------------------------


async def upsert_quiz(db: AsyncSession, module_id: UUID, user_id: UUID, body: QuizWrite) -> Quiz:
    """Create or replace the quiz on a module.

    Addressed by module, not by quiz id: `quizzes.module_id` is UNIQUE, so a
    module has at most one quiz and the module is the stable handle. The old
    `PUT /quizzes/{quiz_id}` could only edit a quiz that already existed, and
    nothing could create the first one.

    `correct_answer` is derived here **unconditionally**. The old code assigned it
    only `if correct_answer:`, so replacing the options without a correct one left
    the previous answer text in place, pointing at an option that no longer
    existed.
    """
    await get_owned_module(db, module_id, user_id)

    quiz = (await db.execute(select(Quiz).where(Quiz.module_id == module_id))).scalar_one_or_none()

    options = [o.model_dump() for o in body.options]
    # Exactly one, guaranteed by QuizWrite's validator.
    correct_answer = next(o["text"] for o in options if o["is_correct"])

    if quiz is None:
        quiz = Quiz(module_id=module_id)
        db.add(quiz)

    quiz.question_text = body.question_text
    quiz.question_type = body.question_type
    quiz.options = options
    quiz.correct_answer = correct_answer

    await db.commit()
    await db.refresh(quiz)
    return quiz


async def get_quiz(db: AsyncSession, module_id: UUID, user_id: UUID) -> Quiz | None:
    await get_owned_module(db, module_id, user_id)
    return (await db.execute(select(Quiz).where(Quiz.module_id == module_id))).scalar_one_or_none()


async def delete_quiz(db: AsyncSession, module_id: UUID, user_id: UUID) -> None:
    quiz = await get_quiz(db, module_id, user_id)
    if quiz is not None:
        await db.delete(quiz)
        await db.commit()
