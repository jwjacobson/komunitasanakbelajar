"""Smoke tests: every page type renders HTTP 200 via the placeholder templates."""
from wagtail.test.utils import WagtailPageTestCase

from core.tests.factories import add_post, make_site_tree


class PageRenderSmokeTest(WagtailPageTestCase):
    def setUp(self):
        self.tree = make_site_tree()
        self.post = add_post(
            self.tree["blog_index"], "Laporan kegiatan", "2025-05-01"
        )

    def test_home_renders(self):
        self.assertPageIsRenderable(self.tree["home"])

    def test_about_renders(self):
        self.assertPageIsRenderable(self.tree["about"])

    def test_blog_index_renders(self):
        self.assertPageIsRenderable(self.tree["blog_index"])

    def test_support_renders(self):
        self.assertPageIsRenderable(self.tree["support"])

    def test_blog_post_renders(self):
        self.assertPageIsRenderable(self.post)

    def test_home_returns_200_over_http(self):
        response = self.client.get(self.tree["home"].url)
        self.assertEqual(response.status_code, 200)

    def test_blog_post_returns_200_over_http(self):
        response = self.client.get(self.post.url)
        self.assertEqual(response.status_code, 200)
