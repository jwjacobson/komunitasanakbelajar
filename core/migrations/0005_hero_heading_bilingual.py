# Split the single hero_heading into paired hero_heading_id / hero_heading_en
# so the homepage hero title joins the ID/EN toggle (DESIGN §7).
from django.db import migrations, models


def copy_heading_to_id(apps, schema_editor):
    """Preserve existing content: the old single heading was Indonesian."""
    HomePage = apps.get_model("core", "HomePage")
    for page in HomePage.objects.all():
        if page.hero_heading:
            page.hero_heading_id = page.hero_heading
            page.save(update_fields=["hero_heading_id"])


def copy_id_to_heading(apps, schema_editor):
    """Reverse: fold the Indonesian heading back into the single field."""
    HomePage = apps.get_model("core", "HomePage")
    for page in HomePage.objects.all():
        if page.hero_heading_id:
            page.hero_heading = page.hero_heading_id
            page.save(update_fields=["hero_heading"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_alter_aboutpage_body_en_alter_aboutpage_body_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="homepage",
            name="hero_heading_id",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="homepage",
            name="hero_heading_en",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.RunPython(copy_heading_to_id, copy_id_to_heading),
        migrations.RemoveField(
            model_name="homepage",
            name="hero_heading",
        ),
    ]
