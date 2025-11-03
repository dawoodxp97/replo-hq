# AI Prompt Locations for Tutorial Generation

## Overview
The tutorial generation uses GPT-4 to create interactive tutorials. The prompts are constructed in two places:

1. **Base Prompt Templates** - `backend/app/core/generation_service.py`
2. **Enhanced Prompts with Repo Contents** - `backend/app/workers/analysis_worker.py`

## Prompt Flow

### 1. Tutorial Outline Prompt
**Location**: `backend/app/core/generation_service.py` → `create_gpt_outline_prompt()`

**Base Prompt** (Lines 5-68):
- System prompt: Explains the role as expert developer and curriculum designer
- User prompt: Includes tutorial level, code structure, and code summaries
- Returns: JSON array of tutorial modules with title, key_concepts, and file_path

**Enhanced in Worker** (`backend/app/workers/analysis_worker.py`):
- Line 600: Calls `create_gpt_outline_prompt()` to get base prompt
- Lines 602-612: **Adds actual repository code files** (first 20 files, truncated to 2000 chars each)
- Lines 614-623: **Adds focus areas and description** if provided
- Line 625: Sends enhanced prompt to GPT-4 via `call_gpt4()`

**Example Enhanced Prompt Structure**:
```
[Base system/user prompt from generation_service.py]
=== Repository Code Files (20 files shown) ===
=== File: src/index.js ===
[actual code content...]
=== File: src/routes/api.js ===
[actual code content...]
...
=== Additional Requirements ===
Focus Areas: architecture, patterns
Additional Context: Focus on async patterns
```

### 2. Module Content Prompt
**Location**: `backend/app/core/generation_service.py` → `create_gpt_module_prompt()`

**Base Prompt** (Lines 71-137):
- System prompt: Role as technical writer for specific level
- User prompt: Includes tutorial level, full outline, current module outline, and source code
- Returns: JSON with title, content_markdown, code_snippet, diagram_mermaid

**Used in Worker** (`backend/app/workers/analysis_worker.py`):
- Line 656: Reads actual file content from repository
- Lines 659-664: Creates module prompt with real file content
- Line 666: Sends to GPT-4 via `call_gpt4()`

### 3. Quiz Prompt
**Location**: `backend/app/core/generation_service.py` → `create_gpt_quiz_prompt()`

**Base Prompt** (Lines 140-189):
- System prompt: Role as technical instructor
- User prompt: Includes tutorial content and code snippet
- Returns: JSON with question_text and options array

**Used in Worker** (`backend/app/workers/analysis_worker.py`):
- Lines 683-686: Creates quiz prompt from generated module content
- Line 688: Sends to GPT-4 via `call_gpt4()`

## Key Files

### Prompt Template File
- **File**: `backend/app/core/generation_service.py`
- **Functions**:
  - `create_gpt_outline_prompt()` - Tutorial outline generation
  - `create_gpt_module_prompt()` - Module content generation
  - `create_gpt_quiz_prompt()` - Quiz question generation

### Worker File (Where Prompts Are Used)
- **File**: `backend/app/workers/analysis_worker.py`
- **Function**: `generate_tutorial()` (Lines 514-754)
- **Key Sections**:
  - Line 600: Outline prompt creation
  - Lines 602-623: **Repository contents added to outline prompt**
  - Line 625: Outline sent to GPT-4
  - Line 659: Module prompt creation
  - Line 666: Module content sent to GPT-4
  - Line 683: Quiz prompt creation
  - Line 688: Quiz sent to GPT-4

### OpenAI API Call
- **Function**: `call_gpt4()` (Lines 245-277 in `analysis_worker.py`)
- **Parameters**: 
  - `api_key`: User's OpenAI API key
  - `prompt`: The enhanced prompt string
  - `response_format`: "json" or "text"
- **Uses**: New OpenAI client (`from openai import OpenAI`)

## Important Notes

1. **Repository Contents Are Added**: The outline prompt is enhanced with actual code files from the repository (up to 20 files, 2000 chars each) to give GPT-4 real context.

2. **User's API Key**: All GPT-4 calls use the user's personal OpenAI API key stored in `UserSettings.openai_api_key`.

3. **Focus Areas & Description**: If provided by the user, these are appended to the outline prompt as additional requirements.

4. **Prompt Enhancement Location**: The actual enhancement (adding repo contents) happens in `analysis_worker.py` at lines 602-623, not in the base prompt templates.

