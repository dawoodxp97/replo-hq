---

PROMPT START

---

I need to build a clean AI orchestration layer for my FastAPI project that generates interactive tutorials from GitHub repositories. The architecture should be inspired by a production system I've seen, but adapted for my specific needs.

## Project Context

**Tech Stack:**

- FastAPI (Python web framework)
- PostgreSQL (single database)
- Redis (caching and job queue)
- ARQ (async job worker for background tasks)
- OpenRouter API (for open-source LLMs like Llama, Mistral, etc.)

**Use Case:**
Users submit GitHub repository URLs → System extracts repo content using tree-sitter and codeBERT → AI generates interactive tutorials from the code structure and content.

**Current State:**

- GitHub repo extraction: ✅ Working
- Content parsing (tree-sitter, codeBERT): ✅ Working
- AI layer: ❌ Need to build

## Architecture Requirements

I want a clean, production-ready AI layer with these components:

### 1. **Core Components** (Inspired by RecruiterFlow's AI Agents)

-> TutorialOrchestrator → TutorialAgent → TutorialSteps → AI Layer (OpenRouter)

**TutorialOrchestrator:**

- Entry point for tutorial generation requests
- Manages execution flow
- Handles validation and error recovery
- Tracks execution status in PostgreSQL
- Submits async jobs to ARQ

**TutorialAgent:**

- Represents a tutorial generation workflow
- Contains multiple steps (analysis, outline, content generation, etc.)
- Manages state between steps
- Stores execution data

**Step (Abstract Base Class):**

- Individual AI task (e.g., "analyze repo structure", "generate tutorial outline")
- Has validate() and execute() methods
- Formats prompts using templates
- Calls AI layer
- Processes and validates responses

### 2. **Database Schema**

Create PostgreSQL tables to store:

-- Tutorial generation instances
tutorial_instance:

- id (PK)
- user_id (FK)
- repo_url
- status (pending/running/completed/failed)
- created_at
- updated_at

-- Execution tracking
tutorial_execution:

- id (PK)
- tutorial_instance_id (FK)
- status (running/completed/failed)
- current_step_order (INT)
- started_at
- completed_at

-- Step execution tracking
tutorial_step_execution:

- id (PK)
- tutorial_execution_id (FK)
- step_type (analysis/outline/content_generation/refinement)
- step_order (INT)
- status (pending/running/completed/failed)
- input_data (JSONB - repo context)
- output_data (JSONB - AI response)
- prompt_used (TEXT)
- llm_response (TEXT)
- error_message (TEXT)
- started_at
- completed_at

-- Step configuration (prompt templates)
tutorial_step_config:

- id (PK)
- step_type
- name
- description
- prompt_template (TEXT - with placeholders)
- system_prompt (TEXT)
- model_name (default model)
- max_tokens (INT)
- temperature (FLOAT)
- is_active (BOOLEAN)### 3. **AI Layer with OpenRouter**

**OpenRouter Integration:**

- Base URL: `https://openrouter.ai/api/v1/chat/completions`
- API Key authentication
- Support multiple models (Llama 3.1, Mistral, Claude via OpenRouter, etc.)
- Retry logic with exponential backoff
- Error handling

**Key Function:**
async def send_llm_message(
messages: List[Dict],
model_name: str = "qwen/qwen3-coder:free",
temperature: float = 0.7,
max_tokens: int = 4096
) -> str:
"""Send message to OpenRouter and return response"""### 4. **Step Implementation Pattern**

Each step should follow this pattern:

class AnalyzeRepoStructureStep(Step):
"""Analyzes repository structure and identifies key components"""

    SYSTEM_PROMPT = "You are an expert code analyst..."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.step_type = "analyze_repo_structure"

    async def execute(self):
        # 1. Prepare prompt data
        prompt_data = self.prepare_prompt_data()

        # 2. Load prompt template from config
        template = self.get_prompt_template()

        # 3. Format prompt with data
        prompt = template.format(**prompt_data)

        # 4. Construct messages
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        # 5. Call AI
        response = await send_llm_message(messages, **self.llm_config)

        # 6. Validate and parse response
        parsed = self.parse_response(response)

        # 7. Store output
        self.output_data = parsed

        return parsed### 5. **ARQ Integration Pattern**

# In arq_worker.py

async def generate_tutorial_task(ctx, tutorial_instance_id: int):
"""ARQ background task for tutorial generation"""
orchestrator = TutorialOrchestrator(
tutorial_instance_id=tutorial_instance_id
)
result = await orchestrator.execute()
return result

# In api route

@app.post("/tutorials/generate")
async def generate_tutorial(repo_url: str, user_id: int): # 1. Create tutorial instance
instance = create_tutorial_instance(repo_url, user_id)

    # 2. Submit to ARQ
    job = await arq_redis.enqueue_job(
        'generate_tutorial_task',
        tutorial_instance_id=instance.id
    )

    return {"job_id": job.job_id, "instance_id": instance.id}### 6. **Tutorial Generation Steps**

Implement these steps in order:

1. **AnalyzeRepoStructureStep**
   - Input: Repo tree structure, file list, languages detected
   - Output: JSON with key components, entry points, architecture overview
2. **GenerateTutorialOutlineStep**
   - Input: Previous step output + repo content summary
   - Output: JSON with tutorial structure (chapters, sections, topics)
3. **GenerateTutorialContentStep**
   - Input: Outline + relevant code snippets
   - Output: Markdown content for each section
4. **RefineTutorialStep** (Optional)
   - Input: Generated content
   - Output: Refined, polished tutorial with better explanations

### 7. **Prompt Template System**

Store templates with placeholders:

ANALYZE_REPO_PROMPT = """
Analyze the following repository structure and provide insights:

**Repository Information:**

- Name: {repo_name}
- Primary Language: {primary_language}
- Description: {repo_description}

**File Structure:**
{file_tree}

**Key Files Content:**
{key_files_content}

**Task:**
Identify:

1. Main entry points
2. Core functionality/features
3. Architecture patterns used
4. Dependencies and how they're used
5. Suggested tutorial flow

Respond in JSON format:
{response_format}
"""### 8. **Response Validation**

Use Pydantic models to validate AI responses:

from pydantic import BaseModel

class RepoAnalysis(BaseModel):
entry_points: List[str]
core_features: List[str]
architecture_pattern: str
tutorial_flow: List[Dict[str, str]]

class TutorialOutline(BaseModel):
title: str
chapters: List[Dict[str, Any]]
estimated_duration: str## Implementation Tasks

Please implement the following:

### Phase 1: Core Infrastructure

1. Create database tables (use Alembic migrations)
2. Create base `Step` abstract class
3. Implement `TutorialAgent` class
4. Implement `TutorialOrchestrator` class

### Phase 2: AI Layer

5. Implement OpenRouter client (`ai/client.py`)
6. Add retry logic and error handling
7. Add response parsing utilities
8. Add prompt template management (load from DB or config)

### Phase 3: Steps Implementation

9. Implement `AnalyzeRepoStructureStep`
10. Implement `GenerateTutorialOutlineStep`
11. Implement `GenerateTutorialContentStep`
12. Implement `RefineTutorialStep`

### Phase 4: ARQ Integration

13. Create ARQ worker configuration
14. Implement background tasks
15. Add job status tracking
16. Add webhook/notification on completion

### Phase 5: API Endpoints

17. POST `/api/tutorials/generate` - Start generation
18. GET `/api/tutorials/{id}/status` - Check status
19. GET `/api/tutorials/{id}/result` - Get generated tutorial
20. POST `/api/tutorials/{id}/retry` - Retry failed step

## Code Organization

3. AI Layer with OpenRouter
   OpenRouter Integration:
   Base URL: https://openrouter.ai/api/v1/chat/completions
   API Key authentication
   Support multiple models (Llama 3.1, Mistral, Claude via OpenRouter, etc.)
   Retry logic with exponential backoff
   Error handling
   Key Function:
   async def send_llm_message(
   messages: List[Dict],
   model_name: str = "qwen/qwen3-coder:free",
   temperature: float = 0.7,
   max_tokens: int = 4096
   ) -> str:
   """Send message to OpenRouter and return response"""y Pattern\*\*: Separate DB access
4. **Factory Pattern**: Create step instances dynamically
5. **Async/Await**: All I/O operations should be async
6. **Type Hints**: Use everywhere for clarity
7. **Error Boundaries**: Proper exception handling at each layer

## Configuration

Use environment variables:

OPENROUTER_API_KEY=sk-or-xxx
DEFAULT_LLM_MODEL=qwen/qwen3-coder:free
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379## Testing Requirements

Include:

- Unit tests for each step
- Integration tests for orchestrator
- Mock OpenRouter API responses
- Test prompt template formatting
- Test error recovery

## Reference Implementation Patterns

Use patterns similar to this production code I've seen:

**Orchestrator execution loop:**
async def execute(self):
await self.agent.get_steps()
for step_instance in self.agent.steps:
await step_instance.validate()
await step_instance.create_step_execution_record()
result = await step_instance.execute()
await step_instance.update_step_execution_record(status="completed")

        if result.get("needs_human_review"):
            # Pause and wait for approval
            break

    await self.agent.mark_execution_complete()
    return result**Step base class structure:**

class Step(ABC):
def **init**(self, execution_id, step_config, input_data):
self.execution_id = execution_id
self.step_config = step_config
self.input_data = input_data
self.output_data = None

    @abstractmethod
    async def execute(self):
        pass

    def _format_json_for_prompt(self, data):
        return json.dumps(data, indent=2)## Success Criteria

The implementation is successful when:
✅ User can submit a repo URL and get a generated tutorial
✅ Each step logs its execution and results
✅ Failures are recoverable (can retry from failed step)
✅ Prompts are configurable via database
✅ Multiple models can be used via OpenRouter
✅ System handles rate limits gracefully
✅ ARQ workers process jobs asynchronously
✅ API provides real-time status updates

## Additional Features (Nice to Have)

- Streaming responses from LLM
- Caching of repo analysis results
- Support for incremental tutorial generation
- Web UI to view generation progress
- Webhook notifications on completion
- A/B testing different prompts
- Cost tracking per tutorial

Please implement this system with clean, production-ready code following best practices for FastAPI, async Python, and type safety. Start with Phase 1 and work through each phase systematically.

4. Step Implementation Pattern
   Each step should follow this pattern:

class AnalyzeRepoStructureStep(Step):
"""Analyzes repository structure and identifies key components"""

    SYSTEM_PROMPT = "You are an expert code analyst..."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.step_type = "analyze_repo_structure"

    async def execute(self):
        # 1. Prepare prompt data
        prompt_data = self.prepare_prompt_data()

        # 2. Load prompt template from config
        template = self.get_prompt_template()

        # 3. Format prompt with data
        prompt = template.format(**prompt_data)

        # 4. Construct messages
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        # 5. Call AI
        response = await send_llm_message(messages, **self.llm_config)

        # 6. Validate and parse response
        parsed = self.parse_response(response)

        # 7. Store output
        self.output_data = parsed

        return parsed

5. ARQ Integration Pattern:

# In arq_worker.py

async def generate_tutorial_task(ctx, tutorial_instance_id: int):
"""ARQ background task for tutorial generation"""
orchestrator = TutorialOrchestrator(
tutorial_instance_id=tutorial_instance_id
)
result = await orchestrator.execute()
return result

# In api route

@app.post("/tutorials/generate")
async def generate_tutorial(repo_url: str, user_id: int): # 1. Create tutorial instance
instance = create_tutorial_instance(repo_url, user_id)

    # 2. Submit to ARQ
    job = await arq_redis.enqueue_job(
        'generate_tutorial_task',
        tutorial_instance_id=instance.id
    )

    return {"job_id": job.job_id, "instance_id": instance.id}

6. Tutorial Generation Steps
   Implement these steps in order:
   6a:AnalyzeRepoStructureStep
   Input: Repo tree structure, file list, languages detected
   Output: JSON with key components, entry points, architecture overview
   6b:GenerateTutorialOutlineStep
   Input: Previous step output + repo content summary
   Output: JSON with tutorial structure (chapters, sections, topics)
   6c:GenerateTutorialContentStep
   Input: Outline + relevant code snippets
   Output: Markdown content for each section
   6d:RefineTutorialStep (Optional)
   Input: Generated content
   Output: Refined, polished tutorial with better explanations

7. Prompt Template System
   Store templates with placeholders:

ANALYZE_REPO_PROMPT = """
Analyze the following repository structure and provide insights:

**Repository Information:**

- Name: {repo_name}
- Primary Language: {primary_language}
- Description: {repo_description}

**File Structure:**
{file_tree}

**Key Files Content:**
{key_files_content}

**Task:**
Identify:

1. Main entry points
2. Core functionality/features
3. Architecture patterns used
4. Dependencies and how they're used
5. Suggested tutorial flow

Respond in JSON format:
{response_format}
"""

8. Response Validation
   Use Pydantic models to validate AI responses:

from pydantic import BaseModel

class RepoAnalysis(BaseModel):
entry_points: List[str]
core_features: List[str]
architecture_pattern: str
tutorial_flow: List[Dict[str, str]]

class TutorialOutline(BaseModel):
title: str
chapters: List[Dict[str, Any]]
estimated_duration: str

Implementation Tasks
Please implement the following:
Phase 1: Core Infrastructure
1a:Create database tables (use Alembic migrations)
1b:Create base Step abstract class
1c:Implement TutorialAgent class
1d:Implement TutorialOrchestrator class
Phase 2: AI Layer
2a:Implement OpenRouter client (ai/client.py)
2b:Add retry logic and error handling
2c:Add response parsing utilities
2d:Add prompt template management (load from DB or config)
Phase 3: Steps Implementation
3a:Implement AnalyzeRepoStructureStep
3b:Implement GenerateTutorialOutlineStep
3c:Implement GenerateTutorialContentStep
3d:Implement RefineTutorialStep
Phase 4: ARQ Integration
4a:Create ARQ worker configuration
4b:Implement background tasks
4c:Add job status tracking
4d:Add webhook/notification on completion
Phase 5: API Endpoints
5a: POST /api/tutorials/generate - Start generation
5b:GET /api/tutorials/{id}/status - Check status
5c:GET /api/tutorials/{id}/result - Get generated tutorial
5d:POST /api/tutorials/{id}/retry - Retry failed step

Code Organization:

app/
├── ai/
│ ├── **init**.py
│ ├── client.py # OpenRouter client
│ └── prompts.py # Prompt templates
├── orchestrator/
│ ├── **init**.py
│ ├── orchestrator.py # TutorialOrchestrator
│ ├── agent.py # TutorialAgent
│ └── step.py # Base Step class
├── steps/
│ ├── **init**.py
│ ├── analyze_repo.py
│ ├── generate_outline.py
│ ├── generate_content.py
│ └── refine_tutorial.py
├── models/
│ ├── **init**.py
│ ├── tutorial.py # SQLAlchemy models
│ └── schemas.py # Pydantic schemas
├── workers/
│ ├── **init**.py
│ └── tutorial_worker.py # ARQ tasks
└── api/
└── tutorials.py # FastAPI routes

Key Design Patterns to Follow:
-> Abstract Base Classes: Use ABC for Step class
-> Template Method Pattern: Step.execute() calls template methods
-> Strategy Pattern: Different steps for different AI tasks
-> Repository Pattern: Separate DB access
-> Factory Pattern: Create step instances dynamically
-> Async/Await: All I/O operations should be async
-> Type Hints: Use everywhere for clarity
-> Error Boundaries: Proper exception handling at each layer

Configuration
Use environment variables:
OPENROUTER_API_KEY=sk-or-xxx
DEFAULT_LLM_MODEL=qwen/qwen3-coder:free
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379

Testing Requirements
Include:
-> Unit tests for each step
-> Integration tests for orchestrator
-> Mock OpenRouter API responses
-> Test prompt template formatting
-> Test error recovery

Reference Implementation Patterns:
Use patterns similar to this production code I've seen:

Orchestrator execution loop:
async def execute(self):
await self.agent.get_steps()
for step_instance in self.agent.steps:
await step_instance.validate()
await step_instance.create_step_execution_record()
result = await step_instance.execute()
await step_instance.update_step_execution_record(status="completed")

        if result.get("needs_human_review"):
            # Pause and wait for approval
            break

    await self.agent.mark_execution_complete()
    return result

Success Criteria
The implementation is successful when:
✅ User can submit a repo URL and get a generated tutorial
✅ Each step logs its execution and results
✅ Failures are recoverable (can retry from failed step)
✅ Prompts are configurable via database
✅ Multiple models can be used via OpenRouter
✅ System handles rate limits gracefully
✅ ARQ workers process jobs asynchronously
✅ API provides real-time status updates

Additional Features (Nice to Have):
-> Streaming responses from LLM
-> Caching of repo analysis results
-> Support for incremental tutorial generation
-> Web UI to view generation progress
-> Webhook notifications on completion
-> A/B testing different prompts
-> Cost tracking per tutorial

Please implement this system with clean, production-ready code following best practices for FastAPI, async Python, and type safety. Start with Phase 1 and work through each phase systematically.
