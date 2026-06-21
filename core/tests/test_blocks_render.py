"""All six StreamField block types render with their DESIGN §5 markup."""
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.rich_text import RichText
from wagtail.test.utils import WagtailPageTestCase

from core.tests.factories import add_post, make_site_tree


def _image(title):
    img = Image.objects.create(title=title, file=get_test_image_file())
    img.contextual_alt_text = title
    img.decorative = False
    return img


class BlocksRenderTest(WagtailPageTestCase):
    def setUp(self):
        self.tree = make_site_tree()
        self.post = add_post(
            self.tree["blog_index"],
            "Semua blok",
            "2024-09-01",
            body=[
                ("heading", "Kegiatan kami"),
                ("paragraph", RichText("<p>Anak-anak belajar bersama.</p>")),
                ("image", _image("Foto kegiatan")),
                ("gallery", [_image("Galeri 1"), _image("Galeri 2")]),
                ("quote", {"text": "Setiap anak berhak belajar.", "attribution": "Debby"}),
                (
                    "callout",
                    {
                        "heading": "Kebutuhan bulan ini",
                        "body": RichText("<p>Dukungan rutin sangat membantu.</p>"),
                    },
                ),
            ],
        )

    def test_all_block_types_render(self):
        response = self.client.get(self.post.url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()

        self.assertIn("block-heading", html)
        self.assertIn("block-paragraph", html)
        self.assertIn("block-image", html)
        self.assertIn("block-gallery", html)
        self.assertIn("block-quote", html)
        self.assertIn("block-callout", html)

        # Block content surfaces.
        self.assertIn("Kegiatan kami", html)
        self.assertIn("Setiap anak berhak belajar.", html)
        self.assertIn("Debby", html)
        # Callout's terracotta giving link resolves to the Support page.
        self.assertIn("Dukung kami", html)
        self.assertIn(self.tree["support"].url, html)
