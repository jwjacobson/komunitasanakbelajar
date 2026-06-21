"""HomePage hero slideshow renders its slides (SPEC §5, DESIGN §7)."""
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.test.utils import WagtailPageTestCase

from core.models import HeroSlide
from core.tests.factories import make_site_tree


class HeroSlidesRenderTest(WagtailPageTestCase):
    def setUp(self):
        self.tree = make_site_tree()
        self.home = self.tree["home"]

    def _add_slide(self):
        image = Image.objects.create(
            title="Slide", file=get_test_image_file()
        )
        return HeroSlide.objects.create(page=self.home, image=image)

    def test_slides_render_in_slideshow(self):
        self._add_slide()
        self._add_slide()
        self._add_slide()

        response = self.client.get(self.home.url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()

        self.assertIn("data-slideshow", html)
        # One slide element per HeroSlide.
        self.assertEqual(html.count("slideshow__slide"), 3)
        # Manual controls are present for the JS to wire up.
        self.assertIn("data-slide-prev", html)
        self.assertIn("data-slide-next", html)
        self.assertIn("data-slide-dots", html)

    def test_no_slideshow_without_slides(self):
        response = self.client.get(self.home.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("data-slideshow", response.content.decode())
