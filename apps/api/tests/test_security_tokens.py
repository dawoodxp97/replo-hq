"""Unit tests for auth primitives: stream tickets, OAuth state, redaction."""

from app.core import security
from app.core.logging import redact


class TestStreamTickets:
    def test_roundtrip(self):
        ticket = security.create_stream_ticket("11111111-1111-1111-1111-111111111111", "u-1")
        data = security.decode_stream_ticket(ticket)
        assert data.instance_id == "11111111-1111-1111-1111-111111111111"
        assert data.user_id == "u-1"

    def test_expired_ticket_is_rejected(self):
        from datetime import timedelta

        ticket = security._encode(
            {"instance_id": "i", "user_id": "u"}, security.STREAM_TICKET_TYPE, timedelta(seconds=-1)
        )
        assert security.decode_stream_ticket(ticket) is None

    def test_tampered_ticket_is_rejected(self):
        ticket = security.create_stream_ticket("i", "u")
        assert security.decode_stream_ticket(ticket + "x") is None

    def test_ticket_is_not_a_session_token(self):
        # Type isolation in both directions: a stream ticket must never be
        # accepted as an access token, and an access token never as a ticket.
        ticket = security.create_stream_ticket("i", "u")
        assert security.decode_access_token(ticket) is None

        access = security.create_access_token(data={"sub": "a@b.c"})
        assert security.decode_stream_ticket(access) is None

    def test_missing_claims_rejected(self):
        from datetime import timedelta

        malformed = security._encode({}, security.STREAM_TICKET_TYPE, timedelta(minutes=1))
        assert security.decode_stream_ticket(malformed) is None


class TestOAuthState:
    def test_roundtrip_same_provider(self):
        state = security.create_oauth_state("github")
        assert security.decode_oauth_state(state, "github") is True

    def test_state_binds_to_provider(self):
        # A state minted for GitHub must not complete a Google flow: that is
        # the CSRF protection, so this is a security property, not a nicety.
        state = security.create_oauth_state("github")
        assert security.decode_oauth_state(state, "google") is False

    def test_forged_state_rejected(self):
        assert security.decode_oauth_state("not-a-jwt", "github") is False


class TestRedaction:
    def test_oauth_code_is_redacted(self):
        line = "callback GET /api/user/oauth/github/callback?code=abc123defghijklm&state=xyz"
        assert "abc123defghijklm" not in redact(line)

    def test_oauth_state_is_redacted(self):
        line = "state=eyJhbGciOiJIUzI1NiJ9.eyJwcm92aWRlciI6ImdpdGh1YiJ9.sigvalue1234"
        assert "eyJhbGciOiJIUzI1NiJ9" not in redact(line)

    def test_jwt_shape_is_redacted(self):
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3j"
        assert jwt not in redact(f"token={jwt}")

    def test_provider_access_token_is_redacted(self):
        # GitHub access tokens start gho_; the pattern predates OAuth, but OAuth
        # is what makes it load-bearing.
        assert "gho_" not in redact("gho_16C7e42F292c6912E7710c838347Ae178B4a")

    def test_benign_text_untouched(self):
        line = "Step analyze_repo completed in 1200ms"
        assert redact(line) == line
