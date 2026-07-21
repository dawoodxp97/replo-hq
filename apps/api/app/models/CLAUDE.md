# app/models/ — SQLAlchemy ORM

All models inherit `Base` from `app/db/session.py`. UUID PKs via
`server_default=text("gen_random_uuid()")` (requires pgcrypto/PG13+).

## Domain tables

| Model | Table | PK column | Notes |
|-------|-------|-----------|-------|
| `User` | `users` | `user_id` | email unique+indexed, `hashed_password`. No `created_at`, no `is_active`, no email verification. |
| `Repository` | `repositories` | `repo_id` | `github_url` is **globally unique** — two different users cannot both add the same public repo. Bug for a multi-tenant SaaS. |
| `Tutorial` | `tutorials` | `tutorial_id` | FK repo_id CASCADE. `level` is a free-form `String(50)`, not an enum. |
| `Module` | `modules` | `module_id` | ordered by `order_index`. |
| `Quiz` | `quizzes` | | |
| `UserProgress` | `user_progress` | | Completion rows. |
| `UserSettings` | `user_settings` | | 1:1 with User. |
| `Notification` | `notifications` | | |

## Orchestration tables (`orchestration.py`)

| Model | Purpose |
|-------|---------|
| `TutorialInstance` | One generation request. `status`: pending/running/completed/failed. |
| `TutorialExecution` | One attempt at an instance. Tracks `current_step_order`. |
| `TutorialStepExecution` | Per-step audit row: input_data, output_data, prompt_used, llm_response, error_message. |
| `TutorialStepConfig` | Per-step-type prompt/model/temperature config, unique on `step_type`. Rows auto-created with `prompt_template="Default prompt"` if absent (see `orchestrator/agent.py`). |

`TutorialInstance` links to `User` but **not** to `Repository` or `Tutorial` — it stores a
raw `repo_url` string. The join back to the produced tutorial is by URL matching, not FK.

## Cross-cutting gaps

- Statuses are bare strings everywhere. No Python enums, no PG enums, no CHECK constraints.
  `Repository.status` uses UPPERCASE (`PENDING`), orchestration uses lowercase (`pending`).
- No `created_at`/`updated_at` mixin; some tables have them, some don't, `users` has neither.
- No tenant/organization table. Everything is scoped to a single `user_id`.
- `TutorialStepExecution.input_data`/`output_data` are unbounded JSON holding full LLM
  context — this table will dominate DB size.
- **No migrations.** Changing a column here has no path to production. See root `CLAUDE.md`.
