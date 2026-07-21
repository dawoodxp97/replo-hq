# app/orchestrator/ — pipeline engine

Three files, ~290 LOC. Design intent documented in root `AI_LAYER_PLAN.md`.

```
TutorialOrchestrator  — owns the run: creates execution row, loops steps, marks terminal state
      ↓
TutorialAgent         — decides which steps exist, builds them, marks complete/failed
      ↓
Step (ABC)            — one unit: validate → execute → persist audit row
```

## `orchestrator.py`

`execute()` seeds `previous_output = {'repo_url': ...}` then loops steps, **merging each
step's dict output into the accumulating context** and passing the whole blob as the next
step's `input_data`.

Consequences of that design:
- Steps have no declared contract. Step 3 reads whatever keys step 2 happened to emit.
  A renamed key in an LLM response silently produces `None` downstream.
- Context grows monotonically; by `save_tutorial` it carries the full file tree and every
  intermediate LLM payload, and all of it is written to `TutorialStepExecution.input_data`.
- First step failure raises and aborts. No retry, no resume-from-step, no compensation —
  even though `TutorialExecution.current_step_order` exists specifically to enable resume.

## `agent.py`

`get_steps()` hardcodes the ordered list of 5 step types, then `create_step_instance` maps
type→class through an if/elif ladder. Adding a step means editing both the list and the
ladder. A registry dict (`STEP_REGISTRY: dict[str, type[Step]]`) would collapse this.

`_create_default_config` inserts a `TutorialStepConfig` row with
`prompt_template="Default prompt"` when none exists. Steps then check
`if template == "Default prompt"` and substitute a hardcoded prompt from their own source.
**Prompts live in two places** — DB rows and Python string literals — and the sentinel
string is the switch between them.

`mark_execution_failed` sets statuses but never records the error message on the execution
row (only on the step row).

## `step.py`

Base class. Provides `call_ai` (merges step_config → kwargs precedence),
`parse_ai_response`, and the two DB audit methods. Note `call_ai` and `parse_ai_response`
each construct a **new `AIClient()`** per call — no shared session, no connection reuse.

`validate()` defaults to `return True`; no step overrides it.

## If refactoring

The seam worth defining is the step contract: typed input/output models per step
(Pydantic), so the pipeline is checkable rather than dict-shaped. Second seam: make
`Orchestrator` resumable using `current_step_order`, which the schema already supports.
