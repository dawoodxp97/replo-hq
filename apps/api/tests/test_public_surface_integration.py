"""Integration tests for the public surface (Phase 5) — real Postgres.

Service-level, like the rest of the integration suite: these check what the
site's `/t/[slug]` and `/explore` pages will consume.
"""

import uuid

import pytest

from app.core.exceptions import NotFoundError
from app.core.pagination import PageParams
from app.models.enums import RepositoryStatus, TutorialVisibility
from app.models.orchestration import TutorialInstance
from app.models.repositories import Repository
from app.models.tutorials import Tutorial
from app.models.user import User
from app.services import tutorial as tutorial_service

pytestmark = pytest.mark.integration


async def _seed_tutorial(db, *, title, visibility, slug, language=None, published=True):
    user = User(email=f"{uuid.uuid4().hex[:10]}@example.com")
    db.add(user)
    await db.flush()

    repo = Repository(
        user_id=user.user_id,
        github_url=f"https://github.com/{uuid.uuid4().hex[:8]}/repo",
        name=title.split()[0],
        status=RepositoryStatus.COMPLETED,
        language=language,
    )
    db.add(repo)
    await db.flush()

    tutorial = Tutorial(
        repo_id=repo.repo_id,
        title=title,
        visibility=visibility,
        slug=slug,
    )
    if published and visibility == TutorialVisibility.PUBLIC:
        from datetime import UTC, datetime

        tutorial.published_at = datetime.now(UTC)
    db.add(tutorial)
    await db.commit()
    await db.refresh(tutorial)
    return tutorial


class TestSlugLookup:
    async def test_public_slug_resolves(self, db):
        created = await _seed_tutorial(
            db,
            title="Public Tutorial",
            visibility=TutorialVisibility.PUBLIC,
            slug="public-tutorial",
        )
        response = await tutorial_service.get_public_tutorial_by_slug(db, "public-tutorial")
        assert response.tutorial_id == created.tutorial_id
        assert response.visibility == TutorialVisibility.PUBLIC

    async def test_private_slug_is_a_plain_404(self, db):
        """404, not 403: confirming a private tutorial's slug exists must not
        be possible from the outside."""
        await _seed_tutorial(
            db, title="Hidden", visibility=TutorialVisibility.PRIVATE, slug="hidden-one"
        )
        with pytest.raises(NotFoundError):
            await tutorial_service.get_public_tutorial_by_slug(db, "hidden-one")

    async def test_unlisted_slug_is_not_in_discovery(self, db):
        """Unlisted is readable-by-link via /{id}, but a slug is a discovery
        surface and unlisted content deliberately stays out of those."""
        await _seed_tutorial(
            db, title="Quiet", visibility=TutorialVisibility.UNLISTED, slug="quiet-one"
        )
        with pytest.raises(NotFoundError):
            await tutorial_service.get_public_tutorial_by_slug(db, "quiet-one")

    async def test_unknown_slug_is_404(self, db):
        with pytest.raises(NotFoundError):
            await tutorial_service.get_public_tutorial_by_slug(db, "never-existed")


class TestExplore:
    async def test_only_public_tutorials_listed(self, db):
        public = await _seed_tutorial(
            db, title="Public A", visibility=TutorialVisibility.PUBLIC, slug="explore-a"
        )
        await _seed_tutorial(
            db, title="Private B", visibility=TutorialVisibility.PRIVATE, slug=None, published=False
        )
        await _seed_tutorial(
            db,
            title="Unlisted C",
            visibility=TutorialVisibility.UNLISTED,
            slug=None,
            published=False,
        )

        items, total = await tutorial_service.list_public_tutorials(
            db, PageParams(limit=10, offset=0)
        )
        assert total == 1
        assert items[0].tutorial_id == public.tutorial_id

    async def test_language_filter_is_case_insensitive(self, db):
        await _seed_tutorial(
            db,
            title="Python Tutorial",
            visibility=TutorialVisibility.PUBLIC,
            slug="explore-python",
            language="python",
        )
        await _seed_tutorial(
            db,
            title="Rust Tutorial",
            visibility=TutorialVisibility.PUBLIC,
            slug="explore-rust",
            language="rust",
        )

        items, total = await tutorial_service.list_public_tutorials(
            db, PageParams(limit=10, offset=0), language="Python"
        )
        assert total == 1
        assert items[0].language == "python"

    async def test_unknown_language_yields_empty_page(self, db):
        items, total = await tutorial_service.list_public_tutorials(
            db, PageParams(limit=10, offset=0), language="cobol"
        )
        assert items == []
        assert total == 0

    async def test_pagination_envelope(self, db):
        for i in range(3):
            await _seed_tutorial(
                db,
                title=f"Page Test {i}",
                visibility=TutorialVisibility.PUBLIC,
                slug=f"explore-page-{i}",
            )

        items, total = await tutorial_service.list_public_tutorials(
            db, PageParams(limit=2, offset=0)
        )
        assert total == 3
        assert len(items) == 2
        assert items[0].module_count == 0  # the per-row correlated count works

        second, _ = await tutorial_service.list_public_tutorials(db, PageParams(limit=2, offset=2))
        assert len(second) == 1


class TestStreamTicketInStatus:
    async def test_status_issues_stream_ticket(self, db, monkeypatch):
        """The status payload must carry a ticket bound to this instance and
        user, decodable by the stream endpoint."""
        from app.core import security

        user = User(email=f"{uuid.uuid4().hex[:10]}@example.com")
        db.add(user)
        await db.flush()
        instance = TutorialInstance(user_id=user.user_id, repo_url="https://github.com/a/b")
        db.add(instance)
        await db.commit()
        await db.refresh(instance)

        status = await tutorial_service.get_generation_status(db, instance.id, user.user_id)
        ticket = status["stream_ticket"]
        data = security.decode_stream_ticket(ticket)
        assert data.instance_id == str(instance.id)
        assert data.user_id == str(user.user_id)
