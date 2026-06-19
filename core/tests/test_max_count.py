"""max_count enforcement on the singleton pages (SPEC §5)."""
from wagtail.models import Page
from wagtail.test.utils import WagtailPageTestCase

from core.models import AboutPage, BlogIndexPage, HomePage, SupportPage
from core.tests.factories import make_site_tree


class SingletonMaxCountTest(WagtailPageTestCase):
    def setUp(self):
        self.tree = make_site_tree()

    def test_only_one_home_allowed(self):
        # One HomePage already exists under root; a second is disallowed.
        root = self.tree["root"]
        self.assertFalse(HomePage.can_create_at(root))

    def test_only_one_about_allowed(self):
        home = self.tree["home"]
        self.assertFalse(AboutPage.can_create_at(home))

    def test_only_one_blog_index_allowed(self):
        home = self.tree["home"]
        self.assertFalse(BlogIndexPage.can_create_at(home))

    def test_only_one_support_allowed(self):
        home = self.tree["home"]
        self.assertFalse(SupportPage.can_create_at(home))

    def test_max_count_is_one(self):
        for model in (HomePage, AboutPage, BlogIndexPage, SupportPage):
            self.assertEqual(model.max_count, 1)
