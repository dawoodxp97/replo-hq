"""Search endpoint — the global "jump to my stuff" box."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.dependencies import get_current_user_async
from ..db.session import get_async_db
from ..models.user import User
from ..schemas.search import SearchResponse
from ..services import search as search_service

router = APIRouter()


@router.get("/entities", response_model=SearchResponse)
async def search_entities(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Substring search across the caller's repositories, tutorials, modules and
    quizzes.

    Scoped to the caller — this is not public discovery (that is `/explore` on
    apps/site). A query shorter than two characters returns nothing, because
    below the trigram threshold every table would be sequentially scanned.
    """
    results = await search_service.search_entities(db, current_user.user_id, q)
    return SearchResponse(query=q.strip(), results=results)
