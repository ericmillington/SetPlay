# SetPlay

**Know what's out there. Own what's yours. Build something worth finding.**

SetPlay is a done-for-you digital presence service. We take a full inventory of
a client's digital footprint, score it, deliver a clear plan, and then build a
responsible, beautiful website that anchors their presence.

## How the work flows

```
 Intake  ─▶  Footprint audit  ─▶  Report + roadmap  ─▶  Cleanup  ─▶  Website  ─▶  Care plan
 (client)    (/footprint-audit)   (tools/render_report)  (client+us)  (/presence-site)
```

| Stage | What happens | Where it lives |
|---|---|---|
| 1. Intake | Client fills in the questionnaire and signs the consent form | `templates/intake.md` |
| 2. Audit | Search, profile inventory, privacy exposure, website check | `framework/audit-checklist.md`, `/footprint-audit` |
| 3. Report | Scored across 6 pillars, findings, a Now / Next / Later roadmap | `tools/render_report.py` |
| 4. Website | Brief, then a fast, accessible, privacy-respecting site | `templates/site-brief.md`, `/presence-site` |

## Repo layout

```
docs/offer.md                 The product: positioning, packages, pricing, process
docs/principles.md            What "responsible web presence" means (our promise)
framework/audit-checklist.md  Everything we check, pillar by pillar
framework/scoring.md          The 0–100 Presence Score rubric
templates/                    Intake, consent, site brief
tools/new_client.sh           Scaffold a client folder
tools/collect.py              Runs every automated collector for a client in one command
tools/serp.py                 Real, localized Google results (DataForSEO; needs API login)
tools/site_check.py           Website check: HTTPS, headers, SEO/social tags, a11y signals, trackers
tools/pagespeed.py            Lighthouse scores (PageSpeed API, or local Chromium fallback)
tools/domain_check.py         Registrar, expiry, WHOIS privacy, MX/SPF/DMARC
tools/handles.py              Handle availability across platforms
tools/render_report.py        audit.json → a polished, client-ready HTML report
clients/pixelheap/            Pilot audit (Pixelheap / Eric Millington), the reference example
.claude/skills/               Claude workflows: /footprint-audit, /presence-site
```

## Quick start

```bash
tools/new_client.sh "Jane Doe"                  # creates clients/jane-doe/
# fill client.inputs in clients/jane-doe/audit.json (name, site, location, handles…)
python3 tools/collect.py jane-doe                # gathers everything into collected/
python3 tools/render_report.py clients/jane-doe/audit.json
```

Or ask Claude to do it: `/footprint-audit jane-doe`.

Open `clients/pixelheap/report.html` to see a finished deliverable.

> **Client data is private.** Everything under `clients/` except the pilot is
> git-ignored on purpose. Store real client folders somewhere access-controlled.

## Accounts the tools use

| Service | Used for | Setup |
|---|---|---|
| DataForSEO | Real Google results by town and device | Account plus API login, saved as a network credential for `api.dataforseo.com` (or `DATAFORSEO_LOGIN`/`DATAFORSEO_PASSWORD` locally) |
| Google PageSpeed API | Lighthouse + real-user Core Web Vitals | Optional `PAGESPEED_API_KEY`; without one, falls back to local Lighthouse |
