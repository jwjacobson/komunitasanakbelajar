"""
Shared StreamField block set (SPEC §6).

Deliberately tight: every block is a way for a non-technical editor to break the
layout, so the set is small and opinionated. Used by AboutPage / SupportPage
(paired *_id / *_en bodies) and BlogPostPage (single body).
"""
from wagtail import blocks
from wagtail.images.blocks import ImageBlock

# RichText is limited to these inline/list features everywhere it appears. No
# inline headings (those are the dedicated `heading` block), no embeds, tables,
# images-in-text, etc.
RICHTEXT_FEATURES = ["bold", "italic", "link", "ol", "ul"]


class QuoteBlock(blocks.StructBlock):
    """A pull quote / testimonial / scripture line."""

    text = blocks.TextBlock()
    attribution = blocks.CharBlock(required=False)

    class Meta:
        icon = "openquote"
        label = "Kutipan"


class CalloutBlock(blocks.StructBlock):
    """Highlighted box — e.g. "this month's operational needs" / "how to help"."""

    heading = blocks.CharBlock()
    body = blocks.RichTextBlock(features=RICHTEXT_FEATURES)

    class Meta:
        icon = "warning"
        label = "Sorotan"


class ContentStreamBlock(blocks.StreamBlock):
    """The shared body block set used by every content StreamField."""

    heading = blocks.CharBlock(icon="title", label="Sub-judul")
    paragraph = blocks.RichTextBlock(
        features=RICHTEXT_FEATURES, icon="pilcrow", label="Paragraf"
    )
    image = ImageBlock()
    gallery = blocks.ListBlock(
        ImageBlock(), icon="image", label="Galeri"
    )
    quote = QuoteBlock()
    callout = CalloutBlock()
