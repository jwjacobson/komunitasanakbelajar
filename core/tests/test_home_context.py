"""HomePage.get_context — latest 3 published posts, date desc (SPEC §5)."""
from django.test import RequestFactory
from wagtail.test.utils import WagtailPageTestCase

from core.tests.factories import add_post, make_site_tree


class HomeContextTest(WagtailPageTestCase):
    def setUp(self):
        self.tree = make_site_tree()
        self.home = self.tree["home"]
        self.blog_index = self.tree["blog_index"]
        self.request = RequestFactory().get("/")

    def test_latest_posts_limited_to_three_in_date_desc_order(self):
        add_post(self.blog_index, "Oldest", "2025-01-01")
        add_post(self.blog_index, "Older", "2025-02-01")
        add_post(self.blog_index, "Newer", "2025-03-01")
        add_post(self.blog_index, "Newest", "2025-04-01")

        context = self.home.get_context(self.request)
        latest = list(context["latest_posts"])

        self.assertEqual(len(latest), 3)
        self.assertEqual(
            [p.title for p in latest], ["Newest", "Newer", "Older"]
        )

    def test_unpublished_posts_excluded(self):
        add_post(self.blog_index, "Published", "2025-03-01")
        add_post(self.blog_index, "Draft", "2025-04-01", live=False)

        context = self.home.get_context(self.request)
        latest = list(context["latest_posts"])

        self.assertEqual([p.title for p in latest], ["Published"])

    def test_no_posts_yields_empty(self):
        context = self.home.get_context(self.request)
        self.assertEqual(list(context["latest_posts"]), [])
