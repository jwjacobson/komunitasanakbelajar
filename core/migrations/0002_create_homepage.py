"""
Replace the stock "Welcome to your new Wagtail site!" page with our HomePage
and point the default Site at it.

Wagtail's bootstrap (wagtailcore initial-data migration) seeds:
  - the true tree root (depth 1, path "0001"),
  - a generic Page "Welcome…" at path "00010001" (depth 2), and
  - a default Site whose root_page is that welcome page.

We delete the welcome page (which cascade-deletes the default Site, since the
Site's root_page FK is the welcome page), create a real HomePage in its slot,
and recreate the default Site pointing at the HomePage.
"""
from django.db import migrations


def create_homepage(apps, schema_editor):
    ContentType = apps.get_model("contenttypes.ContentType")
    Page = apps.get_model("wagtailcore.Page")
    Site = apps.get_model("wagtailcore.Site")
    Locale = apps.get_model("wagtailcore.Locale")
    HomePage = apps.get_model("core.HomePage")

    # Nothing to do if a HomePage already exists (idempotent / re-run safe).
    if HomePage.objects.exists():
        return

    locale = (
        Locale.objects.filter(language_code="id").first()
        or Locale.objects.first()
    )

    # Remove the stock welcome page. This frees its tree slot ("00010001") and
    # cascade-deletes the default Site that points at it.
    Page.objects.filter(depth=2, slug="home").delete()

    homepage_content_type, _ = ContentType.objects.get_or_create(
        app_label="core", model="homepage"
    )

    homepage = HomePage.objects.create(
        title="Beranda",
        draft_title="Beranda",
        slug="home",
        content_type=homepage_content_type,
        path="00010001",
        depth=2,
        numchild=0,
        url_path="/home/",
        locale=locale,
    )

    # Recreate the default Site, now rooted at the HomePage.
    Site.objects.update_or_create(
        is_default_site=True,
        defaults={
            "hostname": "localhost",
            "port": 80,
            "site_name": "Komunitas Anak Belajar",
            "root_page": homepage,
        },
    )


def remove_homepage(apps, schema_editor):
    """Reverse: drop our HomePage and restore a generic welcome page + Site."""
    ContentType = apps.get_model("contenttypes.ContentType")
    Page = apps.get_model("wagtailcore.Page")
    Site = apps.get_model("wagtailcore.Site")
    Locale = apps.get_model("wagtailcore.Locale")
    HomePage = apps.get_model("core.HomePage")

    locale = Locale.objects.first()

    HomePage.objects.all().delete()

    page_content_type, _ = ContentType.objects.get_or_create(
        app_label="wagtailcore", model="page"
    )
    welcome = Page.objects.create(
        title="Welcome to your new Wagtail site!",
        draft_title="Welcome to your new Wagtail site!",
        slug="home",
        content_type=page_content_type,
        path="00010001",
        depth=2,
        numchild=0,
        url_path="/home/",
        locale=locale,
    )
    Site.objects.update_or_create(
        is_default_site=True,
        defaults={
            "hostname": "localhost",
            "port": 80,
            "root_page": welcome,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_homepage, remove_homepage),
    ]
