import asyncio
import json
import logging
import re
from typing import Any

import aiohttp

from ..core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = f"{settings.openrouter_base_url}/chat/completions"
DEFAULT_MODEL = settings.openrouter_model


class AIClient:
    def __init__(self):
        # Phase 3 replaces this with per-user BYOK credential resolution. The
        # credential is fetched at call time and must never enter step context —
        # step input_data/output_data are persisted verbatim to Postgres.
        key = settings.openrouter_api_key
        self.api_key = key.get_secret_value() if key else None
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY is not set.")

    async def send_message(
        self,
        messages: list[dict[str, str]],
        model: str = DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: dict | None = None,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://replo.hq",  # Required by OpenRouter
            "X-Title": "Replo HQ",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            payload["response_format"] = response_format

        async with aiohttp.ClientSession() as session:
            for attempt in range(3):  # Retry logic
                try:
                    async with session.post(BASE_URL, headers=headers, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                            if "choices" in data and len(data["choices"]) > 0:
                                return data["choices"][0]["message"]["content"]
                            else:
                                raise Exception(f"Invalid API response structure: {data}")
                        else:
                            error_text = await response.text()
                            logger.error(
                                f"AI API Error (Attempt {attempt + 1}): {response.status} - {error_text}"
                            )
                            if response.status in [429, 500, 502, 503]:
                                await asyncio.sleep(2**attempt)  # Exponential backoff
                                continue
                            raise Exception(f"AI API Error: {response.status} - {error_text}")

                except aiohttp.ClientError as e:
                    logger.error(f"Network Error (Attempt {attempt + 1}): {str(e)}")
                    await asyncio.sleep(2**attempt)
                    continue

            raise Exception("Max retries exceeded for AI API call")

    def parse_json_response(self, response: str) -> dict[str, Any]:
        try:
            # Use regex to extract JSON content from potential Markdown
            match = re.search(r"```(?:json)?\s*(.*?)```", response, re.DOTALL)
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
                start = response.find("{")
                end = response.rfind("}")
                if start != -1 and end != -1:
                    json_str = response[start : end + 1]
                    return json.loads(json_str)
            except Exception:
                pass

            logger.error(f"Failed to parse JSON response: {response}")
            raise ValueError(f"Invalid JSON response from AI: {str(e)}")
