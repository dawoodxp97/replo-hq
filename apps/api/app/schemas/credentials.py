"""BYOK credential schemas.

**No response model here contains the API key**, and there is no endpoint that
returns one. `services/credentials.py::resolve_credential` is the only path that
decrypts, and it is called by the AI client at the moment of a request — never by
a router. A "reveal key" endpoint would defeat the encryption entirely, since the
value is stored precisely so that a database dump does not yield working keys.

The UI renders `provider`, `label` and `last_four`, all of which are stored in
plaintext for exactly that reason.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..core.net import validate_outbound_url
from ..models.enums import LLMProvider


class CredentialCreate(BaseModel):
    provider: LLMProvider = LLMProvider.OPENROUTER
    api_key: str = Field(min_length=8, max_length=500)
    label: str = Field(default="default", min_length=1, max_length=100)

    # Any OpenAI-compatible endpoint. Validated against the SSRF rules in
    # core/net.py — the server fetches this URL, so it must not be able to reach
    # loopback, private ranges or the cloud metadata endpoint.
    base_url: str | None = Field(default=None, max_length=500)
    default_model: str | None = Field(default=None, max_length=200)

    # Off by default: validation makes a live outbound request, so it happens
    # only when the user asks for it.
    validate_key: bool = False

    @field_validator("base_url")
    @classmethod
    def _check_base_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return validate_outbound_url(value)

    @field_validator("api_key")
    @classmethod
    def _strip(cls, value: str) -> str:
        # A pasted key routinely carries whitespace or a newline, which would
        # otherwise be encrypted verbatim and rejected by the provider with an
        # error the user cannot explain.
        return value.strip()


class CredentialResponse(BaseModel):
    id: UUID
    provider: LLMProvider
    label: str
    last_four: str
    base_url: str | None = None
    default_model: str | None = None
    is_active: bool
    last_validated_at: datetime | None = None
    last_used_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CredentialCreateResponse(BaseModel):
    credential: CredentialResponse
    # None when validation was not requested.
    validated: bool | None = None
    validation_error: str | None = None
