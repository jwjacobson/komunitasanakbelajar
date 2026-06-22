# Komunitas Anak Belajar — Build Specification

**Status:** locked (v1.1 — added migration phase + journal-style index)
**Purpose:** greenfield build spec for a Wagtail website, to be executed by Claude Code.
**Domain:** childrenlearning.org

---

## 1. Project overview

A website for **Komunitas Anak Belajar** (English: *Children Learning Community*), a small charity in the Jakarta area run by one person (Debby). It provides education and outreach for underprivileged children at two learning centres: **Cakung** and **Ciawi**.

This site replaces a dormant Blogspot (last post 2024). Debby writes all content; the developer builds, deploys, and maintains the infrastructure and then steps back.

### Primary goal

Project **legitimacy** to attract donors — specifically, to make it plausible for an individual patron to commit to recurring support. Every design and content decision serves this. The site's real asset is the *ongoing record of activity* (the activity reports), which is proof of consistency.

### Audiences

1. International / English-reading prospective donors (the patron target).
2. Local Indonesian community, partners, and Debby herself.

---

## 2. Scope

### In scope (v1)

- Five-page Wagtail site (see IA).
- Selective bilingual support (Indonesian + English) via a simple front-end toggle on structural pages.
- A reverse-chronological **journal-style** report index ("Laporan kegiatan") — single-column entries with image, date, title, and a generous auto-excerpt; year markers; pagination. (Not a card grid.)
- Photo-forward design using the charity's own photography.
- Admin interface in Indonesian.
- Cloudflare R2 for media storage; Railway for app + managed Postgres.
- Donation info presented as static bank-transfer details + contact (no payment processing).
- **Migration of the full historical Blogspot archive** (back to 2009) into `BlogPostPage` records — see §13. A core deliverable, not optional: the populated chronicle *is* the legitimacy asset.

### Explicitly OUT of scope (do not build)

- **No payment integration** (no Stripe/PayPal/Midtrans/QRIS). Requires a registered legal entity that does not yet exist. Bank details are presented as text only.
- **No `wagtail-localize` / full Wagtail i18n.** Do not duplicate the page tree per locale. Bilingual support is achieved with paired language fields + a JS toggle (see §7). This is deliberate — the sole editor must not face a per-locale tree.
- **No blog taxonomy** (no categories/tags). Flat reverse-chron list only.
- No user accounts, comments, newsletter signup, or search (search may be a v2 addition).

---

## 3. Tech stack

| Component | Choice | Notes |
|---|---|---|
| CMS | **Wagtail 7.4 LTS** | Current LTS, security support through Nov 2027 |
| Framework | **Django 5.2 LTS** | Required by Wagtail 7.4; LTS for longevity |
| Python | **3.13** | |
| Dependency mgmt | **uv** + `pyproject.toml` | |
| Database | **PostgreSQL** | Railway managed plugin |
| Media storage | **Cloudflare R2** via `django-storages[s3]` | S3-compatible; see §8 |
| Static files | **WhiteNoise** + `collectstatic` | Manifest storage |
| App server | **gunicorn** | |
| Hosting | **Railway** | App service + Postgres plugin |

Settings split into `config/settings/{base,dev,production}.py`.

Pin LTS releases in `pyproject.toml`. Rationale: this is a low-touch site the maintainer wants to leave alone for long stretches; LTS maximises the unattended-but-supported window.

---

## 4. Information architecture

Nav labels are **Indonesian-primary** (Debby lives in the admin), English shown as the secondary toggle on the site itself.

```
Beranda (Home)            — HomePage          [root]
├── Tentang (About)        — AboutPage         [bilingual toggle]
├── Laporan (Reports/Blog) — BlogIndexPage
│   └── <post>             — BlogPostPage      (flat, reverse-chron)
└── Dukung (Support)       — SupportPage       [bilingual toggle]
```

**Note:** "Kegiatan" (what we do) is folded into **Tentang** — for an org this size, "who we are" and "what we do" are one page. No separate programs page in v1.

Top nav: Beranda · Tentang · Laporan · Dukung, plus an **ID / EN** language toggle and a terracotta **Dukung kami** button.

---

## 5. Page models

App name suggestion: `home` for HomePage + site-wide pieces, `blog` for the index/post, or a single `core` app — implementer's choice, keep it simple.

### `HomePage` (max_count = 1, child of root)

- `hero_image` — FK to `wagtailimages.Image`, `SET_NULL`, nullable.
- `hero_heading` — CharField. (e.g. "Setiap anak berhak untuk belajar.")
- `hero_subheading_id` — CharField/TextField.
- `hero_subheading_en` — CharField/TextField.
- `intro` — RichTextField, optional, short welcome.
- **Stats** — `InlinePanel` of `HomeStat(Orderable)`: `value` (CharField, e.g. "28"), `label` (CharField, e.g. "anak aktif"). Target ~3. These are the above-the-fold legitimacy chips; keep editable.
- `support_cta_text` — CharField (button label).
- `get_context`: attach latest **3** published `BlogPostPage` by date desc.
- `subpage_types = ['AboutPage', 'BlogIndexPage', 'SupportPage']`
- `parent_page_types = ['wagtailcore.Page']`

### `AboutPage` (max_count = 1, child of HomePage) — *Tentang*

- `intro_image` — FK Image, optional, header image.
- `body_id` — StreamField (shared block set, §6). Indonesian.
- `body_en` — StreamField (shared block set, §6). English.
- Front-end renders both; JS toggle shows one at a time (§7).
- `subpage_types = []`

### `BlogIndexPage` (max_count = 1, child of HomePage) — *Laporan*

- `intro` — RichTextField, optional.
- `get_context`: paginated list of child `BlogPostPage`, date desc.
- **Presentation: journal-style single-column list** (not a card grid). Each entry: `feed_image` thumbnail, `date`, `title`, a generous excerpt, and a "Baca selengkapnya" link. Group entries under **year markers** (e.g. "2024") as the list descends — this renders the archive as a chronicle and is the visible proof-of-consistency.
- Header shows a live **count** ("N laporan") and the founding year ("sejak YYYY") — both legitimacy signals; count derives from published posts.
- Paginate (~10 per page).
- `subpage_types = ['BlogPostPage']`

### `BlogPostPage` (child of BlogIndexPage) — a report

- `date` — DateField.
- `feed_image` — FK Image, optional (used on index cards + post header).
- `excerpt` — TextField, optional. **Auto-generated** from the first ~40 words of `body` (formatting stripped) when left blank; the field acts as a manual override when Debby wants to hand-write the summary. Shown in the journal-list entry.
- `body` — StreamField (shared block set, §6). **Single field** — Debby writes bilingual content however she likes (her natural habit is to stack the full English text then the full Indonesian text). Do not impose a language mechanism here.
- `subpage_types = []`

### `SupportPage` (max_count = 1, child of HomePage) — *Dukung*

- `body_id` — StreamField (shared block set). Indonesian "why give" narrative.
- `body_en` — StreamField (shared block set). English.
- **Donation details** (structured fields, rendered as a clean info block):
  - `account_holder` — CharField
  - `bank_name` — CharField
  - `account_number` — CharField
  - `swift_code` — CharField
- **Contact:** `whatsapp` — CharField, `email` — EmailField.
- **Partners / social proof** — `InlinePanel` of `Partner(Orderable)`: `name` (CharField), `logo` (FK Image). Use for the IFG / BUMN "Berbagi Kebahagiaan" association — third-party validation that an established institution has worked with the charity.
- `subpage_types = []`

### Footer (no settings object)

No `SiteSettings` snippet. Keep the footer minimal: a copyright/credit line + a link to Dukung. Contact details (email/WhatsApp) live only on the Support page, not in the footer — one less concept in the admin for a sole non-technical editor.

---

## 6. Shared StreamField block set

**Keep this tight and opinionated.** Every block type is a way for a non-technical editor to break the layout or get confused. Five blocks (+ one optional). Do not add more without a reason.

1. `heading` — CharBlock. A section subheading.
2. `paragraph` — RichTextBlock, **features limited to**: `bold`, `italic`, `link`, `ol`, `ul`. No inline headings (those come from the `heading` block), no embeds, no tables.
3. `image` — Wagtail's `ImageBlock` (the 6.3+ block with contextual alt text). Use this, **not** `ImageChooserBlock`.
4. `gallery` — `ListBlock(ImageBlock())`. For the photo-heavy reports.
5. `quote` — StructBlock: `text` (TextBlock), `attribution` (CharBlock, optional). Suits testimonials and the occasional scripture line; fits the warm tone.
6. *(optional, recommended)* `callout` — StructBlock: `heading` (CharBlock), `body` (RichTextBlock, limited). For the recurring "this month's operational needs" / "how you can help" highlight. This is Debby's financial-transparency instinct made into a reusable element — it's a real retention tool for recurring donors, so I'd include it.

---

## 7. Bilingual approach

**Mechanism:** paired language fields + a pure front-end toggle. No Django/Wagtail i18n machinery.

- **Toggle pages** (About, Support): two parallel content fields, `*_id` and `*_en`. Both render into the page; a small **ID / EN** control in the header shows one and hides the other via JS (default: ID, since the org is Indonesian and the local audience + editor are the everyday users; English is one tap away for the patron). Persist the choice in `localStorage` so it sticks across pages.
- **Blog posts:** single `body` field. Debby writes in whatever mix she likes (typically English block then Indonesian block, stacked). No toggle — authentic and zero-friction.
- **Nav / chrome:** keep nav labels bilingual-aware where cheap (Indonesian label, English understood via the toggle), but don't over-engineer. The toggle governs page *body* content, not every UI string.

**Admin language:** `LANGUAGE_CODE = 'id'` so Wagtail's admin renders in Indonesian for Debby. `TIME_ZONE = 'Asia/Jakarta'`. `WAGTAIL_SITE_NAME = 'Komunitas Anak Belajar'`. `USE_I18N = True` but **no** locale-prefixed URLs and **no** `LocaleMiddleware` for the public site.

---

## 8. Media & storage (important)

Railway's filesystem is **ephemeral** — uploaded media is wiped on every redeploy. This is a photo-heavy site with a non-technical editor uploading constantly, so media **must** go to external object storage from day one. Retrofitting after a year of uploads risks losing her content.

- **Media:** Cloudflare R2 via `django-storages[s3]`. Configure `STORAGES["default"]` to the S3 backend with the R2 endpoint. Free egress, effectively free at this scale, and the maintainer already uses Cloudflare. Optionally front it with a custom R2 domain (e.g. `media.childrenlearning.org`).
- **Static:** WhiteNoise with manifest storage; `collectstatic` at build. (Static can stay local/WhiteNoise; only *media* needs R2.)
- Required env vars: `R2_ACCOUNT_ID` / endpoint URL, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`.

---

## 9. Design system

Derived from the charity's existing green seedling logo. Warm, photo-forward, trustworthy — **not** brutalist/tech. Flat (no gradients), generous whitespace, modest corner radius (soft, not sharp, not bubbly).

### Palette

| Role | Hex | Use |
|---|---|---|
| Deep green | `#2F5A40` | Headings, wordmark, primary brand |
| Leaf | `#5E8C4E` | Secondary green, accents, links |
| Cream | `#F8F3E7` | Page background (warm paper, never stark white) |
| Terracotta | `#C06A45` | **Donate CTA** + warm human accent (use sparingly; reserve for the primary action) |
| Wheat | `#E6C879` | Optional highlights / dividers |
| Ink | `#262620` | Body text (warm near-black, never pure `#000` on cream) |

### Typography

- **Headings:** a timeless old-style serif — **Spectral** (preferred) or **Lora**. Conveys "established and trustworthy" without being trendy.
- **Body:** a clean humanist sans — **Hanken Grotesk** (or Source Sans 3). Must carry both English and Indonesian comfortably.
- Pairing logic: serif gravitas on top, plain legible sans below = warmth + credibility.

### Wordmark

Indonesian primary, English descender:
> **Komunitas Anak Belajar**
> CHILDREN LEARNING COMMUNITY

Pair with the green seedling mark. (Obtain a clean/vector logo from Debby; do not trace from a photo of a banner.)

### Layout principles

- Lead with real photography (kids *engaged* — learning, field trips, the healthy-meal program — never poverty-as-spectacle).
- Above-the-fold stat chips on Home (28 anak aktif / 2 pusat belajar / X tahun) for instant, concrete credibility.
- Plenty of cream breathing room. Clear, large type.

---

## 10. Deployment (Railway)

- App service (gunicorn) + managed **PostgreSQL** plugin.
- `DATABASE_URL` consumed via `dj-database-url`.
- Build with `uv` (uv sync). Release/build steps: `migrate`, `collectstatic`.
- Start command: `gunicorn config.wsgi:application`.
- Env vars: `SECRET_KEY`, `DJANGO_SETTINGS_MODULE=config.settings.production`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL` (auto), R2 creds (§8).
- **Backups:** enable Railway's Postgres backups. Media durability is handled by R2. The database (her content/structure) is the irreplaceable asset — confirm backups are on before launch.
- Domain: `childrenlearning.org` → Railway, with Cloudflare in front (already in the maintainer's stack).

---

## 11. Content & legitimacy notes (for whoever seeds content)

- **Stat chips** are the cheapest high-yield trust signal — keep them current and specific.
- **IFG / BUMN partnership** ("Berbagi Kebahagiaan Muharram Bersama IFG") belongs on Dukung as a discreet partners/social-proof element. An established financial group ran a CSR event with these kids — that's vetting a diligence-minded patron reads.
- **Photo posture:** active, dignified images of children learning. Be consent-aware about identifiable minors on a public site (more visible than the old blog). Not a blocker, a posture.
- **The legal-entity conversation** (registering a yayasan) is a prerequisite for *both* card payments and the strongest donor trust. Out of scope for the build, but it's the single biggest lever on the actual goal — worth raising with Debby separately.

---

## 12. Build phases

The build proceeds in ordered, separately-promptable phases, each ending in review:

1. **Phase 1 — Backend skeleton** *(complete)*: project scaffold, page models, block set, admin in Indonesian, tests.
2. **Phase 2 — Templates + design + bilingual toggle**: the design system (§9) and all page templates, including the journal-style Laporan index and the ID/EN toggle. Built to match approved mockups.
3. **Phase 3 — Content migration**: import the full historical Blogspot archive into `BlogPostPage` records (§13). Runs *before* deploy so the site launches already populated, not empty.
4. **Phase 4 — Deployment**: R2 media, Railway app + Postgres, env vars, backups, domain (§8, §10).

---

## 13. Content migration (Phase 3)

Import the full archive from the historical reports blog — `cakungchildrencommunity.blogspot.com` — back to 2009. The populated chronicle is the project's primary legitimacy asset, so this is a core deliverable.

**Approach — feed-first (no admin access required).** Blogspot exposes a public feed at `.../feeds/posts/default` with `?max-results=` and `?start-index=` for pagination. By default it returns *full* post content as structured data (title, publish date, full body HTML, labels). A Wagtail management command pages through the feed and creates one `BlogPostPage` per post, mapping: published date → `date`, title → `title`, body HTML → `body` (converted to StreamField blocks — at minimum a `paragraph` block; promote `<img>` to `image` / `gallery` blocks where feasible).

- **No dependency on Debby's login.** The feed is public; her admin access is only a fallback for anything the feed misses.
- **First step:** hit the feed URL and confirm it is live and returns full (not summary-only) content. If the blog was set to "summary only", fall back to fetching each post's HTML page (URLs come from the feed) and extracting the `.post-body` element.
- **Images:** download each image from its `googleusercontent` / Blogger CDN URL and re-upload to Wagtail Images (→ R2). Expect a few of the oldest (2009–2011) images to be already dead on Google's side — unrecoverable, but post *text* always survives via the feed.
- **Cleanup pass:** strip Blogger HTML cruft (inline styles, the `Diposting oleh… / Tidak ada komentar` footer boilerplate, share widgets) before saving.
- **Bilingual content imports as-is:** old posts are stacked English-then-Indonesian, which maps directly onto the free-form `body` field — no transformation needed.
- **Scope:** import everything; unpublish duds afterward rather than curating up front (density is the point). Posts import as **published** with their original dates.
- **Second blog out of scope:** `cakungchildrencreation.blogspot.com` (crafts/products) is not imported in v1.

---

## 14. Decisions (locked)

1. **Toggle-page content fields:** paired **StreamFields** (`body_id`/`body_en`) on About and Support — consistent with the blog, supports inline images.
2. **Version pinning:** **Wagtail 7.4 LTS + Django 5.2 LTS** (not Django 6.0 non-LTS).
3. **Bank details:** discrete structured fields (holder / bank / account no. / SWIFT), not free text.
4. **`callout` block:** included in v1 (the financial-transparency element).
5. **No `SiteSettings` object.** Minimal footer (copyright + link to Dukung); contact lives only on Support. Fewer concepts for the editor.
6. **Search:** deferred to v2.

---

*Next step after this spec is locked: write the Claude Code prompt (models, block set, settings, palette, page tree, deploy config all flow from the decisions above).*
