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
import openai

from ..db.session import SessionLocal
from ..models.repositories import Repository
from ..models.tutorials import Tutorial
from ..models.modules import Module
from ..models.quizzes import Quiz
from ..core.generation_service import create_gpt_outline_prompt, create_gpt_module_prompt, create_gpt_quiz_prompt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

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

# GPT-4 API call function
async def call_gpt4(prompt: str, response_format: str = "text") -> Any:
    """
    Call the GPT-4 API with the given prompt.
    Returns the response in the specified format (text or JSON).
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
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

