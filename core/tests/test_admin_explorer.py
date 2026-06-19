"""
The Pages explorer shows our HomePage as root, with Tentang / Laporan / Dukung
as its children and as the only creatable child types.
"""
from django.urls import reverse
from wagtail.test.utils import WagtailPageTestCase

from core.models import HomePage
from core.tests.factories import make_site_tree


class AdminExplorerTest(WagtailPageTestCase):
    def setUp(self):
        self.tree = make_site_tree()
        self.login()  # superuser

    def test_explorer_root_is_our_homepage(self):
        response = self.client.get(reverse("wagtailadmin_explore_root"))
        self.assertEqual(response.status_code, 200)
        # The root listing shows the single HomePage ("Beranda").
        self.assertContains(response, "Beranda")

    def test_home_children_are_the_three_structural_pages(self):
        response = self.client.get(
            reverse("wagtailadmin_explore", args=[self.tree["home"].id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tentang")
        self.assertContains(response, "Laporan")
        self.assertContains(response, "Dukung")

    def test_add_subpage_menu_offers_only_allowed_types(self):
        # The three structural pages are max_count=1 singletons, so once they
        # exist they drop out of the add menu. Remove them to see the full set
        # of allowed child types the explorer would offer on a fresh Home.
        for key in ("about", "blog_index", "support"):
            self.tree[key].delete()

        response = self.client.get(
            reverse("wagtailadmin_pages:add_subpage", args=[self.tree["home"].id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "About page")
        self.assertContains(response, "Blog index page")
        self.assertContains(response, "Support page")
        # Blog posts are only creatable under the blog index, never under Home.
        self.assertNotContains(response, "Blog post page")

    def test_single_homepage_in_tree(self):
        self.assertEqual(HomePage.objects.count(), 1)
