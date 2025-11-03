# LLM Provider Support

This document explains the multi-provider LLM support added to the codebase.

## Overview

The application now supports multiple LLM providers, including open-source alternatives to OpenAI:

- **OpenAI** (GPT-4, GPT-3.5) - Original provider
- **Ollama** - Local open-source models (Llama, Mistral, etc.)
- **HuggingFace** - Inference API for open-source models
- **Together AI** - Hosted open-source models
- **Groq** - Fast inference for open-source models
- **Gemini** (Google AI Studio) - Google's AI models

## Database Migration

You need to add new columns to the `user_settings` table:

```sql
ALTER TABLE user_settings
ADD COLUMN llm_provider VARCHAR DEFAULT 'openai',
ADD COLUMN llm_api_key VARCHAR,
ADD COLUMN llm_model VARCHAR,
ADD COLUMN llm_base_url VARCHAR;
```

Or using Alembic migration:

```bash
cd backend
alembic revision --autogenerate -m "Add LLM provider support"
alembic upgrade head
```

## API Endpoints

### Get LLM Settings

```
GET /api/settings/llm
```

### Update LLM Settings

```
PUT /api/settings/llm
Body: {
  "llm_provider": "ollama",  // "openai", "ollama", "huggingface", "together", "groq", "replicate", "gemini"
  "llm_api_key": "your-api-key",  // Not required for Ollama
  "llm_model": "llama3",  // Model name
  "llm_base_url": "http://localhost:11434"  // Only for Ollama
}
```

## Provider Setup

### 1. Ollama (Free, Local)

**Setup:**

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3
ollama pull mistral
```

**Configuration:**

- Provider: `ollama`
- Base URL: `http://localhost:11434` (default)
- Model: `llama3`, `mistral`, `codellama`, etc.
- API Key: Not required

**Example:**

```json
{
  "llm_provider": "ollama",
  "llm_model": "llama3",
  "llm_base_url": "http://localhost:11434"
}
```

### 2. HuggingFace (Free Tier Available)

**Setup:**

1. Create account at https://huggingface.co
2. Generate API token at https://huggingface.co/settings/tokens

**Configuration:**

- Provider: `huggingface`
- API Key: Your HuggingFace token
- Model: `mistralai/Mistral-7B-Instruct-v0.2`, `meta-llama/Llama-2-7b-chat-hf`, etc.

**Example:**

```json
{
  "llm_provider": "huggingface",
  "llm_api_key": "hf_xxxxxxxxxxxx",
  "llm_model": "mistralai/Mistral-7B-Instruct-v0.2"
}
```

### 3. Together AI (Pay-as-you-go)

**Setup:**

1. Create account at https://together.ai
2. Generate API key from dashboard

**Configuration:**

- Provider: `together`
- API Key: Your Together AI key
- Model: `meta-llama/Llama-3-8b-chat-hf`, `mistralai/Mixtral-8x7B-Instruct-v0.1`, etc.

**Example:**

```json
{
  "llm_provider": "together",
  "llm_api_key": "your-together-api-key",
  "llm_model": "meta-llama/Llama-3-8b-chat-hf"
}
```

### 4. Groq (Free Tier Available)

**Setup:**

1. Create account at https://console.groq.com
2. Generate API key

**Configuration:**

- Provider: `groq`
- API Key: Your Groq API key
- Model: `llama-3.1-8b-instant`, `mixtral-8x7b-32768`, etc.

**Example:**

```json
{
  "llm_provider": "groq",
  "llm_api_key": "your-groq-api-key",
  "llm_model": "llama-3.1-8b-instant"
}
```

### 5. Replicate (Pay-as-you-go)

**Setup:**

1. Create account at https://replicate.com
2. Generate API token from account settings

**Configuration:**

- Provider: `replicate`
- API Key: Your Replicate API token
- Model: `meta/llama-3-8b-instruct`, etc.

**Example:**

```json
{
  "llm_provider": "replicate",
  "llm_api_key": "your-replicate-api-token",
  "llm_model": "meta/llama-3-8b-instruct"
}
```

### 6. Gemini (Google AI Studio) - Free Tier Available

**Setup:**

1. Go to https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key" to generate a new key

**Configuration:**

- Provider: `gemini`
- API Key: Your Gemini API key (starts with `AIza`)
- Model: `gemini-pro`, `gemini-pro-vision`, etc.

**Example:**

```json
{
  "llm_provider": "gemini",
  "llm_api_key": "AIzaSy...",
  "llm_model": "gemini-pro"
}
```

### 7. OpenAI (Original)

**Configuration:**

- Provider: `openai`
- API Key: Your OpenAI API key (starts with `sk-`)
- Model: `gpt-4o`, `gpt-4-turbo-preview`, `gpt-3.5-turbo`, etc.

**Example:**

```json
{
  "llm_provider": "openai",
  "llm_api_key": "sk-xxxxxxxxxxxx",
  "llm_model": "gpt-4o"
}
```

## Backward Compatibility

The old `openai_api_key` field is still supported for backward compatibility. If a user has `openai_api_key` but no `llm_api_key`, the system will automatically use OpenAI as the provider.

## Code Architecture

### LLM Provider Abstraction

The `backend/app/core/llm_providers.py` file contains:

- `LLMProvider` - Abstract base class
- Provider implementations: `OpenAIProvider`, `OllamaProvider`, `HuggingFaceProvider`, `TogetherAIProvider`, `GroqProvider`, `ReplicateProvider`, `GeminiProvider`
- `create_llm_provider()` - Factory function

### Usage in Worker

The `analysis_worker.py` has been updated to:

1. Retrieve LLM provider settings from user settings
2. Create appropriate provider instance
3. Use unified `call_llm()` function instead of `call_gpt4()`

### Example Code

```python
from app.core.llm_providers import create_llm_provider

# Create provider
provider = create_llm_provider(
    provider_type="ollama",
    api_key=None,  # Not needed for Ollama
    model="llama3",
    base_url="http://localhost:11434"
)

# Generate response
response = await provider.generate(
    prompt="Explain Python decorators",
    response_format="text",
    temperature=0.2
)
```

## Troubleshooting

### Ollama Connection Issues

- Ensure Ollama is running: `ollama serve`
- Check if base URL is correct
- Verify model is downloaded: `ollama list`

### API Key Issues

- Verify API key format for each provider
- Check API key permissions/quotas
- For HuggingFace, ensure token has `read` permission

### Model Not Found

- Verify model name matches provider's model list
- Check if model requires special access (e.g., Meta Llama models)

## Notes

- **Free Options**: Ollama is completely free and runs locally. HuggingFace, Groq, and Gemini offer free tiers.
- **Performance**: Groq is extremely fast for inference. Ollama depends on your hardware. Gemini offers good performance with Google's infrastructure.
- **Privacy**: Ollama keeps everything local. Other providers send data to their servers.
- **Quality**: OpenAI GPT-4 and Google Gemini generally provide high quality responses. Open-source models are improving rapidly.
- **Gemini**: Google's Gemini models offer competitive quality and are available with a generous free tier through Google AI Studio.
