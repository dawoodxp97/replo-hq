# app/routers/ — HTTP layer

**Mid-conversion.** Each slice becomes async + service-backed + typed schemas + N+1-fixed +
paginated + ownership-checked in a single pass.

| Converted | Remaining |
|---|---|
| `user.py`, `repo.py`, `tutorial.py`, `progress.py`, `author.py` | `settings` → `dashboard` → `notification` → `search` |

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
| `author.py` | `/api/author` | 143 | **Converted.** Tutorial/module/quiz CRUD. Quiz addressed by module id. |
| `progress.py` | `/api/progress` | 94 | **Converted.** Completion, quiz grading, overview + paginated history. |
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

**Writes need a check too, and it is a different one.** Progress endpoints use
`get_readable_module` / `get_readable_quiz`, not the `get_owned_*` pair: a learner reading a
public tutorial must be able to record completion against it, and ownership rejects every
one of those. Before the conversion these endpoints had *no* check at all — `complete_module`
inserted a row for any `module_id` supplied, and `GET /progress` joined Module and Tutorial
to enrich the response, so an attacker could write a row against a private module and read
its title and its tutorial's title straight back. Validate the target of a write, not just
the caller.

## Never return the answer key

`quizzes.options` is freeform JSONB whose option dicts carry `is_correct` — that flag *is*
the answer (`author.py` derives `correct_answer` from it). Omitting the `correct_answer`
column is not sufficient; the old `options: list[dict]` passed the raw JSON through and
shipped every answer to the browser.

`schemas/tutorial.py::QuizOption` is an **allowlist** (`extra="ignore"`, fields `id`/`text`),
so a new answer-revealing key added to that JSON later cannot leak by default. The answer is
disclosed in two places, both deliberate: the `POST /progress/submit_quiz` response (after an
attempt) and `GET /author/modules/{id}/quiz` (the owner wrote it). That is why
`schemas/author.py` declares its **own** `QuizResponse` rather than reusing the learner one —
one model serving both audiences is how the key ends up back in the learner payload.

Writes go through `QuizWrite`, which enforces exactly one correct option, unique option text
(grading matches on text, so duplicates make the answer ambiguous) and two options for
true/false. `correct_answer` is derived unconditionally from the options, so it can never
disagree with them.

## Breaking changes in this router

The legacy client calls the old shapes; `apps/web-legacy` is reference-only and Phase 4 owns
the replacement.

| Was | Now |
|---|---|
| `GET /api/author/` | `GET /api/author/tutorials`, paginated |
| `PUT /api/author/tutorials/{id}` | `PATCH` — partial, `level` is the lowercase enum |
| `PUT /api/author/quizzes/{quiz_id}` | `PUT /api/author/modules/{module_id}/quiz` (upsert) |

## When adding an endpoint

Follow the existing shape (router → `Depends(get_current_user)` → `Depends(get_db)` →
inline query), or, if refactoring, extract to a service module and do it consistently
across a whole router — not one endpoint at a time.
