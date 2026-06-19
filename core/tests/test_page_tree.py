"""Page-tree constraint tests (SPEC §4–5)."""
from wagtail.models import Page
from wagtail.test.utils import WagtailPageTestCase

from core.models import (
    AboutPage,
    BlogIndexPage,
    BlogPostPage,
    HomePage,
    SupportPage,
)


class PageTreeRulesTest(WagtailPageTestCase):
    def test_home_allowed_subpage_types(self):
        self.assertAllowedSubpageTypes(
            HomePage, {AboutPage, BlogIndexPage, SupportPage}
        )

    def test_home_allowed_parent_types(self):
        self.assertAllowedParentPageTypes(HomePage, {Page})

    def test_about_is_leaf_under_home(self):
        self.assertAllowedParentPageTypes(AboutPage, {HomePage})
        self.assertAllowedSubpageTypes(AboutPage, set())

    def test_support_is_leaf_under_home(self):
        self.assertAllowedParentPageTypes(SupportPage, {HomePage})
        self.assertAllowedSubpageTypes(SupportPage, set())

    def test_blog_index_under_home_holds_posts(self):
        self.assertAllowedParentPageTypes(BlogIndexPage, {HomePage})
        self.assertAllowedSubpageTypes(BlogIndexPage, {BlogPostPage})

    def test_blog_post_is_leaf_under_index(self):
        self.assertAllowedParentPageTypes(BlogPostPage, {BlogIndexPage})
        self.assertAllowedSubpageTypes(BlogPostPage, set())

    def test_can_create_structural_pages_under_home(self):
        self.assertCanCreateAt(HomePage, AboutPage)
        self.assertCanCreateAt(HomePage, BlogIndexPage)
        self.assertCanCreateAt(HomePage, SupportPage)

    def test_cannot_create_structural_pages_at_root(self):
        self.assertCanCreateAt(Page, HomePage)
        self.assertCanNotCreateAt(Page, AboutPage)
        self.assertCanNotCreateAt(Page, BlogPostPage)

    def test_blog_post_only_under_index(self):
        self.assertCanCreateAt(BlogIndexPage, BlogPostPage)
        self.assertCanNotCreateAt(HomePage, BlogPostPage)
        self.assertCanNotCreateAt(BlogIndexPage, AboutPage)
