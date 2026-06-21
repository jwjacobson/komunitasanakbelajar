"""Regression guard: rendered pages must never show literal template-comment
text.

Django's ``{# … #}`` comment syntax is single-line only — a comment whose
delimiters straddle two lines leaks onto the page as literal text. We use
``{% comment %}…{% endcomment %}`` for multi-line comments (see CLAUDE.md); this
test asserts no ``{#`` token survives into the rendered HTML of any page type,
including a body that exercises the callout block template.
"""
from wagtail.rich_text import RichText
from wagtail.test.utils import WagtailPageTestCase

from core.tests.factories import add_post, make_site_tree


class NoLiteralCommentTest(WagtailPageTestCase):
    def setUp(self):
        self.tree = make_site_tree()
        self.post = add_post(
            self.tree["blog_index"], "Laporan kegiatan", "2025-05-01"
        )
        # Exercise the callout block template, which carries a converted comment.
        about = self.tree["about"]
        about.body_id = [
            ("callout", {"heading": "Transparansi", "body": RichText("<p>Dana.</p>")}),
        ]
        about.save_revision().publish()

    def _assert_no_literal_comment(self, page):
        html = self.client.get(page.url).content.decode()
        self.assertNotIn("{#", html)
        self.assertNotIn("#}", html)

    def test_home_has_no_literal_comment(self):
        self._assert_no_literal_comment(self.tree["home"])

    def test_about_has_no_literal_comment(self):
        self._assert_no_literal_comment(self.tree["about"])

    def test_blog_index_has_no_literal_comment(self):
        self._assert_no_literal_comment(self.tree["blog_index"])

    def test_support_has_no_literal_comment(self):
        self._assert_no_literal_comment(self.tree["support"])

    def test_blog_post_has_no_literal_comment(self):
        self._assert_no_literal_comment(self.post)
