"""Pagination.

No list endpoint in the codebase paginated — `list_tutorials` returned every
tutorial a user owned, and `/explore` would have returned every public tutorial
in the product. That works at one user and falls over silently as data grows,
because the failure is a slow response rather than an error.

Offset-based, deliberately. Cursor pagination is better for very large or
fast-changing sets, but offset supports "page 3 of 12" in a UI and is far simpler
to consume. If a list ever grows past ~100k rows, revisit — deep offsets get slow
because Postgres still walks the skipped rows.
"""

from collections.abc import Sequence

from fastapi import Query
from pydantic import BaseModel, Field
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

MAX_LIMIT = 100
DEFAULT_LIMIT = 20


class PageParams(BaseModel):
    """Query parameters. Use as a FastAPI dependency:

    params: PageParams = Depends(page_params)
    """

    limit: int = Field(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT)
    offset: int = Field(default=0, ge=0)


def page_params(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Items per page"),
    offset: int = Query(0, ge=0, description="Items to skip"),
) -> PageParams:
    """`le=MAX_LIMIT` is the important part: without a ceiling, `?limit=1000000`
    is an unauthenticated way to exhaust memory."""
    return PageParams(limit=limit, offset=offset)


class Page[T](BaseModel):
    """Envelope for a page of results.

    `has_more` is computed rather than left to the client, because deriving it
    from `offset + len(items) < total` is easy to get subtly wrong and every
    client would have to do it.
    """

    items: list[T]
    total: int
    limit: int
    offset: int
    has_more: bool

    @classmethod
    def build(cls, items: Sequence[T], total: int, params: PageParams) -> "Page[T]":
        return cls(
            items=list(items),
            total=total,
            limit=params.limit,
            offset=params.offset,
            has_more=params.offset + len(items) < total,
        )


async def paginate(
    db: AsyncSession,
    stmt: Select,
    params: PageParams,
) -> tuple[Sequence, int]:
    """Run a SELECT windowed to one page, plus its total count.

    Returns `(rows, total)`. Two queries on purpose — a window function
    (`count(*) OVER ()`) would avoid the round trip but forces the count into
    every row and breaks once the statement grows a GROUP BY.

    The count query strips ORDER BY: it changes nothing about a count and makes
    Postgres do a sort it will throw away.
    """
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    result = await db.execute(stmt.limit(params.limit).offset(params.offset))
    return result.scalars().all(), total
