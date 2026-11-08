---
name: presence-site
description: Build a client's responsible, beautiful website from their audit and signed-off site brief (clients/<slug>/site-brief.md). Use for /presence-site or "build the site for <client>".
---

# Presence site build

Inputs: `clients/<slug>/audit.json` (what the site must fix) and `clients/<slug>/site-brief.md`
(pages, voice, visuals, canonical bio). If the brief is empty, draft it from the audit and intake
first, and get the user's sign-off before building.

## Build rules (from docs/principles.md)

- **Static by default.** Use hand-written HTML/CSS, or Astro if there are more than about 6 pages. Output goes to
  `clients/<slug>/site/`. Host it on the client's own Netlify, Cloudflare Pages or GitHub Pages account.
- **Owned.** Use no platform lock-in, and include a README in `site/` explaining how to edit and deploy.
- **Private.** Include no third-party trackers or fonts from ad-tech CDNs. If analytics are wanted, use cookieless analytics only.
  Don't show a home address, and use a contact form or business email rather than a personal one.
- **Accessible.** Meet WCAG 2.2 AA: semantic landmarks, one H1, no skipped heading levels, alt text, visible focus,
  4.5:1 contrast, and `prefers-reduced-motion` respected.
- **Fast.** Keep pages under 1 MB, use responsive images (AVIF/WebP), and use no JavaScript unless it's needed.
- **Secure.** Ship a `_headers` file (or equivalent) with HSTS, CSP, X-Content-Type-Options,
  Referrer-Policy and Permissions-Policy.
- **Found.** Each page's title includes the person's name plus their role and town. Include meta descriptions, OG and Twitter tags
  with a 1200×630 image, `sitemap.xml`, `robots.txt`, and JSON-LD (`Person` and/or `LocalBusiness`) whose
  `sameAs` lists every profile in the inventory.
- **Consistent.** Use the canonical bio from the brief verbatim. Every profile link comes from the inventory.

## Verify before handing off

Serve the site locally, screenshot it at 1280 and 390 wide, run `tools/site_check.py` against it once deployed,
then re-score the Website Quality pillar and show the before/after.
