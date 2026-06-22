"""BlogPostPage excerpt auto-generation (SPEC §5).

A blank excerpt derives from the first ~40 words of the body, formatting
stripped; a hand-written excerpt is respected as a manual override.
"""
from wagtail.rich_text import RichText
from wagtail.test.utils import WagtailPageTestCase

from core.models import EXCERPT_WORD_COUNT
from core.tests.factories import add_post, make_site_tree


def _paragraph(text):
    return [("paragraph", RichText("<p>{}</p>".format(text)))]


class ExcerptTest(WagtailPageTestCase):
    def setUp(self):
        self.tree = make_site_tree()
        self.blog_index = self.tree["blog_index"]

    def test_blank_excerpt_derives_from_body(self):
        post = add_post(
            self.blog_index,
            "Auto",
            "2024-05-01",
            body=_paragraph("Anak-anak belajar di rumah belajar Cakung."),
        )
        self.assertEqual(
            post.get_excerpt(),
            "Anak-anak belajar di rumah belajar Cakung.",
        )

    def test_long_body_truncated_to_word_count_with_ellipsis(self):
        words = " ".join("kata{}".format(i) for i in range(60))
        post = add_post(
            self.blog_index, "Long", "2024-05-02", body=_paragraph(words)
        )
        excerpt = post.get_excerpt()
        self.assertTrue(excerpt.endswith("…"))
        # 40 words plus the trailing ellipsis glued to the 40th.
        self.assertEqual(len(excerpt.split()), EXCERPT_WORD_COUNT)

    def test_short_body_has_no_ellipsis(self):
        post = add_post(
            self.blog_index, "Short", "2024-05-03", body=_paragraph("Tiga kata saja")
        )
        self.assertEqual(post.get_excerpt(), "Tiga kata saja")

    def test_html_formatting_is_stripped(self):
        post = add_post(
            self.blog_index,
            "Formatted",
            "2024-05-04",
            body=[("paragraph", RichText("<p>Halo <b>dunia</b> kecil</p>"))],
        )
        self.assertEqual(post.get_excerpt(), "Halo dunia kecil")

    def test_manual_excerpt_overrides_body(self):
        post = add_post(
            self.blog_index,
            "Override",
            "2024-05-05",
            body=_paragraph("Teks body yang panjang dan berbeda."),
            excerpt="Ringkasan tulisan tangan.",
        )
        self.assertEqual(post.get_excerpt(), "Ringkasan tulisan tangan.")

    def test_heading_and_quote_blocks_contribute_text(self):
        post = add_post(
            self.blog_index,
            "Mixed",
            "2024-05-06",
            body=[
                ("heading", "Kegiatan kami"),
                ("paragraph", RichText("<p>Belajar bersama.</p>")),
            ],
        )
        self.assertEqual(post.get_excerpt(), "Kegiatan kami Belajar bersama.")

    def test_empty_body_yields_empty_excerpt(self):
        post = add_post(self.blog_index, "Empty", "2024-05-07")
        self.assertEqual(post.get_excerpt(), "")
