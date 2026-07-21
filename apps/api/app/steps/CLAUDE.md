# app/steps/ — the 5 pipeline steps

Executed in this fixed order by `orchestrator/agent.py`:

1. **`analyze_repo.py`** (`AnalyzeRepoStructureStep`) — clones the repo, walks the file tree,
   heuristically ranks files by filename priority list, reads the **top 5** files truncated
   to **2000 chars each**, asks the LLM for entry points / features / architecture / flow.
2. **`generate_outline.py`** — takes the analysis dict, asks for title + chapters/sections.
3. **`generate_content.py`** — expands outline into module content.
4. **`refine_tutorial.py`** — a polish pass.
5. **`save_tutorial.py`** — find-or-create `Repository`, insert `Tutorial`, insert `Module`
   rows one at a time with a `commit()` per module.

## Shared shape

Each step: build `prompt_data` dict → take `self.step_config.prompt_template`, and if it
equals the literal `"Default prompt"`, replace with a hardcoded template in the file →
`template.format(**prompt_data)` → `call_ai` → `parse_ai_response`.

## Known weaknesses

- **`str.format()` on LLM templates**: any literal `{` in repo content or a prompt edited
  via the DB raises `KeyError`/`IndexError`. Repo code full of braces is the normal case.
- **Repo comprehension is shallow.** 5 files × 2000 chars is the entire evidence base for a
  whole-repository tutorial. `requirements.txt` still pins `tree-sitter` and `transformers`
  (CodeBERT) — `AI_LAYER_PLAN.md` claims AST parsing works — but **nothing imports them**.
  The heavy ML deps are dead weight in the image.
- ~~`clone_repo` never cleans up~~ / ~~no size or SSRF guard~~ — **fixed in the repo slice.**
  `utils/repo_utils.py` now enforces an https+github.com allowlist, `--depth 1`, a 120s
  timeout, a 500MB cap, symlink refusal, and `remove_clone()`. Cloning runs in a worker
  thread so it no longer blocks the event loop. Read that module's docstring before
  touching anything that handles a URL or a file path.
- **`save_tutorial` is not atomic.** Commit per module; a mid-loop failure leaves a
  half-written tutorial marked as produced by a failed execution.
- **The pipeline never creates quizzes.** `save_tutorial.py` has a `# Future: Generate
  quizzes in a separate step` comment and writes none, so every generated tutorial has
  quiz-shaped UI with nothing behind it. Only manual authoring (`routers/author.py`)
  produces a `Quiz` row.
- `save_tutorial` hardcodes `level="INTERMEDIATE"` — the user's chosen difficulty from
  `GenerateRequest` never reaches the tutorial row.
- Output of step 3 and input of step 5 agree only by convention (`modules` key). Nothing
  validates it; a missing key yields an empty tutorial with no error.

## Adding a step

Subclass `Step`, implement `execute() -> dict`, then register it in **both** the
`step_types` list and the `create_step_instance` ladder in `orchestrator/agent.py`.
