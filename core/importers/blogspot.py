"""
Blogspot archive → StreamField conversion (SPEC §13, Phase 3).

Two pure, network-free functions form the testable core of the importer:

* :func:`sanitize` — turn one post's raw ``content.$t`` (Microsoft-Word paste
  full of ``mso-*`` styling, ``<o:p>`` tags, conditional comments, styling-only
  ``<span>``s and ``&nbsp;``-only paragraphs, plus the donation/blog-promo
  footer) into clean *semantic* HTML, and report what was stripped.
* :func:`extract_blocks` — walk the sanitized tree in document order and map it
  to a flat list of block "intents" (``paragraph`` / ``image`` / ``gallery``).

Neither touches Django, Wagtail or the network, so both can be unit-tested on
real captured feed samples. The management command turns the intents into real
StreamField blocks (downloading images, creating Wagtail Images).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Comment, NavigableString

# The only tags we keep — exactly the paragraph RichTextBlock feature set
# (bold/italic/link/ol/ul) plus images, which become their own blocks.
SEMANTIC_TAGS = {
    "p", "b", "strong", "i", "em", "a", "ul", "ol", "li", "br", "img",
}

# Tags whose *contents* are noise (never unwrap — decompose outright). Anything
# namespaced (``o:p``, ``v:shape``, ``w:…``) is decomposed too.
DROP_TAGS = {"style", "script", "meta", "link", "title", "xml", "head"}

# Attributes worth keeping, per tag. Everything else (style, class, lang,
# mso-*, align, border, data-*, width/height, imageanchor, …) is dropped.
KEEP_ATTRS = {"a": {"href"}, "img": {"src", "alt"}}

# Donation footer marker: the bank/SWIFT/phone block always begins at a "P.S."
# (decision B3). Everything from the first one to the end of the post is cut.
PS_MARKER = re.compile(r"\bP\.\s*S\.", re.IGNORECASE)

# Blog self-promo boilerplate (decision B3) — a paragraph matching any of these
# is dropped wherever it appears. "blogspot.com" catches both the report blog
# and the crafts blog links; the phrases catch the surrounding sentences.
PROMO_MARKERS = (
    "blogspot.com",
    "visit us at",
    "diakses dalam blog kami",
    "to order teenagers",
)

# Heuristic: a URL that points at an actual image file (used to prefer the
# wrapping <a href> high-res source over the <img> display thumbnail).
_IMAGE_URL = re.compile(r"\.(jpe?g|png|gif|webp)(\?|$)", re.IGNORECASE)


@dataclass
class StripReport:
    """What :func:`sanitize` removed, for the dry-run review log (SPEC §13)."""

    comments: int = 0
    footer_paragraphs: list[str] = field(default_factory=list)
    promo_paragraphs: list[str] = field(default_factory=list)
    empty_paragraphs: int = 0


def sanitize(raw_html: str) -> tuple[BeautifulSoup, StripReport]:
    """Clean one post body. Returns ``(soup, report)``.

    The returned soup contains only :data:`SEMANTIC_TAGS` with styling/class/
    lang/mso attributes removed, no ``<o:p>`` or conditional comments, the
    donation P.S. block and blog-promo paragraphs gone, and no ``&nbsp;``-only
    paragraphs.
    """
    soup = BeautifulSoup(raw_html or "", "html.parser")
    report = StripReport()

    # 1. Conditional / Word comments (<!--[if]-->, <!--[endif]-->, …).
    for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
        comment.extract()
        report.comments += 1

    # 2. Noise-content + namespaced tags: decompose (drop their contents too).
    for tag in soup.find_all(True):
        if tag.name in DROP_TAGS or ":" in tag.name:
            tag.decompose()

    # 3. Footer (P.S. → end) and 4. blog-promo paragraphs — done while the
    # original paragraph boundaries are intact (before unwrapping spans).
    report.footer_paragraphs = _strip_footer(soup)
    report.promo_paragraphs = _strip_promo(soup)

    # 5. Unwrap every non-semantic wrapper (span, div, font, center, …),
    # keeping its text/children. Repeat until stable in case of nesting.
    _unwrap_non_semantic(soup)

    # 6. Strip all attributes except the few we keep.
    for tag in soup.find_all(True):
        _clean_attrs(tag)

    # 7. Normalise non-breaking spaces (Word uses runs of them for alignment)
    # to ordinary spaces so they don't survive into stored prose.
    _normalize_nbsp(soup)

    # 8. Collapse &nbsp;-only / empty paragraphs.
    report.empty_paragraphs = _collapse_empty(soup)

    return soup, report


def _strip_footer(soup: BeautifulSoup) -> list[str]:
    """Remove the first "P.S." block and everything after it (decision B3)."""
    nodes = list(soup.children)
    cut_at = None
    for index, node in enumerate(nodes):
        if getattr(node, "name", None) and PS_MARKER.search(node.get_text()):
            cut_at = index
            break
    if cut_at is None:
        return []

    removed = []
    for node in nodes[cut_at:]:
        if getattr(node, "name", None):
            text = node.get_text(" ", strip=True)
            if text:
                removed.append(text[:160])
            node.decompose()
        else:
            text = str(node).strip()
            if text:
                removed.append(text[:160])
            node.extract()
    return removed


def _strip_promo(soup: BeautifulSoup) -> list[str]:
    """Drop any paragraph that is blog self-promo (decision B3)."""
    removed = []
    for paragraph in soup.find_all("p"):
        text = paragraph.get_text(" ", strip=True)
        if not text:
            continue
        lowered = text.lower()
        if any(marker in lowered for marker in PROMO_MARKERS):
            removed.append(text[:160])
            paragraph.decompose()
    return removed


def _unwrap_non_semantic(soup: BeautifulSoup) -> None:
    """Unwrap tags outside :data:`SEMANTIC_TAGS`, preserving their contents."""
    while True:
        unwrapped = False
        for tag in soup.find_all(True):
            if tag.name not in SEMANTIC_TAGS:
                tag.unwrap()
                unwrapped = True
        if not unwrapped:
            break


def _clean_attrs(tag) -> None:
    allowed = KEEP_ATTRS.get(tag.name, set())
    for attr in list(tag.attrs):
        if attr not in allowed:
            del tag[attr]


def _normalize_nbsp(soup: BeautifulSoup) -> None:
    for text in soup.find_all(string=True):
        if "\xa0" in text:
            text.replace_with(text.replace("\xa0", " "))


def _collapse_empty(soup: BeautifulSoup) -> int:
    """Remove <p> elements with no image and no visible text."""
    removed = 0
    for paragraph in soup.find_all("p"):
        if paragraph.find("img"):
            continue
        text = paragraph.get_text().replace("\xa0", " ").strip()
        if not text:
            paragraph.decompose()
            removed += 1
    return removed


# --- block mapping -------------------------------------------------------


def _image_spec(img) -> dict:
    """Build an image intent: display ``src``, best ``download_url`` and alt.

    Blogger wraps the display thumbnail (``…/s320/…``) in an ``<a href>`` that
    points at the high-res original (``…/s1440/…``); prefer that for download.
    """
    src = (img.get("src") or "").strip()
    download_url = src
    anchor = img.find_parent("a")
    if anchor:
        href = (anchor.get("href") or "").strip()
        if href and ("googleusercontent" in href or _IMAGE_URL.search(href)):
            download_url = href
    return {
        "src": src,
        "download_url": download_url,
        "alt": (img.get("alt") or "").strip(),
    }


def _images_in(node) -> list[dict]:
    if getattr(node, "name", None) == "img":
        return [_image_spec(node)]
    if hasattr(node, "find_all"):
        return [_image_spec(img) for img in node.find_all("img")]
    return []


def extract_blocks(soup: BeautifulSoup) -> list[tuple[str, object]]:
    """Map a sanitized tree to ordered block intents.

    Returns a list of ``(kind, value)`` tuples:

    * ``("paragraph", html)`` — consecutive prose accumulated into one block;
    * ``("image", spec)`` — a lone image;
    * ``("gallery", [spec, …])`` — a run of consecutive images.

    ``spec`` is the dict from :func:`_image_spec`. Images must become their own
    blocks because the paragraph RichTextBlock cannot hold inline images.
    """
    blocks: list[tuple[str, object]] = []
    prose: list[str] = []
    images: list[dict] = []

    def flush_prose() -> None:
        html = "".join(prose).strip()
        if html:
            blocks.append(("paragraph", html))
        prose.clear()

    def flush_images() -> None:
        if len(images) == 1:
            blocks.append(("image", images[0]))
        elif len(images) > 1:
            blocks.append(("gallery", list(images)))
        images.clear()

    for node in soup.children:
        if isinstance(node, NavigableString):
            text = str(node).replace("\xa0", " ").strip()
            if text:
                flush_images()
                prose.append(f"<p>{text}</p>")
            continue

        node_images = _images_in(node)
        if node_images:
            flush_prose()
            images.extend(node_images)
        else:
            if not node.get_text().replace("\xa0", " ").strip():
                continue
            flush_images()
            prose.append(str(node))

    flush_prose()
    flush_images()
    return blocks
