"""
Helpers to build a realistic page tree for tests.

The core.0002_create_homepage data migration already seeds a HomePage as the
default Site's root. These helpers reuse that HomePage and add the three
structural children (Tentang / Laporan / Dukung) on top.
"""
import datetime

from wagtail.models import Page, Site

from core.models import (
    AboutPage,
    BlogIndexPage,
    BlogPostPage,
    HomePage,
    SupportPage,
)


def make_site_tree():
    """Return the seeded HomePage plus its three structural children.

    Returns a dict of the pages.
    """
    # Created by the core.0002_create_homepage data migration.
    home = HomePage.objects.get()

    about = AboutPage(title="Tentang", slug="tentang")
    home.add_child(instance=about)

    blog_index = BlogIndexPage(title="Laporan", slug="laporan")
    home.add_child(instance=blog_index)

    support = SupportPage(title="Dukung", slug="dukung")
    home.add_child(instance=support)

    site = Site.objects.get(is_default_site=True)
    site.root_page = home
    # Match Django's default test client host so page.url resolves in requests.
    site.hostname = "testserver"
    site.port = 80
    site.save()

    return {
        "root": Page.objects.get(depth=1),
        "home": home,
        "about": about,
        "blog_index": blog_index,
        "support": support,
    }


def add_post(blog_index, title, date, *, live=True):
    """Add a BlogPostPage child to the given index."""
    if isinstance(date, str):
        date = datetime.date.fromisoformat(date)
    post = BlogPostPage(
        title=title,
        slug=title.lower().replace(" ", "-"),
        date=date,
        live=live,
    )
    blog_index.add_child(instance=post)
    return post
