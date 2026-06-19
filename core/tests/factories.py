"""
Helpers to build a realistic page tree for tests.

Wagtail's migrations seed a default root Page, a default "home" Page and a
default Site. We replace that default home with our HomePage and re-point the
Site at it so URLs resolve.
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
    """Create Home + the three structural children and wire up the Site.

    Returns a dict of the created pages.
    """
    root = Page.objects.get(depth=1)
    site = Site.objects.get(is_default_site=True)

    # Re-point the Site at the root before removing the placeholder home page
    # created by the wagtailcore migration — deleting the Site's root_page would
    # cascade-delete the Site itself.
    old_home = site.root_page
    site.root_page = root
    site.save()
    if old_home is not None and old_home.pk != root.pk:
        old_home.delete()

    home = HomePage(title="Beranda", slug="home")
    root.add_child(instance=home)

    about = AboutPage(title="Tentang", slug="tentang")
    home.add_child(instance=about)

    blog_index = BlogIndexPage(title="Laporan", slug="laporan")
    home.add_child(instance=blog_index)

    support = SupportPage(title="Dukung", slug="dukung")
    home.add_child(instance=support)

    site.root_page = home
    # Match Django's default test client host so page.url resolves in requests.
    site.hostname = "testserver"
    site.port = 80
    site.save()

    return {
        "root": root,
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
