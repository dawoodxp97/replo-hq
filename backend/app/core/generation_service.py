import json
from typing import Any, Dict, List

def create_gpt_outline_prompt(level: str, code_structure_json: Dict[str, Any], code_summaries: Dict[str, str]) -> str:
    files = code_structure_json.get('files', [])[:30]
    file_paths = [f.get('path', '') for f in files if f.get('path')]
    
    top_summaries = dict(list(code_summaries.items())[:10])
    
    system_prompt = f"""You MUST respond with ONLY valid JSON. No markdown, no explanations, no code blocks. Just raw JSON.

Create a {level} tutorial outline. Return JSON array: [{{"title": str, "key_concepts": str, "file_path": str}}, ...]"""
    
    user_prompt = f"""Level: {level}
Files: {', '.join(file_paths[:15])}
Key Functions: {', '.join(list(top_summaries.keys())[:5])}

Generate 5-8 modules. Respond with ONLY the JSON array, nothing else."""
    
    return f"{system_prompt}\n{user_prompt}"


def create_gpt_module_prompt(level: str, module_outline: Dict[str, str], file_content: str, full_outline: List[Dict[str, str]] = None) -> str:
    if len(file_content) > 3000:
        start = len(file_content) // 2 - 1500
        file_content = file_content[max(0, start):start+3000] + "\n[... truncated ...]"
    
    title = module_outline.get('title', 'Module')
    concepts = module_outline.get('key_concepts', '')
    file_path = module_outline.get('file_path', '')
    
    system_prompt = f"""You MUST respond with ONLY valid JSON. No markdown, no explanations, no code blocks. Just raw JSON.

Write a {level} tutorial module. Return JSON: {{"title": str, "content_markdown": str, "code_snippet": str (runnable in Sandpack), "diagram_mermaid": str or null}}"""
    
    user_prompt = f"""Module: {title}
Concepts: {concepts}
File: {file_path}

Code:
{file_content[:3000]}

Respond with ONLY the JSON object, nothing else."""
    
    return f"{system_prompt}\n{user_prompt}"


def create_gpt_quiz_prompt(content_markdown: str, code_snippet: str) -> str:
    """
    Create a concise prompt for LLM to generate quiz question.
    """
    # Limit content to essential parts only
    content_preview = content_markdown[:1000] if len(content_markdown) > 1000 else content_markdown
    code_preview = code_snippet[:500] if len(code_snippet) > 500 else code_snippet
    
    system_prompt = """You MUST respond with ONLY valid JSON. No markdown, no explanations, no code blocks. Just raw JSON.

Create 1 multiple-choice question. Return JSON: {"question_text": str, "options": [{"text": str, "is_correct": bool}]}"""
    
    user_prompt = f"""Content: {content_preview}
Code: {code_preview}

Respond with ONLY the JSON object, nothing else."""
    
    return f"{system_prompt}\n{user_prompt}"