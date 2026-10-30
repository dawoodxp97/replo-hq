"""Phase 3: Updated AIClient supporting BYOK credential resolution."""

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any

import aiohttp
from sqlalchemy import select

from ..core.config import settings
from ..core.crypto import CredentialDecryptionError, decrypt_credential
from ..db.session import AsyncSessionLocal
from ..models.credentials import UserLLMCredential
from ..models.enums import LLMProvider
from ..utils.repo_utils import InvalidInputError

logger = logging.getLogger(__name__)

BASE_URL = f"{settings.openrouter_base_url}/chat/completions"
DEFAULT_MODEL = settings.openrouter_model


class AIClient:
    """AI client supporting both system key and BYOK credentials.

    For BYOK flows, credentials are resolved at call time using user_id and
    provider. The plaintext key never enters step context (input_data/output_data).
    """

    def __init__(
        self,
        user_id: str | None = None,
        provider: str = "openrouter",
        model: str | None = None,
        base_url: str | None = None,
    ):
        self.user_id = user_id
        self.provider = provider.lower()
        self.model = model or DEFAULT_MODEL
        self.base_url = base_url or settings.openrouter_base_url
        self._system_key: str | None = None
        # Token usage from the most recent successful call, as reported by the
        # provider (OpenAI-compatible `usage` object). Read by pipeline Step
        # after each call for the Phase 6 cost rollup. None when the call
        # failed or the provider reported nothing.
        self.last_usage: dict[str, Any] | None = None
        self._load_system_key()

    def _record_usage(self, model: str, usage: Any) -> None:
        """Normalize the provider's usage object into input/output token counts.

        OpenRouter passes through the OpenAI shape (`prompt_tokens` /
        `completion_tokens`). Missing fields become 0 so accumulation never
        crashes on a provider that reports partial usage.
        """
        if not isinstance(usage, dict):
            self.last_usage = None
            return
        self.last_usage = {
            "model": model,
            "input_tokens": int(usage.get("prompt_tokens") or 0),
            "output_tokens": int(usage.get("completion_tokens") or 0),
        }

    def _load_system_key(self) -> None:
        """Load the system OpenRouter key for non-BYOK calls."""
        key = settings.openrouter_api_key
        self._system_key = key.get_secret_value() if key else None
        if not self._system_key:
            logger.debug("OPENROUTER_API_KEY not configured for system calls.")

    async def _get_byok_credential(self) -> tuple[str, str] | None:
        """
        Resolve BYOK credential for the user.

        Returns (api_key, base_url) or None if no credential found.
        """
        if not self.user_id:
            return None

        try:
            user_uuid = uuid.UUID(self.user_id)
        except (ValueError, TypeError):
            logger.warning(f"Invalid user_id format: {self.user_id}")
            return None

        provider_map = {
            "openrouter": LLMProvider.OPENROUTER,
            "openai": LLMProvider.OPENAI,
            "anthropic": LLMProvider.ANTHROPIC,
        }
        provider_enum = provider_map.get(self.provider, LLMProvider.OPENROUTER)

        try:
            # Its own short-lived session: the caller may hold a transaction
            # open, and this lookup must never join or block it.
            async with AsyncSessionLocal() as db:
                credential = (
                    await db.execute(
                        select(UserLLMCredential).where(
                            UserLLMCredential.user_id == user_uuid,
                            UserLLMCredential.provider == provider_enum,
                            UserLLMCredential.is_active == True,  # noqa: E712
                        )
                    )
                ).scalar_first()

                if not credential:
                    return None

                # AAD binds the ciphertext to (user, provider): a row copied
                # from another account fails to decrypt rather than yielding a
                # key billed to someone else.
                aad = f"{credential.user_id}:{self.provider}".encode()

                try:
                    plaintext = decrypt_credential(
                        credential.ciphertext,
                        credential.nonce,
                        credential.key_version,
                        aad=aad,
                    )
                except CredentialDecryptionError:
                    logger.warning(
                        "Failed to decrypt credential for user %s, provider %s",
                        credential.user_id,
                        self.provider,
                    )
                    return None

                base_url = credential.base_url or settings.openrouter_base_url

                # Mark as used
                credential.last_used_at = datetime.utcnow()
                await db.commit()

                return (plaintext, base_url)

        except Exception:
            logger.exception("Error resolving BYOK credential")
            return None

    async def send_message(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Send a message to the AI API with retry logic."""
        model = model or self.model

        # Resolve credentials
        if self.user_id:
            byok = await self._get_byok_credential()
            if byok:
                api_key, base_url = byok
            else:
                api_key = self._system_key
                base_url = self.base_url
                if not api_key:
                    raise InvalidInputError(
                        "No API key available. Please configure BYOK credentials or set OPENROUTER_API_KEY."
                    )
        else:
            api_key = self._system_key
            base_url = self.base_url
            if not api_key:
                raise InvalidInputError(
                    "System API key not configured. Please set OPENROUTER_API_KEY."
                )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://replo.hq",
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
            for attempt in range(3):
                try:
                    async with session.post(
                        f"{base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if "choices" in data and len(data["choices"]) > 0:
                                self._record_usage(model, data.get("usage"))
                                return data["choices"][0]["message"]["content"]
                            else:
                                raise Exception(f"Invalid API response structure: {data}")
                        else:
                            error_text = await response.text()
                            logger.error(
                                f"AI API Error (Attempt {attempt + 1}): "
                                f"{response.status} - {error_text[:500]}"
                            )
                            # Rate limit or server errors - retry with backoff
                            if response.status in [429, 500, 502, 503]:
                                delay = (2**attempt) * 2
                                await asyncio.sleep(delay)
                                continue
                            raise Exception(f"AI API Error: {response.status} - {error_text}")

                except aiohttp.ClientError as e:
                    logger.error(f"Network Error (Attempt {attempt + 1}): {str(e)}")
                    await asyncio.sleep((2**attempt) * 2)
                    continue

            raise Exception("Max retries exceeded for AI API call")

    def parse_json_response(self, response: str) -> dict[str, Any]:
        """Parse JSON from AI response, handling Markdown code blocks."""
        try:
            match = re.search(r"```(?:json)?\s*(.*?)```", response, re.DOTALL)
            json_str = match.group(1).strip() if match else response.strip()
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback: extract JSON object
            start = response.find("{")
            end = response.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(response[start : end + 1])
                except json.JSONDecodeError:
                    pass

            logger.error(f"Failed to parse JSON response: {response[:200]}")
            raise ValueError("Invalid JSON response from AI")
