# ADR 0004 — Step execution data: capped at write time, no preview

Date: 2026-10-29 · Status: Accepted · Decides: Phase 3.13 (deferred)

## Context

`TutorialStepExecution.input_data` / `output_data` persist the accumulated
pipeline context on every step of every run. The input of `generate_content`
carries the whole repo analysis; `output_data` of `generate_content` carries
every generated module. For a large repository, a single row can hold
megabytes — written to Postgres, retained forever, read back by nobody
routinely.

## Decision

**Cap at write time in `Step._serialize_for_db`** — the single write path for
both columns — to `settings.step_data_max_bytes` (default 64 KiB), measured on
the UTF-8 JSON serialization. Over the cap, the payload is replaced by a
marker:

```json
{"truncated": true, "original_bytes": 482113, "max_bytes": 65536}
```

Why these properties:

- **Write time, not a cleanup job.** A retention job deletes; this prevents.
  Postgres never stores the bytes, so no TOAST bloat, no vacuum debt.
- **One implementation, in the base class.** Every step (present and future)
  inherits it; a step cannot forget it. `_serialize_for_db` is also where the
  sensitive-field filter lives — the two guards share one choke point.
- **No preview.** The oversized payloads are repo source code and LLM output —
  exactly the content "never log input data" exists for. A 2 KB preview
  quietly re-introduces the bytes the cap exists to bound. The marker carries
  only sizes.
- **Two shapes only.** Readers ever see either the full payload or the marker;
  there is no partial third shape to handle.

## Consequences

- Debugging a failed run on a large repo loses the full input/output — the
  step row still has `prompt_used`, `llm_response`, `error_message`, the step
  status and timing, which is what post-mortems actually use. If a specific
  investigation needs the full payload, the cap can be raised per environment.
- The cap is a byte cap on the *serialized JSON*, so the number of steps
  affected depends on content, not on a row count.
