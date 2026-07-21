# app/routers/ — HTTP layer

9 routers, ~2.1k LOC. **This is where the business logic lives.** There is no service layer;
routers query the ORM directly, shape responses inline, and own transaction boundaries.

| Router | Prefix | LOC | Notes |
|--------|--------|-----|-------|
| `tutorial.py` | `/api/tutorial` | 443 | List, get-by-id, generate, generation-status. Largest file. |
| `dashboard.py` | `/api/dashboard` | 367 | Aggregate stats. Many separate queries per request. |
| `settings.py` | `/api/settings` | 358 | Profile/notification/learning/appearance/security sub-resources. |
| `author.py` | `/api/author` | 274 | Manual tutorial/module/quiz editing. |
| `progress.py` | `/api/progress` | 269 | Module completion tracking. |
| `repo.py` | `/api/repo` | 238 | Repo CRUD + analyze. |
| `search.py` | `/api/search` | 192 | Likely `ILIKE` scans — no full-text index. |
| `notification.py` | `/api/notifications` | 149 | |
| `user.py` | `/api/user` | 126 | signup / login (OAuth2 form) / refresh. |

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
