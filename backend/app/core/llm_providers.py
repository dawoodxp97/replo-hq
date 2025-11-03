# ./backend/app/core/llm_providers.py
"""
LLM Provider Abstraction Layer

This module provides a unified interface for multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Ollama (Local open-source models: Llama, Mistral, etc.)
- HuggingFace (Inference API or Transformers)
- Together AI (Hosted open-source models)
- Groq (Fast inference for open-source models)
- Gemini (Google AI Studio)
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

from openai import OpenAI

logger = logging.getLogger(__name__)


def extract_json_from_response(content: str, content_type: str = "ollama") -> Any:
    """
    Robust JSON extraction from LLM responses.
    Handles markdown-wrapped JSON, partial responses, and malformed JSON.
    
    Args:
        content: The raw response content from LLM
        content_type: Provider name for logging
        
    Returns:
        Parsed JSON object or array
        
    Raises:
        Exception if no valid JSON can be extracted
    """
    import re
    
    content_original = content
    content = content.strip()
    
    # Strategy 1: Remove markdown code blocks
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    # Strategy 2: Try direct parsing first
    try:
        return json.loads(content)
    except:
        pass
    
    # Strategy 3: Extract JSON from markdown code blocks
    json_pattern = r'```(?:json)?\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```'
    match = re.search(json_pattern, content_original, re.MULTILINE | re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    
    # Strategy 4: Find JSON object/array using regex (non-greedy with better matching)
    # Try to find JSON more precisely
    json_patterns = [
        r'(\{[\s\S]*?\}(?=\s*(?:\n\n|\n#|$|\{|\[)))',  # JSON object followed by line break or end
        r'(\[[\s\S]*?\](?=\s*(?:\n\n|\n#|$|\{|\[)))',  # JSON array followed by line break or end
    ]
    
    for pattern in json_patterns:
        json_match = re.search(pattern, content_original, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                continue
    
    # Strategy 5: Find first valid JSON by bracket matching
    for start_char in ['{', '[']:
        start_idx = content_original.find(start_char)
        if start_idx != -1:
            bracket_stack = 0
            for i in range(start_idx, min(start_idx + 50000, len(content_original))):  # Limit search
                char = content_original[i]
                if char == '{' or char == '[':
                    bracket_stack += 1
                elif char == '}' or char == ']':
                    bracket_stack -= 1
                    if bracket_stack == 0:
                        try:
                            json_str = content_original[start_idx:i+1]
                            parsed = json.loads(json_str)
                            logger.info(f"[{content_type}] ✅ Extracted JSON from markdown response (found at position {start_idx})")
                            return parsed
                        except:
                            break
    
    # All strategies failed
    raise Exception(f"No valid JSON found in response. Response starts with: {content_original[:200]}")


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        response_format: str = "text",
        temperature: float = 0.2,
        system_message: Optional[str] = None
    ) -> Any:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt
            response_format: "text" or "json"
            temperature: Sampling temperature (0.0 to 2.0)
            system_message: Optional system message
            
        Returns:
            Response content (str for text, dict for JSON)
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate that the provider is properly configured."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI provider (GPT-4, GPT-3.5, etc.)"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key)
        
    def validate_config(self) -> bool:
        return bool(self.api_key and self.api_key.startswith("sk-"))
    
    async def generate(
        self,
        prompt: str,
        response_format: str = "text",
        temperature: float = 0.2,
        system_message: Optional[str] = None
    ) -> Any:
        """Generate using OpenAI API."""
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            else:
                messages.append({"role": "system", "content": "You are a helpful assistant."})
            messages.append({"role": "user", "content": prompt})
            
            logger.info(f"[OpenAI] Using model: {self.model}")
            logger.info(f"[OpenAI] Prompt length: {len(prompt)} characters")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                response_format={"type": response_format} if response_format == "json" else None
            )
            
            content = response.choices[0].message.content
            logger.info(f"[OpenAI] ✅ Response received (length: {len(content)} chars)")
            
            if response_format == "json":
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"[OpenAI] ❌ JSON parsing failed: {str(e)}")
                    return {}
            
            return content
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[OpenAI] ❌ API call failed: {error_msg}")
            
            # Check for quota errors
            if "quota" in error_msg.lower() or "429" in error_msg:
                raise Exception("API quota exceeded. Please add credits to your OpenAI account.")
            
            raise Exception(f"OpenAI API error: {error_msg}")


class OllamaProvider(LLMProvider):
    """Ollama provider for local open-source models."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model
        
    def validate_config(self) -> bool:
        import aiohttp
        import asyncio
        try:
            # Test connection (synchronous check)
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self._test_connection())
            loop.close()
            return result
        except:
            return False
    
    async def _test_connection(self) -> bool:
        """Test if Ollama is reachable."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    return resp.status == 200
        except:
            return False
    
    async def generate(
        self,
        prompt: str,
        response_format: str = "text",
        temperature: float = 0.2,
        system_message: Optional[str] = None
    ) -> Any:
        """Generate using Ollama API."""
        try:
            import aiohttp
            import asyncio
            
            # Combine system message and prompt
            full_prompt = prompt
            if system_message:
                full_prompt = f"{system_message}\n\n{prompt}"
            
            logger.info(f"[Ollama] Using model: {self.model}")
            logger.info(f"[Ollama] Prompt length: {len(full_prompt)} characters")
            
            async with aiohttp.ClientSession() as session:
                # Add format instruction if JSON is requested
                if response_format == "json":
                    format_instruction = "\n\nCRITICAL: You MUST respond with ONLY valid JSON. No markdown, no explanations, no code blocks. Just the raw JSON object or array."
                    full_prompt = full_prompt + format_instruction
                
                payload = {
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature
                    }
                }
                
                try:
                    async with session.post(
                        f"{self.base_url}/api/generate",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=300)  # 5 minute timeout
                    ) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            raise Exception(f"Ollama API returned status {resp.status}: {error_text}")
                        
                        result = await resp.json()
                        content = result.get("response", "")
                        logger.info(f"[Ollama] ✅ Response received (length: {len(content)} chars)")
                        
                        if response_format == "json":
                            try:
                                return extract_json_from_response(content, "Ollama")
                            except Exception as e:
                                # Check if response looks like it's completely ignoring JSON instruction
                                content_lower = content.lower()
                                is_markdown_tutorial = (
                                    content_lower.startswith('#') or 
                                    'html' in content_lower[:500] or
                                    'doctype' in content_lower[:500] or
                                    ('tutorial' in content_lower[:100] and 'json' not in content_lower[:500])
                                )
                                
                                if is_markdown_tutorial:
                                    error_msg = f"Ollama model ignored JSON format instruction and returned markdown/tutorial instead. This is a retriable error. Response starts with: {content[:200]}..."
                                    logger.error(f"[Ollama] ❌ {error_msg}")
                                    # Make this retriable by raising a specific exception
                                    raise Exception(error_msg)
                                
                                logger.error(f"[Ollama] ❌ JSON parsing failed: {str(e)}")
                                logger.error(f"[Ollama] Raw content preview: {content[:1000]}...")
                                raise Exception(f"Invalid JSON response from Ollama: {str(e)}")
                        
                        return content
                        
                except asyncio.TimeoutError:
                    error_msg = f"Request timed out after 300 seconds. Ollama may be slow or unresponsive. Check if Ollama is running at {self.base_url} and if the model '{self.model}' is available."
                    logger.error(f"[Ollama] ❌ {error_msg}")
                    raise Exception(error_msg)
                except aiohttp.ClientConnectorError as e:
                    error_msg = f"Cannot connect to Ollama at {self.base_url}. Make sure Ollama is running (try 'ollama serve' or check your base_url setting)."
                    logger.error(f"[Ollama] ❌ {error_msg}")
                    raise Exception(error_msg)
                except aiohttp.ClientError as e:
                    error_msg = f"HTTP client error connecting to Ollama: {str(e)}"
                    logger.error(f"[Ollama] ❌ {error_msg}")
                    raise Exception(error_msg)
                    
        except Exception as e:
            # Re-raise if it's already a formatted exception
            if "Ollama" in str(e) or "Ollama" in type(e).__name__:
                raise
            
            error_msg = str(e) if str(e) else type(e).__name__
            logger.error(f"[Ollama] ❌ API call failed: {error_msg}")
            
            # Provide more context for unknown errors
            if not error_msg or error_msg == type(e).__name__:
                raise Exception(f"Ollama API error: Connection to {self.base_url} failed. Make sure Ollama is running and the model '{self.model}' is available (run 'ollama list' to see available models).")
            
            raise Exception(f"Ollama API error: {error_msg}")


class HuggingFaceProvider(LLMProvider):
    """HuggingFace Inference API provider."""
    
    def __init__(self, api_key: str, model: str = "mistralai/Mistral-7B-Instruct-v0.2"):
        self.api_key = api_key
        self.model = model
        
    def validate_config(self) -> bool:
        return bool(self.api_key)
    
    async def generate(
        self,
        prompt: str,
        response_format: str = "text",
        temperature: float = 0.2,
        system_message: Optional[str] = None
    ) -> Any:
        """Generate using HuggingFace Inference API."""
        try:
            import aiohttp
            
            # Combine system message and prompt
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            logger.info(f"[HuggingFace] Using model: {self.model}")
            logger.info(f"[HuggingFace] Prompt length: {len(prompt)} characters")
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "inputs": messages,
                    "parameters": {
                        "temperature": temperature,
                        "max_new_tokens": 2048,
                        "return_full_text": False
                    }
                }
                
                async with session.post(
                    f"https://api-inference.huggingface.co/models/{self.model}",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"HuggingFace API error: {error_text}")
                    
                    result = await resp.json()
                    # HuggingFace returns a list of generated texts
                    if isinstance(result, list) and len(result) > 0:
                        content = result[0].get("generated_text", "")
                    else:
                        content = str(result)
                    
                    logger.info(f"[HuggingFace] ✅ Response received (length: {len(content)} chars)")
                    
                    if response_format == "json":
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError as e:
                            logger.error(f"[HuggingFace] ❌ JSON parsing failed: {str(e)}")
                            return {}
                    
                    return content
                    
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[HuggingFace] ❌ API call failed: {error_msg}")
            raise Exception(f"HuggingFace API error: {error_msg}")


class TogetherAIProvider(LLMProvider):
    """Together AI provider for hosted open-source models."""
    
    def __init__(self, api_key: str, model: str = "meta-llama/Llama-3-8b-chat-hf"):
        self.api_key = api_key
        self.model = model
        
    def validate_config(self) -> bool:
        return bool(self.api_key)
    
    async def generate(
        self,
        prompt: str,
        response_format: str = "text",
        temperature: float = 0.2,
        system_message: Optional[str] = None
    ) -> Any:
        """Generate using Together AI API."""
        try:
            import aiohttp
            
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            logger.info(f"[TogetherAI] Using model: {self.model}")
            logger.info(f"[TogetherAI] Prompt length: {len(prompt)} characters")
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 4096
                }
                
                async with session.post(
                    "https://api.together.xyz/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Together AI API error: {error_text}")
                    
                    result = await resp.json()
                    content = result["choices"][0]["message"]["content"]
                    logger.info(f"[TogetherAI] ✅ Response received (length: {len(content)} chars)")
                    
                    if response_format == "json":
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError as e:
                            logger.error(f"[TogetherAI] ❌ JSON parsing failed: {str(e)}")
                            return {}
                    
                    return content
                    
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[TogetherAI] ❌ API call failed: {error_msg}")
            raise Exception(f"Together AI API error: {error_msg}")


class GroqProvider(LLMProvider):
    """Groq provider for fast inference (open-source models)."""
    
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        self.api_key = api_key
        self.model = model
        
    def validate_config(self) -> bool:
        return bool(self.api_key)
    
    async def generate(
        self,
        prompt: str,
        response_format: str = "text",
        temperature: float = 0.2,
        system_message: Optional[str] = None
    ) -> Any:
        """Generate using Groq API."""
        try:
            import aiohttp
            
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            logger.info(f"[Groq] Using model: {self.model}")
            logger.info(f"[Groq] Prompt length: {len(prompt)} characters")
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature
                }
                
                async with session.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Groq API error: {error_text}")
                    
                    result = await resp.json()
                    content = result["choices"][0]["message"]["content"]
                    logger.info(f"[Groq] ✅ Response received (length: {len(content)} chars)")
                    
                    if response_format == "json":
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError as e:
                            logger.error(f"[Groq] ❌ JSON parsing failed: {str(e)}")
                            return {}
                    
                    return content
                    
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[Groq] ❌ API call failed: {error_msg}")
            raise Exception(f"Groq API error: {error_msg}")


class ReplicateProvider(LLMProvider):
    """Replicate provider for running open-source models."""
    
    def __init__(self, api_key: str, model: str = "meta/llama-3-8b-instruct"):
        self.api_key = api_key
        self.model = model
        
    def validate_config(self) -> bool:
        return bool(self.api_key)
    
    async def generate(
        self,
        prompt: str,
        response_format: str = "text",
        temperature: float = 0.2,
        system_message: Optional[str] = None
    ) -> Any:
        """Generate using Replicate API."""
        try:
            import aiohttp
            
            # Combine system message and prompt
            full_prompt = prompt
            if system_message:
                full_prompt = f"{system_message}\n\n{prompt}"
            
            logger.info(f"[Replicate] Using model: {self.model}")
            logger.info(f"[Replicate] Prompt length: {len(full_prompt)} characters")
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "input": {
                        "prompt": full_prompt,
                        "temperature": temperature,
                        "max_tokens": 4096
                    }
                }
                
                async with session.post(
                    f"https://api.replicate.com/v1/models/{self.model}/predictions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as resp:
                    if resp.status != 201:
                        error_text = await resp.text()
                        raise Exception(f"Replicate API error: {error_text}")
                    
                    result = await resp.json()
                    prediction_id = result.get("id")
                    
                    # Poll for result (simplified - in production, use proper polling)
                    import asyncio
                    for _ in range(30):  # 30 attempts, ~30 seconds
                        await asyncio.sleep(1)
                        async with session.get(
                            f"https://api.replicate.com/v1/predictions/{prediction_id}",
                            headers=headers
                        ) as status_resp:
                            status_result = await status_resp.json()
                            status = status_result.get("status")
                            if status == "succeeded":
                                content = "".join(status_result.get("output", []))
                                logger.info(f"[Replicate] ✅ Response received (length: {len(content)} chars)")
                                if response_format == "json":
                                    try:
                                        return json.loads(content)
                                    except json.JSONDecodeError as e:
                                        logger.error(f"[Replicate] ❌ JSON parsing failed: {str(e)}")
                                        return {}
                                return content
                            elif status == "failed":
                                raise Exception(f"Replicate prediction failed: {status_result.get('error', 'Unknown error')}")
                    
                    raise Exception("Replicate prediction timeout")
                    
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[Replicate] ❌ API call failed: {error_msg}")
            raise Exception(f"Replicate API error: {error_msg}")


class GeminiProvider(LLMProvider):
    """Google Gemini provider (via Google AI Studio)."""
    
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        self.api_key = api_key
        self.model = model
        
    def validate_config(self) -> bool:
        return bool(self.api_key)
    
    async def generate(
        self,
        prompt: str,
        response_format: str = "text",
        temperature: float = 0.2,
        system_message: Optional[str] = None
    ) -> Any:
        """Generate using Google Gemini API."""
        try:
            import aiohttp
            
            # Validate API key
            if not self.api_key or not self.api_key.strip():
                raise ValueError("Gemini API key is required and cannot be empty")
            
            api_key = self.api_key.strip()
            
            # Log API key info (first 10 chars only for security)
            api_key_preview = api_key[:10] + "..." if len(api_key) > 10 else api_key[:5] + "..."
            logger.info(f"[Gemini] Using model: {self.model}")
            logger.info(f"[Gemini] API key preview: {api_key_preview}")
            logger.info(f"[Gemini] Prompt length: {len(prompt)} characters")
            
            async with aiohttp.ClientSession() as session:
                # Use header-based authentication (more secure than query param)
                headers = {
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key
                }
                
                # Google Gemini API endpoint (without key in URL)
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
                
                # Format content for Gemini API
                contents = []
                if system_message:
                    contents.append({
                        "parts": [{"text": system_message}],
                        "role": "user"
                    })
                    contents.append({
                        "parts": [{"text": "Okay"}],
                        "role": "model"
                    })
                
                contents.append({
                    "parts": [{"text": prompt}],
                    "role": "user"
                })
                
                payload = {
                    "contents": contents,
                    "generationConfig": {
                        "temperature": temperature,
                        "maxOutputTokens": 8192
                    }
                }
                
                async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as resp:
                    if resp.status != 200:
                        # Try to parse error response
                        try:
                            error_json = await resp.json()
                            error_message = error_json.get("error", {}).get("message", "Unknown error")
                            error_code = error_json.get("error", {}).get("code", resp.status)
                            error_status = error_json.get("error", {}).get("status", "UNKNOWN")
                            logger.error(f"[Gemini] API returned status {resp.status}: {error_message}")
                            
                            # Provide more helpful error messages for different error types
                            if "API key not valid" in error_message or "API_KEY_INVALID" in str(error_json):
                                raise Exception("Invalid Gemini API key. Please check your API key at https://aistudio.google.com/app/apikey")
                            elif error_code == 429:
                                raise Exception("Gemini API quota exceeded. Please check your usage limits.")
                            elif error_code == 503 or error_status == "UNAVAILABLE":
                                # Service temporarily unavailable - could retry or fallback
                                raise Exception(f"Gemini API is temporarily unavailable (503): {error_message}. This is usually temporary - please try again in a few moments or use a different provider.")
                            elif error_code >= 500:
                                # Server errors - might be temporary
                                raise Exception(f"Gemini API server error (code {error_code}): {error_message}. Please try again later.")
                            else:
                                raise Exception(f"Gemini API error (code {error_code}): {error_message}")
                        except json.JSONDecodeError:
                            # If we can't parse JSON, try to get text error
                            try:
                                error_text = await resp.text()
                            except:
                                error_text = f"HTTP {resp.status} error"
                            raise Exception(f"Gemini API error (status {resp.status}): {error_text}")
                    
                    # Success - parse the response
                    result = await resp.json()
                    
                    # Extract content from Gemini response
                    if "candidates" in result and len(result["candidates"]) > 0:
                        candidate = result["candidates"][0]
                        
                        # Check for safety ratings blocking the response
                        if "safetyRatings" in candidate:
                            blocking = [r for r in candidate["safetyRatings"] if r.get("category") == "HARM_CATEGORY_DANGEROUS_CONTENT" and r.get("probability") == "HIGH"]
                            if blocking:
                                logger.warning(f"[Gemini] Content blocked by safety filters")
                                raise Exception("Gemini blocked the content due to safety filters. Please modify your prompt.")
                        
                        if "content" in candidate and "parts" in candidate["content"]:
                            parts = candidate["content"]["parts"]
                            if parts and len(parts) > 0:
                                content = parts[0].get("text", "")
                            else:
                                raise Exception("Gemini API returned empty content parts")
                        else:
                            # Check for finish reason
                            finish_reason = candidate.get("finishReason", "UNKNOWN")
                            if finish_reason != "STOP":
                                logger.warning(f"[Gemini] Finish reason: {finish_reason}")
                            raise Exception(f"Gemini API returned unexpected response format: {candidate}")
                    else:
                        raise Exception(f"Gemini API returned no candidates: {result}")
                    
                    logger.info(f"[Gemini] ✅ Response received (length: {len(content)} chars)")
                    
                    if response_format == "json":
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError as e:
                            logger.error(f"[Gemini] ❌ JSON parsing failed: {str(e)}")
                            return {}
                    
                    return content
                    
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[Gemini] ❌ API call failed: {error_msg}")
            raise Exception(f"Gemini API error: {error_msg}")


def create_llm_provider(
    provider_type: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None
) -> LLMProvider:
    """
    Factory function to create an LLM provider instance.
    
    Args:
        provider_type: One of "openai", "ollama", "huggingface", "together", "groq", "replicate", "gemini"
        api_key: Provider API key (required for most providers)
        model: Model name to use
        base_url: Base URL (mainly for Ollama)
        
    Returns:
        LLMProvider instance
    """
    provider_type = provider_type.lower()
    
    if provider_type == "openai":
        if not api_key:
            raise ValueError("OpenAI requires an API key")
        return OpenAIProvider(api_key, model or "gpt-4o")
    
    elif provider_type == "ollama":
        return OllamaProvider(
            base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model or os.getenv("OLLAMA_MODEL", "llama3")
        )
    
    elif provider_type == "huggingface":
        if not api_key:
            raise ValueError("HuggingFace requires an API key")
        return HuggingFaceProvider(
            api_key,
            model or "mistralai/Mistral-7B-Instruct-v0.2"
        )
    
    elif provider_type == "together":
        if not api_key:
            raise ValueError("Together AI requires an API key")
        return TogetherAIProvider(
            api_key,
            model or "meta-llama/Llama-3-8b-chat-hf"
        )
    
    elif provider_type == "groq":
        if not api_key:
            raise ValueError("Groq requires an API key")
        return GroqProvider(
            api_key,
            model or "llama-3.1-8b-instant"
        )
    
    elif provider_type == "replicate":
        if not api_key:
            raise ValueError("Replicate requires an API key")
        return ReplicateProvider(
            api_key,
            model or "meta/llama-3-8b-instruct"
        )
    
    elif provider_type == "gemini":
        if not api_key:
            raise ValueError("Gemini requires an API key")
        return GeminiProvider(
            api_key,
            model or "gemini-pro"
        )
    
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")

