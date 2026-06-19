"""
Page models (SPEC §5).

Tree (SPEC §4):

    HomePage [root]
    ├── AboutPage        [bilingual toggle]
    ├── BlogIndexPage
    │   └── BlogPostPage (flat, reverse-chron)
    └── SupportPage      [bilingual toggle]
"""
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models

from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page

from .blocks import RICHTEXT_FEATURES, ContentStreamBlock

# Number of blog posts per page on the BlogIndexPage listing.
BLOG_POSTS_PER_PAGE = 10


class HomePage(Page):
    """Beranda — the site root. Singleton."""

    max_count = 1
    parent_page_types = ["wagtailcore.Page"]
    subpage_types = ["core.AboutPage", "core.BlogIndexPage", "core.SupportPage"]

    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    hero_heading = models.CharField(max_length=255, blank=True)
    hero_subheading_id = models.TextField(blank=True)
    hero_subheading_en = models.TextField(blank=True)
    intro = RichTextField(features=RICHTEXT_FEATURES, blank=True)
    support_cta_text = models.CharField(max_length=255, blank=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("hero_image"),
                FieldPanel("hero_heading"),
                FieldPanel("hero_subheading_id"),
                FieldPanel("hero_subheading_en"),
            ],
            heading="Hero",
        ),
        FieldPanel("intro"),
        InlinePanel("stats", label="Statistik", max_num=6),
        FieldPanel("support_cta_text"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["latest_posts"] = (
            BlogPostPage.objects.live().order_by("-date")[:3]
        )
        return context


class HomeStat(Orderable):
    """Above-the-fold legitimacy chip, e.g. "28 anak aktif"."""

    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="stats")
    value = models.CharField(max_length=50)
    label = models.CharField(max_length=255)

    panels = [
        FieldPanel("value"),
        FieldPanel("label"),
    ]


class AboutPage(Page):
    """Tentang — who we are / what we do. Singleton, bilingual toggle."""

    max_count = 1
    parent_page_types = ["core.HomePage"]
    subpage_types = []

    intro_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    body_id = StreamField(ContentStreamBlock(), blank=True)
    body_en = StreamField(ContentStreamBlock(), blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro_image"),
        FieldPanel("body_id", heading="Konten (Bahasa Indonesia)"),
        FieldPanel("body_en", heading="Content (English)"),
    ]


class BlogIndexPage(Page):
    """Laporan — flat, reverse-chronological list of activity reports. Singleton."""

    max_count = 1
    parent_page_types = ["core.HomePage"]
    subpage_types = ["core.BlogPostPage"]

    intro = RichTextField(features=RICHTEXT_FEATURES, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    def get_posts(self):
        return (
            BlogPostPage.objects.child_of(self).live().order_by("-date")
        )

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        paginator = Paginator(self.get_posts(), BLOG_POSTS_PER_PAGE)
        page = request.GET.get("page")
        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)
        context["posts"] = posts
        return context


class BlogPostPage(Page):
    """A single activity report (Laporan kegiatan)."""

    parent_page_types = ["core.BlogIndexPage"]
    subpage_types = []

    date = models.DateField("Tanggal")
    feed_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    excerpt = models.TextField(blank=True)
    # Single body field — Debby writes bilingual content however she likes
    # (typically English block then Indonesian block, stacked). No toggle here.
    body = StreamField(ContentStreamBlock(), blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("feed_image"),
        FieldPanel("excerpt"),
        FieldPanel("body"),
    ]


class SupportPage(Page):
    """Dukung — why give + bank details + partners. Singleton, bilingual toggle."""

    max_count = 1
    parent_page_types = ["core.HomePage"]
    subpage_types = []

    body_id = StreamField(ContentStreamBlock(), blank=True)
    body_en = StreamField(ContentStreamBlock(), blank=True)

    # Donation details — discrete structured fields, rendered as a clean info
    # block (SPEC §5, decision §12.3). Text only; no payment processing.
    account_holder = models.CharField(max_length=255, blank=True)
    bank_name = models.CharField(max_length=255, blank=True)
    account_number = models.CharField(max_length=255, blank=True)
    swift_code = models.CharField(max_length=255, blank=True)

    # Contact — lives only here, not in the footer.
    whatsapp = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("body_id", heading="Konten (Bahasa Indonesia)"),
        FieldPanel("body_en", heading="Content (English)"),
        MultiFieldPanel(
            [
                FieldPanel("account_holder"),
                FieldPanel("bank_name"),
                FieldPanel("account_number"),
                FieldPanel("swift_code"),
            ],
            heading="Rekening donasi",
        ),
        MultiFieldPanel(
            [
                FieldPanel("whatsapp"),
                FieldPanel("email"),
            ],
            heading="Kontak",
        ),
        InlinePanel("partners", label="Mitra"),
    ]


class Partner(Orderable):
    """Social-proof logo, e.g. the IFG / BUMN "Berbagi Kebahagiaan" association."""

    page = ParentalKey(
        SupportPage, on_delete=models.CASCADE, related_name="partners"
    )
    name = models.CharField(max_length=255)
    logo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("logo"),
    ]
