"""BlogIndexPage pagination (SPEC §5)."""
from django.test import RequestFactory
from wagtail.test.utils import WagtailPageTestCase

from core.models import BLOG_POSTS_PER_PAGE
from core.tests.factories import add_post, make_site_tree


class BlogPaginationTest(WagtailPageTestCase):
    def setUp(self):
        self.tree = make_site_tree()
        self.blog_index = self.tree["blog_index"]
        self.factory = RequestFactory()
        # One more than a full page so there are exactly two pages.
        self.total = BLOG_POSTS_PER_PAGE + 1
        for i in range(self.total):
            add_post(
                self.blog_index,
                f"Laporan {i:02d}",
                f"2025-01-{i + 1:02d}",
            )

    def _posts_for(self, query=""):
        request = self.factory.get(f"/{query}")
        return self.blog_index.get_context(request)["posts"]

    def test_first_page_is_full(self):
        posts = self._posts_for()
        self.assertEqual(posts.number, 1)
        self.assertEqual(len(posts), BLOG_POSTS_PER_PAGE)
        self.assertTrue(posts.has_next())
        self.assertFalse(posts.has_previous())

    def test_second_page_holds_remainder(self):
        posts = self._posts_for("?page=2")
        self.assertEqual(posts.number, 2)
        self.assertEqual(len(posts), self.total - BLOG_POSTS_PER_PAGE)
        self.assertFalse(posts.has_next())

    def test_posts_ordered_date_desc(self):
        posts = self._posts_for()
        dates = [p.date for p in posts]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_invalid_page_falls_back_to_first(self):
        posts = self._posts_for("?page=not-a-number")
        self.assertEqual(posts.number, 1)

    def test_out_of_range_page_falls_back_to_last(self):
        posts = self._posts_for("?page=999")
        self.assertEqual(posts.number, posts.paginator.num_pages)
