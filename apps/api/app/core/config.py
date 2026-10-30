"""Typed application configuration.

Single source of truth for every environment-derived value. Replaces scattered
`os.getenv(...)` calls and the relative `../../.env` path walk that used to live
in `main.py`.

Why this module exists — the bug it prevents:

    SECRET_KEY = os.environ.get("SECRET_KEY", "a_very_secret_key_fallback")

The root `.env` defines `JWT_SECRET_KEY`. Nothing ever defined `SECRET_KEY`. So
every JWT in every environment was signed with that literal fallback string,
which is public in the repo — meaning anyone could forge a token for any user.
It failed silently because a default was available.

Nothing here has a fallback for a secret. Missing or malformed config raises at
import time, before the app can serve a request.
"""

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, SecretStr, computed_field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _repo_root() -> Path:
    """Walk up to the monorepo root, identified by pnpm-workspace.yaml.

    Explicit marker rather than a fixed number of `.parent` hops, which silently
    pointed at the wrong directory the moment `backend/` moved to `apps/api/`.
    """
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "pnpm-workspace.yaml").exists():
            return candidate
    return Path.cwd()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Root .env first, then a local override for per-app experimentation.
        # In Docker neither exists — compose injects real environment variables,
        # which take precedence over both.
        env_file=(_repo_root() / ".env", Path("apps/api/.env")),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Environment ---
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    # --- Postgres ---
    # DATABASE_URL, when set, wins outright — that is how Railway and docker-compose
    # inject connection details.
    database_url: str | None = Field(default=None)
    postgres_user: str = Field(default="tutorial_user")
    postgres_password: SecretStr = Field(default=SecretStr("tutorial_password"))
    postgres_db: str = Field(default="tutorial_db")
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)

    # --- Redis ---
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_password: SecretStr | None = Field(default=None)
    redis_db: int = Field(default=0)

    # --- Auth ---
    # No default. This is the whole point of the module.
    jwt_secret_key: SecretStr = Field(min_length=32)
    jwt_algorithm: str = Field(default="HS256")
    # Access short, refresh long. The old values were inverted: a 7-day access
    # token against a 1-day refresh token, which makes refresh pointless.
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=30)

    # --- Credential encryption (BYOK) ---
    # Base64-encoded 32 bytes (AES-256). Generate:
    #   python -c "import base64,os; print(base64.b64encode(os.urandom(32)).decode())"
    #
    # Optional so the API can boot without BYOK configured — storing a credential
    # then fails loudly rather than silently writing something unencrypted.
    credential_encryption_key: SecretStr | None = Field(default=None)
    credential_key_version: int = Field(default=1)
    # Set during a key rotation window: new writes use the current key, existing
    # rows still decrypt with the previous one until re-encrypted.
    credential_encryption_key_previous: SecretStr | None = Field(default=None)

    # --- LLM ---
    openrouter_api_key: SecretStr | None = Field(default=None)
    openrouter_model: str = Field(default="anthropic/claude-haiku-4.5")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1")

    # --- OAuth (D10) ---
    # Per-provider client credentials. A provider whose id/secret is unset is
    # simply not offered: the authorize endpoint returns 404 for it rather than
    # redirecting into a broken flow.
    github_client_id: str | None = Field(default=None)
    github_client_secret: SecretStr | None = Field(default=None)
    google_client_id: str | None = Field(default=None)
    google_client_secret: SecretStr | None = Field(default=None)
    # Absolute base the provider is told to call back to. This is the SPA's
    # origin, not the API's: the provider lands on the app, and the app's
    # /api/user/oauth/:provider/callback route exchanges the code through the
    # API (whose callback endpoint returns JSON for exactly that use).
    # Compose/Railway inject the public URL; localhost is only the dev default.
    oauth_callback_base_url: str = Field(default="http://localhost:3000")

    # --- Generation streaming (4.8) ---
    # EventSource cannot send headers, so the SSE endpoint authenticates with a
    # short-lived signed ticket the client takes from the status payload. Long
    # enough to open the connection after a status poll; short enough that a
    # leaked URL in a referrer header expires before it is useful.
    stream_ticket_expire_seconds: int = Field(default=120)

    # --- Rate limiting (Phase 3.12) ---
    # Fixed-window counters in Redis. Generation limits are per user, auth
    # limits per client IP. A window is one limiter instance, not a global knob.
    rate_limit_enabled: bool = Field(default=True)
    auth_rate_limit_per_minute: int = Field(default=10)
    generation_rate_limit_per_hour: int = Field(default=30)

    # --- Step data retention (Phase 3.13) ---
    # TutorialStepExecution.input_data / output_data are written on every step
    # of every run and nobody reads them back routinely. Uncapped, a large repo
    # analysis writes megabytes per row. Serialized JSON larger than this is
    # replaced by a truncation marker. See app/pipeline/base_step.py.
    step_data_max_bytes: int = Field(default=65536)

    # --- Error tracking (Phase 6) ---
    # Optional: the app runs fine with it unset, and tests never enable it.
    sentry_dsn: SecretStr | None = Field(default=None)
    sentry_traces_sample_rate: float = Field(default=0.0)

    # --- CORS ---
    # NoDecode is required: without it the dotenv source tries json.loads() on the
    # raw value before any validator runs, so a plain `a,b` string raises
    # SettingsError instead of reaching _split_csv below.
    cors_origins: Annotated[list[str], NoDecode] = Field(default=["http://localhost:3000"])

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, v: object) -> object:
        """Accept `a,b,c` from .env as well as a real JSON list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("jwt_secret_key")
    @classmethod
    def _reject_known_placeholders(cls, v: SecretStr) -> SecretStr:
        """Refuse to boot on a value that leaked or ships as an example."""
        banned = {
            "a_very_secret_key_fallback",  # the old hardcoded default
            "your_jwt_secret",  # README example
            "changeme",
        }
        if v.get_secret_value() in banned:
            raise ValueError(
                "JWT_SECRET_KEY is a known placeholder. Generate one: "
                "python -c 'import secrets; print(secrets.token_urlsafe(48))'"
            )
        return v

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_url(self) -> str:
        """Sync URL (psycopg2). Used by Alembic only."""
        if self.database_url:
            return self.database_url
        from urllib.parse import quote_plus

        pw = quote_plus(self.postgres_password.get_secret_value())
        return (
            f"postgresql://{self.postgres_user}:{pw}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_sqlalchemy_url(self) -> str:
        """Async URL (asyncpg). Used by the application and the worker.

        Derived from the sync URL so the two can never point at different
        databases. Railway and docker-compose both hand us a `postgresql://`
        DATABASE_URL, which needs the driver swapped in rather than replaced —
        `postgres://` is also accepted since some providers still emit it.
        """
        url = self.sqlalchemy_url
        for prefix in ("postgresql+psycopg2://", "postgresql://", "postgres://"):
            if url.startswith(prefix):
                return "postgresql+asyncpg://" + url[len(prefix) :]
        return url

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @property
    def is_test(self) -> bool:
        """True under pytest. Sentry and other observability stay off here —
        a flaky network call to an APM must never fail a test run."""
        return self.environment.lower() in {"test", "testing", "ci"}


@lru_cache
def get_settings() -> Settings:
    """Cached accessor. Import this, not the class."""
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
