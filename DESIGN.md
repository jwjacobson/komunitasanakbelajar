# Komunitas Anak Belajar — Design System (DESIGN.md)

Companion to `SPEC.md`. **SPEC = what to build and how it's wired. DESIGN = how it looks.** The files in `design/mockups/` are the **visual target** — match their appearance, but build production Wagtail templates per SPEC, not by copying the mockups' inline-styled, placeholder-art markup.

---

## 1. Principles

Warm, photo-forward, and trustworthy — a children's charity, **not** a tech product. Flat (no gradients, no heavy drop-shadows), modest corner radius, generous whitespace, real photography leading. Lead with the children's own activity photos; never poverty-as-spectacle. The whole job of the look is to make a diligence-minded donor feel "this is real and well-run."

---

## 2. Color tokens

Define as CSS custom properties. These are fixed brand colors — do **not** auto-derive a dark mode; the cream ground is the brand.

```css
:root {
  --green:        #2F5A40;  /* primary: headings, wordmark, links, one section band */
  --leaf:         #5E8C4E;  /* secondary green: accents, "read more" links, rules */
  --cream:        #F8F3E7;  /* page background (warm paper, never #fff for the page) */
  --terra:        #C06A45;  /* DONATE ACTION ONLY — buttons, callout edge, donate links */
  --wheat:        #E6C879;  /* sparing highlight; callout fill uses the tint below */
  --ink:          #262620;  /* default text / near-black, never pure #000 */

  --body-ink:     #332F29;  /* body prose (slightly softer than --ink) */
  --muted:        #8A8472;  /* captions, labels, dates, secondary text */
  --card:         #FCFAF3;  /* card surface on cream (or #fff for the donation card) */
  --border:       #E3DAC0;  /* card / control borders */
  --hairline:     #E7DEC5;  /* section dividers, nav underline */
  --footer-bg:    #F1EAD9;  /* footer band */
  --callout-bg:   #F4ECD6;  /* callout fill (wheat tint) */
  --sage:         #DFE7D0;  /* image placeholder only — replaced by real photos */
}
```

**Usage rules (important):**
- **Cream** is the page background everywhere.
- **Green** carries headings, the wordmark, links, and exactly one full-bleed section band (the homepage support CTA). Used as a background it gets cream text.
- **Terracotta is reserved for the giving action** — the "Dukung kami" button, the callout's edge + link, the donate CTA on the green band. A visitor should learn in seconds that the warm color = donate. Do not use terracotta decoratively elsewhere.
- **Ink/body-ink** for text; **muted** for the supporting layer (dates, captions, labels).
- Borders are **hairline (0.5px)** in `--border`/`--hairline`. Flat — no shadows.

---

## 3. Typography

Two families, loaded from Google Fonts:
- **Spectral** (serif) — weights 400, 500, 600; italic 400 (for quotes).
- **Hanken Grotesk** (sans) — weights 400, 500.

### The rule: **prose is serif, interface is sans.**
Body paragraphs and the headings *within* reading content are **Spectral**. Everything in the "furniture" layer — nav, buttons, the language toggle, dates, captions, data values, eyebrows, footer — is **Hanken Grotesk**. This sans/serif split is deliberate; it makes report pages feel like reading a letter while keeping the chrome clean.

### Scale

| Role | Font | Size / line-height | Weight |
|---|---|---|---|
| Hero H1 | Spectral | 31px / 1.12 | 500 |
| Page H1 (About/Support/Laporan) | Spectral | 27px / 1.15 | 500 |
| Post H1 | Spectral | 28px / 1.15 | 500 |
| Section H2 (e.g. "Laporan terbaru") | Spectral | 20px | 500 |
| In-content heading block | Spectral | 19px | 600 |
| Body prose | Spectral | 15.5px / 1.72 | 400 |
| Journal entry title | Spectral | 18px / 1.2 | 500 |
| Quote | Spectral *italic* | 17px / 1.5 | 400 |
| Nav / button / UI | Hanken | 13px | 400–500 |
| Caption / label / date | Hanken | 11–12px | 400 |
| Eyebrow (e.g. "TENTANG") | Hanken | 11px, letter-spacing .1em, uppercase | 400 |
| Wordmark line 1 | Spectral | 15px | 600 |
| Wordmark line 2 | Hanken | 9.5px, letter-spacing .07em, `--muted` | 400 |

---

## 4. Spacing & shape

- Section padding: ~28–30px vertical, 22px horizontal.
- **Reading column max-width: 600px** (posts, Support), **640px** (About). Centered.
- Radii: cards 12px, buttons 8px, pills / segmented toggle 20px, images & gallery 10px.
- Borders: 0.5px hairline. No drop-shadows anywhere.

---

## 5. Components

**Wordmark** — green seedling mark + "Komunitas Anak Belajar" (Spectral 600, green) with "CHILDREN LEARNING COMMUNITY" beneath (Hanken, 9.5px, tracked, muted). Get a clean/vector logo from the client; the seedling in the mockups is a stand-in.

**Nav bar** — wordmark left; right side has the three links (Tentang / Laporan / Dukung — active page in green 500), the ID/EN segmented toggle, and the terracotta "Dukung kami" button. Bottom hairline border.

**Buttons** — primary/donate: terracotta fill, cream text, radius 8px, Hanken 500, 13px. Secondary: green outline, green text, same shape.

**ID/EN segmented toggle** — pill container with hairline border; two segments (ID, EN); active segment = green fill + cream text, inactive = transparent + muted. Default **ID**. Keyboard-focusable buttons. (See §7 for behavior.)

**Stat chip** — white card, hairline border, radius 10px; big number in Spectral 600 green; label in Hanken muted.

**Journal entry (Laporan list)** — horizontal row: image thumbnail (~150px, radius 10px) left; content right = muted date, Spectral 500 title (~18px), serif excerpt (~13px / 1.6), leaf-green "Baca selengkapnya →". Thin top hairline between entries. **Year markers** between year groups: Spectral 500 17px green + a hairline rule filling the row.

**Post reading view** — 600px reading column; eyebrow + back-to-Laporan link; muted date; Spectral title; contained header image (radius 10px); body rendered from blocks; footer with top hairline holding prev-post / back-to-archive / next-post links (leaf green). Header image is **contained, never full-bleed** (photos are variable-quality phone shots).

**StreamField blocks:**
- *heading* — Spectral 600, 19px, green, generous top margin.
- *paragraph* — Spectral 15.5px / 1.72, `--body-ink`.
- *image* — contained, radius 10px, optional Hanken muted caption (11.5px) beneath.
- *gallery* — responsive grid (≈3 across, 8px gap, square-ish cells), optional single caption.
- *quote* — 3px `--leaf` left border, Spectral italic 17px green, muted Hanken attribution.
- *callout* — `--callout-bg` fill, 3px `--terra` left border, radius 10px; Spectral 600 green heading; Hanken body; ends in a terracotta "Dukung kami →" link. This is the financial-transparency → giving bridge; its terracotta ties it to the donate action.

**Donation card (Support)** — white card, hairline border, radius 12px. Title "Rekening donasi" (Spectral 600) + muted Hanken "· Bank transfer". Rows = label (Hanken 11px muted) above value (Hanken 14px 500 ink), separated by thin dividers. **Labels are bilingually static** (e.g. "No. rekening · Account no.") — they do *not* follow the language toggle (values are language-neutral).

**Partners (mitra)** — row of bordered white chips, each a logo + Hanken muted name. Lives on the Support page as social proof.

**Footer** — `--footer-bg` band; small wordmark; muted copyright + a Dukung link. Minimal; no settings object behind it (contact lives only on Support).

---

## 6. Page layouts

- **Beranda (home):** nav → hero (text left, **slideshow right**) → stat band (3 chips) → "Laporan terbaru" (3 compact cards, a teaser — distinct from the journal list) → green support-CTA band → footer.
- **Laporan:** nav → header (title + intro + live count "N laporan · sejak YYYY") → year-markered **journal list** → pagination → footer.
- **Post:** nav → reading column (see component) → footer.
- **Tentang:** nav → eyebrow → optional header image → toggling body (`body_id`/`body_en`) → footer.
- **Dukung:** nav → eyebrow → toggling narrative → donation card → contact → partners → footer.

---

## 7. Behaviors

**Hero slideshow** (home, right-hand slot):
- Crossfade (opacity ~0.55s). Auto-advance **4000ms**. Pause on hover. Manual dots + prev/next arrows.
- **Respect `prefers-reduced-motion`** — no auto-advance when the user has requested reduced motion (manual controls still work).
- **No captions** on hero slides (the photos speak for themselves).
- Backed by a `HeroSlide` InlinePanel (image only); guide the editor toward 3–6 slides.

**ID/EN language toggle** (Tentang, Dukung):
- Both `body_id` and `body_en` render server-side; the toggle shows one and hides the other (JS).
- Default **ID**. Persist the choice in **`localStorage`** so it holds across pages.
- Governs **body prose only** — nav, labels, buttons, and the donation-card labels stay put.

---

## 8. Accessibility

Ink-on-cream and cream-on-green both clear-contrast. Honor reduced-motion (above). Alt text comes through Wagtail's `ImageBlock` contextual alt. Toggle and slideshow controls are real, focusable `<button>`s.

---

## 9. The mockups

`design/mockups/{home,laporan-index,post,tentang,dukung}.html` are the visual targets. They are **mockup-grade**: hardcoded hex, inline styles, placeholder seedling SVGs for photos, invented copy, and a fake browser frame omitted. Use them to match layout, proportion, color, and type — then implement properly with the tokens above and real Wagtail/Django templates per SPEC.
