# ./backend/app/workers/analysis_worker.py
import os
import json
import shutil
import asyncio
import logging
from typing import Dict, List, Any, Optional
import uuid

import git
from tree_sitter import Language, Parser
from transformers import AutoTokenizer, AutoModel
import torch
from openai import OpenAI

from ..db.session import SessionLocal
from ..models.repositories import Repository
from ..models.tutorials import Tutorial
from ..models.modules import Module
from ..models.quizzes import Quiz
from ..models.tutorial_generation import TutorialGeneration
from ..models.user_settings import UserSettings
from ..core.generation_service import create_gpt_outline_prompt, create_gpt_module_prompt, create_gpt_quiz_prompt
from ..core.llm_providers import create_llm_provider, LLMProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database session
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

# Helper function to read file content
async def read_file_content(repo_path: str, file_path: str) -> str:
    """Read the content of a file from the cloned repository."""
    try:
        full_path = os.path.join(repo_path, file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        else:
            logger.warning(f"File not found: {full_path}")
            return ""
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return ""

# Function to extract repository contents (key code files)
async def extract_repository_contents(repo_path: str, max_files: int = 50, max_file_size: int = 50000) -> Dict[str, str]:
    """
    Extract contents of key code files from the repository.
    Returns a dictionary mapping file paths to their contents.
    """
    repo_contents = {}
    code_extensions = ['.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php']
    
    try:
        file_count = 0
        for root, dirs, files in os.walk(repo_path):
            # Skip hidden directories and common ignored folders
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', '.git', 'dist', 'build']]
            
            for file in files:
                if file_count >= max_files:
                    break
                    
                # Check if it's a code file
                if any(file.endswith(ext) for ext in code_extensions):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, repo_path)
                    
                    # Skip if file is too large
                    try:
                        file_size = os.path.getsize(file_path)
                        if file_size > max_file_size:
                            continue
                    except:
                        continue
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            # Only include substantial files (more than just comments)
                            if len(content.strip()) > 50:
                                repo_contents[rel_path] = content
                                file_count += 1
                    except Exception as e:
                        logger.warning(f"Could not read file {rel_path}: {str(e)}")
                        continue
        
        logger.info(f"Extracted {len(repo_contents)} code files from repository")
        return repo_contents
    except Exception as e:
        logger.error(f"Error extracting repository contents: {str(e)}")
        return {}

# Tree-sitter analysis function
async def run_tree_sitter_analysis(repo_path: str) -> Dict[str, Any]:
    """
    Analyze the repository structure using tree-sitter.
    Returns a JSON object representing the codebase structure.
    """
    logger.info(f"Starting tree-sitter analysis on {repo_path}")
    
    # Initialize tree-sitter
    try:
        # Build tree-sitter language libraries if not already built
        Language.build_library(
            'build/languages.so',
            [
                'vendor/tree-sitter-javascript',
                'vendor/tree-sitter-python',
                'vendor/tree-sitter-typescript'
            ]
        )
        
        # Load languages
        JS_LANGUAGE = Language('build/languages.so', 'javascript')
        PY_LANGUAGE = Language('build/languages.so', 'python')
        TS_LANGUAGE = Language('build/languages.so', 'typescript')
        
        # Create parsers
        js_parser = Parser()
        js_parser.set_language(JS_LANGUAGE)
        
        py_parser = Parser()
        py_parser.set_language(PY_LANGUAGE)
        
        ts_parser = Parser()
        ts_parser.set_language(TS_LANGUAGE)
        
        # Initialize result structure
        result = {
            "files": [],
            "functions": [],
            "classes": [],
            "imports": []
        }
        
        # Walk through the repository
        for root, _, files in os.walk(repo_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_path)
                
                # Skip hidden files, node_modules, etc.
                if (file.startswith('.') or 
                    'node_modules' in file_path or 
                    '__pycache__' in file_path or
                    'venv' in file_path):
                    continue
                
                # Determine file type and parser
                parser = None
                if file.endswith('.js'):
                    parser = js_parser
                elif file.endswith('.py'):
                    parser = py_parser
                elif file.endswith('.ts') or file.endswith('.tsx'):
                    parser = ts_parser
                
                if parser:
                    try:
                        with open(file_path, 'rb') as f:
                            content = f.read()
                        
                        # Parse the file
                        tree = parser.parse(content)
                        
                        # Add file to result
                        file_info = {
                            "path": rel_path,
                            "size": len(content)
                        }
                        result["files"].append(file_info)
                        
                        # Extract functions, classes, imports (simplified)
                        # In a real implementation, you would traverse the AST
                        # and extract detailed information
                        
                        # For now, we'll just add placeholder data
                        if len(content) > 0:
                            result["functions"].append({
                                "name": f"function_in_{rel_path}",
                                "file": rel_path,
                                "line": 1
                            })
                    
                    except Exception as e:
                        logger.error(f"Error parsing {file_path}: {str(e)}")
        
        logger.info(f"Tree-sitter analysis complete. Found {len(result['files'])} files.")
        return result
    
    except Exception as e:
        logger.error(f"Tree-sitter analysis failed: {str(e)}")
        # Return minimal structure in case of failure
        return {
            "files": [],
            "functions": [],
            "classes": [],
            "imports": []
        }

# CodeBERT summarization function
async def run_codebert_summarization(repo_path: str, code_structure: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate technical summaries for key functions using CodeBERT.
    Returns a dictionary mapping function names to summaries.
    """
    logger.info("Starting CodeBERT summarization")
    
    try:
        # Initialize CodeBERT model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
        model = AutoModel.from_pretrained("microsoft/codebert-base")
        
        # Move model to GPU if available
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(device)
        
        summaries = {}
        
        # Process each function identified in the code structure
        for func in code_structure["functions"]:
            func_name = func["name"]
            file_path = func["file"]
            
            # Read the file content
            file_content = await read_file_content(repo_path, file_path)
            
            # For a real implementation, you would extract the specific function code
            # Here we'll use a simplified approach
            
            # Tokenize the code
            inputs = tokenizer(file_content, return_tensors="pt", truncation=True, max_length=512)
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Get embeddings
            with torch.no_grad():
                outputs = model(**inputs)
            
            # Use the [CLS] token embedding as a representation of the code
            code_embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            
            # In a real implementation, you would use this embedding to generate a summary
            # For now, we'll just create a placeholder summary
            summaries[func_name] = f"This function appears to handle core functionality in {file_path}."
        
        logger.info(f"CodeBERT summarization complete. Generated {len(summaries)} summaries.")
        return summaries
    
    except Exception as e:
        logger.error(f"CodeBERT summarization failed: {str(e)}")
        return {}

# Dependency graph generation function
async def generate_dependency_graph(code_structure: Dict[str, Any]) -> str:
    """
    Generate a Mermaid.js dependency graph based on the code structure.
    Returns a string containing the Mermaid.js graph definition.
    """
    logger.info("Generating dependency graph")
    
    try:
        # Start building the Mermaid.js graph
        mermaid_graph = "graph TD\n"
        
        # Add nodes for files
        for i, file in enumerate(code_structure["files"]):
            file_id = f"F{i}"
            file_name = os.path.basename(file["path"])
            mermaid_graph += f"  {file_id}[{file_name}]\n"
        
        # Add edges based on imports (simplified)
        # In a real implementation, you would analyze actual import relationships
        
        # For now, we'll create some placeholder connections
        for i in range(len(code_structure["files"]) - 1):
            mermaid_graph += f"  F{i} --> F{i+1}\n"
        
        logger.info("Dependency graph generation complete")
        return mermaid_graph
    
    except Exception as e:
        logger.error(f"Dependency graph generation failed: {str(e)}")
        return "graph TD\n  A[Error] --> B[Failed to generate graph]"

# LLM API call function using provider abstraction with retry logic
async def call_llm(
    provider: LLMProvider, 
    prompt: str, 
    response_format: str = "text", 
    system_message: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 2.0
) -> Any:
    """
    Call the LLM API with the given prompt using the provided LLM provider.
    Automatically retries on timeout and temporary errors with exponential backoff.
    
    Args:
        provider: The LLM provider instance
        prompt: The prompt to send
        response_format: "text" or "json"
        system_message: Optional system message
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Initial retry delay in seconds (default: 2.0, doubles each retry)
    
    Returns:
        Response in the specified format (text or JSON)
    
    Raises:
        Exception if all retries fail or non-retriable error occurs
    
    This function uses the LLM provider abstraction layer to support multiple providers:
    - OpenAI (GPT-4, GPT-3.5)
    - Ollama (local open-source models)
    - HuggingFace (Inference API)
    - Together AI (hosted open-source models)
    - Groq (fast inference)
    - Gemini (Google AI Studio)
    """
    import asyncio
    
    provider_name = provider.__class__.__name__.replace("Provider", "").upper()
    logger.info(f"[{provider_name}] Prompt length: {len(prompt)} characters")
    logger.info(f"[{provider_name}] Response format: {response_format}")
    
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                # Exponential backoff: delay doubles each retry (2s, 4s, 8s)
                delay = retry_delay * (2 ** (attempt - 1))
                logger.info(f"[{provider_name}] Retry attempt {attempt + 1}/{max_retries} after {delay:.1f}s delay...")
                await asyncio.sleep(delay)
            
            response = await provider.generate(
                prompt=prompt,
                response_format=response_format,
                temperature=0.2,
                system_message=system_message
            )
            
            if attempt > 0:
                logger.info(f"[{provider_name}] ✅ Response received on retry attempt {attempt + 1}")
            else:
                logger.info(f"[{provider_name}] ✅ Response received")
            
            # Response is already parsed if JSON format was requested
            return response
            
        except Exception as e:
            error_message = str(e)
            last_exception = e
            
            # Check if it's a retriable error (timeout, temporary service issues, format errors)
            is_retriable = (
                "timed out" in error_message.lower() or
                "timeout" in error_message.lower() or
                "503" in error_message or
                "502" in error_message or
                "temporarily unavailable" in error_message.lower() or
                "unavailable" in error_message.lower() or
                "server error" in error_message.lower() or
                "try again later" in error_message.lower() or
                "ignored json format instruction" in error_message.lower() or
                "retriable error" in error_message.lower()
            )
            
            # Check for non-retriable errors (quota, invalid API key, etc.)
            is_quota_error = (
                "quota" in error_message.lower() or
                "429" in error_message or
                "insufficient_quota" in error_message.lower() or
                "rate limit" in error_message.lower()
            )
            
            is_auth_error = (
                "api key not valid" in error_message.lower() or
                "api_key_invalid" in error_message.lower() or
                "invalid" in error_message.lower() and "api key" in error_message.lower()
            )
            
            # Don't retry non-retriable errors
            if is_quota_error:
                logger.error(f"[{provider_name}] ❌ QUOTA EXCEEDED - not retrying")
                if response_format == "json":
                    return {}
                raise Exception(f"API quota exceeded for {provider_name}.")
            
            if is_auth_error:
                logger.error(f"[{provider_name}] ❌ AUTHENTICATION ERROR - not retrying")
                raise
            
            # If it's a retriable error and we have retries left, continue
            if is_retriable and attempt < max_retries - 1:
                logger.warning(f"[{provider_name}] ⚠️  Retriable error (attempt {attempt + 1}/{max_retries}): {error_message[:100]}")
                continue
            
            # If it's not retriable or we're out of retries, log and re-raise
            if not is_retriable:
                logger.error(f"[{provider_name}] ❌ Non-retriable error: {error_message}")
                raise
            
            # Last retry failed
            logger.error(f"[{provider_name}] ❌ All {max_retries} retry attempts failed. Last error: {error_message}")
            raise
    
    # Should never reach here, but just in case
    if last_exception:
        raise last_exception
    raise Exception(f"{provider_name} API call failed after {max_retries} attempts")


# Legacy function for backward compatibility (deprecated)
async def call_gpt4(api_key: str, prompt: str, response_format: str = "text") -> Any:
    """
    Legacy function for backward compatibility.
    This function creates an OpenAI provider and calls it.
    Consider using call_llm() with a provider instance instead.
    """
    logger.warning("[DEPRECATED] call_gpt4() is deprecated. Use call_llm() with a provider instance instead.")
    provider = create_llm_provider("openai", api_key=api_key, model=os.getenv("OPENAI_MODEL", "gpt-4o"))
    return await call_llm(provider, prompt, response_format)

# Cleanup function
async def cleanup_temp_directory(path: str) -> None:
    """Securely delete the cloned repository."""
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
            logger.info(f"Cleaned up temporary directory: {path}")
    except Exception as e:
        logger.error(f"Error cleaning up {path}: {str(e)}")

# Main worker function for arq
async def process_repository_analysis(ctx, job_data):
    """
    Main worker function to process a repository analysis job.
    This function is triggered by a job from the arq queue.
    
    Args:
        ctx: The worker context
        job_data: The job data containing repo_id and github_url
    """
    repo_id = job_data['repo_id']
    github_url = job_data['github_url']
    
    logger.info(f"Starting analysis for repository: {repo_id} ({github_url})")
    
    # Create temp directory if it doesn't exist
    os.makedirs("/tmp/reploai", exist_ok=True)
    local_repo_path = f"/tmp/reploai/{repo_id}"
    
    db = get_db()
    
    try:
        # 1. Update status in DB
        repo = db.query(Repository).filter(Repository.repo_id == repo_id).first()
        if not repo:
            logger.error(f"Repository with ID {repo_id} not found")
            return {"status": "error", "message": "Repository not found"}
        
        repo.status = 'ANALYZING'
        db.commit()
        
        repo_name = github_url.split('/')[-1].replace('.git', '')
        
        # 2. Ingestion: Clone repo to a temp directory
        logger.info(f"Cloning repository: {github_url}")
        git.Repo.clone_from(github_url, local_repo_path)
        
        # 3. Structure Analysis (tree-sitter)
        logger.info("Starting code structure analysis")
        code_structure_json = await run_tree_sitter_analysis(local_repo_path)
        
        # 4. Code Summarization (CodeBERT)
        logger.info("Starting code summarization")
        code_summaries = await run_codebert_summarization(local_repo_path, code_structure_json)
        
        # 5. Dependency Graph (Mermaid.js)
        logger.info("Generating dependency graph")
        main_diagram = await generate_dependency_graph(code_structure_json)
        
        # 6. Tutorial Generation (GPT-4) - Loop for each level
        levels = ['BEGINNER', 'INTERMEDIATE', 'ADVANCED']
        
        for level in levels:
            logger.info(f"Generating {level} tutorial")
            
            # 6a. === PROMPT 1: GENERATE OUTLINE ===
            outline_prompt = create_gpt_outline_prompt(level, code_structure_json, code_summaries)
            tutorial_outline_json = await call_gpt4(outline_prompt, response_format="json")
            
            # 6b. Save Tutorial to DB
            tutorial = Tutorial(
                repo_id=repo_id,
                level=level,
                title=f"{level} Guide for {repo_name}",
                overview=f"An AI-generated {level} overview of {repo_name}.",
                overview_diagram_mermaid=main_diagram
            )
            db.add(tutorial)
            db.commit()
            db.refresh(tutorial)
            
            # 7. Module & Quiz Generation (Looping through the outline)
            for index, module_outline in enumerate(tutorial_outline_json):
                logger.info(f"Generating module {index+1} for {level} tutorial")
                
                # 7a. === PROMPT 2: GENERATE MODULE CONTENT ===
                file_content = await read_file_content(local_repo_path, module_outline['file_path'])
                
                module_prompt = create_gpt_module_prompt(
                    level=level,
                    module_outline=module_outline,
                    file_content=file_content,
                    full_outline=tutorial_outline_json
                )
                
                module_data_json = await call_gpt4(module_prompt, response_format="json")
                
                # 7b. Save Module to DB
                module = Module(
                    tutorial_id=tutorial.tutorial_id,
                    order_index=index,
                    title=module_data_json['title'],
                    content_markdown=module_data_json['content_markdown'],
                    file_path=module_outline['file_path'],
                    code_snippet=module_data_json['code_snippet'],
                    diagram_mermaid=module_data_json.get('diagram_mermaid')
                )
                db.add(module)
                db.commit()
                db.refresh(module)
                
                # 7c. === PROMPT 3: GENERATE QUIZ ===
                quiz_prompt = create_gpt_quiz_prompt(
                    module_data_json['content_markdown'], 
                    module_data_json['code_snippet']
                )
                
                quiz_data_json = await call_gpt4(quiz_prompt, response_format="json")
                
                # 7d. Save Quiz to DB
                quiz = Quiz(
                    module_id=module.module_id,
                    question_text=quiz_data_json['question_text'],
                    question_type='MULTIPLE_CHOICE',
                    options=quiz_data_json['options'],
                    correct_answer=next((opt['text'] for opt in quiz_data_json['options'] if opt['is_correct']), None)
                )
                db.add(quiz)
                db.commit()
        
        # 8. Finalize: Update repo status
        repo.status = 'COMPLETED'
        db.commit()
        logger.info(f"Repository analysis completed for {repo_id}")
        
        return {
            "status": "success",
            "repo_id": str(repo_id),
            "message": "Repository analysis completed successfully"
        }
        
    except Exception as e:
        logger.error(f"Repository analysis failed: {str(e)}")
        # 9. Handle Failure
        repo = db.query(Repository).filter(Repository.repo_id == repo_id).first()
        if repo:
            repo.status = 'FAILED'
            db.commit()
        
        return {
            "status": "error",
            "repo_id": str(repo_id),
            "message": f"Repository analysis failed: {str(e)}"
        }
    
    finally:
        # 10. Cleanup
        await cleanup_temp_directory(local_repo_path)
        db.close()

# Helper function to update generation progress
def update_generation_progress(
    db,
    generation_id: str,
    status: str,
    step: int,
    progress: int,
    error_message: Optional[str] = None
):
    """Update the generation status and progress."""
    try:
        from sqlalchemy import UUID as UUIDType
        generation = db.query(TutorialGeneration).filter(
            TutorialGeneration.generation_id == uuid.UUID(generation_id)
        ).first()
        
        if generation:
            generation.status = status
            generation.generation_step = step
            generation.generation_progress = progress
            if error_message:
                generation.error_message = error_message
            db.commit()
    except Exception as e:
        logger.error(f"Error updating generation progress: {str(e)}")

# Tutorial generation worker function
async def generate_tutorial(ctx, job_data):
    """
    Worker function to generate a tutorial with custom parameters.
    This function is triggered by a job from the arq queue.
    
    Args:
        ctx: The worker context
        job_data: The job data containing generation_id, repo_id, github_url, difficulty, focus_areas, description
    """
    logger.info("=" * 80)
    logger.info("[WORKER] ========== TUTORIAL GENERATION WORKER STARTED ==========")
    logger.info(f"[WORKER] Received job_data: {job_data}")
    
    generation_id = job_data.get('generation_id')
    repo_id = job_data.get('repo_id')
    github_url = job_data.get('github_url')
    user_id = job_data.get('user_id')
    difficulty = job_data.get('difficulty', 'INTERMEDIATE')
    focus_areas = job_data.get('focus_areas')
    description = job_data.get('description')
    
    logger.info(f"[WORKER] Parsed parameters:")
    logger.info(f"[WORKER]   - generation_id: {generation_id}")
    logger.info(f"[WORKER]   - repo_id: {repo_id}")
    logger.info(f"[WORKER]   - github_url: {github_url}")
    logger.info(f"[WORKER]   - user_id: {user_id}")
    logger.info(f"[WORKER]   - difficulty: {difficulty}")
    logger.info(f"[WORKER]   - focus_areas: {focus_areas}")
    logger.info(f"[WORKER]   - description: {description}")
    
    if not generation_id:
        logger.error("[WORKER] ❌ ERROR: generation_id is missing from job_data!")
        return {"status": "error", "message": "generation_id is required"}
    
    if not repo_id:
        logger.error("[WORKER] ❌ ERROR: repo_id is missing from job_data!")
        return {"status": "error", "message": "repo_id is required"}
    
    if not user_id:
        logger.error("[WORKER] ❌ ERROR: user_id is missing from job_data!")
        return {"status": "error", "message": "user_id is required"}
    
    logger.info(f"[WORKER] ✅ All required parameters present")
    logger.info(f"[WORKER] Starting tutorial generation: {generation_id} for repo {repo_id} ({github_url})")
    
    # Create temp directory if it doesn't exist
    logger.info("[WORKER] Creating temporary directory...")
    os.makedirs("/tmp/reploai", exist_ok=True)
    local_repo_path = f"/tmp/reploai/{generation_id}"
    logger.info(f"[WORKER] ✅ Temp directory ready: {local_repo_path}")
    
    logger.info("[WORKER] Initializing database session...")
    db = SessionLocal()
    logger.info("[WORKER] ✅ Database session created")
    
    # Initialize llm_provider_type early for error handling
    llm_provider_type = "openai"
    llm_provider = None
    
    try:
        # Get user's LLM provider settings
        logger.info(f"[WORKER] Step 1: Retrieving LLM provider settings for user {user_id}...")
        
        # First, get or create UserSettings (like the API does)
        user_settings = db.query(UserSettings).filter(
            UserSettings.user_id == uuid.UUID(user_id)
        ).first()
        
        if not user_settings:
            logger.warning(f"[WORKER] ⚠️  UserSettings not found for user {user_id}, creating default settings...")
            # Get the User object to ensure it exists
            from app.models.user import User
            user = db.query(User).filter(User.user_id == uuid.UUID(user_id)).first()
            if not user:
                logger.error(f"[WORKER] ❌ ERROR: User {user_id} not found in database")
                update_generation_progress(db, generation_id, 'FAILED', 0, 0, "User not found")
                return {"status": "error", "message": "User not found"}
            
            # Create default UserSettings
            logger.info(f"[WORKER] Creating default UserSettings for user {user_id}...")
            user_settings = UserSettings(
                user_id=user.user_id,
                email_notifications_enabled=True,
                tutorial_completions=True,
                new_features=True,
                weekly_digest=True,
                browser_notifications=True,
                language="en",
                code_editor_theme="github-dark",
                default_difficulty_level="beginner",
                daily_learning_goal=10,
                auto_play_next_module=True,
                show_code_hints=True,
                quiz_mode=True,
                llm_provider="openai",  # Default to OpenAI
            )
            db.add(user_settings)
            db.commit()
            db.refresh(user_settings)
            logger.info(f"[WORKER] ✅ Default UserSettings created")
        
        # Validate primary LLM provider is configured
        llm_provider_type = user_settings.llm_provider or "openai"
        
        # Get primary API key
        llm_api_key = user_settings.llm_api_key
        # Backward compatibility: use openai_api_key if llm_api_key is not set and provider is openai
        if not llm_api_key and llm_provider_type == "openai" and user_settings.openai_api_key:
            llm_api_key = user_settings.openai_api_key
        
        # Check if provider is configured (Ollama doesn't need API key)
        if llm_provider_type != "ollama" and not llm_api_key:
            logger.error(f"[WORKER] ❌ ERROR: No LLM API key configured for provider '{llm_provider_type}' for user {user_id}")
            update_generation_progress(db, generation_id, 'FAILED', 0, 0, f"No API key configured for {llm_provider_type}. Please add your API key in settings.")
            return {"status": "error", "message": f"No API key configured for {llm_provider_type}. Please add your API key in settings."}
        
        logger.info(f"[WORKER] ✅ LLM provider configured: {llm_provider_type}")
        
        # Create LLM provider instance
        try:
            llm_provider = create_llm_provider(
                provider_type=llm_provider_type,
                api_key=llm_api_key,
                model=user_settings.llm_model,
                base_url=user_settings.llm_base_url
            )
            logger.info(f"[WORKER] ✅ LLM provider instance created successfully")
        except Exception as e:
            logger.error(f"[WORKER] ❌ ERROR creating LLM provider: {str(e)}")
            update_generation_progress(db, generation_id, 'FAILED', 0, 0, f"Failed to initialize LLM provider: {str(e)}")
            return {"status": "error", "message": f"Failed to initialize LLM provider: {str(e)}"}
        
        # Get generation record
        logger.info(f"[WORKER] Step 2: Retrieving generation record {generation_id}...")
        generation = db.query(TutorialGeneration).filter(
            TutorialGeneration.generation_id == uuid.UUID(generation_id)
        ).first()
        
        if not generation:
            logger.error(f"[WORKER] ❌ ERROR: Generation record {generation_id} not found in database")
            return {"status": "error", "message": "Generation record not found"}
        
        logger.info(f"[WORKER] ✅ Generation record found - Status: {generation.status}, Progress: {generation.generation_progress}%")
        
        # Get repository
        logger.info(f"[WORKER] Step 3: Retrieving repository {repo_id}...")
        repo = db.query(Repository).filter(Repository.repo_id == uuid.UUID(repo_id)).first()
        if not repo:
            logger.error(f"[WORKER] ❌ ERROR: Repository {repo_id} not found in database")
            update_generation_progress(db, generation_id, 'FAILED', 0, 0, "Repository not found")
            return {"status": "error", "message": "Repository not found"}
        
        repo_name = github_url.split('/')[-1].replace('.git', '')
        logger.info(f"[WORKER] ✅ Repository found - Name: {repo_name}, Status: {repo.status}")
        
        # Update status to CLONING before starting
        logger.info("[WORKER] Step 4: Updating generation status to CLONING...")
        update_generation_progress(db, generation_id, 'CLONING', 1, 10)
        logger.info("[WORKER] ✅ Status updated to CLONING (10%)")
        
        # Step 1: Cloning (Step 1, Progress 10%)
        logger.info(f"[WORKER] ========== STEP 1: CLONING REPOSITORY ==========")
        logger.info(f"[WORKER] Cloning {github_url} to {local_repo_path}...")
        import time
        clone_start = time.time()
        
        try:
            git.Repo.clone_from(github_url, local_repo_path)
            clone_duration = time.time() - clone_start
            logger.info(f"[WORKER] ✅ Repository cloned successfully in {clone_duration:.2f} seconds")
        except Exception as e:
            clone_duration = time.time() - clone_start
            logger.error(f"[WORKER] ❌ ERROR cloning repository after {clone_duration:.2f} seconds: {str(e)}")
            raise
        
        # Step 2: Structure Analysis (Step 2, Progress 30%)
        logger.info("[WORKER] ========== STEP 2: ANALYZING CODE STRUCTURE ==========")
        logger.info("[WORKER] Updating status to ANALYZING (30%)...")
        update_generation_progress(db, generation_id, 'ANALYZING', 2, 30)
        
        analysis_start = time.time()
        logger.info("[WORKER] Starting tree-sitter analysis...")
        code_structure_json = await run_tree_sitter_analysis(local_repo_path)
        analysis_duration = time.time() - analysis_start
        logger.info(f"[WORKER] ✅ Code structure analysis completed in {analysis_duration:.2f} seconds")
        logger.info(f"[WORKER] Found {len(code_structure_json.get('files', []))} files in analysis")
        
        # Step 3: Code Summarization (Step 3, Progress 50%)
        logger.info("[WORKER] ========== STEP 3: GENERATING CODE SUMMARIES ==========")
        logger.info("[WORKER] Updating status to PROCESSING (50%)...")
        update_generation_progress(db, generation_id, 'PROCESSING', 3, 50)
        
        summary_start = time.time()
        logger.info("[WORKER] Starting CodeBERT summarization...")
        code_summaries = await run_codebert_summarization(local_repo_path, code_structure_json)
        summary_duration = time.time() - summary_start
        logger.info(f"[WORKER] ✅ Code summarization completed in {summary_duration:.2f} seconds")
        logger.info(f"[WORKER] Generated summaries for {len(code_summaries)} functions")
        
        # Step 4: Dependency Graph (Step 3, Progress 60%)
        logger.info("[WORKER] ========== STEP 4: GENERATING DEPENDENCY GRAPH ==========")
        logger.info("[WORKER] Generating Mermaid dependency graph...")
        diagram_start = time.time()
        main_diagram = await generate_dependency_graph(code_structure_json)
        diagram_duration = time.time() - diagram_start
        logger.info(f"[WORKER] ✅ Dependency graph generated in {diagram_duration:.2f} seconds")
        
        # Step 5: Extract repository contents (Step 4, Progress 65%)
        logger.info("[WORKER] ========== STEP 5: EXTRACTING REPOSITORY CONTENTS ==========")
        logger.info("[WORKER] Updating status to GENERATING (65%)...")
        update_generation_progress(db, generation_id, 'GENERATING', 4, 65)
        
        extract_start = time.time()
        logger.info("[WORKER] Extracting code files from repository...")
        repo_contents = await extract_repository_contents(local_repo_path)
        extract_duration = time.time() - extract_start
        logger.info(f"[WORKER] ✅ Repository contents extracted in {extract_duration:.2f} seconds")
        logger.info(f"[WORKER] Extracted {len(repo_contents)} code files")
        
        # Step 6: Tutorial Generation (Step 4, Progress 70-100%)
        logger.info("[WORKER] ========== STEP 6: GENERATING TUTORIAL WITH AI ==========")
        logger.info(f"[WORKER] Generating {difficulty} tutorial...")
        logger.info("[WORKER] Updating status to GENERATING (70%)...")
        update_generation_progress(db, generation_id, 'GENERATING', 4, 70)
        
        # Build enhanced prompt with repository contents
        logger.info("[WORKER] Building GPT-4 outline prompt...")
        prompt_start = time.time()
        outline_prompt = create_gpt_outline_prompt(difficulty, code_structure_json, code_summaries)
        logger.info(f"[WORKER] Base prompt created (length: {len(outline_prompt)} chars)")
        
        # Add repository contents to prompt (reduced to 10 files, 500 chars each for speed)
        logger.info("[WORKER] Adding repository code files to prompt...")
        repo_contents_str = ""
        file_count = 0
        for file_path, content in list(repo_contents.items())[:10]:  # Reduced from 20 to 10
            # Truncate to 500 chars (reduced from 2000)
            content_preview = content[:500] + "..." if len(content) > 500 else content
            repo_contents_str += f"\n{file_path}: {content_preview[:100]}..."  # Just file path + preview
            file_count += 1
            logger.info(f"[WORKER]   - Added file {file_count}: {file_path}")
        
        if repo_contents_str:
            outline_prompt += f"\n\nFiles: {repo_contents_str}"
            logger.info(f"[WORKER] Added {file_count} files to prompt (total prompt length: {len(outline_prompt)} chars)")
        
        # Add focus areas and description to the prompt if provided
        if focus_areas or description:
            additional_context = []
            if focus_areas:
                additional_context.append(f"Focus Areas: {', '.join(focus_areas)}")
            if description:
                additional_context.append(f"Additional Context: {description}")
            
            if additional_context:
                outline_prompt += f"\n\n=== Additional Requirements ===\n{chr(10).join(additional_context)}"
                logger.info(f"[WORKER] Added additional context to prompt")
        
        logger.info(f"[WORKER] Final prompt length: {len(outline_prompt)} characters")
        logger.info(f"[WORKER] Calling LLM API ({llm_provider_type}) to generate tutorial outline...")
        
        gpt_start = time.time()
        try:
            tutorial_outline_json = await call_llm(
                llm_provider,
                outline_prompt,
                response_format="json",
                system_message="You MUST respond with ONLY valid JSON. No markdown, no explanations. Just raw JSON. You are an expert software engineering educator."
            )
        except Exception as e:
            logger.error(f"[WORKER] ❌ ERROR calling LLM ({llm_provider_type}): {str(e)}")
            update_generation_progress(db, generation_id, 'FAILED', 4, 60, f"LLM API call failed: {str(e)}")
            raise
        
        gpt_duration = time.time() - gpt_start
        logger.info(f"[WORKER] ✅ LLM API call completed in {gpt_duration:.2f} seconds using provider: {llm_provider_type}")
        
        if not tutorial_outline_json or len(tutorial_outline_json) == 0:
            logger.error(f"[WORKER] ❌ ERROR: LLM ({llm_provider_type}) returned empty or invalid outline")
            # Check if it's a quota error message
            error_msg = "Failed to generate tutorial outline"
            if isinstance(tutorial_outline_json, str):
                if "quota" in tutorial_outline_json.lower() or "insufficient_quota" in tutorial_outline_json.lower():
                    error_msg = f"API quota exceeded for {llm_provider_type}. Please check your provider settings."
                elif "error" in tutorial_outline_json.lower():
                    error_msg = f"Failed to generate tutorial outline: {tutorial_outline_json}"
            raise Exception(error_msg)
        
        logger.info(f"[WORKER] ✅ Tutorial outline generated with {len(tutorial_outline_json)} modules")
        for idx, module in enumerate(tutorial_outline_json, 1):
            logger.info(f"[WORKER]   Module {idx}: {module.get('title', 'Untitled')} - {module.get('file_path', 'N/A')}")
        
        # Save Tutorial to DB
        logger.info("[WORKER] Saving tutorial to database...")
        tutorial = Tutorial(
            repo_id=uuid.UUID(repo_id),
            level=difficulty,
            title=f"{difficulty} Guide for {repo_name}",
            overview=f"An AI-generated {difficulty.lower()} overview of {repo_name}.",
            overview_diagram_mermaid=main_diagram
        )
        db.add(tutorial)
        db.commit()
        db.refresh(tutorial)
        logger.info(f"[WORKER] ✅ Tutorial saved to DB - Tutorial ID: {tutorial.tutorial_id}")
        
        # Update generation with tutorial_id
        logger.info("[WORKER] Linking tutorial to generation record...")
        generation.tutorial_id = tutorial.tutorial_id
        db.commit()
        logger.info("[WORKER] ✅ Generation record updated with tutorial_id")
        
        # Generate modules and quizzes
        total_modules = len(tutorial_outline_json)
        logger.info(f"[WORKER] ========== STEP 7: GENERATING {total_modules} MODULES ==========")
        for index, module_outline in enumerate(tutorial_outline_json):
            module_num = index + 1
            logger.info(f"[WORKER] --- Generating Module {module_num}/{total_modules} ---")
            logger.info(f"[WORKER]   Title: {module_outline.get('title', 'N/A')}")
            logger.info(f"[WORKER]   File: {module_outline.get('file_path', 'N/A')}")
            
            # Update progress: 70% + (index/total_modules) * 25%
            progress = 70 + int((index / total_modules) * 25)
            logger.info(f"[WORKER]   Updating progress to {progress}%...")
            update_generation_progress(db, generation_id, 'GENERATING', 4, progress)
            
            # Read file content
            logger.info(f"[WORKER]   Reading file content from {module_outline.get('file_path', 'N/A')}...")
            file_content = await read_file_content(local_repo_path, module_outline.get('file_path', ''))
            logger.info(f"[WORKER]   File content read ({len(file_content)} chars)")
            
            # Generate module content
            logger.info(f"[WORKER]   Creating module prompt for GPT-4...")
            module_prompt = create_gpt_module_prompt(
                level=difficulty,
                module_outline=module_outline,
                file_content=file_content
                # Removed full_outline to reduce prompt size
            )
            logger.info(f"[WORKER]   Module prompt created ({len(module_prompt)} chars)")
            
            logger.info(f"[WORKER]   Calling LLM API ({llm_provider_type}) to generate module content...")
            module_gpt_start = time.time()
            try:
                module_data_json = await call_llm(
                    llm_provider,
                    module_prompt,
                    response_format="json",
                    system_message="You MUST respond with ONLY valid JSON. No markdown, no explanations. Just raw JSON. You are an expert software engineering educator."
                )
            except Exception as e:
                logger.error(f"[WORKER]   ❌ ERROR calling LLM ({llm_provider_type}) for module: {str(e)}")
                raise
            module_gpt_duration = time.time() - module_gpt_start
            logger.info(f"[WORKER]   ✅ Module content generated in {module_gpt_duration:.2f} seconds using provider: {llm_provider_type}")
            
            # Save Module to DB
            logger.info(f"[WORKER]   Saving module {module_num} to database...")
            module = Module(
                tutorial_id=tutorial.tutorial_id,
                order_index=index,
                title=module_data_json.get('title', module_outline.get('title', f"Module {module_num}")),
                content_markdown=module_data_json.get('content_markdown', ''),
                file_path=module_outline.get('file_path'),
                code_snippet=module_data_json.get('code_snippet'),
                diagram_mermaid=module_data_json.get('diagram_mermaid')
            )
            db.add(module)
            db.commit()
            db.refresh(module)
            logger.info(f"[WORKER]   ✅ Module saved - Module ID: {module.module_id}")
            
            # Generate quiz
            logger.info(f"[WORKER]   Generating quiz for module {module_num}...")
            quiz_prompt = create_gpt_quiz_prompt(
                module_data_json.get('content_markdown', ''),
                module_data_json.get('code_snippet', '')
            )
            
            quiz_gpt_start = time.time()
            try:
                quiz_data_json = await call_llm(
                    llm_provider,
                    quiz_prompt,
                    response_format="json",
                    system_message="You MUST respond with ONLY valid JSON. No markdown, no explanations. Just raw JSON. You are an expert quiz creator."
                )
            except Exception as e:
                logger.error(f"[WORKER]   ❌ ERROR calling LLM ({llm_provider_type}) for quiz: {str(e)}")
                raise
            quiz_gpt_duration = time.time() - quiz_gpt_start
            logger.info(f"[WORKER]   ✅ Quiz generated in {quiz_gpt_duration:.2f} seconds using provider: {llm_provider_type}")
            
            # Save Quiz to DB
            if quiz_data_json and 'question_text' in quiz_data_json:
                logger.info(f"[WORKER]   Saving quiz to database...")
                quiz = Quiz(
                    module_id=module.module_id,
                    question_text=quiz_data_json['question_text'],
                    question_type='MULTIPLE_CHOICE',
                    options=quiz_data_json.get('options', []),
                    correct_answer=next((opt['text'] for opt in quiz_data_json.get('options', []) if opt.get('is_correct')), None)
                )
                db.add(quiz)
                db.commit()
                logger.info(f"[WORKER]   ✅ Quiz saved - Quiz ID: {quiz.quiz_id}")
            else:
                logger.warning(f"[WORKER]   ⚠️  No quiz data generated for module {module_num}")
        
        # Update repository status
        logger.info("[WORKER] ========== STEP 8: FINALIZING ==========")
        logger.info("[WORKER] Updating repository status to COMPLETED...")
        repo.status = 'COMPLETED'
        db.commit()
        logger.info("[WORKER] ✅ Repository status updated")
        
        # Mark generation as completed
        from datetime import datetime
        logger.info("[WORKER] Marking generation as COMPLETED (100%)...")
        generation.status = 'COMPLETED'
        generation.generation_step = 4
        generation.generation_progress = 100
        generation.completed_at = datetime.now()
        db.commit()
        logger.info("[WORKER] ✅ Generation status updated to COMPLETED")
        
        total_duration = time.time() - clone_start
        logger.info("=" * 80)
        logger.info(f"[WORKER] ========== ✅ TUTORIAL GENERATION COMPLETED SUCCESSFULLY ==========")
        logger.info(f"[WORKER] Generation ID: {generation_id}")
        logger.info(f"[WORKER] Tutorial ID: {tutorial.tutorial_id}")
        logger.info(f"[WORKER] Total Duration: {total_duration:.2f} seconds ({total_duration/60:.2f} minutes)")
        logger.info(f"[WORKER] Modules Generated: {total_modules}")
        logger.info("=" * 80)
        
        # Note: ARQ automatically handles job completion and cleanup.
        # When this function returns successfully, ARQ:
        # 1. Marks the job as complete in Redis
        # 2. Moves it from "in_progress" to "complete" queue
        # 3. Cleans up after the retention period (default: 1 hour)
        # No manual Redis cleanup is required.
        
        return {
            "status": "success",
            "generation_id": str(generation_id),
            "tutorial_id": str(tutorial.tutorial_id),
            "message": "Tutorial generation completed successfully"
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error("=" * 80)
        logger.error(f"[WORKER] ========== ❌ TUTORIAL GENERATION FAILED ==========")
        logger.error(f"[WORKER] Generation ID: {generation_id}")
        logger.error(f"[WORKER] Error Type: {type(e).__name__}")
        logger.error(f"[WORKER] Error Message: {str(e)}")
        logger.error(f"[WORKER] Full Traceback:")
        logger.error(error_trace)
        logger.error("=" * 80)
        
        # Update generation status to FAILED with detailed error message
        try:
            error_msg = str(e)
            # Use llm_provider_type if available, otherwise default
            provider_name = "unknown"
            try:
                provider_name = llm_provider_type
            except:
                pass
            # Check if it's a quota error
            if "quota" in error_msg.lower() or "insufficient_quota" in error_msg.lower():
                detailed_error = f"API quota exceeded for {provider_name}. Please check your provider settings."
            elif "temporarily unavailable" in error_msg.lower() or "503" in error_msg or "unavailable" in error_msg.lower():
                detailed_error = f"{provider_name} is temporarily unavailable. This is usually temporary - please try again in a few moments or use a different provider."
            elif "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
                if "all" in error_msg.lower() and "retry" in error_msg.lower():
                    # Retries were exhausted
                    if provider_name.lower() == "ollama":
                        detailed_error = f"Ollama request timed out after multiple retry attempts. Ollama may be slow or overloaded. Try using a smaller/faster model, ensure Ollama is running properly, or use a different provider."
                    else:
                        detailed_error = f"{provider_name} request timed out after multiple retry attempts. Please try again later or use a different provider."
                else:
                    # Single timeout (shouldn't happen with retries, but just in case)
                    if provider_name.lower() == "ollama":
                        detailed_error = f"Ollama request timed out. Retrying automatically... (if you see this, retry logic may not be working)"
                    else:
                        detailed_error = f"{provider_name} request timed out. Retrying automatically..."
            elif "cannot connect" in error_msg.lower() or "connection" in error_msg.lower():
                if provider_name.lower() == "ollama":
                    detailed_error = f"Cannot connect to Ollama. Make sure Ollama is running (start it with 'ollama serve') and check your base URL setting."
                else:
                    detailed_error = f"Cannot connect to {provider_name}. Check your connection and provider settings."
            elif "model_not_found" in error_msg.lower() or "404" in error_msg.lower():
                detailed_error = f"Model not available: {error_msg}. Please check your {provider_name} provider access."
            else:
                detailed_error = f"Generation failed: {error_msg}"
            
            update_generation_progress(
                db,
                generation_id,
                'FAILED',
                0,
                0,
                detailed_error
            )
            logger.info(f"[WORKER] ✅ Generation status updated to FAILED: {detailed_error}")
        except Exception as update_error:
            logger.error(f"[WORKER] ❌ Failed to update generation status: {str(update_error)}")
        
        # Update repo status if it exists
        try:
            if 'repo_id' in locals():
                repo = db.query(Repository).filter(Repository.repo_id == uuid.UUID(repo_id)).first()
                if repo:
                    repo.status = 'FAILED'
                    db.commit()
                    logger.info("[WORKER] ✅ Repository status updated to FAILED")
        except Exception as repo_error:
            logger.error(f"[WORKER] ❌ Failed to update repository status: {str(repo_error)}")
        
        return {
            "status": "error",
            "generation_id": str(generation_id) if generation_id else None,
            "message": f"Tutorial generation failed: {str(e)}"
        }
    
    finally:
        # Cleanup
        logger.info("[WORKER] ========== CLEANUP ==========")
        logger.info(f"[WORKER] Cleaning up temporary directory: {local_repo_path}")
        try:
            await cleanup_temp_directory(local_repo_path)
            logger.info("[WORKER] ✅ Temporary directory cleaned up")
        except Exception as cleanup_error:
            logger.error(f"[WORKER] ❌ Cleanup error: {str(cleanup_error)}")
        
        try:
            db.close()
            logger.info("[WORKER] ✅ Database session closed")
        except Exception as db_error:
            logger.error(f"[WORKER] ❌ Error closing database: {str(db_error)}")
        
        logger.info("[WORKER] ========== WORKER EXECUTION COMPLETE ==========")

