# ./backend/app/core/generation_service.py
import json
from typing import Dict, List, Any

def create_gpt_outline_prompt(level: str, code_structure_json: Dict[str, Any], code_summaries: Dict[str, str]) -> str:
    """
    Create a prompt for GPT-4 to generate a tutorial outline.
    
    Args:
        level: The tutorial level (BEGINNER, INTERMEDIATE, ADVANCED)
        code_structure_json: The code structure from tree-sitter analysis
        code_summaries: Technical summaries of key functions from CodeBERT
        
    Returns:
        A formatted prompt string for GPT-4
    """
    # Convert inputs to strings for the prompt
    code_structure_str = json.dumps(code_structure_json)
    code_summaries_str = json.dumps(code_summaries)
    
    # Create the system prompt
    system_prompt = f"""
You are an expert developer and senior technical curriculum designer. Your task is to
create a step-by-step tutorial outline based on a code repository's structure.

You will be given the repository structure (from tree-sitter) and technical summaries
of key functions (from CodeBERT).

The tutorial level MUST be: {level}

Analyze the provided context and generate a JSON array of tutorial modules.
Each module object must have:
- "title": A short, engaging title for the module (e.g., "Setting up the Server").
- "key_concepts": A brief string explaining what this module will teach.
- "file_path": The main file from the repo to focus on for this module.

Respond ONLY with the raw JSON array.
"""

    # Create the user prompt
    user_prompt = f"""
Tutorial Level: {level}
Code Structure: {code_structure_str}
Code Summaries: {code_summaries_str}

Expected JSON Output (Example):
[
  {{
    "title": "Understanding the Entrypoint",
    "key_concepts": "Learn how the application starts and imports main modules.",
    "file_path": "src/index.js"
  }},
  {{
    "title": "Exploring the API Router",
    "key_concepts": "See how API routes are defined and connected to controllers.",
    "file_path": "src/routes/api.js"
  }},
  {{
    "title": "Database Connection",
    "key_concepts": "Analyze how the app connects to the PostgreSQL database.",
    "file_path": "src/config/db.js"
  }}
]
"""
    
    # Combine the prompts
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    return full_prompt


def create_gpt_module_prompt(level: str, module_outline: Dict[str, str], file_content: str, full_outline: List[Dict[str, str]]) -> str:
    """
    Create a prompt for GPT-4 to generate module content.
    
    Args:
        level: The tutorial level (BEGINNER, INTERMEDIATE, ADVANCED)
        module_outline: The outline for this specific module
        file_content: The content of the file for this module
        full_outline: The full tutorial outline for context
        
    Returns:
        A formatted prompt string for GPT-4
    """
    # Convert the full outline to a string for the prompt
    full_outline_str = json.dumps(full_outline)
    
    # Create the system prompt
    system_prompt = f"""
You are a friendly, engaging technical writer. Your task is to write a single
tutorial module for a {level} developer.

You must follow the module's plan and use the provided source code.

Your response MUST be a single JSON object with the following keys:
- "title": The title of this module.
- "content_markdown": The full tutorial text in GitHub-flavored Markdown.
  - Explain the code and concepts clearly.
  - If the logic is complex, generate a Mermaid.js 'graph TD' diagram within the
    markdown (e.g., ```mermaid\\ngraph TD\\n A --> B\\n```) to visualize it.
- "code_snippet": The exact code snippet from the file that is most relevant
  to this lesson.
  - **CRITICAL:** This snippet MUST be runnable in a Sandpack (vanilla-ts)
    environment. This means you may need to add mock data, helper functions,
    or stubs for imports that are outside this file.
- "diagram_mermaid": The Mermaid.js diagram string IF you generated one,
  otherwise null.

Respond ONLY with the raw JSON object.
"""

    # Create the user prompt
    user_prompt = f"""
Tutorial Level: {level}

Full Tutorial Outline (for context):
{full_outline_str}

Current Module to Write:
{json.dumps(module_outline)}

Source Code for {module_outline.get('file_path', 'unknown')}:
---
{file_content}
---

Expected JSON Output (Example):
{{
  "title": "Exploring the API Router",
  "content_markdown": "Welcome! Let's see how our app handles API requests.\\n\\nWe use Express.js to create a router. All our API routes are defined in `src/routes/api.js`.\\n\\nHere's the flow:\\n1. A request hits the server.\\n2. Express matches the path.\\n3. The request is sent to a 'controller' function.\\n\\n```mermaid\\ngraph TD\\n  Req[/api/v1/users] --> Router[api.js]\\n  Router --> Ctrl[userController.getUsers]\\n  Ctrl --> DB[Database]\\n```\\n\\nLet's look at the code.",
  "code_snippet": "// Mock dependencies for Sandpack\\nconst mockExpress = {{ Router: () => ({{ get: (path, handler) => console.log(`Route defined: GET ${{path}}`) }}) }};\\nconst mockController = {{ getUsers: () => console.log('Called getUsers') }};\\n\\n// --- Actual Code from src/routes/api.js ---\\nconst express = mockExpress;\\nconst router = express.Router();\\nconst userController = mockController;\\n\\nrouter.get('/users', userController.getUsers);\\n\\nconsole.log('Router setup complete.');\\n// --- End of Code ---",
  "diagram_mermaid": "graph TD\\n  Req[/api/v1/users] --> Router[api.js]\\n  Router --> Ctrl[userController.getUsers]\\n  Ctrl --> DB[Database]"
}}
"""
    
    # Combine the prompts
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    return full_prompt


def create_gpt_quiz_prompt(content_markdown: str, code_snippet: str) -> str:
    """
    Create a prompt for GPT-4 to generate a quiz question.
    
    Args:
        content_markdown: The markdown content of the module
        code_snippet: The code snippet from the module
        
    Returns:
        A formatted prompt string for GPT-4
    """
    # Create the system prompt
    system_prompt = """
You are a technical instructor. Your task is to create a single, high-quality
multiple-choice question based on the provided tutorial content and code.

The question should test a key concept from the lesson.

Your response MUST be a single JSON object with the following keys:
- "question_text": The text of the question.
- "options": An array of objects, each with:
  - "text": The answer option.
  - "is_correct": A boolean (true for only one option, false for others).

Shuffle the correct answer. Respond ONLY with the raw JSON object.
"""

    # Create the user prompt
    user_prompt = f"""
Tutorial Content:
{content_markdown}

Code Snippet:
{code_snippet}

Expected JSON Output (Example):
{{
  "question_text": "In the provided code snippet, which function is called when a GET request is made to the '/users' path?",
  "options": [
    {{ "text": "router.get()", "is_correct": false }},
    {{ "text": "express.Router()", "is_correct": false }},
    {{ "text": "userController.getUsers", "is_correct": true }},
    {{ "text": "console.log()", "is_correct": false }}
  ]
}}
"""
    
    # Combine the prompts
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    return full_prompt