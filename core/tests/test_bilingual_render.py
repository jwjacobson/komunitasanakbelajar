"""Bilingual pages ship both bodies server-side (SPEC §7, DESIGN §7).

The ID/EN toggle is client-side, so both body_id and body_en must be present in
the rendered HTML of the About and Support pages.
"""
from wagtail.rich_text import RichText
from wagtail.test.utils import WagtailPageTestCase

from core.tests.factories import make_site_tree


def _paragraph(text):
    return [("paragraph", RichText("<p>{}</p>".format(text)))]


class BilingualRenderTest(WagtailPageTestCase):
    def setUp(self):
        self.tree = make_site_tree()

    def test_about_renders_both_bodies(self):
        about = self.tree["about"]
        about.body_id = _paragraph("Teks bahasa Indonesia tentang kami.")
        about.body_en = _paragraph("English text about us.")
        about.save_revision().publish()

        html = self.client.get(about.url).content.decode()
        self.assertIn("Teks bahasa Indonesia tentang kami.", html)
        self.assertIn("English text about us.", html)
        # Both panes are present, tagged for the JS toggle.
        self.assertIn('data-lang-pane="id"', html)
        self.assertIn('data-lang-pane="en"', html)

    def test_support_renders_both_bodies(self):
        support = self.tree["support"]
        support.body_id = _paragraph("Alasan untuk memberi dalam bahasa Indonesia.")
        support.body_en = _paragraph("Why give, in English.")
        support.save_revision().publish()

        html = self.client.get(support.url).content.decode()
        self.assertIn("Alasan untuk memberi dalam bahasa Indonesia.", html)
        self.assertIn("Why give, in English.", html)
        self.assertIn('data-lang-pane="id"', html)
        self.assertIn('data-lang-pane="en"', html)

    def test_home_hero_renders_both_headings(self):
        # Both hero heading languages must ship so the client-side toggle can
        # swap them (DESIGN §7); default ID is shown, EN is hidden until toggled.
        home = self.tree["home"]
        home.hero_heading_id = "Bersama membangun masa depan anak."
        home.hero_heading_en = "Building brighter futures together."
        home.save_revision().publish()

        response = self.client.get(home.url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Bersama membangun masa depan anak.", html)
        self.assertIn("Building brighter futures together.", html)
        self.assertIn('data-lang-pane="id"', html)
        self.assertIn('data-lang-pane="en"', html)

    def test_donation_card_labels_are_bilingually_static(self):
        support = self.tree["support"]
        support.account_number = "342-2792161"
        support.save_revision().publish()

        html = self.client.get(support.url).content.decode()
        # Static label carries both languages regardless of the toggle.
        self.assertIn("No. rekening", html)
        self.assertIn("Account no.", html)
        self.assertIn("342-2792161", html)
