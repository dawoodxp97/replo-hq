# app/routers/ — HTTP layer

**Mid-conversion.** Each slice becomes async + service-backed + typed schemas + N+1-fixed +
paginated + ownership-checked in a single pass.

| Converted | Remaining |
|---|---|
| `user.py`, `repo.py` | `tutorial` → `progress` → `author` → `settings` → `dashboard` → `notification` → `search` |

`grep -l get_db app/routers/` lists what's left.

## The shape to copy (see `user.py`)

```python
@router.post("/thing", response_model=ThingOut, status_code=201)
async def create_thing(
    body: ThingCreate,                                   # schema in app/schemas/
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
) -> Thing:
    return await thing_service.create(db, current_user.user_id, body)
```

Rules:
- **No ORM queries in routers.** Logic goes in `app/services/`.
- **No `HTTPException`.** Raise `AppError` subclasses from `core/exceptions.py`, so services
  stay callable from a worker or a test without FastAPI.
- **No inline response models.** Schemas live in `app/schemas/`.
- Ownership via `core/ownership.py`, never a hand-written join.
- Lists take `page_params` and return `Page[T]`.

| Router | Prefix | LOC | Notes |
|--------|--------|-----|-------|
| `tutorial.py` | `/api/tutorial` | 443 | List, get-by-id, generate, generation-status. Largest file. |
| `dashboard.py` | `/api/dashboard` | 367 | Aggregate stats. Many separate queries per request. |
| `settings.py` | `/api/settings` | 358 | Profile/notification/learning/appearance/security sub-resources. |
| `author.py` | `/api/author` | 274 | Manual tutorial/module/quiz editing. |
| `progress.py` | `/api/progress` | 269 | Module completion tracking. |
| `repo.py` | `/api/repo` | 93 | **Converted.** CRUD + tree + file. See git safety notes in `utils/repo_utils.py`. |
| `search.py` | `/api/search` | 192 | Likely `ILIKE` scans — no full-text index. |
| `notification.py` | `/api/notifications` | 149 | |
| `user.py` | `/api/user` | 78 | **Converted.** signup / login / refresh / **me**. |

## Patterns in use

- Response models are Pydantic classes defined **at the top of each router file**, not in
  `app/schemas/`. `tutorial.py` alone declares 8 of them.
- N+1 avoidance is done by hand: `list_tutorials` fires ~5 separate queries and stitches
  dicts in Python instead of using joins/`selectinload`.
- Ownership checks are ad hoc — each endpoint re-derives "is this row mine?" by joining
  through `Repository.user_id`. Easy to forget one; nothing enforces it centrally.
- No pagination anywhere. `list_tutorials` returns every tutorial a user owns.

## When adding an endpoint

Follow the existing shape (router → `Depends(get_current_user)` → `Depends(get_db)` →
inline query), or, if refactoring, extract to a service module and do it consistently
across a whole router — not one endpoint at a time.
