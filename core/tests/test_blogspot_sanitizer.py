"""
Unit tests for the pure sanitizer / block mapper (SPEC §13, task §7).

Run against real captured feed samples (one EN, one ID) in
``fixtures/blogspot/``. No Django/Wagtail/network needed.
"""
import json
from pathlib import Path

import pytest

from core.importers.blogspot import extract_blocks, sanitize

FIXTURES = Path(__file__).parent / "fixtures" / "blogspot"


def _content(name):
    entry = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return entry["content"]["$t"]


SAMPLES = ["entry_en.json", "entry_id.json"]


@pytest.fixture(params=SAMPLES)
def sample(request):
    raw = _content(request.param)
    soup, report = sanitize(raw)
    return raw, soup, report


def test_no_word_residue(sample):
    _, soup, _ = sample
    html = str(soup)
    assert "mso-" not in html
    assert "style=" not in html
    assert "class=" not in html
    assert "<o:p" not in html
    assert "lang=" not in html


def test_only_semantic_tags_remain(sample):
    from core.importers.blogspot import SEMANTIC_TAGS

    _, soup, _ = sample
    tags = {t.name for t in soup.find_all(True)}
    assert tags <= SEMANTIC_TAGS, f"unexpected tags: {tags - SEMANTIC_TAGS}"


def test_no_nbsp_only_paragraphs(sample):
    _, soup, _ = sample
    for paragraph in soup.find_all("p"):
        if paragraph.find("img"):
            continue
        text = paragraph.get_text().replace("\xa0", " ").strip()
        assert text, "found an empty / nbsp-only <p>"
    # And no stray non-breaking spaces survive in prose at all.
    assert "\xa0" not in str(soup)


def test_donation_footer_removed(sample):
    _, soup, report = sample
    html = str(soup)
    assert "P.S." not in html
    # Bank/SWIFT/account boilerplate from the P.S. block is gone.
    assert "SWIFT" not in html.upper()
    assert "Account holder" not in html
    assert report.footer_paragraphs, "expected footer paragraphs to be reported"


def test_blog_promo_removed(sample):
    _, soup, report = sample
    html = str(soup)
    assert "blogspot.com" not in html
    assert report.promo_paragraphs, "expected promo paragraphs to be reported"


def test_real_content_preserved(sample):
    """Sanity check we didn't eat the body: real prose survives."""
    _, soup, _ = sample
    text = soup.get_text(" ", strip=True)
    assert len(text) > 500
    assert "children" in text.lower() or "anak" in text.lower()


def test_images_become_blocks_with_prose_preserved(sample):
    _, soup, _ = sample
    blocks = extract_blocks(soup)
    kinds = [kind for kind, _ in blocks]
    assert "paragraph" in kinds, "prose should survive as paragraph blocks"
    assert "image" in kinds or "gallery" in kinds, "images should be extracted"
    # No paragraph block contains an inline <img> (they must be their own block).
    for kind, value in blocks:
        if kind == "paragraph":
            assert "<img" not in value


def test_image_blocks_prefer_highres_source(sample):
    _, soup, _ = sample
    blocks = extract_blocks(soup)
    specs = []
    for kind, value in blocks:
        if kind == "image":
            specs.append(value)
        elif kind == "gallery":
            specs.extend(value)
    assert specs, "expected at least one image spec"
    for spec in specs:
        assert spec["download_url"].startswith("http")
        # High-res Blogger originals use a large /sNNNN/ size segment, not the
        # /s320/ display thumbnail.
        assert "googleusercontent" in spec["download_url"]


def test_empty_html_is_safe():
    soup, report = sanitize("")
    assert extract_blocks(soup) == []
    assert report.footer_paragraphs == []
