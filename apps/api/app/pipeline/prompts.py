"""Phase 3: Centralized prompt registry.

Replaces scattered hardcoded strings and `str.format()` templating. Prompts use
`string.Template` with `$placeholders` to avoid `KeyError` when repo code contains
braces.
"""

from string import Template

# =============================================================================
# AnalyzeRepoStep Prompts
# =============================================================================

ANALYZE_REPO_SYSTEM = Template(
    "You are an expert code analyst. "
    "Your goal is to analyze a codebase and provide a structural overview for creating a tutorial."
)

ANALYZE_REPO_USER = Template(
    """Analyze the following repository structure and provide insights:

**Repository Information:**
- Name: $repo_name
- Primary Language: $primary_language
- Description: $repo_description

**File Structure:**
$file_tree

**Key Files Content:**
$key_files_content

**Task:**
Identify:
1. Main entry points
2. Core functionality/features
3. Architecture patterns used
4. Dependencies and how they're used
5. Suggested tutorial flow

Respond in JSON format:
$response_format
"""
)

# =============================================================================
# GenerateOutlineStep Prompts
# =============================================================================

GENERATE_OUTLINE_SYSTEM = Template(
    "You are an expert technical writer. Create a comprehensive tutorial outline."
)

GENERATE_OUTLINE_USER = Template(
    """Based on the following repository analysis, create a structured tutorial outline.

**Repository Analysis:**
$repo_analysis

**Task:**
Create a step-by-step tutorial that guides a developer through building or understanding this project.
Structure it into logical chapters and sections.

Respond in JSON format:
$response_format
"""
)

# =============================================================================
# GenerateContentStep Prompts
# =============================================================================

GENERATE_CONTENT_SYSTEM = Template(
    "You are an expert technical instructor. Write clear, code-focused tutorial content."
)

GENERATE_CONTENT_USER = Template(
    """Write a comprehensive tutorial chapter.

**Chapter Title:** $chapter_title
**Sections to Cover:** $sections

**Context (Key Files):**
$repo_context

**Instructions:**
- Write in Markdown.
- Explain the concepts clearly.
- Use code snippets from the context where relevant.
- Keep it practical and hands-on.
"""
)

# =============================================================================
# RefineStep Prompts
# =============================================================================

REFINE_SYSTEM = Template(
    "You are an expert editor. Improve clarity, flow, and technical accuracy."
)

REFINE_USER = Template(
    """Review and refine the following tutorial chapter: "$title".

**Content:**
$content

**Instructions:**
- Improve clarity and readability.
- Fix any grammatical errors.
- Ensure code snippets are properly formatted.
- Make it engaging.
- Return ONLY the refined Markdown.
"""
)

# =============================================================================
# Model Registry (Phase 3.18)
# =============================================================================

# Map model names to their capabilities and tier
MODEL_REGISTRY = {
    "kwaipilot/kat-coder-pro:free": {
        "tier": "free",
        "context_window": 8192,
        "supports_json": True,
    },
    "kwaipilot/kat-coder-pro:standard": {
        "tier": "paid",
        "context_window": 32768,
        "supports_json": True,
    },
    "kwaipilot/kat-coder-pro:fast": {
        "tier": "paid",
        "context_window": 16384,
        "supports_json": True,
    },
    "openai/gpt-4o-mini": {
        "tier": "paid",
        "context_window": 128000,
        "supports_json": True,
    },
    "anthropic/claude-3-haiku": {
        "tier": "paid",
        "context_window": 200000,
        "supports_json": True,
    },
}


def get_model_tier(model_name: str) -> str:
    """Get the tier (free/paid) for a model name."""
    return MODEL_REGISTRY.get(model_name, {}).get("tier", "free")


def is_free_tier(model_name: str) -> bool:
    """Check if a model is on the free tier."""
    return get_model_tier(model_name) == "free"
