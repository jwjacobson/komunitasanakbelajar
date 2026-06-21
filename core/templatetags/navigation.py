"""
Navigation / chrome template tags.

The header and footer need the URLs of the structural singleton pages (Tentang /
Laporan / Dukung) and the home page, plus the active-section state. These are
all max_count=1 pages, so a simple `.live().first()` resolves each one.
"""
from django import template

from core.models import (
    AboutPage,
    BlogIndexPage,
    BlogPostPage,
    HomePage,
    SupportPage,
)

register = template.Library()


def _active_section(page):
    """Map the current page onto a nav section key for active styling."""
    if isinstance(page, AboutPage):
        return "about"
    if isinstance(page, (BlogIndexPage, BlogPostPage)):
        return "blog"
    if isinstance(page, SupportPage):
        return "support"
    return ""


def _chrome_context(context):
    page = context.get("page")
    return {
        "home": HomePage.objects.live().first(),
        "about": AboutPage.objects.live().first(),
        "blog": BlogIndexPage.objects.live().first(),
        "support": SupportPage.objects.live().first(),
        "active": _active_section(page),
        "request": context.get("request"),
    }


@register.simple_tag
def support_url():
    """URL of the Support (Dukung) page, for the callout's giving link."""
    support = SupportPage.objects.live().first()
    return support.url if support else "#"


@register.simple_tag
def blog_url():
    """URL of the Laporan (BlogIndex) page, for home-page links."""
    blog = BlogIndexPage.objects.live().first()
    return blog.url if blog else "#"


@register.inclusion_tag("core/includes/header.html", takes_context=True)
def site_header(context):
    return _chrome_context(context)


@register.inclusion_tag("core/includes/footer.html", takes_context=True)
def site_footer(context):
    return _chrome_context(context)
