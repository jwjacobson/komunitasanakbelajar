"""BlogIndexPage journal-list rendering (SPEC §5, DESIGN §5/§6).

Covers the year markers, the live report count + founding year in the header,
and that pagination chrome appears once the list overflows one page.
"""
from wagtail.test.utils import WagtailPageTestCase

from core.models import BLOG_POSTS_PER_PAGE
from core.tests.factories import add_post, make_site_tree


class BlogIndexRenderTest(WagtailPageTestCase):
    def setUp(self):
        self.tree = make_site_tree()
        self.blog_index = self.tree["blog_index"]

    def test_year_markers_group_entries(self):
        add_post(self.blog_index, "Laporan A", "2024-08-18")
        add_post(self.blog_index, "Laporan B", "2024-07-12")
        add_post(self.blog_index, "Laporan C", "2023-06-01")

        response = self.client.get(self.blog_index.url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()

        # Both year groups appear as journal markers.
        self.assertIn("journal__year-label", html)
        self.assertIn(">2024<", html)
        self.assertIn(">2023<", html)
        # Exactly two year markers for two distinct years.
        self.assertEqual(html.count("journal__year-label"), 2)

    def test_live_count_and_founding_year_in_header(self):
        add_post(self.blog_index, "Laporan A", "2024-08-18")
        add_post(self.blog_index, "Laporan B", "2011-03-02")

        response = self.client.get(self.blog_index.url)
        html = response.content.decode()
        self.assertIn("2 laporan", html)
        self.assertIn("sejak 2011", html)

    def test_unpublished_posts_excluded_from_count(self):
        add_post(self.blog_index, "Published", "2024-01-01")
        add_post(self.blog_index, "Draft", "2024-02-01", live=False)

        response = self.client.get(self.blog_index.url)
        self.assertIn("1 laporan", response.content.decode())

    def test_pagination_appears_when_overflowing(self):
        for i in range(BLOG_POSTS_PER_PAGE + 1):
            add_post(self.blog_index, "Laporan {:02d}".format(i), "2024-01-{:02d}".format(i + 1))

        response = self.client.get(self.blog_index.url)
        html = response.content.decode()
        self.assertIn("pagination", html)
        self.assertIn("?page=2", html)

    def test_no_pagination_for_single_page(self):
        add_post(self.blog_index, "Solo", "2024-01-01")
        response = self.client.get(self.blog_index.url)
        self.assertNotIn('aria-label="Halaman laporan"', response.content.decode())
