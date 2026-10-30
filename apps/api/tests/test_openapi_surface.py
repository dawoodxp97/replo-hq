"""OpenAPI surface tests — the contract web and site consume.

These are the handoff checks: if one of these fails, the generated TS client in
packages/api-client is about to change shape.
"""

from fastapi.testclient import TestClient  # noqa: F401


def _paths():
    from app.main import app

    return app.openapi()["paths"]


def _methods_for(paths, path):
    return {m.upper() for m in paths[path].keys()}


class TestNewRoutes:
    def test_oauth_authorize_and_callback(self):
        paths = _paths()
        assert "/api/user/oauth/{provider}/authorize" in paths
        assert "/api/user/oauth/{provider}/callback" in paths
        assert "GET" in _methods_for(paths, "/api/user/oauth/{provider}/authorize")
        assert "GET" in _methods_for(paths, "/api/user/oauth/{provider}/callback")

    def test_sse_stream_route(self):
        paths = _paths()
        assert "/api/tutorial/{instance_id}/stream" in paths

    def test_public_slug_route(self):
        paths = _paths()
        assert "/api/tutorial/slug/{slug}" in paths

    def test_public_explore_route(self):
        paths = _paths()
        assert "/api/tutorial/explore" in paths
        assert "GET" in _methods_for(paths, "/api/tutorial/explore")

    def test_status_payload_carries_stream_ticket(self):
        from app.schemas.tutorial import StatusResponse

        assert "stream_ticket" in StatusResponse.model_fields

    def test_health_and_ready_split(self):
        paths = _paths()
        assert "/api/health" in paths
        assert "/api/ready" in paths


class TestResponseShapes:
    def test_explore_returns_page_envelope(self):
        # Page[T] envelope: items/total/limit/offset/has_more — apps/site's
        # pagination depends on these exact keys.
        from app.core.pagination import Page
        from app.schemas.tutorial import ExploreTutorialItem

        page = Page[ExploreTutorialItem].build([], 0, type("P", (), {"limit": 20, "offset": 0})())
        dumped = page.model_dump()
        assert set(dumped) == {"items", "total", "limit", "offset", "has_more"}
        assert dumped["has_more"] is False

    def test_token_pair_unchanged(self):
        # OAuth must issue the SAME pair as password login — this shape is
        # frozen by the session module on the frontend.
        from app.schemas.user import Token

        assert set(Token.model_fields) == {"access_token", "refresh_token", "token_type"}
