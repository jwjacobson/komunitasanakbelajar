"""
Import the historical Blogspot archive into BlogPostPage records (SPEC §13).

Feed-first: pages through the public Blogger JSON feed (full post content),
sanitizes each Word-paste body into clean semantic HTML, maps it to StreamField
blocks, downloads images into Wagtail Images, and upserts one BlogPostPage per
post under the single BlogIndexPage (Laporan).

Idempotent: keyed on ``blogger_post_id`` for posts and on source URL for images,
so a partial/failed run resumes without duplicating anything.

    uv run python manage.py import_blogspot --limit 10      # the dry run

Phase-3 gate: do NOT run the full 752-post import here — that happens against
production in Phase 4, after the developer reviews this dry run.
"""
from __future__ import annotations

import hashlib
import time
from io import BytesIO
from urllib.parse import unquote, urlparse

import requests
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify
from wagtail.images import get_image_model
from wagtail.models import Page

from core.importers.blogspot import extract_blocks, sanitize
from core.models import BlogIndexPage, BlogPostPage

DEFAULT_BLOG_URL = "https://cakungchildrencommunity.blogspot.com"

USER_AGENT = (
    "KomunitasAnakBelajar-importer/1.0 "
    "(+archive migration; contact jeffjacobsonhimself@gmail.com)"
)


class Command(BaseCommand):
    help = "Import the historical Blogspot archive into BlogPostPage records."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", type=int, default=None,
            help="Process only the first N posts (use this for the dry run).",
        )
        parser.add_argument(
            "--start-index", type=int, default=1,
            help="1-based feed index to start at (resume support).",
        )
        parser.add_argument(
            "--blog-url", default=DEFAULT_BLOG_URL,
            help=f"Blog base URL (default: {DEFAULT_BLOG_URL}).",
        )
        parser.add_argument(
            "--batch-size", type=int, default=25,
            help="Feed entries to request per page (max-results).",
        )
        parser.add_argument(
            "--throttle", type=float, default=1.0,
            help="Seconds to wait between feed/image requests (be polite).",
        )
        parser.add_argument(
            "--max-retries", type=int, default=4,
            help="Retries per request, with exponential backoff.",
        )

    def handle(self, *args, **options):
        self.blog_url = options["blog_url"].rstrip("/")
        self.throttle = options["throttle"]
        self.max_retries = options["max_retries"]
        self.limit = options["limit"]
        self.batch_size = options["batch_size"]

        self.Image = get_image_model()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        # Within-run cache of source URL → Image (cross-run dedupe is by title).
        self._image_cache: dict[str, object] = {}

        parent = self._get_blog_index()

        # Running totals for the summary.
        self.posts_created = 0
        self.posts_updated = 0
        self.images_imported = 0
        self.images_reused = 0
        self.dead_images: list[str] = []
        self.stripped_samples: list[str] = []

        for entry in self._iter_entries(options["start_index"]):
            self._import_entry(entry, parent)

        self._print_summary()

    # --- feed ------------------------------------------------------------

    def _get_blog_index(self) -> BlogIndexPage:
        parent = BlogIndexPage.objects.first()
        if parent is None:
            raise CommandError(
                "No BlogIndexPage (Laporan) found — create the page tree first."
            )
        return parent

    def _request(self, url, *, params=None, binary=False):
        """GET with retry + exponential backoff. Returns json or bytes."""
        last_exc = None
        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(url, params=params, timeout=30)
                resp.raise_for_status()
                return resp.content if binary else resp.json()
            except (requests.RequestException, ValueError) as exc:
                last_exc = exc
                wait = self.throttle * (2 ** attempt)
                self.stderr.write(
                    f"  request failed ({exc}); retry in {wait:.1f}s"
                )
                time.sleep(wait)
        raise CommandError(f"Giving up on {url}: {last_exc}")

    def _iter_entries(self, start_index):
        """Yield feed entries, paginating with max-results / start-index."""
        feed_url = f"{self.blog_url}/feeds/posts/default"
        index = start_index
        yielded = 0
        while True:
            page_size = self.batch_size
            if self.limit is not None:
                page_size = min(page_size, self.limit - yielded)
            if page_size <= 0:
                return
            data = self._request(
                feed_url,
                params={
                    "alt": "json",
                    "max-results": page_size,
                    "start-index": index,
                },
            )
            feed = data.get("feed", {})
            entries = feed.get("entry", []) or []
            if not entries:
                return
            for entry in entries:
                yield entry
                yielded += 1
                if self.limit is not None and yielded >= self.limit:
                    return
            index += len(entries)
            total = int(feed.get("openSearch$totalResults", {}).get("$t", 0))
            if total and index > total:
                return
            time.sleep(self.throttle)

    # --- per-post --------------------------------------------------------

    def _import_entry(self, entry, parent):
        blogger_id = entry["id"]["$t"]
        title = entry["title"]["$t"].strip() or "(tanpa judul)"
        published = parse_datetime(entry["published"]["$t"])
        date = published.date()
        alternate = self._alternate_url(entry)

        soup, report = sanitize(entry["content"]["$t"])
        intents = extract_blocks(soup)

        self._log_strip(title, report)

        body, first_image = self._build_body(intents, title)
        feed_image = first_image or self._import_thumbnail(entry, title)

        existing = BlogPostPage.objects.filter(blogger_post_id=blogger_id).first()
        if existing:
            page = existing
            page.title = title
            page.date = date
            page.body = body
            page.feed_image = feed_image
            action = "updated"
            self.posts_updated += 1
        else:
            page = BlogPostPage(
                title=title,
                slug=self._unique_slug(alternate, title, parent),
                date=date,
                body=body,
                feed_image=feed_image,
                blogger_post_id=blogger_id,
            )
            parent.add_child(instance=page)
            action = "created"
            self.posts_created += 1

        # Publish live with the original date so the chronicle orders correctly.
        revision = page.save_revision()
        revision.publish()
        page.first_published_at = published
        page.last_published_at = published
        page.save()

        self.stdout.write(
            f"[{action}] {date} {title[:60]} "
            f"({len(body)} blocks)"
        )

    def _alternate_url(self, entry):
        for link in entry.get("link", []):
            if link.get("rel") == "alternate":
                return link.get("href", "")
        return ""

    def _log_strip(self, title, report):
        bits = []
        if report.footer_paragraphs:
            bits.append(f"{len(report.footer_paragraphs)} footer P.S. paras")
        if report.promo_paragraphs:
            bits.append(f"{len(report.promo_paragraphs)} promo paras")
        if report.empty_paragraphs:
            bits.append(f"{report.empty_paragraphs} empty paras")
        if report.comments:
            bits.append(f"{report.comments} comments")
        self.stdout.write(f"  stripped: {', '.join(bits) or 'nothing'}")
        # Keep a couple of stripped footer/promo snippets for the summary so the
        # reviewer can confirm we are not eating real content.
        for snippet in report.footer_paragraphs[:1] + report.promo_paragraphs[:1]:
            if len(self.stripped_samples) < 8:
                self.stripped_samples.append(f"{title[:30]}: {snippet}")

    def _build_body(self, intents, title):
        """Turn block intents into a StreamField value; return (body, first_image)."""
        body = []
        first_image = None
        for kind, value in intents:
            if kind == "paragraph":
                body.append(("paragraph", value))
            elif kind == "image":
                image = self._image_block(value, title)
                if image is not None:
                    body.append(("image", image))
                    first_image = first_image or image
            elif kind == "gallery":
                images = [self._image_block(spec, title) for spec in value]
                images = [img for img in images if img is not None]
                if len(images) == 1:
                    body.append(("image", images[0]))
                elif images:
                    body.append(("gallery", images))
                if images:
                    first_image = first_image or images[0]
        return body, first_image

    def _image_block(self, spec, title):
        """Download + create (or reuse) a Wagtail Image with contextual alt."""
        image = self._get_or_create_image(spec["download_url"], title)
        if image is None:
            return None
        # ImageBlock carries contextual alt on the instance; fall back to the
        # post title so the image is never alt-less.
        image.contextual_alt_text = spec.get("alt") or title
        image.decorative = False
        return image

    def _get_or_create_image(self, url, title):
        if not url:
            return None
        if url in self._image_cache:
            self.images_reused += 1
            return self._image_cache[url]

        name = self._image_filename(url)
        key = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
        # Cross-run idempotency: a deterministic title keyed on the source URL.
        image_title = f"{name} [{key}]"

        existing = self.Image.objects.filter(title=image_title).first()
        if existing:
            self._image_cache[url] = existing
            self.images_reused += 1
            return existing

        try:
            content = self._request(url, binary=True)
        except CommandError as exc:
            # Dead image (some 2009–2011 URLs 404): skip it, keep the post.
            self.stderr.write(f"  dead image skipped: {url} ({exc})")
            self.dead_images.append(url)
            return None

        image = self.Image(
            title=image_title,
            file=ImageFile(BytesIO(content), name=name),
        )
        image.save()
        self._image_cache[url] = image
        self.images_imported += 1
        time.sleep(self.throttle)
        return image

    def _import_thumbnail(self, entry, title):
        """Fallback feed_image: the entry's media$thumbnail."""
        thumb = (entry.get("media$thumbnail") or {}).get("url")
        if not thumb:
            return None
        image = self._get_or_create_image(thumb, title)
        if image is not None:
            image.contextual_alt_text = title
            image.decorative = False
        return image

    @staticmethod
    def _image_filename(url):
        path = urlparse(url).path
        name = unquote(path.rsplit("/", 1)[-1]) or "image"
        if "." not in name:
            name += ".jpg"
        return name[:90]

    def _unique_slug(self, alternate_url, title, parent):
        """Slug from the original Blogspot path (decision D2), else the title."""
        base = ""
        if alternate_url:
            path = urlparse(alternate_url).path
            last = path.rstrip("/").rsplit("/", 1)[-1]
            if last.endswith(".html"):
                last = last[: -len(".html")]
            base = slugify(last)
        if not base:
            base = slugify(title)
        if not base:
            base = "laporan"

        slug = base
        suffix = 2
        siblings = Page.objects.child_of(parent)
        while siblings.filter(slug=slug).exists():
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug

    def _print_summary(self):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Import summary ==="))
        self.stdout.write(
            f"Posts: {self.posts_created} created, {self.posts_updated} updated"
        )
        self.stdout.write(
            f"Images: {self.images_imported} imported, "
            f"{self.images_reused} reused/deduped, "
            f"{len(self.dead_images)} dead (skipped)"
        )
        if self.dead_images:
            self.stdout.write("Dead image URLs:")
            for url in self.dead_images:
                self.stdout.write(f"  - {url}")
        if self.stripped_samples:
            self.stdout.write("Stripped footer/promo samples:")
            for sample in self.stripped_samples:
                self.stdout.write(f"  - {sample}")
