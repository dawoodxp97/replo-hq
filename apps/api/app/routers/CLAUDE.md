# app/routers/ — HTTP layer

**Mid-conversion.** Each slice becomes async + service-backed + typed schemas + N+1-fixed +
paginated + ownership-checked in a single pass.

| Converted | Remaining |
|---|---|
| `user.py`, `repo.py`, `tutorial.py` | `progress` → `author` → `settings` → `dashboard` → `notification` → `search` |

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
| `tutorial.py` | `/api/tutorial` | 162 | **Converted.** Read/list/delete/publish + generation. Route order matters — see the module docstring. |
| `dashboard.py` | `/api/dashboard` | 367 | Aggregate stats. Many separate queries per request. |
| `settings.py` | `/api/settings` | 358 | Profile/notification/learning/appearance/security sub-resources. |
| `author.py` | `/api/author` | 274 | Manual tutorial/module/quiz editing. |
| `progress.py` | `/api/progress` | 269 | Module completion tracking. |
| `repo.py` | `/api/repo` | 93 | **Converted.** CRUD + tree + file. See git safety notes in `utils/repo_utils.py`. |
| `search.py` | `/api/search` | 192 | Likely `ILIKE` scans — no full-text index. |
| `notification.py` | `/api/notifications` | 149 | |
| `user.py` | `/api/user` | 78 | **Converted.** signup / login / refresh / **me**. |

## Patterns in the unconverted routers

- Response models are Pydantic classes defined **at the top of each router file**, not in
  `app/schemas/`.
- N+1 avoidance is done by hand — several separate queries stitched into dicts in Python
  instead of joins or correlated subqueries.
- Ownership checks are ad hoc: each endpoint re-derives "is this row mine?" by joining
  through `Repository.user_id`. Easy to forget one, and a missing filter looks like correct
  code in review — `tutorial.py`'s `GET /{id}` had **no check at all** and returned any
  user's tutorial to any caller.
- No pagination.

## Public reads

`GET /api/tutorial/{id}` uses `get_optional_user`, not `get_current_user_async`: the owner
sees private tutorials, and anyone — signed in or not — reads public and unlisted ones. It
is the only converted endpoint where an absent token is not an error. Writes on the same
resource (`DELETE`, `PATCH /visibility`) stay owner-only.

`PATCH /{id}/visibility` is the **only** writer of `visibility`, `slug` and `published_at`.
Slugs are assigned on first publish and never change afterwards — a public URL that stops
resolving is worse than one that no longer matches an edited title.

## When adding an endpoint

Follow the existing shape (router → `Depends(get_current_user)` → `Depends(get_db)` →
inline query), or, if refactoring, extract to a service module and do it consistently
across a whole router — not one endpoint at a time.
