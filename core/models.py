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
from django.db.models.functions import ExtractYear
from django.utils.html import strip_tags

from modelcluster.fields import ParentalKey
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page

from .blocks import RICHTEXT_FEATURES, ContentStreamBlock

# Number of blog posts per page on the BlogIndexPage listing.
BLOG_POSTS_PER_PAGE = 10

# Roughly how many words of the body to use for an auto-generated excerpt.
EXCERPT_WORD_COUNT = 40


class HomePage(Page):
    """Beranda — the site root. Singleton."""

    max_count = 1
    parent_page_types = ["wagtailcore.Page"]
    subpage_types = ["core.AboutPage", "core.BlogIndexPage", "core.SupportPage"]

    # The hero photo is now a slideshow backed by HeroSlide (below); the old
    # single hero_image field was removed in favour of the InlinePanel.
    # Heading + subheading are paired ID/EN, driven by the client-side toggle
    # (DESIGN §7) — only the active language shows.
    hero_heading_id = models.CharField(max_length=255, blank=True)
    hero_heading_en = models.CharField(max_length=255, blank=True)
    hero_subheading_id = models.TextField(blank=True)
    hero_subheading_en = models.TextField(blank=True)
    intro = RichTextField(features=RICHTEXT_FEATURES, blank=True)
    support_cta_text = models.CharField(max_length=255, blank=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("hero_heading_id", heading="Judul hero — Bahasa Indonesia"),
                FieldPanel("hero_heading_en", heading="Hero heading — English"),
                FieldPanel("hero_subheading_id", heading="Subjudul hero — Bahasa Indonesia"),
                FieldPanel("hero_subheading_en", heading="Hero subheading — English"),
            ],
            heading="Hero",
        ),
        InlinePanel(
            "hero_slides",
            label="Foto hero (slideshow)",
            help_text=(
                "Tambahkan 3–6 foto untuk slideshow hero. Foto berganti "
                "otomatis di halaman depan."
            ),
            max_num=6,
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


class HeroSlide(Orderable):
    """One photo in the homepage hero slideshow (image only — no caption)."""

    page = ParentalKey(
        HomePage, on_delete=models.CASCADE, related_name="hero_slides"
    )
    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    panels = [
        FieldPanel("image"),
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
        FieldPanel("body_id", heading="Isi — Bahasa Indonesia"),
        FieldPanel("body_en", heading="Content — English"),
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
        all_posts = self.get_posts()

        paginator = Paginator(all_posts, BLOG_POSTS_PER_PAGE)
        page = request.GET.get("page")
        try:
            posts = paginator.page(page)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)
        context["posts"] = posts
        # Compact, elided page list for the numbered pagination control.
        context["page_range"] = list(
            paginator.get_elided_page_range(
                posts.number, on_each_side=1, on_ends=1
            )
        )
        context["pagination_ellipsis"] = paginator.ELLIPSIS

        # Legitimacy signals shown in the header (SPEC §5): a live count of
        # published reports and the founding year ("sejak YYYY"), derived from
        # the oldest published post.
        context["post_count"] = all_posts.count()
        context["founding_year"] = (
            all_posts.aggregate(year=models.Min(ExtractYear("date")))["year"]
        )
        return context


class BlogPostPage(Page):
    """A single activity report (Laporan kegiatan)."""

    parent_page_types = ["core.BlogIndexPage"]
    subpage_types = []

    date = models.DateField("Tanggal")
    # Idempotency key for the Blogspot archive importer (SPEC §13): the stable
    # Blogger entry id (e.g. "tag:blogger.com,1999:blog-…post-784944707…").
    # The importer upserts on this so re-runs update posts instead of
    # duplicating them. Left blank for hand-authored posts.
    blogger_post_id = models.CharField(max_length=255, blank=True, db_index=True)
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

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        siblings = BlogPostPage.objects.sibling_of(self).live()
        # "Previous" reads as the older report, "next" as the newer one — the
        # reader walks the chronicle forward/back in time (DESIGN §5 post nav).
        context["previous_post"] = (
            siblings.filter(date__lt=self.date).order_by("-date").first()
        )
        context["next_post"] = (
            siblings.filter(date__gt=self.date).order_by("date").first()
        )
        context["blog_index"] = self.get_parent().specific
        return context

    def _body_plain_text(self):
        """Flatten the textual body blocks (heading/paragraph/quote) to plain
        text, formatting stripped. Image/gallery blocks contribute nothing."""
        parts = []
        for block in self.body:
            if block.block_type == "heading":
                parts.append(str(block.value))
            elif block.block_type == "paragraph":
                parts.append(strip_tags(block.value.source))
            elif block.block_type == "quote":
                parts.append(block.value.get("text", ""))
        return " ".join(part for part in parts if part).split()

    def get_excerpt(self):
        """The hand-written excerpt when set, otherwise an auto-summary of the
        first ~40 words of the body (SPEC §5)."""
        if self.excerpt.strip():
            return self.excerpt
        words = self._body_plain_text()
        summary = " ".join(words[:EXCERPT_WORD_COUNT])
        if len(words) > EXCERPT_WORD_COUNT:
            summary += "…"
        return summary


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
        FieldPanel("body_id", heading="Isi — Bahasa Indonesia"),
        FieldPanel("body_en", heading="Content — English"),
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
