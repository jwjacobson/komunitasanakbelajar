"""
Importer integration tests (SPEC §13, task §7): idempotent upsert and a real
render smoke test. The network (feed + image downloads) is stubbed; the feed
fixture is a real captured 2-entry page.
"""
import io
import json
from pathlib import Path

import pytest
from PIL import Image as PILImage
from wagtail.images import get_image_model

from core.management.commands import import_blogspot
from core.models import BlogPostPage
from core.tests.factories import make_site_tree

FIXTURES = Path(__file__).parent / "fixtures" / "blogspot"


def _jpeg_bytes():
    buf = io.BytesIO()
    PILImage.new("RGB", (12, 12), (94, 140, 78)).save(buf, "JPEG")
    return buf.getvalue()


@pytest.fixture
def stub_network(monkeypatch):
    """Serve the feed fixture for feed requests and a JPEG for image requests."""
    feed_page = json.loads((FIXTURES / "feed_page.json").read_text("utf-8"))
    jpeg = _jpeg_bytes()
    calls = {"feed": 0, "image": 0}

    def fake_request(self, url, *, params=None, binary=False):
        if binary:
            calls["image"] += 1
            return jpeg
        calls["feed"] += 1
        return feed_page

    monkeypatch.setattr(import_blogspot.Command, "_request", fake_request)
    # Don't actually sleep during the throttle waits.
    monkeypatch.setattr(import_blogspot.time, "sleep", lambda *a, **k: None)
    return calls


@pytest.fixture
def tree(db):
    return make_site_tree()


def _run(**opts):
    from django.core.management import call_command

    call_command("import_blogspot", **opts)


def test_imports_two_posts(tree, stub_network):
    _run(limit=2, throttle=0)
    assert BlogPostPage.objects.count() == 2
    posts = BlogPostPage.objects.all()
    # Published live with original dates, body populated, key set.
    for post in posts:
        assert post.live
        assert post.blogger_post_id
        assert len(post.body) > 0
        assert post.first_published_at.year == 2024


def test_idempotent_reimport(tree, stub_network):
    _run(limit=2, throttle=0)
    image_count = get_image_model().objects.count()
    _run(limit=2, throttle=0)
    # Upsert on blogger_post_id: still two posts, not four.
    assert BlogPostPage.objects.count() == 2
    # Images deduped by source URL: no new images on the second run.
    assert get_image_model().objects.count() == image_count


def test_slug_from_blogspot_path(tree, stub_network):
    _run(limit=2, throttle=0)
    slugs = set(BlogPostPage.objects.values_list("slug", flat=True))
    assert "activities-during-school-holiday" in slugs


def test_feed_image_set(tree, stub_network):
    _run(limit=2, throttle=0)
    for post in BlogPostPage.objects.all():
        assert post.feed_image_id is not None


@pytest.mark.django_db
def test_imported_post_renders_200(tree, stub_network, client):
    _run(limit=2, throttle=0)
    post = BlogPostPage.objects.first()
    response = client.get(post.url)
    assert response.status_code == 200
