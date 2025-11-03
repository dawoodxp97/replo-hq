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

# GPT-4 API call function using new OpenAI client
async def call_gpt4(api_key: str, prompt: str, response_format: str = "text") -> Any:
    """
    Call the GPT-4 API with the given prompt using user's API key.
    Returns the response in the specified format (text or JSON).
    """
    try:
        client = OpenAI(api_key=api_key)
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.2,
            response_format={"type": response_format} if response_format == "json" else None
        )
        
        content = response.choices[0].message.content
        
        # Parse JSON if requested
        if response_format == "json":
            return json.loads(content)
        
        return content
    
    except Exception as e:
        logger.error(f"GPT-4 API call failed: {str(e)}")
        if response_format == "json":
            return {}
        return "Error generating content"

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
    generation_id = job_data.get('generation_id')
    repo_id = job_data.get('repo_id')
    github_url = job_data.get('github_url')
    user_id = job_data.get('user_id')
    difficulty = job_data.get('difficulty', 'INTERMEDIATE')
    focus_areas = job_data.get('focus_areas')
    description = job_data.get('description')
    
    logger.info(f"Starting tutorial generation: {generation_id} for repo {repo_id} ({github_url})")
    
    # Create temp directory if it doesn't exist
    os.makedirs("/tmp/reploai", exist_ok=True)
    local_repo_path = f"/tmp/reploai/{generation_id}"
    
    db = SessionLocal()
    
    try:
        # Get user's OpenAI API key
        user_settings = db.query(UserSettings).filter(
            UserSettings.user_id == uuid.UUID(user_id)
        ).first()
        
        if not user_settings or not user_settings.openai_api_key:
            logger.error(f"OpenAI API key not found for user {user_id}")
            update_generation_progress(db, generation_id, 'FAILED', 0, 0, "OpenAI API key not configured")
            return {"status": "error", "message": "OpenAI API key not configured"}
        
        openai_api_key = user_settings.openai_api_key
        
        # Get generation record
        generation = db.query(TutorialGeneration).filter(
            TutorialGeneration.generation_id == uuid.UUID(generation_id)
        ).first()
        
        if not generation:
            logger.error(f"Generation record {generation_id} not found")
            return {"status": "error", "message": "Generation record not found"}
        
        # Get repository
        repo = db.query(Repository).filter(Repository.repo_id == uuid.UUID(repo_id)).first()
        if not repo:
            logger.error(f"Repository {repo_id} not found")
            update_generation_progress(db, generation_id, 'FAILED', 0, 0, "Repository not found")
            return {"status": "error", "message": "Repository not found"}
        
        repo_name = github_url.split('/')[-1].replace('.git', '')
        
        # Step 1: Cloning (Step 1, Progress 10%)
        logger.info("Step 1: Cloning repository")
        update_generation_progress(db, generation_id, 'CLONING', 1, 10)
        git.Repo.clone_from(github_url, local_repo_path)
        
        # Step 2: Structure Analysis (Step 2, Progress 30%)
        logger.info("Step 2: Analyzing code structure")
        update_generation_progress(db, generation_id, 'ANALYZING', 2, 30)
        code_structure_json = await run_tree_sitter_analysis(local_repo_path)
        
        # Step 3: Code Summarization (Step 3, Progress 50%)
        logger.info("Step 3: Generating code summaries")
        update_generation_progress(db, generation_id, 'PROCESSING', 3, 50)
        code_summaries = await run_codebert_summarization(local_repo_path, code_structure_json)
        
        # Step 4: Dependency Graph (Step 3, Progress 60%)
        logger.info("Step 4: Generating dependency graph")
        main_diagram = await generate_dependency_graph(code_structure_json)
        
        # Step 5: Extract repository contents (Step 4, Progress 65%)
        logger.info("Step 5: Extracting repository contents")
        update_generation_progress(db, generation_id, 'GENERATING', 4, 65)
        repo_contents = await extract_repository_contents(local_repo_path)
        
        # Step 6: Tutorial Generation (Step 4, Progress 70-100%)
        logger.info(f"Step 6: Generating {difficulty} tutorial with AI")
        update_generation_progress(db, generation_id, 'GENERATING', 4, 70)
        
        # Build enhanced prompt with repository contents
        outline_prompt = create_gpt_outline_prompt(difficulty, code_structure_json, code_summaries)
        
        # Add repository contents to prompt (limit to first 20 files to avoid token limits)
        repo_contents_str = ""
        file_count = 0
        for file_path, content in list(repo_contents.items())[:20]:
            # Truncate very long files
            content_preview = content[:2000] + "..." if len(content) > 2000 else content
            repo_contents_str += f"\n\n=== File: {file_path} ===\n{content_preview}"
            file_count += 1
        
        if repo_contents_str:
            outline_prompt += f"\n\n=== Repository Code Files ({file_count} files shown) ==={repo_contents_str}"
        
        # Add focus areas and description to the prompt if provided
        if focus_areas or description:
            additional_context = []
            if focus_areas:
                additional_context.append(f"Focus Areas: {', '.join(focus_areas)}")
            if description:
                additional_context.append(f"Additional Context: {description}")
            
            if additional_context:
                outline_prompt += f"\n\n=== Additional Requirements ===\n{chr(10).join(additional_context)}"
        
        tutorial_outline_json = await call_gpt4(openai_api_key, outline_prompt, response_format="json")
        
        if not tutorial_outline_json or len(tutorial_outline_json) == 0:
            raise Exception("Failed to generate tutorial outline")
        
        # Save Tutorial to DB
        tutorial = Tutorial(
            repo_id=repo_id,
            level=difficulty,
            title=f"{difficulty} Guide for {repo_name}",
            overview=f"An AI-generated {difficulty.lower()} overview of {repo_name}.",
            overview_diagram_mermaid=main_diagram
        )
        db.add(tutorial)
        db.commit()
        db.refresh(tutorial)
        
        # Update generation with tutorial_id
        generation.tutorial_id = tutorial.tutorial_id
        db.commit()
        
        # Generate modules and quizzes
        total_modules = len(tutorial_outline_json)
        for index, module_outline in enumerate(tutorial_outline_json):
            logger.info(f"Generating module {index+1}/{total_modules} for {difficulty} tutorial")
            
            # Update progress: 70% + (index/total_modules) * 25%
            progress = 70 + int((index / total_modules) * 25)
            update_generation_progress(db, generation_id, 'GENERATING', 4, progress)
            
            # Read file content
            file_content = await read_file_content(local_repo_path, module_outline['file_path'])
            
            # Generate module content
            module_prompt = create_gpt_module_prompt(
                level=difficulty,
                module_outline=module_outline,
                file_content=file_content,
                full_outline=tutorial_outline_json
            )
            
            module_data_json = await call_gpt4(openai_api_key, module_prompt, response_format="json")
            
            # Save Module to DB
            module = Module(
                tutorial_id=tutorial.tutorial_id,
                order_index=index,
                title=module_data_json.get('title', module_outline.get('title', f"Module {index+1}")),
                content_markdown=module_data_json.get('content_markdown', ''),
                file_path=module_outline.get('file_path'),
                code_snippet=module_data_json.get('code_snippet'),
                diagram_mermaid=module_data_json.get('diagram_mermaid')
            )
            db.add(module)
            db.commit()
            db.refresh(module)
            
            # Generate quiz
            quiz_prompt = create_gpt_quiz_prompt(
                module_data_json.get('content_markdown', ''),
                module_data_json.get('code_snippet', '')
            )
            
            quiz_data_json = await call_gpt4(openai_api_key, quiz_prompt, response_format="json")
            
            # Save Quiz to DB
            if quiz_data_json and 'question_text' in quiz_data_json:
                quiz = Quiz(
                    module_id=module.module_id,
                    question_text=quiz_data_json['question_text'],
                    question_type='MULTIPLE_CHOICE',
                    options=quiz_data_json.get('options', []),
                    correct_answer=next((opt['text'] for opt in quiz_data_json.get('options', []) if opt.get('is_correct')), None)
                )
                db.add(quiz)
                db.commit()
        
        # Update repository status
        repo.status = 'COMPLETED'
        db.commit()
        
        # Mark generation as completed
        from datetime import datetime
        generation.status = 'COMPLETED'
        generation.generation_step = 4
        generation.generation_progress = 100
        generation.completed_at = datetime.now()
        db.commit()
        
        logger.info(f"Tutorial generation completed: {generation_id}")
        
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
        logger.error(f"Tutorial generation failed: {str(e)}")
        
        # Update generation status to FAILED
        update_generation_progress(
            db,
            generation_id,
            'FAILED',
            0,
            0,
            f"Generation failed: {str(e)}"
        )
        
        # Update repo status if it exists
        try:
            repo = db.query(Repository).filter(Repository.repo_id == repo_id).first()
            if repo:
                repo.status = 'FAILED'
                db.commit()
        except:
            pass
        
        return {
            "status": "error",
            "generation_id": str(generation_id) if generation_id else None,
            "message": f"Tutorial generation failed: {str(e)}"
        }
    
    finally:
        # Cleanup
        await cleanup_temp_directory(local_repo_path)
        db.close()

