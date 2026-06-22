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
        template = "core/blocks/quote_block.html"


class CalloutBlock(blocks.StructBlock):
    """Highlighted box — e.g. "this month's operational needs" / "how to help"."""

    heading = blocks.CharBlock()
    body = blocks.RichTextBlock(features=RICHTEXT_FEATURES)

    class Meta:
        icon = "warning"
        label = "Sorotan"
        template = "core/blocks/callout_block.html"


class ContentStreamBlock(blocks.StreamBlock):
    """The shared body block set used by every content StreamField."""

    heading = blocks.CharBlock(
        icon="title", label="Sub-judul",
        template="core/blocks/heading_block.html",
    )
    paragraph = blocks.RichTextBlock(
        features=RICHTEXT_FEATURES, icon="pilcrow", label="Paragraf",
        template="core/blocks/paragraph_block.html",
    )
    image = ImageBlock(template="core/blocks/image_block.html")
    gallery = blocks.ListBlock(
        ImageBlock(), icon="image", label="Galeri",
        template="core/blocks/gallery_block.html",
    )
    quote = QuoteBlock()
    callout = CalloutBlock()
