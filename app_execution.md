ReploAI: AI-Powered Code Tutorial Generator
Step-by-Step Execution Plan
This document outlines the detailed, phased implementation process for building ReploAI, from database schema to frontend components.



Phase 1: Foundation (Database Schema - PostgreSQL)

First, define the data structures. All other logic builds upon this.
File: backend/models.py (or your ORM definition file)
-- SQL Schema for PostgreSQL


-- Note: User table is omitted as auth is complete.
-- We assume a 'users' table with 'user_id' (UUID or INT) exists.


-- Stores the GitHub repos to be analyzed
CREATE TABLE repositories (
    repo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    github_url VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING', -- PENDING, ANALYZING, COMPLETED, FAILED
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);


-- A repo can have multiple tutorials (Beginner, Intermediate, Advanced)
CREATE TABLE tutorials (
    tutorial_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID REFERENCES repositories(repo_id) ON DELETE CASCADE,
    level VARCHAR(50) NOT NULL, -- BEGINNER, INTERMEDIATE, ADVANCED
    title VARCHAR(255) NOT NULL,
    overview TEXT,
    overview_diagram_mermaid TEXT, -- For the main dependency graph
    generated_at TIMESTAMPTZ DEFAULT now()
);


-- A tutorial is made of multiple modules (steps)
CREATE TABLE modules (
    module_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tutorial_id UUID REFERENCES tutorials(tutorial_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    order_index INT NOT NULL, -- To maintain sequence (e.g., 1, 2, 3...)
    content_markdown TEXT NOT NULL, -- The AI-generated explanation
    file_path VARCHAR(255), -- Relevant file for this step
    code_snippet TEXT, -- The code for the editor
    diagram_mermaid TEXT -- Optional diagram for this specific module
);


-- Each module can have one quiz question
CREATE TABLE quizzes (
    quiz_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID REFERENCES modules(module_id) ON DELETE CASCADE UNIQUE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) DEFAULT 'MULTIPLE_CHOICE', -- MULTIPLE_CHOICE, CODE
    options JSONB, -- e.g., [{"text": "Option A", "is_correct": false}, ...]
    correct_answer TEXT -- For code quizzes or as a redundant check
);


-- Tracks which user has completed which module
CREATE TABLE user_progress (
    progress_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    module_id UUID REFERENCES modules(module_id) ON DELETE CASCADE,
    completed_at TIMESTAMPTZ DEFAULT now(),
    quiz_score INT, -- e.g., 1 for correct, 0 for incorrect
    UNIQUE(user_id, module_id) -- A user can only complete a module once
);


-- Indexes for performance
CREATE INDEX idx_repo_user ON repositories(user_id);
CREATE INDEX idx_tutorial_repo ON tutorials(repo_id);
CREATE INDEX idx_module_tutorial ON modules(tutorial_id);
CREATE INDEX idx_progress_user_module ON user_progress(user_id, module_id);

Phase 2: Core AI Analysis Pipeline (Worker Logic)

This is the "brain" of your app. This logic will run inside your BullMQ/Redis worker. Do not run this on the main API thread.
File: backend/app/worker/analysis_task.py

This is a conceptual Python/pseudocode flow for the worker task.
# Conceptual task for the BullMQ worker
# This function is triggered by a job
async def process_repository_analysis(job):
    repo_id = job.data['repo_id']
    github_url = job.data['github_url']
    
    try:
        # 1. Update status in DB
        await db.repositories.update(repo_id, status='ANALYZING')
        repo = await db.repositories.get_one(repo_id)
        repo_name = github_url.split('/')[-1] # Simplified


        # 2. Ingestion: Clone repo to a temp directory
        local_repo_path = f"/tmp/reploai/{repo_id}"
        git.Repo.clone_from(github_url, local_repo_path)


        # 3. Structure Analysis (tree-sitter)
        # - Output: A large JSON object representing the entire codebase structure
        code_structure_json = await run_tree_sitter_analysis(local_repo_path)
        
        # 4. Code Summarization (CodeBERT)
        # - Get technical summaries for key functions
        code_summaries = await run_codebert_summarization(local_repo_path, code_structure_json)


        # 5. Dependency Graph (Mermaid.js)
        # - Generate a high-level Mermaid.js `graph TD` string
        main_diagram = await generate_dependency_graph(code_structure_json)


        # 6. Tutorial Generation (GPT-4) - Loop for each level
        levels = ['BEGINNER', 'INTERMEDIATE', 'ADVANCED']
        
        for level in levels:
            # 6a. === PROMPT 1: GENERATE OUTLINE ===
            # (See Phase 2a for prompt details)
            outline_prompt = create_gpt_outline_prompt(level, code_structure_json, code_summaries)
            # Expect a JSON array: [{"title": "...", "key_concepts": "...", "file_path": "..."}]
            tutorial_outline_json = await call_gpt4(outline_prompt, response_format="JSON")


            # 6b. Save Tutorial to DB
            tutorial_entry = await db.tutorials.create(
                repo_id=repo_id,
                level=level,
                title=f"{level} Guide for {repo_name}",
                overview=f"An AI-generated {level} overview of {repo_name}.",
                overview_diagram_mermaid=main_diagram
            )
            tutorial_id = tutorial_entry.tutorial_id


            # 7. Module & Quiz Generation (Looping through the outline)
            for index, module_outline in enumerate(tutorial_outline_json):
                # 7a. === PROMPT 2: GENERATE MODULE CONTENT ===
                # (See Phase 2a for prompt details)
                
                # Load the actual code file content to pass to the AI
                file_content = await read_file_content(local_repo_path, module_outline['file_path'])


                module_prompt = create_gpt_module_prompt(
                    level=level,
                    module_outline=module_outline,
                    file_content=file_content,
                    full_outline=tutorial_outline_json # Give context of the whole tutorial
                )
                
                # Expect a single JSON object: {"title": ..., "content_markdown": ..., "code_snippet": ...}
                module_data_json = await call_gpt4(module_prompt, response_format="JSON")


                # 7b. Save Module to DB
                module_entry = await db.modules.create(
                    tutorial_id=tutorial_id,
                    order_index=index,
                    title=module_data_json['title'],
                    content_markdown=module_data_json['content_markdown'],
                    file_path=module_outline['file_path'], # Use file_path from outline
                    code_snippet=module_data_json['code_snippet'],
                    diagram_mermaid=module_data_json.get('diagram_mermaid')
                )
                module_id = module_entry.module_id


                # 7c. === PROMPT 3: GENERATE QUIZ ===
                # (See Phase 2a for prompt details)
                quiz_prompt = create_gpt_quiz_prompt(
                    module_data_json['content_markdown'], 
                    module_data_json['code_snippet']
                )
                
                # Expect a single JSON object: {"question_text": ..., "options": [...]}
                quiz_data_json = await call_gpt4(quiz_prompt, response_format="JSON")
                
                # 7d. Save Quiz to DB
                await db.quizzes.create(
                    module_id=module_id,
                    question_text=quiz_data_json['question_text'],
                    options=quiz_data_json['options'] # e.g., [{"text": "A", "is_correct": true}, ...]
                )


        # 8. Finalize: Update repo status
        await db.repositories.update(repo_id, status='COMPLETED')


    except Exception as e:
        # 9. Handle Failure
        await db.repositories.update(repo_id, status='FAILED', error_message=str(e))
    
    finally:
        # 10. Cleanup
        # Securely delete the cloned repository from /tmp/
        await cleanup_temp_directory(local_repo_path)



Phase 2a: AI Prompt Engineering Strategy (NEW)

This is the core logic for integrating GPT-4. We will use a 3-Prompt Chain to ensure reliable, structured output. All GPT-4 calls must request JSON mode.

Inputs to the AI System:

code_structure_json: The full file/class/function/import map from tree-sitter.
code_summaries: Technical summaries of key functions from CodeBERT.
file_contents: The actual text of source code files, loaded on demand.
tutorial_level: 'BEGINNER', 'INTERMEDIATE', or 'ADVANCED'.

Prompt 1: Generate Tutorial Outline
Goal: To create a logical, step-by-step plan for the tutorial before writing any content. Function: create_gpt_outline_prompt(level, code_structure_json, code_summaries)

SYSTEM:
You are an expert developer and senior technical curriculum designer. Your task is to
create a step-by-step tutorial outline based on a code repository's structure.


You will be given the repository structure (from tree-sitter) and technical summaries
of key functions (from CodeBERT).


The tutorial level MUST be: [level]


Analyze the provided context and generate a JSON array of tutorial modules.
Each module object must have:
- "title": A short, engaging title for the module (e.g., "Setting up the Server").
- "key_concepts": A brief string explaining what this module will teach.
- "file_path": The main file from the repo to focus on for this module.


Respond ONLY with the raw JSON array.


USER:
Tutorial Level: [level]
Code Structure: [Insert minified code_structure_json here]
Code Summaries: [Insert relevant code_summaries here]

Expected JSON Output (Example):
[
  {
    "title": "Understanding the Entrypoint",
    "key_concepts": "Learn how the application starts and imports main modules.",
    "file_path": "src/index.js"
  },
  {
    "title": "Exploring the API Router",
    "key_concepts": "See how API routes are defined and connected to controllers.",
    "file_path": "src/routes/api.js"
  },
  {
    "title": "Database Connection",
    "key_concepts": "Analyze how the app connects to the PostgreSQL database.",
    "file_path": "src/config/db.js"
  }
]

Prompt 2: Generate Module Content

Goal: To be called inside a loop for each module in the outline from Prompt 1. This prompt writes the actual content for a single module. Function: create_gpt_module_prompt(level, module_outline, file_content, full_outline)

SYSTEM:
You are a friendly, engaging technical writer. Your task is to write a single
tutorial module for a [level] developer.


You must follow the module's plan and use the provided source code.


Your response MUST be a single JSON object with the following keys:
- "title": The title of this module.
- "content_markdown": The full tutorial text in GitHub-flavored Markdown.
  - Explain the code and concepts clearly.
  - If the logic is complex, generate a Mermaid.js 'graph TD' diagram within the
    markdown (e.g., ```mermaid\ngraph TD\n A --> B\n```) to visualize it.
- "code_snippet": The exact code snippet from the file that is most relevant
  to this lesson.
  - **CRITICAL:** This snippet MUST be runnable in a Sandpack (vanilla-ts)
    environment. This means you may need to add mock data, helper functions,
    or stubs for imports that are outside this file.
- "diagram_mermaid": The Mermaid.js diagram string IF you generated one,
  otherwise null.


Respond ONLY with the raw JSON object.


USER:
Tutorial Level: [level]


Full Tutorial Outline (for context):
[Insert tutorial_outline_json from Prompt 1 here]


Current Module to Write:
[Insert single module_outline object here, e.g., {"title": "Exploring the API Router", ...}]


Source Code for [module_outline.file_path]:
---
[Insert full file_content string here]
---

Expected JSON Output (Example):
{
  "title": "Exploring the API Router",
  "content_markdown": "Welcome! Let's see how our app handles API requests.\n\nWe use Express.js to create a router. All our API routes are defined in `src/routes/api.js`.\n\nHere's the flow:\n1. A request hits the server.\n2. Express matches the path.\n3. The request is sent to a 'controller' function.\n\n```mermaid\ngraph TD\n  Req[/api/v1/users] --> Router[api.js]\n  Router --> Ctrl[userController.getUsers]\n  Ctrl --> DB[Database]\n```\n\nLet's look at the code.",
  "code_snippet": "// Mock dependencies for Sandpack\nconst mockExpress = { Router: () => ({ get: (path, handler) => console.log(`Route defined: GET ${path}`) }) };\nconst mockController = { getUsers: () => console.log('Called getUsers') };\n\n// --- Actual Code from src/routes/api.js ---\nconst express = mockExpress;\nconst router = express.Router();\nconst userController = mockController;\n\nrouter.get('/users', userController.getUsers);\n\nconsole.log('Router setup complete.');\n// --- End of Code ---",
  "diagram_mermaid": "graph TD\n  Req[/api/v1/users] --> Router[api.js]\n  Router --> Ctrl[userController.getUsers]\n  Ctrl --> DB[Database]"
}

Prompt 3: Generate Quiz Question

Goal: To be called after Prompt 2, using its output to generate a single quiz question. Function: create_gpt_quiz_prompt(content_markdown, code_snippet)

SYSTEM:
You are a technical instructor. Your task is to create a single, high-quality
multiple-choice question based on the provided tutorial content and code.


The question should test a key concept from the lesson.


Your response MUST be a single JSON object with the following keys:
- "question_text": The text of the question.
- "options": An array of objects, each with:
  - "text": The answer option.
  - "is_correct": A boolean (true for only one option, false for others).


Shuffle the correct answer. Respond ONLY with the raw JSON object.


USER:
Tutorial Content:
[Insert content_markdown from Prompt 2's output]


Code Snippet:
[Insert code_snippet from Prompt 2's output]

Expected JSON Output (Example):
{
  "question_text": "In the provided code snippet, which function is called when a GET request is made to the '/users' path?",
  "options": [
    { "text": "router.get()", "is_correct": false },
    { "text": "express.Router()", "is_correct": false },
    { "text": "userController.getUsers", "is_correct": true },
    { "text": "console.log()", "is_correct": false }
  ]
}

Phase 3: Backend API Design (FastAPI)

Define the "contract" for your frontend. These endpoints will be consumed by Next.js using React Query.

File: backend/app/main.py

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
import uuid # Import uuid


# Assume auth_user = Depends(get_current_user) is your JWT auth dependency
# Assume User is a Pydantic model or DB model for the authenticated user


app = FastAPI()


# --- Pydantic Models ---
class RepoCreate(BaseModel):
    github_url: str


class ModuleUpdate(BaseModel):
    title: str
    content_markdown: str
    code_snippet: str


class QuizSubmit(BaseModel):
    quiz_id: uuid.UUID
    submitted_answer: str # or JSON for complex answers


class ProgressUpdate(BaseModel):
    module_id: uuid.UUID


# --- BullMQ Job Enqueue (Conceptual) ---
# This function adds a job to the Redis queue for the worker to pick up
async def add_analysis_job_to_queue(repo_id: uuid.UUID, github_url: str):
    # This is where you interface with BullMQ
    print(f"Adding job to BullMQ: repo_id={repo_id}, url={github_url}")
    # await bullmq_queue.add("analyze-repo", {"repo_id": repo_id, "github_url": github_url})


# --- API Endpoints ---


@app.post("/api/repositories")
async def submit_repository(
    repo_data: RepoCreate, 
    background_tasks: BackgroundTasks, 
    user: User = auth_user # Depends(get_current_user)
):
    """
    Submit a new GitHub URL for analysis.
    Returns 202 Accepted immediately.
    """
    # 1. Check if URL already exists
    existing = await db.repositories.get_by_url(repo_data.github_url)
    if existing:
        return existing # Or return a 409 Conflict


    # 2. Create 'PENDING' entry in DB
    new_repo = await db.repositories.create(
        user_id=user.user_id,
        github_url=repo_data.github_url,
        status='PENDING'
    )
    
    # 3. Add job to background queue (BullMQ)
    # Use FastAPI's BackgroundTasks for non-blocking call to BullMQ
    background_tasks.add_task(
        add_analysis_job_to_queue, new_repo.repo_id, new_repo.github_url
    )


    # 4. Return the new repo entry
    return new_repo


@app.get("/api/repositories")
async def get_user_repositories(user: User = auth_user):
    """
    Get all repositories submitted by the user and their status.
    """
    repos = await db.repositories.get_by_user(user.user_id)
    return repos


@app.get("/api/repositories/{repo_id}")
async def get_repository_details(repo_id: uuid.UUID, user: User = auth_user):
    """
    Get details for one repo, including its generated tutorials.
    """
    repo = await db.repositories.get_one(repo_id, user.user_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    tutorials = await db.tutorials.get_by_repo(repo_id)
    return {"repository": repo, "tutorials": tutorials}


@app.get("/api/tutorials/{tutorial_id}")
async def get_tutorial_content(tutorial_id: uuid.UUID, user: User = auth_user):
    """
    THE MAIN ENDPOINT for the tutorial player.
    Returns the full tutorial, all modules, and all quizzes.
    """
    # This DB call should do a complex JOIN to get all data in one go
    tutorial_data = await db.tutorials.get_full_tutorial_data(tutorial_id, user.user_id)
    if not tutorial_data:
        raise HTTPException(status_code=404, detail="Tutorial not found")
    
    # The DB query should structure the data as nested JSON
    # e.g., { tutorial_info, modules: [ { module_info, quiz: { quiz_info } } ] }
    return tutorial_data


@app.post("/api/progress/complete_module")
async def mark_module_complete(progress: ProgressUpdate, user: User = auth_user):
    """
    Called when a user clicks "Next" on a module.
    """
    await db.user_progress.create_or_update(
        user_id=user.user_id,
        module_id=progress.module_id,
        completed_at=now() # Assumes now() is defined
    )
    return {"status": "success"}


@app.post("/api/progress/submit_quiz")
async def submit_quiz_answer(submission: QuizSubmit, user: User = auth_user):
    """
    Check a user's quiz answer.
    """
    quiz = await db.quizzes.get_one(submission.quiz_id)
    # Logic to check submission.submitted_answer against quiz.options/correct_answer
    is_correct = await check_answer(quiz, submission.submitted_answer)
    
    # Record the score
    await db.user_progress.update_score(
        user_id=user.user_id,
        module_id=quiz.module_id, # Assumes 1-1 quiz-module
        score=(1 if is_correct else 0)
    )
    return {"is_correct": is_correct}


# --- Phase 6: Custom Authoring ---
@app.put("/api/modules/{module_id}")
async def update_module_content(
    module_id: uuid.UUID, 
    data: ModuleUpdate, 
    user: User = auth_user
):
    """
    Allows a user to manually edit a generated module.
    """
    # Check if user owns the tutorial this module belongs to
    is_owner = await db.check_module_ownership(user.user_id, module_id)
    if not is_owner:
        raise HTTPException(status_code=403, detail="Forbidden")


    updated_module = await db.modules.update(
        module_id=module_id,
        title=data.title,
        content_markdown=data.content_markdown,
        code_snippet=data.code_snippet
    )
    return updated_module

Phase 4: Frontend Implementation (Next.js 15)

Use the App Router, React Query (useQuery, useMutation), and a component-based structure.

Page Structure (App Router) (/frontend/replo) -> FE Frontend

app/dashboard/page.tsx: Main dashboard.
app/repo/[repoId]/page.tsx: Shows analysis status and tutorial links.
app/tutorial/[tutorialId]/page.tsx: The main player.
app/edit/[tutorialId]/page.tsx: The authoring panel.
Core Component Breakdown

1. app/dashboard/components/RepoSubmitForm.tsx
UI: A single <input> for the GitHub URL and a <button>.
Logic:
Uses useMutation from React Query to call POST /api/repositories.
const { mutate, isPending } = useMutation({ mutationFn: (url) => api.post('/repositories', { github_url: url }) });
On onSuccess, invalidate the repositories list query to refresh it.

2. app/dashboard/components/RepoList.tsx
UI: A grid or list of cards. Each card shows repo.name and a status badge (e.g., "Pending", "Analyzing", "Completed").
Logic:
Uses useQuery to fetch GET /api/repositories.
const { data, isLoading } = useQuery({ queryKey: ['repos'], queryFn: () => api.get('/repositories') });
CRITICAL: Add a refetchInterval to poll for status changes.
refetchInterval: data?.some(repo => ['PENDING', 'ANALYZING'].includes(repo.status)) ? 5000 : false,
When a repo status is 'COMPLETED', the card becomes a <Link href={'/repo/${repo.repo_id}'}>.
3. app/tutorial/[tutorialId]/components/TutorialPlayer.tsx (The Main App)
State:
const [currentModuleIndex, setCurrentModuleIndex] = useState(0);
const { data: tutorial, isLoading } = useQuery({ queryKey: ['tutorial', tutorialId], queryFn: () => api.get('/tutorials/${tutorialId}') });
const currentModule = tutorial?.modules?.[currentModuleIndex];
UI: A 2-column, full-height split-screen layout.
Left Pane (<TutorialContent />):
<h3>{currentModule.title}</h3>
ProgressBar component (calculates (currentModuleIndex + 1) / tutorial.modules.length).
MarkdownRenderer component (see below).
Quiz component (conditionally rendered: if (currentModule.quiz)).
Navigation div with "Previous" and "Next" buttons.
Right Pane (<CodeSandbox />):
Renders the Sandpack component.
files prop will be: { [currentModule.file_path]: currentModule.code_snippet }.
Note: Sandpack setup is non-trivial. You must provide the correct template (e.g., 'react', 'node', 'vanilla-ts'). This is a major constraint. Your AI must be prompted to generate code for a specific, runnable environment that Sandpack supports.
4. app/tutorial/[tutorialId]/components/MarkdownRenderer.tsx
Purpose: Renders content_markdown and handles Mermaid diagrams.
Libraries: react-markdown, remark-gfm, remark-mermaid-js.

Logic:
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMermaid from 'remark-mermaid-js';


export const MarkdownRenderer = ({ content }) => (
  <ReactMarkdown
    remarkPlugins={[remarkGfm, remarkMermaid]}
    className="prose" // For TailwindCSS typography
  >
    {content}
  </ReactMarkdown>
);


5. app/tutorial/[tutorialId]/components/Quiz.tsx
UI: Renders the quiz.question_text and maps quiz.options to radio buttons or checkboxes.
Logic:
useState to track the selectedAnswer.
useMutation to call POST /api/progress/submit_quiz.
onSubmit, call the mutation. On onSuccess, show a "Correct!" or "Try Again" message based on the is_correct response.

Phase 5: Worker & Queue Integration (BullMQ + Redis)
This connects Phase 3 (API) and Phase 2 (Worker).

FastAPI (Backend):
When POST /api/repositories is hit, it only does two things:
Create a PENDING repo in PostgreSQL.
Add a job to the BullMQ (Redis) queue.
It must return a 202 Accepted response immediately.
Worker Process (Separate Service):
This is a separate process running on your server (e.g., in its own Docker container).
It continuously listens to the Redis queue.
When a job appears, it executes the entire process_repository_analysis function from Phase 2.
This process needs access to tree-sitter, CodeBERT models, GPT-4 API keys, and the PostgreSQL database.
Phase 6: Custom Authoring Panel (Enhancement)
Page: app/edit/[tutorialId]/page.tsx
UI:
Fetches data from GET /api/v1/tutorials/{tutorial_id}.
Renders a list of modules.
Each module is not read-only. Instead of <MarkdownRenderer>, you use a <textarea> or a rich text editor like TipTap.
Each module has a "Save" button.
Logic:
The "Save" button triggers a useMutation to call PUT /api/v1/modules/{module.module_id}.
The body of the request is { title, content_markdown, code_snippet } from the editor's state.
Suggested Rollout Strategy (MVP)
This is a massive project. Build it in stages.
MVP 1: The Core Pipeline
Focus only on JavaScript/TypeScript repos (Sandpack's specialty).
Generate only the 'BEGINNER' tutorial.
No quizzes. No custom authoring.
Get the Repo -> Analyze -> Store -> View loop working perfectly.
MVP 2: Add Interactivity
Implement quizzes (Phase 2, 3, 4).
Implement progress tracking (Phase 3, 4).
MVP 3: Add Depth & Polish
Add 'INTERMEDIATE' and 'ADVANCED' tutorial generation (this is just a prompt-engineering challenge).
Add the custom authoring panel (Phase 6).
Improve the dependency graph visualization.



