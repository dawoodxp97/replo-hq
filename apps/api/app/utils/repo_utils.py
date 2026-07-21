import os
import git
import uuid
from typing import List, Optional, Any

def get_repo_path(repo_id: uuid.UUID) -> str:
    """Get the local path where the repository is cloned."""
    return f"/tmp/reploai/{repo_id}"

class FileTreeNode:
    def __init__(self, name: str, path: str, type: str, children: Optional[List['FileTreeNode']] = None):
        self.name = name
        self.path = path
        self.type = type
        self.children = children

    def to_dict(self):
        return {
            "name": self.name,
            "path": self.path,
            "type": self.type,
            "children": [child.to_dict() for child in self.children] if self.children else None
        }

def build_file_tree(repo_path: str, current_path: str = "", max_depth: int = 10, current_depth: int = 0) -> List[dict]:
    if current_depth >= max_depth:
        return []
    
    if not os.path.exists(repo_path):
        return []
    
    tree = []
    ignored_dirs = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build', '.next', '.cache'}
    code_extensions = {'.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php', 
                      '.json', '.md', '.yml', '.yaml', '.html', '.css', '.scss', '.less', '.sh', '.bash', '.zsh',
                      '.sql', '.xml', '.txt', '.ini', '.conf', '.config', '.env', '.gitignore', '.dockerfile'}
    
    try:
        items = sorted(os.listdir(repo_path))
        for item in items:
            if item.startswith('.'):
                continue
            
            item_path = os.path.join(repo_path, item)
            rel_path = os.path.join(current_path, item) if current_path else item
            
            if os.path.isdir(item_path):
                if item in ignored_dirs:
                    continue
                
                children = build_file_tree(item_path, rel_path, max_depth, current_depth + 1)
                tree.append({
                    "name": item,
                    "path": rel_path,
                    "type": "directory",
                    "children": children if children else None
                })
            elif os.path.isfile(item_path):
                _, ext = os.path.splitext(item)
                if ext.lower() in code_extensions or not ext:
                    tree.append({
                        "name": item,
                        "path": rel_path,
                        "type": "file",
                        "children": None
                    })
    except PermissionError:
        pass
    except Exception:
        pass
    
    return tree

def clone_repo(github_url: str, repo_id: uuid.UUID) -> str:
    repo_path = get_repo_path(repo_id)
    if os.path.exists(repo_path):
        return repo_path
        
    os.makedirs("/tmp/reploai", exist_ok=True)
    git.Repo.clone_from(github_url, repo_path)
    return repo_path

def get_file_content(repo_path: str, file_path: str, max_size: int = 10000) -> Optional[str]:
    full_path = os.path.join(repo_path, file_path)
    if not os.path.exists(full_path):
        return None
    
    try:
        # Check size
        if os.path.getsize(full_path) > max_size:
            return f"File too large to read ({os.path.getsize(full_path)} bytes). Content truncated."
            
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return None

