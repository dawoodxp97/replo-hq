"""Integration tests for the OAuth flow (D10) — real Postgres via testcontainers.

The provider's HTTP half is stubbed at the adapter boundary; everything under
test is the identity matching/linking logic, which is the part that touches the
database and the part that must never get it wrong.
"""

import uuid
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.core import security
from app.core.exceptions import AuthenticationError
from app.models.enums import OAuthProvider
from app.models.user_oauth import UserOAuthIdentity
from app.services import auth as auth_service
from app.services import oauth as oauth_service
from app.services.oauth import ProviderProfile

pytestmark = pytest.mark.integration

# Not a credential: a throwaway fixture value for a row that lives for one test.
TEST_PASSWORD = "long-enough-test-password"  # noqa: S105


def _stub_github(monkeypatch, profile):
    async def exchange(self, code):
        assert code == "good-code"  # the router passes the query param through
        return profile

    monkeypatch.setattr(oauth_service._GitHubAdapter, "exchange_code", exchange)


def _github_callback(db, monkeypatch, profile):
    _stub_github(monkeypatch, profile)
    return oauth_service.handle_callback(
        db, OAuthProvider.GITHUB, "good-code", security.create_oauth_state("github")
    )


class TestNewAccount:
    async def test_first_login_creates_passwordless_user(self, db, monkeypatch):
        user = await _github_callback(
            db,
            monkeypatch,
            ProviderProfile(subject="98765", email="ada@example.com", name="Ada Lovelace"),
        )

        assert user.email == "ada@example.com"
        # Passwordless by design: NULL hashed_password is "no credential", not a
        # bypass — authenticate() refuses login for such accounts.
        assert user.hashed_password is None
        assert user.first_name == "Ada"
        assert user.last_name == "Lovelace"

        identities = (await db.execute(select(UserOAuthIdentity))).scalars().all()
        assert len(identities) == 1
        assert identities[0].provider == "github"
        assert identities[0].provider_user_id == "98765"

    async def test_passwordless_account_cannot_password_login(self, db, monkeypatch):
        user = await _github_callback(
            db,
            monkeypatch,
            ProviderProfile(subject="1", email="no-pass@example.com", name="N P"),
        )
        with pytest.raises(AuthenticationError):
            await auth_service.authenticate(db, user.email, "whatever-password")


class TestIdentityMatching:
    async def test_same_provider_subject_returns_same_user(self, db, monkeypatch):
        profile = ProviderProfile(subject="98765", email="ada@example.com", name="Ada")
        first = await _github_callback(db, monkeypatch, profile)
        second = await _github_callback(db, monkeypatch, profile)

        assert first.user_id == second.user_id
        identities = (await db.execute(select(UserOAuthIdentity))).scalars().all()
        assert len(identities) == 1  # not a second row for the same subject

    async def test_matching_email_links_to_existing_password_account(self, db, monkeypatch):
        """A user who signed up with a password can later sign in with the
        provider whose verified email matches — one account, two doors."""
        email = f"{uuid.uuid4().hex[:10]}@example.com"
        from app.schemas.user import UserCreate

        existing = await auth_service.create_user(
            db, UserCreate(email=email, first_name="Pat", password=TEST_PASSWORD)
        )

        async def exchange(self, code):
            return ProviderProfile(subject="42", email=email, name="Pat Doe")

        monkeypatch.setattr(oauth_service._GoogleAdapter, "exchange_code", exchange)
        user = await oauth_service.handle_callback(
            db, OAuthProvider.GOOGLE, "good-code", security.create_oauth_state("google")
        )

        assert user.user_id == existing.user_id
        assert user.hashed_password is not None  # their password account, untouched
        identity = (await db.execute(select(UserOAuthIdentity))).scalars().one()
        assert identity.provider == "google"
        assert identity.user_id == user.user_id


class TestStateValidation:
    async def test_forged_state_is_rejected(self, db, monkeypatch):
        with pytest.raises(AuthenticationError):
            await _github_callback_with_state(db, monkeypatch, "forged")

    async def test_expired_state_is_rejected(self, db, monkeypatch):
        expired = security._encode(
            {"provider": "github"}, security.OAUTH_STATE_TYPE, timedelta(seconds=-1)
        )
        with pytest.raises(AuthenticationError):
            await _github_callback_with_state(db, monkeypatch, expired)

    async def test_state_from_other_provider_is_rejected(self, db, monkeypatch):
        state = security.create_oauth_state("google")
        with pytest.raises(AuthenticationError):
            await _github_callback_with_state(db, monkeypatch, state)


async def _github_callback_with_state(db, monkeypatch, state):
    _stub_github(monkeypatch, ProviderProfile(subject="98765", email="ada@example.com", name="Ada"))
    return await oauth_service.handle_callback(db, OAuthProvider.GITHUB, "good-code", state)


class TestTokenIssuance:
    async def test_oauth_issues_same_token_pair_as_password_login(self, db, monkeypatch):
        """The property D10 exists for: providers are interchangeable via one
        session module. Both flows call issue_tokens."""
        user = await _github_callback(
            db,
            monkeypatch,
            ProviderProfile(subject="7", email="pair@example.com", name="P"),
        )
        oauth_tokens = auth_service.issue_tokens(user)

        assert set(oauth_tokens.model_dump()) == {"access_token", "refresh_token", "token_type"}
        assert oauth_tokens.token_type == "bearer"  # noqa: S105 - OAuth field name

        # The access token decodes through the same session machinery.
        data = security.decode_access_token(oauth_tokens.access_token)
        assert data.email == "pair@example.com"
