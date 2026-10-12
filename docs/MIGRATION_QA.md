# Light-Theme Migration — QA Rules

**Purpose:** The pass/fail checklist every page must clear before it counts as "migrated to the light Bright-C theme." Companion to [AVA_SITE_PLAYBOOK.md](AVA_SITE_PLAYBOOK.md) §4a (design system) and §7 (QA gate). Two layers: an **automated checker** (`scratchpad/qa_check.py`, run against the live rendered HTML) and a **visual pass** (Playwright desktop + mobile).

> Why this exists: the Naperville proof shipped with giant black triangles in the CTA band because the page used `.cta-bul`/`.faq`/`.soft` classes that weren't in the stylesheet it inherited. HTML-only checks miss that class; the **CSS-class-coverage** rule (A8) and the **visual pass** (V) both now catch it.

## A. Automated rules (must all pass)
Run the session's `qa_check.py` (a throwaway script in the scratchpad — regenerate it from the rules below; it fetches **public** URLs only, so it needs no credentials and must never embed the app password). It fetches each page's live rendered HTML and asserts:

1. **Light tokens present** — contains `--bg:#f7f8fc` **and** `Hanken Grotesk`. (Not still dark.)
2. **No wpautop mangling** — rendered HTML does **not** contain `<p><!DOCTYPE` or `<br />` inside the `<style>`. (Content was wrapped in `<!-- wp:html -->`.)
3. **Self-referential canonical** — `<link rel="canonical">` present and equals the page's own URL.
4. **Title + meta description** — non-empty `<title>` and `<meta name="description">` (or Yoast equivalents).
5. **Nav + branded CTA** — a `.nav-cta` link exists, its text is exactly **"Get a free audit"**, and its `href` is `/contact/`.
6. **Primary CTA → /contact/** — the hero `.btn-p` href is `/contact/`. No `href="#"` anywhere in nav/hero.
7. **No stale CTA wording** — the strings `Book a Call`, `Get Started`, `Get Your Free Audit`, `Get Free Audit` appear **nowhere** (standardized to "Get a free audit").
8. **CSS-class coverage** — for every structural class the markup *uses* (`soft`, `faq`, `cta-bul`, `ctaband`, `ic`, `proof`, `grid3`, `citygrid`, `why`, `crumb`), a matching rule exists in the page's `<style>`. (This is the rule that catches the unsized-SVG / unstyled-section bug.)
9. **Dark band heading is explicitly white** — if `.ctaband` is used, the stylesheet sets `.ctaband h2{…color:#fff…}` (inherited white loses to the theme's `h2` rule).
10. **Schema present** — ≥1 `application/ld+json`; if the page has an FAQ accordion, a `FAQPage` block exists.
11. **Footer present** — `<footer>` with the shared Services/Cities/Company columns.
12. **Page template = `elementor_canvas`** — the page's WP `template` must be `elementor_canvas`, NOT `''` (default). A default-template page renders the **theme header/menu/footer chrome** around the custom HTML (bloats the page to ~200KB and injects `<a href="#">` menu dropdowns → shows up as the A6 dead-hash failure). Set via REST: `POST /pages/<id> {"template":"elementor_canvas"}`. *(This is what broke Lombard/Oak Brook/Aurora-alt/Wheaton in the city rollout.)*

## V. Visual pass (Playwright — desktop 1280 + mobile 390)
12. Full-page screenshot at both widths; eyeball for:
    - No oversized / black / broken SVG icons anywhere (esp. CTA band bullets, card icons).
    - Hero headline legible; gradient text renders; pill visible.
    - CTA band heading **visible** (white on navy), bullets show green checks.
    - FAQ accordion items render as cards; open/close works.
    - Cards align in a grid; nothing overlaps; **no horizontal scroll** on mobile (body never scrolls sideways).
    - Footer columns intact.
13. **Console** — no errors except the known site-wide favicon 404s (`Untitled-design-2-*.jpg`). Any `TypeError`/form error is a fail.
14. **Embedded third-party** (Contact page) — the HubSpot form actually renders its fields + Submit (wait ~4s; it loads in an iframe).

## Known-safe noise (not failures)
- `Untitled-design-2-150x150.jpg` / `-300x300.jpg` **404s** — a site-wide favicon asset referenced by the WP head. Pre-existing, unrelated to migrated pages.
- `JQMIGRATE: Migrate is installed` — informational jQuery-migrate log.

## Process
1. Build → deploy → **purge object + page cache**.
2. Run `qa_check.py` (layer A). Fix any fail, redeploy, re-run.
3. Playwright desktop + mobile screenshot (layer V). Fix, redeploy, re-check.
4. Only then mark the page migrated in the playbook (§5).
