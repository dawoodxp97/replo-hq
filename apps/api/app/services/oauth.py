"""OAuth login (D10): GitHub and Google.

Design, in three lines:

1. `authorize` returns the provider's consent URL with a signed `state` JWT.
2. The provider calls back with `code` + `state`; the state is verified
   cryptographically, so no server-side session store is needed and a forged
   callback fails.
3. The identity is matched or created, and the *same* `issue_tokens` call that
   password login uses mints the session — one session model, N providers.

Provider specifics live in the small adapter classes at the bottom; the service
functions above them are provider-agnostic. Adding a provider is one adapter
plus one Settings pair, nothing else.

Security notes:

- **Only verified emails are linked.** GitHub can report an unverified address;
  linking an account to it would let whoever controls that address take over the
  account. Google addresses are verified by construction.
- **Identity match prefers the provider subject id**, not the email — emails
  change, `sub`/numeric ids do not.
- The access code and provider tokens are never logged and never stored; the
  provider token is exchanged, used once, and dropped.
"""

import logging
from dataclasses import dataclass
from urllib.parse import urlencode

import aiohttp
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core import security
from ..core.config import settings
from ..core.exceptions import AuthenticationError, NotFoundError
from ..models.enums import OAuthProvider
from ..models.user import User
from ..models.user_oauth import UserOAuthIdentity
from . import auth as auth_service

logger = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=15)


class ProviderNotConfiguredError(NotFoundError):
    """The provider is known but has no client credentials configured."""

    default_message = "This sign-in provider is not available."


@dataclass(frozen=True)
class ProviderProfile:
    """What we keep from the provider after a successful exchange."""

    subject: str
    email: str | None
    name: str | None


def callback_path(provider: OAuthProvider) -> str:
    """The redirect URI the provider is told to call back to."""
    return (
        f"{settings.oauth_callback_base_url.rstrip('/')}/api/user/oauth/{provider.value}/callback"
    )


# --- Service ----------------------------------------------------------------


def get_authorization_url(provider: OAuthProvider) -> str:
    """The consent-screen URL the frontend sends the browser to.

    `state` is a signed JWT (see core.security.create_oauth_state) rather than a
    random nonce: it proves the callback belongs to a flow we started and binds
    it to this provider, without a server-side store. If a nonce were stored in
    Redis instead, a Redis outage would disable login.
    """
    adapter = _adapter(provider)

    state = security.create_oauth_state(provider.value)
    return adapter.authorization_url(state, callback_path(provider))


async def handle_callback(
    db: AsyncSession,
    provider: OAuthProvider,
    code: str,
    state: str,
) -> User:
    """Exchange `code` for a profile and return the user it belongs to.

    Raises `AuthenticationError` on a bad state, bad code or provider error —
    the caller cannot distinguish "forged" from "expired", which is the point.
    """
    if not security.decode_oauth_state(state, provider.value):
        raise AuthenticationError("Invalid OAuth state.")

    adapter = _adapter(provider)
    profile = await adapter.exchange_code(code)
    if profile is None:
        raise AuthenticationError("Could not sign in with this provider.")

    identity = (
        await db.execute(
            select(UserOAuthIdentity).where(
                UserOAuthIdentity.provider == provider.value,
                UserOAuthIdentity.provider_user_id == profile.subject,
            )
        )
    ).scalar_one_or_none()

    if identity is not None:
        user = (
            await db.execute(select(User).where(User.user_id == identity.user_id))
        ).scalar_one_or_none()
        if user is None or not user.is_active:
            raise AuthenticationError("This account has been deactivated.")
        # Refresh the email snapshot; the subject id is authoritative.
        if profile.email and profile.email != identity.provider_email:
            identity.provider_email = profile.email
            await db.commit()
        return user

    user = await _resolve_user_for_linking(db, profile)
    db.add(
        UserOAuthIdentity(
            user_id=user.user_id,
            provider=provider.value,
            provider_user_id=profile.subject,
            provider_email=profile.email,
        )
    )
    await db.commit()
    await db.refresh(user)
    return user


async def _resolve_user_for_linking(db: AsyncSession, profile: ProviderProfile) -> User:
    """Find the account this first-time identity belongs to, or create one.

    Linking by verified email means a user who signed up with a password can
    later sign in with the matching GitHub/Google account — one account, three
    doors. Creating a second account for the same human would be the alternative,
    and it is worse in every way that matters (split tutorials, split progress).
    """
    user: User | None = None
    if profile.email:
        user = (
            await db.execute(select(User).where(User.email == profile.email.lower()))
        ).scalar_one_or_none()

    if user is None:
        if not profile.email:
            # No verified email to hang an account on. Creating an account keyed
            # by a provider subject would strand it — the rest of the product
            # (password reset, notifications, everything) is email-addressed.
            raise AuthenticationError(
                "Your provider account has no verified email address to sign in with."
            )
        first, _, last = (profile.name or "").partition(" ")
        user = await auth_service.create_oauth_user(
            db,
            email=profile.email.lower(),
            first_name=first or profile.name or profile.subject,
            last_name=last or None,
        )
    return user


# --- Provider adapters ------------------------------------------------------


class _OAuthAdapter:
    """One provider's URLs and response shapes. Subclasses are data + two
    small methods; the flow above them never branches on provider."""

    authorize_endpoint: str = ""
    token_endpoint: str = ""
    scope: str = ""
    # Extra query params each provider mandates (Google requires
    # response_type=code; GitHub defaults to it).
    extra_authorize_params: dict[str, str] = {}
    client_id: str | None = None
    client_secret = None

    def _credentials(self) -> tuple[str, str]:
        if not self.client_id or not self.client_secret:
            raise ProviderNotConfiguredError(
                "This sign-in provider is not configured on the server."
            )
        return self.client_id, self.client_secret.get_secret_value()

    def authorization_url(self, state: str, redirect_uri: str) -> str:
        client_id, _ = self._credentials()
        params = urlencode(
            {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": self.scope,
                "state": state,
                **self.extra_authorize_params,
            }
        )
        return f"{self.authorize_endpoint}?{params}"

    async def exchange_code(self, code: str) -> ProviderProfile | None:
        """Token exchange + profile fetch. Returns None on any provider failure —
        the caller renders one generic error either way."""
        client_id, client_secret = self._credentials()
        try:
            async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
                async with session.post(
                    self.token_endpoint,
                    data={
                        "code": code,
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uri": callback_path(self.provider),
                        "grant_type": "authorization_code",
                    },
                    headers={"Accept": "application/json"},
                ) as resp:
                    if resp.status != 200:
                        logger.warning("OAuth token exchange failed: %s", resp.status)
                        return None
                    token = (await resp.json()).get("access_token")
                if not token:
                    return None
                return await self._fetch_profile(session, token)
        except aiohttp.ClientError:
            logger.exception("OAuth provider unreachable")
            return None

    async def _fetch_profile(
        self, session: aiohttp.ClientSession, access_token: str
    ) -> ProviderProfile | None:
        raise NotImplementedError


class _GitHubAdapter(_OAuthAdapter):
    provider = OAuthProvider.GITHUB

    authorize_endpoint = "https://github.com/login/oauth/authorize"
    token_endpoint = "https://github.com/login/oauth/access_token"  # noqa: S105 - a URL, not a credential
    # `user:email` is required to read the (possibly private) verified address.
    scope = "read:user user:email"

    client_id = settings.github_client_id
    client_secret = settings.github_client_secret

    async def _fetch_profile(self, session, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        async with session.get("https://api.github.com/user", headers=headers) as resp:
            if resp.status != 200:
                return None
            body = await resp.json()

        email = body.get("email")
        if not email:
            # Public email not set. Fall back to the *verified* primary address.
            async with session.get("https://api.github.com/user/emails", headers=headers) as resp:
                if resp.status == 200:
                    verified = [
                        e for e in await resp.json() if e.get("verified") and e.get("primary")
                    ]
                    email = verified[0]["email"] if verified else None

        return ProviderProfile(
            subject=str(body["id"]),
            email=email.lower() if email else None,
            name=body.get("name") or body.get("login"),
        )


class _GoogleAdapter(_OAuthAdapter):
    provider = OAuthProvider.GOOGLE

    authorize_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
    token_endpoint = "https://oauth2.googleapis.com/token"  # noqa: S105 - a URL, not a credential
    scope = "openid email profile"
    extra_authorize_params = {"response_type": "code"}

    client_id = settings.google_client_id
    client_secret = settings.google_client_secret

    async def _fetch_profile(self, session, access_token):
        async with session.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        ) as resp:
            if resp.status != 200:
                return None
            body = await resp.json()

        return ProviderProfile(
            subject=str(body["sub"]),
            # Google only issues access to verified addresses.
            email=body.get("email", "").lower() or None,
            name=body.get("name"),
        )


_ADAPTERS: dict[OAuthProvider, _OAuthAdapter] = {
    OAuthProvider.GITHUB: _GitHubAdapter(),
    OAuthProvider.GOOGLE: _GoogleAdapter(),
}


def _adapter(provider: OAuthProvider) -> _OAuthAdapter:
    adapter = _ADAPTERS.get(provider)
    if adapter is None:
        raise NotFoundError("Unknown OAuth provider.")
    return adapter
