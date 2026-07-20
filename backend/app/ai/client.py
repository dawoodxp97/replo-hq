import os
import logging
import aiohttp
import asyncio
import json
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "kwaipilot/kat-coder-pro:free"

class AIClient:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY is not set.")

    async def send_message(
        self,
        messages: List[Dict[str, str]],
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://replo.hq", # Required by OpenRouter
            "X-Title": "Replo HQ"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if response_format:
            payload["response_format"] = response_format

        async with aiohttp.ClientSession() as session:
            for attempt in range(3): # Retry logic
                try:
                    async with session.post(BASE_URL, headers=headers, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'choices' in data and len(data['choices']) > 0:
                                return data['choices'][0]['message']['content']
                            else:
                                raise Exception(f"Invalid API response structure: {data}")
                        else:
                            error_text = await response.text()
                            logger.error(f"AI API Error (Attempt {attempt+1}): {response.status} - {error_text}")
                            if response.status in [429, 500, 502, 503]:
                                await asyncio.sleep(2 ** attempt) # Exponential backoff
                                continue
                            raise Exception(f"AI API Error: {response.status} - {error_text}")
                            
                except aiohttp.ClientError as e:
                    logger.error(f"Network Error (Attempt {attempt+1}): {str(e)}")
                    await asyncio.sleep(2 ** attempt)
                    continue
            
            raise Exception("Max retries exceeded for AI API call")

    def parse_json_response(self, response: str) -> Dict[str, Any]:
        try:
            # Use regex to extract JSON content from potential Markdown
            match = re.search(r'```(?:json)?\s*(.*?)```', response, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
            else:
                # Fallback: assume the entire response is JSON or needs cleanup
                json_str = response.strip()

            # Attempt to parse the extracted string
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # Second attempt: aggressive cleanup if simple extraction failed
            try:
                 # Find the first '{' and the last '}'
                start = response.find('{')
                end = response.rfind('}')
                if start != -1 and end != -1:
                    json_str = response[start:end+1]
                    return json.loads(json_str)
            except Exception:
                pass
            
            logger.error(f"Failed to parse JSON response: {response}")
            raise ValueError(f"Invalid JSON response from AI: {str(e)}")
